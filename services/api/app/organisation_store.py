from __future__ import annotations

import re
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

from .document_parser import DEFAULT_ORGANISATION_ID, STORAGE_ROOT, _validate_storage_id
from .storage_paths import atomic_write_text
from .repository import get_repository
from .pricebook import PRICEBOOK_VERSION, get_seed_pricebook
from .quote_boilerplate import (
    DEFAULT_QUOTE_ACCEPTANCE_TEXT,
    DEFAULT_QUOTE_CLOSING_TEXT,
    DEFAULT_QUOTE_DISCLAIMER_TEXT,
    DEFAULT_QUOTE_IMPORTANT_NOTES,
    DEFAULT_QUOTE_INCLUSIONS,
    DEFAULT_QUOTE_INTRO_TEXT,
    DEFAULT_QUOTE_REQUIRED_SERVICES,
    DEFAULT_QUOTE_VARIATION_TEXT,
)
from .schemas import (
    CompanyProfile,
    CreateOrganisationRequest,
    CreateOrganisationUserRequest,
    CreatePricebookRequest,
    CreatePricebookRuleRequest,
    LLMConfig,
    Organisation,
    OrganisationSettings,
    OrganisationUser,
    Pricebook,
    PricebookRule,
    UpdatePricebookRuleRequest,
    UpsertLLMConfigRequest,
    UpsertOrganisationSettingsRequest,
    User,
)


