"""Tests for the Instagram + Facebook (Meta) channel.

Covers the boundary layers that must be bulletproof:
    * ``meta_events.parse_meta_webhook`` — total parser over untrusted input
    * ``meta_webhook.verify_signature``  — X-Hub-Signature-256 validation
    * ``comment_rules``                  — canned keyword → DM resolution
and the dispatch glue (DM text+image interleave, canned vs agent comment)
with a fake pipeline + a monkeypatched ``meta_client``.
"""

from __future__ import annotations

import hashlib
import hmac
import json
from dataclasses import dataclass, field
from datetime import datetime

import pytest

from src.channels import comment_rules, meta_client, meta_webhook
from src.channels.meta_events import (
    IncomingComment,
    IncomingDM,
    parse_meta_webhook,
)
from src.crm.models import ConversationMessage, User

# ---------------------------------------------------------------------------
# Payload builders
# ---------------------------------------------------------------------------


def _dm_payload(text="我成日口氣好重", *, is_echo=False, mid="m1", obj="instagram") -> dict:
    return {
        "object": obj,
        "entry": [{
            "id": "BIZ",
            "messaging": [{
                "sender": {"id": "IGSID123"},
                "recipient": {"id": "BIZ"},
                "timestamp": 1700000000000,
                "message": {"mid": mid, "text": text, "is_echo": is_echo},
            }],
        }],
    }


def _comment_payload(text="gut", *, cid="c1") -> dict:
    return {
        "object": "instagram",
        "entry": [{
            "id": "BIZ",
            "changes": [{
                "field": "comments",
                "value": {
                    "id": cid, "text": text,
                    "from": {"id": "U9", "username": "amy"},
                    "media": {"id": "media42"},
                },
            }],
        }],
    }


# ---------------------------------------------------------------------------
# Parser
# ---------------------------------------------------------------------------


@pytest.mark.unit
def test_parse_dm():
    dm = parse_meta_webhook(_dm_payload())[0]
    assert isinstance(dm, IncomingDM)
    assert dm.crm_key == "ig_IGSID123"
    assert dm.text == "我成日口氣好重"
    assert dm.is_echo is False


@pytest.mark.unit
def test_parse_echo_flagged():
    assert parse_meta_webhook(_dm_payload(is_echo=True))[0].is_echo is True


@pytest.mark.unit
def test_parse_comment():
    ev = parse_meta_webhook(_comment_payload())[0]
    assert isinstance(ev, IncomingComment)
    assert ev.crm_key == "ig_U9"
    assert ev.media_id == "media42"


@pytest.mark.unit
def test_parse_facebook_page_object():
    payload = {
        "object": "page",
        "entry": [{
            "id": "PAGE",
            "messaging": [{
                "sender": {"id": "PSID1"},
                "recipient": {"id": "PAGE"},
                "message": {"mid": "fm1", "text": "hi"},
            }],
        }],
    }
    dm = parse_meta_webhook(payload)[0]
    assert dm.platform == "facebook"
    assert dm.crm_key == "fb_PSID1"


@pytest.mark.unit
@pytest.mark.parametrize("bad", [None, "str", 123, {}, {"object": "x", "entry": []}, {"object": "instagram"}])
def test_parse_garbage_returns_empty(bad):
    assert parse_meta_webhook(bad) == []


@pytest.mark.unit
def test_parse_skips_message_without_mid():
    payload = _dm_payload()
    del payload["entry"][0]["messaging"][0]["message"]["mid"]
    assert parse_meta_webhook(payload) == []


@pytest.mark.unit
def test_parse_comment_missing_from_kept_with_warning(caplog):
    """Meta intermittently omits the ``from`` object on comment webhooks
    (observed on Reels — the 2026-07-06/07 anxiety-post incident). Previously
    this ``continue``'d silently and the WHOLE event vanished with zero log
    output anywhere. Now: keep the event (comment_id is enough to act on,
    from_id="" signals the dispatch layer to attempt a Graph API backfill)
    and log loudly so the drop is diagnosable without Graph API archaeology.
    """
    payload = _comment_payload(cid="c99")
    del payload["entry"][0]["changes"][0]["value"]["from"]

    with caplog.at_level("WARNING", logger="channels.meta_events"):
        events = parse_meta_webhook(payload)

    assert len(events) == 1
    ev = events[0]
    assert isinstance(ev, IncomingComment)
    assert ev.comment_id == "c99"
    assert ev.from_id == ""
    assert any("missing 'from' object" in r.message for r in caplog.records)


