#!/usr/bin/env python3
"""Append Act 2 ("The Patient") to the Hua Tuo EP01 Content Library page.

Continues the page created by create_huatuo_ep01_concept.py
(page_id=3b2f2a3f-4320-8193-9b98-c4e80076a517) rather than making a new
page — one Content Library entry should hold the whole episode's script +
shot guide, per studio convention.

Scene boundary from Act 1: new location (patient's home, interior),
continuous time envelope. Canonical anchors carried over: host identity
(per fanned-out IP), Hua Tuo's locked face (Shot 5, Act 1) — every Hua Tuo
shot below still tags `[SAME_PERSON_AS: Shot 5]`. New anchor introduced
this act: the patient, locked at Shot 11 (`[SAME_PERSON_AS: Shot 11]`
for his later shots) — lower stakes than Hua Tuo since he's not a
recurring character, but still locked within the row for internal
consistency.

Directorial spine for this act: rising (messenger + transit) -> turn
(host's premature diagnosis) -> CLIMAX (Hua Tuo's "为何痛" line, Shot 16 —
the whole episode's thesis statement, held longest, closest framing,
near-total silence) -> release (collaboration, resolution) -> epilogue
hook for EP02.

Usage:
    python3 scripts/append_huatuo_ep01_act2.py
    python3 scripts/append_huatuo_ep01_act2.py --dry-run
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
PAGE_ID = "3b2f2a3f-4320-8193-9b98-c4e80076a517"


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
        req = urllib.request.Request(f"{BASE}{path}", data=data, headers=_headers(), method=method)
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
    return {"object": "block", "type": "bulleted_list_item", "bulleted_list_item": {"rich_text": _rt(text)}}


def _callout(text: str, emoji: str = "⚠️") -> dict:
    return {"object": "block", "type": "callout",
            "callout": {"rich_text": _rt(text), "icon": {"type": "emoji", "emoji": emoji}}}


def _divider() -> dict:
    return {"object": "block", "type": "divider", "divider": {}}


MASTER_SCRIPT_ACT2_EN = [
    "Sir — someone east of the village has had stomach pain all night, he can't get up.",
    "A sudden stomach pain like this — in modern medicine we'd rule out the dangerous causes first. But there's no lab test here, no imaging. Only questioning and physical signs.",
    "When did the pain start? Where did it start first? Any vomiting? What did he eat? Any fever? How's his urination and bowel movement?",
    "(placeholder — swap for the real syndrome before VO) From the pattern, this looks like cold-stagnation abdominal pain.",
    "You already know what disease he has?",
    "This is only a preliminary read.",
    "You only asked him where it hurts. You haven't asked him why.",
    "What did he eat last night?",
    "Wait — his lips are dry, his breathing's shallow. We need to be careful, don't push anything too aggressive.",
    "I used to think that meeting Hua Tuo, what I'd want most to ask about was acupuncture, herbal formulas, mafeisan. Now I realize what actually makes him formidable might not be one secret technique — it's that he never rushes to a conclusion.",
    "(off-camera) Are we going or not? The next house has been waiting half an hour.",
    "Coming. What's the next case?",
    "Headache. Three years.",
]

DIRECTORIAL_NOTES_ACT2 = [
    "Scene boundary from Act 1: new location (patient's home, interior) — legitimate cut, not a continuation chain. Opens from canonical anchors: host (per fanned-out IP) + Hua Tuo's locked face from Act 1 Shot 5.",
    "Climax placement (Step 8): Shot 16 (\"你只问了他哪里痛，还没有问他为何痛\") is the whole episode's thesis line and the pattern break — closest framing, camera fully static, near-total silence, held longest of any shot so far. Don't let it compete with a busier shot around it; everything before it builds toward that stillness, everything after loosens.",
    "The two parallel diagnostic lists (host's 6 questions, Hua Tuo's 7 observations) are each compressed into ONE montage shot per character rather than 13 separate generations — Shot 11 (host, spoken, single-speaker-safe) and Shot 12 (Hua Tuo, silent B-roll, no lip-sync risk). Keeps the scene legible instead of fragmenting into a shot per bullet point.",
    "The three-line conflict exchange (\"你已经知道...\" / \"目前只是初步辨证\" / \"你只问了他哪里痛...\") is split into 3 single-speaker shots (14/15/16) rather than one two-person shot, for the same 即梦 dialogue-hang reason as Act 1.",
    "Collaboration beat (Shots 17-18) is deliberately two SEPARATE single-focus shots, not one shot with both characters acting — per seedance-characters' three-tier rule, multi-person shots should carry exactly one focused action; splitting keeps both discoveries legible.",
    "Shot 19 (the resolution nod) is the one place two people share a beat in the same frame — safe because it's a silent synced gesture (image2video), not audio-driven dialogue; the hang risk is specifically tied to multimodal2video lip-sync, not silent motion.",
    "Shot 20 saves a whole extra shot by putting Hua Tuo's interrupting line off-camera (VO only) while camera stays on the host's reflective close-up — a real documentary would very plausibly catch it exactly this way, and it avoids yet another Hua Tuo dialogue setup for a single throwaway line.",
]

DIAGNOSIS_WARNING = (
    "Shot 13's line (the host's premature 证候判断) is a placeholder — I did not "
    "invent real TCM diagnostic content for an IP account to say on camera. "
    "Swap in the actual syndrome you want taught here, ideally checked against "
    "the same card-driven discipline the live Dr. Baba / social-ip-engine content "
    "uses (no hallucinated TCM content) before this goes anywhere near VO."
)

SHOTS_ACT2 = [
    {
        "title": "Shot 8 · ~6s · The Messenger",
        "visual": (
            "Third-person medium shot at Hua Tuo's stall — a villager (one-off character, no "
            "consistency needed beyond this shot) runs up breathless, hands on knees for a beat "
            "before he can get the words out. SAME_PERSON_AS Shot 5 — Hua Tuo is visible in the "
            "same frame, mid-task, already registering the urgency before the villager finishes — "
            "his one small tier-2 reaction: he sets down what he's holding without being asked twice. "
            "Motivated daylight, handheld, market ambience still present but quieting as attention "
            "shifts to the messenger."
        ),
        "script_zh": "先生，村东有人腹痛一夜，已经不能起身了。",
        "script_en": "Sir — someone east of the village has had stomach pain all night, he can't get up.",
        "production_note": "Villager is the sole lip-synced speaker; Hua Tuo reacts silently (tier-2 focused reaction only, no speech) — dialogue-hang-safe.",
    },
    {
        "title": "Shot 9 · ~6s · Urgency (transition)",
        "visual": (
            "Third-person tracking shot, host and Hua Tuo — SAME_PERSON_AS Shot 5 — moving quickly "
            "together through a narrow alley away from the market — the one deliberate voice "
            "deviation in this act: handheld energy picks up, cut is faster, closer to "
            "kinetic-visceral than the observational default, to physically carry the audience "
            "through urgency. No dialogue. Ambient sound thins as they leave the market behind; "
            "footsteps and breath become audible."
        ),
        "script_zh": "（无对白）",
        "script_en": "(no dialogue — pure transition)",
        "production_note": "Silent transition, no lip-sync needed at all — safe, low-risk shot.",
    },
    {
        "title": "Shot 10 · ~9s · Modern-Medicine Framing",
        "visual": (
            "Back to selfie POV, host walking into the patient's home, voice pitched lower/more "
            "serious than Act 1's curious hook tone — the register shift itself signals this is no "
            "longer sightseeing. Dim interior light through a doorway ahead, cooler and more enclosed "
            "than the market's open daylight."
        ),
        "script_zh": "突发腹痛在现代需要先排除危险情况。但这里没有化验，也没有影像检查，只能靠问诊和身体表现判断。",
        "script_en": "A sudden stomach pain like this — in modern medicine we'd rule out the dangerous causes first. But there's no lab test here, no imaging. Only questioning and physical signs.",
        "production_note": "Single person, selfie-frontal — dialogue-safe.",
    },
    {
        "title": "Shot 11 · ~10s · Host's Questioning (montage) — PATIENT FACE LOCK SHOT",
        "visual": (
            "Medium shot, host kneeling beside the patient's bed, addressing the patient and a "
            "hovering family member just off to the side — NOT the patient himself as a second "
            "on-camera speaker; the patient gives only small reactive tier-1 micro-motion (a wince, "
            "a slow head-shake) while the family member gives brief single-word answers. Host's hand "
            "rests lightly near the patient's wrist as he speaks, checking as he asks. The six "
            "questions are delivered as one fast, connected line — this is a diagnostic rhythm, not "
            "six separate beats."
        ),
        "script_zh": "什么时候开始痛？最早痛在哪里？有没有呕吐？吃过什么？有没有发热？大小便如何？",
        "script_en": "When did the pain start? Where did it start first? Any vomiting? What did he eat? Any fever? How's his urination and bowel movement?",
        "production_note": "THIS IS THE PATIENT FACE-LOCK SHOT. Tag every later patient-visible shot in this row with `[SAME_PERSON_AS: Shot 11]`. Host is the sole lip-synced speaker; patient/family give only micro-reactions, not full dialogue coverage — keeps this dialogue-hang-safe.",
    },
    {
        "title": "Shot 12 · ~10s · Hua Tuo's Observation (silent montage)",
        "visual": (
            "Third-person, close, SAME_PERSON_AS Shot 5 — Hua Tuo, silent, his eyes moving across the "
            "patient's face color, a beat watching the rise and fall of his breathing, a glance at his "
            "posture (curled, guarding the abdomen), a light two-finger touch at the patient's wrist for "
            "pulse, a hand hovering near (not pressing) the abdomen to watch the patient's own reaction "
            "to proximity, one read of the patient's overall alertness. No dialogue — this plays as pure "
            "observation, the visual counterpart to Shot 11's spoken questions."
        ),
        "script_zh": "（无对白，旁白覆盖：华佗则观察面色、呼吸、姿势、汗液、腹部反应、精神状态、脉象变化）",
        "script_en": "(no on-camera dialogue — carries as voiceover: Hua Tuo, meanwhile, reads color, breath, posture, sweat, the belly's response, alertness, the pulse)",
        "production_note": "No lip-sync at all — safest shot in the act. SAME_PERSON_AS Shot 5 required for Hua Tuo's face.",
    },
    {
        "title": "Shot 13 · ~7s · The Premature Diagnosis",
        "visual": (
            "Medium close-up, host, slightly too confident too soon — he half-turns to camera as if "
            "explaining to the audience, a small satisfied nod at his own conclusion. This confidence "
            "is the setup for the turn that follows; play it sincere, not smug, so Hua Tuo's question "
            "in Shot 14 lands as a real correction, not a punchline at the host's expense."
        ),
        "script_zh": "【占位 — 需替换为真实证候，录音前请核实】从症状看，这像是寒凝气滞引起的腹痛。",
        "script_en": "[PLACEHOLDER — replace with the real syndrome, verify before VO] From the pattern, this looks like cold-stagnation abdominal pain.",
        "production_note": "See the callout above the shot list — this line is a placeholder, not approved TCM content.",
    },
    {
        "title": "Shot 14 · ~6s · Hua Tuo's Question (rising toward climax)",
        "visual": (
            "SAME_PERSON_AS Shot 5. Locked static camera, closer than Shot 12 — Hua Tuo stops mid-task "
            "and looks directly at the host for the first time with real focus, not curiosity this time. "
            "Sound drops further toward silence. One true gesture: his hand, which had been reaching for "
            "something, goes still in mid-air."
        ),
        "script_zh": "你已经知道他得了什么病？",
        "script_en": "You already know what disease he has?",
        "production_note": "Single-speaker, static lock — dialogue-hang-safe. First shot in the act at true climax framing distance.",
    },
    {
        "title": "Shot 15 · ~5s · Host Falters",
        "visual": (
            "Reverse to host, same static lock, same near-silence. He straightens slightly, a small, "
            "visible loss of composure — not panic, just the smallest flicker of being caught. One true "
            "gesture: he opens his mouth to answer fully, then visibly shortens what he was going to say."
        ),
        "script_zh": "目前只是初步辨证。",
        "script_en": "This is only a preliminary read.",
        "production_note": "Reuse Shot 14's exact lock/light setup — shot/reverse-shot pair.",
    },
    {
        "title": "Shot 16 · ~9s · THE GOLDEN LINE (climax)",
        "visual": (
            "SAME_PERSON_AS Shot 5. Return to Hua Tuo — the closest, stillest frame of the entire "
            "episode so far. Fully locked camera, no movement at all. Sound is as close to true silence "
            "as the scene gets. He does not raise his voice; he says it plainly, almost gently, which is "
            "what makes it land as correction rather than attack. Hold on his face for a beat after the "
            "line finishes before any cut — do not rush off this shot."
        ),
        "script_zh": "你只问了他哪里痛，还没有问他为何痛。",
        "script_en": "You only asked him where it hurts. You haven't asked him why.",
        "production_note": "The thesis shot of the whole episode. Generate this one with the most care/retakes of the act — everything before it is scaffolding for this line landing clean.",
    },
    {
        "title": "Shot 17 · ~7s · Hua Tuo's Detail (release begins)",
        "visual": (
            "SAME_PERSON_AS Shot 5. Register loosens — warmer light returns, camera unlocks to a small "
            "motivated move again. Hua Tuo turns to the family member, one focused tier-2 action: he "
            "picks up or gestures toward a food container/bowl near the patient's bedside, asking a "
            "short, direct question. Patient and family stay tier-1 micro-motion only."
        ),
        "script_zh": "他昨晚吃了什么？",
        "script_en": "What did he eat last night?",
        "production_note": "Single focused action per the three-tier rule — do not also give the host a competing action in this same shot; his discovery is Shot 18.",
    },
    {
        "title": "Shot 18 · ~8s · Host's Risk Flag",
        "visual": (
            "Cut to host, his own focused tier-2 action — he leans in and gently checks the patient's "
            "lips/skin, a beat of real concern crossing his face, then turns partly to camera (documentary "
            "aside, not fully breaking to the audience) to flag it."
        ),
        "script_zh": "等一下——他嘴唇有点干，呼吸也偏浅。这个我们要小心，别用太猛的处理方式。",
        "script_en": "Wait — his lips are dry, his breathing's shallow. We need to be careful, don't push anything too aggressive.",
        "production_note": "Keep this line as a general caution, not a specific medical claim — same reasoning as the Shot 13 flag, review before final VO.",
    },
    {
        "title": "Shot 19 · ~6s · Resolution (the only shared-frame beat)",
        "visual": (
            "Wide-ish medium two-shot — both characters share the frame for the first time since the "
            "opening. A brief look between host and Hua Tuo, a small mutual nod — not competing, "
            "recognizing — then both turn back to the patient together and begin working in sync. "
            "Composed, steadier framing than the rest of the act; symmetry restored."
        ),
        "script_zh": "（无对白，一个眼神+点头）",
        "script_en": "(no dialogue — a look and a nod)",
        "production_note": "Silent synced gesture, generate as image2video (motion only), NOT multimodal2video — this is the one shot where both faces share a frame, and it's only safe because there's no audio-driven lip-sync involved.",
    },
    {
        "title": "Shot 20 · ~10s · Epilogue Reflection",
        "visual": (
            "Selfie POV again, host walking back out into daylight, warmer light returning fully "
            "(release complete) — reflective, slower pace than any selfie shot since Shot 1, a genuine "
            "small smile of realization rather than the earlier curious/hushed energy. Partway through, "
            "Hua Tuo's voice cuts in from off-camera/behind, unseen — the host's expression flicks to a "
            "small amused reaction before he turns."
        ),
        "script_zh": "我本来以为，见到华佗以后，我最想问的是针灸、方药和麻沸散。现在我发现，他真正厉害的可能不是某一个秘方，而是他从来不会太早给病人下结论。（画外音，华佗）你还走不走？下一家已经等了半个时辰。",
        "script_en": "I used to think that meeting Hua Tuo, what I'd want most to ask about was acupuncture, herbal formulas, mafeisan. Now I realize what actually makes him formidable might not be one secret technique — it's that he never rushes to a conclusion. (off-camera, Hua Tuo) Are we going or not? The next house has been waiting half an hour.",
        "production_note": "Hua Tuo's interruption is OFF-CAMERA VO over the host's shot — no new Hua Tuo coverage setup needed for this single line, saves a shot.",
    },
    {
        "title": "Shot 21 · ~6s · Button + Next-Episode Hook",
        "visual": (
            "Host turns back toward camera/Hua Tuo, small energized \"back to work\" beat: \"来了。下一位是什么情况？\" "
            "Hard cut to SAME_PERSON_AS Shot 5 — Hua Tuo, already walking again, answers without slowing down, "
            "the smallest knowing almost-smile. Hold a beat on his face, then hard cut to black."
        ),
        "script_zh": "（你）来了。下一位是什么情况？（华佗）头痛，三年。[黑屏字幕：下一集：古人的头痛，和现代人的头痛一样吗？]",
        "script_en": "(host) Coming. What's the next case? (Hua Tuo) Headache. Three years. [black card: Next episode — is an ancient headache the same as a modern one?]",
        "production_note": "This is two single-speaker beats (host line, then Hua Tuo line) inside one description for pacing — if 即梦 event-density struggles to hold both cleanly in one generation, split into two shots (21a host, 21b Hua Tuo + black card) rather than forcing it.",
    },
]


def build_blocks() -> list[dict]:
    blocks: list[dict] = [_divider(), _h2("📜 Master Script (EN gloss) — Act 2 continued")]
    for line in MASTER_SCRIPT_ACT2_EN:
        blocks.append(_bullet(line))

    blocks.append(_divider())
    blocks.append(_h2("🎬 Directorial Notes — Act 2"))
    for line in DIRECTORIAL_NOTES_ACT2:
        blocks.append(_bullet(line))

    blocks.append(_divider())
    blocks.append(_callout(DIAGNOSIS_WARNING, emoji="🚨"))

    blocks.append(_divider())
    blocks.append(_h2("🎬 Shot Guide — Act 2: The Patient"))
    for shot in SHOTS_ACT2:
        blocks.append(_h3(shot["title"]))
        blocks.append(_bullet(f"🎥 {shot['visual']}"))
        blocks.append(_bullet(f"🗣️ {shot['script_zh']}"))
        blocks.append(_bullet(f"🇬🇧 {shot['script_en']}"))
        blocks.append(_bullet(f"🎬 即梦 note: {shot['production_note']}"))

    return blocks


def main() -> int:
    ap = argparse.ArgumentParser(description="Append Act 2 to the Hua Tuo EP01 page")
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    blocks = build_blocks()
    print(f"Prepared {len(blocks)} blocks for page {PAGE_ID}")

    if args.dry_run:
        print("dry-run — not writing")
        return 0

    for i in range(0, len(blocks), 25):
        call("PATCH", f"/blocks/{PAGE_ID}/children", {"children": blocks[i:i + 25]})
        time.sleep(0.3)
        print(f"  appended blocks {i}-{min(i+25, len(blocks))}/{len(blocks)}")

    clean_id = PAGE_ID.replace("-", "")
    print(f"\n🔗 https://www.notion.so/{clean_id}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
