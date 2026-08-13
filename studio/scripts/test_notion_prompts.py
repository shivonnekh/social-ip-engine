"""Tests for notion_prompts.py's pure/dependency-free logic.

`_rt_chunked()` is the piece that stops a long composed prompt from 400ing
a Notion PATCH outright. Notion's rich_text API caps each `text.content`
item at 2000 characters — `_rt()` (the un-chunked helper used everywhere
else) puts the WHOLE string in one item, so any code block built from it
that crosses that ceiling fails the write.

This is not a hypothetical: measured against the real "3 Pressure Points"
carousel precedent (`scripts/gen_carousel_pressure_points.py`), a shared
~715-char brand-style block appended to a ~1,140-char panel brief already
composes to ~1,855 chars — 93% of the ceiling — before a position footer,
a language clause, or a dashboard-appended manual instruction. The same
shape already exists on the video side (rich shot-guide prose + the full
【Speech】/【Shot Guide】/【Character】/【Style】/【Camera】/【Important】
assembly in `build_jimeng_prompt`), and `apply_shot_plan`'s per-shot code
blocks still build via the un-chunked `_rt()`.

Only the pure chunking helper is unit-tested here — consistent with the
sibling test files in this folder (test_add_karaoke_captions.py,
test_pipeline_common.py, test_notion_video.py), which cover pure logic and
leave Notion/HTTP I/O untested.

Run: cd studio && python3 -m pytest scripts/test_notion_prompts.py -q
"""
from __future__ import annotations

from notion_prompts import _rt_chunked

_NOTION_RICH_TEXT_ITEM_LIMIT = 2000


def _content_of(rich_text: list[dict]) -> str:
    return "".join(item["text"]["content"] for item in rich_text)


def test_short_text_produces_a_single_chunk():
    text = "a short prompt"
    chunks = _rt_chunked(text)
    assert len(chunks) == 1
    assert chunks[0]["text"]["content"] == text


def test_short_text_matches_plain_rt_shape():
    """_rt_chunked() must be a drop-in replacement for _rt() on the common
    (short) case — same list-of-one-dict shape, not a different structure
    that happens to also work."""
    from notion_prompts import _rt
    text = "a short prompt"
    assert _rt_chunked(text) == _rt(text)


def test_text_over_the_notion_limit_splits_into_multiple_chunks():
    # The exact real-world defect this guards against: a composed prompt
    # (rich shot-guide prose + style/camera/character/importance sections)
    # crossing Notion's 2000-char single-item ceiling.
    text = "x" * 2400
    chunks = _rt_chunked(text)
    assert len(chunks) > 1
    for chunk in chunks:
        assert len(chunk["text"]["content"]) <= _NOTION_RICH_TEXT_ITEM_LIMIT


def test_chunking_never_drops_or_reorders_content():
    text = "".join(f"word{i} " for i in range(400))  # well over 2000 chars
    chunks = _rt_chunked(text)
    assert _content_of(chunks) == text


def test_each_chunk_is_at_most_the_configured_size():
    text = "y" * 5000
    chunks = _rt_chunked(text, size=1900)
    assert all(len(c["text"]["content"]) <= 1900 for c in chunks)
    assert _content_of(chunks) == text


def test_empty_text_produces_one_empty_chunk_not_zero_chunks():
    # A Notion code block's rich_text array being empty is a different
    # (and separately valid) thing from "one chunk with empty content" —
    # match _rt("")'s existing shape rather than inventing a new one.
    from notion_prompts import _rt
    assert _rt_chunked("") == _rt("")
