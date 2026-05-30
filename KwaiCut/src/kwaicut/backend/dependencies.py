"""Reusable FastAPI dependencies (auth, current user)."""

from __future__ import annotations

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from kwaicut.backend.security import decode_token
from kwaicut.common.errors import AuthError
from kwaicut.db.base import get_db
from kwaicut.db.models import User

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login")


def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db),
) -> User:
    """Resolve and return the authenticated user, or raise 401."""
    credentials_exc = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = decode_token(token)
    except AuthError as exc:
        raise credentials_exc from exc
    user_id = payload.get("sub")
    if not user_id:
        raise credentials_exc
    user = db.get(User, user_id)
    if user is None or not user.is_active:
        raise credentials_exc
    return user
