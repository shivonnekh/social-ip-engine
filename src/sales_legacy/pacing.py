"""Jessica 销售旅程 — Pacing 检测器 (A4 Compress Mode).

用户 feedback (wa_60164245634, T12): "1 问 1 答, 太机械".
Bot 机械 grind 5Q quiz, 用户 push back ("you ask too much"), bot 道歉
之后又问下一题 — 完全冇 feedback loop.

呢个 module 检测 fatigue / pushback 信号, set sales_state.pacing_compress=true.
检测后:
  - sales_prompt 注入 COMPRESS MODE block (跳剩低 Q1-Q5)
  - declare_constitution 放宽 precondition (≥2 Q + tongue OR pacing_compress)
  - bot 停问, 让 user lead

检测策略: 纯 regex/keyword (deterministic, fast, 无 LLM call)。
"""
from __future__ import annotations

import re

# 直接说: 你问太多 / ask too much / 好烦
_DIRECT_PATTERNS: tuple[re.Pattern, ...] = (
    re.compile(r"你問太多|你问太多|問太多|问太多|問咁多|问咁多|問甘多|问甘多"),
    re.compile(r"ask\s+too\s+much|too\s+many\s+question", re.IGNORECASE),
    re.compile(r"you\s+ask\s+too\s+much", re.IGNORECASE),
    re.compile(r"好煩|好烦|煩|烦$|annoying", re.IGNORECASE),
)

# 避让: 算啦 / 唔好问咁多 / stop asking
_AVOID_PATTERNS: tuple[re.Pattern, ...] = (
    re.compile(r"算啦|算了|唔好問|不好问|可唔可以唔好|可不可以不要"),
    re.compile(r"stop\s+ask|enough\s+question", re.IGNORECASE),
)

# 拒绝: 唔答 / 唔想答 / skip / 下一步
_REFUSE_PATTERNS: tuple[re.Pattern, ...] = (
    re.compile(r"唔答|不答|唔想答|不想答|懒得答|懶得答"),
    re.compile(r"^\s*skip\s*$", re.IGNORECASE),
    re.compile(r"下一步|下一題|下一题|跳過|跳过"),
)

# 短答 (≤3 chars after strip) — 单独唔算 pushback, 但连续 2 turn 算。
_SHORT_TOKENS: frozenset[str] = frozenset({
    "yes", "no", "ok", "嗯", "好", "係", "系", "唔", "不",
    "normal", "一般", "ya", "ya.", "yep", "nah",
})

# A/B/C scripted Q answers — 呢种系预期答案, 唔算 fatigue 信号。
# Bug fix 2026-04-30: 用户答 "b" + "c" (Q1+Q2 scripted answers) 被误判为
# consecutive_short_answers → pacing_compress 触发 → declare_constitution
# 在只有 Q1+Q2 时被解锁 → 5Q expansion 失效。
_QUIZ_LETTER_RE = re.compile(r"^\s*[ABCabc][\s\.\!。，,]*$")


def _is_quiz_letter_answer(text: str) -> bool:
    """单独 A/B/C/a/b/c (含 trailing 标点) — scripted Q 嘅预期答案。"""
    return bool(_QUIZ_LETTER_RE.match(text or ""))


def _is_short_answer(text: str) -> bool:
    """≤3 chars 或 single token 算短答 (用作连续短答 fatigue 信号)。
    A/B/C 答案唔算 — 呢啲系 scripted Q 嘅预期 input。"""
    stripped = (text or "").strip()
    if not stripped:
        return False
    # Quiz letter answer is EXPECTED — not a fatigue signal
    if _is_quiz_letter_answer(stripped):
        return False
    if len(stripped) <= 3:
        return True
    return stripped.lower() in _SHORT_TOKENS


def _matches_any(patterns: tuple[re.Pattern, ...], text: str) -> bool:
    return any(p.search(text) for p in patterns)


def detect_pushback(message: str, conversation_history: list[dict] | None = None) -> tuple[bool, str]:
    """检测 user 嘅 fatigue / pushback 信号。

    Returns (compress_mode, reason)。reason 用作 telemetry / tracer log。

    Args:
        message: 用户当前 message (raw text)
        conversation_history: 用作检测连续短答 pattern。每个 entry 有
            'role' ('user'|'assistant') + 'content' (str)。可省略。
    """
    text = (message or "").strip()
    if not text:
        return False, ""

    if _matches_any(_DIRECT_PATTERNS, text):
        return True, "direct_pushback"
    if _matches_any(_AVOID_PATTERNS, text):
        return True, "avoid_pushback"
    if _matches_any(_REFUSE_PATTERNS, text):
        return True, "refuse_pushback"

    # 连续 2 turn 短答 (current + 上一 user turn)
    if _is_short_answer(text) and conversation_history:
        prev_user_msgs = [
            (h.get("content") or "")
            for h in reversed(conversation_history)
            if (h.get("role") or "") == "user"
        ]
        # 上一 user message 都短 → 2 turn 短答 fatigue
        if prev_user_msgs and _is_short_answer(prev_user_msgs[0]):
            return True, "consecutive_short_answers"

    return False, ""


def build_compress_block(sales_state: dict) -> str:
    """Render dynamic prompt block when pacing_compress=true.

    Caller must check sales_state.pacing_compress 先 call. 返一段短 block
    (≤400 chars) 注入到 Jessica prompt — 唔系 always-on 静态 instruction。
    """
    answers = sales_state.get("constitution_answers") or {}
    answered = sum(1 for k in ("q1", "q2", "q3", "q4", "q5") if answers.get(k))
    has_tongue = bool(sales_state.get("tongue_findings"))

    # 2026-04-30: declare_constitution 严格 require 5/5 — user explicit
    # requirement「至少要问满 5 条问题, 才判断他的体质」。Compress mode
    # 唔再 bypass declare; 而系 PIVOT 去其他 angle (clinic / 让 user lead)。
    return (
        "\n⚠️ **COMPRESS MODE 已激活** (user signaled fatigue):\n"
        f"  - 已答 Q: {answered}/5, 脷相: {'有' if has_tongue else '冇'}\n"
        "  - **唔好** 即时 declare_constitution (tool 仍然要求 5/5 全答)\n"
        "  - **唔好** 继续机械 grind Q3-Q5\n"
        "  - **应该**: 温柔 acknowledge ('唔好意思问咁多 😊'), 然后 pivot:\n"
        "    (a) 邀请见医师 ('其实呢类问题嚟 clinic 面诊更精准 🌿 想了解嗎?')\n"
        "    (b) 或者 let user lead ('你有冇咩想知?')\n"
        "  - 用户主动想继续 → 再问剩低嘅 Q\n"
    )
