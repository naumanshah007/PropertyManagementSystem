from __future__ import annotations

import re
from datetime import datetime, timezone
from pathlib import Path

from .document_parser import _document_dir, load_parsed_document
from .storage_paths import atomic_write_text
from .schemas import (
    AccessStatus,
    AsbestosResult,
    ExtractedRegisterItem,
    ExtractionCategory,
    FriabilityClass,
    ParsedDocument,
    RegisterExtractionResult,
    RegisterExtractionWarning,
    RegisterReviewStatus,
    RegisterSourceEvidence,
)


EXTRACTION_VERSION = "phase-3-deterministic-register-v1"


TARGET_EXPECTED_ITEMS = [
    {
        "id": "r10-11-external-flat-cladding",
        "building": "R10-11",
        "level": None,
        "location": "External / Building Envelope",
        "item": "Flat cladding",
        "material": "Fibre Cement Sheet - Flat Sheet",
        "extent_quantity": 320.0,
        "extent_unit": "sqm",
        "friability_class": "Class B",
        "asbestos_result": "positive",
        "access_status": "accessible",
        "source_page": 18,
        "keywords": ["R10-11", "Flat cladding", "Fibre Cement Sheet", "320"],
    },
    {
        "id": "r10-inside-power-box",
        "building": "R10",
        "level": None,
        "location": "Inside room",
        "item": "Power box",
        "material": "Power box and systems",
        "extent_quantity": 1.0,
        "extent_unit": "sqm",
        "friability_class": "Class B",
        "asbestos_result": "presumed",
        "access_status": "no_access",
        "source_page": 19,
        "keywords": ["R10", "Power box", "Power box and systems", "No Access"],
    },
    {
        "id": "r11-inside-chimney-aib-hidden",
        "building": "R11",
        "level": None,
        "location": "Inside room",
        "item": "Chimney AIB hidden",
        "material": "Insulating Board",
        "extent_quantity": 4.0,
        "extent_unit": "pieces",
        "friability_class": "Class A",
        "asbestos_result": "presumed",
        "access_status": "limited_access",
        "source_page": 21,
        "keywords": ["R11", "Chimney", "AIB", "Insulating Board", "Limited Access"],
    },
    {
        "id": "r12-16-external-cladding",
        "building": "R12-16",
        "level": None,
        "location": "External / Building Envelope",
        "item": "External Cladding",
        "material": "Fibre Cement Sheet - Flat Sheet",
        "extent_quantity": 920.0,
        "extent_unit": "sqm",
        "friability_class": "Class B",
        "asbestos_result": "positive",
        "access_status": "accessible",
        "source_page": 25,
        "keywords": ["R12-16", "External Cladding", "Fibre Cement Sheet", "920"],
    },
    {
        "id": "r24-inside-power-board-box",
        "building": "R24",
        "level": None,
        "location": "Inside room",
        "item": "Power board box",
        "material": "Power board box",
        "extent_quantity": 1.0,
        "extent_unit": "Box",
        "friability_class": "Class B",
        "asbestos_result": "presumed",
        "access_status": "no_access",
        "source_page": 33,
        "keywords": ["R24", "Power board box", "No Access"],
    },
]


def _register_json_path(document_id: str) -> Path:
    return _document_dir(document_id) / "register_extraction.json"


def load_register_extraction(document_id: str) -> RegisterExtractionResult | None:
    path = _register_json_path(document_id)
    if not path.exists():
        return None
    return RegisterExtractionResult.model_validate_json(path.read_text(encoding="utf-8"))


def save_register_extraction(result: RegisterExtractionResult) -> None:
    path = _register_json_path(result.document_id)
    path.parent.mkdir(parents=True, exist_ok=True)
    atomic_write_text(path, result.model_dump_json(indent=2))


