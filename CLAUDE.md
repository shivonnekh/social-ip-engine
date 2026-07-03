# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

---

## 1. Project Identity

**social-ip-engine** (renamed from TCM-Jessica on 2026-07-03; local path
`/Users/shivonne/Claude Code/social-ip-engine`, GitHub
`shivonnekh/social-ip-engine` — old URLs redirect) is a **multi-IP,
multi-platform social reply service**: AI content-creator personas answer
Instagram comments (canned keyword rules, L0) and DMs (one-call persona
agent, L1). Messenger is next; TikTok after that.

**Active IPs:** Jackie Chan TCM (`jackiechan.tcm`, English — main IP) and
Chloe/陳芷晴 (`chloechan.cccc`, Cantonese). See `data/personas/*.json`.

**Reply policy (all IPs):** standalone content creators. No clinic, no
commerce, no prices, no bookings, no off-platform push. If asked about a
physical clinic / in-person consult: "not at the moment — text guidance
and support right here." Encoded in the persona prompts.

**Strategy doc:** `/Users/shivonne/Claude Code/TCM-INTEGRATION-PLAN.html`
(v2, 2026-07-03) — plan to fold the `ai-tcm-ip` content factory into this
repo as `studio/` and go multi-platform.

### ⚠️ Everything WhatsApp-related below is LEGACY (parked)

The original product in this repo — a WhatsApp sales & care agent
("Jessica") for a clinic partner — was **discontinued in July 2026**
(partnership ended). The deep pipeline (Planner→Specialists→Writer),
sales/booking tools, and broadcaster remain in the codebase but are
**parked: do not extend, do not build on them.**

- `WA_POLL_ENABLED=false` + `BROADCAST_ENABLED=false` — enforced in the
  Render dashboard AND render.yaml (2026-07-03). Do not re-enable.
- Sections 2, 3.1–3.9, and the WhatsApp parts of 4–10 below describe this
  legacy stack. They are kept accurate for archaeology, not direction.
- The LIVE product is §3.10 (Social Channels) + the persona files + the
  comment rules. When in doubt, that's the code that matters.

---

## 2. Architecture (Big Picture) — LEGACY (WhatsApp stack, parked)

```
                          WhatsApp (ChatDaddy IM API)
                                    │
                                    ▼
                       ┌────────────────────────┐
                       │  Inbound Gateway       │  poller + webhook
                       │  - dedup               │
                       │  - blocklist           │
                       │  - media intake        │
                       └────────────┬───────────┘
                                    │
                                    ▼
                       ┌────────────────────────┐
                       │  Buffer & Merge        │  wait window for
                       │  (per-chat queue)      │  rapid-fire msgs
                       └────────────┬───────────┘
                                    │
                                    ▼
                       ┌────────────────────────┐
                       │  CRM Read              │  load user state
                       │  - status, age, loc    │  + conversation
                       │  - history, notes      │    history window
                       └────────────┬───────────┘
                                    │
                                    ▼
                       ┌────────────────────────┐
                       │  PLANNER AGENT         │  decides:
                       │  inputs: CRM + msg     │  which specialist(s)
                       │  output: routing plan  │  + can fan out 2 in
                       │                        │    parallel
                       └────┬───────────────────┘
                            │
                ┌───────────┼───────────┬──────────────┬───────────────┐
                ▼           ▼           ▼              ▼               ▼
        ┌─────────────┐ ┌────────┐ ┌─────────┐ ┌──────────────┐ ┌────────────┐
        │ Greeting/   │ │  FAQ   │ │  Sales  │ │ TCM Constit. │ │ Appointment│
        │ Others      │ │ Agent  │ │  Agent  │ │  Agent       │ │  Agent     │
        │             │ │        │ │         │ │ (9 體質)     │ │            │
        │ - no tools  │ │ - KB   │ │ - paid  │ │ - tongue img │ │ - clinic   │
        │ - chit-chat │ │   search│ │   prods │ │ - 4 MCQs     │ │   match    │
        │             │ │ - cards │ │ - pitch │ │ - 湯水推薦   │ │ - slots    │
        └─────────────┘ └────────┘ └─────────┘ └──────────────┘ └────────────┘
                │           │          │              │               │
                └───────────┴──────────┴──────────────┴───────────────┘
                                    │
                                    ▼
                       ┌────────────────────────┐
                       │  FINAL WRITER AGENT    │  composes 1 final
                       │  - merges all outputs  │  reply, splits into
                       │  - HK Canto polish     │  bubble messages
                       │  - bubble split        │
                       └────────────┬───────────┘
                                    │
                                    ▼
                       ┌────────────────────────┐
                       │  CRM Write + Trace     │  persist state +
                       │  Outbound Send         │  full step trace
                       └────────────┬───────────┘
                                    │
                                    ▼
                          User WhatsApp (bubbles)
```

