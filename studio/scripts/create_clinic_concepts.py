#!/usr/bin/env python3
"""Create the "Jackie treating a patient" Content Library concepts (10).

    python3 scripts/create_clinic_concepts.py [--dry-run] [--only lowback,knot]

Camera plan (director skill)
----------------------------
Every video runs the same four beats, and the beat NAMES are load-bearing:
`notion_prompts._jimeng_camera()` keys the video 运镜 off the title, so
Hook / Root Cause / Quick Win / CTA each yield a DIFFERENT move. Renaming a beat
silently collapses the camera work back to the generic default while the still
still looks correct.

  Shot 1  Hook        medium-wide TWO SHOT, camera on Jackie's left, eye level
                      -> pan across the desk, settle, push in
  Shot 2  Root Cause  tighter TWO SHOT, camera flips to his RIGHT, slightly high
                      -> pan + push, reframe onto his face
  Shot 3  Quick Win   TWO SHOT from low, camera back to his left
                      -> handheld follow of the hand action, settle on face
  Shot 4  CTA         tight CLOSE-UP, Jackie ALONE, square on at eye level
                      -> tilt up from hands to face, gentle push-in

Screen direction deliberately flips between shots 1 and 2, and the height
changes on 3 and 4, so the four frames differ on scale, camera side AND height
rather than being one lens creeping forward four times.

Every angle stays <=15 degrees off-axis. `studio/CLAUDE.md` documents that 即梦's
lip-sync fails silently on a profile face, and that constraint now applies to
BOTH faces in a two shot.

Consistency contract
--------------------
- Jackie: held by the IP reference photos on every gen_image call (always was).
- The guest: `[SAME_PERSON_AS: Shot 1]` on shots 2 and 3, so shot 1's actual
  render is passed to gpt-image-2 as an extra reference. Without it a recurring
  extra has no reference at all and a different-looking stranger is improvised
  per shot — root-caused on the Tongue Never Lies street series, 2026-07-14.
- Props: `[SAME_PROP_AS: Shot 1]` on shots 2-4 via add_prop_markers.py.
- Wardrobe + stool + desk + backdrop are restated verbatim in every shot.

Shot 4 carries neither person marker: it is intentionally Jackie alone, so it
must NOT be chained to the guest.
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

from concepts_clinic_data import CONCEPTS, WARDROBE  # noqa: E402
from notion_prompts import TWO_PERSON_MARKER  # noqa: E402

SETTING = "warm traditional Chinese medicine clinic"
BACKDROP = "a wall of small apothecary drawers softly blurred behind them"
DESK = "dark walnut consultation desk"


def _env() -> dict[str, str]:
    env: dict[str, str] = {}
    for line in (STUDIO / ".env").read_text().splitlines():
        line = line.strip()
        if line and not line.startswith("#") and "=" in line:
            k, v = line.split("=", 1)
            env[k.strip()] = v.strip()
    return env


ENV = _env()
IDS = json.loads((HERE / "notion_ids.json").read_text())
H = {"Authorization": f"Bearer {ENV['NOTION_KEY']}",
     "Notion-Version": "2022-06-28", "Content-Type": "application/json"}


def call(method: str, path: str, body: dict | None = None) -> dict:
    req = urllib.request.Request(
        f"https://api.notion.com/v1/{path}",
        data=json.dumps(body).encode() if body is not None else None,
        method=method, headers=H)
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            return json.loads(r.read().decode())
    except urllib.error.HTTPError as exc:
        raise SystemExit(f"Notion {method} {path}: {exc.read().decode()[:300]}") from exc


# (scale, camera clause, move_a, move_b) — one per beat.
_SHOTS = [
    ("Medium-wide two shot",
     "Camera sits at eye level and slightly to Jackie's left so BOTH faces read near-frontal "
     "about ten degrees off-axis",
     "pans right across the desk", "settles and pushes in on the two of them"),
    ("Tighter two shot",
     "Camera has moved round to Jackie's right at a slightly high eye level looking very gently "
     "down about eight degrees, flipping the screen direction from the previous shot while both "
     "faces stay near-frontal",
     "pans slightly while pushing in", "reframes onto Jackie's face with a serious expression"),
    ("Two shot from a slightly low angle",
     "Camera has dropped to look gently up about ten degrees and moved back to Jackie's left, "
     "both faces still near-frontal",
     "follows the hand action with a slight handheld pan and tilt",
     "drifts back and settles on Jackie's face"),
    ("Tight close-up",
     "Camera is square on at eye level with Jackie framed dead centre and his face fully frontal",
     "tilts slowly up from his hands to his face", "eases into a gentle push-in"),
]
_BEATS = ["Hook", "Root Cause", "Quick Win", "CTA"]
_SECS = ["~10s", "~12s", "~12s", "~8s"]


def shot_guides(c: dict) -> list[str]:
    w = WARDROBE[c["wardrobe"]]
    out = []
    for i, (scale, camera, move_a, move_b) in enumerate(_SHOTS):
        if i < 3:
            body = (
                f"{TWO_PERSON_MARKER} {scale} in a {SETTING} with {BACKDROP}. "
                f"{camera}. "
                f"Jackie wears a {w}. Beside him {c['guest']}. "
                f"Jackie {c['actions'][i]}. "
                f"On the {DESK} sits {c['prop']}. "
                "Jackie is mid-sentence looking straight into the lens with his mouth clearly "
                "visible. The guest is calm and still with her mouth closed, also facing the "
                "camera, and is not speaking. "
                f"Camera {move_a} then {move_b}."
            )
        else:
            body = (
                f"{scale} of Jackie ALONE in the same {SETTING} with a wall of small apothecary "
                f"drawers a soft warm blur behind him. {camera}. "
                f"He wears the same {w} and rests both hands together on the {DESK} at the "
                f"bottom edge of frame, with {c['prop']} beside them. "
                "He looks directly into the lens and gives a small confident nod. "
                f"Camera {move_a} then {move_b}."
            )
        out.append(body)
    return out


def rt(t: str) -> list[dict]:
    return [{"type": "text", "text": {"content": t}}]


def _b(kind: str, t: str) -> dict:
    return {"object": "block", "type": kind, kind: {"rich_text": rt(t)}}


def code(t: str) -> dict:
    return {"object": "block", "type": "code",
            "code": {"rich_text": rt(t), "language": "plain text"}}


PREAMBLE = ("Vertical infographic, 4:5 ratio, warm TCM clinic aesthetic, cream and terracotta "
            "palette, clean sans-serif, flat icons only, no photo-realistic faces.\n")


def build_blocks(c: dict) -> list[dict]:
    g = shot_guides(c)
    blocks = [_b("heading_2", "📜 Master Script (EN)")]
    blocks += [_b("bulleted_list_item", l) for l in c["script"]]
    blocks.append({"object": "block", "type": "divider", "divider": {}})
    blocks.append(_b("heading_2", "🎬 Shot Guide"))
    for i in range(4):
        blocks.append(_b("heading_3", f"Shot {i+1} · {_SECS[i]} · {_BEATS[i]}"))
        blocks.append(_b("bulleted_list_item", f"🎥 {g[i]}"))
        blocks.append(_b("bulleted_list_item", f"🗣️ {c['script'][i]}"))
        blocks.append(_b("bulleted_list_item", f"💡 {c['notes'][i]}"))
    blocks.append({"object": "block", "type": "divider", "divider": {}})
    blocks.append({"object": "block", "type": "callout", "callout": {
        "rich_text": rt("📩 PROTOCOL — DM flow triggered when viewer comments the CTA keyword. "
                        "First DM = instant text. After any reply, send the infographic + second DM."),
        "icon": {"type": "emoji", "emoji": "📩"}}})
    blocks.append(_b("heading_3", "💬 First DM — send immediately (text only)"))
    blocks.append(code(c["first_dm"]))
    blocks.append(_b("heading_3", "🖼️ Infographic Brief — paste into GPT image gen"))
    blocks.append(code(PREAMBLE + c["infographic"] +
                       f"\nFooter strip: 'Comment \"{c['key']}\" for the full protocol'."))
    blocks.append(_b("heading_3", "💬 Second DM — send after any reply (attach infographic)"))
    blocks.append(code(c["second_dm"]))
    return blocks


def existing() -> set[str]:
    names, cur = set(), None
    while True:
        body: dict = {"page_size": 100}
        if cur:
            body["start_cursor"] = cur
        r = call("POST", f"databases/{IDS['content_db']}/query", body)
        for row in r["results"]:
            names.add("".join(x["plain_text"] for x in row["properties"]["Name"]["title"]))
        if not r.get("has_more"):
            return names
        cur = r["next_cursor"]


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--only")
    args = ap.parse_args()
    want = {k.strip() for k in args.only.split(",")} if args.only else None
    have = existing()
    made = []
    for c in CONCEPTS:
        if want and c["key"] not in want:
            continue
        if c["name"] in have:
            print(f"⏭  exists: {c['name']}")
            continue
        if args.dry_run:
            print(f"\n[dry-run] {c['name']}  (keyword={c['key']})")
            for i, g in enumerate(shot_guides(c), 1):
                print(f"  Shot {i}: {g[:170]}…")
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
            "children": build_blocks(c)})
        made.append((c["key"], page["id"]))
        print(f"✅ {c['name']}  id={page['id']}")
    print(f"\n[done] created {len(made)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
