"""Persistence repository — the single seam between the stores and storage.

Two backends, selected by ``DATABASE_PROVIDER`` (default ``json``):

- ``JsonRepository`` — the original on-disk JSON layout under ``STORAGE_ROOT``
  (unchanged behaviour; the default for local dev and tests).
- ``TursoRepository`` — libsql/SQLite aggregate rows (durable, survives
  redeploys). Each record type is one row: indexed columns + a ``data_json``
  blob of the Pydantic model.

Only structured records live here (organisations, settings, company profiles,
pricebooks, org users, auth users, jobs). Document artifacts (PDFs, parsed/
register/quote JSON, exports) are handled separately by ``file_storage``.
"""

from __future__ import annotations

import json
from functools import lru_cache
from typing import Protocol

from .config import get_settings
from .document_parser import STORAGE_ROOT, _validate_storage_id
from .storage_paths import atomic_write_text
from .schemas import (
    CompanyProfile,
    DemoAuthUserRecord,
    Job,
    Organisation,
    OrganisationSettings,
    OrganisationUser,
    Pricebook,
)


class Repository(Protocol):
    # organisations
    def list_organisation_ids(self) -> list[str]: ...
    def get_organisation(self, org_id: str) -> Organisation | None: ...
    def put_organisation(self, org: Organisation) -> None: ...
    # settings
    def get_settings(self, org_id: str) -> OrganisationSettings | None: ...
    def put_settings(self, org_id: str, settings: OrganisationSettings) -> None: ...
    # company profile
    def get_company_profile(self, org_id: str) -> CompanyProfile | None: ...
    def put_company_profile(self, org_id: str, profile: CompanyProfile) -> None: ...
    # org users (replace-all per org)
    def list_org_users(self, org_id: str) -> list[OrganisationUser]: ...
    def put_org_users(self, org_id: str, users: list[OrganisationUser]) -> None: ...
    # pricebooks (replace-all per org)
    def list_pricebooks(self, org_id: str) -> list[Pricebook]: ...
    def put_pricebooks(self, org_id: str, pricebooks: list[Pricebook]) -> None: ...
    # jobs (replace-all per org)
    def list_jobs(self, org_id: str) -> list[Job]: ...
    def put_jobs(self, org_id: str, jobs: list[Job]) -> None: ...
    # auth users (global)
    def auth_users_exist(self) -> bool: ...
    def list_auth_users(self) -> list[DemoAuthUserRecord]: ...
    def put_auth_users(self, users: list[DemoAuthUserRecord]) -> None: ...


# --------------------------------------------------------------------------- #
# JSON backend — preserves the original on-disk layout exactly.
# --------------------------------------------------------------------------- #


