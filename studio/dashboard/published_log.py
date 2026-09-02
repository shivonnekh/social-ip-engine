"""published_log.py — pure event-shaping over the studio publish ledgers,
for the dashboard's Calendar view (state.py's published_events() reads the
three ledger JSON files and calls build_events() below to shape them).

No Notion/HTTP/filesystem I/O here — same separation as publish_schedule.py
(state.py/app.py own I/O, this module is pure and unit-testable).

WHY THE LEDGERS, NOT NOTION'S "Publish Date" PROPERTY
-------------------------------------------------------
A row published immediately (the common case) has its Notion "Publish Date"
property explicitly CLEARED by state.set_stage_with_publish_date() — that
property only ever holds a FUTURE schedule, never a record of when a row
actually went live. The three JSON ledgers under data/channels/ (written by
src/notion_publish*.py, git-committed for durability) are the only place
that records the real "went live at" instant, so they're what the calendar
reads from.

WHY Asia/Kuala_Lumpur IS HARDCODED HERE, NOT IMPORTED FROM src/_publish_tz
-----------------------------------------------------------------------------
studio/ is deliberately standalone from src/ (see studio/CLAUDE.md — no
existing studio file imports `from src...`; publish_schedule.py/.js already
duplicate this same +08:00/Asia-Kuala_Lumpur assumption rather than reach
across that boundary). Keeping the duplication here matches that existing
convention instead of introducing the first cross-boundary import.
"""
from __future__ import annotations

from datetime import datetime
from typing import Any
from zoneinfo import ZoneInfo

_MYT = ZoneInfo("Asia/Kuala_Lumpur")

_CHANNEL_LEDGERS = ("instagram", "facebook")  # carousel_ig, carousel_fb order


def _parse_updated_at(value: Any) -> datetime | None:
    if not isinstance(value, str) or not value:
        return None
    try:
        parsed = datetime.fromisoformat(value)
    except ValueError:
        return None
    if parsed.tzinfo is None:
        return None
    return parsed


def _row_label(row_id: str, row_meta: dict[str, dict]) -> tuple[str, str]:
    meta = row_meta.get(row_id) or {}
    name = meta.get("name") or f"(row {row_id[:8]})"
    title = meta.get("title") or ""
    return name, title


def _reel_events(reel_ledger: dict, row_meta: dict[str, dict]) -> list[dict]:
    events = []
    for row_id, entry in reel_ledger.items():
        if entry.get("status") != "published":
            continue
        published_at = _parse_updated_at(entry.get("updated_at"))
        if published_at is None:
            continue
        name, title = _row_label(row_id, row_meta)
        events.append({
            "row_id": row_id,
            "name": name,
            "title": title,
            "format": "reel",
            "channels": ["instagram"],
            "status": "published",
            "published_at": published_at.isoformat(),
            "date": published_at.astimezone(_MYT).date().isoformat(),
        })
    return events


def _carousel_events(carousel_ig: dict, carousel_fb: dict, row_meta: dict[str, dict]) -> list[dict]:
    row_ids = {
        row_id
        for ledger in (carousel_ig, carousel_fb)
        for row_id, entry in ledger.items()
        if entry.get("status") == "published"
    }
    events = []
    for row_id in row_ids:
        timestamps: dict[str, datetime] = {}
        for channel, ledger in (("instagram", carousel_ig), ("facebook", carousel_fb)):
            entry = ledger.get(row_id)
            if not entry or entry.get("status") != "published":
                continue
            parsed = _parse_updated_at(entry.get("updated_at"))
            if parsed is not None:
                timestamps[channel] = parsed
        if not timestamps:
            continue
        published_at = min(timestamps.values())
        name, title = _row_label(row_id, row_meta)
        events.append({
            "row_id": row_id,
            "name": name,
            "title": title,
            "format": "carousel",
            "channels": sorted(timestamps),
            "status": "published",
            "published_at": published_at.isoformat(),
            "date": published_at.astimezone(_MYT).date().isoformat(),
        })
    return events


def build_scheduled_events(
    candidates: list[dict],
    already_published_row_ids: dict[str, set[str]],
) -> list[dict]:
    """Shape "not yet live but has a Publish Date" rows into calendar events.

    `candidates`: one dict per row/format that structurally qualifies (Stage
    already flipped to Published + a Publish Date is set) —
    {"row_id", "name", "title", "format": "reel"|"carousel", "channels",
    "publish_date": iso-string-or-None}. state.py builds this list since it
    owns the Notion Stage constants; this function stays Notion-agnostic.

    `already_published_row_ids`: {"reel": {row_id, ...}, "carousel": {...}}
    — a candidate whose row_id is already in the matching set is skipped.
    This is the one thing that actually matters here: Notion's Publish Date
    property is NEVER cleared after a scheduled post actually goes live (see
    module docstring for why it's cleared on an IMMEDIATE publish but not
    this case), so without this exclusion every already-published scheduled
    post would show twice — once correctly from the ledger, once stale here.

    Returns events with status="scheduled" and published_at=None (nothing
    to sort a "hasn't happened yet" event by other than its target date).
    """
    events = []
    for c in candidates:
        if c["row_id"] in already_published_row_ids.get(c["format"], ()):
            continue
        target = _parse_updated_at(c.get("publish_date"))
        if target is None:
            continue
        events.append({
            "row_id": c["row_id"],
            "name": c["name"],
            "title": c["title"],
            "format": c["format"],
            "channels": c["channels"],
            "status": "scheduled",
            "published_at": None,
            "date": target.astimezone(_MYT).date().isoformat(),
        })
    return events


def build_events(
    reel_ledger: dict,
    carousel_ig_ledger: dict,
    carousel_fb_ledger: dict,
    row_meta: dict[str, dict],
) -> list[dict]:
    """Shape the three raw publish ledgers into calendar-ready events.

    Each dict maps row_id -> ledger entry (as stored on disk). `row_meta`
    maps row_id -> {"name": ..., "title": ...} for display, e.g. built from
    a fresh Production Tracker query — a row_id with no entry there (an
    archived/deleted row) still gets an event, just with a generic name.

    Returns events sorted by `published_at` ascending.
    """
    events = _reel_events(reel_ledger, row_meta)
    events += _carousel_events(carousel_ig_ledger, carousel_fb_ledger, row_meta)
    events.sort(key=lambda e: e["published_at"])
    return events
