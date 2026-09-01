#!/usr/bin/env python3
"""Merge a row's already-generated shot videos into final.mp4 — WITHOUT the
audio swap.

Why this exists rather than `notion_video.py --merge-only`
----------------------------------------------------------
`--merge-only` runs `replace_shot_audio()`, splicing the original MiniMax voice
clip over Jimeng's render. That was reversed on 2026-08-11 (see studio/CLAUDE.md):
`_dreamina_duration()` rounds the requested clip length UP, Jimeng fills the extra
time by SLOWING its own speech, and pasting the naturally-paced audio back on top
desyncs the whole clip against the lips — not just the tail. Confirmed audibly on
two campaigns.

So the correct merge is a plain concat of each shot's raw multimodal2video output,
exactly what the direct generation path does. That path only runs when it has just
generated every shot, which is no use after a targeted single-shot repair — hence
this script.

Typical repair loop for a shot that lost the Jimeng hang-lottery all 3 attempts:

    # 1. (optional) soften the posture in that shot's 🖼️ Image prompt in Notion,
    #    then re-render the still:
    python3 scripts/notion_image.py --row <id> --shot 3 --force
    # 2. retry just that shot's video:
    python3 scripts/notion_video.py --row <id> --shot 3
    # 3. merge locally, no audio swap:
    python3 scripts/repair_and_merge.py --row <id>
    # 4. captions + upload:
    python3 scripts/add_karaoke_captions.py --row <id> --script vo.txt --upload

Refuses to merge if any shot is missing — a silently short final.mp4 is worse
than no final.mp4, which is the same stance notion_video takes.
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

import notion_video as nv  # noqa: E402


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--row", required=True)
    ap.add_argument("--expect", type=int, default=None,
                    help="expected shot count (default: inferred from the row)")
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    # Reuse notion_video's own resolvers rather than reimplementing the campaign
    # path layout — a second copy of that logic would drift the first time a slug
    # rule changes, and point this at an empty directory.
    vdir = nv._campaign_workdir(args.row) / "video"
    expected = args.expect or len(nv.read_row_shots(args.row))
    mp4s, missing = [], []
    for i in range(1, expected + 1):
        p = Path(vdir) / f"shot{i}.mp4"
        (mp4s if p.exists() else missing).append(str(p) if p.exists() else i)

    if missing:
        raise SystemExit(
            f"❌ refusing to merge — shot(s) {missing} have no local video.\n"
            "   Generate them first (notion_video.py --row <id> --shot N).\n"
            "   Merging around a gap produces a short final.mp4 that looks fine."
        )

    final = str(Path(vdir) / "final.mp4")
    print(f"merging {len(mp4s)} shots (no audio swap) -> {final}")
    for m in mp4s:
        print(f"  {Path(m).name}")
    if args.dry_run:
        return 0

    nv.concat(mp4s, final)
    nv.strip_ai_watermark(final)

    # A fresh merge invalidates any cached Whisper transcript sitting next to the
    # video — otherwise add_karaoke_captions would caption the PREVIOUS cut.
    words = Path(vdir) / "words.json"
    if words.exists():
        words.unlink()
        print("  cleared stale words.json")

    print(f"✅ {final}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
