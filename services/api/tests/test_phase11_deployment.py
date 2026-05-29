from __future__ import annotations

from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from auth_helpers import PLATFORM_ADMIN_HEADERS

from app.config import get_settings
from app.database import DatabaseUnavailable, latest_schema_sql, run_turso_migration, validate_schema_sql
from app.file_storage import LocalFileStorage
from app.main import app


client = TestClient(app, headers=PLATFORM_ADMIN_HEADERS)


def test_json_storage_mode_remains_default(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("DATABASE_PROVIDER", raising=False)
    monkeypatch.delenv("FILE_STORAGE_PROVIDER", raising=False)

    settings = get_settings()

    assert settings.database_provider == "json"
    assert settings.file_storage_provider == "local"


def test_migration_schema_sql_validates() -> None:
    sql = latest_schema_sql()

    validate_schema_sql(sql)

    assert "CREATE TABLE IF NOT EXISTS organisations" in sql
    assert "CREATE TABLE IF NOT EXISTS export_packages" in sql


def test_turso_migration_reports_missing_configuration(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("DATABASE_PROVIDER", "turso")
    monkeypatch.delenv("TURSO_DATABASE_URL", raising=False)
    monkeypatch.delenv("TURSO_AUTH_TOKEN", raising=False)

    with pytest.raises(DatabaseUnavailable):
        import asyncio

        asyncio.run(run_turso_migration())


def test_demo_seed_blocked_when_disabled(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("DEMO_SEED_ENABLED", "false")

    response = client.post("/demo/seed")

    assert response.status_code == 403


def test_cors_allows_quote_privexa_domain() -> None:
    response = client.options(
        "/health",
        headers={
            "Origin": "https://quote.privexa.co",
            "Access-Control-Request-Method": "GET",
        },
    )

    assert response.status_code == 200
    assert response.headers["access-control-allow-origin"] == "https://quote.privexa.co"


def test_local_file_storage_save_read_and_delete(tmp_path: Path) -> None:
    storage = LocalFileStorage(tmp_path)
    source = tmp_path / "source.pdf"
    source.write_bytes(b"pdf-bytes")

    with source.open("rb") as handle:
        saved_path = storage.save_upload(handle, "uploads/demo.pdf")

    assert Path(saved_path).exists()
    assert storage.read_upload("uploads/demo.pdf") == b"pdf-bytes"
    assert storage.get_download_url("uploads/demo.pdf") == saved_path
    storage.delete_file("uploads/demo.pdf")
    assert not Path(saved_path).exists()


def test_production_config_does_not_default_to_localhost(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("APP_ENV", "production")
    monkeypatch.delenv("APP_BASE_URL", raising=False)
    monkeypatch.setenv("FRONTEND_URL", "https://quote.privexa.co")
    # Production refuses to start without a real signing secret — provide one.
    monkeypatch.setenv("AUTH_SECRET", "prod-test-secret")

    settings = get_settings()

    assert "localhost" not in settings.app_base_url
    assert "127.0.0.1" not in settings.app_base_url
    assert "https://quote.privexa.co" in settings.cors_allowed_origins
