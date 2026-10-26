"""notion_publish_language.py — refuse to publish a Reel whose spoken audio
is not the language the IP is supposed to speak.

WHY THIS EXISTS
---------------
2026-10-22: Jackie's "Can't Go Every Morning?" Reel went live with shot 1
spoken in CHINESE. The MiniMax voice track uploaded for that shot was
English, but 即梦 (Jimeng) re-voiced the clip itself. Nothing downstream
looks at the audio, so a wrong-language clip sails straight through to a
real, irreversible Instagram post.

This gate transcribes the FINAL ``Production Video`` and checks it against
the row's own ``🗣️ Voice script`` blocks before a row is claimed.

WHY NOT JUST CHECK THE DETECTED LANGUAGE
----------------------------------------
Whisper picks ONE language for the whole file. On a mixed clip (one Chinese
shot, three English shots) it reports "english" and then silently drops or
garbles the Chinese part, so the language label alone passes the exact
failure this gate exists for (verified on the 2026-10-22 video). The real
proof is script coverage: every sentence we wrote must be audible in the
transcript. A missing/garbled shot shows up as a sentence with no match.

Enforced for English IPs only. Other languages (Cantonese) are passed
through unchecked for now — see ``check_video_language``.

Fail-closed: no speech-to-text key, no script, oversized file, API error → NOT ok.
Set ``PUBLISH_LANGUAGE_GATE=off`` to disable (emergency only).
"""

from __future__ import annotations

import json
import os
import re
import urllib.error
import urllib.request
import uuid
from collections.abc import Callable
from dataclasses import dataclass
from typing import Any, Final

# (url, model, key env var) — Groq first when configured: same Whisper family,
# OpenAI-compatible API, and it does not share OpenAI's image-gen credit pool.
_PROVIDERS: Final = (
    (
        "https://api.groq.com/openai/v1/audio/transcriptions",
        "whisper-large-v3-turbo",
        "GROQ_API_KEY",
    ),
    ("https://api.openai.com/v1/audio/transcriptions", "whisper-1", "OPENAI_API_KEY"),
)
_MAX_BYTES: Final = 24 * 1024 * 1024  # API hard limit is 25 MB
_TIMEOUT_S: Final = 120
_MIN_SENTENCE_COVERAGE: Final = 0.6
_MAX_CJK_RATIO: Final = 0.02
_SCRIPT_MARKER: Final = "voice script"

_CJK = re.compile(r"[㐀-䶿一-鿿぀-ヿ가-힯]")
_WORD = re.compile(r"[a-z0-9']+")
_SENTENCE_SPLIT = re.compile(r"(?<=[.!?])\s+")


@dataclass(frozen=True)
class GateResult:
    ok: bool
    reason: str = ""
    transcript: str = ""


class LanguageGateError(Exception):
    """Transcription could not be completed (treated as a block, never a pass)."""


def gate_enabled() -> bool:
    return os.environ.get("PUBLISH_LANGUAGE_GATE", "on").strip().lower() not in {
        "off",
        "0",
        "false",
    }


def _block_text(block: dict) -> str:
    return "".join(
        x.get("plain_text", "") for x in block.get(block.get("type", ""), {}).get("rich_text", [])
    )


def expected_sentences(row_id: str, children: Callable[[str], list[dict]]) -> list[str]:
    """Every sentence of every ``🗣️ Voice script`` code block on the row."""
    blocks = children(row_id)
    sentences: list[str] = []
    for index, block in enumerate(blocks):
        if block.get("type") != "paragraph" or _SCRIPT_MARKER not in _block_text(block).lower():
            continue
        if index + 1 < len(blocks) and blocks[index + 1].get("type") == "code":
            text = _block_text(blocks[index + 1]).strip()
            sentences.extend(split_sentences(text))
    return sentences


def _words(text: str) -> list[str]:
    return _WORD.findall(text.lower())


def _coverage(sentence: str, transcript_words: set[str]) -> float:
    words = _words(sentence)
    if not words:
        return 1.0
    return sum(1 for w in words if w in transcript_words) / len(words)


def _cjk_ratio(text: str) -> float:
    letters = [c for c in text if not c.isspace()]
    return len(_CJK.findall(text)) / len(letters) if letters else 0.0


