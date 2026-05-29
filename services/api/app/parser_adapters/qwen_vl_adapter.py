from __future__ import annotations

from pathlib import Path

from app.schemas import ParsedDocument

from .base import ParserUnavailable


class QwenVlAdapter:
    name = "qwen2_5_vl_placeholder"
    parser_version = "phase-4.5-qwen2.5-vl-placeholder-v1"

    def parse(self, file_path: Path, document_id: str) -> ParsedDocument:
        raise ParserUnavailable(
            "Qwen2.5-VL adapter placeholder only; no local vision model or inference endpoint is configured."
        )
