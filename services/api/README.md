# TraceQuote AI API

FastAPI service for the Phase 1 product shell.

## Run Locally

```bash
cd services/api
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

OpenAPI docs:

```text
http://localhost:8000/docs
```

## Smoke Tests

```bash
cd services/api
PYTHONPATH=. pytest
```

## Document Ingestion Endpoints

- `POST /documents/upload`
- `GET /documents/{document_id}`
- `GET /documents/{document_id}/pages`

Uploaded PDFs and parsed JSON are stored locally under `services/api/storage/documents/`.

