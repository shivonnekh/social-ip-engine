"""notion_publish.py — plan Instagram Reels auto-publishes from Notion.

WHY THIS EXISTS
---------------
``notion_sync.py`` arms the comment→DM funnel at "🟢 Ready to Publish" (or
"✅ Published" as a safety net) — that stage exists specifically so CC can
test-comment their own post BEFORE it's live. This module is the deliberately
SEPARATE trigger for the actual "go live" action: only "✅ Published" causes
a Reel video to actually get posted to Instagram. Keeping these two triggers
apart preserves the pre-flight test gate — see ``docs/content-flow-diagram.html``
§⑤ for the full rationale. Do not fold this into ``notion_sync.sync_once()``.

WHAT THIS MODULE DOES NOT DO
------------------------------
It never calls the Instagram Graph API — ``plan_publishes()`` is the
BLOCKING half (Notion I/O + cover/caption resolution + the idempotency
claim). The actual create→poll→publish Graph API calls are async and live
in ``notion_publish_runner.py``, spawned as background tasks by the caller
(``POST /admin/notion-publish`` in ``src/web.py``) so a slow Meta processing
time (seconds to minutes) never blocks the webhook response.

THE DUPLICATE-POST GUARD (highest-severity concern in this whole feature)
---------------------------------------------------------------------------
A duplicate live post to a real Instagram business account is irreversible
and embarrassing — the guard here is deliberately more paranoid than
``notion_sync``'s keyword-rule dedup:

1. **Row-level** — ``notion_publish_state.json`` is a ledger keyed by row
   id. Any row already ``"in_flight"``, ``"published"``, or ``"skipped"``
   is never reconsidered. A row ``"failed"`` IS reconsidered, but only up
   to ``NOTION_PUBLISH_MAX_ATTEMPTS`` (default 3) — after that it is marked
   permanently ``"skipped"`` so a persistently broken video can't hammer the
   Graph API forever.
2. **Video-URL-level** — before claiming a row, its Production Video URL
   (query-string stripped, since Notion's S3 signatures rotate) is checked
   against every OTHER ledger entry already ``"published"``. A match means
   some other row already posted this exact video — this row is marked
   ``"skipped"`` and NEVER posted, even though it is its own distinct Notion
   page. Defends a duplicated/recreated Production row pointing at the same
   finished video.
3. **Claim-before-call** — a new row's ledger entry is written to disk
   (atomic tmp+replace, same idiom as ``notion_sync._save_json``)
   IMMEDIATELY as ``"in_flight"``, one row at a time, BEFORE the loop even
   reaches the next row — deliberately not batched at the end of the loop
   like ``notion_sync.sync_once()`` does for keyword rules. This is stricter
   on purpose: if the process crashes mid-loop, only rows already written
   are claimed; nothing is "planned but not yet on disk." No Instagram API
   call happens until AFTER a row's claim is durable.

Resuming a crashed/interrupted publish (container created but never
polled/published, e.g. a Render deploy mid-poll) does not need to re-query
Notion at all — the ledger entry stores everything (video_url, cover_url,
caption, account_id, creation_id) needed to reconstruct a ``PublishJob`` and
continue. See ``load_in_flight_jobs()`` below and
``notion_publish_runner.resume_in_flight()``.

STATE
-----
``data/channels/notion_publish_state.json`` — the ledger described above.
This file is the single source of truth for "has this ever been posted,"
not the Notion Stage property (which can be bounced back and forth).
"""

from __future__ import annotations

import json
import os
import threading
import urllib.parse
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Final
from zoneinfo import ZoneInfo

from src import notion_publish_caption, notion_publish_media
from src.ips import registry as ip_registry
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
_STATE_PATH = REPO_ROOT / "data" / "channels" / "notion_publish_state.json"

# Same operating-timezone convention as src/crm/repo.py's _HKT — this
# business runs on Hong Kong time, so a date-only Publish Date ("no time
# component set) is interpreted as "eligible from 00:00 HKT that day."
_HKT: Final = ZoneInfo("Asia/Hong_Kong")

# Notion property name read for optional scheduled publishing (see
# _publish_date_eligible below). Override via NOTION_PUBLISH_DATE_PROP if
# the Production Tracker column is ever renamed.
_DEFAULT_PUBLISH_DATE_PROP = "Publish Date"

