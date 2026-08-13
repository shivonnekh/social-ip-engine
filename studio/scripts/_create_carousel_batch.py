#!/usr/bin/env python3
"""One-off batch creator for the 10 carousel concepts approved 2026-08-13.
Not part of the reusable pipeline (matches the ad-hoc convention of
gen_carousel_pressure_points.py / the manual concept-1 creation earlier this
session) — creates each Content Library page + its 🎠 Carousel Guide body
section directly via the Notion API, following the exact same schema
notion_carousel_prompts.parse_carousel_guide() reads.

Usage: python3 scripts/_create_carousel_batch.py
"""
from __future__ import annotations

import json
import os
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import requests
from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parent.parent / ".env")

KEY = os.environ["NOTION_KEY"]
HEADERS = {"Authorization": f"Bearer {KEY}", "Notion-Version": "2022-06-28", "Content-Type": "application/json"}
IDS = json.load(open(Path(__file__).resolve().parent / "notion_ids.json"))
CONTENT_DB = IDS["content_db"]


def rt(t: str) -> list[dict]:
    return [{"type": "text", "text": {"content": t}}]


def bullet(t: str) -> dict:
    return {"object": "block", "type": "bulleted_list_item", "bulleted_list_item": {"rich_text": rt(t)}}


def h3(t: str) -> dict:
    return {"object": "block", "type": "heading_3", "heading_3": {"rich_text": rt(t)}}


