"""PyQt6 desktop client.

PyQt6 is an *optional* dependency (``pip install kwaicut[desktop]``). The modules
here import it lazily so that importing :mod:`kwaicut` on a headless server (CI,
the backend container) never requires Qt to be installed.
"""

from __future__ import annotations
