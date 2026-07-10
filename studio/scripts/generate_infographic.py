#!/usr/bin/env python3
"""generate_infographic.py — generate the 📊 DM Infographic image for ONE
Production row, independent of the (currently broken — dangling `server/`
path) dm_map.json batch pipeline in batch_infographic_gen.py.

apply_shot_plan() already copies the Content page's "🖼️ Infographic Brief"
code block verbatim into every row's "📊 DM Infographic" section as prompt
TEXT (fetch_infographic_brief() in notion_prompts.py) — but nothing calls
the image API per row. This is that missing step, scoped to one row so it
fits as its own review checkpoint (no reference photos needed: the brief
itself mandates "illustration style, NOT photorealistic, no real faces").

Idempotent: skips if a "🖼️ Infographic here" toggle already has an image
(pass --force to regenerate). Refuses to generate against the placeholder
text (no brief written on the Content page yet).

Usage:
    python3 scripts/generate_infographic.py --row <production_page_id>
    python3 scripts/generate_infographic.py --row <id> --force
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import notion_image as ni  # noqa: E402 - reuse upload_image / _children / _campaign_workdir
from notion_prompts import NO_BRIEF_PLACEHOLDER  # noqa: E402

ROOT = ni.ROOT
_SIZE = "1024x1536"  # portrait — matches batch_infographic_gen.py's convention


def gen_infographic_image(prompt: str, out_path: str) -> str:
    """Text-to-image (no reference photos) via /v1/images/generations — NOT
    notion_image.py's gen_image(), which hits /v1/images/edits and requires at
    least one reference image. An infographic has no identity to preserve
    (the brief itself mandates illustration style, no real faces), so this
    mirrors batch_infographic_gen.py's _openai_generate() instead."""
    import base64
    import json as _json
    import os
    import urllib.error
    import urllib.request

    key = os.environ.get("OPENAI_API_KEY", "").strip()
    if not key:
        sys.exit("[error] OPENAI_API_KEY not set")
    model = os.environ.get("IMAGE_MODEL", "gpt-image-2")
    body = _json.dumps({"model": model, "prompt": prompt, "size": _SIZE, "n": 1}).encode()
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


def find_infographic_prompt(row_id: str) -> tuple[str | None, str | None, bool]:
    """Return (prompt_text, toggle_id_or_None, has_image_bool) for the row's
    '📊 DM Infographic' section."""
    in_section, want_code, prompt = False, False, None
    toggle_id, has_image = None, False
    for b in ni._children(row_id):
        t = b["type"]
        tx = ni._txt(b)
        if t == "heading_3":
            in_section = "dm infographic" in tx.casefold()
            continue
        if not in_section:
            continue
        if t == "paragraph" and "infographic prompt" in tx.casefold():
            want_code = True
        elif want_code and t == "code":
            prompt = tx
            want_code = False
        elif t == "toggle" and "infographic here" in tx.casefold():
            toggle_id = b["id"]
            children = ni._children(b["id"]) if b.get("has_children") else []
            has_image = any(c["type"] == "image" for c in children)
    return prompt, toggle_id, has_image


def _infographic_prompt_code_id(row_id: str) -> str | None:
    in_section, want_code = False, False
    for b in ni._children(row_id):
        t = b["type"]
        tx = ni._txt(b)
        if t == "heading_3":
            in_section = "dm infographic" in tx.casefold()
            continue
        if not in_section:
            continue
        if t == "paragraph" and "infographic prompt" in tx.casefold():
            want_code = True
        elif want_code and t == "code":
            return b["id"]
    return None


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--row", required=True, help="Production row page id")
    ap.add_argument("--force", action="store_true", help="regenerate even if an image already exists")
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    page = ni.ncall("GET", f"/pages/{args.row}")
    ip_rel = page["properties"].get("IP", {}).get("relation", [])
    ip_name = ni.short_ip("".join(t["plain_text"] for t in
                          ni.ncall("GET", f"/pages/{ip_rel[0]['id']}")["properties"]["IP"]["title"])) if ip_rel else ""

    prompt, toggle_id, has_image = find_infographic_prompt(args.row)
    if not prompt:
        sys.exit("[error] no '🖼️ Infographic prompt' code block found under '📊 DM Infographic' — "
                 "run apply_shot_plan / backfill_cover_dm_prompts.py on this row first")
    if prompt.strip() == NO_BRIEF_PLACEHOLDER:
        sys.exit("[blocked] no Infographic Brief on the linked Content page yet — "
                 "add '🖼️ Infographic Brief' there, then re-sync this row before generating.")
    if has_image and not args.force:
        print("Infographic already present — skip (pass --force to regenerate)")
        return 0

    print(f"row IP: {ip_name or '?'}")
    print(f"  infographic prompt: {prompt[:80]}…")
    if args.dry_run:
        print("[dry-run] would generate + upload now")
        return 0

    outdir = ni._campaign_workdir(page, ip_name) / "images"
    outdir.mkdir(parents=True, exist_ok=True)
    out_path = str(outdir / "infographic.png")
    # No reference images — the brief itself demands illustration style, no real faces.
    out = gen_infographic_image(prompt, out_path)
    fid = ni.upload_image(out)
    img_block = {"object": "block", "type": "image",
                 "image": {"type": "file_upload", "file_upload": {"id": fid}}}

    if toggle_id:
        if has_image:  # --force: clear existing children first
            for c in ni._children(toggle_id):
                ni.ncall("DELETE", f"/blocks/{c['id']}")
        ni.ncall("PATCH", f"/blocks/{toggle_id}/children", {"children": [img_block]})
    else:
        toggle = {"object": "block", "type": "toggle",
                  "toggle": {"rich_text": [{"type": "text", "text": {"content": "🖼️ Infographic here"}}],
                            "children": [img_block]}}
        body = {"children": [toggle]}
        anchor = _infographic_prompt_code_id(args.row)
        if anchor:
            body["after"] = anchor
        ni.ncall("PATCH", f"/blocks/{args.row}/children", body)

    print(f"✅ infographic generated → {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
