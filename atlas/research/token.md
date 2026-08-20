# LLM 成本与 token 效率调研

调研日期 **2026-08-20**。全部定价数据以该日抓取为准 —— 定价页会变，本轮就抓到两处刚变过的（Anthropic Sonnet 5 introductory 转正、OpenAI GPT-5.6 起 cache write 从免费变收费）。

**标注约定**：
- 【官】= 供应商官方文档/定价页原文明说
- 【测】= 第三方或本机实测数据
- 【推】= 我从官方价格表或本机数据推算，算式已写出
- 【突】= 存在互相矛盾的说法，两边都列

**读代码的位置说明**：parent 给的 `AgentDatabase/atlas/build/metrics.py` 路径不存在。实际代码在 worktree
`~/Documents/Codex/GithubProject/_scratch/AD-polish/atlas/build/`（分支 `fix/atlas-v0.5.1-copy`）。
**该 worktree 在本次调研进行中被另一个并行会话收掉了**，所以路径现已失效；本文引用的行号来自收掉之前读到的原文。
**本机实测数字有两个来源，请注意区分**：
1. **派生快照** `/private/tmp/atlas_out_snapshot/*.sessions.jsonl`（2826 场，早于 parent 说的 4802 场，
   但缓存命中率 99.8839% 与 parent 给的 99.88% 逐位吻合、`694,913` 与 parent 给的"约 69.5 万"逐位吻合，
   确认是同一条数据血缘）。**这一份带 §3.P0 的虚高。**
2. **原始 transcript 直扫** `~/.claude/projects/`（1,528 个 JSONL）。**这一份是我自己按 `message.id` 去重后算的，
   是本文里唯一未受 P0 污染的数字。** §3.P0 的全部对照表出自这里。

**本次调研只读不写**：没有改动项目里的任何文件，没有写任何代码，
临时分析脚本只落在 scratchpad（`an.py` / `an2.py` / `an3.py` / `an4.py`），未进入任何仓。

---

## 0. 先看这八条

0. **⚠️ 先修这个 —— 这是唯一的真 bug，它推翻了看板上所有绝对数字。**
   `extract.py` 对**每一条 JSONL 记录**累加 `usage`，但**一个 API 响应在 JSONL 里不是一条记录** ——
   它按 content block 拆成多行（1 个 thinking + 6 个并行 tool_use = **7 行**），**每行都带着同一份完整 `usage`**；
   会话 resume 时还会把整段历史再重放一遍。
   直扫 `~/.claude/projects/` 全部 1,528 个 transcript：**322,284 条 usage 记录，只对应 130,138 个不同的 `message.id`** ——
   **每个 API 响应被计了 2.48 次。**

   | | 现在算出来的 | **去重后** | 虚高 |
   |---|---|---|---|
   | cache_read | 135,709,715,359 | **56,374,433,563** | **2.41×** |
   | cache_write | 1,476,522,068 | **490,323,862** | **3.01×** |
   | 账单（Opus 5） | **$86,068** | **$34,166** | **2.52×** |

   **单场虚高 1× 到 4.99× 不均匀，且并行工具调用越多虚高越狠 —— 最 agentic 的会话虚高最严重。**
   **为什么一直没发现：命中率对它免疫**（四类一起虚高，99.998007% → 99.998682%）。
   一个数据错了也不变、对了也不变的 KPI，本身就不承载信息。（§3.P0）

1. **现有成本口径覆盖 11.7% 的账单。** `aei.py` 的 `cost_tokens = tok_in + tok_out` 主动排除了 cache read 与 cache write，
   而这两类合起来是 **88.3%** 的钱。排除的理由（"缓存单价低一个数量级"）单价判断正确、结论反了 ——
   单价 0.1x，但**量比 860:1**。（§3.P1）

2. **单价最高的那类 token 在看板上不存在。** `cache_write` 采了、算了、但 `web/` 里零渲染。
   它是 fresh input 的 **8.91 倍**（去重后 **660 倍**），按 Opus 5 是 **$3,065–$9,228**。（§3.P2）

3. **99.88% 命中率是恒等式，不是指标。** 分母排除了 cache write；而 Claude Code 的 `input_tokens` 本身
   就定义为扣掉缓存后的残值 —— 这个数**被定义为**趋近 100%，做得多好多差都一样。
   诚实口径是 98.86%，claude-code 单独看，显示的 miss 把真实 fresh input 低估了 **533 倍**。（§3.P3）
   **四份独立外部实测（97% / 91.7% / 98.09% / 84.6–99.5%）证实这是这类负载的结构常数。**（§7.B）

4. **94.5% 的 token 记在了错误的日子上。** 按会话 `start` 日归集，但 194 场跨日会话装着 94.5% 的量。
   最极端一场跨 **24 天 16 小时**、1104 turns、32111 tools、**346 亿 cache_read**，
   独占其 start 日的 **99.7%**。
   ⚠️ **parent 引用的「某天读进 130 亿 token、当天 0 次提交」极可能就是这个归集假象。**（§3.P6）

5. **`69.5 万 token/commit` 是分子子集、分母全集。** 分子只算 human 会话，分母是全部提交。
   同口径 + 价格加权 + **去重**后约 **$44.84/commit**（Opus 5）。
   现值那个 69.5 万既漏了 88% 的账单，又被 P0 虚高了约 3 倍。（§3.P5）

6. **最高性价比的省钱杠杆是"给工具输出封顶"，不是"缩短提示词"。**
   三份独立实测：**−38%**（Towards AI/DeepSeek，质量完全不变）、**−52.7%**（JetBrains+TUM，解决率略升）、
   **−63.9%**（GPT-5/D365，完成率 71%→79%）。实施代价是一个 hook。（§5.L1）

7. **⚠️ "压缩上下文省钱"是错的。** 实测压缩比不压**贵 118%**（$0.11→$0.24/轮），
   同时记忆召回从 92–100% 掉到 38%。机制：摘要调用要把整个历史再发一遍（Claude Code 官方文档承认），
   且摘要后前缀重写导致**缓存全失效**（Anthropic 官方把 compaction 列在"会毁 cache 的动作"里）。
   **正确做法是"开新会话丢掉旧上下文"，不是"压缩"。**（§5.L8）

**外加两条对 Owner 实际供应商组合的直接影响**：

- **DeepSeek 在 2026-08-16 把缓存命中档涨了 6 倍**，且实测显示**命中率越高吃亏越大**
  （同负载账单变 2.7 倍；命中率为 0 反而只涨 1.5 倍）。本机 DSH/kimi 那条线命中率 98.39%，属吃亏最狠的一档。（§5.L4 / §7.A3）
- **SCNet Token Plan 明令禁止 API 脚本化 / 后端 / 批量调用**，只许在交互式工具里用。
  本机有 3818 场扇出/批处理会话 —— 如果那条线走的是 Token Plan，**这是合规风险不只是成本问题**。（§1.7）

---

## 1. 各供应商缓存计价对照表

### 1.1 机制形状：四家其实是四种不同的东西

| 维度 | Anthropic | OpenAI | Google Gemini | DeepSeek |
|---|---|---|---|---|
| 是否需显式标记 | **需要**（`cache_control` breakpoint） | 早期全自动；GPT-5.6+ 自动 + 可显式断点 | 隐式自动 / 显式手动两套并存 | **全自动，无需改代码**【官】 |
| 写入怎么收费 | **写入溢价** 1.25x(5m) / 2x(1h) | 早期**免费**；**GPT-5.6 起 1.25x** | **不收写入费，改收 storage 租金（按 token-hour）** | **不收** |
| 读取折扣 | 0.1x | 0.1x（GPT-5 系）/ 0.25x / 0.5x（老模型）【突】 | 0.1x | **~0.032x（四家最狠）** |
| 最小可缓存 token | 512 / 1024 / 2048 / 4096，**逐版本不同** | 1024（5.6+ 硬性）；1024–2048（早期） | 2048 / 4096 | 旧文档 64；现版无明示门槛【突】 |
| TTL | 5m 默认 / 1h 付费，命中免费续期 | 早期 5–10min 闲置上限 1h；可选 24h；5.6+ 精确 30min 续期 | 显式默认 1 小时可设；隐式无控制 | 无承诺，"几小时到几天"后清 |
| 命中保证 | 有（显式 breakpoint） | 5.6+ exact matching；早期 best-effort | 显式有保证 / **隐式明确无保证**【官】 | **明确 best-effort，不保证**【官】 |
| 额外时段折扣 | 无（有 Batch 50%） | 无（有 Batch/Flex 50%） | 无（有 Batch/Flex 50%） | **off-peak 5 折，覆盖 17h/天** |

**最关键的结构差异**：Gemini 显式缓存不是"写入溢价"模型，是**持续计租**模型 —— storage 按 TTL 全时长收，
不管你读不读。这一条让 Gemini 的盈亏平衡计算完全无法套用另外三家的公式（见 1.5）。

### 1.2 Anthropic — 单价表（$/MTok，抓取 2026-08-20）

来源：https://platform.claude.com/docs/en/about-claude/pricing 与
https://platform.claude.com/docs/en/docs/build-with-claude/prompt-caching
（原 `docs.anthropic.com/...` 301 跳转至此；**两页均无 last-updated 标注**）

倍数原文【官】："5-minute cache write tokens are 1.25 times the base input tokens price /
1-hour cache write tokens are 2 times the base input tokens price / Cache read tokens are 0.1 times the base input tokens price"

| 模型 | Base Input | 5m Write | 1h Write | Cache Hit | Output |
|---|---|---|---|---|---|
| Claude Fable 5 / Mythos 5 | $10 | $12.50 | $20 | $1 | $50 |
| **Claude Opus 5** | **$5** | **$6.25** | **$10** | **$0.50** | **$25** |
| Claude Opus 4.8 / 4.7 / 4.6 / 4.5 | $5 | $6.25 | $10 | $0.50 | $25 |
| **Claude Sonnet 5** | **$2** | **$2.50** | **$4** | **$0.20** | **$10** |
| Claude Sonnet 4.6 / 4.5 | $3 | $3.75 | $6 | $0.30 | $15 |
| **Claude Haiku 4.5** | **$1** | **$1.25** | **$2** | **$0.10** | **$5** |

**注意 output 是 input 的 5 倍**（每一档都是）。任何把 input token 和 output token 当同一单位相加的成本口径都错 5 倍 —— 这直接命中本机代码的问题，见 §3.P1。

**刚变过的两件事**【官】：
- Sonnet 5 的 $2/$10 原标注为"到 2026-08-31 的 introductory pricing"，现已转为标准价，**原定 2026-09-01 涨到 $3/$15 不会发生**。
- Claude 4.7 及以后 + Mythos Preview 换了新 tokenizer，**同样文本约多出 30% token**。换算历史成本时必须计入，否则跨版本比较会把 tokenizer 变更误读成用量增长。

**最小可缓存 token 数是逐版本的，不是按档位**【官】。反直觉：最便宜的 Haiku 4.5 门槛最高（4,096），最贵的 Opus 5 门槛最低（512）。

| 门槛 | 模型 |
|---|---|
| 512 | Opus 5、Fable 5、Mythos 5 |
| 1,024 | Opus 4.8、Sonnet 5、Sonnet 4.6/4.5、Opus 4.1/4、Sonnet 4 |
| 2,048 | Mythos Preview、Opus 4.7、Haiku 3.5 |
| 4,096 | Opus 4.6、Opus 4.5、**Haiku 4.5** |

**TTL 计时陷阱（实操最容易踩的一条）**【官】：
> "The lifetime is measured from the start of the request that writes or reads the cache entry, not from the end of its response. Time spent generating a response counts against the lifetime: if a response takes 4 minutes to stream, a follow-up request that reuses the same cached prefix must start within about 1 minute of that response completing."

即：**TTL 从请求开始计时，不是从响应结束**。agent 会话里长输出很常见，一次流式输出跑 4 分钟，5m TTL 就只剩 1 分钟。这解释了为什么 agent 场景下 cache_write 量会异常高（见 §5.L5）。

其他【官】：
- 缓存**免费续期**："The cache is refreshed for no additional cost each time the cached content is used."
- **最多 4 个 cache breakpoint / 请求**（超出返回 400），另有 20 个 block 的 lookback window
- 失效顺序：`tools` → `system` → `messages`，**任一层变动会让该层及之后全部失效**（见 §5.L6）
- `usage` 三字段：`cache_creation_input_tokens` / `cache_read_input_tokens` / `input_tokens`（最后一个 breakpoint 之后的部分）
- 缓存倍数与 **Batch API 50% 折扣可叠乘**；data residency 1.1x 倍数也叠乘

### 1.3 OpenAI — GPT-5.6 是断层

来源：https://developers.openai.com/api/docs/guides/prompt-caching 与
https://developers.openai.com/api/docs/pricing
（`platform.openai.com/docs/guides/prompt-caching` 301 跳转至此；`openai.com/api/pricing/` 返回 **HTTP 403 无法直取**；两页均无 last-updated）

官方对照表原文【官】：

| Behavior | GPT-5.6 and later | Earlier models |
|---|---|---|
| Cache matching | Exact matching at eligible cache breakpoints | Automatic best-effort reuse of matching prefixes |
| Explicit cache breakpoints | Supported. Implicit caching is also available. | Not supported. Caching is automatic. |
| Minimum cacheable prefix | 1,024 tokens | 1,024 to 2,048 tokens, depending on the model |
| **Cache write charges** | **1.25× the uncached input token rate** | **No additional cache-write fee** |
| Cache lifetime | 30-minute exact TTL set with `prompt_cache_options.ttl` | Model-dependent maximum retention set with `prompt_cache_retention` |

**这是相对普遍认知的重大变化：OpenAI 的 cache write 不再总是免费。** 任何"OpenAI 缓存写入不要钱"的旧结论在 GPT-5.6 之后失效。

**折扣倍数：官方两页互相矛盾**【突】

caching 指南正文写："Cached input tokens are billed at 0.1× the uncached input token rate."
但**同站价格表**上老模型对不上：

| 模型 | Input | Cached Input | Cache Write | Output | 实际倍数 |
|---|---|---|---|---|---|
| gpt-5.6-sol | $5.00 | $0.50 | **$6.25** | $30.00 | 0.1x ✅ |
| gpt-5.6-terra | $2.00 | $0.20 | **$2.50** | $12.00 | 0.1x ✅ |
| gpt-5.6-luna | $0.20 | $0.02 | **$0.25** | $1.20 | 0.1x ✅ |
| gpt-5.5 | $5.00 | $0.50 | 无 | $30.00 | 0.1x ✅ |
| gpt-5.4 | $2.50 | $0.25 | 无 | $15.00 | 0.1x ✅ |
| gpt-5.1 / gpt-5 | $1.25 | $0.125 | 无 | $10.00 | 0.1x |
| gpt-5-nano | $0.05 | $0.005 | 无 | $0.40 | 0.1x |
| **gpt-4.1 / o3** | $2.00 | **$0.50** | 无 | $8.00 | **0.25x** ❌ |
| **gpt-4o / o1 / o3-mini** | $2.50 / $15 / $1.10 | **$1.25 / $7.50 / $0.55** | 无 | — | **0.5x** ❌ |

**分歧点**：指南说 0.1x 是全局规则；价格表上 gpt-4o/o1/o3-mini 是 0.5x、gpt-4.1/o3 是 0.25x。
**这是 OpenAI 官方两页之间的内部不一致，不是第三方误传。按价格表为准。**
GPT-5.6 三个型号的 cache write 价 $6.25/$2.50/$0.25 恰好 = 1.25 × input，与文档倍数自洽【推】。

其他【官】：
- 命中按 **128 token 台阶**结算："Cache hits occur in increments of 128 tokens."
- 早期模型留存："cached prefixes generally remain active for 5 to 10 minutes of inactivity, up to a maximum of one hour."
- 可选 24h 留存 `prompt_cache_retention: "24h"`，支持 gpt-5.5 / 5.4 / 5.2 / 5.1 系 / gpt-5 / gpt-4.1 等
- `prompt_cache_key` 用于提高路由命中率，官方建议每个 key 的总流量控制在 **~15 请求/分钟**

### 1.4 Google Gemini — 唯一按"租金"计费的一家

来源（**这三页有 last-updated，是四家里唯一可核版本的**）：
- https://ai.google.dev/gemini-api/docs/caching — **Last updated 2026-08-13 UTC**
- https://ai.google.dev/gemini-api/docs/generate-content/caching — **Last updated 2026-08-17 UTC**
- https://ai.google.dev/gemini-api/docs/pricing — **Last updated 2026-08-13 UTC**

**隐式 vs 显式**【官】：

