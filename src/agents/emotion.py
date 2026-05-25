"""Emotion detection for TCM 情志調理 (Qing Zhi Tiao Li).

In TCM, the Seven Emotions (七情) directly affect the corresponding organs:
  思 (pensiveness/overthinking) → 脾 (spleen)
  怒 (anger)                   → 肝 (liver)
  悲/憂 (sadness/grief)        → 肺 (lung)
  恐/驚 (fear/fright)          → 腎 (kidney)
  喜 (excessive joy)           → 心 (heart)  ← rare, not mapped here

When a user mentions emotional distress, Jessica connects it to the
affected organ, probes for related physical symptoms, and suggests the
relevant soup/care angle — naturally, without a hard sales pitch.

Usage:
    from src.agents.emotion import detect_emotion, EmotionSignal
    signal = detect_emotion("好大壓力，諗嘢諗唔停")
    # EmotionSignal(emotion_zh="壓力/思慮", organ_zh="脾", ...)
"""

from __future__ import annotations

from typing import NamedTuple


class EmotionSignal(NamedTuple):
    """Parsed emotion signal with TCM mapping."""

    emotion_zh: str          # Human-readable label, e.g. "壓力/思慮"
    tcm_emotion: str         # 七情 label, e.g. "思"
    organ_zh: str            # Affected organ, e.g. "脾"
    imbalance_zh: str        # TCM imbalance phrase, e.g. "思慮傷脾"
    probe_symptoms: tuple    # Physical symptoms to probe, e.g. ("肚脹", "唔想食")
    soup_angle: str          # Care angle for Writer, e.g. "健脾益氣、安神定志"
    faq_query: str           # Enriched query string for FAQ Agent KB search


# ---------------------------------------------------------------------------
# Emotion → Organ mappings
# Each entry: (trigger_keywords, EmotionSignal)
# Order matters — first match wins. More specific first.
# ---------------------------------------------------------------------------

_EMOTION_ENTRIES: list[tuple[tuple[str, ...], EmotionSignal]] = [
    # ── 思 → 脾 (stress / overthinking — most common in HK urban context)
    (
        (
            "壓力好大", "好大壓力", "大壓力", "壓力爆燈",
            "諗太多", "諗嘢諗唔停", "唔停咁諗",
            "擔心好多", "好擔心", "擔憂", "焦慮",
            "煩惱", "唔放得低", "放唔低", "思慮",
            "腦袋停唔到", "停唔到諗",
        ),
        EmotionSignal(
            emotion_zh="壓力/思慮",
            tcm_emotion="思",
            organ_zh="脾",
            imbalance_zh="思慮過度傷脾，脾氣受損",
            probe_symptoms=("肚脹", "唔想食嘢", "食完唔消化", "記性差", "頭腦混沌"),
            soup_angle="健脾益氣、安神定志",
            faq_query="壓力大 脾虛 消化 失眠 養生",
        ),
    ),
    # ── 怒 → 肝 (anger / frustration)
    (
        (
            "好嬲", "發脾氣", "激嬲", "忟憎",
            "火大", "好火", "肝火", "易怒",
            "煩死", "好煩", "激氣", "激到",
        ),
        EmotionSignal(
            emotion_zh="憤怒/鬱悶",
            tcm_emotion="怒",
            organ_zh="肝",
            imbalance_zh="怒氣傷肝，肝氣鬱結",
            probe_symptoms=("兩側頭痛", "眼睛乾澀", "脅肋不適", "口苦", "胸口鬱悶"),
            soup_angle="疏肝解鬱、清肝明目",
            faq_query="肝鬱 疏肝 頭痛 眼睛 養生",
        ),
    ),
    # ── 悲/憂 → 肺 (sadness / grief)
    (
        (
            "好傷心", "好難過", "好唔開心",
            "失落", "心情差", "灰心", "唔開心",
            "無心機", "情緒低落", "抑鬱",
            "喊咗", "喊咁多", "想喊",
        ),
        EmotionSignal(
            emotion_zh="悲傷/憂鬱",
            tcm_emotion="悲",
            organ_zh="肺",
            imbalance_zh="悲憂傷肺，肺氣鬱閉",
            probe_symptoms=("氣短", "容易攰", "皮膚乾", "唔想出門", "胸口悶"),
            soup_angle="潤肺養心、疏解憂鬱",
            faq_query="肺氣虛 情緒 潤肺 養心 養生",
        ),
    ),
    # ── 恐/驚 → 腎 (fear / anxiety / fright)
    (
        (
            "好驚", "害怕", "驚恐", "恐懼",
            "睡唔著", "失眠", "心跳好快", "心悸",
            "夜晚驚醒", "好緊張", "緊張到",
        ),
        EmotionSignal(
            emotion_zh="驚恐/緊張",
            tcm_emotion="恐",
            organ_zh="腎",
            imbalance_zh="恐懼傷腎，腎氣不固",
            probe_symptoms=("腰酸", "夜尿多", "耳鳴", "記性差", "手腳冷"),
            soup_angle="補腎安神、定志寧心",
            faq_query="腎虛 失眠 心悸 安神 養生",
        ),
    ),
]

# Broad single-word fallback for "壓力" alone (lower specificity — check last)
_BROAD_STRESS_KEYWORDS = ("壓力",)  # "好煩" maps to 肝 via anger entry


def detect_emotion(text: str) -> EmotionSignal | None:
    """Return the first matching EmotionSignal for the given text, or None.

    Matches in priority order: specific multi-word phrases first, then
    broad single keywords. Returns None if no emotional signal is found.

    Args:
        text: Raw user message (Cantonese).

    Returns:
        EmotionSignal or None.
    """
    if not text:
        return None

    # Try each entry in priority order (specific → broad)
    for keywords, signal in _EMOTION_ENTRIES:
        if any(kw in text for kw in keywords):
            return signal

    # Broad "壓力" fallback → maps to the 思/脾 entry (index 0)
    if any(kw in text for kw in _BROAD_STRESS_KEYWORDS):
        return _EMOTION_ENTRIES[0][1]

    return None
