"""Tests for src/notion_cover_gen.py — Reels cover generation from a Production
row's already-authored "Cover prompt" text + the IP's reference face photos.

Notion traffic faked via an in-memory ``children_fn``; downloads/uploads/
generation faked via dependency injection (``fetch_bytes``, ``upload_fn``) or
monkeypatching ``urllib.request.urlopen``. No real network calls anywhere in
this file.
"""

from __future__ import annotations

import base64
import io
import json
import urllib.error
import urllib.request
from typing import Any

import pytest

from src import notion_cover_gen as ncg

ROW_ID = "row-1"
IP_PAGE_ID = "ip-1"
TOGGLE_ID = "toggle-cover"
CODE_ID = "code-1"
FAKE_PNG = b"\x89PNGfakebytes"


def _rt(text: str) -> dict:
    return {"rich_text": [{"plain_text": text}]}


def _heading(text: str, block_id: str = "h-cover") -> dict:
    return {"id": block_id, "type": "heading_3", "heading_3": _rt(text)}


def _toggle(text: str = "🖼️ Cover here", block_id: str = TOGGLE_ID) -> dict:
    return {"id": block_id, "type": "toggle", "toggle": _rt(text), "has_children": True}


def _code_block(text: str, block_id: str = CODE_ID) -> dict:
    return {"id": block_id, "type": "code", "code": _rt(text)}


def _bold_paragraph(text: str, block_id: str = "bold-1") -> dict:
    return {"id": block_id, "type": "paragraph", "paragraph": _rt(text)}


def _divider(block_id: str = "div-1") -> dict:
    return {"id": block_id, "type": "divider", "divider": {}}


def _image_block(url: str, kind: str = "file", block_id: str = "img-1") -> dict:
    return {"id": block_id, "type": "image", "image": {"type": kind, kind: {"url": url}}}


def _children_fn(tree: dict[str, list[dict]]):
    def fn(block_id: str) -> list[dict]:
        return tree.get(block_id, [])

    return fn


def _well_formed_cover_section(prompt_text: str = "a cinematic cover shot") -> list[dict]:
    return [
        _heading("🖼️ Cover Photo"),
        _bold_paragraph("🖼️ Cover prompt (thumbnail → GPT)"),
        _code_block(prompt_text),
        _toggle("🖼️ Cover here"),
        _divider(),
    ]


# --------------------------------------------------------------- find_cover_prompt


def test_finds_cover_prompt_in_well_formed_row():
    tree = {ROW_ID: _well_formed_cover_section("draw Jackie Chan smiling")}
    assert ncg.find_cover_prompt(ROW_ID, _children_fn(tree)) == "draw Jackie Chan smiling"


def test_find_cover_prompt_returns_none_when_no_cover_heading():
    tree = {ROW_ID: [_heading("Master Script")]}
    assert ncg.find_cover_prompt(ROW_ID, _children_fn(tree)) is None


def test_find_cover_prompt_ignores_legacy_reel_cover_photo_heading():
    """Regression pinned by audit_cover_schema.py: the legacy '🖼️ Reel Cover
    Photo Image Prompt' heading must NOT be mistaken for the new-schema
    '🖼️ Cover Photo' section, or an old row's stale content gets misread."""
    tree = {
        ROW_ID: [
            _heading("🖼️ Reel Cover Photo Image Prompt", "h-old"),
            _code_block("an old, unrelated prompt"),
        ]
    }
    assert ncg.find_cover_prompt(ROW_ID, _children_fn(tree)) is None


def test_find_cover_prompt_returns_none_when_no_code_block_before_next_heading():
    tree = {
        ROW_ID: [
            _heading("🖼️ Cover Photo"),
            _bold_paragraph("🖼️ Cover prompt (thumbnail → GPT)"),
            # no code block here -- straight to the toggle
            _toggle("🖼️ Cover here"),
            _divider(),
        ]
    }
    assert ncg.find_cover_prompt(ROW_ID, _children_fn(tree)) is None