### Load-Bearing Invariants (Do Not Break)

1. **Every turn must produce a complete trace** — Planner decision, specialist calls (inputs + outputs + tools used + KB cards read), Writer composition, final bubbles sent. Stored per `(user_id, turn_id)`. If a feature breaks tracing, the feature is wrong.
2. **Planner is the ONLY agent that decides routing** — Specialists do not call other specialists. They return structured output and stop.
3. **Final Writer is the ONLY agent that user-facing text passes through** — Specialists never write user-facing copy. They return structured intent/content; the Writer turns it into 廣東話口語 bubbles.
4. **Knowledge access is card-driven** — FAQ + Constitution + Sales agents read from JSON cards in `data/knowledge_base/` and `data/products/`. No hallucinated TCM content. If no card matches, the agent says so honestly to the Writer.
5. **CRM is the single source of user state truth** — Specialists do not maintain their own user memory. Read from CRM at turn start, write back at turn end.

---

## 3. Components

### 3.1 Inbound Gateway (`src/whatsapp/`)
Ported from `dr-baba-agent/src/whatsapp/`. Handles:
- ChatDaddy IM API auth (apit_ token OR refresh-token flow, refresh every 50 min)
- Webhook receiver + dedup
- Polling fallback (when ChatDaddy event service stalls)
- Media download (tongue photos, voice notes)
- Blocklist (per-phone opt-out)

### 3.2 Buffer & Merge (`src/whatsapp/buffer.py`)
Ported from `dr-baba-agent`. When a user fires 3 messages in 4 seconds, we wait ~3-5s after the last message before invoking the Planner — otherwise we'd respond to fragment 1 while fragments 2 and 3 are still arriving. See `dr-baba-agent/src/whatsapp/router.py::_enqueue_for_merge`.

### 3.3 CRM (`src/crm/`)
**This is new — Dr. Baba does not have a real CRM.** Required fields per user:

| Field | Type | Source |
|-------|------|--------|
| `phone` | string | WhatsApp |
| `name` | string | extracted or asked |
| `status` | enum | `new` / `qualified` / `constitution_done` / `bought` / `booked` / `churned` / `opted_out` |
| `age` | int | asked when relevant |
| `location` / `district` | string | asked at appointment stage |
| `constitution` | enum (9 體質) | set by Constitution Agent |
| `pain_points` | list | extracted from conversation |
| `products_pitched` | list | what Sales Agent has shown |
| `products_purchased` | list | confirmed orders |
| `appointments` | list | booked slots (separate table, joined on read) |
| `notes` | text | freeform — written by memory consolidator (§3.8) + agents |
| `conversation_history` | list[message] | rolling window (last 20 turns, full log in `messages` table) |
| `tags` | list[string] | custom labels |
| `temp_state` | dict | cross-turn flow state owned by specialists (e.g. `constitution_q_index`, `awaiting_delivery_address`, `last_consolidated_at`) |
| `last_period_start` | date \| None | menstrual cycle tracking (optional, female users) |
| `cycle_length_days` | int | default 28; drives 月事陪伴 broadcast |

Storage: **PostgreSQL** in production (Render free tier, 1GB, persistent). SQLite for local dev. `CRMRepo` (aiosqlite) and `CRMRepoPG` (asyncpg) implement the same async surface — `repo_factory.py` picks the driver based on `DATABASE_URL`.

### 3.4 Planner Agent (`src/agents/planner.py`)

The Planner does **three jobs in one LLM call** (gpt-5.4-mini):

1. **Route** to 1-2 specialists. Two is the cap (more = too messy for Writer).
2. **Rephrase** the user message into clean HK 廣東話 (`rephrased_query`).
   Strips filler / mixed scripts / typos so downstream specialists work
   on a normalised input. Passed via `SpecialistInput.rephrased_query`;
   specialists pick it up via the `effective_query` property.
