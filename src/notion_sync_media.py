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
import uuid
from collections.abc import Callable
from pathlib import Path
from typing import Any

from src import notion_infographic_gen

REPO_ROOT = Path(__file__).resolve().parent.parent
MEDIA_DIR = REPO_ROOT / "data" / "media" / "guides"
STATE_PATH = REPO_ROOT / "data" / "channels" / "notion_media_state.json"

DEFAULT_BASE_URL = "https://tcm-jessica.onrender.com"
_BASE_URL_ENV_VARS = ("PUBLIC_BASE_URL", "JESSICA_BASE_URL")
_TOGGLE_MARKER = "dm infographic"
_INFOGRAPHIC_PROMPT_MARKER = "infographic prompt"
_GENERATED_MARKER = "generated:"
_TOGGLE_TYPES = ("toggle", "heading_1", "heading_2", "heading_3")
_DOWNLOAD_TIMEOUT_S = 30
NOTION_API = "https://api.notion.com/v1"
_WRITE_BACK_FILENAME = "dm-infographic.png"
_WRITE_BACK_TOGGLE_TEXT = "📊 DM Infographic here"

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


# ------------------------------------------------------ write-back to Notion


def _notion_key() -> str:
    key = os.environ.get("NOTION_KEY", "").strip()
    if not key:
        raise MediaSyncError("NOTION_KEY not set")
    return key


def _notion_api_call(method: str, path: str, body: dict[str, Any] | None = None) -> dict[str, Any]:
    headers = {"Authorization": f"Bearer {_notion_key()}", "Notion-Version": "2022-06-28"}
    data: bytes | None = None
    if body is not None:
        headers["Content-Type"] = "application/json"
        data = json.dumps(body).encode("utf-8")
    req = urllib.request.Request(f"{NOTION_API}{path}", data=data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req, timeout=_DOWNLOAD_TIMEOUT_S) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        # Read the response body BEFORE it's the generic "HTTP Error 403:
        # Forbidden" str(exc) would give — Notion's actual error message
        # (e.g. "token lacks insert capability") is what makes a stuck
        # writeback_pending row diagnosable rather than a mystery.
        detail = exc.read().decode(errors="replace")[:300]
        raise MediaSyncError(f"Notion API {method} {path} failed: {exc.code} {detail}") from exc
    except (urllib.error.URLError, OSError, TimeoutError, ValueError) as exc:
        raise MediaSyncError(f"Notion API {method} {path} failed: {exc}") from exc


def _upload_png_to_notion(png_bytes: bytes, filename: str) -> str:
    """Two-step Notion file upload (create session, then multipart-POST the
    bytes to the returned ``upload_url``). Returns the ``file_upload`` id to
    reference from a block. Raises ``MediaSyncError`` on any failure.

    ``filename`` is currently always the fixed constant
    ``_WRITE_BACK_FILENAME`` — never user/keyword-derived — but is
    sanitized here regardless (strip CR/LF/quotes) so a future caller can't
    accidentally break the multipart header or smuggle extra form fields by
    passing an unsanitized value through."""
    safe_filename = re.sub(r'[\r\n"]', "", filename) or _WRITE_BACK_FILENAME
    session = _notion_api_call(
        "POST", "/file_uploads", {"filename": safe_filename, "content_type": "image/png"}
    )
    upload_url = session.get("upload_url")
    file_id = session.get("id")
    if not upload_url or not file_id:
        raise MediaSyncError(f"unexpected /file_uploads response: {session!r}")

    boundary = "----notionsyncmedia" + uuid.uuid4().hex
    body = (
        f"--{boundary}\r\n"
        f'Content-Disposition: form-data; name="file"; filename="{safe_filename}"\r\n'
        "Content-Type: image/png\r\n\r\n"
    ).encode("utf-8") + png_bytes + f"\r\n--{boundary}--\r\n".encode("utf-8")
    headers = {
        "Authorization": f"Bearer {_notion_key()}",
        "Notion-Version": "2022-06-28",
        "Content-Type": f"multipart/form-data; boundary={boundary}",
    }
    req = urllib.request.Request(upload_url, data=body, headers=headers, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=_DOWNLOAD_TIMEOUT_S):
            pass
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode(errors="replace")[:300]
        raise MediaSyncError(f"Notion file upload (bytes) failed: {exc.code} {detail}") from exc
    except (urllib.error.URLError, OSError, TimeoutError) as exc:
        raise MediaSyncError(f"Notion file upload (bytes) failed: {exc}") from exc
    return str(file_id)


