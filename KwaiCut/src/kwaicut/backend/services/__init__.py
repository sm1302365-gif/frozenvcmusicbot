"""Service layer: business logic decoupled from HTTP routing.

Routes stay thin (parse -> call service -> serialise) while these functions own
the actual rules, which makes them reusable from the desktop client and easy to
unit-test without spinning up the web server.
"""

from __future__ import annotations
