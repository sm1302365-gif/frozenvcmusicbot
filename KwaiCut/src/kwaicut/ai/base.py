"""Stable interfaces for every AI capability in KwaiCut.

The product spec lists dozens of AI features (text-to-video, voice cloning,
object removal, ...). Rather than hard-wire any single vendor, each capability is
expressed as an abstract *provider* here. Concrete providers — a local Whisper
model, an ONNX scene detector, a hosted diffusion API — implement these and are
swapped in via :mod:`kwaicut.ai.registry`. This keeps the editing engine
completely decoupled from which model actually does the work.
"""

from __future__ import annotations

import abc
from dataclasses import dataclass, field
from pathlib import Path


# --------------------------------------------------------------------------- #
# Result value objects
# --------------------------------------------------------------------------- #
@dataclass(frozen=True)
class TranscriptSegment:
    """A single timed span of recognised speech."""

    start: float
    end: float
    text: str


@dataclass(frozen=True)
class Transcript:
    """A full transcription result."""

    language: str
    segments: list[TranscriptSegment]

    @property
    def text(self) -> str:
        return " ".join(s.text.strip() for s in self.segments).strip()


@dataclass(frozen=True)
class SceneCut:
    """A detected scene boundary, in seconds from the start of the clip."""

    timestamp: float
    score: float


@dataclass(frozen=True)
class GeneratedMedia:
    """Output of a generative provider (video/audio/image)."""

    path: Path
    duration_seconds: float = 0.0
    metadata: dict = field(default_factory=dict)


# --------------------------------------------------------------------------- #
# Provider interfaces
# --------------------------------------------------------------------------- #
class AIProvider(abc.ABC):
    """Marker base class with a stable, human-readable name."""

    name: str = "abstract"

    @property
    def available(self) -> bool:
        """Whether the provider's dependencies/credentials are present."""
        return True


class TranscriptionProvider(AIProvider):
    """Speech-to-text (powers auto-captions, dubbing, search)."""

    @abc.abstractmethod
    def transcribe(self, audio_path: str | Path, language: str | None = None) -> Transcript:
        ...


class SceneDetectionProvider(AIProvider):
    """Smart scene / shot boundary detection."""

    @abc.abstractmethod
    def detect_scenes(self, video_path: str | Path) -> list[SceneCut]:
        ...


class TextToVideoProvider(AIProvider):
    """Generative text-to-video."""

    @abc.abstractmethod
    def generate(self, prompt: str, *, seconds: float, output: Path) -> GeneratedMedia:
        ...


class TextToSpeechProvider(AIProvider):
    """Text-to-speech / dubbing / voice generation."""

    @abc.abstractmethod
    def synthesize(self, text: str, *, voice: str, output: Path) -> GeneratedMedia:
        ...
