# UI Design System

## Product Style

TraceQuote AI should feel like governed enterprise SaaS for regulated industrial services.

It must not feel like:

- A chatbot-first tool
- A generic PDF summarizer
- A consumer AI toy
- A marketing landing page
- A loose quote calculator

The core impression should be: operational, traceable, controlled, and commercially useful.

## Visual Tone

Use a clean, professional, industrial-compliance feel:

- Calm neutral backgrounds
- Strong information hierarchy
- Clear tables and panels
- Restrained accent colors
- High readability
- Visible review and risk states
- Minimal decorative imagery

The interface should resemble enterprise compliance, construction operations, or project controls software more than a creative SaaS landing page.

## Application Layout

Primary screens:

- Dashboard
- Workup cockpit
- Evidence viewer
- Quote builder
- Approval/export

### Dashboard

Purpose:

- Show work queue, status, and operational KPIs.

Required elements:

- Workup status cards
- KPI strip
- Recent workups table
- New workup action

### Workup Cockpit

Purpose:

- Show job metadata and workflow progress.

Required elements:

- Client/site details
- Document upload/status panel
- Workflow timeline
- Assigned estimator
- Due date
- Risk summary

### Evidence Viewer

Purpose:

- Make document extraction traceable.

Required elements:

- PDF/document placeholder panel
- Extracted register table
- Source page references
- Evidence snippets/placeholders
- Confidence badges
- Risk chips
- Review controls

### Quote Builder

Purpose:

- Convert extracted findings into editable quote lines.

Required elements:

- Editable pricing table
- Quote section grouping
- Source evidence column
- Pricing logic/why panel
- Totals summary
- Assumptions and exclusions panel
- Review status per line

### Approval/Export

Purpose:

- Prevent unreviewed final output.

Required elements:

- Approval checklist
- Blocking issues panel
- Export package options
- Estimator sign-off placeholder
- Audit trail summary

## Components

Required component types:

- Cards for individual workups, metrics, and repeated items
- Timeline for workflow progress and audit events
- Confidence badges
- Review status chips
- Risk chips
- Evidence panels
- Editable pricing table
- Totals summary panel
- Approval checklist
- Disabled export actions when blocked

## Review Statuses

The UI must support these states:

- `ai_draft`
- `review_required`
- `accepted`
- `edited`
- `approved`
- `blocked`

Recommended display behavior:

- `ai_draft`: neutral state, needs review before final approval
- `review_required`: high-attention state
- `accepted`: reviewed and accepted by estimator
- `edited`: reviewed with estimator changes
- `approved`: final human approval completed
- `blocked`: cannot proceed until required issue is resolved

## Traceability Requirement

Every screen must make traceability visible.

Examples:

- Dashboard shows high-risk jobs and review state.
- Workup cockpit shows document and extraction status.
- Evidence viewer shows page references and extracted snippets.
- Quote builder shows evidence and pricing logic per line.
- Approval/export shows unresolved review gates and audit status.

## Data Display Rules

- Do not display AI output as final by default.
- Do not hide review-required states.
- Do not hide assumptions or exclusions.
- Do not show a quote total without indicating draft/review status.
- Do not present regulatory approval language.
- Do not imply the system replaces a licensed assessor or estimator.

## Phase 1 Mock Data Rules

Phase 1 should use deterministic mock data from `docs/12_DEMO_GOLDEN_OUTPUT.md`.

Mock data must include:

- Asbestos Demolition Survey classification
- Class A item
- Class B items
- No-access items
- Presumed asbestos item
- Evidence/source placeholders
- Review-required quote lines
- Blocked export state

