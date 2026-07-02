# Shello Memory — ai-tcm-ip

## Session — 2026-06-05

### What happened
Research session on social media auto-reply (IG/TikTok/FB) + voice config unification.

### Decisions
- **Social media**: Composio MCP has 0 triggers for IG/FB/TikTok — wrong tool for auto-reply. Best path: extend existing FastAPI server with `/webhook/instagram` (Meta Graph API webhooks), or use n8n for visual workflow. TikTok comment-to-DM blocked in HK — bio link only.
- **Voice config unified**: `campaigns/voice_config.yaml` created as single source of truth. `gen_voice_clip.py` now loads defaults from it — no more manual `--voice --pitch` flags needed.
- **Confirmed MiniMax params** (verified by Shivonne 2026-06-05):
  - Voice: `Cantonese_GentleLady`
  - Speed: 1.0
  - Pitch: +1 (甜啲後生啲；切忌 +4/+6 chipmunk)
  - Emotion: none
  - Model: `speech-2.8-hd`
  - Language: `Chinese,Yue`
  - Audio: mp3 / 32000 Hz / 128000 bps
  - Endpoint: `https://api.minimax.io/v1/t2a_v2`
- **Bug fixed**: Old DEFAULT_VOICE was `Cantonese_KindWoman` (ported from TCM-Jessica) — corrected to `Cantonese_GentleLady`
- **逗號注意**: 「，」令 MiniMax 插停頓，寫稿少用逗號

### Still open
- TikTok: no comment-to-DM in HK — bio link strategy only
- Campaign 01 clips 2–6 — 待稿

## Session — 2026-06-10

### What happened
Built + tested the Meta (Instagram/Facebook) webhook receiver — Phase 1 (receive + log events).

### Built
- `server/webhook.py` — FastAPI receiver:
  - GET `/webhook/instagram` → verify handshake (echoes hub.challenge if META_VERIFY_TOKEN matches)
  - POST `/webhook/instagram` → verifies X-Hub-Signature-256 HMAC vs META_APP_SECRET, logs raw event + human-readable one-liner
  - GET `/health`
- `server/requirements.txt` (fastapi, uvicorn)
- `server/.env.example` + local `server/.env` (gitignored)
- Local verify token (TEST): `chenzhiqing_tcm_2026`

### Tested ✅
- Local: health, verify (correct + wrong token 403), POST comment event parsed → `instagram/comments from=test_user text='gut'`
- Public via **ngrok**: handshake echoes challenge, HTTP 200. (cloudflared quick tunnel was flaky — edge 404, switched to ngrok.)
- ngrok URL (ephemeral, laptop-dependent): https://michele-linguistical-unslyly.ngrok-free.dev/webhook/instagram

### Still open / next
- **User dashboard steps**: create Meta Developer App, IG Business acct linked to FB Page, register callback URL + verify token, subscribe to `comments`+`messages` fields
- Set real `META_APP_SECRET` in server/.env once app exists (then signature check active)
- **Deploy to Render** for persistent URL (ngrok dies on laptop sleep / URL rotates) — OR add endpoint to always-on TCM-Jessica server
- Phase 2: wire AI auto-reply (keyword "gut" → private DM via Graph API)
- Meta App Review (~2wk) for `instagram_manage_messages` + `instagram_manage_comments` before production

## Session — 2026-06-23
What happened: Researched Dreamina OmniHuman API options (image+audio→lipsync video; takes own audio, not TTS — perfect for our MiniMax clips). Generated Campaign 02 (cinnamon-pineapple detox) English VO and split into 4 clips ≤13s.
Decisions:
- **English VO config (LOCKED, = tonsil-stone v5-s1.2):** `voice=elderly_man, speed=1.2, pitch=0, emotion=none, MINIMAX_TTS_LANGUAGE=English`. Run via gen_voice_clip.py with --voice elderly_man --speed 1.2 --pitch 0 and env MINIMAX_TTS_LANGUAGE=English.
- OmniHuman provider recommendation: fal.ai easiest (Authorization: Key, accepts base64/local upload, ~$0.16/s on v1.5, both 1.0+1.5). PiAPI cheapest ($0.13/s, 1.5 only, needs public URLs). BytePlus/Volcengine official = HMAC signing, only for scale.
- All providers accept a pre-recorded AUDIO FILE → feed our clips directly. 13s clips are in OmniHuman's quality sweet spot (<15s).
- Detox split = 4 clips (hook / recipe / TCM-why / CTA), all ≤13s. Removed "1. 2. 3." numerals from recipe for clean TTS.
- Audio cut method: whisper small.en --word_timestamps → group by sentence terminal punctuation → pack into ≤13s, cut in silence gaps. Reusable.
Still open:
- Which OmniHuman platform does Shivonne's API key belong to? (decides integration code)
- Which portrait/avatar image pairs with Campaign 02
- Tonsil-stone (Campaign 01) had 5 clips in voice/segments/ from earlier this session

