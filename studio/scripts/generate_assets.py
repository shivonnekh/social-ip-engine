#!/usr/bin/env python3
"""generate_assets.py — pipeline Stage 1: fan out a Content concept to
every active IP, then auto-generate image + voice for every resulting
Production row.

Run this AFTER you've reviewed the Content Library Script and it's
approved. Replaces manually running notion_fanout.py, then
notion_image.py, then batch_voice_gen.py, once per IP, by hand — see
pipeline_common.py's module docstring for why this subprocess-invokes the
existing tools rather than reimplementing them.

Deliberately does NOT continue on to video generation — that's
generate_all_videos.py, run only after YOU review the image + voice this
step produces. Automating the chaining was the point; automating away the
review checkpoints was not (image/voice quality issues are real and
documented — see studio/CLAUDE.md's 即梦/dreamina gotchas — catching them
here is cheaper than catching them after video-gen has already spent
money on a broken shot).

Usage:
  python3 scripts/generate_assets.py --content "Detox"
  python3 scripts/generate_assets.py --content-id <page_id>
  python3 scripts/generate_assets.py --row <production_row_id>   # single row, skip fan-out
  python3 scripts/generate_assets.py --content "Detox" --all-ips
"""
from __future__ import annotations

import argparse
import sys

import notion_video as nv
import pipeline_common as pc


def main() -> int:
    ap = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    grp = ap.add_mutually_exclusive_group(required=True)
    grp.add_argument("--content", help="Content Library concept name (substring match)")
    grp.add_argument("--content-id", help="Explicit Content Library page id")
    grp.add_argument("--row", help="Skip fan-out — generate assets for ONE existing Production row")
    ap.add_argument(
        "--all-ips", action="store_true",
        help="Fan out to inactive IPs too (passed through to notion_fanout.py)",
    )
    args = ap.parse_args()

    if args.row:
        rows = [nv.ncall(f"/pages/{args.row}")]
    else:
        content_id, content_name = pc.find_content(args.content, args.content_id)
        print(f"[assets] concept: {content_name}")

        fanout_cmd = ["python3", "notion_fanout.py", "--content-id", content_id]
        if args.all_ips:
            fanout_cmd.append("--all-ips")
        pc.run_step(fanout_cmd, "fan-out")

        rows = pc.production_rows_for_content(content_id)
        if not rows:
            sys.exit("[error] no Production rows found for this content even after fan-out")

    print(f"[assets] {len(rows)} row(s) to process")

    results: list[tuple[str, str, bool]] = []
    for row in rows:
        row_id = row["id"]
        name = pc._title_of(row)
        print(f"\n[assets] row: {name} ({row_id})")

        ok_img = pc.run_step(["python3", "notion_image.py", "--row", row_id], "image")
        results.append((name, "image", ok_img))

        ok_voice = pc.run_step(["python3", "batch_voice_gen.py", "--row", row_id], "voice")
        results.append((name, "voice", ok_voice))

    all_ok = pc.print_batch_summary(results)
    print("\nNext: review the image + voice for each row above in Notion, "
          "then run generate_all_videos.py for this content.")
    return 0 if all_ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