def test_find_cover_prompt_returns_none_when_code_block_is_empty():
    tree = {ROW_ID: _well_formed_cover_section(prompt_text="")}
    assert ncg.find_cover_prompt(ROW_ID, _children_fn(tree)) is None


# --------------------------------------------------------------- find_cover_toggle


def test_find_cover_toggle_returns_id_when_section_present():
    tree = {ROW_ID: _well_formed_cover_section()}
    assert ncg.find_cover_toggle(ROW_ID, _children_fn(tree)) == TOGGLE_ID


def test_find_cover_toggle_ignores_shot_image_toggle():
    """A shot's own '🖼️ Image here' toggle must never be mistaken for the
    dedicated Cover Photo section's '🖼️ Cover here' toggle."""
    tree = {
        ROW_ID: [
            _heading("Shot 1 · ~3s · Hook", "h1"),
            {"id": "toggle-shot1", "type": "toggle", "toggle": _rt("🖼️ Image here")},
        ]
    }
    assert ncg.find_cover_toggle(ROW_ID, _children_fn(tree)) is None


def test_find_cover_toggle_returns_none_when_no_cover_heading():
    tree = {ROW_ID: [_heading("Master Script")]}
    assert ncg.find_cover_toggle(ROW_ID, _children_fn(tree)) is None


def test_find_cover_toggle_ignores_legacy_heading():
    tree = {
        ROW_ID: [
            _heading("🖼️ Reel Cover Photo Image Prompt", "h-old"),
            _toggle("🖼️ Cover here", "toggle-old"),
        ]
    }
    assert ncg.find_cover_toggle(ROW_ID, _children_fn(tree)) is None


# ----------------------------------------------------------------- toggle_has_image


def test_toggle_has_image_true_when_image_present():
    tree = {TOGGLE_ID: [_image_block("https://s3.example/cover.png")]}
    assert ncg.toggle_has_image(TOGGLE_ID, _children_fn(tree)) is True


def test_toggle_has_image_false_when_toggle_empty():
    tree = {TOGGLE_ID: []}
    assert ncg.toggle_has_image(TOGGLE_ID, _children_fn(tree)) is False


def test_toggle_has_image_false_when_only_non_image_children():
    tree = {TOGGLE_ID: [_bold_paragraph("some note")]}
    assert ncg.toggle_has_image(TOGGLE_ID, _children_fn(tree)) is False


# ---------------------------------------------------------- find_ip_reference_images


def test_find_ip_reference_images_fetches_file_and_external_blocks():
    tree = {
        IP_PAGE_ID: [
            _image_block("https://s3.example/a.png", kind="file", block_id="a"),
            _image_block("https://cdn.example/b.jpg", kind="external", block_id="b"),
        ]
    }
    calls: list[str] = []

    def fetch(url: str) -> bytes:
        calls.append(url)
        return b"bytes-for-" + url.encode()

    result = ncg.find_ip_reference_images(IP_PAGE_ID, _children_fn(tree), fetch_bytes=fetch)
    assert result == [b"bytes-for-https://s3.example/a.png", b"bytes-for-https://cdn.example/b.jpg"]
    assert calls == ["https://s3.example/a.png", "https://cdn.example/b.jpg"]


def test_find_ip_reference_images_skips_non_image_blocks():
    tree = {IP_PAGE_ID: [_heading("Some heading"), _bold_paragraph("note")]}
    calls: list[str] = []
    result = ncg.find_ip_reference_images(
        IP_PAGE_ID, _children_fn(tree), fetch_bytes=lambda url: calls.append(url) or b"x"
    )
    assert result == []
    assert calls == []