| | 隐式 Implicit | 显式 Explicit |
|---|---|---|
| 开启 | 默认开，2.5 及以上全部支持，无需任何代码 | 手动创建/管理 cache 对象 |
| 省钱保证 | **"no cost saving guarantee"** | **"cost saving guarantee"** |
| **storage 费** | **无** | **有，按 token-hour 计** |
| TTL 控制 | 无 | 可设，不设默认 1 小时 |
| API 支持 | Interactions API 与 generateContent 都支持 | **Interactions API 不支持**，只能走 generateContent |

显式缓存计费构成原文【官】：
> "Billing is based on the following factors: 1. Cache token count: The number of input tokens cached, billed at a reduced rate when included in subsequent prompts. 2. Storage duration: The amount of time cached tokens are stored (TTL), billed based on the TTL duration of cached token count."

**storage 费按 TTL 全时长收，不管读不读。**

价格表节选（Standard 层，$/1M token）【官】：

| 模型 | Input | Output | Cached | **Storage /1M tokens per hour** |
|---|---|---|---|---|
| Gemini 3.1 Pro Preview | $2.00 (≤200k) / $4.00 (>200k) | $12 / $18 | $0.20 / $0.40 | **$4.50/hr** |
| Gemini 3.7 Flash | $0.75 → $1.50 (2027-01-01 起) | $3.75 → $7.50 | $0.075 → $0.15 | **$0.50/hr → $1.00/hr** |
| Gemini 3.5 Flash | $1.50 | $9.00 | $0.15 | **$1.00/hr** |
| Gemini 3.5 Flash-Lite | $0.30 | $2.50 | $0.03 | **$1.00/hr** |
| Gemini 2.5 Pro | $1.25 / $2.50 | $10 / $15 | **"Not available"**（Standard）；Batch/Flex $0.125 / $0.25 | **$4.50/hr** |
| Gemini 2.5 Flash | $0.30 | $2.50 | $0.03 | **$1.00/hr** |
| Gemini 2.5 Flash-Lite | $0.10 | $0.40 | $0.01 | **$1.00/hr** |

最小 token 门槛（隐式与显式同表同值）【官】：3.7/3.6/3.5 Flash 与 3.1 Pro Preview = **4,096**；2.5 Pro / 2.5 Flash = **2,048**。

**隐式缓存折扣是多少 —— 三个说法**【突】：

| 出处 | 说法 | 判定 |
|---|---|---|
| 2026-08-13 官方价格表 | 所有 2.5+ 模型的 cached 价恰好 = input 的 0.1x → **90% 折**【推】 | ✅ 可逐行验证 |
| WebSearch 聚合（引 ai.google.dev / cloud.google.com） | "2.5 及以上 90%，2.0 模型 75%" | 未能在直取页面逐字复核 |
| 2025-05-08 官方 Blog（developers.googleblog.com） | "the same **75%** token discount"，2.5 Flash 门槛 1024、2.5 Pro 门槛 2048 | ❌ **已过时**，折扣与门槛都与现行页面不符 |

**结论：以 2026-08-13 价格表为准 = 0.1x / 90%。** 那篇 2025 blog 仍在线且被大量第三方引用，是当前误传的主要源头。

两处需要留意的官方页面自相矛盾：
1. **Gemini 2.5 Pro 的 Standard 层 caching 标为 "Not available"，但 storage 行仍标 $4.50/hr** —— 用前需向 Google 确认。
2. 第三方常见错误："Gemini 显式缓存需要 32K token 起步" —— 32K 是 Gemini 1.5 的旧值，现行是 2,048 / 4,096。

### 1.5 DeepSeek — 折扣最狠，机制刚改过

来源：https://api-docs.deepseek.com/quick_start/pricing/ 与 https://api-docs.deepseek.com/guides/kv_cache/
（**均无 last-updated**，页脚 `Copyright © 2026 DeepSeek, Inc.`）；旧公告 https://api-docs.deepseek.com/news/news0802/ （2024-08-02）

| | **deepseek-v4-flash** | **deepseek-v4-pro** |
|---|---|---|
| MODEL VERSION | DeepSeek-V4-Flash-0731 | DeepSeek-V4-Pro-0813 |
| CONTEXT / MAX OUTPUT | 1M / 384K | 1M / 384K |
| **INPUT (CACHE HIT)** off-peak / peak | **$0.007 / $0.014** | **$0.022 / $0.044** |
| **INPUT (CACHE MISS)** off-peak / peak | **$0.22 / $0.44** | **$0.66 / $1.32** |
| **OUTPUT** off-peak / peak | **$0.66 / $1.32** | **$1.98 / $3.96** |
| Concurrency Limit | 2500 | 500 |

**人民币价（元 / 百万 tokens）**【官，中文页 https://api-docs.deepseek.com/zh-cn/quick_start/pricing/ 】

| 计费项 | flash 空闲 | flash 高峰 | pro 空闲 | pro 高峰 |
|---|---|---|---|---|
| 输入·缓存命中 | **0.05** | 0.10 | **0.15** | 0.30 |
| 输入·缓存未命中 | 1.5 | 3.0 | 4.5 | 9.0 |
| 输出 | 4.5 | 9.0 | 13.5 | 27.0 |

**Off-peak 时段**【官】英文页脚注：
> "Off-peak rates are half of the peak rates. Peak hours are 01:00 - 04:00 and 06:00 - 10:00 UTC (all other hours are off-peak)."

中文页原文写得更直观：「高峰时段为**北京时间 9:00–12:00、14:00–18:00**」（其余为空闲时段）。

- off-peak = peak 的 **50%**，hit / miss / output **三档一律**打折
- peak 只有 **7 小时/天**，其余 **17 小时全是折扣时段**
- 网上流传的"16:30–00:30 UTC 优惠"是旧规则，已变更
- **换算到悉尼 UTC+10**：peak = 本地 **11:00–14:00** 与 **16:00–20:00**。本地凌晨、上午、以及 20:00 之后全部是折扣时段【推，北京 UTC+8 → 悉尼 UTC+10 加 2 小时】

⚠️ **这套分时是 2026-08-16 UTC 16:00（北京 8/17 零点）才生效的新制**，之前是全天一价
（旧价 v4-pro 命中 ¥0.025 / 未命中 ¥3.00 / 输出 ¥6.00）。
→ **缓存命中档从 ¥0.025 涨到空闲价 ¥0.15，涨了 6.0 倍**。
**这条对本机是坏消息**：命中率越高，这次涨价吃亏越大（详见 §7.A3 的实测对账）。

**缓存机制刚改过 —— 这是本轮最重要的发现之一**【突】：

| 出处 | 说法 |
|---|---|
| 2024-08-02 公告【官】 | "The cache system uses **64 tokens** as a storage unit; content less than 64 tokens will not be cached." + "Only requests with identical prefixes (starting from the 0th token) will be considered duplicates." |
| **当前 kv_cache 指南**【官】 | **完全没有 64 token 的说法**。改为 **cache prefix unit（缓存前缀单元）**："Due to the Sliding Window Attention mechanism, the storage and matching of cached prefixes differs from before. Each cached prefix is an independent, complete unit. **A subsequent request can only hit the cache if it fully matches a cache prefix unit.**" |

前缀单元在三种时机产生【官】：(1) 每次请求在"用户输入结束位置"和"模型输出结束位置"各产生一个；
(2) 系统发现多请求共享前缀时把该前缀单独持久化；(3) 长输入/长输出时按固定间隔切出单元。

**实操含义**：`A+B` → `A+C` **第二轮不命中**（`A+C` 不完整匹配 `A+B`），但系统会把 `A` 持久化，**第三轮 `A+D` 才命中 `A`**。
几乎所有第三方博客描述的 DeepSeek 缓存行为都还停在旧模型上。

存储是否收费【突】：2024 公告说"storage usage for the cache is free"；当前 kv_cache 指南与 pricing 页**均未提及 storage 费用，价格表也无 storage 行**【推】→ 仍为免费，但已无现行文档背书。

缓存留存【官】："Once the cache is no longer in use, it will be automatically cleared, usually within a few hours to a few days." +
"The cache system works on a 'best-effort' basis and does not guarantee a 100% cache hit rate."
`usage` 字段：`prompt_cache_hit_tokens` / `prompt_cache_miss_tokens`。

### 1.6 盈亏平衡：写入需要被读多少次才回本

设 base input 单价 = 1.0，W = 写入倍数，r = 读取倍数：

- 不缓存，1 次写 + N 次读的输入总成本 = `1 + N`
- 缓存 = `W + rN`
- 盈亏平衡：`W + rN ≤ 1 + N` → **`N ≥ (W − 1) / (1 − r)`**

| 供应商 / 档位 | W | r | 命中 vs 未命中价差 | 算式 | **需读几次回本** |
|---|---|---|---|---|---|
| **Anthropic 5m** | 1.25 | 0.1 | 10.0x（省 90%） | (1.25−1)/0.9 = 0.278 | **1 次**【官已确认】 |
| **Anthropic 1h** | 2.0 | 0.1 | 10.0x | (2−1)/0.9 = 1.111 | **2 次**【官已确认】 |
| **OpenAI GPT-5.6+** | 1.25 | 0.1 | 10.0x | 0.278 | **1 次**【推】 |
| **OpenAI GPT-5.5 及更早** | 1.0（免费） | 0.1 | 10.0x | 0 | **0 次 —— 第一次命中即净赚**【推】 |
| **OpenAI gpt-4.1 / o3** | 1.0 | 0.25 | 4.0x | 0 | **0 次**【推】 |
| **OpenAI gpt-4o / o1 / o3-mini** | 1.0 | 0.5 | 2.0x | 0 | **0 次**【推】 |
| **Gemini 隐式** | 无写入费 | 0.1 | 10.0x | 0 | **0 次 —— 纯白捡**【推】 |
| **DeepSeek v4-flash** | 无写入费 | 0.007/0.22 = 0.0318 | **31.43x（省 96.82%）** | 0 | **0 次**【推】 |
| **DeepSeek v4-pro** | 无写入费 | 0.022/0.66 = 0.0333 | **30.00x（省 96.67%）** | 0 | **0 次**【推】 |

Anthropic 官方逐字确认了自己那两行【官】：
> "A cache hit costs 10% of the standard input price, which means caching pays off after one cache read for the 5-minute duration (1.25x write), or after two cache reads for the 1-hour duration (2x write)."

Opus 5 美元验算【推】：5m 写多花 $6.25−$5.00 = $1.25/MTok；每读省 $5.00−$0.50 = $4.50/MTok；$1.25 ÷ $4.50 = 0.278 → **1 次**。
1h 写多花 $5.00；$5.00 ÷ $4.50 = 1.111 → **2 次**。

**Gemini 显式缓存必须单独算 —— 量纲不同**。没有一次性写入溢价，改按 TTL 收租，所以盈亏平衡的单位是"**每小时 TTL 内需要几次读**"：

> **N_每小时 ≥ Storage价 ÷ (Input价 − Cached价) = Storage价 ÷ (0.9 × Input价)**

| 模型（Standard 层） | 算式 | **每小时需读** |
|---|---|---|
| 3.7 / 3.6 Flash、3.5 Flash | 0.50 ÷ 0.675 = 0.741 | **1 次** |
| 3.1 Pro Preview (>200k) | 4.50 ÷ 3.60 = 1.25 | **2 次** |
| 3.1 Pro Preview (≤200k) | 4.50 ÷ 1.80 = 2.50 | **3 次** |
| 3 Flash Preview | 1.00 ÷ 0.45 = 2.22 | **3 次** |
| 3.5 Flash-Lite、2.5 Flash | 1.00 ÷ 0.27 = 3.70 | **4 次** |
| 3.1 Flash-Lite | 1.00 ÷ 0.225 = 4.44 | **5 次** |
| **2.5 Flash-Lite** | 1.00 ÷ 0.09 = 11.11 | **12 次** ⚠️ |

以上全部为【推】（Gemini 官方未给盈亏平衡公式）。

**关键推论：模型越便宜，Gemini 显式缓存越不划算。** storage 是固定 $1.00/1M/hr 与模型档位无关，
但省下的钱正比于 input 单价。2.5 Flash-Lite 要每小时读满 12 次才回本，低频场景用显式缓存**净亏**。
→ Gemini 上低频复用只用隐式缓存（零成本零风险），显式缓存留给高频 + 大 context。

**四家里最便宜的一格**：DeepSeek v4-flash off-peak cache hit = **$0.007/1M**，
对比同模型 peak cache miss $0.44/1M，**差 62.86 倍**（时段 × 缓存双重叠加）。

### 1.7 SCNet（国家超算互联网）与其他国内供应商

**Owner 实际在用 DeepSeek 与 SCNet 两家，`taxonomy.py` 里也有 `SCNet（中国超算）` 这个 provider，所以这一节不是背景资料。**

#### SCNet —— 资料完整，且有三套完全不同的计价形态

运营方：曙光智算信息技术有限公司。主站 https://www.scnet.cn ；
模型 API 文档 https://www.scnet.cn/ac/openapi/doc/2.0/moduleapi/ 。**接口兼容 OpenAI 与 Anthropic 两套协议。**

**（a）按量计费 —— 按 token，不是按卡时**【官】
https://www.scnet.cn/ac/openapi/doc/2.0/moduleapi/tutorial/token.html
- LLM 按 token 后付费；Embedding 只算输入 token；**OCR 按调用次数**
- **有 prompt cache**：「部分模型支持上下文缓存（Context Cache）。当请求的输入内容命中缓存时，命中部分的输入 Token 将以更低的单价计费。」
- **可观测字段（三套协议都给了）**：`usage.prompt_tokens_details.cached_tokens`（Chat Completions）/
  `usage.input_tokens_details.cached_tokens`（Responses）/ **`usage.cache_read_input_tokens`（Anthropic Messages）**
  → **这一条对本机很重要**：走 Anthropic 协议时 SCNet 会返回和 Claude 同名的字段，
  意味着 `extract.py` 现有的解析逻辑**可能已经能接上**，值得核一下 DSH/kimi 那条线为什么 `tok_cache_w` 恒为 0
- 用量与费用数据**最长 5 分钟延迟**；结算顺序：赠送 Tokens → 现金余额
- ⚠️ **按量计费的现行价格表已从公开文档撤下**，指向控制台（需登录）。
  旧版页面 `.../tutorial/modulefee.html` 还留着一份旧价表（MiniMax-M2.5 1.05/4.2 元每百万等）—— **是旧的，别当现价用**

**（b）Token Plan（包月 Credits）**【官】https://www.scnet.cn/ac/openapi/doc/2.0/moduleapi/plans/token-plan.html

| 套餐 | 原价 | 活动价 | 月度额度 |
|---|---|---|---|
| 基础版 | ¥50/月 | **¥30/月** | 60,000 Credits |
| 标准版 | ¥185/月 | ¥110/月 | 240,000 Credits |
| 高级版 | ¥440/月 | ¥265/月 | 600,000 Credits |

**积分抵扣表（积分 / 百万 tokens，2026-08-11 生效）—— 这是目前唯一公开的、逐模型列出缓存命中价的表**：

| 模型 | 未命中输入 | 输出 | **命中输入** | **命中/未命中** |
|---|---|---|---|---|
| GLM-5.2 | 7,543 | 26,400 | **189** | 2.5% |
| GLM-5.1 / GLM-5 | 8,743 | 32,057 | 175 | 2.0% |
| **DeepSeek-V4-Pro** | 10,286 | 20,571 | **86** | **0.84%** |
| **DeepSeek-V4-Flash** | 1,200 | 2,400 | **24** | **2.0%** |
| DeepSeek-V4-Flash-0731 | 1,543 | 3,086 | 31 | 2.0% |
| Kimi-K3 | 34,286 | 171,429 | 343 | 1.0% |
| MiniMax-M2.5 | 2,520 | 10,080 | 50 | 2.0% |
| Qwen3.8-max | 18,514 | 49,371 | 231 | 1.2% |

**缓存命中折扣比四家美国供应商都狠**（0.84%–2.5% vs Anthropic/OpenAI/Gemini 的 10%）。

⚠️ **两条硬限制，对本机直接相关**：
1. **「额度用尽不自动转按量，直接报错」** —— 没有软着陆
2. **「明令禁止 API 脚本化 / 后端 / 批量调用，只许在 Claude Code、OpenClaw、Cursor 等交互式工具里用」**
   → **本机有 3818 场扇出/批处理会话。如果这条线走的是 SCNet Token Plan，这是一个合规风险，不只是成本问题。**
   建议核一下 DSH 的 1929 场 subagent 会话实际走的是哪个计费通道
3. 不支持退款/升档/降档；专属 Key 以 `sk-tp-` 开头，与通用 Key 不互通；剩余 Credits 不结转

