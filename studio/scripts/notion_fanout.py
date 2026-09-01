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
import subprocess
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

from notion_prompts import apply_shot_plan, ip_language, draft_title, apply_script_property
from notion_carousel_prompts import apply_carousel_plan

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


# Every Notion request gets a hard timeout. Without one, urlopen() blocks
# FOREVER on a stalled TCP connection: no exception, no retry, no output. A
# fan-out sat at 0.17s of CPU for 30 minutes that way on 2026-09-01 and silently
# stalled a 10-concept batch behind it. A timeout turns that dead hang into a
# normal retry, which the loop below already knows how to handle.
NOTION_TIMEOUT_S = 30


def call(method: str, path: str, body: dict | None = None, retries: int = 5) -> dict:
    data = json.dumps(body).encode() if body is not None else None
    for attempt in range(retries):
        req = urllib.request.Request(f"{BASE}{path}", data=data, headers=_headers(), method=method)
        try:
            with urllib.request.urlopen(req, timeout=NOTION_TIMEOUT_S) as resp:
                return json.loads(resp.read().decode())
        except urllib.error.HTTPError as exc:
            payload = exc.read().decode()
            if exc.code == 429 and attempt < retries - 1:
                time.sleep(float(exc.headers.get("Retry-After", 1)) + 0.5)
                continue
            if exc.code >= 500 and attempt < retries - 1:
                time.sleep(2 ** attempt)
                continue
            sys.exit(f"[error] {method} {path} -> HTTP {exc.code}: {payload}")
        except (urllib.error.URLError, TimeoutError, OSError) as exc:
            # Transport-level failure (timeout, DNS, reset). Retry with backoff
            # rather than dying — these are routine on a long batch run.
            if attempt < retries - 1:
                print(f"[warn] {method} {path} -> {type(exc).__name__}: {exc} "
                      f"(retry {attempt + 1}/{retries - 1})", file=sys.stderr, flush=True)
                time.sleep(2 ** attempt)
                continue
            sys.exit(f"[error] {method} {path} -> {type(exc).__name__}: {exc}")
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
    ap.add_argument("--ip", help="Filter to a specific IP (substring match, e.g. 'Jackie')")
    ap.add_argument("--dry-run", action="store_true", help="Preview only, no writes")
    args = ap.parse_args()

    ids = load_ids()
    content_id, content_name = find_content(ids, args.content, args.content_id)
    _concept = call("GET", f"/pages/{content_id}")
    _hook = "".join(t["plain_text"] for t in _concept["properties"].get("Hook",{}).get("rich_text",[]))
    _ts = _concept["properties"].get("Topic",{}).get("select"); _topic = _ts["name"] if _ts else content_name
    ips = list_ips(ids, args.all_ips)
    if args.ip:
        ips = [ip for ip in ips if args.ip.lower() in title_of(ip).lower()]
        if not ips:
            sys.exit(f"[error] no IP matching '{args.ip}'")
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
        _title = draft_title(_hook, _topic, ip_language(ip["id"]))
        _props = {
            "Name": {"title": rt(row_name)},
            "Content": {"relation": [{"id": content_id}]},
            "IP": {"relation": [{"id": ip["id"]}]},
            "Stage": {"select": {"name": "💡 Idea"}},
            "Notes": {"rich_text": rt(note)},
        }
        if _title:
            _props["🏷️ Title"] = {"rich_text": rt(_title)}
        new_row = call("POST", "/pages", {"parent": {"database_id": ids["prod_db"]}, "properties": _props})
        sp = apply_script_property(new_row["id"])  # fill Script property (IP language) FIRST
        print(f"      Script: {sp}")
        apply_shot_plan(new_row["id"])  # video body — reads the Script property

        # Carousel is a genuinely separate content system from video (not a
        # section bolted onto apply_shot_plan — that coupling was tried and
        # reverted 2026-08-13: a function named for VIDEO shots has no
        # business also deciding whether a row gets carousel panels). Called
        # independently, unconditionally — apply_carousel_plan() itself is
        # the one that decides "no-carousel-guide" (most concepts, silent,
        # not an error) vs "applied" (the concept actually has a 🎠 Carousel
        # Guide). Runs regardless of whether this concept has a Shot Guide
        # at all, so a carousel-only concept (no video) still gets its
        # panels populated at fan-out time — the bug this call fixes.
        try:
            cs = apply_carousel_plan(new_row["id"])
            if cs not in ("no-carousel-guide", "no-content"):
                print(f"      Carousel: {cs}")
        except Exception as exc:  # noqa: BLE001 - never let this abort the fan-out
            print(f"      ⚠️  carousel section skipped ({exc})")

        time.sleep(0.34)

    if args.dry_run:
        print("[fanout] dry-run — nothing written")
    else:
        print(f"[fanout] done — created {len(to_create)} production rows")
        if to_create and _dm_map_enabled():
            _sync_dm_map()
    return 0


