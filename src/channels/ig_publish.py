"""ig_publish.py — Instagram Reels publish via the Graph API two-step flow.

Kept separate from ``meta_client.py`` (already ~410 lines covering DM/comment
send + read primitives) — publishing a Reel is a distinct, higher-stakes
concern with its own async lifecycle (container create → poll → publish).

THE TWO-STEP FLOW (Meta's Content Publishing API for Reels)
-------------------------------------------------------------
1. ``create_reel_container`` — ``POST /{ig-user-id}/media`` with
   ``media_type=REELS``, ``video_url``, ``caption``, optional ``cover_url``.
   Returns a ``creation_id`` immediately; Meta then processes the video
   ASYNCHRONOUSLY server-side (can take seconds to several minutes).
2. ``poll_container_status`` — ``GET /{creation_id}?fields=status_code``.
   Transitions ``IN_PROGRESS`` → ``FINISHED`` (ready to publish) or
   ``ERROR``/``EXPIRED`` (never publishable — do not retry indefinitely).
3. ``publish_container`` — ``POST /{ig-user-id}/media_publish`` with
   ``creation_id``. Call this AT MOST ONCE per ``creation_id`` — Meta does
   not de-duplicate a second call on your behalf; that responsibility is the
   caller's (``notion_publish_runner`` — see its idempotency ledger).

This module has NO knowledge of Notion, no retry/idempotency policy, and no
opinion on what to do with a failed publish — it is a thin, testable wrapper
around exactly these three Graph API calls, reusing the credential/URL/
response-interpretation helpers already proven in ``meta_client.py``.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Final

import httpx

from src.channels.meta_client import _creds, _graph_url, _interpret

logger = logging.getLogger("channels.ig_publish")

_TIMEOUT_S: Final[float] = 30.0
_STATUS_FIELDS: Final[str] = "status_code"

# Meta's documented container status values. ERROR/EXPIRED are terminal
# failures — a poller must stop and report failure, never keep waiting.
STATUS_IN_PROGRESS: Final[str] = "IN_PROGRESS"
STATUS_FINISHED: Final[str] = "FINISHED"
STATUS_ERROR: Final[str] = "ERROR"
STATUS_EXPIRED: Final[str] = "EXPIRED"
_TERMINAL_FAILURE_STATUSES: Final[frozenset[str]] = frozenset({STATUS_ERROR, STATUS_EXPIRED})


@dataclass(frozen=True)
class ContainerResult:
    """Outcome of creating (or checking) a media container.

    ``ok`` is the only thing callers must branch on for the create step;
    ``creation_id`` is set on success. ``detail`` never contains the token.
    """

    ok: bool
    creation_id: str = ""
    detail: str = ""


@dataclass(frozen=True)
class StatusResult:
    """Outcome of one status poll. ``status_code`` is one of the ``STATUS_*``
    constants above (or "" if the response was unparseable)."""

    ok: bool
    status_code: str = ""
    detail: str = ""

    @property
    def is_finished(self) -> bool:
        return self.status_code == STATUS_FINISHED

    @property
    def is_terminal_failure(self) -> bool:
        return self.status_code in _TERMINAL_FAILURE_STATUSES


@dataclass(frozen=True)
class PublishResult:
    """Outcome of the final ``media_publish`` call. ``media_id`` is the
    live post's id on success."""

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
    """Create a Reels media container. Returns immediately with a
    ``creation_id`` — the video is NOT yet published; poll then publish."""
    creds = _creds("instagram", account_id)
    if not creds.complete:
        logger.warning("[ig_publish] missing instagram credentials — cannot create container")
        return ContainerResult(False, detail="missing credentials")
    if not video_url.strip():
        return ContainerResult(False, detail="empty video_url")

    params: dict[str, str] = {
        "access_token": creds.token,
        "media_type": "REELS",
        "video_url": video_url,
        "caption": caption,
    }
    if cover_url.strip():
        params["cover_url"] = cover_url

    url = _graph_url("instagram", f"{creds.sender_id}/media")
    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT_S) as client:
            resp = await client.post(url, params=params)
    except httpx.HTTPError as exc:
        logger.warning("[ig_publish] create container transport error: %s", exc)
        return ContainerResult(False, detail=f"transport: {exc}")

    if resp.status_code != 200:
        detail = resp.text[:200]
        logger.warning("[ig_publish] create container failed HTTP %d: %s", resp.status_code, detail)
        return ContainerResult(False, detail=f"http {resp.status_code}: {detail}")

    try:
        creation_id = str(resp.json().get("id", "")).strip()
    except (ValueError, TypeError):
        return ContainerResult(False, detail="unparseable response body")
    if not creation_id:
        return ContainerResult(False, detail="response had no container id")

    logger.info("[ig_publish] container created: %s", creation_id)
    return ContainerResult(True, creation_id=creation_id)


