"""Pure state machine for the TCM Sales flow.

advance(state, user_msg, media, config) -> SalesTurnResult

The engine is deliberately *pure*:
  - Reads state as an immutable snapshot (dict treated as read-only)
  - Performs NO network I/O, NO persistence, NO logging side effects
  - Returns a SalesTurnResult describing what the caller should do next

The caller (router) is responsible for:
  - Persisting state_patch via src.sales.state.set_fields
  - Dispatching each ReplyBubble via whatsapp.client.send_message
  - Marking flow_type=qna on escape so future turns bypass the flow

Step execution model
--------------------
Every step has an `action` (send_text, send_image, analyze_tongue, ...) and
optionally an `await` field declaring what user input it expects.

On each incoming message the engine:
  1. Checks for escape keywords — bails out to QnA if found
  2. If state.awaiting_input is True: processes the user's reply against
     the current step's await spec, records the extracted value, advances
     to the step's `next`
  3. Chains forward: executes each step's action (emitting a ReplyBubble)
     and advances until it reaches an await-step; that step's prompt is
     emitted and the loop stops (awaiting_input = True)

Unknown / invalid input on an await step yields a retry bubble. After
_MAX_UNCLEAR_RETRIES consecutive retries the engine escapes to QnA so
the user is never permanently stuck.

Stubs for later commits
-----------------------
analyze_tongue, declare_constitution, match_clinic, propose_booking all
use placeholder logic here (commit 2). Later commits (4-6) replace these
with real vision, matcher, and scheduler implementations — the engine
contract does not change.
"""
from __future__ import annotations

import datetime as _dt
import re
from dataclasses import dataclass, field
from typing import Any, Mapping

from src.sales.config_loader import Clinic, ConstitutionType, FlowStep, SalesConfig
from src.sales.timezone import hk_today

# ── Tunables ──────────────────────────────────────────────────────────

# After this many consecutive unclear inputs on an await step, give up and
# escape to QnA rather than looping forever.
_MAX_UNCLEAR_RETRIES = 3

# ── Result types ──────────────────────────────────────────────────────


@dataclass(frozen=True)
class ReplyBubble:
    """A single outbound message — text and/or one attachment.

    Keeping this immutable (frozen dataclass + tuple) means the router
    can safely log / replay bubbles without worrying about later mutation.
    """
    text: str = ""
    attachments: tuple[dict, ...] = ()


@dataclass(frozen=True)
class SalesTurnResult:
    """Everything the caller needs to execute one sales turn.

    Attributes:
        bubbles:        Messages to send, in order.
        state_patch:    Mapping of sales_state fields to update. Caller
                        merges via set_fields (schema-whitelisted).
        done:           Flow complete (save_booking emitted OR escaped).
        escape_to_qna:  User requested to leave the funnel; caller should
                        mark flow_type='qna' so future messages bypass.
        executed_steps: Step ids executed this turn (debug / test assertions).
    """
    bubbles: tuple[ReplyBubble, ...] = ()
    state_patch: Mapping[str, Any] = field(default_factory=dict)
    done: bool = False
    escape_to_qna: bool = False
    executed_steps: tuple[str, ...] = ()


# ── Public entry point ────────────────────────────────────────────────


def advance(
    *,
    state: Mapping[str, Any],
    user_msg: str,
    media: list[dict] | None,
    config: SalesConfig,
) -> SalesTurnResult:
    """Advance the Sales flow by one user turn.

    Pure function — does not mutate `state`, does not perform I/O.
    """
    media = list(media or [])
    text = (user_msg or "").strip()

    # Escape keyword — user wants out of the funnel.
    if _is_escape_keyword(text, config):
        return _escape_to_qna(config)

    # Initial entry — no prior state OR no current_step set yet.
    current_step_id = state.get("current_step") if state else None
    if not current_step_id:
        return _chain_forward_from("step_1_greeting", state, media, config)

    step = config.step_by_id(current_step_id)
    if step is None:
        # Corrupted state (step id removed from YAML) — reset to start.
        return _chain_forward_from("step_1_greeting", state, media, config)

    if state.get("awaiting_input"):
        return _process_input(step, state, text, media, config)

    # Not awaiting — resume chaining from current step.
    # This path handles the case where init_sales_state set current_step
    # to step_1 but advance() is called for the first time.
    return _chain_forward_from(current_step_id, state, media, config)


