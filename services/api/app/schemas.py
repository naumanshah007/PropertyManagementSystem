from __future__ import annotations

from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, Field

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


ReviewStatus = Literal[
    "ai_draft",
    "review_required",
    "accepted",
    "edited",
    "approved",
    "blocked",
]

WorkupStatus = Literal[
    "intake",
    "extracting",
    "needs_review",
    "pricing_draft",
    "approval_required",
    "approved",
    "exported",
    "blocked",
]


class SourceEvidence(BaseModel):
    id: str
    document_id: str
    page_number: int
    evidence_type: str
    raw_text: str
    confidence: float = Field(ge=0, le=1)
    bounding_box: dict[str, float] | None = None


class SourceDocument(BaseModel):
    id: str
    workup_id: str
    file_name: str
    file_type: str
    page_count: int
    parser_version: str
    ocr_status: str
    created_at: datetime


class RiskFlag(BaseModel):
    id: str
    label: str
    severity: Literal["info", "attention", "high", "blocked"]
    description: str
    review_status: ReviewStatus
    source_evidence_ids: list[str]


class AsbestosRegisterItem(BaseModel):
    id: str
    workup_id: str
    location: str
    area: str
    material: str
    product_type: str
    extent_quantity: float | None
    extent_unit: str
    asbestos_result: str
    fibre_type: str | None
    friability_class: str
    condition: str | None
    recommendation: str
    access_status: str
    source_evidence_ids: list[str]
    confidence: float = Field(ge=0, le=1)
    review_status: ReviewStatus


class PricingRule(BaseModel):
    id: str
    name: str
    job_type: str
    formula: str
    risk_factors: list[str]
    default_assumptions: list[str]
    default_exclusions: list[str]
    version: str


class QuoteLine(BaseModel):
    id: str
    workup_id: str
    section: str
    description: str
    quantity: float | None
    unit: str
    unit_rate: float | None
    base_cost: float | None
    risk_multiplier: float
    margin: float
    gst: float | None
    total: float | None
    source_evidence_ids: list[str]
    pricing_rule_ids: list[str]
    assumptions: list[str]
    exclusions: list[str]
    review_status: ReviewStatus
    approval_status: Literal["not_ready", "ready_for_approval", "approved"]
    why: str


class EstimatorEdit(BaseModel):
    id: str
    workup_id: str
    entity_type: str
    entity_id: str
    field_name: str
    previous_value: Any
    new_value: Any
    reason: str
    user_id: str
    created_at: datetime


class AuditEvent(BaseModel):
    id: str
    workup_id: str
    actor_type: Literal["system", "user"]
    actor_id: str
    event_type: str
    payload: dict[str, Any]
    created_at: datetime


class QuoteWorkup(BaseModel):
    id: str
    client_name: str
    site_address: str
    job_type: str
    survey_type: str
    status: WorkupStatus
    assigned_estimator_id: str
    due_date: str
    created_at: datetime
    updated_at: datetime
    documents: list[SourceDocument]
    source_evidence: list[SourceEvidence]
    register_items: list[AsbestosRegisterItem]
    risk_flags: list[RiskFlag]
    quote_lines: list[QuoteLine]
    pricing_rules: list[PricingRule]
    estimator_edits: list[EstimatorEdit]
    audit_events: list[AuditEvent]
    assumptions: list[str]
    exclusions: list[str]
    export_status: Literal["blocked", "ready", "exported"]


class HealthResponse(BaseModel):
    status: str
    service: str
    version: str


OcrStatus = Literal["not_required", "required_later", "failed"]


class ParsedPage(BaseModel):
    page_number: int
    text: str
    warnings: list[str]


class ParsedTable(BaseModel):
    page_number: int
    rows: list[list[str]]
    extraction_method: str


SurveyType = Literal[
    "management_plan",
    "management_survey",
    "refurbishment_survey",
    "demolition_survey",
    "unknown",
]


