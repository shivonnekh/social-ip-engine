"""Tests for src/notion_transcribe_words.py — word-level timestamp
transcription via OpenAI's whisper-1 endpoint.

The real OpenAI client is never touched: ``client`` is dependency-injected
as a tiny fake object shaped like ``AsyncOpenAI`` (``.audio.transcriptions
.create(...)``), mirroring how ``llm_transcribe.transcribe_audio`` is
exercised in spirit (no test file exists yet for that sibling module, so
this file establishes the fake-client convention for both).
"""

from __future__ import annotations

from types import SimpleNamespace
from typing import Any

import pytest

from src.notion_transcribe_words import transcribe_words


class _FakeTranscriptions:
    def __init__(self, response: Any = None, exc: Exception | None = None):
        self._response = response
        self._exc = exc
        self.calls: list[dict] = []

    async def create(self, **kwargs: Any) -> Any:
        self.calls.append(kwargs)
        if self._exc is not None:
            raise self._exc
        return self._response


class _FakeClient:
    def __init__(self, transcriptions: _FakeTranscriptions):
        self.audio = SimpleNamespace(transcriptions=transcriptions)


def _word(word: str, start: float, end: float) -> SimpleNamespace:
    return SimpleNamespace(word=word, start=start, end=end)


@pytest.mark.asyncio
async def test_empty_audio_bytes_returns_empty_list_without_calling_api():
    transcriptions = _FakeTranscriptions()
    client = _FakeClient(transcriptions)

    result = await transcribe_words(b"", client=client)  # type: ignore[arg-type]

    assert result == []
    assert transcriptions.calls == []  # API never even attempted


@pytest.mark.asyncio
async def test_success_path_returns_plain_dicts():
    fake_response = SimpleNamespace(
        words=[_word("Hello", 0.0, 0.3), _word("world", 0.3, 0.6)]
    )
    transcriptions = _FakeTranscriptions(response=fake_response)
    client = _FakeClient(transcriptions)

    result = await transcribe_words(b"fake-audio-bytes", client=client)  # type: ignore[arg-type]

    assert result == [
        {"word": "Hello", "start": 0.0, "end": 0.3},
        {"word": "world", "start": 0.3, "end": 0.6},
    ]
    assert len(transcriptions.calls) == 1
    call = transcriptions.calls[0]
    assert call["model"] == "whisper-1"
    assert call["response_format"] == "verbose_json"
    assert call["timestamp_granularities"] == ["word"]


@pytest.mark.asyncio
async def test_api_failure_returns_empty_list_never_raises():
    transcriptions = _FakeTranscriptions(exc=RuntimeError("api exploded"))
    client = _FakeClient(transcriptions)

    result = await transcribe_words(b"fake-audio-bytes", client=client)  # type: ignore[arg-type]

    assert result == []


@pytest.mark.asyncio
async def test_response_missing_words_attribute_returns_empty_list():
    fake_response = SimpleNamespace()  # no `words` attribute at all
    transcriptions = _FakeTranscriptions(response=fake_response)
    client = _FakeClient(transcriptions)

    result = await transcribe_words(b"fake-audio-bytes", client=client)  # type: ignore[arg-type]

    assert result == []


@pytest.mark.asyncio
async def test_response_words_is_none_returns_empty_list():
    fake_response = SimpleNamespace(words=None)
    transcriptions = _FakeTranscriptions(response=fake_response)
    client = _FakeClient(transcriptions)

    result = await transcribe_words(b"fake-audio-bytes", client=client)  # type: ignore[arg-type]

    assert result == []


@pytest.mark.asyncio
async def test_response_words_is_empty_list_returns_empty_list():
    fake_response = SimpleNamespace(words=[])
    transcriptions = _FakeTranscriptions(response=fake_response)
    client = _FakeClient(transcriptions)

    result = await transcribe_words(b"fake-audio-bytes", client=client)  # type: ignore[arg-type]

    assert result == []


@pytest.mark.asyncio
async def test_malformed_word_object_missing_attribute_returns_empty_list():
    """A word object that's missing .start/.end (unexpected SDK shape drift)
    must be caught by the broad except, not raise an uncaught AttributeError."""
    fake_response = SimpleNamespace(words=[SimpleNamespace(word="Hello")])  # no .start/.end
    transcriptions = _FakeTranscriptions(response=fake_response)
    client = _FakeClient(transcriptions)

    result = await transcribe_words(b"fake-audio-bytes", client=client)  # type: ignore[arg-type]

    assert result == []


@pytest.mark.asyncio
async def test_filename_hint_used_for_the_uploaded_buffer():
    fake_response = SimpleNamespace(words=[])
    transcriptions = _FakeTranscriptions(response=fake_response)
    client = _FakeClient(transcriptions)

    await transcribe_words(
        b"fake-audio-bytes", filename_hint="row123.mp4", client=client  # type: ignore[arg-type]
    )

    uploaded_file = transcriptions.calls[0]["file"]
    assert uploaded_file.name == "row123.mp4"
