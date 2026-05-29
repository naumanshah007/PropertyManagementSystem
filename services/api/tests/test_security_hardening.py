"""Security regression tests for Phase F hardening.

Covers path traversal, upload size limits, demo-credential exposure, CORS scoping,
and admin password fallback behaviour. These guard against silent regressions in
controls that any external use of the API depends on.
"""

from __future__ import annotations

import os

import fitz
from fastapi.testclient import TestClient
from auth_helpers import PLATFORM_ADMIN_HEADERS

from app.config import _cors_origins, _demo_password
from app.document_parser import InvalidStorageId, _validate_storage_id
from app.main import MAX_UPLOAD_BYTES, app


client = TestClient(app, headers=PLATFORM_ADMIN_HEADERS)


def _make_pdf(text: str = "Asbestos Demolition Survey Register R10-11 Flat cladding Fibre Cement Sheet 320 sqm Class B Positive") -> bytes:
    document = fitz.open()
    page = document.new_page()
    page.insert_text((72, 72), text)
    return document.tobytes()


# ---------------------------------------------------------------------------
# Path traversal
# ---------------------------------------------------------------------------


def test_storage_id_validator_rejects_path_traversal_attempts() -> None:
    for bad_id in ["../etc", "..\\windows", "../../passwd", "doc/../", "doc/sub", "doc\x00"]:
        try:
            _validate_storage_id(bad_id, "document_id")
        except InvalidStorageId:
            continue
        raise AssertionError(f"Validator failed to reject: {bad_id!r}")


def test_storage_id_validator_accepts_well_formed_ids() -> None:
    for good_id in ["doc-abc123", "org-demo-tracequote", "rule_id_42", "A1B2C3"]:
        assert _validate_storage_id(good_id, "id") == good_id


def test_document_endpoint_returns_400_for_traversal_attempt() -> None:
    response = client.get("/documents/..%2F..%2Fetc%2Fpasswd")
    # FastAPI may either match the literal value (then our validator catches it as 400)
    # or fail to match the route at all (404). Both are safe; assert it does NOT 500 or expose data.
    assert response.status_code in {400, 404}


def test_document_pages_endpoint_returns_400_for_invalid_id() -> None:
    response = client.get("/documents/has..dots/pages")
    assert response.status_code in {400, 404}


def test_organisation_endpoint_returns_400_for_invalid_id() -> None:
    # The exception handler converts InvalidStorageId to 400
    response = client.get("/organisations/..bad")
    # Either 400 (validator caught) or 404 (org not found). Never 500 or filesystem-escape.
    assert response.status_code in {400, 404}


# ---------------------------------------------------------------------------
# Upload size limit
# ---------------------------------------------------------------------------


def test_upload_size_limit_is_enforced_with_content_length_header() -> None:
    # Build a body that claims to be larger than the limit. Use a small but valid PDF so
    # the request reaches our handler; FastAPI populates UploadFile.size from Content-Length.
    pdf_bytes = _make_pdf()
    # Padding to push the spooled size over the limit
    oversized = pdf_bytes + b"\x00" * (MAX_UPLOAD_BYTES + 1024)
    response = client.post(
        "/documents/upload",
        files={"file": ("oversized.pdf", oversized, "application/pdf")},
    )
    assert response.status_code == 413
    assert "MB" in response.json()["detail"]


def test_upload_under_size_limit_is_accepted() -> None:
    response = client.post(
        "/documents/upload",
        files={"file": ("small.pdf", _make_pdf(), "application/pdf")},
    )
    assert response.status_code == 200


# ---------------------------------------------------------------------------
# /demo/users endpoint hardening
# ---------------------------------------------------------------------------


def test_demo_users_endpoint_strips_password_hash_and_salt() -> None:
    # In the default test environment, APP_ENV is "local" and demo seed is enabled
    response = client.get("/demo/users")
    assert response.status_code == 200
    users = response.json()
    assert users, "Expected at least one seeded demo user"
    for user in users:
        assert "password_hash" not in user, "password_hash leaked in /demo/users response"
        assert "password_salt" not in user, "password_salt leaked in /demo/users response"
        # Non-sensitive fields still present
        assert "email" in user
        assert "role" in user


# ---------------------------------------------------------------------------
# CORS origin scoping
# ---------------------------------------------------------------------------


def test_cors_origins_include_localhost_only_in_local_env() -> None:
    local = _cors_origins(raw=None, frontend_url="https://quote.privexa.co", app_env="local")
    prod = _cors_origins(raw=None, frontend_url="https://quote.privexa.co", app_env="production")

    assert "http://localhost:3000" in local
    assert "http://127.0.0.1:3000" in local
    assert "http://localhost:3000" not in prod, "Localhost must not be a CORS origin in production"
    assert "http://127.0.0.1:3000" not in prod
    assert "https://quote.privexa.co" in prod


def test_cors_origins_respects_explicit_overrides_in_any_env() -> None:
    origins = _cors_origins(
        raw="https://staging.example.com,https://demo.example.com",
        frontend_url="https://quote.privexa.co",
        app_env="staging",
    )
    assert "https://staging.example.com" in origins
    assert "https://demo.example.com" in origins
    assert "http://localhost:3000" not in origins


# ---------------------------------------------------------------------------
# Admin password fallback hardening
# ---------------------------------------------------------------------------


def test_admin_password_fallback_only_when_app_env_explicitly_local(monkeypatch) -> None:
    # When APP_ENV is unset, no insecure fallback even if app_env arg is "local"
    monkeypatch.delenv("APP_ENV", raising=False)
    monkeypatch.delenv("DEMO_ADMIN_PASSWORD", raising=False)
    assert _demo_password("DEMO_ADMIN_PASSWORD", "local") is None

    # When APP_ENV is explicitly "local", the dev fallback is allowed
    monkeypatch.setenv("APP_ENV", "local")
    assert _demo_password("DEMO_ADMIN_PASSWORD", "local") == "admin123"

    # When APP_ENV is anything else, no fallback
    monkeypatch.setenv("APP_ENV", "production")
    assert _demo_password("DEMO_ADMIN_PASSWORD", "production") is None

    monkeypatch.setenv("APP_ENV", "staging")
    assert _demo_password("DEMO_ADMIN_PASSWORD", "staging") is None


def test_admin_password_respects_explicit_env_var_in_any_env(monkeypatch) -> None:
    monkeypatch.setenv("APP_ENV", "production")
    monkeypatch.setenv("DEMO_ADMIN_PASSWORD", "explicit-prod-password")
    assert _demo_password("DEMO_ADMIN_PASSWORD", "production") == "explicit-prod-password"
