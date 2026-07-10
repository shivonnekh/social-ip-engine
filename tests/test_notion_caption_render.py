"""Tests for src/notion_caption_render.py — karaoke caption chunking +
rendering, ported from studio/scripts/add_karaoke_captions.py.

group_words() and wrap_chunk_to_lines() are pure, dependency-free logic —
fully unit tested here (this is the first time this logic gets pytest
coverage under this repo's TDD requirements; the original studio/ copy only
had ad-hoc scripts/test_add_karaoke_captions.py, run manually via
`cd studio && python3 -m pytest`, never wired into this repo's CI-style
`pytest -q` run). Two cases are pinned as explicit regressions using the
exact before/after inputs described in the original file's own comments:
the two-sentence-merge bug and the lopsided-2-line-split bug.

render() itself does real moviepy/ffmpeg video I/O — not unit-testable in
the traditional sense (see module docstring for why). One integration-style
smoke test builds a tiny real video with moviepy's own ColorClip and asserts
render() produces a valid, non-empty output video.
"""

from __future__ import annotations

from pathlib import Path

from src.notion_caption_render import (
    FONT_PATH,
    _ends_sentence,
    group_words,
    render,
    wrap_chunk_to_lines,
)


def _word(text: str, start: float, end: float) -> dict:
    return {"word": text, "start": start, "end": end}


# ------------------------------------------------------------- _ends_sentence


def test_ends_sentence_true_for_period_exclaim_question():
    assert _ends_sentence("stop.") is True
    assert _ends_sentence("really!") is True
    assert _ends_sentence("why?") is True


def test_ends_sentence_false_for_comma_or_bare_word():
    assert _ends_sentence("ease,") is False
    assert _ends_sentence("hello") is False


# ----------------------------------------------------------------- group_words


def test_group_words_caps_at_max_words_per_chunk():
    # 10 words, no pauses at all -> must split 5 + 5 (MAX_WORDS_PER_CHUNK=5)
    words = [_word(f"w{i}", i * 0.2, i * 0.2 + 0.15) for i in range(10)]
    chunks = group_words(words)
    assert [len(c) for c in chunks] == [5, 5]


def test_group_words_breaks_early_on_a_long_pause():
    words = [
        _word("If", 0.0, 0.28), _word("you", 0.28, 0.4), _word("get", 0.4, 0.58),
        # long pause here (> PAUSE_BREAK_S) must break the chunk early
        _word("Western", 2.0, 2.3), _word("doctors", 2.3, 2.6),
    ]
    chunks = group_words(words)
    assert len(chunks) == 2
    assert [w["word"] for w in chunks[0]] == ["If", "you", "get"]
    assert [w["word"] for w in chunks[1]] == ["Western", "doctors"]


def test_group_words_single_word_input():
    words = [_word("Hi", 0.0, 0.3)]
    assert group_words(words) == [[_word("Hi", 0.0, 0.3)]]


def test_group_words_breaks_on_sentence_end_even_under_max_words():
    """Regression, pinned from the original file's own comments (2026-07-08
    production defect): "stops them, listen." and the very next, unrelated
    sentence "Western doctors will not tell you this" got merged into one
    5-word caption chunk, purely because word count hadn't hit
    MAX_WORDS_PER_CHUNK yet and the speaker didn't pause long enough between
    them for the pause-gap rule to catch it. A word ending in
    sentence-terminal punctuation (. ! ?) must end its chunk immediately,
    regardless of word count or pause length."""
    words = [
        _word("stops", 2.9, 3.1), _word("them,", 3.1, 3.3),
        _word("listen.", 3.3, 3.6),  # sentence ends here — only 3 words in
        # no long pause to the next word — the pre-fix code would keep grouping
        _word("Western", 3.65, 3.9), _word("doctors", 3.9, 4.2),
    ]
    chunks = group_words(words)
    assert len(chunks) == 2
    assert [w["word"] for w in chunks[0]] == ["stops", "them,", "listen."]
    assert [w["word"] for w in chunks[1]] == ["Western", "doctors"]


