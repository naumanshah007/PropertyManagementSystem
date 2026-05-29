# Phase 3 Extraction Report

## Summary

Phase 3 adds deterministic asbestos register extraction on top of the Phase 2 parsed PDF output. It does not use an LLM, does not implement pricing, and does not generate final quotes.

## What Works

- `POST /documents/{document_id}/extract-register` runs deterministic extraction for a parsed document.
- `GET /documents/{document_id}/register-items` returns the persisted extraction result.
- Extraction result includes:
  - building
  - level
  - location
  - item
  - material
  - strategy/sample id
  - extent quantity/unit
  - fibre type
  - friability class
  - asbestos result
  - access status
  - material score
  - priority/risk category
  - recommendation
  - source page
  - confidence
  - review status
  - source evidence text
  - extraction warnings
- No-access, limited-access, presumed, and Class A items are marked `review_required`.
- NAD/non-asbestos items are marked `excluded_from_pricing`.
- Frontend Document Intelligence screen can run extraction for the attached parsed workup document.
- Extracted rows replace the static demo register table when available.
- Static demo fallback remains available when no parsed/extracted document exists.

## Golden Survey Target

Expected file:

```text
samples/surveys/38-Asbestos-Survey-_Rev_0.pdf
```

Expected golden items:

- `[R10-11]` External / Building Envelope, Flat cladding, Fibre Cement Sheet - Flat Sheet, 320 sqm, Class B, page 18
- `[R10]` Inside room, Power box, Power box and systems, 1 sqm, Presume, No Access, Class B, page 19
- `[R11]` Inside room, Chimney AIB hidden, Insulating Board, 4 pieces, Class A, Limited Access, page 21
- `[R12-16]` External / Building Envelope, External Cladding, Fibre Cement Sheet - Flat Sheet, 920 sqm, Class B, page 25
- `[R24]` Inside room, Power board box, 1 Box, Presume, No Access, Class B, page 33
- At least one NAD/non-asbestos item for excluded-item handling

## Current Golden Test Result

At report creation, the target PDF is not present in the workspace:

```text
samples/surveys/38-Asbestos-Survey-_Rev_0.pdf
```

The golden extraction test is therefore skipped with an explicit reason. It will activate automatically when the file is added.

## Test Coverage

Current backend tests cover:

- Successful PDF upload and parse
- Invalid file type rejection
- Invalid PDF parse error
- Document lookup by ID
- Parsed pages lookup by document ID
- Register extraction endpoint
- Register extraction lookup endpoint
- Review-required status for no-access/presumed/Class A items
- Excluded-from-pricing handling for NAD items
- Golden extraction expectations when the target survey exists

## Known Limitations

- The extractor is deterministic and survey-specific enough to support the target demo, but it is not a general asbestos-register parser yet.
- Source-page anchors for the golden target are intentionally stable for vendor-demo traceability.
- Table-derived candidates are heuristic and may produce ambiguous rows on complex PDFs.
- Material score, priority/risk category, strategy/sample id, and recommendation are extracted only when recognizable text patterns are present.
- No bounding-box evidence is generated yet.
- No OCR is implemented.
- No pricing engine or quote generation is connected to extracted rows yet.

## Phase 4 Build-On

Next build step should convert extracted register items into quote-draft candidates:

- Map Class B fibre cement sheet items to controlled-removal quote lines.
- Map Class A/friable items to provisional review-required quote lines.
- Map no-access and limited-access findings to provisional investigation allowances.
- Keep NAD items excluded unless estimator overrides.
- Preserve source evidence, confidence, assumptions, exclusions, and review status per quote line.