# ── Chain-forward: run non-await steps until we hit an await ─────────


def _chain_forward_from(
    start_step_id: str,
    state: Mapping[str, Any],
    media: list[dict],
    config: SalesConfig,
) -> SalesTurnResult:
    """Execute steps starting at start_step_id. Chain through non-await
    steps; stop (emit prompt, set awaiting_input) on the first await step.
    """
    bubbles: list[ReplyBubble] = []
    executed: list[str] = []
    patch: dict[str, Any] = {"flow_type": "sales"}

    # Local scratch state so template interpolation sees patch-in-progress.
    scratch: dict[str, Any] = {**state, **patch}

    next_id: str | None = start_step_id
    done = False

    while next_id is not None:
        step = config.step_by_id(next_id)
        if step is None:
            break
        executed.append(step.id)

        bubble, action_patch = _execute_action(step, scratch, media, config)
        if bubble is not None:
            bubbles.append(bubble)
        if action_patch:
            patch.update(action_patch)
            scratch.update(action_patch)

        if step.await_type:
            # Sent the prompt — now wait for user input.
            patch["current_step"] = step.id
            patch["awaiting_input"] = True
            patch["unclear_retries"] = 0
            break

        # Non-await step — advance to next.
        patch["current_step"] = step.id
        patch["awaiting_input"] = False
        next_id = step.next

        if next_id is None:
            # End of flow reached via chain (e.g. save_booking's next is null).
            patch["flow_type"] = "complete"
            patch["awaiting_input"] = False
            done = True

    return SalesTurnResult(
        bubbles=tuple(bubbles),
        state_patch=patch,
        done=done,
        executed_steps=tuple(executed),
    )


# ── Process input on an await step ────────────────────────────────────


def _process_input(
    step: FlowStep,
    state: Mapping[str, Any],
    user_msg: str,
    media: list[dict],
    config: SalesConfig,
) -> SalesTurnResult:
    """Handle a user reply against the current await-step.

    On valid input: record it and chain forward from step.next.
    On invalid input: emit retry bubble, stay on step. After
    _MAX_UNCLEAR_RETRIES, escape to QnA.
    """
    await_type = step.await_type or ""

    if await_type == "image_attachment":
        img_url = _extract_image_url(media)
        if not img_url:
            return _retry(step, state, config, "image_not_received")
        patch_in: dict[str, Any] = {
            "tongue_image_url": img_url,
            "awaiting_input": False,
            "unclear_retries": 0,
        }
        return _after_input(step, state, media, config, patch_in)

    if await_type == "text_answer":
        # Q1 / Q2 — expect A/B/C.
        if step.id in ("step_5_question_1", "step_6_question_2"):
            letter = _extract_abc(user_msg)
            if not letter:
                return _retry(step, state, config, "unclear_answer")
            qkey = "q1" if step.id == "step_5_question_1" else "q2"
            existing = dict(state.get("constitution_answers") or {})
            existing[qkey] = letter
            patch_in = {
                "constitution_answers": existing,
                "awaiting_input": False,
                "unclear_retries": 0,
            }
            return _after_input(step, state, media, config, patch_in)

        # District ask — free-form text.
        if step.id == "close_a_district":
            if not user_msg.strip():
                return _retry(step, state, config, "unclear_answer")
            patch_in = {
                "user_district": user_msg.strip(),
                "awaiting_input": False,
                "unclear_retries": 0,
            }
            return _after_input(step, state, media, config, patch_in)

        # Greeting reply — capture the user's chief complaint so Doctor Hub
        # (and any downstream agent) sees what the user actually said.
        if step.id == "step_1_greeting":
            patch_in = {
                "complaint": user_msg.strip(),
                "awaiting_input": False,
                "unclear_retries": 0,
            }
            return _after_input(step, state, media, config, patch_in)

        # Generic text answer — just advance.
        patch_in = {"awaiting_input": False, "unclear_retries": 0}
        return _after_input(step, state, media, config, patch_in)

    if await_type == "confirmation_or_alternative":
        if _is_confirmation(user_msg):
            patch_in = {"awaiting_input": False, "unclear_retries": 0}
            return _after_input(step, state, media, config, patch_in)
        # STUB: real time-parsing deferred to commit 6. For commit 2 we
        # treat any non-confirmation as "unclear" and retry.
        return _retry(step, state, config, "unclear_answer")

    # Unknown await — treat as auto-advance.
    patch_in = {"awaiting_input": False}
    return _after_input(step, state, media, config, patch_in)


