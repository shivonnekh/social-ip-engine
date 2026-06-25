#!/usr/bin/env python3
"""Fan out a Content concept into one Production Tracker row per ACTIVE IP.

The scaling core of the AI-IP board: write a master concept once in
Content Library, then explode it into N per-IP production rows (each pre-linked
to its IP so the generation pipeline can read that IP's voice config).

Usage:
    export NOTION_KEY=ntn_...                 # never commit this
    # fan out by concept name (substring match, case-insensitive):
    python3 scripts/notion_fanout.py --content "Detox"
    # or by explicit Content Library page id:
    python3 scripts/notion_fanout.py --content-id 389f2a3f-...
    # include inactive IPs too:
    python3 scripts/notion_fanout.py --content "Detox" --all-ips
    # preview without writing:
    python3 scripts/notion_fanout.py --content "Detox" --dry-run

DB ids are read from scripts/notion_ids.json (not secret).
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

from notion_prompts import apply_shot_plan  # build the per-shot plan (image prompt + voice script) on each row

BASE = "https://api.notion.com/v1"
IDS_PATH = Path(__file__).resolve().parent / "notion_ids.json"


def _headers() -> dict[str, str]:
    key = os.environ.get("NOTION_KEY", "").strip()
    if not key:
        sys.exit("[error] NOTION_KEY env var not set")
    return {
        "Authorization": f"Bearer {key}",
        "Notion-Version": "2022-06-28",
        "Content-Type": "application/json",
    }


def call(method: str, path: str, body: dict | None = None, retries: int = 5) -> dict:
    data = json.dumps(body).encode() if body is not None else None
    for attempt in range(retries):
        req = urllib.request.Request(f"{BASE}{path}", data=data, headers=_headers(), method=method)
        try:
            with urllib.request.urlopen(req) as resp:
                return json.loads(resp.read().decode())
        except urllib.error.HTTPError as exc:
            payload = exc.read().decode()
            if exc.code == 429 and attempt < retries - 1:
                time.sleep(float(exc.headers.get("Retry-After", 1)) + 0.5)
                continue
            sys.exit(f"[error] {method} {path} -> HTTP {exc.code}: {payload}")
    sys.exit("[error] exhausted retries")


def rt(text: str) -> list[dict]:
    return [{"type": "text", "text": {"content": text}}]


def load_ids() -> dict:
    if not IDS_PATH.exists():
        sys.exit(f"[error] {IDS_PATH} missing")
    return json.loads(IDS_PATH.read_text(encoding="utf-8"))


def title_of(page: dict) -> str:
    for prop in page["properties"].values():
        if prop.get("type") == "title":
            return "".join(t["plain_text"] for t in prop["title"])
    return "(untitled)"


def query_all(db: str, body: dict | None = None) -> list[dict]:
    rows: list[dict] = []
    cursor: str | None = None
    while True:
        payload = dict(body or {})
        payload["page_size"] = 100
        if cursor:
            payload["start_cursor"] = cursor
        data = call("POST", f"/databases/{db}/query", payload)
        rows.extend(data["results"])
        if data.get("has_more"):
            cursor = data["next_cursor"]
        else:
            break
    return rows


def find_content(ids: dict, name: str | None, content_id: str | None) -> tuple[str, str]:
    if content_id:
        page = call("GET", f"/pages/{content_id}")
        return page["id"], title_of(page)
    matches = [r for r in query_all(ids["content_db"]) if name.lower() in title_of(r).lower()]
    if not matches:
        sys.exit(f"[error] no Content concept matching '{name}'")
    if len(matches) > 1:
        listing = "\n".join(f"  - {title_of(m)}" for m in matches)
        sys.exit(f"[error] '{name}' matched {len(matches)} concepts; be more specific:\n{listing}")
    return matches[0]["id"], title_of(matches[0])


def list_ips(ids: dict, include_inactive: bool) -> list[dict]:
    rows = query_all(ids["ip_db"])
    out = []
    for r in rows:
        active = (r["properties"].get("Active", {}) or {}).get("checkbox", False)
        if include_inactive or active:
            out.append(r)
    return out


def short_ip_name(full: str) -> str:
    # "🌸 Jessica (HK)" -> "Jessica"
    base = full.split("(")[0].strip()
    parts = [p for p in base.split() if not all(ord(c) > 0x2000 for c in p)]
    return " ".join(parts) or base


def existing_pairs(ids: dict, content_id: str) -> set[str]:
    """IP page ids already linked to this content in Production Tracker (avoid dupes)."""
    body = {"filter": {"property": "Content", "relation": {"contains": content_id}}}
    pairs: set[str] = set()
    for row in query_all(ids["prod_db"], body):
        for rel in row["properties"].get("IP", {}).get("relation", []):
            pairs.add(rel["id"])
    return pairs


def main() -> int:
    ap = argparse.ArgumentParser(description="Fan out a content concept across active IPs")
    grp = ap.add_mutually_exclusive_group(required=True)
    grp.add_argument("--content", help="Concept name (substring, case-insensitive)")
    grp.add_argument("--content-id", help="Explicit Content Library page id")
    ap.add_argument("--all-ips", action="store_true", help="Include inactive IPs too")
    ap.add_argument("--dry-run", action="store_true", help="Preview only, no writes")
    args = ap.parse_args()

    ids = load_ids()
    content_id, content_name = find_content(ids, args.content, args.content_id)
    ips = list_ips(ids, args.all_ips)
    if not ips:
        sys.exit("[error] no matching IPs (none active? try --all-ips)")

    already = existing_pairs(ids, content_id)
    to_create = [ip for ip in ips if ip["id"] not in already]
    skipped = len(ips) - len(to_create)

    print(f"[fanout] concept: {content_name}")
    print(f"[fanout] target IPs: {len(ips)}  | already linked (skip): {skipped}  | to create: {len(to_create)}")
    for ip in to_create:
        ip_name = title_of(ip)
        vid = "".join(t["plain_text"] for t in ip["properties"].get("voice_id", {}).get("rich_text", []))
        speed = (ip["properties"].get("Speed", {}) or {}).get("number")
        pitch = (ip["properties"].get("Pitch", {}) or {}).get("number")
        boost = "".join(t["plain_text"] for t in ip["properties"].get("Language Boost", {}).get("rich_text", []))
        row_name = f"{content_name} × {short_ip_name(ip_name)}"
        note = f"voice_id={vid or '?'} speed={speed} pitch={pitch} boost={boost or '?'}"
        print(f"   + {row_name}   [{note}]")
        if args.dry_run:
            continue
        new_row = call("POST", "/pages", {"parent": {"database_id": ids["prod_db"]}, "properties": {
            "Name": {"title": rt(row_name)},
            "Content": {"relation": [{"id": content_id}]},
            "IP": {"relation": [{"id": ip["id"]}]},
            "Stage": {"select": {"name": "💡 Idea"}},
            "Notes": {"rich_text": rt(note)},
        }})
        apply_shot_plan(new_row["id"])  # per-shot image prompts + voice scripts
        time.sleep(0.34)

    if args.dry_run:
        print("[fanout] dry-run — nothing written")
    else:
        print(f"[fanout] done — created {len(to_create)} production rows")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