3. **Extract** health complaints (`extracted_pain_points: list[str]`) as
   NER tags. Multi-tag in single turn supported ("頭痛+失眠+腰痛" → 3 tags),
   plus catch-up sweep of last 5 turns for any complaints CRM missed.

Output: `PlannerDecision { specialists, mode, reasoning, notes_for_writer,
proactive_hint, rephrased_query, extracted_pain_points }`.

**Why one LLM call**: gpt-5.4-mini can handle routing + rephrase + NER
together; splitting into separate calls would double latency + cost for
no quality gain.

Rule fast-paths bypass the LLM entirely for deterministic cases
(tongue photo, wa.me order, farewell, MCQ answers, simple greetings,
health complaints, etc.). See §3.5 table.

### 3.5 Specialist Agents (`src/agents/`)

| Agent | Tools | Knowledge | Output Schema |
|-------|-------|-----------|---------------|
| `greeting_agent.py` | none | none | `{ tone: "warm", topic: str, suggested_followup: str? }` |
| `casual_agent.py` | none | none | Empathic chit-chat for returning users + non-medical topics. Driven by Planner's `notes_for_writer` for proactive follow-up. |
| `faq_agent.py` | `search_kb`, `read_card` | `data/knowledge_base/` (52 cards: soups, constitution, faq, acupressure) — vector + keyword hybrid via `tools/kb_search.py` | `{ answer_facts: list, cards_used: list[card_id], confidence: float }` |
| `sales_agent.py` | `recommend_product`, `share_product_image`, `share_order_link` | `data/products/` | `{ products_to_pitch: [{ name, price_display, indications, constitution_match, image_url }], pitch_angle, urgency }` — payload **MUST include 功效 (indications) + image** for every product mentioned (Writer enforces this) |
| `constitution_agent.py` | `analyze_tongue` (vision, gpt-5.4-mini), `ask_constitution_question`, `declare_constitution` | `data/knowledge_base/constitution/` | 4-phase state machine: asking_tongue → analyzing_tongue → asking_mcq (4 MCQs) → declaring. On declare, **persists a TongueRecord** to `user.tongue_photos` + clears `constitution_*` temp_state. |
| `appointment_agent.py` | `match_clinic_by_location`, `propose_slot`, `confirm_booking` | `data/clinics/clinics.json` | `{ phase: "asking_mode" \| "asking_location" \| "proposing_slot" \| "confirming", payload: ... }`. Auto-defaults to `in_person` after asking_mode once + user shows scheduling intent. |
| `tongue_progress_agent.py` | vision compare (gpt-5.4-mini), diff structured fields, narrative LLM call | uses prior `TongueRecord` from CRM | `{ phase: "compared" \| "first_photo", current_analysis, previous_record, changes, overall_direction, narrative_zh }`. Emits `tongue_photos_append` diff so pipeline persists the new record. |

**Planner-level rule fast-paths** (bypass LLM, deterministic):

| Rule | File | Effect |
|------|------|--------|
| wa.me order | `sales_agent._ORDER_RE` | "想訂【...HK$...】" → SALES (parse + collect address) |
| Awaiting delivery address | `_TS_AWAITING_ADDRESS` | mid-order-flow → SALES |
| Tongue photo + prior history | `planner.py` | media + `constitution!=UNKNOWN` + `len(tongue_photos)>=1` → TONGUE_PROGRESS (else CONSTITUTION) |
| Mid-constitution flow | `planner.py:_looks_like_mcq_answer` | findings present + UNKNOWN constitution + msg looks like A/B/C/D → CONSTITUTION (escape valve: non-MCQ msg falls through) |
| Farewell detection | `planner.py:_is_farewell` | tail-position match on 拜拜/bye/多謝/晚安/etc. → GREETING + CRM-aware closing summary |
| Returning user greeting | `planner.py:_build_returning_hint` | "hi" + CRM has context → CASUAL + proactive follow-up referencing prior pain_points |
| Health complaint shortcut | `agents/acute_pain.py:detect_health_complaint` | 頭痛/失眠/腰痛/etc. + returning user → FAQ + CASUAL (KB owns acupoint content, NO hardcoded mapping) |
| Emotion detection (七情) | `agents/emotion.py:detect_emotion` | Stress/anger/sadness → 七情 → 五臟 mapping → CASUAL + FAQ. Wins over health-complaint rule when both fire. |
| Symptom memory | `agents/symptom_memory.py` | Same symptom mentioned ≥3 times in history → CASUAL + FAQ with caring tone |

