"""WebSocket route for real-time collaborative editing."""

from __future__ import annotations

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from kwaicut.backend.services.collaboration import manager
from kwaicut.common.logging_config import get_logger

logger = get_logger(__name__)
router = APIRouter(tags=["collaboration"])


@router.websocket("/ws/projects/{project_id}")
async def collaborate(websocket: WebSocket, project_id: str) -> None:
    """Join a project room and relay edit events to all other peers.

    Clients send JSON edit messages (clip moved, effect added, cursor moved);
    the server stamps them and rebroadcasts to everyone else in the room.
    """
    await manager.connect(project_id, websocket)
    try:
        while True:
            message = await websocket.receive_json()
            await manager.broadcast(project_id, message, exclude=websocket)
    except WebSocketDisconnect:
        manager.disconnect(project_id, websocket)
        await manager.broadcast(
            project_id, {"type": "presence", "online": manager.peer_count(project_id)}
        )
