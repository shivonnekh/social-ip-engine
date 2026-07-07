"""src/ops_alert.py — best-effort Slack-compatible webhook alerting.

Built after the 2026-07-06/07 anxiety-comment incident: a correctly-logged
failure sat unnoticed until a lead complained. These tests lock the three
contracts that make this safe to sprinkle into request/background paths
unconditionally:
    1. No-ops (never raises, never blocks) when unconfigured.
    2. Debounces repeats of the same incident so a burst never floods Slack.
    3. Never raises on transport/HTTP failure.
"""

from __future__ import annotations

import pytest

from src import ops_alert


@pytest.fixture(autouse=True)
def _reset_debounce_state(monkeypatch):
    """Every test starts with a clean debounce dict and no ambient config."""
    monkeypatch.setattr(ops_alert, "_last_sent", {})
    monkeypatch.delenv("OPS_ALERT_WEBHOOK_URL", raising=False)
    monkeypatch.delenv("OPS_ALERT_COOLDOWN_S", raising=False)


@pytest.mark.asyncio
async def test_noop_when_webhook_url_unset():
    # Must not raise even though no URL is configured.
    await ops_alert.send_ops_alert("key1", "test message")


@pytest.mark.asyncio
async def test_sends_when_configured(monkeypatch):
    monkeypatch.setenv("OPS_ALERT_WEBHOOK_URL", "https://hooks.example.com/x")
    posted = []

    class _FakeResp:
        status_code = 200
        text = "ok"

    class _FakeClient:
        def __init__(self, *a, **kw):
            pass

        async def __aenter__(self):
            return self

        async def __aexit__(self, *a):
            return False

        async def post(self, url, *, json=None):
            posted.append((url, json))
            return _FakeResp()

    monkeypatch.setattr(ops_alert.httpx, "AsyncClient", _FakeClient)

    await ops_alert.send_ops_alert("key1", "hello ops")

    assert posted == [("https://hooks.example.com/x", {"text": "hello ops"})]


@pytest.mark.asyncio
async def test_debounces_repeated_key(monkeypatch):
    monkeypatch.setenv("OPS_ALERT_WEBHOOK_URL", "https://hooks.example.com/x")
    monkeypatch.setenv("OPS_ALERT_COOLDOWN_S", "9999")  # effectively "never expires" for this test
    posted = []

    class _FakeResp:
        status_code = 200
        text = "ok"

    class _FakeClient:
        def __init__(self, *a, **kw):
            pass

        async def __aenter__(self):
            return self

        async def __aexit__(self, *a):
            return False

        async def post(self, url, *, json=None):
            posted.append(json)
            return _FakeResp()

    monkeypatch.setattr(ops_alert.httpx, "AsyncClient", _FakeClient)

    # Same key fired 3 times in a row (mirrors Meta's redelivery bursts) —
    # only the first should actually reach the webhook.
    await ops_alert.send_ops_alert("burst_key", "first")
    await ops_alert.send_ops_alert("burst_key", "second")
    await ops_alert.send_ops_alert("burst_key", "third")

    assert len(posted) == 1
    assert posted[0] == {"text": "first"}


@pytest.mark.asyncio
async def test_different_keys_not_debounced_against_each_other(monkeypatch):
    monkeypatch.setenv("OPS_ALERT_WEBHOOK_URL", "https://hooks.example.com/x")
    posted = []

    class _FakeResp:
        status_code = 200
        text = "ok"

    class _FakeClient:
        def __init__(self, *a, **kw):
            pass

        async def __aenter__(self):
            return self

        async def __aexit__(self, *a):
            return False

        async def post(self, url, *, json=None):
            posted.append(json)
            return _FakeResp()

    monkeypatch.setattr(ops_alert.httpx, "AsyncClient", _FakeClient)

    await ops_alert.send_ops_alert("key_a", "alpha")
    await ops_alert.send_ops_alert("key_b", "beta")

    assert posted == [{"text": "alpha"}, {"text": "beta"}]


@pytest.mark.asyncio
async def test_transport_error_never_raises(monkeypatch):
    monkeypatch.setenv("OPS_ALERT_WEBHOOK_URL", "https://hooks.example.com/x")

    class _FakeClient:
        def __init__(self, *a, **kw):
            pass

        async def __aenter__(self):
            return self

        async def __aexit__(self, *a):
            return False

        async def post(self, url, *, json=None):
            import httpx
            raise httpx.ConnectError("boom")

    monkeypatch.setattr(ops_alert.httpx, "AsyncClient", _FakeClient)

    # Must not raise.
    await ops_alert.send_ops_alert("key1", "will fail to send")


@pytest.mark.asyncio
async def test_non_2xx_response_never_raises(monkeypatch):
    monkeypatch.setenv("OPS_ALERT_WEBHOOK_URL", "https://hooks.example.com/x")

    class _FakeResp:
        status_code = 500
        text = "server error"

    class _FakeClient:
        def __init__(self, *a, **kw):
            pass

        async def __aenter__(self):
            return self

        async def __aexit__(self, *a):
            return False

        async def post(self, url, *, json=None):
            return _FakeResp()

    monkeypatch.setattr(ops_alert.httpx, "AsyncClient", _FakeClient)

    # Must not raise.
    await ops_alert.send_ops_alert("key1", "will get a 500")
