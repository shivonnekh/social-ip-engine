"""Tests for src/channels/ig_publish.py — IG Reels two-step publish flow.

Same fake-``httpx.AsyncClient`` convention as ``tests/test_channels_facebook.py``
(``_FakeAsyncClient`` monkeypatched onto the module's ``httpx.AsyncClient``) —
no real network, ever.
"""

from __future__ import annotations

import pytest

from src.channels import ig_publish
from src.channels import meta_client


class _FakeResponse:
    def __init__(self, status_code: int, body: dict | None = None, text: str = "{}"):
        self.status_code = status_code
        self._body = body if body is not None else {}
        self.text = text

    def json(self):
        return self._body


class _FakeAsyncClient:
    """Records every call; returns canned responses keyed by call order."""

    calls: list[tuple[str, str, dict]] = []  # (method, url, params)
    responses: list[_FakeResponse] = []

    def __init__(self, *a, **kw):
        pass

    async def __aenter__(self):
        return self

    async def __aexit__(self, *a):
        return False

    async def post(self, url, *, params=None, **_kw):
        _FakeAsyncClient.calls.append(("POST", url, params or {}))
        return _FakeAsyncClient.responses.pop(0)

    async def get(self, url, *, params=None, **_kw):
        _FakeAsyncClient.calls.append(("GET", url, params or {}))
        return _FakeAsyncClient.responses.pop(0)


@pytest.fixture(autouse=True)
def _fake_client(monkeypatch):
    _FakeAsyncClient.calls = []
    _FakeAsyncClient.responses = []
    monkeypatch.setattr(ig_publish.httpx, "AsyncClient", _FakeAsyncClient)


@pytest.fixture(autouse=True)
def _creds(monkeypatch):
    monkeypatch.setenv("IG_PAGE_ACCESS_TOKEN", "ig_tok")
    monkeypatch.setenv("IG_USER_ID", "IGBIZ")
    for var in ("META_GRAPH_BASE", "IG_GRAPH_BASE", "FB_GRAPH_BASE"):
        monkeypatch.delenv(var, raising=False)
    monkeypatch.setenv("META_GRAPH_VERSION", "v25.0")


# --------------------------------------------------------- create_reel_container


@pytest.mark.asyncio
async def test_create_reel_container_success():
    _FakeAsyncClient.responses = [_FakeResponse(200, {"id": "container-1"})]
    result = await ig_publish.create_reel_container(
        video_url="https://example.com/reel.mp4", caption="hi", cover_url="https://example.com/c.jpg"
    )
    assert result.ok
    assert result.creation_id == "container-1"
    method, url, params = _FakeAsyncClient.calls[0]
    assert method == "POST"
    assert url == "https://graph.instagram.com/v25.0/IGBIZ/media"
    assert params["media_type"] == "REELS"
    assert params["video_url"] == "https://example.com/reel.mp4"
    assert params["cover_url"] == "https://example.com/c.jpg"
    assert params["caption"] == "hi"


@pytest.mark.asyncio
async def test_create_reel_container_no_cover_omits_param():
    _FakeAsyncClient.responses = [_FakeResponse(200, {"id": "c1"})]
    await ig_publish.create_reel_container(video_url="https://example.com/r.mp4")
    _, _, params = _FakeAsyncClient.calls[0]
    assert "cover_url" not in params


@pytest.mark.asyncio
async def test_create_reel_container_missing_creds():
    import os

    os.environ.pop("IG_PAGE_ACCESS_TOKEN", None)
    result = await ig_publish.create_reel_container(video_url="https://example.com/r.mp4")
    assert not result.ok
    assert "credentials" in result.detail


@pytest.mark.asyncio
async def test_create_reel_container_empty_video_url():
    result = await ig_publish.create_reel_container(video_url="")
    assert not result.ok
    assert "video_url" in result.detail


@pytest.mark.asyncio
async def test_create_reel_container_http_error():
    _FakeAsyncClient.responses = [_FakeResponse(400, {"error": {"message": "bad"}}, text="bad request")]
    result = await ig_publish.create_reel_container(video_url="https://example.com/r.mp4")
    assert not result.ok
    assert "400" in result.detail


