#!/usr/bin/env python3
"""add_karaoke_captions.py — burn word-level karaoke-highlight captions onto
a Production row's merged final.mp4, and (optionally) upload the result back
to Notion as the row's "Production Video" property.

WHY THIS EXISTS
---------------
`notion_video.py` already merges every shot into
`campaigns/<content>/<ip>/video/final.mp4` (ffmpeg concat, its own last
step — see its module docstring). This script is the NEXT stage: burn
karaoke-style word-by-word highlighted captions on top of that merged
video, then (optionally) push the result to the "Production Video" Notion
property — the EXACT property social-ip-engine's live Reels auto-publish
reads from (see ../../src/notion_publish.py::_extract_video_url). Before
this script existed, both steps (captioning + uploading the final cut)
were done ad hoc, one-off, in-conversation — with no reusable script, which
is why it kept going wrong (JianYing drafts failing to open, etc).

WHY MOVIEPY, NOT FFMPEG's ass/subtitles/drawtext FILTERS
-----------------------------------------------------------
This machine's ffmpeg build has no libass/freetype support (confirmed via
`ffmpeg -filters` showing neither `subtitles` nor `drawtext` — a minimal
Homebrew bottle). moviepy (already installed, 2.1.x) renders text via
Pillow internally and only shells out to ffmpeg for encoding/muxing, so it
works regardless of this ffmpeg build's filter set.

HOW THE KARAOKE LOOK WORKS
---------------------------
Words are grouped into ~6-7 word caption chunks, breaking EARLY on any
>0.5s pause so groups land on natural breath boundaries rather than an
arbitrary word count (see group_words()). Each chunk is wrapped onto 2
lines (ceil(n/2) words on line 1, matching the visual reference below).

Every word in a chunk is rendered TWICE, stacked at the exact same (x, y):
  - a WHITE copy, visible for the chunk's FULL duration (the "base" line)
  - a YELLOW copy, visible ONLY during that word's own [start, end] window
The yellow copy sits on top of the white one, so a viewer just sees the
current word "light up" while the rest of the line stays white. This
composition (not ffmpeg's ASS karaoke tags, which this ffmpeg build can't
render) is what reproduces the exact look approved in
studio/campaigns/period-pain-emergency-do-this-now/jackie-chan-en/video/
karaoke_captions.ass (2026-07-07) — kept there purely as a style/session
artifact, this script does not read it.

Usage:
  cd studio/  (loads studio/.env, same as every other scripts/ tool)
  python3 scripts/add_karaoke_captions.py --row <production_page_id>
  python3 scripts/add_karaoke_captions.py --row <id> --upload
  python3 scripts/add_karaoke_captions.py --video path/to/final.mp4 --out path/to/final_karaoke.mp4
"""
from __future__ import annotations

import argparse
import difflib
import json
import re
import sys
from collections.abc import Callable
from pathlib import Path
from typing import Any

# Reuse ncall_w / _campaign_workdir / upload_to_notion — same convention
# already used by append_material.py, fill_script_property.py, etc.
import notion_video as nv

ROOT = Path(__file__).resolve().parent.parent

# ----------------------------------------------------------------- style
# Tuned to match the approved reference (karaoke_captions.ass): Arial
# Black, white base / yellow highlight, black stroke, captions sitting in
# the lower-third. All pixel values below are for a 1080px-WIDE canvas and
# scaled proportionally to whatever the actual video's width turns out to
# be (render() computes `scale = frame_w / BASE_CANVAS_WIDTH`).
FONT_PATH = "/System/Library/Fonts/Supplemental/Arial Black.ttf"
BASE_CANVAS_WIDTH = 1080
BASE_FONT_SIZE = 74
BASE_STROKE_WIDTH = 5
HIGHLIGHT_COLOR = "yellow"
BASE_COLOR = "white"
STROKE_COLOR = "black"
LINE_GAP_PX = 14  # reverted to the original value on 2026-07-08 — chased this up to
# 70 chasing a "lines look touching" complaint that was actually caused by a SEPARATE
# bug (see WORD_VERTICAL_PAD_RATIO below: individual glyphs were being clipped by
# MoviePy's tight per-word canvas, which made normal spacing look cramped). Once that
# clipping bug was fixed, 70px read as excessive/unnatural gap on real human review —
# 14px (normal typographic leading for this font size) is correct once glyphs render
# whole. Do not re-bump this without a fresh screenshot review — this exact value has
# already round-tripped 14 -> 26 -> 46 -> 70 -> 14 in one session chasing the wrong cause.
SPACE_WIDTH_RATIO = 0.32          # inter-word gap, as a fraction of font_size
BOTTOM_MARGIN_RATIO = 480 / 1920  # matches the reference's MarginV=480 on a 1920-tall canvas