## Session — 2026-06-24
What happened: Built then restructured the AI-IP Notion board to support multiple IPs (target ~10). Moved from single-DB to a 3-DB relational model + reusable fan-out script.
Decisions:
- **Notion board = 3 linked DBs** (page 389f2a3f432080678683fb82eb056ee6):
  - 📚 Content Library (content_db 389f2a3f-4320-81f8-9428-cd01f1d36add) — language-agnostic master concepts. Fields: Name, Topic, Hook, CTA Keyword, Master Script, Concept Status, Notes.
  - 👤 IP Registry (ip_db 389f2a3f-4320-8155-bb64-c4a576610bef) — per-IP profile = SOURCE OF TRUTH for voice config. Fields: IP, Language, Persona, Dimension/Market, voice_id, Speed, Pitch, Language Boost, Emotion, Avatar Image, Platform Handles, Active. Seeded 2 active (🌸 Jessica HK = Cantonese_GentleLady/1.0/+1/Chinese,Yue; 👴 Dr. Chen EN = elderly_man/1.2/0/English) + 8 inactive placeholders IP-3..IP-10.
  - 🎬 Production Tracker (prod_db 389f2a3f-4320-817b-9363-f09b0c4b04b2) — junction: 1 row per Content×IP. Dual relations to both DBs + Stage(7), Image/Voice/Video checkboxes, Translated Script, Publish Date, Platform, Assets, Notes.
- **Why 3 DBs not multi-select:** each IP has independent production state/assets/publish date/language → can't live in one row. Master script written once, 10 renditions relate to it.
- **Scaling mechanism = fan-out**, not manual rows. `scripts/notion_fanout.py --content "<name>"` explodes a concept into 1 Production row per ACTIVE IP, pre-filling each IP's voice config in Notes. Dedup built in (skips already-linked IPs). `--all-ips` includes inactive, `--dry-run` previews. DB ids in `scripts/notion_ids.json` (not secret). Token via NOTION_KEY env only.
- Notion API can't create Board/Calendar VIEWS or "status"-type props — used select for stages; user must add Board/Calendar view in UI manually.
Still open:
- ⚠️ Tell Shivonne to ROTATE the Notion token (pasted in plaintext in chat).
- Need real IP list (languages + personas + voice_ids) to fill IP-3..IP-10 and mark Active.
- Per-IP translated scripts: Cantonese/other-language renditions need translation step (master is EN).
- Next: wire generation pipeline to READ IP Registry voice config + iterate Production rows.

