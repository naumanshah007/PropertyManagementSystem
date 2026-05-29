from __future__ import annotations

import sqlite3
from pathlib import Path

from .config import get_settings


MIGRATIONS_DIR = Path(__file__).resolve().parents[1] / "migrations"


class DatabaseUnavailable(RuntimeError):
    pass


def database_provider() -> str:
    return get_settings().database_provider


def validate_schema_sql(schema_sql: str) -> None:
    connection = sqlite3.connect(":memory:")
    try:
        connection.executescript(schema_sql)
    finally:
        connection.close()


def latest_schema_sql() -> str:
    migrations = sorted(MIGRATIONS_DIR.glob("*.sql"))
    if not migrations:
        raise DatabaseUnavailable(f"No migrations found under {MIGRATIONS_DIR}")
    return "\n\n".join(path.read_text(encoding="utf-8") for path in migrations)


def run_local_sqlite_migration(database_path: Path) -> None:
    database_path.parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(database_path)
    try:
        connection.executescript(latest_schema_sql())
        connection.commit()
    finally:
        connection.close()


async def run_turso_migration() -> str:
    settings = get_settings()
    if not settings.turso_database_url or not settings.turso_auth_token:
        raise DatabaseUnavailable("Turso env vars are missing. Set TURSO_DATABASE_URL and TURSO_AUTH_TOKEN.")
    try:
        import libsql_client  # type: ignore[import-not-found]
    except ImportError as exc:
        raise DatabaseUnavailable("Install libsql-client to run migrations against Turso.") from exc

    client = libsql_client.create_client(
        url=settings.turso_database_url,
        auth_token=settings.turso_auth_token,
    )
    try:
        for statement in _split_sql(latest_schema_sql()):
            await client.execute(statement)
    finally:
        await client.close()
    return "turso"


def _split_sql(sql: str) -> list[str]:
    return [statement.strip() for statement in sql.split(";") if statement.strip()]


def get_libsql_client(url: str | None = None, auth_token: str | None = None):
    """Return a synchronous libsql client.

    Works for local `file:` URLs (tests / local dev) and hosted Turso
    (`libsql://` / `https://` + auth token). Sync keeps the repository layer
    simple (the stores are all synchronous).
    """
    try:
        import libsql_client  # type: ignore[import-not-found]
    except ImportError as exc:  # pragma: no cover - dependency guard
        raise DatabaseUnavailable("Install libsql-client to use the Turso backend.") from exc

    settings = get_settings()
    url = url or settings.turso_database_url
    auth_token = auth_token if auth_token is not None else settings.turso_auth_token
    if not url:
        raise DatabaseUnavailable("TURSO_DATABASE_URL is not set.")

    if url.startswith("file:"):
        return libsql_client.create_client_sync(url=url)
    if url.startswith("/") or url.startswith("./"):
        return libsql_client.create_client_sync(url=f"file:{url}")
    return libsql_client.create_client_sync(url=url, auth_token=auth_token)


def apply_schema_sync(client) -> None:
    """Idempotently apply all migrations to a libsql client (CREATE TABLE IF NOT EXISTS)."""
    for statement in _split_sql(latest_schema_sql()):
        client.execute(statement)