# Each concept: (name, topic, hook, cta, fan_out_to, [(panel_title, visual, copy), ...])
CONCEPTS: list[tuple[str, str, str, str, str, list[tuple[str, str, str]]]] = [
    (
        "5 TCM Body Types — Which One Are You?",
        "🌡️ Body Constitution",
        "You're not 'just tired' — your body type has a name.",
        "Comment TYPE and I'll help you figure out which one you are",
        "Jackie Chan",
        [
            ("Panel 1 · Cover",
             "Center illustration: five small warm-toned line-art silhouette icons in a row, each subtly "
             "different posture (slumped/tired, hunched/cold, flushed/restless, heavy/damp, tense/tight), "
             "with a large question mark floating above the row. Subtitle band: 'Take 30 seconds to find out'.",
             "5 TCM Body Types\nWhich One Are You?"),
            ("Panel 2 · Qi Deficiency",
             "Header bar deep blue, white icon badge (simple line-art figure slumped in a chair). "
             "Illustration: the same tired-slumped silhouette, faint outline, low energy visual (drooping "
             "shoulders, half-closed eyes). Three instruction rows: tired icon + 'Tired even after sleeping "
             "8 hours'; wind icon + 'Catch colds easily, low voice'; leaf icon + 'Fix: warm cooked food, "
             "jujube + astragalus tea'.",
             "QI DEFICIENCY · 气虚"),
            ("Panel 3 · Yang Deficiency",
             "Header bar dark teal, white icon badge (simple line-art snowflake). Illustration: the same "
             "silhouette wrapped in a blanket, hands tucked in, faint cold-blue tint on hands/feet. Three "
             "instruction rows: snowflake icon + 'Always cold hands and feet'; moon icon + 'Prefers warm "
             "drinks, dislikes AC'; flame icon + 'Fix: ginger tea, warm foot soaks before bed'.",
             "YANG DEFICIENCY · 阳虚"),
            ("Panel 4 · Yin Deficiency",
             "Header bar warm amber, white icon badge (simple line-art sun with a small droplet). "
             "Illustration: the same silhouette with a faint flushed-cheek tint and a small heat-shimmer "
             "line rising from the head. Three instruction rows: flame icon + 'Warm palms, flushed cheeks "
             "in the afternoon'; moon-with-eyes icon + 'Restless sleep, night sweats'; droplet icon + 'Fix: "
             "pear + white fungus soup, goji berries'.",
             "YIN DEFICIENCY · 阴虚"),
            ("Panel 5 · Damp-Heat",
             "Header bar olive green, white icon badge (simple line-art droplet with a small flame inside). "
             "Illustration: the same silhouette with a faint heavy/bloated outline and small sweat-drop "
             "marks. Three instruction rows: droplet icon + 'Oily skin, breakouts, heavy limbs'; cloud icon "
             "+ 'Sticky, sluggish feeling after meals'; leaf icon + 'Fix: mung bean soup, barley water, cut "
             "fried food'.",
             "DAMP-HEAT · 濕熱"),
            ("Panel 6 · Qi Stagnation",
             "Header bar dusty purple, white icon badge (simple line-art knot/tangled line). Illustration: "
             "the same silhouette with arms crossed tightly, a small tangled-line motif over the chest. "
             "Three instruction rows: knot icon + 'Sighs a lot, chest feels tight'; storm-cloud icon + "
             "'Mood swings, irritable for no clear reason'; leaf icon + 'Fix: rose tea, 10 minutes of "
             "brisk walking daily'.",
             "QI STAGNATION · 氣鬱"),
            ("Panel 7 · Closing",
             "Summary row: five small colored dots in a horizontal line matching each type's header color "
             "(blue, teal, amber, olive, purple), each with a 2-word label beneath it (Qi Def · Yang Def · "
             "Yin Def · Damp-Heat · Qi Stag). Below that, a bold call-to-action line inside a soft rounded "
             "box. Bottom disclaimer bar: small hollow circular icon of a person in traditional dress next "
             "to the text 'Most people are a mix of two — that's normal.'",
             "Which One Sounds Like You?"),
        ],
    ),
    (
        "3 Sleep Points to Press Before Bed",
        "🧠 Sleep",
        "No melatonin, no white noise app — just three points.",
        "Comment SLEEP and I'll send you the full bedtime routine",
        "Jackie Chan",
        [
            ("Panel 1 · Cover",
             "Center illustration: a simple warm-toned line-art crescent moon with a small sleeping face, "
             "and three small numbered circle markers (1, 2, 3) placed near a small ear icon, a small foot "
             "icon, and a small forehead icon — hinting at the three points to come, without labeling them "
             "yet. Subtitle band: 'Press before bed — takes under 3 minutes'.",
             "3 Sleep Points\nBefore Bed"),
            ("Panel 2 · Anmian",
             "Header bar deep indigo, white icon badge (simple line-art ear). Illustration: clean line-art "
             "of the side of a head/ear, small indigo circle marking the point just behind the earlobe, "
             "thin arrow/label reading 'press here'. Three instruction rows: pressing-finger icon + 'Press "
             "gently in small circles, 1 minute each side'; moon icon + 'Best time: lying in bed, lights "
             "off'; sparkle icon + 'Name means literally \"peaceful sleep\"'.",
             "ANMIAN · 安眠"),
            ("Panel 3 · Yongquan",
             "Header bar deep navy, white icon badge (simple line-art foot sole). Illustration: clean "
             "line-art of the sole of a foot, small navy circle marking the point in the center just below "
             "the ball of the foot, thin arrow/label reading 'press here'. Three instruction rows: "
             "pressing-finger icon + 'Press firmly, 1-2 minutes each foot'; root icon + 'Grounds racing "
             "thoughts, pulls energy downward'; warning icon + 'Best done sitting, not standing'.",
             "YONGQUAN · 湧泉"),
            ("Panel 4 · Yintang",
             "Header bar dusty lavender, white icon badge (simple line-art single star). Illustration: "
             "clean line-art of a face from the front, eyes closed, small lavender circle marking the point "
             "directly between the eyebrows, thin arrow/label reading 'press here'. Three instruction rows: "
             "pressing-finger icon + 'Light circular pressure, 1 minute'; cloud icon + 'Best for: racing "
             "mind, can't switch off'; moon icon + 'Pair with: slow breathing, eyes closed'.",
             "YINTANG · 印堂"),
            ("Panel 5 · Closing",
             "Summary row: three small line-art icons side by side (ear, foot, single star), each with a "
             "small colored dot above it matching its point's color. Below that, a bold call-to-action line "
             "inside a soft rounded box. Bottom disclaimer bar: small hollow circular icon of a person in "
             "traditional dress next to the text 'Ongoing insomnia? See a practitioner.'",
             "Do All Three Tonight"),
        ],
    ),
    (
        "Your Tongue Is Talking — 5 Signs to Check Today",
        "⚕️ General TCM",
        "Stick your tongue out. It's telling you something.",
        "Comment TONGUE and I'll send you the full self-check guide",
        "Jackie Chan",
        [
            ("Panel 1 · Cover",
             "Center illustration: a simple warm-toned line-art mouth with tongue slightly out, a small "
             "magnifying glass hovering over it. Subtitle band: 'Check these 5 things in the mirror today'.",
             "Your Tongue Is Talking\n5 Signs to Check"),
            ("Panel 2 · Pale Tongue",
             "Header bar soft pink, white icon badge (simple line-art droplet). Illustration: clean "
             "line-art of a tongue shape, rendered notably lighter/paler than the surrounding lip line, "
             "small label arrow reading 'lighter than usual'. Three instruction rows: droplet icon + "
             "'Means: blood deficiency'; person icon + 'Often paired with: fatigue, pale nails'; leaf icon "
             "+ 'Fix: red dates, dark leafy greens, beef in small amounts'.",
             "PALE TONGUE"),
            ("Panel 3 · Red Tip",
             "Header bar deep red, white icon badge (simple line-art flame). Illustration: clean line-art "
             "of a tongue shape with the very tip rendered in a deeper red than the rest, small label arrow "
             "reading 'the tip specifically'. Three instruction rows: flame icon + 'Means: heart heat, "
             "usually from stress'; moon icon + 'Often paired with: trouble falling asleep'; leaf icon + "
             "'Fix: lotus seed tea, wind down 30 min before bed'.",
             "RED TIP"),
            ("Panel 4 · Yellow Coating",
             "Header bar olive yellow, white icon badge (simple line-art layered lines). Illustration: "
             "clean line-art of a tongue shape with a textured yellow-tinted coating over the surface, "
             "small label arrow reading 'the coating, not the tongue itself'. Three instruction rows: "
             "droplet icon + 'Means: damp-heat, often digestive'; stomach icon + 'Often paired with: "
             "bloating, bad breath'; leaf icon + 'Fix: barley water, cut fried and greasy food'.",
             "YELLOW COATING"),
            ("Panel 5 · Purple or Dusky",
             "Header bar muted plum, white icon badge (simple line-art small knot). Illustration: clean "
             "line-art of a tongue shape with a faint dusky-purple tint, small label arrow reading 'a "
             "dusky, slightly purple tone'. Three instruction rows: knot icon + 'Means: blood stasis, poor "
             "circulation'; snowflake icon + 'Often paired with: cold hands, period pain'; leaf icon + "
             "'Fix: light daily movement, warming foods'.",
             "PURPLE / DUSKY"),
            ("Panel 6 · Teeth Marks",
             "Header bar sage green, white icon badge (simple line-art scalloped edge). Illustration: "
             "clean line-art of a tongue shape with a visibly scalloped, wavy edge, small label arrow "
             "reading 'the edges, look for small dents'. Three instruction rows: wave icon + 'Means: qi "
             "deficiency or excess dampness'; cloud icon + 'Often paired with: heavy limbs, low energy'; "
             "leaf icon + 'Fix: cooked warm food over raw/cold food'.",
             "TEETH-MARKED EDGES"),
            ("Panel 7 · Closing",
             "Summary row: five small tongue-shape icons in a horizontal line, each with a small colored "
             "dot above matching its panel's color, tiny 2-word labels beneath. Below that, a bold "
             "call-to-action line inside a soft rounded box. Bottom disclaimer bar: small hollow circular "
             "icon of a person in traditional dress next to the text 'One sign isn't a diagnosis — a "
             "pattern over time matters more.'",
             "Which Sign Did You See?"),
        ],
    ),
    (
        "5-Minute Desk Gua Sha — Jawline + Neck",
        "🦷 Skin / Beauty",
        "You don't need a spa. You need 5 minutes and a gua sha tool.",
        "Comment GUASHA and I'll send you the full step-by-step routine",
        "Chloe Chan",
        [
            ("Panel 1 · Cover",
             "Center illustration: a simple warm-toned line-art gua sha stone tool beside a side-profile "
             "silhouette of a jaw and neck, with small directional arrows sketched faintly along the jaw "
             "and neck hinting at the routine to come. Subtitle band: 'At your desk. No mirror needed.'",
             "5-Minute Desk Gua Sha\nJawline + Neck"),
            ("Panel 2 · Step 1 — Jaw Sweep",
             "Header bar soft rose, white icon badge with step number '1'. Illustration: clean line-art "
             "side-profile of a jaw, a gua sha stone icon with a curved arrow sweeping from the chin "
             "outward along the jawline toward the ear. Three instruction rows: arrow icon + 'Sweep chin "
             "to ear, light pressure'; repeat icon + '8-10 strokes each side'; angle icon + 'Hold the tool "
             "at a 15-degree angle'.",
             "STEP 1 · Jaw Sweep"),
            ("Panel 3 · Step 2 — Cheek Lift",
             "Header bar soft coral, white icon badge with step number '2'. Illustration: clean line-art "
             "side-profile of a cheek, a gua sha stone icon with a curved arrow lifting from the corner of "
             "the mouth upward toward the top of the ear. Three instruction rows: arrow icon + 'Lift mouth "
             "corner to ear top'; repeat icon + '8-10 strokes each side'; upward icon + 'Motion goes UP, "
             "never down'.",
             "STEP 2 · Cheek Lift"),
            ("Panel 4 · Step 3 — Neck Drain",
             "Header bar soft teal, white icon badge with step number '3'. Illustration: clean line-art "
             "side-profile of a neck, a gua sha stone icon with a curved arrow sweeping downward from "
             "behind the ear toward the collarbone. Three instruction rows: arrow icon + 'Sweep ear to "
             "collarbone, DOWNWARD'; repeat icon + '8-10 strokes each side'; lymph icon + 'This follows "
             "lymph drainage direction'.",
             "STEP 3 · Neck Drain"),
            ("Panel 5 · Step 4 — Collarbone Finish",
             "Header bar soft gold, white icon badge with step number '4'. Illustration: clean line-art of "
             "a collarbone area from the front, a gua sha stone icon with a short arrow sweeping outward "
             "along the collarbone toward the shoulder. Three instruction rows: arrow icon + 'Sweep center "
             "to shoulder, both sides'; repeat icon + '5-6 strokes each side'; check icon + 'Finishes the "
             "drainage path you just opened'.",
             "STEP 4 · Collarbone Finish"),
            ("Panel 6 · Closing",
             "Summary row: four small numbered circle icons in a horizontal line (1-2-3-4) each with a "
             "tiny arrow matching its step's direction. Below that, a bold call-to-action line inside a "
             "soft rounded box. Bottom disclaimer bar: small hollow circular icon of a person in "
             "traditional dress next to the text 'Always sweep away from the face, never press on active "
             "breakouts.'",
             "Do It Daily — 5 Minutes"),
        ],
    ),
    (
        "3 Foods That Dry You Out (and 3 That Fix It)",
        "🩺 Blood / Circulation",
        "That afternoon dry-mouth, tight-skin feeling? It's not just weather.",
        "Comment DRY and I'll send you the full food list",
        "Jackie Chan",
        [
            ("Panel 1 · Cover",
             "Center illustration: a simple warm-toned line-art scale, one side slightly lower showing "
             "small icons of chili, coffee, and fried food; the other side showing small icons of pear, "
             "white fungus, and honey — visually setting up a before/after without labeling yet. Subtitle "
             "band: 'Swap 3 things, feel the difference in days'.",
             "3 Foods That Dry You Out\n(And 3 That Fix It)"),
            ("Panel 2 · Avoid",
             "Header bar deep red, white icon badge (simple line-art flame). Three items in a row, each "
             "with a clean line-art icon and small caption: chili pepper icon + 'Spicy food, in excess'; "
             "coffee cup icon + 'Too much coffee, no water after'; fried-food icon + 'Deep-fried, greasy "
             "food'. Footer line: 'These burn through your body's fluids'.",
             "MINIMIZE THESE"),
            ("Panel 3 · Eat Instead",
             "Header bar soft teal, white icon badge (simple line-art droplet). Three items in a row, each "
             "with a clean line-art icon and small caption: pear icon + 'Pear, raw or lightly stewed'; "
             "fungus icon + 'White fungus (snow fungus) soup'; honey-jar icon + 'Honey in warm (not hot) "
             "water'. Footer line: 'These replenish yin fluids'.",
             "EAT THESE INSTEAD"),
            ("Panel 4 · Closing",
             "Summary row: a simple line-art glass of water with a small droplet icon beside it. Below "
             "that, a bold call-to-action line inside a soft rounded box. Bottom disclaimer bar: small "
             "hollow circular icon of a person in traditional dress next to the text 'Chronic dryness that "
             "doesn't improve? See a practitioner.'",
             "Small Swaps, Real Difference"),
        ],
    ),
    (
        "Cold Hands, Cold Feet? 4 Habits That Actually Work",
        "🩺 Blood / Circulation",
        "It's not just 'bad circulation' — it's a fixable pattern.",
        "Comment WARM and I'll send you the full daily routine",
        "Jackie Chan",
        [
            ("Panel 1 · Cover",
             "Center illustration: a simple warm-toned line-art pair of hands, one rendered with a faint "
             "cool-blue tint and small snowflake marks, the other rendered warm with small radiating heat "
             "lines — a visual before/after without labeling yet. Subtitle band: 'Always cold, even in "
             "summer? Start here.'",
             "Cold Hands, Cold Feet?\n4 Habits That Work"),
            ("Panel 2 · Habit 1",
             "Header bar deep teal, white icon badge with number '1' (simple line-art foot in a basin). "
             "Illustration: clean line-art of feet soaking in a basin of steaming water. Three instruction "
             "rows: clock icon + '10-15 minutes before bed'; thermometer icon + 'Water just above warm, "
             "not scalding'; leaf icon + 'Add a slice of ginger for extra warmth'.",
             "1 · Warm Foot Soak"),
            ("Panel 3 · Habit 2",
             "Header bar warm amber, white icon badge with number '2' (simple line-art teacup with steam). "
             "Illustration: clean line-art of a steaming teacup with a few slices of ginger visible inside. "
             "Three instruction rows: clock icon + 'Morning, on an empty-ish stomach'; leaf icon + '2-3 "
             "thin ginger slices, steeped 5 min'; sun icon + 'Skip if you already run hot/flushed'.",
             "2 · Ginger Tea"),
            ("Panel 4 · Habit 3",
             "Header bar dusty rose, white icon badge with number '3' (simple line-art walking figure). "
             "Illustration: clean line-art of a figure mid-stride, small motion lines behind. Three "
             "instruction rows: clock icon + 'Every hour, even just 2 minutes'; circulation icon + 'Moves "
             "qi and blood to the extremities'; desk icon + 'Set a reminder if you sit all day'.",
             "3 · Move Every Hour"),
            ("Panel 5 · Habit 4",
             "Header bar soft plum, white icon badge with number '4' (simple line-art wrist with a small "
             "cuff/sleeve). Illustration: clean line-art of a wrist and ankle, each with a small warm "
             "sleeve/sock icon layered over the pulse-point area. Three instruction rows: layer icon + "
             "'Keep wrists and ankles covered'; wind icon + 'These are where cold enters easiest'; sock "
             "icon + 'Wear socks to bed if feet are the main issue'.",
             "4 · Cover the Pulse Points"),
            ("Panel 6 · Closing",
             "Summary row: four small numbered circle icons (1-2-3-4) matching each habit's color. Below "
             "that, a bold call-to-action line inside a soft rounded box. Bottom disclaimer bar: small "
             "hollow circular icon of a person in traditional dress next to the text 'Sudden or one-sided "
             "coldness/numbness — see a doctor, not just TCM.'",
             "Start With Just One"),
        ],
    ),
    (
        "The 5 Emotions & Their Organ — 情緒對照表",
        "😤 Stress",
        "TCM mapped your feelings to your organs 2000 years ago.",
        "留言 EMOTION 我send 你成套嘅情緒調理表",
        "Chloe Chan",
        [
            ("Panel 1 · Cover",
             "Center illustration: a simple warm-toned line-art human silhouette with five small glowing "
             "dots placed at the rough locations of the liver, heart, spleen, lungs, and kidneys, each dot "
             "a different soft color, connected by faint thin lines to five small emotion-face icons "
             "floating around the silhouette. Subtitle band: 'Which one hits you the most?'",
             "5 情緒與五臟\n情緒對照表"),
            ("Panel 2 · Anger — Liver",
             "Header bar deep green, white icon badge (simple line-art liver shape). Illustration: clean "
             "line-art side silhouette with the liver area highlighted in a soft green glow, a small "
             "furrowed-brow face icon beside it. Three instruction rows: flame icon + '易怒 · 唔忍得'; "
             "tight-chest icon + '胸口谷住 · 頭側邊痛'; leaf icon + '調理：玫瑰花茶，早瞓早起'.",
             "怒傷肝 · ANGER"),
            ("Panel 3 · Joy (Excess) — Heart",
             "Header bar warm red, white icon badge (simple line-art heart shape). Illustration: clean "
             "line-art side silhouette with the heart area highlighted in a soft red glow, a small "
             "wide-eyed overstimulated face icon beside it. Three instruction rows: pulse icon + '心跳快 · "
             "坐唔定'; moon icon + '瞓得差 · 發夢多'; leaf icon + '調理：蓮子茶，瞓前放慢節奏'.",
             "喜傷心 · OVER-EXCITEMENT"),
            ("Panel 4 · Worry — Spleen",
             "Header bar warm gold, white icon badge (simple line-art stomach/spleen shape). Illustration: "
             "clean line-art side silhouette with the spleen area highlighted in a soft gold glow, a small "
             "furrowed-thinking face icon beside it. Three instruction rows: knot icon + '諗多咗 · 食唔落'; "
             "cloud icon + '成日攰 · 肚脹'; leaf icon + '調理：淮山粥，食嘢慢啲'.",
             "思傷脾 · WORRY / OVERTHINKING"),
            ("Panel 5 · Grief — Lung",
             "Header bar soft grey-blue, white icon badge (simple line-art lung shape). Illustration: "
             "clean line-art side silhouette with the lung area highlighted in a soft grey-blue glow, a "
             "small downcast face icon beside it. Three instruction rows: cloud icon + '唔想講嘢 · 想喊'; "
             "wind icon + '呼吸淺 · 成日嘆氣'; leaf icon + '調理：雪梨燉川貝，深呼吸練習'.",
             "悲傷肺 · GRIEF / SADNESS"),
            ("Panel 6 · Fear — Kidney",
             "Header bar deep navy, white icon badge (simple line-art kidney shape). Illustration: clean "
             "line-art side silhouette with the kidney area highlighted in a soft navy glow, a small wide "
             "startled-eyes face icon beside it. Three instruction rows: snowflake icon + '腳軟 · 腰痠'; "
             "moon icon + '驚醒 · 瞓得淺'; leaf icon + '調理：黑芝麻，早啲瞓覺'.",
             "恐傷腎 · FEAR / ANXIETY"),
            ("Panel 7 · Closing",
             "Summary row: five small organ-shape icons in a horizontal line, each with a small colored "
             "dot above matching its panel's color, tiny 2-word Cantonese labels beneath. Below that, a "
             "bold call-to-action line inside a soft rounded box. Bottom disclaimer bar: small hollow "
             "circular icon of a person in traditional dress next to the text '情緒持續好耐？搵專業幫手。'",
             "邊一個最似你？"),
        ],
    ),
    (
        "Period Week Survival Kit — Before, During, After",
        "🌸 Women's Health",
        "Your body needs different things each phase — not the same routine every day.",
        "留言 PERIOD 我send 你成套周期調理表",
        "Chloe Chan",
        [
            ("Panel 1 · Cover",
             "Center illustration: a simple warm-toned line-art crescent-moon phase diagram (3 small "
             "circles showing waxing, full, waning), each paired faintly with a small icon (leaf, flame, "
             "droplet) hinting at the three phases to come. Subtitle band: '一個禮拜，三個階段，三種調理法'.",
             "經期生存指南\n經前・經期・經後"),
            ("Panel 2 · Before — Prep Phase",
             "Header bar dusty rose, white icon badge (simple line-art leaf). Illustration: clean line-art "
             "of a warm mug and a small calendar icon with a few days circled. Three instruction rows: leaf "
             "icon + '玫瑰花茶，疏肝理氣'; warning icon + '少凍飲，少生冷嘢'; moon icon + '早啲瞓，唔好捱夜'.",
             "經前 · PREP"),
            ("Panel 3 · During — Flow Phase",
             "Header bar deep red, white icon badge (simple line-art droplet). Illustration: clean line-art "
             "of a hot water bottle resting on a lower-abdomen silhouette outline. Three instruction rows: "
             "flame icon + '暖水袋敷小腹，15分鐘'; leaf icon + '紅糖薑茶，暖宮'; rest icon + '減少劇烈運動，多休息'.",
             "經期 · FLOW"),
            ("Panel 4 · After — Rebuild Phase",
             "Header bar warm gold, white icon badge (simple line-art bowl). Illustration: clean line-art "
             "of a bowl of soup with visible ingredients (dates, goji berries). Three instruction rows: "
             "bowl icon + '紅棗桂圓湯，補血'; leaf icon + '黑芝麻，補腎氣'; sun icon + '呢個階段可以慢慢加返運動量'.",
             "經後 · REBUILD"),
            ("Panel 5 · Closing",
             "Summary row: three small phase icons (leaf, droplet, bowl) in a horizontal line, each with a "
             "small colored dot above. Below that, a bold call-to-action line inside a soft rounded box. "
             "Bottom disclaimer bar: small hollow circular icon of a person in traditional dress next to "
             "the text '經痛好嚴重或者週期好唔規律？搵醫生檢查吓。'",
             "一個禮拜，三個階段"),
        ],
    ),
    (
        "3 Snacks for 3 Body Types",
        "💪 Fitness",
        "Snacking isn't the enemy — the wrong snack for your body type is.",
        "Comment SNACK and I'll send you the full body-type food guide",
        "Jackie Chan",
        [
            ("Panel 1 · Cover",
             "Center illustration: a simple warm-toned line-art plate with three small distinct snack "
             "icons on it (a small jar, a bowl of nuts, a cup of soup), each with a faint number marker "
             "(1, 2, 3) — hinting at the three types to come. Subtitle band: 'Match your snack to your "
             "body, not just your cravings'.",
             "3 Snacks\nFor 3 Body Types"),
            ("Panel 2 · Qi Deficiency Snack",
             "Header bar deep blue, white icon badge (simple line-art figure slumped in a chair — same "
             "motif as the body-type carousel for visual consistency across the library). Illustration: "
             "clean line-art of a small jar of red dates and longan. Three instruction rows: leaf icon + "
             "'Jujube + longan (dried), a small handful'; energy icon + 'Best for: low energy, easily "
             "tired'; clock icon + 'Great mid-afternoon, not late at night'.",
             "QI DEFICIENCY · Jujube + Longan"),
            ("Panel 3 · Yang Deficiency Snack",
             "Header bar dark teal, white icon badge (simple line-art snowflake — matches the body-type "
             "carousel). Illustration: clean line-art of a small bowl of walnuts and black sesame. Three "
             "instruction rows: nut icon + 'Walnuts + black sesame, a small handful'; snowflake icon + "
             "'Best for: always cold, low back ache'; sun icon + 'Warms from the inside'.",
             "YANG DEFICIENCY · Walnut + Black Sesame"),
            ("Panel 4 · Damp-Heat Snack",
             "Header bar olive green, white icon badge (simple line-art droplet with a small flame inside "
             "— matches the body-type carousel). Illustration: clean line-art of a bowl of mung bean soup. "
             "Three instruction rows: droplet icon + 'Mung bean soup, lightly sweetened'; leaf icon + "
             "'Best for: oily skin, heavy/sluggish feeling'; sun icon + 'Cooling — best in warm weather'.",
             "DAMP-HEAT · Mung Bean Soup"),
            ("Panel 5 · Closing",
             "Summary row: three small snack icons (jar, bowl of nuts, bowl of soup) in a horizontal line, "
             "each with a colored dot above matching its body-type carousel color. Below that, a bold "
             "call-to-action line inside a soft rounded box. Bottom disclaimer bar: small hollow circular "
             "icon of a person in traditional dress next to the text 'Not sure which type you are? Check "
             "our 5 Body Types carousel first.'",
             "Snack Smarter, Not Less"),
        ],
    ),
    (
        "5 Signs Your Liver Qi Is Stuck",
        "🫀 Liver",
        "Snapping at small things? Your liver might be trying to tell you something.",
        "Comment LIVER and I'll send you the full daily reset routine",
        "Jackie Chan",
        [
            ("Panel 1 · Cover",
             "Center illustration: a simple warm-toned line-art human silhouette with a small tangled-line "
             "knot motif over the liver/rib area, faint radiating tension lines. Subtitle band: 'Check off "
             "how many of these are true for you'.",
             "5 Signs Your Liver Qi\nIs Stuck"),
            ("Panel 2 · Sign 1",
             "Header bar deep green, white icon badge with number '1' (simple line-art storm cloud). "
             "Illustration: clean line-art face with a sharp furrowed brow and a small storm-cloud icon "
             "above the head. Three instruction rows: flame icon + 'Snapping at small things'; clock icon "
             "+ 'Especially in the morning or before meals'; leaf icon + 'Fix: rose or chrysanthemum tea'.",
             "1 · Short Temper"),
            ("Panel 3 · Sign 2",
             "Header bar deep green, white icon badge with number '2' (simple line-art wave/mood-swing "
             "line). Illustration: clean line-art of a simple up-down wavy line representing mood, with a "
             "small calendar icon beside it. Three instruction rows: wave icon + 'Mood swings, worse before "
             "your period'; calendar icon + 'Predictable timing each month'; leaf icon + 'Fix: consistent "
             "sleep schedule, less caffeine that week'.",
             "2 · PMS Mood Swings"),
            ("Panel 4 · Sign 3",
             "Header bar deep green, white icon badge with number '3' (simple line-art tight chest/lungs). "
             "Illustration: clean line-art of an upper torso with a small tight-knot motif over the chest, "
             "small breath-lines. Three instruction rows: knot icon + 'Tight chest, sighing a lot'; wind "
             "icon + 'Feels better after a big exhale'; leaf icon + 'Fix: 5 slow deep breaths, several "
             "times a day'.",
             "3 · Tight Chest, Sighing"),
            ("Panel 5 · Sign 4",
             "Header bar deep green, white icon badge with number '4' (simple line-art side-of-head "
             "temple mark). Illustration: clean line-art of a face from the side, small circle marking the "
             "temple area with a subtle throb-line. Three instruction rows: pulse icon + 'Tension headaches "
             "at the temples'; clock icon + 'Often after a stressful day'; leaf icon + 'Fix: temple "
             "massage, less screen time before bed'.",
             "4 · Temple Headaches"),
            ("Panel 6 · Sign 5",
             "Header bar deep green, white icon badge with number '5' (simple line-art stomach with a "
             "small tangle). Illustration: clean line-art of a torso with a small bloated-belly outline and "
             "a tangled-line motif over the stomach area. Three instruction rows: stomach icon + 'Bloating "
             "that shows up after stress'; clock icon + 'Worse on tense/busy days, not food-related'; leaf "
             "icon + 'Fix: peppermint tea, slow down while eating'.",
             "5 · Stress Bloating"),
            ("Panel 7 · Closing",
             "Summary row: five small numbered circle icons (1-5) in a horizontal line, all in the same "
             "deep green matching this carousel's header color. Below that, a bold call-to-action line "
             "inside a soft rounded box. Bottom disclaimer bar: small hollow circular icon of a person in "
             "traditional dress next to the text 'Check off 3 or more? Worth a closer look.'",
             "How Many Checked Off?"),
        ],
    ),
]


