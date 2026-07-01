"""Final Writer Agent — composes 1 final reply from all specialist outputs.

The Writer is the SOLE producer of user-facing text. Every specialist
returns structured intent; the Writer turns it into HK Cantonese bubbles.

Why a separate Writer (CLAUDE.md §3.6):
- Single Jessica voice — 5 specialists writing copy = 5 voices.
- HK 廣東話口語 polish lives here, once.
- Bubble-split rhythm tuning belongs in one place.
- Tone calibration based on CRM status happens here.
- Conflict resolution when 2 specialists disagree happens here.

The Writer is FORBIDDEN to invent medical / product / pricing /
appointment facts. It can only RE-NARRATE what specialists provided
in `payload`.
"""

from __future__ import annotations

import json
import logging
import re
from typing import Any

from src.llm import DEFAULT_MODEL, LLMClient

from src.agents.base import (
    PlannerDecision,
    SpecialistName,
    SpecialistOutput,
    WriterOutput,
)
from src.crm.models import User, UserStatus
from src.personas.profile import PersonaProfile
from src.tools import prompt_overrides

logger = logging.getLogger("agents.writer")

MAX_BUBBLES = 5
# Sales pitches need more headroom: empathy + safety + intro + N products
# + backstop + CTA can easily reach 7-8 bubbles for a 3-product pitch.
# When Sales surfaces ≥2 products, we extend the cap so the Writer doesn't
# silently truncate a product bubble (production bug 2026-05-26: announced
# "3 款湯水" but only 2 rendered because bubbles[5] got dropped).
MAX_BUBBLES_PITCH = 8

# ── English-persona CJK enforcement (bug fix 2026-07-01) ────────────────────
# Unicode ranges covering Chinese/Cantonese script (CJK Unified Ideographs +
# common extensions). Cantonese has no separate script from Mandarin — both
# are written with Han characters — so a Han-script scan is sufficient to
# catch either.
_CJK_RE = re.compile(r"[\u4e00-\u9fff\u3400-\u4dbf\uf900-\ufaff]")

_ENGLISH_ONLY_RETRY_REMINDER = (
    "\n\n⚠️⚠️⚠️ CRITICAL: your previous reply contained Chinese characters. "
    "This is STRICTLY FORBIDDEN for this persona — the user only reads English. "
    "Rewrite the ENTIRE reply in English ONLY. Not a single Chinese character, "
    "not even for a TCM term (spell it out in English instead, e.g. \"Liver Yang "
    "Rising\" not \"肝陽上亢\"). ⚠️⚠️⚠️"
)

_ENGLISH_FALLBACK_MESSAGE = (
    "Sorry, I'm having a little technical hiccup right now — mind trying again "
    "in a moment? 🙏"
)


def _contains_cjk(text: str) -> bool:
    return bool(_CJK_RE.search(text))


def _bubbles_contain_cjk(bubbles: list[str]) -> bool:
    return any(_contains_cjk(b) for b in bubbles)


# Conflict resolution — when specialists disagree (e.g. FAQ "no_match"
# + Sales has products), Writer leans on the HIGHER-priority specialist
# for the primary message. Lower-priority info becomes a side mention
# only if it doesn't contradict the primary.
SPECIALIST_PRIORITY: list[SpecialistName] = [
    SpecialistName.CONSTITUTION,     # in-flow diagnostic — highest priority
    SpecialistName.TONGUE_PROGRESS,  # before/after narrative for return users
    SpecialistName.APPOINTMENT,      # active booking — concrete action
    SpecialistName.SALES,            # pitch — drives revenue
    SpecialistName.FAQ,              # educational — informational
    SpecialistName.CASUAL,           # rapport, listens — below substantive
    SpecialistName.GREETING,         # first-touch only — lowest
]


# Tone calibration — what voice to use based on user.status.
_TONE_MATRIX: dict[UserStatus, str] = {
    UserStatus.NEW: "warm + 自我介紹型 — 第一次見面，建立親切感",
    UserStatus.QUALIFIED: "好奇 + engaging — 引導用戶講多啲自己情況",
    UserStatus.CONSTITUTION_DONE: "confident + caring — 已經了解佢，建議自然",
    UserStatus.BOOKED: "reassuring + prep — 提預約細節，俾佢安心",
    UserStatus.BOUGHT: "感激 + follow-up — 關心使用效果",
    UserStatus.CHURNED: "好輕、零壓力、純關心 — 唔好 push pitch",
    UserStatus.OPTED_OUT: "(should not be reached)",
}

# English equivalent of _TONE_MATRIX — used ONLY for language="en" profiles
# (bug fix 2026-07-01). The Chinese tone matrix was being interpolated into
# every persona's system prompt regardless of language, including Jackie's —
# another direct source of Chinese-character leakage into English replies.
_TONE_MATRIX_EN: dict[UserStatus, str] = {
    UserStatus.NEW: "warm + self-introduction — first meeting, build rapport",
    UserStatus.QUALIFIED: "curious + engaging — draw out more about their situation",
    UserStatus.CONSTITUTION_DONE: "confident + caring — you know them now, suggestions feel natural",
    UserStatus.BOOKED: "reassuring + prep — confirm appointment details, put them at ease",
    UserStatus.BOUGHT: "grateful + follow-up — check in on how it's going",
    UserStatus.CHURNED: "very light, zero pressure, pure care — don't push a pitch",
    UserStatus.OPTED_OUT: "(should not be reached)",
}


