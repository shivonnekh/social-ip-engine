"""DM keyword short-circuit must not hijack genuine questions.

Regression tests for the 2026-07-02 "Irene" incident: a real question
("Hi, what about dark under-eye circle? Is there any ways to fix it?")
substring-matched the ``eye`` comment rule and received the canned guide
for the 5th time instead of an agent answer.

Two protections under test:
1. ``_is_bare_keyword_trigger`` — canned guides in DMs only fire when the
   message is essentially the keyword itself, not a sentence/question that
   happens to contain it.
2. ``guides_sent`` dedup — the same canned guide is never sent twice to the
   same user, even when conversation history is missing (the backfill-wrote-
   to-local-SQLite failure mode).
"""

import json

import pytest

from src.channels import comment_rules, meta_client, meta_webhook
from src.channels.meta_events import IncomingDM
from src.crm.models import User


# ---------------------------------------------------------------------------
# Unit: _is_bare_keyword_trigger
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("text,keyword", [
    ("eye", "eye"),
    ("eye pls", "eye"),
    ("EYE", "eye"),
    ("gut", "gut"),
    ("  teeth  ", "teeth"),
    ("腸胃", "腸胃"),
    ("warm", "warm"),
    ("want eye guide", "eye"),             # explicit guide request = canned OK
    ("can i get the gut guide pls", "gut"),
    ("eye 🙏🙏", "eye"),                    # emoji is filler
    ("腸胃 唔該", "腸胃"),                   # Cantonese courtesy filler
])
def test_bare_keyword_triggers(text, keyword):
    assert meta_webhook._is_bare_keyword_trigger(text, keyword) is True


@pytest.mark.parametrize("text,keyword", [
    # The Irene message — question containing a keyword substring.
    ("Hi, what about dark under-eye circle? Is there any  ways to fix it?", "eye"),
    ("what about eye", "eye"),             # question without "?"
    ("tell me more about eye care", "eye"),
    ("eye?", "eye"),                       # question mark = a question
    ("my eye hurts", "eye"),               # symptom statement → agent
    ("sore eye today", "eye"),             # symptom statement → agent
    ("眼乾點算好？", "眼"),                  # Cantonese question mark
    ("眼點算好", "眼"),                     # punctuation-less Cantonese question
    ("腸胃 幾時好返", "腸胃"),               # punctuation-less Cantonese question
    ("眼腫點算", "眼"),                     # Cantonese complaint
    ("我想知道點樣改善眼乾同埋黑眼圈嘅問題", "眼"),  # long CJK sentence
    ("", "eye"),                           # empty never triggers
    ("   ", "eye"),
    ("eye", ""),                           # no keyword never triggers
])
def test_real_messages_do_not_trigger(text, keyword):
    assert meta_webhook._is_bare_keyword_trigger(text, keyword) is False


# ---------------------------------------------------------------------------
# Integration: _dispatch_dm routing
# ---------------------------------------------------------------------------

class _FakeWriterOutput:
    def __init__(self, bubbles):
        self.bubbles = bubbles
        self.media_to_send = []


class _FakeResult:
    def __init__(self, out):
        self.writer_output = out


class _FakePipeline:
    def __init__(self, bubbles=("agent reply",)):
        self._out = _FakeWriterOutput(list(bubbles))
        self.calls = []
        self._crm = None

    async def run_turn(self, *, phone, user_message, wa_message_id=None, **_):
        self.calls.append({"phone": phone, "msg": user_message})
        return _FakeResult(self._out)


class _FakeCRM:
    def __init__(self):
        self.users = {}
        self.messages = []

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


@pytest.fixture()
def eye_rule(monkeypatch, tmp_path):
    cfg = tmp_path / "rules.json"
    cfg.write_text(json.dumps({
        "eye": {"dm_text": "Canned eye guide", "image_url": "https://x/eye.png"},
    }), encoding="utf-8")
    monkeypatch.setenv("COMMENT_RESPONSES_PATH", str(cfg))
    comment_rules._load_raw.cache_clear()
    monkeypatch.setattr(meta_webhook, "_MEDIA_PAUSE_S", 0.0)
    monkeypatch.setattr(meta_webhook, "_BUBBLE_PAUSE_S", 0.0)
    yield
    comment_rules._load_raw.cache_clear()


def _dm(text, sender="IRENE"):
    return IncomingDM(platform="instagram", sender_id=sender, recipient_id="BIZ",
                      text=text, message_id="m1", timestamp=0)


def _capture_sends(monkeypatch):
    sent = []

    async def fake_send_dm(rid, text, *, platform="instagram", **_):
        sent.append(("text", rid, text))
        return meta_client.SendResult(True)

    async def fake_send_dm_image(rid, url, *, platform="instagram", **_):
        sent.append(("image", rid, url))
        return meta_client.SendResult(True)

    monkeypatch.setattr(meta_client, "send_dm", fake_send_dm)
    monkeypatch.setattr(meta_client, "send_dm_image", fake_send_dm_image)
    return sent


@pytest.mark.asyncio
async def test_bare_keyword_dm_gets_canned_guide(monkeypatch, eye_rule):
    sent = _capture_sends(monkeypatch)
    pipe = _FakePipeline()
    pipe._crm = _FakeCRM()

    await meta_webhook._dispatch_dm(_dm("eye"), pipe)

    assert pipe.calls == []                                   # agent skipped
    assert ("text", "IRENE", "Canned eye guide") in sent      # canned sent


@pytest.mark.asyncio
async def test_question_containing_keyword_goes_to_agent(monkeypatch, eye_rule):
    """The Irene regression: her question must reach the agent, not canned."""
    sent = _capture_sends(monkeypatch)
    pipe = _FakePipeline(["real answer about dark circles"])
    pipe._crm = _FakeCRM()

    await meta_webhook._dispatch_dm(
        _dm("Hi, what about dark under-eye circle? Is there any  ways to fix it?"),
        pipe,
    )

    assert len(pipe.calls) == 1                               # agent ran
    assert all(s[2] != "Canned eye guide" for s in sent)      # no canned
    assert ("text", "IRENE", "real answer about dark circles") in sent


@pytest.mark.asyncio
async def test_canned_dispatch_records_guides_sent(monkeypatch, eye_rule):
    sent = _capture_sends(monkeypatch)
    pipe = _FakePipeline()
    crm = _FakeCRM()
    pipe._crm = crm

    await meta_webhook._dispatch_dm(_dm("eye"), pipe)

    user = crm.users["ig_IRENE"]
    assert "eye" in (user.temp_state or {}).get("guides_sent", [])
    assert sent  # sanity: something was sent


@pytest.mark.asyncio
async def test_same_guide_never_sent_twice_even_without_history(monkeypatch, eye_rule):
    """Dedup must hold even when conversation history is empty (the
    backfill-wrote-to-local-SQLite failure mode leaves prod history empty)."""
    sent = _capture_sends(monkeypatch)
    pipe = _FakePipeline(["agent fallback"])
    crm = _FakeCRM()
    pipe._crm = crm
    # User exists with the guide already recorded, but NO history rows.
    crm.users["ig_IRENE"] = User(phone="ig_IRENE").with_updates(
        temp_state={"guides_sent": ["eye"]},
    )

    await meta_webhook._dispatch_dm(_dm("eye"), pipe)

    assert all(s[2] != "Canned eye guide" for s in sent)      # canned blocked
    assert len(pipe.calls) == 1                               # agent answered instead
