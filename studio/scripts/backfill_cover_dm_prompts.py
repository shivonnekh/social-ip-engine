#!/usr/bin/env python3
"""Backfill 🖼️ Cover Photo + 📊 DM Infographic prompt sections onto existing
Production Tracker rows — APPEND-ONLY (never wipes media, unlike a rebuild).

Per row:
  - 🖼️ Cover Photo section (prompt + empty "🖼️ Cover here" toggle) if missing
  - 📊 DM Infographic prompt code block (from the linked Content page's
    Infographic Brief) if missing — the already-uploaded infographic image
    toggle is left untouched.

Idempotent: rows that already have a section are skipped.

Usage:
    python3 scripts/backfill_cover_dm_prompts.py --dry-run
    python3 scripts/backfill_cover_dm_prompts.py                # all rows
    python3 scripts/backfill_cover_dm_prompts.py --ip Jackie    # one IP
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import time
from pathlib import Path

_ENV = Path(__file__).resolve().parent.parent / ".env"
if _ENV.exists():
    for _line in _ENV.read_text(encoding="utf-8").splitlines():
        _line = _line.strip()
        if _line and not _line.startswith("#") and "=" in _line:
            _k, _, _v = _line.partition("=")
            os.environ.setdefault(_k.strip(), _v.strip())

sys.path.insert(0, str(Path(__file__).resolve().parent))
from notion_prompts import (  # noqa: E402
    NO_BRIEF_PLACEHOLDER,
    _all_children,
    _page_title,
    _primary_beat,
    _relation_id,
    _txt,
    call,
    cover_blocks,
    dm_blocks,
    fetch_infographic_brief,
    ip_persona,
    parse_storyboard,
)

IDS_PATH = Path(__file__).resolve().parent / "notion_ids.json"


def row_flags(row_id: str) -> tuple[bool, bool, list[str]]:
    """Return (has_cover_section, has_real_infographic_prompt, stale_block_ids).

    A placeholder infographic prompt does NOT count as satisfied — its blocks
    are returned as stale so the row self-heals once the Content page gains a
    real Infographic Brief."""
    has_cover = has_info = False
    stale: list[str] = []
    expect_info_code = False
    info_label_id: str | None = None
    for b in _all_children(row_id):
        tx = _txt(b)
        if b["type"] in ("heading_3", "paragraph") and "Cover Photo" in tx:
            has_cover = True
        if "Infographic prompt" in tx:
            expect_info_code = True
            info_label_id = b["id"]
            continue
        if expect_info_code and b["type"] == "code":
            if tx.strip() == NO_BRIEF_PLACEHOLDER:
                stale += [info_label_id, b["id"]]  # placeholder — replace later
            else:
                has_info = True
            expect_info_code = False
    return has_cover, has_info, stale


def backfill_row(row_id: str, title: str, dry_run: bool) -> str:
    has_cover, has_info, stale = row_flags(row_id)
    if has_cover and has_info:
        return "complete — skip"

    page = call("GET", f"/pages/{row_id}")
    concept_id = _relation_id(page, "Content")
    ip_id = _relation_id(page, "IP")
    if not concept_id:
        return "no Content relation — skip"

    persona = ip_persona(ip_id)[1] if ip_id else "TCM doctor"
    concept_title = _page_title(call("GET", f"/pages/{concept_id}"))
    shots = parse_storyboard(concept_id)
    hook_visual = _primary_beat(shots[0]["visual"]) if shots else ""
    brief = fetch_infographic_brief(concept_id)

    if stale and not brief:
        return "placeholder still unresolved — Content page has no brief yet"

    blocks: list[dict] = []
    label: list[str] = []
    if not has_cover:
        blocks += cover_blocks(persona, concept_title, hook_visual)
        label.append("cover")
    if not has_info:
        blocks += dm_blocks(brief)
        label.append("infographic-prompt" + ("" if brief else " (NO BRIEF on Content page)"))
    if dry_run:
        return f"would add: {', '.join(label)}"

    for bid in stale:                  # remove placeholder blocks before re-adding
        if bid:
            call("DELETE", f"/blocks/{bid}")
    for i in range(0, len(blocks), 25):
        call("PATCH", f"/blocks/{row_id}/children", {"children": blocks[i:i + 25]})
    time.sleep(0.3)
    return f"added: {', '.join(label)}"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--ip", help="substring match on row title (e.g. Jackie)")
    args = ap.parse_args()

    ids = json.loads(IDS_PATH.read_text())
    rows, cursor = [], None
    while True:
        body: dict = {"page_size": 100}
        if cursor:
            body["start_cursor"] = cursor
        res = call("POST", f"/databases/{ids['prod_db']}/query", body)
        rows += res["results"]
        if not res.get("has_more"):
            break
        cursor = res["next_cursor"]

    done = 0
    for p in rows:
        title = _page_title(p)
        if args.ip and args.ip.lower() not in title.lower():
            continue
        status = backfill_row(p["id"], title, args.dry_run)
        print(f"  {title[:60]:60} | {status}")
        if status.startswith(("added", "would")):
            done += 1
    print(f"\n{'would touch' if args.dry_run else 'touched'} {done} rows")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
