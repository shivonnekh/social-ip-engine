"""Shared Meta (Instagram + Facebook) webhook core.

Both the Instagram and Facebook routers are thin wrappers over this
module — they differ only in URL path, enable-flag, and which product
they were registered for. All the real work lives here:

    * ``verify_subscription``  — GET hub.challenge handshake
    * ``verify_signature``     — X-Hub-Signature-256 validation (fails
                                 closed in production)
    * ``is_duplicate``         — bounded LRU dedup over message/comment ids
    * ``process_post``         — verify → parse → dedup → background dispatch
    * ``handle_dm`` / ``handle_comment`` — pipeline dispatch + reply

DM replies interleave text bubbles with images exactly like the WhatsApp
sender: each ``media_to_send`` entry is grouped by ``after_bubble_idx``
and the image DM is sent right after that bubble.
"""

from __future__ import annotations

import asyncio
import dataclasses
import hashlib
import hmac
import json
import logging
import os
import re
from datetime import datetime
from collections import OrderedDict
from typing import Callable, Final

from src.channels import comment_rules, meta_client, unmatched_comment
from src.channels.chloe_agent import _is_pure_greeting
from src.channels.meta_events import (
    IncomingComment,
    IncomingDM,
    Platform,
    parse_meta_webhook,
)
from src.crm.models import ConversationMessage
from src.ops_alert import send_ops_alert
from src.orchestrator.pipeline import JessicaPipeline
from src.personas.profile import PersonaProfile, load_jackie_profile

logger = logging.getLogger("channels.meta_webhook")

APP_ENV: Final[str] = os.environ.get("APP_ENV", "development").lower()
_BUBBLE_PAUSE_S: Final[float] = 0.6
_MEDIA_PAUSE_S: Final[float] = 0.8
_DEDUP_MAX: Final[int] = 2048


# ---------------------------------------------------------------------------
# Config accessors (read at call time so tests can monkeypatch env)
# ---------------------------------------------------------------------------


def _app_secret() -> str:
    """Instagram-side secret. Instagram API with Instagram Login signs IG
    webhooks with the *Instagram app secret*, stored in ``META_APP_SECRET``."""
    return os.environ.get("META_APP_SECRET", "").strip()


def _fb_app_secret() -> str:
    """Facebook/Messenger secret. Facebook Pages sign webhooks with the
    *Meta app secret* (distinct from the Instagram app secret). Falls back to
    ``META_APP_SECRET`` only if ``FB_APP_SECRET`` is unset (single-app setups)."""
    return os.environ.get("FB_APP_SECRET", "").strip() or _app_secret()


def _verify_token() -> str:
    return os.environ.get("META_VERIFY_TOKEN", "").strip()


# ---------------------------------------------------------------------------
# GET handshake
# ---------------------------------------------------------------------------


def verify_subscription(mode: str, token: str, challenge: str) -> str | None:
    """Return ``challenge`` when the verify token matches, else ``None``."""
    expected = _verify_token()
    if mode == "subscribe" and expected and hmac.compare_digest(token, expected):
        logger.info("[meta] webhook verified")
        return challenge
    logger.warning("[meta] webhook verification failed (mode=%s)", mode)
    return None


# ---------------------------------------------------------------------------
# Signature verification
# ---------------------------------------------------------------------------


def verify_signature(raw: bytes, header: str, *, secret: str | None = None) -> bool:
    """Validate ``X-Hub-Signature-256: sha256=<hex>`` against the app secret.

    ``secret`` lets the caller pick the platform-specific secret (Instagram vs
    Meta app secret). When omitted it defaults to the Instagram secret.
    Production requires a secret (fails closed). Dev with no secret skips
    verification so curl smoke tests work.
    """
    secret = secret if secret is not None else _app_secret()
    if not secret:
        if APP_ENV == "production":
            logger.error("[meta] META_APP_SECRET unset in production — rejecting")
            return False
        return True
    if not header.startswith("sha256="):
        return False
    sent = header.split("=", 1)[1].strip()
    expected = hmac.new(secret.encode(), raw, hashlib.sha256).hexdigest()
    return hmac.compare_digest(sent, expected)


# ---------------------------------------------------------------------------
# Dedup
# ---------------------------------------------------------------------------

_seen_ids: "OrderedDict[str, None]" = OrderedDict()

# Per-account agent registry — keyed by business IG/FB account id.
# When a DM/comment arrives on a known account, its agent handles the reply.
# Falls back to _chloe_agent (default) when no per-account entry exists.
_account_agents: dict[str, object] = {}
_chloe_agent = None  # type: ignore[var-annotated]  # default agent


def set_chloe_agent(agent) -> None:
    """Register the default Chloe agent for IG/FB DMs. Called from web.lifespan."""
    global _chloe_agent
    _chloe_agent = agent


def set_account_agent(account_id: str, agent) -> None:
    """Register a per-account agent (e.g. Jackie for jackiechan.tcm)."""
    _account_agents[account_id] = agent


