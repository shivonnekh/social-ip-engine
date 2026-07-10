"""notion_caption_render.py — karaoke-highlight caption chunking + rendering.

Ported from ``studio/scripts/add_karaoke_captions.py`` (the local content
factory's original tool, verified against real production output on
2026-07-08). This module closes the gap on the DEPLOYED (``src/``) side of
that same capability: the studio script is local, never-deployed content
tooling; this module is what ``notion_caption_gen.py``'s single-row
orchestrator calls from the live server process.

WHAT'S PORTED VERBATIM (no logic changes)
--------------------------------------------
- ``_ends_sentence`` / ``group_words`` — chunking. Breaks a caption group at
  ``MAX_WORDS_PER_CHUNK`` words, an early pause (> ``PAUSE_BREAK_S``), OR a
  sentence-terminal word (``.``/``!``/``?``) — the last rule fixes a real
  2026-07-08 production defect where two unrelated sentences merged into one
  caption chunk because the speaker didn't pause long enough between them.
- ``wrap_chunk_to_lines`` — width-balanced 2-line split (falls back to a
  greedy width-first multi-line wrap for a chunk no 2-line split can fit).
  Fixes two more 2026-07-08 defects: captions overflowing the frame edges,
  and a valid-but-lopsided 2-line split reading as visually disconnected.

Both were pinned down with real before/after inputs described in the
original file's comments — see ``tests/test_notion_caption_render.py`` for
those exact regression cases, now under pytest for the first time.

WHAT'S ADAPTED (I/O + font source only, same constants)
------------------------------------------------------------
``render()`` is the same moviepy compositing technique (every word rendered
TWICE — a white "base" copy visible for the whole chunk, a yellow
"highlight" copy visible only during that word's own [start, end] window),
with exactly the same tuned constants (``BASE_FONT_SIZE=74``,
``WORD_VERTICAL_PAD_RATIO=0.7``, ``LINE_GAP_PX=14``, etc. — see each
constant's own comment for the production incident it fixes). The ONLY
change is ``FONT_PATH``: Anton (OFL-licensed, bundled at
``src/assets/fonts/Anton-Regular.ttf``) instead of a hardcoded macOS system
font path (``/System/Library/Fonts/...`` doesn't exist on Render's Linux
container). Anton was empirically verified (real rendered frames, viewed by
a human) against the exact same torture-word set used to derive
``WORD_VERTICAL_PAD_RATIO`` originally — zero clipping, zero re-tuning
needed. Do not re-derive these constants; see the task history for the full
verification note.

WHY NOT UNIT-TEST render() ITSELF
------------------------------------
``render()`` does real moviepy/ffmpeg video I/O — there is no meaningful way
to unit-test video compositing without either (a) mocking moviepy's
internals so thoroughly the test would no longer catch a real regression,
or (b) doing real (slow) video I/O. This module instead: (1) fully unit
tests the pure logic ``render()`` depends on (``group_words``,
``wrap_chunk_to_lines``) — deterministic, dependency-free, and the part
most likely to silently misbehave without ever raising an exception to
notice by; and (2) has ONE integration-style smoke test that actually calls
``render()`` against a tiny real generated test video (a 1-2s
``ColorClip``, built with moviepy itself) and asserts the output file
exists and is a valid, non-empty video — a real regression net for "the
whole rendering pipeline is broken" (wrong font path, moviepy API drift,
etc.) without asserting on pixel content. This mirrors how this repo
already treats ``scripts/persona_dry_run.py``-style manual/integration
verification as a NECESSARY complement to unit tests, not a replacement.
"""

from __future__ import annotations

from collections.abc import Callable
from pathlib import Path
from typing import Any

FONT_PATH = str(Path(__file__).resolve().parent / "assets" / "fonts" / "Anton-Regular.ttf")

# ----------------------------------------------------------------- style
# Tuned to match the approved reference (see module docstring). All pixel
# values below are for a 1080px-WIDE canvas and scaled proportionally to
# whatever the actual video's width turns out to be (render() computes
# `scale = frame_w / BASE_CANVAS_WIDTH`).
BASE_CANVAS_WIDTH = 1080
BASE_FONT_SIZE = 74
BASE_STROKE_WIDTH = 5
HIGHLIGHT_COLOR = "yellow"
BASE_COLOR = "white"
STROKE_COLOR = "black"
LINE_GAP_PX = 14  # normal typographic leading for this font size, once glyphs render whole
# (see WORD_VERTICAL_PAD_RATIO below) — do not re-bump without a fresh screenshot review.
SPACE_WIDTH_RATIO = 0.32          # inter-word gap, as a fraction of font_size
BOTTOM_MARGIN_RATIO = 480 / 1920  # matches the reference's MarginV=480 on a 1920-tall canvas

# Fixes a real bug found via human screenshot review: a tight auto-sized
# TextClip canvas truncates deep descenders ('y', 'p', 'g') flush against
# the clip's own bottom edge, INSIDE that single word's rendered bitmap,
# before it's ever composited onto the video. 0.7 (~34px at font_size=49)
# was swept against every distinct word in the reference campaign PLUS a
# torture set of deep-descender words ("zygotically", "pygmy", "flying",
# "Sipping") — nothing clips at this margin.
WORD_VERTICAL_PAD_RATIO = 0.7
SIDE_MARGIN_BASE = 60             # matches the reference's MarginL/MarginR=60 on a 1080-wide canvas

