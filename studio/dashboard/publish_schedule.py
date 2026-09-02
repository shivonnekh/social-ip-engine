"""publish_schedule.py — pure validation for a Publish Date ISO string
supplied by the studio dashboard's schedule dialog (app.py's `/api/stage`
and `/api/carousel-stage`). No Notion/HTTP I/O here — that's state.py's
job (state.set_stage_with_publish_date / set_carousel_stage_with_publish_date).

Mirrors studio/dashboard/static/publish_schedule.js's toPublishDateIso() on
the browser side: that helper always builds a string with an explicit
+08:00 (Asia/Kuala_Lumpur) offset, so a value reaching this validator
should never be naive. See src/_publish_tz.py for why Asia/Kuala_Lumpur.
"""
from __future__ import annotations

from datetime import UTC, datetime


class InvalidPublishDate(ValueError):
    """Raised when a client-supplied Publish Date ISO string is malformed
    or missing an explicit UTC offset."""


def validate_publish_date_iso(value: str) -> datetime:
    """Parse and validate an ISO 8601 Publish Date string coming from the
    studio dashboard's schedule dialog.

    Rejects (raises InvalidPublishDate):
      - a value that doesn't parse as ISO 8601 at all
      - a NAIVE value (no offset) — the browser-side helper always attaches
        one; a naive value reaching here means something bypassed the
        studio UI (a stale client, a hand-crafted request). Failing loudly
        HERE, at the point of entry, is deliberately stricter than
        src/notion_publish.py's own `_publish_date_eligible`, which fails
        OPEN (assumes MYT) for a naive value — that fallback exists for a
        human editing the Notion property directly by hand, a case where
        "silently assume MYT and still publish" is the right behaviour.
        This dashboard write path has no such excuse: it should always be
        able to send a fully-qualified value, so a naive one here is a bug
        worth surfacing rather than papering over.

    Does NOT reject a past datetime — a past-or-now value is a legitimate
    (if unusual) "publish immediately" intent; the eligibility check on the
    backend already treats it that way. The caller (app.py) is expected to
    warn the human about a suspiciously-past schedule, not this validator.
    """
    try:
        parsed = datetime.fromisoformat(value)
    except (TypeError, ValueError) as exc:
        raise InvalidPublishDate(f"unparseable publish_date {value!r}: {exc}") from exc
    if parsed.tzinfo is None:
        raise InvalidPublishDate(
            f"publish_date {value!r} has no UTC offset — the studio UI always "
            "attaches +08:00 (Asia/Kuala_Lumpur); a naive value here means "
            "something bypassed it"
        )
    return parsed


def ensure_future(parsed: datetime, *, now: datetime | None = None) -> None:
    """Raise InvalidPublishDate if `parsed` is not strictly in the future.

    Deliberately separate from validate_publish_date_iso() above: format
    validation and "is this actually a schedule" are different questions.
    Kept as a real server-side check (not just app.js's client-side
    isFuturePublishDate) because the client-side guard is trivially
    bypassable — a stale browser tab or a direct API call — and letting a
    "scheduled for later" request through with a past/now timestamp would
    silently behave as "publish immediately" once the sweep next runs
    (~every NOTION_PUBLISH_SCHEDULE_INTERVAL_S seconds), defeating the
    whole point of scheduling without any error surfaced to the caller.

    Comparison works correctly across timezones for any two AWARE
    datetimes (Python compares by absolute instant, not wall-clock digits)
    — `parsed` doesn't need to already be in Asia/Kuala_Lumpur specifically,
    it just needs an explicit offset, which validate_publish_date_iso()
    already guarantees before this is ever called."""
    reference = now if now is not None else datetime.now(UTC)
    if parsed <= reference:
        raise InvalidPublishDate(
            f"publish_date {parsed.isoformat()!r} is not in the future "
            f"(reference: {reference.isoformat()!r}) — use an empty schedule "
            "to publish immediately instead"
        )
