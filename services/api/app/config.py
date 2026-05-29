from __future__ import annotations

import os
from dataclasses import dataclass


DEFAULT_FRONTEND_URL = "https://quote.privexa.co"
LOCAL_FRONTEND_URLS = ["http://localhost:3000", "http://127.0.0.1:3000"]


@dataclass(frozen=True)
class AppSettings:
    app_env: str
    app_base_url: str
    frontend_url: str
    cors_allowed_origins: list[str]
    database_provider: str
    turso_database_url: str | None
    turso_auth_token: str | None
    file_storage_provider: str
    r2_account_id: str | None
    r2_access_key_id: str | None
    r2_secret_access_key: str | None
    r2_bucket_name: str | None
    r2_public_base_url: str | None
    auth_secret: str
    access_token_expire_minutes: int
    demo_seed_enabled: bool
    demo_admin_email: str
    demo_admin_password: str | None
    demo_org_admin_email: str
    demo_org_admin_password: str | None

    @property
    def is_production(self) -> bool:
        return self.app_env == "production"


def get_settings() -> AppSettings:
    app_env = os.getenv("APP_ENV", "local").strip().lower() or "local"
    frontend_url = os.getenv("FRONTEND_URL", DEFAULT_FRONTEND_URL).strip() or DEFAULT_FRONTEND_URL
    app_base_url = os.getenv("APP_BASE_URL", "http://127.0.0.1:8000" if app_env == "local" else "").strip()
    cors_allowed_origins = _cors_origins(os.getenv("CORS_ALLOWED_ORIGINS"), frontend_url, app_env)
    demo_seed_enabled = _bool_env("DEMO_SEED_ENABLED", default=app_env != "production")
    return AppSettings(
        app_env=app_env,
        app_base_url=app_base_url,
        frontend_url=frontend_url,
        cors_allowed_origins=cors_allowed_origins,
        database_provider=os.getenv("DATABASE_PROVIDER", "json").strip().lower() or "json",
        turso_database_url=_optional("TURSO_DATABASE_URL"),
        turso_auth_token=_optional("TURSO_AUTH_TOKEN"),
        file_storage_provider=os.getenv("FILE_STORAGE_PROVIDER", "local").strip().lower() or "local",
        r2_account_id=_optional("R2_ACCOUNT_ID"),
        r2_access_key_id=_optional("R2_ACCESS_KEY_ID"),
        r2_secret_access_key=_optional("R2_SECRET_ACCESS_KEY"),
        r2_bucket_name=_optional("R2_BUCKET_NAME"),
        r2_public_base_url=_optional("R2_PUBLIC_BASE_URL"),
        auth_secret=_auth_secret(app_env),
        access_token_expire_minutes=_int_env("ACCESS_TOKEN_EXPIRE_MINUTES", default=480),
        demo_seed_enabled=demo_seed_enabled,
        demo_admin_email=os.getenv("DEMO_ADMIN_EMAIL", "admin@privexa.co").strip(),
        demo_admin_password=_demo_password("DEMO_ADMIN_PASSWORD", app_env),
        demo_org_admin_email=os.getenv("DEMO_ORG_ADMIN_EMAIL", "test@privexa.co").strip(),
        demo_org_admin_password=_demo_password("DEMO_ORG_ADMIN_PASSWORD", app_env),
    )


def _cors_origins(raw: str | None, frontend_url: str, app_env: str = "local") -> list[str]:
    origins = [frontend_url]
    # Localhost is only an allowed CORS origin in local dev — never in staging/production.
    if app_env == "local":
        origins.extend(LOCAL_FRONTEND_URLS)
    if raw:
        origins.extend(item.strip() for item in raw.split(",") if item.strip())
    return sorted(set(origins))


# Dev-only signing secret. Used only when APP_ENV is not production and no
# AUTH_SECRET is configured — production refuses to start without a real secret.
DEV_AUTH_SECRET = "dev-only-insecure-tracequote-auth-secret-change-me"


def _auth_secret(app_env: str) -> str:
    configured = _optional("AUTH_SECRET")
    if configured:
        return configured
    if app_env == "production":
        raise RuntimeError("AUTH_SECRET must be set in production")
    return DEV_AUTH_SECRET


def _bool_env(name: str, *, default: bool) -> bool:
    raw = os.getenv(name)
    if raw is None:
        return default
    return raw.strip().lower() in {"1", "true", "yes", "on"}


def _int_env(name: str, *, default: int) -> int:
    raw = os.getenv(name)
    if raw is None or not raw.strip():
        return default
    try:
        return int(raw.strip())
    except ValueError:
        return default


def _optional(name: str) -> str | None:
    value = os.getenv(name)
    if value is None or not value.strip():
        return None
    return value.strip()


def _demo_password(name: str, app_env: str) -> str | None:
    configured = _optional(name)
    if configured is not None:
        return configured
    # Only fall back to the dev default when APP_ENV is explicitly set to "local" via env var
    # AND DEMO_SEED_ENABLED is unset or true. Never silently fall back in production.
    explicit_local = os.getenv("APP_ENV", "").strip().lower() == "local"
    return "admin123" if explicit_local and app_env == "local" else None
