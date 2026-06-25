# ai-tcm-ip — AI TCM Content Engine

Multi-IP short-form video factory for TCM marketing. Pipeline: **idea → image → voice → video**, orchestrated through a Notion board and a set of `scripts/notion_*.py` helpers.

## Secrets (NEVER commit)
All keys live in `.env` (gitignored). Scripts auto-load it.
- `NOTION_KEY` — Notion integration token
- `OPENAI_API_KEY` — image gen (`IMAGE_MODEL`, default `gpt-image-2`)
- `MINIMAX_API_KEY` / `MINIMAX_GROUP_ID` / `MINIMAX_BASE_URL` — voice (TTS)
- 即梦 CLI auth is separate (OAuth, `~/.local/bin/dreamina login`)

> Notion/OpenAI keys have been pasted in chat historically — rotate periodically.

## Notion board (3 linked DBs)
Board page `389f2a3f432080678683fb82eb056ee6`. IDs in `scripts/notion_ids.json` (not secret).
- **📚 Content Library** (`content_db`) — language-agnostic concepts. Props: Name, Topic, Hook, CTA, Concept Status. Body = **📜 Master Script (EN)** + optional **🇭🇰 Script (粤语)** + **🎬 Shot Guide**.
- **👤 IP Registry** (`ip_db`) — one row per IP = SOURCE OF TRUTH for voice config. Props: IP, Language, Persona, voice_id, Speed, Pitch, Language Boost, Emotion, Active. Reference face photos live as **image blocks in the IP page body**. Active IPs: 🌸 Jessica (Cantonese), 👴 Jackie Chan (English).
- **🎬 Production Tracker** (`prod_db`) — one row per Content×IP. Dual relations + Stage, 🎨/🎙️/🎬 checkboxes, Script (per-IP language, ONE LINE PER SHOT), Publish Date, Assets, Notes.

## The Shot Guide is the single source of truth
The **Content Library Shot Guide (🎥 Visual)** drives everything. Write it RICH/cinematic (action, insert/cutaway shots, framing/景别 changes, transitions). Both per-shot prompts are DERIVED from it by `apply_shot_plan`:
- 🖼️ **Image prompt** = `_primary_beat()` of the 🎥 (first beat only, cuts/inserts stripped) → ONE still frame.
- 🎬 **即梦 prompt** = FULL rich 🎥 → animates the still into video.

To enrich a video: edit the Shot Guide, re-run `apply_shot_plan` — both prompts auto-update. Don't hand-edit the production prompts.

### Per-shot row layout (built by apply_shot_plan)
```
Shot N · ~Xs · beat
  🖼️ Image prompt (single frame → GPT)      [code]
  🗣️ Voice script (row's IP language)        [code]
  🎬 即梦 prompt (rich shot guide → video)    [code]  — audio-native, {{图片}}/{{对白}} vars, read-language from IP, 运镜 by beat, AI-digital-human disclaimer
  🖼️ Image here   (empty toggle — drop the still here)
  🎬 Video here   (empty toggle — drop the video here)
```

## Scripts (`scripts/`)
- `notion_fanout.py --content "<name>"` — explode a concept into 1 Production row per ACTIVE IP (dedup, auto-runs apply_shot_plan).
- `notion_watch.py [--loop N]` — auto fan-out when Concept Status = "✅ Ready to fan-out" → flips to "🚀 Fanned out".
- `notion_prompts.py --backfill [--force]` — (re)build per-shot prompts on Production rows. Core: `apply_shot_plan(row, rebuild=True)` wipes+rebuilds the body. ⚠️ rebuild is DESTRUCTIVE — wipes uploaded images/audio/video. Don't run on rows that already hold media.
- `notion_image.py --row <id> [--shot N] [--reuse]` — pull IP reference faces FROM Notion + a clinic bg → `gpt-image-2` → place each still in its "🖼️ Image here" toggle → tick 🎨.
- `notion_video.py --row <id>` — 即梦 video: per shot, pull image+audio+即梦prompt from Notion → `dreamina multimodal2video` → download → place in "🎬 Video here" → ffmpeg concat final.
- `gen_voice_clip.py` — MiniMax TTS. Voice config per IP (see voice_config.yaml + IP Registry).
- `notion_assets.json` — clinic backgrounds + (optional) face overrides.

## Voice (MiniMax)
- English IP (Jackie): `voice_id=elderly_man, speed=1.2, pitch=0, MINIMAX_TTS_LANGUAGE=English`
- Cantonese IP (Jessica): `voice_id=Cantonese_GentleLady, speed=1.0, pitch=1, language=Chinese,Yue`
- ⚠️ Commas (，/,) make MiniMax insert pauses — minimize in scripts. Keep each clip ≤13s.

## 即梦 / Dreamina CLI (video)
`~/.local/bin/dreamina` (logged in, maestro VIP). Key command:
`dreamina multimodal2video --image X --audio Y --prompt Z --ratio 9:16 --duration <4-15> --model_version seedance2.0fast_vip --poll 0`
- **Use `_vip` models — they SKIP the queue** (non-vip queue is 500k+, hours).
- **Submit ONE AT A TIME** — submitting many at once throttles the account (tasks stall in "querying" for hours).
- Result video URL: `result_json.videos[0].video_url`.
- **Realistic talking-head + audio is flaky** — retry usually works. **Two people in one image (e.g. doctor + patient) hangs 即梦** — for those shots use `image2video` (motion only) or ffmpeg Ken Burns + voiceover, OR regenerate as a single person.
- Audio must be 2–15s.

## Conventions
- Each shot ≤13s (OmniHuman/即梦 sweet spot). Scripts: ONE line per shot in the row's Script property, in the IP's language.
- Every content gives an on-screen QUICK WIN before the comment CTA (don't only tease).
- 9:16 vertical, warm TCM clinic. Comment-keyword CTA (e.g. "gut", "detox", "stomach") + follow.
- Generated media → `campaigns/_generated/<row_id>/` (gitignored). Source assets (clinic bg, IP faces) → `campaigns/assets/` (tracked).
