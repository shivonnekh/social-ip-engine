"""Chloe — the Instagram / Facebook DM agent (separate route from Jessica).

Chloe (陳芷晴) is the content-creator persona for social channels. She is
intentionally *lighter* than the Jessica clinic pipeline:

    * Greeting-first — every NEW conversation opens with her intro.
    * Warm, educational, short replies (IG-DM cadence).
    * Soft CTA to WhatsApp for deep consultation (where Jessica converts).
    * No 体质 diagnosis / tongue photos / hard sell — those live on WhatsApp.

She reuses the shared CRM (namespaced ``ig_<id>`` / ``fb_<id>`` keys) so
conversation history persists, but does NOT run the Planner→Specialists→
Writer pipeline. One LLM call per turn.

Persona config: ``data/personas/chloe.json`` (env override CHLOE_PERSONA_PATH).
"""

from __future__ import annotations

import json
import logging
import os
import re
from dataclasses import dataclass, field
from datetime import datetime
from functools import lru_cache
from pathlib import Path
from typing import Final

from src.crm.models import ConversationMessage

logger = logging.getLogger("channels.chloe")

_DEFAULT_PERSONA_PATH: Final[str] = str(
    Path(__file__).resolve().parent.parent.parent / "data" / "personas" / "chloe.json"
)
_HISTORY_WINDOW: Final[int] = 16


@dataclass(frozen=True)
class ChloePersona:
    """Immutable Chloe persona profile loaded from JSON."""

    display_name: str
    whatsapp_cta: str
    greeting_bubbles: tuple[str, ...]
    greeting_media_url: str
    system_prompt: str
    model: str
    max_tokens: int
    max_bubbles: int


@dataclass(frozen=True)
class ChloeReply:
    """Bubbles + optional media to send back on a DM."""

    bubbles: list[str] = field(default_factory=list)
    media: list[dict] = field(default_factory=list)  # [{url, after_bubble_idx}]


def _persona_path() -> Path:
    return Path(os.environ.get("CHLOE_PERSONA_PATH", _DEFAULT_PERSONA_PATH))


@lru_cache(maxsize=4)
def _load_persona(path_str: str, mtime: float) -> ChloePersona:
    data = json.loads(Path(path_str).read_text(encoding="utf-8"))
    return ChloePersona(
        display_name=str(data.get("display_name", "Chloe")),
        whatsapp_cta=str(data.get("whatsapp_cta", "")),
        greeting_bubbles=tuple(str(b) for b in data.get("greeting_bubbles", []) if str(b).strip()),
        greeting_media_url=str(data.get("greeting_media_url", "")).strip(),
        system_prompt=str(data.get("system_prompt", "")),
        model=str(data.get("model", "gpt-5.4-mini")),
        max_tokens=int(data.get("max_tokens", 400)),
        max_bubbles=int(data.get("max_bubbles", 3)),
    )


def load_persona() -> ChloePersona:
    p = _persona_path()
    mtime = p.stat().st_mtime if p.exists() else 0.0
    return _load_persona(str(p), mtime)


class ChloeAgent:
    """Single-LLM-call social DM agent. Greeting-first, CRM-backed."""

    def __init__(self, client, crm) -> None:
        # client: src.llm.LLMClient ; crm: CRM repo (same instance as pipeline)
        self._client = client
        self._crm = crm

    async def respond(
        self, *, crm_key: str, user_message: str, message_id: str | None = None
    ) -> ChloeReply:
        """Produce Chloe's reply for one inbound DM.

        Greeting-first: when the user has no prior conversation history,
        the persona greeting bubbles are sent first, then her answer.
        """
        persona = load_persona()

        # 1. Load user + decide if this is a first-touch conversation.
        user = await self._crm.get_or_create_user(crm_key)
        history = list(getattr(user, "conversation_history", []) or [])
        is_first_touch = len(history) == 0

        # 2. Build the LLM reply (always answer their actual message).
        try:
            answer_bubbles = await self._generate(persona, history, user_message)
        except Exception:  # noqa: BLE001
            logger.exception("[chloe] LLM generation failed for %s", crm_key)
            answer_bubbles = ["唔好意思，我而家有少少繁忙 🙏 你可以 WhatsApp 我 "
                              f"{persona.whatsapp_cta}，我盡快覆你 🌿"]

        # 3. Greeting-first composition.
        bubbles: list[str] = []
        media: list[dict] = []
        if is_first_touch:
            bubbles.extend(persona.greeting_bubbles)
            if persona.greeting_media_url:
                media.append({"url": persona.greeting_media_url,
                              "after_bubble_idx": max(0, len(persona.greeting_bubbles) - 1)})
        bubbles.extend(answer_bubbles)
        bubbles = [b for b in bubbles if b.strip()][: max(1, persona.max_bubbles + len(persona.greeting_bubbles))]

        # 4. Persist both sides to CRM (best-effort).
        await self._persist(crm_key, user_message, bubbles, message_id)

        return ChloeReply(bubbles=bubbles, media=media)

    # ------------------------------------------------------------------

    async def _generate(
        self, persona: ChloePersona, history: list[ConversationMessage], user_message: str
    ) -> list[str]:
        messages: list[dict] = []
        for m in history[-_HISTORY_WINDOW:]:
            role = "user" if getattr(m, "role", "user") == "user" else "assistant"
            messages.append({"role": role, "content": getattr(m, "content", "")})
        messages.append({"role": "user", "content": user_message})

        resp = await self._client.messages.create(
            model=persona.model,
            max_tokens=persona.max_tokens,
            system=persona.system_prompt,
            messages=messages,
        )
        text = "".join(
            block.text for block in resp.content if getattr(block, "type", "") == "text"
        )
        return _split_bubbles(text, persona.max_bubbles)

    async def _persist(
        self, crm_key: str, user_message: str, bubbles: list[str], message_id: str | None
    ) -> None:
        now = datetime.utcnow()
        try:
            await self._crm.append_message(
                crm_key,
                ConversationMessage(role="user", content=user_message, at=now,
                                    wa_message_id=message_id),
            )
            reply_text = "\n\n".join(bubbles)
            await self._crm.append_message(
                crm_key,
                ConversationMessage(role="chloe", content=reply_text, at=now),
            )
        except Exception:  # noqa: BLE001
            logger.exception("[chloe] CRM persist failed for %s", crm_key)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _split_bubbles(text: str, max_bubbles: int) -> list[str]:
    """Split Chloe's plain-text reply into bubbles on blank lines.

    Falls back to sentence-ish splitting if the model returned one blob.
    Always returns at least one bubble; caps at ``max_bubbles``.
    """
    text = (text or "").strip()
    if not text:
        return []
    parts = [p.strip() for p in re.split(r"\n\s*\n", text) if p.strip()]
    if len(parts) <= 1:
        # single blob — split on newlines as a softer fallback
        parts = [p.strip() for p in text.split("\n") if p.strip()] or [text]
    return parts[:max_bubbles]
