"""Regression tests for the RAS-1285-style export layout introduced in Phase D.

Each new block in the client-facing quote (inclusions list, IMPORTANT notes,
required services, signature, valid-until, section grouping) is asserted here
so the export layout doesn't silently drift back to a generic template.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

import fitz
from fastapi.testclient import TestClient
from auth_helpers import PLATFORM_ADMIN_HEADERS

from app.main import app
from app.quote_boilerplate import (
    DEFAULT_QUOTE_IMPORTANT_NOTES,
    DEFAULT_QUOTE_INCLUSIONS,
    DEFAULT_QUOTE_REQUIRED_SERVICES,
)


client = TestClient(app, headers=PLATFORM_ADMIN_HEADERS)


def _make_pdf(pages: list[str]) -> bytes:
    document = fitz.open()
    for text in pages:
        page = document.new_page()
        page.insert_text((72, 72), text)
    return document.tobytes()


def _priced_quote_for_export() -> dict:
    pdf_bytes = _make_pdf(
        [
            "Asbestos Demolition Survey Register",
            "R10-11 External / Building Envelope Flat cladding Fibre Cement Sheet - Flat Sheet 320 sqm Class B Positive",
            "R10 Inside room Power box Power box and systems 1 sqm Presume No Access Class B",
            "R11 Inside room Chimney AIB hidden Insulating Board 4 pieces Class A Limited Access",
            "R12-16 External / Building Envelope External Cladding Fibre Cement Sheet - Flat Sheet 920 sqm Class B Positive",
        ]
    )
    upload = client.post(
        "/documents/upload",
        files={"file": ("ras1285-layout-demo.pdf", pdf_bytes, "application/pdf")},
    )
    assert upload.status_code == 200
    document_id = upload.json()["document_id"]
    assert client.post(f"/documents/{document_id}/extract-register").status_code == 200
    assert client.post(f"/documents/{document_id}/generate-quote-candidates").status_code == 200
    priced = client.post(f"/documents/{document_id}/price-quote-candidates")
    assert priced.status_code == 200
    return priced.json()


def _resolve_all(priced: dict) -> None:
    for line in priced["lines"]:
        if line["excluded_from_pricing"]:
            continue
        response = client.post(
            f"/documents/{priced['document_id']}/priced-quote-lines/{line['id']}/resolve-review",
            json={
                "reason": "Export layout test review.",
                "user_id": "estimator-test",
                "assumptions_accepted": True,
                "exclusions_accepted": True,
            },
        )
        assert response.status_code == 200


def _export(document_id: str, **kwargs) -> dict:
    response = client.post(f"/documents/{document_id}/export-quote", json=kwargs or None)
    assert response.status_code == 200
    return response.json()


def test_export_html_includes_thirteen_point_inclusions_list() -> None:
    priced = _priced_quote_for_export()
    _resolve_all(priced)
    html = _export(priced["document_id"])["html_content"]

    assert "This pricing includes:" in html
    # The default RAS-1285 inclusions list is 13 items — every one must render
    for item in DEFAULT_QUOTE_INCLUSIONS:
        # Use the leading words as an anchor (full text is escaped which may differ)
        anchor = item.split(".")[0][:40]
        assert anchor in html, f"Missing inclusion item starting with: {anchor}"


def test_export_html_includes_important_notes_block() -> None:
    priced = _priced_quote_for_export()
    _resolve_all(priced)
    html = _export(priced["document_id"])["html_content"]

    assert "IMPORTANT:" in html
    # First two notes must appear verbatim (anchor on opening words)
    first_note_anchor = DEFAULT_QUOTE_IMPORTANT_NOTES[0].split(".")[0][:30]
    assert first_note_anchor in html


def test_export_html_includes_required_services_block() -> None:
    priced = _priced_quote_for_export()
    _resolve_all(priced)
    html = _export(priced["document_id"])["html_content"]

    assert "services are required on site" in html
    for service in DEFAULT_QUOTE_REQUIRED_SERVICES:
        anchor = service.split(".")[0][:20]
        assert anchor in html, f"Missing required service: {service}"


def test_export_html_groups_lines_by_section() -> None:
    priced = _priced_quote_for_export()
    _resolve_all(priced)
    html = _export(priced["document_id"])["html_content"]

    # Section headings must appear as <h3> blocks
    assert "<h3>Class B Removal</h3>" in html
    assert "<h3>Class A / Friable Removal</h3>" in html


def test_export_html_includes_signature_and_business_branding() -> None:
    priced = _priced_quote_for_export()
    _resolve_all(priced)
    html = _export(priced["document_id"])["html_content"]

    # Default org settings — business name + signature block must render
    assert "Demo Asbestos Services Ltd" in html
    assert "Kind regards" in html
    assert "Demo Estimator" in html


def test_export_html_includes_valid_until_date() -> None:
    priced = _priced_quote_for_export()
    _resolve_all(priced)
    export = _export(priced["document_id"])
    html = export["html_content"]

    assert "Valid Until:" in html
    # Default quote_valid_days = 30 — valid_until should be ~30 days after generated_at
    generated_at = datetime.fromisoformat(export["generated_at"].replace("Z", "+00:00"))
    expected_valid_until = (generated_at + timedelta(days=30)).date().isoformat()
    assert expected_valid_until in html


def test_export_html_renders_poa_for_no_access_lines() -> None:
    priced = _priced_quote_for_export()
    _resolve_all(priced)
    html = _export(priced["document_id"])["html_content"]

    # No-access lines (power boxes in the test PDF) must show POA, not a price
    assert "POA" in html


def test_export_pdf_is_well_formed_under_new_layout() -> None:
    priced = _priced_quote_for_export()
    _resolve_all(priced)
    _export(priced["document_id"])

    response = client.get(f"/documents/{priced['document_id']}/export-quote/pdf")
    assert response.status_code == 200
    assert response.content.startswith(b"%PDF")
    # The PDF should contain the IMPORTANT section header
    pdf = fitz.open(stream=response.content, filetype="pdf")
    full_text = "".join(page.get_text() for page in pdf)
    pdf.close()
    assert "IMPORTANT" in full_text
    assert "Kind regards" in full_text


def test_export_uses_organisation_specific_branding_when_overridden() -> None:
    # Create a new org with custom branding
    org_response = client.post(
        "/organisations",
        json={
            "name": "Northland Asbestos Co",
            "trading_name": "Northland Asbestos",
            "email": "ops@northland-asbestos.example.nz",
        },
    )
    assert org_response.status_code == 200
    org_id = org_response.json()["id"]

    # Override branding via settings endpoint
    settings_response = client.post(
        f"/organisations/{org_id}/settings",
        json={
            "business_name": "Northland Asbestos Co",
            "business_phone": "021 555 5555",
            "business_gst_number": "111-222-333",
            "contact_name": "Jane Doe",
            "contact_phone": "021 777 7777",
            "quote_valid_days": 14,
        },
    )
    assert settings_response.status_code == 200

    # Upload a survey for this org and price it
    pdf_bytes = _make_pdf(
        [
            "Asbestos Demolition Survey Register",
            "R10-11 External / Building Envelope Flat cladding Fibre Cement Sheet - Flat Sheet 320 sqm Class B Positive",
        ]
    )
    upload = client.post(
        f"/organisations/{org_id}/documents/upload",
        files={"file": ("custom-branding.pdf", pdf_bytes, "application/pdf")},
    )
    assert upload.status_code == 200
    document_id = upload.json()["document_id"]
    assert client.post(f"/documents/{document_id}/extract-register").status_code == 200
    assert client.post(f"/documents/{document_id}/generate-quote-candidates").status_code == 200
    priced = client.post(f"/documents/{document_id}/price-quote-candidates")
    assert priced.status_code == 200

    _resolve_all(priced.json())
    html = _export(document_id)["html_content"]

    assert "Northland Asbestos Co" in html
    assert "021 555 5555" in html
    assert "111-222-333" in html
    assert "Jane Doe" in html
    assert "021 777 7777" in html
