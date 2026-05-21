# Jessica Migration Notes — From dr-baba-agent to TCM-Jessica

**Date:** 2026-05-21
**Source:** `/Users/shivonne/Claude Code/dr-baba-agent/`
**Destination:** `/Users/shivonne/Claude Code/TCM-Jessica/`
**Goal:** Document what the legacy Jessica sales flow does, what should be reused in the new Planner → Specialists → Writer architecture, and what should be left behind.

---

## 1. What the legacy sales flow does

### 1.1 High-level architecture (current — state machine + LLM hybrid)

The original implementation went through two generations:

1. **v1 — Pure state machine** (`flow_engine.py`, ~660 lines). YAML-defined steps (`configs/tcm-sales-flow.yaml`) executed sequentially by `advance(state, user_msg) -> SalesTurnResult`. Each step had `action`, `await`, `next` fields. The engine was pure (no I/O), returning `ReplyBubble` lists + `state_patch` dicts for the caller (WhatsApp router) to dispatch and persist.
2. **v2 — LLM agent + tools** (`sales_prompt.py`, ~34kB; tools in `src/tools/sales.py` in the source repo). When `sales_agent_v2` is enabled, the system prompt is REPLACED with a Jessica-mode prompt (~1.5k tokens) that drives a 13-step journey via 8 named tools (`record_complaint`, `request_tongue_photo`, `analyze_tongue`, `ask_constitution_question`, `record_q_answer`, `declare_constitution`, `suggest_treatments`, `share_product`, `share_paid_items`, `match_clinic`, `propose_booking_slot`, `confirm_booking`). The LLM decides which tool to call next based on `sales_state`.

### 1.2 The 13-step journey (sales_prompt.py `_JOURNEY_STEPS`)

| # | Step | Mechanism |
|---|------|-----------|
| 1 | 了解主訴 (complaint) | `record_complaint` |
| 2 | 要求望脷相 (REQUIRED) | `request_tongue_photo` — directly after complaint |
| 3 | 分析脷相 (skippable if no photo) | `analyze_tongue` |
| 4–8 | 5-question constitution quiz (Q1 fatigue, Q2 thermal, Q3 sleep, Q4 digestion, Q5 emotion) | `ask_constitution_question(n)` + `record_q_answer(n, letter, elaboration)` |
| 9a | 宣布體質 | `declare_constitution` + `share_diagnosis` |
| 9b | 主動推薦療程 | `suggest_treatments` |
| 9c | 介紹產品 (1 caring turn after) | `share_product` (Maca) or `share_paid_items` (catalog) |
| 10 | 主動邀請面診 (1–2 turns after pitch) | (LLM speaks directly; no tool) |
| 11 | 問地區 + 配對 clinic | `match_clinic` |
| 12 | Propose booking slot | `propose_booking_slot` |
| 13 | Confirm booking | `confirm_booking` |

### 1.3 Pitch router logic (`pitch_router.py`)

Deterministic keyword classifier that decides ONE pitch path per session:

- **catalog** — 心宜中醫 paid soups + ointments (skin / digestion / sleep / cough / headache / eye / immunity / beauty / hormonal)
- **maca** — Maca legacy product (energy / 性 / kidney yang / general wellness)
- **unclear** — neither matches; LLM defaults to catalog

Output is a `PitchDecision` rendered as a prompt hint (`💡 PITCH PATH HINT: ...`) — strong nudge, not hard force. Cross-rejection in `share_product` / `share_paid_items` enforces "one pitch per session."

### 1.4 Prompt structure (`sales_prompt.py`)

The legacy prompt is constructed dynamically per turn:

1. **Identity block** — doctor name, clinic brand, Cantonese 口語 rules, "I am Jessica" framing.
2. **Journey progress** — bullet list of `done_steps[]` vs `pending_steps[]` derived from `sales_state` via `_journey_progress()`.
3. **Tool guidance** — which tool maps to which step, ordering hints (e.g. "tongue request comes RIGHT after complaint").
4. **Pacing rules** — `pacing.py` enforces a "1 caring turn between diagnosis and pitch."
5. **Pitch hint injection** — output of `pitch_router.classify()`.
6. **Intro dedup** — `intro_dedup.py` prevents re-greeting on every turn.
7. **Escape handling** — keyword list (`不要`, `跳過`, `stop`, etc.) → `flow_type='qna'`.

### 1.5 State persistence (`state.py`)

Per-patient `sales_state` JSON in `patients.journey.sales_state`. Schema-whitelisted (`_ALLOWED_KEYS`) so typos can't create phantom fields. Per-user locks serialise read→mutate→write to prevent TOCTOU clobbering on bursty WhatsApp input. All mutations return new dicts (immutable).

---

## 2. Re-usable patterns (PORT to new architecture)

These ideas survive the architectural transition and should inform the Planner → Specialists → Writer design:

### 2.1 ✅ Clinic data + district adjacency table
**File:** `configs/tcm-sales-flow.yaml` lines 344–440 → extracted into `data/clinics/clinics.json`.
**Why reusable:** Pure data, no logic. The 2-branch routing heuristic (沙田 covers East Rail + 九龍 + 港島; 馬鞍山 covers Tuen Ma east + 西貢 / 將軍澳) is real-world knowledge captured from `careplustcm.com/location`. The new `match_clinic` specialist should read this JSON directly.

