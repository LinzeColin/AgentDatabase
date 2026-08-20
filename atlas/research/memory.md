# agent 记忆／经验沉淀 调研发现

> 调研时间：2026-08-20。所有 GitHub 数字为当天 `gh api` 实抓（抓取时刻 2026-08-20T12:56–13:08Z），非估算。
> 本文只调研，不含实现代码，未改动项目内任何文件。
> **口径约定**：每条结论标注来源类型 —— 〔官方文档〕〔项目自称〕〔厂商互测〕〔独立第三方〕〔本机实测〕〔社区意见〕〔未找到〕。
> 本轮 WebSearch 配额（200 次）在调研中途耗尽，受影响的条目已逐条标注「未能一手核实」。

---

## 〇、先说三条会改变判断方向的事实

1. **没有一个成熟的 agent 记忆开源项目能满足「运行期零模型」。** 覆盖的 6 个项目（mem0、Letta、Graphiti、cognee、LangMem、MemOS）**写入端全部强依赖 LLM**，无一提供非 LLM 模式。唯一能纯算法跑的是 Graphiti 的**检索侧**。对本项目而言，这条红线直接把这 6 个项目全部排除在「可直接引入」之外 —— 但它们的**分层设计与失效语义**仍可借鉴。

2. **所有公开 benchmark 成绩都是卖记忆的厂商自评。** 唯一一条有完整一手证据链的第三方复现（mem0 复现 Zep 的 LoCoMo）以 `84% → 75.14%（Zep 自我更正）→ 58.44%（竞品复现）` 三个数字和一个被以「inactivity」关闭的 issue 收场。且 LoCoMo 上「不用记忆、全上下文塞进去」的 baseline 就有约 73%。**任何单一数字都不能作选型依据。**

3. **本机现有 `sediment.py` 沉淀的是「问题被问了几次」，不是「答案是什么」。** 这是「写下来了下次还找不到」的根因 —— 严格说，**答案从来没被这条流水线写下来过**。`AGENT_BRIEF.md` 是一份成本报告，不是知识库。详见第五节。

---

## 一、项目对照表

### 1.1 硬数据（2026-08-20 实抓）

| 项目 | stars | 许可证(SPDX) | 版本 | 记忆分层 | 写入触发 | 检索触发 | **运行期是否调模型** | **是否需外部 DB** | 第三方评测 |
|---|---:|---|---|---|---|---|---|---|---|
| **mem0** (mem0ai/mem0) | 63,675 | Apache-2.0 | 2.0.18 | 名义 semantic/episodic/procedural，**实际只有 procedural 接线**；真正分层是 user_id/agent_id/run_id 作用域 | 应用层显式 `m.add()` | 应用层显式 `m.search()`，**不自动注入** | **写入 1 次 LLM**（ADD-only 单次抽取）；`infer=False` 可 0 次但仍需 embedding；**检索 0 次 LLM** | **否** —— 默认嵌入式 Qdrant(`/tmp/qdrant`) + SQLite | 有（竞品互测，见 1.3） |
| **Letta**（原 MemGPT） | 24,314（**旧仓已归档**）／letta-code 3,068 | Apache-2.0（letta-code 附品牌例外条款） | letta-code npm 0.30.27 | MemFS：memory blocks(常驻) / external memory / skills / recall；**换层 = mv 文件** | **agent 自己调 `memory` 工具** + 后台 reflection 子 agent | memory blocks 自动注入；external 需 agent 显式读；recall 走子 agent | **是，且无法绕过** —— 记忆编辑本身就是 tool call，压缩摘要、reflection 都要 LLM | 本地模式**否**（纯文件+git，无 DB 无 embedding），但标 EXPERIMENTAL 且默认关 | 有（自评为主） |
| **Graphiti** (getzep/graphiti) | 30,127 | Apache-2.0 | v0.29.3 | Episode / Entity / Community / Saga；**双时间轴** valid_at·invalid_at（世界时间）+ created_at·expired_at（系统时间） | 显式 `add_episode()`；社区更新默认关 | agent 主动 `search()` | **写入必须**（连手工 `add_triplet()` 也要过一遍 LLM 做冲突判定）；**检索默认不用**（RRF/MMR 纯算法） | **是** —— Neo4j / FalkorDB / Neptune；唯一嵌入式选项 Kuzu **已 deprecated** | 无独立复现 |
| **Zep**（服务端） | 4,854 | Apache-2.0 | — | — | — | — | — | 闭源托管 Zep Cloud；开源仓现为示例集合，Go 服务端已挪进 `legacy/`（标 unsupported） | 见 1.3 争议 |
| **cognee** (topoteretes/cognee) | 30,146 | Apache-2.0 | v1.5.0 | chunk → entity → concept → ontology；现行 API 为 `remember`/`recall`/`forget`/`improve` | 显式 `remember()` | 显式 `recall()` | **必须**（可换 Ollama 全本地，但不能零 LLM） | **否** —— 默认全嵌入式 SQLite + LanceDB + Kuzu（仅单进程） | 无独立复现 |
| **LangMem** (langchain-ai/langmem) | 1,619 | MIT | **0.0.30，零 release** | semantic / episodic / procedural | hot path 工具（有可感知延迟）／background + debounce | agent 工具 或 自行 `store.search()` | **必须**，每一步都要 | **否** —— `InMemoryStore` 进程内，重启即失；生产用 `AsyncPostgresStore` | 无 |
| **MemOS** (MemTensor/MemOS) | 10,838 | Apache-2.0 | v2.0.30 | 论文：plaintext/activation/parametric + MemCube；产品 2.0：L1 traces / L2 policies / L3 world model + Skills（**两套不要混用**） | 显式 API + MemScheduler 异步 | hybrid（FTS5 + vector） | **必须**（`MEMRADER_MODEL` 为必填抽取模型；reranker 是本地余弦不调 LLM） | 自建要 **Neo4j + Qdrant**；Local Plugin 可纯 SQLite | 仅自称 |

出处（逐条可核）：
- mem0：README「Mem0 requires an LLM to function, with `gpt-5-mini` from OpenAI as the default」/「Single-pass ADD-only extraction — one LLM call, no UPDATE/DELETE」— <https://github.com/mem0ai/mem0/blob/main/README.md>（2026-08-20 读）
- mem0 记忆类型只有 procedural 生效：<https://docs.mem0.ai/core-concepts/memory-types>（官方自述 semantic/episodic「never read anywhere else in the codebase」）
- mem0 抽取流程「Mem0 sends the messages through an LLM that pulls out key facts…」— <https://docs.mem0.ai/core-concepts/memory-operations>（2026-08-20 读）
- Letta 旧仓归档 commit `87fd37aa`（2026-08-16）— <https://github.com/letta-ai/letta/commit/87fd37aa>；新仓 <https://github.com/letta-ai/letta-code>
- Graphiti 双时间轴与失效：`graphiti_core/utils/maintenance/edge_operations.py`（行 570 / 822–823）— <https://github.com/getzep/graphiti/blob/main/graphiti_core/utils/maintenance/edge_operations.py>
- Graphiti 后端与 Kuzu deprecated：<https://github.com/getzep/graphiti/blob/main/README.md>
- Zep 仓定位变更：README「This repository is **not** Zep's product or service」+ `legacy/` 目录 — <https://github.com/getzep/zep/blob/main/README.md>
- cognee 冲突消解默认 no-op：`cognee/tasks/graph/resolve_temporal_contradictions.py` docstring「**Opt-in**…**The task is a no-op unless `functional_relationships` is given**」— <https://github.com/topoteretes/cognee/blob/main/cognee/tasks/graph/resolve_temporal_contradictions.py>
- LangMem 三分与 hot/background：<https://langchain-ai.github.io/langmem/concepts/conceptual_guide/>、<https://langchain-ai.github.io/langmem/guides/delayed_processing/>
- MemOS 必填模型：<https://github.com/MemTensor/MemOS/blob/main/docker/.env.example>

### 1.2 遗忘 / 降权 / 冲突消解 —— 横向结论

| | 机制 | 是否 LLM 判 | 默认是否生效 |
|---|---|---|---|
| mem0 | **已被移除**。2026-04 起 ADD-only、只增不改；去重只剩 `md5(text)` 精确匹配 | — | 无 |
| Graphiti | 打 `expired_at` **标记失效，不删除**；`remove_episode()` 才是真删 | **是**（`prompts/dedupe_edges.py` 让 LLM 判 `contradicted_facts`） | 是 |
| cognee | 打 `superseded` / `superseded_by` **标记，不删除**；另有一等公民 `forget()` | 否（靠人工声明单值关系） | **否，默认 no-op** |
| LangMem | 只有 delete by ID，冲突靠 LLM 在 consolidate 时自行处理 | 是 | — |
| Letta | 上下文滑窗压缩（30%）+ reflection 子 agent 做 dedup/矛盾消解 | 是 | 是 |
| MemOS | 未找到遗忘/失效描述 | — | — |

**四个项目全部没有时间衰减 / 热度降权**（`decay` 在 Graphiti 全仓零命中）。业界主流做法是**「打标不删除」+ 检索期排序**，不是真遗忘。

- mem0 官方迁移文档原话：「The previous algorithm used two LLM calls… **The new algorithm collapses this into a single call that only adds.**」「When information changes, **the new fact is stored alongside the old one.** Retrieval handles ranking.」— <https://docs.mem0.ai/migration/oss-v2-to-v3>
- **注意资料时效**：mem0 论文（arXiv:2504.19413 v1, 2025-04-28）描述的 ADD/UPDATE/DELETE/NOOP 双 LLM 调用架构**已是死代码**（prompt 仍在 `mem0/configs/prompts.py`，但主写入路径不再引用）。凡引用「mem0 每次 add 调两次模型」的二手资料均已过期。

### 1.3 「项目自称」与「第三方实测」的分界

**mem0 自称**：LoCoMo 92.5%（旧算法 71.4%），p50 延迟 0.88s、7.0K token。
**但 README 自己写着**：「Scores reflect Mem0's managed platform, which includes **proprietary optimizations not available in the open-source SDK**」——即 **92.5% 不是 OSS 可复现的数字，这是 mem0 自己承认的**。基准仓中 OSS 段落只有 LongMemEval 数据，没有 LoCoMo。
出处：<https://github.com/mem0ai/mem0/blob/main/README.md>、<https://github.com/mem0ai/memory-benchmarks>

