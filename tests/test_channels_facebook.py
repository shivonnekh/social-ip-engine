"""Facebook (Messenger + Page feed) channel — end-to-end parity with Instagram.

Phase 4 activation-prep tests. The FB adapter reuses the shared
``meta_webhook`` core, so these tests lock the FB-specific seams:

    * feed-comment parsing (``field == "feed"``, ``value.item == "comment"``)
    * comment → canned private reply + public ack with ``platform="facebook"``
    * public comment replies use the FB ``/comments`` edge (IG uses ``/replies``)
    * DM → agent flow keyed by the ``fb_`` CRM prefix (distinct from ``ig_``)
    * DM keyword protections (bare-trigger heuristic + ``guides_sent`` dedup)
      apply to FB DMs identically
    * language gate covers FB page ids (env-registered) and fails CLOSED for
      language-tagged rules on unregistered accounts
    * FB_ENABLED falsy → {"status": "disabled"} passthrough on the route
"""

from __future__ import annotations

import json

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from src.channels import comment_rules, meta_client, meta_webhook
from src.channels.meta_events import (
    IncomingComment,
    IncomingDM,
    parse_meta_webhook,
)
from src.crm.models import User

FB_PAGE_ID = "120079650977001"


# ---------------------------------------------------------------------------
# Payload builders
# ---------------------------------------------------------------------------


def _fb_dm_payload(text="hello", *, mid="fbm1", sender="PSID1") -> dict:
    return {
        "object": "page",
        "entry": [{
            "id": FB_PAGE_ID,
            "messaging": [{
                "sender": {"id": sender},
                "recipient": {"id": FB_PAGE_ID},
                "timestamp": 1700000000000,
                "message": {"mid": mid, "text": text},
            }],
        }],
    }


def _fb_comment_payload(text="gut", *, cid="fbc1", from_id="FBU9") -> dict:
    return {
        "object": "page",
        "entry": [{
            "id": FB_PAGE_ID,
            "changes": [{
                "field": "feed",
                "value": {
                    "item": "comment",
                    "comment_id": cid,
                    "post_id": f"{FB_PAGE_ID}_777",
                    "message": text,
                    "from": {"id": from_id},
                },
            }],
        }],
    }


# ---------------------------------------------------------------------------
# Fakes (mirrors tests/test_channels_instagram.py)
# ---------------------------------------------------------------------------


class _FakeWriterOutput:
    def __init__(self, bubbles):
        self.bubbles = list(bubbles)
        self.media_to_send = []


class _FakeResult:
    def __init__(self, out):
        self.writer_output = out


class _FakePipeline:
    def __init__(self, bubbles=("agent reply",)):
        self._out = _FakeWriterOutput(bubbles)
        self.calls = []
        self._crm = None

    async def run_turn(self, *, phone, user_message, wa_message_id=None, **_):
        self.calls.append({"phone": phone, "msg": user_message})
        return _FakeResult(self._out)


class _FakeCRM:
    def __init__(self):
        self.users = {}
        self.messages = []
        self.claimed = set()

    async def try_claim_webhook_event(self, event_id, kind):
        if event_id in self.claimed:
            return False
        self.claimed.add(event_id)
        return True

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


def _capture_sends(monkeypatch):
    """Capture every outbound meta_client call incl. the platform argument."""
    sent = []

    async def fake_send_dm(rid, text, *, platform="instagram", **_):
        sent.append(("text", rid, text, platform))
        return meta_client.SendResult(True)

    async def fake_send_dm_image(rid, url, *, platform="instagram", **_):
        sent.append(("image", rid, url, platform))
        return meta_client.SendResult(True)

    async def fake_priv(cid, text, *, platform="instagram", **_):
        sent.append(("private", cid, text, platform))
        return meta_client.SendResult(True)

    async def fake_pub(cid, text, *, platform="instagram", **_):
        sent.append(("public", cid, text, platform))
        return meta_client.SendResult(True)

    monkeypatch.setattr(meta_client, "send_dm", fake_send_dm)
    monkeypatch.setattr(meta_client, "send_dm_image", fake_send_dm_image)
    monkeypatch.setattr(meta_client, "send_private_reply", fake_priv)
    monkeypatch.setattr(meta_client, "reply_to_comment", fake_pub)
    return sent


@pytest.fixture()
def no_pauses(monkeypatch):
    monkeypatch.setattr(meta_webhook, "_MEDIA_PAUSE_S", 0.0)
    monkeypatch.setattr(meta_webhook, "_BUBBLE_PAUSE_S", 0.0)


