#!/usr/bin/env python3
"""Create the "Dark Circles & Eye Bags" Content Library concept.

Authored 2026-09-01 with the seedance-20 director skill (`seedance-camera` +
`[ref:directing-engine]`).

Director's read
---------------
Function : turn — viewer moves from self-blame ("I just need more sleep") to agency.
The turn : futility -> capability.
POV      : the viewer looking at their own face in the mirror at 7am.
Power    : eye-level for most of the piece — trusted elder, never lecturing down.
Subtext  : "you have been treating the wrong thing for years."
Intention: make the viewer feel RECOGNISED, then CAPABLE.

Coherence — one intention, four different instruments:

  Shot | Beat       | Scale        | Camera side / angle          | Move
  -----+------------+--------------+------------------------------+-----------------------------
   1   | Hook       | Medium CU    | his LEFT, eye level (~10deg) | pan right across props -> settle -> push in
   2   | Root Cause | Wider medium | his RIGHT, slightly high (~8)| pan + push, reframe chart -> face
   3   | Quick Win  | Tighter MCU  | his LEFT, slightly LOW (~10) | handheld follow the hand -> settle on face
   4   | CTA        | Tight CU     | dead centre, square on       | tilt up hands -> face + push in

Every angle is deliberately kept <=15 degrees off-axis: `studio/CLAUDE.md`
documents that Jimeng's multimodal2video lip-sync fails silently on profile
faces, so camera SIDE is what varies, never face rotation.

Continuity locks (identical in all four frames, so gpt-image-2 + `[SAME_PROP_AS]`
have something concrete to hold):
  - navy-grey mandarin-collar linen shirt
  - dark walnut consultation desk
  - wall of small apothecary drawers, soft warm blur
  - one small pale celadon tea cup
  - one plain stainless teaspoon (the hero prop)

Subtitle safety: at most ONE in-frame visual aid per shot and zero enumerated
b-roll inserts — the 2026-08-24 finding was that a 1:1 insert-per-listed-item
shot guide pushes Jimeng into "labelled explainer" mode and it burns its own
subtitles regardless of the no-subtitle instruction.
"""
from __future__ import annotations

import json
import sys
import urllib.request
from pathlib import Path

HERE = Path(__file__).resolve().parent
STUDIO = HERE.parent


def _env() -> dict[str, str]:
    env: dict[str, str] = {}
    envfile = STUDIO / ".env"
    if not envfile.exists():
        raise SystemExit(f"missing {envfile}")
    for line in envfile.read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        k, v = line.split("=", 1)
        env[k.strip()] = v.strip()
    return env


ENV = _env()
KEY = ENV["NOTION_KEY"]
IDS = json.loads((HERE / "notion_ids.json").read_text())
HEADERS = {
    "Authorization": f"Bearer {KEY}",
    "Notion-Version": "2022-06-28",
    "Content-Type": "application/json",
}


def call(method: str, path: str, body: dict | None = None) -> dict:
    req = urllib.request.Request(
        f"https://api.notion.com/v1/{path}",
        data=json.dumps(body).encode() if body is not None else None,
        method=method,
        headers=HEADERS,
    )
    try:
        return json.load(urllib.request.urlopen(req))
    except urllib.error.HTTPError as exc:  # pragma: no cover - surfaced to operator
        raise SystemExit(f"Notion {method} {path} failed: {exc.read().decode()}") from exc


# --------------------------------------------------------------------------- content

NAME = "🌑 Dark Circles & Eye Bags — It's Not Your Sleep"
TOPIC = "👁️ Eye Health"
HOOK = "Those dark circles are not from bad sleep."
CTA = "Comment circles"
KEYWORD = "circles"

SCRIPT: list[str] = [
    "Those dark circles under your eyes are not from bad sleep. Sleeping more will "
    "never clear them. Your body is telling you something else.",
    "In Chinese medicine, dark shadows mean your kidney energy has gone cold and weak. "
    "Puffy bags mean your spleen cannot move water. Two different problems.",
    "Try this tonight. Warm a spoon in hot water and press gently under each eye for "
    "one minute. Then stop cold drinks after dinner.",
    "Comment circles and I will send you my full kidney and spleen morning protocol.",
]