**Zep 自称**（arXiv:2501.13956, 2025-01-20, 仅 v1）：DMR 94.8% vs MemGPT 93.4%；LongMemEval 提升「up to 18.5%」、延迟降 90%。**未找到任何第三方对 DMR / LongMemEval 的独立复现。**

**厂商互测（有完整一手证据链，值得完整记住）**：
1. 2025-05-06 Zep 博客《Is Mem0 Really SOTA in Agent Memory?》称 Zep LoCoMo 84%，mem0 graph ~68%，**且「全上下文」baseline ~73%（即 mem0 打不过「不用记忆」）** — <https://blog.getzep.com/lies-damn-lies-statistics-is-mem0-really-sota-in-agent-memory/>
2. 2025-05-08 mem0 CTO Deshraj Yadav 开 issue 反驳：Zep 分母算错（把 adversarial 类的正确数计入分子却从分母剔除），更正后 **58.44%±0.20** — <https://github.com/getzep/zep-papers/issues/5>
3. 2025-05-12 Zep 的 Daniel Chalef **承认算错**：「The corrected score is **75.14% +/- 0.17** (over 10 runs)」，但坚持反诉 mem0 把 Zep 配错了
4. 2025-05-19 issue 以「closing due to inactivity」关闭，**分歧从未收敛**

**Letta 的第三方视角**（厂商自评，但结论对本项目最有价值）：博客《Benchmarking AI Agent Memory: Is a Filesystem All You Need?》，2025-08-12 —
- Letta Filesystem + GPT-4o-mini **74.0%** vs mem0 最好的 graph 变体 **68.5%**
- 原话：「even simple **filesystem tools** are sufficient to perform well on retrieval benchmarks such as LoCoMo」，专用记忆工具「are less effective than simply allowing the agent to **autonomously search through data with iterative querying**」
- 同时指控 mem0 论文的 baseline 设置不公平：Letta 团队「was unable to determine a way to backfill LoCoMo data into MemGPT/Letta without significant refactoring」，且 mem0 对澄清请求「did not respond」。核对论文原表可印证：**MemGPT 在 mem0 论文里没有 LLM-as-a-Judge 分数**，只给 F1/BLEU-1，而其他所有 baseline 都有 J 分。
- <https://www.letta.com/blog/benchmarking-ai-agent-memory/>

**Letta Leaderboard 的认知更正**：`leaderboard.letta.com`（最后更新 2026-03-13）现在排的是 **LLM 模型**，不是记忆框架 —— 两个 suite 是 Filesystem Suite 与 Skills Suite，覆盖 22+ 模型，**不含 mem0/zep/cognee**。`letta-ai/letta-leaderboard` 仓已归档。<https://leaderboard.letta.com/>

### 1.4 其余 star 靠前的同类（2026-08-20 实抓）

| 仓 | stars | SPDX | 最后 push | 定位 / 需注意 |
|---|---:|---|---|---|
| supermemoryai/supermemory | 28,971 | MIT | 2026-08-20 | Memory + context engine，可完全本地跑 |
| mastra-ai/mastra | 27,328 | **NOASSERTION** | 2026-08-20 | TS agent 框架；`@mastra/memory` 是 Apache-2.0，但 `ee/` 目录走企业版 license |
| NevaMind-AI/memU | 14,323 | **NOASSERTION** | 2026-08-20 | 自定义许可，非 OSI，**商用前必须自读 LICENSE.txt** |
| basicmachines-co/basic-memory | 3,687 | **AGPL-3.0** | 2026-08-20 | 本地 Markdown 即记忆，理念与本项目最接近；**AGPL 传染性强** |
| modelscope/MemoryScope（现名 ReMe） | 3,328 | Apache-2.0 | 2026-08-20 | 阿里 ModelScope 出品 |
| memodb-io/memobase | 2,851 | Apache-2.0 | 2026-01-11（7 个月未动） | 用户画像式长期记忆 |
| BAI-LAB/MemoryOS | 1,556 | Apache-2.0 | 2026-07-07 | EMNLP 2025 Oral，**与 MemTensor/MemOS 同名不同项目** |
| agiresearch/A-mem | 1,152 | MIT | 2025-12-12 | 学术实现 |
| kingjulio8238/Memary | 2,639 | MIT | **2024-10-22，已停更近两年** | 不建议 |

不属于本类但搜索会命中：microsoft/graphrag（35,593/MIT，是 graph RAG）、zilliztech/claude-context（12,421/MIT，代码检索）、run-llama/llama_index（51,764/MIT，通用数据框架）。

---

## 二、benchmark 现状

### 2.1 LoCoMo —— 已经不能当主榜用

**出处**：Maharana et al., *Evaluating Very Long-Term Conversational Memory of LLM Agents*, ACL 2024, arXiv:2402.17753（2024-02-27 提交）<https://arxiv.org/abs/2402.17753>；数据 <https://github.com/snap-research/LoCoMo>

**数据是怎么造的**：合成。persona 取自 MSC 数据集 → gpt-3.5-turbo 扩写人设 → 生成时序事件图（每条 3–25 个事件，铺 6–12 个月）→ 两个 LLM agent 对话 → 人工编辑约 15% 的轮次、替换/删除约 19% 的图片。

**规模陷阱（关键）**：论文 Table 5 是 50 场 / 7,512 题、平均 9,209 token；但**公开发布的 `locomo10.json` 只有 10 场（"采样了最长的一批"）、1,986 题，去掉 adversarial 后 1,540 题，单场 16k–26k token**。所有人（mem0/Zep/Letta）跑的都是这个子集。mem0 论文里 full-context 一次喂进去是 **26,031 tokens**。

**指标漂移**：原论文用 token 级 F1 + BLEU-1；2025 年后几乎全改成 LLM-as-a-Judge（mem0 用 gpt-4o-mini 当 judge，称 "J score"）。**同名「LoCoMo 分数」的 judge、prompt、题目子集全都不同，横向不可比。** Mastra 实测换 judge prompt 会造成约 10 个百分点差异（<https://mastra.ai/research/observational-memory>，2026-02-09）。

**当前分数（全部标明性质）**：

| 系统 | 分数 | 性质 |
|---|---:|---|
| mem0（2026 官网） | 92.5 | 厂商自称（且自承 OSS 复现不出来） |
| Zep（2025-05 自我更正后） | 75.14 ± 0.17 | 厂商自称 |
| **Letta「文件系统 + grep」gpt-4o-mini** | **74.0** | 竞品实测 |
| **full-context baseline（全塞 26k token）** | **72.90 ± 0.19** | **mem0 论文自己的表** |
| mem0-graph | 68.44 ± 0.17 | 论文自称 |
| mem0 | 66.88 ± 0.15 | 论文自称 |
| Zep（mem0 复现） | 65.99 ± 0.16 | 第三方复现 |
| RAG 最好变体 | 60.97 | mem0 论文 |
| LangMem | 58.10 ± 0.21 | 第三方复现 |
| Zep（mem0 二次更正后） | 58.44 ± 0.20 | 第三方复现 |
| OpenAI Memory | 52.90 ± 0.14 | 第三方复现 |
| A-Mem | 48.38 ± 0.15 | 第三方复现 |

**「不用记忆」就打赢了所有专用记忆系统 —— 这一行写在 mem0 自己的论文表里。** 记忆系统赢的是成本与延迟（mem0 p95 1.44s / ~7k token，full-context p95 17.1s / ~26k token），不是准确率。

**已知质疑（三条，都有一手证据）**：

1. **上下文太短，全塞就赢。** Zep 博客原话：LoCoMo 对话平均 16,000–26,000 token，完全落在现代窗口内，「根本没法在压力下真正测试长期记忆检索」。<https://blog.getzep.com/lies-damn-lies-statistics-is-mem0-really-sota-in-agent-memory/>（2025-05-06）。这条被 mem0 自己的表和 Letta 的 74.0% 双重印证。
2. **标注有噪声、judge 会放行错答案。** Penfield Labs 逐题审计 1,540 题（2026-04，代码 <https://github.com/dial481/locomo-audit>，文 <https://penfieldlabs.substack.com/p/we-audited-locomo-64-of-the-answer>）：**99 题（6.4%）标准答案是错的**（含幻觉事实、时序算错、说话人张冠李戴 24 题）；对全部题目生成「故意写错但话题相关」的答案，官方同款 judge（gpt-4o-mini）**判对 62.81%** —— 明确的人名/日期错误能抓住约 89%，但含糊只答对话题的答案约三分之二蒙混过关。**结论：LoCoMo 的诚实上限约 93.6%，不是 100%。** 于是 92.5%、94.37% 这类分数本身就可疑。
3. **统计功效不足。** 公开子集类别极度不均衡（single-hop 841 题 vs open-domain 96 题，差 8.8 倍）；同一团队测算 **56% 的「按类别做的系统间比较」在统计上与噪声不可区分**。<https://penfieldlabs.substack.com/p/proposal-a-new-benchmark-for-long>（2026-04-09）

（第 1.3 节已记录 Zep ↔ mem0 关于 baseline 设置的完整互撕时间线：同一系统同一榜单，公开数字在 58.44 / 65.99 / 75.14 / 84 之间摆动 25 个点。）

### 2.2 LongMemEval —— 比 LoCoMo 结实，但也在饱和

**出处**：Di Wu 等（UCLA + Tencent AI Lab），arXiv:2410.10813（2024-10-14 提交，2025-03-04 修订），ICLR 2025。<https://arxiv.org/abs/2410.10813>、<https://github.com/xiaowu0162/LongMemEval>

**测什么**：5 类核心能力 —— information extraction / multi-session reasoning / temporal reasoning / knowledge updates / abstention。**500 题**，三个规模同题：`_S` ≈ 115k token/题（~40 session）、`_M` ≈ 1.5M token/题（~500 session，此数为二手，官方 README 未写，存疑）、`_Oracle` 只放证据 session。判分用 GPT-4o 当 judge。

**论文结论**：商用聊天助手与长上下文 LLM 在持续交互中记忆信息准确率**下降 30%**；长上下文 LLM 在 `_S` 上掉 **30–60%**。

**当前成绩**：

| 系统 | 分数 | 性质 |
|---|---:|---|
| OMEGA | 95.4 | 厂商自称 |
| Mastra Observational Memory（gpt-5-mini） | 94.87 | 厂商自称 |
| mem0 | 94.4 | 厂商自称 |
| **Emergence AI 纯 RAG（gpt-4o）** | **86.0** | 厂商自称 |
| **Oracle 基线（只喂证据 session）** | **82.4** | 基线 |
| Mastra 纯 RAG（调参后） | 80.0 | 厂商自称 |
| Zep（gpt-4o） | 71.2 | 厂商自称 |
| **full-context baseline（gpt-4o）** | **60.2** | 基线 |
| naive RAG | 52.0 | 基线 |