# ----------------------------------------------------------------- chunking
# 5 words/chunk keeps every sampled chunk in the reference campaign to a
# clean 2 lines at this font size (a 6-7 word chunk routinely couldn't fit
# in 2 lines once wrap_chunk_to_lines() started actually checking pixel
# width instead of blindly forcing 2 lines).
MAX_WORDS_PER_CHUNK = 5
PAUSE_BREAK_S = 0.5  # a gap bigger than this ends a chunk early, even under MAX_WORDS_PER_CHUNK

_SENTENCE_END_CHARS = (".", "!", "?")


def _ends_sentence(word: str) -> bool:
    """Whether `word` (as transcribed, punctuation intact) ends a sentence.

    Used to force a caption chunk break even when word-count and pause-gap
    thresholds haven't been hit — see group_words() docstring.
    """
    return word.rstrip().endswith(_SENTENCE_END_CHARS)


def group_words(words: list[dict[str, Any]]) -> list[list[dict[str, Any]]]:
    """Split the flat word list into caption chunks: at most
    MAX_WORDS_PER_CHUNK words, breaking EARLY if the gap to the next word
    exceeds PAUSE_BREAK_S (a natural breath/pause is a better break point
    than an arbitrary word count landing mid-breath) OR if the current word
    ends a sentence (a real production defect: two unrelated sentences got
    merged into one 5-word chunk purely because word count hadn't hit the
    cap yet and the speaker didn't pause long enough between them).
    Sentence-end detection is deliberately eager (any word ending in
    . ! ?) — an occasional false break on an abbreviation just costs one
    extra (still-correct) cue boundary, whereas missing a real sentence
    end merges two unrelated thoughts into one cue, which is the actual
    reported defect."""
    chunks: list[list[dict[str, Any]]] = []
    current: list[dict[str, Any]] = []
    for i, word in enumerate(words):
        current.append(word)
        at_max = len(current) >= MAX_WORDS_PER_CHUNK
        is_last = i == len(words) - 1
        next_gap_too_big = (
            not is_last and (words[i + 1]["start"] - word["end"]) > PAUSE_BREAK_S
        )
        sentence_ended = _ends_sentence(word["word"])
        if at_max or next_gap_too_big or sentence_ended or is_last:
            chunks.append(current)
            current = []
    return [c for c in chunks if c]


