"""WebRTC signaling hub — in-process, keyed by room_id.

Protocol (all messages are JSON over WebSocket):

  Server → Client:
    {"type": "waiting"}          — first to join, waiting for peer
    {"type": "please-offer"}     — peer joined, YOU create & send offer
    {"type": "offer",  "sdp": …} — forwarded from other peer
    {"type": "answer", "sdp": …} — forwarded from other peer
    {"type": "ice-candidate", "candidate": …} — forwarded ICE candidate
    {"type": "peer-left"}        — other peer disconnected

  Client → Server (relay):
    {"type": "offer",  "sdp": …}
    {"type": "answer", "sdp": …}
    {"type": "ice-candidate", "candidate": …}

Single-process safe (Render runs one worker). If you ever scale to multiple
workers you'll need Redis pub/sub here instead.
"""

from __future__ import annotations

import asyncio
import logging
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from starlette.websockets import WebSocket

logger = logging.getLogger("consultation.signaling")

_RELAY_TYPES = {"offer", "answer", "ice-candidate"}


class SignalingHub:
    """Coordinates WebRTC signaling between two peers in a room."""

    def __init__(self) -> None:
        # room_id -> {role: WebSocket}
        self._rooms: dict[str, dict[str, "WebSocket"]] = {}
        self._lock = asyncio.Lock()

    async def join(self, room_id: str, role: str, ws: "WebSocket") -> None:
        async with self._lock:
            if room_id not in self._rooms:
                self._rooms[room_id] = {}

            # Evict stale connection for same role (reconnect)
            if role in self._rooms[room_id]:
                old = self._rooms[room_id][role]
                try:
                    await old.close(code=1001)
                except Exception:  # noqa: BLE001
                    pass

            self._rooms[room_id][role] = ws
            others = {r: w for r, w in self._rooms[room_id].items() if r != role}

        if others:
            # Tell the peer who was already waiting to create the offer
            for _, other_ws in others.items():
                try:
                    await other_ws.send_json({"type": "please-offer"})
                except Exception:  # noqa: BLE001
                    logger.warning("[signaling] failed to notify existing peer in %s", room_id)
        else:
            await ws.send_json({"type": "waiting"})

        logger.info("[signaling] join room=%s role=%s peers=%d", room_id, role, len(others) + 1)

    async def relay(self, room_id: str, sender_role: str, message: dict) -> None:
        """Forward a WebRTC signaling message to all other peers in the room."""
        msg_type = message.get("type", "")
        if msg_type not in _RELAY_TYPES:
            logger.warning("[signaling] unexpected relay type=%s in room=%s", msg_type, room_id)
            return

        room = self._rooms.get(room_id, {})
        for role, ws in list(room.items()):
            if role != sender_role:
                try:
                    await ws.send_json(message)
                except Exception:  # noqa: BLE001
                    logger.warning("[signaling] relay failed room=%s target=%s", room_id, role)

    async def leave(self, room_id: str, role: str) -> None:
        async with self._lock:
            room = self._rooms.get(room_id, {})
            room.pop(role, None)
            if not room:
                self._rooms.pop(room_id, None)

        # Notify remaining peers
        room = self._rooms.get(room_id, {})
        for ws in list(room.values()):
            try:
                await ws.send_json({"type": "peer-left"})
            except Exception:  # noqa: BLE001
                pass

        logger.info("[signaling] leave room=%s role=%s", room_id, role)

    def room_count(self) -> int:
        return len(self._rooms)

    def peer_count(self, room_id: str) -> int:
        return len(self._rooms.get(room_id, {}))


# Process-level singleton
_hub: SignalingHub | None = None


def get_hub() -> SignalingHub:
    global _hub  # noqa: PLW0603
    if _hub is None:
        _hub = SignalingHub()
    return _hub
