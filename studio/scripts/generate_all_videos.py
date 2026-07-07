#!/usr/bin/env python3
"""generate_all_videos.py — pipeline Stage 2: generate (and merge) the
video for every Production row under a Content concept.

Run this AFTER you've reviewed the image + voice generate_assets.py
produced. For each row, this is exactly `notion_video.py --row <id>` —
per-shot 即梦 video-gen, then ffmpeg concat into that row's final.mp4 (see
notion_video.py's own module docstring — merging already happens
automatically there, no separate manual step).

Deliberately does NOT continue on to captioning — that's
finalize_all_videos.py, run only after YOU review each row's final.mp4.

Usage:
  python3 scripts/generate_all_videos.py --content "Detox"
  python3 scripts/generate_all_videos.py --content-id <page_id>
  python3 scripts/generate_all_videos.py --row <production_row_id>
"""
from __future__ import annotations

import argparse

import pipeline_common as pc


def main() -> int:
    ap = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    pc.add_row_selection_args(ap)
    args = ap.parse_args()

    rows = pc.resolve_rows(args)
    print(f"[video] {len(rows)} row(s) to process")

    results: list[tuple[str, str, bool]] = []
    for row in rows:
        row_id = row["id"]
        name = pc._title_of(row)
        print(f"\n[video] row: {name} ({row_id})")

        ok = pc.run_step(["python3", "notion_video.py", "--row", row_id], "video")
        results.append((name, "video", ok))

    all_ok = pc.print_batch_summary(results)
    print("\nNext: review each row's final.mp4 in Notion, "
          "then run finalize_all_videos.py for this content.")
    return 0 if all_ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