class JsonRepository:
    INDEX_PATH = STORAGE_ROOT / "organisations.json"
    AUTH_USERS_PATH = STORAGE_ROOT / "demo_auth" / "users.json"

    def _org_dir(self, org_id: str):
        _validate_storage_id(org_id, "organisation_id")
        return STORAGE_ROOT / org_id

    def _json_path(self, org_id: str, name: str):
        return self._org_dir(org_id) / f"{name}.json"

    # organisations
    def list_organisation_ids(self) -> list[str]:
        if not self.INDEX_PATH.exists():
            return []
        return list(json.loads(self.INDEX_PATH.read_text(encoding="utf-8")))

    def _write_index(self, ids: list[str]) -> None:
        atomic_write_text(self.INDEX_PATH, json.dumps(sorted(set(ids)), indent=2))

    def get_organisation(self, org_id: str) -> Organisation | None:
        path = self._json_path(org_id, "organisation")
        if not path.exists():
            return None
        return Organisation.model_validate_json(path.read_text(encoding="utf-8"))

    def put_organisation(self, org: Organisation) -> None:
        self._org_dir(org.id).mkdir(parents=True, exist_ok=True)
        atomic_write_text(self._json_path(org.id, "organisation"), org.model_dump_json(indent=2))
        self._write_index(self.list_organisation_ids() + [org.id])

    # settings
    def get_settings(self, org_id: str) -> OrganisationSettings | None:
        path = self._json_path(org_id, "settings")
        if not path.exists():
            return None
        return OrganisationSettings.model_validate_json(path.read_text(encoding="utf-8"))

    def put_settings(self, org_id: str, settings: OrganisationSettings) -> None:
        atomic_write_text(self._json_path(org_id, "settings"), settings.model_dump_json(indent=2))

    # company profile
    def get_company_profile(self, org_id: str) -> CompanyProfile | None:
        path = self._json_path(org_id, "company_profile")
        if not path.exists():
            return None
        return CompanyProfile.model_validate_json(path.read_text(encoding="utf-8"))

    def put_company_profile(self, org_id: str, profile: CompanyProfile) -> None:
        atomic_write_text(self._json_path(org_id, "company_profile"), profile.model_dump_json(indent=2))

    # org users
    def list_org_users(self, org_id: str) -> list[OrganisationUser]:
        path = self._json_path(org_id, "users")
        if not path.exists():
            return []
        return [OrganisationUser.model_validate(item) for item in json.loads(path.read_text(encoding="utf-8"))]

    def put_org_users(self, org_id: str, users: list[OrganisationUser]) -> None:
        atomic_write_text(
            self._json_path(org_id, "users"),
            "[" + ",".join(u.model_dump_json() for u in users) + "]",
        )

    # pricebooks
    def list_pricebooks(self, org_id: str) -> list[Pricebook]:
        path = self._json_path(org_id, "pricebooks")
        if not path.exists():
            return []
        return [Pricebook.model_validate(item) for item in json.loads(path.read_text(encoding="utf-8"))]

    def put_pricebooks(self, org_id: str, pricebooks: list[Pricebook]) -> None:
        atomic_write_text(
            self._json_path(org_id, "pricebooks"),
            "[" + ",".join(p.model_dump_json() for p in pricebooks) + "]",
        )

    # jobs
    def list_jobs(self, org_id: str) -> list[Job]:
        path = self._json_path(org_id, "jobs")
        if not path.exists():
            return []
        return [Job.model_validate(item) for item in json.loads(path.read_text(encoding="utf-8"))]

    def put_jobs(self, org_id: str, jobs: list[Job]) -> None:
        atomic_write_text(
            self._json_path(org_id, "jobs"),
            "[" + ",".join(j.model_dump_json() for j in jobs) + "]",
        )

    # auth users
    def auth_users_exist(self) -> bool:
        return self.AUTH_USERS_PATH.exists()

    def list_auth_users(self) -> list[DemoAuthUserRecord]:
        if not self.AUTH_USERS_PATH.exists():
            return []
        return [DemoAuthUserRecord.model_validate(item) for item in json.loads(self.AUTH_USERS_PATH.read_text(encoding="utf-8"))]

    def put_auth_users(self, users: list[DemoAuthUserRecord]) -> None:
        self.AUTH_USERS_PATH.parent.mkdir(parents=True, exist_ok=True)
        atomic_write_text(self.AUTH_USERS_PATH, "[" + ",".join(u.model_dump_json() for u in users) + "]")


# --------------------------------------------------------------------------- #
# Turso backend — libsql aggregate rows (data_json per record).
# --------------------------------------------------------------------------- #


