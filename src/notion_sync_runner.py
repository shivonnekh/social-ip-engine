"""notion_sync_runner.py — one shared dispatch path for the Notion "Ready to
Publish" comment-keyword sync, used by BOTH the live webhook
(``POST /admin/notion-sync`` in ``src/web.py``) and the interval-poll
fallback (``src/notion_sync_scheduler.py``).

WHY THIS EXISTS
----------------
Extracted 2026-07-21 from ``admin_notion_sync``'s handler body, mirroring
the exact same "one dispatch path for every trigger" pattern already used
for publishing (``src.notion_publish_runner.plan_and_dispatch``, shared by
the live webhook and ``notion_publish_scheduler.py``). Root cause: the
Notion Automation that's supposed to call ``POST /admin/notion-sync`` the
instant a row's Stage flips to "🟢 Ready to Publish" was found NOT firing
in production (checked live server logs — no requests for 35+ minutes
after a Stage flip). Since a second, independently-written copy of this
logic in a scheduler module would inevitably drift from the webhook's
copy over time, this module is the ONE place the actual work happens;
both triggers just call ``run_sync()``.

Deliberately does NOT log the summary line itself (``[notion-sync]
added=... skipped=... errors=...``) — each caller does that itself, same
convention as ``notion_publish_runner.plan_and_dispatch()`` (which also
leaves the summary log to its callers). This lets each trigger's log
prefix stay distinguishable (e.g. the scheduler could tag its own log
differently) without this module needing to know which trigger called it.
"""

from __future__ import annotations

import asyncio
import os
from typing import Any

# Serializes every call to run_sync() — added after code review flagged that
# the live webhook (event-driven) and the interval-poll scheduler (added
# 2026-07-21, every ~120s by default) can genuinely overlap: sync_once()
# itself can take "up to a few minutes" (its own docstring — Notion API +
# OpenAI image generation), well within the scheduler's default interval.
# Without this lock, two concurrent runs would both read
# comment_responses.json/notion_sync_state.json before either had written,
# both decide the same rows are new (drafting the SAME rule twice, or one
# run's write silently clobbering the other's — last-write-wins on that
# file), AND both call git_publish.push_paths(), which runs raw `git
# add/commit/push` subprocess commands against the SAME working-tree
# checkout — two of those interleaving can corrupt the index or produce a
# broken commit. A sync run is always a FULL sweep of every eligible row
# (unlike notion_publish_runner's per-row concurrency, where multiple
# DIFFERENT rows publishing in parallel is actually desirable), so there is
# no benefit to letting two sweeps run at once — a waiting caller just gets
# the next sweep's fresh result instead of triggering a redundant,
# racy one of its own.
_RUN_LOCK = asyncio.Lock()


def _caption_enabled() -> bool:
    """Whether a sync run should ALSO dispatch caption-burn background tasks
    for rows with a "Raw Video" but no "Production Video" yet (see
    ``notion_sync._find_caption_eligible_rows``). OFF by default —
    deliberately opt-in, mirroring ``NOTION_PUBLISH_SCHEDULE_ENABLED``'s
    precedent: unlike cover-gen (a quick outbound image-API call), a
    caption burn is a real CPU/RAM-heavy moviepy/ffmpeg render running on
    THIS SAME process, which also answers live Instagram DM replies and
    comment webhooks — a false default-on here would silently start
    spending real compute on live traffic the moment this deploys. Set
    ``NOTION_SYNC_CAPTION_ENABLED=1`` to turn on."""
    return os.environ.get("NOTION_SYNC_CAPTION_ENABLED", "0").strip() == "1"


def _caption_render_cap() -> int:
    """Max caption-burn renders to DISPATCH per sync run. Deliberately
    stingier than the image-gen caps (default 5) — each unit here is real
    CPU-seconds-to-minutes of rendering on the live-traffic process, not a
    quick outbound API call. Override with ``NOTION_SYNC_MAX_CAPTION_RENDERS``
    (default 1)."""
    raw = os.environ.get("NOTION_SYNC_MAX_CAPTION_RENDERS", "1").strip()
    try:
        return max(0, int(raw))
    except ValueError:
        return 1


