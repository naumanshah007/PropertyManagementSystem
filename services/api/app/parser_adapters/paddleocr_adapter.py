from __future__ import annotations

from pathlib import Path

from app.schemas import ParsedDocument

from .base import ParserUnavailable, require_module


class PaddleOcrAdapter:
    name = "paddleocr"
    parser_version = "phase-4.5-paddleocr-v1"

    def parse(self, file_path: Path, document_id: str) -> ParsedDocument:
        require_module("paddleocr", "Install paddleocr and paddlepaddle to enable this OCR benchmark.")
        raise ParserUnavailable(
            "PaddleOCR adapter is registered for benchmarking, but page rasterization/OCR wiring is not enabled in this POC."
        )
