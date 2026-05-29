# Implementation Plan

## Phase 0: Foundation

Deliverables:

- Repository structure
- Product constitution
- Domain model spec
- UX spec
- Document pipeline spec
- Pricing engine spec
- Review and audit spec
- Export package spec
- Vendor demo script
- Security and compliance spec

Exit criteria:

- The MVP scope is concrete enough to implement feature by feature.
- Non-negotiables are captured as engineering invariants.

## Phase 1: Application Scaffold

Deliverables:

- Next.js + TypeScript app in `apps/web`
- FastAPI service in `services/api`
- Worker service skeleton in `services/worker`
- Shared schemas package
- Seed demo data
- Local Docker Compose for Postgres and Redis

Exit criteria:

- Dashboard, intake, evidence review, quote builder, and approval/export routes exist.
- API health check and workup creation endpoint exist.
- Tests run locally.

## Phase 2: Document Intelligence

Deliverables:

- PDF upload
- File storage adapter
- Page text extraction
- Table extraction
- Survey type detection
- Register item extraction
- No-access extraction
- Source evidence mapping
- Golden test for the provided asbestos survey

Exit criteria:

- The demo survey produces reviewable register items and warnings with page references.

## Phase 3: Quote Builder

Deliverables:

- Seed asbestos pricebook
- Rule-based quote line generation
- Risk multipliers
- Editable quote table
- Assumptions and exclusions
- GST/subtotal/total calculations
- Edit recording

Exit criteria:

- Extracted register items can become draft quote lines.
- Estimator edits are stored.
- Pricing logic is visible per line.

## Phase 4: Review And Audit

Deliverables:

- Review gates
- Approval checklist
- Human sign-off
- Append-only audit events
- Learning data capture from estimator edits

Exit criteria:

- Final export is blocked until required review gates are complete.

## Phase 5: Export Package

Deliverables:

- Client quote PDF
- Internal estimator notes
- Evidence appendix
- CSV export

Exit criteria:

- The vendor demo can show a complete source-to-quote package.

## Phase 6: Demo Polish

Deliverables:

- Enterprise dashboard polish
- Demo dataset
- Playwright demo path
- Vendor talk track
- Before/after time-saving story

Exit criteria:

- Demo can be run reliably from a clean local environment.

