from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

from .document_parser import _document_dir, load_parsed_document, resolve_document_organisation_id
from .organisation_store import get_active_pricebook, get_organisation_settings
from .pricebook import GST_RATE, PRICEBOOK_VERSION, get_seed_pricebook
from .quote_candidate_mapper import generate_quote_candidates, load_quote_candidates
from .storage_paths import atomic_write_text
from .schemas import (
    ApprovalReadinessCheck,
    ApprovalReadinessResult,
    AuditEvent,
    EstimatorEdit,
    PricedQuoteLine,
    PricedQuoteLineEditRequest,
    PricedQuoteResult,
    PricingReviewStatus,
    PricingWarning,
    PricebookRule,
    QuoteCandidateLine,
    QuoteCandidateGenerationResult,
    ResolveReviewRequest,
    SeedPricebookRule,
)


PRICING_ENGINE_VERSION = "phase-5-deterministic-pricing-v1"


class PricingLineNotFound(ValueError):
    pass


class PricingValidationError(ValueError):
    pass


def _priced_lines_path(document_id: str) -> Path:
    return _document_dir(document_id) / "priced_quote_lines.json"


def load_priced_quote_lines(document_id: str) -> PricedQuoteResult | None:
    path = _priced_lines_path(document_id)
    if not path.exists():
        return None
    return PricedQuoteResult.model_validate_json(path.read_text(encoding="utf-8"))


def save_priced_quote_lines(result: PricedQuoteResult) -> None:
    path = _priced_lines_path(result.document_id)
    path.parent.mkdir(parents=True, exist_ok=True)
    atomic_write_text(path, result.model_dump_json(indent=2))


def price_quote_candidates(document_id: str) -> PricedQuoteResult | None:
    candidates = load_quote_candidates(document_id) or generate_quote_candidates(document_id)
    if candidates is None:
        return None

    organisation_id = _document_organisation_id(document_id)
    pricebook, pricebook_version, gst_rate = _active_rules_for_document(organisation_id)
    warnings: list[PricingWarning] = []
    lines: list[PricedQuoteLine] = []

    for candidate in candidates.candidates:
        rule = _match_rule(candidate, pricebook)
        if rule is None:
            warnings.append(
                PricingWarning(
                    quote_candidate_id=candidate.id,
                    message=f"No active pricebook rule matched quote candidate {candidate.id}.",
                    severity="warning",
                )
            )
            rule = _fallback_review_rule(candidate)
        lines.append(_price_candidate(candidate, rule, gst_rate=gst_rate, organisation_id=organisation_id))

    subtotal = round(sum(line.subtotal_ex_gst or 0 for line in lines), 2)
    gst = round(sum(line.gst or 0 for line in lines), 2)
    total = round(sum(line.total_inc_gst or 0 for line in lines), 2)

    result = PricedQuoteResult(
        organisation_id=organisation_id,
        document_id=document_id,
        pricing_engine_version=PRICING_ENGINE_VERSION,
        source_mapper_version=candidates.mapper_version,
        pricebook_version=pricebook_version,
        lines=lines,
        warnings=warnings,
        subtotal_ex_gst=subtotal,
        gst=gst,
        total_inc_gst=total,
        approval_status="blocked",
        estimator_edits=[],
        audit_events=[],
        created_at=datetime.now(timezone.utc),
    )
    save_priced_quote_lines(result)
    return result


