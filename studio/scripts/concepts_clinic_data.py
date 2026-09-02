"""Concept data for the "Jackie treating a patient" batch (10 campaigns).

Format brief (2026-09-02): the patient must be VISIBLE in the shots, the SAME
patient across a video, and the framing must vary — e.g. patient seated while
Jackie stands, both facing camera together.

How the four shots are built
----------------------------
  Shot 1  Hook        two shot, guest seated / Jackie standing behind-right
  Shot 2  Root Cause  two shot, camera flips to the other side, tighter
  Shot 3  Quick Win   two shot, Jackie demonstrating the fix ON the guest
  Shot 4  CTA         Jackie ALONE, tight close-up

Shot 4 is deliberately solo. Three two-shots plus one close-up gives the scale
variety the brief asked for, and the CTA is a direct address to the viewer — a
second person standing there mutely through the call-to-action reads oddly.

Patient consistency uses `[SAME_PERSON_AS: Shot 1]` on shots 2-3, the mechanism
built in 2026-07-14 for exactly this (recurring extras had NO reference image, so
gpt-image-2 improvised a different-looking stranger every shot). Shot 1's render
becomes the reference for the rest.

`[TWO_PERSON]` leads every two-shot 🎥 line. It must come FIRST so it survives
`_primary_beat()`'s split into the image prompt, and it flips both prompts:
build_prompt drops its single-person guard, and build_jimeng_prompt adds the
【Second person】block that tells 即梦 which face owns the audio.

Ailments were chosen to be VISIBLY demonstrable on a seated guest — a back, knee,
neck or shoulder complaint reads instantly in frame. Keywords were verified free
against the live matcher before being written down.
"""
from __future__ import annotations

WARDROBE = {
    "navy": "navy-grey mandarin-collar linen shirt",
    "oatmeal": "warm oatmeal-beige mandarin-collar linen jacket",
    "charcoal": "deep charcoal mandarin-collar linen tunic with fine grey piping",
}

