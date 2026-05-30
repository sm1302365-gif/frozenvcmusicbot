from __future__ import annotations

import wave
from pathlib import Path

from kwaicut.ai.base import (
    TextToSpeechProvider,
    TextToVideoProvider,
    TranscriptionProvider,
)
from kwaicut.ai.providers import PlaceholderTextToSpeech


def test_registry_returns_defaults():
    from kwaicut.ai import registry

    assert isinstance(registry.get(TranscriptionProvider), TranscriptionProvider)
    assert isinstance(registry.get(TextToVideoProvider), TextToVideoProvider)
    assert isinstance(registry.get(TextToSpeechProvider), TextToSpeechProvider)


def test_placeholder_tts_writes_valid_wav(tmp_path: Path):
    out = tmp_path / "voice.wav"
    media = PlaceholderTextToSpeech().synthesize("hello there", voice="nova", output=out)
    assert out.exists()
    assert media.duration_seconds > 0
    with wave.open(str(out)) as wav:
        assert wav.getnchannels() == 1
        assert wav.getframerate() == 16000
        assert wav.getnframes() > 0
