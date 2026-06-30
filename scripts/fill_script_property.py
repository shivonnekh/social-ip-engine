#!/usr/bin/env python3
"""
fill_script_property.py — populate the Production Tracker "Script" property from
each row's own body (the per-shot 🗣️ Voice script code blocks).

The Script property = ONE LINE PER SHOT, in the row's IP language (already correct
in the body — Jackie = EN, Jessica = 粤语). This just lifts the body voice lines
into the property so it's visible/usable at a glance.

SAFETY: only writes rows whose Script is currently empty, unless --force.

Usage:
  python3 scripts/fill_script_property.py            # fill empty Script props
  python3 scripts/fill_script_property.py --force    # overwrite all
  python3 scripts/fill_script_property.py --dry       # preview only
"""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
import notion_video as nv

PROD_DB = "389f2a3f-4320-817b-9363-f09b0c4b04b2"


def _title(row: dict) -> str:
    return "".join(
        t["plain_text"] for p in row["properties"].values()
        if p["type"] == "title" for t in p["title"]
    )


def _current_script(row: dict) -> str:
    rt = row["properties"].get("Script", {}).get("rich_text", [])
    return "".join(t["plain_text"] for t in rt)


def _query_all(db: str) -> list:
    rows, cur = [], None
    while True:
        body = {"page_size": 100}
        if cur:
            body["start_cursor"] = cur
        d = nv.ncall_w("POST", f"/databases/{db}/query", body)
        rows += d["results"]
        if d.get("has_more"):
            cur = d["next_cursor"]
        else:
            return rows


def _voice_lines_from_body(page_id: str) -> list[str]:
    """Per shot, grab the code block that follows a '🗣️ Voice script' paragraph."""
    lines: list[str] = []
    expect = False
    for b in nv._children(page_id):
        t, tx = b["type"], nv._txt(b)
        if t == "paragraph" and "Voice script" in tx:
            expect = True
        elif expect and t == "code":
            # collapse any internal newlines/extra spaces → single clean line
            line = re.sub(r"\s+", " ", tx).strip()
            if line:
                lines.append(line)
            expect = False
    return lines


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--force", action="store_true", help="overwrite non-empty Script too")
    ap.add_argument("--dry", action="store_true")
    args = ap.parse_args()

    rows = _query_all(PROD_DB)
    written = skipped = empty_src = 0

    for r in rows:
        title = _title(r)
        if _current_script(r).strip() and not args.force:
            skipped += 1
            continue

        lines = _voice_lines_from_body(r["id"])
        if not lines:
            print(f"  ⚠️ no voice scripts in body: {title}")
            empty_src += 1
            continue

        script = "\n".join(lines)
        if args.dry:
            print(f"\n=== {title} ({len(lines)} shots) ===")
            for ln in lines:
                print(f"   | {ln[:80]}")
            written += 1
            continue

        nv.ncall_w("PATCH", f"/pages/{r['id']}", {
            "properties": {"Script": {"rich_text": [
                {"type": "text", "text": {"content": script[:2000]}}
            ]}}
        })
        print(f"  ✅ {len(lines)} shots → Script: {title}")
        written += 1

    print(f"\nwritten={written} skipped(filled)={skipped} no_source={empty_src}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
