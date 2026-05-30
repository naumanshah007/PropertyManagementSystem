export type ReviewStatus =
  | "ai_draft"
  | "review_required"
  | "accepted"
  | "edited"
  | "approved"
  | "blocked";

export type WorkupStatus =
  | "intake"
  | "extracting"
  | "needs_review"
  | "pricing_draft"
  | "approval_required"
  | "approved"
  | "exported"
  | "blocked";

export interface SourceEvidence {
  id: string;
  document_id: string;
  page_number: number;
  evidence_type: string;
  raw_text: string;
  confidence: number;
  bounding_box?: Record<string, number> | null;
}

export interface SourceDocument {
  id: string;
  workup_id: string;
  file_name: string;
  file_type: string;
  page_count: number;
  parser_version: string;
  ocr_status: string;
  created_at: string;
}

export interface RiskFlag {
  id: string;
  label: string;
  severity: "info" | "attention" | "high" | "blocked";
  description: string;
  review_status: ReviewStatus;
  source_evidence_ids: string[];
}

export interface AsbestosRegisterItem {
  id: string;
  workup_id: string;
  location: string;
  area: string;
  material: string;
  product_type: string;
  extent_quantity: number | null;
  extent_unit: string;
  asbestos_result: string;
  fibre_type: string | null;
  friability_class: string;
  condition: string | null;
  recommendation: string;
  access_status: string;
  source_evidence_ids: string[];
  confidence: number;
  review_status: ReviewStatus;
}

export interface PricingRule {
  id: string;
  name: string;
  job_type: string;
  formula: string;
  risk_factors: string[];
  default_assumptions: string[];
  default_exclusions: string[];
  version: string;
}

export interface QuoteLine {
  id: string;
  workup_id: string;
  section: string;
  description: string;
  quantity: number | null;
  unit: string;
  unit_rate: number | null;
  base_cost: number | null;
  risk_multiplier: number;
  margin: number;
  gst: number | null;
  total: number | null;
  source_evidence_ids: string[];
  pricing_rule_ids: string[];
  assumptions: string[];
  exclusions: string[];
  review_status: ReviewStatus;
  approval_status: "not_ready" | "ready_for_approval" | "approved";
  why: string;
}

export interface EstimatorEdit {
  id: string;
  workup_id: string;
  entity_type: string;
  entity_id: string;
  field_name: string;
  previous_value: unknown;
  new_value: unknown;
  reason: string;
  user_id: string;
  created_at: string;
}

export interface AuditEvent {
  id: string;
  workup_id: string;
  actor_type: "system" | "user";
  actor_id: string;
  event_type: string;
  payload: Record<string, unknown>;
  created_at: string;
}

export interface QuoteWorkup {
  id: string;
  client_name: string;
  site_address: string;
  job_type: string;
  survey_type: string;
  status: WorkupStatus;
  assigned_estimator_id: string;
  due_date: string;
  created_at: string;
  updated_at: string;
  documents: SourceDocument[];
  source_evidence: SourceEvidence[];
  register_items: AsbestosRegisterItem[];
  risk_flags: RiskFlag[];
  quote_lines: QuoteLine[];
  pricing_rules: PricingRule[];
  estimator_edits: EstimatorEdit[];
  audit_events: AuditEvent[];
  assumptions: string[];
  exclusions: string[];
  export_status: "blocked" | "ready" | "exported";
}

export type OcrStatus = "not_required" | "required_later" | "failed";

export interface ParsedPage {
  page_number: number;
  text: string;
  warnings: string[];
}

export interface ParsedTable {
  page_number: number;
  rows: string[][];
  extraction_method: string;
}

export interface ParsedDocument {
  document_id: string;
  file_name: string;
  page_count: number;
  parser_version: string;
  pages: ParsedPage[];
  tables: ParsedTable[];
  ocr_status: OcrStatus;
  stored_path: string;
  parsed_json_path: string;
  created_at: string;
}

export type RegisterReviewStatus = "ai_draft" | "review_required" | "excluded_from_pricing";

export type ExtractionCategory =
  | "quote_ready"
  | "review_required"
  | "reference_only"
  | "excluded_from_pricing";

export interface RegisterSourceEvidence {
  document_id: string;
  page_number: number;
  text: string;
}

export interface ExtractedRegisterItem {
  id: string;
  document_id: string;
  building: string | null;
  level: string | null;
  location: string;
  item: string;
  material: string;
  strategy_sample_id: string | null;
  extent_quantity: number | null;
  extent_unit: string | null;
  fibre_type: string | null;
  friability_class: "Class A" | "Class B" | "Unknown";
  asbestos_result: "positive" | "presumed" | "strongly_presumed" | "cross_reference" | "NAD" | "unknown";
  access_status: "accessible" | "no_access" | "limited_access" | "unknown";
  material_score: string | null;
  priority_risk_category: string | null;
  recommendation: string | null;
  source_page: number;
  source_evidence: RegisterSourceEvidence;
  confidence: number;
  review_status: RegisterReviewStatus;
  extraction_category: ExtractionCategory;
  extraction_warnings: string[];
}

