"""fb_publish.py — Facebook Page Reels publish via the Graph API resumable
upload flow.

Mirrors ``ig_publish.py``'s public 3-function contract (create/poll/publish)
so ``notion_publish_runner.py`` can drive both platforms through the same
generalized create->poll->publish loop — but the actual sequence underneath
has one MORE real HTTP call than Instagram's, because Facebook separates
"open an upload session" from "transfer the video" into two calls where
Instagram's ``POST /{ig-user-id}/media`` does both in one.

THE REAL FLOW (verified against the LIVE Graph API this session, not just
docs — see shello.md 2026-07-08 session notes for the exact request/response
pairs captured)
-------------------------------------------------------------------------
1. **start** — ``POST /{page-id}/video_reels`` with ``upload_phase=start``.
   Returns ``{video_id, upload_url}`` immediately. No video attached yet.
2. **transfer** — ``POST {upload_url}`` with headers
   ``Authorization: OAuth <token>`` and ``file_url: <public video url>``.
   This is Meta's "transfer by URL" resumable-upload mode: Meta fetches the
   video server-side from the given URL, the SAME "point at an
   already-public URL" shape Instagram uses — no binary streaming needed on
   our end. Confirmed live: returns ``{"success": true}`` once the fetch
   completes (synchronous from the caller's perspective for a small file;
   for a real Reel-length video this may take longer, hence a real timeout
   budget below).
3. **poll** — ``GET /{video_id}?fields=status``. The interesting field is
   ``status.video_status``; observed live value right after step 2 is
   ``"upload_complete"`` (not yet processed/published — that only starts
   once ``finish`` is called in step 4). Treated as "finished" for polling
   purposes because it's the signal that we may now call ``finish``.
4. **finish** — ``POST /{page-id}/video_reels`` with ``upload_phase=finish``,
   ``video_id``, ``video_state=PUBLISHED``, ``description=<caption>``. This
   is the point of no return — it triggers Meta's processing AND publish in
   one call. There is no separate "media_publish" step the way Instagram
   has; ``video_id`` IS the eventual media id, there's no second id to
   extract from the finish response.

``create_reel_container`` below bundles steps 1+2 into one awaitable so the
public contract still has exactly 3 functions, matching what
``notion_publish_runner`` already expects from ``ig_publish``. ``cover_url``
is accepted for signature parity with ``ig_publish.create_reel_container``
but Facebook's ``video_reels`` start phase has no cover-image parameter —
it is intentionally ignored (logged at debug, not silently dropped).

This module has NO knowledge of Notion, no retry/idempotency policy, and no
opinion on what to do with a failed publish — same design boundary as
``ig_publish.py``.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Final

import httpx

from src.channels.meta_client import _creds, _graph_url

logger = logging.getLogger("channels.fb_publish")

_TIMEOUT_S: Final[float] = 60.0  # transfer-by-URL can take longer than a simple API call
_STATUS_FIELDS: Final[str] = "status"

# Observed live ``status.video_status`` values (2026-07-08). "error" is the
# only confirmed terminal-failure value seen in Meta's docs for this field;
# treat any status we don't recognise as still-in-progress (never silently
# treat an unknown status as terminal failure — that would abandon a video
# that might still succeed).
STATUS_UPLOAD_COMPLETE: Final[str] = "upload_complete"
STATUS_ERROR: Final[str] = "error"
_TERMINAL_FAILURE_STATUSES: Final[frozenset[str]] = frozenset({STATUS_ERROR})


@dataclass(frozen=True)
class ContainerResult:
    """Outcome of the start+transfer sequence. ``ok`` is the only thing
    callers must branch on; ``creation_id`` (the FB ``video_id``) is set on
    success. ``detail`` never contains the token."""

    ok: bool
    creation_id: str = ""
    detail: str = ""


@dataclass(frozen=True)
class StatusResult:
    """Outcome of one status poll. ``status_code`` holds the raw
    ``status.video_status`` value (or "" if unparseable)."""

    ok: bool
    status_code: str = ""
    detail: str = ""

    @property
    def is_finished(self) -> bool:
        return self.status_code == STATUS_UPLOAD_COMPLETE

    @property
    def is_terminal_failure(self) -> bool:
        return self.status_code in _TERMINAL_FAILURE_STATUSES


@dataclass(frozen=True)
class PublishResult:
    """Outcome of the final ``finish`` call. ``media_id`` equals the
    ``video_id`` from the create step — Facebook has no separate id
    minted at publish time the way Instagram's ``media_publish`` does."""

    ok: bool
    media_id: str = ""
    detail: str = ""


