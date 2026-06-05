"""Debounce merge buffer for social DMs.

IG/FB users fire choppy multi-message thoughts ("我" / "成日攰" / "瞓得唔好").
Without buffering, each fragment hits the webhook separately and Chloe
replies 3 times. This buffer collects fragments per user, waits for a
quiet window, then dispatches ONE merged turn.

Simpler than the WhatsApp buffer (no completeness heuristics) — a plain
debounce: flush when no new message has arrived for ``window_s``, or force
flush after ``max_s`` regardless (so a non-stop typer still gets a reply).

Env (read by the caller, passed in):
    CHLOE_MERGE_WINDOW_S   quiet window before flush (default 5.0; 0 = off)
    CHLOE_MERGE_MAX_S      hard cap from first fragment (default 20.0)
"""

from __future__ import annotations

import asyncio
import logging
import time
from dataclasses import dataclass, field
from typing import Awaitable, Callable

from src.channels.meta_events import IncomingDM, Platform

logger = logging.getLogger("channels.merge_buffer")

OnFlush = Callable[[IncomingDM], Awaitable[None]]


@dataclass
class _Pending:
    platform: Platform
    sender_id: str
    recipient_id: str
    first_arrival: float
    last_activity: float
    fragments: list[str] = field(default_factory=list)
    last_message_id: str = ""


class MergeBuffer:
    """Per-user debounce buffer. One flusher task per active user key."""

    def __init__(self, *, window_s: float, max_s: float, on_flush: OnFlush) -> None:
        self._window = max(0.0, window_s)
        self._max = max(self._window, max_s)
        self._on_flush = on_flush
        self._buffers: dict[str, _Pending] = {}
        self._tasks: set[asyncio.Task] = set()

    async def submit(self, dm: IncomingDM) -> None:
        """Add a DM fragment. Spawns a flusher on the first fragment per key."""
        # Buffering disabled → dispatch immediately.
        if self._window <= 0:
            await self._on_flush(dm)
            return
        if not dm.text.strip():
            return

        key = dm.crm_key
        now = time.monotonic()
        buf = self._buffers.get(key)
        first = buf is None
        if first:
            buf = _Pending(
                platform=dm.platform,
                sender_id=dm.sender_id,
                recipient_id=dm.recipient_id,
                first_arrival=now,
                last_activity=now,
            )
            self._buffers[key] = buf

        buf.fragments.append(dm.text.strip())
        buf.last_message_id = dm.message_id or buf.last_message_id
        buf.last_activity = now

        if first:
            self._spawn(self._flush(key))

    async def _flush(self, key: str) -> None:
        """Owner coroutine — waits for the buffer to settle, then dispatches."""
        try:
            while True:
                buf = self._buffers.get(key)
                if buf is None:
                    return
                now = time.monotonic()
                quiet = now - buf.last_activity
                age = now - buf.first_arrival
                if quiet >= self._window or age >= self._max:
                    break
                # Sleep just past the remaining quiet window (or to the cap).
                remaining = min(self._window - quiet, self._max - age)
                await asyncio.sleep(max(0.1, remaining))

            buf = self._buffers.pop(key, None)
            if buf is None or not buf.fragments:
                return

            merged = IncomingDM(
                platform=buf.platform,
                sender_id=buf.sender_id,
                recipient_id=buf.recipient_id,
                text="\n".join(buf.fragments),
                message_id=buf.last_message_id,
                timestamp=0,
            )
            logger.info(
                "[merge] flushing %s — %d fragment(s)", key, len(buf.fragments)
            )
            await self._on_flush(merged)
        except Exception:  # noqa: BLE001
            logger.exception("[merge] flush failed for %s", key)
            self._buffers.pop(key, None)

    def _spawn(self, coro) -> None:
        task = asyncio.create_task(coro)
        self._tasks.add(task)
        task.add_done_callback(self._tasks.discard)
