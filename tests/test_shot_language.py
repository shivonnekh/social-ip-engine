"""Studio per-shot language check — a 即梦 shot speaking Chinese over an English
script must be rejected before it reaches Notion (2026-10-22 incident)."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "studio" / "scripts"))

import shot_language as sl

from src import notion_publish_language as gate

LINE = (
    "If you cannot go every morning, drinking more coffee will not fix it. Your intestines are dry."
)


def _stub(monkeypatch, result=None, error=None):
    def fake(_url):
        if error:
            raise error
        return result

    monkeypatch.setattr(gate, "transcribe_video", fake)


def test_english_shot_passes(monkeypatch):
    _stub(monkeypatch, {"language": "english", "text": LINE})
    assert sl.check_shot("/tmp/x.mp4", LINE)[0]


def test_chinese_voiced_shot_is_rejected(monkeypatch):
    _stub(monkeypatch, {"language": "chinese", "text": "如果媽早上每天去喝多咖啡"})
    ok, why = sl.check_shot("/tmp/x.mp4", LINE)
    assert not ok and "chinese" in why


def test_silent_and_chinese_scripts_are_not_checked(monkeypatch):
    _stub(monkeypatch, error=AssertionError("must not transcribe"))
    assert sl.check_shot("/tmp/x.mp4", "")[0]
    assert sl.check_shot("/tmp/x.mp4", "你好, 今天我们来聊聊")[0]


def test_unverifiable_audio_fails_closed(monkeypatch):
    _stub(monkeypatch, error=gate.LanguageGateError("no key"))
    monkeypatch.setattr(
        sl, "_local_whisper", lambda _m: (_ for _ in ()).throw(gate.LanguageGateError("no whisper"))
    )
    ok, why = sl.check_shot("/tmp/x.mp4", LINE)
    assert not ok and "could not verify" in why


def test_falls_back_to_local_whisper(monkeypatch):
    _stub(monkeypatch, error=gate.LanguageGateError("no credits"))
    monkeypatch.setattr(sl, "_local_whisper", lambda _m: {"language": "english", "text": LINE})
    assert sl.check_shot("/tmp/x.mp4", LINE)[0]


def test_gate_off_skips(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setenv("PUBLISH_LANGUAGE_GATE", "off")
    _stub(monkeypatch, error=AssertionError("must not transcribe"))
    assert sl.check_shot("/tmp/x.mp4", LINE)[0]