_PUBLISH_STAGE = "✅ Published"
_STATUS_IN_FLIGHT = "in_flight"
_STATUS_PUBLISHED = "published"
_STATUS_FAILED = "failed"
_STATUS_SKIPPED = "skipped"

# Serializes the WHOLE body of plan_publishes() across concurrent calls (e.g.
# two overlapping webhook deliveries — Notion automations are known to retry
# on timeout, and run_in_threadpool genuinely dispatches to separate OS
# threads). Without this, two threads can both load the same unclaimed-row
# snapshot before either persists its claim, and both end up claiming the
# same row / missing each other's just-claimed duplicate video. A
# threading.Lock (not asyncio.Lock) because plan_publishes is a blocking
# function that runs in a worker thread, not on the event loop.
_PLAN_LOCK = threading.Lock()

# Separate lock for the Facebook mirror planner (plan_fb_mirrors) — reads a
# different ledger, writes a different file, has no reason to serialize
# against Instagram's own planning lock. Kept as its own threading.Lock for
# the identical reason _PLAN_LOCK exists: plan_fb_mirrors also runs via
# run_in_threadpool (a worker thread), never on the event loop.
_FB_PLAN_LOCK = threading.Lock()


class LedgerCorruptError(NotionSyncError):
    """The ledger file exists but could not be parsed as a JSON object.

    Deliberately NOT silently treated as an empty ledger ({}) — this file is
    the ONLY thing preventing every historically-published row from being
    re-claimed (Notion's Stage property stays "✅ Published" forever after a
    successful post). Silently defaulting to {} on a corrupt/truncated/
    partially-written file would make the next plan_publishes() call treat
    every already-live row as brand new and re-publish all of them — the
    single worst possible failure mode for this feature. Raise loudly
    instead so the caller (the /admin/notion-publish endpoint) surfaces a
    502 and refuses to plan anything until a human investigates."""


def _max_attempts() -> int:
    raw = os.environ.get("NOTION_PUBLISH_MAX_ATTEMPTS", "3").strip()
    try:
        return max(1, int(raw))
    except ValueError:
        return 3


def _generation_cap() -> int:
    """Max covers to GENERATE (vs reuse Shot 1) per run — bounds image-API
    spend if a bulk edit flips many rows to Published at once. Override with
    ``NOTION_PUBLISH_MAX_COVER_GENERATIONS`` (default 5)."""
    raw = os.environ.get("NOTION_PUBLISH_MAX_COVER_GENERATIONS", "5").strip()
    try:
        return max(0, int(raw))
    except ValueError:
        return 5


def _generate_covers_enabled() -> bool:
    return os.environ.get("NOTION_PUBLISH_GENERATE_COVERS", "1").strip() != "0"


def _publish_date_prop() -> str:
    return os.environ.get("NOTION_PUBLISH_DATE_PROP", "").strip() or _DEFAULT_PUBLISH_DATE_PROP


def _publish_date_eligible(
    props: dict[str, Any], *, now: datetime | None = None
) -> tuple[bool, str | None]:
    """Whether a row is due to go live RIGHT NOW, based on its optional
    ``Publish Date`` property (name overridable via
    ``NOTION_PUBLISH_DATE_PROP``).

    Opt-in by design: a row with no ``Publish Date`` set — every row that
    existed before this gate did, or anyone who just wants "publish the
    instant Stage flips to ✅ Published" — is ALWAYS eligible. This
    property never blocks the existing event-driven trigger unless a human
    deliberately fills it in.

    Returns ``(eligible, warning)``. ``warning`` is set ONLY on a parse
    failure, and deliberately fails OPEN (treats the row as eligible
    anyway) — a parsing bug must never silently and permanently block a
    row a human already deliberately marked Published; it must surface
    loudly instead (see the "warnings" list in plan_publishes' return
    value) and still go live.
    """
    # The WHOLE extraction (not just the final fromisoformat parse) is
    # inside this try — a malformed shape anywhere along the way (e.g.
    # "date" being a list instead of a dict, from a corrupted Notion
    # response or NOTION_PUBLISH_DATE_PROP pointed at the wrong property)
    # must fail OPEN for this ONE row, same as a bad date string. Letting
    # any of these raise uncaught would abort plan_publishes() entirely —
    # stalling every OTHER row in the same batch, not just this one.
    try:
        date_field = (props.get(_publish_date_prop()) or {}).get("date")
        if not date_field:
            return True, None
        start = str(date_field.get("start") or "").strip()
        if not start:
            return True, None
        parsed = datetime.fromisoformat(start)
    except (ValueError, TypeError, AttributeError, OverflowError) as exc:
        return True, f"unparseable Publish Date ({exc!r}) — treating as eligible now"
    if parsed.tzinfo is None:
        # A date-only value ("YYYY-MM-DD") or a naive datetime — Notion's
        # own workspace timezone context isn't preserved by this point, so
        # we assume HKT (see module-level _HKT comment).
        parsed = parsed.replace(tzinfo=_HKT)
    reference = now if now is not None else datetime.now(_HKT)
    return parsed <= reference, None


