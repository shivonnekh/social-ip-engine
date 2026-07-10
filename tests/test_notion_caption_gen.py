"""Tests for src/notion_caption_gen.py — single-row caption-burn orchestrator.

Notion/download/transcription/render/upload are all faked via dependency
injection (``upload_fn``) or monkeypatching the module's own collaborator
functions (``transcribe_words``, ``render``, ``urllib.request.urlopen``) —
no real network or video I/O anywhere in this file, mirroring
tests/test_notion_cover_gen.py's style exactly.
"""

from __future__ import annotations

import io
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any

import pytest

from src import notion_caption_gen as ncap

ROW_ID = "row-1"
VIDEO_URL = "https://s3.example/raw.mp4"

# Captured BEFORE the autouse `_fake_download` fixture (below) monkeypatches
# ncap._download_video for the burn_captions_for_row tests — the
# `_download_video`-specific unit tests further down need the REAL
# implementation, not the fake, so they call this reference directly
# instead of `ncap._download_video`.
_real_download_video = ncap._download_video


# ------------------------------------------------------------- find_raw_video_url


def _page_with_raw_video(url: str | None, kind: str = "file") -> dict:
    files = [] if url is None else [{"type": kind, kind: {"url": url}}]
    return {"properties": {"Raw Video": {"files": files}}}


def test_find_raw_video_url_returns_file_url():
    page = _page_with_raw_video("https://s3.example/raw.mp4", kind="file")
    assert ncap.find_raw_video_url(ROW_ID, page=page) == "https://s3.example/raw.mp4"


def test_find_raw_video_url_returns_external_url():
    page = _page_with_raw_video("https://cdn.example/raw.mp4", kind="external")
    assert ncap.find_raw_video_url(ROW_ID, page=page) == "https://cdn.example/raw.mp4"


def test_find_raw_video_url_none_when_no_files():
    page = _page_with_raw_video(None)
    assert ncap.find_raw_video_url(ROW_ID, page=page) is None


def test_find_raw_video_url_none_when_property_missing_entirely():
    assert ncap.find_raw_video_url(ROW_ID, page={"properties": {}}) is None


def test_find_raw_video_url_ignores_unused_children_fn_param():
    page = _page_with_raw_video("https://s3.example/raw.mp4")

    def boom(_block_id: str) -> list[dict]:
        raise AssertionError("children_fn_unused must never be called")

    assert ncap.find_raw_video_url(ROW_ID, boom, page=page) == "https://s3.example/raw.mp4"


# --------------------------------------------------------- upload_production_video


def test_upload_production_video_raises_for_missing_notion_key(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
):
    monkeypatch.delenv("NOTION_KEY", raising=False)
    video_path = tmp_path / "captioned.mp4"
    video_path.write_bytes(b"fake-mp4-bytes")
    with pytest.raises(ncap.CaptionGenError, match="NOTION_KEY"):
        ncap.upload_production_video(ROW_ID, video_path, api_key="")


def test_upload_production_video_happy_path(monkeypatch: pytest.MonkeyPatch, tmp_path: Path):
    video_path = tmp_path / "captioned.mp4"
    video_path.write_bytes(b"fake-mp4-bytes")
    calls: list[str] = []

    def fake(req: Any, timeout: float = 0) -> io.BytesIO:
        url = req.full_url if isinstance(req, urllib.request.Request) else req
        calls.append(url)
        if url == f"{ncap._NOTION_API}/file_uploads":
            import json

            return io.BytesIO(
                json.dumps({"id": "upload-1", "upload_url": "https://notion-upload.example/put"}).encode()
            )
        if url == "https://notion-upload.example/put":
            return io.BytesIO(b"")
        if url == f"{ncap._NOTION_API}/pages/{ROW_ID}":
            return io.BytesIO(b"{}")
        raise AssertionError(f"unexpected URL: {url}")

    monkeypatch.setattr(urllib.request, "urlopen", fake)
    ncap.upload_production_video(ROW_ID, video_path, api_key="ntn-test")
    assert calls == [
        f"{ncap._NOTION_API}/file_uploads",
        "https://notion-upload.example/put",
        f"{ncap._NOTION_API}/pages/{ROW_ID}",
    ]


