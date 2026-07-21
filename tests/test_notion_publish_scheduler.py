"""Tests for src/notion_publish_scheduler.py — the daily sweep that catches
any row deferred by a future ``Publish Date`` once that date arrives.

The live "go live" trigger (``POST /admin/notion-publish``) is
event-driven: a Notion Automation calls it the instant Stage flips to
"✅ Published". A row with a future ``Publish Date`` gets deferred (see
``notion_publish._publish_date_eligible``) with no future event to
re-check it — this scheduler is that missing "somebody checks back."
"""

from __future__ import annotations

from datetime import datetime
from zoneinfo import ZoneInfo

import pytest

from src import notion_publish_scheduler as sched

_HKT = ZoneInfo("Asia/Hong_Kong")


@pytest.fixture(autouse=True)
def _clean_env(monkeypatch: pytest.MonkeyPatch) -> None:
    for var in (
        "NOTION_PUBLISH_SCHEDULE_ENABLED",
        "NOTION_PUBLISH_SCHEDULE_HOUR_HKT",
        "NOTION_PUBLISH_SCHEDULE_MINUTE_HKT",
        "NOTION_PUBLISH_SCHEDULE_INTERVAL_S",
    ):
        monkeypatch.delenv(var, raising=False)


# --------------------------------------------------------- seconds_until_next_run


def test_seconds_until_next_run_same_day_when_before_target() -> None:
    now = datetime(2026, 7, 7, 6, 0, tzinfo=_HKT)
    assert sched.seconds_until_next_run(now, hour=9, minute=0) == pytest.approx(3 * 3600)


def test_seconds_until_next_run_rolls_to_tomorrow_when_past_target() -> None:
    now = datetime(2026, 7, 7, 9, 30, tzinfo=_HKT)
    assert sched.seconds_until_next_run(now, hour=9, minute=0) == pytest.approx(23.5 * 3600)


def test_seconds_until_next_run_never_zero_or_negative_at_exact_target() -> None:
    """At the EXACT target instant, must roll to tomorrow (never return 0),
    otherwise a loop computing this every iteration could spin without
    ever actually sleeping."""
    now = datetime(2026, 7, 7, 9, 0, tzinfo=_HKT)
    assert sched.seconds_until_next_run(now, hour=9, minute=0) == pytest.approx(24 * 3600)


def test_seconds_until_next_run_converts_from_other_timezone() -> None:
    utc = ZoneInfo("UTC")
    now = datetime(2026, 7, 7, 0, 30, tzinfo=utc)  # == 08:30 HKT
    assert sched.seconds_until_next_run(now, hour=9, minute=0) == pytest.approx(0.5 * 3600)


def test_seconds_until_next_run_respects_minute() -> None:
    now = datetime(2026, 7, 7, 8, 45, tzinfo=_HKT)
    assert sched.seconds_until_next_run(now, hour=9, minute=15) == pytest.approx(0.5 * 3600)


# ------------------------------------------------------------------- env config


def test_disabled_by_default() -> None:
    assert sched._enabled() is False


