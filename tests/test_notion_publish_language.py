"""Language gate: a Reel is only claimed when its audio is English AND matches
the row's Voice script. Regression for the 2026-10-22 Chinese-hook incident."""

from __future__ import annotations

import pytest

from src import notion_publish_language as gate

SCRIPT = [
    "If you cannot go every morning, drinking more coffee will not fix it. "
    "Your intestines are dry, not lazy.",
    "In Chinese medicine, dry stool means fluids and blood are not moistening the bowel.",
    "Comment bowel and I will send you my full morning movement protocol.",
]


def _blocks(scripts: list[str]) -> list[dict]:
    out: list[dict] = []
    for text in scripts:
        out.append(
            {"type": "paragraph", "paragraph": {"rich_text": [{"plain_text": "🗣️ Voice script"}]}}
        )
        out.append({"type": "code", "code": {"rich_text": [{"plain_text": text}]}})
    return out


def _children(scripts: list[str]):
    return lambda _id: _blocks(scripts)


def _run(transcript: dict, scripts=SCRIPT, language="en"):
    return gate.check_video_language(
        "https://x/v.mp4", "row", language, _children(scripts), transcribe=lambda _u: transcript
    )


GOOD = {
    "language": "english",
    "text": " ".join(SCRIPT),
}


def test_passes_when_english_and_script_heard():
    assert _run(GOOD).ok


def test_tolerates_small_asr_slips():
    text = GOOD["text"].replace("stool", "stew").replace("Comment bowel", "I'm in bowel")
    assert _run({"language": "english", "text": text}).ok


def test_blocks_non_english_detection():
    r = _run({"language": "chinese", "text": GOOD["text"]})
    assert not r.ok and "chinese" in r.reason


def test_blocks_chinese_characters_in_transcript():
    r = _run(
        {
            "language": "english",
            "text": GOOD["text"] + " 如果媽早上每天去喝多咖啡你的腸子乾燥不是懶惰",
        }
    )
    assert not r.ok and "Chinese characters" in r.reason


def test_blocks_mixed_clip_where_whisper_drops_the_chinese_shot():
    """The real 2026-10-22 failure: whisper said 'english' and simply omitted
    the Chinese-voiced hook, so only script coverage can catch it."""
    text = " ".join(SCRIPT[1:])
    r = _run({"language": "english", "text": text})
    assert not r.ok and "2/4" in r.reason


def test_fails_closed_without_a_script():
    r = _run(GOOD, scripts=[])
    assert not r.ok and "Voice script" in r.reason


def test_fails_closed_when_transcription_errors():
    def boom(_u):
        raise gate.LanguageGateError("no speech-to-text key set")

    r = gate.check_video_language("u", "row", "en", _children(SCRIPT), transcribe=boom)
    assert not r.ok and "speech-to-text" in r.reason


def test_non_english_ip_is_not_enforced():
    assert _run({"language": "chinese", "text": "你好"}, language="yue").ok


def test_gate_can_be_disabled(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setenv("PUBLISH_LANGUAGE_GATE", "off")
    assert _run({"language": "chinese", "text": "你好"}).ok


def test_planner_does_not_claim_a_blocked_row(monkeypatch: pytest.MonkeyPatch, tmp_path):
    from src import notion_publish as npub
    from tests import test_notion_publish as base

    monkeypatch.setenv("PUBLISH_LANGUAGE_GATE", "on")
    monkeypatch.setattr(npub, "_IDS_PATH", tmp_path / "ids.json")
    (tmp_path / "ids.json").write_text('{"prod_db": "db-1"}', encoding="utf-8")
    monkeypatch.setattr(npub, "_ncall", lambda m, p, body=None: base._pages()[p])
    monkeypatch.setattr(npub, "_children", lambda _id: _blocks(SCRIPT))
    monkeypatch.setattr(npub, "_query_all", lambda _db: [base._row()])
    monkeypatch.setattr(
        gate, "transcribe_video", lambda _u: {"language": "english", "text": " ".join(SCRIPT[1:])}
    )
    monkeypatch.setenv("NOTION_PUBLISH_GENERATE_COVERS", "0")
    result = npub.plan_publishes(
        state_path=tmp_path / "s.json",
        media_dir=tmp_path / "c",
        media_state_path=tmp_path / "m.json",
    )
    assert result["jobs"] == []
    assert any("LANGUAGE GATE" in w for w in result["warnings"])
    assert (
        not (tmp_path / "s.json").exists() or base.ROW_ID not in (tmp_path / "s.json").read_text()
    )