def test_upload_production_video_raises_when_put_fails(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
):
    video_path = tmp_path / "captioned.mp4"
    video_path.write_bytes(b"fake-mp4-bytes")

    def fake(req: Any, timeout: float = 0) -> io.BytesIO:
        url = req.full_url if isinstance(req, urllib.request.Request) else req
        if url == f"{ncap._NOTION_API}/file_uploads":
            import json

            return io.BytesIO(
                json.dumps({"id": "upload-1", "upload_url": "https://notion-upload.example/put"}).encode()
            )
        raise urllib.error.URLError("connection refused")

    monkeypatch.setattr(urllib.request, "urlopen", fake)
    with pytest.raises(ncap.CaptionGenError, match="upload PUT failed"):
        ncap.upload_production_video(ROW_ID, video_path, api_key="ntn-test")


def test_upload_production_video_raises_for_malformed_file_uploads_response(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
):
    video_path = tmp_path / "captioned.mp4"
    video_path.write_bytes(b"fake-mp4-bytes")

    def fake(req: Any, timeout: float = 0) -> io.BytesIO:
        return io.BytesIO(b'{"unexpected": "shape"}')

    monkeypatch.setattr(urllib.request, "urlopen", fake)
    with pytest.raises(ncap.CaptionGenError, match="unexpected file_uploads response"):
        ncap.upload_production_video(ROW_ID, video_path, api_key="ntn-test")


# ------------------------------------------------------------------- _download_video


def test_download_video_writes_response_body_to_dest(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
):
    def fake(req: Any, timeout: float = 0) -> io.BytesIO:
        return io.BytesIO(b"real-video-bytes")

    monkeypatch.setattr(urllib.request, "urlopen", fake)
    dest = tmp_path / "raw.mp4"
    _real_download_video("https://s3.example/raw.mp4", dest)
    assert dest.read_bytes() == b"real-video-bytes"


def test_download_video_raises_for_network_failure(monkeypatch: pytest.MonkeyPatch, tmp_path: Path):
    def boom(req: Any, timeout: float = 0) -> None:
        raise urllib.error.URLError("connection refused")

    monkeypatch.setattr(urllib.request, "urlopen", boom)
    with pytest.raises(ncap.CaptionGenError, match="download failed"):
        _real_download_video("https://s3.example/raw.mp4", tmp_path / "raw.mp4")


def test_download_video_raises_for_empty_body(monkeypatch: pytest.MonkeyPatch, tmp_path: Path):
    def fake(req: Any, timeout: float = 0) -> io.BytesIO:
        return io.BytesIO(b"")

    monkeypatch.setattr(urllib.request, "urlopen", fake)
    with pytest.raises(ncap.CaptionGenError, match="empty body"):
        _real_download_video("https://s3.example/raw.mp4", tmp_path / "raw.mp4")


class _FakeResponseWithHeaders(io.BytesIO):
    """BytesIO + a minimal .headers object exposing .get() — real urllib
    responses always carry .headers; this file's plain io.BytesIO fakes
    don't need to, EXCEPT for the two Content-Length tests below."""

    def __init__(self, data: bytes, content_length: str | None) -> None:
        super().__init__(data)
        self.headers = {"Content-Length": content_length} if content_length is not None else {}


def test_download_video_raises_when_content_length_declares_oversized_body(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
):
    """HIGH regression (security review, 2026-07-08): a declared
    Content-Length over the cap must be refused BEFORE any streaming read,
    not just after fully buffering an oversized body."""
    oversized = str(ncap._MAX_VIDEO_BYTES + 1)

    def fake(req: Any, timeout: float = 0) -> _FakeResponseWithHeaders:
        return _FakeResponseWithHeaders(b"irrelevant", content_length=oversized)

    monkeypatch.setattr(urllib.request, "urlopen", fake)
    with pytest.raises(ncap.CaptionGenError, match="exceeds cap"):
        _real_download_video("https://s3.example/raw.mp4", tmp_path / "raw.mp4")