class TursoRepository:
    def __init__(self, url: str | None = None, auth_token: str | None = None):
        from .database import apply_schema_sync, get_libsql_client

        self._client = get_libsql_client(url=url, auth_token=auth_token)
        apply_schema_sync(self._client)

    def _rows(self, sql: str, args: list | None = None):
        return self._client.execute(sql, args or []).rows

    def _exec(self, sql: str, args: list | None = None) -> None:
        self._client.execute(sql, args or [])

    def close(self) -> None:
        try:
            self._client.close()
        except Exception:  # noqa: BLE001 - best-effort on teardown
            pass

    # organisations
    def list_organisation_ids(self) -> list[str]:
        return [r[0] for r in self._rows("SELECT id FROM kv_organisations ORDER BY id")]

    def get_organisation(self, org_id: str) -> Organisation | None:
        rows = self._rows("SELECT data_json FROM kv_organisations WHERE id = ?", [org_id])
        return Organisation.model_validate_json(rows[0][0]) if rows else None

    def put_organisation(self, org: Organisation) -> None:
        self._exec(
            "INSERT INTO kv_organisations (id, slug, data_json, updated_at) VALUES (?, ?, ?, ?) "
            "ON CONFLICT(id) DO UPDATE SET slug=excluded.slug, data_json=excluded.data_json, updated_at=excluded.updated_at",
            [org.id, org.slug, org.model_dump_json(), org.updated_at.isoformat()],
        )

    # settings
    def get_settings(self, org_id: str) -> OrganisationSettings | None:
        rows = self._rows("SELECT data_json FROM kv_org_settings WHERE organisation_id = ?", [org_id])
        return OrganisationSettings.model_validate_json(rows[0][0]) if rows else None

    def put_settings(self, org_id: str, settings: OrganisationSettings) -> None:
        self._exec(
            "INSERT INTO kv_org_settings (organisation_id, data_json, updated_at) VALUES (?, ?, ?) "
            "ON CONFLICT(organisation_id) DO UPDATE SET data_json=excluded.data_json, updated_at=excluded.updated_at",
            [org_id, settings.model_dump_json(), settings.updated_at.isoformat()],
        )

    # company profile
    def get_company_profile(self, org_id: str) -> CompanyProfile | None:
        rows = self._rows("SELECT data_json FROM kv_company_profiles WHERE organisation_id = ?", [org_id])
        return CompanyProfile.model_validate_json(rows[0][0]) if rows else None

    def put_company_profile(self, org_id: str, profile: CompanyProfile) -> None:
        self._exec(
            "INSERT INTO kv_company_profiles (organisation_id, data_json, updated_at) VALUES (?, ?, ?) "
            "ON CONFLICT(organisation_id) DO UPDATE SET data_json=excluded.data_json, updated_at=excluded.updated_at",
            [org_id, profile.model_dump_json(), profile.updated_at.isoformat()],
        )

    # org users
    def list_org_users(self, org_id: str) -> list[OrganisationUser]:
        rows = self._rows("SELECT data_json FROM kv_org_users WHERE organisation_id = ? ORDER BY rowid", [org_id])
        return [OrganisationUser.model_validate_json(r[0]) for r in rows]

    def put_org_users(self, org_id: str, users: list[OrganisationUser]) -> None:
        self._exec("DELETE FROM kv_org_users WHERE organisation_id = ?", [org_id])
        for u in users:
            self._exec(
                "INSERT INTO kv_org_users (id, organisation_id, email, data_json, created_at) VALUES (?, ?, ?, ?, ?)",
                [u.id, org_id, u.email, u.model_dump_json(), u.created_at.isoformat()],
            )

    # pricebooks
    def list_pricebooks(self, org_id: str) -> list[Pricebook]:
        rows = self._rows("SELECT data_json FROM kv_pricebooks WHERE organisation_id = ? ORDER BY rowid", [org_id])
        return [Pricebook.model_validate_json(r[0]) for r in rows]

    def put_pricebooks(self, org_id: str, pricebooks: list[Pricebook]) -> None:
        self._exec("DELETE FROM kv_pricebooks WHERE organisation_id = ?", [org_id])
        for p in pricebooks:
            self._exec(
                "INSERT INTO kv_pricebooks (id, organisation_id, version, active, data_json, updated_at) VALUES (?, ?, ?, ?, ?, ?)",
                [p.id, org_id, p.version, 1 if p.active else 0, p.model_dump_json(), p.updated_at.isoformat()],
            )

    # jobs
    def list_jobs(self, org_id: str) -> list[Job]:
        rows = self._rows("SELECT data_json FROM kv_jobs WHERE organisation_id = ? ORDER BY rowid", [org_id])
        return [Job.model_validate_json(r[0]) for r in rows]

    def put_jobs(self, org_id: str, jobs: list[Job]) -> None:
        self._exec("DELETE FROM kv_jobs WHERE organisation_id = ?", [org_id])
        for j in jobs:
            self._exec(
                "INSERT INTO kv_jobs (id, organisation_id, status, data_json, created_at, updated_at) VALUES (?, ?, ?, ?, ?, ?)",
                [j.id, org_id, j.status, j.model_dump_json(), j.created_at.isoformat(), j.updated_at.isoformat()],
            )

    # auth users
    def auth_users_exist(self) -> bool:
        return bool(self._rows("SELECT 1 FROM kv_auth_users LIMIT 1"))

    def list_auth_users(self) -> list[DemoAuthUserRecord]:
        rows = self._rows("SELECT data_json FROM kv_auth_users ORDER BY rowid")
        return [DemoAuthUserRecord.model_validate_json(r[0]) for r in rows]

    def put_auth_users(self, users: list[DemoAuthUserRecord]) -> None:
        self._exec("DELETE FROM kv_auth_users")
        for u in users:
            self._exec(
                "INSERT INTO kv_auth_users (id, email, data_json, created_at) VALUES (?, ?, ?, ?)",
                [u.id, u.email, u.model_dump_json(), u.created_at.isoformat()],
            )


@lru_cache(maxsize=4)
def _repository_for(provider: str) -> Repository:
    if provider == "turso":
        return TursoRepository()
    return JsonRepository()


def get_repository() -> Repository:
    return _repository_for(get_settings().database_provider)
