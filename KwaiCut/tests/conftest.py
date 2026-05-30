"""Shared pytest fixtures.

Environment variables are set *before* any ``kwaicut`` module is imported so the
cached settings and the SQLAlchemy engine bind to a throwaway, per-run SQLite
database instead of the developer's real one.
"""

from __future__ import annotations

import os
import tempfile
from pathlib import Path

_TMP = Path(tempfile.mkdtemp(prefix="kwaicut-tests-"))
os.environ.setdefault("KWAICUT_DATABASE_URL", f"sqlite:///{_TMP/'test.db'}")
os.environ.setdefault("KWAICUT_SECRET_KEY", "test-secret-key")
os.environ.setdefault("KWAICUT_MEDIA_ROOT", str(_TMP / "media"))
os.environ.setdefault("KWAICUT_EXPORT_ROOT", str(_TMP / "exports"))

import pytest  # noqa: E402

from kwaicut.db.base import Base, engine, init_db  # noqa: E402


@pytest.fixture(scope="session", autouse=True)
def _database() -> None:
    """Create all tables once for the test session."""
    init_db()
    yield
    Base.metadata.drop_all(bind=engine)


@pytest.fixture
def client():
    """A FastAPI TestClient with the app lifespan active."""
    from fastapi.testclient import TestClient

    from kwaicut.backend.app import app

    with TestClient(app) as test_client:
        yield test_client


@pytest.fixture
def auth_headers(client):
    """Register + log in a user and return Authorization headers."""
    import uuid

    email = f"user-{uuid.uuid4().hex[:8]}@example.com"
    password = "supersecret123"
    client.post("/api/auth/register", json={"email": email, "password": password})
    resp = client.post("/api/auth/login", data={"username": email, "password": password})
    token = resp.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}