def test_group_words_does_not_break_on_mid_sentence_comma():
    """A comma is not a sentence end — must not trigger an early break
    (only . ! ? do)."""
    words = [
        _word("Cold", 0.0, 0.2), _word("Stagnation:", 0.2, 0.5),
        _word("cramps", 0.5, 0.7), _word("that", 0.7, 0.85),
        _word("ease,", 0.85, 1.0), _word("with", 1.0, 1.15),
        _word("heat.", 1.15, 1.4),
    ]
    chunks = group_words(words)
    # MAX_WORDS_PER_CHUNK=5 still caps the first chunk; the comma inside it
    # ("ease,") must NOT have forced an earlier break.
    assert [len(c) for c in chunks] == [5, 2]


def test_group_words_empty_input():
    assert group_words([]) == []


def test_group_words_never_drops_a_word():
    words = [_word(f"w{i}", i * 0.5, i * 0.5 + 0.2) for i in range(23)]
    chunks = group_words(words)
    flattened = [w for chunk in chunks for w in chunk]
    assert flattened == words


# ------------------------------------------------------------- wrap_chunk_to_lines


def _len_width(word_text: str) -> int:
    """Deterministic fake pixel-width function for tests: 1 unit per char."""
    return len(word_text)


def _flatten(lines: list[list[dict]]) -> list[dict]:
    return [w for line in lines for w in line]


def test_wrap_matches_old_ceil_half_split_when_it_already_fits():
    chunk = [_word(f"w{i}", i, i + 0.5) for i in range(7)]  # all 2 chars wide
    lines = wrap_chunk_to_lines(chunk, _len_width, space_width=1, max_width=100)
    assert len(lines) == 2
    assert len(lines[0]) == 4
    assert len(lines[1]) == 3
    assert _flatten(lines) == chunk


def test_wrap_even_count_splits_evenly_when_it_fits():
    chunk = [_word(f"w{i}", i, i + 0.5) for i in range(6)]
    lines = wrap_chunk_to_lines(chunk, _len_width, space_width=1, max_width=100)
    assert len(lines) == 2
    assert len(lines[0]) == 3
    assert len(lines[1]) == 3


def test_wrap_single_word_goes_on_its_own_line():
    chunk = [_word("Hi", 0.0, 0.3)]
    lines = wrap_chunk_to_lines(chunk, _len_width, space_width=1, max_width=100)
    assert lines == [chunk]


def test_wrap_empty_chunk_returns_empty_list():
    assert wrap_chunk_to_lines([], _len_width, space_width=1, max_width=100) == []


def test_wrap_prefers_balanced_width_over_bias_when_both_fit():
    """Regression, pinned from the original file's own comments (2026-07-08,
    human-reported via screenshot): "Treating them the / same is" — both
    lines fit comfortably within max_width, but the word-count-bias split
    (3+2, matching ceil(5/2)) makes line 1 visually much wider than line 2,
    so the two lines read as a disconnected long-line-over-short-stub
    instead of one cohesive centered block (each line is independently
    centered at render time). A DIFFERENT split (2+3) is also valid and far
    more width-balanced — the function must prefer it, not just take the
    first bias-adjacent split that happens to fit."""
    words = ["Treating", "them", "the", "same", "is"]  # lengths: 8,4,3,4,2
    chunk = [_word(w, i, i + 0.5) for i, w in enumerate(words)]
    lines = wrap_chunk_to_lines(chunk, _len_width, space_width=1, max_width=30)
    assert [w["word"] for w in lines[0]] == ["Treating", "them"]
    assert [w["word"] for w in lines[1]] == ["the", "same", "is"]
    assert _flatten(lines) == chunk


