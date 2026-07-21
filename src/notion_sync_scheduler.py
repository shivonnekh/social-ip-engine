"""notion_sync_scheduler.py — interval-poll fallback for the "Ready to
Publish" comment-keyword sync.

WHY THIS EXISTS
----------------
The live "draft the DM rule" trigger (``POST /admin/notion-sync`` in
``src/web.py``) is SUPPOSED to be event-driven: a Notion Automation calls
it the instant a row's Stage flips to "🟢 Ready to Publish". Root-caused
2026-07-21: checking the live server's access logs for a 35+ minute
window after a real Stage flip showed ZERO requests to any ``/admin/*``
endpoint — the Automation simply wasn't firing. This is the same failure
mode already found and worked around for the publish trigger
(``notion_publish_scheduler.py``'s interval mode) — Notion's public API
doesn't expose Automations for inspection or repair, so the fix has to be
self-contained on this side: check Notion ourselves on a short fixed
cadence instead of waiting to be told.

Deliberately simpler than ``notion_publish_scheduler.py``: that module has
TWO trigger reasons (an event AND a future "Publish Date" that needs a
daily re-check), so it supports both a daily-fixed-hour mode and an
interval mode. This scheduler exists for exactly one reason — the
Automation might not fire — so it only ever needs interval mode. No daily
mode, no "Publish Date"-style deferred concept applies here.

Safe to run frequently: ``notion_sync.sync_once()`` already tracks
processed rows in ``notion_sync_state.json`` and only drafts a NEW rule
for a row it hasn't handled yet — a sweep that finds nothing new to do is
a cheap no-op, same guarantee the publish-side scheduler already relies on.

CONFIG (opt-in — default OFF)
    NOTION_SYNC_SCHEDULE_ENABLED     default "false" — set "true" to turn on.
    NOTION_SYNC_SCHEDULE_INTERVAL_S  default 120 (seconds). Any non-positive
                                      or non-numeric value falls back to 120.
"""

from __future__ import annotations

import asyncio
import logging
import os
from typing import Any, Final

from src.ops_alert import send_ops_alert

logger = logging.getLogger("notion_sync_scheduler")

_OPS_ALERT_KEY: Final = "notion_sync_schedule_failed"
_DEFAULT_INTERVAL_S: Final = 120

# Tasks spawned by our own sweep's caption dispatch — held here so asyncio
# never garbage-collects a task with no other strong reference (same
# reasoning as notion_publish_scheduler.py's own module-level task lists).
_scheduler_caption_tasks: Final[list[asyncio.Task]] = []


def _enabled() -> bool:
    return os.environ.get("NOTION_SYNC_SCHEDULE_ENABLED", "false").strip().lower() == "true"


def _interval_seconds() -> int:
    raw = os.environ.get("NOTION_SYNC_SCHEDULE_INTERVAL_S", "").strip()
    if not raw:
        return _DEFAULT_INTERVAL_S
    try:
        value = int(raw)
    except ValueError:
        return _DEFAULT_INTERVAL_S
    return value if value > 0 else _DEFAULT_INTERVAL_S


async def _sleep(seconds: float) -> None:
    """Thin wrapper around ``asyncio.sleep`` so tests can patch just this
    module's sleeping behavior — see notion_publish_scheduler.py's ``_sleep``
    docstring for why (monkeypatching the global directly hangs pytest-asyncio's
    own internal loop scheduling)."""
    await asyncio.sleep(seconds)


async def run_scheduled_sync() -> dict[str, Any]:
    """One sweep — the exact same dispatch path as the live webhook (see
    module docstring: ``notion_sync_runner.run_sync()``). Never raises:
    this loop has no external observer the way the webhook does (Notion
    can see/retry a 502), so a failure here must be logged, alerted, and
    swallowed, never crash the long-running coroutine."""
    from src.notion_sync_runner import run_sync

    try:
        result = await run_sync(caption_task_sink=_scheduler_caption_tasks)
    except Exception as exc:  # noqa: BLE001 — see docstring, must never crash the loop
        logger.exception("[notion-sync-schedule] sweep failed")
        await send_ops_alert(_OPS_ALERT_KEY, f"🔴 Notion sync interval sweep failed: {exc}")
        return {"error": str(exc)}

    logger.info(
        "[notion-sync-schedule] added=%d skipped=%d errors=%d",
        len(result["added"]), len(result["skipped"]), len(result["errors"]),
    )
    if result["errors"]:
        # The sweep itself didn't raise, but individual rows failed inside
        # sync_once (e.g. a transient Notion API error on one row) — same
        # "nobody else is watching" reasoning as the except block above.
        await send_ops_alert(
            _OPS_ALERT_KEY,
            f"🟡 Notion sync interval sweep completed with {len(result['errors'])} "
            f"row error(s): {result['errors']}",
        )

    return result


async def start_sync_schedule_loop() -> None:
    """Long-running coroutine — mirrors
    ``notion_publish_scheduler.start_publish_schedule_loop``'s interval-mode
    shape (and ``channels.reconciliation.start_reconciliation_loop``'s
    overall sleep-loop pattern). Returns immediately (never starts sleeping)
    when disabled."""
    if not _enabled():
        logger.info(
            "[notion-sync-schedule] NOTION_SYNC_SCHEDULE_ENABLED is false — loop not started"
        )
        return
    interval = _interval_seconds()
    logger.info("[notion-sync-schedule] loop started — interval mode, every %ds", interval)
    while True:
        await _sleep(interval)
        try:
            await run_scheduled_sync()
        except Exception:  # belt-and-suspenders — run_scheduled_sync already catches
            logger.exception("[notion-sync-schedule] loop error (will retry next cycle)")
