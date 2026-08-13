"""Tests for src/channels/fb_publish_carousel.py — FB Page carousel
(multi-photo) publish flow.

Same fake-``httpx.AsyncClient`` convention as ``tests/test_ig_publish_carousel.py``
/ ``tests/test_fb_publish.py`` — no real network, ever. Unlike either sibling,
this flow has NO poll step (a Page photo has no Meta-side processing), so
there is nothing here to test for "still in progress."
"""

from __future__ import annotations

import pytest

from src.channels import fb_publish_carousel


class _FakeResponse:
    def __init__(self, status_code: int, body: dict | None = None, text: str = "{}"):
        self.status_code = status_code
        self._body = body if body is not None else {}
        self.text = text

    def json(self):
        return self._body


class _FakeAsyncClient:
    calls: list[tuple[str, str, dict]] = []
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


@pytest.fixture(autouse=True)
def _fake_client(monkeypatch):
    _FakeAsyncClient.calls = []
    _FakeAsyncClient.responses = []
    monkeypatch.setattr(fb_publish_carousel.httpx, "AsyncClient", _FakeAsyncClient)


@pytest.fixture(autouse=True)
def _creds(monkeypatch):
    monkeypatch.setenv("FB_PAGE_ACCESS_TOKEN", "fb_tok")
    monkeypatch.setenv("FB_PAGE_ID", "PAGE123")
    for var in ("META_GRAPH_BASE", "IG_GRAPH_BASE", "FB_GRAPH_BASE"):
        monkeypatch.delenv(var, raising=False)
    monkeypatch.setenv("META_GRAPH_VERSION", "v25.0")


# --------------------------------------------------------- create_unpublished_photo


@pytest.mark.asyncio
async def test_create_unpublished_photo_success():
    _FakeAsyncClient.responses = [_FakeResponse(200, {"id": "photo-1"})]
    result = await fb_publish_carousel.create_unpublished_photo(
        "https://example.com/slide1.png"
    )
    assert result.ok
    assert result.photo_id == "photo-1"
    method, url, params = _FakeAsyncClient.calls[0]
    assert method == "POST"
    assert url == "https://graph.facebook.com/v25.0/PAGE123/photos"
    assert params["url"] == "https://example.com/slide1.png"
    assert params["published"] == "false"


@pytest.mark.asyncio
async def test_create_unpublished_photo_empty_url():
    result = await fb_publish_carousel.create_unpublished_photo("")
    assert not result.ok
    assert "image_url" in result.detail
    assert _FakeAsyncClient.calls == []


@pytest.mark.asyncio
async def test_create_unpublished_photo_missing_creds(monkeypatch):
    monkeypatch.delenv("FB_PAGE_ACCESS_TOKEN", raising=False)
    result = await fb_publish_carousel.create_unpublished_photo("https://example.com/slide1.png")
    assert not result.ok
    assert "credentials" in result.detail


@pytest.mark.asyncio
async def test_create_unpublished_photo_http_error():
    _FakeAsyncClient.responses = [_FakeResponse(400, text="bad")]
    result = await fb_publish_carousel.create_unpublished_photo("https://example.com/slide1.png")
    assert not result.ok
    assert "400" in result.detail


@pytest.mark.asyncio
async def test_create_unpublished_photo_no_id_in_response():
    _FakeAsyncClient.responses = [_FakeResponse(200, {})]
    result = await fb_publish_carousel.create_unpublished_photo("https://example.com/slide1.png")
    assert not result.ok
    assert "no photo id" in result.detail


# --------------------------------------------------------- publish_carousel_post


@pytest.mark.asyncio
async def test_publish_carousel_post_success():
    _FakeAsyncClient.responses = [_FakeResponse(200, {"id": "post-1"})]
    result = await fb_publish_carousel.publish_carousel_post(
        ["photo-1", "photo-2", "photo-3"], caption="hello"
    )
    assert result.ok
    assert result.post_id == "post-1"
    method, url, params = _FakeAsyncClient.calls[0]
    assert method == "POST"
    assert url == "https://graph.facebook.com/v25.0/PAGE123/feed"
    assert params["message"] == "hello"
    import json as _json
    assert _json.loads(params["attached_media"]) == [
        {"media_fbid": "photo-1"}, {"media_fbid": "photo-2"}, {"media_fbid": "photo-3"},
    ]


@pytest.mark.asyncio
async def test_publish_carousel_post_too_few_items():
    result = await fb_publish_carousel.publish_carousel_post(["only-one"])
    assert not result.ok
    assert "at least" in result.detail
    assert _FakeAsyncClient.calls == []


@pytest.mark.asyncio
async def test_publish_carousel_post_too_many_items():
    result = await fb_publish_carousel.publish_carousel_post([f"p{n}" for n in range(11)])
    assert not result.ok
    assert "at most" in result.detail
    assert _FakeAsyncClient.calls == []


@pytest.mark.asyncio
async def test_publish_carousel_post_strips_blank_ids():
    _FakeAsyncClient.responses = [_FakeResponse(200, {"id": "post-2"})]
    result = await fb_publish_carousel.publish_carousel_post(["photo-1", "", "  ", "photo-2"])
    assert result.ok
    import json as _json
    _, _, params = _FakeAsyncClient.calls[0]
    assert _json.loads(params["attached_media"]) == [
        {"media_fbid": "photo-1"}, {"media_fbid": "photo-2"},
    ]


@pytest.mark.asyncio
async def test_publish_carousel_post_missing_creds(monkeypatch):
    monkeypatch.delenv("FB_PAGE_ACCESS_TOKEN", raising=False)
    result = await fb_publish_carousel.publish_carousel_post(["photo-1", "photo-2"])
    assert not result.ok
    assert "credentials" in result.detail


@pytest.mark.asyncio
async def test_publish_carousel_post_http_error():
    _FakeAsyncClient.responses = [_FakeResponse(400, text="bad")]
    result = await fb_publish_carousel.publish_carousel_post(["photo-1", "photo-2"])
    assert not result.ok
    assert "400" in result.detail


@pytest.mark.asyncio
async def test_publish_carousel_post_no_id_in_response():
    _FakeAsyncClient.responses = [_FakeResponse(200, {})]
    result = await fb_publish_carousel.publish_carousel_post(["photo-1", "photo-2"])
    assert not result.ok
    assert "no post id" in result.detail
