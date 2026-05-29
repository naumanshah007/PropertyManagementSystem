# Phase 11 Live Deployment Prep Report

## Scope

Phase 11 prepares TraceQuote AI for a low-cost live demo deployment at `quote.privexa.co` while preserving local JSON/file development mode.

This phase does not add ML, LLM quote writing, billing, Fergus integration, or production authentication.

## Environment Configuration

Added backend configuration for:

- `APP_ENV`
- `APP_BASE_URL`
- `FRONTEND_URL`
- `CORS_ALLOWED_ORIGINS`
- `DATABASE_PROVIDER`
- `TURSO_DATABASE_URL`
- `TURSO_AUTH_TOKEN`
- `FILE_STORAGE_PROVIDER`
- `R2_ACCOUNT_ID`
- `R2_ACCESS_KEY_ID`
- `R2_SECRET_ACCESS_KEY`
- `R2_BUCKET_NAME`
- `R2_PUBLIC_BASE_URL`
- `DEMO_SEED_ENABLED`
- `DEMO_ADMIN_EMAIL`
- `DEMO_ADMIN_PASSWORD`
- `DEMO_ORG_ADMIN_EMAIL`
- `DEMO_ORG_ADMIN_PASSWORD`

Added frontend configuration for:

- `NEXT_PUBLIC_API_BASE_URL`
- `NEXT_PUBLIC_APP_DOMAIN`
- `NEXT_PUBLIC_APP_NAME`

## Persistence Preparation

The app still runs in JSON mode by default. A migration-ready Turso/libSQL schema has been added under `services/api/migrations`.

Tables covered:

- organisations
- users
- organisation_users
- organisation_settings
- company_profiles
- pricebooks
- pricebook_rules
- quote_templates
- documents_metadata
- parsed_documents_metadata
- extracted_register_items
- quote_candidates
- priced_quote_lines
- estimator_edits
- audit_events
- export_packages

Actual PDF bytes and generated PDFs are not intended for Turso. The schema stores metadata and storage keys only.

## Migration Tooling

Added:

- `scripts/db_migrate.py`
- `scripts/db_seed_demo.py`

`db_migrate.py --dry-run` validates SQL locally with SQLite. If `DATABASE_PROVIDER=turso` and Turso env vars plus `libsql-client` are available, the script can run migrations against Turso.

## File Storage

Added a storage abstraction with:

- `save_upload`
- `read_upload`
- `save_export`
- `get_download_url`
- `delete_file`

Implemented:

- Local filesystem adapter

Prepared:

- Cloudflare R2 adapter skeleton with explicit configuration errors until R2 credentials and client dependency are added.

## CORS and Domain

Backend CORS now allows:

- `http://localhost:3000`
- `http://127.0.0.1:3000`
- `https://quote.privexa.co`
- additional origins from `CORS_ALLOWED_ORIGINS`

## Deployment Files

Added:

- `apps/web/vercel.json`
- `apps/web/.env.example`
- `services/api/.env.example`
- `services/api/Dockerfile`
- `services/api/render.yaml`

## Security Hardening

- Demo seed endpoint is blocked when `DEMO_SEED_ENABLED=false`.
- Demo password defaults are local-only.
- Staging/production should set demo passwords explicitly if demo auth remains enabled.
- Production startup logs a warning that demo auth is still a controlled-pilot mechanism.
- Passwords remain salted and hashed.

## Verification Added

Backend tests cover:

- JSON storage remains default.
- Turso migration path reports missing config clearly.
- Migration SQL validates.
- Demo seed is blocked when disabled.
- CORS allows `quote.privexa.co`.
- Local file storage save/read/delete works.
- Production config does not default to localhost.

## Known Limitations

- Runtime repositories still use JSON/file storage in this phase.
- Turso schema and migration tooling are ready, but full repository implementations are a later phase.
- R2 adapter is intentionally a skeleton until dependency and credentials are configured.
- Demo auth remains a temporary controlled-demo mechanism.
- File storage keys are ready for R2-style storage, but export upload to R2 is not active yet.
