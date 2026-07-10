"""notion_cover_gen.py — generate a Reels cover image from a Production
Tracker row's already-authored "🖼️ Cover prompt" text + the IP's reference
face photos, and upload the result into the row's "🖼️ Cover here" toggle.

Closes a real gap: `studio/scripts/notion_prompts.py::cover_blocks()`
already writes a cover PROMPT onto every row (code block, under a
"🖼️ Cover Photo" heading) at fan-out time, but nothing ever turned that text
into an actual image — this module is that missing step.

Structure mirrors ``src/notion_infographic_gen.py`` (same problem shape:
find a prompt on a Notion page via an injected ``children_fn`` -> call the
OpenAI image API -> return bytes, raising a custom ``*Error`` on any
failure) plus ``src/notion_publish_media.py`` (cover-toggle discovery +
upload, and the shared SSRF guard for any URL Notion hands us).

Four pure-ish/orchestration pieces:
1. ``find_cover_prompt`` / ``find_cover_toggle`` / ``toggle_has_image`` —
   pure given ``children_fn``. No network beyond that injected callable.
2. ``find_ip_reference_images`` — walks the IP Registry page for image
   blocks and fetches each via an injected ``fetch_bytes``. Never raises;
   skips (does not crash on) any block/URL/download that fails.
3. ``generate_cover`` — the only place that hits the OpenAI image API.
   Raises ``CoverGenError`` on any failure, INCLUDING zero reference images
   — a cover generated with no reference photo of the IP has no guarantee
   of drawing the right person (the exact 2026-07-08 wrong-person-drawn
   incident this whole feature exists to prevent). Callers decide whether a
   no-reference fallback is acceptable elsewhere; this function refuses.
4. ``generate_and_upload_cover`` — thin, single-row orchestrator. NEVER
   raises (catches everything, returns a warning string or ``None`` on
   success), mirroring ``notion_sync_media.enrich_rule`` /
   ``notion_publish_media.resolve_cover``'s contract.
"""

from __future__ import annotations

import base64
import json
import logging
import os
import urllib.error
import urllib.request
import uuid
from collections.abc import Callable

from src.notion_publish_media import _is_safe_download_url

logger = logging.getLogger("notion_cover_gen")

ChildrenFn = Callable[[str], list[dict]]
FetchBytesFn = Callable[[str], bytes]
UploadFn = Callable[[str, bytes], None]

_NEW_HEADING_MARKER = "cover photo"
_OLD_HEADING_MARKER = "reel cover photo"
_COVER_TOGGLE_MARKER = "cover here"
_STOP_BLOCK_TYPES = ("divider",)

_DEFAULT_MODEL = "gpt-image-1"
_DEFAULT_SIZE = "1024x1536"
_GEN_TIMEOUT_S = 300
_DOWNLOAD_TIMEOUT_S = 30
_UPLOAD_TIMEOUT_S = 60
_OPENAI_IMG_EDIT_URL = "https://api.openai.com/v1/images/edits"
_NOTION_API = "https://api.notion.com/v1"
_NOTION_VERSION = "2022-06-28"


class CoverGenError(RuntimeError):
    """Raised on any failure to generate a cover image."""


def _plain_text(block: dict) -> str:
    block_type = block.get("type", "")
    return "".join(t.get("plain_text", "") for t in block.get(block_type, {}).get("rich_text", []))


def _is_new_cover_heading(text: str) -> bool:
    """True only for the current-schema "🖼️ Cover Photo" heading — the
    legacy "🖼️ Reel Cover Photo Image Prompt" heading (older rows, pre
    2026-07-06) must never match, or its stale content/toggle would be
    misread. Same false-positive guard as
    ``studio/scripts/audit_cover_schema.py``."""
    folded = text.casefold()
    return _NEW_HEADING_MARKER in folded and _OLD_HEADING_MARKER not in folded


