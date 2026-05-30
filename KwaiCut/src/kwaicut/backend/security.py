"""Authentication primitives: password hashing and JWT access tokens.

Passwords are hashed with bcrypt (via passlib). Access tokens are stateless,
signed JWTs carrying the user id (``sub``) and an expiry. Keeping this isolated
from the route handlers makes it straightforward to unit-test and to later swap
in refresh-token rotation or OAuth.
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from typing import Any

import bcrypt
from jose import JWTError, jwt

from kwaicut.common.errors import AuthError
from kwaicut.config import get_settings

# bcrypt only considers the first 72 bytes of the password and raises on longer
# inputs, so we truncate consistently for both hashing and verification.
_BCRYPT_MAX_BYTES = 72


def _encode(password: str) -> bytes:
    return password.encode("utf-8")[:_BCRYPT_MAX_BYTES]


def hash_password(password: str) -> str:
    return bcrypt.hashpw(_encode(password), bcrypt.gensalt()).decode("utf-8")


def verify_password(plain: str, hashed: str) -> bool:
    try:
        return bcrypt.checkpw(_encode(plain), hashed.encode("utf-8"))
    except ValueError:
        return False


def create_access_token(subject: str, extra_claims: dict[str, Any] | None = None) -> str:
    """Create a signed JWT for ``subject`` (the user id)."""
    settings = get_settings()
    now = datetime.now(UTC)
    payload: dict[str, Any] = {
        "sub": subject,
        "iat": now,
        "exp": now + timedelta(minutes=settings.access_token_expire_minutes),
        "type": "access",
    }
    if extra_claims:
        payload.update(extra_claims)
    return jwt.encode(payload, settings.secret_key, algorithm=settings.jwt_algorithm)


def decode_token(token: str) -> dict[str, Any]:
    """Decode and verify a JWT, raising :class:`AuthError` on any problem."""
    settings = get_settings()
    try:
        return jwt.decode(token, settings.secret_key, algorithms=[settings.jwt_algorithm])
    except JWTError as exc:
        raise AuthError("invalid or expired token") from exc
