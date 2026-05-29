"""Phase C tests — LLM-backed register extraction with the 3-provider dispatcher.

These tests do NOT make real API calls. Each provider is monkeypatched to
return a deterministic JSON payload so the wiring (config → dispatcher →
register extractor → settings masking) can be verified offline.
"""

from __future__ import annotations

import json

import fitz
from fastapi.testclient import TestClient
from auth_helpers import PLATFORM_ADMIN_HEADERS

from app import llm_extractor
from app.llm_extractor import (
    DEFAULT_MODELS,
    LLMExtractionError,
    _parse_items_json,
    extract_register_with_llm,
    verify_llm_credentials,
)
from app.main import app


client = TestClient(app, headers=PLATFORM_ADMIN_HEADERS)


def _make_pdf(text: str) -> bytes:
    document = fitz.open()
    page = document.new_page()
    page.insert_text((72, 72), text)
    return document.tobytes()


def _create_org(name: str = "LLM Test Co") -> str:
    response = client.post(
        "/organisations",
        json={"name": name, "trading_name": name, "email": f"{name.lower().replace(' ', '')}@example.com"},
    )
    assert response.status_code == 200
    return response.json()["id"]


_SAMPLE_LLM_PAYLOAD = json.dumps(
    {
        "items": [
            {
                "description": "External flat cladding — fibre cement removal",
                "material": "Fibre Cement Sheet - Flat Sheet",
                "location": "R10-11 External / Building Envelope",
                "extent_quantity": 320,
                "extent_unit": "sqm",
                "friability_class": "Class B",
                "asbestos_result": "positive",
                "access_status": "accessible",
                "source_page": 1,
                "confidence": 0.92,
            },
            {
                "description": "Inside-room power box presumed asbestos",
                "material": "Power box and systems",
                "location": "R10 Inside room",
                "extent_quantity": 1,
                "extent_unit": "sqm",
                "friability_class": "Class B",
                "asbestos_result": "presumed",
                "access_status": "no_access",
                "source_page": 1,
                "confidence": 0.65,
            },
        ]
    }
)


# ---------------------------------------------------------------------------
# JSON parsing
# ---------------------------------------------------------------------------


def test_parse_items_json_accepts_clean_object() -> None:
    items = _parse_items_json(_SAMPLE_LLM_PAYLOAD, provider="test")
    assert len(items) == 2
    assert items[0]["material"] == "Fibre Cement Sheet - Flat Sheet"


def test_parse_items_json_accepts_top_level_array() -> None:
    raw = json.dumps([{"description": "X", "material": "Y"}])
    items = _parse_items_json(raw, provider="test")
    assert items == [{"description": "X", "material": "Y"}]


def test_parse_items_json_strips_markdown_code_fences() -> None:
    fenced = "```json\n" + _SAMPLE_LLM_PAYLOAD + "\n```"
    items = _parse_items_json(fenced, provider="test")
    assert len(items) == 2


def test_parse_items_json_recovers_from_leading_prose() -> None:
    noisy = "Sure, here is the JSON:\n" + _SAMPLE_LLM_PAYLOAD
    items = _parse_items_json(noisy, provider="test")
    assert len(items) == 2


def test_parse_items_json_rejects_empty_response() -> None:
    try:
        _parse_items_json("", provider="test")
    except LLMExtractionError:
        return
    raise AssertionError("Expected LLMExtractionError for empty response")


# ---------------------------------------------------------------------------
# Provider dispatcher (mocked)
# ---------------------------------------------------------------------------


def test_dispatcher_raises_when_provider_none() -> None:
    try:
        extract_register_with_llm(document_text="any", provider="none", api_key="x")
    except LLMExtractionError as exc:
        assert "no llm provider" in str(exc).lower()
        return
    raise AssertionError("Expected LLMExtractionError")


def test_dispatcher_raises_when_api_key_missing() -> None:
    try:
        extract_register_with_llm(document_text="any", provider="anthropic", api_key="")
    except LLMExtractionError as exc:
        assert "api key" in str(exc).lower()
        return
    raise AssertionError("Expected LLMExtractionError")


