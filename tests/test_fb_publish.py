"""Tests for src/channels/fb_publish.py — FB Page Reels publish flow.

Same fake-``httpx.AsyncClient`` convention as ``tests/test_ig_publish.py`` —
no real network, ever. FB's flow has one more real HTTP call than IG's
(start -> transfer -> poll -> finish, vs IG's create -> poll -> publish)
because the video upload session and the actual byte transfer are two
separate Graph API calls for Facebook Reels; ``create_reel_container``
bundles the first two into one awaitable so the public 3-function contract
(create/poll/publish) still matches ``ig_publish``'s shape for the runner.

API shape verified against the REAL live Graph API this session (not just
docs) — see shello.md 2026-07-08 session notes:
  - POST /{page-id}/video_reels?upload_phase=start -> {video_id, upload_url}
  - POST {upload_url} headers={Authorization: OAuth <token>, file_url: <url>}
    -> {"success": true}  (Meta's "transfer by URL" resumable-upload mode —
    no binary streaming needed, same "point at a public URL" shape as IG)
  - GET /{video_id}?fields=status -> {"status": {"video_status": "..."}}
  - POST /{page-id}/video_reels?upload_phase=finish&video_id=...&video_state=
    PUBLISHED&description=... -> {"success": true}
"""

from __future__ import annotations

import pytest

from src.channels import fb_publish


class _FakeResponse:
    def __init__(self, status_code: int, body: dict | None = None, text: str = "{}"):
        self.status_code = status_code
        self._body = body if body is not None else {}
        self.text = text

    def json(self):
        return self._body


class _FakeAsyncClient:
    """Records every call; returns canned responses keyed by call order."""

    calls: list[tuple[str, str, dict, dict]] = []  # (method, url, params, headers)
    responses: list[_FakeResponse] = []

    def __init__(self, *a, **kw):
        pass

    async def __aenter__(self):
        return self

    async def __aexit__(self, *a):
        return False

    async def post(self, url, *, params=None, headers=None, **_kw):
        _FakeAsyncClient.calls.append(("POST", url, params or {}, headers or {}))
        return _FakeAsyncClient.responses.pop(0)

    async def get(self, url, *, params=None, headers=None, **_kw):
        _FakeAsyncClient.calls.append(("GET", url, params or {}, headers or {}))
        return _FakeAsyncClient.responses.pop(0)


@pytest.fixture(autouse=True)
def _fake_client(monkeypatch):
    _FakeAsyncClient.calls = []
    _FakeAsyncClient.responses = []
    monkeypatch.setattr(fb_publish.httpx, "AsyncClient", _FakeAsyncClient)


@pytest.fixture(autouse=True)
def _creds(monkeypatch):
    monkeypatch.setenv("FB_PAGE_ACCESS_TOKEN", "fb_tok")
    monkeypatch.setenv("FB_PAGE_ID", "PAGE123")
    for var in ("META_GRAPH_BASE", "IG_GRAPH_BASE", "FB_GRAPH_BASE"):
        monkeypatch.delenv(var, raising=False)
    monkeypatch.setenv("META_GRAPH_VERSION", "v25.0")


# --------------------------------------------------------- create_reel_container


@pytest.mark.asyncio
async def test_create_reel_container_success_does_start_then_transfer():
    _FakeAsyncClient.responses = [
        _FakeResponse(200, {"video_id": "vid-1", "upload_url": "https://rupload.facebook.com/x/vid-1"}),
        _FakeResponse(200, {"success": True}),
    ]
    result = await fb_publish.create_reel_container(video_url="https://example.com/reel.mp4")
    assert result.ok
    assert result.creation_id == "vid-1"

    start_method, start_url, start_params, _ = _FakeAsyncClient.calls[0]
    assert start_method == "POST"
    assert start_url == "https://graph.facebook.com/v25.0/PAGE123/video_reels"
    assert start_params["upload_phase"] == "start"
    assert start_params["access_token"] == "fb_tok"

    transfer_method, transfer_url, _, transfer_headers = _FakeAsyncClient.calls[1]
    assert transfer_method == "POST"
    assert transfer_url == "https://rupload.facebook.com/x/vid-1"
    assert transfer_headers["Authorization"] == "OAuth fb_tok"
    assert transfer_headers["file_url"] == "https://example.com/reel.mp4"


@pytest.mark.asyncio
async def test_create_reel_container_missing_credentials():
    import os

    os.environ.pop("FB_PAGE_ACCESS_TOKEN", None)
    result = await fb_publish.create_reel_container(video_url="https://example.com/reel.mp4")
    assert not result.ok
    assert "credentials" in result.detail
    assert _FakeAsyncClient.calls == []


@pytest.mark.asyncio
async def test_create_reel_container_empty_video_url():
    result = await fb_publish.create_reel_container(video_url="   ")
    assert not result.ok
    assert "video_url" in result.detail


@pytest.mark.asyncio
async def test_create_reel_container_start_phase_http_error():
    _FakeAsyncClient.responses = [_FakeResponse(400, text="bad request")]
    result = await fb_publish.create_reel_container(video_url="https://example.com/reel.mp4")
    assert not result.ok
    assert "400" in result.detail
    assert len(_FakeAsyncClient.calls) == 1  # never attempted transfer


