"""Pins the "single shared timezone constant, no drift" contract for the
Publish Date gate. See ``src/_publish_tz.py`` for the full reasoning.

If ``notion_publish.py``, ``notion_publish_carousel.py``, or
``notion_publish_scheduler.py`` ever goes back to defining its own local
``_PUBLISH_TZ``/``_HKT`` constant instead of importing ``PUBLISH_TZ``,
these tests catch the ``is``-identity break even though the numeric offset
would still happen to match (both zones are UTC+8, no DST) — the point is
preventing MULTIPLE COPIES of the same assumption from being able to
silently disagree, not just "the offset is currently right."
"""
from __future__ import annotations

from datetime import datetime, timedelta

from src import notion_publish, notion_publish_carousel, notion_publish_scheduler
from src._publish_tz import PUBLISH_TZ


def test_publish_tz_is_kuala_lumpur():
    assert PUBLISH_TZ.key == "Asia/Kuala_Lumpur"


def test_publish_tz_is_fixed_utc_plus_8_no_dst():
    winter = datetime(2026, 1, 1, tzinfo=PUBLISH_TZ)
    summer = datetime(2026, 7, 1, tzinfo=PUBLISH_TZ)
    assert winter.utcoffset() == timedelta(hours=8)
    assert summer.utcoffset() == timedelta(hours=8)


def test_notion_publish_uses_the_shared_constant():
    assert notion_publish._PUBLISH_TZ is PUBLISH_TZ


def test_notion_publish_carousel_uses_the_shared_constant():
    assert notion_publish_carousel._PUBLISH_TZ is PUBLISH_TZ


def test_notion_publish_scheduler_uses_the_shared_constant():
    """Third copy, found in review (2026-09-01) — the first pass of this
    fix only touched notion_publish.py / notion_publish_carousel.py and
    missed that the scheduler sweep had its OWN independent
    ZoneInfo("Asia/Hong_Kong") for the daily-fixed-hour wait-time math."""
    assert notion_publish_scheduler._PUBLISH_TZ is PUBLISH_TZ
