"""Tests for src/token_health.py — the Meta access-token watchdog.

The failure this guards against was invisible for a month (see the module
docstring), so these tests care most about the properties that made it
invisible: an auth failure MUST produce an alert, an alert MUST name the
env var, and nothing here may ever raise into the loop that calls it.
"""

from __future__ import annotations

import pytest

from src import token_health
from src.ips.registry import ChannelConfig


@pytest.fixture(autouse=True)
def _clean_env(monkeypatch):
    monkeypatch.delenv("TOKEN_HEALTH_ENABLED", raising=False)
    monkeypatch.delenv("TOKEN_HEALTH_INTERVAL_S", raising=False)


class _FakeResp:
    def __init__(self, payload, status_code=200):
        self._payload = payload
        self.status_code = status_code

    def json(self):
        return self._payload


def _fake_client(handler):
    """Build a stand-in httpx.AsyncClient whose .get calls `handler(params)`."""

    class _FakeClient:
        def __init__(self, *a, **kw):
            pass

        async def __aenter__(self):
            return self

        async def __aexit__(self, *a):
            return False

        async def get(self, url, *, params=None, headers=None):
            return handler({**(params or {}), **_bearer(headers)})

    return _FakeClient


def _bearer(headers):
    """Expose the bearer token to handlers under the same key the old
    query-param form used, so tests can key off the token value."""
    auth = (headers or {}).get("Authorization", "")
    return {"access_token": auth[7:]} if auth.startswith("Bearer ") else {}


EXPIRED_PAYLOAD = {
    "error": {
        "message": "Error validating access token: Session has expired on Friday, "
                   "04-Sep-26 22:30:41 PDT.",
        "type": "OAuthException",
        "code": 190,
    }
}


# --------------------------------------------------------------------------
# classification
# --------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_live_token_is_ok(monkeypatch):
    monkeypatch.setenv("TOK", "real-token")
    monkeypatch.setattr(
        token_health.httpx, "AsyncClient",
        _fake_client(lambda p: _FakeResp({"id": "1", "username": "jackiechan.tcm"})),
    )
    s = await token_health.check_token("TOK", "instagram", "acct1", "Jackie instagram")
    assert s.status == token_health.OK
    assert s.healthy and not s.needs_attention


@pytest.mark.asyncio
async def test_expired_token_is_flagged(monkeypatch):
    monkeypatch.setenv("TOK", "dead-token")
    monkeypatch.setattr(
        token_health.httpx, "AsyncClient",
        _fake_client(lambda p: _FakeResp(EXPIRED_PAYLOAD, 400)),
    )
    s = await token_health.check_token("TOK", "instagram", "acct1", "Jackie instagram")
    assert s.status == token_health.EXPIRED
    assert s.needs_attention
    assert "Session has expired" in s.detail


@pytest.mark.asyncio
async def test_unset_token_is_missing_not_expired(monkeypatch):
    """Different cause, different fix — collapsing these sends whoever is
    on call to the wrong runbook (re-authorise vs. never configured)."""
    monkeypatch.delenv("TOK", raising=False)
    s = await token_health.check_token("TOK", "instagram", "acct1", "Jackie instagram")
    assert s.status == token_health.MISSING
    assert s.needs_attention


@pytest.mark.asyncio
async def test_transient_server_error_is_unknown_and_does_not_page(monkeypatch):
    """A Meta 5xx / network blip must NOT be reported as a dead token —
    a watchdog that cries wolf gets muted, and then it protects nothing."""
    monkeypatch.setenv("TOK", "real-token")
    monkeypatch.setattr(
        token_health.httpx, "AsyncClient",
        _fake_client(lambda p: _FakeResp({}, 503)),
    )
    s = await token_health.check_token("TOK", "instagram", "acct1", "Jackie instagram")
    assert s.status == token_health.UNKNOWN
    assert not s.needs_attention


@pytest.mark.asyncio
async def test_unrelated_error_mentioning_session_does_not_page(monkeypatch):
    """A non-auth error whose copy happens to say "session" must NOT be
    reported as an expired token. False pages get the alert muted, and a
    muted watchdog protects nothing."""
    monkeypatch.setenv("TOK", "real-token")
    monkeypatch.setattr(
        token_health.httpx, "AsyncClient",
        _fake_client(lambda p: _FakeResp({
            "error": {
                "message": "Application request limit reached for this session",
                "type": "GraphMethodException",
                "code": 4,
            }
        }, 400)),
    )
    s = await token_health.check_token("TOK", "instagram", "acct1", "Jackie instagram")
    assert s.status == token_health.UNKNOWN
    assert not s.needs_attention