### 3.6 Final Writer Agent (`src/agents/writer.py`)
- Input: CRM context + user message + ALL specialist outputs
- Output: list of bubble messages (target ~150 chars, max 250, see `dr-baba-agent/src/whatsapp/client.py` `BUBBLE_TARGET`)
- Responsible for: tone consistency (Jessica voice), HK 口語 polish, removing redundancy when 2 specialists overlap, inserting media (images) at the right bubble boundaries.
- **NEVER** invents medical/product facts. Only re-narrates what specialists provided.

### 3.7 Orchestrator (`src/orchestrator/`)
The conductor — runs the full pipeline per turn:
1. CRM load
2. Planner call (route + rephrase + extract — see §3.4)
3. Fan-out specialist calls (sequential or parallel per Planner decision).
   Each receives `SpecialistInput.rephrased_query` for cleaner downstream
   LLM/KB work.
4. Writer call (gpt-5.4-mini composes 5-bubble reply; adaptive cap to 8
   bubbles when payload has ≥2 products)
5. CRM write + trace persist:
   - Apply specialist diffs (`_apply_specialist_diffs`)
   - **Two-rail pain_points extraction**: use `decision.extracted_pain_points`
     if present, else fall back to `detect_all_health_complaints(text)`
     keyword scan. Prevents CRM going empty when LLM omits the field OR
     when a rule fast-path bypassed the LLM entirely.
   - Persist new appointments + new tongue_photos via `_append` convention
6. **Background: fire memory consolidator if ≥15 new messages** (§3.8) —
   `asyncio.create_task`, zero latency to user
7. Send bubbles via WhatsApp client

Every step emits a structured trace event. See §5.

### 3.8 Memory Consolidator (`src/agents/memory_consolidator.py`)

Jessica's rolling history is 20 messages. Anything older is in the DB but invisible to agents. The consolidator solves this:

- **Trigger:** post-turn background task fires when `total_messages > 20` (first run) or `≥15 messages since last_consolidated_at` (subsequent)
- **Model:** gpt-4o-mini (cheap, ~\$0.0003 / call)
- **Output:** updated `user.notes` containing extracted insights (health issues, emotional state, product reactions, personal details)
- **Failure mode:** silent — never crashes the server. Logs warning + skips.
- **State:** `last_consolidated_at` lives in `user.temp_state` to avoid re-summarising the same messages.

Next time the user returns, `notes` is loaded with the rest of the User snapshot → Planner / Writer see the long-term memory.

### 3.9 Broadcaster (`src/broadcaster/`)

Proactive outreach — 10 channels, all sharing one 6h asyncio loop in `scheduler.py`. Per-user weekly cap enforced via `user_broadcasts` table (`get_broadcast_count_this_week`).

| Channel | Frequency | Trigger | Composer |
|---------|-----------|---------|----------|
| Weather care | event-driven | heatwave / cold front detected | `weather_service.py` + `composer.py` |
| Solar terms (節氣) | per 節氣 (24/yr) | calendar | `solar_terms.py` |
| Constitution recheck | quarterly | user went quiet 90 days | `composer.py` |
| Purchase follow-up | one-shot per purchase | 3 days post-buy | `composer.py` |
| Weekly tea (DIY 茶飲) | weekly | by constitution | `composer.py` |
| Weekly acupressure | weekly | by health-tag | `composer.py` |
| Appointment prep | 48h before appt | upcoming confirmed | `composer.py` |
| Monthly food therapy | monthly | by month + constitution | `composer.py` |
| Weekly sleep tip | weekly | by constitution | `composer.py` |
| 月事陪伴 (menstrual care) | weekly | `last_period_start` set | `menstrual_care.py` |

All gated by `_within_send_window()` (HKT 09:00-21:00) and `is_blocked(phone)`.

### 3.10 Social Channels — Instagram / Facebook (`src/channels/`) — ✅ THE LIVE PRODUCT

