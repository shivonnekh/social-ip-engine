#!/usr/bin/env python3
"""Recover / sync voice clips from all Notion Production rows to local campaign folders.

For every Production row:
  1. Resolve campaigns/<content-slug>/<ip-slug>/voice/
  2. Walk the row body and find audio blocks per shot section
  3. Download each audio → shot{N}_voice.mp3 (skip if already exists locally)

Safe to re-run — skips shots already saved.

Usage:
    python3 scripts/sync_voice_from_notion.py            # all rows
    python3 scripts/sync_voice_from_notion.py --dry-run  # preview only
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
IDS_PATH = Path(__file__).resolve().parent / "notion_ids.json"
NOTION = "https://api.notion.com/v1"


# ── env ───────────────────────────────────────────────────────────────────────

def _load_env() -> None:
    envp = ROOT / ".env"
    if not envp.exists():
        return
    for line in envp.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        k, _, v = line.partition("=")
        os.environ.setdefault(k.strip(), v.strip())


_load_env()


def _nh() -> dict:
    key = os.environ.get("NOTION_KEY", "").strip()
    if not key:
        sys.exit("[error] NOTION_KEY not set")
    return {"Authorization": f"Bearer {key}", "Notion-Version": "2022-06-28"}


# ── Notion API ────────────────────────────────────────────────────────────────

def ncall(method: str, path: str, body: dict | None = None) -> dict:
    h = dict(_nh()); h["Content-Type"] = "application/json"
    data = json.dumps(body).encode() if body is not None else None
    req = urllib.request.Request(f"{NOTION}{path}", data=data, headers=h, method=method)
    with urllib.request.urlopen(req) as r:
        return json.loads(r.read().decode())


def _children(bid: str) -> list[dict]:
    out, cur = [], None
    while True:
        suf = "?page_size=100" + (f"&start_cursor={cur}" if cur else "")
        d = ncall("GET", f"/blocks/{bid}/children{suf}")
        out += d["results"]
        if not d.get("has_more"):
            return out
        cur = d["next_cursor"]


def _txt(b: dict) -> str:
    t = b["type"]
    return "".join(x.get("plain_text", "") for x in b.get(t, {}).get("rich_text", []))


def _all_prod_rows(prod_db: str) -> list[dict]:
    rows, cursor = [], None
    while True:
        body: dict = {"page_size": 100}
        if cursor:
            body["start_cursor"] = cursor
        data = ncall("POST", f"/databases/{prod_db}/query", body)
        rows.extend(data["results"])
        if not data.get("has_more"):
            return rows
        cursor = data["next_cursor"]


# ── slug / path helpers ───────────────────────────────────────────────────────

def _slugify(s: str) -> str:
    s = re.sub(r"[^\x00-\x7F]+", "", s)
    s = re.sub(r"[^a-z0-9\s-]", "", s.lower())
    s = re.sub(r"[\s-]+", "-", s).strip("-")
    return s or "unknown"


def _row_voice_dir(page: dict) -> Path | None:
    """Resolve campaigns/<content-slug>/<ip-slug>/voice/ from a Production row page."""
    content_slug = "unknown"
    content_rel = page["properties"].get("Content", {}).get("relation", [])
    if content_rel:
        cp = ncall("GET", f"/pages/{content_rel[0]['id']}")
        for prop in cp["properties"].values():
            if prop.get("type") == "title":
                content_slug = _slugify("".join(t["plain_text"] for t in prop["title"]))
                break

    ip_slug = "unknown"
    ip_rel = page["properties"].get("IP", {}).get("relation", [])
    if ip_rel:
        ip_page = ncall("GET", f"/pages/{ip_rel[0]['id']}")
        for prop in ip_page["properties"].values():
            if prop.get("type") == "title":
                ip_slug = _slugify("".join(t["plain_text"] for t in prop["title"]))
                break

    if content_slug == "unknown" and ip_slug == "unknown":
        return None
    return ROOT / "campaigns" / content_slug / ip_slug / "voice"


# ── audio extraction ──────────────────────────────────────────────────────────

def _audio_url(b: dict) -> str | None:
    audio = b.get("audio", {})
    return (audio.get("file", {}).get("url")
            or audio.get("external", {}).get("url"))


def extract_shot_audios(row_id: str) -> list[dict]:
    """Return [{shot_num, audio_url}] in order, one per shot that has an audio block."""
    blocks = _children(row_id)
    results: list[dict] = []
    shot_num = 0
    in_shot = False

    for b in blocks:
        t = b["type"]
        tx = _txt(b)
        if t == "heading_3" and tx.lower().startswith("shot"):
            shot_num += 1
            in_shot = True
        elif in_shot and t == "audio":
            url = _audio_url(b)
            if url:
                results.append({"shot": shot_num, "audio_url": url})
            in_shot = False  # only first audio per shot section

    return results


# ── row title ─────────────────────────────────────────────────────────────────

def _row_title(page: dict) -> str:
    for prop in page["properties"].values():
        if prop.get("type") == "title":
            return "".join(t["plain_text"] for t in prop["title"])
    return "(untitled)"


# ── main ──────────────────────────────────────────────────────────────────────

def main() -> None:
    ap = argparse.ArgumentParser(description="Sync voice clips from Notion to local campaign folders")
    ap.add_argument("--dry-run", action="store_true", help="Preview without downloading")
    args = ap.parse_args()

    ids = json.loads(IDS_PATH.read_text())
    print("Fetching all Production rows…")
    rows = _all_prod_rows(ids["prod_db"])
    print(f"Found {len(rows)} rows\n")

    total_saved = total_skipped = total_missing = 0

    for page in rows:
        row_id = page["id"]
        title = _row_title(page)
        print(f"▶ {title}")

        voice_dir = _row_voice_dir(page)
        if voice_dir is None:
            print("  ⚠️  could not resolve campaign path — skip\n")
            continue

        print(f"  → {voice_dir.relative_to(ROOT)}")

        shots = extract_shot_audios(row_id)
        if not shots:
            print("  (no audio blocks found in Notion)\n")
            total_missing += 1
            continue

        if not args.dry_run:
            voice_dir.mkdir(parents=True, exist_ok=True)

        for s in shots:
            dest = voice_dir / f"shot{s['shot']}_voice.mp3"
            if dest.exists():
                print(f"  Shot {s['shot']}: already local — skip")
                total_skipped += 1
                continue
            if args.dry_run:
                print(f"  Shot {s['shot']}: would download → {dest.name}")
                total_saved += 1
                continue
            try:
                urllib.request.urlretrieve(s["audio_url"], dest)
                size = dest.stat().st_size
                print(f"  Shot {s['shot']}: ✅ {dest.name} ({size:,} bytes)")
                total_saved += 1
            except Exception as e:
                print(f"  Shot {s['shot']}: ❌ download failed — {e}")
                total_missing += 1

        print()

    prefix = "[DRY RUN] " if args.dry_run else ""
    print(f"{prefix}Done — {total_saved} downloaded, {total_skipped} already local, {total_missing} missing/failed")


if __name__ == "__main__":
    main()
