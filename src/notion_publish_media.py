"""notion_publish_media.py — resolve a Reels cover image for a Production row.

Cover source, in priority order:
1. Reuse the row's dedicated **🖼️ Cover Photo** section — the studio pipeline
   (``studio/scripts/notion_prompts.py`` / ``backfill_cover_dm_prompts.py``)
   writes a purpose-built thumbnail prompt there (scroll-stopping expression,
   top-third reserved for a title overlay — see the prompt template in
   ``notion_prompts.py``), distinct from any shot's in-scene still. When a
   human/agent has generated an image into that section's "🖼️ Cover here"
   toggle, it is the best available thumbnail and always wins.
2. Reuse the row's already-generated **Shot 1** still frame — the studio
   pipeline (``studio/scripts/notion_image.py``) places each shot's AI image
   inside a ``toggle`` block containing "Image here", immediately following
   that shot's ``heading_3`` (e.g. "Shot 1 · ~3s · Hook"). Falls back to this
   when the row predates the dedicated Cover Photo section, or its toggle is
   still empty.
3. Generate one from the Hook text via ``notion_infographic_gen.generate_png``
   if neither of the above has an image yet.

Mirrors the on-disk dedup + atomic-write + never-raise contract established
in ``notion_sync_media.py`` (deliberately reimplemented here in miniature
rather than importing that module's private helpers — keeps this module
independently movable/testable, consistent with this repo's existing
per-concern module split).
"""

from __future__ import annotations

import json
import os
import urllib.error
import urllib.parse
import urllib.request
from collections.abc import Callable
from pathlib import Path

from src import notion_infographic_gen
from src.notion_sync_media import sanitize_keyword

REPO_ROOT = Path(__file__).resolve().parent.parent
MEDIA_DIR = REPO_ROOT / "data" / "media" / "covers"
STATE_PATH = REPO_ROOT / "data" / "channels" / "notion_publish_media_state.json"

DEFAULT_BASE_URL = "https://tcm-jessica.onrender.com"
_BASE_URL_ENV_VARS = ("PUBLIC_BASE_URL", "JESSICA_BASE_URL")
_SHOT_ONE_MARKER = "shot 1"
_IMAGE_TOGGLE_MARKER = "image here"
_COVER_SECTION_MARKER = "cover photo"
_COVER_TOGGLE_MARKER = "cover here"
_DOWNLOAD_TIMEOUT_S = 30
_GENERATED_MARKER = "generated:"

ChildrenFn = Callable[[str], list[dict]]


def _block_plain_text(block: dict) -> str:
    kind = block.get("type", "")
    return "".join(t.get("plain_text", "") for t in block.get(kind, {}).get("rich_text", []))


def _image_url(block: dict) -> str | None:
    image = block.get("image") or {}
    kind = image.get("type", "")
    return (image.get(kind) or {}).get("url") or None


def find_shot_one_cover_source(row_page_id: str, children_fn: ChildrenFn) -> str | None:
    """First image URL inside Shot 1's "Image here" toggle, else ``None``.

    Matching is loose (case-insensitive substring), mirroring
    ``notion_sync_media.find_infographic_source``.
    """
    in_shot_one = False
    for block in children_fn(row_page_id):
        block_type = block.get("type", "")
        text = _block_plain_text(block).casefold()
        if block_type == "heading_3":
            in_shot_one = _SHOT_ONE_MARKER in text
        elif in_shot_one and block_type == "toggle" and _IMAGE_TOGGLE_MARKER in text:
            for child in children_fn(block["id"]):
                if child.get("type") == "image":
                    url = _image_url(child)
                    if url:
                        return url
            return None  # found the toggle but it has no image yet
    return None


def find_cover_photo_section_source(row_page_id: str, children_fn: ChildrenFn) -> str | None:
    """First image URL inside the dedicated "🖼️ Cover Photo" section's
    "🖼️ Cover here" toggle, else ``None``.

    Mirrors ``find_shot_one_cover_source`` exactly (same loose,
    case-insensitive substring matching against ``heading_3`` / ``toggle``
    block text) — this section sits AFTER the last shot in the row body, not
    inside a shot's scope, so there is no risk of a shot's own image toggle
    being mistaken for this one (the marker text differs: "cover here" vs
    "image here").
    """
    in_cover_section = False
    for block in children_fn(row_page_id):
        block_type = block.get("type", "")
        text = _block_plain_text(block).casefold()
        if block_type == "heading_3":
            in_cover_section = _COVER_SECTION_MARKER in text
        elif in_cover_section and block_type == "toggle" and _COVER_TOGGLE_MARKER in text:
            for child in children_fn(block["id"]):
                if child.get("type") == "image":
                    url = _image_url(child)
                    if url:
                        return url
            return None  # found the toggle but it has no image yet
    return None


def _stable_source_url(url: str) -> str:
    parts = urllib.parse.urlsplit(url)
    return urllib.parse.urlunsplit((parts.scheme, parts.netloc, parts.path, "", ""))


def _load_state(state_path: Path) -> dict[str, str]:
    if not state_path.exists():
        return {}
    try:
        data = json.loads(state_path.read_text(encoding="utf-8"))
        return data if isinstance(data, dict) else {}
    except (OSError, json.JSONDecodeError):
        return {}


def _save_state(state_path: Path, state: dict[str, str]) -> None:
    state_path.parent.mkdir(parents=True, exist_ok=True)
    state_path.write_text(
        json.dumps(state, indent=2, ensure_ascii=False, sort_keys=True), encoding="utf-8"
    )


_ALLOWED_DOWNLOAD_SCHEMES = frozenset({"https"})


