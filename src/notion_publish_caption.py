"""notion_publish_caption.py — derive an Instagram Reels caption from Notion.

Pure functions, no I/O beyond an injected ``children_fn`` (same convention as
``notion_sync_media`` / ``notion_infographic_gen``). Used by ``notion_publish``
when composing a ``PublishJob`` — kept in its own tiny module because it is
trivially unit-testable and has zero dependency on the Notion/Meta clients.

Hook source, in priority order:
1. The content page's ``Hook`` rich_text PROPERTY (this is how every content
   row is authored today — confirmed via the Content Library schema).
2. A body fallback: a ``heading_3`` containing "Hook" followed by the next
   ``code``/``paragraph`` block — mirrors ``notion_sync._extract_first_dm``'s
   heading→sibling walk, for older rows authored before the property existed.
"""

from __future__ import annotations

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