def test_dispatcher_routes_to_anthropic(monkeypatch) -> None:
    captured = {}

    def fake_call(*, api_key, model, prompt):
        captured["called"] = "anthropic"
        captured["model"] = model
        return _SAMPLE_LLM_PAYLOAD

    monkeypatch.setattr(llm_extractor, "_call_anthropic_raw", fake_call)
    items = extract_register_with_llm(
        document_text="Survey",
        provider="anthropic",
        api_key="sk-ant-test",
        model=None,
    )
    assert captured["called"] == "anthropic"
    assert captured["model"] == DEFAULT_MODELS["anthropic"]
    assert len(items) == 2


def test_dispatcher_routes_to_openai(monkeypatch) -> None:
    captured = {}

    def fake_call(*, api_key, model, prompt):
        captured["model"] = model
        return _SAMPLE_LLM_PAYLOAD

    monkeypatch.setattr(llm_extractor, "_call_openai_raw", fake_call)
    items = extract_register_with_llm(
        document_text="Survey",
        provider="openai",
        api_key="sk-openai-test",
    )
    assert captured["model"] == DEFAULT_MODELS["openai"]
    assert len(items) == 2


def test_dispatcher_routes_to_gemini(monkeypatch) -> None:
    captured = {}

    def fake_call(*, api_key, model, prompt):
        captured["model"] = model
        return _SAMPLE_LLM_PAYLOAD

    monkeypatch.setattr(llm_extractor, "_call_gemini_raw", fake_call)
    items = extract_register_with_llm(
        document_text="Survey",
        provider="gemini",
        api_key="gemini-test",
    )
    assert captured["model"] == DEFAULT_MODELS["gemini"]
    assert len(items) == 2


def test_dispatcher_respects_explicit_model_override(monkeypatch) -> None:
    captured = {}

    def fake_call(*, api_key, model, prompt):
        captured["model"] = model
        return _SAMPLE_LLM_PAYLOAD

    monkeypatch.setattr(llm_extractor, "_call_anthropic_raw", fake_call)
    extract_register_with_llm(
        document_text="Survey",
        provider="anthropic",
        api_key="sk-ant-test",
        model="claude-haiku-4-5-20251001",
    )
    assert captured["model"] == "claude-haiku-4-5-20251001"


def test_credential_test_helper_returns_ok_on_success(monkeypatch) -> None:
    monkeypatch.setattr(llm_extractor, "_call_anthropic_raw", lambda **_: "OK")
    ok, detail = verify_llm_credentials(provider="anthropic", api_key="sk-ant-x")
    assert ok is True
    assert "OK" in detail


def test_credential_test_helper_returns_false_on_exception(monkeypatch) -> None:
    def boom(**_):
        raise RuntimeError("invalid key")

    monkeypatch.setattr(llm_extractor, "_call_openai_raw", boom)
    ok, detail = verify_llm_credentials(provider="openai", api_key="bad")
    assert ok is False
    assert "RuntimeError" in detail
    assert "invalid key" in detail


# ---------------------------------------------------------------------------
# Org settings — API key masking and update endpoints
# ---------------------------------------------------------------------------


def test_llm_config_endpoint_returns_masked_preview_after_save() -> None:
    org_id = _create_org("Mask Org")

    update = client.post(
        f"/organisations/{org_id}/llm-config",
        json={
            "llm_provider": "anthropic",
            "llm_api_key": "sk-ant-supersecret-12345",
            "llm_model": "claude-sonnet-4-6",
        },
    )
    assert update.status_code == 200
    payload = update.json()
    assert payload["llm_provider"] == "anthropic"
    assert payload["llm_model"] == "claude-sonnet-4-6"
    assert payload["has_api_key"] is True
    assert payload["api_key_preview"] == "sk-***2345"
    assert "llm_api_key" not in payload  # Raw key never exposed
    assert payload["default_models"]["anthropic"] == DEFAULT_MODELS["anthropic"]


def test_settings_endpoint_never_exposes_raw_api_key() -> None:
    org_id = _create_org("Settings Mask Org")
    client.post(
        f"/organisations/{org_id}/llm-config",
        json={"llm_provider": "openai", "llm_api_key": "sk-openai-leak-check", "llm_model": None},
    )

    response = client.get(f"/organisations/{org_id}/settings")
    assert response.status_code == 200
    settings = response.json()
    # Raw key must be stripped from the generic settings endpoint
    assert settings.get("llm_api_key") is None
    # But the provider is still visible so the UI can show 'configured'
    assert settings["llm_provider"] == "openai"


