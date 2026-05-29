from __future__ import annotations

from pathlib import Path
import logging

from fastapi import Depends, FastAPI, File, Form, HTTPException, Request, Response, UploadFile
from fastapi.responses import FileResponse, JSONResponse, RedirectResponse
from fastapi.middleware.cors import CORSMiddleware

from .auth import (
    AuthUser,
    MUTATING_ROLES,
    get_current_user,
    require_document_access,
    require_document_role,
    require_org_access,
    require_org_role,
    require_platform_admin,
    require_role,
)
from .config import get_settings
from .demo_data import WORKUP_ID, get_demo_workup
from .document_parser import InvalidStorageId, load_parsed_document, parse_pdf, save_upload
from .export_engine import ExportBlockedError, export_quote, load_quote_export
from .fergus_csv_export import save_fergus_csv
from .demo_auth import demo_login, load_demo_auth_users, seed_demo_environment
from .magic_summary import build_magic_summary
from .organisation_store import (
    activate_pricebook,
    add_organisation_user,
    add_pricebook_rule,
    create_organisation,
    create_pricebook,
    delete_pricebook_rule,
    ensure_default_organisation,
    get_llm_config,
    get_organisation,
    get_organisation_settings,
    get_pricebook,
    list_organisation_users,
    list_organisations,
    list_pricebooks,
    update_llm_config,
    update_pricebook_rule,
    upsert_organisation_settings,
)
from .pricing_engine import (
    PricingLineNotFound,
    PricingValidationError,
    edit_priced_quote_line,
    get_approval_readiness,
    load_priced_quote_lines,
    price_quote_candidates,
    resolve_priced_quote_line_review,
)
from .register_extractor import extract_register, load_register_extraction
from .quote_candidate_mapper import generate_quote_candidates, load_quote_candidates
from .job_store import create_job, get_job, list_jobs, set_status
from .schemas import (
    AsbestosRegisterItem,
    AuditEvent,
    ApprovalReadinessResult,
    CreateOrganisationRequest,
    CreateOrganisationUserRequest,
    CreatePricebookRequest,
    CreatePricebookRuleRequest,
    DemoAuthSession,
    DemoAuthUserRecord,
    DemoLoginRequest,
    CreateJobRequest,
    HealthResponse,
    Job,
    JobSummary,
    LLMConfig,
    LLMTestRequest,
    LLMTestResult,
    MagicExtractionSummary,
    ProcessJobResult,
    Organisation,
    OrganisationSettings,
    OrganisationUser,
    ParsedDocument,
    ParsedPage,
    Pricebook,
    PricebookRule,
    PricedQuoteLineEditRequest,
    PricedQuoteResult,
    QuoteExportPackage,
    QuoteExportRequest,
    QuoteLine,
    QuoteWorkup,
    QuoteCandidateGenerationResult,
    RegisterExtractionResult,
    ResolveReviewRequest,
    UpdatePricebookRuleRequest,
    UpsertLLMConfigRequest,
    UpsertOrganisationSettingsRequest,
)

logger = logging.getLogger("tracequote")
settings = get_settings()
if settings.is_production:
    logger.warning("TraceQuote AI is running in production mode. Demo auth remains enabled only for controlled pilot use.")

