#!/usr/bin/env python3
"""One-time (but safely re-runnable) batch: rebuild EVERY Production row's
🖼️ Cover prompt with the current build_cover_prompt() template, then
actually regenerate the cover image from it.

Added 2026-07-16 after rewriting build_cover_prompt() to the viral-thumbnail
style (bold black highlight-box text, yellow/white split-color words, accent
burst) reverse-engineered from Shivonne's real published covers — see
notion_prompts.py's build_cover_prompt() docstring for the full story. That
function only affects NEW rows going forward (fanout writes the prompt once,
at row-creation time) — every EXISTING row still has whatever prompt text was
written back when it was created. This script closes that gap for the whole
board in one pass: rewrite the stored prompt text (matching backfill_cover_
dm_prompts.py's exact persona/title/hook_visual sourcing, so results stay
consistent with how new rows get built), then regenerate + upload the image
(reuses generate_cover.py's own main() via subprocess — no image-gen logic
duplicated here).

Costs one gpt-image-2 call per row — real spend, not free. Reports a clear
✅/❌ per row; one row's failure never aborts the rest (same "don't let a
partial run look like nothing happened" contract as every other batch script
in this pipeline).

Usage:
  python3 scripts/regenerate_all_covers.py --dry-run   # preview prompt rebuild only
  python3 scripts/regenerate_all_covers.py             # rebuild + regenerate everywhere
  python3 scripts/regenerate_all_covers.py --row <id>  # one row only
"""
from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import notion_image as ni  # noqa: E402
import notion_prompts as npm  # noqa: E402
import pipeline_common as pc  # noqa: E402


def _find_cover_prompt_block(row_id: str) -> dict | None:
    in_section, want = False, False
    for b in ni._children(row_id):
        t, tx = b["type"], ni._txt(b)
        if t == "heading_3":
            in_section = "cover photo" in tx.casefold()
            continue
        if not in_section:
            continue
        if t == "paragraph" and "cover prompt" in tx.casefold():
            want = True
        elif want and t == "code":
            return b
    return None


def rebuild_prompt(row_id: str, dry_run: bool) -> tuple[bool, str]:
    """Returns (ok, detail). Rebuilds + writes back the row's Cover prompt
    text using the CURRENT build_cover_prompt() template — same persona/
    title/hook_visual sourcing as backfill_cover_dm_prompts.py."""
    page = ni.ncall("GET", f"/pages/{row_id}")
    content_rel = page["properties"].get("Content", {}).get("relation", [])
    ip_rel = page["properties"].get("IP", {}).get("relation", [])
    if not content_rel:
        return False, "no Content relation"
    if not ip_rel:
        return False, "no IP relation"

    persona = npm.ip_persona(ip_rel[0]["id"])[1]
    concept_title = npm._page_title(ni.ncall("GET", f"/pages/{content_rel[0]['id']}"))
    shots = npm.parse_storyboard(content_rel[0]["id"])
    hook_visual = npm._primary_beat(shots[0]["visual"]) if shots else ""
    new_prompt = npm.build_cover_prompt(persona, concept_title, hook_visual)

    block = _find_cover_prompt_block(row_id)
    if block is None:
        return False, "no '🖼️ Cover Photo' section on this row yet — run backfill_cover_dm_prompts.py first"

    if dry_run:
        return True, f"would rewrite prompt ({len(new_prompt)} chars)"

    chunks = [{"type": "text", "text": {"content": new_prompt[i:i + 1900]}}
              for i in range(0, len(new_prompt), 1900)]
    ni.ncall("PATCH", f"/blocks/{block['id']}", {"code": {"rich_text": chunks}})
    return True, f"prompt rewritten ({len(new_prompt)} chars)"


def regenerate_image(row_id: str) -> tuple[bool, str]:
    """Shells out to generate_cover.py --force — same precedent every other
    batch script in this pipeline follows (never reimplement the image-gen
    call itself)."""
    proc = subprocess.run(
        [sys.executable, str(Path(__file__).resolve().parent / "generate_cover.py"),
         "--row", row_id, "--force"],
        capture_output=True, text=True, timeout=300,
    )
    ok = proc.returncode == 0
    tail = (proc.stdout or proc.stderr).strip().splitlines()
    detail = tail[-1] if tail else f"exit {proc.returncode}"
    return ok, detail


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--row", help="only this Production row page id")
    ap.add_argument("--dry-run", action="store_true", help="rebuild prompt only, no image generation")
    args = ap.parse_args()

    if args.row:
        rows = [ni.ncall("GET", f"/pages/{args.row}")]
    else:
        rows = pc._query_all(pc._load_notion_ids()["prod_db"])

    results: list[tuple[str, bool, str]] = []
    for r in rows:
        name = pc._title_of(r)
        row_id = r["id"]
        print(f"▶ {name}")

        ok, detail = rebuild_prompt(row_id, args.dry_run)
        print(f"    prompt: {'✅' if ok else '❌'} {detail}")
        if not ok:
            results.append((name, False, f"prompt rebuild failed: {detail}"))
            continue
        if args.dry_run:
            results.append((name, True, "dry-run"))
            continue

        img_ok, img_detail = regenerate_image(row_id)
        print(f"    image:  {'✅' if img_ok else '❌'} {img_detail}")
        results.append((name, img_ok, img_detail))

    print("\n" + "=" * 60)
    ok_count = sum(1 for _, ok, _ in results if ok)
    print(f"done: {ok_count}/{len(results)} row(s) succeeded")
    for name, ok, detail in results:
        if not ok:
            print(f"  ❌ {name}: {detail}")
    return 0 if ok_count == len(results) else 1


if __name__ == "__main__":
    raise SystemExit(main())
