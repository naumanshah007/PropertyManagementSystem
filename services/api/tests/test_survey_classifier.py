"""Tests for the Phase B survey-type classifier.

Each test exercises the rule-based detector against the 4 survey types Xavier
named in his Feb 26 brief, plus the unknown-fallback and management-plan-block
paths. The end-to-end test verifies a real upload-and-classify flow.
"""

from __future__ import annotations

import fitz
from fastapi.testclient import TestClient
from auth_helpers import PLATFORM_ADMIN_HEADERS

from app.main import app
from app.schemas import ParsedDocument, ParsedPage
from app.survey_classifier import CLASSIFIER_VERSION, classify_survey


client = TestClient(app, headers=PLATFORM_ADMIN_HEADERS)


def _parsed_doc(header_text: str) -> ParsedDocument:
    """Build a synthetic ParsedDocument whose first page holds the given header."""
    return ParsedDocument(
        document_id="doc-test-classifier",
        file_name="test.pdf",
        page_count=1,
        parser_version="test-parser-v0",
        pages=[ParsedPage(page_number=1, text=header_text, warnings=[])],
        tables=[],
        ocr_status="not_required",
        stored_path="/tmp/test.pdf",
        parsed_json_path="/tmp/test.json",
        created_at=__import__("datetime").datetime.now(__import__("datetime").timezone.utc),
    )


def _make_pdf(header_text: str) -> bytes:
    document = fitz.open()
    page = document.new_page()
    page.insert_text((72, 72), header_text)
    return document.tobytes()


# ---------------------------------------------------------------------------
# Direct classifier unit tests (no API)
# ---------------------------------------------------------------------------


def test_classifier_detects_demolition_survey() -> None:
    parsed = _parsed_doc("Asbestos Demolition Survey - Tauraroa Area School - Rev 0")
    result = classify_survey(parsed)

    assert result.survey_type == "demolition_survey"
    assert result.quotable is True
    assert "demolition survey" in result.matched_keywords
    assert result.classifier_version == CLASSIFIER_VERSION
    assert "quoting OK" in result.reason.lower() or "demolition" in result.reason.lower()


def test_classifier_detects_refurbishment_survey() -> None:
    parsed = _parsed_doc("Refurbishment Survey for 23 Main Road residential property")
    result = classify_survey(parsed)

    assert result.survey_type == "refurbishment_survey"
    assert result.quotable is True


def test_classifier_detects_renovation_survey_as_refurbishment() -> None:
    parsed = _parsed_doc("Asbestos Renovation Survey of warehouse premises")
    result = classify_survey(parsed)

    assert result.survey_type == "refurbishment_survey"
    assert result.quotable is True


def test_classifier_detects_management_survey() -> None:
    parsed = _parsed_doc("Asbestos Management Survey: HMUC Building, dated 2024")
    result = classify_survey(parsed)

    assert result.survey_type == "management_survey"
    assert result.quotable is True
    assert "presumed" in result.reason.lower() or "assumed" in result.reason.lower()


def test_classifier_blocks_management_plan() -> None:
    parsed = _parsed_doc("Asbestos Management Plan – issued by site facilities team")
    result = classify_survey(parsed)

    assert result.survey_type == "management_plan"
    assert result.quotable is False
    assert "not surveys" in result.reason.lower() or "management plan" in result.reason.lower()


def test_classifier_management_survey_takes_priority_over_management_plan_keyword() -> None:
    """If both 'Management Survey' and 'Management Plan' appear, the survey wins (quotable)."""
    parsed = _parsed_doc(
        "Asbestos Management Survey conducted in support of the building's Asbestos Management Plan"
    )
    result = classify_survey(parsed)

    assert result.survey_type == "management_survey"
    assert result.quotable is True


def test_classifier_unknown_when_no_keywords_match() -> None:
    parsed = _parsed_doc("Generic site report with no standard survey-type heading present")
    result = classify_survey(parsed)

    assert result.survey_type == "unknown"
    assert result.quotable is True  # Don't auto-reject — estimator decides
    assert result.confidence < 0.5


def test_classifier_unknown_and_unquotable_when_no_text() -> None:
    parsed = _parsed_doc("")
    result = classify_survey(parsed)

    assert result.survey_type == "unknown"
    assert result.quotable is False
    assert "scan" in result.reason.lower() or "ocr" in result.reason.lower()


# ---------------------------------------------------------------------------
# Upload flow integration tests
# ---------------------------------------------------------------------------


def test_upload_returns_survey_classification_in_parsed_document() -> None:
    response = client.post(
        "/documents/upload",
        files={"file": ("demolition-survey.pdf", _make_pdf("Asbestos Demolition Survey - Rev 0"), "application/pdf")},
    )
    assert response.status_code == 200
    payload = response.json()
    classification = payload["survey_classification"]
    assert classification is not None
    assert classification["survey_type"] == "demolition_survey"
    assert classification["quotable"] is True


def test_generate_quote_candidates_blocks_management_plan_with_422() -> None:
    upload = client.post(
        "/documents/upload",
        files={
            "file": (
                "mgmt-plan.pdf",
                _make_pdf("Asbestos Management Plan – facilities document"),
                "application/pdf",
            ),
        },
    )
    assert upload.status_code == 200
    document_id = upload.json()["document_id"]

    # Extraction is still allowed (an estimator may want to view the register data)
    extract = client.post(f"/documents/{document_id}/extract-register")
    assert extract.status_code == 200

    # But quote generation must be blocked with a 422 and a clear reason
    response = client.post(f"/documents/{document_id}/generate-quote-candidates")
    assert response.status_code == 422
    detail = response.json()["detail"]
    assert detail["survey_type"] == "management_plan"
    assert "not quotable" in detail["message"].lower()
    assert "management" in detail["reason"].lower()


def test_generate_quote_candidates_proceeds_for_quotable_survey() -> None:
    upload = client.post(
        "/documents/upload",
        files={
            "file": (
                "demolition-quotable.pdf",
                _make_pdf(
                    "Asbestos Demolition Survey Register "
                    "R10-11 External / Building Envelope Flat cladding Fibre Cement Sheet - Flat Sheet 320 sqm Class B Positive"
                ),
                "application/pdf",
            ),
        },
    )
    assert upload.status_code == 200
    document_id = upload.json()["document_id"]
    assert client.post(f"/documents/{document_id}/extract-register").status_code == 200

    response = client.post(f"/documents/{document_id}/generate-quote-candidates")
    assert response.status_code == 200
