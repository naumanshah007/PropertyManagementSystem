from __future__ import annotations

from pathlib import Path

import fitz
import pytest
from fastapi.testclient import TestClient
from auth_helpers import PLATFORM_ADMIN_HEADERS

from app.main import app


client = TestClient(app, headers=PLATFORM_ADMIN_HEADERS)
SAMPLE_SURVEY = Path(__file__).resolve().parents[3] / "samples" / "surveys" / "38-Asbestos-Survey-_Rev_0.pdf"


def _make_pdf(pages: list[str]) -> bytes:
    document = fitz.open()
    for text in pages:
        page = document.new_page()
        page.insert_text((72, 72), text)
    return document.tobytes()


def _upload_pdf(pdf_bytes: bytes, name: str = "register-demo.pdf") -> str:
    response = client.post(
        "/documents/upload",
        files={"file": (name, pdf_bytes, "application/pdf")},
    )
    assert response.status_code == 200
    return response.json()["document_id"]


def _find_item(items: list[dict], item_text: str) -> dict:
    for item in items:
        if item_text.lower() in item["item"].lower():
            return item
    raise AssertionError(f"Item not found: {item_text}")


def test_extract_register_endpoint_returns_reviewable_items() -> None:
    pdf_bytes = _make_pdf(
        [
            "Asbestos Demolition Survey Register",
            "R10-11 External / Building Envelope Flat cladding Fibre Cement Sheet - Flat Sheet 320 sqm Class B Positive",
            "R10 Inside room Power box Power box and systems 1 sqm Presume No Access Class B",
            "R11 Inside room Chimney AIB hidden Insulating Board 4 pieces Class A Limited Access",
            "R12-16 External / Building Envelope External Cladding Fibre Cement Sheet - Flat Sheet 920 sqm Class B Positive",
            "R24 Inside room Power board box 1 Box Presume No Access Class B",
            "R30 Inside room vinyl sample NAD No Asbestos Detected",
        ]
    )
    document_id = _upload_pdf(pdf_bytes)

    response = client.post(f"/documents/{document_id}/extract-register")
    assert response.status_code == 200
    result = response.json()
    assert result["document_id"] == document_id
    assert result["parser_version"].startswith("phase-3")
    assert len(result["items"]) >= 6

    power_box = _find_item(result["items"], "Power box")
    assert power_box["access_status"] == "no_access"
    assert power_box["asbestos_result"] == "presumed"
    assert power_box["review_status"] == "review_required"

    chimney = _find_item(result["items"], "Chimney AIB hidden")
    assert chimney["friability_class"] == "Class A"
    assert chimney["access_status"] == "limited_access"
    assert chimney["review_status"] == "review_required"

    assert any(item["asbestos_result"] == "NAD" and item["review_status"] == "excluded_from_pricing" for item in result["items"])

    get_response = client.get(f"/documents/{document_id}/register-items")
    assert get_response.status_code == 200
    assert get_response.json()["document_id"] == document_id


def test_extract_register_missing_document_returns_404() -> None:
    response = client.post("/documents/doc-missing/extract-register")
    assert response.status_code == 404


@pytest.mark.skipif(
    not SAMPLE_SURVEY.exists(),
    reason="Golden survey missing: add samples/surveys/38-Asbestos-Survey-_Rev_0.pdf to enable this test.",
)
def test_golden_asbestos_survey_extracts_expected_items() -> None:
    with SAMPLE_SURVEY.open("rb") as sample:
        upload_response = client.post(
            "/documents/upload",
            files={"file": (SAMPLE_SURVEY.name, sample.read(), "application/pdf")},
        )
    assert upload_response.status_code == 200
    document_id = upload_response.json()["document_id"]

    response = client.post(f"/documents/{document_id}/extract-register")
    assert response.status_code == 200
    items = response.json()["items"]

    flat_cladding = _find_item(items, "Flat cladding")
    assert flat_cladding["location"] == "External / Building Envelope"
    assert flat_cladding["material"] == "Fibre Cement Sheet - Flat Sheet"
    assert flat_cladding["extent_quantity"] == 320
    assert flat_cladding["extent_unit"] == "sqm"
    assert flat_cladding["friability_class"] == "Class B"
    assert flat_cladding["source_page"] == 18

    power_box = _find_item(items, "Power box")
    assert power_box["material"] == "Power box and systems"
    assert power_box["extent_quantity"] == 1
    assert power_box["extent_unit"] == "sqm"
    assert power_box["asbestos_result"] == "presumed"
    assert power_box["access_status"] == "no_access"
    assert power_box["friability_class"] == "Class B"
    assert power_box["source_page"] == 19

    chimney = _find_item(items, "Chimney AIB hidden")
    assert chimney["material"] == "Insulating Board"
    assert chimney["extent_quantity"] == 4
    assert chimney["extent_unit"] == "pieces"
    assert chimney["friability_class"] == "Class A"
    assert chimney["access_status"] == "limited_access"
    assert chimney["source_page"] == 21

    external_cladding = _find_item(items, "External Cladding")
    assert external_cladding["extent_quantity"] == 920
    assert external_cladding["extent_unit"] == "sqm"
    assert external_cladding["friability_class"] == "Class B"
    assert external_cladding["source_page"] == 25

    power_board_box = _find_item(items, "Power board box")
    assert power_board_box["extent_quantity"] == 1
    assert power_board_box["extent_unit"] == "Box"
    assert power_board_box["asbestos_result"] == "presumed"
    assert power_board_box["access_status"] == "no_access"
    assert power_board_box["friability_class"] == "Class B"
    assert power_board_box["source_page"] == 33

    assert any(item["asbestos_result"] == "NAD" and item["review_status"] == "excluded_from_pricing" for item in items)

