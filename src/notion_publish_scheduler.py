"""notion_publish_scheduler.py — daily sweep so a future Publish Date
actually gets picked up.

WHY THIS EXISTS
----------------
The live "go live" trigger for Reels (``POST /admin/notion-publish`` in
``src/web.py``) is event-driven: a Notion Automation calls it the INSTANT
a row's Stage flips to "✅ Published." That's the right trigger for
"publish right now" — but ``notion_publish.py`` also respects an optional
``Publish Date`` property (``_publish_date_eligible``), deferring any row
whose date hasn't arrived yet (compared in HKT, this business's operating
timezone). A deferred row has NO future event to re-trigger it: Stage
doesn't flip again on its own, so without this sweep a row with a future
Publish Date would sit deferred FOREVER once its date finally arrives,
unless a human manually re-hits the endpoint or nudges the Stage property
back and forth.

This module is that missing "somebody checks back" — a long-running
internal ``asyncio`` loop (same shape as
``src.channels.reconciliation.start_reconciliation_loop``, not an
external cron service) that wakes once a day at a configurable HKT time
and calls the EXACT SAME ``notion_publish_runner.plan_and_dispatch()``
used by the live webhook. One dispatch code path for both triggers means
this sweep can never become a second, divergent way to create a duplicate
live post — see ``plan_and_dispatch``'s own docstring.

WHY AN INTERNAL LOOP, NOT AN EXTERNAL CRON HIT
-----------------------------------------------
This service already runs on a Render plan that does not spin down
(upgraded 2026-06-03, see render.yaml), so a long-lived background
coroutine is reliable here in a way it wouldn't be on a free/sleeping
tier. Unlike the free external cron-job.org ping used to keep a sleeping
free tier warm (where a missed ping just costs one slow cold start), this
trigger's job is to fire a REAL, irreversible Instagram post — its
reliability should not depend on a third-party free service's uptime
having no SLA. Mirroring the reconciliation sweep's already-proven
in-process pattern keeps this consistent with how the rest of this app
already does scheduled work.

CONFIG (opt-in — default OFF)
    NOTION_PUBLISH_SCHEDULE_ENABLED     default "false" — set "true" to turn on.
                                         Deliberately opt-IN, unlike
                                         reconciliation's default-on: that
                                         sweep only ever replays
                                         already-safe, dedup-guarded
                                         comment handling, while this one
                                         can cause a brand new, real,
                                         irreversible Instagram post. A
                                         human should turn this on
                                         deliberately, not get it for free
                                         on the next deploy.
    NOTION_PUBLISH_SCHEDULE_HOUR_HKT    default 9  (0-23, Asia/Hong_Kong time)
    NOTION_PUBLISH_SCHEDULE_MINUTE_HKT  default 0  (0-59)
"""

from __future__ import annotations

import asyncio
import logging
import os
from datetime import datetime, timedelta
from typing import Any, Final
from zoneinfo import ZoneInfo

from src.ops_alert import send_ops_alert

logger = logging.getLogger("notion_publish_scheduler")

_OPS_ALERT_KEY: Final = "notion_publish_schedule_failed"

_HKT: Final = ZoneInfo("Asia/Hong_Kong")

# Tasks spawned by our own sweep — held here so asyncio never garbage-
# collects a task with no other strong reference (same reasoning as
# ``request.app.state.notion_publish_tasks`` in src/web.py; this loop has
# no per-request app object to hang a list off of, so it keeps its own).
# The list binding itself never changes (Final) even though its contents
# legitimately mutate (append/remove) across sweep cycles.
_scheduler_tasks: Final[list[asyncio.Task[bool]]] = []


def _enabled() -> bool:
    return os.environ.get("NOTION_PUBLISH_SCHEDULE_ENABLED", "false").strip().lower() == "true"


def _target_hour() -> int:
    raw = os.environ.get("NOTION_PUBLISH_SCHEDULE_HOUR_HKT", "9").strip()
    try:
        value = int(raw)
    except ValueError:
        return 9
    return value if 0 <= value <= 23 else 9


def _target_minute() -> int:
    raw = os.environ.get("NOTION_PUBLISH_SCHEDULE_MINUTE_HKT", "0").strip()
    try:
        value = int(raw)
    except ValueError:
        return 0
    return value if 0 <= value <= 59 else 0


def seconds_until_next_run(now: datetime, hour: int, minute: int = 0) -> float:
    """Seconds from ``now`` (must be tz-aware; any timezone is fine, it's
    converted internally) until the next occurrence of ``hour:minute`` in
    HKT. If ``now`` is already at or past today's target, returns the
    seconds until TOMORROW's target instead — never 0 or negative, so a
    loop calling this every iteration can never spin without sleeping."""
    local_now = now.astimezone(_HKT)
    target = local_now.replace(hour=hour, minute=minute, second=0, microsecond=0)
    if target <= local_now:
        target += timedelta(days=1)
    return (target - local_now).total_seconds()


async def run_scheduled_sweep() -> dict[str, Any]:
    """One sweep — the exact same dispatch path as the live webhook (see
    module docstring). Never raises: unlike the webhook (which Notion
    itself retries on a timeout/5xx AND whose 502 is visible to whoever's
    watching the Notion Automation), this loop has NO external observer —
    a failure here must be logged, alerted, and swallowed, never crash the
    long-running coroutine. Without the alert, a silently-broken sweep
    (e.g. a corrupt ledger, per notion_publish.LedgerCorruptError's own
    "single worst possible failure mode" framing) would leave any row
    deferred by a future Publish Date stuck forever with nobody notified."""
    from src.notion_publish_runner import plan_and_dispatch

    try:
        result = await plan_and_dispatch(task_sink=_scheduler_tasks)
    except Exception as exc:  # see docstring — must never crash the loop
        logger.exception("[notion-publish-schedule] sweep failed")
        await send_ops_alert(_OPS_ALERT_KEY, f"🔴 Notion publish-date sweep failed: {exc}")
        return {"error": str(exc)}

    logger.info(
        "[notion-publish-schedule] checked=%d claimed=%d resumed=%d skipped=%d errors=%d",
        result["checked"], len(result["claimed"]), result["resumed"],
        len(result["skipped"]), len(result["errors"]),
    )
    if result["errors"]:
        # The sweep itself didn't raise, but individual rows failed inside
        # plan_publishes (e.g. a transient Notion API error on one row) —
        # same "nobody else is watching" reasoning as the except block above.
        await send_ops_alert(
            _OPS_ALERT_KEY,
            f"🟡 Notion publish-date sweep completed with {len(result['errors'])} row error(s): "
            f"{result['errors']}",
        )
    return result


async def start_publish_schedule_loop() -> None:
    """Long-running coroutine — mirrors
    ``reconciliation.start_reconciliation_loop``'s sleep-loop pattern.
    Recomputes the next target time FRESH on every iteration (rather than
    sleeping a fixed 24h) so it self-corrects after a slow sweep or a
    Render restart, instead of drifting later each day."""
    if not _enabled():
        logger.info(
            "[notion-publish-schedule] NOTION_PUBLISH_SCHEDULE_ENABLED is false — loop not started"
        )
        return
    hour, minute = _target_hour(), _target_minute()
    logger.info("[notion-publish-schedule] loop started — target=%02d:%02d HKT daily", hour, minute)
    while True:
        wait_s = seconds_until_next_run(datetime.now(_HKT), hour, minute)
        await asyncio.sleep(wait_s)
        try:
            await run_scheduled_sweep()
        except Exception:  # belt-and-suspenders — run_scheduled_sweep already catches
            logger.exception("[notion-publish-schedule] loop error (will retry next cycle)")
