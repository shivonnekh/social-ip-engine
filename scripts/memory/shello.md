# Shello Session Memory — TCM-Jessica

## Session — 2026-05-26

### What happened
Massive day. Started on production bug triage (CRM `list_phones_for_upcoming_appointments` missing), expanded into 15 commits across model migration, query understanding, sales payload enrichment, vision-based tongue progress tracking, full QA agent team sweep, and ended with an emergency prod-down fix for a Postgres column migration bug I caused.

### Major work shipped (15+ commits)
- **CRM**: `list_phones_for_upcoming_appointments` (Postgres + SQLite), idempotent column migrations
- **Memory consolidator**: auto-summary across sessions (gpt-5.4-mini, ~$0.0003/run)
- **Farewell summary** with CRM-aware closing (constitution + pain_points + appointments)
- **Returning user** proactive follow-up using prior pain_points
- **Tongue progress agent** — vision before/after comparison + image attach
- **Acupoint routing** — initially hardcoded map, then refactored to pure KB vector search (user pushed back on hardcoding)
- **Sales payload enrichment** — name + price + 功效 (indications) + image MANDATORY for every product mention
- **Phase 1 model migration** — gpt-4o-mini → gpt-5.4-mini (forced by deprecation deadline)
- **Phase 2 Planner query understanding** — rephrase + extracted_pain_points NER in single LLM call
- **QA agent team**: 3 parallel agents (Sales/Constitution/Conversation) — found + fixed 7 real bugs, added 17 tests, total 511 passing

### Critical bugs found + fixed today
1. `max_completion_tokens` API change for gpt-5.x — every LLM call was failing
2. Constitution agent persisting findings on rejected tongue → infinite loop trap
3. Mid-constitution rule had no escape — non-MCQ messages got force-routed
4. "OK 三點" misclassified as farewell, breaking appointment confirmation
5. Multi-clause farewell (>15 chars) missed by length gate
6. Writer `MAX_BUBBLES=5` silently dropping 3rd product (the screenshot bug)
7. Sales `writer_hint` saying `方向:` instead of new `功效:` template
8. ConstitutionAgent never persisted TongueRecord → tongue progress bootstrap impossible
9. Multi-symptom turns only extracting first match → CRM lost subsequent complaints
10. Skin complaints never persisted to pain_points (skin keywords intentionally excluded)
11. Complaint+Emotion mix → complaint rule won, lost 七情/臟腑 framing
12. **PROD-DOWN**: `UndefinedColumnError: last_period_start` — `CREATE TABLE IF NOT EXISTS` doesn't add new columns to existing tables. Added ALTER TABLE ADD COLUMN IF NOT EXISTS.

### Decisions made
- **Stay on OpenAI** despite running parallel research on 6 providers (Anthropic / Grok / Kimi / DeepSeek / Gemini). gpt-5.4-mini at $0.75/$4.50 is cost/quality sweet spot for HK Canto + budget.
- **Vision on gpt-5.4-mini** not Gemini Pro — keeps single-provider stack, negligible cost diff at ~4 calls/user lifetime
- **Writer on gpt-5.4-mini** not Sonnet — cost ceiling, prompt engineering matters more than model tier
- **Postgres on free tier** until launch — expires 2026-06-20, user wants to wait
- **Don't push back on user UX intuitions** — they were right twice: hardcoded acupoint map was wrong (should be KB), Sales bare-pitch was broken (needs 功效 + 圖)

### Architecture observations worth remembering
- Planner now does 3 jobs in 1 LLM call (route + rephrase + NER) — clean design, gpt-4o handles it
- Two-rail extraction (LLM NER + keyword fallback) catches what LLM omits (gpt-5.4-mini has inconsistent extraction)
- Rule-based fast paths must propagate to NER fallback — easy to miss
- Schema migrations need ALTER TABLE for additive changes; CREATE TABLE IF NOT EXISTS is a trap

