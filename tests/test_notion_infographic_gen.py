"""Tests for src/notion_infographic_gen.py — Brief extraction + PNG generation.

Notion traffic is faked via an in-memory ``children_fn``; the OpenAI image
API is faked by monkeypatching ``urllib.request.urlopen``. No network.
"""

from __future__ import annotations

import base64
import io
import json
import urllib.error
import urllib.request

import pytest

from src import notion_infographic_gen as gen

FAKE_PNG = b"\x89PNG\r\n\x1a\nfakebytes"
PAGE_ID = "content-1"
TOGGLE_ID = "brief-toggle"


def _rt(text: str) -> dict:
    return {"rich_text": [{"plain_text": text}]}


def _heading(text: str) -> dict:
    return {"id": "h", "type": "heading_3", "heading_3": _rt(text)}


def _code(text: str) -> dict:
    return {"id": f"code-{text[:4]}", "type": "code", "code": _rt(text)}


def _para(text: str) -> dict:
    return {"id": f"p-{text[:4]}", "type": "paragraph", "paragraph": _rt(text)}


def _children_fn(tree: dict[str, list[dict]]):
    def fn(block_id: str) -> list[dict]:
        return tree.get(block_id, [])

    return fn


# ---------------------------------------------------------- find_infographic_brief


def test_brief_from_heading_then_code_block():
    tree = {
        PAGE_ID: [
            _heading("📜 Master Script"),
            _code("some script"),
            _heading("🖼️ Infographic Brief"),
            _code("Title: 3 Foods. Icons: walnuts, chives."),
            _heading("💬 Second DM"),
            _code("do not include this"),
        ]
    }
    brief = gen.find_infographic_brief(PAGE_ID, _children_fn(tree))
    assert brief == "Title: 3 Foods. Icons: walnuts, chives."


def test_brief_stops_at_next_heading():
    tree = {
        PAGE_ID: [
            _heading("Infographic Brief"),
            _para("line one"),
            _para("line two"),
            _heading("Next Section"),
            _para("excluded"),
        ]
    }
    brief = gen.find_infographic_brief(PAGE_ID, _children_fn(tree))
    assert brief == "line one\nline two"


def test_brief_from_toggle_children():
    tree = {
        PAGE_ID: [{"id": TOGGLE_ID, "type": "toggle", "toggle": _rt("🖼️ Infographic Brief")}],
        TOGGLE_ID: [_code("brief inside toggle")],
    }
    brief = gen.find_infographic_brief(PAGE_ID, _children_fn(tree))
    assert brief == "brief inside toggle"


def test_brief_absent_returns_none():
    tree = {PAGE_ID: [_heading("Master Script"), _code("script only")]}
    assert gen.find_infographic_brief(PAGE_ID, _children_fn(tree)) is None


def test_brief_marker_present_but_empty_returns_none():
    tree = {PAGE_ID: [_heading("Infographic Brief"), _heading("Next")]}
    assert gen.find_infographic_brief(PAGE_ID, _children_fn(tree)) is None


# ------------------------------------------------------------------ generate_png


def _fake_urlopen_ok(*_args, **_kwargs):
    body = json.dumps({"data": [{"b64_json": base64.b64encode(FAKE_PNG).decode()}]}).encode()

    class _Resp(io.BytesIO):
        def __enter__(self):
            return self

        def __exit__(self, *a):
            return False

    return _Resp(body)


def test_generate_png_returns_decoded_bytes(monkeypatch):
    monkeypatch.setattr(urllib.request, "urlopen", _fake_urlopen_ok)
    out = gen.generate_png("draw a nice infographic", api_key="sk-test")
    assert out == FAKE_PNG


def test_generate_png_no_key_raises(monkeypatch):
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    with pytest.raises(gen.InfographicGenError, match="OPENAI_API_KEY not set"):
        gen.generate_png("brief", api_key="")


def test_generate_png_empty_brief_raises():
    with pytest.raises(gen.InfographicGenError, match="empty infographic brief"):
        gen.generate_png("   ", api_key="sk-test")


def test_generate_png_http_error_wrapped(monkeypatch):
    def _boom(*_a, **_k):
        raise urllib.error.URLError("connection refused")

    monkeypatch.setattr(urllib.request, "urlopen", _boom)
    with pytest.raises(gen.InfographicGenError, match="image API call failed"):
        gen.generate_png("brief", api_key="sk-test")


def test_generate_png_bad_response_wrapped(monkeypatch):
    def _bad(*_a, **_k):
        class _Resp(io.BytesIO):
            def __enter__(self):
                return self

            def __exit__(self, *a):
                return False

        return _Resp(json.dumps({"data": []}).encode())

    monkeypatch.setattr(urllib.request, "urlopen", _bad)
    with pytest.raises(gen.InfographicGenError, match="unexpected image API response"):
        gen.generate_png("brief", api_key="sk-test")
