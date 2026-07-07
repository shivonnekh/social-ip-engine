"""notion_publish_runner.py — async create→poll→publish→checkbox for one Reel.

The async half of the auto-publish feature (see ``notion_publish.py`` for
the blocking half — Notion I/O, cover/caption resolution, and the
duplicate-post ledger). This module owns the actual Instagram Graph API
calls via ``src.channels.ig_publish`` and never touches the event loop
badly: callers (``POST /admin/notion-publish`` in ``src/web.py``) spawn
``run_publish_job`` as a background ``asyncio.Task`` so Meta's processing
time (seconds to minutes) never blocks the webhook response.

CONCURRENCY
-----------
Multiple jobs (one per newly-claimed row) can run concurrently as separate
background tasks, but they all read-modify-write the SAME ledger file
(``notion_publish_state.json``). A module-level ``asyncio.Lock`` serializes
every ledger mutation so two tasks can never clobber each other's writes —
a single Render worker/event loop makes this lock fully sufficient (no
cross-process coordination needed).

A SEPARATE guard, ``_RUNNING_ROW_IDS``, prevents two ``run_publish_job``
coroutines from ever executing for the SAME row concurrently — this can
otherwise happen because ``resume_in_flight()`` runs both at server startup
AND at the top of every ``/admin/notion-publish`` call: if a startup resume
is still mid-poll for a row when a webhook fires, or two webhook deliveries
overlap, both would see the same ``creation_id`` and both could reach
``publish_container`` — Meta does not de-duplicate that call on our behalf
(see ``ig_publish.publish_container``'s docstring). Claiming a row in
``_RUNNING_ROW_IDS`` is checked-and-set atomically under ``_STATE_LOCK``
before ANY work begins, and released in a ``finally`` block no matter how
the job ends.

DURABILITY
----------
Unlike ``POST /admin/notion-sync`` (which pushes changed files to git AFTER
``sync_once()`` returns, all within one request), this runner's mutations
happen long AFTER the webhook's response was already sent — so each
meaningful ledger change (container created, published, checkbox ticked)
git-pushes itself, right here, not in the endpoint. The git push (and the
Notion checkbox PATCH) are blocking calls, so both are run via
``asyncio.to_thread`` and OUTSIDE the ``_STATE_LOCK`` critical section —
only the local JSON read/write needs the lock; a slow subprocess/HTTP call
must never stall every other job's polling or the rest of the app (health
checks, other webhooks) on this process's single event loop.

RESUMING AFTER A CRASH / DEPLOY
---------------------------------
``resume_in_flight()`` reads every ledger row still ``"in_flight"``
(``notion_publish.load_in_flight_jobs`` — no Notion call needed, the ledger
stores everything) and re-runs ``run_publish_job`` for each. If a job
already has a ``creation_id``, the SAME container is reused — a fresh
container is only ever created when ``creation_id`` is still empty, so a
resume can never produce two containers (and therefore never two live
posts) for the same row. Called once at server startup AND at the top of
every ``/admin/notion-publish`` call, mirroring the
``notion_wired_pending.json`` "retried every subsequent sync" pattern in
``notion_sync.py``.
"""

from __future__ import annotations

import asyncio
import logging
import os
from pathlib import Path
from typing import Any

from starlette.concurrency import run_in_threadpool

from src import git_publish, notion_publish
from src.channels import ig_publish
from src.notion_publish import (
    _STATE_PATH,
    PublishJob,
    _now_iso,
    load_in_flight_jobs,
)
from src.notion_sync import _load_json, _ncall, _save_json

logger = logging.getLogger("notion_publish_runner")

_STATE_LOCK = asyncio.Lock()
# Row ids with a run_publish_job currently executing — see CONCURRENCY above.
# Guarded by _STATE_LOCK (a quick in-memory set op, not worth a second lock).
_RUNNING_ROW_IDS: set[str] = set()

_DEFAULT_POSTED_PROP = "🚀 Posted to IG"
_MIN_POLL_INTERVAL_S = 1.0
_POSTED_PENDING_PATH = (
    Path(__file__).resolve().parent.parent
    / "data" / "channels" / "notion_publish_posted_pending.json"
)

_STATE_GIT_PATHS = [
    "data/channels/notion_publish_state.json",
    "data/channels/notion_publish_posted_pending.json",
]


