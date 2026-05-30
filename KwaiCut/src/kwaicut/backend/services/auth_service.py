"""User registration and authentication business logic."""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from kwaicut.backend.schemas import UserCreate
from kwaicut.backend.security import hash_password, verify_password
from kwaicut.common.errors import AuthError, ValidationError
from kwaicut.db.models import PlanTier, Subscription, User


def register_user(db: Session, data: UserCreate) -> User:
    """Create a new user with a default Free subscription."""
    existing = db.scalar(select(User).where(User.email == data.email))
    if existing is not None:
        raise ValidationError("a user with this email already exists")

    user = User(
        email=data.email,
        display_name=data.display_name or data.email.split("@")[0],
        hashed_password=hash_password(data.password),
    )
    user.subscription = Subscription(tier=PlanTier.FREE)
    db.add(user)
    db.flush()
    return user


def authenticate(db: Session, email: str, password: str) -> User:
    """Return the user if credentials are valid, else raise :class:`AuthError`."""
    user = db.scalar(select(User).where(User.email == email))
    if user is None or not verify_password(password, user.hashed_password):
        raise AuthError("invalid email or password")
    if not user.is_active:
        raise AuthError("account is disabled")
    return user
