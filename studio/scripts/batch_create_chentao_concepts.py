#!/usr/bin/env python3
"""
batch_create_chentao_concepts.py
Creates 35 unique concepts in the Content Library based on Chen Tao's
content analysis (382f2a3f43208176bd49e2a2897f98ce).

Deduplication: same-script posts (foot soaks #21/#27/#36, stretch marks #4/#12/#19,
weight-loss tea #7/#14, sock marks #8/#33, baking soda neck #15/#31) collapsed into one.

Run: python3 scripts/batch_create_chentao_concepts.py
"""

import os, json, time, requests
from pathlib import Path

# ── Load env ─────────────────────────────────────────────────────────────────
env = {}
with open(Path(__file__).parent.parent / ".env") as f:
    for line in f:
        line = line.strip()
        if line and not line.startswith("#") and "=" in line:
            k, v = line.split("=", 1)
            env[k.strip()] = v.strip().strip('"').strip("'")

NOTION_KEY  = env["NOTION_KEY"]
CONTENT_DB  = "389f2a3f-4320-81f8-9428-cd01f1d36add"
HEADERS = {
    "Authorization": f"Bearer {NOTION_KEY}",
    "Notion-Version": "2022-06-28",
    "Content-Type": "application/json",
}

# ── Concept definitions ───────────────────────────────────────────────────────
# Fields: name, topic, hook, cta
# Topics: existing + new (Notion creates new select options automatically)
CONCEPTS = [
    # ── HIGH VIRAL (top performers first) ────────────────────────────────────
    {
        "name":  "Bay Leaves in Socks (Sleep + Pain)",
        "topic": "🦶 Feet / Legs",
        "hook":  "Put a few bay leaves inside your socks before bed and leave them overnight. Your body will not be the same in the morning.",
        "cta":   "bay",
    },
    {
        "name":  "Baking Soda Dark Spots (Neck + Elbows)",
        "topic": "🦷 Skin / Beauty",
        "hook":  "Put baking soda on the back of your neck and you will not believe what happens. In Chinese medicine we have used this combination for generations.",
        "cta":   "spots",
    },
    {
        "name":  "Lower Back Pain Fix (Vicks + Epsom Salt)",
        "topic": "🦴 Pain",
        "hook":  "If you have unbearable lower back pain — the kind where you cannot stand, sit, or even lie down — listen to me. This is where kidney qi flows.",
        "cta":   "back",
    },
    {
        "name":  "Lemon + Beet Blood Cleanse",
        "topic": "🫀 Liver",
        "hook":  "Put lemon on beets and just watch what happens. Western doctors do not like this because half their patients would never need them again.",
        "cta":   "beet",
    },
    {
        "name":  "Stretch Marks (Not a Skin Problem)",
        "topic": "🌸 Women's Health",
        "hook":  "Look at the stretch marks on this belly. The skin was never the problem — and in two minutes I will show you exactly what is.",
        "cta":   "marks",
    },
    {
        "name":  "Pineapple + Cinnamon Detox Smoothie",
        "topic": "🍵 Stomach",
        "hook":  "Put cinnamon on pineapple and just watch what happens. Western doctors do not like this because half their patients would never need them again.",
        "cta":   "pineapple",
    },
    {
        "name":  "Cinnamon Weight Loss Tea",
        "topic": "🍍 Detox",
        "hook":  "Do not drink this too often — because you will lose so much weight, your family might not recognize you.",
        "cta":   "tea",
    },
    {
        "name":  "Onion Slices on Feet Overnight",
        "topic": "🍍 Detox",
        "hook":  "Tape a few onion slices to the bottom of your feet one hour before sleep and leave them there all night. Here is what draws out.",
        "cta":   "onion",
    },
    {
        "name":  "Full Body Detox Foot Soak (5 Ingredients)",
        "topic": "🍍 Detox",
        "hook":  "Detox your entire body through the pores of your feet. Five simple ingredients. Twenty minutes. This is what most people never add — and it changes everything.",
        "cta":   "soak",
    },
    {
        "name":  "Eczema (Blood + Gut Root Cause)",
        "topic": "🛡️ Immunity",
        "hook":  "Look at this eczema. Western doctors gave her steroid creams. Then it came back worse. We have always known what this really means.",
        "cta":   "eczema",
    },
    {
        "name":  "Backed Up Liver (3 Warning Signs)",
        "topic": "🫀 Liver",
        "hook":  "This is a backed-up liver. Most people do not know they have one until it is too late. Here are three warning signs your body is screaming at you.",
        "cta":   "liver",
    },
    {
        "name":  "Varicose Veins (Stagnant Blood TCM)",
        "topic": "🩺 Blood / Circulation",
        "hook":  "If your hands look like this and your legs look like this, this is not aging. In Chinese medicine, we call this stagnant blood.",
        "cta":   "veins",
    },
    {
        "name":  "Swollen Ankles + Puffiness (Kidney Fluid)",
        "topic": "🫘 Kidney",
        "hook":  "Those swollen ankles and that puffiness you carry every single day? Your kidneys forgot how to let go — and nobody told you how to fix it.",
        "cta":   "ankles",
    },
    {
        "name":  "Facial Aging = Liver Blood Deficiency",
        "topic": "🦷 Skin / Beauty",
        "hook":  "If your skin is aging faster than it should, dark spots appearing, deep wrinkles — this is not your skin failing you. The liver opens to the eyes.",
        "cta":   "aging",
    },
    {
        "name":  "Buffalo Hump / Cortisol (TCM Root)",
        "topic": "😤 Stress",
        "hook":  "If you have a hump forming at the back of your neck, this is not posture. This is cortisol. In Chinese medicine we have recognized this pattern for centuries.",
        "cta":   "hump",
    },
    {
        "name":  "Sock Marks / Lymphatic Edema",
        "topic": "🦶 Feet / Legs",
        "hook":  "Your socks should not be leaving marks like this. And if they do every single day — this is not a sock problem.",
        "cta":   "socks",
    },
    {
        "name":  "Swollen + Cracked Feet (Internal Root Cause)",
        "topic": "🦶 Feet / Legs",
        "hook":  "If your feet look like this at the end of the day — swollen, heavy, cracked at the heels — this is not a foot problem. American doctors will never tell you why.",
        "cta":   "feet",
    },
    {
        "name":  "Apple PLU Sticker Warning (GMO vs Conventional)",
        "topic": "⚕️ General TCM",
        "hook":  "Never buy an apple without checking the sticker first. Most people have no idea what that little code means — but it tells you everything.",
        "cta":   "apple",
    },
    {
        "name":  "High Blood Sugar Signs (Swollen Feet, Dark Neck, Bags)",
        "topic": "🩺 Blood / Circulation",
        "hook":  "Swollen feet. Bags under your eyes that never go away. Dark patches on your neck. All three together mean one thing: high blood sugar.",
        "cta":   "sugar",
    },
    {
        "name":  "Urine Color Diagnosis (7 Colors, 6 Are Danger)",
        "topic": "🫘 Kidney",
        "hook":  "Go to the bathroom right now. Look at your urine. Tell me which of these seven colors it is — because six of them mean your body is already in trouble.",
        "cta":   "urine",
    },
    {
        "name":  "Bladder Weakness / Urinary Incontinence",
        "topic": "🫘 Kidney",
        "hook":  "If you pee when you walk, when you laugh, or when you cough — this is not just aging. This is your bladder weakened from inflammation.",
        "cta":   "bladder",
    },
    {
        "name":  "Why Nobody in China Walks Barefoot",
        "topic": "⚕️ General TCM",
        "hook":  "Do you know why nobody in China walks barefoot at home? Your feet are not just your feet. They are the most sensitive entry points in the body.",
        "cta":   "cold",
    },
    {
        "name":  "Lower Back + Hip Pain = Kidneys Crying",
        "topic": "🦴 Pain",
        "hook":  "That pain in your back and hips may not be sciatica. It could be your kidneys crying for help — and in Chinese medicine we see this every single day.",
        "cta":   "kidney",
    },
    {
        "name":  "Tongue Diagnosis for Gut Health",
        "topic": "🍵 Stomach",
        "hook":  "If your tongue has a thick white coating — fix your gut. Puffy edges with teeth marks? Fix your gut. Millions deal with this for years treating only the symptoms.",
        "cta":   "tongue",
    },
    {
        "name":  "Magnesium Deficiency (Sleep + Weight + Movement)",
        "topic": "🧠 Sleep",
        "hook":  "To have the body of your dreams, you only need three essential ingredients. Western doctors do everything possible to hide them from you.",
        "cta":   "magnesium",
    },
    {
        "name":  "Phlegm / Mucus (TCM Root Cause)",
        "topic": "🫁 Lung",
        "hook":  "That thick green phlegm can start clearing overnight. In Chinese medicine we have had the remedy for this the whole time — phlegm is not just mucus.",
        "cta":   "phlegm",
    },
    {
        "name":  "Headache Relief in 15 Seconds (Eyebrow Acupressure)",
        "topic": "🦴 Pain",
        "hook":  "Press firmly under your eyebrow ridge right now. You can eliminate your headache in under 15 seconds. This point connects to the meridians that control it.",
        "cta":   "head",
    },
    {
        "name":  "Kidney Stones (4-Day Coconut Water Flush)",
        "topic": "🫘 Kidney",
        "hook":  "Flush your kidney stones in just four days. And no, you do not need a miracle diet or a three thousand dollar surgery.",
        "cta":   "kidney",
    },
    {
        "name":  "Salt in Socks (Ancient Pain Remedy)",
        "topic": "🦶 Feet / Legs",
        "hook":  "Put salt in your socks and big pharma loses money. It sounds strange — but this is one of the most powerful remedies in Chinese medicine for thousands of years.",
        "cta":   "salt",
    },
    {
        "name":  "Nail Fungus (Overnight Garlic + Vinegar Remedy)",
        "topic": "🦶 Feet / Legs",
        "hook":  "That nail fungus on your feet can start clearing overnight. In Chinese medicine we have had the remedy for this the whole time.",
        "cta":   "nails",
    },
    {
        "name":  "Dry Cracked Heels (Overnight Fix)",
        "topic": "🦶 Feet / Legs",
        "hook":  "Those dry cracked heels can start clearing overnight. Big pharma would rather you keep buying creams that only treat the surface.",
        "cta":   "heels",
    },
    {
        "name":  "Yellow Teeth (Baking Soda + Banana Peel)",
        "topic": "⚕️ General TCM",
        "hook":  "The yellow stains on your teeth can start coming off in under 2 minutes. In Chinese medicine we have had a remedy for this since long before whitening strips existed.",
        "cta":   "teeth",
    },
    {
        "name":  "Skin Tags (Shrink Overnight with Castor Oil)",
        "topic": "⚕️ General TCM",
        "hook":  "Those skin tags can start shrinking overnight. In Chinese medicine we have known this remedy for thousands of years. Big pharma will charge you hundreds.",
        "cta":   "tags",
    },
    {
        "name":  "Bad Breath (Gut Root Cause + Oral Rinse Fix)",
        "topic": "⚕️ General TCM",
        "hook":  "Check your breath right now. Put your hand in front of your mouth and breathe out. If it smells — and you can see it on people's faces — save this.",
        "cta":   "breath",
    },
    {
        "name":  "Tonsil Stones (Hidden in Throat, TCM Fix)",
        "topic": "🦠 Tonsil Stone",
        "hook":  "Watch what came out of her throat. Tonsil stones. She came to me embarrassed about her breath — this is what was hiding in there.",
        "cta":   "tonsil",
    },
]


