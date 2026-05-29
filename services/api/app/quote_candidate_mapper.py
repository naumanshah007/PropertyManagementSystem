from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

from .document_parser import _document_dir
from .storage_paths import atomic_write_text
from .register_extractor import extract_register, load_register_extraction
from .schemas import (
    ExtractedRegisterItem,
    QuoteCandidateEvidence,
    QuoteCandidateGenerationResult,
    QuoteCandidateGenerationWarning,
    QuoteCandidateLine,
    QuoteCandidateReviewStatus,
    RegisterExtractionResult,
)


MAPPER_VERSION = "phase-4-deterministic-quote-candidate-v1"


def _quote_candidates_path(document_id: str) -> Path:
    return _document_dir(document_id) / "quote_candidates.json"


def load_quote_candidates(document_id: str) -> QuoteCandidateGenerationResult | None:
    path = _quote_candidates_path(document_id)
    if not path.exists():
        return None
    return QuoteCandidateGenerationResult.model_validate_json(path.read_text(encoding="utf-8"))


def save_quote_candidates(result: QuoteCandidateGenerationResult) -> None:
    path = _quote_candidates_path(result.document_id)
    path.parent.mkdir(parents=True, exist_ok=True)
    atomic_write_text(path, result.model_dump_json(indent=2))


def generate_quote_candidates(document_id: str) -> QuoteCandidateGenerationResult | None:
    extraction = load_register_extraction(document_id) or extract_register(document_id)
    if extraction is None:
        return None

    warnings: list[QuoteCandidateGenerationWarning] = []
    candidates: list[QuoteCandidateLine] = []
    # Only real scope drives the quote: quote_ready + review_required. Reference-only
    # (duplicate / TBC / unknown) rows stay as evidence and are never priced.
    scope_items = [
        item for item in extraction.items if item.extraction_category in {"quote_ready", "review_required"}
    ]

    if scope_items:
        candidates.append(_site_establishment_candidate(document_id, scope_items))

    for item in extraction.items:
        if item.extraction_category == "reference_only":
            # Deduplicated / unpriceable noise — visible in evidence, never priced.
            continue
        candidate = _map_register_item(document_id, item)
        if candidate is None:
            warnings.append(
                QuoteCandidateGenerationWarning(
                    register_item_id=item.id,
                    message=f"No quote candidate rule matched register item {item.id}.",
                    severity="warning",
                )
            )
            continue
        candidates.append(candidate)

    if scope_items:
        candidates.append(_waste_placeholder_candidate(document_id, scope_items))

    result = QuoteCandidateGenerationResult(
        organisation_id=extraction.organisation_id,
        document_id=document_id,
        mapper_version=MAPPER_VERSION,
        source_extraction_version=extraction.parser_version,
        candidates=candidates,
        warnings=warnings,
        created_at=datetime.now(timezone.utc),
    )
    save_quote_candidates(result)
    return result


