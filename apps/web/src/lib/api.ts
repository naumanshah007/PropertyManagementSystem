import type {
  ApprovalReadinessResult,
  DemoAuthSession,
  DemoLoginRequest,
  CreatePricebookRuleRequest,
  MagicExtractionSummary,
  ParsedDocument,
  ParsedPage,
  Pricebook,
  PricebookRule,
  PricedQuoteLineEditRequest,
  PricedQuoteResult,
  QuoteExportPackage,
  QuoteExportRequest,
  QuoteCandidateGenerationResult,
  RegisterExtractionResult,
  ResolveReviewRequest,
  UpdatePricebookRuleRequest,
} from "./types";

export const API_BASE_URL =
  process.env.NEXT_PUBLIC_API_BASE_URL ??
  "http://127.0.0.1:8000";

const SESSION_STORAGE_KEY = "tracequote:demoSession";

/** Typed API error carrying the HTTP status so pages can show 401/403 states. */
export class ApiError extends Error {
  status: number;
  constructor(status: number, message: string) {
    super(message);
    this.status = status;
    this.name = "ApiError";
  }
}

function storedToken(): string | null {
  if (typeof window === "undefined") return null;
  try {
    const raw = window.localStorage.getItem(SESSION_STORAGE_KEY);
    return raw ? (JSON.parse(raw).token ?? null) : null;
  } catch {
    return null;
  }
}

/**
 * Authenticated fetch: attaches the bearer token and, on a 401, clears the
 * stale session and bounces to /login. Everything in this module routes
 * through here except the login call itself.
 */
async function apiFetch(url: string, init: RequestInit = {}): Promise<Response> {
  const token = storedToken();
  const headers = new Headers(init.headers);
  if (token) headers.set("Authorization", `Bearer ${token}`);

  const response = await fetch(url, { ...init, headers });

  if (response.status === 401 && typeof window !== "undefined") {
    window.localStorage.removeItem(SESSION_STORAGE_KEY);
    if (!window.location.pathname.startsWith("/login")) {
      window.location.href = "/login";
    }
  }
  return response;
}

export async function uploadPdf(file: File): Promise<ParsedDocument> {
  const body = new FormData();
  body.append("file", file);

  const response = await apiFetch(`${API_BASE_URL}/documents/upload`, {
    method: "POST",
    body,
  });

  if (!response.ok) {
    const detail = await response.text();
    throw new ApiError(response.status, `Upload failed (${response.status}): ${detail}`);
  }

  return response.json() as Promise<ParsedDocument>;
}

export async function getParsedDocument(documentId: string): Promise<ParsedDocument> {
  const response = await apiFetch(`${API_BASE_URL}/documents/${documentId}`, {
    cache: "no-store",
  });

  if (!response.ok) {
    throw new ApiError(response.status, `Document fetch failed (${response.status})`);
  }

  return response.json() as Promise<ParsedDocument>;
}

export async function getParsedPages(documentId: string): Promise<ParsedPage[]> {
  const response = await apiFetch(`${API_BASE_URL}/documents/${documentId}/pages`, {
    cache: "no-store",
  });

  if (!response.ok) {
    throw new ApiError(response.status, `Pages fetch failed (${response.status})`);
  }

  return response.json() as Promise<ParsedPage[]>;
}

export async function getMagicSummary(documentId: string): Promise<MagicExtractionSummary> {
  const response = await apiFetch(`${API_BASE_URL}/documents/${documentId}/magic-summary`, {
    cache: "no-store",
  });

  if (!response.ok) {
    throw new ApiError(response.status, `Magic summary fetch failed (${response.status})`);
  }

  return response.json() as Promise<MagicExtractionSummary>;
}

export async function extractRegister(documentId: string): Promise<RegisterExtractionResult> {
  const response = await apiFetch(`${API_BASE_URL}/documents/${documentId}/extract-register`, {
    method: "POST",
  });

  if (!response.ok) {
    throw new ApiError(response.status, `Register extraction failed (${response.status})`);
  }

  return response.json() as Promise<RegisterExtractionResult>;
}

export async function getRegisterExtraction(documentId: string): Promise<RegisterExtractionResult> {
  const response = await apiFetch(`${API_BASE_URL}/documents/${documentId}/register-items`, {
    cache: "no-store",
  });

  if (!response.ok) {
    throw new ApiError(response.status, `Register extraction fetch failed (${response.status})`);
  }

  return response.json() as Promise<RegisterExtractionResult>;
}