def test_download_video_tolerates_malformed_content_length_header(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
):
    """A non-numeric Content-Length must not crash the download — falls
    through to the streamed byte-count cap instead (which still applies)."""

    def fake(req: Any, timeout: float = 0) -> _FakeResponseWithHeaders:
        return _FakeResponseWithHeaders(b"small body", content_length="not-a-number")

    monkeypatch.setattr(urllib.request, "urlopen", fake)
    dest = tmp_path / "raw.mp4"
    _real_download_video("https://s3.example/raw.mp4", dest)
    assert dest.read_bytes() == b"small body"


def test_download_video_raises_when_streamed_bytes_exceed_cap_despite_missing_header(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
):
    """HIGH regression (security review, 2026-07-08): a missing OR lying
    Content-Length must never bypass the cap — the streamed byte count
    itself is the real enforcement, the header check is only a fast-path."""
    monkeypatch.setattr(ncap, "_MAX_VIDEO_BYTES", 10)  # tiny cap for a fast test
    monkeypatch.setattr(ncap, "_DOWNLOAD_CHUNK_BYTES", 4)

    def fake(req: Any, timeout: float = 0) -> _FakeResponseWithHeaders:
        return _FakeResponseWithHeaders(b"way more than ten bytes", content_length=None)

    monkeypatch.setattr(urllib.request, "urlopen", fake)
    with pytest.raises(ncap.CaptionGenError, match="exceeded cap"):
        _real_download_video("https://s3.example/raw.mp4", tmp_path / "raw.mp4")


# --------------------------------------------------------------------- _notion_call


def test_notion_call_raises_for_transport_failure(monkeypatch: pytest.MonkeyPatch):
    def boom(req: Any, timeout: float = 0) -> None:
        raise urllib.error.URLError("connection refused")

    monkeypatch.setattr(urllib.request, "urlopen", boom)
    with pytest.raises(ncap.CaptionGenError, match="notion API GET /pages/row-1 failed"):
        ncap._notion_call("GET", "/pages/row-1", "ntn-test")


def test_notion_call_raises_for_invalid_json_body(monkeypatch: pytest.MonkeyPatch):
    def fake(req: Any, timeout: float = 0) -> io.BytesIO:
        return io.BytesIO(b"<html>not json at all</html>")

    monkeypatch.setattr(urllib.request, "urlopen", fake)
    with pytest.raises(ncap.CaptionGenError, match="invalid JSON"):
        ncap._notion_call("GET", "/pages/row-1", "ntn-test")


# ----------------------------------------------------------- burn_captions_for_row


@pytest.fixture(autouse=True)
def _fake_download(monkeypatch: pytest.MonkeyPatch):
    """Every test in this file goes through _download_video — faked once
    here so individual tests only need to care about the parts they're
    actually testing (transcription / render / upload)."""

    def fake_download(url: str, dest: Path) -> None:
        dest.write_bytes(b"fake-video-bytes")

    monkeypatch.setattr(ncap, "_download_video", fake_download)


@pytest.fixture()
def spy_transcribe(monkeypatch: pytest.MonkeyPatch) -> list[Any]:
    calls: list[Any] = []

    async def fake(*args: Any, **kwargs: Any) -> list[dict]:
        calls.append((args, kwargs))
        return [
            {"word": "Hello", "start": 0.0, "end": 0.3},
            {"word": "world", "start": 0.3, "end": 0.6},
        ]

    monkeypatch.setattr(ncap, "transcribe_words", fake)
    return calls


