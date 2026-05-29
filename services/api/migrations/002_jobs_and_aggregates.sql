-- Migration 002 — aggregate (document-in-SQL) tables used by the Turso
-- repository backend, plus the jobs table that postdates the 001 schema.
--
-- Each record type is stored as one row: indexed columns we actually query
-- (id, organisation_id, slug/version/active/status/email) + a `data_json`
-- column holding the full Pydantic model. This is durable + per-org queryable
-- without brittle column-by-column mapping, and resilient to model drift
-- (settings/LLM/boilerplate fields have already churned once). The normalised
-- 001 schema remains as the future target for a fully relational migration.

CREATE TABLE IF NOT EXISTS kv_organisations (
  id TEXT PRIMARY KEY,
  slug TEXT,
  data_json TEXT NOT NULL,
  updated_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS kv_org_settings (
  organisation_id TEXT PRIMARY KEY,
  data_json TEXT NOT NULL,
  updated_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS kv_company_profiles (
  organisation_id TEXT PRIMARY KEY,
  data_json TEXT NOT NULL,
  updated_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS kv_pricebooks (
  id TEXT PRIMARY KEY,
  organisation_id TEXT NOT NULL,
  version TEXT NOT NULL,
  active INTEGER NOT NULL DEFAULT 0,
  data_json TEXT NOT NULL,
  updated_at TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_kv_pricebooks_org ON kv_pricebooks (organisation_id);

CREATE TABLE IF NOT EXISTS kv_org_users (
  id TEXT PRIMARY KEY,
  organisation_id TEXT NOT NULL,
  email TEXT NOT NULL,
  data_json TEXT NOT NULL,
  created_at TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_kv_org_users_org ON kv_org_users (organisation_id);

CREATE TABLE IF NOT EXISTS kv_auth_users (
  id TEXT PRIMARY KEY,
  email TEXT NOT NULL UNIQUE,
  data_json TEXT NOT NULL,
  created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS kv_jobs (
  id TEXT PRIMARY KEY,
  organisation_id TEXT NOT NULL,
  status TEXT NOT NULL,
  data_json TEXT NOT NULL,
  created_at TEXT NOT NULL,
  updated_at TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_kv_jobs_org ON kv_jobs (organisation_id);
