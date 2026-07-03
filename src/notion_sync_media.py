"""notion_sync_media.py — auto-attach DM infographics + language sanity check.

Phase 3 of the Notion → comment-rule bridge. ``notion_sync.sync_once()``
drafts a keyword rule the moment a Production Tracker row hits
``✅ Published``; until now the infographic image was a MANUAL step (copy a
PNG into ``data/media/guides/`` and hand-write ``image_urls``). This module
closes that step:

1. Walk the Production Tracker row's body for a toggle whose text contains
   "DM Infographic" (the 📊 emoji is optional) and take the first image
   block inside it. Notion image blocks carry either a ``file`` (expiring
   S3 signed URL) or ``external`` URL — both are handled.
2. Download it (stdlib ``urllib`` only, same rule as notion_sync.py) to
   ``data/media/guides/<keyword>-page-1.png``.
3. Set the rule's ``image_urls`` to the public URL served by this app:
   ``{PUBLIC_BASE_URL|JESSICA_BASE_URL|default}/media/guides/<file>``.

Also runs a pure-heuristic language-consistency check (CJK ratio) on the
drafted ``dm_text`` vs the rule's ``language`` — mismatches WARN, never block.

FAILURE POLICY: nothing in here may sink the sync. ``enrich_rule`` catches
everything and reports via warnings; the keyword rule always ships.

STATE: ``data/channels/notion_media_state.json`` — ``{keyword: source_url}``
(query string stripped, because Notion S3 signatures rotate on every API
call). Same load/save pattern as ``notion_sync_state.json``. A re-run only
re-downloads when the underlying Notion object actually changed.
"""

from __future__ import annotations

import json
import os
import re
import urllib.error
import urllib.parse
import urllib.request
from collections.abc import Callable
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parent.parent
MEDIA_DIR = REPO_ROOT / "data" / "media" / "guides"
STATE_PATH = REPO_ROOT / "data" / "channels" / "notion_media_state.json"

DEFAULT_BASE_URL = "https://tcm-jessica.onrender.com"
_BASE_URL_ENV_VARS = ("PUBLIC_BASE_URL", "JESSICA_BASE_URL")
_TOGGLE_MARKER = "dm infographic"
_TOGGLE_TYPES = ("toggle", "heading_1", "heading_2", "heading_3")
_DOWNLOAD_TIMEOUT_S = 30

# CJK ratio thresholds for detect_dm_language (see docstring there).
_CJK_HI = 0.40
_CJK_LO = 0.10
_CJK_RANGES = (
    (0x4E00, 0x9FFF),  # CJK Unified Ideographs
    (0x3400, 0x4DBF),  # CJK Extension A
    (0xF900, 0xFAFF),  # CJK Compatibility Ideographs
)

ChildrenFn = Callable[[str], list[dict]]


class MediaSyncError(RuntimeError):
    pass


# ------------------------------------------------------------------ language


def _is_cjk(ch: str) -> bool:
    code = ord(ch)
    return any(lo <= code <= hi for lo, hi in _CJK_RANGES)


def detect_dm_language(dm_text: str) -> str | None:
    """Heuristic language of a DM: CJK share of the letters in the text.

    >40% CJK → "yue"-ish, <10% → "en"-ish, in between (or no letters at
    all) → None = inconclusive. Pure function, no I/O.
    """
    letters = [ch for ch in dm_text if ch.isalpha()]
    if not letters:
        return None
    ratio = sum(1 for ch in letters if _is_cjk(ch)) / len(letters)
    if ratio > _CJK_HI:
        return "yue"
    if ratio < _CJK_LO:
        return "en"
    return None


def language_warning(rule_language: str, dm_text: str) -> str | None:
    """Warning string if dm_text's detected language contradicts the rule's.

    Inconclusive detection passes (returns None). WARN only — callers must
    never block a rule on this.
    """
    detected = detect_dm_language(dm_text)
    if detected is None or detected == rule_language:
        return None
    return (
        f"language_mismatch: rule language is '{rule_language}' but dm_text "
        f"reads as '{detected}' — check the drafted copy"
    )


# ------------------------------------------------------------------ keyword


def sanitize_keyword(keyword: str) -> str:
    """Lowercase and reduce to [a-z0-9-] for use in a filename."""
    slug = re.sub(r"\s+", "-", keyword.strip().lower())
    slug = re.sub(r"[^a-z0-9-]", "", slug)
    return re.sub(r"-{2,}", "-", slug).strip("-")


# --------------------------------------------------------- Notion traversal


def _block_plain_text(block: dict) -> str:
    payload = block.get(block.get("type", ""), {})
    return "".join(t.get("plain_text", "") for t in payload.get("rich_text", []))