export interface RegisterExtractionWarning {
  page_number: number | null;
  message: string;
  severity: "info" | "warning" | "error";
}

export interface RegisterExtractionResult {
  document_id: string;
  parser_version: string;
  source_parser_version: string;
  items: ExtractedRegisterItem[];
  warnings: RegisterExtractionWarning[];
  created_at: string;
}

export type QuoteCandidateReviewStatus = "ai_draft" | "review_required" | "excluded_from_pricing";

export interface QuoteCandidateEvidence {
  register_item_id: string;
  page_number: number;
  text: string;
}

export interface QuoteCandidateLine {
  id: string;
  document_id: string;
  section: string;
  description: string;
  quantity: number | null;
  unit: string | null;
  source_register_item_ids: string[];
  source_evidence: QuoteCandidateEvidence[];
  source_pages: number[];
  confidence: number;
  assumptions: string[];
  exclusions: string[];
  reason: string;
  review_status: QuoteCandidateReviewStatus;
  review_required: boolean;
  approval_status: "not_ready" | "approved";
}

export interface QuoteCandidateGenerationWarning {
  register_item_id: string | null;
  message: string;
  severity: "info" | "warning" | "error";
}

export interface QuoteCandidateGenerationResult {
  document_id: string;
  mapper_version: string;
  source_extraction_version: string;
  candidates: QuoteCandidateLine[];
  warnings: QuoteCandidateGenerationWarning[];
  created_at: string;
}

export type PricingReviewStatus = "ai_draft" | "review_required" | "accepted" | "excluded_from_pricing";

export interface PricedQuoteLine {
  id: string;
  document_id: string;
  quote_candidate_id: string;
  section: string;
  description: string;
  quantity: number | null;
  unit: string | null;
  unit_rate: number | null;
  base_cost: number | null;
  risk_multiplier: number;
  margin: number;
  subtotal_ex_gst: number | null;
  gst: number | null;
  total_inc_gst: number | null;
  pricing_rule_id: string | null;
  pricing_rule_name: string | null;
  pricing_explanation: string;
  source_register_item_ids: string[];
  source_evidence: QuoteCandidateEvidence[];
  source_pages: number[];
  confidence: number;
  assumptions: string[];
  exclusions: string[];
  review_status: PricingReviewStatus;
  review_required: boolean;
  approval_status: "not_ready" | "ready_for_approval" | "approved";
  excluded_from_pricing: boolean;
  assumptions_accepted: boolean;
  exclusions_accepted: boolean;
  reviewed_by: string | null;
  reviewed_at: string | null;
  review_resolution_reason: string | null;
}

export interface PricingWarning {
  quote_candidate_id: string | null;
  message: string;
  severity: "info" | "warning" | "error";
}

export interface PricedQuoteResult {
  document_id: string;
  pricing_engine_version: string;
  source_mapper_version: string;
  pricebook_version: string;
  lines: PricedQuoteLine[];
  warnings: PricingWarning[];
  subtotal_ex_gst: number;
  gst: number;
  total_inc_gst: number;
  approval_status: "blocked" | "ready_for_approval" | "approved";
  estimator_edits: EstimatorEdit[];
  audit_events: AuditEvent[];
  created_at: string;
}

export interface PricedQuoteLineEditRequest {
  quantity?: number | null;
  unit_rate?: number | null;
  risk_multiplier?: number | null;
  margin?: number | null;
  reason: string;
  user_id?: string;
}

export interface ResolveReviewRequest {
  reason: string;
  user_id?: string;
  assumptions_accepted?: boolean;
  exclusions_accepted?: boolean;
}

export interface ApprovalReadinessCheck {
  id: string;
  label: string;
  status: "passed" | "blocked";
  details: string;
  blocking_line_ids: string[];
}

export interface ApprovalReadinessResult {
  document_id: string;
  approval_status: "blocked" | "ready_for_approval" | "approved";
  checks: ApprovalReadinessCheck[];
  unresolved_line_ids: string[];
  created_at: string;
}

export interface QuoteExportPackage {
  document_id: string;
  export_id: string;
  quote_number: string;
  client_name: string;
  project_name: string;
  site_address: string;
  status: "exported";
  html_path: string;
  pdf_path: string | null;
  pdf_download_path: string;
  html_content: string;
  line_count: number;
  subtotal_ex_gst: number;
  gst: number;
  total_inc_gst: number;
  assumptions: string[];
  exclusions: string[];
  source_pages: number[];
  generated_at: string;
}

export interface QuoteExportRequest {
  client_name: string;
  project_name: string;
  site_address: string;
  quote_number?: string | null;
  scope_summary: string;
}

export type Role = "platform_admin" | "organisation_admin" | "estimator" | "reviewer" | "viewer";