def find_cover_prompt(row_page_id: str, children_fn: ChildrenFn) -> str | None:
    """Return the row's authored Cover prompt text, else ``None``.

    Walks the row body for a ``heading_3`` matching the new-schema Cover
    Photo marker (excluding the legacy heading), then the first ``code``
    block that follows before the next heading/divider. ``None`` if the
    section doesn't exist, or exists but has no prompt authored yet (no
    code block, or an empty one).
    """
    blocks = children_fn(row_page_id)
    for index, block in enumerate(blocks):
        if block.get("type") != "heading_3" or not _is_new_cover_heading(_plain_text(block)):
            continue
        for following in blocks[index + 1 :]:
            following_type = following.get("type", "")
            if following_type.startswith("heading") or following_type in _STOP_BLOCK_TYPES:
                break
            if following_type == "code":
                prompt = _plain_text(following).strip()
                return prompt or None
        return None
    return None


def find_cover_toggle(row_page_id: str, children_fn: ChildrenFn) -> str | None:
    """Return the row's "🖼️ Cover here" toggle block id, else ``None`` if the
    dedicated Cover Photo section doesn't exist on this row yet."""
    in_cover_section = False
    for block in children_fn(row_page_id):
        block_type = block.get("type", "")
        text = _plain_text(block).casefold()
        if block_type == "heading_3":
            in_cover_section = _is_new_cover_heading(text)
        elif in_cover_section and block_type == "toggle" and _COVER_TOGGLE_MARKER in text:
            return block.get("id")
    return None


def toggle_has_image(toggle_id: str, children_fn: ChildrenFn) -> bool:
    """True if the toggle already has an image child — idempotency guard,
    a cover must never be silently overwritten once generated/uploaded."""
    return any(child.get("type") == "image" for child in children_fn(toggle_id))


def _block_image_url(block: dict) -> str | None:
    image = block.get("image") or {}
    kind = image.get("type", "")
    return (image.get(kind) or {}).get("url") or None


def find_ip_reference_images(
    ip_page_id: str, children_fn: ChildrenFn, *, fetch_bytes: FetchBytesFn
) -> list[bytes]:
    """Walk the IP Registry page's children for image blocks and fetch each
    via the injected ``fetch_bytes``. NEVER raises — skips (does not crash
    on) any block with no url, any url that fails the shared SSRF guard
    (``notion_publish_media._is_safe_download_url`` — reused, not
    re-derived, to avoid a second, possibly-weaker copy), or any download
    that itself fails. Returns whatever succeeded.
    """
    images: list[bytes] = []
    for block in children_fn(ip_page_id):
        if block.get("type") != "image":
            continue
        url = _block_image_url(block)
        if not url:
            continue
        if not _is_safe_download_url(url):
            logger.warning("cover ref: refused unsafe url for ip=%s", ip_page_id)
            continue
        try:
            data = fetch_bytes(url)
        except Exception as exc:  # noqa: BLE001 - one bad reference must not sink the rest
            # Logged (not silently discarded) precisely so a real outage
            # (revoked token, network egress issue) is distinguishable from
            # "this IP genuinely has zero reference photos authored yet" —
            # both currently produce the same empty-list result to the
            # caller, but only one of them should ever look "normal."
            logger.warning("cover ref: download failed ip=%s url=%s err=%s", ip_page_id, url, exc)
            continue
        if data:
            images.append(data)
    return images


def _default_fetch_bytes(url: str) -> bytes:
    headers = {"User-Agent": "social-ip-engine/notion-cover-gen"}
    request = urllib.request.Request(url, headers=headers)
    with urllib.request.urlopen(request, timeout=_DOWNLOAD_TIMEOUT_S) as response:
        return response.read()


def _multipart_edit_body(
    prompt: str, model: str, size: str, reference_images: list[bytes]
) -> tuple[str, bytes]:
    boundary = "----cover" + uuid.uuid4().hex
    body = b""
    for key, value in {"model": model, "prompt": prompt, "size": size, "n": "1"}.items():
        field = f'--{boundary}\r\nContent-Disposition: form-data; name="{key}"\r\n\r\n{value}\r\n'
        body += field.encode()
    for index, ref_bytes in enumerate(reference_images):
        name = f"ref{index}.png"
        body += (
            f'--{boundary}\r\nContent-Disposition: form-data; name="image[]"; '
            f'filename="{name}"\r\nContent-Type: image/png\r\n\r\n'
        ).encode()
        body += ref_bytes + b"\r\n"
    body += f"--{boundary}--\r\n".encode()
    return boundary, body


