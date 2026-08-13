"""notion_publish_carousel_fb_runner.py — async create->publish->checkbox
for one Facebook Page carousel mirror.

Facebook analogue of ``notion_publish_carousel_runner.py`` (Instagram's
carousel runner) — mirrors its shape (own ``_STATE_LOCK`` +
``_RUNNING_ROW_IDS``, same claim-before-call ledger discipline, same
git-push-after-lock-release durability), fed by
``notion_publish_carousel.plan_fb_carousel_mirrors()`` /
``load_fb_in_flight_jobs()`` (not the Instagram planner).

NO POLL STEP — see ``fb_publish_carousel.py``'s module docstring: a Page
photo has no Meta-side processing step, so there is nothing to poll between
creating the unpublished photos and publishing the post. This runner goes
straight from "create every photo" to "publish the post."
"""

from __future__ import annotations

import asyncio
import logging
import os
from pathlib import Path
from typing import Any

from src import git_publish
from src.channels import fb_publish_carousel
from src.notion_publish_carousel import (
    _FB_STATE_PATH,
    CarouselPublishJob,
    load_fb_in_flight_jobs,
    plan_fb_carousel_mirrors,
)
from src.notion_sync import _load_json, _ncall, _save_json

logger = logging.getLogger("notion_publish_carousel_fb_runner")

_STATE_LOCK = asyncio.Lock()
_RUNNING_ROW_IDS: set[str] = set()

_DEFAULT_POSTED_PROP = "🚀 Posted (Carousel FB)"
_POSTED_PENDING_PATH = (
    Path(__file__).resolve().parent.parent
    / "data" / "channels" / "notion_publish_carousel_fb_posted_pending.json"
)

_STATE_GIT_PATHS = [
    "data/channels/notion_publish_carousel_fb_state.json",
    "data/channels/notion_publish_carousel_fb_posted_pending.json",
]


def _posted_checkbox_enabled() -> bool:
    return os.environ.get("NOTION_PUBLISH_MARK_POSTED", "1").strip() != "0"


def _posted_checkbox_prop() -> str:
    return os.environ.get("NOTION_POSTED_CHECKBOX_PROP_CAROUSEL_FB", "").strip() or _DEFAULT_POSTED_PROP


def _mark_posted(row_id: str) -> str | None:
    prop = _posted_checkbox_prop()
    try:
        _ncall("PATCH", f"/pages/{row_id}", {"properties": {prop: {"checkbox": True}}})
    except Exception as exc:  # noqa: BLE001 - must survive anything
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
    message = f"chore: notion-publish-carousel-fb — {row_id} {status}"
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


async def _ensure_photos(job: CarouselPublishJob, state_path: Path) -> list[str] | None:
    """Return every panel's unpublished-photo id, in panel order — reusing
    any already persisted (a resume) and creating only what's missing.
    ``item_creation_ids`` on the FB ledger record holds photo ids, same
    field name as the IG runner's item container ids for symmetry (the
    ledger schemas are otherwise independent)."""
    photo_ids = list(job.item_creation_ids)
    for image_url in job.image_urls[len(photo_ids):]:
        result = await fb_publish_carousel.create_unpublished_photo(
            image_url, account_id=job.account_id
        )
        if not result.ok:
            logger.warning(
                "[notion-publish-carousel-fb] photo create failed for %s: %s",
                job.row_id, result.detail,
            )
            await _update_ledger(
                state_path, job.row_id, status="failed",
                last_error=f"photo ({len(photo_ids) + 1}/{len(job.image_urls)}): {result.detail}",
                item_creation_ids=photo_ids,
            )
            return None
        photo_ids.append(result.photo_id)
        await _update_ledger(state_path, job.row_id, item_creation_ids=photo_ids)
    return photo_ids


