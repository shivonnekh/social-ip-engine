"""Pitch-path router (Option C, 2026-05-20).

Decides whether a user's complaint should be pitched via:
  - "catalog"  — 心宜中醫 paid catalog (soups + ointments)
  - "maca"     — legacy Maca (energy / 性 / general wellness)
  - "unclear"  — neither pattern matches; LLM defaults to catalog

Logic is deterministic (keyword match on complaint text). The result is
injected into the Jessica prompt as a STRONG HINT, NOT a hard force —
LLM still picks the tool, but with clear guidance. This preserves
conversational flexibility while making routing predictable.

ONE pitch path per session. Cross-rejection in share_product +
share_paid_items prevents pitching both.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Final, Literal

PitchPath = Literal["catalog", "maca", "unclear"]


# Catalog covers: skin, digestion, sleep, cough, headache, eye, immunity,
# beauty/hormonal. Maca is reserved for: energy / 性 / general wellness
# that doesn't map to a specific catalog product.
_CATALOG_KEYWORDS: Final[tuple[str, ...]] = (
    # Skin
    "皮膚", "痕", "癢", "濕疹", "暗瘡", "痘", "敏感", "過敏", "紅疹",
    "生蛇", "手足口", "皮膚乾", "脫皮", "蕁麻疹",
    # Digestion
    "胃脹", "消化", "便秘", "肚瀉", "屙", "腹脹", "胃痛", "胃熱",
    "腸胃", "脾胃",
    # Sleep / mental
    "失眠", "瞓唔到", "瞓唔好", "瞓得唔好", "發夢", "多夢", "夜醒",
    "心火盛", "捱夜",
    # Respiratory
    "咳", "喉嚨", "聲沙", "感冒", "流感", "痰", "鼻塞", "流鼻水",
    "鼻敏感", "氣管", "氣喘",
    # Head / pain
    "頭痛", "頭暈", "偏頭痛", "頭脹", "頭重",
    # Eye / liver-related
    "眼乾", "眼澀", "眼疲勞", "流眼水", "視力",
    # Immunity / recovery / hormonal
    "免疫力", "病後", "術後", "康復", "抗病毒", "更年期", "月經不調",
    "荷爾蒙", "養顏", "美容", "口乾", "口苦", "上火", "熱氣",
)

_MACA_KEYWORDS: Final[tuple[str, ...]] = (
    # Energy / fatigue specifically (general wellness)
    "易攰", "成日攰", "好攰", "精神差", "冇精神", "提不起勁",
    "無力", "疲倦", "活力", "動能",
    # 性 / kidney yang
    "性功能", "性慾", "性能力", "陽痿", "早洩", "腎陽虛",
    "補腎陽", "腰膝", "怕冷",
    # General wellness / preventive
    "養生", "強身", "進補",
)


@dataclass(frozen=True)
class PitchDecision:
    path: PitchPath
    matched_keywords: tuple[str, ...]
    reason: str

    def to_prompt_hint(self) -> str:
        """Render as a one-line strong hint for injection into the LLM prompt."""
        if self.path == "catalog":
            kw = "、".join(self.matched_keywords[:3])
            return (
                f"💡 PITCH PATH HINT: 主訴包含 [{kw}] → 用 **catalog** (心宜中醫 "
                f"湯水 / 藥膏)。Call `recommend_paid_item` + `share_paid_items`. "
                f"⛔ 唔好 pitch Maca (`share_product`) — Maca 同 catalog "
                f"二選一，唔好同一個 session 推兩種。"
            )
        if self.path == "maca":
            kw = "、".join(self.matched_keywords[:3])
            return (
                f"💡 PITCH PATH HINT: 主訴包含 [{kw}] → 用 **Maca** (能量/"
                f"性/養生產品)。Call `share_product` with 瑪卡 pitch. "
                f"⛔ 唔好 pitch catalog (`recommend_paid_item` / "
                f"`share_paid_items`) — Maca 同 catalog 二選一。"
            )
        # unclear
        return (
            "💡 PITCH PATH HINT: 主訴模糊，default 用 **catalog** "
            "(`recommend_paid_item` + `share_paid_items`) — 覆蓋面闊啲。"
            "⛔ 唔好同一個 session pitch 兩種 (Maca + catalog)。"
        )


def determine_pitch_path(
    complaint: str | None, all_user_messages: str | None = None
) -> PitchDecision:
    """Decide pitch path from complaint text + optional broader signal.

    Args:
        complaint: The recorded `sales_state.complaint` field (primary signal).
        all_user_messages: Optional concatenated user messages this session
            (secondary signal — catches complaints user added later that
            didn't end up in `complaint` field).

    Returns:
        PitchDecision with path + matched keywords + reason.
    """
    blob = " ".join(
        s for s in (complaint, all_user_messages) if s
    ).lower()

    if not blob.strip():
        return PitchDecision(
            path="unclear",
            matched_keywords=(),
            reason="no complaint text yet",
        )

    catalog_hits = tuple(
        kw for kw in _CATALOG_KEYWORDS if kw in blob
    )
    maca_hits = tuple(
        kw for kw in _MACA_KEYWORDS if kw in blob
    )

    # Catalog wins ties — broader coverage, more specific products.
    if catalog_hits:
        return PitchDecision(
            path="catalog",
            matched_keywords=catalog_hits,
            reason=f"matched {len(catalog_hits)} catalog keyword(s)",
        )
    if maca_hits:
        return PitchDecision(
            path="maca",
            matched_keywords=maca_hits,
            reason=f"matched {len(maca_hits)} Maca keyword(s)",
        )

    return PitchDecision(
        path="unclear",
        matched_keywords=(),
        reason="no keyword match in catalog or Maca lists",
    )