def _map_register_item(document_id: str, item: ExtractedRegisterItem) -> QuoteCandidateLine | None:
    if item.asbestos_result == "NAD" or item.review_status == "excluded_from_pricing":
        return _candidate(
            document_id=document_id,
            id=f"qc-excluded-{item.id}",
            section="Excluded / NAD Findings",
            description=f"Excluded from asbestos pricing: {item.item} ({item.material})",
            quantity=item.extent_quantity,
            unit=item.extent_unit,
            items=[item],
            assumptions=["Item is treated as non-asbestos/NAD based on extracted register evidence."],
            exclusions=["Excluded from asbestos removal pricing unless estimator overrides."],
            reason="NAD/non-asbestos register item is not priced by default.",
            review_status="excluded_from_pricing",
        )

    if item.access_status == "no_access":
        return _candidate(
            document_id=document_id,
            id=f"qc-no-access-{item.id}",
            section="Provisional / No Access",
            description=f"Provisional investigation: {item.item} ({item.material})",
            quantity=item.extent_quantity,
            unit=item.extent_unit,
            items=[item],
            assumptions=[
                "Pricing requires power isolation or further inspection where services are live or inaccessible.",
                "No-access scope remains provisional until estimator confirms access and condition.",
            ],
            exclusions=["Electrical isolation, disconnection, and reinstatement by others unless separately included."],
            reason="No-access or live-services finding cannot be converted to a final removal allowance without review.",
            review_status="review_required",
        )

    if item.friability_class == "Class A" or "insulating board" in item.material.lower():
        return _candidate(
            document_id=document_id,
            id=f"qc-class-a-{item.id}",
            section="Class A / Friable Removal",
            description=f"Class A/friable provisional allowance: {item.item} ({item.material})",
            quantity=item.extent_quantity,
            unit=item.extent_unit,
            items=[item],
            assumptions=[
                "Class A/friable work requires estimator review and appropriate licensed removal controls.",
                "Quantity and condition may be incomplete where access is limited.",
            ],
            exclusions=["Expanded containment or assessor requirements beyond the confirmed scope."],
            reason="Class A or insulating-board item requires provisional review before pricing can be finalized.",
            review_status="review_required",
        )

    if item.access_status == "limited_access":
        return _candidate(
            document_id=document_id,
            id=f"qc-limited-access-{item.id}",
            section="Provisional / No Access",
            description=f"Limited-access provisional allowance: {item.item} ({item.material})",
            quantity=item.extent_quantity,
            unit=item.extent_unit,
            items=[item],
            assumptions=["Quantity and condition may be incomplete due to limited access."],
            exclusions=["Additional concealed material discovered after access is opened."],
            reason="Limited-access register item remains review-required before final pricing.",
            review_status="review_required",
        )

    if item.friability_class == "Class B" and "fibre cement sheet" in item.material.lower():
        review_status: QuoteCandidateReviewStatus = "review_required" if item.extent_quantity is None else "ai_draft"
        return _candidate(
            document_id=document_id,
            id=f"qc-class-b-{item.id}",
            section="Class B Removal",
            description=f"Controlled Class B removal: {item.item} ({item.material})",
            quantity=item.extent_quantity,
            unit=item.extent_unit,
            items=[item],
            assumptions=["Controlled Class B removal by licensed contractor based on extracted register extent."],
            exclusions=["Replacement materials, structural repairs, scaffolding, and access equipment unless separately included."],
            reason="Class B fibre cement sheet item can become a controlled-removal candidate line.",
            review_status=review_status,
        )

    return _candidate(
        document_id=document_id,
        id=f"qc-review-{item.id}",
        section="Provisional / No Access",
        description=f"Estimator review candidate: {item.item} ({item.material})",
        quantity=item.extent_quantity,
        unit=item.extent_unit,
        items=[item],
        assumptions=["Register item did not match a precise Phase 4 mapping rule."],
        exclusions=["Final pricing until estimator classification is complete."],
        reason="Fallback review candidate preserves traceability for unmatched extracted register item.",
        review_status="review_required",
    )


def _site_establishment_candidate(document_id: str, items: list[ExtractedRegisterItem]) -> QuoteCandidateLine:
    return _candidate(
        document_id=document_id,
        id="qc-site-establishment",
        section="Site Establishment",
        description="Site establishment, compliance documentation, and controlled work area setup placeholder",
        quantity=1,
        unit="item",
        items=items,
        assumptions=["Client provides site access, water, toilet facilities, and parking."],
        exclusions=["Scaffolding, power isolation, and third-party assessor fees unless separately included."],
        reason="Asbestos removal work requires site establishment before any removal or investigation lines are finalized.",
        review_status="review_required",
    )


def _waste_placeholder_candidate(document_id: str, items: list[ExtractedRegisterItem]) -> QuoteCandidateLine:
    return _candidate(
        document_id=document_id,
        id="qc-waste-disposal-placeholder",
        section="Waste / Disposal Placeholder",
        description="Waste handling and compliant asbestos disposal placeholder",
        quantity=None,
        unit="placeholder",
        items=items,
        assumptions=["Waste allowance will be calculated after estimator confirms final quantities and material handling."],
        exclusions=["Unexpected mixed demolition waste and contaminated soil disposal."],
        reason="Waste/disposal line is required but full pricing is deferred until the pricing engine phase.",
        review_status="review_required",
    )


def _candidate(
    *,
    document_id: str,
    id: str,
    section: str,
    description: str,
    quantity: float | None,
    unit: str | None,
    items: list[ExtractedRegisterItem],
    assumptions: list[str],
    exclusions: list[str],
    reason: str,
    review_status: QuoteCandidateReviewStatus,
) -> QuoteCandidateLine:
    evidence = [
        QuoteCandidateEvidence(
            organisation_id=item.organisation_id,
            register_item_id=item.id,
            page_number=item.source_page,
            text=item.source_evidence.text,
        )
        for item in items
    ]
    source_pages = sorted({item.source_page for item in items})
    confidence = min(item.confidence for item in items)
    return QuoteCandidateLine(
        organisation_id=items[0].organisation_id,
        id=id,
        document_id=document_id,
        section=section,
        description=description,
        quantity=quantity,
        unit=unit,
        source_register_item_ids=[item.id for item in items],
        source_evidence=evidence,
        source_pages=source_pages,
        confidence=round(confidence, 2),
        assumptions=assumptions,
        exclusions=exclusions,
        reason=reason,
        review_status=review_status,
        review_required=review_status == "review_required",
        approval_status="not_ready",
    )
