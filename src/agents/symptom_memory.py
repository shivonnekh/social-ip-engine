"""Symptom memory — detects recurring symptoms across conversation history.

Scans the last N user messages for repeated symptom keywords. If the same
symptom appears >= threshold times, returns it as the recurring symptom.

This runs cheaply (pure keyword matching, no LLM) at the end of
_rule_overrides() as a catch-all for sessions where no other rule fired.
"""

from __future__ import annotations

from collections import Counter

from src.crm.models import User


# Maps symptom label → tuple of Cantonese trigger phrases.
# Order matters: extract_symptom_from_text returns the FIRST matching group.
_SYMPTOM_GROUPS: list[tuple[str, tuple[str, ...]]] = [
    ("頭痛", ("頭痛", "頭好痛", "頭疼", "偏頭痛", "頭暈")),
    ("失眠", ("失眠", "睡唔著", "唔瞓得著", "瞓唔好", "夜晚醒", "唔夠瞓")),
    ("肩頸痛", ("肩頸", "頸痛", "膊頭痛", "頸梗", "肩膊")),
    ("胃痛/消化差", ("胃唔舒服", "胃痛", "肚唔舒服", "消化差", "唔想食", "食唔落", "肚脹")),
    ("疲勞", ("好攰", "無氣力", "好累", "攰到", "無精神", "精神差")),
    ("皮膚問題", ("皮膚差", "暗瘡", "濕疹", "皮膚痕", "出疹")),
    ("情緒低落", ("唔開心", "心情差", "情緒低落", "好憂鬱", "好悲")),
    ("腰痛", ("腰痛", "腰酸", "下背痛", "腰唔舒服")),
]


def extract_symptom_from_text(text: str) -> str | None:
    """Scan text against all symptom groups; return the label of the first match.

    Returns None if no group matches. When multiple groups could match,
    the group listed first in _SYMPTOM_GROUPS wins (deterministic ordering).
    """
    if not text:
        return None
    for label, phrases in _SYMPTOM_GROUPS:
        if any(phrase in text for phrase in phrases):
            return label
    return None


def detect_recurring_symptom(
    user: User,
    window: int = 10,
    threshold: int = 3,
) -> str | None:
    """Detect whether the user has repeated the same symptom across recent history.

    Scans the last `window` messages where role == "user". Counts how many
    times each symptom label appears. Returns the most common label if its
    count >= threshold, else None.

    Tie-breaking: if two symptom labels share the highest count, the one
    that also appears in `user.pain_points` wins. If neither (or both)
    appear in pain_points, fall back to the group ordering in _SYMPTOM_GROUPS
    (whichever comes first in the list wins).

    Args:
        user: CRM snapshot; reads conversation_history and pain_points.
        window: how many of the most recent messages to scan.
        threshold: minimum count to consider a symptom "recurring".

    Returns:
        A symptom label string (e.g. "頭痛") or None.
    """
    if not user.conversation_history:
        return None

    # Take the last `window` messages, filter to user-only.
    recent = list(user.conversation_history)[-window:]
    user_messages = [msg for msg in recent if msg.role == "user"]

    if not user_messages:
        return None

    counts: Counter[str] = Counter()
    for msg in user_messages:
        label = extract_symptom_from_text(msg.content)
        if label is not None:
            counts[label] += 1

    if not counts:
        return None

    max_count = counts.most_common(1)[0][1]
    if max_count < threshold:
        return None

    # All labels that share the top count.
    top_labels = [label for label, cnt in counts.items() if cnt == max_count]

    if len(top_labels) == 1:
        return top_labels[0]

    # Tie-break 1: prefer a label that appears in pain_points.
    pain_points = user.pain_points or []
    for label in top_labels:
        if label in pain_points:
            return label

    # Tie-break 2: whichever appears first in _SYMPTOM_GROUPS ordering.
    group_order = [label for label, _ in _SYMPTOM_GROUPS]
    for label in group_order:
        if label in top_labels:
            return label

    # Fallback (shouldn't be reached, but be safe).
    return top_labels[0]
