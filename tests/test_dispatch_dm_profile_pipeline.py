"""Tests for the profile-pipeline DM dispatch path (SOCIAL_PIPELINE_ACCOUNTS).

This is the FIRST change to live IG DM dispatch — real users message
Jackie (@jackiechan.tcm) via ``ChloeAgent`` today. These tests prove:

  1. Accounts NOT opted in keep routing to ChloeAgent exactly as today
     (regression guard — zero behavior change for the default case).
  2. Accounts opted in get profile-driven ``JessicaPipeline.run_turn``
     calls, with ChloeAgent's greeting-first / first-touch semantics
     replicated (greet-once keyed off CRM row existence, not history).
  3. ANY exception in the new path falls back to ``ChloeAgent.respond()``
     for that same turn — the user must never be left without a reply.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime

import pytest

from src.channels import comment_rules, meta_client, meta_webhook
from src.channels.chloe_agent import ChloeReply
from src.channels.meta_events import IncomingDM
from src.crm.models import ConversationMessage, User
from src.personas.profile import PersonaProfile

# ---------------------------------------------------------------------------
# Fakes
# ---------------------------------------------------------------------------


def _make_profile(**overrides) -> PersonaProfile:
    defaults = dict(
        key="testie",
        language="en",
        identity_name="Testie",
        allowed_specialists=frozenset({"faq", "casual"}),
        brand_policy="Testie brand policy.",
        greeting_bubbles=("Hi! I'm Testie 👋", "What's been bothering you?"),
        greeting_media_url="",
        max_bubbles=3,
    )
    defaults.update(overrides)
    return PersonaProfile(**defaults)


@dataclass
class _FakeWriterOutput:
    bubbles: list[str] = field(default_factory=list)
    media_to_send: list[dict] = field(default_factory=list)


@dataclass
class _FakeResult:
    writer_output: _FakeWriterOutput


class _FakePipeline:
    """Fake JessicaPipeline — records run_turn calls (incl. the profile
    kwarg) and returns a canned WriterOutput."""

    def __init__(self, bubbles, media=None, crm=None, raises: Exception | None = None):
        self._out = _FakeWriterOutput(list(bubbles), list(media or []))
        self.calls: list[dict] = []
        self._crm = crm
        self._raises = raises

    async def run_turn(self, *, phone, user_message, profile=None, wa_message_id=None, **_):
        self.calls.append({"phone": phone, "msg": user_message, "profile": profile})
        if self._raises is not None:
            raise self._raises
        return _FakeResult(self._out)


class _FakeCRM:
    """Models user existence explicitly via a ``users`` dict — mirrors the
    real CRM's ``get_user`` (None = brand-new visitor) vs
    ``get_or_create_user`` semantics."""

    def __init__(self):
        self.users: dict[str, User] = {}

    async def get_user(self, key):
        return self.users.get(key)

    async def get_or_create_user(self, key):
        if key not in self.users:
            self.users[key] = User(phone=key)
        return self.users[key]

    async def save_user(self, user):
        self.users[user.phone] = user


class _StubChloe:
    """Stand-in for the registered ChloeAgent fallback — records calls and
    returns a fixed reply so we can prove the safety net fired."""

    def __init__(self, bubbles=("chloe fallback reply",)):
        self.calls: list[dict] = []
        self._bubbles = list(bubbles)

    async def respond(self, *, crm_key, user_message, message_id=None):
        self.calls.append(
            {"crm_key": crm_key, "user_message": user_message, "message_id": message_id}
        )
        return ChloeReply(bubbles=list(self._bubbles))


def _no_canned_rules(monkeypatch):
    """Point comment_rules at a nonexistent file so no test message
    accidentally matches a real keyword rule."""
    monkeypatch.setenv("COMMENT_RESPONSES_PATH", "/no/such/file.json")
    comment_rules._load_raw.cache_clear()


def _capture_send_dm(monkeypatch):
    sent: list[str] = []

    async def fake_send_dm(rid, text, *, platform="instagram", **_):
        sent.append(text)
        return meta_client.SendResult(True)

    monkeypatch.setattr(meta_client, "send_dm", fake_send_dm)
    monkeypatch.setattr(meta_webhook, "_BUBBLE_PAUSE_S", 0.0)
    monkeypatch.setattr(meta_webhook, "_MEDIA_PAUSE_S", 0.0)
    return sent


# ---------------------------------------------------------------------------
# 1. Regression guard — account NOT opted in behaves exactly as today
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_account_not_in_list_routes_to_chloe_unchanged(monkeypatch):
    _no_canned_rules(monkeypatch)
    monkeypatch.delenv("SOCIAL_PIPELINE_ACCOUNTS", raising=False)
    sent = _capture_send_dm(monkeypatch)

    stub_chloe = _StubChloe(bubbles=["chloe reply"])
    monkeypatch.setattr(meta_webhook, "_chloe_agent", stub_chloe)

    profile_path_calls: list[IncomingDM] = []

    async def fake_profile_dispatch(dm):
        profile_path_calls.append(dm)
        return True

    monkeypatch.setattr(meta_webhook, "_dispatch_dm_profile_pipeline", fake_profile_dispatch)

    dm = IncomingDM(
        platform="instagram", sender_id="S1", recipient_id="SOME_OTHER_BIZ",
        text="hi", message_id="m1", timestamp=0,
    )
    await meta_webhook._dispatch_dm(dm, pipeline=None)  # type: ignore[arg-type]

    assert profile_path_calls == []  # profile path never even considered
    assert stub_chloe.calls == [{"crm_key": "ig_S1", "user_message": "hi", "message_id": "m1"}]
    assert sent == ["chloe reply"]


# ---------------------------------------------------------------------------
# 2. First-touch pure greeting -> profile greeting bubbles, NO pipeline call
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_first_touch_pure_greeting_sends_profile_greeting_no_pipeline_call(monkeypatch):
    _no_canned_rules(monkeypatch)
    monkeypatch.setenv("SOCIAL_PIPELINE_ACCOUNTS", "JACKIE_BIZ")
    sent = _capture_send_dm(monkeypatch)

    profile = _make_profile()
    monkeypatch.setattr(
        meta_webhook, "_profile_for_account",
        lambda account_id: profile if account_id == "JACKIE_BIZ" else None,
    )

    crm = _FakeCRM()  # no users yet -> get_user returns None -> first touch
    fake_pipe = _FakePipeline(bubbles=["SHOULD NEVER BE SENT"], crm=crm)
    monkeypatch.setattr(meta_webhook, "_social_pipeline", fake_pipe)

    dm = IncomingDM(
        platform="instagram", sender_id="U1", recipient_id="JACKIE_BIZ",
        text="hi!", message_id="m1", timestamp=0,
    )
    await meta_webhook._dispatch_dm(dm, pipeline=fake_pipe)  # type: ignore[arg-type]

    assert fake_pipe.calls == []  # no LLM/pipeline call for a pure greeting
    assert sent == list(profile.greeting_bubbles)


# ---------------------------------------------------------------------------
# 3. Non-greeting message -> pipeline.run_turn called with profile + crm_key
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_non_greeting_message_runs_pipeline_with_profile(monkeypatch):
    _no_canned_rules(monkeypatch)
    monkeypatch.setenv("SOCIAL_PIPELINE_ACCOUNTS", "JACKIE_BIZ")
    sent = _capture_send_dm(monkeypatch)

    profile = _make_profile()
    monkeypatch.setattr(
        meta_webhook, "_profile_for_account",
        lambda account_id: profile if account_id == "JACKIE_BIZ" else None,
    )

    crm = _FakeCRM()
    # Returning user (existing CRM row) — sidesteps greeting-prepend so we
    # can assert bubbles == answer bubbles exactly.
    crm.users["ig_U2"] = User(
        phone="ig_U2",
        conversation_history=[
            ConversationMessage(role="user", content="earlier", at=datetime.utcnow())
        ],
    )
    fake_pipe = _FakePipeline(bubbles=["Try warm ginger tea 🌿"], crm=crm)
    monkeypatch.setattr(meta_webhook, "_social_pipeline", fake_pipe)

    dm = IncomingDM(
        platform="instagram", sender_id="U2", recipient_id="JACKIE_BIZ",
        text="My knees have been aching", message_id="m2", timestamp=0,
    )
    await meta_webhook._dispatch_dm(dm, pipeline=fake_pipe)  # type: ignore[arg-type]

    assert len(fake_pipe.calls) == 1
    call = fake_pipe.calls[0]
    assert call["phone"] == "ig_U2"
    assert call["msg"] == "My knees have been aching"
    assert call["profile"] is profile
    assert sent == ["Try warm ginger tea 🌿"]


# ---------------------------------------------------------------------------
# 4. pipeline.run_turn raises -> falls back to ChloeAgent.respond() -- the
#    single most important safety-net test.
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_pipeline_exception_falls_back_to_chloe_agent(monkeypatch):
    _no_canned_rules(monkeypatch)
    monkeypatch.setenv("SOCIAL_PIPELINE_ACCOUNTS", "JACKIE_BIZ")
    sent = _capture_send_dm(monkeypatch)

    profile = _make_profile()
    monkeypatch.setattr(
        meta_webhook, "_profile_for_account",
        lambda account_id: profile if account_id == "JACKIE_BIZ" else None,
    )

    crm = _FakeCRM()  # first-touch, non-greeting -> would call run_turn
    fake_pipe = _FakePipeline(bubbles=[], crm=crm, raises=RuntimeError("LLM/DB boom"))
    monkeypatch.setattr(meta_webhook, "_social_pipeline", fake_pipe)

    stub_chloe = _StubChloe(bubbles=["Sorry, one sec — here's a reply anyway 🌿"])
    monkeypatch.setattr(meta_webhook, "_chloe_agent", stub_chloe)
    monkeypatch.setattr(meta_webhook, "_account_agents", {})  # no per-account override

    dm = IncomingDM(
        platform="instagram", sender_id="U3", recipient_id="JACKIE_BIZ",
        text="My migraines are getting worse", message_id="m3", timestamp=0,
    )
    await meta_webhook._dispatch_dm(dm, pipeline=fake_pipe)  # type: ignore[arg-type]

    # Pipeline WAS attempted (and raised) ...
    assert len(fake_pipe.calls) == 1
    # ... but the user still got a reply via the ChloeAgent fallback.
    assert stub_chloe.calls == [
        {"crm_key": "ig_U3", "user_message": "My migraines are getting worse", "message_id": "m3"}
    ]
    assert sent == ["Sorry, one sec — here's a reply anyway 🌿"]


@pytest.mark.asyncio
async def test_unmapped_account_in_list_falls_back_to_chloe_without_crash(monkeypatch):
    """Account listed in SOCIAL_PIPELINE_ACCOUNTS but with no registered
    profile (misconfiguration) must still degrade gracefully."""
    _no_canned_rules(monkeypatch)
    monkeypatch.setenv("SOCIAL_PIPELINE_ACCOUNTS", "GHOST_BIZ")
    sent = _capture_send_dm(monkeypatch)

    monkeypatch.setattr(meta_webhook, "_profile_for_account", lambda account_id: None)
    monkeypatch.setattr(meta_webhook, "_social_pipeline", _FakePipeline(bubbles=[]))

    stub_chloe = _StubChloe(bubbles=["fallback"])
    monkeypatch.setattr(meta_webhook, "_chloe_agent", stub_chloe)

    dm = IncomingDM(
        platform="instagram", sender_id="U4", recipient_id="GHOST_BIZ",
        text="hello", message_id="m4", timestamp=0,
    )
    await meta_webhook._dispatch_dm(dm, pipeline=None)  # type: ignore[arg-type]

    assert sent == ["fallback"]


# ---------------------------------------------------------------------------
# 5. Greet-once semantics preserved: existing CRM row (even with empty
#    history) must NOT get the greeting again.
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_existing_user_empty_history_does_not_regreet(monkeypatch):
    _no_canned_rules(monkeypatch)
    monkeypatch.setenv("SOCIAL_PIPELINE_ACCOUNTS", "JACKIE_BIZ")
    sent = _capture_send_dm(monkeypatch)

    profile = _make_profile()
    monkeypatch.setattr(
        meta_webhook, "_profile_for_account",
        lambda account_id: profile if account_id == "JACKIE_BIZ" else None,
    )

    crm = _FakeCRM()
    # CRM row EXISTS but history is empty (simulates the persist-hiccup
    # scenario ChloeAgent's own comment explicitly guards against).
    crm.users["ig_U5"] = User(phone="ig_U5", conversation_history=[])
    fake_pipe = _FakePipeline(bubbles=["still happy to help 🌿"], crm=crm)
    monkeypatch.setattr(meta_webhook, "_social_pipeline", fake_pipe)

    dm = IncomingDM(
        platform="instagram", sender_id="U5", recipient_id="JACKIE_BIZ",
        text="hi", message_id="m5", timestamp=0,  # pure greeting text
    )
    await meta_webhook._dispatch_dm(dm, pipeline=fake_pipe)  # type: ignore[arg-type]

    # Existing row -> NOT first touch -> pipeline runs even for "hi",
    # greeting bubbles are NOT prepended.
    assert len(fake_pipe.calls) == 1
    assert sent == ["still happy to help 🌿"]
    assert profile.greeting_bubbles[0] not in sent


# ---------------------------------------------------------------------------
# 6. End-to-end wiring sanity check (real account id + real profile loader,
#    no monkeypatching of `_profile_for_account`) — proves the feature flag
#    + account->profile mapping are wired correctly for Jackie's real IG id.
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_jackie_real_account_id_takes_profile_pipeline_path(monkeypatch):
    _no_canned_rules(monkeypatch)
    monkeypatch.setenv("SOCIAL_PIPELINE_ACCOUNTS", "17841417304649448")
    monkeypatch.setenv("IG_USER_ID_JACKIE", "17841417304649448")
    sent = _capture_send_dm(monkeypatch)

    crm = _FakeCRM()
    fake_pipe = _FakePipeline(bubbles=["Try warm ginger tea and rest your eyes 🌿"], crm=crm)
    monkeypatch.setattr(meta_webhook, "_social_pipeline", fake_pipe)

    dm = IncomingDM(
        platform="instagram", sender_id="REALU1", recipient_id="17841417304649448",
        text="My eyes have been so tired lately", message_id="m9", timestamp=0,
    )
    await meta_webhook._dispatch_dm(dm, pipeline=fake_pipe)  # type: ignore[arg-type]

    assert fake_pipe.calls, "pipeline.run_turn was never called — profile path not reached"
    call = fake_pipe.calls[0]
    assert call["phone"] == "ig_REALU1"
    assert call["profile"].key == "jackie"
    assert call["profile"].language == "en"
    # First-touch, non-greeting message -> greeting bubbles prepended, then answer.
    assert sent[0] == call["profile"].greeting_bubbles[0]
    assert sent[-1] == "Try warm ginger tea and rest your eyes 🌿"
