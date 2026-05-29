"""Auth + RBAC enforcement tests.

Exercises token issuance/validation and the role/organisation boundaries:
platform admin vs org admin vs estimator vs viewer, cross-org isolation,
401 for unauthenticated, 403 for forbidden, and the demo-seed gate.
"""

from __future__ import annotations

import fitz
import pytest
from fastapi.testclient import TestClient

from auth_helpers import auth_headers, make_token
from app.auth_tokens import decode_access_token
from app.main import app


# No default headers — every request sets its own auth explicitly.
client = TestClient(app)

PLATFORM = auth_headers("platform_admin")


def _make_pdf() -> bytes:
    document = fitz.open()
    page = document.new_page()
    page.insert_text(
        (72, 72),
        "Asbestos Demolition Survey Register "
        "R10 External Flat cladding Fibre Cement Sheet - Flat Sheet 320 sqm Class B Positive",
    )
    return document.tobytes()


def _create_org(name: str) -> str:
    response = client.post(
        "/organisations",
        json={"name": name, "trading_name": name, "email": f"{name.lower().replace(' ', '')}@example.com"},
        headers=PLATFORM,
    )
    assert response.status_code == 200, response.text
    return response.json()["id"]


# --------------------------------------------------------------------------- #
# Token issuance + validation
# --------------------------------------------------------------------------- #


def test_login_returns_token_with_expiry() -> None:
    response = client.post("/auth/login", json={"email": "admin@privexa.co", "password": "admin123"})
    assert response.status_code == 200
    token = response.json()["token"]
    claims = decode_access_token(token)
    assert claims["role"] == "platform_admin"
    assert claims["email"] == "admin@privexa.co"
    assert claims["exp"] > claims["iat"]


def test_wrong_password_fails() -> None:
    response = client.post("/auth/login", json={"email": "admin@privexa.co", "password": "nope"})
    assert response.status_code == 401


def test_invalid_token_is_rejected() -> None:
    response = client.get("/organisations", headers={"Authorization": "Bearer not.a.realtoken"})
    assert response.status_code == 401


def test_expired_token_is_rejected() -> None:
    expired = make_token("platform_admin", expires_minutes=-1)
    response = client.get("/organisations", headers={"Authorization": f"Bearer {expired}"})
    assert response.status_code == 401


def test_unauthenticated_request_returns_401() -> None:
    assert client.get("/organisations").status_code == 401
    org_id = _create_org("Unauth Probe Co")
    assert client.get(f"/organisations/{org_id}/jobs").status_code == 401


# --------------------------------------------------------------------------- #
# Platform admin
# --------------------------------------------------------------------------- #


def test_platform_admin_can_access_admin_endpoints() -> None:
    assert client.get("/organisations", headers=PLATFORM).status_code == 200
    org_id = _create_org("Platform Reach Co")
    assert client.get(f"/organisations/{org_id}/jobs", headers=PLATFORM).status_code == 200
    assert client.get(f"/organisations/{org_id}/pricebooks", headers=PLATFORM).status_code == 200


def test_non_platform_admin_cannot_create_orgs() -> None:
    org_id = _create_org("Org Admin Create Block Co")
    headers = auth_headers("organisation_admin", org_id)
    assert client.post(
        "/organisations",
        json={"name": "Sneaky", "trading_name": "Sneaky", "email": "s@example.com"},
        headers=headers,
    ).status_code == 403
    # Listing all orgs is platform-only too.
    assert client.get("/organisations", headers=headers).status_code == 403


# --------------------------------------------------------------------------- #
# Organisation admin — own org vs another org
# --------------------------------------------------------------------------- #


def test_org_admin_can_access_own_org() -> None:
    org_id = _create_org("Own Org Co")
    headers = auth_headers("organisation_admin", org_id)
    assert client.get(f"/organisations/{org_id}", headers=headers).status_code == 200
    assert client.get(f"/organisations/{org_id}/pricebooks", headers=headers).status_code == 200
    assert client.get(f"/organisations/{org_id}/settings", headers=headers).status_code == 200
    assert client.get(f"/organisations/{org_id}/jobs", headers=headers).status_code == 200