def _after_input(
    step: FlowStep,
    state: Mapping[str, Any],
    media: list[dict],
    config: SalesConfig,
    patch_in: dict[str, Any],
) -> SalesTurnResult:
    """Merge input-patch, then chain forward from step.next."""
    next_id = step.next
    if next_id is None:
        # No next — mark complete.
        final_patch = {**patch_in, "current_step": None, "flow_type": "complete"}
        return SalesTurnResult(
            bubbles=(),
            state_patch=final_patch,
            done=True,
            executed_steps=(step.id,),
        )
    merged_state = {**state, **patch_in}
    onward = _chain_forward_from(next_id, merged_state, media, config)
    combined_patch = {**patch_in, **onward.state_patch}
    return SalesTurnResult(
        bubbles=onward.bubbles,
        state_patch=combined_patch,
        done=onward.done,
        escape_to_qna=onward.escape_to_qna,
        executed_steps=onward.executed_steps,
    )


# ── Retry / escape helpers ────────────────────────────────────────────


def _retry(
    step: FlowStep,
    state: Mapping[str, Any],
    config: SalesConfig,
    fallback_key: str,
) -> SalesTurnResult:
    retries = int(state.get("unclear_retries") or 0) + 1
    if retries >= _MAX_UNCLEAR_RETRIES:
        return _escape_to_qna(config, reason="retries_exhausted")

    msg = step.retry_script or config.fallback.get(
        fallback_key,
        "唔好意思，可以再試多一次？",
    )
    return SalesTurnResult(
        bubbles=(ReplyBubble(text=msg),),
        state_patch={
            "unclear_retries": retries,
            "awaiting_input": True,
            "current_step": step.id,
        },
        executed_steps=(step.id,),
    )


def _escape_to_qna(config: SalesConfig, *, reason: str = "user_keyword") -> SalesTurnResult:
    return SalesTurnResult(
        bubbles=(
            ReplyBubble(text=config.fallback.get("escape_to_qna", "好呀，你想問咩都可以 😊")),
        ),
        state_patch={
            "flow_type": "qna",
            "current_step": None,
            "awaiting_input": False,
            "unclear_retries": 0,
        },
        done=True,
        escape_to_qna=True,
    )


# ── Step action executors ─────────────────────────────────────────────