@pytest.fixture()
def gut_rule(monkeypatch, tmp_path):
    cfg = tmp_path / "rules.json"
    cfg.write_text(json.dumps({
        "gut": {
            "dm_text": "Canned gut guide",
            "image_url": "https://x/gut.png",
            "public_ack": "Sent you a DM!",
        },
    }), encoding="utf-8")
    monkeypatch.setenv("COMMENT_RESPONSES_PATH", str(cfg))
    comment_rules._load_raw.cache_clear()
    yield
    comment_rules._load_raw.cache_clear()


def _fb_dm(text, *, sender="PSID1", mid="fbm1") -> IncomingDM:
    return IncomingDM(platform="facebook", sender_id=sender,
                      recipient_id=FB_PAGE_ID, text=text,
                      message_id=mid, timestamp=0)


# ---------------------------------------------------------------------------
# Parsing — FB feed comment shape
# ---------------------------------------------------------------------------


@pytest.mark.unit
def test_parse_fb_feed_comment():
    ev = parse_meta_webhook(_fb_comment_payload("gut pls"))[0]
    assert isinstance(ev, IncomingComment)
    assert ev.platform == "facebook"
    assert ev.crm_key == "fb_FBU9"
    assert ev.comment_id == "fbc1"
    assert ev.text == "gut pls"
    assert ev.recipient_id == FB_PAGE_ID
    assert ev.media_id == f"{FB_PAGE_ID}_777"


@pytest.mark.unit
def test_parse_fb_feed_non_comment_items_skipped():
    payload = _fb_comment_payload()
    payload["entry"][0]["changes"][0]["value"]["item"] = "reaction"
    assert parse_meta_webhook(payload) == []


# ---------------------------------------------------------------------------
# CRM key separation — fb_ vs ig_
# ---------------------------------------------------------------------------


@pytest.mark.unit
def test_crm_key_prefix_keeps_fb_and_ig_users_distinct():
    fb = IncomingDM(platform="facebook", sender_id="U9", recipient_id="P",
                    text="hi", message_id="m1", timestamp=0)
    ig = IncomingDM(platform="instagram", sender_id="U9", recipient_id="B",
                    text="hi", message_id="m2", timestamp=0)
    assert fb.crm_key == "fb_U9"
    assert ig.crm_key == "ig_U9"
    assert fb.crm_key != ig.crm_key

    fbc = IncomingComment(platform="facebook", comment_id="c1", text="t",
                          from_id="U9", from_username="", media_id="m")
    igc = IncomingComment(platform="instagram", comment_id="c2", text="t",
                          from_id="U9", from_username="u", media_id="m")
    assert fbc.crm_key == "fb_U9"
    assert igc.crm_key == "ig_U9"


@pytest.mark.asyncio
async def test_same_person_id_on_both_platforms_gets_separate_crm_rows(
    monkeypatch, no_pauses,
):
    sent = _capture_sends(monkeypatch)
    crm = _FakeCRM()
    pipe = _FakePipeline(["reply"])
    pipe._crm = crm

    ig_dm = IncomingDM(platform="instagram", sender_id="U9", recipient_id="B",
                       text="question one", message_id="m1", timestamp=0)
    fb_dm = IncomingDM(platform="facebook", sender_id="U9", recipient_id="P",
                       text="question two", message_id="m2", timestamp=0)
    await meta_webhook._dispatch_dm(ig_dm, pipe)
    await meta_webhook._dispatch_dm(fb_dm, pipe)

    assert [c["phone"] for c in pipe.calls] == ["ig_U9", "fb_U9"]
    assert sent  # sanity


# ---------------------------------------------------------------------------
# FB comment → canned private reply + public ack
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_fb_comment_keyword_gets_canned_reply_and_public_ack(
    monkeypatch, no_pauses, gut_rule,
):
    sent = _capture_sends(monkeypatch)
    pipe = _FakePipeline(["AGENT SHOULD NOT RUN"])
    crm = _FakeCRM()
    pipe._crm = crm

    comment = parse_meta_webhook(_fb_comment_payload("gut pls"))[0]
    await meta_webhook.handle_comment(comment, pipe)

    assert pipe.calls == []  # canned path — no LLM
    assert ("private", "fbc1", "Canned gut guide", "facebook") in sent
    assert ("public", "fbc1", "Sent you a DM!", "facebook") in sent
    # Canned exchange persisted under the fb_ key.
    assert [m[0] for m in crm.messages] == ["fb_FBU9", "fb_FBU9"]
    state = crm.users["fb_FBU9"].temp_state
    assert state["meta_pending_guide_images"] == ["https://x/gut.png"]
    assert "gut" in state["guides_sent"]


# ---------------------------------------------------------------------------
# Public comment reply — FB uses /comments, IG uses /replies
# ---------------------------------------------------------------------------


class _FakeHTTPResponse:
    status_code = 200
    text = "{}"


