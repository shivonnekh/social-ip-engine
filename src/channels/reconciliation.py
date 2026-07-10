"""Periodic reconciliation sweep — a defense-in-depth backstop for comments
the live webhook missed, for ANY reason.

WHY THIS EXISTS
---------------
The 2026-07-06/07 anxiety-comment incident was caused by ONE specific bug
(Meta omitting the webhook's ``from`` object), which is now fixed with a
Graph API backfill fetch (see ``meta_webhook._dispatch_comment``). But
that fix only closes the ONE failure mode we have hard evidence for. This
sweep doesn't assume we found every possible way a comment can slip
through the live webhook path — it independently re-derives "what comments
exist on our recent posts" from the Graph API (ground truth) and replays
anything not yet handled, on a schedule, regardless of why the webhook
missed it.

SAFETY
------
Replaying is always safe, never a duplicate send: ``handle_comment()``
does a DB-backed idempotency claim (``_claim_webhook_event``) before any
outbound reply, so re-processing an already-handled comment costs one
cheap dedup check, never a second DM/ack. This sweep reuses that exact
same function — same code path as the live webhook AND
``POST /admin/backfill-comments`` — no new dispatch logic to get wrong.

Own-comment guard (``is_own_comment``) is applied here too: Graph API's
comment list includes our own public_ack replies, and an ack's text can
legitimately contain a rule's keyword (e.g. "...anxiety guide..." matches
the "anxiety" rule) — without the guard a sweep would misfire the rule
against itself every single cycle, forever.

CONFIG (all opt-out via env, conservative defaults)
    RECONCILE_ENABLED       default "true" — set "false" to disable
    RECONCILE_INTERVAL_S    default 4h between sweeps
    RECONCILE_LOOKBACK_H    default 72h — only re-check media posted within
                            this window, so the sweep stays cheap as an
                            account accumulates history
    RECONCILE_MEDIA_LIMIT   default 10 — cap Graph API calls per account
                            per cycle
"""

from __future__ import annotations

import asyncio
import logging
import os
from datetime import datetime, timedelta, timezone
from typing import Final

from src.channels import meta_client
from src.channels.meta_events import IncomingComment
from src.channels.meta_webhook import handle_comment, is_own_comment
from src.ips import registry as ip_registry
from src.ops_alert import send_ops_alert
from src.orchestrator.pipeline import JessicaPipeline

logger = logging.getLogger("channels.reconciliation")

RECONCILE_INTERVAL_S: Final[int] = int(os.environ.get("RECONCILE_INTERVAL_S", str(4 * 3600)))
RECONCILE_LOOKBACK_H: Final[int] = int(os.environ.get("RECONCILE_LOOKBACK_H", "72"))
RECONCILE_MEDIA_LIMIT: Final[int] = int(os.environ.get("RECONCILE_MEDIA_LIMIT", "10"))


def _enabled() -> bool:
    return os.environ.get("RECONCILE_ENABLED", "true").lower() == "true"


_HKT = timezone(timedelta(hours=8))


def _not_before() -> datetime | None:
    """Optional date gate: sweeps are skipped while now < RECONCILE_NOT_BEFORE.

    WHY (2026-07-10): after the expired-Postgres incident, the dedup table
    (webhook_events) restarted EMPTY on a fresh database — running a sweep
    before the old already-DM'd comments slide out of the 72h media lookback
    would re-DM every one of them. Rather than turning RECONCILE_ENABLED off
    and trusting a human to remember to turn it back on (the explicit
    requirement: "I'm afraid I'll forget"), the gate lives server-side and
    expires on its own — set RECONCILE_NOT_BEFORE=2026-07-13 once, and the
    sweep resumes automatically that day with zero human memory involved.

    A date-only value means midnight HKT. An unparseable value fails OPEN
    (gate ignored, warning logged) — same contract as notion_publish's
    _publish_date_eligible: a parsing bug must never silently disable the
    missed-comment backstop forever. Checked per-iteration (not once at loop
    start) because the comparison flips with TIME, not with a restart.
    """
    raw = os.environ.get("RECONCILE_NOT_BEFORE", "").strip()
    if not raw:
        return None
    try:
        parsed = datetime.fromisoformat(raw)
    except ValueError:
        logger.warning("[reconcile] unparseable RECONCILE_NOT_BEFORE=%r — gate ignored", raw)
        return None
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=_HKT)
    return parsed


def _gated_now() -> bool:
    nb = _not_before()
    if nb is None:
        return False
    if datetime.now(timezone.utc) < nb:
        logger.info("[reconcile] gated until %s — skipping this sweep", nb.isoformat())
        return True
    return False


