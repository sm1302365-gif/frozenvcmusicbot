"""Authentication routes: register, login, current user."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from kwaicut.backend.dependencies import get_current_user
from kwaicut.backend.schemas import Token, UserCreate, UserOut
from kwaicut.backend.security import create_access_token
from kwaicut.backend.services import auth_service
from kwaicut.common.errors import AuthError, ValidationError
from kwaicut.db.base import get_db
from kwaicut.db.models import User

router = APIRouter(prefix="/api/auth", tags=["auth"])


@router.post("/register", response_model=UserOut, status_code=status.HTTP_201_CREATED)
def register(data: UserCreate, db: Session = Depends(get_db)) -> User:
    try:
        return auth_service.register_user(db, data)
    except ValidationError as exc:
        raise HTTPException(status.HTTP_409_CONFLICT, str(exc)) from exc


@router.post("/login", response_model=Token)
def login(
    form: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db),
) -> Token:
    # OAuth2PasswordRequestForm uses `username`; we treat it as the email.
    try:
        user = auth_service.authenticate(db, form.username, form.password)
    except AuthError as exc:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, str(exc)) from exc
    return Token(access_token=create_access_token(user.id))


@router.get("/me", response_model=UserOut)
def me(current: User = Depends(get_current_user)) -> User:
    return current
