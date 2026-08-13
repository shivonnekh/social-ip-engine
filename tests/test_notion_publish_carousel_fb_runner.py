"""Tests for src/notion_publish_carousel_fb_runner.py — async
create-photos->publish->checkbox for one Facebook Page carousel mirror.

No poll step to test here (see fb_publish_carousel.py's module docstring —
a Page photo has no Meta-side processing step). The behavior unique to
this runner is photo-id resumability, mirroring the IG carousel runner's
item-container resumability.
"""

from __future__ import annotations

import asyncio
import json
from pathlib import Path

import pytest

from src import notion_publish_carousel_fb_runner as runner
from src.channels import fb_publish_carousel
from src.notion_publish_carousel import CarouselPublishJob

PANELS = ("https://s3.example/p1.png", "https://s3.example/p2.png", "https://s3.example/p3.png")


def _job(row_id: str = "row-1", item_creation_ids: tuple = ()) -> CarouselPublishJob:
    return CarouselPublishJob(
        row_id=row_id, account_id="fb-page-1", image_urls=PANELS, caption="hi",
        item_creation_ids=item_creation_ids,
    )


@pytest.fixture()
def state_path(tmp_path: Path) -> Path:
    return tmp_path / "notion_publish_carousel_fb_state.json"


@pytest.fixture(autouse=True)
def _no_real_side_effects(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> list:
    pushed_calls: list[tuple[list[str], str]] = []
    monkeypatch.setattr(
        runner.git_publish, "push_paths",
        lambda paths, message: (pushed_calls.append((paths, message)) or {"ok": True, "detail": "faked"}),
    )
    monkeypatch.setattr(runner, "_ncall", lambda method, path, body=None: {})
    monkeypatch.setattr(
        runner, "_POSTED_PENDING_PATH", tmp_path / "notion_publish_carousel_fb_posted_pending.json"
    )
    return pushed_calls


def _ledger(state_path: Path) -> dict:
    return json.loads(state_path.read_text()) if state_path.exists() else {}


async def _ok_photo(photo_id: str):
    return fb_publish_carousel.PhotoResult(True, photo_id=photo_id)


async def _ok_post(post_id: str):
    return fb_publish_carousel.PublishResult(True, post_id=post_id)


# ---------------------------------------------------------------- happy path


@pytest.mark.asyncio
async def test_full_happy_path_creates_photos_then_publishes(
    state_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    photo_calls: list[str] = []

    async def fake_photo(image_url, *, account_id=None):
        photo_calls.append(image_url)
        return fb_publish_carousel.PhotoResult(True, photo_id=f"photo-{len(photo_calls)}")

    monkeypatch.setattr(fb_publish_carousel, "create_unpublished_photo", fake_photo)
    monkeypatch.setattr(
        fb_publish_carousel, "publish_carousel_post",
        lambda photo_ids, **kw: _ok_post("post-1"),
    )

    ok = await runner.run_publish_job(_job(), state_path=state_path)

    assert ok is True
    assert photo_calls == list(PANELS)
    ledger = _ledger(state_path)
    assert ledger["row-1"]["status"] == "published"
    assert ledger["row-1"]["item_creation_ids"] == ["photo-1", "photo-2", "photo-3"]
    assert ledger["row-1"]["fb_media_id"] == "post-1"
    assert ledger["row-1"]["posted_checkbox"] is True


# ---------------------------------------------------------- photo resumability


@pytest.mark.asyncio
async def test_resumes_with_two_photos_already_created(
    state_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    photo_calls: list[str] = []

    async def fake_photo(image_url, *, account_id=None):
        photo_calls.append(image_url)
        return fb_publish_carousel.PhotoResult(True, photo_id="photo-3")

    monkeypatch.setattr(fb_publish_carousel, "create_unpublished_photo", fake_photo)
    monkeypatch.setattr(
        fb_publish_carousel, "publish_carousel_post", lambda photo_ids, **kw: _ok_post("post-1")
    )

    job = _job(item_creation_ids=("photo-1", "photo-2"))
    ok = await runner.run_publish_job(job, state_path=state_path)

    assert ok is True
    assert photo_calls == [PANELS[2]]
    ledger = _ledger(state_path)
    assert ledger["row-1"]["item_creation_ids"] == ["photo-1", "photo-2", "photo-3"]


@pytest.mark.asyncio
async def test_photo_failure_partway_persists_progress_and_marks_failed(
    state_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    calls = {"n": 0}

    async def flaky_photo(image_url, *, account_id=None):
        calls["n"] += 1
        if calls["n"] == 2:
            return fb_publish_carousel.PhotoResult(False, detail="rate limited")
        return fb_publish_carousel.PhotoResult(True, photo_id=f"photo-{calls['n']}")

    monkeypatch.setattr(fb_publish_carousel, "create_unpublished_photo", flaky_photo)

    ok = await runner.run_publish_job(_job(), state_path=state_path)

    assert ok is False
    ledger = _ledger(state_path)
    assert ledger["row-1"]["status"] == "failed"
    assert ledger["row-1"]["item_creation_ids"] == ["photo-1"]
    assert "rate limited" in ledger["row-1"]["last_error"]


@pytest.mark.asyncio
async def test_publish_failure_marks_failed_without_reattempting_photos(
    state_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    photo_calls: list[str] = []

    async def fake_photo(image_url, *, account_id=None):
        photo_calls.append(image_url)
        return fb_publish_carousel.PhotoResult(True, photo_id=f"photo-{len(photo_calls)}")

    async def fail_publish(photo_ids, **kw):
        return fb_publish_carousel.PublishResult(False, detail="feed rejected")

    monkeypatch.setattr(fb_publish_carousel, "create_unpublished_photo", fake_photo)
    monkeypatch.setattr(fb_publish_carousel, "publish_carousel_post", fail_publish)

    ok = await runner.run_publish_job(_job(), state_path=state_path)

    assert ok is False
    assert photo_calls == list(PANELS)  # photos were created once
    ledger = _ledger(state_path)
    assert ledger["row-1"]["status"] == "failed"
    assert "feed rejected" in ledger["row-1"]["last_error"]


# ---------------------------------------------------------------- concurrency guard


@pytest.mark.asyncio
async def test_concurrent_run_publish_job_same_row_only_one_proceeds(
    state_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    gate = asyncio.Event()
    create_calls = {"n": 0}

    async def slow_photo(image_url, *, account_id=None):
        create_calls["n"] += 1
        await gate.wait()
        return fb_publish_carousel.PhotoResult(True, photo_id=f"photo-{create_calls['n']}")

    monkeypatch.setattr(fb_publish_carousel, "create_unpublished_photo", slow_photo)
    monkeypatch.setattr(
        fb_publish_carousel, "publish_carousel_post", lambda photo_ids, **kw: _ok_post("post-1")
    )

    job = _job(row_id="row-race")
    task1 = asyncio.create_task(runner.run_publish_job(job, state_path=state_path))
    await asyncio.sleep(0)
    result2 = await runner.run_publish_job(job, state_path=state_path)

    assert result2 is False
    assert create_calls["n"] == 1

    gate.set()
    result1 = await task1
    assert result1 is True


@pytest.mark.asyncio
async def test_running_guard_released_after_failure(
    state_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    async def fail_photo(image_url, *, account_id=None):
        return fb_publish_carousel.PhotoResult(False, detail="boom")

    monkeypatch.setattr(fb_publish_carousel, "create_unpublished_photo", fail_photo)

    await runner.run_publish_job(_job(row_id="row-y"), state_path=state_path)

    assert "row-y" not in runner._RUNNING_ROW_IDS


# ---------------------------------------------------------------- kill switch


def test_fb_carousel_disabled_by_default(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("NOTION_PUBLISH_CAROUSEL_FB_ENABLED", raising=False)
    assert runner.fb_carousel_enabled() is False


def test_fb_carousel_enabled_when_flag_true(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("NOTION_PUBLISH_CAROUSEL_FB_ENABLED", "true")
    assert runner.fb_carousel_enabled() is True


@pytest.mark.asyncio
async def test_plan_and_dispatch_carousel_fb_is_a_noop_when_disabled(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("NOTION_PUBLISH_CAROUSEL_FB_ENABLED", "false")
    result = await runner.plan_and_dispatch_carousel_fb()
    assert result == {"enabled": False, "checked": 0, "claimed": [], "resumed": 0, "skipped": []}