@pytest.fixture()
def spy_render(monkeypatch: pytest.MonkeyPatch) -> list[Any]:
    calls: list[Any] = []

    def fake(video_path: Path, chunks: list, out_path: Path) -> None:
        calls.append((video_path, chunks, out_path))
        out_path.write_bytes(b"fake-captioned-mp4")

    monkeypatch.setattr(ncap, "render", fake)
    return calls


@pytest.mark.asyncio
async def test_happy_path_returns_none_and_calls_things_in_order(
    spy_transcribe: list[Any], spy_render: list[Any]
):
    upload_calls: list[Any] = []

    def fake_upload(row_id: str, video_path: Path) -> None:
        # Assert the render step already ran and produced a real file
        # before upload is ever invoked.
        assert video_path.exists()
        assert video_path.read_bytes() == b"fake-captioned-mp4"
        upload_calls.append((row_id, video_path))

    result = await ncap.burn_captions_for_row(ROW_ID, VIDEO_URL, upload_fn=fake_upload)

    assert result is None
    assert len(spy_transcribe) == 1
    assert len(spy_render) == 1
    assert len(upload_calls) == 1
    assert upload_calls[0][0] == ROW_ID


@pytest.mark.asyncio
async def test_ssrf_unsafe_url_refused_before_any_download(monkeypatch: pytest.MonkeyPatch):
    download_calls: list[str] = []

    def spy_download(url: str, dest: Path) -> None:
        download_calls.append(url)

    monkeypatch.setattr(ncap, "_download_video", spy_download)

    result = await ncap.burn_captions_for_row(
        ROW_ID, "file:///etc/passwd", upload_fn=lambda *_a: None
    )

    assert result is not None
    assert "no_captions" in result
    assert download_calls == []  # never even attempted


@pytest.mark.asyncio
async def test_empty_transcription_short_circuits_before_render(monkeypatch: pytest.MonkeyPatch):
    async def empty_transcribe(*args: Any, **kwargs: Any) -> list[dict]:
        return []

    monkeypatch.setattr(ncap, "transcribe_words", empty_transcribe)

    render_calls: list[Any] = []

    def spy_render(video_path: Path, chunks: list, out_path: Path) -> None:
        render_calls.append(video_path)

    monkeypatch.setattr(ncap, "render", spy_render)

    result = await ncap.burn_captions_for_row(ROW_ID, VIDEO_URL, upload_fn=lambda *_a: None)

    assert result is not None
    assert "no_captions" in result
    assert render_calls == []


@pytest.mark.asyncio
async def test_render_raising_is_caught(spy_transcribe: list[Any], monkeypatch: pytest.MonkeyPatch):
    def boom_render(video_path: Path, chunks: list, out_path: Path) -> None:
        raise RuntimeError("moviepy exploded")

    monkeypatch.setattr(ncap, "render", boom_render)
    upload_calls: list[Any] = []

    result = await ncap.burn_captions_for_row(
        ROW_ID, VIDEO_URL, upload_fn=lambda *a: upload_calls.append(a)
    )

    assert result is not None
    assert "caption_render_failed" in result
    assert "moviepy exploded" in result
    assert upload_calls == []


@pytest.mark.asyncio
async def test_render_timeout_is_caught_and_reported(
    spy_transcribe: list[Any], monkeypatch: pytest.MonkeyPatch
):
    """HIGH regression (security review, 2026-07-08): a stuck/pathological
    render must not hang burn_captions_for_row forever — a detached
    asyncio.create_task with nothing awaiting it would otherwise be
    invisible forever instead of surfacing a clean, actionable warning."""
    import time

    monkeypatch.setattr(ncap, "_RENDER_TIMEOUT_S", 0.05)

    def slow_render(video_path: Path, chunks: list, out_path: Path) -> None:
        time.sleep(5)  # far longer than the patched 0.05s timeout above

    monkeypatch.setattr(ncap, "render", slow_render)
    upload_calls: list[Any] = []

    result = await ncap.burn_captions_for_row(
        ROW_ID, VIDEO_URL, upload_fn=lambda *a: upload_calls.append(a)
    )

    assert result is not None
    assert "caption_render_timeout" in result
    assert upload_calls == []


