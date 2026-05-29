# Phase 7 Quote Export Report

## Objective
Phase 7 adds a gated client-facing quote package export for reviewed TraceQuote AI priced quote lines.

This phase does not implement ML, LLM quote writing, billing, multi-tenancy, Fergus integration, or production document branding.

## Backend Additions
New endpoints:

```text
POST /documents/{document_id}/export-quote
GET  /documents/{document_id}/export-quote
```

Export is blocked with `409 Conflict` unless Phase 6 approval-readiness passes.

Generated files are stored under:

```text
services/api/storage/documents/{document_id}/exports/
```

Generated files:

```text
client_quote.html
client_quote.pdf
export_package.json
```

## Export Package Schema
The export package includes:

- document ID
- export ID
- quote number placeholder
- generated status
- HTML path
- PDF path
- HTML content
- line count
- subtotal ex GST
- GST
- total inc GST
- assumptions
- exclusions
- source pages
- generated timestamp

## Quote Content
The generated client-facing quote includes:

- client/project placeholder details
- site address placeholder
- quote number placeholder
- date
- scope summary
- priced quote line table
- subtotal ex GST
- GST
- total inc GST
- assumptions
- exclusions
- review statement
- source evidence appendix
- disclaimer that final asbestos decisions require qualified/licensed personnel
- explicit statement that TraceQuote AI does not claim regulatory approval

## Export Gate
Export requires:

- priced quote lines exist
- approval-readiness status is `ready_for_approval`
- every active priced line is estimator-reviewed/accepted
- excluded/NAD lines remain excluded from pricing

The export endpoint does not override review state. It only packages already-reviewed quote lines.

## Frontend Additions
The Review & Export page now includes a live export panel that:

- reads the attached parsed document from POC workup state
- checks backend approval readiness
- shows blocked/ready/exported state
- displays the approval checklist
- calls the export endpoint when ready
- shows generated quote number, total, line count, generated timestamp, stored PDF path, and export metadata link

## Verification
Backend:

```text
36 passed, 5 warnings
```

Frontend:

```text
npm run typecheck: passed
npm run build: passed
```

## Known Limitations
- The PDF is a simple generated PDF suitable for POC validation, not final branded typography.
- The frontend exposes export metadata and stored local paths; a production download route or signed file URL is still needed.
- Client/project/site details are placeholders.
- No final quote approval/signature endpoint exists yet.
- No email/send workflow is included.
- No ML, LLM quote writing, billing, multi-tenancy, or Fergus integration is included.