def _get_agent(account_id: str | None):
    """Return the agent for this account, falling back to the default."""
    if account_id and account_id in _account_agents:
        return _account_agents[account_id]
    return _chloe_agent


# ---------------------------------------------------------------------------
# Social-pipeline feature flag (SOCIAL_PIPELINE_ACCOUNTS)
#
# Opt-in, per-business-account routing to the profile-driven JessicaPipeline
# (Planner -> Specialists -> Writer, KB-grounded) instead of ChloeAgent's
# single-LLM-call model. Empty/unset SOCIAL_PIPELINE_ACCOUNTS = today's
# ChloeAgent behavior for every account (zero-risk default). See
# ``_dispatch_dm_profile_pipeline`` for the dispatch logic + fallback.
# ---------------------------------------------------------------------------

_social_pipeline: JessicaPipeline | None = None


def set_social_pipeline(pipeline: JessicaPipeline) -> None:
    """Register the shared JessicaPipeline for the profile-pipeline DM path.

    Called from ``web.lifespan`` — mirrors ``set_chloe_agent`` /
    ``set_account_agent``'s registration pattern. This is the SAME
    pipeline instance already backing WhatsApp (and the dormant
    Jessica-pipeline fallback branch in ``_dispatch_dm``); registering it
    explicitly here keeps the profile-pipeline path's dependency clear
    and independent of the `pipeline` param threaded through `_dispatch_dm`.
    """
    global _social_pipeline
    _social_pipeline = pipeline


def _social_pipeline_accounts() -> frozenset[str]:
    """Business account ids opted into the profile-pipeline path."""
    raw = os.environ.get("SOCIAL_PIPELINE_ACCOUNTS", "")
    return frozenset(a.strip() for a in raw.split(",") if a.strip())


def _account_profile_loaders() -> dict[str, Callable[[], PersonaProfile]]:
    """Business account id -> PersonaProfile loader.

    Extend THIS mapping (not the dispatch logic in
    ``_dispatch_dm_profile_pipeline``) to opt additional accounts/personas
    into the profile-pipeline path later — e.g. Chloe's own IG account id
    -> ``load_chloe_profile``. Jackie is the only entry today.
    """
    loaders: dict[str, Callable[[], PersonaProfile]] = {}
    jackie_id = os.environ.get("IG_USER_ID_JACKIE", "").strip()
    if jackie_id:
        loaders[jackie_id] = load_jackie_profile
    return loaders


def _profile_for_account(account_id: str | None) -> PersonaProfile | None:
    """Resolve the PersonaProfile for an account id, or None if unmapped.

    A None return is treated as a failure by the caller (falls back to
    ChloeAgent) — an account should not be listed in
    SOCIAL_PIPELINE_ACCOUNTS without a matching profile, but we never
    assume that invariant holds in production.
    """
    if not account_id:
        return None
    loader = _account_profile_loaders().get(account_id)
    return loader() if loader else None


# Merge buffer — debounces rapid-fire DM fragments into one turn (lazy init).
_merge_buffer = None  # type: ignore[var-annotated]


def _get_merge_buffer(pipeline: JessicaPipeline):
    """Lazily build the per-process merge buffer bound to the dispatcher."""
    global _merge_buffer
    if _merge_buffer is None:
        from src.channels.merge_buffer import MergeBuffer

        async def _on_flush(dm: IncomingDM) -> None:
            await _dispatch_dm(dm, pipeline)

        _merge_buffer = MergeBuffer(
            window_s=float(os.environ.get("CHLOE_MERGE_WINDOW_S", "5.0")),
            max_s=float(os.environ.get("CHLOE_MERGE_MAX_S", "20.0")),
            on_flush=_on_flush,
        )
    return _merge_buffer


def reset_merge_buffer() -> None:
    """Test hook — drop the buffer so a fresh window/on_flush is built."""
    global _merge_buffer
    _merge_buffer = None


def is_duplicate(event_id: str) -> bool:
    if not event_id:
        return False
    if event_id in _seen_ids:
        return True
    _seen_ids[event_id] = None
    if len(_seen_ids) > _DEDUP_MAX:
        _seen_ids.popitem(last=False)
    return False


def is_own_comment(comment: IncomingComment) -> bool:
    """True when ``comment`` was authored by one of our own business
    accounts (e.g. a public_ack reply we posted) rather than a real user.

    Public (not underscore-prefixed) because it's now a real cross-module
    contract: the live webhook path (below) AND both comment-backfill tools
    (``scripts/backfill_comments.py``, ``POST /admin/backfill-comments`` in
    ``src/web.py``) all need it — those tools replay a media's FULL comment
    list via the Graph API, which includes our own ack replies, and an ack's
    text can legitimately contain a rule's keyword substring (e.g. "...
    anxiety guide..." matching the "anxiety" rule) — without this guard a
    replay misfires the rule against ourselves.
    """
    own_ids = {
        os.environ.get("IG_USER_ID", "").strip(),
        os.environ.get("IG_USER_ID_JACKIE", "").strip(),
        os.environ.get("FB_PAGE_ID", "").strip(),
        comment.recipient_id or "",
    }
    own_ids.discard("")
    return bool(comment.from_id and comment.from_id in own_ids)


