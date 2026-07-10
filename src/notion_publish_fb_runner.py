"""notion_publish_fb_runner.py — async create→poll→publish→checkbox for
one Facebook Reels mirror.

The Facebook analogue of ``notion_publish_runner.py`` (Instagram's runner).
Deliberately a SEPARATE module rather than a generalized/parameterized
version of the IG runner — see ``notion_publish.py``'s "Facebook mirror"
section docstring for the full reasoning (byte-for-byte mirroring, isolated
ledger, isolated failure/retry). The same reasoning extends to this file:
duplicating ~150 lines of already-proven concurrency logic is a smaller risk
than refactoring the IG runner (which has "the single worst possible
failure mode" written into its own docstring) to support two platforms
through one code path.

Structurally this file mirrors ``notion_publish_runner.py`` almost exactly:
create (start+transfer) -> poll -> publish (finish) -> tick checkbox, with
the same claim-before-call ledger discipline, the same
``_RUNNING_ROW_IDS``-style reentrancy guard (its own, separate set — an IG
job and an FB job legitimately share the same Notion row id, so reusing
Instagram's guard would make them wrongly block each other), and the same
git-push-after-lock-release durability pattern.

Jobs are produced by ``notion_publish.plan_fb_mirrors()`` /
``notion_publish.load_fb_in_flight_jobs()`` (not ``plan_publishes()`` /
``load_in_flight_jobs()`` — those are Instagram's).
"""

from __future__ import annotations

import asyncio
import logging
import os
from pathlib import Path
from typing import Any

from src import git_publish, notion_publish
from src.channels import fb_publish
from src.notion_publish import (
    _FB_STATE_PATH,
    PublishJob,
    _now_iso,
    load_fb_in_flight_jobs,
)
from src.notion_sync import _load_json, _ncall, _save_json

logger = logging.getLogger("notion_publish_fb_runner")

_STATE_LOCK = asyncio.Lock()
# Separate from Instagram's _RUNNING_ROW_IDS — see module docstring for why
# sharing it would be wrong (same row_id, different platform, must not
# block each other).
_RUNNING_ROW_IDS: set[str] = set()

_DEFAULT_POSTED_PROP = "🚀 Posted to FB"
_MIN_POLL_INTERVAL_S = 1.0
_POSTED_PENDING_PATH = (
    Path(__file__).resolve().parent.parent
    / "data" / "channels" / "notion_publish_fb_posted_pending.json"
)

_STATE_GIT_PATHS = [
    "data/channels/notion_publish_fb_state.json",
    "data/channels/notion_publish_fb_posted_pending.json",
]


def _posted_checkbox_enabled() -> bool:
    return os.environ.get("NOTION_PUBLISH_MARK_POSTED", "1").strip() != "0"


def _posted_checkbox_prop() -> str:
    return os.environ.get("NOTION_POSTED_CHECKBOX_PROP_FB", "").strip() or _DEFAULT_POSTED_PROP


def _poll_interval_s() -> float:
    """Same defensive parsing as the IG runner — a non-numeric env value
    must never crash a fire-and-forget background task."""
    raw = os.environ.get("FB_PUBLISH_POLL_INTERVAL_S", "15").strip()
    try:
        value = float(raw)
    except ValueError:
        return 15.0
    return value if value >= _MIN_POLL_INTERVAL_S else _MIN_POLL_INTERVAL_S


def _poll_max_s() -> float:
    raw = os.environ.get("FB_PUBLISH_POLL_MAX_S", "900").strip()
    try:
        value = float(raw)
    except ValueError:
        return 900.0
    return max(0.0, value)


def _mark_posted(row_id: str) -> str | None:
    """Best-effort tick the row's FB "posted" checkbox. NEVER raises — same
    broad-catch contract as notion_sync._mark_wired / the IG runner's
    _mark_posted: a Notion-side failure here must never be confused with a
    failed publish — the Reel is already live on Facebook by the time this
    runs."""
    prop = _posted_checkbox_prop()
    try:
        _ncall("PATCH", f"/pages/{row_id}", {"properties": {prop: {"checkbox": True}}})
    except Exception as exc:  # noqa: BLE001 - must survive anything, see docstring
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
        ledger[row_id] = {**record, **fields, "updated_at": _now_iso()}
        _save_json(state_path, ledger)
        status = fields.get("status", "update")
    message = f"chore: notion-publish-fb — {row_id} {status}"
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


