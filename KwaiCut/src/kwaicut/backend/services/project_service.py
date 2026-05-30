"""Project, version-history and draft-recovery logic."""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from kwaicut.backend.schemas import ProjectCreate, ProjectUpdate, VersionCreate
from kwaicut.common.errors import ValidationError
from kwaicut.db.models import Project, ProjectVersion, User


def create_project(db: Session, owner: User, data: ProjectCreate) -> Project:
    project = Project(
        owner_id=owner.id,
        name=data.name,
        description=data.description,
        width=data.width,
        height=data.height,
        fps=data.fps,
    )
    db.add(project)
    db.flush()
    return project


def list_projects(db: Session, owner: User, *, drafts_only: bool = False) -> list[Project]:
    stmt = select(Project).where(Project.owner_id == owner.id).order_by(Project.updated_at.desc())
    if drafts_only:
        stmt = stmt.where(Project.is_draft.is_(True))
    return list(db.scalars(stmt))


def get_owned_project(db: Session, owner: User, project_id: str) -> Project:
    project = db.get(Project, project_id)
    if project is None or project.owner_id != owner.id:
        raise ValidationError("project not found")
    return project


def update_project(db: Session, project: Project, data: ProjectUpdate) -> Project:
    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(project, field, value)
    db.flush()
    return project


def delete_project(db: Session, project: Project) -> None:
    db.delete(project)


def save_version(
    db: Session, project: Project, data: VersionCreate, author: User
) -> ProjectVersion:
    """Append an immutable timeline snapshot (auto-incrementing revision)."""
    next_revision = (
        max((v.revision for v in project.versions), default=0) + 1
    )
    version = ProjectVersion(
        project_id=project.id,
        revision=next_revision,
        label=data.label or f"Revision {next_revision}",
        timeline_json=data.timeline_json,
        author_id=author.id,
    )
    db.add(version)
    project.is_draft = False
    db.flush()
    return version


def latest_version(db: Session, project: Project) -> ProjectVersion | None:
    stmt = (
        select(ProjectVersion)
        .where(ProjectVersion.project_id == project.id)
        .order_by(ProjectVersion.revision.desc())
        .limit(1)
    )
    return db.scalar(stmt)