class SurveyClassification(BaseModel):
    survey_type: SurveyType
    quotable: bool
    confidence: float = Field(ge=0, le=1)
    matched_keywords: list[str] = Field(default_factory=list)
    reason: str
    classifier_version: str


class ParsedDocument(BaseModel):
    organisation_id: str = "org-demo-tracequote"
    document_id: str
    file_name: str
    page_count: int
    parser_version: str
    pages: list[ParsedPage]
    tables: list[ParsedTable]
    ocr_status: OcrStatus
    stored_path: str
    parsed_json_path: str
    survey_classification: SurveyClassification | None = None
    created_at: datetime


AsbestosResult = Literal[
    "positive",
    "presumed",
    "strongly_presumed",
    "cross_reference",
    "NAD",
    "unknown",
]

AccessStatus = Literal["accessible", "no_access", "limited_access", "unknown"]
FriabilityClass = Literal["Class A", "Class B", "Unknown"]
RegisterReviewStatus = Literal["ai_draft", "review_required", "excluded_from_pricing"]

# Higher-level disposition that drives pricing + UI grouping. A clean detailed
# item is quote_ready; risk/ambiguous scope is review_required; duplicate or
# TBC/unknown noise is reference_only; NAD/non-asbestos is excluded_from_pricing.
# Only quote_ready and review_required items generate priced quote candidates.
ExtractionCategory = Literal["quote_ready", "review_required", "reference_only", "excluded_from_pricing"]


class RegisterSourceEvidence(BaseModel):
    organisation_id: str = "org-demo-tracequote"
    document_id: str
    page_number: int
    text: str


class ExtractedRegisterItem(BaseModel):
    organisation_id: str = "org-demo-tracequote"
    id: str
    document_id: str
    building: str | None
    level: str | None
    location: str
    item: str
    material: str
    strategy_sample_id: str | None
    extent_quantity: float | None
    extent_unit: str | None
    fibre_type: str | None
    friability_class: FriabilityClass
    asbestos_result: AsbestosResult
    access_status: AccessStatus
    material_score: str | None
    priority_risk_category: str | None
    recommendation: str | None
    source_page: int
    source_evidence: RegisterSourceEvidence
    confidence: float = Field(ge=0, le=1)
    review_status: RegisterReviewStatus
    # Defaults to review_required so any legacy stored extraction (pre-classification)
    # is treated conservatively rather than silently priced.
    extraction_category: ExtractionCategory = "review_required"
    extraction_warnings: list[str]


class RegisterExtractionWarning(BaseModel):
    page_number: int | None
    message: str
    severity: Literal["info", "warning", "error"]


class RegisterExtractionResult(BaseModel):
    organisation_id: str = "org-demo-tracequote"
    document_id: str
    parser_version: str
    source_parser_version: str
    items: list[ExtractedRegisterItem]
    warnings: list[RegisterExtractionWarning]
    created_at: datetime


QuoteCandidateReviewStatus = Literal["ai_draft", "review_required", "excluded_from_pricing"]


class QuoteCandidateEvidence(BaseModel):
    organisation_id: str = "org-demo-tracequote"
    register_item_id: str
    page_number: int
    text: str


class QuoteCandidateLine(BaseModel):
    organisation_id: str = "org-demo-tracequote"
    id: str
    document_id: str
    section: str
    description: str
    quantity: float | None
    unit: str | None
    source_register_item_ids: list[str] = Field(min_length=1)
    source_evidence: list[QuoteCandidateEvidence] = Field(min_length=1)
    source_pages: list[int] = Field(min_length=1)
    confidence: float = Field(ge=0, le=1)
    assumptions: list[str]
    exclusions: list[str]
    reason: str
    review_status: QuoteCandidateReviewStatus
    review_required: bool
    approval_status: Literal["not_ready", "approved"]


class QuoteCandidateGenerationWarning(BaseModel):
    register_item_id: str | None
    message: str
    severity: Literal["info", "warning", "error"]


