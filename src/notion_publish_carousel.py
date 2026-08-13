"""notion_publish_carousel.py — plan Instagram carousel auto-publishes from
Notion, plus the Facebook mirror.

Sibling of ``notion_publish.py`` (Reels). Structurally near-identical —
same claim-before-call ledger discipline, same "Facebook mirrors Instagram's
own ledger, never independently decides" design — but the CONTENT unit is
an ordered list of panel image URLs instead of one video_url, and there is
no separate cover: every panel IS the post.

WHY A SEPARATE MODULE, NOT A GENERALIZED ONE
---------------------------------------------
``notion_publish.py``'s own docstring calls its duplicate-post guard "the
single worst possible failure mode for this feature." Refactoring that
already-proven code to be generic over "one video" vs "N panels" is a
strictly higher-risk change than duplicating ~150 lines of already-proven
shape with the one real difference (dedup identity) swapped in. Same
reasoning ``notion_publish_fb_runner.py`` already documents for its own
existence.

THE DUPLICATE-POST GUARD, ADAPTED FOR CAROUSELS
--------------------------------------------------
1. **Row-level** — ``notion_publish_carousel_state.json`` ledger keyed by
   row id, same three-outcome contract (in_flight/published/skipped never
   reconsidered; failed retried up to ``NOTION_PUBLISH_MAX_ATTEMPTS``).
2. **Panel-set-level** — instead of one stable video URL, the identity is a
   hash of the ORDERED, query-string-stripped panel URLs
   (``_panel_set_hash``). A carousel republished under a different row
   (e.g. a duplicated Production row pointing at the same panels) is
   caught the same way a duplicated video is caught in ``notion_publish``.
3. **Claim-before-call** — identical discipline: the ledger entry is
   written to disk as ``"in_flight"`` immediately, before any Meta call,
   one row at a time.

A row with an INCOMPLETE panel set (some panels generated, some not) is
never claimed at all — ``notion_publish_carousel_media.find_carousel_panel_sources``
returns ``complete=False`` for that case and this module skips the row
without writing anything to the ledger, so it's retried fresh once the
missing panel lands.

STATE
-----
- ``data/channels/notion_publish_carousel_state.json`` — Instagram ledger.
- ``data/channels/notion_publish_carousel_fb_state.json`` — Facebook mirror
  ledger, written ONLY by ``plan_fb_carousel_mirrors`` below, never by the
  Instagram planner (same isolation reasoning as ``notion_publish.py``'s
  ``_FB_STATE_PATH``).
"""

from __future__ import annotations

import hashlib
import json
import os
import threading
import urllib.parse
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Final
from zoneinfo import ZoneInfo

from src import notion_publish_caption
from src.ips import registry as ip_registry
from src.notion_publish import LedgerCorruptError, _now_iso
from src.notion_publish_carousel_media import find_carousel_panel_sources
from src.notion_sync import (
    NotionSyncError,
    _children,
    _ip_account,
    _ncall,
    _query_all,
    _save_json,
    _title,
    normalize_keyword,
)

REPO_ROOT = Path(__file__).resolve().parent.parent
_IDS_PATH = REPO_ROOT / "scripts" / "notion_ids.json"
_STATE_PATH = REPO_ROOT / "data" / "channels" / "notion_publish_carousel_state.json"
_FB_STATE_PATH = REPO_ROOT / "data" / "channels" / "notion_publish_carousel_fb_state.json"

_HKT: Final = ZoneInfo("Asia/Hong_Kong")

_CAROUSEL_PUBLISH_STAGE = "✅ Published"
_DEFAULT_CAROUSEL_STAGE_PROP = "🎠 Carousel Stage"
_DEFAULT_CAROUSEL_PUBLISH_DATE_PROP = "🎠 Carousel Publish Date"
_DEFAULT_CAROUSEL_CAPTION_HEADING = "carousel caption"

_STATUS_IN_FLIGHT = "in_flight"
_STATUS_PUBLISHED = "published"
_STATUS_FAILED = "failed"
_STATUS_SKIPPED = "skipped"

MIN_PANELS: Final[int] = 2
MAX_PANELS: Final[int] = 10

