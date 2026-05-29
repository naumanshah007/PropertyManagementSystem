# Demo Golden Output

## Purpose

This file defines the deterministic demo data expected from the provided asbestos survey for the vendor-ready TraceQuote AI demo.

The Phase 1 scaffold should use this as mock data. Phase 2 extraction work should use this as the first golden target for parser validation.

## Source Document

Expected demo source file:

```text
38-Asbestos-Survey-_Rev_0.pdf
```

## Expected Survey Classification

Survey type:

```text
Asbestos Demolition Survey
```

Expected suitability:

```text
Suitable for asbestos removal and demolition quote drafting, subject to estimator review.
```

Required warning:

```text
AI-generated extraction must be reviewed by an estimator before quote approval.
```

## Expected Register Items

### Item 1: External Flat Cladding

- Location: External / Building Envelope
- Material: Fibre cement sheet - flat sheet
- Extent: 320
- Unit: sqm
- Friability class: Class B
- Access status: Accessible
- Asbestos status: Positive or treated as asbestos-containing for demo purposes
- Review status: `ai_draft`
- Required evidence: source page placeholder

### Item 2: Power Box

- Location: Power box
- Material: Suspected asbestos-containing material
- Extent: 1
- Unit: sqm
- Friability class: Unknown or Class B pending review
- Access status: No access
- Asbestos status: Presumed
- Review status: `review_required`
- Required flag: no-access item
- Required evidence: source page placeholder

### Item 3: Chimney Hidden AIB

- Location: Chimney / hidden area
- Material: Asbestos insulating board
- Product type: Insulating board
- Extent: Unknown or provisional
- Unit: provisional
- Friability class: Class A
- Access status: Limited access
- Asbestos status: Presumed or positive for demo purposes
- Review status: `review_required`
- Required flags:
  - Class A/friable
  - Limited access
  - Further investigation required
- Required evidence: source page placeholder

### Item 4: External Cladding

- Location: External cladding
- Material: Fibre cement sheet
- Extent: 920
- Unit: sqm
- Friability class: Class B
- Access status: Accessible
- Asbestos status: Positive or treated as asbestos-containing for demo purposes
- Review status: `ai_draft`
- Required evidence: source page placeholder

### Item 5: Power Board Box

- Location: Power board box
- Material: Suspected asbestos-containing material
- Extent: Unknown or provisional
- Unit: provisional
- Friability class: Unknown pending review
- Access status: No access
- Asbestos status: Presumed
- Review status: `review_required`
- Required flags:
  - No access
  - Presumed asbestos
  - Estimator review required
- Required evidence: source page placeholder

## Expected Risk Flags

The demo workup must include these risk flags:

- Class A/friable material requires specialist review.
- No-access areas require provisional treatment.
- Limited-access areas require further investigation or assumption.
- Presumed asbestos must remain provisional until confirmed.
- Missing or unknown extent requires estimator confirmation.
- Quote cannot be finalized without human approval.

## Expected Quote Sections

The demo quote draft must include these sections:

- Site establishment
- Class B removal
- Class A/friable removal
- Provisional/no-access investigation
- Waste disposal
- Encapsulation/provisional allowance
- Assumptions and exclusions

## Expected Quote Line Behavior

Every quote line must include:

- Description
- Quantity or provisional quantity
- Unit
- Rate placeholder
- Total placeholder
- Source evidence placeholder
- Pricing logic placeholder
- Review status

No line may be marked approved by default.

## Expected Review States

Required states in demo data:

- `ai_draft`
- `review_required`
- `blocked`

Optional states for UI demonstration:

- `accepted`
- `edited`
- `approved`

## Expected Approval State

The demo workup should start with export blocked because:

- No-access items have not been reviewed.
- Class A/friable item has not been reviewed.
- Presumed asbestos items remain provisional.
- Human estimator approval has not been completed.

