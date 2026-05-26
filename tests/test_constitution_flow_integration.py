"""End-to-end constitution flow integration tests (no API key required).

These tests cover the bugs found by the QA dry-run (2026-05-26):

1. After Phase 4 declare, the ConstitutionAgent persists a TongueRecord
   so future re-uploads route to TONGUE_PROGRESS.
2. temp_state's constitution_* keys are cleared after declare so the
   user can't be re-declared in a loop.
3. The planner rule for tongue photos covers the legacy
   constitution_done + empty tongue_photos case (catch-all to constitution).

We mock the vision LLM at the agent level and verify the
ConstitutionAgent's diff propagates correctly through
``_apply_specialist_diffs`` to the User.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any
from unittest.mock import AsyncMock, MagicMock

import pytest

from src.agents.base import (
    PlannerDecision,
    SpecialistInput,
    SpecialistName,
    SpecialistOutput,
)
from src.agents.constitution_agent import (
    MAX_MCQ,
    ConstitutionAgent,
)
from src.agents.planner import _rule_overrides
from src.crm.models import Constitution, TongueRecord, User, UserStatus
from src.orchestrator.pipeline import _apply_specialist_diffs


def _vision_response(json_text: str) -> MagicMock:
    resp = MagicMock()
    resp.content = [MagicMock(type="text", text=json_text)]
    resp.usage = MagicMock(input_tokens=100, output_tokens=40)
    return resp


def _mock_client_with_vision(json_text: str) -> MagicMock:
    client = MagicMock()
    client.messages = MagicMock()
    client.messages.create = AsyncMock(
        return_value=_vision_response(json_text)
    )
    return client


# ---------------------------------------------------------------------------
# Full constitution flow (vision → 4 MCQs → declare)
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_full_flow_declares_and_persists_tongue_record() -> None:
    """Walk a fresh user through Phase 2 → 4 with mocked vision, then
    apply specialist diffs and verify the User after the turn carries
    a constitution + a TongueRecord."""
    vision_json = (
        '{"is_tongue_photo": true, "colour": "pale", '
        '"shape": "tooth_marks", "coating": "thin_white", '
        '"moisture": "normal", "notes": "舌淡、苔薄白、有齒痕"}'
    )
    client = _mock_client_with_vision(vision_json)
    agent = ConstitutionAgent(client=client)

    user = User(phone="+85291234567")

    # T1 — tongue upload triggers vision + asks Q1.
    inp = SpecialistInput(
        user=user,
        user_message="脷相",
        media_urls=["https://x/img.jpg"],
    )
    out, _ = await agent.run(inp)
    assert out.payload["phase"] == "asking_mcq"
    assert out.payload["q_index"] == 0

    user = _apply_specialist_diffs(user, [out])
    # Findings + photo URL must be in temp_state now
    assert "constitution_tongue_findings" in user.temp_state
    assert (
        user.temp_state["constitution_tongue_photo_url"] == "https://x/img.jpg"
    )

    # T2..T5 — answer A, C, B, D
    for i, letter in enumerate(["A", "C", "B", "D"]):
        inp = SpecialistInput(user=user, user_message=letter)
        out, _ = await agent.run(inp)
        user = _apply_specialist_diffs(user, [out])

    # After Q4 → declare
    assert out.payload["phase"] == "declaring"
    assert user.constitution != Constitution.UNKNOWN
    assert user.status == UserStatus.CONSTITUTION_DONE

    # TongueRecord persisted via _append
    assert len(user.tongue_photos) == 1
    rec = user.tongue_photos[0]
    assert rec.photo_url == "https://x/img.jpg"
    assert rec.tongue_colour  # mapped from "pale" → "淡白"
    assert rec.teeth_marks is True
    assert rec.constitution_at_time == user.constitution.value

    # temp_state cleared
    assert "constitution_tongue_findings" not in user.temp_state
    assert "constitution_mcq_answers" not in user.temp_state
    assert "constitution_tongue_photo_url" not in user.temp_state


# ---------------------------------------------------------------------------
# Re-upload after constitution_done routes correctly
# ---------------------------------------------------------------------------


def test_reupload_after_full_flow_routes_to_tongue_progress() -> None:
    """Once a user has constitution_done + 1 TongueRecord (the state
    the integration test above leaves them in), the planner must route
    new tongue uploads to TONGUE_PROGRESS, not CONSTITUTION."""
    record = TongueRecord(
        photo_url="https://x/old.jpg",
        captured_at=datetime(2026, 5, 1),
        tongue_colour="淡白",
        coating_colour="白",
        coating_thickness="薄",
        coating_moisture="潤",
        body_shape="正常",
        teeth_marks=True,
        cracks=False,
        raw_analysis="舌淡白",
        constitution_at_time="氣虛質",
    )
    user = User(
        phone="+85291234567",
        status=UserStatus.CONSTITUTION_DONE,
        constitution=Constitution.QIXU,
        tongue_photos=[record],
    )
    decision = _rule_overrides(user, "再睇下", ["https://x/new.jpg"])
    assert decision is not None
    assert decision.specialists == [SpecialistName.TONGUE_PROGRESS]


def test_reupload_with_constitution_done_but_no_tongue_photos_routes_to_constitution() -> None:
    """Legacy users with status=CONSTITUTION_DONE but empty tongue_photos
    (created before the tongue persistence fix shipped) must NOT fall
    through to the LLM planner — they should route to CONSTITUTION as a
    fresh re-diagnosis."""
    user = User(
        phone="+85291234567",
        status=UserStatus.CONSTITUTION_DONE,
        constitution=Constitution.PINGHE,
        tongue_photos=[],
    )
    decision = _rule_overrides(user, "再睇下", ["https://x/img.jpg"])
    assert decision is not None
    assert decision.specialists == [SpecialistName.CONSTITUTION]


# ---------------------------------------------------------------------------
# Phase 4 idempotence — second turn at declare must not re-declare
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_post_declare_user_is_not_re_declared() -> None:
    """After declare, the user's temp_state has been cleared. If the
    planner mistakenly routes the next turn back to constitution (e.g.
    because the user uploaded a SECOND tongue photo without prior
    history), the agent must enter Phase 2 (vision) — not re-fire Phase
    4 with stale data."""
    vision_json = (
        '{"is_tongue_photo": true, "colour": "pink", '
        '"shape": "normal", "coating": "thin_white", '
        '"moisture": "normal", "notes": "second photo"}'
    )
    client = _mock_client_with_vision(vision_json)
    agent = ConstitutionAgent(client=client)

    # Simulate post-declare user: constitution set, status done,
    # temp_state cleared (per the Phase 4 fix).
    user = User(
        phone="+85291234567",
        status=UserStatus.CONSTITUTION_DONE,
        constitution=Constitution.PINGHE,
        temp_state={},
    )

    # Second tongue upload (planner would actually route to
    # TONGUE_PROGRESS here, but verify the agent itself behaves sanely
    # if dispatched).
    inp = SpecialistInput(
        user=user,
        user_message="另一張",
        media_urls=["https://x/2.jpg"],
    )
    out, _ = await agent.run(inp)

    # Should start over at Phase 2 → MCQ Q0, NOT re-declare.
    assert out.payload["phase"] == "asking_mcq"
    assert out.payload["q_index"] == 0
    # Should NOT carry a `declaring` constitution diff.
    assert "constitution" not in out.suggested_user_state_diff


# ---------------------------------------------------------------------------
# Invalid tongue — no persistence
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_invalid_tongue_does_not_persist_photo_url() -> None:
    """When vision returns is_tongue_photo=False, neither findings nor
    photo URL may be persisted to temp_state."""
    vision_json = (
        '{"is_tongue_photo": false, "colour": "unknown", '
        '"shape": "unknown", "coating": "unknown", '
        '"moisture": "unknown", "notes": "唔似脷相"}'
    )
    client = _mock_client_with_vision(vision_json)
    agent = ConstitutionAgent(client=client)
    user = User(phone="+85291234567")

    inp = SpecialistInput(
        user=user,
        user_message="睇下我張相",
        media_urls=["https://x/not_a_tongue.png"],
    )
    out, _ = await agent.run(inp)

    assert out.payload["phase"] == "asking_tongue"
    assert out.payload["retry"] is True
    assert "temp_state" not in out.suggested_user_state_diff


# ---------------------------------------------------------------------------
# Vision JSON parse failure — graceful fallback
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_vision_returns_garbage_does_not_crash() -> None:
    """Vision LLM returns non-JSON text → agent recovers with neutral
    findings, asks user to re-upload."""
    client = _mock_client_with_vision("blah blah no json here")
    agent = ConstitutionAgent(client=client)
    user = User(phone="+85291234567")

    inp = SpecialistInput(
        user=user,
        user_message="脷",
        media_urls=["https://x/img.jpg"],
    )
    out, _ = await agent.run(inp)

    # Neutral findings have is_tongue_photo=False → retry.
    assert out.payload["phase"] == "asking_tongue"
    assert out.payload["retry"] is True


# ---------------------------------------------------------------------------
# Vision API exception — graceful fallback
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_vision_api_exception_does_not_crash() -> None:
    """Vision call raises → agent returns retry, no temp_state writes."""
    client = MagicMock()
    client.messages = MagicMock()
    client.messages.create = AsyncMock(side_effect=RuntimeError("vision down"))
    agent = ConstitutionAgent(client=client)
    user = User(phone="+85291234567")

    inp = SpecialistInput(
        user=user,
        user_message="脷",
        media_urls=["https://x/img.jpg"],
    )
    out, _ = await agent.run(inp)

    assert out.payload["phase"] == "asking_tongue"
    assert out.payload["retry"] is True
    assert "temp_state" not in out.suggested_user_state_diff
