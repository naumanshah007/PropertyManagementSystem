"""Regression tests covering the RAS-1285-aligned seed pricebook.

These guard against drift between the seed rules in pricebook.py, the static
Tauraroa demo workup in demo_data.py, and the live pricing engine. Each new
pricebook line item from the Revolve RAS-1285 estimate is asserted explicitly.
"""

from __future__ import annotations

import fitz
from fastapi.testclient import TestClient
from auth_helpers import PLATFORM_ADMIN_HEADERS

from app.demo_data import quote_lines
from app.main import app
from app.pricebook import PRICEBOOK_VERSION, get_seed_pricebook


client = TestClient(app, headers=PLATFORM_ADMIN_HEADERS)


def _make_pdf(text: str) -> bytes:
    document = fitz.open()
    page = document.new_page()
    page.insert_text((72, 72), text)
    return document.tobytes()


def test_pricebook_version_is_ras1285_seed() -> None:
    assert PRICEBOOK_VERSION == "revolve-ras-1285-seed-v1"


def test_seed_pricebook_contains_all_ras1285_line_items() -> None:
    rules = {rule.id: rule for rule in get_seed_pricebook()}

    expected = {
        "pb-site-establishment": ("fixed", 698.00, None),
        "pb-class-b-bitumen-sqm": ("per_unit", 195.00, 2500.00),
        "pb-class-b-fibre-cement-sqm": ("per_unit", 80.00, 2500.00),
        "pb-class-b-vinyl-sqm": ("per_unit", 100.00, 2500.00),
        "pb-class-a-insulating-board-provisional": ("per_unit", 650.00, 2500.00),
        "pb-no-access-power-investigation": ("excluded", None, None),
        "pb-waste-disposal-placeholder": ("per_unit", 0.92, None),
        "pb-encapsulation-provisional": ("per_unit", 34.00, None),
        "pb-glue-remover-provisional": ("fixed", 4152.00, None),
        "pb-excluded-nad": ("excluded", None, None),
    }

    for rule_id, (method, rate, min_charge) in expected.items():
        assert rule_id in rules, f"Missing seed rule: {rule_id}"
        rule = rules[rule_id]
        assert rule.pricing_method == method, f"{rule_id} method"
        assert rule.unit_rate == rate, f"{rule_id} unit_rate"
        assert rule.minimum_charge == min_charge, f"{rule_id} minimum_charge"


def test_seed_rules_use_zero_margin_and_unit_risk() -> None:
    """RAS-1285 invoice numbers are final — no hidden margin or risk multiplier."""
    for rule in get_seed_pricebook():
        assert rule.margin == 0.0, f"{rule.id} margin should be 0.0"
        assert rule.risk_multiplier == 1.0, f"{rule.id} risk_multiplier should be 1.0"


def test_minimum_charge_enforced_on_small_class_b_room() -> None:
    """A 5 sqm Class B bitumen room should price at the $2,500 floor, not 5 \xd7 $195 = $975."""
    pdf = _make_pdf(
        "Asbestos Demolition Survey Register "
        "Room A Inside room Floor bitumen adhesive removal 5 sqm Class B Positive"
    )
    upload = client.post(
        "/documents/upload",
        files={"file": ("min-charge-demo.pdf", pdf, "application/pdf")},
    )
    assert upload.status_code == 200
    document_id = upload.json()["document_id"]

    assert client.post(f"/documents/{document_id}/extract-register").status_code == 200
    assert client.post(f"/documents/{document_id}/generate-quote-candidates").status_code == 200
    priced = client.post(f"/documents/{document_id}/price-quote-candidates")
    assert priced.status_code == 200

    # Find any Class B priced line and confirm minimum_charge is honored where base < $2,500
    class_b_lines = [
        line for line in priced.json()["lines"]
        if line["section"] == "Class B Removal" and line["subtotal_ex_gst"] is not None
    ]
    assert class_b_lines, "Expected at least one Class B priced line in response"

    for line in class_b_lines:
        base = line["base_cost"]
        subtotal = line["subtotal_ex_gst"]
        # If base would have been below $2,500, subtotal must be exactly $2,500
        if base is not None and base < 2500.0:
            assert subtotal == 2500.0, (
                f"Min charge not enforced on line {line['id']}: base={base}, subtotal={subtotal}"
            )


def test_demo_workup_quote_lines_reference_real_seed_rule_ids() -> None:
    """Guard against drift: every pricing_rule_id in the demo workup must exist in the seed pricebook."""
    valid_rule_ids = {rule.id for rule in get_seed_pricebook()}

    for line in quote_lines:
        for rule_id in line.pricing_rule_ids:
            assert rule_id in valid_rule_ids, (
                f"Demo quote line {line.id} references unknown pricing rule '{rule_id}'. "
                f"Update demo_data.py or add the rule to pricebook.py."
            )


def test_demo_workup_no_access_line_is_poa() -> None:
    """No-access lines in the static demo must mirror Revolve's POA pattern (no price)."""
    no_access_lines = [
        line for line in quote_lines if line.section == "Provisional / No Access"
    ]
    assert no_access_lines, "Expected a no-access line in demo workup"

    for line in no_access_lines:
        assert line.unit_rate is None
        assert line.base_cost is None
        assert line.gst is None
        assert line.total is None


def test_demo_workup_site_establishment_uses_ras1285_rate() -> None:
    """The static Tauraroa demo's site establishment must match the new $698 RAS-1285 rate."""
    site_lines = [line for line in quote_lines if line.section == "Site Establishment"]
    assert len(site_lines) == 1
    site = site_lines[0]
    assert site.unit_rate == 698
    assert site.gst == 104.70
    assert site.total == 802.70