@pytest.mark.asyncio
async def test_render_runs_on_dedicated_executor_not_default_pool(
    spy_transcribe: list[Any], monkeypatch: pytest.MonkeyPatch
):
    """HIGH regression (security review, 2026-07-08): render() must be
    submitted to the module's own _RENDER_EXECUTOR, not asyncio.to_thread's
    shared default pool — otherwise a stuck render could starve unrelated
    background work (e.g. notion_publish_runner.py's git-push to_thread
    calls) sharing that same default pool. Spies on _RENDER_EXECUTOR.submit
    directly (delegating to the real executor) rather than touching any
    asyncio internals, so this test can't destabilize the event loop for
    anything else running under pytest-asyncio."""
    real_executor = ncap._RENDER_EXECUTOR
    submit_calls: list[Any] = []

    class _SpyExecutor:
        def submit(self, fn: Any, *args: Any, **kwargs: Any) -> Any:
            submit_calls.append(fn)
            return real_executor.submit(fn, *args, **kwargs)

    monkeypatch.setattr(ncap, "_RENDER_EXECUTOR", _SpyExecutor())

    def fake_render(video_path: Path, chunks: list, out_path: Path) -> None:
        out_path.write_bytes(b"fake-captioned-mp4")

    monkeypatch.setattr(ncap, "render", fake_render)
    result = await ncap.burn_captions_for_row(ROW_ID, VIDEO_URL, upload_fn=lambda *a: None)

    assert result is None
    assert submit_calls == [fake_render]


@pytest.mark.asyncio
async def test_upload_raising_is_caught(spy_transcribe: list[Any], spy_render: list[Any]):
    def boom_upload(row_id: str, video_path: Path) -> None:
        raise RuntimeError("notion patch failed")

    result = await ncap.burn_captions_for_row(ROW_ID, VIDEO_URL, upload_fn=boom_upload)

    assert result is not None
    assert "caption_upload_failed" in result
    assert "notion patch failed" in result


@pytest.mark.asyncio
async def test_video_read_bytes_failure_after_download_is_caught(monkeypatch: pytest.MonkeyPatch):
    """Defensive branch: _download_video reported success but the file
    can't be read back (e.g. deleted out from under us, permissions). Must
    surface as a warning, not an uncaught OSError."""

    def fake_download(url: str, dest: Path) -> None:
        pass  # deliberately never creates the file

    monkeypatch.setattr(ncap, "_download_video", fake_download)

    result = await ncap.burn_captions_for_row(ROW_ID, VIDEO_URL, upload_fn=lambda *_a: None)

    assert result is not None
    assert "caption_failed" in result
    assert "could not read downloaded video" in result


@pytest.mark.asyncio
async def test_download_failure_is_caught(monkeypatch: pytest.MonkeyPatch):
    def boom_download(url: str, dest: Path) -> None:
        raise ncap.CaptionGenError("network exploded")

    monkeypatch.setattr(ncap, "_download_video", boom_download)

    result = await ncap.burn_captions_for_row(ROW_ID, VIDEO_URL, upload_fn=lambda *_a: None)

    assert result is not None
    assert "caption_download_failed" in result


@pytest.mark.asyncio
async def test_temp_files_cleaned_up_on_success(
    spy_transcribe: list[Any], spy_render: list[Any], monkeypatch: pytest.MonkeyPatch
):
    captured_tmp_dirs: list[str] = []
    real_mkdtemp = ncap.tempfile.mkdtemp

    def spy_mkdtemp(*args: Any, **kwargs: Any) -> str:
        path = real_mkdtemp(*args, **kwargs)
        captured_tmp_dirs.append(path)
        return path

    monkeypatch.setattr(ncap.tempfile, "mkdtemp", spy_mkdtemp)

    result = await ncap.burn_captions_for_row(ROW_ID, VIDEO_URL, upload_fn=lambda *_a: None)

    assert result is None
    assert len(captured_tmp_dirs) == 1
    assert not Path(captured_tmp_dirs[0]).exists()