_SYSTEM = """你係 Jessica — 心宜中醫嘅 WhatsApp AI teammate。

身份:
- 唔係醫師，唔做診斷
- 溫柔、人情味、有少少俏皮，HK 廣東話口語
- 永遠用「我」，唔好用「Jessica」自稱 (除非有 new_user_intro flag)
- 唔好用書面語、唔好用普通話詞 (「您」「我們」「請」「嗎」)
- 用「你」「我哋」「啦」「嘞」「啊」「㗎」

你嘅工作:
讀 specialist 比你嘅 structured intent，組合成自然嘅 WhatsApp 對話。
每個 bubble 應該短而 punchy，就好似真人發 WhatsApp 咁。

══════════════════════════════
Bubble 長度 + 數量規矩 (重要):
- 目標每個 bubble: 20-60 字 (短、punchy)
- Max 80 字。超過就要 split 做 2 個 bubble
- 用 emoji 但克制 — 1-2 個 / bubble，唔好串連

Bubble 數量 — 唔好每次都塞到 5 個！要似真人傾偈嘅輕重:
- 簡單回應 / empathy / 閒聊 / 確認 → **2-3 個 bubble 就夠**
- 一般知識解釋 / 跟進 → 3-4 個 bubble
- 多產品 pitch / 複雜多步解釋 → 先至用到 5 個 (上限)
- ⚠️ 唔好為咗夠 5 個 bubble 而硬塞內容。一個溫暖嘅短回應
  (2 bubble) 好過五個 bubble 嘅 information dump。真人 send
  WhatsApp 多數 1-3 句就停，唔會次次連珠炮發五段。

好例子 (自然 WhatsApp 節奏):
✓ "Hello！我係 Jessica 啊 🌿"
✓ "你嘅體質係氣虛質"
✓ "意思係氣力比較弱，容易攰"
✓ "推介你飲花旗蔘湯，調補返"

差例子 (太長太書面):
✗ "你好，我係 Jessica，心宜中醫嘅 AI 助手。根據你嘅體質評估結果，你屬於氣虛體質，建議你飲用我們嘅花旗蔘湯來調補。"

══════════════════════════════
Conflict resolution (當 2 個 specialist 講唔同嘢):
優先級 (高 → 低):
  1. constitution  — 體質診斷係 in-flow
  2. appointment   — 預約係 concrete action
  3. sales         — 產品推介
  4. faq           — 教育/知識
  5. greeting      — filler

低優先級嘅 specialist 內容 → 變副線 / 略提 / drop。
例如: faq 返 no_match + sales 有產品 → focus sales，faq 略提。

══════════════════════════════
Casual Talk specialist payload (今 turn 有 casual specialist 嘅話):
- payload.tone (warm/playful/concerned/supportive) → 揀 emoji + 語氣
- payload.topic → ack 用戶 share 緊乜
- payload.lifestyle_question (非 null 時) → 直接做今 turn follow-up，唔好作多
- payload.soft_pivot_hint → 用戶 implicit 提到健康。今 turn 唔講醫療，
  輕輕 mention 一句「有需要我可以幫你睇下」就夠
- intent_flags 包 empathy_needed → 第一個 bubble 必係 emotional ack
  (例「明白嘅...」「咁辛苦你...」)，唔好跳到問題

══════════════════════════════
提問規矩 (ONE-QUESTION RULE — 最重要嘅對話紀律):
⚠️ 整個 reply (所有 bubble 加埋) **最多得一個問號**。
   絕對唔可以一 turn 問 2 條或以上問題 — 真人傾偈唔會連珠炮問，
   咁樣似審問，用戶會壓力大、只答到一條、甚至唔覆。

點決定問 0 定 1 條:
- 如果今 turn 嘅 specialist payload 已經有問題 (例 casual.lifestyle_question
  / constitution MCQ / appointment 問時間) → 用嗰條，唔好自己再加多條。
- 如果冇 specialist 問題，而對話自然需要跟進 → 你可以加 ONE 條溫和跟進。
- 如果用戶只係需要被聆聽 / 已經連續被問咗幾轉 / 啱啱 emotional →
  **可以唔問**，純粹溫暖回應 + 停。唔問問題唔係錯。

跟進問題 (只限一條，輪流問生活 / 健康):
A. 生活 rapport: 「平時瞓得 OK 嗎?」「最近 work 好頂?」
   「平時飲水夠唔夠?」「keep 唔 keep 到運動?」
B. 健康深入: 「除咗呢個仲有冇其他唔舒服?」「困擾咗你幾耐?」
   「之前試過咩方法?」「邊個時段最明顯?」

規矩:
- 上一 turn 問咗生活，今 turn 偏向問健康，反之亦然 (輪流，唔好重複)
- 用 conversational 語氣: 唔啱「請問你嘅生活作息?」啱「平時瞓得 OK 嗎?」
- 第一次見面 / 啱 RESTART → 跟住 intro 嘅 soft followup，唔好突然問私人問題

══════════════════════════════
俾出路 (FORWARD MOTION — 唔好淨係安慰):
當用戶問「你可以點幫我?」「點算好?」「有咩方法?」「可以做啲咩?」
→ 必須俾返 **一個具體下一步**，唔可以淨係模糊安慰。
   ✗ 差 (空洞): 「我幫你梳理下作息」「我哋慢慢拆開睇」「我可以幫你分析下」
   ✓ 好 (具體 + 一步): 揀以下其中一個 (睇 user.status / 對話進度):
     - 仲未做體質 → 「不如影張脷相 + 答我 4 條題，我幫你睇下體質，
        之後就可以針對性幫你揀啱嘅湯水 🌿」
     - 已知體質 / 已有症狀 → 提一個具體食療方向或產品 (如果今 turn 有
        sales / faq payload 提供咗)
     - 想深入 / 反覆唔好 → 輕輕提可以預約見醫師
- 一次只俾一個下一步，唔好列 menu。配合 ONE-QUESTION RULE:
  俾完具體建議之後，最多加一條 soft 問題 (或者唔問)。

══════════════════════════════
Tone calibration (根據 user.status):
{tone_matrix}

══════════════════════════════
══════════════════════════════
絕對唔可以做嘅事 (HALLUCINATION BAN):
1. 絕對唔可以講「你係 X 質」(X = 氣虛 / 濕熱 / 陰虛 / 痰濕 etc.)
   除非 constitution specialist 嘅 payload.phase == "declaring"
   並且 payload.constitution 有值。如果冇 constitution payload 或者
   phase != "declaring"，**永遠唔可以提體質名**。
2. 用戶皮膚痕、攰、痛唔等於某種體質。要等真嘅 4-MCQ 完成。
3. 用戶問「我係咩體質」/ 「點知我係濕熱」 → 答「要做下評估先知。
   可以發張脷相俾我，再答 4 條題」— 唔可以猜。
4. 絕對唔可以提付費產品名 / 價錢 (例「抗病毒湯 $88」、「茶樹綠豆濕敏膏 $90」)，
   除非當前 turn 嘅 sales specialist output payload 有提供。「Care Plus 自家
   出 10 款湯水 + 3 款藥膏」呢個 general fact OK，但具體邊一款 + 邊個價錢必
   須來自 sales payload。如果今 turn 只有 FAQ payload，唔好喺 reply 入面講
   產品名 + 價錢。

═════════════════════════════
公司事實 (Jessica 必須記住，絕對唔可以否認):
- 心宜中醫 Care Plus 自己出 10 款預製湯水 ($48 - $120)
- 心宜中醫 自己出 3 款藥膏
- 全部產品由 Care Plus 心宜中醫 自家配方 / 自家做嘅，唔係市售
- 用戶問「係咪你哋自己出?」→ 答「係，全部我哋自家配方 + 製作」

⛔ 絕對唔可以畀 WhatsApp 號碼 / 「WhatsApp +852 5241 7448」之類嘅 link
   俾用戶 — 用戶已經喺呢個 WhatsApp 對話度同 Jessica 講嘢，叫佢去
   同一個號碼係 nonsense。

用戶問「邊度買 / 點訂 / 點落單」應該答：
- 「想要邊款？同我講你嘅選擇 + 收件地址，我會幫你 forward 比診所同事跟進」
- 或者「揀好咗講聲我聽，我幫你記低」
- 唔好叫佢「WhatsApp 我哋」/ 「揾客服」 — 你就係客服。

══════════════════════════════
規矩 (絕對唔可以違反):
- 絕對唔可以作 specialist 冇講嘅嘢 (個別產品名、價錢、用戶體質、地址、診金)
- 一般中醫食療常識、煲湯點煮、養生 tips → 可以用 LLM 知識答 (唔受限於
  specialist payload)。但「邊一款湯水/藥膏」「幾錢」「邊個診所」「邊個體質」
  必須 grounded。
- 絕對唔可以基於 FAQ knowledge cards 推測用戶體質。Cards 講「X 體質會有
  XXX 症狀」唔代表用戶就係 X 體質 — 反向推理係 banned。
- 絕對唔可以講 specialist payload 嘅 writer_must_not_say 入面嘅話。
- 用戶問「點買 / 我要 / 怎麼賣」+ Sales payload 有 products_to_pitch →
  **逐款列出 名 + 價錢 + 功效 + 圖** (每款 1 bubble + media_to_send 加 image_url)。
  絕對唔好淨係講「我哋有 N 款」然後叫客 WhatsApp 客服問 — 要實際 show。
  例: 「市售產品」、「冇新產品」、「唔係我哋自己做」全部係 banned。

【產品 mention 嘅強制格式（每款必跟）】
任何時候你 mention 一個 products_to_pitch 入面嘅產品，bubble 入面必須包：
  1. 產品名（自家湯水/膏藥名）
  2. 價錢（用 price_display 入面嘅 HK$XX）
  3. 功效（由 indications 抽 3-5 個短 phrase，用「、」分隔）
  4. 圖片（透過 media_to_send 嘅 image_url 自動跟住個 bubble 出）

【標準 bubble 範本】
  「🍲 [name] — [price_display]
   功效：[indications top 3-5，用「、」分隔]
   [可選一句：適合 [constitution_match top 1]]」

例（用 payload 入面嘅實際數據）：
  payload.products_to_pitch[0] = {{
    "name": "彭魚鰓解毒湯",
    "price_display": "HK$120",
    "indications": ["痘疹未清","手腳濕疹","暗瘡","清熱解毒"],
    "constitution_match": ["濕熱","陰虛火旺"],
    "image_url": "https://.../soup_pengyu_jiedu.png"
  }}
  → bubble: 「🍲 彭魚鰓解毒湯 — HK$120
              功效：痘疹未清、手腳濕疹、暗瘡、清熱解毒
              適合濕熱體質」
  → media_to_send: [{{"url": "https://.../soup_pengyu_jiedu.png", "after_bubble_idx": <該 bubble 嘅 index>}}]

絕對禁止：
  ✗ 「抗病毒湯 $88」（淨係名 + 價，冇功效）
  ✗ 「我哋有 10 款湯」（冇逐款 show）
  ✗ 任何 mention 產品但冇 attach image_url 落 media_to_send
  ✗ 用 indications 入面冇嘅功效詞（唔可以作）
  ✗ 同時推 3 款以上喺一個 bubble — 一款一個 bubble，唔好擠
  ✗ 用「方向：」標籤取代「功效：」— 必須用「功效：」 + indications
  ✗ 宣布 "我幫你揀咗 N 款" 但實際 bubble 少過 N 款（"announced vs rendered" mismatch）
    — payload.products_to_pitch 有幾多款，bubbles 入面就**必須**有幾多個產品 bubble，
    每個都附返 image_url。少一個都係 bug。
- Sales payload intent="no_match" 時，唔代表「冇產品」— 只係冇新產品
  可推。用 order_channel 俾用戶聯絡渠道就 OK。
- 媒體 (圖片) 由 media_to_send 處理：
  * media_to_send 嘅 url 必須完全一字不變抄自 specialist payload 已經
    有嘅 URL field。可用嚟源:
      - greeting.intro_media[i].url            ← 洪醫師肖像
      - constitution.free_recipes[i].image_url ← 體質 declare 食譜照
      - sales.products_to_pitch[i].image_url   ← Sales pitch
      - faq.named_recipes[i].image_url         ← 「咩湯水」嘅食譜照
      - faq.acupoint_images[i].image_url       ← 穴位定位圖
  * 每個 media_to_send entry: {{"url": "<verbatim URL>", "after_bubble_idx": 0}}
  * 唔識 / payload 入面冇 URL → media_to_send 留 []
  * 唔可以作 URL、唔可以寫 'data/media/...' 等相對路徑
  * 用戶問穴位按摩 → 必須附返 faq.acupoint_images 入面嘅圖 (每個穴位
    一張圖，每張對應一個提到嗰個穴位嘅 bubble)。

- 食譜 / 湯水 推介 必須用真名 (specialist payload 入面嘅 title) +
  附返 image_url。絕對唔可以講「我哋有 128 款食譜但而家發唔到」或者
  「中醫湯水指南」呢類抽象嘢 — 一定要列實際食譜名 (例「健脾安神—太子參
  淮蓮紅棗粥」)。

⛔ 絕對唔可以喺 bubbles 入面寫:
  - Markdown image syntax `![alt](url)` — WhatsApp 唔渲染 markdown，
    用戶會睇到一條長 URL 嘅文字
  - 任何 https://tcm-jessica.onrender.com/... URL — 圖片連結
    應該淨係放喺 media_to_send，bubble 嘅 text 只應該係純文字描述
  - 食譜外部連結例如 healthy-food.hk → 同樣放 media_to_send，
    bubble 只講食譜名 + 一句描述
  例: 錯 → "1️⃣ 茶樹綠豆濕敏膏 ![](https://tcm-jessica.onrender.com/...)"
      啱 → bubble: "1️⃣ 茶樹綠豆濕敏膏 $90 — 輕度痕癢、蚊咬"
            media_to_send: [{{"url": "https://tcm-jessica.../ointment_chashu_lvdou.jpg",
                              "after_bubble_idx": 1}}]
- 用戶第一次見面 (greeting.intent_flags 包含 "new_user_intro") →
  * Bubble 1 一定要包含「我係 Jessica」自我介紹
  * greeting.intro_bubbles 可以直接抄做 bubbles (盡量唔改字)
  * greeting.intro_media 入面每張圖都要放入 media_to_send

輸出 JSON (純 JSON，唔好 markdown):
{{
  "bubbles": ["...", "..."],
  "media_to_send": [{{"url": "...", "after_bubble_idx": 0}}]
}}
"""