_is_own_comment = is_own_comment  # back-compat alias — prefer the public name above


def _comment_intent_key(comment: IncomingComment) -> str:
    text = " ".join((comment.text or "").casefold().split())[:160]
    return ":".join([
        comment.platform,
        comment.recipient_id or "unknown_account",
        comment.media_id or "unknown_media",
        comment.from_id or "unknown_user",
        text or "empty",
    ])


async def _claim_webhook_event(event_id: str, kind: str, pipeline: JessicaPipeline) -> bool:
    """Persistently claim a Meta event before causing outbound side effects.

    The in-memory LRU only protects one process. Meta may retry webhooks after
    a restart or while a deploy is rolling, so comments also need a DB-backed
    idempotency key before we public-reply or DM. Tests/fakes without a CRM
    keep the old in-memory-only behavior.
    """
    crm = getattr(pipeline, "_crm", None)
    claim = getattr(crm, "try_claim_webhook_event", None)
    if claim is None:
        return True
    key = f"meta:{kind}:{event_id}"
    try:
        return bool(await claim(key, kind))
    except Exception:  # noqa: BLE001
        logger.exception("[meta] webhook idempotency claim failed for %s", key)
        return False


# ---------------------------------------------------------------------------
# POST processing
# ---------------------------------------------------------------------------


async def process_post(
    *,
    raw: bytes,
    signature_header: str,
    pipeline: JessicaPipeline | None,
    enabled: bool,
    app_secret: str | None = None,
    platform: str = "unknown",
) -> tuple[dict, int]:
    """Verify + parse + dispatch. Returns ``(json_body, status_code)``.

    ``app_secret`` selects the platform secret for signature verification
    (Facebook passes the Meta app secret; Instagram leaves it ``None`` to use
    the Instagram secret). ``platform`` is display-only (alert message /
    debounce key) — it does not affect verification or dispatch. The router
    just wraps the return value in a ``JSONResponse``. We always prefer a
    200 once the payload is authentic so Meta doesn't disable the
    subscription on transient downstream issues.
    """
    if not enabled:
        # Silent by design from Meta's POV (still 200 so it doesn't disable
        # the subscription) but NOT silent in our own logs anymore — this
        # exact "no error anywhere, events just vanish" shape caused a
        # multi-day outage on 2026-07-01/02 (see CLAUDE.md). One line here
        # would have cut that from days to minutes. Also alert (debounced
        # per platform — Meta redelivers in bursts) so someone finds out
        # within the cooldown window instead of when a lead complains.
        logger.warning("[meta] %s webhook disabled — dropping payload (200 OK returned to Meta)", platform)
        _spawn(send_ops_alert(
            f"webhook_disabled_{platform}",
            f"🔴 {platform} webhook is DISABLED — inbound comments/DMs are being "
            f"silently dropped (200 OK returned to Meta so the subscription "
            f"stays alive, but nothing is being processed). Check "
            f"{'IG_ENABLED' if platform == 'instagram' else 'FB_ENABLED'} in the Render dashboard.",
        ))
        return {"status": "disabled"}, 200

    if not verify_signature(raw, signature_header, secret=app_secret):
        return {"error": "bad signature"}, 401

    try:
        payload = json.loads(raw.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError):
        return {"error": "invalid json"}, 400

    events = parse_meta_webhook(payload)
    if not events:
        logger.info("[meta] webhook payload parsed to zero actionable events — ignoring")
        return {"status": "ignored"}, 200

    if pipeline is None:
        logger.error("[meta] pipeline not initialised — dropping %d event(s)", len(events))
        return {"status": "no_pipeline"}, 503

    queued = 0
    for event in events:
        if isinstance(event, IncomingDM):
            if event.is_echo or is_duplicate(event.message_id) or not event.text.strip():
                continue
            _spawn(handle_dm(event, pipeline))
            queued += 1
        elif isinstance(event, IncomingComment):
            # These two checks need only comment_id/parent_id — never Graph
            # API I/O — so they stay synchronous here, same ordering
            # guarantee as before (protects against a duplicate webhook
            # delivery racing itself across concurrent requests).
            if event.is_reply_to_comment:
                logger.info("[meta] comment %s: is a reply-to-comment — skipping", event.comment_id)
                continue
            if is_duplicate(event.comment_id):
                logger.info("[meta] comment %s: duplicate delivery — skipping", event.comment_id)
                continue
            # from_id may be missing (see meta_events._parse_changes) and
            # recovering it needs a Graph API round trip — do that + the
            # remaining from_id-dependent check (is_own_comment) inside the
            # spawned background task instead of awaiting it here, so a slow
            # or timed-out Graph call never delays the 200 OK we owe Meta.
            _spawn(_dispatch_comment(event, pipeline))
            queued += 1

    return {"status": "queued", "count": queued}, 200


