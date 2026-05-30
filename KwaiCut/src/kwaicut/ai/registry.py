"""A tiny service registry for AI providers.

Capabilities are looked up by interface type. Defaults are registered lazily so
importing :mod:`kwaicut.ai` never forces the heavy ML stack (torch, whisper) to
load — that only happens when a provider is actually requested.
"""

from __future__ import annotations

from typing import TypeVar

from kwaicut.ai.base import AIProvider
from kwaicut.common.errors import AIProviderError

T = TypeVar("T", bound=AIProvider)

_REGISTRY: dict[type, AIProvider] = {}


def register(interface: type[T], provider: T) -> None:
    """Bind a concrete ``provider`` to a capability ``interface``."""
    _REGISTRY[interface] = provider


def get(interface: type[T]) -> T:
    """Return the registered provider for ``interface``.

    Falls back to lazily constructing a built-in default the first time a
    capability is requested. Raises :class:`AIProviderError` if none exists.
    """
    if interface in _REGISTRY:
        return _REGISTRY[interface]  # type: ignore[return-value]
    provider = _build_default(interface)
    if provider is None:
        raise AIProviderError(f"no provider registered for {interface.__name__}")
    _REGISTRY[interface] = provider
    return provider  # type: ignore[return-value]


def _build_default(interface: type) -> AIProvider | None:
    """Construct the shipped default provider for a capability, if any."""
    # Imported here to avoid importing optional ML deps at module import time.
    from kwaicut.ai import providers

    return providers.DEFAULTS.get(interface)
