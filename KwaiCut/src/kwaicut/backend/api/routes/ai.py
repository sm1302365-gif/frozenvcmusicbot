"""AI Studio routes — thin HTTP wrappers over the AI provider registry."""

from __future__ import annotations

from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel

from kwaicut.ai import registry
from kwaicut.ai.base import TextToSpeechProvider, TextToVideoProvider
from kwaicut.backend.dependencies import get_current_user
from kwaicut.common.errors import AIProviderError
from kwaicut.config import get_settings
from kwaicut.db.models import User

router = APIRouter(prefix="/api/ai", tags=["ai"])


class TextToVideoRequest(BaseModel):
    prompt: str
    seconds: float = 5.0


class TextToSpeechRequest(BaseModel):
    text: str
    voice: str = "default"


class GeneratedMediaOut(BaseModel):
    path: str
    duration_seconds: float


@router.post("/text-to-video", response_model=GeneratedMediaOut)
def text_to_video(req: TextToVideoRequest, user: User = Depends(get_current_user)):
    settings = get_settings()
    out = Path(settings.export_root) / f"t2v_{user.id}_{abs(hash(req.prompt)) % 10**8}.mp4"
    try:
        provider = registry.get(TextToVideoProvider)
        media = provider.generate(req.prompt, seconds=req.seconds, output=out)
    except AIProviderError as exc:
        raise HTTPException(status.HTTP_503_SERVICE_UNAVAILABLE, str(exc)) from exc
    return GeneratedMediaOut(path=str(media.path), duration_seconds=media.duration_seconds)


@router.post("/text-to-speech", response_model=GeneratedMediaOut)
def text_to_speech(req: TextToSpeechRequest, user: User = Depends(get_current_user)):
    settings = get_settings()
    out = Path(settings.export_root) / f"tts_{user.id}_{abs(hash(req.text)) % 10**8}.wav"
    try:
        provider = registry.get(TextToSpeechProvider)
        media = provider.synthesize(req.text, voice=req.voice, output=out)
    except AIProviderError as exc:
        raise HTTPException(status.HTTP_503_SERVICE_UNAVAILABLE, str(exc)) from exc
    return GeneratedMediaOut(path=str(media.path), duration_seconds=media.duration_seconds)