async def _dispatch_comment(comment: IncomingComment, pipeline: JessicaPipeline) -> None:
    """Background entry point for one comment event: backfill ``from`` if
    the webhook omitted it, apply the from_id-dependent own-comment guard,
    then run the real handler. Runs off the request path (see process_post)
    so a slow/timed-out Graph API backfill call never blocks Meta's ack."""
    if not comment.from_id:
        comment = await _backfill_comment_from(comment)
        if not comment.from_id:
            logger.warning(
                "[meta] comment %s: still no 'from_id' after Graph API "
                "backfill attempt — dropping (cannot dedup-by-user or "
                "build a CRM key safely)", comment.comment_id,
            )
            # Rare (both the webhook AND a direct Graph API GET missing
            # 'from' means something is genuinely wrong — deleted account,
            # Meta API trouble, or a new failure mode this code doesn't
            # know about yet) — worth a human looking, not just a log line.
            # POST /admin/backfill-comments (media_ids=[comment.media_id])
            # is the manual recovery path once someone sees this.
            await send_ops_alert(
                f"comment_dropped_{comment.comment_id}",
                f"🟡 {comment.platform} comment {comment.comment_id} on media "
                f"{comment.media_id} was dropped — webhook omitted 'from' "
                f"AND a Graph API backfill fetch also couldn't recover it. "
                f"Recover manually: POST /admin/backfill-comments "
                f'{{"media_ids": ["{comment.media_id}"]}}',
            )
            return
    if is_own_comment(comment):
        logger.info("[meta] comment %s: is our own comment — skipping", comment.comment_id)
        return
    await handle_comment(comment, pipeline)


async def _backfill_comment_from(comment: IncomingComment) -> IncomingComment:
    """Recover a missing ``from`` via one Graph API GET when Meta's webhook
    payload omitted it (see ``meta_events._parse_changes``). Returns the same
    event unchanged (still empty ``from_id``) if the fetch can't recover it —
    callers must handle that case, this never raises.
    """
    from_id, from_username = await meta_client.get_comment_from(
        comment.comment_id, platform=comment.platform, account_id=comment.recipient_id or None,
    )
    if not from_id:
        return comment
    logger.info(
        "[meta] comment %s: backfilled from_id=%s via Graph API (webhook omitted it)",
        comment.comment_id, from_id,
    )
    return dataclasses.replace(comment, from_id=from_id, from_username=from_username)


# ---------------------------------------------------------------------------
# Dispatch handlers
# ---------------------------------------------------------------------------


async def handle_dm(dm: IncomingDM, pipeline: JessicaPipeline) -> None:
    """Entry point for an inbound DM — pushes it into the merge buffer.

    Rapid-fire fragments from one user are debounced and combined into a
    single turn (see ``merge_buffer``). When buffering is off the fragment
    dispatches immediately. The actual reply logic is ``_dispatch_dm``.
    """
    await _get_merge_buffer(pipeline).submit(dm)


# Words allowed AROUND a keyword for the DM to still count as a bare
# trigger ("eye pls", "want gut guide"). Anything else in the message
# means the user is saying something real — route to the agent.
_TRIGGER_FILLER_WORDS = frozenset({
    # courtesy / greeting
    "pls", "please", "plz", "thanks", "thank", "you", "ty",
    "hi", "hello", "hey", "yo", "ok", "okay",
    # request framing
    "want", "send", "give", "get", "have", "need", "share",
    "can", "may", "me", "i", "a", "an", "the", "this", "that",
    # the thing being requested
    "guide", "guides", "info", "protocol", "tips",
})
# CJK equivalent — request framing + particles + "guide/懶人包" nouns.
_TRIGGER_FILLER_CJK = frozenset(
    "我要想俾比畀唔該麻煩請份個嗰啊呀啦喇喎嘅資料懶人包指南攻略貼士圖"
)


def _is_bare_keyword_trigger(text: str, keyword: str) -> bool:
    """True when a DM is essentially a keyword trigger ("eye", "gut pls",
    "want eye guide") rather than a genuine message that merely contains
    a keyword substring.

    Approach: remove the keyword, then everything left must be filler
    (courtesy/request words, particles, emoji, punctuation). This catches
    English statements ("my eye hurts"), English questions ("what about
    dark under-eye circle?") AND punctuation-less Cantonese questions
    ("眼點算好") — all of which must reach the agent.

    Regression guard for the 2026-07-02 incident: a real question
    substring-matched the ``eye`` rule and received the canned guide
    (again) instead of a real answer.
    """
    stripped = (text or "").strip()
    if not stripped or not keyword:
        return False
    if "?" in stripped or "？" in stripped:
        return False
    remainder = stripped.lower().replace(keyword.lower(), " ")
    # Latin words left over must all be filler.
    for word in re.findall(r"[a-z']+", remainder):
        if word.strip("'") not in _TRIGGER_FILLER_WORDS:
            return False
    # CJK characters left over must all be filler.
    for ch in remainder:
        if "一" <= ch <= "鿿" and ch not in _TRIGGER_FILLER_CJK:
            return False
    return True


