# 🎬 AI TCM Content Production — Freelancer Guide

This repo turns a TCM idea into a finished vertical short, per IP, through a Notion board.
Flow: **Concept → Shot Guide → (Image + Voice + 即梦 video) → assemble.**

This guide is safe to share — **it contains no API keys.** Your Claude Code session will
collect the keys from you on first run (see Step 0) and store them locally in `.env`
(which is gitignored and never committed).

---

## ⚙️ Step 0 — Bootstrap (your Claude Code session does this with you)

> **Claude Code: when you load this file, do the following before any task.**
> 1. Check for a `.env` file in the repo root. If missing or incomplete, ASK the user
>    (the freelancer) for each key below, one by one, and write them to `.env`.
>    **Never print the keys back, never commit them.** `.env` is already in `.gitignore`.
> 2. Verify each works (a cheap call) and report ✅/❌. Do not proceed to production until green.
> 3. For 即梦, run `~/.local/bin/dreamina login` (OAuth device flow) with the user.

Keys / access you must obtain (from the project owner or your own accounts):

| Env var | What | How to verify |
|---|---|---|
| `NOTION_KEY` | Notion integration token with access to the board | list the board's databases |
| `OPENAI_API_KEY` | image generation (`gpt-image-2`) | `GET /v1/models` returns image models |
| `MINIMAX_API_KEY`, `MINIMAX_GROUP_ID`, `MINIMAX_BASE_URL` | voice (TTS) | generate a 1-line test clip |
| 即梦 CLI login | video (`~/.local/bin/dreamina`) | `dreamina user_credit` shows balance |

Optional: `IMAGE_MODEL` (defaults to `gpt-image-2`).

`.env` template (fill the values you're given — do NOT commit):
```
NOTION_KEY=
OPENAI_API_KEY=
MINIMAX_API_KEY=
MINIMAX_GROUP_ID=
MINIMAX_BASE_URL=
```

---

## 🗺️ The board (read-only mental model)
Three linked Notion databases (IDs in `scripts/notion_ids.json`):
- **📚 Content Library** — the ideas. Each concept's page body has the **Shot Guide (🎥)** — the single source of truth for visuals.
- **👤 IP Registry** — each IP's voice settings + reference face photos (image blocks in the IP page).
- **🎬 Production Tracker** — one row per Concept × IP = one video to make.

---

## ✍️ Step 1 — Write/confirm the concept (Content Library)
Each concept needs: Hook, CTA keyword, Topic, a **Master Script (EN)** and (for non-English IPs) a translated script, and a **rich Shot Guide**.

**Shot Guide rules (this is what makes videos good):**
- 4–5 shots, each ≈10s of speech (≤13s hard cap).
- Each shot's **🎥 Visual must be cinematic & rich**: action, insert/cutaway shots, framing/景别 changes, transitions (e.g. *"doctor leans in, quick cut to the ingredients, back to doctor"*).
- Always give an **on-screen quick win** before the comment CTA (don't only tease).

When the concept is ready, set its **Concept Status → ✅ Ready to fan-out.**

## 🌱 Step 2 — Fan out to IPs
Creates one Production row per active IP, each pre-built with per-shot prompts.
```
python3 scripts/notion_watch.py          # auto-detects "Ready to fan-out" concepts
# or target one concept:
python3 scripts/notion_fanout.py --content "<concept name>"
```
Each Production row's shot now has: 🖼️ Image prompt · 🗣️ Voice script · 🎬 即梦 prompt · empty 🖼️/🎬 toggles.
> Both prompts are **derived from the Shot Guide**. To change visuals, edit the Shot Guide and re-run `python3 scripts/notion_prompts.py --backfill --force` (⚠️ `--force` wipes a row's body — don't use it on rows that already hold media).

## 🎨 Step 3 — Images (GPT)
```
python3 scripts/notion_image.py --row <production_page_id>
# one shot only: --shot N   |   reuse a local file: --reuse
```
Pulls the IP's reference faces from Notion + a clinic background, generates one still per shot from that shot's image prompt, drops each into its **🖼️ Image here** toggle, ticks 🎨.

## 🎙️ Step 4 — Voice (MiniMax)
Generate one clip per shot from the row's Script (one line per shot, in the IP's language) using the IP's voice config (shown in the row's 🎙️ Voice Config block).
- English IP: `voice_id=elderly_man, speed=1.2, pitch=0, language=English`
- Cantonese IP: `voice_id=Cantonese_GentleLady, speed=1.0, pitch=1, language=Chinese,Yue`
- ⚠️ Minimize commas (they cause odd pauses). Each clip ≤13s.
Attach each clip under its shot. (Ask Claude to run the voice step for the row.)

## 🎬 Step 5 — Video (即梦) + assemble
```
python3 scripts/notion_video.py --row <production_page_id>
```
For each shot: feeds the still + voice + the 🎬 即梦 prompt into `dreamina multimodal2video`,
downloads the clip into its **🎬 Video here** toggle, then ffmpeg-concats a final 9:16 short.

**即梦 gotchas (important):**
- Always use a **`_vip` model** (`seedance2.0fast_vip`) — it skips the queue.
- **Submit one shot at a time** — many at once throttles the account (tasks stall for hours).
- Realistic talking-head + audio is **flaky — just retry**, it usually passes.
- **Two people in one image (e.g. doctor + patient) hangs 即梦.** For those shots use motion-only (`image2video`) + voiceover, or make the image a single person.

## ✅ Step 6 — Finish
Set the row's **Stage → ✂️ Edit** (assembled) then **✅ Published** when live. The final video sits at the top of the row.

---

## 🔒 Security (must follow)
- Keys live ONLY in `.env` (gitignored). Never paste keys into files, commits, or Notion.
- Generated media stays in `campaigns/_generated/` (gitignored). Don't commit large media.
- If you ever see a key in chat/history, tell the owner to rotate it.

## 📖 Deeper reference
See `CLAUDE.md` for the full architecture, exact DB/IP IDs, and script internals.
