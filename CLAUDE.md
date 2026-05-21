# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

---

## 1. Project Identity

**TCM-Jessica** is a WhatsApp-native TCM (Traditional Chinese Medicine) wellness sales & care agent for **心宜中醫 (Care Plus)** clinic. Jessica is a warm, gentle, conversational character — *not* a doctor, but a knowledgeable guide who helps users understand their 體質 (constitution), recommends 湯水 (herbal soups) and 藥膏 (ointments), and books clinic appointments.

- Language: **HK Cantonese 口語** only — never 書面語, never Mandarin phrasing.
- Tone: gentle, warm, human, slightly playful. NOT clinical, NOT pushy.
- Customer: HK consumers using WhatsApp, mixed ages, mostly health-curious / lightly symptomatic.
- Sales channel: WhatsApp via ChatDaddy IM API. Order link: `wa.me/85252417448`.

### Why a Standalone Project (and not part of dr-baba-agent)

Jessica was previously embedded inside `dr-baba-agent` as one of 50 tenant configs. We split her out because:

1. **Observability** — inside dr-baba-agent, Jessica's traces are mixed with 47 cancer pipelines. We can't cleanly see: "for this user, which agent fired, which tool ran, which card was read, what the final reply was." This project's #1 architectural goal is **per-turn step-level traceability**.
2. **Different architecture** — Dr. Baba is a single card-driven retrieval pipeline. Jessica is a **multi-agent orchestration** (Planner → Specialists → Writer) with **parallel specialist calls**. Trying to retrofit that into Dr. Baba's pipeline was creating coupling debt.
3. **Independent deployment** — 心宜中醫 should be able to ship Jessica without coordinating with cancer education releases.

What we **share** with `dr-baba-agent` (ported, then evolved independently):
- ChatDaddy WhatsApp client + auth flow + bubble-split logic
- Message buffer / merge logic (combining rapid-fire user messages before responding)
- TCM knowledge base cards (~30 cards: soups, constitution, FAQ)
- Paid product catalog (10 soups + 3 ointments from 心宜中醫)

Reference legacy code in `src/sales_legacy/` and `docs/legacy/` — **do not import from these**, they are read-only references during the rewrite.

---

## 2. Architecture (Big Picture)

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
| `status` | enum | `new` / `qualified` / `constitution_done` / `bought` / `booked` / `churned` |
| `age` | int | asked when relevant |
| `location` / `district` | string | asked at appointment stage |
| `constitution` | enum (9 體質) | set by Constitution Agent |
| `pain_points` | list | extracted from conversation |
| `products_pitched` | list | what Sales Agent has shown |
| `products_purchased` | list | confirmed orders |
| `appointments` | list | booked slots |
| `notes` | text | freeform |
| `conversation_history` | list[message] | rolling window (~20 turns) |
| `tags` | list[string] | custom labels |

Storage: SQLite for MVP (single-tenant, single-clinic). Move to Postgres if 心宜中醫 needs multi-branch / multi-user-admin.

### 3.4 Planner Agent (`src/agents/planner.py`)
- Input: CRM snapshot + buffered user message + last 5 turns of history
- Output: `RoutingPlan { specialists: [Specialist], reasoning: str, parallel: bool }`
- Can route to **1 or 2 specialists in parallel**. Two is the cap (more = too messy for Writer to compose).
- Routing rules live in the planner prompt + a small ruleset (e.g., `media.tongue_photo == True` → must include Constitution Agent).

### 3.5 Specialist Agents (`src/agents/`)

| Agent | Tools | Knowledge | Output Schema |
|-------|-------|-----------|---------------|
| `greeting_agent.py` | none | none | `{ tone: "warm", topic: str, suggested_followup: str? }` |
| `faq_agent.py` | `search_kb`, `read_card` | `data/knowledge_base/` (soups, constitution, faq cards) | `{ answer_facts: list, cards_used: list[card_id], confidence: float }` |
| `sales_agent.py` | `recommend_product`, `share_product_image`, `share_order_link` | `data/products/` | `{ products_to_pitch: list, pitch_angle: str, urgency: enum }` |
| `constitution_agent.py` | `analyze_tongue` (vision), `ask_constitution_question`, `declare_constitution` | `data/knowledge_base/constitution/` | `{ phase: "asking" \| "diagnosing", question?: MCQ, diagnosis?: Constitution, soup_recs?: list }` |
| `appointment_agent.py` | `match_clinic_by_location`, `propose_slot`, `confirm_booking` | `data/clinics/clinics.json` | `{ phase: "asking_location" \| "proposing_slot" \| "confirming", payload: ... }` |

### 3.6 Final Writer Agent (`src/agents/writer.py`)
- Input: CRM context + user message + ALL specialist outputs
- Output: list of bubble messages (target ~150 chars, max 250, see `dr-baba-agent/src/whatsapp/client.py` `BUBBLE_TARGET`)
- Responsible for: tone consistency (Jessica voice), HK 口語 polish, removing redundancy when 2 specialists overlap, inserting media (images) at the right bubble boundaries.
- **NEVER** invents medical/product facts. Only re-narrates what specialists provided.

### 3.7 Orchestrator (`src/orchestrator/`)
The conductor — runs the full pipeline per turn:
1. CRM load
2. Planner call
3. Fan-out specialist calls (sequential or parallel per Planner decision)
4. Writer call
5. CRM write + trace persist
6. Send bubbles via WhatsApp client

Every step emits a structured trace event. See §5.

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

- **Language:** Python 3.11+
- **Web/API:** FastAPI (webhook endpoint + trace viewer)
- **LLM:** Claude (Anthropic API) — Sonnet 4.6 for Planner + Writer, Haiku 4.5 for Specialists (cost optimization, will validate)
- **Vision:** Claude vision for tongue photo analysis
- **DB:** SQLite (MVP), upgrade path to Postgres
- **Vector search:** TBD — start with simple keyword + card metadata filtering. Only add Qdrant if FAQ retrieval quality requires it.
- **Deployment:** TBD (likely Railway or Fly.io, single container)
- **Test:** pytest

---

## 7. Commands

> Project is bootstrapping — these commands will be added as we build. **If a command isn't listed here yet, it doesn't exist yet.**

```bash
# Install (planned)
pip install -e .

# Run dev server (planned)
uvicorn src.web:app --reload --port 8000

# Run tests (planned)
pytest tests/ -v
pytest tests/test_planner.py::test_routes_constitution_when_tongue_photo -v

# Inspect a turn trace (planned)
python scripts/view_trace.py --turn-id <id>

# Reset CRM for a test user (planned)
python scripts/reset_user.py --phone +85291234567
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
- Do not bloat the Planner prompt with specialist-specific instructions. Specialists own their own prompts.
- Do not add a 6th specialist without explicit approval. The orchestration cost grows non-linearly.