# Each 🎥 line: everything BEFORE the first " then " is the single still frame that
# `notion_prompts._primary_beat()` hands to gpt-image-2; everything after is the
# motion Jimeng animates. Do not use semicolons or full-width commas — they are
# also split points.
SHOTS: list[dict[str, str]] = [
    {
        "title": "Shot 1 · ~10s · Hook",
        "visual": (
            "Medium close-up of Jackie standing behind a dark walnut consultation desk "
            "in a warm traditional Chinese medicine clinic with a wall of small "
            "apothecary drawers softly blurred behind him. Camera sits at eye level and "
            "slightly to his left so his face reads near-frontal about ten degrees "
            "off-axis and he is framed just left of centre. He wears a navy-grey "
            "mandarin-collar linen shirt and holds a plain stainless teaspoon upright in "
            "his right hand. A small pale celadon tea cup sits on the desk beside his "
            "hand. Eyes open and looking straight into the lens mid-sentence. "
            "Camera pans right across the spoon and the cup then settles and pushes in "
            "on his face."
        ),
        "note": "Not a sleep problem",
    },
    {
        "title": "Shot 2 · ~12s · Root Cause",
        "visual": (
            "Wider medium shot of Jackie in the same warm traditional Chinese medicine "
            "clinic standing to the right of frame beside a simple hanging body chart on "
            "the wall. Camera is now on his right side at a slightly high eye level "
            "looking very gently down at him about eight degrees so the framing flips "
            "screen direction from the previous shot while his face stays near-frontal "
            "with mouth clearly visible. Same navy-grey mandarin-collar linen shirt and "
            "the same small pale celadon tea cup on the dark walnut desk in the near "
            "foreground. One hand rests low against his own lower back to indicate the "
            "kidney region while he keeps facing camera. "
            "Camera pans slightly while pushing in to reframe from the chart onto his "
            "face with a serious expression."
        ),
        "note": "腎陽虛 (shadow) vs 脾虛濕 (bags)",
    },
    {
        "title": "Shot 3 · ~12s · Quick Win",
        "visual": (
            "Tighter medium close-up of Jackie in the same warm traditional Chinese "
            "medicine clinic with the camera dropped to a slightly low angle looking "
            "gently up at him about ten degrees and positioned back on his left so his "
            "face reads near-frontal. He holds the same plain stainless teaspoon in his "
            "right hand raised beside his own cheekbone just below the eye to show the "
            "press while still facing camera with eyes open and mouth visible. The same "
            "small pale celadon tea cup holds steaming hot water on the dark walnut desk "
            "in the soft foreground. Same navy-grey mandarin-collar linen shirt. "
            "Camera follows the spoon with a slight handheld pan and tilt then drifts "
            "back and settles on his face."
        ),
        "note": "Warm spoon 1 min + no cold drinks",
    },
    {
        "title": "Shot 4 · ~8s · CTA",
        "visual": (
            "Tight close-up of Jackie in the same warm traditional Chinese medicine "
            "clinic framed dead centre with the camera square on at eye level and his "
            "face fully frontal. Same navy-grey mandarin-collar linen shirt with the "
            "wall of small apothecary drawers a soft warm blur behind him. His hands "
            "rest together on the dark walnut desk at the bottom edge of frame with the "
            "same small pale celadon tea cup beside them. He looks directly into the "
            "lens and gives a small confident nod. "
            "Camera tilts slowly up from his hands to his face with a gentle push-in."
        ),
        "note": "Comment 👇 circles",
    },
]

FIRST_DM = (
    "Hey! The warm-spoon press works fast on dark circles 🌑\n\n"
    "Quick check — is yours more DARK SHADOW under the eye, or PUFFY BAGS in the "
    "morning? They're two different fixes."
)