# Same reasoning as notion_publish._PLAN_LOCK / _FB_PLAN_LOCK — blocking
# functions run via run_in_threadpool (real OS threads), not the event
# loop, so a threading.Lock (not asyncio.Lock) is correct here.
_PLAN_LOCK = threading.Lock()
_FB_PLAN_LOCK = threading.Lock()


def _max_attempts() -> int:
    raw = os.environ.get("NOTION_PUBLISH_MAX_ATTEMPTS", "3").strip()
    try:
        return max(1, int(raw))
    except ValueError:
        return 3


def _carousel_stage_prop() -> str:
    return os.environ.get("NOTION_CAROUSEL_STAGE_PROP", "").strip() or _DEFAULT_CAROUSEL_STAGE_PROP


def _carousel_publish_date_prop() -> str:
    return (
        os.environ.get("NOTION_CAROUSEL_PUBLISH_DATE_PROP", "").strip()
        or _DEFAULT_CAROUSEL_PUBLISH_DATE_PROP
    )


def _carousel_publish_date_eligible(
    props: dict[str, Any], *, now: datetime | None = None
) -> tuple[bool, str | None]:
    """Carousel analogue of ``notion_publish._publish_date_eligible`` — same
    opt-in-only, fail-open-on-parse-error contract, reading the SEPARATE
    ``🎠 Carousel Publish Date`` property instead of the Reel's ``Publish
    Date``. Kept as its own small function rather than parameterizing the
    original (that function has no prop-name parameter today and this repo
    prefers small, obviously-correct duplication over reshaping
    already-proven code — see module docstring)."""
    try:
        date_field = (props.get(_carousel_publish_date_prop()) or {}).get("date")
        if not date_field:
            return True, None
        start = str(date_field.get("start") or "").strip()
        if not start:
            return True, None
        parsed = datetime.fromisoformat(start)
    except (ValueError, TypeError, AttributeError, OverflowError) as exc:
        return True, f"unparseable Carousel Publish Date ({exc!r}) — treating as eligible now"
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=_HKT)
    reference = now if now is not None else datetime.now(_HKT)
    return parsed <= reference, None


def _stable_panel_url(url: str) -> str:
    parts = urllib.parse.urlsplit(url)
    return urllib.parse.urlunsplit((parts.scheme, parts.netloc, parts.path, "", ""))


def _panel_set_hash(image_urls: tuple[str, ...]) -> str:
    """Stable identity for an ORDERED set of panel images — the carousel
    analogue of ``notion_publish._stable_video_url``. Order-sensitive: a
    re-ordered carousel is a genuinely different post. Each URL is
    query-string-stripped first (Notion's presigned S3 URLs rotate)."""
    joined = "|".join(_stable_panel_url(u) for u in image_urls)
    return hashlib.sha256(joined.encode("utf-8")).hexdigest()


