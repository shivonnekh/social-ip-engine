"""Concept data for the 2026-09 Jackie Chan batch (10 campaigns).

Separated from the creator script so the CONTENT (judgement work) is reviewable
on its own, apart from the Notion plumbing.

Gap analysis behind the picks
-----------------------------
75 concepts already sat in the Content Library and 23 Jackie rows were already
produced. Every topic below was genuinely unclaimed, and every CTA keyword was
verified free against the live matcher (`src.channels.comment_rules.match`) on
Jackie's account before being written down — not just eyeballed against the
rules file, because fuzzy matching can claim a keyword that looks free.

Deliberately NOT included: hair-adjacent "scalp gua sha", "dry eyes", "phone
neck", "bad breath", "tonsil stones" and the whole gua-sha family — all already
published, and a near-duplicate cannibalises the original post's search surface.

Camera design
-------------
Shot guides are BUILT (see `shot_guides()` in create_batch_concepts_2026_09.py) rather
than hand-written, from three rotations of (scale, camera side, height). Three
rotations exist so ten videos in a row don't open on the identical frame; each
rotation still gives four distinct scales/sides/heights within one video.

Two hard constraints are baked into every rotation:
  * Every angle stays <=15 degrees off-axis. Camera SIDE varies, the face never
    does — `studio/CLAUDE.md` documents that Jimeng's multimodal2video lip-sync
    fails silently on profile faces.
  * Single continuous talking head, at most ONE in-frame prop, zero cutaway
    inserts. The 2026-08-24 finding was that a shot guide enumerating one b-roll
    insert per spoken item flips Jimeng into "labelled explainer" mode and it
    burns its own subtitles regardless of the no-subtitle instruction. A spoken
    line may still enumerate (see `acne` shot 2) — it's the VISUAL that must not.

Wardrobe varies BETWEEN concepts (so the IG grid isn't ten identical thumbnails)
but is pinned IDENTICAL across the four shots + cover WITHIN a concept, which is
the consistency that actually matters.
"""
from __future__ import annotations

# Pinned per-concept so all four shots + the cover match each other.
WARDROBE = {
    "navy": "navy-grey mandarin-collar linen shirt",
    "oatmeal": "warm oatmeal-beige mandarin-collar linen jacket",
    "charcoal": "deep charcoal mandarin-collar linen tunic with fine grey piping",
}

