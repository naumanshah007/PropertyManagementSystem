# Phase 6 Review and Approval Report

## Objective
Phase 6 adds estimator review, edit persistence, and approval-gate validation for TraceQuote AI priced draft quote lines.

This phase does not implement ML, LLM quote writing, billing, multi-tenancy, Fergus integration, or final export.

## Backend Additions
New endpoints:

```text
POST /documents/{document_id}/priced-quote-lines/{line_id}/edit
POST /documents/{document_id}/priced-quote-lines/{line_id}/resolve-review
GET  /documents/{document_id}/approval-readiness
```

Updated priced quote result persistence:

```text
services/api/storage/documents/{document_id}/priced_quote_lines.json
```

The persisted priced quote result now includes:

- priced lines
- estimator edit records
- audit events
- quote-level approval status

## Editable Fields
Estimator edits support:

- quantity
- unit rate
- risk multiplier
- margin

Every edit requires a reason and creates an `EstimatorEdit` record with:

- entity type
- line ID
- field name
- previous value
- new value
- reason
- user ID
- timestamp

Edited lines are returned to `review_required` and `not_ready` until re-resolved by an estimator.

## Review Resolution
Resolving a review gate requires:

- reason
- estimator user ID
- assumptions accepted
- exclusions accepted

Resolved lines become:

```text
review_status = accepted
review_required = false
approval_status = ready_for_approval
```

No line is marked `approved` by default.

## Approval Readiness Rules
The quote remains blocked until:

- all review-required lines are resolved or accepted
- all no-access lines have assumptions and exclusions accepted
- all Class A/friable lines are estimator-reviewed
- all provisional allowances are accepted
- at least one estimator approval-gate event exists

The readiness endpoint returns:

- quote approval status
- checklist results
- unresolved blocking line IDs

## Frontend Additions
The Quote Builder now supports:

- editable quantity, unit rate, risk multiplier, and margin fields
- mandatory edit reason before saving pricing edits
- mandatory review reason before resolving a review gate
- resolve-review action per priced line
- approval checklist
- blocked/ready approval state
- line-level edit history

## Verification
Backend:

```text
31 passed, 5 warnings
```

Frontend:

```text
npm run typecheck: passed
npm run build: passed
```

## Known Limitations
- User identity is still a POC `user_id` string, not authenticated identity.
- Edit history is stored in the local priced quote JSON for the POC, not in a database table.
- There is no final quote export yet.
- There is no separate global quote approval endpoint yet; Phase 6 exposes readiness for approval/export.
- There is no pricebook editor UI yet.