class QuoteCandidateGenerationResult(BaseModel):
    organisation_id: str = "org-demo-tracequote"
    document_id: str
    mapper_version: str
    source_extraction_version: str
    candidates: list[QuoteCandidateLine]
    warnings: list[QuoteCandidateGenerationWarning]
    created_at: datetime


PricingReviewStatus = Literal["ai_draft", "review_required", "accepted", "excluded_from_pricing"]


class SeedPricebookRule(BaseModel):
    organisation_id: str = "org-demo-tracequote"
    id: str
    name: str
    section: str
    pricing_method: Literal["fixed", "per_unit", "excluded"]
    unit: str
    unit_rate: float | None
    risk_multiplier: float
    margin: float
    material_keywords: list[str]
    class_match: FriabilityClass | None = None
    access_status_match: AccessStatus | None = None
    default_quantity: float | None = None
    minimum_charge: float | None = None
    default_assumptions: list[str]
    default_exclusions: list[str]
    explanation_template: str


class PricedQuoteLine(BaseModel):
    organisation_id: str = "org-demo-tracequote"
    id: str
    document_id: str
    quote_candidate_id: str
    section: str
    description: str
    quantity: float | None
    unit: str | None
    unit_rate: float | None
    base_cost: float | None
    risk_multiplier: float
    margin: float
    subtotal_ex_gst: float | None
    gst: float | None
    total_inc_gst: float | None
    pricing_rule_id: str | None
    pricing_rule_name: str | None
    pricing_explanation: str
    source_register_item_ids: list[str] = Field(min_length=1)
    source_evidence: list[QuoteCandidateEvidence] = Field(min_length=1)
    source_pages: list[int] = Field(min_length=1)
    confidence: float = Field(ge=0, le=1)
    assumptions: list[str]
    exclusions: list[str]
    review_status: PricingReviewStatus
    review_required: bool
    approval_status: Literal["not_ready", "ready_for_approval", "approved"]
    excluded_from_pricing: bool
    assumptions_accepted: bool = False
    exclusions_accepted: bool = False
    reviewed_by: str | None = None
    reviewed_at: datetime | None = None
    review_resolution_reason: str | None = None


class PricingWarning(BaseModel):
    quote_candidate_id: str | None
    message: str
    severity: Literal["info", "warning", "error"]


class PricedQuoteResult(BaseModel):
    organisation_id: str = "org-demo-tracequote"
    document_id: str
    pricing_engine_version: str
    source_mapper_version: str
    pricebook_version: str
    lines: list[PricedQuoteLine]
    warnings: list[PricingWarning]
    subtotal_ex_gst: float
    gst: float
    total_inc_gst: float
    approval_status: Literal["blocked", "ready_for_approval", "approved"]
    estimator_edits: list[EstimatorEdit] = Field(default_factory=list)
    audit_events: list[AuditEvent] = Field(default_factory=list)
    created_at: datetime


class PricedQuoteLineEditRequest(BaseModel):
    quantity: float | None = None
    unit_rate: float | None = None
    risk_multiplier: float | None = Field(default=None, ge=0)
    margin: float | None = Field(default=None, ge=0)
    reason: str = Field(min_length=1)
    user_id: str = "demo-estimator"


class ResolveReviewRequest(BaseModel):
    reason: str = Field(min_length=1)
    user_id: str = "demo-estimator"
    assumptions_accepted: bool = True
    exclusions_accepted: bool = True


class ApprovalReadinessCheck(BaseModel):
    id: str
    label: str
    status: Literal["passed", "blocked"]
    details: str
    blocking_line_ids: list[str] = Field(default_factory=list)


class ApprovalReadinessResult(BaseModel):
    organisation_id: str = "org-demo-tracequote"
    document_id: str
    approval_status: Literal["blocked", "ready_for_approval", "approved"]
    checks: list[ApprovalReadinessCheck]
    unresolved_line_ids: list[str]
    created_at: datetime


# ---------------------------------------------------------------------------
# Jobs — the operator-facing unit of work. A Job wraps one uploaded survey
# (document_id) with intake metadata and a status that drives the whole UI.
# ---------------------------------------------------------------------------

