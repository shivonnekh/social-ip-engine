# Jessica Product Sales Flow — Implementation Plan

**Date:** 2026-05-19
**Owner:** Shivonne + Shello
**Branch (proposed):** `feature/jessica-product-sales`
**Decision:** Option C — Hybrid card-based catalog with `is_product:true` flag + new `recommend_paid_item` tool
**Estimated effort:** 1.5–2 days

---

## 1. What we're building

Add 13 sellable items into Jessica's sales flow:

| Category | Items | Price range | Pitch trigger |
|---|---|---|---|
| **湯水 (soups)** | 10 items: 彭魚鰓解毒湯, 清心潤肺湯, 清肝明目湯, 抗病毒湯, 花膠響螺片湯, 川芎白芷天麻湯, 海星止咳湯, 感冒止咳湯, 止咳潤肺湯, 花旗蔘湯 | $48–$120 | **Constitution-driven** (after `declare_constitution`) |
| **藥膏 (ointments)** | 3 items: 茶樹綠豆濕敏膏 ($90), 蛋黃油乳液 ($120), 止痕濕疹膏 ($180) | $90–$180 | **Symptom-driven** (when 皮膚痕/濕疹/痘疹/暗瘡 detected) |

These are distinct from the existing 128 free DIY recipes (28 + 100 from healthy-food.hk) that Jessica already shares as educational content. Paid items must NEVER be presented as "你可以自己煲" — they're products to order from 心宜中醫.

Checkout = WhatsApp deep link to 心宜中醫 customer service number. No in-bot payment.

---

## 2. Why Option C (recap)

- **Reuses existing Qdrant retrieval + image extraction + bubble flow** — no new infra
- **Card-driven** stays consistent with CLAUDE.md Section 3.1 ("Card-Driven (absolute)")
- **Clear paid/free separation** via `is_product:true` flag — Jessica's prompt branches on it
- **One new tool** (`recommend_paid_item`) keeps the funnel clean; doesn't pollute `find_knowledge_cards`
- **Cheap to revert** if products don't sell — delete cards + tool, prompt step disabled by config flag

Rejected:
- **Option A** (raw cards) — Jessica can't tell paid from free; she'd offer the $120 soup as DIY
- **Option B** (full e-commerce) — overkill until we see what sells

---

## 3. File changes

### 3.1 New files

| File | Purpose | Size |
|---|---|---|
| `data/cards/tcm-wellness-中醫養生/tcm_paid_soups.json` | 10 sellable soups card | ~250 lines |
| `data/cards/tcm-wellness-中醫養生/tcm_paid_ointments.json` | 3 sellable ointments card | ~120 lines |
| `data/product_catalog.json` | Lookup table: card_id → {price, image_url, purchase_method} | ~80 lines |
| `src/tools/products.py` | `recommend_paid_item(complaint, constitution)` tool | ~150 lines |
| `tests/test_product_recommendation.py` | Unit tests for tool + matching logic | ~120 lines |

### 3.2 Modified files

| File | Change | Why |
|---|---|---|
| `src/tools/sales.py` | `share_product` → accepts `product_id` param; lookup from catalog instead of hardcoded Maca | Generalize the existing tool |
| `src/sales/sales_prompt.py` | Step 9c rewrite: "based on constitution + complaint, pick 1 soup + (if skin symptom) 1 ointment from catalog" | New pitch logic |
| `src/sales/flow_engine.py` | Add `paid_item_recommended` state flag | Track that pitch happened so we don't repeat |
| `src/agent.py` | Register `recommend_paid_item` tool, ensure it appears AFTER `share_product` in tool list | Tool registration |
| `configs/tcm-wellness.yaml` | Add `paid_products.enabled: true` + `paid_products.whatsapp_order_number` + `paid_products.max_per_turn: 2` | Config-driven (CLAUDE.md 3.3) |
| `scripts/index_all.py` | Re-index after card add | Standard reindex |

---

## 4. Card schema additions

Add to existing schema (CLAUDE.md Section 6.1) — only NEW fields:

