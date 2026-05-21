"""Planner Agent — decides which specialist(s) handle each turn.

Inputs:
- CRM snapshot (User)
- Buffered user message (post-merge)
- Last 5 turns of history (already on User.conversation_history)

Output: PlannerDecision (1 or 2 specialists, ordered).

Design notes:
- The Planner does NOT understand TCM domain knowledge. It routes based
  on user signals (text patterns, history state, media attachments).
- It can route to 2 specialists in parallel (cap). Two is enforced at
  PlannerDecision schema level.
- Some routes are deterministic and bypass the LLM (see _rule_overrides).
"""

from __future__ import annotations

import json
import logging
from typing import Any

from anthropic import AsyncAnthropic

from src.agents.base import PlannerDecision, SpecialistName
from src.crm.models import Constitution, User, UserStatus

logger = logging.getLogger("agents.planner")

DEFAULT_MODEL = "claude-sonnet-4-5-20250929"

_PLANNER_SYSTEM = """你係 Jessica 嘅 Planner —— 一個路由 brain，唔對用戶講嘢，淨係決定下面 5 個 specialist 邊個處理呢 turn。

可用 specialist：
- greeting: 寒暄、閒聊、無內容嘅問候
- faq: 中醫 / 養生 / 食療 / 穴位嘅知識性問題
- sales: 用戶想睇產品 / 買嘢 / 問價錢
- constitution: 用戶提到健康 / 不適 / 症狀，或者已經 send 咗脷相，要做體質評估
- appointment: 用戶想預約 / 問診所地址 / 問可唔可以視診

規則：
- 一個 turn 最多 2 個 specialist（順序或並行）
- 如果有脷相圖片 → 必須包 constitution
- 如果用戶問「點解」「乜嘢」「邊個」嘅知識問題 + 同時想預約 → faq + appointment 並行
- 如果用戶 status 係 constitution_done 之後第一次回應 → 通常 sales（pitch 湯水/藥膏）
- 唔肯定就揀 greeting

輸出純 JSON，schema：
{
  "specialists": ["...", "..."],   // 1-2 個
  "reasoning": "...",              // 一句中文，解釋點解咁路由
  "parallel": true/false,           // true = 兩個並行；false = 順序
  "notes_for_writer": "..."        // 比 Writer 嘅特別 hint，例如「保持溫和」
}

唔好輸出 markdown，淨係 JSON object。"""


class PlannerAgent:
    def __init__(
        self,
        client: AsyncAnthropic,
        *,
        model: str = DEFAULT_MODEL,
        max_tokens: int = 400,
    ) -> None:
        self._client = client
        self._model = model
        self._max_tokens = max_tokens

    async def decide(
        self,
        user: User,
        user_message: str,
        media_urls: list[str] | None = None,
    ) -> tuple[PlannerDecision, dict[str, Any]]:
        """Return (decision, usage_metadata)."""
        media_urls = media_urls or []

        # Rule-based fast paths
        override = _rule_overrides(user, user_message, media_urls)
        if override is not None:
            return override, {
                "model": "rule",
                "input_tokens": 0,
                "output_tokens": 0,
                "shortcut": True,
            }

        # LLM-based routing
        prompt = _build_user_prompt(user, user_message, media_urls)
        response = await self._client.messages.create(
            model=self._model,
            max_tokens=self._max_tokens,
            system=_PLANNER_SYSTEM,
            messages=[{"role": "user", "content": prompt}],
        )

        raw_text = "".join(
            block.text for block in response.content if block.type == "text"
        ).strip()

        try:
            data = _extract_json(raw_text)
            decision = PlannerDecision.model_validate(data)
        except Exception as exc:  # noqa: BLE001
            logger.warning("planner JSON parse failed (%s); raw=%r", exc, raw_text)
            decision = PlannerDecision(
                specialists=[SpecialistName.GREETING],
                reasoning=f"fallback after parse error: {exc}",
                parallel=False,
            )

        usage = {
            "model": self._model,
            "input_tokens": response.usage.input_tokens,
            "output_tokens": response.usage.output_tokens,
            "shortcut": False,
        }
        return decision, usage


# -------------------------------------------------------------------
# Rule overrides — deterministic short-circuits
# -------------------------------------------------------------------


def _rule_overrides(
    user: User, user_message: str, media_urls: list[str]
) -> PlannerDecision | None:
    """Skip the LLM for routes where the answer is obvious."""

    # Tongue photo → constitution is mandatory
    if media_urls:
        # If user previously asked an FAQ AND now sent tongue photo, do parallel
        if user.status in (UserStatus.NEW, UserStatus.QUALIFIED):
            return PlannerDecision(
                specialists=[SpecialistName.CONSTITUTION],
                reasoning="rule: media (likely tongue photo) → constitution",
                parallel=False,
            )

    # Empty / extremely short greeting → greeting only
    stripped = user_message.strip()
    if stripped in {"hi", "hello", "你好", "Hi", "HI"} and not user.conversation_history:
        return PlannerDecision(
            specialists=[SpecialistName.GREETING],
            reasoning="rule: first-touch greeting",
            parallel=False,
        )

    return None


# -------------------------------------------------------------------
# Helpers
# -------------------------------------------------------------------


def _build_user_prompt(user: User, user_message: str, media_urls: list[str]) -> str:
    history_snippet = _format_history(user.conversation_history[-5:])
    media_note = (
        f"用戶有 send {len(media_urls)} 個 media（可能係脷相）。" if media_urls else ""
    )

    return f"""用戶資料：
- phone: {user.phone}
- status: {user.status.value}
- 體質: {user.constitution.value if user.constitution != Constitution.UNKNOWN else "未評估"}
- pain_points: {user.pain_points or "(無)"}
- 之前 pitched 過: {user.products_pitched or "(無)"}

最近對話（舊→新）：
{history_snippet or "(無歷史)"}

今次用戶訊息：
「{user_message}」
{media_note}

輸出 JSON 決定點 route。"""


def _format_history(messages: list[Any]) -> str:
    lines = []
    for m in messages:
        who = "用戶" if m.role == "user" else "Jessica"
        lines.append(f"- {who}: {m.content[:80]}")
    return "\n".join(lines)


def _extract_json(text: str) -> dict[str, Any]:
    """Pull the first JSON object out of `text`, tolerating leading prose."""
    start = text.find("{")
    end = text.rfind("}")
    if start == -1 or end == -1:
        raise ValueError(f"no JSON object in planner output: {text[:200]!r}")
    return json.loads(text[start : end + 1])