async def create_reel_container(
    *,
    video_url: str,
    caption: str = "",
    cover_url: str = "",
    account_id: str | None = None,
) -> ContainerResult:
    """Open an upload session and transfer the video by URL. Returns with a
    ``creation_id`` (FB's ``video_id``) once Meta confirms the transfer —
    the video is NOT yet published; poll then publish (finish)."""
    creds = _creds("facebook", account_id)
    if not creds.complete:
        logger.warning("[fb_publish] missing facebook credentials — cannot start upload")
        return ContainerResult(False, detail="missing credentials")
    if not video_url.strip():
        return ContainerResult(False, detail="empty video_url")
    if cover_url.strip():
        logger.debug("[fb_publish] cover_url ignored — video_reels has no cover-image param")

    start = await _start_upload_session(creds.sender_id, creds.token)
    if not start.ok:
        return ContainerResult(False, detail=start.detail)

    transfer_ok, transfer_detail = await _transfer_by_url(
        start.upload_url, creds.token, video_url
    )
    if not transfer_ok:
        # Known accepted gap (code-reviewer, 2026-07-08): the upload session
        # opened by _start_upload_session above is now orphaned — we never
        # call `finish`, so it can never publish, but nothing here actively
        # cancels it either. Accepted as-is: Meta expires unfinished upload
        # sessions server-side on its own, this creates no data-integrity
        # risk (a session that's never finished can never go live), and the
        # caller (notion_publish_fb_runner) already marks the row "failed"
        # and will retry with a FRESH session next attempt, not this
        # orphaned one. Revisit only if Meta's session quota ever becomes a
        # real constraint in practice.
        return ContainerResult(False, detail=transfer_detail)

    logger.info("[fb_publish] container created + transferred: %s", start.video_id)
    return ContainerResult(True, creation_id=start.video_id)


@dataclass(frozen=True)
class _StartSessionResult:
    """Internal-only — the start phase returns TWO ids (``video_id`` for
    polling/finishing, ``upload_url`` for the transfer call) that don't fit
    the public ``ContainerResult`` shape (one id field). Not exported."""

    ok: bool
    video_id: str = ""
    upload_url: str = ""
    detail: str = ""


async def _start_upload_session(page_id: str, token: str) -> _StartSessionResult:
    url = _graph_url("facebook", f"{page_id}/video_reels")
    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT_S) as client:
            resp = await client.post(
                url, params={"upload_phase": "start", "access_token": token}
            )
    except httpx.HTTPError as exc:
        logger.warning("[fb_publish] start-phase transport error: %s", exc)
        return _StartSessionResult(False, detail=f"transport: {exc}")

    if resp.status_code != 200:
        detail = resp.text[:200]
        logger.warning("[fb_publish] start phase failed HTTP %d: %s", resp.status_code, detail)
        return _StartSessionResult(False, detail=f"http {resp.status_code}: {detail}")

    try:
        body = resp.json()
        video_id = str(body.get("video_id", "")).strip()
        upload_url = str(body.get("upload_url", "")).strip()
    except (ValueError, TypeError, AttributeError):
        return _StartSessionResult(False, detail="unparseable response body")
    if not video_id or not upload_url:
        return _StartSessionResult(False, detail="response missing video_id or upload_url")

    return _StartSessionResult(True, video_id=video_id, upload_url=upload_url)


