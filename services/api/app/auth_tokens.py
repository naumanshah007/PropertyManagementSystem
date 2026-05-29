"""Signed access tokens (HS256 JWT) implemented with the standard library.

We avoid an external JWT dependency: a JWT is just
``base64url(header).base64url(payload).base64url(hmac_sha256(...))``. This keeps
the build dependency-free while giving us standard, verifiable, expiring tokens
suitable for the controlled hosted demo.
"""

from __future__ import annotations

import base64
import hashlib
import hmac
import json
import time

from .config import get_settings


class TokenError(Exception):
    """Raised when a token is missing, malformed, badly signed, or expired."""


def _b64url_encode(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).rstrip(b"=").decode("ascii")


def _b64url_decode(value: str) -> bytes:
    padding = "=" * (-len(value) % 4)
    return base64.urlsafe_b64decode(value + padding)


def _sign(signing_input: str, secret: str) -> str:
    digest = hmac.new(secret.encode("utf-8"), signing_input.encode("ascii"), hashlib.sha256).digest()
    return _b64url_encode(digest)


def create_access_token(
    *,
    user_id: str,
    email: str,
    role: str,
    organisation_id: str | None,
    expires_minutes: int | None = None,
    secret: str | None = None,
    now: int | None = None,
) -> str:
    settings = get_settings()
    secret = secret or settings.auth_secret
    expires_minutes = settings.access_token_expire_minutes if expires_minutes is None else expires_minutes
    issued = int(time.time()) if now is None else now
    payload = {
        "sub": user_id,
        "email": email,
        "role": role,
        "org": organisation_id,
        "iat": issued,
        "exp": issued + expires_minutes * 60,
    }
    header = {"alg": "HS256", "typ": "JWT"}
    signing_input = (
        _b64url_encode(json.dumps(header, separators=(",", ":")).encode("utf-8"))
        + "."
        + _b64url_encode(json.dumps(payload, separators=(",", ":")).encode("utf-8"))
    )
    return signing_input + "." + _sign(signing_input, secret)


def decode_access_token(token: str, *, secret: str | None = None, now: int | None = None) -> dict:
    secret = secret or get_settings().auth_secret
    parts = token.split(".")
    if len(parts) != 3:
        raise TokenError("Malformed token")
    header_b64, payload_b64, signature = parts
    expected = _sign(f"{header_b64}.{payload_b64}", secret)
    if not hmac.compare_digest(expected, signature):
        raise TokenError("Bad token signature")
    try:
        payload = json.loads(_b64url_decode(payload_b64))
    except Exception as exc:  # noqa: BLE001 - any decode failure is an invalid token
        raise TokenError("Bad token payload") from exc
    current = int(time.time()) if now is None else now
    if int(payload.get("exp", 0)) <= current:
        raise TokenError("Token expired")
    return payload