@pytest.mark.unit
def test_parse_comment_missing_comment_id_dropped():
    """Unlike a missing ``from``, a missing comment_id is truly unusable —
    we can't dedup or reply-target without it — so this one stays dropped."""
    payload = _comment_payload()
    del payload["entry"][0]["changes"][0]["value"]["id"]
    assert parse_meta_webhook(payload) == []


# ---------------------------------------------------------------------------
# Signature verification
# ---------------------------------------------------------------------------


@pytest.mark.unit
def test_signature_dev_no_secret_passes(monkeypatch):
    monkeypatch.setattr(meta_webhook, "APP_ENV", "development")
    monkeypatch.setenv("META_APP_SECRET", "")
    assert meta_webhook.verify_signature(b"{}", "") is True


@pytest.mark.unit
def test_signature_prod_no_secret_fails(monkeypatch):
    monkeypatch.setattr(meta_webhook, "APP_ENV", "production")
    monkeypatch.setenv("META_APP_SECRET", "")
    assert meta_webhook.verify_signature(b"{}", "") is False


@pytest.mark.unit
def test_signature_correct_and_wrong(monkeypatch):
    monkeypatch.setenv("META_APP_SECRET", "shh")
    raw = b'{"a":1}'
    good = "sha256=" + hmac.new(b"shh", raw, hashlib.sha256).hexdigest()
    assert meta_webhook.verify_signature(raw, good) is True
    assert meta_webhook.verify_signature(raw, "sha256=deadbeef") is False
    assert meta_webhook.verify_signature(raw, "") is False


# ---------------------------------------------------------------------------
# Dedup + handshake
# ---------------------------------------------------------------------------


@pytest.mark.unit
def test_dedup(monkeypatch):
    monkeypatch.setattr(meta_webhook, "_seen_ids", type(meta_webhook._seen_ids)())
    assert meta_webhook.is_duplicate("a") is False
    assert meta_webhook.is_duplicate("a") is True
    assert meta_webhook.is_duplicate("") is False


@pytest.mark.unit
def test_verify_subscription(monkeypatch):
    monkeypatch.setenv("META_VERIFY_TOKEN", "tok")
    assert meta_webhook.verify_subscription("subscribe", "tok", "1234") == "1234"
    assert meta_webhook.verify_subscription("subscribe", "wrong", "1234") is None
    assert meta_webhook.verify_subscription("delete", "tok", "1234") is None


# ---------------------------------------------------------------------------
# comment_rules
# ---------------------------------------------------------------------------


@pytest.mark.unit
def test_comment_rules_match(tmp_path, monkeypatch):
    cfg = tmp_path / "rules.json"
    cfg.write_text(json.dumps({
        "gut": {
            "dm_text": "gut guide",
            "image_url": "https://x/y.png",
            "public_ack": "sent",
            "accounts": ["jackie"],
        },
        "濕熱": {"dm_text": "濕熱調理", "use_agent": True, "accounts": ["chloe"]},
    }), encoding="utf-8")
    monkeypatch.setenv("COMMENT_RESPONSES_PATH", str(cfg))
    comment_rules._load_raw.cache_clear()

    r = comment_rules.match("please send me GUT info", account_id="jackie")
    assert r is not None and r.keyword == "gut" and r.dm_text == "gut guide"
    assert r.use_agent is False

    assert comment_rules.match("please send me GUT info", account_id="chloe") is None

    r2 = comment_rules.match("我想知濕熱", account_id="chloe")
    assert r2 is not None and r2.use_agent is True

    assert comment_rules.match("我想知濕熱", account_id="jackie") is None
    assert comment_rules.match("random words", account_id="jackie") is None


@pytest.mark.unit
def test_comment_rules_missing_file(monkeypatch):
    monkeypatch.setenv("COMMENT_RESPONSES_PATH", "/no/such/file.json")
    comment_rules._load_raw.cache_clear()
    assert comment_rules.load_rules() == ()
    assert comment_rules.match("gut") is None


# ---------------------------------------------------------------------------
# Dispatch — fakes
# ---------------------------------------------------------------------------


@dataclass
class _FakeWriterOutput:
    bubbles: list[str] = field(default_factory=list)
    media_to_send: list[dict] = field(default_factory=list)


@dataclass
class _FakeResult:
    writer_output: _FakeWriterOutput


