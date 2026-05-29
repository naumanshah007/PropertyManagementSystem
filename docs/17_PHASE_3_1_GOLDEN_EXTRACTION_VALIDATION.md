# Phase 3.1 Golden Extraction Validation

## Validation Status

Blocked: the expected golden survey PDF is not present in this workspace.

Expected path:

```text
samples/surveys/38-Asbestos-Survey-_Rev_0.pdf
```

Observed:

```text
ls: samples/surveys/38-Asbestos-Survey-_Rev_0.pdf: No such file or directory
```

Files currently present under `samples/`:

```text
samples/expected_outputs/.gitkeep
samples/quotes/.gitkeep
samples/surveys/.gitkeep
```

## Test Result

Backend test command:

```bash
cd services/api
source .venv/bin/activate
PYTHONPATH=. pytest
```

Result:

```text
11 passed, 2 skipped
```

The skipped tests are the ingestion and extraction golden tests that require:

```text
samples/surveys/38-Asbestos-Survey-_Rev_0.pdf
```

The skip is expected while the PDF is missing. The tests will activate automatically once the file is added at that exact path.

## Ingestion Golden Expectations

Not validated because the PDF is missing.

Expected assertions once the file is present:

- `page_count == 50`
- Page 1 contains `Asbestos Demolition Survey`
- Full parsed text contains `Register`
- Full parsed text contains `Summary of Areas or Items of Limited Access or No Access`
- Full parsed text contains `Class A and Class B Asbestos Meaning`

## Extraction Golden Expectations

Not validated because the PDF is missing.

Expected assertions once the file is present:

- `[R10-11]` External / Building Envelope, Flat cladding, Fibre Cement Sheet - Flat Sheet, 320 sqm, Class B, source/detail page 18
- `[R10]` Inside room, Power box, Power box and systems, 1 sqm, Presume, No Access, Class B, source/detail page 19
- `[R11]` Inside room, Chimney AIB hidden, Insulating Board, 4 pieces, Class A, Limited Access, source/detail page 21
- `[R12-16]` External / Building Envelope, External Cladding, Fibre Cement Sheet - Flat Sheet, 920 sqm, Class B, source/detail page 25
- `[R24]` Inside room, Power board box, Power box and systems, 1 Box, Presume, No Access, Class B, source/detail page 33
- At least one NAD/non-asbestos item extracted and marked `excluded_from_pricing`

## Extracted Row Counts

Not available because the golden survey could not be parsed.

Current counts:

- Extracted ACM rows: not run
- No-access rows: not run
- Limited-access rows: not run
- Class A rows: not run
- Class B rows: not run
- NAD/excluded rows: not run

## Mismatches

No extraction mismatches could be assessed because the golden file is missing.

Current blocker:

```text
samples/surveys/38-Asbestos-Survey-_Rev_0.pdf is absent from the workspace
```

## Known Limitations

- The Phase 3 extractor remains deterministic and demo-targeted.
- No LLM extraction has been added.
- No pricing or quote generation has been added.
- No OCR has been added.
- Real golden validation still depends on adding the PDF at the exact expected path.

## Next Validation Step

Add the survey PDF:

```text
samples/surveys/38-Asbestos-Survey-_Rev_0.pdf
```

Then run:

```bash
cd services/api
source .venv/bin/activate
PYTHONPATH=. pytest tests/test_documents.py::test_golden_asbestos_survey_parses_expected_text tests/test_register_extraction.py::test_golden_asbestos_survey_extracts_expected_items
```