async def _should_send_canned_for_dm(
    dm: IncomingDM, pipeline: JessicaPipeline, rule=None
) -> bool:
    """Only use keyword canned guides to open a DM conversation.

    Once the user has CRM history, the social agent should continue naturally
    instead of looping back into the same protocol prompt whenever a keyword is
    mentioned again. Additionally, the same guide is never sent twice to one
    user (``temp_state.guides_sent``) — this holds even when conversation
    history is missing, e.g. when a backfill run persisted elsewhere.
    """
    crm = getattr(pipeline, "_crm", None)
    if crm is None:
        return True
    try:
        user = await crm.get_user(dm.crm_key)
    except Exception:  # noqa: BLE001
        logger.exception("[meta] failed to check CRM history for %s", dm.crm_key)
        return False
    if user is None:
        return True
    history = list(getattr(user, "conversation_history", []) or [])
    state = dict(getattr(user, "temp_state", {}) or {})
    if rule is not None and rule.keyword in state.get("guides_sent", []):
        return False
    return not history and not state.get("meta_pending_guide_images")


async def _dispatch_dm(dm: IncomingDM, pipeline: JessicaPipeline) -> None:
    """Reply to a (possibly merged) DM. Routes to Chloe when registered;
    otherwise falls back to the Jessica pipeline. Text + images interleave."""
    if await _send_pending_guide_images(dm, pipeline):
        return

    # Keyword guide short-circuit — a bare "gut"/"eye" DM sends the canned
    # guide (images) directly, skipping the LLM. Same rules as comments.
    # Genuine sentences/questions containing a keyword go to the agent.
    rule = comment_rules.match(dm.text, account_id=dm.recipient_id)
    if (
        rule is not None
        and not rule.use_agent
        and _is_bare_keyword_trigger(dm.text, rule.keyword)
        and await _should_send_canned_for_dm(dm, pipeline, rule)
    ):
        await _persist_canned_interaction(
            pipeline,
            crm_key=dm.crm_key,
            inbound_text=dm.text,
            inbound_message_id=dm.message_id,
            outbound_text=rule.dm_text,
            image_urls=rule.all_images,
            keyword=rule.keyword,
        )
        await _send_canned_to_user(
            dm.sender_id, rule, platform=dm.platform, account_id=dm.recipient_id
        )
        return

    if dm.recipient_id in _social_pipeline_accounts():
        if await _dispatch_dm_profile_pipeline(dm):
            return
        # Profile-pipeline path failed (exception, or unmapped account) —
        # fall through to the ChloeAgent safety net below so the user is
        # never left without a reply.

    _agent = _get_agent(dm.recipient_id)
    if _agent is not None:
        try:
            reply = await _agent.respond(
                crm_key=dm.crm_key, user_message=dm.text, message_id=dm.message_id
            )
            bubbles = [b for b in reply.bubbles if b.strip()]
            media_by_idx = _group_media(reply.media)
        except Exception:  # noqa: BLE001
            logger.exception("[meta] agent failed for %s", dm.crm_key)
            return
    else:
        try:
            result = await pipeline.run_turn(
                phone=dm.crm_key,
                user_message=dm.text,
                wa_message_id=dm.message_id,
            )
        except Exception:  # noqa: BLE001
            logger.exception("[meta] pipeline failed for %s", dm.crm_key)
            return
        bubbles = [b for b in (result.writer_output.bubbles or []) if b.strip()]
        media_by_idx = _group_media(result.writer_output.media_to_send or [])

    await _send_dm_bubbles(dm, bubbles, media_by_idx)


async def _send_dm_bubbles(
    dm: IncomingDM, bubbles: list[str], media_by_idx: dict[int, list[str]]
) -> None:
    """Send bubbles + interleaved media to a DM recipient.

    Shared send cadence for every DM reply path in this module (ChloeAgent,
    the dormant Jessica-pipeline fallback, and the new profile-pipeline
    path) — one bubble at a time, images grouped right after the bubble
    they follow, paused between sends.
    """
    for i, bubble in enumerate(bubbles):
        send = await meta_client.send_dm(
            dm.sender_id, bubble, platform=dm.platform, account_id=dm.recipient_id
        )
        if not send.ok:
            logger.warning("[meta] DM bubble send failed: %s", send.detail)
            break
        for url in media_by_idx.get(i, []):
            await asyncio.sleep(_MEDIA_PAUSE_S)
            img = await meta_client.send_dm_image(
                dm.sender_id, url, platform=dm.platform, account_id=dm.recipient_id
            )
            if not img.ok:
                logger.warning("[meta] DM image send failed: %s", img.detail)
        if i < len(bubbles) - 1:
            await asyncio.sleep(_BUBBLE_PAUSE_S)


