---
name: ig-reel-editor
description: >-
  Edit an Instagram Reel end-to-end with Claude in the creator's OWN brand style. Use this skill
  whenever the user wants to edit a short-form vertical video with AI/Claude, add motion graphics
  or animated overlays to a talking-head or faceless Reel, "teach Claude my brand/style," turn a
  script + voiceover into a finished 9:16 edit, plan b-roll and on-screen graphics for a Reel, or
  set up a repeatable editing system for short-form content. Triggers on phrases like "edit this
  Reel with Claude," "add motion graphics," "make my Reels look like X," "build my editing style,"
  "plan the visuals for my Reel script," "brand my Reel templates," or "set up my short-form
  edit workflow." Brand-agnostic: it builds each user's Visual Style Profile from their brand
  guide, screenshots, or a short questionnaire, then plans and builds the edit in that brand.
  Prefer this skill over ad-hoc editing whenever brand-consistent motion graphics are wanted.
---

# IG Reel Editor

A runnable, **brand-agnostic** system for editing Instagram Reels (9:16 vertical, ≤90s) with Claude.
Teach Claude a brand once, then plan and build the motion-graphics edit for every future Reel in that brand.

**Canvas:** 1080 × 1920 px · 9:16 · 30fps · ≤90s (sweet spot: 30–60s)

**How it builds good scenes:** Claude does **not** assemble Reels from pre-made parts. It **authors
each scene freely in HyperFrames and imitates the gold-standard anchor inlined at the end of this file** —
the same way the script engine imitates locked script anchors. Free authoring + a high bar = cinematic
output, not thin slides.

## The two layers
1. **The system** (this skill) — universal. No brand specifics live here.
2. **The brand input** — each user's filled **Visual Style Profile** + **brand tokens** (`--brand-bg`,
   `--brand-accent`, `--brand-font-display`, …). Fill the blank profile below. Use the inlined
   **showcase anchor** (end of this file) as your quality bar — imitate its **density/craft**, re-skin
   the **look** to your tokens.

## What this skill produces
- **Once per brand:** a filled **Visual Style Profile** + **brand tokens**.
- **Per Reel:** an approved **storyboard + visual plan**, then **rendered scene MP4s** (avatar +
  graphics composited), an **asset shopping list**, **sound design**, and a short **CapCut assembly order**.

---

## Hard gates — NON-NEGOTIABLE, never skip
Three mandatory stop points. A run MUST NOT generate images/video, author any composition, or render
**until all three gates are explicitly passed by the user**:
0. **Brand gate (Step 0) — FIRST, always.** Colors, fonts, look. Never invent or assume a palette/font.
1. **Direction gate (Step 1.5)** — visual building blocks + style, then WAIT for the pick.
2. **Storyboard gate (Step 2b)** — storyboard + per-beat treatment menu, then WAIT for approval.

Never collapse the gates. If the user hasn't passed a gate, ask its question and stop.

## Run discipline — show the to-do list first ⭐
Seed a visible TodoWrite checklist before Step 0:
1. Preflight (first run on machine only) — ffmpeg · Whisper · HyperFrames · Node
2. **Gate 0 — Brand:** filled Style Profile + brand tokens exist
3. **Gate 1.5a — Direction:** visual building blocks chosen
4. **Gate 1.5b — Direction:** avatar presence (FULL/SIDE/OUT lean) chosen
5. **Gate 1.5c — Direction:** captions choice (word-by-word / payoff-only / none)
6. **Gate 1.5d — Direction:** IF images/video → image style + animation + model chosen
7. **Gate 2b — Storyboard:** storyboard + treatment menu presented and approved
8. **Gate 2-B2 — Mockup:** one still-per-key-animation look check approved
9. Author scenes → assets → sound → assembly

---

## Step 0 — Brand gate / Brand Intake (MANDATORY · non-skippable · FIRST)

Accept any combination of brand material:
1. **Brand guide** (PDF / doc / Notion) — authoritative for color + type
2. **Reference images / screenshots** — the look (glow, captions, cards, layout)
3. **Questionnaire** — the Brand intake questionnaire section (12 plain questions)

Priority: **brand guide > images > questionnaire.** Unknown values → write `⚠️ NEEDS INPUT`, ask one question.

**Output:** save filled profile + brand tokens block. Everything downstream reads these.

---

## Step 1 — Inputs ready
Confirm the user has the **final script** and the **AI voiceover** (or talking-head clip).

**IG Reel constraints:**
- Total duration: ≤90s. Sweet spot for knowledge content: 30–60s.
- First **1.5s** must hook visually — IG autoplays muted. The first frame IS the hook.
- No intros longer than 2s. Get to the value immediately.
- Captions are expected on IG (85% of Reels are watched without sound).

---

## Step 1.5 — Direction gate (MANDATORY · ASK before storyboarding) ⭐
Ask these and WAIT before building any storyboard:

1. **Visual building blocks for this Reel?**
   - Motion graphics only — captions, cards, numbers, kinetic type
   - Motion graphics + images — add AI-generated stills
   - Motion graphics + images + reference video — also real clips / screen-recordings
   - Image-led / video-led — visuals carry it; motion graphics are the accent

2. **If images or video → style + animation? (REQUIRED sub-gate — ASK, never default)**
   - Style: 2D animated sketch · cinematic photoreal · 3D/claymation · real screenshots
   - Animation (images are NEVER static): draw-on reveal · Ken Burns push-in · image-to-video (Seedance)
   - Model: GPT Image 2 (default) · Nano Banana Pro @ 4K (fallback)

3. **Avatar/host presence?**
   - FULL (talking head dominates — most Reels)
   - SIDE (avatar + graphic split — works in 9:16 as top/bottom or left/right)
   - OUT (avatar gone; graphic or b-roll full-frame)

4. **Caption style?**
   - Word-by-word (TikTok/IG standard — recommended)
   - Setup + payoff (two-tone: grey setup, accent payoff word)
   - Payoff moments only
   - None

Record answers. The storyboard is built to match.

---

## Step 2 — Transcribe → Storyboard (approve) → Plan ⭐

**2a. Transcribe** with Whisper (local, no key):
```python
import whisper, json
model = whisper.load_model("base.en")
res = model.transcribe("PATH/TO/reel_vo.mp4", verbose=False, word_timestamps=True)
segs = [{"start": round(s["start"],2), "end": round(s["end"],2), "text": s["text"].strip()} for s in res["segments"]]
json.dump(segs, open("transcript.json","w"), indent=1)
```