def _find_empty_dm_infographic_toggle(row_page_id: str, children_fn: ChildrenFn) -> str | None:
    """id of an existing, genuinely EMPTY (no image inside yet) "DM
    Infographic" toggle block, else ``None``. Restricted to
    ``type == "toggle"`` specifically (unlike ``find_infographic_source``'s
    broader ``_TOGGLE_TYPES`` match) — here we might CREATE new children
    under whatever is returned, so we must never mistake the section's plain
    (non-toggleable) ``heading_3`` for a real toggle block.

    CRITICAL: must actually check for an existing image child, not just
    match on the toggle's own text — ``PATCH .../blocks/{id}/children``
    APPENDS rather than replaces, so returning an already-filled toggle here
    would cause a second call (e.g. a retried/duplicate webhook, or crash
    recovery re-running the dedup-reuse branch in ``_generate_infographic``)
    to silently stack a second image inside the same toggle."""
    for block in children_fn(row_page_id):
        if block.get("type") != "toggle":
            continue
        if _TOGGLE_MARKER not in _block_plain_text(block).casefold():
            continue
        already_has_image = any(
            child.get("type") == "image" for child in children_fn(block["id"])
        )
        if already_has_image:
            continue
        return block["id"]
    return None


def _find_dm_infographic_prompt_anchor(row_page_id: str, children_fn: ChildrenFn) -> str | None:
    """id of the "📊 DM Infographic" section's prompt ``code`` block, to
    insert a new toggle immediately after — else ``None`` (caller falls back
    to appending at the end of the row)."""
    in_section, want_code, anchor = False, False, None
    for block in children_fn(row_page_id):
        block_type = block.get("type", "")
        text = _block_plain_text(block).casefold()
        if block_type == "heading_3":
            in_section = _TOGGLE_MARKER in text
        elif in_section and block_type == "paragraph" and _INFOGRAPHIC_PROMPT_MARKER in text:
            want_code = True
        elif in_section and want_code and block_type == "code":
            anchor = block["id"]
            want_code = False
    return anchor


def write_infographic_to_row(row_page_id: str, png_bytes: bytes, children_fn: ChildrenFn) -> None:
    """Upload ``png_bytes`` and place it in the row's "DM Infographic"
    toggle — filling an existing (empty) one if present, else creating a new
    "📊 DM Infographic here" toggle anchored right after the section's prompt
    ``code`` block (or appended at the end of the row if that anchor can't be
    found, e.g. an older row authored before this section existed).

    Idempotent in practice, not just by caller convention: re-checks
    ``find_infographic_source`` itself (cheap — no upload yet) and no-ops if
    the row already has an image ANYWHERE by the time this runs. This
    matters because the caller's own "confirmed no image yet" check can go
    stale — a retried/duplicate webhook delivery, or crash-recovery
    re-running ``_generate_infographic``'s dedup-reuse branch, can both reach
    this function a second time for the same row. This guard is what makes a
    second call a safe no-op instead of a duplicate image. It does NOT
    protect against two calls racing in TRUE parallel (both could pass this
    check before either PATCHes) — ``sync_once()`` has no cross-request lock
    today; that would need a real mutex if concurrent webhook delivery for
    the same row turns out to happen in practice.

    Raises ``MediaSyncError`` on any failure; callers own the
    catch-everything guarantee (mirrors every other write in this module)."""
    if find_infographic_source(row_page_id, children_fn) is not None:
        return  # already has an image somewhere — nothing to do

    file_id = _upload_png_to_notion(png_bytes, _WRITE_BACK_FILENAME)
    image_block = {
        "object": "block",
        "type": "image",
        "image": {"type": "file_upload", "file_upload": {"id": file_id}},
    }

    existing_toggle_id = _find_empty_dm_infographic_toggle(row_page_id, children_fn)
    if existing_toggle_id:
        _notion_api_call(
            "PATCH", f"/blocks/{existing_toggle_id}/children", {"children": [image_block]}
        )
        return

    toggle_block = {
        "object": "block",
        "type": "toggle",
        "toggle": {
            "rich_text": [{"type": "text", "text": {"content": _WRITE_BACK_TOGGLE_TEXT}}],
            "children": [image_block],
        },
    }
    patch_body: dict[str, Any] = {"children": [toggle_block]}
    anchor_id = _find_dm_infographic_prompt_anchor(row_page_id, children_fn)
    if anchor_id:
        patch_body["after"] = anchor_id
    _notion_api_call("PATCH", f"/blocks/{row_page_id}/children", patch_body)


