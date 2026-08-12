"""Tests for notion_video.py's pure/dependency-free logic.

`_dreamina_duration()` is the piece that decides how many seconds of video
to REQUEST from 即梦 for a given shot's real voice-clip length. Everything
else in this module needs real ffmpeg/ffprobe/Notion/dreamina I/O and isn't
unit-tested here — consistent with the sibling test files in this folder
(test_add_karaoke_captions.py, test_pipeline_common.py), which only cover
the pure logic and leave I/O wrappers untested.

Root cause this guards against (found 2026-08-03 on the Bad Breath
campaign's CTA shot): the real voice clip for shot 4 was 4.435s long, but
the OLD duration calc used Python's `round()` — `round(4.435) == 4`, since
4.435 rounds to the NEAREST integer, not up. That requested only a 4s video
from 即梦, which rendered ~4.02s — shorter than the 4.435s the real voice
needed. concat()'s per-shot audio clamping (intentionally trims audio to
match ITS OWN shot's video length, documented in concat()'s own docstring)
then silently cut the real audio down to the video's ~4.0s, chopping the
sentence's tail off entirely. Confirmed via the shot's own Whisper
transcript (words.json): the word list ends at "...and breath." — the
script's actual last word, "reset", was never spoken in the final merged
video at all, not just mis-captioned.

`math.ceil()` instead of `round()` guarantees the requested duration is
never shorter than the real audio, closing this for any shot whose audio's
fractional-second part happens to be under .5 (round() rounds those down;
ceil() never does).

Run: cd studio && python3 -m pytest scripts/test_notion_video.py -q
"""
from __future__ import annotations

from notion_video import _dreamina_duration


def test_dreamina_duration_rounds_up_not_to_nearest():
    # The actual Bad Breath shot-4 regression: round(4.435) == 4 (wrong,
    # shorter than the real audio); ceil(4.435) == 5 (correct, has margin).
    assert _dreamina_duration(4.435) == 5


def test_dreamina_duration_exact_integer_is_unchanged():
    assert _dreamina_duration(5.0) == 5


def test_dreamina_duration_barely_over_an_integer_rounds_up():
    assert _dreamina_duration(7.02) == 8


def test_dreamina_duration_clamps_to_the_4s_floor():
    assert _dreamina_duration(1.2) == 4


def test_dreamina_duration_clamps_to_the_15s_ceiling():
    assert _dreamina_duration(20.5) == 15


def test_dreamina_duration_zero_falls_back_to_default():
    assert _dreamina_duration(0) == 5


def test_dreamina_duration_negative_falls_back_to_default():
    assert _dreamina_duration(-1) == 5


def test_dreamina_duration_custom_default_is_respected():
    assert _dreamina_duration(0, default=7) == 7


def test_dreamina_duration_sub_second_clip_clamps_to_floor_not_default():
    # Documents an intentional behavior change from the OLD code: the old
    # `round(_dur(aud)) or 5` fell back to the default for ANY audio whose
    # rounded value was 0 (i.e. 0 < audio_dur_s < 0.5), not just audio_dur_s
    # <= 0. ceil(0.3) == 1, clamped up to the 4s floor — still >= the real
    # 0.3s audio, so no truncation risk; just documenting the choice rather
    # than leaving it as an untested edge case.
    assert _dreamina_duration(0.3) == 4
