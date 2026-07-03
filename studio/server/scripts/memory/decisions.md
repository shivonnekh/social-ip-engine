
## 2026-06-10 10:09 — server

### Architecture Decisions
- Key design decision: **CRM key = `ig_<igsid>`** — same per-person pattern as your group chat `g_<lid>`. Jessica's pipeline doesn't care that `phone` is actually an Instagram ID; it's just a routing key. Let me build it.
- Now update the tests to target the refactored core, add coverage for canned comments + FB + media interleaving:

### Decisions & Reasoning
- `gen_voice_clip.py` 的 code 入面 `DEFAULT_VOICE = "Cantonese_KindWoman"`（從 TCM-Jessica ported 過嚟），但 `script.md` 已確認用 **`Cantonese_GentleLady`**。
- **係一齊嘅** — 一個 Jessica pipeline、一個 CRM，三條 channel 共用。但用 **namespaced key** 分開每個人嘅記錄：
- 同一個人用 IG + WhatsApp = 兩條獨立記錄（暫時唔會自動 link，可接受）。
- ### Q1：Facebook comment 用咩 agent 講嘢？
- **預設係「唔用 agent」。** 你嘅 point 完全啱，我已經改咗架構。
- ### Q2：WhatsApp 幾時先直接用 Jessica agent？
- **WhatsApp 永遠用 Jessica agent。** 因為 WhatsApp 入嚟嘅都係已經想傾偈嘅人（1-on-1 對話）。Jessica 本身已經有：
- 4. **測試**：用另一個 account DM 你個 IG → 應該收到 Jessica 回覆；comment "gut" → 收到罐頭 DM


## 2026-06-10 10:10 — server

### Architecture Decisions
- Key design decision: **CRM key = `ig_<igsid>`** — same per-person pattern as your group chat `g_<lid>`. Jessica's pipeline doesn't care that `phone` is actually an Instagram ID; it's just a routing key. Let me build it.
- Now update the tests to target the refactored core, add coverage for canned comments + FB + media interleaving:

### Decisions & Reasoning
- `gen_voice_clip.py` 的 code 入面 `DEFAULT_VOICE = "Cantonese_KindWoman"`（從 TCM-Jessica ported 過嚟），但 `script.md` 已確認用 **`Cantonese_GentleLady`**。
- **係一齊嘅** — 一個 Jessica pipeline、一個 CRM，三條 channel 共用。但用 **namespaced key** 分開每個人嘅記錄：
- 同一個人用 IG + WhatsApp = 兩條獨立記錄（暫時唔會自動 link，可接受）。
- ### Q1：Facebook comment 用咩 agent 講嘢？
- **預設係「唔用 agent」。** 你嘅 point 完全啱，我已經改咗架構。
- ### Q2：WhatsApp 幾時先直接用 Jessica agent？
- **WhatsApp 永遠用 Jessica agent。** 因為 WhatsApp 入嚟嘅都係已經想傾偈嘅人（1-on-1 對話）。Jessica 本身已經有：
- 4. **測試**：用另一個 account DM 你個 IG → 應該收到 Jessica 回覆；comment "gut" → 收到罐頭 DM

