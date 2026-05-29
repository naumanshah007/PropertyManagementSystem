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


def _upload_generate_and_price() -> dict:
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
        files={"file": ("pricing-demo.pdf", pdf_bytes, "application/pdf")},
    )
    assert upload.status_code == 200
    document_id = upload.json()["document_id"]

    extraction = client.post(f"/documents/{document_id}/extract-register")
    assert extraction.status_code == 200

    candidates = client.post(f"/documents/{document_id}/generate-quote-candidates")
    assert candidates.status_code == 200

    priced = client.post(f"/documents/{document_id}/price-quote-candidates")
    assert priced.status_code == 200
    return priced.json()


def _find_line(lines: list[dict], section: str, text: str | None = None) -> dict:
    for line in lines:
        if line["section"] != section:
            continue
        if text is None or text.lower() in line["description"].lower():
            return line
    raise AssertionError(f"Priced line not found: {section} {text or ''}")


def test_class_b_sqm_item_gets_per_sqm_pricing() -> None:
    result = _upload_generate_and_price()
    line = _find_line(result["lines"], "Class B Removal", "Flat cladding")

    assert line["quantity"] == 320
    assert line["unit"] == "sqm"
    assert line["unit_rate"] == 80.0
    assert line["pricing_rule_id"] == "pb-class-b-fibre-cement-sqm"
    assert line["base_cost"] == 25600
    # Explanation can come from either the seed pricebook template (when there's no active org
    # pricebook) or the PricebookRule template (when the auto-seeded starter is active). Both
    # mention "Class B Fibre Cement"; accept either case.
    explanation = line["pricing_explanation"].lower()
    assert "class b" in explanation and "fibre cement" in explanation


def test_class_a_item_gets_provisional_review_required_pricing() -> None:
    result = _upload_generate_and_price()
    line = _find_line(result["lines"], "Class A / Friable Removal", "Chimney AIB hidden")

    assert line["quantity"] == 4
    assert line["unit_rate"] == 650
    assert line["pricing_rule_id"] == "pb-class-a-insulating-board-provisional"
    assert line["review_status"] == "review_required"
    assert line["review_required"] is True


def test_no_access_item_is_marked_poa_and_excluded() -> None:
    result = _upload_generate_and_price()
    line = _find_line(result["lines"], "Provisional / No Access", "Power box")

    assert line["pricing_rule_id"] == "pb-no-access-power-investigation"
    assert line["excluded_from_pricing"] is True
    assert line["unit_rate"] is None
    assert line["subtotal_ex_gst"] is None
    assert line["review_status"] == "excluded_from_pricing"
    assert any("No allowance" in assumption for assumption in line["assumptions"])


def test_nad_item_remains_excluded_from_pricing() -> None:
    result = _upload_generate_and_price()
    line = _find_line(result["lines"], "Excluded / NAD Findings")

    assert line["excluded_from_pricing"] is True
    assert line["unit_rate"] is None
    assert line["subtotal_ex_gst"] is None
    assert line["gst"] is None
    assert line["total_inc_gst"] is None
    assert line["review_status"] == "excluded_from_pricing"


def test_gst_totals_evidence_and_approval_gate() -> None:
    result = _upload_generate_and_price()

    assert result["approval_status"] == "blocked"
    assert result["subtotal_ex_gst"] > 0
    assert result["gst"] == round(result["subtotal_ex_gst"] * 0.15, 2)
    assert result["total_inc_gst"] == round(result["subtotal_ex_gst"] + result["gst"], 2)

    for line in result["lines"]:
        assert line["source_register_item_ids"]
        assert line["source_evidence"]
        assert line["source_pages"]
        assert line["approval_status"] == "not_ready"
        if line["subtotal_ex_gst"] is not None:
            assert line["gst"] == round(line["subtotal_ex_gst"] * 0.15, 2)
            assert line["total_inc_gst"] == round(line["subtotal_ex_gst"] + line["gst"], 2)


def test_priced_quote_lookup_and_missing_document() -> None:
    result = _upload_generate_and_price()
    document_id = result["document_id"]

    lookup = client.get(f"/documents/{document_id}/priced-quote-lines")
    assert lookup.status_code == 200
    assert lookup.json()["document_id"] == document_id

    missing = client.post("/documents/doc-missing/price-quote-candidates")
    assert missing.status_code == 404