**这里 full-context 明显打不过记忆系统（60.2 vs 71.2）**，与 LoCoMo 相反 —— 所以「简单 baseline 总是赢」的说法只在 LoCoMo 上成立。但**调好的纯 RAG（86.0）超过 Oracle（82.4）**，Emergence AI 自己的结论是「高级记忆架构在这个 benchmark 上似乎是 overkill」。注意调参本身很贵：Mastra 自述为此烧掉 **$8k、38 亿 token**（<https://news.ycombinator.com/item?id=44597515>，2025-07-17）。

**Zep 论文的分题型表最有信息量 —— 记忆系统在某些任务上是净损失**（gpt-4o，full-context → Zep）：

| 题型 | full-context | Zep | 差 |
|---|---:|---:|---:|
| single-session-preference | 20.0% | 56.7% | **+36.7** |
| temporal-reasoning | 45.1% | 62.4% | +17.3 |
| multi-session | 44.3% | 57.9% | +13.6 |
| knowledge-update | 78.2% | 83.3% | +5.1 |
| **single-session-assistant** | **94.6%** | **80.4%** | **−14.2** |

即：**压缩／改写记忆在「要精确复述原话」的任务上是净损失。** 这条对本项目直接相关 —— 沉淀时把原话改写成摘要，会损失「精确复述当时的结论」这一类能力。

**已知质疑**：
- `_S` 装得进窗口，可以靠 context-stuffing 绕开记忆架构（Penfield Labs，2026-04-09）。但实证上只成立一半：full-context 只有 60.2%，装得下 ≠ 做得对（见 2.3 Context Rot）。
- 500 题分到 6 类后每类仅 30–133 题，统计功效有限。
- **官方自己承认有噪声**：GitHub README news 栏 —— 2025/09 发布「清洗版数据集，以减少答案互相干扰」；**2026/05 发布 LongMemEval-V2**（451 题、100–498 session、haystack 最大 115M token、web agent 轨迹、含多模态）<https://xiaowu0162.github.io/longmemeval-v2/>。V2 目前**还没有第三方系统提交**。

### 2.3 长上下文侧的关键证据：装得下 ≠ 做得对

| Benchmark | 出处 / 日期 | 关键数字 |
|---|---|---|
| **Chroma "Context Rot"** | Kelly Hong, Anton Troynikov, Jeff Huber，**2025-07-14** <https://www.trychroma.com/research/context-rot> | 18 个模型（Claude Opus 4/Sonnet 4/3.7/3.5/Haiku 3.5、o3、GPT-4.1 系列、GPT-4o、Gemini 2.5 Pro/Flash、Qwen3 三档）。**性能随输入变长而非均匀退化，连极简任务也是**；**LongMemEval 上把 prompt 从 113k token 削到 ~300 token 的聚焦版，准确率显著上升，18 个模型无一例外**；needle 与问题语义相似度越低，退化越快；**加一个干扰项就掉分**；**打乱顺序的 haystack 一致优于结构连贯的 haystack** |
| **Lost in the Middle** | Liu et al., TACL 2024, arXiv:2307.03172（2023-07-06 提交，2023-11-20 修订） <https://arxiv.org/abs/2307.03172> | **U 型曲线**：相关信息在开头或结尾时准确率最高，**在中间时显著退化**；该现象**在显式长上下文模型上同样存在**。原文结论：模型「do not robustly make use of information in long input contexts」 |
| **RULER** | NVIDIA, arXiv:2404.06654, COLM 2024 | 17 个模型宣称 ≥32K，**只有一半能在 32K 上维持可接受表现** |
| **NoLiMa** | arXiv:2502.05167, 2025 | 去掉 needle 与问题的字面重叠后，12 个宣称 ≥128K 的模型里 **10 个到 32K 时掉到短上下文基线的 50% 以下**；GPT-4o 99.3% → 69.7% |
| **HELMET** | Princeton, arXiv:2410.02694, ICLR 2025 | 59 个长上下文模型；**NIAH 这类合成任务不能可靠预测下游表现** |

### 2.4 2026 年该看的榜

- **BEAM**（arXiv:2510.27246, ICLR 2026）：100 场对话、2,000 道人工校验题、10 种记忆能力，四档长度 **128K / 500K / 1M / 10M token**。结论：即便 1M 窗口模型（加不加检索都一样）随对话变长都撑不住。成绩全是厂商自称且**三方数据互相不自洽**（cognee 报 mem0 0.64、mem0 自报 BEAM-1M 64.1，档位对不上）——不要混用。
- **MemoryAgentBench**（arXiv:2507.05257, 2025-07-07）：accurate retrieval / test-time learning / long-range understanding / **selective forgetting**。结论：**没有任何一种方法四项全能**。
- **LongMemEval-V2**（2026-05）。

### 2.5 对本项目的三条硬结论

1. **LoCoMo 已不能作为「我的记忆方案有没有用」的证据**（26k 全塞就 72.9、6.4% 错答案、judge 放行 62.81% 错答）。要引用别人的分数时必须同时问：哪个子集、哪个 judge、跑了几次。
2. **报任何自建方案的效果时，必须同时报三个基线**：全塞（full-context）、调好的 BM25/关键词检索、以及「文件系统 + grep」。少任何一个，结论都站不住 —— Zep/mem0/Letta 已经互相用这一招把对方的数字打掉过 10–25 个点。
3. **「压缩改写」有代价**：Zep 在 LongMemEval 的 `single-session-assistant` 上比 full-context **低 14.2 个点**。本项目沉淀时若把 Owner 原话改写成摘要，会牺牲「精确复述当时的原话/结论」这一类查询。**保留原文指针（文件+行号/会话 ID）比保留摘要更重要。**

---

## 三、「写下来了但下次还是被问」的成因与已验证解法

把这个现象拆开，业界证据支持**五个互相独立的失效点**。它们需要不同的修法，混在一起谈就修不好。

### 成因 A：根本没写下来（本项目的主症）

〔本机实测〕`sediment.py` 产出的 `AGENT_BRIEF.md` 五个小节全是**统计**：问过几次、烧了多少 token、每场几次报错、工具分布。**没有任何一个字段承载「上次的答案／结论是什么」。** 唯一的行动建议是固定文案「固化成模板／脚本／skill；下次先查这里再动手」（`sediment.py` 第 68 行）。

所以严格说，这条流水线**从未把答案写下来过**；它写下来的是「你为这个问题付了多少钱」。用它去解决「下次别再问」，方向就不对。

### 成因 B：写下来了，但那次会话根本没加载

〔官方文档〕Claude Code 的加载规则是**位置决定的，不是内容决定的**：

- 「CLAUDE.md and CLAUDE.local.md files in the directory hierarchy **above** the working directory are **loaded in full at launch**. Files in **subdirectories load on demand** when Claude reads files in those directories.」
- 压缩之后：「Project-root CLAUDE.md survives compaction… **Nested CLAUDE.md files in subdirectories and rules with `paths:` frontmatter are not re-injected automatically**; they reload the next time Claude reads a file in that subdirectory.」
- 「CLAUDE.md content is delivered as a **user message after the system prompt**, not as part of the system prompt itself… there's **no guarantee of strict compliance**.」

出处：<https://code.claude.com/docs/en/memory>（2026-08-20 读）

〔官方文档〕Cursor 的四种规则激活方式里，只有 `alwaysApply: true` 是保证加载的；`globs` 靠**文件路径匹配**；**Agent Requested 靠模型读 `description` 自行判断要不要加载** —— 这一档天生会漏。<https://cursor.com/docs/context/rules>

〔官方文档〕Skills 同理：「Claude matches your task against skill descriptions to decide which are relevant. **If descriptions are vague or overlap, Claude may load the wrong skill or miss one that would help.**」<https://code.claude.com/docs/en/features-overview>

**结论：凡是靠「模型看描述自己判断要不要读」的通道，都有稳定的漏读率。确定性通道（glob 路径匹配、hook 事件）才是保证。**

### 成因 C：加载了，但被稀释掉了

〔独立第三方〕Chroma "Context Rot"（2025-07-14，18 个模型）：**同一道 LongMemEval 题，把 prompt 从 113k token 削到 ~300 token 的聚焦版，准确率显著上升，18 个模型无一例外**；加一个干扰项就掉分；needle 与问题语义相似度越低退化越快。<https://www.trychroma.com/research/context-rot>

〔独立第三方〕Lost in the Middle（TACL 2024，arXiv:2307.03172）：U 型曲线，中间位置的信息被显著忽略，长上下文模型也一样。

〔官方文档〕Anthropic 自己把这条写进了最佳实践，措辞很硬：
- 「**Bloated CLAUDE.md files cause Claude to ignore your actual instructions!**」
- 「**If Claude keeps doing something you don't want despite having a rule against it, the file is probably too long and the rule is getting lost.**」
- 「**The over-specified CLAUDE.md.** If your CLAUDE.md is too long, Claude ignores half of it because important rules get lost in the noise.」
<https://code.claude.com/docs/en/best-practices>（2026-08-20 读）

### 成因 D：加载了，但检索不到（语义 vs 字面）

〔厂商实测，有数字〕Anthropic《Contextual Retrieval》（2024-09-19）在自有语料上：
- contextual embeddings 单独：top-20 检索失败率 **5.7% → 3.7%（降 35%）**
- **contextual embeddings + contextual BM25：5.7% → 2.9%（降 49%）**
- 再加 reranking：**5.7% → 1.9%（降 67%）**
- 并指出**字面匹配在精确标识符上胜过语义 embedding**：「BM25 looks for this specific text string to identify the relevant documentation」（例如 "Error code TS-999"）
<https://www.anthropic.com/news/contextual-retrieval>

**对本项目的直接含义**：沉淀内容里大量是路径、仓名、命令、错误码、专有名词（`~/.memory-atlas`、`InfrequentAccess`、`push_brief.sh`、`R2 IA`）—— 这正是 **BM25/关键词命中率高于 embedding** 的那一类。加上运行期零模型红线，**关键词/BM25 索引不是妥协方案，而是这个场景下本来就更对的方案**。

