"""Tests for src/notion_publish_caption.py — Hook extraction + caption build.

Pure functions — Notion traffic faked via an in-memory ``children_fn``, no
network, no filesystem.
"""

from __future__ import annotations

from src import notion_publish_caption as cap


def _rt(text: str) -> dict:
    return {"rich_text": [{"plain_text": text}]}


def _page_with_hook_property(hook: str) -> dict:
    return {"properties": {"Hook": {"type": "rich_text", "rich_text": [{"plain_text": hook}]}}}


def _page_without_hook_property() -> dict:
    return {"properties": {"Name": {"type": "title", "title": [{"plain_text": "Some Post"}]}}}


def _heading(text: str) -> dict:
    return {"type": "heading_3", "heading_3": _rt(text)}


def _code(text: str) -> dict:
    return {"type": "code", "code": _rt(text)}


def _children_fn(tree: dict[str, list[dict]]):
    def fn(block_id: str) -> list[dict]:
        return tree.get(block_id, [])

    return fn


# --------------------------------------------------------------- extract_hook


def test_extract_hook_from_property_property() -> None:
    page = _page_with_hook_property("I looked at her tongue for 3 seconds.")
    assert cap.extract_hook_from_property(page) == "I looked at her tongue for 3 seconds."


def test_extract_hook_from_property_missing_returns_empty() -> None:
    assert cap.extract_hook_from_property(_page_without_hook_property()) == ""


def test_extract_hook_from_property_empty_string_returns_empty() -> None:
    page = {"properties": {"Hook": {"type": "rich_text", "rich_text": []}}}
    assert cap.extract_hook_from_property(page) == ""


def test_extract_hook_prefers_property_over_body() -> None:
    page = _page_with_hook_property("Property hook wins")
    tree = {"page-1": [_heading("Hook"), _code("Body hook — should not be used")]}
    hook = cap.extract_hook(page, "page-1", _children_fn(tree))
    assert hook == "Property hook wins"


def test_extract_hook_falls_back_to_body_when_no_property() -> None:
    page = _page_without_hook_property()
    tree = {"page-1": [_heading("🎣 Hook"), _code("Body hook text here.")]}
    hook = cap.extract_hook(page, "page-1", _children_fn(tree))
    assert hook == "Body hook text here."


def test_extract_hook_no_property_no_body_returns_empty() -> None:
    page = _page_without_hook_property()
    tree = {"page-1": [_heading("Master Script"), _code("not a hook")]}
    assert cap.extract_hook(page, "page-1", _children_fn(tree)) == ""


def test_extract_hook_from_body_stops_at_next_non_matching_content() -> None:
    """Only the block immediately following the Hook heading counts."""
    page = _page_without_hook_property()
    tree = {
        "page-1": [
            _heading("Hook"),
            _code("the real hook"),
            _code("unrelated trailing block"),
        ]
    }
    assert cap.extract_hook(page, "page-1", _children_fn(tree)) == "the real hook"


# ------------------------------------------------------------- build_caption


def test_build_caption_hook_only_no_keyword() -> None:
    assert cap.build_caption("A great hook.") == "A great hook."


def test_build_caption_appends_cta_english() -> None:
    out = cap.build_caption("A great hook.", keyword="muscle", language="en")
    assert out == 'A great hook.\n\nComment "muscle" 👇'


def test_build_caption_appends_cta_cantonese() -> None:
    out = cap.build_caption("好嘢嘅 hook", keyword="stomach", language="yue")
    assert out == '好嘢嘅 hook\n\n留言"stomach"👇'


def test_build_caption_unknown_language_falls_back_to_english_template() -> None:
    out = cap.build_caption("hook", keyword="x", language="fr")
    assert out == 'hook\n\nComment "x" 👇'


def test_build_caption_empty_hook_with_keyword_returns_cta_only() -> None:
    out = cap.build_caption("", keyword="muscle", language="en")
    assert out == 'Comment "muscle" 👇'


def test_build_caption_empty_hook_no_keyword_returns_empty() -> None:
    assert cap.build_caption("", keyword="", language="en") == ""


def test_build_caption_whitespace_only_keyword_treated_as_no_keyword() -> None:
    assert cap.build_caption("hook", keyword="   ", language="en") == "hook"