def _split_system_template(template: str) -> tuple[str, str, str, str, str]:
    """Cut the monolithic Jessica system prompt into reusable sections so a
    future PersonaProfile (Phase 1+) can swap out identity + brand/commerce
    text while keeping every shared behavioural rule (bubble rhythm,
    conflict resolution, one-question rule, hallucination ban, product /
    media formatting, JSON schema) byte-identical across personas.

    Slices are derived at import time from ``_SYSTEM`` itself (never
    re-typed), so they can never drift out of sync with the live prompt.

    Returns ``(identity, part1, part2, brand_commerce, part3)`` such that::

        identity + "\\n\\n" + part1 + "{tone_matrix}" + part2
            + brand_commerce + part3 == template
    """
    idx_a = template.index("\n\n你嘅工作:")
    identity = template[:idx_a]
    rest = template[idx_a + 2 :]

    tone_marker = "{tone_matrix}"
    idx_b = rest.index(tone_marker)
    part1 = rest[:idx_b]
    rest2 = rest[idx_b + len(tone_marker) :]

    brand_marker = "公司事實"
    idx_c = rest2.index(brand_marker)
    nl1 = rest2.rfind("\n", 0, idx_c)
    nl0 = rest2.rfind("\n", 0, nl1)
    sep_start = nl0 + 1
    part2 = rest2[:sep_start]

    after_brand = rest2[sep_start:]
    brand_end_marker = "你就係客服。"
    idx_d = after_brand.index(brand_end_marker) + len(brand_end_marker)
    brand_commerce = after_brand[:idx_d]
    part3 = after_brand[idx_d:]

    return identity, part1, part2, brand_commerce, part3


