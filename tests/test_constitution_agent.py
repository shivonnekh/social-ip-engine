"""Constitution Agent tests — offline (no LLM)."""

from __future__ import annotations

import pytest

from src.agents.base import SpecialistInput, SpecialistName
from src.agents.constitution_agent import (
    MAX_MCQ,
    MCQS,
    ConstitutionAgent,
    _record_previous_answer,
    _score_constitution,
)
from src.crm.models import Constitution, User, UserStatus


@pytest.fixture
def agent() -> ConstitutionAgent:
    return ConstitutionAgent(client=None)  # offline


@pytest.fixture
def fresh_user() -> User:
    return User(phone="+85291234567")


# ── Phase 1: ask_tongue when nothing started ─────────────────────────


@pytest.mark.asyncio
async def test_phase1_asks_tongue_when_no_media_no_findings(
    agent: ConstitutionAgent, fresh_user: User
) -> None:
    inp = SpecialistInput(user=fresh_user, user_message="我覺得最近好攰")
    out, _ = await agent.run(inp)

    assert out.specialist == SpecialistName.CONSTITUTION
    assert out.payload["phase"] == "asking_tongue"
    assert out.payload["retry"] is False


# ── Phase 2: vision (offline → neutral findings, asks tongue again) ──


@pytest.mark.asyncio
async def test_phase2_offline_returns_not_tongue(
    agent: ConstitutionAgent, fresh_user: User
) -> None:
    """In offline mode, vision returns is_tongue_photo=False → retry."""
    inp = SpecialistInput(
        user=fresh_user, user_message="", media_urls=["https://example.test/img.jpg"]
    )
    out, _ = await agent.run(inp)

    # Vision didn't really run → findings.is_tongue_photo=False → retry
    assert out.payload["phase"] == "asking_tongue"
    assert out.payload["retry"] is True
    # Vision attempt logged
    assert any(t["name"] == "claude_vision.analyze_tongue" for t in out.tools_called)
    # Findings saved to temp_state diff
    assert "temp_state" in out.suggested_user_state_diff


# ── Phase 3: ask MCQ after tongue findings stored ────────────────────


@pytest.mark.asyncio
async def test_phase3_asks_first_mcq_when_findings_present(
    agent: ConstitutionAgent,
) -> None:
    user = User(
        phone="+85291234567",
        temp_state={
            "constitution_tongue_findings": {
                "is_tongue_photo": True,
                "colour": "pale",
                "coating": "thin_white",
                "shape": "tooth_marks",
                "moisture": "normal",
                "notes": "",
            }
        },
    )
    inp = SpecialistInput(user=user, user_message="")
    out, _ = await agent.run(inp)

    assert out.payload["phase"] == "asking_mcq"
    assert out.payload["q_index"] == 0
    assert out.payload["q_total"] == MAX_MCQ
    assert len(out.payload["options"]) == 4


@pytest.mark.asyncio
async def test_phase3_records_answer_and_advances(agent: ConstitutionAgent) -> None:
    user = User(
        phone="+85291234567",
        temp_state={
            "constitution_tongue_findings": {"is_tongue_photo": True, "colour": "pale"},
            "constitution_mcq_index": 1,  # we just asked Q0 last turn
            "constitution_mcq_answers": [],
        },
    )
    # User picks option "C" (often tired) on Q0
    inp = SpecialistInput(user=user, user_message="C")
    out, _ = await agent.run(inp)

    # Should advance to Q1
    assert out.payload["phase"] == "asking_mcq"
    assert out.payload["q_index"] == 1
    # Answer recorded in suggested temp_state
    ts_diff = out.suggested_user_state_diff["temp_state"]
    assert len(ts_diff["constitution_mcq_answers"]) == 1
    assert ts_diff["constitution_mcq_answers"][0]["chosen_id"] == "C"


