#!/usr/bin/env python3
"""Auto-fan-out watcher for the AI-IP board.

Notion has no native "when a property changes, create N rows" trigger, so this
script provides it: it finds Content Library concepts whose Concept Status is
"✅ Ready to fan-out" and fans each one out into the Production Tracker (one row
per ACTIVE IP, each pre-loaded with the in-row checklist). After fanning out, it
flips the concept to "🚀 Fanned out" so it is not reprocessed.

Your workflow becomes:
    1. Duplicate the TEMPLATE row in Content Library, fill it in.
    2. Set Concept Status → ✅ Ready to fan-out.
    3. (this watcher runs) → Production rows appear, each with its template.

Run once:        python3 scripts/notion_watch.py
Poll forever:    python3 scripts/notion_watch.py --loop 30      # check every 30s
Preview only:    python3 scripts/notion_watch.py --dry-run

Make it feel automatic: schedule the single-run via cron/launchd, or leave
--loop running in a terminal. (Real-time on status-change needs a hosted Notion
webhook — that's the future upgrade; this covers it with zero hosting.)
"""
from __future__ import annotations

import argparse
import sys
import time

from notion_fanout import (
    call, existing_pairs, list_ips, load_ids, rt, short_ip_name, title_of,
)
from notion_prompts import apply_shot_plan

READY = "✅ Ready to fan-out"
DONE = "🚀 Fanned out"


def ready_concepts(ids: dict) -> list[dict]:
    body = {"filter": {"property": "Concept Status", "select": {"equals": READY}}}
    rows, cursor = [], None
    while True:
        payload = dict(body)
        payload["page_size"] = 100
        if cursor:
            payload["start_cursor"] = cursor
        data = call("POST", f"/databases/{ids['content_db']}/query", payload)
        rows.extend(data["results"])
        if data.get("has_more"):
            cursor = data["next_cursor"]
        else:
            break
    # never process the template row
    return [r for r in rows if not title_of(r).startswith("📝 TEMPLATE")]


def fan_out_concept(ids: dict, concept: dict, dry: bool) -> int:
    content_id = concept["id"]
    name = title_of(concept)
    ips = list_ips(ids, include_inactive=False)
    already = existing_pairs(ids, content_id)
    todo = [ip for ip in ips if ip["id"] not in already]
    print(f"  • {name}: {len(ips)} active IPs, {len(ips) - len(todo)} already linked, {len(todo)} to create")
    for ip in todo:
        ip_name = title_of(ip)
        vid = "".join(t["plain_text"] for t in ip["properties"].get("voice_id", {}).get("rich_text", []))
        speed = (ip["properties"].get("Speed", {}) or {}).get("number")
        pitch = (ip["properties"].get("Pitch", {}) or {}).get("number")
        boost = "".join(t["plain_text"] for t in ip["properties"].get("Language Boost", {}).get("rich_text", []))
        row_name = f"{name} × {short_ip_name(ip_name)}"
        note = f"voice_id={vid or '?'} speed={speed} pitch={pitch} boost={boost or '?'}"
        print(f"      + {row_name}   [{note}]")
        if dry:
            continue
        new_row = call("POST", "/pages", {"parent": {"database_id": ids["prod_db"]}, "properties": {
            "Name": {"title": rt(row_name)},
            "Content": {"relation": [{"id": content_id}]},
            "IP": {"relation": [{"id": ip["id"]}]},
            "Stage": {"select": {"name": "💡 Idea"}},
            "Notes": {"rich_text": rt(note)},
        }})
        apply_shot_plan(new_row["id"])
        time.sleep(0.34)
    if not dry:
        call("PATCH", f"/pages/{content_id}", {"properties": {"Concept Status": {"select": {"name": DONE}}}})
    return len(todo)


def tick(ids: dict, dry: bool) -> int:
    concepts = ready_concepts(ids)
    if not concepts:
        return 0
    print(f"[watch] {len(concepts)} concept(s) ready to fan out")
    created = 0
    for c in concepts:
        created += fan_out_concept(ids, c, dry)
    if not dry:
        print(f"[watch] created {created} production row(s); concepts marked '{DONE}'")
    return created


def main() -> int:
    ap = argparse.ArgumentParser(description="Auto fan-out on 'Ready to fan-out' status")
    ap.add_argument("--loop", type=int, metavar="SECONDS", help="poll continuously every N seconds")
    ap.add_argument("--dry-run", action="store_true", help="preview only, no writes")
    args = ap.parse_args()
    ids = load_ids()

    if args.loop:
        print(f"[watch] polling every {args.loop}s — Ctrl+C to stop")
        try:
            while True:
                if tick(ids, args.dry_run) == 0:
                    print("[watch] nothing ready", end="\r")
                time.sleep(args.loop)
        except KeyboardInterrupt:
            print("\n[watch] stopped")
            return 0
    else:
        n = tick(ids, args.dry_run)
        if n == 0:
            print("[watch] nothing ready to fan out")
        return 0


if __name__ == "__main__":
    raise SystemExit(main())
