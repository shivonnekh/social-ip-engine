"""Tests for the fan-out action the Database tab dispatches.

Exercised by calling app.api_action() directly with jobs.start_job stubbed —
no HTTP client and, more importantly, no real fan-out against the live Notion
board (which would create actual Production rows).

The distinction these pin down is a spending one: "fan out" creates rows and
costs nothing, while "fan out + generate assets" immediately runs gpt-image-2
and MiniMax TTS for every resulting row. They must stay two separate actions
mapped to two separate scripts.
"""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent))

import app as dashboard_app  # noqa: E402
import jobs  # noqa: E402


@pytest.fixture
def captured(monkeypatch):
    """Capture what would have been run instead of running it."""
    calls = []

    class _FakeJob:
        id = "job-test"

    def fake_start_job(label, steps):
        calls.append({"label": label, "steps": steps})
        return _FakeJob()

    monkeypatch.setattr(jobs, "start_job", fake_start_job)
    monkeypatch.setattr(dashboard_app.jobs, "start_job", fake_start_job)
    return calls


def _request(**kwargs):
    return dashboard_app.ActionRequest(**kwargs)


def test_fan_out_runs_notion_fanout_not_the_asset_generator(captured):
    """The whole point of the separate action: rows only, no API spend."""
    out = dashboard_app.api_action(
        _request(action="fanout_content", content_id="notion-page-1"))
    assert out["job_id"] == "job-test"
    script, args = captured[0]["steps"][0]
    assert script == "notion_fanout.py"
    assert args == ["--content-id", "notion-page-1"]


def test_fan_out_can_be_scoped_to_one_ip(captured):
    dashboard_app.api_action(
        _request(action="fanout_content", content_id="p1", ip="Chloe Chan (HK)"))
    _script, args = captured[0]["steps"][0]
    assert args == ["--content-id", "p1", "--ip", "Chloe Chan (HK)"]


def test_a_blank_ip_means_all_active_ips_not_an_empty_filter(captured):
    """The UI's "All active IPs" option submits "" — that must NOT become
    `--ip ""`, which would match no IP and silently fan out to nobody."""
    dashboard_app.api_action(
        _request(action="fanout_content", content_id="p1", ip="   "))
    _script, args = captured[0]["steps"][0]
    assert "--ip" not in args


def test_fan_out_requires_a_content_id(captured):
    from fastapi import HTTPException
    with pytest.raises(HTTPException) as exc:
        dashboard_app.api_action(_request(action="fanout_content"))
    assert exc.value.status_code == 400
    assert not captured


def test_the_expensive_path_is_still_a_separate_action(captured):
    dashboard_app.api_action(
        _request(action="generate_assets_content", content_id="p1"))
    script, _args = captured[0]["steps"][0]
    assert script == "generate_assets.py"


def test_fan_out_never_touches_stage():
    """Fan-out creates rows at their default Stage. Nothing in this action
    path may flip Stage — that is /api/stage's job, behind a confirm, because
    it fires a real Instagram post."""
    for action, script in dashboard_app._CONTENT_ACTIONS.items():
        assert "stage" not in action.lower()
        assert script in ("notion_fanout.py", "generate_assets.py")


def test_both_fan_out_scripts_actually_exist_on_disk():
    """A mapping to a script that isn't there fails only at click time, in a
    log drawer, after the user has already committed to the action."""
    scripts_dir = Path(__file__).resolve().parent.parent / "scripts"
    for script in dashboard_app._CONTENT_ACTIONS.values():
        assert (scripts_dir / script).exists(), f"missing {script}"
