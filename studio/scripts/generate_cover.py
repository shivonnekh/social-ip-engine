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
import re
import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

sys.path.insert(0, str(Path(__file__).resolve().parent))
import notion_image as ni  # noqa: E402 - reuse gen_image / upload_image / ip_reference_images

ROOT = ni.ROOT

# Same font as add_karaoke_captions.py's on-screen text (white fill + black
# stroke) — one visual identity for every burned-in text element in the pipeline.
_TITLE_FONT_PATH = "/System/Library/Fonts/Supplemental/Arial Black.ttf"

# Targets actual emoji Unicode blocks only (misc symbols/pictographs,
# emoticons, transport, dingbats, supplemental symbols, variation selectors,
# regional indicators) — NOT a blanket non-ASCII strip, since Chloe's titles
# are Cantonese and CJK characters must survive. Arial Black has no emoji
# glyphs, so an un-stripped emoji renders as a broken tofu-box glyph (found
# 2026-07-14 on "Why Do Some Never Get Sick? 😮").
_EMOJI_RE = re.compile(
    "[" "\U0001F300-\U0001FAFF" "\U00002600-\U000027BF" "\U0001F1E6-\U0001F1FF"
    "\U00002190-\U000021FF" "\U00002B00-\U00002BFF" "\U0000FE0F" "]+"
)


def _strip_emoji(text: str) -> str:
    return _EMOJI_RE.sub("", text).strip()


def _wrap_text(draw: ImageDraw.ImageDraw, text: str, font: ImageFont.FreeTypeFont, max_width: int) -> list[str]:
    words = text.split()
    lines: list[str] = []
    cur = ""
    for w in words:
        trial = f"{cur} {w}".strip()
        bbox = draw.textbbox((0, 0), trial, font=font)
        if bbox[2] - bbox[0] <= max_width or not cur:
            cur = trial
        else:
            lines.append(cur)
            cur = w
    if cur:
        lines.append(cur)
    return lines


def overlay_cover_title(image_path: str, title: str, out_path: str) -> str:
    """Burn the row's punchy 🏷️ Title onto the cover's reserved top third.

    Root cause this fixes (found 2026-07-14): build_cover_prompt()'s own
    docstring has always said "clean space reserved for a bold title overlay
    added later" — but nothing in this codebase, local OR live (src/
    notion_cover_gen.py), ever actually added it. Every cover has been
    shipping completely bare since the feature was designed. gpt-image-2 is
    deliberately told "No on-screen text" in the prompt (AI-rendered text is
    reliably garbled/misspelled) — the title has to be composited afterward
    with a real font, same as this project already does for video captions
    (add_karaoke_captions.py: white fill, black stroke, Arial Black).

    Auto-shrinks + wraps to fit the reserved top-30%-of-frame zone (matches
    the prompt's own "top third uncluttered" instruction) without ever
    overflowing onto the subject below."""
    title = _strip_emoji(title)
    img = Image.open(image_path).convert("RGB")
    W, H = img.size
    draw = ImageDraw.Draw(img)

    margin_x = round(W * 0.08)
    max_width = W - 2 * margin_x
    top_zone_height = round(H * 0.30)

    font_size, min_font_size = 96, 40
    font = lines = None
    line_height = 0
    while font_size >= min_font_size:
        font = ImageFont.truetype(_TITLE_FONT_PATH, font_size)
        lines = _wrap_text(draw, title, font, max_width)
        line_height = font.getbbox("Ag")[3] + round(font_size * 0.28)
        if line_height * len(lines) <= top_zone_height and len(lines) <= 4:
            break
        font_size -= 4
    else:
        font = ImageFont.truetype(_TITLE_FONT_PATH, min_font_size)
        lines = _wrap_text(draw, title, font, max_width)
        line_height = font.getbbox("Ag")[3] + round(min_font_size * 0.28)

    stroke_width = max(2, round(font_size * 0.08))
    y = round(H * 0.05)
    for line in lines:
        bbox = draw.textbbox((0, 0), line, font=font, stroke_width=stroke_width)
        x = (W - (bbox[2] - bbox[0])) // 2
        draw.text((x, y), line, font=font, fill="white",
                  stroke_width=stroke_width, stroke_fill="black")
        y += line_height

    img.save(out_path)
    return out_path


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
    # The title is now baked directly into the image by gpt-image-2 itself —
    # build_cover_prompt() (rewritten 2026-07-16) asks for the actual viral-
    # thumbnail text treatment (bold black highlight box, yellow/white
    # split-color words, accent burst) reverse-engineered from Shivonne's
    # real published covers. NOT running overlay_cover_title() here anymore:
    # that PIL post-pass was yesterday's fix for "covers ship completely
    # bare" — it worked, but produced flat "plain text on a photo" results
    # that looked worse than what the model can do natively when asked
    # properly. Running both would double the text. overlay_cover_title()
    # is kept in this file as a manual fallback (e.g. the model garbles a
    # word and you want a quick fix) — just not auto-invoked.
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
