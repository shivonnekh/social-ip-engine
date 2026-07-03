#!/usr/bin/env python3
"""
append_material.py — append ONLY the Material (DM/Infographic) section to the 5
pre-existing concepts that already have Master Script + Shot Guide but no Material.

Non-destructive: appends a divider + PROTOCOL callout + 3 DM/infographic blocks
to the END of the page. Skips a page if it already contains an Infographic Brief.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
import notion_video as nv
from build_content_bodies import divider, callout, h3, code

# title-substring -> material content
MATERIAL = {
    "Stomach pain after meals": {
        "first_dm": (
            "Hey! Warming a cold weak stomach is the whole game here 🍵\n\n"
            "Quick check so I send the right plan — is your stomach pain better with warmth and worse with cold/raw food?"
        ),
        "infographic_brief": (
            "Vertical infographic, 4:5 ratio, warm TCM clinic aesthetic (cream bg, terracotta + sage accents).\n"
            "Title: 'Stomach Pain After Meals — Warm the Spleen'.\n"
            "Three panels:\n"
            "1) WHY — stomach icon; text: cold weak spleen/stomach from cold drinks, raw food, eating while stressed.\n"
            "2) DAILY FIX — porridge + ginger icons; text: warm millet porridge each morning, ginger tea, eat calm + slow.\n"
            "3) AVOID — text: iced drinks, raw salads, skipping meals, late heavy dinners.\n"
            "Footer: 'Severe pain, weight loss, or black stool? See a doctor.' Flat icons only."
        ),
        "second_dm": (
            "Here's your warm-stomach guide — warm millet porridge in the morning is the anchor 🍵\n\n"
            "Want the full spleen-warming food list that stops it returning? Reply 'warm'."
        ),
    },
    "Knee pain isn't just old age": {
        "first_dm": (
            "Hey! Cold-damp knee pain responds really well to warmth + circulation 🦵\n\n"
            "Quick q so I tailor it — are your knees worse in cold/damp weather and a bit stiff in the morning?"
        ),
        "infographic_brief": (
            "Vertical infographic, 4:5 ratio, warm TCM clinic aesthetic.\n"
            "Title: 'Knee Pain — Clear Cold, Damp + Stagnation'.\n"
            "Three panels:\n"
            "1) WHY — knee icon; text: cold + dampness + poor circulation lodge in the joint, not just 'age'.\n"
            "2) DAILY FIX — heat + massage icons; text: warm the knee, ginger-oil rub, gentle bend-and-straighten moves.\n"
            "3) STRENGTHEN — text: keep knees covered, black beans + walnuts, avoid cold floors + damp.\n"
            "Footer: 'Hot, red, swollen, or locked knee? See a doctor.' Flat icons only."
        ),
        "second_dm": (
            "Here's your knee guide — heat first, gentle movement second, never force it 🦵\n\n"
            "Want the kidney + circulation routine that protects the joint? Reply 'strong'."
        ),
    },
    "Can't sleep? Your heart and liver": {
        "first_dm": (
            "Hey! Heart-and-liver sleep issues each have a different fix 🌙\n\n"
            "Quick check so I send the right one — do you struggle to FALL asleep, or WAKE around 1–3am and can't settle?"
        ),
        "infographic_brief": (
            "Vertical infographic, 4:5 ratio, warm TCM clinic aesthetic.\n"
            "Title: 'Can't Sleep? Heart vs Liver'.\n"
            "Two comparison columns:\n"
            "HEART (can't fall asleep, racing mind, palpitations) → calm the shen: warm milk + red dates, less screens, breathing.\n"
            "LIVER (wake 1–3am, tense, irritable) → soothe the liver: lighter dinners, no late alcohol, side stretches.\n"
            "Bottom strip: 'Both: sleep before 11pm, warm foot soak, dim lights.'\n"
            "Footer: 'Ongoing insomnia? See a practitioner.' Flat icons only."
        ),
        "second_dm": (
            "Here's your sleep-type guide — match the column to your pattern 🌙\n\n"
            "Want the full evening wind-down routine for your type? Reply 'sleep'."
        ),
    },
    "Put cinnamon on pineapple": {
        "first_dm": (
            "Hey! Pineapple + cinnamon is a gentle digestion + detox combo 🍍\n\n"
            "Quick q so I tailor it — is your main goal less bloating, better digestion, or feeling lighter overall?"
        ),
        "infographic_brief": (
            "Vertical infographic, 4:5 ratio, warm TCM clinic aesthetic.\n"
            "Title: 'Pineapple + Cinnamon — Gentle Detox'.\n"
            "Three panels:\n"
            "1) WHY — stomach icon; text: pineapple clears damp-heat + aids digestion, cinnamon warms the center.\n"
            "2) RECIPE — pineapple + cinnamon icons; text: fresh pineapple + a pinch of cinnamon, warm water, in the morning.\n"
            "3) SUPPORT — text: eat slowly, warm meals, skip ice-cold drinks.\n"
            "Footer: 'Acid reflux or mouth sensitivity? Go easy on pineapple.' Flat icons only."
        ),
        "second_dm": (
            "Here's your gentle-detox guide — warm water not iced keeps it kind on the gut 🍍\n\n"
            "Want the full anti-bloat morning routine? Reply 'gut'."
        ),
    },
    "Watch what came out of her throat": {
        "first_dm": (
            "Hey! Tonsil stones almost always trace back to the gut, not just the throat 🌿\n\n"
            "Quick check so I send the right plan — is your bad breath worse in the morning, or all day even after brushing?"
        ),
        "infographic_brief": (
            "Vertical infographic, 4:5 ratio, warm TCM clinic aesthetic.\n"
            "Title: 'Tonsil Stones — The Gut–Throat Connection'.\n"
            "Three panels:\n"
            "1) WHY THEY FORM — throat + stones icon; text: dampness, heat, food stagnation rising up.\n"
            "2) DAILY GARGLE — glass + salt + lemon icons; text: warm water, 1 tsp sea salt, squeeze of lemon, gargle after meals.\n"
            "3) ROOT FIX — stomach icon; text: warm cooked food, less dairy + sugar, support digestion.\n"
            "Footer: 'Persistent? See a practitioner.' Flat icons only."
        ),
        "second_dm": (
            "Here's your tonsil-stone guide — start the gargle tonight and watch the breath improve 🧂\n\n"
            "Want the full gut-reset that stops them coming back? Reply 'gut'."
        ),
    },
}


def build_material_blocks(m: dict) -> list:
    return [
        divider(),
        callout(
            "📩 PROTOCOL — DM flow triggered when viewer comments the CTA keyword. "
            "First DM = instant text. After any reply, send the infographic + second DM.",
            "📩"),
        h3("💬 First DM — send immediately (text only)"),
        code(m["first_dm"]),
        h3("🖼️ Infographic Brief — paste into GPT image gen"),
        code(m["infographic_brief"]),
        h3("💬 Second DM — send after any reply (attach infographic)"),
        code(m["second_dm"]),
    ]


def main() -> int:
    targets = json.load(open("/tmp/need_material.json"))
    for t in targets:
        m = next((v for k, v in MATERIAL.items() if k in t["title"]), None)
        if not m:
            print(f"  ✗ no material authored for: {t['title']}"); continue
        existing = " ".join(nv._txt(b) for b in nv._children(t["id"]))
        if "Infographic Brief" in existing:
            print(f"  ⏭  already has Material: {t['title'][:45]}"); continue
        nv.ncall_w("PATCH", f"/blocks/{t['id']}/children",
                   {"children": build_material_blocks(m)})
        print(f"  ✅ appended Material: {t['title'][:45]}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
