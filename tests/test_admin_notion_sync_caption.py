"""Tests for POST /admin/notion-sync's caption-burn dispatch wiring
(src/web.py::admin_notion_sync, the ``_caption_enabled()`` gated block).

The endpoint imports its collaborators LOCALLY inside the function body
(``from src import git_publish, notion_sync`` / ``from src import
notion_caption_gen``) — a fresh lookup on every call — so monkeypatching the
SOURCE modules is picked up correctly without needing to patch anything on
``src.web`` itself. Mirrors tests/test_admin_notion_publish.py's style
exactly: call the endpoint function directly with a minimal fake
``Request``, avoiding the cost of booting the full app lifespan.

THE SAFETY-CRITICAL ASSERTION IN THIS FILE: NOTION_SYNC_CAPTION_ENABLED must
default OFF. A caption burn spends real CPU/RAM on the same process serving
live Instagram traffic — a false default-on would mean this deploy silently
starts burning captions on production the moment it ships.
"""

from __future__ import annotations

import asyncio

import pytest

from src import notion_sync, web


class _FakeAppState:
    pass


class _FakeApp:
    def __init__(self):
        self.state = _FakeAppState()


class _FakeRequest:
    def __init__(self, headers: dict[str, str] | None = None):
        self.headers = headers or {}
        self.app = _FakeApp()


SECRET = "test-secret-123"