def edit_priced_quote_line(
    document_id: str,
    line_id: str,
    request: PricedQuoteLineEditRequest,
) -> PricedQuoteResult | None:
    result = load_priced_quote_lines(document_id)
    if result is None:
        return None
    line = _find_line(result, line_id)
    if line is None:
        raise PricingLineNotFound(f"Priced quote line not found: {line_id}")
    if line.excluded_from_pricing:
        raise PricingValidationError("Excluded/NAD lines cannot be price-edited unless first reclassified by an estimator.")

    edits_before = len(result.estimator_edits)
    changed_fields = {
        "quantity": request.quantity,
        "unit_rate": request.unit_rate,
        "risk_multiplier": request.risk_multiplier,
        "margin": request.margin,
    }
    for field_name, new_value in changed_fields.items():
        if new_value is None:
            continue
        previous_value = getattr(line, field_name)
        if previous_value == new_value:
            continue
        setattr(line, field_name, new_value)
        result.estimator_edits.append(
            _edit_record(
                document_id=document_id,
                line_id=line.id,
                field_name=field_name,
                previous_value=previous_value,
                new_value=new_value,
                reason=request.reason,
                user_id=request.user_id,
            )
        )

    if len(result.estimator_edits) == edits_before:
        raise PricingValidationError("Edit request did not change any editable pricing field.")

    _recalculate_line(line)
    line.review_status = "review_required"
    line.review_required = True
    line.approval_status = "not_ready"
    line.reviewed_by = None
    line.reviewed_at = None
    line.review_resolution_reason = None
    line.assumptions_accepted = False
    line.exclusions_accepted = False

    result.audit_events.append(
        _audit_event(
            document_id=document_id,
            actor_id=request.user_id,
            event_type="estimator.priced_line_edited",
            payload={"line_id": line.id, "reason": request.reason},
        )
    )
    _refresh_totals_and_readiness(result)
    save_priced_quote_lines(result)
    return result


def resolve_priced_quote_line_review(
    document_id: str,
    line_id: str,
    request: ResolveReviewRequest,
) -> PricedQuoteResult | None:
    result = load_priced_quote_lines(document_id)
    if result is None:
        return None
    line = _find_line(result, line_id)
    if line is None:
        raise PricingLineNotFound(f"Priced quote line not found: {line_id}")
    if line.excluded_from_pricing:
        raise PricingValidationError("Excluded/NAD lines do not require review resolution.")
    if not request.assumptions_accepted or not request.exclusions_accepted:
        raise PricingValidationError("Assumptions and exclusions must be accepted to resolve review.")

    now = datetime.now(timezone.utc)
    previous_status = line.review_status
    line.review_status = "accepted"
    line.review_required = False
    line.approval_status = "ready_for_approval"
    line.assumptions_accepted = request.assumptions_accepted
    line.exclusions_accepted = request.exclusions_accepted
    line.reviewed_by = request.user_id
    line.reviewed_at = now
    line.review_resolution_reason = request.reason

    result.estimator_edits.append(
        _edit_record(
            document_id=document_id,
            line_id=line.id,
            field_name="review_status",
            previous_value=previous_status,
            new_value="accepted",
            reason=request.reason,
            user_id=request.user_id,
        )
    )
    result.audit_events.append(
        _audit_event(
            document_id=document_id,
            actor_id=request.user_id,
            event_type="estimator.approval_gate_reviewed",
            payload={
                "line_id": line.id,
                "assumptions_accepted": request.assumptions_accepted,
                "exclusions_accepted": request.exclusions_accepted,
                "reason": request.reason,
            },
        )
    )
    _refresh_totals_and_readiness(result)
    save_priced_quote_lines(result)
    return result


def get_approval_readiness(document_id: str) -> ApprovalReadinessResult | None:
    result = load_priced_quote_lines(document_id)
    if result is None:
        return None
    readiness = _approval_readiness(result)
    result.approval_status = readiness.approval_status
    save_priced_quote_lines(result)
    return readiness


PricebookRuleLike = SeedPricebookRule | PricebookRule


def _document_organisation_id(document_id: str) -> str:
    parsed = load_parsed_document(document_id)
    if parsed is not None:
        return parsed.organisation_id
    return resolve_document_organisation_id(document_id)


def _active_rules_for_document(organisation_id: str) -> tuple[list[PricebookRuleLike], str, float]:
    active_pricebook = get_active_pricebook(organisation_id)
    if active_pricebook is not None and active_pricebook.rules:
        settings = get_organisation_settings(organisation_id)
        gst_rate = settings.gst_rate if settings is not None else GST_RATE
        active_rules = [rule for rule in active_pricebook.rules if rule.active]
        if active_rules:
            return active_rules, active_pricebook.version, gst_rate
    return get_seed_pricebook(), PRICEBOOK_VERSION, GST_RATE


