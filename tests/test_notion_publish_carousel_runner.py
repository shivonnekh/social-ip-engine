"""Tests for src/notion_publish_carousel_runner.py — async
create-items->create-parent->poll->publish->checkbox for one IG carousel.

Same faking convention as test_notion_publish_runner.py. The one behavior
unique to this runner (vs the Reel runner) is item-container resumability —
``_ensure_item_containers`` must persist each item id as it's created and
pick up exactly where a crash left off, never re-creating an already-billed
item container.
"""

from __future__ import annotations

import asyncio
import json
from pathlib import Path

import pytest

from src import notion_publish_carousel_runner as runner
from src.channels import ig_publish, ig_publish_carousel
from src.notion_publish_carousel import CarouselPublishJob

PANELS = ("https://s3.example/p1.png", "https://s3.example/p2.png", "https://s3.example/p3.png")


def _job(row_id: str = "row-1", item_creation_ids: tuple = (), creation_id: str = "") -> CarouselPublishJob:
    return CarouselPublishJob(
        row_id=row_id, account_id="acct-1", image_urls=PANELS, caption="hi",
        item_creation_ids=item_creation_ids, creation_id=creation_id,
    )


@pytest.fixture()
def state_path(tmp_path: Path) -> Path:
    return tmp_path / "notion_publish_carousel_state.json"


