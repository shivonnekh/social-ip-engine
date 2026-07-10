"""notion_publish_caption.py — derive an Instagram Reels caption from Notion.

Pure functions, no I/O beyond an injected ``children_fn`` (same convention as
``notion_sync_media`` / ``notion_infographic_gen``). Used by ``notion_publish``
when composing a ``PublishJob`` — kept in its own tiny module because it is
trivially unit-testable and has zero dependency on the Notion/Meta clients.

Headline source, in priority order (bug found + fixed 2026-07-08, after a
live Facebook test post — commit ``ebe5350`` — went out captioned with the
raw creative-brief Hook instead of the punchy public-facing title):
1. The Production Tracker ROW's ``🏷️ Title`` rich_text PROPERTY — a short
   clickbait viewer-facing title authored by ``studio/scripts/notion_fanout.py``
   (via ``notion_prompts.draft_title``) specifically to be public-facing. This
   is what a human actually wants leading the caption.
2. The content page's ``Hook`` rich_text PROPERTY. This is an internal
   creative-brief / script-opening line (see the row body's "Shot 1 · Hook"
   section) — useful as a fallback for rows authored before ``🏷️ Title``
   existed, but was WRONGLY being used as the primary headline before this
   fix. Never surface it over an available ``🏷️ Title``.
3. A body fallback: a ``heading_3`` containing "Hook" followed by the next
   ``code``/``paragraph`` block — mirrors ``notion_sync._extract_first_dm``'s
   heading→sibling walk, for older rows authored before the Hook property
   existed either.
"""

from __future__ import annotations

import os
from collections.abc import Callable

ChildrenFn = Callable[[str], list[dict]]

_HOOK_BODY_MARKER = "hook"
_HOOK_BODY_BLOCK_TYPES = ("code", "paragraph")

_CTA_LINE = {
    "en": 'Comment "{keyword}" 👇',
    "yue": '留言"{keyword}"👇',
}


def _rich_text(prop: dict) -> str:
    kind = prop.get("type", "")
    return "".join(t.get("plain_text", "") for t in prop.get(kind, []))


def extract_hook_from_property(content_page: dict) -> str:
    """The ``Hook`` rich_text property's plain text, or "" if absent/empty."""
    prop = content_page.get("properties", {}).get("Hook")
    if not prop:
        return ""
    return _rich_text(prop).strip()


def _block_plain_text(block: dict) -> str:
    kind = block.get("type", "")
    return "".join(t.get("plain_text", "") for t in block.get(kind, {}).get("rich_text", []))


def extract_hook_from_body(content_page_id: str, children_fn: ChildrenFn) -> str:
    """Fallback: walk the page body for a 'Hook' heading + its next block."""
    label_active = False
    for block in children_fn(content_page_id):
        block_type = block.get("type", "")
        if block_type == "heading_3":
            label_active = _HOOK_BODY_MARKER in _block_plain_text(block).casefold()
        elif label_active and block_type in _HOOK_BODY_BLOCK_TYPES:
            text = _block_plain_text(block).strip()
            if text:
                return text
    return ""


def extract_hook(content_page: dict, content_page_id: str, children_fn: ChildrenFn) -> str:
    """The Hook text for a content page: property first, body walk as fallback."""
    from_property = extract_hook_from_property(content_page)
    if from_property:
        return from_property
    return extract_hook_from_body(content_page_id, children_fn)


_DEFAULT_TITLE_PROPERTY_NAME = "🏷️ Title"


def _title_property_name() -> str:
    """Override via ``NOTION_PUBLISH_TITLE_PROP`` if the Production Tracker
    column is ever renamed — same escape hatch as ``notion_publish``'s
    ``NOTION_PUBLISH_DATE_PROP`` / ``notion_sync``'s
    ``NOTION_WIRED_CHECKBOX_PROP``. Without this, a renamed column would
    silently and permanently fall back to Hook with no error signal —
    reproducing the exact 2026-07-08 incident this module exists to fix."""
    return os.environ.get("NOTION_PUBLISH_TITLE_PROP", "").strip() or _DEFAULT_TITLE_PROPERTY_NAME


def extract_title_property(row_page: dict) -> str:
    """The Production Tracker row's ``🏷️ Title`` rich_text property's plain
    text, or "" if absent/empty. Lives on the ROW (not the content page) —
    see ``studio/scripts/notion_fanout.py``'s ``draft_title`` call, which is
    what actually authors it."""
    prop = row_page.get("properties", {}).get(_title_property_name())
    if not prop:
        return ""
    return _rich_text(prop).strip()


def extract_headline(
    row_page: dict,
    content_page: dict,
    content_page_id: str,
    children_fn: ChildrenFn,
    *,
    hook: str | None = None,
) -> tuple[str, str | None]:
    """The public-facing caption headline: the row's ``🏷️ Title`` property
    first (the punchy, purpose-authored viewer-facing title), falling back to
    the Hook (the content page's internal creative-brief line) only when no
    Title has been authored yet — see module docstring for the incident this
    ordering fixes.

    Returns ``(headline, warning)`` — ``warning`` is set (non-``None``) only
    when we fell back to Hook, so callers can surface it (same "fails open
    but loudly" contract as ``notion_publish._publish_date_eligible``): a
    blank Title should be visible in ops output, not just silently patched
    over, in case ``draft_title()`` itself starts failing upstream.

    ``hook`` lets the caller pass an ALREADY-resolved Hook (e.g. because it
    also needs it separately, for the cover-image prompt seed) so this
    function never re-triggers a second ``children_fn`` walk / Notion API
    round-trip for the same content page. If omitted, resolves it internally
    exactly as before.
    """
    title = extract_title_property(row_page)
    if title:
        return title, None

    resolved_hook = hook if hook is not None else extract_hook(content_page, content_page_id, children_fn)
    return resolved_hook, "no 🏷️ Title property set — caption fell back to the internal Hook line"


def build_caption(hook: str, *, keyword: str = "", language: str = "en") -> str:
    """Compose the Reels caption: the Hook, plus a CTA line if a keyword exists.

    Never raises. An empty ``hook`` with no ``keyword`` returns "" — the
    caller must decide whether a blank caption is acceptable (Meta allows it).
    """
    hook_text = hook.strip()
    if not keyword.strip():
        return hook_text

    template = _CTA_LINE.get(language, _CTA_LINE["en"])
    cta_line = template.format(keyword=keyword.strip())
    if not hook_text:
        return cta_line
    return f"{hook_text}\n\n{cta_line}"
