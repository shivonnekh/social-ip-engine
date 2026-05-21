"""Tests for the new probabilistic constitution ranking."""

from __future__ import annotations

from src.agents.constitution_agent import _rank_constitutions
from src.crm.models import Constitution


def test_rank_returns_top3_with_percentages_summing_close_to_100() -> None:
    answers = [
        {"points": {"氣虛質": 3}},
        {"points": {"陽虛質": 3}},
        {"points": {"陽虛質": 2, "氣虛質": 1}},
    ]
    ranked, conf = _rank_constitutions({"colour": "pale"}, answers)
    assert 1 <= len(ranked) <= 3
    total = sum(r["percent"] for r in ranked)
    assert 95 <= total <= 100


def test_clear_winner_has_high_confidence() -> None:
    answers = [
        {"points": {"氣虛質": 5}},
        {"points": {"氣虛質": 5}},
        {"points": {"氣虛質": 5}},
        {"points": {"氣虛質": 5}},
    ]
    ranked, conf = _rank_constitutions({}, answers)
    assert ranked[0]["constitution"] == Constitution.QIXU.value
    assert ranked[0]["percent"] >= 80
    assert conf >= 0.6


def test_tied_top_two_has_low_confidence() -> None:
    answers = [
        {"points": {"氣虛質": 3, "陽虛質": 3}},
        {"points": {"氣虛質": 3, "陽虛質": 3}},
    ]
    ranked, conf = _rank_constitutions({}, answers)
    # tie → both near 50%
    top_two = ranked[:2]
    assert abs(top_two[0]["percent"] - top_two[1]["percent"]) <= 10
    # tie + only 2 answers → low confidence
    assert conf < 0.5


def test_zero_signal_returns_low_confidence_default() -> None:
    ranked, conf = _rank_constitutions({}, [])
    assert ranked[0]["constitution"] == Constitution.PINGHE.value
    assert conf < 0.3


def test_more_answers_higher_confidence() -> None:
    """All else equal, more MCQ data → higher confidence."""
    one_answer = [{"points": {"氣虛質": 3}}]
    four_answers = one_answer * 4
    _, c1 = _rank_constitutions({}, one_answer)
    _, c4 = _rank_constitutions({}, four_answers)
    assert c4 > c1
