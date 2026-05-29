"""Rule-based asbestos survey classifier (Phase B).

Per Xavier's Feb 26 brief, every uploaded document falls into one of four
asbestos report types. A management plan is not a survey and cannot produce a
reliable quote; the other three types are quotable (with caveats for
management surveys, which often use presumed/assumed sample results).

Detection is keyword-based on the first few pages where the title/heading
usually appears. No LLM is required for this layer — it stays deterministic
and explainable.
"""

from __future__ import annotations

from .schemas import ParsedDocument, SurveyClassification, SurveyType


CLASSIFIER_VERSION = "phase-b-rule-based-classifier-v1"

# Number of leading pages to scan for type keywords. Titles/headers almost always
# appear in the first 2-3 pages; scanning more would inflate false positives
# from body text referencing other survey types.
_HEADER_PAGE_WINDOW = 4

# Order matters: most-specific (demolition) is checked first because demolition
# surveys often reference refurbishment elsewhere in the document. Management
# plan is checked AFTER management survey to avoid mis-classifying "Management
# Survey" as a Management Plan via partial match.
_DETECTION_RULES: list[tuple[SurveyType, tuple[str, ...], bool]] = [
    # (survey_type, keywords, quotable)
    ("demolition_survey", ("demolition survey", "demolition and refurbishment survey", "pre-demolition"), True),
    ("refurbishment_survey", ("refurbishment survey", "renovation survey", "refurbishment / renovation", "refurbishment and renovation"), True),
    ("management_survey", ("management survey",), True),
    ("management_plan", ("management plan", "asbestos management plan"), False),
]


def _header_text(parsed: ParsedDocument) -> str:
    """Concatenate text from the first few pages — case folded for keyword matching."""
    pages = parsed.pages[:_HEADER_PAGE_WINDOW]
    return " ".join(page.text.lower() for page in pages if page.text)


def classify_survey(parsed: ParsedDocument) -> SurveyClassification:
    """Classify a parsed document into one of the four asbestos report types."""
    haystack = _header_text(parsed)

    if not haystack.strip():
        return SurveyClassification(
            survey_type="unknown",
            quotable=False,
            confidence=0.0,
            matched_keywords=[],
            reason="No extractable text in the first pages — likely a scanned PDF requiring OCR.",
            classifier_version=CLASSIFIER_VERSION,
        )

    for survey_type, keywords, quotable in _DETECTION_RULES:
        matched = [kw for kw in keywords if kw in haystack]
        if matched:
            return SurveyClassification(
                survey_type=survey_type,
                quotable=quotable,
                confidence=0.95 if len(matched) > 1 else 0.85,
                matched_keywords=matched,
                reason=_reason_for(survey_type, matched),
                classifier_version=CLASSIFIER_VERSION,
            )

    # No keyword hit — let estimator decide (do not auto-reject; some valid
    # surveys may use non-standard headings).
    return SurveyClassification(
        survey_type="unknown",
        quotable=True,
        confidence=0.3,
        matched_keywords=[],
        reason=(
            "No standard survey-type keywords found in the document header. "
            "Estimator should confirm the survey type before quoting."
        ),
        classifier_version=CLASSIFIER_VERSION,
    )


def _reason_for(survey_type: SurveyType, matched: list[str]) -> str:
    anchor = matched[0]
    if survey_type == "management_plan":
        return (
            f"Header contains '{anchor}'. Management Plans are not surveys and typically lack "
            "the sample-level detail required to produce a reliable quote. Quoting is blocked — "
            "ask the client for the underlying Management Survey."
        )
    if survey_type == "management_survey":
        return (
            f"Header contains '{anchor}'. Management Surveys often use 'presumed' or 'assumed' "
            "sample results — quote lines for these items should be flagged as provisional."
        )
    if survey_type == "refurbishment_survey":
        return (
            f"Header contains '{anchor}'. Refurbishment / Renovation Survey — quoting OK using "
            "the asbestos register and identified no-access areas."
        )
    if survey_type == "demolition_survey":
        return (
            f"Header contains '{anchor}'. Demolition Survey — quoting OK using the asbestos "
            "register and identified no-access areas. Class A items must include clearance allowances."
        )
    return f"Matched keyword: {anchor}"