@pytest.mark.asyncio
async def test_create_reel_container_no_id_in_response():
    _FakeAsyncClient.responses = [_FakeResponse(200, {})]
    result = await ig_publish.create_reel_container(video_url="https://example.com/r.mp4")
    assert not result.ok
    assert "no container id" in result.detail


# --------------------------------------------------------- poll_container_status


@pytest.mark.asyncio
async def test_poll_container_status_in_progress():
    _FakeAsyncClient.responses = [_FakeResponse(200, {"status_code": "IN_PROGRESS"})]
    result = await ig_publish.poll_container_status("container-1")
    assert result.ok
    assert result.status_code == ig_publish.STATUS_IN_PROGRESS
    assert not result.is_finished
    assert not result.is_terminal_failure


@pytest.mark.asyncio
async def test_poll_container_status_finished():
    _FakeAsyncClient.responses = [_FakeResponse(200, {"status_code": "FINISHED"})]
    result = await ig_publish.poll_container_status("container-1")
    assert result.is_finished
    assert not result.is_terminal_failure


@pytest.mark.asyncio
async def test_poll_container_status_error_is_terminal_failure():
    _FakeAsyncClient.responses = [_FakeResponse(200, {"status_code": "ERROR"})]
    result = await ig_publish.poll_container_status("container-1")
    assert result.is_terminal_failure
    assert not result.is_finished


@pytest.mark.asyncio
async def test_poll_container_status_expired_is_terminal_failure():
    _FakeAsyncClient.responses = [_FakeResponse(200, {"status_code": "EXPIRED"})]
    result = await ig_publish.poll_container_status("container-1")
    assert result.is_terminal_failure


@pytest.mark.asyncio
async def test_poll_container_status_http_error():
    _FakeAsyncClient.responses = [_FakeResponse(500, {}, text="server error")]
    result = await ig_publish.poll_container_status("container-1")
    assert not result.ok


@pytest.mark.asyncio
async def test_poll_container_status_uses_correct_url():
    _FakeAsyncClient.responses = [_FakeResponse(200, {"status_code": "IN_PROGRESS"})]
    await ig_publish.poll_container_status("container-42")
    _, url, params = _FakeAsyncClient.calls[0]
    assert url == "https://graph.instagram.com/v25.0/container-42"
    assert params["fields"] == "status_code"


# ------------------------------------------------------------- publish_container


@pytest.mark.asyncio
async def test_publish_container_success():
    _FakeAsyncClient.responses = [_FakeResponse(200, {"id": "media-1"})]
    result = await ig_publish.publish_container("container-1")
    assert result.ok
    assert result.media_id == "media-1"
    method, url, params = _FakeAsyncClient.calls[0]
    assert method == "POST"
    assert url == "https://graph.instagram.com/v25.0/IGBIZ/media_publish"
    assert params["creation_id"] == "container-1"


@pytest.mark.asyncio
async def test_publish_container_empty_creation_id():
    result = await ig_publish.publish_container("")
    assert not result.ok
    assert "creation_id" in result.detail


@pytest.mark.asyncio
async def test_publish_container_http_error():
    _FakeAsyncClient.responses = [_FakeResponse(400, {"error": {"message": "expired"}}, text="expired")]
    result = await ig_publish.publish_container("container-1")
    assert not result.ok


@pytest.mark.asyncio
async def test_publish_container_per_account_credentials(monkeypatch):
    monkeypatch.setenv("IG_PAGE_ACCESS_TOKEN_JACKIE", "jackie_tok")
    monkeypatch.setenv("IG_USER_ID_JACKIE", "JACKIEBIZ")
    monkeypatch.setattr(
        meta_client.ip_registry,
        "token_envs_for_account",
        lambda account_id, records=None: ("IG_PAGE_ACCESS_TOKEN_JACKIE", "IG_USER_ID_JACKIE")
        if account_id == "jackie-acct"
        else None,
    )
    _FakeAsyncClient.responses = [_FakeResponse(200, {"id": "media-2"})]
    result = await ig_publish.publish_container("container-2", account_id="jackie-acct")
    assert result.ok
    _, url, _ = _FakeAsyncClient.calls[0]
    assert url == "https://graph.instagram.com/v25.0/JACKIEBIZ/media_publish"