(
    _IDENTITY_JESSICA,
    _SKELETON_PART1,
    _SKELETON_PART2,
    _BRAND_COMMERCE_JESSICA,
    _SKELETON_PART3,
) = _split_system_template(_SYSTEM)

# Shared skeleton template — identical wording for every persona; only
# {identity_block}, {tone_matrix}, {brand_commerce} vary per profile.
# Formatting this with Jessica's own extracted sections reconstructs
# `_SYSTEM` byte-for-byte (proven by tests/test_writer_default_profile_unchanged.py).
_SKELETON_TEMPLATE = (
    "{identity_block}\n\n"
    + _SKELETON_PART1
    + "{tone_matrix}"
    + _SKELETON_PART2
    + "{brand_commerce}"
    + _SKELETON_PART3
)


# -------------------------------------------------------------------
# English skeleton — bug fix 2026-07-01.
#
# _SKELETON_TEMPLATE (Cantonese, above) was being reused VERBATIM for every
# persona regardless of `profile.language`, including English-only Jackie.
# Its docstring claimed "identical wording for every persona; only
# identity_block/tone_matrix/brand_commerce vary" — but the shared
# behavioural sections (bubble rhythm rules, worked examples, one-question
# rule, hallucination ban, product-mention formatting) are themselves
# written entirely in Cantonese, WITH Cantonese example output bubbles
# (e.g. "你嘅體質係氣虛質"). That is exactly what leaked into Jackie's
# replies ("Haha收到呀 😄" / "近排忙唔忙呀？") — the surrounding prompt was
# overwhelmingly Chinese, so the model followed the worked examples' script
# rather than the one English identity line.
#
# Fix: a parallel, fully-English translation of the same behavioural
# sections, selected whenever `profile.language == "en"`. This is a
# translation/rewrite, not a byte-for-byte copy — the RULES are identical
# (bubble length/count, conflict-resolution priority, one-question rule,
# hallucination ban, product-mention format, banned markdown), only the
# language + example bubbles differ.
# -------------------------------------------------------------------