Two personas share this surface: **Chloe/陳芷晴** (`chloechan.cccc`, IG id `17841424706900394`, Cantonese, default agent) and **Jackie** (`jackiechan.tcm`, IG id `17841417304649448`, English). `src/channels/meta_webhook.py` is the shared core (verify → parse → dedup → dispatch) behind thin `instagram.py`/`facebook.py` routers.

**Comments → DM (canned-first, live, working):**
`comment_rules.py` matches a keyword substring in a comment against `data/channels/comment_responses.json` (array format — same keyword can exist twice, once per account/language, gated by `_ACCOUNT_LANGUAGE`). A match → `send_private_reply` (the DM) + optional public ack on the thread. No LLM call unless a rule sets `"use_agent": true` (none do today — that path exists but is effectively untested against real traffic, see gotcha below). **No rule match = silent, by design** — never auto-DMs a stranger just because they commented.

**DM replies (two parallel systems — know which one is live):**
- **`ChloeAgent`** (`chloe_agent.py`) — the ONLY thing actually serving live DM traffic today. One LLM call per turn: persona JSON (`data/personas/{jackie,chloe}.json`) system prompt + last 16 CRM messages, no knowledge-base grounding. Greeting-first (keyed off "does the CRM row exist," not history-empty — a persist hiccup reading empty history must never cause a repeat greeting).
- **Profile-pipeline path** (`src/personas/profile.py` + the shared `JessicaPipeline`, Planner→Specialists→Writer, KB-grounded) — built 2026-07-01/02, functionally correct (verified via `scripts/persona_dry_run_social.py`), but **dormant in production** unless an account id is in the `SOCIAL_PIPELINE_ACCOUNTS` env var. On ANY exception it falls back to `ChloeAgent` automatically — the fallback net is real, tested (`tests/test_dispatch_dm_profile_pipeline.py`), don't remove it when extending this path.

**Notion → keyword auto-sync:** `POST /admin/notion-sync` (shared secret `X-Sync-Secret` header) reads Production Tracker directly (stdlib only, no import from `ai-tcm-ip` — separate repo/deploy), drafts a keyword rule the moment a row's `Stage` flips to `✅ Published`, writes straight to `comment_responses.json` (takes effect immediately, no redeploy — `comment_rules.load_rules()` reloads on file mtime) and best-effort pushes to git for durability (`GITHUB_PUSH_TOKEN`). `src/notion_sync.py`. Idempotent via `data/channels/notion_sync_state.json`.

**Backfilling missed comments** (webhooks never replay history): `scripts/backfill_comments.py` (local, `pipeline=None`) is safe ONLY for one-shot canned rules with no expected follow-up — see gotcha below. `POST /admin/backfill-comments` runs the same logic inside the live process against the real production CRM — use this for anything conversational.

---

## 4. Data

```
data/
├── knowledge_base/        # Read-only TCM education content
│   ├── soups/             # 食療湯水 cards
│   ├── constitution/      # 九體質 + 氣虛/濕熱/etc.
│   ├── faq/               # acupressure, beauty, digestion, etc.
│   └── MANIFEST.md
├── products/              # Paid catalog (心宜中醫)
│   ├── soups/             # 10 paid soups
│   ├── ointments/         # 3 paid ointments
│   ├── product_catalog.json
│   └── PRODUCTS_INDEX.md
├── clinics/
│   └── clinics.json       # 心宜中醫 branches: name, address, district, hours, phone
└── media/
    ├── greetings/         # Greeting/intro media
    └── products/          # Product photos (referenced by product cards)
```

Card schema (knowledge_base + products) follows `dr-baba-agent` convention: `metadata`, `overview`, `core_content`, `execution_logic`, `references`. **Do not invent a new schema** — we want to keep card portability with Dr. Baba so content edits can flow between projects.

---

## 5. Observability (Critical — This Is Why The Project Exists)

Every turn produces a **trace bundle** stored at `traces/<date>/<user_id>/<turn_id>.json`:

```json
{
  "turn_id": "...",
  "user_id": "...",
  "received_at": "...",
  "user_message": "...",
  "merged_from_fragments": ["msg_id_1", "msg_id_2"],
  "crm_snapshot": { ... },
  "planner": {
    "input_tokens": N, "output_tokens": N, "latency_ms": N,
    "decision": { "specialists": [...], "reasoning": "..." }
  },
  "specialists": [
    {
      "name": "constitution_agent",
      "input": { ... },
      "tools_called": [{ "name": "...", "args": {...}, "result": {...} }],
      "cards_read": ["tcm_constitution_assessment", ...],
      "output": { ... },
      "tokens": {...}, "latency_ms": N
    }
  ],
  "writer": {
    "input": { ... },
    "output_bubbles": ["...", "...", "..."],
    "tokens": {...}, "latency_ms": N
  },
  "send_log": [{ "bubble_idx": 0, "sent_at": "...", "wa_message_id": "..." }],
  "crm_diff": { "before": {...}, "after": {...} }
}
```

Also expose a **live trace viewer** (simple FastAPI + HTML) at `/trace/<turn_id>` so we can debug a single conversation without grepping JSON.

**If a feature breaks the trace format, fix the feature, not the trace.**

---

## 6. Stack

- **Language:** Python 3.11+ (3.14 in production via Render)
- **Web/API:** FastAPI (webhook + trace viewer + admin views)
- **LLM:** **gpt-5.4-mini** via OpenAI for all roles (Planner / Writer /
  Specialists / Vision). Migrated from gpt-4o-mini on 2026-05-26 (forced
  by deprecation deadline; gpt-5.4-mini is ~60% cheaper too). `src/llm.py`
  is an Anthropic-shaped facade — `LLMClient` wraps `AsyncOpenAI` so agents
  use `client.messages.create(...)` unchanged. `_uses_max_completion_tokens()`
  routes gpt-5.x / o-series to the new `max_completion_tokens` parameter
  (gpt-5 family rejects `max_tokens`).
- **Voice transcribe (STT):** `gpt-4o-transcribe` (migrated from
  `gpt-4o-mini-transcribe` which retired 2026-06-01).
