"""Tests for the pure validation in publish_schedule.py.

No Notion/HTTP I/O here — consistent with this folder's existing
studio/scripts/test_*.py convention of only unit-testing pure,
dependency-free logic (see test_pipeline_common.py's own module
docstring). Run manually: `cd studio/dashboard && pytest test_publish_schedule.py`
— not part of the root repo's `pytest -q` (root testpaths = ["tests"] only
covers src/), same as every other studio/ test file.
"""
from __future__ import annotations

from datetime import UTC, datetime, timedelta

import pytest
from publish_schedule import InvalidPublishDate, ensure_future, validate_publish_date_iso


def test_accepts_an_explicit_offset_value():
    parsed = validate_publish_date_iso("2026-09-05T09:00:00+08:00")
    assert parsed.utcoffset() == timedelta(hours=8)


def test_accepts_a_utc_z_suffixed_value():
    parsed = validate_publish_date_iso("2026-09-05T01:00:00Z")
    assert parsed.utcoffset() == timedelta(hours=0)


def test_rejects_a_naive_value():
    with pytest.raises(InvalidPublishDate):
        validate_publish_date_iso("2026-09-05T09:00:00")


def test_rejects_garbage():
    with pytest.raises(InvalidPublishDate):
        validate_publish_date_iso("not-a-date")


def test_rejects_none():
    with pytest.raises(InvalidPublishDate):
        validate_publish_date_iso(None)


def test_does_not_reject_a_past_datetime():
    """validate_publish_date_iso() alone accepts a past value — rejecting a
    past SCHEDULE (vs "publish now") is ensure_future()'s job, called
    separately by app.py. Keeping these two checks apart lets a caller who
    genuinely wants "publish immediately, but explicitly" (rather than
    omitting the field) still express that."""
    past = (datetime.now(UTC) - timedelta(days=1)).isoformat()
    parsed = validate_publish_date_iso(past)
    assert parsed is not None


# --------------------------------------------------------------- ensure_future

def test_ensure_future_accepts_a_future_datetime():
    now = datetime(2026, 9, 1, 0, 0, tzinfo=UTC)
    future = now + timedelta(hours=1)
    ensure_future(future, now=now)  # must not raise


def test_ensure_future_rejects_a_past_datetime():
    now = datetime(2026, 9, 1, 0, 0, tzinfo=UTC)
    past = now - timedelta(hours=1)
    with pytest.raises(InvalidPublishDate):
        ensure_future(past, now=now)


def test_ensure_future_rejects_exactly_now():
    now = datetime(2026, 9, 1, 0, 0, tzinfo=UTC)
    with pytest.raises(InvalidPublishDate):
        ensure_future(now, now=now)