JobStatus = Literal[
    "uploaded",
    "processing",
    "priced",
    "in_review",
    "approved",
    "exported",
    "rejected",
]


class CreateJobRequest(BaseModel):
    client_name: str | None = None
    site_address: str | None = None
    job_reference: str | None = None


class Job(BaseModel):
    id: str
    organisation_id: str
    document_id: str
    file_name: str
    client_name: str | None = None
    site_address: str | None = None
    job_reference: str | None = None
    survey_type: str | None = None
    quotable: bool = True
    status: JobStatus = "uploaded"
    rejected_reason: str | None = None
    register_items: int = 0
    review_required: int = 0
    total_inc_gst: float | None = None
    approval_status: Literal["blocked", "ready_for_approval", "approved"] | None = None
    created_by: str | None = None
    created_at: datetime
    updated_at: datetime


class JobSummary(BaseModel):
    id: str
    organisation_id: str
    document_id: str
    file_name: str
    client_name: str | None = None
    site_address: str | None = None
    survey_type: str | None = None
    status: JobStatus
    quotable: bool = True
    review_required: int = 0
    total_inc_gst: float | None = None
    created_at: datetime
    updated_at: datetime


class ProcessJobResult(BaseModel):
    job: Job
    priced_quote: PricedQuoteResult | None = None


class QuoteExportRequest(BaseModel):
    client_name: str = "Tauraroa Area School"
    project_name: str = "Asbestos removal workup"
    site_address: str = "Tauraroa Area School, Northland, New Zealand"
    quote_number: str | None = None
    scope_summary: str = (
        "Reviewed asbestos removal and provisional investigation scope derived from the uploaded asbestos demolition survey."
    )


class QuoteExportPackage(BaseModel):
    organisation_id: str = "org-demo-tracequote"
    document_id: str
    export_id: str
    quote_number: str
    client_name: str
    project_name: str
    site_address: str
    status: Literal["exported"]
    html_path: str
    pdf_path: str | None = None
    pdf_download_path: str
    html_content: str
    line_count: int
    subtotal_ex_gst: float
    gst: float
    total_inc_gst: float
    assumptions: list[str]
    exclusions: list[str]
    source_pages: list[int]
    generated_at: datetime


Role = Literal["platform_admin", "organisation_admin", "estimator", "reviewer", "viewer"]


class User(BaseModel):
    id: str
    email: str
    name: str
    created_at: datetime


class OrganisationUser(BaseModel):
    id: str
    organisation_id: str
    user_id: str
    email: str
    name: str
    role: Role
    status: Literal["active", "invited", "disabled"] = "active"
    created_at: datetime


class CompanyProfile(BaseModel):
    organisation_id: str
    legal_name: str
    trading_name: str
    email: str | None = None
    phone: str | None = None
    website: str | None = None
    address: str | None = None
    logo_url: str | None = None
    updated_at: datetime


LLMProvider = Literal["none", "anthropic", "openai", "gemini"]
QuoteTemplateType = Literal["default", "ras_style"]


