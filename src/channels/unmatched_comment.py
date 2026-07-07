"""New comment-reply path for comments with NO keyword rule match.

WHY THIS EXISTS
---------------
``comment_rules.match()`` returning ``None`` today means the comment is
silently dropped — correct for spam, but it also drops a genuine on-topic
question that just didn't happen to contain a CTA keyword. This module is
the orchestrator wired into that gap (see ``meta_webhook.handle_comment``'s
``rule is None`` branch) — it fires ONLY there, never for a keyword-matched
comment (that path is unchanged, see the regression test in
``tests/test_channels_instagram.py``).

COST SHAPE (see CLAUDE.md-adjacent design doc for the full rationale):
    spam path:    1 LLM call  (comment_triage.classify_and_mirror)
    genuine path: 3 LLM calls (classify_and_mirror + FAQAgent.run +
                                comment_dm_answer.compose_faq_dm)

SHIPS DARK: ``UNMATCHED_COMMENT_REPLY_ENABLED`` defaults to OFF. When off,
this module is a byte-identical no-op to "today" — zero CRM reads, zero
LLM calls, zero outbound sends (see the master-flag test in
``tests/test_unmatched_comment.py``).

ORDERING INVARIANT (do not break): the public topic-mirror is sent ONLY
after the private DM send succeeds — this mirrors the existing
``handle_comment`` invariant ("send public ack after the private path
succeeds so failures do not create public-only spam", see
``meta_webhook.py``). It is additionally gated on
``UNMATCHED_COMMENT_PUBLIC_REPLY_ENABLED`` AND
``comment_triage.mirror_is_safe`` — three independent gates must all pass
before anything is ever posted publicly.

DEDUP: this module relies ENTIRELY on the persistent webhook-event claims
already taken in ``meta_webhook.handle_comment`` (comment_id +
comment-intent key) BEFORE the ``rule is None`` branch is reached — it
does not add a second dedup mechanism (CLAUDE.md instruction: do not
duplicate that idempotency guarantee).

PER-USER LOCK + DAILY-CAP SEMANTICS (2026-07 security/python review fix):
the ENTIRE per-comment sequence (read cap -> gate -> FAQ -> compose ->
send -> record) runs inside a per-``crm_key`` ``asyncio.Lock`` (see
``_lock_for``, mirrors ``src/whatsapp/router.py``'s ``_phone_locks``
pattern) — two comments from the SAME commenter, dispatched as
independent background tasks, must not race the daily-cap
read-modify-write. The cap counter is incremented right after the cap
check passes (BEFORE the first LLM call), not only after a successful
send — the cap means "N processing attempts per user per day," i.e. it
rate-limits LLM spend, not "N successful replies per user per day".
"""

from __future__ import annotations

import asyncio
import logging
import os
import re
from datetime import UTC, datetime
from typing import Any, Final

from src.agents.base import SpecialistInput
from src.agents.comment_dm_answer import compose_faq_dm
from src.agents.registry import SpecialistProtocol
from src.channels import comment_rules, meta_client
from src.channels.comment_triage import classify_and_mirror, mirror_is_safe
from src.channels.meta_events import IncomingComment
from src.crm.models import User
from src.llm import LLMClient
from src.ops_alert import send_ops_alert
from src.orchestrator.pipeline import JessicaPipeline

logger = logging.getLogger("channels.unmatched_comment")

# At least one alphanumeric or CJK character — used to reject
# emoji/punctuation-only comments before any LLM call.
_HAS_REAL_CONTENT_RE: Final[re.Pattern[str]] = re.compile(
    r"[0-9a-zA-Z一-鿿㐀-䶿]"
)

_TRUTHY: Final[frozenset[str]] = frozenset({"1", "true", "yes", "on"})

# Sentinel used when MIN > MAX (misconfigured env vars) — see
# _effective_min_max_text_len.
_UNBOUNDED_MAX_TEXT_LEN: Final[int] = 2**31 - 1


# ---------------------------------------------------------------------------
# DI — mirrors set_chloe_agent / set_social_pipeline in meta_webhook.py
# ---------------------------------------------------------------------------

_client: LLMClient | None = None
_faq_agent: SpecialistProtocol | None = None


def set_unmatched_comment_deps(
    client: LLMClient | None, faq_agent: SpecialistProtocol | None
) -> None:
    """Register the shared LLM client + FAQAgent instance. Called from
    ``web.lifespan`` alongside the other ``set_*`` registrations."""
    global _client, _faq_agent
    _client = client
    _faq_agent = faq_agent


# ---------------------------------------------------------------------------
# Env-tunable clamped constants — mirrors comment_rules.py's
# _fuzzy_threshold / _fuzzy_min_keyword_len / _fuzzy_max_text_len pattern.
# ---------------------------------------------------------------------------


def _reply_enabled() -> bool:
    """Master gate. Defaults OFF — ships dark until explicitly enabled."""
    return os.environ.get("UNMATCHED_COMMENT_REPLY_ENABLED", "0").strip().lower() in _TRUTHY


