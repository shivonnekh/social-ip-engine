"""notion_transcribe_words.py — word-level timestamp transcription via
OpenAI's hosted ``whisper-1`` endpoint.

WHY A SEPARATE MODULE FROM ``llm_transcribe.py``
--------------------------------------------------
``llm_transcribe.transcribe_audio()`` returns plain text via
``gpt-4o-transcribe`` — good enough for a WhatsApp voice-note reply, but the
caption-burning pipeline (``notion_caption_render.py`` /
``notion_caption_gen.py``) needs per-WORD start/end timestamps so it can
karaoke-highlight each word as it's spoken. ``gpt-4o-transcribe`` does NOT
support ``timestamp_granularities`` — only the older ``whisper-1`` model
does, via ``response_format="verbose_json"`` +
``timestamp_granularities=["word"]``. Kept as its own module (rather than a
second mode bolted onto ``llm_transcribe.py``) so that module's one job
(voice note -> text) and this one's (video -> word timings) never blur
together — different models, different response shapes, different callers.

CONTRACT
--------
Same never-raise contract as ``llm_transcribe.transcribe_audio`` — any
failure (missing/empty audio, network/API error, a response missing the
``words`` field entirely) returns ``[]``, never raises. This matters
doubly here: the only caller (``notion_caption_gen.burn_captions_for_row``)
is itself dispatched from a detached ``asyncio.create_task`` with nothing
awaiting its result — an uncaught exception anywhere in that chain would
only ever surface as an ugly "Task exception was never retrieved" log line
instead of a clean, actionable warning string.
"""

from __future__ import annotations

import io
import logging

from openai import AsyncOpenAI

logger = logging.getLogger("notion_transcribe_words")

# whisper-1 is the ONLY OpenAI transcription model that supports
# timestamp_granularities=["word"] — gpt-4o-transcribe (this repo's default
# for plain-text voice-note transcription, see llm_transcribe.py) rejects it.
_MODEL = "whisper-1"


async def transcribe_words(
    audio_bytes: bytes,
    *,
    filename_hint: str = "audio.mp3",
    client: AsyncOpenAI | None = None,
) -> list[dict]:
    """Word-level transcription of ``audio_bytes`` (an audio OR video file —
    whisper-1 reads the audio track out of common video containers like mp4
    directly, no separate extraction step needed).

    Returns ``[{"word": str, "start": float, "end": float}, ...]`` in
    playback order, or ``[]`` on ANY failure — never raises, same contract
    as ``llm_transcribe.transcribe_audio``. An empty ``audio_bytes`` returns
    ``[]`` immediately without making an API call at all (mirrors
    ``transcribe_audio``'s identical empty-input short-circuit).
    """
    if not audio_bytes:
        return []
    oai = client or AsyncOpenAI()
    buf = io.BytesIO(audio_bytes)
    buf.name = filename_hint  # OpenAI uses the extension for format detection
    try:
        resp = await oai.audio.transcriptions.create(
            model=_MODEL,
            file=buf,
            response_format="verbose_json",
            timestamp_granularities=["word"],
        )
        # A response with no `words` attribute at all, or an explicit
        # `None`, both mean "no word-level data came back" — treated
        # identically to a clean empty result, not a crash. `getattr` (not
        # `resp.words`) is deliberate: some SDK/response shapes may omit the
        # attribute entirely rather than setting it to None.
        raw_words = getattr(resp, "words", None) or []
        words = [
            {"word": str(w.word), "start": float(w.start), "end": float(w.end)}
            for w in raw_words
        ]
        logger.info("word-transcribed %d bytes → %d words", len(audio_bytes), len(words))
        return words
    except Exception as exc:  # noqa: BLE001 - must survive anything, see module docstring
        logger.exception(
            "whisper word-transcribe failed (%d bytes): %s", len(audio_bytes), exc
        )
        return []
