# Export Package Spec

## Objective

Generate professional quote outputs while preserving internal traceability.

## Export Types

MVP exports:

- Client-facing quote PDF
- Internal estimator notes
- Source evidence appendix
- Quote line audit trail
- CSV export

Later exports:

- Fergus-ready export
- Accounting package export
- Client portal package

## Client-Facing Quote PDF

Sections:

- Cover/header
- Client and site details
- Quote summary
- Included services
- Quote line items
- Subtotal, GST, and total
- Important assumptions
- Exclusions
- Provisional sums
- Acceptance/signature area
- Company contact details

The client-facing quote must not expose raw AI confidence labels unless intentionally configured. It should present reviewed quote content professionally.

## Internal Estimator Notes

Sections:

- Extraction summary
- Register item summary
- High-risk flags
- Pricing rules used
- Similar historical quote references
- Estimator edits
- Open concerns

## Source Evidence Appendix

For each quote line:

- Source document
- Page number
- Evidence snippet
- Register item reference
- Extraction confidence
- Review status

## Audit Trail Export

For compliance and internal QA:

- Workup event timeline
- Estimator edit history
- Approval record
- Export timestamp
- Exported package version

