#!/usr/bin/env python3
"""
build_content_bodies.py — fill EMPTY Content Library concepts with the full
Structure, matching the gold-standard format of "🤯 Which Type of Migraine":

  📜 Master Script (EN)   — bulleted script lines
  🎬 Shot Guide           — Shot N · ~Xs · beat  →  🎥 visual / 🗣️ voice / 💡 caption
  📩 PROTOCOL (Material)   — 💬 First DM (text) · 🖼️ Infographic Brief (GPT) · 💬 Second DM

Content authored in scripts/content_bodies_data.py (CONCEPTS, keyed by exact title).
Page ids resolved from /tmp/empty_seeds.json (title -> id).

SAFETY: refuses to write a page that already has body blocks (won't clobber
existing scripts/media). Use --force to override.

Usage:
  python3 scripts/build_content_bodies.py                # all concepts in data file
  python3 scripts/build_content_bodies.py --only "Tonsil Stones"   # substring match
  python3 scripts/build_content_bodies.py --dry          # print block plan, no write
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
import notion_video as nv  # reuses ncall / ncall_w / _children / NOTION_KEY loading

from content_bodies_data import CONCEPTS


# ── Notion block builders ────────────────────────────────────────────────────
def _rt(text: str) -> list:
    return [{"type": "text", "text": {"content": text}}]


def h2(text: str) -> dict:
    return {"object": "block", "type": "heading_2",
            "heading_2": {"rich_text": _rt(text)}}


def h3(text: str) -> dict:
    return {"object": "block", "type": "heading_3",
            "heading_3": {"rich_text": _rt(text)}}


def bullet(text: str) -> dict:
    return {"object": "block", "type": "bulleted_list_item",
            "bulleted_list_item": {"rich_text": _rt(text)}}


def divider() -> dict:
    return {"object": "block", "type": "divider", "divider": {}}


def callout(text: str, emoji: str = "📩") -> dict:
    return {"object": "block", "type": "callout",
            "callout": {"rich_text": _rt(text), "icon": {"type": "emoji", "emoji": emoji}}}


def code(text: str) -> dict:
    return {"object": "block", "type": "code",
            "code": {"rich_text": _rt(text), "language": "plain text"}}


# ── Assemble one concept's body ──────────────────────────────────────────────
def build_blocks(c: dict) -> list:
    blocks: list = []

    # 1. Master Script
    blocks.append(h2("📜 Master Script (EN)"))
    for line in c["master_script"]:
        blocks.append(bullet(line))
    blocks.append(divider())

    # 2. Shot Guide
    blocks.append(h2("🎬 Shot Guide"))
    for s in c["shots"]:
        blocks.append(h3(f"Shot {s['n']} · ~{s['secs']}s · {s['beat']}"))
        blocks.append(bullet(f"🎥 {s['visual']}"))
        blocks.append(bullet(f"🗣️ {s['voice']}"))
        blocks.append(bullet(f"💡 {s['caption']}"))
    blocks.append(divider())

    # 3. Material — DM protocol
    blocks.append(callout(
        "📩 PROTOCOL — DM flow triggered when viewer comments the CTA keyword. "
        "First DM = instant text. After any reply, send the infographic + second DM.",
        "📩"))
    blocks.append(h3("💬 First DM — send immediately (text only)"))
    blocks.append(code(c["first_dm"]))
    blocks.append(h3("🖼️ Infographic Brief — paste into GPT image gen"))
    blocks.append(code(c["infographic_brief"]))
    blocks.append(h3("💬 Second DM — send after any reply (attach infographic)"))
    blocks.append(code(c["second_dm"]))

    return blocks


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--only", help="substring match on title")
    ap.add_argument("--dry", action="store_true")
    ap.add_argument("--force", action="store_true", help="write even if body exists")
    args = ap.parse_args()

    seeds = json.load(open("/tmp/empty_seeds.json"))
    id_by_title = {s["title"]: s["id"] for s in seeds}
    # also allow filled concepts (not in empty_seeds) via a full title->id map
    all_rows = json.load(open("/tmp/content_rows.json"))
    id_by_title.update({r["title"]: r["id"] for r in all_rows})

    written = skipped = missing = 0
    for c in CONCEPTS:
        title = c["title"]
        if args.only and args.only.lower() not in title.lower():
            continue
        pid = id_by_title.get(title)
        if not pid:
            print(f"  ✗ NO PAGE: {title}"); missing += 1; continue

        blocks = build_blocks(c)
        if args.dry:
            print(f"\n=== {title} ({len(blocks)} blocks) ===")
            for b in blocks:
                t = b["type"]
                tx = "".join(x["text"]["content"] for x in b.get(t, {}).get("rich_text", []))
                print(f"  [{t}] {tx[:70]}")
            written += 1
            continue

        existing = nv._children(pid)
        if existing and not args.force:
            print(f"  ⏭  HAS BODY ({len(existing)} blocks), skip: {title}")
            skipped += 1
            continue

        nv.ncall_w("PATCH", f"/blocks/{pid}/children", {"children": blocks})
        print(f"  ✅ wrote {len(blocks)} blocks: {title}")
        written += 1

    print(f"\nwritten={written} skipped={skipped} missing={missing}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
