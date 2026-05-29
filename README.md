# TraceQuote AI

Enterprise AI estimator workbench for regulated site-services businesses.

TraceQuote AI converts asbestos, demolition, remediation, and hazardous-cleaning reports into traceable, human-reviewed quote drafts. The first vertical is asbestos removal and demolition quoting.

## Product Positioning

Traceable AI quoting for regulated site services.

TraceQuote AI is not a final-price predictor. It is a governed survey-to-quote workbench where every quote line must be linked to:

- Source evidence and page references
- Extraction confidence
- Pricing logic
- Similar historical quote references where available
- Assumptions and exclusions
- Human review and approval status
- Audit history

## MVP Goal

Build a vendor-demo-ready product that can upload the provided asbestos survey, extract register items, flag no-access and Class A/Class B risks, generate editable quote lines, record estimator edits, and export a professional quote draft.

## Repository Layout

```text
docs/                         Product and engineering specifications
apps/web/                     Next.js frontend
services/api/                 FastAPI backend
services/worker/              Document parsing and extraction jobs
packages/schemas/             Shared schemas and contracts
packages/pricing-engine/      Rule-based pricebook and quote logic
packages/extraction-engine/   Document intelligence helpers
packages/audit-engine/        Append-only audit/event helpers
samples/                      Surveys, historical quotes, expected outputs
tests/                        Golden, integration, and e2e tests
```

## Build Method

This product should be developed spec-first:

1. Keep the constitution and feature specs current.
2. Implement one feature slice at a time.
3. Add tests around extraction, pricing, review gates, and exports.
4. Run verification before moving to the next feature.
5. Treat estimator edits as structured learning data, not as invisible feedback.

## Phase 1 Local Run

### Backend

```bash
cd services/api
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

Backend endpoints:

- `GET http://localhost:8000/health`
- `GET http://localhost:8000/workups`
- `GET http://localhost:8000/workups/tw-tauraroa-school-001`
- `GET http://localhost:8000/workups/tw-tauraroa-school-001/register-items`
- `GET http://localhost:8000/workups/tw-tauraroa-school-001/quote-lines`
- `GET http://localhost:8000/workups/tw-tauraroa-school-001/audit-events`
- `POST http://localhost:8000/documents/upload`
- `GET http://localhost:8000/documents/{document_id}`
- `GET http://localhost:8000/documents/{document_id}/pages`
- OpenAPI: `http://localhost:8000/docs`

### Frontend

```bash
cd apps/web
npm install
npm run dev
```

Frontend URL:

```text
http://localhost:3000
```

### Checks

```bash
cd services/api
PYTHONPATH=. pytest

cd ../../apps/web
npm run typecheck
npm run build
```

## Phase 1 Scope

Implemented as a deterministic local product shell:

- Next.js + TypeScript + Tailwind frontend
- FastAPI backend with OpenAPI
- Pydantic backend contracts
- Mirrored TypeScript frontend contracts
- Demo workup for Tauraroa Area School asbestos demolition survey
- Evidence-linked register items and quote lines
- Review-required Class A, no-access, and presumed asbestos states
- Export blocked until human review gates are complete

Not implemented in Phase 1:

- Full PDF parsing
- ML or LLM extraction
- Billing
- Multi-tenancy
- Fergus integration
- Production authentication

## Phase 2 Document Ingestion

Phase 2 adds deterministic local PDF ingestion for POC use:

- Uploaded PDFs are stored under `services/api/storage/documents/`.
- PyMuPDF extracts page-level text.
- pdfplumber extracts tables where possible.
- Parsed JSON is written beside the uploaded file as `parsed.json`.
- OCR is not implemented; empty-text PDFs are marked `required_later`.
- No LLM extraction, asbestos register extraction, or pricing engine is implemented in this phase.

The frontend upload controls are available on:

- `/workups/new`
- `/workups/tw-tauraroa-school-001`

Parsed text/table preview is available on:

- `/workups/tw-tauraroa-school-001/evidence`

### Golden Survey Test

Place the real survey PDF at:

