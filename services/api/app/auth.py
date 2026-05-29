"""FastAPI auth + RBAC dependencies.

Tokens are signed JWTs (see ``auth_tokens``). These dependencies decode the
bearer token, identify the user, and enforce role/organisation boundaries:

- ``get_current_user``        — any authenticated user (401 if not)
- ``require_platform_admin``  — platform_admin only
- ``require_org_access``      — member of the path's org, or platform_admin
- ``require_org_role(*roles)``— member with one of the roles, or platform_admin
- ``require_document_access`` — member of the document's owning org (read)
- ``require_document_role``   — member with role for the document's org (write)
- ``require_role(*roles)``    — role check without an org binding

Platform admins bypass org/role checks. ``viewer`` can read but never mutate.
"""

from __future__ import annotations

from dataclasses import dataclass

from fastapi import Depends, Header, HTTPException

from .auth_tokens import TokenError, decode_access_token
from .document_parser import resolve_document_organisation_id


@dataclass
class AuthUser:
    user_id: str
    email: str
    role: str
    organisation_id: str | None


def get_current_user(authorization: str | None = Header(default=None)) -> AuthUser:
    if not authorization or not authorization.lower().startswith("bearer "):
        raise HTTPException(
            status_code=401,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )
    token = authorization.split(" ", 1)[1].strip()
    try:
        claims = decode_access_token(token)
    except TokenError as exc:
        raise HTTPException(
            status_code=401,
            detail=f"Invalid or expired token: {exc}",
            headers={"WWW-Authenticate": "Bearer"},
        ) from exc
    return AuthUser(
        user_id=str(claims.get("sub", "")),
        email=str(claims.get("email", "")),
        role=str(claims.get("role", "viewer")),
        organisation_id=claims.get("org"),
    )


def _is_platform_admin(user: AuthUser) -> bool:
    return user.role == "platform_admin"


def _can_access_org(user: AuthUser, org_id: str) -> bool:
    return _is_platform_admin(user) or user.organisation_id == org_id


def require_platform_admin(user: AuthUser = Depends(get_current_user)) -> AuthUser:
    if not _is_platform_admin(user):
        raise HTTPException(status_code=403, detail="Platform admin access required")
    return user


def require_org_access(org_id: str, user: AuthUser = Depends(get_current_user)) -> AuthUser:
    if not _can_access_org(user, org_id):
        raise HTTPException(status_code=403, detail="You do not have access to this organisation")
    return user


def require_org_role(*allowed: str):
    """Dependency factory: caller must be platform_admin, or an org member whose
    role is in ``allowed``. Cross-org access is rejected before the role check."""

    def dependency(org_id: str, user: AuthUser = Depends(get_current_user)) -> AuthUser:
        if _is_platform_admin(user):
            return user
        if user.organisation_id != org_id:
            raise HTTPException(status_code=403, detail="You do not have access to this organisation")
        if user.role not in allowed:
            raise HTTPException(status_code=403, detail="Insufficient role for this action")
        return user

    return dependency


def require_role(*allowed: str):
    """Role check with no org binding (for non-org-scoped endpoints)."""

    def dependency(user: AuthUser = Depends(get_current_user)) -> AuthUser:
        if _is_platform_admin(user) or user.role in allowed:
            return user
        raise HTTPException(status_code=403, detail="Insufficient role for this action")

    return dependency


def require_document_access(document_id: str, user: AuthUser = Depends(get_current_user)) -> AuthUser:
    org_id = resolve_document_organisation_id(document_id)
    if not _can_access_org(user, org_id):
        raise HTTPException(status_code=403, detail="You do not have access to this document")
    return user


def require_document_role(*allowed: str):
    """Dependency factory for document-scoped mutations: resolves the document's
    owning org, enforces org membership, then the role."""

    def dependency(document_id: str, user: AuthUser = Depends(get_current_user)) -> AuthUser:
        if _is_platform_admin(user):
            return user
        org_id = resolve_document_organisation_id(document_id)
        if user.organisation_id != org_id:
            raise HTTPException(status_code=403, detail="You do not have access to this document")
        if user.role not in allowed:
            raise HTTPException(status_code=403, detail="Insufficient role for this action")
        return user

    return dependency


# Common role groups
MUTATING_ROLES = ("estimator", "reviewer", "organisation_admin")
ADMIN_ONLY = ("organisation_admin",)