def _match_rule(candidate: QuoteCandidateLine, pricebook: list[PricebookRuleLike]) -> PricebookRuleLike | None:
    description = candidate.description.lower()
    if candidate.review_status == "excluded_from_pricing":
        return _excluded_rule(pricebook)

    if candidate.section == "Provisional / No Access":
        no_access_rule = _best_rule(pricebook, candidate)
        if no_access_rule is not None:
            return no_access_rule

    for rule in pricebook:
        if not _rule_active(rule):
            continue
        if _rule_section(rule) != candidate.section:
            continue
        keywords = _rule_material_keywords(rule)
        if keywords and not any(keyword in description for keyword in keywords):
            continue
        if not _class_matches(rule, candidate):
            continue
        if not _access_matches(rule, candidate):
            continue
        return rule

    return None


def _rule_by_id(pricebook: list[PricebookRuleLike], rule_id: str) -> PricebookRuleLike | None:
    for rule in pricebook:
        if rule.id == rule_id:
            return rule
    return None


def _excluded_rule(pricebook: list[PricebookRuleLike]) -> PricebookRuleLike | None:
    return _rule_by_id(pricebook, "pb-excluded-nad") or next(
        (rule for rule in pricebook if _rule_method(rule) == "excluded" and _rule_active(rule)),
        None,
    )


def _best_rule(pricebook: list[PricebookRuleLike], candidate: QuoteCandidateLine) -> PricebookRuleLike | None:
    matches = [
        rule
        for rule in pricebook
        if _rule_active(rule)
        and _rule_section(rule) == candidate.section
        and _class_matches(rule, candidate)
        and _access_matches(rule, candidate)
    ]
    if not matches:
        return None
    description = candidate.description.lower()
    for rule in matches:
        keywords = _rule_material_keywords(rule)
        if keywords and any(keyword in description for keyword in keywords):
            return rule
    return matches[0]


def _fallback_review_rule(candidate: QuoteCandidateLine) -> SeedPricebookRule:
    return SeedPricebookRule(
        id="pb-fallback-review",
        name="Estimator review fallback",
        section=candidate.section,
        pricing_method="fixed",
        unit=candidate.unit or "allowance",
        unit_rate=0.0,
        risk_multiplier=1.0,
        margin=0.0,
        material_keywords=[],
        default_quantity=candidate.quantity or 1,
        default_assumptions=["No deterministic seed pricebook rule matched this candidate."],
        default_exclusions=["Pricing remains blocked until estimator selects or adds a rule."],
        explanation_template="Fallback zero-value review rule applied because no seed rule matched.",
    )


def _price_candidate(
    candidate: QuoteCandidateLine,
    rule: PricebookRuleLike,
    *,
    gst_rate: float,
    organisation_id: str,
) -> PricedQuoteLine:
    if _rule_method(rule) == "excluded":
        return _excluded_line(candidate, rule, organisation_id=organisation_id)

    quantity = _priced_quantity(candidate, rule)
    unit = _priced_unit(candidate, rule)
    unit_rate = rule.unit_rate or 0.0
    base_cost = round(quantity * unit_rate, 2)
    subtotal_before_minimum = round(base_cost * rule.risk_multiplier * (1 + rule.margin), 2)
    minimum_charge = _rule_minimum_charge(rule)
    subtotal_ex_gst = max(subtotal_before_minimum, minimum_charge) if minimum_charge is not None else subtotal_before_minimum
    gst = round(subtotal_ex_gst * gst_rate, 2) if _rule_gst_taxable(rule) else 0.0
    total_inc_gst = round(subtotal_ex_gst + gst, 2)
    review_status = _review_status(candidate)
    if _rule_review_required(rule) and review_status == "ai_draft":
        review_status = "review_required"
    assumptions = _dedupe(candidate.assumptions + _rule_assumptions(rule))
    exclusions = _dedupe(candidate.exclusions + _rule_exclusions(rule))

    return PricedQuoteLine(
        organisation_id=organisation_id,
        id=f"pql-{candidate.id}",
        document_id=candidate.document_id,
        quote_candidate_id=candidate.id,
        section=candidate.section,
        description=candidate.description,
        quantity=quantity,
        unit=unit,
        unit_rate=unit_rate,
        base_cost=base_cost,
        risk_multiplier=rule.risk_multiplier,
        margin=rule.margin,
        subtotal_ex_gst=subtotal_ex_gst,
        gst=gst,
        total_inc_gst=total_inc_gst,
        pricing_rule_id=rule.id,
        pricing_rule_name=rule.name,
        pricing_explanation=_pricing_explanation(candidate, rule, quantity, unit, unit_rate, gst_rate),
        source_register_item_ids=candidate.source_register_item_ids,
        source_evidence=candidate.source_evidence,
        source_pages=candidate.source_pages,
        confidence=candidate.confidence,
        assumptions=assumptions,
        exclusions=exclusions,
        review_status=review_status,
        review_required=review_status == "review_required",
        approval_status="not_ready",
        excluded_from_pricing=False,
    )