# Fixes a REAL bug (2026-07-08, found via a human screenshot of "period
# crampus" cut off mid-letter — this is a DIFFERENT bug than the LINE_GAP_PX
# history above, which was about line-to-line spacing, not this): MoviePy's
# TextClip auto-sizes its own canvas too tightly for this font (Arial
# Black) — descenders get truncated flush against the clip's own bottom
# edge, INSIDE that single word's rendered bitmap, before it's ever
# composited onto the video.
#
# 0.33 (≈16px at font_size=49) was the FIRST fix and was NOT enough — a
# later human screenshot caught "every" still clipped mid-"y" in production.
# Root cause of the under-fix: the initial test sweep only checked words
# with a 'p' descender ("period", "crampus"), which happens to be
# shallower in this font than 'y' (confirmed by direct pixel measurement:
# at margin=16px, "every"/"your"/"yoga"/"gypsy"/"cramps" all still had ink
# touching the clip's bottom edge — i.e. still clipped — while "period"
# alone happened to clear at that margin, hiding the bug). Swept margin
# 16→36px against every distinct word actually used in this campaign PLUS
# a torture set of deep-descender words ("zygotically", "pygmy", "yyy",
# "flying", "Sipping") — nothing clips at 32px; 0.7 (≈34px at font_size=49)
# is used here for a small safety buffer beyond that confirmed threshold.
WORD_VERTICAL_PAD_RATIO = 0.7
SIDE_MARGIN_BASE = 60             # matches the reference's MarginL/MarginR=60 on a 1080-wide canvas

# ----------------------------------------------------------------- chunking
# Lowered from 7 to 5 on 2026-07-08: at this font size (Arial Black, scaled
# from a 74px/1080px-canvas base) a 6-7 word chunk routinely couldn't fit
# in the intended 2 lines within max_line_width once wrap_chunk_to_lines()
# started actually checking pixel width instead of blindly forcing 2 lines
# — it correctly fell back to 3 stacked lines instead of overflowing, but
# 3 lines pushed up far enough to overlap the subject's chin/mouth on
# several sampled frames of the Period Pain video. 5 words/chunk keeps
# every sampled chunk in that video to a clean 2 lines; see
# scripts/memory/shello.md for the before/after frame comparison.
MAX_WORDS_PER_CHUNK = 5
PAUSE_BREAK_S = 0.5  # a gap bigger than this ends a chunk early, even under MAX_WORDS_PER_CHUNK


def transcribe(video_path: Path, model_name: str = "base.en") -> list[dict[str, Any]]:
    """Word-level transcription via local openai-whisper. Returns a FLAT
    list of {"word", "start", "end"} across the whole video — Whisper's own
    segment boundaries are discarded here; display chunking is entirely
    owned by group_words() below, driven by our own pause/word-count rules
    rather than Whisper's sentence segmentation."""
    import whisper  # local import — loading the model is slow, only pay the cost if this runs

    model = whisper.load_model(model_name)
    result = model.transcribe(str(video_path), word_timestamps=True, verbose=False)
    words: list[dict[str, Any]] = []
    for seg in result["segments"]:
        for w in seg.get("words", []):
            words.append({
                "word": str(w["word"]).strip(),
                "start": round(float(w["start"]), 3),
                "end": round(float(w["end"]), 3),
            })
    return words


