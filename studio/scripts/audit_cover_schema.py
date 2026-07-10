#!/usr/bin/env python3
"""audit_cover_schema.py — scan every Production Tracker row for the
"cover exists but in the wrong place" bug found 2026-07-08 (Dry Eyes had a
real cover uploaded 2026-06-30, but under the OLDER "🖼️ Reel Cover Photo
Image Prompt" heading + bare image block schema — invisible to
notion_publish_media.resolve_cover(), the function the live auto-publish
webhook actually calls, which only reads the NEWER "🖼️ Cover Photo" ->
"🖼️ Cover here" toggle shape).

Classifies every row into one of:
  - new_ok            — new-schema toggle exists and has an image. Nothing to do.
  - migrate           — an image exists somewhere (new toggle, OR the old bare
                         block) but NOT in a new-schema toggle WITH an image.
                         Concretely: old-schema image present, new toggle
                         missing/empty -> mirror the old image into a (new or
                         existing) new-schema toggle.
  - missing           — no cover image anywhere on the page. Flagged only,
                         never auto-generated (blind generation has no
                         character reference -- see the 2026-07-08 incident).
  - no_content_link   — row has no Content relation, can't resolve a persona
                         for a fresh cover_blocks() section if one's needed.

Usage:
    python3 scripts/audit_cover_schema.py                # all rows
    python3 scripts/audit_cover_schema.py --fix           # migrate + fix
    python3 scripts/audit_cover_schema.py --fix --ip Jackie
"""
from __future__ import annotations

import argparse
import json
import mimetypes
import os
import sys
import time
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
    _page_title,
    _primary_beat,
    _relation_id,
    _txt,
    call,
    cover_blocks,
    ip_persona,
    parse_storyboard,
)

IDS_PATH = Path(__file__).resolve().parent / "notion_ids.json"

_NEW_HEADING_MARKER = "cover photo"
_NEW_TOGGLE_MARKER = "cover here"
_OLD_HEADING_MARKER = "reel cover photo"


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


def _image_url(block: dict) -> str | None:
    image = block.get("image") or {}
    kind = image.get("type", "")
    return (image.get(kind) or {}).get("url") or None


def inspect_row(row_id: str) -> dict:
    """Walk the row body once, classifying the cover situation."""
    new_toggle_id: str | None = None
    new_toggle_has_image = False
    old_image_url: str | None = None

    in_new_section = False
    in_old_section = False
    for b in _all_children(row_id):
        t = b["type"]
        text = _txt(b).casefold()
        if t == "heading_3":
            in_new_section = _NEW_HEADING_MARKER in text and _OLD_HEADING_MARKER not in text
            in_old_section = _OLD_HEADING_MARKER in text
        elif in_new_section and t == "toggle" and _NEW_TOGGLE_MARKER in text:
            new_toggle_id = b["id"]
            children = _all_children(b["id"]) if b.get("has_children") else []
            new_toggle_has_image = any(c["type"] == "image" for c in children)
        elif in_old_section and t == "image":
            old_image_url = _image_url(b)
            in_old_section = False  # only the first image right after the heading counts

    if new_toggle_has_image:
        return {"status": "new_ok"}
    if old_image_url:
        return {"status": "migrate", "old_image_url": old_image_url, "new_toggle_id": new_toggle_id}
    return {"status": "missing", "new_toggle_id": new_toggle_id}


def ensure_new_toggle(row_id: str) -> str:
    """Return an empty new-schema toggle id, creating the section if absent."""
    page = call("GET", f"/pages/{row_id}")
    concept_id = _relation_id(page, "Content")
    ip_id = _relation_id(page, "IP")
    persona = ip_persona(ip_id)[1] if ip_id else "TCM doctor"
    title = _page_title(page)
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


def upload_url_to_toggle(toggle_id: str, image_url: str) -> None:
    """Download an existing Notion-hosted image (old-schema block) and
    re-upload the same bytes into the new-schema toggle — no regeneration,
    byte-identical mirror of already-approved art."""
    key = os.environ.get("NOTION_KEY", "").strip()
    data = urllib.request.urlopen(urllib.request.Request(image_url), timeout=30).read()

    upload = call("POST", "/file_uploads", {"filename": "cover.png", "content_type": "image/png"})
    bnd = "----up" + uuid.uuid4().hex
    body = (
        f"--{bnd}\r\n".encode()
        + b'Content-Disposition: form-data; name="file"; filename="cover.png"\r\n'
        + b"Content-Type: image/png\r\n\r\n" + data + b"\r\n"
        + f"--{bnd}--\r\n".encode()
    )
    headers = {"Authorization": f"Bearer {key}", "Notion-Version": "2022-06-28",
               "Content-Type": f"multipart/form-data; boundary={bnd}"}
    req = urllib.request.Request(upload["upload_url"], data=body, headers=headers, method="POST")
    with urllib.request.urlopen(req, timeout=60) as r:
        r.read()

    img_block = {"object": "block", "type": "image",
                 "image": {"type": "file_upload", "file_upload": {"id": upload["id"]}}}
    call("PATCH", f"/blocks/{toggle_id}/children", {"children": [img_block]})


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--fix", action="store_true", help="actually migrate/mirror covers (default: report only)")
    ap.add_argument("--ip", help="substring match on row title")
    args = ap.parse_args()

    ids = json.loads(IDS_PATH.read_text())
    rows, cursor = [], None
    while True:
        b: dict = {"page_size": 100}
        if cursor:
            b["start_cursor"] = cursor
        res = call("POST", f"/databases/{ids['prod_db']}/query", b)
        rows += res["results"]
        if not res.get("has_more"):
            break
        cursor = res["next_cursor"]

    counts = {"new_ok": 0, "migrate": 0, "missing": 0}
    for p in rows:
        title = _page_title(p)
        if args.ip and args.ip.lower() not in title.lower():
            continue
        info = inspect_row(p["id"])
        status = info["status"]
        counts[status] += 1

        if status == "new_ok":
            continue
        if status == "missing":
            print(f"  [missing]  {title[:65]:65} | no cover anywhere — not auto-generating")
            continue

        # status == migrate
        if not args.fix:
            print(f"  [migrate]  {title[:65]:65} | old-schema image found, new toggle empty/absent")
            continue

        toggle_id = info["new_toggle_id"]
        if toggle_id is None:
            toggle_id = ensure_new_toggle(p["id"])
            time.sleep(0.3)
        upload_url_to_toggle(toggle_id, info["old_image_url"])
        print(f"  ✅ [fixed]  {title[:65]:65} | mirrored old cover into new toggle {toggle_id}")
        time.sleep(0.4)

    print(f"\nnew_ok={counts['new_ok']}  migrate={counts['migrate']}  missing={counts['missing']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
