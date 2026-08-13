"""notion_publish_carousel_runner.py — async create->poll->publish->checkbox
for one Instagram carousel.

The async half of the carousel auto-publish feature (see
``notion_publish_carousel.py`` for the blocking half — Notion I/O, panel
resolution, and the duplicate-post ledger). Structurally mirrors
``notion_publish_runner.py`` (the Reel runner) almost exactly — same
``_STATE_LOCK`` + ``_RUNNING_ROW_IDS`` reentrancy guard (**its own,
separate set** — an IG Reel job and an IG carousel job legitimately share
a row id and must not block each other, same reasoning
``notion_publish_fb_runner``'s docstring documents for IG-vs-FB), same
git-push-after-lock-release durability pattern.

THE ONE REAL DIFFERENCE FROM THE REEL RUNNER
-----------------------------------------------
A Reel has ONE container to create. A carousel has N+1: one "item"
container per panel image, THEN one "parent" container referencing all of
them. ``_ensure_item_containers`` is therefore resumable at panel
granularity — ``job.item_creation_ids`` is grown one at a time, persisted
to the ledger after EACH panel (not batched at the end), so a crash
mid-carousel resumes by creating only the panels that don't have an id yet,
never re-creating (and never re-billing/re-uploading) an already-created
item container.
"""

from __future__ import annotations

import asyncio
import logging
import os
from pathlib import Path
from typing import Any

from src import git_publish
from src.channels import ig_publish, ig_publish_carousel
from src.notion_publish_carousel import (
    _STATE_PATH,
    CarouselPublishJob,
    load_in_flight_jobs,
    plan_carousel_publishes,
)
from src.notion_sync import _load_json, _ncall, _save_json

logger = logging.getLogger("notion_publish_carousel_runner")

_STATE_LOCK = asyncio.Lock()
_RUNNING_ROW_IDS: set[str] = set()

_DEFAULT_POSTED_PROP = "🚀 Posted (Carousel)"
_MIN_POLL_INTERVAL_S = 1.0
_POSTED_PENDING_PATH = (
    Path(__file__).resolve().parent.parent
    / "data" / "channels" / "notion_publish_carousel_posted_pending.json"
)

_STATE_GIT_PATHS = [
    "data/channels/notion_publish_carousel_state.json",
    "data/channels/notion_publish_carousel_posted_pending.json",
]


def _posted_checkbox_enabled() -> bool:
    return os.environ.get("NOTION_PUBLISH_MARK_POSTED", "1").strip() != "0"


def _posted_checkbox_prop() -> str:
    return os.environ.get("NOTION_POSTED_CHECKBOX_PROP_CAROUSEL", "").strip() or _DEFAULT_POSTED_PROP


def _poll_interval_s() -> float:
    raw = os.environ.get("IG_PUBLISH_CAROUSEL_POLL_INTERVAL_S", "15").strip()
    try:
        value = float(raw)
    except ValueError:
        return 15.0
    return value if value >= _MIN_POLL_INTERVAL_S else _MIN_POLL_INTERVAL_S


def _poll_max_s() -> float:
    raw = os.environ.get("IG_PUBLISH_CAROUSEL_POLL_MAX_S", "900").strip()
    try:
        value = float(raw)
    except ValueError:
        return 900.0
    return max(0.0, value)


def _mark_posted(row_id: str) -> str | None:
    prop = _posted_checkbox_prop()
    try:
        _ncall("PATCH", f"/pages/{row_id}", {"properties": {prop: {"checkbox": True}}})
    except Exception as exc:  # noqa: BLE001 - must survive anything, mirrors notion_sync._mark_wired
        return f"mark_posted_failed: row {row_id} ('{prop}') — {exc}"
    return None


async def _push_state_to_git(message: str) -> None:
    await asyncio.to_thread(git_publish.push_paths, _STATE_GIT_PATHS, message)


async def _mark_posted_async(row_id: str) -> str | None:
    return await asyncio.to_thread(_mark_posted, row_id)


