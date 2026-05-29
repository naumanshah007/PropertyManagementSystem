# Production Persistence + Go-Live Runbook (quote.privexa.co)

This supersedes the storage notes in docs 28–30. It covers the Turso + R2
persistence wiring and the exact steps to deploy. **I prepare the code,
configs, and commands; the external account steps (GitHub repo, Vercel, Render,
Turso, Cloudflare, DNS) are yours — they require your credentials.**

## What changed (persistence)

- **Atomic writes** — all JSON writes go through `app/storage_paths.atomic_write_text` (temp + `os.replace`), so a crash can't corrupt a record.
- **`DATA_DIR`** — `STORAGE_ROOT` honours `DATA_DIR`; point it at a mounted disk so local artifacts survive redeploys.
- **Repository abstraction** (`app/repository.py`) — structured records (orgs, settings, profiles, pricebooks, org users, auth users, **jobs**) go through `get_repository()`. Two backends, chosen by `DATABASE_PROVIDER`:
  - `json` (default) — original on-disk layout under `DATA_DIR`.
  - `turso` — libsql/SQLite aggregate rows (migration `002_jobs_and_aggregates.sql`). Schema auto-applies on first use; demo org/users seed on first login when `DEMO_SEED_ENABLED=true`.
- **R2** (`app/file_storage.py::R2FileStorage`, boto3) — `FILE_STORAGE_PROVIDER=r2` pushes the client-facing export PDF/HTML to R2 and serves a presigned/public URL (the `/export-quote/pdf` endpoint redirects). Intermediate JSON artifacts stay on the `DATA_DIR` disk (durable there).
- Both backends default to `json`/`local`, so local dev + the 172 backend tests are unchanged. `libsql-client` + `boto3` are lazy imports — only needed when their backend is enabled.

## Environment variables

| Var | Where | Value / note |
|---|---|---|
| `APP_ENV` | render.yaml | `staging` (controlled demo) |
| `FRONTEND_URL`, `CORS_ALLOWED_ORIGINS` | render.yaml | `https://quote.privexa.co` |
| `DATA_DIR` | render.yaml | `/data` (mounted disk) |
| `DATABASE_PROVIDER` | render.yaml | `turso` (or `json` to use the disk) |
| `FILE_STORAGE_PROVIDER` | render.yaml | `r2` (or `local` to use the disk) |
| `DEMO_SEED_ENABLED` | render.yaml | `true` for the demo; `false` to lock down |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | render.yaml | `480` |
| `AUTH_SECRET` | **Render secret** | strong random string (required) |
| `DEMO_ADMIN_PASSWORD`, `DEMO_ORG_ADMIN_PASSWORD` | **Render secrets** | demo logins |
| `TURSO_DATABASE_URL`, `TURSO_AUTH_TOKEN` | **Render secrets** | from `turso db show` / `turso db tokens create` |
| `R2_ACCOUNT_ID`, `R2_ACCESS_KEY_ID`, `R2_SECRET_ACCESS_KEY`, `R2_BUCKET_NAME` | **Render secrets** | from Cloudflare R2 |
| `R2_PUBLIC_BASE_URL` | Render secret (optional) | public bucket URL; presigned URLs used if unset |
| `NEXT_PUBLIC_API_BASE_URL` | **Vercel env** | the Render API URL (e.g. `https://tracequote-api.onrender.com`) |
| `NEXT_PUBLIC_APP_NAME` | Vercel env (optional) | `TraceQuote AI` |

## Go-live steps

### 1. GitHub (I init + commit; you create the repo + push)
```bash
# (already run for you) git init && git add -A && git commit -m "…"
# you:
gh repo create privexa/tracequote --private --source=. --remote=origin   # or create in the GitHub UI
git branch -M main
git remote add origin git@github.com:<you>/tracequote.git
git push -u origin main
```

### 2. Turso (database)
```bash
turso db create tracequote
turso db show tracequote          # → TURSO_DATABASE_URL (libsql://…)
turso db tokens create tracequote # → TURSO_AUTH_TOKEN
```
Schema auto-applies on first API call — no manual migration needed.

### 3. Cloudflare R2 (exports)
Create a bucket (e.g. `tracequote-exports`) + an R2 API token (account id, access key, secret). Optionally enable a public base URL.

### 4. Backend (Render)
- New → Blueprint → point at the repo (uses `services/api/render.yaml`).
- Set the **secret** env vars from the table above in the dashboard.
- Deploy. Confirm `GET /health` → 200 and `POST /auth/login` works.

### 5. Frontend (Vercel)
- Import the repo, root `apps/web`.
- Set `NEXT_PUBLIC_API_BASE_URL` to the Render API URL.
- Deploy.

### 6. DNS (quote.privexa.co)
- In Vercel, add the domain `quote.privexa.co`; Vercel shows the exact record.
- At your DNS provider, add the record Vercel specifies (typically a `CNAME` `quote → cname.vercel-dns.com`, or an `A`/`ALIAS` for an apex).
- Once propagated, the SPA is live and talks to the Render API.

## Verification (already passing locally)
- Backend: `cd services/api && APP_ENV=local PYTHONPATH=. pytest` → **172 passed** (incl. `test_turso_repository.py`, `test_r2_storage.py`).
- Frontend: `npm run typecheck` + `npm run build` → clean.
- Turso path proven against a local libsql file; R2 logic unit-tested. Live Turso/R2 validated post-deploy with your credentials.

## Follow-ups (optional)
- Route the intermediate JSON artifacts (parsed/register/candidates/priced) through R2 too (currently on the `DATA_DIR` disk — durable there). The `file_storage` abstraction already supports it.
- Normalise the Turso aggregate rows into the relational `001` schema if you want SQL-level reporting.
