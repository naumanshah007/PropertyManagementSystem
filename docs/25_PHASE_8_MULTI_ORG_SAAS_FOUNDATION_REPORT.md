# Phase 8 Multi-Organisation SaaS Foundation Report

## Objective
Convert TraceQuote AI from a single-company/local POC foundation into a multi-organisation SaaS structure.

This phase does not add ML, LLM quote writing, billing, multi-tenancy billing plans, or Fergus integration.

## Data Model Added
Phase 8 adds SaaS foundation entities:

- Organisation
- User
- OrganisationUser
- Role
- CompanyProfile
- OrganisationSettings
- Pricebook
- PricebookRule
- QuoteTemplate

Supported roles:

- platform_admin
- organisation_admin
- estimator
- reviewer
- viewer

## Organisation Storage
Local JSON storage is now organised by company boundary:

```text
services/api/storage/organisations/{org_id}/...
```

Documents are stored under:

```text
services/api/storage/organisations/{org_id}/documents/{document_id}/
```

The existing vendor-demo workflow remains backward compatible through:

```text
org-demo-tracequote
```

## Backend Endpoints
Added organisation endpoints:

```text
POST /organisations
GET  /organisations
GET  /organisations/{org_id}
POST /organisations/{org_id}/users
GET  /organisations/{org_id}/users
POST /organisations/{org_id}/pricebooks
GET  /organisations/{org_id}/pricebooks
POST /organisations/{org_id}/settings
GET  /organisations/{org_id}/settings
```

Added organisation-scoped document endpoints:

```text
POST /organisations/{org_id}/documents/upload
GET  /organisations/{org_id}/documents/{document_id}
```

These endpoints prove document storage separation without breaking the current default demo workflow.

## Frontend Additions
Added SaaS/admin screens:

- Platform Admin dashboard
- Organisation list
- Create organisation form
- Organisation settings page
- User management page
- Company pricebook placeholder
- Company profile/branding placeholder

The UI makes the Phase 8 role boundaries explicit:

- platform admin creates organisations
- organisation admin manages users/settings/pricebooks
- estimator uses survey-to-quote workflow

## Verification
Backend:

```text
43 passed, 5 warnings
```

Frontend:

```text
npm run typecheck: passed
npm run build: passed
```

## Tested Guarantees
Backend tests cover:

- creating an organisation
- listing organisations
- creating organisation users
- role assignment
- organisation-specific storage paths
- preventing cross-organisation document reads
- organisation-owned pricebooks
- organisation-owned settings

## Known Limitations
- This is still local JSON persistence, not PostgreSQL.
- Authentication is not implemented yet.
- Role checks are modeled and persisted but not enforced by auth middleware yet.
- Existing default workflow uses the demo organisation automatically for backward compatibility.
- Organisation-scoped extraction/pricing/export wrappers can be added once auth context exists.
- Billing, Fergus integration, ML, and LLM quote writing remain out of scope.
