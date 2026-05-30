from __future__ import annotations

import html
import re
from datetime import datetime, timedelta, timezone
from pathlib import Path
from uuid import uuid4

import fitz

from .config import get_settings
from .document_parser import _document_dir
from .organisation_store import get_organisation_settings
from .pricing_engine import get_approval_readiness, load_priced_quote_lines
from .storage_paths import atomic_write_text
from .schemas import OrganisationSettings, PricedQuoteLine, QuoteExportPackage, QuoteExportRequest


EXPORT_VERSION = "phase-7-client-quote-export-v2-ras1285"

# Section order used to group line items in the quote output, matching RAS-1285 pattern
_SECTION_ORDER: list[str] = [
    "Site Establishment",
    "Class A / Friable Removal",
    "Class B Removal",
    "Provisional / No Access",
    "Waste / Disposal Placeholder",
    "Encapsulation / Provisional Allowance",
    "Excluded / NAD Findings",
]


class ExportBlockedError(ValueError):
    pass


def _exports_dir(document_id: str) -> Path:
    return _document_dir(document_id) / "exports"


def _export_json_path(document_id: str) -> Path:
    return _exports_dir(document_id) / "export_package.json"


def load_quote_export(document_id: str) -> QuoteExportPackage | None:
    path = _export_json_path(document_id)
    if not path.exists():
        return None
    return QuoteExportPackage.model_validate_json(path.read_text(encoding="utf-8"))


def export_quote(document_id: str, request: QuoteExportRequest | None = None) -> QuoteExportPackage | None:
    priced = load_priced_quote_lines(document_id)
    if priced is None:
        return None
    details = request or QuoteExportRequest()

    readiness = get_approval_readiness(document_id)
    if readiness is None:
        return None
    if readiness.approval_status != "ready_for_approval":
        raise ExportBlockedError("Quote export is blocked until approval-readiness passes.")

    active_lines = [line for line in priced.lines if not line.excluded_from_pricing]
    if not active_lines:
        raise ExportBlockedError("Quote export is blocked because there are no reviewed priced quote lines.")
    if not all(line.review_status == "accepted" for line in active_lines):
        raise ExportBlockedError("Quote export is blocked because not all priced lines are estimator-reviewed.")

    org_settings = get_organisation_settings(priced.organisation_id)
    if org_settings is None:
        org_settings = OrganisationSettings(
            organisation_id=priced.organisation_id,
            updated_at=datetime.now(timezone.utc),
        )

    export_id = f"export-{uuid4().hex[:12]}"
    quote_number = details.quote_number or f"{org_settings.quote_prefix}-DEMO-{document_id[-6:].upper()}"
    export_dir = _exports_dir(document_id)
    export_dir.mkdir(parents=True, exist_ok=True)
    html_path = export_dir / "client_quote.html"
    pdf_path = export_dir / "client_quote.pdf"

    assumptions = _unique(item for line in active_lines for item in line.assumptions)
    exclusions = _unique(item for line in priced.lines for item in line.exclusions)
    source_pages = sorted({page for line in priced.lines for page in line.source_pages})
    generated_at = datetime.now(timezone.utc)
    valid_until = generated_at + timedelta(days=org_settings.quote_valid_days or 30)

    html_content = _render_html(
        document_id=document_id,
        quote_number=quote_number,
        details=details,
        settings=org_settings,
        generated_at=generated_at,
        valid_until=valid_until,
        priced_lines=priced.lines,
        subtotal_ex_gst=priced.subtotal_ex_gst,
        gst=priced.gst,
        total_inc_gst=priced.total_inc_gst,
    )
    atomic_write_text(html_path, html_content)
    _render_pdf(
        path=pdf_path,
        quote_number=quote_number,
        details=details,
        settings=org_settings,
        generated_at=generated_at,
        valid_until=valid_until,
        priced_lines=priced.lines,
        subtotal_ex_gst=priced.subtotal_ex_gst,
        gst=priced.gst,
        total_inc_gst=priced.total_inc_gst,
    )

    pdf_download_path = f"/documents/{document_id}/export-quote/pdf"
    settings = get_settings()
    if settings.file_storage_provider == "r2":
        # Push the client-facing deliverables to R2 and serve a (presigned or
        # public) object URL; the download endpoint redirects to it.
        from .file_storage import get_file_storage

        storage = get_file_storage()
        pdf_key = f"documents/{document_id}/exports/client_quote.pdf"
        storage.save_export(pdf_path, pdf_key)
        storage.save_export(html_path, f"documents/{document_id}/exports/client_quote.html")
        url = storage.get_download_url(pdf_key)
        if url:
            pdf_download_path = url

    package = QuoteExportPackage(
        document_id=document_id,
        export_id=export_id,
        quote_number=quote_number,
        client_name=details.client_name,
        project_name=details.project_name,
        site_address=details.site_address,
        status="exported",
        html_path=str(html_path),
        pdf_path=str(pdf_path),
        pdf_download_path=pdf_download_path,
        html_content=html_content,
        line_count=len(active_lines),
        subtotal_ex_gst=priced.subtotal_ex_gst,
        gst=priced.gst,
        total_inc_gst=priced.total_inc_gst,
        assumptions=assumptions,
        exclusions=exclusions,
        source_pages=source_pages,
        generated_at=generated_at,
    )
    atomic_write_text(_export_json_path(document_id), package.model_dump_json(indent=2))
    return package


