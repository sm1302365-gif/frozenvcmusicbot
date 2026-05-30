# Deployment

## Local (SQLite)

```bash
python -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"
kwaicut initdb
kwaicut serve            # http://localhost:8000/docs
```

## Docker Compose (backend + PostgreSQL)

```bash
docker compose -f deploy/docker-compose.yml up --build
```

This builds the backend image from [`deploy/Dockerfile.backend`](../deploy/Dockerfile.backend)
(which installs `ffmpeg`), starts PostgreSQL, and runs the API on port 8000. The
backend creates tables on startup via the lifespan hook; for controlled schema
changes use Alembic (see [`DATABASE.md`](DATABASE.md)).

## Production notes

- **Secrets.** Always set a strong `KWAICUT_SECRET_KEY` and a real
  `KWAICUT_DATABASE_URL`. Never ship the development defaults.
- **ASGI server.** The image runs `uvicorn`. For multiple workers front it with
  `gunicorn -k uvicorn.workers.UvicornWorker -w 4 kwaicut.backend.app:app`.
- **Object storage.** `KWAICUT_MEDIA_ROOT` / `KWAICUT_EXPORT_ROOT` default to the
  local filesystem; mount a volume or back them with S3-compatible storage.
- **Scaling collaboration.** The WebSocket fan-out is in-memory (single process).
  For horizontal scaling, back `CollaborationManager` with Redis pub/sub behind
  the same interface.
- **GPU / AI.** Install the `[ai]` extra in a CUDA-enabled base image and set
  `KWAICUT_AI_DEVICE=cuda` to run Whisper and other models on the GPU. Heavy
  rendering is best offloaded to dedicated worker nodes.

## CI

[`.github/workflows/kwaicut.yml`](../../.github/workflows/kwaicut.yml) installs
the `[dev]` extra, runs `ruff` and the full `pytest` suite on every push/PR that
touches `KwaiCut/`.
