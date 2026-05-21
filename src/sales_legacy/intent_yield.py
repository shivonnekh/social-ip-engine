"""Intent yield detector — A1 fix for "journey state machine ignores user content questions".

Production transcript (wa_60164245634, T5):
- User: "how to improve now?" while bot was mid-journey
- Bot: 跳到 Q1 ("你最近精神点呀? 容易攰嗎?") 因为 journey 强制推进
- User feedback architect: "the journey state machine is the master,
  the user is treated as an interruption."

This module provides a fast regex/keyword detector that classifies a user
message as either:

- CONTENT_QUESTION  → 用户在问内容 (求帮助/求解释/求方法)
                      bot 应该先答, 再回 journey
- JOURNEY_ANSWER    → 用户在答 bot 上一题 (e.g. "A" 或 "两年")
                      bot 继续 journey, 不要 yield

The detector is deterministic (regex + keyword), runs in <1ms, and never
makes another LLM call (latency-critical).

Used by: src/agent.py → build_system_prompt() → build_jessica_prompt(),
which renders a small dynamic block telling Jessica to yield this turn.
"""
from __future__ import annotations

import re
from dataclasses import dataclass

# 内容问题关键词 (中文 + English mix, HK Cantonese style).
# 这些词出现 = 用户求助/询问内容, 不是答 journey question.
_CONTENT_QUESTION_PATTERNS: tuple[re.Pattern[str], ...] = (
    # 中文 wh-words / how-to
    re.compile(r"点(?:样|处理|改善|搞|医|算|算好|做|做好|解决)"),
    re.compile(r"點(?:樣|處理|改善|搞|醫|算|算好|做|做好|解決)"),
    re.compile(r"怎(?:样|麼|樣|麼樣|麽)"),
    re.compile(r"如何"),
    re.compile(r"有冇(?:咩|甚麼|什麼|什么)?(?:方法|办法|辦法|建议|建議|推薦|推荐|tip|tips)"),
    re.compile(r"推薦(?:下|啲|吓|吓)?(?:湯|汤|茶|食|穴位|方法)"),
    re.compile(r"有(?:咩|甚麼|什麼|什么)(?:方法|办法|辦法|建议|建議|可以|食|做|喝|飲|湯|汤|茶)"),
    re.compile(r"可以(?:点|點|食|喝|飲|做|試|试|用|食啲咩|做啲咩|喝啲咩|飲啲咩)"),
    # 什么/甚麼 as standalone wh-words (Mandarin-style questions common in HK)
    re.compile(r"(?:什么|甚麼|啲咩)(?:汤|湯|茶|食物|嘢食|方法|穴位|辦法|办法)"),
    re.compile(r"(?:食|喝|飲)(?:什么|甚麼|咩|啲咩)"),
    re.compile(r"(?:帮|幫|教)(?:我|下我)"),
    re.compile(r"(?:想|要)知"),
    re.compile(r"(?:解释|解釋|讲下|講下|话我知|話我知)"),
    re.compile(r"咩(?:係|是|意思)"),
    re.compile(r"(?:仲|還|还)有(?:冇|无|無|没)(?:其他|其它|别的|別的)"),
    re.compile(r"其他(?:方法|办法|辦法|建议|建議|tip)"),
    # English
    re.compile(r"\bhow\s+(?:to|do|can|should|much|many|long)\b", re.I),
    re.compile(r"\bwhat\s+(?:is|are|can|should|do|does|about|soup|tea|food)\b", re.I),
    re.compile(r"\bwhy\b", re.I),
    re.compile(r"\bcan\s+you\s+(?:help|tell|explain|share|recommend|suggest)\b", re.I),
    re.compile(r"\bany\s+(?:tips|advice|suggestions|other|alternative)\b", re.I),
    re.compile(r"\b(?:want|need)\s+to\s+know\b", re.I),
    # TCM topic keywords — these are always content questions even when short
    # ("穴位呢?" is 4 chars but is asking for acupoint content, not answering a journey Q)
    re.compile(r"穴位"),        # "穴位呢?" / "有冇穴位" / "按邊個穴位"
    re.compile(r"按摩(?:邊|位|點|穴)"),  # "按摩邊個穴位" etc.
    re.compile(r"艾灸(?:邊|點|咩|位)"),  # "艾灸邊個穴位"
    re.compile(r"針灸(?:係|點|咩|邊)"),  # "針灸係點做"
    re.compile(r"拔罐(?:係|點|咩|邊)"),  # "拔罐係點做"
    re.compile(r"推拿(?:係|點|咩|邊)"),  # "推拿係點做"
)