async def _publish_and_tick_checkbox(job: CarouselPublishJob, photo_ids: list[str], state_path: Path) -> bool:
    publish_result = await fb_publish_carousel.publish_carousel_post(
        photo_ids, caption=job.caption, account_id=job.account_id
    )
    if not publish_result.ok:
        logger.warning(
            "[notion-publish-carousel-fb] publish failed for %s: %s", job.row_id, publish_result.detail
        )
        await _update_ledger(
            state_path, job.row_id, status="failed", last_error=publish_result.detail
        )
        return False

    await _update_ledger(
        state_path, job.row_id,
        status="published", fb_media_id=publish_result.post_id, posted_checkbox=False,
    )
    logger.info(
        "[notion-publish-carousel-fb] published %s -> post_id=%s", job.row_id, publish_result.post_id
    )

    if _posted_checkbox_enabled():
        checkbox_warning = await _mark_posted_async(job.row_id)
        if checkbox_warning is None:
            await _update_ledger(state_path, job.row_id, posted_checkbox=True)
        else:
            logger.warning("[notion-publish-carousel-fb] %s", checkbox_warning)
            pending: set[str] = set(_load_json(_POSTED_PENDING_PATH, []))
            pending.add(job.row_id)
            _save_json(_POSTED_PENDING_PATH, sorted(pending))
            await _push_state_to_git("chore: notion-publish-carousel-fb — checkbox retry queued")

    return True


async def run_publish_job(
    job: CarouselPublishJob, *, state_path: Path | None = None,
) -> bool:
    """Create every panel's unpublished photo (resumable) -> publish the
    Page post -> tick checkbox. Never raises."""
    if not await _try_claim_running(job.row_id):
        logger.warning(
            "[notion-publish-carousel-fb] %s already has a run_publish_job in progress — skipping",
            job.row_id,
        )
        return False

    try:
        resolved_state_path = _FB_STATE_PATH if state_path is None else state_path

        photo_ids = await _ensure_photos(job, resolved_state_path)
        if photo_ids is None:
            return False

        return await _publish_and_tick_checkbox(job, photo_ids, resolved_state_path)
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
            await _update_ledger(_FB_STATE_PATH, row_id, posted_checkbox=True)
    _save_json(_POSTED_PENDING_PATH, sorted(pending))
    await _push_state_to_git("chore: notion-publish-carousel-fb — checkbox retry state")


async def resume_in_flight(*, state_path: Path | None = None) -> int:
    jobs = load_fb_in_flight_jobs(state_path)
    if not jobs:
        return 0
    logger.info("[notion-publish-carousel-fb] resuming %d in-flight job(s)", len(jobs))
    results = await asyncio.gather(
        *(run_publish_job(job, state_path=state_path) for job in jobs),
        return_exceptions=True,
    )
    for job, outcome in zip(jobs, results, strict=True):
        if isinstance(outcome, Exception):
            logger.exception("[notion-publish-carousel-fb] resume of %s raised", job.row_id)
    return len(jobs)


def fb_carousel_enabled() -> bool:
    """Kill switch, default OFF — same caution as every other new
    irreversible-post capability in this codebase."""
    return os.environ.get("NOTION_PUBLISH_CAROUSEL_FB_ENABLED", "false").strip().lower() == "true"


async def plan_and_dispatch_carousel_fb(
    *, task_sink: list[asyncio.Task[bool]] | None = None
) -> dict[str, Any]:
    """Facebook analogue of
    ``notion_publish_carousel_runner.plan_and_dispatch_carousel`` — resume
    in-flight FB carousel mirrors, plan newly-published-on-IG carousels not
    yet mirrored, spawn a background task per newly-claimed job."""
    if not fb_carousel_enabled():
        return {"enabled": False, "checked": 0, "claimed": [], "resumed": 0, "skipped": []}

    sink = task_sink if task_sink is not None else []

    resumed_count = await resume_in_flight()

    from starlette.concurrency import run_in_threadpool

    result = await run_in_threadpool(plan_fb_carousel_mirrors)

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
    }