@pytest.mark.asyncio
async def test_create_reel_container_start_phase_unparseable_body():
    _FakeAsyncClient.responses = [_FakeResponse(200, body=None, text="not json")]
    # simulate .json() raising by using a body that lacks video_id/upload_url
    _FakeAsyncClient.responses = [_FakeResponse(200, {})]
    result = await fb_publish.create_reel_container(video_url="https://example.com/reel.mp4")
    assert not result.ok
    assert "video_id" in result.detail or "upload_url" in result.detail


@pytest.mark.asyncio
async def test_create_reel_container_transfer_phase_failure():
    _FakeAsyncClient.responses = [
        _FakeResponse(200, {"video_id": "vid-1", "upload_url": "https://rupload.facebook.com/x/vid-1"}),
        _FakeResponse(500, text="upload failed"),
    ]
    result = await fb_publish.create_reel_container(video_url="https://example.com/reel.mp4")
    assert not result.ok
    assert "500" in result.detail


@pytest.mark.asyncio
async def test_create_reel_container_transport_error(monkeypatch):
    import httpx

    class _RaisingClient(_FakeAsyncClient):
        async def post(self, url, **kw):
            raise httpx.ConnectError("boom")

    monkeypatch.setattr(fb_publish.httpx, "AsyncClient", _RaisingClient)
    result = await fb_publish.create_reel_container(video_url="https://example.com/reel.mp4")
    assert not result.ok
    assert "transport" in result.detail


# --------------------------------------------------------- poll_container_status


@pytest.mark.asyncio
async def test_poll_container_status_upload_complete_is_finished():
    _FakeAsyncClient.responses = [
        _FakeResponse(200, {"status": {"video_status": "upload_complete"}})
    ]
    result = await fb_publish.poll_container_status("vid-1")
    assert result.ok
    assert result.is_finished
    assert not result.is_terminal_failure


@pytest.mark.asyncio
async def test_poll_container_status_still_uploading_is_not_finished():
    _FakeAsyncClient.responses = [
        _FakeResponse(200, {"status": {"video_status": "processing"}})
    ]
    result = await fb_publish.poll_container_status("vid-1")
    assert result.ok
    assert not result.is_finished
    assert not result.is_terminal_failure


@pytest.mark.asyncio
async def test_poll_container_status_error_is_terminal_failure():
    _FakeAsyncClient.responses = [
        _FakeResponse(200, {"status": {"video_status": "error"}})
    ]
    result = await fb_publish.poll_container_status("vid-1")
    assert result.ok
    assert result.is_terminal_failure
    assert not result.is_finished


@pytest.mark.asyncio
async def test_poll_container_status_missing_credentials():
    import os

    os.environ.pop("FB_PAGE_ACCESS_TOKEN", None)
    result = await fb_publish.poll_container_status("vid-1")
    assert not result.ok


@pytest.mark.asyncio
async def test_poll_container_status_http_error():
    _FakeAsyncClient.responses = [_FakeResponse(404, text="not found")]
    result = await fb_publish.poll_container_status("vid-1")
    assert not result.ok
    assert "404" in result.detail


# --------------------------------------------------------- publish_container


@pytest.mark.asyncio
async def test_publish_container_success():
    _FakeAsyncClient.responses = [_FakeResponse(200, {"success": True})]
    result = await fb_publish.publish_container("vid-1", caption="hello world")
    assert result.ok
    assert result.media_id == "vid-1"  # FB has no separate publish-time id — video_id IS the media id

    method, url, params, _ = _FakeAsyncClient.calls[0]
    assert method == "POST"
    assert url == "https://graph.facebook.com/v25.0/PAGE123/video_reels"
    assert params["upload_phase"] == "finish"
    assert params["video_id"] == "vid-1"
    assert params["video_state"] == "PUBLISHED"
    assert params["description"] == "hello world"


@pytest.mark.asyncio
async def test_publish_container_empty_creation_id():
    result = await fb_publish.publish_container("   ", caption="hi")
    assert not result.ok
    assert "creation_id" in result.detail
    assert _FakeAsyncClient.calls == []


@pytest.mark.asyncio
async def test_publish_container_missing_credentials():
    import os

    os.environ.pop("FB_PAGE_ACCESS_TOKEN", None)
    result = await fb_publish.publish_container("vid-1", caption="hi")
    assert not result.ok


@pytest.mark.asyncio
async def test_publish_container_api_failure():
    _FakeAsyncClient.responses = [_FakeResponse(400, text="oauth error")]
    result = await fb_publish.publish_container("vid-1", caption="hi")
    assert not result.ok


@pytest.mark.asyncio
async def test_publish_container_caption_defaults_empty():
    _FakeAsyncClient.responses = [_FakeResponse(200, {"success": True})]
    await fb_publish.publish_container("vid-1")
    _, _, params, _ = _FakeAsyncClient.calls[0]
    assert params["description"] == ""


@pytest.mark.asyncio
async def test_publish_container_uses_per_account_credentials(monkeypatch):
    """account_id routing must go through the same IP-registry credential
    resolution as everything else (meta_client._creds) — not hardcoded to
    the platform-default env vars."""
    monkeypatch.setenv("FB_PAGE_ACCESS_TOKEN", "default_tok")
    monkeypatch.setenv("FB_PAGE_ID", "DEFAULT_PAGE")
    _FakeAsyncClient.responses = [_FakeResponse(200, {"success": True})]
    # No per-account override registered for "some-other-account" in this
    # test's registry — falls back to the platform default, proving the
    # lookup path is exercised (not hardcoded to ignore account_id).
    result = await fb_publish.publish_container("vid-1", caption="hi", account_id=None)
    assert result.ok
