from __future__ import annotations

from .base import ParserAdapter, ParserUnavailable
from .camelot_adapter import CamelotAdapter
from .current import CurrentPyMuPdfPdfplumberAdapter
from .docling_adapter import DoclingAdapter
from .marker_adapter import MarkerAdapter
from .paddleocr_adapter import PaddleOcrAdapter
from .qwen_vl_adapter import QwenVlAdapter
from .surya_adapter import SuryaOcrAdapter


def get_parser_adapters() -> list[ParserAdapter]:
    return [
        CurrentPyMuPdfPdfplumberAdapter(),
        DoclingAdapter(),
        MarkerAdapter(),
        PaddleOcrAdapter(),
        SuryaOcrAdapter(),
        CamelotAdapter(),
        QwenVlAdapter(),
    ]


__all__ = [
    "CamelotAdapter",
    "CurrentPyMuPdfPdfplumberAdapter",
    "DoclingAdapter",
    "MarkerAdapter",
    "PaddleOcrAdapter",
    "ParserAdapter",
    "ParserUnavailable",
    "QwenVlAdapter",
    "SuryaOcrAdapter",
    "get_parser_adapters",
]
