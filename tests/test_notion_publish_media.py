"""Tests for src/notion_publish_media.py — Reels cover resolve-or-generate.

Notion traffic faked via an in-memory ``children_fn``; downloads/generation
faked by monkeypatching ``urllib.request.urlopen`` / ``generate_png``. No
real network.
"""

from __future__ import annotations

import io
import json
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any

import pytest

from src import notion_publish_media as npm

FAKE_JPG = b"\xff\xd8\xfffakejpegbytes"
ROW_ID = "row-1"
TOGGLE_ID = "toggle-1"


def _rt(text: str) -> dict:
    return {"rich_text": [{"plain_text": text}]}


def _heading(text: str, block_id: str = "h1") -> dict:
    return {"id": block_id, "type": "heading_3", "heading_3": _rt(text)}


def _toggle(text: str = "🖼️ Image here", block_id: str = TOGGLE_ID) -> dict:
    return {"id": block_id, "type": "toggle", "toggle": _rt(text), "has_children": True}


def _image_block(url: str, kind: str = "file") -> dict:
    return {"id": "img-1", "type": "image", "image": {"type": kind, kind: {"url": url}}}


def _children_fn(tree: dict[str, list[dict]]):
    def fn(block_id: str) -> list[dict]:
        return tree.get(block_id, [])

    return fn


@pytest.fixture()
def media_paths(tmp_path: Path) -> tuple[Path, Path]:
    return tmp_path / "covers", tmp_path / "notion_publish_media_state.json"


@pytest.fixture()
def fake_urlopen(monkeypatch: pytest.MonkeyPatch) -> list[str]:
    calls: list[str] = []

    def fake(req: Any, timeout: float = 0) -> io.BytesIO:
        url = req.full_url if isinstance(req, urllib.request.Request) else req
        calls.append(url)
        return io.BytesIO(FAKE_JPG)

    monkeypatch.setattr(urllib.request, "urlopen", fake)
    return calls


# --------------------------------------------------- find_shot_one_cover_source


def test_finds_image_in_shot_one_toggle():
    tree = {
        ROW_ID: [_heading("Shot 1 · ~3s · Hook"), _toggle()],
        TOGGLE_ID: [_image_block("https://s3.example/shot1.png")],
    }
    assert npm.find_shot_one_cover_source(ROW_ID, _children_fn(tree)) == "https://s3.example/shot1.png"


def test_ignores_shot_two_image_only_wants_shot_one():
    tree = {
        ROW_ID: [
            _heading("Shot 1 · ~3s · Hook", "h1"),
            _toggle("Image here", "toggle-shot1"),  # empty — no image yet
            _heading("Shot 2 · ~5s · Root Cause", "h2"),
            _toggle("Image here", "toggle-shot2"),
        ],
        "toggle-shot1": [],
        "toggle-shot2": [_image_block("https://s3.example/shot2.png")],
    }
    assert npm.find_shot_one_cover_source(ROW_ID, _children_fn(tree)) is None


def test_no_shot_one_heading_returns_none():
    tree = {ROW_ID: [_heading("Master Script")]}
    assert npm.find_shot_one_cover_source(ROW_ID, _children_fn(tree)) is None


def test_shot_one_toggle_present_but_no_image_yet_returns_none():
    tree = {ROW_ID: [_heading("Shot 1 · Hook"), _toggle()], TOGGLE_ID: []}
    assert npm.find_shot_one_cover_source(ROW_ID, _children_fn(tree)) is None


def test_external_image_type_supported():
    tree = {
        ROW_ID: [_heading("Shot 1 · Hook"), _toggle()],
        TOGGLE_ID: [_image_block("https://cdn.example/x.jpg", kind="external")],
    }
    assert npm.find_shot_one_cover_source(ROW_ID, _children_fn(tree)) == "https://cdn.example/x.jpg"


# --------------------------------------------------------------- resolve_cover


def test_resolve_cover_reuses_shot_one_image(
    fake_urlopen: list[str], media_paths: tuple[Path, Path]
) -> None:
    media_dir, state_path = media_paths
    tree = {
        ROW_ID: [_heading("Shot 1 · Hook"), _toggle()],
        TOGGLE_ID: [_image_block("https://s3.example/shot1.png?sig=abc")],
    }
    url, warning = npm.resolve_cover(
        ROW_ID, "muscle", "some hook", _children_fn(tree), media_dir=media_dir, state_path=state_path
    )
    assert url.endswith("/media/covers/muscle-row-1-cover.jpg")
    assert warning is None
    assert (media_dir / "muscle-row-1-cover.jpg").read_bytes() == FAKE_JPG


