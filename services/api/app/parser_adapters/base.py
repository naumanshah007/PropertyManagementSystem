from __future__ import annotations

import importlib.util
from datetime import datetime, timezone
from pathlib import Path
from typing import Protocol

import fitz

from app.schemas import OcrStatus, ParsedDocument, ParsedPage, ParsedTable


class ParserUnavailable(RuntimeError):
    """Raised when an optional parser cannot run in this local environment."""


class ParserAdapter(Protocol):
    name: str

    def parse(self, file_path: Path, document_id: str) -> ParsedDocument:
        """Parse a PDF into the shared ParsedDocument contract."""


def require_module(module_name: str, install_hint: str) -> None:
    if importlib.util.find_spec(module_name) is None:
        raise ParserUnavailable(f"{module_name} is not installed. {install_hint}")


def pdf_page_count(file_path: Path) -> int:
    with fitz.open(file_path) as document:
        return len(document)


def build_parsed_document(
    *,
    document_id: str,
    file_path: Path,
    parser_version: str,
    pages: list[ParsedPage],
    tables: list[ParsedTable] | None = None,
    ocr_status: OcrStatus = "not_required",
) -> ParsedDocument:
    return ParsedDocument(
        document_id=document_id,
        file_name=file_path.name,
        page_count=len(pages),
        parser_version=parser_version,
        pages=pages,
        tables=tables or [],
        ocr_status=ocr_status,
        stored_path=str(file_path),
        parsed_json_path="",
        created_at=datetime.now(timezone.utc),
    )