def _execute_action(
    step: FlowStep,
    state: Mapping[str, Any],
    media: list[dict],
    config: SalesConfig,
) -> tuple[ReplyBubble | None, dict[str, Any]]:
    """Run one step's action. Returns (bubble, state_fragment).

    All real content generation happens here so _chain_forward_from stays
    a plain dispatcher.
    """
    action = step.action

    if action == "send_text":
        text = _render_script(step, state, config)
        # A send_text step can optionally carry an image (e.g. doctor photo
        # bundled with the greeting) so the user sees text + image as one
        # WhatsApp bubble instead of two separate messages.
        attachment = _build_image_attachment(step, config) if step.image_ref else None
        return ReplyBubble(
            text=text,
            attachments=(attachment,) if attachment else (),
        ), {}

    if action == "send_image":
        attachment = _build_image_attachment(step, config)
        caption = step.caption or ""
        caption = _interpolate(caption, state, config) if caption else ""
        return ReplyBubble(
            text=caption,
            attachments=(attachment,) if attachment else (),
        ), {}

    if action == "analyze_tongue":
        # STUB — real vision in commit 4. Placeholder findings.
        findings = {
            "summary": "顏色偏淡，有少少齒痕",
            "signals": ["淡", "齒痕"],
        }
        text = _render_script(
            step,
            {
                **state,
                "tongue_summary": findings["summary"],
                "suspected_signals": "、".join(findings["signals"]),
            },
            config,
        )
        return ReplyBubble(text=text), {"tongue_findings": findings}

    if action == "declare_constitution":
        constitution = _match_constitution_stub(state, config)
        text = _render_script(
            step,
            {
                **state,
                "constitution_zh": constitution.key_zh,
                "constitution_en": constitution.en,
                "characteristics": constitution.characteristics,
            },
            config,
        )
        return ReplyBubble(text=text), {"dominant_constitution": constitution.key_zh}

    if action == "match_clinic":
        clinic = _match_clinic_stub(state, config)
        travel_hint = _travel_hint(state.get("user_district") or "", clinic, config)
        text = _render_script(
            step,
            {
                **state,
                "clinic_name": clinic.name_zh,
                "clinic_brand_en": getattr(clinic, "name_brand_en", "") or "Care Plus TCM",
                "clinic_address": clinic.address,
                "clinic_phone": clinic.phone,
                "clinic_hours": _fmt_hours(clinic.opening_hours),
                "travel_hint": travel_hint,
            },
            config,
        )
        return ReplyBubble(text=text), {"chosen_clinic": clinic.id}

    if action == "propose_booking":
        proposed_date, weekday, proposed_time = _propose_booking_stub(state)
        text = _render_script(
            step,
            {
                **state,
                "proposed_date": proposed_date,
                "weekday": weekday,
                "proposed_time": proposed_time,
            },
            config,
        )
        return ReplyBubble(text=text), {
            "proposed_booking_date": proposed_date,
            "proposed_booking_time": proposed_time,
        }

    if action == "save_booking":
        clinic_id = state.get("chosen_clinic")
        clinic = config.clinic_by_id(clinic_id) if clinic_id else None
        clinic_name = clinic.name_zh if clinic else ""
        clinic_address = clinic.address if clinic else ""
        clinic_phone = clinic.phone if clinic else ""
        proposed_date = state.get("proposed_booking_date", "")
        proposed_time = state.get("proposed_booking_time", "")
        weekday = _weekday_zh(proposed_date)
        text = _render_script(
            step,
            {
                **state,
                "clinic_name": clinic_name,
                "clinic_address": clinic_address,
                "clinic_phone": clinic_phone,
                "proposed_date": proposed_date,
                "weekday": weekday,
                "proposed_time": proposed_time,
            },
            config,
        )
        return ReplyBubble(text=text), {"flow_type": "complete"}

    # Unknown action — skip silently. config_loader has already whitelisted
    # actions at load time so this is unreachable in production.
    return None, {}


# ── STUB implementations (replaced in commits 4-6) ────────────────────


def _match_constitution_stub(
    state: Mapping[str, Any],
    config: SalesConfig,
) -> ConstitutionType:
    """Pick a constitution based on tongue signals, falling back to 氣虛質.

    Real scoring (tongue + q1 + q2 weighted) arrives in commit 5.
    """
    findings = state.get("tongue_findings") or {}
    signals = set(findings.get("signals") or [])
    if signals:
        for constitution in config.constitutions:
            if set(constitution.tongue_signals) & signals:
                return constitution
    fallback = config.constitution_by_key("氣虛質")
    return fallback or config.constitutions[0]


def _match_clinic_stub(state: Mapping[str, Any], config: SalesConfig) -> Clinic:
    """Pick the user's district clinic, else an adjacent clinic, else first.

    Real adjacency walk + travel-time scoring arrives in commit 6.
    With the current YAML there is exactly one clinic (心宜中醫 馬鞍山) so
    everyone lands on it.
    """
    if not config.clinics:
        raise ValueError("clinic_list is empty — cannot match")

    user_district = state.get("user_district") or ""
    # Exact match
    for clinic in config.clinics:
        if clinic.district == user_district:
            return clinic
    # Adjacency walk
    for adj_district in config.district_adjacency.get(user_district, ()):
        for clinic in config.clinics:
            if clinic.district == adj_district:
                return clinic
    # Fallback — first clinic
    return config.clinics[0]