@pytest.mark.asyncio
async def test_oauth_error_without_code_190_still_counts_as_expired(monkeypatch):
    """Belt and braces: an auth-typed error that says "expired" is trusted
    even if Meta ever stops setting code 190."""
    monkeypatch.setenv("TOK", "real-token")
    monkeypatch.setattr(
        token_health.httpx, "AsyncClient",
        _fake_client(lambda p: _FakeResp({
            "error": {"message": "Session has expired", "type": "OAuthException"}
        }, 400)),
    )
    s = await token_health.check_token("TOK", "instagram", "acct1", "Jackie instagram")
    assert s.status == token_health.EXPIRED


@pytest.mark.asyncio
async def test_transport_exception_never_raises(monkeypatch):
    monkeypatch.setenv("TOK", "real-token")

    def _boom(params):
        raise RuntimeError("connection reset")

    monkeypatch.setattr(token_health.httpx, "AsyncClient", _fake_client(_boom))
    s = await token_health.check_token("TOK", "instagram", "acct1", "Jackie instagram")
    assert s.status == token_health.UNKNOWN
    assert not s.needs_attention


# --------------------------------------------------------------------------
# host selection — the bug that would make a healthy token look dead
# --------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_instagram_is_checked_on_the_instagram_graph_host(monkeypatch):
    """IGAA tokens only validate against graph.instagram.com. Checking them
    on graph.facebook.com would report every healthy IG token as broken."""
    monkeypatch.setenv("TOK", "real-token")
    monkeypatch.delenv("IG_GRAPH_BASE", raising=False)
    monkeypatch.delenv("META_GRAPH_BASE", raising=False)
    seen = {}

    class _FakeClient:
        def __init__(self, *a, **kw):
            pass

        async def __aenter__(self):
            return self

        async def __aexit__(self, *a):
            return False

        async def get(self, url, *, params=None, headers=None):
            seen["url"] = url
            return _FakeResp({"id": "1", "username": "x"})

    monkeypatch.setattr(token_health.httpx, "AsyncClient", _FakeClient)
    await token_health.check_token("TOK", "instagram", "acct1", "Jackie instagram")
    assert "graph.instagram.com" in seen["url"]


@pytest.mark.asyncio
async def test_token_never_appears_in_the_request_url(monkeypatch):
    """httpx logs every request URL at INFO. A token in the query string is
    therefore a live credential written into the log stream — which is
    exactly how production logs ended up containing valid IG tokens
    (found 2026-09-07). It must travel in the Authorization header."""
    secret = "IGAAWsuperSECRETtokenVALUE"
    monkeypatch.setenv("TOK", secret)
    seen = {}

    class _FakeClient:
        def __init__(self, *a, **kw):
            pass

        async def __aenter__(self):
            return self

        async def __aexit__(self, *a):
            return False

        async def get(self, url, *, params=None, headers=None):
            seen["url"] = url
            seen["params"] = params or {}
            seen["headers"] = headers or {}
            return _FakeResp({"id": "1", "username": "x"})

    monkeypatch.setattr(token_health.httpx, "AsyncClient", _FakeClient)
    await token_health.check_token("TOK", "instagram", "acct1", "Jackie instagram")

    assert secret not in seen["url"]
    assert secret not in str(seen["params"])
    assert seen["headers"].get("Authorization") == f"Bearer {secret}"


# --------------------------------------------------------------------------
# alerting
# --------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_expired_token_fires_exactly_one_alert_naming_the_env_var(monkeypatch):
    sent = []

    async def _capture(key, text):
        sent.append((key, text))

    monkeypatch.setattr(token_health, "send_ops_alert", _capture)
    monkeypatch.setattr(
        token_health, "_configured_tokens",
        lambda: [("IG_PAGE_ACCESS_TOKEN_JACKIE", "instagram", "17841417304649448", "Jackie instagram")],
    )
    monkeypatch.setenv("IG_PAGE_ACCESS_TOKEN_JACKIE", "dead")
    monkeypatch.setattr(
        token_health.httpx, "AsyncClient",
        _fake_client(lambda p: _FakeResp(EXPIRED_PAYLOAD, 400)),
    )

    statuses = await token_health.run_token_health_check()

    assert len(sent) == 1
    key, text = sent[0]
    assert key == "token_health:IG_PAGE_ACCESS_TOKEN_JACKIE"
    assert "IG_PAGE_ACCESS_TOKEN_JACKIE" in text
    assert "republish-row" in text  # the non-obvious recovery step
    assert len(statuses) == 1


@pytest.mark.asyncio
async def test_alert_never_contains_the_token_value(monkeypatch):
    """Alerts go to a chat webhook. Leaking a live token into Slack would
    turn a monitoring feature into a credential disclosure."""
    sent = []

    async def _capture(key, text):
        sent.append(text)

    secret = "IGAAWsuperSECRETtokenVALUE"
    monkeypatch.setattr(token_health, "send_ops_alert", _capture)
    monkeypatch.setattr(
        token_health, "_configured_tokens",
        lambda: [("IG_TOK", "instagram", "acct1", "Jackie instagram")],
    )
    monkeypatch.setenv("IG_TOK", secret)
    monkeypatch.setattr(
        token_health.httpx, "AsyncClient",
        _fake_client(lambda p: _FakeResp(EXPIRED_PAYLOAD, 400)),
    )

    await token_health.run_token_health_check()

    assert sent, "expected an alert"
    assert all(secret not in t for t in sent)