export async function generateQuoteCandidates(documentId: string): Promise<QuoteCandidateGenerationResult> {
  const response = await apiFetch(`${API_BASE_URL}/documents/${documentId}/generate-quote-candidates`, {
    method: "POST",
  });

  if (!response.ok) {
    throw new ApiError(response.status, `Quote candidate generation failed (${response.status})`);
  }

  return response.json() as Promise<QuoteCandidateGenerationResult>;
}

export async function getQuoteCandidates(documentId: string): Promise<QuoteCandidateGenerationResult> {
  const response = await apiFetch(`${API_BASE_URL}/documents/${documentId}/quote-candidates`, {
    cache: "no-store",
  });

  if (!response.ok) {
    throw new ApiError(response.status, `Quote candidate fetch failed (${response.status})`);
  }

  return response.json() as Promise<QuoteCandidateGenerationResult>;
}

export async function priceQuoteCandidates(documentId: string): Promise<PricedQuoteResult> {
  const response = await apiFetch(`${API_BASE_URL}/documents/${documentId}/price-quote-candidates`, {
    method: "POST",
  });

  if (!response.ok) {
    throw new ApiError(response.status, `Quote pricing failed (${response.status})`);
  }

  return response.json() as Promise<PricedQuoteResult>;
}

export async function getPricedQuoteLines(documentId: string): Promise<PricedQuoteResult> {
  const response = await apiFetch(`${API_BASE_URL}/documents/${documentId}/priced-quote-lines`, {
    cache: "no-store",
  });

  if (!response.ok) {
    throw new ApiError(response.status, `Priced quote line fetch failed (${response.status})`);
  }

  return response.json() as Promise<PricedQuoteResult>;
}

export async function editPricedQuoteLine(
  documentId: string,
  lineId: string,
  payload: PricedQuoteLineEditRequest,
): Promise<PricedQuoteResult> {
  const response = await apiFetch(`${API_BASE_URL}/documents/${documentId}/priced-quote-lines/${lineId}/edit`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });

  if (!response.ok) {
    const detail = await response.text();
    throw new ApiError(response.status, `Priced line edit failed (${response.status}): ${detail}`);
  }

  return response.json() as Promise<PricedQuoteResult>;
}

export async function resolvePricedQuoteLineReview(
  documentId: string,
  lineId: string,
  payload: ResolveReviewRequest,
): Promise<PricedQuoteResult> {
  const response = await apiFetch(`${API_BASE_URL}/documents/${documentId}/priced-quote-lines/${lineId}/resolve-review`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });

  if (!response.ok) {
    const detail = await response.text();
    throw new ApiError(response.status, `Review resolution failed (${response.status}): ${detail}`);
  }

  return response.json() as Promise<PricedQuoteResult>;
}

export async function getApprovalReadiness(documentId: string): Promise<ApprovalReadinessResult> {
  const response = await apiFetch(`${API_BASE_URL}/documents/${documentId}/approval-readiness`, {
    cache: "no-store",
  });

  if (!response.ok) {
    throw new ApiError(response.status, `Approval readiness fetch failed (${response.status})`);
  }

  return response.json() as Promise<ApprovalReadinessResult>;
}

export async function exportQuote(documentId: string, payload?: QuoteExportRequest): Promise<QuoteExportPackage> {
  const response = await apiFetch(`${API_BASE_URL}/documents/${documentId}/export-quote`, {
    method: "POST",
    headers: payload ? { "Content-Type": "application/json" } : undefined,
    body: payload ? JSON.stringify(payload) : undefined,
  });

  if (!response.ok) {
    const detail = await response.text();
    throw new ApiError(response.status, `Quote export failed (${response.status}): ${detail}`);
  }

  return response.json() as Promise<QuoteExportPackage>;
}

export async function getQuoteExport(documentId: string): Promise<QuoteExportPackage> {
  const response = await apiFetch(`${API_BASE_URL}/documents/${documentId}/export-quote`, {
    cache: "no-store",
  });

  if (!response.ok) {
    throw new ApiError(response.status, `Quote export fetch failed (${response.status})`);
  }

  return response.json() as Promise<QuoteExportPackage>;
}

export async function listOrganisationPricebooks(orgId: string): Promise<Pricebook[]> {
  const response = await apiFetch(`${API_BASE_URL}/organisations/${orgId}/pricebooks`, {
    cache: "no-store",
  });

  if (!response.ok) {
    throw new ApiError(response.status, `Pricebook list fetch failed (${response.status})`);
  }

  return response.json() as Promise<Pricebook[]>;
}

