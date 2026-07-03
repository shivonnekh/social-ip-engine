#!/usr/bin/env python3
"""Batch-create 10 planned TCM Content Library concepts in Notion.

Each concept is created with:
  - Properties: Name, Topic, Hook, CTA, Concept Status = "✍️ Scripted"
  - Body: 📜 Master Script (EN) + 🎬 Shot Guide (4 shots, rich cinematics)

Idempotent — skips any concept whose name already exists.

Usage:
    export NOTION_KEY=ntn_...
    python3 scripts/batch_create_concepts.py
    python3 scripts/batch_create_concepts.py --dry-run   # preview only
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


# ─── API helpers ──────────────────────────────────────────────────────────────

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


# ─── Block builder ────────────────────────────────────────────────────────────

def build_body_blocks(concept: dict) -> list[dict]:
    blocks: list[dict] = []

    # Master Script (EN)
    blocks.append(_h2("📜 Master Script (EN)"))
    for line in concept["master_script_en"]:
        blocks.append(_bullet(line))

    blocks.append(_divider())

    # Shot Guide
    blocks.append(_h2("🎬 Shot Guide"))
    for shot in concept["shots"]:
        blocks.append(_h3(shot["title"]))
        blocks.append(_bullet(f"🎥 {shot['visual']}"))
        blocks.append(_bullet(f"🗣️ {shot['script']}"))
        if shot.get("overlay"):
            blocks.append(_bullet(f"💡 {shot['overlay']}"))

    return blocks


# ─── Notion helpers ───────────────────────────────────────────────────────────

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
    name = concept["name"]

    if dry_run:
        return "dry-run (would create)"

    page = call("POST", "/pages", {
        "parent": {"database_id": content_db_id},
        "properties": {
            "Name": {"title": _rt(name)},
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


# ─── Content definitions ──────────────────────────────────────────────────────

CONCEPTS: list[dict] = [
    # 1 ── Muscle Building ───────────────────────────────────────────────────
    {
        "name": "💪 Why You're Not Building Muscle",
        "topic": "💪 Fitness",
        "hook": "Working out consistently but gains are slow? Your body's missing something the gym can't fix.",
        "cta": "muscle",
        "master_script_en": [
            "You're lifting weights, eating protein — but the muscle just won't come. In TCM, that's a sign your Kidney Essence is running low.",
            "Low Kidney Essence shows up as slow recovery, soreness that lingers 3 days, and muscles that feel weak despite training.",
            "Three foods that build muscle the TCM way: black beans replenish Kidney Essence, walnuts strengthen sinew, Chinese yam builds Qi and supports the Spleen so protein actually absorbs.",
            "Comment 'muscle' and I'll send you the full TCM muscle protocol — including what to eat post-workout.",
        ],
        "shots": [
            {
                "title": "Shot 1 · ~10s · Hook",
                "visual": "Doctor in TCM clinic, arms crossed, half-smiling at camera; slow pull back reveals gym equipment B-roll insert; cut back to doctor leaning forward with knowing look.",
                "script": "You're lifting weights, eating protein — but the muscle just won't come. In TCM, that's a sign your Kidney Essence is running low.",
                "overlay": "Kidney Essence = muscle foundation",
            },
            {
                "title": "Shot 2 · ~10s · Root Cause",
                "visual": "Talking head, doctor gestures to lower back (kidney area); quick insert of tired person slumped at desk; cut to close-up of pale hands, then back to doctor.",
                "script": "Low Kidney Essence shows up as slow recovery, soreness that lingers 3 days, and muscles that feel weak despite training.",
                "overlay": "Signs: slow recovery · constant soreness · weak despite effort",
            },
            {
                "title": "Shot 3 · ~12s · TCM Solution",
                "visual": "Doctor at clinic table with black beans, walnuts, Chinese yam displayed; points to each one; insert close-up of each food; doctor holds walnut up toward camera.",
                "script": "Three foods that build muscle the TCM way: black beans replenish Kidney Essence, walnuts strengthen sinew, Chinese yam builds Qi and supports the Spleen so protein actually absorbs.",
                "overlay": "黑豆 · 核桃 · 山藥",
            },
            {
                "title": "Shot 4 · ~8s · CTA",
                "visual": "Doctor looks directly at camera, warm smile, leans slightly in toward lens.",
                "script": "Comment 'muscle' and I'll send you the full TCM muscle protocol — including what to eat post-workout.",
                "overlay": "Comment 👇 muscle",
            },
        ],
    },

    # 2 ── Immunity / Wei Qi ─────────────────────────────────────────────────
    {
        "name": "🛡️ Never Get Sick — Strengthen Your Wei Qi",
        "topic": "🛡️ Immunity",
        "hook": "Some people catch every cold. Others never do. TCM explains the difference.",
        "cta": "immune",
        "master_script_en": [
            "In TCM, immunity isn't a system — it's a force. We call it Wei Qi. When it's strong, pathogens can't enter. When it's weak, you catch everything.",
            "Weak Wei Qi signs: you get sick after every season change, your hands are always cold, you feel tired even after 8 hours of sleep.",
            "Daily Wei Qi tea: Astragalus and Prince Ginseng, simmer 20 minutes. Drink in the morning. Also — go to bed before 11, and get 20 minutes of sunlight. Your Lung Qi depends on it.",
            "Comment 'immune' and I'll send you the full seasonal Wei Qi plan — spring, summer, autumn, winter versions.",
        ],
        "shots": [
            {
                "title": "Shot 1 · ~10s · Hook",
                "visual": "Doctor in clinic holding a dried Astragalus root (黃耆), camera zooms slowly in; insert of outdoor herb market; cut back to doctor with calm knowing expression.",
                "script": "In TCM, immunity isn't a system — it's a force. We call it Wei Qi. When it's strong, pathogens can't enter. When it's weak, you catch everything.",
                "overlay": "Wei Qi = your invisible shield",
            },
            {
                "title": "Shot 2 · ~10s · Signs of Weakness",
                "visual": "Talking head, doctor counts on fingers; inserts: person blowing nose, person with cold hands warming them, close-up of pale fatigued face; cut back to doctor.",
                "script": "Weak Wei Qi signs: you get sick after every season change, your hands are always cold, you feel tired even after 8 hours of sleep.",
                "overlay": "Always tired · Cold hands · Sick every season",
            },
            {
                "title": "Shot 3 · ~12s · Daily Fix",
                "visual": "Doctor at table with Astragalus (黃耆) and Prince Ginseng (太子參); pours hot water into cup, steam rises slowly; holds cup toward camera with encouraging nod.",
                "script": "Daily Wei Qi tea: Astragalus and Prince Ginseng, simmer 20 minutes. Drink in the morning. Also — go to bed before 11, and get 20 minutes of sunlight. Your Lung Qi depends on it.",
                "overlay": "黃耆 + 太子參 tea · Sleep before 11 · Daily sunlight",
            },
            {
                "title": "Shot 4 · ~8s · CTA",
                "visual": "Doctor smiles warmly, direct to camera, slight lean forward.",
                "script": "Comment 'immune' and I'll send you the full seasonal Wei Qi plan — spring, summer, autumn, winter versions.",
                "overlay": "Comment 👇 immune",
            },
        ],
    },

    # 3 ── Stress Symptoms ────────────────────────────────────────────────────
    {
        "name": "⚡ Stress is Attacking Your Organs",
        "topic": "😤 Stress",
        "hook": "Racing heart, stomach pain, headache, can't sleep — your body is telling you stress has gone too far.",
        "cta": "stress",
        "master_script_en": [
            "In TCM, stress doesn't stay in your mind. It attacks 5 organs simultaneously — and each one sends a different distress signal.",
            "Fast heartbeat — that's your Heart. Migraines and eye strain — your Liver. Stomach pain and bloating — your Spleen. Insomnia and lower back pain — your Kidneys. All from one cause: unresolved stress.",
            "3-minute stress release: press Neiguan point on your wrist — 30 seconds each side. Then Baihui on the crown of your head. Slow breath. This calms the Heart and redirects Liver Qi downward.",
            "Comment 'stress' and I'll send the full organ-by-organ stress recovery guide.",
        ],
        "shots": [
            {
                "title": "Shot 1 · ~10s · Hook",
                "visual": "Doctor, serious expression; insert montage: clock ticking, phone with notifications flooding in, person rubbing temples; cut back to doctor leaning in, urgent but calm.",
                "script": "In TCM, stress doesn't stay in your mind. It attacks 5 organs simultaneously — and each one sends a different distress signal.",
                "overlay": "5 organs. 5 warning signs.",
            },
            {
                "title": "Shot 2 · ~12s · Organ Breakdown",
                "visual": "Talking head, doctor counts on fingers; cutaway inserts for each: hand on chest (heart palpitation), pointing to right side (liver/migraine), stomach area gesture (spleen/bloat), lower back tap (kidney/insomnia); returns to doctor.",
                "script": "Fast heartbeat — that's your Heart. Migraines and eye strain — your Liver. Stomach pain and bloating — your Spleen. Insomnia and lower back pain — your Kidneys. All from one cause: unresolved stress.",
                "overlay": "Heart · Liver · Spleen · Kidney — all from stress",
            },
            {
                "title": "Shot 3 · ~12s · Quick Release",
                "visual": "Doctor demonstrates acupressure: presses 內關穴 on wrist, close-up on finger pressing point; then touches crown of head for 百會穴; breathes slowly and visibly, demonstrating technique.",
                "script": "3-minute stress release: press Neiguan point on your wrist — 30 seconds each side. Then Baihui on the crown of your head. Slow breath. This calms the Heart and redirects Liver Qi downward.",
                "overlay": "內關 · 百會 · 3 minutes",
            },
            {
                "title": "Shot 4 · ~8s · CTA",
                "visual": "Doctor, calm and settled energy, direct to camera, warm close.",
                "script": "Comment 'stress' and I'll send the full organ-by-organ stress recovery guide.",
                "overlay": "Comment 👇 stress",
            },
        ],
    },

    # 4 ── Anxiety ────────────────────────────────────────────────────────────
    {
        "name": "😮‍💨 Constant Anxiety? Your Heart and Liver Are Out of Sync",
        "topic": "🧠 Mental Health",
        "hook": "Always on edge, heart racing for no reason — in TCM, anxiety has a root cause you can actually fix.",
        "cta": "anxiety",
        "master_script_en": [
            "In TCM, anxiety isn't a personality trait. It's a physical imbalance — Heart Blood deficiency combined with Liver Qi stagnation. One drains your calm, the other keeps you trapped in your head.",
            "Physical signs: random heart palpitations, chest tightness that comes and goes, stomach discomfort when you're worried, sighing a lot without knowing why.",
            "To calm anxiety TCM-style: sour jujube seeds nourish Heart Blood, lily bulb quiets the spirit, mimosa flower lifts mood and moves Liver Qi. Make a tea, drink at 6pm — not right before bed.",
            "Comment 'anxiety' for the full 4-week Heart-Liver balance plan.",
        ],
        "shots": [
            {
                "title": "Shot 1 · ~10s · Hook",
                "visual": "Doctor in warm clinic light, direct to camera; insert: person staring at ceiling unable to sleep, then close-up of hand pressed to chest; cut back to doctor, empathetic but composed.",
                "script": "In TCM, anxiety isn't a personality trait. It's a physical imbalance — Heart Blood deficiency combined with Liver Qi stagnation. One drains your calm, the other keeps you trapped in your head.",
                "overlay": "Heart Blood + Liver Qi = anxiety root",
            },
            {
                "title": "Shot 2 · ~10s · Physical Signs",
                "visual": "Talking head, doctor gestures to chest then stomach then head, face shows recognition — naming something familiar; slight nod after each symptom.",
                "script": "Physical signs: random heart palpitations, chest tightness that comes and goes, stomach discomfort when you're worried, sighing a lot without knowing why.",
                "overlay": "Palpitations · Chest tightness · Digestive upset",
            },
            {
                "title": "Shot 3 · ~12s · Herbal Fix",
                "visual": "Doctor at table, three herbs displayed: 酸棗仁 (jujube seeds), 百合 (lily bulb), 合歡花 (mimosa flower); holds each up gently; warm close-up insert of each herb; doctor pours tea into cup.",
                "script": "To calm anxiety TCM-style: sour jujube seeds nourish Heart Blood, lily bulb quiets the spirit, mimosa flower lifts mood and moves Liver Qi. Make a tea, drink at 6pm — not right before bed.",
                "overlay": "酸棗仁 + 百合 + 合歡花 · Drink at 6pm",
            },
            {
                "title": "Shot 4 · ~8s · CTA",
                "visual": "Doctor, soft and warm tone, slight smile, direct and unhurried to camera.",
                "script": "Comment 'anxiety' for the full 4-week Heart-Liver balance plan.",
                "overlay": "Comment 👇 anxiety",
            },
        ],
    },

    # 5 ── Shoulder / Neck Pain ───────────────────────────────────────────────
    {
        "name": "📱 Phone Neck — TCM Fixes What Stretching Can't",
        "topic": "🦴 Pain",
        "hook": "Neck and shoulder pain from your phone? Stretching helps for a day. TCM gets to the root.",
        "cta": "neck",
        "master_script_en": [
            "Phone neck isn't just a posture problem. Every hour your head tilts forward, blood flow to the neck decreases and Qi stagnates. That stagnation is why the pain always comes back.",
            "Two meridians run through your neck — the Gallbladder and the Bladder. When Qi and blood stagnate there, you get not just pain but brain fog, poor sleep, and even dizziness.",
            "Step 1: neck roll with exhale — 5 circles each side. Step 2: press Fengchi at the base of your skull, 60 seconds. Step 3: kudzu root tea — it's the TCM herb specifically for neck tension and stiffness.",
            "Comment 'neck' and I'll send the full phone-neck recovery routine — takes 5 minutes a day.",
        ],
        "shots": [
            {
                "title": "Shot 1 · ~10s · Hook",
                "visual": "Doctor mimics looking at phone, head tilted down exaggeratedly, then looks up slowly rubbing neck with wry smile; insert: close-up of hunched posture at desk, phone in hand.",
                "script": "Phone neck isn't just a posture problem. Every hour your head tilts forward, blood flow to the neck decreases and Qi stagnates. That stagnation is why the pain always comes back.",
                "overlay": "Qi stagnation = the real reason it won't heal",
            },
            {
                "title": "Shot 2 · ~10s · Root Cause",
                "visual": "Talking head, doctor traces imaginary meridian line along neck with one finger; insert: simplified meridian chart or TCM anatomy model close-up; doctor gestures outward showing the affected zone.",
                "script": "Two meridians run through your neck — the Gallbladder and the Bladder. When Qi and blood stagnate there, you get not just pain but brain fog, poor sleep, and even dizziness.",
                "overlay": "GB · BL meridians · More than just pain",
            },
            {
                "title": "Shot 3 · ~12s · 3-Step Fix",
                "visual": "Doctor demonstrates in sequence: (1) slow neck roll with exhale, eyes closed; (2) presses 風池穴 Fengchi at skull base, close-up on fingers pressing point; (3) holds up slice of kudzu root (葛根) toward camera.",
                "script": "Step 1: neck roll with exhale — 5 circles each side. Step 2: press Fengchi at the base of your skull, 60 seconds. Step 3: kudzu root tea — it's the TCM herb specifically for neck tension and stiffness.",
                "overlay": "頸部轉動 · 風池穴 · 葛根茶",
            },
            {
                "title": "Shot 4 · ~8s · CTA",
                "visual": "Doctor casually rolls his own neck, smiles at camera with slight relief expression.",
                "script": "Comment 'neck' and I'll send the full phone-neck recovery routine — takes 5 minutes a day.",
                "overlay": "Comment 👇 neck",
            },
        ],
    },

    # 6 ── Dry Eyes ───────────────────────────────────────────────────────────
    {
        "name": "👀 Dry Eyes from Screens? Your Liver Is Depleted",
        "topic": "👁️ Eye Health",
        "hook": "Eyes dry, tired, blurry after screen time? TCM has known the root cause for 2000 years.",
        "cta": "eye",
        "master_script_en": [
            "In TCM, the liver opens to the eyes. Every hour of screen time depletes Liver Blood — not just your eyes, but the organ behind them. That's why eye drops give you 10 minutes of relief and nothing more.",
            "Liver Blood deficiency in the eyes shows up as: dryness, floaters, eye fatigue after 30 minutes, blurry vision at night, and often waking between 1 and 3am — that's Liver hour.",
            "Chrysanthemum and goji tea — drink every afternoon. Then press Jingming point at the inner corner of your eyes, 30 seconds. Look up and away from your screen every 20 minutes — not your phone, something 20 feet away.",
            "Comment 'eye' and I'll send the full screen-eye recovery protocol — including the 3 liver foods to eat this week.",
        ],
        "shots": [
            {
                "title": "Shot 1 · ~10s · Hook",
                "visual": "Doctor points to his own eyes, then gestures toward an imaginary screen; insert: extreme close-up of red, dry, tired eye; cut back to doctor, calm and knowing, slight smile.",
                "script": "In TCM, the liver opens to the eyes. Every hour of screen time depletes Liver Blood — not just your eyes, but the organ behind them. That's why eye drops give you 10 minutes of relief and nothing more.",
                "overlay": "目為肝之竅 · The liver-eye connection",
            },
            {
                "title": "Shot 2 · ~10s · Signs Beyond Dryness",
                "visual": "Talking head, doctor gestures to eyes then points to side of head, holds up fingers to count symptoms; inserts: person squinting at screen late at night, person waking confused at 2am with phone showing 2:00.",
                "script": "Liver Blood deficiency in the eyes shows up as: dryness, floaters, eye fatigue after 30 minutes, blurry vision at night, and often waking between 1 and 3am — that's Liver hour.",
                "overlay": "Dryness · Floaters · 1–3am waking",
            },
            {
                "title": "Shot 3 · ~12s · Solution",
                "visual": "Doctor at table: chrysanthemum (菊花) and goji berries (枸杞) in a clear glass cup; pours hot water — flowers bloom in slow motion; then doctor presses 睛明穴 beside nose bridge, close-up on point.",
                "script": "Chrysanthemum and goji tea — drink every afternoon. Then press Jingming point at the inner corner of your eyes, 30 seconds. Look up and away from your screen every 20 minutes — not your phone, something 20 feet away.",
                "overlay": "菊花枸杞茶 · 睛明穴 · 20-20-20 rule",
            },
            {
                "title": "Shot 4 · ~8s · CTA",
                "visual": "Doctor holds blooming chrysanthemum tea cup up toward camera with warm smile.",
                "script": "Comment 'eye' and I'll send the full screen-eye recovery protocol — including the 3 liver foods to eat this week.",
                "overlay": "Comment 👇 eye",
            },
        ],
    },

    # 7 ── Migraines (General) ────────────────────────────────────────────────
    {
        "name": "🤯 Which Type of Migraine Do You Have?",
        "topic": "🦴 Pain",
        "hook": "Migraines aren't random. In TCM, there are 3 types — and each one needs a completely different fix.",
        "cta": "migraine",
        "master_script_en": [
            "Most people treat all migraines the same. TCM doesn't. There are three types — and if you've been treating the wrong one, that's why nothing works.",
            "Type 1: Liver Yang Rising — throbbing pain on the side, worse with stress, better lying still. Type 2: Blood Deficiency — dull ache, worse at end of day, you feel exhausted with it. Type 3: Phlegm-Damp — heavy, foggy headache, often with nausea.",
            "Liver Yang: chrysanthemum and cassia seed tea. Blood Deficiency: dang gui and red dates in warm water. Phlegm-Damp: ginger and tangerine peel tea. Drink the right one for your type.",
            "Comment 'migraine' and I'll send a full type quiz plus the complete treatment plan for yours.",
        ],
        "shots": [
            {
                "title": "Shot 1 · ~10s · Hook",
                "visual": "Doctor holds up 3 fingers, leans forward slightly with puzzle-solved expression; insert: person squinting in pain with hands on temples; cut back to doctor, calm and composed.",
                "script": "Most people treat all migraines the same. TCM doesn't. There are three types — and if you've been treating the wrong one, that's why nothing works.",
                "overlay": "3 types. 3 roots. 3 solutions.",
            },
            {
                "title": "Shot 2 · ~12s · The 3 Types",
                "visual": "Doctor counts on fingers: (1) points to temple and side of head with throbbing gesture; (2) touches forehead with dull press gesture and tired look; (3) draws hand across heavy foggy brow with slight nausea mime; brief inserts matching each type.",
                "script": "Type 1: Liver Yang Rising — throbbing pain on the side, worse with stress, better lying still. Type 2: Blood Deficiency — dull ache, worse at end of day, you feel exhausted with it. Type 3: Phlegm-Damp — heavy, foggy headache, often with nausea.",
                "overlay": "肝陽上亢 · 血虛 · 痰濕",
            },
            {
                "title": "Shot 3 · ~12s · Type-Matched Remedies",
                "visual": "Doctor at table, three small cups of herbs displayed side by side; points to each as he names them: chrysanthemum+cassia, dang gui+red dates, ginger+tangerine peel; close-up insert of each cup.",
                "script": "Liver Yang: chrysanthemum and cassia seed tea. Blood Deficiency: dang gui and red dates in warm water. Phlegm-Damp: ginger and tangerine peel tea. Drink the right one for your type.",
                "overlay": "菊花+決明子 · 當歸+紅棗 · 薑+陳皮",
            },
            {
                "title": "Shot 4 · ~8s · CTA",
                "visual": "Doctor, direct and confident, looks straight into camera.",
                "script": "Comment 'migraine' and I'll send a full type quiz plus the complete treatment plan for yours.",
                "overlay": "Comment 👇 migraine",
            },
        ],
    },

    # 8 ── Hormonal Migraines ─────────────────────────────────────────────────
    {
        "name": "🌙 Pre-Period Migraines — It's Your Liver-Kidney",
        "topic": "🌸 Women's Health",
        "hook": "Migraine always hits 2–3 days before your period? That timing is not a coincidence.",
        "cta": "hormone",
        "master_script_en": [
            "If your migraine arrives like clockwork before your period — day 25, day 26 — your body is showing you a Liver-Kidney imbalance. It's not random. It's a pattern TCM has seen for centuries.",
            "Before your period, Liver Blood descends to nourish the uterus. If Liver Blood is already deficient, the brain starves — and the Liver Yang has nothing to hold it down. It rises. That's your migraine.",
            "Build Liver Blood in the 2 weeks after your period: goji, dang gui, ejiao soup. Then in the week before your period, avoid cold foods and alcohol — and sleep before 10:30. Keeping the Liver Blood full prevents the drop.",
            "Comment 'hormone' and I'll send the full cycle-aware migraine prevention plan — week by week.",
        ],
        "shots": [
            {
                "title": "Shot 1 · ~10s · Hook",
                "visual": "Doctor holds up a calendar and circles days 25–28; insert: woman holding head at desk with calendar on wall behind her; cut back to doctor with knowing 'I see this all the time' expression.",
                "script": "If your migraine arrives like clockwork before your period — day 25, day 26 — your body is showing you a Liver-Kidney imbalance. It's not random. It's a pattern TCM has seen for centuries.",
                "overlay": "Pre-period migraine = Liver-Kidney deficiency",
            },
            {
                "title": "Shot 2 · ~10s · Why It Happens",
                "visual": "Talking head, doctor uses hands to illustrate flow: gestures downward (Blood descending to uterus), then shows disruption (brain starving), then hand rising (Yang ascending) — expressive and pedagogical.",
                "script": "Before your period, Liver Blood descends to nourish the uterus. If Liver Blood is already deficient, the brain starves — and the Liver Yang has nothing to hold it down. It rises. That's your migraine.",
                "overlay": "Liver Blood descends → brain gets less → pain",
            },
            {
                "title": "Shot 3 · ~12s · Cycle-Smart Fix",
                "visual": "Doctor at table with goji (枸杞), dang gui (當歸), ejiao (阿膠) displayed; points to calendar phases as he explains; close-up insert of each herb; warm amber lighting throughout.",
                "script": "Build Liver Blood in the 2 weeks after your period: goji, dang gui, ejiao soup. Then in the week before your period, avoid cold foods and alcohol — and sleep before 10:30. Keeping the Liver Blood full prevents the drop.",
                "overlay": "Days 1–14: nourish blood · Days 21–28: protect it",
            },
            {
                "title": "Shot 4 · ~8s · CTA",
                "visual": "Doctor, warm and direct, looks at camera with genuine care.",
                "script": "Comment 'hormone' and I'll send the full cycle-aware migraine prevention plan — week by week.",
                "overlay": "Comment 👇 hormone",
            },
        ],
    },

    # 9 ── Period Pain (Acute) ────────────────────────────────────────────────
    {
        "name": "🩸 Period Pain Emergency — Do This Now",
        "topic": "🌸 Women's Health",
        "hook": "Pain so bad you can't move? Here's the TCM emergency protocol for right now.",
        "cta": "period",
        "master_script_en": [
            "First: identify your type. Cold pain — cramping that feels better with heat — that's Cold Stagnation. Stabbing, fixed pain that doesn't ease with heat — that's Blood Stasis. They need different fixes.",
            "For Cold type: heat pack on lower abdomen, press Sanyinjiao point — 3 finger widths above inner ankle — for 2 minutes each side. Drink ginger and brown sugar tea hot. For Blood Stasis type: press Hegu and Sanyinjiao together.",
            "Do NOT do: cold drinks, ice cream, cold compress, or intense exercise. And don't stress — Liver Qi stagnation makes cramping worse. Keep warm, rest, and stay off the cold food.",
            "Comment 'period' and I'll send the full acute pain protocol — plus what to do the day before it starts.",
        ],
        "shots": [
            {
                "title": "Shot 1 · ~10s · Hook — Type ID",
                "visual": "Doctor, urgent but calm; insert: woman curled up on couch in pain; doctor leans into camera holding up two fingers — two types, different fixes — direct and clear.",
                "script": "First: identify your type. Cold pain — cramping that feels better with heat — that's Cold Stagnation. Stabbing, fixed pain that doesn't ease with heat — that's Blood Stasis. They need different fixes.",
                "overlay": "Cold Stagnation vs Blood Stasis · Identify first",
            },
            {
                "title": "Shot 2 · ~12s · Immediate Relief",
                "visual": "Doctor demonstrates: holds hot water bottle against lower abdomen area; then close-up of pressing 三陰交 Sanyinjiao on inner ankle — finger counts 3 widths above ankle bone; then pours ginger tea into cup, steam rising.",
                "script": "For Cold type: heat pack on lower abdomen, press Sanyinjiao point — 3 finger widths above inner ankle — for 2 minutes each side. Drink ginger and brown sugar tea hot. For Blood Stasis type: press Hegu and Sanyinjiao together.",
                "overlay": "熱敷 · 三陰交 · 合谷 · 薑糖水",
            },
            {
                "title": "Shot 3 · ~10s · What NOT To Do",
                "visual": "Doctor waves hand in a gentle lighthearted 'no' gesture; inserts: glass of ice water, ice cream cone, person stress-scrolling on phone; cut back to doctor shaking head warmly.",
                "script": "Do NOT do: cold drinks, ice cream, cold compress, or intense exercise. And don't stress — Liver Qi stagnation makes cramping worse. Keep warm, rest, and stay off the cold food.",
                "overlay": "❌ 生冷 ❌ 壓力 ❌ 劇烈運動",
            },
            {
                "title": "Shot 4 · ~8s · CTA",
                "visual": "Doctor, gentle and supportive, looks directly at camera with warm and caring expression.",
                "script": "Comment 'period' and I'll send the full acute pain protocol — plus what to do the day before it starts.",
                "overlay": "Comment 👇 period",
            },
        ],
    },

    # 10 ── Pre-Period Prevention ─────────────────────────────────────────────
    {
        "name": "📅 The Week Before Your Period Determines Everything",
        "topic": "🌸 Women's Health",
        "hook": "Most women only think about period pain during their period. TCM says the prevention window is the week before.",
        "cta": "cycle",
        "master_script_en": [
            "The pain you feel during your period was set up 5 to 7 days before it arrived. In TCM, the pre-period phase is when you either protect your body — or set yourself up for pain.",
            "Days 21 to 28: motherwort tea to move Qi and Blood gently, dang gui and red dates in warm soup for Blood nourishment. Eat warm — nothing cold, nothing raw. Your uterus is preparing and needs heat.",
            "Avoid this week: ice water, sashimi, intense cardio, staying up past midnight, and big emotional arguments. Every one of these constricts the flow of Qi and Blood heading to the uterus.",
            "Comment 'cycle' for the full monthly TCM cycle guide — what to eat in each of the 4 phases.",
        ],
        "shots": [
            {
                "title": "Shot 1 · ~10s · Hook",
                "visual": "Doctor holds up calendar and circles days 21–28 with a pen; looks at camera with a 'this is the key' expression; insert: contrast shot between period pain and the calm week before.",
                "script": "The pain you feel during your period was set up 5 to 7 days before it arrived. In TCM, the pre-period phase is when you either protect your body — or set yourself up for pain.",
                "overlay": "Day 21–28 = your pain prevention window",
            },
            {
                "title": "Shot 2 · ~12s · What To Eat",
                "visual": "Doctor at table, motherwort (益母草), dang gui (當歸), red dates (紅棗) displayed; holds each up and explains; insert: warm bowl of soup, steam rising gently; amber clinic lighting.",
                "script": "Days 21 to 28: motherwort tea to move Qi and Blood gently, dang gui and red dates in warm soup for Blood nourishment. Eat warm — nothing cold, nothing raw. Your uterus is preparing and needs heat.",
                "overlay": "益母草茶 · 當歸紅棗湯 · 溫熱飲食",
            },
            {
                "title": "Shot 3 · ~10s · What To Avoid",
                "visual": "Talking head, doctor counts avoid list on fingers; brief inserts for each: ice water glass, sashimi plate, running shoes, phone screen at 1am, person mid-argument; cut back to doctor shaking head gently.",
                "script": "Avoid this week: ice water, sashimi, intense cardio, staying up past midnight, and big emotional arguments. Every one of these constricts the flow of Qi and Blood heading to the uterus.",
                "overlay": "❌ 生冷 ❌ 熬夜 ❌ 過度運動 ❌ 情緒激動",
            },
            {
                "title": "Shot 4 · ~8s · CTA",
                "visual": "Doctor smiling warmly, holds red date or herb toward camera, close and inviting.",
                "script": "Comment 'cycle' for the full monthly TCM cycle guide — what to eat in each of the 4 phases.",
                "overlay": "Comment 👇 cycle",
            },
        ],
    },
]


# ─── Main ─────────────────────────────────────────────────────────────────────

def main() -> None:
    parser = argparse.ArgumentParser(description="Batch-create TCM content concepts in Notion")
    parser.add_argument("--dry-run", action="store_true", help="Preview only — no writes")
    args = parser.parse_args()

    ids = json.loads(IDS_PATH.read_text(encoding="utf-8"))
    content_db_id = ids["content_db"]

    print("Loading existing concepts from Content Library...")
    existing = get_existing_names(content_db_id)
    print(f"Found {len(existing)} existing concepts.\n")

    created: list[str] = []
    skipped: list[str] = []

    for concept in CONCEPTS:
        name = concept["name"]
        # Fuzzy match: skip if core name words already present
        core = name.split("·")[0].strip().lstrip("💪🛡️⚡😮📱👀🤯🌙🩸📅 ")
        if any(core[:20] in ex for ex in existing):
            print(f"  ⏭  Skip (exists): {name}")
            skipped.append(name)
            continue

        print(f"  ✍️  Creating: {name} ...", end="", flush=True)
        result = create_concept(content_db_id, concept, dry_run=args.dry_run)
        print(f" ✓ {result}")
        created.append(name)
        time.sleep(0.5)

    print(f"\n{'[DRY RUN] ' if args.dry_run else ''}Done — "
          f"created {len(created)}, skipped {len(skipped)}")
    if created:
        print("\nCreated:")
        for n in created:
            print(f"  • {n}")
    if skipped:
        print("\nSkipped (already exist):")
        for n in skipped:
            print(f"  • {n}")


if __name__ == "__main__":
    main()