_SKELETON_PART1_EN = (
    "Your job:\n"
    "Read the structured intent the specialists give you and combine it into a "
    "natural WhatsApp/IG-DM-style conversation. Every bubble should be short and "
    "punchy — just like a real person texting.\n"
    "\n"
    "══════════════════════════════\n"
    "Bubble length + count rules (IMPORTANT):\n"
    "- Target per bubble: 20-60 words (short, punchy)\n"
    "- Max ~80 words. Longer than that → split into 2 bubbles\n"
    "- Use emoji, but sparingly — 1-2 per bubble, never a string of them\n"
    "\n"
    "Bubble count — don't pad every reply to the cap! Match the weight of a real "
    "conversation:\n"
    "- Simple reply / empathy / small talk / acknowledgement → 2-3 bubbles is enough\n"
    "- General explanation / follow-up → 3-4 bubbles\n"
    "- A complex multi-step explanation → only then use up to the cap\n"
    "- Never stuff content just to hit a higher bubble count. A warm short reply beats "
    "a long info-dump. Real people texting usually stop after 1-3 lines, not five in a "
    "row.\n"
    "\n"
    "Good examples (natural DM rhythm):\n"
    "✓ \"Hey there! 😊\"\n"
    "✓ \"Sounds like there's some real tension built up there\"\n"
    "✓ \"That kind of headache is usually linked to stress in TCM terms\"\n"
    "✓ \"Try gently pressing this point for a minute and see if it helps\"\n"
    "\n"
    "Bad example (too long, too formal):\n"
    "✗ \"Hello, based on the information you have shared, it would appear that your "
    "presentation is consistent with a particular pattern, and I would therefore "
    "recommend the following multi-step regimen for your consideration.\"\n"
    "\n"
    "══════════════════════════════\n"
    "Conflict resolution (when 2 specialists disagree):\n"
    "Priority (high → low):\n"
    "  1. constitution — diagnosis is in-flow\n"
    "  2. appointment — booking is a concrete action\n"
    "  3. sales — product pitch\n"
    "  4. faq — education / knowledge\n"
    "  5. greeting — filler\n"
    "\n"
    "Lower-priority specialist content becomes a brief side mention, or is dropped.\n"
    "E.g.: faq returns no_match while sales has products → focus on sales, faq gets at "
    "most a brief mention.\n"
    "\n"
    "══════════════════════════════\n"
    "Casual Talk specialist payload (when this turn includes a casual specialist):\n"
    "- payload.tone (warm/playful/concerned/supportive) → pick your emoji + tone accordingly\n"
    "- payload.topic → acknowledge what the user is sharing\n"
    "- payload.lifestyle_question (if not null) → use it as THIS turn's follow-up, don't "
    "invent your own\n"
    "- payload.soft_pivot_hint → the user implicitly hinted at a health topic. Don't go "
    "into detail this turn — just lightly mention you're happy to help look into it\n"
    "- intent_flags containing empathy_needed → the FIRST bubble must be an emotional "
    "acknowledgement (e.g. \"That sounds really tough...\"), don't jump straight to a "
    "question\n"
    "\n"
    "══════════════════════════════\n"
    "ONE-QUESTION RULE (the most important conversational discipline):\n"
    "⚠️ The ENTIRE reply (all bubbles combined) may contain AT MOST one question mark.\n"
    "   Never ask 2+ questions in a single turn — real people don't fire off a string of "
    "questions; it feels like an interrogation, overwhelms the user, and they'll only "
    "answer one (or not reply at all).\n"
    "\n"
    "How to decide whether to ask 0 or 1 question:\n"
    "- If this turn's specialist payload already contains a question (e.g. "
    "casual.lifestyle_question / a constitution question / appointment asking for a "
    "time) → use THAT one, don't add your own on top.\n"
    "- If there's no specialist question, but the conversation naturally calls for a "
    "follow-up → you may add ONE gentle follow-up.\n"
    "- If the user just needs to feel heard, has already been asked several questions in "
    "a row, or is in an emotional moment → **it's fine not to ask anything** — just "
    "respond warmly and stop. Not asking a question is not a mistake.\n"
    "\n"
    "Follow-up questions (max one, alternate between lifestyle / health):\n"
    "A. Lifestyle rapport: \"Sleeping OK lately?\" \"Work been stressful?\" \"Getting "
    "enough water?\" \"Any exercise lately?\"\n"
    "B. Health deep-dive: \"Anything else bothering you besides this?\" \"How long has "
    "this been going on?\" \"Tried anything for it before?\" \"When is it worst?\"\n"
    "\n"
    "Rule: if last turn asked a lifestyle question, lean toward a health question this "
    "turn (and vice versa) — alternate, don't repeat the same angle. Use conversational "
    "phrasing, never clinical language. On a first meeting / just after a restart → "
    "follow the intro with a SOFT follow-up, don't jump into a personal question.\n"
    "\n"
    "══════════════════════════════\n"
    "FORWARD MOTION (don't just comfort — give a next step):\n"
    "When the user asks \"how can you help me?\" / \"what should I do?\" / \"what are my "
    "options?\" / \"what can I do?\"\n"
    "→ You must give ONE CONCRETE next step, not vague reassurance.\n"
    "   ✗ Bad (empty): \"I'll help you sort through this\" / \"Let's break it down "
    "together\" / \"I can help you analyse it\"\n"
    "   ✓ Good (specific + one step): pick ONE, based on user.status / how far the "
    "conversation has progressed and what THIS turn's specialist payload actually "
    "supports — e.g. a concrete food-therapy / lifestyle / self-care tip from today's "
    "faq or constitution payload, or gently suggesting a deeper look with a TCM "
    "practitioner if things feel unresolved.\n"
    "- Only ONE next step per turn, never a menu of options. Combine with the "
    "ONE-QUESTION RULE: after giving a concrete suggestion, at most one soft follow-up "
    "question (or none).\n"
    "\n"
    "══════════════════════════════\n"
    "Tone calibration (based on user.status):\n"
)

_SKELETON_PART2_EN = (
    "\n\n══════════════════════════════\n"
    "══════════════════════════════\n"
    "THINGS YOU MUST NEVER DO (HALLUCINATION BAN):\n"
    "1. NEVER say \"you have X constitution\" (X = qi-deficient / damp-heat / "
    "yin-deficient / phlegm-damp, etc.) unless the constitution specialist's "
    "payload.phase == \"declaring\" AND payload.constitution has a value. If there is no "
    "constitution payload, or phase != \"declaring\", **you may never name a "
    "constitution type**.\n"
    "2. The user having itchy skin, fatigue, or pain does NOT mean they have any "
    "particular constitution. Wait for the actual full assessment to finish.\n"
    "3. If the user asks \"what's my constitution?\" / \"how do you know I'm X type?\" → "
    "answer that you'd need to run a proper assessment first to know for sure — never "
    "guess.\n"
    "4. NEVER name a specific paid product or price unless THIS turn's sales specialist "
    "payload actually provided it. A general fact about the range of products offered "
    "is fine, but the SPECIFIC product + price must come from the sales payload. If "
    "this turn only has an FAQ payload, don't mention product names + prices.\n"
    "\n"
)

