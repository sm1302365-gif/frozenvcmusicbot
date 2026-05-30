"""SQLAlchemy engine, session factory and declarative base.

A single engine is created from :class:`~kwaicut.config.Settings.database_url`,
so the same code targets SQLite locally and PostgreSQL in production with no
changes. ``get_session`` is a context manager used by services; ``get_db`` is the
FastAPI dependency wrapper around it.
"""

from __future__ import annotations

from collections.abc import Iterator
from contextlib import contextmanager

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from kwaicut.config import get_settings


class Base(DeclarativeBase):
    """Declarative base shared by every ORM model."""


def _make_engine():
    settings = get_settings()
    connect_args = {}
    if settings.database_url.startswith("sqlite"):
        # Required so SQLite connections can be shared across threads (the
        # backend serves requests from a thread pool).
        connect_args = {"check_same_thread": False}
    return create_engine(settings.database_url, future=True, connect_args=connect_args)


engine = _make_engine()
SessionLocal = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False, future=True)


def init_db() -> None:
    """Create all tables. For real deployments use Alembic migrations instead."""
    from kwaicut.db import models  # noqa: F401  (register mappers)

    Base.metadata.create_all(bind=engine)


@contextmanager
def get_session() -> Iterator[Session]:
    """Provide a transactional scope around a series of operations."""
    session = SessionLocal()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


def get_db() -> Iterator[Session]:
    """FastAPI dependency that yields a request-scoped session."""
    with get_session() as session:
        yield session
