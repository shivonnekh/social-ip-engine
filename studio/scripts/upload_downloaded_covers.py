#!/usr/bin/env python3
"""upload_downloaded_covers.py — one-off: upload the 6 cover images Shivonne
downloaded on 2026-07-08 (~/Downloads/cover-*.png) back into their matching
Production Tracker rows' "🖼️ Cover Photo → 🖼️ Cover here" toggle.

Why this matters: notion_publish_media.resolve_cover() (the function the
live auto-publish webhook calls) reads the cover from EXACTLY that toggle
shape — heading_3 containing "cover photo" -> toggle containing "cover here"
-> an image block inside it. A cover sitting anywhere else on the page
(e.g. the older "🖼️ Reel Cover Photo Image Prompt" heading + bare image
block schema used by rows authored before 2026-07-06) is invisible to it,
and the row falls through to blind AI generation with no character
reference — the exact bug found in the 2026-07-08 live Facebook test
(wrong person drawn for Jackie's cover).

Two of the six matched rows (Migraine, Dry Eyes) predate the current
"🖼️ Cover Photo" section entirely and have no matching toggle to fill —
this script adds one (via studio's own cover_blocks() helper, same shape
apply_shot_plan/backfill_cover_dm_prompts.py already use) before uploading.

Usage:
    python3 scripts/upload_downloaded_covers.py --dry-run
    python3 scripts/upload_downloaded_covers.py
"""
from __future__ import annotations

import argparse
import json
import mimetypes
import os
import sys
import time
import urllib.error
import urllib.request
import uuid
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
_ENV = ROOT / ".env"
if _ENV.exists():
    for _line in _ENV.read_text(encoding="utf-8").splitlines():
        _line = _line.strip()
        if _line and not _line.startswith("#") and "=" in _line:
            _k, _, _v = _line.partition("=")
            os.environ.setdefault(_k.strip(), _v.strip())

sys.path.insert(0, str(Path(__file__).resolve().parent))
from notion_prompts import (  # noqa: E402
    _primary_beat,
    _relation_id,
    _txt,
    call,
    cover_blocks,
    ip_persona,
    parse_storyboard,
)

DOWNLOADS = Path.home() / "Downloads"

# filename -> (row_id, human label) — matched by topic against the
# Production Tracker (see chat transcript for the match reasoning; 3 of
# the 6 match the row's 🏷️ Title property word-for-word, the other 3 match
# on topic/keyword since the downloaded cover text is an earlier draft).
MATCHES: dict[str, tuple[str, str]] = {
    "cover-migraine.png": ("38df2a3f-4320-81a1-a1a2-c3deb9b79eab", "🤯 Migraine × Jackie Chan"),
    "cover-muscle.png": ("38df2a3f-4320-81d5-884c-fbd22603b293", "💪 Building Muscle × Jackie Chan"),
    "cover-yellow teeth.png": ("38ff2a3f-4320-81c1-bc79-fa3a0ff6adff", "🦷 Yellow Teeth × Jackie Chan"),
    "cover-anxiety.png": ("38df2a3f-4320-818a-8779-f4070bbaaeb4", "😮‍💨 Constant Anxiety × Jackie Chan"),
    "cover-SMYT ep01.png": ("390f2a3f-4320-81c0-8683-f3968f206e4d", "👅 Show Me your Tongue EP01 × Jackie Chan"),
    "cover-eye.png": ("38df2a3f-4320-819f-b0ea-ddcd6b550418", "👀 Dry Eyes × Jackie Chan"),
}


def _all_children(block_id: str) -> list[dict]:
    out, cur = [], None
    while True:
        suf = "?page_size=100" + (f"&start_cursor={cur}" if cur else "")
        d = call("GET", f"/blocks/{block_id}/children{suf}")
        out += d["results"]
        if d.get("has_more"):
            cur = d["next_cursor"]
        else:
            return out


