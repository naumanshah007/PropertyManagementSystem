from __future__ import annotations

import shutil
import subprocess
import tempfile
from pathlib import Path

from app.schemas import ParsedDocument, ParsedPage

from .base import ParserUnavailable, build_parsed_document, pdf_page_count, require_module


class MarkerAdapter:
    name = "marker"
    parser_version = "phase-4.5-marker-v1"

    def parse(self, file_path: Path, document_id: str) -> ParsedDocument:
        require_module("marker", "Install marker-pdf to enable this parser benchmark.")

        marker_single = shutil.which("marker_single")
        if marker_single is None:
            raise ParserUnavailable("marker is installed, but marker_single CLI is not on PATH.")

        with tempfile.TemporaryDirectory() as temp_dir:
            command = [marker_single, str(file_path), temp_dir, "--output_format", "markdown"]
            result = subprocess.run(command, capture_output=True, text=True, check=False, timeout=180)
            if result.returncode != 0:
                raise ParserUnavailable(f"Marker failed: {result.stderr.strip() or result.stdout.strip()}")

            markdown_files = sorted(Path(temp_dir).rglob("*.md"))
            if not markdown_files:
                raise ParserUnavailable("Marker completed but produced no markdown output.")
            text = "\n\n".join(path.read_text(encoding="utf-8") for path in markdown_files).strip()

        if not text:
            raise ParserUnavailable("Marker returned no text for this PDF.")

        page_count = pdf_page_count(file_path)
        pages = [
            ParsedPage(
                page_number=1,
                text=text,
                warnings=["marker_page_boundaries_not_mapped"],
            )
        ]
        pages.extend(
            ParsedPage(
                page_number=page_number,
                text="",
                warnings=["marker_page_text_not_mapped"],
            )
            for page_number in range(2, page_count + 1)
        )
        return build_parsed_document(
            document_id=document_id,
            file_path=file_path,
            parser_version=self.parser_version,
            pages=pages,
            tables=[],
            ocr_status="not_required",
        )
