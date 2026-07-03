#!/usr/bin/env python3
"""Append a 📩 Protocol section to each of the 10 new Content Library concepts.

Protocol = the DM flow triggered when a viewer comments the CTA keyword:
  💬 First DM  → text-only (sent immediately — Meta allows no image on first contact)
  🖼️ Infographic Brief → detailed GPT image prompt (Shivonne generates manually)
  💬 Second DM → sent after any reply, accompanies the infographic

Idempotent — skips pages that already have a Protocol section (sentinel check).

Usage:
    python3 scripts/add_protocols.py
    python3 scripts/add_protocols.py --dry-run
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
SENTINEL = "📩 PROTOCOL"


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


def _code(text: str) -> dict:
    return {"object": "block", "type": "code",
            "code": {"rich_text": _rt(text), "language": "plain text"}}


def _divider() -> dict:
    return {"object": "block", "type": "divider", "divider": {}}


def _callout(text: str, emoji: str = "📩", color: str = "green_background") -> dict:
    return {"object": "block", "type": "callout", "callout": {
        "rich_text": _rt(text),
        "icon": {"type": "emoji", "emoji": emoji},
        "color": color,
    }}


# ─── Notion helpers ───────────────────────────────────────────────────────────

def _all_children(block_id: str) -> list[dict]:
    out, cursor = [], None
    while True:
        suffix = "?page_size=100" + (f"&start_cursor={cursor}" if cursor else "")
        data = call("GET", f"/blocks/{block_id}/children{suffix}")
        out.extend(data["results"])
        if data.get("has_more"):
            cursor = data["next_cursor"]
        else:
            break
    return out


def _txt(block: dict) -> str:
    t = block["type"]
    return "".join(x.get("plain_text", "") for x in block.get(t, {}).get("rich_text", []))


def _has_protocol(page_id: str) -> bool:
    for b in _all_children(page_id):
        if b["type"] == "callout" and SENTINEL in _txt(b):
            return True
        if b["type"] == "heading_2" and SENTINEL in _txt(b):
            return True
    return False


def find_concept_by_name(content_db_id: str, name_fragment: str) -> str | None:
    """Return page_id of the first concept whose title contains name_fragment."""
    cursor: str | None = None
    while True:
        body: dict = {"page_size": 100}
        if cursor:
            body["start_cursor"] = cursor
        data = call("POST", f"/databases/{content_db_id}/query", body)
        for page in data["results"]:
            for prop in page["properties"].values():
                if prop.get("type") == "title":
                    title = "".join(t["plain_text"] for t in prop["title"])
                    if name_fragment.lower() in title.lower():
                        return page["id"]
        if data.get("has_more"):
            cursor = data["next_cursor"]
        else:
            break
    return None


def append_protocol(page_id: str, protocol: dict, *, dry_run: bool = False) -> str:
    if _has_protocol(page_id):
        return "exists — skipped"
    if dry_run:
        return "dry-run (would append)"

    blocks = [
        _divider(),
        _callout(
            f"{SENTINEL} — DM flow triggered when viewer comments the CTA keyword. "
            "First DM = text only (Meta rule: no image on first contact). "
            "Image sent after any reply.",
            emoji="📩",
            color="green_background",
        ),
        _h3("💬 First DM — send immediately (text only)"),
        _code(protocol["first_dm"]),
        _h3("🖼️ Infographic Brief — paste into GPT image gen"),
        _code(protocol["image_brief"]),
        _h3("💬 Second DM — send after any reply (attach infographic)"),
        _code(protocol["second_dm"]),
    ]

    for i in range(0, len(blocks), 25):
        call("PATCH", f"/blocks/{page_id}/children", {"children": blocks[i:i + 25]})
        time.sleep(0.3)

    return "appended"


# ─── Protocol definitions ─────────────────────────────────────────────────────

PROTOCOLS: list[dict] = [
    # 1 ── Muscle Building ───────────────────────────────────────────────────
    {
        "concept": "Building Muscle",
        "first_dm": (
            "Hey! Thanks for commenting — you're in the right place 💪\n\n"
            "Here's your quick TCM muscle protocol:\n"
            "• Build Kidney Essence first: black beans, walnuts, Chinese yam (山藥) daily\n"
            "• Time your protein: eat within 30 min post-workout WITH warm food — cold shakes "
            "block Spleen absorption and slow gains\n"
            "• Sleep before 11pm: Kidney Essence rebuilds between 11pm–1am. "
            "This is when your gains actually happen.\n\n"
            "Quick question — which feels more like you: "
            "slow recovery (3+ days sore), or training hard but muscles feel 'soft'?"
        ),
        "image_brief": (
            "Vertical infographic, 4:5 ratio, warm TCM aesthetic.\n"
            "Title: 'TCM Muscle Building Protocol' — bold serif font.\n"
            "Subtitle: 'Build from the Root — Kidney Essence'\n"
            "Background: warm cream/beige with subtle ink-wash herb illustrations in corners.\n\n"
            "5 protocol points in a clean list with small herb icons:\n"
            "1. 🫘 Black beans (黑豆) — replenish Kidney Essence · handful daily\n"
            "2. 🌰 Walnuts (核桃) — strengthen sinew and tendon · 5–7 daily\n"
            "3. 🍠 Chinese Yam (山藥) — Spleen Qi for protein absorption\n"
            "4. 🌙 Sleep before 11pm — Kidney rebuilds 11pm–1am\n"
            "5. 🌡️ Eat warm post-workout — cold foods block Spleen, slow gains\n\n"
            "Bottom strip: warm amber banner — 'Comment MUSCLE for your personalized plan'\n"
            "Style: clean, educational, no face/person — herbs and simple icons only. "
            "Warm cream + amber palette."
        ),
        "second_dm": (
            "Here's your full TCM muscle protocol — screenshot this and keep it 💪\n"
            "Start with the foods this week. Sleep before 11. "
            "Give it 3 weeks and notice the difference in your recovery."
        ),
    },

    # 2 ── Immunity / Wei Qi ─────────────────────────────────────────────────
    {
        "concept": "Wei Qi",
        "first_dm": (
            "Hey! Wei Qi is everything when it comes to not catching every cold 🛡️\n\n"
            "Your quick Wei Qi protocol:\n"
            "• Morning tea: Astragalus (黃耆) + Prince Ginseng (太子參) — simmer 20 min, drink before 9am\n"
            "• Sleep before 11pm: Wei Qi rebuilds during deep sleep. Past midnight = Wei Qi drain.\n"
            "• 20 min of sunlight daily: Lung Qi (which generates Wei Qi) needs sunlight to stay active\n\n"
            "Tell me — do you get sick after every season change, "
            "or is it more like you're always tired and never feel 100%?"
        ),
        "image_brief": (
            "Vertical infographic, 4:5 ratio, TCM immunity aesthetic.\n"
            "Title: 'Wei Qi Immunity Protocol' — bold serif.\n"
            "Subtitle: 'Your Daily Invisible Shield'\n"
            "Background: soft jade green with subtle brush-stroke borders.\n"
            "Header note (italic): 'Wei Qi = your body's protective force field'\n\n"
            "5 protocol points:\n"
            "1. ☀️ Morning Wei Qi Tea: Astragalus (黃耆) + Prince Ginseng (太子參) "
            "— simmer 20 min, drink before 9am\n"
            "2. 🌙 Sleep before 11pm every night\n"
            "3. ☀️ 20 minutes of sunlight daily\n"
            "4. 🧣 Cover your neck in wind — Wind carries all pathogens in TCM\n"
            "5. 🍲 Eat cooked warm food — raw/cold weakens Spleen, which feeds Wei Qi\n\n"
            "Seasonal note at bottom: 'Double dose during season changes'\n"
            "Style: clean, educational. Warm jade-green palette. "
            "Herb illustrations (astragalus root). No face/person."
        ),
        "second_dm": (
            "Your Wei Qi protocol is attached — screenshot this and put it somewhere you'll see it 🛡️\n"
            "The morning tea is the biggest move. Start tomorrow."
        ),
    },

    # 3 ── Stress Symptoms ────────────────────────────────────────────────────
    {
        "concept": "Stress is Attacking",
        "first_dm": (
            "Hey! So glad you caught that — stress is silent but it hits hard in TCM 🏥\n\n"
            "Your 3-minute organ stress release:\n"
            "• Press Neiguan (內關) — inside of wrist, 3 finger widths from wrist crease. "
            "30 seconds each side.\n"
            "• Press Baihui (百會) — crown of your head. 60 seconds. Slow breath.\n"
            "• After: drink warm water with a slice of ginger. Helps Spleen recover.\n\n"
            "Which organ feels most affected for you — heart (palpitations/anxiety), "
            "stomach (bloating/pain), or sleep (insomnia/restless)?"
        ),
        "image_brief": (
            "Vertical infographic, 4:5 ratio, TCM body-mapping aesthetic.\n"
            "Title: 'Stress & Your Organs — TCM Protocol'\n"
            "Subtitle: '3 Minutes to Release What Stress Builds Up'\n"
            "Background: warm white with amber tones.\n\n"
            "Left side — simplified body outline with 4 organs highlighted:\n"
            "  ❤️ Heart → palpitations, racing heart\n"
            "  🫀 Liver → migraines, eye strain, irritability\n"
            "  🫁 Spleen → bloating, stomach pain, low appetite\n"
            "  🫘 Kidney → insomnia, lower back pain, fatigue\n\n"
            "Right side — 2 acupressure points with small location diagrams:\n"
            "  內關 Neiguan — inner wrist, 3 fingers from crease\n"
            "  百會 Baihui — crown of head\n\n"
            "Bottom: '3 minutes daily. Press. Breathe. Release.'\n"
            "Style: clean medical illustration, warm amber/cream palette. No face/person."
        ),
        "second_dm": (
            "Here's your stress + organ protocol — the body map is the key part, screenshot it 📲\n"
            "The 3-minute acupressure routine works best at 6pm, before dinner."
        ),
    },

    # 4 ── Anxiety ────────────────────────────────────────────────────────────
    {
        "concept": "Anxiety",
        "first_dm": (
            "Hey! Heart-Liver imbalance is one of the most common root causes of anxiety I see 💚\n\n"
            "Your 4-week anxiety reset — start this week:\n"
            "• Evening tea at 6pm: Sour jujube seeds (酸棗仁) + Lily bulb (百合) + "
            "Mimosa flower (合歡花) — steep 15 min\n"
            "• No screens after 9pm: screen light aggravates Liver Yang and keeps the mind up\n"
            "• 5 intentional sighs before bed: moves stuck Liver Qi, signals nervous system to downshift\n\n"
            "Do you notice your anxiety more in your chest (tight/heavy), "
            "your stomach (unsettled), or your head (racing thoughts)?"
        ),
        "image_brief": (
            "Vertical infographic, 4:5 ratio, calm TCM botanical aesthetic.\n"
            "Title: 'TCM Anxiety Reset Protocol'\n"
            "Subtitle: 'Heart Blood + Liver Qi — 4 Weeks to Balance'\n"
            "Background: soft lavender-cream with delicate mimosa flower (合歡花) illustrations.\n\n"
            "Two sections:\n\n"
            "Section 1 — 'What's happening inside' (small, explanatory):\n"
            "  Heart Blood deficiency → restless mind, palpitations\n"
            "  Liver Qi stagnation → trapped emotions, chest tightness\n\n"
            "Section 2 — 'Your daily protocol':\n"
            "  1. 🌿 6pm tea: 酸棗仁 + 百合 + 合歡花 (steep 15 min)\n"
            "  2. 📵 No screens after 9pm\n"
            "  3. 😤 5 intentional sighs before bed\n"
            "  4. 🛏️ Sleep before 11pm (Heart Blood rebuilds 11pm–1am)\n"
            "  5. 🚶 30-min walk daily — moves Liver Qi gently\n\n"
            "Bottom quote: 'Give it 4 weeks. The root shifts slowly — and it shifts.'\n"
            "Style: soft, hopeful. Lavender-cream palette. Botanical illustration feel. "
            "No face/person — herb and flower illustrations only."
        ),
        "second_dm": (
            "Here's your anxiety reset protocol — save this one 💜\n"
            "Start with the 6pm tea this week. "
            "It's the smallest change with the biggest downstream effect."
        ),
    },

    # 5 ── Phone Neck ─────────────────────────────────────────────────────────
    {
        "concept": "Phone Neck",
        "first_dm": (
            "Hey! Phone neck is one of the fastest-growing complaints I see — you're not alone 📱\n\n"
            "Your 5-minute daily neck recovery routine:\n"
            "• Neck roll with exhale: 5 slow circles each direction. "
            "Exhale on the way down — that's when the muscle releases.\n"
            "• Fengchi (風池) point: base of skull, in the two hollows where neck meets skull. "
            "Press 60 seconds.\n"
            "• Kudzu root (葛根) tea: drink once daily — specifically targets neck and "
            "upper back stiffness in TCM.\n\n"
            "Is your pain more in the neck itself, the shoulders pulling down, "
            "or do you also get headaches from it?"
        ),
        "image_brief": (
            "Vertical infographic, 4:5 ratio, clean TCM anatomy aesthetic.\n"
            "Title: 'Phone Neck Recovery — 5-Minute Daily Protocol'\n"
            "Subtitle: 'Unblock the Gallbladder & Bladder Meridians'\n"
            "Background: clean white with warm beige border.\n\n"
            "Top section: side-profile neck outline showing GB and BL meridian pathways "
            "highlighted in amber (simple anatomical illustration).\n\n"
            "Protocol steps — numbered list:\n"
            "1. 🔄 Neck roll with exhale — 5 circles each side, slow\n"
            "2. 👆 Press Fengchi (風池) — 60 seconds, base of skull hollows "
            "[small diagram showing point location]\n"
            "3. 🍵 Kudzu root tea (葛根茶) — 1 cup daily\n"
            "4. 📱 Phone at eye level — raise your screen, not your head\n"
            "5. ⏰ Every 45 min: look up + shoulder rolls x10\n\n"
            "Bottom: 'Stagnation breaks with consistency. 5 min/day.'\n"
            "Style: clean anatomical illustration, warm white + amber. No face/person."
        ),
        "second_dm": (
            "Your phone neck protocol is attached — the Fengchi point diagram is the part to screenshot 📲\n"
            "Do the neck roll every morning before you pick up your phone. Game changer."
        ),
    },

    # 6 ── Dry Eyes ───────────────────────────────────────────────────────────
    {
        "concept": "Dry Eyes",
        "first_dm": (
            "Hey! The liver-eye connection is one of TCM's most underrated insights 👁️\n\n"
            "Your screen-eye recovery protocol:\n"
            "• Chrysanthemum + goji tea (菊花枸杞茶): drink every afternoon — "
            "afternoon is when Liver Qi starts to settle, not morning\n"
            "• Jingming point (睛明): inner corner of each eye, beside the nose. "
            "Press gently 30 seconds each side.\n"
            "• 20-20-20 with a twist: every 20 min, look 20 feet away for 20 seconds — "
            "then blink 10 times rapidly to reset tear film.\n\n"
            "Do you also wake up between 1 and 3am? "
            "That's a key Liver Blood signal I want to check."
        ),
        "image_brief": (
            "Vertical infographic, 4:5 ratio, clean eye health + TCM aesthetic.\n"
            "Title: 'Screen Eye Recovery — TCM Protocol'\n"
            "Subtitle: 'Nourish Liver Blood. Restore Your Eyes.'\n"
            "Background: soft white with pale blue-green accents, "
            "chrysanthemum (菊花) illustration top right corner.\n\n"
            "Section 1 — '3 Liver Blood Foods for Eye Health':\n"
            "  1. 🌼 Chrysanthemum (菊花) — clears Liver heat from the eyes\n"
            "  2. 🔴 Goji berries (枸杞) — nourishes Liver and Kidney Yin\n"
            "  3. 🫐 Blueberries — supports retinal health\n\n"
            "Section 2 — 'Daily Habits':\n"
            "  1. 💧 Chrysanthemum + goji tea — 1 cup every afternoon\n"
            "  2. 👆 Jingming point (睛明) — 30s each side "
            "[small eye diagram showing point at inner corner]\n"
            "  3. 👀 20-20-20 rule + 10 blinks\n"
            "  4. 🌙 Sleep before 11pm — Liver regenerates 11pm–3am\n\n"
            "Bottom: 'Drops fix the symptom. TCM fixes the source.'\n"
            "Style: clean, calm. Soft blue-green and cream palette. "
            "Chrysanthemum illustration. No face/person."
        ),
        "second_dm": (
            "Here's your screen-eye protocol — the Jingming point diagram is the key part 👁️\n"
            "Start the chrysanthemum tea this week. Your eyes will feel different in 10 days."
        ),
    },

    # 7 ── Migraines General ──────────────────────────────────────────────────
    {
        "concept": "Type of Migraine",
        "first_dm": (
            "Hey! Getting your migraine type right changes everything 🧠\n\n"
            "Quick type check — which sounds most like you?\n"
            "• Type 1 (Liver Yang Rising / 肝陽上亢): Throbbing, one side, "
            "worse when stressed, better lying in a dark room\n"
            "• Type 2 (Blood Deficiency / 血虛): Dull, heavy, worse at end of day, "
            "comes with fatigue\n"
            "• Type 3 (Phlegm-Damp / 痰濕): Heavy, foggy, often with nausea, "
            "worse in damp weather\n\n"
            "Reply with your type (1, 2, or 3) and I'll send your specific protocol "
            "+ the right tea to make this week."
        ),
        "image_brief": (
            "Vertical infographic, 4:5 ratio, TCM diagnostic comparison aesthetic.\n"
            "Title: 'TCM Migraine Types — Know Yours, Fix Yours'\n"
            "Background: clean white with subtle ink-wash head/brain illustration at top.\n\n"
            "Three-column comparison layout:\n\n"
            "Column 1 — 肝陽上亢 Liver Yang Rising:\n"
            "  Pain: throbbing, one side\n"
            "  Trigger: stress, anger\n"
            "  Better: lying down, dark room\n"
            "  ✅ Tea: 菊花 + 決明子\n\n"
            "Column 2 — 血虛 Blood Deficiency:\n"
            "  Pain: dull, heavy\n"
            "  Trigger: end of day, fatigue\n"
            "  Better: after eating, rest\n"
            "  ✅ Tea: 當歸 + 紅棗\n\n"
            "Column 3 — 痰濕 Phlegm-Damp:\n"
            "  Pain: foggy, heavy, nausea\n"
            "  Trigger: damp weather, heavy meals\n"
            "  Better: moving around\n"
            "  ✅ Tea: 薑 + 陳皮\n\n"
            "Bottom: 'Wrong type = wrong fix. Right type = real relief.'\n"
            "Style: clean 3-column grid, amber accent lines, professional diagnostic feel. "
            "No face/person — herb icons only."
        ),
        "second_dm": (
            "Here's your full migraine type guide — screenshot the column that matches you 🤯\n"
            "Drink your type's tea daily, not just when the pain hits. "
            "Prevention is the whole game."
        ),
    },

    # 8 ── Hormonal Migraines ─────────────────────────────────────────────────
    {
        "concept": "Pre-Period Migraines",
        "first_dm": (
            "Hey! That pre-period timing is SO specific and SO fixable in TCM 🌙\n\n"
            "The key insight: you need to build Liver Blood in the 2 weeks AFTER your period ends, "
            "so there's enough to go around when it descends pre-period.\n\n"
            "Your cycle-aware plan:\n"
            "• Days 1–14 (after period): Goji + dang gui + ejiao soup, 3x per week — "
            "this is your Liver Blood building window\n"
            "• Days 21–28 (before period): Sleep before 10:30pm. No alcohol. No cold food. "
            "Protect what you built.\n"
            "• Day of migraine: Press Taichong (太衝) — between big and second toe, "
            "60 seconds each side. Brings Liver Yang down.\n\n"
            "Which week are you in right now?"
        ),
        "image_brief": (
            "Vertical infographic, 4:5 ratio, feminine TCM cycle aesthetic.\n"
            "Title: 'Hormonal Migraine Prevention — Cycle Protocol'\n"
            "Subtitle: 'Build Liver Blood. Stop the Drop.'\n"
            "Background: soft dusty rose with moon phase illustration at top.\n\n"
            "Circular cycle diagram divided into 4 phases:\n"
            "  Phase 1 (Days 1–7, during period): 'Rest + light nourishment'\n"
            "  Phase 2 (Days 8–14): '🌟 BUILD LIVER BLOOD — goji, dang gui, ejiao 3x/week'\n"
            "  Phase 3 (Days 15–21): 'Maintain — warm foods, moderate activity'\n"
            "  Phase 4 (Days 22–28): '⚠️ PROTECT — sleep before 10:30, no cold, no alcohol'\n\n"
            "Emergency point box at bottom:\n"
            "  太衝 Taichong — small foot diagram showing point between big and second toe\n"
            "  'Press when migraine starts — brings Liver Yang down'\n\n"
            "Key insight callout: 'The migraine happens in Phase 4. The fix happens in Phase 2.'\n"
            "Style: soft rose and dusty lavender, moon cycle motif, clean and feminine. "
            "No face/person — moon and botanical elements only."
        ),
        "second_dm": (
            "Here's your hormonal migraine cycle protocol — save the diagram 🌙\n"
            "The Phase 2 foods are the most important part. Start there."
        ),
    },

    # 9 ── Period Pain Acute ───────────────────────────────────────────────────
    {
        "concept": "Period Pain Emergency",
        "first_dm": (
            "Hey! Let's get you some relief — but type ID first 🩸\n\n"
            "Two quick questions:\n"
            "1. Does a heat pack on your lower abdomen make the pain better or does it not really help?\n"
            "   → Better = Cold Stagnation type\n"
            "   → Doesn't help much = Blood Stasis type\n\n"
            "2. Is the pain crampy and wave-like, or stabbing and fixed in one spot?\n\n"
            "Tell me which, and I'll send the exact protocol for your type — "
            "including the right acupressure combo."
        ),
        "image_brief": (
            "Vertical infographic, 4:5 ratio, urgent but calm TCM medical aesthetic.\n"
            "Title: 'Period Pain Emergency Protocol'\n"
            "Subtitle: 'Identify Your Type. Act Fast.'\n"
            "Background: deep warm red-cream gradient, clinical and reassuring.\n\n"
            "Split two-column layout:\n\n"
            "Left column — ❄️ Cold Stagnation (寒凝):\n"
            "  Signs: better with heat · crampy wave pain · feels cold\n"
            "  1. 🌡️ Heat pack on lower abdomen\n"
            "  2. 👆 Press 三陰交 Sanyinjiao — inner ankle, 3 fingers above bone · 2 min each\n"
            "  3. 🍵 Ginger + brown sugar tea, drink hot\n"
            "  ❌ Avoid: ice, cold drinks, cold compress\n\n"
            "Right column — 🔴 Blood Stasis (血瘀):\n"
            "  Signs: stabbing fixed pain · heat doesn't help · clots\n"
            "  1. 👆 Press 合谷 Hegu + 三陰交 Sanyinjiao together · 2 min\n"
            "  2. 🚶 Gentle slow walking — moves stagnant Blood\n"
            "  3. 🌿 Motherwort (益母草) tea\n"
            "  ❌ Avoid: intense exercise, stress, cold\n\n"
            "Full-width bottom bar (both types): "
            "'❌ Never (either type): ice cream, cold drinks, cold compress'\n\n"
            "Small acupressure diagrams for 三陰交 and 合谷 point locations.\n"
            "Style: clear split layout. Warm red-cream palette. Clinical but warm. No face/person."
        ),
        "second_dm": (
            "Here's your period pain protocol split by type — screenshot your column 🩸\n"
            "For next month: start the prevention protocol the week before "
            "(comment 'cycle' for that one)."
        ),
    },

    # 10 ── Pre-Period Prevention ─────────────────────────────────────────────
    {
        "concept": "Week Before Your Period",
        "first_dm": (
            "Hey! The week before your period is genuinely the most important week — "
            "and most women miss it 📅\n\n"
            "Your pre-period protection plan (Days 21–28):\n\n"
            "Eat:\n"
            "• 益母草 (Motherwort) tea — moves Qi and Blood gently, prevents stagnation\n"
            "• 當歸 + 紅棗 (Dang gui + red dates) in warm soup — Blood nourishment 3x this week\n"
            "• Everything warm. No raw vegetables, no ice, no cold drinks.\n\n"
            "Avoid:\n"
            "• Ice water, sashimi, anything cold\n"
            "• Intense cardio (light walking only)\n"
            "• Late nights past midnight\n"
            "• Big arguments or emotional stress\n\n"
            "Are you usually more crampy, more PMS-emotional, or more exhausted "
            "in that pre-period week?"
        ),
        "image_brief": (
            "Vertical infographic, 4:5 ratio, warm TCM wellness aesthetic.\n"
            "Title: 'Pre-Period Protection Protocol — Days 21–28'\n"
            "Subtitle: 'The week before determines the week during.'\n"
            "Background: warm amber-cream with subtle red date (紅棗) and herb illustrations.\n\n"
            "Two-section layout:\n\n"
            "Section 1 — ✅ DO THIS (green-amber accents):\n"
            "  1. 🌿 益母草 (Motherwort) tea — daily\n"
            "  2. 🍲 當歸 + 紅棗 soup — 3x this week\n"
            "  3. 🌡️ Eat everything warm — no cold, no raw\n"
            "  4. 🚶 Light walking only — no intense cardio\n"
            "  5. 🛏️ Sleep before midnight\n\n"
            "Section 2 — ❌ AVOID (muted red accents):\n"
            "  1. 🧊 Ice water, cold drinks, ice cream\n"
            "  2. 🐟 Raw food, sashimi\n"
            "  3. 😤 Emotional stress, big arguments\n"
            "  4. 💪 Intense exercise\n"
            "  5. 🌙 Late nights past midnight\n\n"
            "Bottom quote: 'The pain you prevent this week is the pain you won't feel next week.'\n"
            "Style: warm amber and cream. Clean two-column do/avoid layout. "
            "Organic herb illustrations (red dates, dang gui). No face/person."
        ),
        "second_dm": (
            "Here's your pre-period protection plan — screenshot the DO/AVOID columns 📅\n"
            "Start the motherwort tea on Day 21. That's all you need to do differently this week."
        ),
    },
]


# ─── Main ─────────────────────────────────────────────────────────────────────

def main() -> None:
    parser = argparse.ArgumentParser(description="Add Protocol sections to Content Library concepts")
    parser.add_argument("--dry-run", action="store_true", help="Preview only — no writes")
    args = parser.parse_args()

    ids = json.loads(IDS_PATH.read_text(encoding="utf-8"))
    content_db_id = ids["content_db"]

    done, skipped, missing = [], [], []

    for p in PROTOCOLS:
        fragment = p["concept"]
        page_id = find_concept_by_name(content_db_id, fragment)
        if not page_id:
            print(f"  ❌ NOT FOUND: '{fragment}'")
            missing.append(fragment)
            continue

        print(f"  📩 {fragment} ...", end="", flush=True)
        result = append_protocol(page_id, p, dry_run=args.dry_run)
        print(f" → {result}")
        if "skipped" in result:
            skipped.append(fragment)
        else:
            done.append(fragment)
        time.sleep(0.4)

    print(f"\n{'[DRY RUN] ' if args.dry_run else ''}Done — "
          f"appended {len(done)}, skipped {len(skipped)}, missing {len(missing)}")
    if missing:
        print(f"\n⚠️  Missing (check concept names): {missing}")


if __name__ == "__main__":
    main()
