from __future__ import annotations

import pytest

from kwaicut.backend.security import (
    create_access_token,
    decode_token,
    hash_password,
    verify_password,
)
from kwaicut.common.errors import AuthError


def test_password_hash_roundtrip():
    hashed = hash_password("hunter2password")
    assert hashed != "hunter2password"
    assert verify_password("hunter2password", hashed)
    assert not verify_password("wrong", hashed)


def test_jwt_roundtrip():
    token = create_access_token("user-123", {"role": "admin"})
    payload = decode_token(token)
    assert payload["sub"] == "user-123"
    assert payload["role"] == "admin"
    assert payload["type"] == "access"


def test_invalid_token_raises():
    with pytest.raises(AuthError):
        decode_token("not.a.jwt")