def _download(url: str) -> bytes:
    try:
        with urllib.request.urlopen(url, timeout=_TIMEOUT_S) as response:
            data = response.read(_MAX_BYTES + 1)
    except (urllib.error.URLError, OSError, TimeoutError) as exc:
        raise LanguageGateError(f"could not download video: {exc}") from exc
    if len(data) > _MAX_BYTES:
        raise LanguageGateError("video larger than 24 MB — cannot transcribe, check by hand")
    return data


def _provider() -> tuple[str, str, str]:
    for url, model, env in _PROVIDERS:
        key = os.environ.get(env, "").strip()
        if key:
            return url, model, key
    raise LanguageGateError("no speech-to-text key set (GROQ_API_KEY or OPENAI_API_KEY)")


def _multipart(video: bytes, model: str) -> tuple[str, bytes]:
    boundary = uuid.uuid4().hex
    parts = [
        f'--{boundary}\r\nContent-Disposition: form-data; name="model"\r\n\r\n{model}\r\n',
        f'--{boundary}\r\nContent-Disposition: form-data; name="response_format"'
        "\r\n\r\nverbose_json\r\n",
        f'--{boundary}\r\nContent-Disposition: form-data; name="file"; filename="video.mp4"\r\n'
        "Content-Type: video/mp4\r\n\r\n",
    ]
    body = "".join(parts).encode() + video + f"\r\n--{boundary}--\r\n".encode()
    return boundary, body


def transcribe_video(video_url: str) -> dict[str, Any]:
    """→ ``{"language": "english", "text": "..."}`` via hosted Whisper."""
    url, model, key = _provider()
    boundary, body = _multipart(_download(video_url), model)
    request = urllib.request.Request(
        url,
        data=body,
        headers={
            "Authorization": f"Bearer {key}",
            "Content-Type": f"multipart/form-data; boundary={boundary}",
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=_TIMEOUT_S) as response:
            data = json.loads(response.read().decode("utf-8"))
    except (urllib.error.URLError, OSError, TimeoutError, json.JSONDecodeError) as exc:
        raise LanguageGateError(f"transcription failed: {exc}") from exc
    if not isinstance(data, dict) or "text" not in data:
        raise LanguageGateError("unexpected transcription response")
    return {"language": str(data.get("language", "")).lower(), "text": str(data["text"])}


def check_video_language(
    video_url: str,
    row_id: str,
    language: str,
    children: Callable[[str], list[dict]],
    *,
    transcribe: Callable[[str], dict[str, Any]] | None = None,
) -> GateResult:
    """Is the audio of ``video_url`` the IP's language and the script we wrote?"""
    if not gate_enabled():
        return GateResult(True, "gate disabled via PUBLISH_LANGUAGE_GATE")
    if language != "en":
        return GateResult(True, f"language gate only enforced for 'en', not {language!r}")

    sentences = expected_sentences(row_id, children)
    if not sentences:
        return GateResult(False, "row has no 🗣️ Voice script to verify the audio against")
    try:
        result = (transcribe or transcribe_video)(video_url)
    except LanguageGateError as exc:
        return GateResult(False, str(exc))
    return evaluate_transcript(result, sentences)


def evaluate_transcript(result: dict[str, Any], sentences: list[str]) -> GateResult:
    """Is this English transcript the script we wrote? (shared with the studio's
    per-shot check, so a shot is judged by exactly the rule publishing uses)"""
    text = result["text"]
    if result["language"] and result["language"] != "english":
        return GateResult(
            False, f"audio detected as {result['language']!r}, expected English", text
        )
    if _cjk_ratio(text) > _MAX_CJK_RATIO:
        return GateResult(False, "Chinese characters in the spoken transcript", text)

    heard = set(_words(text))
    missing = [s for s in sentences if _coverage(s, heard) < _MIN_SENTENCE_COVERAGE]
    if missing:
        shown = " | ".join(m[:60] for m in missing[:3])
        return GateResult(
            False,
            f"{len(missing)}/{len(sentences)} script sentences not heard in the audio "
            f"(wrong language or wrong words): {shown}",
            text,
        )
    return GateResult(True, "English audio matches script", text)


def split_sentences(script: str) -> list[str]:
    return [s.strip() for s in _SENTENCE_SPLIT.split(script.strip()) if s.strip()]