export async function getOrganisationPricebook(orgId: string, pricebookId: string): Promise<Pricebook> {
  const response = await apiFetch(`${API_BASE_URL}/organisations/${orgId}/pricebooks/${pricebookId}`, {
    cache: "no-store",
  });

  if (!response.ok) {
    throw new ApiError(response.status, `Pricebook fetch failed (${response.status})`);
  }

  return response.json() as Promise<Pricebook>;
}

export async function addPricebookRule(
  orgId: string,
  pricebookId: string,
  payload: CreatePricebookRuleRequest,
): Promise<PricebookRule> {
  const response = await apiFetch(`${API_BASE_URL}/organisations/${orgId}/pricebooks/${pricebookId}/rules`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });

  if (!response.ok) {
    const detail = await response.text();
    throw new ApiError(response.status, `Pricebook rule create failed (${response.status}): ${detail}`);
  }

  return response.json() as Promise<PricebookRule>;
}

export async function updatePricebookRule(
  orgId: string,
  pricebookId: string,
  ruleId: string,
  payload: UpdatePricebookRuleRequest,
): Promise<PricebookRule> {
  const response = await apiFetch(`${API_BASE_URL}/organisations/${orgId}/pricebooks/${pricebookId}/rules/${ruleId}`, {
    method: "PATCH",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });

  if (!response.ok) {
    const detail = await response.text();
    throw new ApiError(response.status, `Pricebook rule update failed (${response.status}): ${detail}`);
  }

  return response.json() as Promise<PricebookRule>;
}

export async function deletePricebookRule(orgId: string, pricebookId: string, ruleId: string): Promise<PricebookRule> {
  const response = await apiFetch(`${API_BASE_URL}/organisations/${orgId}/pricebooks/${pricebookId}/rules/${ruleId}`, {
    method: "DELETE",
  });

  if (!response.ok) {
    const detail = await response.text();
    throw new ApiError(response.status, `Pricebook rule delete failed (${response.status}): ${detail}`);
  }

  return response.json() as Promise<PricebookRule>;
}

export async function activatePricebook(orgId: string, pricebookId: string): Promise<Pricebook> {
  const response = await apiFetch(`${API_BASE_URL}/organisations/${orgId}/pricebooks/${pricebookId}/activate`, {
    method: "POST",
  });

  if (!response.ok) {
    throw new ApiError(response.status, `Pricebook activation failed (${response.status})`);
  }

  return response.json() as Promise<Pricebook>;
}

export function createOfflineParsedDocumentFallback(): ParsedDocument {
  return {
    document_id: "offline-demo-fallback",
    file_name: "offline-demo-fallback.pdf",
    page_count: 1,
    parser_version: "offline-demo-fallback",
    pages: [
      {
        page_number: 1,
        text: "Offline demo fallback only. Start FastAPI and upload a PDF to view real parsed text.",
        warnings: ["offline_demo_fallback"],
      },
    ],
    tables: [],
    ocr_status: "required_later",
    stored_path: "offline-demo-fallback",
    parsed_json_path: "offline-demo-fallback",
    created_at: new Date(0).toISOString(),
  };
}
export async function loginDemo(payload: DemoLoginRequest): Promise<DemoAuthSession> {
  // Raw fetch — there's no token yet and a 401 here means "wrong password",
  // which must surface as an error rather than a redirect loop.
  const response = await fetch(`${API_BASE_URL}/auth/login`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });

  if (!response.ok) {
    throw new ApiError(response.status, `Login failed (${response.status})`);
  }

  return response.json() as Promise<DemoAuthSession>;
}

export async function logoutDemo(): Promise<void> {
  await apiFetch(`${API_BASE_URL}/auth/logout`, { method: "POST" });
}

export async function getLLMConfig(orgId: string): Promise<import("./types").LLMConfig> {
  const response = await apiFetch(`${API_BASE_URL}/organisations/${orgId}/llm-config`, {
    cache: "no-store",
  });
  if (!response.ok) {
    throw new ApiError(response.status, `LLM config fetch failed (${response.status})`);
  }
  return response.json();
}

