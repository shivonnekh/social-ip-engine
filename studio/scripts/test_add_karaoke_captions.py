"""Tests for add_karaoke_captions.py's pure caption-chunking logic.

Only group_words() and wrap_two_lines() are tested here — they're the
deterministic, dependency-free core (no Whisper model, no moviepy render,
no Notion I/O), and the part most likely to silently misbehave (e.g. a
chunk breaking mid-breath, or an off-by-one in the 2-line split) without
ever raising an exception to notice by. render()/transcribe()/upload
aren't unit-tested here — they're thin wrappers around Whisper/moviepy/
Notion I/O, consistent with the rest of studio/scripts/ (no test suite
exists for the sibling notion_*.py tools either — this folder is local,
never-deployed content tooling, not the live bot in ../../src/).

Run: cd studio && python3 -m pytest scripts/test_add_karaoke_captions.py -q
"""
from __future__ import annotations

from add_karaoke_captions import align_to_known_script, group_words, wrap_two_lines


def _word(text: str, start: float, end: float) -> dict:
    return {"word": text, "start": start, "end": end}


def test_group_words_caps_at_max_words_per_chunk():
    # 10 words, no pauses at all -> must split 7 + 3 (MAX_WORDS_PER_CHUNK=7)
    words = [_word(f"w{i}", i * 0.2, i * 0.2 + 0.15) for i in range(10)]
    chunks = group_words(words)
    assert [len(c) for c in chunks] == [7, 3]


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


def test_wrap_two_lines_odd_count_gives_line1_the_extra_word():
    chunk = [_word(f"w{i}", i, i + 0.5) for i in range(7)]
    line1, line2 = wrap_two_lines(chunk)
    assert len(line1) == 4
    assert len(line2) == 3
    assert line1 + line2 == chunk


def test_wrap_two_lines_even_count_splits_evenly():
    chunk = [_word(f"w{i}", i, i + 0.5) for i in range(6)]
    line1, line2 = wrap_two_lines(chunk)
    assert len(line1) == 3
    assert len(line2) == 3


def test_wrap_two_lines_single_word_goes_on_line_one():
    chunk = [_word("Hi", 0.0, 0.3)]
    line1, line2 = wrap_two_lines(chunk)
    assert line1 == chunk
    assert line2 == []


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
