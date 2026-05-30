from __future__ import annotations


def test_health(client):
    resp = client.get("/health")
    assert resp.status_code == 200
    assert resp.json()["status"] == "ok"


def test_register_and_login(client):
    email = "alice@example.com"
    r = client.post("/api/auth/register", json={"email": email, "password": "password123"})
    assert r.status_code == 201
    assert r.json()["email"] == email

    # Duplicate registration is rejected.
    dup = client.post("/api/auth/register", json={"email": email, "password": "password123"})
    assert dup.status_code == 409

    login = client.post("/api/auth/login", data={"username": email, "password": "password123"})
    assert login.status_code == 200
    assert "access_token" in login.json()


def test_me_requires_auth(client):
    assert client.get("/api/auth/me").status_code == 401


def test_project_crud_flow(client, auth_headers):
    created = client.post("/api/projects", json={"name": "My Edit"}, headers=auth_headers)
    assert created.status_code == 201
    project_id = created.json()["id"]

    listed = client.get("/api/projects", headers=auth_headers)
    assert any(p["id"] == project_id for p in listed.json())

    patched = client.patch(
        f"/api/projects/{project_id}", json={"name": "Renamed"}, headers=auth_headers
    )
    assert patched.json()["name"] == "Renamed"

    # Save a timeline version (version history / draft recovery).
    version = client.post(
        f"/api/projects/{project_id}/versions",
        json={"label": "v1", "timeline_json": {"tracks": []}},
        headers=auth_headers,
    )
    assert version.status_code == 201
    assert version.json()["revision"] == 1

    deleted = client.delete(f"/api/projects/{project_id}", headers=auth_headers)
    assert deleted.status_code == 204


def test_subscription_upgrade(client, auth_headers):
    sub = client.get("/api/subscription", headers=auth_headers)
    assert sub.json()["tier"] == "free"

    upgraded = client.post("/api/subscription/upgrade?tier=premium", headers=auth_headers)
    assert upgraded.status_code == 200
    assert upgraded.json()["tier"] == "premium"


def test_marketplace_publish_and_list(client, auth_headers):
    published = client.post(
        "/api/marketplace/templates",
        json={"title": "Neon Intro", "category": "intro", "is_premium": True},
        headers=auth_headers,
    )
    assert published.status_code == 201
    template_id = published.json()["id"]

    listing = client.get("/api/marketplace/templates")
    assert any(t["id"] == template_id for t in listing.json())

    downloaded = client.post(f"/api/marketplace/templates/{template_id}/download")
    assert downloaded.json()["downloads"] == 1