class OrganisationSettings(BaseModel):
    organisation_id: str
    gst_rate: float = 0.15
    default_margin: float = 0.20
    default_currency: str = "NZD"
    quote_prefix: str = "TQ"
    require_review_for_class_a: bool = True
    require_review_for_no_access: bool = True
    # Client-facing quote template. "default" = generic TraceQuote layout (fallback);
    # "ras_style" = RAS-1285 "Estimate" layout. The source-evidence appendix is an
    # internal/audit artifact and is OFF in the client quote unless explicitly enabled.
    template_type: QuoteTemplateType = "default"
    template_name: str = "TraceQuote standard quote"
    show_source_evidence_appendix: bool = False
    show_review_statement: bool = True
    default_email_message: str = (
        "Please find attached your quote. Let us know if you have any questions."
    )
    terms_of_trade_text: str = ""
    # Branding for client-facing quote exports
    business_name: str = "Demo Asbestos Services Ltd"
    business_address_lines: list[str] = Field(default_factory=lambda: ["PO Box 000", "Auckland 1010"])
    business_email: str = "quotes@demo-asbestos.example.nz"
    business_phone: str = "0800 000 000"
    business_gst_number: str = "000-000-000"
    contact_name: str = "Demo Estimator"
    contact_phone: str = "021 000 0000"
    quote_valid_days: int = 30
    # Boilerplate text — defaults to RAS-1285-style content via quote_boilerplate
    quote_intro_text: str = DEFAULT_QUOTE_INTRO_TEXT
    quote_disclaimer_text: str = DEFAULT_QUOTE_DISCLAIMER_TEXT
    quote_acceptance_text: str = DEFAULT_QUOTE_ACCEPTANCE_TEXT
    quote_variation_text: str = DEFAULT_QUOTE_VARIATION_TEXT
    quote_closing_text: str = DEFAULT_QUOTE_CLOSING_TEXT
    quote_inclusions: list[str] = Field(default_factory=lambda: list(DEFAULT_QUOTE_INCLUSIONS))
    quote_important_notes: list[str] = Field(default_factory=lambda: list(DEFAULT_QUOTE_IMPORTANT_NOTES))
    quote_required_services: list[str] = Field(default_factory=lambda: list(DEFAULT_QUOTE_REQUIRED_SERVICES))
    # LLM register extraction (Phase C). Provider "none" falls back to the deterministic hardcoded extractor.
    llm_provider: LLMProvider = "none"
    llm_api_key: str | None = None
    llm_model: str | None = None
    updated_at: datetime


class LLMConfig(BaseModel):
    """API-safe view of an org's LLM configuration — masks the API key."""
    organisation_id: str
    llm_provider: LLMProvider
    llm_model: str | None = None
    has_api_key: bool = False
    api_key_preview: str | None = None  # e.g. "sk-***ab12"
    default_models: dict[str, str] = Field(default_factory=dict)
    updated_at: datetime


class UpsertLLMConfigRequest(BaseModel):
    llm_provider: LLMProvider
    llm_api_key: str | None = None
    llm_model: str | None = None


class LLMTestRequest(BaseModel):
    llm_provider: LLMProvider
    llm_api_key: str
    llm_model: str | None = None


class LLMTestResult(BaseModel):
    ok: bool
    provider: LLMProvider
    model: str
    detail: str


PricebookPricingMethod = Literal["fixed", "per_sqm", "per_piece", "per_hour", "excluded"]
PricebookAccessMatch = Literal["normal", "no-access", "limited-access", "unknown"]


class PricebookRule(BaseModel):
    id: str
    organisation_id: str
    name: str
    category: str = "General"
    section: str = "General"
    material_match: str | None = None
    class_match: FriabilityClass | None = None
    access_match: PricebookAccessMatch = "normal"
    pricing_method: PricebookPricingMethod = "fixed"
    unit: str = "item"
    unit_rate: float | None
    risk_multiplier: float = 1.0
    margin: float = 0.20
    gst_taxable: bool = True
    minimum_charge: float | None = None
    assumptions: list[str] = Field(default_factory=list)
    exclusions: list[str] = Field(default_factory=list)
    review_required: bool = True
    mandatory: bool = False
    active: bool = True


class Pricebook(BaseModel):
    id: str
    organisation_id: str
    name: str
    version: str
    rules: list[PricebookRule]
    active: bool = True
    created_at: datetime
    updated_at: datetime


class QuoteTemplate(BaseModel):
    id: str
    organisation_id: str
    name: str
    description: str
    sections: list[str]
    active: bool = True
    created_at: datetime
    updated_at: datetime


class Organisation(BaseModel):
    id: str
    name: str
    slug: str
    status: Literal["active", "disabled"] = "active"
    company_profile: CompanyProfile
    settings: OrganisationSettings
    created_at: datetime
    updated_at: datetime


class CreateOrganisationRequest(BaseModel):
    name: str = Field(min_length=1)
    slug: str | None = None
    trading_name: str | None = None
    email: str | None = None