**（c）Coding Plan —— 按请求次数，不是按 token**【官】
https://www.scnet.cn/ac/openapi/doc/2.0/moduleapi/plans/coding-plan.html
- **Lite ¥20/月**：每 5 小时 ~1,200 次请求 / 每周 ~9,000 / 每月 ~18,000
- **Pro ¥100/月**：每 5 小时 ~6,000 / 每周 ~45,000 / 每月 ~90,000
- 模型：MiniMax-M2.5、Qwen3-235B-A22B
- 官方换算：简单任务单次提问约 5~15 次模型调用，复杂任务 15~30 次或更多

> **计价形态本身就是一条结论**：Coding Plan 按**请求次数**计费，
> 这个口径下 token 数完全无关 —— §4 里所有 token 类归因单位在这条线上**全部失效**，
> 唯一有意义的单位是「每次请求」和「每 5 小时窗口用掉多少配额」。
> **同一个看板不能用一套口径同时覆盖按 token 和按次数两条计费线。**

**关于"按算力卡时/机时"**：SCNet 确实有超算作业、容器实例、Notebook 这些按资源计费的服务
（文档里有「查询已用机时」接口），但**模型 API 这条线不是按卡时** —— 是 token / Credits / 请求次数三选一。

#### 其他国内供应商

| 供应商 | 缓存机制 | 计价 | 关键点 |
|---|---|---|---|
| **月之暗面 Kimi** | **自动，无需创建、无需引用 cache ID、无需管理 TTL**；命中门槛 prompt > **256 token** | kimi-k3：命中 **¥2** / 未命中 **¥20** / 输出 **¥100** 每 1M（命中 = 未命中的 **1/10**） | ⚠️ **本轮推翻了一个假设**：调研任务里写的"Kimi 按存储时长收费"**是 2024 年公测期显式 Context Caching API 的旧机制**（创建 24 元/M + 存储 10→5 元/1M/min + 调用 0.02 元/次，IT之家 2024-08-07 报道降价）。**现行 platform.kimi.com 文档里已完全没有存储时长计费**，只剩纯 token 价目表 |
| **智谱 GLM** | **隐式，自动识别，无需配置**；字段 `usage.prompt_tokens_details.cached_tokens` | 文档写命中「**通常为标准价格的 50%**」，并给了 50% 算例 | ⚠️【突】**口径冲突**：官方文档说 50%，第三方观察说 1/4~1/5，而 SCNet 积分表里 GLM-5.2 是 189/7543 ≈ **2.5%**。逐模型准确单价在需登录 + JS 渲染的控制台价格页，**未取到**。另注意文档明说「仅适用于标准 API 计费，**不包括资源包和 GLM Coding Plan 套餐**」 |
| **阿里通义千问（百炼）** | **两套**：隐式（自动开启不可关，最小 **256 token**，命中按标准输入价 **20%**）+ 显式（`cache_control` 标记，最小 **1024 token**，**TTL 5 分钟命中重置**，创建 **125%**、命中 **10%**） | 无额外存储费 | 显式缓存的 125%/10% 结构与 Anthropic 的 1.25x/0.1x **完全同构** |
| **火山引擎豆包（方舟）** | 隐式（**不可关闭**，最小 1024 token，分段计费）+ 显式（确定性命中，可配 TTL） | **⚠️ 唯一确认对缓存存储收费的国内厂商** | 显式缓存四个计费项：输入 + 缓存输入 + **存储（元/千 token/小时）** + 输出。**「根据每个自然小时使用缓存的最大量乘以单价累加」「不足 1 小时按照 1 小时计算」**。TTL 最大 168 小时（前缀缓存 [3600, 604800] 秒），**未使用才计时、使用后重置**；Responses API 配的是过期时刻，**不随使用重置** |

> ⚠️ **豆包那条"不足 1 小时按 1 小时计算"值得单独警惕** ——
> 这和本机 R2 红线记的那个坑是同一个形状：**按整单位向上取整**。
> 高频短时缓存在这种计费下会被系统性放大。若要用豆包显式缓存，
> 必须先算「每小时峰值缓存量 × 小时数」而不是「实际用了多少分钟」。
> 官方文档的存储单价举例（0.000017 元/千 token/小时）**明确标注"单价仅为举例使用"**，
> 真实单价在需登录的「开通管理 → 推理(缓存)定价」页，**未取到**。

### 1.8 本节的不确定项

1. Anthropic / OpenAI / DeepSeek 三家的文档页**均无 last-updated 标注**，只能以抓取日 2026-08-20 为准。
   只有 Gemini 三页可核版本（08-13 / 08-17 / 08-13）。
2. `openai.com/api/pricing/` 返回 **HTTP 403 无法直取**，OpenAI 价格取自同为官方站的 `developers.openai.com/api/docs/pricing`。
3. Gemini 隐式缓存的 "90%" 是从价格表逐行推算的【推】，官方 caching 正文没有直接写这个百分比。
4. DeepSeek 的"64 token 存储单元"与"storage 免费"两条**只在 2024-08-02 旧公告页上有**，
   当前文档均未重申。若这两条是成本模型的关键假设，需向 DeepSeek 确认。
5. **未能取到的现行单价**（都在需登录 + JS 渲染的控制台页）：
   SCNet 按量计费的现行模型价格表、智谱 GLM 的逐模型缓存命中单价、火山方舟的缓存存储真实单价。
6. Kimi 的"按存储时长收费"是 **2024 年公测期机制，现已不存在** —— 这条在本轮被推翻，
   任何沿用该假设的成本模型都要改。

---

## 2. token 结构分解的公开实测数据

### 2.0 先给五个最硬的数字

| 数字 | 含义 | 来源等级 |
|---|---|---|
| **4× / 15×** | agent vs chat / multi-agent vs chat 的 token 用量 | 【官】Anthropic 原文逐字核实 |
| **84%** | observation token 占 SWE-agent 单轮的比例 | 【测】JetBrains Research + TUM |
| **>70%** | 读文件命令占 mini-SWE-agent (Sonnet 4.5) token 消耗 | 【测】上海交大 |
| **Θ(n²)，3000 条轨迹 100% 成立** | 上下文随轮次二次增长 | 【测】SWE-rebench 真实轨迹 |
| **实测 cache 命中率 84.6–99.5%** | 硬件级 trace | 【测】UIUC/Intel，2×H100 |

### 2.1 Anthropic 的 4× / 15× —— 官方原文，且有一个流传很广的误引

来源：https://www.anthropic.com/engineering/multi-agent-research-system （2025-06-13，Jeremy Hadfield 等）

原文逐字【官】：
> "In our data, agents typically use about **4× more tokens than chat interactions**, and multi-agent systems use about **15× more tokens than chats**."

> "three factors explained **95%** of the performance variance in the BrowseComp evaluation... **token usage by itself explains 80% of the variance**, with the number of tool calls and the model choice as the two other explanatory factors."

> "a multi-agent system with Claude Opus 4 as the lead agent and Claude Sonnet 4 subagents **outperformed single-agent Claude Opus 4 by 90.2%** on our internal research eval."

⚠️ **常见误引**：大量二手文章（含搜索引擎自动摘要）把 15× 说成「multi-agent 是 single-agent 的 15 倍」。
**原文的分母是 chat，不是 single agent。** 按原文两个数推，multi-agent ÷ agent ≈ 15/4 ≈ **3.75×** 才是对 single-agent 的倍数【推】。

⚠️ **限制**：Anthropic 只说「in our data」，**未公布样本量、任务分布、统计口径**。方向性经验数字，不是可复现测量。

### 2.2 上下文二次增长 vs 账单二次增长 —— 必须分开，这是本节最重要的结构性发现

**（A）上下文确实是 Θ(n²)**【测】
arXiv 2606.15954《Green SARC》，2026-06-14。对 **3,000 条 SWE-rebench 真实轨迹**（Qwen3-Coder-480B 解 GitHub issue，中位深度 61 轮）做二次回归 `c₁n + c₂n²`：
- **3,000 条轨迹 100% 的 c₂ > 0**
- 实测中位曲率 **ĉ₂ = 216**，高于线性累积理论预测 p/2 = 134 —— 真实轨迹比朴素模型累积得还快约 61%

**（B）但账单不是**【测】
arXiv 2605.26297《Agentic AI Workload Characteristics》，2026-05-25（UIUC / Gimlet Labs / Intel）。
真实硬件级 trace：2× H100 NVL、vLLM v0.20.0、TP=2、OpenTelemetry/Jaeger 全链路；
模型 Qwen3.6-27B / Gemma4-31B；5 个 benchmark（ADE-Bench、DABStep、GAIA、SWE-bench Pro、Terminal-Bench 2.0）各 100 任务。

| 指标 | 实测 |
|---|---|
| 原始 input : output 比 | **53.9× – 559.8×** |
| **每轮真正新增的 append : output 比** | **仅 1.5× – 7.3×**，中位常低于 1.5× |
| Cache 命中率 | 理论 87.9–99.3%，**实测 84.6–99.5%** |
| Decode 占 LLM 时间 | **91.0–98.6%**（prefill 只占 1.4–9.0%） |
| 上下文规模 | SWE-bench Pro 均值 68.7K–80.1K、峰值 146K–166K |
| 轮数分布 | 极散：Gemma-Instant 在 ADE 上 108.8±178.7 轮；GAIA 最高 617 轮 |

论文原话：agentic workload "not simply long-prompt workloads"，而是 **decode-dominated**。

> **对本机的直接意义**：这份实测的 84.6–99.5% 命中率，与本机看板上的 99.88% 落在同一区间。
> 它证明 **99.88% 不是本机上下文管理做得好的结果，而是这类负载的结构常数**（§3.P3 从另一侧说了同一件事）。
> 同时它说明：**谁在算 agent 成本时直接套 n(n+1)/2，会系统性高估** —— 缓存把二次增长的账单压平了，
> 但压平后的那条平线（cache read）本身就是账单主体（本机 78.15%）。

### 2.3 agent 任务比 chat 贵多少 —— 学术侧独立数字

arXiv 2604.22750《How Do AI Agents Spend Your Money?》（Michigan / Stanford / Microsoft AI / All Hands AI / Google DeepMind / MIT），2026-04-24。
方法：**SWE-bench Verified 全部 500 实例 × 8 个前沿 LLM，每题独立跑 4 次**。

⚠️ **摘要与正文口径不同，两处都列**：
- 摘要：agentic 任务消耗 "**1000x more tokens** than code reasoning and code chat"
- 正文：consume "**3500x** more tokens than a typical single-round reasoning task and **1200x** more tokens than a multi-round chatting task"

其他一手数字：
- "**input tokens rather than output tokens driving the overall cost**"
- 方差：摘要说同题不同次 "differ by up to **30×**"；正文说典型 "the most expensive runs **double** the token and monetary cost of the least expensive"（2× 是常态，30× 是极值）
- 最贵题比最便宜题平均多 **~700 万 token**
- **模型预测自己 token 用量的相关性只有 0.39，且系统性低估** —— 别信 agent 自报的成本估计

### 2.4 子 agent 扇出的成本结构 —— 对本机 3818 场扇出会话最相关

**（A）唯一一份公开的 Claude Code 扇出实测**【测，但可信度需校准】
https://systima.ai/blog/subagent-tax 《The Subagent Tax》，2026-07-22，Systima。
方法：自建开源本地代理 Meridian 桥接 Claude Max/Pro 订阅做请求/响应日志；同一任务三路对照（顺序 / 2 子 agent / 5 子 agent），隔离工作区；计量**累计 metered input tokens**，区分 cache read 与 cache write。

| 对照 | Opus | Fable 5 |
|---|---|---|
| 2 子 agent vs 顺序 | **2.6×** | **5.9×** |
| 5 子 agent vs 顺序 | **3.2×** | **4.7×** |

- 绝对值（Opus，2 子 agent）：顺序 **295,271** → 扇出 **762,226** metered input tokens
- 每个子 agent 自带 system prompt：Sonnet 3,554 / Opus 3,981 / Fable 4,509 字符，**各带 27 个工具里的 24 个**
- **缓存击穿实例**：「一个 Haiku 子 agent 比兄弟晚 6 秒启动，零 cache read 写满 **52,022** token 前缀；一个 Fable 子 agent 晚 12 秒，miss 后写了 **40,829** token」
- 钉到 Haiku 的对照：762,226 token / 8m00s / 8 请求 → **481,387** token / 3m45s / 3 请求（**少 37% input token，时间不到一半**）
- 墙钟时间（Opus）：顺序 4m15s、2 子 agent **8m00s**、5 子 agent 4m45s —— 原文 **"The speed argument never showed up"**

⚠️ **可信度校准**：作者称数据「checkable rather than asserted」并给了 SHA-256 哈希链和仓库 `systima-ai/agentic-coding-tools-comparison`。
经 GitHub API 核实：**仓库存在（2026-07-13 建，7 stars）但只有 19 KB，最后 push 2026-07-13 —— 原始 trace 并未真正公开**，作者自己说 raw captures 留待「future release」。
作者另主动披露：网关偶尔把 Fable 换成 Opus 且无标记；cache 归因「正是网关最可能扭曲的那个测量」。
**且这是一家卖成本优化服务的公司发的。→ 方向可信、数量级可用，但不是可复现证据。**

**（B）扇出的冗余到底有多大**【测】
arXiv 2604.03143《TokenDance》，2026-04-03（北大 + 上交）：
8-agent GenerativeAgents 一轮内 **"pairwise block similarity ranges from 91% to 97%"** —— 绝大多数 KV cache 在子 agent 之间是重复的。
单卡 A100-80GB 跑 Qwen2.5-14B 时，多智能体负载吃掉 **41.5 GiB KV cache（占池 99.3%）**，独立请求只用 24.8 GiB（59.2%）。

**（C）扇出常花 10× 换负收益**【测】
arXiv 2606.13003《The Illusion of Multi-Agent Advantage》，2026-06-16（Salesforce 系，Shafiq Joty 等）。
4 benchmark × 4 模型 × 6 个自动 MAS 框架。Table 4 实测美元（GPT-5，整套跑完）：

| Benchmark | CoT-SC | 最佳 MAS |
|---|---|---|
| GPQA-Diamond | 87.35% @ **$46.39** | DyLAN 82.33% @ $37.60 |
| HLE-Maths | 33.92% @ **$116.20** | MAS-Zero 38.20% @ **$1,288.30** |
| SWE-Bench Lite | 57.09% @ **$286.40** | DyLAN 55.97% @ $227.40 |
| BrowseComp-Plus | 83.92% @ **$66.80** | DyLAN 76.19% @ $46.00 |

原文：「Automated MAS frequently incur **10× inference costs** vs. SAS baselines for negligible gains.」

arXiv 2607.27942（**慕尼黑工业大学**），2026-07-30，terminal-bench 80+ 任务，Table I（GPT-5-mini）：

| 配置 | 准确率 | 成本 |
|---|---|---|
| Singleton | 0.296 | 基线 |
| MAS-S | 0.341 (+15.2%) | 1× |
| MAS-M | 0.348 (+2.2%) | **1.4×** |
| MAS-L | 0.315 (**−9.7%**) | **3.2×** |

原文：「costs scaled **approximately linearly** with architectural complexity」。MAS-L 成本翻 3.2 倍、准确率反而掉，agent 超时数从 3.33 涨到 50.0。

arXiv 2604.02460（Stanford，Dat Tran & Douwe Kiela），2026-04-11：**卡死相同 thinking token 预算**下，
「SAS is the best-performing system or statistically indistinguishable from the best **for all budgets except the lowest one**」。
理论依据是 Data Processing Inequality —— 每次 agent 间交接只会丢信息。

### 2.5 工具调用回灌上下文的占比 —— 本节数据最扎实的一项

**（A）84%**【测】arXiv 2508.21433《The Complexity Trap》，2025-08-29，**JetBrains Research + 慕尼黑工业大学**。
原文（Introduction §1，配 Figure 1）：
> "Concretely, **observation tokens make up around 84% of an average SWE-agent turn** (Figure 1) in our preliminary experiments (Section D.4) on **SWE-bench Lite-50**."

⚠️ 这是 preliminary experiment，样本是 SWE-bench Lite 的 50 题子集，正文未指明所用模型。

同篇成本数字（Qwen3-Coder 480B，SWE-bench Verified 全 500 题）：
> Observation Masking **$0.61/instance**，比 Raw Agent 基线 **$1.29** 降 **52.7%**，也优于 LLM-Summary **$0.64**

解决率：Observation Masking **54.8% (±4.4)** vs LLM-Summary 53.8% (±4.2) —— **砍掉观察反而略微更准。**