async def poll_container_status(
    creation_id: str, *, account_id: str | None = None,
) -> StatusResult:
    """One status check — the caller owns the polling loop/backoff/timeout
    (see ``notion_publish_runner``), this makes exactly one HTTP call."""
    creds = _creds("instagram", account_id)
    if not creds.token:
        logger.warning("[ig_publish] missing instagram token — cannot poll status")
        return StatusResult(False, detail="missing credentials")

    url = _graph_url("instagram", creation_id)
    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT_S) as client:
            resp = await client.get(
                url, params={"fields": _STATUS_FIELDS, "access_token": creds.token}
            )
    except httpx.HTTPError as exc:
        logger.warning("[ig_publish] poll transport error: %s", exc)
        return StatusResult(False, detail=f"transport: {exc}")

    if resp.status_code != 200:
        detail = resp.text[:200]
        logger.warning("[ig_publish] poll failed HTTP %d: %s", resp.status_code, detail)
        return StatusResult(False, detail=f"http {resp.status_code}: {detail}")

    try:
        status_code = str(resp.json().get("status_code", "")).strip()
    except (ValueError, TypeError):
        return StatusResult(False, detail="unparseable response body")

    return StatusResult(True, status_code=status_code)


async def publish_container(
    creation_id: str, *, account_id: str | None = None,
) -> PublishResult:
    """``POST /{ig-user-id}/media_publish``. Call at most once per
    ``creation_id`` — the caller (``notion_publish_runner``) is responsible
    for that guarantee via its idempotency ledger; this function has no
    memory of prior calls."""
    creds = _creds("instagram", account_id)
    if not creds.complete:
        logger.warning("[ig_publish] missing instagram credentials — cannot publish")
        return PublishResult(False, detail="missing credentials")
    if not creation_id.strip():
        return PublishResult(False, detail="empty creation_id")

    url = _graph_url("instagram", f"{creds.sender_id}/media_publish")
    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT_S) as client:
            resp = await client.post(
                url, params={"creation_id": creation_id, "access_token": creds.token}
            )
    except httpx.HTTPError as exc:
        logger.warning("[ig_publish] publish transport error: %s", exc)
        return PublishResult(False, detail=f"transport: {exc}")

    result = _interpret(resp, context=f"ig_publish:media_publish→{creation_id}")
    if not result.ok:
        return PublishResult(False, detail=result.detail)

    try:
        media_id = str(resp.json().get("id", "")).strip()
    except (ValueError, TypeError):
        media_id = ""
    logger.info("[ig_publish] published: creation_id=%s media_id=%s", creation_id, media_id)
    return PublishResult(True, media_id=media_id)


@dataclass(frozen=True)
class DeleteResult:
    """Outcome of deleting a live media object."""

    ok: bool
    detail: str = ""


async def delete_media(media_id: str, *, account_id: str | None = None) -> DeleteResult:
    """``DELETE /{ig-media-id}`` — permanently removes a LIVE post.

    Added 2026-07-19: the first time this codebase ever needed to delete a
    live post, after discovering 即梦 does not play back an uploaded voice
    verbatim (see notion_video.py's replace_shot_audio() docstring) — a
    post published before that fix went out with the wrong voice, and
    Instagram has no "replace this Reel's video" API, only delete-and-
    republish. Every other module in this codebase treats a live post as
    effectively permanent (the whole ledger/idempotency design exists to
    prevent ever needing this) — so this is a genuinely rare, deliberate,
    human-confirmed operation, not something any automated sweep calls.
    """
    creds = _creds("instagram", account_id)
    if not creds.token:
        logger.warning("[ig_publish] missing instagram token — cannot delete")
        return DeleteResult(False, detail="missing credentials")
    if not media_id.strip():
        return DeleteResult(False, detail="empty media_id")

    url = _graph_url("instagram", media_id)
    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT_S) as client:
            resp = await client.delete(url, params={"access_token": creds.token})
    except httpx.HTTPError as exc:
        logger.warning("[ig_publish] delete transport error: %s", exc)
        return DeleteResult(False, detail=f"transport: {exc}")

    result = _interpret(resp, context=f"ig_publish:delete→{media_id}")
    if not result.ok:
        return DeleteResult(False, detail=result.detail)
    logger.info("[ig_publish] deleted media_id=%s", media_id)
    return DeleteResult(True)
