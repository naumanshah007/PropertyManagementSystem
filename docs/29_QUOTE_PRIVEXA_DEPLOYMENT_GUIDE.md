# quote.privexa.co Deployment Guide

## Target Architecture

Early-stage live demo:

- Frontend: Vercel
- Backend: FastAPI on Render, Fly, Railway, or VPS
- Database: JSON mode for first private demo, Turso/libSQL migration-ready
- File storage: local backend disk for first private demo, Cloudflare R2 planned
- Domain: `quote.privexa.co`

Later paid-pilot path:

- AWS ECS
- RDS PostgreSQL
- S3
- CloudFront

## DNS

Recommended DNS for `quote.privexa.co`:

- Type: `CNAME`
- Name: `quote`
- Target: Vercel project CNAME, usually `cname.vercel-dns.com`

If using Cloudflare DNS, keep proxying disabled until Vercel verifies the domain cleanly, then enable proxying only if the Vercel setup supports it.

## Frontend Deployment on Vercel

Project root:

```text
apps/web
```

Build command:

```bash
npm run build
```

Install command:

```bash
npm install
```

Environment variables:

```text
NEXT_PUBLIC_API_BASE_URL=https://<backend-host>
NEXT_PUBLIC_APP_DOMAIN=quote.privexa.co
NEXT_PUBLIC_APP_NAME=TraceQuote AI
```

After deployment:

1. Add `quote.privexa.co` to the Vercel project domains.
2. Add the DNS CNAME.
3. Wait for Vercel SSL provisioning.
4. Open `https://quote.privexa.co/login`.

## Backend Hosting

Use the Dockerfile at:

```text
services/api/Dockerfile
```

Production start command:

```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

Health check:

```text
/health
```

Render starter configuration is included at:

```text
services/api/render.yaml
```

Backend environment variables:

```text
APP_ENV=staging
APP_BASE_URL=https://<backend-host>
FRONTEND_URL=https://quote.privexa.co
CORS_ALLOWED_ORIGINS=https://quote.privexa.co
DATABASE_PROVIDER=json
FILE_STORAGE_PROVIDER=local
DEMO_SEED_ENABLED=false
```

For a controlled demo where seeded demo users are required:

```text
DEMO_SEED_ENABLED=true
DEMO_ADMIN_EMAIL=admin@privexa.co
DEMO_ADMIN_PASSWORD=<strong temporary password>
DEMO_ORG_ADMIN_EMAIL=test@privexa.co
DEMO_ORG_ADMIN_PASSWORD=<strong temporary password>
```

## Turso Setup

Install Turso CLI and create a database:

```bash
turso db create tracequote-staging
turso db show tracequote-staging --url
turso db tokens create tracequote-staging
```

Set backend env:

```text
DATABASE_PROVIDER=turso
TURSO_DATABASE_URL=<libsql-url>
TURSO_AUTH_TOKEN=<token>
```

Validate migrations locally:

```bash
python3 scripts/db_migrate.py --dry-run
```

Run migration when `libsql-client` and Turso env vars are available:

```bash
DATABASE_PROVIDER=turso python3 scripts/db_migrate.py
```

Current note: Phase 11 provides schema and migration readiness. Runtime repositories still use JSON mode until the Turso repository implementation is completed.

## Cloudflare R2 Setup Plan

Create:

- R2 bucket: `tracequote-ai`
- Access key with object read/write permissions
- Optional public/custom domain for exported PDFs

Backend env:

```text
FILE_STORAGE_PROVIDER=r2
R2_ACCOUNT_ID=<account-id>
R2_ACCESS_KEY_ID=<access-key-id>
R2_SECRET_ACCESS_KEY=<secret>
R2_BUCKET_NAME=tracequote-ai
R2_PUBLIC_BASE_URL=https://<r2-public-domain>
```

Current note: Phase 11 includes the storage interface and R2 skeleton. Add an S3-compatible client dependency before enabling R2 for real uploads.

## Local Mode

Backend:

```bash
cd services/api
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

Frontend:

```bash
cd apps/web
npm install
npm run dev
```

Local env:

```text
DATABASE_PROVIDER=json
FILE_STORAGE_PROVIDER=local
DEMO_SEED_ENABLED=true
NEXT_PUBLIC_API_BASE_URL=http://127.0.0.1:8000
```

## Seed Commands

Seed only demo users, organisation, settings, and pricebook:

```bash
python3 scripts/db_seed_demo.py
```

Reset the full Tauraroa demo workflow:

```bash
python3 scripts/demo_reset.py
```

## Smoke Test Checklist

1. Open `https://quote.privexa.co/login`.
2. Log in as the controlled demo admin.
3. Confirm platform admin or organisation admin route loads.
4. Open the demo organisation pricebook.
5. Confirm active rules are visible.
6. Upload the Tauraroa asbestos survey.
7. Parse document and confirm 50 pages.
8. Extract register items.
9. Generate quote candidates.
10. Apply pricing.
11. Resolve review gates.
12. Export quote package.
13. Download the generated PDF.
14. Confirm `/health` returns `ok`.

## Pre-Public Launch Remaining Work

- Replace demo auth with production auth.
- Complete Turso runtime repositories.
- Complete R2 upload/download adapter.
- Add server-side role enforcement.
- Add persistent audit-event guarantees.
- Add backup and retention policy.
- Add production error monitoring.
- Add rate limits and upload-size limits.
