"""LLM-backed asbestos register extraction (Phase C).

Supports three providers — Anthropic Claude, OpenAI, and Google Gemini — behind
a common extraction interface. The org chooses one in its settings; the
register extractor falls back to the deterministic hardcoded items only when
no provider is configured.

The prompt is identical across providers: extract every register row matching
Xavier's Feb 26 spec (Description, Material, Extent, Friability, plus the
access status and asbestos result that downstream pricing needs).

Each provider call returns a list of raw item dicts that
register_extractor.py converts into ExtractedRegisterItem models. Provider
imports are lazy so the API does not require all three SDKs at install time.
"""

from __future__ import annotations

import json
import logging
import re
from typing import Any

from .schemas import LLMProvider


logger = logging.getLogger("tracequote.llm_extractor")


LLM_EXTRACTOR_VERSION = "phase-c-llm-register-extractor-v1"


DEFAULT_MODELS: dict[str, str] = {
    "anthropic": "claude-sonnet-4-6",
    "openai": "gpt-4o-mini",
    "gemini": "gemini-2.0-flash",
}


_EXTRACTION_INSTRUCTIONS = """You are extracting an asbestos register from a survey report.

Return a JSON object with a single key "items" whose value is an array. Each
item represents one row from the asbestos register and must use these exact
keys:

- "description": short human-readable line item (will become the Fergus cost
  line item title). E.g. "External flat cladding — fibre cement removal".
- "material": the asbestos-containing material described. E.g.
  "Fibre Cement Sheet - Flat Sheet" or "Insulating Board".
- "location": building / room / area where the material is found.
- "extent_quantity": numeric extent value (use null if unknown).
- "extent_unit": one of "sqm", "pieces", "metres", "item", "unknown".
- "friability_class": "Class A" or "Class B" (Class A = friable, Class B =
  bonded/non-friable). Use "Unknown" only if the document genuinely doesn't say.
- "asbestos_result": one of "positive", "presumed", "strongly_presumed",
  "NAD" (No Asbestos Detected), "cross_reference", or "unknown".
- "access_status": one of "accessible", "no_access", "limited_access",
  "unknown". Power boxes, switchboards, and locked rooms are typically
  no_access. Chimneys, voids, and elevated areas are often limited_access.
- "source_page": integer page number where this item appears in the survey.
- "confidence": float between 0 and 1 — how confident you are in this row.

Important rules:
1. Do NOT invent items that aren't in the document. If a row's data is missing
   or unclear, set the field to null/"unknown" rather than guessing.
2. NAD findings should still be returned (set asbestos_result="NAD") so
   downstream code can exclude them from pricing while keeping the audit trail.
3. Group adjacent identical materials in the same building only if the survey
   itself groups them; do not aggregate beyond what the report shows.
4. Return ONLY the JSON object — no markdown, no prose, no code fences.
"""


class LLMExtractionError(RuntimeError):
    """Raised when an LLM provider fails or returns malformed output."""


def extract_register_with_llm(
    *,
    document_text: str,
    provider: LLMProvider,
    api_key: str,
    model: str | None = None,
) -> list[dict[str, Any]]:
    """Route the extraction call to the chosen provider.

    Returns a list of raw item dicts; the caller validates and converts them
    into ExtractedRegisterItem models. Raises LLMExtractionError on any
    network or parsing failure.
    """
    if not provider or provider == "none":
        raise LLMExtractionError("No LLM provider configured")
    if not api_key:
        raise LLMExtractionError("LLM provider configured but no API key set")

    chosen_model = model or DEFAULT_MODELS.get(provider) or DEFAULT_MODELS["anthropic"]
    prompt = _build_user_prompt(document_text)

    if provider == "anthropic":
        return _call_anthropic(api_key=api_key, model=chosen_model, prompt=prompt)
    if provider == "openai":
        return _call_openai(api_key=api_key, model=chosen_model, prompt=prompt)
    if provider == "gemini":
        return _call_gemini(api_key=api_key, model=chosen_model, prompt=prompt)
    raise LLMExtractionError(f"Unknown LLM provider: {provider}")


def verify_llm_credentials(
    *,
    provider: LLMProvider,
    api_key: str,
    model: str | None = None,
) -> tuple[bool, str]:
    """Send a trivial prompt to verify the API key + model work. Returns (ok, detail)."""
    chosen_model = model or DEFAULT_MODELS.get(provider) or DEFAULT_MODELS["anthropic"]
    probe = "Respond with the single word: OK"

    try:
        if provider == "anthropic":
            text = _call_anthropic_raw(api_key=api_key, model=chosen_model, prompt=probe)
        elif provider == "openai":
            text = _call_openai_raw(api_key=api_key, model=chosen_model, prompt=probe)
        elif provider == "gemini":
            text = _call_gemini_raw(api_key=api_key, model=chosen_model, prompt=probe)
        else:
            return False, f"Unknown provider: {provider}"
    except Exception as exc:  # provider SDKs raise many specific exceptions
        return False, f"{type(exc).__name__}: {exc}"

    return True, f"Reply (truncated): {text.strip()[:120]}"


