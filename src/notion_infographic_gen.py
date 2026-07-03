"""notion_infographic_gen.py — generate a DM infographic from a Notion Brief.

Phase 4 of the Notion → comment-rule bridge. When a published row has NO
image in its "DM Infographic" toggle, ``notion_sync_media`` used to ship a
text-only DM. This module lets it instead GENERATE the infographic from the
row's "🖼️ Infographic Brief" block via the OpenAI image API — so a post that
was authored with a Brief but never had its PNG hand-made still goes out with
a graphic.

Two pure-ish pieces:
1. ``find_infographic_brief`` — walk a content page for the Brief text. No
   network beyond the injected ``children_fn`` (same pattern as
   notion_sync_media). Pure given that callable.
2. ``generate_png`` — the only place that hits the OpenAI image API. Raises
   ``InfographicGenError`` on any failure; callers own the catch-everything
   guarantee (the sync must never crash on a failed generation).
"""

from __future__ import annotations

import base64
import json
import os
import urllib.error
import urllib.request
from collections.abc import Callable

ChildrenFn = Callable[[str], list[dict]]

_BRIEF_MARKER = "infographic brief"
_CONTENT_BLOCK_TYPES = ("code", "paragraph")
_DEFAULT_MODEL = "gpt-image-2"
_DEFAULT_SIZE = "1024x1536"
_GEN_TIMEOUT_S = 240
_OPENAI_IMG_URL = "https://api.openai.com/v1/images/generations"


class InfographicGenError(RuntimeError):
    """Raised on any failure to locate or generate an infographic."""


def _plain_text(block: dict) -> str:
    block_type = block.get("type", "")
    return "".join(t.get("plain_text", "") for t in block.get(block_type, {}).get("rich_text", []))


def find_infographic_brief(content_page_id: str, children_fn: ChildrenFn) -> str | None:
    """Return the Infographic Brief text from a content page, else ``None``.

    Matching is loose: any block whose text contains "infographic brief"
    case-insensitively is the marker. The brief itself is:
    - the concatenated ``code``/``paragraph`` children, if the marker is a
      toggle; or
    - the following ``code``/``paragraph`` sibling blocks up to the next
      heading, if the marker is a heading/paragraph.
    """
    blocks = children_fn(content_page_id)
    for index, block in enumerate(blocks):
        if _BRIEF_MARKER not in _plain_text(block).casefold():
            continue
        if block.get("type") == "toggle":
            parts = [
                _plain_text(child)
                for child in children_fn(block["id"])
                if child.get("type") in _CONTENT_BLOCK_TYPES
            ]
        else:
            parts = []
            for following in blocks[index + 1 :]:
                if following.get("type", "").startswith("heading"):
                    break
                if following.get("type") in _CONTENT_BLOCK_TYPES:
                    parts.append(_plain_text(following))
        joined = "\n".join(part for part in parts if part.strip()).strip()
        return joined or None
    return None


def generate_png(
    brief: str,
    *,
    api_key: str | None = None,
    model: str | None = None,
    size: str | None = None,
    timeout: int = _GEN_TIMEOUT_S,
) -> bytes:
    """Generate a PNG from ``brief`` via the OpenAI image API. Raises on failure.

    The API key / model come from the environment (``OPENAI_API_KEY``,
    ``IMAGE_MODEL``) unless overridden — the overrides exist for tests.
    """
    resolved_key = (api_key or os.environ.get("OPENAI_API_KEY", "")).strip()
    if not resolved_key:
        raise InfographicGenError("OPENAI_API_KEY not set")
    if not brief.strip():
        raise InfographicGenError("empty infographic brief")

    resolved_model = (model or os.environ.get("IMAGE_MODEL", _DEFAULT_MODEL)).strip()
    payload = json.dumps(
        {"model": resolved_model, "prompt": brief, "size": size or _DEFAULT_SIZE, "n": 1}
    ).encode("utf-8")
    request = urllib.request.Request(
        _OPENAI_IMG_URL,
        data=payload,
        headers={"Authorization": f"Bearer {resolved_key}", "Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            data = json.loads(response.read().decode("utf-8"))
    except (urllib.error.URLError, OSError, TimeoutError) as exc:
        raise InfographicGenError(f"image API call failed: {exc}") from exc

    try:
        return base64.b64decode(data["data"][0]["b64_json"])
    except (KeyError, IndexError, ValueError, TypeError) as exc:
        raise InfographicGenError(f"unexpected image API response: {exc}") from exc
