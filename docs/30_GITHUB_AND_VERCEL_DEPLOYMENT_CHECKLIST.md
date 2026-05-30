# GitHub and Vercel Deployment Checklist

## Repository Safety

- [ ] `git status` reviewed.
- [ ] No secrets committed.
- [ ] `.env` and `.env.local` ignored.
- [ ] `.venv`, `node_modules`, `.next`, and build caches ignored.
- [ ] `services/api/storage/` ignored.
- [ ] Uploaded PDFs and exported PDFs ignored.
- [ ] Local JSON/file storage ignored.
- [ ] Turso tokens and R2 credentials ignored.
- [ ] Approved sample survey retained at `samples/surveys/38-Asbestos-Survey-_Rev_0.pdf`.
- [ ] Duplicate or sensitive client PDFs outside approved sample paths are not committed.

## Environment Files

- [ ] `apps/web/.env.example` exists.
- [ ] `services/api/.env.example` exists.
- [ ] No real `.env` files are committed.

Frontend env:

```text
NEXT_PUBLIC_API_BASE_URL=http://127.0.0.1:8000
NEXT_PUBLIC_APP_DOMAIN=quote.privexa.co
NEXT_PUBLIC_APP_NAME=TraceQuote AI
```

Backend env:

```text
APP_ENV=local
APP_BASE_URL=http://127.0.0.1:8000
FRONTEND_URL=http://localhost:3000
CORS_ALLOWED_ORIGINS=http://localhost:3000,https://quote.privexa.co
DATABASE_PROVIDER=json
FILE_STORAGE_PROVIDER=local
DEMO_SEED_ENABLED=true
```

## Verification

- [ ] Backend tests pass.
- [ ] Frontend typecheck passes.
- [ ] Frontend build passes.
- [ ] Demo reset script passes.

Commands:

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

## GitHub Push

From a fresh local repository:

```bash
git init
git add .
git status
git commit -m "Prepare TraceQuote AI for Vercel frontend deployment"
git branch -M main
git remote add origin https://github.com/<your-org-or-user>/<repo-name>.git
git push -u origin main
```

If the repository already exists locally:

```bash
git add .
git status
git commit -m "Prepare TraceQuote AI for Vercel frontend deployment"
git push
```

## Vercel Frontend Import

Import the GitHub repository into Vercel with:

```text
Framework Preset: Next.js
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

## quote.privexa.co DNS

Recommended DNS record:

```text
Type: CNAME
Name: quote
Target: cname.vercel-dns.com
```

Then add `quote.privexa.co` in the Vercel project domain settings and wait for SSL provisioning.

## Backend Requirement

- [ ] FastAPI backend deployed separately on Render, Fly, Railway, or VPS.
- [ ] Backend `/health` endpoint returns `ok`.
- [ ] Backend CORS allows `https://quote.privexa.co`.
- [ ] Vercel `NEXT_PUBLIC_API_BASE_URL` points to the deployed backend.

The frontend can deploy before the backend, but upload, extraction, pricing, review, and export workflows require a reachable backend API.

## Remaining Before Public Launch

- [ ] For a public launch, replace demo auth with production auth. For a controlled demo, set strong `AUTH_SECRET`, `DEMO_ADMIN_PASSWORD`, and `DEMO_ORG_ADMIN_PASSWORD` secrets.
- [ ] Deploy with `DATABASE_PROVIDER=turso` and the Turso secrets from doc 31.
- [ ] Deploy with `FILE_STORAGE_PROVIDER=r2` and the Cloudflare R2 secrets from doc 31.
- [ ] Add API rate limits.
- [ ] Add production monitoring and backup policy.
