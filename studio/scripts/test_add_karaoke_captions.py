"""Tests for add_karaoke_captions.py's pure caption-chunking logic.

group_words() and wrap_chunk_to_lines() are tested here — they're the
deterministic, dependency-free core (no Whisper model, no moviepy render,
no Notion I/O), and the part most likely to silently misbehave (e.g. a
chunk breaking mid-breath, or a line overflowing the frame) without ever
raising an exception to notice by. render()/transcribe()/upload aren't
unit-tested here — they're thin wrappers around Whisper/moviepy/Notion
I/O, consistent with the rest of studio/scripts/ (no test suite exists for
the sibling notion_*.py tools either — this folder is local, never-
deployed content tooling, not the live bot in ../../src/).

wrap_chunk_to_lines() replaced wrap_two_lines() on 2026-07-08 — the old
function split every chunk exactly in half by WORD COUNT with zero
awareness of how wide those words actually render, which let a chunk with
a few long words overflow past the frame edges (the exact defect behind
that day's production incident: captions cut off mid-word on a live
Reel). The new function is width-aware: it only accepts a 2-line split if
BOTH lines fit within max_width, and falls back to a greedy width-first
wrap (however many lines it takes) for the rare chunk that can't fit any
2-line split at all.

Run: cd studio && python3 -m pytest scripts/test_add_karaoke_captions.py -q
"""
from __future__ import annotations

from add_karaoke_captions import align_to_known_script, group_words, wrap_chunk_to_lines


def _word(text: str, start: float, end: float) -> dict:
    return {"word": text, "start": start, "end": end}


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


def test_group_words_empty_input():
    assert group_words([]) == []


def test_group_words_never_drops_a_word():
    words = [_word(f"w{i}", i * 0.5, i * 0.5 + 0.2) for i in range(23)]
    chunks = group_words(words)
    flattened = [w for chunk in chunks for w in chunk]
    assert flattened == words


def _len_width(word_text: str) -> int:
    """Deterministic fake pixel-width function for tests: 1 unit per char."""
    return len(word_text)


def _flatten(lines: list[list[dict]]) -> list[dict]:
    return [w for line in lines for w in line]


def test_wrap_matches_old_ceil_half_split_when_it_already_fits():
    # Short, equal-length words at a generous max_width -> behaves exactly
    # like the old always-ceil(n/2) split, since that split already fits.
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
    """Real production defect (2026-07-08, human-reported via screenshot):
    "Treating them the / same is" — both lines fit comfortably within
    max_width, but the word-count-bias split (3+2, matching ceil(5/2))
    makes line 1 visually much wider than line 2, so the two lines read as
    a disconnected long-line-over-short-stub instead of one cohesive
    centered block (each line is independently centered at render time).
    A DIFFERENT split (2+3) is also valid and far more width-balanced —
    the function must prefer it, not just take the first bias-adjacent
    split that happens to fit.
    """
    words = ["Treating", "them", "the", "same", "is"]  # lengths: 8,4,3,4,2
    chunk = [_word(w, i, i + 0.5) for i, w in enumerate(words)]
    lines = wrap_chunk_to_lines(chunk, _len_width, space_width=1, max_width=30)
    assert [w["word"] for w in lines[0]] == ["Treating", "them"]
    assert [w["word"] for w in lines[1]] == ["the", "same", "is"]
    assert _flatten(lines) == chunk


def test_wrap_shifts_split_point_to_keep_both_lines_within_max_width():
    """The exact defect behind the 2026-07-08 overflow incident: the old
    fixed ceil(n/2) split put a long word onto a line that then overflowed
    the frame. The new function must pick a DIFFERENT split point instead
    of forcing the biased one when it doesn't fit.

    "longword" (8 chars) sits at the START of a 6-word chunk. The old
    biased ceil(6/2)=3 split bundles it with 2 short words on line 1
    (width 14) — too wide for max_width=11 below. Shifting the split to
    k=2 instead (longword + 1 short word on line 1, the remaining 4 short
    words on line 2) is the only split where BOTH lines fit.
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


# ---------------------------------------------------- align_to_known_script


def test_align_corrects_a_single_mishearing_same_word_count():
    """The exact real-world defect this function exists to fix: Whisper
    heard 'cramps' as 'crampus' in the reference campaign."""
    words = [
        _word("If", 0.0, 0.28), _word("you", 0.28, 0.4), _word("get", 0.4, 0.58),
        _word("period", 0.58, 0.94), _word("crampus", 0.94, 1.48),
    ]
    corrected = align_to_known_script(words, "If you get period cramps")
    assert [w["word"] for w in corrected] == ["If", "you", "get", "period", "cramps"]
    # Timestamps must be UNTOUCHED — only the displayed word changes.
    assert corrected[4]["start"] == 0.94
    assert corrected[4]["end"] == 1.48


def test_align_leaves_words_unchanged_when_script_matches_exactly():
    words = [_word("Hello", 0.0, 0.3), _word("world", 0.3, 0.6)]
    corrected = align_to_known_script(words, "Hello world")
    assert corrected == words


def test_align_is_case_and_punctuation_insensitive_for_matching():
    words = [_word("hello,", 0.0, 0.3), _word("WORLD", 0.3, 0.6)]
    corrected = align_to_known_script(words, "Hello world")
    # Matches despite case/punctuation differences -> takes the script's spelling
    assert [w["word"] for w in corrected] == ["Hello", "world"]


def test_align_leaves_an_inserted_or_deleted_span_as_whisper_heard_it():
    """A word count MISMATCH (Whisper heard an extra word the script
    doesn't have) must NOT be guessed at — safer to keep what was heard."""
    words = [_word("If", 0.0, 0.2), _word("um", 0.2, 0.3), _word("you", 0.3, 0.5)]
    corrected = align_to_known_script(words, "If you")
    # 'um' has no script counterpart -> left as Whisper heard it, not dropped
    assert "um" in [w["word"] for w in corrected]
    assert len(corrected) == len(words)


def test_align_never_changes_the_word_count():
    words = [_word(f"w{i}", i, i + 0.5) for i in range(5)]
    corrected = align_to_known_script(words, "totally different script text here now")
    assert len(corrected) == len(words)
