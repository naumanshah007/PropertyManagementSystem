from __future__ import annotations

import fitz
from fastapi.testclient import TestClient
from auth_helpers import PLATFORM_ADMIN_HEADERS

from app.main import app


client = TestClient(app, headers=PLATFORM_ADMIN_HEADERS)


def _make_pdf(pages: list[str]) -> bytes:
    document = fitz.open()
    for text in pages:
        page = document.new_page()
        page.insert_text((72, 72), text)
    return document.tobytes()


def _upload_extract_and_generate() -> dict:
    pdf_bytes = _make_pdf(
        [
            "Asbestos Demolition Survey Register",
            "R10-11 External / Building Envelope Flat cladding Fibre Cement Sheet - Flat Sheet 320 sqm Class B Positive",
            "R10 Inside room Power box Power box and systems 1 sqm Presume No Access Class B",
            "R11 Inside room Chimney AIB hidden Insulating Board 4 pieces Class A Limited Access",
            "R12-16 External / Building Envelope External Cladding Fibre Cement Sheet - Flat Sheet 920 sqm Class B Positive",
            "R24 Inside room Power board box 1 Box Presume No Access Class B",
            "R30 Inside room floor tile NAD No Asbestos Detected",
        ]
    )
    upload = client.post(
        "/documents/upload",
        files={"file": ("quote-candidates-demo.pdf", pdf_bytes, "application/pdf")},
    )
    assert upload.status_code == 200
    document_id = upload.json()["document_id"]

    extraction = client.post(f"/documents/{document_id}/extract-register")
    assert extraction.status_code == 200

    candidates = client.post(f"/documents/{document_id}/generate-quote-candidates")
    assert candidates.status_code == 200
    return candidates.json()


def _find_candidate(candidates: list[dict], section: str, text: str | None = None) -> dict:
    for candidate in candidates:
        if candidate["section"] != section:
            continue
        if text is None or text.lower() in candidate["description"].lower():
            return candidate
    raise AssertionError(f"Candidate not found: {section} {text or ''}")


def test_quote_candidate_mapping_rules() -> None:
    result = _upload_extract_and_generate()
    candidates = result["candidates"]

    class_b = _find_candidate(candidates, "Class B Removal", "Flat cladding")
    assert class_b["quantity"] == 320
    assert class_b["unit"] == "sqm"
    assert class_b["review_status"] == "ai_draft"

    class_a = _find_candidate(candidates, "Class A / Friable Removal", "Chimney AIB hidden")
    assert class_a["quantity"] == 4
    assert class_a["unit"] == "pieces"
    assert class_a["review_status"] == "review_required"
    assert class_a["review_required"] is True

    no_access = _find_candidate(candidates, "Provisional / No Access", "Power box")
    assert no_access["review_status"] == "review_required"
    assert any("power isolation" in assumption.lower() for assumption in no_access["assumptions"])

    nad = _find_candidate(candidates, "Excluded / NAD Findings")
    assert nad["review_status"] == "excluded_from_pricing"
    assert nad["review_required"] is False
    assert any("excluded" in exclusion.lower() for exclusion in nad["exclusions"])

    assert _find_candidate(candidates, "Site Establishment")
    assert _find_candidate(candidates, "Waste / Disposal Placeholder")


def test_quote_candidates_preserve_traceability_and_are_not_approved() -> None:
    result = _upload_extract_and_generate()
    candidates = result["candidates"]

    assert candidates
    for candidate in candidates:
        assert candidate["source_register_item_ids"]
        assert candidate["source_evidence"]
        assert candidate["source_pages"]
        assert candidate["confidence"] > 0
        assert candidate["reason"]
        assert candidate["approval_status"] == "not_ready"


def test_quote_candidate_lookup_endpoint() -> None:
    result = _upload_extract_and_generate()
    document_id = result["document_id"]

    response = client.get(f"/documents/{document_id}/quote-candidates")
    assert response.status_code == 200
    assert response.json()["document_id"] == document_id


def test_quote_candidate_missing_document_returns_404() -> None:
    response = client.post("/documents/doc-missing/generate-quote-candidates")
    assert response.status_code == 404