def _excluded_line(candidate: QuoteCandidateLine, rule: PricebookRuleLike, *, organisation_id: str) -> PricedQuoteLine:
    return PricedQuoteLine(
        organisation_id=organisation_id,
        id=f"pql-{candidate.id}",
        document_id=candidate.document_id,
        quote_candidate_id=candidate.id,
        section=candidate.section,
        description=candidate.description,
        quantity=candidate.quantity,
        unit=candidate.unit,
        unit_rate=None,
        base_cost=None,
        risk_multiplier=1.0,
        margin=0.0,
        subtotal_ex_gst=None,
        gst=None,
        total_inc_gst=None,
        pricing_rule_id=rule.id,
        pricing_rule_name=rule.name,
        pricing_explanation=_rule_explanation_template(rule),
        source_register_item_ids=candidate.source_register_item_ids,
        source_evidence=candidate.source_evidence,
        source_pages=candidate.source_pages,
        confidence=candidate.confidence,
        assumptions=_dedupe(candidate.assumptions + _rule_assumptions(rule)),
        exclusions=_dedupe(candidate.exclusions + _rule_exclusions(rule)),
        review_status="excluded_from_pricing",
        review_required=False,
        approval_status="not_ready",
        excluded_from_pricing=True,
        assumptions_accepted=True,
        exclusions_accepted=True,
    )


def _priced_quantity(candidate: QuoteCandidateLine, rule: PricebookRuleLike) -> float:
    if _rule_method(rule) == "fixed":
        return _rule_default_quantity(rule) or 1
    if candidate.quantity is not None:
        return candidate.quantity
    return _rule_default_quantity(rule) or 1


def _priced_unit(candidate: QuoteCandidateLine, rule: PricebookRuleLike) -> str:
    if _rule_method(rule) == "fixed":
        return rule.unit
    return candidate.unit or rule.unit


def _review_status(candidate: QuoteCandidateLine) -> PricingReviewStatus:
    if candidate.review_status == "excluded_from_pricing":
        return "excluded_from_pricing"
    if candidate.review_required or candidate.section in {
        "Class A / Friable Removal",
        "Provisional / No Access",
        "Waste / Disposal Placeholder",
        "Site Establishment",
    }:
        return "review_required"
    return "ai_draft"


def _pricing_explanation(
    candidate: QuoteCandidateLine,
    rule: PricebookRuleLike,
    quantity: float,
    unit: str,
    unit_rate: float,
    gst_rate: float,
) -> str:
    del candidate
    minimum = _rule_minimum_charge(rule)
    minimum_note = f" Minimum charge ${minimum:,.2f} enforced." if minimum is not None else ""
    gst_note = f" GST {(gst_rate * 100):g}% applies." if _rule_gst_taxable(rule) else " GST not applied."
    return (
        f"{_rule_explanation_template(rule)} Calculation: {quantity:g} {unit} x ${unit_rate:,.2f} "
        f"x risk {rule.risk_multiplier:g} x margin {(rule.margin * 100):g}%.{minimum_note}{gst_note}"
    )


def _rule_active(rule: PricebookRuleLike) -> bool:
    return getattr(rule, "active", True)