```json
{
  "knowledge_card": {
    "metadata": {
      "is_product": true,
      "product_type": "soup",        // or "ointment"
      "evidence_level": "Traditional Practice — Care Plus 心宜中醫 product",
      "...standard fields"
    },
    "overview": {
      "...standard fields"
    },
    "core_content": {
      "products": [
        {
          "product_id": "soup_pengyu_jiedu",
          "name": "彭魚鰓解毒湯",
          "price_hkd": 120,
          "indications": ["痘疹未清", "手腳濕疹", "暗瘡", "手足口病", "生蛇調理"],
          "constitution_match": ["濕熱", "陰虛"],
          "complaint_keywords": ["痘", "暗瘡", "濕疹", "皮膚", "生蛇"],
          "image_url": "https://...",
          "purchase_method": "whatsapp",
          "purchase_url": "https://wa.me/85252417448?text=想訂彭魚鰓解毒湯",
          "core_answer": "..."
        }
      ]
    }
  }
}
```

`product_catalog.json` mirrors this as a flat lookup keyed on `product_id` for O(1) retrieval inside the tool — avoids re-parsing the full card every recommendation.

---

## 5. `recommend_paid_item` tool spec

```python
def recommend_paid_item(
    constitution: str | None,      # e.g. "陽虛", "濕熱"
    complaints: list[str],         # e.g. ["皮膚痕", "暗瘡"]
    product_type: str | None = None,  # "soup" | "ointment" | None=auto
    max_items: int = 2,
) -> dict:
    """
    Returns 1-2 matched products as structured pitch payload.

    Matching priority:
      1. Symptom match (ointments): if any complaint keyword in product.complaint_keywords → high priority
      2. Constitution match (soups): if constitution in product.constitution_match → high priority
      3. Generic relevance: TF-IDF or keyword overlap with complaint text

    Returns:
      {
        "items": [
          {"product_id": "...", "name": "...", "price_hkd": 120,
           "pitch_line": "您嘅體質配呢個...", "image_url": "...",
           "purchase_url": "https://wa.me/..."}
        ],
        "matched_by": "constitution" | "symptom" | "fallback",
      }

    Guardrails:
      - max_items hard cap = 2
      - Never returns same product twice in a session (check session.paid_items_pitched)
      - Returns {"items": []} if nothing matches — DO NOT force a recommendation
    """
```

**Important:** the tool does NOT generate the pitch text — the LLM does, using the structured payload. This preserves prompt budget and keeps Jessica's voice consistent. Tool just supplies the candidates + facts.

---

## 6. Prompt diff (Step 9c)

### Current (sales_prompt.py:406)
```
**share_product(pitch_text)** — suggest_treatments 之後主動介紹...自然地連接佢嘅體質同 Maca 功效
```

### Replacement
```
**Step 9c — Paid item recommendation**

After `suggest_treatments`, call `recommend_paid_item(constitution, complaints, product_type)`:
  • product_type="ointment" → IF user mentioned 皮膚痕 / 暗瘡 / 濕疹 / 生蛇 / 痘
  • product_type="soup"     → ALWAYS after constitution declared
  • Both → if skin complaint + constitution known

After tool returns items, call `share_product(product_ids=[...])` with the matched IDs.
The system will attach product photos + WhatsApp order links automatically.

YOUR job is the pitch TEXT in the same turn — connect the product to THEIR constitution/complaint
in plain Cantonese, 1-2 sentences per item, mention price ONCE, then ask if they want to order.

🚫 Never invent products. Only pitch IDs from the tool response.
🚫 Never pitch >2 paid items in one turn.
🚫 If recommend_paid_item returns empty items[] → skip pitch entirely, proceed to clinic invite.
```

**Token budget impact:** +120 tokens in prompt, -80 from removing hardcoded Maca block = **net +40 tokens**. Well within the 5k target.

---

## 7. Pitch matching logic (the "who gets pitched what" decision)

| User context | Soup pitch | Ointment pitch |
|---|---|---|
| Just declared 陽虛, no skin complaint | 花膠響螺片湯 OR 抗病毒湯 (補) | none |
| Declared 濕熱 + says 皮膚痕 | 彭魚鰓解毒湯 | 茶樹綠豆濕敏膏 |
| Declared 陰虛 + 口乾失眠 | 清心潤肺湯 OR 花旗蔘湯 | none |
| Says 咳 (no constitution yet) | none (wait for constitution) | none |
| Mom asks about kid 手足口病 | 彭魚鰓解毒湯 | none (ointments are adult-pitched) |
| Says 頭痛頭暈 + 平和體質 | 川芎白芷天麻湯 | none |