def retry_write_back(
    row_page_id: str, slug: str, children_fn: ChildrenFn, media_dir: Path | None = None
) -> str | None:
    """Retry a previously-failed ``write_infographic_to_row`` call using the
    already-generated PNG cached locally at ``<slug>-page-1.png`` — no
    re-generation, no re-fetch of the Content page's Brief needed.

    Never raises: returns a warning string on failure (caller re-queues the
    same row/slug for the next sync — see ``_WRITEBACK_PENDING_PATH`` in
    ``notion_sync.py``), or ``None`` on success (caller drops it from the
    pending set)."""
    resolved_media_dir = MEDIA_DIR if media_dir is None else media_dir
    dest = resolved_media_dir / f"{slug}-page-1.png"
    if not dest.exists():
        return (
            f"writeback_retry_failed: '{slug}' — locally cached PNG is gone, "
            "cannot retry without re-generating"
        )
    try:
        write_infographic_to_row(row_page_id, dest.read_bytes(), children_fn)
    except Exception as exc:  # noqa: BLE001 - must survive anything, see module docstring
        return f"writeback_retry_failed: '{slug}' — {exc}"
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


def _try_write_back(
    row_page_id: str, png_bytes: bytes, children_fn: ChildrenFn, keyword: str
) -> str | None:
    """Best-effort write-back of a generated infographic onto the Production
    row's body, so it's visible in Notion without a human re-uploading it by
    hand. Isolated in its OWN try/except (not the caller's) — a write-back
    failure must never undo an already-successful generation; the rule still
    ships with ``image_urls`` set either way. Returns a warning string on
    failure, else ``None``."""
    try:
        write_infographic_to_row(row_page_id, png_bytes, children_fn)
    except Exception as exc:  # noqa: BLE001 - must survive anything, see docstring
        return f"infographic_writeback_failed: '{keyword}' — {exc}"
    return None


