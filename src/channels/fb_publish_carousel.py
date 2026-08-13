"""fb_publish_carousel.py — Facebook Page carousel (multi-photo) publish via
the Graph API.

Sibling of ``ig_publish_carousel.py`` (Instagram) and ``fb_publish.py``
(Facebook Reels) — but a Facebook Page photo carousel uses a THIRD, simpler
shape than either: unlike IG's item-container -> parent-container -> poll
-> publish, or FB's own Reels start -> transfer -> poll -> finish, a Page
photo has no Meta-side processing step at all. The flow is:

1. ``create_unpublished_photo`` — ``POST /{page-id}/photos`` with
   ``url=<image_url>``, ``published=false``. Returns a photo id
   IMMEDIATELY — there is nothing to poll; an unpublished photo is ready
   the instant the upload call succeeds (this is documented Graph API
   behavior for photos, unlike video processing).
2. ``publish_carousel_post`` — ``POST /{page-id}/feed`` with
   ``attached_media=[{"media_fbid": id1}, {"media_fbid": id2}, ...]`` and
   ``message=<caption>``. This is the point of no return — it creates the
   live multi-photo Page post in one call. Returns the post id.

Because there is no processing step, this module deliberately has NO
``poll_container_status`` function — a caller (``notion_publish_carousel_fb_runner``)
goes straight from create to publish, unlike the IG/FB-Reel runners which
must poll between those two steps. This asymmetry is intentional, not a
missing feature — forcing an artificial poll here would just be a no-op
sleep loop around a status that never changes.

This module has NO knowledge of Notion, no retry/idempotency policy, and no
opinion on how many images make up the carousel (Meta itself enforces
2-10 attached_media entries, mirrored locally here for the same reason
``ig_publish_carousel.py`` does) — a thin, testable wrapper around the
Graph API calls, reusing the credential/URL helpers already proven in
``meta_client.py``.
"""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass
from typing import Final

import httpx

from src.channels.meta_client import _creds, _graph_url

logger = logging.getLogger("channels.fb_publish_carousel")

_TIMEOUT_S: Final[float] = 30.0
MIN_CAROUSEL_ITEMS: Final[int] = 2
MAX_CAROUSEL_ITEMS: Final[int] = 10


@dataclass(frozen=True)
class PhotoResult:
    """Outcome of one unpublished-photo upload. ``photo_id`` is set on
    success — this id is never itself a live post; it only becomes visible
    once referenced in a ``publish_carousel_post`` call's ``attached_media``."""

    ok: bool
    photo_id: str = ""
    detail: str = ""


@dataclass(frozen=True)
class PublishResult:
    """Outcome of the final ``/feed`` call — the point of no return."""

    ok: bool
    post_id: str = ""
    detail: str = ""


async def create_unpublished_photo(
    image_url: str, *, account_id: str | None = None,
) -> PhotoResult:
    """Upload ONE image as an unpublished Page photo. Never appears on the
    Page's timeline on its own — only once its id is attached to a
    ``publish_carousel_post`` call."""
    creds = _creds("facebook", account_id)
    if not creds.complete:
        logger.warning(
            "[fb_publish_carousel] missing facebook credentials — cannot create photo"
        )
        return PhotoResult(False, detail="missing credentials")
    if not image_url.strip():
        return PhotoResult(False, detail="empty image_url")

    url = _graph_url("facebook", f"{creds.sender_id}/photos")
    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT_S) as client:
            resp = await client.post(
                url,
                params={
                    "url": image_url,
                    "published": "false",
                    "access_token": creds.token,
                },
            )
    except httpx.HTTPError as exc:
        logger.warning("[fb_publish_carousel] create photo transport error: %s", exc)
        return PhotoResult(False, detail=f"transport: {exc}")

    if resp.status_code != 200:
        detail = resp.text[:200]
        logger.warning(
            "[fb_publish_carousel] create photo failed HTTP %d: %s", resp.status_code, detail
        )
        return PhotoResult(False, detail=f"http {resp.status_code}: {detail}")

    try:
        photo_id = str(resp.json().get("id", "")).strip()
    except (ValueError, TypeError):
        return PhotoResult(False, detail="unparseable response body")
    if not photo_id:
        return PhotoResult(False, detail="response had no photo id")

    logger.info("[fb_publish_carousel] unpublished photo created: %s", photo_id)
    return PhotoResult(True, photo_id=photo_id)


async def publish_carousel_post(
    photo_ids: list[str], *, caption: str = "", account_id: str | None = None,
) -> PublishResult:
    """Create the live multi-photo Page post referencing every unpublished
    photo id. Validates Meta's 2-10 item bounds locally so a caller finds
    out immediately rather than from an opaque Graph API error. Call at
    most once per photo-id set; the caller (the runner) is responsible for
    that guarantee via its idempotency ledger, this function has no memory
    of prior calls."""
    ids = [i.strip() for i in photo_ids if i.strip()]
    if len(ids) < MIN_CAROUSEL_ITEMS:
        return PublishResult(
            False, detail=f"need at least {MIN_CAROUSEL_ITEMS} items, got {len(ids)}"
        )
    if len(ids) > MAX_CAROUSEL_ITEMS:
        return PublishResult(
            False, detail=f"at most {MAX_CAROUSEL_ITEMS} items allowed, got {len(ids)}"
        )

    creds = _creds("facebook", account_id)
    if not creds.complete:
        logger.warning(
            "[fb_publish_carousel] missing facebook credentials — cannot publish"
        )
        return PublishResult(False, detail="missing credentials")

    attached_media = json.dumps([{"media_fbid": pid} for pid in ids])
    url = _graph_url("facebook", f"{creds.sender_id}/feed")
    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT_S) as client:
            resp = await client.post(
                url,
                params={
                    "message": caption,
                    "attached_media": attached_media,
                    "access_token": creds.token,
                },
            )
    except httpx.HTTPError as exc:
        logger.warning("[fb_publish_carousel] publish transport error: %s", exc)
        return PublishResult(False, detail=f"transport: {exc}")

    if resp.status_code != 200:
        detail = resp.text[:200]
        logger.warning(
            "[fb_publish_carousel] publish failed HTTP %d: %s", resp.status_code, detail
        )
        return PublishResult(False, detail=f"http {resp.status_code}: {detail}")

    try:
        post_id = str(resp.json().get("id", "")).strip()
    except (ValueError, TypeError):
        return PublishResult(False, detail="unparseable response body")
    if not post_id:
        return PublishResult(False, detail="response had no post id")

    logger.info("[fb_publish_carousel] published: %s", post_id)
    return PublishResult(True, post_id=post_id)
