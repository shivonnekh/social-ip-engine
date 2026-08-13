#!/usr/bin/env python3
"""notion_carousel_image.py — generate the panel images for ONE Production
row's 🎠 Carousel Panels section (written by
`notion_carousel_prompts.apply_carousel_plan()`).

Sibling of `notion_image.py` (video shots), but simpler: carousel panels are
illustration-style with no real faces (the shared brand style mandates this
— see `notion_carousel_prompts.DEFAULT_CAROUSEL_STYLE`), so generation is
text-to-image via `/v1/images/generations` with NO reference photos — the
same reasoning `generate_infographic.py` already applies to the DM
infographic, whose `gen_infographic_image()` this file's `gen_panel_image()`
is a close clone of, with the size changed to
`notion_carousel_prompts.CAROUSEL_PANEL_SIZE` (1024x1024, mandatory — see
that module's ASPECT RATIO docstring section).

Idempotent per panel: skips a panel that already has an image unless
`--force` (which, combined with `--panel N`, regenerates only that one
panel — mirrors `notion_image.py`'s `--force` contract: a full-row run
never overwrites existing panels, only a targeted `--panel N --force`
does). Ticks the row's `🎠 Carousel` checkbox only on a full-row run where
every panel ends up with an image (mirrors `notion_image.py`'s identical
tick-only-on-full-row-run behavior).

Usage:
    python3 scripts/notion_carousel_image.py --row <production_page_id>
    python3 scripts/notion_carousel_image.py --row <id> --panel 3
    python3 scripts/notion_carousel_image.py --row <id> --panel 3 --force
    python3 scripts/notion_carousel_image.py --row <id> --dry-run
"""
from __future__ import annotations

import argparse
import base64
import json as _json
import os
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import notion_image as ni  # noqa: E402 - reuse ncall / _children / _txt / upload_image / _campaign_workdir
from notion_carousel_prompts import CAROUSEL_PANEL_SIZE, CAROUSEL_SENTINEL  # noqa: E402

ROOT = ni.ROOT


def gen_panel_image(prompt: str, out_path: str) -> str:
    """Text-to-image (no reference photos) via /v1/images/generations —
    close clone of `generate_infographic.gen_infographic_image()`, with the
    size swapped to CAROUSEL_PANEL_SIZE (1024x1024, square — see this
    module's docstring for why that's mandatory, not a style choice)."""
    key = os.environ.get("OPENAI_API_KEY", "").strip()
    if not key:
        sys.exit("[error] OPENAI_API_KEY not set")
    model = os.environ.get("IMAGE_MODEL", "gpt-image-2")
    body = _json.dumps({"model": model, "prompt": prompt, "size": CAROUSEL_PANEL_SIZE, "n": 1}).encode()
    req = urllib.request.Request(
        "https://api.openai.com/v1/images/generations", data=body, method="POST",
        headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=120) as r:
            data = _json.loads(r.read().decode())
    except urllib.error.HTTPError as e:
        sys.exit(f"[openai] {e.code}: {e.read().decode()[:300]}")
    Path(out_path).write_bytes(base64.b64decode(data["data"][0]["b64_json"]))
    return out_path