# ── Notion page creator ───────────────────────────────────────────────────────
def create_concept(c: dict) -> dict:
    payload = {
        "parent": {"database_id": CONTENT_DB},
        "properties": {
            "Name": {
                "title": [{"text": {"content": c["name"]}}]
            },
            "Topic": {
                "select": {"name": c["topic"]}
            },
            "Hook": {
                "rich_text": [{"text": {"content": c["hook"]}}]
            },
            "CTA": {
                "rich_text": [{"text": {"content": f'Comment "{c["cta"]}"'}}]
            },
            "Concept Status": {
                "select": {"name": "💡 Idea"}
            },
        },
    }
    r = requests.post(
        "https://api.notion.com/v1/pages",
        headers=HEADERS,
        json=payload,
    )
    if r.status_code != 200:
        return {"error": r.status_code, "msg": r.text[:200], "name": c["name"]}
    return {"ok": True, "id": r.json()["id"], "name": c["name"]}


# ── Main ───────────────────────────────────────────────────────────────────────
def main():
    print(f"Creating {len(CONCEPTS)} concepts in Content Library...\n")
    results = []
    for i, c in enumerate(CONCEPTS, 1):
        res = create_concept(c)
        status = "✅" if res.get("ok") else "❌"
        print(f"  {status} [{i:02d}/{len(CONCEPTS)}] {c['name']}")
        if not res.get("ok"):
            print(f"       ERROR: {res.get('msg','')}")
        results.append(res)
        time.sleep(0.35)  # stay well under Notion rate limit (3 req/s)

    ok  = sum(1 for r in results if r.get("ok"))
    err = len(results) - ok
    print(f"\nDone: {ok} created, {err} errors")
    if err:
        print("Failed concepts:")
        for r in results:
            if not r.get("ok"):
                print(f"  - {r['name']}: {r.get('msg','')}")


if __name__ == "__main__":
    main()
