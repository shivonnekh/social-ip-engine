#!/usr/bin/env python3
"""generate_cover.py — generate the 🖼️ Cover Photo image for ONE Production row.

Fills a real gap: apply_shot_plan() / backfill_cover_dm_prompts.py already write
the *prompt text* for the cover into every row's "🖼️ Cover Photo" section
(build_cover_prompt() in notion_prompts.py), but nothing in studio/ actually
CALLS the image API to fill the "🖼️ Cover here" toggle for a single row on
demand. The only place a cover ever got auto-generated was the live
social-ip-engine webhook's fallback-if-missing path at publish time — which
means today you never get a *review* checkpoint for the cover before it goes
out. This script is that missing manual step, mirroring notion_image.py's
per-shot generation pattern exactly (same gen_image/_multipart/upload_image
helpers, same "same person as reference photo" identity contract via the IP's
reference photos).

Idempotent: skips if the row's "🖼️ Cover here" toggle already has an image
(pass --force to regenerate).

Usage:
    python3 scripts/generate_cover.py --row <production_page_id>
    python3 scripts/generate_cover.py --row <id> --force
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import notion_image as ni  # noqa: E402 - reuse gen_image / upload_image / ip_reference_images

ROOT = ni.ROOT


def find_cover_prompt(row_id: str) -> tuple[str | None, str | None, bool]:
    """Return (prompt_text, toggle_id_or_None, has_image_bool) for the row's
    '🖼️ Cover Photo' -> '🖼️ Cover here' section (same shape cover_blocks() writes
    in notion_prompts.py / audit_cover_schema.py)."""
    in_section, want_code, prompt = False, False, None
    toggle_id, has_image = None, False
    for b in ni._children(row_id):
        t = b["type"]
        tx = ni._txt(b)
        if t == "heading_3":
            in_section = "cover photo" in tx.casefold()
            continue
        if not in_section:
            continue
        if t == "paragraph" and "cover prompt" in tx.casefold():
            want_code = True
        elif want_code and t == "code":
            prompt = tx
            want_code = False
        elif t == "toggle" and "cover here" in tx.casefold():
            toggle_id = b["id"]
            children = ni._children(b["id"]) if b.get("has_children") else []
            has_image = any(c["type"] == "image" for c in children)
    return prompt, toggle_id, has_image


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--row", required=True, help="Production row page id")
    ap.add_argument("--force", action="store_true", help="regenerate even if a cover already exists")
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    page = ni.ncall("GET", f"/pages/{args.row}")
    ip_rel = page["properties"].get("IP", {}).get("relation", [])
    ip_name = ni.short_ip("".join(t["plain_text"] for t in
                          ni.ncall("GET", f"/pages/{ip_rel[0]['id']}")["properties"]["IP"]["title"])) if ip_rel else ""
    ip_refs = ni.ip_reference_images(ip_rel[0]["id"], ROOT / "campaigns" / "assets" / "faces" / ip_name) if ip_rel else []

    prompt, toggle_id, has_image = find_cover_prompt(args.row)
    if not prompt:
        sys.exit("[error] no '🖼️ Cover prompt' code block found — run apply_shot_plan / "
                 "backfill_cover_dm_prompts.py on this row first")
    if has_image and not args.force:
        print("Cover already present — skip (pass --force to regenerate)")
        return 0
    if not ip_refs:
        print(f"[blocked] no reference images on the '{ip_name}' IP page in Notion.")
        return 1

    print(f"row IP: {ip_name or '?'} | face refs: {len(ip_refs)}")
    print(f"  cover prompt: {prompt[:80]}…")
    if args.dry_run:
        print("[dry-run] would generate + upload now")
        return 0

    outdir = ni._campaign_workdir(page, ip_name) / "images"
    outdir.mkdir(parents=True, exist_ok=True)
    out_path = str(outdir / "cover.png")
    out = ni.gen_image(prompt, ip_refs, out_path)
    fid = ni.upload_image(out)
    img_block = {"object": "block", "type": "image",
                 "image": {"type": "file_upload", "file_upload": {"id": fid}}}

    if toggle_id:
        if has_image:  # --force: clear existing children first
            for c in ni._children(toggle_id):
                ni.ncall("DELETE", f"/blocks/{c['id']}")
        ni.ncall("PATCH", f"/blocks/{toggle_id}/children", {"children": [img_block]})
    else:
        # No toggle at all — self-heal like notion_image.py does for shot images.
        toggle = {"object": "block", "type": "toggle",
                  "toggle": {"rich_text": [{"type": "text", "text": {"content": "🖼️ Cover here"}}],
                            "children": [img_block]}}
        ni.ncall("PATCH", f"/blocks/{args.row}/children", {"children": [toggle]})

    print(f"✅ cover generated → {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