def test_org_admin_cannot_access_another_org() -> None:
    org_a = _create_org("Tenant A Co")
    org_b = _create_org("Tenant B Co")
    headers_a = auth_headers("organisation_admin", org_a)

    assert client.get(f"/organisations/{org_b}", headers=headers_a).status_code == 403
    assert client.get(f"/organisations/{org_b}/pricebooks", headers=headers_a).status_code == 403
    assert client.get(f"/organisations/{org_b}/jobs", headers=headers_a).status_code == 403
    assert client.get(f"/organisations/{org_b}/settings", headers=headers_a).status_code == 403


# --------------------------------------------------------------------------- #
# Estimator + viewer on jobs
# --------------------------------------------------------------------------- #


def test_estimator_can_create_and_process_jobs_in_own_org() -> None:
    org_id = _create_org("Estimator Jobs Co")
    headers = auth_headers("estimator", org_id)

    created = client.post(
        f"/organisations/{org_id}/jobs",
        files={"file": ("s.pdf", _make_pdf(), "application/pdf")},
        data={"client_name": "Estimator Client"},
        headers=headers,
    )
    assert created.status_code == 200, created.text
    job_id = created.json()["id"]

    processed = client.post(f"/organisations/{org_id}/jobs/{job_id}/process", headers=headers)
    assert processed.status_code == 200, processed.text


def test_viewer_cannot_mutate_jobs_but_can_read() -> None:
    org_id = _create_org("Viewer Jobs Co")
    viewer = auth_headers("viewer", org_id)

    # Read is allowed.
    assert client.get(f"/organisations/{org_id}/jobs", headers=viewer).status_code == 200

    # Mutation is forbidden.
    created = client.post(
        f"/organisations/{org_id}/jobs",
        files={"file": ("s.pdf", _make_pdf(), "application/pdf")},
        data={"client_name": "Nope"},
        headers=viewer,
    )
    assert created.status_code == 403


def test_estimator_cannot_create_jobs_in_another_org() -> None:
    org_a = _create_org("Estimator Home Co")
    org_b = _create_org("Estimator Foreign Co")
    estimator_a = auth_headers("estimator", org_a)

    blocked = client.post(
        f"/organisations/{org_b}/jobs",
        files={"file": ("s.pdf", _make_pdf(), "application/pdf")},
        data={"client_name": "Cross"},
        headers=estimator_a,
    )
    assert blocked.status_code == 403


# --------------------------------------------------------------------------- #
# Cross-org document isolation
# --------------------------------------------------------------------------- #


def test_cross_org_document_access_is_blocked() -> None:
    org_a = _create_org("Doc Owner Co")
    org_b = _create_org("Doc Intruder Co")
    estimator_a = auth_headers("estimator", org_a)

    created = client.post(
        f"/organisations/{org_a}/jobs",
        files={"file": ("s.pdf", _make_pdf(), "application/pdf")},
        data={"client_name": "Owner"},
        headers=estimator_a,
    )
    assert created.status_code == 200
    document_id = created.json()["document_id"]
    client.post(f"/organisations/{org_a}/jobs/{created.json()['id']}/process", headers=estimator_a)

    # A user from org B must not read org A's document pipeline.
    intruder = auth_headers("organisation_admin", org_b)
    assert client.get(f"/documents/{document_id}/priced-quote-lines", headers=intruder).status_code == 403
    assert client.get(f"/documents/{document_id}/register-items", headers=intruder).status_code == 403
    # ...but the document's own org can.
    assert client.get(f"/documents/{document_id}/register-items", headers=estimator_a).status_code == 200


# --------------------------------------------------------------------------- #
# Demo seed gate
# --------------------------------------------------------------------------- #


def test_demo_seed_blocked_when_disabled(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("DEMO_SEED_ENABLED", "false")
    assert client.post("/demo/seed").status_code == 403
    assert client.get("/demo/users").status_code == 403
