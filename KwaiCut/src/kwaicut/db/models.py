"""ORM models — the persistent KwaiCut data model.

Entity overview::

    User ──< Project ──< ProjectVersion        (version history / draft recovery)
     │         │
     │         └──< Asset                       (media in a project's library)
     │
     └──1 Subscription                          (Free / Premium / Enterprise plan)

    Template                                    (marketplace items, author = User)
    CollaborationSession ──< Project            (real-time editing rooms)

Timeline documents are stored as JSON on :class:`ProjectVersion`, so the editing
engine's model is the single source of truth and the DB never has to know about
clips or keyframes.
"""

from __future__ import annotations

import enum
import uuid
from datetime import UTC, datetime

from sqlalchemy import (
    JSON,
    Boolean,
    DateTime,
    Enum,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from kwaicut.db.base import Base


def _uuid() -> str:
    return uuid.uuid4().hex


def _now() -> datetime:
    return datetime.now(UTC)


class PlanTier(str, enum.Enum):
    FREE = "free"
    PREMIUM = "premium"
    ENTERPRISE = "enterprise"


class AssetKind(str, enum.Enum):
    VIDEO = "video"
    AUDIO = "audio"
    IMAGE = "image"
    FONT = "font"


class TemplateCategory(str, enum.Enum):
    TEMPLATE = "template"
    MOTION_GRAPHICS = "motion_graphics"
    INTRO = "intro"
    OUTRO = "outro"
    FONT = "font"
    STICKER = "sticker"
    SFX = "sfx"
    MUSIC = "music"


class TimestampMixin:
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=_now, onupdate=_now
    )


class User(Base, TimestampMixin):
    __tablename__ = "users"

    id: Mapped[str] = mapped_column(String(32), primary_key=True, default=_uuid)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    display_name: Mapped[str] = mapped_column(String(120), default="")
    hashed_password: Mapped[str] = mapped_column(String(255))
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    is_verified: Mapped[bool] = mapped_column(Boolean, default=False)

    subscription: Mapped[Subscription] = relationship(
        back_populates="user", uselist=False, cascade="all, delete-orphan"
    )
    projects: Mapped[list[Project]] = relationship(
        back_populates="owner", cascade="all, delete-orphan"
    )


class Subscription(Base, TimestampMixin):
    __tablename__ = "subscriptions"

    id: Mapped[str] = mapped_column(String(32), primary_key=True, default=_uuid)
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), unique=True)
    tier: Mapped[PlanTier] = mapped_column(Enum(PlanTier), default=PlanTier.FREE)
    ai_credits: Mapped[int] = mapped_column(Integer, default=100)
    cloud_storage_bytes: Mapped[int] = mapped_column(Integer, default=1_073_741_824)  # 1 GiB
    renews_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    user: Mapped[User] = relationship(back_populates="subscription")


class Project(Base, TimestampMixin):
    __tablename__ = "projects"

    id: Mapped[str] = mapped_column(String(32), primary_key=True, default=_uuid)
    owner_id: Mapped[str] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    name: Mapped[str] = mapped_column(String(200), default="Untitled Project")
    description: Mapped[str] = mapped_column(Text, default="")
    is_draft: Mapped[bool] = mapped_column(Boolean, default=True)
    is_cloud_synced: Mapped[bool] = mapped_column(Boolean, default=False)
    width: Mapped[int] = mapped_column(Integer, default=1920)
    height: Mapped[int] = mapped_column(Integer, default=1080)
    fps: Mapped[float] = mapped_column(Float, default=30.0)

    owner: Mapped[User] = relationship(back_populates="projects")
    assets: Mapped[list[Asset]] = relationship(
        back_populates="project", cascade="all, delete-orphan"
    )
    versions: Mapped[list[ProjectVersion]] = relationship(
        back_populates="project", cascade="all, delete-orphan", order_by="ProjectVersion.revision"
    )


class ProjectVersion(Base, TimestampMixin):
    """An immutable snapshot of a project's timeline (version history)."""

    __tablename__ = "project_versions"

    id: Mapped[str] = mapped_column(String(32), primary_key=True, default=_uuid)
    project_id: Mapped[str] = mapped_column(
        ForeignKey("projects.id", ondelete="CASCADE"), index=True
    )
    revision: Mapped[int] = mapped_column(Integer, default=1)
    label: Mapped[str] = mapped_column(String(200), default="")
    timeline_json: Mapped[dict] = mapped_column(JSON, default=dict)
    author_id: Mapped[str | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )

    project: Mapped[Project] = relationship(back_populates="versions")


class Asset(Base, TimestampMixin):
    __tablename__ = "assets"

    id: Mapped[str] = mapped_column(String(32), primary_key=True, default=_uuid)
    project_id: Mapped[str] = mapped_column(
        ForeignKey("projects.id", ondelete="CASCADE"), index=True
    )
    kind: Mapped[AssetKind] = mapped_column(Enum(AssetKind))
    name: Mapped[str] = mapped_column(String(255))
    storage_path: Mapped[str] = mapped_column(String(1024))
    duration_seconds: Mapped[float] = mapped_column(Float, default=0.0)
    width: Mapped[int] = mapped_column(Integer, default=0)
    height: Mapped[int] = mapped_column(Integer, default=0)
    size_bytes: Mapped[int] = mapped_column(Integer, default=0)

    project: Mapped[Project] = relationship(back_populates="assets")


class Template(Base, TimestampMixin):
    """A marketplace item (template, intro pack, font, sound effect, ...)."""

    __tablename__ = "templates"

    id: Mapped[str] = mapped_column(String(32), primary_key=True, default=_uuid)
    author_id: Mapped[str | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    title: Mapped[str] = mapped_column(String(200), index=True)
    description: Mapped[str] = mapped_column(Text, default="")
    category: Mapped[TemplateCategory] = mapped_column(Enum(TemplateCategory))
    is_premium: Mapped[bool] = mapped_column(Boolean, default=False)
    price_cents: Mapped[int] = mapped_column(Integer, default=0)
    downloads: Mapped[int] = mapped_column(Integer, default=0)
    preview_url: Mapped[str] = mapped_column(String(1024), default="")
    payload_json: Mapped[dict] = mapped_column(JSON, default=dict)


class CollaborationSession(Base, TimestampMixin):
    """A live, multi-user editing room for a project."""

    __tablename__ = "collaboration_sessions"

    id: Mapped[str] = mapped_column(String(32), primary_key=True, default=_uuid)
    project_id: Mapped[str] = mapped_column(
        ForeignKey("projects.id", ondelete="CASCADE"), index=True
    )
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