def _travel_hint(user_district: str, clinic: Clinic, config: SalesConfig) -> str:
    """Friendly one-liner about the user's district vs clinic.

    Sales directive (per 2026-04-23): always frame the clinic as near the
    user's home in HK Cantonese 口語, regardless of actual distance. The
    line becomes part of close_b_clinic's bubble to reduce travel-time
    objections before the booking proposal.
    """
    if not user_district:
        return "咁啱啊，好近我哋診所㗎 🌟"
    return f"咁啱啊，{user_district}好近我哋診所㗎 🌟"


def _propose_booking_stub(state: Mapping[str, Any]) -> tuple[str, str, str]:
    """Return (YYYY-MM-DD, weekday_zh, HH:MM) one day after symptom_day.

    Real open-day walk-forward arrives in commit 6. For commit 2 we just
    use symptom_day + 1 day (falls back to today + 1 if no symptom_day).
    """
    sym_day = state.get("symptom_day")
    if sym_day:
        try:
            base = _dt.date.fromisoformat(sym_day)
        except Exception:
            base = hk_today()
    else:
        base = hk_today()
    proposed = base + _dt.timedelta(days=1)
    return proposed.isoformat(), _WEEKDAY_ZH[proposed.weekday()], "10:00"


# ── Input extraction ──────────────────────────────────────────────────


def _extract_image_url(media: list[dict]) -> str | None:
    """Pull the first image URL from a ChatDaddy-shaped attachment list."""
    for att in media:
        att_type = (att.get("type") or "").lower()
        if att_type in ("image", "photo"):
            url = att.get("url") or att.get("mediaUrl") or ""
            if url:
                return url
    # Some payloads omit `type` but carry image/* mime.
    for att in media:
        mime = (att.get("mimetype") or att.get("mime_type") or "").lower()
        if mime.startswith("image/"):
            url = att.get("url") or att.get("mediaUrl") or ""
            if url:
                return url
    return None


_ABC_PATTERN = re.compile(r"(?:^|[^A-Za-z])([ABCabc])(?:[^A-Za-z]|$)")
_CJK_ABC = {"Ａ": "A", "Ｂ": "B", "Ｃ": "C"}


def _extract_abc(text: str) -> str | None:
    """Pull a single A/B/C letter from a free-form reply.

    Accepts: "A", "a", " A.", "我揀 B", "c", full-width "Ａ", etc.
    Rejects text containing none of those (caller retries).
    """
    if not text:
        return None
    normalised = text.strip()
    if not normalised:
        return None
    # Full-width CJK letters
    for cjk, ascii_letter in _CJK_ABC.items():
        if cjk in normalised:
            return ascii_letter
    # Plain ASCII A/B/C surrounded by non-letter boundaries
    m = _ABC_PATTERN.search(f" {normalised} ")
    if m:
        return m.group(1).upper()
    # Very first char is A/B/C (handles bare "A")
    first = normalised[0]
    if first.upper() in ("A", "B", "C"):
        return first.upper()
    return None


_CONFIRMATION_TOKENS = (
    "確認", "確定", "得", "好", "OK", "可以", "係", "ok", "Ok",
)


def _is_confirmation(text: str) -> bool:
    if not text:
        return False
    stripped = text.strip()
    for tok in _CONFIRMATION_TOKENS:
        if tok in stripped:
            return True
    return False


def _is_escape_keyword(text: str, config: SalesConfig) -> bool:
    if not text:
        return False
    stripped = text.strip()
    for kw in config.escape_keywords:
        if kw and kw in stripped:
            return True
    return False


# ── Template interpolation ────────────────────────────────────────────