@pytest.mark.asyncio
async def test_phase3_handles_label_match(agent: ConstitutionAgent) -> None:
    """User types the answer label instead of a letter."""
    user = User(
        phone="+85291234567",
        temp_state={
            "constitution_tongue_findings": {"is_tongue_photo": True, "colour": "pale"},
            "constitution_mcq_index": 1,
            "constitution_mcq_answers": [],
        },
    )
    inp = SpecialistInput(user=user, user_message="成日攰、講嘢冇力 啊")
    out, _ = await agent.run(inp)

    ts_diff = out.suggested_user_state_diff["temp_state"]
    assert ts_diff["constitution_mcq_answers"][0]["chosen_id"] == "C"


@pytest.mark.asyncio
async def test_phase3_unrecognized_answer_re_asks_same_q(
    agent: ConstitutionAgent,
) -> None:
    user = User(
        phone="+85291234567",
        temp_state={
            "constitution_tongue_findings": {"is_tongue_photo": True, "colour": "pale"},
            "constitution_mcq_index": 1,
            "constitution_mcq_answers": [],
        },
    )
    inp = SpecialistInput(user=user, user_message="唔知點答")
    out, _ = await agent.run(inp)

    # Couldn't parse → answers still empty → asks Q0 again
    assert out.payload["q_index"] == 0


# ── Phase 4: declare after 4 MCQs ────────────────────────────────────


@pytest.mark.asyncio
async def test_phase4_declares_after_all_mcqs(agent: ConstitutionAgent) -> None:
    answers = [
        {"question_key": "energy", "chosen_id": "C", "label": "...", "points": {"氣虛質": 3}},
        {"question_key": "temperature", "chosen_id": "A", "label": "...", "points": {"陽虛質": 3}},
        {"question_key": "digestion", "chosen_id": "C", "label": "...", "points": {"陽虛質": 2, "氣虛質": 1}},
        {"question_key": "mood_sleep", "chosen_id": "B", "label": "...", "points": {"氣鬱質": 2, "陰虛質": 1}},
    ]
    user = User(
        phone="+85291234567",
        temp_state={
            "constitution_tongue_findings": {"is_tongue_photo": True, "colour": "pale"},
            "constitution_mcq_index": MAX_MCQ + 1,  # past the last Q
            "constitution_mcq_answers": answers,
        },
    )
    inp = SpecialistInput(user=user, user_message="(any)")
    out, _ = await agent.run(inp)

    assert out.payload["phase"] == "declaring"
    # Total: 陽虛 3+2 + ... → 陽虛 dominates
    assert out.payload["constitution"] == Constitution.YANGXU.value
    # User state should also flip
    assert out.suggested_user_state_diff["constitution"] == Constitution.YANGXU.value
    assert out.suggested_user_state_diff["status"] == UserStatus.CONSTITUTION_DONE.value
    # Card reference logged
    assert "tcm_constitution_assessment" in out.cards_used


# ── Scoring unit tests ───────────────────────────────────────────────


def test_score_purple_tongue_picks_xueyu() -> None:
    findings = {"colour": "purple"}
    c = _score_constitution(findings, [])
    assert c == Constitution.XUEYU


def test_score_no_signal_defaults_pinghe() -> None:
    c = _score_constitution({}, [])
    assert c == Constitution.PINGHE


def test_score_mixed_mcq_picks_highest() -> None:
    findings = {"colour": "pale"}  # +2 陽虛, +1 氣虛
    answers = [
        {"points": {"氣虛質": 3}},
        {"points": {"陽虛質": 3}},
        {"points": {"陽虛質": 2, "氣虛質": 1}},
    ]
    # 陽虛 = 2+3+2 = 7; 氣虛 = 1+3+1 = 5 → 陽虛 wins
    assert _score_constitution(findings, answers) == Constitution.YANGXU


# ── _record_previous_answer ──────────────────────────────────────────


def test_record_letter_A() -> None:
    out = _record_previous_answer("A", MCQS[0], [])
    assert out is not None
    assert out[0]["chosen_id"] == "A"


def test_record_letter_lowercase_with_dot() -> None:
    out = _record_previous_answer("c.", MCQS[0], [])
    assert out is not None
    assert out[0]["chosen_id"] == "C"


def test_record_garbage_returns_none() -> None:
    assert _record_previous_answer("唔知喎", MCQS[0], []) is None
