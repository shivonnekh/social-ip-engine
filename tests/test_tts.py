"""Tests for ``src.media.tts`` — MiniMax Cantonese TTS module.

Run with: ``pytest tests/test_tts.py -v``

These tests never hit the real MiniMax API. The HTTP boundary is faked via
a respx-style monkey-patch of ``httpx.AsyncClient.post`` so the cache,
hex decode, error handling, and trigger logic can all be exercised offline.
"""

from __future__ import annotations

from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from src.media import tts


# ── Fixtures ──────────────────────────────────────────────────────


@pytest.fixture
def enabled_env(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    """Wire env so synthesize() will actually try to call MiniMax."""
    monkeypatch.setenv("TTS_ENABLED", "true")
    monkeypatch.setenv("MINIMAX_API_KEY", "fake-key")
    monkeypatch.setenv("MINIMAX_TTS_VOICE", "Cantonese_KindWoman")
    monkeypatch.setenv("TTS_CACHE_DIR", str(tmp_path / "tts"))


@pytest.fixture
def fake_response(audio_hex: str = "deadbeef") -> MagicMock:
    """Build a fake ``httpx.Response`` matching the MiniMax success shape."""
    resp = MagicMock()
    resp.status_code = 200
    resp.json.return_value = {
        "base_resp": {"status_code": 0},
        "data": {"audio": audio_hex},
    }
    return resp


# ── _clean_for_speech ─────────────────────────────────────────────


class TestCleanForSpeech:
    def test_strips_urls(self) -> None:
        text = "睇下呢個 https://tcm-jessica.example.com/abc 啦"
        out = tts._clean_for_speech(text)
        assert "https" not in out
        assert "睇下呢個" in out

    def test_strips_emoji(self) -> None:
        text = "好開心呀 😊 ✨🌿 唔該晒"
        out = tts._clean_for_speech(text)
        assert "😊" not in out
        assert "🌿" not in out
        assert "好開心呀" in out
        assert "唔該晒" in out

    def test_strips_markdown_bold_and_headers(self) -> None:
        text = "## 標題\n**重點** 同 *斜體*"
        out = tts._clean_for_speech(text)
        assert "**" not in out
        assert "##" not in out
        assert "重點" in out

    def test_strips_bullet_markers(self) -> None:
        text = "- 第一條\n• 第二條\n· 第三條"
        out = tts._clean_for_speech(text)
        # The dashes / bullets at line start should be gone
        assert not out.startswith("-")
        assert "第一條" in out and "第二條" in out and "第三條" in out

    def test_collapses_whitespace(self) -> None:
        text = "你好  \n\n\n  嗨"
        out = tts._clean_for_speech(text)
        assert out == "你好 嗨"

    def test_empty_input_returns_empty(self) -> None:
        assert tts._clean_for_speech("") == ""
        assert tts._clean_for_speech("   \n  ") == ""


# ── merge_bubbles_for_speech ──────────────────────────────────────


class TestMergeBubbles:
    def test_joins_with_sentence_pause(self) -> None:
        out = tts.merge_bubbles_for_speech(["你好", "我係 Jessica"])
        assert "你好" in out and "我係 Jessica" in out
        # Some sentence separator should be present
        assert "。" in out or " " in out

    def test_drops_empty_bubbles(self) -> None:
        out = tts.merge_bubbles_for_speech(["你好", "", "  ", "再見"])
        assert "你好" in out and "再見" in out

    def test_no_double_full_stop_when_bubble_ends_with_question(self) -> None:
        out = tts.merge_bubbles_for_speech(["係咪呀？", "我幫你"])
        assert "？。" not in out

    def test_no_double_full_stop_when_bubble_ends_with_exclamation(self) -> None:
        out = tts.merge_bubbles_for_speech(["太好喇！", "我哋繼續"])
        assert "！。" not in out

    def test_empty_input_returns_empty(self) -> None:
        assert tts.merge_bubbles_for_speech([]) == ""
        assert tts.merge_bubbles_for_speech(["", "   "]) == ""


# ── synthesize() disabled / empty paths ──────────────────────────


class TestSynthesizeGuards:
    @pytest.mark.asyncio
    async def test_returns_none_when_disabled(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setenv("TTS_ENABLED", "false")
        result = await tts.synthesize("有嘢講")
        assert result is None

    @pytest.mark.asyncio
    async def test_returns_none_for_empty_text(self, enabled_env: None) -> None:
        result = await tts.synthesize("   \n  ")
        assert result is None

    @pytest.mark.asyncio
    async def test_returns_none_when_api_key_missing(
        self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
    ) -> None:
        monkeypatch.setenv("TTS_ENABLED", "true")
        monkeypatch.delenv("MINIMAX_API_KEY", raising=False)
        monkeypatch.setenv("TTS_CACHE_DIR", str(tmp_path / "tts"))
        result = await tts.synthesize("你好")
        assert result is None


# ── synthesize() success / caching ───────────────────────────────


class TestSynthesizeHTTP:
    @pytest.mark.asyncio
    async def test_decodes_hex_audio_and_writes_cache(
        self, enabled_env: None, fake_response: MagicMock
    ) -> None:
        with patch("httpx.AsyncClient") as ClientCls:
            client_instance = AsyncMock()
            client_instance.post = AsyncMock(return_value=fake_response)
            ClientCls.return_value.__aenter__.return_value = client_instance

            result = await tts.synthesize("你好呀")

        assert result is not None
        # 0xdeadbeef → 4 bytes
        assert result.byte_count == 4
        assert result.path.exists()
        assert result.path.read_bytes() == bytes.fromhex("deadbeef")
        assert result.url.endswith(".mp3")
        assert result.mime_type == "audio/mpeg"

    @pytest.mark.asyncio
    async def test_cache_hit_skips_second_api_call(
        self, enabled_env: None, fake_response: MagicMock
    ) -> None:
        with patch("httpx.AsyncClient") as ClientCls:
            client_instance = AsyncMock()
            client_instance.post = AsyncMock(return_value=fake_response)
            ClientCls.return_value.__aenter__.return_value = client_instance

            r1 = await tts.synthesize("同一句話")
            r2 = await tts.synthesize("同一句話")

        assert r1 is not None and r2 is not None
        assert r1.url == r2.url
        # API should have been called exactly once — second call hit cache
        assert client_instance.post.call_count == 1

    @pytest.mark.asyncio
    async def test_returns_none_on_minimax_error_status(
        self, enabled_env: None
    ) -> None:
        bad_resp = MagicMock()
        bad_resp.status_code = 200
        bad_resp.json.return_value = {
            "base_resp": {"status_code": 1001, "status_msg": "invalid voice"},
            "data": {},
        }

        with patch("httpx.AsyncClient") as ClientCls:
            client_instance = AsyncMock()
            client_instance.post = AsyncMock(return_value=bad_resp)
            ClientCls.return_value.__aenter__.return_value = client_instance

            result = await tts.synthesize("錯誤測試")

        assert result is None

    @pytest.mark.asyncio
    async def test_returns_none_on_http_error_status(
        self, enabled_env: None
    ) -> None:
        bad_resp = MagicMock()
        bad_resp.status_code = 500
        bad_resp.text = "server error"

        with patch("httpx.AsyncClient") as ClientCls:
            client_instance = AsyncMock()
            client_instance.post = AsyncMock(return_value=bad_resp)
            ClientCls.return_value.__aenter__.return_value = client_instance

            result = await tts.synthesize("HTTP 500 測試")

        assert result is None


# ── _public_url ───────────────────────────────────────────────────


class TestPublicURL:
    def test_uses_jessica_base_url_when_set(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setenv("JESSICA_BASE_URL", "https://tcm-jessica.example.com/")
        url = tts._public_url("abc.mp3")
        # Trailing slash should be stripped
        assert url == "https://tcm-jessica.example.com/media/tts/abc.mp3"

    def test_falls_back_to_relative_when_unset(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.delenv("JESSICA_BASE_URL", raising=False)
        url = tts._public_url("abc.mp3")
        assert url == "/media/tts/abc.mp3"


# ── _atomic_write_bytes ───────────────────────────────────────────


class TestAtomicWrite:
    def test_writes_full_payload(self, tmp_path: Path) -> None:
        target = tmp_path / "out.mp3"
        tts._atomic_write_bytes(target, b"\x00\x01\x02\x03")
        assert target.read_bytes() == b"\x00\x01\x02\x03"

    def test_overwrites_existing_file(self, tmp_path: Path) -> None:
        target = tmp_path / "out.mp3"
        target.write_bytes(b"old")
        tts._atomic_write_bytes(target, b"new")
        assert target.read_bytes() == b"new"

    def test_creates_parent_dirs(self, tmp_path: Path) -> None:
        target = tmp_path / "nested" / "tts" / "out.mp3"
        tts._atomic_write_bytes(target, b"x")
        assert target.exists() and target.read_bytes() == b"x"

    def test_no_temp_files_leak_on_success(self, tmp_path: Path) -> None:
        target = tmp_path / "out.mp3"
        tts._atomic_write_bytes(target, b"x")
        # No .tts-*.mp3.tmp leftovers in the directory
        leftovers = [p for p in tmp_path.iterdir() if p.name.startswith(".tts-")]
        assert leftovers == []
