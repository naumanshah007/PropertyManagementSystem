# Phase 4 Quote Candidate Mapping Report

## Summary

Phase 4 converts deterministic `ExtractedRegisterItem` records into traceable quote-draft candidate lines for estimator review.

This phase does not implement:

- Full pricing engine
- ML
- LLM quote writing
- Final quote generation
- Export package generation

## What Works

- `POST /documents/{document_id}/generate-quote-candidates` generates deterministic quote candidates.
- `GET /documents/{document_id}/quote-candidates` returns persisted candidate results.
- Quote Builder can generate candidates for the attached parsed/extracted workup document.
- Static demo quote lines remain available as fallback.
- Every candidate includes:
  - source register item IDs
  - source evidence text
  - source pages
  - confidence
  - assumptions
  - exclusions
  - reason why included or excluded
  - review status
  - `approval_status: not_ready`

## Mapping Rules Implemented

### Site Establishment

Generated when at least one active ACM item exists.

Status:

```text
review_required
```

Reason:

```text
Asbestos removal work requires site establishment before any removal or investigation lines are finalized.
```

### Class B Removal

Class B fibre cement sheet items map to:

```text
Class B Removal
```

Examples:

- Fibre Cement Sheet - Flat Sheet, 320 sqm
- Fibre Cement Sheet - Flat Sheet, 920 sqm

Default status:

```text
ai_draft
```

If quantity is missing:

```text
review_required
```

### Class A / Friable Removal

Class A or insulating board items map to:

```text
Class A / Friable Removal
```

Default status:

```text
review_required
```

### Provisional / No Access

No-access and limited-access items map to:

```text
Provisional / No Access
```

Default status:

```text
review_required
```

No-access assumptions include power isolation or further inspection where relevant.

### Waste / Disposal Placeholder

Generated when at least one active ACM item exists.

Default status:

```text
review_required
```

No price is generated in this phase.

### Excluded / NAD Findings

NAD/non-asbestos items map to:

```text
Excluded / NAD Findings
```

Default status:

```text
excluded_from_pricing
```

## Test Result

Backend:

```text
15 passed, 2 skipped
```

The skipped tests require the real golden PDF:

```text
samples/surveys/38-Asbestos-Survey-_Rev_0.pdf
```

Frontend:

```text
npm run typecheck
npm run build
```

Both passed.

## Known Limitations

- Candidate lines do not include priced rates, margins, GST, or totals.
- Site establishment and waste candidates are placeholders.
- Mapping depends on deterministic register extraction quality.
- Workup attachment remains frontend POC localStorage state.
- The real golden PDF is still missing in this workspace, so real Tauraroa survey candidate validation has not run.

## Next Phase

Phase 5 should introduce a seed pricebook and deterministic pricing rules for candidate lines while preserving:

- source register item IDs
- evidence text
- source pages
- review gates
- assumptions and exclusions
- estimator approval status