### Still open
- **Auto-deploy webhook broken** on Render since 2026-05-22 — needs dashboard intervention (manual deploy works via API as workaround)
- **Postgres free expires 2026-06-20** — upgrade to Starter ($7/mo) before launch or data lost
- **Testing gap**: no migration-path test for existing DBs (caused today's prod crash). Should add.
- **KB content gaps**: 三高 / 9 體質 deep dive / 情志 / 男性 / 中藥目錄 / 24 節氣 cards
- **Tongue progress monthly nudge** broadcast not built
- **Appointment district fallback** when user evasive (only `online_video` happy path tested)
- **Real-LLM end-to-end test for constitution** — happy path with valid tongue still untested in prod
- **Sales product cards** lack ingredients/材料 field — clinic team needs to fill

### Files touched (rough)
- `src/llm.py` (model split, max_completion_tokens fix)
- `src/llm_transcribe.py` (gpt-4o-transcribe migration)
- `src/agents/planner.py` (query understanding, multiple rule fixes)
- `src/agents/writer.py` (MAX_BUBBLES adaptive cap, 功效 template)
- `src/agents/sales_agent.py` (writer_hint + payload enrichment)
- `src/agents/constitution_agent.py` (persist TongueRecord, reset state)
- `src/agents/acute_pain.py` (rip hardcoded map, multi-symptom helper)
- `src/agents/memory_consolidator.py` (new)
- `src/agents/tongue_progress_agent.py` (new)
- `src/crm/repo.py` + `repo_pg.py` + `schema.sql` + `schema_pg.sql` (5 schema changes)
- `src/orchestrator/pipeline.py` (Phase 2 wiring, two-rail extraction)
- `scripts/persona_dry_run.py` + `qa_sales_flow.py` + `qa_constitution_flow.py` + `qa_conversation_flow.py` (new test harnesses)
- `docs/today-improvements-showcase.html` (client-facing showcase)
- `CLAUDE.md` (architecture update)

### Service URLs
- Prod: https://tcm-jessica.onrender.com
- Render service ID: `srv-d879lsmq1p3s73av6f80`
- Postgres ID: `dpg-d87ai33eo5us73duobj0-a` (free, expires 2026-06-20)

### Tonal notes for next session
- User trusts dry runs more than tests — they ask for "real run see real replies"
- User flags UX issues fast and accurately — listen carefully
- User runs the company; cost ceiling matters; quality not at all costs
- Auto-deploy issue not yet resolved — user has the dashboard, I don't

### Post-save addendum — 2026-05-26 late evening

- Prod-down fix `f234fc3` actually failed to deploy too (asyncpg + ALTER TABLE IF NOT EXISTS bug in Python 3.14 runtime — `AttributeError: NoneType has no attribute decode`)
- Wrote second fix `115805e`: moved PG column migration out of SQL into Python via `information_schema` lookup + conditional ADD COLUMN. Avoids the asyncpg protocol path entirely.
- Deploy `dep-d8arutjbc2fs73e50rc0` LIVE confirmed working.
- Lesson: asyncpg 0.31 + Python 3.14 has issues with DDL `IF NOT EXISTS` extensions. Use information_schema lookup instead.

## Session — 2026-05-29
What happened: Full day building WhatsApp poll button UX for MCQ constitution questions. Lots of back-and-forth on whether ChatDaddy poll votes can be read.
Decisions:
- Buttons infrastructure: fully wired (WriterOutput.buttons, _extract_buttons in pipeline, buttons on last bubble in router, send_message accepts buttons param)
- MCQ gets poll buttons (4 options = WhatsApp poll widget, not quick-reply buttons)
- Poll vote selection: CANNOT be read via webhook payload (pollReplyOptions always []) or REST API (poll.options has no vote counts). This is likely a WhatsApp E2E encryption limitation.
- Added /admin/webhooks/recent endpoint to read live webhook payloads
- Added WEBHOOK-RAW logger to capture raw POST body of poll vote events
- Updated webhook subscription to include message-update + message-insert
- fetch_poll_selection() implemented but consistently returns "" (no votes > 0 in REST API)
Still open:
- WEBHOOK-RAW log has NOT been captured yet with a vote on the new server (user hasn't voted since deploy at 06:51 HKT). Once they vote, check `render logs -r srv-d879lsmq1p3s73av6f80 | grep WEBHOOK-RAW` immediately.
- If WEBHOOK-RAW shows pollReplyOptions populated → update _extract_poll_selection() to read it
- If WEBHOOK-RAW shows empty → accept limitation, revert MCQ to plain ABCD text
- Appointment mode buttons (診所/電話) and post-pitch CTA buttons are ready to add (≤3 options = real quick-reply buttons, not polls)

## Session — 2026-06-03
What happened: Built group chat support for Jessica. She now listens silently in groups and only replies when @-mentioned or her name is used.

Decisions:
- **Group CRM key**: `g_<sender_lid>` (per-person, not per-group) — each member gets own record
- **Mention detection**: mentionedJids JID match → quote-reply → @<digits> → @<name> → bare name (word boundary for ASCII, substring for CJK)
- **Bare name added** (linter update): ChatDaddy confirmed non-WABA accounts don't deliver mentionedJids — so "jessica你好" with no @ must also trigger REPLY. Already updated in group_gate.py.
- **Bot JID = 85252417448** — same number as ORDER_WHATSAPP (clinic uses one WA number for both). Wired into render.yaml as JESSICA_BOT_JID.
- **JESSICA_BOT_NAMES** defaulted to "Jessica,jessica,Jessica姐" in render.yaml
- Silent listen path: keyword-scan pain_points + capture sender_name + append to conversation_history. Zero LLM cost.

Still open:
- Group CRM records (g_<lid>) and DM records (phone) won't auto-link if same person uses both. Acceptable for now.
- Haven't tested in a real group yet — user should add Jessica to a test group and @-mention her
- Auto-deploy still broken — manual deploy via Render API as workaround
- Postgres free expires 2026-06-20 — upgrade before launch

## Session — 2026-06-03

### What happened
Heavy ship day across voice, conversation quality, group chat, infra, and a prod routing bug. Started from "MiniMax TTS still there?" → shipped voice-out; pivoted to convo/UX hardening via real dry-runs; debugged group chat end-to-end with raw webhook capture; user upgraded web service to Starter; closed with a prod 鬼打墙 routing fix found from a live trace.

### Shipped (11 commits, all live on prod)
- **Voice-out (MiniMax)** `e7c46f0` — `src/media/tts.py`, match-modality (only voice-reply when inbound was voice), `Cantonese_KindWoman`, atomic cache write, task-cancel guard. 30 tests.
- **Planner JSON escape fix** `e136625` — bd09d9f's inferred_patterns example had unescaped `{}` → str.format KeyError → apology on EVERY turn for ~2 days. Added test_prompt_template_render.py forcing function.
- **4 convo/UX fixes** `f71ad49` — found via live persona dry-run:
  - One-question rule (was stacking 3 questions/turn)
  - Bubble restraint (was maxing 5 bubbles every turn)
  - Acupoint media gating (faq_agent only attaches images when USER asks 穴位/按摩 — was scanning card body, pushing 6 images unprompted)
  - Forward motion (concrete next step on "點幫我", not fluff)
  - Before/after dry-run proved all 4 +辨證 surfaces naturally + converts to pitch
- **Group chat** `a456b41`+`f149e2d`+`9adfa93` — reply when name-addressed, listen+absorb CRM otherwise.
  - Fixed LISTEN crash (ConversationMessage built with text=/timestamp= but model is content=/at=datetime)
  - Set JESSICA_BOT_JID=85252417448 + names on live service
  - **KEY FINDING via /admin/webhooks/recent raw capture**: ChatDaddy sends NO mentionedJids on non-WABA — native @-tags arrive as plain text. So matcher now accepts bare name ("hi jessica" not just "@jessica"). ASCII word-boundary, CJK substring.
- **鬼打墙 routing fix** `adeaf9b` — prod trace showed "今天有什么汤水介绍" → appointment (pushed 視診), looped. Root: `_APPOINTMENT_INTENT_KEYWORDS` had bare time words 今日/今天/聽日/明天/幾點/幾時可以. Removed all. Tightened 地址→診所地址 (delivery address ≠ clinic q). 6 regression tests.
- **version-update-showcase.html** — stakeholder summary (voice/convo/group/reliability + DB deadline note)

### Infra
- **Web service: free → Starter ($7)** — user paid. No more spin-down → webhooks reliable. render.yaml updated for parity (`d192294`).
- Tests: 511 → 620 passing.

### Still open / next
- ⚠️ **Postgres STILL FREE — deletes itself 2026-06-20 (17 days)**. The $7 was web service ONLY. DB is separate paid item. HARD DEADLINE — data loss if not upgraded. User aware, handling separately (or wants me to pull upgrade options).
- Group trade-off shipped: name-about-her ("jessica好靚") also triggers reply. Acceptable for consult group; switch to always-reply-whitelisted-groups if noisy.
- Render auto-deploy webhook still broken — manual deploy via API (render CLI key in ~/.render/cli.yaml, SVC=srv-d879lsmq1p3s73av6f80, owner tea-cumb3f5umphs73ehbo30).
- TTS_ENABLED=true on prod, MINIMAX_* shared with dr-baba quota — watch usage.
- Advisory self-critique guard (medical prescriptive red-line) — still not built, flagged earlier.

### Method notes (what worked)
- **persona_dry_run.py is gold** — found 4 convo issues zero unit tests caught; ~$0.25/run. User trusts real replies > tests.
- **/admin/webhooks/recent raw capture** decisively solved the group mystery — read ground truth, don't theorize.
- **Live trace fetch** (`/trace/<id>` on prod) showed exact planner routing for the 鬼打墙 bug. Traces list at `/trace`.
- Render deploy poll pattern: trigger via API, until-loop on status==live, then /health.

### Tonal
- User is decisive + action-oriented ("push", "do all in parallel", "b"). Ships fast, tests on real WhatsApp, sends screenshots of failures with sharp diagnosis ("鬼打墙", "unknown contact").

## Session — 2026-06-03
What happened: Built VoiceBoard from scratch — a new standalone app, nothing to do with TCM-Jessica. Real-time voice → modular thinking board (diagram, bullets, actions, decisions, table, summary blocks).
Decisions:
- MediaRecorder stop/restart every 4s (not chunk stitching) — fixes Whisper HTTP 500 from malformed WebM
- Board generation via Claude Code CLI subprocess (claude --print), not Anthropic SDK — uses Max plan, zero API cost
- Incremental updates: send { newSpeech, currentBoard } not full transcript — GPT/Claude extends existing board
- Queue pattern for concurrent chunk handling (one gen at a time, latest wins)
- Transcription: whisper-1 only (gpt-4o-transcribe doesn't exist on standard plans)
- Text paste input added alongside voice — same handleChunk pipeline
Still open:
- Transcription 500 error may still appear (audio format edge cases on some browsers)
- Phase 2: Excalidraw whiteboard mode, session history, export PNG/PDF
- Claude CLI path hardcoded to /Users/shivonne/.local/bin/claude
Project location: /Users/shivonne/Claude Code/voiceboard

## Session — 2026-06-05
What happened: Built Instagram + Facebook inbound channel for Jessica — DM auto-reply + keyword comment→DM. Mirrors the WhatsApp channel architecture, dispatches into the SAME JessicaPipeline.run_turn with namespaced CRM keys.

Decisions:
- **New package `src/channels/`** (parallel to `src/whatsapp/`):
  - `meta_events.py` — frozen dataclasses (IncomingDM, IncomingComment) + `parse_meta_webhook()` total parser. Handles BOTH `object=="instagram"` and `object=="page"` (FB) — one parser, FB router can be added later for free.
  - `meta_client.py` — Graph API outbound: `send_dm`, `send_private_reply` (comment→DM), `reply_to_comment` (public). Token never logged. v25.0 default.
  - `instagram.py` — APIRouter: GET `/webhook/instagram` (hub.challenge handshake), POST (X-Hub-Signature-256 verify → parse → dedup → background dispatch). 
- **CRM key namespacing**: `ig_<igsid>` / `fb_<psid>` — same per-person pattern as group chat `g_<lid>`. Pipeline doesn't care `phone` is actually an IG id. CRM records never collide across surfaces.
- **Comment behaviour**: keyword-gated (IG_COMMENT_KEYWORDS env). On hit → run pipeline on comment text → send ONE private reply (Meta's 1-DM-per-comment rule). Optional public ack. No keywords configured ⇒ comments ignored, DMs still work.
- **Security**: signature fails CLOSED in production if META_APP_SECRET unset; dev skips for curl tests. Constant-time compare. Feature-flagged off by default (IG_ENABLED=false).
- **No merge buffer / group gate / blocklist for IG v1** — lighter than WA router on purpose. Add if volume warrants.
- Wired into web.py: `include_router(instagram_router)` + `set_ig_pipeline(pipeline)` at startup (same pipeline instance as WA).
- render.yaml: added IG_ENABLED, META_APP_SECRET, META_VERIFY_TOKEN, IG_PAGE_ACCESS_TOKEN, IG_USER_ID, IG_COMMENT_KEYWORDS, IG_COMMENT_PUBLIC_ACK (all sync:false / off).

Tests: `tests/test_channels_instagram.py` — 19 tests (parser, FB object, garbage input, signature verify prod/dev, dedup, DM dispatch sends each bubble, comment keyword hit→private reply, no-keyword skip, disabled-when-empty). Full suite 620→639 passing, zero regressions.

Fixed: FastAPI choked on `PlainTextResponse | JSONResponse` union return annotation → added `response_model=None` to the GET route.

Still open (Meta-side setup, NOT code):
- Need Meta Developer App + IG Business account linked to a FB Page.
- App Review for `instagram_manage_messages` + `instagram_manage_comments` (Advanced Access) — ~2 weeks, needs screencasts per permission.
- Register webhook URL `https://tcm-jessica.onrender.com/webhook/instagram` + subscribe to `messages` + `comments` fields.
- Set the 5 env secrets, flip IG_ENABLED=true.
- TikTok: NO comment-to-DM API in HK — bio link only, not buildable.
- Future: media/image bubbles on IG (v1 is text-only); FB Messenger router (parser already supports it).

### Session 2026-06-05 (cont.) — FB router + media + canned comments
- Refactored channels into shared core: `meta_webhook.py` holds ALL logic (verify_signature, dedup, process_post, handle_dm, handle_comment). `instagram.py` + `facebook.py` are now THIN routers (path + enable-flag + pipeline ref only). DRY.
- `meta_client` is now platform-aware: `send_dm/send_dm_image/send_private_reply/reply_to_comment(..., platform="instagram"|"facebook")`. Creds resolved per-platform: IG=(IG_PAGE_ACCESS_TOKEN, IG_USER_ID), FB=(FB_PAGE_ACCESS_TOKEN, FB_PAGE_ID).
- **DM now interleaves text + images** (mirrors WA `_send_bubbles_impl`): media_to_send grouped by after_bubble_idx, image DM sent right after its bubble via Send API attachment payload.
- **BIG: comment handling is now CANNED-FIRST** (`comment_rules.py` + `data/channels/comment_responses.json`). Keyword → fixed DM (text+image+public_ack), NO LLM. Only `use_agent:true` rules run the pipeline. No rule match → silent (don't DM strangers). This is the right model for CTA comments per Shivonne's point: "comment X → send specific thing, don't call agent."
- Routes live: /webhook/instagram + /webhook/facebook (both GET verify + POST). FB parser already worked (object=="page").
- render.yaml: ONE META_APP_SECRET + META_VERIFY_TOKEN (shared app); separate IG_*/FB_* creds + enable flags; COMMENT_RESPONSES_PATH.
- Tests: rewrote test_channels_instagram.py → 23 tests (parser, FB object, signature prod/dev, dedup, handshake, comment_rules match/missing, DM text+image interleave, canned comment no-agent, use_agent path, no-rule skip, disabled short-circuit). Full suite 639→643 passing.
- Sample rules shipped for "gut" + "濕熱" with wa.me CTA.

### Session 2026-06-05 (cont.2) — IG channel SHIPPED TO PROD ✅
- Meta App "TCM-ChloeChan" (business portfolio: Chloe Chan Chi Ching). IG account: chloechan.cccc.
- **Flow used: Instagram API with Instagram Login** (token prefix IGAA) → API host is graph.instagram.com (NOT graph.facebook.com). META_GRAPH_BASE=https://graph.instagram.com, META_GRAPH_VERSION=v23.0.
- Token: dashboard "Generate token" gives an ALREADY-long-lived (60d) token. ig_exchange_token FAILS on it (error 452) — don't exchange; just use it, or ig_refresh_token to extend. Auto-refresh loop NOT built yet (TODO before ~Aug 2026 / 60 days).
- IG_USER_ID = 17841424706900394 (the `user_id` field from /me, NOT the `id` field 27405003679135878).
- Permissions gotcha solved: "Insufficient Developer Role" = need App role (Admin) AND Business→Apps→Add People (Develop app) AND IG account added as Instagram Tester + accept invite. Business portfolio full control ≠ app role.
- Render env set via API (per-key PUT, no clobber): META_APP_SECRET, META_VERIFY_TOKEN=jessica_tcm_2026_xY9k, IG_PAGE_ACCESS_TOKEN, IG_USER_ID, META_GRAPH_BASE, META_GRAPH_VERSION, IG_ENABLED=true. Service srv-d879lsmq1p3s73av6f80.
- Committed + pushed to main (416fc57) — Render builds from git, so code MUST be pushed (env-only redeploy ran old code → 404 on /webhook/instagram until pushed).
- Webhook verified in Meta dashboard: comments + messages subscribed (v25.0 fields). Live GET handshake PASS, POST self-test (signed) → {"status":"queued","count":1}.
- ⚠️ SECURITY DEBT: App Secret [REDACTED — leaked in chat + git history; rotate]. Lives only in Render env META_APP_SECRET + local .env (gitignored).
- Still TODO: (1) IG token auto-refresh loop (mirror wa_client.start_token_refresh_loop), (2) App Review + Publish for public access (currently only admin/tester accounts trigger webhooks), (3) Facebook line not connected yet (code ready, needs FB_PAGE_ACCESS_TOKEN+FB_PAGE_ID+FB_ENABLED), (4) real DM test from a second IG account pending.

### Session 2026-06-05 (cont.3) — IG channel: built+deployed, BLOCKED on app publish
STATUS: All code shipped & live. Webhook NOT firing because Meta App is UNPUBLISHED.

What's DONE & verified:
- Meta App TCM-ChloeChan (id 1550317559787276), IG account chloechan.cccc, IG_USER_ID=17841424706900394
- Account switched Creator→BUSINESS (was MEDIA_CREATOR — Creator doesn't support messaging API). Now account_type=BUSINESS ✅
- Token (Instagram Login, graph.instagram.com, v23.0) regenerated AFTER business switch, long-lived 60d, in Render IG_PAGE_ACCESS_TOKEN + local .env. Has messaging scope (/me/conversations returns 200).
- subscribed_apps = [messages, comments] on the account ✅
- shivonne_ksw added as Instagram Tester + accepted; mutual follow done; test msg moved to General folder (out of Requests)
- Webhook verified in Meta (GET handshake PASS live), /webhook/instagram + /webhook/facebook live
- POST self-test (signed) → {"status":"queued","count":1} — our pipe is 100% good
- Privacy + data-deletion pages SHIPPED: https://tcm-jessica.onrender.com/privacy + /data-deletion (commit 22a00b4). Meta Settings→Basic "All required app settings complete".
- Render envs all set; IG_ENABLED=true; deploys live.

THE BLOCKER (confirmed by elimination):
- Despite EVERYTHING correct, /me/conversations=0 AND webhook never fires, even on a clean stable-server test.
- Meta banner: "To receive webhooks, your app must be in published state." → LITERAL for the new IG API. Dev/unpublished mode does NOT deliver messaging webhooks even to testers.
- → RESUME ACTION: PUBLISH the app to Live. User couldn't tap the mobile Publish button (Safari). Do it on MacBook desktop dashboard: https://developers.facebook.com/apps/1550317559787276/  → Publish page → blue "Publish" button (or App Mode Dev→Live toggle). Settings already complete, privacy URL accepted.
- Do NOT add permissions one-by-one in the use-case "Customize" screen — "Ready for testing" = Standard Access = enough for testing. Advanced Access (App Review) only needed for PUBLIC users later.

AFTER PUBLISH: send DM from shivonne_ksw → watch logs (render API, ownerId tea-d467almuk2gs73cvmd60, svc srv-d879lsmq1p3s73av6f80). Should see POST /webhook/instagram + queued + [meta] sent ok. If still nothing, then App Review for instagram_business_manage_messages advanced access may be required.

SECURITY DEBT (unresolved): app secret [REDACTED — leaked in chat + git history]. Rotate → update META_APP_SECRET on Render + .env. Old value should be considered burned.

OTHER TODO: IG token auto-refresh loop (60d expiry ~Aug 2026); Facebook line (code ready, needs FB_PAGE_ACCESS_TOKEN+FB_PAGE_ID+FB_ENABLED).

### Session 2026-06-05 (cont.4) — IG LIVE + Chloe persona + gut 懶人包
- ⭐ IG WORKING: publishing the Meta App to Live was THE unlock. After Publish, /me/conversations went 0→1 (saw shivonne_ksw msgs). Meta crawled /privacy + /data-deletion (173.252.x). Re-subscribed messages+comments post-publish.
- Public access still needs App Review (Advanced Access) for instagram_business_manage_messages/_comments. Currently works for connected acct + Instagram Testers only.
- **Chloe persona (陳芷晴)** = SEPARATE agent route for IG/FB DMs (NOT Jessica):
  - data/personas/chloe.json (display_name, greeting_bubbles, system_prompt, model gpt-5.4-mini, max_bubbles 3, whatsapp_cta wa.me/85252417448)
  - src/channels/chloe_agent.py — ChloeAgent: 1 LLM call/turn, CRM-backed (ig_/fb_ keys), GREETING-FIRST on first-touch (no prior history), drives to WhatsApp, no diagnosis/hard-sell. Returns ChloeReply(bubbles, media).
  - meta_webhook.handle_dm: routes IG/FB DMs → Chloe (set_chloe_agent in web.py lifespan with client+crm). Comments stay canned. Pipeline fallback kept.
  - Real LLM dry-run = excellent voice (greeting→empathy→light advice→soft WA CTA; deflects deep体质 to WhatsApp).
- **Gut 懶人包 lead magnet**: comment OR DM "gut"/"GUT" (case-insensitive) → warm text + 6 page images + WA CTA. NO LLM (canned, use_agent:false).
  - PDF found at ~/Library/Mobile Documents/com~apple~CloudDocs/腸胃調理懶人包_IG_DM_陳芷晴.pdf → rendered 6 PNG pages (pdftoppm -r110, 1238px wide) → data/media/guides/gut-page-{1..6}.png + gut-guide.pdf, served at https://tcm-jessica.onrender.com/media/guides/.
  - IG can't attach PDFs (only image/audio/video) → that's why pages-as-images. PDF also hosted if we want a link later.
  - comment_rules.py extended: image_urls (list) + all_images property. _comment_via_canned sends all images; new _send_canned_to_user for DM short-circuit. DM keyword match short-circuits Chloe LLM.
- Tests: test_chloe_agent.py (11) — greeting-first, returning-no-greeting, LLM-failure→CTA, routing, DM keyword short-circuit. Full suite 654 passing. Commit 470fcbf, deployed live.
- Render deploy gotcha reconfirmed: env-only redeploy runs OLD git code; must push then deploy. Also first deploy after big change sometimes needs clearCache (privacy pages 404'd until cache-clear).

### Session 2026-06-05 (cont.5) — Chloe polish: greeting + merge buffer
- IG Chloe flow CONFIRMED working live (screenshot: hi→greeting, GUT→懶人包 images delivered). Persistence confirmed (reset deleted users:1/messages:6).
- Richer greeting: chloe.json greeting_bubbles rewritten (fuller intro — who she is + what she helps + invite). First-touch logic: pure-greeting ("hi"/"你好") → intro ONLY (no redundant LLM); substantive first msg → intro + answer. _is_pure_greeting regex in chloe_agent.py.
- **Merge buffer** (src/channels/merge_buffer.py): per-user debounce, window 5s / force 20s. meta_webhook.handle_dm → buffers → _dispatch_dm runs merged turn. Rapid fragments → 1 Chloe reply (1 LLM call). Env: CHLOE_MERGE_WINDOW_S / CHLOE_MERGE_MAX_S. reset_merge_buffer() test hook.
- Chloe model = gpt-5.4-mini (data/personas/chloe.json), 1 call/turn; greetings + gut keyword = 0 LLM calls.
- /admin/crm/reset endpoint (POST {"key":"ig_<id>"}) added for test resets. shivonne_ksw IG key = ig_2069881150591895. Guard via ADMIN_RESET_TOKEN (unset = open).
- Full suite 659 passing. Commits: 195722f (greeting), 99a27a2 (merge buffer). All deployed live.
- Note: env-only redeploy runs old git code — always push then deploy. clearCache sometimes needed for new routes.

### Session 2026-06-05 (cont.6) — Chloe softer WhatsApp CTA
- Feedback: Chloe pushed WhatsApp every turn (too salesy). Fixed: relationship-gated CTA.
- chloe.json: system_prompt rewritten — default = DO NOT push WhatsApp unsolicited; only share wa.me when (a) user explicitly asks to book/見/詳細諮詢, or (b) after cta_after_turns. Added cta_after_turns=15 + cta_nudge (appended to system prompt only when depth>=15).
- chloe_agent.py: _count_user_turns(history) → if turns>=cta_after_turns, append cta_nudge to system. _generate takes turns kwarg.
- Dry-run verified: early 湯水 ask = NO wa.me; early explicit '我想預約睇你' = wa.me given. 
- Tunable: cta_after_turns in data/personas/chloe.json (raise=softer). Commit 9b3c993, deployed live. Suite 660 passing.

### Session 2026-06-05 (cont.7) — Chloe greet-once fix
- Bug report: Chloe greeted every round. Root cause was twofold: (1) is_first_touch keyed off len(history)==0 which is fragile, (2) MY repeated /admin/crm/reset between deploys wiped history → each next msg looked first-touch.
- Fix (commit 49f7287): is_first_touch now = (get_user(crm_key) is None) — i.e. user-ROW existence, not message history. get_or_create_user always creates the row turn 1, so existing row = met before. Robust to any persistence hiccup.
- Verified persistence WORKS on prod via synthetic signed webhook: reset→send "你好"→wait 9s→reset showed users:1 messages:2. So history saves fine.
- Updated _FakeCRM in tests with get_user (None when history empty = new user). Suite green (12 chloe tests).
- LESSON: stop resetting user's key between their tests — it caused the greet-every-round perception. Reset once, let them have continuous convo.
- shivonne_ksw (ig_2069881150591895) given final clean reset for continuous multi-turn test.

---

## 📇 META APP REFERENCE CARD (Chloe Instagram) — canonical, saved 2026-06-10
> One place to never lose this again. NO secrets stored here (see env note).

**App identity**
- Meta App name: `TCM-ChloeChan` · Instagram app name (use-case): `TCM-ChloeChan-IG`
- ⭐ CORRECTION (2026-06-10): **Meta App ID (parent) = `1546738537122434`** (from FB page-token debug_token, application=TCM-ChloeChan). `1550317559787276` is the *Instagram* app ID (sub-identifier), NOT the parent app. App secret + dashboard belong to the parent.
- Dashboard: https://developers.facebook.com/apps/1546738537122434/
- Business portfolio: Chloe Chan Chi Ching

**Messenger / Facebook Page (added 2026-06-10)**
- FB Page ID (FB_PAGE_ID) = `1200796509776468`
- FB_PAGE_ACCESS_TOKEN: type=PAGE, scope=`pages_messaging`, **expires_at=0 (never expires)** 🎉, is_valid=true. Stored in Render env only (NOT git). data_access_expires_at ~90d (re-auth if it lapses, but token itself permanent).
- Webhook: `/webhook/facebook` callback + verify token `jessica_tcm_2026_xY9k` (shared w/ IG). Handshake tested PASS (echo challenge, wrong token=403).
- Render envs set via API (HTTP 200): FB_PAGE_ACCESS_TOKEN, FB_PAGE_ID=1200796509776468, FB_ENABLED=true. Service srv-d879lsmq1p3s73av6f80.
- ⚠️ CODE FIX REQUIRED & DONE (commit ec67a50): meta_client._base() was GLOBAL (read META_GRAPH_BASE=graph.instagram.com) → would have routed FB sends to graph.instagram.com (wrong host, silent fail). Now per-platform: IG→graph.instagram.com, FB→graph.facebook.com. New override vars IG_GRAPH_BASE/FB_GRAPH_BASE; META_GRAPH_BASE kept as IG legacy alias. Regression test: tests/test_meta_client_base.py (4 tests).
- Public users need App Review for `pages_messaging` (page admin/testers work now). FB code shares Chloe agent route (object=="page").

**🔑 CRITICAL: this app has TWO secrets (Instagram-Login model)**
- Instagram app (sub-id `1550317559787276`) secret = Render `META_APP_SECRET` (32c, signs IG webhooks ✅).
- Meta App (parent `1546738537122434`) secret = [REDACTED] → set as Render `FB_APP_SECRET` (signs FB/Messenger webhooks). ⚠️ leaked in chat → rotate later. Lives only in Render env.
- Proof: IG POSTs verify 200 w/ META_APP_SECRET; app-token `1546…|META_APP_SECRET` = "Invalid signature" but `1546…|<FB_APP_SECRET>` = valid. → genuinely 2 secrets.
- CODE FIX (commit c89278a): verify_signature(raw,header,*,secret=None); process_post(...,app_secret=None); facebook route passes meta_webhook._fb_app_secret() (=FB_APP_SECRET, fallback META_APP_SECRET). IG route unchanged. Tests: tests/test_meta_webhook_signature.py.

**🐞 Messenger delivery root cause (FIXED via Graph API)**
- App-level webhook for `page` object had **EMPTY fields** (callback active, url correct, but no `messages` subscribed) → Meta had nothing to deliver → zero POSTs.
- Fixed by app-token POST /{app_id}/subscriptions object=page fields=`messages,messaging_postbacks` → {"success":true}. (Other fields messaging_optins/referral/reactions need Advanced Access — skipped.)
- Page-level subscribed_apps NOT readable/writable w/ our page token (only has pages_messaging, lacks pages_manage_metadata). Relying on dashboard "Connect page" to have set it. If DMs still don't arrive after the 2 fixes, suspect page subscribed_apps → toggle page subscription in Messenger dashboard step 2.
- Diagnostics how-to: app token = `1546738537122434|<FB_APP_SECRET>`; GET /{app_id}/subscriptions shows object/fields/active. Render logs API: GET https://api.render.com/v1/logs?ownerId=tea-d467almuk2gs73cvmd60&resource=srv-d879lsmq1p3s73av6f80&limit=N&text=POST (filter to dodge /health flood every 5s).
- ⚠️ ROTATE both secrets after testing (IG + Meta app secrets both leaked in chat history).

**✅ MESSENGER LIVE & WORKING (2026-06-10)**
- After both fixes + both subscription layers, real FB DM → `POST /webhook/facebook 200` (from FB IP 66.220.149.4) → Chloe replied in Messenger (screenshot confirmed: greeting intro + reply bubbles). Chloe persona shared with IG (object=="page" routes to ChloeAgent).
- The TWO subscription layers BOTH required (this was the real blocker, not code):
  1. App-level: POST /{app_id}/subscriptions object=page fields=messages,messaging_postbacks (was empty).
  2. Page-level: POST /{page_id}/subscribed_apps subscribed_fields=messages,messaging_postbacks (our page token CAN do this w/ just pages_messaging — returned success). Dashboard "Connect page" did NOT set this.

**Merge buffer — IG & Messenger ALREADY unified**
- `_merge_buffer` is a process-level SINGLETON (meta_webhook._get_merge_buffer). Both IG + FB DMs go through the same handle_dm → same buffer → same window. Keyed by crm_key (ig_/fb_ + sender_id). They are structurally aligned — there are NOT two buffers.
- "Replies to 2 separate messages" causes: (a) default window 5s too short → msgs >5s apart = 2 turns; (b) Chloe sends 2-3 bubbles/turn by design (max_bubbles) — looks like multi-reply but is ONE turn.
- TUNED 2026-06-10: Render CHLOE_MERGE_WINDOW_S=8, CHLOE_MERGE_MAX_S=30 (was unset→5/20). ⚠️ Buffer caches window at first-build → needs redeploy to take effect (done). Applies to BOTH channels (shared buffer).
- Lever for future: raise CHLOE_MERGE_WINDOW_S = merges slower typers but delays first reply.

**Connected account**
- IG handle: `chloechan.cccc` · account_type: **BUSINESS** (must NOT be Creator — Creator can't message)
- IG_USER_ID: `17841424706900394` (the `user_id` from /me, NOT id `27405003679135878`)

**Use case / API flow**
- **Instagram API with Instagram Login** (NOT FB Login). Token prefix `IGAA`.
- API host: `graph.instagram.com` (NOT graph.facebook.com)
- META_GRAPH_BASE=`https://graph.instagram.com` · META_GRAPH_VERSION=`v23.0`
- Permissions on use case: `instagram_business_basic`, `instagram_manage_comments`, `instagram_business_manage_messages`
- App is **PUBLISHED / Live** (that was the unlock — webhooks don't fire when unpublished). Standard Access works for connected acct + Instagram Testers. Public users need App Review (Advanced Access) for `_manage_messages`/`_manage_comments`.

**Webhook**
- Endpoints (live on Render): `/webhook/instagram` + `/webhook/facebook` at https://tcm-jessica.onrender.com
- Verify token: `META_VERIFY_TOKEN=jessica_tcm_2026_xY9k`
- Subscribed fields: `messages`, `comments`
- Privacy / data-deletion pages: /privacy + /data-deletion (Meta crawled & accepted)

**Render deploy**
- Service: `srv-d879lsmq1p3s73av6f80` · ownerId `tea-d467almuk2gs73cvmd60`
- Envs: META_APP_SECRET, META_VERIFY_TOKEN, IG_PAGE_ACCESS_TOKEN, IG_USER_ID, META_GRAPH_BASE, META_GRAPH_VERSION, IG_ENABLED=true
- ⚠️ Gotcha: env-only redeploy runs OLD git code — must `git push` then deploy. clearCache sometimes needed for new routes.

**Token**
- Dashboard "Generate token" = already-long-lived (60d). Do NOT ig_exchange_token (error 452). Use ig_refresh_token to extend.
- Stored in Render `IG_PAGE_ACCESS_TOKEN` + local .env. Expiry ~Aug 2026. Auto-refresh loop NOT built yet (TODO).

**Secrets (NOT in git)**
- App Secret + access token live ONLY in Render env + local `.env` (gitignored). App Secret was leaked in earlier chat/history → **ROTATE recommended** (Meta → App Settings → Basic → App Secret → Reset, then update META_APP_SECRET on Render + .env).

**Open TODOs**
- Rotate app secret (security debt)
- IG token auto-refresh loop before ~Aug 2026
- Facebook line: code ready, needs FB_PAGE_ACCESS_TOKEN + FB_PAGE_ID + FB_ENABLED
- App Review (Advanced Access) for full public messaging/comments

---

## Session — 2026-06-10 / 2026-06-15

### What happened
Two quick fixes: (1) weather broadcast throttle tightened, (2) Render deploy triggered manually.

### Decisions
- `BROADCAST_MIN_GAP_H` bumped 36 → 72 (3 days). Root cause: HK summer `humidity_heat` fires almost every day (≥29°C + ≥85% humidity), and ISO-week reset on Monday meant users could get 4 weather msgs in 5 days despite the 2/week cap. 72h gap + 2/week cap is now the correct dual guard.
- Weekly cap of 2 kept as-is (was already correct).
- 3 tests updated to reflect new 72h gap logic (49h case → now ineligible, 73h case → eligible).
- Render API key `rnd_4KadINh8FUoRVOJf0WLd33GujXI8` was shared in chat — **rotate this key**.

### Still open
- Rotate Render API key (shared in chat)
- Rotate Meta App Secret (security debt, noted prior session)
- IG token auto-refresh loop (~Aug 2026 expiry)
- Facebook line activation (code ready, needs env vars)

## Session — 2026-06-19
What happened: Implemented TCM 望診 vision feature. Browser captures a camera frame (JPEG 320×240) on each turn and sends it as a JSON WS message before the audio. Server runs GPT-4o Vision concurrently with STT so there's zero added latency. Chloe gets vision_notes injected into her system prompt. Also committed the full backlog: post-call summary, welcome TTS warmup, VAD fixes, pitch+1, subtitle chunking, barge-in, post-call routing.
Decisions:
- Vision frame sent as JSON text message before binary audio on each turn (not once at start)
- GPT-4o Vision with detail=low for speed/cost
- 3s timeout on vision task — graceful degradation if slow
- ChloeAgent._generate() vision_notes injects into system prompt (not as a message turn)
- canvas capture ignores CSS scaleX(-1) mirror — correct natural orientation for TCM
Still open:
- WhatsApp post-call summary (phone-number crm_keys, different send path)
- Silero VAD WASM upgrade (neural network, more precise end-of-speech)
- PTT mode fallback button

## Session — 2026-06-26

### What happened
Full day wiring Jackie Chan's IG agent flow into TCM-Jessica. Merged the Jackie branch to main, deployed to Render, set up per-account routing, keyword protocols, and fixed the Postgres DB expiry crash.

### Decisions
- **Jackie agent** on `jackiechan.tcm` (IG id `17841417304649448`) — English, gpt-4o-mini, no WA push
- **Catch-all comment handler**: any comment on Jackie → public ack "I've sent you the details — check your DM! 🌿" + Jackie agent DM
- **Keyword rules wired**: `detox`/`cleanse` (4 images live), `knee`/`knee pain` (images pending), `tonsil`/`tonsil stone` (images pending)
- **Both agents scope-limited to TCM only** — off-topic gets a warm redirect, no credits wasted
- **Chloe model fixed**: was `gpt-5.4-mini` (bad model name) → `gpt-4o-mini`
- **comment_ack** field added to persona JSON — controls what Jackie posts publicly on the thread
- **New Postgres DB**: `tcm-jessica-db-2` (basic_256mb, Singapore) — `dpg-d8v33p67r5hc73e5eri0-a`. Old free DB expired 2026-06-20. New DB internal URL not resolving — left on external URL, deploy still failing at session end.

### Still open
- **Postgres connection still broken** — external URL also failed DNS. User transferred to Codex to continue. Need correct External Database URL from Render dashboard for `dpg-d8v33p67r5hc73e5eri0-a`
- **Knee + tonsil stone images** — user needs to provide; keyword rules are ready (empty image_urls)
- **Rotate Jackie IG token** — the one pasted in chat earlier (`IGAAWCAW9wrw...`) should be rotated
- **Rotate Render API key** `rnd_4KadINh8FUoRVOJf0WLd33GujXI8` — was logged in chat/memory
- **IG token auto-refresh** — Jackie token expires ~60 days (around late August 2026)
- **App Review** for Advanced Access (public users beyond testers)

### Key references
- Render service: `srv-d879lsmq1p3s73av6f80` · owner: `tea-d467almuk2gs73cvmd60`
- New DB ID: `dpg-d8v33p67r5hc73e5eri0-a` · DB name: `jessica_db_k7gp` · user: `jessica`
- Jackie IG token in Render env as `IG_PAGE_ACCESS_TOKEN_JACKIE`

## Session — 2026-06-27

### What happened
Full Jackie IG agent flow audit + two-layer language routing hardened. Continued from previous session where Jackie's IG account was wired up.

### Decisions
- **Array format for comment_responses.json** — switched from dict (can't have duplicate keys) to array so "gut" can exist for Jackie (en) AND Chloe (yue) as separate rules
- **Two-layer match**: keyword substring → account filter → language gate (hard block in code)
- **`_ACCOUNT_LANGUAGE` map** in `comment_rules.py` — Jackie=en, Chloe=yue. Code-level guard logs ERROR and skips rule on language mismatch
- **Chloe gut rule added** — gut-page-1..6.png (Cantonese, 6 pages) with Cantonese DM text
- **濕熱 DM text fixed** — was saying "I'm Jackie", corrected to Chloe Cantonese voice
- Root cause of the incident: shared "gut" keyword with no account/language separation → Jackie sent Cantonese images to English users

### Self-reply guard confirmed
- `_is_own_comment()` runs at two layers (process_post + handle_comment)
- `IG_USER_ID_JACKIE` ✅ confirmed set on Render
- `recipient_id` also in `own_ids` — bulletproof even without the env var

### Still open
- `IG_PAGE_ACCESS_TOKEN` and `IG_PAGE_ACCESS_TOKEN_JACKIE` both MISSING from Render — no outbound DMs/replies work until these are added
- Jackie IG token shared in previous chat session — should be rotated
- Render API key `rnd_4KadINh8FUoRVOJf0WLd33GujXI8` — in memory file, rotate when possible
- IG tokens expire ~60 days (Aug 2026) — no auto-refresh loop built

## Session — 2026-07-01/02 (comment auto-reply outage + KB-grounded DM pipeline)

### What happened
Diagnosed + fixed a real production outage (comments/DMs going unreplied), then built + shipped (behind flags, fallback-protected) the first phase of a bigger migration: giving Jackie/Chloe's IG DMs the same KB-grounded multi-agent brain WhatsApp/Jessica already has, instead of the ungrounded single-LLM-call `ChloeAgent`. Full narrative in CLAUDE.md §3.10 + §10 (What Not To Do) — this is the session log; those are the durable lessons.

### Decisions / what shipped (all merged to main, all verified independently — not just agent-reported)
- **eye/migraine/teeth keyword rules** added for Jackie (images recovered from ai-tcm-ip's already-generated set, not regenerated). Backfilled all stuck historical comments via `scripts/backfill_comments.py` + verified via Graph API (`/replies`, `/conversations`).
- **`POST /admin/notion-sync`** — Notion Automation webhook, drafts keyword rules the moment Production Tracker Stage → ✅ Published. `POST /admin/backfill-comments` — live-CRM version of the backfill script for anything conversational.
- **`PersonaProfile` abstraction** (`src/personas/profile.py`) — Jessica/Jackie/Chloe profiles threaded optionally through `pipeline.run_turn`/`Planner.decide`/`Writer.compose`. Default path proven byte-identical to pre-migration behavior via golden-fixture test.
- **Fixed 2 real bugs found via manual dry-run** (`scripts/persona_dry_run_social.py`), not just unit tests: Planner truncated history to 80 chars (cut off numbered options before it could see them) + FAQAgent searched KB with raw message instead of Planner's `rephrased_query`. Also added a hard code-level CJK-character guard so English personas can never leak Chinese text (retry once, then safe fallback).
- **Jackie wired live behind `SOCIAL_PIPELINE_ACCOUNTS`** (empty by default = zero risk) — `_dispatch_dm_profile_pipeline()` in `meta_webhook.py`, any exception falls back to `ChloeAgent` automatically, tested with a forced-failure case.
- **Root-caused the actual outage**: `IG_ENABLED`/`FB_ENABLED` had a literal `value: "false"` in `render.yaml` (not `sync: false`) since they were first added — every deploy silently reset them, killing comment/DM processing with zero errors. Fixed to `sync: false`. Confirmed the live gate state directly by POSTing a signed synthetic webhook and reading the response `status` field (`"disabled"`) — don't infer from git history, test the real thing.
- **`notion_sync.py` mechanical templating bug**: doesn't check if the Notion source text's language matches the target persona — drafted a Chloe/Cantonese rule that was English-wrapped-in-Cantonese-greeting. Fixed by hand for `teeth`; worth a real fix in the sync script itself later (flagged, not yet built).

### Still open
- **`IG_ENABLED=true` needs to actually be set in the Render dashboard** — the `sync:false` fix prevents future resets but doesn't retroactively fix the current live value. User was walking through this when session ended.
- Chloe's own IG account — no live posts found when checked (`/media` returned empty) — the Chloe/yue teeth rule may be sitting unused for now.
- Shadow-mode / full Chloe cutover for the PersonaProfile pipeline not started — only Jackie is wired, and only behind a flag that isn't flipped on yet either.
- `notion_sync.py` source-language verification — real gap, not yet fixed at the tool level.
- `_comment_via_agent()` (the pre-existing, separately-dormant comment path that calls `pipeline.run_turn` directly with no profile) still mis-voices IG comments if any rule ever sets `use_agent: true` — none do today, confirmed, but it's a live landmine if someone adds one without knowing this.

## Session — 2026-07-02/03 (incident fix + strategy pivot + rename)
What happened: Fixed the DM keyword-hijack incident (Irene/yellowpalm999 got the canned eye guide 5x incl. as "reply" to a real question — manually answered her as Jackie via Graph API, then shipped _is_bare_keyword_trigger keyword-remainder heuristic + guides_sent dedup, 29 regression tests, deployed). Then a full strategy pivot and project rename.
Decisions:
- STRATEGY v2: no WhatsApp funnel, no Ming Pao, forget Jessica/心宜中醫 (partnership ended). Product = multi-IP multi-platform social reply: L0 canned comments + L1 persona DMs. Growth axis = platforms (IG live → Messenger next → TikTok). Plan: /Users/shivonne/Claude Code/TCM-INTEGRATION-PLAN.html (v2).
- RENAMED: TCM-Jessica → social-ip-engine (GitHub w/ redirect, local folder, Render display name). URL stays tcm-jessica.onrender.com (fixed at creation; custom domain later).
- Service is NOT blueprint-attached (verified via API) — render.yaml is docs only, real env flags live in dashboard. The "blueprint resets IG_ENABLED" mechanism no longer exists, keep the probe habit anyway.
- WhatsApp poller + broadcaster OFF and pinned (dashboard WA_POLL_ENABLED=false, BROADCAST_ENABLED=false + hardcoded false in render.yaml).
- Personas: both now answer clinic/booking asks with "not at the moment — text support here" (jackie.json + chloe.json, deployed).
- RENDER_API_KEY saved in social-ip-engine/.env (user explicitly approved, don't ask again). Also in ~/.render/cli.yaml.
- Probe recipe: signed synthetic webhook POST to /webhook/instagram, empty changes → expect {"status":"ignored"} (="enabled+verified"); "disabled" = the bad state.
Still open:
- 04:44 (07-02) mass re-send trigger never identified — investigate before ANY backfill run.
- guides_sent TOCTOU race (review MEDIUM) — fix in Phase 1.
- 2 skip-marked cta_nudge orphan tests in test_chloe_agent.py.
- Phase 1 (IP Registry) not started; D5 (is Chloe actively fed content?) unanswered.
- My manual DM to Irene is NOT in prod CRM (sent via Graph API directly).

## Session — 2026-07-03 (Phase 2 merge executed)
What happened: ai-tcm-ip merged INTO social-ip-engine as studio/ (git subtree, history preserved). Dead server code → docs/legacy/ai-tcm-ip-server/; infographics → studio/assets/infographics/; .env copied to studio/.env (gitignored). GitHub repo shivonnekh/ai-tcm-ip ARCHIVED (read-only); local folder renamed _archived-ai-tcm-ip (contains gitignored campaigns/_generated media — don't delete without checking). launchd auto-fanout job NOT installed (plist was repo-only). All Notion content work now happens in social-ip-engine/studio/ — scripts find studio/.env automatically. 758 tests green post-merge. Integration plan copied to docs/INTEGRATION-PLAN.html (canonical copy).
Still open: Phase 1 (IP Registry — replace 4 hardcoded dicts), Phase 3 (notion-sync auto-copies infographics), 04:44 mass re-send trigger unidentified, guides_sent TOCTOU race, D5 (Chloe content feed?).

## Session — 2026-07-03 PM (Phases 1+3+4 shipped via parallel agents)
What happened: 3 agents in parallel worktrees built Phase 1 (IP Registry), Phase 3 (notion-sync media automation), Phase 4 (FB/Messenger prep). Merged 1→3→4, deployed, probe green. 848 tests passing (was 758).
Decisions:
- IP config single source: data/ips/{jackie,chloe}/ip.json + persona.json, loaded by src/ips/registry.py (frozen dataclasses, import-time validation). The 4 hardcoded dicts are GONE. data/personas/ no longer exists.
- ChloeAgent renamed PersonaAgent (module still chloe_agent.py, ChloeAgent alias kept).
- Language gate semantics CHANGED: unregistered account + language-tagged rule = BLOCKED (fail closed). IG langs from registry; FB via FB_PAGE_ID+FB_PAGE_LANGUAGE env until channels.messenger lands in ip.json.
- notion-sync now auto-pulls 📊 DM Infographic from Production Tracker row → data/media/guides/ → image_urls (idempotent via notion_media_state.json, sig-rotation aware); language-mismatch = warning not block; infographic failure never blocks the rule.
- Phase 4 fixed 2 latent bugs: FB public comment reply used IG's /replies edge (would 400) → per-platform edge; language-gate fail-open hole → fail closed. scripts/fb_probe.py + docs/MESSENGER-ACTIVATION.md ready.
Still open:
- Messenger activation = HUMAN steps (Meta dashboard token + webhook subscribe + 4 Render env vars + FB_ENABLED=true last) — runbook: docs/MESSENGER-ACTIVATION.md
- meta_webhook._account_profile_loaders() still hardcodes jackie (dormant pipeline path) — fold into registry later
- scripts/backfill_comments.py hardcodes DEFAULT_ACCOUNT_ID
- 04:44 mass re-send trigger still unidentified; guides_sent TOCTOU race; D5 (Chloe content feed?)

## Session — 2026-07-03 (notion-sync resurrection + pre-flight + gimmick content)
What happened: Created the male-ED gimmick concept (No.52 "🍆 No Morning Wood") — talked her out of the literal condom-of-water image (IG/TikTok account-restriction risk to the comment→DM engine) into an eggplant-half-mast gag; DETOX-structure script (Hook→pain→solution→CTA) + DM protocol. Then a deep debugging chain that revealed her notion-sync auto-wiring had NEVER run in prod.

Decisions / shipped:
- **notion-sync was dead in prod — 3 env vars never set on Render**: NOTION_SYNC_SECRET (webhooks 401'd — saw them in Render logs from Notion IP 131.149.232.x), NOTION_KEY (502 "not set"), GITHUB_PUSH_TOKEN (rules written but not persisted → lost on deploy). All now set + verified by BEHAVIOR (200, tracker read 26 rows, git_push ok, commit landed).
- **Setting a Render env var does NOT auto-apply** — needs a manual deploy (POST /deploys) to inject into the running process. Auto-deploy webhook still broken.
- **ngrok bug**: PUBLIC_BASE_URL on Render was a stale ngrok dev tunnel; public_media_url() reads it BEFORE JESSICA_BASE_URL → every auto-wired DM infographic got a dead URL. Fixed → tcm-jessica.onrender.com.
- **Feature shipped (1ed1482)**: generate-infographic-from-Brief when a row has no DM-Infographic-toggle image (src/notion_infographic_gen.py); PNGs now pushed to git (were vanishing on deploy). Reviewer-hardened: threadpool (240s gen was going to block async endpoint), on-disk dedup (no re-spend on retry), per-run cap NOTION_SYNC_MAX_GENERATIONS=5. Opt-out via NOTION_SYNC_GENERATE_IMAGES=0.
- **Pre-flight (ce8248f)**: _WIREABLE_STAGES = {🟢 Ready to Publish, ✅ Published}. Arms keyword+DM+infographic at Ready (testable before post goes out); Published = safety net. Idempotent.
- muscle post (💪, live on IG, only comment was @davidafterwork) wired + URL fixed + richer 4-section infographic committed. David answered.

Still open:
- **USER ACTION**: re-point Notion Automation trigger from ✅ Published → 🟢 Ready to Publish (webhook URL + X-Sync-Secret unchanged).
- git_publish.py _REMOTE still says TCM-Jessica.git (works via GitHub redirect — low priority).
- PAT github_pat_11BRLC... is in .env + Render GITHUB_PUSH_TOKEN (Contents:write, social-ip-engine only, exposed in this chat — rotate if paranoid).
- Slug filename collision (pre-existing, download+gen branches) — different keywords sanitizing to same slug overwrite each other's PNG. Not fixed.
- No.52 vitality post not published; will auto-wire (with generated infographic now) when she flips it to Ready.

## Session addendum — 2026-07-03 (E2E verified + docs)
- VERIFIED live end-to-end: flipped rows to 🟢 Ready to Publish → Notion webhook hit /admin/notion-sync (200, from Notion IP 131.149.232.x, seen in Render logs) → auto-wired tongue/anxiety/stomach rules WITH infographics at correct onrender URLs → server git-pushed (ec0746b). stomach-page-1.png loads 200.
- Confirmed generate-from-Brief path works: ran notion_infographic_gen.find_infographic_brief + generate_png on vitality No.52's real Brief in isolation → clean on-brand image (walnuts/韭菜/生薑肉桂茶). vitality itself won't re-wire via webhook (already hand-wired → dedup skips).
- Confirmed 3-layer idempotency answers user's "bounce stage won't re-run" Q: row-id state (git-persisted) → keyword dedup → image reuse. Only re-wires if rule deleted/keyword changed.
- Gotcha for testing: Notion "Stage is set to X" trigger only fires on an actual CHANGE. Re-selecting the same value = no webhook. Test by flipping a NON-Ready row → Ready.
- Updated docs/content-flow-diagram.html (her HTML): trigger ✅ Published → 🟢 Ready to Publish pre-flight throughout + new §⑤ (rule fields table, generate-from-Brief, 3-layer idempotency, durability). English.

## Session — 2026-07-03 (evening)
What happened: Redesigned docs/content-flow-diagram.html from a long vertical mermaid page into a 7-slide horizontal presentation deck (scroll-snap L→R, custom flow nodes, animated connectors, webhook bolts). Renamed Jessica → Chloe everywhere in the doc. Committed d331c07 + pushed.
Decisions:
- Dropped mermaid entirely for the flow diagram — unstyleable, replaced with hand-built HTML/CSS nodes
- Deck pattern: wheel→horizontal scroll, dots + arrows + keyboard nav, vertical fallback <900px, prefers-reduced-motion respected
Still open: decisions.md has uncommitted auto-extracted changes (left unstaged intentionally — hook-owned file)

## Session — 2026-07-07 (afternoon) — pressure-points carousel: research → content → live publish
What happened: Wrote/patched the `tcm-trend-to-script` skill (Step 0 performance-retro checkpoint + marketing-psychology hook fallback) after a merge-conflict question about a nonexistent "IG reel editor" skill (turned out no such skill exists — video-editing/ai-tcm-voice were the closest, neither actually overlaps). Then researched English TCM infographic-format content (Pinterest gave real signal, IG account-level only, Reddit thin), picked "3 Pressure Points, 3 Everyday Problems" (Hegu/LI4, Zusanli/ST36, Shenmen/HT7) as a 5-slide carousel concept, generated it via gpt-image-2 matching Jackie's existing infographic brand exactly (pulled `sleep.png` as ground truth first), then built and ran the full live-publish pipeline end to end on the real @jackiechan.tcm account.

Decisions / shipped:
- **Discovered mid-task**: a full Reels auto-publish pipeline (`ig_publish.py`, `notion_publish*.py`, ledger + async runner + crash-resume) already existed uncommitted in the tree — almost certainly my own earlier work in this same session, dropped from visible context by compaction, not a conflicting concurrent session. Left it alone (didn't review/commit it myself); it got committed separately mid-session as `76683c6` by whatever process owns it.
- **Aspect ratio gotcha**: Instagram's Content Publishing API only accepts 4:5–1.91:1 photos. The established DM-infographic convention (1024x1536, ratio 0.667) would get REJECTED for a feed post — generated at 1024x1024 square instead. Documented in CLAUDE.md so this isn't rediscovered the hard way again.
- **Built `src/channels/ig_publish_carousel.py`** (item container + parent container, 12 passing tests) as a sibling to Reels-only `ig_publish.py` — reused its generic `poll_container_status`/`publish_container` rather than duplicating.
- **Images must be publicly fetchable before any Graph API call** — committed to `data/media/carousel/pressure-points/`, pushed, manually triggered a Render deploy (webhook still broken), verified all 5 URLs HTTP 200 before touching the API.
- **Added a `"pressure"` comment-keyword rule** to `comment_responses.json` so the caption's CTA isn't a dead-end — comment→DM now sends the real point-location text.
- **Safety-gate pattern used**: `publish_pressure_points_carousel.py` preps containers + polls to FINISHED + prints the exact caption/images, then requires an explicit `--confirm-publish` flag for the actual irreversible `media_publish` call. Shivonne reviewed the prepped output before I ran with the flag.
- **Result**: live at https://www.instagram.com/p/Dae2j14HzxY/ (media_id 17905615161444489), verified via `list_recent_media` matching back to the same id.
- Docs: added a "Publishing NEW content to the feed" subsection to CLAUDE.md §3.10 covering both Reels and carousel paths + all the gotchas above. Committed `eebb41b`.

Still open:
- Carousel publishing isn't wired into any Notion ledger yet — today's flow is ad-hoc/manual. If this becomes a repeated content type, it should get its own idempotency ledger like Reels has (`notion_publish_state.json` equivalent), otherwise a re-run risks a duplicate live post.
- Haven't reviewed/tested the pre-existing Reels auto-publish pipeline (`ig_publish.py`/`notion_publish*.py`) myself — it shipped mid-session from what's presumably earlier work in this same session, but I haven't personally verified it end-to-end the way I just did for carousels.
- `zsh` reserves `status` as a variable name — bit me once mid-session on a deploy-poll loop; use `deploy_status` or similar in any future polling script in this repo.

## Session — 2026-07-07 (IG Reels auto-publish: build + 2-pass review + hardening + ship)
What happened: Built full "auto-post Reel to Instagram on Stage=✅ Published" feature (user explicitly chose FULL auto-post over assisted one-tap after a diff explainer). Deliberately kept as a SEPARATE trigger from notion_sync's Ready-to-Publish wiring (that stage arms+tests the DM funnel; Published now actually posts) — this was a pushback-then-agreed design decision, not a request granted as-is.

Shipped (commit 76683c6, pushed + deployed, verified live: /health 200, /admin/notion-publish 401 without secret):
- src/notion_publish_caption.py — Hook property (preferred) + body-heading fallback, caption+CTA builder
- src/channels/ig_publish.py — Graph API 2-step Reels (create container → poll status_code → media_publish)
- src/notion_publish_media.py — cover = reuse Shot-1's "Image here" toggle image (real block structure confirmed from studio/scripts/notion_image.py), else generate from Hook
- src/notion_publish.py — the planner: 3-layer duplicate-post ledger (row-state / video-URL dedup / claim-before-call), Stage="✅ Published" ONLY (not Ready)
- src/notion_publish_runner.py — async create→poll→publish→checkbox, resume_in_flight for crash recovery
- src/web.py — POST /admin/notion-publish (same NOTION_SYNC_SECRET/X-Sync-Secret as notion-sync, by design)

Process: planner agent first (mandatory per repo policy — new capability, >2 files, external irreversible action), then built directly with TDD, then BOTH security-reviewer + python-reviewer dispatched in parallel (not skipped) since this touches auth/secrets/external API + a real live account. Both independently converged on the SAME critical bugs — strong signal, not noise. Fixed ALL critical+high findings, not just acknowledged:
- C1: published_video_urls set was static — two rows sharing a video in the SAME plan_publishes() batch could both get claimed. Fixed: seed includes IN_FLIGHT too, and the set is now mutated live as each row claims.
- C2 (2 independent framings from the 2 reviewers, same root bug): no lock → concurrent webhook calls OR startup-resume overlapping a webhook could run run_publish_job twice for the same row → two containers/two live posts. Fixed: threading.Lock around the whole plan_publishes() body (_PLAN_LOCK) + an in-process _RUNNING_ROW_IDS reentrancy guard in the runner (claimed atomically under _STATE_LOCK, released in finally).
- C3: corrupt/truncated ledger silently _load_json'd to {} → would look like "nothing ever published" → mass re-publish everything. Fixed: LedgerCorruptError (subclass of NotionSyncError) raised loudly instead, surfaces as 502.
- H1 (SSRF): cover download had no scheme check — a file:// or internal URL in the Notion block would be fetched AND re-served publicly at a predictable /media/covers/ path. Fixed: https-only allowlist in _is_safe_download_url.
- H2: git_publish.push_paths (blocking subprocess, up to ~2min) was called INSIDE async with _STATE_LOCK — froze the whole single-worker event loop for every ledger mutation. Fixed: lock released before push, push wrapped in asyncio.to_thread; same for _mark_posted's Notion PATCH.
- H (python-reviewer): cover filename/dedup-state keyed only on CTA-keyword slug — two rows sharing a keyword (e.g. two "Comment muscle" posts) could overwrite each other's cover on a LIVE post. Fixed: row_id folded into both filename and state key.
- H (python-reviewer): poll interval/max_wait had no validation — non-numeric env crashes a fire-and-forget task, zero/negative interval never advances elapsed → infinite poll loop. Fixed: try/except + floor/clamp, plus sleep clamped to remaining budget (was overshooting).
- M1: hmac.compare_digest for this endpoint's secret check (sibling /admin/notion-sync left as plain != — out of scope, lower blast radius).
- M2 (NOT auto-fixed, flagged to user): ledger stores raw signed video_url (needed for resume) and gets git-pushed — repo confirmed PUBLIC (checked via API). Recommended making repo private; tried via PAT but token is deliberately Contents:write-only, 403'd on repo-admin scope — asked user to flip manually (GitHub Settings → Danger Zone), did not push for broader token scope.
- Also caught + fixed a REAL bug in my OWN tests during pre-commit git-status review: test_checkbox_failure_does_not_undo_published_status never redirected _POSTED_PENDING_PATH, so it wrote ["row-1"] into the actual repo file data/channels/notion_publish_posted_pending.json on every local test run. Fixed via a blanket autouse fixture default; deleted the stray leaked file before committing.

125 new tests total (88 initial build + 37 regression tests for the review findings). Full suite 1041 passed/2 skipped throughout. Commit staged CAREFULLY — git status showed several unrelated modified/untracked files from other concurrent work (CLAUDE.md, studio/*, notion_sync.py's own "wired checkbox" feature + its test_notion_sync.py, memory files) — none of that was staged/committed, only the 13 files actually part of this feature.

Still open:
- USER ACTION: create 2nd Notion Automation — trigger Stage=✅ Published → webhook POST https://tcm-jessica.onrender.com/admin/notion-publish, header X-Sync-Secret (same value as the notion-sync automation).
- USER ACTION: make shivonnekh/social-ip-engine private (GitHub Settings) — closes M2.
- Not yet tested against a REAL live Notion row / real Meta API call (all verification so far is unit tests + auth smoke-test only — no real Reel has been posted end-to-end yet).
- H3 from security review (orphaned container on crash between create success and ledger write) — not separately fixed; judged adequately mitigated by the C2 reentrancy-guard fix, not revisited.
- Function length (plan_publishes ~140 lines) intentionally left as-is — mirrors existing accepted notion_sync.sync_once() precedent, non-blocking per reviewer's own note.

## Session — 2026-07-07 (evening) — "jianying cli" video ask → karaoke captions → cover/infographic pipeline → automated write-back
What happened: Started from "merge shots + add subtitle via jianying cli" for the Period Pain × Jackie row and ended up touching almost the whole content→publish chain in one sitting. Big lesson of the session: chased a dead-end tool path for a while before pivoting — worth remembering next time "jianying cli" comes up.

Decisions / what shipped:
- **capcut-cli's `--jianying` mode is a dead end for this Mac's actual JianYing app.** Installed JianYing is v10.9.0 (`com.lemon.lvpro`), which encrypts drafts since v6.0+ — confirmed by trying to read a REAL app-created draft with the CLI (`capcut decrypt` correctly detected AES-encrypted `template-2.tmp`, refuses to decrypt by design). capcut-cli's `--jianying` flag only namespaces enums (transitions/masks) — it still writes CapCut's plaintext schema, which the real app can't open. Built the draft anyway before discovering this (`~/Movies/JianyingPro/.../period-pain-jackie-en`) — abandoned it, do NOT reuse this approach. Real workaround per the tool's own docs: use CapCut International (unencrypted) instead, or pin JianYing to 5.9.x. Neither was worth the friction — pivoted to raw ffmpeg.
- **Installing `ffmpeg-full` (for libass/drawtext, needed for burned captions) silently broke the default `ffmpeg`/`ffprobe`** by upgrading shared deps (`libvpx`, `svt-av1`) out from under the pinned versions the default `ffmpeg` formula was linked against — this is a REAL trap on this machine, not hypothetical. Fixed by `brew upgrade ffmpeg` to match (not by fighting to pin old lib versions — that's whack-a-mole, proved it twice). Both binaries verified working after. If asked to add libass/drawtext support again on this Mac, expect this same collision and go straight to `brew upgrade ffmpeg` after `brew install ffmpeg-full`, don't try to preserve the old linked versions.
- **Word-level karaoke captions** (bold white text, black outline, current word yellow — matching a reference screenshot): used `openai-whisper --word_timestamps True` for TIMING ONLY, discarded its transcribed TEXT entirely and substituted the known-correct script word-for-word (sequential slice alignment by expected per-shot word count, with one manual splice for a spot where whisper merged "be following" into "follow"). This is the right pattern going forward — whisper mishears TCM proper nouns (Sanyinjiao→"saninjiao", Hegu→"hugu", Stagnation→"discation") reliably, but its timing/VAD is trustworthy even when the decoded word is wrong. Built the actual karaoke effect as per-word overlapping ASS Dialogue lines (each covering one word's [start, next-word-start) window, full cue text with just that word color-swapped) rather than trusting libass's native `\k` semantics, since real karaoke behavior (only CURRENT word highlighted, not cumulative) doesn't match `\k`'s stays-highlighted-after-passing convention.
- **Cover photo pipeline gap found + fixed**: `notion_publish_media.resolve_cover()` only ever reused Shot 1's frame or generated fresh from the Hook — never checked the row's own purpose-built "🖼️ Cover Photo" section (built by studio's `notion_prompts.py` specifically for this, top-third reserved for a title overlay that nobody ever added). Added `find_cover_photo_section_source()` as new TOP priority, Shot 1 second, Hook-gen last. Reviewed, one test-quality gap found+fixed (assertions weren't actually checking WHICH url got fetched — verified by temporarily reversing the priority in source and confirming the strengthened tests correctly fail).
- **Researched real IG Reels thumbnail best practices** (actual web search, not priors) before redoing the cover: text-overlay covers get real measured lift (+40% saves, +25% completion, 2x shares vs plain photo) — blank-top-third-for-text-added-later was exactly the anti-pattern research warns against. Rebuilt cover with baked-in Anton-font bold hook text (downloaded free from Google Fonts, not present on the system), centered in the safe zone (not literal top edge), yellow-highlight on the key word, recropped to the video's actual 1080×1920 (source gen was 1024×1536 — wrong ratio for a Reels cover, would not have matched the real video dimensions). Iterated on the copy per user pushback: "CAN'T MOVE FROM PAIN?" was too vague → "CAN'T MOVE FROM PERIOD PAIN?" (explicit, unambiguous) once told people couldn't tell what kind of pain.
- **DM infographic generation is genuinely stochastic** — first two GPT-image-2 generations both had garbled tiny-text captions (a known model weak spot for small labels); my own manual pixel-patch attempt on attempt #1 made it WORSE (overlapped a neighboring text block because I eyeballed crop boundaries instead of measuring them). Third full regeneration came out completely clean (plus added an unprompted safety disclaimer). Lesson banked: for small-label garbling, just regenerate (cheap, non-deterministic) rather than hand-patch unless you can measure exact pixel bounds first.
- **Built the actual automation the user asked for**: `notion_sync_media.write_infographic_to_row()` — when the LIVE `/admin/notion-sync` auto-generates a DM infographic (no image existed yet), it now writes that PNG back onto the Production row's own body automatically (fills existing empty toggle, else creates one anchored after the prompt code block) — previously this only ever reached the bot's local `data/media/guides/` storage, Notion page always stayed text-only, human had to re-upload by hand every time. Gated by `NOTION_SYNC_WRITE_BACK_INFOGRAPHIC` (on by default). Failure-isolated: write-back failing never costs the row its already-working `image_urls` (DM funnel is load-bearing, Notion visibility is not) — queued in new `notion_writeback_pending.json`, retried next sync, mirroring the existing wired-checkbox pending pattern exactly.
- **Review caught a real CRITICAL**: `_find_empty_dm_infographic_toggle` matched on toggle TEXT only, never actually checked whether it already had an image inside — since `PATCH .../children` APPENDS not replaces, a retried/duplicate webhook or crash-recovery re-run could have silently stacked a second image into the same toggle, directly contradicting the function's own "idempotent" docstring claim. Fixed two ways: the finder now actually checks for an existing image child, AND added a defense-in-depth re-check (`find_infographic_source(...) is not None: return`) at the top of `write_infographic_to_row` itself. Verified the fix for real, not just by inspection — added a test that calls the REAL function twice back-to-back with a tree mutated to reflect post-first-write state, confirming the second call is a true no-op (0 additional PATCH calls).
- Also fixed from the same review: HIGH (silent-forever write-back failure, no retry — added the pending-queue), MEDIUM (Notion HTTPError detail was being swallowed to a generic string — now surfaces the real response body), LOW (unsanitized filename param into a multipart header, hardened even though only ever called with a fixed constant today). Deliberately did NOT fix the other MEDIUM finding (cross-row filename collision if two rows share a keyword) — it's a pre-existing pattern across the whole module reaching beyond just this feature, flagged to user rather than scope-creeped into fixing under this task.
- 16 new tests for the write-back feature specifically (52 total in that test file), full suite 1136 passed/2 skipped throughout.
- **A concurrent Claude session (teammate, in the SAME working directory, not a separate worktree)** was independently building the IG Reels-scheduler + comment-spam-gate feature the whole time — reported via inter-agent message a real CRITICAL (cross-lock ledger race between `notion_publish.py`'s `_PLAN_LOCK` and `notion_publish_runner.py`'s `_STATE_LOCK`, both writing the same ledger file uncoordinated → could republish an already-live video) + 2 HIGH findings (a `bool("false") == True` spam-gate bug, an unguarded LLM call in a fire-and-forget path). Did NOT act on it or authorize it to proceed — that's a different session's uncommitted work in unrelated files, not something to greenlight through this session. Gave Shivonne my own independent read (agreed the CRITICAL is real and blocks turning on the scheduler) and left the call to her.
- **Committed ONLY my 3 files** (`src/notion_sync.py`, `src/notion_sync_media.py`, `tests/test_notion_sync_media.py`) despite 13+ OTHER files sitting staged in the same index from that concurrent session — used `git commit -m "..." -- <exact paths>` specifically because it commits only the named paths' current content and leaves everything else (including someone else's already-staged work) completely untouched, rather than risking a blanket commit/add that would have swept in unrelated in-progress work. Verified after the fact that the other session's staged files were still staged, unchanged. Pushed to origin/main (96963d0).

Still open:
- User hasn't yet decided whether to have the other concurrent session (or this one, or themselves) fix the Reels-scheduler lock race + spam-gate bugs — flagged, not actioned.
- Cross-row keyword-collision risk in `notion_sync_media.py`'s local generation cache (keyed by slug only, not row/content id) — same class of bug already fixed once in `notion_publish_media.py`'s cover-resolution (row_id folded into filename), never applied here. Real but out-of-scope-for-now, flagged to user.
- `data/channels/notion_writeback_pending.json` exists on disk as a stray untracked `{}` — harmless (matches sibling `notion_wired_pending.json`'s "never committed, ephemeral runtime state" convention), left alone rather than cleaned up.
- The abandoned JianYing draft at `~/Movies/JianyingPro/.../period-pain-jackie-en` was never deleted — harmless clutter, low priority.
- Whichever OTHER session is running in this same working directory should ideally move to its own git worktree — sharing one working tree + one git index across two concurrent Claude sessions is fragile by construction (this session almost committed 13 unrelated files together before catching it via `git diff --cached --stat`).

## Session — 2026-07-07 (later) — Notion Publish Date scheduler + karaoke captions script + full pipeline automation

What happened: Two distinct pieces of work in one sitting, both pushed. Started from "what's the webhook link for scheduled publish," ended with a working captioning tool + 3-stage pipeline orchestrator Shivonne can run end-to-end herself.

**Part 1 — optional Publish Date gate + daily schedule sweep (social-ip-engine live pipeline):**
- The live "go live" trigger (`POST /admin/notion-publish`) is event-driven — a Notion Automation fires it once, the instant Stage flips to "✅ Published." It was completely ignoring the "Publish Date" property that already existed in Notion — confirmed by grepping the whole publish pipeline, zero references. Added `_publish_date_eligible()` (opt-in — no date set = unchanged behavior, publishes immediately) + a new internal daily sweep (`notion_publish_scheduler.py`, off by default via `NOTION_PUBLISH_SCHEDULE_ENABLED`) since a deferred row has no future event to re-check it once its date arrives.
- Chose an internal `asyncio` loop over an external cron-job.org hit, deliberately — this Render service doesn't sleep (starter plan), and an irreversible live-post trigger shouldn't depend on a free third-party service's uptime. Mirrors the existing `reconciliation.py` sweep pattern already proven in this exact codebase.
- Extracted `notion_publish_runner.plan_and_dispatch()` so BOTH the webhook and the new scheduler share one dispatch path — refactored `src/web.py`'s endpoint to call it too. Verified behavior-preserving: all 8 pre-existing `test_admin_notion_publish.py` tests passed unmodified after the refactor.
- Two independent review agents (code-reviewer + python-reviewer) caught real issues, both fixed: **HIGH** — `_publish_date_eligible` only guarded `ValueError`; a malformed `date` shape (e.g. a list instead of a dict) raised uncaught and would have aborted the WHOLE batch, not just that row, directly contradicting the function's own "fail open per-row" contract. Widened the try to cover the whole extraction, added a regression test proving the crash first (confirmed red), then fixed. **MEDIUM** — the new scheduler swallowed sweep failures with no ops alert (unlike `reconciliation.py`'s established pattern) — a silently-broken daily sweep would leave a deferred row stuck forever with nobody notified; added `send_ops_alert` on both raised exceptions AND non-empty `errors` in a clean result.
- 1079 tests passed throughout (was 1074 before this session). Pushed as `fd534ae`.

**Part 2 — karaoke captions script + 3-stage pipeline automation (studio/):**
- Discovered this machine's ffmpeg (8.1.2, homebrew) has **no libass/drawtext/subtitles filter support** (`ffmpeg -filters` shows neither) — this DIRECTLY CONTRADICTS the 2026-07-07 (evening) session note above claiming `brew upgrade ffmpeg` fixed libass/drawtext and "verified both binaries working" — re-verified twice in this session, filters are genuinely absent now. Whatever fixed it before didn't stick (or the verification was mistaken). Built `add_karaoke_captions.py` on **moviepy** instead (already installed, 2.1.x) — immune to whatever ffmpeg's compiled filter set does going forward, so this is the right call regardless of whether ffmpeg's libass support flips again.
- Technique: local Whisper (`word_timestamps=True`) for TIMING ONLY; every word rendered TWICE at the identical (x,y) — a white "base" copy for the whole caption-chunk's duration, a yellow "highlight" copy only during that word's own [start,end] window, stacked so the current word visually "lights up." Chunking breaks on word-count (max 7) OR an early >0.5s pause, whichever first — lands on natural breath boundaries. Verified end-to-end against the REAL period-pain campaign video (not synthetic test data): transcribed, rendered, extracted a real frame, measured actual text pixel bounds with PIL/numpy (not eyeballing — a scaled preview thumbnail genuinely misled me once into thinking captions were cut off at the frame bottom when they weren't, ~330px of real margin).
- Added `align_to_known_script()` — Whisper mis-heard "cramps" as "crampus" in the real test video (same defect the PRIOR session's memory entry above also hit and hand-fixed with sequential-slice alignment). This session's version does it generically via `difflib.SequenceMatcher` (equal/same-length-replace opcodes only get corrected; word-count mismatches are left as Whisper heard them rather than guessed at) — reusable for any future campaign, not a one-off manual splice.
- `--upload` writes the result to the row's **"Production Video" page PROPERTY** (Files & media type) — distinct from `notion_video.py`'s existing `place_video_in_shot`, which only ever appends a body BLOCK. This property is the exact field `src/notion_publish.py::_extract_video_url` reads for live Reels publish, so a captioned+uploaded row is one Stage-flip away from going live.
- Shivonne then asked for full automation ("我不要 cd studio 了，我要全部东西都自动化跑啊"). Pushed back once on doing this with zero checkpoints (real $ cost per step — gpt-image-2, 即梦, MiniMax — plus documented fragile failure modes at every step in studio/CLAUDE.md itself), proposed keeping her 3 natural review points as the automation boundary instead of removing them. She confirmed exactly that shape unprompted before I even finished asking: script review → fan-out+image+voice, image/voice review → video-gen, video review → captions+upload.
- Built `pipeline_common.py` (shared helpers: content/row resolution, subprocess step runner, batch summary) + 3 thin orchestrator scripts (`generate_assets.py`, `generate_all_videos.py`, `finalize_all_videos.py`), each accepting `--content "<name>"` (every IP under that concept) or `--row <id>` (just one). Deliberately subprocess-invoke the EXISTING single-row tools (`notion_fanout.py`, `notion_image.py`, `batch_voice_gen.py`, `notion_video.py`, `add_karaoke_captions.py`) rather than reimplementing their logic — zero drift risk, matches `notion_fanout.py`'s own established precedent of subprocess-invoking a sibling script (`_sync_dm_map`). One row's failure never aborts the batch — every row attempted, clear ✅/❌ summary at the end.
- **None of the 3 stages ever touch Stage** — flipping to Ready to Publish/Published stays manual, on purpose: it's the one genuinely-hard-to-reverse action in the whole chain (a live Instagram post), so it's the one thing no script does on her behalf.
- Confirmed (and fixed my own docstring's wrong claim) that `cd studio` is NOT actually required for any of these scripts — every path is anchored via `Path(__file__)`, not cwd; verified by running from the repo root directly.
- 19 new tests (pure logic only — chunking, 2-line wrap, script-alignment, `_title_of`, batch-summary; deliberately did NOT unit-test the moviepy/Whisper/Notion-I/O wrappers themselves, consistent with this folder having zero test infra for any sibling script). Pushed as `a15f908`.

**Git hygiene note**: a THIRD concurrent session (different from the "evening" one referenced above, or possibly the same one still running) had ~13 unrelated files sitting modified/staged in this same working tree the whole time (a comment-triage/unmatched-comment DM-answering feature — chloe_agent.py, comment_triage.py, unmatched_comment.py, comment_dm_answer.py, meta_webhook.py, etc.). Staged and committed ONLY my own 17 files by exact path across 2 commits, left everything else untouched — same discipline the prior session's memory entry above already documents needing. This pattern (multiple concurrent sessions sharing one working tree) keeps recurring; worth the user actually setting up separate worktrees per the prior session's own open item, still not done.

Still open:
- Neither commit's underlying feature has been run against a REAL live Notion row / real Meta API / real money-costing API calls end-to-end — `add_karaoke_captions.py` WAS verified against a real existing campaign video (period-pain), but the 3 pipeline orchestrators have only been `--help`-smoke-tested, never a real `--content "X"` run.
- `NOTION_PUBLISH_SCHEDULE_ENABLED` is off by default in Render — Shivonne hasn't turned it on yet, and hasn't confirmed `OPS_ALERT_WEBHOOK_URL` is set (the new scheduler's failure-alerting is a no-op without it, same as every other ops_alert call site).
- The ffmpeg libass/drawtext regression (present now, previously reported fixed) is unresolved and unexplained — didn't investigate WHY it regressed, just routed around it via moviepy. Worth a `brew` investigation if drawtext/subtitles filters are ever needed directly again.
- Whichever concurrent session owns the comment-triage/unmatched-comment files should still move to its own worktree — same open item as the prior session, still unaddressed by anyone.

## Session — 2026-07-08 (Jackie's Facebook Page: full activation, 3 real bugs found+fixed)
What happened: Wired Jackie Chan TCM's Facebook Page end-to-end — Meta App dashboard steps (Page token generation via Graph API Explorer since Messenger's own Access Tokens panel only requests a fixed scope bundle and can't be made to include extra permissions), Render env vars, app-level + page-level webhook subscriptions — then live-tested with a real user (SK Chan commenting "detox") and found/fixed 3 separate real production bugs along the way, each with regression tests + a python-reviewer pass, each deployed same-session.

Decisions / shipped (all on main, all deployed, all verified live):
- **Meta App reuse confirmed**: Jackie's new FB Page (`528216523715336`) sits under the SAME parent Meta App as the original Chloe setup (`1546738537122434`, "TCM-ChloeChan") — one App, multiple Pages/IG accounts via Business Manager, consistent with how IG already worked for both personas.
- **Render env var gotcha (bit us twice this session)**: `restart` API reuses the env snapshot from the LAST REAL DEPLOY — it does NOT re-read freshly-changed env vars. Only `POST /deploys` actually picks up new values. Wasted real time on this before remembering.
- **Bug 1 — FB comments always misclassified as replies** (`src/channels/meta_events.py::IncomingComment.is_reply_to_comment`): Facebook's "feed" webhook sets `value.parent_id` to the POST's id for EVERY comment (top-level or nested), never blank the way IG's shape is — so the old check (`parent_id set and != comment_id`) was true for 100% of FB comments. Comment→DM had been silently broken for the entire FB channel since it shipped. Verified root cause via a direct Graph API fetch of a real top-level comment showing no `parent` field at all. Fix: only a reply when parent_id differs from BOTH comment_id AND media_id/post_id. Fails closed (treated as reply) when media_id can't be parsed. 8 new tests — first coverage this parsing module ever had. Commit `4add8b8`.
- **Bug 2 — all 17 of Jackie's keyword rules were IG-only**: `comment_responses.json` rules had `"accounts": [IG id]` only, so the account gate silently rejected every rule on the new FB Page even after Bug 1 was fixed. Quick unblock: bulk-added the FB Page id to all 17 rules' accounts arrays (mechanical, reversible). Flagged the proper fix (registry-driven `channels.facebook` in ip.json + generic account-equivalence resolution) as follow-up, not done under live-testing pressure. Commit `43ff5ed`.
- **Bug 3 — Jackie's FB DMs replied in Cantonese**: real user got a Cantonese LLM reply from an English-only persona. Root cause: `src/web.py`'s startup agent-registration loop only ever checked `ip.channels.get("instagram")` (hardcoded) — Jackie's FB Page account id was never in `_account_agents`, so `_get_agent()` silently fell back to the DEFAULT agent (Chloe, Cantonese). Proper fix this time (not a quick patch): added a `facebook` channel to `data/ips/jackie/ip.json` (mirrors how `instagram` already stores `token_env`/`user_id_env` pointers) + new pure `registry.persona_dm_channels(ip)` helper + web.py loop now iterates ALL persona channels, not one hardcoded name. 10 new regression tests including a cross-IP-different-channel-name collision test. python-reviewer flagged one HIGH follow-up (`notion_sync.py`'s `_ip_account()` has the same hardcoded-"instagram" pattern for comment-rule auto-drafting — separate feature, not fixed, tracked). Commits `9a14fc1` (+ web.py's portion landed inside a concurrent session's unrelated commit `fd534ae` — see gotcha below).
- **Public comment-reply permission (`pages_manage_engagement`) chase**: wasn't visible in the app's Permissions/Features list because Meta scopes permissions by Use Case now — the app only had "Messenger from Meta" configured. User added it manually (found via "Add more to this use case"), but 2 regenerations from Messenger's own Access Tokens panel still didn't pick it up (that panel always requests a fixed bundle regardless of what's separately enabled). Fix: **Graph API Explorer**, which lets you hand-pick permissions — generates a USER token first, which then needs `/me/accounts` to derive the actual PAGE token carrying those scopes. Final token has `pages_messaging`, `pages_manage_engagement`, `pages_manage_posts`, `pages_read_engagement`, `pages_manage_metadata`, `expires_at: 0` (permanent).
- **End-to-end verified live**: real comment → private-reply DM sent ✅, public comment-reply posted ✅ (fetched back via Graph API to independently confirm, not just trusted the "sent ok" log line), DM images delivered ✅, follow-up conversational turn now correctly answers in English ✅.

Gotcha for next time: **cross-session git collision** — mid-session, `git status` showed my in-progress edit to `src/web.py` had already been committed by a CONCURRENT session's unrelated commit (`fd534ae`, "Publish Date gate" feature) because that session also touched web.py and its commit scooped up whatever was on disk at the time. Then my own `git commit` (after `git add <3 specific files>`) picked up 7 files from the OTHER session that got staged between my `add` and `commit`. Neither caused functional harm (content was correct in both cases) but both are real races from two Claude sessions using git in the same working tree simultaneously — worth being more paranoid about `git status`/`git diff --cached` immediately before every commit in a repo this actively shared, not just before staging.

Still open:
- `notion_sync.py`'s `_ip_account()` hardcoded-"instagram" pattern (HIGH from reviewer) — same bug class as Bug 3, different feature (comment-rule auto-drafting from Notion), not yet fixed.
- FB feed **posting** (not DM/comments) — token now has `pages_manage_posts`, technically unlocked, but ZERO code exists for it (IG has `ig_publish.py`/`ig_publish_carousel.py`/Notion wiring, FB has nothing). Discussed twice, deliberately deferred both times pending an actual scope decision from Shivonne (mirror Reels 1:1 to FB feed? separate content? same Notion trigger?). She just asked again ("can you AutoPost FB page") at the very end of this session — not yet scoped or built.
- Decided NOT to migrate the 17 existing Jackie keyword rules to the language-only (`"language":"en"`, no explicit `accounts`) pattern — they're proven working, no reason to touch. New rules going forward should use the language-only pattern instead of hardcoding both account ids.
- Wrote `docs/META-APP-SETUP-GUIDE.md` — generic, variable-ized Meta App (Instagram+Messenger) setup tutorial for forwarding to a colleague's co-worker, informed by everything learned this session.

## Session — 2026-07-08 (FB Reels mirror — first live test)
What happened: Shivonne asked whether IG/FB auto-posting was done and to try posting one video to Facebook (linked a specific Notion Production row — the tonsil video, already live on IG). Found the FB-mirror feature (commit efa043a) fully built/reviewed but never live-tested; `NOTION_PUBLISH_FB_ENABLED` was already flipped `true` on Render from an earlier session today. Investigated before firing anything: the bulk endpoint (`POST /admin/notion-publish` → `plan_fb_mirrors()`) would have mirrored ALL 5 backlogged IG-published rows at once (not just the one row she linked), and would have done so with **blank captions** — those 5 ledger entries are "reconciled" stubs from an earlier incident (stale git HEAD broke ledger persistence for days) that only captured creation_id/media_id, not caption/cover. Their stored `video_url` is also an expired S3 presigned URL (confirmed 403).
Instead of the bulk path, wrote a scoped one-off (`scripts/fb_test_publish_one_row.py`) that re-fetches ONE row fresh from Notion (live video_url, real Hook/CTA → real caption via the same resolution `plan_publishes()` uses), follows the repo's existing `--confirm-publish` safety-gate pattern (prep + poll to `upload_complete`, stop, require explicit re-run to actually finish/publish). Verified the "gut" CTA keyword already has a wired comment→DM rule covering Jackie's FB Page account before going live.
Result: **first real Facebook Reels post went live** — video_id `1428188979170685`, permalink `/reel/1428188979170685/`, caption/CTA correct. Wrote the "published" record into the real FB ledger (`data/channels/notion_publish_fb_state.json`), pushed to git (commit `ebe5350`), and triggered a manual Render deploy (`dep-d96uk2ks728c738bv9m0`) so the LIVE container's ledger matches — otherwise the next automated `plan_fb_mirrors()` run (webhook or future daily sweep) would have re-mirrored the same row and double-posted, since Render's own disk copy didn't have my locally-written entry until redeploy.

Decisions & reasoning:
- Deliberately did NOT hit the live bulk endpoint even though it was the "obvious" quick test — the blast radius (5 posts, not 1; blank captions) was a real correctness/scope problem, not just theoretical caution. Scoped a single-row script instead.
- Followed the codebase's own established convention for irreversible live-publish scripts (`--confirm-publish` gate, prep-then-stop default) rather than inventing a new pattern — same shape as `scripts/publish_pressure_points_carousel.py`.
- Pulled FB_PAGE_ACCESS_TOKEN / NOTION_KEY from Render env vars into a /tmp file for the one-off run (local .env has neither) since this repo intentionally keeps prod-only secrets off local dev; deleted the temp file immediately after use.

Still open:
- The other 4 backlogged IG-published rows (reconciled stubs, blank caption, expired video_url) are NOT yet mirrored to FB. If Shivonne wants them mirrored too, each needs the same fresh-refetch treatment (or `plan_fb_mirrors()`'s reconciled-ledger gap needs fixing first) — do NOT just flip on the bulk endpoint against the current ledger.
- `notion_publish_state.json` (IG's ledger) is still untracked/uncommitted locally — same underlying persistence gap that caused the original reconciliation incident. Worth committing properly in a future session so Render and local git stay in sync.
- Verify via the live Notion Production Tracker / Jackie's FB Page that the Reel finished processing and is publicly visible (checked mid-processing at test time, status was still `processing_phase: in_progress` — normal async Meta behavior, should finish within minutes).

## Session — 2026-07-08 (session-widget: floating Claude Code status monitor)

### What happened
Built a new personal tool from scratch: a floating macOS widget showing live status for every open Claude Code terminal session — project folder, 1-3 word task label (Haiku-generated), and a working/idle traffic-light dot. Project lives at `/Users/shivonne/Claude Code/session-widget/`. Planned via `planner` agent first, then built + debugged live against real hooks wired into `~/.claude/settings.json`.

### Architecture shipped
- **Data layer**: native Claude Code hooks (`SessionStart`, `PreToolUse`/`PostToolUse` matcher `"*"`, `Stop`, `SessionEnd`) write per-session JSON state to `~/.claude/session-widget/sessions/<id>.json`. Added additively to the user's live `settings.json` (backed up first, merged via `jq`, diffed to confirm existing shared-brain hooks untouched).
- **Renderer**: Python + PySide6 floating always-on-top window, right screen edge, polls every 1.5s. Files: `renderer/{config,status,session_store,session_box,layout,widget,mac_native}.py`.
- **Labeler**: `labeler/{generate-label,should-run,prompt.txt}` — Haiku 4.5 via `claude -p --safe-mode --model claude-haiku-4-5`, debounced (45s or 5 tool-calls), lock-guarded against overlapping runs.

### Critical bugs found + fixed
1. **Phantom sessions from the labeler itself**: any `claude -p` call fires the same global hooks and registers as its own fake "terminal." Tried `--bare` (skips hooks) but it also strips OAuth/keychain auth → "Not logged in". Fix: `--safe-mode` skips hooks too but leaves normal subscription auth intact — the actual correct flag.
2. **Window invisible after adding macOS-native pinning**: `ns_window.setCollectionBehavior_()` raised `NSInternalInconsistencyException` (Qt's default `MoveToActiveSpace` conflicts with `CanJoinAllSpaces`) — exception was silently swallowed by my own try/except, so the whole native-pinning call silently no-op'd. Fix: clear `MoveToActiveSpace` bit before OR-ing in `CanJoinAllSpaces`.
3. **Widget disappearing whenever switching to another app**: Cocoa utility/tool panels default `hidesOnDeactivate=YES`. Fixed via `ns_window.setHidesOnDeactivate_(False)`.
4. **Boxes rendering washed-out/near-transparent instead of dark**: Qt parses 8-digit hex as `#AARRGGBB` (alpha first), I'd written it CSS-style (`#RRGGBBAA`, alpha last) → ~12% opacity instead of 88%. Fixed by switching to `rgba()` to remove the ambiguity.
5. **Sessions silently disappearing after ~10 min of being idle-but-still-open**: original ghost-timeout logic conflated "quiet for a while" with "probably closed." Real fix: added a `SessionEnd` hook (fires on actual terminal close) as the authoritative removal signal; relaxed the time-based fallback to 8 hours (crash-only safety net, not the primary mechanism).
6. **Row order not matching visual terminal tabs**: tested whether hook scripts can see their controlling tty (would have let me match Terminal.app's real left-to-right tab order) — confirmed they can't (`ps -o tty=` reports `??`, no controlling terminal in this sandboxed tool-execution context). True tab-order matching is not buildable with what Claude Code's hooks expose. Pivoted to sorting by most-recently-active session instead (predictable "top = whatever you're touching right now," no correlation needed).
7. Renderer was updating box *content* in place but never re-sorting visual position — fixed to fully re-order the layout every refresh cycle.

### Decisions made
- v1 = personal tool, built on Claude Code's native hooks (not the private shared-brain scripts) specifically so it doubles as the foundation for a possible later sellable version — same data contract, only the renderer/packaging would change for v2.
- Floating window over tmux pane / iTerm-specific integration — works regardless of terminal app, zero workflow disruption.
- Dropped model-name display from the final spec (Shivonne's call) — final v1 fields are project folder + task label + status dot only.
- PySide6 chosen for v1 (fast to build); native SwiftUI `NSPanel` flagged as the right call for a real v2 (handles full-screen Spaces coverage properly, which PySide6 doesn't fully solve).

### Still open
- Widget currently overlaps Shivonne's desktop file icons in the top-right corner (visually, translucent boxes sit on top of them) — offered to reposition, no answer yet.
- Auto-start on login (launchd) not wired — currently a manually-launched foreground process.
- Two of the 6 live sessions still show empty task labels (haven't had fresh activity since the labeler was fixed) — will self-populate on next real tool use in those sessions.
- No automated tests written for any of this (hooks, renderer, labeler) — built via live manual verification against real running sessions instead, given the personal-tool / rapid-iteration nature of the work.
- v2 (sellable product) not started — would need: SwiftUI rewrite of the renderer, a proper installer that merges hooks into a customer's own `settings.json`, and switching the labeler from CLI `--safe-mode` to a direct Anthropic API key for packaging independence.


## Session — 2026-07-08 (continued: caption bug fix + cover-photo audit across the board)
What happened: Following the FB Reels first-live-test session (video_id 1428188979170685), Shivonne caught that the post's Title/Cover were wrong. Root-caused + fixed properly (not just patched the one post):

**Caption bug (shipped in src/, NOT yet pushed/deployed):**
- `src/notion_publish_caption.py` was pulling the caption headline from the Content page's internal "Hook" property instead of the Production Tracker row's `🏷️ Title` property (the actual public-facing punchy title, authored by `studio/scripts/notion_fanout.py`'s `draft_title()`). This is shared code — it drives the LIVE Instagram auto-publish webhook too, not just the FB mirror, so this bug likely affected real IG captions already.
- Fix: added `extract_title_property()` + `extract_headline()` (Title first, Hook fallback), wired into `notion_publish.py`'s `_plan_publishes_locked()`. python-reviewer pass caught 1 HIGH (hardcoded property name — added `NOTION_PUBLISH_TITLE_PROP` env override, same pattern as `NOTION_PUBLISH_DATE_PROP`) + 2 MEDIUM (silent fallback now surfaces a warning into the existing `warnings` list; avoided a duplicate Notion API call by threading the already-resolved `hook` into `extract_headline`). Full suite green (1232 passed, 2 skipped).
- **STILL UNCOMMITTED AND UNDEPLOYED** — sitting only on local disk. Any row that flips to ✅ Published before this ships still gets the old (wrong) Hook-based caption. Shivonne hasn't said commit/push yet — asked, no answer yet, treat as still open next session.
- Live-fixed the ALREADY-PUBLISHED Tonsil FB post's caption directly via Graph API `POST /{video-id}` `description=` param (confirmed editable post-publish).

**Cover-photo audit (all fixes are Notion-only, studio/ is never deployed — no ship/deploy needed for these):**
- Root cause: `notion_publish_media.resolve_cover()` only recognizes the NEW schema (`🖼️ Cover Photo` heading_3 → `🖼️ Cover here` toggle → image inside). Some older rows use a DIFFERENT older schema (`🖼️ Reel Cover Photo Image Prompt` heading + a bare image block, no toggle) which is invisible to it — a row can have a perfectly good, already-approved cover sitting on the page and still silently fall through to blind AI generation (no character reference → wrong person drawn, confirmed once live for Tonsil's FB test).
- Wrote `studio/scripts/audit_cover_schema.py` — scans every Production Tracker row (36 total), classifies `new_ok` / `migrate` (old-schema image exists, needs mirroring into new toggle) / `missing` (no cover anywhere, never auto-generated — blind generation risk). Only ONE row had the `migrate` case (Dry Eyes, cover from 2026-06-30) — already fixed by mirroring the same bytes into a new toggle (old copy left in place, mildly redundant on the page but harmless; Shivonne offered a later cleanup, not done).
- Wrote `studio/scripts/upload_downloaded_covers.py` — matches Shivonne's manually-downloaded ChatGPT cover PNGs (`~/Downloads/cover-*.png`, matched by topic/keyword against row Name/Title) to their Production Tracker row, creates the `🖼️ Cover Photo` section if entirely absent (via `notion_prompts.cover_blocks()`, same shape `apply_shot_plan`/`backfill_cover_dm_prompts.py` use), uploads via Notion's `/file_uploads` API into the `🖼️ Cover here` toggle. Every upload verified end-to-end by actually calling `notion_publish_media.find_cover_photo_section_source()` (the real function the live webhook uses) against the row afterward — not just assumed from the API response.
- **Self-caught mistake, worth remembering**: first pass at compiling the "which published/ready rows still need a cover" table incorrectly included Period Pain — it actually already had a real cover (confirmed has_children=True, dated 2026-07-07). This was MY manual cross-referencing error, not a bug in the audit script (re-ran the same script twice, got consistent correct results both times). Shivonne caught it by screenshotting the row. Lesson: when compiling a cross-referenced summary table by hand from two separate query outputs, re-verify each row directly before reporting it as actionable — don't trust the manual merge.
- Rows fixed this session (cover now uploaded + verified machine-readable): Building Muscle, Yellow Teeth (Jackie/EN), Constant Anxiety, Show Me Your Tongue EP01, Migraine (new section added), Dry Eyes (migrated from old schema), Knee, Detox Juice, Tonsil Stone.
- Tonsil's LIVE Facebook post thumbnail also updated post-hoc via the Graph API `/{video-id}/thumbnails` edge (multipart upload with `source` + `is_preferred=true`) — confirmed via the video's `picture` field that the new thumbnail is now live and all 11 auto-extracted frame candidates are non-preferred. This `/thumbnails` edge works and is reusable for any other already-published-with-wrong-cover FB post in the future.

Still open:
- 2 published/ready rows still missing a cover entirely: 💤 Sleep, 🦷 Yellow Teeth × Jessica (Cantonese). Shivonne generating covers for these manually (ChatGPT), will send when ready — same upload+verify flow applies.
- The caption fix (src/notion_publish_caption.py + src/notion_publish.py) needs a commit + push + Render redeploy before it actually protects the live IG/FB auto-publish path. Ask again next session if not done.
- Dry Eyes has a duplicate cover now (old-schema bare image from 06-30 + new-schema toggle mirror added this session) — Shivonne said maybe clean up the old one later, not done.
- `data/channels/notion_publish_state.json` (IG ledger) still untracked/uncommitted locally — same persistence gap flagged in the earlier FB-mirror session, not yet resolved.
- Consider running `audit_cover_schema.py` again periodically / wiring a check into the publish path itself, since the underlying old-vs-new schema split is still a landmine for any row authored before ~2026-07-06 that nobody has manually reviewed yet.

Decisions & reasoning:
- Never auto-generated a replacement cover via blind text-to-image for any "missing" row — established early (Tonsil incident) that gpt-image-2 has no character reference for Jackie/Jessica and reliably draws the wrong person. Every fix this session was either (a) uploading Shivonne's own reviewed ChatGPT-generated image, or (b) mirroring an already-existing, already-approved image from elsewhere on the same page. Zero new blind generations shipped anywhere.
- Verified every "fixed" claim against the ACTUAL function the live webhook calls (`find_cover_photo_section_source` / a live Graph API re-fetch), not just "the PATCH call returned 200" — caught nothing wrong this way this session, but it's the right discipline given this is literally the same class of bug (something LOOKS done but the machine can't actually see it) that started the whole thread.

## Session — 2026-07-08 (communication preference)
What happened: Shivonne set a standing communication rule for Shello.
Decisions:
- Always lead with the RESULT first, then explain what was done
- Reports must be in point form (bullets), not long paragraphs — she doesn't want to read a lot of text
Still open: planner agent running in background on the finalize-bundler + cover-gen plan (ear campaign row); will report back in this new format once it completes.

## Session — 2026-07-10
What happened: Big infra day. (1) Shipped the cover fix — publish now reads the 🖼️ Cover Photo toggle (was NEVER read; live posts used Shot 1/blind-gen covers). (2) Shipped 🏷️ Title-first captions. (3) Root-caused + fixed FB mirror: ledger's Notion S3 video URL expires in 1h and the mirror STRUCTURALLY runs later → every mirror 403'd; now re-fetches a fresh URL at publish time (stable-URL match guard so a replaced file is refused). Period Pain published to FB successfully (fb_media_id 1717524199489054) — first-ever successful auto-mirror. (4) Found the DM re-send root cause: free Postgres expired 2026-06-20 and was DELETED; DATABASE_URL (fromDatabase → dead db) resolved empty → prod silently ran SQLite on EPHEMERAL disk for 3 weeks — every deploy wiped CRM + webhook_events dedup → reconciliation sweep re-DM'd old comments after every deploy. Reconnected tcm-jessica-db-2 (created 6-26, never wired), added fail-loud guard (APP_ENV=production refuses non-postgres DATABASE_URL), set RECONCILE_ENABLED=false temporarily.
Decisions: FB mirror refreshes ONLY the video URL (transport), never caption/cover (content) — byte-for-byte mirror guarantee kept via stable-URL match. 3 incident-artifact FB rows (blank captions) left to expire into skipped — never auto-mirror. Period Pain's stale FB entry deleted for a clean retry. render.yaml: DATABASE_URL now sync:false — never fromDatabase against an unmonitored free db.
Still open: (1) RE-ENABLE RECONCILE_ENABLED=true after 2026-07-13 (72h lookback window must slide past current comments on the EMPTY new dedup table first). (2) tcm-jessica-db-2 is free tier → expires ~2026-09-24 — user must upgrade or calendar it (guardrail makes expiry loud now, but service still stops). (3) 3 weeks of CRM history permanently lost — new db starts empty. (4) Period Pain's IG post (published 7-09 with OLD cover logic) has a wrong-ish cover that cannot be changed via API. (5) Notion 🚀 Posted to FB checkbox tick queued for retry (property may not exist on the db yet — create it like 🔗 DM Wired).
