"""ig_publish_carousel.py — Instagram carousel (multi-image) publish via the
Graph API two-step flow.

Sibling of ``ig_publish.py`` (Reels-only). Carousels have a DIFFERENT
container shape — one "item" container per image, then a parent "carousel"
container that references them all — so this is kept as its own module
rather than bolted onto ``ig_publish.py``'s Reels-specific docstring/tests.
``publish_container`` (the final ``media_publish`` call) and
``poll_container_status`` are identical for every container type, so this
module reuses ``ig_publish``'s versions directly instead of duplicating them.

THE FLOW (Meta's Content Publishing API for carousels)
---------------------------------------------------------
1. ``create_carousel_item_container`` — ``POST /{ig-user-id}/media`` with
   ``image_url`` + ``is_carousel_item=true`` for EACH image. Returns a
   ``creation_id`` per image; these are never published on their own.
2. ``create_carousel_container`` — ``POST /{ig-user-id}/media`` with
   ``media_type=CAROUSEL``, ``children=<comma-separated item creation_ids>``,
   ``caption``. Returns the parent ``creation_id``.
3. ``ig_publish.poll_container_status`` / ``ig_publish.publish_container`` —
   same two calls used for Reels; a carousel container is just another
   ``creation_id`` to Meta at this point.

ASPECT RATIO — READ BEFORE GENERATING IMAGES
-----------------------------------------------
Instagram's Content Publishing API only accepts photos between 4:5 (0.8) and
1.91:1 aspect ratio. gpt-image-2 cannot render arbitrary sizes (only
1024x1024 / 1024x1536 / 1536x1024) — the 1024x1536 portrait already used for
DM infographics (``notion_infographic_gen.py``, ratio 0.667) is OUTSIDE this
range and WILL be rejected for a feed/carousel post. Generate at 1024x1024
(square) for anything destined for the feed. This bit us on the first run
of ``scripts/gen_carousel_pressure_points.py`` on 2026-07-07 — square was
chosen deliberately there, not by accident.

This module has NO knowledge of Notion, no retry/idempotency policy, and no
opinion on how many images make up the carousel (Meta itself enforces 2-10
children) — it is a thin, testable wrapper around the Graph API calls,
reusing the credential/URL/response-interpretation helpers already proven in
``meta_client.py`` and the dataclasses already proven in ``ig_publish.py``.
"""

from __future__ import annotations

import logging
from typing import Final

import httpx

from src.channels.ig_publish import ContainerResult
from src.channels.meta_client import _creds, _graph_url

logger = logging.getLogger("channels.ig_publish_carousel")

_TIMEOUT_S: Final[float] = 30.0
MIN_CAROUSEL_ITEMS: Final[int] = 2
MAX_CAROUSEL_ITEMS: Final[int] = 10


async def create_carousel_item_container(
    image_url: str, *, account_id: str | None = None,
) -> ContainerResult:
    """Create ONE carousel item container for a single image. This item is
    never published on its own — it only becomes visible once referenced as
    a ``children`` entry of a ``create_carousel_container`` call."""
    creds = _creds("instagram", account_id)
    if not creds.complete:
        logger.warning(
            "[ig_publish_carousel] missing instagram credentials — cannot create item container"
        )
        return ContainerResult(False, detail="missing credentials")
    if not image_url.strip():
        return ContainerResult(False, detail="empty image_url")

    params = {
        "access_token": creds.token,
        "image_url": image_url,
        "is_carousel_item": "true",
    }
    url = _graph_url("instagram", f"{creds.sender_id}/media")
    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT_S) as client:
            resp = await client.post(url, params=params)
    except httpx.HTTPError as exc:
        logger.warning("[ig_publish_carousel] create item transport error: %s", exc)
        return ContainerResult(False, detail=f"transport: {exc}")

    if resp.status_code != 200:
        detail = resp.text[:200]
        logger.warning(
            "[ig_publish_carousel] create item failed HTTP %d: %s", resp.status_code, detail
        )
        return ContainerResult(False, detail=f"http {resp.status_code}: {detail}")

    try:
        creation_id = str(resp.json().get("id", "")).strip()
    except (ValueError, TypeError):
        return ContainerResult(False, detail="unparseable response body")
    if not creation_id:
        return ContainerResult(False, detail="response had no container id")

    logger.info("[ig_publish_carousel] item container created: %s", creation_id)
    return ContainerResult(True, creation_id=creation_id)


async def create_carousel_container(
    item_creation_ids: list[str], *, caption: str = "", account_id: str | None = None,
) -> ContainerResult:
    """Create the PARENT carousel container referencing every item's
    ``creation_id``. Validates Meta's 2-10 item bounds locally so a caller
    finds out immediately rather than from an opaque Graph API error."""
    ids = [i.strip() for i in item_creation_ids if i.strip()]
    if len(ids) < MIN_CAROUSEL_ITEMS:
        return ContainerResult(
            False, detail=f"need at least {MIN_CAROUSEL_ITEMS} items, got {len(ids)}"
        )
    if len(ids) > MAX_CAROUSEL_ITEMS:
        return ContainerResult(
            False, detail=f"at most {MAX_CAROUSEL_ITEMS} items allowed, got {len(ids)}"
        )

    creds = _creds("instagram", account_id)
    if not creds.complete:
        logger.warning(
            "[ig_publish_carousel] missing instagram credentials — cannot create carousel container"
        )
        return ContainerResult(False, detail="missing credentials")

    params = {
        "access_token": creds.token,
        "media_type": "CAROUSEL",
        "children": ",".join(ids),
        "caption": caption,
    }
    url = _graph_url("instagram", f"{creds.sender_id}/media")
    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT_S) as client:
            resp = await client.post(url, params=params)
    except httpx.HTTPError as exc:
        logger.warning("[ig_publish_carousel] create carousel transport error: %s", exc)
        return ContainerResult(False, detail=f"transport: {exc}")

    if resp.status_code != 200:
        detail = resp.text[:200]
        logger.warning(
            "[ig_publish_carousel] create carousel failed HTTP %d: %s", resp.status_code, detail
        )
        return ContainerResult(False, detail=f"http {resp.status_code}: {detail}")

    try:
        creation_id = str(resp.json().get("id", "")).strip()
    except (ValueError, TypeError):
        return ContainerResult(False, detail="unparseable response body")
    if not creation_id:
        return ContainerResult(False, detail="response had no container id")

    logger.info("[ig_publish_carousel] carousel container created: %s", creation_id)
    return ContainerResult(True, creation_id=creation_id)
