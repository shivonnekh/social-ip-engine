"""Tests for src/notion_publish_fb_runner.py — async create->poll->publish
->checkbox for one Facebook Reels mirror. Mirrors the coverage shape of
tests/test_notion_publish_runner.py (Instagram's runner tests); all
external calls (fb_publish, Notion PATCH, git push) are faked.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from src import notion_publish_fb_runner as runner
from src.channels import fb_publish
from src.notion_publish import PublishJob


def _job(row_id: str = "row-1", creation_id: str = "") -> PublishJob:
    return PublishJob(
        row_id=row_id, account_id="fb-acct-1", video_url="https://s3.example/v.mp4",
        cover_url="https://example.com/cover.jpg", caption="hi", creation_id=creation_id,
    )


@pytest.fixture()
def state_path(tmp_path: Path) -> Path:
    return tmp_path / "notion_publish_fb_state.json"


@pytest.fixture(autouse=True)
def _no_real_side_effects(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> list:
    pushed_calls: list[tuple[list[str], str]] = []
    monkeypatch.setattr(
        runner.git_publish, "push_paths",
        lambda paths, message: (pushed_calls.append((paths, message)) or {"ok": True, "detail": "faked"}),
    )
    monkeypatch.setattr(runner, "_ncall", lambda method, path, body=None: {})
    monkeypatch.setattr(runner, "_POSTED_PENDING_PATH", tmp_path / "notion_publish_fb_posted_pending.json")
    return pushed_calls


def _ledger(state_path: Path) -> dict:
    return json.loads(state_path.read_text()) if state_path.exists() else {}


async def _ok_container(creation_id: str):
    return fb_publish.ContainerResult(True, creation_id=creation_id)


async def _ok_publish(media_id: str):
    return fb_publish.PublishResult(True, media_id=media_id)


# ---------------------------------------------------------------- happy path


@pytest.mark.asyncio
async def test_full_happy_path_creates_polls_publishes_ticks_checkbox(
    state_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(fb_publish, "create_reel_container", lambda **kw: _ok_container("vid-1"))
    poll_calls = {"n": 0}

    async def fake_poll(creation_id, *, account_id=None):
        poll_calls["n"] += 1
        status = "processing" if poll_calls["n"] < 2 else "upload_complete"
        return fb_publish.StatusResult(True, status_code=status)

    monkeypatch.setattr(fb_publish, "poll_container_status", fake_poll)

    publish_calls = []

    async def fake_publish(creation_id, caption="", **kw):
        publish_calls.append((creation_id, caption))
        return fb_publish.PublishResult(True, media_id=creation_id)

    monkeypatch.setattr(fb_publish, "publish_container", fake_publish)

    ok = await runner.run_publish_job(_job(), state_path=state_path, poll_interval_s=0, poll_max_s=5)

    assert ok is True
    assert poll_calls["n"] == 2
    assert publish_calls == [("vid-1", "hi")]  # caption threaded through to finish call
    ledger = _ledger(state_path)
    assert ledger["row-1"]["status"] == "published"
    assert ledger["row-1"]["fb_media_id"] == "vid-1"
    assert ledger["row-1"]["posted_checkbox"] is True


# ------------------------------------------------------------------ create step


@pytest.mark.asyncio
async def test_create_failure_marks_ledger_failed(state_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    async def fake_create(**kw):
        return fb_publish.ContainerResult(False, detail="upload session failed")

    monkeypatch.setattr(fb_publish, "create_reel_container", fake_create)

    ok = await runner.run_publish_job(_job(), state_path=state_path)

    assert ok is False
    ledger = _ledger(state_path)
    assert ledger["row-1"]["status"] == "failed"
    assert "upload session" in ledger["row-1"]["last_error"]


@pytest.mark.asyncio
async def test_existing_creation_id_skips_create_call(
    state_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """The core no-duplicate-post guarantee, FB side: resuming a job that
    already has a creation_id must NEVER create a second upload session."""
    create_calls = {"n": 0}

    async def fake_create(**kw):
        create_calls["n"] += 1
        return fb_publish.ContainerResult(True, creation_id="SHOULD-NOT-BE-CALLED")

    async def fake_poll(creation_id, *, account_id=None):
        assert creation_id == "existing-video-id"
        return fb_publish.StatusResult(True, status_code="upload_complete")

    async def fake_publish(creation_id, caption="", **kw):
        return fb_publish.PublishResult(True, media_id=creation_id)

    monkeypatch.setattr(fb_publish, "create_reel_container", fake_create)
    monkeypatch.setattr(fb_publish, "poll_container_status", fake_poll)
    monkeypatch.setattr(fb_publish, "publish_container", fake_publish)

    ok = await runner.run_publish_job(
        _job(creation_id="existing-video-id"), state_path=state_path, poll_interval_s=0, poll_max_s=5
    )

    assert ok is True
    assert create_calls["n"] == 0


# ------------------------------------------------------------------- poll step


@pytest.mark.asyncio
async def test_terminal_failure_status_marks_failed_no_publish_call(
    state_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(fb_publish, "create_reel_container", lambda **kw: _ok_container("v1"))

    async def fake_poll(creation_id, *, account_id=None):
        return fb_publish.StatusResult(True, status_code="error")

    publish_calls = {"n": 0}

    async def fake_publish(creation_id, caption="", **kw):
        publish_calls["n"] += 1
        return fb_publish.PublishResult(True, media_id="should-not-happen")

    monkeypatch.setattr(fb_publish, "poll_container_status", fake_poll)
    monkeypatch.setattr(fb_publish, "publish_container", fake_publish)

    ok = await runner.run_publish_job(_job(), state_path=state_path, poll_interval_s=0, poll_max_s=5)

    assert ok is False
    assert publish_calls["n"] == 0
    ledger = _ledger(state_path)
    assert ledger["row-1"]["status"] == "failed"
    assert "error" in ledger["row-1"]["last_error"]


@pytest.mark.asyncio
async def test_poll_timeout_marks_failed(state_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(fb_publish, "create_reel_container", lambda **kw: _ok_container("v1"))

    async def always_processing(creation_id, *, account_id=None):
        return fb_publish.StatusResult(True, status_code="processing")

    monkeypatch.setattr(fb_publish, "poll_container_status", always_processing)

    ok = await runner.run_publish_job(_job(), state_path=state_path, poll_interval_s=0, poll_max_s=0)

    assert ok is False
    ledger = _ledger(state_path)
    assert ledger["row-1"]["status"] == "failed"
    assert "timeout" in ledger["row-1"]["last_error"]


# ---------------------------------------------------------------- publish step


@pytest.mark.asyncio
async def test_publish_failure_marks_ledger_failed(state_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(fb_publish, "create_reel_container", lambda **kw: _ok_container("v1"))
    monkeypatch.setattr(
        fb_publish, "poll_container_status",
        lambda creation_id, **kw: _status_upload_complete(),
    )

    async def fake_publish(creation_id, caption="", **kw):
        return fb_publish.PublishResult(False, detail="video_id expired")

    monkeypatch.setattr(fb_publish, "publish_container", fake_publish)

    ok = await runner.run_publish_job(_job(), state_path=state_path, poll_interval_s=0, poll_max_s=5)

    assert ok is False
    ledger = _ledger(state_path)
    assert ledger["row-1"]["status"] == "failed"
    assert "expired" in ledger["row-1"]["last_error"]


async def _status_upload_complete():
    return fb_publish.StatusResult(True, status_code="upload_complete")


# --------------------------------------------------------------- checkbox step


@pytest.mark.asyncio
async def test_checkbox_failure_does_not_undo_published_status(
    state_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(fb_publish, "create_reel_container", lambda **kw: _ok_container("v1"))
    monkeypatch.setattr(fb_publish, "poll_container_status", lambda *a, **kw: _status_upload_complete())
    monkeypatch.setattr(fb_publish, "publish_container", lambda *a, **kw: _ok_publish("v1"))
    monkeypatch.setattr(runner, "_ncall", lambda *a, **kw: (_ for _ in ()).throw(RuntimeError("notion down")))

    ok = await runner.run_publish_job(_job(), state_path=state_path, poll_interval_s=0, poll_max_s=5)

    assert ok is True  # publish succeeded — checkbox is cosmetic
    ledger = _ledger(state_path)
    assert ledger["row-1"]["status"] == "published"
    assert ledger["row-1"]["posted_checkbox"] is False


# ------------------------------------------------------------- concurrency


@pytest.mark.asyncio
async def test_same_row_id_never_runs_twice_concurrently(
    state_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """The FB-specific reentrancy guard — must be independent from
    Instagram's (same Notion row_id, different platform, must never
    wrongly block each other — this test only proves FB blocks FB). Uses
    the exact ``asyncio.sleep(0)`` synchronization pattern already proven
    in tests/test_notion_publish_runner.py's equivalent IG test."""
    import asyncio

    create_calls = {"n": 0}
    gate = asyncio.Event()

    async def slow_create(**kw):
        create_calls["n"] += 1
        await gate.wait()
        return fb_publish.ContainerResult(True, creation_id="v1")

    monkeypatch.setattr(fb_publish, "create_reel_container", slow_create)
    monkeypatch.setattr(fb_publish, "poll_container_status", lambda *a, **kw: _status_upload_complete())
    monkeypatch.setattr(fb_publish, "publish_container", lambda *a, **kw: _ok_publish("v1"))

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


# ------------------------------------------------------------- feature flag


@pytest.mark.asyncio
async def test_plan_and_dispatch_fb_noop_when_disabled(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("NOTION_PUBLISH_FB_ENABLED", raising=False)
    result = await runner.plan_and_dispatch_fb()
    assert result["enabled"] is False
    assert result["claimed"] == []


@pytest.mark.asyncio
async def test_plan_and_dispatch_fb_runs_when_enabled(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("NOTION_PUBLISH_FB_ENABLED", "true")
    monkeypatch.setattr(runner, "resume_in_flight", _async_noop_zero)
    monkeypatch.setattr(
        runner.notion_publish, "plan_fb_mirrors",
        lambda: {"checked": 0, "jobs": [], "skipped": []},
    )
    result = await runner.plan_and_dispatch_fb()
    assert result["enabled"] is True
    assert result["claimed"] == []


async def _async_noop_zero() -> int:
    return 0
