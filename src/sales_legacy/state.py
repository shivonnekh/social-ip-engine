"""Per-patient Sales flow state — lives in patients.journey.sales_state (JSON).

All mutations return new dicts. Never mutate the input patient/journey.
Persistence delegates to patient_store.update_journey (already immutable-safe).

State schema (commit 1 — extends as later commits wire more steps):

    sales_state = {
        "flow_type":                "sales" | "qna" | "booking" | "complete",
        "current_step":             "step_1_greeting" | ... | "close_d_confirmed",
        "tongue_image_url":         str | None,
        "tongue_findings":          dict | None,
        "constitution_answers":     {"q1": "A|B|C", "q2": "A|B|C"},
        "dominant_constitution":    "氣虛質" | ... | None,
        "user_district":            str | None,
        "chosen_clinic":            "careplus_shatin" | ... | None,
        "proposed_booking_date":    "YYYY-MM-DD" | None,
        "proposed_booking_time":    "HH:MM" | None,
        "symptom_day":              "YYYY-MM-DD" | None,
        "unclear_retries":          int,
        "started_at":               int  (unix seconds),
        "last_advance_at":          int  (unix seconds),
    }
"""
from __future__ import annotations

import threading
import time
from typing import Any, Callable

from src.db.patient_store import get_patient, update_journey

_KEY = "sales_state"

# Per-user locks serialise the read→mutate→write sequence so two concurrent
# WhatsApp bursts for the same user_id cannot clobber each other (TOCTOU).
# SQLite-level locking would be cleaner but would require changing
# patient_store.update_journey's contract — not in commit 1 scope.
_user_locks: dict[str, threading.Lock] = {}
_user_locks_guard = threading.Lock()

# Schema whitelist — set_field / set_fields refuse to write keys outside this
# set so a caller typo can't silently create a phantom field.
_ALLOWED_KEYS: frozenset[str] = frozenset({
    "flow_type",
    "current_step",
    "awaiting_input",            # True when current_step has sent its prompt
                                 # and is waiting for the user's reply
    "complaint",                 # Free-text chief complaint from greeting reply
    "tongue_image_url",
    "tongue_findings",
    "constitution_answers",
    "dominant_constitution",
    "user_district",
    "chosen_clinic",
    "proposed_booking_date",
    "proposed_booking_time",
    "symptom_day",
    "unclear_retries",
    "faq_answers_given",         # Count of mid-flow TCM FAQ questions the
                                 # router has answered via the knowledge-card
                                 # interceptor. Used to pivot to booking
                                 # after N rounds (faq_interceptor.py).
    "started_at",
    "last_advance_at",
})


def _get_user_lock(user_id: str) -> threading.Lock:
    """Return (creating if needed) the lock for this user_id."""
    with _user_locks_guard:
        lock = _user_locks.get(user_id)
        if lock is None:
            lock = threading.Lock()
            _user_locks[user_id] = lock
        return lock


# ── Public API ─────────────────────────────────────────────────────────


def get_sales_state(user_id: str) -> dict[str, Any]:
    """Return a copy of the patient's sales_state dict (empty dict if none)."""
    patient = get_patient(user_id)
    journey = patient.get("journey") or {}
    state = journey.get(_KEY)
    return dict(state) if state else {}


def has_sales_state(user_id: str) -> bool:
    """True iff a non-empty sales_state exists on the patient record."""
    return bool(get_sales_state(user_id))


def init_sales_state(
    user_id: str,
    *,
    symptom_day: str | None = None,
    starting_step: str = "step_1_greeting",
) -> dict[str, Any]:
    """Create a fresh sales_state for a new sales-flow session.

    Idempotent: replaces any existing state. Use `clear_sales_state` first
    if you want to ensure no state pre-existed.
    """
    now = int(time.time())
    state: dict[str, Any] = {
        "flow_type": "sales",
        "current_step": starting_step,
        "tongue_image_url": None,
        "tongue_findings": None,
        "constitution_answers": {},
        "dominant_constitution": None,
        "user_district": None,
        "chosen_clinic": None,
        "proposed_booking_date": None,
        "proposed_booking_time": None,
        "symptom_day": symptom_day,
        "unclear_retries": 0,
        "started_at": now,
        "last_advance_at": now,
    }
    with _get_user_lock(user_id):
        _persist(user_id, state)
    return state


