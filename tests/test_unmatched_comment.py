"""Tests for src/channels/unmatched_comment.py — the new comment-reply path
that fires only when comment_rules.match() returns None.

Uses the same ``_FakeCRM`` + monkeypatched ``meta_client`` pattern already
established in tests/test_channels_instagram.py.
"""

from __future__ import annotations

import asyncio
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Any

import pytest

from src.agents.base import SpecialistName, SpecialistOutput
from src.channels import meta_client, unmatched_comment
from src.channels.meta_events import IncomingComment
from src.crm.models import User


# ---------------------------------------------------------------------------
# Fakes (mirrors tests/test_channels_instagram.py's _FakeCRM)
# ---------------------------------------------------------------------------


class _FakeCRM:
    def __init__(self) -> None:
        self.claimed: set[str] = set()
        self.messages: list[tuple[str, Any]] = []
        self.users: dict[str, User] = {}

    async def try_claim_webhook_event(self, event_id: str, kind: str) -> bool:
        if event_id in self.claimed:
            return False
        self.claimed.add(event_id)
        return True

    async def get_user(self, phone: str) -> User | None:
        return self.users.get(phone)

    async def get_or_create_user(self, phone: str) -> User:
        if phone not in self.users:
            self.users[phone] = User(phone=phone)
        return self.users[phone]

    async def save_user(self, user: User) -> None:
        self.users[user.phone] = user

    async def append_message(self, phone: str, msg: Any) -> None:
        self.messages.append((phone, msg))


class _FakePipeline:
    def __init__(self, crm: _FakeCRM | None = None) -> None:
        self._crm = crm


class _FakeFAQAgent:
    def __init__(self, output: SpecialistOutput | None = None) -> None:
        self._output = output or SpecialistOutput(
            specialist=SpecialistName.FAQ,
            payload={
                "no_match": False,
                "answer_facts": [{"fact": "some grounded fact", "card_id": "c1"}],
            },
        )
        self.calls: list[Any] = []

    async def run(self, inp: Any) -> tuple[SpecialistOutput, dict[str, Any]]:
        self.calls.append(inp)
        return self._output, {"model": "fake", "input_tokens": 0, "output_tokens": 0}


class _FakeLLMClient:
    """Placeholder — real triage/compose calls are monkeypatched per-test."""


def _comment(text: str = "does TCM help with sleep?", cid: str = "c1") -> IncomingComment:
    return IncomingComment(
        platform="instagram",
        comment_id=cid,
        text=text,
        from_id="U9",
        from_username="amy",
        media_id="media42",
        recipient_id="17841417304649448",  # Jackie's account id (registered)
    )


@pytest.fixture(autouse=True)
def _register_deps(monkeypatch: pytest.MonkeyPatch) -> None:
    """Default DI wiring — individual tests override via monkeypatch as needed."""
    unmatched_comment.set_unmatched_comment_deps(_FakeLLMClient(), _FakeFAQAgent())
    yield
    unmatched_comment.set_unmatched_comment_deps(None, None)