# ---------------------------------------------------------------------------
# Provider implementations
# ---------------------------------------------------------------------------


def _build_user_prompt(document_text: str) -> str:
    # Truncate so we don't blow context windows on huge surveys.
    snippet = document_text[:48000]
    return (
        f"{_EXTRACTION_INSTRUCTIONS}\n\n"
        "----- BEGIN SURVEY TEXT -----\n"
        f"{snippet}\n"
        "----- END SURVEY TEXT -----\n"
        "\nReturn the JSON object now."
    )


def _call_anthropic(*, api_key: str, model: str, prompt: str) -> list[dict[str, Any]]:
    text = _call_anthropic_raw(api_key=api_key, model=model, prompt=prompt)
    return _parse_items_json(text, provider="anthropic")


def _call_anthropic_raw(*, api_key: str, model: str, prompt: str) -> str:
    try:
        from anthropic import Anthropic
    except ImportError as exc:
        raise LLMExtractionError("anthropic package not installed — run: pip install anthropic") from exc

    client = Anthropic(api_key=api_key)
    response = client.messages.create(
        model=model,
        max_tokens=4096,
        messages=[{"role": "user", "content": prompt}],
    )
    # Anthropic returns a list of content blocks; collect their text
    parts: list[str] = []
    for block in response.content:
        text = getattr(block, "text", None)
        if text:
            parts.append(text)
    return "".join(parts)


def _call_openai(*, api_key: str, model: str, prompt: str) -> list[dict[str, Any]]:
    text = _call_openai_raw(api_key=api_key, model=model, prompt=prompt)
    return _parse_items_json(text, provider="openai")


def _call_openai_raw(*, api_key: str, model: str, prompt: str) -> str:
    try:
        from openai import OpenAI
    except ImportError as exc:
        raise LLMExtractionError("openai package not installed — run: pip install openai") from exc

    client = OpenAI(api_key=api_key)
    response = client.chat.completions.create(
        model=model,
        messages=[{"role": "user", "content": prompt}],
        response_format={"type": "json_object"},
    )
    if not response.choices:
        raise LLMExtractionError("OpenAI returned no choices")
    return response.choices[0].message.content or ""


def _call_gemini(*, api_key: str, model: str, prompt: str) -> list[dict[str, Any]]:
    text = _call_gemini_raw(api_key=api_key, model=model, prompt=prompt)
    return _parse_items_json(text, provider="gemini")


def _call_gemini_raw(*, api_key: str, model: str, prompt: str) -> str:
    try:
        from google import genai
    except ImportError as exc:
        raise LLMExtractionError(
            "google-genai package not installed — run: pip install google-genai"
        ) from exc

    client = genai.Client(api_key=api_key)
    response = client.models.generate_content(model=model, contents=prompt)
    return response.text or ""


# ---------------------------------------------------------------------------
# JSON parsing helpers
# ---------------------------------------------------------------------------


_FENCE_PATTERN = re.compile(r"^\s*```(?:json)?\s*|\s*```\s*$", re.IGNORECASE)


def _parse_items_json(raw: str, *, provider: str) -> list[dict[str, Any]]:
    if not raw or not raw.strip():
        raise LLMExtractionError(f"{provider} returned an empty response")

    cleaned = _FENCE_PATTERN.sub("", raw.strip())
    try:
        payload = json.loads(cleaned)
    except json.JSONDecodeError as exc:
        # Some models still wrap output in stray text — try to recover the JSON object
        recovered = _extract_first_json_object(cleaned)
        if recovered is None:
            raise LLMExtractionError(
                f"{provider} returned non-JSON output: {raw[:200]}..."
            ) from exc
        payload = recovered

    if isinstance(payload, list):
        return [item for item in payload if isinstance(item, dict)]
    if isinstance(payload, dict):
        items = payload.get("items") or payload.get("register_items") or []
        if isinstance(items, list):
            return [item for item in items if isinstance(item, dict)]
    raise LLMExtractionError(f"{provider} JSON output missing 'items' array")


def _extract_first_json_object(text: str) -> Any | None:
    """Find the first balanced {...} block in the text. Returns the parsed object."""
    depth = 0
    start = -1
    for index, char in enumerate(text):
        if char == "{":
            if depth == 0:
                start = index
            depth += 1
        elif char == "}":
            depth -= 1
            if depth == 0 and start != -1:
                try:
                    return json.loads(text[start : index + 1])
                except json.JSONDecodeError:
                    start = -1
    return None
