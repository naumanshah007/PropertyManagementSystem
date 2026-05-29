# Phase 1 Feature Brief: Application Scaffold

## Goal

Create the first runnable TraceQuote AI scaffold without implementing the full extraction engine yet.

## Scope

Build:

- Next.js + TypeScript frontend in `apps/web`
- FastAPI backend in `services/api`
- Worker skeleton in `services/worker`
- Shared schema definitions in `packages/schemas`
- Basic local development documentation

## Frontend Routes

Required routes:

- `/` Dashboard
- `/workups/new` Upload & Intake
- `/workups/[id]/evidence` Evidence Review
- `/workups/[id]/quote` Quote Builder
- `/workups/[id]/approval` Approval & Export

## Frontend Requirements

The UI should feel like enterprise operational software:

- Dense but readable layout
- No chatbot-first experience
- No marketing landing page
- Clear chips for Class A, Class B, No Access, Presumed, Positive, and NAD
- Upload state placeholders
- Quote builder table placeholder
- Approval checklist placeholder

## Backend Requirements

Endpoints:

- `GET /health`
- `POST /workups`
- `GET /workups`
- `GET /workups/{workup_id}`
- `POST /workups/{workup_id}/documents`

MVP behavior:

- Store workup records in memory or SQLite for the first scaffold.
- Return deterministic demo data for one asbestos workup.
- Do not call an LLM yet.
- Do not implement auth yet, but keep `created_by` and `assigned_estimator_id` fields in the schema.

## Worker Requirements

Create a command or module placeholder for:

- PDF text extraction
- Table extraction
- Survey type detection
- Register item extraction
- No-access extraction

The placeholder should use typed interfaces so Phase 2 can replace stubs with real parsing.

## Shared Schemas

Define schema contracts for:

- Workup
- SourceDocument
- SourceEvidence
- RegisterItem
- QuoteLine
- RiskFlag
- EstimatorEdit
- AuditEvent

## Acceptance Criteria

- A developer can start the frontend and backend locally.
- Dashboard displays demo workup cards and KPI placeholders.
- New Workup screen has upload/intake controls.
- Evidence Review screen shows a split PDF/evidence layout with demo extracted items.
- Quote Builder screen shows editable-looking quote lines with pricing explanations.
- Approval screen shows checklist and export buttons in disabled/placeholder states.
- API health endpoint passes.
- Basic tests or smoke checks exist.

## Codex Prompt For This Feature

```text
Implement Phase 1 according to docs/10_PHASE_1_FEATURE_BRIEF.md.

Use the existing product specs in docs/ as constraints. Do not implement real PDF extraction, LLM calls, billing, multi-tenant SaaS, or live integrations.

Create a runnable Next.js + TypeScript frontend in apps/web and a FastAPI backend in services/api. Add a worker skeleton in services/worker and shared schemas in packages/schemas. Keep the UI enterprise, operational, and evidence-first.

Add local run instructions and basic smoke tests. Run the tests or smoke checks before finishing. Summarize changed files and any commands needed to run the scaffold.
```

