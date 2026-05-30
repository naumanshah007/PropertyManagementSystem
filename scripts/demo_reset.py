#!/usr/bin/env python3
from __future__ import annotations

import os
import shutil
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
API_ROOT = REPO_ROOT / "services" / "api"
SAMPLE_PDF = REPO_ROOT / "samples" / "surveys" / "38-Asbestos-Survey-_Rev_0.pdf"
STORAGE_ROOT = API_ROOT / "storage"
DOCUMENT_ID = "demo-tauraroa-vendor"
REVOLVE_DOCUMENT_ID = "demo-tauraroa-revolve"

# Phase F security tightening only allows the admin123 dev password fallback when
# APP_ENV is explicitly set to "local". This script is for local demo setup, so
# default APP_ENV here when the operator hasn't set it.
os.environ.setdefault("APP_ENV", "local")

sys.path.insert(0, str(API_ROOT))

from app.document_parser import _document_dir, parse_pdf  # noqa: E402
from app.demo_auth import REVOLVE_ORGANISATION_ID, seed_demo_environment  # noqa: E402
from app.export_engine import export_quote  # noqa: E402
from app.pricing_engine import price_quote_candidates, resolve_priced_quote_line_review  # noqa: E402
from app.quote_candidate_mapper import generate_quote_candidates  # noqa: E402
from app.register_extractor import extract_register  # noqa: E402
from app.schemas import QuoteExportRequest, ResolveReviewRequest  # noqa: E402


def main() -> int:
    if not SAMPLE_PDF.exists():
        print(
            "Missing sample PDF: add samples/surveys/38-Asbestos-Survey-_Rev_0.pdf before running the demo reset.",
            file=sys.stderr,
        )
        return 2

    if STORAGE_ROOT.exists():
        shutil.rmtree(STORAGE_ROOT)

    seed_demo_environment()

    document_dir = _document_dir(DOCUMENT_ID)
    document_dir.mkdir(parents=True, exist_ok=True)
    stored_pdf = document_dir / SAMPLE_PDF.name
    shutil.copyfile(SAMPLE_PDF, stored_pdf)

    parsed = parse_pdf(DOCUMENT_ID, stored_pdf, SAMPLE_PDF.name)
    extraction = extract_register(DOCUMENT_ID)
    candidates = generate_quote_candidates(DOCUMENT_ID)
    priced = price_quote_candidates(DOCUMENT_ID)
    if extraction is None or candidates is None or priced is None:
        print("Demo reset failed before pricing.", file=sys.stderr)
        return 1

    for line in priced.lines:
        if line.excluded_from_pricing:
            continue
        result = resolve_priced_quote_line_review(
            DOCUMENT_ID,
            line.id,
            ResolveReviewRequest(
                reason=f"Demo reset accepted review gate for {line.description}.",
                user_id="demo-estimator",
                assumptions_accepted=True,
                exclusions_accepted=True,
            ),
        )
        if result is not None:
            priced = result

    package = export_quote(
        DOCUMENT_ID,
        QuoteExportRequest(
            client_name="Tauraroa Area School",
            project_name="Vendor demo asbestos quote",
            site_address="Tauraroa Area School, Northland, New Zealand",
            quote_number="TQ-DEMO-READY",
            scope_summary="Vendor-demo reviewed quote package generated from the real asbestos demolition survey.",
        ),
    )
    if package is None:
        print("Demo reset failed during export.", file=sys.stderr)
        return 1

    # --- RAS-style Revolve demo: same survey, exported as a Revolve "Estimate" ---
    revolve_package = _seed_revolve_job()

    print("TraceQuote AI demo reset complete.")
    print(f"Document ID: {DOCUMENT_ID}")
    print(f"Parsed pages: {parsed.page_count}")
    print(f"Register items: {len(extraction.items)}")
    print(f"Quote candidates: {len(candidates.candidates)}")
    print(f"Priced lines: {len(priced.lines)}")
    print(f"Quote number: {package.quote_number}")
    print("Seeded users: admin@privexa.co, test@privexa.co")
    print("Seeded organisations: Demo Asbestos Services Ltd (generic), Revolve Asbestos Solutions Demo (RAS-style)")
    print(f"PDF download endpoint: http://127.0.0.1:8000/documents/{DOCUMENT_ID}/export-quote/pdf")
    if revolve_package is not None:
        print(f"Revolve RAS-style quote: {revolve_package.quote_number}")
        print(f"Revolve PDF endpoint: http://127.0.0.1:8000/documents/{REVOLVE_DOCUMENT_ID}/export-quote/pdf")
    return 0


def _seed_revolve_job():
    """Process the same survey under the Revolve org so its RAS-style estimate is export-ready."""
    document_dir = _document_dir(REVOLVE_DOCUMENT_ID, organisation_id=REVOLVE_ORGANISATION_ID)
    document_dir.mkdir(parents=True, exist_ok=True)
    stored_pdf = document_dir / SAMPLE_PDF.name
    shutil.copyfile(SAMPLE_PDF, stored_pdf)

    parse_pdf(REVOLVE_DOCUMENT_ID, stored_pdf, SAMPLE_PDF.name, organisation_id=REVOLVE_ORGANISATION_ID)
    extract_register(REVOLVE_DOCUMENT_ID)
    generate_quote_candidates(REVOLVE_DOCUMENT_ID)
    priced = price_quote_candidates(REVOLVE_DOCUMENT_ID)
    if priced is None:
        return None
    for line in priced.lines:
        if line.excluded_from_pricing:
            continue
        resolve_priced_quote_line_review(
            REVOLVE_DOCUMENT_ID,
            line.id,
            ResolveReviewRequest(
                reason=f"Demo reset accepted review gate for {line.description}.",
                user_id="demo-estimator",
                assumptions_accepted=True,
                exclusions_accepted=True,
            ),
        )
    # quote_number omitted → uses the org's RAS prefix.
    return export_quote(
        REVOLVE_DOCUMENT_ID,
        QuoteExportRequest(
            client_name="Tauraroa Area School",
            project_name="Asbestos removal works",
            site_address="Tauraroa Area School, Northland, New Zealand",
            scope_summary="RAS-style vendor-demo estimate generated from the asbestos demolition survey.",
        ),
    )


if __name__ == "__main__":
    raise SystemExit(main())
