"""Tests for src/notion_sync_scheduler.py — the interval-poll fallback for
the "Ready to Publish" comment-keyword sync.

Root-caused 2026-07-21: the Notion Automation that's supposed to call
``POST /admin/notion-sync`` on a Stage flip was found NOT firing in
production (35+ minutes, zero requests to any /admin/* endpoint after a
real Stage flip). This scheduler checks Notion itself on a short fixed
cadence instead, reusing the exact same dispatch path
(``notion_sync_runner.run_sync``) as the live webhook.
"""

from __future__ import annotations

import pytest

from src import notion_sync_scheduler as sched


@pytest.fixture(autouse=True)
def _clean_env(monkeypatch: pytest.MonkeyPatch) -> None:
    for var in ("NOTION_SYNC_SCHEDULE_ENABLED", "NOTION_SYNC_SCHEDULE_INTERVAL_S"):
        monkeypatch.delenv(var, raising=False)


# --------------------------------------------------------------- env config


def test_disabled_by_default() -> None:
    assert sched._enabled() is False


def test_enabled_when_env_true(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("NOTION_SYNC_SCHEDULE_ENABLED", "true")
    assert sched._enabled() is True


def test_enabled_is_case_insensitive(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("NOTION_SYNC_SCHEDULE_ENABLED", "TRUE")
    assert sched._enabled() is True


def test_interval_seconds_defaults_to_120() -> None:
    assert sched._interval_seconds() == 120


def test_interval_seconds_reads_env(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("NOTION_SYNC_SCHEDULE_INTERVAL_S", "45")
    assert sched._interval_seconds() == 45


def test_interval_seconds_non_numeric_falls_back_to_default(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("NOTION_SYNC_SCHEDULE_INTERVAL_S", "not-a-number")
    assert sched._interval_seconds() == 120


def test_interval_seconds_zero_or_negative_falls_back_to_default(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("NOTION_SYNC_SCHEDULE_INTERVAL_S", "0")
    assert sched._interval_seconds() == 120
    monkeypatch.setenv("NOTION_SYNC_SCHEDULE_INTERVAL_S", "-30")
    assert sched._interval_seconds() == 120


# ---------------------------------------------------------- run_scheduled_sync


@pytest.mark.asyncio
async def test_run_scheduled_sync_calls_run_sync(monkeypatch: pytest.MonkeyPatch) -> None:
    calls: list[list] = []

    async def fake_run_sync(*, caption_task_sink=None):
        calls.append(caption_task_sink)
        return {"added": [], "skipped": [], "errors": [], "checked": 1}

    monkeypatch.setattr("src.notion_sync_runner.run_sync", fake_run_sync)

    result = await sched.run_scheduled_sync()

    assert result["checked"] == 1
    assert len(calls) == 1
    assert calls[0] is sched._scheduler_caption_tasks  # uses ITS OWN task sink


@pytest.mark.asyncio
async def test_run_scheduled_sync_never_raises_on_failure(monkeypatch: pytest.MonkeyPatch) -> None:
    """No external retry exists for this scheduler (unlike Notion, which
    retries the live webhook on timeout) — a failure here must be
    swallowed and logged, never crash the long-running loop."""
    async def boom(*, caption_task_sink=None):
        raise RuntimeError("simulated Notion outage")

    monkeypatch.setattr("src.notion_sync_runner.run_sync", boom)

    result = await sched.run_scheduled_sync()

    assert "error" in result


@pytest.mark.asyncio
async def test_run_scheduled_sync_failure_sends_ops_alert(monkeypatch: pytest.MonkeyPatch) -> None:
    async def boom(*, caption_task_sink=None):
        raise RuntimeError("simulated Notion outage")

    alerts: list[tuple[str, str]] = []

    async def fake_alert(key: str, text: str) -> None:
        alerts.append((key, text))

    monkeypatch.setattr("src.notion_sync_runner.run_sync", boom)
    monkeypatch.setattr(sched, "send_ops_alert", fake_alert)

    await sched.run_scheduled_sync()

    assert len(alerts) == 1
    key, text = alerts[0]
    assert "notion_sync_schedule" in key
    assert "simulated Notion outage" in text


@pytest.mark.asyncio
async def test_run_scheduled_sync_with_errors_in_result_sends_ops_alert(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    async def fake_run_sync(*, caption_task_sink=None):
        return {"added": [], "skipped": [], "errors": ["row-x: transient failure"]}

    alerts: list[tuple[str, str]] = []

    async def fake_alert(key: str, text: str) -> None:
        alerts.append((key, text))

    monkeypatch.setattr("src.notion_sync_runner.run_sync", fake_run_sync)
    monkeypatch.setattr(sched, "send_ops_alert", fake_alert)

    await sched.run_scheduled_sync()

    assert len(alerts) == 1


@pytest.mark.asyncio
async def test_run_scheduled_sync_clean_result_does_not_alert(monkeypatch: pytest.MonkeyPatch) -> None:
    async def fake_run_sync(*, caption_task_sink=None):
        return {"added": ["row-1"], "skipped": [], "errors": []}

    alerts: list[tuple[str, str]] = []

    async def fake_alert(key: str, text: str) -> None:
        alerts.append((key, text))

    monkeypatch.setattr("src.notion_sync_runner.run_sync", fake_run_sync)
    monkeypatch.setattr(sched, "send_ops_alert", fake_alert)

    await sched.run_scheduled_sync()

    assert alerts == []


# ------------------------------------------------------- start_sync_schedule_loop


@pytest.mark.asyncio
async def test_start_loop_noop_when_disabled(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("NOTION_SYNC_SCHEDULE_ENABLED", "false")
    ran = []

    async def fake_sync():
        ran.append(True)

    monkeypatch.setattr(sched, "run_scheduled_sync", fake_sync)
    # Must return immediately (not hang forever in the sleep loop).
    await sched.start_sync_schedule_loop()
    assert ran == []


class _StopLoop(Exception):
    """Sentinel to break out of the intentionally-infinite loop in tests."""


@pytest.mark.asyncio
async def test_start_loop_sleeps_the_configured_interval_every_iteration(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("NOTION_SYNC_SCHEDULE_ENABLED", "true")
    monkeypatch.setenv("NOTION_SYNC_SCHEDULE_INTERVAL_S", "7")

    sync_calls = []

    async def fake_sync():
        sync_calls.append(True)

    sleep_calls = []

    async def fake_sleep(seconds):
        # Raised from _sleep (not run_scheduled_sync) deliberately — the
        # loop body only wraps the sync call in try/except Exception, so a
        # stop signal raised from inside the sync would just get logged
        # and swallowed, hanging the test forever instead of stopping it.
        sleep_calls.append(seconds)
        if len(sleep_calls) >= 3:
            raise _StopLoop

    monkeypatch.setattr(sched, "run_scheduled_sync", fake_sync)
    monkeypatch.setattr(sched, "_sleep", fake_sleep)

    with pytest.raises(_StopLoop):
        await sched.start_sync_schedule_loop()

    assert len(sync_calls) == 2  # sleep raises on its 3rd call, before a 3rd sync runs
    assert sleep_calls == [7, 7, 7]