〔厂商实测〕同文给出一条阈值：「**If your knowledge base is smaller than 200,000 tokens (about 500 pages of material), you can just include the entire knowledge base in the prompt**」。本项目沉淀语料（`AGENT_BRIEF.md` 11.6KB + 9 个仓 AGENTS.md 约 90KB + 27 个记忆主题文件）**总量远低于 200k token**，理论上「全塞」是可行的 —— 但成因 C 说明全塞会被稀释。**正确解法不是全塞，也不是建向量库，而是「小而准的按需注入」。**

### 成因 E：只给了地址，没给内容（本项目现状）

〔本机实测〕`~/.memory-atlas/announce-devnotes.sh` 在 `SessionStart` 注入的是**一个地址加一条 `gh api` 命令**，不是内容本身。这意味着：
1. 要花掉一次网络往返 + 认证，agent 才可能拿到正文；
2. **没有任何机制检查它到底取没取**。

**本次会话本身就是反例**：SessionStart 注入了指针、`CLAUDE.md` 里写着「先查再问」，而我直到为了找 `sediment.py` 去翻文件系统时才偶然看到 `AGENT_BRIEF.md` —— **全程没有执行过那条 `gh api`**。一个被注入的指针，实测转化率在本会话是 0。

### 已验证的解法（按证据强度排序）

| 解法 | 证据 | 强度 |
|---|---|---|
| **渐进披露：索引常驻 + 正文按需** | Anthropic Agent Skills 三层加载（metadata → SKILL.md → 引用文件），「Progressive disclosure is the core design principle」<https://www.anthropic.com/engineering/equipping-agents-for-the-real-world-with-agent-skills>（2025-10-16）；Claude Code auto memory：`MEMORY.md` 索引前 200 行/25KB 常驻，**topic 文件不在启动时加载，按需读** | 〔官方文档〕，且**本机已在运行**（27 个主题文件 + 28 行索引） |
| **聚焦注入优于全量注入** | Context Rot：300 token 聚焦版 vs 113k 全量版，18/18 模型聚焦版更好 | 〔独立第三方，有数字〕 |
| **混合检索（关键词 + 语义）优于单一** | 检索失败率 −49%（+rerank −67%） | 〔厂商实测，有数字〕 |
| **确定性触发优于语义触发** | 官方明说 hook「Always fires on its event; **the trigger is guaranteed**」、context cost「**Zero**, unless the hook returns output」；而 skill/Agent-Requested 规则「may load the wrong skill or miss one」 | 〔官方文档〕 |
| **规则要短** | 见第四节 | 〔官方文档〕 |
| **保留原文指针而非摘要** | Zep 在 LongMemEval `single-session-assistant` 上比 full-context **低 14.2 点** | 〔厂商自评表，但方向明确〕 |
| 「文件系统 + grep」就能打赢专用记忆系统 | Letta 74.0% vs mem0 68.5%（LoCoMo, gpt-4o-mini） | 〔竞品实测〕 |

---

## 四、规则文件的实证结论（长度、结构、位置）

### 4.1 各家官方给出的硬数字

| 生态 | 官方长度建议 | 原文 | 出处 |
|---|---|---|---|
| **Claude Code / CLAUDE.md** | **< 200 行** | 「**target under 200 lines per CLAUDE.md file. Longer files consume more context and reduce adherence.**」 | <https://code.claude.com/docs/en/memory>（2026-08-20 读） |
| Claude Code / auto memory | **硬上限 200 行或 25KB** | 「The **first 200 lines of `MEMORY.md`, or the first 25KB**, whichever comes first, are loaded at the start of every conversation. **Content beyond that threshold is not loaded at session start.**」超限时写入仍成功但会返回错误要求重写索引 | 同上 |
| **Cursor / `.mdc`** | **< 500 行** | 「**Keep rules under 500 lines**」「**Split large rules into multiple, composable rules.**」 | <https://cursor.com/docs/context/rules> |
| **GitHub Copilot** | **不超过 2 页** | 「**Instructions must be no longer than 2 pages.**」 | <https://docs.github.com/en/copilot/how-tos/configure-custom-instructions/add-repository-instructions> |
| **AGENTS.md** | **无长度规定** | 只说「Add sections that help an agent work effectively」「just standard Markdown」 | <https://agents.md/> |

**三家给了上限，一家没给。** 三个数字互不相同（200 行 / 500 行 / 2 页），说明这不是一个被严格测出来的常数，而是各家的工程经验值 —— 引用时要说清是谁的口径。

### 4.2 「太长会有反效果」——官方承认，独立研究给出机制

〔官方文档〕Anthropic 的措辞是三家里最直白的：
- 「Longer files consume more context and **reduce adherence**」
- 「**Bloated CLAUDE.md files cause Claude to ignore your actual instructions!**」
- 「If Claude keeps doing something you don't want despite having a rule against it, **the file is probably too long and the rule is getting lost**」
- 逐行自检法：「For each line, ask: *"Would removing this cause Claude to make mistakes?"* **If not, cut it.**」
- **`/doctor` 会自动提议裁剪**：「it cuts content Claude can derive from the codebase, such as directory layouts, dependency lists, and architecture overviews, and **keeps pitfalls, rationale, and conventions that differ from tool defaults**」

〔官方文档〕Cursor 侧的对应建议是**降低 always-apply 的用量**（多数规则应走 Auto Attached / Agent Requested），文档本身**未给出 token 开销或性能影响的量化说明**（我实读确认「无此陈述」）。

〔独立第三方〕机制层面的证据是 Context Rot（2025-07-14，18 个模型）与 Lost in the Middle（TACL 2024）—— 见第三节。两者都不是针对规则文件做的实验，但结论可直接迁移：**输入越长越不可靠；中间位置的信息最容易被忽略。**

〔未找到〕**我没有找到任何一份「同一任务、短 rules vs 长 rules」的公开 A/B 实测数据。** 这一格是空的。凡是断言「CLAUDE.md 超过 N 行性能下降 X%」的说法，目前都没有可复现的实验支撑 —— 只有官方经验值 + 长上下文的间接证据。**若本项目要拿这条当决策依据，只能自己做 A/B。**

〔社区意见，非实证〕本轮 WebSearch 配额耗尽，未能系统采集 Reddit/HN/Cursor forum 的高赞讨论。搜索结果中出现的若干二手文章（morphllm、blink.new、DataCamp 等）复述的是 Cursor 官方那两句「under 500 lines」「split into composable rules」，**没有增量证据，不值得引用**。

### 4.3 位置与加载顺序（决定「有没有真的被读到」）

〔官方文档，Claude Code〕
- **加载顺序：从文件系统根向下到工作目录**，越靠近启动目录的越晚读；同一层里 `CLAUDE.local.md` 排在 `CLAUDE.md` 之后。→ **配合 Lost in the Middle 的 U 型曲线，「离工作目录最近」的规则天然占据「结尾」这个高注意力位置。**
- **子目录的 CLAUDE.md 不在启动时加载**，只有当 Claude 读到该目录下的文件时才加载。
- **压缩后**：项目根 CLAUDE.md 会重新注入；**嵌套 CLAUDE.md 和 `paths:` 规则不会**。
- `@path` 导入**不省 context**：「Splitting into `@path` imports helps organization but **doesn't reduce context**, since imported files load at launch.」导入最多 4 跳。
- **`<!-- -->` 块级 HTML 注释在注入前被剥除** —— 给人看的维护说明可以放注释里，不花 token。
- **路径作用域规则**（`.claude/rules/*.md` 带 `paths:` frontmatter）是唯一「零模型、确定性、按需加载」的通道：靠 glob 匹配触发，不靠模型判断。

〔官方文档，Cursor〕四档激活：`alwaysApply: true`（每次都进）／`globs`（路径匹配自动挂载）／`description`（**模型自行判断**）／`@ruleName`（手动）。

〔官方文档，Copilot〕`.github/copilot-instructions.md` 全仓生效；`.github/instructions/*.instructions.md` 用 frontmatter `applyTo` 的 glob 限定路径。也支持 `AGENTS.md`（就近者优先）。

### 4.4 AGENTS.md 生态的事实

- 由 **Agentic AI Foundation（Linux Foundation 旗下）** 托管，参与方包括 OpenAI Codex、Amp、Google Jules、Cursor、Factory。
- 官网自称 **「used by over 60k open-source projects」**，并给了一个 GitHub 搜索链接作为证据。**该数字页面上没有标注日期**（2026-08-20 读到）。
- 解析规则：「Agents automatically read **the nearest file in the directory tree**, so the closest one takes precedence」。
- **Claude Code 不读 `AGENTS.md`**，官方建议在 `CLAUDE.md` 里 `@AGENTS.md` 导入，或做符号链接。
出处：<https://agents.md/>、<https://code.claude.com/docs/en/memory>

### 4.5 渐进披露：官方给的替代方案

〔官方文档〕Agent Skills 的三层加载（Barry Zhang / Keith Lazuka / Mahesh Murag，2025-10-16）：
- **Level 1 metadata**（name + description）进 system prompt，常驻
- **Level 2 SKILL.md 正文**，判定相关时才加载
- **Level 3+ 引用文件**，需要时才读
- 原话：「Progressive disclosure is **the core design principle** that makes Agent Skills flexible and scalable」；「Agents with a filesystem and code execution tools **don't need to read the entirety of a skill into their context window**」
- **该文没有给出任何 token 开销的具体数字**（我实读确认）。<https://www.anthropic.com/engineering/equipping-agents-for-the-real-world-with-agent-skills>

〔官方文档〕context 成本表（<https://code.claude.com/docs/en/features-overview>）：

| 机制 | 何时加载 | 加载什么 | context 成本 |
|---|---|---|---|
| CLAUDE.md | 会话开始 | 全文 | **每次请求都在** |
| Skills | 会话开始 + 使用时 | 描述常驻，正文按需 | 低 |
| MCP | 会话开始 | 只有工具名，schema 按需 | 用之前很低 |
| **Hooks** | 事件触发 | **什么都不加载（外部执行）** | **零，除非 hook 返回输出** |

**这张表是本项目最重要的一条设计依据**：hook 是唯一「零常驻成本 + 触发有保证」的通道。

### 4.6 小结：本项目该采纳的四条