## Session — 2026-06-24 (cont.)
What happened: Built trainer-handoff onboarding for the Notion board. First a standalone Playbook page, then (per Shivonne's clarification) moved to in-ROW guides.
Decisions:
- Notion API CANNOT create DB "templates" (UI-only). Workaround: inject a step-by-step checklist into each Production row's page BODY.
- `scripts/notion_row_guide.py` = single source of truth for the in-row guide (build_guide_blocks). Uses to_do checkboxes + copy-ready code blocks (GPT prompt, MiniMax config). GUIDE_MARK sentinel "🧭 PRODUCTION CHECKLIST" prevents double-injection. `--backfill [--force]` applies to all existing prod rows.
- `notion_fanout.py` now imports apply_guide → every fanned-out row auto-gets the checklist. So both manual-via-template and script-created rows are covered.
- Also built standalone Playbook page (▶️ 389f2a3f432081568ab3ca0d253b1639) + blue entry callout at board top. Kept as overview; in-row guide is the primary UX.
- IP note: user renamed Dr. Chen → "Jackie Chan (EN)" in UI (seen in screenshot). voice config still elderly_man/1.2/0/English.
Still open:
- Optional: user adds a UI default template on Production Tracker so manually-created "New" rows also get it (API can't). Or just always use fan-out.
- Optional: pre-bake the 4 SCENE prompts per concept (tonsil/detox) so operators copy-paste with zero edits.
- Still: rotate Notion token; fill IP-3..IP-10.

## Session — 2026-06-24 (cont. 2)
What happened: Closed the loop on the trainer-handoff "click → fill → auto" flow. Honest about 2 Notion limits (no API UI-templates, no native multi-row trigger) and shipped working workarounds.
Decisions:
- Added "🚀 Fanned out" option to Content Library → Concept Status select. Flow: 💡 Idea → ✍️ Scripted → ✅ Ready to fan-out → (watcher) 🚀 Fanned out.
- Content Library NOTE: real prop is "CTA" (not "CTA Keyword"). Props: Name, Hook, CTA, Master Script, Topic, Notes, Concept Status, Related to Production Tracker (Content).
- Created TEMPLATE concept row "📝 TEMPLATE — duplicate me" (389f2a3f432081e385d3ef841e9c972d) with body scaffold (Master Script + 4-shot 分镜指南 + property hints). Duplicate-row pattern stands in for UI template (API can't make UI templates).
- `scripts/notion_watch.py` = auto-fan-out watcher. Finds concepts with Concept Status="✅ Ready to fan-out" → fans out to active IPs (dedup) → injects in-row guide → flips concept to "🚀 Fanned out". Modes: single run / --loop N / --dry-run. Skips 📝 TEMPLATE row. E2E tested live (created 2 rows w/ guide + correct per-IP voice config, then cleaned up).
- Full pipeline now: duplicate TEMPLATE → fill → set Ready → run notion_watch.py → Production rows appear per active IP, each with checklist → operator opens row, follows steps.
Scripts in repo: notion_ids.json, notion_fanout.py, notion_row_guide.py, notion_watch.py.
Still open:
- Real-time (the instant status flips) needs hosted Notion webhook + server — future upgrade. For now: cron/launchd the watcher, or --loop.
- UI: optionally promote TEMPLATE to a real DB default template + add Board/Calendar views.
- Still: rotate Notion token; fill IP-3..IP-10; pre-bake per-concept SCENE prompts (optional).

## Session — 2026-06-24 (cont. 3)
What happened: Closed the storyboard→prompt automation gap. Rows weren't auto-generating image prompts because Notion formulas can't read a linked page's body — the in-row template had a static <paste SCENE> blank.
Decisions:
- Built `scripts/notion_prompts.py`: reads linked Content concept's 分镜指南 (parses 🎥 Visual + 🗣️ line per Shot heading) + IP Persona → writes finished GPT image prompts into the Production row body as copy-ready code blocks (one per shot). Sentinel "🖼️ IMAGE PROMPTS" prevents dupes; --force wipes sentinel-to-end and rebuilds.
- Smart prompt: B-roll shots (visual contains "b-roll", no "talking head") → no-person product prompt; else "same person from photo (persona)" talking-head prompt. Persona auto-pulled from IP Registry.
- Storyboard structure in concept body: heading_2 "🎬 Shot Guide", heading_3 "Shot N · ...", bullets "🗣️ <line>" / "🎥 <visual>" / "💡 <overlay>". Prop name in prod_db for script = "Script" (renamed from Translated Script).
- Wired apply_prompts into notion_fanout.py AND notion_watch.py (after apply_guide) → every new row auto-gets guide + filled image prompts on creation. Backfilled existing 4 rows (4–5 prompts each).
Pipeline scripts: notion_ids.json, notion_fanout.py, notion_row_guide.py, notion_prompts.py, notion_watch.py.
Still open: rotate token; fill IP-3..IP-10; optional auto-attach generated voice/images into row body (file upload API works — tested w/ detox EN clips); optional auto-copy EN master into Script for English IPs.

## Session — 2026-06-25 (cont. image+video pipeline)
What happened: Built the full media-gen tail of the pipeline — image gen (GPT) + video gen (即梦 CLI) — wired to Notion.
Decisions:
- **Image gen** (`scripts/notion_image.py`): pulls IP reference photos FROM the Notion IP page (image blocks = source of truth, re-downloaded each run since Notion URLs expire) + a clinic bg → OpenAI `gpt-image-2` (key in .env, IMAGE_MODEL=gpt-image-2) → places each shot image in a "🖼️ Image here" toggle under that shot's image prompt → ticks 🎨. Uses each shot's OWN Notion image prompt. --shot N (one), --reuse (skip regen), skip-if-toggle-exists. Timeout 300s.
- **Image prompt rules** (build_prompt): ONE single frame (no split/collage), patients allowed (no blanket "no extra people"), identity-lock only on the doctor when present.
- **Reference faces**: real Jackie Chan refs live on the IP Notion page (3 imgs, beardless). Do NOT use AI-generated candidate. notion_assets.json clinic_bg paths; faces map is override-only.
- **Video gen** (`scripts/notion_video.py`): uses the official 即梦 CLI `~/.local/bin/dreamina` (logged in, maestro VIP, ~10k credits). Command = `multimodal2video --image --audio --prompt --ratio 9:16 --duration <2-15> --model_version seedance2.0fast_vip`. **VIP models (_vip) SKIP the queue** (non-vip queue is 500k+, hours). Pulls per-shot image+audio+即梦prompt from Notion; resolves the 即梦 prompt ({{图片}}→--image, {{对白}}→--audio, rest→--prompt); submits all → polls → downloads (video url at result_json.videos[0].video_url) → places each in "🎬 Video here" toggle → ffmpeg concat → final.mp4.
- Lip-sync CONFIRMED good (Shivonne approved shot1_vip.mp4: 720x1280 9:16, 8s, AAC audio, correct beardless doctor).
- Notion file upload API works for png/mp3/mp4 (single-part <20MB).
- Committed pipeline on branch feat/notion-content-pipeline (commit 93416c1) — that was before image/video scripts; need a follow-up commit for notion_image.py/notion_video.py/notion_assets.json.
Still open:
- Follow-up git commit for notion_image.py + notion_video.py + notion_assets.json + assets.
- Knee × Jackie: Shivonne settled it herself.
- Jessica (Cantonese) image+video not yet generated.
- Rotate Notion + OpenAI tokens (pasted in chat).

## Session — 2026-06-25 (cont. style guide + 养胃)
STYLE GUIDE (locked rules for ALL future content):
- **Richness lives in the Content Library Shot Guide (🎥 Visual), NOT the production 即梦 prompt.** The 即梦 prompt is DERIVED from the Shot Guide by apply_shot_plan. To enrich the video, write a RICH cinematic 🎥 Visual (action, insert/cutaway shots, framing/景别 changes, transitions — e.g. "talking head leans in, quick cut to pineapple"). Then re-run apply_shot_plan; 即梦 prompt auto-updates.
- **Drop the GPT image-prompt section** for new content. Per-shot blocks now = 🗣️ Voice script + 🎬 即梦 prompt (rich) + empty "🖼️ Image here" + empty "🎬 Video here" toggles (left blank to drop assets in later).
- 即梦 prompt (build_jimeng_prompt) now: 分镜指令(=Shot Guide visual) + "画面要生动丰富(动作/插入空镜/景别变化)" + {{图片}}/{{对白}} variables + read-language (from IP) + 运镜(by shot beat) + AI-digital-human disclaimer.
- The single-frame/"one moment/no collage" rule was for IMAGE gen only — for 即梦 VIDEO, multi-beat/cuts/inserts = GOOD (richer).
Built: NEW concept "🍵 Stomach pain after meals" (38af2a3f4320818f9e45de56db178bea) with rich shot guides + EN(Jackie)/粤语(Jessica) shot-aligned scripts. Production rows: Stomach × Jackie (38af2a3f4320811587e6c221d16f396d), Stomach × Jessica (38af2a3f4320812782ced078d6b169bf) — new style (no image prompt, rich 即梦, blank Image/Video toggles). Added Topic option 🍵 Stomach.
Still open: commit generator changes + notion_video.py + new concept. Sleep shot3 real-motion still waiting on 即梦 throttle (poller bnpmqas5o). Don't touch existing content (Sleep/detox/tonsil/knee).

## CORRECTION (2026-06-25): Image prompt is KEPT
- Earlier note "drop image prompt" was WRONG. BOTH prompts are needed, derived from the SAME Shot Guide 🎥:
  - 🖼️ Image prompt = SINGLE frame (apply via _primary_beat(): take the first/primary beat of the rich shot guide, drop cuts/inserts/transitions) → GPT generates the still.
  - 🎬 即梦 prompt = FULL rich shot guide → animates the still into video.
- Per-shot blocks (final): 🖼️ Image prompt → 🗣️ Voice script → 🎬 即梦 prompt → empty 🖼️ Image here → empty 🎬 Video here.
- Pipeline: GPT still (from image prompt) → 即梦 multimodal2video(still + audio + rich 即梦 prompt) → video.

## Session — 2026-06-29
What happened: Full campaigns/ folder reorganization + script updates.
Decisions:
- **New layout**: `campaigns/<campaign>/<ip>/voice|images|video/` — everything under campaign name
- All 3 scripts (`notion_video.py`, `notion_image.py`, `batch_voice_gen.py`) now resolve output path from Notion row: content title slug + IP title slug → `campaigns/<content-slug>/<ip-slug>/`
- `_slugify()` and `_campaign_workdir()` helpers added to each script
- Deleted `campaigns/_generated/` (gitignored runtime output, nothing precious)
- Moved `campaigns/voice_clips/*.mp3` → `campaigns/menstrual/jessica/voice/`
- Moved `campaigns/voice_config.yaml` → `scripts/voice_config.yaml`
- Restructured existing `00-intro`, `01-05` campaign folders: added `<ip>/voice/` subdirs, moved files, deleted `01-tonsil-stone/video/` debug screenshots (kept final video under `jackie-chan/video/`)
- `.gitignore` updated: added `campaigns/**/images/`, removed `campaigns/_generated/`
Still open:
- Scripts will create slug-based folders (e.g. `tonsil-stone/`) while existing folders use numbered names (e.g. `01-tonsil-stone/`). Minor inconsistency — fine for now, converges as new runs happen.
- `menstrual` campaign has voice clips but no Notion concept yet.

## Session — 2026-06-29 (cont. — video gen + IG reel editor skill)
What happened: Fixed Migraine video gen (audio too long), built dry eyes Instagram reel, adapted brand-video-editor skill for 9:16.
Decisions:
- **Migraine Shot 2 audio fix**: voice clip was 15.84s — exceeds 即梦's 15s hard limit (credits=None = rejection). Shortened script to 34 words → 12.55s. Regenerated TTS. Ready to re-run notion_video.py for shots 2 & 3.
- **Dry Eyes Shot 2 voice**: changed "1 and 3am" → "1 to 3am". Old audio block deleted, new clip regenerated.
- **has_video detection**: `read_row_shots()` now checks "🎬 Video here" toggle children for actual video blocks before submitting — prevents duplicate submissions on retry.
- **Sequential submission**: `main()` now submit → poll → place → next shot (avoids 即梦 queue throttling).
- **干眼 Instagram Reel v2** (`/Users/shivonne/Downloads/dry_eye_reel_v2.mp4`): 4 shots concatted, word-by-word captions (ArialHB, white + black stroke, `caption` method), 3 PIL info cards as B-roll (Liver-Eye Connection 3s, Symptoms 4s, TCM Protocol 4s). 720×1280, 53s, 8MB.
- **IG Reel Editor skill**: adapted brand-video-editor (YouTube, 16:9) → `scripts/skills/ig-reel-editor.md` (Instagram Reels, 9:16). Key changes: 1080×1920 canvas, ≤90s, hook ≤1.5s, word-by-word captions in lower-third (not YouTube auto-captions), avatar FULL in upper 60% with lower 40% for graphics, vertical card/list layouts, CTA card in last 3–4s, music bed −18dB (louder than YouTube), 8 anchor scenes covering hook/caption/number/list/b-roll/comparison/CTA.
Still open:
- **Migraine × Jackie shots 2 & 3**: run `notion_video.py --row 38df2a3f-4320-81a1-a1a2-c3deb9b79eab` (shot 1 & 4 already done).
- **Dry Eyes × Jackie all 4 shots**: run `notion_video.py --row 38df2a3f-4320-819f-b0ea-ddcd6b550418` (all 4 images ready per Shivonne).
- Rotate NOTION_KEY and OPENAI_API_KEY (pasted in chat).

## Session — 2026-06-30 (Migraine IG reel edit)
What happened: Combined the 4 Dreamina shots from the "🤯 Migraine × Jackie Chan" Notion row (38df2a3f-4320-81a1-a1a2-c3deb9b79eab) into a finished IG reel via the ig-reel-editor skill.
Decisions:
- New builder: scripts/migraine_reel.py (adapted from dry_eye_reel_v3.py). Output: ~/Downloads/migraine_reel.mp4 — 49.4s, 720x1280, 30fps, ~8.5MB.
- **Mixed-FPS gotcha**: shot3 was 30fps, shots 1/2/4 were 60fps → caused slow-motion last time. Fix: pre-normalize ALL clips to 720x1280@30fps via ffmpeg into campaigns/migraine/jackie-chan/video/norm/ BEFORE moviepy. Durations preserved.
- Subtitles = PIL Arial Bold (white + 3px black stroke), word-by-word, lower third @75% — NOT moviepy TextClip (that's the square-box bug).
- Structure 1→4 with 3 B-roll cards between: setup card (3s) → 3-type comparison table (4.5s) → type→remedy table (4.5s). Hook overlay on shot1, CTA "migraine" card on shot4.
- Caption blackout windows: suppress word-by-word captions under hook (shot1 0-2.6s) + CTA (shot4 last 3s) to avoid text-on-text collision.
- Emoji (⚡◉) render as tofu in Arial — removed from all PIL text.
Still open:
- Final not yet pushed back to Notion row (offered).
- Videos downloaded to campaigns/migraine/jackie-chan/video/ (raw + norm/).

## Session — 2026-06-30 (cont. — Content Library buildout)
What happened: The 35 Chen-Tao batch concepts had Hook+CTA props but EMPTY bodies. Built full structure for all + backfilled 5 older ones. Library now 50/50 complete.
Decisions:
- **Gold-standard structure = the Migraine concept**: 📜 Master Script (EN) bullets + 🎬 Shot Guide (Shot N · 🎥 visual / 🗣️ voice / 💡 caption) + 📩 Material (PROTOCOL callout + 💬 First DM code + 🖼️ Infographic Brief code + 💬 Second DM code). 31 blocks total. Did NOT invent the Material format — replicated Migraine's.
- "DM Material / Infographic Brief" = the lead-magnet DM flow that fires when a viewer comments the CTA keyword. First DM ends with a qualifying question (triggers reply → opens DM window); Infographic Brief is a GPT image-gen prompt (vertical 4:5, TCM diagnostic aesthetic, flat icons, safety footer); Second DM delivers the infographic + soft next step.
- Source grounding: Chen-Tao analysis page (382f2a3f43208176bd49e2a2897f98ce) — each post toggle has original script + keyframe storyboard. Extracted to /tmp/chentao_source.json.
- Scripts authored comma-light (TTS), 4 shots, on-screen quick-win before CTA, remedies framed "try this / may help / support" + medical-safety footer in each infographic.
New files (untracked, not committed):
- scripts/build_content_bodies.py — generator (reads content_bodies_data.py, writes 31-block body; SAFETY: skips pages that already have body unless --force).
- scripts/content_bodies_data.py — CONCEPTS list, all 35 authored.
- scripts/append_material.py — non-destructive Material-only append for the 5 older concepts that had Script+Shots but no Material (Stomach, Knee, Sleep, Pineapple, Tonsil).
Result: 50/50 complete. Flipped the 35 from 💡 Idea → ✍️ Scripted (safe; only ✅ Ready to fan-out triggers notion_watch fan-out).
Still open:
- Concepts are scripted but not fanned out. To produce: set a concept's status to "✅ Ready to fan-out" (or run notion_fanout.py --content "<name>") → creates Production rows per active IP.
- Infographic Briefs are GPT-ready prompts, not yet generated into images.

## Session — 2026-06-30 (cont. — comment→DM auto-reply wiring)
Diagnosis of "why no comment reply / no DM": server/webhook.py HAS the reply code (_reply_to_comment + _private_reply_to_comment via Graph), but it never fires because config is empty — server/.env only has META_VERIFY_TOKEN. No brand IDs (JACKIE_IG_ID/PAGE_ID) → _brand_for_entry returns "unknown" → handler bails. No access tokens → can't call Graph. Render env vars (sync:false) must be set in Render dashboard, not local .env. Also: Meta app must be Live + subscribed to `comments` field, IG must be Business/Creator linked to a FB Page, perms approved (instagram_manage_comments + instagram_manage_messages).
What I built (all additive, tested):
- scripts/export_dm_map.py → server/dm_map.json: keyword→{first_dm,second_dm,infographic_brief} for all concepts. 49 keywords. normalize_keyword() pulls token from CTA ('Comment "tonsil"'→tonsil).
- webhook.py refactor: _maybe_reply_to_jackie_comment → _handle_comment (brand-agnostic, keyword-driven). Comment text → _match_keyword (whole-word) → send concept's First DM as private reply + public "Just sent you a DM 📩". Silent if no keyword/no token. Legacy reply-to-all behind REPLY_TO_ALL_COMMENTS env. Per-brand BRAND_ACCESS_TOKENS (Jackie + Chloe/Jessica).
- /diagnostics endpoint: reports verify/app_secret/brand IDs/tokens/dm_map/any_brand_ready. Current real state: dm_map_loaded=true(49kw) but any_brand_ready=FALSE (no IDs/tokens) — confirms why it's silent.
- server/test_webhook.py: 6 pytest tests (keyword match, send first_dm, silent w/o keyword, silent w/o token, diagnostics readiness, verify handshake). All pass. Needs httpx+pytest.
Content issue flagged: keyword "kidney" claimed by 2 concepts (Kidney Stones + Lower Back/Hip Pain) — need distinct keywords or auto-DM only sends one.
Still open / NOT done (needs Shivonne + Meta/Render, can't do from here):
- Set in RENDER dashboard: META_APP_SECRET, {JACKIE,CHLOE}_IG_ID + _PAGE_ID, {JACKIE,CHLOE}_IG_ACCESS_TOKEN. Then redeploy.
- Meta app: Live mode, subscribe webhook to `comments` (+ `messages`), approve instagram_manage_comments + instagram_manage_messages, IG=Business linked to FB Page.
- Verify videos are actually PUBLISHED (no live posts = no comments to reply to).
- Phase 2: attach the infographic image in the DM (private_replies text works now; image needs hosted URL + attachment flow) + Second DM on viewer reply (needs state/24h window). Generate infographics from the briefs.
- Commit: server/webhook.py, dm_map.json, export_dm_map.py, test_webhook.py, .env.example (not committed yet).

## Session — 2026-06-30 (cont. — Script property auto-fill)
Problem: Production Tracker rows had empty Script property. Root: apply_shot_plan READS the per-shot voice FROM the Script property (notion_prompts.py:379-381), falling back to storyboard EN line only when empty — but nothing POPULATED the Script property at fan-out. So Script property = source of truth, was never set.
Fixes:
- Backfill (one-time): scripts/fill_script_property.py — reads each Production row's BODY 🗣️ Voice script code blocks → writes Script property (one line per shot). Filled the 10 empty rows (Jackie/EN). Safe (--force to overwrite, --dry preview). All 18 rows now filled.
- Permanent wiring: notion_prompts.py new funcs — _translate_lines (EN→IP language via _openai_chat, comma-light for TTS, keeps EN keyword; only translates 粤/mandarin/spanish/etc, else passthrough), script_lines_for_ip(concept_id, ip_id), apply_script_property(row_id, force=False) (sets Script from storyboard lines in IP language; only if empty). _openai_chat now takes max_tokens param.
- notion_fanout.py: calls apply_script_property(row) BEFORE apply_shot_plan(row) so body voice derives from the now-filled Script. Proven E2E: fanned out Migraine → new "Migraine × Jessica" row, Script auto-filled Cantonese (4 shots), body matches.
Design note: Script property is canonical per-shot voice (ONE LINE PER SHOT, IP language). Jackie=EN verbatim, Jessica=auto Cantonese. To re-translate/overwrite use apply_script_property(force=True).
Still open: commit all the new scripts (content_bodies_data, build_content_bodies, append_material, export_dm_map, fill_script_property, webhook changes, dm_map.json, test_webhook). Nothing committed yet this session.

## Session — 2026-06-30 (cont. — per-IP fan-out, scheduled job, MiniMax punctuation)
Answered 4 asks (all one system + 1 voice fix):
1. PER-IP TARGETING: added "Fan out to" multi-select to content_db (options=all IP short names). notion_watch.py rewritten: targets = concept's "Fan out to"; EMPTY → default ["Jackie Chan"]. Maps name→IP via short_ip_name (includes inactive, selection=intent). Dedup via existing_pairs → only creates MISSING Content×IP rows (so re-running to add a new IP later is safe). Creates row → apply_script_property (Script in IP lang) → apply_shot_plan (body) → voice (Jackie). Flips to 🚀 Fanned out only if no unknown IP names.
2. SCHEDULED JOB: scripts/run_watch.sh (loads .env, runs one tick). deploy/com.chatdaddy.tcm-fanout.plist (launchd, every 300s, RunAtLoad, logs /tmp/tcm-fanout.{out,err}). render cron snippet + full guide in deploy/AUTO-FANOUT.md. notion_watch.py flags: --loop N, --dry-run, --no-voice (voice ON by default).
3. "ADD NEW IP LATER / BUTTON": documented — add IP to Fan out to + set status back to Ready (Notion Button property: Edit pages→Concept Status→Ready). Watcher dedups, creates only new IP row. Notion buttons can't run our code/fill body — that's why watcher exists; button just flips the trigger.
4. MINIMAX PUNCTUATION (user: voice sounds fake/no pauses): EMPIRICALLY TESTED — same line 6.86s(no punct) → 8.49s(. , —) → 9.43s(<#0.4#> tags). MiniMax DOES respect punctuation + the <#x.x#> pause-tag syntax works. Root cause of robotic voice: (a) old CLAUDE.md "minimize commas" rule over-applied, (b) my Cantonese translation prompt replaced commas→spaces. FIX: _translate_lines prompt now KEEPS natural punctuation (，。？). Regenerated Yellow Teeth×Jessica + Migraine×Jessica (Script force=True + body rebuild) — now punctuated. Updated CLAUDE.md voice rule (reversed). batch_voice_gen sends text verbatim (no stripping) — EN scripts already have punctuation, so Jackie was fine; Jessica was the culprit.
Design decision flagged to user: empty "Fan out to" = Jackie default (vetoable).
NOT done (left for user): did NOT install launchd or run a live full fan-out pass — several concepts already in "Ready to fan-out" (Bad Breath, Skin Tags, Dry Cracked Heels...) would fan + generate ~30-40 voice clips. Recommend manual ./scripts/run_watch.sh --dry-run first. Voice path only Jackie (synthesize is Jackie-hardcoded); other IPs get rows+scripts, voice TBD. Still uncommitted: large pile this session.

## Session — 2026-07-01

### What happened
Full tracker cleanup + batch production session. Fixed systemic issues with Notion checkboxes, emoji consistency, and a critical bug in notion_video.py.

### Decisions
- **notion_video.py BUG FIXED**: Was using `image2video` (no audio) + ffmpeg mix → now correctly uses `multimodal2video --image --audio --ratio 9:16`. Old videos had random mouth movements with audio overlaid, not lip-synced. Fix is live.
- **`--regen` flag added**: Bypasses `has_video` check, saves as `shot{N}_regen.mp4`, appends `🎬 Video (regen)` toggle in Notion without touching existing content.
- **`--shot N` flag added**: Targeted single-shot retry (avoids re-running all shots and adding duplicate regen toggles).
- **Audio download always force-refreshed**: `_download(..., force=True)` for audio so cached local files don't override fresh Notion clips.
- **Checkbox sync**: 16 rows had voice audio in body but 🎙️ unchecked → patched. Detox Juice Jackie also had 4 video blocks undetected → video checkbox patched.
- **Emoji titles**: 55 rows updated (40 Content Library + 15 Production Tracker). Also fixed 2 truncated "Jackie Cha" → "Jackie Chan" names.
- **Batch voice gen**: 30 clips generated across 7 rows (Onion, Cracked Heels, Skin Tags, Bad Breath Jackie + Migraine, Stomach, Tonsil Stone Jessica). All rows now have audio.
- **Videos completed (regen, correct)**: Yellow Teeth Jackie (4 shots, all ✅), Stomach Jackie (in progress, shot 1 ✅).

### Still open
- Stomach Jackie regen: 4 shots remaining (running in background)
- Image gen for 17 voice-ready rows (none have images yet — biggest unlock)
- Migraine reel at ~/Downloads/migraine_reel.mp4 — ready to post, hasn't been posted
- Jessica channel: Yellow Teeth, Tonsil Stone, Migraine Jessica all have voice, no images
- Render env vars still needed for IG auto-reply to activate (JACKIE_IG_ID, JACKIE_IG_ACCESS_TOKEN etc.)

## Session — 2026-07-01/02 (comment→DM saga — found the REAL live repo, fixed the actual bugs)

### What happened
Started as "why hasn't the eye post comment been replied to" and turned into discovering `ai-tcm-ip/server/webhook.py` was NEVER the live thing — a completely separate, unrelated repo (`TCM-Jessica`, `/Users/shivonne/Claude Code/TCM-Jessica`, deployed at tcm-jessica.onrender.com) is the actual live Jackie/Chloe IG bot + Jessica WhatsApp bot, with real customers. Spent this session almost entirely in that repo. Full detail in TCM-Jessica's own `scripts/memory/shello.md` — this entry is the ai-tcm-ip-side summary.

### Decisions
- **ai-tcm-ip = content factory only, TCM-Jessica = the live bot.** CLAUDE.md updated on both sides with this boundary — cost real time confusing the two twice in one session.
- **`server/webhook.py` in this repo is dead code** — never deployed, don't build it out further; any comment→DM/live-bot work belongs in TCM-Jessica.
- **Infographics already generated here** (`server/static/infographics/<brand>/<keyword>.png`) get manually copied into TCM-Jessica per-keyword — no automated bridge for images yet, only for DM text (via TCM-Jessica's own `notion_sync.py` hitting Notion directly).
- **Always check the Production Tracker row's "📊 DM Infographic" toggle before regenerating an image** — `batch_infographic_gen.py` often already ran and uploaded it there (found this for sleep/eye/migraine keywords that already had real images sitting unused).
- `server/dm_map.json` in this repo is STALE — `export_dm_map.py` was refactored to nest per-brand but the actual file on disk is still flat, never regenerated since. Not urgent (TCM-Jessica doesn't read this file at all), but noted so nobody trusts it as current.

### Still open
- `dm_map.json` staleness — regenerate via `export_dm_map.py` if anyone actually starts relying on it again.
- No automated image bridge (ai-tcm-ip infographic → TCM-Jessica media/guides) — still manual per keyword.
