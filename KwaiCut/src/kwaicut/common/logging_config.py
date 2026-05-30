"""Project-wide logging setup.

A single :func:`configure_logging` call wires up a sane console handler. Call it
once at the process entry point (CLI, backend, or desktop ``main``).
"""

from __future__ import annotations

import logging

_CONFIGURED = False

_FORMAT = "%(asctime)s | %(levelname)-7s | %(name)s | %(message)s"


def configure_logging(level: int | str = logging.INFO) -> None:
    """Configure root logging exactly once (idempotent)."""
    global _CONFIGURED
    if _CONFIGURED:
        return
    logging.basicConfig(level=level, format=_FORMAT)
    _CONFIGURED = True


def get_logger(name: str) -> logging.Logger:
    """Return a named logger, ensuring logging has been configured."""
    configure_logging()
    return logging.getLogger(name)