```text
samples/surveys/38-Asbestos-Survey-_Rev_0.pdf
```

Then run:

```bash
cd services/api
source .venv/bin/activate
PYTHONPATH=. pytest tests/test_documents.py::test_golden_asbestos_survey_parses_expected_text
```

The golden test is skipped only when that exact PDF is missing.

## Phase 3 Register Extraction

Phase 3 adds deterministic asbestos register extraction on top of parsed Phase 2 documents:

- `POST http://localhost:8000/documents/{document_id}/extract-register`
- `GET http://localhost:8000/documents/{document_id}/register-items`

The extractor does not use an LLM. It uses parsed text/tables, rule-based keyword matching, expected source-page anchors for the target survey, and review-status rules.

The Document Intelligence screen can run extraction for an uploaded workup document and will replace the static demo register table with extracted register rows when available.

## Phase 4 Quote Candidate Mapping

Phase 4 maps extracted register items into reviewable quote-draft candidates without generating prices:

- `POST http://localhost:8000/documents/{document_id}/generate-quote-candidates`
- `GET http://localhost:8000/documents/{document_id}/quote-candidates`

Candidate sections:

- Site Establishment
- Class B Removal
- Class A / Friable Removal
- Provisional / No Access
- Waste / Disposal Placeholder
- Excluded / NAD Findings

Every candidate preserves source register item IDs, source evidence text, source pages, assumptions, exclusions, confidence, reason, review status, and `approval_status: not_ready`.

## Phase 4.5 Document AI Benchmark

Phase 4.5 adds parser adapters and a benchmark script for comparing document parsing options before pricing/export work:

- Current PyMuPDF + pdfplumber parser
- Docling
- Marker
- PaddleOCR
- Surya OCR
- Camelot
- Qwen2.5-VL placeholder

Optional parser libraries are not installed by default. The benchmark skips unavailable adapters with a clear reason and keeps the existing `/documents/upload` parser unchanged.

Place the real survey PDF at:

```text
samples/surveys/38-Asbestos-Survey-_Rev_0.pdf
```

Run the benchmark from the repository root:

```bash
cd services/api
source .venv/bin/activate
cd ../..
python3 scripts/benchmark_parsers.py
```

If the sample PDF is missing, the script fails with an instruction to add it first.

## Phase 5 Pricing Engine

Phase 5 applies deterministic seed pricebook rules to generated quote candidates:

- `POST http://localhost:8000/documents/{document_id}/price-quote-candidates`
- `GET http://localhost:8000/documents/{document_id}/priced-quote-lines`

The pricing engine creates reviewable draft quote lines with quantity, unit rate, base cost, risk multiplier, margin, subtotal ex GST, GST, total inc GST, assumptions, exclusions, source evidence, and approval status.

No line is approved by default. The priced quote result remains blocked until human estimator review.

## Phase 6 Review and Approval Gates

Phase 6 adds estimator edits, review resolution, and approval-readiness checks:

- `POST http://localhost:8000/documents/{document_id}/priced-quote-lines/{line_id}/edit`
- `POST http://localhost:8000/documents/{document_id}/priced-quote-lines/{line_id}/resolve-review`
- `GET http://localhost:8000/documents/{document_id}/approval-readiness`

Editable priced-line fields are quantity, unit rate, risk multiplier, and margin. Every edit requires a reason and records an estimator edit. Review-required lines must be resolved with accepted assumptions/exclusions before the quote can become ready for approval.

## Phase 7 Quote Export

Phase 7 generates a gated client-facing quote package from reviewed priced quote lines:

- `POST http://localhost:8000/documents/{document_id}/export-quote`
- `GET http://localhost:8000/documents/{document_id}/export-quote`

Export is blocked until approval-readiness passes. Generated HTML, PDF, and metadata files are stored under:

```text
services/api/storage/documents/{document_id}/exports/
```

The generated package includes quote lines, totals, assumptions, exclusions, review statement, source evidence appendix, and an asbestos-qualified-personnel disclaimer.

## Phase 8 Multi-Organisation SaaS Foundation

