from __future__ import annotations

from pathlib import Path

import fitz
import pytest
from fastapi.testclient import TestClient
from auth_helpers import PLATFORM_ADMIN_HEADERS

from app.main import app


client = TestClient(app, headers=PLATFORM_ADMIN_HEADERS)
SAMPLE_SURVEY = Path(__file__).resolve().parents[3] / "samples" / "surveys" / "38-Asbestos-Survey-_Rev_0.pdf"


def _make_pdf(text: str) -> bytes:
    document = fitz.open()
    page = document.new_page()
    page.insert_text((72, 72), text)
    return document.tobytes()


def test_upload_document_parses_pages() -> None:
    pdf_bytes = _make_pdf("Asbestos Demolition Survey\nRegister\nSummary of Areas or Items of Limited Access or No Access")

    response = client.post(
        "/documents/upload",
        files={"file": ("demo-survey.pdf", pdf_bytes, "application/pdf")},
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["document_id"].startswith("doc-")
    assert payload["file_name"] == "demo-survey.pdf"
    assert payload["page_count"] == 1
    assert payload["parser_version"].startswith("phase-2")
    assert payload["ocr_status"] == "not_required"
    assert "Asbestos Demolition Survey" in payload["pages"][0]["text"]

    document_id = payload["document_id"]
    document_response = client.get(f"/documents/{document_id}")
    assert document_response.status_code == 200
    assert document_response.json()["document_id"] == document_id

    pages_response = client.get(f"/documents/{document_id}/pages")
    assert pages_response.status_code == 200
    pages = pages_response.json()
    assert len(pages) == 1
    assert "Register" in pages[0]["text"]


def test_upload_rejects_non_pdf() -> None:
    response = client.post(
        "/documents/upload",
        files={"file": ("notes.txt", b"not a pdf", "text/plain")},
    )

    assert response.status_code == 400


def test_upload_invalid_pdf_returns_parse_error() -> None:
    response = client.post(
        "/documents/upload",
        files={"file": ("broken.pdf", b"%PDF-1.7\nnot a real pdf", "application/pdf")},
    )

    assert response.status_code == 422
    assert "failed to parse" in response.json()["detail"].lower()


def test_missing_document_returns_404() -> None:
    response = client.get("/documents/doc-does-not-exist")
    assert response.status_code == 404


@pytest.mark.skipif(
    not SAMPLE_SURVEY.exists(),
    reason="Golden survey missing: add samples/surveys/38-Asbestos-Survey-_Rev_0.pdf to enable this test.",
)
def test_golden_asbestos_survey_parses_expected_text() -> None:
    with SAMPLE_SURVEY.open("rb") as sample:
        response = client.post(
            "/documents/upload",
            files={"file": (SAMPLE_SURVEY.name, sample.read(), "application/pdf")},
        )

    assert response.status_code == 200
    payload = response.json()
    assert payload["page_count"] == 50
    assert "Asbestos Demolition Survey" in payload["pages"][0]["text"]

    full_text = "\n".join(page["text"] for page in payload["pages"])
    assert "Register" in full_text
    assert "Summary of Areas or Items of Limited Access or No Access" in full_text
    assert "Class A and Class B Asbestos Meaning" in full_text