def test_find_ip_reference_images_skips_blocks_with_no_url():
    empty_image_block = {"id": "img-empty", "type": "image", "image": {"type": "file", "file": {}}}
    tree = {IP_PAGE_ID: [empty_image_block]}
    calls: list[str] = []
    result = ncg.find_ip_reference_images(
        IP_PAGE_ID, _children_fn(tree), fetch_bytes=lambda url: calls.append(url) or b"x"
    )
    assert result == []
    assert calls == []


def test_find_ip_reference_images_refuses_non_https_url():
    """SSRF regression, same guarantee as
    test_resolve_cover_refuses_non_https_shot_one_source in
    tests/test_notion_publish_media.py: a file:// (or any non-https) URL in
    an IP reference image block must never reach fetch_bytes."""
    tree = {IP_PAGE_ID: [_image_block("file:///etc/passwd", kind="file")]}
    calls: list[str] = []
    result = ncg.find_ip_reference_images(
        IP_PAGE_ID, _children_fn(tree), fetch_bytes=lambda url: calls.append(url) or b"x"
    )
    assert result == []
    assert calls == []  # never even attempted


def test_find_ip_reference_images_refuses_http_url():
    tree = {IP_PAGE_ID: [_image_block("http://s3.example/x.png")]}
    calls: list[str] = []
    result = ncg.find_ip_reference_images(
        IP_PAGE_ID, _children_fn(tree), fetch_bytes=lambda url: calls.append(url) or b"x"
    )
    assert result == []
    assert calls == []


def test_find_ip_reference_images_one_failure_does_not_abort_others():
    tree = {
        IP_PAGE_ID: [
            _image_block("https://s3.example/good1.png", block_id="g1"),
            _image_block("https://s3.example/boom.png", block_id="bad"),
            _image_block("https://s3.example/good2.png", block_id="g2"),
        ]
    }

    def fetch(url: str) -> bytes:
        if "boom" in url:
            raise RuntimeError("network exploded")
        return b"ok-" + url.encode()

    result = ncg.find_ip_reference_images(IP_PAGE_ID, _children_fn(tree), fetch_bytes=fetch)
    assert result == [b"ok-https://s3.example/good1.png", b"ok-https://s3.example/good2.png"]


def test_find_ip_reference_images_logs_on_fetch_failure(caplog: pytest.LogCaptureFixture):
    """HIGH regression (code review): a real download outage (revoked
    token, network egress issue) previously looked EXACTLY like "this IP
    has zero reference photos authored yet" — same empty-list result, and
    nothing logged anywhere to tell the two apart. Assert the failure is
    now logged, not silently discarded."""
    tree = {IP_PAGE_ID: [_image_block("https://s3.example/boom.png")]}

    def fetch(url: str) -> bytes:
        raise RuntimeError("token revoked")

    with caplog.at_level("WARNING", logger="notion_cover_gen"):
        result = ncg.find_ip_reference_images(IP_PAGE_ID, _children_fn(tree), fetch_bytes=fetch)

    assert result == []
    assert any("token revoked" in record.message for record in caplog.records)


def test_find_ip_reference_images_logs_on_unsafe_url(caplog: pytest.LogCaptureFixture):
    tree = {IP_PAGE_ID: [_image_block("file:///etc/passwd")]}

    with caplog.at_level("WARNING", logger="notion_cover_gen"):
        result = ncg.find_ip_reference_images(IP_PAGE_ID, _children_fn(tree), fetch_bytes=lambda url: b"x")

    assert result == []
    assert any("unsafe url" in record.message for record in caplog.records)


# --------------------------------------------------------------------- generate_cover


def _fake_images_edits_response(monkeypatch: pytest.MonkeyPatch, png: bytes) -> list[Any]:
    calls: list[Any] = []

    def fake(req: Any, timeout: float = 0) -> io.BytesIO:
        calls.append(req)
        payload = json.dumps({"data": [{"b64_json": base64.b64encode(png).decode()}]}).encode()
        return io.BytesIO(payload)

    monkeypatch.setattr(urllib.request, "urlopen", fake)
    return calls