@pytest.fixture(autouse=True)
def _no_real_side_effects(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> list:
    pushed_calls: list[tuple[list[str], str]] = []
    monkeypatch.setattr(
        runner.git_publish, "push_paths",
        lambda paths, message: (pushed_calls.append((paths, message)) or {"ok": True, "detail": "faked"}),
    )
    monkeypatch.setattr(runner, "_ncall", lambda method, path, body=None: {})
    monkeypatch.setattr(
        runner, "_POSTED_PENDING_PATH", tmp_path / "notion_publish_carousel_posted_pending.json"
    )
    return pushed_calls


def _ledger(state_path: Path) -> dict:
    return json.loads(state_path.read_text()) if state_path.exists() else {}


async def _ok_item(creation_id: str):
    return ig_publish_carousel.ContainerResult(True, creation_id=creation_id)


async def _ok_container(creation_id: str):
    return ig_publish.ContainerResult(True, creation_id=creation_id)


async def _status_finished():
    return ig_publish.StatusResult(True, status_code=ig_publish.STATUS_FINISHED)


async def _ok_publish(media_id: str):
    return ig_publish.PublishResult(True, media_id=media_id)


# ---------------------------------------------------------------- happy path


@pytest.mark.asyncio
async def test_full_happy_path_creates_items_parent_polls_publishes(
    state_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    item_calls: list[str] = []

    async def fake_item(image_url, *, account_id=None):
        item_calls.append(image_url)
        return ig_publish_carousel.ContainerResult(True, creation_id=f"item-{len(item_calls)}")

    monkeypatch.setattr(ig_publish_carousel, "create_carousel_item_container", fake_item)
    monkeypatch.setattr(
        ig_publish_carousel, "create_carousel_container",
        lambda ids, **kw: _ok_container_carousel("parent-1", ids),
    )
    monkeypatch.setattr(ig_publish, "poll_container_status", lambda creation_id, **kw: _status_finished())
    monkeypatch.setattr(ig_publish, "publish_container", lambda creation_id, **kw: _ok_publish("media-1"))

    ok = await runner.run_publish_job(_job(), state_path=state_path, poll_interval_s=0, poll_max_s=5)

    assert ok is True
    assert item_calls == list(PANELS)
    ledger = _ledger(state_path)
    assert ledger["row-1"]["status"] == "published"
    assert ledger["row-1"]["item_creation_ids"] == ["item-1", "item-2", "item-3"]
    assert ledger["row-1"]["creation_id"] == "parent-1"
    assert ledger["row-1"]["ig_media_id"] == "media-1"
    assert ledger["row-1"]["posted_checkbox"] is True


async def _ok_container_carousel(creation_id: str, item_ids: list[str]):
    return ig_publish_carousel.ContainerResult(True, creation_id=creation_id)


# ---------------------------------------------------------- item resumability


@pytest.mark.asyncio
async def test_resumes_with_two_items_already_created(
    state_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A job resuming after a crash with 2/3 item containers already
    persisted must create ONLY the missing (3rd) item, never re-create the
    first two."""
    item_calls: list[str] = []

    async def fake_item(image_url, *, account_id=None):
        item_calls.append(image_url)
        return ig_publish_carousel.ContainerResult(True, creation_id="item-3")

    monkeypatch.setattr(ig_publish_carousel, "create_carousel_item_container", fake_item)
    monkeypatch.setattr(
        ig_publish_carousel, "create_carousel_container",
        lambda ids, **kw: _ok_container_carousel("parent-1", ids),
    )
    monkeypatch.setattr(ig_publish, "poll_container_status", lambda creation_id, **kw: _status_finished())
    monkeypatch.setattr(ig_publish, "publish_container", lambda creation_id, **kw: _ok_publish("media-1"))

    job = _job(item_creation_ids=("item-1", "item-2"))
    ok = await runner.run_publish_job(job, state_path=state_path, poll_interval_s=0, poll_max_s=5)

    assert ok is True
    assert item_calls == [PANELS[2]]  # only the 3rd, un-created panel
    ledger = _ledger(state_path)
    assert ledger["row-1"]["item_creation_ids"] == ["item-1", "item-2", "item-3"]


@pytest.mark.asyncio
async def test_resumes_with_parent_container_already_created_skips_item_and_parent_creation(
    state_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A job that already has a parent creation_id (all items done, parent
    container created, but crashed before polling finished) must not
    re-create anything — just resume polling/publishing."""
    item_create_called = {"n": 0}
    parent_create_called = {"n": 0}

    async def fake_item(image_url, *, account_id=None):
        item_create_called["n"] += 1
        return ig_publish_carousel.ContainerResult(True, creation_id="unexpected")

    async def fake_parent(ids, **kw):
        parent_create_called["n"] += 1
        return ig_publish_carousel.ContainerResult(True, creation_id="unexpected-parent")

    monkeypatch.setattr(ig_publish_carousel, "create_carousel_item_container", fake_item)
    monkeypatch.setattr(ig_publish_carousel, "create_carousel_container", fake_parent)
    monkeypatch.setattr(ig_publish, "poll_container_status", lambda creation_id, **kw: _status_finished())
    monkeypatch.setattr(ig_publish, "publish_container", lambda creation_id, **kw: _ok_publish("media-1"))

    job = _job(item_creation_ids=("item-1", "item-2", "item-3"), creation_id="parent-already-made")
    ok = await runner.run_publish_job(job, state_path=state_path, poll_interval_s=0, poll_max_s=5)

    assert ok is True
    assert item_create_called["n"] == 0
    assert parent_create_called["n"] == 0
    ledger = _ledger(state_path)
    # _ensure_parent_container short-circuits on an already-set job.creation_id
    # without re-writing it (same convention as the Reel runner's
    # _ensure_container) — the ledger already had this before the resume, in
    # the real flow. What DOES prove no duplicate container was created is
    # the publish succeeding using the pre-existing "parent-already-made" id.
    assert ledger["row-1"]["status"] == "published"
    assert ledger["row-1"]["ig_media_id"] == "media-1"


@pytest.mark.asyncio
async def test_item_container_failure_partway_persists_progress_and_marks_failed(
    state_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    calls = {"n": 0}

    async def flaky_item(image_url, *, account_id=None):
        calls["n"] += 1
        if calls["n"] == 2:
            return ig_publish_carousel.ContainerResult(False, detail="rate limited")
        return ig_publish_carousel.ContainerResult(True, creation_id=f"item-{calls['n']}")

    monkeypatch.setattr(ig_publish_carousel, "create_carousel_item_container", flaky_item)

    ok = await runner.run_publish_job(_job(), state_path=state_path)

    assert ok is False
    ledger = _ledger(state_path)
    assert ledger["row-1"]["status"] == "failed"
    # The FIRST item that succeeded before the failure must still be persisted
    assert ledger["row-1"]["item_creation_ids"] == ["item-1"]
    assert "rate limited" in ledger["row-1"]["last_error"]


# ---------------------------------------------------------------- concurrency guard


@pytest.mark.asyncio
async def test_concurrent_run_publish_job_same_row_only_one_proceeds(
    state_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    gate = asyncio.Event()
    create_calls = {"n": 0}

    async def slow_item(image_url, *, account_id=None):
        create_calls["n"] += 1
        await gate.wait()
        return ig_publish_carousel.ContainerResult(True, creation_id=f"item-{create_calls['n']}")

    monkeypatch.setattr(ig_publish_carousel, "create_carousel_item_container", slow_item)
    monkeypatch.setattr(
        ig_publish_carousel, "create_carousel_container",
        lambda ids, **kw: _ok_container_carousel("parent-1", ids),
    )
    monkeypatch.setattr(ig_publish, "poll_container_status", lambda creation_id, **kw: _status_finished())
    monkeypatch.setattr(ig_publish, "publish_container", lambda creation_id, **kw: _ok_publish("m1"))

    job = _job(row_id="row-race")
    task1 = asyncio.create_task(
        runner.run_publish_job(job, state_path=state_path, poll_interval_s=0, poll_max_s=5)
    )
    await asyncio.sleep(0)
    result2 = await runner.run_publish_job(job, state_path=state_path, poll_interval_s=0, poll_max_s=5)

    assert result2 is False
    assert create_calls["n"] == 1  # the second call never even attempted an item create

    gate.set()
    result1 = await task1
    assert result1 is True


@pytest.mark.asyncio
async def test_running_guard_released_after_failure(
    state_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    async def fail_item(image_url, *, account_id=None):
        return ig_publish_carousel.ContainerResult(False, detail="boom")

    monkeypatch.setattr(ig_publish_carousel, "create_carousel_item_container", fail_item)

    await runner.run_publish_job(_job(row_id="row-y"), state_path=state_path)

    assert "row-y" not in runner._RUNNING_ROW_IDS


# ---------------------------------------------------------------- kill switch


def test_carousel_disabled_by_default(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("NOTION_PUBLISH_CAROUSEL_ENABLED", raising=False)
    assert runner.carousel_enabled() is False


def test_carousel_enabled_when_flag_true(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("NOTION_PUBLISH_CAROUSEL_ENABLED", "true")
    assert runner.carousel_enabled() is True


@pytest.mark.asyncio
async def test_plan_and_dispatch_carousel_is_a_noop_when_disabled(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("NOTION_PUBLISH_CAROUSEL_ENABLED", "false")
    result = await runner.plan_and_dispatch_carousel()
    assert result == {
        "enabled": False, "checked": 0, "claimed": [], "resumed": 0, "skipped": [], "errors": [], "warnings": [],
    }
