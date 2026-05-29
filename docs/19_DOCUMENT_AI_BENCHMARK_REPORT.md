# Phase 4.5 Document AI Benchmark & Parser Router

## Purpose
Phase 4.5 adds a benchmark harness for comparing document parsing options before TraceQuote AI invests in pricing, final export, or LLM extraction.

The existing Phase 2 parser remains the production POC parser:

```text
PyMuPDF page text extraction + pdfplumber table extraction
```

The new adapters let us compare optional parsers against the same `ParsedDocument` contract without changing upload behavior.

## Added Parser Adapters
- `pymupdf_pdfplumber`: current deterministic parser used by `/documents/upload`.
- `docling`: optional Docling adapter, skipped if Docling is not installed.
- `marker`: optional Marker adapter, skipped if Marker or `marker_single` is not installed.
- `paddleocr`: optional PaddleOCR adapter registration, skipped unless OCR wiring is enabled later.
- `surya_ocr`: optional Surya OCR adapter registration, skipped unless OCR wiring is enabled later.
- `camelot`: optional Camelot table extraction adapter, skipped if Camelot or system dependencies are unavailable.
- `qwen2_5_vl_placeholder`: explicit vision-model placeholder; skipped until a local or hosted Qwen2.5-VL inference route is configured.

Each adapter that runs returns the backend `ParsedDocument` schema:

```text
document_id
file_name
page_count
parser_version
pages
tables
ocr_status
stored_path
parsed_json_path
created_at
```

## Benchmark Script
Run from the repository root:

```bash
cd services/api
source .venv/bin/activate
cd ../..
python3 scripts/benchmark_parsers.py
```

The script uses:

```text
samples/surveys/38-Asbestos-Survey-_Rev_0.pdf
```

If the file is missing, the script exits with:

```text
Missing sample PDF: add samples/surveys/38-Asbestos-Survey-_Rev_0.pdf before running the parser benchmark.
```

## Benchmark Metrics
The benchmark records:

- page count
- text coverage
- table count
- OCR status and OCR-required flag
- register section detected
- no-access section detected
- Class A/Class B section detected
- image count
- runtime
- extraction warnings

## Current Workspace Status
The adapter/router code is in place, but this workspace still does not contain:

```text
samples/surveys/38-Asbestos-Survey-_Rev_0.pdf
```

Because the sample is absent, the benchmark cannot produce a real parser comparison yet. The backend golden survey tests remain correctly skipped until that PDF is added at the exact path above.

## Known Limitations
- Optional parser libraries are intentionally not included in `services/api/requirements.txt`.
- PaddleOCR and Surya are registered as benchmark adapters, but full page rasterization and OCR stitching are not enabled in this POC.
- Docling and Marker page boundary mapping is best-effort and may report extracted content as one logical page until a stronger page mapper is added.
- Camelot depends on system-level PDF/table dependencies and may skip or fail locally even when the Python package is present.
- The benchmark does not choose a parser automatically for production ingestion yet; it prepares the comparison layer needed for a later parser router.