def _normalize_word(word: str) -> str:
    return re.sub(r"[^a-z0-9']", "", word.lower())


def align_to_known_script(words: list[dict[str, Any]], script_text: str) -> list[dict[str, Any]]:
    """Swap in the KNOWN correct script's spelling wherever Whisper's word
    list and the real script line up, while keeping Whisper's timestamps —
    Whisper's own transcription is timing-accurate but not always
    spelling-accurate (confirmed empirically: it heard "cramps" as
    "crampus" in the reference campaign — the exact defect this function
    exists to fix). Only "equal" and same-length "replace" opcodes from
    difflib are corrected; any span where Whisper and the script disagree
    on WORD COUNT (an insertion/deletion) is left as Whisper's own words —
    guessing which word was skipped/added is riskier than just displaying
    what was actually heard."""
    script_words = script_text.split()
    whisper_norm = [_normalize_word(w["word"]) for w in words]
    script_norm = [_normalize_word(w) for w in script_words]

    aligned = [dict(w) for w in words]
    matcher = difflib.SequenceMatcher(a=whisper_norm, b=script_norm, autojunk=False)
    for tag, i1, i2, j1, j2 in matcher.get_opcodes():
        if tag in ("equal", "replace") and (i2 - i1) == (j2 - j1):
            for offset in range(i2 - i1):
                aligned[i1 + offset]["word"] = script_words[j1 + offset]
        # 'insert' / 'delete' / uneven 'replace' spans: leave Whisper's word.
    return aligned


