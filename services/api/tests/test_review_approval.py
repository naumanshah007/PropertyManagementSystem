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


def _priced_quote() -> dict:
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
        files={"file": ("review-demo.pdf", pdf_bytes, "application/pdf")},
    )
    assert upload.status_code == 200
    document_id = upload.json()["document_id"]

    assert client.post(f"/documents/{document_id}/extract-register").status_code == 200
    assert client.post(f"/documents/{document_id}/generate-quote-candidates").status_code == 200
    priced = client.post(f"/documents/{document_id}/price-quote-candidates")
    assert priced.status_code == 200
    return priced.json()


def _find_line(lines: list[dict], section: str, text: str | None = None) -> dict:
    for line in lines:
        if line["section"] != section:
            continue
        if text is None or text.lower() in line["description"].lower():
            return line
    raise AssertionError(f"Line not found: {section} {text or ''}")


def test_editing_line_creates_estimator_edit_and_recalculates() -> None:
    result = _priced_quote()
    line = _find_line(result["lines"], "Class B Removal", "Flat cladding")

    response = client.post(
        f"/documents/{result['document_id']}/priced-quote-lines/{line['id']}/edit",
        json={
            "unit_rate": 50,
            "quantity": 340,
            "reason": "Adjusted cladding extent and rate after estimator review.",
            "user_id": "estimator-1",
        },
    )

    assert response.status_code == 200
    updated = response.json()
    updated_line = next(row for row in updated["lines"] if row["id"] == line["id"])
    assert updated_line["quantity"] == 340
    assert updated_line["unit_rate"] == 50
    assert updated_line["base_cost"] == 17000
    assert updated_line["review_status"] == "review_required"
    assert updated_line["approval_status"] == "not_ready"
    assert len([edit for edit in updated["estimator_edits"] if edit["entity_id"] == line["id"]]) == 2
    assert any(edit["field_name"] == "unit_rate" for edit in updated["estimator_edits"])


def test_review_required_line_can_be_resolved() -> None:
    result = _priced_quote()
    line = _find_line(result["lines"], "Class A / Friable Removal", "Chimney AIB hidden")

    response = client.post(
        f"/documents/{result['document_id']}/priced-quote-lines/{line['id']}/resolve-review",
        json={
            "reason": "Estimator accepted Class A provisional allowance for draft approval.",
            "user_id": "estimator-1",
            "assumptions_accepted": True,
            "exclusions_accepted": True,
        },
    )

    assert response.status_code == 200
    updated_line = next(row for row in response.json()["lines"] if row["id"] == line["id"])
    assert updated_line["review_status"] == "accepted"
    assert updated_line["review_required"] is False
    assert updated_line["approval_status"] == "ready_for_approval"
    assert updated_line["assumptions_accepted"] is True
    assert updated_line["exclusions_accepted"] is True
    assert updated_line["reviewed_by"] == "estimator-1"


def test_approval_remains_blocked_while_unresolved_lines_exist() -> None:
    result = _priced_quote()

    readiness = client.get(f"/documents/{result['document_id']}/approval-readiness")

    assert readiness.status_code == 200
    payload = readiness.json()
    assert payload["approval_status"] == "blocked"
    assert payload["unresolved_line_ids"]
    assert any(check["status"] == "blocked" for check in payload["checks"])


def test_approval_becomes_ready_after_required_lines_resolved() -> None:
    result = _priced_quote()
    document_id = result["document_id"]

    for line in result["lines"]:
        if line["review_status"] != "review_required":
            continue
        response = client.post(
            f"/documents/{document_id}/priced-quote-lines/{line['id']}/resolve-review",
            json={
                "reason": f"Estimator accepted review gate for {line['description']}.",
                "user_id": "estimator-1",
                "assumptions_accepted": True,
                "exclusions_accepted": True,
            },
        )
        assert response.status_code == 200

    readiness = client.get(f"/documents/{document_id}/approval-readiness")
    assert readiness.status_code == 200
    payload = readiness.json()
    assert payload["approval_status"] == "ready_for_approval"
    assert payload["unresolved_line_ids"] == []
    assert all(check["status"] == "passed" for check in payload["checks"])


def test_no_line_is_approved_by_default() -> None:
    result = _priced_quote()

    assert result["lines"]
    assert all(line["approval_status"] == "not_ready" for line in result["lines"])
    assert all(line["approval_status"] != "approved" for line in result["lines"])
