"""Tests for src/channels/ig_publish_carousel.py — IG carousel two-step publish.

Same fake-``httpx.AsyncClient`` convention as ``tests/test_ig_publish.py`` —
no real network, ever.
"""

from __future__ import annotations

import pytest

from src.channels import ig_publish_carousel


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
    monkeypatch.setattr(ig_publish_carousel.httpx, "AsyncClient", _FakeAsyncClient)


@pytest.fixture(autouse=True)
def _creds(monkeypatch):
    monkeypatch.setenv("IG_PAGE_ACCESS_TOKEN", "ig_tok")
    monkeypatch.setenv("IG_USER_ID", "IGBIZ")
    for var in ("META_GRAPH_BASE", "IG_GRAPH_BASE", "FB_GRAPH_BASE"):
        monkeypatch.delenv(var, raising=False)
    monkeypatch.setenv("META_GRAPH_VERSION", "v25.0")


# ------------------------------------------------- create_carousel_item_container


@pytest.mark.asyncio
async def test_create_item_container_success():
    _FakeAsyncClient.responses = [_FakeResponse(200, {"id": "item-1"})]
    result = await ig_publish_carousel.create_carousel_item_container(
        image_url="https://example.com/slide1.png"
    )
    assert result.ok
    assert result.creation_id == "item-1"
    method, url, params = _FakeAsyncClient.calls[0]
    assert method == "POST"
    assert url == "https://graph.instagram.com/v25.0/IGBIZ/media"
    assert params["image_url"] == "https://example.com/slide1.png"
    assert params["is_carousel_item"] == "true"


@pytest.mark.asyncio
async def test_create_item_container_empty_url():
    result = await ig_publish_carousel.create_carousel_item_container(image_url="")
    assert not result.ok
    assert "image_url" in result.detail


@pytest.mark.asyncio
async def test_create_item_container_missing_creds():
    import os

    os.environ.pop("IG_PAGE_ACCESS_TOKEN", None)
    result = await ig_publish_carousel.create_carousel_item_container(
        image_url="https://example.com/slide1.png"
    )
    assert not result.ok
    assert "credentials" in result.detail


@pytest.mark.asyncio
async def test_create_item_container_http_error():
    _FakeAsyncClient.responses = [_FakeResponse(400, {"error": {"message": "bad"}}, text="bad")]
    result = await ig_publish_carousel.create_carousel_item_container(
        image_url="https://example.com/slide1.png"
    )
    assert not result.ok
    assert "400" in result.detail


@pytest.mark.asyncio
async def test_create_item_container_no_id_in_response():
    _FakeAsyncClient.responses = [_FakeResponse(200, {})]
    result = await ig_publish_carousel.create_carousel_item_container(
        image_url="https://example.com/slide1.png"
    )
    assert not result.ok
    assert "no container id" in result.detail


# ----------------------------------------------------- create_carousel_container


@pytest.mark.asyncio
async def test_create_carousel_container_success():
    _FakeAsyncClient.responses = [_FakeResponse(200, {"id": "carousel-1"})]
    result = await ig_publish_carousel.create_carousel_container(
        ["item-1", "item-2", "item-3"], caption="hello"
    )
    assert result.ok
    assert result.creation_id == "carousel-1"
    method, url, params = _FakeAsyncClient.calls[0]
    assert method == "POST"
    assert url == "https://graph.instagram.com/v25.0/IGBIZ/media"
    assert params["media_type"] == "CAROUSEL"
    assert params["children"] == "item-1,item-2,item-3"
    assert params["caption"] == "hello"


@pytest.mark.asyncio
async def test_create_carousel_container_too_few_items():
    result = await ig_publish_carousel.create_carousel_container(["only-one"])
    assert not result.ok
    assert "at least" in result.detail
    assert _FakeAsyncClient.calls == []  # never made an HTTP call


@pytest.mark.asyncio
async def test_create_carousel_container_too_many_items():
    result = await ig_publish_carousel.create_carousel_container([f"i{n}" for n in range(11)])
    assert not result.ok
    assert "at most" in result.detail
    assert _FakeAsyncClient.calls == []


@pytest.mark.asyncio
async def test_create_carousel_container_strips_blank_ids():
    _FakeAsyncClient.responses = [_FakeResponse(200, {"id": "carousel-2"})]
    result = await ig_publish_carousel.create_carousel_container(["item-1", "", "  ", "item-2"])
    assert result.ok
    _, _, params = _FakeAsyncClient.calls[0]
    assert params["children"] == "item-1,item-2"


@pytest.mark.asyncio
async def test_create_carousel_container_missing_creds():
    import os

    os.environ.pop("IG_PAGE_ACCESS_TOKEN", None)
    result = await ig_publish_carousel.create_carousel_container(["item-1", "item-2"])
    assert not result.ok
    assert "credentials" in result.detail


@pytest.mark.asyncio
async def test_create_carousel_container_http_error():
    _FakeAsyncClient.responses = [_FakeResponse(400, {"error": {"message": "bad"}}, text="bad")]
    result = await ig_publish_carousel.create_carousel_container(["item-1", "item-2"])
    assert not result.ok
    assert "400" in result.detail


@pytest.mark.asyncio
async def test_create_carousel_container_no_id_in_response():
    _FakeAsyncClient.responses = [_FakeResponse(200, {})]
    result = await ig_publish_carousel.create_carousel_container(["item-1", "item-2"])
    assert not result.ok
    assert "no container id" in result.detail