def group_words(words: list[dict[str, Any]]) -> list[list[dict[str, Any]]]:
    """Split the flat word list into caption chunks: at most
    MAX_WORDS_PER_CHUNK words, breaking EARLY if the gap to the next word
    exceeds PAUSE_BREAK_S — a natural breath/pause is a better break point
    than an arbitrary word count landing mid-breath."""
    chunks: list[list[dict[str, Any]]] = []
    current: list[dict[str, Any]] = []
    for i, word in enumerate(words):
        current.append(word)
        at_max = len(current) >= MAX_WORDS_PER_CHUNK
        is_last = i == len(words) - 1
        next_gap_too_big = (
            not is_last and (words[i + 1]["start"] - word["end"]) > PAUSE_BREAK_S
        )
        if at_max or next_gap_too_big or is_last:
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
    rendered pixel width exceed ``max_width`` — fixes the 2026-07-08
    production incident where captions were cut off at the frame edges.
    The previous implementation (``wrap_two_lines``, word-count only)
    always split a chunk exactly in half by WORD COUNT with zero awareness
    of how wide those words actually render — a chunk with a few long
    words (e.g. "actually", "stops") could overflow the frame even though
    it "fit" by count alone.

    Strategy: among every 2-line split point where BOTH resulting lines
    fit ``max_width``, pick the one whose two lines are the most similar
    in rendered WIDTH (ties broken by proximity to the ceil(n/2) word-count
    bias point, so a chunk of equal-width words still splits exactly like
    the old fixed-bias code did). Picking by word-count bias alone (the
    2026-07-08 first version of this function) could still produce a
    valid-but-lopsided split — e.g. "Treating them the / same is": both
    lines fit within max_width, but line 1 is visually much wider than
    line 2, so the two lines read as disconnected rather than one centered
    block (reported by human review the same day, on real output). Since
    each line is independently centered at render time, minimizing the
    width gap between lines is what actually keeps the block looking
    cohesive. If no 2-line split fits at all (a genuinely too-wide chunk),
    fall back to a greedy width-first wrap that uses as many lines as it
    takes — this only triggers for pathological inputs; any chunk that
    fits in 2 lines takes the branch above.
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
    double-render technique."""
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
    # IMPORTANT: this must be measured WITHOUT word_vertical_pad — that
    # padding exists purely so a single word's own glyph doesn't get
    # clipped by ITS OWN clip's tight canvas edge (see WORD_VERTICAL_PAD_RATIO
    # docstring). It is invisible (transparent) padding, not visible line
    # height. Using the PADDED clip's size here was a real bug (found
    # 2026-07-08 via human review): every line-to-line gap silently grew by
    # 2×word_vertical_pad on top of the intended LINE_GAP_PX, since padded
    # line_height is used TWICE in the stacking math below — once as each
    # line's own height, once as the step to the next line — making 14px of
    # intended gap read as ~46px of actual visible whitespace. Word clips
    # (built by make_word_clip, still padded) are individually shifted up by
    # word_vertical_pad at positioning time below so their VISIBLE glyphs
    # still land flush with this unpadded line_height's baseline grid.
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


def upload_final_video_property(row_id: str, mp4_path: Path) -> None:
    """Upload `mp4_path` and set it as the row's "Production Video" page
    PROPERTY (a Files & media property) — distinct from `notion_video.py`'s
    `place_video_in_shot`, which only ever appends a video BLOCK to the
    page body. social-ip-engine's live-publish pipeline reads the PROPERTY,
    not any body block (see src/notion_publish.py::_extract_video_url)."""
    file_id = nv.upload_to_notion(str(mp4_path), "video/mp4", mp4_path.name)
    file_ref = {"type": "file_upload", "file_upload": {"id": file_id}, "name": mp4_path.name}
    nv.ncall_w("PATCH", f"/pages/{row_id}", {
        "properties": {"Production Video": {"files": [file_ref]}}
    })


def main() -> int:
    ap = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    ap.add_argument(
        "--row",
        help="Production Tracker page id — resolves campaigns/<content>/<ip>/video/final.mp4, "
             "and (with --upload) the row to write the result back to",
    )
    ap.add_argument(
        "--video",
        help="Explicit path to the merged video (overrides --row's default final.mp4 location)",
    )
    ap.add_argument(
        "--out",
        help="Output path for the captioned video (default: <video's dir>/final_karaoke.mp4)",
    )
    ap.add_argument("--model", default="base.en", help="Whisper model name (default: base.en)")
    ap.add_argument(
        "--retranscribe", action="store_true",
        help="Ignore any cached words.json next to the video and re-run Whisper",
    )
    ap.add_argument(
        "--script",
        help="Path to a text file with the KNOWN correct VO script — corrects Whisper "
             "mishearings (e.g. 'cramps' heard as 'crampus') while keeping Whisper's "
             "timestamps; see align_to_known_script()",
    )
    ap.add_argument(
        "--upload", action="store_true",
        help="Upload the result to the row's 'Production Video' property (requires --row)",
    )
    args = ap.parse_args()

    if not args.row and not args.video:
        sys.exit("[error] pass --row or --video")
    if args.upload and not args.row:
        sys.exit("[error] --upload requires --row (need a page id to write back to)")

    if args.video:
        video_path = Path(args.video).resolve()
    else:
        video_path = nv._campaign_workdir(args.row) / "video" / "final.mp4"

    if not video_path.exists():
        sys.exit(f"[error] {video_path} not found — run notion_video.py --row {args.row} first")

    out_path = Path(args.out).resolve() if args.out else video_path.with_name("final_karaoke.mp4")
    words_cache_path = video_path.with_name("words.json")

    if words_cache_path.exists() and not args.retranscribe:
        print(f"🗂️  reusing cached transcript -> {words_cache_path}")
        words = json.loads(words_cache_path.read_text(encoding="utf-8"))
    else:
        print(f"🎙️  transcribing {video_path.name} (whisper {args.model}) ...")
        words = transcribe(video_path, args.model)
        words_cache_path.write_text(json.dumps(words, indent=1), encoding="utf-8")
    print(f"   {len(words)} words")

    if args.script:
        script_text = Path(args.script).read_text(encoding="utf-8")
        words = align_to_known_script(words, script_text)
        print(f"   corrected against known script ({args.script})")

    chunks = group_words(words)
    print(f"🎬 building {len(chunks)} caption groups + rendering ...")
    render(video_path, chunks, out_path)
    print(f"✅ {out_path}")

    if args.upload:
        print("⬆️  uploading to Notion 'Production Video' property ...")
        upload_final_video_property(args.row, out_path)
        print("✅ uploaded")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
