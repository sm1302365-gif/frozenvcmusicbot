"""KwaiCut — a professional, AI-powered video editing platform.

The package is organised into clearly separated layers so each concern can be
developed, tested and scaled independently:

* :mod:`kwaicut.common`   — shared primitives (config, types, errors, helpers).
* :mod:`kwaicut.core`     — the editing engine (timeline model + rendering).
* :mod:`kwaicut.ai`       — pluggable AI providers behind stable interfaces.
* :mod:`kwaicut.db`       — persistence layer (SQLAlchemy models + session).
* :mod:`kwaicut.backend`  — FastAPI service (auth, projects, collaboration).
* :mod:`kwaicut.desktop`  — PyQt6 desktop client.
"""

from __future__ import annotations

__version__ = "0.1.0"
__all__ = ["__version__"]