def _rule_section(rule: PricebookRuleLike) -> str:
    return rule.section


def _rule_method(rule: PricebookRuleLike) -> str:
    method = rule.pricing_method
    if method in {"per_sqm", "per_piece", "per_hour"}:
        return "per_unit"
    return method


def _rule_material_keywords(rule: PricebookRuleLike) -> list[str]:
    if isinstance(rule, SeedPricebookRule):
        return [keyword.lower() for keyword in rule.material_keywords]
    if rule.material_match:
        return [part.strip().lower() for part in rule.material_match.split(",") if part.strip()]
    return []


def _rule_default_quantity(rule: PricebookRuleLike) -> float | None:
    if isinstance(rule, SeedPricebookRule):
        return rule.default_quantity
    if rule.pricing_method == "fixed":
        return 1
    return None


def _rule_assumptions(rule: PricebookRuleLike) -> list[str]:
    return rule.default_assumptions if isinstance(rule, SeedPricebookRule) else rule.assumptions


def _rule_exclusions(rule: PricebookRuleLike) -> list[str]:
    return rule.default_exclusions if isinstance(rule, SeedPricebookRule) else rule.exclusions


def _rule_explanation_template(rule: PricebookRuleLike) -> str:
    if isinstance(rule, SeedPricebookRule):
        return rule.explanation_template
    return f"Active organisation pricebook rule '{rule.name}' matched by category/material/class/access settings."


def _rule_gst_taxable(rule: PricebookRuleLike) -> bool:
    return True if isinstance(rule, SeedPricebookRule) else rule.gst_taxable


def _rule_minimum_charge(rule: PricebookRuleLike) -> float | None:
    return rule.minimum_charge


def _rule_review_required(rule: PricebookRuleLike) -> bool:
    return True if isinstance(rule, SeedPricebookRule) else rule.review_required


def _class_matches(rule: PricebookRuleLike, candidate: QuoteCandidateLine) -> bool:
    class_match = getattr(rule, "class_match", None)
    if class_match is None:
        return True
    haystack = f"{candidate.section} {candidate.description}".lower()
    return class_match.lower() in haystack


def _access_matches(rule: PricebookRuleLike, candidate: QuoteCandidateLine) -> bool:
    if isinstance(rule, SeedPricebookRule):
        access = rule.access_status_match
        if access is None:
            return True
        if access == "no_access":
            return "no access" in candidate.section.lower() or "no-access" in candidate.description.lower()
        if access == "limited_access":
            return "limited" in candidate.description.lower()
        return True
    if rule.access_match == "normal":
        return True
    haystack = f"{candidate.section} {candidate.description}".lower()
    if rule.access_match == "no-access":
        return "no access" in haystack or "no-access" in haystack
    if rule.access_match == "limited-access":
        return "limited" in haystack
    return True


def _dedupe(values: list[str]) -> list[str]:
    seen: set[str] = set()
    output: list[str] = []
    for value in values:
        if value not in seen:
            seen.add(value)
            output.append(value)
    return output


def _find_line(result: PricedQuoteResult, line_id: str) -> PricedQuoteLine | None:
    for line in result.lines:
        if line.id == line_id:
            return line
    return None


def _edit_record(
    *,
    document_id: str,
    line_id: str,
    field_name: str,
    previous_value: object,
    new_value: object,
    reason: str,
    user_id: str,
) -> EstimatorEdit:
    return EstimatorEdit(
        id=f"edit-{uuid4().hex[:12]}",
        workup_id=document_id,
        entity_type="priced_quote_line",
        entity_id=line_id,
        field_name=field_name,
        previous_value=previous_value,
        new_value=new_value,
        reason=reason,
        user_id=user_id,
        created_at=datetime.now(timezone.utc),
    )


def _audit_event(document_id: str, actor_id: str, event_type: str, payload: dict[str, object]) -> AuditEvent:
    return AuditEvent(
        id=f"audit-{uuid4().hex[:12]}",
        workup_id=document_id,
        actor_type="user",
        actor_id=actor_id,
        event_type=event_type,
        payload=payload,
        created_at=datetime.now(timezone.utc),
    )


