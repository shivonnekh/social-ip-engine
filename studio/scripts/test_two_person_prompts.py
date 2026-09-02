"""Tests for the [TWO_PERSON] shot mode in notion_prompts.

Why this mode exists
--------------------
`build_prompt(talking=True)` hardcoded "exactly ONE person in frame, alone …
NEVER … adding a second person", because a doctor+patient frame was believed to
hang 即梦's multimodal2video. That belief was DISPROVEN on 2026-09-02: a
standing-doctor + seated-patient two shot lip-synced correctly on the first
attempt in ~160s, with the patient's mouth staying shut.

What actually makes it work is telling 即梦 WHO speaks. So the video prompt must
carry a 【Second person】block naming the non-speaker and forbidding lip
animation on them — without it the model cannot tell which face owns the audio.

The marker is explicit rather than inferred from the word "patient": the Hua Tuo
series already uses "patient" in solo shot guides, so inferring would silently
flip those to two-person framing.

Run: cd studio && python3 -m pytest scripts/test_two_person_prompts.py -q
"""
from __future__ import annotations

from notion_prompts import TWO_PERSON_MARKER, build_jimeng_prompt, build_prompt

PERSONA = "Steady elderly male, slight Chinese accent"
SOLO = "Medium close-up of Jackie in a warm clinic explaining to camera"
DUO = (f"{TWO_PERSON_MARKER} Medium-wide two shot, the patient sits on a stool at frame "
       "left while Jackie stands at her right, both faces near-frontal")


def test_solo_talking_shot_still_demands_exactly_one_person():
    """The single-person guard must survive for every normal shot."""
    out = build_prompt(PERSONA, SOLO, talking=True)
    assert "exactly ONE person" in out
    assert TWO_PERSON_MARKER not in out


def test_two_person_shot_drops_the_single_person_guard():
    out = build_prompt(PERSONA, DUO, talking=True)
    assert "exactly ONE person" not in out, "the solo guard would forbid the patient"
    assert "TWO people" in out


def test_marker_is_stripped_from_every_prompt_it_touches():
    """The marker is an authoring instruction, never image/video description."""
    img = build_prompt(PERSONA, DUO, talking=True)
    vid = build_jimeng_prompt("Shot 1 · ~10s · Hook", DUO, lang="英文", dialogue="Hello there.")
    assert TWO_PERSON_MARKER not in img
    assert TWO_PERSON_MARKER not in vid


def test_two_person_video_prompt_names_who_speaks_and_who_does_not():
    """The whole reason two-person lip-sync works: 即梦 must be told which face
    owns the audio, and that the other must not be animated."""
    vid = build_jimeng_prompt("Shot 1 · ~10s · Hook", DUO, lang="英文", dialogue="Hello there.")
    assert "【Second person】" in vid
    low = vid.lower()
    assert "only speaker" in low or "only one speaking" in low
    assert "mouth stays closed" in low
    assert "do not animate" in low


def test_solo_video_prompt_has_no_second_person_block():
    vid = build_jimeng_prompt("Shot 1 · ~10s · Hook", SOLO, lang="英文", dialogue="Hello there.")
    assert "【Second person】" not in vid


def test_two_person_still_keeps_the_no_subtitle_contract():
    """Whatever else changes, the textless-plate instruction must survive —
    it is what keeps 即梦 from burning its own captions in."""
    vid = build_jimeng_prompt("Shot 1 · ~10s · Hook", DUO, lang="英文", dialogue="Hello.")
    assert "NO subtitles" in vid
    assert "字幕" in vid
