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
        files={"file": ("export-demo.pdf", pdf_bytes, "application/pdf")},
    )
    assert upload.status_code == 200
    document_id = upload.json()["document_id"]
    assert client.post(f"/documents/{document_id}/extract-register").status_code == 200
    assert client.post(f"/documents/{document_id}/generate-quote-candidates").status_code == 200
    priced = client.post(f"/documents/{document_id}/price-quote-candidates")
    assert priced.status_code == 200
    return priced.json()


def _resolve_all_review_lines(priced: dict) -> None:
    document_id = priced["document_id"]
    for line in priced["lines"]:
        if line["excluded_from_pricing"]:
            continue
        response = client.post(
            f"/documents/{document_id}/priced-quote-lines/{line['id']}/resolve-review",
            json={
                "reason": f"Estimator accepted export gate for {line['description']}.",
                "user_id": "estimator-export",
                "assumptions_accepted": True,
                "exclusions_accepted": True,
            },
        )
        assert response.status_code == 200


def test_export_blocked_when_readiness_fails() -> None:
    priced = _priced_quote()

    response = client.post(f"/documents/{priced['document_id']}/export-quote")

    assert response.status_code == 409
    assert "blocked" in response.json()["detail"].lower()


def test_export_succeeds_when_readiness_passes() -> None:
    priced = _priced_quote()
    _resolve_all_review_lines(priced)

    response = client.post(f"/documents/{priced['document_id']}/export-quote")

    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "exported"
    assert payload["quote_number"].startswith("TQ-DEMO-")
    assert payload["client_name"] == "Tauraroa Area School"
    assert payload["html_path"].endswith("client_quote.html")
    assert payload["pdf_path"].endswith("client_quote.pdf")
    assert payload["pdf_download_path"].endswith("/export-quote/pdf")
    assert payload["line_count"] > 0
    assert payload["total_inc_gst"] > 0


def test_exported_package_contains_required_quote_content() -> None:
    priced = _priced_quote()
    _resolve_all_review_lines(priced)
    response = client.post(f"/documents/{priced['document_id']}/export-quote")
    assert response.status_code == 200

    html = response.json()["html_content"]
    # Client/site details
    assert "Tauraroa Area School" in html
    assert "ATTN" in html
    # RAS-1285-style structure
    assert "Estimate |" in html
    assert "This pricing includes:" in html
    assert "IMPORTANT:" in html
    assert "Job Number:" in html
    assert "GST Number:" in html
    assert "Estimate Date:" in html
    assert "Valid Until:" in html
    # Section grouping with line items
    assert "Priced quote lines" in html
    assert "Fibre Cement Sheet" in html
    # Totals
    assert "Subtotal ex GST" in html
    assert "Total inc GST" in html
    # Signature block
    assert "Kind regards" in html
    # TraceQuote IP — evidence appendix kept for compliance value
    assert "Source evidence appendix" in html
    # Disclaimer
    assert "Final asbestos decisions" in html


def test_get_export_returns_stored_package() -> None:
    priced = _priced_quote()
    _resolve_all_review_lines(priced)
    created = client.post(f"/documents/{priced['document_id']}/export-quote")
    assert created.status_code == 200

    response = client.get(f"/documents/{priced['document_id']}/export-quote")

    assert response.status_code == 200
    assert response.json()["export_id"] == created.json()["export_id"]

    pdf = client.get(f"/documents/{priced['document_id']}/export-quote/pdf")
    assert pdf.status_code == 200
    assert pdf.headers["content-type"] == "application/pdf"
    assert pdf.content.startswith(b"%PDF")


def test_export_accepts_editable_client_project_details() -> None:
    priced = _priced_quote()
    _resolve_all_review_lines(priced)
    response = client.post(
        f"/documents/{priced['document_id']}/export-quote",
        json={
            "client_name": "Demo Client Ltd",
            "project_name": "Board block asbestos removal",
            "site_address": "12 Demo Road, Whangarei",
            "quote_number": "DEMO-QUOTE-001",
            "scope_summary": "Demo-ready reviewed asbestos removal package.",
        },
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["quote_number"] == "DEMO-QUOTE-001"
    assert payload["client_name"] == "Demo Client Ltd"
    assert "12 Demo Road" in payload["html_content"]


def test_no_export_without_reviewed_lines() -> None:
    missing = client.post("/documents/doc-missing/export-quote")
    assert missing.status_code == 404

    priced = _priced_quote()
    readiness = client.get(f"/documents/{priced['document_id']}/approval-readiness")
    assert readiness.status_code == 200
    assert readiness.json()["approval_status"] == "blocked"