def _posted_checkbox_enabled() -> bool:
    return os.environ.get("NOTION_PUBLISH_MARK_POSTED", "1").strip() != "0"


def _posted_checkbox_prop() -> str:
    return os.environ.get("NOTION_POSTED_CHECKBOX_PROP", "").strip() or _DEFAULT_POSTED_PROP


def _poll_interval_s() -> float:
    """Seconds between status polls. Defensively parsed (a non-numeric env
    value must never crash a fire-and-forget background task) and floored
    at ``_MIN_POLL_INTERVAL_S`` — a zero/negative interval would mean
    ``elapsed`` never advances toward ``poll_max_s``, looping forever and
    hammering the Graph API."""
    raw = os.environ.get("IG_PUBLISH_POLL_INTERVAL_S", "15").strip()
    try:
        value = float(raw)
    except ValueError:
        return 15.0
    return value if value >= _MIN_POLL_INTERVAL_S else _MIN_POLL_INTERVAL_S


def _poll_max_s() -> float:
    raw = os.environ.get("IG_PUBLISH_POLL_MAX_S", "900").strip()
    try:
        value = float(raw)
    except ValueError:
        return 900.0
    return max(0.0, value)


def _mark_posted(row_id: str) -> str | None:
    """Best-effort tick the row's "posted" checkbox. NEVER raises — mirrors
    ``notion_sync._mark_wired`` exactly (same broad-catch contract): a
    Notion-side failure here must never be confused with a failed publish —
    the Reel is already live by the time this runs."""
    prop = _posted_checkbox_prop()
    try:
        _ncall("PATCH", f"/pages/{row_id}", {"properties": {prop: {"checkbox": True}}})
    except Exception as exc:  # noqa: BLE001 - must survive anything, see docstring
        return f"mark_posted_failed: row {row_id} ('{prop}') — {exc}"
    return None


async def _push_state_to_git(message: str) -> None:
    """git_publish.push_paths runs blocking subprocess calls (up to ~2 min
    worst case) — always off the event loop, never inside _STATE_LOCK."""
    await asyncio.to_thread(git_publish.push_paths, _STATE_GIT_PATHS, message)


async def _mark_posted_async(row_id: str) -> str | None:
    """Thread-offloaded wrapper — _mark_posted does a blocking HTTP PATCH
    (up to 20s) and must never run directly on the event loop."""
    return await asyncio.to_thread(_mark_posted, row_id)


async def _update_ledger(state_path: Path, row_id: str, **fields: Any) -> None:
    """Read-modify-write one ledger entry, serialized across concurrent
    tasks. The lock guards ONLY the local JSON read/write — the git push
    (a blocking subprocess call) happens after the lock is released, off
    the event loop (see module docstring)."""
    async with _STATE_LOCK:
        ledger: dict[str, dict] = _load_json(state_path, {})
        record = ledger.get(row_id, {})
        ledger[row_id] = {**record, **fields, "updated_at": _now_iso()}
        _save_json(state_path, ledger)
        status = fields.get("status", "update")
    message = f"chore: notion-publish — {row_id} {status}"
    await _push_state_to_git(message)


async def _try_claim_running(row_id: str) -> bool:
    """Atomically check-and-set ``row_id`` into ``_RUNNING_ROW_IDS``. Returns
    ``True`` if THIS call claimed it (caller must release via
    ``_release_running``), ``False`` if another task already owns it."""
    async with _STATE_LOCK:
        if row_id in _RUNNING_ROW_IDS:
            return False
        _RUNNING_ROW_IDS.add(row_id)
        return True


async def _release_running(row_id: str) -> None:
    async with _STATE_LOCK:
        _RUNNING_ROW_IDS.discard(row_id)


async def _ensure_container(job: PublishJob, state_path: Path) -> str | None:
    """Return a ``creation_id`` — reusing ``job.creation_id`` if already
    set (a resume), else creating a fresh container. Returns ``None`` (and
    has already recorded the failure) if creation fails."""
    if job.creation_id:
        return job.creation_id
    result = await ig_publish.create_reel_container(
        video_url=job.video_url, caption=job.caption, cover_url=job.cover_url,
        account_id=job.account_id,
    )
    if not result.ok:
        logger.warning(
            "[notion-publish] container create failed for %s: %s", job.row_id, result.detail
        )
        await _update_ledger(state_path, job.row_id, status="failed", last_error=result.detail)
        return None
    await _update_ledger(state_path, job.row_id, creation_id=result.creation_id)
    return result.creation_id