**（B）>70%**【测】arXiv 2607.18213《SWE-Pruner Pro》，2026-07-20（上海交大）：
> "**file-reading commands account for over 70% of the tokens consumed by Mini-SWE-Agent backed by Claude Sonnet 4.5**"（SWE-Bench Verified）

配套：训练数据标注的 mean keep-rate ≈ **30%**；SWE-Bench Verified 上 MiMo-V2-Flash 解决率 326/500 → 345/500（**+3.8%**），
但 Qwen3-Coder-Next 341/500 → 335/500（**−1.2%**）；剪枝调用额外增加 **15.0% 墙钟时间**。

**（C）反向验证：砍掉工具历史能省多少**【测】arXiv 2606.10209《Less Context, Better Agents》，2026-06-08。
Microsoft Dynamics 365 F&O 差旅费用自动分项，MCP 工具，GPT-5，50 任务，5 次独立运行取平均：

| 策略 | 完成率 | Token | 运行时间 |
|---|---|---|---|
| 无 user model 基线 | 8.0% | — | — |
| **全量保留历史** | 71.0% | **1,480,996** | 14.56 h |
| **只留最近 5 对工具调用/响应** | **79.0%** | **535,274** | 5.39 h |
| 剪枝 + 自动摘要 | **91.6%** | 553,374 | 5.79 h |

**只保留最近 5 对工具交互 = token 砍掉 63.9%，完成率反而从 71% 升到 79%。**

**（D）其他角度的分解**【测】
- arXiv 2601.14470《Tokenomics》，2026-01-20：ChatDev + GPT-5 跑 30 个真实开发任务，按 SDLC 阶段拆 ——
  **Code Review 阶段独占 59.4% 的 token**，input 占 53.9%。成本不在初次生成代码，在自动化的复查与验证。
- arXiv 2605.14558（UIC 等）：Sokoban/FrozenLake/Sudoku/WebShop 上，
  **真正的 action token 只占生成 token 的 2.6%–15.3%**，其余 84.7%–97.4% 是 reasoning。
- arXiv 2605.26297 输出侧：thinking token 占比 Gemma 45.8–67.6% / Qwen 29.0–40.7%；
  tool-call token 占比 Gemma Instant **87.8–98.2%**。

> **与本机数据的合流**：这三份实测说的是「**上下文里 84% 是工具回包**」，
> 本机数据说的是「**账单里 78% 是重读上下文**」。两者是同一件事的两端 ——
> 工具回包堆进上下文，然后每一轮把整个上下文再读一遍。
> 本机 `cache_read ÷ tool call = 696,455` vs `fresh(in+out) ÷ tool call = 2,739`（**254 倍**）正是这条链路的量化（§4.6）。
> 而《Complexity Trap》和《Less Context》两份实测同时给出：**砍掉这部分，准确率不降反升**（54.8% vs 53.8%；79.0% vs 71.0%）。

### 2.6 Benchmark 的每任务成本报告

**Terminal-Bench 官方榜** https://www.tbench.ai/leaderboard/terminal-bench/2.1（提交窗口 2026-05-01 至 2026-07-11）

| 排名 | Agent | Model | 准确率 | Cost |
|---|---|---|---|---|
| 1 | Claude Code | Fable 5 (xhigh) | 83.8% ±1.2% | **$552.67** |
| 2 | Codex | GPT-5.5 (xhigh) | 83.1% ±1.1% | **$2,059.19** |
| 3 | Terminus 2 | Fable 5 (high) | 80.4% ±1.2% | $438.64 |
| 4 | Cursor CLI | Grok 4.5 (high) | 79.3% ±1.5% | **$134.09** |
| 5 | Claude Code | Opus 4.8 (high) | 78.9% ±1.3% | $286.94 |

⚠️ **页面本身没说明 Cost 是整套总额还是单任务均价，也没有任何计费方法论说明。**
同期 Terminal-Bench 论文（arXiv 2601.11868）说「Running Terminal-Bench 2.0 costs anywhere from **one to a hundred dollars**」，
与 $2,059 对不上 —— 榜单数字大概率是多次重复运行的累计。**引用前必须自己确认单位。**

**HAL / Princeton PLI SWE-bench Verified Mini** https://hal.cs.princeton.edu/swebench_verified_mini （**50 题子集**）
方法论原文：「Total API cost for running the agent on all tasks」、
**「Costs are currently calculated without accounting for caching benefits」**（按未缓存全价算，偏高）：

| Agent | Model | 准确率 | 总成本(50题) | 折合每题 |
|---|---|---|---|---|
| SWE-Agent | Claude Sonnet 4.5 High | 72.00% | $463.90 | ~$9.3 |
| SWE-Agent | Claude Opus 4.1 | 61.00% ±7.00% | $1,351.35 ±$438.32 | ~$27 |
| SWE-Agent | GPT-5 Medium | 46.00% | $162.93 | ~$3.3 |
| SWE-Agent | Gemini 2.0 Flash | 24.00% | $4.72 | ~$0.09 |
| HAL Generalist | o3 Medium | **0.00%** | **$585.71** | **花钱零产出** |

HAL 论文（arXiv 2510.11977，ICLR 2026）整体：总评测成本 **~$40,000**、**21,730 次 rollout**、**25 亿 token**；
结论「**the most costly models are rarely on the Pareto frontier**」。

**Aider Polyglot 榜**（页面标注 last updated **2025-11-20**，已停更，无 2026 模型）225 道 Exercism 题：

| Model | 正确率 | 总成本 | 折合每题 |
|---|---|---|---|
| gpt-5 (high) | 88.0% | $29.08 | ~$0.13 |
| o3-pro (high) | 84.9% | **$146.32** | ~$0.65 |
| **DeepSeek-V3.2-Exp** | 74.2% | **$1.30** | **~$0.006** |
| claude-opus-4 (32k thinking) | 72.0% | $65.75 | ~$0.29 |

其他：
- **SWE-bench 官方榜（swebench.com/verified.html）确认无成本列**，只有资源上限约束（2M uncached token、20M cached token reads）
- **Anthropic 官方 SWE-bench 博客仅定性**：「many successful runs took hundreds of turns... and **>100k tokens**」，无美元数字
- **METR Expenditure Horizon**（2026-07-21）：关键提醒「**experiment cost comprised around 70-90% of the cost of most trajectories**」——
  在训练类任务里算力成本远超 token 成本；测的是 NanoGPT 提速竞赛不是修 issue，与编码 agent 不可类比

⚠️ **另有一份看似相关但不可比的**：PACE 论文（arXiv 2607.02032，CMU/LTI）给 Claude Sonnet 4.5 每实例 SWE-bench Verified **$1.19** ——
**不可与 HAL 的 ~$9 直接比**，PACE 用的是非 agentic 单步评测，论文自己说目标是做到全量 agentic 评测成本的「much less than 1%」。

### 2.7 长上下文质量衰减（context rot）的实测

**NoLiMa —— 数字最完整、最可引用的一份**【测】
arXiv 2502.05167（**Adobe Research + LMU Munich**），ICML 2025，GitHub `adobe-research/NoLiMa`。
方法：构造**字面零重叠**的 needle-question 对，逼模型做隐性关联而非字面检索；12 个宣称支持 ≥128K 的模型。
**effective length 定义 = 仍能维持 base 分数 ≥85% 的最长长度。**

摘要原文：「At 32K, for instance, **10 models drop below 50% of their strong short-length baselines**.」

Table 3（准确率 %）：

| Model | Base | 1K | 8K | 16K | **32K** | Effective |
|---|---|---|---|---|---|---|
| GPT-4o | 99.3 | 98.1 | 89.2 | 81.6 | **69.7** | 8K |
| Llama 3.3 70B | 97.3 | 94.2 | 72.1 | 59.5 | **42.7** | 2K |
| Gemini 1.5 Pro | 92.6 | 86.4 | 63.9 | 55.5 | **48.2** | 2K |
| **Claude 3.5 Sonnet** | 87.6 | 85.4 | 61.7 | 45.7 | **29.8** | **4K** |
| Command R+ | 90.9 | 77.0 | 39.5 | 21.3 | **7.4** | <<1K |
| Llama 3.1 8B | 76.7 | 65.7 | 31.9 | 22.6 | **14.2** | 1K |

**RULER**（NVIDIA，arXiv 2404.06654，GitHub 持续更新）—— 宣称长度 vs 实测有效长度的落差：
原文「**only half of them can maintain satisfactory performance at the length of 32K**」

| Model | 宣称 | Effective | 128K |
|---|---|---|---|
| Gemini-1.5-pro | 1M | >128K | 94.4 |
| GPT-4-1106-preview | 128K | **64K** | 81.2 |
| Llama3.1(70B) | 128K | 64K | **66.6** |
| **Yi(34B)** | **200K** | **32K** | 77.3 |
| Mistral-Large-2407 | 128K | 32K | **23.7** |
| LongChat | 32K | **<4K** | **0.0** |

**Lost in the Middle**（arXiv 2307.03172，Stanford/Berkeley，TACL）Table 6（20 篇文档）：
GPT-3.5-Turbo 首位 75.8% → 中间 **53.8%** → 末位 63.2%（首→中降 **22.0 个百分点**）。
⚠️ U 型曲线**不是所有模型都有**：Claude-1.3 是 59.9/56.8/60.1，相当平坦，原文称其「is not as susceptible to the position of relevant information」。

**⚠️ Chroma Context Rot 报告：没有可引用的准确率表**
https://research.trychroma.com/context-rot（2025-07-14，Kelly Hong, Anton Troynikov, Jeff Huber）测了 18 个模型，
但**报告主体以折线/散点图呈现，正文几乎没有「某模型在某 token 数下准确率 X%」式的表格**。
能一手引用的具体数字只有拒答率：Repeated Words 任务上 GPT-3.5 Turbo 拒答 **60.29%**、Claude Opus 4 **2.89%**、GPT-4.1 **2.55%**。

可引用的定性结论（原文）：
> "Models do not use their context uniformly; instead, their performance grows increasingly unreliable as input length grows."
> "**Even a single distractor** reduces performance relative to the baseline... adding four distractors compounds degradation further."
> "Models perform worse when the haystack **preserves a logical flow** of ideas. Shuffling the haystack... consistently improves performance."（反直觉）

⚠️ 网上流传的「10k→100k 准确率掉 20–50%」「相关事实在第 5–15 篇时掉 30+ 个百分点」等**全部是三方读图估算，原报告无此表述**。

### 2.8 ⚠️ 三个流传很广但站不住的数字 —— 别用

| 说法 | 出处 | 判定 |
|---|---|---|
| 「**80% of context is consumed by file reads and tool results, 20% by your messages**」 | SFEIR Institute 的 Claude Code FAQ | ❌ **零出处、零方法论、页面连日期都没有**。数字碰巧接近 §2.5 的 84%，但它不是证据 |
| 「**150,000 tokens → 2,000 tokens，节省 98.7%**」 | Anthropic《Code execution with MCP》，2025-11-04 | ❌ 核实为 **illustrative example（举例说明），不是实测案例**。同文的「2 小时销售会议 50,000 token」同样是假设情景。**Anthropic 在这篇里没给任何实测的工具定义 token 开销** |
| ai-cost-estimator.com 的「Real Data Breakdown」 | 该站自售成本计算器 | ❌ 零方法论、零样本量、零出处，**判定为营销内容** |

**另一条负面结论值得记**：Anthropic《Effective context engineering for AI agents》（2025-09-29）**通篇零个实测数字**。
它引用了 Chroma 的 context rot 报告但不转述任何百分比，只给定性指导（"attention budget"、"a performance gradient rather than a hard cliff"）。
**想从 Anthropic 官方拿 context 退化的数字，这篇拿不到。**

---

## 3. 现有 `metrics.py` / `taxonomy.py` / `aei.py` 口径的问题清单

**先给结论**：现有口径把 **88.3% 的账单**排除在"成本"之外，把**单价最高的那类 token** 完全不显示，
并把 **94.5% 的 token 量记在了错误的日子上**。下面逐条给证据。

### P0 —— **`extract.py` 把每个 API 响应重复计了 2.48 次，所有绝对量虚高 2.4–3.6 倍**（最严重，先修这条）

这是本轮唯一一条**代码 bug**（其余都是口径问题）。它推翻了下面几乎所有绝对数字。

`extract.py:317-320` 对**每一条** JSONL 记录做累加：
```python
if isinstance(u, dict):
    rec["tok_in"]       += int(u.get("input_tokens") or 0)
    rec["tok_out"]      += int(u.get("output_tokens") or 0)
    rec["tok_cache_r"]  += int(u.get("cache_read_input_tokens") or 0)
    rec["tok_cache_w"]  += int(u.get("cache_creation_input_tokens") or 0)
```
**但一个 API 响应在 JSONL 里不是一条记录。**

**直接扫 `~/.claude/projects/` 全部 1,528 个 transcript 实测**：

| | |
|---|---|
| `extract.py` 累加过的 usage 记录数 | **322,284** |
| **实际不同的 `message.id`（= 真实 API 响应数）** | **130,138** |
| **每个 API 响应被计了** | **2.48 次** |

**两个互相独立的重复来源**（在同一份数据里都抓到了实证）：

**(1) 一个 API 响应按 content block 拆成多行，每行都带完整的 `usage`**
`msg_011CdcoGR1iGkKzYJYK8bg7v` 在同一个文件里出现 **14 次**。前 4 次逐行如下：
```
line 26112 uuid=6f926869 stop=tool_use blocks=['thinking']  cr=778766 out=4122
line 26113 uuid=0ccf5c7d stop=tool_use blocks=['tool_use']  cr=778766 out=4122
line 26115 uuid=86e4b904 stop=tool_use blocks=['tool_use']  cr=778766 out=4122
line 26117 uuid=c1a02ece stop=tool_use blocks=['tool_use']  cr=778766 out=4122
```
一个 assistant 消息带 1 个 `thinking` + 6 个并行 `tool_use`，就变成 **7 行，每行都写着同一份 `cr=778766`**。
`+=` 于是把这次响应的 778,766 个 cache_read **算了 7 遍**。

> ⚠️ **推论（这条最要命）**：**一轮里并行工具调用越多，虚高越厉害。**
> 也就是说**最 agentic 的会话虚高最狠** —— 虚高倍数和"这场会话有多像 agent"正相关。

**(2) 会话 resume 时把历史重放进同一个文件**
同一组 14 条记录分成两批：行 **26112–26123** 和行 **29399–29410**。整组又来了一遍。

**实测虚高倍数（全语料，按 `message.id` 去重前后对比）**：

| 类别 | 现在算出来的 | **去重后** | **虚高** |
|---|---|---|---|
| fresh input | 2,704,599 | **742,782** | **3.64×** |
| **cache_read** | **135,709,715,359** | **56,374,433,563** | **2.41×** |
| **cache_write** | **1,476,522,068** | **490,323,862** | **3.01×** |
| output | 358,849,297 | **116,426,151** | **3.08×** |

**按已核实的 Opus 5 单价折算**：

| | 现在算出来的 | **去重后** |
|---|---|---|
| 账单合计 | **$86,068** | **$34,166** |
| 每条提交（762 条） | $112.95 | **$44.84** |

**→ 整体虚高 2.52 倍。**

**单场虚高倍数从 1× 到 4.99× 不等**（最差的几场：4.99×、4.24×、3.62×、3.23×、2.85×）。
**因为虚高不均匀，所有按天/周/来源/项目的排序都被非均匀地扭曲了** —— 不是整体乘个常数就能修好。

#### 为什么这个 bug 一直没被发现

**因为命中率对它免疫。** 四类 token 一起虚高，比值几乎不变：

| | 现在 | 去重后 |
|---|---|---|
| `cached/(in+cached)` | 99.998007% | **99.998682%** |
| `cached/(in+cached+write)` | 98.9218% | **99.1364%** |

看板上最醒目的那个 KPI（缓存命中率）**在 bug 面前纹丝不动**。
这正是 memory 里 `partial-scope-passing-as-global` 那条的另一种形态：
**一个不会因为数据错了而变化的指标，也不会因为数据对了而变化 —— 它不承载信息。**

#### 修法

按 `(会话文件, message.id)` 去重后再累加 —— 每个 API 响应的 `usage` 只取一次。
`message.id` 由 Anthropic 侧生成，一次响应一个，是天然的幂等键。
⚠️ 注意 **codex 那条支路不受影响**（`extract.py:386` 用的是 `max()` 而不是 `+=`，
取累计值的最大值，天然免疫重复）—— 所以**修完之后 claude-code 会大幅下降、codex 不变**，
两者的相对关系会翻转。**改口径时必须同时给新旧对照，否则会被误读成"用量突然降了"。**