def _refresh_video_url(job: PublishJob) -> str | None:
    """Re-resolve the row's "Production Video" URL from Notion RIGHT NOW,
    returning a fresh presigned URL — or ``None`` if it can't be safely used
    (caller falls back to ``job.video_url`` unchanged).

    WHY (2026-07-09/10 incident, 4 rows failed 3x each): the mirror planner
    copies ``video_url`` verbatim out of Instagram's ledger — but that URL is
    a Notion S3 presigned link that expires in ONE HOUR, and the FB mirror
    STRUCTURALLY runs later than that: when ``plan_fb_mirrors()`` executes,
    the same call's IG job is still ``in_flight`` (its ledger entry only says
    ``published`` after the async IG runner finishes), so the row is only
    picked up on the NEXT webhook fire or the daily sweep — hours to a day
    later. Every FB mirror of a not-just-published row was therefore handing
    Meta a dead URL: ``FileUrlProcessingError ... 403 Forbidden``.

    SAFETY — this must never weaken the byte-for-byte mirror guarantee: the
    fresh URL is only used when its STABLE part (scheme+host+path, the same
    normalization the dedup ledger uses) matches ``job.video_url``'s. A
    mismatch means the row's "Production Video" file was REPLACED after the
    IG publish — silently mirroring the new file would post content to FB
    that never went to IG, so we refuse (return ``None``) and let the create
    call fail loudly with the stale URL instead. Caption/cover are NOT
    refreshed for the same reason: URL freshness is a transport concern;
    content stays whatever IG's ledger recorded.

    Sync (urllib) — call via ``asyncio.to_thread``. Never raises."""
    try:
        row = _ncall("GET", f"/pages/{job.row_id}")
        fresh = notion_publish._extract_video_url(row)
        if not fresh:
            logger.warning(
                "[notion-publish-fb] %s: no Production Video on the Notion row — using ledger URL",
                job.row_id,
            )
            return None
        if notion_publish._stable_video_url(fresh) != notion_publish._stable_video_url(job.video_url):
            logger.warning(
                "[notion-publish-fb] %s: Notion's Production Video differs from the one published "
                "to IG — refusing to mirror a different asset; using ledger URL",
                job.row_id,
            )
            return None
        return fresh
    except Exception as exc:  # noqa: BLE001 - refresh is best-effort, stale URL fails loudly downstream
        logger.warning("[notion-publish-fb] %s: video URL refresh failed (%s) — using ledger URL",
                       job.row_id, exc)
        return None


async def _ensure_container(job: PublishJob, state_path: Path) -> str | None:
    """Return a ``creation_id`` (FB ``video_id``) — reusing ``job.creation_id``
    if already set (a resume), else running the start+transfer sequence.

    The transfer URL is re-resolved fresh from Notion first (see
    ``_refresh_video_url``) — the ledger's copy is expired by the time any
    non-instant mirror runs."""
    if job.creation_id:
        return job.creation_id
    video_url = await asyncio.to_thread(_refresh_video_url, job) or job.video_url
    result = await fb_publish.create_reel_container(
        video_url=video_url, caption=job.caption, cover_url=job.cover_url,
        account_id=job.account_id,
    )
    if not result.ok:
        logger.warning(
            "[notion-publish-fb] container create failed for %s: %s", job.row_id, result.detail
        )
        await _update_ledger(state_path, job.row_id, status="failed", last_error=result.detail)
        return None
    await _update_ledger(state_path, job.row_id, creation_id=result.creation_id)
    return result.creation_id


async def _poll_until_finished(
    job: PublishJob, creation_id: str, state_path: Path, *, interval: float, max_wait: float,
) -> bool:
    elapsed = 0.0
    while True:
        status = await fb_publish.poll_container_status(creation_id, account_id=job.account_id)
        if status.ok and status.is_finished:
            return True
        if status.ok and status.is_terminal_failure:
            logger.warning(
                "[notion-publish-fb] container %s reached terminal status %s for %s",
                creation_id, status.status_code, job.row_id,
            )
            await _update_ledger(
                state_path, job.row_id, status="failed",
                last_error=f"container status: {status.status_code}",
            )
            return False
        # else: still uploading/processing, or a transient hiccup on THIS
        # poll — treated the same, bounded by max_wait below.

        if elapsed >= max_wait:
            logger.warning("[notion-publish-fb] poll timeout for %s after %.0fs", job.row_id, elapsed)
            await _update_ledger(state_path, job.row_id, status="failed", last_error="poll timeout")
            return False

        sleep_for = min(interval, max_wait - elapsed)
        await asyncio.sleep(sleep_for)
        elapsed += sleep_for