class _FakePipeline:
    def __init__(self, bubbles, media=None):
        self._out = _FakeWriterOutput(list(bubbles), list(media or []))
        self.calls = []

    async def run_turn(self, *, phone, user_message, wa_message_id=None, **_):
        self.calls.append({"phone": phone, "msg": user_message})
        return _FakeResult(self._out)


@pytest.mark.asyncio
async def test_handle_dm_interleaves_text_and_image(monkeypatch):
    sent = []

    async def fake_send_dm(rid, text, *, platform="instagram", **_):
        sent.append(("text", rid, text, platform)); return meta_client.SendResult(True)

    async def fake_send_dm_image(rid, url, *, platform="instagram", **_):
        sent.append(("image", rid, url, platform)); return meta_client.SendResult(True)

    monkeypatch.setattr(meta_client, "send_dm", fake_send_dm)
    monkeypatch.setattr(meta_client, "send_dm_image", fake_send_dm_image)
    monkeypatch.setattr(meta_webhook, "_BUBBLE_PAUSE_S", 0.0)
    monkeypatch.setattr(meta_webhook, "_MEDIA_PAUSE_S", 0.0)

    dm = IncomingDM(platform="instagram", sender_id="IGSID123", recipient_id="BIZ",
                    text="有咩湯水", message_id="m1", timestamp=0)
    pipe = _FakePipeline(
        ["第一款湯水", "第二款"],
        media=[{"url": "https://x/soup.png", "after_bubble_idx": 0}],
    )
    await meta_webhook._dispatch_dm(dm, pipe)

    assert pipe.calls[0]["phone"] == "ig_IGSID123"
    # text(0) → image(after 0) → text(1)
    assert [s[0] for s in sent] == ["text", "image", "text"]
    assert sent[1] == ("image", "IGSID123", "https://x/soup.png", "instagram")


@pytest.mark.asyncio
async def test_handle_comment_canned_no_agent(monkeypatch, tmp_path):
    cfg = tmp_path / "rules.json"
    cfg.write_text(json.dumps({
        "gut": {"dm_text": "腸胃懶人包送俾你", "image_url": "https://x/g.png", "public_ack": "send咗喇"},
    }), encoding="utf-8")
    monkeypatch.setenv("COMMENT_RESPONSES_PATH", str(cfg))
    comment_rules._load_raw.cache_clear()
    monkeypatch.setattr(meta_webhook, "_MEDIA_PAUSE_S", 0.0)

    private, public, images = [], [], []

    async def fake_priv(cid, text, *, platform="instagram", **_):
        private.append((cid, text)); return meta_client.SendResult(True)

    async def fake_pub(cid, text, *, platform="instagram", **_):
        public.append((cid, text)); return meta_client.SendResult(True)

    async def fake_img(rid, url, *, platform="instagram", **_):
        images.append((rid, url)); return meta_client.SendResult(True)

    monkeypatch.setattr(meta_client, "send_private_reply", fake_priv)
    monkeypatch.setattr(meta_client, "reply_to_comment", fake_pub)
    monkeypatch.setattr(meta_client, "send_dm_image", fake_img)

    comment = IncomingComment(platform="instagram", comment_id="c1", text="gut pls",
                              from_id="U9", from_username="amy", media_id="m42")
    pipe = _FakePipeline(["AGENT SHOULD NOT RUN"])
    await meta_webhook.handle_comment(comment, pipe)

    assert pipe.calls == []                       # agent never ran
    assert private == [("c1", "腸胃懶人包送俾你")]   # canned DM sent
    assert public == [("c1", "send咗喇")]          # public ack sent
    assert images == []                             # images wait for DM reply


class _FakeCRM:
    def __init__(self):
        self.claimed = set()
        self.messages = []
        self.users = {}

    async def try_claim_webhook_event(self, event_id, kind):
        if event_id in self.claimed:
            return False
        self.claimed.add(event_id)
        return True

    async def release_webhook_event(self, event_id):
        self.claimed.discard(event_id)

    async def get_user(self, phone):
        return self.users.get(phone)

    async def get_or_create_user(self, phone):
        if phone not in self.users:
            self.users[phone] = User(phone=phone)
        return self.users[phone]

    async def save_user(self, user):
        self.users[user.phone] = user

    async def append_message(self, phone, msg):
        self.messages.append((phone, msg))