# 单字母 / 极短答案 — 这些必然是 journey answer, 不是 content question.
_LETTER_ANSWER = re.compile(r"^\s*[a-cA-C][\s.呀啊吖嗎么麼]*$")

# Bot 上一句结尾如果系明显嘅 journey question marker, 用户嘅短答案就系 journey answer.
# 这些 hints 仅用作 secondary check — 主信号系 message 本身嘅 wh-word.
_BOT_QUESTION_TAIL_HINTS = (
    "几耐", "幾耐", "几时", "幾時", "几多", "幾多", "边度", "邊度",
    "你住", "住边", "住邊", "几岁", "幾歲",
    # Q1-Q5 question stems
    "精神点", "精神點", "容易攰", "瞓得好", "最近 mood",
    "怕冷", "怕热", "怕熱", "消化点", "消化點",
)


@dataclass(frozen=True)
class IntentYieldResult:
    """Outcome of intent classification.

    `is_content_question` — True 表示要 yield (先答内容).
    `signal` — 简短解释为什么 (debugging/tracing).
    """
    is_content_question: bool
    signal: str


def classify_intent(
    message: str,
    last_assistant_text: str = "",
) -> IntentYieldResult:
    """Classify whether the user message is a CONTENT QUESTION needing yield.

    Args:
        message: The current user message (raw, post-merge).
        last_assistant_text: The previous bot turn text. Used to detect
            obvious "user is answering bot's question" cases.

    Returns:
        IntentYieldResult — `is_content_question=True` 时 prompt 应该
        inject yield block.
    """
    if not message or not isinstance(message, str):
        return IntentYieldResult(False, "empty_message")

    msg = message.strip()

    # Fast exit: single A/B/C letter → always journey answer.
    if _LETTER_ANSWER.match(msg):
        return IntentYieldResult(False, "letter_answer")

    # Content-first: check patterns at ANY length before using character count
    # as a signal. Character count is NOT a reliable proxy for intent —
    # "穴位呢?" is 4 chars but is clearly a content question; "我住沙田" is
    # 5 chars but is a journey answer. Content patterns are the right primitive.
    for pat in _CONTENT_QUESTION_PATTERNS:
        if pat.search(msg):
            return IntentYieldResult(True, f"content_keyword:{pat.pattern[:30]}")

    # No content pattern matched → journey answer or elaboration.
    # Use length only here as a label, NOT as a gate that bypasses content checks.
    if len(msg) <= 6:
        return IntentYieldResult(False, "short_answer")
    return IntentYieldResult(False, "elaboration_no_wh")


def build_yield_block(result: IntentYieldResult) -> str:
    """Render the dynamic prompt block telling Jessica to yield this turn.

    Returns empty string when no yield needed (caller can concatenate freely).
    Block size budget: ≤ 500 chars (CLAUDE.md §3.6 prompt budget).
    """
    if not result.is_content_question:
        return ""

    return (
        "\n\n⚠️ **INTENT YIELD (本 turn 必须先答内容, 唔好推 journey)**\n"
        "用户刚刚问咗一条 **内容问题** (求帮助/求方法/求解释), 唔系答 journey question。\n"
        "→ 先 call `find_knowledge_cards(query, exclude_explored=true)` 答佢嘅问题。\n"
        "→ **唔好** 同 turn 推 journey (e.g. 唔好问 Q1 / 唔好 request_tongue)。\n"
        "→ 答完 + 加 1 条 caring follow-up question, 下一 turn 自然 resume journey。\n"
        f"  (signal: {result.signal})"
    )