- **Voice output (TTS):** **MiniMax T2A** (`speech-2.8-hd`) with native
  HK Cantonese voice `Cantonese_KindWoman` (matches 心宜中醫 brand).
  Lives in `src/media/tts.py` (ported + simplified from
  `dr-baba-agent/src/media_output/tts.py` — keep ONLY the MiniMax
  provider; do NOT re-add Azure / OpenAI / ElevenLabs unless you have
  a reason). Trigger model is **match modality**: voice-reply fires
  ONLY when the inbound turn included a voice note (`transcript != ""`
  in `router._process_turn`). Cached on disk as
  `data/media/tts/<sha16>.mp3`, served via the existing
  `/media` StaticFiles mount; absolute URL requires `JESSICA_BASE_URL`
  env var (otherwise ChatDaddy can't fetch the audio).
- **DB:** PostgreSQL in production (Render free, 1GB, persistent — **free
  tier expires 90 days after creation; current expiry 2026-06-20**).
  SQLite for local dev. Dispatched by `repo_factory.py` based on `DATABASE_URL`.
- **Vector search:** pgvector (Postgres extension) — indexed on startup if
  `DATABASE_URL` is Postgres. Hybrid KB search via `tools/vector_store.py`.
- **Schema migrations:** `CREATE TABLE IF NOT EXISTS` only creates new
  tables — does NOT add new columns to existing ones. To add a column:
  (1) extend the `User` model, (2) add to `_USER_COLUMN_MIGRATIONS` in
  `src/crm/repo.py`, (3) add to `_PG_USER_COLUMN_MIGRATIONS` in
  `src/crm/repo_pg.py`, (4) add to `EXPECTED_NEW_COLUMNS` in
  `tests/test_schema_migrations.py`. Step (4) is a forcing function that
  goes red if any of (1)-(3) is missed. **For Postgres, do NOT use
  `ALTER TABLE ADD COLUMN IF NOT EXISTS` — asyncpg 0.31 + Python 3.14
  hits a protocol bug. Use `information_schema` lookup + conditional ADD
  (see `_migrate_pg_user_columns`).**
- **Deployment:** Render (Singapore region, web Starter + Postgres free).
  **Auto-deploy webhook is currently broken** — push to main does not
  trigger deploy. Workaround: `POST /v1/services/{id}/deploys` via Render
  API. See `docs/DEPLOYMENT.md`.
- **Test:** pytest (758 passing + 2 skipped as of 2026-07-03).

---

## 7. Commands

```bash
# Install
pip install -e .

# Run dev server
uvicorn src.web:app --reload --port 8000

# Run tests
pytest -q                                          # all (523 tests)
pytest tests/test_planner_rules.py -v              # one file
pytest tests/test_schema_migrations.py -v          # migration-path tests

# Run end-to-end persona dry-run (20-turn dialogue, ~$0.50 OpenAI cost)
python3 scripts/persona_dry_run.py                 # full 20 turns
python3 scripts/persona_dry_run.py --short         # first 5 turns only

# Targeted QA harnesses (each ~$1 OpenAI)
python3 scripts/qa_sales_flow.py                   # 6 sales scenarios
python3 scripts/qa_constitution_flow.py            # 5 constitution scenarios
python3 scripts/qa_conversation_flow.py            # 8 conversation scenarios

# Manually trigger Render deploy (workaround for broken webhook)
curl -s -X POST -H "Authorization: Bearer $RENDER_API_KEY" \
  "https://api.render.com/v1/services/srv-d879lsmq1p3s73av6f80/deploys" -d '{}'

# Reset a test user (wipes all CRM data for one phone)
python -c "import asyncio; from src.crm.repo import CRMRepo; \
  asyncio.run((lambda r: r.delete_all_for_phone('+85291234567'))(await CRMRepo.connect('data/jessica.db')))"
```

---

## 8. Agent-First Policy

Same hard triggers as `~/.claude/rules/common/agents.md`. Additionally for this project:

| Task | Required Agent |
|------|----------------|
| Designing the Planner routing logic | **architect** before code |
| Writing a new specialist agent | **planner** → **tdd-guide** (tests first) → **code-reviewer** |
| Touching the trace schema | **architect** (load-bearing — affects every turn) |
| Card schema changes in `data/` | **planner** + **code-reviewer** |
| WhatsApp send/auth changes | **security-reviewer** |
| Constitution Agent vision prompts | **architect** (model behavior is fragile) |
| Build / type errors | **build-error-resolver** immediately |

**Exception:** single content edit in one knowledge card JSON — direct edit is correct.

---

## 9. Migration Notes (from dr-baba-agent)

| Component | Status | Notes |
|-----------|--------|-------|
| ChatDaddy WhatsApp client | **Port as-is** | Already battle-tested. Keep bubble timing, auth refresh, polling fallback. |
| Buffer / merge | **Port as-is** | Already proven. |
| TCM knowledge cards | **Copy and freeze** | Card content is good. Re-index/restructure only if FAQ retrieval underperforms. |
| Paid product cards | **Copy and freeze** | 10 soups + 3 ointments from 心宜中醫. |
| Old sales state machine (`src/sales/flow_engine.py`, `pitch_router.py`, etc.) | **Reference only** | New Planner+Specialist architecture replaces the state machine. Keep in `src/sales_legacy/` to mine for prompt language, pitch angles, intent detection rules. |
| `sales_prompt.py` (Jessica voice) | **Mine for tone** | Excellent HK Canto voice work — port lines into `writer_agent.py` and `greeting_agent.py` prompts. |
| Dr. Baba retrieval pipeline | **Do not port** | Built for a 3,800-card medical KB with high accuracy needs. Jessica's ~30 cards don't need vector search at MVP. |
| CRM | **Build fresh** | Dr. Baba uses ad-hoc patient memory. Jessica needs structured CRM (see §3.3). |
| Observability/trace | **Build fresh** | Dr. Baba's logging is line-based and tenant-mixed. Jessica needs per-turn structured bundles. |

---

## 10. What Not To Do

- Do not import `from dr-baba-agent.*` — projects are independent.
- Do not let a Specialist write user-facing text. Specialists return structured data; Writer composes.
- Do not let the Planner skip the Writer. Even for a one-word "ok" the Writer normalizes the bubble.
- Do not hardcode product names, soup names, clinic addresses, or 體質 logic in Python — they live in `data/`.
- Do not hardcode KB content in Python (e.g. acupoint → symptom mappings).
  KB cards + `AcupointImageMap` own that. We tried and ripped it out on
  2026-05-26 — Python copies of KB drift out of sync with clinic edits.
- Do not bloat the Planner prompt with specialist-specific instructions. Specialists own their own prompts.
- Do not add a 6th specialist without explicit approval. The orchestration cost grows non-linearly.
- Do not add a new column to `User` model without updating
  `_USER_COLUMN_MIGRATIONS` (SQLite) + `_PG_USER_COLUMN_MIGRATIONS` (PG)
  + `EXPECTED_NEW_COLUMNS` (test). `CREATE TABLE IF NOT EXISTS` is a
  trap — existing tables are NOT modified. Caused a prod-down on 2026-05-26.
- Do not use `ALTER TABLE ADD COLUMN IF NOT EXISTS` on Postgres via
  asyncpg 0.31 + Python 3.14 — protocol bug. Use information_schema
  lookup + conditional ADD instead.
- Do not pass `max_tokens` to gpt-5.x / o-series — they require
  `max_completion_tokens`. `_uses_max_completion_tokens()` in `src/llm.py`
  handles this; new direct OpenAI calls should use the facade.
- Do not voice-reply unsolicited. The match-modality trigger in
  `_send_bubbles` only fires when `inbound_was_voice=True`. If you add
  an opt-in voice flag to CRM later, gate it on user consent — sending
  unexpected audio to text-typing users is jarring and burns credits.
- Do not re-add Azure / OpenAI / ElevenLabs TTS providers without a
  reason. We deliberately ship only MiniMax to keep the ops surface
  small. The dr-baba multi-provider abstraction is over-engineered for
  Jessica's single-voice brand identity.
- Do not put raw `{...}` JSON / dict examples in a system-prompt
  template that gets passed through `str.format()` — `str.format()` will
  read the inner content as a `{key}` placeholder and `KeyError` the
  whole reply pipeline. Use `{{...}}` to emit literal braces. Caused a
  prod-down on 2026-05-29 (commit `bd09d9f` added an `inferred_patterns`
  JSON example without escaping). `tests/test_prompt_template_render.py`
  is the forcing function — it actually calls every prompt builder and
  fails if `.format()` raises.
- Do not skip running `scripts/persona_dry_run.py` after any change to
  the Planner, Writer, or a Specialist prompt. The dry-run found 4
  bugs in the same day that unit tests had passed — it tests against
  real LLM, with realistic conversation state.
- **Do not give `IG_ENABLED` / `FB_ENABLED` a literal `value:` in
  `render.yaml` — they MUST be `sync: false`.** `instagram.py`/`facebook.py`
  read this env var fresh on every webhook POST; when falsy it returns
  `{"status":"disabled"}, 200` (so Meta doesn't disable the subscription)
  and processes NOTHING — no error anywhere, comments/DMs just vanish
  silently. A hardcoded `value:` gets re-applied by Render's blueprint
  sync on every deploy, silently overwriting whatever was set in the
  dashboard. This caused a real multi-day outage (2026-07-01/02) — 5
  deploys in one day kept resetting it back to disabled. To check the
  LIVE state without dashboard access: POST a correctly-signed synthetic
  webhook event and read the response `status` field directly
  (`"disabled"` vs `"queued"`) — don't infer from git history or guess.
- Do not run `scripts/backfill_comments.py` (local) for any comment
  where a conversational follow-up is expected (numbered options, "reply
  here"). It runs with `pipeline=None` — even if you wire a real
  pipeline in, running it LOCALLY still writes to local SQLite, never
  the production Postgres the live app actually reads. A user's next
  reply then arrives with zero context. 2026-07-01 incident: David
  replied "1" to a migraine-type DM sent via this script; `ChloeAgent`
  had no memory it was ever sent, replied "did your message get cut
  off?". Use `POST /admin/backfill-comments` (real CRM) for anything
  conversational; the local script is for one-shot canned rules only.
- Meta's private-reply-to-comment API allows roughly ONE reply per
  comment. Re-running `backfill_comments.py` against already-replied
  comments returns generic `HTTP 500 OAuthException "unknown error"` —
  this is expected and harmless (Meta's way of saying "already done"),
  not a sign the token or integration is broken. Verify via `GET
  /{comment_id}/replies`, not by re-sending.
- `notion_sync.py`'s keyword-rule drafting is mechanical templating, not
  translation — it wraps whatever raw text sits in the Notion "First DM"
  code block into the target persona's greeting/closing template without
  checking the source text's actual language. If a Content Library entry
  was authored in English but routed to Chloe (Cantonese), the drafted
  rule comes out Cantonese-greeting-wrapped-around-English-middle. Spot
  check every auto-drafted non-English-source rule before it ships.