async def _poll_until_finished(
    job: PublishJob, creation_id: str, state_path: Path, *, interval: float, max_wait: float,
) -> bool:
    """Poll until the container is FINISHED. Returns ``False`` (and has
    already recorded the failure) on a terminal Meta status or a timeout."""
    elapsed = 0.0
    while True:
        status = await ig_publish.poll_container_status(creation_id, account_id=job.account_id)
        if status.ok and status.is_finished:
            return True
        if status.ok and status.is_terminal_failure:
            logger.warning(
                "[notion-publish] container %s reached terminal status %s for %s",
                creation_id, status.status_code, job.row_id,
            )
            await _update_ledger(
                state_path, job.row_id, status="failed",
                last_error=f"container status: {status.status_code}",
            )
            return False
        # else: still IN_PROGRESS, or a transient transport/HTTP hiccup on
        # THIS poll — treated the same as IN_PROGRESS, bounded by max_wait
        # below, so one flaky poll never fails the whole job.

        if elapsed >= max_wait:
            logger.warning("[notion-publish] poll timeout for %s after %.0fs", job.row_id, elapsed)
            await _update_ledger(state_path, job.row_id, status="failed", last_error="poll timeout")
            return False

        sleep_for = min(interval, max_wait - elapsed)
        await asyncio.sleep(sleep_for)
        elapsed += sleep_for


async def _publish_and_tick_checkbox(job: PublishJob, creation_id: str, state_path: Path) -> bool:
    """Final media_publish call, then best-effort Notion checkbox tick.
    Returns ``True`` iff the Reel itself published (the checkbox is
    cosmetic — its failure never turns a successful publish into a
    reported failure)."""
    publish_result = await ig_publish.publish_container(creation_id, account_id=job.account_id)
    if not publish_result.ok:
        logger.warning(
            "[notion-publish] media_publish failed for %s: %s", job.row_id, publish_result.detail
        )
        await _update_ledger(
            state_path, job.row_id, status="failed", last_error=publish_result.detail
        )
        return False

    await _update_ledger(
        state_path, job.row_id,
        status="published", ig_media_id=publish_result.media_id, posted_checkbox=False,
    )
    logger.info("[notion-publish] published %s -> media_id=%s", job.row_id, publish_result.media_id)

    if _posted_checkbox_enabled():
        checkbox_warning = await _mark_posted_async(job.row_id)
        if checkbox_warning is None:
            await _update_ledger(state_path, job.row_id, posted_checkbox=True)
        else:
            logger.warning("[notion-publish] %s", checkbox_warning)
            pending: set[str] = set(_load_json(_POSTED_PENDING_PATH, []))
            pending.add(job.row_id)
            _save_json(_POSTED_PENDING_PATH, sorted(pending))
            await _push_state_to_git("chore: notion-publish — checkbox retry queued")

    return True


async def run_publish_job(
    job: PublishJob,
    *,
    state_path: Path | None = None,
    poll_interval_s: float | None = None,
    poll_max_s: float | None = None,
) -> bool:
    """Create (or resume) → poll → publish → tick checkbox for one Reel.
    Returns ``True`` on a successful publish, ``False`` otherwise (including
    when another task is already running this same row — see
    ``_RUNNING_ROW_IDS`` / module docstring). Never raises — every failure
    path updates the ledger to ``"failed"`` and returns, so a bad row never
    crashes its background task silently."""
    if not await _try_claim_running(job.row_id):
        logger.warning(
            "[notion-publish] %s already has a run_publish_job in progress — skipping "
            "(another task, e.g. a concurrent resume or overlapping webhook, owns it)",
            job.row_id,
        )
        return False

    try:
        resolved_state_path = _STATE_PATH if state_path is None else state_path
        interval = max(0.0, _poll_interval_s() if poll_interval_s is None else poll_interval_s)
        max_wait = max(0.0, _poll_max_s() if poll_max_s is None else poll_max_s)

        creation_id = await _ensure_container(job, resolved_state_path)
        if creation_id is None:
            return False

        finished = await _poll_until_finished(
            job, creation_id, resolved_state_path, interval=interval, max_wait=max_wait
        )
        if not finished:
            return False

        return await _publish_and_tick_checkbox(job, creation_id, resolved_state_path)
    finally:
        await _release_running(job.row_id)