def test_resolve_cover_dedup_skips_redownload(
    fake_urlopen: list[str], media_paths: tuple[Path, Path]
) -> None:
    media_dir, state_path = media_paths
    tree = {
        ROW_ID: [_heading("Shot 1 · Hook"), _toggle()],
        TOGGLE_ID: [_image_block("https://s3.example/shot1.png?sig=abc")],
    }
    npm.resolve_cover(ROW_ID, "muscle", "hook", _children_fn(tree), media_dir=media_dir, state_path=state_path)
    npm.resolve_cover(ROW_ID, "muscle", "hook", _children_fn(tree), media_dir=media_dir, state_path=state_path)
    assert len(fake_urlopen) == 1  # second call reused the on-disk file


def test_resolve_cover_no_shot_one_image_generate_disabled(media_paths: tuple[Path, Path]) -> None:
    media_dir, state_path = media_paths
    tree = {ROW_ID: []}
    url, warning = npm.resolve_cover(
        ROW_ID, "muscle", "hook", _children_fn(tree),
        generate=False, media_dir=media_dir, state_path=state_path,
    )
    assert url == ""
    assert "generation disabled" in warning


def test_resolve_cover_generates_from_hook_when_no_shot_one(
    media_paths: tuple[Path, Path], monkeypatch: pytest.MonkeyPatch
) -> None:
    media_dir, state_path = media_paths
    monkeypatch.setattr(npm.notion_infographic_gen, "generate_png", lambda *_a, **_k: FAKE_JPG)
    tree = {ROW_ID: []}
    url, warning = npm.resolve_cover(
        ROW_ID, "muscle", "a great hook", _children_fn(tree),
        generate=True, media_dir=media_dir, state_path=state_path,
    )
    assert url.endswith("/media/covers/muscle-row-1-cover.jpg")
    assert (media_dir / "muscle-row-1-cover.jpg").read_bytes() == FAKE_JPG
    assert "generated_cover" in warning


def test_resolve_cover_generation_dedup_skips_second_call(
    media_paths: tuple[Path, Path], monkeypatch: pytest.MonkeyPatch
) -> None:
    media_dir, state_path = media_paths
    calls: list[int] = []

    def _gen(*_a, **_k):
        calls.append(1)
        return FAKE_JPG

    monkeypatch.setattr(npm.notion_infographic_gen, "generate_png", _gen)
    tree = {ROW_ID: []}
    npm.resolve_cover(ROW_ID, "muscle", "hook", _children_fn(tree), generate=True, media_dir=media_dir, state_path=state_path)
    npm.resolve_cover(ROW_ID, "muscle", "hook", _children_fn(tree), generate=True, media_dir=media_dir, state_path=state_path)
    assert len(calls) == 1


def test_resolve_cover_no_image_no_hook_returns_empty(media_paths: tuple[Path, Path]) -> None:
    media_dir, state_path = media_paths
    tree = {ROW_ID: []}
    url, warning = npm.resolve_cover(
        ROW_ID, "muscle", "", _children_fn(tree), generate=True, media_dir=media_dir, state_path=state_path,
    )
    assert url == ""
    assert "no Hook to generate from" in warning


def test_resolve_cover_download_failure_never_raises(
    media_paths: tuple[Path, Path], monkeypatch: pytest.MonkeyPatch
) -> None:
    media_dir, state_path = media_paths

    def boom(req: Any, timeout: float = 0) -> None:
        raise urllib.error.URLError("connection refused")

    monkeypatch.setattr(urllib.request, "urlopen", boom)
    tree = {
        ROW_ID: [_heading("Shot 1 · Hook"), _toggle()],
        TOGGLE_ID: [_image_block("https://s3.example/shot1.png")],
    }
    url, warning = npm.resolve_cover(
        ROW_ID, "muscle", "hook", _children_fn(tree), media_dir=media_dir, state_path=state_path,
    )
    assert url == ""
    assert "cover_failed" in warning


def test_resolve_cover_generation_failure_never_raises(
    media_paths: tuple[Path, Path], monkeypatch: pytest.MonkeyPatch
) -> None:
    media_dir, state_path = media_paths

    def boom(*_a, **_k):
        raise npm.notion_infographic_gen.InfographicGenError("api down")

    monkeypatch.setattr(npm.notion_infographic_gen, "generate_png", boom)
    tree = {ROW_ID: []}
    url, warning = npm.resolve_cover(
        ROW_ID, "muscle", "hook", _children_fn(tree), generate=True, media_dir=media_dir, state_path=state_path,
    )
    assert url == ""
    assert "cover_failed" in warning