@pytest.mark.asyncio
async def test_handle_comment_persistent_dedup_blocks_repeat(monkeypatch, tmp_path):
    cfg = tmp_path / "rules.json"
    cfg.write_text(json.dumps({
        "gut": {
            "dm_text": "腸胃懶人包送俾你",
            "image_url": "https://x/g.png",
            "public_ack": "send咗喇",
        },
    }), encoding="utf-8")
    monkeypatch.setenv("COMMENT_RESPONSES_PATH", str(cfg))
    comment_rules._load_raw.cache_clear()
    monkeypatch.setattr(meta_webhook, "_MEDIA_PAUSE_S", 0.0)

    private, public, images = [], [], []

    async def fake_priv(cid, text, *, platform="instagram", **_):
        private.append((cid, text)); return meta_client.SendResult(True)

    async def fake_pub(cid, text, *, platform="instagram", **_):
        public.append((cid, text)); return meta_client.SendResult(True)

    async def fake_img(rid, url, *, platform="instagram", **_):
        images.append((rid, url)); return meta_client.SendResult(True)

    monkeypatch.setattr(meta_client, "send_private_reply", fake_priv)
    monkeypatch.setattr(meta_client, "reply_to_comment", fake_pub)
    monkeypatch.setattr(meta_client, "send_dm_image", fake_img)

    comment = IncomingComment(platform="instagram", comment_id="c1", text="gut pls",
                              from_id="U9", from_username="amy", media_id="m42")
    pipe = _FakePipeline(["AGENT SHOULD NOT RUN"])
    crm = _FakeCRM()
    pipe._crm = crm

    await meta_webhook.handle_comment(comment, pipe)
    await meta_webhook.handle_comment(comment, pipe)

    assert private == [("c1", "腸胃懶人包送俾你")]
    assert public == [("c1", "send咗喇")]
    assert images == []
    assert crm.users["ig_U9"].temp_state["meta_pending_guide_images"] == ["https://x/g.png"]
    assert [m[0] for m in crm.messages] == ["ig_U9", "ig_U9"]
    assert crm.messages[0][1].role == "user"
    assert crm.messages[0][1].content == "gut pls"
    assert crm.messages[1][1].role == "chloe"
    assert crm.messages[1][1].media_urls == ["https://x/g.png"]


@pytest.mark.asyncio
async def test_handle_comment_failed_send_releases_claims_for_retry(monkeypatch, tmp_path):
    """Root-caused 2026-07-21 (live incident): a real 'guasha' comment matched
    its rule, claimed both idempotency keys, then the private-reply send
    failed — with the claims never released, the customer's actual comment
    (and every retry) was silently dropped as 'duplicate', with NO DM ever
    sent and no way to recover short of a manual fix. This test locks in the
    fix: a failed send must release its claims so the SAME comment posted
    again (or a redelivered webhook) gets a genuine retry, while a comment
    that eventually succeeds must stay permanently claimed (see the sibling
    dedup test above) so a real duplicate send never happens."""
    cfg = tmp_path / "rules.json"
    cfg.write_text(json.dumps({
        "guasha": {
            "dm_text": "here's the map",
            "public_ack": "sent!",
        },
    }), encoding="utf-8")
    monkeypatch.setenv("COMMENT_RESPONSES_PATH", str(cfg))
    comment_rules._load_raw.cache_clear()
    monkeypatch.setattr(meta_webhook, "_MEDIA_PAUSE_S", 0.0)

    private_attempts, public_sent = [], []

    # First attempt fails (simulates the real incident's transient Graph API
    # failure); second attempt (the retry) succeeds.
    async def flaky_priv(cid, text, *, platform="instagram", **_):
        private_attempts.append((cid, text))
        if len(private_attempts) == 1:
            return meta_client.SendResult(False, "transient error")
        return meta_client.SendResult(True)

    async def fake_pub(cid, text, *, platform="instagram", **_):
        public_sent.append((cid, text)); return meta_client.SendResult(True)

    monkeypatch.setattr(meta_client, "send_private_reply", flaky_priv)
    monkeypatch.setattr(meta_client, "reply_to_comment", fake_pub)

    comment = IncomingComment(platform="instagram", comment_id="c-guasha", text="guasha",
                              from_id="U-shivonne", from_username="shivonne_ksw", media_id="m-reel")
    pipe = _FakePipeline(["AGENT SHOULD NOT RUN"])
    crm = _FakeCRM()
    pipe._crm = crm

    # First call: send fails — must NOT leave a permanent claim behind.
    await meta_webhook.handle_comment(comment, pipe)
    assert len(private_attempts) == 1
    assert public_sent == []  # public ack only fires after a successful private send

    # Retry with the SAME comment_id/text (mirrors a webhook redelivery, or
    # the same person commenting "guasha" again after seeing nothing happen).
    await meta_webhook.handle_comment(comment, pipe)

    assert len(private_attempts) == 2          # retry actually re-attempted the send
    assert public_sent == [("c-guasha", "sent!")]  # succeeded on retry


