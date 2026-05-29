"""Fergus-compatible CSV export of priced quote lines (Phase E, free tier).

Xavier's Feb 26 brief mapped each register field to a Fergus cost-line column
(Description → Fergus cost line item title; Material → description; Extent →
quantity; Friability → Class A/B for clearance recommendations). Direct
Fergus API push is intentionally out of scope (paid integration), so we emit
a CSV that an estimator can copy/paste or upload into Fergus' cost-line
builder manually.

Column choices match the structure of a Fergus quote cost line — section,
title (description), quantity/unit, unit rate (ex GST), subtotal, GST, total,
and a notes column containing assumptions + exclusions for full traceability.
Excluded lines (POA / NAD) appear as informational rows with empty pricing.
"""

from __future__ import annotations

import csv
import io
from pathlib import Path

from .document_parser import _document_dir
from .pricing_engine import load_priced_quote_lines
from .storage_paths import atomic_write_text
from .schemas import PricedQuoteLine


FERGUS_CSV_VERSION = "phase-e-fergus-csv-v1"

_CSV_COLUMNS: list[str] = [
    "Section",
    "Description",  # Fergus cost line item title (per Xavier's mapping)
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


def _format_money(value: float | None) -> str:
    return f"{value:.2f}" if value is not None else ""


def _format_quantity(value: float | None) -> str:
    if value is None:
        return ""
    return f"{value:g}"


def _line_status(line: PricedQuoteLine) -> str:
    if line.excluded_from_pricing:
        return "POA" if line.section == "Provisional / No Access" else "Excluded"
    if line.review_required or line.review_status == "review_required":
        return "Review Required"
    if line.review_status == "accepted":
        return "Reviewed"
    return "Draft"


def _line_notes(line: PricedQuoteLine) -> str:
    parts: list[str] = []
    if line.assumptions:
        parts.append("Assumptions: " + " | ".join(line.assumptions))
    if line.exclusions:
        parts.append("Exclusions: " + " | ".join(line.exclusions))
    return " || ".join(parts)


def _line_row(line: PricedQuoteLine) -> dict[str, str]:
    return {
        "Section": line.section,
        "Description": line.description,
        "Quantity": _format_quantity(line.quantity),
        "Unit": line.unit or "",
        "Unit Rate (ex GST)": _format_money(line.unit_rate),
        "Subtotal (ex GST)": _format_money(line.subtotal_ex_gst),
        "GST": _format_money(line.gst),
        "Total (inc GST)": _format_money(line.total_inc_gst),
        "Notes": _line_notes(line),
        "Source Pages": ", ".join(f"p.{p}" for p in line.source_pages),
        "Status": _line_status(line),
    }


def build_fergus_csv(document_id: str) -> str | None:
    """Return the Fergus-importable CSV string for a document's priced quote lines.

    Returns None if the document has not been priced yet — callers should treat
    that as a 404. Lines are emitted in their natural pricebook order (Site
    Establishment first, then per-section).
    """
    priced = load_priced_quote_lines(document_id)
    if priced is None:
        return None

    buffer = io.StringIO()
    writer = csv.DictWriter(buffer, fieldnames=_CSV_COLUMNS, lineterminator="\n")
    writer.writeheader()
    for line in priced.lines:
        writer.writerow(_line_row(line))

    # Trailing totals row so the CSV is verifiable at a glance once imported
    writer.writerow(
        {
            "Section": "TOTALS",
            "Description": "",
            "Quantity": "",
            "Unit": "",
            "Unit Rate (ex GST)": "",
            "Subtotal (ex GST)": _format_money(priced.subtotal_ex_gst),
            "GST": _format_money(priced.gst),
            "Total (inc GST)": _format_money(priced.total_inc_gst),
            "Notes": f"Pricebook: {priced.pricebook_version}",
            "Source Pages": "",
            "Status": "",
        }
    )
    return buffer.getvalue()


def fergus_csv_path(document_id: str) -> Path:
    """Filesystem path where the generated CSV is mirrored for download."""
    return _document_dir(document_id) / "exports" / "fergus_quote_lines.csv"


def save_fergus_csv(document_id: str) -> tuple[str, Path] | None:
    """Generate the CSV and write it to disk alongside the existing exports."""
    csv_content = build_fergus_csv(document_id)
    if csv_content is None:
        return None
    path = fergus_csv_path(document_id)
    path.parent.mkdir(parents=True, exist_ok=True)
    atomic_write_text(path, csv_content)
    return csv_content, path