# Each guest is described concretely (age band, hair, top colour) because that
# description is ALSO what shot 1 renders from — vague wording gives the
# SAME_PERSON_AS chain nothing stable to lock onto.
CONCEPTS: list[dict] = [
    {
        "key": "lowback",
        "name": "🩺 Lower Back Pain — What I Check First",
        "topic": "🦴 Pain",
        "hook": "Lower back pain is usually not the back.",
        "wardrobe": "navy",
        "guest": ("a middle-aged woman guest in a plain sage-green linen top with her dark "
                  "hair tied back, seated on a low wooden stool"),
        "guest_short": "the seated woman guest in the sage-green top",
        "prop": "a small pale celadon cup of warm tea",
        "actions": [
            "stands behind and to her right with one open hand held near her lower back to indicate the sore area",
            "stands at her left and traces a slow line down his OWN lower back to show where the ache sits",
            "guides her to press her own lower back with both thumbs while he demonstrates the same press on himself",
        ],
        "script": [
            "When someone comes to me with lower back pain, I do not start at the back. I start at the kidneys.",
            "In Chinese medicine the kidneys govern the lower back. When they run cold and empty, the muscles there lose their support.",
            "Try this with me. Press both thumbs into your lower back and rub until it feels warm. Do it twice a day.",
            "Comment lowback and I will send you my full kidney warming protocol.",
        ],
        "notes": ["Not the back — the kidneys", "腰為腎之府", "Thumb rub until warm, 2x daily", "Comment 👇 lowback"],
        "first_dm": ("Hey! The thumb-rub warms the lower back fast 🩺\n\n"
                     "Quick check — is your ache worse in the morning, or worse after standing all day? "
                     "They point to different roots."),
        "infographic": ("Title: 'Lower Back Pain — Warm the Root'.\n"
                        "1) ROOT — kidney icon; text: the kidneys govern the lower back. Cold and depleted kidneys leave the muscles unsupported.\n"
                        "2) WHAT WORSENS IT — chair icon; text: long sitting, cold damp weather, late nights, lifting with a cold back, too little rest.\n"
                        "3) DAILY FIX — hands icon; text: thumb-rub the lower back until warm twice a day, keep the waist covered, black beans and walnut."),
        "second_dm": ("Here's your lower-back guide — warmth first, stretching second. That order matters 🌿\n\n"
                      "Want the kidney-warming food list? Reply 'warm'."),
    },
    {
        "key": "clicking",
        "name": "🦵 Knee Pain — Why It Clicks and Aches",
        "topic": "🦵 Joint / Knee",
        "hook": "Knee pain is a circulation problem first.",
        "wardrobe": "oatmeal",
        "guest": ("an older man guest in a soft grey button-front shirt with short greying hair, "
                  "seated on a low wooden stool with one trouser leg rolled to the knee"),
        "guest_short": "the seated older man guest in the grey shirt",
        "prop": "a folded warm towel",
        "actions": [
            "stands at his right with one open hand held just above the guest's knee, not touching it",
            "crouches slightly beside him and circles a finger in the air around the kneecap to show where it aches",
            "hands him the folded warm towel and mimes wrapping it around the knee while facing camera",
        ],
        "script": [
            "This gentleman came to me because his knees click and ache every time he stands up.",
            "The knee is where cold and damp settle first. When blood cannot move through, the joint stiffens and grinds.",
            "Try this tonight. Wrap a warm towel around the knee for ten minutes, then walk gently for five.",
            "Comment clicking and I will send you my full cold and damp clearing protocol.",
        ],
        "notes": ["Clicks on standing", "寒濕困阻 · 血不通", "Warm wrap 10 min + gentle walk", "Comment 👇 clicking"],
        "first_dm": ("Hey! The warm wrap plus a short walk beats rest alone for stiff knees 🦵\n\n"
                     "Quick check — is your knee worse in cold damp weather, or worse after you have been sitting a long time?"),
        "infographic": ("Title: 'Knee Pain — Move the Cold Out'.\n"
                        "1) ROOT — knee icon; text: cold and damp settle in the joint. Blood cannot move through, so it stiffens and grinds.\n"
                        "2) WHAT WORSENS IT — snowflake icon; text: cold damp weather, sitting for hours, bare knees at night, too little movement.\n"
                        "3) NIGHTLY FIX — towel icon; text: warm wrap 10 minutes then walk gently 5 minutes, keep knees covered, ginger and cinnamon."),
        "second_dm": ("Here's your knee guide — warmth THEN movement, never rest alone 🚶\n\n"
                      "Want the joint-warming food list? Reply 'joint'."),
    },
    {
        "key": "knot",
        "name": "💆 Stiff Neck — The Knot Behind It",
        "topic": "🦴 Pain",
        "hook": "A stiff neck starts below the shoulder blade.",
        "wardrobe": "charcoal",
        "guest": ("a young woman guest in a cream ribbed top with long dark hair worn loose, "
                  "seated upright on a low wooden stool"),
        "guest_short": "the seated young woman guest in the cream top",
        "prop": "a smooth pale jade gua sha stone resting on a folded cloth",
        "actions": [
            "stands behind her right shoulder with one hand held just above the base of her neck",
            "stands at her left and rolls his OWN shoulder slowly to show the movement he wants her to copy",
            "holds up the pale jade gua sha stone toward camera and mimes a downward stroke beside his own neck",
        ],
        "script": [
            "She sits at a desk nine hours a day, and the stiffness is never actually in the neck itself.",
            "The knot sits below the shoulder blade. The neck is only where you feel it. Chasing the neck never releases it.",
            "Try this. Stroke downward from the base of the neck to the shoulder blade ten times on each side.",
            "Comment knot and I will send you my full shoulder and neck release protocol.",
        ],
        "notes": ["Feel it in the neck, fix the shoulder", "肩胛下結節", "Downward stroke x10 each side", "Comment 👇 knot"],
        "first_dm": ("Hey! The knot is almost always below the shoulder blade, not in the neck 💆\n\n"
                     "Quick check — does yours hurt more turning your head, or more lifting your arm?"),
        "infographic": ("Title: 'Stiff Neck — Release the Shoulder, Not the Neck'.\n"
                        "1) WHERE IT REALLY IS — shoulder icon; text: the knot sits below the shoulder blade. The neck is only where you feel it.\n"
                        "2) WHAT FEEDS IT — desk icon; text: long desk hours, phone tilt, cold draughts on the shoulders, shallow breathing, stress.\n"
                        "3) DAILY FIX — stone icon; text: stroke downward from neck base to shoulder blade 10 times each side, roll shoulders hourly."),
        "second_dm": ("Here's your neck guide — work the shoulder blade, the neck follows 🌿\n\n"
                      "Want the desk-posture reset? Reply 'desk'."),
    },
    {
        "key": "frozen",
        "name": "🧊 Frozen Shoulder — Why Rest Makes It Worse",
        "topic": "🦴 Pain",
        "hook": "Resting a frozen shoulder makes it worse.",
        "wardrobe": "navy",
        "guest": ("a middle-aged man guest in a plain dusty-blue polo shirt with short dark hair, "
                  "seated on a low wooden stool"),
        "guest_short": "the seated man guest in the dusty-blue polo",
        "prop": "a length of soft cotton strap coiled",
        "actions": [
            "stands at his left with one hand held near the guest's shoulder joint without touching it",
            "stands behind him and lifts his OWN arm slowly sideways to show the limited range",
            "holds the coiled cotton strap up toward camera and mimes a slow assisted arm raise",
        ],
        "script": [
            "He could not lift his arm to reach a shelf. Six months of resting it had made it tighter, not looser.",
            "A frozen shoulder is cold and stagnation locked in the joint. Stillness feeds it. Gentle movement is the medicine.",
            "Try this. Raise the arm slowly with a strap, only to where it feels tight, ten times a day. Never into sharp pain.",
            "Comment frozen and I will send you my full shoulder unlocking protocol.",
        ],
        "notes": ["Rest makes it worse", "寒凝氣滯 · 肩凝", "Strap raise x10 daily, never into pain", "Comment 👇 frozen"],
        "first_dm": ("Hey! Gentle daily movement unlocks a frozen shoulder — rest tightens it 🧊\n\n"
                     "Quick check — can you still lift the arm sideways, or does it stop partway?"),
        "infographic": ("Title: 'Frozen Shoulder — Movement Is the Medicine'.\n"
                        "1) ROOT — shoulder icon; text: cold and stagnation lock the joint. Stillness feeds it, gentle movement releases it.\n"
                        "2) WHAT WORSENS IT — pause icon; text: resting it completely, sleeping on that side, cold draughts, bracing against pain.\n"
                        "3) DAILY FIX — strap icon; text: slow assisted arm raises 10x daily only to the tight point, never into sharp pain, keep the shoulder warm."),
        "second_dm": ("Here's your shoulder guide — to the tight point, never into sharp pain 🌙\n\n"
                      "Want the warming rub recipe? Reply 'rub'."),
    },
    {
        "key": "swollen",
        "name": "🦶 Swollen Ankles — Where the Water Sits",
        "topic": "🦶 Feet / Legs",
        "hook": "Swollen ankles are a spleen signal.",
        "wardrobe": "oatmeal",
        "guest": ("an older woman guest in a soft lavender cardigan with short silver hair, "
                  "seated on a low wooden stool with her feet flat on the floor"),
        "guest_short": "the seated older woman guest in the lavender cardigan",
        "prop": "a shallow wooden basin of warm water",
        "actions": [
            "stands at her right with one open hand held above her ankle to indicate the swelling",
            "stands at her left and presses a fingertip into his OWN forearm to show how the dent stays",
            "gestures down toward the shallow wooden basin of warm water while facing camera",
        ],
        "script": [
            "By evening her ankles were so swollen that pressing a finger left a dent that stayed.",
            "That dent is the sign. The spleen moves water in the body. When it is weak, the water pools at the lowest point.",
            "Try this. Soak the feet in warm water for fifteen minutes, then lie down with the legs above the heart.",
            "Comment swollen and I will send you my full water moving protocol.",
        ],
        "notes": ["The dent that stays", "脾主運化水濕", "Warm soak + legs up", "Comment 👇 swollen"],
        "first_dm": ("Hey! The dent that stays is the sign to watch 🦶\n\n"
                     "Quick check — is it both ankles, or just one? One-sided swelling should be seen in person first."),
        "infographic": ("Title: 'Swollen Ankles — Move the Water'.\n"
                        "1) THE SIGN — footprint icon; text: press a finger in. If the dent stays, water is pooling at the lowest point.\n"
                        "2) ROOT — spleen icon; text: the spleen moves water through the body. When weak, fluid settles instead of circulating.\n"
                        "3) EVENING FIX — basin icon; text: warm foot soak 15 minutes, then legs above the heart 15 minutes, cut salt and cold raw food."),
        "second_dm": ("Here's your guide — soak THEN elevate, in that order 🌙\n\n"
                      "One-sided swelling, or with breathlessness, needs a doctor first. Reply 'water' for the food list."),
    },
    {
        "key": "sciatic",
        "name": "⚡ Sciatica — The Line Down the Leg",
        "topic": "🦴 Pain",
        "hook": "Sciatica follows a line, not a spot.",
        "wardrobe": "charcoal",
        "guest": ("a man guest in his forties in a plain olive t-shirt with short cropped hair, "
                  "seated on a low wooden stool leaning slightly to one side"),
        "guest_short": "the seated man guest in the olive t-shirt",
        "prop": "a rolled bamboo mat standing against the dark walnut desk",
        "actions": [
            "stands behind his left shoulder with an open hand held near the top of the guest's hip",
            "stands at his right and traces a line down his OWN hip and outer thigh to show the path",
            "mimes a slow seated figure-four stretch with his hands while facing camera",
        ],
        "script": [
            "He described it perfectly. Not a sore spot, but a line of fire running from the hip down the back of the leg.",
            "That line is the gallbladder and bladder channel. Cold and stagnation press on it, and the pain travels the whole path.",
            "Try this. Cross the ankle over the opposite knee, sit tall, and lean forward gently for thirty seconds each side.",
            "Comment sciatic and I will send you my full channel opening protocol.",
        ],
        "notes": ["A line, not a spot", "膽經 + 膀胱經", "Figure-four, 30s each side", "Comment 👇 sciatic"],
        "first_dm": ("Hey! Sciatica follows a channel — that is why chasing one sore spot never works ⚡\n\n"
                     "Quick check — does the line run down the BACK of your leg, or down the OUTSIDE?"),
        "infographic": ("Title: 'Sciatica — Open the Channel'.\n"
                        "1) THE PATTERN — leg icon; text: a line of pain from hip down the leg, not a single sore spot. It follows a channel.\n"
                        "2) ROOT — channel icon; text: cold and stagnation press on the gallbladder and bladder channels, so pain travels the whole path.\n"
                        "3) DAILY FIX — stretch icon; text: figure-four stretch 30 seconds each side, keep the hip warm, stand up every hour."),
        "second_dm": ("Here's your sciatica guide — gently, and stop before sharp pain 🌿\n\n"
                      "Numbness or weakness in the leg needs in-person care first. Reply 'channel' for the full routine."),
    },
    {
        "key": "wrist",
        "name": "✋ Wrist and Thumb Pain — The Phone Grip",
        "topic": "🦴 Pain",
        "hook": "Your wrist pain starts at the thumb.",
        "wardrobe": "navy",
        "guest": ("a young man guest in a plain white tee with short dark hair, seated on a low "
                  "wooden stool holding one wrist in the other hand"),
        "guest_short": "the seated young man guest in the white tee",
        "prop": "a small linen bag of warm rice",
        "actions": [
            "stands at his right with an open hand held near the guest's wrist",
            "stands at his left and folds his OWN thumb into his palm to show the test",
            "picks up the small linen bag of warm rice and mimes resting it on his own wrist",
        ],
        "script": [
            "He holds his phone the same way for hours, and now the pain runs from the thumb into the wrist.",
            "Tuck the thumb into the palm and bend the wrist down. If that stings sharply, the tendon sheath is inflamed, not the joint.",
            "Try this. Rest a warm rice bag on the wrist for ten minutes, then move the thumb in slow wide circles.",
            "Comment wrist and I will send you my full tendon calming protocol.",
        ],
        "notes": ["Starts at the thumb", "筋鞘 not 關節", "Warm rice bag + thumb circles", "Comment 👇 wrist"],
        "first_dm": ("Hey! Tuck the thumb in and bend the wrist down — if that stings, it is the tendon sheath ✋\n\n"
                     "Quick check — does the pain run up the forearm, or stay right at the wrist?"),
        "infographic": ("Title: 'Wrist and Thumb Pain — Calm the Tendon'.\n"
                        "1) THE TEST — hand icon; text: tuck the thumb into the palm and bend the wrist down. A sharp sting means the tendon sheath, not the joint.\n"
                        "2) WHAT FEEDS IT — phone icon; text: long one-handed phone grip, repetitive lifting, cold hands, no rest between tasks.\n"
                        "3) DAILY FIX — warm bag icon; text: warm rice bag 10 minutes, slow wide thumb circles, switch grip hands, rest between tasks."),
        "second_dm": ("Here's your wrist guide — warmth then gentle motion, never forced stretching 🌿\n\n"
                      "Want the desk and grip fixes? Reply 'grip'."),
    },
    {
        "key": "firststep",
        "name": "🦶 Heel Pain — Worse on the First Step",
        "topic": "🦶 Feet / Legs",
        "hook": "Heel pain is worst on the first step.",
        "wardrobe": "oatmeal",
        "guest": ("a woman guest in her fifties in a simple terracotta blouse with hair in a low bun, "
                  "seated on a low wooden stool with one foot resting on a small footstool"),
        "guest_short": "the seated woman guest in the terracotta blouse",
        "prop": "a smooth wooden foot roller",
        "actions": [
            "stands at her right with an open hand held near the guest's heel",
            "stands at her left and presses a thumb into his OWN palm to show where the ache maps",
            "sets the smooth wooden foot roller on the floor and mimes rolling his own foot over it",
        ],
        "script": [
            "The first few steps out of bed were the worst part of her whole day. After walking a while it eased.",
            "That pattern tells me the tissue tightens overnight. The kidney channel begins at the sole, and it is running dry.",
            "Try this. Before your feet touch the floor, roll each foot over a bottle or roller thirty times.",
            "Comment firststep and I will send you my full sole and kidney protocol.",
        ],
        "notes": ["Worst on the first step", "腎經起於足底", "Roll 30x BEFORE standing", "Comment 👇 firststep"],
        "first_dm": ("Hey! Roll the foot BEFORE your feet touch the floor — that order is the whole trick 🦶\n\n"
                     "Quick check — is it worst on the first steps of the day, or worse the longer you stand?"),
        "infographic": ("Title: 'Heel Pain — Roll Before You Stand'.\n"
                        "1) THE PATTERN — sunrise icon; text: worst on the first steps of the day, easing as you walk. The tissue tightens overnight.\n"
                        "2) ROOT — sole icon; text: the kidney channel begins at the sole. When it runs dry the tissue loses its give.\n"
                        "3) MORNING FIX — roller icon; text: roll each foot 30 times BEFORE standing, warm soak at night, black sesame and walnut."),
        "second_dm": ("Here's your heel guide — the roll goes before the first step, not after 🌅\n\n"
                      "Want the nourishing food list? Reply 'sole'."),
    },
    {
        "key": "tension",
        "name": "😣 Tension Headache — The Band Around Your Head",
        "topic": "🦴 Pain",
        "hook": "A band around the head is not a migraine.",
        "wardrobe": "charcoal",
        "guest": ("a woman guest in her thirties in a soft slate-blue top with shoulder-length dark hair, "
                  "seated on a low wooden stool"),
        "guest_short": "the seated woman guest in the slate-blue top",
        "prop": "a small celadon dish of dried chrysanthemum flowers",
        "actions": [
            "stands behind her right shoulder with both open hands held wide apart beside her head, not touching",
            "stands at her left and draws a slow band shape in the air around his OWN head",
            "raises one hand to shoulder height and mimes a slow press at the base of the skull, arm clear of his face",
        ],
        "script": [
            "She described a tight band squeezing all the way around her head. That is not a migraine at all.",
            "A band means tension, not fire. It builds where the neck meets the skull, and it tightens all day as you brace.",
            "Try this. Press the two hollows at the base of your skull with your thumbs for one slow minute.",
            "Comment tension and I will send you my full headache release protocol.",
        ],
        "notes": ["A band, not a migraine", "風池 · 頸枕交界", "Thumb press 1 min at skull base", "Comment 👇 tension"],
        "first_dm": ("Hey! A band around the head is tension, not migraine — different fix entirely 😣\n\n"
                     "Quick check — is it a tight BAND all around, or a throbbing on ONE side?"),
        "infographic": ("Title: 'Tension Headache — Release the Skull Base'.\n"
                        "1) TELL THEM APART — head icon; text: a tight band all around is tension. Throbbing on one side with light sensitivity is migraine.\n"
                        "2) WHERE IT BUILDS — neck icon; text: where the neck meets the skull. Bracing, screens and shallow breathing tighten it all day.\n"
                        "3) DAILY FIX — thumbs icon; text: press the two hollows at the skull base 1 slow minute, chrysanthemum tea, unclench the jaw."),
        "second_dm": ("Here's your headache guide — band and throb are different problems, treat the right one 🌿\n\n"
                      "Want the jaw and screen reset? Reply 'band'."),
    },
    {
        "key": "posture",
        "name": "🧍 Rounded Shoulders — Why You Cannot Stand Straight",
        "topic": "🦴 Pain",
        "hook": "You cannot fix posture by pulling your shoulders back.",
        "wardrobe": "navy",
        "guest": ("a young man guest in a plain charcoal sweatshirt with short hair, seated forward "
                  "on a low wooden stool with rounded shoulders"),
        "guest_short": "the seated young man guest in the charcoal sweatshirt",
        "prop": "a rolled hand towel standing upright",
        "actions": [
            "stands behind him with both open hands held just behind the guest's shoulders, not touching",
            "stands at his right and rounds his OWN shoulders forward then opens his chest to show the contrast",
            "holds the rolled hand towel up toward camera and mimes placing it along his own spine",
        ],
        "script": [
            "He kept being told to pull his shoulders back. Ten seconds later they rounded forward again every time.",
            "Pulling back fights the wrong muscle. The front of the chest is short, so the back can never win that argument.",
            "Try this. Lie on a rolled towel along your spine for five minutes and just let the chest fall open.",
            "Comment posture and I will send you my full chest opening protocol.",
        ],
        "notes": ["Stop pulling back", "胸前緊 · 背後拉不贏", "Rolled towel along spine 5 min", "Comment 👇 posture"],
        "first_dm": ("Hey! Pulling the shoulders back fights the wrong muscle — open the chest instead 🧍\n\n"
                     "Quick check — do your shoulders round more when you are tired, or all day regardless?"),
        "infographic": ("Title: 'Rounded Shoulders — Open the Front, Not the Back'.\n"
                        "1) WHY PULLING BACK FAILS — arrow icon; text: the front of the chest is short. The back muscles can never win that argument by force.\n"
                        "2) WHAT SHORTENS IT — desk icon; text: desk hours, phone tilt, driving, carrying on one side, shallow chest breathing.\n"
                        "3) DAILY FIX — towel icon; text: lie on a rolled towel along the spine 5 minutes and let the chest fall open, breathe into the ribs."),
        "second_dm": ("Here's your posture guide — open the front and the back stops fighting 🌿\n\n"
                      "Want the desk setup fixes? Reply 'desk'."),
    },
]