@pytest.mark.asyncio
async def test_handle_comment_unhandled_exception_still_releases_claims(monkeypatch, tmp_path):
    """Code-review finding on the fix above: _comment_via_canned/_comment_via_agent
    returning a clean `sent=False` isn't the only failure mode — an actual
    UNHANDLED exception (a bug, an unexpected error type not caught
    internally by meta_client) must ALSO release the claims, or it silently
    reproduces the exact live incident through a different path (the
    exception skips the `if not sent:` block entirely, leaving both claims
    stuck forever). Forces send_private_reply to raise directly (not just
    return a failed SendResult) to prove handle_comment's dispatch is
    exception-safe end to end."""
    cfg = tmp_path / "rules.json"
    cfg.write_text(json.dumps({
        "ask": {"dm_text": "", "use_agent": True},
    }), encoding="utf-8")
    monkeypatch.setenv("COMMENT_RESPONSES_PATH", str(cfg))
    comment_rules._load_raw.cache_clear()

    attempts = []

    async def raising_priv(cid, text, *, platform="instagram", **_):
        attempts.append((cid, text))
        if len(attempts) == 1:
            raise RuntimeError("simulated unexpected bug")
        return meta_client.SendResult(True)

    monkeypatch.setattr(meta_client, "send_private_reply", raising_priv)

    comment = IncomingComment(platform="instagram", comment_id="c-exc", text="ask me anything",
                              from_id="U-exc", from_username="amy", media_id="m42")
    pipe = _FakePipeline(["你好", "想問咩"])
    crm = _FakeCRM()
    pipe._crm = crm

    await meta_webhook.handle_comment(comment, pipe)  # raises internally, must not propagate
    assert len(attempts) == 1

    await meta_webhook.handle_comment(comment, pipe)  # retry must actually re-attempt
    assert len(attempts) == 2


@pytest.mark.asyncio
async def test_dm_reply_sends_pending_comment_guide_images(monkeypatch):
    monkeypatch.setattr(meta_webhook, "_MEDIA_PAUSE_S", 0.0)
    images, sent_texts = [], []

    async def fake_img(rid, url, *, platform="instagram", **_):
        images.append((rid, url)); return meta_client.SendResult(True)

    async def fake_send_dm(rid, text, *, platform="instagram", **_):
        sent_texts.append((rid, text)); return meta_client.SendResult(True)

    monkeypatch.setattr(meta_client, "send_dm_image", fake_img)
    monkeypatch.setattr(meta_client, "send_dm", fake_send_dm)

    crm = _FakeCRM()
    await crm.save_user(User(phone="ig_U9", temp_state={
        "meta_pending_guide_images": ["https://x/g1.png", "https://x/g2.png"],
    }))
    pipe = _FakePipeline(["AGENT SHOULD NOT RUN"])
    pipe._crm = crm

    dm = IncomingDM(platform="instagram", sender_id="U9", recipient_id="BIZ",
                    text="yes please", message_id="m2", timestamp=0)
    await meta_webhook._dispatch_dm(dm, pipe)

    assert images == [("U9", "https://x/g1.png"), ("U9", "https://x/g2.png")]
    assert pipe.calls and pipe.calls[0]["msg"] == "yes please"
    assert sent_texts == [("U9", "AGENT SHOULD NOT RUN")]
    assert "meta_pending_guide_images" not in crm.users["ig_U9"].temp_state


