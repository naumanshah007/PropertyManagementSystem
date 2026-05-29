from __future__ import annotations

import fitz
from fastapi.testclient import TestClient
from auth_helpers import PLATFORM_ADMIN_HEADERS

from app.demo_auth import TEST_ORGANISATION_ID
from app.main import app


client = TestClient(app, headers=PLATFORM_ADMIN_HEADERS)


def _make_pdf(pages: list[str]) -> bytes:
    document = fitz.open()
    for text in pages:
        page = document.new_page()
        page.insert_text((72, 72), text)
    return document.tobytes()


def _processed_document_id() -> str:
    pdf_bytes = _make_pdf(
        [
            "Asbestos Demolition Survey Register",
            "R10-11 External / Building Envelope Flat cladding Fibre Cement Sheet - Flat Sheet 320 sqm Class B Positive",
            "R10 Inside room Power box Power box and systems 1 sqm Presume No Access Class B",
            "R11 Inside room Chimney AIB hidden Insulating Board 4 pieces Class A Limited Access",
            "R30 Inside room floor tile NAD No Asbestos Detected",
        ]
    )
    upload = client.post(
        "/documents/upload",
        files={"file": ("magic-demo.pdf", pdf_bytes, "application/pdf")},
    )
    assert upload.status_code == 200
    document_id = upload.json()["document_id"]
    assert client.post(f"/documents/{document_id}/extract-register").status_code == 200
    assert client.post(f"/documents/{document_id}/generate-quote-candidates").status_code == 200
    assert client.post(f"/documents/{document_id}/price-quote-candidates").status_code == 200
    return document_id


def test_demo_users_seeded_and_passwords_hashed() -> None:
    response = client.post("/demo/seed")
    assert response.status_code == 200

    users = client.get("/demo/users")
    assert users.status_code == 200
    payload = users.json()
    emails = {user["email"] for user in payload}
    assert {"admin@privexa.co", "test@privexa.co"}.issubset(emails)
    # Per security hardening (Phase F), /demo/users never exposes password material — verify omission
    assert all("password_hash" not in user for user in payload)
    assert all("password_salt" not in user for user in payload)

    # Verify passwords are actually hashed by inspecting the storage layer directly
    from app.demo_auth import load_demo_auth_users

    stored_users = load_demo_auth_users()
    assert stored_users, "Expected seeded demo users in storage"
    assert all(user.password_hash != "admin123" for user in stored_users)
    assert all(user.password_salt != "admin123" for user in stored_users)
    assert all(len(user.password_hash) >= 32 for user in stored_users), "Hashes look too short"


def test_super_admin_and_test_org_admin_login_work() -> None:
    admin = client.post("/auth/login", json={"email": "admin@privexa.co", "password": "admin123"})
    assert admin.status_code == 200
    assert admin.json()["role"] == "platform_admin"
    assert admin.json()["default_route"] == "/admin"

    org_admin = client.post("/auth/login", json={"email": "test@privexa.co", "password": "admin123"})
    assert org_admin.status_code == 200
    assert org_admin.json()["role"] == "organisation_admin"
    assert org_admin.json()["organisation_id"] == TEST_ORGANISATION_ID
    assert org_admin.json()["default_route"] == "/dashboard"


def test_wrong_password_fails() -> None:
    response = client.post("/auth/login", json={"email": "admin@privexa.co", "password": "wrong"})
    assert response.status_code == 401


def test_test_org_has_seeded_pricebook_and_role_metadata() -> None:
    seed = client.post("/demo/seed")
    assert seed.status_code == 200

    pricebooks = client.get(f"/organisations/{TEST_ORGANISATION_ID}/pricebooks")
    assert pricebooks.status_code == 200
    # The test org now has 2 pricebooks: the auto-seeded RAS-1285 starter (deactivated by
    # the demo-auth seed) and the demo-auth full company pricebook (active). Find the
    # one the demo-auth seeder writes.
    payload = pricebooks.json()
    active = next((p for p in payload if p["active"]), payload[-1])
    rule_names = {rule["name"] for rule in active["rules"]}
    assert "Fibre cement sheet per sqm" in rule_names
    assert "Minimum job charge" in rule_names
    assert "GST" in rule_names
    assert "Margin" in rule_names

    users = client.get(f"/organisations/{TEST_ORGANISATION_ID}/users")
    assert users.status_code == 200
    assert any(user["role"] == "organisation_admin" for user in users.json())


def test_magic_extraction_summary_is_produced() -> None:
    document_id = _processed_document_id()

    response = client.get(f"/documents/{document_id}/magic-summary")

    assert response.status_code == 200
    summary = response.json()
    assert summary["survey_type"] == "Asbestos Demolition Survey"
    assert summary["register_items_extracted"] > 0
    assert summary["quote_candidates_generated"] > 0
    assert summary["priced_lines_generated"] > 0
    assert summary["class_a_items"] >= 1
    assert summary["class_b_items"] >= 1
    assert summary["no_access_items"] >= 1
    assert summary["total_extracted_sqm"] >= 320
    assert "materials" in summary["magic_entities"]
    assert "pricing_triggers" in summary["magic_entities"]