async def run_sync(*, caption_task_sink: list[asyncio.Task] | None = None) -> dict[str, Any]:
    """Run one Notion "Ready to Publish" sync — drafts comment-keyword DM
    rules for any newly-eligible row, dispatches opt-in caption-burn tasks,
    and pushes changed state files to git. Raises ``notion_sync.NotionSyncError``
    on failure (callers decide how to surface that — a 502 for the webhook,
    an ops alert for the scheduler).

    ``caption_task_sink``: a list this function appends spawned caption
    tasks to, so the CALLER holds the strong reference (asyncio only keeps
    a weak reference to a task with no other owner) — same pattern as
    ``request.app.state.notion_caption_tasks`` / the scheduler's own
    module-level task list. Pass ``None`` to skip caption dispatch
    entirely regardless of ``_caption_enabled()`` (not used today, but
    keeps the signature honest that this is optional).

    Serialized via ``_RUN_LOCK`` — see that module-level lock's docstring
    for why. A caller blocked waiting for the lock isn't wasted work: it
    still gets a fresh, correct result once the in-flight run finishes,
    just never triggers a second overlapping (and racy) sweep of its own.
    """
    async with _RUN_LOCK:
        from starlette.concurrency import run_in_threadpool

        from src import git_publish, notion_sync

        # sync_once() does blocking I/O (Notion API, image download, and OpenAI
        # image generation up to a few minutes) — never run it on the event
        # loop or it stalls webhooks/health checks for the whole worker.
        result = await run_in_threadpool(notion_sync.sync_once)

        # Caption-burn dispatch — a SEPARATE opt-in step from everything above.
        # Placed AFTER sync_once() has already durably saved comment_responses.json
        # / notion_sync_state.json / the cover-gen work, so this can never affect
        # (or be affected by) that already-completed, higher-priority work.
        # Tasks are DISPATCHED (asyncio.create_task), never awaited here, so a
        # slow render (10-60+ seconds) never delays the caller's response — and
        # never held under _RUN_LOCK either (the task runs independently after
        # this function, and the lock, have already returned/released).
        if caption_task_sink is not None and _caption_enabled():
            from src import notion_caption_gen

            cap = _caption_render_cap()
            for pending in result.get("caption_pending", [])[:cap]:
                task = asyncio.create_task(
                    notion_caption_gen.burn_captions_for_row(pending["row_id"], pending["video_url"])
                )
                caption_task_sink.append(task)

        if result["rules_changed"]:
            # Persist the rules, the processed-row state, the media-attach state,
            # the wired-checkbox retry state, AND the infographic PNGs themselves
            # — git_publish only pushes what it is handed, and anything left off
            # git vanishes on the next deploy. push_paths() silently skips any
            # path that doesn't exist locally (e.g. no pending checkbox retries
            # this run), so it's safe to always list it here.
            paths = [
                "data/channels/comment_responses.json",
                "data/channels/notion_sync_state.json",
                "data/channels/notion_media_state.json",
                "data/channels/notion_wired_pending.json",
                *result.get("media_paths", []),
            ]
            push = git_publish.push_paths(
                paths,
                message=f"chore: notion-sync — {len(result['added'])} new keyword rule(s)",
            )
            result["git_push"] = push
        else:
            # Still persist state (rows we decided to skip permanently, and any
            # checkbox retry that resolved) even with no new rules, so we don't
            # re-check them — or re-attempt an already-fixed checkbox — every
            # trigger.
            push = git_publish.push_paths(
                [
                    "data/channels/notion_sync_state.json",
                    "data/channels/notion_wired_pending.json",
                ],
                message="chore: notion-sync — state update",
            )
            result["git_push"] = push

        return result