1. **常驻的东西必须短**。官方口径 < 200 行；本机 `~/.dsh/AGENTS.md` 已 332 行（见第五节）。
2. **长内容改成「索引常驻 + 正文按需」**，而不是靠 `@import`（导入不省 context）。
3. **要「保证被执行」就用 hook，不要用规则文字**。官方原话：「An instruction like "never edit `.env`" in CLAUDE.md or a skill is **a request, not a guarantee**. A `PreToolUse` hook that blocks the edit is **enforcement**.」
4. **重要规则放靠近工作目录的那一层**（读得最晚 = 结尾位置 = 高注意力），不要埋在长文件中段。

---

## 五、现有 `sediment.py` + `AGENTS_CONTRACT.md` 的差距

> 读的是本机在跑的那一份：`~/.memory-atlas/src/atlas/`（**atlas v0.5.1**，2026-08-20 23:00 安装）。
> 说明：任务里给的路径 `AgentDatabase/atlas/build/sediment.py` 当时不存在 —— 代码在 worktree `_scratch/AD-polish/atlas/` 里，且该 worktree 在本次调研过程中被清理掉了。已核对 `~/.memory-atlas/src/atlas/` 与我读到的内容逐字一致（229 行 / 116 行 / 485 行）。
> 另一条重要前提：**契约分发（0.4.2）与复利层（0.5.0）都是今天（2026-08-20）才上线的**，所以下面凡是「执行率为 0」的观测，是**机制缺失的证据，不是执行不力的证据** —— 观测窗口只有几个小时。

### 5.1 已做对的（有业界对照的）

| 做对的事 | 代码位置 | 为什么这是对的（外部对照） |
|---|---|---|
| **运行期零模型** | `sediment.py` docstring、`compound.py` 第 21 行 | 6 个成熟项目**写入端全部强依赖 LLM**，无一有零模型模式。而 Letta 实测「文件系统 + grep」在 LoCoMo 上 74.0% 打赢 mem0 68.5%；Anthropic 实测 BM25 对精确标识符优于 embedding。**这不是妥协，是这个场景下更对的选择。** |
| **「只降不升」的证据上限** | `compound.py:_evidence_ceiling` / `project_candidates` 里的 `clamps` | 与 Graphiti 的 `expired_at`、cognee 的 `superseded` 同构（打标不删除），且**比 mem0 更完整** —— mem0 已在 2026-04 把冲突消解整个删掉了 |
| **压回时留审计记录** | `clamps` 列表一路带到页面 | 「静默跳过」是假绿的标准形态；这里选了「读到几个、拒了几个、为什么拒」 |
| **金额未知留 `null` 不填 0** | `compound.py` NOT_MEASURED / `economic_rollup` | 缺失语义正确。同一份代码里 `hit_rate` 分母为 0 写 `None` 也是同一原则 |
| **哨兵注释整段替换的分发器 + `--check` 漂移检测** | `install_agents_md.sh` | 五个入口手工同步必然漂移；这一步是对的。官方也用同一思路（Claude Code `/import` 一次性拷贝、`claudeMdExcludes` 排除） |
| **去抖 + 目录锁 + 残留锁超时清理，无死等** | `on_archive.sh` 30 分钟去抖、`daily.sh` 180 分钟锁超时 | 与 LangMem 的 background + debounce 同构；也符合本机既有教训「禁止无上限等待循环」 |
| **推送前核对目标仓可见性** | 契约「不是 PRIVATE 就直接拒绝推送」 | 语料含 Owner 原话，这条必须由代码执行 |
| **允许 NO_PROMOTION** | `compound.py:pick_champion` + `champion_note` | 「逼着每周造一个 Skill 是把这套东西做坏的方式」——与 Letta 的结论（专用记忆工具往往不如让 agent 自己搜）方向一致 |

### 5.2 缺的（每条带本机实测数据）

| # | 缺什么 | 实测证据 |
|---|---|---|
| **1** | **只沉淀「问题被问了几次」，不沉淀「答案是什么」** | `to_markdown()` 五个小节全是统计；唯一行动建议是固定文案「固化成模板／脚本／skill」（`sediment.py:68`）。**没有任何字段承载结论。** 这是「写下来了还找不到」的根因 —— 答案从未被写下 |
| **2** | **提问那一刻没有任何检索** | 回测 4731 场：剔除同日 ≥10 次的扇出后剩 1861 场，其中 **260 场（14.0%）在会话开始时，简报里已存在「同前缀且已出现 ≥3 次」的记录**；跨天复现 497 场。这些都是本可以在提问那一刻命中却没有命中的 |
| **3** | **注入的是地址不是内容，且无人检查取没取** | `announce-devnotes.sh` 只注入一个 `gh api` 命令。**本次会话实测转化率 0**：指针注入了、`CLAUDE.md` 写着「先查再问」，而我全程没执行那条命令，是翻文件系统时才偶然读到 `AGENT_BRIEF.md` 的 |
| **4** | **`topics` 恒为空** | 实测 `~/.memory-atlas/out/*.sessions.jsonl` 共 **4814 场，带非空 topics 的 0 场**。原因：`assign_topics()` 只在 `build.py:216` 运行（IDF 权重要全语料算完才知道），而 `sediment.py` 读的是 extract 阶段的原始记录。后果：每个项目简报的「常见话题：—」**结构性恒空** |
| **5** | **报错信号用错了字段** | 现在用 `joined.lower().count("error") + joined.count("报错")`（`extract.py:333`），统计的是**用户打了几次「error」这个词**（AgentDatabase 每场 0.4 次）。而原始记录里有客观得多的信号：抽样最近 300 个 Claude Code 会话文件，**78% 含 `"is_error":true`，平均每场 6.9 次真实工具失败**。`extract.py:250` 认得 `tool_result` 块却只用来计数，**从不读 `is_error`** —— 最好的零模型错误信号被扔掉了 |
| **6** | **只看每场的第一句** | `sediment.py:55` 只用 `prompts[0]`。实测：语料里共捕获 **8,071 条提示词，只有 4,711 条（58%）参与判重，42% 被忽略**；且 `MAX_PROMPTS=12`、`PROMPT_CHARS=400` 本身还有截断 |
| **7** | **把「扇出批处理」和「真人跨天重问」混成一张表** | 实测 182 个重复组中 **161 个（88%）只跨 1 天**；头部 15 行里 **11 行是同一天**；真正跨 ≥2 天的只有 **21 组**（首末间隔中位 4 天、最大 154 天）。表头「问过 738 次…别再问一遍」对那一行是**错的定性** —— 那是一天内的一次批处理，不是问了 738 遍 |
| **8** | **写回环节没有任何验证** | 契约要求收尾时把结论写进对应仓 `AGENTS.md`（结论/为什么/代价三段式）。实测 7 个仓：**三段式条目 0 条**（散见 4 处正文提及）。同时契约要求 Kimi Code GUI 与 DSH「必须自己跑那一行」，**无任何校验手段**。⚠️ 契约今天才分发，此项是**机制缺失**的证据 |
| **9** | **归档链路会静默失败** | `on-archive.log` 实测 **2026-08-20T09:52:57Z**：`sediment.py: error: unrecognized arguments: --web`（已安装副本比调用方旧）+ `push_brief.sh: No such file or directory`，结果只写了一行「归档刷新失败」到日志。**没有任何面向人或 agent 的告警**；如果那次之后没人改，沉淀会一直停在旧数据上而无人察觉 |
| **10** | **没有失效／降权，结论不带时间** | 简报每天全量重算，旧结论既不过期也不标记；`AGENTS.md` 里人写的结论没有时间戳。对照：Claude Code auto memory 会给带 frontmatter 的记忆文件写 `modified` ISO 时间戳；Graphiti 打 `expired_at`；cognee 打 `superseded` |
| **11** | **与本机已在运行的另一套记忆完全不联动** | `~/.claude/projects/<proj>/memory/` 下已有 **28 行的 `MEMORY.md` 索引 + 27 个主题文件**，每次会话**自动加载**（前 200 行/25KB）。契约里一个字没提。**两套记忆并行、互不知道对方存在** —— 而自动加载的那一套恰恰是唯一真的每次都进上下文的 |
| **12** | **契约块本身吃掉了大部分常驻预算** | 契约 116 行。实测占比：`~/.kimi-code/AGENTS.md` **116/119 = 97%**；`~/.claude/CLAUDE.md` 116/153 = 76%；`GithubProject/AGENTS.md` 116/126 = 92%。官方口径是整份 < 200 行 —— **一份「怎么写沉淀」的元规则吃掉六成以上常驻预算，而它本身不含任何项目知识**。另：`~/.dsh/AGENTS.md` 332 行，超官方建议 66% |

### 5.3 做法过时的

| # | 过时在哪 | 说明 |
|---|---|---|
| **1** | **全量重算 + 全量覆盖式产物** | 每次归档把 4,814 场重算一遍、整份覆盖。没有增量或差分，**回答不了「这一轮新增了什么」** —— 而「新增了什么」正是唯一值得注入的东西。业界方向（Agent Skills 三层、auto memory 索引 + 主题文件）都是**索引常驻 + 正文按需**，不是一份大 Markdown |
| **2** | **前缀 26 字判重：不是主要瓶颈，但两头都不准** | 我做了近重复实验（4-gram Jaccard≥0.6，按时间顺序判）：**prefix-26 对「重复」的召回其实有 91.7%（跨天 85.1%）** —— 所以「换语义检索能大幅提升召回」的直觉是**错的**，不该按这个方向投入。真正的问题是两头都不准：**过合并**（`拆分评分标准…` 与 `你是Otto von Bismarck…` 因前缀相同被并成 327 场一组）＋**过切分**（同一族评委 prompt 被切成 **43 个 key、共 67 场**）。这只影响表的可读性，不影响是否该注入 |
| **3** | **人／机器区分完全没做，且是死代码** | `extract.py:195` 的 `session_kind()` 无条件 `return ""`；`AUTO_PROMPTS` 常量定义了却没被使用。而 `MEMORY.md` 里已经记着「2826 场里只有 952 场是本人」。于是 `sediment.py` 只能靠 `if s.get("prompts")` 当过滤器，注释里也承认「标签必须说清楚，不能叫『真人会话』」—— 说清楚了，但**没能力分开** |
| **4** | **靠规则文字要求行为，而不是靠钩子保证** | 契约第 1、2 步（复审、写进 AGENTS.md）完全靠 agent 自觉。官方原话：「An instruction like "never edit `.env`" in CLAUDE.md or a skill is **a request, not a guarantee**. A `PreToolUse` hook that blocks the edit is **enforcement**.」第 3 步已经上了钩子（PreCompact/SessionEnd），第 1、2 步没有，也没有事后校验 |
| **5** | **单一大 Markdown 的呈现方式** | 190 行 / 11.6KB 的 `AGENT_BRIEF.md`，要么全塞（被 Context Rot 稀释）要么不读（现状）。Chroma 实测：**同题从 113k 削到 ~300 token 的聚焦版，18/18 模型都更准** |