@pytest.fixture(autouse=True)
def _secret(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("NOTION_SYNC_SECRET", SECRET)


@pytest.fixture(autouse=True)
def _no_real_git_push(monkeypatch: pytest.MonkeyPatch):
    """git_publish.push_paths short-circuits cleanly when GITHUB_PUSH_TOKEN
    is unset (returns {"ok": False, ...} without touching the network) —
    ensure that's the state for every test here regardless of the real dev
    environment's .env."""
    monkeypatch.delenv("GITHUB_PUSH_TOKEN", raising=False)


def _fake_sync_result(**overrides) -> dict:
    base = {
        "checked": 1,
        "added": [],
        "skipped": [],
        "errors": [],
        "warnings": [],
        "rules_changed": False,
        "media_paths": [],
        "covers_generated": 0,
        "caption_pending": [],
    }
    base.update(overrides)
    return base


@pytest.mark.asyncio
async def test_caption_disabled_by_default_leaves_app_state_untouched(
    monkeypatch: pytest.MonkeyPatch,
):
    monkeypatch.delenv("NOTION_SYNC_CAPTION_ENABLED", raising=False)
    monkeypatch.setattr(
        notion_sync, "sync_once",
        lambda: _fake_sync_result(
            caption_pending=[{"row_id": "row-1", "video_url": "https://x/raw.mp4"}]
        ),
    )

    fake_request = _FakeRequest({"X-Sync-Secret": SECRET})
    resp = await web.admin_notion_sync(fake_request)

    assert resp.status_code == 200
    assert getattr(fake_request.app.state, "notion_caption_tasks", None) is None


@pytest.mark.asyncio
async def test_caption_enabled_dispatches_up_to_cap(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setenv("NOTION_SYNC_CAPTION_ENABLED", "1")
    monkeypatch.setenv("NOTION_SYNC_MAX_CAPTION_RENDERS", "1")
    monkeypatch.setattr(
        notion_sync, "sync_once",
        lambda: _fake_sync_result(
            caption_pending=[
                {"row_id": "row-1", "video_url": "https://x/raw1.mp4"},
                {"row_id": "row-2", "video_url": "https://x/raw2.mp4"},
            ]
        ),
    )

    from src import notion_caption_gen

    spawned: list[str] = []

    async def fake_burn(row_id: str, video_url: str, **kw):
        spawned.append(row_id)
        return None

    monkeypatch.setattr(notion_caption_gen, "burn_captions_for_row", fake_burn)

    fake_request = _FakeRequest({"X-Sync-Secret": SECRET})
    resp = await web.admin_notion_sync(fake_request)

    assert resp.status_code == 200
    tasks = fake_request.app.state.notion_caption_tasks
    assert len(tasks) == 1  # capped at NOTION_SYNC_MAX_CAPTION_RENDERS=1

    await asyncio.sleep(0)
    await asyncio.sleep(0)
    assert spawned == ["row-1"]  # only the first pending row, respecting the cap


@pytest.mark.asyncio
async def test_caption_enabled_default_cap_is_one(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setenv("NOTION_SYNC_CAPTION_ENABLED", "1")
    monkeypatch.delenv("NOTION_SYNC_MAX_CAPTION_RENDERS", raising=False)
    monkeypatch.setattr(
        notion_sync, "sync_once",
        lambda: _fake_sync_result(
            caption_pending=[
                {"row_id": "row-1", "video_url": "https://x/raw1.mp4"},
                {"row_id": "row-2", "video_url": "https://x/raw2.mp4"},
                {"row_id": "row-3", "video_url": "https://x/raw3.mp4"},
            ]
        ),
    )

    from src import notion_caption_gen

    async def fake_burn(row_id: str, video_url: str, **kw):
        return None

    monkeypatch.setattr(notion_caption_gen, "burn_captions_for_row", fake_burn)

    fake_request = _FakeRequest({"X-Sync-Secret": SECRET})
    await web.admin_notion_sync(fake_request)

    assert len(fake_request.app.state.notion_caption_tasks) == 1


@pytest.mark.asyncio
async def test_endpoint_returns_before_dispatched_caption_task_finishes(
    monkeypatch: pytest.MonkeyPatch,
):
    """The webhook response must return as soon as tasks are DISPATCHED, not
    when they complete — use a coroutine that would hang forever (waits on
    an Event that's never set) and confirm this test doesn't hang."""
    monkeypatch.setenv("NOTION_SYNC_CAPTION_ENABLED", "1")
    monkeypatch.setattr(
        notion_sync, "sync_once",
        lambda: _fake_sync_result(
            caption_pending=[{"row_id": "row-1", "video_url": "https://x/raw.mp4"}]
        ),
    )

    from src import notion_caption_gen

    never_set = asyncio.Event()

    async def hanging_burn(row_id: str, video_url: str, **kw):
        await never_set.wait()  # would hang forever if actually awaited
        return None

    monkeypatch.setattr(notion_caption_gen, "burn_captions_for_row", hanging_burn)

    fake_request = _FakeRequest({"X-Sync-Secret": SECRET})
    resp = await asyncio.wait_for(web.admin_notion_sync(fake_request), timeout=2.0)

    assert resp.status_code == 200
    # The task was dispatched (created) but is still pending -- confirms it
    # was never awaited directly by the endpoint itself.
    task = fake_request.app.state.notion_caption_tasks[0]
    assert not task.done()
    task.cancel()  # cleanup — don't leak a hanging task past this test


@pytest.mark.asyncio
async def test_caption_enabled_but_no_pending_rows_dispatches_nothing(
    monkeypatch: pytest.MonkeyPatch,
):
    monkeypatch.setenv("NOTION_SYNC_CAPTION_ENABLED", "1")
    monkeypatch.setattr(notion_sync, "sync_once", lambda: _fake_sync_result(caption_pending=[]))

    fake_request = _FakeRequest({"X-Sync-Secret": SECRET})
    resp = await web.admin_notion_sync(fake_request)

    assert resp.status_code == 200
    assert fake_request.app.state.notion_caption_tasks == []


# ------------------------------------------------------ unit: env-flag helpers


def test_caption_enabled_defaults_off(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.delenv("NOTION_SYNC_CAPTION_ENABLED", raising=False)
    assert web._caption_enabled() is False


def test_caption_enabled_true_only_for_exact_string_one(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setenv("NOTION_SYNC_CAPTION_ENABLED", "1")
    assert web._caption_enabled() is True

    monkeypatch.setenv("NOTION_SYNC_CAPTION_ENABLED", "0")
    assert web._caption_enabled() is False

    monkeypatch.setenv("NOTION_SYNC_CAPTION_ENABLED", "yes")
    assert web._caption_enabled() is False  # only the literal "1" turns it on


def test_caption_render_cap_default_and_override(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.delenv("NOTION_SYNC_MAX_CAPTION_RENDERS", raising=False)
    assert web._caption_render_cap() == 1

    monkeypatch.setenv("NOTION_SYNC_MAX_CAPTION_RENDERS", "3")
    assert web._caption_render_cap() == 3


def test_caption_render_cap_invalid_value_falls_back_to_default(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setenv("NOTION_SYNC_MAX_CAPTION_RENDERS", "not-a-number")
    assert web._caption_render_cap() == 1
