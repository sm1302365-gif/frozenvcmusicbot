"""A small, explicit exception hierarchy.

Using domain specific exceptions (instead of bare ``ValueError``/``Exception``)
lets the API layer map failures onto meaningful HTTP status codes and lets the
desktop client present actionable error messages to the user.
"""

from __future__ import annotations


class KwaiCutError(Exception):
    """Base class for every error raised by KwaiCut."""


class ValidationError(KwaiCutError):
    """Raised when user supplied data fails validation."""


class TimelineError(KwaiCutError):
    """Raised for illegal timeline operations (bad ranges, overlaps, ...)."""


class RenderError(KwaiCutError):
    """Raised when the rendering / export pipeline fails."""


class AssetError(KwaiCutError):
    """Raised when a media asset is missing or cannot be probed."""


class AuthError(KwaiCutError):
    """Raised on authentication / authorization failures."""


class AIProviderError(KwaiCutError):
    """Raised when an AI provider is unavailable or returns an error."""