class _FakeAsyncClient:
    """Capture the URL a real reply_to_comment would POST to."""

    posted: list[tuple[str, dict]] = []

    def __init__(self, *a, **kw):
        pass

    async def __aenter__(self):
        return self

    async def __aexit__(self, *a):
        return False

    async def post(self, url, *, params=None, json=None):
        _FakeAsyncClient.posted.append((url, json or {}))
        return _FakeHTTPResponse()


@pytest.mark.asyncio
async def test_reply_to_comment_uses_platform_specific_edge(monkeypatch):
    monkeypatch.setenv("IG_PAGE_ACCESS_TOKEN", "ig_tok")
    monkeypatch.setenv("IG_USER_ID", "IGBIZ")
    monkeypatch.setenv("FB_PAGE_ACCESS_TOKEN", "fb_tok")
    monkeypatch.setenv("FB_PAGE_ID", FB_PAGE_ID)
    for var in ("META_GRAPH_BASE", "IG_GRAPH_BASE", "FB_GRAPH_BASE"):
        monkeypatch.delenv(var, raising=False)
    monkeypatch.setenv("META_GRAPH_VERSION", "v25.0")

    _FakeAsyncClient.posted = []
    monkeypatch.setattr(meta_client.httpx, "AsyncClient", _FakeAsyncClient)

    ig = await meta_client.reply_to_comment("c1", "hi", platform="instagram")
    fb = await meta_client.reply_to_comment("c2", "hi", platform="facebook")

    assert ig.ok and fb.ok
    urls = [u for u, _ in _FakeAsyncClient.posted]
    # Instagram comment replies: POST /{comment_id}/replies
    assert urls[0] == "https://graph.instagram.com/v25.0/c1/replies"
    # Facebook Page comment replies: POST /{comment_id}/comments (there is
    # no /replies edge on FB comment nodes).
    assert urls[1] == "https://graph.facebook.com/v25.0/c2/comments"


# ---------------------------------------------------------------------------
# FB DM → agent flow (persona reply, CRM persistence)
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_fb_dm_routes_to_agent_with_fb_crm_key(monkeypatch, no_pauses):
    sent = _capture_sends(monkeypatch)
    crm = _FakeCRM()
    pipe = _FakePipeline(["persona answer"])
    pipe._crm = crm

    dm = parse_meta_webhook(_fb_dm_payload("what soups help digestion?"))[0]
    await meta_webhook._dispatch_dm(dm, pipe)

    assert pipe.calls == [{"phone": "fb_PSID1", "msg": "what soups help digestion?"}]
    assert ("text", "PSID1", "persona answer", "facebook") in sent


@pytest.mark.asyncio
async def test_fb_dm_uses_registered_chloe_agent(monkeypatch, no_pauses):
    """When a default agent is registered it must serve FB DMs too, keyed fb_."""
    sent = _capture_sends(monkeypatch)

    class _FakeAgent:
        def __init__(self):
            self.calls = []

        async def respond(self, *, crm_key, user_message, message_id=None):
            self.calls.append(crm_key)

            class _Reply:
                bubbles = ["hello from persona"]
                media = []

            return _Reply()

    agent = _FakeAgent()
    monkeypatch.setattr(meta_webhook, "_chloe_agent", agent)

    pipe = _FakePipeline(["PIPELINE SHOULD NOT RUN"])
    pipe._crm = _FakeCRM()
    await meta_webhook._dispatch_dm(_fb_dm("hi there, tell me about you"), pipe)

    assert agent.calls == ["fb_PSID1"]
    assert pipe.calls == []
    assert ("text", "PSID1", "hello from persona", "facebook") in sent


# ---------------------------------------------------------------------------
# FB DM keyword protections — identical to IG
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_fb_dm_bare_keyword_gets_canned_guide(monkeypatch, no_pauses, gut_rule):
    sent = _capture_sends(monkeypatch)
    crm = _FakeCRM()
    pipe = _FakePipeline()
    pipe._crm = crm

    await meta_webhook._dispatch_dm(_fb_dm("gut pls"), pipe)

    assert pipe.calls == []  # agent skipped
    assert ("text", "PSID1", "Canned gut guide", "facebook") in sent
    assert ("image", "PSID1", "https://x/gut.png", "facebook") in sent
    assert "gut" in crm.users["fb_PSID1"].temp_state.get("guides_sent", [])


@pytest.mark.asyncio
async def test_fb_dm_genuine_question_not_hijacked_by_keyword(
    monkeypatch, no_pauses, gut_rule,
):
    sent = _capture_sends(monkeypatch)
    crm = _FakeCRM()
    pipe = _FakePipeline(["real answer about digestion"])
    pipe._crm = crm

    await meta_webhook._dispatch_dm(
        _fb_dm("my gut has been hurting after meals, what should I do"), pipe,
    )

    assert len(pipe.calls) == 1  # agent ran
    assert all(s[2] != "Canned gut guide" for s in sent)
    assert ("text", "PSID1", "real answer about digestion", "facebook") in sent


