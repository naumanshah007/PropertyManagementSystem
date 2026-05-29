from __future__ import annotations

import fitz
from fastapi.testclient import TestClient
from auth_helpers import PLATFORM_ADMIN_HEADERS

from app.main import app


client = TestClient(app, headers=PLATFORM_ADMIN_HEADERS)


def _make_pdf(text: str) -> bytes:
    document = fitz.open()
    page = document.new_page()
    page.insert_text((72, 72), text)
    return document.tobytes()


def _create_org(name: str) -> dict:
    response = client.post(
        "/organisations",
        json={"name": name, "trading_name": name, "email": f"{name.lower().replace(' ', '')}@example.com"},
    )
    assert response.status_code == 200
    return response.json()


def test_create_and_list_organisation() -> None:
    org = _create_org("Phase 8 Test Organisation")

    assert org["id"].startswith("org-")
    assert org["name"] == "Phase 8 Test Organisation"
    assert org["company_profile"]["organisation_id"] == org["id"]
    assert org["settings"]["organisation_id"] == org["id"]

    listed = client.get("/organisations")
    assert listed.status_code == 200
    assert any(item["id"] == org["id"] for item in listed.json())


def test_create_organisation_user_and_role_assignment() -> None:
    org = _create_org("Phase 8 User Org")
    response = client.post(
        f"/organisations/{org['id']}/users",
        json={"email": "estimator@example.com", "name": "Demo Estimator", "role": "estimator"},
    )

    assert response.status_code == 200
    user = response.json()
    assert user["organisation_id"] == org["id"]
    assert user["role"] == "estimator"

    users = client.get(f"/organisations/{org['id']}/users")
    assert users.status_code == 200
    assert users.json()[0]["role"] == "estimator"


def test_pricebook_belongs_to_organisation() -> None:
    org = _create_org("Phase 8 Pricebook Org")

    response = client.post(
        f"/organisations/{org['id']}/pricebooks",
        json={"name": "Demo company pricebook", "version": "v1"},
    )

    assert response.status_code == 200
    pricebook = response.json()
    assert pricebook["organisation_id"] == org["id"]
    assert pricebook["rules"]
    assert all(rule["organisation_id"] == org["id"] for rule in pricebook["rules"])

    listed = client.get(f"/organisations/{org['id']}/pricebooks")
    assert listed.status_code == 200
    assert listed.json()[0]["organisation_id"] == org["id"]


def test_organisation_specific_document_storage_and_access_separation() -> None:
    org_a = _create_org("Phase 8 Storage Org A")
    org_b = _create_org("Phase 8 Storage Org B")

    upload = client.post(
        f"/organisations/{org_a['id']}/documents/upload",
        files={"file": ("org-a.pdf", _make_pdf("Asbestos Demolition Survey Register"), "application/pdf")},
    )
    assert upload.status_code == 200
    document = upload.json()
    assert document["organisation_id"] == org_a["id"]
    assert f"/organisations/{org_a['id']}/documents/" in document["stored_path"]

    own_lookup = client.get(f"/organisations/{org_a['id']}/documents/{document['document_id']}")
    assert own_lookup.status_code == 200
    assert own_lookup.json()["organisation_id"] == org_a["id"]

    cross_lookup = client.get(f"/organisations/{org_b['id']}/documents/{document['document_id']}")
    assert cross_lookup.status_code == 404


def test_settings_are_organisation_scoped() -> None:
    org = _create_org("Phase 8 Settings Org")
    response = client.post(
        f"/organisations/{org['id']}/settings",
        json={
            "gst_rate": 0.12,
            "default_currency": "AUD",
            "quote_prefix": "ACME",
            "require_review_for_class_a": True,
            "require_review_for_no_access": False,
        },
    )
    assert response.status_code == 200
    assert response.json()["organisation_id"] == org["id"]
    assert response.json()["default_currency"] == "AUD"

    settings = client.get(f"/organisations/{org['id']}/settings")
    assert settings.status_code == 200
    assert settings.json()["quote_prefix"] == "ACME"
