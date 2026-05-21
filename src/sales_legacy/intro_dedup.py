"""Strip repeated phase-transition intros in sales-mode replies.

Why this exists
---------------
The tongue-receipt intro line — "脷相收到啦 🌿 等我多問你兩條題,
一齊判斷下你嘅體質傾向 ✨" — is queued ONCE as a lead bubble by
``analyze_tongue``'s auto-fallback (see
``src/tools/sales.py::_build_tongue_reading_text``). It marks the
phase transition: tongue → constitution-Q phase.

Observed bug 2026-04-28 (WhatsApp screenshot): after the user
answers Q1 with "B", the bot emits the same intro AGAIN in its
reply text before Q2. The LLM saw the intro in turn 1's transcript
and is mimicking it as a "phase transition" before Q2 — but
Q1 → Q2 is NOT a phase transition. The constitution-Q phase is
already in flight; the user just needs the next question.

Strategy
--------
Strip the canonical intro from LLM reply text ONLY when:

  1. The constitution-Q phase has started AT THE BEGINNING OF THIS
     TURN — i.e. ``tongue_described`` was already true BEFORE this
     turn started, OR Q1 has already been answered.
  2. AND the LLM did NOT call any tongue-analysis tool this turn
     (``analyze_tongue`` / ``describe_tongue_findings``). On the
     very turn those tools run, the LLM may legitimately write
     content alongside the tool-queued lead bubble — we must not
     touch the LLM's output on that turn.

Both gates must pass. This is the conservative posture: we'd
rather miss a duplicate (tolerable cosmetic glitch) than strip a
legitimate first-time analysis (which would leave the customer
with no acknowledgment of their photo — far worse UX).

We're additionally conservative on the regex: only match the
canonical opener token ``脷相收到啦`` and only when it appears as
its own paragraph (own bubble) or at the head of the reply.
Mid-sentence occurrences (quotation, meta-commentary) are left
alone.

Idempotent. Runs BEFORE bubble splitting so we don't have to
reconstruct cross-bubble fragments.
"""
from __future__ import annotations

import logging
import re
from typing import Iterable

logger = logging.getLogger("sales.intro_dedup")

# Tool calls whose presence on the current turn means "we are still
# inside the tongue-acknowledgment phase" — leave the LLM output alone.
_TONGUE_TOOLS_THIS_TURN = frozenset({
    "analyze_tongue",
    "describe_tongue_findings",
})

# Detect the canonical "脷相收到啦" opener as its own paragraph.
# We anchor on the literal trigger token — anything between it and
# the paragraph break (\n\n or end-of-string) is the intro and gets
# dropped wholesale. Conservative: only strikes when it sits at the
# head of a paragraph, never mid-sentence.
_TONGUE_INTRO_PATTERN = re.compile(
    r"(?:\A|\n\n+)\s*脷相收到啦[^\n]*?(?=\n\n|\Z)",
    re.DOTALL,
)


def _phase_constitution_started(sales_state: dict | None) -> bool:
    """Return True when the constitution-Q phase has already begun.

    Triggers:
      * ``tongue_described`` is true (analyze_tongue already auto-queued
        the intro lead bubble OR LLM ran describe_tongue_findings).
      * ``constitution_answers.q1`` is set (Q1 has been answered, so
        the user is firmly past the tongue acknowledgment phase).
    """
    if not isinstance(sales_state, dict):
        return False
    if sales_state.get("tongue_described"):
        return True
    answers = sales_state.get("constitution_answers") or {}
    if isinstance(answers, dict) and answers.get("q1"):
        return True
    return False


def _ran_tongue_tool_this_turn(tool_calls_log: Iterable[dict] | None) -> bool:
    """True when analyze_tongue or describe_tongue_findings was called
    on the current turn — signal that the LLM is *legitimately*
    composing the first-time tongue acknowledgment, so we must not
    touch its reply text."""
    if not tool_calls_log:
        return False
    for tc in tool_calls_log:
        if not isinstance(tc, dict):
            continue
        name = tc.get("tool_name") or tc.get("name") or ""
        if name in _TONGUE_TOOLS_THIS_TURN:
            return True
    return False


def strip_repeated_phase_intro(
    response: str,
    *,
    sales_state: dict | None,
    tool_calls_log: Iterable[dict] | None = None,
) -> tuple[str, bool]:
    """Remove repeated phase-transition intro from LLM reply text.

    Args:
        response: Full LLM response text, BEFORE bubble splitting.
        sales_state: Current sales state (from
            ``patient.clinical.sales``) — used to decide whether the
            constitution phase has already started.
        tool_calls_log: Tool calls executed on the current turn. If
            ``analyze_tongue`` or ``describe_tongue_findings`` is in
            the list, the dedup is skipped — the LLM is composing
            the legitimate first-time acknowledgment.

    Returns:
        ``(text_without_intro, fired)`` where ``fired`` is True if any
        intro paragraph was stripped (useful for the pipeline trace).

    Edge cases:
        * Empty response → no-op.
        * Constitution phase not yet started → no-op (intro is
          legitimate on the tongue-ack turn).
        * analyze_tongue / describe_tongue_findings ran this turn →
          no-op (this is the legitimate tongue-ack turn — leave the
          LLM's reply text alone, the user must see the analysis).
        * Intro phrase appears mid-sentence → no-op (we only strike
          own-paragraph occurrences).
        * Multiple stray intros → all stripped.
    """
    if not response or not _phase_constitution_started(sales_state):
        return response, False

    if _ran_tongue_tool_this_turn(tool_calls_log):
        # Same turn the analysis just happened — leave LLM output alone.
        return response, False

    matches = list(_TONGUE_INTRO_PATTERN.finditer(response))
    if not matches:
        return response, False

    # Wholesale removal of every matched paragraph.
    new_text = _TONGUE_INTRO_PATTERN.sub("", response)

    # Collapse the leading blank lines we may have introduced.
    new_text = re.sub(r"\A\s*\n+", "", new_text)
    # Collapse runs of 3+ blank lines into a clean paragraph break.
    new_text = re.sub(r"\n{3,}", "\n\n", new_text)

    if new_text == response:
        return response, False

    logger.warning(
        "[intro_dedup] stripped %d repeated phase-transition intro paragraph(s) "
        "(constitution phase already started, no tongue tool this turn)",
        len(matches),
    )
    return new_text.strip(), True
