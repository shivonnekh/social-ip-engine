"""Regression tests — bug fix 2026-07-01: an English-only persona (Jackie,
``PersonaProfile.language == "en"``) must NEVER have Chinese characters in
its WriterAgent output, across representative conversation scenarios:
greeting-flavoured chat, an FAQ knowledge answer, an off-topic redirect,
and the exact migraine-type scenario from the production bug report.

Two layers are under test, matching the bug's two root causes:
  1. The English skeleton system prompt (``_build_system_prompt`` picking
     ``_SKELETON_TEMPLATE_EN`` for ``language == "en"``) — exercised
     implicitly by every call to ``WriterAgent.compose(profile=jackie)``.
  2. The hard code-level CJK enforcement in ``WriterAgent.compose`` —
     exercised directly by feeding the fake LLM a deliberately Chinese
     response (reproducing the actual observed bug: "Haha收到呀 😄" /
     "近排忙唔忙呀？") and asserting the FINAL bubbles sent to the user
     are always 100% CJK-free, via retry-then-fallback.

LLM mocking follows this repo's existing convention (see
tests/test_tongue_progress.py::_mock_llm, tests/test_menstrual_care.py):
``MagicMock`` responses with ``.content`` / ``.usage``, and
``AsyncMock(side_effect=[...])`` for sequential calls.
"""

from __future__ import annotations

import json
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock

import pytest

from src.agents.base import (
    PlannerDecision,
    SpecialistName,
    SpecialistOutput,
)
from src.agents.writer import WriterAgent, _bubbles_contain_cjk
from src.crm.models import User
from src.personas.profile import load_chloe_profile, load_jackie_profile

_JACKIE = load_jackie_profile()
_CHLOE = load_chloe_profile()


def _mock_llm(*response_texts: str) -> MagicMock:
    """Sequential fake LLM — each call returns the next `response_texts`
    entry, mirroring tests/test_tongue_progress.py::_mock_llm."""
    responses = []
    for text in response_texts:
        resp = MagicMock()
        resp.content = [MagicMock(type="text", text=text)]
        resp.usage = MagicMock(input_tokens=50, output_tokens=30)
        responses.append(resp)
    llm = MagicMock()
    llm.messages = MagicMock()
    llm.messages.create = AsyncMock(side_effect=responses)
    return llm


def _bubbles_json(bubbles: list[str]) -> str:
    return json.dumps({"bubbles": bubbles, "media_to_send": []}, ensure_ascii=False)


def _user() -> User:
    return User(phone="ig_test_jackie")


def _decision(specialists: list[SpecialistName], **kw) -> PlannerDecision:
    return PlannerDecision(specialists=specialists, mode="solo", reasoning="test", **kw)


# ---------------------------------------------------------------------------
# Scenario fixtures — (specialist_outputs, planner_decision, user_message)
# ---------------------------------------------------------------------------


def _greeting_scenario() -> tuple[list[SpecialistOutput], PlannerDecision, str]:
    outputs = [
        SpecialistOutput(
            specialist=SpecialistName.CASUAL,
            payload={
                "tone": "warm",
                "topic": "first time chatting",
                "lifestyle_question": None,
                "soft_pivot_hint": None,
            },
        )
    ]
    decision = _decision([SpecialistName.CASUAL])
    return outputs, decision, "hi there!"


def _faq_answer_scenario() -> tuple[list[SpecialistOutput], PlannerDecision, str]:
    outputs = [
        SpecialistOutput(
            specialist=SpecialistName.FAQ,
            payload={
                "answer_facts": [
                    {"fact": "Ginger tea helps with cold-type stomach discomfort", "card_id": "tcm_digestion"}
                ],
                "confidence": 0.8,
                "next_best_question": None,
                "no_match": False,
            },
            cards_used=["tcm_digestion"],
        )
    ]
    decision = _decision([SpecialistName.FAQ])
    return outputs, decision, "why does my stomach hurt after cold drinks?"


def _off_topic_redirect_scenario() -> tuple[list[SpecialistOutput], PlannerDecision, str]:
    outputs = [
        SpecialistOutput(
            specialist=SpecialistName.CASUAL,
            payload={
                "tone": "neutral",
                "topic": "asked about something unrelated to TCM",
                "lifestyle_question": None,
                "soft_pivot_hint": None,
            },
        )
    ]
    decision = _decision(
        [SpecialistName.CASUAL],
        notes_for_writer="用戶問緊同 TCM 無關嘅嘢 (e.g. 體育賽果) — 溫柔咁帶返正題。",
    )
    return outputs, decision, "who won the game last night?"


def _migraine_scenario() -> tuple[list[SpecialistOutput], PlannerDecision, str]:
    outputs = [
        SpecialistOutput(
            specialist=SpecialistName.FAQ,
            payload={
                "answer_facts": [],
                "confidence": 0.0,
                "next_best_question": None,
                "no_match": True,
            },
        )
    ]
    decision = _decision(
        [SpecialistName.FAQ],
        rephrased_query="肝陽上亢頭痛",
        notes_for_writer=(
            "用戶啱啱覆咗「1」去回應上一句嘅編號選擇題。佢揀嘅選項係：「Throbbing, "
            "one side, worse when stressed, better lying down in the dark "
            "(Liver Yang Rising)」。Writer：直接確認返佢揀咗嗰個選項，然後用 FAQ "
            "payload 嘅內容俾返針對性建議 — 唔好當純閒聊。"
        ),
    )
    return outputs, decision, "1"


