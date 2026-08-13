"""Tests for src/notion_publish_carousel_media.py — panel image URL
resolution from a carousel row's Notion body, including the HOLE contract
(an incomplete panel set must never be reported as publishable)."""

from __future__ import annotations

from src.notion_publish_carousel_media import find_carousel_panel_sources


def _heading(text: str) -> dict:
    return {"type": "heading_3", "heading_3": {"rich_text": [{"plain_text": text}]}}


def _panel_here_toggle(toggle_id: str, has_image: bool) -> dict:
    return {
        "id": toggle_id,
        "type": "toggle",
        "toggle": {"rich_text": [{"plain_text": "🖼️ Panel here"}]},
        "has_children": has_image,
    }


def _image_block(url: str) -> dict:
    return {"type": "image", "image": {"type": "file", "file": {"url": url}}}


def _children_fn(blocks: dict[str, list[dict]]):
    def fn(block_id: str) -> list[dict]:
        return blocks.get(block_id, [])
    return fn


def test_resolves_urls_in_panel_order():
    row_children = [
        _heading("Panel 1 · Cover"),
        _panel_here_toggle("t1", True),
        _heading("Panel 2 · Anmian"),
        _panel_here_toggle("t2", True),
        _heading("Panel 3 · Closing"),
        _panel_here_toggle("t3", True),
    ]
    blocks = {
        "row-1": row_children,
        "t1": [_image_block("https://s3.example/p1.png")],
        "t2": [_image_block("https://s3.example/p2.png")],
        "t3": [_image_block("https://s3.example/p3.png")],
    }
    urls, complete = find_carousel_panel_sources("row-1", _children_fn(blocks))
    assert complete is True
    assert urls == [
        "https://s3.example/p1.png",
        "https://s3.example/p2.png",
        "https://s3.example/p3.png",
    ]


def test_empty_panel_toggle_is_a_hole():
    row_children = [
        _heading("Panel 1 · Cover"),
        _panel_here_toggle("t1", True),
        _heading("Panel 2 · Anmian"),
        _panel_here_toggle("t2", False),  # never generated yet
        _heading("Panel 3 · Closing"),
        _panel_here_toggle("t3", True),
    ]
    blocks = {
        "row-1": row_children,
        "t1": [_image_block("https://s3.example/p1.png")],
        "t3": [_image_block("https://s3.example/p3.png")],
    }
    urls, complete = find_carousel_panel_sources("row-1", _children_fn(blocks))
    assert complete is False
    # Only what was resolved BEFORE the hole — caller must never use this
    # for a publish, but it's useful for logging.
    assert urls == ["https://s3.example/p1.png"]


def test_toggle_with_children_flag_but_no_actual_image_child_is_also_a_hole():
    """has_children=True but the toggle's children are something other than
    an image block (e.g. only a text note) — must still be treated as a
    hole, not silently resolved to None-then-skipped."""
    row_children = [
        _heading("Panel 1 · Cover"),
        _panel_here_toggle("t1", True),
    ]
    blocks = {
        "row-1": row_children,
        "t1": [{"type": "paragraph", "paragraph": {"rich_text": []}}],
    }
    urls, complete = find_carousel_panel_sources("row-1", _children_fn(blocks))
    assert complete is False
    assert urls == []


def test_no_panels_at_all_is_complete_with_empty_list():
    """A video-only row (no carousel section) is not an error case here —
    it's "not carousel content," which the caller's own MIN_PANELS check
    handles, not this function."""
    row_children = [
        _heading("Shot 1 · Hook"),
    ]
    urls, complete = find_carousel_panel_sources("row-1", _children_fn({"row-1": row_children}))
    assert complete is True
    assert urls == []


def test_only_walks_blocks_inside_panel_sections():
    """A "Cover Photo" or "DM Infographic" trailer section's image toggle
    must never be mistaken for a carousel panel."""
    row_children = [
        _heading("Panel 1 · Cover"),
        _panel_here_toggle("t1", True),
        _heading("🖼️ Cover Photo"),
        {
            "id": "cover-toggle",
            "type": "toggle",
            "toggle": {"rich_text": [{"plain_text": "🖼️ Cover here"}]},
            "has_children": True,
        },
    ]
    blocks = {
        "row-1": row_children,
        "t1": [_image_block("https://s3.example/p1.png")],
        "cover-toggle": [_image_block("https://s3.example/cover.png")],
    }
    urls, complete = find_carousel_panel_sources("row-1", _children_fn(blocks))
    assert complete is True
    assert urls == ["https://s3.example/p1.png"]
