# Review And Audit Spec

## Objective

Ensure every AI-generated quote draft is traceable, reviewed, and auditable before export.

## Review Gates

A workup cannot move to approval until:

- Every extracted register item is accepted, edited, rejected, or marked not relevant.
- Every no-access and limited-access warning is explicitly acknowledged.
- Every quote line has pricing logic attached.
- Every provisional line has a reason.
- Every estimator edit is recorded.

A workup cannot be exported as final until:

- Approval checklist is complete.
- A human estimator has signed off.
- The system has created an audit event for approval.

## Human Approval

Approval record fields:

- `workup_id`
- `approved_by`
- `approved_at`
- `approval_notes`
- `checklist_snapshot`
- `quote_totals_snapshot`

## Edit Recording

Every estimator correction must capture:

- Entity and field changed
- Previous value
- New value
- Optional reason
- User
- Timestamp
- Workup context

Examples:

- AI extracted quantity `320 sqm`; estimator changed to `340 sqm`.
- AI suggested Class B cladding removal; estimator added glue remover allowance.
- AI omitted scaffolding exclusion; estimator added it.

## Audit Event Types

- `workup.created`
- `document.uploaded`
- `document.parsed`
- `extraction.generated`
- `extraction.edited`
- `quote_line.generated`
- `quote_line.edited`
- `review.completed`
- `approval.completed`
- `export.generated`

## Learning Loop

Estimator edits become structured training data. The MVP should store the data clearly before attempting model training.

Learning records should support later analysis of:

- Common quantity corrections
- Common rate corrections
- Missing line items
- Frequently added assumptions
- Material-specific pricing variance
- Rule changes needed

