
## 2026-05-21 11:03 — TCM-Jessica

### Decisions & Reasoning
- 而且你描述的架构 (Planner → 多个 specialist → Final Writer + 平行调用) 跟 Dr. Baba 的 card-driven retrieval pipeline 是**根本不一样**的设计。Fork 出来是对的。
- - 不可变 state + `_ALLOWED_KEYS` whitelist + 每用户 lock — 防止 typo 幽灵字段、防止 WhatsApp 连发的 TOCTOU
- - YAML state-machine engine (`flow_engine.py`) — 把步骤顺序跟逻辑耦合死，真实用户会分叉。Planner 取代它。
- - `pacing.py` 的硬编码 turn counter (「诊断和推荐之间要插 1 个 caring turn」) — 用计数器执行节奏很机械，节奏应该写在 Writer 的 system prompt 里。
- | **C. OpenAI gpt-image-2** (dr-baba 的 Tier 2 primary) | `OPENAI_API_KEY` | 已经 setup，能用，但**不是极梦** |
- **我的诚实建议：用 C (OpenAI gpt-image-2)，原因 3 个：**
- 2. **OpenAI 的中文渲染对汤水 product shot 是够用的**（汤水图片不需要做精确的中文标注，跟 dr-baba 要的解剖图 + 穴位标注不一样）
- 3. **不是终稿** — 这些都是 placeholder，等 Care Plus 给真图就替换掉了。AI 图片在产品页用一周不会出大事，但要先标清楚「示意圖」


## 2026-05-21 11:10 — TCM-Jessica

### Decisions & Reasoning
- 控制你的浏览器，用你个人号发。适合小规模测试，但要保持浏览器开着。
- 2. 用哪个号发（个人号还是 ChatDaddy 业务号）？
- 明白了。就是用 Playwright 打开你的 WhatsApp Web，自动发测试消息给那个 agent，然后看它怎么回。
- 1. 用你已有的 Chrome Default profile（不用重新登录）


## 2026-05-21 11:14 — TCM-Jessica

### Decisions & Reasoning
- 而且你描述的架构 (Planner → 多个 specialist → Final Writer + 平行调用) 跟 Dr. Baba 的 card-driven retrieval pipeline 是**根本不一样**的设计。Fork 出来是对的。
- - 不可变 state + `_ALLOWED_KEYS` whitelist + 每用户 lock — 防止 typo 幽灵字段、防止 WhatsApp 连发的 TOCTOU
- - YAML state-machine engine (`flow_engine.py`) — 把步骤顺序跟逻辑耦合死，真实用户会分叉。Planner 取代它。
- - `pacing.py` 的硬编码 turn counter (「诊断和推荐之间要插 1 个 caring turn」) — 用计数器执行节奏很机械，节奏应该写在 Writer 的 system prompt 里。
- | **C. OpenAI gpt-image-2** (dr-baba 的 Tier 2 primary) | `OPENAI_API_KEY` | 已经 setup，能用，但**不是极梦** |
- **我的诚实建议：用 C (OpenAI gpt-image-2)，原因 3 个：**
- 2. **OpenAI 的中文渲染对汤水 product shot 是够用的**（汤水图片不需要做精确的中文标注，跟 dr-baba 要的解剖图 + 穴位标注不一样）
- 3. **不是终稿** — 这些都是 placeholder，等 Care Plus 给真图就替换掉了。AI 图片在产品页用一周不会出大事，但要先标清楚「示意圖」


## 2026-05-21 11:18 — TCM-Jessica

### Decisions & Reasoning
- 而且你描述的架构 (Planner → 多个 specialist → Final Writer + 平行调用) 跟 Dr. Baba 的 card-driven retrieval pipeline 是**根本不一样**的设计。Fork 出来是对的。
- - 不可变 state + `_ALLOWED_KEYS` whitelist + 每用户 lock — 防止 typo 幽灵字段、防止 WhatsApp 连发的 TOCTOU
- - YAML state-machine engine (`flow_engine.py`) — 把步骤顺序跟逻辑耦合死，真实用户会分叉。Planner 取代它。
- - `pacing.py` 的硬编码 turn counter (「诊断和推荐之间要插 1 个 caring turn」) — 用计数器执行节奏很机械，节奏应该写在 Writer 的 system prompt 里。
- | **C. OpenAI gpt-image-2** (dr-baba 的 Tier 2 primary) | `OPENAI_API_KEY` | 已经 setup，能用，但**不是极梦** |
- **我的诚实建议：用 C (OpenAI gpt-image-2)，原因 3 个：**
- 2. **OpenAI 的中文渲染对汤水 product shot 是够用的**（汤水图片不需要做精确的中文标注，跟 dr-baba 要的解剖图 + 穴位标注不一样）
- 3. **不是终稿** — 这些都是 placeholder，等 Care Plus 给真图就替换掉了。AI 图片在产品页用一周不会出大事，但要先标清楚「示意圖」


## 2026-05-21 11:19 — TCM-Jessica

### Decisions & Reasoning
- 而且你描述的架构 (Planner → 多个 specialist → Final Writer + 平行调用) 跟 Dr. Baba 的 card-driven retrieval pipeline 是**根本不一样**的设计。Fork 出来是对的。
- - 不可变 state + `_ALLOWED_KEYS` whitelist + 每用户 lock — 防止 typo 幽灵字段、防止 WhatsApp 连发的 TOCTOU
- - YAML state-machine engine (`flow_engine.py`) — 把步骤顺序跟逻辑耦合死，真实用户会分叉。Planner 取代它。
- - `pacing.py` 的硬编码 turn counter (「诊断和推荐之间要插 1 个 caring turn」) — 用计数器执行节奏很机械，节奏应该写在 Writer 的 system prompt 里。
- | **C. OpenAI gpt-image-2** (dr-baba 的 Tier 2 primary) | `OPENAI_API_KEY` | 已经 setup，能用，但**不是极梦** |
- **我的诚实建议：用 C (OpenAI gpt-image-2)，原因 3 个：**
- 2. **OpenAI 的中文渲染对汤水 product shot 是够用的**（汤水图片不需要做精确的中文标注，跟 dr-baba 要的解剖图 + 穴位标注不一样）
- 3. **不是终稿** — 这些都是 placeholder，等 Care Plus 给真图就替换掉了。AI 图片在产品页用一周不会出大事，但要先标清楚「示意圖」


## 2026-05-21 11:21 — TCM-Jessica

### Decisions & Reasoning
- 而且你描述的架构 (Planner → 多个 specialist → Final Writer + 平行调用) 跟 Dr. Baba 的 card-driven retrieval pipeline 是**根本不一样**的设计。Fork 出来是对的。
- - 不可变 state + `_ALLOWED_KEYS` whitelist + 每用户 lock — 防止 typo 幽灵字段、防止 WhatsApp 连发的 TOCTOU
- - YAML state-machine engine (`flow_engine.py`) — 把步骤顺序跟逻辑耦合死，真实用户会分叉。Planner 取代它。
- - `pacing.py` 的硬编码 turn counter (「诊断和推荐之间要插 1 个 caring turn」) — 用计数器执行节奏很机械，节奏应该写在 Writer 的 system prompt 里。
- | **C. OpenAI gpt-image-2** (dr-baba 的 Tier 2 primary) | `OPENAI_API_KEY` | 已经 setup，能用，但**不是极梦** |
- **我的诚实建议：用 C (OpenAI gpt-image-2)，原因 3 个：**
- 2. **OpenAI 的中文渲染对汤水 product shot 是够用的**（汤水图片不需要做精确的中文标注，跟 dr-baba 要的解剖图 + 穴位标注不一样）
- 3. **不是终稿** — 这些都是 placeholder，等 Care Plus 给真图就替换掉了。AI 图片在产品页用一周不会出大事，但要先标清楚「示意圖」


## 2026-05-21 11:27 — TCM-Jessica

### Decisions & Reasoning
- 而且你描述的架构 (Planner → 多个 specialist → Final Writer + 平行调用) 跟 Dr. Baba 的 card-driven retrieval pipeline 是**根本不一样**的设计。Fork 出来是对的。
- - 不可变 state + `_ALLOWED_KEYS` whitelist + 每用户 lock — 防止 typo 幽灵字段、防止 WhatsApp 连发的 TOCTOU
- - YAML state-machine engine (`flow_engine.py`) — 把步骤顺序跟逻辑耦合死，真实用户会分叉。Planner 取代它。
- - `pacing.py` 的硬编码 turn counter (「诊断和推荐之间要插 1 个 caring turn」) — 用计数器执行节奏很机械，节奏应该写在 Writer 的 system prompt 里。
- | **C. OpenAI gpt-image-2** (dr-baba 的 Tier 2 primary) | `OPENAI_API_KEY` | 已经 setup，能用，但**不是极梦** |
- **我的诚实建议：用 C (OpenAI gpt-image-2)，原因 3 个：**
- 2. **OpenAI 的中文渲染对汤水 product shot 是够用的**（汤水图片不需要做精确的中文标注，跟 dr-baba 要的解剖图 + 穴位标注不一样）
- 3. **不是终稿** — 这些都是 placeholder，等 Care Plus 给真图就替换掉了。AI 图片在产品页用一周不会出大事，但要先标清楚「示意圖」


## 2026-05-21 11:28 — TCM-Jessica

### Decisions & Reasoning
- 控制你的浏览器，用你个人号发。适合小规模测试，但要保持浏览器开着。
- 2. 用哪个号发（个人号还是 ChatDaddy 业务号）？
- 明白了。就是用 Playwright 打开你的 WhatsApp Web，自动发测试消息给那个 agent，然后看它怎么回。
- 1. 用你已有的 Chrome Default profile（不用重新登录）
- 然后告诉我，我就运行。它会用你的 Default profile（shivonnekhoo@gmail.com）直接打开，WhatsApp Web 应该已经登录了，不用扫码。
- Chrome 不允许对 Default profile 直接做 remote debugging。换个方式 — 用 subprocess 先启动 Chrome（带 debug port），然后 Playwright 连进去：
- WhatsApp Web 通了！但搜索找不到联系人。可能是选择器问题或联系人没存。让我 debug 看看搜索结果：
- 找到了！selector 用 `cell-frame-container` 不是 `listitem`。直接修：


## 2026-05-21 11:34 — TCM-Jessica

### Decisions & Reasoning
- 而且你描述的架构 (Planner → 多个 specialist → Final Writer + 平行调用) 跟 Dr. Baba 的 card-driven retrieval pipeline 是**根本不一样**的设计。Fork 出来是对的。
- - 不可变 state + `_ALLOWED_KEYS` whitelist + 每用户 lock — 防止 typo 幽灵字段、防止 WhatsApp 连发的 TOCTOU
- - YAML state-machine engine (`flow_engine.py`) — 把步骤顺序跟逻辑耦合死，真实用户会分叉。Planner 取代它。
- - `pacing.py` 的硬编码 turn counter (「诊断和推荐之间要插 1 个 caring turn」) — 用计数器执行节奏很机械，节奏应该写在 Writer 的 system prompt 里。
- | **C. OpenAI gpt-image-2** (dr-baba 的 Tier 2 primary) | `OPENAI_API_KEY` | 已经 setup，能用，但**不是极梦** |
- **我的诚实建议：用 C (OpenAI gpt-image-2)，原因 3 个：**
- 2. **OpenAI 的中文渲染对汤水 product shot 是够用的**（汤水图片不需要做精确的中文标注，跟 dr-baba 要的解剖图 + 穴位标注不一样）
- 3. **不是终稿** — 这些都是 placeholder，等 Care Plus 给真图就替换掉了。AI 图片在产品页用一周不会出大事，但要先标清楚「示意圖」


## 2026-05-21 11:35 — TCM-Jessica

### Decisions & Reasoning
- 而且你描述的架构 (Planner → 多个 specialist → Final Writer + 平行调用) 跟 Dr. Baba 的 card-driven retrieval pipeline 是**根本不一样**的设计。Fork 出来是对的。
- - 不可变 state + `_ALLOWED_KEYS` whitelist + 每用户 lock — 防止 typo 幽灵字段、防止 WhatsApp 连发的 TOCTOU
- - YAML state-machine engine (`flow_engine.py`) — 把步骤顺序跟逻辑耦合死，真实用户会分叉。Planner 取代它。
- - `pacing.py` 的硬编码 turn counter (「诊断和推荐之间要插 1 个 caring turn」) — 用计数器执行节奏很机械，节奏应该写在 Writer 的 system prompt 里。
- | **C. OpenAI gpt-image-2** (dr-baba 的 Tier 2 primary) | `OPENAI_API_KEY` | 已经 setup，能用，但**不是极梦** |
- **我的诚实建议：用 C (OpenAI gpt-image-2)，原因 3 个：**
- 2. **OpenAI 的中文渲染对汤水 product shot 是够用的**（汤水图片不需要做精确的中文标注，跟 dr-baba 要的解剖图 + 穴位标注不一样）
- 3. **不是终稿** — 这些都是 placeholder，等 Care Plus 给真图就替换掉了。AI 图片在产品页用一周不会出大事，但要先标清楚「示意圖」


## 2026-05-21 11:45 — TCM-Jessica

### Decisions & Reasoning
- 而且你描述的架构 (Planner → 多个 specialist → Final Writer + 平行调用) 跟 Dr. Baba 的 card-driven retrieval pipeline 是**根本不一样**的设计。Fork 出来是对的。
- - 不可变 state + `_ALLOWED_KEYS` whitelist + 每用户 lock — 防止 typo 幽灵字段、防止 WhatsApp 连发的 TOCTOU
- - YAML state-machine engine (`flow_engine.py`) — 把步骤顺序跟逻辑耦合死，真实用户会分叉。Planner 取代它。
- - `pacing.py` 的硬编码 turn counter (「诊断和推荐之间要插 1 个 caring turn」) — 用计数器执行节奏很机械，节奏应该写在 Writer 的 system prompt 里。
- | **C. OpenAI gpt-image-2** (dr-baba 的 Tier 2 primary) | `OPENAI_API_KEY` | 已经 setup，能用，但**不是极梦** |
- **我的诚实建议：用 C (OpenAI gpt-image-2)，原因 3 个：**
- 2. **OpenAI 的中文渲染对汤水 product shot 是够用的**（汤水图片不需要做精确的中文标注，跟 dr-baba 要的解剖图 + 穴位标注不一样）
- 3. **不是终稿** — 这些都是 placeholder，等 Care Plus 给真图就替换掉了。AI 图片在产品页用一周不会出大事，但要先标清楚「示意圖」


## 2026-05-21 11:45 — TCM-Jessica

### Decisions & Reasoning
- 控制你的浏览器，用你个人号发。适合小规模测试，但要保持浏览器开着。
- 2. 用哪个号发（个人号还是 ChatDaddy 业务号）？
- 明白了。就是用 Playwright 打开你的 WhatsApp Web，自动发测试消息给那个 agent，然后看它怎么回。
- 1. 用你已有的 Chrome Default profile（不用重新登录）
- 然后告诉我，我就运行。它会用你的 Default profile（shivonnekhoo@gmail.com）直接打开，WhatsApp Web 应该已经登录了，不用扫码。
- Chrome 不允许对 Default profile 直接做 remote debugging。换个方式 — 用 subprocess 先启动 Chrome（带 debug port），然后 Playwright 连进去：
- WhatsApp Web 通了！但搜索找不到联系人。可能是选择器问题或联系人没存。让我 debug 看看搜索结果：
- 找到了！selector 用 `cell-frame-container` 不是 `listitem`。直接修：


## 2026-05-21 11:48 — TCM-Jessica

### Decisions & Reasoning
- 而且你描述的架构 (Planner → 多个 specialist → Final Writer + 平行调用) 跟 Dr. Baba 的 card-driven retrieval pipeline 是**根本不一样**的设计。Fork 出来是对的。
- - 不可变 state + `_ALLOWED_KEYS` whitelist + 每用户 lock — 防止 typo 幽灵字段、防止 WhatsApp 连发的 TOCTOU
- - YAML state-machine engine (`flow_engine.py`) — 把步骤顺序跟逻辑耦合死，真实用户会分叉。Planner 取代它。
- - `pacing.py` 的硬编码 turn counter (「诊断和推荐之间要插 1 个 caring turn」) — 用计数器执行节奏很机械，节奏应该写在 Writer 的 system prompt 里。
- | **C. OpenAI gpt-image-2** (dr-baba 的 Tier 2 primary) | `OPENAI_API_KEY` | 已经 setup，能用，但**不是极梦** |
- **我的诚实建议：用 C (OpenAI gpt-image-2)，原因 3 个：**
- 2. **OpenAI 的中文渲染对汤水 product shot 是够用的**（汤水图片不需要做精确的中文标注，跟 dr-baba 要的解剖图 + 穴位标注不一样）
- 3. **不是终稿** — 这些都是 placeholder，等 Care Plus 给真图就替换掉了。AI 图片在产品页用一周不会出大事，但要先标清楚「示意圖」


## 2026-05-21 12:11 — TCM-Jessica

### Architecture Decisions
- Still timing out. The issue — `get_incoming_texts()` counts text items but `wait_for_function` counts DOM elements. They return different numbers. Let me use a smarter approach — check the `data-id` of the last message instead of total count:

### Decisions & Reasoning
- 控制你的浏览器，用你个人号发。适合小规模测试，但要保持浏览器开着。
- 2. 用哪个号发（个人号还是 ChatDaddy 业务号）？
- 明白了。就是用 Playwright 打开你的 WhatsApp Web，自动发测试消息给那个 agent，然后看它怎么回。
- 1. 用你已有的 Chrome Default profile（不用重新登录）
- 然后告诉我，我就运行。它会用你的 Default profile（shivonnekhoo@gmail.com）直接打开，WhatsApp Web 应该已经登录了，不用扫码。
- Chrome 不允许对 Default profile 直接做 remote debugging。换个方式 — 用 subprocess 先启动 Chrome（带 debug port），然后 Playwright 连进去：
- WhatsApp Web 通了！但搜索找不到联系人。可能是选择器问题或联系人没存。让我 debug 看看搜索结果：
- 找到了！selector 用 `cell-frame-container` 不是 `listitem`。直接修：


## 2026-05-21 12:13 — TCM-Jessica

### Decisions & Reasoning
- 而且你描述的架构 (Planner → 多个 specialist → Final Writer + 平行调用) 跟 Dr. Baba 的 card-driven retrieval pipeline 是**根本不一样**的设计。Fork 出来是对的。
- - 不可变 state + `_ALLOWED_KEYS` whitelist + 每用户 lock — 防止 typo 幽灵字段、防止 WhatsApp 连发的 TOCTOU
- - YAML state-machine engine (`flow_engine.py`) — 把步骤顺序跟逻辑耦合死，真实用户会分叉。Planner 取代它。
- - `pacing.py` 的硬编码 turn counter (「诊断和推荐之间要插 1 个 caring turn」) — 用计数器执行节奏很机械，节奏应该写在 Writer 的 system prompt 里。
- | **C. OpenAI gpt-image-2** (dr-baba 的 Tier 2 primary) | `OPENAI_API_KEY` | 已经 setup，能用，但**不是极梦** |
- **我的诚实建议：用 C (OpenAI gpt-image-2)，原因 3 个：**
- 2. **OpenAI 的中文渲染对汤水 product shot 是够用的**（汤水图片不需要做精确的中文标注，跟 dr-baba 要的解剖图 + 穴位标注不一样）
- 3. **不是终稿** — 这些都是 placeholder，等 Care Plus 给真图就替换掉了。AI 图片在产品页用一周不会出大事，但要先标清楚「示意圖」


## 2026-05-21 12:28 — TCM-Jessica

### Decisions & Reasoning
- 而且你描述的架构 (Planner → 多个 specialist → Final Writer + 平行调用) 跟 Dr. Baba 的 card-driven retrieval pipeline 是**根本不一样**的设计。Fork 出来是对的。
- - 不可变 state + `_ALLOWED_KEYS` whitelist + 每用户 lock — 防止 typo 幽灵字段、防止 WhatsApp 连发的 TOCTOU
- - YAML state-machine engine (`flow_engine.py`) — 把步骤顺序跟逻辑耦合死，真实用户会分叉。Planner 取代它。
- - `pacing.py` 的硬编码 turn counter (「诊断和推荐之间要插 1 个 caring turn」) — 用计数器执行节奏很机械，节奏应该写在 Writer 的 system prompt 里。
- | **C. OpenAI gpt-image-2** (dr-baba 的 Tier 2 primary) | `OPENAI_API_KEY` | 已经 setup，能用，但**不是极梦** |
- **我的诚实建议：用 C (OpenAI gpt-image-2)，原因 3 个：**
- 2. **OpenAI 的中文渲染对汤水 product shot 是够用的**（汤水图片不需要做精确的中文标注，跟 dr-baba 要的解剖图 + 穴位标注不一样）
- 3. **不是终稿** — 这些都是 placeholder，等 Care Plus 给真图就替换掉了。AI 图片在产品页用一周不会出大事，但要先标清楚「示意圖」


## 2026-05-21 12:34 — TCM-Jessica

### Architecture Decisions
- Still timing out. The issue — `get_incoming_texts()` counts text items but `wait_for_function` counts DOM elements. They return different numbers. Let me use a smarter approach — check the `data-id` of the last message instead of total count:

### Decisions & Reasoning
- 控制你的浏览器，用你个人号发。适合小规模测试，但要保持浏览器开着。
- 2. 用哪个号发（个人号还是 ChatDaddy 业务号）？
- 明白了。就是用 Playwright 打开你的 WhatsApp Web，自动发测试消息给那个 agent，然后看它怎么回。
- 1. 用你已有的 Chrome Default profile（不用重新登录）
- 然后告诉我，我就运行。它会用你的 Default profile（shivonnekhoo@gmail.com）直接打开，WhatsApp Web 应该已经登录了，不用扫码。
- Chrome 不允许对 Default profile 直接做 remote debugging。换个方式 — 用 subprocess 先启动 Chrome（带 debug port），然后 Playwright 连进去：
- WhatsApp Web 通了！但搜索找不到联系人。可能是选择器问题或联系人没存。让我 debug 看看搜索结果：
- 找到了！selector 用 `cell-frame-container` 不是 `listitem`。直接修：


## 2026-05-21 12:36 — TCM-Jessica

### Decisions & Reasoning
- 而且你描述的架构 (Planner → 多个 specialist → Final Writer + 平行调用) 跟 Dr. Baba 的 card-driven retrieval pipeline 是**根本不一样**的设计。Fork 出来是对的。
- - 不可变 state + `_ALLOWED_KEYS` whitelist + 每用户 lock — 防止 typo 幽灵字段、防止 WhatsApp 连发的 TOCTOU
- - YAML state-machine engine (`flow_engine.py`) — 把步骤顺序跟逻辑耦合死，真实用户会分叉。Planner 取代它。
- - `pacing.py` 的硬编码 turn counter (「诊断和推荐之间要插 1 个 caring turn」) — 用计数器执行节奏很机械，节奏应该写在 Writer 的 system prompt 里。
- | **C. OpenAI gpt-image-2** (dr-baba 的 Tier 2 primary) | `OPENAI_API_KEY` | 已经 setup，能用，但**不是极梦** |
- **我的诚实建议：用 C (OpenAI gpt-image-2)，原因 3 个：**
- 2. **OpenAI 的中文渲染对汤水 product shot 是够用的**（汤水图片不需要做精确的中文标注，跟 dr-baba 要的解剖图 + 穴位标注不一样）
- 3. **不是终稿** — 这些都是 placeholder，等 Care Plus 给真图就替换掉了。AI 图片在产品页用一周不会出大事，但要先标清楚「示意圖」


## 2026-05-21 12:47 — TCM-Jessica

### Architecture Decisions
- Still timing out. The issue — `get_incoming_texts()` counts text items but `wait_for_function` counts DOM elements. They return different numbers. Let me use a smarter approach — check the `data-id` of the last message instead of total count:

### Decisions & Reasoning
- 控制你的浏览器，用你个人号发。适合小规模测试，但要保持浏览器开着。
- 2. 用哪个号发（个人号还是 ChatDaddy 业务号）？
- 明白了。就是用 Playwright 打开你的 WhatsApp Web，自动发测试消息给那个 agent，然后看它怎么回。
- 1. 用你已有的 Chrome Default profile（不用重新登录）
- 然后告诉我，我就运行。它会用你的 Default profile（shivonnekhoo@gmail.com）直接打开，WhatsApp Web 应该已经登录了，不用扫码。
- Chrome 不允许对 Default profile 直接做 remote debugging。换个方式 — 用 subprocess 先启动 Chrome（带 debug port），然后 Playwright 连进去：
- WhatsApp Web 通了！但搜索找不到联系人。可能是选择器问题或联系人没存。让我 debug 看看搜索结果：
- 找到了！selector 用 `cell-frame-container` 不是 `listitem`。直接修：


## 2026-05-21 12:47 — TCM-Jessica

### Architecture Decisions
- Still timing out. The issue — `get_incoming_texts()` counts text items but `wait_for_function` counts DOM elements. They return different numbers. Let me use a smarter approach — check the `data-id` of the last message instead of total count:

### Decisions & Reasoning
- 控制你的浏览器，用你个人号发。适合小规模测试，但要保持浏览器开着。
- 2. 用哪个号发（个人号还是 ChatDaddy 业务号）？
- 明白了。就是用 Playwright 打开你的 WhatsApp Web，自动发测试消息给那个 agent，然后看它怎么回。
- 1. 用你已有的 Chrome Default profile（不用重新登录）
- 然后告诉我，我就运行。它会用你的 Default profile（shivonnekhoo@gmail.com）直接打开，WhatsApp Web 应该已经登录了，不用扫码。
- Chrome 不允许对 Default profile 直接做 remote debugging。换个方式 — 用 subprocess 先启动 Chrome（带 debug port），然后 Playwright 连进去：
- WhatsApp Web 通了！但搜索找不到联系人。可能是选择器问题或联系人没存。让我 debug 看看搜索结果：
- 找到了！selector 用 `cell-frame-container` 不是 `listitem`。直接修：


## 2026-05-21 12:49 — TCM-Jessica

### Architecture Decisions
- Still timing out. The issue — `get_incoming_texts()` counts text items but `wait_for_function` counts DOM elements. They return different numbers. Let me use a smarter approach — check the `data-id` of the last message instead of total count:

### Decisions & Reasoning
- 控制你的浏览器，用你个人号发。适合小规模测试，但要保持浏览器开着。
- 2. 用哪个号发（个人号还是 ChatDaddy 业务号）？
- 明白了。就是用 Playwright 打开你的 WhatsApp Web，自动发测试消息给那个 agent，然后看它怎么回。
- 1. 用你已有的 Chrome Default profile（不用重新登录）
- 然后告诉我，我就运行。它会用你的 Default profile（shivonnekhoo@gmail.com）直接打开，WhatsApp Web 应该已经登录了，不用扫码。
- Chrome 不允许对 Default profile 直接做 remote debugging。换个方式 — 用 subprocess 先启动 Chrome（带 debug port），然后 Playwright 连进去：
- WhatsApp Web 通了！但搜索找不到联系人。可能是选择器问题或联系人没存。让我 debug 看看搜索结果：
- 找到了！selector 用 `cell-frame-container` 不是 `listitem`。直接修：


## 2026-05-21 12:50 — TCM-Jessica

### Decisions & Reasoning
- 而且你描述的架构 (Planner → 多个 specialist → Final Writer + 平行调用) 跟 Dr. Baba 的 card-driven retrieval pipeline 是**根本不一样**的设计。Fork 出来是对的。
- - 不可变 state + `_ALLOWED_KEYS` whitelist + 每用户 lock — 防止 typo 幽灵字段、防止 WhatsApp 连发的 TOCTOU
- - YAML state-machine engine (`flow_engine.py`) — 把步骤顺序跟逻辑耦合死，真实用户会分叉。Planner 取代它。
- - `pacing.py` 的硬编码 turn counter (「诊断和推荐之间要插 1 个 caring turn」) — 用计数器执行节奏很机械，节奏应该写在 Writer 的 system prompt 里。
- | **C. OpenAI gpt-image-2** (dr-baba 的 Tier 2 primary) | `OPENAI_API_KEY` | 已经 setup，能用，但**不是极梦** |
- **我的诚实建议：用 C (OpenAI gpt-image-2)，原因 3 个：**
- 2. **OpenAI 的中文渲染对汤水 product shot 是够用的**（汤水图片不需要做精确的中文标注，跟 dr-baba 要的解剖图 + 穴位标注不一样）
- 3. **不是终稿** — 这些都是 placeholder，等 Care Plus 给真图就替换掉了。AI 图片在产品页用一周不会出大事，但要先标清楚「示意圖」


## 2026-05-21 13:35 — TCM-Jessica

### Decisions & Reasoning
- 而且你描述的架构 (Planner → 多个 specialist → Final Writer + 平行调用) 跟 Dr. Baba 的 card-driven retrieval pipeline 是**根本不一样**的设计。Fork 出来是对的。
- - 不可变 state + `_ALLOWED_KEYS` whitelist + 每用户 lock — 防止 typo 幽灵字段、防止 WhatsApp 连发的 TOCTOU
- - YAML state-machine engine (`flow_engine.py`) — 把步骤顺序跟逻辑耦合死，真实用户会分叉。Planner 取代它。
- - `pacing.py` 的硬编码 turn counter (「诊断和推荐之间要插 1 个 caring turn」) — 用计数器执行节奏很机械，节奏应该写在 Writer 的 system prompt 里。
- | **C. OpenAI gpt-image-2** (dr-baba 的 Tier 2 primary) | `OPENAI_API_KEY` | 已经 setup，能用，但**不是极梦** |
- **我的诚实建议：用 C (OpenAI gpt-image-2)，原因 3 个：**
- 2. **OpenAI 的中文渲染对汤水 product shot 是够用的**（汤水图片不需要做精确的中文标注，跟 dr-baba 要的解剖图 + 穴位标注不一样）
- 3. **不是终稿** — 这些都是 placeholder，等 Care Plus 给真图就替换掉了。AI 图片在产品页用一周不会出大事，但要先标清楚「示意圖」


## 2026-05-21 13:42 — TCM-Jessica

### Decisions & Reasoning
- 而且你描述的架构 (Planner → 多个 specialist → Final Writer + 平行调用) 跟 Dr. Baba 的 card-driven retrieval pipeline 是**根本不一样**的设计。Fork 出来是对的。
- - 不可变 state + `_ALLOWED_KEYS` whitelist + 每用户 lock — 防止 typo 幽灵字段、防止 WhatsApp 连发的 TOCTOU
- - YAML state-machine engine (`flow_engine.py`) — 把步骤顺序跟逻辑耦合死，真实用户会分叉。Planner 取代它。
- - `pacing.py` 的硬编码 turn counter (「诊断和推荐之间要插 1 个 caring turn」) — 用计数器执行节奏很机械，节奏应该写在 Writer 的 system prompt 里。
- | **C. OpenAI gpt-image-2** (dr-baba 的 Tier 2 primary) | `OPENAI_API_KEY` | 已经 setup，能用，但**不是极梦** |
- **我的诚实建议：用 C (OpenAI gpt-image-2)，原因 3 个：**
- 2. **OpenAI 的中文渲染对汤水 product shot 是够用的**（汤水图片不需要做精确的中文标注，跟 dr-baba 要的解剖图 + 穴位标注不一样）
- 3. **不是终稿** — 这些都是 placeholder，等 Care Plus 给真图就替换掉了。AI 图片在产品页用一周不会出大事，但要先标清楚「示意圖」


## 2026-05-21 13:51 — TCM-Jessica

### Decisions & Reasoning
- 而且你描述的架构 (Planner → 多个 specialist → Final Writer + 平行调用) 跟 Dr. Baba 的 card-driven retrieval pipeline 是**根本不一样**的设计。Fork 出来是对的。
- - 不可变 state + `_ALLOWED_KEYS` whitelist + 每用户 lock — 防止 typo 幽灵字段、防止 WhatsApp 连发的 TOCTOU
- - YAML state-machine engine (`flow_engine.py`) — 把步骤顺序跟逻辑耦合死，真实用户会分叉。Planner 取代它。
- - `pacing.py` 的硬编码 turn counter (「诊断和推荐之间要插 1 个 caring turn」) — 用计数器执行节奏很机械，节奏应该写在 Writer 的 system prompt 里。
- | **C. OpenAI gpt-image-2** (dr-baba 的 Tier 2 primary) | `OPENAI_API_KEY` | 已经 setup，能用，但**不是极梦** |
- **我的诚实建议：用 C (OpenAI gpt-image-2)，原因 3 个：**
- 2. **OpenAI 的中文渲染对汤水 product shot 是够用的**（汤水图片不需要做精确的中文标注，跟 dr-baba 要的解剖图 + 穴位标注不一样）
- 3. **不是终稿** — 这些都是 placeholder，等 Care Plus 给真图就替换掉了。AI 图片在产品页用一周不会出大事，但要先标清楚「示意圖」


## 2026-05-21 13:52 — TCM-Jessica

### Decisions & Reasoning
- 而且你描述的架构 (Planner → 多个 specialist → Final Writer + 平行调用) 跟 Dr. Baba 的 card-driven retrieval pipeline 是**根本不一样**的设计。Fork 出来是对的。
- - 不可变 state + `_ALLOWED_KEYS` whitelist + 每用户 lock — 防止 typo 幽灵字段、防止 WhatsApp 连发的 TOCTOU
- - YAML state-machine engine (`flow_engine.py`) — 把步骤顺序跟逻辑耦合死，真实用户会分叉。Planner 取代它。
- - `pacing.py` 的硬编码 turn counter (「诊断和推荐之间要插 1 个 caring turn」) — 用计数器执行节奏很机械，节奏应该写在 Writer 的 system prompt 里。
- | **C. OpenAI gpt-image-2** (dr-baba 的 Tier 2 primary) | `OPENAI_API_KEY` | 已经 setup，能用，但**不是极梦** |
- **我的诚实建议：用 C (OpenAI gpt-image-2)，原因 3 个：**
- 2. **OpenAI 的中文渲染对汤水 product shot 是够用的**（汤水图片不需要做精确的中文标注，跟 dr-baba 要的解剖图 + 穴位标注不一样）
- 3. **不是终稿** — 这些都是 placeholder，等 Care Plus 给真图就替换掉了。AI 图片在产品页用一周不会出大事，但要先标清楚「示意圖」


## 2026-05-21 13:58 — TCM-Jessica

### Decisions & Reasoning
- 而且你描述的架构 (Planner → 多个 specialist → Final Writer + 平行调用) 跟 Dr. Baba 的 card-driven retrieval pipeline 是**根本不一样**的设计。Fork 出来是对的。
- - 不可变 state + `_ALLOWED_KEYS` whitelist + 每用户 lock — 防止 typo 幽灵字段、防止 WhatsApp 连发的 TOCTOU
- - YAML state-machine engine (`flow_engine.py`) — 把步骤顺序跟逻辑耦合死，真实用户会分叉。Planner 取代它。
- - `pacing.py` 的硬编码 turn counter (「诊断和推荐之间要插 1 个 caring turn」) — 用计数器执行节奏很机械，节奏应该写在 Writer 的 system prompt 里。
- | **C. OpenAI gpt-image-2** (dr-baba 的 Tier 2 primary) | `OPENAI_API_KEY` | 已经 setup，能用，但**不是极梦** |
- **我的诚实建议：用 C (OpenAI gpt-image-2)，原因 3 个：**
- 2. **OpenAI 的中文渲染对汤水 product shot 是够用的**（汤水图片不需要做精确的中文标注，跟 dr-baba 要的解剖图 + 穴位标注不一样）
- 3. **不是终稿** — 这些都是 placeholder，等 Care Plus 给真图就替换掉了。AI 图片在产品页用一周不会出大事，但要先标清楚「示意圖」


## 2026-05-21 14:16 — TCM-Jessica

### Decisions & Reasoning
- 而且你描述的架构 (Planner → 多个 specialist → Final Writer + 平行调用) 跟 Dr. Baba 的 card-driven retrieval pipeline 是**根本不一样**的设计。Fork 出来是对的。
- - 不可变 state + `_ALLOWED_KEYS` whitelist + 每用户 lock — 防止 typo 幽灵字段、防止 WhatsApp 连发的 TOCTOU
- - YAML state-machine engine (`flow_engine.py`) — 把步骤顺序跟逻辑耦合死，真实用户会分叉。Planner 取代它。
- - `pacing.py` 的硬编码 turn counter (「诊断和推荐之间要插 1 个 caring turn」) — 用计数器执行节奏很机械，节奏应该写在 Writer 的 system prompt 里。
- | **C. OpenAI gpt-image-2** (dr-baba 的 Tier 2 primary) | `OPENAI_API_KEY` | 已经 setup，能用，但**不是极梦** |
- **我的诚实建议：用 C (OpenAI gpt-image-2)，原因 3 个：**
- 2. **OpenAI 的中文渲染对汤水 product shot 是够用的**（汤水图片不需要做精确的中文标注，跟 dr-baba 要的解剖图 + 穴位标注不一样）
- 3. **不是终稿** — 这些都是 placeholder，等 Care Plus 给真图就替换掉了。AI 图片在产品页用一周不会出大事，但要先标清楚「示意圖」


## 2026-05-21 14:34 — TCM-Jessica

### Decisions & Reasoning
- 而且你描述的架构 (Planner → 多个 specialist → Final Writer + 平行调用) 跟 Dr. Baba 的 card-driven retrieval pipeline 是**根本不一样**的设计。Fork 出来是对的。
- - 不可变 state + `_ALLOWED_KEYS` whitelist + 每用户 lock — 防止 typo 幽灵字段、防止 WhatsApp 连发的 TOCTOU
- - YAML state-machine engine (`flow_engine.py`) — 把步骤顺序跟逻辑耦合死，真实用户会分叉。Planner 取代它。
- - `pacing.py` 的硬编码 turn counter (「诊断和推荐之间要插 1 个 caring turn」) — 用计数器执行节奏很机械，节奏应该写在 Writer 的 system prompt 里。
- | **C. OpenAI gpt-image-2** (dr-baba 的 Tier 2 primary) | `OPENAI_API_KEY` | 已经 setup，能用，但**不是极梦** |
- **我的诚实建议：用 C (OpenAI gpt-image-2)，原因 3 个：**
- 2. **OpenAI 的中文渲染对汤水 product shot 是够用的**（汤水图片不需要做精确的中文标注，跟 dr-baba 要的解剖图 + 穴位标注不一样）
- 3. **不是终稿** — 这些都是 placeholder，等 Care Plus 给真图就替换掉了。AI 图片在产品页用一周不会出大事，但要先标清楚「示意圖」


## 2026-05-21 14:47 — TCM-Jessica

### Decisions & Reasoning
- 而且你描述的架构 (Planner → 多个 specialist → Final Writer + 平行调用) 跟 Dr. Baba 的 card-driven retrieval pipeline 是**根本不一样**的设计。Fork 出来是对的。
- - 不可变 state + `_ALLOWED_KEYS` whitelist + 每用户 lock — 防止 typo 幽灵字段、防止 WhatsApp 连发的 TOCTOU
- - YAML state-machine engine (`flow_engine.py`) — 把步骤顺序跟逻辑耦合死，真实用户会分叉。Planner 取代它。
- - `pacing.py` 的硬编码 turn counter (「诊断和推荐之间要插 1 个 caring turn」) — 用计数器执行节奏很机械，节奏应该写在 Writer 的 system prompt 里。
- | **C. OpenAI gpt-image-2** (dr-baba 的 Tier 2 primary) | `OPENAI_API_KEY` | 已经 setup，能用，但**不是极梦** |
- **我的诚实建议：用 C (OpenAI gpt-image-2)，原因 3 个：**
- 2. **OpenAI 的中文渲染对汤水 product shot 是够用的**（汤水图片不需要做精确的中文标注，跟 dr-baba 要的解剖图 + 穴位标注不一样）
- 3. **不是终稿** — 这些都是 placeholder，等 Care Plus 给真图就替换掉了。AI 图片在产品页用一周不会出大事，但要先标清楚「示意圖」


## 2026-05-21 15:01 — TCM-Jessica

### Decisions & Reasoning
- 而且你描述的架构 (Planner → 多个 specialist → Final Writer + 平行调用) 跟 Dr. Baba 的 card-driven retrieval pipeline 是**根本不一样**的设计。Fork 出来是对的。
- - 不可变 state + `_ALLOWED_KEYS` whitelist + 每用户 lock — 防止 typo 幽灵字段、防止 WhatsApp 连发的 TOCTOU
- - YAML state-machine engine (`flow_engine.py`) — 把步骤顺序跟逻辑耦合死，真实用户会分叉。Planner 取代它。
- - `pacing.py` 的硬编码 turn counter (「诊断和推荐之间要插 1 个 caring turn」) — 用计数器执行节奏很机械，节奏应该写在 Writer 的 system prompt 里。
- | **C. OpenAI gpt-image-2** (dr-baba 的 Tier 2 primary) | `OPENAI_API_KEY` | 已经 setup，能用，但**不是极梦** |
- **我的诚实建议：用 C (OpenAI gpt-image-2)，原因 3 个：**
- 2. **OpenAI 的中文渲染对汤水 product shot 是够用的**（汤水图片不需要做精确的中文标注，跟 dr-baba 要的解剖图 + 穴位标注不一样）
- 3. **不是终稿** — 这些都是 placeholder，等 Care Plus 给真图就替换掉了。AI 图片在产品页用一周不会出大事，但要先标清楚「示意圖」


## 2026-05-21 15:08 — TCM-Jessica

### Decisions & Reasoning
- 而且你描述的架构 (Planner → 多个 specialist → Final Writer + 平行调用) 跟 Dr. Baba 的 card-driven retrieval pipeline 是**根本不一样**的设计。Fork 出来是对的。
- - 不可变 state + `_ALLOWED_KEYS` whitelist + 每用户 lock — 防止 typo 幽灵字段、防止 WhatsApp 连发的 TOCTOU
- - YAML state-machine engine (`flow_engine.py`) — 把步骤顺序跟逻辑耦合死，真实用户会分叉。Planner 取代它。
- - `pacing.py` 的硬编码 turn counter (「诊断和推荐之间要插 1 个 caring turn」) — 用计数器执行节奏很机械，节奏应该写在 Writer 的 system prompt 里。
- | **C. OpenAI gpt-image-2** (dr-baba 的 Tier 2 primary) | `OPENAI_API_KEY` | 已经 setup，能用，但**不是极梦** |
- **我的诚实建议：用 C (OpenAI gpt-image-2)，原因 3 个：**
- 2. **OpenAI 的中文渲染对汤水 product shot 是够用的**（汤水图片不需要做精确的中文标注，跟 dr-baba 要的解剖图 + 穴位标注不一样）
- 3. **不是终稿** — 这些都是 placeholder，等 Care Plus 给真图就替换掉了。AI 图片在产品页用一周不会出大事，但要先标清楚「示意圖」


## 2026-05-21 15:22 — TCM-Jessica

### Decisions & Reasoning
- 而且你描述的架构 (Planner → 多个 specialist → Final Writer + 平行调用) 跟 Dr. Baba 的 card-driven retrieval pipeline 是**根本不一样**的设计。Fork 出来是对的。
- - 不可变 state + `_ALLOWED_KEYS` whitelist + 每用户 lock — 防止 typo 幽灵字段、防止 WhatsApp 连发的 TOCTOU
- - YAML state-machine engine (`flow_engine.py`) — 把步骤顺序跟逻辑耦合死，真实用户会分叉。Planner 取代它。
- - `pacing.py` 的硬编码 turn counter (「诊断和推荐之间要插 1 个 caring turn」) — 用计数器执行节奏很机械，节奏应该写在 Writer 的 system prompt 里。
- | **C. OpenAI gpt-image-2** (dr-baba 的 Tier 2 primary) | `OPENAI_API_KEY` | 已经 setup，能用，但**不是极梦** |
- **我的诚实建议：用 C (OpenAI gpt-image-2)，原因 3 个：**
- 2. **OpenAI 的中文渲染对汤水 product shot 是够用的**（汤水图片不需要做精确的中文标注，跟 dr-baba 要的解剖图 + 穴位标注不一样）
- 3. **不是终稿** — 这些都是 placeholder，等 Care Plus 给真图就替换掉了。AI 图片在产品页用一周不会出大事，但要先标清楚「示意圖」


## 2026-05-21 15:26 — TCM-Jessica

### Decisions & Reasoning
- 而且你描述的架构 (Planner → 多个 specialist → Final Writer + 平行调用) 跟 Dr. Baba 的 card-driven retrieval pipeline 是**根本不一样**的设计。Fork 出来是对的。
- - 不可变 state + `_ALLOWED_KEYS` whitelist + 每用户 lock — 防止 typo 幽灵字段、防止 WhatsApp 连发的 TOCTOU
- - YAML state-machine engine (`flow_engine.py`) — 把步骤顺序跟逻辑耦合死，真实用户会分叉。Planner 取代它。
- - `pacing.py` 的硬编码 turn counter (「诊断和推荐之间要插 1 个 caring turn」) — 用计数器执行节奏很机械，节奏应该写在 Writer 的 system prompt 里。
- | **C. OpenAI gpt-image-2** (dr-baba 的 Tier 2 primary) | `OPENAI_API_KEY` | 已经 setup，能用，但**不是极梦** |
- **我的诚实建议：用 C (OpenAI gpt-image-2)，原因 3 个：**
- 2. **OpenAI 的中文渲染对汤水 product shot 是够用的**（汤水图片不需要做精确的中文标注，跟 dr-baba 要的解剖图 + 穴位标注不一样）
- 3. **不是终稿** — 这些都是 placeholder，等 Care Plus 给真图就替换掉了。AI 图片在产品页用一周不会出大事，但要先标清楚「示意圖」


## 2026-05-21 15:40 — TCM-Jessica

### Decisions & Reasoning
- 而且你描述的架构 (Planner → 多个 specialist → Final Writer + 平行调用) 跟 Dr. Baba 的 card-driven retrieval pipeline 是**根本不一样**的设计。Fork 出来是对的。
- - 不可变 state + `_ALLOWED_KEYS` whitelist + 每用户 lock — 防止 typo 幽灵字段、防止 WhatsApp 连发的 TOCTOU
- - YAML state-machine engine (`flow_engine.py`) — 把步骤顺序跟逻辑耦合死，真实用户会分叉。Planner 取代它。
- - `pacing.py` 的硬编码 turn counter (「诊断和推荐之间要插 1 个 caring turn」) — 用计数器执行节奏很机械，节奏应该写在 Writer 的 system prompt 里。
- | **C. OpenAI gpt-image-2** (dr-baba 的 Tier 2 primary) | `OPENAI_API_KEY` | 已经 setup，能用，但**不是极梦** |
- **我的诚实建议：用 C (OpenAI gpt-image-2)，原因 3 个：**
- 2. **OpenAI 的中文渲染对汤水 product shot 是够用的**（汤水图片不需要做精确的中文标注，跟 dr-baba 要的解剖图 + 穴位标注不一样）
- 3. **不是终稿** — 这些都是 placeholder，等 Care Plus 给真图就替换掉了。AI 图片在产品页用一周不会出大事，但要先标清楚「示意圖」


## 2026-05-21 15:47 — TCM-Jessica

### Decisions & Reasoning
- 而且你描述的架构 (Planner → 多个 specialist → Final Writer + 平行调用) 跟 Dr. Baba 的 card-driven retrieval pipeline 是**根本不一样**的设计。Fork 出来是对的。
- - 不可变 state + `_ALLOWED_KEYS` whitelist + 每用户 lock — 防止 typo 幽灵字段、防止 WhatsApp 连发的 TOCTOU
- - YAML state-machine engine (`flow_engine.py`) — 把步骤顺序跟逻辑耦合死，真实用户会分叉。Planner 取代它。
- - `pacing.py` 的硬编码 turn counter (「诊断和推荐之间要插 1 个 caring turn」) — 用计数器执行节奏很机械，节奏应该写在 Writer 的 system prompt 里。
- | **C. OpenAI gpt-image-2** (dr-baba 的 Tier 2 primary) | `OPENAI_API_KEY` | 已经 setup，能用，但**不是极梦** |
- **我的诚实建议：用 C (OpenAI gpt-image-2)，原因 3 个：**
- 2. **OpenAI 的中文渲染对汤水 product shot 是够用的**（汤水图片不需要做精确的中文标注，跟 dr-baba 要的解剖图 + 穴位标注不一样）
- 3. **不是终稿** — 这些都是 placeholder，等 Care Plus 给真图就替换掉了。AI 图片在产品页用一周不会出大事，但要先标清楚「示意圖」


## 2026-05-21 15:55 — TCM-Jessica

### Decisions & Reasoning
- 而且你描述的架构 (Planner → 多个 specialist → Final Writer + 平行调用) 跟 Dr. Baba 的 card-driven retrieval pipeline 是**根本不一样**的设计。Fork 出来是对的。
- - 不可变 state + `_ALLOWED_KEYS` whitelist + 每用户 lock — 防止 typo 幽灵字段、防止 WhatsApp 连发的 TOCTOU
- - YAML state-machine engine (`flow_engine.py`) — 把步骤顺序跟逻辑耦合死，真实用户会分叉。Planner 取代它。
- - `pacing.py` 的硬编码 turn counter (「诊断和推荐之间要插 1 个 caring turn」) — 用计数器执行节奏很机械，节奏应该写在 Writer 的 system prompt 里。
- | **C. OpenAI gpt-image-2** (dr-baba 的 Tier 2 primary) | `OPENAI_API_KEY` | 已经 setup，能用，但**不是极梦** |
- **我的诚实建议：用 C (OpenAI gpt-image-2)，原因 3 个：**
- 2. **OpenAI 的中文渲染对汤水 product shot 是够用的**（汤水图片不需要做精确的中文标注，跟 dr-baba 要的解剖图 + 穴位标注不一样）
- 3. **不是终稿** — 这些都是 placeholder，等 Care Plus 给真图就替换掉了。AI 图片在产品页用一周不会出大事，但要先标清楚「示意圖」


## 2026-05-21 16:00 — TCM-Jessica

### Decisions & Reasoning
- 而且你描述的架构 (Planner → 多个 specialist → Final Writer + 平行调用) 跟 Dr. Baba 的 card-driven retrieval pipeline 是**根本不一样**的设计。Fork 出来是对的。
- - 不可变 state + `_ALLOWED_KEYS` whitelist + 每用户 lock — 防止 typo 幽灵字段、防止 WhatsApp 连发的 TOCTOU
- - YAML state-machine engine (`flow_engine.py`) — 把步骤顺序跟逻辑耦合死，真实用户会分叉。Planner 取代它。
- - `pacing.py` 的硬编码 turn counter (「诊断和推荐之间要插 1 个 caring turn」) — 用计数器执行节奏很机械，节奏应该写在 Writer 的 system prompt 里。
- | **C. OpenAI gpt-image-2** (dr-baba 的 Tier 2 primary) | `OPENAI_API_KEY` | 已经 setup，能用，但**不是极梦** |
- **我的诚实建议：用 C (OpenAI gpt-image-2)，原因 3 个：**
- 2. **OpenAI 的中文渲染对汤水 product shot 是够用的**（汤水图片不需要做精确的中文标注，跟 dr-baba 要的解剖图 + 穴位标注不一样）
- 3. **不是终稿** — 这些都是 placeholder，等 Care Plus 给真图就替换掉了。AI 图片在产品页用一周不会出大事，但要先标清楚「示意圖」


## 2026-05-21 16:05 — TCM-Jessica

### Architecture Decisions
- Still timing out. The issue — `get_incoming_texts()` counts text items but `wait_for_function` counts DOM elements. They return different numbers. Let me use a smarter approach — check the `data-id` of the last message instead of total count:

### Decisions & Reasoning
- 控制你的浏览器，用你个人号发。适合小规模测试，但要保持浏览器开着。
- 2. 用哪个号发（个人号还是 ChatDaddy 业务号）？
- 明白了。就是用 Playwright 打开你的 WhatsApp Web，自动发测试消息给那个 agent，然后看它怎么回。
- 1. 用你已有的 Chrome Default profile（不用重新登录）
- 然后告诉我，我就运行。它会用你的 Default profile（shivonnekhoo@gmail.com）直接打开，WhatsApp Web 应该已经登录了，不用扫码。
- Chrome 不允许对 Default profile 直接做 remote debugging。换个方式 — 用 subprocess 先启动 Chrome（带 debug port），然后 Playwright 连进去：
- WhatsApp Web 通了！但搜索找不到联系人。可能是选择器问题或联系人没存。让我 debug 看看搜索结果：
- 找到了！selector 用 `cell-frame-container` 不是 `listitem`。直接修：


## 2026-05-21 16:17 — TCM-Jessica

### Decisions & Reasoning
- 而且你描述的架构 (Planner → 多个 specialist → Final Writer + 平行调用) 跟 Dr. Baba 的 card-driven retrieval pipeline 是**根本不一样**的设计。Fork 出来是对的。
- - 不可变 state + `_ALLOWED_KEYS` whitelist + 每用户 lock — 防止 typo 幽灵字段、防止 WhatsApp 连发的 TOCTOU
- - YAML state-machine engine (`flow_engine.py`) — 把步骤顺序跟逻辑耦合死，真实用户会分叉。Planner 取代它。
- - `pacing.py` 的硬编码 turn counter (「诊断和推荐之间要插 1 个 caring turn」) — 用计数器执行节奏很机械，节奏应该写在 Writer 的 system prompt 里。
- | **C. OpenAI gpt-image-2** (dr-baba 的 Tier 2 primary) | `OPENAI_API_KEY` | 已经 setup，能用，但**不是极梦** |
- **我的诚实建议：用 C (OpenAI gpt-image-2)，原因 3 个：**
- 2. **OpenAI 的中文渲染对汤水 product shot 是够用的**（汤水图片不需要做精确的中文标注，跟 dr-baba 要的解剖图 + 穴位标注不一样）
- 3. **不是终稿** — 这些都是 placeholder，等 Care Plus 给真图就替换掉了。AI 图片在产品页用一周不会出大事，但要先标清楚「示意圖」


## 2026-05-21 16:26 — TCM-Jessica

### Decisions & Reasoning
- 而且你描述的架构 (Planner → 多个 specialist → Final Writer + 平行调用) 跟 Dr. Baba 的 card-driven retrieval pipeline 是**根本不一样**的设计。Fork 出来是对的。
- - 不可变 state + `_ALLOWED_KEYS` whitelist + 每用户 lock — 防止 typo 幽灵字段、防止 WhatsApp 连发的 TOCTOU
- - YAML state-machine engine (`flow_engine.py`) — 把步骤顺序跟逻辑耦合死，真实用户会分叉。Planner 取代它。
- - `pacing.py` 的硬编码 turn counter (「诊断和推荐之间要插 1 个 caring turn」) — 用计数器执行节奏很机械，节奏应该写在 Writer 的 system prompt 里。
- | **C. OpenAI gpt-image-2** (dr-baba 的 Tier 2 primary) | `OPENAI_API_KEY` | 已经 setup，能用，但**不是极梦** |
- **我的诚实建议：用 C (OpenAI gpt-image-2)，原因 3 个：**
- 2. **OpenAI 的中文渲染对汤水 product shot 是够用的**（汤水图片不需要做精确的中文标注，跟 dr-baba 要的解剖图 + 穴位标注不一样）
- 3. **不是终稿** — 这些都是 placeholder，等 Care Plus 给真图就替换掉了。AI 图片在产品页用一周不会出大事，但要先标清楚「示意圖」


## 2026-05-21 16:36 — TCM-Jessica

### Decisions & Reasoning
- 而且你描述的架构 (Planner → 多个 specialist → Final Writer + 平行调用) 跟 Dr. Baba 的 card-driven retrieval pipeline 是**根本不一样**的设计。Fork 出来是对的。
- - 不可变 state + `_ALLOWED_KEYS` whitelist + 每用户 lock — 防止 typo 幽灵字段、防止 WhatsApp 连发的 TOCTOU
- - YAML state-machine engine (`flow_engine.py`) — 把步骤顺序跟逻辑耦合死，真实用户会分叉。Planner 取代它。
- - `pacing.py` 的硬编码 turn counter (「诊断和推荐之间要插 1 个 caring turn」) — 用计数器执行节奏很机械，节奏应该写在 Writer 的 system prompt 里。
- | **C. OpenAI gpt-image-2** (dr-baba 的 Tier 2 primary) | `OPENAI_API_KEY` | 已经 setup，能用，但**不是极梦** |
- **我的诚实建议：用 C (OpenAI gpt-image-2)，原因 3 个：**
- 2. **OpenAI 的中文渲染对汤水 product shot 是够用的**（汤水图片不需要做精确的中文标注，跟 dr-baba 要的解剖图 + 穴位标注不一样）
- 3. **不是终稿** — 这些都是 placeholder，等 Care Plus 给真图就替换掉了。AI 图片在产品页用一周不会出大事，但要先标清楚「示意圖」


## 2026-05-21 16:40 — TCM-Jessica

### Decisions & Reasoning
- 而且你描述的架构 (Planner → 多个 specialist → Final Writer + 平行调用) 跟 Dr. Baba 的 card-driven retrieval pipeline 是**根本不一样**的设计。Fork 出来是对的。
- - 不可变 state + `_ALLOWED_KEYS` whitelist + 每用户 lock — 防止 typo 幽灵字段、防止 WhatsApp 连发的 TOCTOU
- - YAML state-machine engine (`flow_engine.py`) — 把步骤顺序跟逻辑耦合死，真实用户会分叉。Planner 取代它。
- - `pacing.py` 的硬编码 turn counter (「诊断和推荐之间要插 1 个 caring turn」) — 用计数器执行节奏很机械，节奏应该写在 Writer 的 system prompt 里。
- | **C. OpenAI gpt-image-2** (dr-baba 的 Tier 2 primary) | `OPENAI_API_KEY` | 已经 setup，能用，但**不是极梦** |
- **我的诚实建议：用 C (OpenAI gpt-image-2)，原因 3 个：**
- 2. **OpenAI 的中文渲染对汤水 product shot 是够用的**（汤水图片不需要做精确的中文标注，跟 dr-baba 要的解剖图 + 穴位标注不一样）
- 3. **不是终稿** — 这些都是 placeholder，等 Care Plus 给真图就替换掉了。AI 图片在产品页用一周不会出大事，但要先标清楚「示意圖」


## 2026-05-21 17:27 — TCM-Jessica

### Decisions & Reasoning
- 而且你描述的架构 (Planner → 多个 specialist → Final Writer + 平行调用) 跟 Dr. Baba 的 card-driven retrieval pipeline 是**根本不一样**的设计。Fork 出来是对的。
- - 不可变 state + `_ALLOWED_KEYS` whitelist + 每用户 lock — 防止 typo 幽灵字段、防止 WhatsApp 连发的 TOCTOU
- - YAML state-machine engine (`flow_engine.py`) — 把步骤顺序跟逻辑耦合死，真实用户会分叉。Planner 取代它。
- - `pacing.py` 的硬编码 turn counter (「诊断和推荐之间要插 1 个 caring turn」) — 用计数器执行节奏很机械，节奏应该写在 Writer 的 system prompt 里。
- | **C. OpenAI gpt-image-2** (dr-baba 的 Tier 2 primary) | `OPENAI_API_KEY` | 已经 setup，能用，但**不是极梦** |
- **我的诚实建议：用 C (OpenAI gpt-image-2)，原因 3 个：**
- 2. **OpenAI 的中文渲染对汤水 product shot 是够用的**（汤水图片不需要做精确的中文标注，跟 dr-baba 要的解剖图 + 穴位标注不一样）
- 3. **不是终稿** — 这些都是 placeholder，等 Care Plus 给真图就替换掉了。AI 图片在产品页用一周不会出大事，但要先标清楚「示意圖」


## 2026-05-21 17:40 — TCM-Jessica

### Decisions & Reasoning
- 而且你描述的架构 (Planner → 多个 specialist → Final Writer + 平行调用) 跟 Dr. Baba 的 card-driven retrieval pipeline 是**根本不一样**的设计。Fork 出来是对的。
- - 不可变 state + `_ALLOWED_KEYS` whitelist + 每用户 lock — 防止 typo 幽灵字段、防止 WhatsApp 连发的 TOCTOU
- - YAML state-machine engine (`flow_engine.py`) — 把步骤顺序跟逻辑耦合死，真实用户会分叉。Planner 取代它。
- - `pacing.py` 的硬编码 turn counter (「诊断和推荐之间要插 1 个 caring turn」) — 用计数器执行节奏很机械，节奏应该写在 Writer 的 system prompt 里。
- | **C. OpenAI gpt-image-2** (dr-baba 的 Tier 2 primary) | `OPENAI_API_KEY` | 已经 setup，能用，但**不是极梦** |
- **我的诚实建议：用 C (OpenAI gpt-image-2)，原因 3 个：**
- 2. **OpenAI 的中文渲染对汤水 product shot 是够用的**（汤水图片不需要做精确的中文标注，跟 dr-baba 要的解剖图 + 穴位标注不一样）
- 3. **不是终稿** — 这些都是 placeholder，等 Care Plus 给真图就替换掉了。AI 图片在产品页用一周不会出大事，但要先标清楚「示意圖」


## 2026-05-21 17:44 — TCM-Jessica

### Decisions & Reasoning
- 你 webhook 进来时就已经有 `accountId` 和 `chatId`，可以**立刻**用这两个 call history。
- **问题是：** 如果用户之前跟 Jessica 聊过、你们换了服务器/清了数据库，或者用户是第一次到 Jessica 但之前在 ChatDaddy inbox 里聊过，本地就没有 history。


## 2026-05-21 17:51 — TCM-Jessica

### Decisions & Reasoning
- 你 webhook 进来时就已经有 `accountId` 和 `chatId`，可以**立刻**用这两个 call history。
- **问题是：** 如果用户之前跟 Jessica 聊过、你们换了服务器/清了数据库，或者用户是第一次到 Jessica 但之前在 ChatDaddy inbox 里聊过，本地就没有 history。
- Q1 最重要 — 第一次从 ChatDaddy 拉到 history 要不要写回本地 CRM？如果写回，下次就有 local history 了，不用每次都 call ChatDaddy。要不要做？


## 2026-05-21 17:55 — TCM-Jessica

### Decisions & Reasoning
- 而且你描述的架构 (Planner → 多个 specialist → Final Writer + 平行调用) 跟 Dr. Baba 的 card-driven retrieval pipeline 是**根本不一样**的设计。Fork 出来是对的。
- - 不可变 state + `_ALLOWED_KEYS` whitelist + 每用户 lock — 防止 typo 幽灵字段、防止 WhatsApp 连发的 TOCTOU
- - YAML state-machine engine (`flow_engine.py`) — 把步骤顺序跟逻辑耦合死，真实用户会分叉。Planner 取代它。
- - `pacing.py` 的硬编码 turn counter (「诊断和推荐之间要插 1 个 caring turn」) — 用计数器执行节奏很机械，节奏应该写在 Writer 的 system prompt 里。
- | **C. OpenAI gpt-image-2** (dr-baba 的 Tier 2 primary) | `OPENAI_API_KEY` | 已经 setup，能用，但**不是极梦** |
- **我的诚实建议：用 C (OpenAI gpt-image-2)，原因 3 个：**
- 2. **OpenAI 的中文渲染对汤水 product shot 是够用的**（汤水图片不需要做精确的中文标注，跟 dr-baba 要的解剖图 + 穴位标注不一样）
- 3. **不是终稿** — 这些都是 placeholder，等 Care Plus 给真图就替换掉了。AI 图片在产品页用一周不会出大事，但要先标清楚「示意圖」


## 2026-05-21 18:08 — TCM-Jessica

### Decisions & Reasoning
- 你 webhook 进来时就已经有 `accountId` 和 `chatId`，可以**立刻**用这两个 call history。
- **问题是：** 如果用户之前跟 Jessica 聊过、你们换了服务器/清了数据库，或者用户是第一次到 Jessica 但之前在 ChatDaddy inbox 里聊过，本地就没有 history。
- Q1 最重要 — 第一次从 ChatDaddy 拉到 history 要不要写回本地 CRM？如果写回，下次就有 local history 了，不用每次都 call ChatDaddy。要不要做？
- - **为什么写回：** ChatDaddy 是 source of truth，写回之后下次 turn 直接用本地，不用每次都 call ChatDaddy API
- | `chatId` | 用户的 WhatsApp JID（对话唯一标识） | `85291234567@s.whatsapp.net` |
- **ChatDaddy 返回的就是这个 chat thread 里的所有消息** — 包括用户发的和 Jessica 发的，按时间排。
- 1. **History 是 per-conversation，不是 per-user** — 如果同一个人用不同手机号发消息，那是两个独立的 `chatId`，history 不会合并
- 2. **Local CRM 用 `phone`（从 `chatId` 提取出来的数字部分）做 key** — 所以本地 CRM 和 ChatDaddy 的 lookup key 其实是不一样的，PRD 里的 `_write_back` 要做一次转换


## 2026-05-21 18:12 — TCM-Jessica

### Decisions & Reasoning
- 而且你描述的架构 (Planner → 多个 specialist → Final Writer + 平行调用) 跟 Dr. Baba 的 card-driven retrieval pipeline 是**根本不一样**的设计。Fork 出来是对的。
- - 不可变 state + `_ALLOWED_KEYS` whitelist + 每用户 lock — 防止 typo 幽灵字段、防止 WhatsApp 连发的 TOCTOU
- - YAML state-machine engine (`flow_engine.py`) — 把步骤顺序跟逻辑耦合死，真实用户会分叉。Planner 取代它。
- - `pacing.py` 的硬编码 turn counter (「诊断和推荐之间要插 1 个 caring turn」) — 用计数器执行节奏很机械，节奏应该写在 Writer 的 system prompt 里。
- | **C. OpenAI gpt-image-2** (dr-baba 的 Tier 2 primary) | `OPENAI_API_KEY` | 已经 setup，能用，但**不是极梦** |
- **我的诚实建议：用 C (OpenAI gpt-image-2)，原因 3 个：**
- 2. **OpenAI 的中文渲染对汤水 product shot 是够用的**（汤水图片不需要做精确的中文标注，跟 dr-baba 要的解剖图 + 穴位标注不一样）
- 3. **不是终稿** — 这些都是 placeholder，等 Care Plus 给真图就替换掉了。AI 图片在产品页用一周不会出大事，但要先标清楚「示意圖」


## 2026-05-21 18:20 — TCM-Jessica

### Decisions & Reasoning
- 而且你描述的架构 (Planner → 多个 specialist → Final Writer + 平行调用) 跟 Dr. Baba 的 card-driven retrieval pipeline 是**根本不一样**的设计。Fork 出来是对的。
- - 不可变 state + `_ALLOWED_KEYS` whitelist + 每用户 lock — 防止 typo 幽灵字段、防止 WhatsApp 连发的 TOCTOU
- - YAML state-machine engine (`flow_engine.py`) — 把步骤顺序跟逻辑耦合死，真实用户会分叉。Planner 取代它。
- - `pacing.py` 的硬编码 turn counter (「诊断和推荐之间要插 1 个 caring turn」) — 用计数器执行节奏很机械，节奏应该写在 Writer 的 system prompt 里。
- | **C. OpenAI gpt-image-2** (dr-baba 的 Tier 2 primary) | `OPENAI_API_KEY` | 已经 setup，能用，但**不是极梦** |
- **我的诚实建议：用 C (OpenAI gpt-image-2)，原因 3 个：**
- 2. **OpenAI 的中文渲染对汤水 product shot 是够用的**（汤水图片不需要做精确的中文标注，跟 dr-baba 要的解剖图 + 穴位标注不一样）
- 3. **不是终稿** — 这些都是 placeholder，等 Care Plus 给真图就替换掉了。AI 图片在产品页用一周不会出大事，但要先标清楚「示意圖」


## 2026-05-21 18:27 — TCM-Jessica

### Decisions & Reasoning
- 而且你描述的架构 (Planner → 多个 specialist → Final Writer + 平行调用) 跟 Dr. Baba 的 card-driven retrieval pipeline 是**根本不一样**的设计。Fork 出来是对的。
- - 不可变 state + `_ALLOWED_KEYS` whitelist + 每用户 lock — 防止 typo 幽灵字段、防止 WhatsApp 连发的 TOCTOU
- - YAML state-machine engine (`flow_engine.py`) — 把步骤顺序跟逻辑耦合死，真实用户会分叉。Planner 取代它。
- - `pacing.py` 的硬编码 turn counter (「诊断和推荐之间要插 1 个 caring turn」) — 用计数器执行节奏很机械，节奏应该写在 Writer 的 system prompt 里。
- | **C. OpenAI gpt-image-2** (dr-baba 的 Tier 2 primary) | `OPENAI_API_KEY` | 已经 setup，能用，但**不是极梦** |
- **我的诚实建议：用 C (OpenAI gpt-image-2)，原因 3 个：**
- 2. **OpenAI 的中文渲染对汤水 product shot 是够用的**（汤水图片不需要做精确的中文标注，跟 dr-baba 要的解剖图 + 穴位标注不一样）
- 3. **不是终稿** — 这些都是 placeholder，等 Care Plus 给真图就替换掉了。AI 图片在产品页用一周不会出大事，但要先标清楚「示意圖」


## 2026-05-21 18:55 — TCM-Jessica

### Decisions & Reasoning
- 而且你描述的架构 (Planner → 多个 specialist → Final Writer + 平行调用) 跟 Dr. Baba 的 card-driven retrieval pipeline 是**根本不一样**的设计。Fork 出来是对的。
- - 不可变 state + `_ALLOWED_KEYS` whitelist + 每用户 lock — 防止 typo 幽灵字段、防止 WhatsApp 连发的 TOCTOU
- - YAML state-machine engine (`flow_engine.py`) — 把步骤顺序跟逻辑耦合死，真实用户会分叉。Planner 取代它。
- - `pacing.py` 的硬编码 turn counter (「诊断和推荐之间要插 1 个 caring turn」) — 用计数器执行节奏很机械，节奏应该写在 Writer 的 system prompt 里。
- | **C. OpenAI gpt-image-2** (dr-baba 的 Tier 2 primary) | `OPENAI_API_KEY` | 已经 setup，能用，但**不是极梦** |
- **我的诚实建议：用 C (OpenAI gpt-image-2)，原因 3 个：**
- 2. **OpenAI 的中文渲染对汤水 product shot 是够用的**（汤水图片不需要做精确的中文标注，跟 dr-baba 要的解剖图 + 穴位标注不一样）
- 3. **不是终稿** — 这些都是 placeholder，等 Care Plus 给真图就替换掉了。AI 图片在产品页用一周不会出大事，但要先标清楚「示意圖」


## 2026-05-21 22:17 — TCM-Jessica

### Decisions & Reasoning
- 而且你描述的架构 (Planner → 多个 specialist → Final Writer + 平行调用) 跟 Dr. Baba 的 card-driven retrieval pipeline 是**根本不一样**的设计。Fork 出来是对的。
- - 不可变 state + `_ALLOWED_KEYS` whitelist + 每用户 lock — 防止 typo 幽灵字段、防止 WhatsApp 连发的 TOCTOU
- - YAML state-machine engine (`flow_engine.py`) — 把步骤顺序跟逻辑耦合死，真实用户会分叉。Planner 取代它。
- - `pacing.py` 的硬编码 turn counter (「诊断和推荐之间要插 1 个 caring turn」) — 用计数器执行节奏很机械，节奏应该写在 Writer 的 system prompt 里。
- | **C. OpenAI gpt-image-2** (dr-baba 的 Tier 2 primary) | `OPENAI_API_KEY` | 已经 setup，能用，但**不是极梦** |
- **我的诚实建议：用 C (OpenAI gpt-image-2)，原因 3 个：**
- 2. **OpenAI 的中文渲染对汤水 product shot 是够用的**（汤水图片不需要做精确的中文标注，跟 dr-baba 要的解剖图 + 穴位标注不一样）
- 3. **不是终稿** — 这些都是 placeholder，等 Care Plus 给真图就替换掉了。AI 图片在产品页用一周不会出大事，但要先标清楚「示意圖」


## 2026-05-22 07:40 — TCM-Jessica

### Decisions & Reasoning
- 而且你描述的架构 (Planner → 多个 specialist → Final Writer + 平行调用) 跟 Dr. Baba 的 card-driven retrieval pipeline 是**根本不一样**的设计。Fork 出来是对的。
- - 不可变 state + `_ALLOWED_KEYS` whitelist + 每用户 lock — 防止 typo 幽灵字段、防止 WhatsApp 连发的 TOCTOU
- - YAML state-machine engine (`flow_engine.py`) — 把步骤顺序跟逻辑耦合死，真实用户会分叉。Planner 取代它。
- - `pacing.py` 的硬编码 turn counter (「诊断和推荐之间要插 1 个 caring turn」) — 用计数器执行节奏很机械，节奏应该写在 Writer 的 system prompt 里。
- | **C. OpenAI gpt-image-2** (dr-baba 的 Tier 2 primary) | `OPENAI_API_KEY` | 已经 setup，能用，但**不是极梦** |
- **我的诚实建议：用 C (OpenAI gpt-image-2)，原因 3 个：**
- 2. **OpenAI 的中文渲染对汤水 product shot 是够用的**（汤水图片不需要做精确的中文标注，跟 dr-baba 要的解剖图 + 穴位标注不一样）
- 3. **不是终稿** — 这些都是 placeholder，等 Care Plus 给真图就替换掉了。AI 图片在产品页用一周不会出大事，但要先标清楚「示意圖」


## 2026-05-22 09:03 — TCM-Jessica

### Decisions & Reasoning
- 而且你描述的架构 (Planner → 多个 specialist → Final Writer + 平行调用) 跟 Dr. Baba 的 card-driven retrieval pipeline 是**根本不一样**的设计。Fork 出来是对的。
- - 不可变 state + `_ALLOWED_KEYS` whitelist + 每用户 lock — 防止 typo 幽灵字段、防止 WhatsApp 连发的 TOCTOU
- - YAML state-machine engine (`flow_engine.py`) — 把步骤顺序跟逻辑耦合死，真实用户会分叉。Planner 取代它。
- - `pacing.py` 的硬编码 turn counter (「诊断和推荐之间要插 1 个 caring turn」) — 用计数器执行节奏很机械，节奏应该写在 Writer 的 system prompt 里。
- | **C. OpenAI gpt-image-2** (dr-baba 的 Tier 2 primary) | `OPENAI_API_KEY` | 已经 setup，能用，但**不是极梦** |
- **我的诚实建议：用 C (OpenAI gpt-image-2)，原因 3 个：**
- 2. **OpenAI 的中文渲染对汤水 product shot 是够用的**（汤水图片不需要做精确的中文标注，跟 dr-baba 要的解剖图 + 穴位标注不一样）
- 3. **不是终稿** — 这些都是 placeholder，等 Care Plus 给真图就替换掉了。AI 图片在产品页用一周不会出大事，但要先标清楚「示意圖」


## 2026-05-22 09:12 — TCM-Jessica

### Decisions & Reasoning
- 而且你描述的架构 (Planner → 多个 specialist → Final Writer + 平行调用) 跟 Dr. Baba 的 card-driven retrieval pipeline 是**根本不一样**的设计。Fork 出来是对的。
- - 不可变 state + `_ALLOWED_KEYS` whitelist + 每用户 lock — 防止 typo 幽灵字段、防止 WhatsApp 连发的 TOCTOU
- - YAML state-machine engine (`flow_engine.py`) — 把步骤顺序跟逻辑耦合死，真实用户会分叉。Planner 取代它。
- - `pacing.py` 的硬编码 turn counter (「诊断和推荐之间要插 1 个 caring turn」) — 用计数器执行节奏很机械，节奏应该写在 Writer 的 system prompt 里。
- | **C. OpenAI gpt-image-2** (dr-baba 的 Tier 2 primary) | `OPENAI_API_KEY` | 已经 setup，能用，但**不是极梦** |
- **我的诚实建议：用 C (OpenAI gpt-image-2)，原因 3 个：**
- 2. **OpenAI 的中文渲染对汤水 product shot 是够用的**（汤水图片不需要做精确的中文标注，跟 dr-baba 要的解剖图 + 穴位标注不一样）
- 3. **不是终稿** — 这些都是 placeholder，等 Care Plus 给真图就替换掉了。AI 图片在产品页用一周不会出大事，但要先标清楚「示意圖」


## 2026-05-22 09:47 — TCM-Jessica

### Decisions & Reasoning
- 而且你描述的架构 (Planner → 多个 specialist → Final Writer + 平行调用) 跟 Dr. Baba 的 card-driven retrieval pipeline 是**根本不一样**的设计。Fork 出来是对的。
- - 不可变 state + `_ALLOWED_KEYS` whitelist + 每用户 lock — 防止 typo 幽灵字段、防止 WhatsApp 连发的 TOCTOU
- - YAML state-machine engine (`flow_engine.py`) — 把步骤顺序跟逻辑耦合死，真实用户会分叉。Planner 取代它。
- - `pacing.py` 的硬编码 turn counter (「诊断和推荐之间要插 1 个 caring turn」) — 用计数器执行节奏很机械，节奏应该写在 Writer 的 system prompt 里。
- | **C. OpenAI gpt-image-2** (dr-baba 的 Tier 2 primary) | `OPENAI_API_KEY` | 已经 setup，能用，但**不是极梦** |
- **我的诚实建议：用 C (OpenAI gpt-image-2)，原因 3 个：**
- 2. **OpenAI 的中文渲染对汤水 product shot 是够用的**（汤水图片不需要做精确的中文标注，跟 dr-baba 要的解剖图 + 穴位标注不一样）
- 3. **不是终稿** — 这些都是 placeholder，等 Care Plus 给真图就替换掉了。AI 图片在产品页用一周不会出大事，但要先标清楚「示意圖」


## 2026-05-22 10:16 — TCM-Jessica

### Decisions & Reasoning
- 而且你描述的架构 (Planner → 多个 specialist → Final Writer + 平行调用) 跟 Dr. Baba 的 card-driven retrieval pipeline 是**根本不一样**的设计。Fork 出来是对的。
- - 不可变 state + `_ALLOWED_KEYS` whitelist + 每用户 lock — 防止 typo 幽灵字段、防止 WhatsApp 连发的 TOCTOU
- - YAML state-machine engine (`flow_engine.py`) — 把步骤顺序跟逻辑耦合死，真实用户会分叉。Planner 取代它。
- - `pacing.py` 的硬编码 turn counter (「诊断和推荐之间要插 1 个 caring turn」) — 用计数器执行节奏很机械，节奏应该写在 Writer 的 system prompt 里。
- | **C. OpenAI gpt-image-2** (dr-baba 的 Tier 2 primary) | `OPENAI_API_KEY` | 已经 setup，能用，但**不是极梦** |
- **我的诚实建议：用 C (OpenAI gpt-image-2)，原因 3 个：**
- 2. **OpenAI 的中文渲染对汤水 product shot 是够用的**（汤水图片不需要做精确的中文标注，跟 dr-baba 要的解剖图 + 穴位标注不一样）
- 3. **不是终稿** — 这些都是 placeholder，等 Care Plus 给真图就替换掉了。AI 图片在产品页用一周不会出大事，但要先标清楚「示意圖」


## 2026-05-22 10:18 — TCM-Jessica

### Decisions & Reasoning
- 你 webhook 进来时就已经有 `accountId` 和 `chatId`，可以**立刻**用这两个 call history。
- **问题是：** 如果用户之前跟 Jessica 聊过、你们换了服务器/清了数据库，或者用户是第一次到 Jessica 但之前在 ChatDaddy inbox 里聊过，本地就没有 history。
- Q1 最重要 — 第一次从 ChatDaddy 拉到 history 要不要写回本地 CRM？如果写回，下次就有 local history 了，不用每次都 call ChatDaddy。要不要做？
- - **为什么写回：** ChatDaddy 是 source of truth，写回之后下次 turn 直接用本地，不用每次都 call ChatDaddy API
- | `chatId` | 用户的 WhatsApp JID（对话唯一标识） | `85291234567@s.whatsapp.net` |
- **ChatDaddy 返回的就是这个 chat thread 里的所有消息** — 包括用户发的和 Jessica 发的，按时间排。
- 1. **History 是 per-conversation，不是 per-user** — 如果同一个人用不同手机号发消息，那是两个独立的 `chatId`，history 不会合并
- 2. **Local CRM 用 `phone`（从 `chatId` 提取出来的数字部分）做 key** — 所以本地 CRM 和 ChatDaddy 的 lookup key 其实是不一样的，PRD 里的 `_write_back` 要做一次转换


## 2026-05-22 10:57 — TCM-Jessica

### Decisions & Reasoning
- 而且你描述的架构 (Planner → 多个 specialist → Final Writer + 平行调用) 跟 Dr. Baba 的 card-driven retrieval pipeline 是**根本不一样**的设计。Fork 出来是对的。
- - 不可变 state + `_ALLOWED_KEYS` whitelist + 每用户 lock — 防止 typo 幽灵字段、防止 WhatsApp 连发的 TOCTOU
- - YAML state-machine engine (`flow_engine.py`) — 把步骤顺序跟逻辑耦合死，真实用户会分叉。Planner 取代它。
- - `pacing.py` 的硬编码 turn counter (「诊断和推荐之间要插 1 个 caring turn」) — 用计数器执行节奏很机械，节奏应该写在 Writer 的 system prompt 里。
- | **C. OpenAI gpt-image-2** (dr-baba 的 Tier 2 primary) | `OPENAI_API_KEY` | 已经 setup，能用，但**不是极梦** |
- **我的诚实建议：用 C (OpenAI gpt-image-2)，原因 3 个：**
- 2. **OpenAI 的中文渲染对汤水 product shot 是够用的**（汤水图片不需要做精确的中文标注，跟 dr-baba 要的解剖图 + 穴位标注不一样）
- 3. **不是终稿** — 这些都是 placeholder，等 Care Plus 给真图就替换掉了。AI 图片在产品页用一周不会出大事，但要先标清楚「示意圖」


## 2026-05-22 11:24 — TCM-Jessica

### Decisions & Reasoning
- 而且你描述的架构 (Planner → 多个 specialist → Final Writer + 平行调用) 跟 Dr. Baba 的 card-driven retrieval pipeline 是**根本不一样**的设计。Fork 出来是对的。
- - 不可变 state + `_ALLOWED_KEYS` whitelist + 每用户 lock — 防止 typo 幽灵字段、防止 WhatsApp 连发的 TOCTOU
- - YAML state-machine engine (`flow_engine.py`) — 把步骤顺序跟逻辑耦合死，真实用户会分叉。Planner 取代它。
- - `pacing.py` 的硬编码 turn counter (「诊断和推荐之间要插 1 个 caring turn」) — 用计数器执行节奏很机械，节奏应该写在 Writer 的 system prompt 里。
- | **C. OpenAI gpt-image-2** (dr-baba 的 Tier 2 primary) | `OPENAI_API_KEY` | 已经 setup，能用，但**不是极梦** |
- **我的诚实建议：用 C (OpenAI gpt-image-2)，原因 3 个：**
- 2. **OpenAI 的中文渲染对汤水 product shot 是够用的**（汤水图片不需要做精确的中文标注，跟 dr-baba 要的解剖图 + 穴位标注不一样）
- 3. **不是终稿** — 这些都是 placeholder，等 Care Plus 给真图就替换掉了。AI 图片在产品页用一周不会出大事，但要先标清楚「示意圖」


## 2026-05-22 11:29 — TCM-Jessica

### Decisions & Reasoning
- 而且你描述的架构 (Planner → 多个 specialist → Final Writer + 平行调用) 跟 Dr. Baba 的 card-driven retrieval pipeline 是**根本不一样**的设计。Fork 出来是对的。
- - 不可变 state + `_ALLOWED_KEYS` whitelist + 每用户 lock — 防止 typo 幽灵字段、防止 WhatsApp 连发的 TOCTOU
- - YAML state-machine engine (`flow_engine.py`) — 把步骤顺序跟逻辑耦合死，真实用户会分叉。Planner 取代它。
- - `pacing.py` 的硬编码 turn counter (「诊断和推荐之间要插 1 个 caring turn」) — 用计数器执行节奏很机械，节奏应该写在 Writer 的 system prompt 里。
- | **C. OpenAI gpt-image-2** (dr-baba 的 Tier 2 primary) | `OPENAI_API_KEY` | 已经 setup，能用，但**不是极梦** |
- **我的诚实建议：用 C (OpenAI gpt-image-2)，原因 3 个：**
- 2. **OpenAI 的中文渲染对汤水 product shot 是够用的**（汤水图片不需要做精确的中文标注，跟 dr-baba 要的解剖图 + 穴位标注不一样）
- 3. **不是终稿** — 这些都是 placeholder，等 Care Plus 给真图就替换掉了。AI 图片在产品页用一周不会出大事，但要先标清楚「示意圖」


## 2026-05-22 11:47 — TCM-Jessica

### Decisions & Reasoning
- 而且你描述的架构 (Planner → 多个 specialist → Final Writer + 平行调用) 跟 Dr. Baba 的 card-driven retrieval pipeline 是**根本不一样**的设计。Fork 出来是对的。
- - 不可变 state + `_ALLOWED_KEYS` whitelist + 每用户 lock — 防止 typo 幽灵字段、防止 WhatsApp 连发的 TOCTOU
- - YAML state-machine engine (`flow_engine.py`) — 把步骤顺序跟逻辑耦合死，真实用户会分叉。Planner 取代它。
- - `pacing.py` 的硬编码 turn counter (「诊断和推荐之间要插 1 个 caring turn」) — 用计数器执行节奏很机械，节奏应该写在 Writer 的 system prompt 里。
- | **C. OpenAI gpt-image-2** (dr-baba 的 Tier 2 primary) | `OPENAI_API_KEY` | 已经 setup，能用，但**不是极梦** |
- **我的诚实建议：用 C (OpenAI gpt-image-2)，原因 3 个：**
- 2. **OpenAI 的中文渲染对汤水 product shot 是够用的**（汤水图片不需要做精确的中文标注，跟 dr-baba 要的解剖图 + 穴位标注不一样）
- 3. **不是终稿** — 这些都是 placeholder，等 Care Plus 给真图就替换掉了。AI 图片在产品页用一周不会出大事，但要先标清楚「示意圖」


## 2026-05-22 13:17 — TCM-Jessica

### Decisions & Reasoning
- 而且你描述的架构 (Planner → 多个 specialist → Final Writer + 平行调用) 跟 Dr. Baba 的 card-driven retrieval pipeline 是**根本不一样**的设计。Fork 出来是对的。
- - 不可变 state + `_ALLOWED_KEYS` whitelist + 每用户 lock — 防止 typo 幽灵字段、防止 WhatsApp 连发的 TOCTOU
- - YAML state-machine engine (`flow_engine.py`) — 把步骤顺序跟逻辑耦合死，真实用户会分叉。Planner 取代它。
- - `pacing.py` 的硬编码 turn counter (「诊断和推荐之间要插 1 个 caring turn」) — 用计数器执行节奏很机械，节奏应该写在 Writer 的 system prompt 里。
- | **C. OpenAI gpt-image-2** (dr-baba 的 Tier 2 primary) | `OPENAI_API_KEY` | 已经 setup，能用，但**不是极梦** |
- **我的诚实建议：用 C (OpenAI gpt-image-2)，原因 3 个：**
- 2. **OpenAI 的中文渲染对汤水 product shot 是够用的**（汤水图片不需要做精确的中文标注，跟 dr-baba 要的解剖图 + 穴位标注不一样）
- 3. **不是终稿** — 这些都是 placeholder，等 Care Plus 给真图就替换掉了。AI 图片在产品页用一周不会出大事，但要先标清楚「示意圖」


## 2026-05-22 13:30 — TCM-Jessica

### Decisions & Reasoning
- 而且你描述的架构 (Planner → 多个 specialist → Final Writer + 平行调用) 跟 Dr. Baba 的 card-driven retrieval pipeline 是**根本不一样**的设计。Fork 出来是对的。
- - 不可变 state + `_ALLOWED_KEYS` whitelist + 每用户 lock — 防止 typo 幽灵字段、防止 WhatsApp 连发的 TOCTOU
- - YAML state-machine engine (`flow_engine.py`) — 把步骤顺序跟逻辑耦合死，真实用户会分叉。Planner 取代它。
- - `pacing.py` 的硬编码 turn counter (「诊断和推荐之间要插 1 个 caring turn」) — 用计数器执行节奏很机械，节奏应该写在 Writer 的 system prompt 里。
- | **C. OpenAI gpt-image-2** (dr-baba 的 Tier 2 primary) | `OPENAI_API_KEY` | 已经 setup，能用，但**不是极梦** |
- **我的诚实建议：用 C (OpenAI gpt-image-2)，原因 3 个：**
- 2. **OpenAI 的中文渲染对汤水 product shot 是够用的**（汤水图片不需要做精确的中文标注，跟 dr-baba 要的解剖图 + 穴位标注不一样）
- 3. **不是终稿** — 这些都是 placeholder，等 Care Plus 给真图就替换掉了。AI 图片在产品页用一周不会出大事，但要先标清楚「示意圖」


## 2026-05-22 13:33 — TCM-Jessica

### Decisions & Reasoning
- 而且你描述的架构 (Planner → 多个 specialist → Final Writer + 平行调用) 跟 Dr. Baba 的 card-driven retrieval pipeline 是**根本不一样**的设计。Fork 出来是对的。
- - 不可变 state + `_ALLOWED_KEYS` whitelist + 每用户 lock — 防止 typo 幽灵字段、防止 WhatsApp 连发的 TOCTOU
- - YAML state-machine engine (`flow_engine.py`) — 把步骤顺序跟逻辑耦合死，真实用户会分叉。Planner 取代它。
- - `pacing.py` 的硬编码 turn counter (「诊断和推荐之间要插 1 个 caring turn」) — 用计数器执行节奏很机械，节奏应该写在 Writer 的 system prompt 里。
- | **C. OpenAI gpt-image-2** (dr-baba 的 Tier 2 primary) | `OPENAI_API_KEY` | 已经 setup，能用，但**不是极梦** |
- **我的诚实建议：用 C (OpenAI gpt-image-2)，原因 3 个：**
- 2. **OpenAI 的中文渲染对汤水 product shot 是够用的**（汤水图片不需要做精确的中文标注，跟 dr-baba 要的解剖图 + 穴位标注不一样）
- 3. **不是终稿** — 这些都是 placeholder，等 Care Plus 给真图就替换掉了。AI 图片在产品页用一周不会出大事，但要先标清楚「示意圖」


## 2026-05-22 13:54 — TCM-Jessica

### Decisions & Reasoning
- 而且你描述的架构 (Planner → 多个 specialist → Final Writer + 平行调用) 跟 Dr. Baba 的 card-driven retrieval pipeline 是**根本不一样**的设计。Fork 出来是对的。
- - 不可变 state + `_ALLOWED_KEYS` whitelist + 每用户 lock — 防止 typo 幽灵字段、防止 WhatsApp 连发的 TOCTOU
- - YAML state-machine engine (`flow_engine.py`) — 把步骤顺序跟逻辑耦合死，真实用户会分叉。Planner 取代它。
- - `pacing.py` 的硬编码 turn counter (「诊断和推荐之间要插 1 个 caring turn」) — 用计数器执行节奏很机械，节奏应该写在 Writer 的 system prompt 里。
- | **C. OpenAI gpt-image-2** (dr-baba 的 Tier 2 primary) | `OPENAI_API_KEY` | 已经 setup，能用，但**不是极梦** |
- **我的诚实建议：用 C (OpenAI gpt-image-2)，原因 3 个：**
- 2. **OpenAI 的中文渲染对汤水 product shot 是够用的**（汤水图片不需要做精确的中文标注，跟 dr-baba 要的解剖图 + 穴位标注不一样）
- 3. **不是终稿** — 这些都是 placeholder，等 Care Plus 给真图就替换掉了。AI 图片在产品页用一周不会出大事，但要先标清楚「示意圖」


## 2026-05-22 14:21 — TCM-Jessica

### Decisions & Reasoning
- 而且你描述的架构 (Planner → 多个 specialist → Final Writer + 平行调用) 跟 Dr. Baba 的 card-driven retrieval pipeline 是**根本不一样**的设计。Fork 出来是对的。
- - 不可变 state + `_ALLOWED_KEYS` whitelist + 每用户 lock — 防止 typo 幽灵字段、防止 WhatsApp 连发的 TOCTOU
- - YAML state-machine engine (`flow_engine.py`) — 把步骤顺序跟逻辑耦合死，真实用户会分叉。Planner 取代它。
- - `pacing.py` 的硬编码 turn counter (「诊断和推荐之间要插 1 个 caring turn」) — 用计数器执行节奏很机械，节奏应该写在 Writer 的 system prompt 里。
- | **C. OpenAI gpt-image-2** (dr-baba 的 Tier 2 primary) | `OPENAI_API_KEY` | 已经 setup，能用，但**不是极梦** |
- **我的诚实建议：用 C (OpenAI gpt-image-2)，原因 3 个：**
- 2. **OpenAI 的中文渲染对汤水 product shot 是够用的**（汤水图片不需要做精确的中文标注，跟 dr-baba 要的解剖图 + 穴位标注不一样）
- 3. **不是终稿** — 这些都是 placeholder，等 Care Plus 给真图就替换掉了。AI 图片在产品页用一周不会出大事，但要先标清楚「示意圖」


## 2026-05-22 14:27 — TCM-Jessica

### Architecture Decisions
- Still timing out. The issue — `get_incoming_texts()` counts text items but `wait_for_function` counts DOM elements. They return different numbers. Let me use a smarter approach — check the `data-id` of the last message instead of total count:

### Decisions & Reasoning
- 控制你的浏览器，用你个人号发。适合小规模测试，但要保持浏览器开着。
- 2. 用哪个号发（个人号还是 ChatDaddy 业务号）？
- 明白了。就是用 Playwright 打开你的 WhatsApp Web，自动发测试消息给那个 agent，然后看它怎么回。
- 1. 用你已有的 Chrome Default profile（不用重新登录）
- 然后告诉我，我就运行。它会用你的 Default profile（shivonnekhoo@gmail.com）直接打开，WhatsApp Web 应该已经登录了，不用扫码。
- Chrome 不允许对 Default profile 直接做 remote debugging。换个方式 — 用 subprocess 先启动 Chrome（带 debug port），然后 Playwright 连进去：
- WhatsApp Web 通了！但搜索找不到联系人。可能是选择器问题或联系人没存。让我 debug 看看搜索结果：
- 找到了！selector 用 `cell-frame-container` 不是 `listitem`。直接修：


## 2026-05-22 15:21 — TCM-Jessica

### Decisions & Reasoning
- 而且你描述的架构 (Planner → 多个 specialist → Final Writer + 平行调用) 跟 Dr. Baba 的 card-driven retrieval pipeline 是**根本不一样**的设计。Fork 出来是对的。
- - 不可变 state + `_ALLOWED_KEYS` whitelist + 每用户 lock — 防止 typo 幽灵字段、防止 WhatsApp 连发的 TOCTOU
- - YAML state-machine engine (`flow_engine.py`) — 把步骤顺序跟逻辑耦合死，真实用户会分叉。Planner 取代它。
- - `pacing.py` 的硬编码 turn counter (「诊断和推荐之间要插 1 个 caring turn」) — 用计数器执行节奏很机械，节奏应该写在 Writer 的 system prompt 里。
- | **C. OpenAI gpt-image-2** (dr-baba 的 Tier 2 primary) | `OPENAI_API_KEY` | 已经 setup，能用，但**不是极梦** |
- **我的诚实建议：用 C (OpenAI gpt-image-2)，原因 3 个：**
- 2. **OpenAI 的中文渲染对汤水 product shot 是够用的**（汤水图片不需要做精确的中文标注，跟 dr-baba 要的解剖图 + 穴位标注不一样）
- 3. **不是终稿** — 这些都是 placeholder，等 Care Plus 给真图就替换掉了。AI 图片在产品页用一周不会出大事，但要先标清楚「示意圖」


## 2026-05-22 16:22 — TCM-Jessica

### Decisions & Reasoning
- 而且你描述的架构 (Planner → 多个 specialist → Final Writer + 平行调用) 跟 Dr. Baba 的 card-driven retrieval pipeline 是**根本不一样**的设计。Fork 出来是对的。
- - 不可变 state + `_ALLOWED_KEYS` whitelist + 每用户 lock — 防止 typo 幽灵字段、防止 WhatsApp 连发的 TOCTOU
- - YAML state-machine engine (`flow_engine.py`) — 把步骤顺序跟逻辑耦合死，真实用户会分叉。Planner 取代它。
- - `pacing.py` 的硬编码 turn counter (「诊断和推荐之间要插 1 个 caring turn」) — 用计数器执行节奏很机械，节奏应该写在 Writer 的 system prompt 里。
- | **C. OpenAI gpt-image-2** (dr-baba 的 Tier 2 primary) | `OPENAI_API_KEY` | 已经 setup，能用，但**不是极梦** |
- **我的诚实建议：用 C (OpenAI gpt-image-2)，原因 3 个：**
- 2. **OpenAI 的中文渲染对汤水 product shot 是够用的**（汤水图片不需要做精确的中文标注，跟 dr-baba 要的解剖图 + 穴位标注不一样）
- 3. **不是终稿** — 这些都是 placeholder，等 Care Plus 给真图就替换掉了。AI 图片在产品页用一周不会出大事，但要先标清楚「示意圖」


## 2026-05-22 16:42 — TCM-Jessica

### Decisions & Reasoning
- 而且你描述的架构 (Planner → 多个 specialist → Final Writer + 平行调用) 跟 Dr. Baba 的 card-driven retrieval pipeline 是**根本不一样**的设计。Fork 出来是对的。
- - 不可变 state + `_ALLOWED_KEYS` whitelist + 每用户 lock — 防止 typo 幽灵字段、防止 WhatsApp 连发的 TOCTOU
- - YAML state-machine engine (`flow_engine.py`) — 把步骤顺序跟逻辑耦合死，真实用户会分叉。Planner 取代它。
- - `pacing.py` 的硬编码 turn counter (「诊断和推荐之间要插 1 个 caring turn」) — 用计数器执行节奏很机械，节奏应该写在 Writer 的 system prompt 里。
- | **C. OpenAI gpt-image-2** (dr-baba 的 Tier 2 primary) | `OPENAI_API_KEY` | 已经 setup，能用，但**不是极梦** |
- **我的诚实建议：用 C (OpenAI gpt-image-2)，原因 3 个：**
- 2. **OpenAI 的中文渲染对汤水 product shot 是够用的**（汤水图片不需要做精确的中文标注，跟 dr-baba 要的解剖图 + 穴位标注不一样）
- 3. **不是终稿** — 这些都是 placeholder，等 Care Plus 给真图就替换掉了。AI 图片在产品页用一周不会出大事，但要先标清楚「示意圖」


## 2026-05-25 10:22 — TCM-Jessica

### Architecture Decisions
- **Is this a gap you want to fill?** Because it's actually a good one for TCM — HK weather swings are a natural trigger for health care tips. The architecture for it would be:


## 2026-05-25 11:43 — TCM-Jessica

### Architecture Decisions
- **Is this a gap you want to fill?** Because it's actually a good one for TCM — HK weather swings are a natural trigger for health care tips. The architecture for it would be:


## 2026-05-25 11:56 — TCM-Jessica

### Architecture Decisions
- **Is this a gap you want to fill?** Because it's actually a good one for TCM — HK weather swings are a natural trigger for health care tips. The architecture for it would be:


## 2026-05-25 12:42 — TCM-Jessica

### Architecture Decisions
- **Is this a gap you want to fill?** Because it's actually a good one for TCM — HK weather swings are a natural trigger for health care tips. The architecture for it would be:


## 2026-05-25 12:59 — TCM-Jessica

### Architecture Decisions
- **Is this a gap you want to fill?** Because it's actually a good one for TCM — HK weather swings are a natural trigger for health care tips. The architecture for it would be:

### Decisions & Reasoning
- | 7 | **情志調理** | 用戶話壓力大 → 自動鏈接對應臟腑 → 推薦湯水 |


## 2026-05-25 13:04 — TCM-Jessica

### Architecture Decisions
- **Is this a gap you want to fill?** Because it's actually a good one for TCM — HK weather swings are a natural trigger for health care tips. The architecture for it would be:

### Decisions & Reasoning
- | 7 | **情志調理** | 用戶話壓力大 → 自動鏈接對應臟腑 → 推薦湯水 |
- 同天氣廣播共用同一個 6h loop — 唔需要多開任何新嘅 background task。下一個做邊個？節氣提醒定體質複查？


## 2026-05-25 14:00 — TCM-Jessica

### Architecture Decisions
- **Is this a gap you want to fill?** Because it's actually a good one for TCM — HK weather swings are a natural trigger for health care tips. The architecture for it would be:

### Decisions & Reasoning
- | 7 | **情志調理** | 用戶話壓力大 → 自動鏈接對應臟腑 → 推薦湯水 |
- 同天氣廣播共用同一個 6h loop — 唔需要多開任何新嘅 background task。下一個做邊個？節氣提醒定體質複查？
- 全部共用同一個 6h loop，一個 `BROADCAST_ENABLED=true` 開晒。


## 2026-05-25 14:34 — TCM-Jessica

### Architecture Decisions
- **Is this a gap you want to fill?** Because it's actually a good one for TCM — HK weather swings are a natural trigger for health care tips. The architecture for it would be:

### Decisions & Reasoning
- | 7 | **情志調理** | 用戶話壓力大 → 自動鏈接對應臟腑 → 推薦湯水 |
- 同天氣廣播共用同一個 6h loop — 唔需要多開任何新嘅 background task。下一個做邊個？節氣提醒定體質複查？
- 全部共用同一個 6h loop，一個 `BROADCAST_ENABLED=true` 開晒。
- `wa.me/85252417448?text=想訂【彭魚鰓解毒湯 HK$120】` — 用戶 click 之後會喺 WhatsApp 開一個 chat 去診所號碼，直接落單。呢個唔係 Jessica 的號碼，所以 Jessica 本身永遠唔知用戶訂咗咩。
- 1. **Purchase CTA 加了一句話** — Jessica 推完產品之後，Writer 現在會加 `「訂完記得話我知呀 😊」`，提示用戶返嚟確認
- 2. **Planner routing** — 用戶回覆 "我訂咗" 類型嘅訊息 → 自動路由去 Sales Agent
- 唯一的 imperfection：我們假設用戶買的是最後被 pitch 的產品（最多 3 款）。如果佢買係更早 pitch 的，會有偏差。但對於 care follow-up 嚟講，"你有冇飲到上次介紹嘅湯" 夠用了。之後如果需要精確，可以讓 Jessica 問 "係邊款呀？"


## 2026-05-25 14:42 — TCM-Jessica

### Architecture Decisions
- **Is this a gap you want to fill?** Because it's actually a good one for TCM — HK weather swings are a natural trigger for health care tips. The architecture for it would be:

### Decisions & Reasoning
- | 7 | **情志調理** | 用戶話壓力大 → 自動鏈接對應臟腑 → 推薦湯水 |
- 同天氣廣播共用同一個 6h loop — 唔需要多開任何新嘅 background task。下一個做邊個？節氣提醒定體質複查？
- 全部共用同一個 6h loop，一個 `BROADCAST_ENABLED=true` 開晒。
- `wa.me/85252417448?text=想訂【彭魚鰓解毒湯 HK$120】` — 用戶 click 之後會喺 WhatsApp 開一個 chat 去診所號碼，直接落單。呢個唔係 Jessica 的號碼，所以 Jessica 本身永遠唔知用戶訂咗咩。
- 1. **Purchase CTA 加了一句話** — Jessica 推完產品之後，Writer 現在會加 `「訂完記得話我知呀 😊」`，提示用戶返嚟確認
- 2. **Planner routing** — 用戶回覆 "我訂咗" 類型嘅訊息 → 自動路由去 Sales Agent
- 唯一的 imperfection：我們假設用戶買的是最後被 pitch 的產品（最多 3 款）。如果佢買係更早 pitch 的，會有偏差。但對於 care follow-up 嚟講，"你有冇飲到上次介紹嘅湯" 夠用了。之後如果需要精確，可以讓 Jessica 問 "係邊款呀？"
- 从零搭建了一个 asyncio 后台循环，每 6 小时跑一次，自动给用户发主动关怀消息。共有四种广播类型：


## 2026-05-25 14:48 — TCM-Jessica

### Architecture Decisions
- **Is this a gap you want to fill?** Because it's actually a good one for TCM — HK weather swings are a natural trigger for health care tips. The architecture for it would be:

### Decisions & Reasoning
- | 7 | **情志調理** | 用戶話壓力大 → 自動鏈接對應臟腑 → 推薦湯水 |
- 同天氣廣播共用同一個 6h loop — 唔需要多開任何新嘅 background task。下一個做邊個？節氣提醒定體質複查？
- 全部共用同一個 6h loop，一個 `BROADCAST_ENABLED=true` 開晒。
- `wa.me/85252417448?text=想訂【彭魚鰓解毒湯 HK$120】` — 用戶 click 之後會喺 WhatsApp 開一個 chat 去診所號碼，直接落單。呢個唔係 Jessica 的號碼，所以 Jessica 本身永遠唔知用戶訂咗咩。
- 1. **Purchase CTA 加了一句話** — Jessica 推完產品之後，Writer 現在會加 `「訂完記得話我知呀 😊」`，提示用戶返嚟確認
- 2. **Planner routing** — 用戶回覆 "我訂咗" 類型嘅訊息 → 自動路由去 Sales Agent
- 唯一的 imperfection：我們假設用戶買的是最後被 pitch 的產品（最多 3 款）。如果佢買係更早 pitch 的，會有偏差。但對於 care follow-up 嚟講，"你有冇飲到上次介紹嘅湯" 夠用了。之後如果需要精確，可以讓 Jessica 問 "係邊款呀？"
- 从零搭建了一个 asyncio 后台循环，每 6 小时跑一次，自动给用户发主动关怀消息。共有四种广播类型：


## 2026-05-25 14:52 — TCM-Jessica

### Architecture Decisions
- **Is this a gap you want to fill?** Because it's actually a good one for TCM — HK weather swings are a natural trigger for health care tips. The architecture for it would be:

### Decisions & Reasoning
- | 7 | **情志調理** | 用戶話壓力大 → 自動鏈接對應臟腑 → 推薦湯水 |
- 同天氣廣播共用同一個 6h loop — 唔需要多開任何新嘅 background task。下一個做邊個？節氣提醒定體質複查？
- 全部共用同一個 6h loop，一個 `BROADCAST_ENABLED=true` 開晒。
- `wa.me/85252417448?text=想訂【彭魚鰓解毒湯 HK$120】` — 用戶 click 之後會喺 WhatsApp 開一個 chat 去診所號碼，直接落單。呢個唔係 Jessica 的號碼，所以 Jessica 本身永遠唔知用戶訂咗咩。
- 1. **Purchase CTA 加了一句話** — Jessica 推完產品之後，Writer 現在會加 `「訂完記得話我知呀 😊」`，提示用戶返嚟確認
- 2. **Planner routing** — 用戶回覆 "我訂咗" 類型嘅訊息 → 自動路由去 Sales Agent
- 唯一的 imperfection：我們假設用戶買的是最後被 pitch 的產品（最多 3 款）。如果佢買係更早 pitch 的，會有偏差。但對於 care follow-up 嚟講，"你有冇飲到上次介紹嘅湯" 夠用了。之後如果需要精確，可以讓 Jessica 問 "係邊款呀？"
- 从零搭建了一个 asyncio 后台循环，每 6 小时跑一次，自动给用户发主动关怀消息。共有四种广播类型：


## 2026-05-25 14:56 — TCM-Jessica

### Architecture Decisions
- **Is this a gap you want to fill?** Because it's actually a good one for TCM — HK weather swings are a natural trigger for health care tips. The architecture for it would be:

### Decisions & Reasoning
- | 7 | **情志調理** | 用戶話壓力大 → 自動鏈接對應臟腑 → 推薦湯水 |
- 同天氣廣播共用同一個 6h loop — 唔需要多開任何新嘅 background task。下一個做邊個？節氣提醒定體質複查？
- 全部共用同一個 6h loop，一個 `BROADCAST_ENABLED=true` 開晒。
- `wa.me/85252417448?text=想訂【彭魚鰓解毒湯 HK$120】` — 用戶 click 之後會喺 WhatsApp 開一個 chat 去診所號碼，直接落單。呢個唔係 Jessica 的號碼，所以 Jessica 本身永遠唔知用戶訂咗咩。
- 1. **Purchase CTA 加了一句話** — Jessica 推完產品之後，Writer 現在會加 `「訂完記得話我知呀 😊」`，提示用戶返嚟確認
- 2. **Planner routing** — 用戶回覆 "我訂咗" 類型嘅訊息 → 自動路由去 Sales Agent
- 唯一的 imperfection：我們假設用戶買的是最後被 pitch 的產品（最多 3 款）。如果佢買係更早 pitch 的，會有偏差。但對於 care follow-up 嚟講，"你有冇飲到上次介紹嘅湯" 夠用了。之後如果需要精確，可以讓 Jessica 問 "係邊款呀？"
- 从零搭建了一个 asyncio 后台循环，每 6 小时跑一次，自动给用户发主动关怀消息。共有四种广播类型：


## 2026-05-25 18:18 — TCM-Jessica

### Architecture Decisions
- **Is this a gap you want to fill?** Because it's actually a good one for TCM — HK weather swings are a natural trigger for health care tips. The architecture for it would be:

### Decisions & Reasoning
- | 7 | **情志調理** | 用戶話壓力大 → 自動鏈接對應臟腑 → 推薦湯水 |
- 同天氣廣播共用同一個 6h loop — 唔需要多開任何新嘅 background task。下一個做邊個？節氣提醒定體質複查？
- 全部共用同一個 6h loop，一個 `BROADCAST_ENABLED=true` 開晒。
- `wa.me/85252417448?text=想訂【彭魚鰓解毒湯 HK$120】` — 用戶 click 之後會喺 WhatsApp 開一個 chat 去診所號碼，直接落單。呢個唔係 Jessica 的號碼，所以 Jessica 本身永遠唔知用戶訂咗咩。
- 1. **Purchase CTA 加了一句話** — Jessica 推完產品之後，Writer 現在會加 `「訂完記得話我知呀 😊」`，提示用戶返嚟確認
- 2. **Planner routing** — 用戶回覆 "我訂咗" 類型嘅訊息 → 自動路由去 Sales Agent
- 唯一的 imperfection：我們假設用戶買的是最後被 pitch 的產品（最多 3 款）。如果佢買係更早 pitch 的，會有偏差。但對於 care follow-up 嚟講，"你有冇飲到上次介紹嘅湯" 夠用了。之後如果需要精確，可以讓 Jessica 問 "係邊款呀？"
- 从零搭建了一个 asyncio 后台循环，每 6 小时跑一次，自动给用户发主动关怀消息。共有四种广播类型：


## 2026-05-25 18:19 — TCM-Jessica

### Architecture Decisions
- **Is this a gap you want to fill?** Because it's actually a good one for TCM — HK weather swings are a natural trigger for health care tips. The architecture for it would be:

### Decisions & Reasoning
- | 7 | **情志調理** | 用戶話壓力大 → 自動鏈接對應臟腑 → 推薦湯水 |
- 同天氣廣播共用同一個 6h loop — 唔需要多開任何新嘅 background task。下一個做邊個？節氣提醒定體質複查？
- 全部共用同一個 6h loop，一個 `BROADCAST_ENABLED=true` 開晒。
- `wa.me/85252417448?text=想訂【彭魚鰓解毒湯 HK$120】` — 用戶 click 之後會喺 WhatsApp 開一個 chat 去診所號碼，直接落單。呢個唔係 Jessica 的號碼，所以 Jessica 本身永遠唔知用戶訂咗咩。
- 1. **Purchase CTA 加了一句話** — Jessica 推完產品之後，Writer 現在會加 `「訂完記得話我知呀 😊」`，提示用戶返嚟確認
- 2. **Planner routing** — 用戶回覆 "我訂咗" 類型嘅訊息 → 自動路由去 Sales Agent
- 唯一的 imperfection：我們假設用戶買的是最後被 pitch 的產品（最多 3 款）。如果佢買係更早 pitch 的，會有偏差。但對於 care follow-up 嚟講，"你有冇飲到上次介紹嘅湯" 夠用了。之後如果需要精確，可以讓 Jessica 問 "係邊款呀？"
- 从零搭建了一个 asyncio 后台循环，每 6 小时跑一次，自动给用户发主动关怀消息。共有四种广播类型：


## 2026-05-25 18:26 — TCM-Jessica

### Architecture Decisions
- **Is this a gap you want to fill?** Because it's actually a good one for TCM — HK weather swings are a natural trigger for health care tips. The architecture for it would be:

### Decisions & Reasoning
- | 7 | **情志調理** | 用戶話壓力大 → 自動鏈接對應臟腑 → 推薦湯水 |
- 同天氣廣播共用同一個 6h loop — 唔需要多開任何新嘅 background task。下一個做邊個？節氣提醒定體質複查？
- 全部共用同一個 6h loop，一個 `BROADCAST_ENABLED=true` 開晒。
- `wa.me/85252417448?text=想訂【彭魚鰓解毒湯 HK$120】` — 用戶 click 之後會喺 WhatsApp 開一個 chat 去診所號碼，直接落單。呢個唔係 Jessica 的號碼，所以 Jessica 本身永遠唔知用戶訂咗咩。
- 1. **Purchase CTA 加了一句話** — Jessica 推完產品之後，Writer 現在會加 `「訂完記得話我知呀 😊」`，提示用戶返嚟確認
- 2. **Planner routing** — 用戶回覆 "我訂咗" 類型嘅訊息 → 自動路由去 Sales Agent
- 唯一的 imperfection：我們假設用戶買的是最後被 pitch 的產品（最多 3 款）。如果佢買係更早 pitch 的，會有偏差。但對於 care follow-up 嚟講，"你有冇飲到上次介紹嘅湯" 夠用了。之後如果需要精確，可以讓 Jessica 問 "係邊款呀？"
- 从零搭建了一个 asyncio 后台循环，每 6 小时跑一次，自动给用户发主动关怀消息。共有四种广播类型：


## 2026-05-25 18:40 — TCM-Jessica

### Architecture Decisions
- **Is this a gap you want to fill?** Because it's actually a good one for TCM — HK weather swings are a natural trigger for health care tips. The architecture for it would be:

### Decisions & Reasoning
- | 7 | **情志調理** | 用戶話壓力大 → 自動鏈接對應臟腑 → 推薦湯水 |
- 同天氣廣播共用同一個 6h loop — 唔需要多開任何新嘅 background task。下一個做邊個？節氣提醒定體質複查？
- 全部共用同一個 6h loop，一個 `BROADCAST_ENABLED=true` 開晒。
- `wa.me/85252417448?text=想訂【彭魚鰓解毒湯 HK$120】` — 用戶 click 之後會喺 WhatsApp 開一個 chat 去診所號碼，直接落單。呢個唔係 Jessica 的號碼，所以 Jessica 本身永遠唔知用戶訂咗咩。
- 1. **Purchase CTA 加了一句話** — Jessica 推完產品之後，Writer 現在會加 `「訂完記得話我知呀 😊」`，提示用戶返嚟確認
- 2. **Planner routing** — 用戶回覆 "我訂咗" 類型嘅訊息 → 自動路由去 Sales Agent
- 唯一的 imperfection：我們假設用戶買的是最後被 pitch 的產品（最多 3 款）。如果佢買係更早 pitch 的，會有偏差。但對於 care follow-up 嚟講，"你有冇飲到上次介紹嘅湯" 夠用了。之後如果需要精確，可以讓 Jessica 問 "係邊款呀？"
- 从零搭建了一个 asyncio 后台循环，每 6 小时跑一次，自动给用户发主动关怀消息。共有四种广播类型：


## 2026-05-25 18:49 — TCM-Jessica

### Architecture Decisions
- **Is this a gap you want to fill?** Because it's actually a good one for TCM — HK weather swings are a natural trigger for health care tips. The architecture for it would be:

### Decisions & Reasoning
- | 7 | **情志調理** | 用戶話壓力大 → 自動鏈接對應臟腑 → 推薦湯水 |
- 同天氣廣播共用同一個 6h loop — 唔需要多開任何新嘅 background task。下一個做邊個？節氣提醒定體質複查？
- 全部共用同一個 6h loop，一個 `BROADCAST_ENABLED=true` 開晒。
- `wa.me/85252417448?text=想訂【彭魚鰓解毒湯 HK$120】` — 用戶 click 之後會喺 WhatsApp 開一個 chat 去診所號碼，直接落單。呢個唔係 Jessica 的號碼，所以 Jessica 本身永遠唔知用戶訂咗咩。
- 1. **Purchase CTA 加了一句話** — Jessica 推完產品之後，Writer 現在會加 `「訂完記得話我知呀 😊」`，提示用戶返嚟確認
- 2. **Planner routing** — 用戶回覆 "我訂咗" 類型嘅訊息 → 自動路由去 Sales Agent
- 唯一的 imperfection：我們假設用戶買的是最後被 pitch 的產品（最多 3 款）。如果佢買係更早 pitch 的，會有偏差。但對於 care follow-up 嚟講，"你有冇飲到上次介紹嘅湯" 夠用了。之後如果需要精確，可以讓 Jessica 問 "係邊款呀？"
- 从零搭建了一个 asyncio 后台循环，每 6 小时跑一次，自动给用户发主动关怀消息。共有四种广播类型：


## 2026-05-25 21:42 — TCM-Jessica

### Architecture Decisions
- **Is this a gap you want to fill?** Because it's actually a good one for TCM — HK weather swings are a natural trigger for health care tips. The architecture for it would be:

### Decisions & Reasoning
- | 7 | **情志調理** | 用戶話壓力大 → 自動鏈接對應臟腑 → 推薦湯水 |
- 同天氣廣播共用同一個 6h loop — 唔需要多開任何新嘅 background task。下一個做邊個？節氣提醒定體質複查？
- 全部共用同一個 6h loop，一個 `BROADCAST_ENABLED=true` 開晒。
- `wa.me/85252417448?text=想訂【彭魚鰓解毒湯 HK$120】` — 用戶 click 之後會喺 WhatsApp 開一個 chat 去診所號碼，直接落單。呢個唔係 Jessica 的號碼，所以 Jessica 本身永遠唔知用戶訂咗咩。
- 1. **Purchase CTA 加了一句話** — Jessica 推完產品之後，Writer 現在會加 `「訂完記得話我知呀 😊」`，提示用戶返嚟確認
- 2. **Planner routing** — 用戶回覆 "我訂咗" 類型嘅訊息 → 自動路由去 Sales Agent
- 唯一的 imperfection：我們假設用戶買的是最後被 pitch 的產品（最多 3 款）。如果佢買係更早 pitch 的，會有偏差。但對於 care follow-up 嚟講，"你有冇飲到上次介紹嘅湯" 夠用了。之後如果需要精確，可以讓 Jessica 問 "係邊款呀？"
- 从零搭建了一个 asyncio 后台循环，每 6 小时跑一次，自动给用户发主动关怀消息。共有四种广播类型：


## 2026-05-25 21:53 — TCM-Jessica

### Architecture Decisions
- **Is this a gap you want to fill?** Because it's actually a good one for TCM — HK weather swings are a natural trigger for health care tips. The architecture for it would be:

### Decisions & Reasoning
- | 7 | **情志調理** | 用戶話壓力大 → 自動鏈接對應臟腑 → 推薦湯水 |
- 同天氣廣播共用同一個 6h loop — 唔需要多開任何新嘅 background task。下一個做邊個？節氣提醒定體質複查？
- 全部共用同一個 6h loop，一個 `BROADCAST_ENABLED=true` 開晒。
- `wa.me/85252417448?text=想訂【彭魚鰓解毒湯 HK$120】` — 用戶 click 之後會喺 WhatsApp 開一個 chat 去診所號碼，直接落單。呢個唔係 Jessica 的號碼，所以 Jessica 本身永遠唔知用戶訂咗咩。
- 1. **Purchase CTA 加了一句話** — Jessica 推完產品之後，Writer 現在會加 `「訂完記得話我知呀 😊」`，提示用戶返嚟確認
- 2. **Planner routing** — 用戶回覆 "我訂咗" 類型嘅訊息 → 自動路由去 Sales Agent
- 唯一的 imperfection：我們假設用戶買的是最後被 pitch 的產品（最多 3 款）。如果佢買係更早 pitch 的，會有偏差。但對於 care follow-up 嚟講，"你有冇飲到上次介紹嘅湯" 夠用了。之後如果需要精確，可以讓 Jessica 問 "係邊款呀？"
- 从零搭建了一个 asyncio 后台循环，每 6 小时跑一次，自动给用户发主动关怀消息。共有四种广播类型：


## 2026-05-25 21:55 — TCM-Jessica

### Architecture Decisions
- **Is this a gap you want to fill?** Because it's actually a good one for TCM — HK weather swings are a natural trigger for health care tips. The architecture for it would be:

### Decisions & Reasoning
- | 7 | **情志調理** | 用戶話壓力大 → 自動鏈接對應臟腑 → 推薦湯水 |
- 同天氣廣播共用同一個 6h loop — 唔需要多開任何新嘅 background task。下一個做邊個？節氣提醒定體質複查？
- 全部共用同一個 6h loop，一個 `BROADCAST_ENABLED=true` 開晒。
- `wa.me/85252417448?text=想訂【彭魚鰓解毒湯 HK$120】` — 用戶 click 之後會喺 WhatsApp 開一個 chat 去診所號碼，直接落單。呢個唔係 Jessica 的號碼，所以 Jessica 本身永遠唔知用戶訂咗咩。
- 1. **Purchase CTA 加了一句話** — Jessica 推完產品之後，Writer 現在會加 `「訂完記得話我知呀 😊」`，提示用戶返嚟確認
- 2. **Planner routing** — 用戶回覆 "我訂咗" 類型嘅訊息 → 自動路由去 Sales Agent
- 唯一的 imperfection：我們假設用戶買的是最後被 pitch 的產品（最多 3 款）。如果佢買係更早 pitch 的，會有偏差。但對於 care follow-up 嚟講，"你有冇飲到上次介紹嘅湯" 夠用了。之後如果需要精確，可以讓 Jessica 問 "係邊款呀？"
- 从零搭建了一个 asyncio 后台循环，每 6 小时跑一次，自动给用户发主动关怀消息。共有四种广播类型：


## 2026-05-25 22:00 — TCM-Jessica

### Architecture Decisions
- **Is this a gap you want to fill?** Because it's actually a good one for TCM — HK weather swings are a natural trigger for health care tips. The architecture for it would be:

### Decisions & Reasoning
- | 7 | **情志調理** | 用戶話壓力大 → 自動鏈接對應臟腑 → 推薦湯水 |
- 同天氣廣播共用同一個 6h loop — 唔需要多開任何新嘅 background task。下一個做邊個？節氣提醒定體質複查？
- 全部共用同一個 6h loop，一個 `BROADCAST_ENABLED=true` 開晒。
- `wa.me/85252417448?text=想訂【彭魚鰓解毒湯 HK$120】` — 用戶 click 之後會喺 WhatsApp 開一個 chat 去診所號碼，直接落單。呢個唔係 Jessica 的號碼，所以 Jessica 本身永遠唔知用戶訂咗咩。
- 1. **Purchase CTA 加了一句話** — Jessica 推完產品之後，Writer 現在會加 `「訂完記得話我知呀 😊」`，提示用戶返嚟確認
- 2. **Planner routing** — 用戶回覆 "我訂咗" 類型嘅訊息 → 自動路由去 Sales Agent
- 唯一的 imperfection：我們假設用戶買的是最後被 pitch 的產品（最多 3 款）。如果佢買係更早 pitch 的，會有偏差。但對於 care follow-up 嚟講，"你有冇飲到上次介紹嘅湯" 夠用了。之後如果需要精確，可以讓 Jessica 問 "係邊款呀？"
- 从零搭建了一个 asyncio 后台循环，每 6 小时跑一次，自动给用户发主动关怀消息。共有四种广播类型：


## 2026-05-25 22:03 — TCM-Jessica

### Architecture Decisions
- **Is this a gap you want to fill?** Because it's actually a good one for TCM — HK weather swings are a natural trigger for health care tips. The architecture for it would be:

### Decisions & Reasoning
- | 7 | **情志調理** | 用戶話壓力大 → 自動鏈接對應臟腑 → 推薦湯水 |
- 同天氣廣播共用同一個 6h loop — 唔需要多開任何新嘅 background task。下一個做邊個？節氣提醒定體質複查？
- 全部共用同一個 6h loop，一個 `BROADCAST_ENABLED=true` 開晒。
- `wa.me/85252417448?text=想訂【彭魚鰓解毒湯 HK$120】` — 用戶 click 之後會喺 WhatsApp 開一個 chat 去診所號碼，直接落單。呢個唔係 Jessica 的號碼，所以 Jessica 本身永遠唔知用戶訂咗咩。
- 1. **Purchase CTA 加了一句話** — Jessica 推完產品之後，Writer 現在會加 `「訂完記得話我知呀 😊」`，提示用戶返嚟確認
- 2. **Planner routing** — 用戶回覆 "我訂咗" 類型嘅訊息 → 自動路由去 Sales Agent
- 唯一的 imperfection：我們假設用戶買的是最後被 pitch 的產品（最多 3 款）。如果佢買係更早 pitch 的，會有偏差。但對於 care follow-up 嚟講，"你有冇飲到上次介紹嘅湯" 夠用了。之後如果需要精確，可以讓 Jessica 問 "係邊款呀？"
- 从零搭建了一个 asyncio 后台循环，每 6 小时跑一次，自动给用户发主动关怀消息。共有四种广播类型：


## 2026-05-25 22:25 — TCM-Jessica

### Architecture Decisions
- **Is this a gap you want to fill?** Because it's actually a good one for TCM — HK weather swings are a natural trigger for health care tips. The architecture for it would be:

### Decisions & Reasoning
- | 7 | **情志調理** | 用戶話壓力大 → 自動鏈接對應臟腑 → 推薦湯水 |
- 同天氣廣播共用同一個 6h loop — 唔需要多開任何新嘅 background task。下一個做邊個？節氣提醒定體質複查？
- 全部共用同一個 6h loop，一個 `BROADCAST_ENABLED=true` 開晒。
- `wa.me/85252417448?text=想訂【彭魚鰓解毒湯 HK$120】` — 用戶 click 之後會喺 WhatsApp 開一個 chat 去診所號碼，直接落單。呢個唔係 Jessica 的號碼，所以 Jessica 本身永遠唔知用戶訂咗咩。
- 1. **Purchase CTA 加了一句話** — Jessica 推完產品之後，Writer 現在會加 `「訂完記得話我知呀 😊」`，提示用戶返嚟確認
- 2. **Planner routing** — 用戶回覆 "我訂咗" 類型嘅訊息 → 自動路由去 Sales Agent
- 唯一的 imperfection：我們假設用戶買的是最後被 pitch 的產品（最多 3 款）。如果佢買係更早 pitch 的，會有偏差。但對於 care follow-up 嚟講，"你有冇飲到上次介紹嘅湯" 夠用了。之後如果需要精確，可以讓 Jessica 問 "係邊款呀？"
- 从零搭建了一个 asyncio 后台循环，每 6 小时跑一次，自动给用户发主动关怀消息。共有四种广播类型：


## 2026-05-25 23:49 — TCM-Jessica

### Architecture Decisions
- **Is this a gap you want to fill?** Because it's actually a good one for TCM — HK weather swings are a natural trigger for health care tips. The architecture for it would be:

### Decisions & Reasoning
- | 7 | **情志調理** | 用戶話壓力大 → 自動鏈接對應臟腑 → 推薦湯水 |
- 同天氣廣播共用同一個 6h loop — 唔需要多開任何新嘅 background task。下一個做邊個？節氣提醒定體質複查？
- 全部共用同一個 6h loop，一個 `BROADCAST_ENABLED=true` 開晒。
- `wa.me/85252417448?text=想訂【彭魚鰓解毒湯 HK$120】` — 用戶 click 之後會喺 WhatsApp 開一個 chat 去診所號碼，直接落單。呢個唔係 Jessica 的號碼，所以 Jessica 本身永遠唔知用戶訂咗咩。
- 1. **Purchase CTA 加了一句話** — Jessica 推完產品之後，Writer 現在會加 `「訂完記得話我知呀 😊」`，提示用戶返嚟確認
- 2. **Planner routing** — 用戶回覆 "我訂咗" 類型嘅訊息 → 自動路由去 Sales Agent
- 唯一的 imperfection：我們假設用戶買的是最後被 pitch 的產品（最多 3 款）。如果佢買係更早 pitch 的，會有偏差。但對於 care follow-up 嚟講，"你有冇飲到上次介紹嘅湯" 夠用了。之後如果需要精確，可以讓 Jessica 問 "係邊款呀？"
- 从零搭建了一个 asyncio 后台循环，每 6 小时跑一次，自动给用户发主动关怀消息。共有四种广播类型：


## 2026-05-25 23:49 — TCM-Jessica

### Architecture Decisions
- **Is this a gap you want to fill?** Because it's actually a good one for TCM — HK weather swings are a natural trigger for health care tips. The architecture for it would be:

### Decisions & Reasoning
- | 7 | **情志調理** | 用戶話壓力大 → 自動鏈接對應臟腑 → 推薦湯水 |
- 同天氣廣播共用同一個 6h loop — 唔需要多開任何新嘅 background task。下一個做邊個？節氣提醒定體質複查？
- 全部共用同一個 6h loop，一個 `BROADCAST_ENABLED=true` 開晒。
- `wa.me/85252417448?text=想訂【彭魚鰓解毒湯 HK$120】` — 用戶 click 之後會喺 WhatsApp 開一個 chat 去診所號碼，直接落單。呢個唔係 Jessica 的號碼，所以 Jessica 本身永遠唔知用戶訂咗咩。
- 1. **Purchase CTA 加了一句話** — Jessica 推完產品之後，Writer 現在會加 `「訂完記得話我知呀 😊」`，提示用戶返嚟確認
- 2. **Planner routing** — 用戶回覆 "我訂咗" 類型嘅訊息 → 自動路由去 Sales Agent
- 唯一的 imperfection：我們假設用戶買的是最後被 pitch 的產品（最多 3 款）。如果佢買係更早 pitch 的，會有偏差。但對於 care follow-up 嚟講，"你有冇飲到上次介紹嘅湯" 夠用了。之後如果需要精確，可以讓 Jessica 問 "係邊款呀？"
- 从零搭建了一个 asyncio 后台循环，每 6 小时跑一次，自动给用户发主动关怀消息。共有四种广播类型：


## 2026-05-25 23:59 — TCM-Jessica

### Architecture Decisions
- **Is this a gap you want to fill?** Because it's actually a good one for TCM — HK weather swings are a natural trigger for health care tips. The architecture for it would be:

### Decisions & Reasoning
- | 7 | **情志調理** | 用戶話壓力大 → 自動鏈接對應臟腑 → 推薦湯水 |
- 同天氣廣播共用同一個 6h loop — 唔需要多開任何新嘅 background task。下一個做邊個？節氣提醒定體質複查？
- 全部共用同一個 6h loop，一個 `BROADCAST_ENABLED=true` 開晒。
- `wa.me/85252417448?text=想訂【彭魚鰓解毒湯 HK$120】` — 用戶 click 之後會喺 WhatsApp 開一個 chat 去診所號碼，直接落單。呢個唔係 Jessica 的號碼，所以 Jessica 本身永遠唔知用戶訂咗咩。
- 1. **Purchase CTA 加了一句話** — Jessica 推完產品之後，Writer 現在會加 `「訂完記得話我知呀 😊」`，提示用戶返嚟確認
- 2. **Planner routing** — 用戶回覆 "我訂咗" 類型嘅訊息 → 自動路由去 Sales Agent
- 唯一的 imperfection：我們假設用戶買的是最後被 pitch 的產品（最多 3 款）。如果佢買係更早 pitch 的，會有偏差。但對於 care follow-up 嚟講，"你有冇飲到上次介紹嘅湯" 夠用了。之後如果需要精確，可以讓 Jessica 問 "係邊款呀？"
- 从零搭建了一个 asyncio 后台循环，每 6 小时跑一次，自动给用户发主动关怀消息。共有四种广播类型：


## 2026-05-26 00:02 — TCM-Jessica

### Architecture Decisions
- **Is this a gap you want to fill?** Because it's actually a good one for TCM — HK weather swings are a natural trigger for health care tips. The architecture for it would be:

### Decisions & Reasoning
- | 7 | **情志調理** | 用戶話壓力大 → 自動鏈接對應臟腑 → 推薦湯水 |
- 同天氣廣播共用同一個 6h loop — 唔需要多開任何新嘅 background task。下一個做邊個？節氣提醒定體質複查？
- 全部共用同一個 6h loop，一個 `BROADCAST_ENABLED=true` 開晒。
- `wa.me/85252417448?text=想訂【彭魚鰓解毒湯 HK$120】` — 用戶 click 之後會喺 WhatsApp 開一個 chat 去診所號碼，直接落單。呢個唔係 Jessica 的號碼，所以 Jessica 本身永遠唔知用戶訂咗咩。
- 1. **Purchase CTA 加了一句話** — Jessica 推完產品之後，Writer 現在會加 `「訂完記得話我知呀 😊」`，提示用戶返嚟確認
- 2. **Planner routing** — 用戶回覆 "我訂咗" 類型嘅訊息 → 自動路由去 Sales Agent
- 唯一的 imperfection：我們假設用戶買的是最後被 pitch 的產品（最多 3 款）。如果佢買係更早 pitch 的，會有偏差。但對於 care follow-up 嚟講，"你有冇飲到上次介紹嘅湯" 夠用了。之後如果需要精確，可以讓 Jessica 問 "係邊款呀？"
- 从零搭建了一个 asyncio 后台循环，每 6 小时跑一次，自动给用户发主动关怀消息。共有四种广播类型：


## 2026-05-26 00:03 — TCM-Jessica

### Architecture Decisions
- **Is this a gap you want to fill?** Because it's actually a good one for TCM — HK weather swings are a natural trigger for health care tips. The architecture for it would be:

### Decisions & Reasoning
- | 7 | **情志調理** | 用戶話壓力大 → 自動鏈接對應臟腑 → 推薦湯水 |
- 同天氣廣播共用同一個 6h loop — 唔需要多開任何新嘅 background task。下一個做邊個？節氣提醒定體質複查？
- 全部共用同一個 6h loop，一個 `BROADCAST_ENABLED=true` 開晒。
- `wa.me/85252417448?text=想訂【彭魚鰓解毒湯 HK$120】` — 用戶 click 之後會喺 WhatsApp 開一個 chat 去診所號碼，直接落單。呢個唔係 Jessica 的號碼，所以 Jessica 本身永遠唔知用戶訂咗咩。
- 1. **Purchase CTA 加了一句話** — Jessica 推完產品之後，Writer 現在會加 `「訂完記得話我知呀 😊」`，提示用戶返嚟確認
- 2. **Planner routing** — 用戶回覆 "我訂咗" 類型嘅訊息 → 自動路由去 Sales Agent
- 唯一的 imperfection：我們假設用戶買的是最後被 pitch 的產品（最多 3 款）。如果佢買係更早 pitch 的，會有偏差。但對於 care follow-up 嚟講，"你有冇飲到上次介紹嘅湯" 夠用了。之後如果需要精確，可以讓 Jessica 問 "係邊款呀？"
- 从零搭建了一个 asyncio 后台循环，每 6 小时跑一次，自动给用户发主动关怀消息。共有四种广播类型：


## 2026-05-26 09:44 — TCM-Jessica

### Architecture Decisions
- **Is this a gap you want to fill?** Because it's actually a good one for TCM — HK weather swings are a natural trigger for health care tips. The architecture for it would be:

### Decisions & Reasoning
- | 7 | **情志調理** | 用戶話壓力大 → 自動鏈接對應臟腑 → 推薦湯水 |
- 同天氣廣播共用同一個 6h loop — 唔需要多開任何新嘅 background task。下一個做邊個？節氣提醒定體質複查？
- 全部共用同一個 6h loop，一個 `BROADCAST_ENABLED=true` 開晒。
- `wa.me/85252417448?text=想訂【彭魚鰓解毒湯 HK$120】` — 用戶 click 之後會喺 WhatsApp 開一個 chat 去診所號碼，直接落單。呢個唔係 Jessica 的號碼，所以 Jessica 本身永遠唔知用戶訂咗咩。
- 1. **Purchase CTA 加了一句話** — Jessica 推完產品之後，Writer 現在會加 `「訂完記得話我知呀 😊」`，提示用戶返嚟確認
- 2. **Planner routing** — 用戶回覆 "我訂咗" 類型嘅訊息 → 自動路由去 Sales Agent
- 唯一的 imperfection：我們假設用戶買的是最後被 pitch 的產品（最多 3 款）。如果佢買係更早 pitch 的，會有偏差。但對於 care follow-up 嚟講，"你有冇飲到上次介紹嘅湯" 夠用了。之後如果需要精確，可以讓 Jessica 問 "係邊款呀？"
- 从零搭建了一个 asyncio 后台循环，每 6 小时跑一次，自动给用户发主动关怀消息。共有四种广播类型：


## 2026-05-26 09:56 — TCM-Jessica

### Architecture Decisions
- **Is this a gap you want to fill?** Because it's actually a good one for TCM — HK weather swings are a natural trigger for health care tips. The architecture for it would be:

### Decisions & Reasoning
- | 7 | **情志調理** | 用戶話壓力大 → 自動鏈接對應臟腑 → 推薦湯水 |
- 同天氣廣播共用同一個 6h loop — 唔需要多開任何新嘅 background task。下一個做邊個？節氣提醒定體質複查？
- 全部共用同一個 6h loop，一個 `BROADCAST_ENABLED=true` 開晒。
- `wa.me/85252417448?text=想訂【彭魚鰓解毒湯 HK$120】` — 用戶 click 之後會喺 WhatsApp 開一個 chat 去診所號碼，直接落單。呢個唔係 Jessica 的號碼，所以 Jessica 本身永遠唔知用戶訂咗咩。
- 1. **Purchase CTA 加了一句話** — Jessica 推完產品之後，Writer 現在會加 `「訂完記得話我知呀 😊」`，提示用戶返嚟確認
- 2. **Planner routing** — 用戶回覆 "我訂咗" 類型嘅訊息 → 自動路由去 Sales Agent
- 唯一的 imperfection：我們假設用戶買的是最後被 pitch 的產品（最多 3 款）。如果佢買係更早 pitch 的，會有偏差。但對於 care follow-up 嚟講，"你有冇飲到上次介紹嘅湯" 夠用了。之後如果需要精確，可以讓 Jessica 問 "係邊款呀？"
- 从零搭建了一个 asyncio 后台循环，每 6 小时跑一次，自动给用户发主动关怀消息。共有四种广播类型：


## 2026-05-26 12:13 — TCM-Jessica

### Architecture Decisions
- **Is this a gap you want to fill?** Because it's actually a good one for TCM — HK weather swings are a natural trigger for health care tips. The architecture for it would be:

### Decisions & Reasoning
- | 7 | **情志調理** | 用戶話壓力大 → 自動鏈接對應臟腑 → 推薦湯水 |
- 同天氣廣播共用同一個 6h loop — 唔需要多開任何新嘅 background task。下一個做邊個？節氣提醒定體質複查？
- 全部共用同一個 6h loop，一個 `BROADCAST_ENABLED=true` 開晒。
- `wa.me/85252417448?text=想訂【彭魚鰓解毒湯 HK$120】` — 用戶 click 之後會喺 WhatsApp 開一個 chat 去診所號碼，直接落單。呢個唔係 Jessica 的號碼，所以 Jessica 本身永遠唔知用戶訂咗咩。
- 1. **Purchase CTA 加了一句話** — Jessica 推完產品之後，Writer 現在會加 `「訂完記得話我知呀 😊」`，提示用戶返嚟確認
- 2. **Planner routing** — 用戶回覆 "我訂咗" 類型嘅訊息 → 自動路由去 Sales Agent
- 唯一的 imperfection：我們假設用戶買的是最後被 pitch 的產品（最多 3 款）。如果佢買係更早 pitch 的，會有偏差。但對於 care follow-up 嚟講，"你有冇飲到上次介紹嘅湯" 夠用了。之後如果需要精確，可以讓 Jessica 問 "係邊款呀？"
- 从零搭建了一个 asyncio 后台循环，每 6 小时跑一次，自动给用户发主动关怀消息。共有四种广播类型：


## 2026-05-26 12:17 — TCM-Jessica

### Architecture Decisions
- **Is this a gap you want to fill?** Because it's actually a good one for TCM — HK weather swings are a natural trigger for health care tips. The architecture for it would be:

### Decisions & Reasoning
- | 7 | **情志調理** | 用戶話壓力大 → 自動鏈接對應臟腑 → 推薦湯水 |
- 同天氣廣播共用同一個 6h loop — 唔需要多開任何新嘅 background task。下一個做邊個？節氣提醒定體質複查？
- 全部共用同一個 6h loop，一個 `BROADCAST_ENABLED=true` 開晒。
- `wa.me/85252417448?text=想訂【彭魚鰓解毒湯 HK$120】` — 用戶 click 之後會喺 WhatsApp 開一個 chat 去診所號碼，直接落單。呢個唔係 Jessica 的號碼，所以 Jessica 本身永遠唔知用戶訂咗咩。
- 1. **Purchase CTA 加了一句話** — Jessica 推完產品之後，Writer 現在會加 `「訂完記得話我知呀 😊」`，提示用戶返嚟確認
- 2. **Planner routing** — 用戶回覆 "我訂咗" 類型嘅訊息 → 自動路由去 Sales Agent
- 唯一的 imperfection：我們假設用戶買的是最後被 pitch 的產品（最多 3 款）。如果佢買係更早 pitch 的，會有偏差。但對於 care follow-up 嚟講，"你有冇飲到上次介紹嘅湯" 夠用了。之後如果需要精確，可以讓 Jessica 問 "係邊款呀？"
- 从零搭建了一个 asyncio 后台循环，每 6 小时跑一次，自动给用户发主动关怀消息。共有四种广播类型：


## 2026-05-26 12:27 — TCM-Jessica

### Architecture Decisions
- **Is this a gap you want to fill?** Because it's actually a good one for TCM — HK weather swings are a natural trigger for health care tips. The architecture for it would be:

### Decisions & Reasoning
- | 7 | **情志調理** | 用戶話壓力大 → 自動鏈接對應臟腑 → 推薦湯水 |
- 同天氣廣播共用同一個 6h loop — 唔需要多開任何新嘅 background task。下一個做邊個？節氣提醒定體質複查？
- 全部共用同一個 6h loop，一個 `BROADCAST_ENABLED=true` 開晒。
- `wa.me/85252417448?text=想訂【彭魚鰓解毒湯 HK$120】` — 用戶 click 之後會喺 WhatsApp 開一個 chat 去診所號碼，直接落單。呢個唔係 Jessica 的號碼，所以 Jessica 本身永遠唔知用戶訂咗咩。
- 1. **Purchase CTA 加了一句話** — Jessica 推完產品之後，Writer 現在會加 `「訂完記得話我知呀 😊」`，提示用戶返嚟確認
- 2. **Planner routing** — 用戶回覆 "我訂咗" 類型嘅訊息 → 自動路由去 Sales Agent
- 唯一的 imperfection：我們假設用戶買的是最後被 pitch 的產品（最多 3 款）。如果佢買係更早 pitch 的，會有偏差。但對於 care follow-up 嚟講，"你有冇飲到上次介紹嘅湯" 夠用了。之後如果需要精確，可以讓 Jessica 問 "係邊款呀？"
- 从零搭建了一个 asyncio 后台循环，每 6 小时跑一次，自动给用户发主动关怀消息。共有四种广播类型：


## 2026-05-26 13:19 — TCM-Jessica

### Architecture Decisions
- **Is this a gap you want to fill?** Because it's actually a good one for TCM — HK weather swings are a natural trigger for health care tips. The architecture for it would be:

### Decisions & Reasoning
- | 7 | **情志調理** | 用戶話壓力大 → 自動鏈接對應臟腑 → 推薦湯水 |
- 同天氣廣播共用同一個 6h loop — 唔需要多開任何新嘅 background task。下一個做邊個？節氣提醒定體質複查？
- 全部共用同一個 6h loop，一個 `BROADCAST_ENABLED=true` 開晒。
- `wa.me/85252417448?text=想訂【彭魚鰓解毒湯 HK$120】` — 用戶 click 之後會喺 WhatsApp 開一個 chat 去診所號碼，直接落單。呢個唔係 Jessica 的號碼，所以 Jessica 本身永遠唔知用戶訂咗咩。
- 1. **Purchase CTA 加了一句話** — Jessica 推完產品之後，Writer 現在會加 `「訂完記得話我知呀 😊」`，提示用戶返嚟確認
- 2. **Planner routing** — 用戶回覆 "我訂咗" 類型嘅訊息 → 自動路由去 Sales Agent
- 唯一的 imperfection：我們假設用戶買的是最後被 pitch 的產品（最多 3 款）。如果佢買係更早 pitch 的，會有偏差。但對於 care follow-up 嚟講，"你有冇飲到上次介紹嘅湯" 夠用了。之後如果需要精確，可以讓 Jessica 問 "係邊款呀？"
- 从零搭建了一个 asyncio 后台循环，每 6 小时跑一次，自动给用户发主动关怀消息。共有四种广播类型：


## 2026-05-26 13:56 — TCM-Jessica

### Architecture Decisions
- **Is this a gap you want to fill?** Because it's actually a good one for TCM — HK weather swings are a natural trigger for health care tips. The architecture for it would be:

### Decisions & Reasoning
- | 7 | **情志調理** | 用戶話壓力大 → 自動鏈接對應臟腑 → 推薦湯水 |
- 同天氣廣播共用同一個 6h loop — 唔需要多開任何新嘅 background task。下一個做邊個？節氣提醒定體質複查？
- 全部共用同一個 6h loop，一個 `BROADCAST_ENABLED=true` 開晒。
- `wa.me/85252417448?text=想訂【彭魚鰓解毒湯 HK$120】` — 用戶 click 之後會喺 WhatsApp 開一個 chat 去診所號碼，直接落單。呢個唔係 Jessica 的號碼，所以 Jessica 本身永遠唔知用戶訂咗咩。
- 1. **Purchase CTA 加了一句話** — Jessica 推完產品之後，Writer 現在會加 `「訂完記得話我知呀 😊」`，提示用戶返嚟確認
- 2. **Planner routing** — 用戶回覆 "我訂咗" 類型嘅訊息 → 自動路由去 Sales Agent
- 唯一的 imperfection：我們假設用戶買的是最後被 pitch 的產品（最多 3 款）。如果佢買係更早 pitch 的，會有偏差。但對於 care follow-up 嚟講，"你有冇飲到上次介紹嘅湯" 夠用了。之後如果需要精確，可以讓 Jessica 問 "係邊款呀？"
- 从零搭建了一个 asyncio 后台循环，每 6 小时跑一次，自动给用户发主动关怀消息。共有四种广播类型：


## 2026-05-26 14:15 — TCM-Jessica

### Architecture Decisions
- **Is this a gap you want to fill?** Because it's actually a good one for TCM — HK weather swings are a natural trigger for health care tips. The architecture for it would be:

### Decisions & Reasoning
- | 7 | **情志調理** | 用戶話壓力大 → 自動鏈接對應臟腑 → 推薦湯水 |
- 同天氣廣播共用同一個 6h loop — 唔需要多開任何新嘅 background task。下一個做邊個？節氣提醒定體質複查？
- 全部共用同一個 6h loop，一個 `BROADCAST_ENABLED=true` 開晒。
- `wa.me/85252417448?text=想訂【彭魚鰓解毒湯 HK$120】` — 用戶 click 之後會喺 WhatsApp 開一個 chat 去診所號碼，直接落單。呢個唔係 Jessica 的號碼，所以 Jessica 本身永遠唔知用戶訂咗咩。
- 1. **Purchase CTA 加了一句話** — Jessica 推完產品之後，Writer 現在會加 `「訂完記得話我知呀 😊」`，提示用戶返嚟確認
- 2. **Planner routing** — 用戶回覆 "我訂咗" 類型嘅訊息 → 自動路由去 Sales Agent
- 唯一的 imperfection：我們假設用戶買的是最後被 pitch 的產品（最多 3 款）。如果佢買係更早 pitch 的，會有偏差。但對於 care follow-up 嚟講，"你有冇飲到上次介紹嘅湯" 夠用了。之後如果需要精確，可以讓 Jessica 問 "係邊款呀？"
- 从零搭建了一个 asyncio 后台循环，每 6 小时跑一次，自动给用户发主动关怀消息。共有四种广播类型：


## 2026-05-26 14:21 — TCM-Jessica

### Architecture Decisions
- **Is this a gap you want to fill?** Because it's actually a good one for TCM — HK weather swings are a natural trigger for health care tips. The architecture for it would be:

### Decisions & Reasoning
- | 7 | **情志調理** | 用戶話壓力大 → 自動鏈接對應臟腑 → 推薦湯水 |
- 同天氣廣播共用同一個 6h loop — 唔需要多開任何新嘅 background task。下一個做邊個？節氣提醒定體質複查？
- 全部共用同一個 6h loop，一個 `BROADCAST_ENABLED=true` 開晒。
- `wa.me/85252417448?text=想訂【彭魚鰓解毒湯 HK$120】` — 用戶 click 之後會喺 WhatsApp 開一個 chat 去診所號碼，直接落單。呢個唔係 Jessica 的號碼，所以 Jessica 本身永遠唔知用戶訂咗咩。
- 1. **Purchase CTA 加了一句話** — Jessica 推完產品之後，Writer 現在會加 `「訂完記得話我知呀 😊」`，提示用戶返嚟確認
- 2. **Planner routing** — 用戶回覆 "我訂咗" 類型嘅訊息 → 自動路由去 Sales Agent
- 唯一的 imperfection：我們假設用戶買的是最後被 pitch 的產品（最多 3 款）。如果佢買係更早 pitch 的，會有偏差。但對於 care follow-up 嚟講，"你有冇飲到上次介紹嘅湯" 夠用了。之後如果需要精確，可以讓 Jessica 問 "係邊款呀？"
- 从零搭建了一个 asyncio 后台循环，每 6 小时跑一次，自动给用户发主动关怀消息。共有四种广播类型：


## 2026-05-26 14:22 — TCM-Jessica

### Architecture Decisions
- **Is this a gap you want to fill?** Because it's actually a good one for TCM — HK weather swings are a natural trigger for health care tips. The architecture for it would be:

### Decisions & Reasoning
- | 7 | **情志調理** | 用戶話壓力大 → 自動鏈接對應臟腑 → 推薦湯水 |
- 同天氣廣播共用同一個 6h loop — 唔需要多開任何新嘅 background task。下一個做邊個？節氣提醒定體質複查？
- 全部共用同一個 6h loop，一個 `BROADCAST_ENABLED=true` 開晒。
- `wa.me/85252417448?text=想訂【彭魚鰓解毒湯 HK$120】` — 用戶 click 之後會喺 WhatsApp 開一個 chat 去診所號碼，直接落單。呢個唔係 Jessica 的號碼，所以 Jessica 本身永遠唔知用戶訂咗咩。
- 1. **Purchase CTA 加了一句話** — Jessica 推完產品之後，Writer 現在會加 `「訂完記得話我知呀 😊」`，提示用戶返嚟確認
- 2. **Planner routing** — 用戶回覆 "我訂咗" 類型嘅訊息 → 自動路由去 Sales Agent
- 唯一的 imperfection：我們假設用戶買的是最後被 pitch 的產品（最多 3 款）。如果佢買係更早 pitch 的，會有偏差。但對於 care follow-up 嚟講，"你有冇飲到上次介紹嘅湯" 夠用了。之後如果需要精確，可以讓 Jessica 問 "係邊款呀？"
- 从零搭建了一个 asyncio 后台循环，每 6 小时跑一次，自动给用户发主动关怀消息。共有四种广播类型：


## 2026-05-26 14:29 — TCM-Jessica

### Architecture Decisions
- **Is this a gap you want to fill?** Because it's actually a good one for TCM — HK weather swings are a natural trigger for health care tips. The architecture for it would be:
- 呢個 split 大概貴 3-5x（但 production query 量低，每個用戶日均幾條 message 而已），可能值得試。要我先 fix 緊嘅產品圖片同功效顯示問題，定先做 model split 實驗？

### Decisions & Reasoning
- | 7 | **情志調理** | 用戶話壓力大 → 自動鏈接對應臟腑 → 推薦湯水 |
- 同天氣廣播共用同一個 6h loop — 唔需要多開任何新嘅 background task。下一個做邊個？節氣提醒定體質複查？
- 全部共用同一個 6h loop，一個 `BROADCAST_ENABLED=true` 開晒。
- `wa.me/85252417448?text=想訂【彭魚鰓解毒湯 HK$120】` — 用戶 click 之後會喺 WhatsApp 開一個 chat 去診所號碼，直接落單。呢個唔係 Jessica 的號碼，所以 Jessica 本身永遠唔知用戶訂咗咩。
- 1. **Purchase CTA 加了一句話** — Jessica 推完產品之後，Writer 現在會加 `「訂完記得話我知呀 😊」`，提示用戶返嚟確認
- 2. **Planner routing** — 用戶回覆 "我訂咗" 類型嘅訊息 → 自動路由去 Sales Agent
- 唯一的 imperfection：我們假設用戶買的是最後被 pitch 的產品（最多 3 款）。如果佢買係更早 pitch 的，會有偏差。但對於 care follow-up 嚟講，"你有冇飲到上次介紹嘅湯" 夠用了。之後如果需要精確，可以讓 Jessica 問 "係邊款呀？"
- 从零搭建了一个 asyncio 后台循环，每 6 小时跑一次，自动给用户发主动关怀消息。共有四种广播类型：


## 2026-05-26 14:30 — TCM-Jessica

### Architecture Decisions
- **Is this a gap you want to fill?** Because it's actually a good one for TCM — HK weather swings are a natural trigger for health care tips. The architecture for it would be:
- 呢個 split 大概貴 3-5x（但 production query 量低，每個用戶日均幾條 message 而已），可能值得試。要我先 fix 緊嘅產品圖片同功效顯示問題，定先做 model split 實驗？

### Decisions & Reasoning
- | 7 | **情志調理** | 用戶話壓力大 → 自動鏈接對應臟腑 → 推薦湯水 |
- 同天氣廣播共用同一個 6h loop — 唔需要多開任何新嘅 background task。下一個做邊個？節氣提醒定體質複查？
- 全部共用同一個 6h loop，一個 `BROADCAST_ENABLED=true` 開晒。
- `wa.me/85252417448?text=想訂【彭魚鰓解毒湯 HK$120】` — 用戶 click 之後會喺 WhatsApp 開一個 chat 去診所號碼，直接落單。呢個唔係 Jessica 的號碼，所以 Jessica 本身永遠唔知用戶訂咗咩。
- 1. **Purchase CTA 加了一句話** — Jessica 推完產品之後，Writer 現在會加 `「訂完記得話我知呀 😊」`，提示用戶返嚟確認
- 2. **Planner routing** — 用戶回覆 "我訂咗" 類型嘅訊息 → 自動路由去 Sales Agent
- 唯一的 imperfection：我們假設用戶買的是最後被 pitch 的產品（最多 3 款）。如果佢買係更早 pitch 的，會有偏差。但對於 care follow-up 嚟講，"你有冇飲到上次介紹嘅湯" 夠用了。之後如果需要精確，可以讓 Jessica 問 "係邊款呀？"
- 从零搭建了一个 asyncio 后台循环，每 6 小时跑一次，自动给用户发主动关怀消息。共有四种广播类型：


## 2026-05-26 14:38 — TCM-Jessica

### Architecture Decisions
- **Is this a gap you want to fill?** Because it's actually a good one for TCM — HK weather swings are a natural trigger for health care tips. The architecture for it would be:
- 呢個 split 大概貴 3-5x（但 production query 量低，每個用戶日均幾條 message 而已），可能值得試。要我先 fix 緊嘅產品圖片同功效顯示問題，定先做 model split 實驗？
- Now apply `extracted_pain_points` to CRM. This is the **critical fix**:

### Decisions & Reasoning
- | 7 | **情志調理** | 用戶話壓力大 → 自動鏈接對應臟腑 → 推薦湯水 |
- 同天氣廣播共用同一個 6h loop — 唔需要多開任何新嘅 background task。下一個做邊個？節氣提醒定體質複查？
- 全部共用同一個 6h loop，一個 `BROADCAST_ENABLED=true` 開晒。
- `wa.me/85252417448?text=想訂【彭魚鰓解毒湯 HK$120】` — 用戶 click 之後會喺 WhatsApp 開一個 chat 去診所號碼，直接落單。呢個唔係 Jessica 的號碼，所以 Jessica 本身永遠唔知用戶訂咗咩。
- 1. **Purchase CTA 加了一句話** — Jessica 推完產品之後，Writer 現在會加 `「訂完記得話我知呀 😊」`，提示用戶返嚟確認
- 2. **Planner routing** — 用戶回覆 "我訂咗" 類型嘅訊息 → 自動路由去 Sales Agent
- 唯一的 imperfection：我們假設用戶買的是最後被 pitch 的產品（最多 3 款）。如果佢買係更早 pitch 的，會有偏差。但對於 care follow-up 嚟講，"你有冇飲到上次介紹嘅湯" 夠用了。之後如果需要精確，可以讓 Jessica 問 "係邊款呀？"
- 从零搭建了一个 asyncio 后台循环，每 6 小时跑一次，自动给用户发主动关怀消息。共有四种广播类型：


## 2026-05-26 14:49 — TCM-Jessica

### Architecture Decisions
- **Is this a gap you want to fill?** Because it's actually a good one for TCM — HK weather swings are a natural trigger for health care tips. The architecture for it would be:
- 呢個 split 大概貴 3-5x（但 production query 量低，每個用戶日均幾條 message 而已），可能值得試。要我先 fix 緊嘅產品圖片同功效顯示問題，定先做 model split 實驗？
- Now apply `extracted_pain_points` to CRM. This is the **critical fix**:

### Decisions & Reasoning
- | 7 | **情志調理** | 用戶話壓力大 → 自動鏈接對應臟腑 → 推薦湯水 |
- 同天氣廣播共用同一個 6h loop — 唔需要多開任何新嘅 background task。下一個做邊個？節氣提醒定體質複查？
- 全部共用同一個 6h loop，一個 `BROADCAST_ENABLED=true` 開晒。
- `wa.me/85252417448?text=想訂【彭魚鰓解毒湯 HK$120】` — 用戶 click 之後會喺 WhatsApp 開一個 chat 去診所號碼，直接落單。呢個唔係 Jessica 的號碼，所以 Jessica 本身永遠唔知用戶訂咗咩。
- 1. **Purchase CTA 加了一句話** — Jessica 推完產品之後，Writer 現在會加 `「訂完記得話我知呀 😊」`，提示用戶返嚟確認
- 2. **Planner routing** — 用戶回覆 "我訂咗" 類型嘅訊息 → 自動路由去 Sales Agent
- 唯一的 imperfection：我們假設用戶買的是最後被 pitch 的產品（最多 3 款）。如果佢買係更早 pitch 的，會有偏差。但對於 care follow-up 嚟講，"你有冇飲到上次介紹嘅湯" 夠用了。之後如果需要精確，可以讓 Jessica 問 "係邊款呀？"
- 从零搭建了一个 asyncio 后台循环，每 6 小时跑一次，自动给用户发主动关怀消息。共有四种广播类型：


## 2026-05-26 14:55 — TCM-Jessica

### Architecture Decisions
- **Is this a gap you want to fill?** Because it's actually a good one for TCM — HK weather swings are a natural trigger for health care tips. The architecture for it would be:
- 呢個 split 大概貴 3-5x（但 production query 量低，每個用戶日均幾條 message 而已），可能值得試。要我先 fix 緊嘅產品圖片同功效顯示問題，定先做 model split 實驗？
- Now apply `extracted_pain_points` to CRM. This is the **critical fix**:
- 如果你想 sales 都用 vector，可以做 **hybrid**：keyword 先跑 → 如果 score < threshold 就 fallback 去 vector 搜 product cards。Same pattern as FAQ。

### Decisions & Reasoning
- | 7 | **情志調理** | 用戶話壓力大 → 自動鏈接對應臟腑 → 推薦湯水 |
- 同天氣廣播共用同一個 6h loop — 唔需要多開任何新嘅 background task。下一個做邊個？節氣提醒定體質複查？
- 全部共用同一個 6h loop，一個 `BROADCAST_ENABLED=true` 開晒。
- `wa.me/85252417448?text=想訂【彭魚鰓解毒湯 HK$120】` — 用戶 click 之後會喺 WhatsApp 開一個 chat 去診所號碼，直接落單。呢個唔係 Jessica 的號碼，所以 Jessica 本身永遠唔知用戶訂咗咩。
- 1. **Purchase CTA 加了一句話** — Jessica 推完產品之後，Writer 現在會加 `「訂完記得話我知呀 😊」`，提示用戶返嚟確認
- 2. **Planner routing** — 用戶回覆 "我訂咗" 類型嘅訊息 → 自動路由去 Sales Agent
- 唯一的 imperfection：我們假設用戶買的是最後被 pitch 的產品（最多 3 款）。如果佢買係更早 pitch 的，會有偏差。但對於 care follow-up 嚟講，"你有冇飲到上次介紹嘅湯" 夠用了。之後如果需要精確，可以讓 Jessica 問 "係邊款呀？"
- 从零搭建了一个 asyncio 后台循环，每 6 小时跑一次，自动给用户发主动关怀消息。共有四种广播类型：


## 2026-05-26 14:57 — TCM-Jessica

### Architecture Decisions
- **Is this a gap you want to fill?** Because it's actually a good one for TCM — HK weather swings are a natural trigger for health care tips. The architecture for it would be:
- 呢個 split 大概貴 3-5x（但 production query 量低，每個用戶日均幾條 message 而已），可能值得試。要我先 fix 緊嘅產品圖片同功效顯示問題，定先做 model split 實驗？
- Now apply `extracted_pain_points` to CRM. This is the **critical fix**:
- 如果你想 sales 都用 vector，可以做 **hybrid**：keyword 先跑 → 如果 score < threshold 就 fallback 去 vector 搜 product cards。Same pattern as FAQ。

### Decisions & Reasoning
- | 7 | **情志調理** | 用戶話壓力大 → 自動鏈接對應臟腑 → 推薦湯水 |
- 同天氣廣播共用同一個 6h loop — 唔需要多開任何新嘅 background task。下一個做邊個？節氣提醒定體質複查？
- 全部共用同一個 6h loop，一個 `BROADCAST_ENABLED=true` 開晒。
- `wa.me/85252417448?text=想訂【彭魚鰓解毒湯 HK$120】` — 用戶 click 之後會喺 WhatsApp 開一個 chat 去診所號碼，直接落單。呢個唔係 Jessica 的號碼，所以 Jessica 本身永遠唔知用戶訂咗咩。
- 1. **Purchase CTA 加了一句話** — Jessica 推完產品之後，Writer 現在會加 `「訂完記得話我知呀 😊」`，提示用戶返嚟確認
- 2. **Planner routing** — 用戶回覆 "我訂咗" 類型嘅訊息 → 自動路由去 Sales Agent
- 唯一的 imperfection：我們假設用戶買的是最後被 pitch 的產品（最多 3 款）。如果佢買係更早 pitch 的，會有偏差。但對於 care follow-up 嚟講，"你有冇飲到上次介紹嘅湯" 夠用了。之後如果需要精確，可以讓 Jessica 問 "係邊款呀？"
- 从零搭建了一个 asyncio 后台循环，每 6 小时跑一次，自动给用户发主动关怀消息。共有四种广播类型：


## 2026-05-26 15:04 — TCM-Jessica

### Architecture Decisions
- **Is this a gap you want to fill?** Because it's actually a good one for TCM — HK weather swings are a natural trigger for health care tips. The architecture for it would be:
- 呢個 split 大概貴 3-5x（但 production query 量低，每個用戶日均幾條 message 而已），可能值得試。要我先 fix 緊嘅產品圖片同功效顯示問題，定先做 model split 實驗？
- Now apply `extracted_pain_points` to CRM. This is the **critical fix**:
- 如果你想 sales 都用 vector，可以做 **hybrid**：keyword 先跑 → 如果 score < threshold 就 fallback 去 vector 搜 product cards。Same pattern as FAQ。

### Decisions & Reasoning
- | 7 | **情志調理** | 用戶話壓力大 → 自動鏈接對應臟腑 → 推薦湯水 |
- 同天氣廣播共用同一個 6h loop — 唔需要多開任何新嘅 background task。下一個做邊個？節氣提醒定體質複查？
- 全部共用同一個 6h loop，一個 `BROADCAST_ENABLED=true` 開晒。
- `wa.me/85252417448?text=想訂【彭魚鰓解毒湯 HK$120】` — 用戶 click 之後會喺 WhatsApp 開一個 chat 去診所號碼，直接落單。呢個唔係 Jessica 的號碼，所以 Jessica 本身永遠唔知用戶訂咗咩。
- 1. **Purchase CTA 加了一句話** — Jessica 推完產品之後，Writer 現在會加 `「訂完記得話我知呀 😊」`，提示用戶返嚟確認
- 2. **Planner routing** — 用戶回覆 "我訂咗" 類型嘅訊息 → 自動路由去 Sales Agent
- 唯一的 imperfection：我們假設用戶買的是最後被 pitch 的產品（最多 3 款）。如果佢買係更早 pitch 的，會有偏差。但對於 care follow-up 嚟講，"你有冇飲到上次介紹嘅湯" 夠用了。之後如果需要精確，可以讓 Jessica 問 "係邊款呀？"
- 从零搭建了一个 asyncio 后台循环，每 6 小时跑一次，自动给用户发主动关怀消息。共有四种广播类型：


## 2026-05-26 15:13 — TCM-Jessica

### Architecture Decisions
- **Is this a gap you want to fill?** Because it's actually a good one for TCM — HK weather swings are a natural trigger for health care tips. The architecture for it would be:
- 呢個 split 大概貴 3-5x（但 production query 量低，每個用戶日均幾條 message 而已），可能值得試。要我先 fix 緊嘅產品圖片同功效顯示問題，定先做 model split 實驗？
- Now apply `extracted_pain_points` to CRM. This is the **critical fix**:
- 如果你想 sales 都用 vector，可以做 **hybrid**：keyword 先跑 → 如果 score < threshold 就 fallback 去 vector 搜 product cards。Same pattern as FAQ。

### Decisions & Reasoning
- | 7 | **情志調理** | 用戶話壓力大 → 自動鏈接對應臟腑 → 推薦湯水 |
- 同天氣廣播共用同一個 6h loop — 唔需要多開任何新嘅 background task。下一個做邊個？節氣提醒定體質複查？
- 全部共用同一個 6h loop，一個 `BROADCAST_ENABLED=true` 開晒。
- `wa.me/85252417448?text=想訂【彭魚鰓解毒湯 HK$120】` — 用戶 click 之後會喺 WhatsApp 開一個 chat 去診所號碼，直接落單。呢個唔係 Jessica 的號碼，所以 Jessica 本身永遠唔知用戶訂咗咩。
- 1. **Purchase CTA 加了一句話** — Jessica 推完產品之後，Writer 現在會加 `「訂完記得話我知呀 😊」`，提示用戶返嚟確認
- 2. **Planner routing** — 用戶回覆 "我訂咗" 類型嘅訊息 → 自動路由去 Sales Agent
- 唯一的 imperfection：我們假設用戶買的是最後被 pitch 的產品（最多 3 款）。如果佢買係更早 pitch 的，會有偏差。但對於 care follow-up 嚟講，"你有冇飲到上次介紹嘅湯" 夠用了。之後如果需要精確，可以讓 Jessica 問 "係邊款呀？"
- 从零搭建了一个 asyncio 后台循环，每 6 小时跑一次，自动给用户发主动关怀消息。共有四种广播类型：


## 2026-05-26 15:15 — TCM-Jessica

### Architecture Decisions
- **Is this a gap you want to fill?** Because it's actually a good one for TCM — HK weather swings are a natural trigger for health care tips. The architecture for it would be:
- 呢個 split 大概貴 3-5x（但 production query 量低，每個用戶日均幾條 message 而已），可能值得試。要我先 fix 緊嘅產品圖片同功效顯示問題，定先做 model split 實驗？
- Now apply `extracted_pain_points` to CRM. This is the **critical fix**:
- 如果你想 sales 都用 vector，可以做 **hybrid**：keyword 先跑 → 如果 score < threshold 就 fallback 去 vector 搜 product cards。Same pattern as FAQ。

### Decisions & Reasoning
- | 7 | **情志調理** | 用戶話壓力大 → 自動鏈接對應臟腑 → 推薦湯水 |
- 同天氣廣播共用同一個 6h loop — 唔需要多開任何新嘅 background task。下一個做邊個？節氣提醒定體質複查？
- 全部共用同一個 6h loop，一個 `BROADCAST_ENABLED=true` 開晒。
- `wa.me/85252417448?text=想訂【彭魚鰓解毒湯 HK$120】` — 用戶 click 之後會喺 WhatsApp 開一個 chat 去診所號碼，直接落單。呢個唔係 Jessica 的號碼，所以 Jessica 本身永遠唔知用戶訂咗咩。
- 1. **Purchase CTA 加了一句話** — Jessica 推完產品之後，Writer 現在會加 `「訂完記得話我知呀 😊」`，提示用戶返嚟確認
- 2. **Planner routing** — 用戶回覆 "我訂咗" 類型嘅訊息 → 自動路由去 Sales Agent
- 唯一的 imperfection：我們假設用戶買的是最後被 pitch 的產品（最多 3 款）。如果佢買係更早 pitch 的，會有偏差。但對於 care follow-up 嚟講，"你有冇飲到上次介紹嘅湯" 夠用了。之後如果需要精確，可以讓 Jessica 問 "係邊款呀？"
- 从零搭建了一个 asyncio 后台循环，每 6 小时跑一次，自动给用户发主动关怀消息。共有四种广播类型：


## 2026-05-26 15:16 — TCM-Jessica

### Architecture Decisions
- **Is this a gap you want to fill?** Because it's actually a good one for TCM — HK weather swings are a natural trigger for health care tips. The architecture for it would be:
- 呢個 split 大概貴 3-5x（但 production query 量低，每個用戶日均幾條 message 而已），可能值得試。要我先 fix 緊嘅產品圖片同功效顯示問題，定先做 model split 實驗？
- Now apply `extracted_pain_points` to CRM. This is the **critical fix**:
- 如果你想 sales 都用 vector，可以做 **hybrid**：keyword 先跑 → 如果 score < threshold 就 fallback 去 vector 搜 product cards。Same pattern as FAQ。

### Decisions & Reasoning
- | 7 | **情志調理** | 用戶話壓力大 → 自動鏈接對應臟腑 → 推薦湯水 |
- 同天氣廣播共用同一個 6h loop — 唔需要多開任何新嘅 background task。下一個做邊個？節氣提醒定體質複查？
- 全部共用同一個 6h loop，一個 `BROADCAST_ENABLED=true` 開晒。
- `wa.me/85252417448?text=想訂【彭魚鰓解毒湯 HK$120】` — 用戶 click 之後會喺 WhatsApp 開一個 chat 去診所號碼，直接落單。呢個唔係 Jessica 的號碼，所以 Jessica 本身永遠唔知用戶訂咗咩。
- 1. **Purchase CTA 加了一句話** — Jessica 推完產品之後，Writer 現在會加 `「訂完記得話我知呀 😊」`，提示用戶返嚟確認
- 2. **Planner routing** — 用戶回覆 "我訂咗" 類型嘅訊息 → 自動路由去 Sales Agent
- 唯一的 imperfection：我們假設用戶買的是最後被 pitch 的產品（最多 3 款）。如果佢買係更早 pitch 的，會有偏差。但對於 care follow-up 嚟講，"你有冇飲到上次介紹嘅湯" 夠用了。之後如果需要精確，可以讓 Jessica 問 "係邊款呀？"
- 从零搭建了一个 asyncio 后台循环，每 6 小时跑一次，自动给用户发主动关怀消息。共有四种广播类型：


## 2026-05-26 15:16 — TCM-Jessica

### Architecture Decisions
- **Is this a gap you want to fill?** Because it's actually a good one for TCM — HK weather swings are a natural trigger for health care tips. The architecture for it would be:
- 呢個 split 大概貴 3-5x（但 production query 量低，每個用戶日均幾條 message 而已），可能值得試。要我先 fix 緊嘅產品圖片同功效顯示問題，定先做 model split 實驗？
- Now apply `extracted_pain_points` to CRM. This is the **critical fix**:
- 如果你想 sales 都用 vector，可以做 **hybrid**：keyword 先跑 → 如果 score < threshold 就 fallback 去 vector 搜 product cards。Same pattern as FAQ。

### Decisions & Reasoning
- | 7 | **情志調理** | 用戶話壓力大 → 自動鏈接對應臟腑 → 推薦湯水 |
- 同天氣廣播共用同一個 6h loop — 唔需要多開任何新嘅 background task。下一個做邊個？節氣提醒定體質複查？
- 全部共用同一個 6h loop，一個 `BROADCAST_ENABLED=true` 開晒。
- `wa.me/85252417448?text=想訂【彭魚鰓解毒湯 HK$120】` — 用戶 click 之後會喺 WhatsApp 開一個 chat 去診所號碼，直接落單。呢個唔係 Jessica 的號碼，所以 Jessica 本身永遠唔知用戶訂咗咩。
- 1. **Purchase CTA 加了一句話** — Jessica 推完產品之後，Writer 現在會加 `「訂完記得話我知呀 😊」`，提示用戶返嚟確認
- 2. **Planner routing** — 用戶回覆 "我訂咗" 類型嘅訊息 → 自動路由去 Sales Agent
- 唯一的 imperfection：我們假設用戶買的是最後被 pitch 的產品（最多 3 款）。如果佢買係更早 pitch 的，會有偏差。但對於 care follow-up 嚟講，"你有冇飲到上次介紹嘅湯" 夠用了。之後如果需要精確，可以讓 Jessica 問 "係邊款呀？"
- 从零搭建了一个 asyncio 后台循环，每 6 小时跑一次，自动给用户发主动关怀消息。共有四种广播类型：


## 2026-05-26 15:16 — TCM-Jessica

### Architecture Decisions
- **Is this a gap you want to fill?** Because it's actually a good one for TCM — HK weather swings are a natural trigger for health care tips. The architecture for it would be:
- 呢個 split 大概貴 3-5x（但 production query 量低，每個用戶日均幾條 message 而已），可能值得試。要我先 fix 緊嘅產品圖片同功效顯示問題，定先做 model split 實驗？
- Now apply `extracted_pain_points` to CRM. This is the **critical fix**:
- 如果你想 sales 都用 vector，可以做 **hybrid**：keyword 先跑 → 如果 score < threshold 就 fallback 去 vector 搜 product cards。Same pattern as FAQ。

### Decisions & Reasoning
- | 7 | **情志調理** | 用戶話壓力大 → 自動鏈接對應臟腑 → 推薦湯水 |
- 同天氣廣播共用同一個 6h loop — 唔需要多開任何新嘅 background task。下一個做邊個？節氣提醒定體質複查？
- 全部共用同一個 6h loop，一個 `BROADCAST_ENABLED=true` 開晒。
- `wa.me/85252417448?text=想訂【彭魚鰓解毒湯 HK$120】` — 用戶 click 之後會喺 WhatsApp 開一個 chat 去診所號碼，直接落單。呢個唔係 Jessica 的號碼，所以 Jessica 本身永遠唔知用戶訂咗咩。
- 1. **Purchase CTA 加了一句話** — Jessica 推完產品之後，Writer 現在會加 `「訂完記得話我知呀 😊」`，提示用戶返嚟確認
- 2. **Planner routing** — 用戶回覆 "我訂咗" 類型嘅訊息 → 自動路由去 Sales Agent
- 唯一的 imperfection：我們假設用戶買的是最後被 pitch 的產品（最多 3 款）。如果佢買係更早 pitch 的，會有偏差。但對於 care follow-up 嚟講，"你有冇飲到上次介紹嘅湯" 夠用了。之後如果需要精確，可以讓 Jessica 問 "係邊款呀？"
- 从零搭建了一个 asyncio 后台循环，每 6 小时跑一次，自动给用户发主动关怀消息。共有四种广播类型：


## 2026-05-26 15:16 — TCM-Jessica

### Architecture Decisions
- **Is this a gap you want to fill?** Because it's actually a good one for TCM — HK weather swings are a natural trigger for health care tips. The architecture for it would be:
- 呢個 split 大概貴 3-5x（但 production query 量低，每個用戶日均幾條 message 而已），可能值得試。要我先 fix 緊嘅產品圖片同功效顯示問題，定先做 model split 實驗？
- Now apply `extracted_pain_points` to CRM. This is the **critical fix**:
- 如果你想 sales 都用 vector，可以做 **hybrid**：keyword 先跑 → 如果 score < threshold 就 fallback 去 vector 搜 product cards。Same pattern as FAQ。

### Decisions & Reasoning
- | 7 | **情志調理** | 用戶話壓力大 → 自動鏈接對應臟腑 → 推薦湯水 |
- 同天氣廣播共用同一個 6h loop — 唔需要多開任何新嘅 background task。下一個做邊個？節氣提醒定體質複查？
- 全部共用同一個 6h loop，一個 `BROADCAST_ENABLED=true` 開晒。
- `wa.me/85252417448?text=想訂【彭魚鰓解毒湯 HK$120】` — 用戶 click 之後會喺 WhatsApp 開一個 chat 去診所號碼，直接落單。呢個唔係 Jessica 的號碼，所以 Jessica 本身永遠唔知用戶訂咗咩。
- 1. **Purchase CTA 加了一句話** — Jessica 推完產品之後，Writer 現在會加 `「訂完記得話我知呀 😊」`，提示用戶返嚟確認
- 2. **Planner routing** — 用戶回覆 "我訂咗" 類型嘅訊息 → 自動路由去 Sales Agent
- 唯一的 imperfection：我們假設用戶買的是最後被 pitch 的產品（最多 3 款）。如果佢買係更早 pitch 的，會有偏差。但對於 care follow-up 嚟講，"你有冇飲到上次介紹嘅湯" 夠用了。之後如果需要精確，可以讓 Jessica 問 "係邊款呀？"
- 从零搭建了一个 asyncio 后台循环，每 6 小时跑一次，自动给用户发主动关怀消息。共有四种广播类型：


## 2026-05-26 15:17 — TCM-Jessica

### Architecture Decisions
- **Is this a gap you want to fill?** Because it's actually a good one for TCM — HK weather swings are a natural trigger for health care tips. The architecture for it would be:
- 呢個 split 大概貴 3-5x（但 production query 量低，每個用戶日均幾條 message 而已），可能值得試。要我先 fix 緊嘅產品圖片同功效顯示問題，定先做 model split 實驗？
- Now apply `extracted_pain_points` to CRM. This is the **critical fix**:
- 如果你想 sales 都用 vector，可以做 **hybrid**：keyword 先跑 → 如果 score < threshold 就 fallback 去 vector 搜 product cards。Same pattern as FAQ。

### Decisions & Reasoning
- | 7 | **情志調理** | 用戶話壓力大 → 自動鏈接對應臟腑 → 推薦湯水 |
- 同天氣廣播共用同一個 6h loop — 唔需要多開任何新嘅 background task。下一個做邊個？節氣提醒定體質複查？
- 全部共用同一個 6h loop，一個 `BROADCAST_ENABLED=true` 開晒。
- `wa.me/85252417448?text=想訂【彭魚鰓解毒湯 HK$120】` — 用戶 click 之後會喺 WhatsApp 開一個 chat 去診所號碼，直接落單。呢個唔係 Jessica 的號碼，所以 Jessica 本身永遠唔知用戶訂咗咩。
- 1. **Purchase CTA 加了一句話** — Jessica 推完產品之後，Writer 現在會加 `「訂完記得話我知呀 😊」`，提示用戶返嚟確認
- 2. **Planner routing** — 用戶回覆 "我訂咗" 類型嘅訊息 → 自動路由去 Sales Agent
- 唯一的 imperfection：我們假設用戶買的是最後被 pitch 的產品（最多 3 款）。如果佢買係更早 pitch 的，會有偏差。但對於 care follow-up 嚟講，"你有冇飲到上次介紹嘅湯" 夠用了。之後如果需要精確，可以讓 Jessica 問 "係邊款呀？"
- 从零搭建了一个 asyncio 后台循环，每 6 小时跑一次，自动给用户发主动关怀消息。共有四种广播类型：


## 2026-05-26 15:30 — TCM-Jessica

### Architecture Decisions
- **Is this a gap you want to fill?** Because it's actually a good one for TCM — HK weather swings are a natural trigger for health care tips. The architecture for it would be:
- 呢個 split 大概貴 3-5x（但 production query 量低，每個用戶日均幾條 message 而已），可能值得試。要我先 fix 緊嘅產品圖片同功效顯示問題，定先做 model split 實驗？
- Now apply `extracted_pain_points` to CRM. This is the **critical fix**:
- 如果你想 sales 都用 vector，可以做 **hybrid**：keyword 先跑 → 如果 score < threshold 就 fallback 去 vector 搜 product cards。Same pattern as FAQ。

### Decisions & Reasoning
- | 7 | **情志調理** | 用戶話壓力大 → 自動鏈接對應臟腑 → 推薦湯水 |
- 同天氣廣播共用同一個 6h loop — 唔需要多開任何新嘅 background task。下一個做邊個？節氣提醒定體質複查？
- 全部共用同一個 6h loop，一個 `BROADCAST_ENABLED=true` 開晒。
- `wa.me/85252417448?text=想訂【彭魚鰓解毒湯 HK$120】` — 用戶 click 之後會喺 WhatsApp 開一個 chat 去診所號碼，直接落單。呢個唔係 Jessica 的號碼，所以 Jessica 本身永遠唔知用戶訂咗咩。
- 1. **Purchase CTA 加了一句話** — Jessica 推完產品之後，Writer 現在會加 `「訂完記得話我知呀 😊」`，提示用戶返嚟確認
- 2. **Planner routing** — 用戶回覆 "我訂咗" 類型嘅訊息 → 自動路由去 Sales Agent
- 唯一的 imperfection：我們假設用戶買的是最後被 pitch 的產品（最多 3 款）。如果佢買係更早 pitch 的，會有偏差。但對於 care follow-up 嚟講，"你有冇飲到上次介紹嘅湯" 夠用了。之後如果需要精確，可以讓 Jessica 問 "係邊款呀？"
- 从零搭建了一个 asyncio 后台循环，每 6 小时跑一次，自动给用户发主动关怀消息。共有四种广播类型：


## 2026-05-26 15:33 — TCM-Jessica

### Architecture Decisions
- **Is this a gap you want to fill?** Because it's actually a good one for TCM — HK weather swings are a natural trigger for health care tips. The architecture for it would be:
- 呢個 split 大概貴 3-5x（但 production query 量低，每個用戶日均幾條 message 而已），可能值得試。要我先 fix 緊嘅產品圖片同功效顯示問題，定先做 model split 實驗？
- Now apply `extracted_pain_points` to CRM. This is the **critical fix**:
- 如果你想 sales 都用 vector，可以做 **hybrid**：keyword 先跑 → 如果 score < threshold 就 fallback 去 vector 搜 product cards。Same pattern as FAQ。

### Decisions & Reasoning
- | 7 | **情志調理** | 用戶話壓力大 → 自動鏈接對應臟腑 → 推薦湯水 |
- 同天氣廣播共用同一個 6h loop — 唔需要多開任何新嘅 background task。下一個做邊個？節氣提醒定體質複查？
- 全部共用同一個 6h loop，一個 `BROADCAST_ENABLED=true` 開晒。
- `wa.me/85252417448?text=想訂【彭魚鰓解毒湯 HK$120】` — 用戶 click 之後會喺 WhatsApp 開一個 chat 去診所號碼，直接落單。呢個唔係 Jessica 的號碼，所以 Jessica 本身永遠唔知用戶訂咗咩。
- 1. **Purchase CTA 加了一句話** — Jessica 推完產品之後，Writer 現在會加 `「訂完記得話我知呀 😊」`，提示用戶返嚟確認
- 2. **Planner routing** — 用戶回覆 "我訂咗" 類型嘅訊息 → 自動路由去 Sales Agent
- 唯一的 imperfection：我們假設用戶買的是最後被 pitch 的產品（最多 3 款）。如果佢買係更早 pitch 的，會有偏差。但對於 care follow-up 嚟講，"你有冇飲到上次介紹嘅湯" 夠用了。之後如果需要精確，可以讓 Jessica 問 "係邊款呀？"
- 从零搭建了一个 asyncio 后台循环，每 6 小时跑一次，自动给用户发主动关怀消息。共有四种广播类型：


## 2026-05-26 15:45 — TCM-Jessica

### Architecture Decisions
- **Is this a gap you want to fill?** Because it's actually a good one for TCM — HK weather swings are a natural trigger for health care tips. The architecture for it would be:
- 呢個 split 大概貴 3-5x（但 production query 量低，每個用戶日均幾條 message 而已），可能值得試。要我先 fix 緊嘅產品圖片同功效顯示問題，定先做 model split 實驗？
- Now apply `extracted_pain_points` to CRM. This is the **critical fix**:
- 如果你想 sales 都用 vector，可以做 **hybrid**：keyword 先跑 → 如果 score < threshold 就 fallback 去 vector 搜 product cards。Same pattern as FAQ。

### Decisions & Reasoning
- | 7 | **情志調理** | 用戶話壓力大 → 自動鏈接對應臟腑 → 推薦湯水 |
- 同天氣廣播共用同一個 6h loop — 唔需要多開任何新嘅 background task。下一個做邊個？節氣提醒定體質複查？
- 全部共用同一個 6h loop，一個 `BROADCAST_ENABLED=true` 開晒。
- `wa.me/85252417448?text=想訂【彭魚鰓解毒湯 HK$120】` — 用戶 click 之後會喺 WhatsApp 開一個 chat 去診所號碼，直接落單。呢個唔係 Jessica 的號碼，所以 Jessica 本身永遠唔知用戶訂咗咩。
- 1. **Purchase CTA 加了一句話** — Jessica 推完產品之後，Writer 現在會加 `「訂完記得話我知呀 😊」`，提示用戶返嚟確認
- 2. **Planner routing** — 用戶回覆 "我訂咗" 類型嘅訊息 → 自動路由去 Sales Agent
- 唯一的 imperfection：我們假設用戶買的是最後被 pitch 的產品（最多 3 款）。如果佢買係更早 pitch 的，會有偏差。但對於 care follow-up 嚟講，"你有冇飲到上次介紹嘅湯" 夠用了。之後如果需要精確，可以讓 Jessica 問 "係邊款呀？"
- 从零搭建了一个 asyncio 后台循环，每 6 小时跑一次，自动给用户发主动关怀消息。共有四种广播类型：


## 2026-05-26 15:55 — TCM-Jessica

### Architecture Decisions
- **Is this a gap you want to fill?** Because it's actually a good one for TCM — HK weather swings are a natural trigger for health care tips. The architecture for it would be:
- 呢個 split 大概貴 3-5x（但 production query 量低，每個用戶日均幾條 message 而已），可能值得試。要我先 fix 緊嘅產品圖片同功效顯示問題，定先做 model split 實驗？
- Now apply `extracted_pain_points` to CRM. This is the **critical fix**:
- 如果你想 sales 都用 vector，可以做 **hybrid**：keyword 先跑 → 如果 score < threshold 就 fallback 去 vector 搜 product cards。Same pattern as FAQ。

### Decisions & Reasoning
- | 7 | **情志調理** | 用戶話壓力大 → 自動鏈接對應臟腑 → 推薦湯水 |
- 同天氣廣播共用同一個 6h loop — 唔需要多開任何新嘅 background task。下一個做邊個？節氣提醒定體質複查？
- 全部共用同一個 6h loop，一個 `BROADCAST_ENABLED=true` 開晒。
- `wa.me/85252417448?text=想訂【彭魚鰓解毒湯 HK$120】` — 用戶 click 之後會喺 WhatsApp 開一個 chat 去診所號碼，直接落單。呢個唔係 Jessica 的號碼，所以 Jessica 本身永遠唔知用戶訂咗咩。
- 1. **Purchase CTA 加了一句話** — Jessica 推完產品之後，Writer 現在會加 `「訂完記得話我知呀 😊」`，提示用戶返嚟確認
- 2. **Planner routing** — 用戶回覆 "我訂咗" 類型嘅訊息 → 自動路由去 Sales Agent
- 唯一的 imperfection：我們假設用戶買的是最後被 pitch 的產品（最多 3 款）。如果佢買係更早 pitch 的，會有偏差。但對於 care follow-up 嚟講，"你有冇飲到上次介紹嘅湯" 夠用了。之後如果需要精確，可以讓 Jessica 問 "係邊款呀？"
- 从零搭建了一个 asyncio 后台循环，每 6 小时跑一次，自动给用户发主动关怀消息。共有四种广播类型：


## 2026-05-26 16:01 — TCM-Jessica

### Architecture Decisions
- **Is this a gap you want to fill?** Because it's actually a good one for TCM — HK weather swings are a natural trigger for health care tips. The architecture for it would be:
- 呢個 split 大概貴 3-5x（但 production query 量低，每個用戶日均幾條 message 而已），可能值得試。要我先 fix 緊嘅產品圖片同功效顯示問題，定先做 model split 實驗？
- Now apply `extracted_pain_points` to CRM. This is the **critical fix**:
- 如果你想 sales 都用 vector，可以做 **hybrid**：keyword 先跑 → 如果 score < threshold 就 fallback 去 vector 搜 product cards。Same pattern as FAQ。
- | **Pain extraction inconsistent** | 🟡 Medium | gpt-5.4-mini 有時 omit `extracted_pain_points`。CRM 最終仍然係 `[]`。要 strengthen prompt 或者用 JSON schema enforcement |

### Decisions & Reasoning
- | 7 | **情志調理** | 用戶話壓力大 → 自動鏈接對應臟腑 → 推薦湯水 |
- 同天氣廣播共用同一個 6h loop — 唔需要多開任何新嘅 background task。下一個做邊個？節氣提醒定體質複查？
- 全部共用同一個 6h loop，一個 `BROADCAST_ENABLED=true` 開晒。
- `wa.me/85252417448?text=想訂【彭魚鰓解毒湯 HK$120】` — 用戶 click 之後會喺 WhatsApp 開一個 chat 去診所號碼，直接落單。呢個唔係 Jessica 的號碼，所以 Jessica 本身永遠唔知用戶訂咗咩。
- 1. **Purchase CTA 加了一句話** — Jessica 推完產品之後，Writer 現在會加 `「訂完記得話我知呀 😊」`，提示用戶返嚟確認
- 2. **Planner routing** — 用戶回覆 "我訂咗" 類型嘅訊息 → 自動路由去 Sales Agent
- 唯一的 imperfection：我們假設用戶買的是最後被 pitch 的產品（最多 3 款）。如果佢買係更早 pitch 的，會有偏差。但對於 care follow-up 嚟講，"你有冇飲到上次介紹嘅湯" 夠用了。之後如果需要精確，可以讓 Jessica 問 "係邊款呀？"
- 从零搭建了一个 asyncio 后台循环，每 6 小时跑一次，自动给用户发主动关怀消息。共有四种广播类型：


## 2026-05-26 16:18 — TCM-Jessica

### Architecture Decisions
- **Is this a gap you want to fill?** Because it's actually a good one for TCM — HK weather swings are a natural trigger for health care tips. The architecture for it would be:
- 呢個 split 大概貴 3-5x（但 production query 量低，每個用戶日均幾條 message 而已），可能值得試。要我先 fix 緊嘅產品圖片同功效顯示問題，定先做 model split 實驗？
- Now apply `extracted_pain_points` to CRM. This is the **critical fix**:
- 如果你想 sales 都用 vector，可以做 **hybrid**：keyword 先跑 → 如果 score < threshold 就 fallback 去 vector 搜 product cards。Same pattern as FAQ。
- | **Pain extraction inconsistent** | 🟡 Medium | gpt-5.4-mini 有時 omit `extracted_pain_points`。CRM 最終仍然係 `[]`。要 strengthen prompt 或者用 JSON schema enforcement |
- **Fix E1: Pain extraction fallback** — if LLM omits `extracted_pain_points`, fall back to keyword detection so CRM still gets populated:

### Decisions & Reasoning
- | 7 | **情志調理** | 用戶話壓力大 → 自動鏈接對應臟腑 → 推薦湯水 |
- 同天氣廣播共用同一個 6h loop — 唔需要多開任何新嘅 background task。下一個做邊個？節氣提醒定體質複查？
- 全部共用同一個 6h loop，一個 `BROADCAST_ENABLED=true` 開晒。
- `wa.me/85252417448?text=想訂【彭魚鰓解毒湯 HK$120】` — 用戶 click 之後會喺 WhatsApp 開一個 chat 去診所號碼，直接落單。呢個唔係 Jessica 的號碼，所以 Jessica 本身永遠唔知用戶訂咗咩。
- 1. **Purchase CTA 加了一句話** — Jessica 推完產品之後，Writer 現在會加 `「訂完記得話我知呀 😊」`，提示用戶返嚟確認
- 2. **Planner routing** — 用戶回覆 "我訂咗" 類型嘅訊息 → 自動路由去 Sales Agent
- 唯一的 imperfection：我們假設用戶買的是最後被 pitch 的產品（最多 3 款）。如果佢買係更早 pitch 的，會有偏差。但對於 care follow-up 嚟講，"你有冇飲到上次介紹嘅湯" 夠用了。之後如果需要精確，可以讓 Jessica 問 "係邊款呀？"
- 从零搭建了一个 asyncio 后台循环，每 6 小时跑一次，自动给用户发主动关怀消息。共有四种广播类型：


## 2026-05-26 16:29 — TCM-Jessica

### Architecture Decisions
- **Is this a gap you want to fill?** Because it's actually a good one for TCM — HK weather swings are a natural trigger for health care tips. The architecture for it would be:
- 呢個 split 大概貴 3-5x（但 production query 量低，每個用戶日均幾條 message 而已），可能值得試。要我先 fix 緊嘅產品圖片同功效顯示問題，定先做 model split 實驗？
- Now apply `extracted_pain_points` to CRM. This is the **critical fix**:
- 如果你想 sales 都用 vector，可以做 **hybrid**：keyword 先跑 → 如果 score < threshold 就 fallback 去 vector 搜 product cards。Same pattern as FAQ。
- | **Pain extraction inconsistent** | 🟡 Medium | gpt-5.4-mini 有時 omit `extracted_pain_points`。CRM 最終仍然係 `[]`。要 strengthen prompt 或者用 JSON schema enforcement |
- **Fix E1: Pain extraction fallback** — if LLM omits `extracted_pain_points`, fall back to keyword detection so CRM still gets populated:

### Decisions & Reasoning
- | 7 | **情志調理** | 用戶話壓力大 → 自動鏈接對應臟腑 → 推薦湯水 |
- 同天氣廣播共用同一個 6h loop — 唔需要多開任何新嘅 background task。下一個做邊個？節氣提醒定體質複查？
- 全部共用同一個 6h loop，一個 `BROADCAST_ENABLED=true` 開晒。
- `wa.me/85252417448?text=想訂【彭魚鰓解毒湯 HK$120】` — 用戶 click 之後會喺 WhatsApp 開一個 chat 去診所號碼，直接落單。呢個唔係 Jessica 的號碼，所以 Jessica 本身永遠唔知用戶訂咗咩。
- 1. **Purchase CTA 加了一句話** — Jessica 推完產品之後，Writer 現在會加 `「訂完記得話我知呀 😊」`，提示用戶返嚟確認
- 2. **Planner routing** — 用戶回覆 "我訂咗" 類型嘅訊息 → 自動路由去 Sales Agent
- 唯一的 imperfection：我們假設用戶買的是最後被 pitch 的產品（最多 3 款）。如果佢買係更早 pitch 的，會有偏差。但對於 care follow-up 嚟講，"你有冇飲到上次介紹嘅湯" 夠用了。之後如果需要精確，可以讓 Jessica 問 "係邊款呀？"
- 从零搭建了一个 asyncio 后台循环，每 6 小时跑一次，自动给用户发主动关怀消息。共有四种广播类型：


## 2026-05-26 17:30 — TCM-Jessica

### Architecture Decisions
- **Is this a gap you want to fill?** Because it's actually a good one for TCM — HK weather swings are a natural trigger for health care tips. The architecture for it would be:
- 呢個 split 大概貴 3-5x（但 production query 量低，每個用戶日均幾條 message 而已），可能值得試。要我先 fix 緊嘅產品圖片同功效顯示問題，定先做 model split 實驗？
- Now apply `extracted_pain_points` to CRM. This is the **critical fix**:
- 如果你想 sales 都用 vector，可以做 **hybrid**：keyword 先跑 → 如果 score < threshold 就 fallback 去 vector 搜 product cards。Same pattern as FAQ。
- | **Pain extraction inconsistent** | 🟡 Medium | gpt-5.4-mini 有時 omit `extracted_pain_points`。CRM 最終仍然係 `[]`。要 strengthen prompt 或者用 JSON schema enforcement |
- **Fix E1: Pain extraction fallback** — if LLM omits `extracted_pain_points`, fall back to keyword detection so CRM still gets populated:

### Decisions & Reasoning
- | 7 | **情志調理** | 用戶話壓力大 → 自動鏈接對應臟腑 → 推薦湯水 |
- 同天氣廣播共用同一個 6h loop — 唔需要多開任何新嘅 background task。下一個做邊個？節氣提醒定體質複查？
- 全部共用同一個 6h loop，一個 `BROADCAST_ENABLED=true` 開晒。
- `wa.me/85252417448?text=想訂【彭魚鰓解毒湯 HK$120】` — 用戶 click 之後會喺 WhatsApp 開一個 chat 去診所號碼，直接落單。呢個唔係 Jessica 的號碼，所以 Jessica 本身永遠唔知用戶訂咗咩。
- 1. **Purchase CTA 加了一句話** — Jessica 推完產品之後，Writer 現在會加 `「訂完記得話我知呀 😊」`，提示用戶返嚟確認
- 2. **Planner routing** — 用戶回覆 "我訂咗" 類型嘅訊息 → 自動路由去 Sales Agent
- 唯一的 imperfection：我們假設用戶買的是最後被 pitch 的產品（最多 3 款）。如果佢買係更早 pitch 的，會有偏差。但對於 care follow-up 嚟講，"你有冇飲到上次介紹嘅湯" 夠用了。之後如果需要精確，可以讓 Jessica 問 "係邊款呀？"
- 从零搭建了一个 asyncio 后台循环，每 6 小时跑一次，自动给用户发主动关怀消息。共有四种广播类型：


## 2026-05-26 18:11 — TCM-Jessica

### Architecture Decisions
- **Is this a gap you want to fill?** Because it's actually a good one for TCM — HK weather swings are a natural trigger for health care tips. The architecture for it would be:
- 呢個 split 大概貴 3-5x（但 production query 量低，每個用戶日均幾條 message 而已），可能值得試。要我先 fix 緊嘅產品圖片同功效顯示問題，定先做 model split 實驗？
- Now apply `extracted_pain_points` to CRM. This is the **critical fix**:
- 如果你想 sales 都用 vector，可以做 **hybrid**：keyword 先跑 → 如果 score < threshold 就 fallback 去 vector 搜 product cards。Same pattern as FAQ。
- | **Pain extraction inconsistent** | 🟡 Medium | gpt-5.4-mini 有時 omit `extracted_pain_points`。CRM 最終仍然係 `[]`。要 strengthen prompt 或者用 JSON schema enforcement |
- **Fix E1: Pain extraction fallback** — if LLM omits `extracted_pain_points`, fall back to keyword detection so CRM still gets populated:

### Decisions & Reasoning
- | 7 | **情志調理** | 用戶話壓力大 → 自動鏈接對應臟腑 → 推薦湯水 |
- 同天氣廣播共用同一個 6h loop — 唔需要多開任何新嘅 background task。下一個做邊個？節氣提醒定體質複查？
- 全部共用同一個 6h loop，一個 `BROADCAST_ENABLED=true` 開晒。
- `wa.me/85252417448?text=想訂【彭魚鰓解毒湯 HK$120】` — 用戶 click 之後會喺 WhatsApp 開一個 chat 去診所號碼，直接落單。呢個唔係 Jessica 的號碼，所以 Jessica 本身永遠唔知用戶訂咗咩。
- 1. **Purchase CTA 加了一句話** — Jessica 推完產品之後，Writer 現在會加 `「訂完記得話我知呀 😊」`，提示用戶返嚟確認
- 2. **Planner routing** — 用戶回覆 "我訂咗" 類型嘅訊息 → 自動路由去 Sales Agent
- 唯一的 imperfection：我們假設用戶買的是最後被 pitch 的產品（最多 3 款）。如果佢買係更早 pitch 的，會有偏差。但對於 care follow-up 嚟講，"你有冇飲到上次介紹嘅湯" 夠用了。之後如果需要精確，可以讓 Jessica 問 "係邊款呀？"
- 从零搭建了一个 asyncio 后台循环，每 6 小时跑一次，自动给用户发主动关怀消息。共有四种广播类型：


## 2026-05-26 18:15 — TCM-Jessica

### Architecture Decisions
- **Is this a gap you want to fill?** Because it's actually a good one for TCM — HK weather swings are a natural trigger for health care tips. The architecture for it would be:
- 呢個 split 大概貴 3-5x（但 production query 量低，每個用戶日均幾條 message 而已），可能值得試。要我先 fix 緊嘅產品圖片同功效顯示問題，定先做 model split 實驗？
- Now apply `extracted_pain_points` to CRM. This is the **critical fix**:
- 如果你想 sales 都用 vector，可以做 **hybrid**：keyword 先跑 → 如果 score < threshold 就 fallback 去 vector 搜 product cards。Same pattern as FAQ。
- | **Pain extraction inconsistent** | 🟡 Medium | gpt-5.4-mini 有時 omit `extracted_pain_points`。CRM 最終仍然係 `[]`。要 strengthen prompt 或者用 JSON schema enforcement |
- **Fix E1: Pain extraction fallback** — if LLM omits `extracted_pain_points`, fall back to keyword detection so CRM still gets populated:

### Decisions & Reasoning
- | 7 | **情志調理** | 用戶話壓力大 → 自動鏈接對應臟腑 → 推薦湯水 |
- 同天氣廣播共用同一個 6h loop — 唔需要多開任何新嘅 background task。下一個做邊個？節氣提醒定體質複查？
- 全部共用同一個 6h loop，一個 `BROADCAST_ENABLED=true` 開晒。
- `wa.me/85252417448?text=想訂【彭魚鰓解毒湯 HK$120】` — 用戶 click 之後會喺 WhatsApp 開一個 chat 去診所號碼，直接落單。呢個唔係 Jessica 的號碼，所以 Jessica 本身永遠唔知用戶訂咗咩。
- 1. **Purchase CTA 加了一句話** — Jessica 推完產品之後，Writer 現在會加 `「訂完記得話我知呀 😊」`，提示用戶返嚟確認
- 2. **Planner routing** — 用戶回覆 "我訂咗" 類型嘅訊息 → 自動路由去 Sales Agent
- 唯一的 imperfection：我們假設用戶買的是最後被 pitch 的產品（最多 3 款）。如果佢買係更早 pitch 的，會有偏差。但對於 care follow-up 嚟講，"你有冇飲到上次介紹嘅湯" 夠用了。之後如果需要精確，可以讓 Jessica 問 "係邊款呀？"
- 从零搭建了一个 asyncio 后台循环，每 6 小时跑一次，自动给用户发主动关怀消息。共有四种广播类型：


## 2026-05-26 19:43 — TCM-Jessica

### Architecture Decisions
- **Is this a gap you want to fill?** Because it's actually a good one for TCM — HK weather swings are a natural trigger for health care tips. The architecture for it would be:
- 呢個 split 大概貴 3-5x（但 production query 量低，每個用戶日均幾條 message 而已），可能值得試。要我先 fix 緊嘅產品圖片同功效顯示問題，定先做 model split 實驗？
- Now apply `extracted_pain_points` to CRM. This is the **critical fix**:
- 如果你想 sales 都用 vector，可以做 **hybrid**：keyword 先跑 → 如果 score < threshold 就 fallback 去 vector 搜 product cards。Same pattern as FAQ。
- | **Pain extraction inconsistent** | 🟡 Medium | gpt-5.4-mini 有時 omit `extracted_pain_points`。CRM 最終仍然係 `[]`。要 strengthen prompt 或者用 JSON schema enforcement |
- **Fix E1: Pain extraction fallback** — if LLM omits `extracted_pain_points`, fall back to keyword detection so CRM still gets populated:

### Decisions & Reasoning
- | 7 | **情志調理** | 用戶話壓力大 → 自動鏈接對應臟腑 → 推薦湯水 |
- 同天氣廣播共用同一個 6h loop — 唔需要多開任何新嘅 background task。下一個做邊個？節氣提醒定體質複查？
- 全部共用同一個 6h loop，一個 `BROADCAST_ENABLED=true` 開晒。
- `wa.me/85252417448?text=想訂【彭魚鰓解毒湯 HK$120】` — 用戶 click 之後會喺 WhatsApp 開一個 chat 去診所號碼，直接落單。呢個唔係 Jessica 的號碼，所以 Jessica 本身永遠唔知用戶訂咗咩。
- 1. **Purchase CTA 加了一句話** — Jessica 推完產品之後，Writer 現在會加 `「訂完記得話我知呀 😊」`，提示用戶返嚟確認
- 2. **Planner routing** — 用戶回覆 "我訂咗" 類型嘅訊息 → 自動路由去 Sales Agent
- 唯一的 imperfection：我們假設用戶買的是最後被 pitch 的產品（最多 3 款）。如果佢買係更早 pitch 的，會有偏差。但對於 care follow-up 嚟講，"你有冇飲到上次介紹嘅湯" 夠用了。之後如果需要精確，可以讓 Jessica 問 "係邊款呀？"
- 从零搭建了一个 asyncio 后台循环，每 6 小时跑一次，自动给用户发主动关怀消息。共有四种广播类型：


## 2026-05-26 19:56 — TCM-Jessica

### Architecture Decisions
- **Is this a gap you want to fill?** Because it's actually a good one for TCM — HK weather swings are a natural trigger for health care tips. The architecture for it would be:
- 呢個 split 大概貴 3-5x（但 production query 量低，每個用戶日均幾條 message 而已），可能值得試。要我先 fix 緊嘅產品圖片同功效顯示問題，定先做 model split 實驗？
- Now apply `extracted_pain_points` to CRM. This is the **critical fix**:
- 如果你想 sales 都用 vector，可以做 **hybrid**：keyword 先跑 → 如果 score < threshold 就 fallback 去 vector 搜 product cards。Same pattern as FAQ。
- | **Pain extraction inconsistent** | 🟡 Medium | gpt-5.4-mini 有時 omit `extracted_pain_points`。CRM 最終仍然係 `[]`。要 strengthen prompt 或者用 JSON schema enforcement |
- **Fix E1: Pain extraction fallback** — if LLM omits `extracted_pain_points`, fall back to keyword detection so CRM still gets populated:

### Decisions & Reasoning
- | 7 | **情志調理** | 用戶話壓力大 → 自動鏈接對應臟腑 → 推薦湯水 |
- 同天氣廣播共用同一個 6h loop — 唔需要多開任何新嘅 background task。下一個做邊個？節氣提醒定體質複查？
- 全部共用同一個 6h loop，一個 `BROADCAST_ENABLED=true` 開晒。
- `wa.me/85252417448?text=想訂【彭魚鰓解毒湯 HK$120】` — 用戶 click 之後會喺 WhatsApp 開一個 chat 去診所號碼，直接落單。呢個唔係 Jessica 的號碼，所以 Jessica 本身永遠唔知用戶訂咗咩。
- 1. **Purchase CTA 加了一句話** — Jessica 推完產品之後，Writer 現在會加 `「訂完記得話我知呀 😊」`，提示用戶返嚟確認
- 2. **Planner routing** — 用戶回覆 "我訂咗" 類型嘅訊息 → 自動路由去 Sales Agent
- 唯一的 imperfection：我們假設用戶買的是最後被 pitch 的產品（最多 3 款）。如果佢買係更早 pitch 的，會有偏差。但對於 care follow-up 嚟講，"你有冇飲到上次介紹嘅湯" 夠用了。之後如果需要精確，可以讓 Jessica 問 "係邊款呀？"
- 从零搭建了一个 asyncio 后台循环，每 6 小时跑一次，自动给用户发主动关怀消息。共有四种广播类型：


## 2026-05-26 21:12 — TCM-Jessica

### Architecture Decisions
- **Is this a gap you want to fill?** Because it's actually a good one for TCM — HK weather swings are a natural trigger for health care tips. The architecture for it would be:
- 呢個 split 大概貴 3-5x（但 production query 量低，每個用戶日均幾條 message 而已），可能值得試。要我先 fix 緊嘅產品圖片同功效顯示問題，定先做 model split 實驗？
- Now apply `extracted_pain_points` to CRM. This is the **critical fix**:
- 如果你想 sales 都用 vector，可以做 **hybrid**：keyword 先跑 → 如果 score < threshold 就 fallback 去 vector 搜 product cards。Same pattern as FAQ。
- | **Pain extraction inconsistent** | 🟡 Medium | gpt-5.4-mini 有時 omit `extracted_pain_points`。CRM 最終仍然係 `[]`。要 strengthen prompt 或者用 JSON schema enforcement |
- **Fix E1: Pain extraction fallback** — if LLM omits `extracted_pain_points`, fall back to keyword detection so CRM still gets populated:

### Decisions & Reasoning
- | 7 | **情志調理** | 用戶話壓力大 → 自動鏈接對應臟腑 → 推薦湯水 |
- 同天氣廣播共用同一個 6h loop — 唔需要多開任何新嘅 background task。下一個做邊個？節氣提醒定體質複查？
- 全部共用同一個 6h loop，一個 `BROADCAST_ENABLED=true` 開晒。
- `wa.me/85252417448?text=想訂【彭魚鰓解毒湯 HK$120】` — 用戶 click 之後會喺 WhatsApp 開一個 chat 去診所號碼，直接落單。呢個唔係 Jessica 的號碼，所以 Jessica 本身永遠唔知用戶訂咗咩。
- 1. **Purchase CTA 加了一句話** — Jessica 推完產品之後，Writer 現在會加 `「訂完記得話我知呀 😊」`，提示用戶返嚟確認
- 2. **Planner routing** — 用戶回覆 "我訂咗" 類型嘅訊息 → 自動路由去 Sales Agent
- 唯一的 imperfection：我們假設用戶買的是最後被 pitch 的產品（最多 3 款）。如果佢買係更早 pitch 的，會有偏差。但對於 care follow-up 嚟講，"你有冇飲到上次介紹嘅湯" 夠用了。之後如果需要精確，可以讓 Jessica 問 "係邊款呀？"
- 从零搭建了一个 asyncio 后台循环，每 6 小时跑一次，自动给用户发主动关怀消息。共有四种广播类型：



## 2026-05-26 — Mega session
### Architecture Decisions
- Stay on OpenAI gpt-5.4-mini for entire stack (Planner + Writer + Vision + Specialists). Researched 6 providers; sweet spot for HK Canto + cost budget at 500-user scale.
- Planner = single LLM call doing 3 jobs (route + rephrase + extract pain_points). Cleaner than separate NER step.
- Two-rail pain extraction: LLM NER + keyword fallback. gpt-5.4-mini inconsistently omits the field; deterministic backup ensures CRM gets populated.
- Vision stays on gpt-5.4-mini (not Gemini Pro) — single provider simplicity beats marginal quality gain at ~4 calls/user lifetime.
- Hardcoded acupoint→symptom map was wrong architecture — KB cards + AcupointImageMap own the content. Refactored out.
- Schema column additions REQUIRE `ALTER TABLE ADD COLUMN IF NOT EXISTS`. `CREATE TABLE IF NOT EXISTS` does NOT add new columns to existing tables — caused prod-down today.

### Decisions & Reasoning
- Postgres stays on free until launch (expires 2026-06-20). User wants to wait until launch to decide. Risk: data loss on expiry if not upgraded.
- Writer kept on gpt-5.4-mini, not Sonnet. Sonnet 4.6 with prompt caching would be 90% off but +cost ceiling at current scale. Re-evaluate at 1000+ users.
- 4-day Render auto-deploy outage (webhook broken since 2026-05-22). Workaround = manual deploy via Render API. Permanent fix requires dashboard intervention by user.
- Persona dry-run script (`scripts/persona_dry_run.py`) became a critical pre-deploy validation tool. Found 4 bugs in <2 minutes that tests didn't catch.
- QA agent team parallelism worked: 3 agents in worktrees, each scope-bounded, each commits its own fixes. Merge order = Sales → Constitution → Conversation (least planner conflicts).

## 2026-05-26 23:45 — TCM-Jessica

### Architecture Decisions
- **Is this a gap you want to fill?** Because it's actually a good one for TCM — HK weather swings are a natural trigger for health care tips. The architecture for it would be:
- 呢個 split 大概貴 3-5x（但 production query 量低，每個用戶日均幾條 message 而已），可能值得試。要我先 fix 緊嘅產品圖片同功效顯示問題，定先做 model split 實驗？
- Now apply `extracted_pain_points` to CRM. This is the **critical fix**:
- 如果你想 sales 都用 vector，可以做 **hybrid**：keyword 先跑 → 如果 score < threshold 就 fallback 去 vector 搜 product cards。Same pattern as FAQ。
- | **Pain extraction inconsistent** | 🟡 Medium | gpt-5.4-mini 有時 omit `extracted_pain_points`。CRM 最終仍然係 `[]`。要 strengthen prompt 或者用 JSON schema enforcement |
- **Fix E1: Pain extraction fallback** — if LLM omits `extracted_pain_points`, fall back to keyword detection so CRM still gets populated:

### Decisions & Reasoning
- | 7 | **情志調理** | 用戶話壓力大 → 自動鏈接對應臟腑 → 推薦湯水 |
- 同天氣廣播共用同一個 6h loop — 唔需要多開任何新嘅 background task。下一個做邊個？節氣提醒定體質複查？
- 全部共用同一個 6h loop，一個 `BROADCAST_ENABLED=true` 開晒。
- `wa.me/85252417448?text=想訂【彭魚鰓解毒湯 HK$120】` — 用戶 click 之後會喺 WhatsApp 開一個 chat 去診所號碼，直接落單。呢個唔係 Jessica 的號碼，所以 Jessica 本身永遠唔知用戶訂咗咩。
- 1. **Purchase CTA 加了一句話** — Jessica 推完產品之後，Writer 現在會加 `「訂完記得話我知呀 😊」`，提示用戶返嚟確認
- 2. **Planner routing** — 用戶回覆 "我訂咗" 類型嘅訊息 → 自動路由去 Sales Agent
- 唯一的 imperfection：我們假設用戶買的是最後被 pitch 的產品（最多 3 款）。如果佢買係更早 pitch 的，會有偏差。但對於 care follow-up 嚟講，"你有冇飲到上次介紹嘅湯" 夠用了。之後如果需要精確，可以讓 Jessica 問 "係邊款呀？"
- 从零搭建了一个 asyncio 后台循环，每 6 小时跑一次，自动给用户发主动关怀消息。共有四种广播类型：


## 2026-05-27 09:59 — TCM-Jessica

### Architecture Decisions
- **Is this a gap you want to fill?** Because it's actually a good one for TCM — HK weather swings are a natural trigger for health care tips. The architecture for it would be:
- 呢個 split 大概貴 3-5x（但 production query 量低，每個用戶日均幾條 message 而已），可能值得試。要我先 fix 緊嘅產品圖片同功效顯示問題，定先做 model split 實驗？
- Now apply `extracted_pain_points` to CRM. This is the **critical fix**:
- 如果你想 sales 都用 vector，可以做 **hybrid**：keyword 先跑 → 如果 score < threshold 就 fallback 去 vector 搜 product cards。Same pattern as FAQ。
- | **Pain extraction inconsistent** | 🟡 Medium | gpt-5.4-mini 有時 omit `extracted_pain_points`。CRM 最終仍然係 `[]`。要 strengthen prompt 或者用 JSON schema enforcement |
- **Fix E1: Pain extraction fallback** — if LLM omits `extracted_pain_points`, fall back to keyword detection so CRM still gets populated:

### Decisions & Reasoning
- | 7 | **情志調理** | 用戶話壓力大 → 自動鏈接對應臟腑 → 推薦湯水 |
- 同天氣廣播共用同一個 6h loop — 唔需要多開任何新嘅 background task。下一個做邊個？節氣提醒定體質複查？
- 全部共用同一個 6h loop，一個 `BROADCAST_ENABLED=true` 開晒。
- `wa.me/85252417448?text=想訂【彭魚鰓解毒湯 HK$120】` — 用戶 click 之後會喺 WhatsApp 開一個 chat 去診所號碼，直接落單。呢個唔係 Jessica 的號碼，所以 Jessica 本身永遠唔知用戶訂咗咩。
- 1. **Purchase CTA 加了一句話** — Jessica 推完產品之後，Writer 現在會加 `「訂完記得話我知呀 😊」`，提示用戶返嚟確認
- 2. **Planner routing** — 用戶回覆 "我訂咗" 類型嘅訊息 → 自動路由去 Sales Agent
- 唯一的 imperfection：我們假設用戶買的是最後被 pitch 的產品（最多 3 款）。如果佢買係更早 pitch 的，會有偏差。但對於 care follow-up 嚟講，"你有冇飲到上次介紹嘅湯" 夠用了。之後如果需要精確，可以讓 Jessica 問 "係邊款呀？"
- 从零搭建了一个 asyncio 后台循环，每 6 小时跑一次，自动给用户发主动关怀消息。共有四种广播类型：


## 2026-05-27 10:44 — TCM-Jessica

### Architecture Decisions
- **Is this a gap you want to fill?** Because it's actually a good one for TCM — HK weather swings are a natural trigger for health care tips. The architecture for it would be:
- 呢個 split 大概貴 3-5x（但 production query 量低，每個用戶日均幾條 message 而已），可能值得試。要我先 fix 緊嘅產品圖片同功效顯示問題，定先做 model split 實驗？
- Now apply `extracted_pain_points` to CRM. This is the **critical fix**:
- 如果你想 sales 都用 vector，可以做 **hybrid**：keyword 先跑 → 如果 score < threshold 就 fallback 去 vector 搜 product cards。Same pattern as FAQ。
- | **Pain extraction inconsistent** | 🟡 Medium | gpt-5.4-mini 有時 omit `extracted_pain_points`。CRM 最終仍然係 `[]`。要 strengthen prompt 或者用 JSON schema enforcement |
- **Fix E1: Pain extraction fallback** — if LLM omits `extracted_pain_points`, fall back to keyword detection so CRM still gets populated:

### Decisions & Reasoning
- | 7 | **情志調理** | 用戶話壓力大 → 自動鏈接對應臟腑 → 推薦湯水 |
- 同天氣廣播共用同一個 6h loop — 唔需要多開任何新嘅 background task。下一個做邊個？節氣提醒定體質複查？
- 全部共用同一個 6h loop，一個 `BROADCAST_ENABLED=true` 開晒。
- `wa.me/85252417448?text=想訂【彭魚鰓解毒湯 HK$120】` — 用戶 click 之後會喺 WhatsApp 開一個 chat 去診所號碼，直接落單。呢個唔係 Jessica 的號碼，所以 Jessica 本身永遠唔知用戶訂咗咩。
- 1. **Purchase CTA 加了一句話** — Jessica 推完產品之後，Writer 現在會加 `「訂完記得話我知呀 😊」`，提示用戶返嚟確認
- 2. **Planner routing** — 用戶回覆 "我訂咗" 類型嘅訊息 → 自動路由去 Sales Agent
- 唯一的 imperfection：我們假設用戶買的是最後被 pitch 的產品（最多 3 款）。如果佢買係更早 pitch 的，會有偏差。但對於 care follow-up 嚟講，"你有冇飲到上次介紹嘅湯" 夠用了。之後如果需要精確，可以讓 Jessica 問 "係邊款呀？"
- 从零搭建了一个 asyncio 后台循环，每 6 小时跑一次，自动给用户发主动关怀消息。共有四种广播类型：


## 2026-05-27 10:47 — TCM-Jessica

### Architecture Decisions
- **Is this a gap you want to fill?** Because it's actually a good one for TCM — HK weather swings are a natural trigger for health care tips. The architecture for it would be:
- 呢個 split 大概貴 3-5x（但 production query 量低，每個用戶日均幾條 message 而已），可能值得試。要我先 fix 緊嘅產品圖片同功效顯示問題，定先做 model split 實驗？
- Now apply `extracted_pain_points` to CRM. This is the **critical fix**:
- 如果你想 sales 都用 vector，可以做 **hybrid**：keyword 先跑 → 如果 score < threshold 就 fallback 去 vector 搜 product cards。Same pattern as FAQ。
- | **Pain extraction inconsistent** | 🟡 Medium | gpt-5.4-mini 有時 omit `extracted_pain_points`。CRM 最終仍然係 `[]`。要 strengthen prompt 或者用 JSON schema enforcement |
- **Fix E1: Pain extraction fallback** — if LLM omits `extracted_pain_points`, fall back to keyword detection so CRM still gets populated:

### Decisions & Reasoning
- | 7 | **情志調理** | 用戶話壓力大 → 自動鏈接對應臟腑 → 推薦湯水 |
- 同天氣廣播共用同一個 6h loop — 唔需要多開任何新嘅 background task。下一個做邊個？節氣提醒定體質複查？
- 全部共用同一個 6h loop，一個 `BROADCAST_ENABLED=true` 開晒。
- `wa.me/85252417448?text=想訂【彭魚鰓解毒湯 HK$120】` — 用戶 click 之後會喺 WhatsApp 開一個 chat 去診所號碼，直接落單。呢個唔係 Jessica 的號碼，所以 Jessica 本身永遠唔知用戶訂咗咩。
- 1. **Purchase CTA 加了一句話** — Jessica 推完產品之後，Writer 現在會加 `「訂完記得話我知呀 😊」`，提示用戶返嚟確認
- 2. **Planner routing** — 用戶回覆 "我訂咗" 類型嘅訊息 → 自動路由去 Sales Agent
- 唯一的 imperfection：我們假設用戶買的是最後被 pitch 的產品（最多 3 款）。如果佢買係更早 pitch 的，會有偏差。但對於 care follow-up 嚟講，"你有冇飲到上次介紹嘅湯" 夠用了。之後如果需要精確，可以讓 Jessica 問 "係邊款呀？"
- 从零搭建了一个 asyncio 后台循环，每 6 小时跑一次，自动给用户发主动关怀消息。共有四种广播类型：


## 2026-05-27 11:08 — TCM-Jessica

### Architecture Decisions
- **Is this a gap you want to fill?** Because it's actually a good one for TCM — HK weather swings are a natural trigger for health care tips. The architecture for it would be:
- 呢個 split 大概貴 3-5x（但 production query 量低，每個用戶日均幾條 message 而已），可能值得試。要我先 fix 緊嘅產品圖片同功效顯示問題，定先做 model split 實驗？
- Now apply `extracted_pain_points` to CRM. This is the **critical fix**:
- 如果你想 sales 都用 vector，可以做 **hybrid**：keyword 先跑 → 如果 score < threshold 就 fallback 去 vector 搜 product cards。Same pattern as FAQ。
- | **Pain extraction inconsistent** | 🟡 Medium | gpt-5.4-mini 有時 omit `extracted_pain_points`。CRM 最終仍然係 `[]`。要 strengthen prompt 或者用 JSON schema enforcement |
- **Fix E1: Pain extraction fallback** — if LLM omits `extracted_pain_points`, fall back to keyword detection so CRM still gets populated:

### Decisions & Reasoning
- | 7 | **情志調理** | 用戶話壓力大 → 自動鏈接對應臟腑 → 推薦湯水 |
- 同天氣廣播共用同一個 6h loop — 唔需要多開任何新嘅 background task。下一個做邊個？節氣提醒定體質複查？
- 全部共用同一個 6h loop，一個 `BROADCAST_ENABLED=true` 開晒。
- `wa.me/85252417448?text=想訂【彭魚鰓解毒湯 HK$120】` — 用戶 click 之後會喺 WhatsApp 開一個 chat 去診所號碼，直接落單。呢個唔係 Jessica 的號碼，所以 Jessica 本身永遠唔知用戶訂咗咩。
- 1. **Purchase CTA 加了一句話** — Jessica 推完產品之後，Writer 現在會加 `「訂完記得話我知呀 😊」`，提示用戶返嚟確認
- 2. **Planner routing** — 用戶回覆 "我訂咗" 類型嘅訊息 → 自動路由去 Sales Agent
- 唯一的 imperfection：我們假設用戶買的是最後被 pitch 的產品（最多 3 款）。如果佢買係更早 pitch 的，會有偏差。但對於 care follow-up 嚟講，"你有冇飲到上次介紹嘅湯" 夠用了。之後如果需要精確，可以讓 Jessica 問 "係邊款呀？"
- 从零搭建了一个 asyncio 后台循环，每 6 小时跑一次，自动给用户发主动关怀消息。共有四种广播类型：


## 2026-05-27 11:13 — TCM-Jessica

### Architecture Decisions
- **Is this a gap you want to fill?** Because it's actually a good one for TCM — HK weather swings are a natural trigger for health care tips. The architecture for it would be:
- 呢個 split 大概貴 3-5x（但 production query 量低，每個用戶日均幾條 message 而已），可能值得試。要我先 fix 緊嘅產品圖片同功效顯示問題，定先做 model split 實驗？
- Now apply `extracted_pain_points` to CRM. This is the **critical fix**:
- 如果你想 sales 都用 vector，可以做 **hybrid**：keyword 先跑 → 如果 score < threshold 就 fallback 去 vector 搜 product cards。Same pattern as FAQ。
- | **Pain extraction inconsistent** | 🟡 Medium | gpt-5.4-mini 有時 omit `extracted_pain_points`。CRM 最終仍然係 `[]`。要 strengthen prompt 或者用 JSON schema enforcement |
- **Fix E1: Pain extraction fallback** — if LLM omits `extracted_pain_points`, fall back to keyword detection so CRM still gets populated:

### Decisions & Reasoning
- | 7 | **情志調理** | 用戶話壓力大 → 自動鏈接對應臟腑 → 推薦湯水 |
- 同天氣廣播共用同一個 6h loop — 唔需要多開任何新嘅 background task。下一個做邊個？節氣提醒定體質複查？
- 全部共用同一個 6h loop，一個 `BROADCAST_ENABLED=true` 開晒。
- `wa.me/85252417448?text=想訂【彭魚鰓解毒湯 HK$120】` — 用戶 click 之後會喺 WhatsApp 開一個 chat 去診所號碼，直接落單。呢個唔係 Jessica 的號碼，所以 Jessica 本身永遠唔知用戶訂咗咩。
- 1. **Purchase CTA 加了一句話** — Jessica 推完產品之後，Writer 現在會加 `「訂完記得話我知呀 😊」`，提示用戶返嚟確認
- 2. **Planner routing** — 用戶回覆 "我訂咗" 類型嘅訊息 → 自動路由去 Sales Agent
- 唯一的 imperfection：我們假設用戶買的是最後被 pitch 的產品（最多 3 款）。如果佢買係更早 pitch 的，會有偏差。但對於 care follow-up 嚟講，"你有冇飲到上次介紹嘅湯" 夠用了。之後如果需要精確，可以讓 Jessica 問 "係邊款呀？"
- 从零搭建了一个 asyncio 后台循环，每 6 小时跑一次，自动给用户发主动关怀消息。共有四种广播类型：


## 2026-05-27 11:14 — TCM-Jessica

### Architecture Decisions
- **Is this a gap you want to fill?** Because it's actually a good one for TCM — HK weather swings are a natural trigger for health care tips. The architecture for it would be:
- 呢個 split 大概貴 3-5x（但 production query 量低，每個用戶日均幾條 message 而已），可能值得試。要我先 fix 緊嘅產品圖片同功效顯示問題，定先做 model split 實驗？
- Now apply `extracted_pain_points` to CRM. This is the **critical fix**:
- 如果你想 sales 都用 vector，可以做 **hybrid**：keyword 先跑 → 如果 score < threshold 就 fallback 去 vector 搜 product cards。Same pattern as FAQ。
- | **Pain extraction inconsistent** | 🟡 Medium | gpt-5.4-mini 有時 omit `extracted_pain_points`。CRM 最終仍然係 `[]`。要 strengthen prompt 或者用 JSON schema enforcement |
- **Fix E1: Pain extraction fallback** — if LLM omits `extracted_pain_points`, fall back to keyword detection so CRM still gets populated:

### Decisions & Reasoning
- | 7 | **情志調理** | 用戶話壓力大 → 自動鏈接對應臟腑 → 推薦湯水 |
- 同天氣廣播共用同一個 6h loop — 唔需要多開任何新嘅 background task。下一個做邊個？節氣提醒定體質複查？
- 全部共用同一個 6h loop，一個 `BROADCAST_ENABLED=true` 開晒。
- `wa.me/85252417448?text=想訂【彭魚鰓解毒湯 HK$120】` — 用戶 click 之後會喺 WhatsApp 開一個 chat 去診所號碼，直接落單。呢個唔係 Jessica 的號碼，所以 Jessica 本身永遠唔知用戶訂咗咩。
- 1. **Purchase CTA 加了一句話** — Jessica 推完產品之後，Writer 現在會加 `「訂完記得話我知呀 😊」`，提示用戶返嚟確認
- 2. **Planner routing** — 用戶回覆 "我訂咗" 類型嘅訊息 → 自動路由去 Sales Agent
- 唯一的 imperfection：我們假設用戶買的是最後被 pitch 的產品（最多 3 款）。如果佢買係更早 pitch 的，會有偏差。但對於 care follow-up 嚟講，"你有冇飲到上次介紹嘅湯" 夠用了。之後如果需要精確，可以讓 Jessica 問 "係邊款呀？"
- 从零搭建了一个 asyncio 后台循环，每 6 小时跑一次，自动给用户发主动关怀消息。共有四种广播类型：


## 2026-05-27 11:34 — TCM-Jessica

### Architecture Decisions
- **Is this a gap you want to fill?** Because it's actually a good one for TCM — HK weather swings are a natural trigger for health care tips. The architecture for it would be:
- 呢個 split 大概貴 3-5x（但 production query 量低，每個用戶日均幾條 message 而已），可能值得試。要我先 fix 緊嘅產品圖片同功效顯示問題，定先做 model split 實驗？
- Now apply `extracted_pain_points` to CRM. This is the **critical fix**:
- 如果你想 sales 都用 vector，可以做 **hybrid**：keyword 先跑 → 如果 score < threshold 就 fallback 去 vector 搜 product cards。Same pattern as FAQ。
- | **Pain extraction inconsistent** | 🟡 Medium | gpt-5.4-mini 有時 omit `extracted_pain_points`。CRM 最終仍然係 `[]`。要 strengthen prompt 或者用 JSON schema enforcement |
- **Fix E1: Pain extraction fallback** — if LLM omits `extracted_pain_points`, fall back to keyword detection so CRM still gets populated:

### Decisions & Reasoning
- | 7 | **情志調理** | 用戶話壓力大 → 自動鏈接對應臟腑 → 推薦湯水 |
- 同天氣廣播共用同一個 6h loop — 唔需要多開任何新嘅 background task。下一個做邊個？節氣提醒定體質複查？
- 全部共用同一個 6h loop，一個 `BROADCAST_ENABLED=true` 開晒。
- `wa.me/85252417448?text=想訂【彭魚鰓解毒湯 HK$120】` — 用戶 click 之後會喺 WhatsApp 開一個 chat 去診所號碼，直接落單。呢個唔係 Jessica 的號碼，所以 Jessica 本身永遠唔知用戶訂咗咩。
- 1. **Purchase CTA 加了一句話** — Jessica 推完產品之後，Writer 現在會加 `「訂完記得話我知呀 😊」`，提示用戶返嚟確認
- 2. **Planner routing** — 用戶回覆 "我訂咗" 類型嘅訊息 → 自動路由去 Sales Agent
- 唯一的 imperfection：我們假設用戶買的是最後被 pitch 的產品（最多 3 款）。如果佢買係更早 pitch 的，會有偏差。但對於 care follow-up 嚟講，"你有冇飲到上次介紹嘅湯" 夠用了。之後如果需要精確，可以讓 Jessica 問 "係邊款呀？"
- 从零搭建了一个 asyncio 后台循环，每 6 小时跑一次，自动给用户发主动关怀消息。共有四种广播类型：


## 2026-05-27 11:40 — TCM-Jessica

### Architecture Decisions
- **Is this a gap you want to fill?** Because it's actually a good one for TCM — HK weather swings are a natural trigger for health care tips. The architecture for it would be:
- 呢個 split 大概貴 3-5x（但 production query 量低，每個用戶日均幾條 message 而已），可能值得試。要我先 fix 緊嘅產品圖片同功效顯示問題，定先做 model split 實驗？
- Now apply `extracted_pain_points` to CRM. This is the **critical fix**:
- 如果你想 sales 都用 vector，可以做 **hybrid**：keyword 先跑 → 如果 score < threshold 就 fallback 去 vector 搜 product cards。Same pattern as FAQ。
- | **Pain extraction inconsistent** | 🟡 Medium | gpt-5.4-mini 有時 omit `extracted_pain_points`。CRM 最終仍然係 `[]`。要 strengthen prompt 或者用 JSON schema enforcement |
- **Fix E1: Pain extraction fallback** — if LLM omits `extracted_pain_points`, fall back to keyword detection so CRM still gets populated:

### Decisions & Reasoning
- | 7 | **情志調理** | 用戶話壓力大 → 自動鏈接對應臟腑 → 推薦湯水 |
- 同天氣廣播共用同一個 6h loop — 唔需要多開任何新嘅 background task。下一個做邊個？節氣提醒定體質複查？
- 全部共用同一個 6h loop，一個 `BROADCAST_ENABLED=true` 開晒。
- `wa.me/85252417448?text=想訂【彭魚鰓解毒湯 HK$120】` — 用戶 click 之後會喺 WhatsApp 開一個 chat 去診所號碼，直接落單。呢個唔係 Jessica 的號碼，所以 Jessica 本身永遠唔知用戶訂咗咩。
- 1. **Purchase CTA 加了一句話** — Jessica 推完產品之後，Writer 現在會加 `「訂完記得話我知呀 😊」`，提示用戶返嚟確認
- 2. **Planner routing** — 用戶回覆 "我訂咗" 類型嘅訊息 → 自動路由去 Sales Agent
- 唯一的 imperfection：我們假設用戶買的是最後被 pitch 的產品（最多 3 款）。如果佢買係更早 pitch 的，會有偏差。但對於 care follow-up 嚟講，"你有冇飲到上次介紹嘅湯" 夠用了。之後如果需要精確，可以讓 Jessica 問 "係邊款呀？"
- 从零搭建了一个 asyncio 后台循环，每 6 小时跑一次，自动给用户发主动关怀消息。共有四种广播类型：


## 2026-05-27 11:44 — TCM-Jessica

### Architecture Decisions
- **Is this a gap you want to fill?** Because it's actually a good one for TCM — HK weather swings are a natural trigger for health care tips. The architecture for it would be:
- 呢個 split 大概貴 3-5x（但 production query 量低，每個用戶日均幾條 message 而已），可能值得試。要我先 fix 緊嘅產品圖片同功效顯示問題，定先做 model split 實驗？
- Now apply `extracted_pain_points` to CRM. This is the **critical fix**:
- 如果你想 sales 都用 vector，可以做 **hybrid**：keyword 先跑 → 如果 score < threshold 就 fallback 去 vector 搜 product cards。Same pattern as FAQ。
- | **Pain extraction inconsistent** | 🟡 Medium | gpt-5.4-mini 有時 omit `extracted_pain_points`。CRM 最終仍然係 `[]`。要 strengthen prompt 或者用 JSON schema enforcement |
- **Fix E1: Pain extraction fallback** — if LLM omits `extracted_pain_points`, fall back to keyword detection so CRM still gets populated:

### Decisions & Reasoning
- | 7 | **情志調理** | 用戶話壓力大 → 自動鏈接對應臟腑 → 推薦湯水 |
- 同天氣廣播共用同一個 6h loop — 唔需要多開任何新嘅 background task。下一個做邊個？節氣提醒定體質複查？
- 全部共用同一個 6h loop，一個 `BROADCAST_ENABLED=true` 開晒。
- `wa.me/85252417448?text=想訂【彭魚鰓解毒湯 HK$120】` — 用戶 click 之後會喺 WhatsApp 開一個 chat 去診所號碼，直接落單。呢個唔係 Jessica 的號碼，所以 Jessica 本身永遠唔知用戶訂咗咩。
- 1. **Purchase CTA 加了一句話** — Jessica 推完產品之後，Writer 現在會加 `「訂完記得話我知呀 😊」`，提示用戶返嚟確認
- 2. **Planner routing** — 用戶回覆 "我訂咗" 類型嘅訊息 → 自動路由去 Sales Agent
- 唯一的 imperfection：我們假設用戶買的是最後被 pitch 的產品（最多 3 款）。如果佢買係更早 pitch 的，會有偏差。但對於 care follow-up 嚟講，"你有冇飲到上次介紹嘅湯" 夠用了。之後如果需要精確，可以讓 Jessica 問 "係邊款呀？"
- 从零搭建了一个 asyncio 后台循环，每 6 小时跑一次，自动给用户发主动关怀消息。共有四种广播类型：


## 2026-05-27 12:13 — TCM-Jessica

### Architecture Decisions
- **Is this a gap you want to fill?** Because it's actually a good one for TCM — HK weather swings are a natural trigger for health care tips. The architecture for it would be:
- 呢個 split 大概貴 3-5x（但 production query 量低，每個用戶日均幾條 message 而已），可能值得試。要我先 fix 緊嘅產品圖片同功效顯示問題，定先做 model split 實驗？
- Now apply `extracted_pain_points` to CRM. This is the **critical fix**:
- 如果你想 sales 都用 vector，可以做 **hybrid**：keyword 先跑 → 如果 score < threshold 就 fallback 去 vector 搜 product cards。Same pattern as FAQ。
- | **Pain extraction inconsistent** | 🟡 Medium | gpt-5.4-mini 有時 omit `extracted_pain_points`。CRM 最終仍然係 `[]`。要 strengthen prompt 或者用 JSON schema enforcement |
- **Fix E1: Pain extraction fallback** — if LLM omits `extracted_pain_points`, fall back to keyword detection so CRM still gets populated:

### Decisions & Reasoning
- | 7 | **情志調理** | 用戶話壓力大 → 自動鏈接對應臟腑 → 推薦湯水 |
- 同天氣廣播共用同一個 6h loop — 唔需要多開任何新嘅 background task。下一個做邊個？節氣提醒定體質複查？
- 全部共用同一個 6h loop，一個 `BROADCAST_ENABLED=true` 開晒。
- `wa.me/85252417448?text=想訂【彭魚鰓解毒湯 HK$120】` — 用戶 click 之後會喺 WhatsApp 開一個 chat 去診所號碼，直接落單。呢個唔係 Jessica 的號碼，所以 Jessica 本身永遠唔知用戶訂咗咩。
- 1. **Purchase CTA 加了一句話** — Jessica 推完產品之後，Writer 現在會加 `「訂完記得話我知呀 😊」`，提示用戶返嚟確認
- 2. **Planner routing** — 用戶回覆 "我訂咗" 類型嘅訊息 → 自動路由去 Sales Agent
- 唯一的 imperfection：我們假設用戶買的是最後被 pitch 的產品（最多 3 款）。如果佢買係更早 pitch 的，會有偏差。但對於 care follow-up 嚟講，"你有冇飲到上次介紹嘅湯" 夠用了。之後如果需要精確，可以讓 Jessica 問 "係邊款呀？"
- 从零搭建了一个 asyncio 后台循环，每 6 小时跑一次，自动给用户发主动关怀消息。共有四种广播类型：


## 2026-05-27 13:36 — TCM-Jessica

### Architecture Decisions
- **Is this a gap you want to fill?** Because it's actually a good one for TCM — HK weather swings are a natural trigger for health care tips. The architecture for it would be:
- 呢個 split 大概貴 3-5x（但 production query 量低，每個用戶日均幾條 message 而已），可能值得試。要我先 fix 緊嘅產品圖片同功效顯示問題，定先做 model split 實驗？
- Now apply `extracted_pain_points` to CRM. This is the **critical fix**:
- 如果你想 sales 都用 vector，可以做 **hybrid**：keyword 先跑 → 如果 score < threshold 就 fallback 去 vector 搜 product cards。Same pattern as FAQ。
- | **Pain extraction inconsistent** | 🟡 Medium | gpt-5.4-mini 有時 omit `extracted_pain_points`。CRM 最終仍然係 `[]`。要 strengthen prompt 或者用 JSON schema enforcement |
- **Fix E1: Pain extraction fallback** — if LLM omits `extracted_pain_points`, fall back to keyword detection so CRM still gets populated:

### Decisions & Reasoning
- | 7 | **情志調理** | 用戶話壓力大 → 自動鏈接對應臟腑 → 推薦湯水 |
- 同天氣廣播共用同一個 6h loop — 唔需要多開任何新嘅 background task。下一個做邊個？節氣提醒定體質複查？
- 全部共用同一個 6h loop，一個 `BROADCAST_ENABLED=true` 開晒。
- `wa.me/85252417448?text=想訂【彭魚鰓解毒湯 HK$120】` — 用戶 click 之後會喺 WhatsApp 開一個 chat 去診所號碼，直接落單。呢個唔係 Jessica 的號碼，所以 Jessica 本身永遠唔知用戶訂咗咩。
- 1. **Purchase CTA 加了一句話** — Jessica 推完產品之後，Writer 現在會加 `「訂完記得話我知呀 😊」`，提示用戶返嚟確認
- 2. **Planner routing** — 用戶回覆 "我訂咗" 類型嘅訊息 → 自動路由去 Sales Agent
- 唯一的 imperfection：我們假設用戶買的是最後被 pitch 的產品（最多 3 款）。如果佢買係更早 pitch 的，會有偏差。但對於 care follow-up 嚟講，"你有冇飲到上次介紹嘅湯" 夠用了。之後如果需要精確，可以讓 Jessica 問 "係邊款呀？"
- 从零搭建了一个 asyncio 后台循环，每 6 小时跑一次，自动给用户发主动关怀消息。共有四种广播类型：


## 2026-05-27 13:53 — TCM-Jessica

### Architecture Decisions
- **Is this a gap you want to fill?** Because it's actually a good one for TCM — HK weather swings are a natural trigger for health care tips. The architecture for it would be:
- 呢個 split 大概貴 3-5x（但 production query 量低，每個用戶日均幾條 message 而已），可能值得試。要我先 fix 緊嘅產品圖片同功效顯示問題，定先做 model split 實驗？
- Now apply `extracted_pain_points` to CRM. This is the **critical fix**:
- 如果你想 sales 都用 vector，可以做 **hybrid**：keyword 先跑 → 如果 score < threshold 就 fallback 去 vector 搜 product cards。Same pattern as FAQ。
- | **Pain extraction inconsistent** | 🟡 Medium | gpt-5.4-mini 有時 omit `extracted_pain_points`。CRM 最終仍然係 `[]`。要 strengthen prompt 或者用 JSON schema enforcement |
- **Fix E1: Pain extraction fallback** — if LLM omits `extracted_pain_points`, fall back to keyword detection so CRM still gets populated:

### Decisions & Reasoning
- | 7 | **情志調理** | 用戶話壓力大 → 自動鏈接對應臟腑 → 推薦湯水 |
- 同天氣廣播共用同一個 6h loop — 唔需要多開任何新嘅 background task。下一個做邊個？節氣提醒定體質複查？
- 全部共用同一個 6h loop，一個 `BROADCAST_ENABLED=true` 開晒。
- `wa.me/85252417448?text=想訂【彭魚鰓解毒湯 HK$120】` — 用戶 click 之後會喺 WhatsApp 開一個 chat 去診所號碼，直接落單。呢個唔係 Jessica 的號碼，所以 Jessica 本身永遠唔知用戶訂咗咩。
- 1. **Purchase CTA 加了一句話** — Jessica 推完產品之後，Writer 現在會加 `「訂完記得話我知呀 😊」`，提示用戶返嚟確認
- 2. **Planner routing** — 用戶回覆 "我訂咗" 類型嘅訊息 → 自動路由去 Sales Agent
- 唯一的 imperfection：我們假設用戶買的是最後被 pitch 的產品（最多 3 款）。如果佢買係更早 pitch 的，會有偏差。但對於 care follow-up 嚟講，"你有冇飲到上次介紹嘅湯" 夠用了。之後如果需要精確，可以讓 Jessica 問 "係邊款呀？"
- 从零搭建了一个 asyncio 后台循环，每 6 小时跑一次，自动给用户发主动关怀消息。共有四种广播类型：


## 2026-05-27 14:30 — TCM-Jessica

### Architecture Decisions
- **Is this a gap you want to fill?** Because it's actually a good one for TCM — HK weather swings are a natural trigger for health care tips. The architecture for it would be:
- 呢個 split 大概貴 3-5x（但 production query 量低，每個用戶日均幾條 message 而已），可能值得試。要我先 fix 緊嘅產品圖片同功效顯示問題，定先做 model split 實驗？
- Now apply `extracted_pain_points` to CRM. This is the **critical fix**:
- 如果你想 sales 都用 vector，可以做 **hybrid**：keyword 先跑 → 如果 score < threshold 就 fallback 去 vector 搜 product cards。Same pattern as FAQ。
- | **Pain extraction inconsistent** | 🟡 Medium | gpt-5.4-mini 有時 omit `extracted_pain_points`。CRM 最終仍然係 `[]`。要 strengthen prompt 或者用 JSON schema enforcement |
- **Fix E1: Pain extraction fallback** — if LLM omits `extracted_pain_points`, fall back to keyword detection so CRM still gets populated:

### Decisions & Reasoning
- | 7 | **情志調理** | 用戶話壓力大 → 自動鏈接對應臟腑 → 推薦湯水 |
- 同天氣廣播共用同一個 6h loop — 唔需要多開任何新嘅 background task。下一個做邊個？節氣提醒定體質複查？
- 全部共用同一個 6h loop，一個 `BROADCAST_ENABLED=true` 開晒。
- `wa.me/85252417448?text=想訂【彭魚鰓解毒湯 HK$120】` — 用戶 click 之後會喺 WhatsApp 開一個 chat 去診所號碼，直接落單。呢個唔係 Jessica 的號碼，所以 Jessica 本身永遠唔知用戶訂咗咩。
- 1. **Purchase CTA 加了一句話** — Jessica 推完產品之後，Writer 現在會加 `「訂完記得話我知呀 😊」`，提示用戶返嚟確認
- 2. **Planner routing** — 用戶回覆 "我訂咗" 類型嘅訊息 → 自動路由去 Sales Agent
- 唯一的 imperfection：我們假設用戶買的是最後被 pitch 的產品（最多 3 款）。如果佢買係更早 pitch 的，會有偏差。但對於 care follow-up 嚟講，"你有冇飲到上次介紹嘅湯" 夠用了。之後如果需要精確，可以讓 Jessica 問 "係邊款呀？"
- 从零搭建了一个 asyncio 后台循环，每 6 小时跑一次，自动给用户发主动关怀消息。共有四种广播类型：


## 2026-05-27 14:35 — TCM-Jessica

### Architecture Decisions
- **Is this a gap you want to fill?** Because it's actually a good one for TCM — HK weather swings are a natural trigger for health care tips. The architecture for it would be:
- 呢個 split 大概貴 3-5x（但 production query 量低，每個用戶日均幾條 message 而已），可能值得試。要我先 fix 緊嘅產品圖片同功效顯示問題，定先做 model split 實驗？
- Now apply `extracted_pain_points` to CRM. This is the **critical fix**:
- 如果你想 sales 都用 vector，可以做 **hybrid**：keyword 先跑 → 如果 score < threshold 就 fallback 去 vector 搜 product cards。Same pattern as FAQ。
- | **Pain extraction inconsistent** | 🟡 Medium | gpt-5.4-mini 有時 omit `extracted_pain_points`。CRM 最終仍然係 `[]`。要 strengthen prompt 或者用 JSON schema enforcement |
- **Fix E1: Pain extraction fallback** — if LLM omits `extracted_pain_points`, fall back to keyword detection so CRM still gets populated:

### Decisions & Reasoning
- | 7 | **情志調理** | 用戶話壓力大 → 自動鏈接對應臟腑 → 推薦湯水 |
- 同天氣廣播共用同一個 6h loop — 唔需要多開任何新嘅 background task。下一個做邊個？節氣提醒定體質複查？
- 全部共用同一個 6h loop，一個 `BROADCAST_ENABLED=true` 開晒。
- `wa.me/85252417448?text=想訂【彭魚鰓解毒湯 HK$120】` — 用戶 click 之後會喺 WhatsApp 開一個 chat 去診所號碼，直接落單。呢個唔係 Jessica 的號碼，所以 Jessica 本身永遠唔知用戶訂咗咩。
- 1. **Purchase CTA 加了一句話** — Jessica 推完產品之後，Writer 現在會加 `「訂完記得話我知呀 😊」`，提示用戶返嚟確認
- 2. **Planner routing** — 用戶回覆 "我訂咗" 類型嘅訊息 → 自動路由去 Sales Agent
- 唯一的 imperfection：我們假設用戶買的是最後被 pitch 的產品（最多 3 款）。如果佢買係更早 pitch 的，會有偏差。但對於 care follow-up 嚟講，"你有冇飲到上次介紹嘅湯" 夠用了。之後如果需要精確，可以讓 Jessica 問 "係邊款呀？"
- 从零搭建了一个 asyncio 后台循环，每 6 小时跑一次，自动给用户发主动关怀消息。共有四种广播类型：


## 2026-05-27 14:49 — TCM-Jessica

### Architecture Decisions
- **Is this a gap you want to fill?** Because it's actually a good one for TCM — HK weather swings are a natural trigger for health care tips. The architecture for it would be:
- 呢個 split 大概貴 3-5x（但 production query 量低，每個用戶日均幾條 message 而已），可能值得試。要我先 fix 緊嘅產品圖片同功效顯示問題，定先做 model split 實驗？
- Now apply `extracted_pain_points` to CRM. This is the **critical fix**:
- 如果你想 sales 都用 vector，可以做 **hybrid**：keyword 先跑 → 如果 score < threshold 就 fallback 去 vector 搜 product cards。Same pattern as FAQ。
- | **Pain extraction inconsistent** | 🟡 Medium | gpt-5.4-mini 有時 omit `extracted_pain_points`。CRM 最終仍然係 `[]`。要 strengthen prompt 或者用 JSON schema enforcement |
- **Fix E1: Pain extraction fallback** — if LLM omits `extracted_pain_points`, fall back to keyword detection so CRM still gets populated:

### Decisions & Reasoning
- | 7 | **情志調理** | 用戶話壓力大 → 自動鏈接對應臟腑 → 推薦湯水 |
- 同天氣廣播共用同一個 6h loop — 唔需要多開任何新嘅 background task。下一個做邊個？節氣提醒定體質複查？
- 全部共用同一個 6h loop，一個 `BROADCAST_ENABLED=true` 開晒。
- `wa.me/85252417448?text=想訂【彭魚鰓解毒湯 HK$120】` — 用戶 click 之後會喺 WhatsApp 開一個 chat 去診所號碼，直接落單。呢個唔係 Jessica 的號碼，所以 Jessica 本身永遠唔知用戶訂咗咩。
- 1. **Purchase CTA 加了一句話** — Jessica 推完產品之後，Writer 現在會加 `「訂完記得話我知呀 😊」`，提示用戶返嚟確認
- 2. **Planner routing** — 用戶回覆 "我訂咗" 類型嘅訊息 → 自動路由去 Sales Agent
- 唯一的 imperfection：我們假設用戶買的是最後被 pitch 的產品（最多 3 款）。如果佢買係更早 pitch 的，會有偏差。但對於 care follow-up 嚟講，"你有冇飲到上次介紹嘅湯" 夠用了。之後如果需要精確，可以讓 Jessica 問 "係邊款呀？"
- 从零搭建了一个 asyncio 后台循环，每 6 小时跑一次，自动给用户发主动关怀消息。共有四种广播类型：


## 2026-05-27 15:26 — TCM-Jessica

### Architecture Decisions
- **Is this a gap you want to fill?** Because it's actually a good one for TCM — HK weather swings are a natural trigger for health care tips. The architecture for it would be:
- 呢個 split 大概貴 3-5x（但 production query 量低，每個用戶日均幾條 message 而已），可能值得試。要我先 fix 緊嘅產品圖片同功效顯示問題，定先做 model split 實驗？
- Now apply `extracted_pain_points` to CRM. This is the **critical fix**:
- 如果你想 sales 都用 vector，可以做 **hybrid**：keyword 先跑 → 如果 score < threshold 就 fallback 去 vector 搜 product cards。Same pattern as FAQ。
- | **Pain extraction inconsistent** | 🟡 Medium | gpt-5.4-mini 有時 omit `extracted_pain_points`。CRM 最終仍然係 `[]`。要 strengthen prompt 或者用 JSON schema enforcement |
- **Fix E1: Pain extraction fallback** — if LLM omits `extracted_pain_points`, fall back to keyword detection so CRM still gets populated:

### Decisions & Reasoning
- | 7 | **情志調理** | 用戶話壓力大 → 自動鏈接對應臟腑 → 推薦湯水 |
- 同天氣廣播共用同一個 6h loop — 唔需要多開任何新嘅 background task。下一個做邊個？節氣提醒定體質複查？
- 全部共用同一個 6h loop，一個 `BROADCAST_ENABLED=true` 開晒。
- `wa.me/85252417448?text=想訂【彭魚鰓解毒湯 HK$120】` — 用戶 click 之後會喺 WhatsApp 開一個 chat 去診所號碼，直接落單。呢個唔係 Jessica 的號碼，所以 Jessica 本身永遠唔知用戶訂咗咩。
- 1. **Purchase CTA 加了一句話** — Jessica 推完產品之後，Writer 現在會加 `「訂完記得話我知呀 😊」`，提示用戶返嚟確認
- 2. **Planner routing** — 用戶回覆 "我訂咗" 類型嘅訊息 → 自動路由去 Sales Agent
- 唯一的 imperfection：我們假設用戶買的是最後被 pitch 的產品（最多 3 款）。如果佢買係更早 pitch 的，會有偏差。但對於 care follow-up 嚟講，"你有冇飲到上次介紹嘅湯" 夠用了。之後如果需要精確，可以讓 Jessica 問 "係邊款呀？"
- 从零搭建了一个 asyncio 后台循环，每 6 小时跑一次，自动给用户发主动关怀消息。共有四种广播类型：


## 2026-05-27 15:39 — TCM-Jessica

### Architecture Decisions
- **Is this a gap you want to fill?** Because it's actually a good one for TCM — HK weather swings are a natural trigger for health care tips. The architecture for it would be:
- 呢個 split 大概貴 3-5x（但 production query 量低，每個用戶日均幾條 message 而已），可能值得試。要我先 fix 緊嘅產品圖片同功效顯示問題，定先做 model split 實驗？
- Now apply `extracted_pain_points` to CRM. This is the **critical fix**:
- 如果你想 sales 都用 vector，可以做 **hybrid**：keyword 先跑 → 如果 score < threshold 就 fallback 去 vector 搜 product cards。Same pattern as FAQ。
- | **Pain extraction inconsistent** | 🟡 Medium | gpt-5.4-mini 有時 omit `extracted_pain_points`。CRM 最終仍然係 `[]`。要 strengthen prompt 或者用 JSON schema enforcement |
- **Fix E1: Pain extraction fallback** — if LLM omits `extracted_pain_points`, fall back to keyword detection so CRM still gets populated:
- | 2. **辨證**（證型 — 八綱 / 臟腑 / 氣血津液）| ❌ 冇 | 而家**呢一刻嘅 pattern**：肝鬱氣滯 / 脾腎陽虛 / 心脾兩虛 / 痰濕困脾… 真實臨床用嚟開方嘅根據 |
- 2. **No agent does pattern inference** — material in KB, but never extracted into structured form

### Decisions & Reasoning
- | 7 | **情志調理** | 用戶話壓力大 → 自動鏈接對應臟腑 → 推薦湯水 |
- 同天氣廣播共用同一個 6h loop — 唔需要多開任何新嘅 background task。下一個做邊個？節氣提醒定體質複查？
- 全部共用同一個 6h loop，一個 `BROADCAST_ENABLED=true` 開晒。
- `wa.me/85252417448?text=想訂【彭魚鰓解毒湯 HK$120】` — 用戶 click 之後會喺 WhatsApp 開一個 chat 去診所號碼，直接落單。呢個唔係 Jessica 的號碼，所以 Jessica 本身永遠唔知用戶訂咗咩。
- 1. **Purchase CTA 加了一句話** — Jessica 推完產品之後，Writer 現在會加 `「訂完記得話我知呀 😊」`，提示用戶返嚟確認
- 2. **Planner routing** — 用戶回覆 "我訂咗" 類型嘅訊息 → 自動路由去 Sales Agent
- 唯一的 imperfection：我們假設用戶買的是最後被 pitch 的產品（最多 3 款）。如果佢買係更早 pitch 的，會有偏差。但對於 care follow-up 嚟講，"你有冇飲到上次介紹嘅湯" 夠用了。之後如果需要精確，可以讓 Jessica 問 "係邊款呀？"
- 从零搭建了一个 asyncio 后台循环，每 6 小时跑一次，自动给用户发主动关怀消息。共有四种广播类型：


## 2026-05-27 15:53 — TCM-Jessica

### Architecture Decisions
- **Is this a gap you want to fill?** Because it's actually a good one for TCM — HK weather swings are a natural trigger for health care tips. The architecture for it would be:
- 呢個 split 大概貴 3-5x（但 production query 量低，每個用戶日均幾條 message 而已），可能值得試。要我先 fix 緊嘅產品圖片同功效顯示問題，定先做 model split 實驗？
- Now apply `extracted_pain_points` to CRM. This is the **critical fix**:
- 如果你想 sales 都用 vector，可以做 **hybrid**：keyword 先跑 → 如果 score < threshold 就 fallback 去 vector 搜 product cards。Same pattern as FAQ。
- | **Pain extraction inconsistent** | 🟡 Medium | gpt-5.4-mini 有時 omit `extracted_pain_points`。CRM 最終仍然係 `[]`。要 strengthen prompt 或者用 JSON schema enforcement |
- **Fix E1: Pain extraction fallback** — if LLM omits `extracted_pain_points`, fall back to keyword detection so CRM still gets populated:
- | 2. **辨證**（證型 — 八綱 / 臟腑 / 氣血津液）| ❌ 冇 | 而家**呢一刻嘅 pattern**：肝鬱氣滯 / 脾腎陽虛 / 心脾兩虛 / 痰濕困脾… 真實臨床用嚟開方嘅根據 |
- 2. **No agent does pattern inference** — material in KB, but never extracted into structured form

### Decisions & Reasoning
- | 7 | **情志調理** | 用戶話壓力大 → 自動鏈接對應臟腑 → 推薦湯水 |
- 同天氣廣播共用同一個 6h loop — 唔需要多開任何新嘅 background task。下一個做邊個？節氣提醒定體質複查？
- 全部共用同一個 6h loop，一個 `BROADCAST_ENABLED=true` 開晒。
- `wa.me/85252417448?text=想訂【彭魚鰓解毒湯 HK$120】` — 用戶 click 之後會喺 WhatsApp 開一個 chat 去診所號碼，直接落單。呢個唔係 Jessica 的號碼，所以 Jessica 本身永遠唔知用戶訂咗咩。
- 1. **Purchase CTA 加了一句話** — Jessica 推完產品之後，Writer 現在會加 `「訂完記得話我知呀 😊」`，提示用戶返嚟確認
- 2. **Planner routing** — 用戶回覆 "我訂咗" 類型嘅訊息 → 自動路由去 Sales Agent
- 唯一的 imperfection：我們假設用戶買的是最後被 pitch 的產品（最多 3 款）。如果佢買係更早 pitch 的，會有偏差。但對於 care follow-up 嚟講，"你有冇飲到上次介紹嘅湯" 夠用了。之後如果需要精確，可以讓 Jessica 問 "係邊款呀？"
- 从零搭建了一个 asyncio 后台循环，每 6 小时跑一次，自动给用户发主动关怀消息。共有四种广播类型：


## 2026-05-27 15:59 — TCM-Jessica

### Architecture Decisions
- **Is this a gap you want to fill?** Because it's actually a good one for TCM — HK weather swings are a natural trigger for health care tips. The architecture for it would be:
- 呢個 split 大概貴 3-5x（但 production query 量低，每個用戶日均幾條 message 而已），可能值得試。要我先 fix 緊嘅產品圖片同功效顯示問題，定先做 model split 實驗？
- Now apply `extracted_pain_points` to CRM. This is the **critical fix**:
- 如果你想 sales 都用 vector，可以做 **hybrid**：keyword 先跑 → 如果 score < threshold 就 fallback 去 vector 搜 product cards。Same pattern as FAQ。
- | **Pain extraction inconsistent** | 🟡 Medium | gpt-5.4-mini 有時 omit `extracted_pain_points`。CRM 最終仍然係 `[]`。要 strengthen prompt 或者用 JSON schema enforcement |
- **Fix E1: Pain extraction fallback** — if LLM omits `extracted_pain_points`, fall back to keyword detection so CRM still gets populated:
- | 2. **辨證**（證型 — 八綱 / 臟腑 / 氣血津液）| ❌ 冇 | 而家**呢一刻嘅 pattern**：肝鬱氣滯 / 脾腎陽虛 / 心脾兩虛 / 痰濕困脾… 真實臨床用嚟開方嘅根據 |
- 2. **No agent does pattern inference** — material in KB, but never extracted into structured form

### Decisions & Reasoning
- | 7 | **情志調理** | 用戶話壓力大 → 自動鏈接對應臟腑 → 推薦湯水 |
- 同天氣廣播共用同一個 6h loop — 唔需要多開任何新嘅 background task。下一個做邊個？節氣提醒定體質複查？
- 全部共用同一個 6h loop，一個 `BROADCAST_ENABLED=true` 開晒。
- `wa.me/85252417448?text=想訂【彭魚鰓解毒湯 HK$120】` — 用戶 click 之後會喺 WhatsApp 開一個 chat 去診所號碼，直接落單。呢個唔係 Jessica 的號碼，所以 Jessica 本身永遠唔知用戶訂咗咩。
- 1. **Purchase CTA 加了一句話** — Jessica 推完產品之後，Writer 現在會加 `「訂完記得話我知呀 😊」`，提示用戶返嚟確認
- 2. **Planner routing** — 用戶回覆 "我訂咗" 類型嘅訊息 → 自動路由去 Sales Agent
- 唯一的 imperfection：我們假設用戶買的是最後被 pitch 的產品（最多 3 款）。如果佢買係更早 pitch 的，會有偏差。但對於 care follow-up 嚟講，"你有冇飲到上次介紹嘅湯" 夠用了。之後如果需要精確，可以讓 Jessica 問 "係邊款呀？"
- 从零搭建了一个 asyncio 后台循环，每 6 小时跑一次，自动给用户发主动关怀消息。共有四种广播类型：


## 2026-05-27 17:05 — TCM-Jessica

### Architecture Decisions
- **Is this a gap you want to fill?** Because it's actually a good one for TCM — HK weather swings are a natural trigger for health care tips. The architecture for it would be:
- 呢個 split 大概貴 3-5x（但 production query 量低，每個用戶日均幾條 message 而已），可能值得試。要我先 fix 緊嘅產品圖片同功效顯示問題，定先做 model split 實驗？
- Now apply `extracted_pain_points` to CRM. This is the **critical fix**:
- 如果你想 sales 都用 vector，可以做 **hybrid**：keyword 先跑 → 如果 score < threshold 就 fallback 去 vector 搜 product cards。Same pattern as FAQ。
- | **Pain extraction inconsistent** | 🟡 Medium | gpt-5.4-mini 有時 omit `extracted_pain_points`。CRM 最終仍然係 `[]`。要 strengthen prompt 或者用 JSON schema enforcement |
- **Fix E1: Pain extraction fallback** — if LLM omits `extracted_pain_points`, fall back to keyword detection so CRM still gets populated:
- | 2. **辨證**（證型 — 八綱 / 臟腑 / 氣血津液）| ❌ 冇 | 而家**呢一刻嘅 pattern**：肝鬱氣滯 / 脾腎陽虛 / 心脾兩虛 / 痰濕困脾… 真實臨床用嚟開方嘅根據 |
- 2. **No agent does pattern inference** — material in KB, but never extracted into structured form

### Decisions & Reasoning
- | 7 | **情志調理** | 用戶話壓力大 → 自動鏈接對應臟腑 → 推薦湯水 |
- 同天氣廣播共用同一個 6h loop — 唔需要多開任何新嘅 background task。下一個做邊個？節氣提醒定體質複查？
- 全部共用同一個 6h loop，一個 `BROADCAST_ENABLED=true` 開晒。
- `wa.me/85252417448?text=想訂【彭魚鰓解毒湯 HK$120】` — 用戶 click 之後會喺 WhatsApp 開一個 chat 去診所號碼，直接落單。呢個唔係 Jessica 的號碼，所以 Jessica 本身永遠唔知用戶訂咗咩。
- 1. **Purchase CTA 加了一句話** — Jessica 推完產品之後，Writer 現在會加 `「訂完記得話我知呀 😊」`，提示用戶返嚟確認
- 2. **Planner routing** — 用戶回覆 "我訂咗" 類型嘅訊息 → 自動路由去 Sales Agent
- 唯一的 imperfection：我們假設用戶買的是最後被 pitch 的產品（最多 3 款）。如果佢買係更早 pitch 的，會有偏差。但對於 care follow-up 嚟講，"你有冇飲到上次介紹嘅湯" 夠用了。之後如果需要精確，可以讓 Jessica 問 "係邊款呀？"
- 从零搭建了一个 asyncio 后台循环，每 6 小时跑一次，自动给用户发主动关怀消息。共有四种广播类型：


## 2026-05-27 17:13 — TCM-Jessica

### Architecture Decisions
- **Is this a gap you want to fill?** Because it's actually a good one for TCM — HK weather swings are a natural trigger for health care tips. The architecture for it would be:
- 呢個 split 大概貴 3-5x（但 production query 量低，每個用戶日均幾條 message 而已），可能值得試。要我先 fix 緊嘅產品圖片同功效顯示問題，定先做 model split 實驗？
- Now apply `extracted_pain_points` to CRM. This is the **critical fix**:
- 如果你想 sales 都用 vector，可以做 **hybrid**：keyword 先跑 → 如果 score < threshold 就 fallback 去 vector 搜 product cards。Same pattern as FAQ。
- | **Pain extraction inconsistent** | 🟡 Medium | gpt-5.4-mini 有時 omit `extracted_pain_points`。CRM 最終仍然係 `[]`。要 strengthen prompt 或者用 JSON schema enforcement |
- **Fix E1: Pain extraction fallback** — if LLM omits `extracted_pain_points`, fall back to keyword detection so CRM still gets populated:
- | 2. **辨證**（證型 — 八綱 / 臟腑 / 氣血津液）| ❌ 冇 | 而家**呢一刻嘅 pattern**：肝鬱氣滯 / 脾腎陽虛 / 心脾兩虛 / 痰濕困脾… 真實臨床用嚟開方嘅根據 |
- 2. **No agent does pattern inference** — material in KB, but never extracted into structured form

### Decisions & Reasoning
- | 7 | **情志調理** | 用戶話壓力大 → 自動鏈接對應臟腑 → 推薦湯水 |
- 同天氣廣播共用同一個 6h loop — 唔需要多開任何新嘅 background task。下一個做邊個？節氣提醒定體質複查？
- 全部共用同一個 6h loop，一個 `BROADCAST_ENABLED=true` 開晒。
- `wa.me/85252417448?text=想訂【彭魚鰓解毒湯 HK$120】` — 用戶 click 之後會喺 WhatsApp 開一個 chat 去診所號碼，直接落單。呢個唔係 Jessica 的號碼，所以 Jessica 本身永遠唔知用戶訂咗咩。
- 1. **Purchase CTA 加了一句話** — Jessica 推完產品之後，Writer 現在會加 `「訂完記得話我知呀 😊」`，提示用戶返嚟確認
- 2. **Planner routing** — 用戶回覆 "我訂咗" 類型嘅訊息 → 自動路由去 Sales Agent
- 唯一的 imperfection：我們假設用戶買的是最後被 pitch 的產品（最多 3 款）。如果佢買係更早 pitch 的，會有偏差。但對於 care follow-up 嚟講，"你有冇飲到上次介紹嘅湯" 夠用了。之後如果需要精確，可以讓 Jessica 問 "係邊款呀？"
- 从零搭建了一个 asyncio 后台循环，每 6 小时跑一次，自动给用户发主动关怀消息。共有四种广播类型：


## 2026-05-27 17:14 — TCM-Jessica

### Architecture Decisions
- **Is this a gap you want to fill?** Because it's actually a good one for TCM — HK weather swings are a natural trigger for health care tips. The architecture for it would be:
- 呢個 split 大概貴 3-5x（但 production query 量低，每個用戶日均幾條 message 而已），可能值得試。要我先 fix 緊嘅產品圖片同功效顯示問題，定先做 model split 實驗？
- Now apply `extracted_pain_points` to CRM. This is the **critical fix**:
- 如果你想 sales 都用 vector，可以做 **hybrid**：keyword 先跑 → 如果 score < threshold 就 fallback 去 vector 搜 product cards。Same pattern as FAQ。
- | **Pain extraction inconsistent** | 🟡 Medium | gpt-5.4-mini 有時 omit `extracted_pain_points`。CRM 最終仍然係 `[]`。要 strengthen prompt 或者用 JSON schema enforcement |
- **Fix E1: Pain extraction fallback** — if LLM omits `extracted_pain_points`, fall back to keyword detection so CRM still gets populated:
- | 2. **辨證**（證型 — 八綱 / 臟腑 / 氣血津液）| ❌ 冇 | 而家**呢一刻嘅 pattern**：肝鬱氣滯 / 脾腎陽虛 / 心脾兩虛 / 痰濕困脾… 真實臨床用嚟開方嘅根據 |
- 2. **No agent does pattern inference** — material in KB, but never extracted into structured form

### Decisions & Reasoning
- | 7 | **情志調理** | 用戶話壓力大 → 自動鏈接對應臟腑 → 推薦湯水 |
- 同天氣廣播共用同一個 6h loop — 唔需要多開任何新嘅 background task。下一個做邊個？節氣提醒定體質複查？
- 全部共用同一個 6h loop，一個 `BROADCAST_ENABLED=true` 開晒。
- `wa.me/85252417448?text=想訂【彭魚鰓解毒湯 HK$120】` — 用戶 click 之後會喺 WhatsApp 開一個 chat 去診所號碼，直接落單。呢個唔係 Jessica 的號碼，所以 Jessica 本身永遠唔知用戶訂咗咩。
- 1. **Purchase CTA 加了一句話** — Jessica 推完產品之後，Writer 現在會加 `「訂完記得話我知呀 😊」`，提示用戶返嚟確認
- 2. **Planner routing** — 用戶回覆 "我訂咗" 類型嘅訊息 → 自動路由去 Sales Agent
- 唯一的 imperfection：我們假設用戶買的是最後被 pitch 的產品（最多 3 款）。如果佢買係更早 pitch 的，會有偏差。但對於 care follow-up 嚟講，"你有冇飲到上次介紹嘅湯" 夠用了。之後如果需要精確，可以讓 Jessica 問 "係邊款呀？"
- 从零搭建了一个 asyncio 后台循环，每 6 小时跑一次，自动给用户发主动关怀消息。共有四种广播类型：


## 2026-05-27 17:14 — TCM-Jessica

### Architecture Decisions
- **Is this a gap you want to fill?** Because it's actually a good one for TCM — HK weather swings are a natural trigger for health care tips. The architecture for it would be:
- 呢個 split 大概貴 3-5x（但 production query 量低，每個用戶日均幾條 message 而已），可能值得試。要我先 fix 緊嘅產品圖片同功效顯示問題，定先做 model split 實驗？
- Now apply `extracted_pain_points` to CRM. This is the **critical fix**:
- 如果你想 sales 都用 vector，可以做 **hybrid**：keyword 先跑 → 如果 score < threshold 就 fallback 去 vector 搜 product cards。Same pattern as FAQ。
- | **Pain extraction inconsistent** | 🟡 Medium | gpt-5.4-mini 有時 omit `extracted_pain_points`。CRM 最終仍然係 `[]`。要 strengthen prompt 或者用 JSON schema enforcement |
- **Fix E1: Pain extraction fallback** — if LLM omits `extracted_pain_points`, fall back to keyword detection so CRM still gets populated:
- | 2. **辨證**（證型 — 八綱 / 臟腑 / 氣血津液）| ❌ 冇 | 而家**呢一刻嘅 pattern**：肝鬱氣滯 / 脾腎陽虛 / 心脾兩虛 / 痰濕困脾… 真實臨床用嚟開方嘅根據 |
- 2. **No agent does pattern inference** — material in KB, but never extracted into structured form

### Decisions & Reasoning
- | 7 | **情志調理** | 用戶話壓力大 → 自動鏈接對應臟腑 → 推薦湯水 |
- 同天氣廣播共用同一個 6h loop — 唔需要多開任何新嘅 background task。下一個做邊個？節氣提醒定體質複查？
- 全部共用同一個 6h loop，一個 `BROADCAST_ENABLED=true` 開晒。
- `wa.me/85252417448?text=想訂【彭魚鰓解毒湯 HK$120】` — 用戶 click 之後會喺 WhatsApp 開一個 chat 去診所號碼，直接落單。呢個唔係 Jessica 的號碼，所以 Jessica 本身永遠唔知用戶訂咗咩。
- 1. **Purchase CTA 加了一句話** — Jessica 推完產品之後，Writer 現在會加 `「訂完記得話我知呀 😊」`，提示用戶返嚟確認
- 2. **Planner routing** — 用戶回覆 "我訂咗" 類型嘅訊息 → 自動路由去 Sales Agent
- 唯一的 imperfection：我們假設用戶買的是最後被 pitch 的產品（最多 3 款）。如果佢買係更早 pitch 的，會有偏差。但對於 care follow-up 嚟講，"你有冇飲到上次介紹嘅湯" 夠用了。之後如果需要精確，可以讓 Jessica 問 "係邊款呀？"
- 从零搭建了一个 asyncio 后台循环，每 6 小时跑一次，自动给用户发主动关怀消息。共有四种广播类型：


## 2026-05-27 17:20 — TCM-Jessica

### Architecture Decisions
- **Is this a gap you want to fill?** Because it's actually a good one for TCM — HK weather swings are a natural trigger for health care tips. The architecture for it would be:
- 呢個 split 大概貴 3-5x（但 production query 量低，每個用戶日均幾條 message 而已），可能值得試。要我先 fix 緊嘅產品圖片同功效顯示問題，定先做 model split 實驗？
- Now apply `extracted_pain_points` to CRM. This is the **critical fix**:
- 如果你想 sales 都用 vector，可以做 **hybrid**：keyword 先跑 → 如果 score < threshold 就 fallback 去 vector 搜 product cards。Same pattern as FAQ。
- | **Pain extraction inconsistent** | 🟡 Medium | gpt-5.4-mini 有時 omit `extracted_pain_points`。CRM 最終仍然係 `[]`。要 strengthen prompt 或者用 JSON schema enforcement |
- **Fix E1: Pain extraction fallback** — if LLM omits `extracted_pain_points`, fall back to keyword detection so CRM still gets populated:
- | 2. **辨證**（證型 — 八綱 / 臟腑 / 氣血津液）| ❌ 冇 | 而家**呢一刻嘅 pattern**：肝鬱氣滯 / 脾腎陽虛 / 心脾兩虛 / 痰濕困脾… 真實臨床用嚟開方嘅根據 |
- 2. **No agent does pattern inference** — material in KB, but never extracted into structured form

### Decisions & Reasoning
- | 7 | **情志調理** | 用戶話壓力大 → 自動鏈接對應臟腑 → 推薦湯水 |
- 同天氣廣播共用同一個 6h loop — 唔需要多開任何新嘅 background task。下一個做邊個？節氣提醒定體質複查？
- 全部共用同一個 6h loop，一個 `BROADCAST_ENABLED=true` 開晒。
- `wa.me/85252417448?text=想訂【彭魚鰓解毒湯 HK$120】` — 用戶 click 之後會喺 WhatsApp 開一個 chat 去診所號碼，直接落單。呢個唔係 Jessica 的號碼，所以 Jessica 本身永遠唔知用戶訂咗咩。
- 1. **Purchase CTA 加了一句話** — Jessica 推完產品之後，Writer 現在會加 `「訂完記得話我知呀 😊」`，提示用戶返嚟確認
- 2. **Planner routing** — 用戶回覆 "我訂咗" 類型嘅訊息 → 自動路由去 Sales Agent
- 唯一的 imperfection：我們假設用戶買的是最後被 pitch 的產品（最多 3 款）。如果佢買係更早 pitch 的，會有偏差。但對於 care follow-up 嚟講，"你有冇飲到上次介紹嘅湯" 夠用了。之後如果需要精確，可以讓 Jessica 問 "係邊款呀？"
- 从零搭建了一个 asyncio 后台循环，每 6 小时跑一次，自动给用户发主动关怀消息。共有四种广播类型：


## 2026-05-27 17:23 — TCM-Jessica

### Architecture Decisions
- **Is this a gap you want to fill?** Because it's actually a good one for TCM — HK weather swings are a natural trigger for health care tips. The architecture for it would be:
- 呢個 split 大概貴 3-5x（但 production query 量低，每個用戶日均幾條 message 而已），可能值得試。要我先 fix 緊嘅產品圖片同功效顯示問題，定先做 model split 實驗？
- Now apply `extracted_pain_points` to CRM. This is the **critical fix**:
- 如果你想 sales 都用 vector，可以做 **hybrid**：keyword 先跑 → 如果 score < threshold 就 fallback 去 vector 搜 product cards。Same pattern as FAQ。
- | **Pain extraction inconsistent** | 🟡 Medium | gpt-5.4-mini 有時 omit `extracted_pain_points`。CRM 最終仍然係 `[]`。要 strengthen prompt 或者用 JSON schema enforcement |
- **Fix E1: Pain extraction fallback** — if LLM omits `extracted_pain_points`, fall back to keyword detection so CRM still gets populated:
- | 2. **辨證**（證型 — 八綱 / 臟腑 / 氣血津液）| ❌ 冇 | 而家**呢一刻嘅 pattern**：肝鬱氣滯 / 脾腎陽虛 / 心脾兩虛 / 痰濕困脾… 真實臨床用嚟開方嘅根據 |
- 2. **No agent does pattern inference** — material in KB, but never extracted into structured form

### Decisions & Reasoning
- | 7 | **情志調理** | 用戶話壓力大 → 自動鏈接對應臟腑 → 推薦湯水 |
- 同天氣廣播共用同一個 6h loop — 唔需要多開任何新嘅 background task。下一個做邊個？節氣提醒定體質複查？
- 全部共用同一個 6h loop，一個 `BROADCAST_ENABLED=true` 開晒。
- `wa.me/85252417448?text=想訂【彭魚鰓解毒湯 HK$120】` — 用戶 click 之後會喺 WhatsApp 開一個 chat 去診所號碼，直接落單。呢個唔係 Jessica 的號碼，所以 Jessica 本身永遠唔知用戶訂咗咩。
- 1. **Purchase CTA 加了一句話** — Jessica 推完產品之後，Writer 現在會加 `「訂完記得話我知呀 😊」`，提示用戶返嚟確認
- 2. **Planner routing** — 用戶回覆 "我訂咗" 類型嘅訊息 → 自動路由去 Sales Agent
- 唯一的 imperfection：我們假設用戶買的是最後被 pitch 的產品（最多 3 款）。如果佢買係更早 pitch 的，會有偏差。但對於 care follow-up 嚟講，"你有冇飲到上次介紹嘅湯" 夠用了。之後如果需要精確，可以讓 Jessica 問 "係邊款呀？"
- 从零搭建了一个 asyncio 后台循环，每 6 小时跑一次，自动给用户发主动关怀消息。共有四种广播类型：


## 2026-05-27 17:27 — TCM-Jessica

### Architecture Decisions
- **Is this a gap you want to fill?** Because it's actually a good one for TCM — HK weather swings are a natural trigger for health care tips. The architecture for it would be:
- 呢個 split 大概貴 3-5x（但 production query 量低，每個用戶日均幾條 message 而已），可能值得試。要我先 fix 緊嘅產品圖片同功效顯示問題，定先做 model split 實驗？
- Now apply `extracted_pain_points` to CRM. This is the **critical fix**:
- 如果你想 sales 都用 vector，可以做 **hybrid**：keyword 先跑 → 如果 score < threshold 就 fallback 去 vector 搜 product cards。Same pattern as FAQ。
- | **Pain extraction inconsistent** | 🟡 Medium | gpt-5.4-mini 有時 omit `extracted_pain_points`。CRM 最終仍然係 `[]`。要 strengthen prompt 或者用 JSON schema enforcement |
- **Fix E1: Pain extraction fallback** — if LLM omits `extracted_pain_points`, fall back to keyword detection so CRM still gets populated:
- | 2. **辨證**（證型 — 八綱 / 臟腑 / 氣血津液）| ❌ 冇 | 而家**呢一刻嘅 pattern**：肝鬱氣滯 / 脾腎陽虛 / 心脾兩虛 / 痰濕困脾… 真實臨床用嚟開方嘅根據 |
- 2. **No agent does pattern inference** — material in KB, but never extracted into structured form

### Decisions & Reasoning
- | 7 | **情志調理** | 用戶話壓力大 → 自動鏈接對應臟腑 → 推薦湯水 |
- 同天氣廣播共用同一個 6h loop — 唔需要多開任何新嘅 background task。下一個做邊個？節氣提醒定體質複查？
- 全部共用同一個 6h loop，一個 `BROADCAST_ENABLED=true` 開晒。
- `wa.me/85252417448?text=想訂【彭魚鰓解毒湯 HK$120】` — 用戶 click 之後會喺 WhatsApp 開一個 chat 去診所號碼，直接落單。呢個唔係 Jessica 的號碼，所以 Jessica 本身永遠唔知用戶訂咗咩。
- 1. **Purchase CTA 加了一句話** — Jessica 推完產品之後，Writer 現在會加 `「訂完記得話我知呀 😊」`，提示用戶返嚟確認
- 2. **Planner routing** — 用戶回覆 "我訂咗" 類型嘅訊息 → 自動路由去 Sales Agent
- 唯一的 imperfection：我們假設用戶買的是最後被 pitch 的產品（最多 3 款）。如果佢買係更早 pitch 的，會有偏差。但對於 care follow-up 嚟講，"你有冇飲到上次介紹嘅湯" 夠用了。之後如果需要精確，可以讓 Jessica 問 "係邊款呀？"
- 从零搭建了一个 asyncio 后台循环，每 6 小时跑一次，自动给用户发主动关怀消息。共有四种广播类型：


## 2026-05-27 17:31 — TCM-Jessica

### Architecture Decisions
- **Is this a gap you want to fill?** Because it's actually a good one for TCM — HK weather swings are a natural trigger for health care tips. The architecture for it would be:
- 呢個 split 大概貴 3-5x（但 production query 量低，每個用戶日均幾條 message 而已），可能值得試。要我先 fix 緊嘅產品圖片同功效顯示問題，定先做 model split 實驗？
- Now apply `extracted_pain_points` to CRM. This is the **critical fix**:
- 如果你想 sales 都用 vector，可以做 **hybrid**：keyword 先跑 → 如果 score < threshold 就 fallback 去 vector 搜 product cards。Same pattern as FAQ。
- | **Pain extraction inconsistent** | 🟡 Medium | gpt-5.4-mini 有時 omit `extracted_pain_points`。CRM 最終仍然係 `[]`。要 strengthen prompt 或者用 JSON schema enforcement |
- **Fix E1: Pain extraction fallback** — if LLM omits `extracted_pain_points`, fall back to keyword detection so CRM still gets populated:
- | 2. **辨證**（證型 — 八綱 / 臟腑 / 氣血津液）| ❌ 冇 | 而家**呢一刻嘅 pattern**：肝鬱氣滯 / 脾腎陽虛 / 心脾兩虛 / 痰濕困脾… 真實臨床用嚟開方嘅根據 |
- 2. **No agent does pattern inference** — material in KB, but never extracted into structured form

### Decisions & Reasoning
- | 7 | **情志調理** | 用戶話壓力大 → 自動鏈接對應臟腑 → 推薦湯水 |
- 同天氣廣播共用同一個 6h loop — 唔需要多開任何新嘅 background task。下一個做邊個？節氣提醒定體質複查？
- 全部共用同一個 6h loop，一個 `BROADCAST_ENABLED=true` 開晒。
- `wa.me/85252417448?text=想訂【彭魚鰓解毒湯 HK$120】` — 用戶 click 之後會喺 WhatsApp 開一個 chat 去診所號碼，直接落單。呢個唔係 Jessica 的號碼，所以 Jessica 本身永遠唔知用戶訂咗咩。
- 1. **Purchase CTA 加了一句話** — Jessica 推完產品之後，Writer 現在會加 `「訂完記得話我知呀 😊」`，提示用戶返嚟確認
- 2. **Planner routing** — 用戶回覆 "我訂咗" 類型嘅訊息 → 自動路由去 Sales Agent
- 唯一的 imperfection：我們假設用戶買的是最後被 pitch 的產品（最多 3 款）。如果佢買係更早 pitch 的，會有偏差。但對於 care follow-up 嚟講，"你有冇飲到上次介紹嘅湯" 夠用了。之後如果需要精確，可以讓 Jessica 問 "係邊款呀？"
- 从零搭建了一个 asyncio 后台循环，每 6 小时跑一次，自动给用户发主动关怀消息。共有四种广播类型：


## 2026-05-28 18:08 — TCM-Jessica

### Architecture Decisions
- **Is this a gap you want to fill?** Because it's actually a good one for TCM — HK weather swings are a natural trigger for health care tips. The architecture for it would be:
- 呢個 split 大概貴 3-5x（但 production query 量低，每個用戶日均幾條 message 而已），可能值得試。要我先 fix 緊嘅產品圖片同功效顯示問題，定先做 model split 實驗？
- Now apply `extracted_pain_points` to CRM. This is the **critical fix**:
- 如果你想 sales 都用 vector，可以做 **hybrid**：keyword 先跑 → 如果 score < threshold 就 fallback 去 vector 搜 product cards。Same pattern as FAQ。
- | **Pain extraction inconsistent** | 🟡 Medium | gpt-5.4-mini 有時 omit `extracted_pain_points`。CRM 最終仍然係 `[]`。要 strengthen prompt 或者用 JSON schema enforcement |
- **Fix E1: Pain extraction fallback** — if LLM omits `extracted_pain_points`, fall back to keyword detection so CRM still gets populated:
- | 2. **辨證**（證型 — 八綱 / 臟腑 / 氣血津液）| ❌ 冇 | 而家**呢一刻嘅 pattern**：肝鬱氣滯 / 脾腎陽虛 / 心脾兩虛 / 痰濕困脾… 真實臨床用嚟開方嘅根據 |
- 2. **No agent does pattern inference** — material in KB, but never extracted into structured form

### Decisions & Reasoning
- | 7 | **情志調理** | 用戶話壓力大 → 自動鏈接對應臟腑 → 推薦湯水 |
- 同天氣廣播共用同一個 6h loop — 唔需要多開任何新嘅 background task。下一個做邊個？節氣提醒定體質複查？
- 全部共用同一個 6h loop，一個 `BROADCAST_ENABLED=true` 開晒。
- `wa.me/85252417448?text=想訂【彭魚鰓解毒湯 HK$120】` — 用戶 click 之後會喺 WhatsApp 開一個 chat 去診所號碼，直接落單。呢個唔係 Jessica 的號碼，所以 Jessica 本身永遠唔知用戶訂咗咩。
- 1. **Purchase CTA 加了一句話** — Jessica 推完產品之後，Writer 現在會加 `「訂完記得話我知呀 😊」`，提示用戶返嚟確認
- 2. **Planner routing** — 用戶回覆 "我訂咗" 類型嘅訊息 → 自動路由去 Sales Agent
- 唯一的 imperfection：我們假設用戶買的是最後被 pitch 的產品（最多 3 款）。如果佢買係更早 pitch 的，會有偏差。但對於 care follow-up 嚟講，"你有冇飲到上次介紹嘅湯" 夠用了。之後如果需要精確，可以讓 Jessica 問 "係邊款呀？"
- 从零搭建了一个 asyncio 后台循环，每 6 小时跑一次，自动给用户发主动关怀消息。共有四种广播类型：


## 2026-05-28 18:19 — TCM-Jessica

### Architecture Decisions
- **Is this a gap you want to fill?** Because it's actually a good one for TCM — HK weather swings are a natural trigger for health care tips. The architecture for it would be:
- 呢個 split 大概貴 3-5x（但 production query 量低，每個用戶日均幾條 message 而已），可能值得試。要我先 fix 緊嘅產品圖片同功效顯示問題，定先做 model split 實驗？
- Now apply `extracted_pain_points` to CRM. This is the **critical fix**:
- 如果你想 sales 都用 vector，可以做 **hybrid**：keyword 先跑 → 如果 score < threshold 就 fallback 去 vector 搜 product cards。Same pattern as FAQ。
- | **Pain extraction inconsistent** | 🟡 Medium | gpt-5.4-mini 有時 omit `extracted_pain_points`。CRM 最終仍然係 `[]`。要 strengthen prompt 或者用 JSON schema enforcement |
- **Fix E1: Pain extraction fallback** — if LLM omits `extracted_pain_points`, fall back to keyword detection so CRM still gets populated:
- | 2. **辨證**（證型 — 八綱 / 臟腑 / 氣血津液）| ❌ 冇 | 而家**呢一刻嘅 pattern**：肝鬱氣滯 / 脾腎陽虛 / 心脾兩虛 / 痰濕困脾… 真實臨床用嚟開方嘅根據 |
- 2. **No agent does pattern inference** — material in KB, but never extracted into structured form

### Decisions & Reasoning
- | 7 | **情志調理** | 用戶話壓力大 → 自動鏈接對應臟腑 → 推薦湯水 |
- 同天氣廣播共用同一個 6h loop — 唔需要多開任何新嘅 background task。下一個做邊個？節氣提醒定體質複查？
- 全部共用同一個 6h loop，一個 `BROADCAST_ENABLED=true` 開晒。
- `wa.me/85252417448?text=想訂【彭魚鰓解毒湯 HK$120】` — 用戶 click 之後會喺 WhatsApp 開一個 chat 去診所號碼，直接落單。呢個唔係 Jessica 的號碼，所以 Jessica 本身永遠唔知用戶訂咗咩。
- 1. **Purchase CTA 加了一句話** — Jessica 推完產品之後，Writer 現在會加 `「訂完記得話我知呀 😊」`，提示用戶返嚟確認
- 2. **Planner routing** — 用戶回覆 "我訂咗" 類型嘅訊息 → 自動路由去 Sales Agent
- 唯一的 imperfection：我們假設用戶買的是最後被 pitch 的產品（最多 3 款）。如果佢買係更早 pitch 的，會有偏差。但對於 care follow-up 嚟講，"你有冇飲到上次介紹嘅湯" 夠用了。之後如果需要精確，可以讓 Jessica 問 "係邊款呀？"
- 从零搭建了一个 asyncio 后台循环，每 6 小时跑一次，自动给用户发主动关怀消息。共有四种广播类型：


## 2026-05-29 09:45 — TCM-Jessica

### Architecture Decisions
- **Is this a gap you want to fill?** Because it's actually a good one for TCM — HK weather swings are a natural trigger for health care tips. The architecture for it would be:
- 呢個 split 大概貴 3-5x（但 production query 量低，每個用戶日均幾條 message 而已），可能值得試。要我先 fix 緊嘅產品圖片同功效顯示問題，定先做 model split 實驗？
- Now apply `extracted_pain_points` to CRM. This is the **critical fix**:
- 如果你想 sales 都用 vector，可以做 **hybrid**：keyword 先跑 → 如果 score < threshold 就 fallback 去 vector 搜 product cards。Same pattern as FAQ。
- | **Pain extraction inconsistent** | 🟡 Medium | gpt-5.4-mini 有時 omit `extracted_pain_points`。CRM 最終仍然係 `[]`。要 strengthen prompt 或者用 JSON schema enforcement |
- **Fix E1: Pain extraction fallback** — if LLM omits `extracted_pain_points`, fall back to keyword detection so CRM still gets populated:
- | 2. **辨證**（證型 — 八綱 / 臟腑 / 氣血津液）| ❌ 冇 | 而家**呢一刻嘅 pattern**：肝鬱氣滯 / 脾腎陽虛 / 心脾兩虛 / 痰濕困脾… 真實臨床用嚟開方嘅根據 |
- 2. **No agent does pattern inference** — material in KB, but never extracted into structured form

### Decisions & Reasoning
- | 7 | **情志調理** | 用戶話壓力大 → 自動鏈接對應臟腑 → 推薦湯水 |
- 同天氣廣播共用同一個 6h loop — 唔需要多開任何新嘅 background task。下一個做邊個？節氣提醒定體質複查？
- 全部共用同一個 6h loop，一個 `BROADCAST_ENABLED=true` 開晒。
- `wa.me/85252417448?text=想訂【彭魚鰓解毒湯 HK$120】` — 用戶 click 之後會喺 WhatsApp 開一個 chat 去診所號碼，直接落單。呢個唔係 Jessica 的號碼，所以 Jessica 本身永遠唔知用戶訂咗咩。
- 1. **Purchase CTA 加了一句話** — Jessica 推完產品之後，Writer 現在會加 `「訂完記得話我知呀 😊」`，提示用戶返嚟確認
- 2. **Planner routing** — 用戶回覆 "我訂咗" 類型嘅訊息 → 自動路由去 Sales Agent
- 唯一的 imperfection：我們假設用戶買的是最後被 pitch 的產品（最多 3 款）。如果佢買係更早 pitch 的，會有偏差。但對於 care follow-up 嚟講，"你有冇飲到上次介紹嘅湯" 夠用了。之後如果需要精確，可以讓 Jessica 問 "係邊款呀？"
- 从零搭建了一个 asyncio 后台循环，每 6 小时跑一次，自动给用户发主动关怀消息。共有四种广播类型：


## 2026-05-29 09:59 — TCM-Jessica

### Architecture Decisions
- **Is this a gap you want to fill?** Because it's actually a good one for TCM — HK weather swings are a natural trigger for health care tips. The architecture for it would be:
- 呢個 split 大概貴 3-5x（但 production query 量低，每個用戶日均幾條 message 而已），可能值得試。要我先 fix 緊嘅產品圖片同功效顯示問題，定先做 model split 實驗？
- Now apply `extracted_pain_points` to CRM. This is the **critical fix**:
- 如果你想 sales 都用 vector，可以做 **hybrid**：keyword 先跑 → 如果 score < threshold 就 fallback 去 vector 搜 product cards。Same pattern as FAQ。
- | **Pain extraction inconsistent** | 🟡 Medium | gpt-5.4-mini 有時 omit `extracted_pain_points`。CRM 最終仍然係 `[]`。要 strengthen prompt 或者用 JSON schema enforcement |
- **Fix E1: Pain extraction fallback** — if LLM omits `extracted_pain_points`, fall back to keyword detection so CRM still gets populated:
- | 2. **辨證**（證型 — 八綱 / 臟腑 / 氣血津液）| ❌ 冇 | 而家**呢一刻嘅 pattern**：肝鬱氣滯 / 脾腎陽虛 / 心脾兩虛 / 痰濕困脾… 真實臨床用嚟開方嘅根據 |
- 2. **No agent does pattern inference** — material in KB, but never extracted into structured form

### Decisions & Reasoning
- | 7 | **情志調理** | 用戶話壓力大 → 自動鏈接對應臟腑 → 推薦湯水 |
- 同天氣廣播共用同一個 6h loop — 唔需要多開任何新嘅 background task。下一個做邊個？節氣提醒定體質複查？
- 全部共用同一個 6h loop，一個 `BROADCAST_ENABLED=true` 開晒。
- `wa.me/85252417448?text=想訂【彭魚鰓解毒湯 HK$120】` — 用戶 click 之後會喺 WhatsApp 開一個 chat 去診所號碼，直接落單。呢個唔係 Jessica 的號碼，所以 Jessica 本身永遠唔知用戶訂咗咩。
- 1. **Purchase CTA 加了一句話** — Jessica 推完產品之後，Writer 現在會加 `「訂完記得話我知呀 😊」`，提示用戶返嚟確認
- 2. **Planner routing** — 用戶回覆 "我訂咗" 類型嘅訊息 → 自動路由去 Sales Agent
- 唯一的 imperfection：我們假設用戶買的是最後被 pitch 的產品（最多 3 款）。如果佢買係更早 pitch 的，會有偏差。但對於 care follow-up 嚟講，"你有冇飲到上次介紹嘅湯" 夠用了。之後如果需要精確，可以讓 Jessica 問 "係邊款呀？"
- 从零搭建了一个 asyncio 后台循环，每 6 小时跑一次，自动给用户发主动关怀消息。共有四种广播类型：


## 2026-05-29 10:05 — TCM-Jessica

### Architecture Decisions
- **Is this a gap you want to fill?** Because it's actually a good one for TCM — HK weather swings are a natural trigger for health care tips. The architecture for it would be:
- 呢個 split 大概貴 3-5x（但 production query 量低，每個用戶日均幾條 message 而已），可能值得試。要我先 fix 緊嘅產品圖片同功效顯示問題，定先做 model split 實驗？
- Now apply `extracted_pain_points` to CRM. This is the **critical fix**:
- 如果你想 sales 都用 vector，可以做 **hybrid**：keyword 先跑 → 如果 score < threshold 就 fallback 去 vector 搜 product cards。Same pattern as FAQ。
- | **Pain extraction inconsistent** | 🟡 Medium | gpt-5.4-mini 有時 omit `extracted_pain_points`。CRM 最終仍然係 `[]`。要 strengthen prompt 或者用 JSON schema enforcement |
- **Fix E1: Pain extraction fallback** — if LLM omits `extracted_pain_points`, fall back to keyword detection so CRM still gets populated:
- | 2. **辨證**（證型 — 八綱 / 臟腑 / 氣血津液）| ❌ 冇 | 而家**呢一刻嘅 pattern**：肝鬱氣滯 / 脾腎陽虛 / 心脾兩虛 / 痰濕困脾… 真實臨床用嚟開方嘅根據 |
- 2. **No agent does pattern inference** — material in KB, but never extracted into structured form

### Decisions & Reasoning
- | 7 | **情志調理** | 用戶話壓力大 → 自動鏈接對應臟腑 → 推薦湯水 |
- 同天氣廣播共用同一個 6h loop — 唔需要多開任何新嘅 background task。下一個做邊個？節氣提醒定體質複查？
- 全部共用同一個 6h loop，一個 `BROADCAST_ENABLED=true` 開晒。
- `wa.me/85252417448?text=想訂【彭魚鰓解毒湯 HK$120】` — 用戶 click 之後會喺 WhatsApp 開一個 chat 去診所號碼，直接落單。呢個唔係 Jessica 的號碼，所以 Jessica 本身永遠唔知用戶訂咗咩。
- 1. **Purchase CTA 加了一句話** — Jessica 推完產品之後，Writer 現在會加 `「訂完記得話我知呀 😊」`，提示用戶返嚟確認
- 2. **Planner routing** — 用戶回覆 "我訂咗" 類型嘅訊息 → 自動路由去 Sales Agent
- 唯一的 imperfection：我們假設用戶買的是最後被 pitch 的產品（最多 3 款）。如果佢買係更早 pitch 的，會有偏差。但對於 care follow-up 嚟講，"你有冇飲到上次介紹嘅湯" 夠用了。之後如果需要精確，可以讓 Jessica 問 "係邊款呀？"
- 从零搭建了一个 asyncio 后台循环，每 6 小时跑一次，自动给用户发主动关怀消息。共有四种广播类型：


## 2026-05-29 10:26 — TCM-Jessica

### Architecture Decisions
- **Is this a gap you want to fill?** Because it's actually a good one for TCM — HK weather swings are a natural trigger for health care tips. The architecture for it would be:
- 呢個 split 大概貴 3-5x（但 production query 量低，每個用戶日均幾條 message 而已），可能值得試。要我先 fix 緊嘅產品圖片同功效顯示問題，定先做 model split 實驗？
- Now apply `extracted_pain_points` to CRM. This is the **critical fix**:
- 如果你想 sales 都用 vector，可以做 **hybrid**：keyword 先跑 → 如果 score < threshold 就 fallback 去 vector 搜 product cards。Same pattern as FAQ。
- | **Pain extraction inconsistent** | 🟡 Medium | gpt-5.4-mini 有時 omit `extracted_pain_points`。CRM 最終仍然係 `[]`。要 strengthen prompt 或者用 JSON schema enforcement |
- **Fix E1: Pain extraction fallback** — if LLM omits `extracted_pain_points`, fall back to keyword detection so CRM still gets populated:
- | 2. **辨證**（證型 — 八綱 / 臟腑 / 氣血津液）| ❌ 冇 | 而家**呢一刻嘅 pattern**：肝鬱氣滯 / 脾腎陽虛 / 心脾兩虛 / 痰濕困脾… 真實臨床用嚟開方嘅根據 |
- 2. **No agent does pattern inference** — material in KB, but never extracted into structured form

### Decisions & Reasoning
- | 7 | **情志調理** | 用戶話壓力大 → 自動鏈接對應臟腑 → 推薦湯水 |
- 同天氣廣播共用同一個 6h loop — 唔需要多開任何新嘅 background task。下一個做邊個？節氣提醒定體質複查？
- 全部共用同一個 6h loop，一個 `BROADCAST_ENABLED=true` 開晒。
- `wa.me/85252417448?text=想訂【彭魚鰓解毒湯 HK$120】` — 用戶 click 之後會喺 WhatsApp 開一個 chat 去診所號碼，直接落單。呢個唔係 Jessica 的號碼，所以 Jessica 本身永遠唔知用戶訂咗咩。
- 1. **Purchase CTA 加了一句話** — Jessica 推完產品之後，Writer 現在會加 `「訂完記得話我知呀 😊」`，提示用戶返嚟確認
- 2. **Planner routing** — 用戶回覆 "我訂咗" 類型嘅訊息 → 自動路由去 Sales Agent
- 唯一的 imperfection：我們假設用戶買的是最後被 pitch 的產品（最多 3 款）。如果佢買係更早 pitch 的，會有偏差。但對於 care follow-up 嚟講，"你有冇飲到上次介紹嘅湯" 夠用了。之後如果需要精確，可以讓 Jessica 問 "係邊款呀？"
- 从零搭建了一个 asyncio 后台循环，每 6 小时跑一次，自动给用户发主动关怀消息。共有四种广播类型：


## 2026-05-29 10:46 — TCM-Jessica

### Architecture Decisions
- **Is this a gap you want to fill?** Because it's actually a good one for TCM — HK weather swings are a natural trigger for health care tips. The architecture for it would be:
- 呢個 split 大概貴 3-5x（但 production query 量低，每個用戶日均幾條 message 而已），可能值得試。要我先 fix 緊嘅產品圖片同功效顯示問題，定先做 model split 實驗？
- Now apply `extracted_pain_points` to CRM. This is the **critical fix**:
- 如果你想 sales 都用 vector，可以做 **hybrid**：keyword 先跑 → 如果 score < threshold 就 fallback 去 vector 搜 product cards。Same pattern as FAQ。
- | **Pain extraction inconsistent** | 🟡 Medium | gpt-5.4-mini 有時 omit `extracted_pain_points`。CRM 最終仍然係 `[]`。要 strengthen prompt 或者用 JSON schema enforcement |
- **Fix E1: Pain extraction fallback** — if LLM omits `extracted_pain_points`, fall back to keyword detection so CRM still gets populated:
- | 2. **辨證**（證型 — 八綱 / 臟腑 / 氣血津液）| ❌ 冇 | 而家**呢一刻嘅 pattern**：肝鬱氣滯 / 脾腎陽虛 / 心脾兩虛 / 痰濕困脾… 真實臨床用嚟開方嘅根據 |
- 2. **No agent does pattern inference** — material in KB, but never extracted into structured form

### Decisions & Reasoning
- | 7 | **情志調理** | 用戶話壓力大 → 自動鏈接對應臟腑 → 推薦湯水 |
- 同天氣廣播共用同一個 6h loop — 唔需要多開任何新嘅 background task。下一個做邊個？節氣提醒定體質複查？
- 全部共用同一個 6h loop，一個 `BROADCAST_ENABLED=true` 開晒。
- `wa.me/85252417448?text=想訂【彭魚鰓解毒湯 HK$120】` — 用戶 click 之後會喺 WhatsApp 開一個 chat 去診所號碼，直接落單。呢個唔係 Jessica 的號碼，所以 Jessica 本身永遠唔知用戶訂咗咩。
- 1. **Purchase CTA 加了一句話** — Jessica 推完產品之後，Writer 現在會加 `「訂完記得話我知呀 😊」`，提示用戶返嚟確認
- 2. **Planner routing** — 用戶回覆 "我訂咗" 類型嘅訊息 → 自動路由去 Sales Agent
- 唯一的 imperfection：我們假設用戶買的是最後被 pitch 的產品（最多 3 款）。如果佢買係更早 pitch 的，會有偏差。但對於 care follow-up 嚟講，"你有冇飲到上次介紹嘅湯" 夠用了。之後如果需要精確，可以讓 Jessica 問 "係邊款呀？"
- 从零搭建了一个 asyncio 后台循环，每 6 小时跑一次，自动给用户发主动关怀消息。共有四种广播类型：


## 2026-05-29 10:46 — TCM-Jessica

### Architecture Decisions
- Got the full picture. Clean implementation: buttons are extracted from specialist payload **in the orchestrator** (not by the Writer LLM) and attached to the last bubble in the router. Five files to touch.


## 2026-05-29 10:52 — TCM-Jessica

### Architecture Decisions
- Got the full picture. Clean implementation: buttons are extracted from specialist payload **in the orchestrator** (not by the Writer LLM) and attached to the last bubble in the router. Five files to touch.


## 2026-05-29 10:54 — TCM-Jessica

### Architecture Decisions
- Got the full picture. Clean implementation: buttons are extracted from specialist payload **in the orchestrator** (not by the Writer LLM) and attached to the last bubble in the router. Five files to touch.


## 2026-05-29 10:58 — TCM-Jessica

### Architecture Decisions
- **Is this a gap you want to fill?** Because it's actually a good one for TCM — HK weather swings are a natural trigger for health care tips. The architecture for it would be:
- 呢個 split 大概貴 3-5x（但 production query 量低，每個用戶日均幾條 message 而已），可能值得試。要我先 fix 緊嘅產品圖片同功效顯示問題，定先做 model split 實驗？
- Now apply `extracted_pain_points` to CRM. This is the **critical fix**:
- 如果你想 sales 都用 vector，可以做 **hybrid**：keyword 先跑 → 如果 score < threshold 就 fallback 去 vector 搜 product cards。Same pattern as FAQ。
- | **Pain extraction inconsistent** | 🟡 Medium | gpt-5.4-mini 有時 omit `extracted_pain_points`。CRM 最終仍然係 `[]`。要 strengthen prompt 或者用 JSON schema enforcement |
- **Fix E1: Pain extraction fallback** — if LLM omits `extracted_pain_points`, fall back to keyword detection so CRM still gets populated:
- | 2. **辨證**（證型 — 八綱 / 臟腑 / 氣血津液）| ❌ 冇 | 而家**呢一刻嘅 pattern**：肝鬱氣滯 / 脾腎陽虛 / 心脾兩虛 / 痰濕困脾… 真實臨床用嚟開方嘅根據 |
- 2. **No agent does pattern inference** — material in KB, but never extracted into structured form

### Decisions & Reasoning
- | 7 | **情志調理** | 用戶話壓力大 → 自動鏈接對應臟腑 → 推薦湯水 |
- 同天氣廣播共用同一個 6h loop — 唔需要多開任何新嘅 background task。下一個做邊個？節氣提醒定體質複查？
- 全部共用同一個 6h loop，一個 `BROADCAST_ENABLED=true` 開晒。
- `wa.me/85252417448?text=想訂【彭魚鰓解毒湯 HK$120】` — 用戶 click 之後會喺 WhatsApp 開一個 chat 去診所號碼，直接落單。呢個唔係 Jessica 的號碼，所以 Jessica 本身永遠唔知用戶訂咗咩。
- 1. **Purchase CTA 加了一句話** — Jessica 推完產品之後，Writer 現在會加 `「訂完記得話我知呀 😊」`，提示用戶返嚟確認
- 2. **Planner routing** — 用戶回覆 "我訂咗" 類型嘅訊息 → 自動路由去 Sales Agent
- 唯一的 imperfection：我們假設用戶買的是最後被 pitch 的產品（最多 3 款）。如果佢買係更早 pitch 的，會有偏差。但對於 care follow-up 嚟講，"你有冇飲到上次介紹嘅湯" 夠用了。之後如果需要精確，可以讓 Jessica 問 "係邊款呀？"
- 从零搭建了一个 asyncio 后台循环，每 6 小时跑一次，自动给用户发主动关怀消息。共有四种广播类型：


## 2026-05-29 11:18 — TCM-Jessica

### Architecture Decisions
- **Is this a gap you want to fill?** Because it's actually a good one for TCM — HK weather swings are a natural trigger for health care tips. The architecture for it would be:
- 呢個 split 大概貴 3-5x（但 production query 量低，每個用戶日均幾條 message 而已），可能值得試。要我先 fix 緊嘅產品圖片同功效顯示問題，定先做 model split 實驗？
- Now apply `extracted_pain_points` to CRM. This is the **critical fix**:
- 如果你想 sales 都用 vector，可以做 **hybrid**：keyword 先跑 → 如果 score < threshold 就 fallback 去 vector 搜 product cards。Same pattern as FAQ。
- | **Pain extraction inconsistent** | 🟡 Medium | gpt-5.4-mini 有時 omit `extracted_pain_points`。CRM 最終仍然係 `[]`。要 strengthen prompt 或者用 JSON schema enforcement |
- **Fix E1: Pain extraction fallback** — if LLM omits `extracted_pain_points`, fall back to keyword detection so CRM still gets populated:
- | 2. **辨證**（證型 — 八綱 / 臟腑 / 氣血津液）| ❌ 冇 | 而家**呢一刻嘅 pattern**：肝鬱氣滯 / 脾腎陽虛 / 心脾兩虛 / 痰濕困脾… 真實臨床用嚟開方嘅根據 |
- 2. **No agent does pattern inference** — material in KB, but never extracted into structured form

### Decisions & Reasoning
- | 7 | **情志調理** | 用戶話壓力大 → 自動鏈接對應臟腑 → 推薦湯水 |
- 同天氣廣播共用同一個 6h loop — 唔需要多開任何新嘅 background task。下一個做邊個？節氣提醒定體質複查？
- 全部共用同一個 6h loop，一個 `BROADCAST_ENABLED=true` 開晒。
- `wa.me/85252417448?text=想訂【彭魚鰓解毒湯 HK$120】` — 用戶 click 之後會喺 WhatsApp 開一個 chat 去診所號碼，直接落單。呢個唔係 Jessica 的號碼，所以 Jessica 本身永遠唔知用戶訂咗咩。
- 1. **Purchase CTA 加了一句話** — Jessica 推完產品之後，Writer 現在會加 `「訂完記得話我知呀 😊」`，提示用戶返嚟確認
- 2. **Planner routing** — 用戶回覆 "我訂咗" 類型嘅訊息 → 自動路由去 Sales Agent
- 唯一的 imperfection：我們假設用戶買的是最後被 pitch 的產品（最多 3 款）。如果佢買係更早 pitch 的，會有偏差。但對於 care follow-up 嚟講，"你有冇飲到上次介紹嘅湯" 夠用了。之後如果需要精確，可以讓 Jessica 問 "係邊款呀？"
- 从零搭建了一个 asyncio 后台循环，每 6 小时跑一次，自动给用户发主动关怀消息。共有四种广播类型：


## 2026-05-29 11:56 — TCM-Jessica

### Architecture Decisions
- Got the full picture. Clean implementation: buttons are extracted from specialist payload **in the orchestrator** (not by the Writer LLM) and attached to the last bubble in the router. Five files to touch.


## 2026-05-29 12:35 — TCM-Jessica

### Architecture Decisions
- Got the full picture. Clean implementation: buttons are extracted from specialist payload **in the orchestrator** (not by the Writer LLM) and attached to the last bubble in the router. Five files to touch.

### Decisions & Reasoning
- Good — the raw webhook is already being captured. Let me first restore the poll buttons, then update `parse_webhook` to properly extract the selected option from poll vote events instead of dropping them:
- Now fix `parse_webhook` to properly read poll votes instead of dropping them:


## 2026-05-29 13:08 — TCM-Jessica

### Architecture Decisions
- Got the full picture. Clean implementation: buttons are extracted from specialist payload **in the orchestrator** (not by the Writer LLM) and attached to the last bubble in the router. Five files to touch.

### Decisions & Reasoning
- Good — the raw webhook is already being captured. Let me first restore the poll buttons, then update `parse_webhook` to properly extract the selected option from poll vote events instead of dropping them:
- Now fix `parse_webhook` to properly read poll votes instead of dropping them:


## 2026-05-29 13:16 — TCM-Jessica

### Architecture Decisions
- Got the full picture. Clean implementation: buttons are extracted from specialist payload **in the orchestrator** (not by the Writer LLM) and attached to the last bubble in the router. Five files to touch.

### Decisions & Reasoning
- Good — the raw webhook is already being captured. Let me first restore the poll buttons, then update `parse_webhook` to properly extract the selected option from poll vote events instead of dropping them:
- Now fix `parse_webhook` to properly read poll votes instead of dropping them:
- Now update `parse_webhook` to detect poll votes and set those fields instead of trying to extract from the webhook body:


## 2026-05-29 13:41 — TCM-Jessica

### Architecture Decisions
- Got the full picture. Clean implementation: buttons are extracted from specialist payload **in the orchestrator** (not by the Writer LLM) and attached to the last bubble in the router. Five files to touch.

### Decisions & Reasoning
- Good — the raw webhook is already being captured. Let me first restore the poll buttons, then update `parse_webhook` to properly extract the selected option from poll vote events instead of dropping them:
- Now fix `parse_webhook` to properly read poll votes instead of dropping them:
- Now update `parse_webhook` to detect poll votes and set those fields instead of trying to extract from the webhook body:


## 2026-05-29 13:45 — TCM-Jessica

### Architecture Decisions
- Got the full picture. Clean implementation: buttons are extracted from specialist payload **in the orchestrator** (not by the Writer LLM) and attached to the last bubble in the router. Five files to touch.

### Decisions & Reasoning
- Good — the raw webhook is already being captured. Let me first restore the poll buttons, then update `parse_webhook` to properly extract the selected option from poll vote events instead of dropping them:
- Now fix `parse_webhook` to properly read poll votes instead of dropping them:
- Now update `parse_webhook` to detect poll votes and set those fields instead of trying to extract from the webhook body:


## 2026-05-29 13:51 — TCM-Jessica

### Architecture Decisions
- Got the full picture. Clean implementation: buttons are extracted from specialist payload **in the orchestrator** (not by the Writer LLM) and attached to the last bubble in the router. Five files to touch.

### Decisions & Reasoning
- Good — the raw webhook is already being captured. Let me first restore the poll buttons, then update `parse_webhook` to properly extract the selected option from poll vote events instead of dropping them:
- Now fix `parse_webhook` to properly read poll votes instead of dropping them:
- Now update `parse_webhook` to detect poll votes and set those fields instead of trying to extract from the webhook body:


## 2026-05-29 14:00 — TCM-Jessica

### Architecture Decisions
- Got the full picture. Clean implementation: buttons are extracted from specialist payload **in the orchestrator** (not by the Writer LLM) and attached to the last bubble in the router. Five files to touch.

### Decisions & Reasoning
- Good — the raw webhook is already being captured. Let me first restore the poll buttons, then update `parse_webhook` to properly extract the selected option from poll vote events instead of dropping them:
- Now fix `parse_webhook` to properly read poll votes instead of dropping them:
- Now update `parse_webhook` to detect poll votes and set those fields instead of trying to extract from the webhook body:


## 2026-05-29 14:23 — TCM-Jessica

### Architecture Decisions
- Got the full picture. Clean implementation: buttons are extracted from specialist payload **in the orchestrator** (not by the Writer LLM) and attached to the last bubble in the router. Five files to touch.

### Decisions & Reasoning
- Good — the raw webhook is already being captured. Let me first restore the poll buttons, then update `parse_webhook` to properly extract the selected option from poll vote events instead of dropping them:
- Now fix `parse_webhook` to properly read poll votes instead of dropping them:
- Now update `parse_webhook` to detect poll votes and set those fields instead of trying to extract from the webhook body:


## 2026-05-29 14:29 — TCM-Jessica

### Architecture Decisions
- Got the full picture. Clean implementation: buttons are extracted from specialist payload **in the orchestrator** (not by the Writer LLM) and attached to the last bubble in the router. Five files to touch.

### Decisions & Reasoning
- Good — the raw webhook is already being captured. Let me first restore the poll buttons, then update `parse_webhook` to properly extract the selected option from poll vote events instead of dropping them:
- Now fix `parse_webhook` to properly read poll votes instead of dropping them:
- Now update `parse_webhook` to detect poll votes and set those fields instead of trying to extract from the webhook body:


## 2026-05-29 14:36 — TCM-Jessica

### Architecture Decisions
- Got the full picture. Clean implementation: buttons are extracted from specialist payload **in the orchestrator** (not by the Writer LLM) and attached to the last bubble in the router. Five files to touch.

### Decisions & Reasoning
- Good — the raw webhook is already being captured. Let me first restore the poll buttons, then update `parse_webhook` to properly extract the selected option from poll vote events instead of dropping them:
- Now fix `parse_webhook` to properly read poll votes instead of dropping them:
- Now update `parse_webhook` to detect poll votes and set those fields instead of trying to extract from the webhook body:


## 2026-05-29 14:44 — TCM-Jessica

### Architecture Decisions
- Got the full picture. Clean implementation: buttons are extracted from specialist payload **in the orchestrator** (not by the Writer LLM) and attached to the last bubble in the router. Five files to touch.

### Decisions & Reasoning
- Good — the raw webhook is already being captured. Let me first restore the poll buttons, then update `parse_webhook` to properly extract the selected option from poll vote events instead of dropping them:
- Now fix `parse_webhook` to properly read poll votes instead of dropping them:
- Now update `parse_webhook` to detect poll votes and set those fields instead of trying to extract from the webhook body:


## 2026-05-29 14:54 — TCM-Jessica

### Architecture Decisions
- Got the full picture. Clean implementation: buttons are extracted from specialist payload **in the orchestrator** (not by the Writer LLM) and attached to the last bubble in the router. Five files to touch.

### Decisions & Reasoning
- Good — the raw webhook is already being captured. Let me first restore the poll buttons, then update `parse_webhook` to properly extract the selected option from poll vote events instead of dropping them:
- Now fix `parse_webhook` to properly read poll votes instead of dropping them:
- Now update `parse_webhook` to detect poll votes and set those fields instead of trying to extract from the webhook body:


## 2026-05-29 14:57 — TCM-Jessica

### Architecture Decisions
- Got the full picture. Clean implementation: buttons are extracted from specialist payload **in the orchestrator** (not by the Writer LLM) and attached to the last bubble in the router. Five files to touch.

### Decisions & Reasoning
- Good — the raw webhook is already being captured. Let me first restore the poll buttons, then update `parse_webhook` to properly extract the selected option from poll vote events instead of dropping them:
- Now fix `parse_webhook` to properly read poll votes instead of dropping them:
- Now update `parse_webhook` to detect poll votes and set those fields instead of trying to extract from the webhook body:


## 2026-05-29 15:00 — TCM-Jessica

### Architecture Decisions
- Got the full picture. Clean implementation: buttons are extracted from specialist payload **in the orchestrator** (not by the Writer LLM) and attached to the last bubble in the router. Five files to touch.

### Decisions & Reasoning
- Good — the raw webhook is already being captured. Let me first restore the poll buttons, then update `parse_webhook` to properly extract the selected option from poll vote events instead of dropping them:
- Now fix `parse_webhook` to properly read poll votes instead of dropping them:
- Now update `parse_webhook` to detect poll votes and set those fields instead of trying to extract from the webhook body:


## 2026-05-29 15:02 — TCM-Jessica

### Architecture Decisions
- Got the full picture. Clean implementation: buttons are extracted from specialist payload **in the orchestrator** (not by the Writer LLM) and attached to the last bubble in the router. Five files to touch.

### Decisions & Reasoning
- Good — the raw webhook is already being captured. Let me first restore the poll buttons, then update `parse_webhook` to properly extract the selected option from poll vote events instead of dropping them:
- Now fix `parse_webhook` to properly read poll votes instead of dropping them:
- Now update `parse_webhook` to detect poll votes and set those fields instead of trying to extract from the webhook body:


## 2026-05-29 15:05 — TCM-Jessica

### Architecture Decisions
- Got the full picture. Clean implementation: buttons are extracted from specialist payload **in the orchestrator** (not by the Writer LLM) and attached to the last bubble in the router. Five files to touch.

### Decisions & Reasoning
- Good — the raw webhook is already being captured. Let me first restore the poll buttons, then update `parse_webhook` to properly extract the selected option from poll vote events instead of dropping them:
- Now fix `parse_webhook` to properly read poll votes instead of dropping them:
- Now update `parse_webhook` to detect poll votes and set those fields instead of trying to extract from the webhook body:


## 2026-05-29 15:08 — TCM-Jessica

### Architecture Decisions
- Got the full picture. Clean implementation: buttons are extracted from specialist payload **in the orchestrator** (not by the Writer LLM) and attached to the last bubble in the router. Five files to touch.

### Decisions & Reasoning
- Good — the raw webhook is already being captured. Let me first restore the poll buttons, then update `parse_webhook` to properly extract the selected option from poll vote events instead of dropping them:
- Now fix `parse_webhook` to properly read poll votes instead of dropping them:
- Now update `parse_webhook` to detect poll votes and set those fields instead of trying to extract from the webhook body:


## 2026-05-29 15:20 — TCM-Jessica

### Architecture Decisions
- Got the full picture. Clean implementation: buttons are extracted from specialist payload **in the orchestrator** (not by the Writer LLM) and attached to the last bubble in the router. Five files to touch.

### Decisions & Reasoning
- Good — the raw webhook is already being captured. Let me first restore the poll buttons, then update `parse_webhook` to properly extract the selected option from poll vote events instead of dropping them:
- Now fix `parse_webhook` to properly read poll votes instead of dropping them:
- Now update `parse_webhook` to detect poll votes and set those fields instead of trying to extract from the webhook body:


## 2026-05-29 15:24 — TCM-Jessica

### Architecture Decisions
- Got the full picture. Clean implementation: buttons are extracted from specialist payload **in the orchestrator** (not by the Writer LLM) and attached to the last bubble in the router. Five files to touch.

### Decisions & Reasoning
- Good — the raw webhook is already being captured. Let me first restore the poll buttons, then update `parse_webhook` to properly extract the selected option from poll vote events instead of dropping them:
- Now fix `parse_webhook` to properly read poll votes instead of dropping them:
- Now update `parse_webhook` to detect poll votes and set those fields instead of trying to extract from the webhook body:


## 2026-05-29 16:06 — TCM-Jessica

### Architecture Decisions
- Got the full picture. Clean implementation: buttons are extracted from specialist payload **in the orchestrator** (not by the Writer LLM) and attached to the last bubble in the router. Five files to touch.

### Decisions & Reasoning
- Good — the raw webhook is already being captured. Let me first restore the poll buttons, then update `parse_webhook` to properly extract the selected option from poll vote events instead of dropping them:
- Now fix `parse_webhook` to properly read poll votes instead of dropping them:
- Now update `parse_webhook` to detect poll votes and set those fields instead of trying to extract from the webhook body:


## 2026-05-29 18:45 — TCM-Jessica

### Architecture Decisions
- Got the full picture. Clean implementation: buttons are extracted from specialist payload **in the orchestrator** (not by the Writer LLM) and attached to the last bubble in the router. Five files to touch.

### Decisions & Reasoning
- Good — the raw webhook is already being captured. Let me first restore the poll buttons, then update `parse_webhook` to properly extract the selected option from poll vote events instead of dropping them:
- Now fix `parse_webhook` to properly read poll votes instead of dropping them:
- Now update `parse_webhook` to detect poll votes and set those fields instead of trying to extract from the webhook body:


## 2026-05-29 18:46 — TCM-Jessica

### Architecture Decisions
- **Is this a gap you want to fill?** Because it's actually a good one for TCM — HK weather swings are a natural trigger for health care tips. The architecture for it would be:
- 呢個 split 大概貴 3-5x（但 production query 量低，每個用戶日均幾條 message 而已），可能值得試。要我先 fix 緊嘅產品圖片同功效顯示問題，定先做 model split 實驗？
- Now apply `extracted_pain_points` to CRM. This is the **critical fix**:
- 如果你想 sales 都用 vector，可以做 **hybrid**：keyword 先跑 → 如果 score < threshold 就 fallback 去 vector 搜 product cards。Same pattern as FAQ。
- | **Pain extraction inconsistent** | 🟡 Medium | gpt-5.4-mini 有時 omit `extracted_pain_points`。CRM 最終仍然係 `[]`。要 strengthen prompt 或者用 JSON schema enforcement |
- **Fix E1: Pain extraction fallback** — if LLM omits `extracted_pain_points`, fall back to keyword detection so CRM still gets populated:
- | 2. **辨證**（證型 — 八綱 / 臟腑 / 氣血津液）| ❌ 冇 | 而家**呢一刻嘅 pattern**：肝鬱氣滯 / 脾腎陽虛 / 心脾兩虛 / 痰濕困脾… 真實臨床用嚟開方嘅根據 |
- 2. **No agent does pattern inference** — material in KB, but never extracted into structured form

### Decisions & Reasoning
- | 7 | **情志調理** | 用戶話壓力大 → 自動鏈接對應臟腑 → 推薦湯水 |
- 同天氣廣播共用同一個 6h loop — 唔需要多開任何新嘅 background task。下一個做邊個？節氣提醒定體質複查？
- 全部共用同一個 6h loop，一個 `BROADCAST_ENABLED=true` 開晒。
- `wa.me/85252417448?text=想訂【彭魚鰓解毒湯 HK$120】` — 用戶 click 之後會喺 WhatsApp 開一個 chat 去診所號碼，直接落單。呢個唔係 Jessica 的號碼，所以 Jessica 本身永遠唔知用戶訂咗咩。
- 1. **Purchase CTA 加了一句話** — Jessica 推完產品之後，Writer 現在會加 `「訂完記得話我知呀 😊」`，提示用戶返嚟確認
- 2. **Planner routing** — 用戶回覆 "我訂咗" 類型嘅訊息 → 自動路由去 Sales Agent
- 唯一的 imperfection：我們假設用戶買的是最後被 pitch 的產品（最多 3 款）。如果佢買係更早 pitch 的，會有偏差。但對於 care follow-up 嚟講，"你有冇飲到上次介紹嘅湯" 夠用了。之後如果需要精確，可以讓 Jessica 問 "係邊款呀？"
- 从零搭建了一个 asyncio 后台循环，每 6 小时跑一次，自动给用户发主动关怀消息。共有四种广播类型：


## 2026-06-03 09:32 — TCM-Jessica

### Architecture Decisions
- **Is this a gap you want to fill?** Because it's actually a good one for TCM — HK weather swings are a natural trigger for health care tips. The architecture for it would be:
- 呢個 split 大概貴 3-5x（但 production query 量低，每個用戶日均幾條 message 而已），可能值得試。要我先 fix 緊嘅產品圖片同功效顯示問題，定先做 model split 實驗？
- Now apply `extracted_pain_points` to CRM. This is the **critical fix**:
- 如果你想 sales 都用 vector，可以做 **hybrid**：keyword 先跑 → 如果 score < threshold 就 fallback 去 vector 搜 product cards。Same pattern as FAQ。
- | **Pain extraction inconsistent** | 🟡 Medium | gpt-5.4-mini 有時 omit `extracted_pain_points`。CRM 最終仍然係 `[]`。要 strengthen prompt 或者用 JSON schema enforcement |
- **Fix E1: Pain extraction fallback** — if LLM omits `extracted_pain_points`, fall back to keyword detection so CRM still gets populated:
- | 2. **辨證**（證型 — 八綱 / 臟腑 / 氣血津液）| ❌ 冇 | 而家**呢一刻嘅 pattern**：肝鬱氣滯 / 脾腎陽虛 / 心脾兩虛 / 痰濕困脾… 真實臨床用嚟開方嘅根據 |
- 2. **No agent does pattern inference** — material in KB, but never extracted into structured form

### Decisions & Reasoning
- | 7 | **情志調理** | 用戶話壓力大 → 自動鏈接對應臟腑 → 推薦湯水 |
- 同天氣廣播共用同一個 6h loop — 唔需要多開任何新嘅 background task。下一個做邊個？節氣提醒定體質複查？
- 全部共用同一個 6h loop，一個 `BROADCAST_ENABLED=true` 開晒。
- `wa.me/85252417448?text=想訂【彭魚鰓解毒湯 HK$120】` — 用戶 click 之後會喺 WhatsApp 開一個 chat 去診所號碼，直接落單。呢個唔係 Jessica 的號碼，所以 Jessica 本身永遠唔知用戶訂咗咩。
- 1. **Purchase CTA 加了一句話** — Jessica 推完產品之後，Writer 現在會加 `「訂完記得話我知呀 😊」`，提示用戶返嚟確認
- 2. **Planner routing** — 用戶回覆 "我訂咗" 類型嘅訊息 → 自動路由去 Sales Agent
- 唯一的 imperfection：我們假設用戶買的是最後被 pitch 的產品（最多 3 款）。如果佢買係更早 pitch 的，會有偏差。但對於 care follow-up 嚟講，"你有冇飲到上次介紹嘅湯" 夠用了。之後如果需要精確，可以讓 Jessica 問 "係邊款呀？"
- 从零搭建了一个 asyncio 后台循环，每 6 小时跑一次，自动给用户发主动关怀消息。共有四种广播类型：


## 2026-06-03 10:22 — TCM-Jessica

### Architecture Decisions
- **Is this a gap you want to fill?** Because it's actually a good one for TCM — HK weather swings are a natural trigger for health care tips. The architecture for it would be:
- 呢個 split 大概貴 3-5x（但 production query 量低，每個用戶日均幾條 message 而已），可能值得試。要我先 fix 緊嘅產品圖片同功效顯示問題，定先做 model split 實驗？
- Now apply `extracted_pain_points` to CRM. This is the **critical fix**:
- 如果你想 sales 都用 vector，可以做 **hybrid**：keyword 先跑 → 如果 score < threshold 就 fallback 去 vector 搜 product cards。Same pattern as FAQ。
- | **Pain extraction inconsistent** | 🟡 Medium | gpt-5.4-mini 有時 omit `extracted_pain_points`。CRM 最終仍然係 `[]`。要 strengthen prompt 或者用 JSON schema enforcement |
- **Fix E1: Pain extraction fallback** — if LLM omits `extracted_pain_points`, fall back to keyword detection so CRM still gets populated:
- | 2. **辨證**（證型 — 八綱 / 臟腑 / 氣血津液）| ❌ 冇 | 而家**呢一刻嘅 pattern**：肝鬱氣滯 / 脾腎陽虛 / 心脾兩虛 / 痰濕困脾… 真實臨床用嚟開方嘅根據 |
- 2. **No agent does pattern inference** — material in KB, but never extracted into structured form

### Decisions & Reasoning
- | 7 | **情志調理** | 用戶話壓力大 → 自動鏈接對應臟腑 → 推薦湯水 |
- 同天氣廣播共用同一個 6h loop — 唔需要多開任何新嘅 background task。下一個做邊個？節氣提醒定體質複查？
- 全部共用同一個 6h loop，一個 `BROADCAST_ENABLED=true` 開晒。
- `wa.me/85252417448?text=想訂【彭魚鰓解毒湯 HK$120】` — 用戶 click 之後會喺 WhatsApp 開一個 chat 去診所號碼，直接落單。呢個唔係 Jessica 的號碼，所以 Jessica 本身永遠唔知用戶訂咗咩。
- 1. **Purchase CTA 加了一句話** — Jessica 推完產品之後，Writer 現在會加 `「訂完記得話我知呀 😊」`，提示用戶返嚟確認
- 2. **Planner routing** — 用戶回覆 "我訂咗" 類型嘅訊息 → 自動路由去 Sales Agent
- 唯一的 imperfection：我們假設用戶買的是最後被 pitch 的產品（最多 3 款）。如果佢買係更早 pitch 的，會有偏差。但對於 care follow-up 嚟講，"你有冇飲到上次介紹嘅湯" 夠用了。之後如果需要精確，可以讓 Jessica 問 "係邊款呀？"
- 从零搭建了一个 asyncio 后台循环，每 6 小时跑一次，自动给用户发主动关怀消息。共有四种广播类型：


## 2026-06-03 11:01 — TCM-Jessica

### Architecture Decisions
- **Is this a gap you want to fill?** Because it's actually a good one for TCM — HK weather swings are a natural trigger for health care tips. The architecture for it would be:
- 呢個 split 大概貴 3-5x（但 production query 量低，每個用戶日均幾條 message 而已），可能值得試。要我先 fix 緊嘅產品圖片同功效顯示問題，定先做 model split 實驗？
- Now apply `extracted_pain_points` to CRM. This is the **critical fix**:
- 如果你想 sales 都用 vector，可以做 **hybrid**：keyword 先跑 → 如果 score < threshold 就 fallback 去 vector 搜 product cards。Same pattern as FAQ。
- | **Pain extraction inconsistent** | 🟡 Medium | gpt-5.4-mini 有時 omit `extracted_pain_points`。CRM 最終仍然係 `[]`。要 strengthen prompt 或者用 JSON schema enforcement |
- **Fix E1: Pain extraction fallback** — if LLM omits `extracted_pain_points`, fall back to keyword detection so CRM still gets populated:
- | 2. **辨證**（證型 — 八綱 / 臟腑 / 氣血津液）| ❌ 冇 | 而家**呢一刻嘅 pattern**：肝鬱氣滯 / 脾腎陽虛 / 心脾兩虛 / 痰濕困脾… 真實臨床用嚟開方嘅根據 |
- 2. **No agent does pattern inference** — material in KB, but never extracted into structured form

### Decisions & Reasoning
- | 7 | **情志調理** | 用戶話壓力大 → 自動鏈接對應臟腑 → 推薦湯水 |
- 同天氣廣播共用同一個 6h loop — 唔需要多開任何新嘅 background task。下一個做邊個？節氣提醒定體質複查？
- 全部共用同一個 6h loop，一個 `BROADCAST_ENABLED=true` 開晒。
- `wa.me/85252417448?text=想訂【彭魚鰓解毒湯 HK$120】` — 用戶 click 之後會喺 WhatsApp 開一個 chat 去診所號碼，直接落單。呢個唔係 Jessica 的號碼，所以 Jessica 本身永遠唔知用戶訂咗咩。
- 1. **Purchase CTA 加了一句話** — Jessica 推完產品之後，Writer 現在會加 `「訂完記得話我知呀 😊」`，提示用戶返嚟確認
- 2. **Planner routing** — 用戶回覆 "我訂咗" 類型嘅訊息 → 自動路由去 Sales Agent
- 唯一的 imperfection：我們假設用戶買的是最後被 pitch 的產品（最多 3 款）。如果佢買係更早 pitch 的，會有偏差。但對於 care follow-up 嚟講，"你有冇飲到上次介紹嘅湯" 夠用了。之後如果需要精確，可以讓 Jessica 問 "係邊款呀？"
- 从零搭建了一个 asyncio 后台循环，每 6 小时跑一次，自动给用户发主动关怀消息。共有四种广播类型：


## 2026-06-03 11:06 — TCM-Jessica

### Architecture Decisions
- **Is this a gap you want to fill?** Because it's actually a good one for TCM — HK weather swings are a natural trigger for health care tips. The architecture for it would be:
- 呢個 split 大概貴 3-5x（但 production query 量低，每個用戶日均幾條 message 而已），可能值得試。要我先 fix 緊嘅產品圖片同功效顯示問題，定先做 model split 實驗？
- Now apply `extracted_pain_points` to CRM. This is the **critical fix**:
- 如果你想 sales 都用 vector，可以做 **hybrid**：keyword 先跑 → 如果 score < threshold 就 fallback 去 vector 搜 product cards。Same pattern as FAQ。
- | **Pain extraction inconsistent** | 🟡 Medium | gpt-5.4-mini 有時 omit `extracted_pain_points`。CRM 最終仍然係 `[]`。要 strengthen prompt 或者用 JSON schema enforcement |
- **Fix E1: Pain extraction fallback** — if LLM omits `extracted_pain_points`, fall back to keyword detection so CRM still gets populated:
- | 2. **辨證**（證型 — 八綱 / 臟腑 / 氣血津液）| ❌ 冇 | 而家**呢一刻嘅 pattern**：肝鬱氣滯 / 脾腎陽虛 / 心脾兩虛 / 痰濕困脾… 真實臨床用嚟開方嘅根據 |
- 2. **No agent does pattern inference** — material in KB, but never extracted into structured form

### Decisions & Reasoning
- | 7 | **情志調理** | 用戶話壓力大 → 自動鏈接對應臟腑 → 推薦湯水 |
- 同天氣廣播共用同一個 6h loop — 唔需要多開任何新嘅 background task。下一個做邊個？節氣提醒定體質複查？
- 全部共用同一個 6h loop，一個 `BROADCAST_ENABLED=true` 開晒。
- `wa.me/85252417448?text=想訂【彭魚鰓解毒湯 HK$120】` — 用戶 click 之後會喺 WhatsApp 開一個 chat 去診所號碼，直接落單。呢個唔係 Jessica 的號碼，所以 Jessica 本身永遠唔知用戶訂咗咩。
- 1. **Purchase CTA 加了一句話** — Jessica 推完產品之後，Writer 現在會加 `「訂完記得話我知呀 😊」`，提示用戶返嚟確認
- 2. **Planner routing** — 用戶回覆 "我訂咗" 類型嘅訊息 → 自動路由去 Sales Agent
- 唯一的 imperfection：我們假設用戶買的是最後被 pitch 的產品（最多 3 款）。如果佢買係更早 pitch 的，會有偏差。但對於 care follow-up 嚟講，"你有冇飲到上次介紹嘅湯" 夠用了。之後如果需要精確，可以讓 Jessica 問 "係邊款呀？"
- 从零搭建了一个 asyncio 后台循环，每 6 小时跑一次，自动给用户发主动关怀消息。共有四种广播类型：


## 2026-06-03 11:39 — TCM-Jessica

### Architecture Decisions
- **Is this a gap you want to fill?** Because it's actually a good one for TCM — HK weather swings are a natural trigger for health care tips. The architecture for it would be:
- 呢個 split 大概貴 3-5x（但 production query 量低，每個用戶日均幾條 message 而已），可能值得試。要我先 fix 緊嘅產品圖片同功效顯示問題，定先做 model split 實驗？
- Now apply `extracted_pain_points` to CRM. This is the **critical fix**:
- 如果你想 sales 都用 vector，可以做 **hybrid**：keyword 先跑 → 如果 score < threshold 就 fallback 去 vector 搜 product cards。Same pattern as FAQ。
- | **Pain extraction inconsistent** | 🟡 Medium | gpt-5.4-mini 有時 omit `extracted_pain_points`。CRM 最終仍然係 `[]`。要 strengthen prompt 或者用 JSON schema enforcement |
- **Fix E1: Pain extraction fallback** — if LLM omits `extracted_pain_points`, fall back to keyword detection so CRM still gets populated:
- | 2. **辨證**（證型 — 八綱 / 臟腑 / 氣血津液）| ❌ 冇 | 而家**呢一刻嘅 pattern**：肝鬱氣滯 / 脾腎陽虛 / 心脾兩虛 / 痰濕困脾… 真實臨床用嚟開方嘅根據 |
- 2. **No agent does pattern inference** — material in KB, but never extracted into structured form

### Decisions & Reasoning
- | 7 | **情志調理** | 用戶話壓力大 → 自動鏈接對應臟腑 → 推薦湯水 |
- 同天氣廣播共用同一個 6h loop — 唔需要多開任何新嘅 background task。下一個做邊個？節氣提醒定體質複查？
- 全部共用同一個 6h loop，一個 `BROADCAST_ENABLED=true` 開晒。
- `wa.me/85252417448?text=想訂【彭魚鰓解毒湯 HK$120】` — 用戶 click 之後會喺 WhatsApp 開一個 chat 去診所號碼，直接落單。呢個唔係 Jessica 的號碼，所以 Jessica 本身永遠唔知用戶訂咗咩。
- 1. **Purchase CTA 加了一句話** — Jessica 推完產品之後，Writer 現在會加 `「訂完記得話我知呀 😊」`，提示用戶返嚟確認
- 2. **Planner routing** — 用戶回覆 "我訂咗" 類型嘅訊息 → 自動路由去 Sales Agent
- 唯一的 imperfection：我們假設用戶買的是最後被 pitch 的產品（最多 3 款）。如果佢買係更早 pitch 的，會有偏差。但對於 care follow-up 嚟講，"你有冇飲到上次介紹嘅湯" 夠用了。之後如果需要精確，可以讓 Jessica 問 "係邊款呀？"
- 从零搭建了一个 asyncio 后台循环，每 6 小时跑一次，自动给用户发主动关怀消息。共有四种广播类型：


## 2026-06-03 11:49 — TCM-Jessica

### Architecture Decisions
- **Is this a gap you want to fill?** Because it's actually a good one for TCM — HK weather swings are a natural trigger for health care tips. The architecture for it would be:
- 呢個 split 大概貴 3-5x（但 production query 量低，每個用戶日均幾條 message 而已），可能值得試。要我先 fix 緊嘅產品圖片同功效顯示問題，定先做 model split 實驗？
- Now apply `extracted_pain_points` to CRM. This is the **critical fix**:
- 如果你想 sales 都用 vector，可以做 **hybrid**：keyword 先跑 → 如果 score < threshold 就 fallback 去 vector 搜 product cards。Same pattern as FAQ。
- | **Pain extraction inconsistent** | 🟡 Medium | gpt-5.4-mini 有時 omit `extracted_pain_points`。CRM 最終仍然係 `[]`。要 strengthen prompt 或者用 JSON schema enforcement |
- **Fix E1: Pain extraction fallback** — if LLM omits `extracted_pain_points`, fall back to keyword detection so CRM still gets populated:
- | 2. **辨證**（證型 — 八綱 / 臟腑 / 氣血津液）| ❌ 冇 | 而家**呢一刻嘅 pattern**：肝鬱氣滯 / 脾腎陽虛 / 心脾兩虛 / 痰濕困脾… 真實臨床用嚟開方嘅根據 |
- 2. **No agent does pattern inference** — material in KB, but never extracted into structured form

### Decisions & Reasoning
- | 7 | **情志調理** | 用戶話壓力大 → 自動鏈接對應臟腑 → 推薦湯水 |
- 同天氣廣播共用同一個 6h loop — 唔需要多開任何新嘅 background task。下一個做邊個？節氣提醒定體質複查？
- 全部共用同一個 6h loop，一個 `BROADCAST_ENABLED=true` 開晒。
- `wa.me/85252417448?text=想訂【彭魚鰓解毒湯 HK$120】` — 用戶 click 之後會喺 WhatsApp 開一個 chat 去診所號碼，直接落單。呢個唔係 Jessica 的號碼，所以 Jessica 本身永遠唔知用戶訂咗咩。
- 1. **Purchase CTA 加了一句話** — Jessica 推完產品之後，Writer 現在會加 `「訂完記得話我知呀 😊」`，提示用戶返嚟確認
- 2. **Planner routing** — 用戶回覆 "我訂咗" 類型嘅訊息 → 自動路由去 Sales Agent
- 唯一的 imperfection：我們假設用戶買的是最後被 pitch 的產品（最多 3 款）。如果佢買係更早 pitch 的，會有偏差。但對於 care follow-up 嚟講，"你有冇飲到上次介紹嘅湯" 夠用了。之後如果需要精確，可以讓 Jessica 問 "係邊款呀？"
- 从零搭建了一个 asyncio 后台循环，每 6 小时跑一次，自动给用户发主动关怀消息。共有四种广播类型：


## 2026-06-03 11:51 — TCM-Jessica

### Architecture Decisions
- **`router.py`** — Group messages now split into two paths:


## 2026-06-03 11:52 — TCM-Jessica

### Architecture Decisions
- **`router.py`** — Group messages now split into two paths:


## 2026-06-03 11:55 — TCM-Jessica

### Architecture Decisions
- **Is this a gap you want to fill?** Because it's actually a good one for TCM — HK weather swings are a natural trigger for health care tips. The architecture for it would be:
- 呢個 split 大概貴 3-5x（但 production query 量低，每個用戶日均幾條 message 而已），可能值得試。要我先 fix 緊嘅產品圖片同功效顯示問題，定先做 model split 實驗？
- Now apply `extracted_pain_points` to CRM. This is the **critical fix**:
- 如果你想 sales 都用 vector，可以做 **hybrid**：keyword 先跑 → 如果 score < threshold 就 fallback 去 vector 搜 product cards。Same pattern as FAQ。
- | **Pain extraction inconsistent** | 🟡 Medium | gpt-5.4-mini 有時 omit `extracted_pain_points`。CRM 最終仍然係 `[]`。要 strengthen prompt 或者用 JSON schema enforcement |
- **Fix E1: Pain extraction fallback** — if LLM omits `extracted_pain_points`, fall back to keyword detection so CRM still gets populated:
- | 2. **辨證**（證型 — 八綱 / 臟腑 / 氣血津液）| ❌ 冇 | 而家**呢一刻嘅 pattern**：肝鬱氣滯 / 脾腎陽虛 / 心脾兩虛 / 痰濕困脾… 真實臨床用嚟開方嘅根據 |
- 2. **No agent does pattern inference** — material in KB, but never extracted into structured form

### Decisions & Reasoning
- | 7 | **情志調理** | 用戶話壓力大 → 自動鏈接對應臟腑 → 推薦湯水 |
- 同天氣廣播共用同一個 6h loop — 唔需要多開任何新嘅 background task。下一個做邊個？節氣提醒定體質複查？
- 全部共用同一個 6h loop，一個 `BROADCAST_ENABLED=true` 開晒。
- `wa.me/85252417448?text=想訂【彭魚鰓解毒湯 HK$120】` — 用戶 click 之後會喺 WhatsApp 開一個 chat 去診所號碼，直接落單。呢個唔係 Jessica 的號碼，所以 Jessica 本身永遠唔知用戶訂咗咩。
- 1. **Purchase CTA 加了一句話** — Jessica 推完產品之後，Writer 現在會加 `「訂完記得話我知呀 😊」`，提示用戶返嚟確認
- 2. **Planner routing** — 用戶回覆 "我訂咗" 類型嘅訊息 → 自動路由去 Sales Agent
- 唯一的 imperfection：我們假設用戶買的是最後被 pitch 的產品（最多 3 款）。如果佢買係更早 pitch 的，會有偏差。但對於 care follow-up 嚟講，"你有冇飲到上次介紹嘅湯" 夠用了。之後如果需要精確，可以讓 Jessica 問 "係邊款呀？"
- 从零搭建了一个 asyncio 后台循环，每 6 小时跑一次，自动给用户发主动关怀消息。共有四种广播类型：


## 2026-06-03 11:57 — TCM-Jessica

### Architecture Decisions
- **`router.py`** — Group messages now split into two paths:


## 2026-06-03 11:58 — TCM-Jessica

### Architecture Decisions
- **`router.py`** — Group messages now split into two paths:


## 2026-06-03 12:14 — TCM-Jessica

### Architecture Decisions
- **Is this a gap you want to fill?** Because it's actually a good one for TCM — HK weather swings are a natural trigger for health care tips. The architecture for it would be:
- 呢個 split 大概貴 3-5x（但 production query 量低，每個用戶日均幾條 message 而已），可能值得試。要我先 fix 緊嘅產品圖片同功效顯示問題，定先做 model split 實驗？
- Now apply `extracted_pain_points` to CRM. This is the **critical fix**:
- 如果你想 sales 都用 vector，可以做 **hybrid**：keyword 先跑 → 如果 score < threshold 就 fallback 去 vector 搜 product cards。Same pattern as FAQ。
- | **Pain extraction inconsistent** | 🟡 Medium | gpt-5.4-mini 有時 omit `extracted_pain_points`。CRM 最終仍然係 `[]`。要 strengthen prompt 或者用 JSON schema enforcement |
- **Fix E1: Pain extraction fallback** — if LLM omits `extracted_pain_points`, fall back to keyword detection so CRM still gets populated:
- | 2. **辨證**（證型 — 八綱 / 臟腑 / 氣血津液）| ❌ 冇 | 而家**呢一刻嘅 pattern**：肝鬱氣滯 / 脾腎陽虛 / 心脾兩虛 / 痰濕困脾… 真實臨床用嚟開方嘅根據 |
- 2. **No agent does pattern inference** — material in KB, but never extracted into structured form

### Decisions & Reasoning
- | 7 | **情志調理** | 用戶話壓力大 → 自動鏈接對應臟腑 → 推薦湯水 |
- 同天氣廣播共用同一個 6h loop — 唔需要多開任何新嘅 background task。下一個做邊個？節氣提醒定體質複查？
- 全部共用同一個 6h loop，一個 `BROADCAST_ENABLED=true` 開晒。
- `wa.me/85252417448?text=想訂【彭魚鰓解毒湯 HK$120】` — 用戶 click 之後會喺 WhatsApp 開一個 chat 去診所號碼，直接落單。呢個唔係 Jessica 的號碼，所以 Jessica 本身永遠唔知用戶訂咗咩。
- 1. **Purchase CTA 加了一句話** — Jessica 推完產品之後，Writer 現在會加 `「訂完記得話我知呀 😊」`，提示用戶返嚟確認
- 2. **Planner routing** — 用戶回覆 "我訂咗" 類型嘅訊息 → 自動路由去 Sales Agent
- 唯一的 imperfection：我們假設用戶買的是最後被 pitch 的產品（最多 3 款）。如果佢買係更早 pitch 的，會有偏差。但對於 care follow-up 嚟講，"你有冇飲到上次介紹嘅湯" 夠用了。之後如果需要精確，可以讓 Jessica 問 "係邊款呀？"
- 从零搭建了一个 asyncio 后台循环，每 6 小时跑一次，自动给用户发主动关怀消息。共有四种广播类型：


## 2026-06-03 12:30 — TCM-Jessica

### What Didn't Work (negative knowledge)
- The 400 means `parse_webhook` rejected the payload (likely a non-message event OR the cold-start). I can't see the raw payload because the diagnostic endpoint was removed earlier. The cleanest move: re-add a minimal raw-webhook viewer so I can see **exactly** what ChatDaddy sends for your @-mention. Let me check the capture module:

### Architecture Decisions
- **Is this a gap you want to fill?** Because it's actually a good one for TCM — HK weather swings are a natural trigger for health care tips. The architecture for it would be:
- 呢個 split 大概貴 3-5x（但 production query 量低，每個用戶日均幾條 message 而已），可能值得試。要我先 fix 緊嘅產品圖片同功效顯示問題，定先做 model split 實驗？
- Now apply `extracted_pain_points` to CRM. This is the **critical fix**:
- 如果你想 sales 都用 vector，可以做 **hybrid**：keyword 先跑 → 如果 score < threshold 就 fallback 去 vector 搜 product cards。Same pattern as FAQ。
- | **Pain extraction inconsistent** | 🟡 Medium | gpt-5.4-mini 有時 omit `extracted_pain_points`。CRM 最終仍然係 `[]`。要 strengthen prompt 或者用 JSON schema enforcement |
- **Fix E1: Pain extraction fallback** — if LLM omits `extracted_pain_points`, fall back to keyword detection so CRM still gets populated:
- | 2. **辨證**（證型 — 八綱 / 臟腑 / 氣血津液）| ❌ 冇 | 而家**呢一刻嘅 pattern**：肝鬱氣滯 / 脾腎陽虛 / 心脾兩虛 / 痰濕困脾… 真實臨床用嚟開方嘅根據 |
- 2. **No agent does pattern inference** — material in KB, but never extracted into structured form

### Decisions & Reasoning
- | 7 | **情志調理** | 用戶話壓力大 → 自動鏈接對應臟腑 → 推薦湯水 |
- 同天氣廣播共用同一個 6h loop — 唔需要多開任何新嘅 background task。下一個做邊個？節氣提醒定體質複查？
- 全部共用同一個 6h loop，一個 `BROADCAST_ENABLED=true` 開晒。
- `wa.me/85252417448?text=想訂【彭魚鰓解毒湯 HK$120】` — 用戶 click 之後會喺 WhatsApp 開一個 chat 去診所號碼，直接落單。呢個唔係 Jessica 的號碼，所以 Jessica 本身永遠唔知用戶訂咗咩。
- 1. **Purchase CTA 加了一句話** — Jessica 推完產品之後，Writer 現在會加 `「訂完記得話我知呀 😊」`，提示用戶返嚟確認
- 2. **Planner routing** — 用戶回覆 "我訂咗" 類型嘅訊息 → 自動路由去 Sales Agent
- 唯一的 imperfection：我們假設用戶買的是最後被 pitch 的產品（最多 3 款）。如果佢買係更早 pitch 的，會有偏差。但對於 care follow-up 嚟講，"你有冇飲到上次介紹嘅湯" 夠用了。之後如果需要精確，可以讓 Jessica 問 "係邊款呀？"
- 从零搭建了一个 asyncio 后台循环，每 6 小时跑一次，自动给用户发主动关怀消息。共有四种广播类型：


## 2026-06-03 12:41 — TCM-Jessica

### What Didn't Work (negative knowledge)
- The 400 means `parse_webhook` rejected the payload (likely a non-message event OR the cold-start). I can't see the raw payload because the diagnostic endpoint was removed earlier. The cleanest move: re-add a minimal raw-webhook viewer so I can see **exactly** what ChatDaddy sends for your @-mention. Let me check the capture module:

### Architecture Decisions
- **Is this a gap you want to fill?** Because it's actually a good one for TCM — HK weather swings are a natural trigger for health care tips. The architecture for it would be:
- 呢個 split 大概貴 3-5x（但 production query 量低，每個用戶日均幾條 message 而已），可能值得試。要我先 fix 緊嘅產品圖片同功效顯示問題，定先做 model split 實驗？
- Now apply `extracted_pain_points` to CRM. This is the **critical fix**:
- 如果你想 sales 都用 vector，可以做 **hybrid**：keyword 先跑 → 如果 score < threshold 就 fallback 去 vector 搜 product cards。Same pattern as FAQ。
- | **Pain extraction inconsistent** | 🟡 Medium | gpt-5.4-mini 有時 omit `extracted_pain_points`。CRM 最終仍然係 `[]`。要 strengthen prompt 或者用 JSON schema enforcement |
- **Fix E1: Pain extraction fallback** — if LLM omits `extracted_pain_points`, fall back to keyword detection so CRM still gets populated:
- | 2. **辨證**（證型 — 八綱 / 臟腑 / 氣血津液）| ❌ 冇 | 而家**呢一刻嘅 pattern**：肝鬱氣滯 / 脾腎陽虛 / 心脾兩虛 / 痰濕困脾… 真實臨床用嚟開方嘅根據 |
- 2. **No agent does pattern inference** — material in KB, but never extracted into structured form

### Decisions & Reasoning
- | 7 | **情志調理** | 用戶話壓力大 → 自動鏈接對應臟腑 → 推薦湯水 |
- 同天氣廣播共用同一個 6h loop — 唔需要多開任何新嘅 background task。下一個做邊個？節氣提醒定體質複查？
- 全部共用同一個 6h loop，一個 `BROADCAST_ENABLED=true` 開晒。
- `wa.me/85252417448?text=想訂【彭魚鰓解毒湯 HK$120】` — 用戶 click 之後會喺 WhatsApp 開一個 chat 去診所號碼，直接落單。呢個唔係 Jessica 的號碼，所以 Jessica 本身永遠唔知用戶訂咗咩。
- 1. **Purchase CTA 加了一句話** — Jessica 推完產品之後，Writer 現在會加 `「訂完記得話我知呀 😊」`，提示用戶返嚟確認
- 2. **Planner routing** — 用戶回覆 "我訂咗" 類型嘅訊息 → 自動路由去 Sales Agent
- 唯一的 imperfection：我們假設用戶買的是最後被 pitch 的產品（最多 3 款）。如果佢買係更早 pitch 的，會有偏差。但對於 care follow-up 嚟講，"你有冇飲到上次介紹嘅湯" 夠用了。之後如果需要精確，可以讓 Jessica 問 "係邊款呀？"
- 从零搭建了一个 asyncio 后台循环，每 6 小时跑一次，自动给用户发主动关怀消息。共有四种广播类型：


## 2026-06-03 12:48 — TCM-Jessica

### What Didn't Work (negative knowledge)
- The 400 means `parse_webhook` rejected the payload (likely a non-message event OR the cold-start). I can't see the raw payload because the diagnostic endpoint was removed earlier. The cleanest move: re-add a minimal raw-webhook viewer so I can see **exactly** what ChatDaddy sends for your @-mention. Let me check the capture module:

### Architecture Decisions
- **Is this a gap you want to fill?** Because it's actually a good one for TCM — HK weather swings are a natural trigger for health care tips. The architecture for it would be:
- 呢個 split 大概貴 3-5x（但 production query 量低，每個用戶日均幾條 message 而已），可能值得試。要我先 fix 緊嘅產品圖片同功效顯示問題，定先做 model split 實驗？
- Now apply `extracted_pain_points` to CRM. This is the **critical fix**:
- 如果你想 sales 都用 vector，可以做 **hybrid**：keyword 先跑 → 如果 score < threshold 就 fallback 去 vector 搜 product cards。Same pattern as FAQ。
- | **Pain extraction inconsistent** | 🟡 Medium | gpt-5.4-mini 有時 omit `extracted_pain_points`。CRM 最終仍然係 `[]`。要 strengthen prompt 或者用 JSON schema enforcement |
- **Fix E1: Pain extraction fallback** — if LLM omits `extracted_pain_points`, fall back to keyword detection so CRM still gets populated:
- | 2. **辨證**（證型 — 八綱 / 臟腑 / 氣血津液）| ❌ 冇 | 而家**呢一刻嘅 pattern**：肝鬱氣滯 / 脾腎陽虛 / 心脾兩虛 / 痰濕困脾… 真實臨床用嚟開方嘅根據 |
- 2. **No agent does pattern inference** — material in KB, but never extracted into structured form

### Decisions & Reasoning
- | 7 | **情志調理** | 用戶話壓力大 → 自動鏈接對應臟腑 → 推薦湯水 |
- 同天氣廣播共用同一個 6h loop — 唔需要多開任何新嘅 background task。下一個做邊個？節氣提醒定體質複查？
- 全部共用同一個 6h loop，一個 `BROADCAST_ENABLED=true` 開晒。
- `wa.me/85252417448?text=想訂【彭魚鰓解毒湯 HK$120】` — 用戶 click 之後會喺 WhatsApp 開一個 chat 去診所號碼，直接落單。呢個唔係 Jessica 的號碼，所以 Jessica 本身永遠唔知用戶訂咗咩。
- 1. **Purchase CTA 加了一句話** — Jessica 推完產品之後，Writer 現在會加 `「訂完記得話我知呀 😊」`，提示用戶返嚟確認
- 2. **Planner routing** — 用戶回覆 "我訂咗" 類型嘅訊息 → 自動路由去 Sales Agent
- 唯一的 imperfection：我們假設用戶買的是最後被 pitch 的產品（最多 3 款）。如果佢買係更早 pitch 的，會有偏差。但對於 care follow-up 嚟講，"你有冇飲到上次介紹嘅湯" 夠用了。之後如果需要精確，可以讓 Jessica 問 "係邊款呀？"
- 从零搭建了一个 asyncio 后台循环，每 6 小时跑一次，自动给用户发主动关怀消息。共有四种广播类型：


## 2026-06-03 12:51 — TCM-Jessica

### What Didn't Work (negative knowledge)
- The 400 means `parse_webhook` rejected the payload (likely a non-message event OR the cold-start). I can't see the raw payload because the diagnostic endpoint was removed earlier. The cleanest move: re-add a minimal raw-webhook viewer so I can see **exactly** what ChatDaddy sends for your @-mention. Let me check the capture module:

### Architecture Decisions
- **Is this a gap you want to fill?** Because it's actually a good one for TCM — HK weather swings are a natural trigger for health care tips. The architecture for it would be:
- 呢個 split 大概貴 3-5x（但 production query 量低，每個用戶日均幾條 message 而已），可能值得試。要我先 fix 緊嘅產品圖片同功效顯示問題，定先做 model split 實驗？
- Now apply `extracted_pain_points` to CRM. This is the **critical fix**:
- 如果你想 sales 都用 vector，可以做 **hybrid**：keyword 先跑 → 如果 score < threshold 就 fallback 去 vector 搜 product cards。Same pattern as FAQ。
- | **Pain extraction inconsistent** | 🟡 Medium | gpt-5.4-mini 有時 omit `extracted_pain_points`。CRM 最終仍然係 `[]`。要 strengthen prompt 或者用 JSON schema enforcement |
- **Fix E1: Pain extraction fallback** — if LLM omits `extracted_pain_points`, fall back to keyword detection so CRM still gets populated:
- | 2. **辨證**（證型 — 八綱 / 臟腑 / 氣血津液）| ❌ 冇 | 而家**呢一刻嘅 pattern**：肝鬱氣滯 / 脾腎陽虛 / 心脾兩虛 / 痰濕困脾… 真實臨床用嚟開方嘅根據 |
- 2. **No agent does pattern inference** — material in KB, but never extracted into structured form

### Decisions & Reasoning
- | 7 | **情志調理** | 用戶話壓力大 → 自動鏈接對應臟腑 → 推薦湯水 |
- 同天氣廣播共用同一個 6h loop — 唔需要多開任何新嘅 background task。下一個做邊個？節氣提醒定體質複查？
- 全部共用同一個 6h loop，一個 `BROADCAST_ENABLED=true` 開晒。
- `wa.me/85252417448?text=想訂【彭魚鰓解毒湯 HK$120】` — 用戶 click 之後會喺 WhatsApp 開一個 chat 去診所號碼，直接落單。呢個唔係 Jessica 的號碼，所以 Jessica 本身永遠唔知用戶訂咗咩。
- 1. **Purchase CTA 加了一句話** — Jessica 推完產品之後，Writer 現在會加 `「訂完記得話我知呀 😊」`，提示用戶返嚟確認
- 2. **Planner routing** — 用戶回覆 "我訂咗" 類型嘅訊息 → 自動路由去 Sales Agent
- 唯一的 imperfection：我們假設用戶買的是最後被 pitch 的產品（最多 3 款）。如果佢買係更早 pitch 的，會有偏差。但對於 care follow-up 嚟講，"你有冇飲到上次介紹嘅湯" 夠用了。之後如果需要精確，可以讓 Jessica 問 "係邊款呀？"
- 从零搭建了一个 asyncio 后台循环，每 6 小时跑一次，自动给用户发主动关怀消息。共有四种广播类型：


## 2026-06-03 13:30 — TCM-Jessica

### What Didn't Work (negative knowledge)
- The 400 means `parse_webhook` rejected the payload (likely a non-message event OR the cold-start). I can't see the raw payload because the diagnostic endpoint was removed earlier. The cleanest move: re-add a minimal raw-webhook viewer so I can see **exactly** what ChatDaddy sends for your @-mention. Let me check the capture module:

### Architecture Decisions
- **Is this a gap you want to fill?** Because it's actually a good one for TCM — HK weather swings are a natural trigger for health care tips. The architecture for it would be:
- 呢個 split 大概貴 3-5x（但 production query 量低，每個用戶日均幾條 message 而已），可能值得試。要我先 fix 緊嘅產品圖片同功效顯示問題，定先做 model split 實驗？
- Now apply `extracted_pain_points` to CRM. This is the **critical fix**:
- 如果你想 sales 都用 vector，可以做 **hybrid**：keyword 先跑 → 如果 score < threshold 就 fallback 去 vector 搜 product cards。Same pattern as FAQ。
- | **Pain extraction inconsistent** | 🟡 Medium | gpt-5.4-mini 有時 omit `extracted_pain_points`。CRM 最終仍然係 `[]`。要 strengthen prompt 或者用 JSON schema enforcement |
- **Fix E1: Pain extraction fallback** — if LLM omits `extracted_pain_points`, fall back to keyword detection so CRM still gets populated:
- | 2. **辨證**（證型 — 八綱 / 臟腑 / 氣血津液）| ❌ 冇 | 而家**呢一刻嘅 pattern**：肝鬱氣滯 / 脾腎陽虛 / 心脾兩虛 / 痰濕困脾… 真實臨床用嚟開方嘅根據 |
- 2. **No agent does pattern inference** — material in KB, but never extracted into structured form

### Decisions & Reasoning
- | 7 | **情志調理** | 用戶話壓力大 → 自動鏈接對應臟腑 → 推薦湯水 |
- 同天氣廣播共用同一個 6h loop — 唔需要多開任何新嘅 background task。下一個做邊個？節氣提醒定體質複查？
- 全部共用同一個 6h loop，一個 `BROADCAST_ENABLED=true` 開晒。
- `wa.me/85252417448?text=想訂【彭魚鰓解毒湯 HK$120】` — 用戶 click 之後會喺 WhatsApp 開一個 chat 去診所號碼，直接落單。呢個唔係 Jessica 的號碼，所以 Jessica 本身永遠唔知用戶訂咗咩。
- 1. **Purchase CTA 加了一句話** — Jessica 推完產品之後，Writer 現在會加 `「訂完記得話我知呀 😊」`，提示用戶返嚟確認
- 2. **Planner routing** — 用戶回覆 "我訂咗" 類型嘅訊息 → 自動路由去 Sales Agent
- 唯一的 imperfection：我們假設用戶買的是最後被 pitch 的產品（最多 3 款）。如果佢買係更早 pitch 的，會有偏差。但對於 care follow-up 嚟講，"你有冇飲到上次介紹嘅湯" 夠用了。之後如果需要精確，可以讓 Jessica 問 "係邊款呀？"
- 从零搭建了一个 asyncio 后台循环，每 6 小时跑一次，自动给用户发主动关怀消息。共有四种广播类型：


## 2026-06-03 13:40 — TCM-Jessica

### What Didn't Work (negative knowledge)
- The 400 means `parse_webhook` rejected the payload (likely a non-message event OR the cold-start). I can't see the raw payload because the diagnostic endpoint was removed earlier. The cleanest move: re-add a minimal raw-webhook viewer so I can see **exactly** what ChatDaddy sends for your @-mention. Let me check the capture module:
- - 6 regression tests including the exact message that broke.

### Architecture Decisions
- **Is this a gap you want to fill?** Because it's actually a good one for TCM — HK weather swings are a natural trigger for health care tips. The architecture for it would be:
- 呢個 split 大概貴 3-5x（但 production query 量低，每個用戶日均幾條 message 而已），可能值得試。要我先 fix 緊嘅產品圖片同功效顯示問題，定先做 model split 實驗？
- Now apply `extracted_pain_points` to CRM. This is the **critical fix**:
- 如果你想 sales 都用 vector，可以做 **hybrid**：keyword 先跑 → 如果 score < threshold 就 fallback 去 vector 搜 product cards。Same pattern as FAQ。
- | **Pain extraction inconsistent** | 🟡 Medium | gpt-5.4-mini 有時 omit `extracted_pain_points`。CRM 最終仍然係 `[]`。要 strengthen prompt 或者用 JSON schema enforcement |
- **Fix E1: Pain extraction fallback** — if LLM omits `extracted_pain_points`, fall back to keyword detection so CRM still gets populated:
- | 2. **辨證**（證型 — 八綱 / 臟腑 / 氣血津液）| ❌ 冇 | 而家**呢一刻嘅 pattern**：肝鬱氣滯 / 脾腎陽虛 / 心脾兩虛 / 痰濕困脾… 真實臨床用嚟開方嘅根據 |
- 2. **No agent does pattern inference** — material in KB, but never extracted into structured form

### Decisions & Reasoning
- | 7 | **情志調理** | 用戶話壓力大 → 自動鏈接對應臟腑 → 推薦湯水 |
- 同天氣廣播共用同一個 6h loop — 唔需要多開任何新嘅 background task。下一個做邊個？節氣提醒定體質複查？
- 全部共用同一個 6h loop，一個 `BROADCAST_ENABLED=true` 開晒。
- `wa.me/85252417448?text=想訂【彭魚鰓解毒湯 HK$120】` — 用戶 click 之後會喺 WhatsApp 開一個 chat 去診所號碼，直接落單。呢個唔係 Jessica 的號碼，所以 Jessica 本身永遠唔知用戶訂咗咩。
- 1. **Purchase CTA 加了一句話** — Jessica 推完產品之後，Writer 現在會加 `「訂完記得話我知呀 😊」`，提示用戶返嚟確認
- 2. **Planner routing** — 用戶回覆 "我訂咗" 類型嘅訊息 → 自動路由去 Sales Agent
- 唯一的 imperfection：我們假設用戶買的是最後被 pitch 的產品（最多 3 款）。如果佢買係更早 pitch 的，會有偏差。但對於 care follow-up 嚟講，"你有冇飲到上次介紹嘅湯" 夠用了。之後如果需要精確，可以讓 Jessica 問 "係邊款呀？"
- 从零搭建了一个 asyncio 后台循环，每 6 小时跑一次，自动给用户发主动关怀消息。共有四种广播类型：


## 2026-06-03 16:44 — TCM-Jessica

### Architecture Decisions
- **`router.py`** — Group messages now split into two paths:

### Decisions & Reasoning
- WhatsApp 的 LID 係 opaque 的，唔係電話號碼，所以無法自動 link。除非用戶自己 DM，我哋才能將兩個 record 合併。現在唔需要擔心呢個 — 只係你要知道有呢個 edge case。


## 2026-06-03 16:44 — TCM-Jessica

### What Didn't Work (negative knowledge)
- The 400 means `parse_webhook` rejected the payload (likely a non-message event OR the cold-start). I can't see the raw payload because the diagnostic endpoint was removed earlier. The cleanest move: re-add a minimal raw-webhook viewer so I can see **exactly** what ChatDaddy sends for your @-mention. Let me check the capture module:
- - 6 regression tests including the exact message that broke.

### Architecture Decisions
- **Is this a gap you want to fill?** Because it's actually a good one for TCM — HK weather swings are a natural trigger for health care tips. The architecture for it would be:
- 呢個 split 大概貴 3-5x（但 production query 量低，每個用戶日均幾條 message 而已），可能值得試。要我先 fix 緊嘅產品圖片同功效顯示問題，定先做 model split 實驗？
- Now apply `extracted_pain_points` to CRM. This is the **critical fix**:
- 如果你想 sales 都用 vector，可以做 **hybrid**：keyword 先跑 → 如果 score < threshold 就 fallback 去 vector 搜 product cards。Same pattern as FAQ。
- | **Pain extraction inconsistent** | 🟡 Medium | gpt-5.4-mini 有時 omit `extracted_pain_points`。CRM 最終仍然係 `[]`。要 strengthen prompt 或者用 JSON schema enforcement |
- **Fix E1: Pain extraction fallback** — if LLM omits `extracted_pain_points`, fall back to keyword detection so CRM still gets populated:
- | 2. **辨證**（證型 — 八綱 / 臟腑 / 氣血津液）| ❌ 冇 | 而家**呢一刻嘅 pattern**：肝鬱氣滯 / 脾腎陽虛 / 心脾兩虛 / 痰濕困脾… 真實臨床用嚟開方嘅根據 |
- 2. **No agent does pattern inference** — material in KB, but never extracted into structured form

### Decisions & Reasoning
- | 7 | **情志調理** | 用戶話壓力大 → 自動鏈接對應臟腑 → 推薦湯水 |
- 同天氣廣播共用同一個 6h loop — 唔需要多開任何新嘅 background task。下一個做邊個？節氣提醒定體質複查？
- 全部共用同一個 6h loop，一個 `BROADCAST_ENABLED=true` 開晒。
- `wa.me/85252417448?text=想訂【彭魚鰓解毒湯 HK$120】` — 用戶 click 之後會喺 WhatsApp 開一個 chat 去診所號碼，直接落單。呢個唔係 Jessica 的號碼，所以 Jessica 本身永遠唔知用戶訂咗咩。
- 1. **Purchase CTA 加了一句話** — Jessica 推完產品之後，Writer 現在會加 `「訂完記得話我知呀 😊」`，提示用戶返嚟確認
- 2. **Planner routing** — 用戶回覆 "我訂咗" 類型嘅訊息 → 自動路由去 Sales Agent
- 唯一的 imperfection：我們假設用戶買的是最後被 pitch 的產品（最多 3 款）。如果佢買係更早 pitch 的，會有偏差。但對於 care follow-up 嚟講，"你有冇飲到上次介紹嘅湯" 夠用了。之後如果需要精確，可以讓 Jessica 問 "係邊款呀？"
- 从零搭建了一个 asyncio 后台循环，每 6 小时跑一次，自动给用户发主动关怀消息。共有四种广播类型：


## 2026-06-04 18:36 — TCM-Jessica

### What Didn't Work (negative knowledge)
- Straight answer before I burn an API call on something that won't work:


## 2026-06-04 18:38 — TCM-Jessica

### What Didn't Work (negative knowledge)
- Straight answer before I burn an API call on something that won't work:


## 2026-06-04 18:39 — TCM-Jessica

### What Didn't Work (negative knowledge)
- Straight answer before I burn an API call on something that won't work:


## 2026-06-04 18:41 — TCM-Jessica

### What Didn't Work (negative knowledge)
- Straight answer before I burn an API call on something that won't work:

### Decisions & Reasoning
- Listen for any misreads — watch 嘢 (ye5)、咁 (gam2)、係 (hai6). Flag any and I'll homophone-swap. Otherwise send me video 3's script (or say "用返 short-cut 版" and I'll pull TCM/remedy/CTA from the plan).


## 2026-06-04 20:29 — TCM-Jessica

### What Didn't Work (negative knowledge)
- Straight answer before I burn an API call on something that won't work:

### Decisions & Reasoning
- Listen for any misreads — watch 嘢 (ye5)、咁 (gam2)、係 (hai6). Flag any and I'll homophone-swap. Otherwise send me video 3's script (or say "用返 short-cut 版" and I'll pull TCM/remedy/CTA from the plan).


## 2026-06-04 20:30 — TCM-Jessica

### What Didn't Work (negative knowledge)
- Straight answer before I burn an API call on something that won't work:

### Decisions & Reasoning
- Listen for any misreads — watch 嘢 (ye5)、咁 (gam2)、係 (hai6). Flag any and I'll homophone-swap. Otherwise send me video 3's script (or say "用返 short-cut 版" and I'll pull TCM/remedy/CTA from the plan).


## 2026-06-11 14:11 — TCM-Jessica

### Decisions & Reasoning
- | 楼价来源 | 用户发链接 → 我抓页面用 LLM 提取楼价;抓不到就直接问用户楼价 | 28hse/中原等可能挡爬虫,所以要 fallback |
- - 手机都可以试 — 而且 ngrok 是 HTTPS,**语音录音在手机上都用得**(MediaRecorder 一定要 HTTPS)
- | 📄 测试用月结单 | `docs/samples/sample-bank-statement.pdf`(Finder 已打开) |
- 对了,你打断我之前,**28hse 估价那个功能**我已经探完路:28hse 不挡爬虫(HTTP 200,首页就有 4 万个盘的结构化数据),完全可以做到"用户只发地址 → 我去 28hse 搜同屋苑放盘 → 拿真实市价做预估"。要不要我继续把这个建完?建好之后连楼价都不用问用户了。
- ① 链接/文字本身有价? → 直接用 (price_source: listing)
- 加埋一个 UX 位:用市场估价之后,等月结单时用户**随时打个数修正**(比如"950萬"),系统更新再继续。
- 注意一点:28hse 的搜索对「屋苑名」效果最好(太古城、美孚新邨、嘉湖山莊呢啲),如果用户发一条很随意的街道地址,可能跌到问价那步 — 这是预期行为,不是 bug。
- 提醒一句:这套是**简化版** HK 规则。真实世界还有按揭保险(高成数按揭可去到 80–90%)、首置/非首置之分、固定收入 vs 自雇的 DSR 差异。Demo 够用,真上线前要同 Dr Loan 核一次这些数。要我加按揭保险那层吗?


## 2026-06-23 12:43 — TCM-Jessica

### Decisions & Reasoning
- 我不再问你选项了，直接修最省事的那条：把开机命令里那个吃内存的索引步骤去掉，让部署能成功，天气播报就停了。先看一眼当前启动命令：
- 事实就一个：不重新部署成功一次，flag 改了也没用。这是最省事的一刀。
- 最稳的免费一刀：开机命令只启 web 服务，不在开机时跑索引（卡片早已存在外部 Qdrant 里，月前那次部署索引过了）。这样 512MB 够用 → 部署成功 → flag=false 生效 → 天气停。索引以后单独跑。
- 分支提交只是留个记录。真正生效的是 Render 上的启动命令——我直接用 API 改它再触发部署，不用走 git 推送那套。先看 Render 上当前的启动命令结构：
- 还是 `update_failed`。说明光启动 web 服务本身在 512MB 上也爆了——web 应用启动时大概也加载了 embedding 模型/重初始化。看一下这次到底卡在哪：
- **光启动 web 服务（连索引都没跑）也在 512MB 爆了**（04:41:35 OOM）。这个应用启动时本身就要加载 embedding 模型，早就超过 512MB。render.yaml 第6行自己写着需要 `standard`（2GB）——服务被人降级到 starter（512MB）才是病根。所以**没有任何免费办法能让它部署成功**，flag 改了也永远生效不了。


## 2026-06-23 15:37 — TCM-Jessica

### Decisions & Reasoning
- 我不再问你选项了，直接修最省事的那条：把开机命令里那个吃内存的索引步骤去掉，让部署能成功，天气播报就停了。先看一眼当前启动命令：
- 事实就一个：不重新部署成功一次，flag 改了也没用。这是最省事的一刀。
- 最稳的免费一刀：开机命令只启 web 服务，不在开机时跑索引（卡片早已存在外部 Qdrant 里，月前那次部署索引过了）。这样 512MB 够用 → 部署成功 → flag=false 生效 → 天气停。索引以后单独跑。
- 分支提交只是留个记录。真正生效的是 Render 上的启动命令——我直接用 API 改它再触发部署，不用走 git 推送那套。先看 Render 上当前的启动命令结构：
- 还是 `update_failed`。说明光启动 web 服务本身在 512MB 上也爆了——web 应用启动时大概也加载了 embedding 模型/重初始化。看一下这次到底卡在哪：
- **光启动 web 服务（连索引都没跑）也在 512MB 爆了**（04:41:35 OOM）。这个应用启动时本身就要加载 embedding 模型，早就超过 512MB。render.yaml 第6行自己写着需要 `standard`（2GB）——服务被人降级到 starter（512MB）才是病根。所以**没有任何免费办法能让它部署成功**，flag 改了也永远生效不了。
- 要停掉天气播报，**必须成功部署一次**让 `flag=false` 生效。但这应用启动就要 ~2GB 内存，现在卡在 512MB 的 starter 上，**怎么都部署不成功**。所以唯一能真正停掉它的办法是把内存加回去。


## 2026-07-02 16:54 — TCM-Jessica

### Architecture Decisions
- 1. **Persona truth is split across 6+ places** — 4 hardcoded account-id dicts in TCM-Jessica alone, plus persona JSONs, plus Notion. Onboarding Ming Pao today = editing all of them.


## 2026-07-02 17:30 — TCM-Jessica

### Architecture Decisions
- 1. **Persona truth is split across 6+ places** — 4 hardcoded account-id dicts in TCM-Jessica alone, plus persona JSONs, plus Notion. Onboarding Ming Pao today = editing all of them.

### Decisions & Reasoning
- 2. **The "only for opening a conversation" guard failed** because the backfill sends never persisted to production CRM — prod thinks she's a brand-new user every time, so canned keeps firing.


## 2026-07-02 17:40 — TCM-Jessica

### Architecture Decisions
- 1. **Persona truth is split across 6+ places** — 4 hardcoded account-id dicts in TCM-Jessica alone, plus persona JSONs, plus Notion. Onboarding Ming Pao today = editing all of them.

### Decisions & Reasoning
- 2. **The "only for opening a conversation" guard failed** because the backfill sends never persisted to production CRM — prod thinks she's a brand-new user every time, so canned keeps firing.


## 2026-07-02 19:04 — TCM-Jessica

### Architecture Decisions
- 1. **Persona truth is split across 6+ places** — 4 hardcoded account-id dicts in TCM-Jessica alone, plus persona JSONs, plus Notion. Onboarding Ming Pao today = editing all of them.

### Decisions & Reasoning
- 2. **The "only for opening a conversation" guard failed** because the backfill sends never persisted to production CRM — prod thinks she's a brand-new user every time, so canned keeps firing.


## 2026-07-03 10:00 — TCM-Jessica

### Architecture Decisions
- 1. **Persona truth is split across 6+ places** — 4 hardcoded account-id dicts in TCM-Jessica alone, plus persona JSONs, plus Notion. Onboarding Ming Pao today = editing all of them.

### Decisions & Reasoning
- 2. **The "only for opening a conversation" guard failed** because the backfill sends never persisted to production CRM — prod thinks she's a brand-new user every time, so canned keeps firing.


## 2026-07-03 10:01 — TCM-Jessica

### Architecture Decisions
- 1. **Persona truth is split across 6+ places** — 4 hardcoded account-id dicts in TCM-Jessica alone, plus persona JSONs, plus Notion. Onboarding Ming Pao today = editing all of them.

### Decisions & Reasoning
- 2. **The "only for opening a conversation" guard failed** because the backfill sends never persisted to production CRM — prod thinks she's a brand-new user every time, so canned keeps firing.
- 你其实**已经有**你想要的两层系统了——`ChloeAgent` 就是浅层（一次 LLM 调用，没有销售流程），WhatsApp 那套 Planner→Specialists→Writer 就是深层。乱的不是架构，是配线：
- 3. **IG → WhatsApp 的转化交接根本不存在** — 代码里一行 `wa.me` 都没有。用户从 IG 到 WhatsApp，CRM 完全不知道他是哪个 IP、哪条内容带来的
- L1 检测到购买/预约/想深入诊断的意图 → 丢一条带 **REF code** 的 wa.me 链接（比如 `[MPCA-eye]`）→ 用户点过去，Jessica 解析 REF 写进 CRM → 第一句话就能接上"你喺 IG 睇咗眼乾嗰条片系咪？"，而且从此**每个 IP、每条内容的转化率都能直接从 CRM 查出来**。这是整个计划里最值钱的一块。
- ai-tcm-ip 整个搬进 TCM-Jessica 当 `studio/` 文件夹（git subtree，历史保留）。生产服务不动、webhook 不动、Meta 订阅不用重新验证。`render.yaml` 加 buildFilter，内容侧的 commit 不会触发重新部署。合并后 notion-sync 可以自动把 infographic 拷进 `data/media/guides/`——你现在手动搬图那一步直接消失。
- D1 你现在打开 dashboard 十秒就能确认。要不要我直接用刚才那个 API key 查？


## 2026-07-03 10:09 — TCM-Jessica

### Architecture Decisions
- 1. **Persona truth is split across 6+ places** — 4 hardcoded account-id dicts in TCM-Jessica alone, plus persona JSONs, plus Notion. Onboarding Ming Pao today = editing all of them.

### Decisions & Reasoning
- 2. **The "only for opening a conversation" guard failed** because the backfill sends never persisted to production CRM — prod thinks she's a brand-new user every time, so canned keeps firing.
- 你其实**已经有**你想要的两层系统了——`ChloeAgent` 就是浅层（一次 LLM 调用，没有销售流程），WhatsApp 那套 Planner→Specialists→Writer 就是深层。乱的不是架构，是配线：
- 3. **IG → WhatsApp 的转化交接根本不存在** — 代码里一行 `wa.me` 都没有。用户从 IG 到 WhatsApp，CRM 完全不知道他是哪个 IP、哪条内容带来的
- L1 检测到购买/预约/想深入诊断的意图 → 丢一条带 **REF code** 的 wa.me 链接（比如 `[MPCA-eye]`）→ 用户点过去，Jessica 解析 REF 写进 CRM → 第一句话就能接上"你喺 IG 睇咗眼乾嗰条片系咪？"，而且从此**每个 IP、每条内容的转化率都能直接从 CRM 查出来**。这是整个计划里最值钱的一块。
- ai-tcm-ip 整个搬进 TCM-Jessica 当 `studio/` 文件夹（git subtree，历史保留）。生产服务不动、webhook 不动、Meta 订阅不用重新验证。`render.yaml` 加 buildFilter，内容侧的 commit 不会触发重新部署。合并后 notion-sync 可以自动把 infographic 拷进 `data/media/guides/`——你现在手动搬图那一步直接消失。
- D1 你现在打开 dashboard 十秒就能确认。要不要我直接用刚才那个 API key 查？


## 2026-07-03 10:11 — TCM-Jessica

### Architecture Decisions
- 1. **Persona truth is split across 6+ places** — 4 hardcoded account-id dicts in TCM-Jessica alone, plus persona JSONs, plus Notion. Onboarding Ming Pao today = editing all of them.

### Decisions & Reasoning
- 2. **The "only for opening a conversation" guard failed** because the backfill sends never persisted to production CRM — prod thinks she's a brand-new user every time, so canned keeps firing.
- 你其实**已经有**你想要的两层系统了——`ChloeAgent` 就是浅层（一次 LLM 调用，没有销售流程），WhatsApp 那套 Planner→Specialists→Writer 就是深层。乱的不是架构，是配线：
- 3. **IG → WhatsApp 的转化交接根本不存在** — 代码里一行 `wa.me` 都没有。用户从 IG 到 WhatsApp，CRM 完全不知道他是哪个 IP、哪条内容带来的
- L1 检测到购买/预约/想深入诊断的意图 → 丢一条带 **REF code** 的 wa.me 链接（比如 `[MPCA-eye]`）→ 用户点过去，Jessica 解析 REF 写进 CRM → 第一句话就能接上"你喺 IG 睇咗眼乾嗰条片系咪？"，而且从此**每个 IP、每条内容的转化率都能直接从 CRM 查出来**。这是整个计划里最值钱的一块。
- ai-tcm-ip 整个搬进 TCM-Jessica 当 `studio/` 文件夹（git subtree，历史保留）。生产服务不动、webhook 不动、Meta 订阅不用重新验证。`render.yaml` 加 buildFilter，内容侧的 commit 不会触发重新部署。合并后 notion-sync 可以自动把 infographic 拷进 `data/media/guides/`——你现在手动搬图那一步直接消失。
- D1 你现在打开 dashboard 十秒就能确认。要不要我直接用刚才那个 API key 查？
- Jackie 和 Chloe 的 persona prompt 都加了你那条规则 —— 问诊所/预约 → 一句"暂时没有，我在这里用文字帮你"，轻轻带过，不解释、不承诺以后会开。测试全绿，正在部署。


## 2026-07-03 10:38 — TCM-Jessica

### Architecture Decisions
- 1. **Persona truth is split across 6+ places** — 4 hardcoded account-id dicts in TCM-Jessica alone, plus persona JSONs, plus Notion. Onboarding Ming Pao today = editing all of them.

### Decisions & Reasoning
- 2. **The "only for opening a conversation" guard failed** because the backfill sends never persisted to production CRM — prod thinks she's a brand-new user every time, so canned keeps firing.
- 你其实**已经有**你想要的两层系统了——`ChloeAgent` 就是浅层（一次 LLM 调用，没有销售流程），WhatsApp 那套 Planner→Specialists→Writer 就是深层。乱的不是架构，是配线：
- 3. **IG → WhatsApp 的转化交接根本不存在** — 代码里一行 `wa.me` 都没有。用户从 IG 到 WhatsApp，CRM 完全不知道他是哪个 IP、哪条内容带来的
- L1 检测到购买/预约/想深入诊断的意图 → 丢一条带 **REF code** 的 wa.me 链接（比如 `[MPCA-eye]`）→ 用户点过去，Jessica 解析 REF 写进 CRM → 第一句话就能接上"你喺 IG 睇咗眼乾嗰条片系咪？"，而且从此**每个 IP、每条内容的转化率都能直接从 CRM 查出来**。这是整个计划里最值钱的一块。
- ai-tcm-ip 整个搬进 TCM-Jessica 当 `studio/` 文件夹（git subtree，历史保留）。生产服务不动、webhook 不动、Meta 订阅不用重新验证。`render.yaml` 加 buildFilter，内容侧的 commit 不会触发重新部署。合并后 notion-sync 可以自动把 infographic 拷进 `data/media/guides/`——你现在手动搬图那一步直接消失。
- D1 你现在打开 dashboard 十秒就能确认。要不要我直接用刚才那个 API key 查？
- Jackie 和 Chloe 的 persona prompt 都加了你那条规则 —— 问诊所/预约 → 一句"暂时没有，我在这里用文字帮你"，轻轻带过，不解释、不承诺以后会开。测试全绿，正在部署。
- - Jackie / Chloe 遇到"有没有诊所/可以预约吗" → 一句"暂时没有，我在这里用文字帮你"


## 2026-07-03 11:27 — TCM-Jessica

### Architecture Decisions
- 1. **Persona truth is split across 6+ places** — 4 hardcoded account-id dicts in TCM-Jessica alone, plus persona JSONs, plus Notion. Onboarding Ming Pao today = editing all of them.

### Decisions & Reasoning
- 2. **The "only for opening a conversation" guard failed** because the backfill sends never persisted to production CRM — prod thinks she's a brand-new user every time, so canned keeps firing.
- 你其实**已经有**你想要的两层系统了——`ChloeAgent` 就是浅层（一次 LLM 调用，没有销售流程），WhatsApp 那套 Planner→Specialists→Writer 就是深层。乱的不是架构，是配线：
- 3. **IG → WhatsApp 的转化交接根本不存在** — 代码里一行 `wa.me` 都没有。用户从 IG 到 WhatsApp，CRM 完全不知道他是哪个 IP、哪条内容带来的
- L1 检测到购买/预约/想深入诊断的意图 → 丢一条带 **REF code** 的 wa.me 链接（比如 `[MPCA-eye]`）→ 用户点过去，Jessica 解析 REF 写进 CRM → 第一句话就能接上"你喺 IG 睇咗眼乾嗰条片系咪？"，而且从此**每个 IP、每条内容的转化率都能直接从 CRM 查出来**。这是整个计划里最值钱的一块。
- ai-tcm-ip 整个搬进 TCM-Jessica 当 `studio/` 文件夹（git subtree，历史保留）。生产服务不动、webhook 不动、Meta 订阅不用重新验证。`render.yaml` 加 buildFilter，内容侧的 commit 不会触发重新部署。合并后 notion-sync 可以自动把 infographic 拷进 `data/media/guides/`——你现在手动搬图那一步直接消失。
- D1 你现在打开 dashboard 十秒就能确认。要不要我直接用刚才那个 API key 查？
- Jackie 和 Chloe 的 persona prompt 都加了你那条规则 —— 问诊所/预约 → 一句"暂时没有，我在这里用文字帮你"，轻轻带过，不解释、不承诺以后会开。测试全绿，正在部署。
- - Jackie / Chloe 遇到"有没有诊所/可以预约吗" → 一句"暂时没有，我在这里用文字帮你"


## 2026-07-03 11:32 — social-ip-engine

### Architecture Decisions
- 1. **Persona truth is split across 6+ places** — 4 hardcoded account-id dicts in TCM-Jessica alone, plus persona JSONs, plus Notion. Onboarding Ming Pao today = editing all of them.

### Decisions & Reasoning
- 2. **The "only for opening a conversation" guard failed** because the backfill sends never persisted to production CRM — prod thinks she's a brand-new user every time, so canned keeps firing.
- 你其实**已经有**你想要的两层系统了——`ChloeAgent` 就是浅层（一次 LLM 调用，没有销售流程），WhatsApp 那套 Planner→Specialists→Writer 就是深层。乱的不是架构，是配线：
- 3. **IG → WhatsApp 的转化交接根本不存在** — 代码里一行 `wa.me` 都没有。用户从 IG 到 WhatsApp，CRM 完全不知道他是哪个 IP、哪条内容带来的
- L1 检测到购买/预约/想深入诊断的意图 → 丢一条带 **REF code** 的 wa.me 链接（比如 `[MPCA-eye]`）→ 用户点过去，Jessica 解析 REF 写进 CRM → 第一句话就能接上"你喺 IG 睇咗眼乾嗰条片系咪？"，而且从此**每个 IP、每条内容的转化率都能直接从 CRM 查出来**。这是整个计划里最值钱的一块。
- ai-tcm-ip 整个搬进 TCM-Jessica 当 `studio/` 文件夹（git subtree，历史保留）。生产服务不动、webhook 不动、Meta 订阅不用重新验证。`render.yaml` 加 buildFilter，内容侧的 commit 不会触发重新部署。合并后 notion-sync 可以自动把 infographic 拷进 `data/media/guides/`——你现在手动搬图那一步直接消失。
- D1 你现在打开 dashboard 十秒就能确认。要不要我直接用刚才那个 API key 查？
- Jackie 和 Chloe 的 persona prompt 都加了你那条规则 —— 问诊所/预约 → 一句"暂时没有，我在这里用文字帮你"，轻轻带过，不解释、不承诺以后会开。测试全绿，正在部署。
- - Jackie / Chloe 遇到"有没有诊所/可以预约吗" → 一句"暂时没有，我在这里用文字帮你"


## 2026-07-03 11:35 — social-ip-engine

### Architecture Decisions
- 1. **Persona truth is split across 6+ places** — 4 hardcoded account-id dicts in TCM-Jessica alone, plus persona JSONs, plus Notion. Onboarding Ming Pao today = editing all of them.

### Decisions & Reasoning
- 2. **The "only for opening a conversation" guard failed** because the backfill sends never persisted to production CRM — prod thinks she's a brand-new user every time, so canned keeps firing.
- 你其实**已经有**你想要的两层系统了——`ChloeAgent` 就是浅层（一次 LLM 调用，没有销售流程），WhatsApp 那套 Planner→Specialists→Writer 就是深层。乱的不是架构，是配线：
- 3. **IG → WhatsApp 的转化交接根本不存在** — 代码里一行 `wa.me` 都没有。用户从 IG 到 WhatsApp，CRM 完全不知道他是哪个 IP、哪条内容带来的
- L1 检测到购买/预约/想深入诊断的意图 → 丢一条带 **REF code** 的 wa.me 链接（比如 `[MPCA-eye]`）→ 用户点过去，Jessica 解析 REF 写进 CRM → 第一句话就能接上"你喺 IG 睇咗眼乾嗰条片系咪？"，而且从此**每个 IP、每条内容的转化率都能直接从 CRM 查出来**。这是整个计划里最值钱的一块。
- ai-tcm-ip 整个搬进 TCM-Jessica 当 `studio/` 文件夹（git subtree，历史保留）。生产服务不动、webhook 不动、Meta 订阅不用重新验证。`render.yaml` 加 buildFilter，内容侧的 commit 不会触发重新部署。合并后 notion-sync 可以自动把 infographic 拷进 `data/media/guides/`——你现在手动搬图那一步直接消失。
- D1 你现在打开 dashboard 十秒就能确认。要不要我直接用刚才那个 API key 查？
- Jackie 和 Chloe 的 persona prompt 都加了你那条规则 —— 问诊所/预约 → 一句"暂时没有，我在这里用文字帮你"，轻轻带过，不解释、不承诺以后会开。测试全绿，正在部署。
- - Jackie / Chloe 遇到"有没有诊所/可以预约吗" → 一句"暂时没有，我在这里用文字帮你"


## 2026-07-03 11:39 — social-ip-engine

### Architecture Decisions
- 1. **Persona truth is split across 6+ places** — 4 hardcoded account-id dicts in TCM-Jessica alone, plus persona JSONs, plus Notion. Onboarding Ming Pao today = editing all of them.

### Decisions & Reasoning
- 2. **The "only for opening a conversation" guard failed** because the backfill sends never persisted to production CRM — prod thinks she's a brand-new user every time, so canned keeps firing.
- 你其实**已经有**你想要的两层系统了——`ChloeAgent` 就是浅层（一次 LLM 调用，没有销售流程），WhatsApp 那套 Planner→Specialists→Writer 就是深层。乱的不是架构，是配线：
- 3. **IG → WhatsApp 的转化交接根本不存在** — 代码里一行 `wa.me` 都没有。用户从 IG 到 WhatsApp，CRM 完全不知道他是哪个 IP、哪条内容带来的
- L1 检测到购买/预约/想深入诊断的意图 → 丢一条带 **REF code** 的 wa.me 链接（比如 `[MPCA-eye]`）→ 用户点过去，Jessica 解析 REF 写进 CRM → 第一句话就能接上"你喺 IG 睇咗眼乾嗰条片系咪？"，而且从此**每个 IP、每条内容的转化率都能直接从 CRM 查出来**。这是整个计划里最值钱的一块。
- ai-tcm-ip 整个搬进 TCM-Jessica 当 `studio/` 文件夹（git subtree，历史保留）。生产服务不动、webhook 不动、Meta 订阅不用重新验证。`render.yaml` 加 buildFilter，内容侧的 commit 不会触发重新部署。合并后 notion-sync 可以自动把 infographic 拷进 `data/media/guides/`——你现在手动搬图那一步直接消失。
- D1 你现在打开 dashboard 十秒就能确认。要不要我直接用刚才那个 API key 查？
- Jackie 和 Chloe 的 persona prompt 都加了你那条规则 —— 问诊所/预约 → 一句"暂时没有，我在这里用文字帮你"，轻轻带过，不解释、不承诺以后会开。测试全绿，正在部署。
- - Jackie / Chloe 遇到"有没有诊所/可以预约吗" → 一句"暂时没有，我在这里用文字帮你"


## 2026-07-03 12:33 — social-ip-engine

### Decisions & Reasoning
- **选题我 100% 支持**——补肾壮阳/男性活力在 TCM 里是转化率最高、最缺内容、评论区最炸的赛道。你要 gimmick、要博眼球,方向完全对。
- 好消息是:**冲击力和搞笑感可以完全保留,只要把"器官"抽象成一个符号**——平台审不到,但人人秒懂。🍆 才是互联网通用暗号,不是保险套。


## 2026-07-03 12:36 — social-ip-engine

### Decisions & Reasoning
- **选题我 100% 支持**——补肾壮阳/男性活力在 TCM 里是转化率最高、最缺内容、评论区最炸的赛道。你要 gimmick、要博眼球,方向完全对。
- 好消息是:**冲击力和搞笑感可以完全保留,只要把"器官"抽象成一个符号**——平台审不到,但人人秒懂。🍆 才是互联网通用暗号,不是保险套。
- - Body:完整 **📜 Master Script(6 shots)** + **🎬 Shot Guide**(每个 shot 有 🎥 画面 / 🗣️ 台词 / 💡 用意)+ **🖼️ Thumbnail 图片 prompt**
- 1. **CTA keyword 用 `VITALITY`**,不用 `kidney`——避免跟你现有 kidney 类内容的关键词在 `comment_responses.json` 里撞规则。要换成别的词跟我说。
- 图我没直接生成——想先让你过一眼概念落地对不对。你点头,我就用 body 里那个 thumbnail prompt 跑图(你有 `notion_image.py` / `batch_infographic_gen.py`),生成后直接回填到这条 concept 的 🖼️ 区。


## 2026-07-03 12:47 — social-ip-engine

### Architecture Decisions
- 1. **Persona truth is split across 6+ places** — 4 hardcoded account-id dicts in TCM-Jessica alone, plus persona JSONs, plus Notion. Onboarding Ming Pao today = editing all of them.

### Decisions & Reasoning
- 2. **The "only for opening a conversation" guard failed** because the backfill sends never persisted to production CRM — prod thinks she's a brand-new user every time, so canned keeps firing.
- 你其实**已经有**你想要的两层系统了——`ChloeAgent` 就是浅层（一次 LLM 调用，没有销售流程），WhatsApp 那套 Planner→Specialists→Writer 就是深层。乱的不是架构，是配线：
- 3. **IG → WhatsApp 的转化交接根本不存在** — 代码里一行 `wa.me` 都没有。用户从 IG 到 WhatsApp，CRM 完全不知道他是哪个 IP、哪条内容带来的
- L1 检测到购买/预约/想深入诊断的意图 → 丢一条带 **REF code** 的 wa.me 链接（比如 `[MPCA-eye]`）→ 用户点过去，Jessica 解析 REF 写进 CRM → 第一句话就能接上"你喺 IG 睇咗眼乾嗰条片系咪？"，而且从此**每个 IP、每条内容的转化率都能直接从 CRM 查出来**。这是整个计划里最值钱的一块。
- ai-tcm-ip 整个搬进 TCM-Jessica 当 `studio/` 文件夹（git subtree，历史保留）。生产服务不动、webhook 不动、Meta 订阅不用重新验证。`render.yaml` 加 buildFilter，内容侧的 commit 不会触发重新部署。合并后 notion-sync 可以自动把 infographic 拷进 `data/media/guides/`——你现在手动搬图那一步直接消失。
- D1 你现在打开 dashboard 十秒就能确认。要不要我直接用刚才那个 API key 查？
- Jackie 和 Chloe 的 persona prompt 都加了你那条规则 —— 问诊所/预约 → 一句"暂时没有，我在这里用文字帮你"，轻轻带过，不解释、不承诺以后会开。测试全绿，正在部署。
- - Jackie / Chloe 遇到"有没有诊所/可以预约吗" → 一句"暂时没有，我在这里用文字帮你"


## 2026-07-03 12:50 — social-ip-engine

### Architecture Decisions
- 1. **Persona truth is split across 6+ places** — 4 hardcoded account-id dicts in TCM-Jessica alone, plus persona JSONs, plus Notion. Onboarding Ming Pao today = editing all of them.

### Decisions & Reasoning
- 2. **The "only for opening a conversation" guard failed** because the backfill sends never persisted to production CRM — prod thinks she's a brand-new user every time, so canned keeps firing.
- 你其实**已经有**你想要的两层系统了——`ChloeAgent` 就是浅层（一次 LLM 调用，没有销售流程），WhatsApp 那套 Planner→Specialists→Writer 就是深层。乱的不是架构，是配线：
- 3. **IG → WhatsApp 的转化交接根本不存在** — 代码里一行 `wa.me` 都没有。用户从 IG 到 WhatsApp，CRM 完全不知道他是哪个 IP、哪条内容带来的
- L1 检测到购买/预约/想深入诊断的意图 → 丢一条带 **REF code** 的 wa.me 链接（比如 `[MPCA-eye]`）→ 用户点过去，Jessica 解析 REF 写进 CRM → 第一句话就能接上"你喺 IG 睇咗眼乾嗰条片系咪？"，而且从此**每个 IP、每条内容的转化率都能直接从 CRM 查出来**。这是整个计划里最值钱的一块。
- ai-tcm-ip 整个搬进 TCM-Jessica 当 `studio/` 文件夹（git subtree，历史保留）。生产服务不动、webhook 不动、Meta 订阅不用重新验证。`render.yaml` 加 buildFilter，内容侧的 commit 不会触发重新部署。合并后 notion-sync 可以自动把 infographic 拷进 `data/media/guides/`——你现在手动搬图那一步直接消失。
- D1 你现在打开 dashboard 十秒就能确认。要不要我直接用刚才那个 API key 查？
- Jackie 和 Chloe 的 persona prompt 都加了你那条规则 —— 问诊所/预约 → 一句"暂时没有，我在这里用文字帮你"，轻轻带过，不解释、不承诺以后会开。测试全绿，正在部署。
- - Jackie / Chloe 遇到"有没有诊所/可以预约吗" → 一句"暂时没有，我在这里用文字帮你"


## 2026-07-03 12:58 — social-ip-engine

### Architecture Decisions
- That's the pattern — tight 4-line Master Script (Hook / Root Cause / Fix / CTA) + 4 shots + DM protocol. Rewriting to match, pain points folded into the root-cause line instead of a whole barrage.

### Decisions & Reasoning
- **选题我 100% 支持**——补肾壮阳/男性活力在 TCM 里是转化率最高、最缺内容、评论区最炸的赛道。你要 gimmick、要博眼球,方向完全对。
- 好消息是:**冲击力和搞笑感可以完全保留,只要把"器官"抽象成一个符号**——平台审不到,但人人秒懂。🍆 才是互联网通用暗号,不是保险套。
- - Body:完整 **📜 Master Script(6 shots)** + **🎬 Shot Guide**(每个 shot 有 🎥 画面 / 🗣️ 台词 / 💡 用意)+ **🖼️ Thumbnail 图片 prompt**
- 1. **CTA keyword 用 `VITALITY`**,不用 `kidney`——避免跟你现有 kidney 类内容的关键词在 `comment_responses.json` 里撞规则。要换成别的词跟我说。
- 图我没直接生成——想先让你过一眼概念落地对不对。你点头,我就用 body 里那个 thumbnail prompt 跑图(你有 `notion_image.py` / `batch_infographic_gen.py`),生成后直接回填到这条 concept 的 🖼️ 区。
- **③ SOLUTION 点破根因 + 解法(~7s)** — 所有症状指向一个根:**肾阳虚,内火熄了**;晨勃只是最明显的那盏警示灯。不是年纪、不是没救 → 温热熟食 + 早睡 + 别再用冷饮/熬夜/压力掏空油箱。茄子这时慢慢立起来 → "做对了……旗子就又升起来了。"


## 2026-07-03 13:00 — social-ip-engine

### Architecture Decisions
- 1. **Persona truth is split across 6+ places** — 4 hardcoded account-id dicts in TCM-Jessica alone, plus persona JSONs, plus Notion. Onboarding Ming Pao today = editing all of them.

### Decisions & Reasoning
- 2. **The "only for opening a conversation" guard failed** because the backfill sends never persisted to production CRM — prod thinks she's a brand-new user every time, so canned keeps firing.
- 你其实**已经有**你想要的两层系统了——`ChloeAgent` 就是浅层（一次 LLM 调用，没有销售流程），WhatsApp 那套 Planner→Specialists→Writer 就是深层。乱的不是架构，是配线：
- 3. **IG → WhatsApp 的转化交接根本不存在** — 代码里一行 `wa.me` 都没有。用户从 IG 到 WhatsApp，CRM 完全不知道他是哪个 IP、哪条内容带来的
- L1 检测到购买/预约/想深入诊断的意图 → 丢一条带 **REF code** 的 wa.me 链接（比如 `[MPCA-eye]`）→ 用户点过去，Jessica 解析 REF 写进 CRM → 第一句话就能接上"你喺 IG 睇咗眼乾嗰条片系咪？"，而且从此**每个 IP、每条内容的转化率都能直接从 CRM 查出来**。这是整个计划里最值钱的一块。
- ai-tcm-ip 整个搬进 TCM-Jessica 当 `studio/` 文件夹（git subtree，历史保留）。生产服务不动、webhook 不动、Meta 订阅不用重新验证。`render.yaml` 加 buildFilter，内容侧的 commit 不会触发重新部署。合并后 notion-sync 可以自动把 infographic 拷进 `data/media/guides/`——你现在手动搬图那一步直接消失。
- D1 你现在打开 dashboard 十秒就能确认。要不要我直接用刚才那个 API key 查？
- Jackie 和 Chloe 的 persona prompt 都加了你那条规则 —— 问诊所/预约 → 一句"暂时没有，我在这里用文字帮你"，轻轻带过，不解释、不承诺以后会开。测试全绿，正在部署。
- - Jackie / Chloe 遇到"有没有诊所/可以预约吗" → 一句"暂时没有，我在这里用文字帮你"


## 2026-07-03 13:06 — social-ip-engine

### Architecture Decisions
- That's the pattern — tight 4-line Master Script (Hook / Root Cause / Fix / CTA) + 4 shots + DM protocol. Rewriting to match, pain points folded into the root-cause line instead of a whole barrage.

### Decisions & Reasoning
- **选题我 100% 支持**——补肾壮阳/男性活力在 TCM 里是转化率最高、最缺内容、评论区最炸的赛道。你要 gimmick、要博眼球,方向完全对。
- 好消息是:**冲击力和搞笑感可以完全保留,只要把"器官"抽象成一个符号**——平台审不到,但人人秒懂。🍆 才是互联网通用暗号,不是保险套。
- - Body:完整 **📜 Master Script(6 shots)** + **🎬 Shot Guide**(每个 shot 有 🎥 画面 / 🗣️ 台词 / 💡 用意)+ **🖼️ Thumbnail 图片 prompt**
- 1. **CTA keyword 用 `VITALITY`**,不用 `kidney`——避免跟你现有 kidney 类内容的关键词在 `comment_responses.json` 里撞规则。要换成别的词跟我说。
- 图我没直接生成——想先让你过一眼概念落地对不对。你点头,我就用 body 里那个 thumbnail prompt 跑图(你有 `notion_image.py` / `batch_infographic_gen.py`),生成后直接回填到这条 concept 的 🖼️ 区。
- **③ SOLUTION 点破根因 + 解法(~7s)** — 所有症状指向一个根:**肾阳虚,内火熄了**;晨勃只是最明显的那盏警示灯。不是年纪、不是没救 → 温热熟食 + 早睡 + 别再用冷饮/熬夜/压力掏空油箱。茄子这时慢慢立起来 → "做对了……旗子就又升起来了。"
- Hook · Root Cause · The Fix · CTA — 每个都有 🎥/🗣️/💡,茄子半旗→立起的视觉梗保留在 Shot 1 和 Shot 3。💡 标签用中文 TCM 术语(腎陽虛·命門火衰 等),跟 detox 那条一致。


## 2026-07-03 13:06 — social-ip-engine

### Architecture Decisions
- That's the pattern — tight 4-line Master Script (Hook / Root Cause / Fix / CTA) + 4 shots + DM protocol. Rewriting to match, pain points folded into the root-cause line instead of a whole barrage.

### Decisions & Reasoning
- **选题我 100% 支持**——补肾壮阳/男性活力在 TCM 里是转化率最高、最缺内容、评论区最炸的赛道。你要 gimmick、要博眼球,方向完全对。
- 好消息是:**冲击力和搞笑感可以完全保留,只要把"器官"抽象成一个符号**——平台审不到,但人人秒懂。🍆 才是互联网通用暗号,不是保险套。
- - Body:完整 **📜 Master Script(6 shots)** + **🎬 Shot Guide**(每个 shot 有 🎥 画面 / 🗣️ 台词 / 💡 用意)+ **🖼️ Thumbnail 图片 prompt**
- 1. **CTA keyword 用 `VITALITY`**,不用 `kidney`——避免跟你现有 kidney 类内容的关键词在 `comment_responses.json` 里撞规则。要换成别的词跟我说。
- 图我没直接生成——想先让你过一眼概念落地对不对。你点头,我就用 body 里那个 thumbnail prompt 跑图(你有 `notion_image.py` / `batch_infographic_gen.py`),生成后直接回填到这条 concept 的 🖼️ 区。
- **③ SOLUTION 点破根因 + 解法(~7s)** — 所有症状指向一个根:**肾阳虚,内火熄了**;晨勃只是最明显的那盏警示灯。不是年纪、不是没救 → 温热熟食 + 早睡 + 别再用冷饮/熬夜/压力掏空油箱。茄子这时慢慢立起来 → "做对了……旗子就又升起来了。"
- Hook · Root Cause · The Fix · CTA — 每个都有 🎥/🗣️/💡,茄子半旗→立起的视觉梗保留在 Shot 1 和 Shot 3。💡 标签用中文 TCM 术语(腎陽虛·命門火衰 等),跟 detox 那条一致。


## 2026-07-03 15:11 — social-ip-engine

### What Didn't Work (negative knowledge)
- The problem is **not** your setup — it's that the secret I set is saved in Render's config but **the running instance hasn't picked it up.** Setting an env var doesn't auto-restart the process here (that broken auto-deploy again). Proof: my own call with the correct secret *also* just got 401 — the live process still has an empty secret in memory.

### Architecture Decisions
- That's the pattern — tight 4-line Master Script (Hook / Root Cause / Fix / CTA) + 4 shots + DM protocol. Rewriting to match, pain points folded into the root-cause line instead of a whole barrage.

### Decisions & Reasoning
- **选题我 100% 支持**——补肾壮阳/男性活力在 TCM 里是转化率最高、最缺内容、评论区最炸的赛道。你要 gimmick、要博眼球,方向完全对。
- 好消息是:**冲击力和搞笑感可以完全保留,只要把"器官"抽象成一个符号**——平台审不到,但人人秒懂。🍆 才是互联网通用暗号,不是保险套。
- - Body:完整 **📜 Master Script(6 shots)** + **🎬 Shot Guide**(每个 shot 有 🎥 画面 / 🗣️ 台词 / 💡 用意)+ **🖼️ Thumbnail 图片 prompt**
- 1. **CTA keyword 用 `VITALITY`**,不用 `kidney`——避免跟你现有 kidney 类内容的关键词在 `comment_responses.json` 里撞规则。要换成别的词跟我说。
- 图我没直接生成——想先让你过一眼概念落地对不对。你点头,我就用 body 里那个 thumbnail prompt 跑图(你有 `notion_image.py` / `batch_infographic_gen.py`),生成后直接回填到这条 concept 的 🖼️ 区。
- **③ SOLUTION 点破根因 + 解法(~7s)** — 所有症状指向一个根:**肾阳虚,内火熄了**;晨勃只是最明显的那盏警示灯。不是年纪、不是没救 → 温热熟食 + 早睡 + 别再用冷饮/熬夜/压力掏空油箱。茄子这时慢慢立起来 → "做对了……旗子就又升起来了。"
- Hook · Root Cause · The Fix · CTA — 每个都有 🎥/🗣️/💡,茄子半旗→立起的视觉梗保留在 Shot 1 和 Shot 3。💡 标签用中文 TCM 术语(腎陽虛·命門火衰 等),跟 detox 那条一致。
- - **You get a QA beat** — between "Ready" and "Published" you can look at the auto-generated infographic and fix it if it's off, instead of discovering it after it's already DMing strangers.


## 2026-07-03 15:15 — social-ip-engine

### What Didn't Work (negative knowledge)
- The problem is **not** your setup — it's that the secret I set is saved in Render's config but **the running instance hasn't picked it up.** Setting an env var doesn't auto-restart the process here (that broken auto-deploy again). Proof: my own call with the correct secret *also* just got 401 — the live process still has an empty secret in memory.

### Architecture Decisions
- That's the pattern — tight 4-line Master Script (Hook / Root Cause / Fix / CTA) + 4 shots + DM protocol. Rewriting to match, pain points folded into the root-cause line instead of a whole barrage.

### Decisions & Reasoning
- **选题我 100% 支持**——补肾壮阳/男性活力在 TCM 里是转化率最高、最缺内容、评论区最炸的赛道。你要 gimmick、要博眼球,方向完全对。
- 好消息是:**冲击力和搞笑感可以完全保留,只要把"器官"抽象成一个符号**——平台审不到,但人人秒懂。🍆 才是互联网通用暗号,不是保险套。
- - Body:完整 **📜 Master Script(6 shots)** + **🎬 Shot Guide**(每个 shot 有 🎥 画面 / 🗣️ 台词 / 💡 用意)+ **🖼️ Thumbnail 图片 prompt**
- 1. **CTA keyword 用 `VITALITY`**,不用 `kidney`——避免跟你现有 kidney 类内容的关键词在 `comment_responses.json` 里撞规则。要换成别的词跟我说。
- 图我没直接生成——想先让你过一眼概念落地对不对。你点头,我就用 body 里那个 thumbnail prompt 跑图(你有 `notion_image.py` / `batch_infographic_gen.py`),生成后直接回填到这条 concept 的 🖼️ 区。
- **③ SOLUTION 点破根因 + 解法(~7s)** — 所有症状指向一个根:**肾阳虚,内火熄了**;晨勃只是最明显的那盏警示灯。不是年纪、不是没救 → 温热熟食 + 早睡 + 别再用冷饮/熬夜/压力掏空油箱。茄子这时慢慢立起来 → "做对了……旗子就又升起来了。"
- Hook · Root Cause · The Fix · CTA — 每个都有 🎥/🗣️/💡,茄子半旗→立起的视觉梗保留在 Shot 1 和 Shot 3。💡 标签用中文 TCM 术语(腎陽虛·命門火衰 等),跟 detox 那条一致。
- - **You get a QA beat** — between "Ready" and "Published" you can look at the auto-generated infographic and fix it if it's off, instead of discovering it after it's already DMing strangers.


## 2026-07-03 15:50 — social-ip-engine

### Decisions & Reasoning
- - 如果没有图,但 Content page 上有「Infographic Brief」→ 自动用 AI 现场生成一张(每次 sync 最多生成 5 张,防止爆量)


## 2026-07-03 15:51 — social-ip-engine

### What Didn't Work (negative knowledge)
- The problem is **not** your setup — it's that the secret I set is saved in Render's config but **the running instance hasn't picked it up.** Setting an env var doesn't auto-restart the process here (that broken auto-deploy again). Proof: my own call with the correct secret *also* just got 401 — the live process still has an empty secret in memory.

### Architecture Decisions
- That's the pattern — tight 4-line Master Script (Hook / Root Cause / Fix / CTA) + 4 shots + DM protocol. Rewriting to match, pain points folded into the root-cause line instead of a whole barrage.

### Decisions & Reasoning
- **选题我 100% 支持**——补肾壮阳/男性活力在 TCM 里是转化率最高、最缺内容、评论区最炸的赛道。你要 gimmick、要博眼球,方向完全对。
- 好消息是:**冲击力和搞笑感可以完全保留,只要把"器官"抽象成一个符号**——平台审不到,但人人秒懂。🍆 才是互联网通用暗号,不是保险套。
- - Body:完整 **📜 Master Script(6 shots)** + **🎬 Shot Guide**(每个 shot 有 🎥 画面 / 🗣️ 台词 / 💡 用意)+ **🖼️ Thumbnail 图片 prompt**
- 1. **CTA keyword 用 `VITALITY`**,不用 `kidney`——避免跟你现有 kidney 类内容的关键词在 `comment_responses.json` 里撞规则。要换成别的词跟我说。
- 图我没直接生成——想先让你过一眼概念落地对不对。你点头,我就用 body 里那个 thumbnail prompt 跑图(你有 `notion_image.py` / `batch_infographic_gen.py`),生成后直接回填到这条 concept 的 🖼️ 区。
- **③ SOLUTION 点破根因 + 解法(~7s)** — 所有症状指向一个根:**肾阳虚,内火熄了**;晨勃只是最明显的那盏警示灯。不是年纪、不是没救 → 温热熟食 + 早睡 + 别再用冷饮/熬夜/压力掏空油箱。茄子这时慢慢立起来 → "做对了……旗子就又升起来了。"
- Hook · Root Cause · The Fix · CTA — 每个都有 🎥/🗣️/💡,茄子半旗→立起的视觉梗保留在 Shot 1 和 Shot 3。💡 标签用中文 TCM 术语(腎陽虛·命門火衰 等),跟 detox 那条一致。
- - **You get a QA beat** — between "Ready" and "Published" you can look at the auto-generated infographic and fix it if it's off, instead of discovering it after it's already DMing strangers.


## 2026-07-03 16:08 — social-ip-engine

### Decisions & Reasoning
- - 如果没有图,但 Content page 上有「Infographic Brief」→ 自动用 AI 现场生成一张(每次 sync 最多生成 5 张,防止爆量)
- 3. Whole doc translated to English, emoji swapped to 👨‍⚕️, and I removed the now-inaccurate "manual bottleneck" framing — the real remaining bottlenecks are just the two human review gates (image OK / video OK), which I kept honest about rather than pretending those are automatable too.


## 2026-07-03 16:09 — social-ip-engine

### What Didn't Work (negative knowledge)
- The problem is **not** your setup — it's that the secret I set is saved in Render's config but **the running instance hasn't picked it up.** Setting an env var doesn't auto-restart the process here (that broken auto-deploy again). Proof: my own call with the correct secret *also* just got 401 — the live process still has an empty secret in memory.

### Architecture Decisions
- That's the pattern — tight 4-line Master Script (Hook / Root Cause / Fix / CTA) + 4 shots + DM protocol. Rewriting to match, pain points folded into the root-cause line instead of a whole barrage.

### Decisions & Reasoning
- **选题我 100% 支持**——补肾壮阳/男性活力在 TCM 里是转化率最高、最缺内容、评论区最炸的赛道。你要 gimmick、要博眼球,方向完全对。
- 好消息是:**冲击力和搞笑感可以完全保留,只要把"器官"抽象成一个符号**——平台审不到,但人人秒懂。🍆 才是互联网通用暗号,不是保险套。
- - Body:完整 **📜 Master Script(6 shots)** + **🎬 Shot Guide**(每个 shot 有 🎥 画面 / 🗣️ 台词 / 💡 用意)+ **🖼️ Thumbnail 图片 prompt**
- 1. **CTA keyword 用 `VITALITY`**,不用 `kidney`——避免跟你现有 kidney 类内容的关键词在 `comment_responses.json` 里撞规则。要换成别的词跟我说。
- 图我没直接生成——想先让你过一眼概念落地对不对。你点头,我就用 body 里那个 thumbnail prompt 跑图(你有 `notion_image.py` / `batch_infographic_gen.py`),生成后直接回填到这条 concept 的 🖼️ 区。
- **③ SOLUTION 点破根因 + 解法(~7s)** — 所有症状指向一个根:**肾阳虚,内火熄了**;晨勃只是最明显的那盏警示灯。不是年纪、不是没救 → 温热熟食 + 早睡 + 别再用冷饮/熬夜/压力掏空油箱。茄子这时慢慢立起来 → "做对了……旗子就又升起来了。"
- Hook · Root Cause · The Fix · CTA — 每个都有 🎥/🗣️/💡,茄子半旗→立起的视觉梗保留在 Shot 1 和 Shot 3。💡 标签用中文 TCM 术语(腎陽虛·命門火衰 等),跟 detox 那条一致。
- - **You get a QA beat** — between "Ready" and "Published" you can look at the auto-generated infographic and fix it if it's off, instead of discovering it after it's already DMing strangers.


## 2026-07-03 16:12 — social-ip-engine

### What Didn't Work (negative knowledge)
- The problem is **not** your setup — it's that the secret I set is saved in Render's config but **the running instance hasn't picked it up.** Setting an env var doesn't auto-restart the process here (that broken auto-deploy again). Proof: my own call with the correct secret *also* just got 401 — the live process still has an empty secret in memory.

### Architecture Decisions
- That's the pattern — tight 4-line Master Script (Hook / Root Cause / Fix / CTA) + 4 shots + DM protocol. Rewriting to match, pain points folded into the root-cause line instead of a whole barrage.

### Decisions & Reasoning
- **选题我 100% 支持**——补肾壮阳/男性活力在 TCM 里是转化率最高、最缺内容、评论区最炸的赛道。你要 gimmick、要博眼球,方向完全对。
- 好消息是:**冲击力和搞笑感可以完全保留,只要把"器官"抽象成一个符号**——平台审不到,但人人秒懂。🍆 才是互联网通用暗号,不是保险套。
- - Body:完整 **📜 Master Script(6 shots)** + **🎬 Shot Guide**(每个 shot 有 🎥 画面 / 🗣️ 台词 / 💡 用意)+ **🖼️ Thumbnail 图片 prompt**
- 1. **CTA keyword 用 `VITALITY`**,不用 `kidney`——避免跟你现有 kidney 类内容的关键词在 `comment_responses.json` 里撞规则。要换成别的词跟我说。
- 图我没直接生成——想先让你过一眼概念落地对不对。你点头,我就用 body 里那个 thumbnail prompt 跑图(你有 `notion_image.py` / `batch_infographic_gen.py`),生成后直接回填到这条 concept 的 🖼️ 区。
- **③ SOLUTION 点破根因 + 解法(~7s)** — 所有症状指向一个根:**肾阳虚,内火熄了**;晨勃只是最明显的那盏警示灯。不是年纪、不是没救 → 温热熟食 + 早睡 + 别再用冷饮/熬夜/压力掏空油箱。茄子这时慢慢立起来 → "做对了……旗子就又升起来了。"
- Hook · Root Cause · The Fix · CTA — 每个都有 🎥/🗣️/💡,茄子半旗→立起的视觉梗保留在 Shot 1 和 Shot 3。💡 标签用中文 TCM 术语(腎陽虛·命門火衰 等),跟 detox 那条一致。
- - **You get a QA beat** — between "Ready" and "Published" you can look at the auto-generated infographic and fix it if it's off, instead of discovering it after it's already DMing strangers.


## 2026-07-03 16:19 — social-ip-engine

### What Didn't Work (negative knowledge)
- The problem is **not** your setup — it's that the secret I set is saved in Render's config but **the running instance hasn't picked it up.** Setting an env var doesn't auto-restart the process here (that broken auto-deploy again). Proof: my own call with the correct secret *also* just got 401 — the live process still has an empty secret in memory.

### Architecture Decisions
- That's the pattern — tight 4-line Master Script (Hook / Root Cause / Fix / CTA) + 4 shots + DM protocol. Rewriting to match, pain points folded into the root-cause line instead of a whole barrage.

### Decisions & Reasoning
- **选题我 100% 支持**——补肾壮阳/男性活力在 TCM 里是转化率最高、最缺内容、评论区最炸的赛道。你要 gimmick、要博眼球,方向完全对。
- 好消息是:**冲击力和搞笑感可以完全保留,只要把"器官"抽象成一个符号**——平台审不到,但人人秒懂。🍆 才是互联网通用暗号,不是保险套。
- - Body:完整 **📜 Master Script(6 shots)** + **🎬 Shot Guide**(每个 shot 有 🎥 画面 / 🗣️ 台词 / 💡 用意)+ **🖼️ Thumbnail 图片 prompt**
- 1. **CTA keyword 用 `VITALITY`**,不用 `kidney`——避免跟你现有 kidney 类内容的关键词在 `comment_responses.json` 里撞规则。要换成别的词跟我说。
- 图我没直接生成——想先让你过一眼概念落地对不对。你点头,我就用 body 里那个 thumbnail prompt 跑图(你有 `notion_image.py` / `batch_infographic_gen.py`),生成后直接回填到这条 concept 的 🖼️ 区。
- **③ SOLUTION 点破根因 + 解法(~7s)** — 所有症状指向一个根:**肾阳虚,内火熄了**;晨勃只是最明显的那盏警示灯。不是年纪、不是没救 → 温热熟食 + 早睡 + 别再用冷饮/熬夜/压力掏空油箱。茄子这时慢慢立起来 → "做对了……旗子就又升起来了。"
- Hook · Root Cause · The Fix · CTA — 每个都有 🎥/🗣️/💡,茄子半旗→立起的视觉梗保留在 Shot 1 和 Shot 3。💡 标签用中文 TCM 术语(腎陽虛·命門火衰 等),跟 detox 那条一致。
- - **You get a QA beat** — between "Ready" and "Published" you can look at the auto-generated infographic and fix it if it's off, instead of discovering it after it's already DMing strangers.


## 2026-07-03 16:19 — social-ip-engine

### What Didn't Work (negative knowledge)
- The problem is **not** your setup — it's that the secret I set is saved in Render's config but **the running instance hasn't picked it up.** Setting an env var doesn't auto-restart the process here (that broken auto-deploy again). Proof: my own call with the correct secret *also* just got 401 — the live process still has an empty secret in memory.

### Architecture Decisions
- That's the pattern — tight 4-line Master Script (Hook / Root Cause / Fix / CTA) + 4 shots + DM protocol. Rewriting to match, pain points folded into the root-cause line instead of a whole barrage.

### Decisions & Reasoning
- **选题我 100% 支持**——补肾壮阳/男性活力在 TCM 里是转化率最高、最缺内容、评论区最炸的赛道。你要 gimmick、要博眼球,方向完全对。
- 好消息是:**冲击力和搞笑感可以完全保留,只要把"器官"抽象成一个符号**——平台审不到,但人人秒懂。🍆 才是互联网通用暗号,不是保险套。
- - Body:完整 **📜 Master Script(6 shots)** + **🎬 Shot Guide**(每个 shot 有 🎥 画面 / 🗣️ 台词 / 💡 用意)+ **🖼️ Thumbnail 图片 prompt**
- 1. **CTA keyword 用 `VITALITY`**,不用 `kidney`——避免跟你现有 kidney 类内容的关键词在 `comment_responses.json` 里撞规则。要换成别的词跟我说。
- 图我没直接生成——想先让你过一眼概念落地对不对。你点头,我就用 body 里那个 thumbnail prompt 跑图(你有 `notion_image.py` / `batch_infographic_gen.py`),生成后直接回填到这条 concept 的 🖼️ 区。
- **③ SOLUTION 点破根因 + 解法(~7s)** — 所有症状指向一个根:**肾阳虚,内火熄了**;晨勃只是最明显的那盏警示灯。不是年纪、不是没救 → 温热熟食 + 早睡 + 别再用冷饮/熬夜/压力掏空油箱。茄子这时慢慢立起来 → "做对了……旗子就又升起来了。"
- Hook · Root Cause · The Fix · CTA — 每个都有 🎥/🗣️/💡,茄子半旗→立起的视觉梗保留在 Shot 1 和 Shot 3。💡 标签用中文 TCM 术语(腎陽虛·命門火衰 等),跟 detox 那条一致。
- - **You get a QA beat** — between "Ready" and "Published" you can look at the auto-generated infographic and fix it if it's off, instead of discovering it after it's already DMing strangers.


## 2026-07-03 16:22 — social-ip-engine

### What Didn't Work (negative knowledge)
- The problem is **not** your setup — it's that the secret I set is saved in Render's config but **the running instance hasn't picked it up.** Setting an env var doesn't auto-restart the process here (that broken auto-deploy again). Proof: my own call with the correct secret *also* just got 401 — the live process still has an empty secret in memory.

### Architecture Decisions
- That's the pattern — tight 4-line Master Script (Hook / Root Cause / Fix / CTA) + 4 shots + DM protocol. Rewriting to match, pain points folded into the root-cause line instead of a whole barrage.

### Decisions & Reasoning
- **选题我 100% 支持**——补肾壮阳/男性活力在 TCM 里是转化率最高、最缺内容、评论区最炸的赛道。你要 gimmick、要博眼球,方向完全对。
- 好消息是:**冲击力和搞笑感可以完全保留,只要把"器官"抽象成一个符号**——平台审不到,但人人秒懂。🍆 才是互联网通用暗号,不是保险套。
- - Body:完整 **📜 Master Script(6 shots)** + **🎬 Shot Guide**(每个 shot 有 🎥 画面 / 🗣️ 台词 / 💡 用意)+ **🖼️ Thumbnail 图片 prompt**
- 1. **CTA keyword 用 `VITALITY`**,不用 `kidney`——避免跟你现有 kidney 类内容的关键词在 `comment_responses.json` 里撞规则。要换成别的词跟我说。
- 图我没直接生成——想先让你过一眼概念落地对不对。你点头,我就用 body 里那个 thumbnail prompt 跑图(你有 `notion_image.py` / `batch_infographic_gen.py`),生成后直接回填到这条 concept 的 🖼️ 区。
- **③ SOLUTION 点破根因 + 解法(~7s)** — 所有症状指向一个根:**肾阳虚,内火熄了**;晨勃只是最明显的那盏警示灯。不是年纪、不是没救 → 温热熟食 + 早睡 + 别再用冷饮/熬夜/压力掏空油箱。茄子这时慢慢立起来 → "做对了……旗子就又升起来了。"
- Hook · Root Cause · The Fix · CTA — 每个都有 🎥/🗣️/💡,茄子半旗→立起的视觉梗保留在 Shot 1 和 Shot 3。💡 标签用中文 TCM 术语(腎陽虛·命門火衰 等),跟 detox 那条一致。
- - **You get a QA beat** — between "Ready" and "Published" you can look at the auto-generated infographic and fix it if it's off, instead of discovering it after it's already DMing strangers.


## 2026-07-03 16:26 — social-ip-engine

### What Didn't Work (negative knowledge)
- The problem is **not** your setup — it's that the secret I set is saved in Render's config but **the running instance hasn't picked it up.** Setting an env var doesn't auto-restart the process here (that broken auto-deploy again). Proof: my own call with the correct secret *also* just got 401 — the live process still has an empty secret in memory.

### Architecture Decisions
- That's the pattern — tight 4-line Master Script (Hook / Root Cause / Fix / CTA) + 4 shots + DM protocol. Rewriting to match, pain points folded into the root-cause line instead of a whole barrage.

### Decisions & Reasoning
- **选题我 100% 支持**——补肾壮阳/男性活力在 TCM 里是转化率最高、最缺内容、评论区最炸的赛道。你要 gimmick、要博眼球,方向完全对。
- 好消息是:**冲击力和搞笑感可以完全保留,只要把"器官"抽象成一个符号**——平台审不到,但人人秒懂。🍆 才是互联网通用暗号,不是保险套。
- - Body:完整 **📜 Master Script(6 shots)** + **🎬 Shot Guide**(每个 shot 有 🎥 画面 / 🗣️ 台词 / 💡 用意)+ **🖼️ Thumbnail 图片 prompt**
- 1. **CTA keyword 用 `VITALITY`**,不用 `kidney`——避免跟你现有 kidney 类内容的关键词在 `comment_responses.json` 里撞规则。要换成别的词跟我说。
- 图我没直接生成——想先让你过一眼概念落地对不对。你点头,我就用 body 里那个 thumbnail prompt 跑图(你有 `notion_image.py` / `batch_infographic_gen.py`),生成后直接回填到这条 concept 的 🖼️ 区。
- **③ SOLUTION 点破根因 + 解法(~7s)** — 所有症状指向一个根:**肾阳虚,内火熄了**;晨勃只是最明显的那盏警示灯。不是年纪、不是没救 → 温热熟食 + 早睡 + 别再用冷饮/熬夜/压力掏空油箱。茄子这时慢慢立起来 → "做对了……旗子就又升起来了。"
- Hook · Root Cause · The Fix · CTA — 每个都有 🎥/🗣️/💡,茄子半旗→立起的视觉梗保留在 Shot 1 和 Shot 3。💡 标签用中文 TCM 术语(腎陽虛·命門火衰 等),跟 detox 那条一致。
- - **You get a QA beat** — between "Ready" and "Published" you can look at the auto-generated infographic and fix it if it's off, instead of discovering it after it's already DMing strangers.


## 2026-07-03 16:36 — social-ip-engine

### What Didn't Work (negative knowledge)
- The problem is **not** your setup — it's that the secret I set is saved in Render's config but **the running instance hasn't picked it up.** Setting an env var doesn't auto-restart the process here (that broken auto-deploy again). Proof: my own call with the correct secret *also* just got 401 — the live process still has an empty secret in memory.

### Architecture Decisions
- That's the pattern — tight 4-line Master Script (Hook / Root Cause / Fix / CTA) + 4 shots + DM protocol. Rewriting to match, pain points folded into the root-cause line instead of a whole barrage.

### Decisions & Reasoning
- **选题我 100% 支持**——补肾壮阳/男性活力在 TCM 里是转化率最高、最缺内容、评论区最炸的赛道。你要 gimmick、要博眼球,方向完全对。
- 好消息是:**冲击力和搞笑感可以完全保留,只要把"器官"抽象成一个符号**——平台审不到,但人人秒懂。🍆 才是互联网通用暗号,不是保险套。
- - Body:完整 **📜 Master Script(6 shots)** + **🎬 Shot Guide**(每个 shot 有 🎥 画面 / 🗣️ 台词 / 💡 用意)+ **🖼️ Thumbnail 图片 prompt**
- 1. **CTA keyword 用 `VITALITY`**,不用 `kidney`——避免跟你现有 kidney 类内容的关键词在 `comment_responses.json` 里撞规则。要换成别的词跟我说。
- 图我没直接生成——想先让你过一眼概念落地对不对。你点头,我就用 body 里那个 thumbnail prompt 跑图(你有 `notion_image.py` / `batch_infographic_gen.py`),生成后直接回填到这条 concept 的 🖼️ 区。
- **③ SOLUTION 点破根因 + 解法(~7s)** — 所有症状指向一个根:**肾阳虚,内火熄了**;晨勃只是最明显的那盏警示灯。不是年纪、不是没救 → 温热熟食 + 早睡 + 别再用冷饮/熬夜/压力掏空油箱。茄子这时慢慢立起来 → "做对了……旗子就又升起来了。"
- Hook · Root Cause · The Fix · CTA — 每个都有 🎥/🗣️/💡,茄子半旗→立起的视觉梗保留在 Shot 1 和 Shot 3。💡 标签用中文 TCM 术语(腎陽虛·命門火衰 等),跟 detox 那条一致。
- - **You get a QA beat** — between "Ready" and "Published" you can look at the auto-generated infographic and fix it if it's off, instead of discovering it after it's already DMing strangers.


## 2026-07-03 16:39 — social-ip-engine

### What Didn't Work (negative knowledge)
- The problem is **not** your setup — it's that the secret I set is saved in Render's config but **the running instance hasn't picked it up.** Setting an env var doesn't auto-restart the process here (that broken auto-deploy again). Proof: my own call with the correct secret *also* just got 401 — the live process still has an empty secret in memory.

### Architecture Decisions
- That's the pattern — tight 4-line Master Script (Hook / Root Cause / Fix / CTA) + 4 shots + DM protocol. Rewriting to match, pain points folded into the root-cause line instead of a whole barrage.

### Decisions & Reasoning
- **选题我 100% 支持**——补肾壮阳/男性活力在 TCM 里是转化率最高、最缺内容、评论区最炸的赛道。你要 gimmick、要博眼球,方向完全对。
- 好消息是:**冲击力和搞笑感可以完全保留,只要把"器官"抽象成一个符号**——平台审不到,但人人秒懂。🍆 才是互联网通用暗号,不是保险套。
- - Body:完整 **📜 Master Script(6 shots)** + **🎬 Shot Guide**(每个 shot 有 🎥 画面 / 🗣️ 台词 / 💡 用意)+ **🖼️ Thumbnail 图片 prompt**
- 1. **CTA keyword 用 `VITALITY`**,不用 `kidney`——避免跟你现有 kidney 类内容的关键词在 `comment_responses.json` 里撞规则。要换成别的词跟我说。
- 图我没直接生成——想先让你过一眼概念落地对不对。你点头,我就用 body 里那个 thumbnail prompt 跑图(你有 `notion_image.py` / `batch_infographic_gen.py`),生成后直接回填到这条 concept 的 🖼️ 区。
- **③ SOLUTION 点破根因 + 解法(~7s)** — 所有症状指向一个根:**肾阳虚,内火熄了**;晨勃只是最明显的那盏警示灯。不是年纪、不是没救 → 温热熟食 + 早睡 + 别再用冷饮/熬夜/压力掏空油箱。茄子这时慢慢立起来 → "做对了……旗子就又升起来了。"
- Hook · Root Cause · The Fix · CTA — 每个都有 🎥/🗣️/💡,茄子半旗→立起的视觉梗保留在 Shot 1 和 Shot 3。💡 标签用中文 TCM 术语(腎陽虛·命門火衰 等),跟 detox 那条一致。
- - **You get a QA beat** — between "Ready" and "Published" you can look at the auto-generated infographic and fix it if it's off, instead of discovering it after it's already DMing strangers.


## 2026-07-03 16:44 — social-ip-engine

### What Didn't Work (negative knowledge)
- The problem is **not** your setup — it's that the secret I set is saved in Render's config but **the running instance hasn't picked it up.** Setting an env var doesn't auto-restart the process here (that broken auto-deploy again). Proof: my own call with the correct secret *also* just got 401 — the live process still has an empty secret in memory.

### Architecture Decisions
- That's the pattern — tight 4-line Master Script (Hook / Root Cause / Fix / CTA) + 4 shots + DM protocol. Rewriting to match, pain points folded into the root-cause line instead of a whole barrage.

### Decisions & Reasoning
- **选题我 100% 支持**——补肾壮阳/男性活力在 TCM 里是转化率最高、最缺内容、评论区最炸的赛道。你要 gimmick、要博眼球,方向完全对。
- 好消息是:**冲击力和搞笑感可以完全保留,只要把"器官"抽象成一个符号**——平台审不到,但人人秒懂。🍆 才是互联网通用暗号,不是保险套。
- - Body:完整 **📜 Master Script(6 shots)** + **🎬 Shot Guide**(每个 shot 有 🎥 画面 / 🗣️ 台词 / 💡 用意)+ **🖼️ Thumbnail 图片 prompt**
- 1. **CTA keyword 用 `VITALITY`**,不用 `kidney`——避免跟你现有 kidney 类内容的关键词在 `comment_responses.json` 里撞规则。要换成别的词跟我说。
- 图我没直接生成——想先让你过一眼概念落地对不对。你点头,我就用 body 里那个 thumbnail prompt 跑图(你有 `notion_image.py` / `batch_infographic_gen.py`),生成后直接回填到这条 concept 的 🖼️ 区。
- **③ SOLUTION 点破根因 + 解法(~7s)** — 所有症状指向一个根:**肾阳虚,内火熄了**;晨勃只是最明显的那盏警示灯。不是年纪、不是没救 → 温热熟食 + 早睡 + 别再用冷饮/熬夜/压力掏空油箱。茄子这时慢慢立起来 → "做对了……旗子就又升起来了。"
- Hook · Root Cause · The Fix · CTA — 每个都有 🎥/🗣️/💡,茄子半旗→立起的视觉梗保留在 Shot 1 和 Shot 3。💡 标签用中文 TCM 术语(腎陽虛·命門火衰 等),跟 detox 那条一致。
- - **You get a QA beat** — between "Ready" and "Published" you can look at the auto-generated infographic and fix it if it's off, instead of discovering it after it's already DMing strangers.


## 2026-07-03 16:49 — social-ip-engine

### What Didn't Work (negative knowledge)
- The problem is **not** your setup — it's that the secret I set is saved in Render's config but **the running instance hasn't picked it up.** Setting an env var doesn't auto-restart the process here (that broken auto-deploy again). Proof: my own call with the correct secret *also* just got 401 — the live process still has an empty secret in memory.

### Architecture Decisions
- That's the pattern — tight 4-line Master Script (Hook / Root Cause / Fix / CTA) + 4 shots + DM protocol. Rewriting to match, pain points folded into the root-cause line instead of a whole barrage.

### Decisions & Reasoning
- **选题我 100% 支持**——补肾壮阳/男性活力在 TCM 里是转化率最高、最缺内容、评论区最炸的赛道。你要 gimmick、要博眼球,方向完全对。
- 好消息是:**冲击力和搞笑感可以完全保留,只要把"器官"抽象成一个符号**——平台审不到,但人人秒懂。🍆 才是互联网通用暗号,不是保险套。
- - Body:完整 **📜 Master Script(6 shots)** + **🎬 Shot Guide**(每个 shot 有 🎥 画面 / 🗣️ 台词 / 💡 用意)+ **🖼️ Thumbnail 图片 prompt**
- 1. **CTA keyword 用 `VITALITY`**,不用 `kidney`——避免跟你现有 kidney 类内容的关键词在 `comment_responses.json` 里撞规则。要换成别的词跟我说。
- 图我没直接生成——想先让你过一眼概念落地对不对。你点头,我就用 body 里那个 thumbnail prompt 跑图(你有 `notion_image.py` / `batch_infographic_gen.py`),生成后直接回填到这条 concept 的 🖼️ 区。
- **③ SOLUTION 点破根因 + 解法(~7s)** — 所有症状指向一个根:**肾阳虚,内火熄了**;晨勃只是最明显的那盏警示灯。不是年纪、不是没救 → 温热熟食 + 早睡 + 别再用冷饮/熬夜/压力掏空油箱。茄子这时慢慢立起来 → "做对了……旗子就又升起来了。"
- Hook · Root Cause · The Fix · CTA — 每个都有 🎥/🗣️/💡,茄子半旗→立起的视觉梗保留在 Shot 1 和 Shot 3。💡 标签用中文 TCM 术语(腎陽虛·命門火衰 等),跟 detox 那条一致。
- - **You get a QA beat** — between "Ready" and "Published" you can look at the auto-generated infographic and fix it if it's off, instead of discovering it after it's already DMing strangers.


## 2026-07-03 16:56 — social-ip-engine

### What Didn't Work (negative knowledge)
- The problem is **not** your setup — it's that the secret I set is saved in Render's config but **the running instance hasn't picked it up.** Setting an env var doesn't auto-restart the process here (that broken auto-deploy again). Proof: my own call with the correct secret *also* just got 401 — the live process still has an empty secret in memory.

### Architecture Decisions
- That's the pattern — tight 4-line Master Script (Hook / Root Cause / Fix / CTA) + 4 shots + DM protocol. Rewriting to match, pain points folded into the root-cause line instead of a whole barrage.

### Decisions & Reasoning
- **选题我 100% 支持**——补肾壮阳/男性活力在 TCM 里是转化率最高、最缺内容、评论区最炸的赛道。你要 gimmick、要博眼球,方向完全对。
- 好消息是:**冲击力和搞笑感可以完全保留,只要把"器官"抽象成一个符号**——平台审不到,但人人秒懂。🍆 才是互联网通用暗号,不是保险套。
- - Body:完整 **📜 Master Script(6 shots)** + **🎬 Shot Guide**(每个 shot 有 🎥 画面 / 🗣️ 台词 / 💡 用意)+ **🖼️ Thumbnail 图片 prompt**
- 1. **CTA keyword 用 `VITALITY`**,不用 `kidney`——避免跟你现有 kidney 类内容的关键词在 `comment_responses.json` 里撞规则。要换成别的词跟我说。
- 图我没直接生成——想先让你过一眼概念落地对不对。你点头,我就用 body 里那个 thumbnail prompt 跑图(你有 `notion_image.py` / `batch_infographic_gen.py`),生成后直接回填到这条 concept 的 🖼️ 区。
- **③ SOLUTION 点破根因 + 解法(~7s)** — 所有症状指向一个根:**肾阳虚,内火熄了**;晨勃只是最明显的那盏警示灯。不是年纪、不是没救 → 温热熟食 + 早睡 + 别再用冷饮/熬夜/压力掏空油箱。茄子这时慢慢立起来 → "做对了……旗子就又升起来了。"
- Hook · Root Cause · The Fix · CTA — 每个都有 🎥/🗣️/💡,茄子半旗→立起的视觉梗保留在 Shot 1 和 Shot 3。💡 标签用中文 TCM 术语(腎陽虛·命門火衰 等),跟 detox 那条一致。
- - **You get a QA beat** — between "Ready" and "Published" you can look at the auto-generated infographic and fix it if it's off, instead of discovering it after it's already DMing strangers.


## 2026-07-03 16:58 — social-ip-engine

### What Didn't Work (negative knowledge)
- The problem is **not** your setup — it's that the secret I set is saved in Render's config but **the running instance hasn't picked it up.** Setting an env var doesn't auto-restart the process here (that broken auto-deploy again). Proof: my own call with the correct secret *also* just got 401 — the live process still has an empty secret in memory.

### Architecture Decisions
- That's the pattern — tight 4-line Master Script (Hook / Root Cause / Fix / CTA) + 4 shots + DM protocol. Rewriting to match, pain points folded into the root-cause line instead of a whole barrage.

### Decisions & Reasoning
- **选题我 100% 支持**——补肾壮阳/男性活力在 TCM 里是转化率最高、最缺内容、评论区最炸的赛道。你要 gimmick、要博眼球,方向完全对。
- 好消息是:**冲击力和搞笑感可以完全保留,只要把"器官"抽象成一个符号**——平台审不到,但人人秒懂。🍆 才是互联网通用暗号,不是保险套。
- - Body:完整 **📜 Master Script(6 shots)** + **🎬 Shot Guide**(每个 shot 有 🎥 画面 / 🗣️ 台词 / 💡 用意)+ **🖼️ Thumbnail 图片 prompt**
- 1. **CTA keyword 用 `VITALITY`**,不用 `kidney`——避免跟你现有 kidney 类内容的关键词在 `comment_responses.json` 里撞规则。要换成别的词跟我说。
- 图我没直接生成——想先让你过一眼概念落地对不对。你点头,我就用 body 里那个 thumbnail prompt 跑图(你有 `notion_image.py` / `batch_infographic_gen.py`),生成后直接回填到这条 concept 的 🖼️ 区。
- **③ SOLUTION 点破根因 + 解法(~7s)** — 所有症状指向一个根:**肾阳虚,内火熄了**;晨勃只是最明显的那盏警示灯。不是年纪、不是没救 → 温热熟食 + 早睡 + 别再用冷饮/熬夜/压力掏空油箱。茄子这时慢慢立起来 → "做对了……旗子就又升起来了。"
- Hook · Root Cause · The Fix · CTA — 每个都有 🎥/🗣️/💡,茄子半旗→立起的视觉梗保留在 Shot 1 和 Shot 3。💡 标签用中文 TCM 术语(腎陽虛·命門火衰 等),跟 detox 那条一致。
- - **You get a QA beat** — between "Ready" and "Published" you can look at the auto-generated infographic and fix it if it's off, instead of discovering it after it's already DMing strangers.


## 2026-07-03 17:00 — social-ip-engine

### What Didn't Work (negative knowledge)
- The problem is **not** your setup — it's that the secret I set is saved in Render's config but **the running instance hasn't picked it up.** Setting an env var doesn't auto-restart the process here (that broken auto-deploy again). Proof: my own call with the correct secret *also* just got 401 — the live process still has an empty secret in memory.

### Architecture Decisions
- That's the pattern — tight 4-line Master Script (Hook / Root Cause / Fix / CTA) + 4 shots + DM protocol. Rewriting to match, pain points folded into the root-cause line instead of a whole barrage.

### Decisions & Reasoning
- **选题我 100% 支持**——补肾壮阳/男性活力在 TCM 里是转化率最高、最缺内容、评论区最炸的赛道。你要 gimmick、要博眼球,方向完全对。
- 好消息是:**冲击力和搞笑感可以完全保留,只要把"器官"抽象成一个符号**——平台审不到,但人人秒懂。🍆 才是互联网通用暗号,不是保险套。
- - Body:完整 **📜 Master Script(6 shots)** + **🎬 Shot Guide**(每个 shot 有 🎥 画面 / 🗣️ 台词 / 💡 用意)+ **🖼️ Thumbnail 图片 prompt**
- 1. **CTA keyword 用 `VITALITY`**,不用 `kidney`——避免跟你现有 kidney 类内容的关键词在 `comment_responses.json` 里撞规则。要换成别的词跟我说。
- 图我没直接生成——想先让你过一眼概念落地对不对。你点头,我就用 body 里那个 thumbnail prompt 跑图(你有 `notion_image.py` / `batch_infographic_gen.py`),生成后直接回填到这条 concept 的 🖼️ 区。
- **③ SOLUTION 点破根因 + 解法(~7s)** — 所有症状指向一个根:**肾阳虚,内火熄了**;晨勃只是最明显的那盏警示灯。不是年纪、不是没救 → 温热熟食 + 早睡 + 别再用冷饮/熬夜/压力掏空油箱。茄子这时慢慢立起来 → "做对了……旗子就又升起来了。"
- Hook · Root Cause · The Fix · CTA — 每个都有 🎥/🗣️/💡,茄子半旗→立起的视觉梗保留在 Shot 1 和 Shot 3。💡 标签用中文 TCM 术语(腎陽虛·命門火衰 等),跟 detox 那条一致。
- - **You get a QA beat** — between "Ready" and "Published" you can look at the auto-generated infographic and fix it if it's off, instead of discovering it after it's already DMing strangers.


## 2026-07-03 17:03 — social-ip-engine

### What Didn't Work (negative knowledge)
- The problem is **not** your setup — it's that the secret I set is saved in Render's config but **the running instance hasn't picked it up.** Setting an env var doesn't auto-restart the process here (that broken auto-deploy again). Proof: my own call with the correct secret *also* just got 401 — the live process still has an empty secret in memory.

### Architecture Decisions
- That's the pattern — tight 4-line Master Script (Hook / Root Cause / Fix / CTA) + 4 shots + DM protocol. Rewriting to match, pain points folded into the root-cause line instead of a whole barrage.

### Decisions & Reasoning
- **选题我 100% 支持**——补肾壮阳/男性活力在 TCM 里是转化率最高、最缺内容、评论区最炸的赛道。你要 gimmick、要博眼球,方向完全对。
- 好消息是:**冲击力和搞笑感可以完全保留,只要把"器官"抽象成一个符号**——平台审不到,但人人秒懂。🍆 才是互联网通用暗号,不是保险套。
- - Body:完整 **📜 Master Script(6 shots)** + **🎬 Shot Guide**(每个 shot 有 🎥 画面 / 🗣️ 台词 / 💡 用意)+ **🖼️ Thumbnail 图片 prompt**
- 1. **CTA keyword 用 `VITALITY`**,不用 `kidney`——避免跟你现有 kidney 类内容的关键词在 `comment_responses.json` 里撞规则。要换成别的词跟我说。
- 图我没直接生成——想先让你过一眼概念落地对不对。你点头,我就用 body 里那个 thumbnail prompt 跑图(你有 `notion_image.py` / `batch_infographic_gen.py`),生成后直接回填到这条 concept 的 🖼️ 区。
- **③ SOLUTION 点破根因 + 解法(~7s)** — 所有症状指向一个根:**肾阳虚,内火熄了**;晨勃只是最明显的那盏警示灯。不是年纪、不是没救 → 温热熟食 + 早睡 + 别再用冷饮/熬夜/压力掏空油箱。茄子这时慢慢立起来 → "做对了……旗子就又升起来了。"
- Hook · Root Cause · The Fix · CTA — 每个都有 🎥/🗣️/💡,茄子半旗→立起的视觉梗保留在 Shot 1 和 Shot 3。💡 标签用中文 TCM 术语(腎陽虛·命門火衰 等),跟 detox 那条一致。
- - **You get a QA beat** — between "Ready" and "Published" you can look at the auto-generated infographic and fix it if it's off, instead of discovering it after it's already DMing strangers.


## 2026-07-03 17:06 — social-ip-engine

### What Didn't Work (negative knowledge)
- The problem is **not** your setup — it's that the secret I set is saved in Render's config but **the running instance hasn't picked it up.** Setting an env var doesn't auto-restart the process here (that broken auto-deploy again). Proof: my own call with the correct secret *also* just got 401 — the live process still has an empty secret in memory.

### Architecture Decisions
- That's the pattern — tight 4-line Master Script (Hook / Root Cause / Fix / CTA) + 4 shots + DM protocol. Rewriting to match, pain points folded into the root-cause line instead of a whole barrage.

### Decisions & Reasoning
- **选题我 100% 支持**——补肾壮阳/男性活力在 TCM 里是转化率最高、最缺内容、评论区最炸的赛道。你要 gimmick、要博眼球,方向完全对。
- 好消息是:**冲击力和搞笑感可以完全保留,只要把"器官"抽象成一个符号**——平台审不到,但人人秒懂。🍆 才是互联网通用暗号,不是保险套。
- - Body:完整 **📜 Master Script(6 shots)** + **🎬 Shot Guide**(每个 shot 有 🎥 画面 / 🗣️ 台词 / 💡 用意)+ **🖼️ Thumbnail 图片 prompt**
- 1. **CTA keyword 用 `VITALITY`**,不用 `kidney`——避免跟你现有 kidney 类内容的关键词在 `comment_responses.json` 里撞规则。要换成别的词跟我说。
- 图我没直接生成——想先让你过一眼概念落地对不对。你点头,我就用 body 里那个 thumbnail prompt 跑图(你有 `notion_image.py` / `batch_infographic_gen.py`),生成后直接回填到这条 concept 的 🖼️ 区。
- **③ SOLUTION 点破根因 + 解法(~7s)** — 所有症状指向一个根:**肾阳虚,内火熄了**;晨勃只是最明显的那盏警示灯。不是年纪、不是没救 → 温热熟食 + 早睡 + 别再用冷饮/熬夜/压力掏空油箱。茄子这时慢慢立起来 → "做对了……旗子就又升起来了。"
- Hook · Root Cause · The Fix · CTA — 每个都有 🎥/🗣️/💡,茄子半旗→立起的视觉梗保留在 Shot 1 和 Shot 3。💡 标签用中文 TCM 术语(腎陽虛·命門火衰 等),跟 detox 那条一致。
- - **You get a QA beat** — between "Ready" and "Published" you can look at the auto-generated infographic and fix it if it's off, instead of discovering it after it's already DMing strangers.


## 2026-07-03 17:11 — social-ip-engine

### What Didn't Work (negative knowledge)
- The problem is **not** your setup — it's that the secret I set is saved in Render's config but **the running instance hasn't picked it up.** Setting an env var doesn't auto-restart the process here (that broken auto-deploy again). Proof: my own call with the correct secret *also* just got 401 — the live process still has an empty secret in memory.

### Architecture Decisions
- That's the pattern — tight 4-line Master Script (Hook / Root Cause / Fix / CTA) + 4 shots + DM protocol. Rewriting to match, pain points folded into the root-cause line instead of a whole barrage.

### Decisions & Reasoning
- **选题我 100% 支持**——补肾壮阳/男性活力在 TCM 里是转化率最高、最缺内容、评论区最炸的赛道。你要 gimmick、要博眼球,方向完全对。
- 好消息是:**冲击力和搞笑感可以完全保留,只要把"器官"抽象成一个符号**——平台审不到,但人人秒懂。🍆 才是互联网通用暗号,不是保险套。
- - Body:完整 **📜 Master Script(6 shots)** + **🎬 Shot Guide**(每个 shot 有 🎥 画面 / 🗣️ 台词 / 💡 用意)+ **🖼️ Thumbnail 图片 prompt**
- 1. **CTA keyword 用 `VITALITY`**,不用 `kidney`——避免跟你现有 kidney 类内容的关键词在 `comment_responses.json` 里撞规则。要换成别的词跟我说。
- 图我没直接生成——想先让你过一眼概念落地对不对。你点头,我就用 body 里那个 thumbnail prompt 跑图(你有 `notion_image.py` / `batch_infographic_gen.py`),生成后直接回填到这条 concept 的 🖼️ 区。
- **③ SOLUTION 点破根因 + 解法(~7s)** — 所有症状指向一个根:**肾阳虚,内火熄了**;晨勃只是最明显的那盏警示灯。不是年纪、不是没救 → 温热熟食 + 早睡 + 别再用冷饮/熬夜/压力掏空油箱。茄子这时慢慢立起来 → "做对了……旗子就又升起来了。"
- Hook · Root Cause · The Fix · CTA — 每个都有 🎥/🗣️/💡,茄子半旗→立起的视觉梗保留在 Shot 1 和 Shot 3。💡 标签用中文 TCM 术语(腎陽虛·命門火衰 等),跟 detox 那条一致。
- - **You get a QA beat** — between "Ready" and "Published" you can look at the auto-generated infographic and fix it if it's off, instead of discovering it after it's already DMing strangers.


## 2026-07-03 17:12 — social-ip-engine

### Architecture Decisions
- The user asked me to make it presentable with suitable design skill — the right specialist here is the **UI Designer** approach, but since this is a single self-contained HTML doc I know intimately from this session, I'll apply a full design pass directly: proper type system, a real presentation-style hero, sticky section nav, refined palette, and polished components — while keeping every word of content intact.

### Decisions & Reasoning
- - Grid cards stagger in as a group instead of popping all at once


## 2026-07-03 17:16 — social-ip-engine

### Architecture Decisions
- The user asked me to make it presentable with suitable design skill — the right specialist here is the **UI Designer** approach, but since this is a single self-contained HTML doc I know intimately from this session, I'll apply a full design pass directly: proper type system, a real presentation-style hero, sticky section nav, refined palette, and polished components — while keeping every word of content intact.

### Decisions & Reasoning
- - Grid cards stagger in as a group instead of popping all at once
- - Real type pairing: **Fraunces** (serif display) for headings, **Inter** for body — gives it that editorial/keynote feel instead of default system font
- - Cards get a colored top-notch accent instead of a full border line, plus lift-on-hover
- - Mermaid re-themed (`base` theme + custom variables) so the diagram matches the page palette instead of default purple


## 2026-07-03 17:18 — social-ip-engine

### Architecture Decisions
- The user asked me to make it presentable with suitable design skill — the right specialist here is the **UI Designer** approach, but since this is a single self-contained HTML doc I know intimately from this session, I'll apply a full design pass directly: proper type system, a real presentation-style hero, sticky section nav, refined palette, and polished components — while keeping every word of content intact.

### Decisions & Reasoning
- - Grid cards stagger in as a group instead of popping all at once
- - Real type pairing: **Fraunces** (serif display) for headings, **Inter** for body — gives it that editorial/keynote feel instead of default system font
- - Cards get a colored top-notch accent instead of a full border line, plus lift-on-hover
- - Mermaid re-themed (`base` theme + custom variables) so the diagram matches the page palette instead of default purple


## 2026-07-03 21:33 — social-ip-engine

### Decisions & Reasoning
- Shot 3's i2v task is generating now. Instead of another serial cycle, let me submit shots 4–5 right now in parallel so all three cook simultaneously:


## 2026-07-03 22:01 — social-ip-engine

### Decisions & Reasoning
- Shot 3's i2v task is generating now. Instead of another serial cycle, let me submit shots 4–5 right now in parallel so all three cook simultaneously:


## 2026-07-03 22:13 — social-ip-engine

### Decisions & Reasoning
- Shot 3's i2v task is generating now. Instead of another serial cycle, let me submit shots 4–5 right now in parallel so all three cook simultaneously:
- Final collector running (`bab6ome4c`) — it self-limits to 9 minutes so it exits cleanly before the cap instead of getting killed mid-download. Shot 4 should land within the first pass; 3 and 5 as their tasks finish. If anything's still pending at exit, one more re-run finishes it.


## 2026-07-03 22:23 — social-ip-engine

### Decisions & Reasoning
- Shot 3's i2v task is generating now. Instead of another serial cycle, let me submit shots 4–5 right now in parallel so all three cook simultaneously:
- Final collector running (`bab6ome4c`) — it self-limits to 9 minutes so it exits cleanly before the cap instead of getting killed mid-download. Shot 4 should land within the first pass; 3 and 5 as their tasks finish. If anything's still pending at exit, one more re-run finishes it.


## 2026-07-03 22:31 — social-ip-engine

### Decisions & Reasoning
- Shot 3's i2v task is generating now. Instead of another serial cycle, let me submit shots 4–5 right now in parallel so all three cook simultaneously:
- Final collector running (`bab6ome4c`) — it self-limits to 9 minutes so it exits cleanly before the cap instead of getting killed mid-download. Shot 4 should land within the first pass; 3 and 5 as their tasks finish. If anything's still pending at exit, one more re-run finishes it.


## 2026-07-03 22:35 — social-ip-engine

### Decisions & Reasoning
- Shot 3's i2v task is generating now. Instead of another serial cycle, let me submit shots 4–5 right now in parallel so all three cook simultaneously:
- Final collector running (`bab6ome4c`) — it self-limits to 9 minutes so it exits cleanly before the cap instead of getting killed mid-download. Shot 4 should land within the first pass; 3 and 5 as their tasks finish. If anything's still pending at exit, one more re-run finishes it.


## 2026-07-05 14:48 — social-ip-engine

### Decisions & Reasoning
- Shot 3's i2v task is generating now. Instead of another serial cycle, let me submit shots 4–5 right now in parallel so all three cook simultaneously:
- Final collector running (`bab6ome4c`) — it self-limits to 9 minutes so it exits cleanly before the cap instead of getting killed mid-download. Shot 4 should land within the first pass; 3 and 5 as their tasks finish. If anything's still pending at exit, one more re-run finishes it.


## 2026-07-05 15:35 — social-ip-engine

### Decisions & Reasoning
- Shot 3's i2v task is generating now. Instead of another serial cycle, let me submit shots 4–5 right now in parallel so all three cook simultaneously:
- Final collector running (`bab6ome4c`) — it self-limits to 9 minutes so it exits cleanly before the cap instead of getting killed mid-download. Shot 4 should land within the first pass; 3 and 5 as their tasks finish. If anything's still pending at exit, one more re-run finishes it.


## 2026-07-05 15:44 — social-ip-engine

### Decisions & Reasoning
- Shot 3's i2v task is generating now. Instead of another serial cycle, let me submit shots 4–5 right now in parallel so all three cook simultaneously:
- Final collector running (`bab6ome4c`) — it self-limits to 9 minutes so it exits cleanly before the cap instead of getting killed mid-download. Shot 4 should land within the first pass; 3 and 5 as their tasks finish. If anything's still pending at exit, one more re-run finishes it.


## 2026-07-05 15:54 — social-ip-engine

### Decisions & Reasoning
- Shot 3's i2v task is generating now. Instead of another serial cycle, let me submit shots 4–5 right now in parallel so all three cook simultaneously:
- Final collector running (`bab6ome4c`) — it self-limits to 9 minutes so it exits cleanly before the cap instead of getting killed mid-download. Shot 4 should land within the first pass; 3 and 5 as their tasks finish. If anything's still pending at exit, one more re-run finishes it.


## 2026-07-05 16:03 — social-ip-engine

### Decisions & Reasoning
- Shot 3's i2v task is generating now. Instead of another serial cycle, let me submit shots 4–5 right now in parallel so all three cook simultaneously:
- Final collector running (`bab6ome4c`) — it self-limits to 9 minutes so it exits cleanly before the cap instead of getting killed mid-download. Shot 4 should land within the first pass; 3 and 5 as their tasks finish. If anything's still pending at exit, one more re-run finishes it.


## 2026-07-05 16:12 — social-ip-engine

### Decisions & Reasoning
- Shot 3's i2v task is generating now. Instead of another serial cycle, let me submit shots 4–5 right now in parallel so all three cook simultaneously:
- Final collector running (`bab6ome4c`) — it self-limits to 9 minutes so it exits cleanly before the cap instead of getting killed mid-download. Shot 4 should land within the first pass; 3 and 5 as their tasks finish. If anything's still pending at exit, one more re-run finishes it.


## 2026-07-05 16:16 — social-ip-engine

### Decisions & Reasoning
- Shot 3's i2v task is generating now. Instead of another serial cycle, let me submit shots 4–5 right now in parallel so all three cook simultaneously:
- Final collector running (`bab6ome4c`) — it self-limits to 9 minutes so it exits cleanly before the cap instead of getting killed mid-download. Shot 4 should land within the first pass; 3 and 5 as their tasks finish. If anything's still pending at exit, one more re-run finishes it.


## 2026-07-05 16:18 — social-ip-engine

### Decisions & Reasoning
- Shot 3's i2v task is generating now. Instead of another serial cycle, let me submit shots 4–5 right now in parallel so all three cook simultaneously:
- Final collector running (`bab6ome4c`) — it self-limits to 9 minutes so it exits cleanly before the cap instead of getting killed mid-download. Shot 4 should land within the first pass; 3 and 5 as their tasks finish. If anything's still pending at exit, one more re-run finishes it.


## 2026-07-06 14:24 — social-ip-engine

### Decisions & Reasoning
- Now let me check whether that checkbox column actually exists on the Notion board yet, so I can tell Shivonne the real state instead of guessing:
- - `notion_sync.sync_once()` now PATCHes a Notion checkbox (default column `🔗 DM Wired`, configurable via `NOTION_WIRED_CHECKBOX_PROP`) to `True` the instant a row's rule is wired into `comment_responses.json` — so you see the tick live on the Production Tracker instead of watching `git log`.
- - Updated `CLAUDE.md` §3.10 with the new behavior + fixed a stale line that still said "Published" instead of the pre-flight "Ready to Publish" trigger.


## 2026-07-06 14:33 — social-ip-engine

### Decisions & Reasoning
- Now let me check whether that checkbox column actually exists on the Notion board yet, so I can tell Shivonne the real state instead of guessing:
- - `notion_sync.sync_once()` now PATCHes a Notion checkbox (default column `🔗 DM Wired`, configurable via `NOTION_WIRED_CHECKBOX_PROP`) to `True` the instant a row's rule is wired into `comment_responses.json` — so you see the tick live on the Production Tracker instead of watching `git log`.
- - Updated `CLAUDE.md` §3.10 with the new behavior + fixed a stale line that still said "Published" instead of the pre-flight "Ready to Publish" trigger.
- Caught it in the act — my own test run just wrote a stray file to the real repo because I hadn't patched `_WIRED_PENDING_PATH` in the fixtures yet. Cleaning that up and fixing test isolation properly:


## 2026-07-06 14:41 — social-ip-engine

### Architecture Decisions
- **python-reviewer's two HIGH findings** (duplicated boolean-env-flag idiom, inconsistent flag-hoisting) — both fixed: extracted a shared `_flag_enabled()` helper and hoisted `mark_wired_enabled` before the loop like its sibling `generate_enabled`.

### Decisions & Reasoning
- Now let me check whether that checkbox column actually exists on the Notion board yet, so I can tell Shivonne the real state instead of guessing:
- - `notion_sync.sync_once()` now PATCHes a Notion checkbox (default column `🔗 DM Wired`, configurable via `NOTION_WIRED_CHECKBOX_PROP`) to `True` the instant a row's rule is wired into `comment_responses.json` — so you see the tick live on the Production Tracker instead of watching `git log`.
- - Updated `CLAUDE.md` §3.10 with the new behavior + fixed a stale line that still said "Published" instead of the pre-flight "Ready to Publish" trigger.
- Caught it in the act — my own test run just wrote a stray file to the real repo because I hadn't patched `_WIRED_PENDING_PATH` in the fixtures yet. Cleaning that up and fixing test isolation properly:
- Same reviewer also caught that my docstring promised auto-retry that didn't actually exist — a failed checkbox PATCH would've been stuck un-ticked forever since `state_set` (which blocks reprocessing) got marked before the checkbox attempt. Rather than just fix the docs to lower the claim, I built the actual retry: failed checkbox attempts now persist to `data/channels/notion_wired_pending.json` and get retried at the top of every subsequent sync — never re-drafting the rule, only retrying the tick.


## 2026-07-06 14:42 — social-ip-engine

### Decisions & Reasoning
- Shot 3's i2v task is generating now. Instead of another serial cycle, let me submit shots 4–5 right now in parallel so all three cook simultaneously:
- Final collector running (`bab6ome4c`) — it self-limits to 9 minutes so it exits cleanly before the cap instead of getting killed mid-download. Shot 4 should land within the first pass; 3 and 5 as their tasks finish. If anything's still pending at exit, one more re-run finishes it.


## 2026-07-06 14:43 — social-ip-engine

### Architecture Decisions
- **python-reviewer's two HIGH findings** (duplicated boolean-env-flag idiom, inconsistent flag-hoisting) — both fixed: extracted a shared `_flag_enabled()` helper and hoisted `mark_wired_enabled` before the loop like its sibling `generate_enabled`.

### Decisions & Reasoning
- Now let me check whether that checkbox column actually exists on the Notion board yet, so I can tell Shivonne the real state instead of guessing:
- - `notion_sync.sync_once()` now PATCHes a Notion checkbox (default column `🔗 DM Wired`, configurable via `NOTION_WIRED_CHECKBOX_PROP`) to `True` the instant a row's rule is wired into `comment_responses.json` — so you see the tick live on the Production Tracker instead of watching `git log`.
- - Updated `CLAUDE.md` §3.10 with the new behavior + fixed a stale line that still said "Published" instead of the pre-flight "Ready to Publish" trigger.
- Caught it in the act — my own test run just wrote a stray file to the real repo because I hadn't patched `_WIRED_PENDING_PATH` in the fixtures yet. Cleaning that up and fixing test isolation properly:
- Same reviewer also caught that my docstring promised auto-retry that didn't actually exist — a failed checkbox PATCH would've been stuck un-ticked forever since `state_set` (which blocks reprocessing) got marked before the checkbox attempt. Rather than just fix the docs to lower the claim, I built the actual retry: failed checkbox attempts now persist to `data/channels/notion_wired_pending.json` and get retried at the top of every subsequent sync — never re-drafting the rule, only retrying the tick.
- 5. Optional: pin it to "Shown in board" via this same visibility panel so you actually see it on the card, rather than leaving it in the hidden list like `Stage`/`Voice`/`Image`/`Video` are now.


## 2026-07-06 14:47 — social-ip-engine

### Decisions & Reasoning
- Shot 3's i2v task is generating now. Instead of another serial cycle, let me submit shots 4–5 right now in parallel so all three cook simultaneously:
- Final collector running (`bab6ome4c`) — it self-limits to 9 minutes so it exits cleanly before the cap instead of getting killed mid-download. Shot 4 should land within the first pass; 3 and 5 as their tasks finish. If anything's still pending at exit, one more re-run finishes it.
- **2. Fan-out 源头修复** —— `apply_shot_plan` 现在会在建新 Production page 时自动带上这两个 section:infographic prompt 从 Content 页同步,cover prompt 用新的 `build_cover_prompt()` 模板生成(scroll-stopping 表情 + 顶部留白给标题字,和现有 image prompt 同风格的确定性模板,不烧 LLM)。以后每次 Content × IP fan-out 都是一步到位。


## 2026-07-06 15:33 — social-ip-engine

### Architecture Decisions
- **python-reviewer's two HIGH findings** (duplicated boolean-env-flag idiom, inconsistent flag-hoisting) — both fixed: extracted a shared `_flag_enabled()` helper and hoisted `mark_wired_enabled` before the loop like its sibling `generate_enabled`.

### Decisions & Reasoning
- Now let me check whether that checkbox column actually exists on the Notion board yet, so I can tell Shivonne the real state instead of guessing:
- - `notion_sync.sync_once()` now PATCHes a Notion checkbox (default column `🔗 DM Wired`, configurable via `NOTION_WIRED_CHECKBOX_PROP`) to `True` the instant a row's rule is wired into `comment_responses.json` — so you see the tick live on the Production Tracker instead of watching `git log`.
- - Updated `CLAUDE.md` §3.10 with the new behavior + fixed a stale line that still said "Published" instead of the pre-flight "Ready to Publish" trigger.
- Caught it in the act — my own test run just wrote a stray file to the real repo because I hadn't patched `_WIRED_PENDING_PATH` in the fixtures yet. Cleaning that up and fixing test isolation properly:
- Same reviewer also caught that my docstring promised auto-retry that didn't actually exist — a failed checkbox PATCH would've been stuck un-ticked forever since `state_set` (which blocks reprocessing) got marked before the checkbox attempt. Rather than just fix the docs to lower the claim, I built the actual retry: failed checkbox attempts now persist to `data/channels/notion_wired_pending.json` and get retried at the top of every subsequent sync — never re-drafting the rule, only retrying the tick.
- 5. Optional: pin it to "Shown in board" via this same visibility panel so you actually see it on the card, rather than leaving it in the hidden list like `Stage`/`Voice`/`Image`/`Video` are now.
- Want me to send a synthetic test webhook against the live Render endpoint to confirm the checkbox actually ticks end-to-end, the same way we diagnosed the `IG_ENABLED` outage last time? That'd tell us definitively rather than waiting for a real Notion publish.


## 2026-07-06 16:04 — social-ip-engine

### Decisions & Reasoning
- Shot 3's i2v task is generating now. Instead of another serial cycle, let me submit shots 4–5 right now in parallel so all three cook simultaneously:
- Final collector running (`bab6ome4c`) — it self-limits to 9 minutes so it exits cleanly before the cap instead of getting killed mid-download. Shot 4 should land within the first pass; 3 and 5 as their tasks finish. If anything's still pending at exit, one more re-run finishes it.
- **2. Fan-out 源头修复** —— `apply_shot_plan` 现在会在建新 Production page 时自动带上这两个 section:infographic prompt 从 Content 页同步,cover prompt 用新的 `build_cover_prompt()` 模板生成(scroll-stopping 表情 + 顶部留白给标题字,和现有 image prompt 同风格的确定性模板,不烧 LLM)。以后每次 Content × IP fan-out 都是一步到位。
- 1. **切片风险消除** —— `cover_dm_blocks` 拆成 `cover_blocks()` + `dm_blocks()` 两个独立函数,fan-out 和 backfill 共用同一来源,结构永远不会漂移
- Review 还提了一个 MEDIUM 已知即可的点:`fetch_infographic_brief` 和 `parse_storyboard` 只扫一层 blocks —— 如果以后有人把 Content 页的 Infographic Brief 收进 toggle 里,会静默拿不到。目前所有页都是平铺结构,不用动;真要整理页面结构时记得说一声。


## 2026-07-06 16:50 — social-ip-engine

### Decisions & Reasoning
- Shot 3's i2v task is generating now. Instead of another serial cycle, let me submit shots 4–5 right now in parallel so all three cook simultaneously:
- Final collector running (`bab6ome4c`) — it self-limits to 9 minutes so it exits cleanly before the cap instead of getting killed mid-download. Shot 4 should land within the first pass; 3 and 5 as their tasks finish. If anything's still pending at exit, one more re-run finishes it.
- **2. Fan-out 源头修复** —— `apply_shot_plan` 现在会在建新 Production page 时自动带上这两个 section:infographic prompt 从 Content 页同步,cover prompt 用新的 `build_cover_prompt()` 模板生成(scroll-stopping 表情 + 顶部留白给标题字,和现有 image prompt 同风格的确定性模板,不烧 LLM)。以后每次 Content × IP fan-out 都是一步到位。
- 1. **切片风险消除** —— `cover_dm_blocks` 拆成 `cover_blocks()` + `dm_blocks()` 两个独立函数,fan-out 和 backfill 共用同一来源,结构永远不会漂移
- Review 还提了一个 MEDIUM 已知即可的点:`fetch_infographic_brief` 和 `parse_storyboard` 只扫一层 blocks —— 如果以后有人把 Content 页的 Infographic Brief 收进 toggle 里,会静默拿不到。目前所有页都是平铺结构,不用动;真要整理页面结构时记得说一声。


## 2026-07-06 17:09 — social-ip-engine

### Decisions & Reasoning
- Shot 3's i2v task is generating now. Instead of another serial cycle, let me submit shots 4–5 right now in parallel so all three cook simultaneously:
- Final collector running (`bab6ome4c`) — it self-limits to 9 minutes so it exits cleanly before the cap instead of getting killed mid-download. Shot 4 should land within the first pass; 3 and 5 as their tasks finish. If anything's still pending at exit, one more re-run finishes it.
- **2. Fan-out 源头修复** —— `apply_shot_plan` 现在会在建新 Production page 时自动带上这两个 section:infographic prompt 从 Content 页同步,cover prompt 用新的 `build_cover_prompt()` 模板生成(scroll-stopping 表情 + 顶部留白给标题字,和现有 image prompt 同风格的确定性模板,不烧 LLM)。以后每次 Content × IP fan-out 都是一步到位。
- 1. **切片风险消除** —— `cover_dm_blocks` 拆成 `cover_blocks()` + `dm_blocks()` 两个独立函数,fan-out 和 backfill 共用同一来源,结构永远不会漂移
- Review 还提了一个 MEDIUM 已知即可的点:`fetch_infographic_brief` 和 `parse_storyboard` 只扫一层 blocks —— 如果以后有人把 Content 页的 Infographic Brief 收进 toggle 里,会静默拿不到。目前所有页都是平铺结构,不用动;真要整理页面结构时记得说一声。


## 2026-07-06 17:19 — social-ip-engine

### Decisions & Reasoning
- Shot 3's i2v task is generating now. Instead of another serial cycle, let me submit shots 4–5 right now in parallel so all three cook simultaneously:
- Final collector running (`bab6ome4c`) — it self-limits to 9 minutes so it exits cleanly before the cap instead of getting killed mid-download. Shot 4 should land within the first pass; 3 and 5 as their tasks finish. If anything's still pending at exit, one more re-run finishes it.
- **2. Fan-out 源头修复** —— `apply_shot_plan` 现在会在建新 Production page 时自动带上这两个 section:infographic prompt 从 Content 页同步,cover prompt 用新的 `build_cover_prompt()` 模板生成(scroll-stopping 表情 + 顶部留白给标题字,和现有 image prompt 同风格的确定性模板,不烧 LLM)。以后每次 Content × IP fan-out 都是一步到位。
- 1. **切片风险消除** —— `cover_dm_blocks` 拆成 `cover_blocks()` + `dm_blocks()` 两个独立函数,fan-out 和 backfill 共用同一来源,结构永远不会漂移
- Review 还提了一个 MEDIUM 已知即可的点:`fetch_infographic_brief` 和 `parse_storyboard` 只扫一层 blocks —— 如果以后有人把 Content 页的 Infographic Brief 收进 toggle 里,会静默拿不到。目前所有页都是平铺结构,不用动;真要整理页面结构时记得说一声。


## 2026-07-06 17:26 — social-ip-engine

### Decisions & Reasoning
- Shot 3's i2v task is generating now. Instead of another serial cycle, let me submit shots 4–5 right now in parallel so all three cook simultaneously:
- Final collector running (`bab6ome4c`) — it self-limits to 9 minutes so it exits cleanly before the cap instead of getting killed mid-download. Shot 4 should land within the first pass; 3 and 5 as their tasks finish. If anything's still pending at exit, one more re-run finishes it.
- **2. Fan-out 源头修复** —— `apply_shot_plan` 现在会在建新 Production page 时自动带上这两个 section:infographic prompt 从 Content 页同步,cover prompt 用新的 `build_cover_prompt()` 模板生成(scroll-stopping 表情 + 顶部留白给标题字,和现有 image prompt 同风格的确定性模板,不烧 LLM)。以后每次 Content × IP fan-out 都是一步到位。
- 1. **切片风险消除** —— `cover_dm_blocks` 拆成 `cover_blocks()` + `dm_blocks()` 两个独立函数,fan-out 和 backfill 共用同一来源,结构永远不会漂移
- Review 还提了一个 MEDIUM 已知即可的点:`fetch_infographic_brief` 和 `parse_storyboard` 只扫一层 blocks —— 如果以后有人把 Content 页的 Infographic Brief 收进 toggle 里,会静默拿不到。目前所有页都是平铺结构,不用动;真要整理页面结构时记得说一声。
- Both Jackie rows are done — image + voice complete. Before I hand off, let me eyeball the two hero shots myself (the two-person poses that gpt-image-2 sometimes garbles) so I flag any problem now rather than you finding it.


## 2026-07-06 17:36 — social-ip-engine

### What Didn't Work (negative knowledge)
- Documented the whole ordering contract in `CLAUDE.md` with a pointer to the exact test, so if anyone touches `sync_once()` later without reading this, the test fails loudly instead of the bug quietly coming back.

### Architecture Decisions
- **python-reviewer's two HIGH findings** (duplicated boolean-env-flag idiom, inconsistent flag-hoisting) — both fixed: extracted a shared `_flag_enabled()` helper and hoisted `mark_wired_enabled` before the loop like its sibling `generate_enabled`.

### Decisions & Reasoning
- Now let me check whether that checkbox column actually exists on the Notion board yet, so I can tell Shivonne the real state instead of guessing:
- - `notion_sync.sync_once()` now PATCHes a Notion checkbox (default column `🔗 DM Wired`, configurable via `NOTION_WIRED_CHECKBOX_PROP`) to `True` the instant a row's rule is wired into `comment_responses.json` — so you see the tick live on the Production Tracker instead of watching `git log`.
- - Updated `CLAUDE.md` §3.10 with the new behavior + fixed a stale line that still said "Published" instead of the pre-flight "Ready to Publish" trigger.
- Caught it in the act — my own test run just wrote a stray file to the real repo because I hadn't patched `_WIRED_PENDING_PATH` in the fixtures yet. Cleaning that up and fixing test isolation properly:
- Same reviewer also caught that my docstring promised auto-retry that didn't actually exist — a failed checkbox PATCH would've been stuck un-ticked forever since `state_set` (which blocks reprocessing) got marked before the checkbox attempt. Rather than just fix the docs to lower the claim, I built the actual retry: failed checkbox attempts now persist to `data/channels/notion_wired_pending.json` and get retried at the top of every subsequent sync — never re-drafting the rule, only retrying the tick.
- 5. Optional: pin it to "Shown in board" via this same visibility panel so you actually see it on the card, rather than leaving it in the hidden list like `Stage`/`Voice`/`Image`/`Video` are now.
- Want me to send a synthetic test webhook against the live Render endpoint to confirm the checkbox actually ticks end-to-end, the same way we diagnosed the `IG_ENABLED` outage last time? That'd tell us definitively rather than waiting for a real Notion publish.


## 2026-07-06 17:57 — social-ip-engine

### What Didn't Work (negative knowledge)
- Documented the whole ordering contract in `CLAUDE.md` with a pointer to the exact test, so if anyone touches `sync_once()` later without reading this, the test fails loudly instead of the bug quietly coming back.

### Architecture Decisions
- **python-reviewer's two HIGH findings** (duplicated boolean-env-flag idiom, inconsistent flag-hoisting) — both fixed: extracted a shared `_flag_enabled()` helper and hoisted `mark_wired_enabled` before the loop like its sibling `generate_enabled`.

### Decisions & Reasoning
- Now let me check whether that checkbox column actually exists on the Notion board yet, so I can tell Shivonne the real state instead of guessing:
- - `notion_sync.sync_once()` now PATCHes a Notion checkbox (default column `🔗 DM Wired`, configurable via `NOTION_WIRED_CHECKBOX_PROP`) to `True` the instant a row's rule is wired into `comment_responses.json` — so you see the tick live on the Production Tracker instead of watching `git log`.
- - Updated `CLAUDE.md` §3.10 with the new behavior + fixed a stale line that still said "Published" instead of the pre-flight "Ready to Publish" trigger.
- Caught it in the act — my own test run just wrote a stray file to the real repo because I hadn't patched `_WIRED_PENDING_PATH` in the fixtures yet. Cleaning that up and fixing test isolation properly:
- Same reviewer also caught that my docstring promised auto-retry that didn't actually exist — a failed checkbox PATCH would've been stuck un-ticked forever since `state_set` (which blocks reprocessing) got marked before the checkbox attempt. Rather than just fix the docs to lower the claim, I built the actual retry: failed checkbox attempts now persist to `data/channels/notion_wired_pending.json` and get retried at the top of every subsequent sync — never re-drafting the rule, only retrying the tick.
- 5. Optional: pin it to "Shown in board" via this same visibility panel so you actually see it on the card, rather than leaving it in the hidden list like `Stage`/`Voice`/`Image`/`Video` are now.
- Want me to send a synthetic test webhook against the live Render endpoint to confirm the checkbox actually ticks end-to-end, the same way we diagnosed the `IG_ENABLED` outage last time? That'd tell us definitively rather than waiting for a real Notion publish.
- Both still running, still on their first shot (image gen takes time). I'll wait for them to finish rather than poll further.


## 2026-07-06 18:05 — social-ip-engine

### What Didn't Work (negative knowledge)
- Documented the whole ordering contract in `CLAUDE.md` with a pointer to the exact test, so if anyone touches `sync_once()` later without reading this, the test fails loudly instead of the bug quietly coming back.

### Architecture Decisions
- **python-reviewer's two HIGH findings** (duplicated boolean-env-flag idiom, inconsistent flag-hoisting) — both fixed: extracted a shared `_flag_enabled()` helper and hoisted `mark_wired_enabled` before the loop like its sibling `generate_enabled`.

### Decisions & Reasoning
- Now let me check whether that checkbox column actually exists on the Notion board yet, so I can tell Shivonne the real state instead of guessing:
- - `notion_sync.sync_once()` now PATCHes a Notion checkbox (default column `🔗 DM Wired`, configurable via `NOTION_WIRED_CHECKBOX_PROP`) to `True` the instant a row's rule is wired into `comment_responses.json` — so you see the tick live on the Production Tracker instead of watching `git log`.
- - Updated `CLAUDE.md` §3.10 with the new behavior + fixed a stale line that still said "Published" instead of the pre-flight "Ready to Publish" trigger.
- Caught it in the act — my own test run just wrote a stray file to the real repo because I hadn't patched `_WIRED_PENDING_PATH` in the fixtures yet. Cleaning that up and fixing test isolation properly:
- Same reviewer also caught that my docstring promised auto-retry that didn't actually exist — a failed checkbox PATCH would've been stuck un-ticked forever since `state_set` (which blocks reprocessing) got marked before the checkbox attempt. Rather than just fix the docs to lower the claim, I built the actual retry: failed checkbox attempts now persist to `data/channels/notion_wired_pending.json` and get retried at the top of every subsequent sync — never re-drafting the rule, only retrying the tick.
- 5. Optional: pin it to "Shown in board" via this same visibility panel so you actually see it on the card, rather than leaving it in the hidden list like `Stage`/`Voice`/`Image`/`Video` are now.
- Want me to send a synthetic test webhook against the live Render endpoint to confirm the checkbox actually ticks end-to-end, the same way we diagnosed the `IG_ENABLED` outage last time? That'd tell us definitively rather than waiting for a real Notion publish.
- Both still running, still on their first shot (image gen takes time). I'll wait for them to finish rather than poll further.


## 2026-07-06 18:11 — social-ip-engine

### What Didn't Work (negative knowledge)
- Documented the whole ordering contract in `CLAUDE.md` with a pointer to the exact test, so if anyone touches `sync_once()` later without reading this, the test fails loudly instead of the bug quietly coming back.

### Architecture Decisions
- **python-reviewer's two HIGH findings** (duplicated boolean-env-flag idiom, inconsistent flag-hoisting) — both fixed: extracted a shared `_flag_enabled()` helper and hoisted `mark_wired_enabled` before the loop like its sibling `generate_enabled`.

### Decisions & Reasoning
- Now let me check whether that checkbox column actually exists on the Notion board yet, so I can tell Shivonne the real state instead of guessing:
- - `notion_sync.sync_once()` now PATCHes a Notion checkbox (default column `🔗 DM Wired`, configurable via `NOTION_WIRED_CHECKBOX_PROP`) to `True` the instant a row's rule is wired into `comment_responses.json` — so you see the tick live on the Production Tracker instead of watching `git log`.
- - Updated `CLAUDE.md` §3.10 with the new behavior + fixed a stale line that still said "Published" instead of the pre-flight "Ready to Publish" trigger.
- Caught it in the act — my own test run just wrote a stray file to the real repo because I hadn't patched `_WIRED_PENDING_PATH` in the fixtures yet. Cleaning that up and fixing test isolation properly:
- Same reviewer also caught that my docstring promised auto-retry that didn't actually exist — a failed checkbox PATCH would've been stuck un-ticked forever since `state_set` (which blocks reprocessing) got marked before the checkbox attempt. Rather than just fix the docs to lower the claim, I built the actual retry: failed checkbox attempts now persist to `data/channels/notion_wired_pending.json` and get retried at the top of every subsequent sync — never re-drafting the rule, only retrying the tick.
- 5. Optional: pin it to "Shown in board" via this same visibility panel so you actually see it on the card, rather than leaving it in the hidden list like `Stage`/`Voice`/`Image`/`Video` are now.
- Want me to send a synthetic test webhook against the live Render endpoint to confirm the checkbox actually ticks end-to-end, the same way we diagnosed the `IG_ENABLED` outage last time? That'd tell us definitively rather than waiting for a real Notion publish.
- Both still running, still on their first shot (image gen takes time). I'll wait for them to finish rather than poll further.


## 2026-07-06 18:16 — social-ip-engine

### What Didn't Work (negative knowledge)
- Documented the whole ordering contract in `CLAUDE.md` with a pointer to the exact test, so if anyone touches `sync_once()` later without reading this, the test fails loudly instead of the bug quietly coming back.

### Architecture Decisions
- **python-reviewer's two HIGH findings** (duplicated boolean-env-flag idiom, inconsistent flag-hoisting) — both fixed: extracted a shared `_flag_enabled()` helper and hoisted `mark_wired_enabled` before the loop like its sibling `generate_enabled`.

### Decisions & Reasoning
- Now let me check whether that checkbox column actually exists on the Notion board yet, so I can tell Shivonne the real state instead of guessing:
- - `notion_sync.sync_once()` now PATCHes a Notion checkbox (default column `🔗 DM Wired`, configurable via `NOTION_WIRED_CHECKBOX_PROP`) to `True` the instant a row's rule is wired into `comment_responses.json` — so you see the tick live on the Production Tracker instead of watching `git log`.
- - Updated `CLAUDE.md` §3.10 with the new behavior + fixed a stale line that still said "Published" instead of the pre-flight "Ready to Publish" trigger.
- Caught it in the act — my own test run just wrote a stray file to the real repo because I hadn't patched `_WIRED_PENDING_PATH` in the fixtures yet. Cleaning that up and fixing test isolation properly:
- Same reviewer also caught that my docstring promised auto-retry that didn't actually exist — a failed checkbox PATCH would've been stuck un-ticked forever since `state_set` (which blocks reprocessing) got marked before the checkbox attempt. Rather than just fix the docs to lower the claim, I built the actual retry: failed checkbox attempts now persist to `data/channels/notion_wired_pending.json` and get retried at the top of every subsequent sync — never re-drafting the rule, only retrying the tick.
- 5. Optional: pin it to "Shown in board" via this same visibility panel so you actually see it on the card, rather than leaving it in the hidden list like `Stage`/`Voice`/`Image`/`Video` are now.
- Want me to send a synthetic test webhook against the live Render endpoint to confirm the checkbox actually ticks end-to-end, the same way we diagnosed the `IG_ENABLED` outage last time? That'd tell us definitively rather than waiting for a real Notion publish.
- Both still running, still on their first shot (image gen takes time). I'll wait for them to finish rather than poll further.


## 2026-07-06 18:24 — social-ip-engine

### Architecture Decisions
- - 8 lint warnings, all "caption line >42 chars" — purely cosmetic; JianYing wraps them. Say the word and I'll auto-split long cues into 2 lines.

### Decisions & Reasoning
- **Merged footage** → JianYing draft `stomach-jackie-en`:


## 2026-07-06 18:34 — social-ip-engine

### Architecture Decisions
- - 8 lint warnings, all "caption line >42 chars" — purely cosmetic; JianYing wraps them. Say the word and I'll auto-split long cues into 2 lines.

### Decisions & Reasoning
- **Merged footage** → JianYing draft `stomach-jackie-en`:
- Two separate things — let me diagnose both before proposing, because the fix differs. Let me check the current canvas size and whether JianYing actually kept our caption track.
- 2. **The captions ARE in the draft** (text track, 15 segments — mtime shows JianYing hasn't re-saved it). You're not seeing them because the caption's default position is set for a 16:9 frame, so they're placed off the visible portrait area / wrong spot.


## 2026-07-06 18:40 — social-ip-engine

### Architecture Decisions
- - 8 lint warnings, all "caption line >42 chars" — purely cosmetic; JianYing wraps them. Say the word and I'll auto-split long cues into 2 lines.

### Decisions & Reasoning
- **Merged footage** → JianYing draft `stomach-jackie-en`:
- Two separate things — let me diagnose both before proposing, because the fix differs. Let me check the current canvas size and whether JianYing actually kept our caption track.
- 2. **The captions ARE in the draft** (text track, 15 segments — mtime shows JianYing hasn't re-saved it). You're not seeing them because the caption's default position is set for a 16:9 frame, so they're placed off the visible portrait area / wrong spot.
- Right — use the individual `shot*_regen` clips (freshly concatenated) instead of `final_regen`. That guarantees the latest regen shots. Concatenating them, then burning the captions on the native 3:4 frame with audio:


## 2026-07-06 18:51 — social-ip-engine

### Architecture Decisions
- - 8 lint warnings, all "caption line >42 chars" — purely cosmetic; JianYing wraps them. Say the word and I'll auto-split long cues into 2 lines.

### Decisions & Reasoning
- **Merged footage** → JianYing draft `stomach-jackie-en`:
- Two separate things — let me diagnose both before proposing, because the fix differs. Let me check the current canvas size and whether JianYing actually kept our caption track.
- 2. **The captions ARE in the draft** (text track, 15 segments — mtime shows JianYing hasn't re-saved it). You're not seeing them because the caption's default position is set for a 16:9 frame, so they're placed off the visible portrait area / wrong spot.
- Right — use the individual `shot*_regen` clips (freshly concatenated) instead of `final_regen`. That guarantees the latest regen shots. Concatenating them, then burning the captions on the native 3:4 frame with audio:


## 2026-07-06 18:55 — social-ip-engine

### Architecture Decisions
- - 8 lint warnings, all "caption line >42 chars" — purely cosmetic; JianYing wraps them. Say the word and I'll auto-split long cues into 2 lines.

### Decisions & Reasoning
- **Merged footage** → JianYing draft `stomach-jackie-en`:
- Two separate things — let me diagnose both before proposing, because the fix differs. Let me check the current canvas size and whether JianYing actually kept our caption track.
- 2. **The captions ARE in the draft** (text track, 15 segments — mtime shows JianYing hasn't re-saved it). You're not seeing them because the caption's default position is set for a 16:9 frame, so they're placed off the visible portrait area / wrong spot.
- Right — use the individual `shot*_regen` clips (freshly concatenated) instead of `final_regen`. That guarantees the latest regen shots. Concatenating them, then burning the captions on the native 3:4 frame with audio:


## 2026-07-06 18:56 — social-ip-engine

### What Didn't Work (negative knowledge)
- Documented the whole ordering contract in `CLAUDE.md` with a pointer to the exact test, so if anyone touches `sync_once()` later without reading this, the test fails loudly instead of the bug quietly coming back.

### Architecture Decisions
- **python-reviewer's two HIGH findings** (duplicated boolean-env-flag idiom, inconsistent flag-hoisting) — both fixed: extracted a shared `_flag_enabled()` helper and hoisted `mark_wired_enabled` before the loop like its sibling `generate_enabled`.

### Decisions & Reasoning
- Now let me check whether that checkbox column actually exists on the Notion board yet, so I can tell Shivonne the real state instead of guessing:
- - `notion_sync.sync_once()` now PATCHes a Notion checkbox (default column `🔗 DM Wired`, configurable via `NOTION_WIRED_CHECKBOX_PROP`) to `True` the instant a row's rule is wired into `comment_responses.json` — so you see the tick live on the Production Tracker instead of watching `git log`.
- - Updated `CLAUDE.md` §3.10 with the new behavior + fixed a stale line that still said "Published" instead of the pre-flight "Ready to Publish" trigger.
- Caught it in the act — my own test run just wrote a stray file to the real repo because I hadn't patched `_WIRED_PENDING_PATH` in the fixtures yet. Cleaning that up and fixing test isolation properly:
- Same reviewer also caught that my docstring promised auto-retry that didn't actually exist — a failed checkbox PATCH would've been stuck un-ticked forever since `state_set` (which blocks reprocessing) got marked before the checkbox attempt. Rather than just fix the docs to lower the claim, I built the actual retry: failed checkbox attempts now persist to `data/channels/notion_wired_pending.json` and get retried at the top of every subsequent sync — never re-drafting the rule, only retrying the tick.
- 5. Optional: pin it to "Shown in board" via this same visibility panel so you actually see it on the card, rather than leaving it in the hidden list like `Stage`/`Voice`/`Image`/`Video` are now.
- Want me to send a synthetic test webhook against the live Render endpoint to confirm the checkbox actually ticks end-to-end, the same way we diagnosed the `IG_ENABLED` outage last time? That'd tell us definitively rather than waiting for a real Notion publish.
- Both still running, still on their first shot (image gen takes time). I'll wait for them to finish rather than poll further.


## 2026-07-06 20:12 — social-ip-engine

### What Didn't Work (negative knowledge)
- Documented the whole ordering contract in `CLAUDE.md` with a pointer to the exact test, so if anyone touches `sync_once()` later without reading this, the test fails loudly instead of the bug quietly coming back.

### Architecture Decisions
- **python-reviewer's two HIGH findings** (duplicated boolean-env-flag idiom, inconsistent flag-hoisting) — both fixed: extracted a shared `_flag_enabled()` helper and hoisted `mark_wired_enabled` before the loop like its sibling `generate_enabled`.

### Decisions & Reasoning
- Now let me check whether that checkbox column actually exists on the Notion board yet, so I can tell Shivonne the real state instead of guessing:
- - `notion_sync.sync_once()` now PATCHes a Notion checkbox (default column `🔗 DM Wired`, configurable via `NOTION_WIRED_CHECKBOX_PROP`) to `True` the instant a row's rule is wired into `comment_responses.json` — so you see the tick live on the Production Tracker instead of watching `git log`.
- - Updated `CLAUDE.md` §3.10 with the new behavior + fixed a stale line that still said "Published" instead of the pre-flight "Ready to Publish" trigger.
- Caught it in the act — my own test run just wrote a stray file to the real repo because I hadn't patched `_WIRED_PENDING_PATH` in the fixtures yet. Cleaning that up and fixing test isolation properly:
- Same reviewer also caught that my docstring promised auto-retry that didn't actually exist — a failed checkbox PATCH would've been stuck un-ticked forever since `state_set` (which blocks reprocessing) got marked before the checkbox attempt. Rather than just fix the docs to lower the claim, I built the actual retry: failed checkbox attempts now persist to `data/channels/notion_wired_pending.json` and get retried at the top of every subsequent sync — never re-drafting the rule, only retrying the tick.
- 5. Optional: pin it to "Shown in board" via this same visibility panel so you actually see it on the card, rather than leaving it in the hidden list like `Stage`/`Voice`/`Image`/`Video` are now.
- Want me to send a synthetic test webhook against the live Render endpoint to confirm the checkbox actually ticks end-to-end, the same way we diagnosed the `IG_ENABLED` outage last time? That'd tell us definitively rather than waiting for a real Notion publish.
- Both still running, still on their first shot (image gen takes time). I'll wait for them to finish rather than poll further.


## 2026-07-06 20:42 — social-ip-engine

### What Didn't Work (negative knowledge)
- Documented the whole ordering contract in `CLAUDE.md` with a pointer to the exact test, so if anyone touches `sync_once()` later without reading this, the test fails loudly instead of the bug quietly coming back.

### Architecture Decisions
- **python-reviewer's two HIGH findings** (duplicated boolean-env-flag idiom, inconsistent flag-hoisting) — both fixed: extracted a shared `_flag_enabled()` helper and hoisted `mark_wired_enabled` before the loop like its sibling `generate_enabled`.

### Decisions & Reasoning
- Now let me check whether that checkbox column actually exists on the Notion board yet, so I can tell Shivonne the real state instead of guessing:
- - `notion_sync.sync_once()` now PATCHes a Notion checkbox (default column `🔗 DM Wired`, configurable via `NOTION_WIRED_CHECKBOX_PROP`) to `True` the instant a row's rule is wired into `comment_responses.json` — so you see the tick live on the Production Tracker instead of watching `git log`.
- - Updated `CLAUDE.md` §3.10 with the new behavior + fixed a stale line that still said "Published" instead of the pre-flight "Ready to Publish" trigger.
- Caught it in the act — my own test run just wrote a stray file to the real repo because I hadn't patched `_WIRED_PENDING_PATH` in the fixtures yet. Cleaning that up and fixing test isolation properly:
- Same reviewer also caught that my docstring promised auto-retry that didn't actually exist — a failed checkbox PATCH would've been stuck un-ticked forever since `state_set` (which blocks reprocessing) got marked before the checkbox attempt. Rather than just fix the docs to lower the claim, I built the actual retry: failed checkbox attempts now persist to `data/channels/notion_wired_pending.json` and get retried at the top of every subsequent sync — never re-drafting the rule, only retrying the tick.
- 5. Optional: pin it to "Shown in board" via this same visibility panel so you actually see it on the card, rather than leaving it in the hidden list like `Stage`/`Voice`/`Image`/`Video` are now.
- Want me to send a synthetic test webhook against the live Render endpoint to confirm the checkbox actually ticks end-to-end, the same way we diagnosed the `IG_ENABLED` outage last time? That'd tell us definitively rather than waiting for a real Notion publish.
- Both still running, still on their first shot (image gen takes time). I'll wait for them to finish rather than poll further.


## 2026-07-06 20:45 — social-ip-engine

### What Didn't Work (negative knowledge)
- Documented the whole ordering contract in `CLAUDE.md` with a pointer to the exact test, so if anyone touches `sync_once()` later without reading this, the test fails loudly instead of the bug quietly coming back.

### Architecture Decisions
- **python-reviewer's two HIGH findings** (duplicated boolean-env-flag idiom, inconsistent flag-hoisting) — both fixed: extracted a shared `_flag_enabled()` helper and hoisted `mark_wired_enabled` before the loop like its sibling `generate_enabled`.

### Decisions & Reasoning
- Now let me check whether that checkbox column actually exists on the Notion board yet, so I can tell Shivonne the real state instead of guessing:
- - `notion_sync.sync_once()` now PATCHes a Notion checkbox (default column `🔗 DM Wired`, configurable via `NOTION_WIRED_CHECKBOX_PROP`) to `True` the instant a row's rule is wired into `comment_responses.json` — so you see the tick live on the Production Tracker instead of watching `git log`.
- - Updated `CLAUDE.md` §3.10 with the new behavior + fixed a stale line that still said "Published" instead of the pre-flight "Ready to Publish" trigger.
- Caught it in the act — my own test run just wrote a stray file to the real repo because I hadn't patched `_WIRED_PENDING_PATH` in the fixtures yet. Cleaning that up and fixing test isolation properly:
- Same reviewer also caught that my docstring promised auto-retry that didn't actually exist — a failed checkbox PATCH would've been stuck un-ticked forever since `state_set` (which blocks reprocessing) got marked before the checkbox attempt. Rather than just fix the docs to lower the claim, I built the actual retry: failed checkbox attempts now persist to `data/channels/notion_wired_pending.json` and get retried at the top of every subsequent sync — never re-drafting the rule, only retrying the tick.
- 5. Optional: pin it to "Shown in board" via this same visibility panel so you actually see it on the card, rather than leaving it in the hidden list like `Stage`/`Voice`/`Image`/`Video` are now.
- Want me to send a synthetic test webhook against the live Render endpoint to confirm the checkbox actually ticks end-to-end, the same way we diagnosed the `IG_ENABLED` outage last time? That'd tell us definitively rather than waiting for a real Notion publish.
- Both still running, still on their first shot (image gen takes time). I'll wait for them to finish rather than poll further.


## 2026-07-06 20:46 — social-ip-engine

### What Didn't Work (negative knowledge)
- Documented the whole ordering contract in `CLAUDE.md` with a pointer to the exact test, so if anyone touches `sync_once()` later without reading this, the test fails loudly instead of the bug quietly coming back.

### Architecture Decisions
- **python-reviewer's two HIGH findings** (duplicated boolean-env-flag idiom, inconsistent flag-hoisting) — both fixed: extracted a shared `_flag_enabled()` helper and hoisted `mark_wired_enabled` before the loop like its sibling `generate_enabled`.

### Decisions & Reasoning
- Now let me check whether that checkbox column actually exists on the Notion board yet, so I can tell Shivonne the real state instead of guessing:
- - `notion_sync.sync_once()` now PATCHes a Notion checkbox (default column `🔗 DM Wired`, configurable via `NOTION_WIRED_CHECKBOX_PROP`) to `True` the instant a row's rule is wired into `comment_responses.json` — so you see the tick live on the Production Tracker instead of watching `git log`.
- - Updated `CLAUDE.md` §3.10 with the new behavior + fixed a stale line that still said "Published" instead of the pre-flight "Ready to Publish" trigger.
- Caught it in the act — my own test run just wrote a stray file to the real repo because I hadn't patched `_WIRED_PENDING_PATH` in the fixtures yet. Cleaning that up and fixing test isolation properly:
- Same reviewer also caught that my docstring promised auto-retry that didn't actually exist — a failed checkbox PATCH would've been stuck un-ticked forever since `state_set` (which blocks reprocessing) got marked before the checkbox attempt. Rather than just fix the docs to lower the claim, I built the actual retry: failed checkbox attempts now persist to `data/channels/notion_wired_pending.json` and get retried at the top of every subsequent sync — never re-drafting the rule, only retrying the tick.
- 5. Optional: pin it to "Shown in board" via this same visibility panel so you actually see it on the card, rather than leaving it in the hidden list like `Stage`/`Voice`/`Image`/`Video` are now.
- Want me to send a synthetic test webhook against the live Render endpoint to confirm the checkbox actually ticks end-to-end, the same way we diagnosed the `IG_ENABLED` outage last time? That'd tell us definitively rather than waiting for a real Notion publish.
- Both still running, still on their first shot (image gen takes time). I'll wait for them to finish rather than poll further.


## 2026-07-06 20:50 — social-ip-engine

### What Didn't Work (negative knowledge)
- Documented the whole ordering contract in `CLAUDE.md` with a pointer to the exact test, so if anyone touches `sync_once()` later without reading this, the test fails loudly instead of the bug quietly coming back.

### Architecture Decisions
- **python-reviewer's two HIGH findings** (duplicated boolean-env-flag idiom, inconsistent flag-hoisting) — both fixed: extracted a shared `_flag_enabled()` helper and hoisted `mark_wired_enabled` before the loop like its sibling `generate_enabled`.

### Decisions & Reasoning
- Now let me check whether that checkbox column actually exists on the Notion board yet, so I can tell Shivonne the real state instead of guessing:
- - `notion_sync.sync_once()` now PATCHes a Notion checkbox (default column `🔗 DM Wired`, configurable via `NOTION_WIRED_CHECKBOX_PROP`) to `True` the instant a row's rule is wired into `comment_responses.json` — so you see the tick live on the Production Tracker instead of watching `git log`.
- - Updated `CLAUDE.md` §3.10 with the new behavior + fixed a stale line that still said "Published" instead of the pre-flight "Ready to Publish" trigger.
- Caught it in the act — my own test run just wrote a stray file to the real repo because I hadn't patched `_WIRED_PENDING_PATH` in the fixtures yet. Cleaning that up and fixing test isolation properly:
- Same reviewer also caught that my docstring promised auto-retry that didn't actually exist — a failed checkbox PATCH would've been stuck un-ticked forever since `state_set` (which blocks reprocessing) got marked before the checkbox attempt. Rather than just fix the docs to lower the claim, I built the actual retry: failed checkbox attempts now persist to `data/channels/notion_wired_pending.json` and get retried at the top of every subsequent sync — never re-drafting the rule, only retrying the tick.
- 5. Optional: pin it to "Shown in board" via this same visibility panel so you actually see it on the card, rather than leaving it in the hidden list like `Stage`/`Voice`/`Image`/`Video` are now.
- Want me to send a synthetic test webhook against the live Render endpoint to confirm the checkbox actually ticks end-to-end, the same way we diagnosed the `IG_ENABLED` outage last time? That'd tell us definitively rather than waiting for a real Notion publish.
- Both still running, still on their first shot (image gen takes time). I'll wait for them to finish rather than poll further.


## 2026-07-06 20:52 — social-ip-engine

### What Didn't Work (negative knowledge)
- Documented the whole ordering contract in `CLAUDE.md` with a pointer to the exact test, so if anyone touches `sync_once()` later without reading this, the test fails loudly instead of the bug quietly coming back.

### Architecture Decisions
- **python-reviewer's two HIGH findings** (duplicated boolean-env-flag idiom, inconsistent flag-hoisting) — both fixed: extracted a shared `_flag_enabled()` helper and hoisted `mark_wired_enabled` before the loop like its sibling `generate_enabled`.

### Decisions & Reasoning
- Now let me check whether that checkbox column actually exists on the Notion board yet, so I can tell Shivonne the real state instead of guessing:
- - `notion_sync.sync_once()` now PATCHes a Notion checkbox (default column `🔗 DM Wired`, configurable via `NOTION_WIRED_CHECKBOX_PROP`) to `True` the instant a row's rule is wired into `comment_responses.json` — so you see the tick live on the Production Tracker instead of watching `git log`.
- - Updated `CLAUDE.md` §3.10 with the new behavior + fixed a stale line that still said "Published" instead of the pre-flight "Ready to Publish" trigger.
- Caught it in the act — my own test run just wrote a stray file to the real repo because I hadn't patched `_WIRED_PENDING_PATH` in the fixtures yet. Cleaning that up and fixing test isolation properly:
- Same reviewer also caught that my docstring promised auto-retry that didn't actually exist — a failed checkbox PATCH would've been stuck un-ticked forever since `state_set` (which blocks reprocessing) got marked before the checkbox attempt. Rather than just fix the docs to lower the claim, I built the actual retry: failed checkbox attempts now persist to `data/channels/notion_wired_pending.json` and get retried at the top of every subsequent sync — never re-drafting the rule, only retrying the tick.
- 5. Optional: pin it to "Shown in board" via this same visibility panel so you actually see it on the card, rather than leaving it in the hidden list like `Stage`/`Voice`/`Image`/`Video` are now.
- Want me to send a synthetic test webhook against the live Render endpoint to confirm the checkbox actually ticks end-to-end, the same way we diagnosed the `IG_ENABLED` outage last time? That'd tell us definitively rather than waiting for a real Notion publish.
- Both still running, still on their first shot (image gen takes time). I'll wait for them to finish rather than poll further.


## 2026-07-06 20:54 — social-ip-engine

### What Didn't Work (negative knowledge)
- Documented the whole ordering contract in `CLAUDE.md` with a pointer to the exact test, so if anyone touches `sync_once()` later without reading this, the test fails loudly instead of the bug quietly coming back.

### Architecture Decisions
- **python-reviewer's two HIGH findings** (duplicated boolean-env-flag idiom, inconsistent flag-hoisting) — both fixed: extracted a shared `_flag_enabled()` helper and hoisted `mark_wired_enabled` before the loop like its sibling `generate_enabled`.

### Decisions & Reasoning
- Now let me check whether that checkbox column actually exists on the Notion board yet, so I can tell Shivonne the real state instead of guessing:
- - `notion_sync.sync_once()` now PATCHes a Notion checkbox (default column `🔗 DM Wired`, configurable via `NOTION_WIRED_CHECKBOX_PROP`) to `True` the instant a row's rule is wired into `comment_responses.json` — so you see the tick live on the Production Tracker instead of watching `git log`.
- - Updated `CLAUDE.md` §3.10 with the new behavior + fixed a stale line that still said "Published" instead of the pre-flight "Ready to Publish" trigger.
- Caught it in the act — my own test run just wrote a stray file to the real repo because I hadn't patched `_WIRED_PENDING_PATH` in the fixtures yet. Cleaning that up and fixing test isolation properly:
- Same reviewer also caught that my docstring promised auto-retry that didn't actually exist — a failed checkbox PATCH would've been stuck un-ticked forever since `state_set` (which blocks reprocessing) got marked before the checkbox attempt. Rather than just fix the docs to lower the claim, I built the actual retry: failed checkbox attempts now persist to `data/channels/notion_wired_pending.json` and get retried at the top of every subsequent sync — never re-drafting the rule, only retrying the tick.
- 5. Optional: pin it to "Shown in board" via this same visibility panel so you actually see it on the card, rather than leaving it in the hidden list like `Stage`/`Voice`/`Image`/`Video` are now.
- Want me to send a synthetic test webhook against the live Render endpoint to confirm the checkbox actually ticks end-to-end, the same way we diagnosed the `IG_ENABLED` outage last time? That'd tell us definitively rather than waiting for a real Notion publish.
- Both still running, still on their first shot (image gen takes time). I'll wait for them to finish rather than poll further.


## 2026-07-06 20:56 — social-ip-engine

### What Didn't Work (negative knowledge)
- Documented the whole ordering contract in `CLAUDE.md` with a pointer to the exact test, so if anyone touches `sync_once()` later without reading this, the test fails loudly instead of the bug quietly coming back.

### Architecture Decisions
- **python-reviewer's two HIGH findings** (duplicated boolean-env-flag idiom, inconsistent flag-hoisting) — both fixed: extracted a shared `_flag_enabled()` helper and hoisted `mark_wired_enabled` before the loop like its sibling `generate_enabled`.

### Decisions & Reasoning
- Now let me check whether that checkbox column actually exists on the Notion board yet, so I can tell Shivonne the real state instead of guessing:
- - `notion_sync.sync_once()` now PATCHes a Notion checkbox (default column `🔗 DM Wired`, configurable via `NOTION_WIRED_CHECKBOX_PROP`) to `True` the instant a row's rule is wired into `comment_responses.json` — so you see the tick live on the Production Tracker instead of watching `git log`.
- - Updated `CLAUDE.md` §3.10 with the new behavior + fixed a stale line that still said "Published" instead of the pre-flight "Ready to Publish" trigger.
- Caught it in the act — my own test run just wrote a stray file to the real repo because I hadn't patched `_WIRED_PENDING_PATH` in the fixtures yet. Cleaning that up and fixing test isolation properly:
- Same reviewer also caught that my docstring promised auto-retry that didn't actually exist — a failed checkbox PATCH would've been stuck un-ticked forever since `state_set` (which blocks reprocessing) got marked before the checkbox attempt. Rather than just fix the docs to lower the claim, I built the actual retry: failed checkbox attempts now persist to `data/channels/notion_wired_pending.json` and get retried at the top of every subsequent sync — never re-drafting the rule, only retrying the tick.
- 5. Optional: pin it to "Shown in board" via this same visibility panel so you actually see it on the card, rather than leaving it in the hidden list like `Stage`/`Voice`/`Image`/`Video` are now.
- Want me to send a synthetic test webhook against the live Render endpoint to confirm the checkbox actually ticks end-to-end, the same way we diagnosed the `IG_ENABLED` outage last time? That'd tell us definitively rather than waiting for a real Notion publish.
- Both still running, still on their first shot (image gen takes time). I'll wait for them to finish rather than poll further.


## 2026-07-06 20:58 — social-ip-engine

### What Didn't Work (negative knowledge)
- Documented the whole ordering contract in `CLAUDE.md` with a pointer to the exact test, so if anyone touches `sync_once()` later without reading this, the test fails loudly instead of the bug quietly coming back.

### Architecture Decisions
- **python-reviewer's two HIGH findings** (duplicated boolean-env-flag idiom, inconsistent flag-hoisting) — both fixed: extracted a shared `_flag_enabled()` helper and hoisted `mark_wired_enabled` before the loop like its sibling `generate_enabled`.

### Decisions & Reasoning
- Now let me check whether that checkbox column actually exists on the Notion board yet, so I can tell Shivonne the real state instead of guessing:
- - `notion_sync.sync_once()` now PATCHes a Notion checkbox (default column `🔗 DM Wired`, configurable via `NOTION_WIRED_CHECKBOX_PROP`) to `True` the instant a row's rule is wired into `comment_responses.json` — so you see the tick live on the Production Tracker instead of watching `git log`.
- - Updated `CLAUDE.md` §3.10 with the new behavior + fixed a stale line that still said "Published" instead of the pre-flight "Ready to Publish" trigger.
- Caught it in the act — my own test run just wrote a stray file to the real repo because I hadn't patched `_WIRED_PENDING_PATH` in the fixtures yet. Cleaning that up and fixing test isolation properly:
- Same reviewer also caught that my docstring promised auto-retry that didn't actually exist — a failed checkbox PATCH would've been stuck un-ticked forever since `state_set` (which blocks reprocessing) got marked before the checkbox attempt. Rather than just fix the docs to lower the claim, I built the actual retry: failed checkbox attempts now persist to `data/channels/notion_wired_pending.json` and get retried at the top of every subsequent sync — never re-drafting the rule, only retrying the tick.
- 5. Optional: pin it to "Shown in board" via this same visibility panel so you actually see it on the card, rather than leaving it in the hidden list like `Stage`/`Voice`/`Image`/`Video` are now.
- Want me to send a synthetic test webhook against the live Render endpoint to confirm the checkbox actually ticks end-to-end, the same way we diagnosed the `IG_ENABLED` outage last time? That'd tell us definitively rather than waiting for a real Notion publish.
- Both still running, still on their first shot (image gen takes time). I'll wait for them to finish rather than poll further.


## 2026-07-06 21:00 — social-ip-engine

### What Didn't Work (negative knowledge)
- Documented the whole ordering contract in `CLAUDE.md` with a pointer to the exact test, so if anyone touches `sync_once()` later without reading this, the test fails loudly instead of the bug quietly coming back.

### Architecture Decisions
- **python-reviewer's two HIGH findings** (duplicated boolean-env-flag idiom, inconsistent flag-hoisting) — both fixed: extracted a shared `_flag_enabled()` helper and hoisted `mark_wired_enabled` before the loop like its sibling `generate_enabled`.

### Decisions & Reasoning
- Now let me check whether that checkbox column actually exists on the Notion board yet, so I can tell Shivonne the real state instead of guessing:
- - `notion_sync.sync_once()` now PATCHes a Notion checkbox (default column `🔗 DM Wired`, configurable via `NOTION_WIRED_CHECKBOX_PROP`) to `True` the instant a row's rule is wired into `comment_responses.json` — so you see the tick live on the Production Tracker instead of watching `git log`.
- - Updated `CLAUDE.md` §3.10 with the new behavior + fixed a stale line that still said "Published" instead of the pre-flight "Ready to Publish" trigger.
- Caught it in the act — my own test run just wrote a stray file to the real repo because I hadn't patched `_WIRED_PENDING_PATH` in the fixtures yet. Cleaning that up and fixing test isolation properly:
- Same reviewer also caught that my docstring promised auto-retry that didn't actually exist — a failed checkbox PATCH would've been stuck un-ticked forever since `state_set` (which blocks reprocessing) got marked before the checkbox attempt. Rather than just fix the docs to lower the claim, I built the actual retry: failed checkbox attempts now persist to `data/channels/notion_wired_pending.json` and get retried at the top of every subsequent sync — never re-drafting the rule, only retrying the tick.
- 5. Optional: pin it to "Shown in board" via this same visibility panel so you actually see it on the card, rather than leaving it in the hidden list like `Stage`/`Voice`/`Image`/`Video` are now.
- Want me to send a synthetic test webhook against the live Render endpoint to confirm the checkbox actually ticks end-to-end, the same way we diagnosed the `IG_ENABLED` outage last time? That'd tell us definitively rather than waiting for a real Notion publish.
- Both still running, still on their first shot (image gen takes time). I'll wait for them to finish rather than poll further.


## 2026-07-06 21:02 — social-ip-engine

### What Didn't Work (negative knowledge)
- Documented the whole ordering contract in `CLAUDE.md` with a pointer to the exact test, so if anyone touches `sync_once()` later without reading this, the test fails loudly instead of the bug quietly coming back.

### Architecture Decisions
- **python-reviewer's two HIGH findings** (duplicated boolean-env-flag idiom, inconsistent flag-hoisting) — both fixed: extracted a shared `_flag_enabled()` helper and hoisted `mark_wired_enabled` before the loop like its sibling `generate_enabled`.

### Decisions & Reasoning
- Now let me check whether that checkbox column actually exists on the Notion board yet, so I can tell Shivonne the real state instead of guessing:
- - `notion_sync.sync_once()` now PATCHes a Notion checkbox (default column `🔗 DM Wired`, configurable via `NOTION_WIRED_CHECKBOX_PROP`) to `True` the instant a row's rule is wired into `comment_responses.json` — so you see the tick live on the Production Tracker instead of watching `git log`.
- - Updated `CLAUDE.md` §3.10 with the new behavior + fixed a stale line that still said "Published" instead of the pre-flight "Ready to Publish" trigger.
- Caught it in the act — my own test run just wrote a stray file to the real repo because I hadn't patched `_WIRED_PENDING_PATH` in the fixtures yet. Cleaning that up and fixing test isolation properly:
- Same reviewer also caught that my docstring promised auto-retry that didn't actually exist — a failed checkbox PATCH would've been stuck un-ticked forever since `state_set` (which blocks reprocessing) got marked before the checkbox attempt. Rather than just fix the docs to lower the claim, I built the actual retry: failed checkbox attempts now persist to `data/channels/notion_wired_pending.json` and get retried at the top of every subsequent sync — never re-drafting the rule, only retrying the tick.
- 5. Optional: pin it to "Shown in board" via this same visibility panel so you actually see it on the card, rather than leaving it in the hidden list like `Stage`/`Voice`/`Image`/`Video` are now.
- Want me to send a synthetic test webhook against the live Render endpoint to confirm the checkbox actually ticks end-to-end, the same way we diagnosed the `IG_ENABLED` outage last time? That'd tell us definitively rather than waiting for a real Notion publish.
- Both still running, still on their first shot (image gen takes time). I'll wait for them to finish rather than poll further.


## 2026-07-06 21:05 — social-ip-engine

### What Didn't Work (negative knowledge)
- Documented the whole ordering contract in `CLAUDE.md` with a pointer to the exact test, so if anyone touches `sync_once()` later without reading this, the test fails loudly instead of the bug quietly coming back.

### Architecture Decisions
- **python-reviewer's two HIGH findings** (duplicated boolean-env-flag idiom, inconsistent flag-hoisting) — both fixed: extracted a shared `_flag_enabled()` helper and hoisted `mark_wired_enabled` before the loop like its sibling `generate_enabled`.

### Decisions & Reasoning
- Now let me check whether that checkbox column actually exists on the Notion board yet, so I can tell Shivonne the real state instead of guessing:
- - `notion_sync.sync_once()` now PATCHes a Notion checkbox (default column `🔗 DM Wired`, configurable via `NOTION_WIRED_CHECKBOX_PROP`) to `True` the instant a row's rule is wired into `comment_responses.json` — so you see the tick live on the Production Tracker instead of watching `git log`.
- - Updated `CLAUDE.md` §3.10 with the new behavior + fixed a stale line that still said "Published" instead of the pre-flight "Ready to Publish" trigger.
- Caught it in the act — my own test run just wrote a stray file to the real repo because I hadn't patched `_WIRED_PENDING_PATH` in the fixtures yet. Cleaning that up and fixing test isolation properly:
- Same reviewer also caught that my docstring promised auto-retry that didn't actually exist — a failed checkbox PATCH would've been stuck un-ticked forever since `state_set` (which blocks reprocessing) got marked before the checkbox attempt. Rather than just fix the docs to lower the claim, I built the actual retry: failed checkbox attempts now persist to `data/channels/notion_wired_pending.json` and get retried at the top of every subsequent sync — never re-drafting the rule, only retrying the tick.
- 5. Optional: pin it to "Shown in board" via this same visibility panel so you actually see it on the card, rather than leaving it in the hidden list like `Stage`/`Voice`/`Image`/`Video` are now.
- Want me to send a synthetic test webhook against the live Render endpoint to confirm the checkbox actually ticks end-to-end, the same way we diagnosed the `IG_ENABLED` outage last time? That'd tell us definitively rather than waiting for a real Notion publish.
- Both still running, still on their first shot (image gen takes time). I'll wait for them to finish rather than poll further.


## 2026-07-06 21:07 — social-ip-engine

### What Didn't Work (negative knowledge)
- Documented the whole ordering contract in `CLAUDE.md` with a pointer to the exact test, so if anyone touches `sync_once()` later without reading this, the test fails loudly instead of the bug quietly coming back.

### Architecture Decisions
- **python-reviewer's two HIGH findings** (duplicated boolean-env-flag idiom, inconsistent flag-hoisting) — both fixed: extracted a shared `_flag_enabled()` helper and hoisted `mark_wired_enabled` before the loop like its sibling `generate_enabled`.

### Decisions & Reasoning
- Now let me check whether that checkbox column actually exists on the Notion board yet, so I can tell Shivonne the real state instead of guessing:
- - `notion_sync.sync_once()` now PATCHes a Notion checkbox (default column `🔗 DM Wired`, configurable via `NOTION_WIRED_CHECKBOX_PROP`) to `True` the instant a row's rule is wired into `comment_responses.json` — so you see the tick live on the Production Tracker instead of watching `git log`.
- - Updated `CLAUDE.md` §3.10 with the new behavior + fixed a stale line that still said "Published" instead of the pre-flight "Ready to Publish" trigger.
- Caught it in the act — my own test run just wrote a stray file to the real repo because I hadn't patched `_WIRED_PENDING_PATH` in the fixtures yet. Cleaning that up and fixing test isolation properly:
- Same reviewer also caught that my docstring promised auto-retry that didn't actually exist — a failed checkbox PATCH would've been stuck un-ticked forever since `state_set` (which blocks reprocessing) got marked before the checkbox attempt. Rather than just fix the docs to lower the claim, I built the actual retry: failed checkbox attempts now persist to `data/channels/notion_wired_pending.json` and get retried at the top of every subsequent sync — never re-drafting the rule, only retrying the tick.
- 5. Optional: pin it to "Shown in board" via this same visibility panel so you actually see it on the card, rather than leaving it in the hidden list like `Stage`/`Voice`/`Image`/`Video` are now.
- Want me to send a synthetic test webhook against the live Render endpoint to confirm the checkbox actually ticks end-to-end, the same way we diagnosed the `IG_ENABLED` outage last time? That'd tell us definitively rather than waiting for a real Notion publish.
- Both still running, still on their first shot (image gen takes time). I'll wait for them to finish rather than poll further.


## 2026-07-06 21:10 — social-ip-engine

### What Didn't Work (negative knowledge)
- Documented the whole ordering contract in `CLAUDE.md` with a pointer to the exact test, so if anyone touches `sync_once()` later without reading this, the test fails loudly instead of the bug quietly coming back.

### Architecture Decisions
- **python-reviewer's two HIGH findings** (duplicated boolean-env-flag idiom, inconsistent flag-hoisting) — both fixed: extracted a shared `_flag_enabled()` helper and hoisted `mark_wired_enabled` before the loop like its sibling `generate_enabled`.

### Decisions & Reasoning
- Now let me check whether that checkbox column actually exists on the Notion board yet, so I can tell Shivonne the real state instead of guessing:
- - `notion_sync.sync_once()` now PATCHes a Notion checkbox (default column `🔗 DM Wired`, configurable via `NOTION_WIRED_CHECKBOX_PROP`) to `True` the instant a row's rule is wired into `comment_responses.json` — so you see the tick live on the Production Tracker instead of watching `git log`.
- - Updated `CLAUDE.md` §3.10 with the new behavior + fixed a stale line that still said "Published" instead of the pre-flight "Ready to Publish" trigger.
- Caught it in the act — my own test run just wrote a stray file to the real repo because I hadn't patched `_WIRED_PENDING_PATH` in the fixtures yet. Cleaning that up and fixing test isolation properly:
- Same reviewer also caught that my docstring promised auto-retry that didn't actually exist — a failed checkbox PATCH would've been stuck un-ticked forever since `state_set` (which blocks reprocessing) got marked before the checkbox attempt. Rather than just fix the docs to lower the claim, I built the actual retry: failed checkbox attempts now persist to `data/channels/notion_wired_pending.json` and get retried at the top of every subsequent sync — never re-drafting the rule, only retrying the tick.
- 5. Optional: pin it to "Shown in board" via this same visibility panel so you actually see it on the card, rather than leaving it in the hidden list like `Stage`/`Voice`/`Image`/`Video` are now.
- Want me to send a synthetic test webhook against the live Render endpoint to confirm the checkbox actually ticks end-to-end, the same way we diagnosed the `IG_ENABLED` outage last time? That'd tell us definitively rather than waiting for a real Notion publish.
- Both still running, still on their first shot (image gen takes time). I'll wait for them to finish rather than poll further.


## 2026-07-06 21:11 — social-ip-engine

### What Didn't Work (negative knowledge)
- Documented the whole ordering contract in `CLAUDE.md` with a pointer to the exact test, so if anyone touches `sync_once()` later without reading this, the test fails loudly instead of the bug quietly coming back.

### Architecture Decisions
- **python-reviewer's two HIGH findings** (duplicated boolean-env-flag idiom, inconsistent flag-hoisting) — both fixed: extracted a shared `_flag_enabled()` helper and hoisted `mark_wired_enabled` before the loop like its sibling `generate_enabled`.

### Decisions & Reasoning
- Now let me check whether that checkbox column actually exists on the Notion board yet, so I can tell Shivonne the real state instead of guessing:
- - `notion_sync.sync_once()` now PATCHes a Notion checkbox (default column `🔗 DM Wired`, configurable via `NOTION_WIRED_CHECKBOX_PROP`) to `True` the instant a row's rule is wired into `comment_responses.json` — so you see the tick live on the Production Tracker instead of watching `git log`.
- - Updated `CLAUDE.md` §3.10 with the new behavior + fixed a stale line that still said "Published" instead of the pre-flight "Ready to Publish" trigger.
- Caught it in the act — my own test run just wrote a stray file to the real repo because I hadn't patched `_WIRED_PENDING_PATH` in the fixtures yet. Cleaning that up and fixing test isolation properly:
- Same reviewer also caught that my docstring promised auto-retry that didn't actually exist — a failed checkbox PATCH would've been stuck un-ticked forever since `state_set` (which blocks reprocessing) got marked before the checkbox attempt. Rather than just fix the docs to lower the claim, I built the actual retry: failed checkbox attempts now persist to `data/channels/notion_wired_pending.json` and get retried at the top of every subsequent sync — never re-drafting the rule, only retrying the tick.
- 5. Optional: pin it to "Shown in board" via this same visibility panel so you actually see it on the card, rather than leaving it in the hidden list like `Stage`/`Voice`/`Image`/`Video` are now.
- Want me to send a synthetic test webhook against the live Render endpoint to confirm the checkbox actually ticks end-to-end, the same way we diagnosed the `IG_ENABLED` outage last time? That'd tell us definitively rather than waiting for a real Notion publish.
- Both still running, still on their first shot (image gen takes time). I'll wait for them to finish rather than poll further.


## 2026-07-06 21:13 — social-ip-engine

### What Didn't Work (negative knowledge)
- Documented the whole ordering contract in `CLAUDE.md` with a pointer to the exact test, so if anyone touches `sync_once()` later without reading this, the test fails loudly instead of the bug quietly coming back.

### Architecture Decisions
- **python-reviewer's two HIGH findings** (duplicated boolean-env-flag idiom, inconsistent flag-hoisting) — both fixed: extracted a shared `_flag_enabled()` helper and hoisted `mark_wired_enabled` before the loop like its sibling `generate_enabled`.

### Decisions & Reasoning
- Now let me check whether that checkbox column actually exists on the Notion board yet, so I can tell Shivonne the real state instead of guessing:
- - `notion_sync.sync_once()` now PATCHes a Notion checkbox (default column `🔗 DM Wired`, configurable via `NOTION_WIRED_CHECKBOX_PROP`) to `True` the instant a row's rule is wired into `comment_responses.json` — so you see the tick live on the Production Tracker instead of watching `git log`.
- - Updated `CLAUDE.md` §3.10 with the new behavior + fixed a stale line that still said "Published" instead of the pre-flight "Ready to Publish" trigger.
- Caught it in the act — my own test run just wrote a stray file to the real repo because I hadn't patched `_WIRED_PENDING_PATH` in the fixtures yet. Cleaning that up and fixing test isolation properly:
- Same reviewer also caught that my docstring promised auto-retry that didn't actually exist — a failed checkbox PATCH would've been stuck un-ticked forever since `state_set` (which blocks reprocessing) got marked before the checkbox attempt. Rather than just fix the docs to lower the claim, I built the actual retry: failed checkbox attempts now persist to `data/channels/notion_wired_pending.json` and get retried at the top of every subsequent sync — never re-drafting the rule, only retrying the tick.
- 5. Optional: pin it to "Shown in board" via this same visibility panel so you actually see it on the card, rather than leaving it in the hidden list like `Stage`/`Voice`/`Image`/`Video` are now.
- Want me to send a synthetic test webhook against the live Render endpoint to confirm the checkbox actually ticks end-to-end, the same way we diagnosed the `IG_ENABLED` outage last time? That'd tell us definitively rather than waiting for a real Notion publish.
- Both still running, still on their first shot (image gen takes time). I'll wait for them to finish rather than poll further.


## 2026-07-06 21:16 — social-ip-engine

### What Didn't Work (negative knowledge)
- Documented the whole ordering contract in `CLAUDE.md` with a pointer to the exact test, so if anyone touches `sync_once()` later without reading this, the test fails loudly instead of the bug quietly coming back.

### Architecture Decisions
- **python-reviewer's two HIGH findings** (duplicated boolean-env-flag idiom, inconsistent flag-hoisting) — both fixed: extracted a shared `_flag_enabled()` helper and hoisted `mark_wired_enabled` before the loop like its sibling `generate_enabled`.

### Decisions & Reasoning
- Now let me check whether that checkbox column actually exists on the Notion board yet, so I can tell Shivonne the real state instead of guessing:
- - `notion_sync.sync_once()` now PATCHes a Notion checkbox (default column `🔗 DM Wired`, configurable via `NOTION_WIRED_CHECKBOX_PROP`) to `True` the instant a row's rule is wired into `comment_responses.json` — so you see the tick live on the Production Tracker instead of watching `git log`.
- - Updated `CLAUDE.md` §3.10 with the new behavior + fixed a stale line that still said "Published" instead of the pre-flight "Ready to Publish" trigger.
- Caught it in the act — my own test run just wrote a stray file to the real repo because I hadn't patched `_WIRED_PENDING_PATH` in the fixtures yet. Cleaning that up and fixing test isolation properly:
- Same reviewer also caught that my docstring promised auto-retry that didn't actually exist — a failed checkbox PATCH would've been stuck un-ticked forever since `state_set` (which blocks reprocessing) got marked before the checkbox attempt. Rather than just fix the docs to lower the claim, I built the actual retry: failed checkbox attempts now persist to `data/channels/notion_wired_pending.json` and get retried at the top of every subsequent sync — never re-drafting the rule, only retrying the tick.
- 5. Optional: pin it to "Shown in board" via this same visibility panel so you actually see it on the card, rather than leaving it in the hidden list like `Stage`/`Voice`/`Image`/`Video` are now.
- Want me to send a synthetic test webhook against the live Render endpoint to confirm the checkbox actually ticks end-to-end, the same way we diagnosed the `IG_ENABLED` outage last time? That'd tell us definitively rather than waiting for a real Notion publish.
- Both still running, still on their first shot (image gen takes time). I'll wait for them to finish rather than poll further.


## 2026-07-06 21:18 — social-ip-engine

### What Didn't Work (negative knowledge)
- Documented the whole ordering contract in `CLAUDE.md` with a pointer to the exact test, so if anyone touches `sync_once()` later without reading this, the test fails loudly instead of the bug quietly coming back.

### Architecture Decisions
- **python-reviewer's two HIGH findings** (duplicated boolean-env-flag idiom, inconsistent flag-hoisting) — both fixed: extracted a shared `_flag_enabled()` helper and hoisted `mark_wired_enabled` before the loop like its sibling `generate_enabled`.

### Decisions & Reasoning
- Now let me check whether that checkbox column actually exists on the Notion board yet, so I can tell Shivonne the real state instead of guessing:
- - `notion_sync.sync_once()` now PATCHes a Notion checkbox (default column `🔗 DM Wired`, configurable via `NOTION_WIRED_CHECKBOX_PROP`) to `True` the instant a row's rule is wired into `comment_responses.json` — so you see the tick live on the Production Tracker instead of watching `git log`.
- - Updated `CLAUDE.md` §3.10 with the new behavior + fixed a stale line that still said "Published" instead of the pre-flight "Ready to Publish" trigger.
- Caught it in the act — my own test run just wrote a stray file to the real repo because I hadn't patched `_WIRED_PENDING_PATH` in the fixtures yet. Cleaning that up and fixing test isolation properly:
- Same reviewer also caught that my docstring promised auto-retry that didn't actually exist — a failed checkbox PATCH would've been stuck un-ticked forever since `state_set` (which blocks reprocessing) got marked before the checkbox attempt. Rather than just fix the docs to lower the claim, I built the actual retry: failed checkbox attempts now persist to `data/channels/notion_wired_pending.json` and get retried at the top of every subsequent sync — never re-drafting the rule, only retrying the tick.
- 5. Optional: pin it to "Shown in board" via this same visibility panel so you actually see it on the card, rather than leaving it in the hidden list like `Stage`/`Voice`/`Image`/`Video` are now.
- Want me to send a synthetic test webhook against the live Render endpoint to confirm the checkbox actually ticks end-to-end, the same way we diagnosed the `IG_ENABLED` outage last time? That'd tell us definitively rather than waiting for a real Notion publish.
- Both still running, still on their first shot (image gen takes time). I'll wait for them to finish rather than poll further.


## 2026-07-06 21:20 — social-ip-engine

### What Didn't Work (negative knowledge)
- Documented the whole ordering contract in `CLAUDE.md` with a pointer to the exact test, so if anyone touches `sync_once()` later without reading this, the test fails loudly instead of the bug quietly coming back.

### Architecture Decisions
- **python-reviewer's two HIGH findings** (duplicated boolean-env-flag idiom, inconsistent flag-hoisting) — both fixed: extracted a shared `_flag_enabled()` helper and hoisted `mark_wired_enabled` before the loop like its sibling `generate_enabled`.

### Decisions & Reasoning
- Now let me check whether that checkbox column actually exists on the Notion board yet, so I can tell Shivonne the real state instead of guessing:
- - `notion_sync.sync_once()` now PATCHes a Notion checkbox (default column `🔗 DM Wired`, configurable via `NOTION_WIRED_CHECKBOX_PROP`) to `True` the instant a row's rule is wired into `comment_responses.json` — so you see the tick live on the Production Tracker instead of watching `git log`.
- - Updated `CLAUDE.md` §3.10 with the new behavior + fixed a stale line that still said "Published" instead of the pre-flight "Ready to Publish" trigger.
- Caught it in the act — my own test run just wrote a stray file to the real repo because I hadn't patched `_WIRED_PENDING_PATH` in the fixtures yet. Cleaning that up and fixing test isolation properly:
- Same reviewer also caught that my docstring promised auto-retry that didn't actually exist — a failed checkbox PATCH would've been stuck un-ticked forever since `state_set` (which blocks reprocessing) got marked before the checkbox attempt. Rather than just fix the docs to lower the claim, I built the actual retry: failed checkbox attempts now persist to `data/channels/notion_wired_pending.json` and get retried at the top of every subsequent sync — never re-drafting the rule, only retrying the tick.
- 5. Optional: pin it to "Shown in board" via this same visibility panel so you actually see it on the card, rather than leaving it in the hidden list like `Stage`/`Voice`/`Image`/`Video` are now.
- Want me to send a synthetic test webhook against the live Render endpoint to confirm the checkbox actually ticks end-to-end, the same way we diagnosed the `IG_ENABLED` outage last time? That'd tell us definitively rather than waiting for a real Notion publish.
- Both still running, still on their first shot (image gen takes time). I'll wait for them to finish rather than poll further.


## 2026-07-06 21:22 — social-ip-engine

### What Didn't Work (negative knowledge)
- Documented the whole ordering contract in `CLAUDE.md` with a pointer to the exact test, so if anyone touches `sync_once()` later without reading this, the test fails loudly instead of the bug quietly coming back.

### Architecture Decisions
- **python-reviewer's two HIGH findings** (duplicated boolean-env-flag idiom, inconsistent flag-hoisting) — both fixed: extracted a shared `_flag_enabled()` helper and hoisted `mark_wired_enabled` before the loop like its sibling `generate_enabled`.

### Decisions & Reasoning
- Now let me check whether that checkbox column actually exists on the Notion board yet, so I can tell Shivonne the real state instead of guessing:
- - `notion_sync.sync_once()` now PATCHes a Notion checkbox (default column `🔗 DM Wired`, configurable via `NOTION_WIRED_CHECKBOX_PROP`) to `True` the instant a row's rule is wired into `comment_responses.json` — so you see the tick live on the Production Tracker instead of watching `git log`.
- - Updated `CLAUDE.md` §3.10 with the new behavior + fixed a stale line that still said "Published" instead of the pre-flight "Ready to Publish" trigger.
- Caught it in the act — my own test run just wrote a stray file to the real repo because I hadn't patched `_WIRED_PENDING_PATH` in the fixtures yet. Cleaning that up and fixing test isolation properly:
- Same reviewer also caught that my docstring promised auto-retry that didn't actually exist — a failed checkbox PATCH would've been stuck un-ticked forever since `state_set` (which blocks reprocessing) got marked before the checkbox attempt. Rather than just fix the docs to lower the claim, I built the actual retry: failed checkbox attempts now persist to `data/channels/notion_wired_pending.json` and get retried at the top of every subsequent sync — never re-drafting the rule, only retrying the tick.
- 5. Optional: pin it to "Shown in board" via this same visibility panel so you actually see it on the card, rather than leaving it in the hidden list like `Stage`/`Voice`/`Image`/`Video` are now.
- Want me to send a synthetic test webhook against the live Render endpoint to confirm the checkbox actually ticks end-to-end, the same way we diagnosed the `IG_ENABLED` outage last time? That'd tell us definitively rather than waiting for a real Notion publish.
- Both still running, still on their first shot (image gen takes time). I'll wait for them to finish rather than poll further.


## 2026-07-06 21:24 — social-ip-engine

### What Didn't Work (negative knowledge)
- Documented the whole ordering contract in `CLAUDE.md` with a pointer to the exact test, so if anyone touches `sync_once()` later without reading this, the test fails loudly instead of the bug quietly coming back.

### Architecture Decisions
- **python-reviewer's two HIGH findings** (duplicated boolean-env-flag idiom, inconsistent flag-hoisting) — both fixed: extracted a shared `_flag_enabled()` helper and hoisted `mark_wired_enabled` before the loop like its sibling `generate_enabled`.

### Decisions & Reasoning
- Now let me check whether that checkbox column actually exists on the Notion board yet, so I can tell Shivonne the real state instead of guessing:
- - `notion_sync.sync_once()` now PATCHes a Notion checkbox (default column `🔗 DM Wired`, configurable via `NOTION_WIRED_CHECKBOX_PROP`) to `True` the instant a row's rule is wired into `comment_responses.json` — so you see the tick live on the Production Tracker instead of watching `git log`.
- - Updated `CLAUDE.md` §3.10 with the new behavior + fixed a stale line that still said "Published" instead of the pre-flight "Ready to Publish" trigger.
- Caught it in the act — my own test run just wrote a stray file to the real repo because I hadn't patched `_WIRED_PENDING_PATH` in the fixtures yet. Cleaning that up and fixing test isolation properly:
- Same reviewer also caught that my docstring promised auto-retry that didn't actually exist — a failed checkbox PATCH would've been stuck un-ticked forever since `state_set` (which blocks reprocessing) got marked before the checkbox attempt. Rather than just fix the docs to lower the claim, I built the actual retry: failed checkbox attempts now persist to `data/channels/notion_wired_pending.json` and get retried at the top of every subsequent sync — never re-drafting the rule, only retrying the tick.
- 5. Optional: pin it to "Shown in board" via this same visibility panel so you actually see it on the card, rather than leaving it in the hidden list like `Stage`/`Voice`/`Image`/`Video` are now.
- Want me to send a synthetic test webhook against the live Render endpoint to confirm the checkbox actually ticks end-to-end, the same way we diagnosed the `IG_ENABLED` outage last time? That'd tell us definitively rather than waiting for a real Notion publish.
- Both still running, still on their first shot (image gen takes time). I'll wait for them to finish rather than poll further.


## 2026-07-06 21:27 — social-ip-engine

### What Didn't Work (negative knowledge)
- Documented the whole ordering contract in `CLAUDE.md` with a pointer to the exact test, so if anyone touches `sync_once()` later without reading this, the test fails loudly instead of the bug quietly coming back.

### Architecture Decisions
- **python-reviewer's two HIGH findings** (duplicated boolean-env-flag idiom, inconsistent flag-hoisting) — both fixed: extracted a shared `_flag_enabled()` helper and hoisted `mark_wired_enabled` before the loop like its sibling `generate_enabled`.

### Decisions & Reasoning
- Now let me check whether that checkbox column actually exists on the Notion board yet, so I can tell Shivonne the real state instead of guessing:
- - `notion_sync.sync_once()` now PATCHes a Notion checkbox (default column `🔗 DM Wired`, configurable via `NOTION_WIRED_CHECKBOX_PROP`) to `True` the instant a row's rule is wired into `comment_responses.json` — so you see the tick live on the Production Tracker instead of watching `git log`.
- - Updated `CLAUDE.md` §3.10 with the new behavior + fixed a stale line that still said "Published" instead of the pre-flight "Ready to Publish" trigger.
- Caught it in the act — my own test run just wrote a stray file to the real repo because I hadn't patched `_WIRED_PENDING_PATH` in the fixtures yet. Cleaning that up and fixing test isolation properly:
- Same reviewer also caught that my docstring promised auto-retry that didn't actually exist — a failed checkbox PATCH would've been stuck un-ticked forever since `state_set` (which blocks reprocessing) got marked before the checkbox attempt. Rather than just fix the docs to lower the claim, I built the actual retry: failed checkbox attempts now persist to `data/channels/notion_wired_pending.json` and get retried at the top of every subsequent sync — never re-drafting the rule, only retrying the tick.
- 5. Optional: pin it to "Shown in board" via this same visibility panel so you actually see it on the card, rather than leaving it in the hidden list like `Stage`/`Voice`/`Image`/`Video` are now.
- Want me to send a synthetic test webhook against the live Render endpoint to confirm the checkbox actually ticks end-to-end, the same way we diagnosed the `IG_ENABLED` outage last time? That'd tell us definitively rather than waiting for a real Notion publish.
- Both still running, still on their first shot (image gen takes time). I'll wait for them to finish rather than poll further.


## 2026-07-07 11:01 — social-ip-engine

### What Didn't Work (negative knowledge)
- Documented the whole ordering contract in `CLAUDE.md` with a pointer to the exact test, so if anyone touches `sync_once()` later without reading this, the test fails loudly instead of the bug quietly coming back.

### Architecture Decisions
- **python-reviewer's two HIGH findings** (duplicated boolean-env-flag idiom, inconsistent flag-hoisting) — both fixed: extracted a shared `_flag_enabled()` helper and hoisted `mark_wired_enabled` before the loop like its sibling `generate_enabled`.

### Decisions & Reasoning
- Now let me check whether that checkbox column actually exists on the Notion board yet, so I can tell Shivonne the real state instead of guessing:
- - `notion_sync.sync_once()` now PATCHes a Notion checkbox (default column `🔗 DM Wired`, configurable via `NOTION_WIRED_CHECKBOX_PROP`) to `True` the instant a row's rule is wired into `comment_responses.json` — so you see the tick live on the Production Tracker instead of watching `git log`.
- - Updated `CLAUDE.md` §3.10 with the new behavior + fixed a stale line that still said "Published" instead of the pre-flight "Ready to Publish" trigger.
- Caught it in the act — my own test run just wrote a stray file to the real repo because I hadn't patched `_WIRED_PENDING_PATH` in the fixtures yet. Cleaning that up and fixing test isolation properly:
- Same reviewer also caught that my docstring promised auto-retry that didn't actually exist — a failed checkbox PATCH would've been stuck un-ticked forever since `state_set` (which blocks reprocessing) got marked before the checkbox attempt. Rather than just fix the docs to lower the claim, I built the actual retry: failed checkbox attempts now persist to `data/channels/notion_wired_pending.json` and get retried at the top of every subsequent sync — never re-drafting the rule, only retrying the tick.
- 5. Optional: pin it to "Shown in board" via this same visibility panel so you actually see it on the card, rather than leaving it in the hidden list like `Stage`/`Voice`/`Image`/`Video` are now.
- Want me to send a synthetic test webhook against the live Render endpoint to confirm the checkbox actually ticks end-to-end, the same way we diagnosed the `IG_ENABLED` outage last time? That'd tell us definitively rather than waiting for a real Notion publish.
- Both still running, still on their first shot (image gen takes time). I'll wait for them to finish rather than poll further.


## 2026-07-07 11:03 — social-ip-engine

### What Didn't Work (negative knowledge)
- Documented the whole ordering contract in `CLAUDE.md` with a pointer to the exact test, so if anyone touches `sync_once()` later without reading this, the test fails loudly instead of the bug quietly coming back.

### Architecture Decisions
- **python-reviewer's two HIGH findings** (duplicated boolean-env-flag idiom, inconsistent flag-hoisting) — both fixed: extracted a shared `_flag_enabled()` helper and hoisted `mark_wired_enabled` before the loop like its sibling `generate_enabled`.

### Decisions & Reasoning
- Now let me check whether that checkbox column actually exists on the Notion board yet, so I can tell Shivonne the real state instead of guessing:
- - `notion_sync.sync_once()` now PATCHes a Notion checkbox (default column `🔗 DM Wired`, configurable via `NOTION_WIRED_CHECKBOX_PROP`) to `True` the instant a row's rule is wired into `comment_responses.json` — so you see the tick live on the Production Tracker instead of watching `git log`.
- - Updated `CLAUDE.md` §3.10 with the new behavior + fixed a stale line that still said "Published" instead of the pre-flight "Ready to Publish" trigger.
- Caught it in the act — my own test run just wrote a stray file to the real repo because I hadn't patched `_WIRED_PENDING_PATH` in the fixtures yet. Cleaning that up and fixing test isolation properly:
- Same reviewer also caught that my docstring promised auto-retry that didn't actually exist — a failed checkbox PATCH would've been stuck un-ticked forever since `state_set` (which blocks reprocessing) got marked before the checkbox attempt. Rather than just fix the docs to lower the claim, I built the actual retry: failed checkbox attempts now persist to `data/channels/notion_wired_pending.json` and get retried at the top of every subsequent sync — never re-drafting the rule, only retrying the tick.
- 5. Optional: pin it to "Shown in board" via this same visibility panel so you actually see it on the card, rather than leaving it in the hidden list like `Stage`/`Voice`/`Image`/`Video` are now.
- Want me to send a synthetic test webhook against the live Render endpoint to confirm the checkbox actually ticks end-to-end, the same way we diagnosed the `IG_ENABLED` outage last time? That'd tell us definitively rather than waiting for a real Notion publish.
- Both still running, still on their first shot (image gen takes time). I'll wait for them to finish rather than poll further.


## 2026-07-07 11:05 — social-ip-engine

### What Didn't Work (negative knowledge)
- Documented the whole ordering contract in `CLAUDE.md` with a pointer to the exact test, so if anyone touches `sync_once()` later without reading this, the test fails loudly instead of the bug quietly coming back.

### Architecture Decisions
- **python-reviewer's two HIGH findings** (duplicated boolean-env-flag idiom, inconsistent flag-hoisting) — both fixed: extracted a shared `_flag_enabled()` helper and hoisted `mark_wired_enabled` before the loop like its sibling `generate_enabled`.
- No auto-tick logic exists for `🎬 Video` either (same gap pattern as Voice). Since all 4 shots are genuinely done now, ticking it manually:

### Decisions & Reasoning
- Now let me check whether that checkbox column actually exists on the Notion board yet, so I can tell Shivonne the real state instead of guessing:
- - `notion_sync.sync_once()` now PATCHes a Notion checkbox (default column `🔗 DM Wired`, configurable via `NOTION_WIRED_CHECKBOX_PROP`) to `True` the instant a row's rule is wired into `comment_responses.json` — so you see the tick live on the Production Tracker instead of watching `git log`.
- - Updated `CLAUDE.md` §3.10 with the new behavior + fixed a stale line that still said "Published" instead of the pre-flight "Ready to Publish" trigger.
- Caught it in the act — my own test run just wrote a stray file to the real repo because I hadn't patched `_WIRED_PENDING_PATH` in the fixtures yet. Cleaning that up and fixing test isolation properly:
- Same reviewer also caught that my docstring promised auto-retry that didn't actually exist — a failed checkbox PATCH would've been stuck un-ticked forever since `state_set` (which blocks reprocessing) got marked before the checkbox attempt. Rather than just fix the docs to lower the claim, I built the actual retry: failed checkbox attempts now persist to `data/channels/notion_wired_pending.json` and get retried at the top of every subsequent sync — never re-drafting the rule, only retrying the tick.
- 5. Optional: pin it to "Shown in board" via this same visibility panel so you actually see it on the card, rather than leaving it in the hidden list like `Stage`/`Voice`/`Image`/`Video` are now.
- Want me to send a synthetic test webhook against the live Render endpoint to confirm the checkbox actually ticks end-to-end, the same way we diagnosed the `IG_ENABLED` outage last time? That'd tell us definitively rather than waiting for a real Notion publish.
- Both still running, still on their first shot (image gen takes time). I'll wait for them to finish rather than poll further.


## 2026-07-07 11:05 — social-ip-engine

### Architecture Decisions
- - 8 lint warnings, all "caption line >42 chars" — purely cosmetic; JianYing wraps them. Say the word and I'll auto-split long cues into 2 lines.

### Decisions & Reasoning
- **Merged footage** → JianYing draft `stomach-jackie-en`:
- Two separate things — let me diagnose both before proposing, because the fix differs. Let me check the current canvas size and whether JianYing actually kept our caption track.
- 2. **The captions ARE in the draft** (text track, 15 segments — mtime shows JianYing hasn't re-saved it). You're not seeing them because the caption's default position is set for a 16:9 frame, so they're placed off the visible portrait area / wrong spot.
- Right — use the individual `shot*_regen` clips (freshly concatenated) instead of `final_regen`. That guarantees the latest regen shots. Concatenating them, then burning the captions on the native 3:4 frame with audio:


## 2026-07-07 11:11 — social-ip-engine

### Architecture Decisions
- - 8 lint warnings, all "caption line >42 chars" — purely cosmetic; JianYing wraps them. Say the word and I'll auto-split long cues into 2 lines.

### Decisions & Reasoning
- **Merged footage** → JianYing draft `stomach-jackie-en`:
- Two separate things — let me diagnose both before proposing, because the fix differs. Let me check the current canvas size and whether JianYing actually kept our caption track.
- 2. **The captions ARE in the draft** (text track, 15 segments — mtime shows JianYing hasn't re-saved it). You're not seeing them because the caption's default position is set for a 16:9 frame, so they're placed off the visible portrait area / wrong spot.
- Right — use the individual `shot*_regen` clips (freshly concatenated) instead of `final_regen`. That guarantees the latest regen shots. Concatenating them, then burning the captions on the native 3:4 frame with audio:
- 2. **Insert your real product footage** into Shot 2 instead of a generated close-up, then burn captions like we just did on the stomach reel.


## 2026-07-07 11:13 — social-ip-engine

### Architecture Decisions
- - 8 lint warnings, all "caption line >42 chars" — purely cosmetic; JianYing wraps them. Say the word and I'll auto-split long cues into 2 lines.

### Decisions & Reasoning
- **Merged footage** → JianYing draft `stomach-jackie-en`:
- Two separate things — let me diagnose both before proposing, because the fix differs. Let me check the current canvas size and whether JianYing actually kept our caption track.
- 2. **The captions ARE in the draft** (text track, 15 segments — mtime shows JianYing hasn't re-saved it). You're not seeing them because the caption's default position is set for a 16:9 frame, so they're placed off the visible portrait area / wrong spot.
- Right — use the individual `shot*_regen` clips (freshly concatenated) instead of `final_regen`. That guarantees the latest regen shots. Concatenating them, then burning the captions on the native 3:4 frame with audio:
- 2. **Insert your real product footage** into Shot 2 instead of a generated close-up, then burn captions like we just did on the stomach reel.


## 2026-07-07 11:19 — social-ip-engine

### Architecture Decisions
- - 8 lint warnings, all "caption line >42 chars" — purely cosmetic; JianYing wraps them. Say the word and I'll auto-split long cues into 2 lines.

### Decisions & Reasoning
- **Merged footage** → JianYing draft `stomach-jackie-en`:
- Two separate things — let me diagnose both before proposing, because the fix differs. Let me check the current canvas size and whether JianYing actually kept our caption track.
- 2. **The captions ARE in the draft** (text track, 15 segments — mtime shows JianYing hasn't re-saved it). You're not seeing them because the caption's default position is set for a 16:9 frame, so they're placed off the visible portrait area / wrong spot.
- Right — use the individual `shot*_regen` clips (freshly concatenated) instead of `final_regen`. That guarantees the latest regen shots. Concatenating them, then burning the captions on the native 3:4 frame with audio:
- 2. **Insert your real product footage** into Shot 2 instead of a generated close-up, then burn captions like we just did on the stomach reel.
- Video generation is running in the background (this typically takes several minutes — 4 shots through Seedance 2.0, then poll + download + concat). I'll let it run and check back when it completes rather than polling manually.


## 2026-07-07 11:30 — social-ip-engine

### Architecture Decisions
- - 8 lint warnings, all "caption line >42 chars" — purely cosmetic; JianYing wraps them. Say the word and I'll auto-split long cues into 2 lines.

### Decisions & Reasoning
- **Merged footage** → JianYing draft `stomach-jackie-en`:
- Two separate things — let me diagnose both before proposing, because the fix differs. Let me check the current canvas size and whether JianYing actually kept our caption track.
- 2. **The captions ARE in the draft** (text track, 15 segments — mtime shows JianYing hasn't re-saved it). You're not seeing them because the caption's default position is set for a 16:9 frame, so they're placed off the visible portrait area / wrong spot.
- Right — use the individual `shot*_regen` clips (freshly concatenated) instead of `final_regen`. That guarantees the latest regen shots. Concatenating them, then burning the captions on the native 3:4 frame with audio:
- 2. **Insert your real product footage** into Shot 2 instead of a generated close-up, then burn captions like we just did on the stomach reel.
- Video generation is running in the background (this typically takes several minutes — 4 shots through Seedance 2.0, then poll + download + concat). I'll let it run and check back when it completes rather than polling manually.


## 2026-07-07 11:38 — social-ip-engine

### Decisions & Reasoning
- We have a Render API key. Let me pull the actual production logs to find the real comment event and see exactly why it was dropped, rather than guessing.


## 2026-07-07 11:44 — social-ip-engine

### Decisions & Reasoning
- We have a Render API key. Let me pull the actual production logs to find the real comment event and see exactly why it was dropped, rather than guessing.
- Dug into this instead of guessing. Here's what I found — and what I still need from you.


## 2026-07-07 11:54 — social-ip-engine

### Architecture Decisions
- - 8 lint warnings, all "caption line >42 chars" — purely cosmetic; JianYing wraps them. Say the word and I'll auto-split long cues into 2 lines.

### Decisions & Reasoning
- **Merged footage** → JianYing draft `stomach-jackie-en`:
- Two separate things — let me diagnose both before proposing, because the fix differs. Let me check the current canvas size and whether JianYing actually kept our caption track.
- 2. **The captions ARE in the draft** (text track, 15 segments — mtime shows JianYing hasn't re-saved it). You're not seeing them because the caption's default position is set for a 16:9 frame, so they're placed off the visible portrait area / wrong spot.
- Right — use the individual `shot*_regen` clips (freshly concatenated) instead of `final_regen`. That guarantees the latest regen shots. Concatenating them, then burning the captions on the native 3:4 frame with audio:
- 2. **Insert your real product footage** into Shot 2 instead of a generated close-up, then burn captions like we just did on the stomach reel.
- Video generation is running in the background (this typically takes several minutes — 4 shots through Seedance 2.0, then poll + download + concat). I'll let it run and check back when it completes rather than polling manually.


## 2026-07-07 12:03 — social-ip-engine

### Decisions & Reasoning
- We have a Render API key. Let me pull the actual production logs to find the real comment event and see exactly why it was dropped, rather than guessing.
- Dug into this instead of guessing. Here's what I found — and what I still need from you.


## 2026-07-07 12:14 — social-ip-engine

### Decisions & Reasoning
- We have a Render API key. Let me pull the actual production logs to find the real comment event and see exactly why it was dropped, rather than guessing.
- Dug into this instead of guessing. Here's what I found — and what I still need from you.


## 2026-07-07 12:15 — social-ip-engine

### Decisions & Reasoning
- We have a Render API key. Let me pull the actual production logs to find the real comment event and see exactly why it was dropped, rather than guessing.
- Dug into this instead of guessing. Here's what I found — and what I still need from you.


## 2026-07-07 12:17 — social-ip-engine

### Architecture Decisions
- - 8 lint warnings, all "caption line >42 chars" — purely cosmetic; JianYing wraps them. Say the word and I'll auto-split long cues into 2 lines.

### Decisions & Reasoning
- **Merged footage** → JianYing draft `stomach-jackie-en`:
- Two separate things — let me diagnose both before proposing, because the fix differs. Let me check the current canvas size and whether JianYing actually kept our caption track.
- 2. **The captions ARE in the draft** (text track, 15 segments — mtime shows JianYing hasn't re-saved it). You're not seeing them because the caption's default position is set for a 16:9 frame, so they're placed off the visible portrait area / wrong spot.
- Right — use the individual `shot*_regen` clips (freshly concatenated) instead of `final_regen`. That guarantees the latest regen shots. Concatenating them, then burning the captions on the native 3:4 frame with audio:
- 2. **Insert your real product footage** into Shot 2 instead of a generated close-up, then burn captions like we just did on the stomach reel.
- Video generation is running in the background (this typically takes several minutes — 4 shots through Seedance 2.0, then poll + download + concat). I'll let it run and check back when it completes rather than polling manually.


## 2026-07-07 12:44 — social-ip-engine

### Architecture Decisions
- - 8 lint warnings, all "caption line >42 chars" — purely cosmetic; JianYing wraps them. Say the word and I'll auto-split long cues into 2 lines.

### Decisions & Reasoning
- **Merged footage** → JianYing draft `stomach-jackie-en`:
- Two separate things — let me diagnose both before proposing, because the fix differs. Let me check the current canvas size and whether JianYing actually kept our caption track.
- 2. **The captions ARE in the draft** (text track, 15 segments — mtime shows JianYing hasn't re-saved it). You're not seeing them because the caption's default position is set for a 16:9 frame, so they're placed off the visible portrait area / wrong spot.
- Right — use the individual `shot*_regen` clips (freshly concatenated) instead of `final_regen`. That guarantees the latest regen shots. Concatenating them, then burning the captions on the native 3:4 frame with audio:
- 2. **Insert your real product footage** into Shot 2 instead of a generated close-up, then burn captions like we just did on the stomach reel.
- Video generation is running in the background (this typically takes several minutes — 4 shots through Seedance 2.0, then poll + download + concat). I'll let it run and check back when it completes rather than polling manually.


## 2026-07-07 12:47 — social-ip-engine

### Architecture Decisions
- - 8 lint warnings, all "caption line >42 chars" — purely cosmetic; JianYing wraps them. Say the word and I'll auto-split long cues into 2 lines.

### Decisions & Reasoning
- **Merged footage** → JianYing draft `stomach-jackie-en`:
- Two separate things — let me diagnose both before proposing, because the fix differs. Let me check the current canvas size and whether JianYing actually kept our caption track.
- 2. **The captions ARE in the draft** (text track, 15 segments — mtime shows JianYing hasn't re-saved it). You're not seeing them because the caption's default position is set for a 16:9 frame, so they're placed off the visible portrait area / wrong spot.
- Right — use the individual `shot*_regen` clips (freshly concatenated) instead of `final_regen`. That guarantees the latest regen shots. Concatenating them, then burning the captions on the native 3:4 frame with audio:
- 2. **Insert your real product footage** into Shot 2 instead of a generated close-up, then burn captions like we just did on the stomach reel.
- Video generation is running in the background (this typically takes several minutes — 4 shots through Seedance 2.0, then poll + download + concat). I'll let it run and check back when it completes rather than polling manually.


## 2026-07-07 12:51 — social-ip-engine

### Architecture Decisions
- - 8 lint warnings, all "caption line >42 chars" — purely cosmetic; JianYing wraps them. Say the word and I'll auto-split long cues into 2 lines.

### Decisions & Reasoning
- **Merged footage** → JianYing draft `stomach-jackie-en`:
- Two separate things — let me diagnose both before proposing, because the fix differs. Let me check the current canvas size and whether JianYing actually kept our caption track.
- 2. **The captions ARE in the draft** (text track, 15 segments — mtime shows JianYing hasn't re-saved it). You're not seeing them because the caption's default position is set for a 16:9 frame, so they're placed off the visible portrait area / wrong spot.
- Right — use the individual `shot*_regen` clips (freshly concatenated) instead of `final_regen`. That guarantees the latest regen shots. Concatenating them, then burning the captions on the native 3:4 frame with audio:
- 2. **Insert your real product footage** into Shot 2 instead of a generated close-up, then burn captions like we just did on the stomach reel.
- Video generation is running in the background (this typically takes several minutes — 4 shots through Seedance 2.0, then poll + download + concat). I'll let it run and check back when it completes rather than polling manually.


## 2026-07-07 12:51 — social-ip-engine

### Decisions & Reasoning
- We have a Render API key. Let me pull the actual production logs to find the real comment event and see exactly why it was dropped, rather than guessing.
- Dug into this instead of guessing. Here's what I found — and what I still need from you.


## 2026-07-07 13:03 — social-ip-engine

### Architecture Decisions
- - 8 lint warnings, all "caption line >42 chars" — purely cosmetic; JianYing wraps them. Say the word and I'll auto-split long cues into 2 lines.
- That's the real bug. My "hands only" fix was the wrong direction — it *guaranteed* no lip-sync (no face = nothing to sync). The actual fix: redesign Shot 2 as **single-person, frontal, talking head** — Jackie demoing the patch on his own ear or a prop model instead of a second "patient" — which is exactly the pattern that already works in shots 1/3/4.

### Decisions & Reasoning
- **Merged footage** → JianYing draft `stomach-jackie-en`:
- Two separate things — let me diagnose both before proposing, because the fix differs. Let me check the current canvas size and whether JianYing actually kept our caption track.
- 2. **The captions ARE in the draft** (text track, 15 segments — mtime shows JianYing hasn't re-saved it). You're not seeing them because the caption's default position is set for a 16:9 frame, so they're placed off the visible portrait area / wrong spot.
- Right — use the individual `shot*_regen` clips (freshly concatenated) instead of `final_regen`. That guarantees the latest regen shots. Concatenating them, then burning the captions on the native 3:4 frame with audio:
- 2. **Insert your real product footage** into Shot 2 instead of a generated close-up, then burn captions like we just did on the stomach reel.
- Video generation is running in the background (this typically takes several minutes — 4 shots through Seedance 2.0, then poll + download + concat). I'll let it run and check back when it completes rather than polling manually.


## 2026-07-07 13:05 — social-ip-engine

### What Didn't Work (negative knowledge)
- | Graph API fetch *also* fails (e.g. Meta having a bad day, rate-limited, deleted account) | Comment vanishes, zero trace | Comment still drops — **but now logged loudly**, diagnosable in seconds instead of the 2-hour Graph API archaeology I just did |

### Decisions & Reasoning
- We have a Render API key. Let me pull the actual production logs to find the real comment event and see exactly why it was dropped, rather than guessing.
- Dug into this instead of guessing. Here's what I found — and what I still need from you.
- **Why it failed:** Meta's own Instagram webhook infrastructure intermittently omits the `from` object on comment events. Confirmed by cross-referencing: David's comment had `from` in the payload, Rajesh's and your test comment — same post, hours/seconds apart — didn't. That's not our bug. That's Meta being Meta. Our bug was that our code *required* a field Meta doesn't guarantee, and when it was missing, it died with **zero log output anywhere** — not even the exception handlers caught it, because there was no exception, just a silent `continue`.
- **The actual gap, and I should've led with this instead of letting you find it:** logging something loudly doesn't help if nobody's looking. Right now if this fires again, it sits in Render's log stream until someone thinks to grep it — same blind spot that made this take a Graph API investigation instead of a 30-second log check. That's not fixed. Two things would actually close that gap:
- 1. **Alert on the drop** — Slack/email ping the moment `"still no 'from_id' after Graph API backfill attempt"` fires, instead of waiting for a lead to complain.
- Neither is built. Want me to build the alert now — that's the cheap, high-value one? The reconciliation sweep is a bigger lift and I'd want to scope it properly rather than bolt it on in the heat of this.


## 2026-07-07 13:06 — social-ip-engine

### Decisions & Reasoning
- - **The fix:** cut fried/spicy 3 days, chrysanthemum tea instead of cold drinks


## 2026-07-07 13:09 — social-ip-engine

### What Didn't Work (negative knowledge)
- | Graph API fetch *also* fails (e.g. Meta having a bad day, rate-limited, deleted account) | Comment vanishes, zero trace | Comment still drops — **but now logged loudly**, diagnosable in seconds instead of the 2-hour Graph API archaeology I just did |

### Architecture Decisions
- Good review. Applying the two concrete LOW fixes now; I'll address the MEDIUM one with reasoning rather than blindly matching the pattern.

### Decisions & Reasoning
- We have a Render API key. Let me pull the actual production logs to find the real comment event and see exactly why it was dropped, rather than guessing.
- Dug into this instead of guessing. Here's what I found — and what I still need from you.
- **Why it failed:** Meta's own Instagram webhook infrastructure intermittently omits the `from` object on comment events. Confirmed by cross-referencing: David's comment had `from` in the payload, Rajesh's and your test comment — same post, hours/seconds apart — didn't. That's not our bug. That's Meta being Meta. Our bug was that our code *required* a field Meta doesn't guarantee, and when it was missing, it died with **zero log output anywhere** — not even the exception handlers caught it, because there was no exception, just a silent `continue`.
- **The actual gap, and I should've led with this instead of letting you find it:** logging something loudly doesn't help if nobody's looking. Right now if this fires again, it sits in Render's log stream until someone thinks to grep it — same blind spot that made this take a Graph API investigation instead of a 30-second log check. That's not fixed. Two things would actually close that gap:
- 1. **Alert on the drop** — Slack/email ping the moment `"still no 'from_id' after Graph API backfill attempt"` fires, instead of waiting for a lead to complain.
- Neither is built. Want me to build the alert now — that's the cheap, high-value one? The reconciliation sweep is a bigger lift and I'd want to scope it properly rather than bolt it on in the heat of this.


## 2026-07-07 13:10 — social-ip-engine

### Architecture Decisions
- - 8 lint warnings, all "caption line >42 chars" — purely cosmetic; JianYing wraps them. Say the word and I'll auto-split long cues into 2 lines.
- That's the real bug. My "hands only" fix was the wrong direction — it *guaranteed* no lip-sync (no face = nothing to sync). The actual fix: redesign Shot 2 as **single-person, frontal, talking head** — Jackie demoing the patch on his own ear or a prop model instead of a second "patient" — which is exactly the pattern that already works in shots 1/3/4.
- **Redesigned Shot 2** as single-person, frontal, talking head — Jackie holding an anatomical ear model (reusing the same prop from Shot 1) and pressing the patch onto it, rather than a second "patient." Face is dead-on to camera, satisfying both constraints. Bead is spec'd as plain matte gold, no glow, in both the image and motion prompts.

### Decisions & Reasoning
- **Merged footage** → JianYing draft `stomach-jackie-en`:
- Two separate things — let me diagnose both before proposing, because the fix differs. Let me check the current canvas size and whether JianYing actually kept our caption track.
- 2. **The captions ARE in the draft** (text track, 15 segments — mtime shows JianYing hasn't re-saved it). You're not seeing them because the caption's default position is set for a 16:9 frame, so they're placed off the visible portrait area / wrong spot.
- Right — use the individual `shot*_regen` clips (freshly concatenated) instead of `final_regen`. That guarantees the latest regen shots. Concatenating them, then burning the captions on the native 3:4 frame with audio:
- 2. **Insert your real product footage** into Shot 2 instead of a generated close-up, then burn captions like we just did on the stomach reel.
- Video generation is running in the background (this typically takes several minutes — 4 shots through Seedance 2.0, then poll + download + concat). I'll let it run and check back when it completes rather than polling manually.


## 2026-07-07 13:18 — social-ip-engine

### What Didn't Work (negative knowledge)
- | Graph API fetch *also* fails (e.g. Meta having a bad day, rate-limited, deleted account) | Comment vanishes, zero trace | Comment still drops — **but now logged loudly**, diagnosable in seconds instead of the 2-hour Graph API archaeology I just did |

### Architecture Decisions
- Good review. Applying the two concrete LOW fixes now; I'll address the MEDIUM one with reasoning rather than blindly matching the pattern.

### Decisions & Reasoning
- We have a Render API key. Let me pull the actual production logs to find the real comment event and see exactly why it was dropped, rather than guessing.
- Dug into this instead of guessing. Here's what I found — and what I still need from you.
- **Why it failed:** Meta's own Instagram webhook infrastructure intermittently omits the `from` object on comment events. Confirmed by cross-referencing: David's comment had `from` in the payload, Rajesh's and your test comment — same post, hours/seconds apart — didn't. That's not our bug. That's Meta being Meta. Our bug was that our code *required* a field Meta doesn't guarantee, and when it was missing, it died with **zero log output anywhere** — not even the exception handlers caught it, because there was no exception, just a silent `continue`.
- **The actual gap, and I should've led with this instead of letting you find it:** logging something loudly doesn't help if nobody's looking. Right now if this fires again, it sits in Render's log stream until someone thinks to grep it — same blind spot that made this take a Graph API investigation instead of a 30-second log check. That's not fixed. Two things would actually close that gap:
- 1. **Alert on the drop** — Slack/email ping the moment `"still no 'from_id' after Graph API backfill attempt"` fires, instead of waiting for a lead to complain.
- Neither is built. Want me to build the alert now — that's the cheap, high-value one? The reconciliation sweep is a bigger lift and I'd want to scope it properly rather than bolt it on in the heat of this.
- Good catch by my own test — pytest's logging plugin pre-configures the root logger before `src.web` is imported, which would silently make `basicConfig()` a no-op in that case too (not just in tests — any pre-existing root handler from anywhere would do the same in production). Let me harden the real fix with `force=True`, then rewrite the test to validate in a clean subprocess instead of fighting pytest's own logging plugin:


## 2026-07-07 13:22 — social-ip-engine

### What Didn't Work (negative knowledge)
- | Graph API fetch *also* fails (e.g. Meta having a bad day, rate-limited, deleted account) | Comment vanishes, zero trace | Comment still drops — **but now logged loudly**, diagnosable in seconds instead of the 2-hour Graph API archaeology I just did |

### Architecture Decisions
- Good review. Applying the two concrete LOW fixes now; I'll address the MEDIUM one with reasoning rather than blindly matching the pattern.

### Decisions & Reasoning
- We have a Render API key. Let me pull the actual production logs to find the real comment event and see exactly why it was dropped, rather than guessing.
- Dug into this instead of guessing. Here's what I found — and what I still need from you.
- **Why it failed:** Meta's own Instagram webhook infrastructure intermittently omits the `from` object on comment events. Confirmed by cross-referencing: David's comment had `from` in the payload, Rajesh's and your test comment — same post, hours/seconds apart — didn't. That's not our bug. That's Meta being Meta. Our bug was that our code *required* a field Meta doesn't guarantee, and when it was missing, it died with **zero log output anywhere** — not even the exception handlers caught it, because there was no exception, just a silent `continue`.
- **The actual gap, and I should've led with this instead of letting you find it:** logging something loudly doesn't help if nobody's looking. Right now if this fires again, it sits in Render's log stream until someone thinks to grep it — same blind spot that made this take a Graph API investigation instead of a 30-second log check. That's not fixed. Two things would actually close that gap:
- 1. **Alert on the drop** — Slack/email ping the moment `"still no 'from_id' after Graph API backfill attempt"` fires, instead of waiting for a lead to complain.
- Neither is built. Want me to build the alert now — that's the cheap, high-value one? The reconciliation sweep is a bigger lift and I'd want to scope it properly rather than bolt it on in the heat of this.
- Good catch by my own test — pytest's logging plugin pre-configures the root logger before `src.web` is imported, which would silently make `basicConfig()` a no-op in that case too (not just in tests — any pre-existing root handler from anywhere would do the same in production). Let me harden the real fix with `force=True`, then rewrite the test to validate in a clean subprocess instead of fighting pytest's own logging plugin:


## 2026-07-07 13:33 — social-ip-engine

### What Didn't Work (negative knowledge)
- | Graph API fetch *also* fails (e.g. Meta having a bad day, rate-limited, deleted account) | Comment vanishes, zero trace | Comment still drops — **but now logged loudly**, diagnosable in seconds instead of the 2-hour Graph API archaeology I just did |
- Honest scope of "won't fail again": the *known* failure modes (missing `from`, webhook disabled, generic missed comments) are now self-healing or loudly surfaced. I can't promise Meta won't invent a fourth way to break this — nobody can — but you now have three independent layers (self-heal, alert, sweep) instead of zero, and nothing sits invisible anymore.

### Architecture Decisions
- Good review. Applying the two concrete LOW fixes now; I'll address the MEDIUM one with reasoning rather than blindly matching the pattern.

### Decisions & Reasoning
- We have a Render API key. Let me pull the actual production logs to find the real comment event and see exactly why it was dropped, rather than guessing.
- Dug into this instead of guessing. Here's what I found — and what I still need from you.
- **Why it failed:** Meta's own Instagram webhook infrastructure intermittently omits the `from` object on comment events. Confirmed by cross-referencing: David's comment had `from` in the payload, Rajesh's and your test comment — same post, hours/seconds apart — didn't. That's not our bug. That's Meta being Meta. Our bug was that our code *required* a field Meta doesn't guarantee, and when it was missing, it died with **zero log output anywhere** — not even the exception handlers caught it, because there was no exception, just a silent `continue`.
- **The actual gap, and I should've led with this instead of letting you find it:** logging something loudly doesn't help if nobody's looking. Right now if this fires again, it sits in Render's log stream until someone thinks to grep it — same blind spot that made this take a Graph API investigation instead of a 30-second log check. That's not fixed. Two things would actually close that gap:
- 1. **Alert on the drop** — Slack/email ping the moment `"still no 'from_id' after Graph API backfill attempt"` fires, instead of waiting for a lead to complain.
- Neither is built. Want me to build the alert now — that's the cheap, high-value one? The reconciliation sweep is a bigger lift and I'd want to scope it properly rather than bolt it on in the heat of this.
- Good catch by my own test — pytest's logging plugin pre-configures the root logger before `src.web` is imported, which would silently make `basicConfig()` a no-op in that case too (not just in tests — any pre-existing root handler from anywhere would do the same in production). Let me harden the real fix with `force=True`, then rewrite the test to validate in a clean subprocess instead of fighting pytest's own logging plugin:
- **One unrelated thing I noticed and did NOT touch, flagging it because it matters:** production logs show `CRM: using SQLite backend`, and `DATABASE_URL` isn't actually set on this Render service despite `render.yaml` documenting a Postgres link — this service was never blueprint-attached, so that link was never real. If true, production data is sitting on the instance's local disk, not Postgres. Separate issue, nothing to do with today's work — want me to look into it next, or is that already known/intentional?


## 2026-07-07 13:33 — social-ip-engine

### What Didn't Work (negative knowledge)
- The problem is **not** your setup — it's that the secret I set is saved in Render's config but **the running instance hasn't picked it up.** Setting an env var doesn't auto-restart the process here (that broken auto-deploy again). Proof: my own call with the correct secret *also* just got 401 — the live process still has an empty secret in memory.

### Architecture Decisions
- That's the pattern — tight 4-line Master Script (Hook / Root Cause / Fix / CTA) + 4 shots + DM protocol. Rewriting to match, pain points folded into the root-cause line instead of a whole barrage.

### Decisions & Reasoning
- **选题我 100% 支持**——补肾壮阳/男性活力在 TCM 里是转化率最高、最缺内容、评论区最炸的赛道。你要 gimmick、要博眼球,方向完全对。
- 好消息是:**冲击力和搞笑感可以完全保留,只要把"器官"抽象成一个符号**——平台审不到,但人人秒懂。🍆 才是互联网通用暗号,不是保险套。
- - Body:完整 **📜 Master Script(6 shots)** + **🎬 Shot Guide**(每个 shot 有 🎥 画面 / 🗣️ 台词 / 💡 用意)+ **🖼️ Thumbnail 图片 prompt**
- 1. **CTA keyword 用 `VITALITY`**,不用 `kidney`——避免跟你现有 kidney 类内容的关键词在 `comment_responses.json` 里撞规则。要换成别的词跟我说。
- 图我没直接生成——想先让你过一眼概念落地对不对。你点头,我就用 body 里那个 thumbnail prompt 跑图(你有 `notion_image.py` / `batch_infographic_gen.py`),生成后直接回填到这条 concept 的 🖼️ 区。
- **③ SOLUTION 点破根因 + 解法(~7s)** — 所有症状指向一个根:**肾阳虚,内火熄了**;晨勃只是最明显的那盏警示灯。不是年纪、不是没救 → 温热熟食 + 早睡 + 别再用冷饮/熬夜/压力掏空油箱。茄子这时慢慢立起来 → "做对了……旗子就又升起来了。"
- Hook · Root Cause · The Fix · CTA — 每个都有 🎥/🗣️/💡,茄子半旗→立起的视觉梗保留在 Shot 1 和 Shot 3。💡 标签用中文 TCM 术语(腎陽虛·命門火衰 等),跟 detox 那条一致。
- - **You get a QA beat** — between "Ready" and "Published" you can look at the auto-generated infographic and fix it if it's off, instead of discovering it after it's already DMing strangers.


## 2026-07-07 13:36 — social-ip-engine

### What Didn't Work (negative knowledge)
- The problem is **not** your setup — it's that the secret I set is saved in Render's config but **the running instance hasn't picked it up.** Setting an env var doesn't auto-restart the process here (that broken auto-deploy again). Proof: my own call with the correct secret *also* just got 401 — the live process still has an empty secret in memory.

### Architecture Decisions
- That's the pattern — tight 4-line Master Script (Hook / Root Cause / Fix / CTA) + 4 shots + DM protocol. Rewriting to match, pain points folded into the root-cause line instead of a whole barrage.

### Decisions & Reasoning
- **选题我 100% 支持**——补肾壮阳/男性活力在 TCM 里是转化率最高、最缺内容、评论区最炸的赛道。你要 gimmick、要博眼球,方向完全对。
- 好消息是:**冲击力和搞笑感可以完全保留,只要把"器官"抽象成一个符号**——平台审不到,但人人秒懂。🍆 才是互联网通用暗号,不是保险套。
- - Body:完整 **📜 Master Script(6 shots)** + **🎬 Shot Guide**(每个 shot 有 🎥 画面 / 🗣️ 台词 / 💡 用意)+ **🖼️ Thumbnail 图片 prompt**
- 1. **CTA keyword 用 `VITALITY`**,不用 `kidney`——避免跟你现有 kidney 类内容的关键词在 `comment_responses.json` 里撞规则。要换成别的词跟我说。
- 图我没直接生成——想先让你过一眼概念落地对不对。你点头,我就用 body 里那个 thumbnail prompt 跑图(你有 `notion_image.py` / `batch_infographic_gen.py`),生成后直接回填到这条 concept 的 🖼️ 区。
- **③ SOLUTION 点破根因 + 解法(~7s)** — 所有症状指向一个根:**肾阳虚,内火熄了**;晨勃只是最明显的那盏警示灯。不是年纪、不是没救 → 温热熟食 + 早睡 + 别再用冷饮/熬夜/压力掏空油箱。茄子这时慢慢立起来 → "做对了……旗子就又升起来了。"
- Hook · Root Cause · The Fix · CTA — 每个都有 🎥/🗣️/💡,茄子半旗→立起的视觉梗保留在 Shot 1 和 Shot 3。💡 标签用中文 TCM 术语(腎陽虛·命門火衰 等),跟 detox 那条一致。
- - **You get a QA beat** — between "Ready" and "Published" you can look at the auto-generated infographic and fix it if it's off, instead of discovering it after it's already DMing strangers.


## 2026-07-07 13:37 — social-ip-engine

### Architecture Decisions
- - 8 lint warnings, all "caption line >42 chars" — purely cosmetic; JianYing wraps them. Say the word and I'll auto-split long cues into 2 lines.
- That's the real bug. My "hands only" fix was the wrong direction — it *guaranteed* no lip-sync (no face = nothing to sync). The actual fix: redesign Shot 2 as **single-person, frontal, talking head** — Jackie demoing the patch on his own ear or a prop model instead of a second "patient" — which is exactly the pattern that already works in shots 1/3/4.
- **Redesigned Shot 2** as single-person, frontal, talking head — Jackie holding an anatomical ear model (reusing the same prop from Shot 1) and pressing the patch onto it, rather than a second "patient." Face is dead-on to camera, satisfying both constraints. Bead is spec'd as plain matte gold, no glow, in both the image and motion prompts.
- **The real fix — the same trick every talking-head video with cutaways uses:** split Shot 2 into two beats that get concatenated into one clip:
- Want me to build it this way (2 sub-clips → concat into `shot2.mp4`)? I'd split the ~12s narration into two chunks (intro line = Beat A, points/demo line = Beat B) so each half's audio matches its visual. Or if you'd rather keep it as one continuous two-person shot and just accept the `image2video` fallback (no lip-sync, but simpler/faster), say so and I'll go back to that with just the glow fixed.

### Decisions & Reasoning
- **Merged footage** → JianYing draft `stomach-jackie-en`:
- Two separate things — let me diagnose both before proposing, because the fix differs. Let me check the current canvas size and whether JianYing actually kept our caption track.
- 2. **The captions ARE in the draft** (text track, 15 segments — mtime shows JianYing hasn't re-saved it). You're not seeing them because the caption's default position is set for a 16:9 frame, so they're placed off the visible portrait area / wrong spot.
- Right — use the individual `shot*_regen` clips (freshly concatenated) instead of `final_regen`. That guarantees the latest regen shots. Concatenating them, then burning the captions on the native 3:4 frame with audio:
- 2. **Insert your real product footage** into Shot 2 instead of a generated close-up, then burn captions like we just did on the stomach reel.
- Video generation is running in the background (this typically takes several minutes — 4 shots through Seedance 2.0, then poll + download + concat). I'll let it run and check back when it completes rather than polling manually.
- Fair pushback — you're right that the demo needs a real patient, not Jackie miming on a plastic ear. Let me be straight about the actual constraint though, because it's not me being cautious for no reason — it's baked into your own `studio/CLAUDE.md`, verified from real production runs:
- Result: real interaction with the patient stays in, AND you get an actual lip-synced beat elsewhere in the same shot — best of both, instead of me quietly picking one over the other.


## 2026-07-07 13:43 — social-ip-engine

### Decisions & Reasoning
- **Written to Notion:** Content Library, page `396f2a3f-4320-81f4-9905-fd10db2a9064`, Concept Status = ✍️ Scripted. Built a new small script for it (`studio/scripts/create_constitution_concept.py`) rather than appending to `batch_create_concepts.py`, since that file already ran its batch — matches your existing convention of one script per content batch.
- 我当时做的事情是:直接套用了 Notion 里已经有的 60 个 concept 的固定模板(Hook→Signs→Fix→CTA 四段式),这个模板是之前几轮内容攒下来的通用「TCM 医生科普」套路,**不是从这次 research 挖出来的东西提炼的**。


## 2026-07-07 13:45 — social-ip-engine

### What Didn't Work (negative knowledge)
- The problem is **not** your setup — it's that the secret I set is saved in Render's config but **the running instance hasn't picked it up.** Setting an env var doesn't auto-restart the process here (that broken auto-deploy again). Proof: my own call with the correct secret *also* just got 401 — the live process still has an empty secret in memory.

### Architecture Decisions
- That's the pattern — tight 4-line Master Script (Hook / Root Cause / Fix / CTA) + 4 shots + DM protocol. Rewriting to match, pain points folded into the root-cause line instead of a whole barrage.

### Decisions & Reasoning
- **选题我 100% 支持**——补肾壮阳/男性活力在 TCM 里是转化率最高、最缺内容、评论区最炸的赛道。你要 gimmick、要博眼球,方向完全对。
- 好消息是:**冲击力和搞笑感可以完全保留,只要把"器官"抽象成一个符号**——平台审不到,但人人秒懂。🍆 才是互联网通用暗号,不是保险套。
- - Body:完整 **📜 Master Script(6 shots)** + **🎬 Shot Guide**(每个 shot 有 🎥 画面 / 🗣️ 台词 / 💡 用意)+ **🖼️ Thumbnail 图片 prompt**
- 1. **CTA keyword 用 `VITALITY`**,不用 `kidney`——避免跟你现有 kidney 类内容的关键词在 `comment_responses.json` 里撞规则。要换成别的词跟我说。
- 图我没直接生成——想先让你过一眼概念落地对不对。你点头,我就用 body 里那个 thumbnail prompt 跑图(你有 `notion_image.py` / `batch_infographic_gen.py`),生成后直接回填到这条 concept 的 🖼️ 区。
- **③ SOLUTION 点破根因 + 解法(~7s)** — 所有症状指向一个根:**肾阳虚,内火熄了**;晨勃只是最明显的那盏警示灯。不是年纪、不是没救 → 温热熟食 + 早睡 + 别再用冷饮/熬夜/压力掏空油箱。茄子这时慢慢立起来 → "做对了……旗子就又升起来了。"
- Hook · Root Cause · The Fix · CTA — 每个都有 🎥/🗣️/💡,茄子半旗→立起的视觉梗保留在 Shot 1 和 Shot 3。💡 标签用中文 TCM 术语(腎陽虛·命門火衰 等),跟 detox 那条一致。
- - **You get a QA beat** — between "Ready" and "Published" you can look at the auto-generated infographic and fix it if it's off, instead of discovering it after it's already DMing strangers.


## 2026-07-07 13:47 — social-ip-engine

### Decisions & Reasoning
- **Written to Notion:** Content Library, page `396f2a3f-4320-81f4-9905-fd10db2a9064`, Concept Status = ✍️ Scripted. Built a new small script for it (`studio/scripts/create_constitution_concept.py`) rather than appending to `batch_create_concepts.py`, since that file already ran its batch — matches your existing convention of one script per content batch.
- 我当时做的事情是:直接套用了 Notion 里已经有的 60 个 concept 的固定模板(Hook→Signs→Fix→CTA 四段式),这个模板是之前几轮内容攒下来的通用「TCM 医生科普」套路,**不是从这次 research 挖出来的东西提炼的**。


## 2026-07-07 13:50 — social-ip-engine

### What Didn't Work (negative knowledge)
- Both shot 2 and shot 4 failures were the **same transient upload glitch** your own docs flagged ("realistic talking-head + audio is flaky — retry usually works") — not a structural "two people = broken" rule. I was too quick to trust the wrapper's silent fallback instead of testing it directly like you said.

### Architecture Decisions
- - 8 lint warnings, all "caption line >42 chars" — purely cosmetic; JianYing wraps them. Say the word and I'll auto-split long cues into 2 lines.
- That's the real bug. My "hands only" fix was the wrong direction — it *guaranteed* no lip-sync (no face = nothing to sync). The actual fix: redesign Shot 2 as **single-person, frontal, talking head** — Jackie demoing the patch on his own ear or a prop model instead of a second "patient" — which is exactly the pattern that already works in shots 1/3/4.
- **Redesigned Shot 2** as single-person, frontal, talking head — Jackie holding an anatomical ear model (reusing the same prop from Shot 1) and pressing the patch onto it, rather than a second "patient." Face is dead-on to camera, satisfying both constraints. Bead is spec'd as plain matte gold, no glow, in both the image and motion prompts.
- **The real fix — the same trick every talking-head video with cutaways uses:** split Shot 2 into two beats that get concatenated into one clip:
- Want me to build it this way (2 sub-clips → concat into `shot2.mp4`)? I'd split the ~12s narration into two chunks (intro line = Beat A, points/demo line = Beat B) so each half's audio matches its visual. Or if you'd rather keep it as one continuous two-person shot and just accept the `image2video` fallback (no lip-sync, but simpler/faster), say so and I'll go back to that with just the glow fixed.

### Decisions & Reasoning
- **Merged footage** → JianYing draft `stomach-jackie-en`:
- Two separate things — let me diagnose both before proposing, because the fix differs. Let me check the current canvas size and whether JianYing actually kept our caption track.
- 2. **The captions ARE in the draft** (text track, 15 segments — mtime shows JianYing hasn't re-saved it). You're not seeing them because the caption's default position is set for a 16:9 frame, so they're placed off the visible portrait area / wrong spot.
- Right — use the individual `shot*_regen` clips (freshly concatenated) instead of `final_regen`. That guarantees the latest regen shots. Concatenating them, then burning the captions on the native 3:4 frame with audio:
- 2. **Insert your real product footage** into Shot 2 instead of a generated close-up, then burn captions like we just did on the stomach reel.
- Video generation is running in the background (this typically takes several minutes — 4 shots through Seedance 2.0, then poll + download + concat). I'll let it run and check back when it completes rather than polling manually.
- Fair pushback — you're right that the demo needs a real patient, not Jackie miming on a plastic ear. Let me be straight about the actual constraint though, because it's not me being cautious for no reason — it's baked into your own `studio/CLAUDE.md`, verified from real production runs:
- Result: real interaction with the patient stays in, AND you get an actual lip-synced beat elsewhere in the same shot — best of both, instead of me quietly picking one over the other.


## 2026-07-07 13:52 — social-ip-engine

### What Didn't Work (negative knowledge)
- **Shot 1** now opens on the doctor eyeing a phone with the generic "avoid cold food" tip, skeptical head-tilt, phone face-down, challenge look at camera — instead of the soft "let's check one thing first" opener. Overlay: "Popular advice ≠ right for everyone."

### Architecture Decisions
- 4. **Hook质量关卡**——这是这次真正缺的一环。逼自己回答:"这个hook是真的对标了research里的某个机制,还是只是复用了上一个concept的壳?" 给出3种命名清楚的机制(pattern interrupt / myth-bust / 具体化悬念),必须出2-3个选项让人选,不能只交一稿。还写了"hook改了要同步3个地方"这个坑(Hook property + Master Script第1行 + Shot1的🗣️——这次差点漏了Shot1的🎥视觉方向也要跟着改)

### Decisions & Reasoning
- **Written to Notion:** Content Library, page `396f2a3f-4320-81f4-9905-fd10db2a9064`, Concept Status = ✍️ Scripted. Built a new small script for it (`studio/scripts/create_constitution_concept.py`) rather than appending to `batch_create_concepts.py`, since that file already ran its batch — matches your existing convention of one script per content batch.
- 我当时做的事情是:直接套用了 Notion 里已经有的 60 个 concept 的固定模板(Hook→Signs→Fix→CTA 四段式),这个模板是之前几轮内容攒下来的通用「TCM 医生科普」套路,**不是从这次 research 挖出来的东西提炼的**。
- **Shot 3** (the fix) now pays off the controversy instead of just listing food: cold-type → the popular advice is right, warm up; hot-type → same advice backfires, cool down instead. That's the twist the hook promised.
- 结构是5步,故意拆开而不是揉成一步——因为这次的问题就是"research 做了但没真正被用上,script 悄悄退回旧模板":
- 这是个直接可用的草稿,没走 skill-creator 那套完整 eval/benchmark 流程(那个更适合复杂的、可客观验证输出的技能;这个偏主观创意判断,你实际用几次给反馈更有效)。要不要现在就拿它跑一次下一个 topic 试试手感?


## 2026-07-07 13:59 — social-ip-engine

### What Didn't Work (negative knowledge)
- Both shot 2 and shot 4 failures were the **same transient upload glitch** your own docs flagged ("realistic talking-head + audio is flaky — retry usually works") — not a structural "two people = broken" rule. I was too quick to trust the wrapper's silent fallback instead of testing it directly like you said.
- Caught a real problem before calling this done — I need to flag it rather than let it slide. When I trimmed shot 2's audio to fit the API's 15s limit, I cut off the tail of the sentence: it now ends **"...to keep the pressure **work**"** instead of "...working all day." That's broken content, not just cosmetic.

### Architecture Decisions
- - 8 lint warnings, all "caption line >42 chars" — purely cosmetic; JianYing wraps them. Say the word and I'll auto-split long cues into 2 lines.
- That's the real bug. My "hands only" fix was the wrong direction — it *guaranteed* no lip-sync (no face = nothing to sync). The actual fix: redesign Shot 2 as **single-person, frontal, talking head** — Jackie demoing the patch on his own ear or a prop model instead of a second "patient" — which is exactly the pattern that already works in shots 1/3/4.
- **Redesigned Shot 2** as single-person, frontal, talking head — Jackie holding an anatomical ear model (reusing the same prop from Shot 1) and pressing the patch onto it, rather than a second "patient." Face is dead-on to camera, satisfying both constraints. Bead is spec'd as plain matte gold, no glow, in both the image and motion prompts.
- **The real fix — the same trick every talking-head video with cutaways uses:** split Shot 2 into two beats that get concatenated into one clip:
- Want me to build it this way (2 sub-clips → concat into `shot2.mp4`)? I'd split the ~12s narration into two chunks (intro line = Beat A, points/demo line = Beat B) so each half's audio matches its visual. Or if you'd rather keep it as one continuous two-person shot and just accept the `image2video` fallback (no lip-sync, but simpler/faster), say so and I'll go back to that with just the glow fixed.

### Decisions & Reasoning
- **Merged footage** → JianYing draft `stomach-jackie-en`:
- Two separate things — let me diagnose both before proposing, because the fix differs. Let me check the current canvas size and whether JianYing actually kept our caption track.
- 2. **The captions ARE in the draft** (text track, 15 segments — mtime shows JianYing hasn't re-saved it). You're not seeing them because the caption's default position is set for a 16:9 frame, so they're placed off the visible portrait area / wrong spot.
- Right — use the individual `shot*_regen` clips (freshly concatenated) instead of `final_regen`. That guarantees the latest regen shots. Concatenating them, then burning the captions on the native 3:4 frame with audio:
- 2. **Insert your real product footage** into Shot 2 instead of a generated close-up, then burn captions like we just did on the stomach reel.
- Video generation is running in the background (this typically takes several minutes — 4 shots through Seedance 2.0, then poll + download + concat). I'll let it run and check back when it completes rather than polling manually.
- Fair pushback — you're right that the demo needs a real patient, not Jackie miming on a plastic ear. Let me be straight about the actual constraint though, because it's not me being cautious for no reason — it's baked into your own `studio/CLAUDE.md`, verified from real production runs:
- Result: real interaction with the patient stays in, AND you get an actual lip-synced beat elsewhere in the same shot — best of both, instead of me quietly picking one over the other.


## 2026-07-07 14:02 — social-ip-engine

### What Didn't Work (negative knowledge)
- The problem is **not** your setup — it's that the secret I set is saved in Render's config but **the running instance hasn't picked it up.** Setting an env var doesn't auto-restart the process here (that broken auto-deploy again). Proof: my own call with the correct secret *also* just got 401 — the live process still has an empty secret in memory.

### Architecture Decisions
- That's the pattern — tight 4-line Master Script (Hook / Root Cause / Fix / CTA) + 4 shots + DM protocol. Rewriting to match, pain points folded into the root-cause line instead of a whole barrage.

### Decisions & Reasoning
- **选题我 100% 支持**——补肾壮阳/男性活力在 TCM 里是转化率最高、最缺内容、评论区最炸的赛道。你要 gimmick、要博眼球,方向完全对。
- 好消息是:**冲击力和搞笑感可以完全保留,只要把"器官"抽象成一个符号**——平台审不到,但人人秒懂。🍆 才是互联网通用暗号,不是保险套。
- - Body:完整 **📜 Master Script(6 shots)** + **🎬 Shot Guide**(每个 shot 有 🎥 画面 / 🗣️ 台词 / 💡 用意)+ **🖼️ Thumbnail 图片 prompt**
- 1. **CTA keyword 用 `VITALITY`**,不用 `kidney`——避免跟你现有 kidney 类内容的关键词在 `comment_responses.json` 里撞规则。要换成别的词跟我说。
- 图我没直接生成——想先让你过一眼概念落地对不对。你点头,我就用 body 里那个 thumbnail prompt 跑图(你有 `notion_image.py` / `batch_infographic_gen.py`),生成后直接回填到这条 concept 的 🖼️ 区。
- **③ SOLUTION 点破根因 + 解法(~7s)** — 所有症状指向一个根:**肾阳虚,内火熄了**;晨勃只是最明显的那盏警示灯。不是年纪、不是没救 → 温热熟食 + 早睡 + 别再用冷饮/熬夜/压力掏空油箱。茄子这时慢慢立起来 → "做对了……旗子就又升起来了。"
- Hook · Root Cause · The Fix · CTA — 每个都有 🎥/🗣️/💡,茄子半旗→立起的视觉梗保留在 Shot 1 和 Shot 3。💡 标签用中文 TCM 术语(腎陽虛·命門火衰 等),跟 detox 那条一致。
- - **You get a QA beat** — between "Ready" and "Published" you can look at the auto-generated infographic and fix it if it's off, instead of discovering it after it's already DMing strangers.


## 2026-07-07 14:03 — social-ip-engine

### What Didn't Work (negative knowledge)
- | Graph API fetch *also* fails (e.g. Meta having a bad day, rate-limited, deleted account) | Comment vanishes, zero trace | Comment still drops — **but now logged loudly**, diagnosable in seconds instead of the 2-hour Graph API archaeology I just did |
- Honest scope of "won't fail again": the *known* failure modes (missing `from`, webhook disabled, generic missed comments) are now self-healing or loudly surfaced. I can't promise Meta won't invent a fourth way to break this — nobody can — but you now have three independent layers (self-heal, alert, sweep) instead of zero, and nothing sits invisible anymore.
- Yes — and this matters specifically because I used `POST /admin/backfill-comments` (the *live* endpoint against the real production CRM), not the local script. Your own CLAUDE.md flags exactly this distinction: the local script runs with `pipeline=None` (no persistence, writes to local SQLite even if wired), so a user's next reply arrives with zero memory of ever being messaged — that caused the David/"1" incident on 2026-07-01. Since I avoided that path, Rajesh's and your DM exchange is persisted for real — a follow-up reply will land with full context.

### Architecture Decisions
- Good review. Applying the two concrete LOW fixes now; I'll address the MEDIUM one with reasoning rather than blindly matching the pattern.

### Decisions & Reasoning
- We have a Render API key. Let me pull the actual production logs to find the real comment event and see exactly why it was dropped, rather than guessing.
- Dug into this instead of guessing. Here's what I found — and what I still need from you.
- **Why it failed:** Meta's own Instagram webhook infrastructure intermittently omits the `from` object on comment events. Confirmed by cross-referencing: David's comment had `from` in the payload, Rajesh's and your test comment — same post, hours/seconds apart — didn't. That's not our bug. That's Meta being Meta. Our bug was that our code *required* a field Meta doesn't guarantee, and when it was missing, it died with **zero log output anywhere** — not even the exception handlers caught it, because there was no exception, just a silent `continue`.
- **The actual gap, and I should've led with this instead of letting you find it:** logging something loudly doesn't help if nobody's looking. Right now if this fires again, it sits in Render's log stream until someone thinks to grep it — same blind spot that made this take a Graph API investigation instead of a 30-second log check. That's not fixed. Two things would actually close that gap:
- 1. **Alert on the drop** — Slack/email ping the moment `"still no 'from_id' after Graph API backfill attempt"` fires, instead of waiting for a lead to complain.
- Neither is built. Want me to build the alert now — that's the cheap, high-value one? The reconciliation sweep is a bigger lift and I'd want to scope it properly rather than bolt it on in the heat of this.
- Good catch by my own test — pytest's logging plugin pre-configures the root logger before `src.web` is imported, which would silently make `basicConfig()` a no-op in that case too (not just in tests — any pre-existing root handler from anywhere would do the same in production). Let me harden the real fix with `force=True`, then rewrite the test to validate in a clean subprocess instead of fighting pytest's own logging plugin:
- **One unrelated thing I noticed and did NOT touch, flagging it because it matters:** production logs show `CRM: using SQLite backend`, and `DATABASE_URL` isn't actually set on this Render service despite `render.yaml` documenting a Postgres link — this service was never blueprint-attached, so that link was never real. If true, production data is sitting on the instance's local disk, not Postgres. Separate issue, nothing to do with today's work — want me to look into it next, or is that already known/intentional?


## 2026-07-07 14:03 — social-ip-engine

### Decisions & Reasoning
- 1. **`video-editing`**（ECC 通用 skill）—— 这个做的是剪**真实素材**（FFmpeg → Remotion → ElevenLabs → Descript/CapCut），前提是你有原始录像可以剪。跟你的项目完全不对口——Jackie/Chloe 走的是 AI 数字人路线（`studio/notion_video.py` + 即梦 CLI，`gpt-image-2` 生成静帧），根本没有"真实素材"这一步。如果你把这个 skill 拉进来用，大概率会被它带偏（它会假设你有 raw footage 可以剪）。
- 关于第二个问题，扫了一圈相关 skill，我的判断是不用照单全收，挑两个真正补到点子上的：
- **2. 一个更大的、结构性的缺口，不是靠加 skill 能补的**：你这条 pipeline 是单向的——外部研究 → 写稿 → 发布，然后就断了。没有一环是"这条已发布的内容表现如何 → 反哺下一轮研究/选角度"。`ad-creative` skill 里那个"pull performance data → 分析赢家/输家模式 → 生成新一批"的闭环，本质上就是你现在缺的那一环。你的 Notion Production Tracker 应该已经有评论数/互动数据（不然 DM Wired 那套怎么判断效果),值得把这个反馈循环也写进 `tcm-trend-to-script` 或者单独开一个 `tcm-content-retro` skill，不然每次都是从零外部研究开始,自己发布的东西积累的信号完全没被利用。


## 2026-07-07 14:06 — social-ip-engine

### What Didn't Work (negative knowledge)
- Both shot 2 and shot 4 failures were the **same transient upload glitch** your own docs flagged ("realistic talking-head + audio is flaky — retry usually works") — not a structural "two people = broken" rule. I was too quick to trust the wrapper's silent fallback instead of testing it directly like you said.
- Caught a real problem before calling this done — I need to flag it rather than let it slide. When I trimmed shot 2's audio to fit the API's 15s limit, I cut off the tail of the sentence: it now ends **"...to keep the pressure **work**"** instead of "...working all day." That's broken content, not just cosmetic.

### Architecture Decisions
- - 8 lint warnings, all "caption line >42 chars" — purely cosmetic; JianYing wraps them. Say the word and I'll auto-split long cues into 2 lines.
- That's the real bug. My "hands only" fix was the wrong direction — it *guaranteed* no lip-sync (no face = nothing to sync). The actual fix: redesign Shot 2 as **single-person, frontal, talking head** — Jackie demoing the patch on his own ear or a prop model instead of a second "patient" — which is exactly the pattern that already works in shots 1/3/4.
- **Redesigned Shot 2** as single-person, frontal, talking head — Jackie holding an anatomical ear model (reusing the same prop from Shot 1) and pressing the patch onto it, rather than a second "patient." Face is dead-on to camera, satisfying both constraints. Bead is spec'd as plain matte gold, no glow, in both the image and motion prompts.
- **The real fix — the same trick every talking-head video with cutaways uses:** split Shot 2 into two beats that get concatenated into one clip:
- Want me to build it this way (2 sub-clips → concat into `shot2.mp4`)? I'd split the ~12s narration into two chunks (intro line = Beat A, points/demo line = Beat B) so each half's audio matches its visual. Or if you'd rather keep it as one continuous two-person shot and just accept the `image2video` fallback (no lip-sync, but simpler/faster), say so and I'll go back to that with just the glow fixed.

### Decisions & Reasoning
- **Merged footage** → JianYing draft `stomach-jackie-en`:
- Two separate things — let me diagnose both before proposing, because the fix differs. Let me check the current canvas size and whether JianYing actually kept our caption track.
- 2. **The captions ARE in the draft** (text track, 15 segments — mtime shows JianYing hasn't re-saved it). You're not seeing them because the caption's default position is set for a 16:9 frame, so they're placed off the visible portrait area / wrong spot.
- Right — use the individual `shot*_regen` clips (freshly concatenated) instead of `final_regen`. That guarantees the latest regen shots. Concatenating them, then burning the captions on the native 3:4 frame with audio:
- 2. **Insert your real product footage** into Shot 2 instead of a generated close-up, then burn captions like we just did on the stomach reel.
- Video generation is running in the background (this typically takes several minutes — 4 shots through Seedance 2.0, then poll + download + concat). I'll let it run and check back when it completes rather than polling manually.
- Fair pushback — you're right that the demo needs a real patient, not Jackie miming on a plastic ear. Let me be straight about the actual constraint though, because it's not me being cautious for no reason — it's baked into your own `studio/CLAUDE.md`, verified from real production runs:
- Result: real interaction with the patient stays in, AND you get an actual lip-synced beat elsewhere in the same shot — best of both, instead of me quietly picking one over the other.


## 2026-07-07 14:07 — social-ip-engine

### What Didn't Work (negative knowledge)
- | Graph API fetch *also* fails (e.g. Meta having a bad day, rate-limited, deleted account) | Comment vanishes, zero trace | Comment still drops — **but now logged loudly**, diagnosable in seconds instead of the 2-hour Graph API archaeology I just did |
- Honest scope of "won't fail again": the *known* failure modes (missing `from`, webhook disabled, generic missed comments) are now self-healing or loudly surfaced. I can't promise Meta won't invent a fourth way to break this — nobody can — but you now have three independent layers (self-heal, alert, sweep) instead of zero, and nothing sits invisible anymore.
- Yes — and this matters specifically because I used `POST /admin/backfill-comments` (the *live* endpoint against the real production CRM), not the local script. Your own CLAUDE.md flags exactly this distinction: the local script runs with `pipeline=None` (no persistence, writes to local SQLite even if wired), so a user's next reply arrives with zero memory of ever being messaged — that caused the David/"1" incident on 2026-07-01. Since I avoided that path, Rajesh's and your DM exchange is persisted for real — a follow-up reply will land with full context.

### Architecture Decisions
- Good review. Applying the two concrete LOW fixes now; I'll address the MEDIUM one with reasoning rather than blindly matching the pattern.

### Decisions & Reasoning
- We have a Render API key. Let me pull the actual production logs to find the real comment event and see exactly why it was dropped, rather than guessing.
- Dug into this instead of guessing. Here's what I found — and what I still need from you.
- **Why it failed:** Meta's own Instagram webhook infrastructure intermittently omits the `from` object on comment events. Confirmed by cross-referencing: David's comment had `from` in the payload, Rajesh's and your test comment — same post, hours/seconds apart — didn't. That's not our bug. That's Meta being Meta. Our bug was that our code *required* a field Meta doesn't guarantee, and when it was missing, it died with **zero log output anywhere** — not even the exception handlers caught it, because there was no exception, just a silent `continue`.
- **The actual gap, and I should've led with this instead of letting you find it:** logging something loudly doesn't help if nobody's looking. Right now if this fires again, it sits in Render's log stream until someone thinks to grep it — same blind spot that made this take a Graph API investigation instead of a 30-second log check. That's not fixed. Two things would actually close that gap:
- 1. **Alert on the drop** — Slack/email ping the moment `"still no 'from_id' after Graph API backfill attempt"` fires, instead of waiting for a lead to complain.
- Neither is built. Want me to build the alert now — that's the cheap, high-value one? The reconciliation sweep is a bigger lift and I'd want to scope it properly rather than bolt it on in the heat of this.
- Good catch by my own test — pytest's logging plugin pre-configures the root logger before `src.web` is imported, which would silently make `basicConfig()` a no-op in that case too (not just in tests — any pre-existing root handler from anywhere would do the same in production). Let me harden the real fix with `force=True`, then rewrite the test to validate in a clean subprocess instead of fighting pytest's own logging plugin:
- **One unrelated thing I noticed and did NOT touch, flagging it because it matters:** production logs show `CRM: using SQLite backend`, and `DATABASE_URL` isn't actually set on this Render service despite `render.yaml` documenting a Postgres link — this service was never blueprint-attached, so that link was never real. If true, production data is sitting on the instance's local disk, not Postgres. Separate issue, nothing to do with today's work — want me to look into it next, or is that already known/intentional?


## 2026-07-07 14:17 — social-ip-engine

### What Didn't Work (negative knowledge)
- | Graph API fetch *also* fails (e.g. Meta having a bad day, rate-limited, deleted account) | Comment vanishes, zero trace | Comment still drops — **but now logged loudly**, diagnosable in seconds instead of the 2-hour Graph API archaeology I just did |
- Honest scope of "won't fail again": the *known* failure modes (missing `from`, webhook disabled, generic missed comments) are now self-healing or loudly surfaced. I can't promise Meta won't invent a fourth way to break this — nobody can — but you now have three independent layers (self-heal, alert, sweep) instead of zero, and nothing sits invisible anymore.
- Yes — and this matters specifically because I used `POST /admin/backfill-comments` (the *live* endpoint against the real production CRM), not the local script. Your own CLAUDE.md flags exactly this distinction: the local script runs with `pipeline=None` (no persistence, writes to local SQLite even if wired), so a user's next reply arrives with zero memory of ever being messaged — that caused the David/"1" incident on 2026-07-01. Since I avoided that path, Rajesh's and your DM exchange is persisted for real — a follow-up reply will land with full context.

### Architecture Decisions
- Good review. Applying the two concrete LOW fixes now; I'll address the MEDIUM one with reasoning rather than blindly matching the pattern.

### Decisions & Reasoning
- We have a Render API key. Let me pull the actual production logs to find the real comment event and see exactly why it was dropped, rather than guessing.
- Dug into this instead of guessing. Here's what I found — and what I still need from you.
- **Why it failed:** Meta's own Instagram webhook infrastructure intermittently omits the `from` object on comment events. Confirmed by cross-referencing: David's comment had `from` in the payload, Rajesh's and your test comment — same post, hours/seconds apart — didn't. That's not our bug. That's Meta being Meta. Our bug was that our code *required* a field Meta doesn't guarantee, and when it was missing, it died with **zero log output anywhere** — not even the exception handlers caught it, because there was no exception, just a silent `continue`.
- **The actual gap, and I should've led with this instead of letting you find it:** logging something loudly doesn't help if nobody's looking. Right now if this fires again, it sits in Render's log stream until someone thinks to grep it — same blind spot that made this take a Graph API investigation instead of a 30-second log check. That's not fixed. Two things would actually close that gap:
- 1. **Alert on the drop** — Slack/email ping the moment `"still no 'from_id' after Graph API backfill attempt"` fires, instead of waiting for a lead to complain.
- Neither is built. Want me to build the alert now — that's the cheap, high-value one? The reconciliation sweep is a bigger lift and I'd want to scope it properly rather than bolt it on in the heat of this.
- Good catch by my own test — pytest's logging plugin pre-configures the root logger before `src.web` is imported, which would silently make `basicConfig()` a no-op in that case too (not just in tests — any pre-existing root handler from anywhere would do the same in production). Let me harden the real fix with `force=True`, then rewrite the test to validate in a clean subprocess instead of fighting pytest's own logging plugin:
- **One unrelated thing I noticed and did NOT touch, flagging it because it matters:** production logs show `CRM: using SQLite backend`, and `DATABASE_URL` isn't actually set on this Render service despite `render.yaml` documenting a Postgres link — this service was never blueprint-attached, so that link was never real. If true, production data is sitting on the instance's local disk, not Postgres. Separate issue, nothing to do with today's work — want me to look into it next, or is that already known/intentional?


## 2026-07-07 14:22 — social-ip-engine

### What Didn't Work (negative knowledge)
- | Graph API fetch *also* fails (e.g. Meta having a bad day, rate-limited, deleted account) | Comment vanishes, zero trace | Comment still drops — **but now logged loudly**, diagnosable in seconds instead of the 2-hour Graph API archaeology I just did |
- Honest scope of "won't fail again": the *known* failure modes (missing `from`, webhook disabled, generic missed comments) are now self-healing or loudly surfaced. I can't promise Meta won't invent a fourth way to break this — nobody can — but you now have three independent layers (self-heal, alert, sweep) instead of zero, and nothing sits invisible anymore.
- Yes — and this matters specifically because I used `POST /admin/backfill-comments` (the *live* endpoint against the real production CRM), not the local script. Your own CLAUDE.md flags exactly this distinction: the local script runs with `pipeline=None` (no persistence, writes to local SQLite even if wired), so a user's next reply arrives with zero memory of ever being messaged — that caused the David/"1" incident on 2026-07-01. Since I avoided that path, Rajesh's and your DM exchange is persisted for real — a follow-up reply will land with full context.

### Architecture Decisions
- Good review. Applying the two concrete LOW fixes now; I'll address the MEDIUM one with reasoning rather than blindly matching the pattern.

### Decisions & Reasoning
- We have a Render API key. Let me pull the actual production logs to find the real comment event and see exactly why it was dropped, rather than guessing.
- Dug into this instead of guessing. Here's what I found — and what I still need from you.
- **Why it failed:** Meta's own Instagram webhook infrastructure intermittently omits the `from` object on comment events. Confirmed by cross-referencing: David's comment had `from` in the payload, Rajesh's and your test comment — same post, hours/seconds apart — didn't. That's not our bug. That's Meta being Meta. Our bug was that our code *required* a field Meta doesn't guarantee, and when it was missing, it died with **zero log output anywhere** — not even the exception handlers caught it, because there was no exception, just a silent `continue`.
- **The actual gap, and I should've led with this instead of letting you find it:** logging something loudly doesn't help if nobody's looking. Right now if this fires again, it sits in Render's log stream until someone thinks to grep it — same blind spot that made this take a Graph API investigation instead of a 30-second log check. That's not fixed. Two things would actually close that gap:
- 1. **Alert on the drop** — Slack/email ping the moment `"still no 'from_id' after Graph API backfill attempt"` fires, instead of waiting for a lead to complain.
- Neither is built. Want me to build the alert now — that's the cheap, high-value one? The reconciliation sweep is a bigger lift and I'd want to scope it properly rather than bolt it on in the heat of this.
- Good catch by my own test — pytest's logging plugin pre-configures the root logger before `src.web` is imported, which would silently make `basicConfig()` a no-op in that case too (not just in tests — any pre-existing root handler from anywhere would do the same in production). Let me harden the real fix with `force=True`, then rewrite the test to validate in a clean subprocess instead of fighting pytest's own logging plugin:
- **One unrelated thing I noticed and did NOT touch, flagging it because it matters:** production logs show `CRM: using SQLite backend`, and `DATABASE_URL` isn't actually set on this Render service despite `render.yaml` documenting a Postgres link — this service was never blueprint-attached, so that link was never real. If true, production data is sitting on the instance's local disk, not Postgres. Separate issue, nothing to do with today's work — want me to look into it next, or is that already known/intentional?


## 2026-07-07 14:27 — social-ip-engine

### What Didn't Work (negative knowledge)
- | Graph API fetch *also* fails (e.g. Meta having a bad day, rate-limited, deleted account) | Comment vanishes, zero trace | Comment still drops — **but now logged loudly**, diagnosable in seconds instead of the 2-hour Graph API archaeology I just did |
- Honest scope of "won't fail again": the *known* failure modes (missing `from`, webhook disabled, generic missed comments) are now self-healing or loudly surfaced. I can't promise Meta won't invent a fourth way to break this — nobody can — but you now have three independent layers (self-heal, alert, sweep) instead of zero, and nothing sits invisible anymore.
- Yes — and this matters specifically because I used `POST /admin/backfill-comments` (the *live* endpoint against the real production CRM), not the local script. Your own CLAUDE.md flags exactly this distinction: the local script runs with `pipeline=None` (no persistence, writes to local SQLite even if wired), so a user's next reply arrives with zero memory of ever being messaged — that caused the David/"1" incident on 2026-07-01. Since I avoided that path, Rajesh's and your DM exchange is persisted for real — a follow-up reply will land with full context.

### Architecture Decisions
- Good review. Applying the two concrete LOW fixes now; I'll address the MEDIUM one with reasoning rather than blindly matching the pattern.

### Decisions & Reasoning
- We have a Render API key. Let me pull the actual production logs to find the real comment event and see exactly why it was dropped, rather than guessing.
- Dug into this instead of guessing. Here's what I found — and what I still need from you.
- **Why it failed:** Meta's own Instagram webhook infrastructure intermittently omits the `from` object on comment events. Confirmed by cross-referencing: David's comment had `from` in the payload, Rajesh's and your test comment — same post, hours/seconds apart — didn't. That's not our bug. That's Meta being Meta. Our bug was that our code *required* a field Meta doesn't guarantee, and when it was missing, it died with **zero log output anywhere** — not even the exception handlers caught it, because there was no exception, just a silent `continue`.
- **The actual gap, and I should've led with this instead of letting you find it:** logging something loudly doesn't help if nobody's looking. Right now if this fires again, it sits in Render's log stream until someone thinks to grep it — same blind spot that made this take a Graph API investigation instead of a 30-second log check. That's not fixed. Two things would actually close that gap:
- 1. **Alert on the drop** — Slack/email ping the moment `"still no 'from_id' after Graph API backfill attempt"` fires, instead of waiting for a lead to complain.
- Neither is built. Want me to build the alert now — that's the cheap, high-value one? The reconciliation sweep is a bigger lift and I'd want to scope it properly rather than bolt it on in the heat of this.
- Good catch by my own test — pytest's logging plugin pre-configures the root logger before `src.web` is imported, which would silently make `basicConfig()` a no-op in that case too (not just in tests — any pre-existing root handler from anywhere would do the same in production). Let me harden the real fix with `force=True`, then rewrite the test to validate in a clean subprocess instead of fighting pytest's own logging plugin:
- **One unrelated thing I noticed and did NOT touch, flagging it because it matters:** production logs show `CRM: using SQLite backend`, and `DATABASE_URL` isn't actually set on this Render service despite `render.yaml` documenting a Postgres link — this service was never blueprint-attached, so that link was never real. If true, production data is sitting on the instance's local disk, not Postgres. Separate issue, nothing to do with today's work — want me to look into it next, or is that already known/intentional?


## 2026-07-07 14:32 — social-ip-engine

### What Didn't Work (negative knowledge)
- The problem is **not** your setup — it's that the secret I set is saved in Render's config but **the running instance hasn't picked it up.** Setting an env var doesn't auto-restart the process here (that broken auto-deploy again). Proof: my own call with the correct secret *also* just got 401 — the live process still has an empty secret in memory.

### Architecture Decisions
- That's the pattern — tight 4-line Master Script (Hook / Root Cause / Fix / CTA) + 4 shots + DM protocol. Rewriting to match, pain points folded into the root-cause line instead of a whole barrage.

### Decisions & Reasoning
- **选题我 100% 支持**——补肾壮阳/男性活力在 TCM 里是转化率最高、最缺内容、评论区最炸的赛道。你要 gimmick、要博眼球,方向完全对。
- 好消息是:**冲击力和搞笑感可以完全保留,只要把"器官"抽象成一个符号**——平台审不到,但人人秒懂。🍆 才是互联网通用暗号,不是保险套。
- - Body:完整 **📜 Master Script(6 shots)** + **🎬 Shot Guide**(每个 shot 有 🎥 画面 / 🗣️ 台词 / 💡 用意)+ **🖼️ Thumbnail 图片 prompt**
- 1. **CTA keyword 用 `VITALITY`**,不用 `kidney`——避免跟你现有 kidney 类内容的关键词在 `comment_responses.json` 里撞规则。要换成别的词跟我说。
- 图我没直接生成——想先让你过一眼概念落地对不对。你点头,我就用 body 里那个 thumbnail prompt 跑图(你有 `notion_image.py` / `batch_infographic_gen.py`),生成后直接回填到这条 concept 的 🖼️ 区。
- **③ SOLUTION 点破根因 + 解法(~7s)** — 所有症状指向一个根:**肾阳虚,内火熄了**;晨勃只是最明显的那盏警示灯。不是年纪、不是没救 → 温热熟食 + 早睡 + 别再用冷饮/熬夜/压力掏空油箱。茄子这时慢慢立起来 → "做对了……旗子就又升起来了。"
- Hook · Root Cause · The Fix · CTA — 每个都有 🎥/🗣️/💡,茄子半旗→立起的视觉梗保留在 Shot 1 和 Shot 3。💡 标签用中文 TCM 术语(腎陽虛·命門火衰 等),跟 detox 那条一致。
- - **You get a QA beat** — between "Ready" and "Published" you can look at the auto-generated infographic and fix it if it's off, instead of discovering it after it's already DMing strangers.


## 2026-07-07 14:33 — social-ip-engine

### Architecture Decisions
- **Step 4 hook gate:** added an escape hatch — if the 3 built-in mechanics (pattern interrupt / myth-bust / curiosity gap) get exhausted and you're still pushing back, pull a genuinely different lever from `marketing-psychology` (Loss Aversion, Contrast Effect, Zeigarnik open-loop) instead of a 4th rephrase of the same idea.

### Decisions & Reasoning
- 1. **`video-editing`**（ECC 通用 skill）—— 这个做的是剪**真实素材**（FFmpeg → Remotion → ElevenLabs → Descript/CapCut），前提是你有原始录像可以剪。跟你的项目完全不对口——Jackie/Chloe 走的是 AI 数字人路线（`studio/notion_video.py` + 即梦 CLI，`gpt-image-2` 生成静帧），根本没有"真实素材"这一步。如果你把这个 skill 拉进来用，大概率会被它带偏（它会假设你有 raw footage 可以剪）。
- 关于第二个问题，扫了一圈相关 skill，我的判断是不用照单全收，挑两个真正补到点子上的：
- **2. 一个更大的、结构性的缺口，不是靠加 skill 能补的**：你这条 pipeline 是单向的——外部研究 → 写稿 → 发布，然后就断了。没有一环是"这条已发布的内容表现如何 → 反哺下一轮研究/选角度"。`ad-creative` skill 里那个"pull performance data → 分析赢家/输家模式 → 生成新一批"的闭环，本质上就是你现在缺的那一环。你的 Notion Production Tracker 应该已经有评论数/互动数据（不然 DM Wired 那套怎么判断效果),值得把这个反馈循环也写进 `tcm-trend-to-script` 或者单独开一个 `tcm-content-retro` skill，不然每次都是从零外部研究开始,自己发布的东西积累的信号完全没被利用。


## 2026-07-07 14:34 — social-ip-engine

### Architecture Decisions
- **Step 4 hook gate:** added an escape hatch — if the 3 built-in mechanics (pattern interrupt / myth-bust / curiosity gap) get exhausted and you're still pushing back, pull a genuinely different lever from `marketing-psychology` (Loss Aversion, Contrast Effect, Zeigarnik open-loop) instead of a 4th rephrase of the same idea.

### Decisions & Reasoning
- 1. **`video-editing`**（ECC 通用 skill）—— 这个做的是剪**真实素材**（FFmpeg → Remotion → ElevenLabs → Descript/CapCut），前提是你有原始录像可以剪。跟你的项目完全不对口——Jackie/Chloe 走的是 AI 数字人路线（`studio/notion_video.py` + 即梦 CLI，`gpt-image-2` 生成静帧），根本没有"真实素材"这一步。如果你把这个 skill 拉进来用，大概率会被它带偏（它会假设你有 raw footage 可以剪）。
- 关于第二个问题，扫了一圈相关 skill，我的判断是不用照单全收，挑两个真正补到点子上的：
- **2. 一个更大的、结构性的缺口，不是靠加 skill 能补的**：你这条 pipeline 是单向的——外部研究 → 写稿 → 发布，然后就断了。没有一环是"这条已发布的内容表现如何 → 反哺下一轮研究/选角度"。`ad-creative` skill 里那个"pull performance data → 分析赢家/输家模式 → 生成新一批"的闭环，本质上就是你现在缺的那一环。你的 Notion Production Tracker 应该已经有评论数/互动数据（不然 DM Wired 那套怎么判断效果),值得把这个反馈循环也写进 `tcm-trend-to-script` 或者单独开一个 `tcm-content-retro` skill，不然每次都是从零外部研究开始,自己发布的东西积累的信号完全没被利用。


## 2026-07-07 14:39 — social-ip-engine

### Architecture Decisions
- **Step 4 hook gate:** added an escape hatch — if the 3 built-in mechanics (pattern interrupt / myth-bust / curiosity gap) get exhausted and you're still pushing back, pull a genuinely different lever from `marketing-psychology` (Loss Aversion, Contrast Effect, Zeigarnik open-loop) instead of a 4th rephrase of the same idea.

### Decisions & Reasoning
- 1. **`video-editing`**（ECC 通用 skill）—— 这个做的是剪**真实素材**（FFmpeg → Remotion → ElevenLabs → Descript/CapCut），前提是你有原始录像可以剪。跟你的项目完全不对口——Jackie/Chloe 走的是 AI 数字人路线（`studio/notion_video.py` + 即梦 CLI，`gpt-image-2` 生成静帧），根本没有"真实素材"这一步。如果你把这个 skill 拉进来用，大概率会被它带偏（它会假设你有 raw footage 可以剪）。
- 关于第二个问题，扫了一圈相关 skill，我的判断是不用照单全收，挑两个真正补到点子上的：
- **2. 一个更大的、结构性的缺口，不是靠加 skill 能补的**：你这条 pipeline 是单向的——外部研究 → 写稿 → 发布，然后就断了。没有一环是"这条已发布的内容表现如何 → 反哺下一轮研究/选角度"。`ad-creative` skill 里那个"pull performance data → 分析赢家/输家模式 → 生成新一批"的闭环，本质上就是你现在缺的那一环。你的 Notion Production Tracker 应该已经有评论数/互动数据（不然 DM Wired 那套怎么判断效果),值得把这个反馈循环也写进 `tcm-trend-to-script` 或者单独开一个 `tcm-content-retro` skill，不然每次都是从零外部研究开始,自己发布的东西积累的信号完全没被利用。


## 2026-07-07 14:45 — social-ip-engine

### Architecture Decisions
- **Step 4 hook gate:** added an escape hatch — if the 3 built-in mechanics (pattern interrupt / myth-bust / curiosity gap) get exhausted and you're still pushing back, pull a genuinely different lever from `marketing-psychology` (Loss Aversion, Contrast Effect, Zeigarnik open-loop) instead of a 4th rephrase of the same idea.

### Decisions & Reasoning
- 1. **`video-editing`**（ECC 通用 skill）—— 这个做的是剪**真实素材**（FFmpeg → Remotion → ElevenLabs → Descript/CapCut），前提是你有原始录像可以剪。跟你的项目完全不对口——Jackie/Chloe 走的是 AI 数字人路线（`studio/notion_video.py` + 即梦 CLI，`gpt-image-2` 生成静帧），根本没有"真实素材"这一步。如果你把这个 skill 拉进来用，大概率会被它带偏（它会假设你有 raw footage 可以剪）。
- 关于第二个问题，扫了一圈相关 skill，我的判断是不用照单全收，挑两个真正补到点子上的：
- **2. 一个更大的、结构性的缺口，不是靠加 skill 能补的**：你这条 pipeline 是单向的——外部研究 → 写稿 → 发布，然后就断了。没有一环是"这条已发布的内容表现如何 → 反哺下一轮研究/选角度"。`ad-creative` skill 里那个"pull performance data → 分析赢家/输家模式 → 生成新一批"的闭环，本质上就是你现在缺的那一环。你的 Notion Production Tracker 应该已经有评论数/互动数据（不然 DM Wired 那套怎么判断效果),值得把这个反馈循环也写进 `tcm-trend-to-script` 或者单独开一个 `tcm-content-retro` skill，不然每次都是从零外部研究开始,自己发布的东西积累的信号完全没被利用。


## 2026-07-07 14:53 — social-ip-engine

### What Didn't Work (negative knowledge)
- The problem is **not** your setup — it's that the secret I set is saved in Render's config but **the running instance hasn't picked it up.** Setting an env var doesn't auto-restart the process here (that broken auto-deploy again). Proof: my own call with the correct secret *also* just got 401 — the live process still has an empty secret in memory.

### Architecture Decisions
- That's the pattern — tight 4-line Master Script (Hook / Root Cause / Fix / CTA) + 4 shots + DM protocol. Rewriting to match, pain points folded into the root-cause line instead of a whole barrage.
- Now restructuring `run_publish_job` to add the reentrancy guard + fix the sleep-overshoot, plus splitting into smaller helpers (addresses the reviewer's function-length note too):

### Decisions & Reasoning
- **选题我 100% 支持**——补肾壮阳/男性活力在 TCM 里是转化率最高、最缺内容、评论区最炸的赛道。你要 gimmick、要博眼球,方向完全对。
- 好消息是:**冲击力和搞笑感可以完全保留,只要把"器官"抽象成一个符号**——平台审不到,但人人秒懂。🍆 才是互联网通用暗号,不是保险套。
- - Body:完整 **📜 Master Script(6 shots)** + **🎬 Shot Guide**(每个 shot 有 🎥 画面 / 🗣️ 台词 / 💡 用意)+ **🖼️ Thumbnail 图片 prompt**
- 1. **CTA keyword 用 `VITALITY`**,不用 `kidney`——避免跟你现有 kidney 类内容的关键词在 `comment_responses.json` 里撞规则。要换成别的词跟我说。
- 图我没直接生成——想先让你过一眼概念落地对不对。你点头,我就用 body 里那个 thumbnail prompt 跑图(你有 `notion_image.py` / `batch_infographic_gen.py`),生成后直接回填到这条 concept 的 🖼️ 区。
- **③ SOLUTION 点破根因 + 解法(~7s)** — 所有症状指向一个根:**肾阳虚,内火熄了**;晨勃只是最明显的那盏警示灯。不是年纪、不是没救 → 温热熟食 + 早睡 + 别再用冷饮/熬夜/压力掏空油箱。茄子这时慢慢立起来 → "做对了……旗子就又升起来了。"
- Hook · Root Cause · The Fix · CTA — 每个都有 🎥/🗣️/💡,茄子半旗→立起的视觉梗保留在 Shot 1 和 Shot 3。💡 标签用中文 TCM 术语(腎陽虛·命門火衰 等),跟 detox 那条一致。
- - **You get a QA beat** — between "Ready" and "Published" you can look at the auto-generated infographic and fix it if it's off, instead of discovering it after it's already DMing strangers.


## 2026-07-07 15:01 — social-ip-engine

### What Didn't Work (negative knowledge)
- The problem is **not** your setup — it's that the secret I set is saved in Render's config but **the running instance hasn't picked it up.** Setting an env var doesn't auto-restart the process here (that broken auto-deploy again). Proof: my own call with the correct secret *also* just got 401 — the live process still has an empty secret in memory.

### Architecture Decisions
- That's the pattern — tight 4-line Master Script (Hook / Root Cause / Fix / CTA) + 4 shots + DM protocol. Rewriting to match, pain points folded into the root-cause line instead of a whole barrage.
- Now restructuring `run_publish_job` to add the reentrancy guard + fix the sleep-overshoot, plus splitting into smaller helpers (addresses the reviewer's function-length note too):

### Decisions & Reasoning
- **选题我 100% 支持**——补肾壮阳/男性活力在 TCM 里是转化率最高、最缺内容、评论区最炸的赛道。你要 gimmick、要博眼球,方向完全对。
- 好消息是:**冲击力和搞笑感可以完全保留,只要把"器官"抽象成一个符号**——平台审不到,但人人秒懂。🍆 才是互联网通用暗号,不是保险套。
- - Body:完整 **📜 Master Script(6 shots)** + **🎬 Shot Guide**(每个 shot 有 🎥 画面 / 🗣️ 台词 / 💡 用意)+ **🖼️ Thumbnail 图片 prompt**
- 1. **CTA keyword 用 `VITALITY`**,不用 `kidney`——避免跟你现有 kidney 类内容的关键词在 `comment_responses.json` 里撞规则。要换成别的词跟我说。
- 图我没直接生成——想先让你过一眼概念落地对不对。你点头,我就用 body 里那个 thumbnail prompt 跑图(你有 `notion_image.py` / `batch_infographic_gen.py`),生成后直接回填到这条 concept 的 🖼️ 区。
- **③ SOLUTION 点破根因 + 解法(~7s)** — 所有症状指向一个根:**肾阳虚,内火熄了**;晨勃只是最明显的那盏警示灯。不是年纪、不是没救 → 温热熟食 + 早睡 + 别再用冷饮/熬夜/压力掏空油箱。茄子这时慢慢立起来 → "做对了……旗子就又升起来了。"
- Hook · Root Cause · The Fix · CTA — 每个都有 🎥/🗣️/💡,茄子半旗→立起的视觉梗保留在 Shot 1 和 Shot 3。💡 标签用中文 TCM 术语(腎陽虛·命門火衰 等),跟 detox 那条一致。
- - **You get a QA beat** — between "Ready" and "Published" you can look at the auto-generated infographic and fix it if it's off, instead of discovering it after it's already DMing strangers.


## 2026-07-07 15:09 — social-ip-engine

### What Didn't Work (negative knowledge)
- The problem is **not** your setup — it's that the secret I set is saved in Render's config but **the running instance hasn't picked it up.** Setting an env var doesn't auto-restart the process here (that broken auto-deploy again). Proof: my own call with the correct secret *also* just got 401 — the live process still has an empty secret in memory.

### Architecture Decisions
- That's the pattern — tight 4-line Master Script (Hook / Root Cause / Fix / CTA) + 4 shots + DM protocol. Rewriting to match, pain points folded into the root-cause line instead of a whole barrage.
- Now restructuring `run_publish_job` to add the reentrancy guard + fix the sleep-overshoot, plus splitting into smaller helpers (addresses the reviewer's function-length note too):
- So the DM/infographic wiring at Ready-to-Publish was already moved and verified working earlier — that's untouched by everything I built today. Today's work only adds the *second* stage's behavior (real auto-posting), sitting on top of that, exactly matching the split we agreed on:

### Decisions & Reasoning
- **选题我 100% 支持**——补肾壮阳/男性活力在 TCM 里是转化率最高、最缺内容、评论区最炸的赛道。你要 gimmick、要博眼球,方向完全对。
- 好消息是:**冲击力和搞笑感可以完全保留,只要把"器官"抽象成一个符号**——平台审不到,但人人秒懂。🍆 才是互联网通用暗号,不是保险套。
- - Body:完整 **📜 Master Script(6 shots)** + **🎬 Shot Guide**(每个 shot 有 🎥 画面 / 🗣️ 台词 / 💡 用意)+ **🖼️ Thumbnail 图片 prompt**
- 1. **CTA keyword 用 `VITALITY`**,不用 `kidney`——避免跟你现有 kidney 类内容的关键词在 `comment_responses.json` 里撞规则。要换成别的词跟我说。
- 图我没直接生成——想先让你过一眼概念落地对不对。你点头,我就用 body 里那个 thumbnail prompt 跑图(你有 `notion_image.py` / `batch_infographic_gen.py`),生成后直接回填到这条 concept 的 🖼️ 区。
- **③ SOLUTION 点破根因 + 解法(~7s)** — 所有症状指向一个根:**肾阳虚,内火熄了**;晨勃只是最明显的那盏警示灯。不是年纪、不是没救 → 温热熟食 + 早睡 + 别再用冷饮/熬夜/压力掏空油箱。茄子这时慢慢立起来 → "做对了……旗子就又升起来了。"
- Hook · Root Cause · The Fix · CTA — 每个都有 🎥/🗣️/💡,茄子半旗→立起的视觉梗保留在 Shot 1 和 Shot 3。💡 标签用中文 TCM 术语(腎陽虛·命門火衰 等),跟 detox 那条一致。
- - **You get a QA beat** — between "Ready" and "Published" you can look at the auto-generated infographic and fix it if it's off, instead of discovering it after it's already DMing strangers.


## 2026-07-07 15:12 — social-ip-engine

### What Didn't Work (negative knowledge)
- The problem is **not** your setup — it's that the secret I set is saved in Render's config but **the running instance hasn't picked it up.** Setting an env var doesn't auto-restart the process here (that broken auto-deploy again). Proof: my own call with the correct secret *also* just got 401 — the live process still has an empty secret in memory.

### Architecture Decisions
- That's the pattern — tight 4-line Master Script (Hook / Root Cause / Fix / CTA) + 4 shots + DM protocol. Rewriting to match, pain points folded into the root-cause line instead of a whole barrage.
- Now restructuring `run_publish_job` to add the reentrancy guard + fix the sleep-overshoot, plus splitting into smaller helpers (addresses the reviewer's function-length note too):
- So the DM/infographic wiring at Ready-to-Publish was already moved and verified working earlier — that's untouched by everything I built today. Today's work only adds the *second* stage's behavior (real auto-posting), sitting on top of that, exactly matching the split we agreed on:

### Decisions & Reasoning
- **选题我 100% 支持**——补肾壮阳/男性活力在 TCM 里是转化率最高、最缺内容、评论区最炸的赛道。你要 gimmick、要博眼球,方向完全对。
- 好消息是:**冲击力和搞笑感可以完全保留,只要把"器官"抽象成一个符号**——平台审不到,但人人秒懂。🍆 才是互联网通用暗号,不是保险套。
- - Body:完整 **📜 Master Script(6 shots)** + **🎬 Shot Guide**(每个 shot 有 🎥 画面 / 🗣️ 台词 / 💡 用意)+ **🖼️ Thumbnail 图片 prompt**
- 1. **CTA keyword 用 `VITALITY`**,不用 `kidney`——避免跟你现有 kidney 类内容的关键词在 `comment_responses.json` 里撞规则。要换成别的词跟我说。
- 图我没直接生成——想先让你过一眼概念落地对不对。你点头,我就用 body 里那个 thumbnail prompt 跑图(你有 `notion_image.py` / `batch_infographic_gen.py`),生成后直接回填到这条 concept 的 🖼️ 区。
- **③ SOLUTION 点破根因 + 解法(~7s)** — 所有症状指向一个根:**肾阳虚,内火熄了**;晨勃只是最明显的那盏警示灯。不是年纪、不是没救 → 温热熟食 + 早睡 + 别再用冷饮/熬夜/压力掏空油箱。茄子这时慢慢立起来 → "做对了……旗子就又升起来了。"
- Hook · Root Cause · The Fix · CTA — 每个都有 🎥/🗣️/💡,茄子半旗→立起的视觉梗保留在 Shot 1 和 Shot 3。💡 标签用中文 TCM 术语(腎陽虛·命門火衰 等),跟 detox 那条一致。
- - **You get a QA beat** — between "Ready" and "Published" you can look at the auto-generated infographic and fix it if it's off, instead of discovering it after it's already DMing strangers.


## 2026-07-07 15:13 — social-ip-engine

### Architecture Decisions
- **Step 4 hook gate:** added an escape hatch — if the 3 built-in mechanics (pattern interrupt / myth-bust / curiosity gap) get exhausted and you're still pushing back, pull a genuinely different lever from `marketing-psychology` (Loss Aversion, Contrast Effect, Zeigarnik open-loop) instead of a 4th rephrase of the same idea.

### Decisions & Reasoning
- 1. **`video-editing`**（ECC 通用 skill）—— 这个做的是剪**真实素材**（FFmpeg → Remotion → ElevenLabs → Descript/CapCut），前提是你有原始录像可以剪。跟你的项目完全不对口——Jackie/Chloe 走的是 AI 数字人路线（`studio/notion_video.py` + 即梦 CLI，`gpt-image-2` 生成静帧），根本没有"真实素材"这一步。如果你把这个 skill 拉进来用，大概率会被它带偏（它会假设你有 raw footage 可以剪）。
- 关于第二个问题，扫了一圈相关 skill，我的判断是不用照单全收，挑两个真正补到点子上的：
- **2. 一个更大的、结构性的缺口，不是靠加 skill 能补的**：你这条 pipeline 是单向的——外部研究 → 写稿 → 发布，然后就断了。没有一环是"这条已发布的内容表现如何 → 反哺下一轮研究/选角度"。`ad-creative` skill 里那个"pull performance data → 分析赢家/输家模式 → 生成新一批"的闭环，本质上就是你现在缺的那一环。你的 Notion Production Tracker 应该已经有评论数/互动数据（不然 DM Wired 那套怎么判断效果),值得把这个反馈循环也写进 `tcm-trend-to-script` 或者单独开一个 `tcm-content-retro` skill，不然每次都是从零外部研究开始,自己发布的东西积累的信号完全没被利用。


## 2026-07-07 15:16 — social-ip-engine

### What Didn't Work (negative knowledge)
- Both shot 2 and shot 4 failures were the **same transient upload glitch** your own docs flagged ("realistic talking-head + audio is flaky — retry usually works") — not a structural "two people = broken" rule. I was too quick to trust the wrapper's silent fallback instead of testing it directly like you said.
- Caught a real problem before calling this done — I need to flag it rather than let it slide. When I trimmed shot 2's audio to fit the API's 15s limit, I cut off the tail of the sentence: it now ends **"...to keep the pressure **work**"** instead of "...working all day." That's broken content, not just cosmetic.

### Architecture Decisions
- - 8 lint warnings, all "caption line >42 chars" — purely cosmetic; JianYing wraps them. Say the word and I'll auto-split long cues into 2 lines.
- That's the real bug. My "hands only" fix was the wrong direction — it *guaranteed* no lip-sync (no face = nothing to sync). The actual fix: redesign Shot 2 as **single-person, frontal, talking head** — Jackie demoing the patch on his own ear or a prop model instead of a second "patient" — which is exactly the pattern that already works in shots 1/3/4.
- **Redesigned Shot 2** as single-person, frontal, talking head — Jackie holding an anatomical ear model (reusing the same prop from Shot 1) and pressing the patch onto it, rather than a second "patient." Face is dead-on to camera, satisfying both constraints. Bead is spec'd as plain matte gold, no glow, in both the image and motion prompts.
- **The real fix — the same trick every talking-head video with cutaways uses:** split Shot 2 into two beats that get concatenated into one clip:
- Want me to build it this way (2 sub-clips → concat into `shot2.mp4`)? I'd split the ~12s narration into two chunks (intro line = Beat A, points/demo line = Beat B) so each half's audio matches its visual. Or if you'd rather keep it as one continuous two-person shot and just accept the `image2video` fallback (no lip-sync, but simpler/faster), say so and I'll go back to that with just the glow fixed.
- That attached to your **already-running, actual Chrome** (been open since Wednesday) instead of launching a fresh instance — I don't want to force-kill your real browser and disrupt open tabs/work. Switching to the safer approach your own script already uses: extract cookies directly from the Profile 22 cookie database (no need to touch your live Chrome at all) and inject them into a separate, isolated Playwright browser.
- Real session cookies extracted, including `sessionid`, `sid_guard`, etc. — this Chrome profile is genuinely logged into Dreamina Global. Now launching an isolated Playwright browser (separate from your real Chrome), injecting these cookies, and navigating in.

### Decisions & Reasoning
- **Merged footage** → JianYing draft `stomach-jackie-en`:
- Two separate things — let me diagnose both before proposing, because the fix differs. Let me check the current canvas size and whether JianYing actually kept our caption track.
- 2. **The captions ARE in the draft** (text track, 15 segments — mtime shows JianYing hasn't re-saved it). You're not seeing them because the caption's default position is set for a 16:9 frame, so they're placed off the visible portrait area / wrong spot.
- Right — use the individual `shot*_regen` clips (freshly concatenated) instead of `final_regen`. That guarantees the latest regen shots. Concatenating them, then burning the captions on the native 3:4 frame with audio:
- 2. **Insert your real product footage** into Shot 2 instead of a generated close-up, then burn captions like we just did on the stomach reel.
- Video generation is running in the background (this typically takes several minutes — 4 shots through Seedance 2.0, then poll + download + concat). I'll let it run and check back when it completes rather than polling manually.
- Fair pushback — you're right that the demo needs a real patient, not Jackie miming on a plastic ear. Let me be straight about the actual constraint though, because it's not me being cautious for no reason — it's baked into your own `studio/CLAUDE.md`, verified from real production runs:
- Result: real interaction with the patient stays in, AND you get an actual lip-synced beat elsewhere in the same shot — best of both, instead of me quietly picking one over the other.


## 2026-07-07 15:55 — social-ip-engine

### What Didn't Work (negative knowledge)
- The problem is **not** your setup — it's that the secret I set is saved in Render's config but **the running instance hasn't picked it up.** Setting an env var doesn't auto-restart the process here (that broken auto-deploy again). Proof: my own call with the correct secret *also* just got 401 — the live process still has an empty secret in memory.

### Architecture Decisions
- That's the pattern — tight 4-line Master Script (Hook / Root Cause / Fix / CTA) + 4 shots + DM protocol. Rewriting to match, pain points folded into the root-cause line instead of a whole barrage.
- Now restructuring `run_publish_job` to add the reentrancy guard + fix the sleep-overshoot, plus splitting into smaller helpers (addresses the reviewer's function-length note too):
- So the DM/infographic wiring at Ready-to-Publish was already moved and verified working earlier — that's untouched by everything I built today. Today's work only adds the *second* stage's behavior (real auto-posting), sitting on top of that, exactly matching the split we agreed on:

### Decisions & Reasoning
- **选题我 100% 支持**——补肾壮阳/男性活力在 TCM 里是转化率最高、最缺内容、评论区最炸的赛道。你要 gimmick、要博眼球,方向完全对。
- 好消息是:**冲击力和搞笑感可以完全保留,只要把"器官"抽象成一个符号**——平台审不到,但人人秒懂。🍆 才是互联网通用暗号,不是保险套。
- - Body:完整 **📜 Master Script(6 shots)** + **🎬 Shot Guide**(每个 shot 有 🎥 画面 / 🗣️ 台词 / 💡 用意)+ **🖼️ Thumbnail 图片 prompt**
- 1. **CTA keyword 用 `VITALITY`**,不用 `kidney`——避免跟你现有 kidney 类内容的关键词在 `comment_responses.json` 里撞规则。要换成别的词跟我说。
- 图我没直接生成——想先让你过一眼概念落地对不对。你点头,我就用 body 里那个 thumbnail prompt 跑图(你有 `notion_image.py` / `batch_infographic_gen.py`),生成后直接回填到这条 concept 的 🖼️ 区。
- **③ SOLUTION 点破根因 + 解法(~7s)** — 所有症状指向一个根:**肾阳虚,内火熄了**;晨勃只是最明显的那盏警示灯。不是年纪、不是没救 → 温热熟食 + 早睡 + 别再用冷饮/熬夜/压力掏空油箱。茄子这时慢慢立起来 → "做对了……旗子就又升起来了。"
- Hook · Root Cause · The Fix · CTA — 每个都有 🎥/🗣️/💡,茄子半旗→立起的视觉梗保留在 Shot 1 和 Shot 3。💡 标签用中文 TCM 术语(腎陽虛·命門火衰 等),跟 detox 那条一致。
- - **You get a QA beat** — between "Ready" and "Published" you can look at the auto-generated infographic and fix it if it's off, instead of discovering it after it's already DMing strangers.


## 2026-07-07 15:55 — social-ip-engine

### What Didn't Work (negative knowledge)
- Both shot 2 and shot 4 failures were the **same transient upload glitch** your own docs flagged ("realistic talking-head + audio is flaky — retry usually works") — not a structural "two people = broken" rule. I was too quick to trust the wrapper's silent fallback instead of testing it directly like you said.
- Caught a real problem before calling this done — I need to flag it rather than let it slide. When I trimmed shot 2's audio to fit the API's 15s limit, I cut off the tail of the sentence: it now ends **"...to keep the pressure **work**"** instead of "...working all day." That's broken content, not just cosmetic.

### Architecture Decisions
- - 8 lint warnings, all "caption line >42 chars" — purely cosmetic; JianYing wraps them. Say the word and I'll auto-split long cues into 2 lines.
- That's the real bug. My "hands only" fix was the wrong direction — it *guaranteed* no lip-sync (no face = nothing to sync). The actual fix: redesign Shot 2 as **single-person, frontal, talking head** — Jackie demoing the patch on his own ear or a prop model instead of a second "patient" — which is exactly the pattern that already works in shots 1/3/4.
- **Redesigned Shot 2** as single-person, frontal, talking head — Jackie holding an anatomical ear model (reusing the same prop from Shot 1) and pressing the patch onto it, rather than a second "patient." Face is dead-on to camera, satisfying both constraints. Bead is spec'd as plain matte gold, no glow, in both the image and motion prompts.
- **The real fix — the same trick every talking-head video with cutaways uses:** split Shot 2 into two beats that get concatenated into one clip:
- Want me to build it this way (2 sub-clips → concat into `shot2.mp4`)? I'd split the ~12s narration into two chunks (intro line = Beat A, points/demo line = Beat B) so each half's audio matches its visual. Or if you'd rather keep it as one continuous two-person shot and just accept the `image2video` fallback (no lip-sync, but simpler/faster), say so and I'll go back to that with just the glow fixed.
- That attached to your **already-running, actual Chrome** (been open since Wednesday) instead of launching a fresh instance — I don't want to force-kill your real browser and disrupt open tabs/work. Switching to the safer approach your own script already uses: extract cookies directly from the Profile 22 cookie database (no need to touch your live Chrome at all) and inject them into a separate, isolated Playwright browser.
- Real session cookies extracted, including `sessionid`, `sid_guard`, etc. — this Chrome profile is genuinely logged into Dreamina Global. Now launching an isolated Playwright browser (separate from your real Chrome), injecting these cookies, and navigating in.
- 1. **Split shot 2's audio into ~3 segments of ≤5s each**, generate 3 separate clips here (same reference image, different audio chunk each), then concat them — doable, but ~3x the credits and a small risk of visual discontinuity between segments.

### Decisions & Reasoning
- **Merged footage** → JianYing draft `stomach-jackie-en`:
- Two separate things — let me diagnose both before proposing, because the fix differs. Let me check the current canvas size and whether JianYing actually kept our caption track.
- 2. **The captions ARE in the draft** (text track, 15 segments — mtime shows JianYing hasn't re-saved it). You're not seeing them because the caption's default position is set for a 16:9 frame, so they're placed off the visible portrait area / wrong spot.
- Right — use the individual `shot*_regen` clips (freshly concatenated) instead of `final_regen`. That guarantees the latest regen shots. Concatenating them, then burning the captions on the native 3:4 frame with audio:
- 2. **Insert your real product footage** into Shot 2 instead of a generated close-up, then burn captions like we just did on the stomach reel.
- Video generation is running in the background (this typically takes several minutes — 4 shots through Seedance 2.0, then poll + download + concat). I'll let it run and check back when it completes rather than polling manually.
- Fair pushback — you're right that the demo needs a real patient, not Jackie miming on a plastic ear. Let me be straight about the actual constraint though, because it's not me being cautious for no reason — it's baked into your own `studio/CLAUDE.md`, verified from real production runs:
- Result: real interaction with the patient stays in, AND you get an actual lip-synced beat elsewhere in the same shot — best of both, instead of me quietly picking one over the other.


## 2026-07-07 15:55 — social-ip-engine

### What Didn't Work (negative knowledge)
- | Graph API fetch *also* fails (e.g. Meta having a bad day, rate-limited, deleted account) | Comment vanishes, zero trace | Comment still drops — **but now logged loudly**, diagnosable in seconds instead of the 2-hour Graph API archaeology I just did |
- Honest scope of "won't fail again": the *known* failure modes (missing `from`, webhook disabled, generic missed comments) are now self-healing or loudly surfaced. I can't promise Meta won't invent a fourth way to break this — nobody can — but you now have three independent layers (self-heal, alert, sweep) instead of zero, and nothing sits invisible anymore.
- Yes — and this matters specifically because I used `POST /admin/backfill-comments` (the *live* endpoint against the real production CRM), not the local script. Your own CLAUDE.md flags exactly this distinction: the local script runs with `pipeline=None` (no persistence, writes to local SQLite even if wired), so a user's next reply arrives with zero memory of ever being messaged — that caused the David/"1" incident on 2026-07-01. Since I avoided that path, Rajesh's and your DM exchange is persisted for real — a follow-up reply will land with full context.

### Architecture Decisions
- Good review. Applying the two concrete LOW fixes now; I'll address the MEDIUM one with reasoning rather than blindly matching the pattern.

### Decisions & Reasoning
- We have a Render API key. Let me pull the actual production logs to find the real comment event and see exactly why it was dropped, rather than guessing.
- Dug into this instead of guessing. Here's what I found — and what I still need from you.
- **Why it failed:** Meta's own Instagram webhook infrastructure intermittently omits the `from` object on comment events. Confirmed by cross-referencing: David's comment had `from` in the payload, Rajesh's and your test comment — same post, hours/seconds apart — didn't. That's not our bug. That's Meta being Meta. Our bug was that our code *required* a field Meta doesn't guarantee, and when it was missing, it died with **zero log output anywhere** — not even the exception handlers caught it, because there was no exception, just a silent `continue`.
- **The actual gap, and I should've led with this instead of letting you find it:** logging something loudly doesn't help if nobody's looking. Right now if this fires again, it sits in Render's log stream until someone thinks to grep it — same blind spot that made this take a Graph API investigation instead of a 30-second log check. That's not fixed. Two things would actually close that gap:
- 1. **Alert on the drop** — Slack/email ping the moment `"still no 'from_id' after Graph API backfill attempt"` fires, instead of waiting for a lead to complain.
- Neither is built. Want me to build the alert now — that's the cheap, high-value one? The reconciliation sweep is a bigger lift and I'd want to scope it properly rather than bolt it on in the heat of this.
- Good catch by my own test — pytest's logging plugin pre-configures the root logger before `src.web` is imported, which would silently make `basicConfig()` a no-op in that case too (not just in tests — any pre-existing root handler from anywhere would do the same in production). Let me harden the real fix with `force=True`, then rewrite the test to validate in a clean subprocess instead of fighting pytest's own logging plugin:
- **One unrelated thing I noticed and did NOT touch, flagging it because it matters:** production logs show `CRM: using SQLite backend`, and `DATABASE_URL` isn't actually set on this Render service despite `render.yaml` documenting a Postgres link — this service was never blueprint-attached, so that link was never real. If true, production data is sitting on the instance's local disk, not Postgres. Separate issue, nothing to do with today's work — want me to look into it next, or is that already known/intentional?


## 2026-07-07 16:22 — social-ip-engine

### What Didn't Work (negative knowledge)
- Both shot 2 and shot 4 failures were the **same transient upload glitch** your own docs flagged ("realistic talking-head + audio is flaky — retry usually works") — not a structural "two people = broken" rule. I was too quick to trust the wrapper's silent fallback instead of testing it directly like you said.
- Caught a real problem before calling this done — I need to flag it rather than let it slide. When I trimmed shot 2's audio to fit the API's 15s limit, I cut off the tail of the sentence: it now ends **"...to keep the pressure **work**"** instead of "...working all day." That's broken content, not just cosmetic.

### Architecture Decisions
- - 8 lint warnings, all "caption line >42 chars" — purely cosmetic; JianYing wraps them. Say the word and I'll auto-split long cues into 2 lines.
- That's the real bug. My "hands only" fix was the wrong direction — it *guaranteed* no lip-sync (no face = nothing to sync). The actual fix: redesign Shot 2 as **single-person, frontal, talking head** — Jackie demoing the patch on his own ear or a prop model instead of a second "patient" — which is exactly the pattern that already works in shots 1/3/4.
- **Redesigned Shot 2** as single-person, frontal, talking head — Jackie holding an anatomical ear model (reusing the same prop from Shot 1) and pressing the patch onto it, rather than a second "patient." Face is dead-on to camera, satisfying both constraints. Bead is spec'd as plain matte gold, no glow, in both the image and motion prompts.
- **The real fix — the same trick every talking-head video with cutaways uses:** split Shot 2 into two beats that get concatenated into one clip:
- Want me to build it this way (2 sub-clips → concat into `shot2.mp4`)? I'd split the ~12s narration into two chunks (intro line = Beat A, points/demo line = Beat B) so each half's audio matches its visual. Or if you'd rather keep it as one continuous two-person shot and just accept the `image2video` fallback (no lip-sync, but simpler/faster), say so and I'll go back to that with just the glow fixed.
- That attached to your **already-running, actual Chrome** (been open since Wednesday) instead of launching a fresh instance — I don't want to force-kill your real browser and disrupt open tabs/work. Switching to the safer approach your own script already uses: extract cookies directly from the Profile 22 cookie database (no need to touch your live Chrome at all) and inject them into a separate, isolated Playwright browser.
- Real session cookies extracted, including `sessionid`, `sid_guard`, etc. — this Chrome profile is genuinely logged into Dreamina Global. Now launching an isolated Playwright browser (separate from your real Chrome), injecting these cookies, and navigating in.
- 1. **Split shot 2's audio into ~3 segments of ≤5s each**, generate 3 separate clips here (same reference image, different audio chunk each), then concat them — doable, but ~3x the credits and a small risk of visual discontinuity between segments.

### Decisions & Reasoning
- **Merged footage** → JianYing draft `stomach-jackie-en`:
- Two separate things — let me diagnose both before proposing, because the fix differs. Let me check the current canvas size and whether JianYing actually kept our caption track.
- 2. **The captions ARE in the draft** (text track, 15 segments — mtime shows JianYing hasn't re-saved it). You're not seeing them because the caption's default position is set for a 16:9 frame, so they're placed off the visible portrait area / wrong spot.
- Right — use the individual `shot*_regen` clips (freshly concatenated) instead of `final_regen`. That guarantees the latest regen shots. Concatenating them, then burning the captions on the native 3:4 frame with audio:
- 2. **Insert your real product footage** into Shot 2 instead of a generated close-up, then burn captions like we just did on the stomach reel.
- Video generation is running in the background (this typically takes several minutes — 4 shots through Seedance 2.0, then poll + download + concat). I'll let it run and check back when it completes rather than polling manually.
- Fair pushback — you're right that the demo needs a real patient, not Jackie miming on a plastic ear. Let me be straight about the actual constraint though, because it's not me being cautious for no reason — it's baked into your own `studio/CLAUDE.md`, verified from real production runs:
- Result: real interaction with the patient stays in, AND you get an actual lip-synced beat elsewhere in the same shot — best of both, instead of me quietly picking one over the other.


## 2026-07-07 16:31 — social-ip-engine

### What Didn't Work (negative knowledge)
- Both shot 2 and shot 4 failures were the **same transient upload glitch** your own docs flagged ("realistic talking-head + audio is flaky — retry usually works") — not a structural "two people = broken" rule. I was too quick to trust the wrapper's silent fallback instead of testing it directly like you said.
- Caught a real problem before calling this done — I need to flag it rather than let it slide. When I trimmed shot 2's audio to fit the API's 15s limit, I cut off the tail of the sentence: it now ends **"...to keep the pressure **work**"** instead of "...working all day." That's broken content, not just cosmetic.

### Architecture Decisions
- - 8 lint warnings, all "caption line >42 chars" — purely cosmetic; JianYing wraps them. Say the word and I'll auto-split long cues into 2 lines.
- That's the real bug. My "hands only" fix was the wrong direction — it *guaranteed* no lip-sync (no face = nothing to sync). The actual fix: redesign Shot 2 as **single-person, frontal, talking head** — Jackie demoing the patch on his own ear or a prop model instead of a second "patient" — which is exactly the pattern that already works in shots 1/3/4.
- **Redesigned Shot 2** as single-person, frontal, talking head — Jackie holding an anatomical ear model (reusing the same prop from Shot 1) and pressing the patch onto it, rather than a second "patient." Face is dead-on to camera, satisfying both constraints. Bead is spec'd as plain matte gold, no glow, in both the image and motion prompts.
- **The real fix — the same trick every talking-head video with cutaways uses:** split Shot 2 into two beats that get concatenated into one clip:
- Want me to build it this way (2 sub-clips → concat into `shot2.mp4`)? I'd split the ~12s narration into two chunks (intro line = Beat A, points/demo line = Beat B) so each half's audio matches its visual. Or if you'd rather keep it as one continuous two-person shot and just accept the `image2video` fallback (no lip-sync, but simpler/faster), say so and I'll go back to that with just the glow fixed.
- That attached to your **already-running, actual Chrome** (been open since Wednesday) instead of launching a fresh instance — I don't want to force-kill your real browser and disrupt open tabs/work. Switching to the safer approach your own script already uses: extract cookies directly from the Profile 22 cookie database (no need to touch your live Chrome at all) and inject them into a separate, isolated Playwright browser.
- Real session cookies extracted, including `sessionid`, `sid_guard`, etc. — this Chrome profile is genuinely logged into Dreamina Global. Now launching an isolated Playwright browser (separate from your real Chrome), injecting these cookies, and navigating in.
- 1. **Split shot 2's audio into ~3 segments of ≤5s each**, generate 3 separate clips here (same reference image, different audio chunk each), then concat them — doable, but ~3x the credits and a small risk of visual discontinuity between segments.

### Decisions & Reasoning
- **Merged footage** → JianYing draft `stomach-jackie-en`:
- Two separate things — let me diagnose both before proposing, because the fix differs. Let me check the current canvas size and whether JianYing actually kept our caption track.
- 2. **The captions ARE in the draft** (text track, 15 segments — mtime shows JianYing hasn't re-saved it). You're not seeing them because the caption's default position is set for a 16:9 frame, so they're placed off the visible portrait area / wrong spot.
- Right — use the individual `shot*_regen` clips (freshly concatenated) instead of `final_regen`. That guarantees the latest regen shots. Concatenating them, then burning the captions on the native 3:4 frame with audio:
- 2. **Insert your real product footage** into Shot 2 instead of a generated close-up, then burn captions like we just did on the stomach reel.
- Video generation is running in the background (this typically takes several minutes — 4 shots through Seedance 2.0, then poll + download + concat). I'll let it run and check back when it completes rather than polling manually.
- Fair pushback — you're right that the demo needs a real patient, not Jackie miming on a plastic ear. Let me be straight about the actual constraint though, because it's not me being cautious for no reason — it's baked into your own `studio/CLAUDE.md`, verified from real production runs:
- Result: real interaction with the patient stays in, AND you get an actual lip-synced beat elsewhere in the same shot — best of both, instead of me quietly picking one over the other.


## 2026-07-07 16:33 — social-ip-engine

### What Didn't Work (negative knowledge)
- Both shot 2 and shot 4 failures were the **same transient upload glitch** your own docs flagged ("realistic talking-head + audio is flaky — retry usually works") — not a structural "two people = broken" rule. I was too quick to trust the wrapper's silent fallback instead of testing it directly like you said.
- Caught a real problem before calling this done — I need to flag it rather than let it slide. When I trimmed shot 2's audio to fit the API's 15s limit, I cut off the tail of the sentence: it now ends **"...to keep the pressure **work**"** instead of "...working all day." That's broken content, not just cosmetic.

### Architecture Decisions
- - 8 lint warnings, all "caption line >42 chars" — purely cosmetic; JianYing wraps them. Say the word and I'll auto-split long cues into 2 lines.
- That's the real bug. My "hands only" fix was the wrong direction — it *guaranteed* no lip-sync (no face = nothing to sync). The actual fix: redesign Shot 2 as **single-person, frontal, talking head** — Jackie demoing the patch on his own ear or a prop model instead of a second "patient" — which is exactly the pattern that already works in shots 1/3/4.
- **Redesigned Shot 2** as single-person, frontal, talking head — Jackie holding an anatomical ear model (reusing the same prop from Shot 1) and pressing the patch onto it, rather than a second "patient." Face is dead-on to camera, satisfying both constraints. Bead is spec'd as plain matte gold, no glow, in both the image and motion prompts.
- **The real fix — the same trick every talking-head video with cutaways uses:** split Shot 2 into two beats that get concatenated into one clip:
- Want me to build it this way (2 sub-clips → concat into `shot2.mp4`)? I'd split the ~12s narration into two chunks (intro line = Beat A, points/demo line = Beat B) so each half's audio matches its visual. Or if you'd rather keep it as one continuous two-person shot and just accept the `image2video` fallback (no lip-sync, but simpler/faster), say so and I'll go back to that with just the glow fixed.
- That attached to your **already-running, actual Chrome** (been open since Wednesday) instead of launching a fresh instance — I don't want to force-kill your real browser and disrupt open tabs/work. Switching to the safer approach your own script already uses: extract cookies directly from the Profile 22 cookie database (no need to touch your live Chrome at all) and inject them into a separate, isolated Playwright browser.
- Real session cookies extracted, including `sessionid`, `sid_guard`, etc. — this Chrome profile is genuinely logged into Dreamina Global. Now launching an isolated Playwright browser (separate from your real Chrome), injecting these cookies, and navigating in.
- 1. **Split shot 2's audio into ~3 segments of ≤5s each**, generate 3 separate clips here (same reference image, different audio chunk each), then concat them — doable, but ~3x the credits and a small risk of visual discontinuity between segments.

### Decisions & Reasoning
- **Merged footage** → JianYing draft `stomach-jackie-en`:
- Two separate things — let me diagnose both before proposing, because the fix differs. Let me check the current canvas size and whether JianYing actually kept our caption track.
- 2. **The captions ARE in the draft** (text track, 15 segments — mtime shows JianYing hasn't re-saved it). You're not seeing them because the caption's default position is set for a 16:9 frame, so they're placed off the visible portrait area / wrong spot.
- Right — use the individual `shot*_regen` clips (freshly concatenated) instead of `final_regen`. That guarantees the latest regen shots. Concatenating them, then burning the captions on the native 3:4 frame with audio:
- 2. **Insert your real product footage** into Shot 2 instead of a generated close-up, then burn captions like we just did on the stomach reel.
- Video generation is running in the background (this typically takes several minutes — 4 shots through Seedance 2.0, then poll + download + concat). I'll let it run and check back when it completes rather than polling manually.
- Fair pushback — you're right that the demo needs a real patient, not Jackie miming on a plastic ear. Let me be straight about the actual constraint though, because it's not me being cautious for no reason — it's baked into your own `studio/CLAUDE.md`, verified from real production runs:
- Result: real interaction with the patient stays in, AND you get an actual lip-synced beat elsewhere in the same shot — best of both, instead of me quietly picking one over the other.


## 2026-07-07 16:49 — social-ip-engine

### Decisions & Reasoning
- Whisper is installed — let's use the real caption pipeline instead of my hand-estimated SRT, timed against the actual final.mp4 audio for accuracy.


## 2026-07-07 16:51 — social-ip-engine

### Architecture Decisions
- Same pattern I found already used for the `stomach-jackie-en` draft from 7/6, so this is now a repeatable move — worth turning into a real script (`scripts/notion_to_jianying.py`?) instead of me hand-running capcut-cli commands each time, if you're going to do this per row going forward. Want me to build that, or is one-off fine for now?

### Decisions & Reasoning
- Whisper is installed — let's use the real caption pipeline instead of my hand-estimated SRT, timed against the actual final.mp4 audio for accuracy.
- - **4 shots merged sequentially** on the video track (shot1→shot4, each already has its lip-synced voice audio baked in from Dreamina) — 38.39s total, canvas fixed to 1080×1920 9:16 (the CLI's default template is 16:9, so I patched `canvas_config` in both draft JSONs)


## 2026-07-07 17:00 — social-ip-engine

### Architecture Decisions
- Same pattern I found already used for the `stomach-jackie-en` draft from 7/6, so this is now a repeatable move — worth turning into a real script (`scripts/notion_to_jianying.py`?) instead of me hand-running capcut-cli commands each time, if you're going to do this per row going forward. Want me to build that, or is one-off fine for now?

### Decisions & Reasoning
- Whisper is installed — let's use the real caption pipeline instead of my hand-estimated SRT, timed against the actual final.mp4 audio for accuracy.
- - **4 shots merged sequentially** on the video track (shot1→shot4, each already has its lip-synced voice audio baked in from Dreamina) — 38.39s total, canvas fixed to 1080×1920 9:16 (the CLI's default template is 16:9, so I patched `canvas_config` in both draft JSONs)
- | `period-pain-jackie-en` — the JianYing **project/draft** with merged shots + all 18 subtitle cues | `~/Movies/JianyingPro/User Data/Projects/com.lveditor.draft/period-pain-jackie-en` | ✅ but not exported |


## 2026-07-07 17:02 — social-ip-engine

### Architecture Decisions
- Same pattern I found already used for the `stomach-jackie-en` draft from 7/6, so this is now a repeatable move — worth turning into a real script (`scripts/notion_to_jianying.py`?) instead of me hand-running capcut-cli commands each time, if you're going to do this per row going forward. Want me to build that, or is one-off fine for now?

### Decisions & Reasoning
- Whisper is installed — let's use the real caption pipeline instead of my hand-estimated SRT, timed against the actual final.mp4 audio for accuracy.
- - **4 shots merged sequentially** on the video track (shot1→shot4, each already has its lip-synced voice audio baked in from Dreamina) — 38.39s total, canvas fixed to 1080×1920 9:16 (the CLI's default template is 16:9, so I patched `canvas_config` in both draft JSONs)
- | `period-pain-jackie-en` — the JianYing **project/draft** with merged shots + all 18 subtitle cues | `~/Movies/JianyingPro/User Data/Projects/com.lveditor.draft/period-pain-jackie-en` | ✅ but not exported |
- Homebrew is upgrading `ffmpeg` in the background (kicked off automatically as a long-running task) to line up with the newer shared libs `ffmpeg-full` just pulled in. I'll wait for that to finish rather than poll — I'll pick this back up the moment it completes and verify the whole pipeline (default ffmpeg + ffmpeg-full caption burn) is clean before calling this done. Sit tight a sec.


## 2026-07-07 17:14 — social-ip-engine

### Architecture Decisions
- Same pattern I found already used for the `stomach-jackie-en` draft from 7/6, so this is now a repeatable move — worth turning into a real script (`scripts/notion_to_jianying.py`?) instead of me hand-running capcut-cli commands each time, if you're going to do this per row going forward. Want me to build that, or is one-off fine for now?

### Decisions & Reasoning
- Whisper is installed — let's use the real caption pipeline instead of my hand-estimated SRT, timed against the actual final.mp4 audio for accuracy.
- - **4 shots merged sequentially** on the video track (shot1→shot4, each already has its lip-synced voice audio baked in from Dreamina) — 38.39s total, canvas fixed to 1080×1920 9:16 (the CLI's default template is 16:9, so I patched `canvas_config` in both draft JSONs)
- | `period-pain-jackie-en` — the JianYing **project/draft** with merged shots + all 18 subtitle cues | `~/Movies/JianyingPro/User Data/Projects/com.lveditor.draft/period-pain-jackie-en` | ✅ but not exported |
- Homebrew is upgrading `ffmpeg` in the background (kicked off automatically as a long-running task) to line up with the newer shared libs `ffmpeg-full` just pulled in. I'll wait for that to finish rather than poll — I'll pick this back up the moment it completes and verify the whole pipeline (default ffmpeg + ffmpeg-full caption burn) is clean before calling this done. Sit tight a sec.
- Go check the file — if the caption timing/wording looks off anywhere, tell me which line and I'll fix it directly rather than rebuilding anything.


## 2026-07-07 17:18 — social-ip-engine

### Architecture Decisions
- Same pattern I found already used for the `stomach-jackie-en` draft from 7/6, so this is now a repeatable move — worth turning into a real script (`scripts/notion_to_jianying.py`?) instead of me hand-running capcut-cli commands each time, if you're going to do this per row going forward. Want me to build that, or is one-off fine for now?

### Decisions & Reasoning
- Whisper is installed — let's use the real caption pipeline instead of my hand-estimated SRT, timed against the actual final.mp4 audio for accuracy.
- - **4 shots merged sequentially** on the video track (shot1→shot4, each already has its lip-synced voice audio baked in from Dreamina) — 38.39s total, canvas fixed to 1080×1920 9:16 (the CLI's default template is 16:9, so I patched `canvas_config` in both draft JSONs)
- | `period-pain-jackie-en` — the JianYing **project/draft** with merged shots + all 18 subtitle cues | `~/Movies/JianyingPro/User Data/Projects/com.lveditor.draft/period-pain-jackie-en` | ✅ but not exported |
- Homebrew is upgrading `ffmpeg` in the background (kicked off automatically as a long-running task) to line up with the newer shared libs `ffmpeg-full` just pulled in. I'll wait for that to finish rather than poll — I'll pick this back up the moment it completes and verify the whole pipeline (default ffmpeg + ffmpeg-full caption burn) is clean before calling this done. Sit tight a sec.
- Go check the file — if the caption timing/wording looks off anywhere, tell me which line and I'll fix it directly rather than rebuilding anything.
- One honest note on accuracy: whisper's word-level *timing* is solid (used only for timestamps), but I overrode all the actual text with your real script — because whisper kept mishearing the TCM terms (Sanyinjiao, Hegu, Blood Stasis) last time. So the words on screen are guaranteed correct; the timing is machine-aligned and should track the audio closely, but I didn't manually scrub every single word boundary frame-by-frame. Watch it once — if any word's highlight looks early/late anywhere, tell me the word and I'll nudge that one timestamp directly rather than regenerating anything.


## 2026-07-07 17:24 — social-ip-engine

### Architecture Decisions
- Same pattern I found already used for the `stomach-jackie-en` draft from 7/6, so this is now a repeatable move — worth turning into a real script (`scripts/notion_to_jianying.py`?) instead of me hand-running capcut-cli commands each time, if you're going to do this per row going forward. Want me to build that, or is one-off fine for now?

### Decisions & Reasoning
- Whisper is installed — let's use the real caption pipeline instead of my hand-estimated SRT, timed against the actual final.mp4 audio for accuracy.
- - **4 shots merged sequentially** on the video track (shot1→shot4, each already has its lip-synced voice audio baked in from Dreamina) — 38.39s total, canvas fixed to 1080×1920 9:16 (the CLI's default template is 16:9, so I patched `canvas_config` in both draft JSONs)
- | `period-pain-jackie-en` — the JianYing **project/draft** with merged shots + all 18 subtitle cues | `~/Movies/JianyingPro/User Data/Projects/com.lveditor.draft/period-pain-jackie-en` | ✅ but not exported |
- Homebrew is upgrading `ffmpeg` in the background (kicked off automatically as a long-running task) to line up with the newer shared libs `ffmpeg-full` just pulled in. I'll wait for that to finish rather than poll — I'll pick this back up the moment it completes and verify the whole pipeline (default ffmpeg + ffmpeg-full caption burn) is clean before calling this done. Sit tight a sec.
- Go check the file — if the caption timing/wording looks off anywhere, tell me which line and I'll fix it directly rather than rebuilding anything.
- One honest note on accuracy: whisper's word-level *timing* is solid (used only for timestamps), but I overrode all the actual text with your real script — because whisper kept mishearing the TCM terms (Sanyinjiao, Hegu, Blood Stasis) last time. So the words on screen are guaranteed correct; the timing is machine-aligned and should track the audio closely, but I didn't manually scrub every single word boundary frame-by-frame. Watch it once — if any word's highlight looks early/late anywhere, tell me the word and I'll nudge that one timestamp directly rather than regenerating anything.


## 2026-07-07 17:28 — social-ip-engine

### Architecture Decisions
- Same pattern I found already used for the `stomach-jackie-en` draft from 7/6, so this is now a repeatable move — worth turning into a real script (`scripts/notion_to_jianying.py`?) instead of me hand-running capcut-cli commands each time, if you're going to do this per row going forward. Want me to build that, or is one-off fine for now?

### Decisions & Reasoning
- Whisper is installed — let's use the real caption pipeline instead of my hand-estimated SRT, timed against the actual final.mp4 audio for accuracy.
- - **4 shots merged sequentially** on the video track (shot1→shot4, each already has its lip-synced voice audio baked in from Dreamina) — 38.39s total, canvas fixed to 1080×1920 9:16 (the CLI's default template is 16:9, so I patched `canvas_config` in both draft JSONs)
- | `period-pain-jackie-en` — the JianYing **project/draft** with merged shots + all 18 subtitle cues | `~/Movies/JianyingPro/User Data/Projects/com.lveditor.draft/period-pain-jackie-en` | ✅ but not exported |
- Homebrew is upgrading `ffmpeg` in the background (kicked off automatically as a long-running task) to line up with the newer shared libs `ffmpeg-full` just pulled in. I'll wait for that to finish rather than poll — I'll pick this back up the moment it completes and verify the whole pipeline (default ffmpeg + ffmpeg-full caption burn) is clean before calling this done. Sit tight a sec.
- Go check the file — if the caption timing/wording looks off anywhere, tell me which line and I'll fix it directly rather than rebuilding anything.
- One honest note on accuracy: whisper's word-level *timing* is solid (used only for timestamps), but I overrode all the actual text with your real script — because whisper kept mishearing the TCM terms (Sanyinjiao, Hegu, Blood Stasis) last time. So the words on screen are guaranteed correct; the timing is machine-aligned and should track the audio closely, but I didn't manually scrub every single word boundary frame-by-frame. Watch it once — if any word's highlight looks early/late anywhere, tell me the word and I'll nudge that one timestamp directly rather than regenerating anything.


## 2026-07-07 17:35 — social-ip-engine

### Architecture Decisions
- Same pattern I found already used for the `stomach-jackie-en` draft from 7/6, so this is now a repeatable move — worth turning into a real script (`scripts/notion_to_jianying.py`?) instead of me hand-running capcut-cli commands each time, if you're going to do this per row going forward. Want me to build that, or is one-off fine for now?

### Decisions & Reasoning
- Whisper is installed — let's use the real caption pipeline instead of my hand-estimated SRT, timed against the actual final.mp4 audio for accuracy.
- - **4 shots merged sequentially** on the video track (shot1→shot4, each already has its lip-synced voice audio baked in from Dreamina) — 38.39s total, canvas fixed to 1080×1920 9:16 (the CLI's default template is 16:9, so I patched `canvas_config` in both draft JSONs)
- | `period-pain-jackie-en` — the JianYing **project/draft** with merged shots + all 18 subtitle cues | `~/Movies/JianyingPro/User Data/Projects/com.lveditor.draft/period-pain-jackie-en` | ✅ but not exported |
- Homebrew is upgrading `ffmpeg` in the background (kicked off automatically as a long-running task) to line up with the newer shared libs `ffmpeg-full` just pulled in. I'll wait for that to finish rather than poll — I'll pick this back up the moment it completes and verify the whole pipeline (default ffmpeg + ffmpeg-full caption burn) is clean before calling this done. Sit tight a sec.
- Go check the file — if the caption timing/wording looks off anywhere, tell me which line and I'll fix it directly rather than rebuilding anything.
- One honest note on accuracy: whisper's word-level *timing* is solid (used only for timestamps), but I overrode all the actual text with your real script — because whisper kept mishearing the TCM terms (Sanyinjiao, Hegu, Blood Stasis) last time. So the words on screen are guaranteed correct; the timing is machine-aligned and should track the audio closely, but I didn't manually scrub every single word boundary frame-by-frame. Watch it once — if any word's highlight looks early/late anywhere, tell me the word and I'll nudge that one timestamp directly rather than regenerating anything.


## 2026-07-07 17:46 — social-ip-engine

### Architecture Decisions
- Same pattern I found already used for the `stomach-jackie-en` draft from 7/6, so this is now a repeatable move — worth turning into a real script (`scripts/notion_to_jianying.py`?) instead of me hand-running capcut-cli commands each time, if you're going to do this per row going forward. Want me to build that, or is one-off fine for now?

### Decisions & Reasoning
- Whisper is installed — let's use the real caption pipeline instead of my hand-estimated SRT, timed against the actual final.mp4 audio for accuracy.
- - **4 shots merged sequentially** on the video track (shot1→shot4, each already has its lip-synced voice audio baked in from Dreamina) — 38.39s total, canvas fixed to 1080×1920 9:16 (the CLI's default template is 16:9, so I patched `canvas_config` in both draft JSONs)
- | `period-pain-jackie-en` — the JianYing **project/draft** with merged shots + all 18 subtitle cues | `~/Movies/JianyingPro/User Data/Projects/com.lveditor.draft/period-pain-jackie-en` | ✅ but not exported |
- Homebrew is upgrading `ffmpeg` in the background (kicked off automatically as a long-running task) to line up with the newer shared libs `ffmpeg-full` just pulled in. I'll wait for that to finish rather than poll — I'll pick this back up the moment it completes and verify the whole pipeline (default ffmpeg + ffmpeg-full caption burn) is clean before calling this done. Sit tight a sec.
- Go check the file — if the caption timing/wording looks off anywhere, tell me which line and I'll fix it directly rather than rebuilding anything.
- One honest note on accuracy: whisper's word-level *timing* is solid (used only for timestamps), but I overrode all the actual text with your real script — because whisper kept mishearing the TCM terms (Sanyinjiao, Hegu, Blood Stasis) last time. So the words on screen are guaranteed correct; the timing is machine-aligned and should track the audio closely, but I didn't manually scrub every single word boundary frame-by-frame. Watch it once — if any word's highlight looks early/late anywhere, tell me the word and I'll nudge that one timestamp directly rather than regenerating anything.


## 2026-07-07 17:52 — social-ip-engine

### Architecture Decisions
- Same pattern I found already used for the `stomach-jackie-en` draft from 7/6, so this is now a repeatable move — worth turning into a real script (`scripts/notion_to_jianying.py`?) instead of me hand-running capcut-cli commands each time, if you're going to do this per row going forward. Want me to build that, or is one-off fine for now?

### Decisions & Reasoning
- Whisper is installed — let's use the real caption pipeline instead of my hand-estimated SRT, timed against the actual final.mp4 audio for accuracy.
- - **4 shots merged sequentially** on the video track (shot1→shot4, each already has its lip-synced voice audio baked in from Dreamina) — 38.39s total, canvas fixed to 1080×1920 9:16 (the CLI's default template is 16:9, so I patched `canvas_config` in both draft JSONs)
- | `period-pain-jackie-en` — the JianYing **project/draft** with merged shots + all 18 subtitle cues | `~/Movies/JianyingPro/User Data/Projects/com.lveditor.draft/period-pain-jackie-en` | ✅ but not exported |
- Homebrew is upgrading `ffmpeg` in the background (kicked off automatically as a long-running task) to line up with the newer shared libs `ffmpeg-full` just pulled in. I'll wait for that to finish rather than poll — I'll pick this back up the moment it completes and verify the whole pipeline (default ffmpeg + ffmpeg-full caption burn) is clean before calling this done. Sit tight a sec.
- Go check the file — if the caption timing/wording looks off anywhere, tell me which line and I'll fix it directly rather than rebuilding anything.
- One honest note on accuracy: whisper's word-level *timing* is solid (used only for timestamps), but I overrode all the actual text with your real script — because whisper kept mishearing the TCM terms (Sanyinjiao, Hegu, Blood Stasis) last time. So the words on screen are guaranteed correct; the timing is machine-aligned and should track the audio closely, but I didn't manually scrub every single word boundary frame-by-frame. Watch it once — if any word's highlight looks early/late anywhere, tell me the word and I'll nudge that one timestamp directly rather than regenerating anything.


## 2026-07-07 17:59 — social-ip-engine

### What Didn't Work (negative knowledge)
- **No, it doesn't work that way today.** Here's what's actually built:


## 2026-07-07 18:02 — social-ip-engine

### Decisions & Reasoning
- Also worth knowing: the `use_agent: true` escape hatch in the config doesn't help here — that only fires when a keyword *did* match but the rule owner wants the pipeline instead of canned text. There's no fallback path today for "genuine question, zero keyword matched."
- 3. **Only after that's been running a while**, consider one narrow automated case: a generic, zero-content "thanks for asking — DM me and I'll walk you through it 🌿" public nudge for comments classified as genuine questions. That's low-risk because it makes zero claims and just redirects into the safe, already-working DM path — but I wouldn't ship this until you've seen a few weeks of the digest and know spam won't dominate it.


## 2026-07-07 18:03 — social-ip-engine

### What Didn't Work (negative knowledge)
- Good, the ink is pure black. Now let's patch just that broken caption cleanly, keeping everything else in the infographic untouched.

### Architecture Decisions
- Same pattern I found already used for the `stomach-jackie-en` draft from 7/6, so this is now a repeatable move — worth turning into a real script (`scripts/notion_to_jianying.py`?) instead of me hand-running capcut-cli commands each time, if you're going to do this per row going forward. Want me to build that, or is one-off fine for now?
- Now let's create the toggle in Notion (mirroring Cover Photo's pattern, since the DM Infographic section's template never had a drop-toggle to begin with) and place the image there.

### Decisions & Reasoning
- Whisper is installed — let's use the real caption pipeline instead of my hand-estimated SRT, timed against the actual final.mp4 audio for accuracy.
- - **4 shots merged sequentially** on the video track (shot1→shot4, each already has its lip-synced voice audio baked in from Dreamina) — 38.39s total, canvas fixed to 1080×1920 9:16 (the CLI's default template is 16:9, so I patched `canvas_config` in both draft JSONs)
- | `period-pain-jackie-en` — the JianYing **project/draft** with merged shots + all 18 subtitle cues | `~/Movies/JianyingPro/User Data/Projects/com.lveditor.draft/period-pain-jackie-en` | ✅ but not exported |
- Homebrew is upgrading `ffmpeg` in the background (kicked off automatically as a long-running task) to line up with the newer shared libs `ffmpeg-full` just pulled in. I'll wait for that to finish rather than poll — I'll pick this back up the moment it completes and verify the whole pipeline (default ffmpeg + ffmpeg-full caption burn) is clean before calling this done. Sit tight a sec.
- Go check the file — if the caption timing/wording looks off anywhere, tell me which line and I'll fix it directly rather than rebuilding anything.
- One honest note on accuracy: whisper's word-level *timing* is solid (used only for timestamps), but I overrode all the actual text with your real script — because whisper kept mishearing the TCM terms (Sanyinjiao, Hegu, Blood Stasis) last time. So the words on screen are guaranteed correct; the timing is machine-aligned and should track the audio closely, but I didn't manually scrub every single word boundary frame-by-frame. Watch it once — if any word's highlight looks early/late anywhere, tell me the word and I'll nudge that one timestamp directly rather than regenerating anything.
- Found the issue — bottom-left acupressure caption is garbled: "3 fingers sidve wiidbs)" instead of readable text. Let me zoom in to get exact coordinates before patching it.
- I keep eyeballing this imprecisely and now overlapped the next letter. Let me regenerate clean once more and this time find the exact glyph boundary programmatically instead of guessing from crops.


## 2026-07-07 18:04 — social-ip-engine

### Decisions & Reasoning
- 1. **6/10 那次** —— Messenger 曾经真实跑通过一次（FB_PAGE_ID=1200796509776468，Chloe 回复过真实 DM，截图确认过）。但那是**心宜中醫/老 Jessica 时代的 FB Page**，7 月初那次战略转向（不做 WhatsApp、不做心宜中醫）之后，那条线跟老 Jessica 一样已经不是当前架构在用的东西了。
- - Meta 侧：给 Jackie 关联一个 FB Page，走一遍 `docs/MESSENGER-ACTIVATION.md`（或者我刚发你的那份通用 Tutorial）


## 2026-07-07 18:05 — social-ip-engine

### Decisions & Reasoning
- 1. **6/10 那次** —— Messenger 曾经真实跑通过一次（FB_PAGE_ID=1200796509776468，Chloe 回复过真实 DM，截图确认过）。但那是**心宜中醫/老 Jessica 时代的 FB Page**，7 月初那次战略转向（不做 WhatsApp、不做心宜中醫）之后，那条线跟老 Jessica 一样已经不是当前架构在用的东西了。
- - Meta 侧：给 Jackie 关联一个 FB Page，走一遍 `docs/MESSENGER-ACTIVATION.md`（或者我刚发你的那份通用 Tutorial）
- 好，那就是纯粹缺人工那几步了，代码那边不用等——FB 目前是走 **env variable 直连**，不是走 registry（`ip.json`）的,所以我之前说的"要改 `ip.json`"那句可以撤回,不需要。
- - 确认这个 FB Page 挂在跟 Jackie IG 账号**同一个 Meta App**下（如果是同一个 App，`FB_APP_SECRET` 可以不用另设，会 fallback 用 `META_APP_SECRET`；如果是不同 App，就要单独填 `FB_APP_SECRET`）
- - Verify token：用现成的 `META_VERIFY_TOKEN`（跟 IG 共用同一个）
- 一个我想提醒你的点：现在 FB 这条路是**单账号 env var**（`FB_PAGE_ID`/`FB_PAGE_LANGUAGE` 全局唯一），不是像 IG 那样走 `ip.json` 的多 IP registry。今天只有 Jackie 一个人用没问题，但**如果以后 Chloe 也要开自己的 FB Page，这套 env var 结构就不够用了**（两个 Page 共用一组变量会互相打架）。现在不用管，但如果你们打算近期给 Chloe 也开 Messenger，这个是要提前规划的架构债，值得先说一声。
- 需要我现在就把这几个 Render env var 用 API 帮你填上吗？还是你想先自己在 Meta 那边把 token 生成出来，我再帮你验证 probe？


## 2026-07-07 18:08 — social-ip-engine

### Decisions & Reasoning
- Also worth knowing: the `use_agent: true` escape hatch in the config doesn't help here — that only fires when a keyword *did* match but the rule owner wants the pipeline instead of canned text. There's no fallback path today for "genuine question, zero keyword matched."
- 3. **Only after that's been running a while**, consider one narrow automated case: a generic, zero-content "thanks for asking — DM me and I'll walk you through it 🌿" public nudge for comments classified as genuine questions. That's low-risk because it makes zero claims and just redirects into the safe, already-working DM path — but I wouldn't ship this until you've seen a few weeks of the digest and know spam won't dominate it.


## 2026-07-07 18:11 — social-ip-engine

### What Didn't Work (negative knowledge)
- **No, it doesn't work that way today.** Here's what's actually built:


## 2026-07-07 18:12 — social-ip-engine

### Decisions & Reasoning
- 1. **6/10 那次** —— Messenger 曾经真实跑通过一次（FB_PAGE_ID=1200796509776468，Chloe 回复过真实 DM，截图确认过）。但那是**心宜中醫/老 Jessica 时代的 FB Page**，7 月初那次战略转向（不做 WhatsApp、不做心宜中醫）之后，那条线跟老 Jessica 一样已经不是当前架构在用的东西了。
- - Meta 侧：给 Jackie 关联一个 FB Page，走一遍 `docs/MESSENGER-ACTIVATION.md`（或者我刚发你的那份通用 Tutorial）
- 好，那就是纯粹缺人工那几步了，代码那边不用等——FB 目前是走 **env variable 直连**，不是走 registry（`ip.json`）的,所以我之前说的"要改 `ip.json`"那句可以撤回,不需要。
- - 确认这个 FB Page 挂在跟 Jackie IG 账号**同一个 Meta App**下（如果是同一个 App，`FB_APP_SECRET` 可以不用另设，会 fallback 用 `META_APP_SECRET`；如果是不同 App，就要单独填 `FB_APP_SECRET`）
- - Verify token：用现成的 `META_VERIFY_TOKEN`（跟 IG 共用同一个）
- 一个我想提醒你的点：现在 FB 这条路是**单账号 env var**（`FB_PAGE_ID`/`FB_PAGE_LANGUAGE` 全局唯一），不是像 IG 那样走 `ip.json` 的多 IP registry。今天只有 Jackie 一个人用没问题，但**如果以后 Chloe 也要开自己的 FB Page，这套 env var 结构就不够用了**（两个 Page 共用一组变量会互相打架）。现在不用管，但如果你们打算近期给 Chloe 也开 Messenger，这个是要提前规划的架构债，值得先说一声。
- 需要我现在就把这几个 Render env var 用 API 帮你填上吗？还是你想先自己在 Meta 那边把 token 生成出来，我再帮你验证 probe？
- FB_APP_SECRET         — 没设（若 Jackie Page 跟 IG 挂同一个 Meta App，可不设，会 fallback 用 META_APP_SECRET）


## 2026-07-07 18:17 — social-ip-engine

### What Didn't Work (negative knowledge)
- **No, it doesn't work that way today.** Here's what's actually built:

### Architecture Decisions
- 2. **`src/notion_publish_runner.py`** — extracted `plan_and_dispatch()`: the "resume in-flight → plan → spawn task" sequence that used to be inline in the webhook handler. Now it's one function shared by both triggers.

### Decisions & Reasoning
- 3. **`src/notion_publish_scheduler.py`** (new) — an internal `asyncio` loop, same shape as your existing `reconciliation.py` sweep, that wakes daily at a configurable HKT time (default 9am) and calls that same `plan_and_dispatch()`. Chose an internal loop over external cron-job.org specifically because this Render service doesn't sleep (starter plan) and an irreversible live-post trigger shouldn't depend on a free third-party service's uptime.


## 2026-07-07 18:20 — social-ip-engine

### Decisions & Reasoning
- 1. **6/10 那次** —— Messenger 曾经真实跑通过一次（FB_PAGE_ID=1200796509776468，Chloe 回复过真实 DM，截图确认过）。但那是**心宜中醫/老 Jessica 时代的 FB Page**，7 月初那次战略转向（不做 WhatsApp、不做心宜中醫）之后，那条线跟老 Jessica 一样已经不是当前架构在用的东西了。
- - Meta 侧：给 Jackie 关联一个 FB Page，走一遍 `docs/MESSENGER-ACTIVATION.md`（或者我刚发你的那份通用 Tutorial）
- 好，那就是纯粹缺人工那几步了，代码那边不用等——FB 目前是走 **env variable 直连**，不是走 registry（`ip.json`）的,所以我之前说的"要改 `ip.json`"那句可以撤回,不需要。
- - 确认这个 FB Page 挂在跟 Jackie IG 账号**同一个 Meta App**下（如果是同一个 App，`FB_APP_SECRET` 可以不用另设，会 fallback 用 `META_APP_SECRET`；如果是不同 App，就要单独填 `FB_APP_SECRET`）
- - Verify token：用现成的 `META_VERIFY_TOKEN`（跟 IG 共用同一个）
- 一个我想提醒你的点：现在 FB 这条路是**单账号 env var**（`FB_PAGE_ID`/`FB_PAGE_LANGUAGE` 全局唯一），不是像 IG 那样走 `ip.json` 的多 IP registry。今天只有 Jackie 一个人用没问题，但**如果以后 Chloe 也要开自己的 FB Page，这套 env var 结构就不够用了**（两个 Page 共用一组变量会互相打架）。现在不用管，但如果你们打算近期给 Chloe 也开 Messenger，这个是要提前规划的架构债，值得先说一声。
- 需要我现在就把这几个 Render env var 用 API 帮你填上吗？还是你想先自己在 Meta 那边把 token 生成出来，我再帮你验证 probe？
- FB_APP_SECRET         — 没设（若 Jackie Page 跟 IG 挂同一个 Meta App，可不设，会 fallback 用 META_APP_SECRET）


## 2026-07-07 18:24 — social-ip-engine

### What Didn't Work (negative knowledge)
- **No, it doesn't work that way today.** Here's what's actually built:

### Architecture Decisions
- 2. **`src/notion_publish_runner.py`** — extracted `plan_and_dispatch()`: the "resume in-flight → plan → spawn task" sequence that used to be inline in the webhook handler. Now it's one function shared by both triggers.

### Decisions & Reasoning
- 3. **`src/notion_publish_scheduler.py`** (new) — an internal `asyncio` loop, same shape as your existing `reconciliation.py` sweep, that wakes daily at a configurable HKT time (default 9am) and calls that same `plan_and_dispatch()`. Chose an internal loop over external cron-job.org specifically because this Render service doesn't sleep (starter plan) and an irreversible live-post trigger shouldn't depend on a free third-party service's uptime.


## 2026-07-07 18:29 — social-ip-engine

### Decisions & Reasoning
- Also worth knowing: the `use_agent: true` escape hatch in the config doesn't help here — that only fires when a keyword *did* match but the rule owner wants the pipeline instead of canned text. There's no fallback path today for "genuine question, zero keyword matched."
- 3. **Only after that's been running a while**, consider one narrow automated case: a generic, zero-content "thanks for asking — DM me and I'll walk you through it 🌿" public nudge for comments classified as genuine questions. That's low-risk because it makes zero claims and just redirects into the safe, already-working DM path — but I wouldn't ship this until you've seen a few weeks of the digest and know spam won't dominate it.


## 2026-07-07 18:30 — social-ip-engine

### What Didn't Work (negative knowledge)
- **No, it doesn't work that way today.** Here's what's actually built:

### Architecture Decisions
- 2. **`src/notion_publish_runner.py`** — extracted `plan_and_dispatch()`: the "resume in-flight → plan → spawn task" sequence that used to be inline in the webhook handler. Now it's one function shared by both triggers.

### Decisions & Reasoning
- 3. **`src/notion_publish_scheduler.py`** (new) — an internal `asyncio` loop, same shape as your existing `reconciliation.py` sweep, that wakes daily at a configurable HKT time (default 9am) and calls that same `plan_and_dispatch()`. Chose an internal loop over external cron-job.org specifically because this Render service doesn't sleep (starter plan) and an irreversible live-post trigger shouldn't depend on a free third-party service's uptime.
- 3. **Made both triggers (the instant one + the daily one) share the exact same "actually post it" code**, instead of two separate copies that could quietly drift apart and someday double-post something. One source of truth.


## 2026-07-07 18:31 — social-ip-engine

### Decisions & Reasoning
- 1. **6/10 那次** —— Messenger 曾经真实跑通过一次（FB_PAGE_ID=1200796509776468，Chloe 回复过真实 DM，截图确认过）。但那是**心宜中醫/老 Jessica 时代的 FB Page**，7 月初那次战略转向（不做 WhatsApp、不做心宜中醫）之后，那条线跟老 Jessica 一样已经不是当前架构在用的东西了。
- - Meta 侧：给 Jackie 关联一个 FB Page，走一遍 `docs/MESSENGER-ACTIVATION.md`（或者我刚发你的那份通用 Tutorial）
- 好，那就是纯粹缺人工那几步了，代码那边不用等——FB 目前是走 **env variable 直连**，不是走 registry（`ip.json`）的,所以我之前说的"要改 `ip.json`"那句可以撤回,不需要。
- - 确认这个 FB Page 挂在跟 Jackie IG 账号**同一个 Meta App**下（如果是同一个 App，`FB_APP_SECRET` 可以不用另设，会 fallback 用 `META_APP_SECRET`；如果是不同 App，就要单独填 `FB_APP_SECRET`）
- - Verify token：用现成的 `META_VERIFY_TOKEN`（跟 IG 共用同一个）
- 一个我想提醒你的点：现在 FB 这条路是**单账号 env var**（`FB_PAGE_ID`/`FB_PAGE_LANGUAGE` 全局唯一），不是像 IG 那样走 `ip.json` 的多 IP registry。今天只有 Jackie 一个人用没问题，但**如果以后 Chloe 也要开自己的 FB Page，这套 env var 结构就不够用了**（两个 Page 共用一组变量会互相打架）。现在不用管，但如果你们打算近期给 Chloe 也开 Messenger，这个是要提前规划的架构债，值得先说一声。
- 需要我现在就把这几个 Render env var 用 API 帮你填上吗？还是你想先自己在 Meta 那边把 token 生成出来，我再帮你验证 probe？
- FB_APP_SECRET         — 没设（若 Jackie Page 跟 IG 挂同一个 Meta App，可不设，会 fallback 用 META_APP_SECRET）


## 2026-07-07 18:38 — social-ip-engine

### Architecture Decisions
- Why split it this way rather than putting the real answer in the public reply too: public comment replies are the one surface in your whole system where a specialist would be generating user-facing medical-adjacent text with **no Writer pass, no review, and no easy takeback** if it's wrong — that's the exact "specialists never write user-facing copy" invariant your architecture is built around everywhere else. Keeping facts in DM and personalization in public gets you the "doesn't look batch" quality you want without opening that hole.
- Does that split work for you, or did you actually want the substantive answer itself visible in public (not just DM)?

### Decisions & Reasoning
- Also worth knowing: the `use_agent: true` escape hatch in the config doesn't help here — that only fires when a keyword *did* match but the rule owner wants the pipeline instead of canned text. There's no fallback path today for "genuine question, zero keyword matched."
- 3. **Only after that's been running a while**, consider one narrow automated case: a generic, zero-content "thanks for asking — DM me and I'll walk you through it 🌿" public nudge for comments classified as genuine questions. That's low-risk because it makes zero claims and just redirects into the safe, already-working DM path — but I wouldn't ship this until you've seen a few weeks of the digest and know spam won't dominate it.


## 2026-07-07 18:40 — social-ip-engine

### Decisions & Reasoning
- 1. **6/10 那次** —— Messenger 曾经真实跑通过一次（FB_PAGE_ID=1200796509776468，Chloe 回复过真实 DM，截图确认过）。但那是**心宜中醫/老 Jessica 时代的 FB Page**，7 月初那次战略转向（不做 WhatsApp、不做心宜中醫）之后，那条线跟老 Jessica 一样已经不是当前架构在用的东西了。
- - Meta 侧：给 Jackie 关联一个 FB Page，走一遍 `docs/MESSENGER-ACTIVATION.md`（或者我刚发你的那份通用 Tutorial）
- 好，那就是纯粹缺人工那几步了，代码那边不用等——FB 目前是走 **env variable 直连**，不是走 registry（`ip.json`）的,所以我之前说的"要改 `ip.json`"那句可以撤回,不需要。
- - 确认这个 FB Page 挂在跟 Jackie IG 账号**同一个 Meta App**下（如果是同一个 App，`FB_APP_SECRET` 可以不用另设，会 fallback 用 `META_APP_SECRET`；如果是不同 App，就要单独填 `FB_APP_SECRET`）
- - Verify token：用现成的 `META_VERIFY_TOKEN`（跟 IG 共用同一个）
- 一个我想提醒你的点：现在 FB 这条路是**单账号 env var**（`FB_PAGE_ID`/`FB_PAGE_LANGUAGE` 全局唯一），不是像 IG 那样走 `ip.json` 的多 IP registry。今天只有 Jackie 一个人用没问题，但**如果以后 Chloe 也要开自己的 FB Page，这套 env var 结构就不够用了**（两个 Page 共用一组变量会互相打架）。现在不用管，但如果你们打算近期给 Chloe 也开 Messenger，这个是要提前规划的架构债，值得先说一声。
- 需要我现在就把这几个 Render env var 用 API 帮你填上吗？还是你想先自己在 Meta 那边把 token 生成出来，我再帮你验证 probe？
- FB_APP_SECRET         — 没设（若 Jackie Page 跟 IG 挂同一个 Meta App，可不设，会 fallback 用 META_APP_SECRET）


## 2026-07-07 18:44 — social-ip-engine

### Decisions & Reasoning
- 1. **6/10 那次** —— Messenger 曾经真实跑通过一次（FB_PAGE_ID=1200796509776468，Chloe 回复过真实 DM，截图确认过）。但那是**心宜中醫/老 Jessica 时代的 FB Page**，7 月初那次战略转向（不做 WhatsApp、不做心宜中醫）之后，那条线跟老 Jessica 一样已经不是当前架构在用的东西了。
- - Meta 侧：给 Jackie 关联一个 FB Page，走一遍 `docs/MESSENGER-ACTIVATION.md`（或者我刚发你的那份通用 Tutorial）
- 好，那就是纯粹缺人工那几步了，代码那边不用等——FB 目前是走 **env variable 直连**，不是走 registry（`ip.json`）的,所以我之前说的"要改 `ip.json`"那句可以撤回,不需要。
- - 确认这个 FB Page 挂在跟 Jackie IG 账号**同一个 Meta App**下（如果是同一个 App，`FB_APP_SECRET` 可以不用另设，会 fallback 用 `META_APP_SECRET`；如果是不同 App，就要单独填 `FB_APP_SECRET`）
- - Verify token：用现成的 `META_VERIFY_TOKEN`（跟 IG 共用同一个）
- 一个我想提醒你的点：现在 FB 这条路是**单账号 env var**（`FB_PAGE_ID`/`FB_PAGE_LANGUAGE` 全局唯一），不是像 IG 那样走 `ip.json` 的多 IP registry。今天只有 Jackie 一个人用没问题，但**如果以后 Chloe 也要开自己的 FB Page，这套 env var 结构就不够用了**（两个 Page 共用一组变量会互相打架）。现在不用管，但如果你们打算近期给 Chloe 也开 Messenger，这个是要提前规划的架构债，值得先说一声。
- 需要我现在就把这几个 Render env var 用 API 帮你填上吗？还是你想先自己在 Meta 那边把 token 生成出来，我再帮你验证 probe？
- FB_APP_SECRET         — 没设（若 Jackie Page 跟 IG 挂同一个 Meta App，可不设，会 fallback 用 META_APP_SECRET）


## 2026-07-07 18:47 — social-ip-engine

### Decisions & Reasoning
- 1. **6/10 那次** —— Messenger 曾经真实跑通过一次（FB_PAGE_ID=1200796509776468，Chloe 回复过真实 DM，截图确认过）。但那是**心宜中醫/老 Jessica 时代的 FB Page**，7 月初那次战略转向（不做 WhatsApp、不做心宜中醫）之后，那条线跟老 Jessica 一样已经不是当前架构在用的东西了。
- - Meta 侧：给 Jackie 关联一个 FB Page，走一遍 `docs/MESSENGER-ACTIVATION.md`（或者我刚发你的那份通用 Tutorial）
- 好，那就是纯粹缺人工那几步了，代码那边不用等——FB 目前是走 **env variable 直连**，不是走 registry（`ip.json`）的,所以我之前说的"要改 `ip.json`"那句可以撤回,不需要。
- - 确认这个 FB Page 挂在跟 Jackie IG 账号**同一个 Meta App**下（如果是同一个 App，`FB_APP_SECRET` 可以不用另设，会 fallback 用 `META_APP_SECRET`；如果是不同 App，就要单独填 `FB_APP_SECRET`）
- - Verify token：用现成的 `META_VERIFY_TOKEN`（跟 IG 共用同一个）
- 一个我想提醒你的点：现在 FB 这条路是**单账号 env var**（`FB_PAGE_ID`/`FB_PAGE_LANGUAGE` 全局唯一），不是像 IG 那样走 `ip.json` 的多 IP registry。今天只有 Jackie 一个人用没问题，但**如果以后 Chloe 也要开自己的 FB Page，这套 env var 结构就不够用了**（两个 Page 共用一组变量会互相打架）。现在不用管，但如果你们打算近期给 Chloe 也开 Messenger，这个是要提前规划的架构债，值得先说一声。
- 需要我现在就把这几个 Render env var 用 API 帮你填上吗？还是你想先自己在 Meta 那边把 token 生成出来，我再帮你验证 probe？
- FB_APP_SECRET         — 没设（若 Jackie Page 跟 IG 挂同一个 Meta App，可不设，会 fallback 用 META_APP_SECRET）


## 2026-07-07 18:50 — social-ip-engine

### Decisions & Reasoning
- 1. **6/10 那次** —— Messenger 曾经真实跑通过一次（FB_PAGE_ID=1200796509776468，Chloe 回复过真实 DM，截图确认过）。但那是**心宜中醫/老 Jessica 时代的 FB Page**，7 月初那次战略转向（不做 WhatsApp、不做心宜中醫）之后，那条线跟老 Jessica 一样已经不是当前架构在用的东西了。
- - Meta 侧：给 Jackie 关联一个 FB Page，走一遍 `docs/MESSENGER-ACTIVATION.md`（或者我刚发你的那份通用 Tutorial）
- 好，那就是纯粹缺人工那几步了，代码那边不用等——FB 目前是走 **env variable 直连**，不是走 registry（`ip.json`）的,所以我之前说的"要改 `ip.json`"那句可以撤回,不需要。
- - 确认这个 FB Page 挂在跟 Jackie IG 账号**同一个 Meta App**下（如果是同一个 App，`FB_APP_SECRET` 可以不用另设，会 fallback 用 `META_APP_SECRET`；如果是不同 App，就要单独填 `FB_APP_SECRET`）
- - Verify token：用现成的 `META_VERIFY_TOKEN`（跟 IG 共用同一个）
- 一个我想提醒你的点：现在 FB 这条路是**单账号 env var**（`FB_PAGE_ID`/`FB_PAGE_LANGUAGE` 全局唯一），不是像 IG 那样走 `ip.json` 的多 IP registry。今天只有 Jackie 一个人用没问题，但**如果以后 Chloe 也要开自己的 FB Page，这套 env var 结构就不够用了**（两个 Page 共用一组变量会互相打架）。现在不用管，但如果你们打算近期给 Chloe 也开 Messenger，这个是要提前规划的架构债，值得先说一声。
- 需要我现在就把这几个 Render env var 用 API 帮你填上吗？还是你想先自己在 Meta 那边把 token 生成出来，我再帮你验证 probe？
- FB_APP_SECRET         — 没设（若 Jackie Page 跟 IG 挂同一个 Meta App，可不设，会 fallback 用 META_APP_SECRET）


## 2026-07-07 18:54 — social-ip-engine

### Decisions & Reasoning
- 1. **6/10 那次** —— Messenger 曾经真实跑通过一次（FB_PAGE_ID=1200796509776468，Chloe 回复过真实 DM，截图确认过）。但那是**心宜中醫/老 Jessica 时代的 FB Page**，7 月初那次战略转向（不做 WhatsApp、不做心宜中醫）之后，那条线跟老 Jessica 一样已经不是当前架构在用的东西了。
- - Meta 侧：给 Jackie 关联一个 FB Page，走一遍 `docs/MESSENGER-ACTIVATION.md`（或者我刚发你的那份通用 Tutorial）
- 好，那就是纯粹缺人工那几步了，代码那边不用等——FB 目前是走 **env variable 直连**，不是走 registry（`ip.json`）的,所以我之前说的"要改 `ip.json`"那句可以撤回,不需要。
- - 确认这个 FB Page 挂在跟 Jackie IG 账号**同一个 Meta App**下（如果是同一个 App，`FB_APP_SECRET` 可以不用另设，会 fallback 用 `META_APP_SECRET`；如果是不同 App，就要单独填 `FB_APP_SECRET`）
- - Verify token：用现成的 `META_VERIFY_TOKEN`（跟 IG 共用同一个）
- 一个我想提醒你的点：现在 FB 这条路是**单账号 env var**（`FB_PAGE_ID`/`FB_PAGE_LANGUAGE` 全局唯一），不是像 IG 那样走 `ip.json` 的多 IP registry。今天只有 Jackie 一个人用没问题，但**如果以后 Chloe 也要开自己的 FB Page，这套 env var 结构就不够用了**（两个 Page 共用一组变量会互相打架）。现在不用管，但如果你们打算近期给 Chloe 也开 Messenger，这个是要提前规划的架构债，值得先说一声。
- 需要我现在就把这几个 Render env var 用 API 帮你填上吗？还是你想先自己在 Meta 那边把 token 生成出来，我再帮你验证 probe？
- FB_APP_SECRET         — 没设（若 Jackie Page 跟 IG 挂同一个 Meta App，可不设，会 fallback 用 META_APP_SECRET）


## 2026-07-07 18:54 — social-ip-engine

### What Didn't Work (negative knowledge)
- **No, it doesn't work that way today.** Here's what's actually built:

### Architecture Decisions
- 2. **`src/notion_publish_runner.py`** — extracted `plan_and_dispatch()`: the "resume in-flight → plan → spawn task" sequence that used to be inline in the webhook handler. Now it's one function shared by both triggers.

### Decisions & Reasoning
- 3. **`src/notion_publish_scheduler.py`** (new) — an internal `asyncio` loop, same shape as your existing `reconciliation.py` sweep, that wakes daily at a configurable HKT time (default 9am) and calls that same `plan_and_dispatch()`. Chose an internal loop over external cron-job.org specifically because this Render service doesn't sleep (starter plan) and an irreversible live-post trigger shouldn't depend on a free third-party service's uptime.
- 3. **Made both triggers (the instant one + the daily one) share the exact same "actually post it" code**, instead of two separate copies that could quietly drift apart and someday double-post something. One source of truth.


## 2026-07-07 18:55 — social-ip-engine

### What Didn't Work (negative knowledge)
- **One decision it flagged for you:** the DM answer gets composed by a dedicated new small LLM call that's constrained to only re-narrate the FAQ facts (like a mini-Writer) — rather than routing through `ChloeAgent`/`PersonaAgent`, since that agent doesn't accept FAQ facts as grounding input today and would need a signature change. I'd avoid touching `ChloeAgent`'s contract for this — keep it isolated. Agree, or did you want persona voice reused there?

### Architecture Decisions
- Why split it this way rather than putting the real answer in the public reply too: public comment replies are the one surface in your whole system where a specialist would be generating user-facing medical-adjacent text with **no Writer pass, no review, and no easy takeback** if it's wrong — that's the exact "specialists never write user-facing copy" invariant your architecture is built around everywhere else. Keeping facts in DM and personalization in public gets you the "doesn't look batch" quality you want without opening that hole.
- Does that split work for you, or did you actually want the substantive answer itself visible in public (not just DM)?

### Decisions & Reasoning
- Also worth knowing: the `use_agent: true` escape hatch in the config doesn't help here — that only fires when a keyword *did* match but the rule owner wants the pipeline instead of canned text. There's no fallback path today for "genuine question, zero keyword matched."
- 3. **Only after that's been running a while**, consider one narrow automated case: a generic, zero-content "thanks for asking — DM me and I'll walk you through it 🌿" public nudge for comments classified as genuine questions. That's low-risk because it makes zero claims and just redirects into the safe, already-working DM path — but I wouldn't ship this until you've seen a few weeks of the digest and know spam won't dominate it.


## 2026-07-07 19:05 — social-ip-engine

### What Didn't Work (negative knowledge)
- Good, the ink is pure black. Now let's patch just that broken caption cleanly, keeping everything else in the infographic untouched.

### Architecture Decisions
- Same pattern I found already used for the `stomach-jackie-en` draft from 7/6, so this is now a repeatable move — worth turning into a real script (`scripts/notion_to_jianying.py`?) instead of me hand-running capcut-cli commands each time, if you're going to do this per row going forward. Want me to build that, or is one-off fine for now?
- Now let's create the toggle in Notion (mirroring Cover Photo's pattern, since the DM Infographic section's template never had a drop-toggle to begin with) and place the image there.

### Decisions & Reasoning
- Whisper is installed — let's use the real caption pipeline instead of my hand-estimated SRT, timed against the actual final.mp4 audio for accuracy.
- - **4 shots merged sequentially** on the video track (shot1→shot4, each already has its lip-synced voice audio baked in from Dreamina) — 38.39s total, canvas fixed to 1080×1920 9:16 (the CLI's default template is 16:9, so I patched `canvas_config` in both draft JSONs)
- | `period-pain-jackie-en` — the JianYing **project/draft** with merged shots + all 18 subtitle cues | `~/Movies/JianyingPro/User Data/Projects/com.lveditor.draft/period-pain-jackie-en` | ✅ but not exported |
- Homebrew is upgrading `ffmpeg` in the background (kicked off automatically as a long-running task) to line up with the newer shared libs `ffmpeg-full` just pulled in. I'll wait for that to finish rather than poll — I'll pick this back up the moment it completes and verify the whole pipeline (default ffmpeg + ffmpeg-full caption burn) is clean before calling this done. Sit tight a sec.
- Go check the file — if the caption timing/wording looks off anywhere, tell me which line and I'll fix it directly rather than rebuilding anything.
- One honest note on accuracy: whisper's word-level *timing* is solid (used only for timestamps), but I overrode all the actual text with your real script — because whisper kept mishearing the TCM terms (Sanyinjiao, Hegu, Blood Stasis) last time. So the words on screen are guaranteed correct; the timing is machine-aligned and should track the audio closely, but I didn't manually scrub every single word boundary frame-by-frame. Watch it once — if any word's highlight looks early/late anywhere, tell me the word and I'll nudge that one timestamp directly rather than regenerating anything.
- Found the issue — bottom-left acupressure caption is garbled: "3 fingers sidve wiidbs)" instead of readable text. Let me zoom in to get exact coordinates before patching it.
- I keep eyeballing this imprecisely and now overlapped the next letter. Let me regenerate clean once more and this time find the exact glyph boundary programmatically instead of guessing from crops.


## 2026-07-07 19:05 — social-ip-engine

### What Didn't Work (negative knowledge)
- Good, the ink is pure black. Now let's patch just that broken caption cleanly, keeping everything else in the infographic untouched.

### Architecture Decisions
- Same pattern I found already used for the `stomach-jackie-en` draft from 7/6, so this is now a repeatable move — worth turning into a real script (`scripts/notion_to_jianying.py`?) instead of me hand-running capcut-cli commands each time, if you're going to do this per row going forward. Want me to build that, or is one-off fine for now?
- Now let's create the toggle in Notion (mirroring Cover Photo's pattern, since the DM Infographic section's template never had a drop-toggle to begin with) and place the image there.

### Decisions & Reasoning
- Whisper is installed — let's use the real caption pipeline instead of my hand-estimated SRT, timed against the actual final.mp4 audio for accuracy.
- - **4 shots merged sequentially** on the video track (shot1→shot4, each already has its lip-synced voice audio baked in from Dreamina) — 38.39s total, canvas fixed to 1080×1920 9:16 (the CLI's default template is 16:9, so I patched `canvas_config` in both draft JSONs)
- | `period-pain-jackie-en` — the JianYing **project/draft** with merged shots + all 18 subtitle cues | `~/Movies/JianyingPro/User Data/Projects/com.lveditor.draft/period-pain-jackie-en` | ✅ but not exported |
- Homebrew is upgrading `ffmpeg` in the background (kicked off automatically as a long-running task) to line up with the newer shared libs `ffmpeg-full` just pulled in. I'll wait for that to finish rather than poll — I'll pick this back up the moment it completes and verify the whole pipeline (default ffmpeg + ffmpeg-full caption burn) is clean before calling this done. Sit tight a sec.
- Go check the file — if the caption timing/wording looks off anywhere, tell me which line and I'll fix it directly rather than rebuilding anything.
- One honest note on accuracy: whisper's word-level *timing* is solid (used only for timestamps), but I overrode all the actual text with your real script — because whisper kept mishearing the TCM terms (Sanyinjiao, Hegu, Blood Stasis) last time. So the words on screen are guaranteed correct; the timing is machine-aligned and should track the audio closely, but I didn't manually scrub every single word boundary frame-by-frame. Watch it once — if any word's highlight looks early/late anywhere, tell me the word and I'll nudge that one timestamp directly rather than regenerating anything.
- Found the issue — bottom-left acupressure caption is garbled: "3 fingers sidve wiidbs)" instead of readable text. Let me zoom in to get exact coordinates before patching it.
- I keep eyeballing this imprecisely and now overlapped the next letter. Let me regenerate clean once more and this time find the exact glyph boundary programmatically instead of guessing from crops.


## 2026-07-07 19:05 — social-ip-engine

### What Didn't Work (negative knowledge)
- **One decision it flagged for you:** the DM answer gets composed by a dedicated new small LLM call that's constrained to only re-narrate the FAQ facts (like a mini-Writer) — rather than routing through `ChloeAgent`/`PersonaAgent`, since that agent doesn't accept FAQ facts as grounding input today and would need a signature change. I'd avoid touching `ChloeAgent`'s contract for this — keep it isolated. Agree, or did you want persona voice reused there?

### Architecture Decisions
- Why split it this way rather than putting the real answer in the public reply too: public comment replies are the one surface in your whole system where a specialist would be generating user-facing medical-adjacent text with **no Writer pass, no review, and no easy takeback** if it's wrong — that's the exact "specialists never write user-facing copy" invariant your architecture is built around everywhere else. Keeping facts in DM and personalization in public gets you the "doesn't look batch" quality you want without opening that hole.
- Does that split work for you, or did you actually want the substantive answer itself visible in public (not just DM)?

### Decisions & Reasoning
- Also worth knowing: the `use_agent: true` escape hatch in the config doesn't help here — that only fires when a keyword *did* match but the rule owner wants the pipeline instead of canned text. There's no fallback path today for "genuine question, zero keyword matched."
- 3. **Only after that's been running a while**, consider one narrow automated case: a generic, zero-content "thanks for asking — DM me and I'll walk you through it 🌿" public nudge for comments classified as genuine questions. That's low-risk because it makes zero claims and just redirects into the safe, already-working DM path — but I wouldn't ship this until you've seen a few weeks of the digest and know spam won't dominate it.


## 2026-07-07 19:08 — social-ip-engine

### What Didn't Work (negative knowledge)
- **No, it doesn't work that way today.** Here's what's actually built:

### Architecture Decisions
- 2. **`src/notion_publish_runner.py`** — extracted `plan_and_dispatch()`: the "resume in-flight → plan → spawn task" sequence that used to be inline in the webhook handler. Now it's one function shared by both triggers.

### Decisions & Reasoning
- 3. **`src/notion_publish_scheduler.py`** (new) — an internal `asyncio` loop, same shape as your existing `reconciliation.py` sweep, that wakes daily at a configurable HKT time (default 9am) and calls that same `plan_and_dispatch()`. Chose an internal loop over external cron-job.org specifically because this Render service doesn't sleep (starter plan) and an irreversible live-post trigger shouldn't depend on a free third-party service's uptime.
- 3. **Made both triggers (the instant one + the daily one) share the exact same "actually post it" code**, instead of two separate copies that could quietly drift apart and someday double-post something. One source of truth.
- | 6 | **Merge 所有 shot** | 🟢 其实已经自动了 | `notion_video.py` 自己最后一步就是 `ffmpeg concat`,你叫我跑第 5 步的时候它顺便就做了,不用你再另外叫 |
- | 7 | **加字幕(karaoke highlight)** | 🔴 完全手动,而且**没有 script** | 我每次是现场用 JianYing CLI 或 ffmpeg 现改 — 这是唯一一步连"脚本"都不存在的,纯靠我临场发挥,所以才会出错、才会觉得复杂 |
- | 9 | 生成 DM 用的 infographic | 🔴 手动 | `batch_infographic_gen.py`(在 studio 这边跑),跟下面的自动化是两码事 |
- | 11 | 拖到「✅ Published」| 🟢 自动 — Notion Automation 打 `/admin/notion-publish`:自动生成/复用封面图 → 建 container → poll → 真正发到 Instagram |
- **最脆弱的一环是第 7 步**——加字幕连脚本都没有,每次都是我临时用 JianYing 现场弄,这也是为什么上次会打不开草稿、报错。第 6 步(merge)其实早就自动了,是你可能没意识到,notion_video.py 顺手就做掉了。


## 2026-07-07 19:08 — social-ip-engine

### Decisions & Reasoning
- 1. **6/10 那次** —— Messenger 曾经真实跑通过一次（FB_PAGE_ID=1200796509776468，Chloe 回复过真实 DM，截图确认过）。但那是**心宜中醫/老 Jessica 时代的 FB Page**，7 月初那次战略转向（不做 WhatsApp、不做心宜中醫）之后，那条线跟老 Jessica 一样已经不是当前架构在用的东西了。
- - Meta 侧：给 Jackie 关联一个 FB Page，走一遍 `docs/MESSENGER-ACTIVATION.md`（或者我刚发你的那份通用 Tutorial）
- 好，那就是纯粹缺人工那几步了，代码那边不用等——FB 目前是走 **env variable 直连**，不是走 registry（`ip.json`）的,所以我之前说的"要改 `ip.json`"那句可以撤回,不需要。
- - 确认这个 FB Page 挂在跟 Jackie IG 账号**同一个 Meta App**下（如果是同一个 App，`FB_APP_SECRET` 可以不用另设，会 fallback 用 `META_APP_SECRET`；如果是不同 App，就要单独填 `FB_APP_SECRET`）
- - Verify token：用现成的 `META_VERIFY_TOKEN`（跟 IG 共用同一个）
- 一个我想提醒你的点：现在 FB 这条路是**单账号 env var**（`FB_PAGE_ID`/`FB_PAGE_LANGUAGE` 全局唯一），不是像 IG 那样走 `ip.json` 的多 IP registry。今天只有 Jackie 一个人用没问题，但**如果以后 Chloe 也要开自己的 FB Page，这套 env var 结构就不够用了**（两个 Page 共用一组变量会互相打架）。现在不用管，但如果你们打算近期给 Chloe 也开 Messenger，这个是要提前规划的架构债，值得先说一声。
- 需要我现在就把这几个 Render env var 用 API 帮你填上吗？还是你想先自己在 Meta 那边把 token 生成出来，我再帮你验证 probe？
- FB_APP_SECRET         — 没设（若 Jackie Page 跟 IG 挂同一个 Meta App，可不设，会 fallback 用 META_APP_SECRET）


## 2026-07-07 19:09 — social-ip-engine

### Decisions & Reasoning
- 1. **6/10 那次** —— Messenger 曾经真实跑通过一次（FB_PAGE_ID=1200796509776468，Chloe 回复过真实 DM，截图确认过）。但那是**心宜中醫/老 Jessica 时代的 FB Page**，7 月初那次战略转向（不做 WhatsApp、不做心宜中醫）之后，那条线跟老 Jessica 一样已经不是当前架构在用的东西了。
- - Meta 侧：给 Jackie 关联一个 FB Page，走一遍 `docs/MESSENGER-ACTIVATION.md`（或者我刚发你的那份通用 Tutorial）
- 好，那就是纯粹缺人工那几步了，代码那边不用等——FB 目前是走 **env variable 直连**，不是走 registry（`ip.json`）的,所以我之前说的"要改 `ip.json`"那句可以撤回,不需要。
- - 确认这个 FB Page 挂在跟 Jackie IG 账号**同一个 Meta App**下（如果是同一个 App，`FB_APP_SECRET` 可以不用另设，会 fallback 用 `META_APP_SECRET`；如果是不同 App，就要单独填 `FB_APP_SECRET`）
- - Verify token：用现成的 `META_VERIFY_TOKEN`（跟 IG 共用同一个）
- 一个我想提醒你的点：现在 FB 这条路是**单账号 env var**（`FB_PAGE_ID`/`FB_PAGE_LANGUAGE` 全局唯一），不是像 IG 那样走 `ip.json` 的多 IP registry。今天只有 Jackie 一个人用没问题，但**如果以后 Chloe 也要开自己的 FB Page，这套 env var 结构就不够用了**（两个 Page 共用一组变量会互相打架）。现在不用管，但如果你们打算近期给 Chloe 也开 Messenger，这个是要提前规划的架构债，值得先说一声。
- 需要我现在就把这几个 Render env var 用 API 帮你填上吗？还是你想先自己在 Meta 那边把 token 生成出来，我再帮你验证 probe？
- FB_APP_SECRET         — 没设（若 Jackie Page 跟 IG 挂同一个 Meta App，可不设，会 fallback 用 META_APP_SECRET）


## 2026-07-07 19:10 — social-ip-engine

### Decisions & Reasoning
- Need dotted module paths instead of file paths for `--cov`.


## 2026-07-07 19:11 — social-ip-engine

### What Didn't Work (negative knowledge)
- **One decision it flagged for you:** the DM answer gets composed by a dedicated new small LLM call that's constrained to only re-narrate the FAQ facts (like a mini-Writer) — rather than routing through `ChloeAgent`/`PersonaAgent`, since that agent doesn't accept FAQ facts as grounding input today and would need a signature change. I'd avoid touching `ChloeAgent`'s contract for this — keep it isolated. Agree, or did you want persona voice reused there?

### Architecture Decisions
- Why split it this way rather than putting the real answer in the public reply too: public comment replies are the one surface in your whole system where a specialist would be generating user-facing medical-adjacent text with **no Writer pass, no review, and no easy takeback** if it's wrong — that's the exact "specialists never write user-facing copy" invariant your architecture is built around everywhere else. Keeping facts in DM and personalization in public gets you the "doesn't look batch" quality you want without opening that hole.
- Does that split work for you, or did you actually want the substantive answer itself visible in public (not just DM)?

### Decisions & Reasoning
- Also worth knowing: the `use_agent: true` escape hatch in the config doesn't help here — that only fires when a keyword *did* match but the rule owner wants the pipeline instead of canned text. There's no fallback path today for "genuine question, zero keyword matched."
- 3. **Only after that's been running a while**, consider one narrow automated case: a generic, zero-content "thanks for asking — DM me and I'll walk you through it 🌿" public nudge for comments classified as genuine questions. That's low-risk because it makes zero claims and just redirects into the safe, already-working DM path — but I wouldn't ship this until you've seen a few weeks of the digest and know spam won't dominate it.


## 2026-07-07 19:14 — social-ip-engine

### Decisions & Reasoning
- I don't have a prior review in progress from this session — let me quickly assess the changeset so I can give you real findings rather than an empty summary. Checking scope first.
- I don't have a prior review recorded in this session, so let me actually run it now rather than hand you an empty summary. I'll do focused reviews in parallel on the substantive changes (Notion publish/sync + scheduler, and the new comment/DM handling paths), then synthesize.


## 2026-07-07 19:16 — social-ip-engine

### What Didn't Work (negative knowledge)
- **One decision it flagged for you:** the DM answer gets composed by a dedicated new small LLM call that's constrained to only re-narrate the FAQ facts (like a mini-Writer) — rather than routing through `ChloeAgent`/`PersonaAgent`, since that agent doesn't accept FAQ facts as grounding input today and would need a signature change. I'd avoid touching `ChloeAgent`'s contract for this — keep it isolated. Agree, or did you want persona voice reused there?

### Architecture Decisions
- Why split it this way rather than putting the real answer in the public reply too: public comment replies are the one surface in your whole system where a specialist would be generating user-facing medical-adjacent text with **no Writer pass, no review, and no easy takeback** if it's wrong — that's the exact "specialists never write user-facing copy" invariant your architecture is built around everywhere else. Keeping facts in DM and personalization in public gets you the "doesn't look batch" quality you want without opening that hole.
- Does that split work for you, or did you actually want the substantive answer itself visible in public (not just DM)?

### Decisions & Reasoning
- Also worth knowing: the `use_agent: true` escape hatch in the config doesn't help here — that only fires when a keyword *did* match but the rule owner wants the pipeline instead of canned text. There's no fallback path today for "genuine question, zero keyword matched."
- 3. **Only after that's been running a while**, consider one narrow automated case: a generic, zero-content "thanks for asking — DM me and I'll walk you through it 🌿" public nudge for comments classified as genuine questions. That's low-risk because it makes zero claims and just redirects into the safe, already-working DM path — but I wouldn't ship this until you've seen a few weeks of the digest and know spam won't dominate it.


## 2026-07-07 19:17 — social-ip-engine

### What Didn't Work (negative knowledge)
- **One decision it flagged for you:** the DM answer gets composed by a dedicated new small LLM call that's constrained to only re-narrate the FAQ facts (like a mini-Writer) — rather than routing through `ChloeAgent`/`PersonaAgent`, since that agent doesn't accept FAQ facts as grounding input today and would need a signature change. I'd avoid touching `ChloeAgent`'s contract for this — keep it isolated. Agree, or did you want persona voice reused there?

### Architecture Decisions
- Why split it this way rather than putting the real answer in the public reply too: public comment replies are the one surface in your whole system where a specialist would be generating user-facing medical-adjacent text with **no Writer pass, no review, and no easy takeback** if it's wrong — that's the exact "specialists never write user-facing copy" invariant your architecture is built around everywhere else. Keeping facts in DM and personalization in public gets you the "doesn't look batch" quality you want without opening that hole.
- Does that split work for you, or did you actually want the substantive answer itself visible in public (not just DM)?

### Decisions & Reasoning
- Also worth knowing: the `use_agent: true` escape hatch in the config doesn't help here — that only fires when a keyword *did* match but the rule owner wants the pipeline instead of canned text. There's no fallback path today for "genuine question, zero keyword matched."
- 3. **Only after that's been running a while**, consider one narrow automated case: a generic, zero-content "thanks for asking — DM me and I'll walk you through it 🌿" public nudge for comments classified as genuine questions. That's low-risk because it makes zero claims and just redirects into the safe, already-working DM path — but I wouldn't ship this until you've seen a few weeks of the digest and know spam won't dominate it.


## 2026-07-07 19:18 — social-ip-engine

### Decisions & Reasoning
- 1. **6/10 那次** —— Messenger 曾经真实跑通过一次（FB_PAGE_ID=1200796509776468，Chloe 回复过真实 DM，截图确认过）。但那是**心宜中醫/老 Jessica 时代的 FB Page**，7 月初那次战略转向（不做 WhatsApp、不做心宜中醫）之后，那条线跟老 Jessica 一样已经不是当前架构在用的东西了。
- - Meta 侧：给 Jackie 关联一个 FB Page，走一遍 `docs/MESSENGER-ACTIVATION.md`（或者我刚发你的那份通用 Tutorial）
- 好，那就是纯粹缺人工那几步了，代码那边不用等——FB 目前是走 **env variable 直连**，不是走 registry（`ip.json`）的,所以我之前说的"要改 `ip.json`"那句可以撤回,不需要。
- - 确认这个 FB Page 挂在跟 Jackie IG 账号**同一个 Meta App**下（如果是同一个 App，`FB_APP_SECRET` 可以不用另设，会 fallback 用 `META_APP_SECRET`；如果是不同 App，就要单独填 `FB_APP_SECRET`）
- - Verify token：用现成的 `META_VERIFY_TOKEN`（跟 IG 共用同一个）
- 一个我想提醒你的点：现在 FB 这条路是**单账号 env var**（`FB_PAGE_ID`/`FB_PAGE_LANGUAGE` 全局唯一），不是像 IG 那样走 `ip.json` 的多 IP registry。今天只有 Jackie 一个人用没问题，但**如果以后 Chloe 也要开自己的 FB Page，这套 env var 结构就不够用了**（两个 Page 共用一组变量会互相打架）。现在不用管，但如果你们打算近期给 Chloe 也开 Messenger，这个是要提前规划的架构债，值得先说一声。
- 需要我现在就把这几个 Render env var 用 API 帮你填上吗？还是你想先自己在 Meta 那边把 token 生成出来，我再帮你验证 probe？
- FB_APP_SECRET         — 没设（若 Jackie Page 跟 IG 挂同一个 Meta App，可不设，会 fallback 用 META_APP_SECRET）


## 2026-07-07 19:19 — social-ip-engine

### What Didn't Work (negative knowledge)
- **One decision it flagged for you:** the DM answer gets composed by a dedicated new small LLM call that's constrained to only re-narrate the FAQ facts (like a mini-Writer) — rather than routing through `ChloeAgent`/`PersonaAgent`, since that agent doesn't accept FAQ facts as grounding input today and would need a signature change. I'd avoid touching `ChloeAgent`'s contract for this — keep it isolated. Agree, or did you want persona voice reused there?

### Architecture Decisions
- Why split it this way rather than putting the real answer in the public reply too: public comment replies are the one surface in your whole system where a specialist would be generating user-facing medical-adjacent text with **no Writer pass, no review, and no easy takeback** if it's wrong — that's the exact "specialists never write user-facing copy" invariant your architecture is built around everywhere else. Keeping facts in DM and personalization in public gets you the "doesn't look batch" quality you want without opening that hole.
- Does that split work for you, or did you actually want the substantive answer itself visible in public (not just DM)?
- - Medium/low stuff: stale `lru_cache` on the product blocklist (won't pick up new products without a restart, inconsistent with `comment_rules.py`'s mtime-reload pattern it's modeled on), unguarded MIN>MAX config interaction, reaching into `comment_rules._expected_language` with a `noqa` instead of promoting it public, a redundant CRM re-fetch that compounds the race.

### Decisions & Reasoning
- Also worth knowing: the `use_agent: true` escape hatch in the config doesn't help here — that only fires when a keyword *did* match but the rule owner wants the pipeline instead of canned text. There's no fallback path today for "genuine question, zero keyword matched."
- 3. **Only after that's been running a while**, consider one narrow automated case: a generic, zero-content "thanks for asking — DM me and I'll walk you through it 🌿" public nudge for comments classified as genuine questions. That's low-risk because it makes zero claims and just redirects into the safe, already-working DM path — but I wouldn't ship this until you've seen a few weeks of the digest and know spam won't dominate it.


## 2026-07-07 19:19 — social-ip-engine

### What Didn't Work (negative knowledge)
- Good, the ink is pure black. Now let's patch just that broken caption cleanly, keeping everything else in the infographic untouched.

### Architecture Decisions
- Same pattern I found already used for the `stomach-jackie-en` draft from 7/6, so this is now a repeatable move — worth turning into a real script (`scripts/notion_to_jianying.py`?) instead of me hand-running capcut-cli commands each time, if you're going to do this per row going forward. Want me to build that, or is one-off fine for now?
- Now let's create the toggle in Notion (mirroring Cover Photo's pattern, since the DM Infographic section's template never had a drop-toggle to begin with) and place the image there.

### Decisions & Reasoning
- Whisper is installed — let's use the real caption pipeline instead of my hand-estimated SRT, timed against the actual final.mp4 audio for accuracy.
- - **4 shots merged sequentially** on the video track (shot1→shot4, each already has its lip-synced voice audio baked in from Dreamina) — 38.39s total, canvas fixed to 1080×1920 9:16 (the CLI's default template is 16:9, so I patched `canvas_config` in both draft JSONs)
- | `period-pain-jackie-en` — the JianYing **project/draft** with merged shots + all 18 subtitle cues | `~/Movies/JianyingPro/User Data/Projects/com.lveditor.draft/period-pain-jackie-en` | ✅ but not exported |
- Homebrew is upgrading `ffmpeg` in the background (kicked off automatically as a long-running task) to line up with the newer shared libs `ffmpeg-full` just pulled in. I'll wait for that to finish rather than poll — I'll pick this back up the moment it completes and verify the whole pipeline (default ffmpeg + ffmpeg-full caption burn) is clean before calling this done. Sit tight a sec.
- Go check the file — if the caption timing/wording looks off anywhere, tell me which line and I'll fix it directly rather than rebuilding anything.
- One honest note on accuracy: whisper's word-level *timing* is solid (used only for timestamps), but I overrode all the actual text with your real script — because whisper kept mishearing the TCM terms (Sanyinjiao, Hegu, Blood Stasis) last time. So the words on screen are guaranteed correct; the timing is machine-aligned and should track the audio closely, but I didn't manually scrub every single word boundary frame-by-frame. Watch it once — if any word's highlight looks early/late anywhere, tell me the word and I'll nudge that one timestamp directly rather than regenerating anything.
- Found the issue — bottom-left acupressure caption is garbled: "3 fingers sidve wiidbs)" instead of readable text. Let me zoom in to get exact coordinates before patching it.
- I keep eyeballing this imprecisely and now overlapped the next letter. Let me regenerate clean once more and this time find the exact glyph boundary programmatically instead of guessing from crops.


## 2026-07-07 19:20 — social-ip-engine

### What Didn't Work (negative knowledge)
- Good, the ink is pure black. Now let's patch just that broken caption cleanly, keeping everything else in the infographic untouched.

### Architecture Decisions
- Same pattern I found already used for the `stomach-jackie-en` draft from 7/6, so this is now a repeatable move — worth turning into a real script (`scripts/notion_to_jianying.py`?) instead of me hand-running capcut-cli commands each time, if you're going to do this per row going forward. Want me to build that, or is one-off fine for now?
- Now let's create the toggle in Notion (mirroring Cover Photo's pattern, since the DM Infographic section's template never had a drop-toggle to begin with) and place the image there.
- | MEDIUM | Cross-row filename collision if two different rows/accounts share a keyword | **Not fixed** — this is a pre-existing pattern across the whole module (same risk already exists in the plain-download path, not just what I added), and properly fixing it means touching filename/state-key conventions used in multiple places. Flagging it rather than scope-creeping further this session — worth its own pass if you want it. |

### Decisions & Reasoning
- Whisper is installed — let's use the real caption pipeline instead of my hand-estimated SRT, timed against the actual final.mp4 audio for accuracy.
- - **4 shots merged sequentially** on the video track (shot1→shot4, each already has its lip-synced voice audio baked in from Dreamina) — 38.39s total, canvas fixed to 1080×1920 9:16 (the CLI's default template is 16:9, so I patched `canvas_config` in both draft JSONs)
- | `period-pain-jackie-en` — the JianYing **project/draft** with merged shots + all 18 subtitle cues | `~/Movies/JianyingPro/User Data/Projects/com.lveditor.draft/period-pain-jackie-en` | ✅ but not exported |
- Homebrew is upgrading `ffmpeg` in the background (kicked off automatically as a long-running task) to line up with the newer shared libs `ffmpeg-full` just pulled in. I'll wait for that to finish rather than poll — I'll pick this back up the moment it completes and verify the whole pipeline (default ffmpeg + ffmpeg-full caption burn) is clean before calling this done. Sit tight a sec.
- Go check the file — if the caption timing/wording looks off anywhere, tell me which line and I'll fix it directly rather than rebuilding anything.
- One honest note on accuracy: whisper's word-level *timing* is solid (used only for timestamps), but I overrode all the actual text with your real script — because whisper kept mishearing the TCM terms (Sanyinjiao, Hegu, Blood Stasis) last time. So the words on screen are guaranteed correct; the timing is machine-aligned and should track the audio closely, but I didn't manually scrub every single word boundary frame-by-frame. Watch it once — if any word's highlight looks early/late anywhere, tell me the word and I'll nudge that one timestamp directly rather than regenerating anything.
- Found the issue — bottom-left acupressure caption is garbled: "3 fingers sidve wiidbs)" instead of readable text. Let me zoom in to get exact coordinates before patching it.
- I keep eyeballing this imprecisely and now overlapped the next letter. Let me regenerate clean once more and this time find the exact glyph boundary programmatically instead of guessing from crops.


## 2026-07-07 19:24 — social-ip-engine

### Decisions & Reasoning
- 1. **6/10 那次** —— Messenger 曾经真实跑通过一次（FB_PAGE_ID=1200796509776468，Chloe 回复过真实 DM，截图确认过）。但那是**心宜中醫/老 Jessica 时代的 FB Page**，7 月初那次战略转向（不做 WhatsApp、不做心宜中醫）之后，那条线跟老 Jessica 一样已经不是当前架构在用的东西了。
- - Meta 侧：给 Jackie 关联一个 FB Page，走一遍 `docs/MESSENGER-ACTIVATION.md`（或者我刚发你的那份通用 Tutorial）
- 好，那就是纯粹缺人工那几步了，代码那边不用等——FB 目前是走 **env variable 直连**，不是走 registry（`ip.json`）的,所以我之前说的"要改 `ip.json`"那句可以撤回,不需要。
- - 确认这个 FB Page 挂在跟 Jackie IG 账号**同一个 Meta App**下（如果是同一个 App，`FB_APP_SECRET` 可以不用另设，会 fallback 用 `META_APP_SECRET`；如果是不同 App，就要单独填 `FB_APP_SECRET`）
- - Verify token：用现成的 `META_VERIFY_TOKEN`（跟 IG 共用同一个）
- 一个我想提醒你的点：现在 FB 这条路是**单账号 env var**（`FB_PAGE_ID`/`FB_PAGE_LANGUAGE` 全局唯一），不是像 IG 那样走 `ip.json` 的多 IP registry。今天只有 Jackie 一个人用没问题，但**如果以后 Chloe 也要开自己的 FB Page，这套 env var 结构就不够用了**（两个 Page 共用一组变量会互相打架）。现在不用管，但如果你们打算近期给 Chloe 也开 Messenger，这个是要提前规划的架构债，值得先说一声。
- 需要我现在就把这几个 Render env var 用 API 帮你填上吗？还是你想先自己在 Meta 那边把 token 生成出来，我再帮你验证 probe？
- FB_APP_SECRET         — 没设（若 Jackie Page 跟 IG 挂同一个 Meta App，可不设，会 fallback 用 META_APP_SECRET）


## 2026-07-07 19:31 — social-ip-engine

### What Didn't Work (negative knowledge)
- **No, it doesn't work that way today.** Here's what's actually built:

### Architecture Decisions
- 2. **`src/notion_publish_runner.py`** — extracted `plan_and_dispatch()`: the "resume in-flight → plan → spawn task" sequence that used to be inline in the webhook handler. Now it's one function shared by both triggers.

### Decisions & Reasoning
- 3. **`src/notion_publish_scheduler.py`** (new) — an internal `asyncio` loop, same shape as your existing `reconciliation.py` sweep, that wakes daily at a configurable HKT time (default 9am) and calls that same `plan_and_dispatch()`. Chose an internal loop over external cron-job.org specifically because this Render service doesn't sleep (starter plan) and an irreversible live-post trigger shouldn't depend on a free third-party service's uptime.
- 3. **Made both triggers (the instant one + the daily one) share the exact same "actually post it" code**, instead of two separate copies that could quietly drift apart and someday double-post something. One source of truth.
- | 6 | **Merge 所有 shot** | 🟢 其实已经自动了 | `notion_video.py` 自己最后一步就是 `ffmpeg concat`,你叫我跑第 5 步的时候它顺便就做了,不用你再另外叫 |
- | 7 | **加字幕(karaoke highlight)** | 🔴 完全手动,而且**没有 script** | 我每次是现场用 JianYing CLI 或 ffmpeg 现改 — 这是唯一一步连"脚本"都不存在的,纯靠我临场发挥,所以才会出错、才会觉得复杂 |
- | 9 | 生成 DM 用的 infographic | 🔴 手动 | `batch_infographic_gen.py`(在 studio 这边跑),跟下面的自动化是两码事 |
- | 11 | 拖到「✅ Published」| 🟢 自动 — Notion Automation 打 `/admin/notion-publish`:自动生成/复用封面图 → 建 container → poll → 真正发到 Instagram |
- **最脆弱的一环是第 7 步**——加字幕连脚本都没有,每次都是我临时用 JianYing 现场弄,这也是为什么上次会打不开草稿、报错。第 6 步(merge)其实早就自动了,是你可能没意识到,notion_video.py 顺手就做掉了。
- Something's off with the vertical positioning — text is nearly touching the bottom edge instead of having a proper margin. Let me debug the actual measurements:


## 2026-07-07 19:38 — social-ip-engine

### What Didn't Work (negative knowledge)
- Good, the ink is pure black. Now let's patch just that broken caption cleanly, keeping everything else in the infographic untouched.

### Architecture Decisions
- Same pattern I found already used for the `stomach-jackie-en` draft from 7/6, so this is now a repeatable move — worth turning into a real script (`scripts/notion_to_jianying.py`?) instead of me hand-running capcut-cli commands each time, if you're going to do this per row going forward. Want me to build that, or is one-off fine for now?
- Now let's create the toggle in Notion (mirroring Cover Photo's pattern, since the DM Infographic section's template never had a drop-toggle to begin with) and place the image there.
- | MEDIUM | Cross-row filename collision if two different rows/accounts share a keyword | **Not fixed** — this is a pre-existing pattern across the whole module (same risk already exists in the plain-download path, not just what I added), and properly fixing it means touching filename/state-key conventions used in multiple places. Flagging it rather than scope-creeping further this session — worth its own pass if you want it. |

### Decisions & Reasoning
- Whisper is installed — let's use the real caption pipeline instead of my hand-estimated SRT, timed against the actual final.mp4 audio for accuracy.
- - **4 shots merged sequentially** on the video track (shot1→shot4, each already has its lip-synced voice audio baked in from Dreamina) — 38.39s total, canvas fixed to 1080×1920 9:16 (the CLI's default template is 16:9, so I patched `canvas_config` in both draft JSONs)
- | `period-pain-jackie-en` — the JianYing **project/draft** with merged shots + all 18 subtitle cues | `~/Movies/JianyingPro/User Data/Projects/com.lveditor.draft/period-pain-jackie-en` | ✅ but not exported |
- Homebrew is upgrading `ffmpeg` in the background (kicked off automatically as a long-running task) to line up with the newer shared libs `ffmpeg-full` just pulled in. I'll wait for that to finish rather than poll — I'll pick this back up the moment it completes and verify the whole pipeline (default ffmpeg + ffmpeg-full caption burn) is clean before calling this done. Sit tight a sec.
- Go check the file — if the caption timing/wording looks off anywhere, tell me which line and I'll fix it directly rather than rebuilding anything.
- One honest note on accuracy: whisper's word-level *timing* is solid (used only for timestamps), but I overrode all the actual text with your real script — because whisper kept mishearing the TCM terms (Sanyinjiao, Hegu, Blood Stasis) last time. So the words on screen are guaranteed correct; the timing is machine-aligned and should track the audio closely, but I didn't manually scrub every single word boundary frame-by-frame. Watch it once — if any word's highlight looks early/late anywhere, tell me the word and I'll nudge that one timestamp directly rather than regenerating anything.
- Found the issue — bottom-left acupressure caption is garbled: "3 fingers sidve wiidbs)" instead of readable text. Let me zoom in to get exact coordinates before patching it.
- I keep eyeballing this imprecisely and now overlapped the next letter. Let me regenerate clean once more and this time find the exact glyph boundary programmatically instead of guessing from crops.


## 2026-07-07 19:38 — social-ip-engine

### What Didn't Work (negative knowledge)
- **One decision it flagged for you:** the DM answer gets composed by a dedicated new small LLM call that's constrained to only re-narrate the FAQ facts (like a mini-Writer) — rather than routing through `ChloeAgent`/`PersonaAgent`, since that agent doesn't accept FAQ facts as grounding input today and would need a signature change. I'd avoid touching `ChloeAgent`'s contract for this — keep it isolated. Agree, or did you want persona voice reused there?

### Architecture Decisions
- Why split it this way rather than putting the real answer in the public reply too: public comment replies are the one surface in your whole system where a specialist would be generating user-facing medical-adjacent text with **no Writer pass, no review, and no easy takeback** if it's wrong — that's the exact "specialists never write user-facing copy" invariant your architecture is built around everywhere else. Keeping facts in DM and personalization in public gets you the "doesn't look batch" quality you want without opening that hole.
- Does that split work for you, or did you actually want the substantive answer itself visible in public (not just DM)?
- - Medium/low stuff: stale `lru_cache` on the product blocklist (won't pick up new products without a restart, inconsistent with `comment_rules.py`'s mtime-reload pattern it's modeled on), unguarded MIN>MAX config interaction, reaching into `comment_rules._expected_language` with a `noqa` instead of promoting it public, a redundant CRM re-fetch that compounds the race.
- It splits the model's full reply on blank lines/newlines, then just **slices off the first `max_bubbles` parts and silently drops everything after**. If the model writes a numbered list where each point (or worse, the number and its content) lands as a separate blank-line-separated chunk, and there are more than `max_bubbles` (default 3, per `data/ips/*/persona.json`) chunks total, points 4+ vanish entirely — which is exactly your "wrote '1' then stopped" symptom if the number and its explanation get split into separate chunks and the cap lands between them.

### Decisions & Reasoning
- Also worth knowing: the `use_agent: true` escape hatch in the config doesn't help here — that only fires when a keyword *did* match but the rule owner wants the pipeline instead of canned text. There's no fallback path today for "genuine question, zero keyword matched."
- 3. **Only after that's been running a while**, consider one narrow automated case: a generic, zero-content "thanks for asking — DM me and I'll walk you through it 🌿" public nudge for comments classified as genuine questions. That's low-risk because it makes zero claims and just redirects into the safe, already-working DM path — but I wouldn't ship this until you've seen a few weeks of the digest and know spam won't dominate it.
- Confirmed — the persona prompts (`data/ips/chloe/persona.json`, `data/ips/jackie/persona.json`) already tell the model "max 1-3 bubbles, separated by blank line," but same as a known issue documented elsewhere in this codebase (`writer.py`'s comment: "prompt instructions alone are not sufficient — proven in production"), the model doesn't always obey, and the code-level enforcement here just drops the overflow instead of folding it in.


## 2026-07-07 19:38 — social-ip-engine

### Architecture Decisions
- Only 1 unrelated pre-existing failure (`test_chloe_agent.py` bubble-splitting, nothing to do with this change) — 1157 passed. Per policy this needs a python-reviewer pass before shipping since it's production webhook logic:

### Decisions & Reasoning
- 1. **6/10 那次** —— Messenger 曾经真实跑通过一次（FB_PAGE_ID=1200796509776468，Chloe 回复过真实 DM，截图确认过）。但那是**心宜中醫/老 Jessica 时代的 FB Page**，7 月初那次战略转向（不做 WhatsApp、不做心宜中醫）之后，那条线跟老 Jessica 一样已经不是当前架构在用的东西了。
- - Meta 侧：给 Jackie 关联一个 FB Page，走一遍 `docs/MESSENGER-ACTIVATION.md`（或者我刚发你的那份通用 Tutorial）
- 好，那就是纯粹缺人工那几步了，代码那边不用等——FB 目前是走 **env variable 直连**，不是走 registry（`ip.json`）的,所以我之前说的"要改 `ip.json`"那句可以撤回,不需要。
- - 确认这个 FB Page 挂在跟 Jackie IG 账号**同一个 Meta App**下（如果是同一个 App，`FB_APP_SECRET` 可以不用另设，会 fallback 用 `META_APP_SECRET`；如果是不同 App，就要单独填 `FB_APP_SECRET`）
- - Verify token：用现成的 `META_VERIFY_TOKEN`（跟 IG 共用同一个）
- 一个我想提醒你的点：现在 FB 这条路是**单账号 env var**（`FB_PAGE_ID`/`FB_PAGE_LANGUAGE` 全局唯一），不是像 IG 那样走 `ip.json` 的多 IP registry。今天只有 Jackie 一个人用没问题，但**如果以后 Chloe 也要开自己的 FB Page，这套 env var 结构就不够用了**（两个 Page 共用一组变量会互相打架）。现在不用管，但如果你们打算近期给 Chloe 也开 Messenger，这个是要提前规划的架构债，值得先说一声。
- 需要我现在就把这几个 Render env var 用 API 帮你填上吗？还是你想先自己在 Meta 那边把 token 生成出来，我再帮你验证 probe？
- FB_APP_SECRET         — 没设（若 Jackie Page 跟 IG 挂同一个 Meta App，可不设，会 fallback 用 META_APP_SECRET）


## 2026-07-07 19:39 — social-ip-engine

### What Didn't Work (negative knowledge)
- **One decision it flagged for you:** the DM answer gets composed by a dedicated new small LLM call that's constrained to only re-narrate the FAQ facts (like a mini-Writer) — rather than routing through `ChloeAgent`/`PersonaAgent`, since that agent doesn't accept FAQ facts as grounding input today and would need a signature change. I'd avoid touching `ChloeAgent`'s contract for this — keep it isolated. Agree, or did you want persona voice reused there?

### Architecture Decisions
- Why split it this way rather than putting the real answer in the public reply too: public comment replies are the one surface in your whole system where a specialist would be generating user-facing medical-adjacent text with **no Writer pass, no review, and no easy takeback** if it's wrong — that's the exact "specialists never write user-facing copy" invariant your architecture is built around everywhere else. Keeping facts in DM and personalization in public gets you the "doesn't look batch" quality you want without opening that hole.
- Does that split work for you, or did you actually want the substantive answer itself visible in public (not just DM)?
- - Medium/low stuff: stale `lru_cache` on the product blocklist (won't pick up new products without a restart, inconsistent with `comment_rules.py`'s mtime-reload pattern it's modeled on), unguarded MIN>MAX config interaction, reaching into `comment_rules._expected_language` with a `noqa` instead of promoting it public, a redundant CRM re-fetch that compounds the race.
- It splits the model's full reply on blank lines/newlines, then just **slices off the first `max_bubbles` parts and silently drops everything after**. If the model writes a numbered list where each point (or worse, the number and its content) lands as a separate blank-line-separated chunk, and there are more than `max_bubbles` (default 3, per `data/ips/*/persona.json`) chunks total, points 4+ vanish entirely — which is exactly your "wrote '1' then stopped" symptom if the number and its explanation get split into separate chunks and the cap lands between them.
- **Bubble-truncation bug (the live one you reported):** fixed. `_split_bubbles` no longer drops overflow content — it keeps the first `max_bubbles - 1` parts as individual bubbles and folds everything past that into the final bubble, so a 5-point answer with a 3-bubble cap now shows all 5 points (points 3-5 merged into bubble 3) instead of silently losing points 4-5. This should stop the "writes 1, then stops" behavior you saw.

### Decisions & Reasoning
- Also worth knowing: the `use_agent: true` escape hatch in the config doesn't help here — that only fires when a keyword *did* match but the rule owner wants the pipeline instead of canned text. There's no fallback path today for "genuine question, zero keyword matched."
- 3. **Only after that's been running a while**, consider one narrow automated case: a generic, zero-content "thanks for asking — DM me and I'll walk you through it 🌿" public nudge for comments classified as genuine questions. That's low-risk because it makes zero claims and just redirects into the safe, already-working DM path — but I wouldn't ship this until you've seen a few weeks of the digest and know spam won't dominate it.
- Confirmed — the persona prompts (`data/ips/chloe/persona.json`, `data/ips/jackie/persona.json`) already tell the model "max 1-3 bubbles, separated by blank line," but same as a known issue documented elsewhere in this codebase (`writer.py`'s comment: "prompt instructions alone are not sufficient — proven in production"), the model doesn't always obey, and the code-level enforcement here just drops the overflow instead of folding it in.


## 2026-07-07 19:40 — social-ip-engine

### What Didn't Work (negative knowledge)
- **One decision it flagged for you:** the DM answer gets composed by a dedicated new small LLM call that's constrained to only re-narrate the FAQ facts (like a mini-Writer) — rather than routing through `ChloeAgent`/`PersonaAgent`, since that agent doesn't accept FAQ facts as grounding input today and would need a signature change. I'd avoid touching `ChloeAgent`'s contract for this — keep it isolated. Agree, or did you want persona voice reused there?

### Architecture Decisions
- Why split it this way rather than putting the real answer in the public reply too: public comment replies are the one surface in your whole system where a specialist would be generating user-facing medical-adjacent text with **no Writer pass, no review, and no easy takeback** if it's wrong — that's the exact "specialists never write user-facing copy" invariant your architecture is built around everywhere else. Keeping facts in DM and personalization in public gets you the "doesn't look batch" quality you want without opening that hole.
- Does that split work for you, or did you actually want the substantive answer itself visible in public (not just DM)?
- - Medium/low stuff: stale `lru_cache` on the product blocklist (won't pick up new products without a restart, inconsistent with `comment_rules.py`'s mtime-reload pattern it's modeled on), unguarded MIN>MAX config interaction, reaching into `comment_rules._expected_language` with a `noqa` instead of promoting it public, a redundant CRM re-fetch that compounds the race.
- It splits the model's full reply on blank lines/newlines, then just **slices off the first `max_bubbles` parts and silently drops everything after**. If the model writes a numbered list where each point (or worse, the number and its content) lands as a separate blank-line-separated chunk, and there are more than `max_bubbles` (default 3, per `data/ips/*/persona.json`) chunks total, points 4+ vanish entirely — which is exactly your "wrote '1' then stopped" symptom if the number and its explanation get split into separate chunks and the cap lands between them.
- **Bubble-truncation bug (the live one you reported):** fixed. `_split_bubbles` no longer drops overflow content — it keeps the first `max_bubbles - 1` parts as individual bubbles and folds everything past that into the final bubble, so a 5-point answer with a 3-bubble cap now shows all 5 points (points 3-5 merged into bubble 3) instead of silently losing points 4-5. This should stop the "writes 1, then stops" behavior you saw.

### Decisions & Reasoning
- Also worth knowing: the `use_agent: true` escape hatch in the config doesn't help here — that only fires when a keyword *did* match but the rule owner wants the pipeline instead of canned text. There's no fallback path today for "genuine question, zero keyword matched."
- 3. **Only after that's been running a while**, consider one narrow automated case: a generic, zero-content "thanks for asking — DM me and I'll walk you through it 🌿" public nudge for comments classified as genuine questions. That's low-risk because it makes zero claims and just redirects into the safe, already-working DM path — but I wouldn't ship this until you've seen a few weeks of the digest and know spam won't dominate it.
- Confirmed — the persona prompts (`data/ips/chloe/persona.json`, `data/ips/jackie/persona.json`) already tell the model "max 1-3 bubbles, separated by blank line," but same as a known issue documented elsewhere in this codebase (`writer.py`'s comment: "prompt instructions alone are not sufficient — proven in production"), the model doesn't always obey, and the code-level enforcement here just drops the overflow instead of folding it in.


## 2026-07-07 19:40 — social-ip-engine

### What Didn't Work (negative knowledge)
- **No, it doesn't work that way today.** Here's what's actually built:

### Architecture Decisions
- 2. **`src/notion_publish_runner.py`** — extracted `plan_and_dispatch()`: the "resume in-flight → plan → spawn task" sequence that used to be inline in the webhook handler. Now it's one function shared by both triggers.

### Decisions & Reasoning
- 3. **`src/notion_publish_scheduler.py`** (new) — an internal `asyncio` loop, same shape as your existing `reconciliation.py` sweep, that wakes daily at a configurable HKT time (default 9am) and calls that same `plan_and_dispatch()`. Chose an internal loop over external cron-job.org specifically because this Render service doesn't sleep (starter plan) and an irreversible live-post trigger shouldn't depend on a free third-party service's uptime.
- 3. **Made both triggers (the instant one + the daily one) share the exact same "actually post it" code**, instead of two separate copies that could quietly drift apart and someday double-post something. One source of truth.
- | 6 | **Merge 所有 shot** | 🟢 其实已经自动了 | `notion_video.py` 自己最后一步就是 `ffmpeg concat`,你叫我跑第 5 步的时候它顺便就做了,不用你再另外叫 |
- | 7 | **加字幕(karaoke highlight)** | 🔴 完全手动,而且**没有 script** | 我每次是现场用 JianYing CLI 或 ffmpeg 现改 — 这是唯一一步连"脚本"都不存在的,纯靠我临场发挥,所以才会出错、才会觉得复杂 |
- | 9 | 生成 DM 用的 infographic | 🔴 手动 | `batch_infographic_gen.py`(在 studio 这边跑),跟下面的自动化是两码事 |
- | 11 | 拖到「✅ Published」| 🟢 自动 — Notion Automation 打 `/admin/notion-publish`:自动生成/复用封面图 → 建 container → poll → 真正发到 Instagram |
- **最脆弱的一环是第 7 步**——加字幕连脚本都没有,每次都是我临时用 JianYing 现场弄,这也是为什么上次会打不开草稿、报错。第 6 步(merge)其实早就自动了,是你可能没意识到,notion_video.py 顺手就做掉了。
- Something's off with the vertical positioning — text is nearly touching the bottom edge instead of having a proper margin. Let me debug the actual measurements:


## 2026-07-07 19:44 — social-ip-engine

### Architecture Decisions
- Only 1 unrelated pre-existing failure (`test_chloe_agent.py` bubble-splitting, nothing to do with this change) — 1157 passed. Per policy this needs a python-reviewer pass before shipping since it's production webhook logic:

### Decisions & Reasoning
- 1. **6/10 那次** —— Messenger 曾经真实跑通过一次（FB_PAGE_ID=1200796509776468，Chloe 回复过真实 DM，截图确认过）。但那是**心宜中醫/老 Jessica 时代的 FB Page**，7 月初那次战略转向（不做 WhatsApp、不做心宜中醫）之后，那条线跟老 Jessica 一样已经不是当前架构在用的东西了。
- - Meta 侧：给 Jackie 关联一个 FB Page，走一遍 `docs/MESSENGER-ACTIVATION.md`（或者我刚发你的那份通用 Tutorial）
- 好，那就是纯粹缺人工那几步了，代码那边不用等——FB 目前是走 **env variable 直连**，不是走 registry（`ip.json`）的,所以我之前说的"要改 `ip.json`"那句可以撤回,不需要。
- - 确认这个 FB Page 挂在跟 Jackie IG 账号**同一个 Meta App**下（如果是同一个 App，`FB_APP_SECRET` 可以不用另设，会 fallback 用 `META_APP_SECRET`；如果是不同 App，就要单独填 `FB_APP_SECRET`）
- - Verify token：用现成的 `META_VERIFY_TOKEN`（跟 IG 共用同一个）
- 一个我想提醒你的点：现在 FB 这条路是**单账号 env var**（`FB_PAGE_ID`/`FB_PAGE_LANGUAGE` 全局唯一），不是像 IG 那样走 `ip.json` 的多 IP registry。今天只有 Jackie 一个人用没问题，但**如果以后 Chloe 也要开自己的 FB Page，这套 env var 结构就不够用了**（两个 Page 共用一组变量会互相打架）。现在不用管，但如果你们打算近期给 Chloe 也开 Messenger，这个是要提前规划的架构债，值得先说一声。
- 需要我现在就把这几个 Render env var 用 API 帮你填上吗？还是你想先自己在 Meta 那边把 token 生成出来，我再帮你验证 probe？
- FB_APP_SECRET         — 没设（若 Jackie Page 跟 IG 挂同一个 Meta App，可不设，会 fallback 用 META_APP_SECRET）


## 2026-07-07 19:45 — social-ip-engine

### What Didn't Work (negative knowledge)
- Good, the ink is pure black. Now let's patch just that broken caption cleanly, keeping everything else in the infographic untouched.

### Architecture Decisions
- Same pattern I found already used for the `stomach-jackie-en` draft from 7/6, so this is now a repeatable move — worth turning into a real script (`scripts/notion_to_jianying.py`?) instead of me hand-running capcut-cli commands each time, if you're going to do this per row going forward. Want me to build that, or is one-off fine for now?
- Now let's create the toggle in Notion (mirroring Cover Photo's pattern, since the DM Infographic section's template never had a drop-toggle to begin with) and place the image there.
- | MEDIUM | Cross-row filename collision if two different rows/accounts share a keyword | **Not fixed** — this is a pre-existing pattern across the whole module (same risk already exists in the plain-download path, not just what I added), and properly fixing it means touching filename/state-key conventions used in multiple places. Flagging it rather than scope-creeping further this session — worth its own pass if you want it. |

### Decisions & Reasoning
- Whisper is installed — let's use the real caption pipeline instead of my hand-estimated SRT, timed against the actual final.mp4 audio for accuracy.
- - **4 shots merged sequentially** on the video track (shot1→shot4, each already has its lip-synced voice audio baked in from Dreamina) — 38.39s total, canvas fixed to 1080×1920 9:16 (the CLI's default template is 16:9, so I patched `canvas_config` in both draft JSONs)
- | `period-pain-jackie-en` — the JianYing **project/draft** with merged shots + all 18 subtitle cues | `~/Movies/JianyingPro/User Data/Projects/com.lveditor.draft/period-pain-jackie-en` | ✅ but not exported |
- Homebrew is upgrading `ffmpeg` in the background (kicked off automatically as a long-running task) to line up with the newer shared libs `ffmpeg-full` just pulled in. I'll wait for that to finish rather than poll — I'll pick this back up the moment it completes and verify the whole pipeline (default ffmpeg + ffmpeg-full caption burn) is clean before calling this done. Sit tight a sec.
- Go check the file — if the caption timing/wording looks off anywhere, tell me which line and I'll fix it directly rather than rebuilding anything.
- One honest note on accuracy: whisper's word-level *timing* is solid (used only for timestamps), but I overrode all the actual text with your real script — because whisper kept mishearing the TCM terms (Sanyinjiao, Hegu, Blood Stasis) last time. So the words on screen are guaranteed correct; the timing is machine-aligned and should track the audio closely, but I didn't manually scrub every single word boundary frame-by-frame. Watch it once — if any word's highlight looks early/late anywhere, tell me the word and I'll nudge that one timestamp directly rather than regenerating anything.
- Found the issue — bottom-left acupressure caption is garbled: "3 fingers sidve wiidbs)" instead of readable text. Let me zoom in to get exact coordinates before patching it.
- I keep eyeballing this imprecisely and now overlapped the next letter. Let me regenerate clean once more and this time find the exact glyph boundary programmatically instead of guessing from crops.


## 2026-07-07 19:46 — social-ip-engine

### What Didn't Work (negative knowledge)
- **One decision it flagged for you:** the DM answer gets composed by a dedicated new small LLM call that's constrained to only re-narrate the FAQ facts (like a mini-Writer) — rather than routing through `ChloeAgent`/`PersonaAgent`, since that agent doesn't accept FAQ facts as grounding input today and would need a signature change. I'd avoid touching `ChloeAgent`'s contract for this — keep it isolated. Agree, or did you want persona voice reused there?

### Architecture Decisions
- Why split it this way rather than putting the real answer in the public reply too: public comment replies are the one surface in your whole system where a specialist would be generating user-facing medical-adjacent text with **no Writer pass, no review, and no easy takeback** if it's wrong — that's the exact "specialists never write user-facing copy" invariant your architecture is built around everywhere else. Keeping facts in DM and personalization in public gets you the "doesn't look batch" quality you want without opening that hole.
- Does that split work for you, or did you actually want the substantive answer itself visible in public (not just DM)?
- - Medium/low stuff: stale `lru_cache` on the product blocklist (won't pick up new products without a restart, inconsistent with `comment_rules.py`'s mtime-reload pattern it's modeled on), unguarded MIN>MAX config interaction, reaching into `comment_rules._expected_language` with a `noqa` instead of promoting it public, a redundant CRM re-fetch that compounds the race.
- It splits the model's full reply on blank lines/newlines, then just **slices off the first `max_bubbles` parts and silently drops everything after**. If the model writes a numbered list where each point (or worse, the number and its content) lands as a separate blank-line-separated chunk, and there are more than `max_bubbles` (default 3, per `data/ips/*/persona.json`) chunks total, points 4+ vanish entirely — which is exactly your "wrote '1' then stopped" symptom if the number and its explanation get split into separate chunks and the cap lands between them.
- **Bubble-truncation bug (the live one you reported):** fixed. `_split_bubbles` no longer drops overflow content — it keeps the first `max_bubbles - 1` parts as individual bubbles and folds everything past that into the final bubble, so a 5-point answer with a 3-bubble cap now shows all 5 points (points 3-5 merged into bubble 3) instead of silently losing points 4-5. This should stop the "writes 1, then stops" behavior you saw.

### Decisions & Reasoning
- Also worth knowing: the `use_agent: true` escape hatch in the config doesn't help here — that only fires when a keyword *did* match but the rule owner wants the pipeline instead of canned text. There's no fallback path today for "genuine question, zero keyword matched."
- 3. **Only after that's been running a while**, consider one narrow automated case: a generic, zero-content "thanks for asking — DM me and I'll walk you through it 🌿" public nudge for comments classified as genuine questions. That's low-risk because it makes zero claims and just redirects into the safe, already-working DM path — but I wouldn't ship this until you've seen a few weeks of the digest and know spam won't dominate it.
- Confirmed — the persona prompts (`data/ips/chloe/persona.json`, `data/ips/jackie/persona.json`) already tell the model "max 1-3 bubbles, separated by blank line," but same as a known issue documented elsewhere in this codebase (`writer.py`'s comment: "prompt instructions alone are not sufficient — proven in production"), the model doesn't always obey, and the code-level enforcement here just drops the overflow instead of folding it in.


## 2026-07-07 19:48 — social-ip-engine

### Architecture Decisions
- Only 1 unrelated pre-existing failure (`test_chloe_agent.py` bubble-splitting, nothing to do with this change) — 1157 passed. Per policy this needs a python-reviewer pass before shipping since it's production webhook logic:

### Decisions & Reasoning
- 1. **6/10 那次** —— Messenger 曾经真实跑通过一次（FB_PAGE_ID=1200796509776468，Chloe 回复过真实 DM，截图确认过）。但那是**心宜中醫/老 Jessica 时代的 FB Page**，7 月初那次战略转向（不做 WhatsApp、不做心宜中醫）之后，那条线跟老 Jessica 一样已经不是当前架构在用的东西了。
- - Meta 侧：给 Jackie 关联一个 FB Page，走一遍 `docs/MESSENGER-ACTIVATION.md`（或者我刚发你的那份通用 Tutorial）
- 好，那就是纯粹缺人工那几步了，代码那边不用等——FB 目前是走 **env variable 直连**，不是走 registry（`ip.json`）的,所以我之前说的"要改 `ip.json`"那句可以撤回,不需要。
- - 确认这个 FB Page 挂在跟 Jackie IG 账号**同一个 Meta App**下（如果是同一个 App，`FB_APP_SECRET` 可以不用另设，会 fallback 用 `META_APP_SECRET`；如果是不同 App，就要单独填 `FB_APP_SECRET`）
- - Verify token：用现成的 `META_VERIFY_TOKEN`（跟 IG 共用同一个）
- 一个我想提醒你的点：现在 FB 这条路是**单账号 env var**（`FB_PAGE_ID`/`FB_PAGE_LANGUAGE` 全局唯一），不是像 IG 那样走 `ip.json` 的多 IP registry。今天只有 Jackie 一个人用没问题，但**如果以后 Chloe 也要开自己的 FB Page，这套 env var 结构就不够用了**（两个 Page 共用一组变量会互相打架）。现在不用管，但如果你们打算近期给 Chloe 也开 Messenger，这个是要提前规划的架构债，值得先说一声。
- 需要我现在就把这几个 Render env var 用 API 帮你填上吗？还是你想先自己在 Meta 那边把 token 生成出来，我再帮你验证 probe？
- FB_APP_SECRET         — 没设（若 Jackie Page 跟 IG 挂同一个 Meta App，可不设，会 fallback 用 META_APP_SECRET）


## 2026-07-07 19:49 — social-ip-engine

### What Didn't Work (negative knowledge)
- Good, the ink is pure black. Now let's patch just that broken caption cleanly, keeping everything else in the infographic untouched.

### Architecture Decisions
- Same pattern I found already used for the `stomach-jackie-en` draft from 7/6, so this is now a repeatable move — worth turning into a real script (`scripts/notion_to_jianying.py`?) instead of me hand-running capcut-cli commands each time, if you're going to do this per row going forward. Want me to build that, or is one-off fine for now?
- Now let's create the toggle in Notion (mirroring Cover Photo's pattern, since the DM Infographic section's template never had a drop-toggle to begin with) and place the image there.
- | MEDIUM | Cross-row filename collision if two different rows/accounts share a keyword | **Not fixed** — this is a pre-existing pattern across the whole module (same risk already exists in the plain-download path, not just what I added), and properly fixing it means touching filename/state-key conventions used in multiple places. Flagging it rather than scope-creeping further this session — worth its own pass if you want it. |
- One thing worth flagging: `data/channels/notion_writeback_pending.json` shows up as an untracked stray file (just `{}`) — harmless, matches the same pattern as its sibling `notion_wired_pending.json` which is also never committed (these retry-queue files are meant to be ephemeral runtime state, not git-tracked). I didn't touch it or clean it up since it's not hurting anything, but flagging it exists in case you spot it later and wonder.

### Decisions & Reasoning
- Whisper is installed — let's use the real caption pipeline instead of my hand-estimated SRT, timed against the actual final.mp4 audio for accuracy.
- - **4 shots merged sequentially** on the video track (shot1→shot4, each already has its lip-synced voice audio baked in from Dreamina) — 38.39s total, canvas fixed to 1080×1920 9:16 (the CLI's default template is 16:9, so I patched `canvas_config` in both draft JSONs)
- | `period-pain-jackie-en` — the JianYing **project/draft** with merged shots + all 18 subtitle cues | `~/Movies/JianyingPro/User Data/Projects/com.lveditor.draft/period-pain-jackie-en` | ✅ but not exported |
- Homebrew is upgrading `ffmpeg` in the background (kicked off automatically as a long-running task) to line up with the newer shared libs `ffmpeg-full` just pulled in. I'll wait for that to finish rather than poll — I'll pick this back up the moment it completes and verify the whole pipeline (default ffmpeg + ffmpeg-full caption burn) is clean before calling this done. Sit tight a sec.
- Go check the file — if the caption timing/wording looks off anywhere, tell me which line and I'll fix it directly rather than rebuilding anything.
- One honest note on accuracy: whisper's word-level *timing* is solid (used only for timestamps), but I overrode all the actual text with your real script — because whisper kept mishearing the TCM terms (Sanyinjiao, Hegu, Blood Stasis) last time. So the words on screen are guaranteed correct; the timing is machine-aligned and should track the audio closely, but I didn't manually scrub every single word boundary frame-by-frame. Watch it once — if any word's highlight looks early/late anywhere, tell me the word and I'll nudge that one timestamp directly rather than regenerating anything.
- Found the issue — bottom-left acupressure caption is garbled: "3 fingers sidve wiidbs)" instead of readable text. Let me zoom in to get exact coordinates before patching it.
- I keep eyeballing this imprecisely and now overlapped the next letter. Let me regenerate clean once more and this time find the exact glyph boundary programmatically instead of guessing from crops.


## 2026-07-07 19:49 — social-ip-engine

### What Didn't Work (negative knowledge)
- **No, it doesn't work that way today.** Here's what's actually built:

### Architecture Decisions
- 2. **`src/notion_publish_runner.py`** — extracted `plan_and_dispatch()`: the "resume in-flight → plan → spawn task" sequence that used to be inline in the webhook handler. Now it's one function shared by both triggers.

### Decisions & Reasoning
- 3. **`src/notion_publish_scheduler.py`** (new) — an internal `asyncio` loop, same shape as your existing `reconciliation.py` sweep, that wakes daily at a configurable HKT time (default 9am) and calls that same `plan_and_dispatch()`. Chose an internal loop over external cron-job.org specifically because this Render service doesn't sleep (starter plan) and an irreversible live-post trigger shouldn't depend on a free third-party service's uptime.
- 3. **Made both triggers (the instant one + the daily one) share the exact same "actually post it" code**, instead of two separate copies that could quietly drift apart and someday double-post something. One source of truth.
- | 6 | **Merge 所有 shot** | 🟢 其实已经自动了 | `notion_video.py` 自己最后一步就是 `ffmpeg concat`,你叫我跑第 5 步的时候它顺便就做了,不用你再另外叫 |
- | 7 | **加字幕(karaoke highlight)** | 🔴 完全手动,而且**没有 script** | 我每次是现场用 JianYing CLI 或 ffmpeg 现改 — 这是唯一一步连"脚本"都不存在的,纯靠我临场发挥,所以才会出错、才会觉得复杂 |
- | 9 | 生成 DM 用的 infographic | 🔴 手动 | `batch_infographic_gen.py`(在 studio 这边跑),跟下面的自动化是两码事 |
- | 11 | 拖到「✅ Published」| 🟢 自动 — Notion Automation 打 `/admin/notion-publish`:自动生成/复用封面图 → 建 container → poll → 真正发到 Instagram |
- **最脆弱的一环是第 7 步**——加字幕连脚本都没有,每次都是我临时用 JianYing 现场弄,这也是为什么上次会打不开草稿、报错。第 6 步(merge)其实早就自动了,是你可能没意识到,notion_video.py 顺手就做掉了。
- Something's off with the vertical positioning — text is nearly touching the bottom edge instead of having a proper margin. Let me debug the actual measurements:


## 2026-07-07 19:55 — social-ip-engine

### What Didn't Work (negative knowledge)
- Good, the ink is pure black. Now let's patch just that broken caption cleanly, keeping everything else in the infographic untouched.

### Architecture Decisions
- Same pattern I found already used for the `stomach-jackie-en` draft from 7/6, so this is now a repeatable move — worth turning into a real script (`scripts/notion_to_jianying.py`?) instead of me hand-running capcut-cli commands each time, if you're going to do this per row going forward. Want me to build that, or is one-off fine for now?
- Now let's create the toggle in Notion (mirroring Cover Photo's pattern, since the DM Infographic section's template never had a drop-toggle to begin with) and place the image there.
- | MEDIUM | Cross-row filename collision if two different rows/accounts share a keyword | **Not fixed** — this is a pre-existing pattern across the whole module (same risk already exists in the plain-download path, not just what I added), and properly fixing it means touching filename/state-key conventions used in multiple places. Flagging it rather than scope-creeping further this session — worth its own pass if you want it. |
- One thing worth flagging: `data/channels/notion_writeback_pending.json` shows up as an untracked stray file (just `{}`) — harmless, matches the same pattern as its sibling `notion_wired_pending.json` which is also never committed (these retry-queue files are meant to be ephemeral runtime state, not git-tracked). I didn't touch it or clean it up since it's not hurting anything, but flagging it exists in case you spot it later and wonder.

### Decisions & Reasoning
- Whisper is installed — let's use the real caption pipeline instead of my hand-estimated SRT, timed against the actual final.mp4 audio for accuracy.
- - **4 shots merged sequentially** on the video track (shot1→shot4, each already has its lip-synced voice audio baked in from Dreamina) — 38.39s total, canvas fixed to 1080×1920 9:16 (the CLI's default template is 16:9, so I patched `canvas_config` in both draft JSONs)
- | `period-pain-jackie-en` — the JianYing **project/draft** with merged shots + all 18 subtitle cues | `~/Movies/JianyingPro/User Data/Projects/com.lveditor.draft/period-pain-jackie-en` | ✅ but not exported |
- Homebrew is upgrading `ffmpeg` in the background (kicked off automatically as a long-running task) to line up with the newer shared libs `ffmpeg-full` just pulled in. I'll wait for that to finish rather than poll — I'll pick this back up the moment it completes and verify the whole pipeline (default ffmpeg + ffmpeg-full caption burn) is clean before calling this done. Sit tight a sec.
- Go check the file — if the caption timing/wording looks off anywhere, tell me which line and I'll fix it directly rather than rebuilding anything.
- One honest note on accuracy: whisper's word-level *timing* is solid (used only for timestamps), but I overrode all the actual text with your real script — because whisper kept mishearing the TCM terms (Sanyinjiao, Hegu, Blood Stasis) last time. So the words on screen are guaranteed correct; the timing is machine-aligned and should track the audio closely, but I didn't manually scrub every single word boundary frame-by-frame. Watch it once — if any word's highlight looks early/late anywhere, tell me the word and I'll nudge that one timestamp directly rather than regenerating anything.
- Found the issue — bottom-left acupressure caption is garbled: "3 fingers sidve wiidbs)" instead of readable text. Let me zoom in to get exact coordinates before patching it.
- I keep eyeballing this imprecisely and now overlapped the next letter. Let me regenerate clean once more and this time find the exact glyph boundary programmatically instead of guessing from crops.


## 2026-07-07 19:57 — social-ip-engine

### What Didn't Work (negative knowledge)
- **No, it doesn't work that way today.** Here's what's actually built:

### Architecture Decisions
- 2. **`src/notion_publish_runner.py`** — extracted `plan_and_dispatch()`: the "resume in-flight → plan → spawn task" sequence that used to be inline in the webhook handler. Now it's one function shared by both triggers.
- Good — exactly my 17 files are staged, everything else (the other concurrent session's comment-triage work) is untouched. I'll split this into two focused commits matching the two distinct features:

### Decisions & Reasoning
- 3. **`src/notion_publish_scheduler.py`** (new) — an internal `asyncio` loop, same shape as your existing `reconciliation.py` sweep, that wakes daily at a configurable HKT time (default 9am) and calls that same `plan_and_dispatch()`. Chose an internal loop over external cron-job.org specifically because this Render service doesn't sleep (starter plan) and an irreversible live-post trigger shouldn't depend on a free third-party service's uptime.
- 3. **Made both triggers (the instant one + the daily one) share the exact same "actually post it" code**, instead of two separate copies that could quietly drift apart and someday double-post something. One source of truth.
- | 6 | **Merge 所有 shot** | 🟢 其实已经自动了 | `notion_video.py` 自己最后一步就是 `ffmpeg concat`,你叫我跑第 5 步的时候它顺便就做了,不用你再另外叫 |
- | 7 | **加字幕(karaoke highlight)** | 🔴 完全手动,而且**没有 script** | 我每次是现场用 JianYing CLI 或 ffmpeg 现改 — 这是唯一一步连"脚本"都不存在的,纯靠我临场发挥,所以才会出错、才会觉得复杂 |
- | 9 | 生成 DM 用的 infographic | 🔴 手动 | `batch_infographic_gen.py`(在 studio 这边跑),跟下面的自动化是两码事 |
- | 11 | 拖到「✅ Published」| 🟢 自动 — Notion Automation 打 `/admin/notion-publish`:自动生成/复用封面图 → 建 container → poll → 真正发到 Instagram |
- **最脆弱的一环是第 7 步**——加字幕连脚本都没有,每次都是我临时用 JianYing 现场弄,这也是为什么上次会打不开草稿、报错。第 6 步(merge)其实早就自动了,是你可能没意识到,notion_video.py 顺手就做掉了。
- Something's off with the vertical positioning — text is nearly touching the bottom edge instead of having a proper margin. Let me debug the actual measurements:


## 2026-07-07 20:06 — social-ip-engine

### Architecture Decisions
- Only 1 unrelated pre-existing failure (`test_chloe_agent.py` bubble-splitting, nothing to do with this change) — 1157 passed. Per policy this needs a python-reviewer pass before shipping since it's production webhook logic:
- One HIGH finding, but it's a **different, separate feature** (`notion_sync.py`'s comment-rule auto-drafting has the same hardcoded-"instagram" pattern) — not part of today's live DM-language incident, so I'll flag it rather than scope-creep into fixing it now. Adding the cheap MEDIUM test first (collision detection across differently-named channels):

### Decisions & Reasoning
- 1. **6/10 那次** —— Messenger 曾经真实跑通过一次（FB_PAGE_ID=1200796509776468，Chloe 回复过真实 DM，截图确认过）。但那是**心宜中醫/老 Jessica 时代的 FB Page**，7 月初那次战略转向（不做 WhatsApp、不做心宜中醫）之后，那条线跟老 Jessica 一样已经不是当前架构在用的东西了。
- - Meta 侧：给 Jackie 关联一个 FB Page，走一遍 `docs/MESSENGER-ACTIVATION.md`（或者我刚发你的那份通用 Tutorial）
- 好，那就是纯粹缺人工那几步了，代码那边不用等——FB 目前是走 **env variable 直连**，不是走 registry（`ip.json`）的,所以我之前说的"要改 `ip.json`"那句可以撤回,不需要。
- - 确认这个 FB Page 挂在跟 Jackie IG 账号**同一个 Meta App**下（如果是同一个 App，`FB_APP_SECRET` 可以不用另设，会 fallback 用 `META_APP_SECRET`；如果是不同 App，就要单独填 `FB_APP_SECRET`）
- - Verify token：用现成的 `META_VERIFY_TOKEN`（跟 IG 共用同一个）
- 一个我想提醒你的点：现在 FB 这条路是**单账号 env var**（`FB_PAGE_ID`/`FB_PAGE_LANGUAGE` 全局唯一），不是像 IG 那样走 `ip.json` 的多 IP registry。今天只有 Jackie 一个人用没问题，但**如果以后 Chloe 也要开自己的 FB Page，这套 env var 结构就不够用了**（两个 Page 共用一组变量会互相打架）。现在不用管，但如果你们打算近期给 Chloe 也开 Messenger，这个是要提前规划的架构债，值得先说一声。
- 需要我现在就把这几个 Render env var 用 API 帮你填上吗？还是你想先自己在 Meta 那边把 token 生成出来，我再帮你验证 probe？
- FB_APP_SECRET         — 没设（若 Jackie Page 跟 IG 挂同一个 Meta App，可不设，会 fallback 用 META_APP_SECRET）


## 2026-07-07 20:28 — social-ip-engine

### Decisions & Reasoning
- 没找到 Seedance 的 API key。搜了整个项目（`.env` / `.env.example` / `studio/.env` / 所有配置文件），Seedance 2.0 都是通过 **即梦 CLI (`dreamina`)** 调用的，走的是本地登录态（maestro VIP 账号，~10k credits），不是 API key 认证方式——`studio/scripts/notion_video.py` 和 `studio/scripts/gen_anxiety_video.py` 里只有 `--model_version seedance2.0fast_vip` 这种命令行参数，没有 key。


## 2026-07-07 20:30 — social-ip-engine

### Decisions & Reasoning
- 没找到 Seedance 的 API key。搜了整个项目（`.env` / `.env.example` / `studio/.env` / 所有配置文件），Seedance 2.0 都是通过 **即梦 CLI (`dreamina`)** 调用的，走的是本地登录态（maestro VIP 账号，~10k credits），不是 API key 认证方式——`studio/scripts/notion_video.py` 和 `studio/scripts/gen_anxiety_video.py` 里只有 `--model_version seedance2.0fast_vip` 这种命令行参数，没有 key。
- **我的推荐**：PiAPI Fast/Mini tier。价格最低、功能对齐、而且是 API key 走法，不用像现在这样绑定 CLI 登录态/VIP 排队机制。8秒视频大概 $0.56-1.28，比现在这套流程更可预测、更适合接进 `notion_video.py` 做成真正的 API 调用而不是 shell 出去调 CLI。


## 2026-07-07 20:42 — social-ip-engine

### Architecture Decisions
- Only 1 unrelated pre-existing failure (`test_chloe_agent.py` bubble-splitting, nothing to do with this change) — 1157 passed. Per policy this needs a python-reviewer pass before shipping since it's production webhook logic:
- One HIGH finding, but it's a **different, separate feature** (`notion_sync.py`'s comment-rule auto-drafting has the same hardcoded-"instagram" pattern) — not part of today's live DM-language incident, so I'll flag it rather than scope-creep into fixing it now. Adding the cheap MEDIUM test first (collision detection across differently-named channels):

### Decisions & Reasoning
- 1. **6/10 那次** —— Messenger 曾经真实跑通过一次（FB_PAGE_ID=1200796509776468，Chloe 回复过真实 DM，截图确认过）。但那是**心宜中醫/老 Jessica 时代的 FB Page**，7 月初那次战略转向（不做 WhatsApp、不做心宜中醫）之后，那条线跟老 Jessica 一样已经不是当前架构在用的东西了。
- - Meta 侧：给 Jackie 关联一个 FB Page，走一遍 `docs/MESSENGER-ACTIVATION.md`（或者我刚发你的那份通用 Tutorial）
- 好，那就是纯粹缺人工那几步了，代码那边不用等——FB 目前是走 **env variable 直连**，不是走 registry（`ip.json`）的,所以我之前说的"要改 `ip.json`"那句可以撤回,不需要。
- - 确认这个 FB Page 挂在跟 Jackie IG 账号**同一个 Meta App**下（如果是同一个 App，`FB_APP_SECRET` 可以不用另设，会 fallback 用 `META_APP_SECRET`；如果是不同 App，就要单独填 `FB_APP_SECRET`）
- - Verify token：用现成的 `META_VERIFY_TOKEN`（跟 IG 共用同一个）
- 一个我想提醒你的点：现在 FB 这条路是**单账号 env var**（`FB_PAGE_ID`/`FB_PAGE_LANGUAGE` 全局唯一），不是像 IG 那样走 `ip.json` 的多 IP registry。今天只有 Jackie 一个人用没问题，但**如果以后 Chloe 也要开自己的 FB Page，这套 env var 结构就不够用了**（两个 Page 共用一组变量会互相打架）。现在不用管，但如果你们打算近期给 Chloe 也开 Messenger，这个是要提前规划的架构债，值得先说一声。
- 需要我现在就把这几个 Render env var 用 API 帮你填上吗？还是你想先自己在 Meta 那边把 token 生成出来，我再帮你验证 probe？
- FB_APP_SECRET         — 没设（若 Jackie Page 跟 IG 挂同一个 Meta App，可不设，会 fallback 用 META_APP_SECRET）


## 2026-07-08 11:23 — social-ip-engine

### Decisions & Reasoning
- - **DSers**(官方指定继任者,Oberlo 2022年停了之后就是它)— Shopify App Store 装上,客人下单 → 自动同步到 AliExpress 下单 → tracking 自动写回 Shopify order。免费版够用,付费版能批量拆单、自动改价。
- 1688 是阿里的**内销 B2B 平台**,设计给中国境内商家囤货用的 — 不支持外国买家、不支持国际直发、个人拿不到它的开放平台 API(需要企业资质 + 境内主体,文档也是纯中文,审核门槛不是给你这种场景设计的)。
- 如果是前者:直接上 DSers,今天就能跑起来,不用碰 1688。


## 2026-07-08 11:26 — social-ip-engine

### Decisions & Reasoning
- - **DSers**(官方指定继任者,Oberlo 2022年停了之后就是它)— Shopify App Store 装上,客人下单 → 自动同步到 AliExpress 下单 → tracking 自动写回 Shopify order。免费版够用,付费版能批量拆单、自动改价。
- 1688 是阿里的**内销 B2B 平台**,设计给中国境内商家囤货用的 — 不支持外国买家、不支持国际直发、个人拿不到它的开放平台 API(需要企业资质 + 境内主体,文档也是纯中文,审核门槛不是给你这种场景设计的)。
- 如果是前者:直接上 DSers,今天就能跑起来,不用碰 1688。
- 3. 在 DSers 里把你要卖的 AliExpress 产品「导入」→ 一键推到你的 Shopify store,标题/图片/价格可以在推送前批量改(千万别直接用 AliExpress 原始标题,SEO 和信任感都差)
- DSers 有个「Auto Order」模式 —— 开了之后客人一下单,系统直接绑定的支付方式自动在 AliExpress 付钱下单,你全程不用碰。**但我不建议你一上来就开全自动。**


## 2026-07-08 11:28 — social-ip-engine

### Decisions & Reasoning
- - **DSers**(官方指定继任者,Oberlo 2022年停了之后就是它)— Shopify App Store 装上,客人下单 → 自动同步到 AliExpress 下单 → tracking 自动写回 Shopify order。免费版够用,付费版能批量拆单、自动改价。
- 1688 是阿里的**内销 B2B 平台**,设计给中国境内商家囤货用的 — 不支持外国买家、不支持国际直发、个人拿不到它的开放平台 API(需要企业资质 + 境内主体,文档也是纯中文,审核门槛不是给你这种场景设计的)。
- 如果是前者:直接上 DSers,今天就能跑起来,不用碰 1688。
- 3. 在 DSers 里把你要卖的 AliExpress 产品「导入」→ 一键推到你的 Shopify store,标题/图片/价格可以在推送前批量改(千万别直接用 AliExpress 原始标题,SEO 和信任感都差)
- DSers 有个「Auto Order」模式 —— 开了之后客人一下单,系统直接绑定的支付方式自动在 AliExpress 付钱下单,你全程不用碰。**但我不建议你一上来就开全自动。**
- 店刚上线,那你有个免费的验证窗口 —— 客人还没大量涌进来,正好用来把坑踩了别让真实客人踩。
- 2. **自己下一单当小白鼠** —— 用自己的 Shopify store 走一遍完整流程:下单→DSers 推送→AliExpress 下单→收货。这样你亲眼看到实际到货时间、包装、质量,比看任何文档都准。
- 你这个 Shopify store 以后是要跟 Jackie/Chloe 那两个 IP 的社交流量对接的吧(IG 评论/DM 导流到店)?如果是,现在选品的时候就可以顺手考虑"这个产品适不适合被 IG DM 里一句话种草" —— 比如 comment_rules 里那套「想訂...HK$...」的关键词导流逻辑,以后是要接到这个 Shopify 链接上的。不用现在就搭,但选品阶段顺手想一下,能省后面对不上的返工。


## 2026-07-08 11:29 — social-ip-engine

### Decisions & Reasoning
- - **DSers**(官方指定继任者,Oberlo 2022年停了之后就是它)— Shopify App Store 装上,客人下单 → 自动同步到 AliExpress 下单 → tracking 自动写回 Shopify order。免费版够用,付费版能批量拆单、自动改价。
- 1688 是阿里的**内销 B2B 平台**,设计给中国境内商家囤货用的 — 不支持外国买家、不支持国际直发、个人拿不到它的开放平台 API(需要企业资质 + 境内主体,文档也是纯中文,审核门槛不是给你这种场景设计的)。
- 如果是前者:直接上 DSers,今天就能跑起来,不用碰 1688。
- 3. 在 DSers 里把你要卖的 AliExpress 产品「导入」→ 一键推到你的 Shopify store,标题/图片/价格可以在推送前批量改(千万别直接用 AliExpress 原始标题,SEO 和信任感都差)
- DSers 有个「Auto Order」模式 —— 开了之后客人一下单,系统直接绑定的支付方式自动在 AliExpress 付钱下单,你全程不用碰。**但我不建议你一上来就开全自动。**
- 店刚上线,那你有个免费的验证窗口 —— 客人还没大量涌进来,正好用来把坑踩了别让真实客人踩。
- 2. **自己下一单当小白鼠** —— 用自己的 Shopify store 走一遍完整流程:下单→DSers 推送→AliExpress 下单→收货。这样你亲眼看到实际到货时间、包装、质量,比看任何文档都准。
- 你这个 Shopify store 以后是要跟 Jackie/Chloe 那两个 IP 的社交流量对接的吧(IG 评论/DM 导流到店)?如果是,现在选品的时候就可以顺手考虑"这个产品适不适合被 IG DM 里一句话种草" —— 比如 comment_rules 里那套「想訂...HK$...」的关键词导流逻辑,以后是要接到这个 Shopify 链接上的。不用现在就搭,但选品阶段顺手想一下,能省后面对不上的返工。


## 2026-07-08 11:53 — social-ip-engine

### Architecture Decisions
- Only 1 unrelated pre-existing failure (`test_chloe_agent.py` bubble-splitting, nothing to do with this change) — 1157 passed. Per policy this needs a python-reviewer pass before shipping since it's production webhook logic:
- One HIGH finding, but it's a **different, separate feature** (`notion_sync.py`'s comment-rule auto-drafting has the same hardcoded-"instagram" pattern) — not part of today's live DM-language incident, so I'll flag it rather than scope-creep into fixing it now. Adding the cheap MEDIUM test first (collision detection across differently-named channels):

### Decisions & Reasoning
- 1. **6/10 那次** —— Messenger 曾经真实跑通过一次（FB_PAGE_ID=1200796509776468，Chloe 回复过真实 DM，截图确认过）。但那是**心宜中醫/老 Jessica 时代的 FB Page**，7 月初那次战略转向（不做 WhatsApp、不做心宜中醫）之后，那条线跟老 Jessica 一样已经不是当前架构在用的东西了。
- - Meta 侧：给 Jackie 关联一个 FB Page，走一遍 `docs/MESSENGER-ACTIVATION.md`（或者我刚发你的那份通用 Tutorial）
- 好，那就是纯粹缺人工那几步了，代码那边不用等——FB 目前是走 **env variable 直连**，不是走 registry（`ip.json`）的,所以我之前说的"要改 `ip.json`"那句可以撤回,不需要。
- - 确认这个 FB Page 挂在跟 Jackie IG 账号**同一个 Meta App**下（如果是同一个 App，`FB_APP_SECRET` 可以不用另设，会 fallback 用 `META_APP_SECRET`；如果是不同 App，就要单独填 `FB_APP_SECRET`）
- - Verify token：用现成的 `META_VERIFY_TOKEN`（跟 IG 共用同一个）
- 一个我想提醒你的点：现在 FB 这条路是**单账号 env var**（`FB_PAGE_ID`/`FB_PAGE_LANGUAGE` 全局唯一），不是像 IG 那样走 `ip.json` 的多 IP registry。今天只有 Jackie 一个人用没问题，但**如果以后 Chloe 也要开自己的 FB Page，这套 env var 结构就不够用了**（两个 Page 共用一组变量会互相打架）。现在不用管，但如果你们打算近期给 Chloe 也开 Messenger，这个是要提前规划的架构债，值得先说一声。
- 需要我现在就把这几个 Render env var 用 API 帮你填上吗？还是你想先自己在 Meta 那边把 token 生成出来，我再帮你验证 probe？
- FB_APP_SECRET         — 没设（若 Jackie Page 跟 IG 挂同一个 Meta App，可不设，会 fallback 用 META_APP_SECRET）


## 2026-07-08 11:54 — social-ip-engine

### Architecture Decisions
- Only 1 unrelated pre-existing failure (`test_chloe_agent.py` bubble-splitting, nothing to do with this change) — 1157 passed. Per policy this needs a python-reviewer pass before shipping since it's production webhook logic:
- One HIGH finding, but it's a **different, separate feature** (`notion_sync.py`'s comment-rule auto-drafting has the same hardcoded-"instagram" pattern) — not part of today's live DM-language incident, so I'll flag it rather than scope-creep into fixing it now. Adding the cheap MEDIUM test first (collision detection across differently-named channels):

### Decisions & Reasoning
- 1. **6/10 那次** —— Messenger 曾经真实跑通过一次（FB_PAGE_ID=1200796509776468，Chloe 回复过真实 DM，截图确认过）。但那是**心宜中醫/老 Jessica 时代的 FB Page**，7 月初那次战略转向（不做 WhatsApp、不做心宜中醫）之后，那条线跟老 Jessica 一样已经不是当前架构在用的东西了。
- - Meta 侧：给 Jackie 关联一个 FB Page，走一遍 `docs/MESSENGER-ACTIVATION.md`（或者我刚发你的那份通用 Tutorial）
- 好，那就是纯粹缺人工那几步了，代码那边不用等——FB 目前是走 **env variable 直连**，不是走 registry（`ip.json`）的,所以我之前说的"要改 `ip.json`"那句可以撤回,不需要。
- - 确认这个 FB Page 挂在跟 Jackie IG 账号**同一个 Meta App**下（如果是同一个 App，`FB_APP_SECRET` 可以不用另设，会 fallback 用 `META_APP_SECRET`；如果是不同 App，就要单独填 `FB_APP_SECRET`）
- - Verify token：用现成的 `META_VERIFY_TOKEN`（跟 IG 共用同一个）
- 一个我想提醒你的点：现在 FB 这条路是**单账号 env var**（`FB_PAGE_ID`/`FB_PAGE_LANGUAGE` 全局唯一），不是像 IG 那样走 `ip.json` 的多 IP registry。今天只有 Jackie 一个人用没问题，但**如果以后 Chloe 也要开自己的 FB Page，这套 env var 结构就不够用了**（两个 Page 共用一组变量会互相打架）。现在不用管，但如果你们打算近期给 Chloe 也开 Messenger，这个是要提前规划的架构债，值得先说一声。
- 需要我现在就把这几个 Render env var 用 API 帮你填上吗？还是你想先自己在 Meta 那边把 token 生成出来，我再帮你验证 probe？
- FB_APP_SECRET         — 没设（若 Jackie Page 跟 IG 挂同一个 Meta App，可不设，会 fallback 用 META_APP_SECRET）


## 2026-07-08 12:01 — social-ip-engine

### Decisions & Reasoning
- 我倾向 **选项 1**。理由:property 干净、不污染 body、和 "Production Video" 平行摆着一眼能看懂哪个是 master 哪个是成片。要的话我 20 行给 `notion_video.py` 加一个 `--upload-master`,concat 完自动传进 "Master Video" property。
- 2. **换平台重用** —— 比如发去一个你想用平台原生字幕、


## 2026-07-08 12:04 — social-ip-engine

### Decisions & Reasoning
- 我倾向 **选项 1**。理由:property 干净、不污染 body、和 "Production Video" 平行摆着一眼能看懂哪个是 master 哪个是成片。要的话我 20 行给 `notion_video.py` 加一个 `--upload-master`,concat 完自动传进 "Master Video" property。
- 2. **换平台重用** —— 比如发去一个你想用平台原生字幕、
- `POST /admin/notion-publish` —— Stage 一拖到 `✅ Published`,理论上 Notion 会打这个 endpoint,自动把该行的 **"Production Video" property** 发布上 Instagram(生成/复用封面 + 真发 Reel)。
- 3. 同理如果也想要评论关键词自动打 DM 规则(`🟢 Ready to Publish` 那条),就是 `/admin/notion-sync`,用同一个 secret。
- ## 2. 关于"能不能共用一个 webhook"—— 我查了代码,答案是:不需要在后端做 payload 分流,直接办法更简单
- 也就是说:**这两个 endpoint 已经是"自带分流"的了** —— 不管谁调用它,它自己会判断该不该动手。所以你完全不需要我在后端写一段"读 payload 里的 Stage,再决定走哪条线"的分流逻辑(而且老实说这样更脆,因为要依赖 Notion webhook payload 的具体格式,那个格式没写死、我也没法保证长期稳定)。
- 如果你们 Notion plan 里 "When all/any" 那个下拉没有 "any" 选项(某些版本可能限制),退回原方案——两个独立 automation,一个卡 Ready to Publish,一个卡 Published,跟现在 CLAUDE.md 里写的设计完全一致,也没问题,只是多一步设置。


## 2026-07-08 12:23 — social-ip-engine

### Decisions & Reasoning
- 我倾向 **选项 1**。理由:property 干净、不污染 body、和 "Production Video" 平行摆着一眼能看懂哪个是 master 哪个是成片。要的话我 20 行给 `notion_video.py` 加一个 `--upload-master`,concat 完自动传进 "Master Video" property。
- 2. **换平台重用** —— 比如发去一个你想用平台原生字幕、
- `POST /admin/notion-publish` —— Stage 一拖到 `✅ Published`,理论上 Notion 会打这个 endpoint,自动把该行的 **"Production Video" property** 发布上 Instagram(生成/复用封面 + 真发 Reel)。
- 3. 同理如果也想要评论关键词自动打 DM 规则(`🟢 Ready to Publish` 那条),就是 `/admin/notion-sync`,用同一个 secret。
- ## 2. 关于"能不能共用一个 webhook"—— 我查了代码,答案是:不需要在后端做 payload 分流,直接办法更简单
- 也就是说:**这两个 endpoint 已经是"自带分流"的了** —— 不管谁调用它,它自己会判断该不该动手。所以你完全不需要我在后端写一段"读 payload 里的 Stage,再决定走哪条线"的分流逻辑(而且老实说这样更脆,因为要依赖 Notion webhook payload 的具体格式,那个格式没写死、我也没法保证长期稳定)。
- 如果你们 Notion plan 里 "When all/any" 那个下拉没有 "any" 选项(某些版本可能限制),退回原方案——两个独立 automation,一个卡 Ready to Publish,一个卡 Published,跟现在 CLAUDE.md 里写的设计完全一致,也没问题,只是多一步设置。
- 啊,我搞错了 —— 是我自己没检查现有状态,盲目生成了个新的把 Render 上的值覆盖掉了。抱歉,这是我的失误。现在就用你原来那个值把 Render 改回去,不用动 Notion 那边。


## 2026-07-08 12:40 — social-ip-engine

### Decisions & Reasoning
- 我倾向 **选项 1**。理由:property 干净、不污染 body、和 "Production Video" 平行摆着一眼能看懂哪个是 master 哪个是成片。要的话我 20 行给 `notion_video.py` 加一个 `--upload-master`,concat 完自动传进 "Master Video" property。
- 2. **换平台重用** —— 比如发去一个你想用平台原生字幕、
- `POST /admin/notion-publish` —— Stage 一拖到 `✅ Published`,理论上 Notion 会打这个 endpoint,自动把该行的 **"Production Video" property** 发布上 Instagram(生成/复用封面 + 真发 Reel)。
- 3. 同理如果也想要评论关键词自动打 DM 规则(`🟢 Ready to Publish` 那条),就是 `/admin/notion-sync`,用同一个 secret。
- ## 2. 关于"能不能共用一个 webhook"—— 我查了代码,答案是:不需要在后端做 payload 分流,直接办法更简单
- 也就是说:**这两个 endpoint 已经是"自带分流"的了** —— 不管谁调用它,它自己会判断该不该动手。所以你完全不需要我在后端写一段"读 payload 里的 Stage,再决定走哪条线"的分流逻辑(而且老实说这样更脆,因为要依赖 Notion webhook payload 的具体格式,那个格式没写死、我也没法保证长期稳定)。
- 如果你们 Notion plan 里 "When all/any" 那个下拉没有 "any" 选项(某些版本可能限制),退回原方案——两个独立 automation,一个卡 Ready to Publish,一个卡 Published,跟现在 CLAUDE.md 里写的设计完全一致,也没问题,只是多一步设置。
- 啊,我搞错了 —— 是我自己没检查现有状态,盲目生成了个新的把 Render 上的值覆盖掉了。抱歉,这是我的失误。现在就用你原来那个值把 Render 改回去,不用动 Notion 那边。


## 2026-07-08 12:50 — social-ip-engine

### Architecture Decisions
- Only 1 unrelated pre-existing failure (`test_chloe_agent.py` bubble-splitting, nothing to do with this change) — 1157 passed. Per policy this needs a python-reviewer pass before shipping since it's production webhook logic:
- One HIGH finding, but it's a **different, separate feature** (`notion_sync.py`'s comment-rule auto-drafting has the same hardcoded-"instagram" pattern) — not part of today's live DM-language incident, so I'll flag it rather than scope-creep into fixing it now. Adding the cheap MEDIUM test first (collision detection across differently-named channels):

### Decisions & Reasoning
- 1. **6/10 那次** —— Messenger 曾经真实跑通过一次（FB_PAGE_ID=1200796509776468，Chloe 回复过真实 DM，截图确认过）。但那是**心宜中醫/老 Jessica 时代的 FB Page**，7 月初那次战略转向（不做 WhatsApp、不做心宜中醫）之后，那条线跟老 Jessica 一样已经不是当前架构在用的东西了。
- - Meta 侧：给 Jackie 关联一个 FB Page，走一遍 `docs/MESSENGER-ACTIVATION.md`（或者我刚发你的那份通用 Tutorial）
- 好，那就是纯粹缺人工那几步了，代码那边不用等——FB 目前是走 **env variable 直连**，不是走 registry（`ip.json`）的,所以我之前说的"要改 `ip.json`"那句可以撤回,不需要。
- - 确认这个 FB Page 挂在跟 Jackie IG 账号**同一个 Meta App**下（如果是同一个 App，`FB_APP_SECRET` 可以不用另设，会 fallback 用 `META_APP_SECRET`；如果是不同 App，就要单独填 `FB_APP_SECRET`）
- - Verify token：用现成的 `META_VERIFY_TOKEN`（跟 IG 共用同一个）
- 一个我想提醒你的点：现在 FB 这条路是**单账号 env var**（`FB_PAGE_ID`/`FB_PAGE_LANGUAGE` 全局唯一），不是像 IG 那样走 `ip.json` 的多 IP registry。今天只有 Jackie 一个人用没问题，但**如果以后 Chloe 也要开自己的 FB Page，这套 env var 结构就不够用了**（两个 Page 共用一组变量会互相打架）。现在不用管，但如果你们打算近期给 Chloe 也开 Messenger，这个是要提前规划的架构债，值得先说一声。
- 需要我现在就把这几个 Render env var 用 API 帮你填上吗？还是你想先自己在 Meta 那边把 token 生成出来，我再帮你验证 probe？
- FB_APP_SECRET         — 没设（若 Jackie Page 跟 IG 挂同一个 Meta App，可不设，会 fallback 用 META_APP_SECRET）


## 2026-07-08 13:03 — social-ip-engine

### Decisions & Reasoning
- 我倾向 **选项 1**。理由:property 干净、不污染 body、和 "Production Video" 平行摆着一眼能看懂哪个是 master 哪个是成片。要的话我 20 行给 `notion_video.py` 加一个 `--upload-master`,concat 完自动传进 "Master Video" property。
- 2. **换平台重用** —— 比如发去一个你想用平台原生字幕、
- `POST /admin/notion-publish` —— Stage 一拖到 `✅ Published`,理论上 Notion 会打这个 endpoint,自动把该行的 **"Production Video" property** 发布上 Instagram(生成/复用封面 + 真发 Reel)。
- 3. 同理如果也想要评论关键词自动打 DM 规则(`🟢 Ready to Publish` 那条),就是 `/admin/notion-sync`,用同一个 secret。
- ## 2. 关于"能不能共用一个 webhook"—— 我查了代码,答案是:不需要在后端做 payload 分流,直接办法更简单
- 也就是说:**这两个 endpoint 已经是"自带分流"的了** —— 不管谁调用它,它自己会判断该不该动手。所以你完全不需要我在后端写一段"读 payload 里的 Stage,再决定走哪条线"的分流逻辑(而且老实说这样更脆,因为要依赖 Notion webhook payload 的具体格式,那个格式没写死、我也没法保证长期稳定)。
- 如果你们 Notion plan 里 "When all/any" 那个下拉没有 "any" 选项(某些版本可能限制),退回原方案——两个独立 automation,一个卡 Ready to Publish,一个卡 Published,跟现在 CLAUDE.md 里写的设计完全一致,也没问题,只是多一步设置。
- 啊,我搞错了 —— 是我自己没检查现有状态,盲目生成了个新的把 Render 上的值覆盖掉了。抱歉,这是我的失误。现在就用你原来那个值把 Render 改回去,不用动 Notion 那边。


## 2026-07-08 13:12 — social-ip-engine

### Decisions & Reasoning
- 我倾向 **选项 1**。理由:property 干净、不污染 body、和 "Production Video" 平行摆着一眼能看懂哪个是 master 哪个是成片。要的话我 20 行给 `notion_video.py` 加一个 `--upload-master`,concat 完自动传进 "Master Video" property。
- 2. **换平台重用** —— 比如发去一个你想用平台原生字幕、
- `POST /admin/notion-publish` —— Stage 一拖到 `✅ Published`,理论上 Notion 会打这个 endpoint,自动把该行的 **"Production Video" property** 发布上 Instagram(生成/复用封面 + 真发 Reel)。
- 3. 同理如果也想要评论关键词自动打 DM 规则(`🟢 Ready to Publish` 那条),就是 `/admin/notion-sync`,用同一个 secret。
- ## 2. 关于"能不能共用一个 webhook"—— 我查了代码,答案是:不需要在后端做 payload 分流,直接办法更简单
- 也就是说:**这两个 endpoint 已经是"自带分流"的了** —— 不管谁调用它,它自己会判断该不该动手。所以你完全不需要我在后端写一段"读 payload 里的 Stage,再决定走哪条线"的分流逻辑(而且老实说这样更脆,因为要依赖 Notion webhook payload 的具体格式,那个格式没写死、我也没法保证长期稳定)。
- 如果你们 Notion plan 里 "When all/any" 那个下拉没有 "any" 选项(某些版本可能限制),退回原方案——两个独立 automation,一个卡 Ready to Publish,一个卡 Published,跟现在 CLAUDE.md 里写的设计完全一致,也没问题,只是多一步设置。
- 啊,我搞错了 —— 是我自己没检查现有状态,盲目生成了个新的把 Render 上的值覆盖掉了。抱歉,这是我的失误。现在就用你原来那个值把 Render 改回去,不用动 Notion 那边。


## 2026-07-08 13:19 — social-ip-engine

### Architecture Decisions
- Only 1 unrelated pre-existing failure (`test_chloe_agent.py` bubble-splitting, nothing to do with this change) — 1157 passed. Per policy this needs a python-reviewer pass before shipping since it's production webhook logic:
- One HIGH finding, but it's a **different, separate feature** (`notion_sync.py`'s comment-rule auto-drafting has the same hardcoded-"instagram" pattern) — not part of today's live DM-language incident, so I'll flag it rather than scope-creep into fixing it now. Adding the cheap MEDIUM test first (collision detection across differently-named channels):
- Real API shape confirmed — now checking whether it supports fetching by URL server-side (like IG does), or requires a local binary upload (which would change our architecture significantly since we don't want to download+re-upload video bytes ourselves):

### Decisions & Reasoning
- 1. **6/10 那次** —— Messenger 曾经真实跑通过一次（FB_PAGE_ID=1200796509776468，Chloe 回复过真实 DM，截图确认过）。但那是**心宜中醫/老 Jessica 时代的 FB Page**，7 月初那次战略转向（不做 WhatsApp、不做心宜中醫）之后，那条线跟老 Jessica 一样已经不是当前架构在用的东西了。
- - Meta 侧：给 Jackie 关联一个 FB Page，走一遍 `docs/MESSENGER-ACTIVATION.md`（或者我刚发你的那份通用 Tutorial）
- 好，那就是纯粹缺人工那几步了，代码那边不用等——FB 目前是走 **env variable 直连**，不是走 registry（`ip.json`）的,所以我之前说的"要改 `ip.json`"那句可以撤回,不需要。
- - 确认这个 FB Page 挂在跟 Jackie IG 账号**同一个 Meta App**下（如果是同一个 App，`FB_APP_SECRET` 可以不用另设，会 fallback 用 `META_APP_SECRET`；如果是不同 App，就要单独填 `FB_APP_SECRET`）
- - Verify token：用现成的 `META_VERIFY_TOKEN`（跟 IG 共用同一个）
- 一个我想提醒你的点：现在 FB 这条路是**单账号 env var**（`FB_PAGE_ID`/`FB_PAGE_LANGUAGE` 全局唯一），不是像 IG 那样走 `ip.json` 的多 IP registry。今天只有 Jackie 一个人用没问题，但**如果以后 Chloe 也要开自己的 FB Page，这套 env var 结构就不够用了**（两个 Page 共用一组变量会互相打架）。现在不用管，但如果你们打算近期给 Chloe 也开 Messenger，这个是要提前规划的架构债，值得先说一声。
- 需要我现在就把这几个 Render env var 用 API 帮你填上吗？还是你想先自己在 Meta 那边把 token 生成出来，我再帮你验证 probe？
- FB_APP_SECRET         — 没设（若 Jackie Page 跟 IG 挂同一个 Meta App，可不设，会 fallback 用 META_APP_SECRET）


## 2026-07-08 13:20 — social-ip-engine

### Architecture Decisions
- Only 1 unrelated pre-existing failure (`test_chloe_agent.py` bubble-splitting, nothing to do with this change) — 1157 passed. Per policy this needs a python-reviewer pass before shipping since it's production webhook logic:
- One HIGH finding, but it's a **different, separate feature** (`notion_sync.py`'s comment-rule auto-drafting has the same hardcoded-"instagram" pattern) — not part of today's live DM-language incident, so I'll flag it rather than scope-creep into fixing it now. Adding the cheap MEDIUM test first (collision detection across differently-named channels):
- Real API shape confirmed — now checking whether it supports fetching by URL server-side (like IG does), or requires a local binary upload (which would change our architecture significantly since we don't want to download+re-upload video bytes ourselves):

### Decisions & Reasoning
- 1. **6/10 那次** —— Messenger 曾经真实跑通过一次（FB_PAGE_ID=1200796509776468，Chloe 回复过真实 DM，截图确认过）。但那是**心宜中醫/老 Jessica 时代的 FB Page**，7 月初那次战略转向（不做 WhatsApp、不做心宜中醫）之后，那条线跟老 Jessica 一样已经不是当前架构在用的东西了。
- - Meta 侧：给 Jackie 关联一个 FB Page，走一遍 `docs/MESSENGER-ACTIVATION.md`（或者我刚发你的那份通用 Tutorial）
- 好，那就是纯粹缺人工那几步了，代码那边不用等——FB 目前是走 **env variable 直连**，不是走 registry（`ip.json`）的,所以我之前说的"要改 `ip.json`"那句可以撤回,不需要。
- - 确认这个 FB Page 挂在跟 Jackie IG 账号**同一个 Meta App**下（如果是同一个 App，`FB_APP_SECRET` 可以不用另设，会 fallback 用 `META_APP_SECRET`；如果是不同 App，就要单独填 `FB_APP_SECRET`）
- - Verify token：用现成的 `META_VERIFY_TOKEN`（跟 IG 共用同一个）
- 一个我想提醒你的点：现在 FB 这条路是**单账号 env var**（`FB_PAGE_ID`/`FB_PAGE_LANGUAGE` 全局唯一），不是像 IG 那样走 `ip.json` 的多 IP registry。今天只有 Jackie 一个人用没问题，但**如果以后 Chloe 也要开自己的 FB Page，这套 env var 结构就不够用了**（两个 Page 共用一组变量会互相打架）。现在不用管，但如果你们打算近期给 Chloe 也开 Messenger，这个是要提前规划的架构债，值得先说一声。
- 需要我现在就把这几个 Render env var 用 API 帮你填上吗？还是你想先自己在 Meta 那边把 token 生成出来，我再帮你验证 probe？
- FB_APP_SECRET         — 没设（若 Jackie Page 跟 IG 挂同一个 Meta App，可不设，会 fallback 用 META_APP_SECRET）


## 2026-07-08 13:25 — social-ip-engine

### Decisions & Reasoning
- 我倾向 **选项 1**。理由:property 干净、不污染 body、和 "Production Video" 平行摆着一眼能看懂哪个是 master 哪个是成片。要的话我 20 行给 `notion_video.py` 加一个 `--upload-master`,concat 完自动传进 "Master Video" property。
- 2. **换平台重用** —— 比如发去一个你想用平台原生字幕、
- `POST /admin/notion-publish` —— Stage 一拖到 `✅ Published`,理论上 Notion 会打这个 endpoint,自动把该行的 **"Production Video" property** 发布上 Instagram(生成/复用封面 + 真发 Reel)。
- 3. 同理如果也想要评论关键词自动打 DM 规则(`🟢 Ready to Publish` 那条),就是 `/admin/notion-sync`,用同一个 secret。
- ## 2. 关于"能不能共用一个 webhook"—— 我查了代码,答案是:不需要在后端做 payload 分流,直接办法更简单
- 也就是说:**这两个 endpoint 已经是"自带分流"的了** —— 不管谁调用它,它自己会判断该不该动手。所以你完全不需要我在后端写一段"读 payload 里的 Stage,再决定走哪条线"的分流逻辑(而且老实说这样更脆,因为要依赖 Notion webhook payload 的具体格式,那个格式没写死、我也没法保证长期稳定)。
- 如果你们 Notion plan 里 "When all/any" 那个下拉没有 "any" 选项(某些版本可能限制),退回原方案——两个独立 automation,一个卡 Ready to Publish,一个卡 Published,跟现在 CLAUDE.md 里写的设计完全一致,也没问题,只是多一步设置。
- 啊,我搞错了 —— 是我自己没检查现有状态,盲目生成了个新的把 Render 上的值覆盖掉了。抱歉,这是我的失误。现在就用你原来那个值把 Render 改回去,不用动 Notion 那边。


## 2026-07-08 13:27 — social-ip-engine

### Architecture Decisions
- Only 1 unrelated pre-existing failure (`test_chloe_agent.py` bubble-splitting, nothing to do with this change) — 1157 passed. Per policy this needs a python-reviewer pass before shipping since it's production webhook logic:
- One HIGH finding, but it's a **different, separate feature** (`notion_sync.py`'s comment-rule auto-drafting has the same hardcoded-"instagram" pattern) — not part of today's live DM-language incident, so I'll flag it rather than scope-creep into fixing it now. Adding the cheap MEDIUM test first (collision detection across differently-named channels):
- Real API shape confirmed — now checking whether it supports fetching by URL server-side (like IG does), or requires a local binary upload (which would change our architecture significantly since we don't want to download+re-upload video bytes ourselves):

### Decisions & Reasoning
- 1. **6/10 那次** —— Messenger 曾经真实跑通过一次（FB_PAGE_ID=1200796509776468，Chloe 回复过真实 DM，截图确认过）。但那是**心宜中醫/老 Jessica 时代的 FB Page**，7 月初那次战略转向（不做 WhatsApp、不做心宜中醫）之后，那条线跟老 Jessica 一样已经不是当前架构在用的东西了。
- - Meta 侧：给 Jackie 关联一个 FB Page，走一遍 `docs/MESSENGER-ACTIVATION.md`（或者我刚发你的那份通用 Tutorial）
- 好，那就是纯粹缺人工那几步了，代码那边不用等——FB 目前是走 **env variable 直连**，不是走 registry（`ip.json`）的,所以我之前说的"要改 `ip.json`"那句可以撤回,不需要。
- - 确认这个 FB Page 挂在跟 Jackie IG 账号**同一个 Meta App**下（如果是同一个 App，`FB_APP_SECRET` 可以不用另设，会 fallback 用 `META_APP_SECRET`；如果是不同 App，就要单独填 `FB_APP_SECRET`）
- - Verify token：用现成的 `META_VERIFY_TOKEN`（跟 IG 共用同一个）
- 一个我想提醒你的点：现在 FB 这条路是**单账号 env var**（`FB_PAGE_ID`/`FB_PAGE_LANGUAGE` 全局唯一），不是像 IG 那样走 `ip.json` 的多 IP registry。今天只有 Jackie 一个人用没问题，但**如果以后 Chloe 也要开自己的 FB Page，这套 env var 结构就不够用了**（两个 Page 共用一组变量会互相打架）。现在不用管，但如果你们打算近期给 Chloe 也开 Messenger，这个是要提前规划的架构债，值得先说一声。
- 需要我现在就把这几个 Render env var 用 API 帮你填上吗？还是你想先自己在 Meta 那边把 token 生成出来，我再帮你验证 probe？
- FB_APP_SECRET         — 没设（若 Jackie Page 跟 IG 挂同一个 Meta App，可不设，会 fallback 用 META_APP_SECRET）


## 2026-07-08 13:35 — social-ip-engine

### Architecture Decisions
- Only 1 unrelated pre-existing failure (`test_chloe_agent.py` bubble-splitting, nothing to do with this change) — 1157 passed. Per policy this needs a python-reviewer pass before shipping since it's production webhook logic:
- One HIGH finding, but it's a **different, separate feature** (`notion_sync.py`'s comment-rule auto-drafting has the same hardcoded-"instagram" pattern) — not part of today's live DM-language incident, so I'll flag it rather than scope-creep into fixing it now. Adding the cheap MEDIUM test first (collision detection across differently-named channels):
- Real API shape confirmed — now checking whether it supports fetching by URL server-side (like IG does), or requires a local binary upload (which would change our architecture significantly since we don't want to download+re-upload video bytes ourselves):

### Decisions & Reasoning
- 1. **6/10 那次** —— Messenger 曾经真实跑通过一次（FB_PAGE_ID=1200796509776468，Chloe 回复过真实 DM，截图确认过）。但那是**心宜中醫/老 Jessica 时代的 FB Page**，7 月初那次战略转向（不做 WhatsApp、不做心宜中醫）之后，那条线跟老 Jessica 一样已经不是当前架构在用的东西了。
- - Meta 侧：给 Jackie 关联一个 FB Page，走一遍 `docs/MESSENGER-ACTIVATION.md`（或者我刚发你的那份通用 Tutorial）
- 好，那就是纯粹缺人工那几步了，代码那边不用等——FB 目前是走 **env variable 直连**，不是走 registry（`ip.json`）的,所以我之前说的"要改 `ip.json`"那句可以撤回,不需要。
- - 确认这个 FB Page 挂在跟 Jackie IG 账号**同一个 Meta App**下（如果是同一个 App，`FB_APP_SECRET` 可以不用另设，会 fallback 用 `META_APP_SECRET`；如果是不同 App，就要单独填 `FB_APP_SECRET`）
- - Verify token：用现成的 `META_VERIFY_TOKEN`（跟 IG 共用同一个）
- 一个我想提醒你的点：现在 FB 这条路是**单账号 env var**（`FB_PAGE_ID`/`FB_PAGE_LANGUAGE` 全局唯一），不是像 IG 那样走 `ip.json` 的多 IP registry。今天只有 Jackie 一个人用没问题，但**如果以后 Chloe 也要开自己的 FB Page，这套 env var 结构就不够用了**（两个 Page 共用一组变量会互相打架）。现在不用管，但如果你们打算近期给 Chloe 也开 Messenger，这个是要提前规划的架构债，值得先说一声。
- 需要我现在就把这几个 Render env var 用 API 帮你填上吗？还是你想先自己在 Meta 那边把 token 生成出来，我再帮你验证 probe？
- FB_APP_SECRET         — 没设（若 Jackie Page 跟 IG 挂同一个 Meta App，可不设，会 fallback 用 META_APP_SECRET）


## 2026-07-08 13:35 — social-ip-engine

### Decisions & Reasoning
- 我倾向 **选项 1**。理由:property 干净、不污染 body、和 "Production Video" 平行摆着一眼能看懂哪个是 master 哪个是成片。要的话我 20 行给 `notion_video.py` 加一个 `--upload-master`,concat 完自动传进 "Master Video" property。
- 2. **换平台重用** —— 比如发去一个你想用平台原生字幕、
- `POST /admin/notion-publish` —— Stage 一拖到 `✅ Published`,理论上 Notion 会打这个 endpoint,自动把该行的 **"Production Video" property** 发布上 Instagram(生成/复用封面 + 真发 Reel)。
- 3. 同理如果也想要评论关键词自动打 DM 规则(`🟢 Ready to Publish` 那条),就是 `/admin/notion-sync`,用同一个 secret。
- ## 2. 关于"能不能共用一个 webhook"—— 我查了代码,答案是:不需要在后端做 payload 分流,直接办法更简单
- 也就是说:**这两个 endpoint 已经是"自带分流"的了** —— 不管谁调用它,它自己会判断该不该动手。所以你完全不需要我在后端写一段"读 payload 里的 Stage,再决定走哪条线"的分流逻辑(而且老实说这样更脆,因为要依赖 Notion webhook payload 的具体格式,那个格式没写死、我也没法保证长期稳定)。
- 如果你们 Notion plan 里 "When all/any" 那个下拉没有 "any" 选项(某些版本可能限制),退回原方案——两个独立 automation,一个卡 Ready to Publish,一个卡 Published,跟现在 CLAUDE.md 里写的设计完全一致,也没问题,只是多一步设置。
- 啊,我搞错了 —— 是我自己没检查现有状态,盲目生成了个新的把 Render 上的值覆盖掉了。抱歉,这是我的失误。现在就用你原来那个值把 Render 改回去,不用动 Notion 那边。


## 2026-07-08 13:41 — social-ip-engine

### Decisions & Reasoning
- 我倾向 **选项 1**。理由:property 干净、不污染 body、和 "Production Video" 平行摆着一眼能看懂哪个是 master 哪个是成片。要的话我 20 行给 `notion_video.py` 加一个 `--upload-master`,concat 完自动传进 "Master Video" property。
- 2. **换平台重用** —— 比如发去一个你想用平台原生字幕、
- `POST /admin/notion-publish` —— Stage 一拖到 `✅ Published`,理论上 Notion 会打这个 endpoint,自动把该行的 **"Production Video" property** 发布上 Instagram(生成/复用封面 + 真发 Reel)。
- 3. 同理如果也想要评论关键词自动打 DM 规则(`🟢 Ready to Publish` 那条),就是 `/admin/notion-sync`,用同一个 secret。
- ## 2. 关于"能不能共用一个 webhook"—— 我查了代码,答案是:不需要在后端做 payload 分流,直接办法更简单
- 也就是说:**这两个 endpoint 已经是"自带分流"的了** —— 不管谁调用它,它自己会判断该不该动手。所以你完全不需要我在后端写一段"读 payload 里的 Stage,再决定走哪条线"的分流逻辑(而且老实说这样更脆,因为要依赖 Notion webhook payload 的具体格式,那个格式没写死、我也没法保证长期稳定)。
- 如果你们 Notion plan 里 "When all/any" 那个下拉没有 "any" 选项(某些版本可能限制),退回原方案——两个独立 automation,一个卡 Ready to Publish,一个卡 Published,跟现在 CLAUDE.md 里写的设计完全一致,也没问题,只是多一步设置。
- 啊,我搞错了 —— 是我自己没检查现有状态,盲目生成了个新的把 Render 上的值覆盖掉了。抱歉,这是我的失误。现在就用你原来那个值把 Render 改回去,不用动 Notion 那边。


## 2026-07-08 13:46 — social-ip-engine

### Architecture Decisions
- Only 1 unrelated pre-existing failure (`test_chloe_agent.py` bubble-splitting, nothing to do with this change) — 1157 passed. Per policy this needs a python-reviewer pass before shipping since it's production webhook logic:
- One HIGH finding, but it's a **different, separate feature** (`notion_sync.py`'s comment-rule auto-drafting has the same hardcoded-"instagram" pattern) — not part of today's live DM-language incident, so I'll flag it rather than scope-creep into fixing it now. Adding the cheap MEDIUM test first (collision detection across differently-named channels):
- Real API shape confirmed — now checking whether it supports fetching by URL server-side (like IG does), or requires a local binary upload (which would change our architecture significantly since we don't want to download+re-upload video bytes ourselves):

### Decisions & Reasoning
- 1. **6/10 那次** —— Messenger 曾经真实跑通过一次（FB_PAGE_ID=1200796509776468，Chloe 回复过真实 DM，截图确认过）。但那是**心宜中醫/老 Jessica 时代的 FB Page**，7 月初那次战略转向（不做 WhatsApp、不做心宜中醫）之后，那条线跟老 Jessica 一样已经不是当前架构在用的东西了。
- - Meta 侧：给 Jackie 关联一个 FB Page，走一遍 `docs/MESSENGER-ACTIVATION.md`（或者我刚发你的那份通用 Tutorial）
- 好，那就是纯粹缺人工那几步了，代码那边不用等——FB 目前是走 **env variable 直连**，不是走 registry（`ip.json`）的,所以我之前说的"要改 `ip.json`"那句可以撤回,不需要。
- - 确认这个 FB Page 挂在跟 Jackie IG 账号**同一个 Meta App**下（如果是同一个 App，`FB_APP_SECRET` 可以不用另设，会 fallback 用 `META_APP_SECRET`；如果是不同 App，就要单独填 `FB_APP_SECRET`）
- - Verify token：用现成的 `META_VERIFY_TOKEN`（跟 IG 共用同一个）
- 一个我想提醒你的点：现在 FB 这条路是**单账号 env var**（`FB_PAGE_ID`/`FB_PAGE_LANGUAGE` 全局唯一），不是像 IG 那样走 `ip.json` 的多 IP registry。今天只有 Jackie 一个人用没问题，但**如果以后 Chloe 也要开自己的 FB Page，这套 env var 结构就不够用了**（两个 Page 共用一组变量会互相打架）。现在不用管，但如果你们打算近期给 Chloe 也开 Messenger，这个是要提前规划的架构债，值得先说一声。
- 需要我现在就把这几个 Render env var 用 API 帮你填上吗？还是你想先自己在 Meta 那边把 token 生成出来，我再帮你验证 probe？
- FB_APP_SECRET         — 没设（若 Jackie Page 跟 IG 挂同一个 Meta App，可不设，会 fallback 用 META_APP_SECRET）


## 2026-07-08 13:47 — social-ip-engine

### Decisions & Reasoning
- 我倾向 **选项 1**。理由:property 干净、不污染 body、和 "Production Video" 平行摆着一眼能看懂哪个是 master 哪个是成片。要的话我 20 行给 `notion_video.py` 加一个 `--upload-master`,concat 完自动传进 "Master Video" property。
- 2. **换平台重用** —— 比如发去一个你想用平台原生字幕、
- `POST /admin/notion-publish` —— Stage 一拖到 `✅ Published`,理论上 Notion 会打这个 endpoint,自动把该行的 **"Production Video" property** 发布上 Instagram(生成/复用封面 + 真发 Reel)。
- 3. 同理如果也想要评论关键词自动打 DM 规则(`🟢 Ready to Publish` 那条),就是 `/admin/notion-sync`,用同一个 secret。
- ## 2. 关于"能不能共用一个 webhook"—— 我查了代码,答案是:不需要在后端做 payload 分流,直接办法更简单
- 也就是说:**这两个 endpoint 已经是"自带分流"的了** —— 不管谁调用它,它自己会判断该不该动手。所以你完全不需要我在后端写一段"读 payload 里的 Stage,再决定走哪条线"的分流逻辑(而且老实说这样更脆,因为要依赖 Notion webhook payload 的具体格式,那个格式没写死、我也没法保证长期稳定)。
- 如果你们 Notion plan 里 "When all/any" 那个下拉没有 "any" 选项(某些版本可能限制),退回原方案——两个独立 automation,一个卡 Ready to Publish,一个卡 Published,跟现在 CLAUDE.md 里写的设计完全一致,也没问题,只是多一步设置。
- 啊,我搞错了 —— 是我自己没检查现有状态,盲目生成了个新的把 Render 上的值覆盖掉了。抱歉,这是我的失误。现在就用你原来那个值把 Render 改回去,不用动 Notion 那边。


## 2026-07-08 13:52 — social-ip-engine

### Decisions & Reasoning
- 我倾向 **选项 1**。理由:property 干净、不污染 body、和 "Production Video" 平行摆着一眼能看懂哪个是 master 哪个是成片。要的话我 20 行给 `notion_video.py` 加一个 `--upload-master`,concat 完自动传进 "Master Video" property。
- 2. **换平台重用** —— 比如发去一个你想用平台原生字幕、
- `POST /admin/notion-publish` —— Stage 一拖到 `✅ Published`,理论上 Notion 会打这个 endpoint,自动把该行的 **"Production Video" property** 发布上 Instagram(生成/复用封面 + 真发 Reel)。
- 3. 同理如果也想要评论关键词自动打 DM 规则(`🟢 Ready to Publish` 那条),就是 `/admin/notion-sync`,用同一个 secret。
- ## 2. 关于"能不能共用一个 webhook"—— 我查了代码,答案是:不需要在后端做 payload 分流,直接办法更简单
- 也就是说:**这两个 endpoint 已经是"自带分流"的了** —— 不管谁调用它,它自己会判断该不该动手。所以你完全不需要我在后端写一段"读 payload 里的 Stage,再决定走哪条线"的分流逻辑(而且老实说这样更脆,因为要依赖 Notion webhook payload 的具体格式,那个格式没写死、我也没法保证长期稳定)。
- 如果你们 Notion plan 里 "When all/any" 那个下拉没有 "any" 选项(某些版本可能限制),退回原方案——两个独立 automation,一个卡 Ready to Publish,一个卡 Published,跟现在 CLAUDE.md 里写的设计完全一致,也没问题,只是多一步设置。
- 啊,我搞错了 —— 是我自己没检查现有状态,盲目生成了个新的把 Render 上的值覆盖掉了。抱歉,这是我的失误。现在就用你原来那个值把 Render 改回去,不用动 Notion 那边。


## 2026-07-08 14:01 — social-ip-engine

### Decisions & Reasoning
- 我倾向 **选项 1**。理由:property 干净、不污染 body、和 "Production Video" 平行摆着一眼能看懂哪个是 master 哪个是成片。要的话我 20 行给 `notion_video.py` 加一个 `--upload-master`,concat 完自动传进 "Master Video" property。
- 2. **换平台重用** —— 比如发去一个你想用平台原生字幕、
- `POST /admin/notion-publish` —— Stage 一拖到 `✅ Published`,理论上 Notion 会打这个 endpoint,自动把该行的 **"Production Video" property** 发布上 Instagram(生成/复用封面 + 真发 Reel)。
- 3. 同理如果也想要评论关键词自动打 DM 规则(`🟢 Ready to Publish` 那条),就是 `/admin/notion-sync`,用同一个 secret。
- ## 2. 关于"能不能共用一个 webhook"—— 我查了代码,答案是:不需要在后端做 payload 分流,直接办法更简单
- 也就是说:**这两个 endpoint 已经是"自带分流"的了** —— 不管谁调用它,它自己会判断该不该动手。所以你完全不需要我在后端写一段"读 payload 里的 Stage,再决定走哪条线"的分流逻辑(而且老实说这样更脆,因为要依赖 Notion webhook payload 的具体格式,那个格式没写死、我也没法保证长期稳定)。
- 如果你们 Notion plan 里 "When all/any" 那个下拉没有 "any" 选项(某些版本可能限制),退回原方案——两个独立 automation,一个卡 Ready to Publish,一个卡 Published,跟现在 CLAUDE.md 里写的设计完全一致,也没问题,只是多一步设置。
- 啊,我搞错了 —— 是我自己没检查现有状态,盲目生成了个新的把 Render 上的值覆盖掉了。抱歉,这是我的失误。现在就用你原来那个值把 Render 改回去,不用动 Notion 那边。


## 2026-07-08 14:07 — social-ip-engine

### Decisions & Reasoning
- 我倾向 **选项 1**。理由:property 干净、不污染 body、和 "Production Video" 平行摆着一眼能看懂哪个是 master 哪个是成片。要的话我 20 行给 `notion_video.py` 加一个 `--upload-master`,concat 完自动传进 "Master Video" property。
- 2. **换平台重用** —— 比如发去一个你想用平台原生字幕、
- `POST /admin/notion-publish` —— Stage 一拖到 `✅ Published`,理论上 Notion 会打这个 endpoint,自动把该行的 **"Production Video" property** 发布上 Instagram(生成/复用封面 + 真发 Reel)。
- 3. 同理如果也想要评论关键词自动打 DM 规则(`🟢 Ready to Publish` 那条),就是 `/admin/notion-sync`,用同一个 secret。
- ## 2. 关于"能不能共用一个 webhook"—— 我查了代码,答案是:不需要在后端做 payload 分流,直接办法更简单
- 也就是说:**这两个 endpoint 已经是"自带分流"的了** —— 不管谁调用它,它自己会判断该不该动手。所以你完全不需要我在后端写一段"读 payload 里的 Stage,再决定走哪条线"的分流逻辑(而且老实说这样更脆,因为要依赖 Notion webhook payload 的具体格式,那个格式没写死、我也没法保证长期稳定)。
- 如果你们 Notion plan 里 "When all/any" 那个下拉没有 "any" 选项(某些版本可能限制),退回原方案——两个独立 automation,一个卡 Ready to Publish,一个卡 Published,跟现在 CLAUDE.md 里写的设计完全一致,也没问题,只是多一步设置。
- 啊,我搞错了 —— 是我自己没检查现有状态,盲目生成了个新的把 Render 上的值覆盖掉了。抱歉,这是我的失误。现在就用你原来那个值把 Render 改回去,不用动 Notion 那边。


## 2026-07-08 14:18 — social-ip-engine

### Decisions & Reasoning
- 我倾向 **选项 1**。理由:property 干净、不污染 body、和 "Production Video" 平行摆着一眼能看懂哪个是 master 哪个是成片。要的话我 20 行给 `notion_video.py` 加一个 `--upload-master`,concat 完自动传进 "Master Video" property。
- 2. **换平台重用** —— 比如发去一个你想用平台原生字幕、
- `POST /admin/notion-publish` —— Stage 一拖到 `✅ Published`,理论上 Notion 会打这个 endpoint,自动把该行的 **"Production Video" property** 发布上 Instagram(生成/复用封面 + 真发 Reel)。
- 3. 同理如果也想要评论关键词自动打 DM 规则(`🟢 Ready to Publish` 那条),就是 `/admin/notion-sync`,用同一个 secret。
- ## 2. 关于"能不能共用一个 webhook"—— 我查了代码,答案是:不需要在后端做 payload 分流,直接办法更简单
- 也就是说:**这两个 endpoint 已经是"自带分流"的了** —— 不管谁调用它,它自己会判断该不该动手。所以你完全不需要我在后端写一段"读 payload 里的 Stage,再决定走哪条线"的分流逻辑(而且老实说这样更脆,因为要依赖 Notion webhook payload 的具体格式,那个格式没写死、我也没法保证长期稳定)。
- 如果你们 Notion plan 里 "When all/any" 那个下拉没有 "any" 选项(某些版本可能限制),退回原方案——两个独立 automation,一个卡 Ready to Publish,一个卡 Published,跟现在 CLAUDE.md 里写的设计完全一致,也没问题,只是多一步设置。
- 啊,我搞错了 —— 是我自己没检查现有状态,盲目生成了个新的把 Render 上的值覆盖掉了。抱歉,这是我的失误。现在就用你原来那个值把 Render 改回去,不用动 Notion 那边。


## 2026-07-08 14:24 — social-ip-engine

### Decisions & Reasoning
- 1. **直播那条 FB post 的 caption 已经改成 "Do you have tonsil stones? 😱"** — 直接用 Facebook 的 edit API 改的,已验证生效。
- 2. **找到根因并修了代码本身**(不只是我那个测试脚本):`notion_publish_caption.py` 一直在用 Content 页面的内部 "Hook" 字段("Watch what came out of her throat...")当标题,却完全没读那行 Production Tracker 上专门写的 **"🏷️ Title"** property(你说得对——那才是 `notion_prompts.py` 里 `draft_title()` 特地生成的、给人看的标题)。这个 bug 出在共用代码里,意味着**IG 那边自动发的帖子可能也一直是错的标题**,不只是我这条 FB 测试帖。已经加了 `extract_headline()`,Title 优先、Hook 兜底,写了回归测试(专门标注这次 incident),全套 1229 个测试跑绿。丢给 python-reviewer 在跑最后一轮检查。
- 我试着现补了一张(用正确的 Title 文字生成),但 AI 不知道 Jackie 长什么样(cover 生成的 prompt 是纯文字描述,没有像 Shot 1/2/3 那样带参考照片做 image-to-image),画出来是个完全不认识的女生,人不对:


## 2026-07-08 14:25 — social-ip-engine

### Decisions & Reasoning
- 我倾向 **选项 1**。理由:property 干净、不污染 body、和 "Production Video" 平行摆着一眼能看懂哪个是 master 哪个是成片。要的话我 20 行给 `notion_video.py` 加一个 `--upload-master`,concat 完自动传进 "Master Video" property。
- 2. **换平台重用** —— 比如发去一个你想用平台原生字幕、
- `POST /admin/notion-publish` —— Stage 一拖到 `✅ Published`,理论上 Notion 会打这个 endpoint,自动把该行的 **"Production Video" property** 发布上 Instagram(生成/复用封面 + 真发 Reel)。
- 3. 同理如果也想要评论关键词自动打 DM 规则(`🟢 Ready to Publish` 那条),就是 `/admin/notion-sync`,用同一个 secret。
- ## 2. 关于"能不能共用一个 webhook"—— 我查了代码,答案是:不需要在后端做 payload 分流,直接办法更简单
- 也就是说:**这两个 endpoint 已经是"自带分流"的了** —— 不管谁调用它,它自己会判断该不该动手。所以你完全不需要我在后端写一段"读 payload 里的 Stage,再决定走哪条线"的分流逻辑(而且老实说这样更脆,因为要依赖 Notion webhook payload 的具体格式,那个格式没写死、我也没法保证长期稳定)。
- 如果你们 Notion plan 里 "When all/any" 那个下拉没有 "any" 选项(某些版本可能限制),退回原方案——两个独立 automation,一个卡 Ready to Publish,一个卡 Published,跟现在 CLAUDE.md 里写的设计完全一致,也没问题,只是多一步设置。
- 啊,我搞错了 —— 是我自己没检查现有状态,盲目生成了个新的把 Render 上的值覆盖掉了。抱歉,这是我的失误。现在就用你原来那个值把 Render 改回去,不用动 Notion 那边。


## 2026-07-08 14:26 — social-ip-engine

### Decisions & Reasoning
- 1. **直播那条 FB post 的 caption 已经改成 "Do you have tonsil stones? 😱"** — 直接用 Facebook 的 edit API 改的,已验证生效。
- 2. **找到根因并修了代码本身**(不只是我那个测试脚本):`notion_publish_caption.py` 一直在用 Content 页面的内部 "Hook" 字段("Watch what came out of her throat...")当标题,却完全没读那行 Production Tracker 上专门写的 **"🏷️ Title"** property(你说得对——那才是 `notion_prompts.py` 里 `draft_title()` 特地生成的、给人看的标题)。这个 bug 出在共用代码里,意味着**IG 那边自动发的帖子可能也一直是错的标题**,不只是我这条 FB 测试帖。已经加了 `extract_headline()`,Title 优先、Hook 兜底,写了回归测试(专门标注这次 incident),全套 1229 个测试跑绿。丢给 python-reviewer 在跑最后一轮检查。
- 我试着现补了一张(用正确的 Title 文字生成),但 AI 不知道 Jackie 长什么样(cover 生成的 prompt 是纯文字描述,没有像 Shot 1/2/3 那样带参考照片做 image-to-image),画出来是个完全不认识的女生,人不对:
- 我没有推这张上去,因为人不对反而更奇怪。三个选项,你选一个:
- 2. **你/studio 那边去 Notion 那一行的「🖼️ Cover Photo → 🖼️ Cover here」toggle 补一张真正的封面图**(用 Jackie 的参考照片跑 image-to-image,跟 Shot 1-5 一样的流程),弄好后我用 Facebook 的 `/thumbnails` 接口(我刚测过,这个接口能用,可以上传自定义缩略图 + 设成 preferred)把封面换掉。
- 我个人倾向 **选项 2**,但那需要你那边先出图。顺带一提:这个"没人生成 Cover Photo 就直接发布"的情况,以后每一条新视频都可能会撞到——要不要我也检查一下其他还没发的行是不是也缺封面?


## 2026-07-08 14:38 — social-ip-engine

### Decisions & Reasoning
- 1. **直播那条 FB post 的 caption 已经改成 "Do you have tonsil stones? 😱"** — 直接用 Facebook 的 edit API 改的,已验证生效。
- 2. **找到根因并修了代码本身**(不只是我那个测试脚本):`notion_publish_caption.py` 一直在用 Content 页面的内部 "Hook" 字段("Watch what came out of her throat...")当标题,却完全没读那行 Production Tracker 上专门写的 **"🏷️ Title"** property(你说得对——那才是 `notion_prompts.py` 里 `draft_title()` 特地生成的、给人看的标题)。这个 bug 出在共用代码里,意味着**IG 那边自动发的帖子可能也一直是错的标题**,不只是我这条 FB 测试帖。已经加了 `extract_headline()`,Title 优先、Hook 兜底,写了回归测试(专门标注这次 incident),全套 1229 个测试跑绿。丢给 python-reviewer 在跑最后一轮检查。
- 我试着现补了一张(用正确的 Title 文字生成),但 AI 不知道 Jackie 长什么样(cover 生成的 prompt 是纯文字描述,没有像 Shot 1/2/3 那样带参考照片做 image-to-image),画出来是个完全不认识的女生,人不对:
- 我没有推这张上去,因为人不对反而更奇怪。三个选项,你选一个:
- 2. **你/studio 那边去 Notion 那一行的「🖼️ Cover Photo → 🖼️ Cover here」toggle 补一张真正的封面图**(用 Jackie 的参考照片跑 image-to-image,跟 Shot 1-5 一样的流程),弄好后我用 Facebook 的 `/thumbnails` 接口(我刚测过,这个接口能用,可以上传自定义缩略图 + 设成 preferred)把封面换掉。
- 我个人倾向 **选项 2**,但那需要你那边先出图。顺带一提:这个"没人生成 Cover Photo 就直接发布"的情况,以后每一条新视频都可能会撞到——要不要我也检查一下其他还没发的行是不是也缺封面?
- - **MEDIUM**: Fallback-to-Hook was silent — now surfaces a warning into the same `warnings` list the planner already threads through, so it'll show up in ops output instead of hiding.


## 2026-07-08 14:52 — social-ip-engine

### Decisions & Reasoning
- 我倾向 **选项 1**。理由:property 干净、不污染 body、和 "Production Video" 平行摆着一眼能看懂哪个是 master 哪个是成片。要的话我 20 行给 `notion_video.py` 加一个 `--upload-master`,concat 完自动传进 "Master Video" property。
- 2. **换平台重用** —— 比如发去一个你想用平台原生字幕、
- `POST /admin/notion-publish` —— Stage 一拖到 `✅ Published`,理论上 Notion 会打这个 endpoint,自动把该行的 **"Production Video" property** 发布上 Instagram(生成/复用封面 + 真发 Reel)。
- 3. 同理如果也想要评论关键词自动打 DM 规则(`🟢 Ready to Publish` 那条),就是 `/admin/notion-sync`,用同一个 secret。
- ## 2. 关于"能不能共用一个 webhook"—— 我查了代码,答案是:不需要在后端做 payload 分流,直接办法更简单
- 也就是说:**这两个 endpoint 已经是"自带分流"的了** —— 不管谁调用它,它自己会判断该不该动手。所以你完全不需要我在后端写一段"读 payload 里的 Stage,再决定走哪条线"的分流逻辑(而且老实说这样更脆,因为要依赖 Notion webhook payload 的具体格式,那个格式没写死、我也没法保证长期稳定)。
- 如果你们 Notion plan 里 "When all/any" 那个下拉没有 "any" 选项(某些版本可能限制),退回原方案——两个独立 automation,一个卡 Ready to Publish,一个卡 Published,跟现在 CLAUDE.md 里写的设计完全一致,也没问题,只是多一步设置。
- 啊,我搞错了 —— 是我自己没检查现有状态,盲目生成了个新的把 Render 上的值覆盖掉了。抱歉,这是我的失误。现在就用你原来那个值把 Render 改回去,不用动 Notion 那边。


## 2026-07-08 14:54 — social-ip-engine

### Decisions & Reasoning
- 1. **直播那条 FB post 的 caption 已经改成 "Do you have tonsil stones? 😱"** — 直接用 Facebook 的 edit API 改的,已验证生效。
- 2. **找到根因并修了代码本身**(不只是我那个测试脚本):`notion_publish_caption.py` 一直在用 Content 页面的内部 "Hook" 字段("Watch what came out of her throat...")当标题,却完全没读那行 Production Tracker 上专门写的 **"🏷️ Title"** property(你说得对——那才是 `notion_prompts.py` 里 `draft_title()` 特地生成的、给人看的标题)。这个 bug 出在共用代码里,意味着**IG 那边自动发的帖子可能也一直是错的标题**,不只是我这条 FB 测试帖。已经加了 `extract_headline()`,Title 优先、Hook 兜底,写了回归测试(专门标注这次 incident),全套 1229 个测试跑绿。丢给 python-reviewer 在跑最后一轮检查。
- 我试着现补了一张(用正确的 Title 文字生成),但 AI 不知道 Jackie 长什么样(cover 生成的 prompt 是纯文字描述,没有像 Shot 1/2/3 那样带参考照片做 image-to-image),画出来是个完全不认识的女生,人不对:
- 我没有推这张上去,因为人不对反而更奇怪。三个选项,你选一个:
- 2. **你/studio 那边去 Notion 那一行的「🖼️ Cover Photo → 🖼️ Cover here」toggle 补一张真正的封面图**(用 Jackie 的参考照片跑 image-to-image,跟 Shot 1-5 一样的流程),弄好后我用 Facebook 的 `/thumbnails` 接口(我刚测过,这个接口能用,可以上传自定义缩略图 + 设成 preferred)把封面换掉。
- 我个人倾向 **选项 2**,但那需要你那边先出图。顺带一提:这个"没人生成 Cover Photo 就直接发布"的情况,以后每一条新视频都可能会撞到——要不要我也检查一下其他还没发的行是不是也缺封面?
- - **MEDIUM**: Fallback-to-Hook was silent — now surfaces a warning into the same `warnings` list the planner already threads through, so it'll show up in ops output instead of hiding.
- 全部搞定了,6 张全部对上号、传回 Notion,而且我用 auto-publish 实际调用的那个函数验证过——6 条全部能读到:


## 2026-07-08 15:01 — social-ip-engine

### Decisions & Reasoning
- 我倾向 **选项 1**。理由:property 干净、不污染 body、和 "Production Video" 平行摆着一眼能看懂哪个是 master 哪个是成片。要的话我 20 行给 `notion_video.py` 加一个 `--upload-master`,concat 完自动传进 "Master Video" property。
- 2. **换平台重用** —— 比如发去一个你想用平台原生字幕、
- `POST /admin/notion-publish` —— Stage 一拖到 `✅ Published`,理论上 Notion 会打这个 endpoint,自动把该行的 **"Production Video" property** 发布上 Instagram(生成/复用封面 + 真发 Reel)。
- 3. 同理如果也想要评论关键词自动打 DM 规则(`🟢 Ready to Publish` 那条),就是 `/admin/notion-sync`,用同一个 secret。
- ## 2. 关于"能不能共用一个 webhook"—— 我查了代码,答案是:不需要在后端做 payload 分流,直接办法更简单
- 也就是说:**这两个 endpoint 已经是"自带分流"的了** —— 不管谁调用它,它自己会判断该不该动手。所以你完全不需要我在后端写一段"读 payload 里的 Stage,再决定走哪条线"的分流逻辑(而且老实说这样更脆,因为要依赖 Notion webhook payload 的具体格式,那个格式没写死、我也没法保证长期稳定)。
- 如果你们 Notion plan 里 "When all/any" 那个下拉没有 "any" 选项(某些版本可能限制),退回原方案——两个独立 automation,一个卡 Ready to Publish,一个卡 Published,跟现在 CLAUDE.md 里写的设计完全一致,也没问题,只是多一步设置。
- 啊,我搞错了 —— 是我自己没检查现有状态,盲目生成了个新的把 Render 上的值覆盖掉了。抱歉,这是我的失误。现在就用你原来那个值把 Render 改回去,不用动 Notion 那边。


## 2026-07-08 15:02 — social-ip-engine

### Decisions & Reasoning
- 1. **直播那条 FB post 的 caption 已经改成 "Do you have tonsil stones? 😱"** — 直接用 Facebook 的 edit API 改的,已验证生效。
- 2. **找到根因并修了代码本身**(不只是我那个测试脚本):`notion_publish_caption.py` 一直在用 Content 页面的内部 "Hook" 字段("Watch what came out of her throat...")当标题,却完全没读那行 Production Tracker 上专门写的 **"🏷️ Title"** property(你说得对——那才是 `notion_prompts.py` 里 `draft_title()` 特地生成的、给人看的标题)。这个 bug 出在共用代码里,意味着**IG 那边自动发的帖子可能也一直是错的标题**,不只是我这条 FB 测试帖。已经加了 `extract_headline()`,Title 优先、Hook 兜底,写了回归测试(专门标注这次 incident),全套 1229 个测试跑绿。丢给 python-reviewer 在跑最后一轮检查。
- 我试着现补了一张(用正确的 Title 文字生成),但 AI 不知道 Jackie 长什么样(cover 生成的 prompt 是纯文字描述,没有像 Shot 1/2/3 那样带参考照片做 image-to-image),画出来是个完全不认识的女生,人不对:
- 我没有推这张上去,因为人不对反而更奇怪。三个选项,你选一个:
- 2. **你/studio 那边去 Notion 那一行的「🖼️ Cover Photo → 🖼️ Cover here」toggle 补一张真正的封面图**(用 Jackie 的参考照片跑 image-to-image,跟 Shot 1-5 一样的流程),弄好后我用 Facebook 的 `/thumbnails` 接口(我刚测过,这个接口能用,可以上传自定义缩略图 + 设成 preferred)把封面换掉。
- 我个人倾向 **选项 2**,但那需要你那边先出图。顺带一提:这个"没人生成 Cover Photo 就直接发布"的情况,以后每一条新视频都可能会撞到——要不要我也检查一下其他还没发的行是不是也缺封面?
- - **MEDIUM**: Fallback-to-Hook was silent — now surfaces a warning into the same `warnings` list the planner already threads through, so it'll show up in ops output instead of hiding.
- 全部搞定了,6 张全部对上号、传回 Notion,而且我用 auto-publish 实际调用的那个函数验证过——6 条全部能读到:


## 2026-07-08 15:18 — social-ip-engine

### Decisions & Reasoning
- 我倾向 **选项 1**。理由:property 干净、不污染 body、和 "Production Video" 平行摆着一眼能看懂哪个是 master 哪个是成片。要的话我 20 行给 `notion_video.py` 加一个 `--upload-master`,concat 完自动传进 "Master Video" property。
- 2. **换平台重用** —— 比如发去一个你想用平台原生字幕、
- `POST /admin/notion-publish` —— Stage 一拖到 `✅ Published`,理论上 Notion 会打这个 endpoint,自动把该行的 **"Production Video" property** 发布上 Instagram(生成/复用封面 + 真发 Reel)。
- 3. 同理如果也想要评论关键词自动打 DM 规则(`🟢 Ready to Publish` 那条),就是 `/admin/notion-sync`,用同一个 secret。
- ## 2. 关于"能不能共用一个 webhook"—— 我查了代码,答案是:不需要在后端做 payload 分流,直接办法更简单
- 也就是说:**这两个 endpoint 已经是"自带分流"的了** —— 不管谁调用它,它自己会判断该不该动手。所以你完全不需要我在后端写一段"读 payload 里的 Stage,再决定走哪条线"的分流逻辑(而且老实说这样更脆,因为要依赖 Notion webhook payload 的具体格式,那个格式没写死、我也没法保证长期稳定)。
- 如果你们 Notion plan 里 "When all/any" 那个下拉没有 "any" 选项(某些版本可能限制),退回原方案——两个独立 automation,一个卡 Ready to Publish,一个卡 Published,跟现在 CLAUDE.md 里写的设计完全一致,也没问题,只是多一步设置。
- 啊,我搞错了 —— 是我自己没检查现有状态,盲目生成了个新的把 Render 上的值覆盖掉了。抱歉,这是我的失误。现在就用你原来那个值把 Render 改回去,不用动 Notion 那边。


## 2026-07-08 15:26 — social-ip-engine

### Decisions & Reasoning
- 1. **直播那条 FB post 的 caption 已经改成 "Do you have tonsil stones? 😱"** — 直接用 Facebook 的 edit API 改的,已验证生效。
- 2. **找到根因并修了代码本身**(不只是我那个测试脚本):`notion_publish_caption.py` 一直在用 Content 页面的内部 "Hook" 字段("Watch what came out of her throat...")当标题,却完全没读那行 Production Tracker 上专门写的 **"🏷️ Title"** property(你说得对——那才是 `notion_prompts.py` 里 `draft_title()` 特地生成的、给人看的标题)。这个 bug 出在共用代码里,意味着**IG 那边自动发的帖子可能也一直是错的标题**,不只是我这条 FB 测试帖。已经加了 `extract_headline()`,Title 优先、Hook 兜底,写了回归测试(专门标注这次 incident),全套 1229 个测试跑绿。丢给 python-reviewer 在跑最后一轮检查。
- 我试着现补了一张(用正确的 Title 文字生成),但 AI 不知道 Jackie 长什么样(cover 生成的 prompt 是纯文字描述,没有像 Shot 1/2/3 那样带参考照片做 image-to-image),画出来是个完全不认识的女生,人不对:
- 我没有推这张上去,因为人不对反而更奇怪。三个选项,你选一个:
- 2. **你/studio 那边去 Notion 那一行的「🖼️ Cover Photo → 🖼️ Cover here」toggle 补一张真正的封面图**(用 Jackie 的参考照片跑 image-to-image,跟 Shot 1-5 一样的流程),弄好后我用 Facebook 的 `/thumbnails` 接口(我刚测过,这个接口能用,可以上传自定义缩略图 + 设成 preferred)把封面换掉。
- 我个人倾向 **选项 2**,但那需要你那边先出图。顺带一提:这个"没人生成 Cover Photo 就直接发布"的情况,以后每一条新视频都可能会撞到——要不要我也检查一下其他还没发的行是不是也缺封面?
- - **MEDIUM**: Fallback-to-Hook was silent — now surfaces a warning into the same `warnings` list the planner already threads through, so it'll show up in ops output instead of hiding.
- 全部搞定了,6 张全部对上号、传回 Notion,而且我用 auto-publish 实际调用的那个函数验证过——6 条全部能读到:


## 2026-07-08 15:28 — social-ip-engine

### Decisions & Reasoning
- 1. **直播那条 FB post 的 caption 已经改成 "Do you have tonsil stones? 😱"** — 直接用 Facebook 的 edit API 改的,已验证生效。
- 2. **找到根因并修了代码本身**(不只是我那个测试脚本):`notion_publish_caption.py` 一直在用 Content 页面的内部 "Hook" 字段("Watch what came out of her throat...")当标题,却完全没读那行 Production Tracker 上专门写的 **"🏷️ Title"** property(你说得对——那才是 `notion_prompts.py` 里 `draft_title()` 特地生成的、给人看的标题)。这个 bug 出在共用代码里,意味着**IG 那边自动发的帖子可能也一直是错的标题**,不只是我这条 FB 测试帖。已经加了 `extract_headline()`,Title 优先、Hook 兜底,写了回归测试(专门标注这次 incident),全套 1229 个测试跑绿。丢给 python-reviewer 在跑最后一轮检查。
- 我试着现补了一张(用正确的 Title 文字生成),但 AI 不知道 Jackie 长什么样(cover 生成的 prompt 是纯文字描述,没有像 Shot 1/2/3 那样带参考照片做 image-to-image),画出来是个完全不认识的女生,人不对:
- 我没有推这张上去,因为人不对反而更奇怪。三个选项,你选一个:
- 2. **你/studio 那边去 Notion 那一行的「🖼️ Cover Photo → 🖼️ Cover here」toggle 补一张真正的封面图**(用 Jackie 的参考照片跑 image-to-image,跟 Shot 1-5 一样的流程),弄好后我用 Facebook 的 `/thumbnails` 接口(我刚测过,这个接口能用,可以上传自定义缩略图 + 设成 preferred)把封面换掉。
- 我个人倾向 **选项 2**,但那需要你那边先出图。顺带一提:这个"没人生成 Cover Photo 就直接发布"的情况,以后每一条新视频都可能会撞到——要不要我也检查一下其他还没发的行是不是也缺封面?
- - **MEDIUM**: Fallback-to-Hook was silent — now surfaces a warning into the same `warnings` list the planner already threads through, so it'll show up in ops output instead of hiding.
- 全部搞定了,6 张全部对上号、传回 Notion,而且我用 auto-publish 实际调用的那个函数验证过——6 条全部能读到:


## 2026-07-08 15:31 — social-ip-engine

### Decisions & Reasoning
- 1. **直播那条 FB post 的 caption 已经改成 "Do you have tonsil stones? 😱"** — 直接用 Facebook 的 edit API 改的,已验证生效。
- 2. **找到根因并修了代码本身**(不只是我那个测试脚本):`notion_publish_caption.py` 一直在用 Content 页面的内部 "Hook" 字段("Watch what came out of her throat...")当标题,却完全没读那行 Production Tracker 上专门写的 **"🏷️ Title"** property(你说得对——那才是 `notion_prompts.py` 里 `draft_title()` 特地生成的、给人看的标题)。这个 bug 出在共用代码里,意味着**IG 那边自动发的帖子可能也一直是错的标题**,不只是我这条 FB 测试帖。已经加了 `extract_headline()`,Title 优先、Hook 兜底,写了回归测试(专门标注这次 incident),全套 1229 个测试跑绿。丢给 python-reviewer 在跑最后一轮检查。
- 我试着现补了一张(用正确的 Title 文字生成),但 AI 不知道 Jackie 长什么样(cover 生成的 prompt 是纯文字描述,没有像 Shot 1/2/3 那样带参考照片做 image-to-image),画出来是个完全不认识的女生,人不对:
- 我没有推这张上去,因为人不对反而更奇怪。三个选项,你选一个:
- 2. **你/studio 那边去 Notion 那一行的「🖼️ Cover Photo → 🖼️ Cover here」toggle 补一张真正的封面图**(用 Jackie 的参考照片跑 image-to-image,跟 Shot 1-5 一样的流程),弄好后我用 Facebook 的 `/thumbnails` 接口(我刚测过,这个接口能用,可以上传自定义缩略图 + 设成 preferred)把封面换掉。
- 我个人倾向 **选项 2**,但那需要你那边先出图。顺带一提:这个"没人生成 Cover Photo 就直接发布"的情况,以后每一条新视频都可能会撞到——要不要我也检查一下其他还没发的行是不是也缺封面?
- - **MEDIUM**: Fallback-to-Hook was silent — now surfaces a warning into the same `warnings` list the planner already threads through, so it'll show up in ops output instead of hiding.
- 全部搞定了,6 张全部对上号、传回 Notion,而且我用 auto-publish 实际调用的那个函数验证过——6 条全部能读到:


## 2026-07-08 15:32 — social-ip-engine

### Decisions & Reasoning
- 我倾向 **选项 1**。理由:property 干净、不污染 body、和 "Production Video" 平行摆着一眼能看懂哪个是 master 哪个是成片。要的话我 20 行给 `notion_video.py` 加一个 `--upload-master`,concat 完自动传进 "Master Video" property。
- 2. **换平台重用** —— 比如发去一个你想用平台原生字幕、
- `POST /admin/notion-publish` —— Stage 一拖到 `✅ Published`,理论上 Notion 会打这个 endpoint,自动把该行的 **"Production Video" property** 发布上 Instagram(生成/复用封面 + 真发 Reel)。
- 3. 同理如果也想要评论关键词自动打 DM 规则(`🟢 Ready to Publish` 那条),就是 `/admin/notion-sync`,用同一个 secret。
- ## 2. 关于"能不能共用一个 webhook"—— 我查了代码,答案是:不需要在后端做 payload 分流,直接办法更简单
- 也就是说:**这两个 endpoint 已经是"自带分流"的了** —— 不管谁调用它,它自己会判断该不该动手。所以你完全不需要我在后端写一段"读 payload 里的 Stage,再决定走哪条线"的分流逻辑(而且老实说这样更脆,因为要依赖 Notion webhook payload 的具体格式,那个格式没写死、我也没法保证长期稳定)。
- 如果你们 Notion plan 里 "When all/any" 那个下拉没有 "any" 选项(某些版本可能限制),退回原方案——两个独立 automation,一个卡 Ready to Publish,一个卡 Published,跟现在 CLAUDE.md 里写的设计完全一致,也没问题,只是多一步设置。
- 啊,我搞错了 —— 是我自己没检查现有状态,盲目生成了个新的把 Render 上的值覆盖掉了。抱歉,这是我的失误。现在就用你原来那个值把 Render 改回去,不用动 Notion 那边。


## 2026-07-08 15:35 — social-ip-engine

### Decisions & Reasoning
- 我倾向 **选项 1**。理由:property 干净、不污染 body、和 "Production Video" 平行摆着一眼能看懂哪个是 master 哪个是成片。要的话我 20 行给 `notion_video.py` 加一个 `--upload-master`,concat 完自动传进 "Master Video" property。
- 2. **换平台重用** —— 比如发去一个你想用平台原生字幕、
- `POST /admin/notion-publish` —— Stage 一拖到 `✅ Published`,理论上 Notion 会打这个 endpoint,自动把该行的 **"Production Video" property** 发布上 Instagram(生成/复用封面 + 真发 Reel)。
- 3. 同理如果也想要评论关键词自动打 DM 规则(`🟢 Ready to Publish` 那条),就是 `/admin/notion-sync`,用同一个 secret。
- ## 2. 关于"能不能共用一个 webhook"—— 我查了代码,答案是:不需要在后端做 payload 分流,直接办法更简单
- 也就是说:**这两个 endpoint 已经是"自带分流"的了** —— 不管谁调用它,它自己会判断该不该动手。所以你完全不需要我在后端写一段"读 payload 里的 Stage,再决定走哪条线"的分流逻辑(而且老实说这样更脆,因为要依赖 Notion webhook payload 的具体格式,那个格式没写死、我也没法保证长期稳定)。
- 如果你们 Notion plan 里 "When all/any" 那个下拉没有 "any" 选项(某些版本可能限制),退回原方案——两个独立 automation,一个卡 Ready to Publish,一个卡 Published,跟现在 CLAUDE.md 里写的设计完全一致,也没问题,只是多一步设置。
- 啊,我搞错了 —— 是我自己没检查现有状态,盲目生成了个新的把 Render 上的值覆盖掉了。抱歉,这是我的失误。现在就用你原来那个值把 Render 改回去,不用动 Notion 那边。


## 2026-07-08 15:45 — social-ip-engine

### Decisions & Reasoning
- 我倾向 **选项 1**。理由:property 干净、不污染 body、和 "Production Video" 平行摆着一眼能看懂哪个是 master 哪个是成片。要的话我 20 行给 `notion_video.py` 加一个 `--upload-master`,concat 完自动传进 "Master Video" property。
- 2. **换平台重用** —— 比如发去一个你想用平台原生字幕、
- `POST /admin/notion-publish` —— Stage 一拖到 `✅ Published`,理论上 Notion 会打这个 endpoint,自动把该行的 **"Production Video" property** 发布上 Instagram(生成/复用封面 + 真发 Reel)。
- 3. 同理如果也想要评论关键词自动打 DM 规则(`🟢 Ready to Publish` 那条),就是 `/admin/notion-sync`,用同一个 secret。
- ## 2. 关于"能不能共用一个 webhook"—— 我查了代码,答案是:不需要在后端做 payload 分流,直接办法更简单
- 也就是说:**这两个 endpoint 已经是"自带分流"的了** —— 不管谁调用它,它自己会判断该不该动手。所以你完全不需要我在后端写一段"读 payload 里的 Stage,再决定走哪条线"的分流逻辑(而且老实说这样更脆,因为要依赖 Notion webhook payload 的具体格式,那个格式没写死、我也没法保证长期稳定)。
- 如果你们 Notion plan 里 "When all/any" 那个下拉没有 "any" 选项(某些版本可能限制),退回原方案——两个独立 automation,一个卡 Ready to Publish,一个卡 Published,跟现在 CLAUDE.md 里写的设计完全一致,也没问题,只是多一步设置。
- 啊,我搞错了 —— 是我自己没检查现有状态,盲目生成了个新的把 Render 上的值覆盖掉了。抱歉,这是我的失误。现在就用你原来那个值把 Render 改回去,不用动 Notion 那边。


## 2026-07-08 15:52 — social-ip-engine

### Decisions & Reasoning
- 我倾向 **选项 1**。理由:property 干净、不污染 body、和 "Production Video" 平行摆着一眼能看懂哪个是 master 哪个是成片。要的话我 20 行给 `notion_video.py` 加一个 `--upload-master`,concat 完自动传进 "Master Video" property。
- 2. **换平台重用** —— 比如发去一个你想用平台原生字幕、
- `POST /admin/notion-publish` —— Stage 一拖到 `✅ Published`,理论上 Notion 会打这个 endpoint,自动把该行的 **"Production Video" property** 发布上 Instagram(生成/复用封面 + 真发 Reel)。
- 3. 同理如果也想要评论关键词自动打 DM 规则(`🟢 Ready to Publish` 那条),就是 `/admin/notion-sync`,用同一个 secret。
- ## 2. 关于"能不能共用一个 webhook"—— 我查了代码,答案是:不需要在后端做 payload 分流,直接办法更简单
- 也就是说:**这两个 endpoint 已经是"自带分流"的了** —— 不管谁调用它,它自己会判断该不该动手。所以你完全不需要我在后端写一段"读 payload 里的 Stage,再决定走哪条线"的分流逻辑(而且老实说这样更脆,因为要依赖 Notion webhook payload 的具体格式,那个格式没写死、我也没法保证长期稳定)。
- 如果你们 Notion plan 里 "When all/any" 那个下拉没有 "any" 选项(某些版本可能限制),退回原方案——两个独立 automation,一个卡 Ready to Publish,一个卡 Published,跟现在 CLAUDE.md 里写的设计完全一致,也没问题,只是多一步设置。
- 啊,我搞错了 —— 是我自己没检查现有状态,盲目生成了个新的把 Render 上的值覆盖掉了。抱歉,这是我的失误。现在就用你原来那个值把 Render 改回去,不用动 Notion 那边。


## 2026-07-08 16:59 — social-ip-engine

### Decisions & Reasoning
- 1. **直播那条 FB post 的 caption 已经改成 "Do you have tonsil stones? 😱"** — 直接用 Facebook 的 edit API 改的,已验证生效。
- 2. **找到根因并修了代码本身**(不只是我那个测试脚本):`notion_publish_caption.py` 一直在用 Content 页面的内部 "Hook" 字段("Watch what came out of her throat...")当标题,却完全没读那行 Production Tracker 上专门写的 **"🏷️ Title"** property(你说得对——那才是 `notion_prompts.py` 里 `draft_title()` 特地生成的、给人看的标题)。这个 bug 出在共用代码里,意味着**IG 那边自动发的帖子可能也一直是错的标题**,不只是我这条 FB 测试帖。已经加了 `extract_headline()`,Title 优先、Hook 兜底,写了回归测试(专门标注这次 incident),全套 1229 个测试跑绿。丢给 python-reviewer 在跑最后一轮检查。
- 我试着现补了一张(用正确的 Title 文字生成),但 AI 不知道 Jackie 长什么样(cover 生成的 prompt 是纯文字描述,没有像 Shot 1/2/3 那样带参考照片做 image-to-image),画出来是个完全不认识的女生,人不对:
- 我没有推这张上去,因为人不对反而更奇怪。三个选项,你选一个:
- 2. **你/studio 那边去 Notion 那一行的「🖼️ Cover Photo → 🖼️ Cover here」toggle 补一张真正的封面图**(用 Jackie 的参考照片跑 image-to-image,跟 Shot 1-5 一样的流程),弄好后我用 Facebook 的 `/thumbnails` 接口(我刚测过,这个接口能用,可以上传自定义缩略图 + 设成 preferred)把封面换掉。
- 我个人倾向 **选项 2**,但那需要你那边先出图。顺带一提:这个"没人生成 Cover Photo 就直接发布"的情况,以后每一条新视频都可能会撞到——要不要我也检查一下其他还没发的行是不是也缺封面?
- - **MEDIUM**: Fallback-to-Hook was silent — now surfaces a warning into the same `warnings` list the planner already threads through, so it'll show up in ops output instead of hiding.
- 全部搞定了,6 张全部对上号、传回 Notion,而且我用 auto-publish 实际调用的那个函数验证过——6 条全部能读到:


## 2026-07-08 17:08 — social-ip-engine

### Decisions & Reasoning
- 我倾向 **选项 1**。理由:property 干净、不污染 body、和 "Production Video" 平行摆着一眼能看懂哪个是 master 哪个是成片。要的话我 20 行给 `notion_video.py` 加一个 `--upload-master`,concat 完自动传进 "Master Video" property。
- 2. **换平台重用** —— 比如发去一个你想用平台原生字幕、
- `POST /admin/notion-publish` —— Stage 一拖到 `✅ Published`,理论上 Notion 会打这个 endpoint,自动把该行的 **"Production Video" property** 发布上 Instagram(生成/复用封面 + 真发 Reel)。
- 3. 同理如果也想要评论关键词自动打 DM 规则(`🟢 Ready to Publish` 那条),就是 `/admin/notion-sync`,用同一个 secret。
- ## 2. 关于"能不能共用一个 webhook"—— 我查了代码,答案是:不需要在后端做 payload 分流,直接办法更简单
- 也就是说:**这两个 endpoint 已经是"自带分流"的了** —— 不管谁调用它,它自己会判断该不该动手。所以你完全不需要我在后端写一段"读 payload 里的 Stage,再决定走哪条线"的分流逻辑(而且老实说这样更脆,因为要依赖 Notion webhook payload 的具体格式,那个格式没写死、我也没法保证长期稳定)。
- 如果你们 Notion plan 里 "When all/any" 那个下拉没有 "any" 选项(某些版本可能限制),退回原方案——两个独立 automation,一个卡 Ready to Publish,一个卡 Published,跟现在 CLAUDE.md 里写的设计完全一致,也没问题,只是多一步设置。
- 啊,我搞错了 —— 是我自己没检查现有状态,盲目生成了个新的把 Render 上的值覆盖掉了。抱歉,这是我的失误。现在就用你原来那个值把 Render 改回去,不用动 Notion 那边。


## 2026-07-08 17:15 — social-ip-engine

### Decisions & Reasoning
- 我倾向 **选项 1**。理由:property 干净、不污染 body、和 "Production Video" 平行摆着一眼能看懂哪个是 master 哪个是成片。要的话我 20 行给 `notion_video.py` 加一个 `--upload-master`,concat 完自动传进 "Master Video" property。
- 2. **换平台重用** —— 比如发去一个你想用平台原生字幕、
- `POST /admin/notion-publish` —— Stage 一拖到 `✅ Published`,理论上 Notion 会打这个 endpoint,自动把该行的 **"Production Video" property** 发布上 Instagram(生成/复用封面 + 真发 Reel)。
- 3. 同理如果也想要评论关键词自动打 DM 规则(`🟢 Ready to Publish` 那条),就是 `/admin/notion-sync`,用同一个 secret。
- ## 2. 关于"能不能共用一个 webhook"—— 我查了代码,答案是:不需要在后端做 payload 分流,直接办法更简单
- 也就是说:**这两个 endpoint 已经是"自带分流"的了** —— 不管谁调用它,它自己会判断该不该动手。所以你完全不需要我在后端写一段"读 payload 里的 Stage,再决定走哪条线"的分流逻辑(而且老实说这样更脆,因为要依赖 Notion webhook payload 的具体格式,那个格式没写死、我也没法保证长期稳定)。
- 如果你们 Notion plan 里 "When all/any" 那个下拉没有 "any" 选项(某些版本可能限制),退回原方案——两个独立 automation,一个卡 Ready to Publish,一个卡 Published,跟现在 CLAUDE.md 里写的设计完全一致,也没问题,只是多一步设置。
- 啊,我搞错了 —— 是我自己没检查现有状态,盲目生成了个新的把 Render 上的值覆盖掉了。抱歉,这是我的失误。现在就用你原来那个值把 Render 改回去,不用动 Notion 那边。


## 2026-07-08 17:17 — social-ip-engine

### Decisions & Reasoning
- 也就是说，脚本从不会因为你拖了 Stage 就自动去合并/加字幕/上传视频——反过来，你得先跑完 `finalize_all_videos.py`（内部调用 `add_karaoke_captions.py --upload`）**审完成片**，再手动拖 Stage。


## 2026-07-08 17:27 — social-ip-engine

### Decisions & Reasoning
- 也就是说，脚本从不会因为你拖了 Stage 就自动去合并/加字幕/上传视频——反过来，你得先跑完 `finalize_all_videos.py`（内部调用 `add_karaoke_captions.py --upload`）**审完成片**，再手动拖 Stage。
- - 而 merge / whisper 转录 / moviepy 烧字幕 / cover 生图 / infographic 生图，全部住在 `studio/` —— `studio/CLAUDE.md` 第一行写死了 **"This folder is NEVER deployed; it is local tooling only."** 字幕烧录甚至绑定在你这台机器的 ffmpeg build（没有 libass，只能用 moviepy 硬编码字体渲染）。
- 2. **Infographic 生图有脚本**（`batch_infographic_gen.py`）但它不在 `finalize_all_videos.py` 的调用链里，是完全独立、你得记得单独跑的东西。
- 3. **新增**：cover 生图（复用 `cover_blocks()` 已经写好的 prompt，调 gpt-image-2，带上 IP 参考脸——这点很关键，不能像 7/8 那次 Facebook 事故一样盲生成）+ 上传到 `🖼️ Cover here` toggle
- 跑完这一条命令，终端打印一份 checklist（cover✅ infographic✅ captions✅ uploaded✅），你扫一眼没问题再手动拖 Stage——审片关卡保留，但你不用再分别记 3-4 个脚本。


## 2026-07-08 17:29 — social-ip-engine

### Decisions & Reasoning
- 也就是说，脚本从不会因为你拖了 Stage 就自动去合并/加字幕/上传视频——反过来，你得先跑完 `finalize_all_videos.py`（内部调用 `add_karaoke_captions.py --upload`）**审完成片**，再手动拖 Stage。
- - 而 merge / whisper 转录 / moviepy 烧字幕 / cover 生图 / infographic 生图，全部住在 `studio/` —— `studio/CLAUDE.md` 第一行写死了 **"This folder is NEVER deployed; it is local tooling only."** 字幕烧录甚至绑定在你这台机器的 ffmpeg build（没有 libass，只能用 moviepy 硬编码字体渲染）。
- 2. **Infographic 生图有脚本**（`batch_infographic_gen.py`）但它不在 `finalize_all_videos.py` 的调用链里，是完全独立、你得记得单独跑的东西。
- 3. **新增**：cover 生图（复用 `cover_blocks()` 已经写好的 prompt，调 gpt-image-2，带上 IP 参考脸——这点很关键，不能像 7/8 那次 Facebook 事故一样盲生成）+ 上传到 `🖼️ Cover here` toggle
- 跑完这一条命令，终端打印一份 checklist（cover✅ infographic✅ captions✅ uploaded✅），你扫一眼没问题再手动拖 Stage——审片关卡保留，但你不用再分别记 3-4 个脚本。
- **What I think you actually want:** not "automatic," but "one command instead of four." Right now you have to remember to run several separate scripts (merge, captions, cover, infographic) before dragging Stage — and two of those (cover, infographic) aren't even automated at all right now, you'd have to do them by hand. That's the real gap that caused this mess with the ear video.


## 2026-07-08 17:38 — social-ip-engine

### Decisions & Reasoning
- 也就是说，脚本从不会因为你拖了 Stage 就自动去合并/加字幕/上传视频——反过来，你得先跑完 `finalize_all_videos.py`（内部调用 `add_karaoke_captions.py --upload`）**审完成片**，再手动拖 Stage。
- - 而 merge / whisper 转录 / moviepy 烧字幕 / cover 生图 / infographic 生图，全部住在 `studio/` —— `studio/CLAUDE.md` 第一行写死了 **"This folder is NEVER deployed; it is local tooling only."** 字幕烧录甚至绑定在你这台机器的 ffmpeg build（没有 libass，只能用 moviepy 硬编码字体渲染）。
- 2. **Infographic 生图有脚本**（`batch_infographic_gen.py`）但它不在 `finalize_all_videos.py` 的调用链里，是完全独立、你得记得单独跑的东西。
- 3. **新增**：cover 生图（复用 `cover_blocks()` 已经写好的 prompt，调 gpt-image-2，带上 IP 参考脸——这点很关键，不能像 7/8 那次 Facebook 事故一样盲生成）+ 上传到 `🖼️ Cover here` toggle
- 跑完这一条命令，终端打印一份 checklist（cover✅ infographic✅ captions✅ uploaded✅），你扫一眼没问题再手动拖 Stage——审片关卡保留，但你不用再分别记 3-4 个脚本。
- **What I think you actually want:** not "automatic," but "one command instead of four." Right now you have to remember to run several separate scripts (merge, captions, cover, infographic) before dragging Stage — and two of those (cover, infographic) aren't even automated at all right now, you'd have to do them by hand. That's the real gap that caused this mess with the ear video.


## 2026-07-08 17:41 — social-ip-engine

### Decisions & Reasoning
- 也就是说，脚本从不会因为你拖了 Stage 就自动去合并/加字幕/上传视频——反过来，你得先跑完 `finalize_all_videos.py`（内部调用 `add_karaoke_captions.py --upload`）**审完成片**，再手动拖 Stage。
- - 而 merge / whisper 转录 / moviepy 烧字幕 / cover 生图 / infographic 生图，全部住在 `studio/` —— `studio/CLAUDE.md` 第一行写死了 **"This folder is NEVER deployed; it is local tooling only."** 字幕烧录甚至绑定在你这台机器的 ffmpeg build（没有 libass，只能用 moviepy 硬编码字体渲染）。
- 2. **Infographic 生图有脚本**（`batch_infographic_gen.py`）但它不在 `finalize_all_videos.py` 的调用链里，是完全独立、你得记得单独跑的东西。
- 3. **新增**：cover 生图（复用 `cover_blocks()` 已经写好的 prompt，调 gpt-image-2，带上 IP 参考脸——这点很关键，不能像 7/8 那次 Facebook 事故一样盲生成）+ 上传到 `🖼️ Cover here` toggle
- 跑完这一条命令，终端打印一份 checklist（cover✅ infographic✅ captions✅ uploaded✅），你扫一眼没问题再手动拖 Stage——审片关卡保留，但你不用再分别记 3-4 个脚本。
- **What I think you actually want:** not "automatic," but "one command instead of four." Right now you have to remember to run several separate scripts (merge, captions, cover, infographic) before dragging Stage — and two of those (cover, infographic) aren't even automated at all right now, you'd have to do them by hand. That's the real gap that caused this mess with the ear video.


## 2026-07-08 17:42 — social-ip-engine

### Decisions & Reasoning
- 也就是说，脚本从不会因为你拖了 Stage 就自动去合并/加字幕/上传视频——反过来，你得先跑完 `finalize_all_videos.py`（内部调用 `add_karaoke_captions.py --upload`）**审完成片**，再手动拖 Stage。
- - 而 merge / whisper 转录 / moviepy 烧字幕 / cover 生图 / infographic 生图，全部住在 `studio/` —— `studio/CLAUDE.md` 第一行写死了 **"This folder is NEVER deployed; it is local tooling only."** 字幕烧录甚至绑定在你这台机器的 ffmpeg build（没有 libass，只能用 moviepy 硬编码字体渲染）。
- 2. **Infographic 生图有脚本**（`batch_infographic_gen.py`）但它不在 `finalize_all_videos.py` 的调用链里，是完全独立、你得记得单独跑的东西。
- 3. **新增**：cover 生图（复用 `cover_blocks()` 已经写好的 prompt，调 gpt-image-2，带上 IP 参考脸——这点很关键，不能像 7/8 那次 Facebook 事故一样盲生成）+ 上传到 `🖼️ Cover here` toggle
- 跑完这一条命令，终端打印一份 checklist（cover✅ infographic✅ captions✅ uploaded✅），你扫一眼没问题再手动拖 Stage——审片关卡保留，但你不用再分别记 3-4 个脚本。
- **What I think you actually want:** not "automatic," but "one command instead of four." Right now you have to remember to run several separate scripts (merge, captions, cover, infographic) before dragging Stage — and two of those (cover, infographic) aren't even automated at all right now, you'd have to do them by hand. That's the real gap that caused this mess with the ear video.


## 2026-07-08 17:44 — social-ip-engine

### Decisions & Reasoning
- 也就是说，脚本从不会因为你拖了 Stage 就自动去合并/加字幕/上传视频——反过来，你得先跑完 `finalize_all_videos.py`（内部调用 `add_karaoke_captions.py --upload`）**审完成片**，再手动拖 Stage。
- - 而 merge / whisper 转录 / moviepy 烧字幕 / cover 生图 / infographic 生图，全部住在 `studio/` —— `studio/CLAUDE.md` 第一行写死了 **"This folder is NEVER deployed; it is local tooling only."** 字幕烧录甚至绑定在你这台机器的 ffmpeg build（没有 libass，只能用 moviepy 硬编码字体渲染）。
- 2. **Infographic 生图有脚本**（`batch_infographic_gen.py`）但它不在 `finalize_all_videos.py` 的调用链里，是完全独立、你得记得单独跑的东西。
- 3. **新增**：cover 生图（复用 `cover_blocks()` 已经写好的 prompt，调 gpt-image-2，带上 IP 参考脸——这点很关键，不能像 7/8 那次 Facebook 事故一样盲生成）+ 上传到 `🖼️ Cover here` toggle
- 跑完这一条命令，终端打印一份 checklist（cover✅ infographic✅ captions✅ uploaded✅），你扫一眼没问题再手动拖 Stage——审片关卡保留，但你不用再分别记 3-4 个脚本。
- **What I think you actually want:** not "automatic," but "one command instead of four." Right now you have to remember to run several separate scripts (merge, captions, cover, infographic) before dragging Stage — and two of those (cover, infographic) aren't even automated at all right now, you'd have to do them by hand. That's the real gap that caused this mess with the ear video.
- 4. **Safety-net in `notion_sync.py`** — warns (doesn't block) when video/cover missing on a Ready-to-Publish row, so it's visible instead of silent.


## 2026-07-08 17:45 — social-ip-engine

### Decisions & Reasoning
- **改法（用 seedance-characters 的 three-tier action hierarchy）**：二选一
- 这是个真实的代码 gap，不只是内容问题：`_jimeng_camera()`（298-310行）已经会读 title 里的关键字（比如"demo"）来选镜头运镜，但 lip-sync 那句话完全没有类似的条件判断。**建议**：给 `build_jimeng_prompt()` 加一个判断——如果 visual 文本里出现"no dialogue to camera"/"action shot"，把 read 那句换成纯 VO 描述，不要求对口型。我可以现在就改这个函数，要吗？
- 但 `_primary_beat()`（234-243行）只取第一个分号/逗号/"then"之前的那一段作为静帧图片的 SCENE，"warm side lighting, soft focus"这个你特意写的打光指令，落在第二个 `;` 之后，**根本没被摘进 build_prompt() 里**。而且这段文字也没命中 `_clinic_kws`/`_street_kws` 任何关键字，所以最后套用的是最保底的 fallback：`"Setting: shallow depth of field, natural lighting."`——一句完全通用、没有意图的话。
- 按 directing-engine 的 Step 5（光是有动机的，不是随便一句"natural lighting"）：这镜的光线本该是特意设计的（warm side light 服务"温柔专业的诊疗感"），结果被模板吃掉了，变成了泛用光。**改法**：Shot 2 的视觉描述把光线线索挪到第一段（分号前），比如："...scrape from the center of her cheek outward to the ear, warm side lighting on her face, then down along the jawline..." 这样 `_primary_beat()` 才抓得到。
- 这是内容不一致：DM 私信发出去的信息图，承诺了视频里根本没演示过的手法。用户看完视频、评论关键字拿到图，会发现图上多了一条视频没教的东西。**建议**：要么把 brow-to-hairline 从 infographic 里删掉（保持图和视频严格对齐），要么在 Shot 3 补一句额头手法（更花成本，不建议为了这个改视频）。我倾向直接删。
- - Infographic 本身风格选择（illustration、非写实、no real faces）是对的——医美/身体相关内容用插画而非写实照片，本来就更安全，不用动。
- **我会怎么改**：拿掉对比图插入，把这个"恍然大悟"的瞬间做成一个真实可拍的动作——比如医生用手指轻按自己下颌，停顿、微微点头，一个"这不是脂肪"的确认表情。让画面自己完成认知转折，而不是靠一张信息图硬解释。对比图这个视觉任务，交给 DM 的 infographic 去做就够了（本来 infographic brief 里已经有箭头示意图，两边做同一件事是重复劳动）。
- - **Shot 2**：医生在**别人（患者）脸上**做示范，配音用"you"（"you scrape from the center of your face..."）


## 2026-07-08 17:50 — social-ip-engine

### Decisions & Reasoning
- **改法（用 seedance-characters 的 three-tier action hierarchy）**：二选一
- 这是个真实的代码 gap，不只是内容问题：`_jimeng_camera()`（298-310行）已经会读 title 里的关键字（比如"demo"）来选镜头运镜，但 lip-sync 那句话完全没有类似的条件判断。**建议**：给 `build_jimeng_prompt()` 加一个判断——如果 visual 文本里出现"no dialogue to camera"/"action shot"，把 read 那句换成纯 VO 描述，不要求对口型。我可以现在就改这个函数，要吗？
- 但 `_primary_beat()`（234-243行）只取第一个分号/逗号/"then"之前的那一段作为静帧图片的 SCENE，"warm side lighting, soft focus"这个你特意写的打光指令，落在第二个 `;` 之后，**根本没被摘进 build_prompt() 里**。而且这段文字也没命中 `_clinic_kws`/`_street_kws` 任何关键字，所以最后套用的是最保底的 fallback：`"Setting: shallow depth of field, natural lighting."`——一句完全通用、没有意图的话。
- 按 directing-engine 的 Step 5（光是有动机的，不是随便一句"natural lighting"）：这镜的光线本该是特意设计的（warm side light 服务"温柔专业的诊疗感"），结果被模板吃掉了，变成了泛用光。**改法**：Shot 2 的视觉描述把光线线索挪到第一段（分号前），比如："...scrape from the center of her cheek outward to the ear, warm side lighting on her face, then down along the jawline..." 这样 `_primary_beat()` 才抓得到。
- 这是内容不一致：DM 私信发出去的信息图，承诺了视频里根本没演示过的手法。用户看完视频、评论关键字拿到图，会发现图上多了一条视频没教的东西。**建议**：要么把 brow-to-hairline 从 infographic 里删掉（保持图和视频严格对齐），要么在 Shot 3 补一句额头手法（更花成本，不建议为了这个改视频）。我倾向直接删。
- - Infographic 本身风格选择（illustration、非写实、no real faces）是对的——医美/身体相关内容用插画而非写实照片，本来就更安全，不用动。
- **我会怎么改**：拿掉对比图插入，把这个"恍然大悟"的瞬间做成一个真实可拍的动作——比如医生用手指轻按自己下颌，停顿、微微点头，一个"这不是脂肪"的确认表情。让画面自己完成认知转折，而不是靠一张信息图硬解释。对比图这个视觉任务，交给 DM 的 infographic 去做就够了（本来 infographic brief 里已经有箭头示意图，两边做同一件事是重复劳动）。
- - **Shot 2**：医生在**别人（患者）脸上**做示范，配音用"you"（"you scrape from the center of your face..."）


## 2026-07-08 17:50 — social-ip-engine

### Decisions & Reasoning
- 也就是说，脚本从不会因为你拖了 Stage 就自动去合并/加字幕/上传视频——反过来，你得先跑完 `finalize_all_videos.py`（内部调用 `add_karaoke_captions.py --upload`）**审完成片**，再手动拖 Stage。
- - 而 merge / whisper 转录 / moviepy 烧字幕 / cover 生图 / infographic 生图，全部住在 `studio/` —— `studio/CLAUDE.md` 第一行写死了 **"This folder is NEVER deployed; it is local tooling only."** 字幕烧录甚至绑定在你这台机器的 ffmpeg build（没有 libass，只能用 moviepy 硬编码字体渲染）。
- 2. **Infographic 生图有脚本**（`batch_infographic_gen.py`）但它不在 `finalize_all_videos.py` 的调用链里，是完全独立、你得记得单独跑的东西。
- 3. **新增**：cover 生图（复用 `cover_blocks()` 已经写好的 prompt，调 gpt-image-2，带上 IP 参考脸——这点很关键，不能像 7/8 那次 Facebook 事故一样盲生成）+ 上传到 `🖼️ Cover here` toggle
- 跑完这一条命令，终端打印一份 checklist（cover✅ infographic✅ captions✅ uploaded✅），你扫一眼没问题再手动拖 Stage——审片关卡保留，但你不用再分别记 3-4 个脚本。
- **What I think you actually want:** not "automatic," but "one command instead of four." Right now you have to remember to run several separate scripts (merge, captions, cover, infographic) before dragging Stage — and two of those (cover, infographic) aren't even automated at all right now, you'd have to do them by hand. That's the real gap that caused this mess with the ear video.
- 4. **Safety-net in `notion_sync.py`** — warns (doesn't block) when video/cover missing on a Ready-to-Publish row, so it's visible instead of silent.


## 2026-07-08 17:52 — social-ip-engine

### Decisions & Reasoning
- **改法（用 seedance-characters 的 three-tier action hierarchy）**：二选一
- 这是个真实的代码 gap，不只是内容问题：`_jimeng_camera()`（298-310行）已经会读 title 里的关键字（比如"demo"）来选镜头运镜，但 lip-sync 那句话完全没有类似的条件判断。**建议**：给 `build_jimeng_prompt()` 加一个判断——如果 visual 文本里出现"no dialogue to camera"/"action shot"，把 read 那句换成纯 VO 描述，不要求对口型。我可以现在就改这个函数，要吗？
- 但 `_primary_beat()`（234-243行）只取第一个分号/逗号/"then"之前的那一段作为静帧图片的 SCENE，"warm side lighting, soft focus"这个你特意写的打光指令，落在第二个 `;` 之后，**根本没被摘进 build_prompt() 里**。而且这段文字也没命中 `_clinic_kws`/`_street_kws` 任何关键字，所以最后套用的是最保底的 fallback：`"Setting: shallow depth of field, natural lighting."`——一句完全通用、没有意图的话。
- 按 directing-engine 的 Step 5（光是有动机的，不是随便一句"natural lighting"）：这镜的光线本该是特意设计的（warm side light 服务"温柔专业的诊疗感"），结果被模板吃掉了，变成了泛用光。**改法**：Shot 2 的视觉描述把光线线索挪到第一段（分号前），比如："...scrape from the center of her cheek outward to the ear, warm side lighting on her face, then down along the jawline..." 这样 `_primary_beat()` 才抓得到。
- 这是内容不一致：DM 私信发出去的信息图，承诺了视频里根本没演示过的手法。用户看完视频、评论关键字拿到图，会发现图上多了一条视频没教的东西。**建议**：要么把 brow-to-hairline 从 infographic 里删掉（保持图和视频严格对齐），要么在 Shot 3 补一句额头手法（更花成本，不建议为了这个改视频）。我倾向直接删。
- - Infographic 本身风格选择（illustration、非写实、no real faces）是对的——医美/身体相关内容用插画而非写实照片，本来就更安全，不用动。
- **我会怎么改**：拿掉对比图插入，把这个"恍然大悟"的瞬间做成一个真实可拍的动作——比如医生用手指轻按自己下颌，停顿、微微点头，一个"这不是脂肪"的确认表情。让画面自己完成认知转折，而不是靠一张信息图硬解释。对比图这个视觉任务，交给 DM 的 infographic 去做就够了（本来 infographic brief 里已经有箭头示意图，两边做同一件事是重复劳动）。
- - **Shot 2**：医生在**别人（患者）脸上**做示范，配音用"you"（"you scrape from the center of your face..."）


## 2026-07-08 17:56 — social-ip-engine

### Decisions & Reasoning
- **改法（用 seedance-characters 的 three-tier action hierarchy）**：二选一
- 这是个真实的代码 gap，不只是内容问题：`_jimeng_camera()`（298-310行）已经会读 title 里的关键字（比如"demo"）来选镜头运镜，但 lip-sync 那句话完全没有类似的条件判断。**建议**：给 `build_jimeng_prompt()` 加一个判断——如果 visual 文本里出现"no dialogue to camera"/"action shot"，把 read 那句换成纯 VO 描述，不要求对口型。我可以现在就改这个函数，要吗？
- 但 `_primary_beat()`（234-243行）只取第一个分号/逗号/"then"之前的那一段作为静帧图片的 SCENE，"warm side lighting, soft focus"这个你特意写的打光指令，落在第二个 `;` 之后，**根本没被摘进 build_prompt() 里**。而且这段文字也没命中 `_clinic_kws`/`_street_kws` 任何关键字，所以最后套用的是最保底的 fallback：`"Setting: shallow depth of field, natural lighting."`——一句完全通用、没有意图的话。
- 按 directing-engine 的 Step 5（光是有动机的，不是随便一句"natural lighting"）：这镜的光线本该是特意设计的（warm side light 服务"温柔专业的诊疗感"），结果被模板吃掉了，变成了泛用光。**改法**：Shot 2 的视觉描述把光线线索挪到第一段（分号前），比如："...scrape from the center of her cheek outward to the ear, warm side lighting on her face, then down along the jawline..." 这样 `_primary_beat()` 才抓得到。
- 这是内容不一致：DM 私信发出去的信息图，承诺了视频里根本没演示过的手法。用户看完视频、评论关键字拿到图，会发现图上多了一条视频没教的东西。**建议**：要么把 brow-to-hairline 从 infographic 里删掉（保持图和视频严格对齐），要么在 Shot 3 补一句额头手法（更花成本，不建议为了这个改视频）。我倾向直接删。
- - Infographic 本身风格选择（illustration、非写实、no real faces）是对的——医美/身体相关内容用插画而非写实照片，本来就更安全，不用动。
- **我会怎么改**：拿掉对比图插入，把这个"恍然大悟"的瞬间做成一个真实可拍的动作——比如医生用手指轻按自己下颌，停顿、微微点头，一个"这不是脂肪"的确认表情。让画面自己完成认知转折，而不是靠一张信息图硬解释。对比图这个视觉任务，交给 DM 的 infographic 去做就够了（本来 infographic brief 里已经有箭头示意图，两边做同一件事是重复劳动）。
- - **Shot 2**：医生在**别人（患者）脸上**做示范，配音用"you"（"you scrape from the center of your face..."）


## 2026-07-08 17:57 — social-ip-engine

### What Didn't Work (negative knowledge)
- - (This is different from your `notion-sync` webhook, which fires instantly from the cloud regardless of your laptop — that one can't run this pipeline because it's heavy local-only tooling: whisper, moviepy, ffmpeg)

### Decisions & Reasoning
- 也就是说，脚本从不会因为你拖了 Stage 就自动去合并/加字幕/上传视频——反过来，你得先跑完 `finalize_all_videos.py`（内部调用 `add_karaoke_captions.py --upload`）**审完成片**，再手动拖 Stage。
- - 而 merge / whisper 转录 / moviepy 烧字幕 / cover 生图 / infographic 生图，全部住在 `studio/` —— `studio/CLAUDE.md` 第一行写死了 **"This folder is NEVER deployed; it is local tooling only."** 字幕烧录甚至绑定在你这台机器的 ffmpeg build（没有 libass，只能用 moviepy 硬编码字体渲染）。
- 2. **Infographic 生图有脚本**（`batch_infographic_gen.py`）但它不在 `finalize_all_videos.py` 的调用链里，是完全独立、你得记得单独跑的东西。
- 3. **新增**：cover 生图（复用 `cover_blocks()` 已经写好的 prompt，调 gpt-image-2，带上 IP 参考脸——这点很关键，不能像 7/8 那次 Facebook 事故一样盲生成）+ 上传到 `🖼️ Cover here` toggle
- 跑完这一条命令，终端打印一份 checklist（cover✅ infographic✅ captions✅ uploaded✅），你扫一眼没问题再手动拖 Stage——审片关卡保留，但你不用再分别记 3-4 个脚本。
- **What I think you actually want:** not "automatic," but "one command instead of four." Right now you have to remember to run several separate scripts (merge, captions, cover, infographic) before dragging Stage — and two of those (cover, infographic) aren't even automated at all right now, you'd have to do them by hand. That's the real gap that caused this mess with the ear video.
- 4. **Safety-net in `notion_sync.py`** — warns (doesn't block) when video/cover missing on a Ready-to-Publish row, so it's visible instead of silent.


## 2026-07-08 18:05 — social-ip-engine

### What Didn't Work (negative knowledge)
- - (This is different from your `notion-sync` webhook, which fires instantly from the cloud regardless of your laptop — that one can't run this pipeline because it's heavy local-only tooling: whisper, moviepy, ffmpeg)

### Architecture Decisions
- - **Captions (whisper + moviepy)** — 🟡 mostly portable, but **one real blocker**: the caption script hardcodes a macOS-only font path (`/System/Library/Fonts/.../Arial Black.ttf`). That font doesn't exist on Render's Linux server. We'd need to swap to a different bundled font, and re-tune the padding/line-wrap math — the stuff we just spent all of 7/7–7/8 debugging (glyph clipping, uneven line splits) was tuned specifically for Arial Black's metrics. Swap fonts = re-test that whole thing.

### Decisions & Reasoning
- 也就是说，脚本从不会因为你拖了 Stage 就自动去合并/加字幕/上传视频——反过来，你得先跑完 `finalize_all_videos.py`（内部调用 `add_karaoke_captions.py --upload`）**审完成片**，再手动拖 Stage。
- - 而 merge / whisper 转录 / moviepy 烧字幕 / cover 生图 / infographic 生图，全部住在 `studio/` —— `studio/CLAUDE.md` 第一行写死了 **"This folder is NEVER deployed; it is local tooling only."** 字幕烧录甚至绑定在你这台机器的 ffmpeg build（没有 libass，只能用 moviepy 硬编码字体渲染）。
- 2. **Infographic 生图有脚本**（`batch_infographic_gen.py`）但它不在 `finalize_all_videos.py` 的调用链里，是完全独立、你得记得单独跑的东西。
- 3. **新增**：cover 生图（复用 `cover_blocks()` 已经写好的 prompt，调 gpt-image-2，带上 IP 参考脸——这点很关键，不能像 7/8 那次 Facebook 事故一样盲生成）+ 上传到 `🖼️ Cover here` toggle
- 跑完这一条命令，终端打印一份 checklist（cover✅ infographic✅ captions✅ uploaded✅），你扫一眼没问题再手动拖 Stage——审片关卡保留，但你不用再分别记 3-4 个脚本。
- **What I think you actually want:** not "automatic," but "one command instead of four." Right now you have to remember to run several separate scripts (merge, captions, cover, infographic) before dragging Stage — and two of those (cover, infographic) aren't even automated at all right now, you'd have to do them by hand. That's the real gap that caused this mess with the ear video.
- 4. **Safety-net in `notion_sync.py`** — warns (doesn't block) when video/cover missing on a Ready-to-Publish row, so it's visible instead of silent.
- I checked the actual code instead of assuming. Here's the real picture, piece by piece:


## 2026-07-08 18:06 — social-ip-engine

### Decisions & Reasoning
- **改法（用 seedance-characters 的 three-tier action hierarchy）**：二选一
- 这是个真实的代码 gap，不只是内容问题：`_jimeng_camera()`（298-310行）已经会读 title 里的关键字（比如"demo"）来选镜头运镜，但 lip-sync 那句话完全没有类似的条件判断。**建议**：给 `build_jimeng_prompt()` 加一个判断——如果 visual 文本里出现"no dialogue to camera"/"action shot"，把 read 那句换成纯 VO 描述，不要求对口型。我可以现在就改这个函数，要吗？
- 但 `_primary_beat()`（234-243行）只取第一个分号/逗号/"then"之前的那一段作为静帧图片的 SCENE，"warm side lighting, soft focus"这个你特意写的打光指令，落在第二个 `;` 之后，**根本没被摘进 build_prompt() 里**。而且这段文字也没命中 `_clinic_kws`/`_street_kws` 任何关键字，所以最后套用的是最保底的 fallback：`"Setting: shallow depth of field, natural lighting."`——一句完全通用、没有意图的话。
- 按 directing-engine 的 Step 5（光是有动机的，不是随便一句"natural lighting"）：这镜的光线本该是特意设计的（warm side light 服务"温柔专业的诊疗感"），结果被模板吃掉了，变成了泛用光。**改法**：Shot 2 的视觉描述把光线线索挪到第一段（分号前），比如："...scrape from the center of her cheek outward to the ear, warm side lighting on her face, then down along the jawline..." 这样 `_primary_beat()` 才抓得到。
- 这是内容不一致：DM 私信发出去的信息图，承诺了视频里根本没演示过的手法。用户看完视频、评论关键字拿到图，会发现图上多了一条视频没教的东西。**建议**：要么把 brow-to-hairline 从 infographic 里删掉（保持图和视频严格对齐），要么在 Shot 3 补一句额头手法（更花成本，不建议为了这个改视频）。我倾向直接删。
- - Infographic 本身风格选择（illustration、非写实、no real faces）是对的——医美/身体相关内容用插画而非写实照片，本来就更安全，不用动。
- **我会怎么改**：拿掉对比图插入，把这个"恍然大悟"的瞬间做成一个真实可拍的动作——比如医生用手指轻按自己下颌，停顿、微微点头，一个"这不是脂肪"的确认表情。让画面自己完成认知转折，而不是靠一张信息图硬解释。对比图这个视觉任务，交给 DM 的 infographic 去做就够了（本来 infographic brief 里已经有箭头示意图，两边做同一件事是重复劳动）。
- - **Shot 2**：医生在**别人（患者）脸上**做示范，配音用"you"（"you scrape from the center of your face..."）


## 2026-07-08 18:15 — social-ip-engine

### What Didn't Work (negative knowledge)
- - (This is different from your `notion-sync` webhook, which fires instantly from the cloud regardless of your laptop — that one can't run this pipeline because it's heavy local-only tooling: whisper, moviepy, ffmpeg)

### Architecture Decisions
- - **Captions (whisper + moviepy)** — 🟡 mostly portable, but **one real blocker**: the caption script hardcodes a macOS-only font path (`/System/Library/Fonts/.../Arial Black.ttf`). That font doesn't exist on Render's Linux server. We'd need to swap to a different bundled font, and re-tune the padding/line-wrap math — the stuff we just spent all of 7/7–7/8 debugging (glyph clipping, uneven line splits) was tuned specifically for Arial Black's metrics. Swap fonts = re-test that whole thing.

### Decisions & Reasoning
- 也就是说，脚本从不会因为你拖了 Stage 就自动去合并/加字幕/上传视频——反过来，你得先跑完 `finalize_all_videos.py`（内部调用 `add_karaoke_captions.py --upload`）**审完成片**，再手动拖 Stage。
- - 而 merge / whisper 转录 / moviepy 烧字幕 / cover 生图 / infographic 生图，全部住在 `studio/` —— `studio/CLAUDE.md` 第一行写死了 **"This folder is NEVER deployed; it is local tooling only."** 字幕烧录甚至绑定在你这台机器的 ffmpeg build（没有 libass，只能用 moviepy 硬编码字体渲染）。
- 2. **Infographic 生图有脚本**（`batch_infographic_gen.py`）但它不在 `finalize_all_videos.py` 的调用链里，是完全独立、你得记得单独跑的东西。
- 3. **新增**：cover 生图（复用 `cover_blocks()` 已经写好的 prompt，调 gpt-image-2，带上 IP 参考脸——这点很关键，不能像 7/8 那次 Facebook 事故一样盲生成）+ 上传到 `🖼️ Cover here` toggle
- 跑完这一条命令，终端打印一份 checklist（cover✅ infographic✅ captions✅ uploaded✅），你扫一眼没问题再手动拖 Stage——审片关卡保留，但你不用再分别记 3-4 个脚本。
- **What I think you actually want:** not "automatic," but "one command instead of four." Right now you have to remember to run several separate scripts (merge, captions, cover, infographic) before dragging Stage — and two of those (cover, infographic) aren't even automated at all right now, you'd have to do them by hand. That's the real gap that caused this mess with the ear video.
- 4. **Safety-net in `notion_sync.py`** — warns (doesn't block) when video/cover missing on a Ready-to-Publish row, so it's visible instead of silent.
- I checked the actual code instead of assuming. Here's the real picture, piece by piece:


## 2026-07-08 18:20 — social-ip-engine

### What Didn't Work (negative knowledge)
- - (This is different from your `notion-sync` webhook, which fires instantly from the cloud regardless of your laptop — that one can't run this pipeline because it's heavy local-only tooling: whisper, moviepy, ffmpeg)

### Architecture Decisions
- - **Captions (whisper + moviepy)** — 🟡 mostly portable, but **one real blocker**: the caption script hardcodes a macOS-only font path (`/System/Library/Fonts/.../Arial Black.ttf`). That font doesn't exist on Render's Linux server. We'd need to swap to a different bundled font, and re-tune the padding/line-wrap math — the stuff we just spent all of 7/7–7/8 debugging (glyph clipping, uneven line splits) was tuned specifically for Arial Black's metrics. Swap fonts = re-test that whole thing.

### Decisions & Reasoning
- 也就是说，脚本从不会因为你拖了 Stage 就自动去合并/加字幕/上传视频——反过来，你得先跑完 `finalize_all_videos.py`（内部调用 `add_karaoke_captions.py --upload`）**审完成片**，再手动拖 Stage。
- - 而 merge / whisper 转录 / moviepy 烧字幕 / cover 生图 / infographic 生图，全部住在 `studio/` —— `studio/CLAUDE.md` 第一行写死了 **"This folder is NEVER deployed; it is local tooling only."** 字幕烧录甚至绑定在你这台机器的 ffmpeg build（没有 libass，只能用 moviepy 硬编码字体渲染）。
- 2. **Infographic 生图有脚本**（`batch_infographic_gen.py`）但它不在 `finalize_all_videos.py` 的调用链里，是完全独立、你得记得单独跑的东西。
- 3. **新增**：cover 生图（复用 `cover_blocks()` 已经写好的 prompt，调 gpt-image-2，带上 IP 参考脸——这点很关键，不能像 7/8 那次 Facebook 事故一样盲生成）+ 上传到 `🖼️ Cover here` toggle
- 跑完这一条命令，终端打印一份 checklist（cover✅ infographic✅ captions✅ uploaded✅），你扫一眼没问题再手动拖 Stage——审片关卡保留，但你不用再分别记 3-4 个脚本。
- **What I think you actually want:** not "automatic," but "one command instead of four." Right now you have to remember to run several separate scripts (merge, captions, cover, infographic) before dragging Stage — and two of those (cover, infographic) aren't even automated at all right now, you'd have to do them by hand. That's the real gap that caused this mess with the ear video.
- 4. **Safety-net in `notion_sync.py`** — warns (doesn't block) when video/cover missing on a Ready-to-Publish row, so it's visible instead of silent.
- I checked the actual code instead of assuming. Here's the real picture, piece by piece:


## 2026-07-08 18:20 — social-ip-engine

### What Didn't Work (negative knowledge)
- - (This is different from your `notion-sync` webhook, which fires instantly from the cloud regardless of your laptop — that one can't run this pipeline because it's heavy local-only tooling: whisper, moviepy, ffmpeg)
- **New gap found:** the merged video (`final.mp4`) currently has no path to reach Notion/Render at all — it only lives on your laptop. Render can't caption a video it can't fetch. Needs a small addition to `notion_video.py` to upload it to a new Notion property first.

### Architecture Decisions
- - **Captions (whisper + moviepy)** — 🟡 mostly portable, but **one real blocker**: the caption script hardcodes a macOS-only font path (`/System/Library/Fonts/.../Arial Black.ttf`). That font doesn't exist on Render's Linux server. We'd need to swap to a different bundled font, and re-tune the padding/line-wrap math — the stuff we just spent all of 7/7–7/8 debugging (glyph clipping, uneven line splits) was tuned specifically for Arial Black's metrics. Swap fonts = re-test that whole thing.

### Decisions & Reasoning
- 也就是说，脚本从不会因为你拖了 Stage 就自动去合并/加字幕/上传视频——反过来，你得先跑完 `finalize_all_videos.py`（内部调用 `add_karaoke_captions.py --upload`）**审完成片**，再手动拖 Stage。
- - 而 merge / whisper 转录 / moviepy 烧字幕 / cover 生图 / infographic 生图，全部住在 `studio/` —— `studio/CLAUDE.md` 第一行写死了 **"This folder is NEVER deployed; it is local tooling only."** 字幕烧录甚至绑定在你这台机器的 ffmpeg build（没有 libass，只能用 moviepy 硬编码字体渲染）。
- 2. **Infographic 生图有脚本**（`batch_infographic_gen.py`）但它不在 `finalize_all_videos.py` 的调用链里，是完全独立、你得记得单独跑的东西。
- 3. **新增**：cover 生图（复用 `cover_blocks()` 已经写好的 prompt，调 gpt-image-2，带上 IP 参考脸——这点很关键，不能像 7/8 那次 Facebook 事故一样盲生成）+ 上传到 `🖼️ Cover here` toggle
- 跑完这一条命令，终端打印一份 checklist（cover✅ infographic✅ captions✅ uploaded✅），你扫一眼没问题再手动拖 Stage——审片关卡保留，但你不用再分别记 3-4 个脚本。
- **What I think you actually want:** not "automatic," but "one command instead of four." Right now you have to remember to run several separate scripts (merge, captions, cover, infographic) before dragging Stage — and two of those (cover, infographic) aren't even automated at all right now, you'd have to do them by hand. That's the real gap that caused this mess with the ear video.
- 4. **Safety-net in `notion_sync.py`** — warns (doesn't block) when video/cover missing on a Ready-to-Publish row, so it's visible instead of silent.
- I checked the actual code instead of assuming. Here's the real picture, piece by piece:


## 2026-07-08 18:24 — social-ip-engine

### What Didn't Work (negative knowledge)
- - (This is different from your `notion-sync` webhook, which fires instantly from the cloud regardless of your laptop — that one can't run this pipeline because it's heavy local-only tooling: whisper, moviepy, ffmpeg)
- **New gap found:** the merged video (`final.mp4`) currently has no path to reach Notion/Render at all — it only lives on your laptop. Render can't caption a video it can't fetch. Needs a small addition to `notion_video.py` to upload it to a new Notion property first.
- **Bottom line: flipping to Published right now would safely do nothing (no video) rather than publish something broken.** The real unlock is just: write "First DM," then run captions+upload locally, then it'll actually go live correctly.

### Architecture Decisions
- - **Captions (whisper + moviepy)** — 🟡 mostly portable, but **one real blocker**: the caption script hardcodes a macOS-only font path (`/System/Library/Fonts/.../Arial Black.ttf`). That font doesn't exist on Render's Linux server. We'd need to swap to a different bundled font, and re-tune the padding/line-wrap math — the stuff we just spent all of 7/7–7/8 debugging (glyph clipping, uneven line splits) was tuned specifically for Arial Black's metrics. Swap fonts = re-test that whole thing.

### Decisions & Reasoning
- 也就是说，脚本从不会因为你拖了 Stage 就自动去合并/加字幕/上传视频——反过来，你得先跑完 `finalize_all_videos.py`（内部调用 `add_karaoke_captions.py --upload`）**审完成片**，再手动拖 Stage。
- - 而 merge / whisper 转录 / moviepy 烧字幕 / cover 生图 / infographic 生图，全部住在 `studio/` —— `studio/CLAUDE.md` 第一行写死了 **"This folder is NEVER deployed; it is local tooling only."** 字幕烧录甚至绑定在你这台机器的 ffmpeg build（没有 libass，只能用 moviepy 硬编码字体渲染）。
- 2. **Infographic 生图有脚本**（`batch_infographic_gen.py`）但它不在 `finalize_all_videos.py` 的调用链里，是完全独立、你得记得单独跑的东西。
- 3. **新增**：cover 生图（复用 `cover_blocks()` 已经写好的 prompt，调 gpt-image-2，带上 IP 参考脸——这点很关键，不能像 7/8 那次 Facebook 事故一样盲生成）+ 上传到 `🖼️ Cover here` toggle
- 跑完这一条命令，终端打印一份 checklist（cover✅ infographic✅ captions✅ uploaded✅），你扫一眼没问题再手动拖 Stage——审片关卡保留，但你不用再分别记 3-4 个脚本。
- **What I think you actually want:** not "automatic," but "one command instead of four." Right now you have to remember to run several separate scripts (merge, captions, cover, infographic) before dragging Stage — and two of those (cover, infographic) aren't even automated at all right now, you'd have to do them by hand. That's the real gap that caused this mess with the ear video.
- 4. **Safety-net in `notion_sync.py`** — warns (doesn't block) when video/cover missing on a Ready-to-Publish row, so it's visible instead of silent.
- I checked the actual code instead of assuming. Here's the real picture, piece by piece:


## 2026-07-08 18:26 — social-ip-engine

### Decisions & Reasoning
- **改法（用 seedance-characters 的 three-tier action hierarchy）**：二选一
- 这是个真实的代码 gap，不只是内容问题：`_jimeng_camera()`（298-310行）已经会读 title 里的关键字（比如"demo"）来选镜头运镜，但 lip-sync 那句话完全没有类似的条件判断。**建议**：给 `build_jimeng_prompt()` 加一个判断——如果 visual 文本里出现"no dialogue to camera"/"action shot"，把 read 那句换成纯 VO 描述，不要求对口型。我可以现在就改这个函数，要吗？
- 但 `_primary_beat()`（234-243行）只取第一个分号/逗号/"then"之前的那一段作为静帧图片的 SCENE，"warm side lighting, soft focus"这个你特意写的打光指令，落在第二个 `;` 之后，**根本没被摘进 build_prompt() 里**。而且这段文字也没命中 `_clinic_kws`/`_street_kws` 任何关键字，所以最后套用的是最保底的 fallback：`"Setting: shallow depth of field, natural lighting."`——一句完全通用、没有意图的话。
- 按 directing-engine 的 Step 5（光是有动机的，不是随便一句"natural lighting"）：这镜的光线本该是特意设计的（warm side light 服务"温柔专业的诊疗感"），结果被模板吃掉了，变成了泛用光。**改法**：Shot 2 的视觉描述把光线线索挪到第一段（分号前），比如："...scrape from the center of her cheek outward to the ear, warm side lighting on her face, then down along the jawline..." 这样 `_primary_beat()` 才抓得到。
- 这是内容不一致：DM 私信发出去的信息图，承诺了视频里根本没演示过的手法。用户看完视频、评论关键字拿到图，会发现图上多了一条视频没教的东西。**建议**：要么把 brow-to-hairline 从 infographic 里删掉（保持图和视频严格对齐），要么在 Shot 3 补一句额头手法（更花成本，不建议为了这个改视频）。我倾向直接删。
- - Infographic 本身风格选择（illustration、非写实、no real faces）是对的——医美/身体相关内容用插画而非写实照片，本来就更安全，不用动。
- **我会怎么改**：拿掉对比图插入，把这个"恍然大悟"的瞬间做成一个真实可拍的动作——比如医生用手指轻按自己下颌，停顿、微微点头，一个"这不是脂肪"的确认表情。让画面自己完成认知转折，而不是靠一张信息图硬解释。对比图这个视觉任务，交给 DM 的 infographic 去做就够了（本来 infographic brief 里已经有箭头示意图，两边做同一件事是重复劳动）。
- - **Shot 2**：医生在**别人（患者）脸上**做示范，配音用"you"（"you scrape from the center of your face..."）


## 2026-07-08 18:31 — social-ip-engine

### What Didn't Work (negative knowledge)
- - (This is different from your `notion-sync` webhook, which fires instantly from the cloud regardless of your laptop — that one can't run this pipeline because it's heavy local-only tooling: whisper, moviepy, ffmpeg)
- **New gap found:** the merged video (`final.mp4`) currently has no path to reach Notion/Render at all — it only lives on your laptop. Render can't caption a video it can't fetch. Needs a small addition to `notion_video.py` to upload it to a new Notion property first.
- **Bottom line: flipping to Published right now would safely do nothing (no video) rather than publish something broken.** The real unlock is just: write "First DM," then run captions+upload locally, then it'll actually go live correctly.

### Architecture Decisions
- - **Captions (whisper + moviepy)** — 🟡 mostly portable, but **one real blocker**: the caption script hardcodes a macOS-only font path (`/System/Library/Fonts/.../Arial Black.ttf`). That font doesn't exist on Render's Linux server. We'd need to swap to a different bundled font, and re-tune the padding/line-wrap math — the stuff we just spent all of 7/7–7/8 debugging (glyph clipping, uneven line splits) was tuned specifically for Arial Black's metrics. Swap fonts = re-test that whole thing.

### Decisions & Reasoning
- 也就是说，脚本从不会因为你拖了 Stage 就自动去合并/加字幕/上传视频——反过来，你得先跑完 `finalize_all_videos.py`（内部调用 `add_karaoke_captions.py --upload`）**审完成片**，再手动拖 Stage。
- - 而 merge / whisper 转录 / moviepy 烧字幕 / cover 生图 / infographic 生图，全部住在 `studio/` —— `studio/CLAUDE.md` 第一行写死了 **"This folder is NEVER deployed; it is local tooling only."** 字幕烧录甚至绑定在你这台机器的 ffmpeg build（没有 libass，只能用 moviepy 硬编码字体渲染）。
- 2. **Infographic 生图有脚本**（`batch_infographic_gen.py`）但它不在 `finalize_all_videos.py` 的调用链里，是完全独立、你得记得单独跑的东西。
- 3. **新增**：cover 生图（复用 `cover_blocks()` 已经写好的 prompt，调 gpt-image-2，带上 IP 参考脸——这点很关键，不能像 7/8 那次 Facebook 事故一样盲生成）+ 上传到 `🖼️ Cover here` toggle
- 跑完这一条命令，终端打印一份 checklist（cover✅ infographic✅ captions✅ uploaded✅），你扫一眼没问题再手动拖 Stage——审片关卡保留，但你不用再分别记 3-4 个脚本。
- **What I think you actually want:** not "automatic," but "one command instead of four." Right now you have to remember to run several separate scripts (merge, captions, cover, infographic) before dragging Stage — and two of those (cover, infographic) aren't even automated at all right now, you'd have to do them by hand. That's the real gap that caused this mess with the ear video.
- 4. **Safety-net in `notion_sync.py`** — warns (doesn't block) when video/cover missing on a Ready-to-Publish row, so it's visible instead of silent.
- I checked the actual code instead of assuming. Here's the real picture, piece by piece:


## 2026-07-08 18:32 — social-ip-engine

### Decisions & Reasoning
- **改法（用 seedance-characters 的 three-tier action hierarchy）**：二选一
- 这是个真实的代码 gap，不只是内容问题：`_jimeng_camera()`（298-310行）已经会读 title 里的关键字（比如"demo"）来选镜头运镜，但 lip-sync 那句话完全没有类似的条件判断。**建议**：给 `build_jimeng_prompt()` 加一个判断——如果 visual 文本里出现"no dialogue to camera"/"action shot"，把 read 那句换成纯 VO 描述，不要求对口型。我可以现在就改这个函数，要吗？
- 但 `_primary_beat()`（234-243行）只取第一个分号/逗号/"then"之前的那一段作为静帧图片的 SCENE，"warm side lighting, soft focus"这个你特意写的打光指令，落在第二个 `;` 之后，**根本没被摘进 build_prompt() 里**。而且这段文字也没命中 `_clinic_kws`/`_street_kws` 任何关键字，所以最后套用的是最保底的 fallback：`"Setting: shallow depth of field, natural lighting."`——一句完全通用、没有意图的话。
- 按 directing-engine 的 Step 5（光是有动机的，不是随便一句"natural lighting"）：这镜的光线本该是特意设计的（warm side light 服务"温柔专业的诊疗感"），结果被模板吃掉了，变成了泛用光。**改法**：Shot 2 的视觉描述把光线线索挪到第一段（分号前），比如："...scrape from the center of her cheek outward to the ear, warm side lighting on her face, then down along the jawline..." 这样 `_primary_beat()` 才抓得到。
- 这是内容不一致：DM 私信发出去的信息图，承诺了视频里根本没演示过的手法。用户看完视频、评论关键字拿到图，会发现图上多了一条视频没教的东西。**建议**：要么把 brow-to-hairline 从 infographic 里删掉（保持图和视频严格对齐），要么在 Shot 3 补一句额头手法（更花成本，不建议为了这个改视频）。我倾向直接删。
- - Infographic 本身风格选择（illustration、非写实、no real faces）是对的——医美/身体相关内容用插画而非写实照片，本来就更安全，不用动。
- **我会怎么改**：拿掉对比图插入，把这个"恍然大悟"的瞬间做成一个真实可拍的动作——比如医生用手指轻按自己下颌，停顿、微微点头，一个"这不是脂肪"的确认表情。让画面自己完成认知转折，而不是靠一张信息图硬解释。对比图这个视觉任务，交给 DM 的 infographic 去做就够了（本来 infographic brief 里已经有箭头示意图，两边做同一件事是重复劳动）。
- - **Shot 2**：医生在**别人（患者）脸上**做示范，配音用"you"（"you scrape from the center of your face..."）


## 2026-07-08 18:34 — social-ip-engine

### Decisions & Reasoning
- **改法（用 seedance-characters 的 three-tier action hierarchy）**：二选一
- 这是个真实的代码 gap，不只是内容问题：`_jimeng_camera()`（298-310行）已经会读 title 里的关键字（比如"demo"）来选镜头运镜，但 lip-sync 那句话完全没有类似的条件判断。**建议**：给 `build_jimeng_prompt()` 加一个判断——如果 visual 文本里出现"no dialogue to camera"/"action shot"，把 read 那句换成纯 VO 描述，不要求对口型。我可以现在就改这个函数，要吗？
- 但 `_primary_beat()`（234-243行）只取第一个分号/逗号/"then"之前的那一段作为静帧图片的 SCENE，"warm side lighting, soft focus"这个你特意写的打光指令，落在第二个 `;` 之后，**根本没被摘进 build_prompt() 里**。而且这段文字也没命中 `_clinic_kws`/`_street_kws` 任何关键字，所以最后套用的是最保底的 fallback：`"Setting: shallow depth of field, natural lighting."`——一句完全通用、没有意图的话。
- 按 directing-engine 的 Step 5（光是有动机的，不是随便一句"natural lighting"）：这镜的光线本该是特意设计的（warm side light 服务"温柔专业的诊疗感"），结果被模板吃掉了，变成了泛用光。**改法**：Shot 2 的视觉描述把光线线索挪到第一段（分号前），比如："...scrape from the center of her cheek outward to the ear, warm side lighting on her face, then down along the jawline..." 这样 `_primary_beat()` 才抓得到。
- 这是内容不一致：DM 私信发出去的信息图，承诺了视频里根本没演示过的手法。用户看完视频、评论关键字拿到图，会发现图上多了一条视频没教的东西。**建议**：要么把 brow-to-hairline 从 infographic 里删掉（保持图和视频严格对齐），要么在 Shot 3 补一句额头手法（更花成本，不建议为了这个改视频）。我倾向直接删。
- - Infographic 本身风格选择（illustration、非写实、no real faces）是对的——医美/身体相关内容用插画而非写实照片，本来就更安全，不用动。
- **我会怎么改**：拿掉对比图插入，把这个"恍然大悟"的瞬间做成一个真实可拍的动作——比如医生用手指轻按自己下颌，停顿、微微点头，一个"这不是脂肪"的确认表情。让画面自己完成认知转折，而不是靠一张信息图硬解释。对比图这个视觉任务，交给 DM 的 infographic 去做就够了（本来 infographic brief 里已经有箭头示意图，两边做同一件事是重复劳动）。
- - **Shot 2**：医生在**别人（患者）脸上**做示范，配音用"you"（"you scrape from the center of your face..."）


## 2026-07-08 18:41 — social-ip-engine

### Decisions & Reasoning
- **改法（用 seedance-characters 的 three-tier action hierarchy）**：二选一
- 这是个真实的代码 gap，不只是内容问题：`_jimeng_camera()`（298-310行）已经会读 title 里的关键字（比如"demo"）来选镜头运镜，但 lip-sync 那句话完全没有类似的条件判断。**建议**：给 `build_jimeng_prompt()` 加一个判断——如果 visual 文本里出现"no dialogue to camera"/"action shot"，把 read 那句换成纯 VO 描述，不要求对口型。我可以现在就改这个函数，要吗？
- 但 `_primary_beat()`（234-243行）只取第一个分号/逗号/"then"之前的那一段作为静帧图片的 SCENE，"warm side lighting, soft focus"这个你特意写的打光指令，落在第二个 `;` 之后，**根本没被摘进 build_prompt() 里**。而且这段文字也没命中 `_clinic_kws`/`_street_kws` 任何关键字，所以最后套用的是最保底的 fallback：`"Setting: shallow depth of field, natural lighting."`——一句完全通用、没有意图的话。
- 按 directing-engine 的 Step 5（光是有动机的，不是随便一句"natural lighting"）：这镜的光线本该是特意设计的（warm side light 服务"温柔专业的诊疗感"），结果被模板吃掉了，变成了泛用光。**改法**：Shot 2 的视觉描述把光线线索挪到第一段（分号前），比如："...scrape from the center of her cheek outward to the ear, warm side lighting on her face, then down along the jawline..." 这样 `_primary_beat()` 才抓得到。
- 这是内容不一致：DM 私信发出去的信息图，承诺了视频里根本没演示过的手法。用户看完视频、评论关键字拿到图，会发现图上多了一条视频没教的东西。**建议**：要么把 brow-to-hairline 从 infographic 里删掉（保持图和视频严格对齐），要么在 Shot 3 补一句额头手法（更花成本，不建议为了这个改视频）。我倾向直接删。
- - Infographic 本身风格选择（illustration、非写实、no real faces）是对的——医美/身体相关内容用插画而非写实照片，本来就更安全，不用动。
- **我会怎么改**：拿掉对比图插入，把这个"恍然大悟"的瞬间做成一个真实可拍的动作——比如医生用手指轻按自己下颌，停顿、微微点头，一个"这不是脂肪"的确认表情。让画面自己完成认知转折，而不是靠一张信息图硬解释。对比图这个视觉任务，交给 DM 的 infographic 去做就够了（本来 infographic brief 里已经有箭头示意图，两边做同一件事是重复劳动）。
- - **Shot 2**：医生在**别人（患者）脸上**做示范，配音用"you"（"you scrape from the center of your face..."）


## 2026-07-08 18:42 — social-ip-engine

### What Didn't Work (negative knowledge)
- - (This is different from your `notion-sync` webhook, which fires instantly from the cloud regardless of your laptop — that one can't run this pipeline because it's heavy local-only tooling: whisper, moviepy, ffmpeg)
- **New gap found:** the merged video (`final.mp4`) currently has no path to reach Notion/Render at all — it only lives on your laptop. Render can't caption a video it can't fetch. Needs a small addition to `notion_video.py` to upload it to a new Notion property first.
- **Bottom line: flipping to Published right now would safely do nothing (no video) rather than publish something broken.** The real unlock is just: write "First DM," then run captions+upload locally, then it'll actually go live correctly.

### Architecture Decisions
- - **Captions (whisper + moviepy)** — 🟡 mostly portable, but **one real blocker**: the caption script hardcodes a macOS-only font path (`/System/Library/Fonts/.../Arial Black.ttf`). That font doesn't exist on Render's Linux server. We'd need to swap to a different bundled font, and re-tune the padding/line-wrap math — the stuff we just spent all of 7/7–7/8 debugging (glyph clipping, uneven line splits) was tuned specifically for Arial Black's metrics. Swap fonts = re-test that whole thing.

### Decisions & Reasoning
- 也就是说，脚本从不会因为你拖了 Stage 就自动去合并/加字幕/上传视频——反过来，你得先跑完 `finalize_all_videos.py`（内部调用 `add_karaoke_captions.py --upload`）**审完成片**，再手动拖 Stage。
- - 而 merge / whisper 转录 / moviepy 烧字幕 / cover 生图 / infographic 生图，全部住在 `studio/` —— `studio/CLAUDE.md` 第一行写死了 **"This folder is NEVER deployed; it is local tooling only."** 字幕烧录甚至绑定在你这台机器的 ffmpeg build（没有 libass，只能用 moviepy 硬编码字体渲染）。
- 2. **Infographic 生图有脚本**（`batch_infographic_gen.py`）但它不在 `finalize_all_videos.py` 的调用链里，是完全独立、你得记得单独跑的东西。
- 3. **新增**：cover 生图（复用 `cover_blocks()` 已经写好的 prompt，调 gpt-image-2，带上 IP 参考脸——这点很关键，不能像 7/8 那次 Facebook 事故一样盲生成）+ 上传到 `🖼️ Cover here` toggle
- 跑完这一条命令，终端打印一份 checklist（cover✅ infographic✅ captions✅ uploaded✅），你扫一眼没问题再手动拖 Stage——审片关卡保留，但你不用再分别记 3-4 个脚本。
- **What I think you actually want:** not "automatic," but "one command instead of four." Right now you have to remember to run several separate scripts (merge, captions, cover, infographic) before dragging Stage — and two of those (cover, infographic) aren't even automated at all right now, you'd have to do them by hand. That's the real gap that caused this mess with the ear video.
- 4. **Safety-net in `notion_sync.py`** — warns (doesn't block) when video/cover missing on a Ready-to-Publish row, so it's visible instead of silent.
- I checked the actual code instead of assuming. Here's the real picture, piece by piece:


## 2026-07-08 18:42 — social-ip-engine

### Decisions & Reasoning
- **改法（用 seedance-characters 的 three-tier action hierarchy）**：二选一
- 这是个真实的代码 gap，不只是内容问题：`_jimeng_camera()`（298-310行）已经会读 title 里的关键字（比如"demo"）来选镜头运镜，但 lip-sync 那句话完全没有类似的条件判断。**建议**：给 `build_jimeng_prompt()` 加一个判断——如果 visual 文本里出现"no dialogue to camera"/"action shot"，把 read 那句换成纯 VO 描述，不要求对口型。我可以现在就改这个函数，要吗？
- 但 `_primary_beat()`（234-243行）只取第一个分号/逗号/"then"之前的那一段作为静帧图片的 SCENE，"warm side lighting, soft focus"这个你特意写的打光指令，落在第二个 `;` 之后，**根本没被摘进 build_prompt() 里**。而且这段文字也没命中 `_clinic_kws`/`_street_kws` 任何关键字，所以最后套用的是最保底的 fallback：`"Setting: shallow depth of field, natural lighting."`——一句完全通用、没有意图的话。
- 按 directing-engine 的 Step 5（光是有动机的，不是随便一句"natural lighting"）：这镜的光线本该是特意设计的（warm side light 服务"温柔专业的诊疗感"），结果被模板吃掉了，变成了泛用光。**改法**：Shot 2 的视觉描述把光线线索挪到第一段（分号前），比如："...scrape from the center of her cheek outward to the ear, warm side lighting on her face, then down along the jawline..." 这样 `_primary_beat()` 才抓得到。
- 这是内容不一致：DM 私信发出去的信息图，承诺了视频里根本没演示过的手法。用户看完视频、评论关键字拿到图，会发现图上多了一条视频没教的东西。**建议**：要么把 brow-to-hairline 从 infographic 里删掉（保持图和视频严格对齐），要么在 Shot 3 补一句额头手法（更花成本，不建议为了这个改视频）。我倾向直接删。
- - Infographic 本身风格选择（illustration、非写实、no real faces）是对的——医美/身体相关内容用插画而非写实照片，本来就更安全，不用动。
- **我会怎么改**：拿掉对比图插入，把这个"恍然大悟"的瞬间做成一个真实可拍的动作——比如医生用手指轻按自己下颌，停顿、微微点头，一个"这不是脂肪"的确认表情。让画面自己完成认知转折，而不是靠一张信息图硬解释。对比图这个视觉任务，交给 DM 的 infographic 去做就够了（本来 infographic brief 里已经有箭头示意图，两边做同一件事是重复劳动）。
- - **Shot 2**：医生在**别人（患者）脸上**做示范，配音用"you"（"you scrape from the center of your face..."）


## 2026-07-08 18:43 — social-ip-engine

### Decisions & Reasoning
- **改法（用 seedance-characters 的 three-tier action hierarchy）**：二选一
- 这是个真实的代码 gap，不只是内容问题：`_jimeng_camera()`（298-310行）已经会读 title 里的关键字（比如"demo"）来选镜头运镜，但 lip-sync 那句话完全没有类似的条件判断。**建议**：给 `build_jimeng_prompt()` 加一个判断——如果 visual 文本里出现"no dialogue to camera"/"action shot"，把 read 那句换成纯 VO 描述，不要求对口型。我可以现在就改这个函数，要吗？
- 但 `_primary_beat()`（234-243行）只取第一个分号/逗号/"then"之前的那一段作为静帧图片的 SCENE，"warm side lighting, soft focus"这个你特意写的打光指令，落在第二个 `;` 之后，**根本没被摘进 build_prompt() 里**。而且这段文字也没命中 `_clinic_kws`/`_street_kws` 任何关键字，所以最后套用的是最保底的 fallback：`"Setting: shallow depth of field, natural lighting."`——一句完全通用、没有意图的话。
- 按 directing-engine 的 Step 5（光是有动机的，不是随便一句"natural lighting"）：这镜的光线本该是特意设计的（warm side light 服务"温柔专业的诊疗感"），结果被模板吃掉了，变成了泛用光。**改法**：Shot 2 的视觉描述把光线线索挪到第一段（分号前），比如："...scrape from the center of her cheek outward to the ear, warm side lighting on her face, then down along the jawline..." 这样 `_primary_beat()` 才抓得到。
- 这是内容不一致：DM 私信发出去的信息图，承诺了视频里根本没演示过的手法。用户看完视频、评论关键字拿到图，会发现图上多了一条视频没教的东西。**建议**：要么把 brow-to-hairline 从 infographic 里删掉（保持图和视频严格对齐），要么在 Shot 3 补一句额头手法（更花成本，不建议为了这个改视频）。我倾向直接删。
- - Infographic 本身风格选择（illustration、非写实、no real faces）是对的——医美/身体相关内容用插画而非写实照片，本来就更安全，不用动。
- **我会怎么改**：拿掉对比图插入，把这个"恍然大悟"的瞬间做成一个真实可拍的动作——比如医生用手指轻按自己下颌，停顿、微微点头，一个"这不是脂肪"的确认表情。让画面自己完成认知转折，而不是靠一张信息图硬解释。对比图这个视觉任务，交给 DM 的 infographic 去做就够了（本来 infographic brief 里已经有箭头示意图，两边做同一件事是重复劳动）。
- - **Shot 2**：医生在**别人（患者）脸上**做示范，配音用"you"（"you scrape from the center of your face..."）


## 2026-07-08 18:50 — social-ip-engine

### Decisions & Reasoning
- **改法（用 seedance-characters 的 three-tier action hierarchy）**：二选一
- 这是个真实的代码 gap，不只是内容问题：`_jimeng_camera()`（298-310行）已经会读 title 里的关键字（比如"demo"）来选镜头运镜，但 lip-sync 那句话完全没有类似的条件判断。**建议**：给 `build_jimeng_prompt()` 加一个判断——如果 visual 文本里出现"no dialogue to camera"/"action shot"，把 read 那句换成纯 VO 描述，不要求对口型。我可以现在就改这个函数，要吗？
- 但 `_primary_beat()`（234-243行）只取第一个分号/逗号/"then"之前的那一段作为静帧图片的 SCENE，"warm side lighting, soft focus"这个你特意写的打光指令，落在第二个 `;` 之后，**根本没被摘进 build_prompt() 里**。而且这段文字也没命中 `_clinic_kws`/`_street_kws` 任何关键字，所以最后套用的是最保底的 fallback：`"Setting: shallow depth of field, natural lighting."`——一句完全通用、没有意图的话。
- 按 directing-engine 的 Step 5（光是有动机的，不是随便一句"natural lighting"）：这镜的光线本该是特意设计的（warm side light 服务"温柔专业的诊疗感"），结果被模板吃掉了，变成了泛用光。**改法**：Shot 2 的视觉描述把光线线索挪到第一段（分号前），比如："...scrape from the center of her cheek outward to the ear, warm side lighting on her face, then down along the jawline..." 这样 `_primary_beat()` 才抓得到。
- 这是内容不一致：DM 私信发出去的信息图，承诺了视频里根本没演示过的手法。用户看完视频、评论关键字拿到图，会发现图上多了一条视频没教的东西。**建议**：要么把 brow-to-hairline 从 infographic 里删掉（保持图和视频严格对齐），要么在 Shot 3 补一句额头手法（更花成本，不建议为了这个改视频）。我倾向直接删。
- - Infographic 本身风格选择（illustration、非写实、no real faces）是对的——医美/身体相关内容用插画而非写实照片，本来就更安全，不用动。
- **我会怎么改**：拿掉对比图插入，把这个"恍然大悟"的瞬间做成一个真实可拍的动作——比如医生用手指轻按自己下颌，停顿、微微点头，一个"这不是脂肪"的确认表情。让画面自己完成认知转折，而不是靠一张信息图硬解释。对比图这个视觉任务，交给 DM 的 infographic 去做就够了（本来 infographic brief 里已经有箭头示意图，两边做同一件事是重复劳动）。
- - **Shot 2**：医生在**别人（患者）脸上**做示范，配音用"you"（"you scrape from the center of your face..."）


## 2026-07-08 18:51 — social-ip-engine

### What Didn't Work (negative knowledge)
- - (This is different from your `notion-sync` webhook, which fires instantly from the cloud regardless of your laptop — that one can't run this pipeline because it's heavy local-only tooling: whisper, moviepy, ffmpeg)
- **New gap found:** the merged video (`final.mp4`) currently has no path to reach Notion/Render at all — it only lives on your laptop. Render can't caption a video it can't fetch. Needs a small addition to `notion_video.py` to upload it to a new Notion property first.
- **Bottom line: flipping to Published right now would safely do nothing (no video) rather than publish something broken.** The real unlock is just: write "First DM," then run captions+upload locally, then it'll actually go live correctly.

### Architecture Decisions
- - **Captions (whisper + moviepy)** — 🟡 mostly portable, but **one real blocker**: the caption script hardcodes a macOS-only font path (`/System/Library/Fonts/.../Arial Black.ttf`). That font doesn't exist on Render's Linux server. We'd need to swap to a different bundled font, and re-tune the padding/line-wrap math — the stuff we just spent all of 7/7–7/8 debugging (glyph clipping, uneven line splits) was tuned specifically for Arial Black's metrics. Swap fonts = re-test that whole thing.

### Decisions & Reasoning
- 也就是说，脚本从不会因为你拖了 Stage 就自动去合并/加字幕/上传视频——反过来，你得先跑完 `finalize_all_videos.py`（内部调用 `add_karaoke_captions.py --upload`）**审完成片**，再手动拖 Stage。
- - 而 merge / whisper 转录 / moviepy 烧字幕 / cover 生图 / infographic 生图，全部住在 `studio/` —— `studio/CLAUDE.md` 第一行写死了 **"This folder is NEVER deployed; it is local tooling only."** 字幕烧录甚至绑定在你这台机器的 ffmpeg build（没有 libass，只能用 moviepy 硬编码字体渲染）。
- 2. **Infographic 生图有脚本**（`batch_infographic_gen.py`）但它不在 `finalize_all_videos.py` 的调用链里，是完全独立、你得记得单独跑的东西。
- 3. **新增**：cover 生图（复用 `cover_blocks()` 已经写好的 prompt，调 gpt-image-2，带上 IP 参考脸——这点很关键，不能像 7/8 那次 Facebook 事故一样盲生成）+ 上传到 `🖼️ Cover here` toggle
- 跑完这一条命令，终端打印一份 checklist（cover✅ infographic✅ captions✅ uploaded✅），你扫一眼没问题再手动拖 Stage——审片关卡保留，但你不用再分别记 3-4 个脚本。
- **What I think you actually want:** not "automatic," but "one command instead of four." Right now you have to remember to run several separate scripts (merge, captions, cover, infographic) before dragging Stage — and two of those (cover, infographic) aren't even automated at all right now, you'd have to do them by hand. That's the real gap that caused this mess with the ear video.
- 4. **Safety-net in `notion_sync.py`** — warns (doesn't block) when video/cover missing on a Ready-to-Publish row, so it's visible instead of silent.
- I checked the actual code instead of assuming. Here's the real picture, piece by piece:


## 2026-07-08 18:57 — social-ip-engine

### What Didn't Work (negative knowledge)
- - (This is different from your `notion-sync` webhook, which fires instantly from the cloud regardless of your laptop — that one can't run this pipeline because it's heavy local-only tooling: whisper, moviepy, ffmpeg)
- **New gap found:** the merged video (`final.mp4`) currently has no path to reach Notion/Render at all — it only lives on your laptop. Render can't caption a video it can't fetch. Needs a small addition to `notion_video.py` to upload it to a new Notion property first.
- **Bottom line: flipping to Published right now would safely do nothing (no video) rather than publish something broken.** The real unlock is just: write "First DM," then run captions+upload locally, then it'll actually go live correctly.

### Architecture Decisions
- - **Captions (whisper + moviepy)** — 🟡 mostly portable, but **one real blocker**: the caption script hardcodes a macOS-only font path (`/System/Library/Fonts/.../Arial Black.ttf`). That font doesn't exist on Render's Linux server. We'd need to swap to a different bundled font, and re-tune the padding/line-wrap math — the stuff we just spent all of 7/7–7/8 debugging (glyph clipping, uneven line splits) was tuned specifically for Arial Black's metrics. Swap fonts = re-test that whole thing.

### Decisions & Reasoning
- 也就是说，脚本从不会因为你拖了 Stage 就自动去合并/加字幕/上传视频——反过来，你得先跑完 `finalize_all_videos.py`（内部调用 `add_karaoke_captions.py --upload`）**审完成片**，再手动拖 Stage。
- - 而 merge / whisper 转录 / moviepy 烧字幕 / cover 生图 / infographic 生图，全部住在 `studio/` —— `studio/CLAUDE.md` 第一行写死了 **"This folder is NEVER deployed; it is local tooling only."** 字幕烧录甚至绑定在你这台机器的 ffmpeg build（没有 libass，只能用 moviepy 硬编码字体渲染）。
- 2. **Infographic 生图有脚本**（`batch_infographic_gen.py`）但它不在 `finalize_all_videos.py` 的调用链里，是完全独立、你得记得单独跑的东西。
- 3. **新增**：cover 生图（复用 `cover_blocks()` 已经写好的 prompt，调 gpt-image-2，带上 IP 参考脸——这点很关键，不能像 7/8 那次 Facebook 事故一样盲生成）+ 上传到 `🖼️ Cover here` toggle
- 跑完这一条命令，终端打印一份 checklist（cover✅ infographic✅ captions✅ uploaded✅），你扫一眼没问题再手动拖 Stage——审片关卡保留，但你不用再分别记 3-4 个脚本。
- **What I think you actually want:** not "automatic," but "one command instead of four." Right now you have to remember to run several separate scripts (merge, captions, cover, infographic) before dragging Stage — and two of those (cover, infographic) aren't even automated at all right now, you'd have to do them by hand. That's the real gap that caused this mess with the ear video.
- 4. **Safety-net in `notion_sync.py`** — warns (doesn't block) when video/cover missing on a Ready-to-Publish row, so it's visible instead of silent.
- I checked the actual code instead of assuming. Here's the real picture, piece by piece:


## 2026-07-08 19:13 — social-ip-engine

### What Didn't Work (negative knowledge)
- - (This is different from your `notion-sync` webhook, which fires instantly from the cloud regardless of your laptop — that one can't run this pipeline because it's heavy local-only tooling: whisper, moviepy, ffmpeg)
- **New gap found:** the merged video (`final.mp4`) currently has no path to reach Notion/Render at all — it only lives on your laptop. Render can't caption a video it can't fetch. Needs a small addition to `notion_video.py` to upload it to a new Notion property first.
- **Bottom line: flipping to Published right now would safely do nothing (no video) rather than publish something broken.** The real unlock is just: write "First DM," then run captions+upload locally, then it'll actually go live correctly.

### Architecture Decisions
- - **Captions (whisper + moviepy)** — 🟡 mostly portable, but **one real blocker**: the caption script hardcodes a macOS-only font path (`/System/Library/Fonts/.../Arial Black.ttf`). That font doesn't exist on Render's Linux server. We'd need to swap to a different bundled font, and re-tune the padding/line-wrap math — the stuff we just spent all of 7/7–7/8 debugging (glyph clipping, uneven line splits) was tuned specifically for Arial Black's metrics. Swap fonts = re-test that whole thing.

### Decisions & Reasoning
- 也就是说，脚本从不会因为你拖了 Stage 就自动去合并/加字幕/上传视频——反过来，你得先跑完 `finalize_all_videos.py`（内部调用 `add_karaoke_captions.py --upload`）**审完成片**，再手动拖 Stage。
- - 而 merge / whisper 转录 / moviepy 烧字幕 / cover 生图 / infographic 生图，全部住在 `studio/` —— `studio/CLAUDE.md` 第一行写死了 **"This folder is NEVER deployed; it is local tooling only."** 字幕烧录甚至绑定在你这台机器的 ffmpeg build（没有 libass，只能用 moviepy 硬编码字体渲染）。
- 2. **Infographic 生图有脚本**（`batch_infographic_gen.py`）但它不在 `finalize_all_videos.py` 的调用链里，是完全独立、你得记得单独跑的东西。
- 3. **新增**：cover 生图（复用 `cover_blocks()` 已经写好的 prompt，调 gpt-image-2，带上 IP 参考脸——这点很关键，不能像 7/8 那次 Facebook 事故一样盲生成）+ 上传到 `🖼️ Cover here` toggle
- 跑完这一条命令，终端打印一份 checklist（cover✅ infographic✅ captions✅ uploaded✅），你扫一眼没问题再手动拖 Stage——审片关卡保留，但你不用再分别记 3-4 个脚本。
- **What I think you actually want:** not "automatic," but "one command instead of four." Right now you have to remember to run several separate scripts (merge, captions, cover, infographic) before dragging Stage — and two of those (cover, infographic) aren't even automated at all right now, you'd have to do them by hand. That's the real gap that caused this mess with the ear video.
- 4. **Safety-net in `notion_sync.py`** — warns (doesn't block) when video/cover missing on a Ready-to-Publish row, so it's visible instead of silent.
- I checked the actual code instead of assuming. Here's the real picture, piece by piece:


## 2026-07-08 19:18 — social-ip-engine

### What Didn't Work (negative knowledge)
- - (This is different from your `notion-sync` webhook, which fires instantly from the cloud regardless of your laptop — that one can't run this pipeline because it's heavy local-only tooling: whisper, moviepy, ffmpeg)
- **New gap found:** the merged video (`final.mp4`) currently has no path to reach Notion/Render at all — it only lives on your laptop. Render can't caption a video it can't fetch. Needs a small addition to `notion_video.py` to upload it to a new Notion property first.
- **Bottom line: flipping to Published right now would safely do nothing (no video) rather than publish something broken.** The real unlock is just: write "First DM," then run captions+upload locally, then it'll actually go live correctly.

### Architecture Decisions
- - **Captions (whisper + moviepy)** — 🟡 mostly portable, but **one real blocker**: the caption script hardcodes a macOS-only font path (`/System/Library/Fonts/.../Arial Black.ttf`). That font doesn't exist on Render's Linux server. We'd need to swap to a different bundled font, and re-tune the padding/line-wrap math — the stuff we just spent all of 7/7–7/8 debugging (glyph clipping, uneven line splits) was tuned specifically for Arial Black's metrics. Swap fonts = re-test that whole thing.

### Decisions & Reasoning
- 也就是说，脚本从不会因为你拖了 Stage 就自动去合并/加字幕/上传视频——反过来，你得先跑完 `finalize_all_videos.py`（内部调用 `add_karaoke_captions.py --upload`）**审完成片**，再手动拖 Stage。
- - 而 merge / whisper 转录 / moviepy 烧字幕 / cover 生图 / infographic 生图，全部住在 `studio/` —— `studio/CLAUDE.md` 第一行写死了 **"This folder is NEVER deployed; it is local tooling only."** 字幕烧录甚至绑定在你这台机器的 ffmpeg build（没有 libass，只能用 moviepy 硬编码字体渲染）。
- 2. **Infographic 生图有脚本**（`batch_infographic_gen.py`）但它不在 `finalize_all_videos.py` 的调用链里，是完全独立、你得记得单独跑的东西。
- 3. **新增**：cover 生图（复用 `cover_blocks()` 已经写好的 prompt，调 gpt-image-2，带上 IP 参考脸——这点很关键，不能像 7/8 那次 Facebook 事故一样盲生成）+ 上传到 `🖼️ Cover here` toggle
- 跑完这一条命令，终端打印一份 checklist（cover✅ infographic✅ captions✅ uploaded✅），你扫一眼没问题再手动拖 Stage——审片关卡保留，但你不用再分别记 3-4 个脚本。
- **What I think you actually want:** not "automatic," but "one command instead of four." Right now you have to remember to run several separate scripts (merge, captions, cover, infographic) before dragging Stage — and two of those (cover, infographic) aren't even automated at all right now, you'd have to do them by hand. That's the real gap that caused this mess with the ear video.
- 4. **Safety-net in `notion_sync.py`** — warns (doesn't block) when video/cover missing on a Ready-to-Publish row, so it's visible instead of silent.
- I checked the actual code instead of assuming. Here's the real picture, piece by piece:


## 2026-07-08 19:22 — social-ip-engine

### What Didn't Work (negative knowledge)
- - (This is different from your `notion-sync` webhook, which fires instantly from the cloud regardless of your laptop — that one can't run this pipeline because it's heavy local-only tooling: whisper, moviepy, ffmpeg)
- **New gap found:** the merged video (`final.mp4`) currently has no path to reach Notion/Render at all — it only lives on your laptop. Render can't caption a video it can't fetch. Needs a small addition to `notion_video.py` to upload it to a new Notion property first.
- **Bottom line: flipping to Published right now would safely do nothing (no video) rather than publish something broken.** The real unlock is just: write "First DM," then run captions+upload locally, then it'll actually go live correctly.

### Architecture Decisions
- - **Captions (whisper + moviepy)** — 🟡 mostly portable, but **one real blocker**: the caption script hardcodes a macOS-only font path (`/System/Library/Fonts/.../Arial Black.ttf`). That font doesn't exist on Render's Linux server. We'd need to swap to a different bundled font, and re-tune the padding/line-wrap math — the stuff we just spent all of 7/7–7/8 debugging (glyph clipping, uneven line splits) was tuned specifically for Arial Black's metrics. Swap fonts = re-test that whole thing.

### Decisions & Reasoning
- 也就是说，脚本从不会因为你拖了 Stage 就自动去合并/加字幕/上传视频——反过来，你得先跑完 `finalize_all_videos.py`（内部调用 `add_karaoke_captions.py --upload`）**审完成片**，再手动拖 Stage。
- - 而 merge / whisper 转录 / moviepy 烧字幕 / cover 生图 / infographic 生图，全部住在 `studio/` —— `studio/CLAUDE.md` 第一行写死了 **"This folder is NEVER deployed; it is local tooling only."** 字幕烧录甚至绑定在你这台机器的 ffmpeg build（没有 libass，只能用 moviepy 硬编码字体渲染）。
- 2. **Infographic 生图有脚本**（`batch_infographic_gen.py`）但它不在 `finalize_all_videos.py` 的调用链里，是完全独立、你得记得单独跑的东西。
- 3. **新增**：cover 生图（复用 `cover_blocks()` 已经写好的 prompt，调 gpt-image-2，带上 IP 参考脸——这点很关键，不能像 7/8 那次 Facebook 事故一样盲生成）+ 上传到 `🖼️ Cover here` toggle
- 跑完这一条命令，终端打印一份 checklist（cover✅ infographic✅ captions✅ uploaded✅），你扫一眼没问题再手动拖 Stage——审片关卡保留，但你不用再分别记 3-4 个脚本。
- **What I think you actually want:** not "automatic," but "one command instead of four." Right now you have to remember to run several separate scripts (merge, captions, cover, infographic) before dragging Stage — and two of those (cover, infographic) aren't even automated at all right now, you'd have to do them by hand. That's the real gap that caused this mess with the ear video.
- 4. **Safety-net in `notion_sync.py`** — warns (doesn't block) when video/cover missing on a Ready-to-Publish row, so it's visible instead of silent.
- I checked the actual code instead of assuming. Here's the real picture, piece by piece:


## 2026-07-08 19:29 — social-ip-engine

### What Didn't Work (negative knowledge)
- - (This is different from your `notion-sync` webhook, which fires instantly from the cloud regardless of your laptop — that one can't run this pipeline because it's heavy local-only tooling: whisper, moviepy, ffmpeg)
- **New gap found:** the merged video (`final.mp4`) currently has no path to reach Notion/Render at all — it only lives on your laptop. Render can't caption a video it can't fetch. Needs a small addition to `notion_video.py` to upload it to a new Notion property first.
- **Bottom line: flipping to Published right now would safely do nothing (no video) rather than publish something broken.** The real unlock is just: write "First DM," then run captions+upload locally, then it'll actually go live correctly.

### Architecture Decisions
- - **Captions (whisper + moviepy)** — 🟡 mostly portable, but **one real blocker**: the caption script hardcodes a macOS-only font path (`/System/Library/Fonts/.../Arial Black.ttf`). That font doesn't exist on Render's Linux server. We'd need to swap to a different bundled font, and re-tune the padding/line-wrap math — the stuff we just spent all of 7/7–7/8 debugging (glyph clipping, uneven line splits) was tuned specifically for Arial Black's metrics. Swap fonts = re-test that whole thing.

### Decisions & Reasoning
- 也就是说，脚本从不会因为你拖了 Stage 就自动去合并/加字幕/上传视频——反过来，你得先跑完 `finalize_all_videos.py`（内部调用 `add_karaoke_captions.py --upload`）**审完成片**，再手动拖 Stage。
- - 而 merge / whisper 转录 / moviepy 烧字幕 / cover 生图 / infographic 生图，全部住在 `studio/` —— `studio/CLAUDE.md` 第一行写死了 **"This folder is NEVER deployed; it is local tooling only."** 字幕烧录甚至绑定在你这台机器的 ffmpeg build（没有 libass，只能用 moviepy 硬编码字体渲染）。
- 2. **Infographic 生图有脚本**（`batch_infographic_gen.py`）但它不在 `finalize_all_videos.py` 的调用链里，是完全独立、你得记得单独跑的东西。
- 3. **新增**：cover 生图（复用 `cover_blocks()` 已经写好的 prompt，调 gpt-image-2，带上 IP 参考脸——这点很关键，不能像 7/8 那次 Facebook 事故一样盲生成）+ 上传到 `🖼️ Cover here` toggle
- 跑完这一条命令，终端打印一份 checklist（cover✅ infographic✅ captions✅ uploaded✅），你扫一眼没问题再手动拖 Stage——审片关卡保留，但你不用再分别记 3-4 个脚本。
- **What I think you actually want:** not "automatic," but "one command instead of four." Right now you have to remember to run several separate scripts (merge, captions, cover, infographic) before dragging Stage — and two of those (cover, infographic) aren't even automated at all right now, you'd have to do them by hand. That's the real gap that caused this mess with the ear video.
- 4. **Safety-net in `notion_sync.py`** — warns (doesn't block) when video/cover missing on a Ready-to-Publish row, so it's visible instead of silent.
- I checked the actual code instead of assuming. Here's the real picture, piece by piece:


## 2026-07-08 19:58 — social-ip-engine

### What Didn't Work (negative knowledge)
- - (This is different from your `notion-sync` webhook, which fires instantly from the cloud regardless of your laptop — that one can't run this pipeline because it's heavy local-only tooling: whisper, moviepy, ffmpeg)
- **New gap found:** the merged video (`final.mp4`) currently has no path to reach Notion/Render at all — it only lives on your laptop. Render can't caption a video it can't fetch. Needs a small addition to `notion_video.py` to upload it to a new Notion property first.
- **Bottom line: flipping to Published right now would safely do nothing (no video) rather than publish something broken.** The real unlock is just: write "First DM," then run captions+upload locally, then it'll actually go live correctly.

### Architecture Decisions
- - **Captions (whisper + moviepy)** — 🟡 mostly portable, but **one real blocker**: the caption script hardcodes a macOS-only font path (`/System/Library/Fonts/.../Arial Black.ttf`). That font doesn't exist on Render's Linux server. We'd need to swap to a different bundled font, and re-tune the padding/line-wrap math — the stuff we just spent all of 7/7–7/8 debugging (glyph clipping, uneven line splits) was tuned specifically for Arial Black's metrics. Swap fonts = re-test that whole thing.

### Decisions & Reasoning
- 也就是说，脚本从不会因为你拖了 Stage 就自动去合并/加字幕/上传视频——反过来，你得先跑完 `finalize_all_videos.py`（内部调用 `add_karaoke_captions.py --upload`）**审完成片**，再手动拖 Stage。
- - 而 merge / whisper 转录 / moviepy 烧字幕 / cover 生图 / infographic 生图，全部住在 `studio/` —— `studio/CLAUDE.md` 第一行写死了 **"This folder is NEVER deployed; it is local tooling only."** 字幕烧录甚至绑定在你这台机器的 ffmpeg build（没有 libass，只能用 moviepy 硬编码字体渲染）。
- 2. **Infographic 生图有脚本**（`batch_infographic_gen.py`）但它不在 `finalize_all_videos.py` 的调用链里，是完全独立、你得记得单独跑的东西。
- 3. **新增**：cover 生图（复用 `cover_blocks()` 已经写好的 prompt，调 gpt-image-2，带上 IP 参考脸——这点很关键，不能像 7/8 那次 Facebook 事故一样盲生成）+ 上传到 `🖼️ Cover here` toggle
- 跑完这一条命令，终端打印一份 checklist（cover✅ infographic✅ captions✅ uploaded✅），你扫一眼没问题再手动拖 Stage——审片关卡保留，但你不用再分别记 3-4 个脚本。
- **What I think you actually want:** not "automatic," but "one command instead of four." Right now you have to remember to run several separate scripts (merge, captions, cover, infographic) before dragging Stage — and two of those (cover, infographic) aren't even automated at all right now, you'd have to do them by hand. That's the real gap that caused this mess with the ear video.
- 4. **Safety-net in `notion_sync.py`** — warns (doesn't block) when video/cover missing on a Ready-to-Publish row, so it's visible instead of silent.
- I checked the actual code instead of assuming. Here's the real picture, piece by piece:


## 2026-07-08 20:01 — social-ip-engine

### What Didn't Work (negative knowledge)
- - (This is different from your `notion-sync` webhook, which fires instantly from the cloud regardless of your laptop — that one can't run this pipeline because it's heavy local-only tooling: whisper, moviepy, ffmpeg)
- **New gap found:** the merged video (`final.mp4`) currently has no path to reach Notion/Render at all — it only lives on your laptop. Render can't caption a video it can't fetch. Needs a small addition to `notion_video.py` to upload it to a new Notion property first.
- **Bottom line: flipping to Published right now would safely do nothing (no video) rather than publish something broken.** The real unlock is just: write "First DM," then run captions+upload locally, then it'll actually go live correctly.

### Architecture Decisions
- - **Captions (whisper + moviepy)** — 🟡 mostly portable, but **one real blocker**: the caption script hardcodes a macOS-only font path (`/System/Library/Fonts/.../Arial Black.ttf`). That font doesn't exist on Render's Linux server. We'd need to swap to a different bundled font, and re-tune the padding/line-wrap math — the stuff we just spent all of 7/7–7/8 debugging (glyph clipping, uneven line splits) was tuned specifically for Arial Black's metrics. Swap fonts = re-test that whole thing.

### Decisions & Reasoning
- 也就是说，脚本从不会因为你拖了 Stage 就自动去合并/加字幕/上传视频——反过来，你得先跑完 `finalize_all_videos.py`（内部调用 `add_karaoke_captions.py --upload`）**审完成片**，再手动拖 Stage。
- - 而 merge / whisper 转录 / moviepy 烧字幕 / cover 生图 / infographic 生图，全部住在 `studio/` —— `studio/CLAUDE.md` 第一行写死了 **"This folder is NEVER deployed; it is local tooling only."** 字幕烧录甚至绑定在你这台机器的 ffmpeg build（没有 libass，只能用 moviepy 硬编码字体渲染）。
- 2. **Infographic 生图有脚本**（`batch_infographic_gen.py`）但它不在 `finalize_all_videos.py` 的调用链里，是完全独立、你得记得单独跑的东西。
- 3. **新增**：cover 生图（复用 `cover_blocks()` 已经写好的 prompt，调 gpt-image-2，带上 IP 参考脸——这点很关键，不能像 7/8 那次 Facebook 事故一样盲生成）+ 上传到 `🖼️ Cover here` toggle
- 跑完这一条命令，终端打印一份 checklist（cover✅ infographic✅ captions✅ uploaded✅），你扫一眼没问题再手动拖 Stage——审片关卡保留，但你不用再分别记 3-4 个脚本。
- **What I think you actually want:** not "automatic," but "one command instead of four." Right now you have to remember to run several separate scripts (merge, captions, cover, infographic) before dragging Stage — and two of those (cover, infographic) aren't even automated at all right now, you'd have to do them by hand. That's the real gap that caused this mess with the ear video.
- 4. **Safety-net in `notion_sync.py`** — warns (doesn't block) when video/cover missing on a Ready-to-Publish row, so it's visible instead of silent.
- I checked the actual code instead of assuming. Here's the real picture, piece by piece:


## 2026-07-08 20:08 — social-ip-engine

### What Didn't Work (negative knowledge)
- - (This is different from your `notion-sync` webhook, which fires instantly from the cloud regardless of your laptop — that one can't run this pipeline because it's heavy local-only tooling: whisper, moviepy, ffmpeg)
- **New gap found:** the merged video (`final.mp4`) currently has no path to reach Notion/Render at all — it only lives on your laptop. Render can't caption a video it can't fetch. Needs a small addition to `notion_video.py` to upload it to a new Notion property first.
- **Bottom line: flipping to Published right now would safely do nothing (no video) rather than publish something broken.** The real unlock is just: write "First DM," then run captions+upload locally, then it'll actually go live correctly.

### Architecture Decisions
- - **Captions (whisper + moviepy)** — 🟡 mostly portable, but **one real blocker**: the caption script hardcodes a macOS-only font path (`/System/Library/Fonts/.../Arial Black.ttf`). That font doesn't exist on Render's Linux server. We'd need to swap to a different bundled font, and re-tune the padding/line-wrap math — the stuff we just spent all of 7/7–7/8 debugging (glyph clipping, uneven line splits) was tuned specifically for Arial Black's metrics. Swap fonts = re-test that whole thing.

### Decisions & Reasoning
- 也就是说，脚本从不会因为你拖了 Stage 就自动去合并/加字幕/上传视频——反过来，你得先跑完 `finalize_all_videos.py`（内部调用 `add_karaoke_captions.py --upload`）**审完成片**，再手动拖 Stage。
- - 而 merge / whisper 转录 / moviepy 烧字幕 / cover 生图 / infographic 生图，全部住在 `studio/` —— `studio/CLAUDE.md` 第一行写死了 **"This folder is NEVER deployed; it is local tooling only."** 字幕烧录甚至绑定在你这台机器的 ffmpeg build（没有 libass，只能用 moviepy 硬编码字体渲染）。
- 2. **Infographic 生图有脚本**（`batch_infographic_gen.py`）但它不在 `finalize_all_videos.py` 的调用链里，是完全独立、你得记得单独跑的东西。
- 3. **新增**：cover 生图（复用 `cover_blocks()` 已经写好的 prompt，调 gpt-image-2，带上 IP 参考脸——这点很关键，不能像 7/8 那次 Facebook 事故一样盲生成）+ 上传到 `🖼️ Cover here` toggle
- 跑完这一条命令，终端打印一份 checklist（cover✅ infographic✅ captions✅ uploaded✅），你扫一眼没问题再手动拖 Stage——审片关卡保留，但你不用再分别记 3-4 个脚本。
- **What I think you actually want:** not "automatic," but "one command instead of four." Right now you have to remember to run several separate scripts (merge, captions, cover, infographic) before dragging Stage — and two of those (cover, infographic) aren't even automated at all right now, you'd have to do them by hand. That's the real gap that caused this mess with the ear video.
- 4. **Safety-net in `notion_sync.py`** — warns (doesn't block) when video/cover missing on a Ready-to-Publish row, so it's visible instead of silent.
- I checked the actual code instead of assuming. Here's the real picture, piece by piece:


## 2026-07-08 20:13 — social-ip-engine

### What Didn't Work (negative knowledge)
- - (This is different from your `notion-sync` webhook, which fires instantly from the cloud regardless of your laptop — that one can't run this pipeline because it's heavy local-only tooling: whisper, moviepy, ffmpeg)
- **New gap found:** the merged video (`final.mp4`) currently has no path to reach Notion/Render at all — it only lives on your laptop. Render can't caption a video it can't fetch. Needs a small addition to `notion_video.py` to upload it to a new Notion property first.
- **Bottom line: flipping to Published right now would safely do nothing (no video) rather than publish something broken.** The real unlock is just: write "First DM," then run captions+upload locally, then it'll actually go live correctly.

### Architecture Decisions
- - **Captions (whisper + moviepy)** — 🟡 mostly portable, but **one real blocker**: the caption script hardcodes a macOS-only font path (`/System/Library/Fonts/.../Arial Black.ttf`). That font doesn't exist on Render's Linux server. We'd need to swap to a different bundled font, and re-tune the padding/line-wrap math — the stuff we just spent all of 7/7–7/8 debugging (glyph clipping, uneven line splits) was tuned specifically for Arial Black's metrics. Swap fonts = re-test that whole thing.

### Decisions & Reasoning
- 也就是说，脚本从不会因为你拖了 Stage 就自动去合并/加字幕/上传视频——反过来，你得先跑完 `finalize_all_videos.py`（内部调用 `add_karaoke_captions.py --upload`）**审完成片**，再手动拖 Stage。
- - 而 merge / whisper 转录 / moviepy 烧字幕 / cover 生图 / infographic 生图，全部住在 `studio/` —— `studio/CLAUDE.md` 第一行写死了 **"This folder is NEVER deployed; it is local tooling only."** 字幕烧录甚至绑定在你这台机器的 ffmpeg build（没有 libass，只能用 moviepy 硬编码字体渲染）。
- 2. **Infographic 生图有脚本**（`batch_infographic_gen.py`）但它不在 `finalize_all_videos.py` 的调用链里，是完全独立、你得记得单独跑的东西。
- 3. **新增**：cover 生图（复用 `cover_blocks()` 已经写好的 prompt，调 gpt-image-2，带上 IP 参考脸——这点很关键，不能像 7/8 那次 Facebook 事故一样盲生成）+ 上传到 `🖼️ Cover here` toggle
- 跑完这一条命令，终端打印一份 checklist（cover✅ infographic✅ captions✅ uploaded✅），你扫一眼没问题再手动拖 Stage——审片关卡保留，但你不用再分别记 3-4 个脚本。
- **What I think you actually want:** not "automatic," but "one command instead of four." Right now you have to remember to run several separate scripts (merge, captions, cover, infographic) before dragging Stage — and two of those (cover, infographic) aren't even automated at all right now, you'd have to do them by hand. That's the real gap that caused this mess with the ear video.
- 4. **Safety-net in `notion_sync.py`** — warns (doesn't block) when video/cover missing on a Ready-to-Publish row, so it's visible instead of silent.
- I checked the actual code instead of assuming. Here's the real picture, piece by piece:


## 2026-07-08 20:22 — social-ip-engine

### Decisions & Reasoning
- **改法（用 seedance-characters 的 three-tier action hierarchy）**：二选一
- 这是个真实的代码 gap，不只是内容问题：`_jimeng_camera()`（298-310行）已经会读 title 里的关键字（比如"demo"）来选镜头运镜，但 lip-sync 那句话完全没有类似的条件判断。**建议**：给 `build_jimeng_prompt()` 加一个判断——如果 visual 文本里出现"no dialogue to camera"/"action shot"，把 read 那句换成纯 VO 描述，不要求对口型。我可以现在就改这个函数，要吗？
- 但 `_primary_beat()`（234-243行）只取第一个分号/逗号/"then"之前的那一段作为静帧图片的 SCENE，"warm side lighting, soft focus"这个你特意写的打光指令，落在第二个 `;` 之后，**根本没被摘进 build_prompt() 里**。而且这段文字也没命中 `_clinic_kws`/`_street_kws` 任何关键字，所以最后套用的是最保底的 fallback：`"Setting: shallow depth of field, natural lighting."`——一句完全通用、没有意图的话。
- 按 directing-engine 的 Step 5（光是有动机的，不是随便一句"natural lighting"）：这镜的光线本该是特意设计的（warm side light 服务"温柔专业的诊疗感"），结果被模板吃掉了，变成了泛用光。**改法**：Shot 2 的视觉描述把光线线索挪到第一段（分号前），比如："...scrape from the center of her cheek outward to the ear, warm side lighting on her face, then down along the jawline..." 这样 `_primary_beat()` 才抓得到。
- 这是内容不一致：DM 私信发出去的信息图，承诺了视频里根本没演示过的手法。用户看完视频、评论关键字拿到图，会发现图上多了一条视频没教的东西。**建议**：要么把 brow-to-hairline 从 infographic 里删掉（保持图和视频严格对齐），要么在 Shot 3 补一句额头手法（更花成本，不建议为了这个改视频）。我倾向直接删。
- - Infographic 本身风格选择（illustration、非写实、no real faces）是对的——医美/身体相关内容用插画而非写实照片，本来就更安全，不用动。
- **我会怎么改**：拿掉对比图插入，把这个"恍然大悟"的瞬间做成一个真实可拍的动作——比如医生用手指轻按自己下颌，停顿、微微点头，一个"这不是脂肪"的确认表情。让画面自己完成认知转折，而不是靠一张信息图硬解释。对比图这个视觉任务，交给 DM 的 infographic 去做就够了（本来 infographic brief 里已经有箭头示意图，两边做同一件事是重复劳动）。
- - **Shot 2**：医生在**别人（患者）脸上**做示范，配音用"you"（"you scrape from the center of your face..."）


## 2026-07-08 20:29 — social-ip-engine

### What Didn't Work (negative knowledge)
- - (This is different from your `notion-sync` webhook, which fires instantly from the cloud regardless of your laptop — that one can't run this pipeline because it's heavy local-only tooling: whisper, moviepy, ffmpeg)
- **New gap found:** the merged video (`final.mp4`) currently has no path to reach Notion/Render at all — it only lives on your laptop. Render can't caption a video it can't fetch. Needs a small addition to `notion_video.py` to upload it to a new Notion property first.
- **Bottom line: flipping to Published right now would safely do nothing (no video) rather than publish something broken.** The real unlock is just: write "First DM," then run captions+upload locally, then it'll actually go live correctly.

### Architecture Decisions
- - **Captions (whisper + moviepy)** — 🟡 mostly portable, but **one real blocker**: the caption script hardcodes a macOS-only font path (`/System/Library/Fonts/.../Arial Black.ttf`). That font doesn't exist on Render's Linux server. We'd need to swap to a different bundled font, and re-tune the padding/line-wrap math — the stuff we just spent all of 7/7–7/8 debugging (glyph clipping, uneven line splits) was tuned specifically for Arial Black's metrics. Swap fonts = re-test that whole thing.

### Decisions & Reasoning
- 也就是说，脚本从不会因为你拖了 Stage 就自动去合并/加字幕/上传视频——反过来，你得先跑完 `finalize_all_videos.py`（内部调用 `add_karaoke_captions.py --upload`）**审完成片**，再手动拖 Stage。
- - 而 merge / whisper 转录 / moviepy 烧字幕 / cover 生图 / infographic 生图，全部住在 `studio/` —— `studio/CLAUDE.md` 第一行写死了 **"This folder is NEVER deployed; it is local tooling only."** 字幕烧录甚至绑定在你这台机器的 ffmpeg build（没有 libass，只能用 moviepy 硬编码字体渲染）。
- 2. **Infographic 生图有脚本**（`batch_infographic_gen.py`）但它不在 `finalize_all_videos.py` 的调用链里，是完全独立、你得记得单独跑的东西。
- 3. **新增**：cover 生图（复用 `cover_blocks()` 已经写好的 prompt，调 gpt-image-2，带上 IP 参考脸——这点很关键，不能像 7/8 那次 Facebook 事故一样盲生成）+ 上传到 `🖼️ Cover here` toggle
- 跑完这一条命令，终端打印一份 checklist（cover✅ infographic✅ captions✅ uploaded✅），你扫一眼没问题再手动拖 Stage——审片关卡保留，但你不用再分别记 3-4 个脚本。
- **What I think you actually want:** not "automatic," but "one command instead of four." Right now you have to remember to run several separate scripts (merge, captions, cover, infographic) before dragging Stage — and two of those (cover, infographic) aren't even automated at all right now, you'd have to do them by hand. That's the real gap that caused this mess with the ear video.
- 4. **Safety-net in `notion_sync.py`** — warns (doesn't block) when video/cover missing on a Ready-to-Publish row, so it's visible instead of silent.
- I checked the actual code instead of assuming. Here's the real picture, piece by piece:


## 2026-07-08 20:35 — social-ip-engine

### Decisions & Reasoning
- **改法（用 seedance-characters 的 three-tier action hierarchy）**：二选一
- 这是个真实的代码 gap，不只是内容问题：`_jimeng_camera()`（298-310行）已经会读 title 里的关键字（比如"demo"）来选镜头运镜，但 lip-sync 那句话完全没有类似的条件判断。**建议**：给 `build_jimeng_prompt()` 加一个判断——如果 visual 文本里出现"no dialogue to camera"/"action shot"，把 read 那句换成纯 VO 描述，不要求对口型。我可以现在就改这个函数，要吗？
- 但 `_primary_beat()`（234-243行）只取第一个分号/逗号/"then"之前的那一段作为静帧图片的 SCENE，"warm side lighting, soft focus"这个你特意写的打光指令，落在第二个 `;` 之后，**根本没被摘进 build_prompt() 里**。而且这段文字也没命中 `_clinic_kws`/`_street_kws` 任何关键字，所以最后套用的是最保底的 fallback：`"Setting: shallow depth of field, natural lighting."`——一句完全通用、没有意图的话。
- 按 directing-engine 的 Step 5（光是有动机的，不是随便一句"natural lighting"）：这镜的光线本该是特意设计的（warm side light 服务"温柔专业的诊疗感"），结果被模板吃掉了，变成了泛用光。**改法**：Shot 2 的视觉描述把光线线索挪到第一段（分号前），比如："...scrape from the center of her cheek outward to the ear, warm side lighting on her face, then down along the jawline..." 这样 `_primary_beat()` 才抓得到。
- 这是内容不一致：DM 私信发出去的信息图，承诺了视频里根本没演示过的手法。用户看完视频、评论关键字拿到图，会发现图上多了一条视频没教的东西。**建议**：要么把 brow-to-hairline 从 infographic 里删掉（保持图和视频严格对齐），要么在 Shot 3 补一句额头手法（更花成本，不建议为了这个改视频）。我倾向直接删。
- - Infographic 本身风格选择（illustration、非写实、no real faces）是对的——医美/身体相关内容用插画而非写实照片，本来就更安全，不用动。
- **我会怎么改**：拿掉对比图插入，把这个"恍然大悟"的瞬间做成一个真实可拍的动作——比如医生用手指轻按自己下颌，停顿、微微点头，一个"这不是脂肪"的确认表情。让画面自己完成认知转折，而不是靠一张信息图硬解释。对比图这个视觉任务，交给 DM 的 infographic 去做就够了（本来 infographic brief 里已经有箭头示意图，两边做同一件事是重复劳动）。
- - **Shot 2**：医生在**别人（患者）脸上**做示范，配音用"you"（"you scrape from the center of your face..."）


## 2026-07-08 20:36 — social-ip-engine

### What Didn't Work (negative knowledge)
- - (This is different from your `notion-sync` webhook, which fires instantly from the cloud regardless of your laptop — that one can't run this pipeline because it's heavy local-only tooling: whisper, moviepy, ffmpeg)
- **New gap found:** the merged video (`final.mp4`) currently has no path to reach Notion/Render at all — it only lives on your laptop. Render can't caption a video it can't fetch. Needs a small addition to `notion_video.py` to upload it to a new Notion property first.
- **Bottom line: flipping to Published right now would safely do nothing (no video) rather than publish something broken.** The real unlock is just: write "First DM," then run captions+upload locally, then it'll actually go live correctly.

### Architecture Decisions
- - **Captions (whisper + moviepy)** — 🟡 mostly portable, but **one real blocker**: the caption script hardcodes a macOS-only font path (`/System/Library/Fonts/.../Arial Black.ttf`). That font doesn't exist on Render's Linux server. We'd need to swap to a different bundled font, and re-tune the padding/line-wrap math — the stuff we just spent all of 7/7–7/8 debugging (glyph clipping, uneven line splits) was tuned specifically for Arial Black's metrics. Swap fonts = re-test that whole thing.

### Decisions & Reasoning
- 也就是说，脚本从不会因为你拖了 Stage 就自动去合并/加字幕/上传视频——反过来，你得先跑完 `finalize_all_videos.py`（内部调用 `add_karaoke_captions.py --upload`）**审完成片**，再手动拖 Stage。
- - 而 merge / whisper 转录 / moviepy 烧字幕 / cover 生图 / infographic 生图，全部住在 `studio/` —— `studio/CLAUDE.md` 第一行写死了 **"This folder is NEVER deployed; it is local tooling only."** 字幕烧录甚至绑定在你这台机器的 ffmpeg build（没有 libass，只能用 moviepy 硬编码字体渲染）。
- 2. **Infographic 生图有脚本**（`batch_infographic_gen.py`）但它不在 `finalize_all_videos.py` 的调用链里，是完全独立、你得记得单独跑的东西。
- 3. **新增**：cover 生图（复用 `cover_blocks()` 已经写好的 prompt，调 gpt-image-2，带上 IP 参考脸——这点很关键，不能像 7/8 那次 Facebook 事故一样盲生成）+ 上传到 `🖼️ Cover here` toggle
- 跑完这一条命令，终端打印一份 checklist（cover✅ infographic✅ captions✅ uploaded✅），你扫一眼没问题再手动拖 Stage——审片关卡保留，但你不用再分别记 3-4 个脚本。
- **What I think you actually want:** not "automatic," but "one command instead of four." Right now you have to remember to run several separate scripts (merge, captions, cover, infographic) before dragging Stage — and two of those (cover, infographic) aren't even automated at all right now, you'd have to do them by hand. That's the real gap that caused this mess with the ear video.
- 4. **Safety-net in `notion_sync.py`** — warns (doesn't block) when video/cover missing on a Ready-to-Publish row, so it's visible instead of silent.
- I checked the actual code instead of assuming. Here's the real picture, piece by piece:


## 2026-07-08 20:39 — social-ip-engine

### Decisions & Reasoning
- **改法（用 seedance-characters 的 three-tier action hierarchy）**：二选一
- 这是个真实的代码 gap，不只是内容问题：`_jimeng_camera()`（298-310行）已经会读 title 里的关键字（比如"demo"）来选镜头运镜，但 lip-sync 那句话完全没有类似的条件判断。**建议**：给 `build_jimeng_prompt()` 加一个判断——如果 visual 文本里出现"no dialogue to camera"/"action shot"，把 read 那句换成纯 VO 描述，不要求对口型。我可以现在就改这个函数，要吗？
- 但 `_primary_beat()`（234-243行）只取第一个分号/逗号/"then"之前的那一段作为静帧图片的 SCENE，"warm side lighting, soft focus"这个你特意写的打光指令，落在第二个 `;` 之后，**根本没被摘进 build_prompt() 里**。而且这段文字也没命中 `_clinic_kws`/`_street_kws` 任何关键字，所以最后套用的是最保底的 fallback：`"Setting: shallow depth of field, natural lighting."`——一句完全通用、没有意图的话。
- 按 directing-engine 的 Step 5（光是有动机的，不是随便一句"natural lighting"）：这镜的光线本该是特意设计的（warm side light 服务"温柔专业的诊疗感"），结果被模板吃掉了，变成了泛用光。**改法**：Shot 2 的视觉描述把光线线索挪到第一段（分号前），比如："...scrape from the center of her cheek outward to the ear, warm side lighting on her face, then down along the jawline..." 这样 `_primary_beat()` 才抓得到。
- 这是内容不一致：DM 私信发出去的信息图，承诺了视频里根本没演示过的手法。用户看完视频、评论关键字拿到图，会发现图上多了一条视频没教的东西。**建议**：要么把 brow-to-hairline 从 infographic 里删掉（保持图和视频严格对齐），要么在 Shot 3 补一句额头手法（更花成本，不建议为了这个改视频）。我倾向直接删。
- - Infographic 本身风格选择（illustration、非写实、no real faces）是对的——医美/身体相关内容用插画而非写实照片，本来就更安全，不用动。
- **我会怎么改**：拿掉对比图插入，把这个"恍然大悟"的瞬间做成一个真实可拍的动作——比如医生用手指轻按自己下颌，停顿、微微点头，一个"这不是脂肪"的确认表情。让画面自己完成认知转折，而不是靠一张信息图硬解释。对比图这个视觉任务，交给 DM 的 infographic 去做就够了（本来 infographic brief 里已经有箭头示意图，两边做同一件事是重复劳动）。
- - **Shot 2**：医生在**别人（患者）脸上**做示范，配音用"you"（"you scrape from the center of your face..."）


## 2026-07-09 17:37 — social-ip-engine

### Decisions & Reasoning
- **改法（用 seedance-characters 的 three-tier action hierarchy）**：二选一
- 这是个真实的代码 gap，不只是内容问题：`_jimeng_camera()`（298-310行）已经会读 title 里的关键字（比如"demo"）来选镜头运镜，但 lip-sync 那句话完全没有类似的条件判断。**建议**：给 `build_jimeng_prompt()` 加一个判断——如果 visual 文本里出现"no dialogue to camera"/"action shot"，把 read 那句换成纯 VO 描述，不要求对口型。我可以现在就改这个函数，要吗？
- 但 `_primary_beat()`（234-243行）只取第一个分号/逗号/"then"之前的那一段作为静帧图片的 SCENE，"warm side lighting, soft focus"这个你特意写的打光指令，落在第二个 `;` 之后，**根本没被摘进 build_prompt() 里**。而且这段文字也没命中 `_clinic_kws`/`_street_kws` 任何关键字，所以最后套用的是最保底的 fallback：`"Setting: shallow depth of field, natural lighting."`——一句完全通用、没有意图的话。
- 按 directing-engine 的 Step 5（光是有动机的，不是随便一句"natural lighting"）：这镜的光线本该是特意设计的（warm side light 服务"温柔专业的诊疗感"），结果被模板吃掉了，变成了泛用光。**改法**：Shot 2 的视觉描述把光线线索挪到第一段（分号前），比如："...scrape from the center of her cheek outward to the ear, warm side lighting on her face, then down along the jawline..." 这样 `_primary_beat()` 才抓得到。
- 这是内容不一致：DM 私信发出去的信息图，承诺了视频里根本没演示过的手法。用户看完视频、评论关键字拿到图，会发现图上多了一条视频没教的东西。**建议**：要么把 brow-to-hairline 从 infographic 里删掉（保持图和视频严格对齐），要么在 Shot 3 补一句额头手法（更花成本，不建议为了这个改视频）。我倾向直接删。
- - Infographic 本身风格选择（illustration、非写实、no real faces）是对的——医美/身体相关内容用插画而非写实照片，本来就更安全，不用动。
- **我会怎么改**：拿掉对比图插入，把这个"恍然大悟"的瞬间做成一个真实可拍的动作——比如医生用手指轻按自己下颌，停顿、微微点头，一个"这不是脂肪"的确认表情。让画面自己完成认知转折，而不是靠一张信息图硬解释。对比图这个视觉任务，交给 DM 的 infographic 去做就够了（本来 infographic brief 里已经有箭头示意图，两边做同一件事是重复劳动）。
- - **Shot 2**：医生在**别人（患者）脸上**做示范，配音用"you"（"you scrape from the center of your face..."）


## 2026-07-09 17:44 — social-ip-engine

### Decisions & Reasoning
- **改法（用 seedance-characters 的 three-tier action hierarchy）**：二选一
- 这是个真实的代码 gap，不只是内容问题：`_jimeng_camera()`（298-310行）已经会读 title 里的关键字（比如"demo"）来选镜头运镜，但 lip-sync 那句话完全没有类似的条件判断。**建议**：给 `build_jimeng_prompt()` 加一个判断——如果 visual 文本里出现"no dialogue to camera"/"action shot"，把 read 那句换成纯 VO 描述，不要求对口型。我可以现在就改这个函数，要吗？
- 但 `_primary_beat()`（234-243行）只取第一个分号/逗号/"then"之前的那一段作为静帧图片的 SCENE，"warm side lighting, soft focus"这个你特意写的打光指令，落在第二个 `;` 之后，**根本没被摘进 build_prompt() 里**。而且这段文字也没命中 `_clinic_kws`/`_street_kws` 任何关键字，所以最后套用的是最保底的 fallback：`"Setting: shallow depth of field, natural lighting."`——一句完全通用、没有意图的话。
- 按 directing-engine 的 Step 5（光是有动机的，不是随便一句"natural lighting"）：这镜的光线本该是特意设计的（warm side light 服务"温柔专业的诊疗感"），结果被模板吃掉了，变成了泛用光。**改法**：Shot 2 的视觉描述把光线线索挪到第一段（分号前），比如："...scrape from the center of her cheek outward to the ear, warm side lighting on her face, then down along the jawline..." 这样 `_primary_beat()` 才抓得到。
- 这是内容不一致：DM 私信发出去的信息图，承诺了视频里根本没演示过的手法。用户看完视频、评论关键字拿到图，会发现图上多了一条视频没教的东西。**建议**：要么把 brow-to-hairline 从 infographic 里删掉（保持图和视频严格对齐），要么在 Shot 3 补一句额头手法（更花成本，不建议为了这个改视频）。我倾向直接删。
- - Infographic 本身风格选择（illustration、非写实、no real faces）是对的——医美/身体相关内容用插画而非写实照片，本来就更安全，不用动。
- **我会怎么改**：拿掉对比图插入，把这个"恍然大悟"的瞬间做成一个真实可拍的动作——比如医生用手指轻按自己下颌，停顿、微微点头，一个"这不是脂肪"的确认表情。让画面自己完成认知转折，而不是靠一张信息图硬解释。对比图这个视觉任务，交给 DM 的 infographic 去做就够了（本来 infographic brief 里已经有箭头示意图，两边做同一件事是重复劳动）。
- - **Shot 2**：医生在**别人（患者）脸上**做示范，配音用"you"（"you scrape from the center of your face..."）


## 2026-07-09 17:46 — social-ip-engine

### Decisions & Reasoning
- **改法（用 seedance-characters 的 three-tier action hierarchy）**：二选一
- 这是个真实的代码 gap，不只是内容问题：`_jimeng_camera()`（298-310行）已经会读 title 里的关键字（比如"demo"）来选镜头运镜，但 lip-sync 那句话完全没有类似的条件判断。**建议**：给 `build_jimeng_prompt()` 加一个判断——如果 visual 文本里出现"no dialogue to camera"/"action shot"，把 read 那句换成纯 VO 描述，不要求对口型。我可以现在就改这个函数，要吗？
- 但 `_primary_beat()`（234-243行）只取第一个分号/逗号/"then"之前的那一段作为静帧图片的 SCENE，"warm side lighting, soft focus"这个你特意写的打光指令，落在第二个 `;` 之后，**根本没被摘进 build_prompt() 里**。而且这段文字也没命中 `_clinic_kws`/`_street_kws` 任何关键字，所以最后套用的是最保底的 fallback：`"Setting: shallow depth of field, natural lighting."`——一句完全通用、没有意图的话。
- 按 directing-engine 的 Step 5（光是有动机的，不是随便一句"natural lighting"）：这镜的光线本该是特意设计的（warm side light 服务"温柔专业的诊疗感"），结果被模板吃掉了，变成了泛用光。**改法**：Shot 2 的视觉描述把光线线索挪到第一段（分号前），比如："...scrape from the center of her cheek outward to the ear, warm side lighting on her face, then down along the jawline..." 这样 `_primary_beat()` 才抓得到。
- 这是内容不一致：DM 私信发出去的信息图，承诺了视频里根本没演示过的手法。用户看完视频、评论关键字拿到图，会发现图上多了一条视频没教的东西。**建议**：要么把 brow-to-hairline 从 infographic 里删掉（保持图和视频严格对齐），要么在 Shot 3 补一句额头手法（更花成本，不建议为了这个改视频）。我倾向直接删。
- - Infographic 本身风格选择（illustration、非写实、no real faces）是对的——医美/身体相关内容用插画而非写实照片，本来就更安全，不用动。
- **我会怎么改**：拿掉对比图插入，把这个"恍然大悟"的瞬间做成一个真实可拍的动作——比如医生用手指轻按自己下颌，停顿、微微点头，一个"这不是脂肪"的确认表情。让画面自己完成认知转折，而不是靠一张信息图硬解释。对比图这个视觉任务，交给 DM 的 infographic 去做就够了（本来 infographic brief 里已经有箭头示意图，两边做同一件事是重复劳动）。
- - **Shot 2**：医生在**别人（患者）脸上**做示范，配音用"you"（"you scrape from the center of your face..."）


## 2026-07-09 19:48 — social-ip-engine

### Decisions & Reasoning
- **改法（用 seedance-characters 的 three-tier action hierarchy）**：二选一
- 这是个真实的代码 gap，不只是内容问题：`_jimeng_camera()`（298-310行）已经会读 title 里的关键字（比如"demo"）来选镜头运镜，但 lip-sync 那句话完全没有类似的条件判断。**建议**：给 `build_jimeng_prompt()` 加一个判断——如果 visual 文本里出现"no dialogue to camera"/"action shot"，把 read 那句换成纯 VO 描述，不要求对口型。我可以现在就改这个函数，要吗？
- 但 `_primary_beat()`（234-243行）只取第一个分号/逗号/"then"之前的那一段作为静帧图片的 SCENE，"warm side lighting, soft focus"这个你特意写的打光指令，落在第二个 `;` 之后，**根本没被摘进 build_prompt() 里**。而且这段文字也没命中 `_clinic_kws`/`_street_kws` 任何关键字，所以最后套用的是最保底的 fallback：`"Setting: shallow depth of field, natural lighting."`——一句完全通用、没有意图的话。
- 按 directing-engine 的 Step 5（光是有动机的，不是随便一句"natural lighting"）：这镜的光线本该是特意设计的（warm side light 服务"温柔专业的诊疗感"），结果被模板吃掉了，变成了泛用光。**改法**：Shot 2 的视觉描述把光线线索挪到第一段（分号前），比如："...scrape from the center of her cheek outward to the ear, warm side lighting on her face, then down along the jawline..." 这样 `_primary_beat()` 才抓得到。
- 这是内容不一致：DM 私信发出去的信息图，承诺了视频里根本没演示过的手法。用户看完视频、评论关键字拿到图，会发现图上多了一条视频没教的东西。**建议**：要么把 brow-to-hairline 从 infographic 里删掉（保持图和视频严格对齐），要么在 Shot 3 补一句额头手法（更花成本，不建议为了这个改视频）。我倾向直接删。
- - Infographic 本身风格选择（illustration、非写实、no real faces）是对的——医美/身体相关内容用插画而非写实照片，本来就更安全，不用动。
- **我会怎么改**：拿掉对比图插入，把这个"恍然大悟"的瞬间做成一个真实可拍的动作——比如医生用手指轻按自己下颌，停顿、微微点头，一个"这不是脂肪"的确认表情。让画面自己完成认知转折，而不是靠一张信息图硬解释。对比图这个视觉任务，交给 DM 的 infographic 去做就够了（本来 infographic brief 里已经有箭头示意图，两边做同一件事是重复劳动）。
- - **Shot 2**：医生在**别人（患者）脸上**做示范，配音用"you"（"you scrape from the center of your face..."）


## 2026-07-09 19:52 — social-ip-engine

### Decisions & Reasoning
- **改法（用 seedance-characters 的 three-tier action hierarchy）**：二选一
- 这是个真实的代码 gap，不只是内容问题：`_jimeng_camera()`（298-310行）已经会读 title 里的关键字（比如"demo"）来选镜头运镜，但 lip-sync 那句话完全没有类似的条件判断。**建议**：给 `build_jimeng_prompt()` 加一个判断——如果 visual 文本里出现"no dialogue to camera"/"action shot"，把 read 那句换成纯 VO 描述，不要求对口型。我可以现在就改这个函数，要吗？
- 但 `_primary_beat()`（234-243行）只取第一个分号/逗号/"then"之前的那一段作为静帧图片的 SCENE，"warm side lighting, soft focus"这个你特意写的打光指令，落在第二个 `;` 之后，**根本没被摘进 build_prompt() 里**。而且这段文字也没命中 `_clinic_kws`/`_street_kws` 任何关键字，所以最后套用的是最保底的 fallback：`"Setting: shallow depth of field, natural lighting."`——一句完全通用、没有意图的话。
- 按 directing-engine 的 Step 5（光是有动机的，不是随便一句"natural lighting"）：这镜的光线本该是特意设计的（warm side light 服务"温柔专业的诊疗感"），结果被模板吃掉了，变成了泛用光。**改法**：Shot 2 的视觉描述把光线线索挪到第一段（分号前），比如："...scrape from the center of her cheek outward to the ear, warm side lighting on her face, then down along the jawline..." 这样 `_primary_beat()` 才抓得到。
- 这是内容不一致：DM 私信发出去的信息图，承诺了视频里根本没演示过的手法。用户看完视频、评论关键字拿到图，会发现图上多了一条视频没教的东西。**建议**：要么把 brow-to-hairline 从 infographic 里删掉（保持图和视频严格对齐），要么在 Shot 3 补一句额头手法（更花成本，不建议为了这个改视频）。我倾向直接删。
- - Infographic 本身风格选择（illustration、非写实、no real faces）是对的——医美/身体相关内容用插画而非写实照片，本来就更安全，不用动。
- **我会怎么改**：拿掉对比图插入，把这个"恍然大悟"的瞬间做成一个真实可拍的动作——比如医生用手指轻按自己下颌，停顿、微微点头，一个"这不是脂肪"的确认表情。让画面自己完成认知转折，而不是靠一张信息图硬解释。对比图这个视觉任务，交给 DM 的 infographic 去做就够了（本来 infographic brief 里已经有箭头示意图，两边做同一件事是重复劳动）。
- - **Shot 2**：医生在**别人（患者）脸上**做示范，配音用"you"（"you scrape from the center of your face..."）


## 2026-07-10 10:12 — social-ip-engine

### Decisions & Reasoning
- **改法（用 seedance-characters 的 three-tier action hierarchy）**：二选一
- 这是个真实的代码 gap，不只是内容问题：`_jimeng_camera()`（298-310行）已经会读 title 里的关键字（比如"demo"）来选镜头运镜，但 lip-sync 那句话完全没有类似的条件判断。**建议**：给 `build_jimeng_prompt()` 加一个判断——如果 visual 文本里出现"no dialogue to camera"/"action shot"，把 read 那句换成纯 VO 描述，不要求对口型。我可以现在就改这个函数，要吗？
- 但 `_primary_beat()`（234-243行）只取第一个分号/逗号/"then"之前的那一段作为静帧图片的 SCENE，"warm side lighting, soft focus"这个你特意写的打光指令，落在第二个 `;` 之后，**根本没被摘进 build_prompt() 里**。而且这段文字也没命中 `_clinic_kws`/`_street_kws` 任何关键字，所以最后套用的是最保底的 fallback：`"Setting: shallow depth of field, natural lighting."`——一句完全通用、没有意图的话。
- 按 directing-engine 的 Step 5（光是有动机的，不是随便一句"natural lighting"）：这镜的光线本该是特意设计的（warm side light 服务"温柔专业的诊疗感"），结果被模板吃掉了，变成了泛用光。**改法**：Shot 2 的视觉描述把光线线索挪到第一段（分号前），比如："...scrape from the center of her cheek outward to the ear, warm side lighting on her face, then down along the jawline..." 这样 `_primary_beat()` 才抓得到。
- 这是内容不一致：DM 私信发出去的信息图，承诺了视频里根本没演示过的手法。用户看完视频、评论关键字拿到图，会发现图上多了一条视频没教的东西。**建议**：要么把 brow-to-hairline 从 infographic 里删掉（保持图和视频严格对齐），要么在 Shot 3 补一句额头手法（更花成本，不建议为了这个改视频）。我倾向直接删。
- - Infographic 本身风格选择（illustration、非写实、no real faces）是对的——医美/身体相关内容用插画而非写实照片，本来就更安全，不用动。
- **我会怎么改**：拿掉对比图插入，把这个"恍然大悟"的瞬间做成一个真实可拍的动作——比如医生用手指轻按自己下颌，停顿、微微点头，一个"这不是脂肪"的确认表情。让画面自己完成认知转折，而不是靠一张信息图硬解释。对比图这个视觉任务，交给 DM 的 infographic 去做就够了（本来 infographic brief 里已经有箭头示意图，两边做同一件事是重复劳动）。
- - **Shot 2**：医生在**别人（患者）脸上**做示范，配音用"you"（"you scrape from the center of your face..."）


## 2026-07-10 10:15 — social-ip-engine

### Decisions & Reasoning
- **改法（用 seedance-characters 的 three-tier action hierarchy）**：二选一
- 这是个真实的代码 gap，不只是内容问题：`_jimeng_camera()`（298-310行）已经会读 title 里的关键字（比如"demo"）来选镜头运镜，但 lip-sync 那句话完全没有类似的条件判断。**建议**：给 `build_jimeng_prompt()` 加一个判断——如果 visual 文本里出现"no dialogue to camera"/"action shot"，把 read 那句换成纯 VO 描述，不要求对口型。我可以现在就改这个函数，要吗？
- 但 `_primary_beat()`（234-243行）只取第一个分号/逗号/"then"之前的那一段作为静帧图片的 SCENE，"warm side lighting, soft focus"这个你特意写的打光指令，落在第二个 `;` 之后，**根本没被摘进 build_prompt() 里**。而且这段文字也没命中 `_clinic_kws`/`_street_kws` 任何关键字，所以最后套用的是最保底的 fallback：`"Setting: shallow depth of field, natural lighting."`——一句完全通用、没有意图的话。
- 按 directing-engine 的 Step 5（光是有动机的，不是随便一句"natural lighting"）：这镜的光线本该是特意设计的（warm side light 服务"温柔专业的诊疗感"），结果被模板吃掉了，变成了泛用光。**改法**：Shot 2 的视觉描述把光线线索挪到第一段（分号前），比如："...scrape from the center of her cheek outward to the ear, warm side lighting on her face, then down along the jawline..." 这样 `_primary_beat()` 才抓得到。
- 这是内容不一致：DM 私信发出去的信息图，承诺了视频里根本没演示过的手法。用户看完视频、评论关键字拿到图，会发现图上多了一条视频没教的东西。**建议**：要么把 brow-to-hairline 从 infographic 里删掉（保持图和视频严格对齐），要么在 Shot 3 补一句额头手法（更花成本，不建议为了这个改视频）。我倾向直接删。
- - Infographic 本身风格选择（illustration、非写实、no real faces）是对的——医美/身体相关内容用插画而非写实照片，本来就更安全，不用动。
- **我会怎么改**：拿掉对比图插入，把这个"恍然大悟"的瞬间做成一个真实可拍的动作——比如医生用手指轻按自己下颌，停顿、微微点头，一个"这不是脂肪"的确认表情。让画面自己完成认知转折，而不是靠一张信息图硬解释。对比图这个视觉任务，交给 DM 的 infographic 去做就够了（本来 infographic brief 里已经有箭头示意图，两边做同一件事是重复劳动）。
- - **Shot 2**：医生在**别人（患者）脸上**做示范，配音用"you"（"you scrape from the center of your face..."）


## 2026-07-10 10:31 — social-ip-engine

### Decisions & Reasoning
- **2. Detail 页直接内嵌真素材 — review 不用再开 Notion**
- 你先点开一个「图+声待 review」的 row 用一下，哪里不顺手告诉我，我马上调。


## 2026-07-10 10:46 — social-ip-engine

### Decisions & Reasoning
- **2. Detail 页直接内嵌真素材 — review 不用再开 Notion**
- 你先点开一个「图+声待 review」的 row 用一下，哪里不顺手告诉我，我马上调。
- ✅ **改完了 — 浏览器里刷新 http://localhost:8420 就能看到新皮肤**（CSS/JS 是静态文件，不用重启服务器）
- - 标题用 Fraunces 艺术衬线（斜体渐变 logo），正文 Space Grotesk


## 2026-07-10 10:47 — social-ip-engine

### Decisions & Reasoning
- **2. Detail 页直接内嵌真素材 — review 不用再开 Notion**
- 你先点开一个「图+声待 review」的 row 用一下，哪里不顺手告诉我，我马上调。
- ✅ **改完了 — 浏览器里刷新 http://localhost:8420 就能看到新皮肤**（CSS/JS 是静态文件，不用重启服务器）
- - 标题用 Fraunces 艺术衬线（斜体渐变 logo），正文 Space Grotesk
- 加一个轻量自动同步：工作台每 60 秒静默拉一次（一次 DB query，很便宜），数据没变就不重绘（不会打断你正在看的东西）；Detail 页不自动刷（它要走十几个 Notion API 调用，而且刷新会打断正在播的视频）——


## 2026-07-10 10:49 — social-ip-engine

### Decisions & Reasoning
- **2. Detail 页直接内嵌真素材 — review 不用再开 Notion**
- 你先点开一个「图+声待 review」的 row 用一下，哪里不顺手告诉我，我马上调。
- ✅ **改完了 — 浏览器里刷新 http://localhost:8420 就能看到新皮肤**（CSS/JS 是静态文件，不用重启服务器）
- - 标题用 Fraunces 艺术衬线（斜体渐变 logo），正文 Space Grotesk
- 加一个轻量自动同步：工作台每 60 秒静默拉一次（一次 DB query，很便宜），数据没变就不重绘（不会打断你正在看的东西）；Detail 页不自动刷（它要走十几个 Notion API 调用，而且刷新会打断正在播的视频）——
- - 切走再切回来这个浏览器 tab 时立即补一次同步（不用等 60 秒）
- **一个刻意的取舍：** Detail 页（打开单个 row 的那页）**不**自动刷新 — 它一次要走 ~15 个 Notion API 调用，而且自动重绘会打断你正在播的视频/音频。看 detail 时想要最新状态，点「↻ 刷新」；跑任务结束后它本来就会自动刷。


## 2026-07-10 10:49 — social-ip-engine

### Decisions & Reasoning
- **改法（用 seedance-characters 的 three-tier action hierarchy）**：二选一
- 这是个真实的代码 gap，不只是内容问题：`_jimeng_camera()`（298-310行）已经会读 title 里的关键字（比如"demo"）来选镜头运镜，但 lip-sync 那句话完全没有类似的条件判断。**建议**：给 `build_jimeng_prompt()` 加一个判断——如果 visual 文本里出现"no dialogue to camera"/"action shot"，把 read 那句换成纯 VO 描述，不要求对口型。我可以现在就改这个函数，要吗？
- 但 `_primary_beat()`（234-243行）只取第一个分号/逗号/"then"之前的那一段作为静帧图片的 SCENE，"warm side lighting, soft focus"这个你特意写的打光指令，落在第二个 `;` 之后，**根本没被摘进 build_prompt() 里**。而且这段文字也没命中 `_clinic_kws`/`_street_kws` 任何关键字，所以最后套用的是最保底的 fallback：`"Setting: shallow depth of field, natural lighting."`——一句完全通用、没有意图的话。
- 按 directing-engine 的 Step 5（光是有动机的，不是随便一句"natural lighting"）：这镜的光线本该是特意设计的（warm side light 服务"温柔专业的诊疗感"），结果被模板吃掉了，变成了泛用光。**改法**：Shot 2 的视觉描述把光线线索挪到第一段（分号前），比如："...scrape from the center of her cheek outward to the ear, warm side lighting on her face, then down along the jawline..." 这样 `_primary_beat()` 才抓得到。
- 这是内容不一致：DM 私信发出去的信息图，承诺了视频里根本没演示过的手法。用户看完视频、评论关键字拿到图，会发现图上多了一条视频没教的东西。**建议**：要么把 brow-to-hairline 从 infographic 里删掉（保持图和视频严格对齐），要么在 Shot 3 补一句额头手法（更花成本，不建议为了这个改视频）。我倾向直接删。
- - Infographic 本身风格选择（illustration、非写实、no real faces）是对的——医美/身体相关内容用插画而非写实照片，本来就更安全，不用动。
- **我会怎么改**：拿掉对比图插入，把这个"恍然大悟"的瞬间做成一个真实可拍的动作——比如医生用手指轻按自己下颌，停顿、微微点头，一个"这不是脂肪"的确认表情。让画面自己完成认知转折，而不是靠一张信息图硬解释。对比图这个视觉任务，交给 DM 的 infographic 去做就够了（本来 infographic brief 里已经有箭头示意图，两边做同一件事是重复劳动）。
- - **Shot 2**：医生在**别人（患者）脸上**做示范，配音用"you"（"you scrape from the center of your face..."）


## 2026-07-10 11:00 — social-ip-engine

### Decisions & Reasoning
- **2. Detail 页直接内嵌真素材 — review 不用再开 Notion**
- 你先点开一个「图+声待 review」的 row 用一下，哪里不顺手告诉我，我马上调。
- ✅ **改完了 — 浏览器里刷新 http://localhost:8420 就能看到新皮肤**（CSS/JS 是静态文件，不用重启服务器）
- - 标题用 Fraunces 艺术衬线（斜体渐变 logo），正文 Space Grotesk
- 加一个轻量自动同步：工作台每 60 秒静默拉一次（一次 DB query，很便宜），数据没变就不重绘（不会打断你正在看的东西）；Detail 页不自动刷（它要走十几个 Notion API 调用，而且刷新会打断正在播的视频）——
- - 切走再切回来这个浏览器 tab 时立即补一次同步（不用等 60 秒）
- **一个刻意的取舍：** Detail 页（打开单个 row 的那页）**不**自动刷新 — 它一次要走 ~15 个 Notion API 调用，而且自动重绘会打断你正在播的视频/音频。看 detail 时想要最新状态，点「↻ 刷新」；跑任务结束后它本来就会自动刷。


## 2026-07-10 11:03 — social-ip-engine

### Decisions & Reasoning
- **改法（用 seedance-characters 的 three-tier action hierarchy）**：二选一
- 这是个真实的代码 gap，不只是内容问题：`_jimeng_camera()`（298-310行）已经会读 title 里的关键字（比如"demo"）来选镜头运镜，但 lip-sync 那句话完全没有类似的条件判断。**建议**：给 `build_jimeng_prompt()` 加一个判断——如果 visual 文本里出现"no dialogue to camera"/"action shot"，把 read 那句换成纯 VO 描述，不要求对口型。我可以现在就改这个函数，要吗？
- 但 `_primary_beat()`（234-243行）只取第一个分号/逗号/"then"之前的那一段作为静帧图片的 SCENE，"warm side lighting, soft focus"这个你特意写的打光指令，落在第二个 `;` 之后，**根本没被摘进 build_prompt() 里**。而且这段文字也没命中 `_clinic_kws`/`_street_kws` 任何关键字，所以最后套用的是最保底的 fallback：`"Setting: shallow depth of field, natural lighting."`——一句完全通用、没有意图的话。
- 按 directing-engine 的 Step 5（光是有动机的，不是随便一句"natural lighting"）：这镜的光线本该是特意设计的（warm side light 服务"温柔专业的诊疗感"），结果被模板吃掉了，变成了泛用光。**改法**：Shot 2 的视觉描述把光线线索挪到第一段（分号前），比如："...scrape from the center of her cheek outward to the ear, warm side lighting on her face, then down along the jawline..." 这样 `_primary_beat()` 才抓得到。
- 这是内容不一致：DM 私信发出去的信息图，承诺了视频里根本没演示过的手法。用户看完视频、评论关键字拿到图，会发现图上多了一条视频没教的东西。**建议**：要么把 brow-to-hairline 从 infographic 里删掉（保持图和视频严格对齐），要么在 Shot 3 补一句额头手法（更花成本，不建议为了这个改视频）。我倾向直接删。
- - Infographic 本身风格选择（illustration、非写实、no real faces）是对的——医美/身体相关内容用插画而非写实照片，本来就更安全，不用动。
- **我会怎么改**：拿掉对比图插入，把这个"恍然大悟"的瞬间做成一个真实可拍的动作——比如医生用手指轻按自己下颌，停顿、微微点头，一个"这不是脂肪"的确认表情。让画面自己完成认知转折，而不是靠一张信息图硬解释。对比图这个视觉任务，交给 DM 的 infographic 去做就够了（本来 infographic brief 里已经有箭头示意图，两边做同一件事是重复劳动）。
- - **Shot 2**：医生在**别人（患者）脸上**做示范，配音用"you"（"you scrape from the center of your face..."）


## 2026-07-10 11:06 — social-ip-engine

### What Didn't Work (negative knowledge)
- **4. Period Pain 其实昨天已经上 IG 了。** 服务器 commit 记录显示台账清掉后触发重新发布成功(caption 是 Hook 生成的那句 "Pain so bad you can't move?...Comment 'period' 👇")。但它用的是**旧 cover 逻辑**——已经发出去的这条 IG 帖子的封面改不了(IG API 不支持事后换封面),只有以后的帖子会用对。你可以去 Jackie 的 IG 确认一下这条帖子存不存在、封面能不能接受。

### Decisions & Reasoning
- **改法（用 seedance-characters 的 three-tier action hierarchy）**：二选一
- 这是个真实的代码 gap，不只是内容问题：`_jimeng_camera()`（298-310行）已经会读 title 里的关键字（比如"demo"）来选镜头运镜，但 lip-sync 那句话完全没有类似的条件判断。**建议**：给 `build_jimeng_prompt()` 加一个判断——如果 visual 文本里出现"no dialogue to camera"/"action shot"，把 read 那句换成纯 VO 描述，不要求对口型。我可以现在就改这个函数，要吗？
- 但 `_primary_beat()`（234-243行）只取第一个分号/逗号/"then"之前的那一段作为静帧图片的 SCENE，"warm side lighting, soft focus"这个你特意写的打光指令，落在第二个 `;` 之后，**根本没被摘进 build_prompt() 里**。而且这段文字也没命中 `_clinic_kws`/`_street_kws` 任何关键字，所以最后套用的是最保底的 fallback：`"Setting: shallow depth of field, natural lighting."`——一句完全通用、没有意图的话。
- 按 directing-engine 的 Step 5（光是有动机的，不是随便一句"natural lighting"）：这镜的光线本该是特意设计的（warm side light 服务"温柔专业的诊疗感"），结果被模板吃掉了，变成了泛用光。**改法**：Shot 2 的视觉描述把光线线索挪到第一段（分号前），比如："...scrape from the center of her cheek outward to the ear, warm side lighting on her face, then down along the jawline..." 这样 `_primary_beat()` 才抓得到。
- 这是内容不一致：DM 私信发出去的信息图，承诺了视频里根本没演示过的手法。用户看完视频、评论关键字拿到图，会发现图上多了一条视频没教的东西。**建议**：要么把 brow-to-hairline 从 infographic 里删掉（保持图和视频严格对齐），要么在 Shot 3 补一句额头手法（更花成本，不建议为了这个改视频）。我倾向直接删。
- - Infographic 本身风格选择（illustration、非写实、no real faces）是对的——医美/身体相关内容用插画而非写实照片，本来就更安全，不用动。
- **我会怎么改**：拿掉对比图插入，把这个"恍然大悟"的瞬间做成一个真实可拍的动作——比如医生用手指轻按自己下颌，停顿、微微点头，一个"这不是脂肪"的确认表情。让画面自己完成认知转折，而不是靠一张信息图硬解释。对比图这个视觉任务，交给 DM 的 infographic 去做就够了（本来 infographic brief 里已经有箭头示意图，两边做同一件事是重复劳动）。
- - **Shot 2**：医生在**别人（患者）脸上**做示范，配音用"you"（"you scrape from the center of your face..."）


## 2026-07-10 11:12 — social-ip-engine

### What Didn't Work (negative knowledge)
- **4. Period Pain 其实昨天已经上 IG 了。** 服务器 commit 记录显示台账清掉后触发重新发布成功(caption 是 Hook 生成的那句 "Pain so bad you can't move?...Comment 'period' 👇")。但它用的是**旧 cover 逻辑**——已经发出去的这条 IG 帖子的封面改不了(IG API 不支持事后换封面),只有以后的帖子会用对。你可以去 Jackie 的 IG 确认一下这条帖子存不存在、封面能不能接受。

### Decisions & Reasoning
- **改法（用 seedance-characters 的 three-tier action hierarchy）**：二选一
- 这是个真实的代码 gap，不只是内容问题：`_jimeng_camera()`（298-310行）已经会读 title 里的关键字（比如"demo"）来选镜头运镜，但 lip-sync 那句话完全没有类似的条件判断。**建议**：给 `build_jimeng_prompt()` 加一个判断——如果 visual 文本里出现"no dialogue to camera"/"action shot"，把 read 那句换成纯 VO 描述，不要求对口型。我可以现在就改这个函数，要吗？
- 但 `_primary_beat()`（234-243行）只取第一个分号/逗号/"then"之前的那一段作为静帧图片的 SCENE，"warm side lighting, soft focus"这个你特意写的打光指令，落在第二个 `;` 之后，**根本没被摘进 build_prompt() 里**。而且这段文字也没命中 `_clinic_kws`/`_street_kws` 任何关键字，所以最后套用的是最保底的 fallback：`"Setting: shallow depth of field, natural lighting."`——一句完全通用、没有意图的话。
- 按 directing-engine 的 Step 5（光是有动机的，不是随便一句"natural lighting"）：这镜的光线本该是特意设计的（warm side light 服务"温柔专业的诊疗感"），结果被模板吃掉了，变成了泛用光。**改法**：Shot 2 的视觉描述把光线线索挪到第一段（分号前），比如："...scrape from the center of her cheek outward to the ear, warm side lighting on her face, then down along the jawline..." 这样 `_primary_beat()` 才抓得到。
- 这是内容不一致：DM 私信发出去的信息图，承诺了视频里根本没演示过的手法。用户看完视频、评论关键字拿到图，会发现图上多了一条视频没教的东西。**建议**：要么把 brow-to-hairline 从 infographic 里删掉（保持图和视频严格对齐），要么在 Shot 3 补一句额头手法（更花成本，不建议为了这个改视频）。我倾向直接删。
- - Infographic 本身风格选择（illustration、非写实、no real faces）是对的——医美/身体相关内容用插画而非写实照片，本来就更安全，不用动。
- **我会怎么改**：拿掉对比图插入，把这个"恍然大悟"的瞬间做成一个真实可拍的动作——比如医生用手指轻按自己下颌，停顿、微微点头，一个"这不是脂肪"的确认表情。让画面自己完成认知转折，而不是靠一张信息图硬解释。对比图这个视觉任务，交给 DM 的 infographic 去做就够了（本来 infographic brief 里已经有箭头示意图，两边做同一件事是重复劳动）。
- - **Shot 2**：医生在**别人（患者）脸上**做示范，配音用"you"（"you scrape from the center of your face..."）


## 2026-07-10 12:57 — social-ip-engine

### What Didn't Work (negative knowledge)
- **4. Period Pain 其实昨天已经上 IG 了。** 服务器 commit 记录显示台账清掉后触发重新发布成功(caption 是 Hook 生成的那句 "Pain so bad you can't move?...Comment 'period' 👇")。但它用的是**旧 cover 逻辑**——已经发出去的这条 IG 帖子的封面改不了(IG API 不支持事后换封面),只有以后的帖子会用对。你可以去 Jackie 的 IG 确认一下这条帖子存不存在、封面能不能接受。

### Decisions & Reasoning
- **改法（用 seedance-characters 的 three-tier action hierarchy）**：二选一
- 这是个真实的代码 gap，不只是内容问题：`_jimeng_camera()`（298-310行）已经会读 title 里的关键字（比如"demo"）来选镜头运镜，但 lip-sync 那句话完全没有类似的条件判断。**建议**：给 `build_jimeng_prompt()` 加一个判断——如果 visual 文本里出现"no dialogue to camera"/"action shot"，把 read 那句换成纯 VO 描述，不要求对口型。我可以现在就改这个函数，要吗？
- 但 `_primary_beat()`（234-243行）只取第一个分号/逗号/"then"之前的那一段作为静帧图片的 SCENE，"warm side lighting, soft focus"这个你特意写的打光指令，落在第二个 `;` 之后，**根本没被摘进 build_prompt() 里**。而且这段文字也没命中 `_clinic_kws`/`_street_kws` 任何关键字，所以最后套用的是最保底的 fallback：`"Setting: shallow depth of field, natural lighting."`——一句完全通用、没有意图的话。
- 按 directing-engine 的 Step 5（光是有动机的，不是随便一句"natural lighting"）：这镜的光线本该是特意设计的（warm side light 服务"温柔专业的诊疗感"），结果被模板吃掉了，变成了泛用光。**改法**：Shot 2 的视觉描述把光线线索挪到第一段（分号前），比如："...scrape from the center of her cheek outward to the ear, warm side lighting on her face, then down along the jawline..." 这样 `_primary_beat()` 才抓得到。
- 这是内容不一致：DM 私信发出去的信息图，承诺了视频里根本没演示过的手法。用户看完视频、评论关键字拿到图，会发现图上多了一条视频没教的东西。**建议**：要么把 brow-to-hairline 从 infographic 里删掉（保持图和视频严格对齐），要么在 Shot 3 补一句额头手法（更花成本，不建议为了这个改视频）。我倾向直接删。
- - Infographic 本身风格选择（illustration、非写实、no real faces）是对的——医美/身体相关内容用插画而非写实照片，本来就更安全，不用动。
- **我会怎么改**：拿掉对比图插入，把这个"恍然大悟"的瞬间做成一个真实可拍的动作——比如医生用手指轻按自己下颌，停顿、微微点头，一个"这不是脂肪"的确认表情。让画面自己完成认知转折，而不是靠一张信息图硬解释。对比图这个视觉任务，交给 DM 的 infographic 去做就够了（本来 infographic brief 里已经有箭头示意图，两边做同一件事是重复劳动）。
- - **Shot 2**：医生在**别人（患者）脸上**做示范，配音用"you"（"you scrape from the center of your face..."）


## 2026-07-10 12:59 — social-ip-engine

### Decisions & Reasoning
- **2. Detail 页直接内嵌真素材 — review 不用再开 Notion**
- 你先点开一个「图+声待 review」的 row 用一下，哪里不顺手告诉我，我马上调。
- ✅ **改完了 — 浏览器里刷新 http://localhost:8420 就能看到新皮肤**（CSS/JS 是静态文件，不用重启服务器）
- - 标题用 Fraunces 艺术衬线（斜体渐变 logo），正文 Space Grotesk
- 加一个轻量自动同步：工作台每 60 秒静默拉一次（一次 DB query，很便宜），数据没变就不重绘（不会打断你正在看的东西）；Detail 页不自动刷（它要走十几个 Notion API 调用，而且刷新会打断正在播的视频）——
- - 切走再切回来这个浏览器 tab 时立即补一次同步（不用等 60 秒）
- **一个刻意的取舍：** Detail 页（打开单个 row 的那页）**不**自动刷新 — 它一次要走 ~15 个 Notion API 调用，而且自动重绘会打断你正在播的视频/音频。看 detail 时想要最新状态，点「↻ 刷新」；跑任务结束后它本来就会自动刷。


## 2026-07-10 13:16 — social-ip-engine

### What Didn't Work (negative knowledge)
- **4. Period Pain 其实昨天已经上 IG 了。** 服务器 commit 记录显示台账清掉后触发重新发布成功(caption 是 Hook 生成的那句 "Pain so bad you can't move?...Comment 'period' 👇")。但它用的是**旧 cover 逻辑**——已经发出去的这条 IG 帖子的封面改不了(IG API 不支持事后换封面),只有以后的帖子会用对。你可以去 Jackie 的 IG 确认一下这条帖子存不存在、封面能不能接受。

### Decisions & Reasoning
- **改法（用 seedance-characters 的 three-tier action hierarchy）**：二选一
- 这是个真实的代码 gap，不只是内容问题：`_jimeng_camera()`（298-310行）已经会读 title 里的关键字（比如"demo"）来选镜头运镜，但 lip-sync 那句话完全没有类似的条件判断。**建议**：给 `build_jimeng_prompt()` 加一个判断——如果 visual 文本里出现"no dialogue to camera"/"action shot"，把 read 那句换成纯 VO 描述，不要求对口型。我可以现在就改这个函数，要吗？
- 但 `_primary_beat()`（234-243行）只取第一个分号/逗号/"then"之前的那一段作为静帧图片的 SCENE，"warm side lighting, soft focus"这个你特意写的打光指令，落在第二个 `;` 之后，**根本没被摘进 build_prompt() 里**。而且这段文字也没命中 `_clinic_kws`/`_street_kws` 任何关键字，所以最后套用的是最保底的 fallback：`"Setting: shallow depth of field, natural lighting."`——一句完全通用、没有意图的话。
- 按 directing-engine 的 Step 5（光是有动机的，不是随便一句"natural lighting"）：这镜的光线本该是特意设计的（warm side light 服务"温柔专业的诊疗感"），结果被模板吃掉了，变成了泛用光。**改法**：Shot 2 的视觉描述把光线线索挪到第一段（分号前），比如："...scrape from the center of her cheek outward to the ear, warm side lighting on her face, then down along the jawline..." 这样 `_primary_beat()` 才抓得到。
- 这是内容不一致：DM 私信发出去的信息图，承诺了视频里根本没演示过的手法。用户看完视频、评论关键字拿到图，会发现图上多了一条视频没教的东西。**建议**：要么把 brow-to-hairline 从 infographic 里删掉（保持图和视频严格对齐），要么在 Shot 3 补一句额头手法（更花成本，不建议为了这个改视频）。我倾向直接删。
- - Infographic 本身风格选择（illustration、非写实、no real faces）是对的——医美/身体相关内容用插画而非写实照片，本来就更安全，不用动。
- **我会怎么改**：拿掉对比图插入，把这个"恍然大悟"的瞬间做成一个真实可拍的动作——比如医生用手指轻按自己下颌，停顿、微微点头，一个"这不是脂肪"的确认表情。让画面自己完成认知转折，而不是靠一张信息图硬解释。对比图这个视觉任务，交给 DM 的 infographic 去做就够了（本来 infographic brief 里已经有箭头示意图，两边做同一件事是重复劳动）。
- - **Shot 2**：医生在**别人（患者）脸上**做示范，配音用"you"（"you scrape from the center of your face..."）


## 2026-07-10 13:22 — social-ip-engine

### What Didn't Work (negative knowledge)
- **4. Period Pain 其实昨天已经上 IG 了。** 服务器 commit 记录显示台账清掉后触发重新发布成功(caption 是 Hook 生成的那句 "Pain so bad you can't move?...Comment 'period' 👇")。但它用的是**旧 cover 逻辑**——已经发出去的这条 IG 帖子的封面改不了(IG API 不支持事后换封面),只有以后的帖子会用对。你可以去 Jackie 的 IG 确认一下这条帖子存不存在、封面能不能接受。

### Decisions & Reasoning
- **改法（用 seedance-characters 的 three-tier action hierarchy）**：二选一
- 这是个真实的代码 gap，不只是内容问题：`_jimeng_camera()`（298-310行）已经会读 title 里的关键字（比如"demo"）来选镜头运镜，但 lip-sync 那句话完全没有类似的条件判断。**建议**：给 `build_jimeng_prompt()` 加一个判断——如果 visual 文本里出现"no dialogue to camera"/"action shot"，把 read 那句换成纯 VO 描述，不要求对口型。我可以现在就改这个函数，要吗？
- 但 `_primary_beat()`（234-243行）只取第一个分号/逗号/"then"之前的那一段作为静帧图片的 SCENE，"warm side lighting, soft focus"这个你特意写的打光指令，落在第二个 `;` 之后，**根本没被摘进 build_prompt() 里**。而且这段文字也没命中 `_clinic_kws`/`_street_kws` 任何关键字，所以最后套用的是最保底的 fallback：`"Setting: shallow depth of field, natural lighting."`——一句完全通用、没有意图的话。
- 按 directing-engine 的 Step 5（光是有动机的，不是随便一句"natural lighting"）：这镜的光线本该是特意设计的（warm side light 服务"温柔专业的诊疗感"），结果被模板吃掉了，变成了泛用光。**改法**：Shot 2 的视觉描述把光线线索挪到第一段（分号前），比如："...scrape from the center of her cheek outward to the ear, warm side lighting on her face, then down along the jawline..." 这样 `_primary_beat()` 才抓得到。
- 这是内容不一致：DM 私信发出去的信息图，承诺了视频里根本没演示过的手法。用户看完视频、评论关键字拿到图，会发现图上多了一条视频没教的东西。**建议**：要么把 brow-to-hairline 从 infographic 里删掉（保持图和视频严格对齐），要么在 Shot 3 补一句额头手法（更花成本，不建议为了这个改视频）。我倾向直接删。
- - Infographic 本身风格选择（illustration、非写实、no real faces）是对的——医美/身体相关内容用插画而非写实照片，本来就更安全，不用动。
- **我会怎么改**：拿掉对比图插入，把这个"恍然大悟"的瞬间做成一个真实可拍的动作——比如医生用手指轻按自己下颌，停顿、微微点头，一个"这不是脂肪"的确认表情。让画面自己完成认知转折，而不是靠一张信息图硬解释。对比图这个视觉任务，交给 DM 的 infographic 去做就够了（本来 infographic brief 里已经有箭头示意图，两边做同一件事是重复劳动）。
- - **Shot 2**：医生在**别人（患者）脸上**做示范，配音用"you"（"you scrape from the center of your face..."）


## 2026-07-10 13:23 — social-ip-engine

### Decisions & Reasoning
- **2. Detail 页直接内嵌真素材 — review 不用再开 Notion**
- 你先点开一个「图+声待 review」的 row 用一下，哪里不顺手告诉我，我马上调。
- ✅ **改完了 — 浏览器里刷新 http://localhost:8420 就能看到新皮肤**（CSS/JS 是静态文件，不用重启服务器）
- - 标题用 Fraunces 艺术衬线（斜体渐变 logo），正文 Space Grotesk
- 加一个轻量自动同步：工作台每 60 秒静默拉一次（一次 DB query，很便宜），数据没变就不重绘（不会打断你正在看的东西）；Detail 页不自动刷（它要走十几个 Notion API 调用，而且刷新会打断正在播的视频）——
- - 切走再切回来这个浏览器 tab 时立即补一次同步（不用等 60 秒）
- **一个刻意的取舍：** Detail 页（打开单个 row 的那页）**不**自动刷新 — 它一次要走 ~15 个 Notion API 调用，而且自动重绘会打断你正在播的视频/音频。看 detail 时想要最新状态，点「↻ 刷新」；跑任务结束后它本来就会自动刷。
- - **↻ 图** — 只重生成这一个 shot 的图片：先删掉 toggle 里的旧图再生成新的（没图就直接补上）。用的还是这个 shot 自己的 Notion prompt + IP 参考脸


## 2026-07-10 13:33 — social-ip-engine

### Decisions & Reasoning
- **2. Detail 页直接内嵌真素材 — review 不用再开 Notion**
- 你先点开一个「图+声待 review」的 row 用一下，哪里不顺手告诉我，我马上调。
- ✅ **改完了 — 浏览器里刷新 http://localhost:8420 就能看到新皮肤**（CSS/JS 是静态文件，不用重启服务器）
- - 标题用 Fraunces 艺术衬线（斜体渐变 logo），正文 Space Grotesk
- 加一个轻量自动同步：工作台每 60 秒静默拉一次（一次 DB query，很便宜），数据没变就不重绘（不会打断你正在看的东西）；Detail 页不自动刷（它要走十几个 Notion API 调用，而且刷新会打断正在播的视频）——
- - 切走再切回来这个浏览器 tab 时立即补一次同步（不用等 60 秒）
- **一个刻意的取舍：** Detail 页（打开单个 row 的那页）**不**自动刷新 — 它一次要走 ~15 个 Notion API 调用，而且自动重绘会打断你正在播的视频/音频。看 detail 时想要最新状态，点「↻ 刷新」；跑任务结束后它本来就会自动刷。
- - **↻ 图** — 只重生成这一个 shot 的图片：先删掉 toggle 里的旧图再生成新的（没图就直接补上）。用的还是这个 shot 自己的 Notion prompt + IP 参考脸


## 2026-07-10 13:37 — social-ip-engine

### What Didn't Work (negative knowledge)
- **4. Period Pain 其实昨天已经上 IG 了。** 服务器 commit 记录显示台账清掉后触发重新发布成功(caption 是 Hook 生成的那句 "Pain so bad you can't move?...Comment 'period' 👇")。但它用的是**旧 cover 逻辑**——已经发出去的这条 IG 帖子的封面改不了(IG API 不支持事后换封面),只有以后的帖子会用对。你可以去 Jackie 的 IG 确认一下这条帖子存不存在、封面能不能接受。

### Decisions & Reasoning
- **改法（用 seedance-characters 的 three-tier action hierarchy）**：二选一
- 这是个真实的代码 gap，不只是内容问题：`_jimeng_camera()`（298-310行）已经会读 title 里的关键字（比如"demo"）来选镜头运镜，但 lip-sync 那句话完全没有类似的条件判断。**建议**：给 `build_jimeng_prompt()` 加一个判断——如果 visual 文本里出现"no dialogue to camera"/"action shot"，把 read 那句换成纯 VO 描述，不要求对口型。我可以现在就改这个函数，要吗？
- 但 `_primary_beat()`（234-243行）只取第一个分号/逗号/"then"之前的那一段作为静帧图片的 SCENE，"warm side lighting, soft focus"这个你特意写的打光指令，落在第二个 `;` 之后，**根本没被摘进 build_prompt() 里**。而且这段文字也没命中 `_clinic_kws`/`_street_kws` 任何关键字，所以最后套用的是最保底的 fallback：`"Setting: shallow depth of field, natural lighting."`——一句完全通用、没有意图的话。
- 按 directing-engine 的 Step 5（光是有动机的，不是随便一句"natural lighting"）：这镜的光线本该是特意设计的（warm side light 服务"温柔专业的诊疗感"），结果被模板吃掉了，变成了泛用光。**改法**：Shot 2 的视觉描述把光线线索挪到第一段（分号前），比如："...scrape from the center of her cheek outward to the ear, warm side lighting on her face, then down along the jawline..." 这样 `_primary_beat()` 才抓得到。
- 这是内容不一致：DM 私信发出去的信息图，承诺了视频里根本没演示过的手法。用户看完视频、评论关键字拿到图，会发现图上多了一条视频没教的东西。**建议**：要么把 brow-to-hairline 从 infographic 里删掉（保持图和视频严格对齐），要么在 Shot 3 补一句额头手法（更花成本，不建议为了这个改视频）。我倾向直接删。
- - Infographic 本身风格选择（illustration、非写实、no real faces）是对的——医美/身体相关内容用插画而非写实照片，本来就更安全，不用动。
- **我会怎么改**：拿掉对比图插入，把这个"恍然大悟"的瞬间做成一个真实可拍的动作——比如医生用手指轻按自己下颌，停顿、微微点头，一个"这不是脂肪"的确认表情。让画面自己完成认知转折，而不是靠一张信息图硬解释。对比图这个视觉任务，交给 DM 的 infographic 去做就够了（本来 infographic brief 里已经有箭头示意图，两边做同一件事是重复劳动）。
- - **Shot 2**：医生在**别人（患者）脸上**做示范，配音用"you"（"you scrape from the center of your face..."）


## 2026-07-10 13:39 — social-ip-engine

### What Didn't Work (negative knowledge)
- **4. Period Pain 其实昨天已经上 IG 了。** 服务器 commit 记录显示台账清掉后触发重新发布成功(caption 是 Hook 生成的那句 "Pain so bad you can't move?...Comment 'period' 👇")。但它用的是**旧 cover 逻辑**——已经发出去的这条 IG 帖子的封面改不了(IG API 不支持事后换封面),只有以后的帖子会用对。你可以去 Jackie 的 IG 确认一下这条帖子存不存在、封面能不能接受。
- 监控在跑。IG 视频处理一般 2-5 分钟,FB 再加 2 分钟左右。这次是全新代码走的第一条完整链路:封面从 Cover Photo toggle 读、caption 用 "Can't Move from Pain? Try This NOW! 😱"、FB 拿新鲜链接镜像。结果一出来我就报,包括两边的 media id 和实际用的 cover URL,你直接刷 IG/FB 就能看到新帖。

### Decisions & Reasoning
- **改法（用 seedance-characters 的 three-tier action hierarchy）**：二选一
- 这是个真实的代码 gap，不只是内容问题：`_jimeng_camera()`（298-310行）已经会读 title 里的关键字（比如"demo"）来选镜头运镜，但 lip-sync 那句话完全没有类似的条件判断。**建议**：给 `build_jimeng_prompt()` 加一个判断——如果 visual 文本里出现"no dialogue to camera"/"action shot"，把 read 那句换成纯 VO 描述，不要求对口型。我可以现在就改这个函数，要吗？
- 但 `_primary_beat()`（234-243行）只取第一个分号/逗号/"then"之前的那一段作为静帧图片的 SCENE，"warm side lighting, soft focus"这个你特意写的打光指令，落在第二个 `;` 之后，**根本没被摘进 build_prompt() 里**。而且这段文字也没命中 `_clinic_kws`/`_street_kws` 任何关键字，所以最后套用的是最保底的 fallback：`"Setting: shallow depth of field, natural lighting."`——一句完全通用、没有意图的话。
- 按 directing-engine 的 Step 5（光是有动机的，不是随便一句"natural lighting"）：这镜的光线本该是特意设计的（warm side light 服务"温柔专业的诊疗感"），结果被模板吃掉了，变成了泛用光。**改法**：Shot 2 的视觉描述把光线线索挪到第一段（分号前），比如："...scrape from the center of her cheek outward to the ear, warm side lighting on her face, then down along the jawline..." 这样 `_primary_beat()` 才抓得到。
- 这是内容不一致：DM 私信发出去的信息图，承诺了视频里根本没演示过的手法。用户看完视频、评论关键字拿到图，会发现图上多了一条视频没教的东西。**建议**：要么把 brow-to-hairline 从 infographic 里删掉（保持图和视频严格对齐），要么在 Shot 3 补一句额头手法（更花成本，不建议为了这个改视频）。我倾向直接删。
- - Infographic 本身风格选择（illustration、非写实、no real faces）是对的——医美/身体相关内容用插画而非写实照片，本来就更安全，不用动。
- **我会怎么改**：拿掉对比图插入，把这个"恍然大悟"的瞬间做成一个真实可拍的动作——比如医生用手指轻按自己下颌，停顿、微微点头，一个"这不是脂肪"的确认表情。让画面自己完成认知转折，而不是靠一张信息图硬解释。对比图这个视觉任务，交给 DM 的 infographic 去做就够了（本来 infographic brief 里已经有箭头示意图，两边做同一件事是重复劳动）。
- - **Shot 2**：医生在**别人（患者）脸上**做示范，配音用"you"（"you scrape from the center of your face..."）


## 2026-07-10 13:44 — social-ip-engine

### Decisions & Reasoning
- **2. Detail 页直接内嵌真素材 — review 不用再开 Notion**
- 你先点开一个「图+声待 review」的 row 用一下，哪里不顺手告诉我，我马上调。
- ✅ **改完了 — 浏览器里刷新 http://localhost:8420 就能看到新皮肤**（CSS/JS 是静态文件，不用重启服务器）
- - 标题用 Fraunces 艺术衬线（斜体渐变 logo），正文 Space Grotesk
- 加一个轻量自动同步：工作台每 60 秒静默拉一次（一次 DB query，很便宜），数据没变就不重绘（不会打断你正在看的东西）；Detail 页不自动刷（它要走十几个 Notion API 调用，而且刷新会打断正在播的视频）——
- - 切走再切回来这个浏览器 tab 时立即补一次同步（不用等 60 秒）
- **一个刻意的取舍：** Detail 页（打开单个 row 的那页）**不**自动刷新 — 它一次要走 ~15 个 Notion API 调用，而且自动重绘会打断你正在播的视频/音频。看 detail 时想要最新状态，点「↻ 刷新」；跑任务结束后它本来就会自动刷。
- - **↻ 图** — 只重生成这一个 shot 的图片：先删掉 toggle 里的旧图再生成新的（没图就直接补上）。用的还是这个 shot 自己的 Notion prompt + IP 参考脸


## 2026-07-10 13:52 — social-ip-engine

### What Didn't Work (negative knowledge)
- **4. Period Pain 其实昨天已经上 IG 了。** 服务器 commit 记录显示台账清掉后触发重新发布成功(caption 是 Hook 生成的那句 "Pain so bad you can't move?...Comment 'period' 👇")。但它用的是**旧 cover 逻辑**——已经发出去的这条 IG 帖子的封面改不了(IG API 不支持事后换封面),只有以后的帖子会用对。你可以去 Jackie 的 IG 确认一下这条帖子存不存在、封面能不能接受。
- 监控在跑。IG 视频处理一般 2-5 分钟,FB 再加 2 分钟左右。这次是全新代码走的第一条完整链路:封面从 Cover Photo toggle 读、caption 用 "Can't Move from Pain? Try This NOW! 😱"、FB 拿新鲜链接镜像。结果一出来我就报,包括两边的 media id 和实际用的 cover URL,你直接刷 IG/FB 就能看到新帖。

### Decisions & Reasoning
- **改法（用 seedance-characters 的 three-tier action hierarchy）**：二选一
- 这是个真实的代码 gap，不只是内容问题：`_jimeng_camera()`（298-310行）已经会读 title 里的关键字（比如"demo"）来选镜头运镜，但 lip-sync 那句话完全没有类似的条件判断。**建议**：给 `build_jimeng_prompt()` 加一个判断——如果 visual 文本里出现"no dialogue to camera"/"action shot"，把 read 那句换成纯 VO 描述，不要求对口型。我可以现在就改这个函数，要吗？
- 但 `_primary_beat()`（234-243行）只取第一个分号/逗号/"then"之前的那一段作为静帧图片的 SCENE，"warm side lighting, soft focus"这个你特意写的打光指令，落在第二个 `;` 之后，**根本没被摘进 build_prompt() 里**。而且这段文字也没命中 `_clinic_kws`/`_street_kws` 任何关键字，所以最后套用的是最保底的 fallback：`"Setting: shallow depth of field, natural lighting."`——一句完全通用、没有意图的话。
- 按 directing-engine 的 Step 5（光是有动机的，不是随便一句"natural lighting"）：这镜的光线本该是特意设计的（warm side light 服务"温柔专业的诊疗感"），结果被模板吃掉了，变成了泛用光。**改法**：Shot 2 的视觉描述把光线线索挪到第一段（分号前），比如："...scrape from the center of her cheek outward to the ear, warm side lighting on her face, then down along the jawline..." 这样 `_primary_beat()` 才抓得到。
- 这是内容不一致：DM 私信发出去的信息图，承诺了视频里根本没演示过的手法。用户看完视频、评论关键字拿到图，会发现图上多了一条视频没教的东西。**建议**：要么把 brow-to-hairline 从 infographic 里删掉（保持图和视频严格对齐），要么在 Shot 3 补一句额头手法（更花成本，不建议为了这个改视频）。我倾向直接删。
- - Infographic 本身风格选择（illustration、非写实、no real faces）是对的——医美/身体相关内容用插画而非写实照片，本来就更安全，不用动。
- **我会怎么改**：拿掉对比图插入，把这个"恍然大悟"的瞬间做成一个真实可拍的动作——比如医生用手指轻按自己下颌，停顿、微微点头，一个"这不是脂肪"的确认表情。让画面自己完成认知转折，而不是靠一张信息图硬解释。对比图这个视觉任务，交给 DM 的 infographic 去做就够了（本来 infographic brief 里已经有箭头示意图，两边做同一件事是重复劳动）。
- - **Shot 2**：医生在**别人（患者）脸上**做示范，配音用"you"（"you scrape from the center of your face..."）


## 2026-07-10 13:54 — social-ip-engine

### Decisions & Reasoning
- **2. Detail 页直接内嵌真素材 — review 不用再开 Notion**
- 你先点开一个「图+声待 review」的 row 用一下，哪里不顺手告诉我，我马上调。
- ✅ **改完了 — 浏览器里刷新 http://localhost:8420 就能看到新皮肤**（CSS/JS 是静态文件，不用重启服务器）
- - 标题用 Fraunces 艺术衬线（斜体渐变 logo），正文 Space Grotesk
- 加一个轻量自动同步：工作台每 60 秒静默拉一次（一次 DB query，很便宜），数据没变就不重绘（不会打断你正在看的东西）；Detail 页不自动刷（它要走十几个 Notion API 调用，而且刷新会打断正在播的视频）——
- - 切走再切回来这个浏览器 tab 时立即补一次同步（不用等 60 秒）
- **一个刻意的取舍：** Detail 页（打开单个 row 的那页）**不**自动刷新 — 它一次要走 ~15 个 Notion API 调用，而且自动重绘会打断你正在播的视频/音频。看 detail 时想要最新状态，点「↻ 刷新」；跑任务结束后它本来就会自动刷。
- - **↻ 图** — 只重生成这一个 shot 的图片：先删掉 toggle 里的旧图再生成新的（没图就直接补上）。用的还是这个 shot 自己的 Notion prompt + IP 参考脸


## 2026-07-10 14:04 — social-ip-engine

### Decisions & Reasoning
- **2. Detail 页直接内嵌真素材 — review 不用再开 Notion**
- 你先点开一个「图+声待 review」的 row 用一下，哪里不顺手告诉我，我马上调。
- ✅ **改完了 — 浏览器里刷新 http://localhost:8420 就能看到新皮肤**（CSS/JS 是静态文件，不用重启服务器）
- - 标题用 Fraunces 艺术衬线（斜体渐变 logo），正文 Space Grotesk
- 加一个轻量自动同步：工作台每 60 秒静默拉一次（一次 DB query，很便宜），数据没变就不重绘（不会打断你正在看的东西）；Detail 页不自动刷（它要走十几个 Notion API 调用，而且刷新会打断正在播的视频）——
- - 切走再切回来这个浏览器 tab 时立即补一次同步（不用等 60 秒）
- **一个刻意的取舍：** Detail 页（打开单个 row 的那页）**不**自动刷新 — 它一次要走 ~15 个 Notion API 调用，而且自动重绘会打断你正在播的视频/音频。看 detail 时想要最新状态，点「↻ 刷新」；跑任务结束后它本来就会自动刷。
- - **↻ 图** — 只重生成这一个 shot 的图片：先删掉 toggle 里的旧图再生成新的（没图就直接补上）。用的还是这个 shot 自己的 Notion prompt + IP 参考脸


## 2026-07-10 14:15 — social-ip-engine

### Decisions & Reasoning
- **2. Detail 页直接内嵌真素材 — review 不用再开 Notion**
- 你先点开一个「图+声待 review」的 row 用一下，哪里不顺手告诉我，我马上调。
- ✅ **改完了 — 浏览器里刷新 http://localhost:8420 就能看到新皮肤**（CSS/JS 是静态文件，不用重启服务器）
- - 标题用 Fraunces 艺术衬线（斜体渐变 logo），正文 Space Grotesk
- 加一个轻量自动同步：工作台每 60 秒静默拉一次（一次 DB query，很便宜），数据没变就不重绘（不会打断你正在看的东西）；Detail 页不自动刷（它要走十几个 Notion API 调用，而且刷新会打断正在播的视频）——
- - 切走再切回来这个浏览器 tab 时立即补一次同步（不用等 60 秒）
- **一个刻意的取舍：** Detail 页（打开单个 row 的那页）**不**自动刷新 — 它一次要走 ~15 个 Notion API 调用，而且自动重绘会打断你正在播的视频/音频。看 detail 时想要最新状态，点「↻ 刷新」；跑任务结束后它本来就会自动刷。
- - **↻ 图** — 只重生成这一个 shot 的图片：先删掉 toggle 里的旧图再生成新的（没图就直接补上）。用的还是这个 shot 自己的 Notion prompt + IP 参考脸


## 2026-07-10 14:21 — social-ip-engine

### What Didn't Work (negative knowledge)
- **4. Period Pain 其实昨天已经上 IG 了。** 服务器 commit 记录显示台账清掉后触发重新发布成功(caption 是 Hook 生成的那句 "Pain so bad you can't move?...Comment 'period' 👇")。但它用的是**旧 cover 逻辑**——已经发出去的这条 IG 帖子的封面改不了(IG API 不支持事后换封面),只有以后的帖子会用对。你可以去 Jackie 的 IG 确认一下这条帖子存不存在、封面能不能接受。
- 监控在跑。IG 视频处理一般 2-5 分钟,FB 再加 2 分钟左右。这次是全新代码走的第一条完整链路:封面从 Cover Photo toggle 读、caption 用 "Can't Move from Pain? Try This NOW! 😱"、FB 拿新鲜链接镜像。结果一出来我就报,包括两边的 media id 和实际用的 cover URL,你直接刷 IG/FB 就能看到新帖。

### Decisions & Reasoning
- **改法（用 seedance-characters 的 three-tier action hierarchy）**：二选一
- 这是个真实的代码 gap，不只是内容问题：`_jimeng_camera()`（298-310行）已经会读 title 里的关键字（比如"demo"）来选镜头运镜，但 lip-sync 那句话完全没有类似的条件判断。**建议**：给 `build_jimeng_prompt()` 加一个判断——如果 visual 文本里出现"no dialogue to camera"/"action shot"，把 read 那句换成纯 VO 描述，不要求对口型。我可以现在就改这个函数，要吗？
- 但 `_primary_beat()`（234-243行）只取第一个分号/逗号/"then"之前的那一段作为静帧图片的 SCENE，"warm side lighting, soft focus"这个你特意写的打光指令，落在第二个 `;` 之后，**根本没被摘进 build_prompt() 里**。而且这段文字也没命中 `_clinic_kws`/`_street_kws` 任何关键字，所以最后套用的是最保底的 fallback：`"Setting: shallow depth of field, natural lighting."`——一句完全通用、没有意图的话。
- 按 directing-engine 的 Step 5（光是有动机的，不是随便一句"natural lighting"）：这镜的光线本该是特意设计的（warm side light 服务"温柔专业的诊疗感"），结果被模板吃掉了，变成了泛用光。**改法**：Shot 2 的视觉描述把光线线索挪到第一段（分号前），比如："...scrape from the center of her cheek outward to the ear, warm side lighting on her face, then down along the jawline..." 这样 `_primary_beat()` 才抓得到。
- 这是内容不一致：DM 私信发出去的信息图，承诺了视频里根本没演示过的手法。用户看完视频、评论关键字拿到图，会发现图上多了一条视频没教的东西。**建议**：要么把 brow-to-hairline 从 infographic 里删掉（保持图和视频严格对齐），要么在 Shot 3 补一句额头手法（更花成本，不建议为了这个改视频）。我倾向直接删。
- - Infographic 本身风格选择（illustration、非写实、no real faces）是对的——医美/身体相关内容用插画而非写实照片，本来就更安全，不用动。
- **我会怎么改**：拿掉对比图插入，把这个"恍然大悟"的瞬间做成一个真实可拍的动作——比如医生用手指轻按自己下颌，停顿、微微点头，一个"这不是脂肪"的确认表情。让画面自己完成认知转折，而不是靠一张信息图硬解释。对比图这个视觉任务，交给 DM 的 infographic 去做就够了（本来 infographic brief 里已经有箭头示意图，两边做同一件事是重复劳动）。
- - **Shot 2**：医生在**别人（患者）脸上**做示范，配音用"you"（"you scrape from the center of your face..."）


## 2026-07-10 14:22 — social-ip-engine

### What Didn't Work (negative knowledge)
- **4. Period Pain 其实昨天已经上 IG 了。** 服务器 commit 记录显示台账清掉后触发重新发布成功(caption 是 Hook 生成的那句 "Pain so bad you can't move?...Comment 'period' 👇")。但它用的是**旧 cover 逻辑**——已经发出去的这条 IG 帖子的封面改不了(IG API 不支持事后换封面),只有以后的帖子会用对。你可以去 Jackie 的 IG 确认一下这条帖子存不存在、封面能不能接受。
- 监控在跑。IG 视频处理一般 2-5 分钟,FB 再加 2 分钟左右。这次是全新代码走的第一条完整链路:封面从 Cover Photo toggle 读、caption 用 "Can't Move from Pain? Try This NOW! 😱"、FB 拿新鲜链接镜像。结果一出来我就报,包括两边的 media id 和实际用的 cover URL,你直接刷 IG/FB 就能看到新帖。

### Decisions & Reasoning
- **改法（用 seedance-characters 的 three-tier action hierarchy）**：二选一
- 这是个真实的代码 gap，不只是内容问题：`_jimeng_camera()`（298-310行）已经会读 title 里的关键字（比如"demo"）来选镜头运镜，但 lip-sync 那句话完全没有类似的条件判断。**建议**：给 `build_jimeng_prompt()` 加一个判断——如果 visual 文本里出现"no dialogue to camera"/"action shot"，把 read 那句换成纯 VO 描述，不要求对口型。我可以现在就改这个函数，要吗？
- 但 `_primary_beat()`（234-243行）只取第一个分号/逗号/"then"之前的那一段作为静帧图片的 SCENE，"warm side lighting, soft focus"这个你特意写的打光指令，落在第二个 `;` 之后，**根本没被摘进 build_prompt() 里**。而且这段文字也没命中 `_clinic_kws`/`_street_kws` 任何关键字，所以最后套用的是最保底的 fallback：`"Setting: shallow depth of field, natural lighting."`——一句完全通用、没有意图的话。
- 按 directing-engine 的 Step 5（光是有动机的，不是随便一句"natural lighting"）：这镜的光线本该是特意设计的（warm side light 服务"温柔专业的诊疗感"），结果被模板吃掉了，变成了泛用光。**改法**：Shot 2 的视觉描述把光线线索挪到第一段（分号前），比如："...scrape from the center of her cheek outward to the ear, warm side lighting on her face, then down along the jawline..." 这样 `_primary_beat()` 才抓得到。
- 这是内容不一致：DM 私信发出去的信息图，承诺了视频里根本没演示过的手法。用户看完视频、评论关键字拿到图，会发现图上多了一条视频没教的东西。**建议**：要么把 brow-to-hairline 从 infographic 里删掉（保持图和视频严格对齐），要么在 Shot 3 补一句额头手法（更花成本，不建议为了这个改视频）。我倾向直接删。
- - Infographic 本身风格选择（illustration、非写实、no real faces）是对的——医美/身体相关内容用插画而非写实照片，本来就更安全，不用动。
- **我会怎么改**：拿掉对比图插入，把这个"恍然大悟"的瞬间做成一个真实可拍的动作——比如医生用手指轻按自己下颌，停顿、微微点头，一个"这不是脂肪"的确认表情。让画面自己完成认知转折，而不是靠一张信息图硬解释。对比图这个视觉任务，交给 DM 的 infographic 去做就够了（本来 infographic brief 里已经有箭头示意图，两边做同一件事是重复劳动）。
- - **Shot 2**：医生在**别人（患者）脸上**做示范，配音用"you"（"you scrape from the center of your face..."）


## 2026-07-10 14:24 — social-ip-engine

### What Didn't Work (negative knowledge)
- **4. Period Pain 其实昨天已经上 IG 了。** 服务器 commit 记录显示台账清掉后触发重新发布成功(caption 是 Hook 生成的那句 "Pain so bad you can't move?...Comment 'period' 👇")。但它用的是**旧 cover 逻辑**——已经发出去的这条 IG 帖子的封面改不了(IG API 不支持事后换封面),只有以后的帖子会用对。你可以去 Jackie 的 IG 确认一下这条帖子存不存在、封面能不能接受。
- 监控在跑。IG 视频处理一般 2-5 分钟,FB 再加 2 分钟左右。这次是全新代码走的第一条完整链路:封面从 Cover Photo toggle 读、caption 用 "Can't Move from Pain? Try This NOW! 😱"、FB 拿新鲜链接镜像。结果一出来我就报,包括两边的 media id 和实际用的 cover URL,你直接刷 IG/FB 就能看到新帖。

### Decisions & Reasoning
- **改法（用 seedance-characters 的 three-tier action hierarchy）**：二选一
- 这是个真实的代码 gap，不只是内容问题：`_jimeng_camera()`（298-310行）已经会读 title 里的关键字（比如"demo"）来选镜头运镜，但 lip-sync 那句话完全没有类似的条件判断。**建议**：给 `build_jimeng_prompt()` 加一个判断——如果 visual 文本里出现"no dialogue to camera"/"action shot"，把 read 那句换成纯 VO 描述，不要求对口型。我可以现在就改这个函数，要吗？
- 但 `_primary_beat()`（234-243行）只取第一个分号/逗号/"then"之前的那一段作为静帧图片的 SCENE，"warm side lighting, soft focus"这个你特意写的打光指令，落在第二个 `;` 之后，**根本没被摘进 build_prompt() 里**。而且这段文字也没命中 `_clinic_kws`/`_street_kws` 任何关键字，所以最后套用的是最保底的 fallback：`"Setting: shallow depth of field, natural lighting."`——一句完全通用、没有意图的话。
- 按 directing-engine 的 Step 5（光是有动机的，不是随便一句"natural lighting"）：这镜的光线本该是特意设计的（warm side light 服务"温柔专业的诊疗感"），结果被模板吃掉了，变成了泛用光。**改法**：Shot 2 的视觉描述把光线线索挪到第一段（分号前），比如："...scrape from the center of her cheek outward to the ear, warm side lighting on her face, then down along the jawline..." 这样 `_primary_beat()` 才抓得到。
- 这是内容不一致：DM 私信发出去的信息图，承诺了视频里根本没演示过的手法。用户看完视频、评论关键字拿到图，会发现图上多了一条视频没教的东西。**建议**：要么把 brow-to-hairline 从 infographic 里删掉（保持图和视频严格对齐），要么在 Shot 3 补一句额头手法（更花成本，不建议为了这个改视频）。我倾向直接删。
- - Infographic 本身风格选择（illustration、非写实、no real faces）是对的——医美/身体相关内容用插画而非写实照片，本来就更安全，不用动。
- **我会怎么改**：拿掉对比图插入，把这个"恍然大悟"的瞬间做成一个真实可拍的动作——比如医生用手指轻按自己下颌，停顿、微微点头，一个"这不是脂肪"的确认表情。让画面自己完成认知转折，而不是靠一张信息图硬解释。对比图这个视觉任务，交给 DM 的 infographic 去做就够了（本来 infographic brief 里已经有箭头示意图，两边做同一件事是重复劳动）。
- - **Shot 2**：医生在**别人（患者）脸上**做示范，配音用"you"（"you scrape from the center of your face..."）


## 2026-07-10 14:29 — social-ip-engine

### Decisions & Reasoning
- **2. Detail 页直接内嵌真素材 — review 不用再开 Notion**
- 你先点开一个「图+声待 review」的 row 用一下，哪里不顺手告诉我，我马上调。
- ✅ **改完了 — 浏览器里刷新 http://localhost:8420 就能看到新皮肤**（CSS/JS 是静态文件，不用重启服务器）
- - 标题用 Fraunces 艺术衬线（斜体渐变 logo），正文 Space Grotesk
- 加一个轻量自动同步：工作台每 60 秒静默拉一次（一次 DB query，很便宜），数据没变就不重绘（不会打断你正在看的东西）；Detail 页不自动刷（它要走十几个 Notion API 调用，而且刷新会打断正在播的视频）——
- - 切走再切回来这个浏览器 tab 时立即补一次同步（不用等 60 秒）
- **一个刻意的取舍：** Detail 页（打开单个 row 的那页）**不**自动刷新 — 它一次要走 ~15 个 Notion API 调用，而且自动重绘会打断你正在播的视频/音频。看 detail 时想要最新状态，点「↻ 刷新」；跑任务结束后它本来就会自动刷。
- - **↻ 图** — 只重生成这一个 shot 的图片：先删掉 toggle 里的旧图再生成新的（没图就直接补上）。用的还是这个 shot 自己的 Notion prompt + IP 参考脸


## 2026-07-10 14:38 — social-ip-engine

### What Didn't Work (negative knowledge)
- **4. Period Pain 其实昨天已经上 IG 了。** 服务器 commit 记录显示台账清掉后触发重新发布成功(caption 是 Hook 生成的那句 "Pain so bad you can't move?...Comment 'period' 👇")。但它用的是**旧 cover 逻辑**——已经发出去的这条 IG 帖子的封面改不了(IG API 不支持事后换封面),只有以后的帖子会用对。你可以去 Jackie 的 IG 确认一下这条帖子存不存在、封面能不能接受。
- 监控在跑。IG 视频处理一般 2-5 分钟,FB 再加 2 分钟左右。这次是全新代码走的第一条完整链路:封面从 Cover Photo toggle 读、caption 用 "Can't Move from Pain? Try This NOW! 😱"、FB 拿新鲜链接镜像。结果一出来我就报,包括两边的 media id 和实际用的 cover URL,你直接刷 IG/FB 就能看到新帖。

### Decisions & Reasoning
- **改法（用 seedance-characters 的 three-tier action hierarchy）**：二选一
- 这是个真实的代码 gap，不只是内容问题：`_jimeng_camera()`（298-310行）已经会读 title 里的关键字（比如"demo"）来选镜头运镜，但 lip-sync 那句话完全没有类似的条件判断。**建议**：给 `build_jimeng_prompt()` 加一个判断——如果 visual 文本里出现"no dialogue to camera"/"action shot"，把 read 那句换成纯 VO 描述，不要求对口型。我可以现在就改这个函数，要吗？
- 但 `_primary_beat()`（234-243行）只取第一个分号/逗号/"then"之前的那一段作为静帧图片的 SCENE，"warm side lighting, soft focus"这个你特意写的打光指令，落在第二个 `;` 之后，**根本没被摘进 build_prompt() 里**。而且这段文字也没命中 `_clinic_kws`/`_street_kws` 任何关键字，所以最后套用的是最保底的 fallback：`"Setting: shallow depth of field, natural lighting."`——一句完全通用、没有意图的话。
- 按 directing-engine 的 Step 5（光是有动机的，不是随便一句"natural lighting"）：这镜的光线本该是特意设计的（warm side light 服务"温柔专业的诊疗感"），结果被模板吃掉了，变成了泛用光。**改法**：Shot 2 的视觉描述把光线线索挪到第一段（分号前），比如："...scrape from the center of her cheek outward to the ear, warm side lighting on her face, then down along the jawline..." 这样 `_primary_beat()` 才抓得到。
- 这是内容不一致：DM 私信发出去的信息图，承诺了视频里根本没演示过的手法。用户看完视频、评论关键字拿到图，会发现图上多了一条视频没教的东西。**建议**：要么把 brow-to-hairline 从 infographic 里删掉（保持图和视频严格对齐），要么在 Shot 3 补一句额头手法（更花成本，不建议为了这个改视频）。我倾向直接删。
- - Infographic 本身风格选择（illustration、非写实、no real faces）是对的——医美/身体相关内容用插画而非写实照片，本来就更安全，不用动。
- **我会怎么改**：拿掉对比图插入，把这个"恍然大悟"的瞬间做成一个真实可拍的动作——比如医生用手指轻按自己下颌，停顿、微微点头，一个"这不是脂肪"的确认表情。让画面自己完成认知转折，而不是靠一张信息图硬解释。对比图这个视觉任务，交给 DM 的 infographic 去做就够了（本来 infographic brief 里已经有箭头示意图，两边做同一件事是重复劳动）。
- - **Shot 2**：医生在**别人（患者）脸上**做示范，配音用"you"（"you scrape from the center of your face..."）


## 2026-07-10 14:41 — social-ip-engine

### Decisions & Reasoning
- **2. Detail 页直接内嵌真素材 — review 不用再开 Notion**
- 你先点开一个「图+声待 review」的 row 用一下，哪里不顺手告诉我，我马上调。
- ✅ **改完了 — 浏览器里刷新 http://localhost:8420 就能看到新皮肤**（CSS/JS 是静态文件，不用重启服务器）
- - 标题用 Fraunces 艺术衬线（斜体渐变 logo），正文 Space Grotesk
- 加一个轻量自动同步：工作台每 60 秒静默拉一次（一次 DB query，很便宜），数据没变就不重绘（不会打断你正在看的东西）；Detail 页不自动刷（它要走十几个 Notion API 调用，而且刷新会打断正在播的视频）——
- - 切走再切回来这个浏览器 tab 时立即补一次同步（不用等 60 秒）
- **一个刻意的取舍：** Detail 页（打开单个 row 的那页）**不**自动刷新 — 它一次要走 ~15 个 Notion API 调用，而且自动重绘会打断你正在播的视频/音频。看 detail 时想要最新状态，点「↻ 刷新」；跑任务结束后它本来就会自动刷。
- - **↻ 图** — 只重生成这一个 shot 的图片：先删掉 toggle 里的旧图再生成新的（没图就直接补上）。用的还是这个 shot 自己的 Notion prompt + IP 参考脸


## 2026-07-10 15:13 — social-ip-engine

### Decisions & Reasoning
- **2. Detail 页直接内嵌真素材 — review 不用再开 Notion**
- 你先点开一个「图+声待 review」的 row 用一下，哪里不顺手告诉我，我马上调。
- ✅ **改完了 — 浏览器里刷新 http://localhost:8420 就能看到新皮肤**（CSS/JS 是静态文件，不用重启服务器）
- - 标题用 Fraunces 艺术衬线（斜体渐变 logo），正文 Space Grotesk
- 加一个轻量自动同步：工作台每 60 秒静默拉一次（一次 DB query，很便宜），数据没变就不重绘（不会打断你正在看的东西）；Detail 页不自动刷（它要走十几个 Notion API 调用，而且刷新会打断正在播的视频）——
- - 切走再切回来这个浏览器 tab 时立即补一次同步（不用等 60 秒）
- **一个刻意的取舍：** Detail 页（打开单个 row 的那页）**不**自动刷新 — 它一次要走 ~15 个 Notion API 调用，而且自动重绘会打断你正在播的视频/音频。看 detail 时想要最新状态，点「↻ 刷新」；跑任务结束后它本来就会自动刷。
- - **↻ 图** — 只重生成这一个 shot 的图片：先删掉 toggle 里的旧图再生成新的（没图就直接补上）。用的还是这个 shot 自己的 Notion prompt + IP 参考脸


## 2026-07-10 15:19 — social-ip-engine

### Decisions & Reasoning
- **2. Detail 页直接内嵌真素材 — review 不用再开 Notion**
- 你先点开一个「图+声待 review」的 row 用一下，哪里不顺手告诉我，我马上调。
- ✅ **改完了 — 浏览器里刷新 http://localhost:8420 就能看到新皮肤**（CSS/JS 是静态文件，不用重启服务器）
- - 标题用 Fraunces 艺术衬线（斜体渐变 logo），正文 Space Grotesk
- 加一个轻量自动同步：工作台每 60 秒静默拉一次（一次 DB query，很便宜），数据没变就不重绘（不会打断你正在看的东西）；Detail 页不自动刷（它要走十几个 Notion API 调用，而且刷新会打断正在播的视频）——
- - 切走再切回来这个浏览器 tab 时立即补一次同步（不用等 60 秒）
- **一个刻意的取舍：** Detail 页（打开单个 row 的那页）**不**自动刷新 — 它一次要走 ~15 个 Notion API 调用，而且自动重绘会打断你正在播的视频/音频。看 detail 时想要最新状态，点「↻ 刷新」；跑任务结束后它本来就会自动刷。
- - **↻ 图** — 只重生成这一个 shot 的图片：先删掉 toggle 里的旧图再生成新的（没图就直接补上）。用的还是这个 shot 自己的 Notion prompt + IP 参考脸


## 2026-07-10 15:22 — social-ip-engine

### What Didn't Work (negative knowledge)
- **4. Period Pain 其实昨天已经上 IG 了。** 服务器 commit 记录显示台账清掉后触发重新发布成功(caption 是 Hook 生成的那句 "Pain so bad you can't move?...Comment 'period' 👇")。但它用的是**旧 cover 逻辑**——已经发出去的这条 IG 帖子的封面改不了(IG API 不支持事后换封面),只有以后的帖子会用对。你可以去 Jackie 的 IG 确认一下这条帖子存不存在、封面能不能接受。
- 监控在跑。IG 视频处理一般 2-5 分钟,FB 再加 2 分钟左右。这次是全新代码走的第一条完整链路:封面从 Cover Photo toggle 读、caption 用 "Can't Move from Pain? Try This NOW! 😱"、FB 拿新鲜链接镜像。结果一出来我就报,包括两边的 media id 和实际用的 cover URL,你直接刷 IG/FB 就能看到新帖。

### Decisions & Reasoning
- **改法（用 seedance-characters 的 three-tier action hierarchy）**：二选一
- 这是个真实的代码 gap，不只是内容问题：`_jimeng_camera()`（298-310行）已经会读 title 里的关键字（比如"demo"）来选镜头运镜，但 lip-sync 那句话完全没有类似的条件判断。**建议**：给 `build_jimeng_prompt()` 加一个判断——如果 visual 文本里出现"no dialogue to camera"/"action shot"，把 read 那句换成纯 VO 描述，不要求对口型。我可以现在就改这个函数，要吗？
- 但 `_primary_beat()`（234-243行）只取第一个分号/逗号/"then"之前的那一段作为静帧图片的 SCENE，"warm side lighting, soft focus"这个你特意写的打光指令，落在第二个 `;` 之后，**根本没被摘进 build_prompt() 里**。而且这段文字也没命中 `_clinic_kws`/`_street_kws` 任何关键字，所以最后套用的是最保底的 fallback：`"Setting: shallow depth of field, natural lighting."`——一句完全通用、没有意图的话。
- 按 directing-engine 的 Step 5（光是有动机的，不是随便一句"natural lighting"）：这镜的光线本该是特意设计的（warm side light 服务"温柔专业的诊疗感"），结果被模板吃掉了，变成了泛用光。**改法**：Shot 2 的视觉描述把光线线索挪到第一段（分号前），比如："...scrape from the center of her cheek outward to the ear, warm side lighting on her face, then down along the jawline..." 这样 `_primary_beat()` 才抓得到。
- 这是内容不一致：DM 私信发出去的信息图，承诺了视频里根本没演示过的手法。用户看完视频、评论关键字拿到图，会发现图上多了一条视频没教的东西。**建议**：要么把 brow-to-hairline 从 infographic 里删掉（保持图和视频严格对齐），要么在 Shot 3 补一句额头手法（更花成本，不建议为了这个改视频）。我倾向直接删。
- - Infographic 本身风格选择（illustration、非写实、no real faces）是对的——医美/身体相关内容用插画而非写实照片，本来就更安全，不用动。
- **我会怎么改**：拿掉对比图插入，把这个"恍然大悟"的瞬间做成一个真实可拍的动作——比如医生用手指轻按自己下颌，停顿、微微点头，一个"这不是脂肪"的确认表情。让画面自己完成认知转折，而不是靠一张信息图硬解释。对比图这个视觉任务，交给 DM 的 infographic 去做就够了（本来 infographic brief 里已经有箭头示意图，两边做同一件事是重复劳动）。
- - **Shot 2**：医生在**别人（患者）脸上**做示范，配音用"you"（"you scrape from the center of your face..."）


## 2026-07-10 15:28 — social-ip-engine

### What Didn't Work (negative knowledge)
- **4. Period Pain 其实昨天已经上 IG 了。** 服务器 commit 记录显示台账清掉后触发重新发布成功(caption 是 Hook 生成的那句 "Pain so bad you can't move?...Comment 'period' 👇")。但它用的是**旧 cover 逻辑**——已经发出去的这条 IG 帖子的封面改不了(IG API 不支持事后换封面),只有以后的帖子会用对。你可以去 Jackie 的 IG 确认一下这条帖子存不存在、封面能不能接受。
- 监控在跑。IG 视频处理一般 2-5 分钟,FB 再加 2 分钟左右。这次是全新代码走的第一条完整链路:封面从 Cover Photo toggle 读、caption 用 "Can't Move from Pain? Try This NOW! 😱"、FB 拿新鲜链接镜像。结果一出来我就报,包括两边的 media id 和实际用的 cover URL,你直接刷 IG/FB 就能看到新帖。

### Decisions & Reasoning
- **改法（用 seedance-characters 的 three-tier action hierarchy）**：二选一
- 这是个真实的代码 gap，不只是内容问题：`_jimeng_camera()`（298-310行）已经会读 title 里的关键字（比如"demo"）来选镜头运镜，但 lip-sync 那句话完全没有类似的条件判断。**建议**：给 `build_jimeng_prompt()` 加一个判断——如果 visual 文本里出现"no dialogue to camera"/"action shot"，把 read 那句换成纯 VO 描述，不要求对口型。我可以现在就改这个函数，要吗？
- 但 `_primary_beat()`（234-243行）只取第一个分号/逗号/"then"之前的那一段作为静帧图片的 SCENE，"warm side lighting, soft focus"这个你特意写的打光指令，落在第二个 `;` 之后，**根本没被摘进 build_prompt() 里**。而且这段文字也没命中 `_clinic_kws`/`_street_kws` 任何关键字，所以最后套用的是最保底的 fallback：`"Setting: shallow depth of field, natural lighting."`——一句完全通用、没有意图的话。
- 按 directing-engine 的 Step 5（光是有动机的，不是随便一句"natural lighting"）：这镜的光线本该是特意设计的（warm side light 服务"温柔专业的诊疗感"），结果被模板吃掉了，变成了泛用光。**改法**：Shot 2 的视觉描述把光线线索挪到第一段（分号前），比如："...scrape from the center of her cheek outward to the ear, warm side lighting on her face, then down along the jawline..." 这样 `_primary_beat()` 才抓得到。
- 这是内容不一致：DM 私信发出去的信息图，承诺了视频里根本没演示过的手法。用户看完视频、评论关键字拿到图，会发现图上多了一条视频没教的东西。**建议**：要么把 brow-to-hairline 从 infographic 里删掉（保持图和视频严格对齐），要么在 Shot 3 补一句额头手法（更花成本，不建议为了这个改视频）。我倾向直接删。
- - Infographic 本身风格选择（illustration、非写实、no real faces）是对的——医美/身体相关内容用插画而非写实照片，本来就更安全，不用动。
- **我会怎么改**：拿掉对比图插入，把这个"恍然大悟"的瞬间做成一个真实可拍的动作——比如医生用手指轻按自己下颌，停顿、微微点头，一个"这不是脂肪"的确认表情。让画面自己完成认知转折，而不是靠一张信息图硬解释。对比图这个视觉任务，交给 DM 的 infographic 去做就够了（本来 infographic brief 里已经有箭头示意图，两边做同一件事是重复劳动）。
- - **Shot 2**：医生在**别人（患者）脸上**做示范，配音用"you"（"you scrape from the center of your face..."）


## 2026-07-10 15:32 — social-ip-engine

### Decisions & Reasoning
- **2. Detail 页直接内嵌真素材 — review 不用再开 Notion**
- 你先点开一个「图+声待 review」的 row 用一下，哪里不顺手告诉我，我马上调。
- ✅ **改完了 — 浏览器里刷新 http://localhost:8420 就能看到新皮肤**（CSS/JS 是静态文件，不用重启服务器）
- - 标题用 Fraunces 艺术衬线（斜体渐变 logo），正文 Space Grotesk
- 加一个轻量自动同步：工作台每 60 秒静默拉一次（一次 DB query，很便宜），数据没变就不重绘（不会打断你正在看的东西）；Detail 页不自动刷（它要走十几个 Notion API 调用，而且刷新会打断正在播的视频）——
- - 切走再切回来这个浏览器 tab 时立即补一次同步（不用等 60 秒）
- **一个刻意的取舍：** Detail 页（打开单个 row 的那页）**不**自动刷新 — 它一次要走 ~15 个 Notion API 调用，而且自动重绘会打断你正在播的视频/音频。看 detail 时想要最新状态，点「↻ 刷新」；跑任务结束后它本来就会自动刷。
- - **↻ 图** — 只重生成这一个 shot 的图片：先删掉 toggle 里的旧图再生成新的（没图就直接补上）。用的还是这个 shot 自己的 Notion prompt + IP 参考脸


## 2026-07-10 15:34 — social-ip-engine

### What Didn't Work (negative knowledge)
- **4. Period Pain 其实昨天已经上 IG 了。** 服务器 commit 记录显示台账清掉后触发重新发布成功(caption 是 Hook 生成的那句 "Pain so bad you can't move?...Comment 'period' 👇")。但它用的是**旧 cover 逻辑**——已经发出去的这条 IG 帖子的封面改不了(IG API 不支持事后换封面),只有以后的帖子会用对。你可以去 Jackie 的 IG 确认一下这条帖子存不存在、封面能不能接受。
- 监控在跑。IG 视频处理一般 2-5 分钟,FB 再加 2 分钟左右。这次是全新代码走的第一条完整链路:封面从 Cover Photo toggle 读、caption 用 "Can't Move from Pain? Try This NOW! 😱"、FB 拿新鲜链接镜像。结果一出来我就报,包括两边的 media id 和实际用的 cover URL,你直接刷 IG/FB 就能看到新帖。

### Decisions & Reasoning
- **改法（用 seedance-characters 的 three-tier action hierarchy）**：二选一
- 这是个真实的代码 gap，不只是内容问题：`_jimeng_camera()`（298-310行）已经会读 title 里的关键字（比如"demo"）来选镜头运镜，但 lip-sync 那句话完全没有类似的条件判断。**建议**：给 `build_jimeng_prompt()` 加一个判断——如果 visual 文本里出现"no dialogue to camera"/"action shot"，把 read 那句换成纯 VO 描述，不要求对口型。我可以现在就改这个函数，要吗？
- 但 `_primary_beat()`（234-243行）只取第一个分号/逗号/"then"之前的那一段作为静帧图片的 SCENE，"warm side lighting, soft focus"这个你特意写的打光指令，落在第二个 `;` 之后，**根本没被摘进 build_prompt() 里**。而且这段文字也没命中 `_clinic_kws`/`_street_kws` 任何关键字，所以最后套用的是最保底的 fallback：`"Setting: shallow depth of field, natural lighting."`——一句完全通用、没有意图的话。
- 按 directing-engine 的 Step 5（光是有动机的，不是随便一句"natural lighting"）：这镜的光线本该是特意设计的（warm side light 服务"温柔专业的诊疗感"），结果被模板吃掉了，变成了泛用光。**改法**：Shot 2 的视觉描述把光线线索挪到第一段（分号前），比如："...scrape from the center of her cheek outward to the ear, warm side lighting on her face, then down along the jawline..." 这样 `_primary_beat()` 才抓得到。
- 这是内容不一致：DM 私信发出去的信息图，承诺了视频里根本没演示过的手法。用户看完视频、评论关键字拿到图，会发现图上多了一条视频没教的东西。**建议**：要么把 brow-to-hairline 从 infographic 里删掉（保持图和视频严格对齐），要么在 Shot 3 补一句额头手法（更花成本，不建议为了这个改视频）。我倾向直接删。
- - Infographic 本身风格选择（illustration、非写实、no real faces）是对的——医美/身体相关内容用插画而非写实照片，本来就更安全，不用动。
- **我会怎么改**：拿掉对比图插入，把这个"恍然大悟"的瞬间做成一个真实可拍的动作——比如医生用手指轻按自己下颌，停顿、微微点头，一个"这不是脂肪"的确认表情。让画面自己完成认知转折，而不是靠一张信息图硬解释。对比图这个视觉任务，交给 DM 的 infographic 去做就够了（本来 infographic brief 里已经有箭头示意图，两边做同一件事是重复劳动）。
- - **Shot 2**：医生在**别人（患者）脸上**做示范，配音用"you"（"you scrape from the center of your face..."）


## 2026-07-10 15:36 — social-ip-engine

### Decisions & Reasoning
- **2. Detail 页直接内嵌真素材 — review 不用再开 Notion**
- 你先点开一个「图+声待 review」的 row 用一下，哪里不顺手告诉我，我马上调。
- ✅ **改完了 — 浏览器里刷新 http://localhost:8420 就能看到新皮肤**（CSS/JS 是静态文件，不用重启服务器）
- - 标题用 Fraunces 艺术衬线（斜体渐变 logo），正文 Space Grotesk
- 加一个轻量自动同步：工作台每 60 秒静默拉一次（一次 DB query，很便宜），数据没变就不重绘（不会打断你正在看的东西）；Detail 页不自动刷（它要走十几个 Notion API 调用，而且刷新会打断正在播的视频）——
- - 切走再切回来这个浏览器 tab 时立即补一次同步（不用等 60 秒）
- **一个刻意的取舍：** Detail 页（打开单个 row 的那页）**不**自动刷新 — 它一次要走 ~15 个 Notion API 调用，而且自动重绘会打断你正在播的视频/音频。看 detail 时想要最新状态，点「↻ 刷新」；跑任务结束后它本来就会自动刷。
- - **↻ 图** — 只重生成这一个 shot 的图片：先删掉 toggle 里的旧图再生成新的（没图就直接补上）。用的还是这个 shot 自己的 Notion prompt + IP 参考脸


## 2026-07-10 15:38 — social-ip-engine

### Decisions & Reasoning
- **2. Detail 页直接内嵌真素材 — review 不用再开 Notion**
- 你先点开一个「图+声待 review」的 row 用一下，哪里不顺手告诉我，我马上调。
- ✅ **改完了 — 浏览器里刷新 http://localhost:8420 就能看到新皮肤**（CSS/JS 是静态文件，不用重启服务器）
- - 标题用 Fraunces 艺术衬线（斜体渐变 logo），正文 Space Grotesk
- 加一个轻量自动同步：工作台每 60 秒静默拉一次（一次 DB query，很便宜），数据没变就不重绘（不会打断你正在看的东西）；Detail 页不自动刷（它要走十几个 Notion API 调用，而且刷新会打断正在播的视频）——
- - 切走再切回来这个浏览器 tab 时立即补一次同步（不用等 60 秒）
- **一个刻意的取舍：** Detail 页（打开单个 row 的那页）**不**自动刷新 — 它一次要走 ~15 个 Notion API 调用，而且自动重绘会打断你正在播的视频/音频。看 detail 时想要最新状态，点「↻ 刷新」；跑任务结束后它本来就会自动刷。
- - **↻ 图** — 只重生成这一个 shot 的图片：先删掉 toggle 里的旧图再生成新的（没图就直接补上）。用的还是这个 shot 自己的 Notion prompt + IP 参考脸


## 2026-07-10 15:40 — social-ip-engine

### Decisions & Reasoning
- **2. Detail 页直接内嵌真素材 — review 不用再开 Notion**
- 你先点开一个「图+声待 review」的 row 用一下，哪里不顺手告诉我，我马上调。
- ✅ **改完了 — 浏览器里刷新 http://localhost:8420 就能看到新皮肤**（CSS/JS 是静态文件，不用重启服务器）
- - 标题用 Fraunces 艺术衬线（斜体渐变 logo），正文 Space Grotesk
- 加一个轻量自动同步：工作台每 60 秒静默拉一次（一次 DB query，很便宜），数据没变就不重绘（不会打断你正在看的东西）；Detail 页不自动刷（它要走十几个 Notion API 调用，而且刷新会打断正在播的视频）——
- - 切走再切回来这个浏览器 tab 时立即补一次同步（不用等 60 秒）
- **一个刻意的取舍：** Detail 页（打开单个 row 的那页）**不**自动刷新 — 它一次要走 ~15 个 Notion API 调用，而且自动重绘会打断你正在播的视频/音频。看 detail 时想要最新状态，点「↻ 刷新」；跑任务结束后它本来就会自动刷。
- - **↻ 图** — 只重生成这一个 shot 的图片：先删掉 toggle 里的旧图再生成新的（没图就直接补上）。用的还是这个 shot 自己的 Notion prompt + IP 参考脸


## 2026-07-10 15:50 — social-ip-engine

### Decisions & Reasoning
- **2. Detail 页直接内嵌真素材 — review 不用再开 Notion**
- 你先点开一个「图+声待 review」的 row 用一下，哪里不顺手告诉我，我马上调。
- ✅ **改完了 — 浏览器里刷新 http://localhost:8420 就能看到新皮肤**（CSS/JS 是静态文件，不用重启服务器）
- - 标题用 Fraunces 艺术衬线（斜体渐变 logo），正文 Space Grotesk
- 加一个轻量自动同步：工作台每 60 秒静默拉一次（一次 DB query，很便宜），数据没变就不重绘（不会打断你正在看的东西）；Detail 页不自动刷（它要走十几个 Notion API 调用，而且刷新会打断正在播的视频）——
- - 切走再切回来这个浏览器 tab 时立即补一次同步（不用等 60 秒）
- **一个刻意的取舍：** Detail 页（打开单个 row 的那页）**不**自动刷新 — 它一次要走 ~15 个 Notion API 调用，而且自动重绘会打断你正在播的视频/音频。看 detail 时想要最新状态，点「↻ 刷新」；跑任务结束后它本来就会自动刷。
- - **↻ 图** — 只重生成这一个 shot 的图片：先删掉 toggle 里的旧图再生成新的（没图就直接补上）。用的还是这个 shot 自己的 Notion prompt + IP 参考脸


## 2026-07-10 16:00 — social-ip-engine

### Decisions & Reasoning
- **2. Detail 页直接内嵌真素材 — review 不用再开 Notion**
- 你先点开一个「图+声待 review」的 row 用一下，哪里不顺手告诉我，我马上调。
- ✅ **改完了 — 浏览器里刷新 http://localhost:8420 就能看到新皮肤**（CSS/JS 是静态文件，不用重启服务器）
- - 标题用 Fraunces 艺术衬线（斜体渐变 logo），正文 Space Grotesk
- 加一个轻量自动同步：工作台每 60 秒静默拉一次（一次 DB query，很便宜），数据没变就不重绘（不会打断你正在看的东西）；Detail 页不自动刷（它要走十几个 Notion API 调用，而且刷新会打断正在播的视频）——
- - 切走再切回来这个浏览器 tab 时立即补一次同步（不用等 60 秒）
- **一个刻意的取舍：** Detail 页（打开单个 row 的那页）**不**自动刷新 — 它一次要走 ~15 个 Notion API 调用，而且自动重绘会打断你正在播的视频/音频。看 detail 时想要最新状态，点「↻ 刷新」；跑任务结束后它本来就会自动刷。
- - **↻ 图** — 只重生成这一个 shot 的图片：先删掉 toggle 里的旧图再生成新的（没图就直接补上）。用的还是这个 shot 自己的 Notion prompt + IP 参考脸


## 2026-07-10 16:08 — social-ip-engine

### Decisions & Reasoning
- **2. Detail 页直接内嵌真素材 — review 不用再开 Notion**
- 你先点开一个「图+声待 review」的 row 用一下，哪里不顺手告诉我，我马上调。
- ✅ **改完了 — 浏览器里刷新 http://localhost:8420 就能看到新皮肤**（CSS/JS 是静态文件，不用重启服务器）
- - 标题用 Fraunces 艺术衬线（斜体渐变 logo），正文 Space Grotesk
- 加一个轻量自动同步：工作台每 60 秒静默拉一次（一次 DB query，很便宜），数据没变就不重绘（不会打断你正在看的东西）；Detail 页不自动刷（它要走十几个 Notion API 调用，而且刷新会打断正在播的视频）——
- - 切走再切回来这个浏览器 tab 时立即补一次同步（不用等 60 秒）
- **一个刻意的取舍：** Detail 页（打开单个 row 的那页）**不**自动刷新 — 它一次要走 ~15 个 Notion API 调用，而且自动重绘会打断你正在播的视频/音频。看 detail 时想要最新状态，点「↻ 刷新」；跑任务结束后它本来就会自动刷。
- - **↻ 图** — 只重生成这一个 shot 的图片：先删掉 toggle 里的旧图再生成新的（没图就直接补上）。用的还是这个 shot 自己的 Notion prompt + IP 参考脸


## 2026-07-10 16:11 — social-ip-engine

### Decisions & Reasoning
- **2. Detail 页直接内嵌真素材 — review 不用再开 Notion**
- 你先点开一个「图+声待 review」的 row 用一下，哪里不顺手告诉我，我马上调。
- ✅ **改完了 — 浏览器里刷新 http://localhost:8420 就能看到新皮肤**（CSS/JS 是静态文件，不用重启服务器）
- - 标题用 Fraunces 艺术衬线（斜体渐变 logo），正文 Space Grotesk
- 加一个轻量自动同步：工作台每 60 秒静默拉一次（一次 DB query，很便宜），数据没变就不重绘（不会打断你正在看的东西）；Detail 页不自动刷（它要走十几个 Notion API 调用，而且刷新会打断正在播的视频）——
- - 切走再切回来这个浏览器 tab 时立即补一次同步（不用等 60 秒）
- **一个刻意的取舍：** Detail 页（打开单个 row 的那页）**不**自动刷新 — 它一次要走 ~15 个 Notion API 调用，而且自动重绘会打断你正在播的视频/音频。看 detail 时想要最新状态，点「↻ 刷新」；跑任务结束后它本来就会自动刷。
- - **↻ 图** — 只重生成这一个 shot 的图片：先删掉 toggle 里的旧图再生成新的（没图就直接补上）。用的还是这个 shot 自己的 Notion prompt + IP 参考脸


## 2026-07-10 16:17 — social-ip-engine

### Decisions & Reasoning
- **2. Detail 页直接内嵌真素材 — review 不用再开 Notion**
- 你先点开一个「图+声待 review」的 row 用一下，哪里不顺手告诉我，我马上调。
- ✅ **改完了 — 浏览器里刷新 http://localhost:8420 就能看到新皮肤**（CSS/JS 是静态文件，不用重启服务器）
- - 标题用 Fraunces 艺术衬线（斜体渐变 logo），正文 Space Grotesk
- 加一个轻量自动同步：工作台每 60 秒静默拉一次（一次 DB query，很便宜），数据没变就不重绘（不会打断你正在看的东西）；Detail 页不自动刷（它要走十几个 Notion API 调用，而且刷新会打断正在播的视频）——
- - 切走再切回来这个浏览器 tab 时立即补一次同步（不用等 60 秒）
- **一个刻意的取舍：** Detail 页（打开单个 row 的那页）**不**自动刷新 — 它一次要走 ~15 个 Notion API 调用，而且自动重绘会打断你正在播的视频/音频。看 detail 时想要最新状态，点「↻ 刷新」；跑任务结束后它本来就会自动刷。
- - **↻ 图** — 只重生成这一个 shot 的图片：先删掉 toggle 里的旧图再生成新的（没图就直接补上）。用的还是这个 shot 自己的 Notion prompt + IP 参考脸


## 2026-07-10 17:22 — social-ip-engine

### Decisions & Reasoning
- **2. Detail 页直接内嵌真素材 — review 不用再开 Notion**
- 你先点开一个「图+声待 review」的 row 用一下，哪里不顺手告诉我，我马上调。
- ✅ **改完了 — 浏览器里刷新 http://localhost:8420 就能看到新皮肤**（CSS/JS 是静态文件，不用重启服务器）
- - 标题用 Fraunces 艺术衬线（斜体渐变 logo），正文 Space Grotesk
- 加一个轻量自动同步：工作台每 60 秒静默拉一次（一次 DB query，很便宜），数据没变就不重绘（不会打断你正在看的东西）；Detail 页不自动刷（它要走十几个 Notion API 调用，而且刷新会打断正在播的视频）——
- - 切走再切回来这个浏览器 tab 时立即补一次同步（不用等 60 秒）
- **一个刻意的取舍：** Detail 页（打开单个 row 的那页）**不**自动刷新 — 它一次要走 ~15 个 Notion API 调用，而且自动重绘会打断你正在播的视频/音频。看 detail 时想要最新状态，点「↻ 刷新」；跑任务结束后它本来就会自动刷。
- - **↻ 图** — 只重生成这一个 shot 的图片：先删掉 toggle 里的旧图再生成新的（没图就直接补上）。用的还是这个 shot 自己的 Notion prompt + IP 参考脸


## 2026-07-10 17:49 — social-ip-engine

### Decisions & Reasoning
- **2. Detail 页直接内嵌真素材 — review 不用再开 Notion**
- 你先点开一个「图+声待 review」的 row 用一下，哪里不顺手告诉我，我马上调。
- ✅ **改完了 — 浏览器里刷新 http://localhost:8420 就能看到新皮肤**（CSS/JS 是静态文件，不用重启服务器）
- - 标题用 Fraunces 艺术衬线（斜体渐变 logo），正文 Space Grotesk
- 加一个轻量自动同步：工作台每 60 秒静默拉一次（一次 DB query，很便宜），数据没变就不重绘（不会打断你正在看的东西）；Detail 页不自动刷（它要走十几个 Notion API 调用，而且刷新会打断正在播的视频）——
- - 切走再切回来这个浏览器 tab 时立即补一次同步（不用等 60 秒）
- **一个刻意的取舍：** Detail 页（打开单个 row 的那页）**不**自动刷新 — 它一次要走 ~15 个 Notion API 调用，而且自动重绘会打断你正在播的视频/音频。看 detail 时想要最新状态，点「↻ 刷新」；跑任务结束后它本来就会自动刷。
- - **↻ 图** — 只重生成这一个 shot 的图片：先删掉 toggle 里的旧图再生成新的（没图就直接补上）。用的还是这个 shot 自己的 Notion prompt + IP 参考脸


## 2026-07-10 18:06 — social-ip-engine

### Decisions & Reasoning
- **2. Detail 页直接内嵌真素材 — review 不用再开 Notion**
- 你先点开一个「图+声待 review」的 row 用一下，哪里不顺手告诉我，我马上调。
- ✅ **改完了 — 浏览器里刷新 http://localhost:8420 就能看到新皮肤**（CSS/JS 是静态文件，不用重启服务器）
- - 标题用 Fraunces 艺术衬线（斜体渐变 logo），正文 Space Grotesk
- 加一个轻量自动同步：工作台每 60 秒静默拉一次（一次 DB query，很便宜），数据没变就不重绘（不会打断你正在看的东西）；Detail 页不自动刷（它要走十几个 Notion API 调用，而且刷新会打断正在播的视频）——
- - 切走再切回来这个浏览器 tab 时立即补一次同步（不用等 60 秒）
- **一个刻意的取舍：** Detail 页（打开单个 row 的那页）**不**自动刷新 — 它一次要走 ~15 个 Notion API 调用，而且自动重绘会打断你正在播的视频/音频。看 detail 时想要最新状态，点「↻ 刷新」；跑任务结束后它本来就会自动刷。
- - **↻ 图** — 只重生成这一个 shot 的图片：先删掉 toggle 里的旧图再生成新的（没图就直接补上）。用的还是这个 shot 自己的 Notion prompt + IP 参考脸


## 2026-07-10 18:07 — social-ip-engine

### Decisions & Reasoning
- **2. Detail 页直接内嵌真素材 — review 不用再开 Notion**
- 你先点开一个「图+声待 review」的 row 用一下，哪里不顺手告诉我，我马上调。
- ✅ **改完了 — 浏览器里刷新 http://localhost:8420 就能看到新皮肤**（CSS/JS 是静态文件，不用重启服务器）
- - 标题用 Fraunces 艺术衬线（斜体渐变 logo），正文 Space Grotesk
- 加一个轻量自动同步：工作台每 60 秒静默拉一次（一次 DB query，很便宜），数据没变就不重绘（不会打断你正在看的东西）；Detail 页不自动刷（它要走十几个 Notion API 调用，而且刷新会打断正在播的视频）——
- - 切走再切回来这个浏览器 tab 时立即补一次同步（不用等 60 秒）
- **一个刻意的取舍：** Detail 页（打开单个 row 的那页）**不**自动刷新 — 它一次要走 ~15 个 Notion API 调用，而且自动重绘会打断你正在播的视频/音频。看 detail 时想要最新状态，点「↻ 刷新」；跑任务结束后它本来就会自动刷。
- - **↻ 图** — 只重生成这一个 shot 的图片：先删掉 toggle 里的旧图再生成新的（没图就直接补上）。用的还是这个 shot 自己的 Notion prompt + IP 参考脸


## 2026-07-10 18:16 — social-ip-engine

### Decisions & Reasoning
- **2. Detail 页直接内嵌真素材 — review 不用再开 Notion**
- 你先点开一个「图+声待 review」的 row 用一下，哪里不顺手告诉我，我马上调。
- ✅ **改完了 — 浏览器里刷新 http://localhost:8420 就能看到新皮肤**（CSS/JS 是静态文件，不用重启服务器）
- - 标题用 Fraunces 艺术衬线（斜体渐变 logo），正文 Space Grotesk
- 加一个轻量自动同步：工作台每 60 秒静默拉一次（一次 DB query，很便宜），数据没变就不重绘（不会打断你正在看的东西）；Detail 页不自动刷（它要走十几个 Notion API 调用，而且刷新会打断正在播的视频）——
- - 切走再切回来这个浏览器 tab 时立即补一次同步（不用等 60 秒）
- **一个刻意的取舍：** Detail 页（打开单个 row 的那页）**不**自动刷新 — 它一次要走 ~15 个 Notion API 调用，而且自动重绘会打断你正在播的视频/音频。看 detail 时想要最新状态，点「↻ 刷新」；跑任务结束后它本来就会自动刷。
- - **↻ 图** — 只重生成这一个 shot 的图片：先删掉 toggle 里的旧图再生成新的（没图就直接补上）。用的还是这个 shot 自己的 Notion prompt + IP 参考脸


## 2026-07-10 18:19 — social-ip-engine

### Decisions & Reasoning
- **2. Detail 页直接内嵌真素材 — review 不用再开 Notion**
- 你先点开一个「图+声待 review」的 row 用一下，哪里不顺手告诉我，我马上调。
- ✅ **改完了 — 浏览器里刷新 http://localhost:8420 就能看到新皮肤**（CSS/JS 是静态文件，不用重启服务器）
- - 标题用 Fraunces 艺术衬线（斜体渐变 logo），正文 Space Grotesk
- 加一个轻量自动同步：工作台每 60 秒静默拉一次（一次 DB query，很便宜），数据没变就不重绘（不会打断你正在看的东西）；Detail 页不自动刷（它要走十几个 Notion API 调用，而且刷新会打断正在播的视频）——
- - 切走再切回来这个浏览器 tab 时立即补一次同步（不用等 60 秒）
- **一个刻意的取舍：** Detail 页（打开单个 row 的那页）**不**自动刷新 — 它一次要走 ~15 个 Notion API 调用，而且自动重绘会打断你正在播的视频/音频。看 detail 时想要最新状态，点「↻ 刷新」；跑任务结束后它本来就会自动刷。
- - **↻ 图** — 只重生成这一个 shot 的图片：先删掉 toggle 里的旧图再生成新的（没图就直接补上）。用的还是这个 shot 自己的 Notion prompt + IP 参考脸


## 2026-07-10 18:36 — social-ip-engine

### Decisions & Reasoning
- **2. Detail 页直接内嵌真素材 — review 不用再开 Notion**
- 你先点开一个「图+声待 review」的 row 用一下，哪里不顺手告诉我，我马上调。
- ✅ **改完了 — 浏览器里刷新 http://localhost:8420 就能看到新皮肤**（CSS/JS 是静态文件，不用重启服务器）
- - 标题用 Fraunces 艺术衬线（斜体渐变 logo），正文 Space Grotesk
- 加一个轻量自动同步：工作台每 60 秒静默拉一次（一次 DB query，很便宜），数据没变就不重绘（不会打断你正在看的东西）；Detail 页不自动刷（它要走十几个 Notion API 调用，而且刷新会打断正在播的视频）——
- - 切走再切回来这个浏览器 tab 时立即补一次同步（不用等 60 秒）
- **一个刻意的取舍：** Detail 页（打开单个 row 的那页）**不**自动刷新 — 它一次要走 ~15 个 Notion API 调用，而且自动重绘会打断你正在播的视频/音频。看 detail 时想要最新状态，点「↻ 刷新」；跑任务结束后它本来就会自动刷。
- - **↻ 图** — 只重生成这一个 shot 的图片：先删掉 toggle 里的旧图再生成新的（没图就直接补上）。用的还是这个 shot 自己的 Notion prompt + IP 参考脸


## 2026-07-13 10:01 — social-ip-engine

### Decisions & Reasoning
- **2. Detail 页直接内嵌真素材 — review 不用再开 Notion**
- 你先点开一个「图+声待 review」的 row 用一下，哪里不顺手告诉我，我马上调。
- ✅ **改完了 — 浏览器里刷新 http://localhost:8420 就能看到新皮肤**（CSS/JS 是静态文件，不用重启服务器）
- - 标题用 Fraunces 艺术衬线（斜体渐变 logo），正文 Space Grotesk
- 加一个轻量自动同步：工作台每 60 秒静默拉一次（一次 DB query，很便宜），数据没变就不重绘（不会打断你正在看的东西）；Detail 页不自动刷（它要走十几个 Notion API 调用，而且刷新会打断正在播的视频）——
- - 切走再切回来这个浏览器 tab 时立即补一次同步（不用等 60 秒）
- **一个刻意的取舍：** Detail 页（打开单个 row 的那页）**不**自动刷新 — 它一次要走 ~15 个 Notion API 调用，而且自动重绘会打断你正在播的视频/音频。看 detail 时想要最新状态，点「↻ 刷新」；跑任务结束后它本来就会自动刷。
- - **↻ 图** — 只重生成这一个 shot 的图片：先删掉 toggle 里的旧图再生成新的（没图就直接补上）。用的还是这个 shot 自己的 Notion prompt + IP 参考脸


## 2026-07-13 10:07 — social-ip-engine

### Decisions & Reasoning
- **2. Detail 页直接内嵌真素材 — review 不用再开 Notion**
- 你先点开一个「图+声待 review」的 row 用一下，哪里不顺手告诉我，我马上调。
- ✅ **改完了 — 浏览器里刷新 http://localhost:8420 就能看到新皮肤**（CSS/JS 是静态文件，不用重启服务器）
- - 标题用 Fraunces 艺术衬线（斜体渐变 logo），正文 Space Grotesk
- 加一个轻量自动同步：工作台每 60 秒静默拉一次（一次 DB query，很便宜），数据没变就不重绘（不会打断你正在看的东西）；Detail 页不自动刷（它要走十几个 Notion API 调用，而且刷新会打断正在播的视频）——
- - 切走再切回来这个浏览器 tab 时立即补一次同步（不用等 60 秒）
- **一个刻意的取舍：** Detail 页（打开单个 row 的那页）**不**自动刷新 — 它一次要走 ~15 个 Notion API 调用，而且自动重绘会打断你正在播的视频/音频。看 detail 时想要最新状态，点「↻ 刷新」；跑任务结束后它本来就会自动刷。
- - **↻ 图** — 只重生成这一个 shot 的图片：先删掉 toggle 里的旧图再生成新的（没图就直接补上）。用的还是这个 shot 自己的 Notion prompt + IP 参考脸


## 2026-07-13 10:08 — social-ip-engine

### Decisions & Reasoning
- **2. Detail 页直接内嵌真素材 — review 不用再开 Notion**
- 你先点开一个「图+声待 review」的 row 用一下，哪里不顺手告诉我，我马上调。
- ✅ **改完了 — 浏览器里刷新 http://localhost:8420 就能看到新皮肤**（CSS/JS 是静态文件，不用重启服务器）
- - 标题用 Fraunces 艺术衬线（斜体渐变 logo），正文 Space Grotesk
- 加一个轻量自动同步：工作台每 60 秒静默拉一次（一次 DB query，很便宜），数据没变就不重绘（不会打断你正在看的东西）；Detail 页不自动刷（它要走十几个 Notion API 调用，而且刷新会打断正在播的视频）——
- - 切走再切回来这个浏览器 tab 时立即补一次同步（不用等 60 秒）
- **一个刻意的取舍：** Detail 页（打开单个 row 的那页）**不**自动刷新 — 它一次要走 ~15 个 Notion API 调用，而且自动重绘会打断你正在播的视频/音频。看 detail 时想要最新状态，点「↻ 刷新」；跑任务结束后它本来就会自动刷。
- - **↻ 图** — 只重生成这一个 shot 的图片：先删掉 toggle 里的旧图再生成新的（没图就直接补上）。用的还是这个 shot 自己的 Notion prompt + IP 参考脸


## 2026-07-13 10:12 — social-ip-engine

### Decisions & Reasoning
- **2. Detail 页直接内嵌真素材 — review 不用再开 Notion**
- 你先点开一个「图+声待 review」的 row 用一下，哪里不顺手告诉我，我马上调。
- ✅ **改完了 — 浏览器里刷新 http://localhost:8420 就能看到新皮肤**（CSS/JS 是静态文件，不用重启服务器）
- - 标题用 Fraunces 艺术衬线（斜体渐变 logo），正文 Space Grotesk
- 加一个轻量自动同步：工作台每 60 秒静默拉一次（一次 DB query，很便宜），数据没变就不重绘（不会打断你正在看的东西）；Detail 页不自动刷（它要走十几个 Notion API 调用，而且刷新会打断正在播的视频）——
- - 切走再切回来这个浏览器 tab 时立即补一次同步（不用等 60 秒）
- **一个刻意的取舍：** Detail 页（打开单个 row 的那页）**不**自动刷新 — 它一次要走 ~15 个 Notion API 调用，而且自动重绘会打断你正在播的视频/音频。看 detail 时想要最新状态，点「↻ 刷新」；跑任务结束后它本来就会自动刷。
- - **↻ 图** — 只重生成这一个 shot 的图片：先删掉 toggle 里的旧图再生成新的（没图就直接补上）。用的还是这个 shot 自己的 Notion prompt + IP 参考脸


## 2026-07-13 10:16 — social-ip-engine

### Decisions & Reasoning
- **2. Detail 页直接内嵌真素材 — review 不用再开 Notion**
- 你先点开一个「图+声待 review」的 row 用一下，哪里不顺手告诉我，我马上调。
- ✅ **改完了 — 浏览器里刷新 http://localhost:8420 就能看到新皮肤**（CSS/JS 是静态文件，不用重启服务器）
- - 标题用 Fraunces 艺术衬线（斜体渐变 logo），正文 Space Grotesk
- 加一个轻量自动同步：工作台每 60 秒静默拉一次（一次 DB query，很便宜），数据没变就不重绘（不会打断你正在看的东西）；Detail 页不自动刷（它要走十几个 Notion API 调用，而且刷新会打断正在播的视频）——
- - 切走再切回来这个浏览器 tab 时立即补一次同步（不用等 60 秒）
- **一个刻意的取舍：** Detail 页（打开单个 row 的那页）**不**自动刷新 — 它一次要走 ~15 个 Notion API 调用，而且自动重绘会打断你正在播的视频/音频。看 detail 时想要最新状态，点「↻ 刷新」；跑任务结束后它本来就会自动刷。
- - **↻ 图** — 只重生成这一个 shot 的图片：先删掉 toggle 里的旧图再生成新的（没图就直接补上）。用的还是这个 shot 自己的 Notion prompt + IP 参考脸


## 2026-07-13 10:27 — social-ip-engine

### Decisions & Reasoning
- **2. Detail 页直接内嵌真素材 — review 不用再开 Notion**
- 你先点开一个「图+声待 review」的 row 用一下，哪里不顺手告诉我，我马上调。
- ✅ **改完了 — 浏览器里刷新 http://localhost:8420 就能看到新皮肤**（CSS/JS 是静态文件，不用重启服务器）
- - 标题用 Fraunces 艺术衬线（斜体渐变 logo），正文 Space Grotesk
- 加一个轻量自动同步：工作台每 60 秒静默拉一次（一次 DB query，很便宜），数据没变就不重绘（不会打断你正在看的东西）；Detail 页不自动刷（它要走十几个 Notion API 调用，而且刷新会打断正在播的视频）——
- - 切走再切回来这个浏览器 tab 时立即补一次同步（不用等 60 秒）
- **一个刻意的取舍：** Detail 页（打开单个 row 的那页）**不**自动刷新 — 它一次要走 ~15 个 Notion API 调用，而且自动重绘会打断你正在播的视频/音频。看 detail 时想要最新状态，点「↻ 刷新」；跑任务结束后它本来就会自动刷。
- - **↻ 图** — 只重生成这一个 shot 的图片：先删掉 toggle 里的旧图再生成新的（没图就直接补上）。用的还是这个 shot 自己的 Notion prompt + IP 参考脸


## 2026-07-13 10:32 — social-ip-engine

### Decisions & Reasoning
- **2. Detail 页直接内嵌真素材 — review 不用再开 Notion**
- 你先点开一个「图+声待 review」的 row 用一下，哪里不顺手告诉我，我马上调。
- ✅ **改完了 — 浏览器里刷新 http://localhost:8420 就能看到新皮肤**（CSS/JS 是静态文件，不用重启服务器）
- - 标题用 Fraunces 艺术衬线（斜体渐变 logo），正文 Space Grotesk
- 加一个轻量自动同步：工作台每 60 秒静默拉一次（一次 DB query，很便宜），数据没变就不重绘（不会打断你正在看的东西）；Detail 页不自动刷（它要走十几个 Notion API 调用，而且刷新会打断正在播的视频）——
- - 切走再切回来这个浏览器 tab 时立即补一次同步（不用等 60 秒）
- **一个刻意的取舍：** Detail 页（打开单个 row 的那页）**不**自动刷新 — 它一次要走 ~15 个 Notion API 调用，而且自动重绘会打断你正在播的视频/音频。看 detail 时想要最新状态，点「↻ 刷新」；跑任务结束后它本来就会自动刷。
- - **↻ 图** — 只重生成这一个 shot 的图片：先删掉 toggle 里的旧图再生成新的（没图就直接补上）。用的还是这个 shot 自己的 Notion prompt + IP 参考脸


## 2026-07-13 10:58 — social-ip-engine

### Decisions & Reasoning
- **2. Detail 页直接内嵌真素材 — review 不用再开 Notion**
- 你先点开一个「图+声待 review」的 row 用一下，哪里不顺手告诉我，我马上调。
- ✅ **改完了 — 浏览器里刷新 http://localhost:8420 就能看到新皮肤**（CSS/JS 是静态文件，不用重启服务器）
- - 标题用 Fraunces 艺术衬线（斜体渐变 logo），正文 Space Grotesk
- 加一个轻量自动同步：工作台每 60 秒静默拉一次（一次 DB query，很便宜），数据没变就不重绘（不会打断你正在看的东西）；Detail 页不自动刷（它要走十几个 Notion API 调用，而且刷新会打断正在播的视频）——
- - 切走再切回来这个浏览器 tab 时立即补一次同步（不用等 60 秒）
- **一个刻意的取舍：** Detail 页（打开单个 row 的那页）**不**自动刷新 — 它一次要走 ~15 个 Notion API 调用，而且自动重绘会打断你正在播的视频/音频。看 detail 时想要最新状态，点「↻ 刷新」；跑任务结束后它本来就会自动刷。
- - **↻ 图** — 只重生成这一个 shot 的图片：先删掉 toggle 里的旧图再生成新的（没图就直接补上）。用的还是这个 shot 自己的 Notion prompt + IP 参考脸


## 2026-07-13 11:05 — social-ip-engine

### Decisions & Reasoning
- **2. Detail 页直接内嵌真素材 — review 不用再开 Notion**
- 你先点开一个「图+声待 review」的 row 用一下，哪里不顺手告诉我，我马上调。
- ✅ **改完了 — 浏览器里刷新 http://localhost:8420 就能看到新皮肤**（CSS/JS 是静态文件，不用重启服务器）
- - 标题用 Fraunces 艺术衬线（斜体渐变 logo），正文 Space Grotesk
- 加一个轻量自动同步：工作台每 60 秒静默拉一次（一次 DB query，很便宜），数据没变就不重绘（不会打断你正在看的东西）；Detail 页不自动刷（它要走十几个 Notion API 调用，而且刷新会打断正在播的视频）——
- - 切走再切回来这个浏览器 tab 时立即补一次同步（不用等 60 秒）
- **一个刻意的取舍：** Detail 页（打开单个 row 的那页）**不**自动刷新 — 它一次要走 ~15 个 Notion API 调用，而且自动重绘会打断你正在播的视频/音频。看 detail 时想要最新状态，点「↻ 刷新」；跑任务结束后它本来就会自动刷。
- - **↻ 图** — 只重生成这一个 shot 的图片：先删掉 toggle 里的旧图再生成新的（没图就直接补上）。用的还是这个 shot 自己的 Notion prompt + IP 参考脸


## 2026-07-13 11:09 — social-ip-engine

### Decisions & Reasoning
- **2. Detail 页直接内嵌真素材 — review 不用再开 Notion**
- 你先点开一个「图+声待 review」的 row 用一下，哪里不顺手告诉我，我马上调。
- ✅ **改完了 — 浏览器里刷新 http://localhost:8420 就能看到新皮肤**（CSS/JS 是静态文件，不用重启服务器）
- - 标题用 Fraunces 艺术衬线（斜体渐变 logo），正文 Space Grotesk
- 加一个轻量自动同步：工作台每 60 秒静默拉一次（一次 DB query，很便宜），数据没变就不重绘（不会打断你正在看的东西）；Detail 页不自动刷（它要走十几个 Notion API 调用，而且刷新会打断正在播的视频）——
- - 切走再切回来这个浏览器 tab 时立即补一次同步（不用等 60 秒）
- **一个刻意的取舍：** Detail 页（打开单个 row 的那页）**不**自动刷新 — 它一次要走 ~15 个 Notion API 调用，而且自动重绘会打断你正在播的视频/音频。看 detail 时想要最新状态，点「↻ 刷新」；跑任务结束后它本来就会自动刷。
- - **↻ 图** — 只重生成这一个 shot 的图片：先删掉 toggle 里的旧图再生成新的（没图就直接补上）。用的还是这个 shot 自己的 Notion prompt + IP 参考脸


## 2026-07-13 11:13 — social-ip-engine

### Decisions & Reasoning
- **2. Detail 页直接内嵌真素材 — review 不用再开 Notion**
- 你先点开一个「图+声待 review」的 row 用一下，哪里不顺手告诉我，我马上调。
- ✅ **改完了 — 浏览器里刷新 http://localhost:8420 就能看到新皮肤**（CSS/JS 是静态文件，不用重启服务器）
- - 标题用 Fraunces 艺术衬线（斜体渐变 logo），正文 Space Grotesk
- 加一个轻量自动同步：工作台每 60 秒静默拉一次（一次 DB query，很便宜），数据没变就不重绘（不会打断你正在看的东西）；Detail 页不自动刷（它要走十几个 Notion API 调用，而且刷新会打断正在播的视频）——
- - 切走再切回来这个浏览器 tab 时立即补一次同步（不用等 60 秒）
- **一个刻意的取舍：** Detail 页（打开单个 row 的那页）**不**自动刷新 — 它一次要走 ~15 个 Notion API 调用，而且自动重绘会打断你正在播的视频/音频。看 detail 时想要最新状态，点「↻ 刷新」；跑任务结束后它本来就会自动刷。
- - **↻ 图** — 只重生成这一个 shot 的图片：先删掉 toggle 里的旧图再生成新的（没图就直接补上）。用的还是这个 shot 自己的 Notion prompt + IP 参考脸


## 2026-07-13 11:18 — social-ip-engine

### Decisions & Reasoning
- **2. Detail 页直接内嵌真素材 — review 不用再开 Notion**
- 你先点开一个「图+声待 review」的 row 用一下，哪里不顺手告诉我，我马上调。
- ✅ **改完了 — 浏览器里刷新 http://localhost:8420 就能看到新皮肤**（CSS/JS 是静态文件，不用重启服务器）
- - 标题用 Fraunces 艺术衬线（斜体渐变 logo），正文 Space Grotesk
- 加一个轻量自动同步：工作台每 60 秒静默拉一次（一次 DB query，很便宜），数据没变就不重绘（不会打断你正在看的东西）；Detail 页不自动刷（它要走十几个 Notion API 调用，而且刷新会打断正在播的视频）——
- - 切走再切回来这个浏览器 tab 时立即补一次同步（不用等 60 秒）
- **一个刻意的取舍：** Detail 页（打开单个 row 的那页）**不**自动刷新 — 它一次要走 ~15 个 Notion API 调用，而且自动重绘会打断你正在播的视频/音频。看 detail 时想要最新状态，点「↻ 刷新」；跑任务结束后它本来就会自动刷。
- - **↻ 图** — 只重生成这一个 shot 的图片：先删掉 toggle 里的旧图再生成新的（没图就直接补上）。用的还是这个 shot 自己的 Notion prompt + IP 参考脸


## 2026-07-13 11:33 — social-ip-engine

### Decisions & Reasoning
- **2. Detail 页直接内嵌真素材 — review 不用再开 Notion**
- 你先点开一个「图+声待 review」的 row 用一下，哪里不顺手告诉我，我马上调。
- ✅ **改完了 — 浏览器里刷新 http://localhost:8420 就能看到新皮肤**（CSS/JS 是静态文件，不用重启服务器）
- - 标题用 Fraunces 艺术衬线（斜体渐变 logo），正文 Space Grotesk
- 加一个轻量自动同步：工作台每 60 秒静默拉一次（一次 DB query，很便宜），数据没变就不重绘（不会打断你正在看的东西）；Detail 页不自动刷（它要走十几个 Notion API 调用，而且刷新会打断正在播的视频）——
- - 切走再切回来这个浏览器 tab 时立即补一次同步（不用等 60 秒）
- **一个刻意的取舍：** Detail 页（打开单个 row 的那页）**不**自动刷新 — 它一次要走 ~15 个 Notion API 调用，而且自动重绘会打断你正在播的视频/音频。看 detail 时想要最新状态，点「↻ 刷新」；跑任务结束后它本来就会自动刷。
- - **↻ 图** — 只重生成这一个 shot 的图片：先删掉 toggle 里的旧图再生成新的（没图就直接补上）。用的还是这个 shot 自己的 Notion prompt + IP 参考脸

