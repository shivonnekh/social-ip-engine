"""Compose a persona-voiced DM strictly from FAQAgent-provided facts.

WHY THIS EXISTS
---------------
The second (of two) constrained LLM calls in the unmatched-comment reply
path (see ``src/channels/unmatched_comment.py``). ``FAQAgent.run()``
already did the KB grounding + fact extraction (CLAUDE.md §3.5) — this
module's ONLY job is to turn those already-grounded facts into a warm,
persona-voiced DM sentence or two. Same non-negotiable rule as
``src/agents/writer.py``: this is a re-narration step, never a fact
source. The system prompt explicitly forbids adding any fact, product
name, or price not present in the input.

``compose_faq_dm`` returns ``None`` (never sends a DM) whenever there is
nothing safely groundable to answer with — a stranger commenting on a
post must never receive a hallucinated private reply just because the
triage gate said "genuine".
"""

from __future__ import annotations

import logging
from typing import Any

from src.agents.base import SpecialistOutput
from src.llm import DEFAULT_MODEL, LLMClient

logger = logging.getLogger("agents.comment_dm_answer")

_SYSTEM = """You are composing a SHORT, warm, persona-voiced DM reply to \
someone who commented on a TCM (Traditional Chinese Medicine) wellness \
content-creator's social post.

You are given:
  - the commenter's original comment/question
  - a list of grounded facts (already extracted from a knowledge-base card \
by another step in the pipeline)

Your ONLY job is to re-narrate those facts warmly and conversationally, \
1-3 short sentences, suitable for a direct message.

HARD RULES — never break these:
  - NEVER invent, assume, or fabricate any fact, health claim, product \
name, price, clinic name, or booking detail that is not explicitly present \
in the facts you were given below. If the facts don't fully answer the \
question, say so honestly rather than filling the gap yourself.
  - Do not add a call-to-action to book/visit a clinic or buy anything.
  - Keep it short and friendly — this is a DM reply, not an essay.

Output the DM text only — no JSON, no markdown, no preamble."""


async def compose_faq_dm(
    comment_text: str,
    faq_output: SpecialistOutput,
    *,
    client: LLMClient | None,
    lang: str,
) -> str | None:
    """Render a grounded, persona-voiced DM from ``faq_output``'s payload.

    Returns ``None`` (caller MUST send no DM) when:
      - the FAQ payload signals ``no_match``,
      - there are no usable facts (``answer_facts`` empty AND no
        ``top_card_content.core_answer``), or
      - ``client`` is ``None`` (no LLM available — fails closed rather than
        silently proceeding without one).
    """
    payload = faq_output.payload or {}
    if payload.get("no_match"):
        return None

    facts: list[dict[str, Any]] = list(payload.get("answer_facts") or [])
    top_card: dict[str, Any] = dict(payload.get("top_card_content") or {})
    core_answer = str(top_card.get("core_answer", "")).strip()

    if not facts and not core_answer:
        return None

    if client is None:
        logger.warning(
            "[comment_dm_answer] compose_faq_dm called with no LLM client — "
            "cannot compose a grounded reply, returning None (no DM sent)"
        )
        return None

    prompt = _build_prompt(comment_text, facts, top_card, lang)
    response = await client.messages.create(
        model=DEFAULT_MODEL,
        max_tokens=400,
        system=_SYSTEM,
        messages=[{"role": "user", "content": prompt}],
    )
    text = "".join(
        block.text for block in response.content if block.type == "text"
    ).strip()
    return text or None


def _build_prompt(
    comment_text: str,
    facts: list[dict[str, Any]],
    top_card: dict[str, Any],
    lang: str,
) -> str:
    fact_lines = "\n".join(f"- {f.get('fact', '')}" for f in facts if f.get("fact"))
    supporting = "\n".join(
        f"- {p}" for p in top_card.get("supporting_points", []) if p
    )
    core_answer = str(top_card.get("core_answer", "")).strip()

    return f"""Reply language hint: {lang or 'unknown'}

Commenter's comment/question: {comment_text!r}

Grounded facts (ONLY source of truth — do not add anything beyond this):
{fact_lines or '(none)'}

Card core answer (if present, ONLY source of truth):
{core_answer or '(none)'}

Card supporting points (ONLY source of truth):
{supporting or '(none)'}

Compose the DM reply now, following your system instructions exactly."""
