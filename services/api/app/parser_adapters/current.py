from __future__ import annotations

from pathlib import Path

from app.document_parser import parse_pdf
from app.schemas import ParsedDocument


class CurrentPyMuPdfPdfplumberAdapter:
    name = "pymupdf_pdfplumber"

    def parse(self, file_path: Path, document_id: str) -> ParsedDocument:
        return parse_pdf(document_id=document_id, file_path=file_path, file_name=file_path.name)