INFOGRAPHIC_BRIEF = (
    "Vertical infographic, 4:5 ratio, warm TCM clinic aesthetic, cream and terracotta "
    "palette, clean sans-serif, no photo-realistic faces.\n"
    "Title: 'Dark Circles vs Eye Bags — Two Different Signals'.\n"
    "Three panels:\n"
    "1) DARK SHADOW — half-moon under-eye icon; text: kidney yang gone cold and weak. "
    "Worse with late nights, cold raw food, long-running worry and overwork.\n"
    "2) PUFFY BAGS — puffy lower-lid icon; text: spleen cannot move water. Worse with "
    "cold drinks, dairy, salty late dinners, too little movement.\n"
    "3) TONIGHT'S FIX — teaspoon and cup icons; text: warm spoon press under each eye "
    "for 1 minute, stop cold drinks after dinner, black sesame and walnut at breakfast.\n"
    "Footer strip: 'Comment \"circles\" for the full protocol'."
)

SECOND_DM = (
    "Here's your dark-circle guide — do the warm-spoon press 5 nights in a row and "
    "check the mirror 🌙\n\n"
    "Want the kidney-warming breakfast list that fixes it from the inside? Reply 'warm'."
)


# --------------------------------------------------------------------------- blocks

def rt(text: str) -> list[dict]:
    return [{"type": "text", "text": {"content": text}}]


def h2(text: str) -> dict:
    return {"object": "block", "type": "heading_2", "heading_2": {"rich_text": rt(text)}}


def h3(text: str) -> dict:
    return {"object": "block", "type": "heading_3", "heading_3": {"rich_text": rt(text)}}


def bullet(text: str) -> dict:
    return {
        "object": "block",
        "type": "bulleted_list_item",
        "bulleted_list_item": {"rich_text": rt(text)},
    }


def code(text: str) -> dict:
    return {
        "object": "block",
        "type": "code",
        "code": {"rich_text": rt(text), "language": "plain text"},
    }


def divider() -> dict:
    return {"object": "block", "type": "divider", "divider": {}}


def build_blocks() -> list[dict]:
    blocks: list[dict] = [h2("📜 Master Script (EN)")]
    blocks += [bullet(line) for line in SCRIPT]
    blocks.append(divider())
    blocks.append(h2("🎬 Shot Guide"))
    for shot, line in zip(SHOTS, SCRIPT):
        blocks.append(h3(shot["title"]))
        blocks.append(bullet(f"🎥 {shot['visual']}"))
        blocks.append(bullet(f"🗣️ {line}"))
        blocks.append(bullet(f"💡 {shot['note']}"))
    blocks.append(divider())
    blocks.append(
        {
            "object": "block",
            "type": "callout",
            "callout": {
                "rich_text": rt(
                    "📩 PROTOCOL — DM flow triggered when viewer comments the CTA "
                    "keyword. First DM = instant text. After any reply, send the "
                    "infographic + second DM."
                ),
                "icon": {"type": "emoji", "emoji": "📩"},
            },
        }
    )
    blocks.append(h3("💬 First DM — send immediately (text only)"))
    blocks.append(code(FIRST_DM))
    blocks.append(h3("🖼️ Infographic Brief — paste into GPT image gen"))
    blocks.append(code(INFOGRAPHIC_BRIEF))
    blocks.append(h3("💬 Second DM — send after any reply (attach infographic)"))
    blocks.append(code(SECOND_DM))
    return blocks


def find_existing() -> str | None:
    res = call(
        "POST",
        f"databases/{IDS['content_db']}/query",
        {"filter": {"property": "Name", "title": {"contains": "Dark Circles"}}},
    )
    for r in res["results"]:
        return r["id"]
    return None


def main() -> int:
    existing = find_existing()
    if existing:
        print(f"⏭  already exists: {existing}")
        return 0
    page = call(
        "POST",
        "pages",
        {
            "parent": {"database_id": IDS["content_db"]},
            "properties": {
                "Name": {"title": rt(NAME)},
                "Topic": {"select": {"name": TOPIC}},
                "Hook": {"rich_text": rt(HOOK)},
                "CTA": {"rich_text": rt(CTA)},
                "Concept Status": {"select": {"name": "✍️ Scripted"}},
                "Fan out to": {"multi_select": [{"name": "Jackie Chan"}]},
            },
            "children": build_blocks(),
        },
    )
    print(f"✅ created {NAME}\n   id={page['id']}\n   url={page['url']}")
    print(f"   keyword={KEYWORD!r}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
