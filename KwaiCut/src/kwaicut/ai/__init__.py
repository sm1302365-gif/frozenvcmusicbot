"""Pluggable AI capabilities behind stable interfaces.

Typical usage::

    from kwaicut.ai import registry
    from kwaicut.ai.base import TranscriptionProvider

    provider = registry.get(TranscriptionProvider)
    transcript = provider.transcribe("clip.wav")
"""

from __future__ import annotations

from kwaicut.ai import registry
from kwaicut.ai.base import (
    GeneratedMedia,
    SceneCut,
    TextToSpeechProvider,
    TextToVideoProvider,
    Transcript,
    TranscriptionProvider,
    TranscriptSegment,
)
from kwaicut.ai.captions import AutoCaptions, transcript_to_srt

__all__ = [
    "registry",
    "GeneratedMedia",
    "SceneCut",
    "Transcript",
    "TranscriptSegment",
    "TranscriptionProvider",
    "TextToVideoProvider",
    "TextToSpeechProvider",
    "AutoCaptions",
    "transcript_to_srt",
]
