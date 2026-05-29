# Document Pipeline Spec

## Objective

Parse uploaded asbestos surveys and related site documents into traceable structured data suitable for estimator review and quote generation.

## Pipeline

```text
Upload PDF
  -> store source file
  -> extract page text
  -> extract tables
  -> detect survey/report type
  -> extract asbestos register items
  -> extract no-access and limited-access warnings
  -> extract recommendations and assumptions
  -> attach page-level source evidence
  -> produce reviewable extraction package
```

## MVP Parsers

Use local parsing first:

- PyMuPDF for page text and page rendering
- pdfplumber for table extraction
- OCR fallback later when text extraction is insufficient

## Survey Type Detection

Detect:

- Asbestos survey
- Demolition/refurbishment survey
- Management survey
- Hazardous material report
- Quote or estimate
- Unknown report

Output:

- `survey_type`
- `confidence`
- `source_evidence_ids`
- `quote_suitability`
- `warnings`

## Register Item Extraction

Target fields:

- Location
- Area
- Material
- Product type
- Extent
- Unit
- Asbestos result
- Fibre type
- Friability class
- Condition
- Recommendation
- Access status
- Source page
- Evidence snippet
- Confidence

The extractor must preserve enough raw evidence to let an estimator verify the result without trusting the model blindly.

## No-Access Extraction

Extract and flag:

- No-access areas
- Limited-access areas
- Live electricity
- Power boxes
- Chimneys or cavities requiring further inspection
- Missing extent
- Further investigation required
- Client access dependencies

Default review state: `review_required`.

## Confidence Rules

High confidence:

- Structured table row with clear material, extent, result, and page source.

Medium confidence:

- Field inferred from nearby page text or a partially structured table.

Low confidence:

- Ambiguous location, missing extent, conflicting result, OCR-only extraction, or inferred quantity.

## Golden Test Strategy

For each sample survey, store:

- Expected survey type
- Expected register item count
- Expected no-access warnings
- Expected Class A/Class B counts
- Expected key quote-source evidence links

Golden tests should fail when extraction loses important items or page references.