INDEX_PATH = STORAGE_ROOT / "organisations.json"


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _slug(value: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")
    return slug or f"org-{uuid4().hex[:8]}"


def _org_dir(org_id: str) -> Path:
    _validate_storage_id(org_id, "organisation_id")
    return STORAGE_ROOT / org_id


def _json_path(org_id: str, name: str) -> Path:
    return _org_dir(org_id) / f"{name}.json"


def _read_index() -> list[str]:
    if not INDEX_PATH.exists():
        return []
    import json

    return list(json.loads(INDEX_PATH.read_text(encoding="utf-8")))


def _write_index(org_ids: list[str]) -> None:
    import json

    atomic_write_text(INDEX_PATH, json.dumps(sorted(set(org_ids)), indent=2))


def ensure_default_organisation() -> Organisation:
    existing = get_organisation(DEFAULT_ORGANISATION_ID)
    if existing is not None:
        return existing
    # Trading name is used as the default business_name on the export — keep it aligned
    # with demo materials so the static demo dashboard and the freshly created org show
    # the same branding.
    return create_organisation(
        CreateOrganisationRequest(
            name="TraceQuote Demo Organisation",
            slug="tracequote-demo",
            trading_name="Demo Asbestos Services Ltd",
            email="demo@tracequote.local",
        ),
        org_id=DEFAULT_ORGANISATION_ID,
    )


def create_organisation(request: CreateOrganisationRequest, org_id: str | None = None) -> Organisation:
    created_at = _now()
    organisation_id = org_id or f"org-{uuid4().hex[:12]}"
    slug = request.slug or _slug(request.name)
    org_dir = _org_dir(organisation_id)
    org_dir.mkdir(parents=True, exist_ok=True)

    settings = OrganisationSettings(
        organisation_id=organisation_id,
        business_name=request.trading_name or request.name,
        business_email=request.email,
        quote_intro_text=DEFAULT_QUOTE_INTRO_TEXT,
        quote_disclaimer_text=DEFAULT_QUOTE_DISCLAIMER_TEXT,
        quote_acceptance_text=DEFAULT_QUOTE_ACCEPTANCE_TEXT,
        quote_variation_text=DEFAULT_QUOTE_VARIATION_TEXT,
        quote_closing_text=DEFAULT_QUOTE_CLOSING_TEXT,
        quote_inclusions=list(DEFAULT_QUOTE_INCLUSIONS),
        quote_important_notes=list(DEFAULT_QUOTE_IMPORTANT_NOTES),
        quote_required_services=list(DEFAULT_QUOTE_REQUIRED_SERVICES),
        updated_at=created_at,
    )
    profile = CompanyProfile(
        organisation_id=organisation_id,
        legal_name=request.name,
        trading_name=request.trading_name or request.name,
        email=request.email,
        updated_at=created_at,
    )
    organisation = Organisation(
        id=organisation_id,
        name=request.name,
        slug=slug,
        company_profile=profile,
        settings=settings,
        created_at=created_at,
        updated_at=created_at,
    )
    repo = get_repository()
    repo.put_organisation(organisation)
    repo.put_settings(organisation_id, settings)
    repo.put_company_profile(organisation_id, profile)
    repo.put_org_users(organisation_id, [])
    repo.put_pricebooks(organisation_id, [])

    # Auto-seed a starter pricebook with all 10 RAS-1285 rules so admins land on
    # an editable pricebook (not a "no pricebook exists yet" empty state).
    create_pricebook(
        organisation_id,
        CreatePricebookRequest(
            name=f"{request.trading_name or request.name} starter pricebook",
            version=PRICEBOOK_VERSION,
            rules=None,  # None → clone from seed pricebook
        ),
    )

    return organisation


def list_organisations() -> list[Organisation]:
    ensure_default_organisation()
    organisations: list[Organisation] = []
    for org_id in get_repository().list_organisation_ids():
        organisation = get_organisation(org_id)
        if organisation is not None:
            organisations.append(organisation)
    return organisations


def get_organisation(org_id: str) -> Organisation | None:
    return get_repository().get_organisation(org_id)


def add_organisation_user(org_id: str, request: CreateOrganisationUserRequest) -> OrganisationUser | None:
    if get_organisation(org_id) is None:
        return None
    users = list_organisation_users(org_id)
    now = _now()
    user = User(id=f"user-{uuid4().hex[:12]}", email=request.email, name=request.name, created_at=now)
    org_user = OrganisationUser(
        id=f"orguser-{uuid4().hex[:12]}",
        organisation_id=org_id,
        user_id=user.id,
        email=user.email,
        name=user.name,
        role=request.role,
        created_at=now,
    )
    users.append(org_user)
    get_repository().put_org_users(org_id, users)
    return org_user


def list_organisation_users(org_id: str) -> list[OrganisationUser]:
    return get_repository().list_org_users(org_id)


def get_organisation_settings(org_id: str) -> OrganisationSettings | None:
    return get_repository().get_settings(org_id)


def _mask_api_key(api_key: str | None) -> str | None:
    """Return a safe preview of an API key for display in UI. None when not set."""
    if not api_key:
        return None
    if len(api_key) <= 6:
        return "***"
    return f"{api_key[:3]}***{api_key[-4:]}"


def get_llm_config(org_id: str) -> LLMConfig | None:
    """Read the org's current LLM provider settings without exposing the API key."""
    from .llm_extractor import DEFAULT_MODELS

    settings = get_organisation_settings(org_id)
    if settings is None:
        return None
    return LLMConfig(
        organisation_id=org_id,
        llm_provider=settings.llm_provider,
        llm_model=settings.llm_model,
        has_api_key=bool(settings.llm_api_key),
        api_key_preview=_mask_api_key(settings.llm_api_key),
        default_models=dict(DEFAULT_MODELS),
        updated_at=settings.updated_at,
    )


def update_llm_config(org_id: str, request: UpsertLLMConfigRequest) -> LLMConfig | None:
    """Update only the LLM-related fields on org settings. Leaves everything else untouched."""
    if get_organisation(org_id) is None:
        return None
    settings = get_organisation_settings(org_id)
    if settings is None:
        return None
    data = settings.model_dump()
    data["llm_provider"] = request.llm_provider
    # API key: if request specifies a value, use it; if empty string, clear; if None, keep current.
    if request.llm_api_key is not None:
        data["llm_api_key"] = request.llm_api_key or None
    if request.llm_model is not None:
        data["llm_model"] = request.llm_model or None
    data["updated_at"] = _now()
    updated = OrganisationSettings.model_validate(data)
    repo = get_repository()
    repo.put_settings(org_id, updated)
    organisation = get_organisation(org_id)
    if organisation is not None:
        organisation.settings = updated
        organisation.updated_at = updated.updated_at
        repo.put_organisation(organisation)
    return get_llm_config(org_id)


def upsert_organisation_settings(org_id: str, request: UpsertOrganisationSettingsRequest) -> OrganisationSettings | None:
    if get_organisation(org_id) is None:
        return None
    existing = get_organisation_settings(org_id)
    base_data = existing.model_dump() if existing is not None else {"organisation_id": org_id}
    # Only override fields the caller actually set (non-None values from the request)
    updates = {key: value for key, value in request.model_dump().items() if value is not None}
    base_data.update(updates)
    base_data["organisation_id"] = org_id
    base_data["updated_at"] = _now()
    settings = OrganisationSettings.model_validate(base_data)
    repo = get_repository()
    repo.put_settings(org_id, settings)
    organisation = get_organisation(org_id)
    if organisation is not None:
        organisation.settings = settings
        organisation.updated_at = settings.updated_at
        repo.put_organisation(organisation)
    return settings


def create_pricebook(org_id: str, request: CreatePricebookRequest) -> Pricebook | None:
    if get_organisation(org_id) is None:
        return None
    now = _now()
    raw_rules = request.rules if request.rules is not None else [
        PricebookRule(
            id=rule.id,
            organisation_id=org_id,
            name=rule.name,
            category=rule.section,
            section=rule.section,
            material_match=", ".join(rule.material_keywords) if rule.material_keywords else None,
            class_match=rule.class_match,
            access_match=_access_match_from_seed(rule.access_status_match),
            pricing_method=_pricing_method_from_seed(rule.pricing_method, rule.unit),
            unit=rule.unit,
            unit_rate=rule.unit_rate,
            risk_multiplier=rule.risk_multiplier,
            margin=rule.margin,
            gst_taxable=True,
            minimum_charge=rule.minimum_charge,
            assumptions=rule.default_assumptions,
            exclusions=rule.default_exclusions,
            review_required=True,
            mandatory=rule.id
            in {
                "pb-site-establishment",
                "pb-class-b-fibre-cement-sqm",
                "pb-class-a-insulating-board-provisional",
                "pb-no-access-power-investigation",
                "pb-waste-disposal-placeholder",
                "pb-excluded-nad",
            },
        )
        for rule in get_seed_pricebook()
    ]
    rules = [rule.model_copy(update={"organisation_id": org_id}) for rule in raw_rules]
    pricebook = Pricebook(
        id=f"pricebook-{uuid4().hex[:12]}",
        organisation_id=org_id,
        name=request.name,
        version=request.version,
        rules=rules,
        created_at=now,
        updated_at=now,
    )
    pricebooks = list_pricebooks(org_id)
    # Newest pricebook becomes the active one; older ones are archived for history.
    # Estimators can still re-activate an older book via the activate endpoint.
    if pricebook.active:
        for existing in pricebooks:
            existing.active = False
            existing.updated_at = now
    pricebooks.append(pricebook)
    _write_pricebooks(org_id, pricebooks)
    return pricebook


def list_pricebooks(org_id: str) -> list[Pricebook]:
    return get_repository().list_pricebooks(org_id)


def get_pricebook(org_id: str, pricebook_id: str) -> Pricebook | None:
    for pricebook in list_pricebooks(org_id):
        if pricebook.id == pricebook_id:
            return pricebook
    return None


def get_active_pricebook(org_id: str) -> Pricebook | None:
    active = [pricebook for pricebook in list_pricebooks(org_id) if pricebook.active]
    if active:
        return active[0]
    pricebooks = list_pricebooks(org_id)
    return pricebooks[0] if pricebooks else None


def add_pricebook_rule(org_id: str, pricebook_id: str, request: CreatePricebookRuleRequest) -> Pricebook | None:
    pricebooks = list_pricebooks(org_id)
    for index, pricebook in enumerate(pricebooks):
        if pricebook.id != pricebook_id:
            continue
        rule = PricebookRule(
            id=f"pbr-{uuid4().hex[:12]}",
            organisation_id=org_id,
            **request.model_dump(),
        )
        pricebook.rules.append(rule)
        pricebook.updated_at = _now()
        pricebooks[index] = pricebook
        _write_pricebooks(org_id, pricebooks)
        return pricebook
    return None


def update_pricebook_rule(
    org_id: str,
    pricebook_id: str,
    rule_id: str,
    request: UpdatePricebookRuleRequest,
) -> Pricebook | None:
    pricebooks = list_pricebooks(org_id)
    for pricebook_index, pricebook in enumerate(pricebooks):
        if pricebook.id != pricebook_id:
            continue
        for rule_index, rule in enumerate(pricebook.rules):
            if rule.id != rule_id:
                continue
            updates = {key: value for key, value in request.model_dump(exclude_unset=True).items()}
            pricebook.rules[rule_index] = rule.model_copy(update=updates)
            pricebook.updated_at = _now()
            pricebooks[pricebook_index] = pricebook
            _write_pricebooks(org_id, pricebooks)
            return pricebook
        return None
    return None


def delete_pricebook_rule(org_id: str, pricebook_id: str, rule_id: str) -> Pricebook | None:
    return update_pricebook_rule(
        org_id,
        pricebook_id,
        rule_id,
        UpdatePricebookRuleRequest(active=False),
    )


def activate_pricebook(org_id: str, pricebook_id: str) -> Pricebook | None:
    pricebooks = list_pricebooks(org_id)
    selected: Pricebook | None = None
    now = _now()
    for index, pricebook in enumerate(pricebooks):
        pricebook.active = pricebook.id == pricebook_id
        pricebook.updated_at = now
        pricebooks[index] = pricebook
        if pricebook.id == pricebook_id:
            selected = pricebook
    if selected is None:
        return None
    _write_pricebooks(org_id, pricebooks)
    return selected


def _write_pricebooks(org_id: str, pricebooks: list[Pricebook]) -> None:
    get_repository().put_pricebooks(org_id, pricebooks)


def _pricing_method_from_seed(method: str, unit: str) -> str:
    if method == "excluded":
        return "excluded"
    if method == "fixed":
        return "fixed"
    normalized_unit = unit.lower()
    if normalized_unit == "sqm":
        return "per_sqm"
    if normalized_unit in {"piece", "pieces", "box", "item"}:
        return "per_piece"
    if normalized_unit in {"hour", "hr"}:
        return "per_hour"
    return "fixed"


def _access_match_from_seed(access_status: str | None) -> str:
    if access_status == "no_access":
        return "no-access"
    if access_status == "limited_access":
        return "limited-access"
    if access_status == "unknown":
        return "unknown"
    return "normal"
