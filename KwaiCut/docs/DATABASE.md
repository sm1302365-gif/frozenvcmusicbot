# Database Schema

KwaiCut uses SQLAlchemy 2.0 (typed `Mapped` columns). SQLite is the default for
local development; point `KWAICUT_DATABASE_URL` at PostgreSQL for production.
Models live in [`src/kwaicut/db/models.py`](../src/kwaicut/db/models.py).

## Entity relationship overview

```
User ──1:1── Subscription
  │
  ├──1:N── Project ──1:N── ProjectVersion   (immutable timeline snapshots)
  │            └──1:N── Asset               (media library for the project)
  │
  └──1:N── Template                         (marketplace items authored by user)

Project ──1:N── CollaborationSession        (live editing rooms)
```

## Tables

### `users`
| column | type | notes |
| --- | --- | --- |
| id | str(32) PK | uuid hex |
| email | str(255) | unique, indexed |
| display_name | str(120) | |
| hashed_password | str(255) | bcrypt |
| is_active / is_verified | bool | |
| created_at / updated_at | datetime | |

### `subscriptions`
One row per user. `tier` ∈ `free | premium | enterprise`. `ai_credits` and
`cloud_storage_bytes` capture plan entitlements (a large sentinel = "unlimited").

### `projects`
Owned by a user. Stores canvas settings (`width`, `height`, `fps`), `is_draft`
(for **draft recovery**) and `is_cloud_synced` (for **cloud projects**).

### `project_versions`
Append-only **version history**. Each row is an immutable snapshot with an
auto-incrementing `revision` and the full timeline document in `timeline_json`
(JSON). This powers undo across sessions, approval workflows and draft recovery.

### `assets`
Per-project media (`video | audio | image | font`) with probed metadata
(`duration_seconds`, `width`, `height`, `size_bytes`) and a `storage_path`.

### `templates`
The **asset marketplace**. `category` covers templates, motion graphics, intro/
outro packs, fonts, stickers, SFX and music. `is_premium` / `price_cents` gate
purchases; `downloads` tracks popularity; `payload_json` holds the item data.

### `collaboration_sessions`
Tracks active real-time editing rooms for a project.

## Migrations

`init_db()` (and `kwaicut initdb`) create tables directly for local development.
For real deployments use **Alembic** (already a dependency) — generate the first
revision with:

```bash
alembic init migrations          # one-time
alembic revision --autogenerate -m "initial schema"
alembic upgrade head
```

Timeline structure (clips, keyframes, effects) is intentionally **not** modelled
as relational tables — it is stored as JSON on `project_versions`, keeping the
editing engine the single source of truth and avoiding schema churn as the model
evolves.
