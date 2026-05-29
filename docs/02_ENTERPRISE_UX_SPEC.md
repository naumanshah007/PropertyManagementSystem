# Enterprise UX Spec

## Experience Principles

- Build the usable workbench first, not a marketing landing page.
- Keep the interface dense, calm, and operational.
- Show source evidence, confidence, and review state near every AI-generated decision.
- Never hide pricing math behind a generic AI explanation.
- Use clear status chips, tables, side panels, and approval gates.

## Main Navigation

Primary areas:

- Dashboard
- New Workup
- Evidence Review
- Quote Builder
- Approval & Export
- Settings

## Screen 1: Dashboard

Purpose: give managers and estimators a work queue.

Cards:

- New Quote Workup
- In Review
- Ready for Approval
- Exported
- Needs More Info

KPIs:

- Average quote prep time saved
- AI extraction confidence
- Estimator edit rate
- Quote value this month
- High-risk jobs flagged

Primary actions:

- Create workup
- Open review queue
- Export ready quote

## Screen 2: Upload & Intake

Purpose: start a quote workup.

Fields:

- Client
- Site address
- Job type
- Survey/report type
- Target output
- Estimator assigned
- Due date
- Historical quote matching on/off

Upload state:

- Drag-and-drop upload zone
- File validation
- Extraction progress timeline
- Parser status
- OCR status

## Screen 3: Evidence Review

Purpose: inspect what the system extracted before pricing.

Layout:

- Left: PDF page viewer
- Right: extracted intelligence
- Bottom: source evidence timeline

Sections:

- Survey Type
- Asbestos Register
- No Access / Limited Access
- Positive / Presumed / NAD Items
- Class A / Class B
- Material Scores
- Recommendations
- Scope Warnings

Chips:

- `Class A`: high attention
- `Class B`: standard controlled removal
- `No Access`: review required
- `Presumed`: provisional
- `Positive`: confirmed
- `NAD`: excluded

Required interactions:

- Click extracted row to jump to PDF page.
- Click source evidence to highlight text or table region.
- Mark extraction as accepted, edited, or rejected.
- Add missing register item manually.

## Screen 4: Quote Builder

Purpose: convert extracted findings into editable commercial quote lines.

Table columns:

- Line item
- Source evidence
- Quantity
- Unit
- Rate
- Risk factor
- Total
- Review status

Expandable "Why?" panel:

- Why included?
- Where found?
- What assumption?
- What similar quote?
- What must estimator confirm?

Required interactions:

- Edit quantity, unit, rate, risk factor, margin, assumptions, and exclusions.
- Show subtotal, GST, and total continuously.
- Record every edit.
- Require explicit acceptance for provisional and no-access lines.

## Screen 5: Approval & Export

Purpose: prevent unreviewed final quotes.

Approval checklist:

- All no-access items reviewed
- All missing extents resolved
- All provisional sums confirmed
- Assumptions selected
- Exclusions selected
- GST checked
- Final estimator sign-off

Exports:

- Client-facing quote PDF
- Internal estimator notes
- Source evidence appendix
- Quote line audit trail
- CSV export