def test_generate_cover_raises_for_missing_api_key(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    with pytest.raises(ncg.CoverGenError, match="API_KEY"):
        ncg.generate_cover("a prompt", [b"ref-bytes"], api_key="")


def test_generate_cover_raises_for_empty_prompt():
    with pytest.raises(ncg.CoverGenError, match="prompt"):
        ncg.generate_cover("   ", [b"ref-bytes"], api_key="sk-test")


def test_generate_cover_raises_for_zero_reference_images():
    """THE single most important test in this whole module: a cover
    generated with ZERO reference photos of the IP has no guarantee of
    drawing the right person. This is the exact 2026-07-08 wrong-person-
    drawn incident this feature exists to prevent — generate_cover MUST
    hard-refuse rather than silently falling back to a blind (no-reference)
    generation call."""
    with pytest.raises(ncg.CoverGenError, match="reference"):
        ncg.generate_cover("a prompt", [], api_key="sk-test")


def test_generate_cover_raises_for_http_failure(monkeypatch: pytest.MonkeyPatch):
    def boom(req: Any, timeout: float = 0) -> None:
        raise urllib.error.URLError("connection refused")

    monkeypatch.setattr(urllib.request, "urlopen", boom)
    with pytest.raises(ncg.CoverGenError, match="failed"):
        ncg.generate_cover("a prompt", [b"ref-bytes"], api_key="sk-test")


def test_generate_cover_raises_for_malformed_response(monkeypatch: pytest.MonkeyPatch):
    def fake(req: Any, timeout: float = 0) -> io.BytesIO:
        return io.BytesIO(json.dumps({"unexpected": "shape"}).encode())

    monkeypatch.setattr(urllib.request, "urlopen", fake)
    with pytest.raises(ncg.CoverGenError, match="response"):
        ncg.generate_cover("a prompt", [b"ref-bytes"], api_key="sk-test")


def test_generate_cover_raises_for_invalid_json_body(monkeypatch: pytest.MonkeyPatch):
    """HIGH regression (code review): a non-JSON response body (proxy error
    page, truncated response, HTML 5xx served with a 200 status) previously
    raised a raw json.JSONDecodeError instead of CoverGenError, violating
    this function's own documented contract."""

    def fake(req: Any, timeout: float = 0) -> io.BytesIO:
        return io.BytesIO(b"<html>not json at all</html>")

    monkeypatch.setattr(urllib.request, "urlopen", fake)
    with pytest.raises(ncg.CoverGenError, match="failed"):
        ncg.generate_cover("a prompt", [b"ref-bytes"], api_key="sk-test")


def test_generate_cover_success_returns_decoded_bytes(monkeypatch: pytest.MonkeyPatch):
    calls = _fake_images_edits_response(monkeypatch, FAKE_PNG)
    result = ncg.generate_cover("a prompt", [b"ref-bytes-1", b"ref-bytes-2"], api_key="sk-test")
    assert result == FAKE_PNG
    assert len(calls) == 1


# --------------------------------------------------------- _default_fetch_bytes


def test_default_fetch_bytes_returns_response_body(monkeypatch: pytest.MonkeyPatch):
    def fake(req: Any, timeout: float = 0) -> io.BytesIO:
        return io.BytesIO(b"real-bytes")

    monkeypatch.setattr(urllib.request, "urlopen", fake)
    assert ncg._default_fetch_bytes("https://s3.example/ref.png") == b"real-bytes"


# ------------------------------------------------------------- upload_cover_to_toggle


def test_upload_cover_to_toggle_raises_for_missing_notion_key(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.delenv("NOTION_KEY", raising=False)
    with pytest.raises(ncg.CoverGenError, match="NOTION_KEY"):
        ncg.upload_cover_to_toggle(TOGGLE_ID, FAKE_PNG, api_key="")


def test_upload_cover_to_toggle_happy_path(monkeypatch: pytest.MonkeyPatch):
    calls: list[str] = []

    def fake(req: Any, timeout: float = 0) -> io.BytesIO:
        url = req.full_url if isinstance(req, urllib.request.Request) else req
        calls.append(url)
        if url == f"{ncg._NOTION_API}/file_uploads":
            return io.BytesIO(
                json.dumps({"id": "upload-1", "upload_url": "https://notion-upload.example/put"}).encode()
            )
        if url == "https://notion-upload.example/put":
            return io.BytesIO(b"")
        if url == f"{ncg._NOTION_API}/blocks/{TOGGLE_ID}/children":
            return io.BytesIO(json.dumps({"results": []}).encode())
        raise AssertionError(f"unexpected URL: {url}")

    monkeypatch.setattr(urllib.request, "urlopen", fake)
    ncg.upload_cover_to_toggle(TOGGLE_ID, FAKE_PNG, api_key="ntn-test")
    assert calls == [
        f"{ncg._NOTION_API}/file_uploads",
        "https://notion-upload.example/put",
        f"{ncg._NOTION_API}/blocks/{TOGGLE_ID}/children",
    ]


def test_upload_cover_to_toggle_raises_when_put_fails(monkeypatch: pytest.MonkeyPatch):
    def fake(req: Any, timeout: float = 0) -> io.BytesIO:
        url = req.full_url if isinstance(req, urllib.request.Request) else req
        if url == f"{ncg._NOTION_API}/file_uploads":
            return io.BytesIO(
                json.dumps({"id": "upload-1", "upload_url": "https://notion-upload.example/put"}).encode()
            )
        raise urllib.error.URLError("connection refused")

    monkeypatch.setattr(urllib.request, "urlopen", fake)
    with pytest.raises(ncg.CoverGenError, match="upload PUT failed"):
        ncg.upload_cover_to_toggle(TOGGLE_ID, FAKE_PNG, api_key="ntn-test")


def test_upload_cover_to_toggle_raises_when_file_uploads_call_fails(monkeypatch: pytest.MonkeyPatch):
    """HIGH regression (code review): the very first Notion hop
    (POST /file_uploads, made via _notion_call) previously had zero error
    handling — a raw URLError would escape instead of CoverGenError."""

    def boom(req: Any, timeout: float = 0) -> None:
        raise urllib.error.URLError("connection refused")

    monkeypatch.setattr(urllib.request, "urlopen", boom)
    with pytest.raises(ncg.CoverGenError, match="notion API POST /file_uploads failed"):
        ncg.upload_cover_to_toggle(TOGGLE_ID, FAKE_PNG, api_key="ntn-test")


def test_upload_cover_to_toggle_raises_for_malformed_file_uploads_response(
    monkeypatch: pytest.MonkeyPatch,
):
    """HIGH regression (code review): a file_uploads response missing
    'upload_url'/'id' previously raised a bare KeyError instead of
    CoverGenError."""

    def fake(req: Any, timeout: float = 0) -> io.BytesIO:
        return io.BytesIO(json.dumps({"unexpected": "shape"}).encode())

    monkeypatch.setattr(urllib.request, "urlopen", fake)
    with pytest.raises(ncg.CoverGenError, match="unexpected file_uploads response"):
        ncg.upload_cover_to_toggle(TOGGLE_ID, FAKE_PNG, api_key="ntn-test")


# --------------------------------------------------------- generate_and_upload_cover


@pytest.fixture()
def spy_generate(monkeypatch: pytest.MonkeyPatch) -> list[Any]:
    calls: list[Any] = []

    def fake(*args: Any, **kwargs: Any) -> bytes:
        calls.append((args, kwargs))
        return FAKE_PNG

    monkeypatch.setattr(ncg, "generate_cover", fake)
    return calls


def test_generate_and_upload_cover_happy_path(spy_generate: list[Any]):
    tree = {ROW_ID: _well_formed_cover_section("a great prompt"), TOGGLE_ID: [], IP_PAGE_ID: [_image_block("https://s3.example/ref.png")]}
    upload_calls: list[Any] = []

    result = ncg.generate_and_upload_cover(
        ROW_ID,
        IP_PAGE_ID,
        _children_fn(tree),
        fetch_bytes=lambda url: b"ref-bytes",
        upload_fn=lambda toggle_id, png: upload_calls.append((toggle_id, png)),
    )

    assert result is None
    assert len(spy_generate) == 1
    assert upload_calls == [(TOGGLE_ID, FAKE_PNG)]


def test_generate_and_upload_cover_already_has_image_short_circuits(spy_generate: list[Any]):
    tree = {
        ROW_ID: _well_formed_cover_section("a great prompt"),
        TOGGLE_ID: [_image_block("https://s3.example/already-there.png")],
    }
    fetch_calls: list[str] = []
    upload_calls: list[Any] = []

    result = ncg.generate_and_upload_cover(
        ROW_ID,
        IP_PAGE_ID,
        _children_fn(tree),
        fetch_bytes=lambda url: fetch_calls.append(url) or b"x",
        upload_fn=lambda toggle_id, png: upload_calls.append((toggle_id, png)),
    )

    assert result is None
    assert spy_generate == []  # generate_cover never invoked
    assert fetch_calls == []  # no reference-photo fetch attempted
    assert upload_calls == []  # no upload attempted


def test_generate_and_upload_cover_missing_cover_section_warns(spy_generate: list[Any]):
    tree = {ROW_ID: [_heading("Master Script")]}
    result = ncg.generate_and_upload_cover(
        ROW_ID,
        IP_PAGE_ID,
        _children_fn(tree),
        fetch_bytes=lambda url: b"x",
        upload_fn=lambda *_a: None,
    )
    assert result is not None
    assert "cover section" in result
    assert spy_generate == []


def test_generate_and_upload_cover_missing_prompt_warns(spy_generate: list[Any]):
    tree = {
        ROW_ID: [
            _heading("🖼️ Cover Photo"),
            _toggle("🖼️ Cover here"),  # no code block -- no prompt authored yet
            _divider(),
        ],
        TOGGLE_ID: [],
    }
    result = ncg.generate_and_upload_cover(
        ROW_ID,
        IP_PAGE_ID,
        _children_fn(tree),
        fetch_bytes=lambda url: b"x",
        upload_fn=lambda *_a: None,
    )
    assert result is not None
    assert "prompt" in result
    assert spy_generate == []


def test_generate_and_upload_cover_zero_reference_photos_warns(spy_generate: list[Any]):
    tree = {ROW_ID: _well_formed_cover_section("a great prompt"), TOGGLE_ID: [], IP_PAGE_ID: []}
    result = ncg.generate_and_upload_cover(
        ROW_ID,
        IP_PAGE_ID,
        _children_fn(tree),
        fetch_bytes=lambda url: b"x",
        upload_fn=lambda *_a: None,
    )
    assert result is not None
    assert "reference" in result
    # per generate_cover's no-blind-generation contract: zero refs must
    # short-circuit BEFORE generate_cover is ever called.
    assert spy_generate == []


def test_generate_and_upload_cover_generate_error_never_propagates(monkeypatch: pytest.MonkeyPatch):
    tree = {ROW_ID: _well_formed_cover_section("a great prompt"), TOGGLE_ID: [], IP_PAGE_ID: [_image_block("https://s3.example/ref.png")]}

    def boom(*_a: Any, **_k: Any) -> bytes:
        raise ncg.CoverGenError("api exploded")

    monkeypatch.setattr(ncg, "generate_cover", boom)
    upload_calls: list[Any] = []

    result = ncg.generate_and_upload_cover(
        ROW_ID,
        IP_PAGE_ID,
        _children_fn(tree),
        fetch_bytes=lambda url: b"ref-bytes",
        upload_fn=lambda toggle_id, png: upload_calls.append((toggle_id, png)),
    )

    assert result is not None
    assert "api exploded" in result
    assert upload_calls == []  # never reached upload


def test_generate_and_upload_cover_generate_non_cover_gen_error_never_propagates(
    monkeypatch: pytest.MonkeyPatch,
):
    """HIGH regression (code review): the generate-step catch used to only
    catch CoverGenError, unlike the upload step right below it — any OTHER
    exception type (e.g. a bug surfacing as AttributeError/ValueError) would
    have escaped this inner try, relying entirely on the outer catch-all by
    accident rather than by design. Assert the inner catch itself is broad."""
    tree = {
        ROW_ID: _well_formed_cover_section("a great prompt"),
        TOGGLE_ID: [],
        IP_PAGE_ID: [_image_block("https://s3.example/ref.png")],
    }

    def boom(*_a: Any, **_k: Any) -> bytes:
        raise ValueError("not a CoverGenError at all")

    monkeypatch.setattr(ncg, "generate_cover", boom)
    upload_calls: list[Any] = []

    result = ncg.generate_and_upload_cover(
        ROW_ID,
        IP_PAGE_ID,
        _children_fn(tree),
        fetch_bytes=lambda url: b"ref-bytes",
        upload_fn=lambda toggle_id, png: upload_calls.append((toggle_id, png)),
    )

    assert result is not None
    assert result.startswith("cover_gen_failed:")
    assert "not a CoverGenError at all" in result
    assert upload_calls == []


def test_generate_and_upload_cover_upload_error_never_propagates(spy_generate: list[Any]):
    tree = {ROW_ID: _well_formed_cover_section("a great prompt"), TOGGLE_ID: [], IP_PAGE_ID: [_image_block("https://s3.example/ref.png")]}

    def boom_upload(toggle_id: str, png: bytes) -> None:
        raise RuntimeError("notion patch failed")

    result = ncg.generate_and_upload_cover(
        ROW_ID,
        IP_PAGE_ID,
        _children_fn(tree),
        fetch_bytes=lambda url: b"ref-bytes",
        upload_fn=boom_upload,
    )

    assert result is not None
    assert "notion patch failed" in result


@pytest.mark.parametrize(
    "break_point",
    ["children_fn", "fetch_bytes", "upload_fn"],
)
def test_generate_and_upload_cover_never_raises_regardless_of_which_dependency_throws(
    monkeypatch: pytest.MonkeyPatch, break_point: str
) -> None:
    """This function's whole contract is 'never raises' — a caller looping
    over many rows must be able to treat one row's total failure as fully
    independent/catchable, never a crash. Explicitly throw from every
    injected dependency in turn and assert the function still returns a
    string (or None), never propagating an exception."""
    tree = {
        ROW_ID: _well_formed_cover_section("a great prompt"),
        TOGGLE_ID: [],
        IP_PAGE_ID: [_image_block("https://s3.example/ref.png")],
    }
    monkeypatch.setattr(ncg, "generate_cover", lambda *_a, **_k: FAKE_PNG)

    def broken_children_fn(block_id: str) -> list[dict]:
        raise RuntimeError("notion exploded")

    def broken_fetch(url: str) -> bytes:
        raise RuntimeError("download exploded")

    def broken_upload(toggle_id: str, png: bytes) -> None:
        raise RuntimeError("upload exploded")

    children_fn = broken_children_fn if break_point == "children_fn" else _children_fn(tree)
    fetch_bytes = broken_fetch if break_point == "fetch_bytes" else (lambda url: b"ref-bytes")
    upload_fn = broken_upload if break_point == "upload_fn" else (lambda toggle_id, png: None)

    result = ncg.generate_and_upload_cover(
        ROW_ID, IP_PAGE_ID, children_fn, fetch_bytes=fetch_bytes, upload_fn=upload_fn
    )
    assert result is None or isinstance(result, str)
