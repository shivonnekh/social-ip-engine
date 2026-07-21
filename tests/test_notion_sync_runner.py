"""Tests for src/notion_sync_runner.py — the shared dispatch path for the
Notion "Ready to Publish" comment-keyword sync, used by BOTH the live
webhook (POST /admin/notion-sync) and the interval-poll scheduler.
"""

from __future__ import annotations

import asyncio

import pytest

from src import notion_sync, notion_sync_runner


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


@pytest.fixture(autouse=True)
def _no_real_git_push(monkeypatch: pytest.MonkeyPatch):
    """git_publish.push_paths short-circuits cleanly when GITHUB_PUSH_TOKEN
    is unset (returns {"ok": False, ...} without touching the network)."""
    monkeypatch.delenv("GITHUB_PUSH_TOKEN", raising=False)


@pytest.mark.asyncio
async def test_run_sync_returns_sync_once_result(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(notion_sync, "sync_once", lambda: _fake_sync_result(checked=5))
    result = await notion_sync_runner.run_sync()
    assert result["checked"] == 5


@pytest.mark.asyncio
async def test_run_sync_pushes_full_paths_when_rules_changed(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        notion_sync, "sync_once",
        lambda: _fake_sync_result(rules_changed=True, added=["guasha"]),
    )
    pushed_paths = []

    def fake_push(paths, *, message):
        pushed_paths.append(list(paths))
        return {"ok": True}

    monkeypatch.setattr("src.git_publish.push_paths", fake_push)

    result = await notion_sync_runner.run_sync()

    assert result["git_push"] == {"ok": True}
    assert "data/channels/comment_responses.json" in pushed_paths[0]


@pytest.mark.asyncio
async def test_run_sync_pushes_state_only_when_rules_unchanged(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(notion_sync, "sync_once", lambda: _fake_sync_result(rules_changed=False))
    pushed_paths = []

    def fake_push(paths, *, message):
        pushed_paths.append(list(paths))
        return {"ok": True}

    monkeypatch.setattr("src.git_publish.push_paths", fake_push)

    await notion_sync_runner.run_sync()

    assert "data/channels/comment_responses.json" not in pushed_paths[0]
    assert "data/channels/notion_sync_state.json" in pushed_paths[0]


@pytest.mark.asyncio
async def test_concurrent_calls_are_serialized_not_overlapped(monkeypatch: pytest.MonkeyPatch) -> None:
    """Code-review finding (2026-07-21): the live webhook (event-driven) and
    the interval-poll scheduler (every ~120s) can both call run_sync() at
    roughly the same time. Without a lock, two overlapping sync_once() runs
    would race on comment_responses.json/notion_sync_state.json and on the
    shared git working tree (git_publish.push_paths() runs raw git
    add/commit/push subprocess commands). This test proves the SECOND call
    only starts its own sync_once() after the FIRST has fully finished —
    never interleaved.

    Uses a real (short) blocking sleep inside sync_once (dispatched onto a
    genuine OS thread via run_in_threadpool, exactly as production does) so
    two overlapping calls have a real window to race in if the lock were
    ever removed — without a real sleep here, both calls could finish so
    fast that the assertion would pass "by accident" regardless of whether
    the lock actually works, which would defeat the point of this test."""
    import time

    active = 0
    max_concurrent = 0
    call_order: list[str] = []

    def slow_sync_once():
        nonlocal active, max_concurrent
        active += 1
        max_concurrent = max(max_concurrent, active)
        call_order.append("start")
        time.sleep(0.05)
        active -= 1
        call_order.append("end")
        return _fake_sync_result()

    monkeypatch.setattr(notion_sync, "sync_once", slow_sync_once)
    monkeypatch.setattr("src.git_publish.push_paths", lambda *a, **kw: {"ok": True})

    await asyncio.gather(
        notion_sync_runner.run_sync(),
        notion_sync_runner.run_sync(),
    )

    assert max_concurrent == 1
    # Each call's sync_once must fully start-then-end before the next starts.
    assert call_order == ["start", "end", "start", "end"]
