# Phase 2 Ingestion Report

## Summary

Phase 2 adds deterministic PDF ingestion for the TraceQuote AI POC. It does not perform LLM extraction, asbestos register extraction, pricing, OCR, billing, multi-tenancy, or Fergus integration.

## What Works

- `POST /documents/upload` accepts PDF uploads.
- Uploaded PDFs are stored locally under `services/api/storage/documents/`.
- PyMuPDF extracts page-level text.
- pdfplumber extracts tables where possible.
- Parsed JSON is written as `parsed.json` beside the uploaded file.
- `GET /documents/{document_id}` returns parsed document JSON.
- `GET /documents/{document_id}/pages` returns parsed pages.
- Frontend upload controls use the centralized FastAPI client in `apps/web/src/lib/api.ts`.
- Workup cockpit stores POC parsed-document metadata against the demo workup in browser localStorage.
- Document Intelligence screen shows parsed pages, search/filter, page text, tables, parser warnings, and source-ready status.
- Existing deterministic Phase 1 quote/register demo data is preserved.

## Golden Test Result

The golden survey test targets:

```text
samples/surveys/38-Asbestos-Survey-_Rev_0.pdf
```

Expected assertions:

- `page_count == 50`
- Page 1 contains `Asbestos Demolition Survey`
- Full parsed text contains `Register`
- Full parsed text contains `Summary of Areas or Items of Limited Access or No Access`
- Full parsed text contains `Class A and Class B Asbestos Meaning`

Current result at report creation:

```text
skipped because samples/surveys/38-Asbestos-Survey-_Rev_0.pdf is not present
```

When the sample is added, the test activates automatically.

## Parser Limitations

- OCR is not implemented. PDFs with no extractable text are marked `required_later`.
- Page text is raw extraction text and may contain layout artifacts.
- No semantic asbestos register extraction is performed yet.
- No source bounding boxes are generated for UI highlighting yet.
- Uploaded files are stored locally only; this is POC storage, not production file storage.
- Parsed document attachment is frontend POC state stored in localStorage.

## Known Table Extraction Issues

- pdfplumber table extraction depends on PDF structure and ruling lines.
- Some visually tabular content may appear only in page text.
- Some tables may have merged cells, missing cells, or row wrapping.
- No table normalization, header detection, or register-specific schema mapping is implemented yet.

## Phase 3 Build-On

Phase 3 should build asbestos register extraction on top of this parser layer:

- Detect survey/report type from parsed pages.
- Locate asbestos register sections.
- Extract register rows into structured `AsbestosRegisterItem` candidates.
- Extract no-access and limited-access warnings from parsed text.
- Link each extracted candidate to page-level source evidence.
- Add golden assertions for known register items from the sample survey.

