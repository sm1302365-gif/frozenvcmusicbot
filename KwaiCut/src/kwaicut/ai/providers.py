"""Built-in default providers.

Two kinds ship in the box:

* **Real, local** providers that work offline — most importantly Whisper speech
  recognition (used by auto-captions and dubbing).
* **Placeholder generators** for the heavyweight generative features
  (text-to-video, text-to-speech). These produce a valid media file via FFmpeg
  so the *pipeline* is fully exercised and demoable, while clearly advertising
  themselves as placeholders. Swap in a hosted model by calling
  :func:`kwaicut.ai.registry.register` at startup.
"""

from __future__ import annotations

import math
import subprocess
import wave
from pathlib import Path

from kwaicut.ai.base import (
    GeneratedMedia,
    TextToSpeechProvider,
    TextToVideoProvider,
    Transcript,
    TranscriptionProvider,
    TranscriptSegment,
)
from kwaicut.common.errors import AIProviderError
from kwaicut.common.logging_config import get_logger
from kwaicut.config import get_settings

logger = get_logger(__name__)


class WhisperTranscriptionProvider(TranscriptionProvider):
    """Local speech-to-text powered by openai-whisper.

    The model is loaded lazily on first use and cached. If whisper/torch are not
    installed the provider reports itself unavailable instead of crashing import.
    """

    name = "whisper-local"

    def __init__(self, model_name: str | None = None) -> None:
        self._model_name = model_name or get_settings().whisper_model
        self._model = None

    @property
    def available(self) -> bool:
        try:
            import whisper  # noqa: F401
        except ImportError:
            return False
        return True

    def _load(self):
        if self._model is None:
            try:
                import whisper
            except ImportError as exc:  # pragma: no cover - env dependent
                raise AIProviderError(
                    "openai-whisper is not installed; `pip install kwaicut[ai]`"
                ) from exc
            logger.info("loading whisper model %s", self._model_name)
            self._model = whisper.load_model(self._model_name)
        return self._model

    def transcribe(self, audio_path, language=None) -> Transcript:
        model = self._load()
        result = model.transcribe(str(audio_path), language=language)
        segments = [
            TranscriptSegment(
                start=float(s["start"]), end=float(s["end"]), text=str(s["text"]).strip()
            )
            for s in result.get("segments", [])
        ]
        return Transcript(language=result.get("language", language or "en"), segments=segments)


class PlaceholderTextToVideo(TextToVideoProvider):
    """Generate a labelled colour-bars clip as a stand-in for real T2V."""

    name = "placeholder-t2v"

    def generate(self, prompt: str, *, seconds: float, output: Path) -> GeneratedMedia:
        output.parent.mkdir(parents=True, exist_ok=True)
        settings = get_settings()
        cmd = [
            settings.ffmpeg_binary, "-y", "-hide_banner", "-loglevel", "error",
            "-f", "lavfi", "-i", f"smptebars=size=1280x720:rate=30:duration={seconds:.2f}",
            "-vf", f"drawtext=text='{prompt[:48]}':x=20:y=20:fontsize=36:fontcolor=white",
            "-pix_fmt", "yuv420p", str(output),
        ]
        try:
            subprocess.run(cmd, check=True, capture_output=True)
        except (subprocess.CalledProcessError, FileNotFoundError) as exc:
            raise AIProviderError(f"placeholder t2v failed: {exc}") from exc
        return GeneratedMedia(path=output, duration_seconds=seconds, metadata={"prompt": prompt})


class PlaceholderTextToSpeech(TextToSpeechProvider):
    """Synthesize a short tone as a stand-in for real TTS/voice generation.

    Writes a valid mono WAV using only the stdlib so it works with zero external
    dependencies (handy for tests and offline demos).
    """

    name = "placeholder-tts"

    def synthesize(self, text: str, *, voice: str, output: Path) -> GeneratedMedia:
        output.parent.mkdir(parents=True, exist_ok=True)
        sample_rate = 16000
        seconds = max(1.0, min(10.0, len(text) / 15))
        frames = int(sample_rate * seconds)
        freq = 220.0 + (hash(voice) % 220)
        with wave.open(str(output), "w") as wav:
            wav.setnchannels(1)
            wav.setsampwidth(2)
            wav.setframerate(sample_rate)
            for i in range(frames):
                sample = int(32767 * 0.2 * math.sin(2 * math.pi * freq * i / sample_rate))
                wav.writeframes(sample.to_bytes(2, "little", signed=True))
        return GeneratedMedia(path=output, duration_seconds=seconds, metadata={"voice": voice})


# Map capability interface -> default instance. Consumed by the registry.
DEFAULTS = {
    TranscriptionProvider: WhisperTranscriptionProvider(),
    TextToVideoProvider: PlaceholderTextToVideo(),
    TextToSpeechProvider: PlaceholderTextToSpeech(),
}
