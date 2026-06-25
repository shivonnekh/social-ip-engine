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
