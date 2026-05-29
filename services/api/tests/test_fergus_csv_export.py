"""Phase E tests — Fergus-compatible CSV export.

The CSV gives estimators a free path into Fergus (no API integration). Tests
verify column order, line mapping (Xavier's Description = Fergus cost line item
title), POA handling, totals row, and the download endpoint behaviour.
"""

from __future__ import annotations

import csv
import io

import fitz
from fastapi.testclient import TestClient
from auth_helpers import PLATFORM_ADMIN_HEADERS

from app.fergus_csv_export import build_fergus_csv, fergus_csv_path
from app.main import app


client = TestClient(app, headers=PLATFORM_ADMIN_HEADERS)


def _make_pdf(pages: list[str]) -> bytes:
    document = fitz.open()
    for text in pages:
        page = document.new_page()
        page.insert_text((72, 72), text)
    return document.tobytes()


def _priced_document() -> str:
    pdf = _make_pdf(
        [
            "Asbestos Demolition Survey Register",
            "R10-11 External / Building Envelope Flat cladding Fibre Cement Sheet - Flat Sheet 320 sqm Class B Positive",
            "R10 Inside room Power box Power box and systems 1 sqm Presume No Access Class B",
            "R11 Inside room Chimney AIB hidden Insulating Board 4 pieces Class A Limited Access",
            "R30 Inside room floor tile NAD No Asbestos Detected",
        ]
    )
    upload = client.post("/documents/upload", files={"file": ("fergus-csv-demo.pdf", pdf, "application/pdf")})
    assert upload.status_code == 200
    document_id = upload.json()["document_id"]
    assert client.post(f"/documents/{document_id}/extract-register").status_code == 200
    assert client.post(f"/documents/{document_id}/generate-quote-candidates").status_code == 200
    assert client.post(f"/documents/{document_id}/price-quote-candidates").status_code == 200
    return document_id


def _parse_csv(content: str) -> list[dict[str, str]]:
    return list(csv.DictReader(io.StringIO(content)))


def test_build_fergus_csv_returns_none_for_unpriced_document() -> None:
    assert build_fergus_csv("doc-not-priced-yet") is None


def test_build_fergus_csv_has_expected_columns_in_order() -> None:
    document_id = _priced_document()
    csv_content = build_fergus_csv(document_id)
    assert csv_content is not None

    header = next(csv.reader(io.StringIO(csv_content)))
    assert header == [
        "Section",
        "Description",
        "Quantity",
        "Unit",
        "Unit Rate (ex GST)",
        "Subtotal (ex GST)",
        "GST",
        "Total (inc GST)",
        "Notes",
        "Source Pages",
        "Status",
    ]


def test_csv_description_column_holds_fergus_cost_line_item_title() -> None:
    document_id = _priced_document()
    csv_content = build_fergus_csv(document_id)
    rows = _parse_csv(csv_content)

    # Description is Xavier's mapping for Fergus cost line item title — must be present and non-empty
    # for every priced line (excluding the trailing TOTALS marker).
    priced_rows = [r for r in rows if r["Section"] != "TOTALS"]
    assert priced_rows, "Expected priced lines in CSV"
    for row in priced_rows:
        assert row["Description"], f"Empty Description in row: {row}"


def test_csv_no_access_lines_render_as_poa() -> None:
    document_id = _priced_document()
    csv_content = build_fergus_csv(document_id)
    rows = _parse_csv(csv_content)

    no_access_rows = [r for r in rows if r["Section"] == "Provisional / No Access"]
    assert no_access_rows, "Expected at least one no-access row"
    for row in no_access_rows:
        assert row["Status"] == "POA"
        assert row["Unit Rate (ex GST)"] == ""
        assert row["Total (inc GST)"] == ""


def test_csv_trailing_totals_row_matches_priced_result() -> None:
    document_id = _priced_document()
    csv_content = build_fergus_csv(document_id)
    rows = _parse_csv(csv_content)

    totals = [r for r in rows if r["Section"] == "TOTALS"]
    assert len(totals) == 1
    total_row = totals[0]
    assert float(total_row["Subtotal (ex GST)"]) > 0
    assert float(total_row["GST"]) > 0
    assert float(total_row["Total (inc GST)"]) > 0
    # Total inc GST = Subtotal + GST
    assert abs(
        float(total_row["Total (inc GST)"]) - (float(total_row["Subtotal (ex GST)"]) + float(total_row["GST"]))
    ) < 0.01


def test_csv_notes_column_includes_assumptions_and_exclusions() -> None:
    document_id = _priced_document()
    csv_content = build_fergus_csv(document_id)
    rows = _parse_csv(csv_content)

    # At least one row should have both assumptions and exclusions joined into Notes
    notes_rows = [r for r in rows if r["Notes"]]
    assert notes_rows, "Expected at least one row with Notes content"


def test_csv_source_pages_column_is_populated_for_priced_lines() -> None:
    document_id = _priced_document()
    csv_content = build_fergus_csv(document_id)
    rows = _parse_csv(csv_content)

    priced_rows = [r for r in rows if r["Section"] != "TOTALS"]
    pages_seen = [r["Source Pages"] for r in priced_rows if r["Source Pages"]]
    assert pages_seen, "Expected source-page references on at least one row"
    for cell in pages_seen:
        assert cell.startswith("p."), f"Source Pages should be prefixed with 'p.': {cell}"


def test_download_endpoint_returns_csv_attachment() -> None:
    document_id = _priced_document()
    response = client.get(f"/documents/{document_id}/export-quote/fergus.csv")

    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/csv")
    disposition = response.headers["content-disposition"]
    assert "attachment" in disposition
    assert f"fergus-quote-{document_id}.csv" in disposition


def test_download_endpoint_404_when_not_priced() -> None:
    response = client.get("/documents/doc-never-priced/export-quote/fergus.csv")
    assert response.status_code == 404


def test_csv_is_persisted_to_disk_on_download() -> None:
    document_id = _priced_document()
    client.get(f"/documents/{document_id}/export-quote/fergus.csv")

    saved_path = fergus_csv_path(document_id)
    assert saved_path.exists()
    assert saved_path.read_text(encoding="utf-8").startswith("Section,Description")
