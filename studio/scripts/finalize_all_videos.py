#!/usr/bin/env python3
"""finalize_all_videos.py — pipeline Stage 3: burn karaoke captions onto
every Production row's final.mp4 under a Content concept, and upload each
result to Notion's "Production Video" property.

Run this AFTER you've reviewed each row's final.mp4 from
generate_all_videos.py. For each row, this is exactly
`add_karaoke_captions.py --row <id> --upload` — see that script's module
docstring for how the captioning works and why "Production Video" (a page
PROPERTY, not a body block) is the field that matters: it's what
social-ip-engine's live Reels auto-publish reads from.

After this step, each row is ONE Stage-flip away from actually going live
on Instagram — that flip is deliberately NEVER done by any script in this
pipeline. You decide when, in Notion, yourself.

Usage:
  python3 scripts/finalize_all_videos.py --content "Detox"
  python3 scripts/finalize_all_videos.py --content-id <page_id>
  python3 scripts/finalize_all_videos.py --row <production_row_id>
  python3 scripts/finalize_all_videos.py --content "Detox" --script path/to/known_script.txt
"""
from __future__ import annotations

import argparse

import pipeline_common as pc


def main() -> int:
    ap = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    pc.add_row_selection_args(ap)
    ap.add_argument(
        "--script",
        help="Path to a text file with the KNOWN correct VO script (applied to EVERY row — "
             "only makes sense with --row, since each row's script differs). See "
             "add_karaoke_captions.py::align_to_known_script().",
    )
    args = ap.parse_args()

    rows = pc.resolve_rows(args)
    print(f"[finalize] {len(rows)} row(s) to process")

    results: list[tuple[str, str, bool]] = []
    for row in rows:
        row_id = row["id"]
        name = pc._title_of(row)
        print(f"\n[finalize] row: {name} ({row_id})")

        cmd = ["python3", "add_karaoke_captions.py", "--row", row_id, "--upload"]
        if args.script:
            cmd += ["--script", args.script]
        ok = pc.run_step(cmd, "captions + upload")
        results.append((name, "captions + upload", ok))

    all_ok = pc.print_batch_summary(results)
    print("\nNext: review each row's captioned video in Notion, "
          "then flip Stage to 🟢 Ready to Publish / ✅ Published yourself when ready.")
    return 0 if all_ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