@pytest.mark.asyncio
async def test_temp_files_cleaned_up_on_render_failure(
    spy_transcribe: list[Any], monkeypatch: pytest.MonkeyPatch
):
    def boom_render(video_path: Path, chunks: list, out_path: Path) -> None:
        raise RuntimeError("moviepy exploded")

    monkeypatch.setattr(ncap, "render", boom_render)

    captured_tmp_dirs: list[str] = []
    real_mkdtemp = ncap.tempfile.mkdtemp

    def spy_mkdtemp(*args: Any, **kwargs: Any) -> str:
        path = real_mkdtemp(*args, **kwargs)
        captured_tmp_dirs.append(path)
        return path

    monkeypatch.setattr(ncap.tempfile, "mkdtemp", spy_mkdtemp)

    result = await ncap.burn_captions_for_row(ROW_ID, VIDEO_URL, upload_fn=lambda *_a: None)

    assert result is not None
    assert len(captured_tmp_dirs) == 1
    assert not Path(captured_tmp_dirs[0]).exists()


@pytest.mark.asyncio
async def test_temp_files_cleaned_up_on_upload_failure(
    spy_transcribe: list[Any], spy_render: list[Any], monkeypatch: pytest.MonkeyPatch
):
    def boom_upload(row_id: str, video_path: Path) -> None:
        raise RuntimeError("notion patch failed")

    captured_tmp_dirs: list[str] = []
    real_mkdtemp = ncap.tempfile.mkdtemp

    def spy_mkdtemp(*args: Any, **kwargs: Any) -> str:
        path = real_mkdtemp(*args, **kwargs)
        captured_tmp_dirs.append(path)
        return path

    monkeypatch.setattr(ncap.tempfile, "mkdtemp", spy_mkdtemp)

    result = await ncap.burn_captions_for_row(ROW_ID, VIDEO_URL, upload_fn=boom_upload)

    assert result is not None
    assert len(captured_tmp_dirs) == 1
    assert not Path(captured_tmp_dirs[0]).exists()


@pytest.mark.parametrize(
    "break_point", ["download", "transcribe", "render", "upload"],
)
@pytest.mark.asyncio
async def test_never_raises_regardless_of_which_dependency_throws(
    monkeypatch: pytest.MonkeyPatch, break_point: str
) -> None:
    """This function's whole contract is 'never raises' — a caller (the
    detached asyncio.create_task in web.py) must never see an uncaught
    exception. Explicitly throw from every injected/monkeypatched
    dependency in turn and assert the function still returns a string,
    never propagating."""

    if break_point == "download":
        monkeypatch.setattr(
            ncap, "_download_video", lambda *_a: (_ for _ in ()).throw(RuntimeError("boom"))
        )
    else:
        monkeypatch.setattr(ncap, "_download_video", lambda url, dest: dest.write_bytes(b"x"))

    async def fake_transcribe(*a: Any, **k: Any) -> list[dict]:
        if break_point == "transcribe":
            raise RuntimeError("boom")
        return [{"word": "Hi", "start": 0.0, "end": 0.2}]

    monkeypatch.setattr(ncap, "transcribe_words", fake_transcribe)

    def fake_render(video_path: Path, chunks: list, out_path: Path) -> None:
        if break_point == "render":
            raise RuntimeError("boom")
        out_path.write_bytes(b"x")

    monkeypatch.setattr(ncap, "render", fake_render)

    def fake_upload(row_id: str, video_path: Path) -> None:
        if break_point == "upload":
            raise RuntimeError("boom")

    result = await ncap.burn_captions_for_row(ROW_ID, VIDEO_URL, upload_fn=fake_upload)

    assert result is None or isinstance(result, str)
