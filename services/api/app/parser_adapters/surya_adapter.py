from __future__ import annotations

from pathlib import Path

from app.schemas import ParsedDocument

from .base import ParserUnavailable, require_module


class SuryaOcrAdapter:
    name = "surya_ocr"
    parser_version = "phase-4.5-surya-v1"

    def parse(self, file_path: Path, document_id: str) -> ParsedDocument:
        require_module("surya", "Install surya-ocr to enable this OCR benchmark.")
        raise ParserUnavailable(
            "Surya OCR adapter is registered for benchmarking, but page rasterization/OCR wiring is not enabled in this POC."
        )