def advance_step(user_id: str, next_step: str) -> dict[str, Any]:
    """Return new state with current_step set to next_step."""
    updated = _mutate(user_id, {"current_step": next_step})
    return updated


def record_answer(user_id: str, qkey: str, answer: str) -> dict[str, Any]:
    """Store a constitution question answer (q1, q2, ...) immutably.

    The read of existing answers MUST happen under the lock — otherwise two
    concurrent answers would both read empty, each build a patch with only
    their own key, and the second write would clobber the first.
    """
    def patch_fn(current: dict[str, Any]) -> dict[str, Any]:
        answers = dict(current.get("constitution_answers") or {})
        answers[qkey] = answer
        return {"constitution_answers": answers}

    return _mutate_with(user_id, patch_fn)


def bump_unclear_retry(user_id: str) -> dict[str, Any]:
    """Increment unclear_retries atomically under the lock."""
    def patch_fn(current: dict[str, Any]) -> dict[str, Any]:
        return {"unclear_retries": int(current.get("unclear_retries") or 0) + 1}

    return _mutate_with(user_id, patch_fn)


def set_field(user_id: str, key: str, value: Any) -> dict[str, Any]:
    """Set a single top-level field on sales_state (new dict returned).

    Raises ValueError if `key` is not in the documented schema — prevents
    caller typos from silently creating phantom fields.
    """
    if key not in _ALLOWED_KEYS:
        raise ValueError(
            f"sales_state key {key!r} not in schema. Allowed: {sorted(_ALLOWED_KEYS)}"
        )
    return _mutate(user_id, {key: value})


def set_fields(user_id: str, updates: dict[str, Any]) -> dict[str, Any]:
    """Merge a dict of updates into sales_state (new dict returned).

    Raises ValueError if any key is not in the documented schema.
    """
    unknown = set(updates.keys()) - _ALLOWED_KEYS
    if unknown:
        raise ValueError(
            f"sales_state keys {sorted(unknown)} not in schema. "
            f"Allowed: {sorted(_ALLOWED_KEYS)}"
        )
    return _mutate(user_id, updates)


def reset_unclear_retry(user_id: str) -> dict[str, Any]:
    """Reset unclear_retries to 0 after a successful step advance."""
    return _mutate(user_id, {"unclear_retries": 0})


def mark_flow_type(user_id: str, flow_type: str) -> dict[str, Any]:
    """Change flow_type (e.g. 'qna' when user escapes, 'complete' on finish)."""
    if flow_type not in ("sales", "qna", "booking", "complete"):
        raise ValueError(f"invalid flow_type: {flow_type}")
    return _mutate(user_id, {"flow_type": flow_type})


def clear_sales_state(user_id: str) -> None:
    """Remove sales_state entirely (e.g. on RESTART or hard reset)."""
    with _get_user_lock(user_id):
        update_journey(user_id, {_KEY: None})


# ── Internal helpers ──────────────────────────────────────────────────


def _mutate(user_id: str, patch: dict[str, Any]) -> dict[str, Any]:
    """Apply a static `patch` dict to current state and persist.

    Use this when the patch does not depend on the existing state value.
    For compute-on-read-modify-write (e.g. record_answer), use _mutate_with.
    """
    with _get_user_lock(user_id):
        state = get_sales_state(user_id)
        updated = dict(state)
        updated.update(patch)
        updated["last_advance_at"] = int(time.time())
        _persist(user_id, updated)
        return updated


def _mutate_with(
    user_id: str,
    patch_fn: Callable[[dict[str, Any]], dict[str, Any]],
) -> dict[str, Any]:
    """Apply a patch computed FROM the current state, atomically.

    The patch_fn is called INSIDE the lock with a snapshot of the current
    state, and returns the patch dict. This prevents TOCTOU when the new
    value depends on the existing value (e.g. appending to a dict, counter
    increment).
    """
    with _get_user_lock(user_id):
        state = get_sales_state(user_id)
        patch = patch_fn(state)
        updated = dict(state)
        updated.update(patch)
        updated["last_advance_at"] = int(time.time())
        _persist(user_id, updated)
        return updated


def _persist(user_id: str, state: dict[str, Any]) -> None:
    update_journey(user_id, {_KEY: state})