@pytest.fixture(autouse=True)
def _enable_and_register_account(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("UNMATCHED_COMMENT_REPLY_ENABLED", "1")
    monkeypatch.setenv("IG_USER_ID_JACKIE", "17841417304649448")


@pytest.fixture(autouse=True)
def _no_send_pauses(monkeypatch: pytest.MonkeyPatch) -> None:
    pass


async def _no_llm_calls_guard(monkeypatch: pytest.MonkeyPatch) -> list[str]:
    """Patch classify_and_mirror to record calls without doing real LLM work."""
    calls: list[str] = []

    async def fake_classify(text: str, *, client: Any, lang: str) -> Any:
        calls.append(text)
        from src.channels.comment_triage import CommentTriage
        return CommentTriage(is_genuine=True, topic_mirror="mirrored topic", reason="ok")

    monkeypatch.setattr(unmatched_comment, "classify_and_mirror", fake_classify)
    return calls


# ---------------------------------------------------------------------------
# Master flag disabled — byte-identical to today (regression pin)
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_master_flag_disabled_zero_calls(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("UNMATCHED_COMMENT_REPLY_ENABLED", "0")
    private, public = [], []

    async def fake_priv(*a: Any, **kw: Any) -> meta_client.SendResult:
        private.append((a, kw)); return meta_client.SendResult(True)

    async def fake_pub(*a: Any, **kw: Any) -> meta_client.SendResult:
        public.append((a, kw)); return meta_client.SendResult(True)

    monkeypatch.setattr(meta_client, "send_private_reply", fake_priv)
    monkeypatch.setattr(meta_client, "reply_to_comment", fake_pub)

    crm = _FakeCRM()
    pipeline = _FakePipeline(crm)
    await unmatched_comment.handle_unmatched_comment(_comment(), pipeline)

    assert private == []
    assert public == []
    assert crm.users == {}


# ---------------------------------------------------------------------------
# Deterministic pre-filters — zero LLM calls
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_comment_too_short_zero_llm_calls(monkeypatch: pytest.MonkeyPatch) -> None:
    calls = await _no_llm_calls_guard(monkeypatch)
    crm = _FakeCRM()
    await unmatched_comment.handle_unmatched_comment(_comment(text="hi"), _FakePipeline(crm))
    assert calls == []
    assert crm.users == {}


@pytest.mark.asyncio
async def test_comment_too_long_zero_llm_calls(monkeypatch: pytest.MonkeyPatch) -> None:
    calls = await _no_llm_calls_guard(monkeypatch)
    monkeypatch.setenv("UNMATCHED_COMMENT_MAX_TEXT_LEN", "10")
    crm = _FakeCRM()
    await unmatched_comment.handle_unmatched_comment(
        _comment(text="this comment is definitely longer than ten characters"),
        _FakePipeline(crm),
    )
    assert calls == []
    assert crm.users == {}


@pytest.mark.asyncio
async def test_emoji_only_comment_zero_llm_calls(monkeypatch: pytest.MonkeyPatch) -> None:
    calls = await _no_llm_calls_guard(monkeypatch)
    crm = _FakeCRM()
    await unmatched_comment.handle_unmatched_comment(
        _comment(text="😍😍😍!!!"), _FakePipeline(crm)
    )
    assert calls == []
    assert crm.users == {}


@pytest.mark.asyncio
async def test_unregistered_account_skips(monkeypatch: pytest.MonkeyPatch) -> None:
    calls = await _no_llm_calls_guard(monkeypatch)
    crm = _FakeCRM()
    comment = _comment(cid="c_unreg")
    comment = IncomingComment(
        platform="instagram", comment_id="c_unreg", text="does TCM help with sleep?",
        from_id="U9", from_username="amy", media_id="media42",
        recipient_id="UNKNOWN_ACCOUNT_ID",
    )
    await unmatched_comment.handle_unmatched_comment(comment, _FakePipeline(crm))
    assert calls == []
    assert crm.users == {}


# ---------------------------------------------------------------------------
# Per-user daily cap
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_over_daily_cap_skips(monkeypatch: pytest.MonkeyPatch) -> None:
    calls = await _no_llm_calls_guard(monkeypatch)
    monkeypatch.setenv("UNMATCHED_COMMENT_MAX_PER_USER_PER_DAY", "1")
    crm = _FakeCRM()
    today = unmatched_comment._today_key()
    crm.users["ig_U9"] = User(
        phone="ig_U9", temp_state={"unmatched_reply_log": {today: 1}}
    )
    await unmatched_comment.handle_unmatched_comment(_comment(), _FakePipeline(crm))
    assert calls == []


# ---------------------------------------------------------------------------
# Gate says not-genuine
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_gate_not_genuine_no_dm_no_public_reply(monkeypatch: pytest.MonkeyPatch) -> None:
    async def fake_classify(text: str, *, client: Any, lang: str) -> Any:
        from src.channels.comment_triage import CommentTriage
        return CommentTriage(is_genuine=False, topic_mirror="", reason="spam")

    monkeypatch.setattr(unmatched_comment, "classify_and_mirror", fake_classify)

    private, public = [], []

    async def fake_priv(*a: Any, **kw: Any) -> meta_client.SendResult:
        private.append((a, kw)); return meta_client.SendResult(True)

    async def fake_pub(*a: Any, **kw: Any) -> meta_client.SendResult:
        public.append((a, kw)); return meta_client.SendResult(True)

    monkeypatch.setattr(meta_client, "send_private_reply", fake_priv)
    monkeypatch.setattr(meta_client, "reply_to_comment", fake_pub)

    crm = _FakeCRM()
    await unmatched_comment.handle_unmatched_comment(_comment(), _FakePipeline(crm))

    assert private == []
    assert public == []
    # Pinned behavior (post-fix #2): the cap now means "N processing
    # attempts per user per day," not "N successful replies per user per
    # day" — a spam-classified comment still cost an LLM call (the triage
    # classify itself), so it still counts against the cap.
    assert "ig_U9" in crm.users
    today = unmatched_comment._today_key()
    assert crm.users["ig_U9"].temp_state["unmatched_reply_log"][today] == 1


# ---------------------------------------------------------------------------
# DM send failure -> public mirror NOT sent (hard ordering invariant)
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_dm_send_failure_blocks_public_mirror(monkeypatch: pytest.MonkeyPatch) -> None:
    await _no_llm_calls_guard(monkeypatch)  # is_genuine=True fake

    public = []

    async def fake_priv(*a: Any, **kw: Any) -> meta_client.SendResult:
        return meta_client.SendResult(False, "http 500")

    async def fake_pub(*a: Any, **kw: Any) -> meta_client.SendResult:
        public.append((a, kw)); return meta_client.SendResult(True)

    monkeypatch.setattr(meta_client, "send_private_reply", fake_priv)
    monkeypatch.setattr(meta_client, "reply_to_comment", fake_pub)

    faq_agent = _FakeFAQAgent()
    unmatched_comment.set_unmatched_comment_deps(_FakeLLMClient(), faq_agent)

    async def fake_compose(*a: Any, **kw: Any) -> str:
        return "a grounded DM reply"

    monkeypatch.setattr(unmatched_comment, "compose_faq_dm", fake_compose)

    crm = _FakeCRM()
    await unmatched_comment.handle_unmatched_comment(_comment(), _FakePipeline(crm))

    assert public == []  # the hard invariant: no public-only spam


# ---------------------------------------------------------------------------
# no_match FAQ output -> no DM AND no public mirror
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_faq_no_match_skips_dm_and_public_mirror(monkeypatch: pytest.MonkeyPatch) -> None:
    await _no_llm_calls_guard(monkeypatch)

    private, public = [], []

    async def fake_priv(*a: Any, **kw: Any) -> meta_client.SendResult:
        private.append((a, kw)); return meta_client.SendResult(True)

    async def fake_pub(*a: Any, **kw: Any) -> meta_client.SendResult:
        public.append((a, kw)); return meta_client.SendResult(True)

    monkeypatch.setattr(meta_client, "send_private_reply", fake_priv)
    monkeypatch.setattr(meta_client, "reply_to_comment", fake_pub)

    faq_agent = _FakeFAQAgent(
        SpecialistOutput(specialist=SpecialistName.FAQ, payload={"no_match": True, "answer_facts": []})
    )
    unmatched_comment.set_unmatched_comment_deps(_FakeLLMClient(), faq_agent)

    crm = _FakeCRM()
    await unmatched_comment.handle_unmatched_comment(_comment(), _FakePipeline(crm))

    assert private == []
    assert public == []
    # Post-fix #2: genuine-but-unanswerable still spent an LLM call
    # (triage + FAQAgent.run), so it still counts against the daily cap.
    today = unmatched_comment._today_key()
    assert crm.users["ig_U9"].temp_state["unmatched_reply_log"][today] == 1


# ---------------------------------------------------------------------------
# Full happy path — DM sent, THEN public mirror sent (assert call order)
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_happy_path_dm_then_public_mirror_in_order(monkeypatch: pytest.MonkeyPatch) -> None:
    await _no_llm_calls_guard(monkeypatch)  # topic_mirror="mirrored topic" (safe)

    call_order: list[str] = []

    async def fake_priv(comment_id: str, text: str, **kw: Any) -> meta_client.SendResult:
        call_order.append("private")
        return meta_client.SendResult(True)

    async def fake_pub(comment_id: str, text: str, **kw: Any) -> meta_client.SendResult:
        call_order.append("public")
        return meta_client.SendResult(True)

    monkeypatch.setattr(meta_client, "send_private_reply", fake_priv)
    monkeypatch.setattr(meta_client, "reply_to_comment", fake_pub)

    async def fake_compose(*a: Any, **kw: Any) -> str:
        return "a grounded DM reply"

    monkeypatch.setattr(unmatched_comment, "compose_faq_dm", fake_compose)

    faq_agent = _FakeFAQAgent()
    unmatched_comment.set_unmatched_comment_deps(_FakeLLMClient(), faq_agent)

    crm = _FakeCRM()
    await unmatched_comment.handle_unmatched_comment(_comment(), _FakePipeline(crm))

    assert call_order == ["private", "public"]
    assert faq_agent.calls  # FAQAgent.run() was invoked
    # CRM history persisted for ChloeAgent's next-turn context
    assert any(m[0] == "ig_U9" for m in crm.messages)
    # Daily cap incremented
    today = unmatched_comment._today_key()
    assert crm.users["ig_U9"].temp_state["unmatched_reply_log"][today] == 1


@pytest.mark.asyncio
async def test_public_reply_disabled_env_skips_public_mirror(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    await _no_llm_calls_guard(monkeypatch)
    monkeypatch.setenv("UNMATCHED_COMMENT_PUBLIC_REPLY_ENABLED", "0")

    public = []

    async def fake_priv(*a: Any, **kw: Any) -> meta_client.SendResult:
        return meta_client.SendResult(True)

    async def fake_pub(*a: Any, **kw: Any) -> meta_client.SendResult:
        public.append((a, kw)); return meta_client.SendResult(True)

    monkeypatch.setattr(meta_client, "send_private_reply", fake_priv)
    monkeypatch.setattr(meta_client, "reply_to_comment", fake_pub)

    async def fake_compose(*a: Any, **kw: Any) -> str:
        return "a grounded DM reply"

    monkeypatch.setattr(unmatched_comment, "compose_faq_dm", fake_compose)
    unmatched_comment.set_unmatched_comment_deps(_FakeLLMClient(), _FakeFAQAgent())

    crm = _FakeCRM()
    await unmatched_comment.handle_unmatched_comment(_comment(), _FakePipeline(crm))

    assert public == []


@pytest.mark.asyncio
async def test_unsafe_mirror_skips_public_reply(monkeypatch: pytest.MonkeyPatch) -> None:
    async def fake_classify(text: str, *, client: Any, lang: str) -> Any:
        from src.channels.comment_triage import CommentTriage
        return CommentTriage(is_genuine=True, topic_mirror="just visit our 診所!", reason="ok")

    monkeypatch.setattr(unmatched_comment, "classify_and_mirror", fake_classify)

    public = []

    async def fake_priv(*a: Any, **kw: Any) -> meta_client.SendResult:
        return meta_client.SendResult(True)

    async def fake_pub(*a: Any, **kw: Any) -> meta_client.SendResult:
        public.append((a, kw)); return meta_client.SendResult(True)

    monkeypatch.setattr(meta_client, "send_private_reply", fake_priv)
    monkeypatch.setattr(meta_client, "reply_to_comment", fake_pub)

    async def fake_compose(*a: Any, **kw: Any) -> str:
        return "a grounded DM reply"

    monkeypatch.setattr(unmatched_comment, "compose_faq_dm", fake_compose)
    unmatched_comment.set_unmatched_comment_deps(_FakeLLMClient(), _FakeFAQAgent())

    crm = _FakeCRM()
    await unmatched_comment.handle_unmatched_comment(_comment(), _FakePipeline(crm))

    assert public == []


# ---------------------------------------------------------------------------
# Item 1 — daily-cap read-modify-write race (per-user lock)
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_concurrent_same_user_respects_daily_cap(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Regression for the read-modify-write race: two comments from the
    SAME crm_key processed concurrently (as independent background tasks)
    must not both bypass a cap of 1 — the second must see the first's
    increment before deciding to send."""
    monkeypatch.setenv("UNMATCHED_COMMENT_MAX_PER_USER_PER_DAY", "1")

    class _RacyCRM(_FakeCRM):
        async def get_or_create_user(self, phone: str) -> User:
            # Force a yield point between "read the cap" and "write the
            # increment" so two concurrent calls for the same user are
            # guaranteed to interleave here absent a per-user lock.
            await asyncio.sleep(0)
            return await super().get_or_create_user(phone)

    async def fake_classify(text: str, *, client: Any, lang: str) -> Any:
        from src.channels.comment_triage import CommentTriage
        return CommentTriage(is_genuine=True, topic_mirror="mirrored topic", reason="ok")

    monkeypatch.setattr(unmatched_comment, "classify_and_mirror", fake_classify)

    async def fake_compose(*a: Any, **kw: Any) -> str:
        return "a grounded DM reply"

    monkeypatch.setattr(unmatched_comment, "compose_faq_dm", fake_compose)

    sends: list[str] = []

    async def fake_priv(comment_id: str, *a: Any, **kw: Any) -> meta_client.SendResult:
        sends.append(comment_id)
        return meta_client.SendResult(True)

    async def fake_pub(*a: Any, **kw: Any) -> meta_client.SendResult:
        return meta_client.SendResult(True)

    monkeypatch.setattr(meta_client, "send_private_reply", fake_priv)
    monkeypatch.setattr(meta_client, "reply_to_comment", fake_pub)

    faq_agent = _FakeFAQAgent()
    unmatched_comment.set_unmatched_comment_deps(_FakeLLMClient(), faq_agent)

    crm = _RacyCRM()
    pipeline = _FakePipeline(crm)

    await asyncio.gather(
        unmatched_comment.handle_unmatched_comment(_comment(cid="c_a"), pipeline),
        unmatched_comment.handle_unmatched_comment(_comment(cid="c_b"), pipeline),
    )

    assert len(sends) == 1
    today = unmatched_comment._today_key()
    assert crm.users["ig_U9"].temp_state["unmatched_reply_log"][today] == 1


# ---------------------------------------------------------------------------
# Item 4 — no unhandled exception from FAQAgent.run() / compose_faq_dm()
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_faq_agent_run_exception_does_not_propagate(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    await _no_llm_calls_guard(monkeypatch)  # is_genuine=True fake

    class _BoomFAQAgent:
        async def run(self, inp: Any) -> Any:
            raise RuntimeError("faq agent boom")

    unmatched_comment.set_unmatched_comment_deps(_FakeLLMClient(), _BoomFAQAgent())

    private, public = [], []

    async def fake_priv(*a: Any, **kw: Any) -> meta_client.SendResult:
        private.append((a, kw)); return meta_client.SendResult(True)

    async def fake_pub(*a: Any, **kw: Any) -> meta_client.SendResult:
        public.append((a, kw)); return meta_client.SendResult(True)

    monkeypatch.setattr(meta_client, "send_private_reply", fake_priv)
    monkeypatch.setattr(meta_client, "reply_to_comment", fake_pub)

    crm = _FakeCRM()
    # Must not raise.
    await unmatched_comment.handle_unmatched_comment(_comment(), _FakePipeline(crm))

    assert private == []
    assert public == []


@pytest.mark.asyncio
async def test_compose_faq_dm_exception_does_not_propagate(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    await _no_llm_calls_guard(monkeypatch)  # is_genuine=True fake

    async def fake_compose(*a: Any, **kw: Any) -> str:
        raise RuntimeError("compose boom")

    monkeypatch.setattr(unmatched_comment, "compose_faq_dm", fake_compose)

    private, public = [], []

    async def fake_priv(*a: Any, **kw: Any) -> meta_client.SendResult:
        private.append((a, kw)); return meta_client.SendResult(True)

    async def fake_pub(*a: Any, **kw: Any) -> meta_client.SendResult:
        public.append((a, kw)); return meta_client.SendResult(True)

    monkeypatch.setattr(meta_client, "send_private_reply", fake_priv)
    monkeypatch.setattr(meta_client, "reply_to_comment", fake_pub)

    faq_agent = _FakeFAQAgent()
    unmatched_comment.set_unmatched_comment_deps(_FakeLLMClient(), faq_agent)

    crm = _FakeCRM()
    # Must not raise.
    await unmatched_comment.handle_unmatched_comment(_comment(), _FakePipeline(crm))

    assert private == []
    assert public == []


# ---------------------------------------------------------------------------
# Item 6 — composed DM text also runs through the deterministic safety
# check (defense-in-depth; DM is private, but cheap to add)
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_unsafe_composed_dm_is_not_sent(monkeypatch: pytest.MonkeyPatch) -> None:
    await _no_llm_calls_guard(monkeypatch)  # is_genuine=True fake, safe topic_mirror

    async def fake_compose(*a: Any, **kw: Any) -> str:
        return "just $50 for the full course"  # blocked price pattern

    monkeypatch.setattr(unmatched_comment, "compose_faq_dm", fake_compose)

    private, public = [], []

    async def fake_priv(*a: Any, **kw: Any) -> meta_client.SendResult:
        private.append((a, kw)); return meta_client.SendResult(True)

    async def fake_pub(*a: Any, **kw: Any) -> meta_client.SendResult:
        public.append((a, kw)); return meta_client.SendResult(True)

    monkeypatch.setattr(meta_client, "send_private_reply", fake_priv)
    monkeypatch.setattr(meta_client, "reply_to_comment", fake_pub)

    faq_agent = _FakeFAQAgent()
    unmatched_comment.set_unmatched_comment_deps(_FakeLLMClient(), faq_agent)

    crm = _FakeCRM()
    await unmatched_comment.handle_unmatched_comment(_comment(), _FakePipeline(crm))

    assert private == []
    assert public == []


# ---------------------------------------------------------------------------
# Item 8 — MIN > MAX config guard
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_misconfigured_min_greater_than_max_does_not_blackhole_everything(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """If MIN ends up > MAX via misconfigured env vars, the length gate
    must not silently reject every comment forever."""
    monkeypatch.setenv("UNMATCHED_COMMENT_MIN_TEXT_LEN", "50")
    monkeypatch.setenv("UNMATCHED_COMMENT_MAX_TEXT_LEN", "10")

    calls = await _no_llm_calls_guard(monkeypatch)
    crm = _FakeCRM()
    await unmatched_comment.handle_unmatched_comment(
        _comment(text="does TCM help with sleep?"), _FakePipeline(crm)
    )
    # The length gate is effectively disabled rather than blackholing
    # every comment — processing continues past it.
    assert calls == ["does TCM help with sleep?"]