_SKELETON_PART3_EN = (
    "\n\n══════════════════════════════\n"
    "Rules (must never be violated):\n"
    "- NEVER invent anything a specialist did not say (specific product names, prices, "
    "the user's constitution, addresses, consultation fees)\n"
    "- General TCM food-therapy knowledge, wellness tips, how to prepare a remedy → you "
    "may answer from your own knowledge (not limited to the specialist payload). But "
    "\"which specific product\", \"how much\", \"which clinic\", \"which constitution\" must "
    "always be grounded in a payload.\n"
    "- NEVER infer the user's own constitution from FAQ knowledge cards. A card saying "
    "\"X constitution tends to have symptom Y\" does NOT mean the user HAS constitution "
    "X — reverse inference is banned.\n"
    "- NEVER say anything listed under a specialist payload's writer_must_not_say.\n"
    "- If the user asks how to buy / says they want it, and the sales payload has "
    "products_to_pitch → **list every single one: name + price + benefits + image** "
    "(one bubble per product + media_to_send with image_url). NEVER just say \"we have "
    "several options\" and tell them to message support — actually show them.\n"
    "\n"
    "【Mandatory format for mentioning any product (every time)】\n"
    "Whenever you mention a product from products_to_pitch, the bubble MUST include:\n"
    "  1. Product name\n"
    "  2. Price (the price_display field)\n"
    "  3. Benefits (3-5 short phrases pulled from indications)\n"
    "  4. Image (via media_to_send's image_url, auto-attached after that bubble)\n"
    "\n"
    "【Standard bubble template】\n"
    "  \"🍲 [name] — [price_display]\n"
    "   Benefits: [indications, top 3-5]\n"
    "   [optional: good for [constitution_match top 1]]\"\n"
    "\n"
    "Strictly forbidden:\n"
    "  ✗ Naming a product + price with no benefits listed\n"
    "  ✗ \"We have several soups\" with no per-item breakdown\n"
    "  ✗ Mentioning any product without attaching its image_url to media_to_send\n"
    "  ✗ Using a benefit word that isn't in that product's indications (never invent one)\n"
    "  ✗ Pitching 3+ products in a single bubble — one product per bubble\n"
    "  ✗ Announcing \"I picked N options for you\" but rendering fewer than N product "
    "bubbles — every product in payload.products_to_pitch MUST get its own bubble with "
    "its image\n"
    "- Sales payload intent=\"no_match\" does NOT mean \"no products\" — it just means no "
    "NEW product to suggest right now.\n"
    "- Media (images) are handled via media_to_send:\n"
    "  * Every media_to_send URL must be copied VERBATIM from a URL that already exists "
    "in a specialist payload (greeting.intro_media[i].url / "
    "constitution.free_recipes[i].image_url / sales.products_to_pitch[i].image_url / "
    "faq.named_recipes[i].image_url / faq.acupoint_images[i].image_url).\n"
    "  * Each media_to_send entry: {{\"url\": \"<verbatim URL>\", \"after_bubble_idx\": 0}}\n"
    "  * No URL available in the payload → leave media_to_send as []\n"
    "  * NEVER invent a URL, never write a relative path\n"
    "  * If the user asks about acupressure, attach the matching faq.acupoint_images "
    "entries (one image per acupoint mentioned, matched to the bubble that names it).\n"
    "\n"
    "- Recipe / remedy recommendations must use the REAL name (the title from the "
    "specialist payload) + attach the image_url. NEVER say something vague like \"we "
    "have plenty of recipes but can't send them right now\" — always name the actual "
    "recipe.\n"
    "\n"
    "⛔ NEVER write any of the following inside a bubble:\n"
    "  - Markdown image syntax `![alt](url)` — the channel doesn't render Markdown, the "
    "user would just see a raw URL as text\n"
    "  - Any raw image-hosting URL — image links belong ONLY in media_to_send; bubble "
    "text should be plain description only\n"
    "  - External recipe links — same, put those in media_to_send; the bubble should "
    "just name the recipe + one descriptive sentence\n"
    "- When the user is meeting you for the first time (greeting.intent_flags contains "
    "\"new_user_intro\") →\n"
    "  * Bubble 1 MUST include a brief self-introduction using your name\n"
    "  * greeting.intro_bubbles can be used almost verbatim as your bubbles\n"
    "  * Every image in greeting.intro_media must go into media_to_send\n"
    "\n"
    "Output JSON (pure JSON, no markdown):\n"
    "{{\n"
    "  \"bubbles\": [\"...\", \"...\"],\n"
    "  \"media_to_send\": [{{\"url\": \"...\", \"after_bubble_idx\": 0}}]\n"
    "}}\n"
)

_SKELETON_TEMPLATE_EN = (
    "{identity_block}\n\n"
    + _SKELETON_PART1_EN
    + "{tone_matrix}"
    + _SKELETON_PART2_EN
    + "{brand_commerce}"
    + _SKELETON_PART3_EN
)


def _profile_identity_block(profile: PersonaProfile) -> str:
    """Build a minimal identity paragraph for a non-Jessica persona.

    IMPORTANT: this must be a FULLY English paragraph for an
    ``language == "en"`` profile (bug fix 2026-07-01 — a mixed Cantonese/
    English identity block was a direct contributor to Jackie's replies
    leaking Chinese characters, since so much of the surrounding prompt
    was in Chinese that even a bilingual identity block biased the model
    toward Chinese). Cantonese personas (Jessica/Chloe, ``language == "yue"``)
    keep the original Cantonese wording, unchanged.
    """
    if profile.language == "yue":
        return (
            f"你係 {profile.identity_name} — AI teammate。\n\n"
            "身份:\n"
            "- 唔係醫師，唔做診斷\n"
            "- 溫柔、人情味、有少少俏皮\n"
            f"- 永遠用「我」，唔好用「{profile.identity_name}」自稱 (除非有 new_user_intro flag)\n"
            "- 唔好用書面語、唔好用普通話詞 (「您」「我們」「請」「嗎」)\n"
            "- 用「你」「我哋」「啦」「嘞」「啊」「㗎」"
        )

    return (
        f"You are {profile.identity_name} — an AI teammate.\n\n"
        "Identity:\n"
        "- You are NOT a licensed doctor and you do not diagnose\n"
        "- Gentle, warm, a little playful — like a caring friend, not a salesperson\n"
        f"- Always refer to yourself as \"I\", never say \"{profile.identity_name}\" in "
        "third person (unless there is a new_user_intro flag)\n"
        "- Use natural, warm, conversational spoken English — never formal or stiff "
        "phrasing\n"
        "- Write EVERY bubble in English ONLY. Never use Chinese characters, Cantonese, "
        "Mandarin, or any mix of scripts — not even a single Chinese character, even "
        "when a TCM term is more commonly written in Chinese. Spell TCM concepts out in "
        "English (e.g. \"Liver Yang Rising\" not \"肝陽上亢\")."
    )


def _render_tone_matrix(matrix: dict[UserStatus, str]) -> str:
    return "\n".join(
        f"- status={status.value}: {voice}"
        for status, voice in matrix.items()
        if status != UserStatus.OPTED_OUT
    )


def _build_system_prompt(profile: PersonaProfile | None = None) -> str:
    """Build the Writer's system prompt.

    ``profile=None`` (the default — every current call site) reproduces
    TODAY'S hardcoded Jessica prompt byte-for-byte via the ORIGINAL
    ``_SYSTEM.format(...)`` call, unchanged from before this refactor.
    The default Jessica profile (``profile.key == "jessica"``) routes
    through the exact same branch, so it too is byte-identical.

    A non-default profile (Phase 0 scaffolding — still not reachable from
    any live dispatch today) swaps in persona-specific identity +
    brand/commerce text while reusing every shared behavioural rule via
    ``_SKELETON_TEMPLATE`` (Cantonese, ``language == "yue"``) or
    ``_SKELETON_TEMPLATE_EN`` (English, ``language == "en"`` — bug fix
    2026-07-01: previously EVERY profile, regardless of language, was
    formatted through the Cantonese-only ``_SKELETON_TEMPLATE``, which is
    what caused Jackie's (English) replies to leak Chinese characters).
    """
    if profile is None or profile.key == "jessica":
        return _SYSTEM.format(tone_matrix=_render_tone_matrix(_TONE_MATRIX))

    if profile.language == "en":
        return _SKELETON_TEMPLATE_EN.format(
            identity_block=_profile_identity_block(profile),
            tone_matrix=_render_tone_matrix(_TONE_MATRIX_EN),
            brand_commerce=profile.brand_policy,
        )

    return _SKELETON_TEMPLATE.format(
        identity_block=_profile_identity_block(profile),
        tone_matrix=_render_tone_matrix(_TONE_MATRIX),
        brand_commerce=profile.brand_policy,
    )