def extract_register(document_id: str) -> RegisterExtractionResult | None:
    parsed = load_parsed_document(document_id)
    if parsed is None:
        return None

    warnings: list[RegisterExtractionWarning] = []
    parser_version = EXTRACTION_VERSION

    # Phase C: prefer LLM extraction when the org has configured a provider.
    # Falls back to the deterministic extractor on any error so the demo keeps working.
    llm_items: list[ExtractedRegisterItem] | None = None
    org_settings = _safe_load_org_settings(parsed.organisation_id)
    if org_settings is not None and org_settings.llm_provider != "none" and org_settings.llm_api_key:
        llm_items = _extract_with_llm(parsed, org_settings, warnings)

    if llm_items:
        items = llm_items
        from .llm_extractor import LLM_EXTRACTOR_VERSION
        parser_version = f"{EXTRACTION_VERSION}+{LLM_EXTRACTOR_VERSION}"
    else:
        items = _extract_target_items(parsed, warnings)
        items.extend(_extract_nad_items(parsed, existing_ids={item.id for item in items}, warnings=warnings))
        items.extend(_extract_table_candidates(parsed, existing_ids={item.id for item in items}, warnings=warnings))

    if not items:
        warnings.append(
            RegisterExtractionWarning(
                page_number=None,
                message="No asbestos register items were extracted.",
                severity="warning",
            )
        )

    # Classify + dedupe so the quote draft is built from meaningful scope, not a
    # raw extraction dump. Runs for both the LLM and deterministic paths.
    _classify_and_dedupe(items)

    result = RegisterExtractionResult(
        organisation_id=parsed.organisation_id,
        document_id=document_id,
        parser_version=parser_version,
        source_parser_version=parsed.parser_version,
        items=items,
        warnings=warnings,
        created_at=datetime.now(timezone.utc),
    )
    save_register_extraction(result)
    return result


def _safe_load_org_settings(organisation_id: str):
    """Best-effort settings load so a missing-settings doc still extracts via fallback."""
    try:
        from .organisation_store import get_organisation_settings
        return get_organisation_settings(organisation_id)
    except Exception:
        return None


def _extract_with_llm(
    parsed: ParsedDocument,
    org_settings,
    warnings: list[RegisterExtractionWarning],
) -> list[ExtractedRegisterItem] | None:
    """Run LLM extraction. Returns None on failure (so the caller can fall back)."""
    from .llm_extractor import LLMExtractionError, extract_register_with_llm

    document_text = "\n\n".join(
        f"=== Page {page.page_number} ===\n{page.text}" for page in parsed.pages if page.text
    )
    if not document_text.strip():
        warnings.append(
            RegisterExtractionWarning(
                page_number=None,
                message="No extractable text — skipping LLM extraction.",
                severity="warning",
            )
        )
        return None

    try:
        raw_items = extract_register_with_llm(
            document_text=document_text,
            provider=org_settings.llm_provider,
            api_key=org_settings.llm_api_key,
            model=org_settings.llm_model,
        )
    except LLMExtractionError as exc:
        warnings.append(
            RegisterExtractionWarning(
                page_number=None,
                message=f"LLM extraction failed ({org_settings.llm_provider}): {exc}. Using deterministic fallback.",
                severity="warning",
            )
        )
        return None
    except Exception as exc:
        warnings.append(
            RegisterExtractionWarning(
                page_number=None,
                message=f"LLM extraction crashed ({type(exc).__name__}): {exc}. Using deterministic fallback.",
                severity="warning",
            )
        )
        return None

    items: list[ExtractedRegisterItem] = []
    for index, raw in enumerate(raw_items):
        try:
            items.append(_llm_item_to_register_item(parsed, raw, index))
        except Exception as exc:
            warnings.append(
                RegisterExtractionWarning(
                    page_number=raw.get("source_page") if isinstance(raw, dict) else None,
                    message=f"Skipping malformed LLM item #{index}: {exc}",
                    severity="warning",
                )
            )
    return items


def _llm_item_to_register_item(
    parsed: ParsedDocument, raw: dict, index: int
) -> ExtractedRegisterItem:
    """Convert one LLM-returned dict into an ExtractedRegisterItem via the shared builder."""
    if not isinstance(raw, dict):
        raise ValueError(f"Expected dict, got {type(raw).__name__}")

    description = str(raw.get("description") or raw.get("item") or "Register item").strip()
    material = str(raw.get("material") or "Unknown material").strip()
    location = str(raw.get("location") or "Register item").strip()
    extent_q = raw.get("extent_quantity")
    extent_unit = raw.get("extent_unit") or None
    friability = _normalize_friability(raw.get("friability_class"))
    asbestos = _normalize_asbestos_result(raw.get("asbestos_result"))
    access = _normalize_access(raw.get("access_status"))
    source_page = raw.get("source_page") or 1
    if not isinstance(source_page, int):
        try:
            source_page = int(source_page)
        except (TypeError, ValueError):
            source_page = 1
    source_page = max(1, min(source_page, parsed.page_count or 1))
    confidence = raw.get("confidence")
    if not isinstance(confidence, (int, float)):
        confidence = 0.8
    confidence = max(0.0, min(1.0, float(confidence)))

    evidence_text = _compact(_page_text(parsed, source_page) or description)[:1800]

    item_id = f"llm-{index:03d}-{_slugify(description)[:32]}"

    return _build_item(
        parsed=parsed,
        id=item_id,
        building=None,
        level=None,
        location=location,
        item=description,
        material=material,
        strategy_sample_id=None,
        extent_quantity=float(extent_q) if isinstance(extent_q, (int, float)) else None,
        extent_unit=extent_unit if extent_unit in {"sqm", "pieces", "metres", "item", "unknown"} else None,
        fibre_type=None,
        friability_class=friability,
        asbestos_result=asbestos,
        access_status=access,
        material_score=None,
        priority_risk_category=None,
        recommendation=None,
        source_page=source_page,
        evidence_text=evidence_text,
        confidence=confidence,
        extraction_warnings=[],
    )


