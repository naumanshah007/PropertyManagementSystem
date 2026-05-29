from __future__ import annotations

from pathlib import Path

import fitz
import pytest

from app.parser_adapters import CurrentPyMuPdfPdfplumberAdapter, ParserUnavailable, QwenVlAdapter
from app.parser_adapters.camelot_adapter import CamelotAdapter


def _make_pdf(path: Path, text: str) -> None:
    document = fitz.open()
    page = document.new_page()
    page.insert_text((72, 72), text)
    document.save(path)


def test_current_adapter_returns_shared_parsed_document(tmp_path: Path) -> None:
    pdf_path = tmp_path / "adapter-demo.pdf"
    _make_pdf(pdf_path, "Asbestos Demolition Survey\nRegister\nClass A and Class B Asbestos Meaning")

    parsed = CurrentPyMuPdfPdfplumberAdapter().parse(pdf_path, "adapter-current")

    assert parsed.document_id == "adapter-current"
    assert parsed.file_name == "adapter-demo.pdf"
    assert parsed.page_count == 1
    assert parsed.parser_version.startswith("phase-2")
    assert "Register" in parsed.pages[0].text


def test_qwen_adapter_is_explicit_placeholder(tmp_path: Path) -> None:
    pdf_path = tmp_path / "adapter-demo.pdf"
    _make_pdf(pdf_path, "placeholder")

    with pytest.raises(ParserUnavailable, match="placeholder"):
        QwenVlAdapter().parse(pdf_path, "adapter-qwen")


def test_camelot_adapter_skips_cleanly_when_unavailable(tmp_path: Path) -> None:
    pdf_path = tmp_path / "adapter-demo.pdf"
    _make_pdf(pdf_path, "table benchmark")

    try:
        CamelotAdapter().parse(pdf_path, "adapter-camelot")
    except ParserUnavailable as exc:
        assert str(exc)
