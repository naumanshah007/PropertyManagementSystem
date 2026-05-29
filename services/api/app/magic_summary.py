from __future__ import annotations

from datetime import datetime, timezone

from .document_parser import DEFAULT_ORGANISATION_ID, load_parsed_document
from .pricing_engine import load_priced_quote_lines, price_quote_candidates
from .quote_candidate_mapper import generate_quote_candidates, load_quote_candidates
from .register_extractor import extract_register, load_register_extraction
from .schemas import ExtractedRegisterItem, MagicExtractionSummary


def build_magic_summary(document_id: str, organisation_id: str = DEFAULT_ORGANISATION_ID) -> MagicExtractionSummary | None:
    parsed = load_parsed_document(document_id, organisation_id=organisation_id)
    if parsed is None:
        return None
    extraction = load_register_extraction(document_id) or extract_register(document_id)
    candidates = load_quote_candidates(document_id) or generate_quote_candidates(document_id)
    priced = load_priced_quote_lines(document_id) or price_quote_candidates(document_id)
    items = extraction.items if extraction else []
    candidate_count = len(candidates.candidates) if candidates else 0
    priced_count = len(priced.lines) if priced else 0
    confidences = [item.confidence for item in items]
    sqm_total = sum(item.extent_quantity or 0 for item in items if (item.extent_unit or "").lower() == "sqm")
    source_pages = sorted({item.source_page for item in items})

    return MagicExtractionSummary(
        organisation_id=organisation_id,
        document_id=document_id,
        survey_type="Asbestos Demolition Survey" if "Asbestos Demolition Survey" in parsed.pages[0].text else "Unknown survey/report",
        total_pages_parsed=parsed.page_count,
        register_items_extracted=len(items),
        quote_ready_items=sum(1 for item in items if item.extraction_category == "quote_ready"),
        review_required_items=sum(1 for item in items if item.extraction_category == "review_required"),
        reference_only_items=sum(1 for item in items if item.extraction_category == "reference_only"),
        quote_candidates_generated=candidate_count,
        priced_lines_generated=priced_count,
        class_a_items=sum(1 for item in items if item.friability_class == "Class A"),
        class_b_items=sum(1 for item in items if item.friability_class == "Class B"),
        no_access_items=sum(1 for item in items if item.access_status == "no_access"),
        limited_access_items=sum(1 for item in items if item.access_status == "limited_access"),
        nad_excluded_items=sum(1 for item in items if item.asbestos_result == "NAD" or item.review_status == "excluded_from_pricing"),
        total_extracted_sqm=round(sqm_total, 2),
        source_pages_detected=source_pages,
        confidence_summary={
            "average": round(sum(confidences) / len(confidences), 3) if confidences else 0,
            "min": round(min(confidences), 3) if confidences else 0,
            "max": round(max(confidences), 3) if confidences else 0,
        },
        magic_entities={
            "materials": _unique(item.material for item in items),
            "locations": _unique(item.location for item in items),
            "quantities": _unique(_quantity_label(item) for item in items if item.extent_quantity is not None),
            "access_risks": _unique(item.access_status for item in items if item.access_status != "accessible"),
            "friability_classes": _unique(item.friability_class for item in items),
            "recommendations": _unique(item.recommendation for item in items if item.recommendation),
            "pricing_triggers": _pricing_triggers(items),
            "assumptions": _unique(assumption for line in (priced.lines if priced else []) for assumption in line.assumptions),
            "exclusions": _unique(exclusion for line in (priced.lines if priced else []) for exclusion in line.exclusions),
        },
        created_at=datetime.now(timezone.utc),
    )


def _quantity_label(item: ExtractedRegisterItem) -> str:
    return f"{item.extent_quantity:g} {item.extent_unit or ''}".strip()


def _pricing_triggers(items: list[ExtractedRegisterItem]) -> list[str]:
    triggers: list[str] = []
    for item in items:
        if item.friability_class == "Class A":
            triggers.append("Class A/friable provisional pricing")
        if item.friability_class == "Class B":
            triggers.append("Class B controlled-removal pricing")
        if item.access_status == "no_access":
            triggers.append("No-access investigation allowance")
        if "fibre cement" in item.material.lower():
            triggers.append("Fibre cement sheet sqm rate")
        if "insulating board" in item.material.lower():
            triggers.append("Insulating board per-piece allowance")
        if item.asbestos_result == "NAD":
            triggers.append("NAD excluded from pricing")
    return _unique(triggers)


def _unique(values) -> list[str]:
    output: list[str] = []
    seen: set[str] = set()
    for value in values:
        if value is None:
            continue
        text = str(value)
        if text and text not in seen:
            seen.add(text)
            output.append(text)
    return output[:18]
