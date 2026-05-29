from __future__ import annotations

import re
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

import fitz
import pdfplumber
from fastapi import UploadFile

from .file_storage import get_file_storage
from .schemas import ParsedDocument, ParsedPage, ParsedTable
from .storage_paths import STORAGE_ROOT, atomic_write_text


PARSER_VERSION = "phase-2-pymupdf-pdfplumber-v1"
DEFAULT_ORGANISATION_ID = "org-demo-tracequote"
# STORAGE_ROOT is re-exported from storage_paths (DATA_DIR-aware) so the many
# `from .document_parser import STORAGE_ROOT` call sites keep working unchanged.

# Storage IDs (document_id, organisation_id) must match this pattern to prevent path traversal.
# Allow alphanumerics, dash, and underscore only. Reject path separators, dots, etc.
_SAFE_ID_PATTERN = re.compile(r"^[A-Za-z0-9_-]{1,100}$")


class InvalidStorageId(ValueError):
    """Raised when an organisation_id, document_id, or similar ID fails sanitization."""


def _validate_storage_id(value: str, kind: str) -> str:
    """Reject IDs that could escape the storage root via path traversal."""
    if not isinstance(value, str) or not _SAFE_ID_PATTERN.match(value):
        raise InvalidStorageId(f"Invalid {kind}: must be 1-100 chars of [A-Za-z0-9_-]")
    return value


def _safe_file_name(file_name: str) -> str:
    name = Path(file_name).name
    return re.sub(r"[^A-Za-z0-9._-]+", "_", name) or "uploaded.pdf"


def _document_dir(document_id: str, organisation_id: str = DEFAULT_ORGANISATION_ID) -> Path:
    _validate_storage_id(document_id, "document_id")
    _validate_storage_id(organisation_id, "organisation_id")
    requested = STORAGE_ROOT / organisation_id / "documents" / document_id
    if organisation_id != DEFAULT_ORGANISATION_ID or requested.exists():
        return requested

    for candidate in STORAGE_ROOT.glob("org-*/documents/*"):
        if candidate.name == document_id and candidate.is_dir():
            return candidate
    return requested


def resolve_document_organisation_id(document_id: str, organisation_id: str = DEFAULT_ORGANISATION_ID) -> str:
    document_dir = _document_dir(document_id, organisation_id)
    try:
        return document_dir.parents[1].name
    except IndexError:
        return organisation_id


def _parsed_json_path(document_id: str, organisation_id: str = DEFAULT_ORGANISATION_ID) -> Path:
    return _document_dir(document_id, organisation_id) / "parsed.json"


def _original_path(document_id: str, file_name: str, organisation_id: str = DEFAULT_ORGANISATION_ID) -> Path:
    return _document_dir(document_id, organisation_id) / _safe_file_name(file_name)


def save_upload(file: UploadFile, organisation_id: str = DEFAULT_ORGANISATION_ID) -> tuple[str, Path]:
    document_id = f"doc-{uuid4().hex[:12]}"
    target_dir = _document_dir(document_id, organisation_id)
    target_dir.mkdir(parents=True, exist_ok=True)
    target_path = _original_path(document_id, file.filename or "uploaded.pdf", organisation_id)

    try:
        storage_key = str(target_path.relative_to(STORAGE_ROOT.parent))
        saved_path = get_file_storage(STORAGE_ROOT.parent).save_upload(file.file, storage_key)
        target_path = Path(saved_path)
    finally:
        file.file.close()

    return document_id, target_path


def parse_pdf(
    document_id: str,
    file_path: Path,
    file_name: str,
    organisation_id: str = DEFAULT_ORGANISATION_ID,
) -> ParsedDocument:
    pages: list[ParsedPage] = []
    tables: list[ParsedTable] = []
    ocr_status = "not_required"

    try:
        with fitz.open(file_path) as document:
            for index, page in enumerate(document, start=1):
                text = page.get_text("text").strip()
                warnings: list[str] = []
                if not text:
                    warnings.append("no_text_extracted")
                pages.append(ParsedPage(page_number=index, text=text, warnings=warnings))
    except Exception as exc:
        raise ValueError(f"PyMuPDF failed to parse PDF text: {exc}") from exc

    if not pages:
        raise ValueError("PyMuPDF failed to parse PDF text: document has no pages")

    if pages and all(not page.text for page in pages):
        ocr_status = "required_later"

    try:
        with pdfplumber.open(file_path) as pdf:
            for index, page in enumerate(pdf.pages, start=1):
                extracted_tables = page.extract_tables() or []
                for table in extracted_tables:
                    normalized_rows = [
                        ["" if cell is None else str(cell).strip() for cell in row]
                        for row in table
                        if row
                    ]
                    if normalized_rows:
                        tables.append(
                            ParsedTable(
                                page_number=index,
                                rows=normalized_rows,
                                extraction_method="pdfplumber.extract_tables",
                            )
                        )
    except Exception:
        for page in pages:
            page.warnings.append("table_extraction_failed")

    parsed = ParsedDocument(
        organisation_id=organisation_id,
        document_id=document_id,
        file_name=file_name,
        page_count=len(pages),
        parser_version=PARSER_VERSION,
        pages=pages,
        tables=tables,
        ocr_status=ocr_status,
        stored_path=str(file_path),
        parsed_json_path=str(_parsed_json_path(document_id, organisation_id)),
        created_at=datetime.now(timezone.utc),
    )

    # Phase B: classify survey type so callers can block Management Plans early
    # and surface presumed-pricing warnings for Management Surveys.
    from .survey_classifier import classify_survey
    parsed.survey_classification = classify_survey(parsed)

    parsed_path = _parsed_json_path(document_id, organisation_id)
    parsed_path.parent.mkdir(parents=True, exist_ok=True)
    atomic_write_text(parsed_path, parsed.model_dump_json(indent=2))

    return parsed


def load_parsed_document(document_id: str, organisation_id: str = DEFAULT_ORGANISATION_ID) -> ParsedDocument | None:
    parsed_path = _parsed_json_path(document_id, organisation_id)
    if not parsed_path.exists():
        return None
    return ParsedDocument.model_validate_json(parsed_path.read_text(encoding="utf-8"))