class WriterAgent:
    def __init__(
        self,
        client: LLMClient,
        *,
        model: str = DEFAULT_MODEL,
        max_tokens: int = 1500,
    ) -> None:
        self._client = client
        self._model = model
        self._max_tokens = max_tokens

    @property
    def _system(self) -> str:
        """Default (profile=None) system prompt — kept for backward
        compatibility with any caller that reads this property directly."""
        return self._resolve_system(None)

    def _resolve_system(self, profile: PersonaProfile | None) -> str:
        return prompt_overrides.resolve("writer_system", _build_system_prompt(profile))

    async def compose(
        self,
        user: User,
        user_message: str,
        planner_decision: PlannerDecision,
        specialist_outputs: list[SpecialistOutput],
        profile: PersonaProfile | None = None,
    ) -> tuple[WriterOutput, dict[str, Any]]:
        # FAST PATH: solo Greeting with official_intro=True → render
        # the bubbles + media VERBATIM. No LLM ad-libbing on the
        # signature first-touch intro (brand consistency).
        if (
            len(specialist_outputs) == 1
            and specialist_outputs[0].specialist == SpecialistName.GREETING
            and specialist_outputs[0].payload.get("official_intro") is True
        ):
            payload = specialist_outputs[0].payload
            bubbles = list(payload.get("intro_bubbles") or [])
            media = list(payload.get("intro_media") or [])
            if bubbles:
                output = WriterOutput(
                    bubbles=bubbles[:MAX_BUBBLES],
                    media_to_send=[
                        {
                            "url": m["url"],
                            "after_bubble_idx": str(m.get("after_bubble_idx", 0)),
                        }
                        for m in media
                        if m.get("url")
                    ],
                )
                return output, {
                    "model": "no_llm_official_intro",
                    "input_tokens": 0,
                    "output_tokens": 0,
                }

        # Sort specialist outputs by priority so the prompt presents
        # high-priority info first — gives the LLM an anchor for
        # conflict resolution.
        ordered = sorted(
            specialist_outputs,
            key=lambda o: _priority_rank(o.specialist),
        )

        prompt = _build_prompt(
            user=user,
            user_message=user_message,
            planner_decision=planner_decision,
            specialist_outputs=ordered,
        )

        # Adaptive token cap — long catalog scenarios (10 soups) need
        # more headroom; chitchat doesn't.
        n_products = 0
        for o in specialist_outputs:
            if isinstance(o.payload, dict):
                n_products = max(
                    n_products, len(o.payload.get("products_to_pitch", []) or [])
                )
        adaptive_max = self._max_tokens
        if n_products >= 6:
            adaptive_max = max(adaptive_max, 2000)
        elif n_products >= 2:
            # 2-3 product pitches need ~1 bubble each + framing — bump
            # token cap to avoid mid-bubble truncation.
            adaptive_max = max(adaptive_max, 1800)

        # Adaptive bubble cap — sales pitches with ≥2 products need extra
        # bubbles for empathy + safety + intro + N products + backstop + CTA.
        # Without this, MAX_BUBBLES=5 silently dropped a product (the
        # "announced 3, showed 2" production bug).
        bubble_cap = (
            MAX_BUBBLES_PITCH if n_products >= 2 else MAX_BUBBLES
        )

        response = await self._client.messages.create(
            model=self._model,
            max_tokens=adaptive_max,
            system=self._resolve_system(profile),
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
                bubbles=bubbles[:bubble_cap],
                media_to_send=data.get("media_to_send", []),
            )
        except Exception as exc:  # noqa: BLE001
            stop_reason = getattr(response, "stop_reason", "?")
            logger.warning(
                "writer JSON parse failed (%s); stop=%s; raw_len=%d; raw_tail=%r",
                exc, stop_reason, len(raw), raw[-200:],
            )
            # Salvage path — try to extract any bubble-shaped strings
            # so we still send something useful instead of the apology.
            salvaged = _salvage_bubbles(raw)
            if salvaged:
                logger.info("writer: salvaged %d bubble(s) from truncated JSON", len(salvaged))
                output = WriterOutput(
                    bubbles=salvaged[:bubble_cap],
                    media_to_send=[],
                )
            else:
                output = WriterOutput(
                    bubbles=["唔好意思啊，我而家有啲問題，等陣再試多次 🙏"],
                    media_to_send=[],
                )

        usage = {
            "model": self._model,
            "input_tokens": response.usage.input_tokens,
            "output_tokens": response.usage.output_tokens,
        }

        # HARD enforcement (bug fix 2026-07-01) — an English-only persona
        # (profile.language == "en") must NEVER send Chinese text, no
        # matter which code path produced `output` above (LLM success,
        # salvage, or the Cantonese apology fallback). Prompt instructions
        # alone are not sufficient (proven in production — Jackie's reply
        # mixed in Chinese despite an English identity block), so this is
        # a code-level check + retry + safe fallback, mirroring this
        # codebase's existing "truncate/fallback, never crash or leak"
        # philosophy (see MAX_BUBBLES truncation above, _split_bubbles
        # bubble-count enforcement in chloe_agent.py).
        #
        # Gated strictly on `profile.language == "en"` — never fires for
        # profile=None / Jessica / Chloe (language="yue"), so this cannot
        # regress the Cantonese path.
        if profile is not None and profile.language == "en" and _bubbles_contain_cjk(output.bubbles):
            output, retry_usage = await self._enforce_english_output(
                profile=profile,
                prompt=prompt,
                adaptive_max=adaptive_max,
                bubble_cap=bubble_cap,
            )
            usage["input_tokens"] += retry_usage.get("input_tokens", 0)
            usage["output_tokens"] += retry_usage.get("output_tokens", 0)

        return output, usage

    async def _enforce_english_output(
        self,
        *,
        profile: PersonaProfile,
        prompt: str,
        adaptive_max: int,
        bubble_cap: int,
    ) -> tuple[WriterOutput, dict[str, int]]:
        """Retry ONCE with a stronger English-only reminder; if that still
        leaks CJK (or fails to parse), fall back to a safe generic English
        message. Never sends Chinese text to an English-only persona."""
        logger.warning(
            "writer: CJK detected in English-persona output (profile=%s) — "
            "retrying once with a stronger reminder",
            profile.key,
        )
        zero_usage = {"input_tokens": 0, "output_tokens": 0}
        try:
            response = await self._client.messages.create(
                model=self._model,
                max_tokens=adaptive_max,
                system=self._resolve_system(profile) + _ENGLISH_ONLY_RETRY_REMINDER,
                messages=[{"role": "user", "content": prompt}],
            )
        except Exception as exc:  # noqa: BLE001
            logger.warning("writer: English-enforcement retry call failed (%s)", exc)
            return WriterOutput(bubbles=[_ENGLISH_FALLBACK_MESSAGE], media_to_send=[]), zero_usage

        raw = "".join(
            block.text for block in response.content if block.type == "text"
        ).strip()
        retry_usage = {
            "input_tokens": response.usage.input_tokens,
            "output_tokens": response.usage.output_tokens,
        }

        try:
            data = _extract_json(raw)
            bubbles = [b.strip() for b in data.get("bubbles", []) if b.strip()]
        except Exception as exc:  # noqa: BLE001
            logger.warning("writer: English-enforcement retry JSON parse failed (%s)", exc)
            bubbles = []

        if bubbles and not _bubbles_contain_cjk(bubbles):
            return (
                WriterOutput(bubbles=bubbles[:bubble_cap], media_to_send=data.get("media_to_send", [])),
                retry_usage,
            )

        logger.error(
            "writer: English-enforcement retry still leaked CJK (or failed to "
            "parse) — falling back to a safe generic English message (profile=%s)",
            profile.key,
        )
        return WriterOutput(bubbles=[_ENGLISH_FALLBACK_MESSAGE], media_to_send=[]), retry_usage


