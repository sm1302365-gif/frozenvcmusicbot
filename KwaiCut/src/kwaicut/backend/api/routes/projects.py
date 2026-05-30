"""Project CRUD, version history and draft recovery routes."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from kwaicut.backend.dependencies import get_current_user
from kwaicut.backend.schemas import (
    ProjectCreate,
    ProjectOut,
    ProjectUpdate,
    VersionCreate,
    VersionOut,
)
from kwaicut.backend.services import project_service
from kwaicut.common.errors import ValidationError
from kwaicut.db.base import get_db
from kwaicut.db.models import User

router = APIRouter(prefix="/api/projects", tags=["projects"])


@router.post("", response_model=ProjectOut, status_code=status.HTTP_201_CREATED)
def create(
    data: ProjectCreate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    return project_service.create_project(db, user, data)


@router.get("", response_model=list[ProjectOut])
def list_all(
    drafts_only: bool = False,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    return project_service.list_projects(db, user, drafts_only=drafts_only)


@router.get("/{project_id}", response_model=ProjectOut)
def get_one(project_id: str, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    try:
        return project_service.get_owned_project(db, user, project_id)
    except ValidationError as exc:
        raise HTTPException(status.HTTP_404_NOT_FOUND, str(exc)) from exc


@router.patch("/{project_id}", response_model=ProjectOut)
def update(
    project_id: str,
    data: ProjectUpdate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    try:
        project = project_service.get_owned_project(db, user, project_id)
    except ValidationError as exc:
        raise HTTPException(status.HTTP_404_NOT_FOUND, str(exc)) from exc
    return project_service.update_project(db, project, data)


@router.delete("/{project_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete(project_id: str, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    try:
        project = project_service.get_owned_project(db, user, project_id)
    except ValidationError as exc:
        raise HTTPException(status.HTTP_404_NOT_FOUND, str(exc)) from exc
    project_service.delete_project(db, project)


@router.post(
    "/{project_id}/versions",
    response_model=VersionOut,
    status_code=status.HTTP_201_CREATED,
)
def save_version(
    project_id: str,
    data: VersionCreate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    try:
        project = project_service.get_owned_project(db, user, project_id)
    except ValidationError as exc:
        raise HTTPException(status.HTTP_404_NOT_FOUND, str(exc)) from exc
    return project_service.save_version(db, project, data, user)


@router.get("/{project_id}/versions", response_model=list[VersionOut])
def list_versions(
    project_id: str,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    try:
        project = project_service.get_owned_project(db, user, project_id)
    except ValidationError as exc:
        raise HTTPException(status.HTTP_404_NOT_FOUND, str(exc)) from exc
    return project.versions
