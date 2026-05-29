"""Tests for the org-onboarding refinement: every new org gets a fully editable
RAS-1285 starter pricebook so admins land on real prices, not an empty state.
"""

from __future__ import annotations

from fastapi.testclient import TestClient
from auth_helpers import PLATFORM_ADMIN_HEADERS

from app.main import app
from app.pricebook import get_seed_pricebook


client = TestClient(app, headers=PLATFORM_ADMIN_HEADERS)


def _create_org(name: str) -> dict:
    response = client.post(
        "/organisations",
        json={"name": name, "trading_name": name, "email": f"{name.lower().replace(' ', '')}@example.com"},
    )
    assert response.status_code == 200, response.text
    return response.json()


def test_new_organisation_auto_creates_starter_pricebook() -> None:
    org = _create_org("Onboarding Auto-Seed Co")

    pricebooks = client.get(f"/organisations/{org['id']}/pricebooks")
    assert pricebooks.status_code == 200
    payload = pricebooks.json()

    assert len(payload) == 1, "Expected exactly one auto-seeded pricebook"
    starter = payload[0]
    assert starter["active"] is True
    assert "starter pricebook" in starter["name"].lower()
    assert starter["version"] == "revolve-ras-1285-seed-v1"


def test_starter_pricebook_contains_all_ten_seed_rules() -> None:
    org = _create_org("Ten Rules Co")
    pricebooks = client.get(f"/organisations/{org['id']}/pricebooks").json()
    starter = pricebooks[0]

    seed_ids = {rule.id for rule in get_seed_pricebook()}
    starter_ids = {rule["id"] for rule in starter["rules"]}
    assert starter_ids == seed_ids, f"Starter pricebook missing rules: {seed_ids - starter_ids}"


def test_starter_pricebook_minimum_charge_carries_through() -> None:
    """The $2,500 small-room floor on Class B rules must survive the seed → org clone."""
    org = _create_org("Min Charge Co")
    pricebooks = client.get(f"/organisations/{org['id']}/pricebooks").json()
    rules = pricebooks[0]["rules"]

    bitumen = next(r for r in rules if r["id"] == "pb-class-b-bitumen-sqm")
    assert bitumen["minimum_charge"] == 2500.0
    assert bitumen["unit_rate"] == 195.0


def test_creating_a_second_pricebook_deactivates_the_starter() -> None:
    """SaaS-style semantics: newest pricebook is active; older ones become history."""
    org = _create_org("Multi Pricebook Co")
    starter = client.get(f"/organisations/{org['id']}/pricebooks").json()[0]
    assert starter["active"] is True

    second = client.post(
        f"/organisations/{org['id']}/pricebooks",
        json={"name": "FY26 pricebook", "version": "fy26-v1", "rules": []},
    )
    assert second.status_code == 200

    all_pricebooks = client.get(f"/organisations/{org['id']}/pricebooks").json()
    assert len(all_pricebooks) == 2

    by_version = {p["version"]: p for p in all_pricebooks}
    assert by_version["fy26-v1"]["active"] is True
    assert by_version["revolve-ras-1285-seed-v1"]["active"] is False


def test_starter_pricebook_is_used_immediately_in_pricing_flow() -> None:
    """End-to-end: create org → upload survey → starter rates drive the priced quote."""
    import fitz

    org = _create_org("E2E Pricing Co")

    document = fitz.open()
    page = document.new_page()
    page.insert_text(
        (72, 72),
        "Asbestos Demolition Survey Register "
        "R10-11 External / Building Envelope Flat cladding Fibre Cement Sheet - Flat Sheet 320 sqm Class B Positive",
    )
    pdf_bytes = document.tobytes()

    upload = client.post(
        f"/organisations/{org['id']}/documents/upload",
        files={"file": ("e2e-onboarding.pdf", pdf_bytes, "application/pdf")},
    )
    assert upload.status_code == 200
    document_id = upload.json()["document_id"]

    assert client.post(f"/documents/{document_id}/extract-register").status_code == 200
    assert client.post(f"/documents/{document_id}/generate-quote-candidates").status_code == 200
    priced = client.post(f"/documents/{document_id}/price-quote-candidates")
    assert priced.status_code == 200

    payload = priced.json()
    assert payload["pricebook_version"] == "revolve-ras-1285-seed-v1"
    # The fibre cement seed rate is $80/sqm; the org's starter clone preserves it.
    class_b_lines = [
        line for line in payload["lines"]
        if line["section"] == "Class B Removal" and "Flat cladding" in line["description"]
    ]
    assert class_b_lines, "Expected the Class B fibre cement line to be priced"
    assert class_b_lines[0]["unit_rate"] == 80.0
