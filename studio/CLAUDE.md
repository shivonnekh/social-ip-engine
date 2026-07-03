# studio/ — Content Factory (formerly the ai-tcm-ip repo)

> **Merged into `social-ip-engine` on 2026-07-03** (git history preserved).
> Run all scripts FROM THIS FOLDER (`cd studio/`) — they load `studio/.env`.
> This folder is NEVER deployed; it is local tooling only.
> The old repo `shivonnekh/ai-tcm-ip` is archived; the old local folder is
> `_archived-ai-tcm-ip` (delete once you're comfortable).
> Dead server code (webhook.py, dm_map.json) → `../docs/legacy/ai-tcm-ip-server/`.
> Generated infographics now live in `studio/assets/infographics/`.

Multi-IP short-form video factory for TCM marketing. Pipeline: **idea → image → voice → video**, orchestrated through a Notion board and a set of `scripts/notion_*.py` helpers.

## ⚠️ This folder does NOT run the live Instagram bot — `../src/` does

**`social-ip-engine`** (formerly TCM-Jessica; `/Users/shivonne/Claude Code/social-ip-engine`, `github.com/shivonnekh/social-ip-engine`, deployed at `https://tcm-jessica.onrender.com`) is a completely separate, unrelated live-production repo — Jackie's and Chloe's real Instagram comment→DM auto-reply, plus Jessica's WhatsApp bot for 心宜中醫. Confused these twice in one session (2026-07-01/02) — burned real time investigating this repo's dead-code `server/webhook.py` (never deployed, was never the live thing) before finding the actual live system. Do not assume a "webhook"/"comment reply" ask is about this repo's `server/` folder — it almost certainly means social-ip-engine.

**What lives where:**
- **Here (ai-tcm-ip)**: authoring — Notion content pipeline, image/voice/video generation, DM copy + infographic *briefs* written per concept.
- **social-ip-engine**: the actual live bot — `data/channels/comment_responses.json` (keyword→DM rules, separate schema from anything here), Meta webhook/Graph API integration, real customer conversations.
- **The bridge**: social-ip-engine's `POST /admin/notion-sync` (its own `src/notion_sync.py`, stdlib-only, reads Notion directly — does NOT import anything from this repo) polls Production Tracker for `Stage = ✅ Published` and auto-drafts a keyword rule the moment content goes live. `scripts/notion_ids.json` here is duplicated (not secret) into social-ip-engine for this purpose — keep both in sync if the Notion board structure changes.
- **Infographic images already generated here** (`server/static/infographics/<brand>/<keyword>.png` via `batch_infographic_gen.py`) need a **manual copy** into social-ip-engine's `data/media/guides/<keyword>-page-1.png` + a matching `image_urls` entry in its `comment_responses.json` — the auto-sync does not do this step yet.
- **Check Notion FIRST before regenerating an infographic**: `batch_infographic_gen.py` sometimes already ran and uploaded the real image to the **Production Tracker row's "📊 DM Infographic" toggle** (not the Content Library concept page, which only ever has the text brief). Walk the row body for that toggle before assuming a new GPT image-gen call is needed.

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
- English IP (Jackie): `voice_id=jackie_chan_clone_v2, speed=1.2, pitch=0` — **custom voice clone, NOT a preset**. IP Registry is source of truth.
- Cantonese IP (Jessica): `voice_id=Cantonese_GentleLady, speed=1.0, pitch=1, language=Chinese,Yue`
- ✅ **Use NATURAL punctuation (，。？—) — MiniMax respects it for pauses + rhythm.** Verified empirically: same line 6.9s (no punctuation) → 8.5s (with `. , —`) → 9.4s (with `<#x#>` tags). Stripping punctuation = robotic/fake delivery. Do NOT replace punctuation with spaces.
- Optional explicit pause: `<#x.x#>` tags (seconds, 0.01–99.99), e.g. `…the same.<#0.4#> TCM doesn't.` — for extra emphasis beyond punctuation.
- Keep each clip ≤13s.

## Voice Cloning (MiniMax)
Jackie's voice is a **custom MiniMax clone** of his real voice — not a preset. Clone history:
- `jackie_chan_clone` — v1, from `~/Downloads/tcm.m4a` (12.8s)
- `jackie_chan_clone_v2` — **ACTIVE**, clearer sample: `tcm.m4a` + `ScreenRecording_07-02-2026_16-28-09_1.MP4` concatenated → 22s

**Re-cloning flow** (when user provides a new voice sample):
1. Convert to WAV mono 44100Hz: `ffmpeg -i input.mp4 -ar 44100 -ac 1 -c:a pcm_s16le out.wav`
2. If sample < 10s, concat with previous sample to reach 10-30s total
3. `POST /v1/files/upload` — `purpose=voice_clone`, WAV file → get `file_id`
4. `POST /v1/voice_clone` — `voice_id=jackie_chan_clone_vN` + `file_id` (⚠️ cannot overwrite existing ID — increment version)
5. Update Jackie's IP Registry page in Notion → `voice_id` property
6. Run `batch_voice_gen.py --ip Jackie --force` to regen all rows

**`batch_voice_gen.py --force`**: deletes existing Notion audio blocks and regenerates. Required whenever voice_id changes.

## 即梦 / Dreamina CLI (video)
`~/.local/bin/dreamina` (logged in, maestro VIP). Key command:
`dreamina multimodal2video --image X --audio Y --prompt Z --ratio 9:16 --duration <4-15> --model_version seedance2.0fast_vip --poll 0`
- **Use `_vip` models — they SKIP the queue** (non-vip queue is 500k+, hours).
- **Submit ONE AT A TIME** — submitting many at once throttles the account (tasks stall in "querying" for hours).
- Result video URL: `result_json.videos[0].video_url`.
- **Realistic talking-head + audio is flaky** — retry usually works. **Two people in one image (e.g. doctor + patient) hangs 即梦** — for those shots use `image2video` (motion only) or ffmpeg Ken Burns + voiceover, OR regenerate as a single person.
- **Lip-sync requires a near-frontal face** — side/profile angles (>30° off-axis) cause multimodal2video to fail silently → Ken Burns fallback. Always generate image prompts with face ≤15° off-axis when lip-sync is needed.
- Audio must be 2–15s.

## Conventions
- Each shot ≤13s (OmniHuman/即梦 sweet spot). Scripts: ONE line per shot in the row's Script property, in the IP's language.
- Every content gives an on-screen QUICK WIN before the comment CTA (don't only tease).
- 9:16 vertical, warm TCM clinic. Comment-keyword CTA (e.g. "gut", "detox", "stomach") + follow.
- Generated media → `campaigns/_generated/<row_id>/` (gitignored). Source assets (clinic bg, IP faces) → `campaigns/assets/` (tracked).