def main() -> int:
    created = []
    for name, topic, hook, cta, fan_to, panels in CONCEPTS:
        payload = {
            "parent": {"database_id": CONTENT_DB},
            "properties": {
                "Name": {"title": rt(name)},
                "Topic": {"select": {"name": topic}},
                "Hook": {"rich_text": rt(hook)},
                "CTA": {"rich_text": rt(cta)},
                "Concept Status": {"select": {"name": "✍️ Scripted"}},
                "Fan out to": {"multi_select": [{"name": fan_to}]},
            },
        }
        r = requests.post("https://api.notion.com/v1/pages", headers=HEADERS, json=payload)
        if r.status_code != 200:
            print(f"[error] create page failed for {name!r}: {r.status_code} {r.text[:300]}")
            continue
        concept_id = r.json()["id"]

        blocks = [
            {"object": "block", "type": "divider", "divider": {}},
            {"object": "block", "type": "heading_2", "heading_2": {"rich_text": rt("🎠 Carousel Guide")}},
        ]
        for title, visual, copy in panels:
            blocks.append(h3(title))
            blocks.append(bullet(f"🖼️ {visual}"))
            blocks.append(bullet(f"✏️ {copy}"))

        r2 = requests.patch(f"https://api.notion.com/v1/blocks/{concept_id}/children",
                             headers=HEADERS, json={"children": blocks})
        if r2.status_code != 200:
            print(f"[error] write Carousel Guide failed for {name!r}: {r2.status_code} {r2.text[:300]}")
            continue

        print(f"✅ {name} ({len(panels)} panels) -> {concept_id}")
        created.append((name, concept_id, fan_to))
        time.sleep(0.4)

    print(f"\n{len(created)}/{len(CONCEPTS)} concepts created.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