def _parse_media_timestamp(raw: str) -> datetime | None:
    """Best-effort ISO8601 parse. Returns None (never raises) on any
    unexpected shape — callers treat "unknown timestamp" as "include it",
    since skipping a comment we can't date is worse than one extra check."""
    if not raw:
        return None
    try:
        parsed = datetime.fromisoformat(raw)
    except ValueError:
        return None
    if parsed.tzinfo is None:
        # Meta's Graph API always includes a UTC offset in practice, but
        # guard anyway: comparing a naive datetime against the tz-aware
        # `cutoff` in _sweep_account raises TypeError, which would abort
        # that account's whole sweep cycle over a single malformed field.
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed


def _active_ig_accounts() -> list[str]:
    """Every active IP's Instagram business account id, deduped, excluding
    any explicitly set to ``comments: "off"``."""
    accounts: list[str] = []
    for ip in ip_registry.all_ips():
        if not ip.active:
            continue
        channel = ip.channels.get("instagram")
        if channel is None or channel.comments == "off":
            continue
        if channel.account_id not in accounts:
            accounts.append(channel.account_id)
    return accounts


async def _sweep_account(account_id: str, pipeline: JessicaPipeline) -> dict:
    """Reconcile one IG account's recent media against the live handler."""
    cutoff = datetime.now(timezone.utc) - timedelta(hours=RECONCILE_LOOKBACK_H)
    media_list = await meta_client.list_recent_media(
        platform="instagram", account_id=account_id, limit=RECONCILE_MEDIA_LIMIT,
    )

    media_checked = 0
    comments_checked = 0
    replayed = 0

    for media in media_list:
        ts = _parse_media_timestamp(str(media.get("timestamp", "")))
        if ts is not None and ts < cutoff:
            continue  # older than our lookback window — skip, keeps cost bounded

        media_id = str(media.get("id") or "")
        if not media_id:
            continue
        media_checked += 1

        comments = await meta_client.list_comments(
            media_id, platform="instagram", account_id=account_id,
        )
        for raw in comments:
            comments_checked += 1
            comment_id = str(raw.get("id") or "")
            from_id = str((raw.get("from") or {}).get("id") or "")
            if not comment_id or not from_id:
                continue  # genuinely unusable even for the sweep itself

            comment = IncomingComment(
                platform="instagram",
                comment_id=comment_id,
                text=str(raw.get("text") or ""),
                from_id=from_id,
                from_username=str((raw.get("from") or {}).get("username") or ""),
                media_id=media_id,
                recipient_id=account_id,
            )
            if is_own_comment(comment):
                continue

            try:
                await handle_comment(comment, pipeline)
            except Exception:  # noqa: BLE001
                # One bad comment must never abort the rest of the sweep.
                logger.exception(
                    "[reconcile] handle_comment failed for %s (account=%s)",
                    comment_id, account_id,
                )
                continue
            replayed += 1  # note: includes already-handled no-ops (cheap, safe)

    return {
        "account_id": account_id,
        "media_checked": media_checked,
        "comments_checked": comments_checked,
        "replayed": replayed,
    }


async def run_reconciliation_sweep(pipeline: JessicaPipeline) -> None:
    """One full sweep across every active IG account with comments enabled."""
    accounts = _active_ig_accounts()
    if not accounts:
        logger.info("[reconcile] no active IG accounts with comments enabled — skipping sweep")
        return

    logger.info(
        "[reconcile] sweep starting — accounts=%s lookback=%dh media_limit=%d",
        accounts, RECONCILE_LOOKBACK_H, RECONCILE_MEDIA_LIMIT,
    )
    for account_id in accounts:
        try:
            summary = await _sweep_account(account_id, pipeline)
            logger.info("[reconcile] account %s done: %s", account_id, summary)
        except Exception as exc:  # noqa: BLE001
            logger.exception("[reconcile] sweep failed for account %s", account_id)
            await send_ops_alert(
                f"reconcile_failed_{account_id}",
                f"🟡 IG reconciliation sweep failed for account {account_id}: {exc}",
            )


async def start_reconciliation_loop(pipeline: JessicaPipeline) -> None:
    """Long-running coroutine — mirrors ``broadcaster.scheduler``'s
    sleep-loop pattern (see ``start_broadcast_loop``). Sleeps first so we
    don't sweep at boot, when other startup work is also hitting the CRM
    and Graph API rate limits matter more."""
    if not _enabled():
        logger.info("[reconcile] RECONCILE_ENABLED is false — loop not started")
        return
    logger.info("[reconcile] loop started — interval=%ds lookback=%dh", RECONCILE_INTERVAL_S, RECONCILE_LOOKBACK_H)
    while True:
        await asyncio.sleep(RECONCILE_INTERVAL_S)
        if _gated_now():
            continue
        try:
            await run_reconciliation_sweep(pipeline)
        except Exception as exc:  # noqa: BLE001
            logger.error("[reconcile] loop error (will retry next cycle): %s", exc)