@pytest.mark.asyncio
async def test_dm_keyword_existing_conversation_routes_to_agent(monkeypatch, tmp_path):
    cfg = tmp_path / "rules.json"
    cfg.write_text(json.dumps({
        "gut": {"dm_text": "懶人包俾你", "image_url": "https://x/g.png"},
    }), encoding="utf-8")
    monkeypatch.setenv("COMMENT_RESPONSES_PATH", str(cfg))
    comment_rules._load_raw.cache_clear()

    sent_texts, images = [], []

    async def fake_send_dm(rid, text, *, platform="instagram", **_):
        sent_texts.append((rid, text)); return meta_client.SendResult(True)

    async def fake_img(rid, url, *, platform="instagram", **_):
        images.append((rid, url)); return meta_client.SendResult(True)

    monkeypatch.setattr(meta_client, "send_dm", fake_send_dm)
    monkeypatch.setattr(meta_client, "send_dm_image", fake_img)

    crm = _FakeCRM()
    user = User(
        phone="ig_U9",
        conversation_history=[
            ConversationMessage(role="user", content="earlier", at=datetime.utcnow())
        ],
    )
    await crm.save_user(user)
    pipe = _FakePipeline(["let's continue about your detox symptoms"])
    pipe._crm = crm

    dm = IncomingDM(platform="instagram", sender_id="U9", recipient_id="BIZ",
                    text="detox again", message_id="m3", timestamp=0)
    await meta_webhook._dispatch_dm(dm, pipe)

    assert pipe.calls and pipe.calls[0]["msg"] == "detox again"
    assert sent_texts == [("U9", "let's continue about your detox symptoms")]
    assert images == []


@pytest.mark.asyncio
async def test_handle_comment_use_agent_runs_pipeline(monkeypatch, tmp_path):
    cfg = tmp_path / "rules.json"
    cfg.write_text(json.dumps({
        "ask": {"dm_text": "", "use_agent": True},
    }), encoding="utf-8")
    monkeypatch.setenv("COMMENT_RESPONSES_PATH", str(cfg))
    comment_rules._load_raw.cache_clear()

    private = []

    async def fake_priv(cid, text, *, platform="instagram", **_):
        private.append((cid, text)); return meta_client.SendResult(True)

    monkeypatch.setattr(meta_client, "send_private_reply", fake_priv)

    comment = IncomingComment(platform="instagram", comment_id="c2", text="ask me anything",
                              from_id="U9", from_username="amy", media_id="m42")
    pipe = _FakePipeline(["你好", "想問咩"])
    await meta_webhook.handle_comment(comment, pipe)

    assert pipe.calls and pipe.calls[0]["phone"] == "ig_U9"
    assert private == [("c2", "你好\n\n想問咩")]


@pytest.mark.asyncio
async def test_handle_comment_no_rule_skips(monkeypatch, tmp_path):
    cfg = tmp_path / "rules.json"
    cfg.write_text(json.dumps({"gut": {"dm_text": "x"}}), encoding="utf-8")
    monkeypatch.setenv("COMMENT_RESPONSES_PATH", str(cfg))
    comment_rules._load_raw.cache_clear()
    # Unmatched-comment reply path defaults OFF — no-op regardless of env leakage.
    monkeypatch.delenv("UNMATCHED_COMMENT_REPLY_ENABLED", raising=False)

    called = []

    async def fake_priv(cid, text, *, platform="instagram", **_):
        called.append(cid); return meta_client.SendResult(True)

    monkeypatch.setattr(meta_client, "send_private_reply", fake_priv)
    comment = IncomingComment(platform="instagram", comment_id="c3", text="thanks doctor",
                              from_id="U9", from_username="amy", media_id="m42")
    await meta_webhook.handle_comment(comment, _FakePipeline(["no"]))
    assert called == []


@pytest.mark.asyncio
async def test_handle_comment_keyword_matched_path_unchanged_by_unmatched_wiring(
    monkeypatch, tmp_path
):
    """Regression guard: the new unmatched-comment branch must never leak into
    the existing keyword-matched (canned/use_agent) path — same calls, same
    order, even with the new module wired in and enabled."""
    from src.channels import unmatched_comment

    monkeypatch.setenv("UNMATCHED_COMMENT_REPLY_ENABLED", "1")  # prove it still never fires

    unmatched_calls = []

    async def fake_handle_unmatched(comment, pipeline):
        unmatched_calls.append(comment.comment_id)

    # meta_webhook.py imports the `unmatched_comment` MODULE (not the
    # function directly), so patching the attribute on the module object
    # once is sufficient — meta_webhook.unmatched_comment IS this same
    # module object, not a separate reference.
    monkeypatch.setattr(
        unmatched_comment, "handle_unmatched_comment", fake_handle_unmatched
    )

    cfg = tmp_path / "rules.json"
    cfg.write_text(json.dumps({
        "gut": {"dm_text": "腸胃懶人包送俾你", "image_url": "https://x/g.png", "public_ack": "send咗喇"},
    }), encoding="utf-8")
    monkeypatch.setenv("COMMENT_RESPONSES_PATH", str(cfg))
    comment_rules._load_raw.cache_clear()
    monkeypatch.setattr(meta_webhook, "_MEDIA_PAUSE_S", 0.0)

    private, public = [], []

    async def fake_priv(cid, text, *, platform="instagram", **_):
        private.append((cid, text)); return meta_client.SendResult(True)

    async def fake_pub(cid, text, *, platform="instagram", **_):
        public.append((cid, text)); return meta_client.SendResult(True)

    monkeypatch.setattr(meta_client, "send_private_reply", fake_priv)
    monkeypatch.setattr(meta_client, "reply_to_comment", fake_pub)

    comment = IncomingComment(platform="instagram", comment_id="c_kw", text="gut pls",
                              from_id="U9", from_username="amy", media_id="m42")
    pipe = _FakePipeline(["AGENT SHOULD NOT RUN"])
    await meta_webhook.handle_comment(comment, pipe)

    assert pipe.calls == []
    assert private == [("c_kw", "腸胃懶人包送俾你")]
    assert public == [("c_kw", "send咗喇")]
    assert unmatched_calls == []  # the new path never runs for a keyword match