This logic lives in the **tool**, not the prompt. The tool ranks candidates and returns top N. LLM doesn't decide which products — it decides whether the timing feels right.

---

## 8. Image flow (no code changes)

Existing `_extract_images_into_bubbles()` (router.py:2425-2470) already handles `🖼️ <url>` markers in bubble text. Plan:

1. Each product card has `image_url` (uploaded to `data/media/products/` or hosted on healthy-food.hk-style CDN — TBD: where do we host these 13 product photos?)
2. `share_product` tool response includes the image URLs as `🖼️ <url>` lines in the bubble template
3. Router strips them, emits separate image bubbles before text
4. Cap: 2 image bubbles per turn (matches `max_items=2`)

**Decision needed from you:** where do the 3 ointment photos live? You provided box shots — we'd need them at stable URLs. Options:
- Upload to `/data/media/products/` and serve via FastAPI static route
- Upload to a CDN
- Skip images for now, text only

I'd go with **option 1** (FastAPI static) — already serves `data/media/` for acupoint videos. Zero new infra.

---

## 9. Checkout = WhatsApp deep link

Per Option (a) — no in-bot payment. Each product gets a pre-filled WhatsApp link:

```
https://wa.me/85252417448?text=想訂【彭魚鰓解毒湯 $120】
```

- `wa.me` opens WhatsApp with the text pre-filled
- 心宜中醫 staff sees who's ordering what and follows up
- Phone number lives in `configs/tcm-wellness.yaml`, NOT hardcoded
- **TBD: confirm 心宜中醫 order WhatsApp number** — placeholder above is the existing Jessica WA test number; we need the real customer service line

When the bubble renders, the link becomes a tap-to-open button in WhatsApp UI.

---

## 10. Regression checklist (post-implementation)

Run before merging — per CLAUDE.md Section 7.2 + add these:

- [ ] `find_knowledge_cards` still first in tool list (CLAUDE.md 7.2)
- [ ] `_enforce_role_question_first` still uses pre-turn snapshot (7.2)
- [ ] Classifier still skipped during onboarding (7.2)
- [ ] **NEW:** `recommend_paid_item` returns ≤2 items even when 5+ match (cap enforced)
- [ ] **NEW:** Same product never pitched twice in one session (dedup works)
- [ ] **NEW:** Empty `items[]` returned → Jessica skips Step 9c silently, moves to clinic invite (no awkward "我冇咩產品推薦")
- [ ] **NEW:** WhatsApp links render correctly in real WhatsApp client (manual test, 1 of each)
- [ ] **NEW:** Product images appear as separate bubble BEFORE pitch text
- [ ] **NEW:** Stress test 30-round mini run → `paid_item_pitched` ≥ 80% in cases where constitution + complaint match a product
- [ ] Prompt size budget still ≤ 5k tokens per execution path (`GET /api/admin/prompt-size`)

---

## 11. Phased timeline

