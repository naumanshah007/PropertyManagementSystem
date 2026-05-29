"""R2 (S3-compatible) file storage backend.

Covers backend selection, key sanitisation, public-URL building, and the
not-configured error path. The live-bucket S3 calls (upload/get/delete) are
validated post-deploy with real credentials; here we assert the wiring and the
local round-trip via LocalFileStorage.
"""

from __future__ import annotations

import io
import tempfile
from pathlib import Path

import pytest

from auth_helpers import PLATFORM_ADMIN_HEADERS  # noqa: F401 (ensures APP_ENV=local)
from app.file_storage import LocalFileStorage, R2FileStorage, get_file_storage


def test_local_is_default_backend() -> None:
    assert isinstance(get_file_storage(), LocalFileStorage)


def test_local_round_trip() -> None:
    root = Path(tempfile.mkdtemp())
    storage = LocalFileStorage(root)
    storage.save_upload(io.BytesIO(b"hello"), "org/a/doc/b/file.bin")
    assert storage.read_upload("org/a/doc/b/file.bin") == b"hello"
    assert storage.get_download_url("org/a/doc/b/file.bin") is not None
    storage.delete_file("org/a/doc/b/file.bin")
    assert storage.get_download_url("org/a/doc/b/file.bin") is None


def test_r2_selected_when_configured(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("FILE_STORAGE_PROVIDER", "r2")
    monkeypatch.setenv("R2_ACCOUNT_ID", "acct")
    monkeypatch.setenv("R2_ACCESS_KEY_ID", "key")
    monkeypatch.setenv("R2_SECRET_ACCESS_KEY", "secret")
    monkeypatch.setenv("R2_BUCKET_NAME", "bucket")
    assert isinstance(get_file_storage(), R2FileStorage)


def test_r2_raises_when_unconfigured(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("FILE_STORAGE_PROVIDER", "r2")
    for var in ("R2_ACCOUNT_ID", "R2_ACCESS_KEY_ID", "R2_SECRET_ACCESS_KEY", "R2_BUCKET_NAME"):
        monkeypatch.delenv(var, raising=False)
    with pytest.raises(RuntimeError):
        get_file_storage()


def test_r2_public_url_building(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("FILE_STORAGE_PROVIDER", "r2")
    monkeypatch.setenv("R2_ACCOUNT_ID", "acct")
    monkeypatch.setenv("R2_ACCESS_KEY_ID", "key")
    monkeypatch.setenv("R2_SECRET_ACCESS_KEY", "secret")
    monkeypatch.setenv("R2_BUCKET_NAME", "bucket")
    monkeypatch.setenv("R2_PUBLIC_BASE_URL", "https://cdn.example.com")
    storage = get_file_storage()
    # Public base + sanitised key, no live S3 call needed.
    assert storage.get_download_url("/documents/x/exports/q.pdf") == "https://cdn.example.com/documents/x/exports/q.pdf"
    assert R2FileStorage._key("../../etc/passwd") == "etc/passwd" or ".." not in R2FileStorage._key("../../etc/passwd")
