from __future__ import annotations

import pytest

from kwaicut.backend.services.collaboration import CollaborationManager


class FakeWebSocket:
    """Minimal stand-in capturing accepted state and sent messages."""

    def __init__(self) -> None:
        self.accepted = False
        self.sent: list[str] = []

    async def accept(self) -> None:
        self.accepted = True

    async def send_text(self, text: str) -> None:
        self.sent.append(text)


@pytest.mark.asyncio
async def test_connect_tracks_peers_and_broadcasts():
    manager = CollaborationManager()
    a = FakeWebSocket()
    b = FakeWebSocket()

    await manager.connect("proj1", a)
    await manager.connect("proj1", b)
    assert manager.peer_count("proj1") == 2
    assert a.accepted and b.accepted

    await manager.broadcast("proj1", {"type": "edit", "op": "split"}, exclude=a)
    assert any("split" in msg for msg in b.sent)
    assert not any("split" in msg for msg in a.sent)


@pytest.mark.asyncio
async def test_disconnect_decrements_and_cleans_up():
    manager = CollaborationManager()
    ws = FakeWebSocket()
    await manager.connect("p", ws)
    manager.disconnect("p", ws)
    assert manager.peer_count("p") == 0