async def _update_ledger(state_path: Path, row_id: str, **fields: Any) -> None:
    async with _STATE_LOCK:
        ledger: dict[str, dict] = _load_json(state_path, {})
        record = ledger.get(row_id, {})
        ledger[row_id] = {**record, **fields}
        _save_json(state_path, ledger)
        status = fields.get("status", "update")
    message = f"chore: notion-publish-carousel — {row_id} {status}"
    await _push_state_to_git(message)


async def _try_claim_running(row_id: str) -> bool:
    async with _STATE_LOCK:
        if row_id in _RUNNING_ROW_IDS:
            return False
        _RUNNING_ROW_IDS.add(row_id)
        return True


async def _release_running(row_id: str) -> None:
    async with _STATE_LOCK:
        _RUNNING_ROW_IDS.discard(row_id)


async def _ensure_item_containers(job: CarouselPublishJob, state_path: Path) -> list[str] | None:
    """Return every panel's item ``creation_id``, in panel order — reusing
    any already persisted (a resume) and creating only what's missing.
    Persists to the ledger after EACH new item, not batched, so a crash
    partway through a large carousel never loses already-created (and
    already Meta-billed) item containers."""
    item_ids = list(job.item_creation_ids)
    for image_url in job.image_urls[len(item_ids):]:
        result = await ig_publish_carousel.create_carousel_item_container(
            image_url, account_id=job.account_id
        )
        if not result.ok:
            logger.warning(
                "[notion-publish-carousel] item container create failed for %s: %s",
                job.row_id, result.detail,
            )
            await _update_ledger(
                state_path, job.row_id, status="failed",
                last_error=f"item container ({len(item_ids) + 1}/{len(job.image_urls)}): {result.detail}",
                item_creation_ids=item_ids,
            )
            return None
        item_ids.append(result.creation_id)
        await _update_ledger(state_path, job.row_id, item_creation_ids=item_ids)
    return item_ids


async def _ensure_parent_container(
    job: CarouselPublishJob, item_ids: list[str], state_path: Path,
) -> str | None:
    if job.creation_id:
        return job.creation_id
    result = await ig_publish_carousel.create_carousel_container(
        item_ids, caption=job.caption, account_id=job.account_id
    )
    if not result.ok:
        logger.warning(
            "[notion-publish-carousel] parent container create failed for %s: %s",
            job.row_id, result.detail,
        )
        await _update_ledger(state_path, job.row_id, status="failed", last_error=result.detail)
        return None
    await _update_ledger(state_path, job.row_id, creation_id=result.creation_id)
    return result.creation_id


async def _poll_until_finished(
    job: CarouselPublishJob, creation_id: str, state_path: Path, *, interval: float, max_wait: float,
) -> bool:
    elapsed = 0.0
    while True:
        status = await ig_publish.poll_container_status(creation_id, account_id=job.account_id)
        if status.ok and status.is_finished:
            return True
        if status.ok and status.is_terminal_failure:
            logger.warning(
                "[notion-publish-carousel] container %s reached terminal status %s for %s",
                creation_id, status.status_code, job.row_id,
            )
            await _update_ledger(
                state_path, job.row_id, status="failed",
                last_error=f"container status: {status.status_code}",
            )
            return False

        if elapsed >= max_wait:
            logger.warning(
                "[notion-publish-carousel] poll timeout for %s after %.0fs", job.row_id, elapsed
            )
            await _update_ledger(state_path, job.row_id, status="failed", last_error="poll timeout")
            return False

        sleep_for = min(interval, max_wait - elapsed)
        await asyncio.sleep(sleep_for)
        elapsed += sleep_for