def test_wrap_shifts_split_point_to_keep_both_lines_within_max_width():
    """Regression, pinned from the original file's own comments — the exact
    defect behind the 2026-07-08 overflow incident: the old fixed ceil(n/2)
    split put a long word onto a line that then overflowed the frame. The
    function must pick a DIFFERENT split point instead of forcing the biased
    one when it doesn't fit.

    "longword" (8 chars) sits at the START of a 6-word chunk. The old biased
    ceil(6/2)=3 split bundles it with 2 short words on line 1 (width 14) —
    too wide for max_width=11 below. Shifting the split to k=2 instead
    (longword + 1 short word on line 1, the remaining 4 short words on line
    2) is the only split where BOTH lines fit.
    """
    words = ["longword", "ab", "ab", "ab", "ab", "ab"]  # lengths: 8,2,2,2,2,2
    chunk = [_word(w, i, i + 0.5) for i, w in enumerate(words)]
    lines = wrap_chunk_to_lines(chunk, _len_width, space_width=1, max_width=11)
    assert len(lines) == 2
    assert [w["word"] for w in lines[0]] == ["longword", "ab"]
    assert [w["word"] for w in lines[1]] == ["ab", "ab", "ab", "ab"]
    for line in lines:
        widths = [_len_width(w["word"]) for w in line]
        total = sum(widths) + 1 * max(0, len(line) - 1)
        assert total <= 11, f"line overflowed: {[w['word'] for w in line]} = {total}px"
    assert _flatten(lines) == chunk


def test_wrap_falls_back_to_more_than_two_lines_when_no_2_line_split_fits():
    words = ["mediumword", "mediumword", "mediumword"]  # each 10 chars
    chunk = [_word(w, i, i + 0.5) for i, w in enumerate(words)]
    # At max_width=15, no 2-line split can fit (10+1+10=21 either way) —
    # must fall back to one line per word rather than silently overflowing.
    lines = wrap_chunk_to_lines(chunk, _len_width, space_width=1, max_width=15)
    assert len(lines) == 3
    for line in lines:
        widths = [_len_width(w["word"]) for w in line]
        total = sum(widths) + 1 * max(0, len(line) - 1)
        assert total <= 15
    assert _flatten(lines) == chunk


def test_wrap_never_drops_or_reorders_words_regardless_of_width():
    chunk = [_word(f"word{i}", i, i + 0.5) for i in range(9)]
    lines = wrap_chunk_to_lines(chunk, _len_width, space_width=1, max_width=8)
    assert _flatten(lines) == chunk


# ------------------------------------------------------------------------ FONT_PATH


def test_font_path_resolves_to_bundled_anton_font_and_exists():
    """The task's central constraint: FONT_PATH must resolve to
    src/assets/fonts/Anton-Regular.ttf relative to THIS module's own
    location, and that file must actually be present on disk (already
    downloaded + empirically verified, per the task history — this test
    just pins the wiring, not the font choice itself)."""
    resolved = Path(FONT_PATH)
    assert resolved.name == "Anton-Regular.ttf"
    assert resolved.parent.name == "fonts"
    assert resolved.exists()


# ------------------------------------------------------------------- render() smoke


def test_render_produces_a_valid_non_empty_video(tmp_path: Path):
    """Integration-style smoke test — NOT a pixel-content assertion. Builds
    a tiny real 2-second background video with moviepy's own ColorClip (same
    technique used for the original manual font torture-test), runs a
    couple of fake word-timing chunks through the real render() pipeline,
    and asserts the output file exists, is non-empty, and is a valid,
    openable video with positive duration. This is a real regression net —
    it would have caught "the font path is wrong" or "the whole rendering
    pipeline is broken" — without trying to assert on visual pixel content."""
    from moviepy import ColorClip

    video_path = tmp_path / "bg.mp4"
    out_path = tmp_path / "captioned.mp4"

    bg = ColorClip(size=(320, 568), color=(20, 20, 20), duration=2.0).with_fps(24)
    bg.write_videofile(str(video_path), codec="libx264", audio=False, logger=None)
    bg.close()

    chunks = [
        [
            {"word": "Hello", "start": 0.0, "end": 0.4},
            {"word": "there", "start": 0.4, "end": 0.8},
        ],
        [
            {"word": "world", "start": 1.0, "end": 1.4},
        ],
    ]

    render(video_path, chunks, out_path)

    assert out_path.exists()
    assert out_path.stat().st_size > 0

    from moviepy import VideoFileClip

    produced = VideoFileClip(str(out_path))
    try:
        assert produced.duration > 0
    finally:
        produced.close()