def _stable_video_url(url: str) -> str:
    parts = urllib.parse.urlsplit(url)
    return urllib.parse.urlunsplit((parts.scheme, parts.netloc, parts.path, "", ""))


def _now_iso() -> str:
    return datetime.now(UTC).isoformat()


def _load_ledger(state_path: Path) -> dict[str, dict]:
    """Load the publish ledger. A MISSING file legitimately means "nothing
    has ever been published" (returns {}) — a PRESENT-but-unparseable file
    means something is wrong with the one source of truth that prevents
    duplicate posts, and must never be silently treated the same way. See
    ``LedgerCorruptError``."""
    if not state_path.exists():
        return {}
    try:
        data = json.loads(state_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise LedgerCorruptError(
            f"{state_path} exists but is corrupt/unreadable — refusing to plan "
            f"publishes (this file is the only thing preventing every already-"
            f"published row from being re-posted): {exc}"
        ) from exc
    if not isinstance(data, dict):
        raise LedgerCorruptError(f"{state_path} does not contain a JSON object")
    return data


def clear_ledger_entry(row_id: str, *, state_path: Path | None = None) -> dict | None:
    """Remove a row's ledger entry so the NEXT ``/admin/notion-publish``
    sweep treats it as never-published and re-claims + republishes it fresh.

    Returns the removed entry (so the caller can read ``account_id`` /
    ``ig_media_id`` before it's gone) or ``None`` if the row had no entry.

    Added 2026-07-19 alongside ``ig_publish.delete_media()`` for the first
    delete-and-republish this codebase has ever needed (即梦 audio-swap
    root cause — see that module's docstring). Deliberately a SEPARATE,
    explicit call from the normal publish flow: clearing a ledger entry is
    exactly what the ledger exists to prevent happening accidentally, so
    the caller (an admin endpoint, human-triggered) must call this before
    the live media is actually deleted, never automatically."""
    resolved = _STATE_PATH if state_path is None else state_path
    ledger = _load_ledger(resolved)
    entry = ledger.pop(row_id, None)
    if entry is not None:
        _save_json(resolved, ledger)
    return entry


@dataclass(frozen=True)
class PublishJob:
    """Everything a runner needs to create → poll → publish one Reel,
    without any further Notion I/O. Reconstructable from the ledger alone,
    which is what makes resuming a crashed publish possible."""

    row_id: str
    account_id: str
    video_url: str
    cover_url: str
    caption: str
    creation_id: str = ""


def _extract_video_url(row: dict) -> str:
    files = row.get("properties", {}).get("Production Video", {}).get("files") or []
    if not files:
        return ""
    file_obj = files[0]
    kind = file_obj.get("type", "")
    return str((file_obj.get(kind) or {}).get("url", "")).strip()


def _job_from_ledger(row_id: str, record: dict[str, Any]) -> PublishJob:
    return PublishJob(
        row_id=row_id,
        account_id=str(record.get("account_id", "")),
        video_url=str(record.get("video_url", "")),
        cover_url=str(record.get("cover_url", "")),
        caption=str(record.get("caption", "")),
        creation_id=str(record.get("creation_id") or ""),
    )


def load_in_flight_jobs(state_path: Path | None = None) -> list[PublishJob]:
    """Every ledger row still ``"in_flight"`` — reconstructed purely from
    the state file, NO Notion call. Used to resume publishes interrupted by
    a crash or deploy (at server startup, and at the top of every
    ``/admin/notion-publish`` call)."""
    ledger = _load_ledger(_STATE_PATH if state_path is None else state_path)
    return [
        _job_from_ledger(row_id, record)
        for row_id, record in ledger.items()
        if record.get("status") == _STATUS_IN_FLIGHT
    ]


def plan_publishes(
    *,
    state_path: Path | None = None,
    media_dir: Path | None = None,
    media_state_path: Path | None = None,
) -> dict[str, Any]:
    """Find rows newly at "✅ Published" and claim any that pass the
    duplicate-post guard. Returns a summary dict (never raises for expected
    "nothing to do" paths; raises ``NotionSyncError`` for auth/config
    problems, same contract as ``notion_sync.sync_once``).

    Returns ``{"jobs": [PublishJob, ...], "skipped": [...], "errors": [...],
    "warnings": [...], "checked": int}`` — ``jobs`` are ONLY the rows newly
    claimed THIS call (already-in-flight rows from a prior run are NOT
    re-returned here — see ``load_in_flight_jobs`` for those).

    The entire body runs under a process-wide lock (see ``_PLAN_LOCK``) so
    two concurrent calls (e.g. overlapping webhook deliveries) can never
    both read a stale "unclaimed" snapshot and both claim the same row or
    the same underlying video.
    """
    with _PLAN_LOCK:
        return _plan_publishes_locked(
            state_path=state_path, media_dir=media_dir, media_state_path=media_state_path,
        )


def _plan_publishes_locked(
    *,
    state_path: Path | None,
    media_dir: Path | None,
    media_state_path: Path | None,
) -> dict[str, Any]:
    """The actual planning body — ONLY ever called with ``_PLAN_LOCK`` held.
    Split out from ``plan_publishes`` purely so the lock-acquisition wrapper
    stays a one-liner; not part of this module's public surface."""
    resolved_state_path = _STATE_PATH if state_path is None else state_path
    ids = json.loads(_IDS_PATH.read_text(encoding="utf-8"))
    # Mutated in place (not rebuilt) as rows are claimed below — an
    # intentional exception to this repo's immutability preference: this is
    # a function-local accumulator, not an externally-owned input the
    # caller expects untouched.
    ledger: dict[str, dict[str, Any]] = _load_ledger(resolved_state_path)

    # Layer 2's seed set. Includes IN_FLIGHT (not just PUBLISHED) because a
    # row already mid-publish must ALSO block a different row from claiming
    # the same video — "published" alone misses the window while a container
    # is being created/polled. This set is deliberately MUTATED (not
    # rebuilt) as rows are claimed below, in the SAME call — otherwise two
    # rows sharing a video in the same batch would both slip past this
    # check, since neither is "published" yet when the other is evaluated.
    claimed_video_urls = {
        record["video_url_stable"]
        for record in ledger.values()
        if record.get("status") in (_STATUS_PUBLISHED, _STATUS_IN_FLIGHT)
        and record.get("video_url_stable")
    }

    rows = _query_all(ids["prod_db"])
    jobs: list[PublishJob] = []
    skipped: list[str] = []
    errors: list[str] = []
    warnings: list[str] = []
    generate_enabled = _generate_covers_enabled()
    generation_cap = _generation_cap()
    generations_done = 0

    for row in rows:
        row_id = row["id"]
        existing = ledger.get(row_id)
        if existing is not None:
            status = existing.get("status")
            if status in (_STATUS_IN_FLIGHT, _STATUS_PUBLISHED, _STATUS_SKIPPED):
                continue  # never reconsidered — layer 1 (row-level guard)
            if status == _STATUS_FAILED and existing.get("attempts", 0) >= _max_attempts():
                # Give up for good — transition to "skipped" (not left as
                # "failed") so the ledger is unambiguous about why this row
                # is never retried again, and so this exact branch is never
                # re-evaluated on the next run.
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
        stage = (props.get("Stage", {}).get("select") or {}).get("name", "")
        if stage != _PUBLISH_STAGE:
            continue  # only the real "go live" stage triggers this module

        eligible, date_warning = _publish_date_eligible(props)
        if date_warning:
            warnings.append(f"{row_id}: {date_warning}")
        if not eligible:
            # Deliberately NOT written to the ledger — this row must be
            # reconsidered on every future run (the daily schedule sweep in
            # notion_publish_scheduler.py exists specifically to catch this,
            # since the Notion Automation that calls this module only fires
            # ONCE, at the moment Stage flips — there is no second event to
            # re-trigger a deferred row once its date finally arrives).
            skipped.append(f"{row_id}: Publish Date not reached yet — deferred")
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
            continue  # transient — retry next run, do NOT claim

        ip_full = _title(ip_page)
        account = _ip_account(ip_full)
        if account is None:
            skipped.append(f"{row_id}: no known account for IP '{ip_full}'")
            continue
        account_id, language = account

        video_url = _extract_video_url(row)
        if not video_url:
            skipped.append(f"{row_id}: no Production Video file — will retry")
            continue  # video may land later, do NOT claim

        stable_video = _stable_video_url(video_url)
        if stable_video in claimed_video_urls:
            # Layer 2 — this exact video is already live OR already claimed
            # (possibly by an earlier row in THIS SAME batch — see the
            # dynamic .add() below). Permanently skip THIS row so it's never
            # reconsidered.
            ledger[row_id] = {
                "status": _STATUS_SKIPPED,
                "video_url": video_url,
                "video_url_stable": stable_video,
                "account_id": account_id,
                "creation_id": None,
                "ig_media_id": None,
                "posted_checkbox": False,
                "attempts": 0,
                "last_error": "duplicate video_url already published under a different row",
                "updated_at": _now_iso(),
            }
            _save_json(resolved_state_path, ledger)
            skipped.append(f"{row_id}: duplicate video already published elsewhere")
            continue

        cta = "".join(
            t["plain_text"] for t in content_page["properties"].get("CTA", {}).get("rich_text", [])
        )
        keyword = normalize_keyword(cta)
        # Headline: row's 🏷️ Title property first (punchy, public-facing —
        # see notion_publish_caption module docstring), Hook as fallback.
        # hook itself is ALSO needed below as the cover generator's
        # text-to-image prompt seed (notion_publish_media has no opinion on
        # Title vs Hook — cosmetic fallback only) — resolved once here and
        # threaded into extract_headline so a legacy row with neither Title
        # nor a Hook property doesn't pay for two separate _children() walks
        # (a real paginated Notion API call, not a cheap re-check).
        hook = notion_publish_caption.extract_hook(content_page, content_rel[0]["id"], _children)
        headline, headline_warning = notion_publish_caption.extract_headline(
            row, content_page, content_rel[0]["id"], _children, hook=hook
        )
        if headline_warning:
            warnings.append(f"{row_id}: {headline_warning}")
        caption = notion_publish_caption.build_caption(headline, keyword=keyword, language=language)

        allow_cover_generate = generate_enabled and generations_done < generation_cap
        cover_url, cover_warning = notion_publish_media.resolve_cover(
            row_id, keyword or row_id, hook, _children,
            generate=allow_cover_generate,
            media_dir=media_dir,
            state_path=media_state_path,
        )
        if cover_warning:
            warnings.append(cover_warning)
            if "generated_cover" in cover_warning and "created from" in cover_warning:
                generations_done += 1

        attempts = (existing or {}).get("attempts", 0) + 1

        # Layer 3 — claim-before-call: persist to disk NOW, one row at a
        # time, before any Meta API call is ever made for this row.
        ledger[row_id] = {
            "status": _STATUS_IN_FLIGHT,
            "video_url": video_url,
            "video_url_stable": stable_video,
            "cover_url": cover_url,
            "caption": caption,
            "account_id": account_id,
            "creation_id": None,
            "ig_media_id": None,
            "posted_checkbox": False,
            "attempts": attempts,
            "last_error": "",
            "updated_at": _now_iso(),
        }
        _save_json(resolved_state_path, ledger)
        # Extend the SAME-BATCH guard immediately — a later row in this run
        # sharing this exact video must see it as already claimed, not just
        # rows claimed in a PRIOR call.
        claimed_video_urls.add(stable_video)

        jobs.append(
            PublishJob(
                row_id=row_id, account_id=account_id, video_url=video_url,
                cover_url=cover_url, caption=caption, creation_id="",
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
# Facebook mirror — deliberately SEPARATE from everything above
# ---------------------------------------------------------------------------
#
# WHY A MIRROR, NOT A SECOND INDEPENDENT PLANNER
# -----------------------------------------------------------------------
# The product requirement is "post to Jackie's FB Page the same content
# already auto-published to his Instagram" (2026-07-08) — not "independently
# decide what to publish to Facebook." So instead of re-querying Notion and
# re-resolving cover/caption a second time (which risks the two platforms
# drifting apart if resolution ever behaves differently on a second call),
# ``plan_fb_mirrors()`` reads Instagram's OWN ledger (``_STATE_PATH``) for
# rows already ``"published"`` there and reuses that record's ``video_url``/
# ``cover_url``/``caption`` VERBATIM. Byte-for-byte mirroring is achieved by
# construction, not by trusting two independent code paths to agree.
#
# WHY A SEPARATE LEDGER FILE (``_FB_STATE_PATH``), NOT A SHARED ONE
# -----------------------------------------------------------------------
# ``LedgerCorruptError``'s docstring calls silently treating a corrupt
# ledger as empty "the single worst possible failure mode for this
# feature" (mass re-post of every already-live row). Mixing FB's write path
# into the SAME file as Instagram's would mean a bug anywhere in the new FB
# code could corrupt the one file protecting Instagram from duplicate posts.
# A separate file makes that impossible by construction: no FB code path
# ever opens ``_STATE_PATH`` for writing.
#
# WHY THIS ACHIEVES "RETRY ONLY THE FAILED PLATFORM" FOR FREE
# -----------------------------------------------------------------------
# ``plan_publishes()`` (above) permanently skips a row once ITS ledger marks
# it ``published``/``in_flight``/``skipped`` — Instagram never reconsiders a
# row it already succeeded on. ``plan_fb_mirrors()`` is intentionally NOT
# gated by that: every call re-scans EVERY Instagram-published row and
# independently checks the FB ledger's own status for it. So:
#   * IG published, FB never attempted / previously failed -> mirrored now.
#   * IG published, FB already published -> layer-1 guard skips (below).
#   * IG still in_flight / never published -> nothing to mirror yet; this
#     row is picked up on a LATER call, once Instagram's ledger shows it
#     published (the daily schedule sweep and the next webhook fire both
#     call this the same way they call the Instagram planner).
# No coupling to Instagram's own retry/attempt counters — the two ledgers
# are fully independent, exactly as required.

_FB_STATE_PATH = REPO_ROOT / "data" / "channels" / "notion_publish_fb_state.json"


def _fb_account_for_ig_account(ig_account_id: str) -> str | None:
    """The Facebook Page account id for whichever IP owns ``ig_account_id``,
    or ``None`` if that IP has no Facebook channel registered (e.g. Chloe
    today) or its credentials aren't set. Registry-driven — adding a new
    IP's Facebook Page later needs only an ``ip.json`` edit, no code change
    here (same pattern as ``ip_registry.persona_dm_channels`` — see its
    docstring for the incident this pattern was born from)."""
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


def plan_fb_mirrors(*, ig_state_path: Path | None = None, fb_state_path: Path | None = None) -> dict[str, Any]:
    """Mirror every Instagram-published row to Facebook that hasn't been
    mirrored yet. Pure ledger-to-ledger — no Notion I/O, no cover/caption
    re-resolution (see module-level comment above for why). Safe to call as
    often as desired; layers 1-3 below are the same shape as
    ``plan_publishes()``'s guard, applied to the FB ledger only.

    Returns ``{"jobs": [PublishJob, ...], "skipped": [...], "checked": int}``
    — ``jobs`` are FB ``PublishJob``s newly claimed this call.
    """
    with _FB_PLAN_LOCK:
        return _plan_fb_mirrors_locked(ig_state_path=ig_state_path, fb_state_path=fb_state_path)


def _plan_fb_mirrors_locked(
    *, ig_state_path: Path | None, fb_state_path: Path | None,
) -> dict[str, Any]:
    resolved_ig_path = _STATE_PATH if ig_state_path is None else ig_state_path
    resolved_fb_path = _FB_STATE_PATH if fb_state_path is None else fb_state_path

    ig_ledger = _load_ledger(resolved_ig_path)
    fb_ledger = _load_ledger(resolved_fb_path)

    claimed_video_urls = {
        record["video_url_stable"]
        for record in fb_ledger.values()
        if record.get("status") in (_STATUS_PUBLISHED, _STATUS_IN_FLIGHT)
        and record.get("video_url_stable")
    }

    jobs: list[PublishJob] = []
    skipped: list[str] = []
    checked = 0

    for row_id, ig_record in ig_ledger.items():
        if ig_record.get("status") != _STATUS_PUBLISHED:
            continue  # nothing to mirror yet — see module docstring
        checked += 1

        existing = fb_ledger.get(row_id)
        if existing is not None:
            status = existing.get("status")
            if status in (_STATUS_IN_FLIGHT, _STATUS_PUBLISHED, _STATUS_SKIPPED):
                continue  # layer 1 — never reconsidered
            if status == _STATUS_FAILED and existing.get("attempts", 0) >= _max_attempts():
                fb_ledger[row_id] = {
                    **existing,
                    "status": _STATUS_SKIPPED,
                    "last_error": f"gave up after {existing.get('attempts', 0)} attempts",
                    "updated_at": _now_iso(),
                }
                _save_json(resolved_fb_path, fb_ledger)
                skipped.append(f"{row_id}: FB mirror gave up after {existing.get('attempts', 0)} attempts")
                continue

        fb_account_id = _fb_account_for_ig_account(str(ig_record.get("account_id", "")))
        if fb_account_id is None:
            skipped.append(f"{row_id}: no Facebook channel/credentials for this IP — not mirrored")
            continue

        video_url = str(ig_record.get("video_url", ""))
        stable_video = str(ig_record.get("video_url_stable") or _stable_video_url(video_url))
        if stable_video in claimed_video_urls:
            fb_ledger[row_id] = {
                "status": _STATUS_SKIPPED,
                "video_url": video_url,
                "video_url_stable": stable_video,
                "account_id": fb_account_id,
                "creation_id": None,
                "fb_media_id": None,
                "posted_checkbox": False,
                "attempts": 0,
                "last_error": "duplicate video_url already mirrored to FB under a different row",
                "updated_at": _now_iso(),
            }
            _save_json(resolved_fb_path, fb_ledger)
            skipped.append(f"{row_id}: duplicate video already mirrored to FB elsewhere")
            continue

        attempts = (existing or {}).get("attempts", 0) + 1

        # Layer 3 — claim-before-call, same discipline as plan_publishes().
        fb_ledger[row_id] = {
            "status": _STATUS_IN_FLIGHT,
            "video_url": video_url,
            "video_url_stable": stable_video,
            "cover_url": str(ig_record.get("cover_url", "")),
            "caption": str(ig_record.get("caption", "")),
            "account_id": fb_account_id,
            "creation_id": None,
            "fb_media_id": None,
            "posted_checkbox": False,
            "attempts": attempts,
            "last_error": "",
            "updated_at": _now_iso(),
        }
        _save_json(resolved_fb_path, fb_ledger)
        claimed_video_urls.add(stable_video)

        jobs.append(
            PublishJob(
                row_id=row_id, account_id=fb_account_id,
                video_url=video_url, cover_url=str(ig_record.get("cover_url", "")),
                caption=str(ig_record.get("caption", "")), creation_id="",
            )
        )

    return {"checked": checked, "jobs": jobs, "skipped": skipped}


def load_fb_in_flight_jobs(state_path: Path | None = None) -> list[PublishJob]:
    """FB analogue of ``load_in_flight_jobs`` — every FB ledger row still
    ``"in_flight"``, reconstructed purely from the FB ledger, no Notion
    call. Used to resume FB mirrors interrupted by a crash/deploy."""
    ledger = _load_ledger(_FB_STATE_PATH if state_path is None else state_path)
    return [
        _job_from_ledger(row_id, record)
        for row_id, record in ledger.items()
        if record.get("status") == _STATUS_IN_FLIGHT
    ]
