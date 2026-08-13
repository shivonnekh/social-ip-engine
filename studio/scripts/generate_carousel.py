#!/usr/bin/env python3
"""generate_carousel.py — pipeline stage: ensure the 🎠 Carousel Panels
section exists on every Production row under a Content concept (idempotent
— `notion_fanout.py` already calls this at row-creation time, this step
covers rows created before a concept grew a Carousel Guide, or before this
feature existed), then generate every panel's image.

Independent of generate_assets.py / generate_all_videos.py /
finalize_all_videos.py on purpose — see docs/carousel-format-plan.md
(D7): a carousel is reviewed on its own schedule, not the Reel's, and
folding this into generate_assets.py would spend gpt-image-2 credits on
every concept including ones with no Carousel Guide at all. Rows whose
linked concept has no Carousel Guide are reported as skipped (not
failed) — most concepts are video-only, that's expected, not an error.

Usage:
  python3 scripts/generate_carousel.py --content "Detox"
  python3 scripts/generate_carousel.py --content-id <page_id>
  python3 scripts/generate_carousel.py --row <production_row_id>
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import pipeline_common as pc  # noqa: E402
from notion_carousel_prompts import apply_carousel_plan  # noqa: E402


def main() -> int:
    ap = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    pc.add_row_selection_args(ap)
    args = ap.parse_args()

    rows = pc.resolve_rows(args)
    print(f"[carousel] {len(rows)} row(s) to check")

    results: list[tuple[str, str, bool]] = []
    skipped: list[str] = []
    for row in rows:
        row_id = row["id"]
        name = pc._title_of(row)

        plan_status = apply_carousel_plan(row_id)
        if plan_status == "no-carousel-guide":
            skipped.append(name)
            continue
        if plan_status == "no-content":
            print(f"\n[carousel] row: {name} ({row_id}) — ⚠️  no linked Content concept, skipping")
            skipped.append(name)
            continue

        print(f"\n[carousel] row: {name} ({row_id}) — plan: {plan_status}")
        ok = pc.run_step(["python3", "notion_carousel_image.py", "--row", row_id], "carousel")
        results.append((name, "carousel", ok))

    if skipped:
        print(f"\n[carousel] {len(skipped)} row(s) skipped — no Carousel Guide on the linked concept "
              f"(expected for video-only content): {', '.join(skipped)}")

    if not results:
        print("\n[carousel] nothing to generate — no row in this batch has a Carousel Guide")
        return 0

    all_ok = pc.print_batch_summary(results)
    print("\nNext: review each row's 🎠 Carousel Panels filmstrip in Notion, "
          "then flip 🎠 Carousel Stage to publish.")
    return 0 if all_ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