def read_panels(row_id: str) -> list[dict]:
    """[{title, prompt, toggle_id, has_image}] parsed from the row's
    🎠 Carousel Panels section — same heading_3 → paragraph("Panel prompt")
    → code → toggle("Panel here") shape `carousel_blocks()` writes.
    Returns [] for a row with no carousel section (most rows — carousels
    are opt-in per concept), which callers must treat as "nothing to do
    here," not an error."""
    in_section, panels, cur, want = False, [], None, False
    for b in ni._children(row_id):
        t, tx = b["type"], ni._txt(b)
        if t == "callout" and CAROUSEL_SENTINEL in tx:
            in_section = True
            continue
        if not in_section:
            continue
        if t == "heading_3":
            cur = {"title": tx, "prompt": "", "toggle_id": None, "has_image": False}
            panels.append(cur)
            want = False
        elif t == "paragraph" and "Panel prompt" in tx:
            want = True
        elif want and t == "code" and cur is not None:
            cur["prompt"] = tx
            want = False
        elif t == "toggle" and "Panel here" in tx and cur is not None:
            cur["toggle_id"] = b["id"]
            has_img = b.get("has_children") and any(
                c["type"] == "image" for c in ni._children(b["id"]))
            cur["has_image"] = bool(has_img)
    return [p for p in panels if p["prompt"]]


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--row", required=True, help="Production row page id")
    ap.add_argument("--panel", type=int, help="process only panel N (1-based, useful for targeted retry)")
    ap.add_argument("--force", action="store_true",
                     help="regenerate --panel N even if it already has an image (deletes the old one "
                          "first). Requires --panel; a full-row run never overwrites existing panels.")
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    if args.force and not args.panel:
        sys.exit("[error] --force requires --panel N — a full-row run never overwrites existing panels")

    page = ni.ncall("GET", f"/pages/{args.row}")
    ip_rel = page["properties"].get("IP", {}).get("relation", [])
    ip_title_raw = ("".join(t["plain_text"] for t in
                    ni.ncall("GET", f"/pages/{ip_rel[0]['id']}")["properties"]["IP"]["title"])) if ip_rel else ""
    ip_name = ni.short_ip(ip_title_raw)

    panels = read_panels(args.row)
    print(f"row IP: {ip_name or '?'} | panels: {len(panels)}")
    if not panels:
        print("[nothing to do] no '🎠 Carousel Panels' section on this row — "
              "run notion_carousel_prompts.apply_carousel_plan() first, or this "
              "concept has no Carousel Guide (most rows are video-only)")
        return 0

    outdir = ni._campaign_workdir(page, ip_title_raw) / "carousel"
    outdir.mkdir(parents=True, exist_ok=True)

    done = 0
    for i, p in enumerate(panels, 1):
        if args.panel and i != args.panel:
            continue
        if p["has_image"] and not (args.force and args.panel == i):
            print(f"  Panel {i}: image already present — skip")
            continue
        if p["has_image"] and args.force:
            print(f"  Panel {i}: image already present — --force set, regenerating anyway")
            for c in ni._children(p["toggle_id"]):
                if c["type"] == "image":
                    ni.ncall("DELETE", f"/blocks/{c['id']}")
        out_path = str(outdir / f"panel{i}.png")
        print(f"  Panel {i}: {p['title']} | square {CAROUSEL_PANEL_SIZE} | gen from THIS panel's Notion prompt")
        if args.dry_run:
            continue
        out = gen_panel_image(p["prompt"], out_path)
        fid = ni.upload_image(out)
        img_block = {"object": "block", "type": "image",
                     "image": {"type": "file_upload", "file_upload": {"id": fid}}}
        if p["toggle_id"]:
            ni.ncall("PATCH", f"/blocks/{p['toggle_id']}/children", {"children": [img_block]})
        else:
            print(f"    ⚠️  Panel {i} has no '🖼️ Panel here' toggle — skipping placement "
                  "(re-run apply_carousel_plan to rebuild the section)")
            continue
        print(f"    ✅ Panel {i} → 🖼️ Panel here ({out})")
        done += 1
        time.sleep(0.4)

    if not args.dry_run and not args.panel:
        # Re-check each panel's toggle rather than trusting `p["has_image"]"`
        # — that reflects state BEFORE this run and would under-report on a
        # fresh full-row generation (every panel starts False).
        if all(_still_has_image(args.row, p) for p in panels):
            ni.ncall("PATCH", f"/pages/{args.row}", {"properties": {"🎠 Carousel": {"checkbox": True}}})
            print("✅ all panels have images + 🎠 ticked")
    return 0


def _still_has_image(row_id: str, panel: dict) -> bool:
    """Re-check a panel's toggle for an image AFTER this run's writes —
    `panel["has_image"]` reflects the state BEFORE this run, which would
    under-report on a fresh full-row generation (every panel starts False,
    gets filled during the loop above). Cheap re-read, one row's worth of
    panels, only on the tick-check path."""
    if not panel["toggle_id"]:
        return False
    return any(c["type"] == "image" for c in ni._children(panel["toggle_id"]))


if __name__ == "__main__":
    raise SystemExit(main())
