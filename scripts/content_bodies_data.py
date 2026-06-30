# -*- coding: utf-8 -*-
"""
Authored Content Library bodies — matches the gold-standard Migraine format.

Each concept:
  master_script : 4 lines (hook → TCM root cause → on-screen quick win → CTA).
                  Comma-light (commas make MiniMax TTS pause). Each line ≤ ~13s.
  shots         : 4 shots; voice mirrors the master_script lines 1:1.
  first_dm      : instant text DM (ends with a qualifying question → triggers reply).
  infographic_brief : GPT image-gen prompt (vertical 4:5, TCM diagnostic aesthetic).
  second_dm     : delivered with the infographic after the viewer replies.

Style: confident hook, root-cause TCM framing, ONE concrete at-home quick win
shown on screen before the CTA. Remedies framed as "try this / may help / support".
"""

CONCEPTS = [
    # ───────────────────────── 1. Tonsil Stones ─────────────────────────
    {
        "title": "Tonsil Stones (Hidden in Throat, TCM Fix)",
        "master_script": [
            "Watch what came out of her throat. Tonsil stones. She came to me embarrassed about her breath.",
            "In Chinese medicine we do not only look at the tonsils. The root is dampness heat and digestive stagnation rising up into the throat.",
            "Try this daily gargle. Warm water with one teaspoon of sea salt and a squeeze of lemon. It may help loosen the buildup and support the throat.",
            "Comment tonsil and I will send you my full throat and gut clearing protocol.",
        ],
        "shots": [
            {"n": 1, "secs": 10, "beat": "Hook",
             "visual": "Elderly TCM doctor in a warm clinic faces a slightly embarrassed woman; he holds up a small tongue depressor toward camera with a knowing look. Quick insert cut to an extreme close-up of a single pale tonsil stone on a tissue. Back to the doctor leaning in.",
             "voice": "Watch what came out of her throat. Tonsil stones. She came to me embarrassed about her breath.",
             "caption": "Those white chunks = tonsil stones"},
            {"n": 2, "secs": 12, "beat": "Root Cause",
             "visual": "Doctor turns to a simple anatomy chart, traces a line from the stomach up to the throat with two fingers. Cutaway insert of steam rising from a bowl to suggest dampness and heat. Return to doctor pointing at his own throat.",
             "voice": "In Chinese medicine we do not only look at the tonsils. The root is dampness heat and digestive stagnation rising up into the throat.",
             "caption": "濕熱 + 食滯 → 咽喉"},
            {"n": 3, "secs": 12, "beat": "The Fix",
             "visual": "Doctor at the table pours warm water into a glass, adds a spoon of sea salt and squeezes half a lemon; he stirs and lifts it toward camera, then mimes gargling. Clean overhead insert of the salt and lemon beside the glass.",
             "voice": "Try this daily gargle. Warm water with one teaspoon of sea salt and a squeeze of lemon. It may help loosen the buildup and support the throat.",
             "caption": "Warm water + salt + lemon gargle"},
            {"n": 4, "secs": 8, "beat": "CTA",
             "visual": "Doctor looks straight into the camera, calm and confident, gives a small reassuring nod.",
             "voice": "Comment tonsil and I will send you my full throat and gut clearing protocol.",
             "caption": "Comment 👇 tonsil"},
        ],
        "first_dm": (
            "Hey! Tonsil stones almost always trace back to the gut, not just the throat 🌿\n\n"
            "Quick check so I send the right plan — is your bad breath worse in the morning, "
            "or all day even after brushing?"
        ),
        "infographic_brief": (
            "Vertical infographic, 4:5 ratio, warm TCM clinic aesthetic (cream background, "
            "terracotta + sage accents, clean serif headings).\n"
            "Title: 'Tonsil Stones — The Gut–Throat Connection'.\n"
            "Three stacked panels:\n"
            "1) WHY THEY FORM — icon of throat + small stones; text: dampness, heat, food stagnation rising up.\n"
            "2) DAILY GARGLE — icon of glass + salt + lemon; text: warm water, 1 tsp sea salt, squeeze of lemon, gargle 30s after meals.\n"
            "3) ROOT FIX — icon of stomach; text: warm cooked food, less dairy and sugar, support digestion.\n"
            "Footer: 'Persistent? See a practitioner.' No real photos — clean flat icons only."
        ),
        "second_dm": (
            "Here's your tonsil-stone clearing guide — save it and start with the gargle tonight 🧂\n\n"
            "Want the full gut-reset food list that stops them coming back? Just reply 'gut'."
        ),
    },

    # ───────────────────────── 2. Bad Breath ─────────────────────────
    {
        "title": "Bad Breath (Gut Root Cause + Oral Rinse Fix)",
        "master_script": [
            "Check your breath right now. Cup your hand over your mouth and breathe out. If it smells the cause is not your mouth.",
            "In Chinese medicine chronic bad breath comes from heat and food stagnation in the stomach. The smell rises up from the gut not the tongue.",
            "Try this. Chew a few fennel seeds after meals and rinse with warm salt water. It may cool stomach heat and freshen the breath at the source.",
            "Comment breath and I will send you my full gut and breath reset.",
        ],
        "shots": [
            {"n": 1, "secs": 10, "beat": "Hook",
             "visual": "Doctor demonstrates to camera by cupping his hand near his mouth and breathing out, raising an eyebrow. Quick insert of a worried person doing the same and recoiling slightly. Back to doctor shaking his head gently.",
             "voice": "Check your breath right now. Cup your hand over your mouth and breathe out. If it smells the cause is not your mouth.",
             "caption": "Bad breath starts in the gut"},
            {"n": 2, "secs": 12, "beat": "Root Cause",
             "visual": "Doctor points to a stomach diagram, makes a rising-heat gesture with both hands moving upward. Cutaway insert of a covered pot simmering, lid rattling with steam to suggest stomach heat.",
             "voice": "In Chinese medicine chronic bad breath comes from heat and food stagnation in the stomach. The smell rises up from the gut not the tongue.",
             "caption": "胃熱 + 食滯"},
            {"n": 3, "secs": 12, "beat": "The Fix",
             "visual": "Doctor tips a small spoon of fennel seeds into his palm and offers them to camera, then stirs salt into a warm glass and mimes rinsing. Overhead insert of fennel seeds and the salt-water glass on the table.",
             "voice": "Try this. Chew a few fennel seeds after meals and rinse with warm salt water. It may cool stomach heat and freshen the breath at the source.",
             "caption": "Fennel seeds + warm salt rinse"},
            {"n": 4, "secs": 8, "beat": "CTA",
             "visual": "Doctor leans in toward camera with a friendly confident expression.",
             "voice": "Comment breath and I will send you my full gut and breath reset.",
             "caption": "Comment 👇 breath"},
        ],
        "first_dm": (
            "Hey! Fresh-breath fix coming 🌬️ — but it works best when we target the right cause.\n\n"
            "Quick one: is your tongue more white-coated or yellow-coated in the morning?"
        ),
        "infographic_brief": (
            "Vertical infographic, 4:5 ratio, warm TCM clinic aesthetic (cream bg, terracotta + sage accents).\n"
            "Title: 'Bad Breath — Fix the Gut, Not Just the Mouth'.\n"
            "Three panels:\n"
            "1) THE REAL CAUSE — stomach icon with heat lines; text: stomach heat + undigested food.\n"
            "2) QUICK FIX — fennel + glass icons; text: chew fennel after meals, rinse with warm salt water.\n"
            "3) ROOT RESET — plate icon; text: smaller warm meals, less greasy/spicy food, more bitter greens.\n"
            "Footer: 'No improvement in 2 weeks? Check for reflux or sinus.' Flat icons, no photos."
        ),
        "second_dm": (
            "Here's your breath-reset guide — the fennel trick works fastest after meals 🌿\n\n"
            "Reply 'gut' and I'll send the food list that keeps stomach heat down for good."
        ),
    },

    # ───────────────────────── 3. Skin Tags ─────────────────────────
    {
        "title": "Skin Tags (Shrink Overnight with Castor Oil)",
        "master_script": [
            "Those skin tags can start shrinking overnight. In Chinese medicine we have used this remedy for generations.",
            "Skin tags are not just skin. They are a sign of dampness and stagnation and often blood sugar running high underneath.",
            "Try this. Dab pure castor oil on the tag morning and night and cover it. It may slowly dry the tag while you fix the inside.",
            "Comment tags and I will send you my full skin and blood sugar protocol.",
        ],
        "shots": [
            {"n": 1, "secs": 10, "beat": "Hook",
             "visual": "Doctor holds up a small amber bottle of castor oil to camera with a confident half-smile. Macro insert of a tiny dropper releasing one golden drop. Back to doctor nodding.",
             "voice": "Those skin tags can start shrinking overnight. In Chinese medicine we have used this remedy for generations.",
             "caption": "Skin tags can shrink overnight"},
            {"n": 2, "secs": 12, "beat": "Root Cause",
             "visual": "Doctor gestures to neck and underarm areas on a body chart, then makes a sticky pinching motion with his fingers to suggest dampness. Cutaway insert of a sugar cube dissolving in water.",
             "voice": "Skin tags are not just skin. They are a sign of dampness and stagnation and often blood sugar running high underneath.",
             "caption": "痰濕 + 血糖偏高"},
            {"n": 3, "secs": 12, "beat": "The Fix",
             "visual": "Doctor dips a cotton swab into the castor oil and gently dabs the side of his own neck, then presses a small plaster over it. Clean overhead insert of castor oil bottle, cotton swab and plaster.",
             "voice": "Try this. Dab pure castor oil on the tag morning and night and cover it. It may slowly dry the tag while you fix the inside.",
             "caption": "Castor oil + cover, twice daily"},
            {"n": 4, "secs": 8, "beat": "CTA",
             "visual": "Doctor faces camera directly, warm and assured.",
             "voice": "Comment tags and I will send you my full skin and blood sugar protocol.",
             "caption": "Comment 👇 tags"},
        ],
        "first_dm": (
            "Hey! The castor-oil method works — but skin tags love high blood sugar, so let's check the root 🍃\n\n"
            "Quick q: do you have just a few tags, or clusters around the neck and underarms?"
        ),
        "infographic_brief": (
            "Vertical infographic, 4:5 ratio, warm TCM clinic aesthetic.\n"
            "Title: 'Skin Tags — Surface Sign of an Inside Problem'.\n"
            "Three panels:\n"
            "1) WHAT THEY MEAN — neck/underarm icon; text: dampness, stagnation, often high blood sugar.\n"
            "2) OVERNIGHT FIX — castor oil + plaster icon; text: dab pure castor oil morning + night, cover.\n"
            "3) FIX THE INSIDE — plate icon; text: cut refined sugar, add cinnamon + bitter greens, move after meals.\n"
            "Footer: 'Changing, bleeding, or fast-growing? See a doctor.' Flat icons only."
        ),
        "second_dm": (
            "Here's your skin-tag guide — patience is key, the oil works gradually 🌙\n\n"
            "Want the blood-sugar food list that stops new tags forming? Reply 'sugar'."
        ),
    },

    # ───────────────────────── 4. Yellow Teeth ─────────────────────────
    {
        "title": "Yellow Teeth (Baking Soda + Banana Peel)",
        "master_script": [
            "The yellow on your teeth can start lifting in under two minutes. No expensive strips needed.",
            "Yellowing is not only coffee and tea. In Chinese medicine the teeth reflect the kidneys and the bones so the inside matters too.",
            "Try this twice a week. Rub the inside of a banana peel on your teeth then brush with a little baking soda. It may gently lift surface stains.",
            "Comment teeth and I will send you my full teeth and kidney support guide.",
        ],
        "shots": [
            {"n": 1, "secs": 10, "beat": "Hook",
             "visual": "Doctor smiles widely to camera and taps his own teeth, then holds up a ripe banana. Macro insert of the soft white inside of a banana peel. Back to doctor with a confident grin.",
             "voice": "The yellow on your teeth can start lifting in under two minutes. No expensive strips needed.",
             "caption": "Whiter teeth in 2 minutes"},
            {"n": 2, "secs": 12, "beat": "Root Cause",
             "visual": "Doctor points to a tooth diagram then to the lower back to indicate the kidney link. Cutaway insert of a cup of dark tea staining a white cloth.",
             "voice": "Yellowing is not only coffee and tea. In Chinese medicine the teeth reflect the kidneys and the bones so the inside matters too.",
             "caption": "齒為腎之餘"},
            {"n": 3, "secs": 12, "beat": "The Fix",
             "visual": "Doctor rubs the inside of a banana peel across his teeth, then sprinkles a little baking soda onto a toothbrush and brushes. Overhead insert of banana peel and a small dish of baking soda.",
             "voice": "Try this twice a week. Rub the inside of a banana peel on your teeth then brush with a little baking soda. It may gently lift surface stains.",
             "caption": "Banana peel + baking soda, 2x/week"},
            {"n": 4, "secs": 8, "beat": "CTA",
             "visual": "Doctor faces camera with a bright reassuring smile.",
             "voice": "Comment teeth and I will send you my full teeth and kidney support guide.",
             "caption": "Comment 👇 teeth"},
        ],
        "first_dm": (
            "Hey! The banana-peel + baking soda trick is great for surface stains ✨\n\n"
            "Quick check so I tailor it — is your yellowing more on the surface, or deep and grey-ish?"
        ),
        "infographic_brief": (
            "Vertical infographic, 4:5 ratio, warm TCM clinic aesthetic.\n"
            "Title: 'Yellow Teeth — Surface vs Inside'.\n"
            "Three panels:\n"
            "1) WHY — tooth icon; text: stains from food + the kidney/bone connection in TCM.\n"
            "2) 2-MIN FIX — banana peel + baking soda icons; text: rub peel, brush with pinch of baking soda, 2x weekly only.\n"
            "3) PROTECT — water icon; text: rinse after coffee/tea, limit baking soda to avoid enamel wear.\n"
            "Footer: 'Sensitivity or deep discoloration? See a dentist.' Flat icons only."
        ),
        "second_dm": (
            "Here's your whitening guide — twice a week max so you protect the enamel 🦷\n\n"
            "Want the kidney-support foods that strengthen teeth from inside? Reply 'kidney'."
        ),
    },

    # ───────────────────────── 5. Dry Cracked Heels ─────────────────────────
    {
        "title": "Dry Cracked Heels (Overnight Fix)",
        "master_script": [
            "Those dry cracked heels can start clearing overnight. You do not need to keep buying creams that never last.",
            "Cracked heels are not only dry skin. In Chinese medicine they point to blood deficiency and weak kidney and spleen unable to moisten the skin.",
            "Try this. Soak your feet in warm water then rub on coconut oil and sleep in cotton socks. It may deeply soften and seal the cracks.",
            "Comment heels and I will send you my full skin and blood nourishing protocol.",
        ],
        "shots": [
            {"n": 1, "secs": 10, "beat": "Hook",
             "visual": "Doctor holds up a jar of coconut oil and a pair of cotton socks toward camera. Macro insert of a cracked dry heel, then the same heel looking smoother. Back to doctor with an encouraging nod.",
             "voice": "Those dry cracked heels can start clearing overnight. You do not need to keep buying creams that never last.",
             "caption": "Heal cracked heels overnight"},
            {"n": 2, "secs": 12, "beat": "Root Cause",
             "visual": "Doctor traces from the lower abdomen down to the feet on a body chart to show the spleen and kidney link. Cutaway insert of a dry riverbed cracking to mirror the heel.",
             "voice": "Cracked heels are not only dry skin. In Chinese medicine they point to blood deficiency and weak kidney and spleen unable to moisten the skin.",
             "caption": "血虛 + 脾腎不足"},
            {"n": 3, "secs": 12, "beat": "The Fix",
             "visual": "Doctor lifts a foot from a basin of warm water pats it dry scoops coconut oil and massages the heel then pulls on a cotton sock. Overhead insert of basin coconut oil and socks.",
             "voice": "Try this. Soak your feet in warm water then rub on coconut oil and sleep in cotton socks. It may deeply soften and seal the cracks.",
             "caption": "Soak + coconut oil + cotton socks"},
            {"n": 4, "secs": 8, "beat": "CTA",
             "visual": "Doctor looks into camera warmly and gives a small confident nod.",
             "voice": "Comment heels and I will send you my full skin and blood nourishing protocol.",
             "caption": "Comment 👇 heels"},
        ],
        "first_dm": (
            "Hey! The overnight coconut-oil soak softens heels fast 🦶\n\n"
            "Quick check — are your cracks just dry, or deep and sometimes painful or bleeding?"
        ),
        "infographic_brief": (
            "Vertical infographic, 4:5 ratio, warm TCM clinic aesthetic.\n"
            "Title: 'Cracked Heels — It's Not Just Dry Skin'.\n"
            "Three panels:\n"
            "1) ROOT — foot icon; text: blood deficiency + weak spleen/kidney can't moisten skin.\n"
            "2) OVERNIGHT FIX — basin + oil + sock icons; text: warm soak 10 min, coconut oil, cotton socks to bed.\n"
            "3) NOURISH INSIDE — bowl icon; text: red dates, black sesame, bone broth, enough water.\n"
            "Footer: 'Diabetic or deep painful cracks? See a podiatrist.' Flat icons only."
        ),
        "second_dm": (
            "Here's your cracked-heel guide — do the soak 3 nights in a row to see the change 🌙\n\n"
            "Want the blood-nourishing food list that fixes it from inside? Reply 'blood'."
        ),
    },

    # ───────────────────────── 6. Nail Fungus ─────────────────────────
    {
        "title": "Nail Fungus (Overnight Garlic + Vinegar Remedy)",
        "master_script": [
            "That nail fungus can start clearing overnight. In Chinese medicine we have had the remedy for a very long time.",
            "Fungus takes hold when there is dampness and heat in the body and weak circulation reaching the toes.",
            "Try this. Soak the toe in warm water with apple cider vinegar then rub on a little crushed garlic and cover it. It may fight the fungus directly.",
            "Comment nails and I will send you my full anti fungal and circulation protocol.",
        ],
        "shots": [
            {"n": 1, "secs": 10, "beat": "Hook",
             "visual": "Doctor holds up a head of garlic and a bottle of apple cider vinegar toward camera. Macro insert of a thick discolored toenail, then a healthier looking nail. Back to doctor nodding firmly.",
             "voice": "That nail fungus can start clearing overnight. In Chinese medicine we have had the remedy for a very long time.",
             "caption": "Clear nail fungus overnight"},
            {"n": 2, "secs": 12, "beat": "Root Cause",
             "visual": "Doctor makes a damp sticky gesture with his fingers then points to the toes on a foot chart and traces poor circulation up the leg. Cutaway insert of mold spreading on a damp surface, fast.",
             "voice": "Fungus takes hold when there is dampness and heat in the body and weak circulation reaching the toes.",
             "caption": "濕熱 + 末梢循環差"},
            {"n": 3, "secs": 12, "beat": "The Fix",
             "visual": "Doctor lifts a foot from a small basin pats it dry then dabs crushed garlic onto the toenail and wraps it with a plaster. Overhead insert of vinegar basin garlic and plaster.",
             "voice": "Try this. Soak the toe in warm water with apple cider vinegar then rub on a little crushed garlic and cover it. It may fight the fungus directly.",
             "caption": "ACV soak + garlic + cover"},
            {"n": 4, "secs": 8, "beat": "CTA",
             "visual": "Doctor looks straight into camera with calm authority.",
             "voice": "Comment nails and I will send you my full anti fungal and circulation protocol.",
             "caption": "Comment 👇 nails"},
        ],
        "first_dm": (
            "Hey! The vinegar + garlic combo is a strong natural antifungal 🧄\n\n"
            "Quick check so I send the right plan — is it one nail, or spreading across several toes?"
        ),
        "infographic_brief": (
            "Vertical infographic, 4:5 ratio, warm TCM clinic aesthetic.\n"
            "Title: 'Nail Fungus — Clear It, Then Keep It Away'.\n"
            "Three panels:\n"
            "1) WHY — toe icon; text: dampness + heat + poor circulation to the feet.\n"
            "2) NIGHTLY FIX — basin + garlic icons; text: ACV soak 10 min, dab crushed garlic, cover overnight.\n"
            "3) STOP RETURN — sock icon; text: dry feet fully, breathable socks, warm the feet, move daily.\n"
            "Footer: 'Diabetic or painful/spreading? See a doctor.' Flat icons only."
        ),
        "second_dm": (
            "Here's your nail-fungus guide — stay consistent nightly for a few weeks 🌿\n\n"
            "Want the circulation routine that helps it heal faster? Reply 'circ'."
        ),
    },

    # ───────────────────────── 7. Salt in Socks ─────────────────────────
    {
        "title": "Salt in Socks (Ancient Pain Remedy)",
        "master_script": [
            "Put salt in your socks and big pharma loses money. It sounds strange but it is one of the oldest pain remedies we have.",
            "In Chinese medicine the soles of the feet hold powerful points that connect to the whole body. Cold and damp settling there can drive aches and poor sleep.",
            "Try this. Warm coarse sea salt gently put it in a thin cotton sock and rest your feet on it. It holds heat and may ease pain and tension.",
            "Comment salt and I will send you my full foot warming and pain relief routine.",
        ],
        "shots": [
            {"n": 1, "secs": 10, "beat": "Hook",
             "visual": "Doctor in a cozy room holds up a spoonful of coarse sea salt and a cotton sock, with a slightly mischievous smile. Macro insert of salt being poured into the sock. Back to doctor raising an eyebrow.",
             "voice": "Put salt in your socks and big pharma loses money. It sounds strange but it is one of the oldest pain remedies we have.",
             "caption": "Salt in your socks for pain"},
            {"n": 2, "secs": 12, "beat": "Root Cause",
             "visual": "Doctor points to the sole of a foot chart showing the key point, then mimes cold seeping in by rubbing his arms. Cutaway insert of frost forming, then warmth spreading as a glow.",
             "voice": "In Chinese medicine the soles of the feet hold powerful points that connect to the whole body. Cold and damp settling there can drive aches and poor sleep.",
             "caption": "湧泉穴 · 寒濕"},
            {"n": 3, "secs": 12, "beat": "The Fix",
             "visual": "Doctor warms salt in a pan tips it into a thin sock ties it and presses it against the sole of his foot with a satisfied expression. Overhead insert of warm salt sock and bare feet.",
             "voice": "Try this. Warm coarse sea salt gently put it in a thin cotton sock and rest your feet on it. It holds heat and may ease pain and tension.",
             "caption": "Warm salt sock on the soles"},
            {"n": 4, "secs": 8, "beat": "CTA",
             "visual": "Doctor faces camera with a calm reassuring nod.",
             "voice": "Comment salt and I will send you my full foot warming and pain relief routine.",
             "caption": "Comment 👇 salt"},
        ],
        "first_dm": (
            "Hey! Warm-salt foot therapy is one of my favorite simple remedies 🧦\n\n"
            "Quick q so I tailor it — is your pain more in the feet and legs, or in the lower back?"
        ),
        "infographic_brief": (
            "Vertical infographic, 4:5 ratio, warm TCM clinic aesthetic.\n"
            "Title: 'Salt in Socks — Warmth Where It Matters'.\n"
            "Three panels:\n"
            "1) WHY — sole-of-foot icon with point marked; text: feet hold key points; cold + damp cause aches.\n"
            "2) HOW — warm salt + sock icons; text: warm coarse sea salt, thin cotton sock, rest soles on it 15–20 min.\n"
            "3) BOOST — text: best before bed, pair with warm water, keep feet covered.\n"
            "Footer: 'Never use salt hot enough to burn. Numb feet? See a doctor.' Flat icons only."
        ),
        "second_dm": (
            "Here's your warm-salt routine — do it before bed for better sleep too 🌙\n\n"
            "Want my full cold-and-damp clearing plan for stubborn aches? Reply 'warm'."
        ),
    },

    # ───────────────────────── 8. Kidney Stones ─────────────────────────
    {
        "title": "Kidney Stones (4-Day Coconut Water Flush)",
        "master_script": [
            "Those kidney stones can be gone in about four days. And no you do not need an expensive miracle diet.",
            "In Chinese medicine stones form when heat and dampness condense in the kidneys and the water pathways get blocked.",
            "Try this for four days. Drink fresh coconut water with a squeeze of lemon each morning and plenty of warm water. It may help flush and soothe the tract.",
            "Comment kidney and I will send you my full stone flushing protocol.",
        ],
        "shots": [
            {"n": 1, "secs": 10, "beat": "Hook",
             "visual": "Doctor holds up a fresh green coconut with a straw and a lemon, confident smile. Macro insert of coconut water pouring into a glass. Back to doctor raising four fingers.",
             "voice": "Those kidney stones can be gone in about four days. And no you do not need an expensive miracle diet.",
             "caption": "Flush kidney stones in 4 days"},
            {"n": 2, "secs": 12, "beat": "Root Cause",
             "visual": "Doctor points to a kidney diagram and traces the path down to the bladder, then mimes a blockage clearing. Cutaway insert of mineral crystals forming in still water versus dissolving in flowing water.",
             "voice": "In Chinese medicine stones form when heat and dampness condense in the kidneys and the water pathways get blocked.",
             "caption": "濕熱 → 結石"},
            {"n": 3, "secs": 12, "beat": "The Fix",
             "visual": "Doctor squeezes lemon into a glass of coconut water stirs and drinks, then gestures to a large jug of warm water. Overhead insert of coconut lemon and glass on the table.",
             "voice": "Try this for four days. Drink fresh coconut water with a squeeze of lemon each morning and plenty of warm water. It may help flush and soothe the tract.",
             "caption": "Coconut water + lemon, 4 mornings"},
            {"n": 4, "secs": 8, "beat": "CTA",
             "visual": "Doctor looks into camera with steady reassuring confidence.",
             "voice": "Comment kidney and I will send you my full stone flushing protocol.",
             "caption": "Comment 👇 kidney"},
        ],
        "first_dm": (
            "Hey! The coconut-water flush is gentle and effective for small stones 🥥\n\n"
            "Quick and important — do you know roughly how big your stones are, or are they tiny/gravel-like?"
        ),
        "infographic_brief": (
            "Vertical infographic, 4:5 ratio, warm TCM clinic aesthetic.\n"
            "Title: 'Kidney Stones — The 4-Day Coconut Flush'.\n"
            "Three panels:\n"
            "1) WHY — kidney icon; text: heat + dampness condense; blocked water pathways.\n"
            "2) 4-DAY FLUSH — coconut + lemon icons; text: fresh coconut water + lemon each AM, 2–3L warm water daily.\n"
            "3) PREVENT — text: less salt + oxalate-heavy foods, stay hydrated, warm not iced drinks.\n"
            "Footer: 'Severe pain, fever, or blood in urine? Go to a doctor immediately.' Flat icons only."
        ),
        "second_dm": (
            "Here's your stone-flush guide — large stones need a doctor, so please get them checked 🩺\n\n"
            "Want the prevention food list so they don't come back? Reply 'prevent'."
        ),
    },

    # ───────────────────────── 9. Headache Relief 15s ─────────────────────────
    {
        "title": "Headache Relief in 15 Seconds (Eyebrow Acupressure)",
        "master_script": [
            "Press firmly under your eyebrow ridge right now. You may ease your headache in under fifteen seconds.",
            "In Chinese medicine most tension headaches come from stuck liver energy and tight muscles pulling at the head and the eyes.",
            "Try this. Find the small notch under the inner eyebrow and press up gently for fifteen seconds then release. It may relax the area and ease the pain.",
            "Comment head and I will send you my full headache pressure point map.",
        ],
        "shots": [
            {"n": 1, "secs": 10, "beat": "Hook",
             "visual": "Doctor presses his own inner eyebrow with a thumb closes his eyes and exhales with relief, then opens eyes to camera. Macro insert of a thumb finding the notch under the brow. Back to doctor nodding.",
             "voice": "Press firmly under your eyebrow ridge right now. You may ease your headache in under fifteen seconds.",
             "caption": "Headache gone in 15 seconds"},
            {"n": 2, "secs": 12, "beat": "Root Cause",
             "visual": "Doctor mimes tension by tightening his hands near his temples, then points to the liver area on a body chart. Cutaway insert of a tight knotted rope slowly loosening.",
             "voice": "In Chinese medicine most tension headaches come from stuck liver energy and tight muscles pulling at the head and the eyes.",
             "caption": "肝鬱 + 緊張"},
            {"n": 3, "secs": 12, "beat": "The Fix",
             "visual": "Doctor demonstrates slowly. He places both thumbs in the notches under the inner eyebrows presses upward holds and counts then releases with a calm exhale. Close insert of the press point marked on the brow.",
             "voice": "Try this. Find the small notch under the inner eyebrow and press up gently for fifteen seconds then release. It may relax the area and ease the pain.",
             "caption": "攢竹穴 · press 15s"},
            {"n": 4, "secs": 8, "beat": "CTA",
             "visual": "Doctor looks into camera relaxed and reassuring.",
             "voice": "Comment head and I will send you my full headache pressure point map.",
             "caption": "Comment 👇 head"},
        ],
        "first_dm": (
            "Hey! That brow point gives fast relief for tension headaches 🧠\n\n"
            "Quick check so I send the right map — are your headaches more at the temples, the forehead, or the back of the head?"
        ),
        "infographic_brief": (
            "Vertical infographic, 4:5 ratio, warm TCM clinic aesthetic.\n"
            "Title: 'Headache Relief — 3 Pressure Points'.\n"
            "Three panels, each a simple face/hand icon with the point marked:\n"
            "1) BROW NOTCH (Zanzhu) — under inner eyebrow; press up 15s.\n"
            "2) TEMPLE (Taiyang) — small circles 15s for side headaches.\n"
            "3) HAND WEBBING (Hegu) — between thumb + index, press 30s for overall relief.\n"
            "Footer: 'Sudden severe or unusual headache? Seek care immediately.' Flat icons only."
        ),
        "second_dm": (
            "Here's your pressure-point map — screenshot it for the next time one hits 📍\n\n"
            "Want the liver-calming habits that stop tension headaches forming? Reply 'liver'."
        ),
    },

    # ───────────────────────── 10. Phlegm / Mucus ─────────────────────────
    {
        "title": "Phlegm / Mucus (TCM Root Cause)",
        "master_script": [
            "That thick phlegm can start clearing overnight. The mucus is not the problem. It is a signal.",
            "In Chinese medicine phlegm is made by a weak and damp spleen. When digestion is sluggish it turns food into dampness that pools as mucus.",
            "Try this. Sip warm water with fresh ginger and a slice of tangerine peel through the day. It may warm the spleen and help thin the phlegm.",
            "Comment phlegm and I will send you my full lung and spleen clearing protocol.",
        ],
        "shots": [
            {"n": 1, "secs": 10, "beat": "Hook",
             "visual": "Doctor holds up a knob of fresh ginger and a piece of dried tangerine peel toward camera. Macro insert of ginger being sliced, then steam rising from a cup. Back to doctor nodding.",
             "voice": "That thick phlegm can start clearing overnight. The mucus is not the problem. It is a signal.",
             "caption": "Clear phlegm overnight"},
            {"n": 2, "secs": 12, "beat": "Root Cause",
             "visual": "Doctor points to the stomach and spleen area on a body chart, then makes a sluggish swirling motion to show dampness pooling. Cutaway insert of thick cloudy liquid versus clear flowing water.",
             "voice": "In Chinese medicine phlegm is made by a weak and damp spleen. When digestion is sluggish it turns food into dampness that pools as mucus.",
             "caption": "脾為生痰之源"},
            {"n": 3, "secs": 12, "beat": "The Fix",
             "visual": "Doctor drops ginger slices and tangerine peel into a cup pours hot water stirs and sips with a satisfied breath. Overhead insert of ginger peel and the warm cup.",
             "voice": "Try this. Sip warm water with fresh ginger and a slice of tangerine peel through the day. It may warm the spleen and help thin the phlegm.",
             "caption": "Ginger + tangerine peel tea"},
            {"n": 4, "secs": 8, "beat": "CTA",
             "visual": "Doctor looks into camera calm and reassuring.",
             "voice": "Comment phlegm and I will send you my full lung and spleen clearing protocol.",
             "caption": "Comment 👇 phlegm"},
        ],
        "first_dm": (
            "Hey! Clearing phlegm is really about warming the spleen 🌿\n\n"
            "Quick check so I tailor it — is your phlegm more clear/white, or thick yellow-green?"
        ),
        "infographic_brief": (
            "Vertical infographic, 4:5 ratio, warm TCM clinic aesthetic.\n"
            "Title: 'Phlegm — Fix the Spleen, Not Just the Cough'.\n"
            "Three panels:\n"
            "1) WHY — spleen icon; text: weak damp spleen turns food into mucus.\n"
            "2) DAILY FIX — ginger + peel icons; text: warm ginger + tangerine-peel tea sipped through the day.\n"
            "3) AVOID — text: cut cold drinks, dairy, sugar and raw food that feed dampness.\n"
            "Footer: 'Phlegm with blood or fever? See a doctor.' Flat icons only."
        ),
        "second_dm": (
            "Here's your phlegm-clearing guide — warm everything, nothing iced 🍵\n\n"
            "Want the full anti-damp food list that stops it returning? Reply 'damp'."
        ),
    },

    # ───────────────────────── 11. Magnesium Deficiency ─────────────────────────
    {
        "title": "Magnesium Deficiency (Sleep + Weight + Movement)",
        "master_script": [
            "To feel rested lighter and calmer you may only be missing one mineral. Magnesium.",
            "Most people run low on magnesium. In Chinese medicine that shows up as restless sleep tight muscles and a body that cannot relax or let go of water.",
            "Try this. Eat more pumpkin seeds leafy greens and a square of dark chocolate and soak your feet in epsom salt at night. It may calm the body and improve sleep.",
            "Comment magnesium and I will send you my full magnesium and sleep guide.",
        ],
        "shots": [
            {"n": 1, "secs": 10, "beat": "Hook",
             "visual": "Doctor holds up a small bowl of pumpkin seeds and a piece of dark chocolate, warm reassuring smile. Macro insert of pumpkin seeds and leafy greens. Back to doctor raising one finger.",
             "voice": "To feel rested lighter and calmer you may only be missing one mineral. Magnesium.",
             "caption": "One mineral changes everything"},
            {"n": 2, "secs": 12, "beat": "Root Cause",
             "visual": "Doctor mimes tossing and turning sleep then tense shoulders, pointing to a body chart. Cutaway insert of a tight spring versus a relaxed loose coil.",
             "voice": "Most people run low on magnesium. In Chinese medicine that shows up as restless sleep tight muscles and a body that cannot relax or let go of water.",
             "caption": "鎂不足 · 緊張 · 水腫"},
            {"n": 3, "secs": 12, "beat": "The Fix",
             "visual": "Doctor lays out pumpkin seeds leafy greens and dark chocolate on the table then mimes pouring epsom salt into a foot basin. Overhead insert of the foods and the epsom basin.",
             "voice": "Try this. Eat more pumpkin seeds leafy greens and a square of dark chocolate and soak your feet in epsom salt at night. It may calm the body and improve sleep.",
             "caption": "Seeds + greens + epsom soak"},
            {"n": 4, "secs": 8, "beat": "CTA",
             "visual": "Doctor faces camera with a calm gentle nod.",
             "voice": "Comment magnesium and I will send you my full magnesium and sleep guide.",
             "caption": "Comment 👇 magnesium"},
        ],
        "first_dm": (
            "Hey! Magnesium is the calm-down mineral most people are short on 🌙\n\n"
            "Quick q so I focus the plan — is your main issue sleep, muscle cramps, or puffiness/water retention?"
        ),
        "infographic_brief": (
            "Vertical infographic, 4:5 ratio, warm TCM clinic aesthetic.\n"
            "Title: 'Magnesium — Sleep, Calm, Less Puffiness'.\n"
            "Three panels:\n"
            "1) SIGNS — body icon; text: restless sleep, cramps, tension, water retention.\n"
            "2) EAT — seed + leaf + cacao icons; text: pumpkin seeds, leafy greens, dark chocolate, beans.\n"
            "3) ABSORB — foot-basin icon; text: epsom-salt foot soak at night, less coffee + sugar that deplete it.\n"
            "Footer: 'Kidney issues? Check with a doctor before supplementing.' Flat icons only."
        ),
        "second_dm": (
            "Here's your magnesium guide — the epsom soak at night is a game-changer for sleep 🛁\n\n"
            "Want the full evening wind-down routine? Reply 'sleep'."
        ),
    },

    # ───────────────────────── 12. Tongue Diagnosis ─────────────────────────
    {
        "title": "Tongue Diagnosis for Gut Health",
        "master_script": [
            "Stick out your tongue in the mirror right now. It is reading your gut like a report card.",
            "In Chinese medicine the tongue mirrors digestion. A thick white coat means cold and damp. Teeth marks on the edges mean a tired spleen. A red tip means heat and stress.",
            "If you see a thick coat or teeth marks start here. Warm cooked food smaller meals and less raw and cold. It may lighten the coat within days.",
            "Comment tongue and I will send you my full tongue map and gut reset.",
        ],
        "shots": [
            {"n": 1, "secs": 10, "beat": "Hook",
             "visual": "Doctor points to his own tongue in a small hand mirror toward camera with a teaching expression. Macro insert of a tongue with a thick white coating and scalloped edges. Back to doctor raising a finger.",
             "voice": "Stick out your tongue in the mirror right now. It is reading your gut like a report card.",
             "caption": "Your tongue = a gut report card"},
            {"n": 2, "secs": 12, "beat": "Root Cause",
             "visual": "Doctor holds up three diagram cards of tongues, pointing to white coat, teeth marks, then red tip. Cutaway inserts of each tongue type close up.",
             "voice": "In Chinese medicine the tongue mirrors digestion. A thick white coat means cold and damp. Teeth marks on the edges mean a tired spleen. A red tip means heat and stress.",
             "caption": "白苔 · 齒痕 · 紅尖"},
            {"n": 3, "secs": 12, "beat": "The Fix",
             "visual": "Doctor gestures to a bowl of warm porridge and waves away a plate of cold salad and ice. Overhead insert of warm cooked food versus cold raw food.",
             "voice": "If you see a thick coat or teeth marks start here. Warm cooked food smaller meals and less raw and cold. It may lighten the coat within days.",
             "caption": "Warm cooked food, less raw/cold"},
            {"n": 4, "secs": 8, "beat": "CTA",
             "visual": "Doctor looks into camera friendly and direct.",
             "voice": "Comment tongue and I will send you my full tongue map and gut reset.",
             "caption": "Comment 👇 tongue"},
        ],
        "first_dm": (
            "Hey! Your tongue tells me a lot about your digestion 👅\n\n"
            "Quick check so I read it right — is your coating more thick-white, or is the tip quite red?"
        ),
        "infographic_brief": (
            "Vertical infographic, 4:5 ratio, warm TCM clinic aesthetic.\n"
            "Title: 'Read Your Tongue — Gut Health Map'.\n"
            "Three panels, each a clean tongue illustration:\n"
            "1) THICK WHITE COAT — cold + dampness; warm food, less raw/cold.\n"
            "2) TEETH MARKS ON EDGES — tired spleen; smaller warm meals, cooked grains.\n"
            "3) RED TIP — heat + stress; calm the mind, less spicy + alcohol.\n"
            "Footer: 'Persistent purple or cracked tongue? See a practitioner.' Flat illustrations only."
        ),
        "second_dm": (
            "Here's your tongue map — check it each morning before brushing for the clearest read 👅\n\n"
            "Want the gut-reset meal plan that matches your tongue type? Reply 'gut'."
        ),
    },

    # ───────────────────────── 13. Lower Back + Hip Pain = Kidneys ─────────────────────────
    {
        "title": "Lower Back + Hip Pain = Kidneys Crying",
        "master_script": [
            "That ache in your lower back and hips may not be sciatica. It could be your kidneys asking for help.",
            "In Chinese medicine the lower back is the home of the kidneys. When kidney energy runs cold and weak the back and hips grow stiff and sore.",
            "Try this. Warm the lower back with a heat pad each night and rub in a little ginger oil over the kidney area. It may warm the region and ease the ache.",
            "Comment kidney and I will send you my full kidney warming and back protocol.",
        ],
        "shots": [
            {"n": 1, "secs": 10, "beat": "Hook",
             "visual": "Doctor places a hand on his own lower back with a knowing wince then shakes his head as if to say it is not what you think. Cutaway insert of hands cupping the lower-back kidney area. Back to doctor leaning in.",
             "voice": "That ache in your lower back and hips may not be sciatica. It could be your kidneys asking for help.",
             "caption": "Back pain = kidneys crying"},
            {"n": 2, "secs": 12, "beat": "Root Cause",
             "visual": "Doctor points to the kidney region on a body chart and mimes cold seeping into the lower back. Cutaway insert of a warm glow spreading across a cold blue lower back.",
             "voice": "In Chinese medicine the lower back is the home of the kidneys. When kidney energy runs cold and weak the back and hips grow stiff and sore.",
             "caption": "腰為腎之府 · 腎陽虛"},
            {"n": 3, "secs": 12, "beat": "The Fix",
             "visual": "Doctor presses a heat pad to his lower back then warms ginger oil between his palms and rubs the kidney area. Overhead insert of heat pad and ginger oil bottle.",
             "voice": "Try this. Warm the lower back with a heat pad each night and rub in a little ginger oil over the kidney area. It may warm the region and ease the ache.",
             "caption": "Heat pad + ginger oil, nightly"},
            {"n": 4, "secs": 8, "beat": "CTA",
             "visual": "Doctor faces camera steady and confident.",
             "voice": "Comment kidney and I will send you my full kidney warming and back protocol.",
             "caption": "Comment 👇 kidney"},
        ],
        "first_dm": (
            "Hey! Cold-type lower-back pain responds beautifully to warmth 🔥\n\n"
            "Quick q so I send the right plan — is your ache worse in cold weather and better with heat?"
        ),
        "infographic_brief": (
            "Vertical infographic, 4:5 ratio, warm TCM clinic aesthetic.\n"
            "Title: 'Lower Back + Hip Pain — The Kidney Link'.\n"
            "Three panels:\n"
            "1) WHY — lower-back/kidney icon; text: the low back houses the kidneys; cold + weakness = stiffness.\n"
            "2) NIGHTLY FIX — heat-pad + oil icons; text: warm the kidney area, ginger-oil rub, keep the waist covered.\n"
            "3) STRENGTHEN — text: black beans, walnuts, gentle waist twists, avoid sitting on cold surfaces.\n"
            "Footer: 'Numbness, leg weakness, or bladder changes? See a doctor.' Flat icons only."
        ),
        "second_dm": (
            "Here's your kidney-back guide — never let the lower back get cold 🔥\n\n"
            "Want the kidney-strengthening foods + gentle moves? Reply 'strong'."
        ),
    },

    # ───────────────────────── 14. Why Nobody in China Walks Barefoot ─────────────────────────
    {
        "title": "Why Nobody in China Walks Barefoot",
        "master_script": [
            "Do you know why so few people in China walk barefoot at home? It is not about the floor.",
            "In Chinese medicine cold enters the body through the soles of the feet. From there it travels up and settles in the joints the womb and the stomach.",
            "Try this. Keep warm socks or slippers on at home and soak your feet in warm water before bed. It may keep cold out and protect your core warmth.",
            "Comment cold and I will send you my full keep warm and protect your qi guide.",
        ],
        "shots": [
            {"n": 1, "secs": 10, "beat": "Hook",
             "visual": "Doctor points down at his own slippered feet then wags a finger at a pair of bare feet on a cold tiled floor. Cutaway insert of bare feet on cold tiles. Back to doctor shaking his head.",
             "voice": "Do you know why so few people in China walk barefoot at home? It is not about the floor.",
             "caption": "Why we never go barefoot"},
            {"n": 2, "secs": 12, "beat": "Root Cause",
             "visual": "Doctor traces cold rising from the soles up the legs into the belly on a body chart. Cutaway insert of a blue cold mist creeping up from the floor.",
             "voice": "In Chinese medicine cold enters the body through the soles of the feet. From there it travels up and settles in the joints the womb and the stomach.",
             "caption": "寒從腳起"},
            {"n": 3, "secs": 12, "beat": "The Fix",
             "visual": "Doctor pulls on warm socks and slippers then lowers his feet into a basin of warm water with a relieved smile. Overhead insert of warm socks slippers and foot basin.",
             "voice": "Try this. Keep warm socks or slippers on at home and soak your feet in warm water before bed. It may keep cold out and protect your core warmth.",
             "caption": "Warm socks + nightly foot soak"},
            {"n": 4, "secs": 8, "beat": "CTA",
             "visual": "Doctor looks into camera warm and caring.",
             "voice": "Comment cold and I will send you my full keep warm and protect your qi guide.",
             "caption": "Comment 👇 cold"},
        ],
        "first_dm": (
            "Hey! Keeping the feet warm protects your whole core 🧦\n\n"
            "Quick check — do you often have cold hands and feet, or feel the cold more than others around you?"
        ),
        "infographic_brief": (
            "Vertical infographic, 4:5 ratio, warm TCM clinic aesthetic.\n"
            "Title: 'Cold Enters Through the Feet'.\n"
            "Three panels:\n"
            "1) WHY — feet + rising-cold icon; text: cold enters the soles and settles in joints, womb, stomach.\n"
            "2) PROTECT — sock + basin icons; text: warm socks/slippers indoors, nightly warm foot soak.\n"
            "3) WARM CORE — text: warm cooked food, ginger tea, keep the waist + belly covered.\n"
            "Footer: 'Persistent coldness or numbness? Check circulation with a doctor.' Flat icons only."
        ),
        "second_dm": (
            "Here's your stay-warm guide — cold feet at night undo a lot of good work 🧦\n\n"
            "Want my full warming routine for cold-type bodies? Reply 'warm'."
        ),
    },

    # ───────────────────────── 15. Bladder Weakness ─────────────────────────
    {
        "title": "Bladder Weakness / Urinary Incontinence",
        "master_script": [
            "If you leak a little when you laugh cough or walk this is not just aging.",
            "In Chinese medicine the bladder is held by kidney energy. When kidney qi weakens it can no longer hold and small leaks begin.",
            "Try this. Practice gentle hold and release squeezes a few times a day and keep your lower belly and back warm. It may help rebuild the holding strength.",
            "Comment bladder and I will send you my full bladder and kidney strengthening plan.",
        ],
        "shots": [
            {"n": 1, "secs": 10, "beat": "Hook",
             "visual": "Doctor gives a gentle empathetic look to camera and mimes a small surprised laugh-then-leak reaction with a reassuring shake of the head. Cutaway insert of hands resting protectively over the lower belly.",
             "voice": "If you leak a little when you laugh cough or walk this is not just aging.",
             "caption": "Leaks aren't just aging"},
            {"n": 2, "secs": 12, "beat": "Root Cause",
             "visual": "Doctor points to the kidney and bladder on a body chart and mimes a loosening grip with his hand. Cutaway insert of a hand loosening its hold on a small bag of water.",
             "voice": "In Chinese medicine the bladder is held by kidney energy. When kidney qi weakens it can no longer hold and small leaks begin.",
             "caption": "腎氣不固 · 膀胱失約"},
            {"n": 3, "secs": 12, "beat": "The Fix",
             "visual": "Doctor demonstrates a calm breathing-and-squeeze exercise with a hand on the lower belly, then tucks a warm wrap around the waist. Overhead insert of a warm wrap over the lower abdomen.",
             "voice": "Try this. Practice gentle hold and release squeezes a few times a day and keep your lower belly and back warm. It may help rebuild the holding strength.",
             "caption": "Hold-release squeezes + keep warm"},
            {"n": 4, "secs": 8, "beat": "CTA",
             "visual": "Doctor faces camera kind and reassuring.",
             "voice": "Comment bladder and I will send you my full bladder and kidney strengthening plan.",
             "caption": "Comment 👇 bladder"},
        ],
        "first_dm": (
            "Hey! Bladder control is really about kidney strength in TCM 🌿\n\n"
            "Quick q so I tailor it — are the leaks mainly with laughing/coughing, or do you also feel urgency and frequency?"
        ),
        "infographic_brief": (
            "Vertical infographic, 4:5 ratio, warm TCM clinic aesthetic.\n"
            "Title: 'Bladder Weakness — Strengthen Kidney Qi'.\n"
            "Three panels:\n"
            "1) WHY — kidney + bladder icon; text: weak kidney qi can't hold the bladder.\n"
            "2) REBUILD — breathing icon; text: gentle hold-release squeezes daily, keep belly + back warm.\n"
            "3) SUPPORT — text: black beans, walnuts, yam; avoid too much cold + caffeine.\n"
            "Footer: 'Sudden onset, pain, or blood? See a doctor.' Flat icons only."
        ),
        "second_dm": (
            "Here's your bladder-strength guide — consistency with the squeezes is everything 💪\n\n"
            "Want the kidney-qi food list that supports it? Reply 'kidney'."
        ),
    },

    # ───────────────────────── 16. Urine Color Diagnosis ─────────────────────────
    {
        "title": "Urine Color Diagnosis (7 Colors, 6 Are Danger)",
        "master_script": [
            "Go to the bathroom and look at your urine. Its color is telling you something important right now.",
            "In Chinese medicine urine reflects your inner heat cold and hydration. Pale and clear can mean cold. Dark yellow means heat. Cloudy means dampness.",
            "Aim for a light straw color. Drink enough warm water through the day and ease off cold and greasy food. It may bring the color back to healthy.",
            "Comment urine and I will send you my full urine color chart and meaning.",
        ],
        "shots": [
            {"n": 1, "secs": 10, "beat": "Hook",
             "visual": "Doctor holds up a chart of seven graded urine-color swatches from pale to dark, pointing with a serious teaching expression. Cutaway insert of the color strip close up. Back to doctor raising an eyebrow.",
             "voice": "Go to the bathroom and look at your urine. Its color is telling you something important right now.",
             "caption": "7 colors — what yours means"},
            {"n": 2, "secs": 12, "beat": "Root Cause",
             "visual": "Doctor points across the color chart explaining pale then dark then cloudy, with matching hand gestures for cold heat and damp. Cutaway inserts of clear, dark, and cloudy glasses of water.",
             "voice": "In Chinese medicine urine reflects your inner heat cold and hydration. Pale and clear can mean cold. Dark yellow means heat. Cloudy means dampness.",
             "caption": "清=寒 · 黃=熱 · 濁=濕"},
            {"n": 3, "secs": 12, "beat": "The Fix",
             "visual": "Doctor points to the ideal straw-colored swatch then lifts a glass of warm water and gestures away from fried food. Overhead insert of a glass of warm water beside the target color.",
             "voice": "Aim for a light straw color. Drink enough warm water through the day and ease off cold and greasy food. It may bring the color back to healthy.",
             "caption": "Aim for light straw color"},
            {"n": 4, "secs": 8, "beat": "CTA",
             "visual": "Doctor looks into camera direct and helpful.",
             "voice": "Comment urine and I will send you my full urine color chart and meaning.",
             "caption": "Comment 👇 urine"},
        ],
        "first_dm": (
            "Hey! Urine color is a fast daily health read 🚽\n\n"
            "Quick check so I read it right — is yours more pale-and-clear, dark-yellow, or cloudy?"
        ),
        "infographic_brief": (
            "Vertical infographic, 4:5 ratio, warm TCM clinic aesthetic.\n"
            "Title: 'Urine Color — What Your Body Is Saying'.\n"
            "A vertical strip of 7 color swatches, each labeled:\n"
            "Clear → too cold / over-hydrated · Pale straw → healthy · Yellow → mild heat/dehydration · "
            "Dark amber → heat, drink water · Cloudy → dampness · Pink/red → see a doctor · Brown → see a doctor.\n"
            "Footer: 'Red, brown, or persistent changes? Seek medical care.' Clean swatches + labels only."
        ),
        "second_dm": (
            "Here's your urine color chart — screenshot it for the bathroom 🚽\n\n"
            "Want the hydration + food plan to keep yours in the healthy zone? Reply 'water'."
        ),
    },

    # ───────────────────────── 17. High Blood Sugar Signs ─────────────────────────
    {
        "title": "High Blood Sugar Signs (Swollen Feet, Dark Neck, Bags)",
        "master_script": [
            "Swollen feet. Bags under the eyes that never leave. A dark velvety patch on the neck. Together they can warn of high blood sugar.",
            "In Chinese medicine this is dampness and heat from an overloaded spleen struggling to move sugar and fluid through the body.",
            "Try this. Start the day with cinnamon water and walk for ten minutes after meals. It may help steady your sugar and reduce the puffiness.",
            "Comment sugar and I will send you my full blood sugar balancing protocol.",
        ],
        "shots": [
            {"n": 1, "secs": 10, "beat": "Hook",
             "visual": "Doctor points in turn to a swollen foot, under-eye bags, and a dark neck patch on three diagram cards, with a concerned teaching look. Cutaway inserts of each sign close up. Back to doctor holding up three fingers.",
             "voice": "Swollen feet. Bags under the eyes that never leave. A dark velvety patch on the neck. Together they can warn of high blood sugar.",
             "caption": "3 signs of high blood sugar"},
            {"n": 2, "secs": 12, "beat": "Root Cause",
             "visual": "Doctor points to the spleen on a body chart and mimes a heavy sluggish churning motion. Cutaway insert of thick syrup moving slowly versus water moving freely.",
             "voice": "In Chinese medicine this is dampness and heat from an overloaded spleen struggling to move sugar and fluid through the body.",
             "caption": "脾虛濕熱"},
            {"n": 3, "secs": 12, "beat": "The Fix",
             "visual": "Doctor stirs cinnamon into a glass of warm water and drinks then mimes a brisk short walk. Overhead insert of cinnamon stick water and a clock showing ten minutes.",
             "voice": "Try this. Start the day with cinnamon water and walk for ten minutes after meals. It may help steady your sugar and reduce the puffiness.",
             "caption": "Cinnamon water + walk after meals"},
            {"n": 4, "secs": 8, "beat": "CTA",
             "visual": "Doctor faces camera serious and caring.",
             "voice": "Comment sugar and I will send you my full blood sugar balancing protocol.",
             "caption": "Comment 👇 sugar"},
        ],
        "first_dm": (
            "Hey! Those three signs together are worth taking seriously 🩺\n\n"
            "Quick q so I send the right plan — have you had your blood sugar checked recently, or not in a while?"
        ),
        "infographic_brief": (
            "Vertical infographic, 4:5 ratio, warm TCM clinic aesthetic.\n"
            "Title: 'High Blood Sugar — 3 Warning Signs'.\n"
            "Three sign panels: swollen feet · dark neck patch (acanthosis) · persistent eye bags.\n"
            "Then a FIX strip: cinnamon water in the morning · 10-min walk after meals · cut refined sugar + white carbs.\n"
            "Footer: 'These are warning signs — please get your blood sugar tested by a doctor.' Flat icons only."
        ),
        "second_dm": (
            "Here's your blood-sugar guide — and please do get a proper test, this one matters 🩺\n\n"
            "Want the full sugar-balancing food list? Reply 'balance'."
        ),
    },

    # ───────────────────────── 18. Apple PLU Sticker ─────────────────────────
    {
        "title": "Apple PLU Sticker Warning (GMO vs Conventional)",
        "master_script": [
            "Never buy an apple without checking the little sticker first. That code tells you how it was grown.",
            "The number on the sticker is a clue. A five digit code starting with eight can mean genetically modified. A code starting with nine means organically grown.",
            "Try this. Choose codes that start with nine when you can and always wash your fruit in water with a little baking soda. It may reduce surface residue.",
            "Comment apple and I will send you my full clean produce shopping guide.",
        ],
        "shots": [
            {"n": 1, "secs": 10, "beat": "Hook",
             "visual": "Doctor holds an apple close to camera and taps the small PLU sticker with a knowing look. Macro insert of the PLU code sticker on the apple skin. Back to doctor raising an eyebrow.",
             "voice": "Never buy an apple without checking the little sticker first. That code tells you how it was grown.",
             "caption": "Check the sticker first"},
            {"n": 2, "secs": 12, "beat": "Decode",
             "visual": "Doctor holds up three cards showing example codes — a 4 digit, an 8 prefix, and a 9 prefix — pointing to each. Cutaway inserts of each sticker code close up.",
             "voice": "The number on the sticker is a clue. A five digit code starting with eight can mean genetically modified. A code starting with nine means organically grown.",
             "caption": "9 = organic · 8 = GMO"},
            {"n": 3, "secs": 12, "beat": "The Fix",
             "visual": "Doctor drops apples into a bowl of water sprinkles baking soda and swishes them then lifts one out clean. Overhead insert of apples in the baking-soda water bath.",
             "voice": "Try this. Choose codes that start with nine when you can and always wash your fruit in water with a little baking soda. It may reduce surface residue.",
             "caption": "Pick 9-codes + baking-soda wash"},
            {"n": 4, "secs": 8, "beat": "CTA",
             "visual": "Doctor looks into camera helpful and direct.",
             "voice": "Comment apple and I will send you my full clean produce shopping guide.",
             "caption": "Comment 👇 apple"},
        ],
        "first_dm": (
            "Hey! Those little PLU codes are a handy shopping shortcut 🍎\n\n"
            "Quick q — do you mostly shop supermarket produce, or local/farmers-market when you can?"
        ),
        "infographic_brief": (
            "Vertical infographic, 4:5 ratio, warm TCM clinic aesthetic.\n"
            "Title: 'Decode the Fruit Sticker'.\n"
            "Three code panels with a sample sticker each:\n"
            "1) 4 DIGITS (e.g. 4131) — conventionally grown.\n"
            "2) STARTS WITH 9 (5 digits) — organically grown — best pick.\n"
            "3) STARTS WITH 8 — flagged as GMO (rarely used, but know it).\n"
            "Bottom strip: 'Always wash: water + 1 tsp baking soda, 2 min, rinse.'\n"
            "Footer: 'Codes are voluntary — washing matters most.' Flat icons only."
        ),
        "second_dm": (
            "Here's your produce-code guide — keep it in your notes for grocery runs 🍎\n\n"
            "Want my full clean-eating shopping list? Reply 'clean'."
        ),
    },

    # ───────────────────────── 19. Swollen + Cracked Feet ─────────────────────────
    {
        "title": "Swollen + Cracked Feet (Internal Root Cause)",
        "master_script": [
            "If your feet look like this at the end of the day swollen heavy and cracked this is not just tired feet.",
            "In Chinese medicine the feet are the lowest point where dampness pools. Weak spleen and kidney let fluid sink and stagnate down there.",
            "Try this. Soak your feet in warm water with ginger and salt at night then elevate them on a pillow. It may move the fluid and ease the swelling.",
            "Comment feet and I will send you my full fluid draining and foot care protocol.",
        ],
        "shots": [
            {"n": 1, "secs": 10, "beat": "Hook",
             "visual": "Doctor gestures to a pair of swollen aching feet on a stool with a concerned look. Cutaway insert of a finger pressing a swollen ankle leaving a dent. Back to doctor shaking his head gently.",
             "voice": "If your feet look like this at the end of the day swollen heavy and cracked this is not just tired feet.",
             "caption": "Swollen feet = inside signal"},
            {"n": 2, "secs": 12, "beat": "Root Cause",
             "visual": "Doctor traces fluid sinking from the belly down to the feet on a body chart. Cutaway insert of water pooling at the lowest point of a tilted tray.",
             "voice": "In Chinese medicine the feet are the lowest point where dampness pools. Weak spleen and kidney let fluid sink and stagnate down there.",
             "caption": "脾腎虛 · 水濕下注"},
            {"n": 3, "secs": 12, "beat": "The Fix",
             "visual": "Doctor lowers his feet into a warm basin with ginger and salt then lies back and rests his feet up on a pillow. Overhead insert of the ginger-salt foot basin and a propped pillow.",
             "voice": "Try this. Soak your feet in warm water with ginger and salt at night then elevate them on a pillow. It may move the fluid and ease the swelling.",
             "caption": "Ginger-salt soak + elevate feet"},
            {"n": 4, "secs": 8, "beat": "CTA",
             "visual": "Doctor faces camera calm and reassuring.",
             "voice": "Comment feet and I will send you my full fluid draining and foot care protocol.",
             "caption": "Comment 👇 feet"},
        ],
        "first_dm": (
            "Hey! End-of-day foot swelling usually points to fluid + spleen 🦶\n\n"
            "Quick check so I tailor it — does the swelling go down overnight, or is it there in the morning too?"
        ),
        "infographic_brief": (
            "Vertical infographic, 4:5 ratio, warm TCM clinic aesthetic.\n"
            "Title: 'Swollen Feet — Drain the Dampness'.\n"
            "Three panels:\n"
            "1) WHY — feet icon; text: weak spleen/kidney let fluid sink + pool in the feet.\n"
            "2) NIGHTLY FIX — basin + pillow icons; text: warm ginger-salt soak, then elevate feet 15 min.\n"
            "3) MOVE FLUID — text: reduce salt, gentle walking, red bean + barley water.\n"
            "Footer: 'Sudden, one-sided, or with breathlessness? See a doctor urgently.' Flat icons only."
        ),
        "second_dm": (
            "Here's your foot-swelling guide — elevating after the soak makes a big difference 🦶\n\n"
            "Want the diuretic-food list that drains dampness? Reply 'drain'."
        ),
    },

    # ───────────────────────── 20. Sock Marks / Lymphatic Edema ─────────────────────────
    {
        "title": "Sock Marks / Lymphatic Edema",
        "master_script": [
            "Your socks should not be leaving deep marks like this every single day. That ring is a message.",
            "In Chinese medicine these marks mean dampness and stagnant fluid that the spleen and lymph are too sluggish to move.",
            "Try this. Each morning dry brush your legs upward toward the heart and do a few ankle pumps. It may wake up the flow and soften the marks.",
            "Comment socks and I will send you my full lymph and fluid moving routine.",
        ],
        "shots": [
            {"n": 1, "secs": 10, "beat": "Hook",
             "visual": "Doctor peels back a sock to reveal a deep red indentation around the ankle and raises an eyebrow at camera. Macro insert of the pressed ring mark on the skin. Back to doctor pointing at it.",
             "voice": "Your socks should not be leaving deep marks like this every single day. That ring is a message.",
             "caption": "Deep sock marks = a warning"},
            {"n": 2, "secs": 12, "beat": "Root Cause",
             "visual": "Doctor points to the legs and lower body on a body chart and mimes a slow heavy drag to show stagnant fluid. Cutaway insert of still swampy water versus a clear flowing stream.",
             "voice": "In Chinese medicine these marks mean dampness and stagnant fluid that the spleen and lymph are too sluggish to move.",
             "caption": "脾虛濕停 · 淋巴瘀滯"},
            {"n": 3, "secs": 12, "beat": "The Fix",
             "visual": "Doctor dry brushes his lower leg in upward strokes toward the heart then pumps his ankle up and down. Overhead insert of a dry brush and bare feet pumping.",
             "voice": "Try this. Each morning dry brush your legs upward toward the heart and do a few ankle pumps. It may wake up the flow and soften the marks.",
             "caption": "Dry brush up + ankle pumps"},
            {"n": 4, "secs": 8, "beat": "CTA",
             "visual": "Doctor looks into camera friendly and encouraging.",
             "voice": "Comment socks and I will send you my full lymph and fluid moving routine.",
             "caption": "Comment 👇 socks"},
        ],
        "first_dm": (
            "Hey! Deep daily sock marks point to sluggish lymph + dampness 🌿\n\n"
            "Quick q so I tailor it — are the marks on both legs equally, or worse on one side?"
        ),
        "infographic_brief": (
            "Vertical infographic, 4:5 ratio, warm TCM clinic aesthetic.\n"
            "Title: 'Sock Marks — Get the Fluid Moving'.\n"
            "Three panels:\n"
            "1) WHY — ankle-ring icon; text: dampness + sluggish lymph from a weak spleen.\n"
            "2) MORNING FIX — dry-brush + ankle-pump icons; text: brush legs upward to the heart, pump ankles.\n"
            "3) KEEP FLOWING — text: move every hour, reduce salt, red bean + barley water.\n"
            "Footer: 'Sudden one-sided swelling? Rule out a clot with a doctor.' Flat icons only."
        ),
        "second_dm": (
            "Here's your lymph-moving routine — do the dry brushing before your shower ✨\n\n"
            "Want the anti-damp food list that keeps fluid moving? Reply 'damp'."
        ),
    },

    # ───────────────────────── 21. Buffalo Hump / Cortisol ─────────────────────────
    {
        "title": "Buffalo Hump / Cortisol (TCM Root)",
        "master_script": [
            "If a hump is forming at the back of your neck this is not bad posture. It can be a sign of high stress hormones.",
            "In Chinese medicine this is phlegm and dampness piling up where chronic stress and a tired spleen meet at the base of the neck.",
            "Try this. Each evening do slow neck rolls and shoulder circles and press the point at the base of the skull. It may ease tension and reduce the buildup over time.",
            "Comment hump and I will send you my full stress and neck release protocol.",
        ],
        "shots": [
            {"n": 1, "secs": 10, "beat": "Hook",
             "visual": "Doctor gestures to the base of the neck on a side-profile diagram showing a soft hump with a concerned look. Cutaway insert of the upper-back neck area close up. Back to doctor shaking his head.",
             "voice": "If a hump is forming at the back of your neck this is not bad posture. It can be a sign of high stress hormones.",
             "caption": "Neck hump = cortisol, not posture"},
            {"n": 2, "secs": 12, "beat": "Root Cause",
             "visual": "Doctor points to the spleen then to the neck base on a body chart and mimes piling up with his hands. Cutaway insert of soft material slowly accumulating in one spot.",
             "voice": "In Chinese medicine this is phlegm and dampness piling up where chronic stress and a tired spleen meet at the base of the neck.",
             "caption": "痰濕 + 壓力"},
            {"n": 3, "secs": 12, "beat": "The Fix",
             "visual": "Doctor does slow neck rolls and shoulder circles then presses his thumbs into the base of his skull with eyes closed. Close insert of the point at the base of the skull marked.",
             "voice": "Try this. Each evening do slow neck rolls and shoulder circles and press the point at the base of the skull. It may ease tension and reduce the buildup over time.",
             "caption": "Neck rolls + press 風池"},
            {"n": 4, "secs": 8, "beat": "CTA",
             "visual": "Doctor faces camera calm and supportive.",
             "voice": "Comment hump and I will send you my full stress and neck release protocol.",
             "caption": "Comment 👇 hump"},
        ],
        "first_dm": (
            "Hey! That neck hump is often stress + dampness, not just posture 🌿\n\n"
            "Quick q so I tailor it — are you under long-term stress or poor sleep right now?"
        ),
        "infographic_brief": (
            "Vertical infographic, 4:5 ratio, warm TCM clinic aesthetic.\n"
            "Title: 'Neck Hump — The Cortisol Connection'.\n"
            "Three panels:\n"
            "1) WHY — side-neck icon; text: chronic stress + dampness pile up at the neck base.\n"
            "2) EVENING FIX — neck-roll + pressure-point icons; text: neck rolls, shoulder circles, press base of skull.\n"
            "3) LOWER STRESS — text: earlier sleep, less sugar + caffeine, calming breath before bed.\n"
            "Footer: 'Rapid growth or other symptoms? See a doctor to rule out causes.' Flat icons only."
        ),
        "second_dm": (
            "Here's your neck-release guide — pair it with earlier nights to lower cortisol 🌙\n\n"
            "Want my full stress-reset routine? Reply 'calm'."
        ),
    },

    # ───────────────────────── 22. Facial Aging = Liver Blood ─────────────────────────
    {
        "title": "Facial Aging = Liver Blood Deficiency",
        "master_script": [
            "If your skin is aging faster than it should with dull tone and new lines this is not only about creams.",
            "In Chinese medicine the face is fed by liver blood. When liver blood runs low the skin loses its glow and ages before its time.",
            "Try this. Eat red dates goji berries and black sesame and sleep before eleven so the liver can rebuild blood. It may bring back tone and softness.",
            "Comment aging and I will send you my full skin from within nourishing protocol.",
        ],
        "shots": [
            {"n": 1, "secs": 10, "beat": "Hook",
             "visual": "Doctor gently gestures to the cheeks and under eyes on a face diagram with a thoughtful expression. Cutaway insert of dull tired skin then softer glowing skin. Back to doctor giving an encouraging nod.",
             "voice": "If your skin is aging faster than it should with dull tone and new lines this is not only about creams.",
             "caption": "Aging skin starts inside"},
            {"n": 2, "secs": 12, "beat": "Root Cause",
             "visual": "Doctor points to the liver on a body chart then traces a line up to the face to show it feeding the skin. Cutaway insert of a wilting plant reviving as water reaches it.",
             "voice": "In Chinese medicine the face is fed by liver blood. When liver blood runs low the skin loses its glow and ages before its time.",
             "caption": "肝血養面"},
            {"n": 3, "secs": 12, "beat": "The Fix",
             "visual": "Doctor lays out red dates goji berries and black sesame in small bowls then gestures to a clock at eleven and a calm sleeping pose. Overhead insert of the three foods and a small clock.",
             "voice": "Try this. Eat red dates goji berries and black sesame and sleep before eleven so the liver can rebuild blood. It may bring back tone and softness.",
             "caption": "Red dates + goji + sleep by 11"},
            {"n": 4, "secs": 8, "beat": "CTA",
             "visual": "Doctor looks into camera warm and reassuring.",
             "voice": "Comment aging and I will send you my full skin from within nourishing protocol.",
             "caption": "Comment 👇 aging"},
        ],
        "first_dm": (
            "Hey! Glowing skin in TCM is really about liver blood ✨\n\n"
            "Quick q so I tailor it — is your skin more dull-and-dry, or also showing dark circles + brittle nails?"
        ),
        "infographic_brief": (
            "Vertical infographic, 4:5 ratio, warm TCM clinic aesthetic.\n"
            "Title: 'Aging Skin — Nourish Liver Blood'.\n"
            "Three panels:\n"
            "1) WHY — face + liver icon; text: the face is fed by liver blood; low blood = dull, early aging.\n"
            "2) EAT — red date + goji + sesame icons; text: red dates, goji, black sesame, beetroot, leafy greens.\n"
            "3) RESTORE — moon icon; text: sleep before 11pm so the liver rebuilds blood; manage stress.\n"
            "Footer: 'Pair inside-nourishment with sun protection.' Flat icons only."
        ),
        "second_dm": (
            "Here's your skin-from-within guide — the 11pm bedtime is the secret weapon 🌙\n\n"
            "Want the full blood-nourishing meal plan? Reply 'glow'."
        ),
    },

    # ───────────────────────── 23. Swollen Ankles + Puffiness ─────────────────────────
    {
        "title": "Swollen Ankles + Puffiness (Kidney Fluid)",
        "master_script": [
            "Those swollen ankles and the puffiness you carry every day mean your body forgot how to let water go.",
            "In Chinese medicine the kidneys govern water. When kidney yang runs cold and weak fluid is not transformed and it pools in the ankles and face.",
            "Try this. Drink warm red bean and barley water and gently massage from ankle up toward the knee. It may help your body release the trapped fluid.",
            "Comment ankles and I will send you my full fluid releasing protocol.",
        ],
        "shots": [
            {"n": 1, "secs": 10, "beat": "Hook",
             "visual": "Doctor presses a swollen ankle leaving a lingering dent and gives a knowing look to camera. Cutaway insert of the finger-dent slowly filling back in. Back to doctor shaking his head.",
             "voice": "Those swollen ankles and the puffiness you carry every day mean your body forgot how to let water go.",
             "caption": "Puffiness = trapped water"},
            {"n": 2, "secs": 12, "beat": "Root Cause",
             "visual": "Doctor points to the kidneys on a body chart and mimes cold water failing to move. Cutaway insert of icy still water versus warm water flowing freely.",
             "voice": "In Chinese medicine the kidneys govern water. When kidney yang runs cold and weak fluid is not transformed and it pools in the ankles and face.",
             "caption": "腎陽虛 · 水濕內停"},
            {"n": 3, "secs": 12, "beat": "The Fix",
             "visual": "Doctor sips warm red bean and barley water then massages firmly from his ankle upward toward the knee. Overhead insert of red beans barley and a warm cup.",
             "voice": "Try this. Drink warm red bean and barley water and gently massage from ankle up toward the knee. It may help your body release the trapped fluid.",
             "caption": "Red bean barley water + leg massage"},
            {"n": 4, "secs": 8, "beat": "CTA",
             "visual": "Doctor faces camera calm and caring.",
             "voice": "Comment ankles and I will send you my full fluid releasing protocol.",
             "caption": "Comment 👇 ankles"},
        ],
        "first_dm": (
            "Hey! Ankle + face puffiness usually means fluid isn't being transformed 💧\n\n"
            "Quick check so I tailor it — is the puffiness worse in the morning, or by the end of the day?"
        ),
        "infographic_brief": (
            "Vertical infographic, 4:5 ratio, warm TCM clinic aesthetic.\n"
            "Title: 'Puffiness — Help Your Body Release Water'.\n"
            "Three panels:\n"
            "1) WHY — kidney icon; text: weak kidney yang can't transform fluid; it pools low.\n"
            "2) DAILY FIX — red-bean + massage icons; text: warm red bean + barley water, massage ankle→knee.\n"
            "3) SUPPORT — text: reduce salt + cold drinks, keep warm, gentle daily movement.\n"
            "Footer: 'Sudden, severe, or with breathlessness? See a doctor urgently.' Flat icons only."
        ),
        "second_dm": (
            "Here's your de-puffing guide — warm red bean + barley water is the daily staple 💧\n\n"
            "Want the full kidney-warming food list? Reply 'kidney'."
        ),
    },

    # ───────────────────────── 24. Varicose Veins ─────────────────────────
    {
        "title": "Varicose Veins (Stagnant Blood TCM)",
        "master_script": [
            "If the veins on your legs are bulging and twisted like this it is not just aging. It is stuck blood.",
            "In Chinese medicine varicose veins are blood stagnation. When qi is too weak to push blood upward it pools and the veins swell.",
            "Try this. Elevate your legs above your heart each evening and massage with a little warming circulation oil moving upward. It may help the blood move again.",
            "Comment veins and I will send you my full circulation and blood moving protocol.",
        ],
        "shots": [
            {"n": 1, "secs": 10, "beat": "Hook",
             "visual": "Doctor gestures to a leg diagram showing bulging twisted veins with a concerned teaching look. Cutaway insert of the raised veins close up. Back to doctor shaking his head.",
             "voice": "If the veins on your legs are bulging and twisted like this it is not just aging. It is stuck blood.",
             "caption": "Varicose veins = stuck blood"},
            {"n": 2, "secs": 12, "beat": "Root Cause",
             "visual": "Doctor points to the legs on a body chart and mimes weak upward pushing then pooling. Cutaway insert of water failing to rise and pooling at the bottom of a tube.",
             "voice": "In Chinese medicine varicose veins are blood stagnation. When qi is too weak to push blood upward it pools and the veins swell.",
             "caption": "氣虛血瘀"},
            {"n": 3, "secs": 12, "beat": "The Fix",
             "visual": "Doctor lies back resting his legs up a wall then warms oil and massages his calf in upward strokes. Overhead insert of legs elevated and a small bottle of circulation oil.",
             "voice": "Try this. Elevate your legs above your heart each evening and massage with a little warming circulation oil moving upward. It may help the blood move again.",
             "caption": "Legs up + upward massage"},
            {"n": 4, "secs": 8, "beat": "CTA",
             "visual": "Doctor looks into camera steady and reassuring.",
             "voice": "Comment veins and I will send you my full circulation and blood moving protocol.",
             "caption": "Comment 👇 veins"},
        ],
        "first_dm": (
            "Hey! Varicose veins are a blood-flow issue we can support a lot 🦵\n\n"
            "Quick q so I tailor it — do your legs feel heavy and achy by evening, or mostly look bothersome?"
        ),
        "infographic_brief": (
            "Vertical infographic, 4:5 ratio, warm TCM clinic aesthetic.\n"
            "Title: 'Varicose Veins — Get the Blood Moving'.\n"
            "Three panels:\n"
            "1) WHY — leg-vein icon; text: weak qi can't push blood up; it pools + stagnates.\n"
            "2) EVENING FIX — legs-up + massage icons; text: elevate legs above heart 15 min, massage upward.\n"
            "3) CIRCULATE — text: walk daily, avoid long standing, hawthorn + ginger, stay warm.\n"
            "Footer: 'Hot, hard, painful veins? Rule out a clot with a doctor.' Flat icons only."
        ),
        "second_dm": (
            "Here's your circulation guide — legs-up-the-wall nightly is the easy win 🦵\n\n"
            "Want the blood-moving food + movement list? Reply 'flow'."
        ),
    },

    # ───────────────────────── 25. Backed Up Liver ─────────────────────────
    {
        "title": "Backed Up Liver (3 Warning Signs)",
        "master_script": [
            "This is a backed up liver. Most people do not know they have one until the signs pile up.",
            "In Chinese medicine a stuck liver shows three signs. Waking between one and three in the morning. Tight irritable moods. And tension across the right ribs.",
            "Try this. Sip warm lemon water in the morning and do slow side stretches to open the ribs. It may help the liver energy move and unwind.",
            "Comment liver and I will send you my full liver decongesting protocol.",
        ],
        "shots": [
            {"n": 1, "secs": 10, "beat": "Hook",
             "visual": "Doctor places a hand under the right ribs with a knowing look then holds up three fingers to camera. Cutaway insert of the right-rib liver area on a body chart. Back to doctor leaning in.",
             "voice": "This is a backed up liver. Most people do not know they have one until the signs pile up.",
             "caption": "3 signs of a backed-up liver"},
            {"n": 2, "secs": 12, "beat": "The 3 Signs",
             "visual": "Doctor counts on fingers: points to a clock at two in the morning, then to a tense frowning face, then to the right ribs. Cutaway inserts of each — clock, mood, ribs.",
             "voice": "In Chinese medicine a stuck liver shows three signs. Waking between one and three in the morning. Tight irritable moods. And tension across the right ribs.",
             "caption": "丑時醒 · 易怒 · 脅脹"},
            {"n": 3, "secs": 12, "beat": "The Fix",
             "visual": "Doctor sips warm lemon water then does a slow standing side stretch reaching one arm overhead to open the ribs. Overhead insert of lemon water and a simple side-stretch icon.",
             "voice": "Try this. Sip warm lemon water in the morning and do slow side stretches to open the ribs. It may help the liver energy move and unwind.",
             "caption": "Warm lemon water + side stretch"},
            {"n": 4, "secs": 8, "beat": "CTA",
             "visual": "Doctor faces camera calm and direct.",
             "voice": "Comment liver and I will send you my full liver decongesting protocol.",
             "caption": "Comment 👇 liver"},
        ],
        "first_dm": (
            "Hey! A stuck liver loves to wake you at 1–3am 🌙\n\n"
            "Quick check so I tailor it — do you wake in the early hours, feel tense/irritable, or both?"
        ),
        "infographic_brief": (
            "Vertical infographic, 4:5 ratio, warm TCM clinic aesthetic.\n"
            "Title: 'Backed-Up Liver — 3 Warning Signs'.\n"
            "Three sign panels: 1–3am waking · irritability + tight mood · right-rib tension.\n"
            "Then a FIX strip: warm lemon water AM · side stretches to open ribs · less alcohol, sugar + late meals.\n"
            "Footer: 'Yellowing skin/eyes or severe pain? See a doctor.' Flat icons only."
        ),
        "second_dm": (
            "Here's your liver-decongesting guide — the early-hours waking often improves first 🌙\n\n"
            "Want the full liver-soothing food + routine? Reply 'flow'."
        ),
    },

    # ───────────────────────── 26. Eczema ─────────────────────────
    {
        "title": "Eczema (Blood + Gut Root Cause)",
        "master_script": [
            "Look at this eczema. Steroid creams calmed it then it came back worse. The skin was never the root.",
            "In Chinese medicine stubborn eczema is heat and dampness in the blood often fed by a struggling gut. The skin is just where it shows.",
            "Try this. Cool the blood with mung bean soup and calm the gut by cutting dairy and sugar. Soothe the skin outside with cooled chamomile compress.",
            "Comment eczema and I will send you my full skin and gut clearing protocol.",
        ],
        "shots": [
            {"n": 1, "secs": 10, "beat": "Hook",
             "visual": "Doctor gestures gently to an inflamed eczema patch on an arm diagram with a compassionate look then shakes his head at a tube of cream. Cutaway insert of red flaky skin close up. Back to doctor leaning in.",
             "voice": "Look at this eczema. Steroid creams calmed it then it came back worse. The skin was never the root.",
             "caption": "Eczema isn't a skin problem"},
            {"n": 2, "secs": 12, "beat": "Root Cause",
             "visual": "Doctor points to the blood and gut on a body chart and mimes heat rising to the skin. Cutaway insert of a heated pot bubbling over to the surface.",
             "voice": "In Chinese medicine stubborn eczema is heat and dampness in the blood often fed by a struggling gut. The skin is just where it shows.",
             "caption": "血熱濕盛 · 脾胃"},
            {"n": 3, "secs": 12, "beat": "The Fix",
             "visual": "Doctor ladles mung bean soup into a bowl waves away dairy and sugar then lays a cool chamomile compress on his forearm. Overhead insert of mung bean soup and a chamomile compress.",
             "voice": "Try this. Cool the blood with mung bean soup and calm the gut by cutting dairy and sugar. Soothe the skin outside with cooled chamomile compress.",
             "caption": "Mung bean soup + chamomile compress"},
            {"n": 4, "secs": 8, "beat": "CTA",
             "visual": "Doctor faces camera warm and reassuring.",
             "voice": "Comment eczema and I will send you my full skin and gut clearing protocol.",
             "caption": "Comment 👇 eczema"},
        ],
        "first_dm": (
            "Hey! Stubborn eczema is usually blood-heat + gut, not just skin 🌿\n\n"
            "Quick q so I tailor it — is your eczema more red-hot-and-itchy, or dry-and-flaky?"
        ),
        "infographic_brief": (
            "Vertical infographic, 4:5 ratio, warm TCM clinic aesthetic.\n"
            "Title: 'Eczema — Clear the Blood + Gut'.\n"
            "Three panels:\n"
            "1) ROOT — blood + gut icon; text: heat + dampness in the blood, fed by the gut.\n"
            "2) COOL + CALM — mung bean + compress icons; text: mung bean soup, cool chamomile compress, cut dairy + sugar.\n"
            "3) PROTECT SKIN — text: gentle fragrance-free moisturizer, avoid hot water + scratching.\n"
            "Footer: 'Infected, weeping, or spreading fast? See a doctor.' Flat icons only."
        ),
        "second_dm": (
            "Here's your eczema guide — cooling the blood from inside is the slow but real fix 🌿\n\n"
            "Want the full gut-and-skin elimination plan? Reply 'gut'."
        ),
    },

    # ───────────────────────── 27. Full Body Detox Foot Soak ─────────────────────────
    {
        "title": "Full Body Detox Foot Soak (5 Ingredients)",
        "master_script": [
            "Detox your whole body through the soles of your feet. Five simple ingredients and twenty minutes.",
            "In Chinese medicine the feet hold the start and end of many channels. A warm soak opens the pores and helps the body release dampness and cold.",
            "Try this. Warm water with epsom salt ginger a splash of vinegar and a handful of mugwort. Soak twenty minutes before bed. It may relax you deeply and aid release.",
            "Comment soak and I will send you my full detox foot soak recipe.",
        ],
        "shots": [
            {"n": 1, "secs": 10, "beat": "Hook",
             "visual": "Doctor lowers his feet into a steaming herbal basin with a relaxed sigh and gestures five fingers to camera. Cutaway insert of the steaming basin with herbs floating. Back to doctor smiling.",
             "voice": "Detox your whole body through the soles of your feet. Five simple ingredients and twenty minutes.",
             "caption": "Whole-body detox through the feet"},
            {"n": 2, "secs": 12, "beat": "Root Cause",
             "visual": "Doctor points to the soles on a foot-channel chart then mimes warmth opening the pores. Cutaway insert of steam opening tiny pores on skin.",
             "voice": "In Chinese medicine the feet hold the start and end of many channels. A warm soak opens the pores and helps the body release dampness and cold.",
             "caption": "足部經絡 · 排寒濕"},
            {"n": 3, "secs": 12, "beat": "The Fix",
             "visual": "Doctor adds epsom salt ginger vinegar and mugwort one by one into the warm basin then settles his feet in. Overhead insert of the five ingredients laid out beside the basin.",
             "voice": "Try this. Warm water with epsom salt ginger a splash of vinegar and a handful of mugwort. Soak twenty minutes before bed. It may relax you deeply and aid release.",
             "caption": "Epsom + ginger + vinegar + mugwort"},
            {"n": 4, "secs": 8, "beat": "CTA",
             "visual": "Doctor faces camera relaxed and inviting.",
             "voice": "Comment soak and I will send you my full detox foot soak recipe.",
             "caption": "Comment 👇 soak"},
        ],
        "first_dm": (
            "Hey! This foot soak is the easiest way to unwind + release dampness 🛁\n\n"
            "Quick q so I tailor it — are you after better sleep, less puffiness, or warming up cold feet?"
        ),
        "infographic_brief": (
            "Vertical infographic, 4:5 ratio, warm TCM clinic aesthetic.\n"
            "Title: 'Detox Foot Soak — 5 Ingredients'.\n"
            "Top: a basin illustration. Five labeled ingredient icons: epsom salt · fresh ginger · splash of vinegar · "
            "mugwort (艾葉) · warm water.\n"
            "Method strip: 'Warm (not hot), soak 20 min before bed, dry feet + keep warm after.'\n"
            "Footer: 'Pregnant, diabetic, or low BP? Check with a practitioner first.' Flat icons only."
        ),
        "second_dm": (
            "Here's your foot-soak recipe — do it 2–3 nights a week before bed 🛁\n\n"
            "Want the seasonal variations (warming vs cooling)? Reply 'soak'."
        ),
    },

    # ───────────────────────── 28. Onion Slices on Feet ─────────────────────────
    {
        "title": "Onion Slices on Feet Overnight",
        "master_script": [
            "Tape a few onion slices to the soles of your feet before bed and leave them overnight.",
            "In Chinese medicine the soles connect to the whole body. Onion is warming and pungent and is traditionally used to draw out cold and support the lungs.",
            "Try this. Slice a fresh onion tape a piece to each sole put on socks and sleep. It may warm the feet and ease a stubborn cough by morning.",
            "Comment onion and I will send you my full overnight remedies guide.",
        ],
        "shots": [
            {"n": 1, "secs": 10, "beat": "Hook",
             "visual": "Doctor holds up a fresh onion and a roll of tape with a slightly playful confident look. Macro insert of an onion being sliced into rounds. Back to doctor nodding.",
             "voice": "Tape a few onion slices to the soles of your feet before bed and leave them overnight.",
             "caption": "Onion on the feet overnight"},
            {"n": 2, "secs": 12, "beat": "Root Cause",
             "visual": "Doctor points to the soles on a foot-channel chart and mimes warmth rising and cold leaving. Cutaway insert of an onion with warm pungent vapor lines.",
             "voice": "In Chinese medicine the soles connect to the whole body. Onion is warming and pungent and is traditionally used to draw out cold and support the lungs.",
             "caption": "辛溫 · 散寒 · 宣肺"},
            {"n": 3, "secs": 12, "beat": "The Fix",
             "visual": "Doctor places an onion round on each sole tapes it then pulls on socks and lies back. Overhead insert of onion slices tape and socks.",
             "voice": "Try this. Slice a fresh onion tape a piece to each sole put on socks and sleep. It may warm the feet and ease a stubborn cough by morning.",
             "caption": "Onion + tape + socks to bed"},
            {"n": 4, "secs": 8, "beat": "CTA",
             "visual": "Doctor faces camera warm and friendly.",
             "voice": "Comment onion and I will send you my full overnight remedies guide.",
             "caption": "Comment 👇 onion"},
        ],
        "first_dm": (
            "Hey! The onion-on-feet trick is an old warming remedy 🧅\n\n"
            "Quick q so I tailor it — are you mainly fighting a cough/cold, or cold feet at night?"
        ),
        "infographic_brief": (
            "Vertical infographic, 4:5 ratio, warm TCM clinic aesthetic.\n"
            "Title: 'Onion on the Feet — Overnight Warming Remedy'.\n"
            "Three panels:\n"
            "1) WHY — sole + onion icon; text: feet connect to the body; onion is warming + pungent, traditionally clears cold.\n"
            "2) HOW — onion + tape + sock icons; text: slice fresh onion, tape to each sole, socks on, sleep.\n"
            "3) SUPPORT — text: warm fluids, ginger tea, rest; best at the first sign of a chill.\n"
            "Footer: 'A comfort remedy — see a doctor for high fever or breathing trouble.' Flat icons only."
        ),
        "second_dm": (
            "Here's your overnight-remedy guide — fresh onion works better than old 🧅\n\n"
            "Want my full first-sign-of-a-cold kit? Reply 'cold'."
        ),
    },

    # ───────────────────────── 29. Cinnamon Weight Loss Tea ─────────────────────────
    {
        "title": "Cinnamon Weight Loss Tea",
        "master_script": [
            "Do not drink this too often or your clothes may start feeling loose faster than you expect.",
            "In Chinese medicine slow weight gain often comes from a cold damp spleen that cannot move food and fluid. Warming spices wake it up.",
            "Try this. Simmer cinnamon with a slice of ginger and a little honey and sip it warm before meals. It may warm the spleen and curb cravings.",
            "Comment tea and I will send you my full metabolism warming tea guide.",
        ],
        "shots": [
            {"n": 1, "secs": 10, "beat": "Hook",
             "visual": "Doctor holds up a cinnamon stick and a warm cup with a playful raised eyebrow. Macro insert of cinnamon and ginger steeping in a clear pot. Back to doctor smiling.",
             "voice": "Do not drink this too often or your clothes may start feeling loose faster than you expect.",
             "caption": "The tea that loosens your clothes"},
            {"n": 2, "secs": 12, "beat": "Root Cause",
             "visual": "Doctor points to the spleen on a body chart and mimes a cold sluggish belly then warmth waking it. Cutaway insert of a cold stiff engine starting to turn with warmth.",
             "voice": "In Chinese medicine slow weight gain often comes from a cold damp spleen that cannot move food and fluid. Warming spices wake it up.",
             "caption": "脾虛濕困"},
            {"n": 3, "secs": 12, "beat": "The Fix",
             "visual": "Doctor simmers cinnamon and ginger stirs in honey pours a cup and sips before a meal. Overhead insert of cinnamon ginger honey and a warm cup.",
             "voice": "Try this. Simmer cinnamon with a slice of ginger and a little honey and sip it warm before meals. It may warm the spleen and curb cravings.",
             "caption": "Cinnamon + ginger tea before meals"},
            {"n": 4, "secs": 8, "beat": "CTA",
             "visual": "Doctor faces camera warm and encouraging.",
             "voice": "Comment tea and I will send you my full metabolism warming tea guide.",
             "caption": "Comment 👇 tea"},
        ],
        "first_dm": (
            "Hey! This warming tea supports a sluggish metabolism 🍂\n\n"
            "Quick q so I tailor it — do you tend to feel cold, bloated, and crave sweets in the afternoon?"
        ),
        "infographic_brief": (
            "Vertical infographic, 4:5 ratio, warm TCM clinic aesthetic.\n"
            "Title: 'Cinnamon Tea — Warm a Sluggish Metabolism'.\n"
            "Three panels:\n"
            "1) WHY — spleen icon; text: a cold damp spleen slows metabolism + traps fluid.\n"
            "2) RECIPE — cinnamon + ginger + honey icons; text: simmer cinnamon + ginger, a little honey, sip warm before meals.\n"
            "3) SUPPORT — text: warm cooked food, fewer cold drinks, walk after meals.\n"
            "Footer: 'Pregnant or on blood-sugar meds? Check with a doctor.' Flat icons only."
        ),
        "second_dm": (
            "Here's your metabolism-tea guide — before meals is the sweet spot 🍂\n\n"
            "Want the full warm-eating plan that supports it? Reply 'warm'."
        ),
    },

    # ───────────────────────── 30. Pineapple + Cinnamon Detox Smoothie ─────────────────────────
    {
        "title": "Pineapple + Cinnamon Detox Smoothie",
        "master_script": [
            "Put cinnamon on pineapple and just watch what happens. This pairing is gentle and powerful.",
            "In Chinese medicine pineapple clears damp heat and aids digestion while cinnamon warms the center. Together they move stuck food and bloating.",
            "Try this. Blend fresh pineapple with a pinch of cinnamon and warm water and drink it in the morning. It may ease bloating and support digestion.",
            "Comment pineapple and I will send you my full gut and detox smoothie guide.",
        ],
        "shots": [
            {"n": 1, "secs": 10, "beat": "Hook",
             "visual": "Doctor sprinkles cinnamon over fresh pineapple chunks with a curious smile to camera. Macro insert of cinnamon dusting golden pineapple. Back to doctor nodding.",
             "voice": "Put cinnamon on pineapple and just watch what happens. This pairing is gentle and powerful.",
             "caption": "Cinnamon + pineapple = magic"},
            {"n": 2, "secs": 12, "beat": "Root Cause",
             "visual": "Doctor points to the stomach on a body chart and mimes stuck food then easy movement. Cutaway insert of pineapple enzymes breaking down a heavy meal.",
             "voice": "In Chinese medicine pineapple clears damp heat and aids digestion while cinnamon warms the center. Together they move stuck food and bloating.",
             "caption": "清濕熱 + 溫中"},
            {"n": 3, "secs": 12, "beat": "The Fix",
             "visual": "Doctor blends pineapple cinnamon and warm water pours the smoothie and sips with a satisfied nod. Overhead insert of pineapple cinnamon and the blended cup.",
             "voice": "Try this. Blend fresh pineapple with a pinch of cinnamon and warm water and drink it in the morning. It may ease bloating and support digestion.",
             "caption": "Pineapple + cinnamon smoothie AM"},
            {"n": 4, "secs": 8, "beat": "CTA",
             "visual": "Doctor faces camera bright and friendly.",
             "voice": "Comment pineapple and I will send you my full gut and detox smoothie guide.",
             "caption": "Comment 👇 pineapple"},
        ],
        "first_dm": (
            "Hey! Pineapple + cinnamon is a lovely gentle digestive combo 🍍\n\n"
            "Quick q so I tailor it — is your main issue bloating, sluggish digestion, or both?"
        ),
        "infographic_brief": (
            "Vertical infographic, 4:5 ratio, warm TCM clinic aesthetic.\n"
            "Title: 'Pineapple + Cinnamon — Gentle Gut Reset'.\n"
            "Three panels:\n"
            "1) WHY — stomach icon; text: pineapple clears damp-heat + aids digestion, cinnamon warms the center.\n"
            "2) RECIPE — pineapple + cinnamon icons; text: blend fresh pineapple, pinch of cinnamon, warm water, AM.\n"
            "3) SUPPORT — text: eat slowly, warm meals, don't drink ice-cold.\n"
            "Footer: 'Acid reflux or mouth sensitivity? Go easy on pineapple.' Flat icons only."
        ),
        "second_dm": (
            "Here's your gut-reset smoothie guide — warm water, never iced, keeps it gentle 🍍\n\n"
            "Want the full anti-bloat morning routine? Reply 'gut'."
        ),
    },

    # ───────────────────────── 31. Stretch Marks ─────────────────────────
    {
        "title": "Stretch Marks (Not a Skin Problem)",
        "master_script": [
            "Look at these stretch marks. The skin was never the real problem and creams alone rarely fix them.",
            "In Chinese medicine the skin is held by spleen qi and fed by blood. When they run weak the skin tears under the surface and marks form.",
            "Try this. Nourish from inside with bone broth and red dates and massage the marks with warm sesame oil daily. It may slowly soften and fade them.",
            "Comment marks and I will send you my full skin firming from within protocol.",
        ],
        "shots": [
            {"n": 1, "secs": 10, "beat": "Hook",
             "visual": "Doctor gestures to stretch marks on a belly diagram with a thoughtful look then sets down a cream tube and shakes his head. Cutaway insert of silvery stretch marks close up. Back to doctor leaning in.",
             "voice": "Look at these stretch marks. The skin was never the real problem and creams alone rarely fix them.",
             "caption": "Stretch marks start inside"},
            {"n": 2, "secs": 12, "beat": "Root Cause",
             "visual": "Doctor points to the spleen and blood on a body chart and mimes weak support under the skin. Cutaway insert of fabric stretching and tearing from underneath.",
             "voice": "In Chinese medicine the skin is held by spleen qi and fed by blood. When they run weak the skin tears under the surface and marks form.",
             "caption": "脾主肌肉 · 血養膚"},
            {"n": 3, "secs": 12, "beat": "The Fix",
             "visual": "Doctor ladles bone broth and sets out red dates then warms sesame oil and massages it into the skin in circles. Overhead insert of bone broth red dates and sesame oil.",
             "voice": "Try this. Nourish from inside with bone broth and red dates and massage the marks with warm sesame oil daily. It may slowly soften and fade them.",
             "caption": "Bone broth + sesame oil massage"},
            {"n": 4, "secs": 8, "beat": "CTA",
             "visual": "Doctor faces camera warm and reassuring.",
             "voice": "Comment marks and I will send you my full skin firming from within protocol.",
             "caption": "Comment 👇 marks"},
        ],
        "first_dm": (
            "Hey! Stretch marks really are an inside-out fix in TCM 🌿\n\n"
            "Quick q so I tailor it — are your marks more fresh-and-red, or older-and-silvery?"
        ),
        "infographic_brief": (
            "Vertical infographic, 4:5 ratio, warm TCM clinic aesthetic.\n"
            "Title: 'Stretch Marks — Firm the Skin From Within'.\n"
            "Three panels:\n"
            "1) WHY — skin-layer icon; text: skin is held by spleen qi + fed by blood; weakness = tearing.\n"
            "2) NOURISH — broth + red-date icons; text: bone broth, red dates, protein, enough water.\n"
            "3) OUTSIDE — sesame-oil icon; text: daily warm sesame-oil massage in circles.\n"
            "Footer: 'Fresh red marks respond best — be patient + consistent.' Flat icons only."
        ),
        "second_dm": (
            "Here's your skin-firming guide — the inside nourishment is what creams miss 🌿\n\n"
            "Want the full blood + qi building meal plan? Reply 'firm'."
        ),
    },

    # ───────────────────────── 32. Lemon + Beet Blood Cleanse ─────────────────────────
    {
        "title": "Lemon + Beet Blood Cleanse",
        "master_script": [
            "Put lemon on beets and just watch what happens. This simple pairing supports your blood.",
            "In Chinese medicine dull skin fatigue and cold hands can mean weak and stagnant blood. Beets build blood and lemon helps move and brighten it.",
            "Try this. Juice fresh beetroot with a squeeze of lemon and sip it a few times a week. It may support blood building and circulation.",
            "Comment beet and I will send you my full blood building cleanse guide.",
        ],
        "shots": [
            {"n": 1, "secs": 10, "beat": "Hook",
             "visual": "Doctor squeezes lemon over deep red beet slices with a curious confident look to camera. Macro insert of lemon juice hitting vivid beet red. Back to doctor nodding.",
             "voice": "Put lemon on beets and just watch what happens. This simple pairing supports your blood.",
             "caption": "Lemon + beets for your blood"},
            {"n": 2, "secs": 12, "beat": "Root Cause",
             "visual": "Doctor points to pale skin and cold hands on a body chart then to the heart and liver that govern blood. Cutaway insert of pale dull liquid turning rich and vivid red.",
             "voice": "In Chinese medicine dull skin fatigue and cold hands can mean weak and stagnant blood. Beets build blood and lemon helps move and brighten it.",
             "caption": "血虛血瘀"},
            {"n": 3, "secs": 12, "beat": "The Fix",
             "visual": "Doctor juices beetroot adds a squeeze of lemon pours the deep red juice and sips. Overhead insert of beets lemon and the ruby juice glass.",
             "voice": "Try this. Juice fresh beetroot with a squeeze of lemon and sip it a few times a week. It may support blood building and circulation.",
             "caption": "Beet + lemon juice, few times a week"},
            {"n": 4, "secs": 8, "beat": "CTA",
             "visual": "Doctor faces camera warm and assured.",
             "voice": "Comment beet and I will send you my full blood building cleanse guide.",
             "caption": "Comment 👇 beet"},
        ],
        "first_dm": (
            "Hey! Beet + lemon is a lovely blood-building combo 🫐\n\n"
            "Quick q so I tailor it — do you get tired easily, pale, or cold hands and feet?"
        ),
        "infographic_brief": (
            "Vertical infographic, 4:5 ratio, warm TCM clinic aesthetic.\n"
            "Title: 'Beet + Lemon — Build + Move Your Blood'.\n"
            "Three panels:\n"
            "1) SIGNS — body icon; text: dull skin, fatigue, cold hands = weak/stagnant blood.\n"
            "2) RECIPE — beet + lemon icons; text: juice fresh beetroot + squeeze of lemon, a few times a week.\n"
            "3) BUILD MORE — text: red dates, leafy greens, black sesame, beans.\n"
            "Footer: 'On blood thinners or low BP? Check with a doctor.' Flat icons only."
        ),
        "second_dm": (
            "Here's your blood-cleanse guide — beets can turn urine pink, that's normal 🫐\n\n"
            "Want the full blood-building food list? Reply 'blood'."
        ),
    },

    # ───────────────────────── 33. Lower Back Pain (Vicks + Epsom) ─────────────────────────
    {
        "title": "Lower Back Pain Fix (Vicks + Epsom Salt)",
        "master_script": [
            "If you have unbearable lower back pain the kind where you cannot stand sit or lie down listen closely.",
            "In Chinese medicine this lower back is the seat of the kidneys. Cold and damp lodging there stiffen the muscles and lock the back.",
            "Try this. Soak in a warm epsom salt bath then rub a warming balm over the sore area and cover it. It may relax the muscles and ease the lock.",
            "Comment back and I will send you my full lower back rescue protocol.",
        ],
        "shots": [
            {"n": 1, "secs": 10, "beat": "Hook",
             "visual": "Doctor places both hands on his lower back wincing then steadies and looks to camera with empathy. Cutaway insert of hands cupping a stiff lower back. Back to doctor leaning in.",
             "voice": "If you have unbearable lower back pain the kind where you cannot stand sit or lie down listen closely.",
             "caption": "For unbearable lower back pain"},
            {"n": 2, "secs": 12, "beat": "Root Cause",
             "visual": "Doctor points to the kidney area on a body chart and mimes cold damp lodging and muscles tightening. Cutaway insert of a cold blue lower back stiffening.",
             "voice": "In Chinese medicine this lower back is the seat of the kidneys. Cold and damp lodging there stiffen the muscles and lock the back.",
             "caption": "腰為腎府 · 寒濕痹阻"},
            {"n": 3, "secs": 12, "beat": "The Fix",
             "visual": "Doctor eases into a warm epsom bath then steps out and rubs warming balm over the lower back and presses a warm cloth on. Overhead insert of epsom salt and a balm jar.",
             "voice": "Try this. Soak in a warm epsom salt bath then rub a warming balm over the sore area and cover it. It may relax the muscles and ease the lock.",
             "caption": "Epsom bath + warming balm + cover"},
            {"n": 4, "secs": 8, "beat": "CTA",
             "visual": "Doctor faces camera steady and caring.",
             "voice": "Comment back and I will send you my full lower back rescue protocol.",
             "caption": "Comment 👇 back"},
        ],
        "first_dm": (
            "Hey! For a locked-up cold-type lower back, warmth is everything 🔥\n\n"
            "Quick check so I send the right plan — is the pain worse with cold + rest, and a bit better with movement + heat?"
        ),
        "infographic_brief": (
            "Vertical infographic, 4:5 ratio, warm TCM clinic aesthetic.\n"
            "Title: 'Lower Back Rescue — Warm + Release'.\n"
            "Three panels:\n"
            "1) WHY — kidney/low-back icon; text: cold + damp lodge in the back, locking muscles.\n"
            "2) RELIEF — bath + balm icons; text: warm epsom soak, warming balm over the area, keep it covered.\n"
            "3) PROTECT — text: keep the waist warm, gentle movement, avoid cold floors + drafts.\n"
            "Footer: 'Leg numbness, weakness, or bladder changes? See a doctor.' Flat icons only."
        ),
        "second_dm": (
            "Here's your lower-back rescue guide — heat first, gentle movement second 🔥\n\n"
            "Want the kidney-strengthening routine that prevents flare-ups? Reply 'strong'."
        ),
    },

    # ───────────────────────── 34. Baking Soda Dark Spots ─────────────────────────
    {
        "title": "Baking Soda Dark Spots (Neck + Elbows)",
        "master_script": [
            "Put a little baking soda on the dark patches on your neck and you may not believe the change.",
            "In Chinese medicine dark patches on the neck and elbows often signal dampness and sluggish circulation under the skin not just dirt.",
            "Try this twice a week. Make a paste of baking soda and water gently rub the area then seal with coconut oil. It may lift buildup and soften the skin.",
            "Comment spots and I will send you my full dark patch and circulation guide.",
        ],
        "shots": [
            {"n": 1, "secs": 10, "beat": "Hook",
             "visual": "Doctor dabs a baking soda paste onto the side of the neck on a model with a confident look to camera. Macro insert of paste being rubbed in small circles. Back to doctor nodding.",
             "voice": "Put a little baking soda on the dark patches on your neck and you may not believe the change.",
             "caption": "Lift dark neck patches"},
            {"n": 2, "secs": 12, "beat": "Root Cause",
             "visual": "Doctor points to the neck and elbows on a body chart and mimes sluggish flow under the skin. Cutaway insert of a dull patch with slow underlying circulation.",
             "voice": "In Chinese medicine dark patches on the neck and elbows often signal dampness and sluggish circulation under the skin not just dirt.",
             "caption": "濕濁 · 循環不暢"},
            {"n": 3, "secs": 12, "beat": "The Fix",
             "visual": "Doctor mixes baking soda with a little water into a paste rubs it gently on the elbow then smooths coconut oil over the spot. Overhead insert of baking soda water paste and coconut oil.",
             "voice": "Try this twice a week. Make a paste of baking soda and water gently rub the area then seal with coconut oil. It may lift buildup and soften the skin.",
             "caption": "Baking soda paste + coconut oil, 2x/week"},
            {"n": 4, "secs": 8, "beat": "CTA",
             "visual": "Doctor faces camera friendly and assured.",
             "voice": "Comment spots and I will send you my full dark patch and circulation guide.",
             "caption": "Comment 👇 spots"},
        ],
        "first_dm": (
            "Hey! Dark neck/elbow patches are often circulation + dampness, not just dirt 🌿\n\n"
            "Quick q so I tailor it — are the patches velvety-dark (neck), or rough-and-grey (elbows/knees)?"
        ),
        "infographic_brief": (
            "Vertical infographic, 4:5 ratio, warm TCM clinic aesthetic.\n"
            "Title: 'Dark Patches — Lift + Support Circulation'.\n"
            "Three panels:\n"
            "1) WHY — neck/elbow icon; text: dampness + sluggish circulation under the skin.\n"
            "2) 2x WEEK FIX — baking soda + oil icons; text: baking soda paste, gentle rub, seal with coconut oil.\n"
            "3) FROM INSIDE — text: move daily, less refined sugar, check blood sugar if velvety neck.\n"
            "Footer: 'Velvety dark neck can signal insulin issues — get checked.' Flat icons only."
        ),
        "second_dm": (
            "Here's your dark-patch guide — twice a week only so skin stays happy 🌿\n\n"
            "Want the circulation + blood-sugar food list? Reply 'sugar'."
        ),
    },

    # ───────────────────────── 35. Bay Leaves in Socks ─────────────────────────
    {
        "title": "Bay Leaves in Socks (Sleep + Pain)",
        "master_script": [
            "Put a few bay leaves inside your socks before bed and leave them overnight. Your morning may feel different.",
            "In Chinese medicine the soles hold key points and bay leaf is warming and aromatic traditionally used to calm the mind and ease tension.",
            "Try this. Tuck two or three bay leaves against each sole put on socks and sleep. It may relax the body and support deeper rest.",
            "Comment bay and I will send you my full sleep and relaxation foot guide.",
        ],
        "shots": [
            {"n": 1, "secs": 10, "beat": "Hook",
             "visual": "Doctor holds up a few dried bay leaves and a sock with a calm inviting smile. Macro insert of bay leaves being tucked into a sock. Back to doctor nodding gently.",
             "voice": "Put a few bay leaves inside your socks before bed and leave them overnight. Your morning may feel different.",
             "caption": "Bay leaves in socks overnight"},
            {"n": 2, "secs": 12, "beat": "Root Cause",
             "visual": "Doctor points to the sole points on a foot chart then to the head to show the mind-calming link. Cutaway insert of aromatic vapor rising softly from a bay leaf.",
             "voice": "In Chinese medicine the soles hold key points and bay leaf is warming and aromatic traditionally used to calm the mind and ease tension.",
             "caption": "湧泉穴 · 芳香安神"},
            {"n": 3, "secs": 12, "beat": "The Fix",
             "visual": "Doctor places two bay leaves against each sole pulls on cotton socks and settles back with a relaxed breath. Overhead insert of bay leaves and cotton socks.",
             "voice": "Try this. Tuck two or three bay leaves against each sole put on socks and sleep. It may relax the body and support deeper rest.",
             "caption": "Bay leaves + cotton socks to bed"},
            {"n": 4, "secs": 8, "beat": "CTA",
             "visual": "Doctor faces camera warm and calming.",
             "voice": "Comment bay and I will send you my full sleep and relaxation foot guide.",
             "caption": "Comment 👇 bay"},
        ],
        "first_dm": (
            "Hey! The bay-leaf foot trick is a gentle wind-down ritual 🌿\n\n"
            "Quick q so I tailor it — is your main goal falling asleep faster, or staying asleep through the night?"
        ),
        "infographic_brief": (
            "Vertical infographic, 4:5 ratio, warm TCM clinic aesthetic.\n"
            "Title: 'Bay Leaves in Socks — Calm + Sleep'.\n"
            "Three panels:\n"
            "1) WHY — sole + bay-leaf icon; text: soles hold key points; bay leaf is warming + calming.\n"
            "2) HOW — bay + sock icons; text: 2–3 bay leaves on each sole, cotton socks, sleep.\n"
            "3) WIND DOWN — text: warm foot soak first, dim lights, no screens before bed.\n"
            "Footer: 'A comfort ritual — see a doctor for ongoing insomnia.' Flat icons only."
        ),
        "second_dm": (
            "Here's your sleep-ritual guide — pair the bay leaves with a warm foot soak 🌙\n\n"
            "Want my full wind-down routine for deeper sleep? Reply 'sleep'."
        ),
    },
]