---

### 本机实测底数（快照 2826 场，2026-08-20 计算）

> ⚠️ **下面这一节以及 §3 / §4 里全部来自快照的绝对数字，都是「未去重」口径**
> —— 因为它们来自同一个有 P0 bug 的 `extract.py` 产物。
> **按 P0 实测，真实量约为这些数字的 1/2.4 ~ 1/3.6，且各场不均匀。**
> 保留原值是为了让每条批评能对上看板上现在显示的数；
> **凡是涉及"多少"的结论都要按 P0 打折，凡是涉及"结构占比"的结论不受影响**（四类一起虚高，占比几乎不变）。

```
tok_in (不含缓存)      160,701,495
cache_read         138,218,494,218
cache_write          1,431,683,412      ← 是 tok_in 的 8.91 倍
tok_out                382,783,962
input_total(现口径)  138,379,195,713
```

按 §1.2 已核实的 Anthropic 单价折算（Opus 5，5m 缓存）：

| 类别 | 量 | 金额 | **占账单** |
|---|---|---|---|
| fresh input | 160.7M | $804 | **0.91%** |
| **cache READ** | **138.22B** | **$69,109** | **78.15%** |
| **cache WRITE** | **1.432B** | **$8,948** | **10.12%** |
| output | 382.8M | $9,570 | **10.82%** |
| **合计** | | **$88,430** | 100% |

（Sonnet 5 口径 $35,372；Haiku 4.5 口径 $17,686。占比在三档完全相同，因为四类的相对倍数在每一档都一样。）

---

### P1 —— `cost_tokens = tok_in + tok_out` 只覆盖 11.7% 的账单（严重）

`aei.py:289`：
```python
def cost_tokens(s: dict) -> int:
    return s.get("tok_in", 0) + s.get("tok_out", 0)
```
注释给的理由是："缓存读取虽然计费，但单价低一个数量级……把它算进 ROI，「每条提交 1.85 亿 token」这种荒谬数字就出来了。"

**单价判断是对的，结论是反的。** 单价确实是 0.1x（Anthropic 官方原文，§1.2 已核）。
但**量比是 860 : 1**（138.22B vs 160.7M）。0.1 × 860 = **86** —— 缓存读取的账单是 fresh input 的 86 倍。

这个口径覆盖 `fresh input 0.91% + output 10.82% = **11.73%**`，
**主动排除掉的 88.27% 恰恰是钱所在的地方。**

而且它还把 output 当 1x 记 —— **output 在每一档 Anthropic 模型上都是 input 的 5 倍**（Opus 5: $5 in / $25 out）。
所以即使在它覆盖的那 11.73% 里面，两项的相对权重也是错的。

**正确的修法不是"排除"，是"价格加权"。** "1.85 亿 token/commit 很荒谬"这个直觉本身是对的 ——
荒谬的不是这个数，是**把四类单价差 50 倍的 token 当同一单位相加**。折算后是 $116.05/commit（见 P5），
这个数一点都不荒谬，它是可以拿去和"我自己干这个 commit 要花多少小时"直接比的。

---

### P2 —— `cache_write` 采了、算了、但**从来不显示**，而它是单价最高的输入 token（严重）

`metrics.py:53`、`taxonomy.py:105`：
```python
raw_in = b["input_excl"] + b["cached"]
b["input_total"] = raw_in
```
`cache_write` 被累加进 `b["cache_write"]`（`metrics.py:48`、`taxonomy.py:99`），
但**不进 `input_total`**，并且 —— grep 全部 `web/` 目录，`cache_write` **零命中**。
UI 上出现的只有 `input_total` / `cached` / `hit_rate` / `output`。

后果：
- **1,431,683,412 个 token 在看板上完全不存在**，而它是 fresh input 的 **8.91 倍**
- 按 Opus 5：这块 **$8,948**，是能看见的那块 fresh input（$804）的 **11.1 倍**
- 它占总账单 **10.12%**，比 output 少不了多少，但 output 显示了、它没有

`stack.js:17` 写的是「读进去的（含缓存）」+「其中重复读的缓存 」—— 措辞诚实，
但"含缓存"里的"缓存"只含 read 不含 write。看板上没有任何一处能让人发现缺了一块。

---

### P3 —— `hit_rate` 分母排除 cache_write，命中率被系统性抬高（严重）

`metrics.py:57`、`taxonomy.py:108`：
```python
b["hit_rate"] = (b["cached"] / raw_in) if raw_in else None   # raw_in = input_excl + cached
```

**cache_write 在结构上就是一次 miss** —— 那是模型必须从头处理的内容，而且是按 1.25x 溢价处理的。
把它既不算 hit 也不算 miss，等于把最贵的那类 miss 从分母里拿掉。

全量对照：

| 口径 | 命中率 |
|---|---|
| 现口径 `cached / (in + cached)` | **99.8839%** |
| 诚实口径 `cached / (in + cached + write)` | **98.8610%** |
| "真正新读进来的" `(in + write + out) / 全部` | **1.4089%** |

**claude-code 单独看，问题放大到荒谬**：

| | 值 |
|---|---|
| 显示的命中率 | **99.99798%** |
| 显示的未命中 | **0.00202%** |
| 真实 fresh input（`tok_in + cache_write`） | **1,434,373,005** |
| 诚实的 fresh 占比 | **1.0644%** |
| **显示的 miss 把 fresh input 低估了** | **533 倍** |

这就是"99.88% 命中率"这个数字的真面目：**它不是一个效率指标，它是一个恒等式。**
Claude Code 的 `input_tokens` 字段本身就定义为"扣掉 cache read 和 cache creation 之后的残值"，
所以 `cached/(input_excl+cached)` 被**定义为**趋近 100%，不管你的上下文管理做得多好多差。
一个不可能变差的指标，是不能用来做决策的。

---

### P4 —— 跨 harness 的命中率不可比，但并排展示在同一张表里（严重）

`taxonomy.summarize()` 的输出被 `stack.js:31-44` 渲染成 harness / provider / model 三张并排的表，每行一个 `rate(r.hit_rate)`。
实测三个来源：

| source | 场次 | measured | tok_in | cache_read | **cache_write** | 显示的 hit |
|---|---|---|---|---|---|---|
| claude-code | 1501 | 1455 | 2,689,593 | 133,326,066,141 | **1,431,683,412** | **99.9980%** |
| codex | 455 | 349 | 140,100,566 | 3,796,440,064 | **0** | **96.4410%** |
| kimi-code | 432 | 430 | 17,911,336 | 1,095,988,013 | **0** | **98.3920%** |

三个问题叠在一起：

1. **分子分母的定义不同**。claude-code 的 `input_tokens` 是残值（原生不含缓存）；
   codex 走的是 `extract.py:386` 的 `int(inp) - int(cached)`，是另一种残值。
   代码注释里明确写了这两家口径不同并做了对齐 —— 对齐的是**总量**，但**没对齐命中率的语义**。
2. **codex 和 kimi 的 `cache_write` 恒为 0，不是"没有缓存写入"，是"没有这个字段可读"。**
   在 UI 上这两家会显得比 claude-code"更干净"，纯属测量缺口。
3. **在 OpenAI 侧这个 0 还有第二层歧义**：按 §1.3，GPT-5.6 之前 cache write **真的免费**，5.6 起收 1.25x。
   所以 codex 的 0 在早期模型上是"真 0 成本"，在 5.6 之后是"漏计"。同一个 0，两种意思。

**并排比较等于拿三把不同刻度的尺子量三个人，然后宣布谁最高。**

---

### P5 —— `tokens_per_commit` 分子是子集、分母是全集（严重）

`aei.py:443`：
```python
tot_tok = sum(cost_tokens(s) for s in hum)      # 只有 kind == "human" 的会话
...
"tokens_per_commit": int(tot_tok / max(1, t["commits"])),   # t["commits"] 是全部提交
```

`hum` 在 `aei.build()` 开头就过滤成 `kind == "human"`；而 `t["commits"]` 来自 `delivery_block`，
数的是 GitHub 上**全部**提交，不区分是谁的会话产出的。

**实测复算确认**：`529,523,914 ÷ 762 = 694,913` —— 与 parent 给的"约 69.5 万"逐位吻合，
证实这就是看板上那个数的算法（本快照 762 条提交）。

这正是 memory 里那条 `partial-scope-passing-as-global` 的形态：
本快照 732 场 auto 会话（parent 说的新数据里是 3818 场）烧掉的 token 完全没进分子，
但它们产出的提交进了分母。**扇出规模越大，这个数被低估得越狠。**

| 口径 | 每条提交 |
|---|---|
| 现口径（human-only，in+out，不加权，未去重） | **694,913 token** |
| 价格加权 + 全会话 + **未去重**（Opus 5） | **$116.05** |
| **价格加权 + 全会话 + 按 `message.id` 去重（Opus 5）** | **$44.84** ← 最接近真实的一个 |
| 同上（Sonnet 5 折算） | 约 $17.9 |
| 同上（Haiku 4.5 折算） | 约 $9.0 |

两个方向的误差在这个数上**部分相消**：漏掉 88% 的账单让它偏小，P0 虚高 ~3 倍让它偏大。
**相消不等于抵消 —— 两个都错的东西凑出来的数没有意义**，必须两个都修。

---

### P6 —— 按会话 **start 日**归集，94.5% 的 token 记在了错误的日子（严重，且直接影响 parent 引用的那个结论）

`metrics.py:69-72`：
```python
d = local_dt(s.get("start", ""))
...
day = d.date().isoformat()
_fold(by_day[day], s)
```
一场会话的全部 token 都被记到它**开始**的那一天，不管它跑了多久。

实测：

| | |
|---|---|
| end 日 ≠ start 日的会话 | **194 场（6.9%）** |
| 这些会话装着的 input_total | **130,710,001,320 = 全部的 94.5%** |
| 跨度分布（天） | 1天:92, 2天:32, 3天:13 … 最长 **198 天** |
| 时长 > 24h 的会话 | **110 场**，装着 **93.0% 的 cache_read** |
| 会话时长中位数 | **0.03 小时**（不到 2 分钟） |
| p90 | 0.85 小时 |

**最极端的一场**：
```
source=claude-code  kind=human
start = 2026-07-25 17:25 UTC     end = 2026-08-19 09:30 UTC     duration = 24 天 16 小时
turns = 1104    tools = 32111    cache_read = 34,598,043,804
```
**这一场就是 2026-07-25 那天 input_total 的 99.7%**，也是全部 cache_read 的 **25.03%**。
按 Opus 5 命中价 $0.50/MTok 算，**这一场 = $17,299**。

所以 `calendar.js` / `day.js` 上那句「这天读进 XXX 亿 token」实际说的是
「**这天开始了一场后来跑了 24 天的会话**」。

⚠️ **对 parent 那个结论的直接影响**：「某一天读进 130 亿 token，当天 0 次 git 提交」
—— 2026-07-14 的 13,077,938,159 正是这个量级。**这个结论极可能是归集假象**：
那天真正消耗的可能只是那 130 亿里的一小段，其余分布在之后几天/几周。
"当天 0 次提交"就更站不住了 —— 一场会话跨 24 天，你不能拿它开始那天的提交数去评判它。

**顺带一条**：24 天、1104 turns、32111 tools 的"一场会话"几乎必然是
`--continue` / `--resume` 反复追加到同一个 JSONL 文件。**Claude Code 的"一个 session 文件" ≠ "一次对话"**，
所以"会话"作为分析单位在这个来源上是坏的。

---

### P7 —— 极端集中：所有"按天/周/时段/来源"的平均都被极少数会话绑架（严重）

cache_read 的集中度实测：

| | 占全部 cache_read |
|---|---|
| top **1** 场 | **25.03%** |
| top **5** 场 | **60.01%** |
| top **10** 场 | **78.77%** |
| top **25** 场 | **92.90%** |
| top 50 场 | 96.31% |
| top 100 场 | 97.83% |

`by_day` / `by_week` / `by_slice` / `by_source` 的柱状图，画的不是"哪天忙"，
而是"**那 10 场大会话落在哪个格子里**"。加上 P6 的 start-日归集，两个偏差叠乘。

会话时长是**双峰**的：中位数 0.03h vs 110 场 >24h。
在双峰分布上，任何"平均每场 XXX"都是在两个峰之间取了一个**不存在的中点**。

---

### P8 —— 人机边界在不同来源上含义不同（中等，但会污染所有 `hum` 口径）

`extract.py:769-773`：
```python
rec["kind"] = session_kind(rec)
# DSH 的 origin=subagent 是 agent 自己派生的子会话 —— 1937 场里 1929 场是这个。
if rec.get("dsh_origin") == "subagent":
    rec["kind"] = "auto"
```

**DSH 的扇出被单独识别并剔出 `hum`；Claude Code 侧则完全没有对应处理。**

⚠️ **我先给出一个假设，然后自己实测推翻了它，两边都记下来** ——
我原本推断"Claude Code 的子 agent 消息带 `isSidechain: true` 写在同一个 session JSONL 里，
所以扇出 token 被折进了父会话"。**实测不成立**：
扫 `~/.claude/projects/` 的大 transcript，`isSidechain` 字段**存在但全部是 `false`**
（6,718 次出现，`true` 零次）。

**实测到的真实情况是另一回事，而且更难办**：
在那场 165,169 行的大会话里，`agentId`(649) / `agentType`(186) / `subagent_type`(642) 都出现了，
说明**确实发生过扇出**；但逐条检查 69,162 条带 `usage` 的记录，
**被 `agentId` / `agentType` 标记的是 0 条**：

```
usage records tagged with agentId/agentType : 0
usage records NOT tagged (main thread)      : 69,162
cache_read  subagent=0   main=34,598,043,804   subagent share=0.00%
```

→ **子 agent 自己的 token 用量根本不在父会话文件里。**
`agentId` / `subagent_type` 只出现在 Task 调用的入参和回包里，不带 `usage`。

**所以结论要改成**：不是"扇出被错误地算进了 human"，而是
**Claude Code 的扇出 token 目前处于「不在父会话里、也没被识别成独立会话」的状态 —— 它是不可观测的。**

后果仍然成立且更严重：`economics_block` / `coupling_block` / `aei.build()` / `roi` 全部只跑 `hum`，
而 `hum` 在 DSH 上是"剔了扇出的"、在 Claude Code 上是"扇出根本没被看见的"。
**跨来源比较"人真的开口的会话"在语义上无效**，而且**Claude Code 那条线的真实成本被系统性低估**
（低估多少 = 扇出去了多少，这个数现在算不出来）。

⚠️ 配套缺口：输出的 sessions.jsonl 里**没有 `tool_names` 字段**
（`extract.py` 内部有 `rec["tool_names"]`，写出时被裁掉了），
所以连"这场会话调了几次 Task"都看不到。
**先补 `tool_names` + 按 `agentId` 关联子会话文件，扇出规模才谈得上可观测**（§6.M5 的前置条件）。

---

### P9 —— 20.9% 的会话没有任何用量记录，却仍留在会话类分母里（中等）

| source | measured=0 的场次 |
|---|---|
| chatgpt | **379**（结构上永远不会有 token —— 导出格式里就没有 usage 字段） |
| codex | 106 |
| claude-code | 46 |
| claude-desktop | 38 |
| dws | 12 |
| openchatcut | 9 |
| **合计** | **592 / 2826 = 20.9%** |

**做得对的部分**：`metrics.py:113` 的 `no_usage` 和 `_close()` 的 `unmeasured` 有报出来，
`stack.js:18` 也渲染了「有用量记录 N 场 / 没记录 M 场」。分母为 0 时写 `None` 而不是 `0`（`metrics.py:57` 的注释说得很对）也是对的。

**问题在别处**：`economics_block` 的 `mode_share`、`hhi_topic_all`、`tools_per_turn`，
以及 `roi` 里的 `sessions_per_commit`，分母都是**会话数**，把这 592 场算进去了。
chatgpt 的 379 场和有用量的会话放进同一个分母，任何"每场平均"都被稀释了 20.9%。
`taxonomy.py` 已经把 dws / openchatcut 标成 `kind="tool"` 并单独列（做得对），
但 chatgpt 被标成 `kind="llm"`，它的 379 场就混进去了。

---

### P10 —— `taxonomy` 按模型数**均分** token，在没有依据的情况下编了一个分布（中等）

`taxonomy.py:129-136`：
```python
# 一场会话可能换过模型。**按模型数均分**而不是每个都记全量，
# 否则总量会被放大成模型个数倍 —— 这是最容易做出的假数据。
w = 1.0 / len(mods)
for mo in mods:
    ...
    fold(by_p[prov], s, w)
```