@pytest.mark.asyncio
async def test_healthy_tokens_produce_no_alert(monkeypatch):
    sent = []

    async def _capture(key, text):
        sent.append(text)

    monkeypatch.setattr(token_health, "send_ops_alert", _capture)
    monkeypatch.setattr(
        token_health, "_configured_tokens",
        lambda: [("IG_TOK", "instagram", "acct1", "Jackie instagram")],
    )
    monkeypatch.setenv("IG_TOK", "good")
    monkeypatch.setattr(
        token_health.httpx, "AsyncClient",
        _fake_client(lambda p: _FakeResp({"id": "1", "username": "x"})),
    )

    await token_health.run_token_health_check()
    assert sent == []


@pytest.mark.asyncio
async def test_one_dead_token_still_lets_the_others_be_checked(monkeypatch):
    """Per-account isolation: the whole point is that Chloe being dead for
    a month must not hide Jackie's status (or vice versa)."""
    sent = []

    async def _capture(key, text):
        sent.append(key)

    monkeypatch.setattr(token_health, "send_ops_alert", _capture)
    monkeypatch.setattr(
        token_health, "_configured_tokens",
        lambda: [
            ("IG_A", "instagram", "a", "Chloe instagram"),
            ("IG_B", "instagram", "b", "Jackie instagram"),
        ],
    )
    monkeypatch.setenv("IG_A", "dead")
    monkeypatch.setenv("IG_B", "good")

    def _handler(params):
        if params.get("access_token") == "dead":
            return _FakeResp(EXPIRED_PAYLOAD, 400)
        return _FakeResp({"id": "1", "username": "ok"})

    monkeypatch.setattr(token_health.httpx, "AsyncClient", _fake_client(_handler))

    statuses = await token_health.run_token_health_check()

    assert sorted(s.env_var for s in statuses) == ["IG_A", "IG_B"]
    assert sent == ["token_health:IG_A"]


# --------------------------------------------------------------------------
# registry wiring
# --------------------------------------------------------------------------

def test_shared_env_var_is_only_checked_once(monkeypatch):
    """Chloe's Instagram and the global default are the SAME env var —
    checking it twice would double-alert for one real problem."""

    class _IP:
        def __init__(self, name, channels):
            self.display_name = name
            self.channels = channels

    ch = ChannelConfig(
        account_id="acct1", token_env="IG_PAGE_ACCESS_TOKEN",
        user_id_env="IG_USER_ID", comments="canned", dms="persona",
    )
    monkeypatch.setattr(
        token_health.ip_registry, "all_ips",
        lambda: (_IP("A", {"instagram": ch}), _IP("B", {"instagram": ch})),
    )
    assert [t[0] for t in token_health._configured_tokens()] == ["IG_PAGE_ACCESS_TOKEN"]


def test_real_registry_covers_the_tokens_that_actually_broke():
    """Guards the wiring itself: if ip.json stops being the source of
    truth, this watchdog silently watches nothing."""
    env_vars = {t[0] for t in token_health._configured_tokens()}
    assert "IG_PAGE_ACCESS_TOKEN" in env_vars          # Chloe — dead since 2026-08-04
    assert "IG_PAGE_ACCESS_TOKEN_JACKIE" in env_vars   # Jackie — dead since 2026-09-04


# --------------------------------------------------------------------------
# config
# --------------------------------------------------------------------------

def test_enabled_by_default():
    assert token_health._enabled() is True


def test_can_be_disabled(monkeypatch):
    monkeypatch.setenv("TOKEN_HEALTH_ENABLED", "false")
    assert token_health._enabled() is False


def test_interval_has_a_floor(monkeypatch):
    """A typo'd '1' must not turn a watchdog into a Graph API hammer."""
    monkeypatch.setenv("TOKEN_HEALTH_INTERVAL_S", "1")
    assert token_health._interval_seconds() == 300.0


def test_garbage_interval_falls_back_to_default(monkeypatch):
    monkeypatch.setenv("TOKEN_HEALTH_INTERVAL_S", "soon")
    assert token_health._interval_seconds() == 6 * 60 * 60


@pytest.mark.asyncio
async def test_disabled_loop_returns_immediately(monkeypatch):
    monkeypatch.setenv("TOKEN_HEALTH_ENABLED", "false")
    called = []
    monkeypatch.setattr(
        token_health, "run_token_health_check",
        lambda: called.append(1),
    )
    await token_health.start_token_health_loop()
    assert called == []