### 2.2 ✅ Pitch path classifier (catalog vs maca vs unclear)
**File:** `pitch_router.py`.
**Why reusable:** Deterministic keyword routing is the right choice for "which product family to pitch" — far cheaper and more predictable than an LLM call for every turn. In the new architecture this becomes a **Specialist Tool** the Planner consults early. Keep the "one pitch path per session" cross-rejection rule.

### 2.3 ✅ Immutable state with schema whitelist + per-user locks
**File:** `state.py` (the `_ALLOWED_KEYS` frozenset + `_user_locks` pattern).
**Why reusable:** Prevents silent typos and TOCTOU bugs from bursty messages. The new Planner needs the same protections — Planner output (next action + state delta) should pass through a whitelisted validator before persistence.

### Honourable mentions

- **Escape keyword list** — small Chinese + English vocabulary for "user wants out." Move to a shared `escape_classifier.py`.
- **District adjacency JSON** (now in `clinics.json`) — the new `match_clinic` specialist can use it as-is.
- **Constitution Q1–Q5 wording** — already battle-tested with users; copy the questions verbatim into the new Constitution Specialist.

---

## 3. Top 3 things NOT to port (OBSOLETE)

### 3.1 ❌ The YAML state-machine engine (`flow_engine.py` + `tcm-sales-flow.yaml` steps)
**Why:** This is exactly what the Planner → Specialists → Writer architecture replaces. The state machine couples step ORDER with step LOGIC and forces every conversation through the same 13-step rail. Real users branch (escape, ask FAQs mid-flow, repeat questions, send tongue photo unprompted). The v1 engine accumulated retry counters, unclear-retry escapes, and mid-flow FAQ counters — all band-aids for "the state machine doesn't fit the conversation." The Planner replaces this with intent-driven dispatch.

### 3.2 ❌ The 34 kB `sales_prompt.py` mega-prompt
**Why:** Even after the v2 rewrite trimmed to "~1.5k tokens," the file is 34 kB because it dynamically reconstructs identity + journey progress + tool guidance + pacing + pitch hint + intro dedup on every turn. This violates the new architecture's separation of concerns:
- Identity / persona → Writer's static system prompt
- Journey progress → Planner's input (structured, not prose)
- Tool guidance → Each Specialist's own prompt
- Pacing / dedup → Orchestrator-level concerns, not prompt-injected

Inlining all of this into one prompt is what made it 15–18k tokens in the dr-baba-agent legacy and blew past the 5k budget (CLAUDE.md §7.3).

### 3.3 ❌ Hard-coded "1 caring turn between diagnosis and pitch" pacing (`pacing.py`)
**Why:** `pacing.py` enforces narrative beats with turn counters (`turns_since_diagnosis >= 1` before allowing `share_product`). This is the wrong layer — it's the LLM's job to know "I just shared a sad result, don't pivot to selling in the same breath." Encoding it as a turn counter creates rigid pauses that feel robotic when the user is already asking "what should I buy?" The new Writer Specialist should handle tone-pacing in its system prompt ("never pitch in the same message as a diagnosis") and let the Planner decide whether the next move is pitch or caring response based on user signal, not turn count.

### Honourable mention

- **`intro_dedup.py`** — its job (don't re-greet) is solved structurally in the new architecture: the Writer's system prompt contains the greeting only on `state.turn == 0`. No runtime dedup logic needed.
- **`intent_yield.py`** — mid-flow FAQ counter exists because the v1 state machine treated FAQs as interruptions. In the new architecture, Q&A is just another Specialist the Planner can call any time.

---

## 4. File inventory (what was copied)

| Source | Destination | Status |
|--------|-------------|--------|
| `configs/tcm-wellness.yaml` | `configs/jessica.yaml` | Renamed |
| `configs/tcm-sales-flow.yaml` | `configs/tcm-sales-flow.yaml` | Copy |
| `src/sales/sales_prompt.py` | `src/sales_legacy/sales_prompt.py` | Reference |
| `src/sales/pitch_router.py` | `src/sales_legacy/pitch_router.py` | Reference (port logic) |
| `src/sales/flow_engine.py` | `src/sales_legacy/flow_engine.py` | Reference (do not port) |
| `src/sales/intent_yield.py` | `src/sales_legacy/intent_yield.py` | Reference (obsolete) |
| `src/sales/pacing.py` | `src/sales_legacy/pacing.py` | Reference (obsolete) |
| `src/sales/state.py` | `src/sales_legacy/state.py` | Reference (port whitelist + locks) |
| `src/sales/intro_dedup.py` | `src/sales_legacy/intro_dedup.py` | Reference (obsolete) |
| `src/sales/config_loader.py` | `src/sales_legacy/config_loader.py` | Reference |
| `src/sales/__init__.py` | `src/sales_legacy/__init__.py` | Reference |
| `docs/plans/jessica-product-sales-flow.md` | `docs/legacy/jessica-product-sales-flow.md` | Read-only |
| `docs/plans/tcm-jessica-flow-map.md` | `docs/legacy/tcm-jessica-flow-map.md` | Read-only |
| `docs/jessica-tcm-anatomy.html` | `docs/legacy/jessica-tcm-anatomy.html` | Visual reference |
| `docs/tcm-jessica-flow-map.html` | `docs/legacy/tcm-jessica-flow-map.html` | Visual reference |
| `docs/tcm-agent-path-flow.html` | `docs/legacy/tcm-agent-path-flow.html` | Visual reference |
| (extracted) | `data/clinics/clinics.json` | NEW — single source of truth for 心宜中醫 clinic data |

NOTE: The originals in `dr-baba-agent` are untouched (used `cp`, not `mv`).
