"""Centralised, environment-driven configuration.

Settings are loaded once and cached. Every value can be overridden through an
environment variable prefixed with ``KWAICUT_`` or via a local ``.env`` file,
which keeps secrets out of source control and makes the app 12-factor friendly.
"""

from __future__ import annotations

from enum import Enum
from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Environment(str, Enum):
    """Deployment environment the process is running in."""

    DEVELOPMENT = "development"
    STAGING = "staging"
    PRODUCTION = "production"


class Settings(BaseSettings):
    """Strongly-typed application settings.

    Instantiated through :func:`get_settings` so the values are parsed and
    validated exactly once per process.
    """

    model_config = SettingsConfigDict(
        env_prefix="KWAICUT_",
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # -- General -----------------------------------------------------------
    env: Environment = Environment.DEVELOPMENT
    debug: bool = True
    app_name: str = "KwaiCut"

    # -- Persistence -------------------------------------------------------
    database_url: str = "sqlite:///./kwaicut.db"

    # -- Auth --------------------------------------------------------------
    secret_key: str = "change-me-in-production"
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 60
    refresh_token_expire_days: int = 14

    # -- Storage -----------------------------------------------------------
    media_root: Path = Path("./var/media")
    export_root: Path = Path("./var/exports")

    # -- External binaries -------------------------------------------------
    ffmpeg_binary: str = "ffmpeg"
    ffprobe_binary: str = "ffprobe"

    # -- AI ----------------------------------------------------------------
    whisper_model: str = "base"
    openai_api_key: str = ""
    ai_device: str = "auto"

    @property
    def is_production(self) -> bool:
        return self.env is Environment.PRODUCTION

    def ensure_directories(self) -> None:
        """Create the storage roots if they do not yet exist."""
        for path in (self.media_root, self.export_root):
            path.mkdir(parents=True, exist_ok=True)


@lru_cache
def get_settings() -> Settings:
    """Return the cached, process-wide :class:`Settings` instance."""
    return Settings()