def _public_reply_enabled() -> bool:
    """Defaults ON — gated behind the master flag + mirror_is_safe anyway."""
    return os.environ.get(
        "UNMATCHED_COMMENT_PUBLIC_REPLY_ENABLED", "1"
    ).strip().lower() in _TRUTHY


def _max_text_len() -> int:
    """Clamped to >= 1 — see comment_rules._fuzzy_max_text_len for why an
    unclamped override would be dangerous (a "0" would silently reject
    every comment, which is at least safe; but future negative values are
    guarded here for consistency)."""
    try:
        value = int(os.environ.get("UNMATCHED_COMMENT_MAX_TEXT_LEN", "300"))
    except ValueError:
        return 300
    return max(1, value)


def _min_text_len() -> int:
    try:
        value = int(os.environ.get("UNMATCHED_COMMENT_MIN_TEXT_LEN", "4"))
    except ValueError:
        return 4
    return max(1, value)


def _max_per_user_per_day() -> int:
    try:
        value = int(os.environ.get("UNMATCHED_COMMENT_MAX_PER_USER_PER_DAY", "2"))
    except ValueError:
        return 2
    return max(0, value)


# ---------------------------------------------------------------------------
# Deterministic pre-filters (no LLM, no CRM)
# ---------------------------------------------------------------------------


def _effective_min_max_text_len() -> tuple[int, int] | None:
    """Returns ``(min_len, max_len)``, or ``None`` if MIN > MAX.

    ``_min_text_len`` / ``_max_text_len`` are each clamped independently
    (>= 1), so a misconfigured pair of env vars (e.g. MIN=50, MAX=10) is
    still possible and would otherwise make the length gate reject EVERY
    comment forever, silently. Simplest safe behavior: detect that case
    and disable the length gate entirely (return ``None``) rather than
    guess at a "corrected" range — logged at WARNING so the
    misconfiguration is visible and gets fixed instead of quietly eating
    all traffic.
    """
    min_len = _min_text_len()
    max_len = _max_text_len()
    if min_len > max_len:
        logger.warning(
            "[unmatched_comment] misconfigured length bounds: MIN (%d) > "
            "MAX (%d) — disabling the length gate entirely rather than "
            "rejecting every comment",
            min_len, max_len,
        )
        return None
    return min_len, max_len


def _length_in_bounds(text: str) -> bool:
    bounds = _effective_min_max_text_len()
    if bounds is None:
        return True
    min_len, max_len = bounds
    return min_len <= len(text) <= max_len


def _has_real_content(text: str) -> bool:
    return bool(_HAS_REAL_CONTENT_RE.search(text))


# ---------------------------------------------------------------------------
# Per-user daily cap (CRM-backed, immutable updates only)
# ---------------------------------------------------------------------------


def _today_key() -> str:
    return datetime.now(UTC).strftime("%Y-%m-%d")


def _reply_count_today(user: User) -> int:
    log = dict(getattr(user, "temp_state", {}) or {}).get("unmatched_reply_log", {})
    return int(log.get(_today_key(), 0)) if isinstance(log, dict) else 0


async def _record_reply_sent(crm: Any, user: User) -> User:
    """Immutable increment of today's reply count, persisted via with_updates.

    Returns the updated ``User`` so the caller keeps working with the fresh
    snapshot instead of the stale pre-increment one.
    """
    state = dict(getattr(user, "temp_state", {}) or {})
    log = dict(state.get("unmatched_reply_log", {}))
    today = _today_key()
    new_log = {**log, today: int(log.get(today, 0)) + 1}
    new_state = {**state, "unmatched_reply_log": new_log}
    updated = user.with_updates(temp_state=new_state)
    await crm.save_user(updated)
    return updated


# ---------------------------------------------------------------------------
# Per-user lock — serializes the whole read-cap -> ... -> record sequence
# for a given crm_key, so two comments from the same commenter processed
# concurrently (each dispatched as an independent background task) cannot
# race the daily-cap read-modify-write. Mirrors
# src/whatsapp/router.py's _phone_locks / _lock_for pattern exactly.
# ---------------------------------------------------------------------------

_user_locks: dict[str, asyncio.Lock] = {}


def _lock_for(crm_key: str) -> asyncio.Lock:
    lock = _user_locks.get(crm_key)
    if lock is None:
        lock = asyncio.Lock()
        _user_locks[crm_key] = lock
    return lock


# ---------------------------------------------------------------------------
# Orchestrator
# ---------------------------------------------------------------------------


