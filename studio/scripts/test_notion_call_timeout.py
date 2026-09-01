"""Tests for the Notion `call()` transport guards in notion_prompts / notion_fanout.

Why this file exists
--------------------
On 2026-09-01 a `notion_fanout.py` run sat at 0.17 seconds of CPU for THIRTY
MINUTES and stalled a ten-concept batch queued behind it. There was no
exception, no retry, no output — `urllib.request.urlopen(req)` was called with
no `timeout`, so a stalled TCP connection simply blocked forever. Worse, it had
already created the production row and hung part-way through `apply_shot_plan`,
leaving that row with 3 of 4 shots and a half-written body: silent corruption,
not just a delay.

Two guards were added to `call()` in BOTH modules (they carry a duplicated copy
of the same helper):

  1. every request passes `timeout=NOTION_TIMEOUT_S`
  2. transport-level failures (timeout / DNS / reset) retry with backoff
     instead of either hanging or dying

A retry guard nobody has watched fire is not a guard, so both are exercised here
against a fake `urlopen`. These are the only I/O-touching tests in this folder —
justified because the thing under test IS the I/O behaviour.

Run: cd studio && python3 -m pytest scripts/test_notion_call_timeout.py -q
"""
from __future__ import annotations

import importlib
import io
import json
import urllib.error

import pytest

MODULES = ["notion_prompts", "notion_fanout"]


class _Resp(io.BytesIO):
    """Minimal stand-in for the object urlopen() yields as a context manager."""

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return False


def _ok_body() -> _Resp:
    return _Resp(json.dumps({"ok": True}).encode())


@pytest.fixture(params=MODULES)
def mod(request, monkeypatch):
    m = importlib.import_module(request.param)
    monkeypatch.setenv("NOTION_KEY", "secret_test_key")
    monkeypatch.setattr(m.time, "sleep", lambda *_: None)  # no real backoff waits
    return m


def test_every_request_carries_a_timeout(mod, monkeypatch):
    """The actual regression: a request with no timeout can hang forever."""
    seen: list[object] = []

    def fake_urlopen(req, timeout=None):
        seen.append(timeout)
        return _ok_body()

    monkeypatch.setattr(mod.urllib.request, "urlopen", fake_urlopen)
    assert mod.call("GET", "/pages/abc") == {"ok": True}
    assert seen == [mod.NOTION_TIMEOUT_S]
    assert isinstance(mod.NOTION_TIMEOUT_S, (int, float))
    assert 0 < mod.NOTION_TIMEOUT_S <= 120, "a timeout this long is barely a timeout"


def test_transport_timeout_is_retried_then_succeeds(mod, monkeypatch):
    """A TimeoutError must be retried, not raised and not hung on."""
    calls = {"n": 0}

    def fake_urlopen(req, timeout=None):
        calls["n"] += 1
        if calls["n"] < 3:
            raise TimeoutError("read timed out")
        return _ok_body()

    monkeypatch.setattr(mod.urllib.request, "urlopen", fake_urlopen)
    assert mod.call("POST", "/blocks/abc/children", {"children": []}) == {"ok": True}
    assert calls["n"] == 3, "expected two retries before the success"


def test_url_error_is_retried(mod, monkeypatch):
    """DNS / connection-reset failures are routine on a long batch run."""
    calls = {"n": 0}

    def fake_urlopen(req, timeout=None):
        calls["n"] += 1
        if calls["n"] < 2:
            raise urllib.error.URLError("connection reset by peer")
        return _ok_body()

    monkeypatch.setattr(mod.urllib.request, "urlopen", fake_urlopen)
    assert mod.call("GET", "/pages/abc") == {"ok": True}
    assert calls["n"] == 2


def test_transport_failure_eventually_exits_rather_than_looping(mod, monkeypatch):
    """Retries are bounded — a permanently dead connection must end the run
    loudly, never spin forever (which is just the original hang with extra steps)."""

    def fake_urlopen(req, timeout=None):
        raise TimeoutError("still dead")

    monkeypatch.setattr(mod.urllib.request, "urlopen", fake_urlopen)
    with pytest.raises(SystemExit) as excinfo:
        mod.call("GET", "/pages/abc", retries=3)
    assert "TimeoutError" in str(excinfo.value)


def test_http_500_is_retried_but_400_is_not(mod, monkeypatch):
    """A 5xx is worth retrying; a 4xx is our own bad request and never will be."""
    calls = {"n": 0}

    def flaky(req, timeout=None):
        calls["n"] += 1
        if calls["n"] == 1:
            raise urllib.error.HTTPError(
                "https://api.notion.com", 502, "Bad Gateway", {}, io.BytesIO(b"upstream")
            )
        return _ok_body()

    monkeypatch.setattr(mod.urllib.request, "urlopen", flaky)
    assert mod.call("GET", "/pages/abc") == {"ok": True}
    assert calls["n"] == 2

    def always_400(req, timeout=None):
        raise urllib.error.HTTPError(
            "https://api.notion.com", 400, "Bad Request", {}, io.BytesIO(b"validation_error")
        )

    monkeypatch.setattr(mod.urllib.request, "urlopen", always_400)
    with pytest.raises(SystemExit):
        mod.call("GET", "/pages/abc")