def _recalculate_line(line: PricedQuoteLine) -> None:
    if line.quantity is None or line.unit_rate is None:
        line.base_cost = None
        line.subtotal_ex_gst = None
        line.gst = None
        line.total_inc_gst = None
        return

    line.base_cost = round(line.quantity * line.unit_rate, 2)
    line.subtotal_ex_gst = round(line.base_cost * line.risk_multiplier * (1 + line.margin), 2)
    line.gst = round(line.subtotal_ex_gst * GST_RATE, 2)
    line.total_inc_gst = round(line.subtotal_ex_gst + line.gst, 2)


def _refresh_totals_and_readiness(result: PricedQuoteResult) -> None:
    result.subtotal_ex_gst = round(sum(line.subtotal_ex_gst or 0 for line in result.lines), 2)
    result.gst = round(sum(line.gst or 0 for line in result.lines), 2)
    result.total_inc_gst = round(sum(line.total_inc_gst or 0 for line in result.lines), 2)
    result.approval_status = _approval_readiness(result).approval_status


def _approval_readiness(result: PricedQuoteResult) -> ApprovalReadinessResult:
    review_required_ids = [
        line.id
        for line in result.lines
        if not line.excluded_from_pricing and (line.review_required or line.review_status == "review_required")
    ]
    no_access_ids = [
        line.id
        for line in result.lines
        if not line.excluded_from_pricing
        and line.section == "Provisional / No Access"
        and (not line.assumptions_accepted or not line.exclusions_accepted)
    ]
    class_a_ids = [
        line.id
        for line in result.lines
        if not line.excluded_from_pricing
        and line.section == "Class A / Friable Removal"
        and line.review_status != "accepted"
    ]
    provisional_ids = [
        line.id
        for line in result.lines
        if not line.excluded_from_pricing
        and (
            "Provisional" in line.section
            or "provisional" in line.description.lower()
            or line.section in {"Waste / Disposal Placeholder", "Site Establishment"}
        )
        and line.review_status != "accepted"
    ]
    approval_events = [
        event
        for event in result.audit_events
        if event.event_type in {"estimator.approval_gate_reviewed", "estimator.quote_approval_recorded"}
    ]

    checks = [
        _check(
            "all_review_lines_resolved",
            "All review-required lines resolved",
            review_required_ids,
            "Every review-required priced line has been resolved or accepted.",
        ),
        _check(
            "no_access_assumptions_accepted",
            "No-access assumptions and exclusions accepted",
            no_access_ids,
            "No-access/power lines have accepted assumptions and exclusions.",
        ),
        _check(
            "class_a_reviewed",
            "Class A/friable lines estimator-reviewed",
            class_a_ids,
            "Class A/friable lines have estimator review records.",
        ),
        _check(
            "provisional_allowances_accepted",
            "Provisional allowances accepted",
            provisional_ids,
            "Site, waste, and provisional allowances have been accepted.",
        ),
        ApprovalReadinessCheck(
            id="estimator_approval_event_exists",
            label="Estimator approval event exists",
            status="passed" if approval_events else "blocked",
            details="At least one estimator review/approval event has been recorded."
            if approval_events
            else "Estimator must resolve at least one approval gate before export readiness.",
            blocking_line_ids=[],
        ),
    ]
    unresolved = sorted({line_id for check in checks for line_id in check.blocking_line_ids})
    approval_status = "ready_for_approval" if all(check.status == "passed" for check in checks) else "blocked"
    return ApprovalReadinessResult(
        document_id=result.document_id,
        approval_status=approval_status,
        checks=checks,
        unresolved_line_ids=unresolved,
        created_at=datetime.now(timezone.utc),
    )


def _check(id: str, label: str, blocking_line_ids: list[str], passed_details: str) -> ApprovalReadinessCheck:
    return ApprovalReadinessCheck(
        id=id,
        label=label,
        status="blocked" if blocking_line_ids else "passed",
        details=passed_details if not blocking_line_ids else f"{len(blocking_line_ids)} line(s) still block this gate.",
        blocking_line_ids=blocking_line_ids,
    )
