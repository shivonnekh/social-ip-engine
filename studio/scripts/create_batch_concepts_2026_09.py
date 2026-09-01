#!/usr/bin/env python3
"""Create the 2026-09 Jackie batch (10 Content Library concepts) in Notion.

Content lives in ``concepts_2026_09_data.py``; this file is the plumbing plus
the camera work. Idempotent — a concept whose exact Name already exists is
skipped, so a partial run is safe to repeat.

    python3 scripts/create_batch_concepts_2026_09.py [--dry-run] [--only hair,acne]

Camera rotations (the "director skill" output)
----------------------------------------------
Three rotations, cycled across the ten concepts so the batch doesn't open on the
same frame ten times. Within ANY rotation the four shots differ on all three
axes that actually read on screen — scale, camera side, camera height:

  rot 0 : MCU left/eye  →  wide-MS right/high  →  tight-MCU left/low   →  CU centre/eye
  rot 1 : MS right/low  →  MCU left/eye        →  MS centre/high       →  CU right/eye
  rot 2 : CU centre/eye →  MS left/low         →  wide-MS right/eye    →  MCU left/low

Two invariants hold in every template:

* **<=15 degrees off-axis, always.** Camera SIDE and HEIGHT vary; the face never
  turns. ``studio/CLAUDE.md`` documents that Jimeng's multimodal2video lip-sync
  fails silently on a profile face, so this is a hard constraint, not taste.
* **One continuous talking head, one in-frame prop, zero cutaway inserts.** A
  shot guide that enumerates a b-roll insert per spoken item flips Jimeng into
  "labelled explainer" mode and it burns its own subtitles over the no-subtitle
  instruction (root-caused 2026-08-24).

Split-point discipline: ``notion_prompts._primary_beat()`` cuts the shot guide at
the first ``;`` / full-width comma / ``then`` / insert-word and feeds only that
to gpt-image-2. So every template below states the whole still BEFORE the word
"then", and puts the second half of the camera move after it. Never introduce a
semicolon or a full-width comma into these strings.
"""
from __future__ import annotations

import argparse
import json
import sys
import urllib.error
import urllib.request
from pathlib import Path

HERE = Path(__file__).resolve().parent
STUDIO = HERE.parent
sys.path.insert(0, str(HERE))

from concepts_2026_09_data import CONCEPTS, WARDROBE  # noqa: E402

SETTING = "warm traditional Chinese medicine clinic"
BACKDROP = "a wall of small apothecary drawers softly blurred behind him"
DESK = "dark walnut consultation desk"


def _load_env() -> dict[str, str]:
    env: dict[str, str] = {}
    envfile = STUDIO / ".env"
    if not envfile.exists():
        raise SystemExit(f"missing {envfile}")
    for line in envfile.read_text().splitlines():
        line = line.strip()
        if line and not line.startswith("#") and "=" in line:
            k, v = line.split("=", 1)
            env[k.strip()] = v.strip()
    return env


