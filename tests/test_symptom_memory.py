"""Tests for symptom memory — recurring symptom detection."""
from __future__ import annotations

import pytest
from datetime import datetime, timezone

from src.agents.symptom_memory import extract_symptom_from_text, detect_recurring_symptom
from src.crm.models import User, ConversationMessage, UserStatus

UTC = timezone.utc


def _msg(role: str, content: str) -> ConversationMessage:
    return ConversationMessage(role=role, content=content, at=datetime.now(UTC))


# ---------------------------------------------------------------------------
# Tests for extract_symptom_from_text
# ---------------------------------------------------------------------------


def test_detects_headache():
    assert extract_symptom_from_text("頭好痛") == "頭痛"


def test_detects_insomnia():
    assert extract_symptom_from_text("最近失眠好嚴重") == "失眠"


def test_detects_fatigue():
    assert extract_symptom_from_text("好攰，無氣力") == "疲勞"


def test_detects_stomach():
    assert extract_symptom_from_text("肚脹，消化差") == "胃痛/消化差"


def test_returns_none_for_no_match():
    assert extract_symptom_from_text("你好") is None


def test_returns_none_for_empty():
    assert extract_symptom_from_text("") is None


def test_first_match_wins():
    # "頭痛" group (index 0) comes before "失眠" group (index 1) in _SYMPTOM_GROUPS.
    # A message containing both should return "頭痛".
    result = extract_symptom_from_text("頭痛，仲失眠")
    assert result == "頭痛"


# ---------------------------------------------------------------------------
# Tests for detect_recurring_symptom
# ---------------------------------------------------------------------------


def test_returns_none_when_no_history():
    user = User(phone="+85291234567")
    assert detect_recurring_symptom(user) is None


def test_returns_none_below_threshold():
    # "頭好痛" appears only twice — threshold=3 not met.
    history = [_msg("user", "頭好痛")] * 2
    user = User(phone="+85291234567", conversation_history=history)
    assert detect_recurring_symptom(user, threshold=3) is None


def test_detects_at_threshold():
    # "失眠" appears exactly 3 times — exactly at threshold.
    history = [_msg("user", "最近失眠好嚴重")] * 3
    user = User(phone="+85291234567", conversation_history=history)
    assert detect_recurring_symptom(user, threshold=3) == "失眠"


def test_ignores_jessica_messages():
    # Symptom keyword appears 3x but only in Jessica's messages — should NOT count.
    history = [_msg("jessica", "你係咪有頭痛？")] * 3
    user = User(phone="+85291234567", conversation_history=history)
    assert detect_recurring_symptom(user, threshold=3) is None


def test_uses_last_window_messages():
    # 15 messages total: first 5 have 頭痛, last 10 have 失眠.
    # With window=10, only the last 10 (失眠) count → returns 失眠.
    early = [_msg("user", "頭好痛")] * 5
    recent = [_msg("user", "失眠好辛苦，唔夠瞓")] * 10
    history = early + recent
    user = User(phone="+85291234567", conversation_history=history)
    # window=10: only the last 10 messages (all 失眠) are scanned.
    assert detect_recurring_symptom(user, window=10, threshold=3) == "失眠"


def test_returns_most_frequent():
    # 頭痛 appears 4x, 失眠 appears 3x → returns 頭痛.
    history = (
        [_msg("user", "頭好痛")] * 4
        + [_msg("user", "失眠好辛苦")] * 3
    )
    user = User(phone="+85291234567", conversation_history=history)
    assert detect_recurring_symptom(user, threshold=3) == "頭痛"


def test_pain_points_breaks_tie():
    # 頭痛 and 失眠 both appear 3x (tied). 失眠 is in pain_points → 失眠 wins.
    history = (
        [_msg("user", "頭好痛")] * 3
        + [_msg("user", "失眠好辛苦")] * 3
    )
    user = User(
        phone="+85291234567",
        conversation_history=history,
        pain_points=["失眠"],
    )
    assert detect_recurring_symptom(user, threshold=3) == "失眠"


# ---------------------------------------------------------------------------
# Tests for planner integration
# ---------------------------------------------------------------------------


def test_planner_fires_on_recurring_symptom():
    """When user history has 3+ instances of same symptom and no other rule fires,
    planner routes to [CASUAL, FAQ] with symptom in notes."""
    from src.agents.planner import _rule_overrides
    from src.agents.base import SpecialistName

    history = [_msg("user", "最近頭好痛")] * 4  # 4x headache
    user = User(
        phone="+85291234567",
        status=UserStatus.QUALIFIED,
        conversation_history=history,
    )
    # Use a truly neutral message that doesn't match any earlier rule.
    # "你好" would be caught by the "repeat hi" rule before symptom memory runs.
    decision = _rule_overrides(user, "係咁㗎", [])
    assert decision is not None
    assert SpecialistName.CASUAL in decision.specialists
    assert SpecialistName.FAQ in decision.specialists
    assert "頭痛" in decision.notes_for_writer


def test_planner_does_not_fire_below_threshold():
    """Only 2x headache — below threshold of 3 — planner returns None."""
    from src.agents.planner import _rule_overrides

    history = [_msg("user", "頭好痛")] * 2
    user = User(
        phone="+85291234567",
        status=UserStatus.QUALIFIED,
        conversation_history=history,
    )
    # Use a truly neutral message that doesn't match any earlier rule.
    decision = _rule_overrides(user, "係咁㗎", [])
    # Should fall through to None (LLM handles it)
    assert decision is None


def test_planner_symptom_memory_does_not_fire_when_other_rule_fires():
    """If another rule fires (e.g. first-touch hi), symptom memory is irrelevant."""
    from src.agents.planner import _rule_overrides
    from src.agents.base import SpecialistName

    history = [_msg("user", "頭好痛")] * 5
    user = User(
        phone="+85291234567",
        status=UserStatus.NEW,
        conversation_history=[],  # first-touch
    )
    decision = _rule_overrides(user, "hi", [])
    # first-touch hi → GREETING, not symptom memory
    assert decision is not None
    assert SpecialistName.GREETING in decision.specialists