def _shift_media_by_idx(
    media_by_idx: dict[int, list[str]], offset: int
) -> dict[int, list[str]]:
    """Return a NEW media-by-bubble-index mapping shifted by ``offset``.

    Used when greeting bubbles are prepended ahead of the pipeline's own
    answer bubbles — the Writer's media indices are relative to its own
    bubble list, so they must shift by however many greeting bubbles now
    precede them.
    """
    if not offset:
        return dict(media_by_idx)
    return {idx + offset: list(urls) for idx, urls in media_by_idx.items()}


async def _dispatch_dm_profile_pipeline(dm: IncomingDM) -> bool:
    """Profile-driven pipeline path (Planner -> Specialists -> Writer,
    KB-grounded) for accounts opted into SOCIAL_PIPELINE_ACCOUNTS.

    Mirrors ``ChloeAgent.respond()``'s greeting-first / first-touch
    semantics so the user experience does not regress relative to today's
    live ChloeAgent path:
      * First-touch is keyed off "does the CRM row exist" (NOT
        history-empty — a persist hiccup can read empty history and cause
        repeat greetings; same reasoning as ``ChloeAgent.respond()``).
      * A first-touch PURE greeting gets ONLY the persona's greeting
        bubbles (+ optional greeting media), verbatim — no LLM/pipeline
        call, mirroring ChloeAgent's fast path.
      * Otherwise the pipeline runs; greeting bubbles are prepended first
        if this is still the user's first (non-greeting) message.

    Returns True once the reply has been sent (including the "greeting
    bubbles only" fast path). Returns False on ANY failure (exception, or
    an unmapped account/pipeline) — the caller MUST then fall back to
    ``ChloeAgent.respond()`` for this same turn so the user is never left
    without a reply.
    """
    pipeline = _social_pipeline
    profile = _profile_for_account(dm.recipient_id)
    if pipeline is None or profile is None:
        logger.warning(
            "[meta] account %s is in SOCIAL_PIPELINE_ACCOUNTS but has no "
            "registered pipeline/profile — falling back to ChloeAgent",
            dm.recipient_id,
        )
        return False

    try:
        crm = getattr(pipeline, "_crm", None)
        existing = await crm.get_user(dm.crm_key) if crm is not None else None
        is_first_touch = existing is None
        logger.info(
            "[meta] profile-pipeline turn key=%s profile=%s first_touch=%s",
            dm.crm_key, profile.key, is_first_touch,
        )

        if is_first_touch and _is_pure_greeting(dm.text):
            bubbles = [b for b in profile.greeting_bubbles if b.strip()]
            media_by_idx: dict[int, list[str]] = {}
            if profile.greeting_media_url:
                media_by_idx[max(0, len(bubbles) - 1)] = [profile.greeting_media_url]
        else:
            result = await pipeline.run_turn(
                phone=dm.crm_key,
                user_message=dm.text,
                profile=profile,
                wa_message_id=dm.message_id,
            )
            answer_bubbles = [
                b for b in (result.writer_output.bubbles or []) if b.strip()
            ]
            answer_media = _group_media(result.writer_output.media_to_send or [])

            greeting_bubbles = list(profile.greeting_bubbles) if is_first_touch else []
            media_by_idx = _shift_media_by_idx(answer_media, len(greeting_bubbles))
            if is_first_touch and profile.greeting_media_url:
                greet_idx = max(0, len(greeting_bubbles) - 1)
                media_by_idx = {
                    **media_by_idx,
                    greet_idx: [profile.greeting_media_url, *media_by_idx.get(greet_idx, [])],
                }

            bubbles = [b for b in greeting_bubbles + answer_bubbles if b.strip()]
            # Safety cap — the shared Writer's own bubble_cap is a fixed
            # MAX_BUBBLES / MAX_BUBBLES_PITCH constant (src/agents/writer.py),
            # NOT profile.max_bubbles, so a persona's bubble cap is not
            # actually enforced upstream today. Enforce it here so the
            # persona's reply-shape limit always holds regardless of what
            # the shared Writer internals decide to do.
            cap = len(greeting_bubbles) + profile.max_bubbles
            bubbles = bubbles[: max(1, cap)]

        await _send_dm_bubbles(dm, bubbles, media_by_idx)
        return True
    except Exception:  # noqa: BLE001
        logger.exception(
            "[meta] profile-pipeline failed for %s, falling back to ChloeAgent",
            dm.crm_key,
        )
        return False


