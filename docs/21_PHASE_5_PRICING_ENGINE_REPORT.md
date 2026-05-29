# Phase 5 Pricing Engine Report

## Objective
Phase 5 adds a deterministic seed pricebook and pricing engine for TraceQuote AI quote candidates.

It does not implement ML, LLM quote writing, final export, billing, multi-tenancy, or Fergus integration.

## Preconditions
Phase 4.6 passed against:

```text
samples/surveys/38-Asbestos-Survey-_Rev_0.pdf
```

The real golden PDF parsed successfully with:

- 50 pages
- full text coverage
- register section detected
- no-access section detected
- Class A/Class B section detected

## Backend Additions
New endpoints:

```text
POST /documents/{document_id}/price-quote-candidates
GET  /documents/{document_id}/priced-quote-lines
```

New backend modules:

```text
services/api/app/pricebook.py
services/api/app/pricing_engine.py
```

New persisted output:

```text
services/api/storage/documents/{document_id}/priced_quote_lines.json
```

## Seed Pricebook
Version:

```text
phase-5-seed-pricebook-v1
```

Seed rules:

| Rule | Method | Unit rate | Risk multiplier | Margin |
| --- | --- | ---: | ---: | ---: |
| Site establishment and controlled work setup | fixed | $1,850 | 1.00 | 20% |
| Class B fibre cement sheet removal | per sqm | $42.50 | 1.10 | 22% |
| Class A / friable insulating board provisional allowance | per piece | $650 | 1.35 | 25% |
| No-access / power isolation investigation allowance | fixed | $750 | 1.20 | 20% |
| Waste disposal placeholder | fixed | $1,800 | 1.15 | 20% |
| Encapsulation / provisional allowance | fixed | $1,250 | 1.10 | 20% |
| Excluded / NAD finding | excluded | none | 1.00 | 0% |

All rates are demo seed rates and must be estimator-reviewed before client issue.

## Pricing Formula
For priced lines:

```text
base_cost = quantity * unit_rate
subtotal_ex_gst = base_cost * risk_multiplier * (1 + margin)
gst = subtotal_ex_gst * 0.15
total_inc_gst = subtotal_ex_gst + gst
```

For excluded/NAD lines:

```text
unit_rate = null
base_cost = null
subtotal_ex_gst = null
gst = null
total_inc_gst = null
excluded_from_pricing = true
```

## Review Gates
No priced line is approved by default.

Each priced line has:

- source register item IDs
- source evidence text
- source pages
- pricing rule ID and name
- pricing explanation
- assumptions
- exclusions
- review status
- approval status

Class A, no-access, site establishment, waste, and provisional items remain `review_required`.

NAD/non-asbestos findings remain `excluded_from_pricing`.

The priced quote result remains:

```text
approval_status = blocked
```

## Frontend Additions
The Quote Builder now:

- loads priced draft lines when available
- can apply the deterministic seed pricebook after quote candidate generation
- shows subtotal, GST, total, and blocked approval state
- shows line-level pricing explanation
- shows assumptions and exclusions
- preserves source evidence/page links
- keeps review-required and excluded statuses visible

## Verification
Backend:

```text
26 passed, 5 warnings
```

Frontend:

```text
npm run typecheck: passed
npm run build: passed
```

## Known Limitations
- Rates are deterministic demo seed rates, not production pricebook values.
- No estimator editing persistence for priced values yet.
- No live pricebook editor UI yet.
- No historical quote retrieval is included yet.
- No final quote export is included yet.
- Waste and encapsulation are placeholder/provisional rules.
- Pricing uses candidate sections and descriptions; richer material metadata can improve rule matching in later phases.