---

## 六、「运行期零模型」约束下仍然可行的 5 个改进（按预期收益排序）

> 五条全部满足：运行期不调任何模型、不需要外部数据库、不需要 embedding。
> 每条都给了**可量化的验收口径和负控**——「更好找了」不算验收。

### 改进 1：把注入从「会话开始给地址」改成「提问那一刻给命中项」

**怎么做**
- 离线（每日 / 归档时）派生一份 `brief_index.jsonl`：每行一条候选，字段为 `{terms:[…], line:"一句话", pointers:[…], first_seen, last_seen, n}`。`terms` 取**字面词元**：路径片段、仓名、命令名、错误码、专有名词、中文 2–4 字切片。
- 运行期挂 **`UserPromptSubmit` 钩子**（官方确认该事件能拿到用户 prompt，并可用 `hookSpecificOutput.additionalContext` 或纯 stdout 注入上下文；`command` 类默认超时 30 秒）。钩子用 **Python 标准库做 BM25／字面打分**，命中就注入 **≤3 条、每条 ≤2 行**；无命中注入空串。
- 索引同时覆盖三个来源：`AGENT_BRIEF.md` 的重复项、各仓 `AGENTS.md` 的结论条目、以及**已经在自动加载的 `~/.claude/projects/<proj>/memory/` 主题文件**（把两套记忆并到一个索引里，见差距 5.2-11）。

**为什么不需要模型**
- BM25 是算术，不是推理。Anthropic 实测：contextual embeddings **+ BM25** 把检索失败率从 5.7% 降到 2.9%（−49%），并明确指出**精确标识符上字面匹配优于语义 embedding** —— 而本项目的沉淀内容几乎全是路径、命令、错误码。
- 钩子的 context 成本官方写明「**Zero, unless the hook returns output**」，触发「**Always fires on its event; the trigger is guaranteed**」——不依赖模型判断要不要读。

**怎么验证有效（量化）**
| 指标 | 基线（已实测） | 目标 |
|---|---|---|
| 注入命中率上限（剔除批处理扇出后） | **对「扇出」的定义极其敏感**，实测：剔除同日同前缀 ≥5 次 → 4.6%；**≥10 次 → 14.0%**；≥20 次 → 21.3%；≥50 次 → 33.2% | **先把扇出剔除规则写死并公布，再谈命中率** —— 否则这个指标可以随便调到好看。建议锁定 T=10，目标为实际命中 ≥ 上限的 70%（即 ≥9.8%） |
| 跨天重复组新增次数 | 当前 **21 组**跨天，首末间隔中位 **4 天** | 30 天内新增跨天重复组数下降；同一组不再产生第 4 次以后的复现。**这个指标不受扇出定义影响，比命中率更可信，应作为主指标** |
| 单次注入 token | — | **中位 < 300 token**（对齐 Context Rot 的聚焦阈值）；无命中时必须为 **0** |
| 无关注入率 | — | 人工抽 30 次命中，判「这条与我要做的事有关吗」，**≥80% 判有关**才算通过 |

**负控（必须单独跑，不许只跑正例）**
1. 造一个语料里从未出现过的问题 → 必须 **0 注入**（防「什么都命中」的假绿）。
2. 造一个已知重复问题 → 必须命中且给出正确指针。
3. 把索引文件删掉 → 钩子必须**静默成功**（不能阻断用户提问），并在日志留痕。

**⚠️ 不要用「省了多少 token」当指标。** 中文社区一份配对实测（V2EX #1228396，140 次 Codex run）测出：**cached input 占总 token 的 96.46%、占成本的 63.91%，模型输出只占 token 的 0.38%** —— 所以任何针对「注入体积」的优化映射到总成本上都不足 1%。该文提出的指标是 **「每个成功完成任务的总成本」**（附方差、轮数、时长、验证结果）。本项目应照搬这个口径：注入的价值来自**少返工一次**，不来自省下几百 token。

---

### 改进 2：沉淀「答案的指针」，而不是「问题的频次」

**怎么做**
在 `repeats` 每一组上补三个**可确定性派生**的字段（全部来自工具调用的结构化记录，不需要理解语义）：
- `artifacts`：该组**最后一次**会话里 Write/Edit 触碰过的文件路径
- `commands`：该组会话里成功执行过的 Bash 命令（去重、取频次最高的 3 条）
- `commits`：当天该仓的 commit hash（`github.json` 已经在拉了）

产出的一行长这样（示意，不是代码）：`问过 N 次 → 最后一次落在 <path>，用的是 <cmd>，commit <hash>`。**不写摘要、不改写原话** —— 只给指针。

**为什么不需要模型**
`tool_use` 的 `name` 与 `input.file_path` / `input.command` 都是结构化字段，`extract.py` 已经在解析同一批块（`extract.py:315` 已在统计 `tool_names`），只是没保留参数。

**怎么验证有效（量化）**
| 指标 | 目标 |
|---|---|
| 指针可核率 | 卡片里的路径/commit **≥95% 能被解析且目标存在**（自动校验，跑不通就是坏卡片） |
| 「够不够用」 | 人工抽 20 条，判「只看这一行，下一个 agent 能不能不重问」，**≥60% 通过**才算这层有价值 |
| 覆盖率 | 跨天重复组（当前 21 组）中**能产出非空指针的比例 ≥80%** |

**依据**：Zep 在 LongMemEval 的 `single-session-assistant` 上比 full-context **低 14.2 个点** —— 压缩改写会牺牲「精确复述当时的东西」。**保留指针优于保留摘要。**

**负控**：故意构造一条「会话里什么文件都没改」的重复组 → 必须产出空指针并如实标「没有产物」，**不许编一个路径**。

---

### 改进 3：口径修正三件套（让简报说的是真的）

现在的简报有三处在说不准确的话，都是纯计数问题，改起来最便宜。

**(a) 把「同日扇出」和「跨天重问」拆成两张表。**
实测：182 组里 **88% 只跨 1 天**，头部 15 行有 **11 行是同一天**。「问过 738 次 … 别再问一遍」对那一行是错的定性 —— 那是一次批处理。拆开后：表一「一次批处理里重复了 N 次」（该固化成脚本），表二「隔了 N 天又问了一遍」（该固化成结论）。**这两件事的修法完全不同，混在一起两件都修不好。**
验收：表二的每一行**跨天数 ≥2**（硬断言）；表一每一行**跨天数 =1**。

**(b) 修 `topics` 恒空。**
实测 4814/4814 场 topics 为空，导致每个项目简报「常见话题：—」结构性恒空。
验收：**非空率从 0% → ≥80%**；且 `unclassified` 比例要在页面上如实标出（`build.py` 已经有这个字段，沉淀侧没有）。

**(c) 报错信号换成 `is_error`。**
实测最近 300 个会话文件：**78% 含 `"is_error":true`，平均每场 6.9 次**；而现在报的是「用户打了几次 error 这个词」（AgentDatabase 每场 0.4 次），**差约 17 倍**，且两者度量的根本不是同一件事。
验收：新旧两套「痛点项目排序」都算出来，人工对 12 个项目排一次真实痛感序，报**两套各自与人工序的 Spearman 相关系数**；新口径必须更高才算改对。**光换字段不报相关性 = 没验收。**

**为什么不需要模型**：三条全是计数和字段读取。

---

### 改进 4：常驻预算改造 —— 契约瘦身 + 索引常驻 + 正文按需

**怎么做**
- 常驻只留：**唯一地址 + 三条硬规矩 + 一行「命中会自动注入，无需手动取」** ≤ **25 行**（现在 116 行）。
- 其余搬到两处：
  - `.claude/rules/*.md` 带 `paths:` frontmatter —— **glob 确定性触发**，只在动到相关目录时才进上下文；
  - skill —— 收尾流程这种「有时才用」的多步流程，官方明确建议放 skill 而不是 CLAUDE.md。
- 给人看的维护说明放 `<!-- -->` 块级注释：**注入前被剥除，零 token**（官方明文）。
- `~/.dsh/AGENTS.md`（332 行）同步压到 200 行以内。

**为什么不需要模型**：纯文件重排。

**怎么验证有效（量化）**
| 指标 | 基线（已实测） | 目标 |
|---|---|---|
| 契约占常驻文件比例 | kimi **97%** / claude **76%** / workspace **92%** | **≤20%** |
| 每个常驻文件行数 | dsh **332 行** | **全部 ≤200 行**（官方口径） |
| 实际加载情况 | 现在无观测 | 挂 **`InstructionsLoaded` 钩子**（官方提供，matcher 为加载原因：`session_start`/`nested_traversal`/`path_glob_match`/`include`/`compact`）记录**哪些文件在什么原因下被加载**，形成可核账 |
| 行为不退化 | — | 瘦身前后各观测 20 场，契约要求的收尾动作执行率**不下降**（这是必须报的反指标 —— 只报「变短了」是半个验收） |

**负控**：删掉某条 `paths:` 规则该匹配的目录 → `InstructionsLoaded` 必须**不出现**该文件；动到该目录 → 必须出现。

---

### 改进 5：给结论加时间与失效，给链路加可见失败

**(a) 结论带时间与失效标记。**
每条沉淀结论带 `first_seen` / `last_seen` / `superseded_by`，**打标不删除** —— 与 Graphiti 的 `expired_at`、cognee 的 `superseded` 同构，也与 Claude Code auto memory 给记忆文件写 `modified` ISO 时间戳一致。失效判定用确定性规则（同一 `AGENTS.md` 条目被编辑 → 旧版标 superseded），**不做语义矛盾检测**（那是 Graphiti 唯一必须调 LLM 的地方，本项目不做）。
验收：**任意一条注入内容都能回答「这是什么时候的结论」**；抽 20 条人工判「是否已过时」，标 superseded 的准确率 ≥90%，且**漏标率**单独报（只报准确率是半个验收）。

**(b) 静默失败变可见失败。**
实测 **2026-08-20T09:52:57Z** 的归档刷新因为「已安装副本比调用方旧」（`--web` 参数不认）+ `push_brief.sh` 缺失而整轮失败，**只在日志里留了一行**。加两个纯脚本守卫：
- `~/.memory-atlas/src/atlas/VERSION` 与仓里的 `atlas/VERSION` 不一致 → SessionStart 注入一行告警；
- `on-archive.log` 里最近一次是失败 → 同样注入一行。