**2b. Storyboard FIRST — get approval — do NOT build yet. (MANDATORY gate.)**

**IG Reel storyboard format:**

| # | Time | Line (abbrev) | Avatar | Asset type | What to show |
|---|---|---|---|---|---|

Beat treatments: `AVATAR` · `MOTION GRAPHIC` · `IMAGE` · `SOURCE (screen-rec/clip)`

**IG-specific storyboard rules:**
- **Beat 1 (0–1.5s):** always a HOOK beat — big claim, number, or pattern-break. No logo, no intro. Visual hook even if muted.
- **Analyze first:** most lines get NO graphic. Only crucial-to-understand lines earn a visual. Over-animating is the #1 amateur tell.
- **Max 4–6 graphic beats** for a 30–60s Reel.
- **Every graphic out before the next sentence starts** — Reels have no patience for stale frames.
- State explicitly per beat if NO image needed and why.

**Per-beat retention job:** number-bomb / claim / evidence / mechanism / consequence / bridge / payoff

**Always surface the treatment menu at approval:**
> **Each beat can be: `avatar` · `motion-graphic` · `generate` (AI image/video) · `source` (real clip/screenshot).**
> Currently planned: [N motion graphics, N images, N screen-recs]. Want to change any beat? Tell me the beat and what you picture.

**2c. Plan with story + craft.** Every beat: retention job → avatar position → treatment → what it shows → timestamp (word-accurate).

---

## Step 3 — Author the scenes ⭐

**Read the inlined showcase anchor (end of this file) before authoring — it is the bar.**

Author each scene in HyperFrames at **1080 × 1920** (9:16 canvas).

**9:16-specific authoring rules:**
- **Canvas is tall, not wide.** Stack elements vertically. Horizontal layouts break.
- **Text wraps sooner** — max ~18–20 chars per line at large size. Use shorter lines.
- **The avatar** sits in the upper 50–60% of the frame in FULL mode; graphics live in the lower 40% (or full-frame for OUT).
- **Kinetic captions** sit at 70–80% from top (lower-third = IG standard; avoid bottom 200px for navigation bar).
- **B-roll** fills the full 1080×1920 frame.
- **Cards/overlays** are narrower (max 960px wide, padded 60px each side).
- **Camera motion on held shots** — slow upward drift (y: -2–3%) or scale push (1.0→1.04) so nothing is ever perfectly static.

### Pre-render quality gate
- [ ] Canvas is 1080 × 1920 · 30fps
- [ ] Hero element BIG: headlines 80–120px, hero numbers 160–220px (scaled for 1080px wide)
- [ ] First frame IS the hook — grabs attention muted
- [ ] Captions sit at ~75% from top, readable on mobile
- [ ] Smooth in AND out (eased, overlapping, no empty frames)
- [ ] Camera motion on every held visual
- [ ] On-brand tokens + fonts embedded

---

## Step 4 — Fill the asset layer
- **generate** → GPT Image 2 (default); Nano Banana Pro @ 4K (fallback); Seedance for motion. Generate 9:16 (1080×1920) or crop from 16:9. Animate — no static slides.
- **source** → tell user exactly what to capture (screen-rec, clip), with filename + destination.

---

## Step 5 — Sound design
- **Whoosh** on graphic entrances
- **Pop/tick** on element-ins
- **Music bed** ~−18 dB (slightly louder than YouTube — Reels compete with music)
- **No long silence** — Reels without audio feel dead; even ambient music helps
- Bake SFX into HyperFrames scenes where possible

---

