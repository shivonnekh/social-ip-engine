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
