"""Pydantic request/response models for the HTTP API.

These define the public contract of the backend and are intentionally separate
from the SQLAlchemy ORM models (which are an internal detail). ``from_attributes``
lets us return ORM objects directly from route handlers.
"""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field

from kwaicut.db.models import AssetKind, PlanTier, TemplateCategory


class _ORMModel(BaseModel):
    model_config = ConfigDict(from_attributes=True)


# -- Auth ------------------------------------------------------------------
class UserCreate(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)
    display_name: str = ""


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


class UserOut(_ORMModel):
    id: str
    email: EmailStr
    display_name: str
    is_active: bool
    is_verified: bool


# -- Subscription ----------------------------------------------------------
class SubscriptionOut(_ORMModel):
    tier: PlanTier
    ai_credits: int
    cloud_storage_bytes: int
    renews_at: datetime | None


# -- Projects --------------------------------------------------------------
class ProjectCreate(BaseModel):
    name: str = "Untitled Project"
    description: str = ""
    width: int = 1920
    height: int = 1080
    fps: float = 30.0


class ProjectUpdate(BaseModel):
    name: str | None = None
    description: str | None = None
    is_draft: bool | None = None
    is_cloud_synced: bool | None = None


class ProjectOut(_ORMModel):
    id: str
    name: str
    description: str
    is_draft: bool
    is_cloud_synced: bool
    width: int
    height: int
    fps: float
    created_at: datetime
    updated_at: datetime


class VersionCreate(BaseModel):
    label: str = ""
    timeline_json: dict = Field(default_factory=dict)


class VersionOut(_ORMModel):
    id: str
    revision: int
    label: str
    timeline_json: dict
    created_at: datetime


# -- Assets ----------------------------------------------------------------
class AssetOut(_ORMModel):
    id: str
    kind: AssetKind
    name: str
    storage_path: str
    duration_seconds: float
    width: int
    height: int
    size_bytes: int


# -- Marketplace -----------------------------------------------------------
class TemplateCreate(BaseModel):
    title: str
    description: str = ""
    category: TemplateCategory
    is_premium: bool = False
    price_cents: int = 0
    preview_url: str = ""
    payload_json: dict = Field(default_factory=dict)


class TemplateOut(_ORMModel):
    id: str
    title: str
    description: str
    category: TemplateCategory
    is_premium: bool
    price_cents: int
    downloads: int
    preview_url: str
