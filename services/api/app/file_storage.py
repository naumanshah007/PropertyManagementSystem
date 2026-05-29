from __future__ import annotations

from abc import ABC, abstractmethod
from pathlib import Path
from shutil import copyfileobj
from typing import BinaryIO

from .config import get_settings


class FileStorage(ABC):
    @abstractmethod
    def save_upload(self, source: BinaryIO, storage_key: str) -> str:
        raise NotImplementedError

    @abstractmethod
    def read_upload(self, storage_key: str) -> bytes:
        raise NotImplementedError

    @abstractmethod
    def save_export(self, source_path: Path, storage_key: str) -> str:
        raise NotImplementedError

    @abstractmethod
    def get_download_url(self, storage_key: str) -> str | None:
        raise NotImplementedError

    @abstractmethod
    def delete_file(self, storage_key: str) -> None:
        raise NotImplementedError


class LocalFileStorage(FileStorage):
    def __init__(self, root: Path):
        self.root = root

    def _path(self, storage_key: str) -> Path:
        safe_key = storage_key.strip("/").replace("..", "_")
        return self.root / safe_key

    def save_upload(self, source: BinaryIO, storage_key: str) -> str:
        target = self._path(storage_key)
        target.parent.mkdir(parents=True, exist_ok=True)
        with target.open("wb") as output:
            copyfileobj(source, output)
        return str(target)

    def read_upload(self, storage_key: str) -> bytes:
        return self._path(storage_key).read_bytes()

    def save_export(self, source_path: Path, storage_key: str) -> str:
        target = self._path(storage_key)
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(source_path.read_bytes())
        return str(target)

    def get_download_url(self, storage_key: str) -> str | None:
        path = self._path(storage_key)
        return str(path) if path.exists() else None

    def delete_file(self, storage_key: str) -> None:
        path = self._path(storage_key)
        if path.exists():
            path.unlink()


class R2FileStorage(FileStorage):
    """Cloudflare R2 (S3-compatible) object storage via boto3.

    boto3 is imported lazily so json/local deployments never need it. Requires
    R2_ACCOUNT_ID, R2_ACCESS_KEY_ID, R2_SECRET_ACCESS_KEY, R2_BUCKET_NAME
    (R2_PUBLIC_BASE_URL optional — falls back to presigned URLs).
    """

    def __init__(self):
        self.settings = get_settings()
        missing = [
            name
            for name, value in {
                "R2_ACCOUNT_ID": self.settings.r2_account_id,
                "R2_ACCESS_KEY_ID": self.settings.r2_access_key_id,
                "R2_SECRET_ACCESS_KEY": self.settings.r2_secret_access_key,
                "R2_BUCKET_NAME": self.settings.r2_bucket_name,
            }.items()
            if not value
        ]
        if missing:
            raise RuntimeError(f"Cloudflare R2 is not configured. Missing: {', '.join(missing)}.")
        self.bucket = self.settings.r2_bucket_name

    def _client(self):
        try:
            import boto3  # type: ignore[import-not-found]
        except ImportError as exc:  # pragma: no cover - dependency guard
            raise RuntimeError("Install boto3 to use R2 storage.") from exc
        return boto3.client(
            "s3",
            endpoint_url=f"https://{self.settings.r2_account_id}.r2.cloudflarestorage.com",
            aws_access_key_id=self.settings.r2_access_key_id,
            aws_secret_access_key=self.settings.r2_secret_access_key,
            region_name="auto",
        )

    @staticmethod
    def _key(storage_key: str) -> str:
        return storage_key.strip("/").replace("..", "_")

    def save_upload(self, source: BinaryIO, storage_key: str) -> str:
        key = self._key(storage_key)
        self._client().upload_fileobj(source, self.bucket, key)
        return key

    def read_upload(self, storage_key: str) -> bytes:
        obj = self._client().get_object(Bucket=self.bucket, Key=self._key(storage_key))
        return obj["Body"].read()

    def save_export(self, source_path: Path, storage_key: str) -> str:
        key = self._key(storage_key)
        self._client().upload_file(str(source_path), self.bucket, key)
        return key

    def get_download_url(self, storage_key: str) -> str | None:
        key = self._key(storage_key)
        if self.settings.r2_public_base_url:
            return f"{self.settings.r2_public_base_url.rstrip('/')}/{key}"
        return self._client().generate_presigned_url(
            "get_object",
            Params={"Bucket": self.bucket, "Key": key},
            ExpiresIn=3600,
        )

    def delete_file(self, storage_key: str) -> None:
        self._client().delete_object(Bucket=self.bucket, Key=self._key(storage_key))


def get_file_storage(root: Path | None = None) -> FileStorage:
    settings = get_settings()
    if settings.file_storage_provider == "r2":
        return R2FileStorage()
    if root is None:
        root = Path(__file__).resolve().parents[1] / "storage"
    return LocalFileStorage(root)