Phase 8 adds organisation boundaries and admin screens while keeping the demo workflow compatible through `org-demo-tracequote`.

SaaS endpoints:

- `POST http://localhost:8000/organisations`
- `GET http://localhost:8000/organisations`
- `GET http://localhost:8000/organisations/{org_id}`
- `POST http://localhost:8000/organisations/{org_id}/users`
- `GET http://localhost:8000/organisations/{org_id}/users`
- `POST http://localhost:8000/organisations/{org_id}/pricebooks`
- `GET http://localhost:8000/organisations/{org_id}/pricebooks`
- `POST http://localhost:8000/organisations/{org_id}/settings`
- `GET http://localhost:8000/organisations/{org_id}/settings`
- `POST http://localhost:8000/organisations/{org_id}/documents/upload`
- `GET http://localhost:8000/organisations/{org_id}/documents/{document_id}`

Local storage is now organised under:

```text
services/api/storage/organisations/{org_id}/
```

Frontend admin routes:

- `/admin`
- `/admin/organisations`
- `/admin/organisations/new`
- `/admin/organisations/org-demo-tracequote/settings`
- `/admin/organisations/org-demo-tracequote/users`
- `/admin/organisations/org-demo-tracequote/pricebook`
- `/admin/organisations/org-demo-tracequote/profile`

## Phase 9 Demo Authentication and Seeded Organisation

Phase 9 adds local-only demo authentication and a seeded asbestos services organisation for vendor walkthroughs. This is not production auth.

Demo accounts:

- Super admin: `admin@privexa.co` / `admin123`
- Test org admin: `test@privexa.co` / `admin123`

Passwords are stored as salted PBKDF2 hashes in local demo storage, not as plain text. Login routes redirect by role:

- `platform_admin` -> `/admin`
- `organisation_admin` -> `/org`
- `estimator` / `reviewer` -> `/workups`

Seed or reset demo data:

```bash
source services/api/.venv/bin/activate
python3 scripts/demo_reset.py
```

Seed only users, organisation, settings, and pricebook:

```bash
source services/api/.venv/bin/activate
python3 scripts/seed_demo_users.py
```

Seeded organisation:

- `Demo Asbestos Services Ltd`
- GST: `15%`
- Default margin: `20%`
- Currency: `NZD`
- Branding placeholder: `TraceQuote Demo`

Phase 9 also adds the Document Intelligence “Extracted Intelligence” panel, which summarizes parsed pages, register rows, quote candidates, priced lines, access risks, friability classes, extracted quantities, source pages, confidence, pricing triggers, assumptions, and exclusions.

## Phase 10 Editable Organisation Pricebooks

Phase 10 lets organisation admins manage company-owned pricebook rules from:

```text
/admin/organisations/{org_id}/pricebook
```

Pricebook endpoints:

- `GET http://localhost:8000/organisations/{org_id}/pricebooks/{pricebook_id}`
- `POST http://localhost:8000/organisations/{org_id}/pricebooks/{pricebook_id}/rules`
- `PATCH http://localhost:8000/organisations/{org_id}/pricebooks/{pricebook_id}/rules/{rule_id}`
- `DELETE http://localhost:8000/organisations/{org_id}/pricebooks/{pricebook_id}/rules/{rule_id}`
- `POST http://localhost:8000/organisations/{org_id}/pricebooks/{pricebook_id}/activate`

Rules support category/material/class/access matching, fixed/per-sqm/per-piece/per-hour/excluded pricing, GST taxable flags, minimum charges, assumptions, exclusions, review-required status, and active/mandatory states.

The deterministic pricing engine now uses the active organisation pricebook when present and falls back to the seed pricebook when no organisation pricebook exists.

## Phase 11 Live Deployment Preparation

Phase 11 prepares the app for a low-cost live deployment at `quote.privexa.co`.

Frontend env:

- `NEXT_PUBLIC_API_BASE_URL`
- `NEXT_PUBLIC_APP_DOMAIN`
- `NEXT_PUBLIC_APP_NAME`