async def handle_comment(comment: IncomingComment, pipeline: JessicaPipeline) -> None:
    """Comment → DM, driven by ``comment_rules`` (canned-first).

    A keyword match resolves to a rule. By default the rule sends a FIXED
    DM (text + optional image) — no agent, because for a CTA we already
    know what the lead wants. Only ``use_agent: true`` rules run the
    pipeline. No matching rule ⇒ we stay silent (don't auto-DM strangers).
    """
    if comment.is_reply_to_comment or is_own_comment(comment):
        logger.info("[meta] ignoring own/reply comment %s", comment.comment_id)
        return
    if not await _claim_webhook_event(comment.comment_id, "comment", pipeline):
        logger.info("[meta] duplicate comment %s — already handled", comment.comment_id)
        return
    intent_key = _comment_intent_key(comment)
    if not await _claim_webhook_event(intent_key, "comment_intent", pipeline):
        logger.info("[meta] duplicate comment intent %s — already handled", intent_key)
        return

    rule = comment_rules.match(comment.text, account_id=comment.recipient_id or None)
    if rule is None:
        logger.info("[meta] comment %s: no rule match — skipping", comment.comment_id)
        await unmatched_comment.handle_unmatched_comment(comment, pipeline)
        return

    if rule.use_agent:
        sent = await _comment_via_agent(comment, pipeline)
    else:
        sent = await _comment_via_canned(comment, rule, pipeline)

    # Optional public acknowledgement on the thread (per-rule). Send it after
    # the private path succeeds so failures do not create public-only spam.
    if sent and rule.public_ack:
        await meta_client.reply_to_comment(
            comment.comment_id, rule.public_ack, platform=comment.platform,
            account_id=comment.recipient_id or None,
        )


async def _comment_via_canned(
    comment: IncomingComment, rule, pipeline: JessicaPipeline | None = None
) -> bool:
    """Send the predefined DM for this keyword — no LLM call.

    The first message is a private reply (comment→DM). Any images then
    follow as normal DMs to the commenter (recipient by id).
    """
    if rule.dm_text:
        send = await meta_client.send_private_reply(
            comment.comment_id, rule.dm_text, platform=comment.platform,
            account_id=comment.recipient_id or None,
        )
        if not send.ok:
            logger.warning("[meta] canned private reply failed: %s", send.detail)
            return False
    if pipeline is not None:
        await _persist_canned_interaction(
            pipeline,
            crm_key=comment.crm_key,
            inbound_text=comment.text,
            inbound_message_id=comment.comment_id,
            outbound_text=rule.dm_text,
            image_urls=rule.all_images,
            pending_images=True,
            keyword=rule.keyword,
        )
    return True


async def _send_canned_to_user(
    recipient_id: str, rule, *, platform, account_id: str | None = None
) -> None:
    """Send a canned keyword reply (text + images) straight to a DM user."""
    if rule.dm_text:
        await meta_client.send_dm(
            recipient_id, rule.dm_text, platform=platform, account_id=account_id
        )
    for url in rule.all_images:
        await asyncio.sleep(_MEDIA_PAUSE_S)
        img = await meta_client.send_dm_image(
            recipient_id, url, platform=platform, account_id=account_id
        )
        if not img.ok:
            logger.warning("[meta] canned DM image failed: %s", img.detail)


async def _comment_via_agent(comment: IncomingComment, pipeline: JessicaPipeline) -> bool:
    """Run the pipeline on the comment text; send the joined reply as one DM."""
    try:
        result = await pipeline.run_turn(
            phone=comment.crm_key,
            user_message=comment.text,
            wa_message_id=comment.comment_id,
        )
    except Exception:  # noqa: BLE001
        logger.exception("[meta] pipeline failed for comment %s", comment.comment_id)
        return False

    bubbles = [b for b in (result.writer_output.bubbles or []) if b.strip()]
    if not bubbles:
        return False

    joined = "\n\n".join(bubbles)
    send = await meta_client.send_private_reply(
        comment.comment_id, joined, platform=comment.platform,
        account_id=comment.recipient_id or None,
    )
    if not send.ok:
        logger.warning("[meta] agent private reply failed: %s", send.detail)
        return False
    return True


async def _comment_via_account_agent(comment: IncomingComment) -> bool:
    """Catch-all DM for accounts with a registered ChloeAgent (e.g. Jackie).

    Uses the commenter's IG id as the CRM key so each unique commenter gets
    their own conversation thread. Sends greeting + first response as a
    private reply (comment→DM) linked to the original comment.
    """
    _agent = _get_agent(comment.recipient_id or None)
    if _agent is None:
        return False
    try:
        reply = await _agent.respond(
            crm_key=comment.crm_key,
            user_message=comment.text,
            message_id=comment.comment_id,
        )
        bubbles = [b for b in reply.bubbles if b.strip()]
    except Exception:  # noqa: BLE001
        logger.exception("[meta] account agent failed for comment %s", comment.comment_id)
        return False

    if not bubbles:
        return False

    # Send greeting + reply as a private reply (appears as DM linked to comment).
    for i, bubble in enumerate(bubbles):
        if i == 0:
            send = await meta_client.send_private_reply(
                comment.comment_id, bubble, platform=comment.platform,
                account_id=comment.recipient_id or None,
            )
        else:
            # Subsequent bubbles go as regular DMs to the commenter.
            if not comment.from_id:
                break
            send = await meta_client.send_dm(
                comment.from_id, bubble, platform=comment.platform,
                account_id=comment.recipient_id or None,
            )
        if not send.ok:
            logger.warning("[meta] account agent DM bubble %d failed: %s", i, send.detail)
            return False
        if i < len(bubbles) - 1:
            await asyncio.sleep(_BUBBLE_PAUSE_S)
    return True


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


