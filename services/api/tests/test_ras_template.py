"""Organisation-branded quote templates + the RAS-style Revolve demo org.

Proves: the Revolve demo org is seeded with the RAS-1285 estimate template; its
export uses the RAS prefix/GST/company details/inclusions/notes/services and the
"Estimate" framing; a generic org falls back to the generic "Quote" template;
and the source-evidence appendix is hidden from the client quote unless enabled.
"""

from __future__ import annotations

import fitz
from fastapi.testclient import TestClient
from auth_helpers import PLATFORM_ADMIN_HEADERS

from app.demo_auth import REVOLVE_ORGANISATION_ID
from app.main import app


client = TestClient(app, headers=PLATFORM_ADMIN_HEADERS)


def _survey_pdf() -> bytes:
    document = fitz.open()
    for text in [
        "Asbestos Demolition Survey Register",
        "R10-11 External / Building Envelope Flat cladding Fibre Cement Sheet - Flat Sheet 320 sqm Class B Positive",
        "R11 Inside room Chimney AIB hidden Insulating Board 4 pieces Class A Limited Access",
    ]:
        page = document.new_page()
        page.insert_text((72, 72), text)
    return document.tobytes()


def _priced_export(org_id: str, *, enable_appendix: bool = False) -> dict:
    client.post("/demo/seed")
    if enable_appendix:
        client.post(f"/organisations/{org_id}/settings", json={"show_source_evidence_appendix": True})
    created = client.post(
        f"/organisations/{org_id}/jobs",
        files={"file": ("survey.pdf", _survey_pdf(), "application/pdf")},
        data={"client_name": "Tauraroa Area School", "site_address": "Northland, New Zealand"},
    )
    assert created.status_code == 200, created.text
    job = created.json()
    document_id, job_id = job["document_id"], job["id"]

    client.post(f"/organisations/{org_id}/jobs/{job_id}/process")

    priced = client.get(f"/documents/{document_id}/priced-quote-lines").json()
    for line in priced["lines"]:
        if line["excluded_from_pricing"]:
            continue
        client.post(
            f"/documents/{document_id}/priced-quote-lines/{line['id']}/resolve-review",
            json={"reason": "Confirmed by estimator for test.", "user_id": "estimator-test"},
        )

    export = client.post(
        f"/organisations/{org_id}/jobs/{job_id}/export",
        json={"client_name": "Tauraroa Area School", "project_name": "Asbestos removal", "site_address": "Northland"},
    )
    assert export.status_code == 200, export.text
    return export.json()


def test_revolve_demo_org_is_seeded() -> None:
    client.post("/demo/seed")
    org = client.get(f"/organisations/{REVOLVE_ORGANISATION_ID}")
    assert org.status_code == 200
    assert org.json()["name"] == "Revolve Asbestos Solutions Demo"

    settings = client.get(f"/organisations/{REVOLVE_ORGANISATION_ID}/settings").json()
    assert settings["template_type"] == "ras_style"
    assert settings["quote_prefix"] == "RAS"
    assert settings["business_gst_number"] == "139-221-346"
    assert settings["contact_name"] == "Xavier Unkovich"


def test_ras_org_exports_ras_style_estimate() -> None:
    pkg = _priced_export(REVOLVE_ORGANISATION_ID)
    html = pkg["html_content"]

    assert pkg["quote_number"].startswith("RAS")          # RAS prefix
    assert "Estimate |" in html                            # RAS framing
    assert "139-221-346" in html                           # GST number
    assert "Revolve Asbestos Solutions Demo" in html       # company details
    assert "Xavier Unkovich" in html                       # contact person
    assert "This pricing includes:" in html                # seeded inclusions
    assert "WorkSafe notification" in html
    assert "IMPORTANT:" in html                            # important notes
    assert "No one is allowed on site" in html
    assert "services are required on site" in html         # required client services


def test_generic_org_uses_fallback_quote_template() -> None:
    # Fresh org → defaults to the generic "default" template + RAS-1285 starter
    # pricebook (isolated from any cross-test template changes on the demo orgs).
    created = client.post(
        "/organisations",
        json={"name": "Generic Quote Co", "trading_name": "Generic Quote Co", "email": "generic@example.com"},
    )
    assert created.status_code == 200, created.text
    pkg = _priced_export(created.json()["id"])
    html = pkg["html_content"]
    # Generic org → "Quote", never the RAS "Estimate |" framing.
    assert "Quote |" in html
    assert "Estimate |" not in html
    # Still a complete quote (inclusions/totals render), just generic framing.
    assert "Subtotal ex GST" in html


def test_source_evidence_appendix_hidden_by_default() -> None:
    pkg = _priced_export(REVOLVE_ORGANISATION_ID)
    assert "Source evidence appendix" not in pkg["html_content"]


def test_source_evidence_appendix_shown_when_enabled() -> None:
    pkg = _priced_export(REVOLVE_ORGANISATION_ID, enable_appendix=True)
    assert "Source evidence appendix" in pkg["html_content"]
