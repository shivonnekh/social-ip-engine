"""Tests for ClinicMatcher — pure function, no network."""

from __future__ import annotations

from datetime import datetime

import pytest

from src.tools.clinic_matcher import ClinicMatcher


@pytest.fixture(scope="module")
def matcher() -> ClinicMatcher:
    return ClinicMatcher()


def test_exact_district_match(matcher: ClinicMatcher) -> None:
    result = matcher.match("沙田")
    assert result.clinic["id"] == "careplus_shatin"
    assert result.match_reason == "exact"


def test_exact_match_maanshan(matcher: ClinicMatcher) -> None:
    result = matcher.match("馬鞍山")
    assert result.clinic["id"] == "careplus_maanshan"
    assert result.match_reason == "exact"


def test_adjacency_match_kowloon_to_shatin(matcher: ClinicMatcher) -> None:
    """旺角 has no clinic → should route to 沙田."""
    result = matcher.match("旺角")
    assert result.clinic["id"] == "careplus_shatin"
    assert result.match_reason == "adjacent"


def test_adjacency_match_seungkwanO_prefers_maanshan(matcher: ClinicMatcher) -> None:
    """將軍澳 adjacency is [馬鞍山, 沙田] — should prefer 馬鞍山."""
    # Use a weekday when 馬鞍山 is open (Mon)
    monday = datetime(2026, 5, 25, 10, 0)  # Mon
    result = matcher.match("將軍澳", when=monday)
    assert result.clinic["id"] == "careplus_maanshan"
    assert result.match_reason == "adjacent"


def test_unknown_district_fallback(matcher: ClinicMatcher) -> None:
    """An unknown district should fall back to first OPEN clinic."""
    monday = datetime(2026, 5, 25, 10, 0)  # Mon — both open
    result = matcher.match("月球", when=monday)
    assert result.match_reason == "fallback"
    assert result.open_today is True


def test_empty_district_fallback(matcher: ClinicMatcher) -> None:
    result = matcher.match(None)
    assert result.match_reason == "fallback"


def test_open_today_wed_closes_maanshan(matcher: ClinicMatcher) -> None:
    """馬鞍山 is closed Wed — open_today should be False."""
    wed = datetime(2026, 5, 27, 10, 0)  # Wed
    result = matcher.match("馬鞍山", when=wed)
    assert result.clinic["id"] == "careplus_maanshan"
    assert result.open_today is False
    assert result.today_hours is None


def test_open_today_shatin_sunday(matcher: ClinicMatcher) -> None:
    """沙田 is open 7 days."""
    sun = datetime(2026, 5, 24, 10, 0)  # Sun
    result = matcher.match("沙田", when=sun)
    assert result.open_today is True
    assert result.today_hours is not None