## Step 6 — Final assembly (CapCut → IG)
Scenes render with canvas + avatar + graphics composited. CapCut is light:
1. Sequence rendered scenes
2. Sync voiceover
3. Add music bed (~−18 dB)
4. Add auto-captions (CapCut's word-by-word, if not baked in)
5. Export: **1080×1920 · H.264 · 30fps · ≤90s** for IG Reels
6. First 3s = cover frame preview in IG — pick this carefully (not a blank/dark frame)

---

## Sharing / rebranding
New user runs Step 0 with their own brand; nothing in the system changes.

---

# 📎 Inlined references

---

# The IG Reel Editing System — Overview

> A brand-agnostic system for editing Instagram Reels with Claude. Teach Claude your brand once,
> then plan and build the motion-graphics edit for every future Reel in your style.

**Canvas:** 1080 × 1920 · 9:16 · 30fps · ≤90s

| Step | Name | Output |
|---|---|---|
| **0** | Brand Intake | Filled Style Profile + brand tokens |
| **1** | Inputs ready | Final script + AI voiceover (≤90s) |
| **2** | Plan the visuals ⭐ | Beat-by-beat plan; 4–6 graphic beats max |
| **3** | Build motion graphics | Rendered 9:16 components in brand tokens |
| **4** | Fill asset layer | Generated (GPT/Nano/Seedance) + sourced clips |
| **5** | Sound design | Whoosh + pop + music bed (−18 dB) |
| **6** | Final assembly | CapCut → export 1080×1920 H.264 ≤90s |

---

# Step 0 — Setup Preflight

| Need | For | Check | If missing |
|---|---|---|---|
| **ffmpeg** | trim audio, frames | `ffmpeg -version` | brew/apt install ffmpeg |
| **Whisper** | word timestamps | `python -c "import whisper"` | `pip install -U openai-whisper` |
| **HyperFrames CLI** | build 9:16 scenes | `npx hyperframes --version` | `npx hyperframes init` |
| **Node** | runs HyperFrames | `node -v` | install Node LTS |
| **Image gen** (optional) | generate beats | image-gen MCP connected? | fallback: motion graphic |

**Degraded paths:**
- No Whisper: paste script with rough timing.
- No image-gen: use motion graphics for those beats.
- Claude.ai only: can transcribe-plan-storyboard but not render locally.

---

# Step 0 — Brand Intake

Same as original skill (brand guide > images > questionnaire priority). See below for the IG-adapted questionnaire.

## Brand tokens (9:16 kit reads these)
```
--brand-bg:           /* base background */
--brand-accent:       /* primary pop color */
--brand-accent-2:     /* secondary accent */
--brand-glow:         /* glow/halo color */
--brand-text:         /* main text color */
--brand-text-muted:   /* setup / secondary text */
--brand-font-display: /* big titles + caption payoff */
--brand-font-body:    /* body / secondary text */
--brand-font-mono:    /* small labels */
--brand-radius:       /* card & pill corner rounding */
--brand-glass-bg:     /* glassmorphism fill */
--brand-glass-border: /* glassmorphism border */
```

---

# [BRAND NAME] — Visual Style Profile (IG Reel)

## Brand tokens
```
--brand-bg:           /* dark or light, warm or cool */
--brand-accent:
--brand-accent-2:
--brand-glow:
--brand-text:
--brand-text-muted:
--brand-font-display:
--brand-font-body:
--brand-font-mono:
--brand-radius:
--brand-glass-bg:
--brand-glass-border:
```

## 0. One-line identity
`______`

## 1. Color world
- **Base:** dark / light · warm / cool · hex: `____`
- **Accent:** hex `____`
- **Glow:** yes / no · color `____`
- **Text:** main `____` · muted `____`
- **Forbidden:** `____`

## 2. Typography
- **Display font:** `____` — serif / sans?
- **Body font:** `____`
- **Hard rule:** `____`

## 3. Caption style (IG-specific)
- Word-by-word / two-tone setup+payoff / payoff-only / none?
- Position: lower-third (recommended) / center / other?
- Every line / key moments only?

## 4. Motion-graphic kit elements
- [ ] Word-by-word kinetic captions (IG standard)
- [ ] Numbered section cards (#1, #2…)
- [ ] Glassmorphism pills / labels
- [ ] List-card stacks (2–3 items — keep short for vertical)
- [ ] Bullet rows
- [ ] Full-frame text cards (OUT beat)
- [ ] Animated hook title (first 1.5s)
- [ ] CTA card (last 3s — "Comment X", "Follow", "Save this")
- [ ] Other: `____`

## 5. Asset layer (b-roll)
- B-roll: none / sparse / heavy?
- Generated sources: GPT Image 2 / Nano Banana Pro / Seedance / other?
- When to SOURCE real assets: `____`

## 6. Pacing (IG-specific)
- Max seconds without a visual change: `____` (recommended: 4–5s max)
- Hook duration: `____` (recommended: ≤1.5s before value starts)

## 7. Sound
- Whoosh on entrances? yes / no
- Pop/tick? yes / no
- Music bed level: `____` (recommended: −18 dB for Reels)

## 8. Non-negotiables
1. `____`
2. `____`
3. `____`

## Host
- Real face / avatar / none?
- Frame position (FULL talking-head): upper 55% / upper 65% / other?

---

# Brand Intake Questionnaire (IG Reel)

## Colors
1. Dark or light background? Warm or cool?
2. Main accent color (name or hex)?
3. Second accent?
4. Glow/halo effect or flat/clean?
5. Off-limits colors?

## Type
6. Headline/title font? Serif or sans-serif?
7. Any hard font rule?

## Captions
8. Word-by-word captions (TikTok/IG style) or payoff-only or none?
9. Caption position: lower-third standard, or centered?

## The kit
10. Which do you already use or want? *Word-by-word kinetic captions · numbered section cards · glassy pills · 2–3 item lists · bullet rows · full-frame text cards · animated hook · CTA card*

## B-roll
11. How much b-roll — none, sparse, or heavy? AI-generated or real footage or both?

## Feel
12. Three words for the vibe. (e.g. "calm, premium, medical" / "bold, fast, informative")

---

# Transcription + Storyboard

## A. Transcribe with word timestamps
```python
import whisper, json
model = whisper.load_model("base.en")
res = model.transcribe("reel.mp4", verbose=False, word_timestamps=True)
# Flatten to word level for graphic-on-word precision
words = []
for seg in res["segments"]:
    for w in seg.get("words", []):
        words.append({"word": w["word"].strip(), "start": round(w["start"],2), "end": round(w["end"],2)})
json.dump(words, open("words.json","w"), indent=1)
print(len(words), "words")
```

## B. Storyboard (then get approval)

### B0 — Analyze first: most lines get NO graphic
For a 45s Reel, ~4–6 lines are crucial; the rest is avatar. Ask per line: **"Is this crucial for the viewer to understand?"**
- **concept** line → introduce it (title card, icon, number)
- **explanation** line → represent it (list, comparison, mechanism)

IG-specific: also ask: **"Does this line need a caption graphic even if it's avatar-only?"** (Reels viewers often watch muted → captions on every line may be needed even if no other graphic.)

### IG Reel storyboard table
| # | Time | She says (abbrev) | Avatar | Graphic | Caption | What to build |
|---|---|---|---|---|---|---|

Avatar states for 9:16:
- **FULL** — host fills upper ~60% of frame; lower 40% open for graphics
- **SIDE** — host left or top half; graphic right or bottom half (works in portrait if vertical split: top host / bottom graphic)
- **OUT** — host gone; graphic or b-roll full 1080×1920

### IG Reel asset shopping list
- MOTION GRAPHICS: (list components)
- IMAGES to generate: (or "none — abstract, no pictorial subject")
- B-ROLL / SOURCE clips: (exact screens or footage)
- CAPTIONS: (word-by-word on all lines / payoff lines only)
- CTA CARD: (last 3s — what's the comment keyword or CTA)
- AVATAR: (already have)

**STOP. Get approval before building.** Present the treatment menu:
> **Each beat: `avatar` · `motion-graphic` · `generate` · `source`.** Currently: [N motion graphics, N images, N source]. Change any beat?

### B2 — Mockup gate
Render one still per key animation. Review look (brand, layout, font size, avatar frame) before building all scenes.

---

# Storytelling / Direction Layer (IG Reel)

> Adapted from the YouTube direction layer for short-form vertical. The core grammar is the same
> (CLAIM→EVIDENCE→MECHANISM); the pacing is compressed. Anchored in high-performing educational Reels.

## Core principle
> **A visual is a retention device, not decoration.** On IG Reels, you have 1.5s to earn the next
> 1.5s. Every frame must earn its stay.

## 1. The IG Reel opening grammar (first 1.5s decide everything)
Unlike YouTube (15s), IG gives you **1.5s** before the thumb-stop decision.

**Structure:** Visual hook → micro-pattern-break → curiosity lock → implicit promise

- **Visual hook (0–0.5s):** big number, bold claim on screen, or unexpected visual — even if muted.
  e.g. "Your liver is why your eyes hurt." / "3 types of migraine. Most doctors treat all the same."
- **Micro-pattern-break (0.5–1.0s):** the thing that's counterintuitive. One sentence.
- **Curiosity lock (1.0–1.5s):** the viewer must feel "I don't know the end of this" — plant the gap.
- **No intro, no name, no logo** in the first 3s. Jump straight to the value.

Direction: Beat 1 always `OUT` or `FULL-with-big-text`. Hook claim = on-screen, **on the word**.

## 2. The core retention unit: CLAIM → EVIDENCE → MECHANISM
Same as YouTube, compressed for Reels:
1. **Claim** (1 sentence) → avatar FULL, caption on the contrarian payoff word
2. **Evidence** (1–2 sentences) → avatar SIDE or OUT, visual proof (number, card, list)
3. **Mechanism** (1–2 sentences) → list-stack or bullets, the *why*

## 3. Recurring retention beats
| Beat | Example | Visual | Timing |
|---|---|---|---|
| **Number bomb** | "1 in 3 migraines is misdiagnosed" | big number callout, full-frame | on the number word |
| **Pattern-break** | "Eye drops treat symptoms. Not the organ." | caption flip | on the snap |
| **Mechanism** | "Liver Blood feeds the eyes" | list or diagram card | builds as said |
| **Signpost** | "Here's what actually works:" | clean reset, accent rule | on "works" |
| **CTA** | "Comment 'eye'" | CTA card with keyword highlighted | last 3s |

## 4. Section bridges
Short Reels rarely have more than 2–3 sections. Bridge with a single sentence that opens the next gap:
*"But knowing the type isn't enough — here's the fix."*

## 5. Structural devices for Reels
- **Rule of 3** — 3 types, 3 symptoms, 3 steps. Visuals come in threes.
- **Consequence per point** — "if you don't know your type, the remedy won't work."
- **Withhold** — pose the question visually, hold ~0.5s on avatar, then drop the answer graphic.

## 6. Pacing / cadence
- Never >4s with zero visual change on IG (vs 6s on YouTube).
- Withhold timing shorter: ~0.5–1s (not 1–2s as on YouTube).
- CTA card always appears in last 3–4s.

## 7. How the planner uses this
Same as YouTube version — retention job per beat, place graphic on key word, withhold answer ~0.5s.

---

# Editing Principles (IG Reel Craft Layer)

## 0. The non-negotiable feel
**Big. Smooth. Cinematic. Earns every second.** On IG, "meh" = swipe. There is no "good enough."

## 1. Four visual treatments
| Treatment | What | Use when |
|---|---|---|
| **Avatar (A-roll)** | host in upper frame | talking beats with no stronger visual |
| **Motion graphic** | cards, captions, numbers | abstract ideas, structure, data |
| **Generated image/video** | AI-created picture, animated | concept needs a *picture* (default: GPT Image 2; Seedance for motion) |
| **Source / real footage** | real clip, screenshot | viewer must recognize a real, specific thing |

> Images are a deliberate choice — not a default. Many Reels need NO images; pure motion graphics + avatar is often stronger. State per beat if no image needed and why.

### Animate b-roll (never a static slide)
- Slow push-in (Ken Burns): 2–4% scale over clip duration
- Vertical parallax: foreground/background drift at different speeds (works well in 9:16)
- Mask/wipe reveal
- Rounded brand frame or full-bleed with grade

## 2. Scale / legibility (9:16 at 1080px wide)
- **Headlines:** 80–120px. Hero numbers: 160–220px.
- **Card titles:** 40px+. Card body: 26px+. Labels: 22px+.
- **Line width:** ≤960px (60px padding each side). Shorter lines — ~15–18 chars at large size.
- **One big thing beats five small things.** If it matters, make it large and isolated.
- **Mobile check:** imagine it on a 375px screen (2.88× downscale). Still readable?

## 3. Smooth flow in & out
- Everything eases. Entrances 0.4–0.6s (`back.out`, `power3.out`); exits 0.25–0.35s (`power2.in`).
- Overlap entrances/exits (150–250ms overlap) — no empty frames.
- Directional wipes and vertical pushes work naturally in 9:16.
- One hero element moves at a time.

## 4. Cinematic feel (9:16 specific)
- **Vertical depth:** foreground elements (captions, cards) at bottom; background glow/blur behind avatar.
- **Camera motion on held visuals** — slow upward drift (y -2%) or push-in on b-roll.
- **Grade consistency** — one warm-dark grade across everything.
- **Sound** — even 0.5s whoosh makes a graphic feel intentional.

## 5. Tells a story — in ≤90s
- Hook → tension → payoff. No meandering.
- Each visual ADVANCES the argument. If it doesn't, cut it.
- Escalate toward payoffs — bigger emphasis as the section climaxes.

## 6. Supporting principles
- **Over-animating is the #1 amateur tell** — 4–6 graphic beats max for a 45s Reel.
- **Visual hierarchy:** one focal point per beat.
- **Reading time:** text shows exactly as long as the VO — synced to the word.
- **Consistency:** the steady avatar anchor + repeating card systems.
- **Restraint:** big elements + breathing room. Clutter kills focus.

## 7. Avatar moves NATURALLY — FULL / SIDE / OUT (9:16 variant)

**FULL:** Host fills upper 55–65% of frame. Lower 35–45% is open for graphics (captions, cards, CTA).
Use for hook, direct points, the CTA.

**OUT:** Host gone. Full 1080×1920 frame owned by graphic or b-roll. Use for mechanism beats, lists, data.

**SIDE (vertical 9:16 variant):**
- *Left/right split:* host takes left 50%, graphic takes right 50%. Works for comparisons.
- *Top/bottom split:* host takes upper 50%, graphic fills lower 50%. Works for caption-heavy beats.
- Use sparingly — the dominant rhythm is FULL ↔ OUT.

**Same failure modes:** stuck in one position (dead), or bouncing every beat (nervous).
Move with **motivation** — when the content changes who should own the screen.

---

# HyperFrames Build Standards (9:16)

## 0. Quality bar = anchor scenes
Calibrate to the inlined 9:16 showcase anchor at the end of this file.

## 1. FONTS — load every time
```html
<link rel="preconnect" href="https://fonts.googleapis.com">
<link href="https://fonts.googleapis.com/css2?family=Your+Display+Font:wght@400;700&family=Your+Body+Font:wght@400;500&display=swap" rel="stylesheet">
```
Use **literal font names** in CSS — never `var(--font)` alone. Tokens for color/radius; literals for font-family.

## 2. Background — layered & textured (9:16)
```css
.bg-canvas{
  position:absolute; inset:0; z-index:0;
  background:
    radial-gradient(ellipse 80% 40% at 50% 20%, rgba(232,162,74,0.16), transparent 55%),
    radial-gradient(ellipse 60% 35% at 80% 85%, rgba(232,162,74,0.12), transparent 55%),
    radial-gradient(ellipse 100% 70% at 50% 50%, #15151c 0%, #0e0e13 55%, #0b0b0f 100%);
}
/* Grid + grain same as YouTube version — scales to any canvas */
```
Note: in 9:16, glows sit at top 20% (behind avatar) and bottom 85% (behind graphics area).

## 3. Animation — every element choreographed
Same patterns as YouTube version; vertical axes matter more in 9:16:
- **Caption words:** `y:20, opacity:0` → in (not `y:50` — less travel on tall canvas)
- **Cards:** `y:40, opacity:0, back.out(1.5)` (slide up from bottom)
- **Numbers:** count-up slam, same pattern
- **Full-frame OUT beats:** wipe from bottom (vertical reveal, natural in 9:16)

## 4. Timing — word-accurate
Same as YouTube: Whisper word timestamps, land each graphic on the spoken word.

## 5. Caption placement
```css
.caption-layer {
  position: absolute;
  bottom: 220px;          /* above IG navigation bar (~200px) */
  left: 60px;
  right: 60px;
  text-align: center;
  z-index: 10;
}
```

## 6. Approval — scrollable visual storyboard
Same as YouTube version: plain HTML page, real rendered frame per beat, ~2 across (portrait), numbered.

---

# Re-skin to YOUR brand (9:16)

Same as YouTube version:
1. Swap the token block (`--brand-bg`, `--brand-accent`, etc.)
2. Fix FONT literals (not just `var()`)
3. Render one frame, eyeball it

Quick checklist:
- [ ] Token block swapped
- [ ] Font literals swapped + fonts embed correctly
- [ ] One frame rendered + verified (colors, typeface, layout)
- [ ] No off-brand colors from example defaults

---

# 📎 Inlined anchor — 9:16 quality bar (read this in Step 3)

Match its density/craft; invent beyond it. Canvas: 1080 × 1920.

```html
<!doctype html>
<html lang="en">
<head><meta charset="utf-8" /><title>Anchor — IG Reel Scene Showcase (9:16)</title></head>
<body style="margin:0;background:#0b0b0f;">
<!--
  NEUTRAL 9:16 ANCHOR — quality bar + starting vocabulary of scene types for IG Reels.
  Canvas: 1080 × 1920. Claude reads this to learn density, choreography, vertical layout,
  caption placement, and vertical-motion easing. Match the craft; invent new treatments.
  All driven by --brand-* tokens. No media files — avatar is a placeholder box.
-->
<div id="anchor-reel" data-composition-id="anchor-reel" data-start="0" data-duration="30"
     data-width="1080" data-height="1920">

  <div class="bg"></div>
  <div class="glow-top" id="glow-t"></div>
  <div class="glow-bot" id="glow-b"></div>

  <!-- AVATAR placeholder (upper 60% of frame) -->
  <div class="avatar-zone" id="av"></div>

  <!-- S1 — HOOK TITLE (OUT beat · full-frame · first 0–2s) -->
  <div id="s1" class="clip scene center-v" data-start="0.1" data-duration="2.4" data-track-index="1">
    <div class="hook-eyebrow" id="s1-eye">⚡ THE HOOK</div>
    <div class="hook-title" id="s1-title">Bold one-liner<br/>that stops the scroll</div>
    <div class="hook-rule" id="s1-rule"></div>
  </div>

  <!-- S2 — KINETIC CAPTION (lower-third · avatar FULL) -->
  <div id="s2" class="clip scene caption-pos" data-start="2.5" data-duration="3.0" data-track-index="2">
    <div class="cap-setup" id="s2-setup">Here's the part</div>
    <div class="cap-pay-wrap">
      <div class="cap-pay-glow" id="s2-glow" aria-hidden="true">that matters</div>
      <div class="cap-pay" id="s2-pay">that matters</div>
    </div>
  </div>

  <!-- S3 — HERO NUMBER (OUT beat · full-frame slam) -->
  <div id="s3" class="clip scene center-v" data-start="5.5" data-duration="3.2" data-track-index="3">
    <div class="flash" id="s3-flash"></div>
    <div class="ring" id="s3-ring"></div>
    <div class="eyebrow" id="s3-eye">THE NUMBER</div>
    <div class="hero-num-wrap">
      <div class="hn-glow" id="s3-ng" aria-hidden="true">100K</div>
      <div class="hn" id="s3-n">100K</div>
    </div>
    <div class="hero-lbl" id="s3-lbl">ONE LINE OF CONTEXT</div>
  </div>

  <!-- S4 — VERTICAL LIST BUILD (lower 45% · avatar FULL or OUT) -->
  <div id="s4" class="clip scene list-pos" data-start="8.7" data-duration="4.0" data-track-index="4">
    <div class="eyebrow" id="s4-eye">◉ THREE THINGS</div>
    <div class="rows">
      <div class="row" id="s4-r1"><span class="dia"></span>First point</div>
      <div class="row" id="s4-r2"><span class="dia"></span>Second point</div>
      <div class="row" id="s4-r3"><span class="dia"></span>Third point</div>
    </div>
  </div>

  <!-- S5 — IMAGE CUTAWAY (OUT · full-frame · vertical b-roll) -->
  <div id="s5" class="clip scene center-v" data-start="12.7" data-duration="3.4" data-track-index="5">
    <div class="img-frame" id="s5-frame">
      <div class="img-ph" id="s5-img">IMAGE / B-ROLL<br/>9:16 VERTICAL</div>
      <div class="img-mask" id="s5-mask"></div>
    </div>
    <div class="img-cap" id="s5-cap">caption under the visual</div>
  </div>

  <!-- S6 — COMPARISON (two pills stacked vertically) -->
  <div id="s6" class="clip scene center-v" data-start="16.1" data-duration="3.6" data-track-index="6">
    <div class="eyebrow" id="s6-eye">BEFORE × AFTER</div>
    <div class="cmp-v">
      <div class="cmp-card" id="s6-c1"><div class="c-eye">THE OLD WAY</div><div class="c-name">Doesn't work</div></div>
      <div class="cmp-x" id="s6-x">↓</div>
      <div class="cmp-card hot" id="s6-c2"><div class="c-eye">THE FIX</div><div class="c-name">Actually works</div></div>
    </div>
  </div>

  <!-- S7 — CTA CARD (last 3–4s · OUT · high-contrast) -->
  <div id="s7" class="clip scene center-v" data-start="26.5" data-duration="3.5" data-track-index="7">
    <div class="cta-wrap" id="s7-wrap">
      <div class="cta-label" id="s7-lbl">COMMENT BELOW</div>
      <div class="cta-keyword" id="s7-kw">"eye"</div>
      <div class="cta-sub" id="s7-sub">I'll send the full protocol</div>
    </div>
    <div class="wordmark" id="s7-wm">◉ YOUR BRAND</div>
  </div>

  <style>
    /* ===== BRAND TOKENS — swap to re-skin ===== */
    #anchor-reel{
      --bg:#0b0b0f; --bg-mid:#15151c;
      --accent:#E8A24A; --accent-2:#C98A3A; --deep:#B5532A; --soft:#F3D9B5;
      --glow:rgba(232,162,74,0.5);
      --text:#FFFFFF; --muted:#A8A29E;
      --font-display:Georgia,'Times New Roman',serif;
      --font-body:Georgia,serif;
      --font-mono:'Courier New',monospace;
    }
    /* ============================================ */

    /* Canvas & background */
    #anchor-reel{ position:absolute; inset:0; overflow:hidden; font-family:var(--font-body); }
    #anchor-reel .bg{ position:absolute; inset:0; z-index:0;
      background:radial-gradient(150% 80% at 50% 110%, var(--bg-mid) 0%, var(--bg) 60%), var(--bg); }
    /* Glow zones: top (behind avatar) + bottom (behind graphics) */
    #anchor-reel .glow-top{ position:absolute; top:0; left:0; right:0; height:60%; z-index:0;
      background:radial-gradient(55% 45% at 50% 25%, rgba(232,162,74,0.10) 0%, transparent 60%); }
    #anchor-reel .glow-bot{ position:absolute; bottom:0; left:0; right:0; height:55%; z-index:0;
      background:radial-gradient(60% 40% at 50% 85%, rgba(232,162,74,0.12) 0%, transparent 60%); }

    /* Avatar placeholder zone (upper 58% of 1920px = 1114px) */
    #anchor-reel .avatar-zone{ position:absolute; top:0; left:0; right:0; height:58%;
      background:linear-gradient(180deg, rgba(232,162,74,0.04), transparent);
      border:2px dashed rgba(232,162,74,0.12); border-radius:0 0 32px 32px; z-index:1;
      display:flex; align-items:center; justify-content:center;
      font-family:var(--font-mono); font-size:28px; letter-spacing:0.2em; color:rgba(232,162,74,0.3); }
    #anchor-reel .avatar-zone::after{ content:"AVATAR LAYER"; }

    /* Scene base */
    #anchor-reel .scene{ position:absolute; inset:0; z-index:5; }

    /* Layout helpers */
    #anchor-reel .center-v{ display:flex; flex-direction:column; align-items:center;
      justify-content:center; gap:24px; text-align:center; padding:60px; box-sizing:border-box; }
    /* Caption: lower-third, above navigation bar */
    #anchor-reel .caption-pos{ display:flex; flex-direction:column; align-items:center;
      justify-content:flex-end; padding:0 60px 220px; text-align:center; }
    /* List: occupies lower 45% */
    #anchor-reel .list-pos{ display:flex; flex-direction:column; justify-content:flex-end;
      align-items:flex-start; padding:0 60px 200px; gap:20px; }

    /* Eyebrow */
    #anchor-reel .eyebrow{ font-family:var(--font-mono); font-weight:700; font-size:28px;
      letter-spacing:0.32em; text-transform:uppercase; color:var(--accent); }

    /* S1 hook */
    #anchor-reel .hook-eyebrow{ font-family:var(--font-mono); font-weight:700; font-size:26px;
      letter-spacing:0.3em; text-transform:uppercase; color:var(--accent); }
    #anchor-reel .hook-title{ font-family:var(--font-display); font-weight:700; font-size:96px;
      line-height:1.06; letter-spacing:-0.02em; color:var(--text);
      text-shadow:0 6px 30px rgba(0,0,0,.85); }
    #anchor-reel .hook-rule{ height:5px; width:320px; border-radius:3px; transform-origin:left center;
      background:linear-gradient(90deg, var(--accent), rgba(232,162,74,0));
      box-shadow:0 0 16px var(--glow); }

    /* S2 kinetic caption */
    #anchor-reel .cap-setup{ font-family:var(--font-body); font-size:50px; color:var(--text);
      text-shadow:0 2px 12px rgba(0,0,0,.8); }
    #anchor-reel .cap-pay-wrap{ position:relative; }
    #anchor-reel .cap-pay{ position:relative; font-family:var(--font-display); font-weight:700;
      font-size:96px; line-height:1.1; letter-spacing:-0.02em; color:var(--accent);
      filter:drop-shadow(0 4px 20px var(--glow)); }
    #anchor-reel .cap-pay-glow{ position:absolute; inset:0; font-family:var(--font-display);
      font-weight:700; font-size:96px; line-height:1.1; color:var(--accent); filter:blur(22px); opacity:.45; }

    /* S3 hero number */
    #anchor-reel .flash{ position:absolute; inset:0; background:var(--soft); opacity:0; z-index:2; }
    #anchor-reel .ring{ position:absolute; left:50%; top:50%; width:600px; height:600px;
      margin:-300px 0 0 -300px; border:2px solid rgba(232,162,74,0.3); border-radius:50%; opacity:0; }
    #anchor-reel .hero-num-wrap{ position:relative; }
    #anchor-reel .hn{ position:relative; font-family:var(--font-display); font-weight:700;
      font-size:240px; line-height:0.9; letter-spacing:-0.04em; color:var(--accent);
      text-shadow:0 0 60px rgba(232,162,74,0.4), 0 12px 40px rgba(0,0,0,.8);
      font-variant-numeric:tabular-nums; }
    #anchor-reel .hn-glow{ position:absolute; inset:0; font-family:var(--font-display);
      font-weight:700; font-size:240px; line-height:0.9; color:var(--accent); filter:blur(36px); opacity:.5; }
    #anchor-reel .hero-lbl{ font-family:var(--font-mono); font-weight:700; font-size:30px;
      letter-spacing:0.28em; color:var(--text); }

    /* S4 vertical list */
    #anchor-reel .rows{ display:flex; flex-direction:column; gap:20px; width:100%; }
    #anchor-reel .row{ display:flex; align-items:center; gap:22px; padding:24px 36px;
      border-radius:16px; width:100%; box-sizing:border-box;
      background:rgba(232,162,74,0.10); border:1.5px solid rgba(232,162,74,0.28);
      box-shadow:0 12px 36px rgba(0,0,0,0.45);
      font-family:var(--font-display); font-weight:700; font-size:46px; color:var(--text); }
    #anchor-reel .row .dia{ width:22px; height:22px; flex:0 0 auto; transform:rotate(45deg);
      border-radius:4px; background:linear-gradient(135deg,var(--accent),var(--accent-2));
      box-shadow:0 0 14px var(--glow); }

    /* S5 image cutaway — full-frame 9:16 */
    #anchor-reel .img-frame{ position:relative; width:960px; height:680px; border-radius:20px;
      overflow:hidden; border:3px solid var(--accent);
      box-shadow:0 24px 70px rgba(0,0,0,0.55), 0 0 50px rgba(232,162,74,0.18); }
    #anchor-reel .img-ph{ position:absolute; inset:0; display:flex; flex-direction:column;
      align-items:center; justify-content:center;
      background:linear-gradient(160deg,#1d1a14,#0c0a07);
      font-family:var(--font-mono); font-weight:700; font-size:32px;
      letter-spacing:0.24em; color:var(--muted); text-align:center; gap:12px; }
    #anchor-reel .img-mask{ position:absolute; inset:0; background:var(--bg); transform-origin:top center; }
    #anchor-reel .img-cap{ margin-top:18px; font-family:var(--font-body); font-style:italic;
      font-size:32px; color:var(--soft); }

    /* S6 vertical comparison */
    #anchor-reel .cmp-v{ display:flex; flex-direction:column; align-items:center; gap:20px; width:100%; }
    #anchor-reel .cmp-card{ width:900px; padding:44px 36px; border-radius:20px;
      display:flex; flex-direction:column; gap:10px; box-sizing:border-box;
      background:rgba(255,255,255,0.05); border:1.5px solid rgba(255,255,255,0.12);
      box-shadow:0 18px 50px rgba(0,0,0,0.5); }
    #anchor-reel .cmp-card.hot{ background:rgba(232,162,74,0.15); border-color:var(--accent);
      box-shadow:0 0 44px rgba(232,162,74,0.28), 0 18px 50px rgba(0,0,0,0.5); }
    #anchor-reel .c-eye{ font-family:var(--font-mono); font-weight:700; font-size:18px;
      letter-spacing:0.24em; color:var(--accent-2); }
    #anchor-reel .c-name{ font-family:var(--font-display); font-weight:700; font-size:48px; color:var(--text); }
    #anchor-reel .cmp-x{ font-family:var(--font-display); font-weight:700; font-size:64px; color:var(--accent); }

    /* S7 CTA card */
    #anchor-reel .cta-wrap{ display:flex; flex-direction:column; align-items:center; gap:16px;
      padding:60px 60px 50px; border-radius:28px; width:900px; box-sizing:border-box;
      background:rgba(232,162,74,0.14); border:2px solid var(--accent);
      box-shadow:0 0 60px rgba(232,162,74,0.28), 0 24px 60px rgba(0,0,0,0.55); }
    #anchor-reel .cta-label{ font-family:var(--font-mono); font-weight:700; font-size:26px;
      letter-spacing:0.3em; text-transform:uppercase; color:var(--muted); }
    #anchor-reel .cta-keyword{ font-family:var(--font-display); font-weight:700; font-size:110px;
      line-height:1; letter-spacing:-0.02em; color:var(--accent);
      text-shadow:0 0 50px rgba(232,162,74,0.4); }
    #anchor-reel .cta-sub{ font-family:var(--font-body); font-size:36px; color:var(--soft); }
    #anchor-reel .wordmark{ font-family:var(--font-mono); font-weight:700; font-size:22px;
      letter-spacing:0.32em; color:var(--muted); margin-top:20px; }
  </style>

  <script src="https://cdn.jsdelivr.net/npm/gsap@3.14.2/dist/gsap.min.js"></script>
  <script>
    window.__timelines = window.__timelines || {};
    const tl = gsap.timeline({ paused: true });

    /* ambient: glow zones breathe */
    tl.fromTo("#glow-t", { opacity:0.8 }, { opacity:1, duration:6, ease:"sine.inOut", yoyo:true, repeat:2 }, 0);
    tl.fromTo("#glow-b", { opacity:0.8 }, { opacity:1, duration:7, ease:"sine.inOut", yoyo:true, repeat:2 }, 0.5);

    /* ---- S1 hook: eyebrow drops, title rises (vertical y), rule sweeps; zoom-out exit ---- */
    tl.from("#s1-eye",   { y:-20, opacity:0, duration:0.45, ease:"power3.out" }, 0.15);
    tl.from("#s1-title", { y:60,  opacity:0, duration:0.6,  ease:"back.out(1.5)" }, 0.45);
    tl.fromTo("#s1-rule",{ scaleX:0 },{ scaleX:1, duration:0.5, ease:"expo.out" }, 0.95);
    tl.to("#s1", { opacity:0, y:-20, duration:0.35, ease:"power2.in" }, 2.15);
    tl.set("#s1", { opacity:0 }, 2.5);

    /* ---- S2 caption: setup up, payoff slams from below + glow; exit down ---- */
    tl.from("#s2",       { opacity:0, y:20, duration:0.35, ease:"power2.out" }, 2.55);
    tl.from("#s2-setup", { y:22, opacity:0, duration:0.4, ease:"power3.out" }, 2.7);
    tl.from("#s2-pay",   { y:48, opacity:0, scale:0.92, duration:0.55, ease:"back.out(1.7)" }, 3.05);
    tl.from("#s2-glow",  { y:48, opacity:0, scale:0.92, duration:0.55, ease:"back.out(1.7)" }, 3.05);
    tl.to("#s2", { opacity:0, y:-16, duration:0.3, ease:"power2.in" }, 5.15);
    tl.set("#s2", { opacity:0 }, 5.5);

    /* ---- S3 hero number: flash → ring expand → number slam (vertical); breathe; exit ---- */
    tl.from("#s3",          { opacity:0, duration:0.25, ease:"power2.out" }, 5.55);
    tl.fromTo("#s3-flash",  { opacity:0 },{ opacity:0.65, duration:0.08, ease:"expo.in" }, 5.75);
    tl.to("#s3-flash",      { opacity:0, duration:0.3, ease:"power2.out" }, 5.84);
    tl.fromTo("#s3-ring",   { scale:0.35, opacity:0 },{ scale:1, opacity:1, duration:0.8, ease:"expo.out" }, 5.8);
    tl.from("#s3-eye",      { y:-18, opacity:0, duration:0.35, ease:"power2.out" }, 5.68);
    tl.from("#s3-n",        { scale:0.15, opacity:0, duration:0.6, ease:"back.out(1.8)" }, 5.78);
    tl.from("#s3-ng",       { scale:0.15, opacity:0, duration:0.6, ease:"back.out(1.8)" }, 5.78);
    tl.from("#s3-lbl",      { y:24, opacity:0, letterSpacing:"0.6em", duration:0.45, ease:"expo.out" }, 6.28);
    tl.to("#s3-n",          { scale:1.03, duration:1.6, ease:"sine.inOut", yoyo:true, repeat:1 }, 6.5);
    tl.to("#s3", { opacity:0, scale:1.05, duration:0.35, ease:"power2.in" }, 8.4);
    tl.set("#s3", { opacity:0 }, 8.7);

    /* ---- S4 vertical list: eyebrow, rows slide up with stagger; exit ---- */
    tl.from("#s4",    { opacity:0, y:20, duration:0.35, ease:"power2.out" }, 8.75);
    tl.from("#s4-eye",{ x:-22, opacity:0, duration:0.4, ease:"power3.out" }, 8.9);
    tl.from("#s4-r1", { y:40, opacity:0, duration:0.5, ease:"back.out(1.4)" }, 9.3);
    tl.from("#s4-r2", { y:40, opacity:0, duration:0.5, ease:"back.out(1.4)" }, 9.8);
    tl.from("#s4-r3", { y:40, opacity:0, duration:0.5, ease:"back.out(1.4)" }, 10.3);
    tl.to("#s4", { opacity:0, y:-16, duration:0.35, ease:"power2.in" }, 12.35);
    tl.set("#s4", { opacity:0 }, 12.7);

    /* ---- S5 image cutaway: frame in from below, mask wipes top-to-bottom, push-up; exit ---- */
    tl.from("#s5",       { opacity:0, duration:0.25, ease:"power2.out" }, 12.75);
    tl.from("#s5-frame", { y:50, opacity:0, scale:0.96, duration:0.5, ease:"back.out(1.3)" }, 12.9);
    tl.fromTo("#s5-mask",{ scaleY:1 },{ scaleY:0, duration:0.8, ease:"power2.inOut" }, 13.15);
    tl.fromTo("#s5-img", { scale:1.0 },{ scale:1.06, y:-12, duration:3.0, ease:"sine.inOut" }, 13.15);
    tl.from("#s5-cap",   { y:18, opacity:0, duration:0.4, ease:"power2.out" }, 14.0);
    tl.to("#s5", { opacity:0, scale:1.04, duration:0.35, ease:"power2.in" }, 15.75);
    tl.set("#s5", { opacity:0 }, 16.1);

    /* ---- S6 vertical comparison: cards slide up in sequence, × pops; glow pulse; exit ---- */
    tl.from("#s6",     { opacity:0, y:20, duration:0.35, ease:"power2.out" }, 16.15);
    tl.from("#s6-eye", { y:-18, opacity:0, duration:0.35, ease:"power2.out" }, 16.3);
    tl.from("#s6-c1",  { y:50, opacity:0, scale:0.94, duration:0.5, ease:"back.out(1.4)" }, 16.5);
    tl.from("#s6-x",   { scale:0, opacity:0, duration:0.4, ease:"back.out(2.2)" }, 16.95);
    tl.from("#s6-c2",  { y:50, opacity:0, scale:0.94, duration:0.5, ease:"back.out(1.4)" }, 17.2);
    tl.to("#s6-c2",    { boxShadow:"0 0 70px rgba(232,162,74,0.5)", duration:0.8, ease:"sine.inOut", yoyo:true, repeat:1 }, 17.8);
    tl.to("#s6", { opacity:0, y:-16, duration:0.35, ease:"power2.in" }, 19.4);
    tl.set("#s6", { opacity:0 }, 19.75);

    /* ---- S7 CTA: wrap slams in from below, keyword pulses, wordmark fades; hold ---- */
    tl.from("#s7",      { opacity:0, duration:0.3, ease:"power2.out" }, 26.55);
    tl.from("#s7-wrap", { y:80, opacity:0, scale:0.92, duration:0.6, ease:"back.out(1.6)" }, 26.7);
    tl.from("#s7-lbl",  { y:16, opacity:0, duration:0.4, ease:"power2.out" }, 27.1);
    tl.from("#s7-kw",   { scale:0.5, opacity:0, duration:0.55, ease:"back.out(2.0)" }, 27.3);
    tl.to("#s7-kw",     { scale:1.05, duration:0.8, ease:"sine.inOut", yoyo:true, repeat:2 }, 27.9);
    tl.from("#s7-sub",  { y:16, opacity:0, duration:0.4, ease:"power2.out" }, 27.5);
    tl.from("#s7-wm",   { y:12, opacity:0, duration:0.4, ease:"power2.out" }, 27.8);
    tl.to("#s7", { opacity:0, duration:0.35, ease:"power2.in" }, 29.65);

    window.__timelines["anchor-reel"] = tl;
  </script>
</div>
</body>
</html>
```
