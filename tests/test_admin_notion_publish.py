"""Tests for POST /admin/notion-publish (src/web.py::admin_notion_publish).

The endpoint imports its collaborators LOCALLY inside the function body
(``from src import notion_publish`` / ``from src.notion_publish_runner
import ...``) — a fresh lookup on every call — so monkeypatching the
SOURCE modules (``notion_publish``, ``notion_publish_runner``) is picked up
correctly without needing to patch anything on ``src.web`` itself.

Tested by calling the endpoint function directly with a minimal fake
``Request`` (it only ever reads ``request.headers``), avoiding the cost of
booting the full app lifespan (CRM connect, KB index, etc.) just to test
one admin endpoint — same reasoning as testing any plain async function.
"""

from __future__ import annotations

import pytest

from src import notion_publish, web
from src.notion_publish import PublishJob


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
def _no_real_resume(monkeypatch: pytest.MonkeyPatch):
    """Default: resume_in_flight is a no-op returning 0, so tests that don't
    care about resume behavior aren't slowed down or affected by it."""
    import src.notion_publish_runner as runner_mod

    async def fake_resume(**kw):
        return 0

    monkeypatch.setattr(runner_mod, "resume_in_flight", fake_resume)
    return runner_mod


@pytest.mark.asyncio
async def test_missing_secret_header_returns_401():
    resp = await web.admin_notion_publish(_FakeRequest())
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_wrong_secret_returns_401():
    resp = await web.admin_notion_publish(_FakeRequest({"X-Sync-Secret": "wrong"}))
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_secret_not_configured_at_all_returns_401(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.delenv("NOTION_SYNC_SECRET", raising=False)
    resp = await web.admin_notion_publish(_FakeRequest({"X-Sync-Secret": "anything"}))
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_correct_secret_plans_and_spawns_jobs(monkeypatch: pytest.MonkeyPatch):
    job = PublishJob(
        row_id="row-1", account_id="acct-1", video_url="https://x/v.mp4",
        cover_url="", caption="hi",
    )
    monkeypatch.setattr(
        notion_publish, "plan_publishes",
        lambda **kw: {"checked": 5, "jobs": [job], "skipped": [], "errors": [], "warnings": []},
    )

    spawned: list[str] = []

    async def fake_run_publish_job(j, **kw):
        spawned.append(j.row_id)
        return True

    import src.notion_publish_runner as runner_mod

    monkeypatch.setattr(runner_mod, "run_publish_job", fake_run_publish_job)

    resp = await web.admin_notion_publish(_FakeRequest({"X-Sync-Secret": SECRET}))

    assert resp.status_code == 200
    body = resp.body.decode()
    assert '"claimed":["row-1"]' in body or "row-1" in body

    # Let the spawned asyncio.create_task actually run before asserting.
    import asyncio

    await asyncio.sleep(0)
    await asyncio.sleep(0)
    assert spawned == ["row-1"]


@pytest.mark.asyncio
async def test_planning_error_returns_502(monkeypatch: pytest.MonkeyPatch):
    def boom(**kw):
        raise notion_publish.NotionSyncError("NOTION_KEY not set")

    monkeypatch.setattr(notion_publish, "plan_publishes", boom)

    resp = await web.admin_notion_publish(_FakeRequest({"X-Sync-Secret": SECRET}))

    assert resp.status_code == 502


@pytest.mark.asyncio
async def test_resume_in_flight_called_before_planning(monkeypatch: pytest.MonkeyPatch):
    order: list[str] = []

    async def fake_resume(**kw):
        order.append("resume")
        return 2

    def fake_plan(**kw):
        order.append("plan")
        return {"checked": 0, "jobs": [], "skipped": [], "errors": [], "warnings": []}

    import src.notion_publish_runner as runner_mod

    monkeypatch.setattr(runner_mod, "resume_in_flight", fake_resume)
    monkeypatch.setattr(notion_publish, "plan_publishes", fake_plan)

    resp = await web.admin_notion_publish(_FakeRequest({"X-Sync-Secret": SECRET}))

    assert resp.status_code == 200
    assert order == ["resume", "plan"]
    import json

    body = json.loads(resp.body.decode())
    assert body["resumed"] == 2


@pytest.mark.asyncio
async def test_corrupt_ledger_during_resume_returns_502_not_silently_zero(
    monkeypatch: pytest.MonkeyPatch,
):
    """A corrupt ledger surfacing during resume must be a loud 502, not
    silently treated as 'nothing to resume' (which would look identical to
    the healthy empty case)."""
    import src.notion_publish_runner as runner_mod

    async def raising_resume(**kw):
        raise notion_publish.LedgerCorruptError("ledger is corrupt")

    monkeypatch.setattr(runner_mod, "resume_in_flight", raising_resume)

    resp = await web.admin_notion_publish(_FakeRequest({"X-Sync-Secret": SECRET}))

    assert resp.status_code == 502


@pytest.mark.asyncio
async def test_no_jobs_returns_empty_claimed_list(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setattr(
        notion_publish, "plan_publishes",
        lambda **kw: {"checked": 3, "jobs": [], "skipped": ["r1: no video"], "errors": [], "warnings": []},
    )
    resp = await web.admin_notion_publish(_FakeRequest({"X-Sync-Secret": SECRET}))
    assert resp.status_code == 200
    import json

    body = json.loads(resp.body.decode())
    assert body["claimed"] == []
    assert body["checked"] == 3
    assert body["skipped"] == ["r1: no video"]
