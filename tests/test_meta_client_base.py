"""Per-platform Graph host resolution for the Meta send client.

Instagram (Instagram Login / IGAA tokens) MUST talk to graph.instagram.com,
while Facebook Pages / Messenger MUST talk to graph.facebook.com. A single
global ``META_GRAPH_BASE`` cannot serve both, so the base is resolved per
platform. These tests lock that contract.
"""

from __future__ import annotations

import importlib

import pytest


@pytest.fixture()
def meta_client(monkeypatch):
    """Reload the module with a clean env each test (it reads env lazily,
    but the reload guards against import-time caching regressions)."""
    for var in (
        "META_GRAPH_BASE",
        "IG_GRAPH_BASE",
        "FB_GRAPH_BASE",
        "META_GRAPH_VERSION",
    ):
        monkeypatch.delenv(var, raising=False)
    module = importlib.import_module("src.channels.meta_client")
    return importlib.reload(module)


def test_defaults_are_platform_correct(meta_client):
    assert meta_client._base("instagram") == "https://graph.instagram.com"
    assert meta_client._base("facebook") == "https://graph.facebook.com"


def test_legacy_global_only_affects_instagram(meta_client, monkeypatch):
    # Real prod state: IG setup set the global to the instagram host.
    monkeypatch.setenv("META_GRAPH_BASE", "https://graph.instagram.com")
    assert meta_client._base("instagram") == "https://graph.instagram.com"
    # Facebook MUST NOT inherit the instagram host.
    assert meta_client._base("facebook") == "https://graph.facebook.com"


def test_per_platform_overrides_win(meta_client, monkeypatch):
    monkeypatch.setenv("IG_GRAPH_BASE", "https://ig.example.com/")
    monkeypatch.setenv("FB_GRAPH_BASE", "https://fb.example.com/")
    assert meta_client._base("instagram") == "https://ig.example.com"
    assert meta_client._base("facebook") == "https://fb.example.com"


def test_graph_url_uses_platform_host(meta_client, monkeypatch):
    monkeypatch.setenv("META_GRAPH_BASE", "https://graph.instagram.com")
    monkeypatch.setenv("META_GRAPH_VERSION", "v23.0")
    ig_url = meta_client._graph_url("instagram", "123/messages")
    fb_url = meta_client._graph_url("facebook", "1200796509776468/messages")
    assert ig_url == "https://graph.instagram.com/v23.0/123/messages"
    assert fb_url == "https://graph.facebook.com/v23.0/1200796509776468/messages"
