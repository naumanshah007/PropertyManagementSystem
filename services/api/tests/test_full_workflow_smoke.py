from __future__ import annotations

from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from auth_helpers import PLATFORM_ADMIN_HEADERS

from app.main import app


client = TestClient(app, headers=PLATFORM_ADMIN_HEADERS)
SAMPLE_SURVEY = Path(__file__).resolve().parents[3] / "samples" / "surveys" / "38-Asbestos-Survey-_Rev_0.pdf"


@pytest.mark.skipif(
    not SAMPLE_SURVEY.exists(),
    reason="Golden survey missing: add samples/surveys/38-Asbestos-Survey-_Rev_0.pdf to enable full workflow smoke test.",
)
def test_tauraroa_full_vendor_demo_workflow_smoke() -> None:
    with SAMPLE_SURVEY.open("rb") as sample:
        upload = client.post(
            "/documents/upload",
            files={"file": (SAMPLE_SURVEY.name, sample.read(), "application/pdf")},
        )
    assert upload.status_code == 200
    document_id = upload.json()["document_id"]
    assert upload.json()["page_count"] == 50

    extraction = client.post(f"/documents/{document_id}/extract-register")
    assert extraction.status_code == 200
    assert extraction.json()["items"]

    candidates = client.post(f"/documents/{document_id}/generate-quote-candidates")
    assert candidates.status_code == 200
    assert candidates.json()["candidates"]

    priced = client.post(f"/documents/{document_id}/price-quote-candidates")
    assert priced.status_code == 200
    priced_payload = priced.json()
    assert priced_payload["approval_status"] == "blocked"

    class_b_line = next(line for line in priced_payload["lines"] if line["section"] == "Class B Removal")
    edited = client.post(
        f"/documents/{document_id}/priced-quote-lines/{class_b_line['id']}/edit",
        json={
            "unit_rate": class_b_line["unit_rate"] + 1,
            "reason": "Smoke test estimator rate adjustment.",
            "user_id": "smoke-estimator",
        },
    )
    assert edited.status_code == 200
    latest = edited.json()

    for line in latest["lines"]:
        if line["excluded_from_pricing"]:
            continue
        resolved = client.post(
            f"/documents/{document_id}/priced-quote-lines/{line['id']}/resolve-review",
            json={
                "reason": f"Smoke test accepted {line['description']}.",
                "user_id": "smoke-estimator",
                "assumptions_accepted": True,
                "exclusions_accepted": True,
            },
        )
        assert resolved.status_code == 200

    readiness = client.get(f"/documents/{document_id}/approval-readiness")
    assert readiness.status_code == 200
    assert readiness.json()["approval_status"] == "ready_for_approval"

    exported = client.post(
        f"/documents/{document_id}/export-quote",
        json={
            "client_name": "Tauraroa Area School",
            "project_name": "Vendor demo asbestos quote",
            "site_address": "Tauraroa Area School, Northland, New Zealand",
            "quote_number": "TQ-SMOKE-001",
            "scope_summary": "Vendor demo reviewed quote package from the real asbestos demolition survey.",
        },
    )
    assert exported.status_code == 200
    assert exported.json()["quote_number"] == "TQ-SMOKE-001"
    assert "Source evidence appendix" in exported.json()["html_content"]

    pdf = client.get(f"/documents/{document_id}/export-quote/pdf")
    assert pdf.status_code == 200
    assert pdf.content.startswith(b"%PDF")