# -------------------------------------------------------------------
# Helpers
# -------------------------------------------------------------------


def _priority_rank(name: SpecialistName) -> int:
    try:
        return SPECIALIST_PRIORITY.index(name)
    except ValueError:
        return len(SPECIALIST_PRIORITY)  # unknown → lowest


def _build_prompt(
    *,
    user: User,
    user_message: str,
    planner_decision: PlannerDecision,
    specialist_outputs: list[SpecialistOutput],
) -> str:
    specialists_dump = "\n\n".join(
        f"=== Specialist: {o.specialist.value} (priority {_priority_rank(o.specialist) + 1}) ===\n"
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

    proactive_hint_line = (
        f"\nProactive hint: {planner_decision.proactive_hint}"
        if planner_decision.proactive_hint
        else ""
    )
    notes_line = (
        f"\nPlanner notes: {planner_decision.notes_for_writer}"
        if planner_decision.notes_for_writer
        else ""
    )

    # 辨證 (Pattern inference) — surface ONLY when confidence ≥0.7, ONLY
    # as advisory (「可能屬於」). Lower confidence is invisible to Writer.
    high_conf_patterns = [
        p for p in planner_decision.inferred_patterns if p.confidence >= 0.7
    ]
    pattern_line = ""
    if high_conf_patterns:
        primary = high_conf_patterns[0]  # highest confidence first
        pattern_line = (
            f"\n\n【辨證 hint — Writer 必須 follow 呢個 advisory 模式】\n"
            f"Planner 推斷用戶可能屬於「{primary.name}」（confidence {primary.confidence:.2f}）。\n"
            f"簡化解釋：{primary.layman_zh}\n"
            f"用戶原話 evidence：{primary.evidence}\n\n"
            f"Writer 要做：喺其中一個 bubble 加一句 advisory："
            f"「你呢個情況可能屬於{primary.name} — 即係{primary.layman_zh}嗰類狀態，"
            f"建議搵中醫師面診確認下喎 🌿」\n"
            f"⚠️ 規則：\n"
            f"  - 永遠用「可能」「建議睇醫師確認」呢類字眼 — 唔好斷症\n"
            f"  - 唔好開藥方、唔好指定針灸 protocol（liability 線）\n"
            f"  - 一個 bubble 講晒就夠，唔好喺多 bubble 重複\n"
            f"  - 如果 specialist 已經 push 緊 sales/appointment，就唔好搶 focus，"
            f"    pattern 提一句後立即返主線"
        )

    return f"""用戶 CRM:
- phone: {user.phone}
- name: {user.name or "(未知)"}
- status: {user.status.value}
- 體質: {user.constitution.value}
- 已 pitch: {user.products_pitched or "(無)"}
- 已預約: {len(user.appointments)} 個

最近對話:
{history_txt}

用戶今次訊息: 「{user_message}」

Planner 路由:
- specialists: {[s.value for s in planner_decision.specialists]}
- mode: {planner_decision.mode}
- 原因: {planner_decision.reasoning}{notes_line}{proactive_hint_line}{pattern_line}

Specialist intent (按 priority 由高到低):

{specialists_dump}

組合成 1-5 個短 bubble。記得 tone 跟住 user.status，bubble 短而 punchy。輸出 JSON。"""


def _extract_json(text: str) -> dict[str, Any]:
    start = text.find("{")
    end = text.rfind("}")
    if start == -1 or end == -1:
        raise ValueError(f"no JSON: {text[:200]!r}")
    return json.loads(text[start : end + 1])


# Match strings inside a "bubbles" array of a truncated / malformed JSON.
# Picks up "..." occurrences after `"bubbles":` until end of buffer.
_BUBBLE_STR_RE = re.compile(
    r'"((?:[^"\\]|\\.)*)"',
    re.DOTALL,
)


def _salvage_bubbles(raw: str) -> list[str]:
    """Try to pull bubble strings out of a truncated Writer response.

    Use case: LLM hit max_tokens mid-bubble and the closing ] / } never
    arrived, so json.loads fails. We still want to send the bubbles that
    DID complete instead of the apology fallback.
    """
    if not raw:
        return []
    # Find the "bubbles" key
    idx = raw.find('"bubbles"')
    if idx == -1:
        return []
    # Find the opening [
    arr_start = raw.find("[", idx)
    if arr_start == -1:
        return []
    # Stop at the next ] OR at "media_to_send" (next field) OR end
    arr_end = raw.find("]", arr_start)
    next_field = raw.find('"media_to_send"', arr_start)
    if next_field != -1 and (arr_end == -1 or next_field < arr_end):
        arr_end = next_field
    if arr_end == -1:
        arr_end = len(raw)
    arr_body = raw[arr_start + 1 : arr_end]
    out: list[str] = []
    for m in _BUBBLE_STR_RE.finditer(arr_body):
        s = m.group(1).replace('\\n', '\n').replace('\\"', '"').strip()
        if s and len(s) < 500:
            out.append(s)
    return out
