"""Shared test auth helpers.

Most endpoint tests assert *behaviour*, not auth, so they run as a platform
admin (which bypasses org/role checks). The dedicated RBAC tests mint
role/org-specific tokens to exercise the boundaries.
"""

from __future__ import annotations

import os

# Tests must run in local mode so the deterministic dev signing secret is used
# both when minting tokens here and when the app decodes them.
os.environ.setdefault("APP_ENV", "local")

from app.auth_tokens import create_access_token  # noqa: E402


def make_token(
    role: str = "platform_admin",
    organisation_id: str | None = None,
    *,
    email: str | None = None,
    user_id: str = "test-user",
    expires_minutes: int = 60,
) -> str:
    return create_access_token(
        user_id=user_id,
        email=email or f"{role}@example.com",
        role=role,
        organisation_id=organisation_id,
        expires_minutes=expires_minutes,
    )


def auth_headers(
    role: str = "platform_admin",
    organisation_id: str | None = None,
    **kwargs,
) -> dict[str, str]:
    return {"Authorization": f"Bearer {make_token(role, organisation_id, **kwargs)}"}


PLATFORM_ADMIN_HEADERS = auth_headers("platform_admin")