def generate_cover(
    prompt: str,
    reference_images: list[bytes],
    *,
    api_key: str | None = None,
    model: str | None = None,
    size: str | None = None,
    timeout: int = _GEN_TIMEOUT_S,
) -> bytes:
    """Generate a PNG cover via ``POST images/edits``. Raises
    ``CoverGenError`` on: missing API key, empty prompt, zero reference
    images, HTTP/network failure, or an unexpected response shape.

    The API key / model come from the environment (``OPENAI_API_KEY``,
    ``IMAGE_MODEL``) unless overridden — the overrides exist for tests.
    """
    resolved_key = (api_key or os.environ.get("OPENAI_API_KEY", "")).strip()
    if not resolved_key:
        raise CoverGenError("OPENAI_API_KEY not set")
    if not prompt.strip():
        raise CoverGenError("empty cover prompt")
    if not reference_images:
        # THE single most important guard in this module: a cover generated
        # with zero reference photos of the IP has no guarantee whatsoever
        # of drawing the right person -- this is the exact 2026-07-08
        # wrong-person-drawn incident the whole feature exists to prevent.
        # Refuse outright; do NOT silently fall back to a blind
        # (no-reference) generation call. The caller decides if a fallback
        # path is acceptable elsewhere -- this function never does.
        raise CoverGenError("no reference images supplied — refusing blind generation")

    resolved_model = (model or os.environ.get("IMAGE_MODEL", _DEFAULT_MODEL)).strip()
    resolved_size = size or _DEFAULT_SIZE
    boundary, body = _multipart_edit_body(prompt, resolved_model, resolved_size, reference_images)
    request = urllib.request.Request(
        _OPENAI_IMG_EDIT_URL,
        data=body,
        headers={
            "Authorization": f"Bearer {resolved_key}",
            "Content-Type": f"multipart/form-data; boundary={boundary}",
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            data = json.loads(response.read().decode("utf-8"))
    except (urllib.error.URLError, OSError, TimeoutError, json.JSONDecodeError) as exc:
        raise CoverGenError(f"image API call failed: {exc}") from exc

    try:
        return base64.b64decode(data["data"][0]["b64_json"])
    except (KeyError, IndexError, ValueError, TypeError) as exc:
        raise CoverGenError(f"unexpected image API response: {exc}") from exc


def _notion_call(method: str, path: str, api_key: str, body: dict | None = None) -> dict:
    """POST/PATCH/GET against the Notion API. Raises ``CoverGenError`` on any
    transport failure or malformed response — the single shared error
    contract for every Notion hop this module makes (file-upload creation,
    the children PATCH, and — via the caller — the raw upload PUT)."""
    headers = {"Authorization": f"Bearer {api_key}", "Notion-Version": _NOTION_VERSION}
    data = None
    if body is not None:
        headers["Content-Type"] = "application/json"
        data = json.dumps(body).encode("utf-8")
    url = f"{_NOTION_API}{path}"
    request = urllib.request.Request(url, data=data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(request, timeout=_UPLOAD_TIMEOUT_S) as response:
            return json.loads(response.read().decode("utf-8"))
    except (urllib.error.URLError, OSError, TimeoutError, json.JSONDecodeError) as exc:
        raise CoverGenError(f"notion API {method} {path} failed: {exc}") from exc


def upload_cover_to_toggle(
    toggle_id: str, image_bytes: bytes, *, api_key: str | None = None, filename: str = "cover.png"
) -> None:
    """Default ``upload_fn`` implementation: ``POST /file_uploads`` -> the
    returned multipart ``upload_url`` PUT -> ``PATCH /blocks/{toggle_id}/children``
    referencing the new ``file_upload`` id. Ported from
    ``studio/scripts/upload_downloaded_covers.py::upload_image_to_toggle``,
    working from in-memory bytes instead of a local ``Path``. Raises on
    failure -- callers (``generate_and_upload_cover``) own the catch.
    """
    resolved_key = (api_key or os.environ.get("NOTION_KEY", "")).strip()
    if not resolved_key:
        raise CoverGenError("NOTION_KEY not set")

    # _notion_call already raises CoverGenError on transport failure; a
    # response missing the keys this function needs is its own distinct
    # failure mode (malformed/unexpected shape), so it gets its own message
    # rather than surfacing as a bare KeyError.
    upload = _notion_call(
        "POST", "/file_uploads", resolved_key, {"filename": filename, "content_type": "image/png"}
    )
    try:
        upload_url = upload["upload_url"]
        upload_id = upload["id"]
    except (KeyError, TypeError) as exc:
        raise CoverGenError(f"unexpected file_uploads response: {exc}") from exc

    boundary = "----up" + uuid.uuid4().hex
    body = (
        f'--{boundary}\r\nContent-Disposition: form-data; name="file"; '
        f'filename="{filename}"\r\nContent-Type: image/png\r\n\r\n'
    ).encode() + image_bytes + f"\r\n--{boundary}--\r\n".encode()
    headers = {
        "Authorization": f"Bearer {resolved_key}",
        "Content-Type": f"multipart/form-data; boundary={boundary}",
    }
    request = urllib.request.Request(upload_url, data=body, headers=headers, method="POST")
    try:
        with urllib.request.urlopen(request, timeout=_UPLOAD_TIMEOUT_S) as response:
            response.read()
    except (urllib.error.URLError, OSError, TimeoutError) as exc:
        raise CoverGenError(f"notion file upload PUT failed: {exc}") from exc

    image_block = {
        "object": "block",
        "type": "image",
        "image": {"type": "file_upload", "file_upload": {"id": upload_id}},
    }
    patch_path = f"/blocks/{toggle_id}/children"
    _notion_call("PATCH", patch_path, resolved_key, {"children": [image_block]})


def generate_and_upload_cover(
    row_id: str,
    ip_page_id: str,
    children_fn: ChildrenFn,
    *,
    fetch_bytes: FetchBytesFn | None = None,
    upload_fn: UploadFn | None = None,
    api_key: str | None = None,
    model: str | None = None,
) -> str | None:
    """Single-row orchestrator: find the row's Cover prompt + the IP's
    reference photos, generate the cover, upload it. NEVER raises (catches
    everything, returns a warning string or ``None`` on success) — same
    contract as ``notion_sync_media.enrich_rule`` /
    ``notion_publish_media.resolve_cover``, so a caller looping over many
    rows can treat one row's total failure as fully independent.

    Narrowly scoped to "prompt + refs -> image" -- does NOT auto-create a
    missing Cover Photo section (a separate concern, left to the caller,
    matching the existing find_*/generate_* vs. caller split established in
    ``notion_infographic_gen.py``).
    """
    resolved_fetch = fetch_bytes if fetch_bytes is not None else _default_fetch_bytes
    resolved_upload = upload_fn if upload_fn is not None else upload_cover_to_toggle

    try:
        toggle_id = find_cover_toggle(row_id, children_fn)
        if toggle_id is None:
            return f"no_cover: '{row_id}' — no cover section on this row yet"

        if toggle_has_image(toggle_id, children_fn):
            return None  # already done -- idempotent, skip silently

        prompt = find_cover_prompt(row_id, children_fn)
        if not prompt or not prompt.strip():
            return f"no_cover: '{row_id}' — no Cover prompt text yet"

        refs = find_ip_reference_images(ip_page_id, children_fn, fetch_bytes=resolved_fetch)
        if not refs:
            return f"no_cover: '{row_id}' — no reference photos for this IP"

        try:
            png_bytes = generate_cover(prompt, refs, api_key=api_key, model=model)
        except Exception as exc:  # noqa: BLE001 - must survive anything, see docstring
            return f"cover_gen_failed: '{row_id}' — {exc}"

        try:
            resolved_upload(toggle_id, png_bytes)
        except Exception as exc:  # noqa: BLE001 - must survive anything, see docstring
            return f"cover_upload_failed: '{row_id}' — {exc}"

        return None
    except Exception as exc:  # noqa: BLE001 - must survive anything, see docstring
        return f"cover_failed: '{row_id}' — {exc}"