async def _send_pending_guide_images(dm: IncomingDM, pipeline: JessicaPipeline) -> bool:
    """Send queued guide images, then let the agent continue the conversation.

    Instagram may allow the first comment→DM text but reject immediate follow-up
    media while the thread is still in a message-request state. Once the user
    replies in DM, they have opened the conversation, so we send queued protocol
    images first, clear the pending state, and then still allow the LLM to reply
    naturally on the same turn.
    """
    crm = getattr(pipeline, "_crm", None)
    if crm is None:
        return False
    try:
        user = await crm.get_user(dm.crm_key)
    except Exception:  # noqa: BLE001
        logger.exception("[meta] failed to load pending guide state for %s", dm.crm_key)
        return False
    state = dict(getattr(user, "temp_state", {}) or {}) if user is not None else {}
    urls = [u for u in state.get("meta_pending_guide_images", []) if isinstance(u, str)]
    if not urls:
        return False

    await _persist_canned_interaction(
        pipeline,
        crm_key=dm.crm_key,
        inbound_text=dm.text,
        inbound_message_id=dm.message_id,
        outbound_text="[sent pending guide images]",
        image_urls=urls,
    )
    for url in urls:
        await asyncio.sleep(_MEDIA_PAUSE_S)
        img = await meta_client.send_dm_image(
            dm.sender_id, url, platform=dm.platform, account_id=dm.recipient_id
        )
        if not img.ok:
            logger.warning("[meta] pending guide image failed url=%s: %s", url, img.detail)

    if user is not None:
        state.pop("meta_pending_guide_images", None)
        state.pop("meta_pending_guide_text", None)
        try:
            await crm.save_user(user.with_updates(temp_state=state))
        except Exception:  # noqa: BLE001
            logger.exception("[meta] failed to clear pending guide state for %s", dm.crm_key)
    return False


async def _persist_canned_interaction(
    pipeline: JessicaPipeline,
    *,
    crm_key: str,
    inbound_text: str,
    inbound_message_id: str | None,
    outbound_text: str,
    image_urls: list[str],
    pending_images: bool = False,
    keyword: str | None = None,
) -> None:
    """Store canned guide exchanges so later agent replies have context."""
    crm = getattr(pipeline, "_crm", None)
    if crm is None:
        return
    try:
        user = await crm.get_or_create_user(crm_key)
        state = dict(getattr(user, "temp_state", {}) or {})
        state_dirty = False
        if pending_images and image_urls:
            state["meta_pending_guide_images"] = list(image_urls)
            state["meta_pending_guide_text"] = outbound_text
            state_dirty = True
        if keyword:
            already = [s for s in state.get("guides_sent", []) if isinstance(s, str)]
            if keyword not in already:
                state["guides_sent"] = [*already, keyword]
                state_dirty = True
        if state_dirty:
            await crm.save_user(user.with_updates(temp_state=state))
        now = datetime.utcnow()
        await crm.append_message(
            crm_key,
            ConversationMessage(
                role="user",
                content=inbound_text,
                at=now,
                wa_message_id=inbound_message_id,
            ),
        )
        if outbound_text or image_urls:
            await crm.append_message(
                crm_key,
                ConversationMessage(
                    role="chloe",
                    content=outbound_text or "[sent guide images]",
                    media_urls=list(image_urls),
                    at=now,
                ),
            )
    except Exception:  # noqa: BLE001
        logger.exception("[meta] failed to persist canned interaction for %s", crm_key)


def _group_media(media_to_send: list[dict]) -> dict[int, list[str]]:
    """Group absolute image URLs by the bubble index they follow."""
    by_idx: dict[int, list[str]] = {}
    for m in media_to_send:
        url = (m.get("url") or "").strip()
        if not url.startswith(("http://", "https://")):
            continue
        try:
            idx = int(m.get("after_bubble_idx") or 0)
        except (TypeError, ValueError):
            idx = 0
        by_idx.setdefault(idx, []).append(url)
    return by_idx


# Background task helper — keep refs so tasks aren't GC'd mid-flight.
_bg_tasks: set[asyncio.Task] = set()


def _spawn(coro) -> None:
    task = asyncio.create_task(coro)
    _bg_tasks.add(task)
    task.add_done_callback(_bg_tasks.discard)