def test_enabled_when_env_true(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("NOTION_PUBLISH_SCHEDULE_ENABLED", "true")
    assert sched._enabled() is True


def test_enabled_is_case_insensitive(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("NOTION_PUBLISH_SCHEDULE_ENABLED", "TRUE")
    assert sched._enabled() is True


def test_target_hour_defaults_to_9() -> None:
    assert sched._target_hour() == 9


def test_target_hour_reads_env(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("NOTION_PUBLISH_SCHEDULE_HOUR_HKT", "14")
    assert sched._target_hour() == 14


def test_target_hour_non_numeric_falls_back_to_default(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("NOTION_PUBLISH_SCHEDULE_HOUR_HKT", "not-a-number")
    assert sched._target_hour() == 9


def test_target_hour_out_of_range_falls_back_to_default(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("NOTION_PUBLISH_SCHEDULE_HOUR_HKT", "99")
    assert sched._target_hour() == 9


def test_target_minute_defaults_to_0() -> None:
    assert sched._target_minute() == 0


def test_target_minute_out_of_range_falls_back_to_default(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("NOTION_PUBLISH_SCHEDULE_MINUTE_HKT", "-1")
    assert sched._target_minute() == 0


# ------------------------------------------------------------- interval mode


def test_interval_seconds_unset_by_default() -> None:
    assert sched._interval_seconds() is None


def test_interval_seconds_reads_env(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("NOTION_PUBLISH_SCHEDULE_INTERVAL_S", "120")
    assert sched._interval_seconds() == 120


def test_interval_seconds_non_numeric_falls_back_to_none(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("NOTION_PUBLISH_SCHEDULE_INTERVAL_S", "not-a-number")
    assert sched._interval_seconds() is None


def test_interval_seconds_zero_or_negative_falls_back_to_none(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("NOTION_PUBLISH_SCHEDULE_INTERVAL_S", "0")
    assert sched._interval_seconds() is None
    monkeypatch.setenv("NOTION_PUBLISH_SCHEDULE_INTERVAL_S", "-5")
    assert sched._interval_seconds() is None


# -------------------------------------------------------------- run_scheduled_sweep


@pytest.mark.asyncio
async def test_run_scheduled_sweep_calls_plan_and_dispatch(monkeypatch: pytest.MonkeyPatch) -> None:
    calls: list[list] = []

    async def fake_dispatch(*, task_sink=None):
        calls.append(task_sink)
        return {"checked": 1, "claimed": [], "resumed": 0, "skipped": [], "errors": [], "warnings": []}

    monkeypatch.setattr("src.notion_publish_runner.plan_and_dispatch", fake_dispatch)

    result = await sched.run_scheduled_sweep()

    assert result["checked"] == 1
    assert len(calls) == 1
    assert calls[0] is sched._scheduler_tasks  # uses ITS OWN task sink, not the webhook's


@pytest.mark.asyncio
async def test_run_scheduled_sweep_never_raises_on_failure(monkeypatch: pytest.MonkeyPatch) -> None:
    """No external retry exists for the scheduler (unlike Notion, which
    retries the webhook on timeout) — a failure here must be swallowed and
    logged, never crash the long-running loop."""
    async def boom(*, task_sink=None):
        raise RuntimeError("simulated Notion outage")

    monkeypatch.setattr("src.notion_publish_runner.plan_and_dispatch", boom)

    result = await sched.run_scheduled_sweep()

    assert "error" in result


@pytest.mark.asyncio
async def test_run_scheduled_sweep_failure_sends_ops_alert(monkeypatch: pytest.MonkeyPatch) -> None:
    """Unlike the live webhook (whose 502 is visible to the Notion
    Automation, which can see/retry it), this loop has no external
    observer — a silently-broken daily sweep would leave any deferred row
    stuck forever with nobody notified. Must alert exactly like
    src.channels.reconciliation.run_reconciliation_sweep does on failure."""
    async def boom(*, task_sink=None):
        raise RuntimeError("simulated Notion outage")

    alerts: list[tuple[str, str]] = []

    async def fake_alert(key: str, text: str) -> None:
        alerts.append((key, text))

    monkeypatch.setattr("src.notion_publish_runner.plan_and_dispatch", boom)
    monkeypatch.setattr(sched, "send_ops_alert", fake_alert)

    await sched.run_scheduled_sweep()

    assert len(alerts) == 1
    key, text = alerts[0]
    assert "notion_publish_schedule" in key
    assert "simulated Notion outage" in text


@pytest.mark.asyncio
async def test_run_scheduled_sweep_with_errors_in_result_sends_ops_alert(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A sweep that completes without raising but reports per-row errors
    (e.g. a transient Notion API failure on one row) must also alert — the
    exception-only path above doesn't cover this case."""
    async def fake_dispatch(*, task_sink=None):
        return {
            "checked": 2, "claimed": [], "resumed": 0, "skipped": [],
            "errors": ["row-x: transient failure"], "warnings": [],
        }

    alerts: list[tuple[str, str]] = []

    async def fake_alert(key: str, text: str) -> None:
        alerts.append((key, text))

    monkeypatch.setattr("src.notion_publish_runner.plan_and_dispatch", fake_dispatch)
    monkeypatch.setattr(sched, "send_ops_alert", fake_alert)

    await sched.run_scheduled_sweep()

    assert len(alerts) == 1


@pytest.mark.asyncio
async def test_run_scheduled_sweep_clean_result_does_not_alert(monkeypatch: pytest.MonkeyPatch) -> None:
    async def fake_dispatch(*, task_sink=None):
        return {
            "checked": 1, "claimed": ["row-1"], "resumed": 0, "skipped": [],
            "errors": [], "warnings": [],
        }

    alerts: list[tuple[str, str]] = []

    async def fake_alert(key: str, text: str) -> None:
        alerts.append((key, text))

    monkeypatch.setattr("src.notion_publish_runner.plan_and_dispatch", fake_dispatch)
    monkeypatch.setattr(sched, "send_ops_alert", fake_alert)

    await sched.run_scheduled_sweep()

    assert alerts == []


# --------------------------------------------------------- start_publish_schedule_loop


@pytest.mark.asyncio
async def test_start_loop_noop_when_disabled(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("NOTION_PUBLISH_SCHEDULE_ENABLED", "false")
    ran = []

    async def fake_sweep():
        ran.append(True)

    monkeypatch.setattr(sched, "run_scheduled_sweep", fake_sweep)
    # Must return immediately (not hang forever in the sleep loop).
    await sched.start_publish_schedule_loop()
    assert ran == []


@pytest.mark.asyncio
async def test_start_loop_uses_interval_mode_when_configured(monkeypatch: pytest.MonkeyPatch) -> None:
    """The daily-fixed-hour trigger depends on a Notion Automation existing
    and firing correctly — root-caused 2026-07-21 as unreliable in
    production (a Stage flip to '✅ Published' produced zero requests to
    the live webhook for over an hour). NOTION_PUBLISH_SCHEDULE_INTERVAL_S
    is the self-contained fallback: when set, this service checks Notion
    itself on a short fixed cadence instead of waiting to be told, so
    'the button works' no longer depends on a no-code automation staying
    correctly wired forever. plan_and_dispatch()'s own duplicate-post
    ledger makes checking frequently safe — a sweep with nothing new to do
    is a no-op, exactly like the existing daily sweep."""
    monkeypatch.setenv("NOTION_PUBLISH_SCHEDULE_ENABLED", "true")
    monkeypatch.setenv("NOTION_PUBLISH_SCHEDULE_INTERVAL_S", "5")

    sweep_calls = []

    async def fake_sweep():
        sweep_calls.append(True)

    sleep_calls = []

    async def fake_sleep(seconds):
        # Raised from _sleep (not run_scheduled_sweep) deliberately: the
        # loop body only wraps the sweep call in try/except Exception, so a
        # stop signal raised from inside the sweep would just get logged
        # and swallowed, hanging the test forever instead of stopping it.
        sleep_calls.append(seconds)
        if len(sleep_calls) >= 3:
            raise _StopLoop

    monkeypatch.setattr(sched, "run_scheduled_sweep", fake_sweep)
    monkeypatch.setattr(sched, "_sleep", fake_sleep)

    with pytest.raises(_StopLoop):
        await sched.start_publish_schedule_loop()

    assert len(sweep_calls) == 2  # sleep raises on its 3rd call, before a 3rd sweep runs
    # Interval mode sleeps the configured interval every iteration —
    # never the daily seconds_until_next_run() computation.
    assert sleep_calls == [5, 5, 5]


class _StopLoop(Exception):
    """Sentinel to break out of the intentionally-infinite loop in tests."""
