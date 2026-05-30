"""Asset marketplace routes."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from kwaicut.backend.dependencies import get_current_user
from kwaicut.backend.schemas import TemplateCreate, TemplateOut
from kwaicut.backend.services import marketplace_service
from kwaicut.common.errors import ValidationError
from kwaicut.db.base import get_db
from kwaicut.db.models import TemplateCategory, User

router = APIRouter(prefix="/api/marketplace", tags=["marketplace"])


@router.get("/templates", response_model=list[TemplateOut])
def list_templates(
    category: TemplateCategory | None = None,
    premium: bool | None = None,
    db: Session = Depends(get_db),
):
    return marketplace_service.list_templates(db, category=category, premium=premium)


@router.post("/templates", response_model=TemplateOut, status_code=status.HTTP_201_CREATED)
def publish(
    data: TemplateCreate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    return marketplace_service.publish_template(db, user, data)


@router.post("/templates/{template_id}/download", response_model=TemplateOut)
def download(template_id: str, db: Session = Depends(get_db)):
    try:
        return marketplace_service.download_template(db, template_id)
    except ValidationError as exc:
        raise HTTPException(status.HTTP_404_NOT_FOUND, str(exc)) from exc