def test_resolve_cover_children_fn_crash_never_raises(media_paths: tuple[Path, Path]) -> None:
    media_dir, state_path = media_paths

    def broken(block_id: str) -> list[dict]:
        raise RuntimeError("notion exploded")

    url, warning = npm.resolve_cover(
        ROW_ID, "muscle", "hook", broken, media_dir=media_dir, state_path=state_path,
    )
    assert url == ""
    assert "cover_failed" in warning


def test_resolve_cover_unsafe_slug_returns_no_cover(media_paths: tuple[Path, Path]) -> None:
    media_dir, state_path = media_paths
    url, warning = npm.resolve_cover(
        ROW_ID, "!!!", "hook", _children_fn({ROW_ID: []}), media_dir=media_dir, state_path=state_path,
    )
    assert url == ""
    assert "not filename-safe" in warning


def test_public_cover_url_uses_env_base(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("PUBLIC_BASE_URL", "https://staging.example.com/")
    assert npm.public_cover_url("x-cover.jpg") == "https://staging.example.com/media/covers/x-cover.jpg"


def test_public_cover_url_defaults_when_no_env(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("PUBLIC_BASE_URL", raising=False)
    monkeypatch.delenv("JESSICA_BASE_URL", raising=False)
    assert npm.public_cover_url("x-cover.jpg") == "https://tcm-jessica.onrender.com/media/covers/x-cover.jpg"


# --------------------------------------------------------------- H1: SSRF guard


def test_is_safe_download_url_accepts_https() -> None:
    assert npm._is_safe_download_url("https://s3.example/x.png") is True


def test_is_safe_download_url_rejects_file_scheme() -> None:
    assert npm._is_safe_download_url("file:///etc/passwd") is False


def test_is_safe_download_url_rejects_http_scheme() -> None:
    assert npm._is_safe_download_url("http://s3.example/x.png") is False


def test_is_safe_download_url_rejects_ftp_scheme() -> None:
    assert npm._is_safe_download_url("ftp://example.com/x.png") is False


def test_resolve_cover_refuses_non_https_shot_one_source(
    media_paths: tuple[Path, Path],
) -> None:
    """CRITICAL/HIGH regression: a file:// (or any non-https) URL in the
    Shot-1 image block must never be fetched — would read local files /
    internal endpoints and re-serve them publicly at a predictable path."""
    media_dir, state_path = media_paths
    tree = {
        ROW_ID: [_heading("Shot 1 · Hook"), _toggle()],
        TOGGLE_ID: [_image_block("file:///etc/passwd")],
    }
    url, warning = npm.resolve_cover(
        ROW_ID, "muscle", "hook", _children_fn(tree), media_dir=media_dir, state_path=state_path,
    )
    assert url == ""
    assert "cover_failed" in warning
    assert not (media_dir / "muscle-row-1-cover.jpg").exists()


# ------------------------------------------------- filename collision (fix #5)


def test_two_rows_sharing_a_keyword_never_collide_on_filename(
    fake_urlopen: list[str], media_paths: tuple[Path, Path]
) -> None:
    """HIGH regression: two DIFFERENT Production rows using the same CTA
    keyword ('muscle') must resolve to two DISTINCT files — a shared
    filename would let one row's cover silently overwrite the other's."""
    media_dir, state_path = media_paths
    tree = {
        "row-A": [_heading("Shot 1 · Hook"), _toggle(block_id="toggle-A")],
        "toggle-A": [_image_block("https://s3.example/a.png")],
        "row-B": [_heading("Shot 1 · Hook"), _toggle(block_id="toggle-B")],
        "toggle-B": [_image_block("https://s3.example/b.png")],
    }
    fn = _children_fn(tree)

    url_a, _ = npm.resolve_cover("row-A", "muscle", "hook", fn, media_dir=media_dir, state_path=state_path)
    url_b, _ = npm.resolve_cover("row-B", "muscle", "hook", fn, media_dir=media_dir, state_path=state_path)

    assert url_a != url_b
    assert "row-a" in url_a.lower()
    assert "row-b" in url_b.lower()
    # Both files exist independently — neither overwrote the other.
    assert (media_dir / "muscle-row-a-cover.jpg").exists()
    assert (media_dir / "muscle-row-b-cover.jpg").exists()