@pytest.mark.asyncio
async def test_fb_dm_guides_sent_dedup_blocks_second_canned(
    monkeypatch, no_pauses, gut_rule,
):
    sent = _capture_sends(monkeypatch)
    crm = _FakeCRM()
    pipe = _FakePipeline(["agent fallback"])
    pipe._crm = crm
    crm.users["fb_PSID1"] = User(phone="fb_PSID1").with_updates(
        temp_state={"guides_sent": ["gut"]},
    )

    await meta_webhook._dispatch_dm(_fb_dm("gut"), pipe)

    assert all(s[2] != "Canned gut guide" for s in sent)  # canned blocked
    assert len(pipe.calls) == 1  # agent answered instead


# ---------------------------------------------------------------------------
# Language gate — FB page registration + fail-closed for unregistered ids
# ---------------------------------------------------------------------------


@pytest.fixture()
def language_rules(monkeypatch, tmp_path):
    cfg = tmp_path / "rules.json"
    cfg.write_text(json.dumps([
        {"keyword": "gut", "language": "yue", "dm_text": "腸胃懶人包"},
        {"keyword": "gut", "language": "en", "dm_text": "English gut guide"},
        {"keyword": "hello", "dm_text": "untagged rule"},
    ]), encoding="utf-8")
    monkeypatch.setenv("COMMENT_RESPONSES_PATH", str(cfg))
    comment_rules._load_raw.cache_clear()
    yield
    comment_rules._load_raw.cache_clear()


@pytest.mark.unit
def test_fb_page_language_registered_via_env(monkeypatch, language_rules):
    monkeypatch.setenv("FB_PAGE_ID", FB_PAGE_ID)
    monkeypatch.setenv("FB_PAGE_LANGUAGE", "en")

    r = comment_rules.match("gut pls", account_id=FB_PAGE_ID)
    assert r is not None
    assert r.language == "en"
    assert r.dm_text == "English gut guide"  # yue rule skipped for en page


@pytest.mark.unit
def test_language_tagged_rule_fails_closed_for_unregistered_account(
    monkeypatch, language_rules,
):
    monkeypatch.delenv("FB_PAGE_ID", raising=False)
    monkeypatch.delenv("FB_PAGE_LANGUAGE", raising=False)

    # Unregistered account: language-tagged rules must NOT be served — the
    # pre-fix behavior served the first (possibly wrong-language) rule.
    assert comment_rules.match("gut pls", account_id="UNKNOWN_PAGE") is None
    # Untagged rules keep working for unregistered accounts (back-compat).
    r = comment_rules.match("hello", account_id="UNKNOWN_PAGE")
    assert r is not None and r.dm_text == "untagged rule"


@pytest.mark.unit
def test_ig_static_language_map_still_gates(monkeypatch, language_rules):
    # jackiechan.tcm is registered "en" in the static map.
    r = comment_rules.match("gut pls", account_id="17841417304649448")
    assert r is not None and r.language == "en"


# ---------------------------------------------------------------------------
# Route: FB_ENABLED falsy → disabled passthrough
# ---------------------------------------------------------------------------


@pytest.fixture()
def fb_app():
    from src.channels.facebook import router as facebook_router

    app = FastAPI()
    app.include_router(facebook_router)
    return TestClient(app)


@pytest.mark.parametrize("value", [None, "false", "FALSE", "0", ""])
def test_fb_route_disabled_passthrough(monkeypatch, fb_app, value):
    if value is None:
        monkeypatch.delenv("FB_ENABLED", raising=False)
    else:
        monkeypatch.setenv("FB_ENABLED", value)

    resp = fb_app.post(
        "/webhook/facebook",
        content=b'{"object":"page","entry":[]}',
        headers={"X-Hub-Signature-256": ""},
    )
    assert resp.status_code == 200
    assert resp.json() == {"status": "disabled"}


def test_fb_route_enabled_empty_entry_is_ignored(monkeypatch, fb_app):
    """The probe contract: enabled + authentic no-op body → "ignored"."""
    import hashlib
    import hmac as hmac_mod

    monkeypatch.setenv("FB_ENABLED", "true")
    monkeypatch.setenv("FB_APP_SECRET", "fbsecret")
    raw = b'{"object":"page","entry":[]}'
    sig = "sha256=" + hmac_mod.new(b"fbsecret", raw, hashlib.sha256).hexdigest()

    resp = fb_app.post(
        "/webhook/facebook", content=raw, headers={"X-Hub-Signature-256": sig},
    )
    assert resp.status_code == 200
    assert resp.json() == {"status": "ignored"}