def wrap_chunk_to_lines(
    chunk: list[dict[str, Any]],
    word_width: Callable[[str], int],
    space_width: int,
    max_width: int,
) -> list[list[dict[str, Any]]]:
    """Wrap a caption chunk across lines WITHOUT letting any line's
    rendered pixel width exceed ``max_width`` — fixes a real production
    incident where captions were cut off at the frame edges. A previous
    word-count-only implementation always split a chunk exactly in half by
    WORD COUNT with zero awareness of how wide those words actually render
    (a chunk with a few long words could overflow the frame even though it
    "fit" by count alone).

    Strategy: among every 2-line split point where BOTH resulting lines
    fit ``max_width``, pick the one whose two lines are the most similar
    in rendered WIDTH (ties broken by proximity to the ceil(n/2) word-count
    bias point, so a chunk of equal-width words still splits exactly like
    the old fixed-bias code did). Picking by word-count bias alone could
    still produce a valid-but-lopsided split — both lines fit within
    max_width, but one is visually much wider than the other, so the two
    lines read as disconnected rather than one centered block (each line is
    independently centered at render time, so minimizing the width gap
    between lines is what actually keeps the block looking cohesive). If no
    2-line split fits at all (a genuinely too-wide chunk), fall back to a
    greedy width-first wrap that uses as many lines as it takes — this only
    triggers for pathological inputs; any chunk that fits in 2 lines takes
    the branch above.
    """
    def line_width(words: list[dict[str, Any]]) -> int:
        if not words:
            return 0
        return sum(word_width(w["word"]) for w in words) + space_width * (len(words) - 1)

    if len(chunk) <= 1:
        return [list(chunk)] if chunk else []

    n = len(chunk)
    bias = -(-n // 2)  # ceil(n/2) — tiebreak anchor, matching the old fixed split
    candidates: list[tuple[int, int, list[dict[str, Any]], list[dict[str, Any]]]] = []
    for k in range(1, n):
        line1, line2 = chunk[:k], chunk[k:]
        w1, w2 = line_width(line1), line_width(line2)
        if w1 <= max_width and w2 <= max_width:
            candidates.append((abs(w1 - w2), abs(k - bias), line1, line2))
    if candidates:
        candidates.sort(key=lambda c: (c[0], c[1]))
        _, _, line1, line2 = candidates[0]
        return [line1, line2]

    # Fallback: no 2-line split fits — greedy width-first wrap instead.
    lines: list[list[dict[str, Any]]] = []
    current: list[dict[str, Any]] = []
    for word in chunk:
        candidate = [*current, word]
        if current and line_width(candidate) > max_width:
            lines.append(current)
            current = [word]
        else:
            current = candidate
    if current:
        lines.append(current)
    return lines


def render(video_path: Path, chunks: list[list[dict[str, Any]]], out_path: Path) -> None:
    """Composite the karaoke caption layer over `video_path` and write
    `out_path`. See module docstring for the white-base + yellow-highlight
    double-render technique. Real moviepy/ffmpeg I/O — not unit-tested
    directly, see module docstring for the integration-smoke-test
    complement instead."""
    from moviepy import CompositeVideoClip, TextClip, VideoFileClip

    video = VideoFileClip(str(video_path))
    frame_w, frame_h = video.size
    scale = frame_w / BASE_CANVAS_WIDTH
    font_size = round(BASE_FONT_SIZE * scale)
    stroke_width = max(1, round(BASE_STROKE_WIDTH * scale))
    space_width = round(font_size * SPACE_WIDTH_RATIO)
    bottom_margin = round(BOTTOM_MARGIN_RATIO * frame_h)
    side_margin = round(SIDE_MARGIN_BASE * scale)
    max_line_width = frame_w - 2 * side_margin

    # Vertical-only padding (see WORD_VERTICAL_PAD_RATIO docstring above) —
    # deliberately NO horizontal margin, so word_width()/space_width/x
    # positioning below are completely unaffected by this fix; only the
    # vertical descender-clipping bug needed a canvas-size change.
    word_vertical_pad = round(font_size * WORD_VERTICAL_PAD_RATIO)

    def make_word_clip(text: str, color: str) -> TextClip:
        return TextClip(
            font=FONT_PATH, text=text, font_size=font_size, color=color,
            stroke_color=STROKE_COLOR, stroke_width=stroke_width,
            margin=(0, word_vertical_pad),
        )

    # Reference glyph with both an ascender and a descender ("A" + "g") —
    # gives a stable line height so line spacing never jitters word-to-word
    # depending on which individual letters happen to have descenders.
    # IMPORTANT: measured WITHOUT word_vertical_pad — that padding exists
    # purely so a single word's own glyph doesn't get clipped by ITS OWN
    # clip's tight canvas edge (see WORD_VERTICAL_PAD_RATIO docstring). Word
    # clips (built by make_word_clip, still padded) are individually
    # shifted up by word_vertical_pad at positioning time below so their
    # VISIBLE glyphs still land flush with this unpadded line_height's
    # baseline grid.
    line_height = make_word_clip("Ag", BASE_COLOR).size[1] - 2 * word_vertical_pad

    size_cache: dict[str, tuple[int, int]] = {}

    def word_width(word_text: str) -> int:
        if word_text not in size_cache:
            size_cache[word_text] = make_word_clip(word_text, BASE_COLOR).size
        return size_cache[word_text][0]

    overlay_clips = []

    for chunk in chunks:
        lines = wrap_chunk_to_lines(chunk, word_width, space_width, max_line_width)
        chunk_start = chunk[0]["start"]
        chunk_dur = max(0.01, chunk[-1]["end"] - chunk_start)

        # Stack however many lines this chunk needed, anchored to the SAME
        # bottom margin every chunk uses — the last line always lands at
        # `frame_h - bottom_margin - line_height` regardless of whether
        # this chunk rendered as 1, 2, or (rare fallback) 3+ lines, so the
        # caption block's bottom edge never jitters chunk-to-chunk.
        line_ys: list[float] = []
        y = frame_h - bottom_margin - line_height
        for _ in lines:
            line_ys.append(y)
            y -= line_height + LINE_GAP_PX
        line_ys.reverse()

        for line_words, line_y in zip(lines, line_ys, strict=True):
            if not line_words:
                continue
            widths = [word_width(w["word"]) for w in line_words]
            total_width = sum(widths) + space_width * (len(line_words) - 1)
            x = (frame_w - total_width) / 2

            # Each word clip carries word_vertical_pad of invisible padding
            # ABOVE its own glyphs (see make_word_clip) — shift the whole
            # padded clip up by that amount so the VISIBLE glyph still lands
            # at line_y (the position line_ys was computed for), instead of
            # the glyph appearing word_vertical_pad lower than intended.
            glyph_y = line_y - word_vertical_pad

            for word, width in zip(line_words, widths, strict=True):
                base_clip = (
                    make_word_clip(word["word"], BASE_COLOR)
                    .with_start(chunk_start).with_duration(chunk_dur)
                    .with_position((x, glyph_y))
                )
                highlight_clip = (
                    make_word_clip(word["word"], HIGHLIGHT_COLOR)
                    .with_start(word["start"])
                    .with_duration(max(0.01, word["end"] - word["start"]))
                    .with_position((x, glyph_y))
                )
                overlay_clips.append(base_clip)
                overlay_clips.append(highlight_clip)
                x += width + space_width

    final = CompositeVideoClip([video, *overlay_clips])
    final.write_videofile(
        str(out_path), codec="libx264", audio_codec="aac", fps=video.fps or 30, logger=None,
    )
    video.close()
    final.close()
