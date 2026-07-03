#!/usr/bin/env python3
"""Auto-fan-out watcher for the AI-IP board (IP-targeted + voice).

Notion has no native "when a property changes, create N rows" trigger, so this
script provides it. On each tick it finds Content Library concepts whose
Concept Status is "✅ Ready to fan-out" and, for each, creates Production Tracker
rows for the TARGETED IPs only:

  • Target IPs = the concept's "Fan out to" multi-select.
  • If "Fan out to" is EMPTY → default to just **Jackie Chan**.

For every new row it:
  1. fills all properties (Content/IP relations, Stage, Notes, 🏷️ Title),
  2. fills the Script property in the IP's language (apply_script_property),
  3. builds the per-shot page body (apply_shot_plan),
  4. generates the Jackie voice clips (MiniMax) unless --no-voice,
then flips the concept to "🚀 Fanned out".

ADD A NEW IP LATER (no manual row building):
  add the IP to "Fan out to", then set Concept Status back to "✅ Ready to fan-out"
  (a one-click Notion button works great). The watcher dedups existing rows and
  creates only the new IP's row.

Run once (for cron):   python3 scripts/notion_watch.py
Poll forever:          python3 scripts/notion_watch.py --loop 300
Preview only:          python3 scripts/notion_watch.py --dry-run
Skip voice clips:      python3 scripts/notion_watch.py --no-voice
"""
from __future__ import annotations

import argparse
import time

from notion_fanout import (
    call, existing_pairs, list_ips, load_ids, rt, short_ip_name, title_of,
)
from notion_prompts import apply_shot_plan, apply_script_property, ip_language, draft_title

READY = "✅ Ready to fan-out"
DONE = "🚀 Fanned out"
DEFAULT_TARGETS = ["Jackie Chan"]   # used when "Fan out to" is empty


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
    return [r for r in rows if not title_of(r).startswith("📝 TEMPLATE")]


def _targets(concept: dict) -> list[str]:
    """IP names this concept should fan out to (multi-select; empty → default)."""
    ms = concept["properties"].get("Fan out to", {}).get("multi_select", [])
    names = [o["name"] for o in ms]
    return names or list(DEFAULT_TARGETS)


def _ip_index(ids: dict) -> dict[str, dict]:
    """short IP name → IP page (includes inactive: selection is the explicit intent)."""
    return {short_ip_name(title_of(ip)): ip for ip in list_ips(ids, include_inactive=True)}


def _gen_voice(row_id: str, row_name: str, ip_page: dict, dry: bool) -> None:
    """Generate MiniMax voice clips for a Production row (best-effort, never fatal).

    Uses the IP's voice config from its registry page — works for any IP.
    """
    if dry:
        print("        (voice: skipped — dry run)")
        return
    try:
        from batch_voice_gen import process_row, _ip_voice_config_from_page  # noqa: PLC0415
        cfg = _ip_voice_config_from_page(ip_page)
        if not cfg.get("voice_id"):
            print("        (voice: skipped — no voice_id in IP Registry)")
            return
        result = process_row(row_id, row_name, voice_config=cfg)
        print(f"        🎙️ voice: {result}")
    except Exception as exc:  # noqa: BLE001 — voice is optional, don't break fan-out
        print(f"        ⚠️ voice failed: {exc!r}")


def fan_out_concept(ids: dict, concept: dict, ip_index: dict, dry: bool, voice: bool) -> int:
    content_id = concept["id"]
    name = title_of(concept)
    hook = "".join(t["plain_text"] for t in concept["properties"].get("Hook", {}).get("rich_text", []))
    ts = concept["properties"].get("Topic", {}).get("select")
    topic = ts["name"] if ts else name

    targets = _targets(concept)
    already = existing_pairs(ids, content_id)

    resolved, missing = [], []
    for tname in targets:
        ip = ip_index.get(tname)
        if not ip:
            missing.append(tname)
        elif ip["id"] not in already:
            resolved.append(ip)

    print(f"  • {name}: target={targets} | to create={len(resolved)} | "
          f"already linked={len(targets) - len(resolved) - len(missing)}"
          + (f" | UNKNOWN IPs={missing}" if missing else ""))

    created = 0
    for ip in resolved:
        ip_name = title_of(ip)
        vid = "".join(t["plain_text"] for t in ip["properties"].get("voice_id", {}).get("rich_text", []))
        speed = (ip["properties"].get("Speed", {}) or {}).get("number")
        pitch = (ip["properties"].get("Pitch", {}) or {}).get("number")
        boost = "".join(t["plain_text"] for t in ip["properties"].get("Language Boost", {}).get("rich_text", []))
        short = short_ip_name(ip_name)
        row_name = f"{name} × {short}"
        note = f"voice_id={vid or '?'} speed={speed} pitch={pitch} boost={boost or '?'}"
        print(f"      + {row_name}   [{note}]")
        if dry:
            created += 1
            continue
        props = {
            "Name": {"title": rt(row_name)},
            "Content": {"relation": [{"id": content_id}]},
            "IP": {"relation": [{"id": ip["id"]}]},
            "Stage": {"select": {"name": "💡 Idea"}},
            "Notes": {"rich_text": rt(note)},
        }
        t = draft_title(hook, topic, ip_language(ip["id"]))
        if t:
            props["🏷️ Title"] = {"rich_text": rt(t)}
        new_row = call("POST", "/pages", {"parent": {"database_id": ids["prod_db"]}, "properties": props})
        print(f"        Script: {apply_script_property(new_row['id'])}")
        apply_shot_plan(new_row["id"])           # build per-shot body from Script
        if voice:
            _gen_voice(new_row["id"], row_name, ip, dry)
        created += 1
        time.sleep(0.34)

    # Flip to done only if every targeted IP is now satisfied (no unknown names left).
    if not dry and not missing:
        call("PATCH", f"/pages/{content_id}",
             {"properties": {"Concept Status": {"select": {"name": DONE}}}})
    elif not dry and missing:
        print(f"      ↳ left as '{READY}' — fix unknown IP names in 'Fan out to': {missing}")
    return created


def tick(ids: dict, dry: bool, voice: bool) -> int:
    concepts = ready_concepts(ids)
    if not concepts:
        return 0
    print(f"[watch] {len(concepts)} concept(s) ready to fan out")
    ip_index = _ip_index(ids)
    created = 0
    for c in concepts:
        created += fan_out_concept(ids, c, ip_index, dry, voice)
    if not dry:
        print(f"[watch] created {created} production row(s)")
    return created


def main() -> int:
    ap = argparse.ArgumentParser(description="Auto fan-out on 'Ready to fan-out' status")
    ap.add_argument("--loop", type=int, metavar="SECONDS", help="poll continuously every N seconds")
    ap.add_argument("--dry-run", action="store_true", help="preview only, no writes")
    ap.add_argument("--no-voice", action="store_true", help="do not generate voice clips")
    args = ap.parse_args()
    ids = load_ids()
    voice = not args.no_voice

    if args.loop:
        print(f"[watch] polling every {args.loop}s — Ctrl+C to stop")
        try:
            while True:
                if tick(ids, args.dry_run, voice) == 0:
                    print("[watch] nothing ready", end="\r")
                time.sleep(args.loop)
        except KeyboardInterrupt:
            print("\n[watch] stopped")
            return 0
    else:
        if tick(ids, args.dry_run, voice) == 0:
            print("[watch] nothing ready to fan out")
        return 0


if __name__ == "__main__":
    raise SystemExit(main())
