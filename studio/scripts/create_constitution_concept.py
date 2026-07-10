#!/usr/bin/env python3
"""Create the "Hot or Cold Constitution Self-Check" Content Library concept.

Sourced from the 2026-07 TCM viral-content research pass (cross-platform
overlap: IG + TikTok + Reddit all converge on hot/cold constitution typing
as the single most durable, non-fad TCM content topic). This is content
angle #1 of 5 identified — the safest first pick because it needs zero
physical technique demo, so it's low-risk for AI-avatar video production.

Created with: Properties (Name, Topic, Hook, CTA, Concept Status = "✍️ Scripted")
+ Body (📜 Master Script (EN) + 🎬 Shot Guide), same shape as
batch_create_concepts.py so notion_fanout.py can explode it per-IP later.

Idempotent — skips if a concept with a matching name already exists.

Usage:
    export NOTION_KEY=ntn_...
    python3 scripts/create_constitution_concept.py
    python3 scripts/create_constitution_concept.py --dry-run   # preview only
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

BASE = "https://api.notion.com/v1"
IDS_PATH = Path(__file__).resolve().parent / "notion_ids.json"


def _load_key() -> str:
    key = os.environ.get("NOTION_KEY", "").strip()
    if key:
        return key
    envp = Path(__file__).resolve().parent.parent / ".env"
    if envp.exists():
        for line in envp.read_text(encoding="utf-8").splitlines():
            if line.strip().startswith("NOTION_KEY="):
                return line.split("=", 1)[1].strip()
    sys.exit("[error] NOTION_KEY not found in env or .env")


def _headers() -> dict[str, str]:
    return {
        "Authorization": f"Bearer {_load_key()}",
        "Notion-Version": "2022-06-28",
        "Content-Type": "application/json",
    }


def call(method: str, path: str, body: dict | None = None, retries: int = 5) -> dict:
    data = json.dumps(body).encode() if body is not None else None
    for attempt in range(retries):
        req = urllib.request.Request(
            f"{BASE}{path}", data=data, headers=_headers(), method=method
        )
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


def _rt(text: str) -> list[dict]:
    return [{"type": "text", "text": {"content": text}}]


def _h2(text: str) -> dict:
    return {"object": "block", "type": "heading_2",
            "heading_2": {"rich_text": _rt(text)}}


def _h3(text: str) -> dict:
    return {"object": "block", "type": "heading_3",
            "heading_3": {"rich_text": _rt(text)}}


def _bullet(text: str) -> dict:
    return {"object": "block", "type": "bulleted_list_item",
            "bulleted_list_item": {"rich_text": _rt(text)}}


def _divider() -> dict:
    return {"object": "block", "type": "divider", "divider": {}}


def build_body_blocks(concept: dict) -> list[dict]:
    blocks: list[dict] = []

    blocks.append(_h2("📜 Master Script (EN)"))
    for line in concept["master_script_en"]:
        blocks.append(_bullet(line))

    blocks.append(_divider())

    blocks.append(_h2("🎬 Shot Guide"))
    for shot in concept["shots"]:
        blocks.append(_h3(shot["title"]))
        blocks.append(_bullet(f"🎥 {shot['visual']}"))
        blocks.append(_bullet(f"🗣️ {shot['script']}"))
        if shot.get("overlay"):
            blocks.append(_bullet(f"💡 {shot['overlay']}"))

    return blocks


def get_existing_names(content_db_id: str) -> set[str]:
    names: set[str] = set()
    cursor: str | None = None
    while True:
        body: dict = {"page_size": 100}
        if cursor:
            body["start_cursor"] = cursor
        data = call("POST", f"/databases/{content_db_id}/query", body)
        for page in data["results"]:
            for prop in page["properties"].values():
                if prop.get("type") == "title":
                    names.add("".join(t["plain_text"] for t in prop["title"]))
        if data.get("has_more"):
            cursor = data["next_cursor"]
        else:
            break
    return names


def create_concept(content_db_id: str, concept: dict, *, dry_run: bool = False) -> str:
    if dry_run:
        return "dry-run (would create)"

    page = call("POST", "/pages", {
        "parent": {"database_id": content_db_id},
        "properties": {
            "Name": {"title": _rt(concept["name"])},
            "Topic": {"select": {"name": concept["topic"]}},
            "Hook": {"rich_text": _rt(concept["hook"])},
            "CTA": {"rich_text": _rt(concept["cta"])},
            "Concept Status": {"select": {"name": "✍️ Scripted"}},
        },
    })
    page_id = page["id"]

    blocks = build_body_blocks(concept)
    for i in range(0, len(blocks), 25):
        call("PATCH", f"/blocks/{page_id}/children", {"children": blocks[i:i + 25]})
        time.sleep(0.3)

    return page_id


# ─── Content definition ────────────────────────────────────────────────────

CONCEPT: dict = {
    "name": "🌡️ Are You Hot or Cold? — Your TCM Body Type",
    "topic": "🌡️ Body Constitution",
    "hook": "Before we talk about symptoms — are you a hot body or a cold body? Most people have never checked, and it changes everything you should eat.",
    "cta": "type",
    "master_script_en": [
        "Before we talk about your symptoms, let's check one thing first: are you a hot body or a cold body? In TCM this is your 體質 — your constitution — and most people have never actually checked it.",
        "Hot signs: you're always thirsty, your face flushes easily, you hate the heat, your urine runs dark. Cold signs: your hands and feet are always cold, you look pale, you crave hot drinks, and you feel drained even after resting.",
        "If you're hot — cool down with mung bean, chrysanthemum tea, bitter melon. If you're cold — warm up with ginger, cinnamon, red dates. Eating against your type is why some 'healthy' foods make you feel worse.",
        "Comment 'type' and I'll send you the full self-check quiz plus your personalized food list.",
    ],
    "shots": [
        {
            "title": "Shot 1 · ~10s · Hook",
            "visual": "Doctor direct to camera in warm clinic light, calm and curious energy; quick insert: split-screen of a glass of ice water vs a steaming cup of tea; cut back to doctor with a knowing, raised-eyebrow look.",
            "script": "Before we talk about your symptoms, let's check one thing first: are you a hot body or a cold body? In TCM this is your 體質 — your constitution — and most people have never actually checked it.",
            "overlay": "🔥 Hot or ❄️ Cold? Check first.",
        },
        {
            "title": "Shot 2 · ~12s · Self-Check Signs",
            "visual": "Split-screen while doctor voice-over continues: left side stacks hot-sign icons (flushed face, dark glass of water, fanning motion), right side stacks cold-sign icons (hands rubbing together, pale face, blanket); doctor gestures alternately left and right.",
            "script": "Hot signs: you're always thirsty, your face flushes easily, you hate the heat, your urine runs dark. Cold signs: your hands and feet are always cold, you look pale, you crave hot drinks, and you feel drained even after resting.",
            "overlay": "🔥 Hot: thirsty · flushed · dark urine  |  ❄️ Cold: cold hands · pale · drained",
        },
        {
            "title": "Shot 3 · ~12s · TCM Fix By Type",
            "visual": "Doctor at clinic table with two ingredient sets laid out side by side — cooling foods on the left (mung bean, chrysanthemum flowers, bitter melon), warming foods on the right (ginger root, cinnamon bark, red dates); doctor picks up one item from each side in turn.",
            "script": "If you're hot — cool down with mung bean, chrysanthemum tea, bitter melon. If you're cold — warm up with ginger, cinnamon, red dates. Eating against your type is why some 'healthy' foods make you feel worse.",
            "overlay": "🔥 Cool down: 綠豆 · 菊花 · 苦瓜   ❄️ Warm up: 薑 · 桂皮 · 紅棗",
        },
        {
            "title": "Shot 4 · ~8s · CTA",
            "visual": "Doctor direct to camera, warm smile, slight lean forward toward the lens.",
            "script": "Comment 'type' and I'll send you the full self-check quiz plus your personalized food list.",
            "overlay": "Comment 👇 type",
        },
    ],
}


def main() -> int:
    ap = argparse.ArgumentParser(description="Create the hot/cold constitution concept")
    ap.add_argument("--dry-run", action="store_true", help="Preview only, no writes")
    args = ap.parse_args()

    ids = json.loads(IDS_PATH.read_text(encoding="utf-8"))
    content_db_id = ids["content_db"]

    print("Loading existing concepts from Content Library...")
    existing = get_existing_names(content_db_id)
    print(f"Found {len(existing)} existing concepts.\n")

    name = CONCEPT["name"]
    core = name.split("·")[0].strip().lstrip("🌡️💪🛡️⚡😮📱👀🤯🌙🩸📅 ")
    if any(core[:20] in ex for ex in existing):
        print(f"  ⏭  Skip (exists): {name}")
        return 0

    print(f"  ✍️  Creating: {name} ...", end="", flush=True)
    result = create_concept(content_db_id, CONCEPT, dry_run=args.dry_run)
    print(f" ✓ {result}")
    print(f"\n{'[DRY RUN] ' if args.dry_run else ''}Done.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