**"避免放大"是对的，"均分"是错的。** 一场会话若 90% token 走 Opus、10% 走 Haiku，会被记成 50/50。
Opus 5 与 Haiku 4.5 的 input 是 $5 vs $1、output 是 $25 vs $5 —— **5 倍**。
只要 provider/model 那一屏后面接任何成本口径，误差就是 5 倍量级。

更诚实的做法是标「该会话跨了 N 个模型，token 无法归因」，把它放进一个显式的"不可归因"桶，
而不是编一个均匀分布。**"算不出"和"均分"在看板上长得一样，但意思完全不同** —— 这正是这份代码自己在
`metrics.py:55-57` 对 `hit_rate` 采取的态度（分母为 0 写 `None` 不写 `0`），只是没有一致地用在这里。

---

### P11 —— 固定 UTC+10 不处理夏令时（低，但会在 10 月引爆）

`metrics.py:13`：
```python
TZ_OFFSET_H = 10   # Owner 在悉尼。固定 +10，不猜夏令时 —— 猜错比差一小时更糟。
```

悉尼 10 月初至 4 月初是 **UTC+11**。本快照窗口（2026-05~08）恰好全在标准时内，**当前无影响**。
但窗口一旦跨过 10 月，日界就错一小时 —— 而在 P6/P7 那种极端集中的分布下，
**一小时足以把一场 346 亿 token 的会话整体挪到隔壁一天**。

"不猜"的判断是对的，"写死 +10"是错的实现 —— 正确做法是 `zoneinfo.ZoneInfo("Australia/Sydney")`，
那是查表不是猜。

---

### P12 —— 术语和实现相反：cache_write 才是"最新"的 token，却不在"新 token"里（低，但会误导读者）

`aei.py:449` 的 `cost_basis` 文案：
> "只算新 token（不含缓存命中的输入 + 输出）。"

而 `cache_write` 恰恰是**第一次被处理的内容** —— 它是四类里最"新"的那一类，
且按 1.25x 溢价计费。它不在这个"新 token"里。

`stack.js:17` 的措辞「读进去的（含缓存）」/「其中重复读的缓存」本身是准确的，
问题是「含缓存」的"缓存"只含 read。整个看板缺一个词来指 cache_write，于是它就消失了。

---

### 问题清单速查（按严重度）

| # | 问题 | 严重度 | 一句话 |
|---|---|---|---|
| **P0** | **每个 API 响应被重复累加 2.48 次** | **最严重（唯一的真 bug）** | **所有绝对量虚高 2.4–3.6 倍（账单 $86,068 → $34,166）；单场 1×–4.99× 不均匀；命中率对它免疫所以一直没被发现** |
| P1 | `cost_tokens = in + out` | 严重 | 只覆盖 11.73% 的账单，且 output 权重错 5 倍 |
| P2 | `cache_write` 从不显示 | 严重 | 1.43B token / $8,948 在看板上不存在，是可见 fresh input 的 11 倍 |
| P3 | `hit_rate` 分母排除 write | 严重 | 99.88% 是恒等式不是指标；claude-code 的 miss 低估 533 倍 |
| P4 | 跨 harness 命中率并排展示 | 严重 | 三把不同刻度的尺子；codex/kimi 的 write=0 是"没测"不是"没有" |
| P5 | `tokens_per_commit` 子集当全集 | 严重 | 分子 human-only、分母全部提交；实际是 $116/commit 不是 69.5 万 token |
| P6 | 按 start 日归集 | 严重 | 94.5% 的量记错了日子；单场跨 24 天占该日 99.7% |
| P7 | 极端集中未披露 | 严重 | top 1 场 = 25%，top 10 场 = 78.8%；所有平均值失效 |
| P8 | 扇出在 Claude Code 侧完全不可观测 | 中 | 子 agent 的 usage 不在父会话文件里、也没被识别成独立会话；该线成本被系统性低估，低估多少算不出来 |
| P9 | 20.9% 无用量会话留在分母 | 中 | `no_usage` 报了（对），但 mode_share/hhi/per_commit 的分母没扣 |
| P10 | 按模型数均分 token | 中 | 编了一个均匀分布；Opus↔Haiku 差 5 倍 |
| P11 | 固定 UTC+10 | 低 | 10 月起日界错一小时，在 P7 的分布下足以挪走一整场 |
| P12 | "新 token"术语与实现相反 | 低 | cache_write 是最新的 token，却不算"新" |

---

## 4. 更诚实的成本归因单位

每个单位给：它回答什么、**适用条件**、**失效条件**、本机数据下的取值。

### 4.1 价格加权 token（base-input-equivalent, BIE）

**算法**：`BIE = in×1.0 + cache_read×r + cache_write×W + out×(out价/in价)`（倍数按 provider 取）
**本机**：17.69B BIE（Anthropic 5m 口径）
**回答**：在同一家供应商内部，钱花在哪、趋势往哪走

- **适用**：同 provider 内部横比、日/周趋势、模型间比较（倍数结构在 Anthropic 三档完全一致，所以 BIE 在档间可比）
- **失效**：跨 provider 加总。DeepSeek 的 r = 0.032 不是 0.1，且 off-peak 再砍半；
  **Gemini 显式缓存根本装不进这个公式** —— 它的成本是"租金 × 小时"，与 token 量正交
- **失效**：模型混用 + P10 的均分归因同时存在时，误差 5 倍
- **失效**：跨 tokenizer 版本。Claude 4.7+ 换了 tokenizer，同样文本多约 30% token【官，§1.2】。
  BIE 跨版本比较会把 tokenizer 变更读成用量增长

### 4.2 直接美元

**本机**：$88,430（全按 Opus 5）/ $35,372（全按 Sonnet 5）/ $17,686（全按 Haiku 4.5）
**回答**：这个月花了多少 —— **唯一能跨 provider 加总的单位**

- **适用**：唯一能把 Anthropic + OpenAI + DeepSeek + SCNet 加在一起的单位；唯一能和"我自己干要多少小时"直接比的单位
- **失效**：单价会变。本轮就抓到两处刚变过（§1.2 Sonnet 5 转正、§1.3 OpenAI 5.6 起 write 收费）。
  → **必须把单价表版本化并记抓取日期；历史数据用当时的价重算，不能用今天的价重算历史**
- **失效（最容易被忽略的一条）**：**包月订阅下按量单价是虚拟的**。
  Claude Code Max / ChatGPT Plus 之类的定额套餐里，边际成本是 0，账单是固定的。
  这时美元口径给出的是**机会成本**（"如果按 API 计价会花多少"），不是**实付**。
  两者差几十倍，看板上必须标清楚是哪一个 —— 否则会有人拿一个从没发生过的账单去做决策
- **失效**：Batch API / off-peak / data residency 倍数没建模时，会系统性高估

### 4.3 每次交付的成本（per commit / per merged PR / per release）

**本机**：$116.05/commit（Opus 5 口径，全会话价格加权，762 条提交）
**回答**：进 git 的那部分产出有多贵

- **适用条件（三条必须同时满足，现在一条都不满足）**：
  1. 分子分母同口径 —— 现在不满足（P5）
  2. 产出确实进 git —— Excel、方案、视频、运维动作、这份调研本身，都不进
  3. 分母粒度可比 —— 1 行 typo 和 2000 行重构同为 1 commit
- **改进**：分母换成 **merged PR** 而不是 commit。PR 有 review 边界、粒度比 commit 均匀，
  而且能区分"合了"和"提了没合"。`delivery_block` **已经在采 `prs` / `merged` 了**（`metrics.py:270-271`），
  只是 `roi` 只用了 `commits` —— 这是零成本的改进
- **失效**：分母可被被考核者自己制造。任何按 commit 数考核的口径，最终都会得到更多、更小的 commit

### 4.4 每次"回答了一个 A-vs-B 决定"的成本

**回答**：这笔钱换来了哪个决定 —— 唯一能覆盖"不进 git 的产出"的单位
（这是 owner 自己 CLAUDE.md 里的判据："这次产出，支撑他哪一个「A 还是 B」的决定"）

- **适用**：调研、方案对比、排障定位这类**产出是"知道了一件事"**的工作。这类在本机占比不低，而且完全不进 git
- **失效**：需要人工标注，无法确定性派生 → **与本仓"零 agent 零 token"红线冲突**
  （`zero-agent-zero-token-rule`：运行期禁调模型、数据靠派生）
- **可行的折中**：会话结束时人手打一个一位标签（`decided` / `explored` / `shipped` / `dead-end`）。
  单次成本 2 秒，但需要习惯。**这是唯一能让"没进 git 的产出"进入分母的办法**，
  不做的话 §4.3 会永远系统性高估每次交付的成本

### 4.5 每个通过的测试 / 每个关闭的 issue

- **适用**：分母机器可验证，且与质量直接挂钩；比 commit 更难灌水一点
- **失效**：仍然可以灌水（100 个断言同一件事的测试；把一个 issue 拆成 5 个）。
  **任何"分母可被被考核者自己制造"的指标，最终都会被制造出来。**
  这条对 §4.3 和 §4.5 同样成立，是这两个单位共同的天花板

### 4.6 每次工具调用的成本 —— **本机数据里最有行动价值的一个**

**本机实测**：

| | 值 |
|---|---|
| `cache_read ÷ tool call` | **696,455** |
| `fresh(in+out) ÷ tool call` | **2,739** |
| 比值 | **254 倍** |

**回答**：成本的驱动因子是什么

这个比值说的是：**工具调用是重读上下文的触发器 —— 每多一次工具调用，就把当时的整个上下文再读一遍。**
一次工具调用的边际成本 ≈ `当前上下文长度 × cache read 单价`。
20 万 token 的上下文，Opus 5 下一次工具调用 = **$0.10**。那场 32111 次工具调用的会话 ≈ **$3,211**。

- **适用**：这是唯一直接指向可操作行为的单位（见 §5.L2）
- **失效**：不同工具的回包大小差几个数量级（一次 `ls` vs 一次 200 行 `Read`）→ 必须按工具名分桶
- **失效（更重要）**：**同一个工具在第 3 轮和第 300 轮的成本差 100 倍**，因为成本取决于当时的上下文长度而非工具本身。
  → 必须报"工具 × 轮次分位"的二维，不能只报工具
- **当前不可算**：`tool_names` 在写出时被裁掉了（P8），要改采集

### 4.7 Fresh token 吨位 = `in + cache_write`

**本机**：1.59B / 139.8B = **1.14%**
**回答**：上下文里有多少是**真的新内容** —— 即"内容周转率"

- **适用**：判断上下文里有多少是新进来的 vs 反复重读的旧的
- **失效**：codex / kimi 的 `cache_write` 未测量（P4），该口径在这两个来源上退化成 `in`，
  会让它们显得"更省"。必须显式标"未测量"而不是 0

⚠️ **一个容易顺手推出的错误结论，我自己先犯了再纠正**：
"既然 fresh 只占 1.14%，那把 CLAUDE.md 写短一点最多也只能省 1.14%" —— **这是错的。**

正确的账单分解是：

> **`cache_read ≈ Σ(每次 API 调用时的上下文长度)`**

于是**两个乘数关系完全不同的杠杆**：

| 杠杆 | 省下的量 | 乘数 |
|---|---|---|
| **缩短一段"每次调用都在场"的前缀**（CLAUDE.md、工具定义、system prompt） | `X × N_调用次数 × read单价` | **乘以调用次数** |
| **减少调用次数** | `当时上下文长度 × ΔN × read单价` | 乘以上下文长度 |

**缩短常驻前缀的杠杆被调用次数放大了** —— 砍掉 5K token 的工具定义，在一场 3000 次调用的会话里就是省 1500 万 token 的读取。
这不是 1.14% 的一小部分，这是 `cache_read` 那 78% 里的一块。

**实证**：Anthropic 官方 Tool Search Tool 的实测就是这个杠杆 ——
50+ MCP 工具场景的工具定义从 **约 77K 降到约 8.7K（−85%）**，
而 MCP 评测分数 **Opus 4.5 从 79.5% 升到 88.1%**（§5.L3）。省钱且更准。

`fresh token 吨位` 回答的是"内容周转率"，**不是"优化空间的上限"**。别把它当后者用。

---

## 5. 可落地的省钱杠杆（按「省下的量 ÷ 实施代价」排序）

**先说一条反直觉的前提**：本机 78.15% 的账单是 cache read。
cache read 的账单 ≈ `Σ(每次调用的上下文长度)`。所以**所有省钱杠杆只有两类**：
**(a) 让每次调用的上下文更短**，**(b) 让调用次数更少**。
其他一切（换便宜模型、缩短你打字的提示词）都是在动那 0.91% 的 fresh input。

---

### L1 —— 工具输出封顶 / 裁剪（**最高性价比，三份独立实测且质量不降反升**）

| 实测 | 基线 → 处理后 | 质量变化 |
|---|---|---|
| Towards AI 2026-08（DeepSeek，15 组配对轨迹） | **$0.189 → $0.117（−38%）** | **缓存命中率 96.0% → 95.9%（几乎没动）；记忆探针准确率完全相同** |
| 《The Complexity Trap》（JetBrains+TUM，Qwen3-Coder 480B，SWE-bench Verified 全 500 题） | **$1.29 → $0.61（−52.7%）** | 解决率 **53.8% → 54.8%（略升）** |
| 《Less Context, Better Agents》（GPT-5，D365，50 任务 ×5 次） | **1,480,996 → 535,274 token（−63.9%）** | 完成率 **71% → 79%** |

Towards AI 的作者把这条称为「白捡的 38%」——**15 组配对轨迹里赢 14 组，缓存命中率没动，质量没掉。**

**实施代价：极低。** Anthropic 官方文档直接给了范例：
用 `PreToolUse` hook 把一万行日志 grep 成只剩报错行，把上下文从几万 token 降到几百
（https://code.claude.com/docs/en/costs ）。

**为什么这条排第一**：三份来源、三种模型、三个场景，方向完全一致，
而且都测到**质量不降反升** —— 工具回包里的绝大部分不是信息，是噪声（§2.5 的 84% / >70%）。

⚠️ **失效条件**：《SWE-Pruner Pro》测到剪枝在不同模型上方向相反 ——
MiMo-V2-Flash **+3.8%**，但 Qwen3-Coder-Next **−1.2%**，且剪枝调用本身额外增加 **15.0% 墙钟时间**。
所以裁剪规则要按工具/场景单独验，不要全局一刀切。

---

### L2 —— 常驻前缀瘦身（工具定义 / MCP / system prompt）

这条的杠杆被**调用次数放大**（§4.7）：砍掉的每一个 token，在每一次调用里都省一次。

**Anthropic 官方实测**（https://www.anthropic.com/engineering/advanced-tool-use ，2025-11-24）：

| 特性 | token 变化 | **质量变化** |
|---|---|---|
| **Tool Search Tool** | 50+ MCP 工具场景从约 **77K 降到约 8.7K（−85%）**；工具搜索本身开销约 500 token | MCP 评测 **Opus 4：49% → 74%**；**Opus 4.5：79.5% → 88.1%** |
| **Programmatic Tool Calling** | 复杂研究任务 **43,588 → 27,297 token（−37%）** | 内部知识检索 25.6% → 28.5%；GIA 46.5% → 51.2% |
| Tool Use Examples | — | 复杂参数处理准确率 **72% → 90%** |

**省 85% 的同时准确率涨 8.6 个百分点** —— 这是所有杠杆里唯一一条官方给了 benchmark 且两头都赢的。

Claude Code 侧的对应机制（官方文档）：MCP 工具**默认 deferred，只有名字进上下文（约 120 token）**；
系统提示约 4,200 token、auto memory 约 680、环境信息约 280。

**实施代价：低**（开个开关 / 审一遍挂了哪些 MCP）。

⚠️ **第三方存在反证，且利益相关**：Stacklok（2025-12-10，卖竞品）用 2,792 个 MCP 工具测得
Tool Search Tool 选择准确率仅 **34%（BM25）**、检索准确率 **48%**，
他们自家产品 94%/98%；他们明确说**没有独立复现 Anthropic 的 85%**，因为"Anthropic 的实验和数据集未公开"。
→ Anthropic 的数字是官方自测、数据集未公开；Stacklok 的数字来自竞品厂商。**两边都要打折。**

---

### L3 —— TTL 选对（一个参数，可能是本机最大的一块未量化损失）

**Anthropic 官方的两条硬事实**：
1. **TTL 从请求「开始」计时，不是响应结束**。一次流式输出跑 4 分钟，5m TTL 只剩约 1 分钟（§1.2 原文）
2. **1h 写溢价 2x，读 2 次即回本**（§1.6 官方原话确认）
3. Claude Code 订阅默认 **1 小时**；API / 云厂商默认 **5 分钟**（https://code.claude.com/docs/en/prompt-caching ）

