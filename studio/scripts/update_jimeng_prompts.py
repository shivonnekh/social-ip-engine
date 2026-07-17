#!/usr/bin/env python3
"""Rewrite every Production Tracker row's 🎬 即梦 prompt code blocks to the new
content-safety-passing template (notion_prompts.build_jimeng_prompt, rewritten
2026-07-10 after root-causing the 即梦 hang-lottery to medical-vocabulary
content review).

NON-DESTRUCTIVE by design: patches ONLY the 即梦 prompt code block text, in
place — never touches images, audio, videos, or any other block (unlike
apply_shot_plan's rebuild, which wipes the row body).

The shot's visual text is recovered FROM the existing prompt (both historical
formats), so this needs no access to the Content Library shot guide:
  - 2026-07 format:  分镜指令（Shot Guide）：<visual>
  - 2026-06 format:  画面 / 动作（按分镜）：<visual>
Blocks already in the new format (contain 【Character】) are skipped, so the
script is idempotent.

Usage:
  python3 scripts/update_jimeng_prompts.py --dry-run   # preview only
  python3 scripts/update_jimeng_prompts.py             # patch all rows
  python3 scripts/update_jimeng_prompts.py --row <id>  # one row only
"""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import notion_image as ni  # noqa: E402  (ncall/_children/_txt helpers)
import notion_prompts as npm  # noqa: E402
import pipeline_common as pc  # noqa: E402

_VISUAL_PATTERNS = [
    re.compile(r"分镜指令（Shot Guide）：(.*?)(?=\n画面要生动丰富|\n图片：|\n人物對口型|\n运镜：|\Z)", re.S),
    re.compile(r"分镜指令：(.*?)(?=\n画面要生动丰富|\n图片：|\n人物對口型|\n运镜：|\Z)", re.S),  # bare variant (Building Muscle era)
    re.compile(r"画面 / 动作（按分镜）：(.*?)(?=\n人物對口型|\n运镜：|\n图片：|\Z)", re.S),
    re.compile(r"【Shot Guide】(.*?)(?=\n【|\Z)", re.S),  # rerun over new format
]


def _extract_visual(old_prompt: str) -> str | None:
    for pat in _VISUAL_PATTERNS:
        m = pat.search(old_prompt)
        if m:
            visual = m.group(1).strip()
            # Strip the harmonizing clause build_jimeng_prompt() appends to
            # dialogue shots' Shot Guides (fourth-pass, 2026-07-16) — without
            # this, every re-extraction would re-capture the clause as part
            # of the visual and the rebuild would append it AGAIN, compounding
            # one copy per run.
            visual = re.sub(
                r"\s*Throughout every beat the presenter keeps facing the "
                r"camera, mouth visible, speaking the line\.?\s*$",
                "", visual)
            return visual.strip()
    return None


def _rt_chunks(text: str) -> list[dict]:
    """Notion caps each rich_text object at 2000 chars — chunk to be safe."""
    return [{"type": "text", "text": {"content": text[i:i + 1900]}}
            for i in range(0, len(text), 1900)]


def update_row(row_id: str, dry_run: bool) -> tuple[int, int]:
    """Returns (updated, skipped) counts for one row."""
    page = ni.ncall("GET", f"/pages/{row_id}")
    ip_id = page["properties"].get("IP", {}).get("relation", [])
    lang = npm.ip_language(ip_id[0]["id"]) if ip_id else ""

    updated = skipped = 0
    cur_shot: str | None = None
    want_code = False
    want_voice = False
    dialogue = ""
    for b in ni._children(row_id):
        t, tx = b["type"], ni._txt(b)
        if t == "heading_3":
            cur_shot = tx if tx.lower().startswith("shot") else None
            want_code = False
            want_voice = False
            dialogue = ""
        elif cur_shot and t == "paragraph" and "Voice script" in tx:
            want_voice = True
        elif cur_shot and want_voice and t == "code":
            dialogue = tx.strip()
            want_voice = False
        elif cur_shot and t == "paragraph" and "即梦" in tx:
            want_code = True
        elif cur_shot and want_code and t == "code":
            want_code = False
            # Staleness detection is REBUILD-AND-COMPARE (switched 2026-07-16,
            # fifth pass, from the previous "template marker phrase" scheme):
            # re-extract the shot's visual, rebuild the prompt with the
            # CURRENT build_jimeng_prompt(), and skip only if the result is
            # byte-identical to what's already stored. The marker scheme had
            # to be hand-updated on every template change and silently
            # no-ops the whole batch when forgotten (nearly happened twice
            # today); comparing actual output is idempotent by construction
            # and needs zero maintenance.
            visual = _extract_visual(tx)
            if visual is None:
                print(f"    ⚠️  {cur_shot}: unrecognized prompt format — left untouched")
                skipped += 1
                continue
            new_prompt = npm.build_jimeng_prompt(cur_shot, visual, lang, dialogue)
            if new_prompt == tx:
                skipped += 1
                continue
            if dry_run:
                print(f"    [dry-run] would update {cur_shot} ({len(new_prompt)} chars)")
            else:
                ni.ncall("PATCH", f"/blocks/{b['id']}",
                         {"code": {"rich_text": _rt_chunks(new_prompt)}})
                print(f"    ✅ {cur_shot} updated")
            updated += 1
    return updated, skipped


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--row", help="only this Production row page id")
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    if args.row:
        rows = [ni.ncall("GET", f"/pages/{args.row}")]
    else:
        rows = pc._query_all(pc._load_notion_ids()["prod_db"])

    total_u = total_s = 0
    for r in rows:
        name = pc._title_of(r)
        print(f"▶ {name}")
        u, s = update_row(r["id"], args.dry_run)
        total_u += u
        total_s += s
    print(f"\n{'[dry-run] ' if args.dry_run else ''}done: {total_u} prompt(s) updated, {total_s} skipped")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