def _load_ledger(state_path: Path) -> dict[str, dict]:
    """Same contract as ``notion_publish._load_ledger`` — a present-but-
    unparseable file must never be silently treated as empty (see
    ``LedgerCorruptError``)."""
    if not state_path.exists():
        return {}
    try:
        data = json.loads(state_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise LedgerCorruptError(
            f"{state_path} exists but is corrupt/unreadable — refusing to plan "
            f"carousel publishes (this file is the only thing preventing every "
            f"already-published carousel from being re-posted): {exc}"
        ) from exc
    if not isinstance(data, dict):
        raise LedgerCorruptError(f"{state_path} does not contain a JSON object")
    return data


@dataclass(frozen=True)
class CarouselPublishJob:
    """Everything a runner needs to create -> poll -> publish one carousel,
    without any further Notion I/O. Reconstructable from the ledger alone
    (same resumability contract as ``notion_publish.PublishJob``)."""

    row_id: str
    account_id: str
    image_urls: tuple[str, ...]
    caption: str
    item_creation_ids: tuple[str, ...] = ()
    creation_id: str = ""


def _job_from_ledger(row_id: str, record: dict[str, Any]) -> CarouselPublishJob:
    return CarouselPublishJob(
        row_id=row_id,
        account_id=str(record.get("account_id", "")),
        image_urls=tuple(record.get("image_urls") or ()),
        caption=str(record.get("caption", "")),
        item_creation_ids=tuple(record.get("item_creation_ids") or ()),
        creation_id=str(record.get("creation_id") or ""),
    )


def load_in_flight_jobs(state_path: Path | None = None) -> list[CarouselPublishJob]:
    ledger = _load_ledger(_STATE_PATH if state_path is None else state_path)
    return [
        _job_from_ledger(row_id, record)
        for row_id, record in ledger.items()
        if record.get("status") == _STATUS_IN_FLIGHT
    ]


def _extract_carousel_caption_override(content_page_id: str, children_fn) -> str:
    """Optional per-concept caption override — a ``heading_3`` containing
    "carousel caption" followed by a ``code`` block, same convention as the
    Reel's "First DM" extraction in ``notion_sync._extract_first_dm``.
    Empty string means "no override" (caller falls back to the normal
    hook-derived caption)."""
    label_matched = False
    for block in children_fn(content_page_id):
        block_type = block.get("type", "")
        if block_type == "heading_3":
            text = "".join(
                t.get("plain_text", "") for t in block.get("heading_3", {}).get("rich_text", [])
            ).casefold()
            label_matched = _DEFAULT_CAROUSEL_CAPTION_HEADING in text
        elif block_type == "code" and label_matched:
            return "".join(
                t.get("plain_text", "") for t in block.get("code", {}).get("rich_text", [])
            )
    return ""


def plan_carousel_publishes(*, state_path: Path | None = None) -> dict[str, Any]:
    """Find rows newly at Carousel-Stage-Published and claim any that pass
    the duplicate-post guard. Same return contract as
    ``notion_publish.plan_publishes``."""
    with _PLAN_LOCK:
        return _plan_carousel_publishes_locked(state_path=state_path)


def _plan_carousel_publishes_locked(*, state_path: Path | None) -> dict[str, Any]:
    resolved_state_path = _STATE_PATH if state_path is None else state_path
    ids = json.loads(_IDS_PATH.read_text(encoding="utf-8"))
    ledger: dict[str, dict[str, Any]] = _load_ledger(resolved_state_path)

    claimed_hashes = {
        record["panel_set_hash"]
        for record in ledger.values()
        if record.get("status") in (_STATUS_PUBLISHED, _STATUS_IN_FLIGHT)
        and record.get("panel_set_hash")
    }

    rows = _query_all(ids["prod_db"])
    jobs: list[CarouselPublishJob] = []
    skipped: list[str] = []
    errors: list[str] = []
    warnings: list[str] = []

    for row in rows:
        row_id = row["id"]
        existing = ledger.get(row_id)
        if existing is not None:
            status = existing.get("status")
            if status in (_STATUS_IN_FLIGHT, _STATUS_PUBLISHED, _STATUS_SKIPPED):
                continue
            if status == _STATUS_FAILED and existing.get("attempts", 0) >= _max_attempts():
                ledger[row_id] = {
                    **existing,
                    "status": _STATUS_SKIPPED,
                    "last_error": f"gave up after {existing.get('attempts', 0)} attempts",
                    "updated_at": _now_iso(),
                }
                _save_json(resolved_state_path, ledger)
                skipped.append(f"{row_id}: gave up after {existing.get('attempts', 0)} attempts")
                continue

        props = row["properties"]
        stage = (props.get(_carousel_stage_prop(), {}).get("select") or {}).get("name", "")
        if stage != _CAROUSEL_PUBLISH_STAGE:
            continue

        eligible, date_warning = _carousel_publish_date_eligible(props)
        if date_warning:
            warnings.append(f"{row_id}: {date_warning}")
        if not eligible:
            skipped.append(f"{row_id}: Carousel Publish Date not reached yet — deferred")
            continue

        content_rel = props.get("Content", {}).get("relation") or []
        ip_rel = props.get("IP", {}).get("relation") or []
        if not content_rel or not ip_rel:
            skipped.append(f"{row_id}: missing Content/IP relation")
            continue

        try:
            content_page = _ncall("GET", f"/pages/{content_rel[0]['id']}")
            ip_page = _ncall("GET", f"/pages/{ip_rel[0]['id']}")
        except NotionSyncError as exc:
            errors.append(str(exc))
            continue

        ip_full = _title(ip_page)
        account = _ip_account(ip_full)
        if account is None:
            skipped.append(f"{row_id}: no known account for IP '{ip_full}'")
            continue
        account_id, language = account

        image_urls, complete = find_carousel_panel_sources(row_id, _children)
        if not complete:
            skipped.append(f"{row_id}: panel set has a hole — will retry")
            continue  # never claim an incomplete carousel
        if len(image_urls) < MIN_PANELS:
            skipped.append(f"{row_id}: need at least {MIN_PANELS} panels, got {len(image_urls)}")
            continue
        if len(image_urls) > MAX_PANELS:
            skipped.append(f"{row_id}: at most {MAX_PANELS} panels allowed, got {len(image_urls)}")
            continue

        panel_hash = _panel_set_hash(tuple(image_urls))
        if panel_hash in claimed_hashes:
            ledger[row_id] = {
                "status": _STATUS_SKIPPED,
                "image_urls": image_urls,
                "panel_set_hash": panel_hash,
                "account_id": account_id,
                "creation_id": None,
                "item_creation_ids": [],
                "ig_media_id": None,
                "posted_checkbox": False,
                "attempts": 0,
                "last_error": "duplicate panel set already published under a different row",
                "updated_at": _now_iso(),
            }
            _save_json(resolved_state_path, ledger)
            skipped.append(f"{row_id}: duplicate panel set already published elsewhere")
            continue

        cta = "".join(
            t["plain_text"] for t in content_page["properties"].get("CTA", {}).get("rich_text", [])
        )
        keyword = normalize_keyword(cta)
        override = _extract_carousel_caption_override(content_rel[0]["id"], _children)
        if override.strip():
            caption = override
        else:
            hook = notion_publish_caption.extract_hook(content_page, content_rel[0]["id"], _children)
            headline, headline_warning = notion_publish_caption.extract_headline(
                row, content_page, content_rel[0]["id"], _children, hook=hook
            )
            if headline_warning:
                warnings.append(f"{row_id}: {headline_warning}")
            caption = notion_publish_caption.build_caption(headline, keyword=keyword, language=language)

        attempts = (existing or {}).get("attempts", 0) + 1

        ledger[row_id] = {
            "status": _STATUS_IN_FLIGHT,
            "image_urls": image_urls,
            "panel_set_hash": panel_hash,
            "caption": caption,
            "account_id": account_id,
            "creation_id": None,
            "item_creation_ids": [],
            "ig_media_id": None,
            "posted_checkbox": False,
            "attempts": attempts,
            "last_error": "",
            "updated_at": _now_iso(),
        }
        _save_json(resolved_state_path, ledger)
        claimed_hashes.add(panel_hash)

        jobs.append(
            CarouselPublishJob(
                row_id=row_id, account_id=account_id, image_urls=tuple(image_urls), caption=caption,
            )
        )

    return {
        "checked": len(rows),
        "jobs": jobs,
        "skipped": skipped,
        "errors": errors,
        "warnings": warnings,
    }


# ---------------------------------------------------------------------------
# Facebook mirror — reads the IG carousel ledger, never independently
# decides. Same "why a mirror, why a separate lock/file" reasoning as
# notion_publish.py's plan_fb_mirrors — see that module for the long form.
# ---------------------------------------------------------------------------


def _fb_account_for_ig_account(ig_account_id: str) -> str | None:
    ip = ip_registry.for_account(ig_account_id)
    if ip is None:
        return None
    fb_channel = ip.channels.get("facebook")
    if fb_channel is None:
        return None
    account_id = os.environ.get(fb_channel.user_id_env, "").strip()
    token = os.environ.get(fb_channel.token_env, "").strip()
    if not account_id or not token:
        return None
    return account_id


def plan_fb_carousel_mirrors(
    *, ig_state_path: Path | None = None, fb_state_path: Path | None = None
) -> dict[str, Any]:
    with _FB_PLAN_LOCK:
        return _plan_fb_carousel_mirrors_locked(ig_state_path=ig_state_path, fb_state_path=fb_state_path)


def _plan_fb_carousel_mirrors_locked(
    *, ig_state_path: Path | None, fb_state_path: Path | None,
) -> dict[str, Any]:
    resolved_ig_path = _STATE_PATH if ig_state_path is None else ig_state_path
    resolved_fb_path = _FB_STATE_PATH if fb_state_path is None else fb_state_path

    ig_ledger = _load_ledger(resolved_ig_path)
    fb_ledger = _load_ledger(resolved_fb_path)

    claimed_hashes = {
        record["panel_set_hash"]
        for record in fb_ledger.values()
        if record.get("status") in (_STATUS_PUBLISHED, _STATUS_IN_FLIGHT)
        and record.get("panel_set_hash")
    }

    jobs: list[CarouselPublishJob] = []
    skipped: list[str] = []
    checked = 0

    for row_id, ig_record in ig_ledger.items():
        if ig_record.get("status") != _STATUS_PUBLISHED:
            continue
        checked += 1

        existing = fb_ledger.get(row_id)
        if existing is not None:
            status = existing.get("status")
            if status in (_STATUS_IN_FLIGHT, _STATUS_PUBLISHED, _STATUS_SKIPPED):
                continue
            if status == _STATUS_FAILED and existing.get("attempts", 0) >= _max_attempts():
                fb_ledger[row_id] = {
                    **existing,
                    "status": _STATUS_SKIPPED,
                    "last_error": f"gave up after {existing.get('attempts', 0)} attempts",
                    "updated_at": _now_iso(),
                }
                _save_json(resolved_fb_path, fb_ledger)
                skipped.append(f"{row_id}: FB carousel mirror gave up after {existing.get('attempts', 0)} attempts")
                continue

        fb_account_id = _fb_account_for_ig_account(str(ig_record.get("account_id", "")))
        if fb_account_id is None:
            skipped.append(f"{row_id}: no Facebook channel/credentials for this IP — not mirrored")
            continue

        image_urls = tuple(ig_record.get("image_urls") or ())
        panel_hash = str(ig_record.get("panel_set_hash") or _panel_set_hash(image_urls))
        if panel_hash in claimed_hashes:
            fb_ledger[row_id] = {
                "status": _STATUS_SKIPPED,
                "image_urls": image_urls,
                "panel_set_hash": panel_hash,
                "account_id": fb_account_id,
                "creation_id": None,
                "photo_ids": [],
                "fb_media_id": None,
                "posted_checkbox": False,
                "attempts": 0,
                "last_error": "duplicate panel set already mirrored to FB under a different row",
                "updated_at": _now_iso(),
            }
            _save_json(resolved_fb_path, fb_ledger)
            skipped.append(f"{row_id}: duplicate panel set already mirrored to FB elsewhere")
            continue

        attempts = (existing or {}).get("attempts", 0) + 1

        fb_ledger[row_id] = {
            "status": _STATUS_IN_FLIGHT,
            "image_urls": image_urls,
            "panel_set_hash": panel_hash,
            "caption": str(ig_record.get("caption", "")),
            "account_id": fb_account_id,
            "creation_id": None,
            "photo_ids": [],
            "fb_media_id": None,
            "posted_checkbox": False,
            "attempts": attempts,
            "last_error": "",
            "updated_at": _now_iso(),
        }
        _save_json(resolved_fb_path, fb_ledger)
        claimed_hashes.add(panel_hash)

        jobs.append(
            CarouselPublishJob(
                row_id=row_id, account_id=fb_account_id, image_urls=image_urls,
                caption=str(ig_record.get("caption", "")),
            )
        )

    return {"checked": checked, "jobs": jobs, "skipped": skipped}


def load_fb_in_flight_jobs(state_path: Path | None = None) -> list[CarouselPublishJob]:
    ledger = _load_ledger(_FB_STATE_PATH if state_path is None else state_path)
    return [
        _job_from_ledger(row_id, record)
        for row_id, record in ledger.items()
        if record.get("status") == _STATUS_IN_FLIGHT
    ]