@pytest.mark.asyncio
async def test_process_post_disabled_short_circuits():
    body, status = await meta_webhook.process_post(
        raw=b"{}", signature_header="", pipeline=None, enabled=False,
    )
    assert status == 200 and body["status"] == "disabled"


@pytest.mark.unit
def test_process_post_disabled_logs_warning(caplog):
    """The disabled/ignored branches used to return 200 with ZERO log
    output — indistinguishable from a genuinely-empty webhook ping. That
    silence is what made the 2026-07-06/07 anxiety-comment drop take a full
    Graph API investigation to diagnose instead of a log grep."""
    import asyncio

    with caplog.at_level("WARNING", logger="channels.meta_webhook"):
        asyncio.run(meta_webhook.process_post(
            raw=b"{}", signature_header="", pipeline=None, enabled=False,
        ))
    assert any("webhook disabled" in r.message for r in caplog.records)


@pytest.mark.asyncio
async def test_process_post_disabled_fires_ops_alert(monkeypatch):
    """Logging the outage isn't enough on its own (see the module-level test
    above) — this locks in that a human actually gets pinged, debounced per
    platform so Meta's redelivery bursts don't flood the channel."""
    alerts = []

    async def fake_alert(key, text):
        alerts.append((key, text))

    monkeypatch.setattr(meta_webhook, "send_ops_alert", fake_alert)

    body, status = await meta_webhook.process_post(
        raw=b"{}", signature_header="", pipeline=None, enabled=False,
        platform="instagram",
    )
    for task in list(meta_webhook._bg_tasks):
        await task

    assert status == 200 and body["status"] == "disabled"
    assert len(alerts) == 1
    key, text = alerts[0]
    assert key == "webhook_disabled_instagram"
    assert "instagram" in text and "IG_ENABLED" in text


@pytest.mark.asyncio
async def test_process_post_no_events_logs_info(caplog, monkeypatch):
    # Dev-mode signature bypass requires an empty secret — isolate explicitly
    # (matches the convention above) rather than relying on ambient env,
    # since importing scripts.backfill_comments elsewhere in the suite loads
    # the real .env (including a real META_APP_SECRET) at collection time.
    monkeypatch.setenv("META_APP_SECRET", "")
    with caplog.at_level("INFO", logger="channels.meta_webhook"):
        body, status = await meta_webhook.process_post(
            raw=b'{"object": "instagram", "entry": []}',
            signature_header="", pipeline=None, enabled=True,
        )
    assert status == 200 and body["status"] == "ignored"
    assert any("zero actionable events" in r.message for r in caplog.records)