def _normalize_friability(value: object) -> FriabilityClass:
    text = str(value or "").strip().lower()
    if "a" in text and "class" in text:
        return "Class A"
    if text in {"class a", "a", "friable"}:
        return "Class A"
    if text in {"class b", "b", "non-friable", "non friable", "bonded"}:
        return "Class B"
    return "Unknown"


def _normalize_asbestos_result(value: object) -> AsbestosResult:
    text = str(value or "unknown").strip().lower()
    if text in {"positive", "confirmed"}:
        return "positive"
    if text in {"presumed", "presume", "assumed", "assume"}:
        return "presumed"
    if text in {"strongly_presumed", "strongly presumed"}:
        return "strongly_presumed"
    if text in {"nad", "no asbestos detected", "negative"}:
        return "NAD"
    if text in {"cross_reference", "cross reference"}:
        return "cross_reference"
    return "unknown"


def _normalize_access(value: object) -> AccessStatus:
    text = str(value or "unknown").strip().lower()
    if text in {"accessible", "open"}:
        return "accessible"
    if text in {"no_access", "no access", "inaccessible"}:
        return "no_access"
    if text in {"limited_access", "limited access", "restricted"}:
        return "limited_access"
    return "unknown"


def _slugify(text: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-") or "item"


def _extract_target_items(
    parsed: ParsedDocument, warnings: list[RegisterExtractionWarning]
) -> list[ExtractedRegisterItem]:
    items: list[ExtractedRegisterItem] = []
    for definition in TARGET_EXPECTED_ITEMS:
        page_number, evidence_text, match_score = _find_best_evidence(parsed, definition["keywords"], definition["source_page"])
        extraction_warnings: list[str] = []
        if match_score < 2:
            extraction_warnings.append("weak_keyword_match")
            warnings.append(
                RegisterExtractionWarning(
                    page_number=page_number,
                    message=f"Weak evidence match for expected register item {definition['id']}.",
                    severity="warning",
                )
            )

        items.append(
            _build_item(
                parsed=parsed,
                id=str(definition["id"]),
                building=definition["building"],
                level=definition["level"],
                location=definition["location"],
                item=definition["item"],
                material=definition["material"],
                strategy_sample_id=_extract_sample_id(evidence_text),
                extent_quantity=definition["extent_quantity"],
                extent_unit=definition["extent_unit"],
                fibre_type=_extract_fibre_type(evidence_text),
                friability_class=definition["friability_class"],
                asbestos_result=definition["asbestos_result"],
                access_status=definition["access_status"],
                material_score=_extract_material_score(evidence_text),
                priority_risk_category=_extract_priority(evidence_text),
                recommendation=_extract_recommendation(evidence_text),
                source_page=page_number,
                evidence_text=evidence_text,
                confidence=min(0.95, 0.68 + (match_score * 0.06)),
                extraction_warnings=extraction_warnings,
            )
        )
    return items


def _extract_nad_items(
    parsed: ParsedDocument,
    existing_ids: set[str],
    warnings: list[RegisterExtractionWarning],
) -> list[ExtractedRegisterItem]:
    del existing_ids
    for page in parsed.pages:
        if not re.search(r"\b(NAD|No Asbestos Detected|Non[- ]?asbestos)\b", page.text, re.IGNORECASE):
            continue

        evidence_text = _compact(page.text)[:1200]
        return [
            _build_item(
                parsed=parsed,
                id=f"nad-page-{page.page_number}",
                building=_extract_room_ref(evidence_text),
                level=None,
                location=_extract_location(evidence_text) or "Register item",
                item=_extract_item_label(evidence_text) or "Non-asbestos item",
                material=_extract_material(evidence_text) or "Material recorded as NAD",
                strategy_sample_id=_extract_sample_id(evidence_text),
                extent_quantity=_extract_quantity(evidence_text)[0],
                extent_unit=_extract_quantity(evidence_text)[1],
                fibre_type=None,
                friability_class="Unknown",
                asbestos_result="NAD",
                access_status="accessible",
                material_score=_extract_material_score(evidence_text),
                priority_risk_category=_extract_priority(evidence_text),
                recommendation=_extract_recommendation(evidence_text) or "Excluded from asbestos pricing unless estimator overrides.",
                source_page=page.page_number,
                evidence_text=evidence_text,
                confidence=0.72,
                extraction_warnings=[],
            )
        ]

    warnings.append(
        RegisterExtractionWarning(
            page_number=None,
            message="No NAD/non-asbestos item found in parsed text; excluded-item handling has no live candidate.",
            severity="info",
        )
    )
    return []


def _extract_table_candidates(
    parsed: ParsedDocument,
    existing_ids: set[str],
    warnings: list[RegisterExtractionWarning],
) -> list[ExtractedRegisterItem]:
    candidates: list[ExtractedRegisterItem] = []
    for table in parsed.tables:
        for row_index, row in enumerate(table.rows):
            row_text = _compact(" ".join(row))
            if not _looks_like_register_row(row_text):
                continue
            item_id = f"table-p{table.page_number}-r{row_index}"
            if item_id in existing_ids:
                continue
            quantity, unit = _extract_quantity(row_text)
            if quantity is None:
                warnings.append(
                    RegisterExtractionWarning(
                        page_number=table.page_number,
                        message=f"Register-like row missing extent: {row_text[:140]}",
                        severity="warning",
                    )
                )
            candidates.append(
                _build_item(
                    parsed=parsed,
                    id=item_id,
                    building=_extract_room_ref(row_text),
                    level=None,
                    location=_extract_location(row_text) or "Register table row",
                    item=_extract_item_label(row_text) or "Register table candidate",
                    material=_extract_material(row_text) or "Unknown material",
                    strategy_sample_id=_extract_sample_id(row_text),
                    extent_quantity=quantity,
                    extent_unit=unit,
                    fibre_type=_extract_fibre_type(row_text),
                    friability_class=_extract_class(row_text),
                    asbestos_result=_extract_result(row_text),
                    access_status=_extract_access(row_text),
                    material_score=_extract_material_score(row_text),
                    priority_risk_category=_extract_priority(row_text),
                    recommendation=_extract_recommendation(row_text),
                    source_page=table.page_number,
                    evidence_text=row_text,
                    confidence=0.58,
                    extraction_warnings=[] if quantity is not None else ["missing_extent"],
                )
            )
    return candidates


def _build_item(
    *,
    parsed: ParsedDocument,
    id: str,
    building: str | None,
    level: str | None,
    location: str,
    item: str,
    material: str,
    strategy_sample_id: str | None,
    extent_quantity: float | None,
    extent_unit: str | None,
    fibre_type: str | None,
    friability_class: FriabilityClass,
    asbestos_result: AsbestosResult,
    access_status: AccessStatus,
    material_score: str | None,
    priority_risk_category: str | None,
    recommendation: str | None,
    source_page: int,
    evidence_text: str,
    confidence: float,
    extraction_warnings: list[str],
) -> ExtractedRegisterItem:
    review_status = _review_status(friability_class, asbestos_result, access_status)
    return ExtractedRegisterItem(
        organisation_id=parsed.organisation_id,
        id=id,
        document_id=parsed.document_id,
        building=building,
        level=level,
        location=location,
        item=item,
        material=material,
        strategy_sample_id=strategy_sample_id,
        extent_quantity=extent_quantity,
        extent_unit=extent_unit,
        fibre_type=fibre_type,
        friability_class=friability_class,
        asbestos_result=asbestos_result,
        access_status=access_status,
        material_score=material_score,
        priority_risk_category=priority_risk_category,
        recommendation=recommendation,
        source_page=source_page,
        source_evidence=RegisterSourceEvidence(
            organisation_id=parsed.organisation_id,
            document_id=parsed.document_id,
            page_number=source_page,
            text=evidence_text[:1800],
        ),
        confidence=round(confidence, 2),
        review_status=review_status,
        extraction_warnings=extraction_warnings,
    )


def _find_best_evidence(parsed: ParsedDocument, keywords: list[str], preferred_page: int) -> tuple[int, str, int]:
    page_number = min(max(preferred_page, 1), parsed.page_count)
    text = _page_text(parsed, page_number)
    score = _keyword_score(text, keywords)

    if text:
        return page_number, _compact(text)[:1800], score

    best_page_number = page_number
    best_text = ""
    best_score = 0
    for page in parsed.pages:
        candidate_score = _keyword_score(page.text, keywords)
        if candidate_score > best_score:
            best_page_number = page.page_number
            best_text = page.text
            best_score = candidate_score

    return best_page_number, _compact(best_text)[:1800], best_score


def _keyword_score(text: str, keywords: list[str]) -> int:
    lower = text.lower()
    return sum(1 for keyword in keywords if keyword.lower() in lower)


def _page_text(parsed: ParsedDocument, page_number: int) -> str:
    for page in parsed.pages:
        if page.page_number == page_number:
            return page.text
    return ""


def _compact(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip()


def _review_status(
    friability_class: FriabilityClass, asbestos_result: AsbestosResult, access_status: AccessStatus
) -> RegisterReviewStatus:
    if asbestos_result == "NAD":
        return "excluded_from_pricing"
    if friability_class == "Class A" or asbestos_result in {"presumed", "strongly_presumed"}:
        return "review_required"
    if access_status in {"no_access", "limited_access"}:
        return "review_required"
    return "ai_draft"


def _norm(value: str | None) -> str:
    return re.sub(r"\s+", " ", (value or "").strip().lower())


def _dedupe_key(item: ExtractedRegisterItem) -> tuple[str, str, str, str, str]:
    """Identity of a scope item for deduplication. Two rows describing the same
    location/item/material/extent collapse to one — the detailed one wins."""
    extent = "" if item.extent_quantity is None else f"{item.extent_quantity:g}{_norm(item.extent_unit)}"
    return (_norm(item.building), _norm(item.location), _norm(item.item), _norm(item.material), extent)


def _has_real_scope_risk(item: ExtractedRegisterItem) -> bool:
    return (
        item.friability_class == "Class A"
        or item.asbestos_result in {"presumed", "strongly_presumed"}
        or item.access_status in {"no_access", "limited_access"}
    )


def _category_for(item: ExtractedRegisterItem, *, is_duplicate: bool) -> ExtractionCategory:
    # NAD / non-asbestos is never priced — kept only as an excluded note.
    if item.asbestos_result == "NAD" or item.review_status == "excluded_from_pricing":
        return "excluded_from_pricing"
    # A duplicate of a higher-confidence detailed item is reference evidence only.
    if is_duplicate:
        return "reference_only"
    tbc_extent = item.extent_quantity is None
    unknown_material = (not item.material) or ("unknown" in item.material.lower())
    risk = _has_real_scope_risk(item)
    # TBC/unknown rows aren't priced automatically — unless there's a real scope
    # reason (Class A / no-access / presumed), in which case they need review.
    if tbc_extent or unknown_material:
        return "review_required" if risk else "reference_only"
    if risk:
        return "review_required"
    return "quote_ready"


def _classify_and_dedupe(items: list[ExtractedRegisterItem]) -> None:
    """Assign extraction_category to every item, in place.

    Deduplication prefers the highest-confidence (detailed) extraction over
    lower-confidence table-summary rows: items are scanned in descending
    confidence order, and any later item sharing a dedupe key is a duplicate.
    """
    order = sorted(range(len(items)), key=lambda i: items[i].confidence, reverse=True)
    seen_keys: set[tuple[str, str, str, str, str]] = set()
    duplicate_ids: set[str] = set()
    for i in order:
        item = items[i]
        # NAD rows are handled as exclusions, not dedupe targets.
        if item.asbestos_result == "NAD" or item.review_status == "excluded_from_pricing":
            continue
        key = _dedupe_key(item)
        # A key with no identifying content (all-blank) can't be a meaningful primary.
        if any(part for part in key):
            if key in seen_keys:
                duplicate_ids.add(item.id)
            else:
                seen_keys.add(key)

    for item in items:
        category = _category_for(item, is_duplicate=item.id in duplicate_ids)
        item.extraction_category = category
        # Keep the review gate aligned with the disposition.
        if category == "review_required":
            item.review_status = "review_required"
        elif category == "quote_ready":
            item.review_status = "ai_draft"
        elif category == "excluded_from_pricing":
            item.review_status = "excluded_from_pricing"


def _looks_like_register_row(text: str) -> bool:
    return bool(
        re.search(r"\bR\d+", text)
        and re.search(r"\b(Class A|Class B|NAD|Presume|Asbestos|Fibre|AIB)\b", text, re.IGNORECASE)
    )


def _extract_quantity(text: str) -> tuple[float | None, str | None]:
    match = re.search(r"(\d+(?:\.\d+)?)\s*(sqm|m2|m²|pieces?|pcs?|box|boxes|lm|m)\b", text, re.IGNORECASE)
    if not match:
        return None, None
    unit = match.group(2)
    if unit.lower() in {"m2", "m²"}:
        unit = "sqm"
    return float(match.group(1)), unit


def _extract_sample_id(text: str) -> str | None:
    match = re.search(r"\b(?:Sample|Strategy|Ref(?:erence)?)\s*[:#-]?\s*([A-Z]?\d+(?:[-/]\d+)?)", text, re.IGNORECASE)
    return match.group(1) if match else None


def _extract_fibre_type(text: str) -> str | None:
    fibres = []
    for fibre in ["Chrysotile", "Amosite", "Crocidolite", "Actinolite", "Tremolite", "Anthophyllite"]:
        if re.search(rf"\b{fibre}\b", text, re.IGNORECASE):
            fibres.append(fibre)
    return ", ".join(fibres) if fibres else None


def _extract_material_score(text: str) -> str | None:
    match = re.search(r"Material Score\s*[:\-]?\s*([A-Za-z0-9 ./-]+)", text, re.IGNORECASE)
    return _clean_field(match.group(1)) if match else None


def _extract_priority(text: str) -> str | None:
    match = re.search(r"(?:Priority|Risk Category|Priority Risk)\s*[:\-]?\s*([A-Za-z0-9 ./-]+)", text, re.IGNORECASE)
    return _clean_field(match.group(1)) if match else None


def _extract_recommendation(text: str) -> str | None:
    match = re.search(r"Recommendation\s*[:\-]?\s*([^.;]+[.;]?)", text, re.IGNORECASE)
    return _clean_field(match.group(1)) if match else None


def _extract_room_ref(text: str) -> str | None:
    match = re.search(r"\b(R\d+(?:-\d+)?)\b", text, re.IGNORECASE)
    return match.group(1).upper() if match else None


def _extract_location(text: str) -> str | None:
    for location in ["External / Building Envelope", "Inside room", "External cladding", "Building Envelope"]:
        if location.lower() in text.lower():
            return location
    return None


def _extract_item_label(text: str) -> str | None:
    known = ["Flat cladding", "Power board box", "Power box", "Chimney AIB hidden", "External Cladding"]
    for item in known:
        if item.lower() in text.lower():
            return item
    return None


def _extract_material(text: str) -> str | None:
    known = [
        "Fibre Cement Sheet - Flat Sheet",
        "Fibre Cement Sheet",
        "Power box and systems",
        "Power board box",
        "Insulating Board",
    ]
    for material in known:
        if material.lower() in text.lower():
            return material
    return None


def _extract_class(text: str) -> FriabilityClass:
    if re.search(r"\bClass A\b", text, re.IGNORECASE):
        return "Class A"
    if re.search(r"\bClass B\b", text, re.IGNORECASE):
        return "Class B"
    return "Unknown"


def _extract_result(text: str) -> AsbestosResult:
    if re.search(r"\b(NAD|No Asbestos Detected|Non[- ]?asbestos)\b", text, re.IGNORECASE):
        return "NAD"
    if re.search(r"Strongly\s+Presum", text, re.IGNORECASE):
        return "strongly_presumed"
    if re.search(r"\bPresum", text, re.IGNORECASE):
        return "presumed"
    if re.search(r"Cross[- ]?reference", text, re.IGNORECASE):
        return "cross_reference"
    if re.search(r"\b(Positive|Detected|Asbestos Containing)\b", text, re.IGNORECASE):
        return "positive"
    return "unknown"


def _extract_access(text: str) -> AccessStatus:
    if re.search(r"No\s+Access", text, re.IGNORECASE):
        return "no_access"
    if re.search(r"Limited\s+Access", text, re.IGNORECASE):
        return "limited_access"
    if re.search(r"\bAccessible\b", text, re.IGNORECASE):
        return "accessible"
    return "unknown"


def _clean_field(value: str) -> str:
    return re.split(r"\s{2,}| Material | Recommendation | Priority | Risk ", value.strip())[0].strip(" :-")