def _group_lines_by_section(lines: list[PricedQuoteLine]) -> list[tuple[str, list[PricedQuoteLine]]]:
    grouped: dict[str, list[PricedQuoteLine]] = {}
    for line in lines:
        grouped.setdefault(line.section, []).append(line)
    ordered: list[tuple[str, list[PricedQuoteLine]]] = []
    seen: set[str] = set()
    for section in _SECTION_ORDER:
        if section in grouped:
            ordered.append((section, grouped[section]))
            seen.add(section)
    for section, items in grouped.items():
        if section not in seen:
            ordered.append((section, items))
    return ordered


def _render_html(
    *,
    document_id: str,
    quote_number: str,
    details: QuoteExportRequest,
    settings: OrganisationSettings,
    generated_at: datetime,
    valid_until: datetime,
    priced_lines: list[PricedQuoteLine],
    subtotal_ex_gst: float,
    gst: float,
    total_inc_gst: float,
) -> str:
    grouped = _group_lines_by_section(priced_lines)
    inclusions_html = "".join(f"<li>{_e(item)}</li>" for item in settings.quote_inclusions)
    important_html = "".join(f"<li>{_e(item)}</li>" for item in settings.quote_important_notes)
    required_services_html = "".join(f"<li>{_e(item)}</li>" for item in settings.quote_required_services)

    # Template type controls the client-facing framing. "ras_style" → "Estimate"
    # (RAS-1285 layout); "default" → generic TraceQuote "Quote".
    title_label = "Estimate" if settings.template_type == "ras_style" else "Quote"
    subtitle_html = (
        "" if settings.template_type == "ras_style"
        else f'<p style="margin-top:-6px;color:#6b7280;font-size:11px;">Prepared by {_e(settings.business_name)}</p>'
    )
    review_statement_html = (
        '<p style="margin:16px 0;padding:10px 14px;background:#ecfdf5;border-left:4px solid #10b981;font-size:11px;">'
        "Every priced line in this quote has been reviewed and approved by a qualified estimator before issue.</p>"
        if settings.show_review_statement else ""
    )

    sections_html_parts: list[str] = []
    for section, lines in grouped:
        rows: list[str] = []
        for line in lines:
            qty = _quantity_display(line)
            rate = _rate_display(line)
            total = _total_display(line)
            rows.append(
                f"""
                <tr>
                  <td class="desc">
                    <div class="line-desc">{_e(line.description)}</div>
                    <div class="line-source">Source p.{', p.'.join(str(p) for p in line.source_pages)}</div>
                  </td>
                  <td class="num">{qty}</td>
                  <td class="num">{rate}</td>
                  <td class="num">{total}</td>
                </tr>
                """
            )
        sections_html_parts.append(
            f"""
            <div class="section-block">
              <h3>{_e(section)}</h3>
              <table class="lines">
                <thead>
                  <tr><th class="desc">Description</th><th class="num">Quantity</th><th class="num">Price</th><th class="num">Total</th></tr>
                </thead>
                <tbody>
                  {''.join(rows)}
                </tbody>
              </table>
            </div>
            """
        )

    evidence_rows = "".join(
        f"""
        <tr>
          <td>{_e(line.description)}</td>
          <td>p.{', p.'.join(str(p) for p in line.source_pages)}</td>
          <td>{_e(_evidence_text(line))}</td>
        </tr>
        """
        for line in priced_lines
    )
    # The source-evidence appendix is an INTERNAL audit artifact. It is omitted
    # from the client-facing quote unless the org explicitly enables it.
    evidence_section_html = (
        f"""
  <section class="evidence-section">
    <h2>Source evidence appendix</h2>
    <p style="font-size:10px;color:#6b7280;">For audit and compliance. Every priced line above is traceable to the survey pages below.</p>
    <table class="evidence">
      <thead><tr><th>Quote line</th><th>Source pages</th><th>Evidence</th></tr></thead>
      <tbody>{evidence_rows}</tbody>
    </table>
  </section>"""
        if settings.show_source_evidence_appendix
        else ""
    )

    business_address = "<br />".join(_e(line) for line in settings.business_address_lines)

    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8" />
  <title>{_e(quote_number)} — {_e(settings.business_name)}</title>
  <style>
    body {{ font-family: Arial, sans-serif; color: #17202a; margin: 40px; line-height: 1.45; font-size: 12px; }}
    .header-grid {{ display: grid; grid-template-columns: 1fr 1fr; gap: 24px; margin-bottom: 24px; }}
    .business-block {{ text-align: right; font-size: 11px; color: #2b343b; }}
    .business-block .name {{ font-size: 16px; font-weight: 700; color: #235347; }}
    .client-block .label {{ font-size: 10px; color: #6b7280; letter-spacing: .08em; text-transform: uppercase; }}
    .client-block .value {{ font-size: 13px; font-weight: 600; }}
    .meta-grid {{ display: grid; grid-template-columns: 1fr 1fr; gap: 8px 24px; padding: 14px 18px; background: #f3f6f5; border-left: 4px solid #235347; margin-bottom: 24px; }}
    .meta-label {{ font-weight: 600; color: #2b343b; }}
    h1.estimate-title {{ font-size: 22px; margin: 18px 0 12px; color: #17202a; }}
    h2 {{ font-size: 15px; margin: 24px 0 8px; color: #235347; }}
    h3 {{ font-size: 13px; margin: 18px 0 6px; color: #17202a; border-bottom: 1px solid #d1d5db; padding-bottom: 4px; }}
    p {{ margin: 8px 0; }}
    ol.inclusions, ul.notes, ul.required {{ padding-left: 22px; }}
    ol.inclusions li, ul.notes li, ul.required li {{ margin: 3px 0; }}
    .section-block {{ margin: 12px 0; }}
    table.lines {{ width: 100%; border-collapse: collapse; }}
    table.lines th, table.lines td {{ padding: 6px 8px; border-bottom: 1px solid #e5e7eb; vertical-align: top; font-size: 12px; }}
    table.lines th {{ background: #fafafa; text-align: left; font-size: 11px; color: #4b5563; font-weight: 600; }}
    table.lines td.desc {{ width: 55%; }}
    table.lines td.num, table.lines th.num {{ text-align: right; white-space: nowrap; }}
    .line-desc {{ font-weight: 500; }}
    .line-source {{ font-size: 10px; color: #6b7280; margin-top: 2px; }}
    .totals {{ margin-top: 16px; margin-left: auto; width: 360px; border-collapse: collapse; }}
    .totals td {{ padding: 6px 8px; border-top: 1px solid #d1d5db; }}
    .totals .grand-total td {{ font-size: 14px; font-weight: 700; background: #f3f6f5; border-top: 2px solid #235347; }}
    .acceptance {{ margin: 28px 0 8px; padding: 12px 16px; background: #fff7ed; border-left: 4px solid #f59e0b; font-style: italic; }}
    .important-block {{ margin: 18px 0; }}
    .important-block h2 {{ color: #b45309; }}
    .required-block ul {{ margin: 6px 0; }}
    .signature {{ margin-top: 32px; }}
    .signature .name {{ font-weight: 600; }}
    .evidence-section {{ margin-top: 32px; padding-top: 18px; border-top: 1px dashed #d1d5db; }}
    .evidence-section h2 {{ color: #4b5563; font-size: 13px; }}
    table.evidence {{ width: 100%; border-collapse: collapse; font-size: 10px; }}
    table.evidence th, table.evidence td {{ border: 1px solid #e5e7eb; padding: 5px 7px; vertical-align: top; }}
    table.evidence th {{ background: #fafafa; color: #4b5563; }}
    .footer {{ margin-top: 24px; padding-top: 12px; border-top: 1px solid #d1d5db; font-size: 10px; color: #6b7280; }}
  </style>
</head>
<body>
  <header class="header-grid">
    <div class="client-block">
      <div class="label">ATTN</div>
      <div class="value">{_e(details.client_name)}</div>
      <div style="margin-top:4px;">{_e(details.project_name)}</div>
    </div>
    <div class="business-block">
      <div class="name">{_e(settings.business_name)}</div>
      <div>{business_address}</div>
      <div>{_e(settings.business_email)}</div>
      <div>{_e(settings.business_phone)}</div>
    </div>
  </header>

  <div class="meta-grid">
    <div><span class="meta-label">Site Address:</span> {_e(details.site_address)}</div>
    <div><span class="meta-label">Job Number:</span> {_e(quote_number)}</div>
    <div><span class="meta-label">GST Number:</span> {_e(settings.business_gst_number)}</div>
    <div><span class="meta-label">Estimate Date:</span> {_e(generated_at.date().isoformat())}</div>
    <div><span class="meta-label">Valid Until:</span> {_e(valid_until.date().isoformat())}</div>
    <div><span class="meta-label">Currency:</span> {_e(settings.default_currency)}</div>
  </div>

  <h1 class="estimate-title">{title_label} | {_e(details.project_name)}</h1>
  {subtitle_html}
  <p>{_e(settings.quote_intro_text)}</p>

  <h2>This pricing includes:</h2>
  <ol class="inclusions">{inclusions_html}</ol>

  <p>{_e(settings.quote_disclaimer_text)}</p>

  <h2>Priced quote lines</h2>
  {''.join(sections_html_parts)}

  <table class="totals">
    <tr><td>Subtotal ex GST</td><td class="num">{_money(subtotal_ex_gst)}</td></tr>
    <tr><td>GST ({(settings.gst_rate * 100):g}%)</td><td class="num">{_money(gst)}</td></tr>
    <tr class="grand-total"><td>Total inc GST</td><td class="num">{_money(total_inc_gst)}</td></tr>
  </table>

  <div class="acceptance">{_e(settings.quote_acceptance_text)}</div>

  <div class="important-block">
    <h2>IMPORTANT:</h2>
    <ul class="notes">{important_html}</ul>
  </div>

  <div class="required-block">
    <h2>The following services are required on site (provided by client):</h2>
    <ul class="required">{required_services_html}</ul>
    <p>{_e(settings.quote_variation_text)}</p>
  </div>

  <p>{_e(settings.quote_closing_text)}</p>

  {review_statement_html}

  <div class="signature">
    <p>Kind regards</p>
    <p class="name">{_e(settings.contact_name)}</p>
    <p>{_e(settings.contact_phone)}</p>
  </div>
{evidence_section_html}

  <div class="footer">
    Quote {_e(quote_number)} · Generated {_e(generated_at.isoformat(timespec='seconds'))} · Document {_e(document_id)}
    <br />
    Disclaimer: This quote was prepared with computer-assisted survey extraction. Final asbestos decisions, removal methodology, clearance requirements, and compliance determinations require qualified/licensed personnel.
  </div>
</body>
</html>
"""


def _render_pdf(
    *,
    path: Path,
    quote_number: str,
    details: QuoteExportRequest,
    settings: OrganisationSettings,
    generated_at: datetime,
    valid_until: datetime,
    priced_lines: list[PricedQuoteLine],
    subtotal_ex_gst: float,
    gst: float,
    total_inc_gst: float,
) -> None:
    document = fitz.open()
    page = _new_page(document)
    y = _pdf_header_block(page, quote_number, details, settings, generated_at, valid_until)

    title_label = "Estimate" if settings.template_type == "ras_style" else "Quote"
    y = _pdf_text(page, f"{title_label} | {details.project_name}", 48, y + 14, size=15, bold=True)
    y = _pdf_text(page, settings.quote_intro_text, 48, y + 6, size=9, width=500)

    y = _pdf_text(page, "This pricing includes:", 48, y + 14, size=11, bold=True, color=(0.13, 0.33, 0.28))
    for index, item in enumerate(settings.quote_inclusions, start=1):
        if y > 770:
            page = _new_page(document)
            y = 60
        y = _pdf_text(page, f"{index}. {item}", 58, y + 5, size=8, width=490)

    y = _pdf_text(page, settings.quote_disclaimer_text, 48, y + 12, size=8, width=500, color=(0.42, 0.45, 0.50))

    grouped = _group_lines_by_section(priced_lines)
    for section, lines in grouped:
        if y > 730:
            page = _new_page(document)
            y = 60
        y = _pdf_text(page, section, 48, y + 14, size=11, bold=True, color=(0.13, 0.33, 0.28))
        for line in lines:
            if y > 760:
                page = _new_page(document)
                y = 60
            page.draw_line(fitz.Point(48, y + 4), fitz.Point(547, y + 4), color=(0.86, 0.88, 0.90), width=0.5)
            _pdf_text(page, line.description, 58, y + 8, size=9, width=320, bold=False)
            _pdf_text(page, _quantity_display_text(line), 380, y + 8, size=9, width=80)
            _pdf_text(page, _rate_display_text(line), 440, y + 8, size=9, width=50)
            _pdf_text(page, _total_display_text(line), 490, y + 8, size=9, width=60, bold=True)
            _pdf_text(
                page,
                f"Source p.{', p.'.join(str(p) for p in line.source_pages)}",
                58,
                y + 22,
                size=7,
                color=(0.42, 0.45, 0.50),
                width=300,
            )
            y += 34

    if y > 700:
        page = _new_page(document)
        y = 60
    y = _pdf_text(page, "Totals", 350, y + 14, size=11, bold=True, color=(0.13, 0.33, 0.28))
    page.draw_rect(fitz.Rect(330, y + 4, 547, y + 84), color=(0.13, 0.33, 0.28), fill=(0.96, 0.98, 0.97), width=0.7)
    _pdf_text(page, f"Subtotal ex GST: {_money(subtotal_ex_gst)}", 344, y + 14, size=9, width=190)
    _pdf_text(page, f"GST ({(settings.gst_rate * 100):g}%): {_money(gst)}", 344, y + 34, size=9, width=190)
    _pdf_text(page, f"Total inc GST: {_money(total_inc_gst)}", 344, y + 58, size=12, bold=True, width=190)
    y += 96

    # Acceptance + IMPORTANT block
    page = _new_page(document)
    y = 60
    y = _pdf_text(page, settings.quote_acceptance_text, 48, y, size=9, width=500, color=(0.55, 0.40, 0.05))
    y = _pdf_text(page, "IMPORTANT:", 48, y + 18, size=12, bold=True, color=(0.55, 0.30, 0.05))
    for item in settings.quote_important_notes:
        if y > 760:
            page = _new_page(document)
            y = 60
        y = _pdf_text(page, f"• {item}", 58, y + 5, size=8, width=490)

    if y > 700:
        page = _new_page(document)
        y = 60
    y = _pdf_text(page, "The following services are required on site (provided by client):", 48, y + 14, size=10, bold=True)
    for item in settings.quote_required_services:
        y = _pdf_text(page, f"• {item}", 58, y + 5, size=8, width=490)

    y = _pdf_text(page, settings.quote_variation_text, 48, y + 12, size=8, width=500, color=(0.42, 0.45, 0.50))
    y = _pdf_text(page, settings.quote_closing_text, 48, y + 14, size=9, width=500)

    y = _pdf_text(page, "Kind regards", 48, y + 22, size=9)
    y = _pdf_text(page, settings.contact_name, 48, y + 4, size=10, bold=True)
    y = _pdf_text(page, settings.contact_phone, 48, y + 4, size=9)

    document.save(path)
    document.close()


def _new_page(document: fitz.Document) -> fitz.Page:
    return document.new_page(width=595, height=842)


def _pdf_header_block(
    page: fitz.Page,
    quote_number: str,
    details: QuoteExportRequest,
    settings: OrganisationSettings,
    generated_at: datetime,
    valid_until: datetime,
) -> float:
    # Business name and contact info on the right
    page.insert_text((48, 50), "ATTN", fontsize=8, fontname="helv", color=(0.42, 0.45, 0.50))
    page.insert_text((48, 64), details.client_name, fontsize=12, fontname="helv", color=(0.1, 0.13, 0.16))
    page.insert_text((48, 80), details.project_name, fontsize=9, fontname="helv", color=(0.3, 0.33, 0.36))

    page.insert_text((400, 50), settings.business_name, fontsize=12, fontname="helv", color=(0.13, 0.33, 0.28))
    text_y = 64
    for line in settings.business_address_lines + [settings.business_email, settings.business_phone]:
        page.insert_text((400, text_y), line, fontsize=8, fontname="helv", color=(0.30, 0.33, 0.36))
        text_y += 11

    # Meta block
    meta_y = 110
    page.draw_rect(fitz.Rect(40, meta_y, 555, meta_y + 60), color=(0.92, 0.94, 0.93), fill=(0.96, 0.97, 0.96), width=0.5)
    page.insert_text((52, meta_y + 14), f"Site Address: {details.site_address}", fontsize=9, fontname="helv", color=(0.13, 0.16, 0.19))
    page.insert_text((52, meta_y + 30), f"Job Number: {quote_number}", fontsize=9, fontname="helv", color=(0.13, 0.16, 0.19))
    page.insert_text((52, meta_y + 46), f"GST Number: {settings.business_gst_number}", fontsize=9, fontname="helv", color=(0.13, 0.16, 0.19))
    page.insert_text((310, meta_y + 14), f"Estimate Date: {generated_at.date().isoformat()}", fontsize=9, fontname="helv", color=(0.13, 0.16, 0.19))
    page.insert_text((310, meta_y + 30), f"Valid Until: {valid_until.date().isoformat()}", fontsize=9, fontname="helv", color=(0.13, 0.16, 0.19))
    page.insert_text((310, meta_y + 46), f"Currency: {settings.default_currency}", fontsize=9, fontname="helv", color=(0.13, 0.16, 0.19))

    return meta_y + 70


def _pdf_text(
    page: fitz.Page,
    text: str,
    x: float,
    y: float,
    *,
    size: float,
    width: float = 500,
    color=(0.1, 0.13, 0.16),
    bold: bool = False,
) -> float:
    if not text:
        return y
    rect = fitz.Rect(x, y, x + width, y + 400)
    page.insert_textbox(rect, text, fontsize=size, fontname="helv", color=color)
    # Rough line-count estimate so subsequent text doesn't overlap
    chars_per_line = max(20, int(width / max(size * 0.55, 1)))
    line_count = max(1, (len(text) + chars_per_line - 1) // chars_per_line)
    return y + (size + 3) * line_count


def _money(value: float | None) -> str:
    if value is None:
        return "—"
    return f"${value:,.2f}"


def _quantity_display(line: PricedQuoteLine) -> str:
    if line.excluded_from_pricing or line.quantity is None:
        return "POA" if line.section == "Provisional / No Access" else "—"
    return f"{line.quantity:g} {line.unit or ''}".strip()


def _rate_display(line: PricedQuoteLine) -> str:
    if line.excluded_from_pricing or line.unit_rate is None:
        return "POA" if line.section == "Provisional / No Access" else "—"
    return _money(line.unit_rate)


def _total_display(line: PricedQuoteLine) -> str:
    if line.excluded_from_pricing or line.total_inc_gst is None:
        return "POA" if line.section == "Provisional / No Access" else "—"
    # RAS-1285 shows the per-line price ex-GST in the section table; GST is summed at the bottom
    return _money(line.subtotal_ex_gst)


def _quantity_display_text(line: PricedQuoteLine) -> str:
    return _quantity_display(line)


def _rate_display_text(line: PricedQuoteLine) -> str:
    return _rate_display(line)


def _total_display_text(line: PricedQuoteLine) -> str:
    return _total_display(line)


def _e(value: object) -> str:
    return html.escape(str(value), quote=True)


def _evidence_text(line: PricedQuoteLine) -> str:
    text = " ".join(evidence.text for evidence in line.source_evidence)
    return re.sub(r"\s+", " ", text).strip()[:700]


def _unique(values) -> list[str]:
    seen: set[str] = set()
    output: list[str] = []
    for value in values:
        if value and value not in seen:
            seen.add(value)
            output.append(value)
    return output
