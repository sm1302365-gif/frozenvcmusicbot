"""Shared primitives used across every KwaiCut layer."""

from __future__ import annotations

from kwaicut.common.errors import (
    AssetError,
    AuthError,
    KwaiCutError,
    RenderError,
    TimelineError,
    ValidationError,
)
from kwaicut.common.types import (
    Fraction,
    Rect,
    Resolution,
    RGBAColor,
    TimeCode,
)

__all__ = [
    "KwaiCutError",
    "ValidationError",
    "TimelineError",
    "RenderError",
    "AssetError",
    "AuthError",
    "TimeCode",
    "Resolution",
    "Rect",
    "RGBAColor",
    "Fraction",
]