async def _publish_and_tick_checkbox(job: CarouselPublishJob, creation_id: str, state_path: Path) -> bool:
    publish_result = await ig_publish.publish_container(creation_id, account_id=job.account_id)
    if not publish_result.ok:
        logger.warning(
            "[notion-publish-carousel] media_publish failed for %s: %s", job.row_id, publish_result.detail
        )
        await _update_ledger(
            state_path, job.row_id, status="failed", last_error=publish_result.detail
        )
        return False

    await _update_ledger(
        state_path, job.row_id,
        status="published", ig_media_id=publish_result.media_id, posted_checkbox=False,
    )
    logger.info(
        "[notion-publish-carousel] published %s -> media_id=%s", job.row_id, publish_result.media_id
    )

    if _posted_checkbox_enabled():
        checkbox_warning = await _mark_posted_async(job.row_id)
        if checkbox_warning is None:
            await _update_ledger(state_path, job.row_id, posted_checkbox=True)
        else:
            logger.warning("[notion-publish-carousel] %s", checkbox_warning)
            pending: set[str] = set(_load_json(_POSTED_PENDING_PATH, []))
            pending.add(job.row_id)
            _save_json(_POSTED_PENDING_PATH, sorted(pending))
            await _push_state_to_git("chore: notion-publish-carousel — checkbox retry queued")

    return True


async def run_publish_job(
    job: CarouselPublishJob,
    *,
    state_path: Path | None = None,
    poll_interval_s: float | None = None,
    poll_max_s: float | None = None,
) -> bool:
    """Create item containers (resumable) -> create parent container ->
    poll -> publish -> tick checkbox for one carousel. Never raises — every
    failure path updates the ledger to ``"failed"`` and returns."""
    if not await _try_claim_running(job.row_id):
        logger.warning(
            "[notion-publish-carousel] %s already has a run_publish_job in progress — skipping",
            job.row_id,
        )
        return False

    try:
        resolved_state_path = _STATE_PATH if state_path is None else state_path
        interval = max(0.0, _poll_interval_s() if poll_interval_s is None else poll_interval_s)
        max_wait = max(0.0, _poll_max_s() if poll_max_s is None else poll_max_s)

        item_ids = await _ensure_item_containers(job, resolved_state_path)
        if item_ids is None:
            return False

        creation_id = await _ensure_parent_container(job, item_ids, resolved_state_path)
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
    await _push_state_to_git("chore: notion-publish-carousel — checkbox retry state")


async def resume_in_flight(*, state_path: Path | None = None) -> int:
    jobs = load_in_flight_jobs(state_path)
    if not jobs:
        return 0
    logger.info("[notion-publish-carousel] resuming %d in-flight job(s)", len(jobs))
    results = await asyncio.gather(
        *(run_publish_job(job, state_path=state_path) for job in jobs),
        return_exceptions=True,
    )
    for job, outcome in zip(jobs, results, strict=True):
        if isinstance(outcome, Exception):
            logger.exception("[notion-publish-carousel] resume of %s raised", job.row_id)
    return len(jobs)


def carousel_enabled() -> bool:
    """Kill switch, default OFF — same caution as
    ``notion_publish_fb_runner._fb_mirror_enabled``: a new capability that
    creates a brand new, real, irreversible post should be opted into
    deliberately."""
    return os.environ.get("NOTION_PUBLISH_CAROUSEL_ENABLED", "false").strip().lower() == "true"


async def plan_and_dispatch_carousel(
    *, task_sink: list[asyncio.Task[bool]] | None = None
) -> dict[str, Any]:
    """Resume in-flight carousel jobs, plan newly-published rows, spawn a
    background task per newly-claimed job. Mirrors
    ``notion_publish_runner.plan_and_dispatch`` — called from
    ``/admin/notion-publish`` (as a THIRD, independently ``except
    Exception``-wrapped block, after Reel + FB) and from the daily
    schedule sweep."""
    if not carousel_enabled():
        return {"enabled": False, "checked": 0, "claimed": [], "resumed": 0, "skipped": [], "errors": [], "warnings": []}

    from starlette.concurrency import run_in_threadpool

    sink = task_sink if task_sink is not None else []

    resumed_count = await resume_in_flight()

    result = await run_in_threadpool(plan_carousel_publishes)

    for job in result["jobs"]:
        task = asyncio.create_task(run_publish_job(job))
        sink.append(task)
        task.add_done_callback(lambda t: sink.remove(t) if t in sink else None)

    return {
        "enabled": True,
        "checked": result["checked"],
        "claimed": [job.row_id for job in result["jobs"]],
        "resumed": resumed_count,
        "skipped": result["skipped"],
        "errors": result["errors"],
        "warnings": result["warnings"],
    }