def _is_safe_download_url(url: str) -> bool:
    """Only ``https://`` may be fetched by this server and re-served
    publicly. Cover source URLs come from a Notion block that could, in
    principle, contain anything a workspace editor pastes in — without this
    check, a ``file://`` or internal-network URL would be fetched by this
    process and the resulting bytes served back PUBLICLY at a predictable
    ``/media/covers/<slug>.jpg`` path, turning a content-authoring trust
    boundary into a secrets-exfiltration primitive (e.g. reading local files
    or cloud-metadata endpoints and re-publishing them). ``video_url`` is
    NOT run through this check — that URL is handed to Meta's own
    infrastructure to fetch, never fetched or re-served by this server."""
    return urllib.parse.urlsplit(url).scheme.lower() in _ALLOWED_DOWNLOAD_SCHEMES


def _download_image(url: str, dest: Path) -> None:
    if not _is_safe_download_url(url):
        raise RuntimeError(f"refusing to fetch non-https URL: {url!r}")
    req = urllib.request.Request(url, headers={"User-Agent": "social-ip-engine/notion-publish"})
    try:
        with urllib.request.urlopen(req, timeout=_DOWNLOAD_TIMEOUT_S) as resp:
            payload = resp.read()
    except (urllib.error.URLError, OSError, TimeoutError) as exc:
        raise RuntimeError(f"download failed for {url}: {exc}") from exc
    if not payload:
        raise RuntimeError(f"download returned empty body for {url}")
    dest.parent.mkdir(parents=True, exist_ok=True)
    tmp = dest.with_suffix(dest.suffix + ".part")
    tmp.write_bytes(payload)
    tmp.replace(dest)


def public_cover_url(filename: str) -> str:
    for var in _BASE_URL_ENV_VARS:
        value = os.environ.get(var, "").strip()
        if value:
            return f"{value.rstrip('/')}/media/covers/{filename}"
    return f"{DEFAULT_BASE_URL}/media/covers/{filename}"


def _cover_prompt(hook: str) -> str:
    return (
        "Vertical Instagram Reels cover frame, 9:16, premium TCM content aesthetic, "
        "clean bold title-safe text overlay area. The moment should visually capture "
        f"this hook: '{hook.strip()}'. Sharp, eye-catching, no watermarks or logos."
    )


def resolve_cover(
    row_page_id: str,
    slug: str,
    hook: str,
    children_fn: ChildrenFn,
    *,
    generate: bool = False,
    media_dir: Path | None = None,
    state_path: Path | None = None,
) -> tuple[str, str | None]:
    """Resolve a public cover_url for ``row_page_id``. Returns ``(cover_url,
    warning)`` — ``cover_url == ""`` means unresolved (caller may still
    publish without a cover; Meta falls back to ``thumb_offset``/first frame).

    NEVER raises — any failure returns ("", warning), same contract as
    ``notion_sync_media.enrich_rule``.
    """
    safe_slug = sanitize_keyword(slug)
    if not safe_slug:
        return "", "no_cover: slug not filename-safe, publishing without cover_url"

    # The row id is ALWAYS folded into the filename (not just the keyword
    # slug) — two different Production rows can share the same CTA keyword
    # (e.g. two posts both "Comment 'muscle'"), and a filename derived from
    # the keyword alone would let one row's cover resolution silently
    # overwrite another's, possibly AFTER Meta already created a container
    # for the first but BEFORE it fetched the image — attaching the wrong
    # cover to a live Reel. Folding in the row id makes collisions
    # impossible regardless of keyword reuse.
    safe_row_id = sanitize_keyword(row_page_id) or "row"
    # Same reasoning as the filename above: the dedup-state KEY must also be
    # per-row, not per-slug alone, or two rows sharing a keyword would read/
    # write each other's dedup entry and get incorrect skip-redownload
    # behavior.
    state_key = f"{safe_slug}-{safe_row_id}"
    resolved_media_dir = MEDIA_DIR if media_dir is None else media_dir
    resolved_state_path = STATE_PATH if state_path is None else state_path
    filename = f"{safe_slug}-{safe_row_id}-cover.jpg"
    dest = resolved_media_dir / filename

    try:
        source = find_cover_photo_section_source(row_page_id, children_fn)
        if source is None:
            source = find_shot_one_cover_source(row_page_id, children_fn)
        state = _load_state(resolved_state_path)

        if source is not None:
            stable = _stable_source_url(source)
            if state.get(state_key) != stable or not dest.exists():
                _download_image(source, dest)
                _save_state(resolved_state_path, {**state, state_key: stable})
            return public_cover_url(filename), None

        if not generate:
            return "", f"no_cover: '{slug}' — no Shot 1 image yet, generation disabled this run"

        if not hook.strip():
            return "", f"no_cover: '{slug}' — no Shot 1 image and no Hook to generate from"

        if dest.exists() and str(state.get(state_key, "")).startswith(_GENERATED_MARKER):
            return public_cover_url(filename), f"generated_cover: '{slug}' — reused existing"

        png = notion_infographic_gen.generate_png(_cover_prompt(hook))
        dest.parent.mkdir(parents=True, exist_ok=True)
        tmp = dest.with_suffix(dest.suffix + ".part")
        tmp.write_bytes(png)
        tmp.replace(dest)
        _save_state(resolved_state_path, {**state, state_key: f"{_GENERATED_MARKER}{len(png)}"})
        return public_cover_url(filename), f"generated_cover: '{slug}' — created from Hook"
    except Exception as exc:  # noqa: BLE001 - must survive anything, see docstring
        return "", f"cover_failed: '{slug}' — {exc}"
