"""Tests for src/notion_publish_runner.py — async create→poll→publish→checkbox.

ALL external calls are faked: ``ig_publish`` (Graph API), ``_ncall`` (Notion
checkbox PATCH), and ``git_publish.push_paths`` (never allowed to run a real
git/Notion/Meta call from a test, even if the developer's shell happens to
have real tokens exported — see the autouse ``_no_real_side_effects``
fixture, which explicitly stubs ``git_publish.push_paths`` regardless of
env, since a real dev shell in this repo IS likely to have
``GITHUB_PUSH_TOKEN``/``NOTION_KEY`` set).
"""

from __future__ import annotations

import asyncio
import json
from pathlib import Path

import pytest

from src import notion_publish_runner as runner
from src.channels import ig_publish
from src.notion_publish import PublishJob


def _job(row_id: str = "row-1", creation_id: str = "") -> PublishJob:
    return PublishJob(
        row_id=row_id, account_id="acct-1", video_url="https://s3.example/v.mp4",
        cover_url="https://example.com/cover.jpg", caption="hi", creation_id=creation_id,
    )


@pytest.fixture()
def state_path(tmp_path: Path) -> Path:
    return tmp_path / "notion_publish_state.json"


@pytest.fixture(autouse=True)
def _no_real_side_effects(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> list:
    """Guarantee no test ever hits real git or real Notion, and never writes
    to this repo's REAL data/channels/notion_publish_posted_pending.json,
    regardless of what's exported in the developer's shell or which failure
    path a test happens to exercise. A test that wants to assert specific
    pending-file behavior can still override ``_POSTED_PENDING_PATH`` itself
    (monkeypatch layers cleanly on top of this default)."""
    pushed_calls: list[tuple[list[str], str]] = []
    monkeypatch.setattr(
        runner.git_publish, "push_paths",
        lambda paths, message: (pushed_calls.append((paths, message)) or {"ok": True, "detail": "faked"}),
    )
    monkeypatch.setattr(runner, "_ncall", lambda method, path, body=None: {})
    monkeypatch.setattr(runner, "_POSTED_PENDING_PATH", tmp_path / "notion_publish_posted_pending.json")
    return pushed_calls


def _ledger(state_path: Path) -> dict:
    return json.loads(state_path.read_text()) if state_path.exists() else {}


# ---------------------------------------------------------------- happy path


@pytest.mark.asyncio
async def test_full_happy_path_creates_polls_publishes_ticks_checkbox(
    state_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(
        ig_publish, "create_reel_container",
        lambda **kw: _ok_container("container-1"),
    )
    poll_calls = {"n": 0}

    async def fake_poll(creation_id, *, account_id=None):
        poll_calls["n"] += 1
        status = "IN_PROGRESS" if poll_calls["n"] < 2 else "FINISHED"
        return ig_publish.StatusResult(True, status_code=status)

    monkeypatch.setattr(ig_publish, "poll_container_status", fake_poll)
    monkeypatch.setattr(
        ig_publish, "publish_container",
        lambda creation_id, **kw: _ok_publish("media-1"),
    )

    ok = await runner.run_publish_job(_job(), state_path=state_path, poll_interval_s=0, poll_max_s=5)

    assert ok is True
    assert poll_calls["n"] == 2  # polled until FINISHED
    ledger = _ledger(state_path)
    assert ledger["row-1"]["status"] == "published"
    assert ledger["row-1"]["ig_media_id"] == "media-1"
    assert ledger["row-1"]["posted_checkbox"] is True


async def _ok_container(creation_id: str):
    return ig_publish.ContainerResult(True, creation_id=creation_id)


async def _ok_publish(media_id: str):
    return ig_publish.PublishResult(True, media_id=media_id)


# ------------------------------------------------------------------ create step


@pytest.mark.asyncio
async def test_create_failure_marks_ledger_failed(state_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    async def fake_create(**kw):
        return ig_publish.ContainerResult(False, detail="quota exceeded")

    monkeypatch.setattr(ig_publish, "create_reel_container", fake_create)

    ok = await runner.run_publish_job(_job(), state_path=state_path)

    assert ok is False
    ledger = _ledger(state_path)
    assert ledger["row-1"]["status"] == "failed"
    assert "quota" in ledger["row-1"]["last_error"]


@pytest.mark.asyncio
async def test_existing_creation_id_skips_create_call(
    state_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Resuming a job that already has a creation_id must NEVER create a
    second container — this is the core no-duplicate-post guarantee."""
    create_calls = {"n": 0}

    async def fake_create(**kw):
        create_calls["n"] += 1
        return ig_publish.ContainerResult(True, creation_id="SHOULD-NOT-BE-CALLED")

    async def fake_poll(creation_id, *, account_id=None):
        assert creation_id == "existing-container"  # the resumed one, not a new one
        return ig_publish.StatusResult(True, status_code="FINISHED")

    async def fake_publish(creation_id, **kw):
        return ig_publish.PublishResult(True, media_id="m1")

    monkeypatch.setattr(ig_publish, "create_reel_container", fake_create)
    monkeypatch.setattr(ig_publish, "poll_container_status", fake_poll)
    monkeypatch.setattr(ig_publish, "publish_container", fake_publish)

    ok = await runner.run_publish_job(
        _job(creation_id="existing-container"), state_path=state_path, poll_interval_s=0, poll_max_s=5
    )

    assert ok is True
    assert create_calls["n"] == 0  # never created a NEW container


# ------------------------------------------------------------------- poll step


@pytest.mark.asyncio
async def test_terminal_failure_status_marks_failed_no_publish_call(
    state_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(ig_publish, "create_reel_container", lambda **kw: _ok_container("c1"))

    async def fake_poll(creation_id, *, account_id=None):
        return ig_publish.StatusResult(True, status_code="ERROR")

    publish_calls = {"n": 0}

    async def fake_publish(creation_id, **kw):
        publish_calls["n"] += 1
        return ig_publish.PublishResult(True, media_id="should-not-happen")

    monkeypatch.setattr(ig_publish, "poll_container_status", fake_poll)
    monkeypatch.setattr(ig_publish, "publish_container", fake_publish)

    ok = await runner.run_publish_job(_job(), state_path=state_path, poll_interval_s=0, poll_max_s=5)

    assert ok is False
    assert publish_calls["n"] == 0
    ledger = _ledger(state_path)
    assert ledger["row-1"]["status"] == "failed"
    assert "ERROR" in ledger["row-1"]["last_error"]


@pytest.mark.asyncio
async def test_poll_timeout_marks_failed(state_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(ig_publish, "create_reel_container", lambda **kw: _ok_container("c1"))

    async def always_in_progress(creation_id, *, account_id=None):
        return ig_publish.StatusResult(True, status_code="IN_PROGRESS")

    monkeypatch.setattr(ig_publish, "poll_container_status", always_in_progress)

    ok = await runner.run_publish_job(_job(), state_path=state_path, poll_interval_s=0, poll_max_s=0)

    assert ok is False
    ledger = _ledger(state_path)
    assert ledger["row-1"]["status"] == "failed"
    assert "timeout" in ledger["row-1"]["last_error"]


@pytest.mark.asyncio
async def test_transient_poll_error_does_not_immediately_fail(
    state_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(ig_publish, "create_reel_container", lambda **kw: _ok_container("c1"))
    calls = {"n": 0}

    async def flaky_then_finished(creation_id, *, account_id=None):
        calls["n"] += 1
        if calls["n"] == 1:
            return ig_publish.StatusResult(False, detail="transport error")
        return ig_publish.StatusResult(True, status_code="FINISHED")

    monkeypatch.setattr(ig_publish, "poll_container_status", flaky_then_finished)
    monkeypatch.setattr(ig_publish, "publish_container", lambda creation_id, **kw: _ok_publish("m1"))

    ok = await runner.run_publish_job(_job(), state_path=state_path, poll_interval_s=0, poll_max_s=5)

    assert ok is True
    assert calls["n"] == 2


# ---------------------------------------------------------------- publish step


@pytest.mark.asyncio
async def test_publish_failure_marks_ledger_failed(state_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(ig_publish, "create_reel_container", lambda **kw: _ok_container("c1"))
    monkeypatch.setattr(
        ig_publish, "poll_container_status",
        lambda creation_id, **kw: _status_finished(),
    )

    async def fake_publish(creation_id, **kw):
        return ig_publish.PublishResult(False, detail="creation_id expired")

    monkeypatch.setattr(ig_publish, "publish_container", fake_publish)

    ok = await runner.run_publish_job(_job(), state_path=state_path, poll_interval_s=0, poll_max_s=5)

    assert ok is False
    ledger = _ledger(state_path)
    assert ledger["row-1"]["status"] == "failed"
    assert "expired" in ledger["row-1"]["last_error"]


async def _status_finished():
    return ig_publish.StatusResult(True, status_code="FINISHED")


# --------------------------------------------------------------- checkbox step


@pytest.mark.asyncio
async def test_checkbox_failure_does_not_undo_published_status(
    state_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(ig_publish, "create_reel_container", lambda **kw: _ok_container("c1"))
    monkeypatch.setattr(ig_publish, "poll_container_status", lambda creation_id, **kw: _status_finished())
    monkeypatch.setattr(ig_publish, "publish_container", lambda creation_id, **kw: _ok_publish("m1"))
    monkeypatch.setattr(runner, "_ncall", lambda *a, **kw: (_ for _ in ()).throw(RuntimeError("column missing")))

    ok = await runner.run_publish_job(_job(), state_path=state_path, poll_interval_s=0, poll_max_s=5)

    assert ok is True  # the REEL published fine — checkbox is cosmetic
    ledger = _ledger(state_path)
    assert ledger["row-1"]["status"] == "published"
    assert ledger["row-1"]["posted_checkbox"] is False


@pytest.mark.asyncio
async def test_checkbox_disabled_skips_patch_entirely(
    state_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("NOTION_PUBLISH_MARK_POSTED", "0")
    monkeypatch.setattr(ig_publish, "create_reel_container", lambda **kw: _ok_container("c1"))
    monkeypatch.setattr(ig_publish, "poll_container_status", lambda creation_id, **kw: _status_finished())
    monkeypatch.setattr(ig_publish, "publish_container", lambda creation_id, **kw: _ok_publish("m1"))
    ncall_calls = {"n": 0}
    monkeypatch.setattr(runner, "_ncall", lambda *a, **kw: ncall_calls.__setitem__("n", ncall_calls["n"] + 1))

    ok = await runner.run_publish_job(_job(), state_path=state_path, poll_interval_s=0, poll_max_s=5)

    assert ok is True
    assert ncall_calls["n"] == 0


# ------------------------------------------------------------------ retry queue


@pytest.mark.asyncio
async def test_retry_posted_checkboxes_clears_resolved_entries(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    pending_path = tmp_path / "notion_publish_posted_pending.json"
    pending_path.write_text(json.dumps(["row-a", "row-b"]))
    monkeypatch.setattr(runner, "_POSTED_PENDING_PATH", pending_path)
    monkeypatch.setattr(runner, "_STATE_PATH", tmp_path / "notion_publish_state.json")

    calls: list[str] = []

    def fake_ncall(method, path, body=None):
        calls.append(path)
        if "row-a" in path:
            raise RuntimeError("still failing")
        return {}

    monkeypatch.setattr(runner, "_ncall", fake_ncall)

    await runner.retry_posted_checkboxes()

    remaining = json.loads(pending_path.read_text())
    assert remaining == ["row-a"]  # row-b resolved and was removed


@pytest.mark.asyncio
async def test_retry_posted_checkboxes_noop_when_empty(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(runner, "_POSTED_PENDING_PATH", tmp_path / "missing.json")
    calls = {"n": 0}
    monkeypatch.setattr(runner, "_ncall", lambda *a, **kw: calls.__setitem__("n", calls["n"] + 1))
    await runner.retry_posted_checkboxes()
    assert calls["n"] == 0


# -------------------------------------------------------------- resume_in_flight


@pytest.mark.asyncio
async def test_resume_in_flight_reruns_every_in_flight_job(
    state_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    state_path.write_text(json.dumps({
        "r1": {
            "status": "in_flight", "video_url": "https://x/1.mp4", "cover_url": "",
            "caption": "c1", "account_id": "a1", "creation_id": None,
        },
        "r2": {"status": "published", "video_url": "https://x/2.mp4"},
    }))
    ran: list[str] = []

    async def fake_run(job, *, state_path=None, **kw):
        ran.append(job.row_id)
        return True

    monkeypatch.setattr(runner, "run_publish_job", fake_run)

    count = await runner.resume_in_flight(state_path=state_path)

    assert count == 1
    assert ran == ["r1"]  # only the in_flight row, not the published one


@pytest.mark.asyncio
async def test_resume_in_flight_empty_ledger_is_noop(tmp_path: Path) -> None:
    count = await runner.resume_in_flight(state_path=tmp_path / "missing.json")
    assert count == 0


@pytest.mark.asyncio
async def test_resume_in_flight_one_job_raising_does_not_crash_others(
    state_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    state_path.write_text(json.dumps({
        "r1": {"status": "in_flight", "video_url": "https://x/1.mp4", "cover_url": "",
               "caption": "c1", "account_id": "a1", "creation_id": None},
        "r2": {"status": "in_flight", "video_url": "https://x/2.mp4", "cover_url": "",
               "caption": "c2", "account_id": "a2", "creation_id": None},
    }))

    async def fake_run(job, *, state_path=None, **kw):
        if job.row_id == "r1":
            raise RuntimeError("boom")
        return True

    monkeypatch.setattr(runner, "run_publish_job", fake_run)

    count = await runner.resume_in_flight(state_path=state_path)
    assert count == 2  # both were attempted despite r1 raising


# ------------------------------------------------- reentrancy guard (CRITICAL)


@pytest.mark.asyncio
async def test_concurrent_run_publish_job_same_row_only_one_creates_container(
    state_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """CRITICAL regression: two run_publish_job coroutines for the SAME row
    running concurrently (e.g. startup resume overlapping a webhook call)
    must never both create a container / both publish — only one may
    proceed; the other must back off immediately."""
    create_calls = {"n": 0}
    gate = asyncio.Event()

    async def slow_create(**kw):
        create_calls["n"] += 1
        await gate.wait()  # hold this task "in progress" so a second one can race in
        return ig_publish.ContainerResult(True, creation_id="c1")

    monkeypatch.setattr(ig_publish, "create_reel_container", slow_create)
    monkeypatch.setattr(ig_publish, "poll_container_status", lambda creation_id, **kw: _status_finished())
    monkeypatch.setattr(ig_publish, "publish_container", lambda creation_id, **kw: _ok_publish("m1"))

    job = _job(row_id="row-race")
    task1 = asyncio.create_task(
        runner.run_publish_job(job, state_path=state_path, poll_interval_s=0, poll_max_s=5)
    )
    await asyncio.sleep(0)  # let task1 reach the gate and claim _RUNNING_ROW_IDS
    result2 = await runner.run_publish_job(job, state_path=state_path, poll_interval_s=0, poll_max_s=5)

    assert result2 is False  # the second call backed off immediately
    assert create_calls["n"] == 1  # only ONE container was ever created

    gate.set()
    result1 = await task1
    assert result1 is True


@pytest.mark.asyncio
async def test_running_guard_is_released_after_success(
    state_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(ig_publish, "create_reel_container", lambda **kw: _ok_container("c1"))
    monkeypatch.setattr(ig_publish, "poll_container_status", lambda creation_id, **kw: _status_finished())
    monkeypatch.setattr(ig_publish, "publish_container", lambda creation_id, **kw: _ok_publish("m1"))

    await runner.run_publish_job(_job(row_id="row-x"), state_path=state_path, poll_interval_s=0, poll_max_s=5)

    assert "row-x" not in runner._RUNNING_ROW_IDS


@pytest.mark.asyncio
async def test_running_guard_is_released_after_failure(
    state_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    async def fake_create(**kw):
        return ig_publish.ContainerResult(False, detail="boom")

    monkeypatch.setattr(ig_publish, "create_reel_container", fake_create)

    await runner.run_publish_job(_job(row_id="row-y"), state_path=state_path)

    assert "row-y" not in runner._RUNNING_ROW_IDS


# -------------------------------------------------- H2: git push off the lock


@pytest.mark.asyncio
async def test_git_push_happens_with_lock_released(
    state_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """The lock must be released BEFORE the (potentially slow) git push —
    otherwise every other job's ledger update stalls behind a subprocess
    call for as long as it takes."""
    lock_was_held_during_push = {"value": None}

    # asyncio.to_thread wraps a SYNC callable — push_paths is called via
    # to_thread in the implementation, so the spy must be sync too.
    def spy_push_sync(paths, message):
        lock_was_held_during_push["value"] = runner._STATE_LOCK.locked()
        return {"ok": True, "detail": "faked"}

    monkeypatch.setattr(runner.git_publish, "push_paths", spy_push_sync)

    await runner._update_ledger(state_path, "row-z", status="published")

    assert lock_was_held_during_push["value"] is False


# ------------------------------------------------------- poll interval safety


def test_poll_interval_env_non_numeric_falls_back_to_default(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("IG_PUBLISH_POLL_INTERVAL_S", "not-a-number")
    assert runner._poll_interval_s() == 15.0


def test_poll_interval_env_zero_is_floored_to_minimum(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("IG_PUBLISH_POLL_INTERVAL_S", "0")
    assert runner._poll_interval_s() == runner._MIN_POLL_INTERVAL_S


def test_poll_interval_env_negative_is_floored_to_minimum(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("IG_PUBLISH_POLL_INTERVAL_S", "-5")
    assert runner._poll_interval_s() == runner._MIN_POLL_INTERVAL_S


def test_poll_max_env_non_numeric_falls_back_to_default(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("IG_PUBLISH_POLL_MAX_S", "garbage")
    assert runner._poll_max_s() == 900.0


def test_poll_max_env_negative_clamped_to_zero(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("IG_PUBLISH_POLL_MAX_S", "-100")
    assert runner._poll_max_s() == 0.0


@pytest.mark.asyncio
async def test_run_publish_job_never_raises_on_negative_explicit_poll_override(
    state_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A caller passing a negative override directly must not cause an
    infinite/backwards-moving loop — run_publish_job clamps defensively."""
    async def always_in_progress(creation_id, *, account_id=None):
        return ig_publish.StatusResult(True, status_code="IN_PROGRESS")

    monkeypatch.setattr(ig_publish, "create_reel_container", lambda **kw: _ok_container("c1"))
    monkeypatch.setattr(ig_publish, "poll_container_status", always_in_progress)
    ok = await runner.run_publish_job(
        _job(row_id="row-neg"), state_path=state_path, poll_interval_s=-5, poll_max_s=-5
    )
    assert ok is False  # clamped to 0/0 -> immediate timeout, not an infinite loop


# --------------------------------------------------------- plan_and_dispatch
#
# The shared "resume in-flight -> plan newly-published rows -> spawn a
# background task per new job" sequence, reused by BOTH
# POST /admin/notion-publish (the live, event-driven Notion Automation
# webhook) and the daily schedule sweep (notion_publish_scheduler.py) — one
# code path, so the two triggers can never drift into two different ways to
# dispatch a live Instagram publish.


@pytest.mark.asyncio
async def test_plan_and_dispatch_spawns_a_task_per_claimed_job(monkeypatch: pytest.MonkeyPatch) -> None:
    from src import notion_publish

    job = _job(row_id="row-new")
    monkeypatch.setattr(
        notion_publish, "plan_publishes",
        lambda **kw: {"checked": 1, "jobs": [job], "skipped": [], "errors": [], "warnings": []},
    )

    async def fake_resume(**kw):
        return 0

    spawned: list[str] = []

    async def fake_run(j, **kw):
        spawned.append(j.row_id)
        return True

    monkeypatch.setattr(runner, "resume_in_flight", fake_resume)
    monkeypatch.setattr(runner, "run_publish_job", fake_run)

    sink: list[asyncio.Task] = []
    result = await runner.plan_and_dispatch(task_sink=sink)

    assert result["claimed"] == ["row-new"]
    assert result["checked"] == 1
    assert result["resumed"] == 0
    await asyncio.sleep(0)
    await asyncio.sleep(0)
    assert spawned == ["row-new"]


@pytest.mark.asyncio
async def test_plan_and_dispatch_calls_resume_before_plan(monkeypatch: pytest.MonkeyPatch) -> None:
    from src import notion_publish

    order: list[str] = []

    async def fake_resume(**kw):
        order.append("resume")
        return 3

    def fake_plan(**kw):
        order.append("plan")
        return {"checked": 0, "jobs": [], "skipped": [], "errors": [], "warnings": []}

    monkeypatch.setattr(runner, "resume_in_flight", fake_resume)
    monkeypatch.setattr(notion_publish, "plan_publishes", fake_plan)

    result = await runner.plan_and_dispatch(task_sink=[])

    assert order == ["resume", "plan"]
    assert result["resumed"] == 3


@pytest.mark.asyncio
async def test_plan_and_dispatch_propagates_planning_errors(monkeypatch: pytest.MonkeyPatch) -> None:
    """Callers (the webhook, the scheduler) decide how to handle a planning
    failure — plan_and_dispatch itself must not swallow it."""
    from src import notion_publish

    async def fake_resume(**kw):
        return 0

    def boom(**kw):
        raise notion_publish.NotionSyncError("simulated Notion outage")

    monkeypatch.setattr(runner, "resume_in_flight", fake_resume)
    monkeypatch.setattr(notion_publish, "plan_publishes", boom)

    with pytest.raises(notion_publish.NotionSyncError):
        await runner.plan_and_dispatch(task_sink=[])


@pytest.mark.asyncio
async def test_plan_and_dispatch_defaults_to_its_own_task_sink_when_none_given(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """No task_sink passed must not crash — the spawned task still needs a
    strong reference held somewhere for its lifetime."""
    from src import notion_publish

    job = _job(row_id="row-no-sink")
    monkeypatch.setattr(
        notion_publish, "plan_publishes",
        lambda **kw: {"checked": 1, "jobs": [job], "skipped": [], "errors": [], "warnings": []},
    )

    async def fake_resume(**kw):
        return 0

    async def fake_run(j, **kw):
        return True

    monkeypatch.setattr(runner, "resume_in_flight", fake_resume)
    monkeypatch.setattr(runner, "run_publish_job", fake_run)

    result = await runner.plan_and_dispatch()
    assert result["claimed"] == ["row-no-sink"]
    await asyncio.sleep(0)
