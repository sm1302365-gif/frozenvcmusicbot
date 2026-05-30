# KwaiCut Architecture

KwaiCut is organised into independent layers with one-directional dependencies.
Lower layers never import higher ones, which keeps the editing engine reusable
from the CLI, the backend and the desktop client alike.

```
            ┌─────────────┐      ┌─────────────┐
            │  desktop/   │      │   cli.py    │
            │  (PyQt6)    │      │             │
            └──────┬──────┘      └──────┬──────┘
                   │                    │
                   ▼                    ▼
            ┌──────────────────────────────────┐
            │            backend/               │   FastAPI: HTTP + WebSocket
            │  auth · projects · marketplace ·  │
            │  subscriptions · collaboration ·  │
            │  ai routes                        │
            └───────┬───────────────┬───────────┘
                    │               │
          ┌─────────▼──────┐   ┌────▼─────────┐
          │     core/      │   │     ai/      │   pluggable providers
          │ timeline +     │   │ transcription│
          │ rendering      │   │ generators…  │
          └─────────┬──────┘   └────┬─────────┘
                    │               │
                    ▼               ▼
            ┌──────────────────────────────────┐
            │              db/                  │   SQLAlchemy 2.0
            └──────────────────────────────────┘
                          │
                          ▼
            ┌──────────────────────────────────┐
            │            common/                │   config · types · errors · logging
            └──────────────────────────────────┘
```

## Design principles

- **Model / engine / storage separation.** The timeline model
  (`core/timeline`) describes *what* the edit is. The renderer
  (`core/rendering`) decides *how* to produce pixels. The database (`db`) decides
  *how* to persist it. Each can change without touching the others. Timeline
  objects are plain dataclasses with `to_dict()` so they serialise to JSON for
  storage, cloud sync and version-history diffing.

- **Microsecond time base.** All timing uses `TimeCode` (integer microseconds)
  to avoid floating-point drift across thousands of edits, with helpers to
  convert to/from frames at any frame rate.

- **Pluggable AI.** Every AI capability is an abstract provider
  (`ai/base.py`). Concrete providers are bound at runtime via a small registry
  (`ai/registry.py`), so a local Whisper model, an ONNX runtime model or a hosted
  API are interchangeable without touching callers.

- **Thin routes, fat services.** FastAPI route handlers only parse, dispatch and
  serialise. Business rules live in `backend/services/*`, which are reusable from
  the desktop client and unit-testable without the web server.

- **12-factor config.** A single `Settings` object (`config.py`) reads every
  value from the environment, so the same code runs on a laptop (SQLite) and in
  production (PostgreSQL) with no changes.

## The rendering pipeline

1. `RenderEngine.compile(timeline, output, preset)` walks the timeline and emits
   a single FFmpeg `-filter_complex` graph: per-clip `trim` + `setpts`/`atempo`
   (+ `reverse`), video clips `scale`d and `overlay`'d onto a base canvas in
   track order, audio clips `adelay`'d, gain-adjusted and `amix`'d.
2. The result is a pure `list[str]` of arguments (no process spawned) — trivially
   unit-testable.
3. `ExportPipeline` runs that command through the `FFmpeg` wrapper, parsing
   `-progress` output into a 0–1 fraction, and supports sequential batch jobs.

## Real-time collaboration

`CollaborationManager` keeps an in-memory map of project rooms → connected
WebSocket peers and rebroadcasts each edit event to the other peers. The
interface is deliberately small so a multi-process deployment can swap the
in-memory fan-out for Redis pub/sub without changing the route.

## Testing strategy

Pure logic (timeline ops, keyframe interpolation, render-graph compilation,
captions formatting, JWT/bcrypt) is unit-tested directly. The HTTP API is tested
end-to-end with FastAPI's `TestClient` against a throwaway SQLite database. The
FFmpeg integration is verified by a smoke run that generates media, composites a
timeline and exports a real MP4.