def _image_url(block: dict) -> str | None:
    """URL from a Notion image block — 'file' (S3, expiring) or 'external'."""
    image = block.get("image") or {}
    kind = image.get("type", "")
    return (image.get(kind) or {}).get("url") or None


def find_infographic_source(row_page_id: str, children_fn: ChildrenFn) -> str | None:
    """First image URL inside the row's "DM Infographic" toggle, else None.

    Matching is loose: any toggle (or toggleable heading) whose text contains
    "dm infographic" case-insensitively — the 📊 emoji may or may not be there.
    """
    for block in children_fn(row_page_id):
        if block.get("type") not in _TOGGLE_TYPES:
            continue
        if _TOGGLE_MARKER not in _block_plain_text(block).casefold():
            continue
        for child in children_fn(block["id"]):
            if child.get("type") == "image":
                url = _image_url(child)
                if url:
                    return url
    return None


# ----------------------------------------------------------------- download


def _stable_source_url(url: str) -> str:
    """URL minus query/fragment — Notion S3 signatures rotate every fetch,
    but the object path only changes when the image itself is replaced."""
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


def _download_image(url: str, dest: Path) -> None:
    req = urllib.request.Request(url, headers={"User-Agent": "social-ip-engine/notion-sync"})
    try:
        with urllib.request.urlopen(req, timeout=_DOWNLOAD_TIMEOUT_S) as resp:
            payload = resp.read()
    except (urllib.error.URLError, OSError, TimeoutError) as exc:
        raise MediaSyncError(f"download failed for {url}: {exc}") from exc
    if not payload:
        raise MediaSyncError(f"download returned empty body for {url}")
    dest.parent.mkdir(parents=True, exist_ok=True)
    tmp = dest.with_suffix(dest.suffix + ".part")
    tmp.write_bytes(payload)
    tmp.replace(dest)


def public_media_url(filename: str) -> str:
    """Public URL this app serves the file at, base from env with fallback."""
    for var in _BASE_URL_ENV_VARS:
        value = os.environ.get(var, "").strip()
        if value:
            return f"{value.rstrip('/')}/media/guides/{filename}"
    return f"{DEFAULT_BASE_URL}/media/guides/{filename}"


# -------------------------------------------------------------- entry point


def _attach_infographic(
    rule: dict[str, Any],
    row_page_id: str,
    children_fn: ChildrenFn,
    media_dir: Path,
    state_path: Path,
) -> tuple[dict[str, Any], list[str]]:
    """Try to wire an infographic into a copy of ``rule``. May raise —
    ``enrich_rule`` owns the catch-everything guarantee."""
    keyword = str(rule.get("keyword", ""))
    slug = sanitize_keyword(keyword)
    if not slug:
        return rule, [f"no_infographic: '{keyword}' — keyword not filename-safe, left text-only"]

    source = find_infographic_source(row_page_id, children_fn)
    if source is None:
        return rule, [f"no_infographic: '{keyword}' — no DM Infographic toggle/image on row"]

    filename = f"{slug}-page-1.png"
    dest = media_dir / filename
    stable = _stable_source_url(source)
    state = _load_state(state_path)

    if state.get(slug) != stable or not dest.exists():
        _download_image(source, dest)
        _save_state(state_path, {**state, slug: stable})

    return {**rule, "image_urls": [public_media_url(filename)]}, []


def enrich_rule(
    rule: dict[str, Any],
    row_page_id: str,
    children_fn: ChildrenFn,
    *,
    media_dir: Path | None = None,
    state_path: Path | None = None,
) -> tuple[dict[str, Any], list[str]]:
    """Infographic attach + language check for one freshly drafted rule.

    Returns ``(new_rule, warnings)``. NEVER raises and NEVER mutates the
    input — on any failure the original rule ships unchanged and the problem
    lands in ``warnings`` (surfaced in the /admin/notion-sync response).
    """
    warnings: list[str] = []
    enriched = rule
    try:
        enriched, notes = _attach_infographic(
            rule,
            row_page_id,
            children_fn,
            MEDIA_DIR if media_dir is None else media_dir,
            STATE_PATH if state_path is None else state_path,
        )
        warnings.extend(notes)
    except Exception as exc:  # broad by design — sync must survive anything here
        warnings.append(f"infographic_failed: '{rule.get('keyword', '')}' — {exc}")
        enriched = rule

    mismatch = language_warning(str(rule.get("language", "")), str(rule.get("dm_text", "")))
    if mismatch:
        warnings.append(f"'{rule.get('keyword', '')}': {mismatch}")

    return enriched, warnings
