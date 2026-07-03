#!/usr/bin/env python3
"""In-row production guide for the AI-IP Production Tracker.

Notion's API can't create a UI "template", so instead we inject this step-by-step
checklist into the BODY of every Production row — existing rows (via --backfill)
and every future fan-out row (notion_fanout.py imports build_guide_blocks).

The guide uses to-do checkboxes so an operator can tick each step inside the row,
plus copy-ready code blocks for the GPT prompt and MiniMax config.

Usage:
    export NOTION_KEY=ntn_...
    python3 scripts/notion_row_guide.py --backfill            # add guide to all rows missing it
    python3 scripts/notion_row_guide.py --backfill --force    # add even if a guide seems present
"""
from __future__ import annotations

import json
import os
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

BASE = "https://api.notion.com/v1"
IDS_PATH = Path(__file__).resolve().parent / "notion_ids.json"
GUIDE_MARK = "🧭 PRODUCTION CHECKLIST"  # sentinel so we don't double-inject


def _headers() -> dict[str, str]:
    key = os.environ.get("NOTION_KEY", "").strip()
    if not key:
        sys.exit("[error] NOTION_KEY env var not set")
    return {"Authorization": f"Bearer {key}",
            "Notion-Version": "2022-06-28", "Content-Type": "application/json"}


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


# ---------- block helpers ----------
def _rt(t): return [{"type": "text", "text": {"content": t}}]
def _callout(t, e, c="gray_background"):
    return {"object": "block", "type": "callout",
            "callout": {"rich_text": _rt(t), "icon": {"type": "emoji", "emoji": e}, "color": c}}
def _h3(t): return {"object": "block", "type": "heading_3", "heading_3": {"rich_text": _rt(t)}}
def _todo(t): return {"object": "block", "type": "to_do", "to_do": {"rich_text": _rt(t), "checked": False}}
def _para(t): return {"object": "block", "type": "paragraph", "paragraph": {"rich_text": _rt(t)}}
def _code(t): return {"object": "block", "type": "code",
                      "code": {"rich_text": _rt(t), "language": "plain text"}}
def _div(): return {"object": "block", "type": "divider", "divider": {}}


def build_guide_blocks() -> list[dict]:
    """The full in-row checklist. Same for every video; specifics live in the
    row's linked IP (voice config) + Content (shot guide) + Notes."""
    return [
        _callout(f"{GUIDE_MARK} — do these top to bottom and tick each box. "
                 "Everything for THIS video is here: your IP, script and config are in the "
                 "properties above (voice config is in Notes; script is in Translated Script).",
                 "🧭", "blue_background"),

        _h3("1️⃣ Images (GPT)"),
        _todo("Open ChatGPT (GPT-4o) and upload this IP's face photo (👤 IP Registry → Avatar Image)."),
        _todo("Scroll to the 🖼️ Image Prompts section below — the prompts are already filled in for you. Copy each one into GPT."),
        _todo("Generate one image per shot (4–5 total)."),
        _todo("Drag the images into this page / paste links in Assets, then tick the 🎨 Image property + set Stage = 🎨 Image."),

        _h3("2️⃣ Voice (MiniMax)"),
        _todo("Open MiniMax (T2A). Copy the Script property above → paste into the text box. ⚠️ Avoid commas (they cause odd pauses)."),
        _todo("Use the values in the 🎙️ Voice Config section below — already filled in for you."),
        _todo("Generate → download mp3 → paste link in Assets → tick the 🎙️ Voice property + set Stage = 🎙️ Voice."),

        _h3("3️⃣ Video (即梦 / Jimeng)"),
        _todo("Open 即梦 → OmniHuman. Upload ONE portrait image + ONE voice clip. ⚠️ Each clip must be ≤13s (use one segment at a time)."),
        _todo("Generate → download mp4. Repeat for every voice segment."),
        _todo("Paste the final video link in Assets → tick the 🎬 Video property + set Stage = 🎬 Video (or ✂️ Edit if it needs cutting/captions)."),

        _div(),
        _callout("🎉 When it is posted live, set Stage = ✅ Published. Stuck? Tell your trainer where.",
                 "🏁", "green_background"),
    ]


def has_guide(page_id: str) -> bool:
    kids = call("GET", f"/blocks/{page_id}/children?page_size=50").get("results", [])
    for b in kids:
        if b.get("type") == "callout":
            txt = "".join(t.get("plain_text", "") for t in b["callout"].get("rich_text", []))
            if GUIDE_MARK in txt:
                return True
    return False


def apply_guide(page_id: str, force: bool = False) -> bool:
    if not force and has_guide(page_id):
        return False
    blocks = build_guide_blocks()
    for i in range(0, len(blocks), 25):
        call("PATCH", f"/blocks/{page_id}/children", {"children": blocks[i:i + 25]})
    return True


def _title(page: dict) -> str:
    for prop in page["properties"].values():
        if prop.get("type") == "title":
            return "".join(t["plain_text"] for t in prop["title"])
    return "(untitled)"


def backfill(force: bool) -> int:
    ids = json.loads(IDS_PATH.read_text(encoding="utf-8"))
    rows, cursor = [], None
    while True:
        body = {"page_size": 100}
        if cursor:
            body["start_cursor"] = cursor
        data = call("POST", f"/databases/{ids['prod_db']}/query", body)
        rows.extend(data["results"])
        if data.get("has_more"):
            cursor = data["next_cursor"]
        else:
            break
    added = 0
    for r in rows:
        if apply_guide(r["id"], force):
            print(f"  + guide added → {_title(r)}")
            added += 1
            time.sleep(0.34)
        else:
            print(f"  · skipped (already has guide) → {_title(r)}")
    print(f"[done] guide added to {added}/{len(rows)} rows")
    return 0


if __name__ == "__main__":
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("--backfill", action="store_true", help="add guide to all Production rows missing it")
    ap.add_argument("--force", action="store_true", help="add even if a guide seems present")
    args = ap.parse_args()
    if not args.backfill:
        sys.exit("nothing to do — pass --backfill")
    raise SystemExit(backfill(args.force))
