"""Greeting / Others Agent — casual, warm, gentle.

This is the first specialist we ship end-to-end. Goal: prove the
pipeline (Planner → Specialist → Writer → Send → Trace).

Output schema:
    {
        "tone": "warm" | "playful" | "concerned",
        "topic": str,                       # what the user touched on
        "suggested_followup": str | None,   # an open question Writer can ask
        "intent_flags": list[str]           # e.g. ["new_user_intro"]
    }

The Greeting agent does NOT have tools. It only inspects the conversation
and produces structured intent. The Writer composes the actual bubbles.
"""

from __future__ import annotations

import json
import logging
from typing import Any

from anthropic import AsyncAnthropic

from src.agents.base import (
    SpecialistInput,
    SpecialistName,
    SpecialistOutput,
)
from src.crm.models import UserStatus

logger = logging.getLogger("agents.greeting")

DEFAULT_MODEL = "claude-haiku-4-5-20250303"  # cheap — Greeting doesn't need Sonnet

_SYSTEM = """你係 Jessica 嘅 Greeting Specialist —— 處理寒暄、閒聊、初次見面。

你 *唔* 直接寫俾用戶嘅嘢。你淨係輸出 structured intent 比 Writer。

輸入：用戶最新一句 + 對話歷史 + CRM 狀態
輸出：純 JSON，schema：
{
  "tone": "warm" | "playful" | "concerned",
  "topic": "...",                          // 一句概括用戶講咩
  "suggested_followup": "..." | null,      // Writer 可以用嘅 follow-up 問題（中文）
  "intent_flags": ["..."]                  // 例如 ["new_user_intro", "rapport_check"]
}

規則：
- 第一次見面 → tone=warm, intent_flags=["new_user_intro"]，suggested_followup 應該係邀請用戶講下自己嘅 health concerns
- 用戶情緒低落 → tone=concerned
- 隨意閒聊 → tone=playful
- topic 用一句中文總結，唔好用英文

唔好輸出 markdown，淨係 JSON。"""


class GreetingAgent:
    def __init__(
        self,
        client: AsyncAnthropic,
        *,
        model: str = DEFAULT_MODEL,
        max_tokens: int = 300,
    ) -> None:
        self._client = client
        self._model = model
        self._max_tokens = max_tokens

    async def run(self, inp: SpecialistInput) -> tuple[SpecialistOutput, dict[str, Any]]:
        is_first_touch = (
            inp.user.status == UserStatus.NEW
            and not inp.user.conversation_history
        )

        prompt = _build_prompt(inp, is_first_touch=is_first_touch)
        response = await self._client.messages.create(
            model=self._model,
            max_tokens=self._max_tokens,
            system=_SYSTEM,
            messages=[{"role": "user", "content": prompt}],
        )

        raw = "".join(
            block.text for block in response.content if block.type == "text"
        ).strip()

        try:
            payload = _extract_json(raw)
        except Exception as exc:  # noqa: BLE001
            logger.warning("greeting JSON parse failed (%s); raw=%r", exc, raw)
            payload = {
                "tone": "warm",
                "topic": "（解析失敗，預設友善寒暄）",
                "suggested_followup": None,
                "intent_flags": ["parse_error"],
            }

        suggested_diff: dict[str, Any] = {}
        if is_first_touch:
            suggested_diff["status"] = UserStatus.QUALIFIED.value

        output = SpecialistOutput(
            specialist=SpecialistName.GREETING,
            payload=payload,
            suggested_user_state_diff=suggested_diff,
        )
        usage = {
            "model": self._model,
            "input_tokens": response.usage.input_tokens,
            "output_tokens": response.usage.output_tokens,
        }
        return output, usage


def _build_prompt(inp: SpecialistInput, *, is_first_touch: bool) -> str:
    history_lines = []
    for m in inp.user.conversation_history[-4:]:
        who = "用戶" if m.role == "user" else "Jessica"
        history_lines.append(f"- {who}: {m.content[:80]}")
    history_txt = "\n".join(history_lines) or "(冇歷史)"

    first_touch_hint = (
        "\n** 呢個係首次見面，記得 warm + new_user_intro **" if is_first_touch else ""
    )

    return f"""用戶 phone: {inp.user.phone}
status: {inp.user.status.value}
最近對話:
{history_txt}

今次訊息: 「{inp.user_message}」
{first_touch_hint}

輸出 JSON。"""


def _extract_json(text: str) -> dict[str, Any]:
    start = text.find("{")
    end = text.rfind("}")
    if start == -1 or end == -1:
        raise ValueError(f"no JSON object: {text[:200]!r}")
    return json.loads(text[start : end + 1])