### Phase 1 — Cards + catalog (4 hr)
- Write the 2 new JSON cards (10 soups + 3 ointments) with full schema
- Build `data/product_catalog.json` lookup
- Source/upload 13 product images
- Reindex Qdrant
- **Deliverable:** cards retrievable via `find_knowledge_cards` (even though we don't use it for pitch — verifies indexing)

### Phase 2 — Tool + matching logic (3 hr)
- Implement `src/tools/products.py`
- Unit tests: 8 scenarios (each constitution × 1, each complaint type × 1)
- Register tool in `agent.py`
- **Deliverable:** `python -c "from src.tools.products import recommend_paid_item; print(recommend_paid_item('濕熱', ['皮膚痕']))"` returns 2 items

### Phase 3 — Prompt + flow integration (3 hr)
- Refactor `share_product` in `sales.py` to accept product IDs
- Rewrite Step 9c in `sales_prompt.py`
- Add `paid_item_recommended` state flag in `flow_engine.py`
- Wire `paid_products.enabled` config flag
- **Deliverable:** local test conversation → constitution declared → product pitched

### Phase 4 — Image flow + WhatsApp deep links (2 hr)
- Wire image URLs through bubble template
- Test pre-filled WhatsApp links in real WhatsApp
- Add config for order phone number
- **Deliverable:** full end-to-end pitch with image + tap-to-order

### Phase 5 — Regression + stress test (2 hr)
- Run 30-round mini stress test (variant of `scripts/stress_test_tcm.py`)
- Verify all regression checklist items
- Verify prompt size budget
- **Deliverable:** green checklist, merge candidate

**Total: ~14 hr = 2 working days.**

---

## 12. Risks + things to watch

| Risk | Mitigation |
|---|---|
| **Jessica still mentions free DIY recipes when she should pitch paid** | Prompt rule: when `recommend_paid_item` returns items, suppress `find_knowledge_cards` soup retrieval that turn. Belt + suspenders. |
| **WhatsApp deep link gets rate-limited or flagged as spam** | Use 心宜中醫's customer service WA — they expect inbound orders. Don't blast >5 links/day per user (config cap). |
| **LLM invents products not in catalog** | Tool returns `product_id` whitelist. `share_product` validates ID exists in `product_catalog.json` and rejects unknown IDs. |
| **Prompt budget creeps past 5k** | Step 9c rewrite is +40 tokens net. If approaching budget, move the matching table from prompt to tool docstring. |
| **Images break (404, slow load)** | Host via FastAPI static (`data/media/products/`), preload at startup, fail-soft to text-only pitch if image missing. |
| **Same user gets pitched same product across sessions** | Out of scope for v1 — session-scoped dedup only. v2 can add SQLite `pitch_history` table if needed. |
| **彭魚鰓 / 海星 raise sustainability concerns from sensitive users** | Card text presents them as TCM-formulated soups with the indication, not the exotic ingredient. Mirror how 燕窩/魚翅 are described in existing cards. |

---

## 13. Open decisions (need your call before Phase 1)

1. **心宜中醫 order WhatsApp number** — what's the real number? Placeholder is 85252417448 (Jessica test).
2. **Product photo source** — do you have official 心宜中醫 photos for all 13, or only the 3 ointments shown? For soups, do we want stock food photography or actual product packaging?
3. **Should ointments be pitched WITHOUT constitution declared?** — If a user says 皮膚痕 in turn 2, do we pitch the ointment immediately, or wait for full constitution flow? My recommendation: **wait for constitution** even for ointments, to preserve the diagnostic narrative ("based on your 體質 + complaint, this works for you"). But could argue for fast-pitch when symptom is acute.
4. **Pricing display** — show as "$120" or "HK$120"? Existing Maca pitch uses plain dollar sign.

Once you answer these I can start Phase 1.

---

## Appendix A — Raw product data (from user)

### 湯水 (10 items)
```
彭魚鰓解毒湯 $120 — 清熱解毒、痘疹未清、手腳濕疹、暗瘡、手足口病、生蛇調理
清心潤肺湯 $48  — 捱夜失眠、心火盛、流鼻血、口腔潰瘍、皮膚乾燥、乾咳、口乾口苦
清肝明目湯 $68  — 眼睛乾澀、流眼水、舒緩眼睛疲勞、滋補肝腎
抗病毒湯  $88  — 增強免疫力、抗病毒、抗疲勞、化痰止咳、健脾胃、促進術後康復
花膠響螺片湯 $48 — 健脾補腎、滋陰養顏、調節荷爾蒙、提高免疫力
川芎白芷天麻湯 $48 — 頭痛頭暈、驅風活血、行氣止痛、健脾醒腦
海星止咳湯 $58 — 止咳潤肺、化痰、袪痰火核、扁桃腺發炎、喉嚨痛、聲沙
感冒止咳湯 $58 — 傷風感冒、喉嚨痛、止咳化痰、預防流感
止咳潤肺湯 $98 — 新咳久咳、感冒未清、氣管敏感、痰結氣喘
花旗蔘湯  $48 — 口乾口苦、心火性、喉嚨痛、失眠、腸胃濕熱
```

### 藥膏 (3 items)
```
茶樹綠豆濕敏膏 $90  — Double Green Ointment, 30g, Made in HK
                    Relieves itching, Australian Tea Tree Oil + 綠豆
蛋黃油乳液    $120 — Egg Yolk Oil Lotion, 100g, Made in HK
                    無香料/色素/礦物油, CO2 SFE 超臨界流體萃取法
                    蛋黃油 + 蒲背巴布 + 乳木果油 + 二大黃金護膚成份
止痕濕疹膏    $180 — 心宜中醫 Care Plus
                    (description TBD — need product details)
```
