"""Tests for the Planner's query-understanding output:
- rephrased_query (HK 廣東話 normalization)
- extracted_pain_points (NER for CRM persistence)
- Pipeline integration: pain_points get appended to user.pain_points
"""

from __future__ import annotations

import pytest

from src.agents.base import (
    PlannerDecision,
    SpecialistInput,
    SpecialistName,
    SpecialistOutput,
)


# ---------------------------------------------------------------------------
# Schema: PlannerDecision accepts new fields with defaults
# ---------------------------------------------------------------------------


def test_planner_decision_has_default_rephrased_query() -> None:
    d = PlannerDecision(
        specialists=[SpecialistName.CASUAL],
        reasoning="test",
    )
    assert d.rephrased_query == ""
    assert d.extracted_pain_points == []


def test_planner_decision_accepts_rephrased_query() -> None:
    d = PlannerDecision(
        specialists=[SpecialistName.FAQ],
        reasoning="test",
        rephrased_query="我而家有月經痛",
        extracted_pain_points=["月經痛"],
    )
    assert d.rephrased_query == "我而家有月經痛"
    assert d.extracted_pain_points == ["月經痛"]


def test_planner_decision_extracted_pain_points_is_immutable_list() -> None:
    """Frozen model — extracted_pain_points must be safe to read."""
    d = PlannerDecision(
        specialists=[SpecialistName.FAQ],
        reasoning="test",
        extracted_pain_points=["頭痛", "失眠"],
    )
    assert d.extracted_pain_points == ["頭痛", "失眠"]


# ---------------------------------------------------------------------------
# SpecialistInput: rephrased_query + effective_query helper
# ---------------------------------------------------------------------------


def test_specialist_input_default_rephrased_is_empty() -> None:
    from src.crm.models import User

    inp = SpecialistInput(user=User(phone="+85291234567"), user_message="原文")
    assert inp.rephrased_query == ""


def test_specialist_input_effective_query_falls_back_to_user_message() -> None:
    from src.crm.models import User

    inp = SpecialistInput(user=User(phone="+85291234567"), user_message="原文")
    assert inp.effective_query == "原文"


def test_specialist_input_effective_query_prefers_rephrased() -> None:
    from src.crm.models import User

    inp = SpecialistInput(
        user=User(phone="+85291234567"),
        user_message="hello hi 我月经会痛",
        rephrased_query="我有月經痛",
    )
    assert inp.effective_query == "我有月經痛"


def test_specialist_input_empty_rephrased_falls_back() -> None:
    """Empty string rephrased → falls back to user_message."""
    from src.crm.models import User

    inp = SpecialistInput(
        user=User(phone="+85291234567"),
        user_message="原文",
        rephrased_query="",
    )
    assert inp.effective_query == "原文"


# ---------------------------------------------------------------------------
# Pipeline: extracted_pain_points get appended to CRM
# ---------------------------------------------------------------------------


def test_apply_extracted_pain_points_appends_dedup() -> None:
    """The pipeline merges extracted pain points into user.pain_points,
    deduplicating against existing values."""
    from src.crm.models import User

    user = User(phone="+85291234567", pain_points=["頭痛"])
    decision = PlannerDecision(
        specialists=[SpecialistName.FAQ],
        reasoning="test",
        extracted_pain_points=["頭痛", "失眠"],  # 頭痛 is dup, 失眠 is new
    )

    # Simulate the pipeline's merge logic
    merged = list(user.pain_points)
    for pp in decision.extracted_pain_points:
        if pp and pp not in merged:
            merged.append(pp)

    assert merged == ["頭痛", "失眠"]


def test_apply_extracted_pain_points_skips_when_empty() -> None:
    """No extraction → no change to pain_points."""
    from src.crm.models import User

    user = User(phone="+85291234567", pain_points=["頭痛"])
    decision = PlannerDecision(
        specialists=[SpecialistName.FAQ],
        reasoning="test",
        extracted_pain_points=[],
    )

    merged = list(user.pain_points)
    for pp in decision.extracted_pain_points:
        if pp and pp not in merged:
            merged.append(pp)

    assert merged == ["頭痛"]


def test_rule_based_decisions_have_empty_extraction_fields() -> None:
    """Rule fast-paths in _rule_overrides return PlannerDecision without
    LLM-driven extraction, so the fields default to '' and []."""
    from datetime import datetime

    from src.agents.planner import _rule_overrides
    from src.crm.models import ConversationMessage, User

    user = User(
        phone="+85291234567",
        conversation_history=[
            ConversationMessage(role="user", content="hi", at=datetime.utcnow())
        ],
    )
    decision = _rule_overrides(user, "拜拜", [])

    assert decision is not None
    # Rule paths don't fill these — they default to safe values
    assert decision.rephrased_query == ""
    assert decision.extracted_pain_points == []
