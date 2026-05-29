"""Job lifecycle: the operator-facing unit of work.

Covers create (org-scoped upload + intake metadata), one-click process
orchestration (extract → candidates → price), management-plan rejection,
approval gating, and that the jobs list reflects status.
"""

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


def _create_org(name: str) -> str:
    response = client.post(
        "/organisations",
        json={"name": name, "trading_name": name, "email": f"{name.lower().replace(' ', '')}@example.com"},
    )
    assert response.status_code == 200, response.text
    return response.json()["id"]


def _demolition_pdf() -> bytes:
    return _make_pdf(
        [
            "Asbestos Demolition Survey Register",
            "R10-11 External / Building Envelope Flat cladding Fibre Cement Sheet - Flat Sheet 320 sqm Class B Positive",
            "R10 Inside room Power box Power box and systems 1 sqm Presume No Access Class B",
            "R11 Inside room Chimney AIB hidden Insulating Board 4 pieces Class A Limited Access",
        ]
    )


def _create_job(org_id: str, pdf: bytes, *, client_name: str = "Acme School") -> dict:
    response = client.post(
        f"/organisations/{org_id}/jobs",
        files={"file": ("survey.pdf", pdf, "application/pdf")},
        data={"client_name": client_name, "site_address": "1 Test Rd, Auckland", "created_by": "test@privexa.co"},
    )
    assert response.status_code == 200, response.text
    return response.json()


def test_create_job_captures_intake_and_classification() -> None:
    org_id = _create_org("Job Create Co")
    job = _create_job(org_id, _demolition_pdf())

    assert job["status"] == "uploaded"
    assert job["client_name"] == "Acme School"
    assert job["site_address"] == "1 Test Rd, Auckland"
    assert job["survey_type"] == "demolition_survey"
    assert job["quotable"] is True
    assert job["document_id"]
    assert job["created_by"] == "test@privexa.co"


def test_process_job_orchestrates_pipeline_and_snapshots() -> None:
    org_id = _create_org("Job Process Co")
    job = _create_job(org_id, _demolition_pdf())

    processed = client.post(f"/organisations/{org_id}/jobs/{job['id']}/process")
    assert processed.status_code == 200, processed.text
    payload = processed.json()

    assert payload["priced_quote"] is not None
    assert payload["priced_quote"]["lines"], "Expected priced lines"

    updated = payload["job"]
    # Class A + no-access lines require review, so the job lands in_review.
    assert updated["status"] == "in_review"
    assert updated["register_items"] > 0
    assert updated["review_required"] >= 1
    assert updated["total_inc_gst"] is not None


def test_jobs_list_reflects_status() -> None:
    org_id = _create_org("Job List Co")
    job = _create_job(org_id, _demolition_pdf())
    client.post(f"/organisations/{org_id}/jobs/{job['id']}/process")

    listing = client.get(f"/organisations/{org_id}/jobs")
    assert listing.status_code == 200
    rows = listing.json()
    assert len(rows) == 1
    assert rows[0]["id"] == job["id"]
    assert rows[0]["status"] == "in_review"
    assert rows[0]["client_name"] == "Acme School"


def test_management_plan_is_rejected_not_priced() -> None:
    org_id = _create_org("Job Reject Co")
    plan_pdf = _make_pdf(
        [
            "Asbestos Management Plan",
            "This document is a management plan for ongoing asbestos containing materials.",
        ]
    )
    job = _create_job(org_id, plan_pdf, client_name="Plan Holder")
    assert job["quotable"] is False
    assert job["survey_type"] == "management_plan"

    processed = client.post(f"/organisations/{org_id}/jobs/{job['id']}/process")
    assert processed.status_code == 200, processed.text
    payload = processed.json()
    assert payload["priced_quote"] is None
    assert payload["job"]["status"] == "rejected"
    assert payload["job"]["rejected_reason"]


def test_approve_is_blocked_until_reviews_resolved() -> None:
    org_id = _create_org("Job Approve Co")
    job = _create_job(org_id, _demolition_pdf())
    client.post(f"/organisations/{org_id}/jobs/{job['id']}/process")

    # Class A / no-access lines are unresolved → approval must be blocked.
    blocked = client.post(f"/organisations/{org_id}/jobs/{job['id']}/approve")
    assert blocked.status_code == 409


def test_get_missing_job_returns_404() -> None:
    org_id = _create_org("Job Missing Co")
    missing = client.get(f"/organisations/{org_id}/jobs/job-does-not-exist")
    assert missing.status_code == 404
