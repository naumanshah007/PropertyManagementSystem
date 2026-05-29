CREATE TABLE IF NOT EXISTS organisations (
  id TEXT PRIMARY KEY,
  name TEXT NOT NULL,
  slug TEXT NOT NULL UNIQUE,
  status TEXT NOT NULL DEFAULT 'active',
  created_at TEXT NOT NULL,
  updated_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS users (
  id TEXT PRIMARY KEY,
  email TEXT NOT NULL UNIQUE,
  name TEXT NOT NULL,
  password_hash TEXT,
  password_salt TEXT,
  created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS organisation_users (
  id TEXT PRIMARY KEY,
  organisation_id TEXT NOT NULL REFERENCES organisations(id),
  user_id TEXT NOT NULL REFERENCES users(id),
  email TEXT NOT NULL,
  name TEXT NOT NULL,
  role TEXT NOT NULL,
  status TEXT NOT NULL DEFAULT 'active',
  created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS organisation_settings (
  organisation_id TEXT PRIMARY KEY REFERENCES organisations(id),
  gst_rate REAL NOT NULL DEFAULT 0.15,
  default_margin REAL NOT NULL DEFAULT 0.20,
  default_currency TEXT NOT NULL DEFAULT 'NZD',
  quote_prefix TEXT NOT NULL DEFAULT 'TQ',
  require_review_for_class_a INTEGER NOT NULL DEFAULT 1,
  require_review_for_no_access INTEGER NOT NULL DEFAULT 1,
  updated_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS company_profiles (
  organisation_id TEXT PRIMARY KEY REFERENCES organisations(id),
  legal_name TEXT NOT NULL,
  trading_name TEXT NOT NULL,
  email TEXT,
  phone TEXT,
  website TEXT,
  address TEXT,
  logo_url TEXT,
  updated_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS pricebooks (
  id TEXT PRIMARY KEY,
  organisation_id TEXT NOT NULL REFERENCES organisations(id),
  name TEXT NOT NULL,
  version TEXT NOT NULL,
  active INTEGER NOT NULL DEFAULT 1,
  created_at TEXT NOT NULL,
  updated_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS pricebook_rules (
  id TEXT PRIMARY KEY,
  pricebook_id TEXT NOT NULL REFERENCES pricebooks(id),
  organisation_id TEXT NOT NULL REFERENCES organisations(id),
  name TEXT NOT NULL,
  category TEXT NOT NULL,
  section TEXT NOT NULL,
  material_match TEXT,
  class_match TEXT,
  access_match TEXT NOT NULL DEFAULT 'normal',
  pricing_method TEXT NOT NULL,
  unit TEXT NOT NULL,
  unit_rate REAL,
  risk_multiplier REAL NOT NULL DEFAULT 1.0,
  margin REAL NOT NULL DEFAULT 0.20,
  gst_taxable INTEGER NOT NULL DEFAULT 1,
  minimum_charge REAL,
  assumptions_json TEXT NOT NULL DEFAULT '[]',
  exclusions_json TEXT NOT NULL DEFAULT '[]',
  review_required INTEGER NOT NULL DEFAULT 1,
  mandatory INTEGER NOT NULL DEFAULT 0,
  active INTEGER NOT NULL DEFAULT 1
);

CREATE TABLE IF NOT EXISTS quote_templates (
  id TEXT PRIMARY KEY,
  organisation_id TEXT NOT NULL REFERENCES organisations(id),
  name TEXT NOT NULL,
  description TEXT NOT NULL,
  sections_json TEXT NOT NULL DEFAULT '[]',
  active INTEGER NOT NULL DEFAULT 1,
  created_at TEXT NOT NULL,
  updated_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS documents_metadata (
  id TEXT PRIMARY KEY,
  organisation_id TEXT NOT NULL REFERENCES organisations(id),
  workup_id TEXT,
  file_name TEXT NOT NULL,
  file_type TEXT NOT NULL,
  storage_key TEXT NOT NULL,
  page_count INTEGER,
  parser_version TEXT,
  ocr_status TEXT,
  created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS parsed_documents_metadata (
  document_id TEXT PRIMARY KEY REFERENCES documents_metadata(id),
  organisation_id TEXT NOT NULL REFERENCES organisations(id),
  parser_version TEXT NOT NULL,
  page_count INTEGER NOT NULL,
  parsed_json_storage_key TEXT NOT NULL,
  table_count INTEGER NOT NULL DEFAULT 0,
  ocr_status TEXT NOT NULL,
  created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS extracted_register_items (
  id TEXT PRIMARY KEY,
  document_id TEXT NOT NULL REFERENCES documents_metadata(id),
  organisation_id TEXT NOT NULL REFERENCES organisations(id),
  building TEXT,
  level TEXT,
  location TEXT NOT NULL,
  item TEXT NOT NULL,
  material TEXT NOT NULL,
  strategy_sample_id TEXT,
  extent_quantity REAL,
  extent_unit TEXT,
  fibre_type TEXT,
  friability_class TEXT NOT NULL,
  asbestos_result TEXT NOT NULL,
  access_status TEXT NOT NULL,
  material_score TEXT,
  priority_risk_category TEXT,
  recommendation TEXT,
  source_page INTEGER NOT NULL,
  confidence REAL NOT NULL,
  review_status TEXT NOT NULL,
  source_evidence_json TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS quote_candidates (
  id TEXT PRIMARY KEY,
  document_id TEXT NOT NULL REFERENCES documents_metadata(id),
  organisation_id TEXT NOT NULL REFERENCES organisations(id),
  section TEXT NOT NULL,
  description TEXT NOT NULL,
  quantity REAL,
  unit TEXT,
  source_register_item_ids_json TEXT NOT NULL,
  source_evidence_json TEXT NOT NULL,
  source_pages_json TEXT NOT NULL,
  confidence REAL NOT NULL,
  assumptions_json TEXT NOT NULL,
  exclusions_json TEXT NOT NULL,
  reason TEXT NOT NULL,
  review_status TEXT NOT NULL,
  review_required INTEGER NOT NULL,
  approval_status TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS priced_quote_lines (
  id TEXT PRIMARY KEY,
  document_id TEXT NOT NULL REFERENCES documents_metadata(id),
  organisation_id TEXT NOT NULL REFERENCES organisations(id),
  quote_candidate_id TEXT NOT NULL REFERENCES quote_candidates(id),
  section TEXT NOT NULL,
  description TEXT NOT NULL,
  quantity REAL,
  unit TEXT,
  unit_rate REAL,
  base_cost REAL,
  risk_multiplier REAL NOT NULL,
  margin REAL NOT NULL,
  subtotal_ex_gst REAL,
  gst REAL,
  total_inc_gst REAL,
  pricing_rule_id TEXT,
  pricing_rule_name TEXT,
  pricing_explanation TEXT NOT NULL,
  source_register_item_ids_json TEXT NOT NULL,
  source_evidence_json TEXT NOT NULL,
  source_pages_json TEXT NOT NULL,
  confidence REAL NOT NULL,
  assumptions_json TEXT NOT NULL,
  exclusions_json TEXT NOT NULL,
  review_status TEXT NOT NULL,
  review_required INTEGER NOT NULL,
  approval_status TEXT NOT NULL,
  excluded_from_pricing INTEGER NOT NULL DEFAULT 0
);

CREATE TABLE IF NOT EXISTS estimator_edits (
  id TEXT PRIMARY KEY,
  organisation_id TEXT NOT NULL REFERENCES organisations(id),
  workup_id TEXT NOT NULL,
  entity_type TEXT NOT NULL,
  entity_id TEXT NOT NULL,
  field_name TEXT NOT NULL,
  previous_value_json TEXT,
  new_value_json TEXT,
  reason TEXT NOT NULL,
  user_id TEXT NOT NULL,
  created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS audit_events (
  id TEXT PRIMARY KEY,
  organisation_id TEXT NOT NULL REFERENCES organisations(id),
  workup_id TEXT NOT NULL,
  actor_type TEXT NOT NULL,
  actor_id TEXT NOT NULL,
  event_type TEXT NOT NULL,
  payload_json TEXT NOT NULL,
  created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS export_packages (
  id TEXT PRIMARY KEY,
  organisation_id TEXT NOT NULL REFERENCES organisations(id),
  document_id TEXT NOT NULL REFERENCES documents_metadata(id),
  quote_number TEXT NOT NULL,
  client_name TEXT NOT NULL,
  project_name TEXT NOT NULL,
  site_address TEXT NOT NULL,
  html_storage_key TEXT NOT NULL,
  pdf_storage_key TEXT,
  pdf_download_path TEXT NOT NULL,
  subtotal_ex_gst REAL NOT NULL,
  gst REAL NOT NULL,
  total_inc_gst REAL NOT NULL,
  assumptions_json TEXT NOT NULL,
  exclusions_json TEXT NOT NULL,
  source_pages_json TEXT NOT NULL,
  generated_at TEXT NOT NULL
);
