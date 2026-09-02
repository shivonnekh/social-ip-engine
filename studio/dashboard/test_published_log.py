"""Tests for the pure event-shaping logic in published_log.py — the data
behind the studio dashboard's Calendar view.

No Notion/HTTP/filesystem I/O here — same convention as
test_publish_schedule.py (see that file's module docstring). Run manually:
`cd studio/dashboard && pytest test_published_log.py`
"""
from __future__ import annotations

from published_log import build_events, build_scheduled_events


def test_published_reel_becomes_one_event():
    reel = {"row1": {"status": "published", "updated_at": "2026-08-13T05:00:00+00:00"}}
    events = build_events(reel, {}, {}, {})
    assert len(events) == 1
    assert events[0]["row_id"] == "row1"
    assert events[0]["format"] == "reel"
    assert events[0]["channels"] == ["instagram"]
    assert events[0]["status"] == "published"


def test_non_published_status_ignored():
    reel = {
        "row1": {"status": "skipped", "updated_at": "2026-08-13T05:00:00+00:00"},
        "row2": {"status": "failed", "updated_at": "2026-08-13T05:00:00+00:00"},
        "row3": {"status": "in_flight", "updated_at": "2026-08-13T05:00:00+00:00"},
    }
    assert build_events(reel, {}, {}, {}) == []


def test_entry_missing_updated_at_is_skipped_not_crashed():
    reel = {"row1": {"status": "published"}}
    assert build_events(reel, {}, {}, {}) == []


def test_entry_with_unparseable_updated_at_is_skipped_not_crashed():
    reel = {"row1": {"status": "published", "updated_at": "not-a-date"}}
    assert build_events(reel, {}, {}, {}) == []


def test_carousel_merges_ig_and_fb_entries_for_the_same_row_into_one_event():
    ig = {"row1": {"status": "published", "updated_at": "2026-08-13T10:39:17+00:00"}}
    fb = {"row1": {"status": "published", "updated_at": "2026-08-13T10:41:18+00:00"}}
    events = build_events({}, ig, fb, {})
    assert len(events) == 1
    ev = events[0]
    assert ev["format"] == "carousel"
    assert ev["channels"] == ["facebook", "instagram"]
    # earlier of the two timestamps — first channel it actually went live on
    assert ev["published_at"] == "2026-08-13T10:39:17+00:00"


def test_carousel_ig_only_reports_only_instagram():
    ig = {"row1": {"status": "published", "updated_at": "2026-08-13T10:39:17+00:00"}}
    events = build_events({}, ig, {}, {})
    assert events[0]["channels"] == ["instagram"]


def test_carousel_fb_only_reports_only_facebook():
    fb = {"row1": {"status": "published", "updated_at": "2026-08-13T10:41:18+00:00"}}
    events = build_events({}, {}, fb, {})
    assert events[0]["channels"] == ["facebook"]


def test_date_is_computed_in_asia_kuala_lumpur_not_utc():
    # 2026-08-13T20:30:00+00:00 is 2026-08-14T04:30:00+08:00 MYT — a real
    # published-late-at-night post must land on the NEXT calendar day here,
    # not the UTC day, or the calendar would show it one day early.
    reel = {"row1": {"status": "published", "updated_at": "2026-08-13T20:30:00+00:00"}}
    events = build_events(reel, {}, {}, {})
    assert events[0]["date"] == "2026-08-14"


def test_row_meta_attaches_name_and_title_when_present():
    reel = {"row1": {"status": "published", "updated_at": "2026-08-13T05:00:00+00:00"}}
    row_meta = {"row1": {"name": "Tonsil Ep 3", "title": "Sore throat? Try this"}}
    events = build_events(reel, {}, {}, row_meta)
    assert events[0]["name"] == "Tonsil Ep 3"
    assert events[0]["title"] == "Sore throat? Try this"


def test_row_meta_missing_falls_back_gracefully():
    reel = {"row1": {"status": "published", "updated_at": "2026-08-13T05:00:00+00:00"}}
    events = build_events(reel, {}, {}, {})
    assert events[0]["row_id"] == "row1"
    assert events[0]["name"]
    assert events[0]["title"] == ""


def test_events_sorted_by_published_at_ascending():
    reel = {
        "row_later": {"status": "published", "updated_at": "2026-08-14T05:00:00+00:00"},
        "row_earlier": {"status": "published", "updated_at": "2026-08-13T05:00:00+00:00"},
    }
    events = build_events(reel, {}, {}, {})
    assert [e["row_id"] for e in events] == ["row_earlier", "row_later"]


# ------------------------------------------------------------ build_scheduled_events

def _candidate(row_id="row1", fmt="reel", publish_date="2026-09-10T09:00:00+08:00"):
    return {
        "row_id": row_id, "name": "Some Row", "title": "Some Title",
        "format": fmt, "channels": ["instagram"], "publish_date": publish_date,
    }


def test_scheduled_candidate_becomes_an_event():
    events = build_scheduled_events([_candidate()], {})
    assert len(events) == 1
    ev = events[0]
    assert ev["row_id"] == "row1"
    assert ev["status"] == "scheduled"
    assert ev["published_at"] is None
    assert ev["date"] == "2026-09-10"


def test_scheduled_candidate_already_live_is_excluded():
    # Notion's Publish Date is never cleared after a SCHEDULED post actually
    # goes live (unlike an immediate publish) — without this exclusion the
    # calendar would show the same post twice.
    already = {"reel": {"row1"}}
    events = build_scheduled_events([_candidate()], already)
    assert events == []


def test_scheduled_candidate_live_under_a_different_format_still_shows():
    # "row1" already live as a reel doesn't suppress a genuinely separate
    # scheduled carousel candidate for the same row.
    already = {"reel": {"row1"}}
    events = build_scheduled_events([_candidate(fmt="carousel")], already)
    assert len(events) == 1
    assert events[0]["format"] == "carousel"


def test_scheduled_candidate_with_unparseable_date_is_skipped_not_crashed():
    events = build_scheduled_events([_candidate(publish_date="not-a-date")], {})
    assert events == []


def test_scheduled_candidate_with_no_publish_date_is_skipped():
    events = build_scheduled_events([_candidate(publish_date=None)], {})
    assert events == []