def _dm_map_enabled() -> bool:
    """Whether the legacy dm_map.json export should still run.

    OFF by default since 2026-09-01. `dm_map.json` fed studio/server/, which was
    retired to docs/legacy/ai-tcm-ip-server/ — the LIVE keyword->DM path is
    social-ip-engine's data/channels/comment_responses.json, wired by
    src/notion_sync.py on the Stage flip. Nothing reads dm_map.json any more, so
    the export could only ever fail, and it did: every single fan-out printed a
    FileNotFoundError traceback for a missing studio/server/dm_map.json.

    That noise is not cosmetic. During the 2026-09-01 ten-concept batch it sat in
    the tail of every fan-out's captured output, which is exactly where a real
    error would have appeared — a routine failure that trains you to ignore the
    place real failures show up. Set FANOUT_DM_MAP=1 to re-enable.
    """
    return os.environ.get("FANOUT_DM_MAP", "").strip().lower() in {"1", "true", "yes"}


def _sync_dm_map() -> None:
    """Re-export dm_map.json and auto-push so Render picks up new keywords.

    LEGACY — disabled by default, see _dm_map_enabled().
    Set FANOUT_NO_PUSH=1 to skip the git push (e.g. during local dev).
    """
    scripts_dir = Path(__file__).resolve().parent
    root = scripts_dir.parent
    dm_map_path = root / "server" / "dm_map.json"

    print("\n[dm_map] regenerating dm_map.json ...")
    result = subprocess.run(
        [sys.executable, str(scripts_dir / "export_dm_map.py")],
        cwd=str(root),
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        print(f"[dm_map] ⚠️  export failed:\n{result.stderr}")
        return
    print(result.stdout.strip())

    if os.environ.get("FANOUT_NO_PUSH", "").lower() in {"1", "true", "yes"}:
        print("[dm_map] FANOUT_NO_PUSH set — skipping git push")
        return

    # Check if dm_map.json actually changed before committing
    diff = subprocess.run(
        ["git", "diff", "--quiet", str(dm_map_path)],
        cwd=str(root),
    )
    if diff.returncode == 0:
        print("[dm_map] dm_map.json unchanged — no push needed")
        return

    kw_count = len(json.loads(dm_map_path.read_text(encoding="utf-8")))
    print(f"[dm_map] pushing updated dm_map.json ({kw_count} keywords) → Render redeploys in ~2 min")
    subprocess.run(["git", "add", str(dm_map_path)], cwd=str(root), check=True)
    subprocess.run(
        ["git", "commit", "-m", f"chore: update dm_map ({kw_count} keywords)"],
        cwd=str(root),
        check=True,
    )
    push = subprocess.run(["git", "push"], cwd=str(root), capture_output=True, text=True)
    if push.returncode == 0:
        print("[dm_map] pushed ✓ — new keywords will be live on Render in ~2 min")
    else:
        print(f"[dm_map] ⚠️  push failed (commit saved locally):\n{push.stderr}")


if __name__ == "__main__":
    raise SystemExit(main())
