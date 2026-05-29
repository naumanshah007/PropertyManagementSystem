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


def _create_pricebook(org_id: str) -> dict:
    response = client.post(
        f"/organisations/{org_id}/pricebooks",
        json={"name": "Company asbestos pricebook", "version": "company-v1", "rules": []},
    )
    assert response.status_code == 200
    return response.json()


def _class_b_rule(rate: float = 88.0) -> dict:
    return {
        "name": "Company Class B fibre cement per sqm",
        "category": "Class B Removal",
        "section": "Class B Removal",
        "material_match": "fibre cement sheet",
        "class_match": "Class B",
        "access_match": "normal",
        "pricing_method": "per_sqm",
        "unit": "sqm",
        "unit_rate": rate,
        "risk_multiplier": 1.0,
        "margin": 0.10,
        "gst_taxable": True,
        "minimum_charge": 500.0,
        "assumptions": ["Company Class B rule assumption."],
        "exclusions": ["Company Class B rule exclusion."],
        "review_required": False,
        "mandatory": True,
        "active": True,
    }


def _upload_extract_generate_price(org_id: str) -> dict:
    upload = client.post(
        f"/organisations/{org_id}/documents/upload",
        files={
            "file": (
                "org-pricebook.pdf",
                _make_pdf(
                    "Asbestos Demolition Survey Register "
                    "R10-11 External / Building Envelope Flat cladding Fibre Cement Sheet - Flat Sheet 320 sqm Class B Positive"
                ),
                "application/pdf",
            )
        },
    )
    assert upload.status_code == 200
    document_id = upload.json()["document_id"]
    assert client.post(f"/documents/{document_id}/extract-register").status_code == 200
    assert client.post(f"/documents/{document_id}/generate-quote-candidates").status_code == 200
    priced = client.post(f"/documents/{document_id}/price-quote-candidates")
    assert priced.status_code == 200
    return priced.json()


def test_create_edit_deactivate_and_activate_pricebook_rule() -> None:
    org = _create_org("Phase 10 Rule Org")
    pricebook = _create_pricebook(org["id"])

    created = client.post(
        f"/organisations/{org['id']}/pricebooks/{pricebook['id']}/rules",
        json=_class_b_rule(),
    )
    assert created.status_code == 200
    rule = created.json()
    assert rule["name"] == "Company Class B fibre cement per sqm"
    assert rule["material_match"] == "fibre cement sheet"
    assert rule["assumptions"] == ["Company Class B rule assumption."]

    edited = client.patch(
        f"/organisations/{org['id']}/pricebooks/{pricebook['id']}/rules/{rule['id']}",
        json={"unit_rate": 95.0, "exclusions": ["Updated exclusion persists."]},
    )
    assert edited.status_code == 200
    assert edited.json()["unit_rate"] == 95.0
    assert edited.json()["exclusions"] == ["Updated exclusion persists."]

    deleted = client.delete(f"/organisations/{org['id']}/pricebooks/{pricebook['id']}/rules/{rule['id']}")
    assert deleted.status_code == 200
    assert deleted.json()["active"] is False

    activated = client.post(f"/organisations/{org['id']}/pricebooks/{pricebook['id']}/activate")
    assert activated.status_code == 200
    assert activated.json()["active"] is True


def test_active_organisation_pricebook_is_used_in_pricing() -> None:
    org = _create_org("Phase 10 Pricing Org")
    pricebook = _create_pricebook(org["id"])
    created = client.post(
        f"/organisations/{org['id']}/pricebooks/{pricebook['id']}/rules",
        json=_class_b_rule(rate=88.0),
    )
    assert created.status_code == 200

    result = _upload_extract_generate_price(org["id"])
    class_b_lines = [
        line
        for line in result["lines"]
        if line["section"] == "Class B Removal" and "Flat cladding" in line["description"]
    ]

    assert class_b_lines
    line = class_b_lines[0]
    assert result["organisation_id"] == org["id"]
    assert result["pricebook_version"] == "company-v1"
    assert line["unit_rate"] == 88.0
    assert line["pricing_rule_name"] == "Company Class B fibre cement per sqm"
    assert "Company Class B rule assumption." in line["assumptions"]
    assert "Company Class B rule exclusion." in line["exclusions"]


def test_seed_pricebook_fallback_still_prices_default_documents() -> None:
    upload = client.post(
        "/documents/upload",
        files={
            "file": (
                "fallback-pricebook.pdf",
                _make_pdf(
                    "Asbestos Demolition Survey Register "
                    "R10-11 External / Building Envelope Flat cladding Fibre Cement Sheet - Flat Sheet 320 sqm Class B Positive"
                ),
                "application/pdf",
            )
        },
    )
    assert upload.status_code == 200
    document_id = upload.json()["document_id"]
    assert client.post(f"/documents/{document_id}/extract-register").status_code == 200
    assert client.post(f"/documents/{document_id}/generate-quote-candidates").status_code == 200
    priced = client.post(f"/documents/{document_id}/price-quote-candidates")
    assert priced.status_code == 200

    class_b_line = next(line for line in priced.json()["lines"] if line["section"] == "Class B Removal")
    assert priced.json()["pricebook_version"] == "revolve-ras-1285-seed-v1"
    assert class_b_line["pricing_rule_id"] == "pb-class-b-fibre-cement-sqm"
    assert class_b_line["unit_rate"] == 80.0
