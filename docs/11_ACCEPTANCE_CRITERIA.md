# Phase 1 Acceptance Criteria

## Objective

Phase 1 creates a runnable application scaffold for TraceQuote AI. It must demonstrate the intended enterprise workflow using deterministic mock data only.

## Local Run Criteria

- The frontend can be started locally from `apps/web`.
- The backend can be started locally from `services/api`.
- Local run commands are documented.
- The app does not require paid services, live integrations, or external AI APIs to run.
- The frontend can reach the backend in local development.

## Backend Criteria

The backend must expose:

- `GET /health`
- `GET /workups`
- `GET /workups/{workup_id}`
- A deterministic demo workup JSON payload

The demo workup JSON must include:

- Workup metadata
- Uploaded source document placeholder
- Survey type
- Register items
- Risk flags
- Quote lines
- Source evidence placeholders
- Review statuses
- Export status placeholder

## Frontend Criteria

The frontend must show:

- Dashboard
- Workup detail/cockpit
- Document intelligence screen
- Quote builder screen
- Approval/export placeholder screen

Required routes may be implemented as separate pages or equivalent navigable views, but the Phase 1 demo must clearly show the full workflow.

## UI Criteria

- The interface must feel like governed enterprise SaaS, not a chatbot-first tool.
- The UI must use enterprise-grade layout, spacing, typography, and mock data.
- Dashboard must show work queue cards and KPI placeholders.
- Workup cockpit must show intake details, document status, and workflow progress.
- Document intelligence screen must show extracted register items and evidence placeholders.
- Quote builder must show editable-looking quote lines with pricing explanation placeholders.
- Approval/export screen must show review gates and disabled or placeholder export actions.

## Traceability Criteria

- All quote lines must show an evidence/source placeholder.
- Every register item must show a source page placeholder.
- Every quote line must show pricing logic or pricing rationale placeholder.
- No generated quote line may appear as final or approved by default.

## Risk And Review Criteria

- No-access items must appear as `review_required`.
- Class A items must appear as `review_required`.
- Presumed asbestos items must appear as provisional or `review_required`.
- Class B items may appear as standard controlled removal but must still show source evidence.
- Approval/export must remain blocked or placeholder until review gates are satisfied.

## Explicit Non-Scope

Phase 1 must not implement:

- Real ML or LLM extraction
- Real PDF parsing
- Billing
- Multi-tenant SaaS
- Fergus integration
- Live historical quote retrieval
- Production authentication

## Testing And Smoke Checks

Phase 1 must include tests or smoke checks that verify:

- Backend starts or imports successfully.
- `GET /health` returns success.
- Demo workup JSON is available.
- Frontend build, lint, or smoke command runs.
- Core routes or views can render with mock data.

## Exit Criteria

Phase 1 is complete when a reviewer can run the frontend and backend locally, navigate the demo workflow, inspect deterministic asbestos workup mock data, and see evidence-linked quote draft placeholders without any live AI integration.