# Narrow `{var}` interpolation — no format specs, no code eval.
_PLACEHOLDER_RE = re.compile(r"\{([a-zA-Z_][a-zA-Z0-9_]*)\}")


def _render_script(
    step: FlowStep,
    state: Mapping[str, Any],
    config: SalesConfig,
) -> str:
    raw = step.script_template or step.script or step.caption or ""
    return _interpolate(raw, state, config)


def _interpolate(
    template: str,
    state: Mapping[str, Any],
    config: SalesConfig,
) -> str:
    """Replace {var} occurrences. Unknown placeholders are left as-is."""
    if not template:
        return ""

    # Assemble the lookup namespace from config + state + scratch overrides.
    ns: dict[str, Any] = {
        "doctor_name_zh": config.doctor_name_zh,
        "doctor_name_full_zh": getattr(
            config, "doctor_name_full_zh", config.doctor_name_zh,
        ),
        "product_name": config.product.name,
        "product_url": config.product.url,
        "booking_url": getattr(config, "booking_url", ""),
        "clinic_brand_zh": getattr(config, "clinic_brand_zh", "心宜中醫"),
        "clinic_brand_en": getattr(config, "clinic_brand_en", "Care Plus TCM"),
    }
    # State overrides take precedence — lets match_clinic inject clinic_name etc.
    for k, v in state.items():
        if v is None or isinstance(v, (dict, list, tuple)):
            continue
        ns[k] = v

    def _sub(m: re.Match) -> str:
        key = m.group(1)
        val = ns.get(key)
        return str(val) if val is not None else m.group(0)

    return _PLACEHOLDER_RE.sub(_sub, template)


# ── Misc formatting helpers ───────────────────────────────────────────

_WEEKDAY_ORDER = ("mon", "tue", "wed", "thu", "fri", "sat", "sun")
_WEEKDAY_ZH = ("一", "二", "三", "四", "五", "六", "日")


def _weekday_zh(iso_date: str) -> str:
    if not iso_date:
        return ""
    try:
        d = _dt.date.fromisoformat(iso_date)
    except Exception:
        return ""
    return _WEEKDAY_ZH[d.weekday()]


def _fmt_hours(hours: Mapping[str, str]) -> str:
    """Compact human-readable opening hours summary.

    Groups consecutive identical ranges (Mon-Fri 10:00-20:00 / Sat-Sun ...).
    """
    if not hours:
        return "請致電確認"
    # Pull values in mon..sun order.
    values = [(d, hours.get(d, "").strip()) for d in _WEEKDAY_ORDER]

    # Group consecutive days with the same value.
    groups: list[tuple[list[str], str]] = []
    for day, val in values:
        if groups and groups[-1][1] == val:
            groups[-1][0].append(day)
        else:
            groups.append(([day], val))

    day_to_zh = dict(zip(_WEEKDAY_ORDER, _WEEKDAY_ZH))
    parts: list[str] = []
    for days, val in groups:
        if not val or val == "closed":
            continue
        if len(days) == 1:
            parts.append(f"星期{day_to_zh[days[0]]} {val}")
        else:
            parts.append(f"星期{day_to_zh[days[0]]}–{day_to_zh[days[-1]]} {val}")

    return " / ".join(parts) if parts else "請致電確認"


def _build_image_attachment(step: FlowStep, config: SalesConfig) -> dict | None:
    """Build a ChatDaddy-shaped attachment dict for a send_image step."""
    if step.image_ref == "doctor_photo":
        return _image_dict(config.doctor_photo_url)
    if step.image_ref == "product_photo":
        if not config.product.photo_url:
            return None  # Product image optional — no-op if not configured
        return _image_dict(config.product.photo_url)
    return None


def _image_dict(url: str) -> dict:
    """Shape a ChatDaddy image attachment from a URL (relative or absolute)."""
    lower = url.lower()
    if lower.endswith(".png"):
        mime = "image/png"
    elif lower.endswith(".webp"):
        mime = "image/webp"
    else:
        mime = "image/jpeg"
    return {"url": url, "type": "image", "mimetype": mime}