export interface DemoLoginRequest {
  email: string;
  password: string;
}

export interface DemoAuthSession {
  token: string;
  email: string;
  name: string;
  role: Role;
  organisation_id: string | null;
  default_route: string;
  demo_mode: boolean;
}

export interface MagicExtractionSummary {
  organisation_id: string;
  document_id: string;
  survey_type: string;
  total_pages_parsed: number;
  register_items_extracted: number;
  quote_ready_items: number;
  review_required_items: number;
  reference_only_items: number;
  quote_candidates_generated: number;
  priced_lines_generated: number;
  class_a_items: number;
  class_b_items: number;
  no_access_items: number;
  limited_access_items: number;
  nad_excluded_items: number;
  total_extracted_sqm: number;
  source_pages_detected: number[];
  confidence_summary: Record<string, number>;
  magic_entities: Record<string, string[]>;
  created_at: string;
}

export type PricebookPricingMethod = "fixed" | "per_sqm" | "per_piece" | "per_hour" | "excluded";
export type PricebookAccessMatch = "normal" | "no-access" | "limited-access" | "unknown";

export interface PricebookRule {
  id: string;
  organisation_id: string;
  name: string;
  category: string;
  section: string;
  material_match: string | null;
  class_match: "Class A" | "Class B" | "Unknown" | null;
  access_match: PricebookAccessMatch;
  pricing_method: PricebookPricingMethod;
  unit: string;
  unit_rate: number | null;
  risk_multiplier: number;
  margin: number;
  gst_taxable: boolean;
  minimum_charge: number | null;
  assumptions: string[];
  exclusions: string[];
  review_required: boolean;
  mandatory: boolean;
  active: boolean;
}

export interface Pricebook {
  id: string;
  organisation_id: string;
  name: string;
  version: string;
  rules: PricebookRule[];
  active: boolean;
  created_at: string;
  updated_at: string;
}

export type CreatePricebookRuleRequest = Omit<PricebookRule, "id" | "organisation_id">;
export type UpdatePricebookRuleRequest = Partial<CreatePricebookRuleRequest>;

export type QuoteTemplateType = "default" | "ras_style";

export interface OrganisationSettings {
  organisation_id: string;
  gst_rate: number;
  default_margin: number;
  default_currency: string;
  quote_prefix: string;
  template_type: QuoteTemplateType;
  template_name: string;
  show_source_evidence_appendix: boolean;
  show_review_statement: boolean;
  default_email_message: string;
  terms_of_trade_text: string;
  business_name: string;
  business_address_lines: string[];
  business_email: string;
  business_phone: string;
  business_gst_number: string;
  contact_name: string;
  contact_phone: string;
  quote_valid_days: number;
  quote_intro_text: string;
  quote_closing_text: string;
  quote_inclusions: string[];
  quote_important_notes: string[];
  quote_required_services: string[];
  updated_at: string;
}

export type UpsertOrganisationSettingsPayload = Partial<
  Omit<OrganisationSettings, "organisation_id" | "updated_at">
>;

export type LLMProvider = "none" | "anthropic" | "openai" | "gemini";

export interface LLMConfig {
  organisation_id: string;
  llm_provider: LLMProvider;
  llm_model: string | null;
  has_api_key: boolean;
  api_key_preview: string | null;
  default_models: Record<string, string>;
  updated_at: string;
}

export interface UpsertLLMConfigRequest {
  llm_provider: LLMProvider;
  llm_api_key?: string | null;
  llm_model?: string | null;
}

export interface LLMTestResult {
  ok: boolean;
  provider: LLMProvider;
  model: string;
  detail: string;
}

export type JobStatus =
  | "uploaded"
  | "processing"
  | "priced"
  | "in_review"
  | "approved"
  | "exported"
  | "rejected";

export interface Job {
  id: string;
  organisation_id: string;
  document_id: string;
  file_name: string;
  client_name: string | null;
  site_address: string | null;
  job_reference: string | null;
  survey_type: string | null;
  quotable: boolean;
  status: JobStatus;
  rejected_reason: string | null;
  register_items: number;
  review_required: number;
  total_inc_gst: number | null;
  approval_status: "blocked" | "ready_for_approval" | "approved" | null;
  created_by: string | null;
  created_at: string;
  updated_at: string;
}

export interface JobSummary {
  id: string;
  organisation_id: string;
  document_id: string;
  file_name: string;
  client_name: string | null;
  site_address: string | null;
  survey_type: string | null;
  status: JobStatus;
  quotable: boolean;
  review_required: number;
  total_inc_gst: number | null;
  created_at: string;
  updated_at: string;
}

export interface ProcessJobResult {
  job: Job;
  priced_quote: PricedQuoteResult | null;
}

export interface CreateJobPayload {
  file: File;
  client_name?: string;
  site_address?: string;
  job_reference?: string;
  created_by?: string;
}
