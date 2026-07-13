#!/usr/bin/env python3
"""One-time (but safely re-runnable) cleanup: collapse every shot's video
toggles down to exactly ONE per shot, across the whole Production Tracker.

Root cause this fixes: `place_video_in_shot()` used to APPEND a new "🎬 Video
(regen)" toggle every time a shot was regenerated, rather than replacing
content in place — a heavily-iterated shot could accumulate 3-4 video
toggles, and every reader (dashboard, merge) needed a "newest created_time
wins" tie-break to know which one was current. That was fragile — a NEW
reader once trusted document order instead and silently served a STALE
video (found live 2026-07-13). `place_video_in_shot()` has been rewritten to
never create duplicates going forward; this script cleans up what already
accumulated before that fix.

For each shot: keep the toggle whose video has the newest created_time,
normalize its label to "🎬 Video here", delete every other video toggle (and
their video blocks) for that shot. Idempotent — a shot already down to one
toggle is left untouched (reported as "already 1").

Usage:
  python3 scripts/consolidate_video_toggles.py --dry-run   # preview only
  python3 scripts/consolidate_video_toggles.py             # apply to all rows
  python3 scripts/consolidate_video_toggles.py --row <id>  # one row only
"""
from __future__ import annotations

import argparse
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import notion_image as ni  # noqa: E402  (ncall/_children/_txt helpers)
import notion_video as nv  # noqa: E402  (ncall_w)
import pipeline_common as pc  # noqa: E402


def consolidate_row(row_id: str, dry_run: bool) -> tuple[int, int]:
    """Returns (shots_consolidated, shots_already_one) for one row."""
    consolidated = already_one = 0
    cur_shot: str | None = None
    # shot_title -> list of (toggle_id, video_created_time_or_None)
    shots: dict[str, list[tuple[str, str]]] = {}

    for b in ni._children(row_id):
        t, tx = b["type"], ni._txt(b)
        if t == "heading_3":
            cur_shot = tx if tx.lower().startswith("shot") else None
            if cur_shot:
                shots.setdefault(cur_shot, [])
        elif cur_shot and t == "toggle" and ("Video here" in tx or "Video (regen)" in tx):
            video_created = ""
            if b.get("has_children"):
                for k in ni._children(b["id"]):
                    if k["type"] == "video":
                        video_created = k.get("created_time", "")
                        break
            shots[cur_shot].append((b["id"], video_created))

    for shot_title, toggles in shots.items():
        if len(toggles) <= 1:
            already_one += 1
            continue
        # newest video wins (empty-video toggles sort last — never preferred over a real video)
        toggles_sorted = sorted(toggles, key=lambda t: t[1], reverse=True)
        keep_id, _ = toggles_sorted[0]
        extras = [tid for tid, _ in toggles_sorted[1:]]
        print(f"    {shot_title}: {len(toggles)} toggles -> keeping 1 (deleting {len(extras)})")
        if dry_run:
            consolidated += 1
            continue
        try:
            nv.ncall_w("PATCH", f"/blocks/{keep_id}",
                       {"toggle": {"rich_text": [{"type": "text", "text": {"content": "🎬 Video here"}}]}})
        except Exception as exc:  # noqa: BLE001 - cosmetic only
            print(f"      ⚠️  couldn't normalize label: {exc}")
        for extra_id in extras:
            try:
                nv.ncall_w("DELETE", f"/blocks/{extra_id}")
            except Exception as exc:  # noqa: BLE001 - a stale block must not abort the whole row
                print(f"      ⚠️  couldn't delete {extra_id}: {exc}")
            time.sleep(0.3)
        consolidated += 1
    return consolidated, already_one


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--row", help="only this Production row page id")
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    if args.row:
        rows = [{"id": args.row}]
    else:
        rows = pc._query_all(pc._load_notion_ids()["prod_db"])

    total_c = total_o = 0
    for r in rows:
        row_id = r["id"]
        name = pc._title_of(ni.ncall("GET", f"/pages/{row_id}")) if "properties" not in r else pc._title_of(r)
        print(f"▶ {name}")
        c, o = consolidate_row(row_id, args.dry_run)
        total_c += c
        total_o += o
    verb = "would consolidate" if args.dry_run else "consolidated"
    print(f"\ndone: {verb} {total_c} shot(s), {total_o} already had exactly 1 toggle")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