def find_cover_toggle(row_id: str) -> str | None:
    """The row's "🖼️ Cover Photo" -> "🖼️ Cover here" toggle id, or None if
    that section doesn't exist yet (older-schema row)."""
    in_cover = False
    for b in _all_children(row_id):
        text = _txt(b)
        if b["type"] == "heading_3":
            in_cover = "cover photo" in text.casefold()
        elif in_cover and b["type"] == "toggle" and "cover here" in text.casefold():
            return b["id"]
    return None


def toggle_has_image(toggle_id: str) -> bool:
    return any(c["type"] == "image" for c in _all_children(toggle_id))


def add_cover_section(row_id: str) -> str:
    """Append a fresh 🖼️ Cover Photo section (same shape as
    backfill_cover_dm_prompts.py) and return the new empty toggle's id."""
    page = call("GET", f"/pages/{row_id}")
    concept_id = _relation_id(page, "Content")
    ip_id = _relation_id(page, "IP")
    persona = ip_persona(ip_id)[1] if ip_id else "TCM doctor"
    title = ""
    for prop in page["properties"].values():
        if prop.get("type") == "title":
            title = "".join(t["plain_text"] for t in prop["title"])
    hook_visual = ""
    if concept_id:
        shots = parse_storyboard(concept_id)
        hook_visual = _primary_beat(shots[0]["visual"]) if shots else ""

    blocks = cover_blocks(persona, title, hook_visual)
    result = call("PATCH", f"/blocks/{row_id}/children", {"children": blocks})
    for b in result["results"]:
        if b["type"] == "toggle":
            return b["id"]
    raise RuntimeError(f"cover_blocks() PATCH for {row_id} returned no toggle block")


def upload_image_to_toggle(toggle_id: str, path: Path) -> None:
    key = os.environ.get("NOTION_KEY", "").strip()
    if not key:
        sys.exit("[error] NOTION_KEY not set")
    headers = {"Authorization": f"Bearer {key}", "Notion-Version": "2022-06-28"}

    upload = call("POST", "/file_uploads", {"filename": path.name, "content_type": "image/png"})
    bnd = "----up" + uuid.uuid4().hex
    ctype = mimetypes.guess_type(path.name)[0] or "image/png"
    body = (
        f"--{bnd}\r\n".encode()
        + f'Content-Disposition: form-data; name="file"; filename="{path.name}"\r\n'.encode()
        + f"Content-Type: {ctype}\r\n\r\n".encode()
        + path.read_bytes()
        + b"\r\n"
        + f"--{bnd}--\r\n".encode()
    )
    hh = dict(headers)
    hh["Content-Type"] = f"multipart/form-data; boundary={bnd}"
    req = urllib.request.Request(upload["upload_url"], data=body, headers=hh, method="POST")
    with urllib.request.urlopen(req, timeout=60) as r:
        r.read()

    img_block = {
        "object": "block", "type": "image",
        "image": {"type": "file_upload", "file_upload": {"id": upload["id"]}},
    }
    call("PATCH", f"/blocks/{toggle_id}/children", {"children": [img_block]})


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    for filename, (row_id, label) in MATCHES.items():
        path = DOWNLOADS / filename
        print(f"\n=== {filename} -> {label} ===")
        if not path.exists():
            print(f"  [skip] file not found: {path}")
            continue

        toggle_id = find_cover_toggle(row_id)
        if toggle_id is not None and toggle_has_image(toggle_id):
            print("  [skip] toggle already has an image — not overwriting")
            continue

        if args.dry_run:
            if toggle_id is None:
                print("  [would] add a new 🖼️ Cover Photo section, then upload into it")
            else:
                print(f"  [would] upload into existing empty toggle {toggle_id}")
            continue

        if toggle_id is None:
            print("  [info] no 🖼️ Cover Photo section on this row yet — adding one")
            toggle_id = add_cover_section(row_id)
            time.sleep(0.3)

        print(f"  [uploading] -> toggle {toggle_id}")
        upload_image_to_toggle(toggle_id, path)
        print("  ✅ uploaded")
        time.sleep(0.4)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
