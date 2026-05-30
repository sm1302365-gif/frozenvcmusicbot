"""Asset marketplace logic: listing, publishing and downloading templates."""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from kwaicut.backend.schemas import TemplateCreate
from kwaicut.common.errors import ValidationError
from kwaicut.db.models import Template, TemplateCategory, User


def publish_template(db: Session, author: User, data: TemplateCreate) -> Template:
    template = Template(
        author_id=author.id,
        title=data.title,
        description=data.description,
        category=data.category,
        is_premium=data.is_premium,
        price_cents=data.price_cents,
        preview_url=data.preview_url,
        payload_json=data.payload_json,
    )
    db.add(template)
    db.flush()
    return template


def list_templates(
    db: Session,
    *,
    category: TemplateCategory | None = None,
    premium: bool | None = None,
    limit: int = 50,
) -> list[Template]:
    stmt = select(Template).order_by(Template.downloads.desc()).limit(limit)
    if category is not None:
        stmt = stmt.where(Template.category == category)
    if premium is not None:
        stmt = stmt.where(Template.is_premium.is_(premium))
    return list(db.scalars(stmt))


def download_template(db: Session, template_id: str) -> Template:
    template = db.get(Template, template_id)
    if template is None:
        raise ValidationError("template not found")
    template.downloads += 1
    db.flush()
    return template
