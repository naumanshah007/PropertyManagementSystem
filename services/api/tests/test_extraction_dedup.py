"""Extraction deduplication + quote-ready classification.

Proves the pipeline produces a professional quote draft, not a raw extraction
dump: duplicate table rows collapse to reference-only, detailed items win over
summaries, TBC/unknown rows aren't auto-priced, no-access/Class A stay
review-required, NAD stays excluded, and priced lines shrink to real scope.
"""

from __future__ import annotations

from uuid import uuid4

from auth_helpers import PLATFORM_ADMIN_HEADERS  # noqa: F401 (ensures APP_ENV=local)
from app.register_extractor import _classify_and_dedupe, save_register_extraction
from app.quote_candidate_mapper import generate_quote_candidates
from app.schemas import (
    ExtractedRegisterItem,
    RegisterExtractionResult,
    RegisterSourceEvidence,
)
from datetime import datetime, timezone


def _item(
    *,
    id: str,
    building: str | None = "R10",
    location: str = "External / Building Envelope",
    item: str = "Flat cladding",
    material: str = "Fibre Cement Sheet - Flat Sheet",
    extent_quantity: float | None = 320.0,
    extent_unit: str | None = "sqm",
    friability_class: str = "Class B",
    asbestos_result: str = "positive",
    access_status: str = "accessible",
    confidence: float = 0.9,
) -> ExtractedRegisterItem:
    return ExtractedRegisterItem(
        organisation_id="org-demo-tracequote",
        id=id,
        document_id="dedup-doc",
        building=building,
        level=None,
        location=location,
        item=item,
        material=material,
        strategy_sample_id=None,
        extent_quantity=extent_quantity,
        extent_unit=extent_unit,
        fibre_type=None,
        friability_class=friability_class,  # type: ignore[arg-type]
        asbestos_result=asbestos_result,  # type: ignore[arg-type]
        access_status=access_status,  # type: ignore[arg-type]
        material_score=None,
        priority_risk_category=None,
        recommendation=None,
        source_page=18,
        source_evidence=RegisterSourceEvidence(
            organisation_id="org-demo-tracequote", document_id="dedup-doc", page_number=18, text="evidence"
        ),
        confidence=confidence,
        review_status="ai_draft",
        extraction_warnings=[],
    )


def _category(items: list[ExtractedRegisterItem]) -> dict[str, str]:
    _classify_and_dedupe(items)
    return {i.id: i.extraction_category for i in items}


# --------------------------------------------------------------------------- #
# Classification rules
# --------------------------------------------------------------------------- #


def test_clean_detailed_item_is_quote_ready() -> None:
    cats = _category([_item(id="detailed")])
    assert cats["detailed"] == "quote_ready"


def test_detailed_item_wins_over_summary_duplicate() -> None:
    detailed = _item(id="detailed", confidence=0.9)
    summary = _item(id="summary", confidence=0.58)  # same dedupe key, lower confidence
    cats = _category([summary, detailed])  # order shouldn't matter
    assert cats["detailed"] == "quote_ready"
    assert cats["summary"] == "reference_only"


def test_tbc_extent_is_not_quote_ready() -> None:
    cats = _category([_item(id="tbc", extent_quantity=None, extent_unit=None)])
    assert cats["tbc"] == "reference_only"


def test_unknown_material_is_not_quote_ready() -> None:
    cats = _category([_item(id="unk", material="Unknown material")])
    assert cats["unk"] == "reference_only"


def test_tbc_with_class_a_is_review_required() -> None:
    cats = _category([_item(id="tbc-a", extent_quantity=None, friability_class="Class A")])
    assert cats["tbc-a"] == "review_required"


def test_no_access_remains_review_required() -> None:
    cats = _category([_item(id="na", access_status="no_access")])
    assert cats["na"] == "review_required"


def test_class_a_remains_review_required() -> None:
    cats = _category([_item(id="ca", friability_class="Class A", material="Insulating Board", extent_quantity=4, extent_unit="pieces")])
    assert cats["ca"] == "review_required"


def test_presumed_remains_review_required() -> None:
    cats = _category([_item(id="pre", asbestos_result="presumed")])
    assert cats["pre"] == "review_required"


def test_nad_remains_excluded() -> None:
    nad = _item(id="nad", asbestos_result="NAD", friability_class="Unknown")
    nad.review_status = "excluded_from_pricing"
    cats = _category([nad])
    assert cats["nad"] == "excluded_from_pricing"


# --------------------------------------------------------------------------- #
# End-to-end: dedupe → candidate generation
# --------------------------------------------------------------------------- #


def _save_and_generate(items: list[ExtractedRegisterItem]):
    document_id = f"dedup-{uuid4().hex[:8]}"
    for i in items:
        i.document_id = document_id
        i.source_evidence.document_id = document_id
    _classify_and_dedupe(items)
    save_register_extraction(
        RegisterExtractionResult(
            organisation_id="org-demo-tracequote",
            document_id=document_id,
            parser_version="test",
            source_parser_version="test",
            items=items,
            warnings=[],
            created_at=datetime.now(timezone.utc),
        )
    )
    return generate_quote_candidates(document_id)


def test_duplicate_rows_do_not_create_duplicate_candidates() -> None:
    detailed = _item(id="detailed", confidence=0.9)
    duplicate = _item(id="duplicate", confidence=0.58)  # same scope, summary row

    result = _save_and_generate([detailed, duplicate])
    assert result is not None

    # The duplicate (reference_only) must not appear in any priced candidate.
    sourced_ids = {rid for c in result.candidates for rid in c.source_register_item_ids}
    assert "detailed" in sourced_ids
    assert "duplicate" not in sourced_ids


def test_reference_and_tbc_rows_shrink_priced_candidates() -> None:
    items = [
        _item(id="scope-1", building="R10", confidence=0.9),
        _item(id="scope-2", building="R12", item="External Cladding", extent_quantity=920, confidence=0.9),
        _item(id="dup-of-1", building="R10", confidence=0.55),       # duplicate -> reference_only
        _item(id="tbc", building="R30", extent_quantity=None),        # TBC -> reference_only
        _item(id="unknown", building="R31", material="Unknown material"),  # unknown -> reference_only
    ]
    result = _save_and_generate(items)
    assert result is not None

    sourced_ids = {rid for c in result.candidates for rid in c.source_register_item_ids}
    # Only the two real scope items are priced; the three noise rows are not.
    assert {"scope-1", "scope-2"}.issubset(sourced_ids)
    assert {"dup-of-1", "tbc", "unknown"}.isdisjoint(sourced_ids)
    # Candidates (site est + 2 scope + waste) are far fewer than 5 raw rows + scaffolding.
    assert len(result.candidates) <= 4
