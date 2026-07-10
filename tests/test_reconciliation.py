"""src/channels/reconciliation.py — periodic IG comment reconciliation sweep.

Defense-in-depth backstop built after the 2026-07-06/07 anxiety-comment
incident: independently re-derives "what comments exist" from the Graph
API on a schedule and replays anything through the same handle_comment()
the live webhook uses (safe no-op on anything already claimed).
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pytest

from src.channels import meta_client, reconciliation


class _FakePipeline:
    _crm = None


@pytest.fixture(autouse=True)
def _clean_env(monkeypatch):
    for var in ("RECONCILE_ENABLED", "RECONCILE_INTERVAL_S", "RECONCILE_LOOKBACK_H", "RECONCILE_MEDIA_LIMIT"):
        monkeypatch.delenv(var, raising=False)


def _iso(dt: datetime) -> str:
    return dt.isoformat()


@pytest.mark.asyncio
async def test_sweep_replays_unhandled_comment_and_skips_own(monkeypatch):
    now = datetime.now(timezone.utc)

    async def fake_list_recent_media(*, platform="instagram", account_id=None, limit=25):
        return [{"id": "media1", "timestamp": _iso(now), "caption": "test post"}]

    async def fake_list_comments(media_id, *, platform="instagram", account_id=None):
        assert media_id == "media1"
        return [
            {"id": "c1", "text": "Anxiety", "from": {"id": "U_david", "username": "davidafterwork"}},
            {
                "id": "ack1",
                "text": "I've sent you the TCM anxiety guide — check your DM! 🌿",
                "from": {"id": account_id, "username": "jackiechan.tcm"},
            },
        ]

    handled = []

    async def fake_handle_comment(comment, pipeline):
        handled.append(comment.comment_id)

    monkeypatch.setattr(meta_client, "list_recent_media", fake_list_recent_media)
    monkeypatch.setattr(meta_client, "list_comments", fake_list_comments)
    monkeypatch.setattr(reconciliation, "handle_comment", fake_handle_comment)

    summary = await reconciliation._sweep_account("17841417304649448", _FakePipeline())

    assert handled == ["c1"]  # ack1 (own comment) never reaches handle_comment
    assert summary["media_checked"] == 1
    assert summary["comments_checked"] == 2
    assert summary["replayed"] == 1


@pytest.mark.asyncio
async def test_sweep_skips_media_older_than_lookback(monkeypatch):
    monkeypatch.setenv("RECONCILE_LOOKBACK_H", "72")
    old_ts = datetime.now(timezone.utc) - timedelta(hours=200)

    async def fake_list_recent_media(*, platform="instagram", account_id=None, limit=25):
        return [{"id": "media_old", "timestamp": _iso(old_ts)}]

    called = []

    async def fake_list_comments(media_id, *, platform="instagram", account_id=None):
        called.append(media_id)
        return []

    monkeypatch.setattr(meta_client, "list_recent_media", fake_list_recent_media)
    monkeypatch.setattr(meta_client, "list_comments", fake_list_comments)

    summary = await reconciliation._sweep_account("17841417304649448", _FakePipeline())

    assert called == []  # never even listed comments for the too-old post
    assert summary["media_checked"] == 0


@pytest.mark.asyncio
async def test_sweep_one_bad_comment_does_not_abort_the_rest(monkeypatch):
    now = datetime.now(timezone.utc)

    async def fake_list_recent_media(*, platform="instagram", account_id=None, limit=25):
        return [{"id": "media1", "timestamp": _iso(now)}]

    async def fake_list_comments(media_id, *, platform="instagram", account_id=None):
        return [
            {"id": "bad", "text": "boom", "from": {"id": "U1", "username": "u1"}},
            {"id": "good", "text": "fine", "from": {"id": "U2", "username": "u2"}},
        ]

    handled = []

    async def fake_handle_comment(comment, pipeline):
        if comment.comment_id == "bad":
            raise RuntimeError("simulated failure")
        handled.append(comment.comment_id)

    monkeypatch.setattr(meta_client, "list_recent_media", fake_list_recent_media)
    monkeypatch.setattr(meta_client, "list_comments", fake_list_comments)
    monkeypatch.setattr(reconciliation, "handle_comment", fake_handle_comment)

    summary = await reconciliation._sweep_account("17841417304649448", _FakePipeline())

    assert handled == ["good"]
    assert summary["replayed"] == 1


@pytest.mark.asyncio
async def test_run_sweep_skips_when_no_active_accounts(monkeypatch):
    monkeypatch.setattr(reconciliation, "_active_ig_accounts", lambda: [])
    called = []

    async def fake_sweep_account(account_id, pipeline):
        called.append(account_id)
        return {}

    monkeypatch.setattr(reconciliation, "_sweep_account", fake_sweep_account)
    await reconciliation.run_reconciliation_sweep(_FakePipeline())
    assert called == []


@pytest.mark.asyncio
async def test_start_loop_noop_when_disabled(monkeypatch):
    monkeypatch.setenv("RECONCILE_ENABLED", "false")
    ran = []

    async def fake_sweep(pipeline):
        ran.append(True)

    monkeypatch.setattr(reconciliation, "run_reconciliation_sweep", fake_sweep)
    # Should return immediately (not hang in the sleep loop) since disabled.
    await reconciliation.start_reconciliation_loop(_FakePipeline())
    assert ran == []


def test_active_ig_accounts_excludes_comments_off(monkeypatch):
    from src.ips import registry as ip_registry
    from dataclasses import replace

    records = ip_registry.all_ips()
    assert records, "expected at least one IP registered for this test to be meaningful"
    ip = records[0]
    channel = ip.channels.get("instagram")
    if channel is None:
        pytest.skip("first registered IP has no instagram channel")

    off_channel = replace(channel, comments="off")
    off_ip = replace(ip, channels={**ip.channels, "instagram": off_channel})

    monkeypatch.setattr(ip_registry, "all_ips", lambda *a, **kw: (off_ip,))
    monkeypatch.setattr(reconciliation.ip_registry, "all_ips", lambda *a, **kw: (off_ip,))

    assert reconciliation._active_ig_accounts() == []


# ------------------------------------------------ RECONCILE_NOT_BEFORE gate
# Server-side self-expiring alternative to "turn it off and hope a human
# remembers to turn it back on" (2026-07-10, post-Postgres-incident: the
# fresh dedup table must not sweep until old comments leave the lookback).

from src.channels.reconciliation import _gated_now, _not_before


def test_gate_absent_means_not_gated(monkeypatch):
    monkeypatch.delenv("RECONCILE_NOT_BEFORE", raising=False)
    assert _not_before() is None
    assert _gated_now() is False


def test_future_date_gates(monkeypatch):
    monkeypatch.setenv("RECONCILE_NOT_BEFORE", "2099-01-01")
    assert _gated_now() is True


def test_past_date_does_not_gate(monkeypatch):
    monkeypatch.setenv("RECONCILE_NOT_BEFORE", "2020-01-01")
    assert _gated_now() is False


def test_date_only_value_is_hkt_midnight(monkeypatch):
    monkeypatch.setenv("RECONCILE_NOT_BEFORE", "2026-07-13")
    nb = _not_before()
    assert nb is not None and nb.utcoffset().total_seconds() == 8 * 3600


def test_unparseable_fails_open(monkeypatch):
    monkeypatch.setenv("RECONCILE_NOT_BEFORE", "next monday")
    assert _not_before() is None
    assert _gated_now() is False  # backstop must never be silently disabled forever
