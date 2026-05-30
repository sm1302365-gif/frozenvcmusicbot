"""Caption generation and subtitle formatting.

Turns a :class:`~kwaicut.ai.base.Transcript` into industry-standard subtitle
files (SRT now; ASS — which supports the karaoke/animated/emoji styling in the
spec — is a natural extension). The :class:`AutoCaptions` service wires the
registered transcription provider to this formatter, which is exactly what the
"Auto Captions" button calls.
"""

from __future__ import annotations

from pathlib import Path

from kwaicut.ai import registry
from kwaicut.ai.base import Transcript, TranscriptionProvider


def _format_timestamp(seconds: float) -> str:
    """Format seconds as an SRT timestamp ``HH:MM:SS,mmm``."""
    millis = int(round(seconds * 1000))
    hours, millis = divmod(millis, 3_600_000)
    minutes, millis = divmod(millis, 60_000)
    secs, millis = divmod(millis, 1000)
    return f"{hours:02d}:{minutes:02d}:{secs:02d},{millis:03d}"


def transcript_to_srt(transcript: Transcript) -> str:
    """Render a transcript as an SRT subtitle document."""
    blocks: list[str] = []
    for index, segment in enumerate(transcript.segments, start=1):
        blocks.append(
            f"{index}\n"
            f"{_format_timestamp(segment.start)} --> {_format_timestamp(segment.end)}\n"
            f"{segment.text}\n"
        )
    return "\n".join(blocks)


class AutoCaptions:
    """High-level "generate captions for this clip" service."""

    def __init__(self, provider: TranscriptionProvider | None = None) -> None:
        self._provider = provider

    @property
    def provider(self) -> TranscriptionProvider:
        return self._provider or registry.get(TranscriptionProvider)

    def generate(
        self,
        audio_path: str | Path,
        output_srt: str | Path,
        language: str | None = None,
    ) -> Transcript:
        """Transcribe ``audio_path`` and write an SRT file next to it."""
        transcript = self.provider.transcribe(audio_path, language=language)
        Path(output_srt).write_text(transcript_to_srt(transcript), encoding="utf-8")
        return transcript