验收：
| 指标 | 基线 | 目标 |
|---|---|---|
| 静默失败次数 | **已发生 1 次且无人知道** | **0** —— 每一次失败都必须有对应的可见告警 |
| 告警假阳性 | — | 连续 7 天 0 次误报（否则会被当噪音忽略，等于没做） |

**负控（必须实跑，不许推理）**：
1. 故意把 `~/.memory-atlas/src/atlas/VERSION` 改旧 → SessionStart **必须**出现告警；改回去 → **必须**消失。
2. 故意删掉 `push_brief.sh` 跑一次归档 → 必须出现告警，且**不能阻断会话**。

---

### 明确不建议做的三件事

1. **不要引入 mem0 / Letta / Graphiti / cognee / LangMem / MemOS 中的任何一个。** 六个项目**写入端全部强依赖 LLM**，直接违反红线；Graphiti 连手工插三元组都要过一遍 LLM。它们值得借鉴的是**语义**（打标不删除、双时间轴、索引+按需），不是代码。
2. **不要建 embedding / 向量库。** 本项目语料远小于 200k token（Anthropic 给的「小于这个就直接全塞」阈值）；内容以精确标识符为主，**BM25 在这类查询上本来就更准**；引入 embedding 会同时破坏「零模型」与「零外部 DB」。
3. **不要用 LoCoMo / LongMemEval 之类的公开 benchmark 来证明本方案有效。** LoCoMo 全塞 26k token 就 72.9 分、6.4% 标准答案是错的、judge 会放行 62.81% 的错答案；LongMemEval-S 也已接近饱和。**唯一有说服力的验收是上面那些本机可复现的数字**（命中率、跨天重复组增量、指针可核率、Spearman 相关、静默失败数）。

---

## 七、中文社区实践

### 7.0 先说工具覆盖的边界（决定下面哪些能信）

**可读并已验证正文**：V2EX（含 sov2ex 全文搜索）、掘金（搜索 API + 正文）。
**读不到，仅索引可见或完全不可验证**：知乎（`zhuanlan.zhihu.com` 403 / `www.zhihu.com/p/*` 404）、CSDN（521，Cloudflare）、微信公众号（搜狗索引能看到标题+账号，但 `/link?url=` 一律 302 到 antispider，**拿不到永久链接与日期**）、微博（登录墙）、小红书（SPA 壳）、B 站（只有标题/UP主/日期）。InfoQ 中文站无可用 GET 搜索接口，**QCon/ArchSummit 演讲稿这条线没打通**。
另：本轮 WebSearch 配额已耗尽，Bing 的 `site:` 过滤器被忽略。**所以「没找到」在很多平台上等价于「没能验证」，不等于「不存在」。**

### 7.1 有一手数据、我逐字读过正文的（全网只捞到不到十条）

| 内容 | 出处 | 日期 | 性质 |
|---|---|---|---|
| **mem0 规模化后召回塌方** —— 自建 mem0 + 腾讯 TencentDB-Agent-Memory 双写，qwen3.7-plus 摘要 + bge-m3 embedding，**存到 10,932 条时召回开始出错**（原话「越来越像老年痴呆了」）；回帖 `willie1991` 报 12,000 条同样退化 | V2EX #1235793，`lynn1su` <https://www.v2ex.com/t/1235793> | 2026-08-20 | 真实一手，**样本=个人使用，无对照组** |
| 同一作者更早的：「Mem0 好野鸡啊，代码拉下来，我和 chatgpt 一起修复了 13 个 bug，才能正常用」 | V2EX #1210610 <https://www.v2ex.com/t/1210610> | 2026-05-06 | 真实一手 |
| **mem0 的 Java 接入评估报告** —— 自建成本模型（10K DAU ≈ $271/月，100K ≈ $1,560/月）、集成工时（2 周 PoC + 6 周加固）、四类生产事故（PostHog 遥测 800+ 空闲线程 ×10MB → OOM-kill；ADD-only 导致矛盾事实共存；embedding 失败静默丢记忆；LLM 超时挂 10 分钟）；点名 Issue #4875（CVSS 8.1 注入，未修）。**结论是「特定场景引入」，不是放弃** | 掘金，`朕瞧着你甚好` <https://juejin.cn/post/7654049463790518326> | 2026-06-22 | 真实评估报告（其中 92.5% 等分数是**引用 mem0 官方数字**，非自测） |
| **自建「日志→离线蒸馏→规则文件」** —— PreToolUse/PostToolUse Hook 落 `observations.jsonl` → Stop Hook 触发脚本（统计模式检测 + LLM 语义分析双路）产出原子化 Instinct markdown → SessionStart Hook 用本地 nomic-embed-text + qdrant 召回 Top-5 注入。防膨胀：观测超 5MB/8000 行按月归档、置信度 <0.55 标 deprecated、Memory 文件超 160 行按优先级裁剪 | 掘金，**得物技术**（官方号） <https://juejin.cn/post/7649571695950856234> | 2026-06-11 | **形态与本项目最接近**。声称冷启动 10 分钟→30 秒、Token 降 78%、错误重复率降 80% —— **四个数字都没给工作负载、样本量、对照组，属厂商博客级自报，不可当实测引用** |
| 更轻的同类：一个 skill + **append-only JSONL 单文件**做记忆，bash 读写、无依赖、可 git 同步、多工具共享 | V2EX #1180736，`shadeofgod` <https://www.v2ex.com/t/1180736> | 2025-12-23 | 真实一手。回帖一句值得记：「**如果长时间充斥着的是垃圾记忆，还不如没有这段记忆**」 |
| **生产级记忆分层的取舍** —— 四层（实时表／小模型会话摘要／核心身份卡／向量事实库），作者说核心身份卡那层「摔得最狠」；要点是写入去重、后台周期合并与升降级、用户手动加的永久免删、三道容量天花板。标题即结论：「最难的一课居然是『学会忘』」 | V2EX #1218210，`woodchen` <https://www.v2ex.com/t/1218210> | 2026-06-05 | 真实一手，**无成本/延迟数字** |
| **多工具「记忆割裂」痛点清单** —— worktree 换分支上下文清零、部署配置反复重讲、多 CLI 各问一遍技术偏好、一个月后 `epic-payment.md / -v2 / -draft` 分不清哪个是现状 | V2EX #1190513，`alenryuichi` <https://www.v2ex.com/t/1190513> | 2026-02-03 | 前半段痛点真实（**与本项目 5 个 agent 入口的处境同构**）；后半段自推自家开源项目，按软文折价 |

### 7.2 成本实测：中文社区最严谨的一份，且结论与直觉相反

**V2EX #1228396「为什么『节省 90% Token』不等于 Coding Agent 总成本降低 90%」**，`yohjisakamoto`，**2026-07-19** <https://www.v2ex.com/t/1228396>

配对实验（把 Rust 的 eza 重写成 Python，过 52 项 harness 检查）：

| 配置 | 通过率 | 平均 token | 成本 | 轮数 |
|---|---:|---:|---:|---:|
| 无插件 | 78.85% | 6.66M | ~$5.28 | 62.5 |
| Ponytail | 80.77% | −7.56% | −8.87% | 耗时 +13.51% |
| RTK | 76.92% | **+13.20%** | **+7.18%** | +44% |

**最有价值的一条测量**：140 次 Codex run 里，**cached input 占总 token 的 96.46%、占成本的 63.91%；模型输出只占 token 的 0.38%**。所以「把输出压缩 90%」映射到总成本上不足 1%。RTK 能识别的 shell 内容只占总 token 的 **0.1618%**。

作者提出的指标是 **「每个成功完成任务的总成本」**（附方差、轮数、时长、验证结果）。回帖一句：「**少走一次弯路就能省下 1× 的 token**」——成功率比压缩率重要。

**这条直接影响本项目改进 1 的验收口径**：不要用「注入省了多少 token」当指标，要用「每个成功完成任务的总成本」。注入本身很便宜（几百 token），真正的收益来自**少返工一次**。

相关但要打折：
- 掘金「曾经狂推的 Superpowers，今天我终于把它卸载了！臃肿，Token 吞金兽！」`卡卡罗特AI`，2026-07-16 <https://juejin.cn/post/7662933531113324586> —— 论点对（超长 skill 说明书每轮重载、上下文污染），**全文无任何量化数字**，定性吐槽。
- V2EX #1202137，`tw93`，2026-03-30 <https://www.v2ex.com/t/1202137> —— 提出「稳定的大系统提示比频繁变动的小提示实际成本更低」（prompt caching 的逻辑），以及 skill 描述写「**何时该用我**」而非「我能做什么」可把路由准确率从 **53% 提到 85%**。**该数字是他的说法，帖内未给实验细节。**

### 7.3 中文的 LoCoMo 复现

**唯一一份跑了全量并公开分数演进曲线的**：掘金「NylonME-05：从 47 分到 84 分 - LoCoMo 实测全记录」，`用户25865805286`，**2026-08-12** <https://juejin.cn/post/7672956220740272154>

全量 10 sessions / 1,536 题，一轮约 1 小时。演进：纯关键词 **47.1%** → 加 embedding **70.6%** → 双层写入 79.2% → 查询类型路由 80.1% → 84.2% → 加向量重排 **84.6%**。分类：单跳 88.0%、时序 86.6%、多跳 80.5%、**常识 53.3%（明显短板）**。
**性质：数字详细、过程可复现，但作者在推自己的开源项目 NylonME —— 属「自测有数据的自推」，不是中立复现。**

**注意这条对本项目的含义**：纯关键词 47.1% → 加 embedding 70.6%，看起来 embedding 很关键。但这是在 **LoCoMo 那种「合成对话里找语义相近的事实」** 任务上；本项目的查询是路径、命令、错误码这类精确标识符，**与 LoCoMo 的任务形态不同**，不能把这 23 个点直接搬过来当「必须上 embedding」的证据。

**LongMemEval 的中文复现或质疑：没找到可信的。** 掘金搜只有一条 2025-04 的论文摘要搬运和若干厂商稿引用官方分数。
**对 LoCoMo 的中文质疑：只有一条线索且无法验证** —— 知乎「Agent 记忆赛道大洗牌！LoCoMo-Refined 重磅发布」（Bing 索引显示 2026-04-15），**知乎 403/404 打不开正文，作者与具体批评均无法核实，不做陈述。**