export async function updateLLMConfig(
  orgId: string,
  payload: import("./types").UpsertLLMConfigRequest
): Promise<import("./types").LLMConfig> {
  const response = await apiFetch(`${API_BASE_URL}/organisations/${orgId}/llm-config`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  if (!response.ok) {
    const detail = await response.text();
    throw new ApiError(response.status, `LLM config update failed (${response.status}): ${detail}`);
  }
  return response.json();
}

export async function testLLMConfig(
  orgId: string,
  payload: { llm_provider: import("./types").LLMProvider; llm_api_key: string; llm_model?: string | null }
): Promise<import("./types").LLMTestResult> {
  const response = await apiFetch(`${API_BASE_URL}/organisations/${orgId}/llm-config/test`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  if (!response.ok) {
    const detail = await response.text();
    throw new ApiError(response.status, `LLM credentials test failed (${response.status}): ${detail}`);
  }
  return response.json();
}

export interface CreateOrganisationPayload {
  name: string;
  trading_name?: string | null;
  slug?: string | null;
  email: string;
}

export interface CreatedOrganisation {
  id: string;
  name: string;
  slug: string;
}

export async function createOrganisation(
  payload: CreateOrganisationPayload
): Promise<CreatedOrganisation> {
  const response = await apiFetch(`${API_BASE_URL}/organisations`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  if (!response.ok) {
    const detail = await response.text();
    throw new ApiError(response.status, `Organisation creation failed (${response.status}): ${detail}`);
  }
  return response.json();
}

// ---------------------------------------------------------------------------
// Jobs — the operator-facing unit of work (org-scoped).
// ---------------------------------------------------------------------------

/**
 * The org a logged-in user operates within. Org admins carry their own
 * organisation_id; platform admins (org_id === null) fall back to the seeded
 * demo org so the workflow is still operable from the admin seat.
 */
export const DEFAULT_DEMO_ORG_ID = "org-demo-asbestos-services";

export function getActiveOrgId(orgId?: string | null): string {
  return orgId && orgId.length > 0 ? orgId : DEFAULT_DEMO_ORG_ID;
}

export async function createJob(
  orgId: string,
  payload: import("./types").CreateJobPayload,
): Promise<import("./types").Job> {
  const body = new FormData();
  body.append("file", payload.file);
  if (payload.client_name) body.append("client_name", payload.client_name);
  if (payload.site_address) body.append("site_address", payload.site_address);
  if (payload.job_reference) body.append("job_reference", payload.job_reference);
  if (payload.created_by) body.append("created_by", payload.created_by);

  const response = await apiFetch(`${API_BASE_URL}/organisations/${orgId}/jobs`, {
    method: "POST",
    body,
  });
  if (!response.ok) {
    const detail = await response.text();
    throw new ApiError(response.status, `Job creation failed (${response.status}): ${detail}`);
  }
  return response.json();
}

export async function listJobs(orgId: string): Promise<import("./types").JobSummary[]> {
  const response = await apiFetch(`${API_BASE_URL}/organisations/${orgId}/jobs`, { cache: "no-store" });
  if (!response.ok) {
    throw new ApiError(response.status, `Job list fetch failed (${response.status})`);
  }
  return response.json();
}

export async function getJob(orgId: string, jobId: string): Promise<import("./types").Job> {
  const response = await apiFetch(`${API_BASE_URL}/organisations/${orgId}/jobs/${jobId}`, { cache: "no-store" });
  if (!response.ok) {
    throw new ApiError(response.status, `Job fetch failed (${response.status})`);
  }
  return response.json();
}

export async function processJob(orgId: string, jobId: string): Promise<import("./types").ProcessJobResult> {
  const response = await apiFetch(`${API_BASE_URL}/organisations/${orgId}/jobs/${jobId}/process`, {
    method: "POST",
  });
  if (!response.ok) {
    const detail = await response.text();
    throw new ApiError(response.status, `Job processing failed (${response.status}): ${detail}`);
  }
  return response.json();
}

export async function approveJob(orgId: string, jobId: string): Promise<import("./types").Job> {
  const response = await apiFetch(`${API_BASE_URL}/organisations/${orgId}/jobs/${jobId}/approve`, {
    method: "POST",
  });
  if (!response.ok) {
    const detail = await response.text();
    throw new ApiError(response.status, `Job approval failed (${response.status}): ${detail}`);
  }
  return response.json();
}

export async function exportJob(
  orgId: string,
  jobId: string,
  payload?: QuoteExportRequest,
): Promise<QuoteExportPackage> {
  const response = await apiFetch(`${API_BASE_URL}/organisations/${orgId}/jobs/${jobId}/export`, {
    method: "POST",
    headers: payload ? { "Content-Type": "application/json" } : undefined,
    body: payload ? JSON.stringify(payload) : undefined,
  });
  if (!response.ok) {
    const detail = await response.text();
    throw new ApiError(response.status, `Job export failed (${response.status}): ${detail}`);
  }
  return response.json();
}