async def _transfer_by_url(upload_url: str, token: str, video_url: str) -> tuple[bool, str]:
    """Meta's "transfer by URL" resumable-upload mode — Meta fetches
    ``video_url`` server-side, no binary streaming needed on our end.
    Returns ``(ok, detail)``; ``detail`` is empty on success."""
    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT_S) as client:
            resp = await client.post(
                upload_url,
                headers={"Authorization": f"OAuth {token}", "file_url": video_url},
            )
    except httpx.HTTPError as exc:
        logger.warning("[fb_publish] transfer-phase transport error: %s", exc)
        return False, f"transport: {exc}"

    if resp.status_code != 200:
        detail = resp.text[:200]
        logger.warning("[fb_publish] transfer phase failed HTTP %d: %s", resp.status_code, detail)
        return False, f"http {resp.status_code}: {detail}"

    return True, ""


async def poll_container_status(
    creation_id: str, *, account_id: str | None = None,
) -> StatusResult:
    """One status check — the caller owns the polling loop/backoff/timeout
    (see ``notion_publish_runner``), this makes exactly one HTTP call."""
    creds = _creds("facebook", account_id)
    if not creds.token:
        logger.warning("[fb_publish] missing facebook token — cannot poll status")
        return StatusResult(False, detail="missing credentials")

    url = _graph_url("facebook", creation_id)
    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT_S) as client:
            resp = await client.get(
                url, params={"fields": _STATUS_FIELDS, "access_token": creds.token}
            )
    except httpx.HTTPError as exc:
        logger.warning("[fb_publish] poll transport error: %s", exc)
        return StatusResult(False, detail=f"transport: {exc}")

    if resp.status_code != 200:
        detail = resp.text[:200]
        logger.warning("[fb_publish] poll failed HTTP %d: %s", resp.status_code, detail)
        return StatusResult(False, detail=f"http {resp.status_code}: {detail}")

    try:
        status_obj = resp.json().get("status", {})
        status_code = str(status_obj.get("video_status", "")).strip()
    except (ValueError, TypeError, AttributeError):
        return StatusResult(False, detail="unparseable response body")

    return StatusResult(True, status_code=status_code)


async def publish_container(
    creation_id: str, caption: str = "", *, account_id: str | None = None,
) -> PublishResult:
    """``POST /{page-id}/video_reels`` with ``upload_phase=finish`` — the
    point of no return. Call at most once per ``creation_id``; the caller
    (``notion_publish_runner``) is responsible for that guarantee via its
    idempotency ledger, this function has no memory of prior calls."""
    creds = _creds("facebook", account_id)
    if not creds.complete:
        logger.warning("[fb_publish] missing facebook credentials — cannot publish")
        return PublishResult(False, detail="missing credentials")
    if not creation_id.strip():
        return PublishResult(False, detail="empty creation_id")

    url = _graph_url("facebook", f"{creds.sender_id}/video_reels")
    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT_S) as client:
            resp = await client.post(
                url,
                params={
                    "upload_phase": "finish",
                    "video_id": creation_id,
                    "video_state": "PUBLISHED",
                    "description": caption,
                    "access_token": creds.token,
                },
            )
    except httpx.HTTPError as exc:
        logger.warning("[fb_publish] finish-phase transport error: %s", exc)
        return PublishResult(False, detail=f"transport: {exc}")

    if resp.status_code != 200:
        detail = resp.text[:200]
        logger.warning("[fb_publish] finish phase failed HTTP %d: %s", resp.status_code, detail)
        return PublishResult(False, detail=f"http {resp.status_code}: {detail}")

    logger.info("[fb_publish] published: video_id=%s", creation_id)
    # No separate media id is minted at finish time — video_id IS the id.
    return PublishResult(True, media_id=creation_id)
