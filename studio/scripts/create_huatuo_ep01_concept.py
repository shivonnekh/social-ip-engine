#!/usr/bin/env python3
"""Create the "我是现代中医，今天跟华佗出诊 — EP01" Content Library concept.

Act 1 only ("The Approach" — portal hook through the first exchange with
Hua Tuo, ending on his cliffhanger line "跟上"). The patient-diagnosis scene
(the back half of the full episode brief) is intentionally NOT included yet —
Shivonne asked for "a few shots" as a directing sample to review before
committing to the full episode.

Directed with seedance-20's directing-engine (one voice: observational
naturalist / found-footage vlogger, biased toward grounded sensory texture
per the brief's own "脏、熱、吵、擠、真實" note) + seedance-sequence's scene/
clip discipline (one narrative job + felt_intent per clip, single-speaker
framing per dialogue clip to avoid 即梦's known two-face-talking hang).

Created with: Properties (Name, Topic, Hook, CTA, Concept Status = "✍️
Scripted" — deliberately NOT "✅ Ready to fan-out", this is a review-first
draft) + Body (📜 Master Script (EN) + 🎬 Directorial Notes + 🎬 Shot Guide),
same shape as create_constitution_concept.py so notion_fanout.py can explode
it per-IP later, once approved.

Idempotent — skips if a concept with a matching name already exists.

Usage:
    python3 scripts/create_huatuo_ep01_concept.py
    python3 scripts/create_huatuo_ep01_concept.py --dry-run   # preview only
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
    return {"object": "block", "type": "heading_2", "heading_2": {"rich_text": _rt(text)}}


def _h3(text: str) -> dict:
    return {"object": "block", "type": "heading_3", "heading_3": {"rich_text": _rt(text)}}


def _bullet(text: str) -> dict:
    return {"object": "block", "type": "bulleted_list_item",
            "bulleted_list_item": {"rich_text": _rt(text)}}


def _para(text: str) -> dict:
    return {"object": "block", "type": "paragraph", "paragraph": {"rich_text": _rt(text)}}


def _callout(text: str, emoji: str = "⚠️") -> dict:
    return {"object": "block", "type": "callout", "callout": {
        "rich_text": _rt(text), "icon": {"type": "emoji", "emoji": emoji}}}


def _divider() -> dict:
    return {"object": "block", "type": "divider", "divider": {}}


def build_body_blocks(concept: dict) -> list[dict]:
    blocks: list[dict] = []

    blocks.append(_h2("📜 Master Script (EN gloss)"))
    for line in concept["master_script_en"]:
        blocks.append(_bullet(line))

    blocks.append(_divider())

    blocks.append(_h2("🎬 Directorial Notes (seedance-20 director's read)"))
    for line in concept["directorial_notes"]:
        blocks.append(_bullet(line))

    blocks.append(_divider())

    blocks.append(_callout(concept["fanout_warning"], emoji="🚨"))

    blocks.append(_divider())

    blocks.append(_h2("🎬 Shot Guide — Act 1: The Approach"))
    for shot in concept["shots"]:
        blocks.append(_h3(shot["title"]))
        blocks.append(_bullet(f"🎥 {shot['visual']}"))
        blocks.append(_bullet(f"🗣️ {shot['script_zh']}"))
        blocks.append(_bullet(f"🇬🇧 {shot['script_en']}"))
        blocks.append(_bullet(f"🎬 即梦 note: {shot['production_note']}"))

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

HUATUO_ANCHOR = (
    "Hua Tuo: East-Han-dynasty physician, early 60s, weathered sun-browned "
    "face, deep laugh-lines, long grey-streaked beard loosely tied, thinning "
    "grey hair in a simple topknot under a plain undyed hemp headscarf, faded "
    "indigo-brown short physician's robe with rolled sleeves faintly stained "
    "with herb dust, sturdy calloused hands, calm unhurried eyes that miss "
    "nothing"
)

CONCEPT: dict = {
    "name": "🩺 我是现代中医，今天跟华佗出诊 · EP01 Act 1 The Approach",
    "topic": "📺 History Series",
    "hook": "A modern TCM doctor time-travels into the Eastern Han dynasty to find out if the Hua Tuo we studied in school is the same man history actually remembers — then gets pulled onto his rounds.",
    "cta": "part2",
    "master_script_en": [
        "I think this is the Eastern Han. That man treating a patient up ahead — they say that's Hua Tuo. I'm a TCM doctor myself. Today I want to find out: is the Hua Tuo we studied the real one?",
        "No modern pharmacy here, no disposable needles. Herbs are processed right on the street, even the way they're weighed is different.",
        "The smell here is so much stronger than a modern herbal shop. The ground is just dirt, and Hua Tuo sits right in it to take a pulse. This herb isn't sliced — it's kept whole.",
        "Sir — I'm a healer too, from very far away.",
        "A healer travels without a medicine chest, and carries only a mirror that glows?",
        "I'll explain that later. I want to follow you on your rounds today.",
        "Medicine isn't about watching me. It's about watching the patient. Keep up.",
    ],
    "directorial_notes": [
        "Project voice (Step 6): Observational naturalist — invisible, motivated, mostly handheld; muted true color; long-ish holds. This is the found-footage vlogger register the brief itself calls for (\"脏、熱、吵、擠、真實\") — resist the urge to make Han-dynasty China look like a clean costume-drama set.",
        "Long-form spine (Step 8): open on selfie intimacy (tight, quiet under VO) → widen and thicken sound through the market pass (rising) → the first exchange with Hua Tuo is the pattern break: camera goes still and close for the first time, sound drops to near-silence. That stillness is what sells \"this is a real conversation,\" not a tour.",
        "Two-character dialogue is shot single-speaker per clip on purpose — 即梦's multimodal2video hangs on two faces talking in one frame (documented gotcha in studio/CLAUDE.md). Every dialogue beat below is one speaker, near-frontal, eyes open, mouth visible; the other character is present but not the lip-synced subject.",
        "Character contract — 华佗: " + HUATUO_ANCHOR + ". Reuse this description verbatim in every Hua Tuo shot prompt (no photo reference exists yet). Lock his face at Shot 5 (his first close dialogue shot) via the studio's `[SAME_PERSON_AS: Shot 5]` marker for Shots 5 and 7.",
        "Character contract — Host: played by whichever IP fans out into this role, in their own real modern clothes/face per their IP Registry reference — the anachronism against the Han-dynasty backdrop IS the joke, do not costume them into period dress.",
        "World bible: dusty Han-dynasty street market outside a small town — thatched/wood stalls, herb-drying racks, an open-air clinic stall; soft overcast daylight; warm-neutral, slightly desaturated palette (not saturated fantasy-China); layered ambience (pestle grinding, distant livestock, murmured overlapping chatter, a cook-fire) that thins to near-silence for the two intimate dialogue beats.",
    ],
    "fanout_warning": (
        "Before fanning to more than one IP: SAME_PERSON_AS today only resolves "
        "an image from a shot in the SAME Production row — it does not share a "
        "face across two different IPs' rows. If this fans out to both Jackie "
        "and Jessica independently, Hua Tuo will very likely render as two "
        "different-looking men across the two Instagram accounts, breaking the "
        "\"same recurring character\" premise the whole series depends on. "
        "Recommended fix before fan-out: generate Shot 5's Hua Tuo still once, "
        "save it as a standalone asset (e.g. campaigns/assets/huatuo-reference.png, "
        "same pattern as the clinic-bg reference), and pass it as an explicit "
        "extra reference image into notion_image.py for every Hua Tuo shot on "
        "every IP row — not just via SAME_PERSON_AS. Flagging this now, before "
        "any fan-out, since it's cheap to fix here and expensive to fix after "
        "two IPs have already generated mismatched versions of him."
    ),
    "shots": [
        {
            "title": "Shot 1 · ~10s · Portal Hook",
            "visual": (
                "Selfie POV, handheld, host's phone-arm slightly low so the angle reads as a real "
                "self-shot, not a polished vlog rig; he walks at a a slow, careful pace. Muted, true "
                "overcast daylight, dust hanging faintly in the air. Behind him a Han-dynasty market "
                "street resolves out of soft focus as he moves — wooden stalls, a haze of cook-smoke, "
                "figures in unfamiliar dress. He lowers his voice conspiratorially, then glances past "
                "the lens toward the background — one true gesture: the sideways glance that confirms "
                "to himself this is real. Camera holds steady on the glance, does not cut away from it."
            ),
            "script_zh": "各位，我现在应该是在东汉。前面那个正在给人看病的，据说就是华佗。我是现代中医。今天我想确认一件事——我们现在学到的华佗，和真正的华佗，到底是不是同一个人。",
            "script_en": "I think this is the Eastern Han. That man treating a patient up ahead — they say that's Hua Tuo. I'm a TCM doctor myself. Today I want to find out: is the Hua Tuo we studied the real one?",
            "production_note": "Single person, selfie-frontal — dialogue-safe. No two-person risk. This is the shot that sets the whole project's found-footage voice; keep the handheld wobble small and motivated (footsteps), not stylized shake.",
        },
        {
            "title": "Shot 2 · ~9s · World Reveal (wide)",
            "visual": (
                "Cut from selfie to a third-person medium-wide, low three-quarter angle, following the "
                "host from a few steps back and to the side as he threads through the market — this is "
                "the first shot where the audience sees him IN the world rather than through his own "
                "eyes, establishing scale and the crowd around him. Motivated overcast key, dust catching "
                "the light. A cart wheel and hanging bundles of drying herbs cross close to camera in the "
                "foreground as he passes. Ambient market sound thickens: overlapping chatter, distant "
                "livestock, a hammer on wood."
            ),
            "script_zh": "（无对白，环境音+旁白继续）这里没有现代药房，也没有一次性针具。药材就在街边处理，连称量方法都和我们不一样。",
            "script_en": "(no on-camera dialogue — carries as voiceover) No modern pharmacy here, no disposable needles. Herbs are processed right on the street, even the way they're weighed is different.",
            "production_note": "No lip-sync needed (host not facing camera / VO only) — safe to generate as image2video motion, add the VO line in post rather than fighting multimodal2video for a non-speaking shot.",
        },
        {
            "title": "Shot 3 · ~10s · Sensory Texture Montage",
            "visual": (
                "Third-person, no host in frame — a tight, tactile insert pass through the clinic-adjacent "
                "stalls: a hand grinding a mortar and pestle, a clay pot boiling over an open flame with "
                "visible steam, a whole (unsliced) root herb resting on a worn wooden medicine chest, bare "
                "dust and packed dirt underfoot where Hua Tuo's stall sits. Handheld, close, motivated "
                "practical light only (the cook-fire, filtered daylight). No wide shots here — everything "
                "reads texture and proximity, not scenery."
            ),
            "script_zh": "（旁白）这里的药房味道比现代中药房浓很多。地上全是灰，华佗居然就坐在这里诊脉。这个药不是切片，是整段保存的。",
            "script_en": "(voiceover) The smell here is so much stronger than a modern herbal shop. The ground is just dirt, and Hua Tuo sits right in it to take a pulse. This herb isn't sliced — it's kept whole.",
            "production_note": "Pure B-roll insert — no faces to preserve, no lip-sync. Lowest-risk shot in the sequence; good candidate to generate first if testing the world's look before committing to character shots.",
        },
        {
            "title": "Shot 4 · ~6s · Arrival — Host Speaks",
            "visual": (
                "Cut to stillness — the pattern break. Medium close-up on the host, eye-level, camera "
                "locked (first static shot in the sequence), standing at the edge of Hua Tuo's stall. Hua "
                "Tuo is visible over the host's shoulder in the near background, softly out of focus, mid-"
                "task, not looking up yet. Ambient sound drops to near-silence — a held breath before the "
                "first real exchange. The host's posture is slightly deferential, a small respectful bow "
                "of the head as he speaks."
            ),
            "script_zh": "先生，我也是医者，从很远的地方来。",
            "script_en": "Sir — I'm a healer too, from very far away.",
            "production_note": "Host is the sole lip-synced speaker; Hua Tuo present but soft-focus/not addressing camera — avoids the two-face-talking hang. Lock camera fully static for clean lip-sync per 即梦's dialogue-shot requirements.",
        },
        {
            "title": "Shot 5 · ~7s · Reverse — Hua Tuo Speaks (FACE LOCK SHOT)",
            "visual": (
                f"Reverse angle, same locked-camera stillness and near-silence as Shot 4. Medium close-up "
                f"on Hua Tuo, near-frontal, eyes open, unhurried — he looks up from his patient for the "
                f"first time and studies the host's clothes and the phone/camera device with open, "
                f"amused curiosity, not hostility. {HUATUO_ANCHOR}. One true gesture: he tilts his head "
                f"slightly, the way someone does when they've spotted something they don't have a word "
                f"for yet."
            ),
            "script_zh": "医者出门，为何不带药箱，只带一面会发光的镜子？",
            "script_en": "A healer travels without a medicine chest, and carries only a mirror that glows?",
            "production_note": "THIS IS THE HUA TUO FACE-LOCK SHOT. Generate this still first among his shots. Tag every later Hua Tuo shot in this row with `[SAME_PERSON_AS: Shot 5]`. Before fanning to a second IP, save this still as a standalone reference asset per the fan-out warning above.",
        },
        {
            "title": "Shot 6 · ~5s · Host Replies",
            "visual": (
                "Same static medium close-up setup as Shot 4 (same lock, same eyeline, same near-silence) "
                "— return to the host. He gives a small, slightly evasive smile at 'I'll explain that "
                "later,' then a more direct, sincere look on the second sentence — the shift from deflection "
                "to genuine ask is the one true gesture."
            ),
            "script_zh": "这个以后解释。我想跟您出诊一天。",
            "script_en": "I'll explain that later. I want to follow you on your rounds today.",
            "production_note": "Reuse Shot 4's exact camera/light setup for continuity — this is a shot/reverse-shot pair, not a new setup.",
        },
        {
            "title": "Shot 7 · ~8s · Button — Hua Tuo's Line + Walk-Off",
            "visual": (
                f"Return to Hua Tuo's setup (SAME_PERSON_AS Shot 5). He delivers his line without ceremony, "
                f"already turning back to his patient bag/tools as he finishes speaking — power stays with "
                f"him, he never fully faces the host. On the last word he rises and begins walking deeper "
                f"into the market; camera holds static and lets him exit frame rather than following, then "
                f"the host steps INTO frame from the side to fall in behind him — a clean button shot, held "
                f"a beat after they've both exited. Sound: the market ambience swells back up as the near-"
                f"silence breaks, marking the return to the wider world."
            ),
            "script_zh": "医术不在看我，在看病人。跟上。",
            "script_en": "Medicine isn't about watching me. It's about watching the patient. Keep up.",
            "production_note": "Closing beat of Act 1 — deliberately ends on a static held frame (not a cut mid-motion) so it reads as a real scene button, not a truncated clip. Good stopping point before the patient-diagnosis scene (Act 2, not yet built).",
        },
    ],
}


def main() -> int:
    ap = argparse.ArgumentParser(description="Create the Hua Tuo EP01 Act 1 concept")
    ap.add_argument("--dry-run", action="store_true", help="Preview only, no writes")
    args = ap.parse_args()

    ids = json.loads(IDS_PATH.read_text(encoding="utf-8"))
    content_db_id = ids["content_db"]

    print("Loading existing concepts from Content Library...")
    existing = get_existing_names(content_db_id)
    print(f"Found {len(existing)} existing concepts.\n")

    name = CONCEPT["name"]
    core = name.split("·")[0].strip().lstrip("🩺📺💡✍️ ")
    if any(core[:20] in ex for ex in existing):
        print(f"  ⏭  Skip (exists): {name}")
        return 0

    print(f"  ✍️  Creating: {name} ...", end="", flush=True)
    page_id = create_concept(content_db_id, CONCEPT, dry_run=args.dry_run)
    print(f" done ({page_id})")

    if not args.dry_run:
        clean_id = page_id.replace("-", "")
        print(f"\n🔗 https://www.notion.so/{clean_id}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