async def retry_posted_checkboxes() -> None:
    """Retry any row whose Reel published fine but the checkbox PATCH
    failed on a prior run — mirrors ``notion_sync``'s
    ``notion_wired_pending.json`` retry-every-run pattern."""
    if not _posted_checkbox_enabled():
        return
    pending: set[str] = set(_load_json(_POSTED_PENDING_PATH, []))
    if not pending:
        return
    for row_id in sorted(pending):
        if await _mark_posted_async(row_id) is None:
            pending.discard(row_id)
            await _update_ledger(_STATE_PATH, row_id, posted_checkbox=True)
    _save_json(_POSTED_PENDING_PATH, sorted(pending))
    await _push_state_to_git("chore: notion-publish — checkbox retry state")


async def resume_in_flight(*, state_path: Path | None = None) -> int:
    """Re-run every ledger row still ``"in_flight"`` — recovers from a
    process crash or Render deploy that happened mid-publish. Safe to call
    repeatedly: a job with a ``creation_id`` resumes that SAME container
    (never creates a second one); a job without one creates fresh (it never
    got far enough to reach Meta before the crash). Returns the count of
    jobs resumed (for logging)."""
    jobs = load_in_flight_jobs(state_path)
    if not jobs:
        return 0
    logger.info("[notion-publish] resuming %d in-flight job(s)", len(jobs))
    results = await asyncio.gather(
        *(run_publish_job(job, state_path=state_path) for job in jobs),
        return_exceptions=True,
    )
    for job, outcome in zip(jobs, results, strict=True):
        if isinstance(outcome, Exception):
            logger.exception("[notion-publish] resume of %s raised", job.row_id)
    return len(jobs)


async def plan_and_dispatch(*, task_sink: list[asyncio.Task[bool]] | None = None) -> dict[str, Any]:
    """Resume in-flight jobs, plan newly-published rows, and spawn a
    background ``asyncio.Task`` per newly-claimed job — the exact sequence
    ``POST /admin/notion-publish`` in ``src/web.py`` used to do inline.

    Extracted so BOTH the live, event-driven Notion Automation webhook
    (fires the instant a row's Stage flips to "✅ Published") AND the daily
    schedule sweep (``notion_publish_scheduler.py`` — catches any row
    deferred by a future ``Publish Date`` that has since arrived, since
    that deferred row has no future Stage-change event to re-trigger it)
    share ONE dispatch code path. Two independent implementations of
    "create the container, spawn the task" would be exactly the kind of
    duplicated dispatch logic that risks the two triggers drifting apart
    and, worse, someday disagreeing about the duplicate-post guard.

    ``task_sink`` holds a strong reference to every spawned task for as
    long as the caller needs (``asyncio`` only holds a WEAK reference to a
    task with no other owner, so an unheld task can be garbage-collected
    mid-publish). The webhook passes ``request.app.state.notion_publish_tasks``
    (survives across requests); the scheduler passes its own module-level
    list (survives across sweep cycles). If the caller doesn't care (e.g.
    a one-off script), a fresh list is used internally so a spawned task is
    never immediately eligible for GC before it even starts running.

    Propagates any ``NotionSyncError`` (including ``LedgerCorruptError``)
    raised by ``resume_in_flight`` or ``notion_publish.plan_publishes`` —
    this function does not decide how to handle a planning failure; each
    caller does (502 for the webhook, a logged error for the scheduler).
    """
    sink = task_sink if task_sink is not None else []

    resumed_count = await resume_in_flight()

    # plan_publishes() does blocking I/O (Notion API, cover resolve/
    # generate) — never run it on the event loop.
    result = await run_in_threadpool(notion_publish.plan_publishes)

    for job in result["jobs"]:
        task = asyncio.create_task(run_publish_job(job))
        sink.append(task)
        # No `s=sink` default-arg trick needed here (unlike the classic
        # late-binding-in-a-loop footgun) — `sink` is one variable set once
        # above the loop and never reassigned inside it, so a plain closure
        # over it is unambiguous.
        task.add_done_callback(lambda t: sink.remove(t) if t in sink else None)

    return {
        "checked": result["checked"],
        "claimed": [job.row_id for job in result["jobs"]],
        "resumed": resumed_count,
        "skipped": result["skipped"],
        "errors": result["errors"],
        "warnings": result["warnings"],
    }
