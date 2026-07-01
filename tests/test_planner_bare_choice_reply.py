"""Regression tests — bug fix 2026-07-01 ("David" production scenario).

Ground truth (reproduced via ``scripts/persona_dry_run_social.py --persona
jackie``): a prior canned migraine-type DM is already in CRM history
(``_MIGRAINE_CANNED_DM`` — a numbered "1. ... 2. ... 3. ..." choice
question). The user then replies with the bare digit "1". The Planner used
to route this to CASUAL (small talk) because:

  1. ``_format_history`` truncated each history message to 80 characters —
     hiding the numbered options entirely (the canned DM's preamble alone
     is ~80 chars).
  2. There was no rule/instruction telling the Planner to resolve a bare
     short reply against the previous assistant question.

This test asserts the fixed behaviour: given that exact history + user
reply, ``PlannerAgent.decide(..., profile=jackie_profile)`` selects FAQ,
never CASUAL — via the new deterministic rule in
``src.agents.planner._rule_overrides`` (so this test needs no LLM call:
`_NoOpClient` proves the LLM is never even reached, mirroring the existing
convention in tests/test_planner_profile_scope.py).
"""

from __future__ import annotations

import importlib
from datetime import datetime

import pytest

from src.agents.base import SpecialistName
from src.agents.planner import (
    PlannerAgent,
    _extract_chosen_option,
    _label_to_zh_query,
    _leading_digit,
    _looks_like_bare_choice_reply,
    _looks_like_numbered_question,
    _rule_overrides,
)
from src.crm.models import ConversationMessage, User
from src.personas.profile import load_jackie_profile

# Import the EXACT canned DM text from the dry-run script (not a re-typed
# copy) so this test can never silently drift out of sync with the real
# production scenario it guards against.
_dry_run = importlib.import_module("scripts.persona_dry_run_social")
_MIGRAINE_CANNED_DM = _dry_run._MIGRAINE_CANNED_DM


class _NoOpClient:
    """LLM client that would raise if ever called — proves the rule-based
    fast path (not the LLM) handles this scenario."""

    class messages:
        @staticmethod
        async def create(**_kwargs):  # noqa: ANN003
            raise AssertionError(
                "LLM should never be reached — the bare-choice-reply rule "
                "must short-circuit before falling through to the LLM"
            )


def _user_with_migraine_history() -> User:
    return User(
        phone="ig_test_jackie",
        conversation_history=[
            ConversationMessage(
                role="chloe", content=_MIGRAINE_CANNED_DM, at=datetime.utcnow()
            )
        ],
    )


# ---------------------------------------------------------------------------
# Unit tests on the small helpers
# ---------------------------------------------------------------------------


def test_migraine_dm_is_recognised_as_a_numbered_question() -> None:
    assert _looks_like_numbered_question(_MIGRAINE_CANNED_DM) is True


def test_bare_digit_reply_is_recognised() -> None:
    assert _looks_like_bare_choice_reply("1") is True
    assert _looks_like_bare_choice_reply("2.") is True
    assert _looks_like_bare_choice_reply("3)") is True


def test_long_sentence_is_not_a_bare_choice_reply() -> None:
    assert _looks_like_bare_choice_reply("我想問下1點去邊度買嘢") is False


def test_question_is_not_a_bare_choice_reply() -> None:
    assert _looks_like_bare_choice_reply("1?") is False


def test_extract_chosen_option_pulls_the_right_line() -> None:
    chosen = _extract_chosen_option(_MIGRAINE_CANNED_DM, "1")
    assert chosen is not None
    assert "Liver Yang Rising" in chosen
    assert "Throbbing" in chosen


def test_label_to_zh_query_resolves_known_tcm_pattern() -> None:
    option = _extract_chosen_option(_MIGRAINE_CANNED_DM, "1")
    assert _label_to_zh_query(option) == "肝陽上亢頭痛"


def test_label_to_zh_query_falls_back_to_generic_headache() -> None:
    assert _label_to_zh_query("some option with no recognised label") == "頭痛"


# ---------------------------------------------------------------------------
# _rule_overrides — the deterministic short-circuit itself
# ---------------------------------------------------------------------------


def test_bare_reply_to_migraine_question_routes_to_faq_not_casual() -> None:
    user = _user_with_migraine_history()
    decision = _rule_overrides(user, "1", [])

    assert decision is not None
    assert decision.specialists == [SpecialistName.FAQ]
    assert SpecialistName.CASUAL not in decision.specialists
    assert decision.mode == "solo"


def test_bare_reply_populates_a_kb_searchable_rephrased_query() -> None:
    """The rephrased_query must contain Chinese keywords the KB's
    keyword-matcher can actually find (the KB card is Chinese-only) —
    a bare "1" would never match anything on its own."""
    user = _user_with_migraine_history()
    decision = _rule_overrides(user, "1", [])

    assert decision is not None
    assert decision.rephrased_query == "肝陽上亢頭痛"


def test_bare_reply_notes_for_writer_quotes_the_chosen_option() -> None:
    user = _user_with_migraine_history()
    decision = _rule_overrides(user, "1", [])

    assert decision is not None
    assert "Liver Yang Rising" in decision.notes_for_writer


def test_unrelated_bare_digit_without_prior_numbered_question_falls_through() -> None:
    """A bare "1" with NO prior numbered question in history must NOT be
    caught by this rule (regression guard against false positives)."""
    user = User(
        phone="+85291234567",
        conversation_history=[
            ConversationMessage(role="user", content="hi", at=datetime.utcnow())
        ],
    )
    decision = _rule_overrides(user, "1", [])
    assert decision is None  # falls through — some other rule / the LLM decides


# ---------------------------------------------------------------------------
# End-to-end via PlannerAgent.decide() — the exact scenario from the bug
# report, profile=jackie (English, no-commerce persona).
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_decide_bare_migraine_reply_selects_faq_with_jackie_profile() -> None:
    agent = PlannerAgent(_NoOpClient())
    user = _user_with_migraine_history()
    jackie = load_jackie_profile()

    decision, usage = await agent.decide(user, "1", media_urls=[], profile=jackie)

    assert decision.specialists == [SpecialistName.FAQ]
    assert SpecialistName.CASUAL not in decision.specialists
    assert usage["shortcut"] is True  # rule fast-path, LLM never called


@pytest.mark.asyncio
async def test_decide_bare_migraine_reply_stays_within_jackie_scope() -> None:
    """FAQ is in Jackie's allowed_specialists, so the profile-scope clamp
    is a no-op here — but assert it explicitly since it's the mechanism
    that would otherwise remap an out-of-scope specialist."""
    jackie = load_jackie_profile()
    assert "faq" in jackie.allowed_specialists

    agent = PlannerAgent(_NoOpClient())
    user = _user_with_migraine_history()
    decision, _usage = await agent.decide(user, "1", media_urls=[], profile=jackie)
    assert decision.specialists == [SpecialistName.FAQ]