def test_llm_config_update_with_none_api_key_keeps_existing_secret() -> None:
    org_id = _create_org("Persist Key Org")
    client.post(
        f"/organisations/{org_id}/llm-config",
        json={"llm_provider": "gemini", "llm_api_key": "gemini-original-key", "llm_model": None},
    )

    # Subsequent update with llm_api_key=None should NOT clear the existing key
    second = client.post(
        f"/organisations/{org_id}/llm-config",
        json={"llm_provider": "gemini", "llm_api_key": None, "llm_model": "gemini-1.5-pro"},
    )
    assert second.status_code == 200
    assert second.json()["has_api_key"] is True
    assert second.json()["llm_model"] == "gemini-1.5-pro"


def test_llm_config_update_with_empty_string_clears_the_key() -> None:
    org_id = _create_org("Clear Key Org")
    client.post(
        f"/organisations/{org_id}/llm-config",
        json={"llm_provider": "anthropic", "llm_api_key": "sk-ant-will-be-cleared", "llm_model": None},
    )

    cleared = client.post(
        f"/organisations/{org_id}/llm-config",
        json={"llm_provider": "anthropic", "llm_api_key": "", "llm_model": None},
    )
    assert cleared.status_code == 200
    assert cleared.json()["has_api_key"] is False


# ---------------------------------------------------------------------------
# End-to-end: configured LLM is used in extract-register
# ---------------------------------------------------------------------------


def test_extract_register_uses_llm_when_org_has_provider_configured(monkeypatch) -> None:
    org_id = _create_org("E2E LLM Org")
    client.post(
        f"/organisations/{org_id}/llm-config",
        json={"llm_provider": "anthropic", "llm_api_key": "sk-ant-e2e", "llm_model": None},
    )

    monkeypatch.setattr(llm_extractor, "_call_anthropic_raw", lambda **_: _SAMPLE_LLM_PAYLOAD)

    pdf = _make_pdf(
        "Asbestos Demolition Survey Register "
        "R10-11 External / Building Envelope Flat cladding Fibre Cement Sheet - Flat Sheet 320 sqm Class B Positive"
    )
    upload = client.post(
        f"/organisations/{org_id}/documents/upload",
        files={"file": ("llm-e2e.pdf", pdf, "application/pdf")},
    )
    assert upload.status_code == 200
    document_id = upload.json()["document_id"]

    response = client.post(f"/documents/{document_id}/extract-register")
    assert response.status_code == 200
    payload = response.json()

    # Items should come from the LLM payload (two items, with their material values)
    materials = [item["material"] for item in payload["items"]]
    assert "Fibre Cement Sheet - Flat Sheet" in materials
    assert "Power box and systems" in materials

    # Parser version stamps both deterministic + LLM versions for audit
    assert "llm-register-extractor" in payload["parser_version"]


def test_extract_register_falls_back_when_llm_call_fails(monkeypatch) -> None:
    org_id = _create_org("Fallback Org")
    client.post(
        f"/organisations/{org_id}/llm-config",
        json={"llm_provider": "anthropic", "llm_api_key": "sk-ant-broken", "llm_model": None},
    )

    def boom(**_):
        raise RuntimeError("provider unavailable")

    monkeypatch.setattr(llm_extractor, "_call_anthropic_raw", boom)

    pdf = _make_pdf(
        "Asbestos Demolition Survey Register "
        "R10-11 External / Building Envelope Flat cladding Fibre Cement Sheet - Flat Sheet 320 sqm Class B Positive"
    )
    upload = client.post(
        f"/organisations/{org_id}/documents/upload",
        files={"file": ("llm-fallback.pdf", pdf, "application/pdf")},
    )
    assert upload.status_code == 200
    document_id = upload.json()["document_id"]

    response = client.post(f"/documents/{document_id}/extract-register")
    assert response.status_code == 200
    payload = response.json()

    # Fallback path returns the deterministic items (not LLM-id-prefixed)
    item_ids = [item["id"] for item in payload["items"]]
    assert not all(item_id.startswith("llm-") for item_id in item_ids)

    # A warning records the LLM failure for the audit trail
    warnings = " ".join(w["message"] for w in payload["warnings"])
    assert "LLM extraction" in warnings or "llm" in warnings.lower()