**本机的可疑信号**：`cache_write = 1,431,683,412`，是 fresh input 的 **8.91 倍**。
如果每段上下文只在会话开头写一次、之后全靠读，这个比例不该这么高。
**【推】这个 8.91 倍很可能就是 TTL 反复过期在重写。**

⚠️ **这条我只能推断，不能断言** —— 我没有 per-request 的 `cache_creation` 时间分布。
**要验证只需要一件事**：把 extract 里已经在遍历的每条 message 的 `cache_creation_input_tokens`
按时间戳留下来，看它是集中在会话开头还是散布全程。散布全程 = TTL 在漏。这正是 §6.M3 那个指标。

**实施代价：低。** 但**先量再改** —— 在没有量之前，把所有会话改成 1h TTL 会让写溢价从 1.25x 变 2x，
对短会话是净亏。

---

### L4 —— DeepSeek off-peak 排程（对本机 DSH / kimi 那条线，代价接近零）

官方【官】：off-peak = peak 的 **50%**，hit / miss / output 三档一律打折；
peak 只有 **UTC 01:00–04:00 与 06:00–10:00**（7 小时/天），其余 17 小时全折扣。

**换算到悉尼 UTC+10**【推】：peak = 本地 **11:00–14:00** 与 **16:00–20:00**。
**本地凌晨、上午、以及 20:00 之后全是折扣时段。**

本机的 `by_slice` 已经在按时段切了 —— 把 DSH / kimi 的批处理 cron 挪到折扣时段是**纯排程改动，省 50%**。

**实施代价：≈0**（改 cron 时间）。
**收益上限受限于 DeepSeek 侧的量** —— 本快照 kimi-code 只有 1.1B cache_read，占比不大；
但 parent 说的新数据里 DSH 有 1937 场，量级可能完全不同。**先看 DSH 的绝对量再决定优先级。**

⚠️ 这条只对 DeepSeek 有效。Anthropic / OpenAI / Gemini 都**没有时段折扣**（但都有 Batch 50%）。

⚠️⚠️ **但这条杠杆同时带来一条坏消息，必须一起看**：
分时定价是 **2026-08-16 生效的新制**，同时把**缓存命中档从 ¥0.025 涨到空闲价 ¥0.15（6.0 倍）**。
GitHub 上一份做了官方对账的实测（§7.A3）算出：
**同样的负载，按新价重算账单变成原来的 2.7 倍；而如果命中率为 0，反倒只涨到 1.5 倍。**
→ **缓存命中率越高，这次涨价吃亏越大。**
本机 DSH/kimi 那条线的命中率是 98.39%，属于吃亏最狠的那一档。
**排程优化能拿回 50%，但拿不回这 2.7 倍。** 这是一条应该重新评估供应商组合的信号，不只是排程问题。

---

### L5 —— 稳定前缀，别让缓存被击穿

**Anthropic 官方列全了会毁 cache 的动作**（https://code.claude.com/docs/en/prompt-caching ）：
换模型、改 effort level、开 fast mode、MCP server 连断（仅当工具没被 defer）、整工具 deny、
**compaction**、升级 Claude Code。

**Anthropic 官方失效顺序**：`tools` → `system` → `messages`，**任一层变动会让该层及之后全部失效**（§1.2）。

**推论**：CLAUDE.md / AGENTS.md / 工具定义必须在最前且**逐字节稳定**。
任何带时间戳、随机 ID、动态路径、会变的环境信息放在前面 = **每次全量重写**。

**Systima 实测的击穿实例**：「一个 Haiku 子 agent 比兄弟晚 6 秒启动，零 cache read 写满 **52,022** token 前缀；
一个 Fable 子 agent 晚 12 秒，miss 后写了 **40,829** token」。

**实施代价：低**（审一遍 system prompt 里有没有动态内容；别在会话中途换模型/改 effort）。
**收益不可量化** —— 因为击穿是隐性的，除非先做 §6.M3。

---

### L6 —— 收缩扇出（**收益最大，但实施代价也最大**）

**对本机最相关的一条**：parent 说 4802 场里 **3818 场是扇出/批处理**。这是账单结构的主因，不是副作用。

**Anthropic 官方的两条硬事实，直接决定扇出的成本下限**（https://code.claude.com/docs/en/prompt-caching ）：
1. **子 agent 即使在订阅上也只用 5 分钟 TTL**（不是父会话的 1 小时）
2. **子 agent 的首个请求读不到父 agent 的缓存**（只有 fork 才能读到）

→ **每一次扇出，至少要付一次完整的 cache write（1.25x 溢价）。** 这不是可以优化掉的开销，是机制。

**实测佐证**：

| 来源 | 数字 |
|---|---|
| Systima（Claude Code，2 子 agent vs 顺序） | Opus **2.6×**、Fable 5 **5.9×** metered input token |
| Systima 墙钟时间（Opus） | 顺序 4m15s、2 子 agent **8m00s** —— **"The speed argument never showed up"** |
| TokenDance（北大+上交，8-agent） | 子 agent 之间 KV cache 相似度 **91%–97%** —— 绝大部分是重复 |
| Salesforce《Illusion of Multi-Agent Advantage》 | 自动 MAS 常花 **10× 成本换 negligible gains**；HLE-Maths 上 $116.20 → **$1,288.30** |
| TUM《Scaling MAS》 | MAS-L 成本 **3.2×**、准确率 **−9.7%**，agent 超时数 3.33 → 50.0 |
| Stanford（Tran & Kiela） | **等 thinking token 预算下**，单 agent 在除最低预算外的**所有预算档上打平或更好** |
| Anthropic 官方（另一面） | multi-agent 在其内部 research eval 上 **outperformed single-agent Opus 4 by 90.2%** |

⚠️ **两边都列**：Anthropic 官方测到扇出在**研究类任务**上大幅胜出（+90.2%）；
学术侧多份测到扇出在**编码 / 多跳推理**上打平或更差。
**分歧点是任务类型**：扇出的价值在于**并行探索独立的搜索空间**（研究、检索），
不在于**分解一条有依赖的任务链**（编码、多跳推理 —— 每次交接都丢信息，Data Processing Inequality）。

**实施代价：中**（要改工作方式）。**但这是唯一能动到账单结构的杠杆。**

---

### L7 —— Batch API 50%

Anthropic 官方：**batch 折扣与缓存倍数可叠乘**。OpenAI / Gemini 也各有 Batch/Flex 50%。
适用：每日复审、蒸馏、批量出图 prompt 这类不需要即时回复的活。
**实施代价：中**（要改成异步调用 + 处理回收）。

---

### L8 —— ⚠️ 慎用「压缩」：实测它可能**更贵**（这是止损，不是省钱）

这是本轮调研最推翻直觉的一条。

**Towards AI 对照实验**（2026-08，11 种配置、660 轮对话、Gemini 3.5 Flash + DeepSeek V4 Flash 对照，整个程序约 $590；
质量量法：第 0 轮埋事实 → 养到触发摘要 → 探针提问 → 盲评，与人工标注一致率 98%）
https://www.louisbouchard.ai/context-engineering-2026/

| 配置 | 记忆召回 | **每轮成本** |
|---|---|---|
| **full_history（不压）** | **92–100%** | **$0.11** |
| production preset（5k 清陈旧工具输出 + 30k 摘要旧轮次，保留最近 20 条） | 广筛 58%，两轮复测 **38%** | **$0.24** |
| context reset | **17%** | — |

**压缩比不压贵 118%，同时记忆召回从 92–100% 掉到 38%。**

**机制**（三条独立证据指向同一件事）：
1. **摘要调用要把整个历史再发一遍** —— Claude Code 官方文档承认：
   「To produce the summary, Claude Code sends a separate request with the same system prompt, tools, and history as your conversation」，
   且明确说"缓存冷掉后要按未缓存价重算全量历史，这是 `/compact` 最贵的情况"，**但不给比例**
2. **摘要后前缀重写 → 缓存全失效**。Anthropic 官方把 `compaction` 明确列在"会毁 cache 的动作"里
3. **串行压缩吃掉大量墙钟时间** —— arXiv 2605.23296 实测：τ=16k 时压缩占端到端 **51.3%–62.4%**（τ=96k 时降到 8.6%–14.5%）

**同时压缩的质量代价是可量的**：arXiv 2605.23296 测到 96k 输入产出 500 token 摘要，
**保留原上下文不到 1%**；且**摘要保留率和准确率正相关，压得越狠越掉分**
（4k block 保留 12.37–34.13%，2k block 保留 28.16–50.98%，准确率随保留率单调上升）。

**正确的做法不是「压缩」，是「开新会话、丢掉旧上下文」。** 区别在于：
- **压缩**：付一次全量重发（全价）+ 缓存击穿 + 之后仍带着摘要在跑
- **开新会话**：只付一次**小上下文**的 cache write，之后每次读的都是小上下文

按 §1.6 的盈亏平衡：新会话只要还会跑 ≥1 轮（5m TTL）或 ≥2 轮（1h TTL），这次 cache write 就已回本。

⚠️ **但也别一刀切**：arXiv 2606.11213《Beyond Compaction》在单会话连续跑 89 个任务 / 8000 万 token 的实验里，
对比"每任务全新上下文"基线，四个 benchmark 差异都 ≤3 个百分点
（Terminal Bench 2.0 68.25% vs 68.40%、SWE Bench Lite 43.00% vs 40.00%），
靠维持**稳定前缀**拿到 **20–70%** 推理成本下降。
→ 结论是"**稳定前缀 > 压缩**"，而不是"上下文管理没用"。

---

### L9 —— 别把「总 token 数」当 KPI（纯止损）

现在的看板会让人去优化 `input_total`（138B）。但那 78% 是 cache read，
**优化它的唯一方式是 §5 开头那两条（缩短每次调用的上下文 / 减少调用次数）**，
而看板上没有任何一屏指向这两件事。
一个指标如果指不出可执行动作，它就只是让人焦虑。

---

### 杠杆排序总表

| # | 杠杆 | 实测省下 | 实施代价 | 质量影响 | 证据强度 |
|---|---|---|---|---|---|
| **L1** | 工具输出封顶/裁剪 | **−38% ~ −64%** | **极低**（一个 hook） | **不降反升**（3 份独立实测） | ★★★ 三方独立 |
| **L2** | 常驻前缀瘦身 | **−85%**（工具定义） | 低（开关/审计） | **+8.6 pt**（Opus 4.5 MCP eval） | ★★ 官方自测，数据集未公开；有竞品反证 |
| **L3** | TTL 选对 | 未量化（本机 write 是 fresh 的 8.91×） | 低（一个参数） | 无 | ★ 官方机制确凿，本机幅度待测 |
| **L4** | DeepSeek off-peak 排程 | **−50%**（仅 DeepSeek 侧） | **≈0**（改 cron） | 无 | ★★★ 官方定价页 |
| **L5** | 稳定前缀防击穿 | 未量化 | 低 | 无 | ★★ 官方列全了击穿动作 |
| **L6** | 收缩扇出 | **2.6×–5.9× 的反向**（即少扇出=省这么多） | **中**（改工作方式） | **看任务类型**，两边都有证据 | ★★ 多方实测，但方向依任务而异 |
| **L7** | Batch API | −50% | 中（改异步） | 无 | ★★★ 官方 |
| **L8** | ~~压缩~~ → 改为「开新会话」 | 压缩实测 **−118%（更贵）** | 低 | 记忆召回 92–100% → **38%** | ★★ 单份对照实验 + 官方机制佐证 |

---

## 6. 建议 Memory Atlas 新增的 5 个 token 指标

每个给：**回答什么问题 / 怎么算 / 什么情况下会骗人**。

---

### M1 —— 价格加权成本，四类堆叠

**回答什么问题**：这个月的钱花在哪一类 token 上 —— 直接替代现在那个 `input_total`。

**怎么算**：
```
成本 = tok_in × 单价_in
     + tok_cache_r × 单价_read
     + tok_cache_w × 单价_write(按 TTL 档)
     + tok_out × 单价_out
```
单价表按 provider × model 查，**表本身要版本化并记抓取日期**。
展示成一个四段堆叠条：`fresh input / cache READ / cache WRITE / output`。

本机当前值（Opus 5 口径）：`$804 / $69,109 / $8,948 / $9,570 = $88,430`。

**什么情况下会骗人**：
1. **包月订阅下这是机会成本不是实付**。Claude Code Max 之类的定额套餐里边际成本是 0。
   → 必须在同一屏标出「实付 = 订阅费」和「按 API 计价的机会成本」两个数，不能只给一个
2. **跨 provider 加总时结构不同**：DeepSeek 的 read 是 0.032x 不是 0.1x 且 off-peak 再砍半；
   **Gemini 显式缓存是「租金 × 小时」，根本装不进这个公式**（§1.6）
3. **模型混用 + taxonomy 均分归因（P10）叠加时错 5 倍**。混用会话应进"不可归因"桶
4. **跨 tokenizer 版本比较会把版本变更读成用量增长** —— Claude 4.7+ 同样文本多约 30% token【官】
5. **codex / kimi 的 `cache_write` 未测量**，它们的成本会被系统性低估。必须显式标"未测量"而不是当 0

---

### M2 —— 每次工具调用的边际成本（按 `工具名 × 轮次分位` 二维分桶）

**回答什么问题**：钱是被哪个动作烧掉的 —— 这是唯一直接指向可执行行为的指标。

**怎么算**：
```
每次调用的边际成本 ≈ 当时的上下文长度 × cache_read 单价
```
按 `tool_name` 汇总，同时按该调用发生在会话的第几个轮次分位（p25/p50/p75/p95）切第二维。

本机现有的一维近似（**已可算，但带 P0 虚高，需除以约 2.4**）：

| | 未去重 | **按 P0 折算后（÷2.41）** |
|---|---|---|
| `cache_read ÷ tool call` | 696,455 | **≈ 289,000（≈ $0.14 / 次，Opus 5）** |
| `fresh(in+out) ÷ tool call` | 2,739 | ≈ 900 |
| 比值 | **254 倍** | **254 倍（比值不受 P0 影响）** |

最大那场：32,111 次工具调用、cache_read 未去重 34,598,043,804 → **去重后 15,433,971,029（该场虚高 2.24×）**，
整场约 **$7,717**（未去重口径会报成 $17,299）。

**什么情况下会骗人**：
1. **不分桶就没意义** —— 一次 `ls` 和一次 200 行 `Read` 的回包差几个数量级
2. **更要命的第二维**：**同一个工具在第 3 轮和第 300 轮的成本差 100 倍**，
   因为成本取决于**当时的上下文长度**而不是工具本身。
   只报"哪个工具贵"会得出错误结论 —— 贵的可能只是"被安排在后面调用"的那个
3. **当前不可算**：`tool_names` 在写出 sessions.jsonl 时被裁掉了（§3.P8），要先改采集
4. 上游会计缺失：**每场会话的 API 调用次数没有被记录**，所以现在只能用 tool call 数做代理。
   工具调用数 ≠ API 调用数（一次 assistant 消息可能带多个 tool_use 块）

---

### M3 —— 缓存击穿指数：`cache_write` 的**时间分布**，不是总量

**回答什么问题**：缓存是不是在反复过期重建 —— 这直接对应 TTL 选错和前缀不稳（§5.L3 / L5）。

**怎么算**：把每条 message 的 `cache_creation_input_tokens` **连同时间戳**留下来，然后报：
- **会话开头 vs 全程的分布**：集中在开头 = 健康（一次性建缓存）；散布全程 = **TTL 在漏**
- **相邻两次 cache_creation 的时间间隔分布**：大量间隔恰好略大于 5 分钟 = 5m TTL 不够用的铁证
- 每场会话的 `cache_write ÷ cache_read` 比

本机当前只有总量：`cache_write / tok_in = 8.91×`（去重后 **660×**），`cache_write / (in+cached) = 1.03%`。
**这个比值就是要拆的那个数。**

**判据可以直接拿现成的** —— B站那份抓包实测（§7.A5）已经给出健康状态的样子：
```
Turn 1: cache_creation 48,654   cache_read 0        ← 建缓存，正常
Turn 2: cache_creation 24       cache_read 48,654   ← 健康：每轮只写几十个
Turn 3: cache_creation 29       cache_read 48,678   ← 健康
规律：每一轮 cache_read = 上一轮 cache_read + 上一轮 cache_creation
```
**一旦某轮 `cache_creation` 突然从几十跳回几万，就是缓存被击穿了。**
不需要额外建模，一条阈值规则即可。
另一份实测（§7.A2）给了同样的形状：Turn 1 写 138,997、Turn 2 写 220、Turn 3 写 206。

