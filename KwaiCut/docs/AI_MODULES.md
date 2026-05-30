# AI Module Architecture

The product spec lists dozens of AI features. Rather than bind to any single
vendor, KwaiCut models each capability as an **abstract provider** and resolves a
concrete implementation at runtime through a tiny registry. This keeps the
editing engine completely decoupled from which model does the work and lets you
mix local (offline) and hosted providers freely.

## Interfaces — `ai/base.py`

| Interface | Powers |
| --- | --- |
| `TranscriptionProvider` | Auto captions, dubbing, speech-to-text, searchable transcripts |
| `SceneDetectionProvider` | Smart scene/shot detection, highlight & viral-clip detection |
| `TextToVideoProvider` | AI text-to-video / image-to-video / story generation |
| `TextToSpeechProvider` | Voice generator, TTS, voice cloning, multi-language dubbing |

Result value objects (`Transcript`, `TranscriptSegment`, `SceneCut`,
`GeneratedMedia`) are shared, immutable dataclasses.

## Registry — `ai/registry.py`

```python
from kwaicut.ai import registry
from kwaicut.ai.base import TranscriptionProvider

provider = registry.get(TranscriptionProvider)   # default = local Whisper
transcript = provider.transcribe("clip.wav")
```

`registry.get()` returns a registered provider, lazily constructing the shipped
default the first time a capability is requested. Heavy ML imports (torch,
whisper) only load on first use, so importing `kwaicut` stays cheap on headless
machines and in CI.

## Bundled default providers — `ai/providers.py`

- **`WhisperTranscriptionProvider`** — real, local speech-to-text using
  `openai-whisper`. The model loads lazily and is cached; if the `[ai]` extra is
  not installed the provider reports itself unavailable instead of crashing.
- **`PlaceholderTextToVideo`** — generates a labelled colour-bars clip via FFmpeg
  so the *pipeline* is fully exercised and demoable.
- **`PlaceholderTextToSpeech`** — writes a valid WAV using only the stdlib
  (zero external deps), handy for offline demos and tests.

## Swapping in a real model

Register your own provider at process startup — no caller changes required:

```python
from kwaicut.ai import registry
from kwaicut.ai.base import TextToVideoProvider

class MyHostedT2V(TextToVideoProvider):
    name = "hosted-t2v"
    def generate(self, prompt, *, seconds, output):
        ...  # call your hosted diffusion API, download to `output`

registry.register(TextToVideoProvider, MyHostedT2V())
```

## Captions — `ai/captions.py`

`AutoCaptions` wires the registered `TranscriptionProvider` to an SRT formatter.
ASS output (for the karaoke / animated / emoji caption styles in the spec) is a
natural extension of the same `Transcript` → subtitle pipeline.

## Roadmap features and where they plug in

| Feature | Plugs into |
| --- | --- |
| Background replacement, object removal, masking, motion tracking | a new `vision` provider returning per-frame masks consumed by the render graph |
| Voice cloning, noise removal, music generation | additional `audio` providers behind the same registry |
| Auto-zoom, face tracking, highlight detection | `SceneDetectionProvider` + keyframe generation on the timeline model |
