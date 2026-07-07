"""pipeline_common.py — shared helpers for the 3 pipeline-stage scripts
(generate_assets.py / generate_all_videos.py / finalize_all_videos.py).

WHY THIS EXISTS
---------------
Each of those 3 scripts corresponds to one of Shivonne's own review
checkpoints:
  1. She reviews the Content Library Script -> generate_assets.py
     (fan-out + image + voice, for every active IP in one go)
  2. She reviews image + voice -> generate_all_videos.py
     (video-gen, for every row under that content)
  3. She reviews video -> finalize_all_videos.py
     (karaoke captions + upload to "Production Video", for every row)

None of these wrap or re-implement the underlying tools (notion_fanout.py,
notion_image.py, batch_voice_gen.py, notion_video.py,
add_karaoke_captions.py) — they subprocess-invoke them exactly as if typed
by hand, one row at a time, per notion_fanout.py's OWN established
precedent (_sync_dm_map() already subprocess-invokes a sibling script).
This means zero risk of drifting from each tool's already-working,
independently-runnable behavior; the only new code is "which rows, in
what order, keep going if one fails."

ERROR ISOLATION (the whole point of doing this instead of one shell one-liner)
--------------------------------------------------------------------------------
A batch across multiple IPs (e.g. Jackie + Chloe) must NEVER let one row's
failure silently swallow or abort the others — every row is attempted, and
a clear pass/fail summary is printed at the end so a partial failure is
impossible to miss.
"""
from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path
from typing import Any

import notion_video as nv  # reuse ncall / _load_env (already run at import time)

SCRIPTS_DIR = Path(__file__).resolve().parent


def _load_notion_ids() -> dict[str, Any]:
    import json

    ids_path = SCRIPTS_DIR / "notion_ids.json"
    return json.loads(ids_path.read_text(encoding="utf-8"))


def _query_all(db_id: str, body: dict[str, Any] | None = None) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    cursor: str | None = None
    while True:
        payload = dict(body or {})
        payload["page_size"] = 100
        if cursor:
            payload["start_cursor"] = cursor
        data = nv.ncall_w("POST", f"/databases/{db_id}/query", payload)
        rows.extend(data["results"])
        if not data.get("has_more"):
            break
        cursor = data["next_cursor"]
    return rows


def _title_of(page: dict[str, Any]) -> str:
    for prop in page["properties"].values():
        if prop.get("type") == "title":
            return "".join(t["plain_text"] for t in prop["title"])
    return "(untitled)"


def production_rows_for_content(content_id: str) -> list[dict[str, Any]]:
    """Every Production Tracker row whose "Content" relation contains
    `content_id` — same filter notion_fanout.py's existing_pairs() uses for
    dedup, just returning full rows (with names) instead of a set of IP ids.
    Ordered by title for stable, predictable batch-run output."""
    ids = _load_notion_ids()
    body = {"filter": {"property": "Content", "relation": {"contains": content_id}}}
    rows = _query_all(ids["prod_db"], body)
    rows.sort(key=_title_of)
    return rows


def find_content(name: str | None, content_id: str | None) -> tuple[str, str]:
    """Resolve a Content Library concept by name (substring, case-insensitive)
    or explicit page id -> (content_id, content_name). Mirrors
    notion_fanout.find_content exactly (kept independent rather than
    imported — notion_fanout.py's own `call()` sys.exit()s the WHOLE
    process on any HTTP error, which is fine for a single-purpose CLI but
    would be too blunt inside code these 3 orchestrators also use for
    later steps)."""
    ids = _load_notion_ids()
    if content_id:
        page = nv.ncall(f"/pages/{content_id}")
        return page["id"], _title_of(page)
    all_content = _query_all(ids["content_db"])
    matches = [r for r in all_content if name and name.lower() in _title_of(r).lower()]
    if not matches:
        sys.exit(f"[error] no Content concept matching '{name}'")
    if len(matches) > 1:
        listing = "\n".join(f"  - {_title_of(m)}" for m in matches)
        sys.exit(f"[error] '{name}' matched {len(matches)} concepts; be more specific:\n{listing}")
    return matches[0]["id"], _title_of(matches[0])


def run_step(cmd: list[str], label: str) -> bool:
    """Run one subprocess step, streaming its output live (so a long-running
    step like video-gen or Whisper transcription isn't silent for minutes).
    Returns True/False — never raises, so one row's failure can never take
    down the rest of a batch."""
    print(f"    -> {' '.join(cmd)}")
    result = subprocess.run(cmd, cwd=str(SCRIPTS_DIR))
    ok = result.returncode == 0
    status = "✅" if ok else f"❌ (exit {result.returncode})"
    print(f"    {status} {label}")
    return ok


def print_batch_summary(results: list[tuple[str, str, bool]]) -> bool:
    """`results` is a list of (row_name, step_label, ok). Prints a clear
    pass/fail table and returns True iff EVERYTHING succeeded — callers use
    this to decide the process exit code, but every row was still
    attempted regardless of earlier failures (see module docstring)."""
    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    all_ok = True
    for row_name, step_label, ok in results:
        mark = "✅" if ok else "❌"
        if not ok:
            all_ok = False
        print(f"  {mark} {row_name} — {step_label}")
    print("=" * 60)
    if all_ok:
        print("all steps succeeded")
    else:
        print("⚠️  one or more steps FAILED — see ❌ rows above, safe to re-run just those")
    return all_ok


def add_row_selection_args(ap: argparse.ArgumentParser) -> None:
    """The 3-way selector shared by all 3 pipeline-stage scripts: operate
    on every Production row under a Content concept, or on just one row."""
    grp = ap.add_mutually_exclusive_group(required=True)
    grp.add_argument("--content", help="Content Library concept name (substring match)")
    grp.add_argument("--content-id", help="Explicit Content Library page id")
    grp.add_argument("--row", help="Operate on ONE existing Production row only")


def resolve_rows(args: argparse.Namespace) -> list[dict[str, Any]]:
    """Turn --content/--content-id/--row into a list of full Production row
    dicts. Used by generate_all_videos.py and finalize_all_videos.py
    directly; generate_assets.py has its own variant since it ALSO needs to
    run fan-out in between resolving the content and querying its rows."""
    if args.row:
        return [nv.ncall(f"/pages/{args.row}")]
    content_id, content_name = find_content(args.content, args.content_id)
    print(f"[pipeline] concept: {content_name}")
    rows = production_rows_for_content(content_id)
    if not rows:
        sys.exit(
            f"[error] no Production rows found for content '{content_name}' "
            "— run generate_assets.py first"
        )
    return rows