class CreateOrganisationUserRequest(BaseModel):
    email: str
    name: str
    role: Role


class UpsertOrganisationSettingsRequest(BaseModel):
    gst_rate: float = 0.15
    default_margin: float = 0.20
    default_currency: str = "NZD"
    quote_prefix: str = "TQ"
    require_review_for_class_a: bool = True
    require_review_for_no_access: bool = True
    business_name: str | None = None
    business_address_lines: list[str] | None = None
    business_email: str | None = None
    business_phone: str | None = None
    business_gst_number: str | None = None
    contact_name: str | None = None
    contact_phone: str | None = None
    quote_valid_days: int | None = None
    quote_intro_text: str | None = None
    quote_disclaimer_text: str | None = None
    quote_acceptance_text: str | None = None
    quote_variation_text: str | None = None
    quote_closing_text: str | None = None
    quote_inclusions: list[str] | None = None
    quote_important_notes: list[str] | None = None
    quote_required_services: list[str] | None = None
    template_type: QuoteTemplateType | None = None
    template_name: str | None = None
    show_source_evidence_appendix: bool | None = None
    show_review_statement: bool | None = None
    default_email_message: str | None = None
    terms_of_trade_text: str | None = None


class CreatePricebookRequest(BaseModel):
    name: str
    version: str = "v1"
    rules: list[PricebookRule] | None = None


class CreatePricebookRuleRequest(BaseModel):
    name: str
    category: str = "General"
    section: str = "General"
    material_match: str | None = None
    class_match: FriabilityClass | None = None
    access_match: PricebookAccessMatch = "normal"
    pricing_method: PricebookPricingMethod = "fixed"
    unit: str = "item"
    unit_rate: float | None = None
    risk_multiplier: float = Field(default=1.0, ge=0)
    margin: float = Field(default=0.20, ge=0)
    gst_taxable: bool = True
    minimum_charge: float | None = Field(default=None, ge=0)
    assumptions: list[str] = Field(default_factory=list)
    exclusions: list[str] = Field(default_factory=list)
    review_required: bool = True
    mandatory: bool = False
    active: bool = True


class UpdatePricebookRuleRequest(BaseModel):
    name: str | None = None
    category: str | None = None
    section: str | None = None
    material_match: str | None = None
    class_match: FriabilityClass | None = None
    access_match: PricebookAccessMatch | None = None
    pricing_method: PricebookPricingMethod | None = None
    unit: str | None = None
    unit_rate: float | None = None
    risk_multiplier: float | None = Field(default=None, ge=0)
    margin: float | None = Field(default=None, ge=0)
    gst_taxable: bool | None = None
    minimum_charge: float | None = Field(default=None, ge=0)
    assumptions: list[str] | None = None
    exclusions: list[str] | None = None
    review_required: bool | None = None
    mandatory: bool | None = None
    active: bool | None = None


class DemoLoginRequest(BaseModel):
    email: str
    password: str


class DemoAuthSession(BaseModel):
    token: str
    email: str
    name: str
    role: Role
    organisation_id: str | None
    default_route: str
    demo_mode: bool = True


class DemoAuthUserRecord(BaseModel):
    id: str
    email: str
    name: str
    role: Role
    organisation_id: str | None
    password_hash: str
    password_salt: str
    created_at: datetime


class MagicExtractionSummary(BaseModel):
    organisation_id: str = "org-demo-tracequote"
    document_id: str
    survey_type: str
    total_pages_parsed: int
    register_items_extracted: int
    quote_ready_items: int = 0
    review_required_items: int = 0
    reference_only_items: int = 0
    quote_candidates_generated: int
    priced_lines_generated: int
    class_a_items: int
    class_b_items: int
    no_access_items: int
    limited_access_items: int
    nad_excluded_items: int
    total_extracted_sqm: float
    source_pages_detected: list[int]
    confidence_summary: dict[str, float]
    magic_entities: dict[str, list[str]]
    created_at: datetime
