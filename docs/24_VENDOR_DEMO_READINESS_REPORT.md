# Phase 7.1 Vendor Demo Readiness Report

## Objective
Harden the current TraceQuote AI end-to-end flow for a vendor demo without adding ML, LLM quote writing, billing, multi-tenancy, or Fergus integration.

## Added
PDF download endpoint:

```text
GET /documents/{document_id}/export-quote/pdf
```

Editable export details:

- client name
- project name
- site address
- quote number
- scope summary

Demo reset script:

```bash
python3 scripts/demo_reset.py
```

Full workflow smoke test:

```text
tests/test_full_workflow_smoke.py
```

## Export Improvements
The generated quote package now has:

- improved branded HTML
- improved branded PDF layout
- editable client/project/site details
- direct PDF download route
- source evidence appendix
- assumptions and exclusions
- review statement
- licensed-personnel asbestos disclaimer

## Demo Reset Behavior
The reset script:

1. Clears local API storage.
2. Copies the real Tauraroa survey into a deterministic demo document folder.
3. Parses the 50-page PDF.
4. Extracts the asbestos register.
5. Generates quote candidates.
6. Applies seed pricing.
7. Resolves all review gates for demo readiness.
8. Exports a client quote package.
9. Prints the PDF download endpoint.

Default demo document ID:

```text
demo-tauraroa-vendor
```

Default generated quote number:

```text
TQ-DEMO-READY
```

## Guided Demo Flow
1. Upload survey.
2. Extract register.
3. Generate quote candidates.
4. Apply pricing.
5. Edit/review one line.
6. Resolve approval gates.
7. Export quote.
8. Download PDF.

## Verification
Backend:

```text
38 passed, 5 warnings
```

Demo reset:

```text
Parsed pages: 50
Register items: 55
Quote candidates: 57
Priced lines: 57
Quote number: TQ-DEMO-READY
```

Frontend:

```text
npm run typecheck: passed
npm run build: passed
```

## Remaining Demo Limitations
- The PDF layout is vendor-demo quality, not final brand-production design.
- The app still uses local JSON storage for POC state.
- User identity is not authenticated.
- The export package uses placeholder commercial terms.
- No ML, LLM quote writing, billing, multi-tenancy, or Fergus integration is included.