### 7.4 大厂公开实践（全部为厂商自评，无第三方复现）

| 主体 | 数字 | 出处 / 日期 | 性质 |
|---|---|---|---|
| **腾讯云** `TencentDB-Agent-Memory`（TS/MIT，13,404 stars） | WideSearch 成功率 33%→50%、token −61.38%；SWE-bench 58.4%→64.2%、token −33.09%；PersonaMem 48%→76% | 拆解文：掘金 `苏灿烤鱼`，2026-08-05 <https://juejin.cn/post/7670369216241074202> | **拆解者本人写明「基准全部是官方自测，且都在 OpenClaw 这一个宿主上测得，目前没有第三方复现」** |
| **字节跳动** OpenViking（Agent 上下文数据库，**「虚拟文件系统」范式**） | LoCoMo10/1540 用例：原生 memory-core 完成率 35.65% / 24.6M input token；+OpenViking 52.08% / 4.26M；+两者 51.23% / **2.10M**。宣称完成率 +43%、input token **−91%** | 掘金，**字节跳动开源**（官方号），2026-03-18 <https://juejin.cn/post/7618167499356766235> | 厂商自测。**「虚拟文件系统」这条与 Letta「filesystem + grep 就够了」的结论方向一致，值得注意** |
| **阿里云** Hologres 长记忆服务 | LoCoMo 总分 **95.23%**（多跳 96.74 / 时序 97.45 / 单跳 95.46 / 开放域 81.46），称超原生 Mem0 2.73%；token 节省 78.7%~98.7% | 掘金，**阿里云大数据AI技术**（官方号），2026-08-06 <https://juejin.cn/post/7670746416008495146> | **厂商自评，标题「登顶世界第一」，按营销稿处理**（且 95.23% 已超过 LoCoMo 的诚实上限 ~93.6%，见 2.1） |
| **OPPO**「面向手机 Agent 的记忆系统工程：Agentic-RAG 实战与演进」 | — | 公众号 DataFunSummit | **仅索引可见，永久链接与日期取不到，正文未读** |
| **MemOS/MemTensor**「MemOS 2.0 StarDust 技术演进｜QCon 北京」 | — | InfoQ 公众号 | **仅索引可见，未验证** |

**通义 / 豆包 / Trae / CodeBuddy 的 memory 设计：没找到可信的官方工程文章。** 掘金前 20 条全是 AI-IDE 横评和使用教程；搜狗微信索引里只有第三方评论文，非官方技术披露且正文未验证。

### 7.5 明确标记为营销软文 / 内容农场（不要引用其数字）

- **掘金 `jessai2099`**：「AI Agent 记忆方案实测：TiMEM、Mem0、MemOS 三种架构到底怎么选」**同一篇发了两次**（article id 7613950767188361267 与 …328499，时间戳相隔 6 分钟）；同作者另有两篇横评，**每篇结论都指向 TiMEM**。判定：TiMEM 的铺量稿。
- **MemOS 官方掘金号**：「Tokens 消耗降低 72%+」「Memory 系统全面横评：谁让 Agent 具备更强长期智能？」—— 自家产品自评第一。
- **掘金 `joe45`「10人团队AI协作30天完整复盘」**（2026-06-10）：冲突次数 8-12→0-1、PR 合入 4 小时→20 分钟、AI 采纳率 20%→80%，**全是 90%+ 的整齐提升且不归因，正文是可复制粘贴的 YAML 样板，没有任何失败/回滚叙事** —— 模板化内容农场。
- V2EX 上一批以「分享/开源」为名的记忆产品贴实为自推（Hermes Memory Sidecar #1208596/#1216371/#1217342、memU #1231096、TiMem #1194237、MIP #1197152、LycheeMem #1204136 声称 token −71% 自测）。**可当「赛道有多拥挤」的证据，不能当复盘证据。**

### 7.6 水文比例：如实说

- 掘金搜 `CLAUDE.md` 前 20 条：**18 条是「完全指南／速通／8 个技巧／保姆级」类教程**，只有 2 条选题像原创工程内容（`洛卡卡了`「Claude Code Hook，当 CLAUDE.md 规则不生效时，我们还需要强制拦截机制」2026-07-02；`donecoding`「别再被 .cursorrules 绑架了：AGENTS.md + .spec/」2026-04-16）—— **这两篇正文未读，只能说选题不是水文，质量未验证**。
- 掘金搜 `智能体 记忆 实践` 前 20 条：几乎全是 LangChain/LangGraph 教程连载与综述，**0 条真实复盘**。
- B 站搜 `agent 长期记忆 mem0` 前 10 个视频：清一色「架构解析／完整拆解／一口气搞懂」，**没有一个标题指向踩坑或成本复盘**（仅凭标题判断）。

**粗估：中文社区这个主题 80%~90% 是复述官方文档、翻译或厂商稿。** 真有一手数据的，本轮全网只捞到 7.1、7.2 那不到十条，且一半集中在 V2EX。

### 7.7 明确没找到的

1. **「用了 mem0/Letta/Zep/cognee/LangMem 之后最终放弃」的完整中文复盘 —— 没找到可信的。** 最接近的两条（V2EX #1210610 骂 mem0 要修 13 个 bug、7.1 那份 Java 评估）结论都是「有条件引入」而非放弃。**Letta / cognee / LangMem 的中文一手实践，一条都没有** —— 中文社区提到 Letta/MemGPT 基本只出现在「竞品罗列」和一条招聘 JD 里（V2EX #1224418，2026-07-02，「Agent 记忆工程师」加分项列了 mem0/MemGPT/Zep/Letta）。
2. **LongMemEval 的中文复现或质疑 —— 没找到。**
3. **`CLAUDE.md` / `AGENTS.md` 长度的中文定量实测 —— 没找到。** 唯一沾边的数字（MEMORY.md「200 行 / 25KB」、压缩触发于 Token 使用率 ≥87%、Hermes MEMORY 限 2200 字符）来自掘金 `北辰alk`「AI Agent 记忆系统架构设计：OpenClaw、Claude Code、Hermes Agent 深度对比」（2026-05-28），**该文自己就是读文档写的，不是实测**。
4. **通义 / 豆包 / Trae / CodeBuddy 官方 memory 设计披露 —— 没找到。**
5. **知乎、CSDN、微信公众号、微博、小红书的正文，一条都没能验证。** 微信公众号那批标题选题正对（`架构和远方`「AI Agent 的长期记忆：我在工程落地里踩过的坑、做过的取舍」、`Xd聊架构`「多 Agent 之间怎么实现共享记忆」、`阿里开发者`「AI Agent 记忆系统：从短期到长期的技术架构与实践」、DataFunSummit 的 OPPO 那篇），但搜狗跳 antispider，**拿不到永久链接、日期和正文，因此只算线索，需要在微信里自己搜标题打开**。

---

## 附录：本机实测数据一览（全部可复现）

数据源：`~/.memory-atlas/out/*.sessions.jsonl`（4,814 场，覆盖 2025-11-24 → 2026-08-20，124 天）、`~/.claude/projects/**/*.jsonl`、各仓 `AGENTS.md`、`~/.memory-atlas/*.log`。测量时间 2026-08-20。

| 测的什么 | 数字 | 用在哪 |
|---|---|---|
| 会话总数 / 带提示词的 | 4,814 / 4,711 | — |
| **带非空 `topics` 的会话** | **0（0.0%）** | 差距 5.2-4 |
| 捕获的提示词总条数 / 参与判重的 | 8,071 / 4,711（**41.6% 被忽略**） | 差距 5.2-6 |
| 重复组（≥3 次）总数 | 182 | — |
| **其中只跨 1 天的** | **161（88%）** | 差距 5.2-7 |
| 头部 15 行中只跨 1 天的 | **11 / 15** | 差距 5.2-7 |
| 真正跨 ≥2 天的重复组 | **21** 组，首末间隔中位 **4 天**、最大 **154 天** | 改进 1 的主指标基线 |
| prefix-26 对近重复复现的召回 | **91.7%**（跨天 85.1%），漏 8.3% | 过时 5.3-2（说明**不该**往语义检索投入） |
| 近重复聚类会合并的组数 | 58 组（最极端：43 个 prefix key → 1 个 67 场的簇） | 过时 5.3-2 |
| 「本可命中」上限（全语料） | 3,031 / 4,731 = **64.1%** | — |
| **「本可命中」上限（剔除批处理扇出后）** | **对阈值极敏感**：T=5 → 4.6%（1,524 场）；**T=10 → 14.0%（1,862 场里 261 场）**；T=20 → 21.3%；T=50 → 33.2% | **改进 1 的验收基线 —— 必须先锁定 T 再报数** |
| 跨天「真·下次又问」 | **727 场（15.4%）** | 改进 1 |
| 最近 300 个 Claude Code 会话文件含 `is_error:true` | **78%**，平均每场 **6.9 次** | 改进 3(c) |
| 现有口径「每场平均提到报错」（AgentDatabase） | 0.4 次 | 改进 3(c)，约差 17 倍 |
| 契约块行数 | **116 行** | 差距 5.2-12 |
| 契约占比：`~/.kimi-code/AGENTS.md` | **116 / 119 = 97%** | 改进 4 |
| 契约占比：`~/.claude/CLAUDE.md` | 116 / 153 = 76% | 改进 4 |
| 契约占比：`GithubProject/AGENTS.md` | 116 / 126 = 92% | 改进 4 |
| `~/.dsh/AGENTS.md` 行数 | **332 行**（超官方 200 行建议 66%） | 改进 4 |
| `AGENT_BRIEF.md` 体量 | 190 行 / 11,620 字节 | 过时 5.3-5 |
| 7 个仓 `AGENTS.md` 里「结论/为什么/代价」三段式条目 | **0 条** | 差距 5.2-8（⚠️ 契约今天才上线） |
| 收到的 compounding event | **1 个**（`claude-code-20260820-001.json`） | — |
| 归档链路静默失败 | **1 次**（2026-08-20T09:52:57Z，版本偏斜 + 缺文件） | 改进 5(b) |
| 本机 auto memory 规模 | `MEMORY.md` 28 行索引 + **27 个主题文件**，每次会话自动加载 | 差距 5.2-11 |
| 本会话「指针注入 → 实际取用」转化率 | **0**（注入了地址，全程没执行那条 `gh api`） | 差距 5.2-3 |