ENV = _load_env()
IDS = json.loads((HERE / "notion_ids.json").read_text())
HEADERS = {
    "Authorization": f"Bearer {ENV['NOTION_KEY']}",
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
    except urllib.error.HTTPError as exc:
        raise SystemExit(f"Notion {method} {path} failed: {exc.read().decode()}") from exc


# ------------------------------------------------------------------ camera

def _shot(scale: str, camera: str, wardrobe: str, prop_rest: str, action: str,
          move_a: str, move_b: str) -> str:
    """Assemble one 🎥 line.

    Sentence order is deliberate: SCALE + setting, then the CAMERA clause, then
    wardrobe + the one hand action, then whatever prop stays on the desk. The
    held item is named inside `action` and the desk item inside `prop_rest`, so
    the same object is never described twice in one frame (an early version said
    Jackie held the comb AND that the comb sat on the desk — gpt-image-2 would
    happily render two combs).
    """
    return " ".join([
        f"{scale} of Jackie in a {SETTING} with {BACKDROP}.",
        f"{camera}.",
        f"He wears a {wardrobe} and {action}.",
        f"On the {DESK} in front of him sits {prop_rest}.",
        "Eyes open and looking straight into the lens mid-sentence.",
        f"Camera {move_a} then {move_b}.",
    ])


# Each rotation = 4 (scale, camera_clause, move_a, move_b) tuples, one per beat.
_ROTATIONS: list[list[tuple[str, str, str, str]]] = [
    [
        ("Medium close-up",
         "Camera sits at eye level and slightly to his left so his face reads near-frontal "
         "about ten degrees off-axis and he is framed just left of centre",
         "pans right across the desk", "settles and pushes in on his face"),
        ("Wider medium shot",
         "Camera is now on his right side at a slightly high eye level looking very gently "
         "down at him about eight degrees so the framing flips screen direction from the "
         "previous shot while his face stays near-frontal",
         "pans slightly while pushing in", "reframes onto his face with a serious expression"),
        ("Tighter medium close-up",
         "Camera has dropped to a slightly low angle looking gently up at him about ten "
         "degrees and moved back to his left so his face reads near-frontal",
         "follows the hand action with a slight handheld pan and tilt",
         "drifts back and settles on his face"),
        ("Tight close-up",
         "Camera is square on at eye level with him framed dead centre and his face fully "
         "frontal",
         "tilts slowly up from his hands to his face", "eases into a gentle push-in"),
    ],
    [
        ("Medium shot",
         "Camera is low and slightly to his right looking gently up at him about ten "
         "degrees so he reads tall in frame while his face stays near-frontal",
         "pans left across the desk", "rises slightly and pushes in on his face"),
        ("Medium close-up",
         "Camera is at eye level and slightly to his left so his face reads near-frontal "
         "about twelve degrees off-axis and he sits right of centre",
         "drifts gently left while pushing in",
         "settles square on his face with a serious expression"),
        ("Medium shot",
         "Camera is centred at a slightly high eye level looking very gently down at him "
         "about eight degrees with the desk large in the near foreground",
         "tilts down to follow the hand action with a light handheld sway",
         "lifts back up and settles on his face"),
        ("Tight close-up",
         "Camera is just right of centre at eye level with his face turned barely ten "
         "degrees back toward the lens and filling the frame",
         "tilts slowly up from his hands to his face", "closes in with a gentle push"),
    ],
    [
        ("Close-up",
         "Camera is dead centre at eye level with his face fully frontal and filling much "
         "of the frame for a cold open",
         "holds still on his face", "eases back to reveal the desk"),
        ("Medium shot",
         "Camera is on his left and dropped low looking gently up at him about twelve "
         "degrees so he reads grounded and steady while his face stays near-frontal",
         "pans right along the desk", "rises and pushes in on his face"),
        ("Wider medium shot",
         "Camera is on his right at eye level with the desk clearly visible in the near "
         "foreground and his face near-frontal about ten degrees off-axis",
         "tracks the hand action with a soft handheld pan",
         "drifts back to frame his face square on"),
        ("Medium close-up",
         "Camera is slightly left of centre and a touch low looking gently up at him about "
         "eight degrees with his face near-frontal",
         "tilts up from his hands to his face", "settles with a slow warm push-in"),
    ],
]

_BEATS = ["Hook", "Root Cause", "Quick Win", "CTA"]
_SECS = ["~10s", "~12s", "~12s", "~8s"]


def shot_guides(concept: dict) -> list[str]:
    """Four 🎥 lines for one concept, from its assigned camera rotation.

    Beat NAMES are load-bearing: notion_prompts._jimeng_camera() keys the video
    运镜 off the beat title, and Hook / Root Cause / Quick Win / CTA each map to
    a DIFFERENT move. Renaming a beat silently collapses the video camera work
    back to the generic default even though the still would still look right.
    """
    rot = _ROTATIONS[concept["rotation"] % len(_ROTATIONS)]
    wardrobe = WARDROBE[concept["wardrobe"]]
    return [
        _shot(scale, camera, wardrobe, concept["prop_rest"],
              concept["actions"][i], move_a, move_b)
        for i, (scale, camera, move_a, move_b) in enumerate(rot)
    ]


# ------------------------------------------------------------------ blocks

def rt(text: str) -> list[dict]:
    return [{"type": "text", "text": {"content": text}}]


def _b(kind: str, text: str) -> dict:
    return {"object": "block", "type": kind, kind: {"rich_text": rt(text)}}


def code(text: str) -> dict:
    return {"object": "block", "type": "code",
            "code": {"rich_text": rt(text), "language": "plain text"}}


INFOGRAPHIC_PREAMBLE = (
    "Vertical infographic, 4:5 ratio, warm TCM clinic aesthetic, cream and terracotta "
    "palette, clean sans-serif, flat icons only, no photo-realistic faces.\n"
)


def build_blocks(concept: dict) -> list[dict]:
    guides = shot_guides(concept)
    blocks: list[dict] = [_b("heading_2", "📜 Master Script (EN)")]
    blocks += [_b("bulleted_list_item", line) for line in concept["script"]]
    blocks.append({"object": "block", "type": "divider", "divider": {}})
    blocks.append(_b("heading_2", "🎬 Shot Guide"))
    for i in range(4):
        blocks.append(_b("heading_3", f"Shot {i + 1} · {_SECS[i]} · {_BEATS[i]}"))
        blocks.append(_b("bulleted_list_item", f"🎥 {guides[i]}"))
        blocks.append(_b("bulleted_list_item", f"🗣️ {concept['script'][i]}"))
        blocks.append(_b("bulleted_list_item", f"💡 {concept['notes'][i]}"))
    blocks.append({"object": "block", "type": "divider", "divider": {}})
    blocks.append({
        "object": "block", "type": "callout",
        "callout": {
            "rich_text": rt(
                "📩 PROTOCOL — DM flow triggered when viewer comments the CTA keyword. "
                "First DM = instant text. After any reply, send the infographic + second DM."
            ),
            "icon": {"type": "emoji", "emoji": "📩"},
        },
    })
    blocks.append(_b("heading_3", "💬 First DM — send immediately (text only)"))
    blocks.append(code(concept["first_dm"]))
    blocks.append(_b("heading_3", "🖼️ Infographic Brief — paste into GPT image gen"))
    blocks.append(code(
        INFOGRAPHIC_PREAMBLE
        + concept["infographic"]
        + f"\nFooter strip: 'Comment \"{concept['key']}\" for the full protocol'."
    ))
    blocks.append(_b("heading_3", "💬 Second DM — send after any reply (attach infographic)"))
    blocks.append(code(concept["second_dm"]))
    return blocks


def existing_names() -> set[str]:
    names, cursor = set(), None
    while True:
        body: dict = {"page_size": 100}
        if cursor:
            body["start_cursor"] = cursor
        res = call("POST", f"databases/{IDS['content_db']}/query", body)
        for r in res["results"]:
            names.add("".join(x["plain_text"] for x in r["properties"]["Name"]["title"]))
        if not res.get("has_more"):
            return names
        cursor = res["next_cursor"]


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--only", help="comma-separated concept keys")
    args = ap.parse_args()

    wanted = {k.strip() for k in args.only.split(",")} if args.only else None
    have = existing_names()
    created = []
    for c in CONCEPTS:
        if wanted and c["key"] not in wanted:
            continue
        if c["name"] in have:
            print(f"⏭  exists: {c['name']}")
            continue
        if args.dry_run:
            print(f"[dry-run] would create {c['name']}  (keyword={c['key']}, rot={c['rotation']})")
            for i, g in enumerate(shot_guides(c), 1):
                print(f"    Shot {i}: {g[:150]}…")
            continue
        page = call("POST", "pages", {
            "parent": {"database_id": IDS["content_db"]},
            "properties": {
                "Name": {"title": rt(c["name"])},
                "Topic": {"select": {"name": c["topic"]}},
                "Hook": {"rich_text": rt(c["hook"])},
                "CTA": {"rich_text": rt(f"Comment {c['key']}")},
                "Concept Status": {"select": {"name": "✍️ Scripted"}},
                "Fan out to": {"multi_select": [{"name": "Jackie Chan"}]},
            },
            "children": build_blocks(c),
        })
        created.append((c["key"], page["id"]))
        print(f"✅ {c['name']}\n   id={page['id']}  keyword={c['key']}")

    print(f"\n[done] created {len(created)} concept(s)")
    for key, pid in created:
        print(f"  {key:<10} {pid}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
