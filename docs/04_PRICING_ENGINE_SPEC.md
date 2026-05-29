# Pricing Engine Spec

## Objective

Generate explainable draft quote lines from extracted survey findings using deterministic rules, company pricebook data, and similar historical quote retrieval.

## Pricing Architecture

```text
Layer 1: Company pricebook
Layer 2: Rule formulas
Layer 3: Similar historical quote retrieval
Layer 4: ML adjustment later
Layer 5: Human estimator approval
```

MVP rule: rules decide numbers, retrieval provides supporting context, and the estimator approves.

## Quote Sections

Expected asbestos quote sections:

- Site establishment
- Class B non-friable removal
- Class A friable removal
- Provisional investigation
- Waste disposal
- Encapsulation
- Independent assessor or clearance allowance
- Access exclusions
- No-access provisional allowance
- Assumptions and exclusions
- GST

## Pricebook Item

Fields:

- `id`
- `code`
- `name`
- `job_type`
- `material_type`
- `friability_class`
- `unit`
- `base_rate`
- `minimum_charge`
- `waste_rate`
- `default_margin`
- `default_risk_multiplier`
- `default_assumptions`
- `default_exclusions`
- `requires_review`

## Rule Formula

Example:

```text
line_base = max(quantity * unit_rate, minimum_charge)
risk_adjusted = line_base * risk_multiplier
margin_adjusted = risk_adjusted * (1 + margin)
gst = margin_adjusted * gst_rate
total = margin_adjusted + gst
```

Each calculated line must expose:

- Quantity source
- Unit rate source
- Risk multiplier reason
- Margin source
- GST setting
- Rounding

## Review Triggers

Force review when:

- Class A material is present
- Item is presumed asbestos
- Access status is no-access or limited-access
- Quantity is missing or inferred
- Unit rate comes from fallback/default pricing
- Similar quote retrieval conflicts with rule output
- Total variance exceeds configured threshold

## Similar Quote Retrieval

Historical quote matching should retrieve:

- Similar material type
- Similar quantity/unit
- Similar job type
- Similar access constraints
- Similar location or building type where available
- Final approved estimator pricing

Retrieval output must be supporting context only in the MVP. It must not silently override deterministic pricing.

