# Phase 4.6 Real Parser Benchmark Validation

## Validation Date
2026-05-23

## Objective
Validate TraceQuote AI parser performance against the real Tauraroa Area School asbestos demolition survey:

```text
samples/surveys/38-Asbestos-Survey-_Rev_0.pdf
```

This phase is limited to document parser validation. It does not implement pricing, ML, LLM extraction, final quote generation, or final export.

## Input File
The PDF was found first at:

```text
tests/38-Asbestos-Survey-_Rev_0.pdf
```

It was copied to the expected golden-test and benchmark path:

```text
samples/surveys/38-Asbestos-Survey-_Rev_0.pdf
```

File size:

```text
6.6 MB
```

## Backend Golden Test Result
Command:

```bash
cd services/api
source .venv/bin/activate
PYTHONPATH=. pytest
```

Result:

```text
20 passed, 5 warnings
```

The golden survey tests are no longer skipped. The ingestion and deterministic extraction tests pass against the real 50-page PDF.

## Parser Benchmark Result
Command:

```bash
source services/api/.venv/bin/activate
python3 scripts/benchmark_parsers.py
```

Result:

```text
completed successfully
```

## Benchmark Summary
| Parser | Status | Pages | Text chars | Tables | OCR status | Register detected | No-access detected | Class A/B detected | Runtime |
| --- | --- | ---: | ---: | ---: | --- | --- | --- | --- | ---: |
| PyMuPDF + pdfplumber | ok | 50 | 43,622 | 57 | not_required | yes | yes | yes | 1.924s |
| Docling | skipped | - | - | - | - | - | - | - | 0.000s |
| Marker | skipped | - | - | - | - | - | - | - | 0.000s |
| PaddleOCR | skipped | - | - | - | - | - | - | - | 0.000s |
| Surya OCR | skipped | - | - | - | - | - | - | - | 0.000s |
| Camelot | skipped | - | - | - | - | - | - | - | 0.000s |
| Qwen2.5-VL placeholder | skipped | - | - | - | - | - | - | - | 0.000s |

## Baseline Parser Metrics
Parser:

```text
pymupdf_pdfplumber
```

Parser version:

```text
phase-2-pymupdf-pdfplumber-v1
```

Metrics:

- page count: `50`
- pages with text: `50`
- text coverage ratio: `1.0`
- extracted character count: `43,622`
- table count: `57`
- OCR required: `false`
- OCR status: `not_required`
- register section detected: `true`
- no-access section detected: `true`
- Class A/Class B section detected: `true`
- image count: `119`
- runtime: `1.924s`
- parser warnings: none

## Optional Parser Status
Docling:

```text
skipped: docling is not installed. Install docling to enable this parser benchmark.
```

Marker:

```text
skipped: marker is not installed. Install marker-pdf to enable this parser benchmark.
```

PaddleOCR:

```text
skipped: paddleocr is not installed. Install paddleocr and paddlepaddle to enable this OCR benchmark.
```

Surya OCR:

```text
skipped: surya is not installed. Install surya-ocr to enable this OCR benchmark.
```

Camelot:

```text
skipped: camelot is not installed. Install camelot-py with its system dependencies to enable Camelot table benchmarking.
```

Qwen2.5-VL placeholder:

```text
skipped: Qwen2.5-VL adapter placeholder only; no local vision model or inference endpoint is configured.
```

## Recommended Production Parser Path
Keep the current production POC ingestion path:

```text
PyMuPDF page text extraction + pdfplumber table extraction
```

Reason:

- It parsed the full 50-page survey.
- It extracted text from every page.
- It detected the register, no-access, and Class A/Class B sections.
- It extracted 57 tables without requiring OCR.
- It completes quickly enough for a local POC benchmark.
- It is already integrated with `/documents/upload`.
- It supports the current deterministic register extraction and quote-candidate mapping flow.

## Next Parser Work
Recommended next parser work should be incremental:

1. Keep PyMuPDF/pdfplumber as the default parser.
2. Add a table-quality scoring check against the known register pages before adding more parser dependencies.
3. Benchmark Camelot only if table quality becomes a blocker.
4. Add OCR adapters only for scanned PDFs or pages with low text coverage.
5. Keep Qwen2.5-VL as a later research path for visual layout understanding, not as the Phase 5 production parser.

## Known Limitations
- Optional parser libraries were not installed in this environment, so only the baseline parser produced real metrics.
- The benchmark reports table count, not semantic table quality.
- OCR was not required for this PDF, so PaddleOCR and Surya do not add immediate value for the Tauraroa survey.
- Image count is informational only; image content is not interpreted.
