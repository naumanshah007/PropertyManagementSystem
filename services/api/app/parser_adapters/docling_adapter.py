from __future__ import annotations

from pathlib import Path

from app.schemas import ParsedDocument, ParsedPage

from .base import ParserUnavailable, build_parsed_document, pdf_page_count, require_module


class DoclingAdapter:
    name = "docling"
    parser_version = "phase-4.5-docling-v1"

    def parse(self, file_path: Path, document_id: str) -> ParsedDocument:
        require_module("docling", "Install docling to enable this parser benchmark.")

        try:
            from docling.document_converter import DocumentConverter  # type: ignore[import-not-found]
        except Exception as exc:
            raise ParserUnavailable(f"Docling is installed but its DocumentConverter API is unavailable: {exc}") from exc

        try:
            result = DocumentConverter().convert(str(file_path))
            document = result.document
            markdown = document.export_to_markdown()
        except Exception as exc:
            raise ParserUnavailable(f"Docling failed to parse this PDF: {exc}") from exc

        if not markdown.strip():
            raise ParserUnavailable("Docling returned no text for this PDF.")

        page_count = pdf_page_count(file_path)
        pages = [
            ParsedPage(
                page_number=1,
                text=markdown.strip(),
                warnings=["docling_page_boundaries_not_mapped"],
            )
        ]
        pages.extend(
            ParsedPage(
                page_number=page_number,
                text="",
                warnings=["docling_page_text_not_mapped"],
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