app = FastAPI(
    title="TraceQuote AI API",
    description="Contract-first API for the TraceQuote AI Phase 1 product shell.",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.exception_handler(InvalidStorageId)
def _handle_invalid_storage_id(request: Request, exc: InvalidStorageId) -> JSONResponse:
    """Reject path-traversal and malformed ID inputs with a 400, not a 500."""
    return JSONResponse(status_code=400, content={"detail": str(exc)})


# Maximum upload size in bytes (50 MB). Larger uploads are rejected with 413.
MAX_UPLOAD_BYTES = 50 * 1024 * 1024


async def _read_upload_capped(file: UploadFile, max_bytes: int = MAX_UPLOAD_BYTES) -> bytes:
    """Read an UploadFile in chunks, rejecting if total exceeds max_bytes."""
    chunks: list[bytes] = []
    total = 0
    chunk_size = 1024 * 1024  # 1 MB chunks
    while True:
        chunk = await file.read(chunk_size)
        if not chunk:
            break
        total += len(chunk)
        if total > max_bytes:
            raise HTTPException(
                status_code=413,
                detail=f"Upload exceeds maximum size of {max_bytes // (1024 * 1024)} MB",
            )
        chunks.append(chunk)
    return b"".join(chunks)


@app.get("/health", response_model=HealthResponse)
def health() -> HealthResponse:
    ensure_default_organisation()
    return HealthResponse(status="ok", service="tracequote-api", version="0.1.0")


@app.post("/auth/login", response_model=DemoAuthSession)
def login(request: DemoLoginRequest) -> DemoAuthSession:
    if get_settings().demo_seed_enabled:
        seed_demo_environment()
    session = demo_login(request)
    if session is None:
        raise HTTPException(status_code=401, detail="Invalid demo credentials")
    return session


@app.post("/auth/logout")
def logout() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/demo/seed")
def seed_demo() -> dict[str, object]:
    if not get_settings().demo_seed_enabled:
        raise HTTPException(status_code=403, detail="Demo seed is disabled for this environment")
    return seed_demo_environment()


@app.get("/demo/users")
def get_demo_users() -> list[dict[str, object]]:
    current_settings = get_settings()
    if not current_settings.demo_seed_enabled:
        raise HTTPException(status_code=403, detail="Demo seed is disabled for this environment")
    # Defence in depth: never expose demo user records outside a local-dev env, even if demo seed is enabled.
    if current_settings.app_env != "local":
        raise HTTPException(status_code=403, detail="Demo users are only listed in local development")
    seed_demo_environment()
    # Strip password hash + salt before returning — even on local, these never need to leave the server.
    return [
        user.model_dump(exclude={"password_hash", "password_salt"})
        for user in load_demo_auth_users()
    ]


@app.post("/organisations", response_model=Organisation)
def create_organisation_endpoint(
    request: CreateOrganisationRequest,
    _user: AuthUser = Depends(require_platform_admin),
) -> Organisation:
    return create_organisation(request)


@app.get("/organisations", response_model=list[Organisation])
def list_organisations_endpoint(
    _user: AuthUser = Depends(require_platform_admin),
) -> list[Organisation]:
    return list_organisations()


@app.get("/organisations/{org_id}", response_model=Organisation)
def get_organisation_endpoint(
    org_id: str,
    _user: AuthUser = Depends(require_org_access),
) -> Organisation:
    organisation = get_organisation(org_id)
    if organisation is None:
        raise HTTPException(status_code=404, detail="Organisation not found")
    return organisation


@app.post("/organisations/{org_id}/users", response_model=OrganisationUser)
def add_organisation_user_endpoint(
    org_id: str,
    request: CreateOrganisationUserRequest,
    _user: AuthUser = Depends(require_org_role("organisation_admin")),
) -> OrganisationUser:
    user = add_organisation_user(org_id, request)
    if user is None:
        raise HTTPException(status_code=404, detail="Organisation not found")
    return user


@app.get("/organisations/{org_id}/users", response_model=list[OrganisationUser])
def list_organisation_users_endpoint(
    org_id: str,
    _user: AuthUser = Depends(require_org_role("organisation_admin")),
) -> list[OrganisationUser]:
    if get_organisation(org_id) is None:
        raise HTTPException(status_code=404, detail="Organisation not found")
    return list_organisation_users(org_id)


@app.post("/organisations/{org_id}/pricebooks", response_model=Pricebook)
def create_organisation_pricebook_endpoint(
    org_id: str,
    request: CreatePricebookRequest,
    _user: AuthUser = Depends(require_org_role("organisation_admin")),
) -> Pricebook:
    pricebook = create_pricebook(org_id, request)
    if pricebook is None:
        raise HTTPException(status_code=404, detail="Organisation not found")
    return pricebook


@app.get("/organisations/{org_id}/pricebooks", response_model=list[Pricebook])
def list_organisation_pricebooks_endpoint(
    org_id: str,
    _user: AuthUser = Depends(require_org_role("organisation_admin")),
) -> list[Pricebook]:
    if get_organisation(org_id) is None:
        raise HTTPException(status_code=404, detail="Organisation not found")
    return list_pricebooks(org_id)


@app.get("/organisations/{org_id}/pricebooks/{pricebook_id}", response_model=Pricebook)
def get_organisation_pricebook_endpoint(
    org_id: str,
    pricebook_id: str,
    _user: AuthUser = Depends(require_org_role("organisation_admin")),
) -> Pricebook:
    if get_organisation(org_id) is None:
        raise HTTPException(status_code=404, detail="Organisation not found")
    pricebook = get_pricebook(org_id, pricebook_id)
    if pricebook is None:
        raise HTTPException(status_code=404, detail="Pricebook not found")
    return pricebook


@app.post("/organisations/{org_id}/pricebooks/{pricebook_id}/rules", response_model=PricebookRule)
def add_organisation_pricebook_rule_endpoint(
    org_id: str,
    pricebook_id: str,
    request: CreatePricebookRuleRequest,
    _user: AuthUser = Depends(require_org_role("organisation_admin")),
) -> PricebookRule:
    if get_organisation(org_id) is None:
        raise HTTPException(status_code=404, detail="Organisation not found")
    pricebook = add_pricebook_rule(org_id, pricebook_id, request)
    if pricebook is None:
        raise HTTPException(status_code=404, detail="Pricebook not found")
    return pricebook.rules[-1]


@app.patch("/organisations/{org_id}/pricebooks/{pricebook_id}/rules/{rule_id}", response_model=PricebookRule)
def update_organisation_pricebook_rule_endpoint(
    org_id: str,
    pricebook_id: str,
    rule_id: str,
    request: UpdatePricebookRuleRequest,
    _user: AuthUser = Depends(require_org_role("organisation_admin")),
) -> PricebookRule:
    if get_organisation(org_id) is None:
        raise HTTPException(status_code=404, detail="Organisation not found")
    pricebook = update_pricebook_rule(org_id, pricebook_id, rule_id, request)
    if pricebook is None:
        raise HTTPException(status_code=404, detail="Pricebook or rule not found")
    for rule in pricebook.rules:
        if rule.id == rule_id:
            return rule
    raise HTTPException(status_code=404, detail="Pricebook rule not found")


@app.delete("/organisations/{org_id}/pricebooks/{pricebook_id}/rules/{rule_id}", response_model=PricebookRule)
def delete_organisation_pricebook_rule_endpoint(
    org_id: str,
    pricebook_id: str,
    rule_id: str,
    _user: AuthUser = Depends(require_org_role("organisation_admin")),
) -> PricebookRule:
    if get_organisation(org_id) is None:
        raise HTTPException(status_code=404, detail="Organisation not found")
    pricebook = delete_pricebook_rule(org_id, pricebook_id, rule_id)
    if pricebook is None:
        raise HTTPException(status_code=404, detail="Pricebook or rule not found")
    for rule in pricebook.rules:
        if rule.id == rule_id:
            return rule
    raise HTTPException(status_code=404, detail="Pricebook rule not found")


@app.post("/organisations/{org_id}/pricebooks/{pricebook_id}/activate", response_model=Pricebook)
def activate_organisation_pricebook_endpoint(
    org_id: str,
    pricebook_id: str,
    _user: AuthUser = Depends(require_org_role("organisation_admin")),
) -> Pricebook:
    if get_organisation(org_id) is None:
        raise HTTPException(status_code=404, detail="Organisation not found")
    pricebook = activate_pricebook(org_id, pricebook_id)
    if pricebook is None:
        raise HTTPException(status_code=404, detail="Pricebook not found")
    return pricebook


@app.post("/organisations/{org_id}/settings", response_model=OrganisationSettings)
def upsert_organisation_settings_endpoint(
    org_id: str,
    request: UpsertOrganisationSettingsRequest,
    _user: AuthUser = Depends(require_org_role("organisation_admin")),
) -> OrganisationSettings:
    settings = upsert_organisation_settings(org_id, request)
    if settings is None:
        raise HTTPException(status_code=404, detail="Organisation not found")
    return settings


@app.get("/organisations/{org_id}/settings", response_model=OrganisationSettings)
def get_organisation_settings_endpoint(
    org_id: str,
    _user: AuthUser = Depends(require_org_role("organisation_admin")),
) -> OrganisationSettings:
    settings = get_organisation_settings(org_id)
    if settings is None:
        raise HTTPException(status_code=404, detail="Organisation not found")
    # Never expose the raw LLM API key on the wire — UI uses /llm-config to see the masked preview.
    return settings.model_copy(update={"llm_api_key": None})


@app.get("/organisations/{org_id}/llm-config", response_model=LLMConfig)
def get_organisation_llm_config_endpoint(
    org_id: str,
    _user: AuthUser = Depends(require_org_role("organisation_admin")),
) -> LLMConfig:
    if get_organisation(org_id) is None:
        raise HTTPException(status_code=404, detail="Organisation not found")
    config = get_llm_config(org_id)
    if config is None:
        raise HTTPException(status_code=404, detail="Organisation settings not found")
    return config


@app.post("/organisations/{org_id}/llm-config", response_model=LLMConfig)
def update_organisation_llm_config_endpoint(
    org_id: str,
    request: UpsertLLMConfigRequest,
    _user: AuthUser = Depends(require_org_role("organisation_admin")),
) -> LLMConfig:
    config = update_llm_config(org_id, request)
    if config is None:
        raise HTTPException(status_code=404, detail="Organisation not found")
    return config


@app.post("/organisations/{org_id}/llm-config/test", response_model=LLMTestResult)
def test_organisation_llm_config_endpoint(
    org_id: str,
    request: LLMTestRequest,
    _user: AuthUser = Depends(require_org_role("organisation_admin")),
) -> LLMTestResult:
    if get_organisation(org_id) is None:
        raise HTTPException(status_code=404, detail="Organisation not found")
    from .llm_extractor import DEFAULT_MODELS, verify_llm_credentials

    if request.llm_provider == "none":
        raise HTTPException(status_code=400, detail="Choose a provider before testing credentials")
    chosen_model = request.llm_model or DEFAULT_MODELS.get(request.llm_provider) or ""
    ok, detail = verify_llm_credentials(
        provider=request.llm_provider,
        api_key=request.llm_api_key,
        model=request.llm_model,
    )
    return LLMTestResult(ok=ok, provider=request.llm_provider, model=chosen_model, detail=detail)


@app.get("/workups", response_model=list[QuoteWorkup])
def list_workups(_user: AuthUser = Depends(get_current_user)) -> list[QuoteWorkup]:
    return [get_demo_workup()]


@app.get("/workups/{workup_id}", response_model=QuoteWorkup)
def get_workup(workup_id: str, _user: AuthUser = Depends(get_current_user)) -> QuoteWorkup:
    if workup_id != WORKUP_ID:
        raise HTTPException(status_code=404, detail="Workup not found")
    return get_demo_workup()


@app.get("/workups/{workup_id}/register-items", response_model=list[AsbestosRegisterItem])
def get_register_items(workup_id: str, _user: AuthUser = Depends(get_current_user)) -> list[AsbestosRegisterItem]:
    if workup_id != WORKUP_ID:
        raise HTTPException(status_code=404, detail="Workup not found")
    return get_demo_workup().register_items


@app.get("/workups/{workup_id}/quote-lines", response_model=list[QuoteLine])
def get_quote_lines(workup_id: str, _user: AuthUser = Depends(get_current_user)) -> list[QuoteLine]:
    if workup_id != WORKUP_ID:
        raise HTTPException(status_code=404, detail="Workup not found")
    return get_demo_workup().quote_lines


@app.get("/workups/{workup_id}/audit-events", response_model=list[AuditEvent])
def get_audit_events(workup_id: str, _user: AuthUser = Depends(get_current_user)) -> list[AuditEvent]:
    if workup_id != WORKUP_ID:
        raise HTTPException(status_code=404, detail="Workup not found")
    return get_demo_workup().audit_events


def _validate_upload(file: UploadFile) -> None:
    """Guard against non-PDF uploads and oversized files (path traversal is blocked by storage_id validation)."""
    if file.content_type not in {"application/pdf", "application/octet-stream"} and not (
        file.filename or ""
    ).lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF uploads are supported")
    if file.size is not None and file.size > MAX_UPLOAD_BYTES:
        raise HTTPException(
            status_code=413,
            detail=f"Upload exceeds maximum size of {MAX_UPLOAD_BYTES // (1024 * 1024)} MB",
        )


@app.post("/documents/upload", response_model=ParsedDocument)
def upload_document(
    file: UploadFile = File(...),
    _user: AuthUser = Depends(require_role(*MUTATING_ROLES)),
) -> ParsedDocument:
    _validate_upload(file)
    document_id, stored_path = save_upload(file)
    try:
        return parse_pdf(document_id=document_id, file_path=stored_path, file_name=file.filename or "uploaded.pdf")
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@app.post("/organisations/{org_id}/documents/upload", response_model=ParsedDocument)
def upload_organisation_document(
    org_id: str,
    file: UploadFile = File(...),
    _user: AuthUser = Depends(require_org_role(*MUTATING_ROLES)),
) -> ParsedDocument:
    if get_organisation(org_id) is None:
        raise HTTPException(status_code=404, detail="Organisation not found")
    _validate_upload(file)
    document_id, stored_path = save_upload(file, organisation_id=org_id)
    try:
        return parse_pdf(
            document_id=document_id,
            file_path=stored_path,
            file_name=file.filename or "uploaded.pdf",
            organisation_id=org_id,
        )
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@app.get("/organisations/{org_id}/documents/{document_id}", response_model=ParsedDocument)
def get_organisation_document(
    org_id: str,
    document_id: str,
    _user: AuthUser = Depends(require_org_access),
) -> ParsedDocument:
    if get_organisation(org_id) is None:
        raise HTTPException(status_code=404, detail="Organisation not found")
    parsed = load_parsed_document(document_id, organisation_id=org_id)
    if parsed is None:
        raise HTTPException(status_code=404, detail="Document not found")
    return parsed


# ---------------------------------------------------------------------------
# Jobs — the operator-facing, org-scoped unit of work. One uploaded survey
# becomes one Job whose status drives the guided UI. The /process endpoint
# orchestrates the existing per-document pipeline in a single call.
# ---------------------------------------------------------------------------


def _job_summary(job: Job) -> JobSummary:
    return JobSummary(
        id=job.id,
        organisation_id=job.organisation_id,
        document_id=job.document_id,
        file_name=job.file_name,
        client_name=job.client_name,
        site_address=job.site_address,
        survey_type=job.survey_type,
        status=job.status,
        quotable=job.quotable,
        review_required=job.review_required,
        total_inc_gst=job.total_inc_gst,
        created_at=job.created_at,
        updated_at=job.updated_at,
    )


@app.post("/organisations/{org_id}/jobs", response_model=Job)
def create_organisation_job(
    org_id: str,
    file: UploadFile = File(...),
    client_name: str | None = Form(None),
    site_address: str | None = Form(None),
    job_reference: str | None = Form(None),
    created_by: str | None = Form(None),
    _user: AuthUser = Depends(require_org_role(*MUTATING_ROLES)),
) -> Job:
    if get_organisation(org_id) is None:
        raise HTTPException(status_code=404, detail="Organisation not found")
    _validate_upload(file)
    document_id, stored_path = save_upload(file, organisation_id=org_id)
    try:
        parsed = parse_pdf(
            document_id=document_id,
            file_path=stored_path,
            file_name=file.filename or "uploaded.pdf",
            organisation_id=org_id,
        )
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc

    classification = parsed.survey_classification
    return create_job(
        org_id,
        document_id=document_id,
        file_name=parsed.file_name,
        request=CreateJobRequest(
            client_name=client_name,
            site_address=site_address,
            job_reference=job_reference,
        ),
        survey_type=classification.survey_type if classification else None,
        quotable=classification.quotable if classification else True,
        created_by=created_by,
    )


@app.get("/organisations/{org_id}/jobs", response_model=list[JobSummary])
def list_organisation_jobs(
    org_id: str,
    _user: AuthUser = Depends(require_org_access),
) -> list[JobSummary]:
    if get_organisation(org_id) is None:
        raise HTTPException(status_code=404, detail="Organisation not found")
    return [_job_summary(job) for job in list_jobs(org_id)]


@app.get("/organisations/{org_id}/jobs/{job_id}", response_model=Job)
def get_organisation_job(
    org_id: str,
    job_id: str,
    _user: AuthUser = Depends(require_org_access),
) -> Job:
    job = get_job(org_id, job_id)
    if job is None:
        raise HTTPException(status_code=404, detail="Job not found")
    return job


@app.post("/organisations/{org_id}/jobs/{job_id}/process", response_model=ProcessJobResult)
def process_organisation_job(
    org_id: str,
    job_id: str,
    _user: AuthUser = Depends(require_org_role(*MUTATING_ROLES)),
) -> ProcessJobResult:
    job = get_job(org_id, job_id)
    if job is None:
        raise HTTPException(status_code=404, detail="Job not found")

    # Management plans (and any non-quotable survey) are rejected, not priced.
    parsed = load_parsed_document(job.document_id)
    classification = parsed.survey_classification if parsed is not None else None
    if classification is not None and not classification.quotable:
        rejected = set_status(
            org_id,
            job_id,
            "rejected",
            rejected_reason=classification.reason,
            survey_type=classification.survey_type,
        )
        return ProcessJobResult(job=rejected or job, priced_quote=None)

    set_status(org_id, job_id, "processing")

    # Reuse the exact per-document pipeline behind extract → candidates → price.
    if extract_register(job.document_id) is None:
        raise HTTPException(status_code=404, detail="Document not found")
    if generate_quote_candidates(job.document_id) is None:
        raise HTTPException(status_code=404, detail="Document not found")
    priced = price_quote_candidates(job.document_id)
    if priced is None:
        raise HTTPException(status_code=404, detail="Document not found")

    register = load_register_extraction(job.document_id)
    register_count = len(register.items) if register is not None else 0
    review_required = sum(1 for line in priced.lines if line.review_status == "review_required")
    status = "in_review" if review_required > 0 else "priced"

    updated = set_status(
        org_id,
        job_id,
        status,
        register_items=register_count,
        review_required=review_required,
        total_inc_gst=priced.total_inc_gst,
        approval_status=priced.approval_status,
        survey_type=classification.survey_type if classification else job.survey_type,
    )
    return ProcessJobResult(job=updated or job, priced_quote=priced)


@app.post("/organisations/{org_id}/jobs/{job_id}/approve", response_model=Job)
def approve_organisation_job(
    org_id: str,
    job_id: str,
    _user: AuthUser = Depends(require_org_role(*MUTATING_ROLES)),
) -> Job:
    job = get_job(org_id, job_id)
    if job is None:
        raise HTTPException(status_code=404, detail="Job not found")
    readiness = get_approval_readiness(job.document_id)
    if readiness is None:
        raise HTTPException(status_code=409, detail="Job has not been priced yet")
    if readiness.approval_status == "blocked":
        raise HTTPException(
            status_code=409,
            detail="Approval blocked: resolve all review-required lines first.",
        )
    updated = set_status(org_id, job_id, "approved", approval_status="approved")
    return updated or job


@app.post("/organisations/{org_id}/jobs/{job_id}/export", response_model=QuoteExportPackage)
def export_organisation_job(
    org_id: str,
    job_id: str,
    request: QuoteExportRequest | None = None,
    _user: AuthUser = Depends(require_org_role(*MUTATING_ROLES)),
) -> QuoteExportPackage:
    job = get_job(org_id, job_id)
    if job is None:
        raise HTTPException(status_code=404, detail="Job not found")
    try:
        result = export_quote(job.document_id, request)
    except ExportBlockedError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    if result is None:
        raise HTTPException(status_code=404, detail="Reviewed priced quote lines not found")
    set_status(org_id, job_id, "exported")
    return result


@app.get("/documents/{document_id}", response_model=ParsedDocument)
def get_document(
    document_id: str,
    _user: AuthUser = Depends(require_document_access),
) -> ParsedDocument:
    parsed = load_parsed_document(document_id)
    if parsed is None:
        raise HTTPException(status_code=404, detail="Document not found")
    return parsed


@app.get("/documents/{document_id}/pages", response_model=list[ParsedPage])
def get_document_pages(
    document_id: str,
    _user: AuthUser = Depends(require_document_access),
) -> list[ParsedPage]:
    parsed = load_parsed_document(document_id)
    if parsed is None:
        raise HTTPException(status_code=404, detail="Document not found")
    return parsed.pages


@app.get("/documents/{document_id}/magic-summary", response_model=MagicExtractionSummary)
def get_document_magic_summary(
    document_id: str,
    _user: AuthUser = Depends(require_document_access),
) -> MagicExtractionSummary:
    summary = build_magic_summary(document_id)
    if summary is None:
        raise HTTPException(status_code=404, detail="Document not found")
    return summary


@app.post("/documents/{document_id}/extract-register", response_model=RegisterExtractionResult)
def extract_document_register(
    document_id: str,
    _user: AuthUser = Depends(require_document_role(*MUTATING_ROLES)),
) -> RegisterExtractionResult:
    result = extract_register(document_id)
    if result is None:
        raise HTTPException(status_code=404, detail="Document not found")
    return result


@app.get("/documents/{document_id}/register-items", response_model=RegisterExtractionResult)
def get_document_register_items(
    document_id: str,
    _user: AuthUser = Depends(require_document_access),
) -> RegisterExtractionResult:
    result = load_register_extraction(document_id)
    if result is None:
        raise HTTPException(status_code=404, detail="Register extraction not found")
    return result


@app.post("/documents/{document_id}/generate-quote-candidates", response_model=QuoteCandidateGenerationResult)
def generate_document_quote_candidates(
    document_id: str,
    _user: AuthUser = Depends(require_document_role(*MUTATING_ROLES)),
) -> QuoteCandidateGenerationResult:
    # Phase B: block quote generation for non-quotable survey types (e.g. Management Plans)
    # per Xavier's brief — these documents lack the sample-level detail needed for pricing.
    parsed = load_parsed_document(document_id)
    if parsed is not None and parsed.survey_classification is not None:
        classification = parsed.survey_classification
        if not classification.quotable:
            raise HTTPException(
                status_code=422,
                detail={
                    "message": "This document is not quotable.",
                    "survey_type": classification.survey_type,
                    "reason": classification.reason,
                },
            )
    result = generate_quote_candidates(document_id)
    if result is None:
        raise HTTPException(status_code=404, detail="Document not found")
    return result


@app.get("/documents/{document_id}/quote-candidates", response_model=QuoteCandidateGenerationResult)
def get_document_quote_candidates(
    document_id: str,
    _user: AuthUser = Depends(require_document_access),
) -> QuoteCandidateGenerationResult:
    result = load_quote_candidates(document_id)
    if result is None:
        raise HTTPException(status_code=404, detail="Quote candidates not found")
    return result


@app.post("/documents/{document_id}/price-quote-candidates", response_model=PricedQuoteResult)
def price_document_quote_candidates(
    document_id: str,
    _user: AuthUser = Depends(require_document_role(*MUTATING_ROLES)),
) -> PricedQuoteResult:
    result = price_quote_candidates(document_id)
    if result is None:
        raise HTTPException(status_code=404, detail="Document not found")
    return result


@app.get("/documents/{document_id}/priced-quote-lines", response_model=PricedQuoteResult)
def get_document_priced_quote_lines(
    document_id: str,
    _user: AuthUser = Depends(require_document_access),
) -> PricedQuoteResult:
    result = load_priced_quote_lines(document_id)
    if result is None:
        raise HTTPException(status_code=404, detail="Priced quote lines not found")
    return result


@app.post("/documents/{document_id}/priced-quote-lines/{line_id}/edit", response_model=PricedQuoteResult)
def edit_document_priced_quote_line(
    document_id: str,
    line_id: str,
    request: PricedQuoteLineEditRequest,
    _user: AuthUser = Depends(require_document_role(*MUTATING_ROLES)),
) -> PricedQuoteResult:
    try:
        result = edit_priced_quote_line(document_id, line_id, request)
    except PricingLineNotFound as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except PricingValidationError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    if result is None:
        raise HTTPException(status_code=404, detail="Priced quote lines not found")
    return result


@app.post("/documents/{document_id}/priced-quote-lines/{line_id}/resolve-review", response_model=PricedQuoteResult)
def resolve_document_priced_quote_line_review(
    document_id: str,
    line_id: str,
    request: ResolveReviewRequest,
    _user: AuthUser = Depends(require_document_role(*MUTATING_ROLES)),
) -> PricedQuoteResult:
    try:
        result = resolve_priced_quote_line_review(document_id, line_id, request)
    except PricingLineNotFound as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except PricingValidationError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    if result is None:
        raise HTTPException(status_code=404, detail="Priced quote lines not found")
    return result


@app.get("/documents/{document_id}/approval-readiness", response_model=ApprovalReadinessResult)
def get_document_approval_readiness(
    document_id: str,
    _user: AuthUser = Depends(require_document_access),
) -> ApprovalReadinessResult:
    result = get_approval_readiness(document_id)
    if result is None:
        raise HTTPException(status_code=404, detail="Priced quote lines not found")
    return result


@app.post("/documents/{document_id}/export-quote", response_model=QuoteExportPackage)
def export_document_quote(
    document_id: str,
    request: QuoteExportRequest | None = None,
    _user: AuthUser = Depends(require_document_role(*MUTATING_ROLES)),
) -> QuoteExportPackage:
    try:
        result = export_quote(document_id, request)
    except ExportBlockedError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    if result is None:
        raise HTTPException(status_code=404, detail="Reviewed priced quote lines not found")
    return result


@app.get("/documents/{document_id}/export-quote", response_model=QuoteExportPackage)
def get_document_quote_export(
    document_id: str,
    _user: AuthUser = Depends(require_document_access),
) -> QuoteExportPackage:
    result = load_quote_export(document_id)
    if result is None:
        raise HTTPException(status_code=404, detail="Quote export not found")
    return result


@app.get("/documents/{document_id}/export-quote/pdf", response_model=None)
def download_document_quote_pdf(
    document_id: str,
    _user: AuthUser = Depends(require_document_access),
) -> FileResponse | RedirectResponse:
    result = load_quote_export(document_id)
    if result is None or result.pdf_path is None:
        raise HTTPException(status_code=404, detail="Quote PDF export not found")
    if get_settings().file_storage_provider == "r2":
        if result.pdf_download_path.startswith("http"):
            return RedirectResponse(result.pdf_download_path)
        raise HTTPException(status_code=501, detail="R2 PDF download URL is not configured")
    pdf_path = Path(result.pdf_path)
    if not pdf_path.exists():
        raise HTTPException(status_code=404, detail="Quote PDF file not found")
    return FileResponse(
        path=pdf_path,
        filename=f"{result.quote_number}.pdf",
        media_type="application/pdf",
    )


@app.get("/documents/{document_id}/export-quote/fergus.csv", response_model=None)
def download_document_fergus_csv(
    document_id: str,
    _user: AuthUser = Depends(require_document_access),
) -> Response:
    """Fergus-importable CSV of all priced quote lines.

    Free alternative to a paid Fergus API integration. The estimator downloads
    this CSV and pastes/imports it into Fergus' cost-line builder. Description
    column matches Fergus's "cost line item title" per Xavier's Feb 26 brief.
    """
    saved = save_fergus_csv(document_id)
    if saved is None:
        raise HTTPException(
            status_code=404,
            detail="Priced quote lines not found — price the document before exporting to Fergus CSV.",
        )
    csv_content, _path = saved
    filename = f"fergus-quote-{document_id}.csv"
    return Response(
        content=csv_content,
        media_type="text/csv",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )
