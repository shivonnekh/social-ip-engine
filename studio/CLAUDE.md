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

### Trailer sections (after the last shot — synced at fan-out since 2026-07-06)
```
🖼️ Cover Photo
  🖼️ Cover prompt (thumbnail → GPT)          [code]  — build_cover_prompt(): scroll-stopping frame, top third reserved for title overlay
  🖼️ Cover here   (empty toggle — drop the cover here)
📊 DM Infographic
  🖼️ Infographic prompt (→ GPT image gen)    [code]  — copied from the Content page's "🖼️ Infographic Brief" by fetch_infographic_brief()
```
Older rows were backfilled with `scripts/backfill_cover_dm_prompts.py`
(append-only + idempotent — safe on rows holding media, unlike a rebuild).

## Scripts (`scripts/`)
- `notion_fanout.py --content "<name>"` — explode a concept into 1 Production row per ACTIVE IP (dedup, auto-runs apply_shot_plan).
- `notion_watch.py [--loop N]` — auto fan-out when Concept Status = "✅ Ready to fan-out" → flips to "🚀 Fanned out".
- `notion_prompts.py --backfill [--force]` — (re)build per-shot prompts on Production rows. Core: `apply_shot_plan(row, rebuild=True)` wipes+rebuilds the body. ⚠️ rebuild is DESTRUCTIVE — wipes uploaded images/audio/video. Don't run on rows that already hold media.
- `notion_image.py --row <id> [--shot N] [--reuse]` — pull IP reference faces FROM Notion + a clinic bg → `gpt-image-2` → place each still in its "🖼️ Image here" toggle → tick 🎨.
- `notion_video.py --row <id>` — 即梦 video: per shot, pull image+audio+即梦prompt from Notion → `dreamina multimodal2video` → download → place in "🎬 Video here" → ffmpeg concat final (merge is already automatic here — no separate manual "merge" step needed).
- `add_karaoke_captions.py --row <id> [--upload] [--script <path>]` — burns word-level karaoke-highlight captions (white base, current word yellow) onto that row's merged `final.mp4` → `final_karaoke.mp4`. Added 2026-07-07 to replace the previous ad-hoc process (JianYing CLI drafts kept failing to open). **Uses moviepy, NOT ffmpeg's `ass`/`subtitles`/`drawtext` filters** — this machine's ffmpeg build has no libass/freetype support (`ffmpeg -filters` shows neither). Word timing comes from local `openai-whisper` (`word_timestamps=True`) run directly against the merged video's audio. Pass `--script <path-to-txt>` with the KNOWN correct VO script to fix Whisper mishearings (e.g. it transcribed "cramps" as "crampus" in the period-pain campaign) while keeping Whisper's timestamps — see `align_to_known_script()`. `--upload` pushes the result to the row's **"Production Video" page PROPERTY** (not a body block) — the exact property social-ip-engine's live Reels auto-publish reads (`src/notion_publish.py::_extract_video_url`), so a captioned row is then one Stage-flip away from going live. Caches the Whisper transcript as `words.json` next to the video (gitignored, `campaigns/**/video/`) — pass `--retranscribe` to force a redo.
- `generate_cover.py --row <id> [--force]` — generate the 🖼️ Cover Photo image for ONE row (reads the row's own Cover prompt code block, uses the IP's reference faces, fills the "🖼️ Cover here" toggle). This is the review checkpoint the LIVE publish path now reads FIRST (see root CLAUDE.md "Cover priority") — generate + eyeball it BEFORE flipping Stage.
- `generate_infographic.py --row <id> [--force]` — same for the 📊 DM Infographic (text-to-image, no face refs — the brief mandates illustration style). Refuses to run against the no-brief placeholder.
- `gen_voice_clip.py` — MiniMax TTS. Voice config per IP (see voice_config.yaml + IP Registry). Low-level single-clip tool — for a whole Production row use `batch_voice_gen.py --row <id>` instead (reads each shot's Voice script property, calls this per shot).
- `notion_assets.json` — clinic backgrounds + (optional) face overrides.

### Pipeline orchestrators (`pipeline_common.py` + 3 stage scripts, added 2026-07-07)
Chains the tools above across every IP under a Content concept, at the 3 points Shivonne actually wants to review by hand — nothing more is automated than that; see each script's own module docstring for the full reasoning. Each accepts `--content "<name>"` / `--content-id <id>` (every row for that concept) or `--row <id>` (just one). **Run from anywhere — no `cd studio` needed** (every path is anchored via `Path(__file__)`, not cwd; verified by running from the repo root).

1. **After you approve the Script** → `generate_assets.py --content "<name>"` — fans out to every active IP (`notion_fanout.py`), then runs `notion_image.py` + `batch_voice_gen.py` for every resulting row.
2. **After you review image + voice** → `generate_all_videos.py --content "<name>"` — runs `notion_video.py` (video-gen + auto-merge) for every row under that content.
3. **After you review the video** → `finalize_all_videos.py --content "<name>"` — runs `add_karaoke_captions.py --upload` for every row, landing the captioned final video straight in each row's "Production Video" property.

Each stage subprocess-invokes the existing single-row tools exactly as if typed by hand (no reimplementation, no drift risk) and NEVER lets one row's failure abort the rest of the batch — a clear ✅/❌ summary prints per row at the end, so a partial failure can't be missed, and only the failed rows need re-running. **None of the 3 stages ever touch Stage** — flipping to `🟢 Ready to Publish` / `✅ Published` (which is what actually triggers the social-ip-engine automations below) stays a deliberate, manual, in-Notion decision, on purpose: it's the one action in this whole chain that's genuinely hard to reverse (a live Instagram post), so it's the one thing no script does on your behalf.

### The full content pipeline — what's automated vs manual (updated 2026-07-07)
Content Library Script review (manual, by you) → `generate_assets.py` (fan-out + image + voice, one command) → **you review image/voice** → `generate_all_videos.py` (video-gen, one command) → **you review video** → `finalize_all_videos.py` (captions + upload, one command) → **you review the final captioned video, then drag Stage yourself.** `batch_infographic_gen.py` (for the DM infographic) is separate/unrelated to this chain — run it whenever, it just needs to land in "📊 DM Infographic" before the row goes live.

Automation only starts once a human drags **Stage** in the social-ip-engine-side Production Tracker:
- `🟢 Ready to Publish` → Notion Automation → `POST /admin/notion-sync` — auto-drafts the comment-keyword DM rule, auto-FETCHES (doesn't generate) whatever's already in "📊 DM Infographic".
- `✅ Published` → Notion Automation → `POST /admin/notion-publish` — auto-generates/reuses a cover photo if missing, then actually publishes the "Production Video" file live to Instagram.

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
- **⚠️ The 即梦 hang-lottery (root-caused 2026-07-10, 236-task analysis).**
  ~45% of audio-driven multimodal2video submissions (and ~35% of image2video)
  hang in `querying` FOREVER — never scheduled, never failed, never charged
  (tasks from 2026-06-25 still answered `querying` on 07-10). When a task DOES
  run, vip is genuinely fast: 81% of successes <5 min, 95% <15 min, NONE ever
  succeeded past ~62 min. So a task `querying` >15 min is a lost lottery
  ticket: **the fix is resubmitting the same task ("retry usually works"),
  NOT waiting and NOT downgrading quality.** Rules encoded in
  `notion_video.py`: (1) poll 10 min per attempt, up to 3 multimodal attempts
  per shot; (2) image2video fallback only on an EXPLICIT `gen_status=fail`
  (content problems: two-person frame, no face), never on a hang; (3)
  pre-flight only blocks when a task submitted <15 min ago is still
  `querying` (might genuinely be rendering) — old hung tasks don't block;
  (4) hung submit_ids stay in `video_submits.json` — a rare late-completer
  can still be harvested with `--collect` (dashboard: 收割已提交).
- `query_result` answers `querying` even for long-dead tasks — it is NOT
  evidence a task is alive. `list_task` reads a local sqlite cache
  (`~/.dreamina_cli/tasks.db`) that goes stale unless each id is re-queried.
  There is NO task-cancel API in the CLI.
- `CreditPreDeductNotEnough` (ret=1006) = credit balance can't cover the vip
  pre-deduct — check `dreamina user_credit` before batches (dashboard shows it
  in the topbar; a 4-shot vip batch on a ~29-credit balance is asking for a
  mid-batch failure).
- Result video URL: `result_json.videos[0].video_url`.
- **Realistic talking-head + audio is flaky** — retry usually works. **Two people in one image (e.g. doctor + patient) hangs 即梦** — for those shots use `image2video` (motion only) or ffmpeg Ken Burns + voiceover, OR regenerate as a single person.
- **Lip-sync requires a near-frontal face** — side/profile angles (>30° off-axis) cause multimodal2video to fail silently → Ken Burns fallback. Always generate image prompts with face ≤15° off-axis when lip-sync is needed.
- Audio must be 2–15s.

## Local dashboard (`dashboard/`, added 2026-07-08)

`python3 -m uvicorn dashboard.app:app --port 8420` (from `studio/`) → browser control panel for the whole 6-stage pipeline: workbench view groups every Production row by "what do I do next", row detail shows shot images/audio/videos/cover/infographic inline (review without opening Notion), every button subprocess-invokes the existing `scripts/*.py` tools verbatim (pipeline_common.py precedent — ZERO pipeline logic reimplemented), job logs stream live via SSE. **Stateless: Notion is the only source of truth** — every screen load re-reads Notion, so dashboard and manual-Notion edits can never diverge. Publish is gated behind a hard confirm dialog (irreversible). Local-only, never deployed. Unverified: whether a Notion Automation fires on an API-set Stage change same as a manual drag — check on first real dashboard-driven publish; fallback is one line (call the webhook directly after the Stage PATCH).

## Conventions
- Each shot ≤13s (OmniHuman/即梦 sweet spot). Scripts: ONE line per shot in the row's Script property, in the IP's language.
- Every content gives an on-screen QUICK WIN before the comment CTA (don't only tease).
- 9:16 vertical, warm TCM clinic. Comment-keyword CTA (e.g. "gut", "detox", "stomach") + follow.
- Generated media → `campaigns/_generated/<row_id>/` (gitignored). Source assets (clinic bg, IP faces) → `campaigns/assets/` (tracked).
