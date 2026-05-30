"""FastAPI application factory and entry point.

``create_app`` wires the routers, middleware and startup hooks together and is
imported by both the ASGI server (``kwaicut.backend.app:app``) and the test
suite. ``run`` is the console-script used for local development.
"""

from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from kwaicut import __version__
from kwaicut.backend.api.routes import (
    ai,
    auth,
    collaboration,
    marketplace,
    projects,
    subscriptions,
)
from kwaicut.common.logging_config import get_logger
from kwaicut.config import get_settings
from kwaicut.db.base import init_db

logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialise storage and database tables on startup."""
    settings = get_settings()
    settings.ensure_directories()
    init_db()
    logger.info("KwaiCut backend started (env=%s)", settings.env.value)
    yield


def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(
        title="KwaiCut API",
        version=__version__,
        description="Backend for the KwaiCut AI video editing platform.",
        lifespan=lifespan,
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"] if not settings.is_production else [],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(auth.router)
    app.include_router(projects.router)
    app.include_router(marketplace.router)
    app.include_router(subscriptions.router)
    app.include_router(ai.router)
    app.include_router(collaboration.router)

    @app.get("/health", tags=["meta"])
    def health() -> dict:
        return {"status": "ok", "version": __version__, "env": settings.env.value}

    return app


app = create_app()


def run() -> None:  # pragma: no cover - convenience launcher
    import uvicorn

    uvicorn.run("kwaicut.backend.app:app", host="0.0.0.0", port=8000, reload=True)


if __name__ == "__main__":  # pragma: no cover
    run()
