#!/usr/bin/env python3
"""
upload_infographics_to_notion.py — upload per-IP infographics to Production Tracker rows.

For each Production row:
  1. Follows the Content relation → gets CTA keyword
  2. Finds the matching local PNG in campaigns/assets/dm-infographics/<keyword>.png
  3. Uploads to Notion + appends a "📊 DM Infographic" toggle to the row body
  4. Skips rows that already have the toggle

Infographics are per-IP: campaigns/assets/dm-infographics/<keyword>.png is English (Jackie).
When Jessica infographics exist, add them to campaigns/assets/dm-infographics/jessica/<keyword>.png
and this script will pick them up automatically.

Usage:
    python3 scripts/upload_infographics_to_notion.py
    python3 scripts/upload_infographics_to_notion.py --ip Jackie
    python3 scripts/upload_infographics_to_notion.py --dry-run
    python3 scripts/upload_infographics_to_notion.py --force   # re-upload even if toggle exists
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))

import notion_video as nv  # reuse ncall_w, _children, _txt

IDS_PATH = ROOT / "scripts" / "notion_ids.json"
IDS = json.loads(IDS_PATH.read_text(encoding="utf-8"))

# Where local infographic PNGs live (flat, English/Jackie)
INFOGRAPHIC_DIR = ROOT / "campaigns" / "assets" / "dm-infographics"

_STOP = {"comment", "the", "word", "below", "type", "now"}


# ── helpers ────────────────────────────────────────────────────────────────────

def _normalize_keyword(cta: str) -> str:
    if not cta:
        return ""
    m = re.search(r"[\"'""'']([^\"'""'']+)[\"'""'']", cta)
    if m:
        return m.group(1).strip().lower().split()[0]
    tokens = re.findall(r"[a-zA-Z]+", cta.lower())
    for tok in tokens:
        if tok not in _STOP:
            return tok
    return tokens[0] if tokens else ""


def _title(page: dict) -> str:
    for prop in page["properties"].values():
        if prop.get("type") == "title":
            return "".join(t["plain_text"] for t in prop["title"])
    return ""


def _query_all(db: str) -> list[dict]:
    rows, cursor = [], None
    while True:
        body: dict = {"page_size": 100}
        if cursor:
            body["start_cursor"] = cursor
        d = nv.ncall_w("POST", f"/databases/{db}/query", body)
        rows += d["results"]
        if not d.get("has_more"):
            return rows
        cursor = d["next_cursor"]


def _short_ip(full: str) -> str:
    base = full.split("(")[0].strip()
    return " ".join(p for p in base.split() if not all(ord(c) > 0x2000 for c in p)) or base


def _ip_slug(full: str) -> str:
    """Map IP name to the subfolder name used under campaigns/assets/dm-infographics/."""
    name = _short_ip(full).lower()
    if "jackie" in name:
        return "jackie"
    if "chloe" in name:
        return "chloe"
    return re.sub(r"[^a-z0-9]+", "-", name).strip("-")


def _infographic_path(ip_full: str, keyword: str) -> Path | None:
    """Return local PNG path for this IP + keyword, or None if not found."""
    slug = _ip_slug(ip_full)
    # Per-IP subfolder first (future: jessica/migraine.png)
    per_ip = INFOGRAPHIC_DIR / slug / f"{keyword}.png"
    if per_ip.exists():
        return per_ip
    # Flat fallback (Jackie's English images live directly in dm-infographics/)
    flat = INFOGRAPHIC_DIR / f"{keyword}.png"
    if flat.exists() and slug == "jackie":
        return flat
    return None


def _has_infographic_toggle(row_id: str) -> bool:
    """Check if this Production row already has a 📊 DM Infographic toggle."""
    for b in nv._children(row_id):
        if b["type"] == "toggle" and "DM Infographic" in nv._txt(b):
            return True
    return False


def _upload_to_notion(path: Path) -> str:
    """Upload a PNG to Notion and return the file_upload id."""
    h = {"Authorization": f"Bearer {os.environ['NOTION_KEY']}", "Notion-Version": "2022-06-28"}
    # Step 1: create upload slot
    req = urllib.request.Request(
        "https://api.notion.com/v1/file_uploads",
        data=json.dumps({"filename": path.name, "content_type": "image/png"}).encode(),
        headers={**h, "Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            meta = json.loads(r.read().decode())
    except urllib.error.HTTPError as exc:
        raise RuntimeError(f"Notion file_uploads: {exc.code} {exc.read().decode()[:200]}") from exc

    # Step 2: upload bytes
    bnd = "----up" + meta["id"].replace("-", "")
    body = (
        f"--{bnd}\r\nContent-Disposition: form-data; name=\"file\"; filename=\"{path.name}\"\r\n"
        f"Content-Type: image/png\r\n\r\n"
    ).encode() + path.read_bytes() + f"\r\n--{bnd}--\r\n".encode()
    up_req = urllib.request.Request(
        meta["upload_url"],
        data=body,
        headers={**h, "Content-Type": f"multipart/form-data; boundary={bnd}"},
        method="POST",
    )
    try:
        urllib.request.urlopen(up_req, timeout=120)
    except urllib.error.HTTPError as exc:
        raise RuntimeError(f"Notion upload PUT: {exc.code} {exc.read().decode()[:200]}") from exc

    return meta["id"]


def _append_infographic_toggle(row_id: str, file_upload_id: str) -> None:
    """Append a 📊 DM Infographic toggle with the uploaded image to the row body."""
    img_block = {
        "object": "block",
        "type": "image",
        "image": {"type": "file_upload", "file_upload": {"id": file_upload_id}},
    }
    toggle = {
        "object": "block",
        "type": "toggle",
        "toggle": {
            "rich_text": [{"type": "text", "text": {"content": "📊 DM Infographic"}}],
            "children": [img_block],
        },
    }
    nv.ncall_w("PATCH", f"/blocks/{row_id}/children", {"children": [toggle]})


# ── main ───────────────────────────────────────────────────────────────────────

def main() -> int:
    ap = argparse.ArgumentParser(description="Upload infographics to Production Tracker rows")
    ap.add_argument("--ip", help="Filter to IP name substring (e.g. Jackie, Jessica)")
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--force", action="store_true", help="Re-upload even if toggle already exists")
    args = ap.parse_args()

    key = os.environ.get("NOTION_KEY", "").strip()
    if not key:
        sys.exit("[error] NOTION_KEY not set")

    print("[query] fetching Production Tracker rows ...")
    prod_rows = _query_all(IDS["prod_db"])
    print(f"[query] {len(prod_rows)} rows total")

    done = skipped = missing = errors = 0

    for row in prod_rows:
        row_id = row["id"]
        row_name = _title(row)

        # Get IP
        ip_rel = row["properties"].get("IP", {}).get("relation", [])
        if not ip_rel:
            continue
        ip_page = nv.ncall_w("GET", f"/pages/{ip_rel[0]['id']}")
        ip_full = _title(ip_page)

        if args.ip and args.ip.lower() not in ip_full.lower():
            continue

        # Get CTA keyword from Content Library
        content_rel = row["properties"].get("Content", {}).get("relation", [])
        if not content_rel:
            continue
        content_page = nv.ncall_w("GET", f"/pages/{content_rel[0]['id']}")
        cta = "".join(
            t["plain_text"]
            for t in content_page["properties"].get("CTA", {}).get("rich_text", [])
        )
        keyword = _normalize_keyword(cta)
        if not keyword:
            print(f"  [skip] {row_name} — no CTA keyword")
            skipped += 1
            continue

        # Find infographic PNG
        png = _infographic_path(ip_full, keyword)
        if not png:
            print(f"  [missing] {row_name} — no PNG for keyword={keyword} ip={_ip_slug(ip_full)}")
            missing += 1
            continue

        # Check if already uploaded
        if not args.force and _has_infographic_toggle(row_id):
            print(f"  [exists] {row_name} (keyword={keyword}) — toggle already present")
            skipped += 1
            continue

        print(f"  [upload] {row_name}")
        print(f"           keyword={keyword}  png={png.name}  ({png.stat().st_size // 1024}KB)")

        if args.dry_run:
            done += 1
            continue

        try:
            fid = _upload_to_notion(png)
            _append_infographic_toggle(row_id, fid)
            print(f"           ✅ uploaded → 📊 DM Infographic toggle added")
            done += 1
        except Exception as exc:  # noqa: BLE001
            print(f"           ❌ error: {exc}")
            errors += 1

        time.sleep(0.5)

    label = "dry-run: would upload" if args.dry_run else "uploaded"
    print(f"\n{label} {done}  |  skipped {skipped}  |  missing PNG {missing}  |  errors {errors}")
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
