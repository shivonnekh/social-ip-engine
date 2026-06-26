"""Tests for the social-DM merge buffer + its integration in meta_webhook."""

from __future__ import annotations

import asyncio

import pytest

from src.channels import meta_client, meta_webhook
from src.channels.merge_buffer import MergeBuffer
from src.channels.meta_events import IncomingDM


def _dm(text, *, sender="U1", mid="m"):
    return IncomingDM(platform="instagram", sender_id=sender, recipient_id="B",
                      text=text, message_id=mid, timestamp=0)


@pytest.mark.asyncio
async def test_merges_rapid_fragments():
    flushed = []

    async def on_flush(dm): flushed.append(dm.text)

    buf = MergeBuffer(window_s=0.15, max_s=2.0, on_flush=on_flush)
    await buf.submit(_dm("我", mid="m1"))
    await asyncio.sleep(0.05)
    await buf.submit(_dm("成日攰", mid="m2"))
    await asyncio.sleep(0.05)
    await buf.submit(_dm("瞓得唔好", mid="m3"))

    await asyncio.sleep(0.4)  # let the quiet window elapse + flush
    assert flushed == ["我\n成日攰\n瞓得唔好"]


@pytest.mark.asyncio
async def test_separate_users_dont_merge():
    flushed = []

    async def on_flush(dm): flushed.append((dm.sender_id, dm.text))

    buf = MergeBuffer(window_s=0.15, max_s=2.0, on_flush=on_flush)
    await buf.submit(_dm("hi", sender="A", mid="a1"))
    await buf.submit(_dm("hello", sender="B", mid="b1"))
    await asyncio.sleep(0.4)
    assert ("A", "hi") in flushed and ("B", "hello") in flushed


@pytest.mark.asyncio
async def test_force_flush_on_nonstop_typer():
    flushed = []

    async def on_flush(dm): flushed.append(dm.text)

    # window never settles (we keep typing), but max_s forces a flush
    buf = MergeBuffer(window_s=0.2, max_s=0.5, on_flush=on_flush)
    await buf.submit(_dm("a", mid="1"))
    for i in range(8):
        await asyncio.sleep(0.1)
        await buf.submit(_dm(str(i), mid=f"m{i}"))
    await asyncio.sleep(0.4)
    assert flushed, "max_s should have forced a flush"
    assert flushed[0].startswith("a")


@pytest.mark.asyncio
async def test_window_zero_dispatches_immediately():
    flushed = []

    async def on_flush(dm): flushed.append(dm.text)

    buf = MergeBuffer(window_s=0.0, max_s=0.0, on_flush=on_flush)
    await buf.submit(_dm("immediate"))
    assert flushed == ["immediate"]  # no waiting


@pytest.mark.asyncio
async def test_handle_dm_routes_through_buffer(monkeypatch):
    """meta_webhook.handle_dm buffers, then _dispatch_dm sends the merged turn."""
    monkeypatch.setenv("CHLOE_MERGE_WINDOW_S", "0.15")
    monkeypatch.setenv("CHLOE_MERGE_MAX_S", "2.0")
    meta_webhook.reset_merge_buffer()

    sent = []

    async def fake_send_dm(rid, text, *, platform="instagram", **_):
        sent.append(text); return meta_client.SendResult(True)

    monkeypatch.setattr(meta_client, "send_dm", fake_send_dm)
    monkeypatch.setattr(meta_webhook, "_BUBBLE_PAUSE_S", 0.0)
    # no keyword rule match
    monkeypatch.setenv("COMMENT_RESPONSES_PATH", "/no/file.json")
    from src.channels import comment_rules
    comment_rules._load_raw.cache_clear()

    captured = {}

    class _Chloe:
        async def respond(self, *, crm_key, user_message, message_id=None):
            from src.channels.chloe_agent import ChloeReply
            captured["msg"] = user_message
            return ChloeReply(bubbles=["收到～"])

    monkeypatch.setattr(meta_webhook, "_chloe_agent", _Chloe())

    await meta_webhook.handle_dm(_dm("我", mid="m1"), pipeline=None)  # type: ignore[arg-type]
    await asyncio.sleep(0.03)
    await meta_webhook.handle_dm(_dm("成日攰", mid="m2"), pipeline=None)  # type: ignore[arg-type]
    await asyncio.sleep(0.5)

    # Chloe saw the MERGED text, and replied once.
    assert captured["msg"] == "我\n成日攰"
    assert sent == ["收到～"]
    meta_webhook.reset_merge_buffer()
