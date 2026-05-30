"""Real-time collaboration via WebSockets.

A :class:`CollaborationManager` keeps an in-memory map of project "rooms" to the
set of connected clients and broadcasts every edit event to the other peers in
the room. This is the transport for multiplayer editing, live cursors and
presence. For a multi-process deployment the in-memory fan-out would be swapped
for a Redis pub/sub backend behind the same interface.
"""

from __future__ import annotations

import json
from collections import defaultdict
from dataclasses import dataclass, field

from kwaicut.common.logging_config import get_logger

logger = get_logger(__name__)


@dataclass
class Room:
    project_id: str
    connections: set = field(default_factory=set)


class CollaborationManager:
    """Tracks rooms and broadcasts edit events to peers."""

    def __init__(self) -> None:
        self._rooms: dict[str, Room] = {}
        self._peer_count: dict[str, int] = defaultdict(int)

    async def connect(self, project_id: str, websocket) -> None:
        await websocket.accept()
        room = self._rooms.setdefault(project_id, Room(project_id=project_id))
        room.connections.add(websocket)
        self._peer_count[project_id] += 1
        logger.info("peer joined project %s (%d online)", project_id, self.peer_count(project_id))
        await self.broadcast(
            project_id, {"type": "presence", "online": self.peer_count(project_id)}
        )

    def disconnect(self, project_id: str, websocket) -> None:
        room = self._rooms.get(project_id)
        if room and websocket in room.connections:
            room.connections.discard(websocket)
            self._peer_count[project_id] = max(0, self._peer_count[project_id] - 1)
            if not room.connections:
                self._rooms.pop(project_id, None)

    def peer_count(self, project_id: str) -> int:
        return self._peer_count.get(project_id, 0)

    async def broadcast(self, project_id: str, message: dict, *, exclude=None) -> None:
        """Send ``message`` (as JSON) to every peer in the room except ``exclude``."""
        room = self._rooms.get(project_id)
        if not room:
            return
        payload = json.dumps(message)
        stale = []
        for connection in room.connections:
            if connection is exclude:
                continue
            try:
                await connection.send_text(payload)
            except Exception:  # connection dropped mid-broadcast
                stale.append(connection)
        for connection in stale:
            self.disconnect(project_id, connection)


# Process-wide manager instance used by the WebSocket route.
manager = CollaborationManager()
