# Care Plus 心宜中醫 — Product Index

**Source:** Extracted from `dr-baba-agent` on 2026-05-21.
**Order channel:** WhatsApp **+852 5241 7448** (`wa.me/85252417448`)
**Currency:** HKD
**Image note:** All 10 soup photos + 3 ointment photos received from Care Plus 心宜中醫. Stored at `../media/products/soups/` and `../media/products/`.

---

## 🍲 Soups (10 — HK$48–HK$120)

Pre-cooked therapeutic soups by Care Plus 心宜中醫. Pitched after constitution declared. Source card: `soups/tcm_paid_soups.json`.

| # | Name (中文) | Pinyin / Product ID | Price | One-liner | Image |
|---|---|---|---|---|---|
| 1 | 彭魚鰓解毒湯 | `soup_pengyu_jiedu` (Pengyu Jiedu) | HK$120 | 清熱解毒、皮膚問題首選 — 痘疹、暗瘡、濕疹、手足口、生蛇調理 | `../media/products/soups/soup_pengyu_jiedu.png` |
| 2 | 清心潤肺湯 | `soup_qingxin_runfei` (Qingxin Runfei) | HK$48 | 降心火、安神潤燥 — 捱夜失眠、心火盛、流鼻血、乾咳 | `../media/products/soups/soup_qingxin_runfei.png` |
| 3 | 清肝明目湯 | `soup_qinggan_mingmu` (Qinggan Mingmu) | HK$68 | 明目、舒緩眼疲勞 — 眼乾澀、流眼水、滋補肝腎 | `../media/products/soups/soup_qinggan_mingmu.png` |
| 4 | 抗病毒湯 | `soup_kang_bingdu` (Kang Bingdu) | HK$88 | 增免疫、健脾胃、病後恢復 — 抗病毒、抗疲勞、化痰止咳 | `../media/products/soups/soup_kang_bingdu.png` |
| 5 | 花膠響螺片湯 | `soup_huajiao_xiangluo` (Huajiao Xiangluo) | HK$48 | 滋陰養顏、調節荷爾蒙 — 健脾補腎、提高免疫力 | `../media/products/soups/soup_huajiao_xiangluo.png` |
| 6 | 川芎白芷天麻湯 | `soup_chuanxiong_tianma` (Chuanxiong Tianma) | HK$48 | 驅風活血止頭痛 — 頭痛頭暈、行氣止痛、健脾醒腦 ⚠️ 孕婦忌 | `../media/products/soups/soup_chuanxiong_tianma.png` |
| 7 | 海星止咳湯 | `soup_haixing_zhike` (Haixing Zhike) | HK$58 | 潤肺化痰、止聲沙 — 扁桃腺發炎、喉嚨痛、痰火核 | `../media/products/soups/soup_haixing_zhike.png` |
| 8 | 感冒止咳湯 | `soup_ganmao_zhike` (Ganmao Zhike) | HK$58 | 急性感冒首選 — 傷風、喉嚨痛、止咳化痰、預防流感 | `../media/products/soups/soup_ganmao_zhike.png` |
| 9 | 止咳潤肺湯 | `soup_zhike_runfei` (Zhike Runfei) | HK$98 | 強力潤肺、平喘 — 新咳久咳、氣管敏感、痰結氣喘 | `../media/products/soups/soup_zhike_runfei.png` |
| 10 | 花旗蔘湯 | `soup_huaqi_shen` (Huaqi Shen) | HK$48 | 清補唔上火、捱夜首選 — 口乾口苦、心火盛、失眠、腸胃濕熱 | `../media/products/soups/soup_huaqi_shen.png` |

---

## 💊 Ointments (3 — HK$90–HK$180)

External use only. Made in Hong Kong. Source card: `ointments/tcm_paid_ointments.json`.

| # | Name (中文) | English / Product ID | Price | Size | One-liner | Image |
|---|---|---|---|---|---|---|
| 1 | 茶樹綠豆濕敏膏 | Double Green Ointment / `ointment_chashu_lvdou` | HK$90 | 30g | 止痕消炎、輕度痕癢首選 — 澳洲茶樹油 + 綠豆，蚊咬、皮膚紅、輕度濕疹 | `../media/products/ointment_chashu_lvdou.jpg` |
| 2 | 蛋黃油乳液 | Egg Yolk Oil Lotion / `ointment_danhuang_lotion` | HK$120 | 100g | 深層滋潤、敏感肌專用、BB都用得 — CO2 SFE 萃取，無香料/色素/礦物油 | `../media/products/ointment_danhuang_lotion.jpg` |
| 3 | 止痕濕疹膏 | Care Plus Anti-Itch Eczema Cream / `ointment_zhihen_shizhen` | HK$180 | — | 中度至嚴重濕疹專用、心宜中醫自家配方 — 強效止痕、抑制濕疹、急性發作 | `../media/products/ointment_zhihen_shizhen.jpg` |

---

## File Layout

```
data/products/
├── PRODUCTS_INDEX.md            (this file)
├── product_catalog.json         (flat lookup, source-of-truth for recommend_paid_item tool)
├── soups/
│   └── tcm_paid_soups.json      (10 soup product card)
└── ointments/
    └── tcm_paid_ointments.json  (3 ointment product card)

data/media/products/
├── ointment_chashu_lvdou.jpg
├── ointment_danhuang_lotion.jpg
└── ointment_zhihen_shizhen.jpg

docs/
└── 心宜中醫-產品照-請求.md       (WhatsApp draft to request real soup photos from Care Plus)
```

---

## Image Status

- **Soups (10):** all `image_url` fields are `PLACEHOLDER_TO_BE_REPLACED` in the card; `product_catalog.json` points to external healthy-food.hk URLs marked as 示意圖. No local soup image files exist. Send the WhatsApp draft in `docs/心宜中醫-產品照-請求.md` to Care Plus to obtain the 10 official photos.
- **Ointments (3):** all 3 official Care Plus product photos extracted and copied to `data/media/products/`.

## Order Flow

Each product entry has a pre-filled WhatsApp deep link (`purchase_url`) that opens `wa.me/85252417448` with a Cantonese order message — e.g. `想訂【彭魚鰓解毒湯 HK$120】`. Tap = direct to Care Plus 心宜中醫 客服.

## Safety Reminders

- 孕婦慎用：彭魚鰓解毒湯、川芎白芷天麻湯（活血）、海星止咳湯、所有藥膏
- 急性感冒發燒期：抗病毒湯、花旗蔘湯 忌（閉門留寇）
- 嚴重症狀（持續 >2 週、發高燒、急性出血、大面積濕疹、滲液感染）→ 必須中醫師或西醫面診，唔好淨係靠湯水/藥膏