Backend env:

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
- `AUTH_SECRET` (required in production — signs access tokens; app refuses to start without it)
- `ACCESS_TOKEN_EXPIRE_MINUTES` (default 480)
- `DEMO_SEED_ENABLED` (gates `/demo/seed` and `/demo/users`; set `false` to lock down)
- `DEMO_ADMIN_EMAIL` / `DEMO_ADMIN_PASSWORD`
- `DEMO_ORG_ADMIN_EMAIL` / `DEMO_ORG_ADMIN_PASSWORD`

Auth & RBAC details: `docs/AUTH_RBAC_HARDENING_REPORT.md`.

Deployment prep files:

- `apps/web/vercel.json`
- `apps/web/.env.example`
- `services/api/.env.example`
- `services/api/Dockerfile`
- `services/api/render.yaml`
- `services/api/migrations/001_initial_live_ready_schema.sql`
- `scripts/db_migrate.py`
- `scripts/db_seed_demo.py`

Migration dry run:

```bash
python3 scripts/db_migrate.py --dry-run
```

Deployment guide:

```text
docs/29_QUOTE_PRIVEXA_DEPLOYMENT_GUIDE.md
```

## GitHub and Vercel Deployment

This repository is prepared for GitHub push and Vercel frontend deployment. The FastAPI backend must be deployed separately; do not deploy `services/api` to Vercel.

Local verification:

```bash
cd services/api
source .venv/bin/activate
PYTHONPATH=. pytest

cd ../../apps/web
npm run typecheck
npm run build

cd ../..
source services/api/.venv/bin/activate
python3 scripts/demo_reset.py
```

GitHub push from a fresh local repository:

```bash
git init
git add .
git status
git commit -m "Prepare TraceQuote AI for Vercel frontend deployment"
git branch -M main
git remote add origin https://github.com/<your-org-or-user>/<repo-name>.git
git push -u origin main
```

Before committing, confirm `git status` does not include:

- `.env` or `.env.local`
- `.venv`
- `node_modules`
- `.next`
- `services/api/storage/`
- uploaded PDFs
- exported PDFs
- local JSON storage
- Turso tokens
- R2 credentials

Vercel frontend import settings:

```text
Root Directory: apps/web
Install Command: npm install
Build Command: npm run build
Output Directory: .next
```

Vercel environment variables:

```text
NEXT_PUBLIC_API_BASE_URL=https://<backend-host>
NEXT_PUBLIC_APP_DOMAIN=quote.privexa.co
NEXT_PUBLIC_APP_NAME=TraceQuote AI
```

Custom domain:

```text
quote -> cname.vercel-dns.com
```

Add `quote.privexa.co` in Vercel project domains, then create the DNS CNAME at the DNS provider.

Backend hosting note:

- Host FastAPI separately on Render, Fly, Railway, or a VPS.
- Set `FRONTEND_URL=https://quote.privexa.co`.
- Set `CORS_ALLOWED_ORIGINS=https://quote.privexa.co`.
- Use `/health` as the backend health check.
- The live frontend workflow needs `NEXT_PUBLIC_API_BASE_URL` pointed at that backend URL.

## Vendor Demo Checklist

Use the real Tauraroa survey at:

```text
samples/surveys/38-Asbestos-Survey-_Rev_0.pdf
```

Reset and prebuild a ready demo package:

```bash
source services/api/.venv/bin/activate
python3 scripts/demo_reset.py
```

Manual demo flow:

1. Start the backend and frontend.
2. Open `http://localhost:3000`.
3. Upload `samples/surveys/38-Asbestos-Survey-_Rev_0.pdf`.
4. Open Document Intelligence and run register extraction.
5. Open Quote Builder and generate quote candidates.
6. Apply the seed pricebook.
7. Edit one priced line with a reason.
8. Resolve review gates with assumptions/exclusions accepted.
9. Open Review & Export.
10. Enter client/project/site details.
11. Generate the quote package.
12. Download the generated PDF.

Backend demo PDF endpoint after reset:

```text
http://127.0.0.1:8000/documents/demo-tauraroa-vendor/export-quote/pdf
```
