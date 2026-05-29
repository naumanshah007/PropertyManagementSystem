# Auth Hardening & RBAC Enforcement Report

**Scope:** Replace unverifiable demo tokens with signed, expiring access tokens and enforce role/organisation access on the API. Suitable for a controlled hosted demo on `quote.privexa.co`. No billing, no new product features, no PDF viewer. Demo seed users are retained but made safe.

---

## 1. Token model

Access tokens are **HS256 JWTs** signed with `AUTH_SECRET`, implemented with the standard library (no external JWT dependency) in `services/api/app/auth_tokens.py`.

Claims:

| Claim | Meaning |
|-------|---------|
| `sub` | user_id |
| `email` | user email |
| `role` | `platform_admin` \| `organisation_admin` \| `estimator` \| `reviewer` \| `viewer` |
| `org` | organisation_id (null for platform admins) |
| `iat` / `exp` | issued-at / expiry (from `ACCESS_TOKEN_EXPIRE_MINUTES`, default 480) |

`POST /auth/login` (in `demo_auth.py`) verifies the PBKDF2-hashed demo password and issues a real signed token. Tokens are **stateless** — verified by signature + expiry on every request; tampering or expiry yields 401.

## 2. Auth dependencies (`services/api/app/auth.py`)

| Dependency | Rule |
|-----------|------|
| `get_current_user` | Decodes `Authorization: Bearer <jwt>`; 401 if missing/invalid/expired |
| `require_platform_admin` | role == `platform_admin`, else 403 |
| `require_org_access(org_id)` | platform_admin, or `token.org == org_id`; else 403 |
| `require_org_role(*roles)(org_id)` | platform_admin, or (same-org **and** role ∈ roles); else 403 |
| `require_document_access(document_id)` | resolves the document's owning org, then same rule as org_access |
| `require_document_role(*roles)(document_id)` | document org + role check (mutations) |
| `require_role(*roles)` | role check with no org binding (legacy global upload) |

Platform admins bypass org/role checks. `viewer` can read but is excluded from `MUTATING_ROLES = (estimator, reviewer, organisation_admin)`.

## 3. Endpoint protection matrix (`services/api/app/main.py`)

| Endpoint group | Guard |
|---|---|
| `POST/GET /organisations` (create / list-all) | `require_platform_admin` |
| `GET /organisations/{org}` | `require_org_access` |
| `GET/POST /organisations/{org}/jobs`, `GET .../jobs/{id}` | `require_org_access` (read) |
| `POST .../jobs`, `/process`, `/approve`, `/export`, org `documents/upload` | `require_org_role(*MUTATING_ROLES)` |
| `*/users`, `*/pricebooks*`, `*/settings`, `*/llm-config*` | `require_org_role("organisation_admin")` |
| `GET /documents/{id}/*` (reads) | `require_document_access` |
| `POST /documents/{id}/*` (extract, candidates, price, edit, resolve-review, export) | `require_document_role(*MUTATING_ROLES)` |
| `/workups*` (legacy demo) | `get_current_user` |
| `POST /documents/upload` (legacy global) | `require_role(*MUTATING_ROLES)` |
| `POST /demo/seed`, `GET /demo/users` | `DEMO_SEED_ENABLED` gate (+ `/demo/users` local-only) |

## 4. Cross-organisation isolation

A token's `org` claim is the tenant binding. `require_org_access` / `require_org_role` reject any request whose path org ≠ token org (unless platform_admin). Document endpoints resolve the document's owning org via `resolve_document_organisation_id` and apply the same rule — so a user from org B **cannot** read or mutate org A's documents, jobs, pricebooks, or exports. Proven by `test_auth_rbac.py::test_cross_org_document_access_is_blocked` and `test_org_admin_cannot_access_another_org`.

## 5. Frontend session handling (`apps/web`)

- `lib/api.ts` → `apiFetch` attaches `Authorization: Bearer <token>` (read from the stored session) to every API call; a `401` clears the session and redirects to `/login`. A typed `ApiError(status)` lets pages distinguish `403`.
- `components/authed-shell.tsx` gates the `(app)` route group: `/login` renders bare; every other route requires a stored session or redirects to `/login`.
- `components/access-denied.tsx` renders a clear "Access denied" state, wired into the jobs list and job workspace on `403`.
- Login UX is unchanged (same form, same demo credentials).

> Note: the browser stores the token in `localStorage` — acceptable for a controlled demo. The **security boundary is the server**; the frontend guard is UX only.

## 6. Environment variables

| Var | Purpose | Default |
|-----|---------|---------|
| `AUTH_SECRET` | HS256 signing secret | dev secret in local; **required in production** |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | token lifetime | `480` |
| `DEMO_SEED_ENABLED` | gates `/demo/seed` + `/demo/users` | `true` (non-prod), `false` (prod) |
| `DEMO_ADMIN_PASSWORD` | platform admin demo password | dev fallback `admin123` (local only) |
| `DEMO_ORG_ADMIN_PASSWORD` | org admin demo password | dev fallback `admin123` (local only) |

Production refuses to start without `AUTH_SECRET` (`config.py::_auth_secret`).

## 7. Tests (`services/api/tests/test_auth_rbac.py`, 14 tests)

login token+expiry · wrong password 401 · invalid token 401 · expired token 401 · unauthenticated 401 · platform admin reach · non-admin can't create/list orgs · org admin own-org access · org admin cross-org 403 · estimator create+process · estimator cross-org 403 · viewer read-only (mutation 403) · cross-org document 403 · demo-seed gate 403 when disabled.

Existing endpoint tests authenticate via a shared platform-admin token (`tests/auth_helpers.py`), which bypasses RBAC so behavioural assertions are unchanged.

## 8. Verification

- Backend: `cd services/api && APP_ENV=local PYTHONPATH=. pytest` → **151 passed**.
- Frontend: `npm run typecheck` + `npm run build` → clean.
- `python3 scripts/demo_reset.py` → succeeds.

## 9. Out of scope / follow-ups

- Token **revocation** / refresh tokens (stateless tokens expire only by time).
- Per-user org **membership records** drive nothing yet — the token's `org` claim is the binding. A future step could verify membership against `OrganisationUser` on each request.
- Rate limiting / brute-force protection on `/auth/login`.
- Moving the token to an httpOnly cookie (localStorage is fine for the demo, not ideal for production).
