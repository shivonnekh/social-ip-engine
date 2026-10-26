"""shot_language.py — is a freshly generated 即梦 shot actually speaking its script?

即梦 re-synthesizes the voice from the uploaded clip and sometimes speaks
CHINESE over an English script (2026-10-22: shot 1 of Jackie's "Can't Go Every
Morning?" went live that way). This checks each shot right after it is
generated, so a bad one is regenerated instead of reaching Notion.

Same judge as the publish gate (``src/notion_publish_language.py``) so a shot
that passes here cannot be blocked there for language.

English-only: a script with no CJK characters is expected to be spoken in
English; Chinese/Cantonese scripts and silent shots are not checked.
"""
from __future__ import annotations

import json
import re
import subprocess
import sys
import tempfile
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

from src import notion_publish_language as gate  # noqa: E402

_CJK = re.compile(r"[㐀-䶿一-鿿]")


def expects_english(voice_text: str) -> bool:
    return bool(voice_text.strip()) and not _CJK.search(voice_text)


def _local_whisper(mp4: str) -> dict:
    """Fallback when no hosted key works: the `whisper` CLI (brew openai-whisper)."""
    with tempfile.TemporaryDirectory() as out:
        run = subprocess.run(
            ["whisper", mp4, "--model", "base", "--output_format", "json", "--output_dir", out],
            capture_output=True, text=True,
        )
        files = list(Path(out).glob("*.json"))
        if run.returncode != 0 or not files:
            raise gate.LanguageGateError(f"local whisper failed: {(run.stderr or '')[-200:]}")
        data = json.loads(files[0].read_text(encoding="utf-8"))
    return {"language": {"english": "english", "en": "english"}.get(
        str(data.get("language", "")).lower(), str(data.get("language", "")).lower()),
        "text": data.get("text", "")}


def check_shot(mp4: str, voice_text: str) -> tuple[bool, str]:
    """→ (ok, reason). Shots that aren't English-scripted pass untouched."""
    if not gate.gate_enabled() or not expects_english(voice_text):
        return True, "not checked"
    sentences = gate.split_sentences(voice_text)
    try:
        result = gate.transcribe_video(Path(mp4).resolve().as_uri())
    except gate.LanguageGateError as hosted_err:
        try:
            result = _local_whisper(mp4)
        except gate.LanguageGateError as local_err:
            return False, f"could not verify audio ({hosted_err}; {local_err})"
    verdict = gate.evaluate_transcript(result, sentences)
    return verdict.ok, verdict.reason
