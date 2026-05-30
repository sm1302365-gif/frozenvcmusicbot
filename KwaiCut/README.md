# KwaiCut

**KwaiCut** is a professional, AI-powered video editing platform. This repository
contains a production-grade **foundation**: a clean, modular, well-tested
architecture that implements the core editing engine, backend services and
desktop shell, with stable interfaces for the large surface of AI features.

> ⚠️ **Scope.** The full product vision (every generative AI model, 10,000+
> effects, cross-platform mobile builds, cloud rendering) is a multi-year effort.
> What ships here is a *real, runnable* core that those features plug into — not a
> mock. Core editing, the FFmpeg render/export pipeline, auth, projects,
> marketplace, real-time collaboration and Whisper-based captioning all work
> end-to-end today. Generative features ship as well-defined provider interfaces
> with working local/placeholder implementations you can swap for hosted models.

---

## Architecture at a glance

```
src/kwaicut/
├── common/      Shared primitives: config, value types, errors, logging
├── core/        The editing engine
│   ├── timeline/    Model (clips/tracks/keyframes) + operations (split/trim/ripple)
│   └── rendering/   FFmpeg wrapper, filter-graph compiler, export pipeline & presets
├── ai/          Pluggable AI providers behind stable interfaces (+ Whisper captions)
├── db/          SQLAlchemy 2.0 models + session management
├── backend/     FastAPI service: auth, projects, marketplace, subscriptions, WS collab
├── desktop/     PyQt6 client: dashboard, timeline view, AI panel (dark/glassmorphism)
└── cli.py       Operational entry points (serve, initdb, captions, version)
```

See [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md) for the full design, and the
other files in [`docs/`](docs/) for the database schema, HTTP API, AI module
design and deployment.

## What actually works today

| Area | Status |
| --- | --- |
| Multi-track timeline model (video/audio, keyframes, blend modes, transforms) | ✔ implemented + tested |
| Non-destructive operations: split, trim, ripple-delete, speed ramping | ✔ implemented + tested |
| FFmpeg render engine (filter-graph compositing) + export pipeline | ✔ implemented + tested |
| Export presets: 720p–8K, H.264/H.265/ProRes/VP9, MP4/MOV/MKV, HDR, transparent, batch | ✔ implemented |
| Auth (register/login, JWT, bcrypt) | ✔ implemented + tested |
| Projects, version history, draft recovery | ✔ implemented + tested |
| Asset marketplace (publish/list/download) | ✔ implemented + tested |
| Subscriptions (Free/Premium/Enterprise entitlements) | ✔ implemented + tested |
| Real-time collaboration (WebSocket rooms + presence) | ✔ implemented + tested |
| AI auto-captions via local Whisper (SRT export) | ✔ implemented (optional `[ai]` extra) |
| AI generators (text-to-video, TTS/voice) | ✔ pipeline works via placeholder providers; swap in hosted models |
| PyQt6 desktop shell | ✔ implemented (optional `[desktop]` extra) |

## Quick start

```bash
# 1. Install (core + backend + dev tooling). Python 3.12+ and ffmpeg required.
python -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"

# 2. Run the tests and linter.
pytest
ruff check src tests

# 3. Initialise the database and run the API.
kwaicut initdb
kwaicut serve            # http://localhost:8000/docs

# 4. (optional) Desktop client and AI features.
pip install -e ".[desktop,ai]"
kwaicut-desktop
kwaicut captions input.wav output.srt
```

## Configuration

All settings are environment-driven (prefix `KWAICUT_`) with sensible local
defaults. Copy [`.env.example`](.env.example) to `.env` and adjust. SQLite is the
default datastore; set `KWAICUT_DATABASE_URL` to a PostgreSQL URL in production.

## Optional extras

| Extra | Installs | Enables |
| --- | --- | --- |
| `desktop` | PyQt6 | the desktop client |
| `ai` | torch, whisper, onnxruntime, opencv | local AI (captions, etc.) |
| `postgres` | psycopg2 | PostgreSQL driver |
| `dev` | pytest, ruff, mypy | tests, lint, type-check |

## License

MIT.
