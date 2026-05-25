"""24 Solar Terms (節氣) data + detection for TCM Jessica proactive care.

Each term has:
  - date for 2026 and 2027 (hardcoded from HK Observatory solar term table)
  - TCM advice aligned with the classic 養生 principle for that term
  - condition_code used as broadcast dedup key

Detection window: ±2 days around the term date. If today is within the
window AND the user hasn't received this term's broadcast this year →
eligible for the solar term tip.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, timedelta


@dataclass(frozen=True)
class SolarTerm:
    name_zh: str          # e.g. "冬至"
    name_en: str          # e.g. "winter_solstice"
    dates: list[date]     # one date per year (2026, 2027, ...)
    tcm_focus_zh: str     # 1-liner on what to nourish this term
    season_tip_zh: str    # 1-2 sentences of actionable advice
    organ_zh: str         # which organ is in focus

    @property
    def condition_code(self) -> str:
        return f"solar_{self.name_en}"


# ---------------------------------------------------------------------------
# 24 Solar Terms — 2026 + 2027 dates (HK Observatory table)
# TCM advice from 《黃帝內經》四時養生 + standard HK TCM clinical guidelines
# ---------------------------------------------------------------------------

SOLAR_TERMS: list[SolarTerm] = [
    SolarTerm(
        name_zh="立春", name_en="lichun",
        dates=[date(2026, 2, 4), date(2027, 2, 4)],
        tcm_focus_zh="養肝疏肝",
        season_tip_zh="立春係一年起點，中醫講「春養肝」。多食韭菜、薺菜疏肝升陽，少食酸收，保持好心情讓肝氣流通。",
        organ_zh="肝",
    ),
    SolarTerm(
        name_zh="雨水", name_en="yushui",
        dates=[date(2026, 2, 19), date(2027, 2, 18)],
        tcm_focus_zh="健脾祛濕",
        season_tip_zh="雨水後濕氣漸重，脾胃最怕濕。飲薏米赤小豆水祛濕，少食生冷，保護脾胃係關鍵。",
        organ_zh="脾",
    ),
    SolarTerm(
        name_zh="驚蟄", name_en="jingzhe",
        dates=[date(2026, 3, 6), date(2027, 3, 6)],
        tcm_focus_zh="升陽護肝",
        season_tip_zh="驚蟄陽氣升發，情緒容易波動。適合適量運動，早瞓早起，疏肝解鬱，飲菊花杞子茶明目舒肝。",
        organ_zh="肝",
    ),
    SolarTerm(
        name_zh="春分", name_en="chunfen",
        dates=[date(2026, 3, 20), date(2027, 3, 20)],
        tcm_focus_zh="陰陽平衡",
        season_tip_zh="春分晝夜等長，飲食要均衡。多食時令蔬菜，少食辛辣，作息規律，保持陰陽平衡係今日重點。",
        organ_zh="肝",
    ),
    SolarTerm(
        name_zh="清明", name_en="qingming",
        dates=[date(2026, 4, 5), date(2027, 4, 5)],
        tcm_focus_zh="祛濕升清",
        season_tip_zh="清明前後香港潮濕，濕氣困脾。飲粟米鬚茶利水祛濕，早晚散步升清陽，唔好成日坐住唔郁。",
        organ_zh="脾",
    ),
    SolarTerm(
        name_zh="穀雨", name_en="guyu",
        dates=[date(2026, 4, 20), date(2027, 4, 20)],
        tcm_focus_zh="健脾利濕",
        season_tip_zh="穀雨是春末最後一個節氣，濕熱開始。煲冬瓜荷葉湯清熱祛濕，少食肥膩，為夏天來臨做準備。",
        organ_zh="脾",
    ),
    SolarTerm(
        name_zh="立夏", name_en="lixia",
        dates=[date(2026, 5, 6), date(2027, 5, 6)],
        tcm_focus_zh="養心清暑",
        season_tip_zh="立夏開始養心，紅色食物最補心——紅棗、番茄、紅豆。唔好熬夜，心火盛容易失眠，午休 20 分鐘最好。",
        organ_zh="心",
    ),
    SolarTerm(
        name_zh="小滿", name_en="xiaoman",
        dates=[date(2026, 5, 21), date(2027, 5, 21)],
        tcm_focus_zh="清熱祛濕防暑",
        season_tip_zh="小滿後香港又熱又濕，暑濕困脾最常見。飲五花茶清熱，少食煎炸，冷氣房要加件外套護頸背。",
        organ_zh="脾心",
    ),
    SolarTerm(
        name_zh="芒種", name_en="mangzhong",
        dates=[date(2026, 6, 6), date(2027, 6, 6)],
        tcm_focus_zh="清心解暑",
        season_tip_zh="芒種暑熱漸盛，心火易旺。多飲溫水少飲凍飲，荷葉冬瓜湯清暑利濕，避免烈日下長時間活動。",
        organ_zh="心",
    ),
    SolarTerm(
        name_zh="夏至", name_en="xiazhi",
        dates=[date(2026, 6, 21), date(2027, 6, 22)],
        tcm_focus_zh="養心補陽",
        season_tip_zh="夏至陽氣最旺，係「冬病夏治」天灸嘅黃金時機。虛寒體質、鼻敏感人士可以考慮做三伏天灸，預防秋冬發作。",
        organ_zh="心",
    ),
    SolarTerm(
        name_zh="小暑", name_en="xiaoshu",
        dates=[date(2026, 7, 7), date(2027, 7, 7)],
        tcm_focus_zh="防中暑清暑濕",
        season_tip_zh="小暑暑氣最重，防中暑最關鍵。多飲綠豆湯、竹蔗茅根水，避免下午 12–3 時外出，頭頸記得防曬。",
        organ_zh="心",
    ),
    SolarTerm(
        name_zh="大暑", name_en="dashu",
        dates=[date(2026, 7, 23), date(2027, 7, 23)],
        tcm_focus_zh="清熱解暑益氣",
        season_tip_zh="大暑係一年最熱，消耗大量陽氣。飲花旗蔘茶清補提神，少食冷飲傷脾，每日補充足夠水分係基本。",
        organ_zh="心脾",
    ),
    SolarTerm(
        name_zh="立秋", name_en="liqiu",
        dates=[date(2026, 8, 7), date(2027, 8, 7)],
        tcm_focus_zh="潤燥養肺",
        season_tip_zh="立秋開始養肺。白色食物最潤肺——銀耳、百合、梨、蓮藕。香港秋天仍熱，但早晚溫差開始大，記得帶薄外套。",
        organ_zh="肺",
    ),
    SolarTerm(
        name_zh="處暑", name_en="chushu",
        dates=[date(2026, 8, 23), date(2027, 8, 23)],
        tcm_focus_zh="潤燥生津",
        season_tip_zh="處暑後暑熱漸退，燥氣登場。多食潤燥食物（雪梨、蜂蜜），少食辛辣，補充水分，皮膚乾燥係燥邪信號。",
        organ_zh="肺",
    ),
    SolarTerm(
        name_zh="白露", name_en="bailu",
        dates=[date(2026, 9, 8), date(2027, 9, 8)],
        tcm_focus_zh="收斂養肺",
        season_tip_zh="白露晝夜溫差加大，是感冒高峰期。加衣保暖尤其頸部，飲雪梨陳皮水潤肺止燥咳，少食生冷涼物。",
        organ_zh="肺",
    ),
    SolarTerm(
        name_zh="秋分", name_en="qiufen",
        dates=[date(2026, 9, 23), date(2027, 9, 23)],
        tcm_focus_zh="平衡陰陽養肺腎",
        season_tip_zh="秋分後陰氣漸重。養肺同時開始補腎，黑芝麻、核桃、山藥都係好選擇，作息調整為「早瞓早起」。",
        organ_zh="肺腎",
    ),
    SolarTerm(
        name_zh="寒露", name_en="hanlu",
        dates=[date(2026, 10, 8), date(2027, 10, 8)],
        tcm_focus_zh="養陰補腎",
        season_tip_zh="寒露後天氣轉涼，腎陽開始需要保護。泡腳暖身、多食黑色食物補腎，避免深夜受寒，腰腎最怕凍。",
        organ_zh="腎",
    ),
    SolarTerm(
        name_zh="霜降", name_en="shuangjiang",
        dates=[date(2026, 10, 23), date(2027, 10, 23)],
        tcm_focus_zh="健脾補腎防寒",
        season_tip_zh="霜降係秋天最後一個節氣，進補好時機。可以開始飲滋補湯水，脾腎雙補，為冬天儲存能量。",
        organ_zh="脾腎",
    ),
    SolarTerm(
        name_zh="立冬", name_en="lidong",
        dates=[date(2026, 11, 7), date(2027, 11, 7)],
        tcm_focus_zh="補腎藏陽",
        season_tip_zh="立冬係冬天開始，中醫講「冬藏」。補腎食物：核桃、黑芝麻、羊肉、韭菜。早瞓晚起，保護陽氣唔外泄。",
        organ_zh="腎",
    ),
    SolarTerm(
        name_zh="小雪", name_en="xiaoxue",
        dates=[date(2026, 11, 22), date(2027, 11, 22)],
        tcm_focus_zh="溫陽補腎",
        season_tip_zh="小雪後陰氣最盛，容易情緒低落。中醫建議曬太陽補充陽氣，飲薑棗茶暖胃，運動唔宜過激——散步最合適。",
        organ_zh="腎心",
    ),
    SolarTerm(
        name_zh="大雪", name_en="daxue",
        dates=[date(2026, 12, 7), date(2027, 12, 7)],
        tcm_focus_zh="溫補腎陽",
        season_tip_zh="大雪是冬季進補最佳時期。每晚用熱水泡腳至微微出汗，加薑片效果更好，引火歸元，全身暖和一整夜。",
        organ_zh="腎",
    ),
    SolarTerm(
        name_zh="冬至", name_en="dongzhi",
        dates=[date(2026, 12, 22), date(2027, 12, 22)],
        tcm_focus_zh="補腎壯陽固本",
        season_tip_zh="冬至係陰氣極盛、陽氣初生嘅轉折點，最適合進補。食湯圓象徵團圓，同時係補腎陽嘅好時機——羊肉、韭菜、黑豆都啱。",
        organ_zh="腎",
    ),
    SolarTerm(
        name_zh="小寒", name_en="xiaohan",
        dates=[date(2027, 1, 6), date(2028, 1, 5)],
        tcm_focus_zh="補腎禦寒",
        season_tip_zh="小寒係全年最冷時期之一，腎陽消耗大。做三九灸補陽效果最好，日常多食補腎食物，出門護好頭頸腰腎。",
        organ_zh="腎",
    ),
    SolarTerm(
        name_zh="大寒", name_en="dahan",
        dates=[date(2027, 1, 20), date(2028, 1, 20)],
        tcm_focus_zh="固本培元迎春",
        season_tip_zh="大寒係冬季最後一個節氣，準備迎接立春。收尾補腎同時開始疏肝，飲點薑棗茶暖胃，作息規律迎接新一年陽氣升發。",
        organ_zh="腎肝",
    ),
]

# Quick lookup by name
_BY_NAME: dict[str, SolarTerm] = {t.name_zh: t for t in SOLAR_TERMS}

# ---------------------------------------------------------------------------
# Detection
# ---------------------------------------------------------------------------

DETECTION_WINDOW_DAYS = 2   # fire within ±2 days of the solar term date


def get_active_solar_term(today: date | None = None) -> SolarTerm | None:
    """Return the solar term currently active (within ±2 days), or None.

    Picks the CLOSEST term if multiple are in range (edge case near year boundary).
    """
    if today is None:
        from datetime import date as _date
        today = _date.today()

    best: SolarTerm | None = None
    best_dist = DETECTION_WINDOW_DAYS + 1

    for term in SOLAR_TERMS:
        for term_date in term.dates:
            dist = abs((today - term_date).days)
            if dist <= DETECTION_WINDOW_DAYS and dist < best_dist:
                best = term
                best_dist = dist

    return best


def solar_term_condition_code_for_year(term: SolarTerm, year: int) -> str:
    """Unique code per term per year — prevents re-sending same term next year."""
    return f"solar_{term.name_en}_{year}"