async def _publish_and_tick_checkbox(job: PublishJob, creation_id: str, state_path: Path) -> bool:
    """Final finish call, then best-effort Notion checkbox tick. Returns
    ``True`` iff the Reel itself published (the checkbox is cosmetic)."""
    publish_result = await fb_publish.publish_container(
        creation_id, job.caption, account_id=job.account_id
    )
    if not publish_result.ok:
        logger.warning(
            "[notion-publish-fb] finish failed for %s: %s", job.row_id, publish_result.detail
        )
        await _update_ledger(
            state_path, job.row_id, status="failed", last_error=publish_result.detail
        )
        return False

    await _update_ledger(
        state_path, job.row_id,
        status="published", fb_media_id=publish_result.media_id, posted_checkbox=False,
    )
    logger.info(
        "[notion-publish-fb] published %s -> media_id=%s", job.row_id, publish_result.media_id
    )

    if _posted_checkbox_enabled():
        checkbox_warning = await _mark_posted_async(job.row_id)
        if checkbox_warning is None:
            await _update_ledger(state_path, job.row_id, posted_checkbox=True)
        else:
            logger.warning("[notion-publish-fb] %s", checkbox_warning)
            pending: set[str] = set(_load_json(_POSTED_PENDING_PATH, []))
            pending.add(job.row_id)
            _save_json(_POSTED_PENDING_PATH, sorted(pending))
            await _push_state_to_git("chore: notion-publish-fb — checkbox retry queued")

    return True


async def run_publish_job(
    job: PublishJob,
    *,
    state_path: Path | None = None,
    poll_interval_s: float | None = None,
    poll_max_s: float | None = None,
) -> bool:
    """Create (or resume) → poll → publish → tick checkbox for one FB Reel
    mirror. Same contract as the IG runner's ``run_publish_job`` — never
    raises, returns ``False`` on any failure path (already recorded in the
    ledger) or if another task already owns this row."""
    if not await _try_claim_running(job.row_id):
        logger.warning(
            "[notion-publish-fb] %s already has a run_publish_job in progress — skipping",
            job.row_id,
        )
        return False

    try:
        resolved_state_path = _FB_STATE_PATH if state_path is None else state_path
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
    await _push_state_to_git("chore: notion-publish-fb — checkbox retry state")


async def resume_in_flight(*, state_path: Path | None = None) -> int:
    """Re-run every FB ledger row still ``"in_flight"``. Same crash-recovery
    contract as the IG runner's ``resume_in_flight``."""
    jobs = load_fb_in_flight_jobs(state_path)
    if not jobs:
        return 0
    logger.info("[notion-publish-fb] resuming %d in-flight job(s)", len(jobs))
    results = await asyncio.gather(
        *(run_publish_job(job, state_path=state_path) for job in jobs),
        return_exceptions=True,
    )
    for job, outcome in zip(jobs, results, strict=True):
        if isinstance(outcome, Exception):
            logger.exception("[notion-publish-fb] resume of %s raised", job.row_id)
    return len(jobs)


def _fb_mirror_enabled() -> bool:
    """Kill switch, default OFF — mirrors the caution already applied to
    ``NOTION_PUBLISH_SCHEDULE_ENABLED`` (a new capability that creates a
    brand new, real, irreversible post should be opted into deliberately,
    not enabled for free on the next deploy). Flip to "true" once the live
    verification script has confirmed the flow end-to-end."""
    return os.environ.get("NOTION_PUBLISH_FB_ENABLED", "false").strip().lower() == "true"


async def plan_and_dispatch_fb(*, task_sink: list[asyncio.Task[bool]] | None = None) -> dict[str, Any]:
    """Facebook analogue of ``notion_publish_runner.plan_and_dispatch`` —
    resume in-flight FB mirrors, plan newly-published-on-IG rows that
    haven't been mirrored yet, spawn a background task per newly-claimed
    job. Intended to be called RIGHT AFTER the IG dispatch, from the same
    trigger (the Notion "✅ Published" webhook and the daily schedule
    sweep) — see ``src/web.py``'s ``/admin/notion-publish`` handler and
    ``notion_publish_scheduler.py``.

    A no-op (returns immediately with an explanatory summary, spawns
    nothing) when ``NOTION_PUBLISH_FB_ENABLED`` is not "true" — see
    ``_fb_mirror_enabled``.
    """
    if not _fb_mirror_enabled():
        return {"enabled": False, "checked": 0, "claimed": [], "resumed": 0, "skipped": [], "jobs_spawned": 0}

    sink = task_sink if task_sink is not None else []

    resumed_count = await resume_in_flight()

    from starlette.concurrency import run_in_threadpool

    result = await run_in_threadpool(notion_publish.plan_fb_mirrors)

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
