"""Tests for the match-modality voice-out path in ``src.whatsapp.router``.

Verifies that ``_send_bubbles(inbound_was_voice=True)``:
  - calls TTS synth
  - sends the audio file as a final attachment (after the text bubbles)
  - degrades gracefully when synthesis returns None (still sends text)

Run with: ``pytest tests/test_voice_reply_routing.py -v``
"""

from __future__ import annotations

from pathlib import Path
from unittest.mock import AsyncMock, patch

import pytest

from src.media.tts import TTSResult
from src.whatsapp import router as wa_router


@pytest.fixture
def fake_client_send(monkeypatch: pytest.MonkeyPatch) -> AsyncMock:
    """Replace WA client send methods with AsyncMocks so we can inspect calls."""
    send_long = AsyncMock()
    send_message = AsyncMock()

    monkeypatch.setattr(wa_router.client, "send_long_message", send_long)
    monkeypatch.setattr(wa_router.client, "send_message", send_message)
    monkeypatch.setattr(wa_router.client, "_typing_delay", lambda _t: 0.0)
    return send_message  # attachment sends go through send_message


# ── Voice path ──────────────────────────────────────────────────


class TestVoiceReplyPath:
    @pytest.mark.asyncio
    async def test_audio_attachment_sent_after_text_when_inbound_was_voice(
        self,
        fake_client_send: AsyncMock,
        tmp_path: Path,
    ) -> None:
        fake_audio = tmp_path / "abc.mp3"
        fake_audio.write_bytes(b"\x00\x01\x02")
        fake_result = TTSResult(
            path=fake_audio,
            url="https://tcm-jessica.example.com/media/tts/abc.mp3",
            byte_count=3,
        )

        with patch(
            "src.media.tts.synthesize",
            new=AsyncMock(return_value=fake_result),
        ) as synth:
            await wa_router._send_bubbles(
                account_id="acc",
                chat_id="chat",
                bubbles=["你好呀", "好開心見到你"],
                inbound_was_voice=True,
            )

        # TTS was invoked once with the merged script
        assert synth.call_count == 1
        merged_arg = synth.call_args.args[0]
        assert "你好呀" in merged_arg and "好開心見到你" in merged_arg

        # Audio attachment sent via send_message at the end
        attachment_calls = [
            call for call in fake_client_send.call_args_list
            if call.kwargs.get("attachments")
        ]
        assert len(attachment_calls) == 1
        att = attachment_calls[0].kwargs["attachments"][0]
        assert att["type"] == "audio"
        assert att["mimetype"] == "audio/mpeg"
        assert att["url"].endswith("abc.mp3")

    @pytest.mark.asyncio
    async def test_voice_skipped_when_inbound_was_text(
        self, fake_client_send: AsyncMock
    ) -> None:
        with patch("src.media.tts.synthesize", new=AsyncMock()) as synth:
            await wa_router._send_bubbles(
                account_id="acc",
                chat_id="chat",
                bubbles=["text-only reply"],
                inbound_was_voice=False,
            )

        # Synth never called for text-only turns
        assert synth.call_count == 0
        # No audio attachment sent
        for call in fake_client_send.call_args_list:
            for att in (call.kwargs.get("attachments") or []):
                assert att.get("type") != "audio"

    @pytest.mark.asyncio
    async def test_text_still_sends_when_synthesis_returns_none(
        self, fake_client_send: AsyncMock
    ) -> None:
        with patch(
            "src.media.tts.synthesize", new=AsyncMock(return_value=None)
        ):
            await wa_router._send_bubbles(
                account_id="acc",
                chat_id="chat",
                bubbles=["fallback to text"],
                inbound_was_voice=True,
            )

        # send_long_message still called with the text bubble
        assert wa_router.client.send_long_message.await_count == 1
        # No audio attachment ever sent
        for call in fake_client_send.call_args_list:
            for att in (call.kwargs.get("attachments") or []):
                assert att.get("type") != "audio"

    @pytest.mark.asyncio
    async def test_relative_url_does_not_send_audio_attachment(
        self, fake_client_send: AsyncMock, tmp_path: Path
    ) -> None:
        """If JESSICA_BASE_URL isn't configured, TTS returns a relative URL
        which ChatDaddy can't fetch. We log + skip rather than send a
        broken attachment that the user would see as a question mark."""
        fake_result = TTSResult(
            path=tmp_path / "rel.mp3",
            url="/media/tts/rel.mp3",  # relative — should be skipped
            byte_count=10,
        )
        with patch(
            "src.media.tts.synthesize",
            new=AsyncMock(return_value=fake_result),
        ):
            await wa_router._send_bubbles(
                account_id="acc",
                chat_id="chat",
                bubbles=["text"],
                inbound_was_voice=True,
            )

        # Audio attachment should be skipped entirely
        for call in fake_client_send.call_args_list:
            for att in (call.kwargs.get("attachments") or []):
                assert att.get("type") != "audio"

    @pytest.mark.asyncio
    async def test_voice_task_cancelled_when_outer_send_raises(
        self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
    ) -> None:
        """If the bubble-send section raises an unhandled exception, the
        voice synthesis task must be cancelled — otherwise asyncio logs
        "Task was destroyed but it is pending" and the MiniMax HTTP call
        keeps running uselessly."""
        import asyncio as _asyncio

        slow_synth_started = _asyncio.Event()
        slow_synth_finished = _asyncio.Event()

        async def slow_synth(_text: str) -> TTSResult | None:
            slow_synth_started.set()
            try:
                await _asyncio.sleep(5.0)  # never completes within the test
            except _asyncio.CancelledError:
                slow_synth_finished.set()
                raise
            return None

        # Force the bubble-send section to crash hard. We patch the inner
        # impl so the outer try/finally still runs and exercises the
        # cancellation path.
        async def boom(**_kwargs: object) -> None:
            await slow_synth_started.wait()
            raise RuntimeError("simulated crash inside _send_bubbles_impl")

        monkeypatch.setattr(wa_router, "_send_bubbles_impl", boom)

        with patch("src.media.tts.synthesize", new=slow_synth):
            with pytest.raises(RuntimeError, match="simulated crash"):
                await wa_router._send_bubbles(
                    account_id="acc",
                    chat_id="chat",
                    bubbles=["any text"],
                    inbound_was_voice=True,
                )

        # Cancellation should have propagated into the slow synth coroutine
        await _asyncio.wait_for(slow_synth_finished.wait(), timeout=1.0)

    @pytest.mark.asyncio
    async def test_voice_still_attempted_when_text_send_fails_midway(
        self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
    ) -> None:
        """If a text bubble fails to send, we still try to deliver the voice
        file — so a voice-replying user gets at least the audio version."""
        text_send = AsyncMock(side_effect=RuntimeError("network down"))
        audio_send = AsyncMock()
        monkeypatch.setattr(wa_router.client, "send_long_message", text_send)
        monkeypatch.setattr(wa_router.client, "send_message", audio_send)
        monkeypatch.setattr(wa_router.client, "_typing_delay", lambda _t: 0.0)

        fake_result = TTSResult(
            path=tmp_path / "v.mp3",
            url="https://example.com/media/tts/v.mp3",
            byte_count=10,
        )
        with patch(
            "src.media.tts.synthesize",
            new=AsyncMock(return_value=fake_result),
        ):
            await wa_router._send_bubbles(
                account_id="acc",
                chat_id="chat",
                bubbles=["first bubble"],
                inbound_was_voice=True,
            )

        # Audio attachment WAS sent despite text failure
        assert audio_send.call_count == 1
        att = audio_send.call_args.kwargs["attachments"][0]
        assert att["type"] == "audio"
