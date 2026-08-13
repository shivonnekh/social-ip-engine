"""notion_publish_carousel_media.py — resolve a carousel row's panel image
URLs from its Notion body, in deterministic (Notion block) order.

Sibling of ``notion_publish_media.py`` (Reel cover resolution), but a
carousel has no separate "cover" concept — every panel IS the content, and
ALL of them must be present before anything is allowed to publish. A row
with 4 filled panels out of 5 must never silently ship as a 4-panel post;
see ``find_carousel_panel_sources``'s "hole" contract below.
"""

from __future__ import annotations

from typing import Protocol


class ChildrenFn(Protocol):
    def __call__(self, block_id: str) -> list[dict]: ...


def _block_plain_text(block: dict) -> str:
    kind = block.get("type", "")
    return "".join(t.get("plain_text", "") for t in block.get(kind, {}).get("rich_text", []))


def _image_url(block: dict) -> str | None:
    image = block.get("image") or {}
    kind = image.get("type", "")
    return (image.get(kind) or {}).get("url") or None


def find_carousel_panel_sources(
    row_page_id: str, children_fn: ChildrenFn
) -> tuple[list[str], bool]:
    """Ordered panel image URLs from the row body's "🎠 Carousel Panels"
    section (each ``heading_3`` block whose text starts with "panel" —
    matches ``notion_carousel_prompts.carousel_blocks()``'s "Panel N ·
    <role>" convention exactly, same title-prefix detection the dashboard's
    ``state.py::row_detail`` already uses).

    Returns ``(image_urls, complete)``:
    - ``complete`` is ``False`` the moment ANY panel's "🖼️ Panel here" toggle
      is found empty (a HOLE) — the caller must skip the row rather than
      silently publish a 4-panel set that should be 5. ``image_urls`` in
      that case contains whatever was resolved before the hole, for
      logging only; it must never be published.
    - An empty ``image_urls`` with ``complete=True`` means the row has no
      carousel panels at all (not carousel content) — the caller's own
      ``MIN_PANELS`` check handles that, this function has no opinion on
      panel count.

    Panel order is Notion block order, which is deterministic (Notion does
    not reorder a page's children on its own).
    """
    urls: list[str] = []
    in_panel = False
    for block in children_fn(row_page_id):
        block_type = block.get("type", "")
        text = _block_plain_text(block).casefold()
        if block_type == "heading_3":
            in_panel = text.startswith("panel")
            continue
        if not in_panel:
            continue
        if block_type == "toggle" and "panel here" in text:
            found: str | None = None
            if block.get("has_children"):
                for child in children_fn(block["id"]):
                    if child.get("type") == "image":
                        found = _image_url(child)
                        break
            if not found:
                return urls, False  # HOLE — refuse to publish an incomplete set
            urls.append(found)
    return urls, True