**实施代价接近零** —— `extract.py` 已经在遍历每条 message 并读 `usage` 了（`extract.py:317-320`），
只是把值加进了一个累加器。留下 `(时间戳, cache_creation)` 的序列是纯增量。

**什么情况下会骗人**：
1. **Anthropic 允许一次请求最多 4 个 cache breakpoint**，所以一次请求可能**合法地**产生多段 cache_creation。
   把它当"过期重写"会高估 → 要按该请求的 breakpoint 数归一
2. **会话开头的第一次写入是必要成本，不是浪费**，必须扣掉
3. **子 agent 的首次写入也是必要的** —— 官方明说子 agent 读不到父 agent 的缓存（§5.L6）。
   扇出场景下 cache_write 高是**机制**不是**故障**，要按 `kind` 分开报
4. **codex / kimi 恒为 0**，该指标在这两个来源上完全不可用，要显式标"未测量"

---

### M4 —— 按**真实发生时间**归集的每日成本（修 §3.P6）

**回答什么问题**：这一天到底烧了多少 —— **现在这个问题答错了 94.5%。**

**怎么算**：按 **per-message 时间戳**把每条 `usage` 归到它实际发生的那一天，
而不是把整场会话记到 `start` 那天。`extract.py` 已经在遍历每条 message 并且已经在读 `timestamp`（`extract.py:295`），
所以这是纯增量改动。

配套要加**「活跃时长」**：相邻消息间隔 < 30 分钟才计入，取代现在的 `end − start`。
本机 `end − start` 的中位数 0.03h、但有 110 场 > 24h、最长 198 天 —— 后者显然是挂机不是干活。

**什么情况下会骗人**：
1. **⚠️ 千万别用线性摊分当过渡方案。** agent 会话是**爆发式**的（跑 3 小时然后挂着 20 天），
   把 34.6B 线性摊到 24 天上**同样是虚构**，只是换了一种错法。
   要么做 per-message 归集，要么就诚实地标"该会话跨 N 天，无法按日归集"
2. **改完之后所有历史日线图都会变**，包括 parent 引用的「某天 130 亿 token / 0 次提交」。
   → 改口径时必须同时给出新旧对照，不能悄悄换掉
3. 归集变准之后，**日线的方差会暴涨**（因为不再有一根柱子吸走 94.5%），
   看起来会"更乱" —— 那是真实的样子，不要为了好看再平滑回去

---

### M5 —— 扇出税（fan-out tax）：`扇出会话的成本 ÷ 顶层会话的成本`

**回答什么问题**：3818 场机器会话到底吃掉了多少 —— 本机账单结构的主因，**目前完全不可观测**。

**怎么算**：
```
扇出税 = Σ成本(kind == auto) ÷ Σ成本(kind == human)
```
配套三个分解：
- **按来源分**（DSH 扇出 vs Claude Code 内部 Task 扇出 vs 批处理）
- **每次扇出的固定开销**：子 agent 的首次 cache_write 中位数（官方：子 agent 读不到父缓存，
  所以这是**每次扇出的机制性下限**）
- **扇出深度分布**：一层扇出 vs 嵌套扇出

本机现有的（残缺）数据：`auto` 会话 732 场，`cost_tokens = 13,961,543`，仅占 `human` 的 **2.6%**。
**这个 2.6% 几乎肯定是假的** —— 因为 Claude Code 的内部扇出根本没被识别成 `auto`（§3.P8）。

**什么情况下会骗人**：
1. **⚠️ 分类口径本身是坏的**：DSH 的扇出被剔出 `hum`、Claude Code 的扇出没有（`isSidechain` 从未被读）。
   **不先修 §3.P8，这个指标只会给出一个漂亮的错数。** 这是 M5 的前置条件
2. **扇出"贵"不等于扇出"浪费"**。Anthropic 官方在研究类任务上测到 multi-agent **+90.2%**；
   学术侧在编码/多跳推理上测到打平或更差（§5.L6）。
   → 扇出税必须**和产出并排看**，单独报一个倍数会诱导出错误的结论（"把扇出全砍了"）
3. **子 agent 的 5 分钟 TTL 是机制不是浪费**（官方），
   所以扇出税里有一块**不可压缩的下限**。报总数时要把这块单独标出来，
   否则会让人去优化一个物理上优化不掉的东西
4. Systima 那份唯一的公开扇出实测**原始 trace 并未真正公开**（仓库只有 19 KB），
   且发布方是卖成本优化服务的公司 → **本机应该自己测，不要拿它的 2.6×–5.9× 当基线**

---

### 五个指标的依赖关系

```
【先修 P0：按 (会话文件, message.id) 去重】  ← 不修这条，下面 5 个指标全部建在虚高 2.4–3.6 倍的量上
   ↓
M4（按真实发生时间归集）  ← 不修这条，M1/M2/M3/M5 的所有日/周切片都建在错的日期上
   ↓
M1（价格加权成本）        ← 只需要现有字段 + 一张版本化的单价表，可立即做
   ↓
M3（缓存击穿指数）        ← 需要 extract 留下 (时间戳, cache_creation) 序列，增量小
                            判据可直接用 §7.A5 那条实测规律
   ↓
M2（每次工具调用成本）    ← 需要恢复被裁掉的 tool_names + 记录真实 API 响应数（去重后的 message.id 数）
   ↓
M5（扇出税）              ← 前置条件是先解决 P8：子 agent 的 usage 根本不在父会话文件里，
                            要先能把子会话关联上，否则出的是漂亮的错数
```

⚠️ **这个顺序不能跳。** 尤其 M1：在没修 P0 之前上线一个"价格加权成本"，
只会把一个虚高 2.5 倍的数字**换成美元单位再显示一遍** —— 看起来更专业，错得一模一样。

---

## 7. 中文社区的实践：找到了什么、没找到什么

**总体判定：确实存在，但极少。** 核查约 40 个候选页面，**只有 5 条**满足「有作者自己跑出来的数字」这个门槛。
中文这个赛道 90% 以上是估算文、转述官方价目表的 SEO 文、以及卖 API 中转的软文 ——
**标题都写「实测」，点进去全是「假设你用 Sonnet…」。**

### A. 命中：确认有真实数据的 5 条

#### A1 · 知乎 MarsZhou《AI Token 消耗深度认知：原理+实验+最佳实践》—— 最强的 Cursor 账单证据
https://zhuanlan.zhihu.com/p/2015520315757843266 （上，2026-03-12，浙江）／
https://zhuanlan.zhihu.com/p/2015528262047118202 （下）

**附 Cursor 用量统计截图**，`claude-4.5-opus-high-thinking` 同一仓库任务的两段对话：

| | 对话一 | 对话二（接续） |
|---|---|---|
| Cache Write | 135,192 | 215,274 |
| Input w/o Cache | 320 | 1,403 |
| **Cache Read** | **6,073,251** | **6,698,396** |
| Output | 32,834 | 22,980 |
| Total | 6,241,597 | 6,938,053 |
| **费用** | **$4.70** | **$5.28** |

合计 1,318 万 token，**Cache Read ≈ 97%**。

**另有 prompt cache 过期实测**：同一对话间隔约 **8 小时**后继续，Cache Read 几乎不变（缓存仍有效）；
间隔约 **14 小时**后，**Cache Read 骤降 59%**。

⚠️ **只采信账单表和那个过期实验。** 文中大量周边数据标注了「估算值」，
且个别机制描述不准（称 Anthropic TTL「5~10 分钟」、DeepSeek 缓存粒度「64 tokens」——后者已不符现行文档，§1.5）。

附带价值：文中转引了**小红书**上的真实吐槽（**二手，未能打开原帖核实**）：
「cursor ultra $200 套餐不到半个月用完，共 11 亿 token，实际计费接近 530 刀」「一下午花了 120 美元」
「一个月用了 2000 刀」「支付 700 多刀的 opus」。

#### A2 · 知乎 不亦乐乎《Claude Code Token 深度拆解：一次会话烧掉 970 万 token》—— 最强的单会话分解
https://zhuanlan.zhihu.com/p/2027108001257890538 （2026-04-13，北京）

单会话 **9,721,744 token** 四类分解：

| 类别 | token | 占比 |
|---|---|---|
| Input | 2,971 | **0.03%** |
| Cache Creation | 790,452 | **8.1%** |
| **Cache Read** | **8,913,330** | **91.7%** |
| Output | 14,991 | 0.15% |

逐 turn 明细（这是最有价值的部分）：
- Turn 1: cache_create **138,997**、cache_read **0**、output 89
- Turn 2: cache_read **138,997**、cache_create 220、output 5
- Turn 3: cache_read **139,217**、cache_create 206、output 118

上下文构成实测：消息历史 95,600 / Autocompact 缓冲 21,200 / Memory 10,400 / Skills 10,100 /
自定义 Agents 5,000 / 系统提示 6,400 / 内置工具定义 4,400 ≈ **153,000**。

数据来源：`tuin`（Claude Code 会话 token 分析工具）导出。

⚠️ **扣分项**：全文在推 `context-mode` 开源项目，「76.2% 上下文减少」是该项目自己的基准不是第三方复现；
且称「Anthropic Prompt Cache TTL 大约在 1 小时以内」与官方 5min/1h 双档不符。**token 分解表可信，周边解释打折。**

#### A3 · GitHub deepseek-harness Discussion #1571 —— **唯一与官方账单对过账的**
https://github.com/deepseek-ai/deepseek-harness/discussions/1571 （2026-08-14，KevinZhangMe）

**650 次请求 / 16 个会话 / 613 次 v4-pro / 提示词 1.559 亿 tokens / 缓存命中率 98.09%**

**与 DeepSeek 官方控制台逐项对账**：

| | 本地日志 | DeepSeek 控制台 | 差距 |
|---|---|---|---|
| 花费 | ¥17.45 | ¥17.73 | **−2%** |
| Tokens | 157.7M | 160.2M | **−2%** |
| 请求数 | 650 | 684 | −5% |

**结论**：按 8/16 新价重算，账单变成原来的 **2.7 倍**；
同样 token 若**命中率为 0 反而只涨到 1.5 倍** → **缓存命中率越高，这次涨价越吃亏**（§5.L4 已引）。
旧价 v4-pro 缓存命中 ¥0.025/M → 新空闲价 ¥0.15/M，**涨 6.0 倍**。

时段实测：这 650 次请求里 **41.1% 的 token 落在新的高峰计费窗口**（纯因为在北京时间白天干活）。
同一负载下，缓存把本该 ¥711.73 的账单压到 ¥46.53（**15.3 倍**）。

**可信度：本节最高** —— 唯一做了官方对账、且公开了审计脚本。
⚠️ 作者自营 deepseekprice.com（计算器页），有导流成分，但数据本身经得起核。

#### A4 · 博客园 曾左《每月 20 美元的 Claude Pro 会员到底能消耗多少 Token 及额度》
https://www.cnblogs.com/zengzuo613/p/20595884 （2026-06-17）

实测窗口 2026-06-03 15:00–19:00：**4 小时内消耗 3,925 万 Token / 18.36 美元 / 占用 10% 的周额度**（ccusage 统计）。

⚠️ **可信度中**：有具体日期和数字，但**无截图**，作者本人声明「Claude 内部计算与配额机制从未公开，结论可能变化」。

#### A5 · B站 张司机在路上《解密多轮对话 Claude Code 如何计算 token 消耗》
https://www.bilibili.com/video/BV1KGoyBGEjN/ （2026-04-27，播放 44.1 万）

用 `claude-tap` **拦截三轮真实 API 请求逐条对比**：
- 首条：**48,654 token 全部写入缓存，读取 0**
- 第二条：**48,654 从缓存读取，24 个新 token 写入**
- 第三条：**48,678 缓存读取，29 个新增**

**归纳出的规律**：`每一轮 cache_read = 上一轮 cache_read + 上一轮 cache_creation`

同 UP 另有 https://www.bilibili.com/video/BV1ZQ5u6bEJ7/ 《教你最大化 Claude Code 缓存命中来节省 token》（2026-05-12，2.5 万播放）。

**可信度中高**（抓包方法论可复现）。

> **这条规律是本节最有用的一条** —— 它是 §6.M3（缓存击穿指数）在真实数据上的机制说明：
> 健康状态下 `cache_creation` 每轮只有几十个 token（24、29），
> **一旦某轮 `cache_creation` 突然回到几万，就是缓存被击穿了。**
> 这给了 M3 一个可直接用的判据，不需要额外建模。

### B. 与本机数据的交叉验证

三份独立的中文实测，与本机 99.88% 落在同一结构上：

| 来源 | 场景 | cache read 占比 |
|---|---|---|
| A1 MarsZhou | Cursor + Opus 4.5 | **≈97%** |
| A2 不亦乐乎 | Claude Code 单会话 | **91.7%** |
| A3 KevinZhangMe | DeepSeek 650 请求 | **98.09%** |
| §2.2 UIUC/Intel 硬件 trace | 5 个 benchmark | **84.6–99.5%** |
| **本机（快照）** | **2826 场** | **99.88%（现口径）/ 98.86%（含 write）** |

→ **再次印证 §3.P3 的结论：这个数字是负载的结构常数，不是本机上下文管理的成绩单。**

同时 A1 的 TTL 实验（8 小时仍有效 / 14 小时掉 59%）与 A2 的逐 turn 数据（首轮 write 13.9 万、次轮 write 220）
共同支持 §6.M3 的设计：**要看的是 `cache_creation` 的时间分布，不是它的总量。**

### C. 判定为「无数据 / 不可信」的（逐条核实过正文，不是看标题）

| 标题 | 判定 |
|---|---|
| 知乎《Claude Code Token 烧钱实录》 | **知乎官方标注「内容疑似 AI 生成」**；全部是估算表；模型名/价格有错 |
| 知乎《Token 花在哪了？消耗监控统计神器（四种方法）》 | 纯工具安装教程，**零真实数据**（搜索摘要里那些「3520万Token=16.70美元」并不在正文里） |
| 知乎《我把 Cursor、Codex、Claude Code 都用了一遍》 | 云厂商官号内容营销，数字全是二手转引，文末推自家套餐 |
| 掘金《月账单从 $800 砍到 $150》 | 「一次典型交互约 15 万 tokens」是经验估算，**无截图无日志** |
| 掘金《实测 5 招，把月费从 250 美金砍到 50 美金》 | 「日均成本估算」「可能在 150~250 美元之间」，引 CloudZero 报告但无链接 |
| 掘金《12 个省 token 技巧》 | 只有「中文 100 行 ≈ 800 tokens」这类换算和「高/很高/中高」定性表 |
| 博客园《[LLM] Claude Code 省钱小妙招》 | 全部转述官方定价；建议对比 Dashboard 但**自己没贴对比结果** |
| holysheep.cn / jishuzhan.net / bytenote.net / ofox.io / vibecafe.ai / deepai.wiki 等 | 高度疑似批量生成的 SEO 站群，同一批数字在多站复用，**不采信** |

### D. 平台分布的诚实结论

| 平台 | 结论 |
|---|---|
| **知乎** | 有 2 条真货（A1/A2），但淹没在大量 AI 生成文里 |
| **B站** | **有真货且质量不错**（抓包实测），是被低估的一块 |
| **GitHub 中文 discussion** | **质量最高的一条在这里**（A3，唯一做了官方对账） |
| **博客园** | 1 条（A4） |
| **掘金** | 核了 3 篇，**全军覆没** |
| **CSDN** | ⚠️ **未能核实** —— 访问触发图形安全验证。《DeepSeek 涨价实录 日账单 1.8→9.7 元》等看起来最像有真数据，**没打开正文之前不下结论** |
| **小红书 / 微博** | **没找到可直接引用的一手帖**。只有 A1 里转引的截图内容（11 亿 token / 530 刀等），**二手，未能核实原帖** |
| **微信公众号** | **搜不到可公开访问的有数据原文** |

### E. 明确没找到的（这是结论，不是遗漏）

1. **agent 扇出 / 子 agent 成本的中文一手实测：没找到可信的。**
   搜到的全是「subagent 省 60~90%」「开 N 个等于 N 倍 token」这类无数据断言，站点特征均为 SEO 农场。
   **这一项是空的。** 英文侧也只有 Systima 一份，且原始 trace 并未真正公开（§2.4）。
   → **本机 3818 场扇出会话的实测数据，如果做出来，在中英文两边都是稀缺的。**
2. **prompt cache 命中率实测：中文侧只有 3 条**（A1 的 8h/14h 过期实验、A2 的 91.7%、A3 的 98.09%）。

---
