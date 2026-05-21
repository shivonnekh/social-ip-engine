"""Final Writer Agent — composes 1 final reply from all specialist outputs.

Inputs:
- CRM snapshot (for tone calibration + history)
- Original user message
- Planner decision (so Writer knows what was attempted)
- Specialist outputs (1 or 2)

Output: WriterOutput — list of bubbles + optional media to inline.

Why a separate Writer (CLAUDE.md §3.6):
- Single Jessica voice — 5 specialists writing copy = 5 voices.
- HK 廣東話口語 polish lives here, once.
- Bubble-split rhythm tuning belongs in one place.
- Specialists return structured INTENT; Writer turns it into language.

The Writer is FORBIDDEN to invent medical / product facts. It can only
re-narrate what specialists provided in `payload`.
"""

from __future__ import annotations

import json
import logging
from typing import Any

from anthropic import AsyncAnthropic

from src.agents.base import (
    PlannerDecision,
    SpecialistOutput,
    WriterOutput,
)
from src.crm.models import User

logger = logging.getLogger("agents.writer")

DEFAULT_MODEL = "claude-sonnet-4-5-20250929"
MAX_BUBBLES = 5

_SYSTEM = """你係 Jessica —— 心宜中醫嘅 WhatsApp AI teammate。

身份：
- 唔係醫師，唔做診斷
- 溫柔、人情味、有少少俏皮，HK 廣東話口語
- 永遠用「我」唔好用「Jessica」自稱
- 唔好用書面語、唔好用 mandarin 詞（例如「您」「我們」「請」"嗎"），用「你」「我哋」「唔該」「啊」

你嘅工作：
讀 specialist 比你嘅 structured intent，組合成自然嘅 WhatsApp 對話。

規則：
- 輸出 1-5 個 message bubbles（每個 ~80-180 字）
- 每個 bubble 用「\\n」分隔，唔好用 markdown bullet
- 用 emoji 但唔好過多（每 bubble 最多 1-2 個）
- 如果有 2 個 specialist 嘅 output，*融合* 佢哋，唔好簡單拼接
- 絕對唔好作 specialist 冇講過嘅 fact（產品 / 價錢 / 體質 / 診所地址）
- 如果用戶第一次見面 → 一定要做自我介紹「我係 Jessica」

輸出 JSON：
{
  "bubbles": ["第一句", "第二句", "..."],
  "media_to_send": []   // 暫時冇用，留空 array
}"""


class WriterAgent:
    def __init__(
        self,
        client: AsyncAnthropic,
        *,
        model: str = DEFAULT_MODEL,
        max_tokens: int = 800,
    ) -> None:
        self._client = client
        self._model = model
        self._max_tokens = max_tokens

    async def compose(
        self,
        user: User,
        user_message: str,
        planner_decision: PlannerDecision,
        specialist_outputs: list[SpecialistOutput],
    ) -> tuple[WriterOutput, dict[str, Any]]:
        prompt = _build_prompt(
            user=user,
            user_message=user_message,
            planner_decision=planner_decision,
            specialist_outputs=specialist_outputs,
        )

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
            data = _extract_json(raw)
            bubbles = [b.strip() for b in data.get("bubbles", []) if b.strip()]
            if not bubbles:
                raise ValueError("empty bubbles")
            output = WriterOutput(
                bubbles=bubbles[:MAX_BUBBLES],
                media_to_send=data.get("media_to_send", []),
            )
        except Exception as exc:  # noqa: BLE001
            logger.warning("writer JSON parse failed (%s); raw=%r", exc, raw)
            output = WriterOutput(
                bubbles=["唔好意思啊，我而家有啲問題，等陣再試多次 🙏"],
                media_to_send=[],
            )

        usage = {
            "model": self._model,
            "input_tokens": response.usage.input_tokens,
            "output_tokens": response.usage.output_tokens,
        }
        return output, usage


def _build_prompt(
    *,
    user: User,
    user_message: str,
    planner_decision: PlannerDecision,
    specialist_outputs: list[SpecialistOutput],
) -> str:
    specialists_dump = "\n\n".join(
        f"=== Specialist: {o.specialist.value} ===\n"
        f"payload: {json.dumps(o.payload, ensure_ascii=False, indent=2)}"
        + (f"\ncards_used: {o.cards_used}" if o.cards_used else "")
        + (f"\ntools: {[t.get('name') for t in o.tools_called]}" if o.tools_called else "")
        for o in specialist_outputs
    )

    history_lines = []
    for m in user.conversation_history[-4:]:
        who = "用戶" if m.role == "user" else "Jessica"
        history_lines.append(f"- {who}: {m.content[:80]}")
    history_txt = "\n".join(history_lines) or "(冇歷史)"

    return f"""用戶資料：
phone: {user.phone}
name: {user.name or "(未知)"}
status: {user.status.value}
體質: {user.constitution.value}
pain_points: {user.pain_points or "(無)"}

最近對話：
{history_txt}

用戶今次訊息：「{user_message}」

Planner 路由：
- specialists: {[s.value for s in planner_decision.specialists]}
- 並行: {planner_decision.parallel}
- 原因: {planner_decision.reasoning}
- notes_for_writer: {planner_decision.notes_for_writer or "(無)"}

Specialist 比你嘅 structured intent：

{specialists_dump}

請組合成 1-5 個 WhatsApp message bubbles，輸出 JSON。"""


def _extract_json(text: str) -> dict[str, Any]:
    start = text.find("{")
    end = text.rfind("}")
    if start == -1 or end == -1:
        raise ValueError(f"no JSON: {text[:200]!r}")
    return json.loads(text[start : end + 1])