_SCENARIOS = {
    "greeting": _greeting_scenario,
    "faq_answer": _faq_answer_scenario,
    "off_topic_redirect": _off_topic_redirect_scenario,
    "migraine_type": _migraine_scenario,
}


# ---------------------------------------------------------------------------
# Normal path — a well-behaved English LLM response needs no retry
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
@pytest.mark.parametrize("scenario_name", list(_SCENARIOS.keys()))
async def test_clean_english_response_passes_through_unmodified(scenario_name: str) -> None:
    outputs, decision, user_message = _SCENARIOS[scenario_name]()
    clean_bubbles = ["Hey! Thanks for sharing that with me 🌿", "Here's what might help."]
    llm = _mock_llm(_bubbles_json(clean_bubbles))
    writer = WriterAgent(llm)

    output, _usage = await writer.compose(
        user=_user(),
        user_message=user_message,
        planner_decision=decision,
        specialist_outputs=outputs,
        profile=_JACKIE,
    )

    assert output.bubbles == clean_bubbles
    assert _bubbles_contain_cjk(output.bubbles) is False
    # No retry needed — exactly one LLM call.
    assert llm.messages.create.await_count == 1


# ---------------------------------------------------------------------------
# Hard enforcement — LLM leaks CJK; retry recovers with clean English
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
@pytest.mark.parametrize("scenario_name", list(_SCENARIOS.keys()))
async def test_cjk_leak_is_caught_and_retry_recovers(scenario_name: str) -> None:
    outputs, decision, user_message = _SCENARIOS[scenario_name]()
    # First call reproduces the actual observed production bug.
    buggy_bubbles = ["Haha收到呀 😄", "近排忙唔忙呀？"]
    # Retry (stronger reminder) succeeds with clean English.
    fixed_bubbles = ["Haha got it! 😄", "Been busy lately?"]
    llm = _mock_llm(_bubbles_json(buggy_bubbles), _bubbles_json(fixed_bubbles))
    writer = WriterAgent(llm)

    output, _usage = await writer.compose(
        user=_user(),
        user_message=user_message,
        planner_decision=decision,
        specialist_outputs=outputs,
        profile=_JACKIE,
    )

    assert _bubbles_contain_cjk(output.bubbles) is False
    assert output.bubbles == fixed_bubbles
    # First call (buggy) + retry call.
    assert llm.messages.create.await_count == 2


# ---------------------------------------------------------------------------
# Hard enforcement — retry ALSO leaks CJK → safe generic English fallback
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_cjk_leak_persists_through_retry_falls_back_to_safe_english() -> None:
    outputs, decision, user_message = _migraine_scenario()
    still_buggy = ["咁樣你就明白喇 😄"]
    llm = _mock_llm(_bubbles_json(["Haha收到呀 😄"]), _bubbles_json(still_buggy))
    writer = WriterAgent(llm)

    output, _usage = await writer.compose(
        user=_user(),
        user_message=user_message,
        planner_decision=decision,
        specialist_outputs=outputs,
        profile=_JACKIE,
    )

    assert _bubbles_contain_cjk(output.bubbles) is False
    assert len(output.bubbles) == 1
    assert "technical hiccup" in output.bubbles[0] or "try again" in output.bubbles[0]
    assert llm.messages.create.await_count == 2


# ---------------------------------------------------------------------------
# Gating — must NEVER trigger for language="yue" (Chloe) or profile=None
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_chloe_yue_profile_is_never_cjk_scrubbed() -> None:
    """Chloe (language='yue') MUST keep Cantonese output untouched — the
    English-enforcement code path must not fire for a non-English profile."""
    outputs, decision, user_message = _faq_answer_scenario()
    cantonese_bubbles = ["好呀，我明白你嘅意思 😊", "呢個情況好常見㗎"]
    llm = _mock_llm(_bubbles_json(cantonese_bubbles))
    writer = WriterAgent(llm)

    output, _usage = await writer.compose(
        user=_user(),
        user_message=user_message,
        planner_decision=decision,
        specialist_outputs=outputs,
        profile=_CHLOE,
    )

    assert output.bubbles == cantonese_bubbles  # unchanged, Chinese kept
    # Only 1 LLM call — no retry attempted for a Cantonese persona.
    assert llm.messages.create.await_count == 1


@pytest.mark.asyncio
async def test_default_jessica_profile_is_never_cjk_scrubbed() -> None:
    """profile=None (the live WhatsApp default) must be completely
    unaffected by the new enforcement code — Jessica's Cantonese output
    is expected and must pass through untouched."""
    outputs, decision, user_message = _faq_answer_scenario()
    cantonese_bubbles = ["好呀，我明白你嘅意思 😊"]
    llm = _mock_llm(_bubbles_json(cantonese_bubbles))
    writer = WriterAgent(llm)

    output, _usage = await writer.compose(
        user=_user(),
        user_message=user_message,
        planner_decision=decision,
        specialist_outputs=outputs,
        profile=None,
    )

    assert output.bubbles == cantonese_bubbles
    assert llm.messages.create.await_count == 1