# ---------------------------------------------------------------------------
# Comment 'from' backfill (Meta intermittently omits it — see meta_events)
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_process_post_backfills_missing_from_then_dispatches(monkeypatch, tmp_path):
    """End-to-end: webhook payload arrives with NO 'from' object (the exact
    2026-07-06/07 shape). process_post should recover it via one Graph API
    call and still dispatch to handle_comment — not silently drop it."""
    monkeypatch.setenv("META_APP_SECRET", "")
    cfg = tmp_path / "rules.json"
    cfg.write_text(json.dumps({
        "anxiety": {"dm_text": "anxiety guide", "public_ack": "sent!"},
    }), encoding="utf-8")
    monkeypatch.setenv("COMMENT_RESPONSES_PATH", str(cfg))
    comment_rules._load_raw.cache_clear()
    monkeypatch.setattr(meta_webhook, "_MEDIA_PAUSE_S", 0.0)
    monkeypatch.setattr(meta_webhook, "_seen_ids", type(meta_webhook._seen_ids)())

    async def fake_get_comment_from(comment_id, *, platform="instagram", account_id=None):
        assert comment_id == "c_missing_from"
        return "U_rajesh", "rajeshnaidu"

    private, public = [], []

    async def fake_priv(cid, text, *, platform="instagram", **_):
        private.append((cid, text)); return meta_client.SendResult(True)

    async def fake_pub(cid, text, *, platform="instagram", **_):
        public.append((cid, text)); return meta_client.SendResult(True)

    monkeypatch.setattr(meta_client, "get_comment_from", fake_get_comment_from)
    monkeypatch.setattr(meta_client, "send_private_reply", fake_priv)
    monkeypatch.setattr(meta_client, "reply_to_comment", fake_pub)

    payload = {
        "object": "instagram",
        "entry": [{
            "id": "17841417304649448",
            "changes": [{
                "field": "comments",
                "value": {"id": "c_missing_from", "text": "Anxiety",
                          "media": {"id": "media42"}},
            }],
        }],
    }

    class _FakePipeline:
        _crm = None

    body, status = await meta_webhook.process_post(
        raw=json.dumps(payload).encode(), signature_header="",
        pipeline=_FakePipeline(), enabled=True,
    )
    assert status == 200 and body["count"] == 1
    for task in list(meta_webhook._bg_tasks):
        await task

    assert private == [("c_missing_from", "anxiety guide")]
    assert public == [("c_missing_from", "sent!")]


@pytest.mark.asyncio
async def test_process_post_drops_when_backfill_also_fails(monkeypatch, caplog):
    monkeypatch.setenv("META_APP_SECRET", "")

    async def fake_get_comment_from(comment_id, *, platform="instagram", account_id=None):
        return "", ""  # Graph API also couldn't recover it

    alerts = []

    async def fake_alert(key, text):
        alerts.append((key, text))

    monkeypatch.setattr(meta_client, "get_comment_from", fake_get_comment_from)
    monkeypatch.setattr(meta_webhook, "send_ops_alert", fake_alert)
    monkeypatch.setattr(meta_webhook, "_seen_ids", type(meta_webhook._seen_ids)())

    payload = {
        "object": "instagram",
        "entry": [{
            "id": "17841417304649448",
            "changes": [{
                "field": "comments",
                "value": {"id": "c_still_missing", "text": "Anxiety",
                          "media": {"id": "media42"}},
            }],
        }],
    }

    class _FakePipeline:
        _crm = None

    with caplog.at_level("WARNING", logger="channels.meta_webhook"):
        body, status = await meta_webhook.process_post(
            raw=json.dumps(payload).encode(), signature_header="",
            pipeline=_FakePipeline(), enabled=True,
        )
        # The backfill attempt (and its failure) now happens inside the
        # spawned background task — process_post itself never awaits the
        # Graph API call, so it still reports the event as "queued" (a
        # task was scheduled) even though that task goes on to drop it.
        # This is the fix for the reviewer's HIGH finding: a slow/timed-out
        # Graph API backfill must never delay Meta's 200 OK.
        assert status == 200 and body["count"] == 1
        for task in list(meta_webhook._bg_tasks):
            await task
    assert any("still no 'from_id'" in r.message for r in caplog.records)
    assert len(alerts) == 1
    key, text = alerts[0]
    assert key == "comment_dropped_c_still_missing"
    assert "c_still_missing" in text and "media42" in text


@pytest.mark.unit
def test_is_own_comment_matches_business_account_ids(monkeypatch):
    monkeypatch.setenv("IG_USER_ID_JACKIE", "17841417304649448")
    own = IncomingComment(
        platform="instagram", comment_id="ack1", text="I've sent you the guide!",
        from_id="17841417304649448", from_username="jackiechan.tcm",
        media_id="media42", recipient_id="17841417304649448",
    )
    stranger = IncomingComment(
        platform="instagram", comment_id="c1", text="Anxiety",
        from_id="1329310679416362", from_username="davidafterwork",
        media_id="media42", recipient_id="17841417304649448",
    )
    assert meta_webhook.is_own_comment(own) is True
    assert meta_webhook.is_own_comment(stranger) is False