def _generate_infographic(
    slug: str,
    keyword: str,
    row_page_id: str,
    content_page_id: str,
    children_fn: ChildrenFn,
    media_dir: Path,
    state_path: Path,
    *,
    write_back: bool = True,
) -> tuple[dict[str, str] | None, list[str]]:
    """Generate a PNG from the content page's Infographic Brief, and (unless
    ``write_back=False``) place it back onto the Production row's body so a
    human sees it in Notion without re-uploading it manually — see
    ``write_infographic_to_row``.

    Returns ``(image_urls_patch, notes)``. ``image_urls_patch`` is ``None``
    when there was no Brief to generate from (caller ships text-only);
    otherwise it is the ``{"image_urls": [...]}`` patch to apply. ``notes``
    is always a non-empty list. May raise — the caller (``_attach_infographic``)
    is inside ``enrich_rule``'s catch-all."""
    brief = notion_infographic_gen.find_infographic_brief(content_page_id, children_fn)
    if not brief:
        return None, [
            f"no_infographic: '{keyword}' — no toggle image and no Brief to generate from"
        ]

    filename = f"{slug}-page-1.png"
    dest = media_dir / filename
    state = _load_state(state_path)

    # Dedup: if we already generated this slug's PNG (and it survived on disk),
    # never re-pay the image API — just re-attach. Guards against a re-run after
    # a mid-loop crash where the keyword rule wasn't yet persisted. Write-back
    # is still attempted here — reaching this branch means the row STILL has
    # no image in its body (see write_infographic_to_row's idempotency note),
    # most likely because a prior run generated the PNG but crashed/failed
    # before writing it back to Notion.
    if dest.exists() and str(state.get(slug, "")).startswith(_GENERATED_MARKER):
        notes = [f"generated_infographic: '{keyword}' — reused existing generated image"]
        if write_back:
            failure = _try_write_back(row_page_id, dest.read_bytes(), children_fn, keyword)
            if failure:
                notes.append(failure)
        return {"image_urls": [public_media_url(filename)]}, notes

    png = notion_infographic_gen.generate_png(brief)
    dest.parent.mkdir(parents=True, exist_ok=True)
    tmp = dest.with_suffix(dest.suffix + ".part")
    tmp.write_bytes(png)
    tmp.replace(dest)

    _save_state(state_path, {**state, slug: f"{_GENERATED_MARKER}{len(png)}"})
    notes = [f"generated_infographic: '{keyword}' — created from Brief"]
    if write_back:
        failure = _try_write_back(row_page_id, png, children_fn, keyword)
        if failure:
            notes.append(failure)
    return {"image_urls": [public_media_url(filename)]}, notes


def _attach_infographic(
    rule: dict[str, Any],
    row_page_id: str,
    children_fn: ChildrenFn,
    media_dir: Path,
    state_path: Path,
    *,
    content_page_id: str | None = None,
    generate: bool = False,
    write_back: bool = True,
) -> tuple[dict[str, Any], list[str]]:
    """Try to wire an infographic into a copy of ``rule``. May raise —
    ``enrich_rule`` owns the catch-everything guarantee."""
    keyword = str(rule.get("keyword", ""))
    slug = sanitize_keyword(keyword)
    if not slug:
        return rule, [f"no_infographic: '{keyword}' — keyword not filename-safe, left text-only"]

    source = find_infographic_source(row_page_id, children_fn)
    if source is None:
        if generate and content_page_id:
            patch, notes = _generate_infographic(
                slug,
                keyword,
                row_page_id,
                content_page_id,
                children_fn,
                media_dir,
                state_path,
                write_back=write_back,
            )
            if patch is None:
                return rule, notes
            return {**rule, **patch}, notes
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
    content_page_id: str | None = None,
    generate: bool = False,
    write_back: bool = True,
    media_dir: Path | None = None,
    state_path: Path | None = None,
) -> tuple[dict[str, Any], list[str]]:
    """Infographic attach + language check for one freshly drafted rule.

    Returns ``(new_rule, warnings)``. NEVER raises and NEVER mutates the
    input — on any failure the original rule ships unchanged and the problem
    lands in ``warnings`` (surfaced in the /admin/notion-sync response).

    When the row has no infographic in its "DM Infographic" toggle and
    ``generate`` is set (with a ``content_page_id``), the image is generated
    from the content page's "Infographic Brief" instead of shipping text-only.
    When a fresh image is generated, ``write_back`` (on by default) also
    places it back onto the Production row's body — see
    ``write_infographic_to_row`` — so it's visible in Notion without a human
    re-uploading it by hand every time. A write-back failure never affects
    the rule shipping; it only adds a warning.
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
            content_page_id=content_page_id,
            generate=generate,
            write_back=write_back,
        )
        warnings.extend(notes)
    except Exception as exc:  # broad by design — sync must survive anything here
        warnings.append(f"infographic_failed: '{rule.get('keyword', '')}' — {exc}")
        enriched = rule

    mismatch = language_warning(str(rule.get("language", "")), str(rule.get("dm_text", "")))
    if mismatch:
        warnings.append(f"'{rule.get('keyword', '')}': {mismatch}")

    return enriched, warnings