async def handle_unmatched_comment(
    comment: IncomingComment, pipeline: JessicaPipeline
) -> None:
    """Genuine-vs-spam gate + mirrored public ack + KB-grounded private DM.

    Fires ONLY from ``meta_webhook.handle_comment``'s ``rule is None``
    branch, AFTER that function's persistent webhook-event dedup claims —
    see this module's docstring for the full invariant list.
    """
    if not _reply_enabled():
        logger.info(
            "[unmatched_comment] master flag disabled — no-op for comment %s",
            comment.comment_id,
        )
        return

    text = (comment.text or "").strip()
    if not _length_in_bounds(text):
        logger.info(
            "[unmatched_comment] comment %s: length %d outside bounds — skipping",
            comment.comment_id, len(text),
        )
        return
    if not _has_real_content(text):
        logger.info(
            "[unmatched_comment] comment %s: emoji/punctuation-only — skipping",
            comment.comment_id,
        )
        return

    lang = comment_rules.expected_language(comment.recipient_id or None)
    if not lang:
        logger.info(
            "[unmatched_comment] comment %s: unregistered account %s — skipping",
            comment.comment_id, comment.recipient_id,
        )
        return

    crm = getattr(pipeline, "_crm", None)
    if crm is None:
        logger.warning(
            "[unmatched_comment] comment %s: pipeline has no CRM — skipping",
            comment.comment_id,
        )
        return

    # Everything from here on touches per-user CRM state (the daily cap
    # counter) and must be atomic per commenter — see module docstring.
    async with _lock_for(comment.crm_key):
        user = await crm.get_or_create_user(comment.crm_key)
        if _reply_count_today(user) >= _max_per_user_per_day():
            logger.info(
                "[unmatched_comment] comment %s: user %s over daily cap — skipping",
                comment.comment_id, comment.crm_key,
            )
            return

        if _client is None:
            logger.warning(
                "[unmatched_comment] no LLM client registered — skipping comment %s",
                comment.comment_id,
            )
            return

        # Increment NOW — we're about to spend at least one LLM call
        # (classify_and_mirror) on this user today regardless of whether
        # this turns out to be spam or unanswerable. The cap means "N
        # processing attempts per user per day," not "N successful
        # replies per user per day" (see module docstring).
        user = await _record_reply_sent(crm, user)

        triage = await classify_and_mirror(text, client=_client, lang=lang)
        if not triage.is_genuine:
            logger.info(
                "[unmatched_comment] comment %s: gated as not genuine (%s) — skipping",
                comment.comment_id, triage.reason,
            )
            return

        if _faq_agent is None:
            logger.warning(
                "[unmatched_comment] no FAQAgent registered — skipping comment %s",
                comment.comment_id,
            )
            return

        faq_input = SpecialistInput(user=user, user_message=text)
        try:
            faq_output, _usage = await _faq_agent.run(faq_input)
            dm_text = await compose_faq_dm(text, faq_output, client=_client, lang=lang)
        except Exception:
            logger.exception(
                "[unmatched_comment] comment %s: FAQ/compose step failed — "
                "skipping (no DM, no public reply)", comment.comment_id,
            )
            await send_ops_alert(
                f"unmatched_comment_faq_failed_{comment.comment_id}",
                f"🟡 unmatched-comment reply pipeline failed composing a DM "
                f"for {comment.platform} comment {comment.comment_id} — "
                f"FAQAgent.run/compose_faq_dm raised. Comment silently "
                f"skipped (no DM, no public reply, dedup key already "
                f"claimed so it will not retry). Check logs for the "
                f"traceback.",
            )
            return

        if not dm_text:
            logger.info(
                "[unmatched_comment] comment %s: nothing groundable to answer with — "
                "skipping (no DM, no public mirror)", comment.comment_id,
            )
            return

        # Defense-in-depth (item 6, security review): the composed DM is
        # private, so lower priority than the public-mirror check below,
        # but cheap insurance against a hallucinated/prompt-injected
        # unsafe DM slipping past compose_faq_dm's prompt-only constraint.
        if not mirror_is_safe(dm_text, lang):
            logger.warning(
                "[unmatched_comment] comment %s: composed DM failed the "
                "deterministic safety check — not sending", comment.comment_id,
            )
            return

        send = await meta_client.send_private_reply(
            comment.comment_id, dm_text, platform=comment.platform,
            account_id=comment.recipient_id or None,
        )
        if not send.ok:
            logger.warning(
                "[unmatched_comment] DM send failed for comment %s: %s — no public mirror",
                comment.comment_id, send.detail,
            )
            return

        # Local import breaks the meta_webhook <-> unmatched_comment import
        # cycle: meta_webhook imports this module at module load time, so
        # this module cannot import meta_webhook at module load time too.
        from src.channels.meta_webhook import _persist_canned_interaction

        await _persist_canned_interaction(
            pipeline,
            crm_key=comment.crm_key,
            inbound_text=text,
            inbound_message_id=comment.comment_id,
            outbound_text=dm_text,
            image_urls=[],
        )

        if _public_reply_enabled() and mirror_is_safe(triage.topic_mirror, lang):
            await meta_client.reply_to_comment(
                comment.comment_id, triage.topic_mirror, platform=comment.platform,
                account_id=comment.recipient_id or None,
            )
