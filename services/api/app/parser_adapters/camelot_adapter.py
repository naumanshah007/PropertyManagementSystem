from __future__ import annotations

from pathlib import Path

import fitz

from app.schemas import ParsedDocument, ParsedPage, ParsedTable

from .base import ParserUnavailable, build_parsed_document, require_module


class CamelotAdapter:
    name = "camelot"
    parser_version = "phase-4.5-camelot-v1"

    def parse(self, file_path: Path, document_id: str) -> ParsedDocument:
        require_module(
            "camelot",
            "Install camelot-py with its system dependencies to enable Camelot table benchmarking.",
        )
        import camelot  # type: ignore[import-not-found]

        pages: list[ParsedPage] = []
        with fitz.open(file_path) as document:
            for index, page in enumerate(document, start=1):
                text = page.get_text("text").strip()
                warnings: list[str] = []
                if not text:
                    warnings.append("no_text_extracted")
                pages.append(ParsedPage(page_number=index, text=text, warnings=warnings))

        tables: list[ParsedTable] = []
        try:
            extracted_tables = camelot.read_pdf(str(file_path), pages="all", flavor="lattice")
        except Exception as exc:
            raise ParserUnavailable(f"Camelot could not parse tables: {exc}") from exc

        for table in extracted_tables:
            page_number = int(getattr(table, "page", 0) or 0)
            rows = [
                ["" if cell is None else str(cell).strip() for cell in row]
                for row in table.df.values.tolist()
            ]
            if rows:
                tables.append(
                    ParsedTable(
                        page_number=page_number,
                        rows=rows,
                        extraction_method="camelot.read_pdf(lattice)",
                    )
                )

        if not pages:
            raise ParserUnavailable("Camelot benchmark could not read PDF pages via PyMuPDF.")

        ocr_status = "required_later" if all(not page.text for page in pages) else "not_required"
        return build_parsed_document(
            document_id=document_id,
            file_path=file_path,
            parser_version=self.parser_version,
            pages=pages,
            tables=tables,
            ocr_status=ocr_status,
        )