# One row per concept. `rotation` picks the camera rotation (0/1/2).
#
# Props are split in two on purpose:
#   `actions[i]` names the item Jackie HOLDS in shot i.
#   `prop_rest`  names what stays on the DESK, in every shot.
# They must never name the same object, or gpt-image-2 renders it twice (an
# early draft had Jackie holding the comb while a second comb lay on the desk).
# Both are locked across shots by [SAME_PROP_AS: Shot 1], so both must be
# described concretely — material and colour — never as "the tool".
# `prop_hero` is kept only as the original authoring note; nothing reads it.
CONCEPTS: list[dict] = [
    {
        "key": "hair",
        "name": "💇 Thinning Hair — It's Not Your Shampoo",
        "topic": "⚕️ General TCM",
        "hook": "Thinning hair is not a shampoo problem.",
        "wardrobe": "navy",
        "rotation": 0,
        "prop_rest": 'a small dark ceramic bowl of black sesame seeds',
        "prop_hero": "a pale wooden wide-tooth comb and a small dark ceramic bowl of black sesame seeds",
        "actions": [
            "holds the pale wooden wide-tooth comb upright in his right hand",
            "rests one hand lightly on the crown of his own head to indicate the scalp",
            "taps his own scalp with spread fingertips to show the technique",
            "rests both hands together on the desk",
        ],
        "script": [
            "If your hair is thinning, the problem is not your shampoo. In Chinese "
            "medicine, hair is the surplus of your blood.",
            "When blood and kidney essence run low, the hair loses its root. That is "
            "why long stress and illness thin it so fast.",
            "Try this. Tap your whole scalp with your fingertips for one minute each "
            "morning, and eat black sesame every day.",
            "Comment hair and I will send you my full blood and kidney nourishing protocol.",
        ],
        "notes": [
            "Not a shampoo problem",
            "髮為血之餘 · 腎其華在髮",
            "Scalp tapping + black sesame",
            "Comment 👇 hair",
        ],
        "first_dm": (
            "Hey! Scalp tapping plus black sesame is the combination that actually "
            "moves the needle 💇\n\n"
            "Quick check — is yours more thinning all over, or receding at the temples "
            "and hairline? They point to different roots."
        ),
        "infographic": (
            "Title: 'Thinning Hair — Blood and Essence, Not Shampoo'.\n"
            "1) ROOT — strand-and-follicle icon; text: hair is the surplus of blood, and "
            "the kidney governs its growth. Low blood or spent essence starves the root.\n"
            "2) WHAT DRAINS IT — hourglass icon; text: long stress, illness, crash "
            "dieting, too little sleep, heavy blood loss.\n"
            "3) DAILY FIX — comb and bowl icons; text: tap the whole scalp 1 minute each "
            "morning, black sesame daily, add walnut, goji and dark leafy greens."
        ),
        "second_dm": (
            "Here's your hair guide — give the scalp tapping a full six weeks, hair "
            "grows on a slow clock 🌱\n\n"
            "Want the blood-building food list that feeds it from the inside? Reply 'blood'."
        ),
    },
    {
        "key": "snoring",
        "name": "😴 Snoring Isn't About Your Nose",
        "topic": "🫁 Lung",
        "hook": "Snoring is a damp and phlegm problem.",
        "wardrobe": "oatmeal",
        "rotation": 1,
        "prop_rest": 'a saucer of curled dried tangerine peel',
        "prop_hero": "a small pale celadon cup of warm tea and a saucer of dried tangerine peel",
        "actions": [
            "holds the small pale celadon cup of warm tea in his right hand",
            "touches the base of his own throat with two fingers to indicate the airway",
            "lifts a curl of dried tangerine peel from the saucer to show it to camera",
            "sets the cup down and rests both hands on the desk",
        ],
        "script": [
            "If you snore every single night, it is not just about your nose. Your body "
            "is holding damp and phlegm it cannot clear.",
            "A weak spleen turns food into phlegm instead of energy. That phlegm settles "
            "in the throat and narrows the airway at night.",
            "Try this. Drink warm dried tangerine peel tea after dinner, and stop cold "
            "dairy at night. It helps dry the damp.",
            "Comment snoring and I will send you my full phlegm clearing protocol.",
        ],
        "notes": [
            "Not a nose problem",
            "脾虛生濕 · 痰阻氣道",
            "陳皮 tea + no cold dairy at night",
            "Comment 👇 snoring",
        ],
        "first_dm": (
            "Hey! Warm tangerine-peel tea after dinner is the easiest first step for "
            "snoring 😴\n\n"
            "Quick check — do you also wake with a thick coating on your tongue or "
            "phlegm in your throat?"
        ),
        "infographic": (
            "Title: 'Snoring — Clear the Damp, Open the Airway'.\n"
            "1) ROOT — throat-and-airway icon; text: a weak spleen turns food into "
            "phlegm instead of energy. Phlegm settles and narrows the airway at night.\n"
            "2) WHAT FEEDS IT — bowl icon; text: cold dairy at night, sugar, fried and "
            "greasy food, late heavy dinners, alcohol.\n"
            "3) TONIGHT'S FIX — cup and peel icons; text: warm dried tangerine peel tea "
            "after dinner, nothing cold after 8pm, sleep on your side."
        ),
        "second_dm": (
            "Here's your snoring guide — the tongue coating is the fastest way to track "
            "if the damp is clearing 🌙\n\n"
            "Want the damp-clearing food list? Reply 'damp'."
        ),
    },
    {
        "key": "bowel",
        "name": "🚽 Can't Go Every Morning? It's Dryness, Not Laziness",
        "topic": "🍵 Stomach",
        "hook": "Your intestines are dry, not lazy.",
        "wardrobe": "charcoal",
        "rotation": 2,
        "prop_rest": 'a small wooden honey spoon resting on a light ceramic dish',
        "prop_hero": "a tall clear glass of warm water and a small wooden honey spoon",
        "actions": [
            "holds the tall clear glass of warm water in his right hand",
            "rests a flat palm on his own lower abdomen while facing camera",
            "circles a flat palm slowly on his own belly to show the direction",
            "rests both hands together beside the glass on the desk",
        ],
        "script": [
            "If you cannot go every morning, drinking more coffee will not fix it. Your "
            "intestines are dry, not lazy.",
            "In Chinese medicine, dry stool means fluids and blood are not moistening "
            "the bowel. Pushing harder only weakens you further.",
            "Try this. Warm water with honey the moment you wake, then rub your belly "
            "clockwise thirty times before you get up.",
            "Comment bowel and I will send you my full morning movement protocol.",
        ],
        "notes": [
            "Dry, not lazy",
            "腸燥津虧 · 血不濡腸",
            "Warm honey water + clockwise belly rub",
            "Comment 👇 bowel",
        ],
        "first_dm": (
            "Hey! Warm honey water plus the clockwise belly rub is the combination that "
            "gets things moving 🚽\n\n"
            "Quick check — is your stool more dry and hard like pellets, or soft but "
            "still hard to pass?"
        ),
        "infographic": (
            "Title: 'Constipation — Moisten, Don't Force'.\n"
            "1) ROOT — intestine icon; text: fluids and blood are not moistening the "
            "bowel. Straining and stimulant laxatives weaken it further.\n"
            "2) WHAT DRIES IT — sun icon; text: too little water, coffee as a substitute "
            "for fluids, late nights, spicy and grilled food, long stress.\n"
            "3) MORNING FIX — glass and hand icons; text: warm honey water on waking, "
            "clockwise belly rub 30 times before getting up, add black sesame and pear."
        ),
        "second_dm": (
            "Here's your guide — do the belly rub before you sit up, not after. That "
            "order matters 🌅\n\n"
            "Want the moistening food list? Reply 'moisten'."
        ),
    },
    {
        "key": "piles",
        "name": "🪑 Hemorrhoids — Your Energy Has Sunk",
        "topic": "⚕️ General TCM",
        "hook": "Hemorrhoids mean your central energy has sunk.",
        "wardrobe": "navy",
        "rotation": 1,
        "prop_rest": 'a shallow dark ceramic basin of steaming water',
        "prop_hero": "a shallow dark ceramic basin and a small tied bundle of dried mugwort",
        "actions": [
            "holds the small tied bundle of dried mugwort up in his right hand",
            "rests a hand low on his own abdomen to indicate the centre sinking",
            "lowers the mugwort bundle towards the shallow dark ceramic basin on the desk",
            "rests both hands together on the desk beside the basin",
        ],
        "script": [
            "Hemorrhoids are not only a vein problem. In Chinese medicine they mean your "
            "central energy has sunk downward.",
            "Long sitting, straining and a weak spleen let everything descend. The "
            "vessels stay congested and cannot lift back up.",
            "Try this. A warm mugwort sitz bath for ten minutes at night, and gently "
            "lift your lower belly as you breathe out.",
            "Comment piles and I will send you my full lifting and soothing protocol.",
        ],
        "notes": [
            "Not just a vein problem",
            "中氣下陷",
            "艾葉 sitz bath + lift on the exhale",
            "Comment 👇 piles",
        ],
        "first_dm": (
            "Hey! The warm mugwort sitz bath calms things down fast 🪑\n\n"
            "Quick check — is it more itching and swelling, or bleeding when you go? "
            "They're handled differently."
        ),
        "infographic": (
            "Title: 'Hemorrhoids — Lift What Has Sunk'.\n"
            "1) ROOT — downward-arrow icon; text: central qi has sunk. Weak spleen plus "
            "long sitting and straining keeps the vessels congested.\n"
            "2) WHAT WORSENS IT — chair icon; text: sitting for hours, straining on the "
            "toilet, phone time on the seat, spicy food, alcohol, heavy lifting.\n"
            "3) NIGHTLY FIX — basin and herb icons; text: warm mugwort sitz bath 10 "
            "minutes, gently lift the lower belly on each exhale 20 times, stand up hourly."
        ),
        "second_dm": (
            "Here's your guide — the lifting breath is the part most people skip, and "
            "it's the part that stops it coming back 🌿\n\n"
            "Bleeding every time? Please get it checked in person first. Reply 'lift' "
            "for the qi-raising food list."
        ),
    },
    {
        "key": "ringing",
        "name": "👂 Ringing Ears — High Pitch vs Low Hum",
        "topic": "🫘 Kidney",
        "hook": "The ear is the opening of the kidney.",
        "wardrobe": "oatmeal",
        "rotation": 0,
        "prop_rest": 'a small empty pale celadon dish and a folded indigo cloth',
        "prop_hero": "a pair of polished walnuts resting in a small pale celadon dish",
        "actions": [
            "rolls the pair of polished walnuts in his right palm toward camera",
            "touches the outer rim of his own ear with one finger while facing camera",
            "cups one palm over his own ear to show the technique while facing camera",
            "rests both hands on the desk beside the small pale celadon dish",
        ],
        "script": [
            "If your ears ring in a quiet room, do not ignore it. In Chinese medicine, "
            "the ear is the opening of the kidney.",
            "A high sharp ring usually means liver fire rising. A low steady hum usually "
            "means kidney essence running empty.",
            "Try this. Cover both ears with your palms and flick your fingers on the "
            "back of your head twenty four times.",
            "Comment ringing and I will send you my full kidney and liver ear protocol.",
        ],
        "notes": [
            "Ear = opening of the kidney",
            "High ring 肝火 · low hum 腎虛",
            "鳴天鼓 × 24",
            "Comment 👇 ringing",
        ],
        "first_dm": (
            "Hey! The drumming-the-heavenly-drum technique is the one to start with 👂\n\n"
            "Quick check — is your ringing a HIGH sharp tone, or a LOW steady hum? That "
            "one answer changes the whole protocol."
        ),
        "infographic": (
            "Title: 'Ringing Ears — Two Sounds, Two Causes'.\n"
            "1) HIGH SHARP RING — flame icon; text: liver fire rising. Worse with anger, "
            "stress, late nights, alcohol. Often sudden and loud.\n"
            "2) LOW STEADY HUM — empty-vessel icon; text: kidney essence running low. "
            "Worse with overwork and age, often with lower back ache and night waking.\n"
            "3) DAILY FIX — palms-on-ears icon; text: drum the heavenly drum 24 times "
            "daily, black beans and walnut for essence, cut alcohol and late nights."
        ),
        "second_dm": (
            "Here's your guide — do the drumming morning and night, and track whether "
            "the pitch changes 🔔\n\n"
            "Sudden ringing in ONE ear with hearing loss needs a doctor now, not a tea. "
            "Reply 'ears' for the food list."
        ),
    },
    {
        "key": "sweat",
        "name": "💦 Night Sweats — Your Yin Is Running Low",
        "topic": "🌡️ Body Constitution",
        "hook": "Waking up damp at night is yin deficiency.",
        "wardrobe": "charcoal",
        "rotation": 2,
        "prop_rest": 'a small pale celadon bowl of goji berries and dried lily bulb',
        "prop_hero": "a folded white cotton towel and a small pale celadon bowl of goji berries and dried lily bulb",
        "actions": [
            "holds the folded white cotton towel in his right hand",
            "touches the centre of his own chest with a flat palm while facing camera",
            "lifts the small pale celadon bowl of goji berries and dried lily bulb toward camera",
            "sets the bowl down and rests both hands on the desk",
        ],
        "script": [
            "If you wake up damp at night but feel fine all day, that is not the room "
            "being hot. That is yin deficiency.",
            "When yin runs low it can no longer hold the yang at night. The heat floats "
            "up and pushes sweat out while you sleep.",
            "Try this. Simmer lily bulb and goji berries into a light soup and drink it "
            "warm in the evening. It refills the yin.",
            "Comment sweat and I will send you my full yin nourishing night protocol.",
        ],
        "notes": [
            "Damp at night, fine by day",
            "陰虛不斂陽 · 盜汗",
            "百合 + 枸杞 evening soup",
            "Comment 👇 sweat",
        ],
        "first_dm": (
            "Hey! Lily bulb and goji simmered into a light evening soup is the classic "
            "fix for night sweats 💦\n\n"
            "Quick check — do you also get warm palms and soles, or wake around three "
            "in the morning?"
        ),
        "infographic": (
            "Title: 'Night Sweats — Refill the Yin'.\n"
            "1) THE SIGN — moon-and-droplet icon; text: damp at night, fine by day. Yin "
            "can no longer hold yang, so heat floats up in sleep.\n"
            "2) COMES WITH — hand icon; text: warm palms and soles, dry mouth at night, "
            "waking around 3am, red tongue with little coating.\n"
            "3) EVENING FIX — bowl icon; text: lily bulb and goji soup warm in the "
            "evening, black beans and pear, cut spicy food, alcohol and late screens."
        ),
        "second_dm": (
            "Here's your guide — drink it warm in the EVENING, not the morning. Timing "
            "is half of it 🌙\n\n"
            "Night sweats with weight loss or fever need a doctor first. Reply 'yin' for "
            "the full food list."
        ),
    },
    {
        "key": "reflux",
        "name": "🔥 Reflux and Burping — It's a Direction Problem",
        "topic": "🍵 Stomach",
        "hook": "Your stomach energy is going the wrong way.",
        "wardrobe": "navy",
        "rotation": 1,
        "prop_rest": 'two fresh ginger slices on a light wooden board',
        "prop_hero": "a small pale celadon cup of warm rice water and two fresh ginger slices on a light wooden board",
        "actions": [
            "holds the small pale celadon cup of warm rice water in his right hand",
            "draws a slow downward line in the air in front of his own chest",
            "lifts one fresh ginger slice from the light wooden board toward camera",
            "sets the cup down and rests both hands on the desk",
        ],
        "script": [
            "If you burn and burp after every meal, the problem is direction. Your "
            "stomach energy is going up instead of down.",
            "Cold food, late dinners and eating in a rush all break that downward flow. "
            "Then the acid follows the wrong way.",
            "Try this. Sip warm rice water with two slices of ginger before your meal, "
            "and finish eating three hours before bed.",
            "Comment reflux and I will send you my full stomach settling protocol.",
        ],
        "notes": [
            "A direction problem",
            "胃氣上逆",
            "Warm rice water + ginger, 3h before bed",
            "Comment 👇 reflux",
        ],
        "first_dm": (
            "Hey! Warm rice water with ginger before meals settles the stomach "
            "downward 🔥\n\n"
            "Quick check — is it worse when you lie down, or worse on an empty stomach? "
            "Different pattern, different fix."
        ),
        "infographic": (
            "Title: 'Reflux — Send the Stomach Qi Back Down'.\n"
            "1) ROOT — upward-arrow icon; text: stomach qi is rebelling upward instead "
            "of descending. Acid simply follows the wrong direction.\n"
            "2) WHAT BREAKS THE FLOW — clock icon; text: cold and raw food, eating in a "
            "rush, late heavy dinners, lying down after meals, stress at the table.\n"
            "3) MEALTIME FIX — cup and ginger icons; text: warm rice water with 2 ginger "
            "slices before meals, stop eating 3 hours before bed, sit upright 20 minutes after."
        ),
        "second_dm": (
            "Here's your guide — the three-hour rule before bed does more than any tea "
            "on its own 🌙\n\n"
            "Want the stomach-warming food list? Reply 'warm'."
        ),
    },
    {
        "key": "cramps",
        "name": "🦵 Night Leg Cramps — Your Liver Blood Is Low",
        "topic": "🦶 Feet / Legs",
        "hook": "The liver rules the tendons, not calcium.",
        "wardrobe": "oatmeal",
        "rotation": 0,
        "prop_rest": 'a shallow wooden bowl of plump red dates',
        "prop_hero": "a shallow wooden bowl of plump red dates",
        "actions": [
            "lifts one plump red date from the shallow wooden bowl toward camera",
            "runs a hand down the side of his own forearm to trace the tendon line",
            "presses two fingers behind his own knee to show the point while facing camera",
            "rests both hands on the desk beside the shallow wooden bowl",
        ],
        "script": [
            "If your calf seizes up at night, more calcium is not always the answer. In "
            "Chinese medicine, the liver rules the tendons.",
            "When liver blood is low the tendons lose their moisture. They shorten and "
            "grip, and it always happens at night.",
            "Try this. Eat red dates every day, and press the point behind your knee for "
            "one minute before you sleep.",
            "Comment cramps and I will send you my full liver blood and tendon protocol.",
        ],
        "notes": [
            "Not always calcium",
            "肝血虛 · 筋失所養",
            "紅棗 daily + 委中 before bed",
            "Comment 👇 cramps",
        ],
        "first_dm": (
            "Hey! Red dates plus the point behind the knee is where I'd start for night "
            "cramps 🦵\n\n"
            "Quick check — is it mostly the calf, or do your toes curl too? And do you "
            "also get dry eyes or brittle nails?"
        ),
        "infographic": (
            "Title: 'Night Leg Cramps — Feed the Tendons'.\n"
            "1) ROOT — tendon icon; text: the liver rules the tendons and stores the "
            "blood. Low liver blood leaves tendons dry, so they shorten and grip.\n"
            "2) COMES WITH — eye icon; text: dry eyes, brittle nails, floaters, pale "
            "lips, light and easily broken sleep.\n"
            "3) NIGHTLY FIX — dates and knee icons; text: red dates daily, press behind "
            "the knee 1 minute before bed, warm the calves, add goji and dark greens."
        ),
        "second_dm": (
            "Here's your guide — press the point BEFORE bed, not during the cramp 🌙\n\n"
            "Want the liver-blood food list? Reply 'blood'."
        ),
    },
    {
        "key": "memory",
        "name": "🌫️ Brain Fog — Your Brain Is Under-Fed",
        "topic": "🧠 Mental Health",
        "hook": "Brain fog is not just age.",
        "wardrobe": "charcoal",
        "rotation": 2,
        "prop_rest": 'a little unglazed clay teapot',
        "prop_hero": "a small pale celadon bowl of shelled walnuts and a little clay teapot",
        "actions": [
            "holds a shelled walnut up between his fingers toward camera",
            "touches the side of his own temple with two fingers while facing camera",
            "presses the crown of his own head with two fingers to show the point",
            "rests both hands on the desk beside the little clay teapot",
        ],
        "script": [
            "If you walk into a room and forget why, that is not just age. Your brain is "
            "being starved of blood and essence.",
            "In Chinese medicine, the kidney fills the brain and the spleen makes the "
            "blood. When both are tired, thinking gets foggy.",
            "Try this. Eat two walnuts every morning, and press the top of your head for "
            "one minute to lift the clear energy.",
            "Comment memory and I will send you my full brain clearing protocol.",
        ],
        "notes": [
            "Not just age",
            "腎生髓充腦 · 脾統血",
            "2 walnuts + 百會 press",
            "Comment 👇 memory",
        ],
        "first_dm": (
            "Hey! Two walnuts a morning plus the crown-point press is the simplest place "
            "to start 🌫️\n\n"
            "Quick check — is your fog worse in the morning, or does it come on after "
            "you eat? That tells me which organ to treat."
        ),
        "infographic": (
            "Title: 'Brain Fog — Feed the Sea of Marrow'.\n"
            "1) ROOT — brain icon; text: the kidney fills the brain and the spleen makes "
            "the blood. When both are tired, the mind is under-fed.\n"
            "2) WHAT DRAINS IT — screen icon; text: overwork, late nights, skipped "
            "meals, too much cold and raw food, long worry and rumination.\n"
            "3) DAILY FIX — walnut and crown icons; text: 2 walnuts each morning, press "
            "the crown of the head 1 minute, warm breakfast, protect sleep before 11pm."
        ),
        "second_dm": (
            "Here's your guide — fog that lifts after a warm breakfast is a spleen "
            "pattern, fog that never lifts is a kidney one 🧠\n\n"
            "Want the brain-feeding food list? Reply 'clear'."
        ),
    },
    {
        "key": "acne",
        "name": "🗺️ Your Face Is a Map — Where Acne Appears Matters",
        "topic": "🦷 Skin / Beauty",
        "hook": "Where your pimples appear is not random.",
        "wardrobe": "navy",
        "rotation": 1,
        "prop_rest": 'a tiny celadon cup holding a sprig of fresh mint',
        "prop_hero": "a small round wooden-handled hand mirror and a sprig of fresh mint in a tiny celadon cup",
        "actions": [
            "holds the small round wooden-handled hand mirror up beside his own face",
            "touches his own forehead lightly with two fingers while facing camera",
            "lifts the tiny celadon cup with the sprig of fresh mint toward camera",
            "lowers the mirror and rests both hands on the desk",
        ],
        "script": [
            "Where your pimples appear is not random. Your face is a map, and each area "
            "points to a different organ inside.",
            "The forehead follows heart and small intestine heat. The cheeks follow the "
            "lungs. The chin and jaw follow your hormones.",
            "Try this. Read your own pattern in a mirror, then cool the matching organ "
            "with mint tea instead of scrubbing your skin.",
            "Comment acne and I will send you my full face map and cooling protocol.",
        ],
        "notes": [
            "The face is a map",
            "Forehead 心/小腸 · cheeks 肺 · jaw 腎/衝任",
            "Read the zone, cool the organ",
            "Comment 👇 acne",
        ],
        "first_dm": (
            "Hey! Face mapping tells you which organ to cool instead of just attacking "
            "the skin 🗺️\n\n"
            "Quick check — where do yours cluster most: forehead, cheeks, or chin and "
            "jawline?"
        ),
        "infographic": (
            "Title: 'Face Map — Where Acne Appears, and Why'.\n"
            "1) FOREHEAD — flame icon; text: heart and small intestine heat. Worse with "
            "late nights, stress, spicy food and too much coffee.\n"
            "2) CHEEKS — lung icon; text: lung heat and outside irritation. Worse with "
            "smoke, dry air, dairy and an unwashed pillowcase.\n"
            "3) CHIN AND JAW — moon icon; text: hormonal and kidney-related. Flares "
            "around the cycle and with sugar and long sleep debt.\n"
            "Footer band: cool the matching organ with mint tea, don't scrub the skin."
        ),
        "second_dm": (
            "Here's your face map — match your main zone, then treat THAT organ for four "
            "weeks 🌿\n\n"
            "Want the cooling food list for your zone? Reply with 'forehead', 'cheeks' "
            "or 'jaw'."
        ),
    },
]
