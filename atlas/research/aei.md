# AEI 对标调研：完整版本演进、指标定义、现有实现差距、单人数据的诚实替代

调研日期：2026-08-20
调研范围：Anthropic Economic Index 全部 6 个已发布版本 + 同类经济度量工作 + 单人/单时间线数据的统计效力
产出约束：每条结论带 URL + 发布时间；「原文这么说」与「我的推断」分开标注；查不到就写「查不到」

---

## TL;DR —— 如果只读十二行

1. **任务给的 `atlas/build/aei.py` 在本机不存在。** 真正的 AEI 对标件是 `memory_atlas_private/analytics.py` + `normalization.py`（实现 A）和 `build_memory_atlas_economic_proxy.py`（实现 B）。
2. **实现 A 的 automation/augmentation 是对整段 JSON 做关键词子串匹配**（含 "automation"/"自动化"/"scheduled" 就判自动化）。AEI 分的是**交互形态**，这里分的是**文本里出现了哪个词** —— 不是精度问题，是测了另一个东西。
3. **91.22% 的事件是 `mixed_or_unknown`**，却和另外两类并列成三个百分比。「没测出来」被当成了「第三类」。
4. **分析单位是文件行不是会话**（320,539 events vs ~4,685 会话），一个 6 万行日志压过 100 场真实对话。
5. **数据本身三分之二是机器**：实测 2,826 场里只有 952 场是人在对话，1,485 场是 agent 扇出、389 场是批处理。不拆开，所有 share 都是人机混算。
6. **两个「经济」面板显示的是结构性零**：`verified_outcome_rate = 0.0 但标 MEASURED`（验证管道从没接上）、`failure_compound` 全部指标为 0（引擎实现了但没喂过数据）。
7. **实现 B 的 `opportunity_score_proxy = 86` 是一个常数** —— 12 个机会的分数全是 100、证据数全是 10，代入公式恒等于 86，数学上无法变化。
8. **AEI 自己在 16 个月里把结论翻了两次**：automation/augmentation 从 57/43 → 49/47（automation 反超）→ 45/52（又翻回来）；并把自己的生产率估计从 1.8pp 砍到 1.0–1.2pp；还明确推翻了「越资深越倾向自动化」。
9. **文献里最接近本场景的那条证据是负的**：METR 实测资深开发者在自己熟悉的成熟仓上用 AI **慢了 19%**，而当事人自评是**快了 20%** —— 差 39 个百分点。本项目测的恰好就是这个最真实的一端。
10. **单人数据上有四类指标是伪科学，不是精度不够**：职业任务覆盖率、工资分布/task value、Hulten 生产率增长 pp、AUI/Gini —— 它们的分母在单人数据上不存在（§5.1）。
11. **SPACE 原文其实允许你测自己**（"Individual-level productivity analysis, however, may be insightful for developers"），它禁止的是组织拿个人数据做评价。**但按 SPACE 自己的四条规则，现在这版不合格**：只有一个维度有数据、零个感知类指标、而那唯一的维度（Activity）正是原文点名「绝不能单独使用」的（§4.4）。
12. **有一条实证给了这个项目意外的支撑**：微软 81 人研究实测，纯遥测只能解释自评生产力方差的 **7–9%**，加上「这个人是谁」的个人截距才跳到 **34%**。**跨人比较活动量几乎没有立足点，而个人纵向基线是必要条件** —— 所以正确的叙事是「我和我的过去比」，不是「我和世界比」（§4.4）。

---

## 0. 先说三件必须先纠正的事实（否则后面所有对照都是错的）

### 0.1 任务里给的代码路径不存在

任务说实现在 `~/Documents/Codex/GithubProject/AgentDatabase/atlas/build/aei.py`（约 550 行）。

**实测结论：这个文件在本机不存在。** 验证方式：

- `find / -maxdepth 12 -path "*/atlas/build/aei.py"` → 无结果
- 全 `GithubProject/` 下 `find -iname 'aei*'` → 无结果
- 全仓 grep `economic_index|economicindex|anthropic economic index` → 只命中下面两处真实实现

所以我改为审计**真实存在的两处 AEI 对标实现**（下面 §3 逐条对照）：

| 编号 | 文件（绝对路径） | 行数 | 它是什么 |
|---|---|---|---|
| **实现 A** | `~/Documents/Codex/GithubProject/AgentDatabase/OpenAIDatabase/scripts/memory_atlas_private/analytics.py` + `normalization.py` | 202 + 184 | **真正的 AEI 对标件**。产出 `memory_atlas.behavior_economics.v1`，含 `augmentation_distribution`（automation / augmentation / mixed_or_unknown）、`activity_distribution`、`verified_outcome_rate`。前端在 `MemoryAtlas/src/features/v31/BehaviorEconomyView.tsx` 以「行为经济」页展示。 |
| **实现 B** | `~/Documents/Codex/GithubProject/AgentDatabase/OpenAIDatabase/scripts/build_memory_atlas_economic_proxy.py` | 449 | 「个人经济代理指数」（S07 P1）。产出 `personal_ai_economic_index_score` 与 `automation_ratio` / `enhancement_ratio`。公式配置在 `OpenAIDatabase/机器治理/参数与公式/personal_economic_proxy.v1_2_s07_p1.json`。 |

线上产出样本：`~/Documents/Codex/GithubProject/_scratch/private-database-devnotes/Private-AgentDatabase/memory-atlas/analytics/latest.json`（生成于 2026-08-20T08:33:53Z）。

**这个页面确实是上线的**：`MemoryAtlas/src/app/routeRegistry.tsx:130` 注册了 `behaviorEconomy` 路由，且 `MemoryAtlas/dist/assets/index-DiOwXC3R.js` 里能搜到「行为经济」字样 —— 说明它已经进了构建产物，不是死代码。

> **推断（我的）**：任务描述里的 `atlas/build/aei.py` 可能是给 PRD 起的目标路径，而不是已有文件。如果 owner 说「还是不够」，很可能他看到的就是实现 A 那三个数字（automation 4.25% / augmentation 4.53% / mixed_or_unknown 91.22%），而 91% 的未分类正是「不够」的直接来源。

### 0.2 这份数据不是「一个人的时间线」，三分之二是机器

本机已有实测记录（`~/.claude/projects/.../memory/agent-session-data-is-mostly-machine.md`，2026-08-20）：

- 7 个来源共 **2,826 场会话，只有 952 场是 Owner 真的在对话**
- **1,485 场是 agent 密集扇出**（判定：同一 source 同一小时内启动 ≥15 场），单次最大 518 场
- **389 场是批处理**（判定：无用户发言／单轮机器指令／同一段提示词前 80 字重复 ≥5 次），最大一组 340 场

而 `dev-notes/agent_brief.json`（2026-08-20T09:59:43Z）里 `sessions_analysed = 4685`，`sessions_scope = "含 agent 扇出与批处理"`。

**这条事实决定了整份 PRD 的地基**：AEI 的分析单位是「一个人类用户的一次对话」，而这里的分析单位一大半是「一个 agent 被 fan-out 出来的一次调用」。**在不拆分这两个总体之前，任何 AEI 式的 share/百分比都是把人和机器混在一个分母里算出来的，不成立。**（详见 §5.1）

### 0.3 目前的分析单位是「文件/JSONL 行」，不是「会话」

实现 A 的 `event_count = 320,539`，而会话数是 4,685 量级。原因见 `normalization.py:134-183`：一个 `.jsonl` 文件的**每一行**产出一个 event，一个 `.json` 数组的**每个元素**产出一个 event。

**后果**：一个 6 万行的日志文件会以 6 万票的权重压过 100 场真实会话。`latest.json` 里 `projects` 排第一的是 `public_raw`（61,463 events），第二是 `wd_linzezhang_a539f10d744d`（47,560）——这两个都是目录名，不是项目。260 个「项目」里大量是 `2026`、`desktop`、`marketplaces` 这类路径片段。

---

## 1. AEI 版本演进表

数据集官方 release 列表来源：https://huggingface.co/datasets/Anthropic/EconomicIndex/raw/main/README.md（读取于 2026-08-20，License: 数据 CC-BY / 代码 MIT）

| # | 发布日 | 报告名 | 新增维度 | 方法变化 | 被修正/推翻的结论 |
|---|---|---|---|---|---|
| **v1** | **2025-02-10** | *Which Economic Tasks are Performed with AI?* / "Anthropic Economic Index" 首发 | O*NET 任务映射；automation vs augmentation 五种协作模式；职业任务覆盖率 | Clio 隐私保护聚类；层级树自顶向下匹配到 O*NET 任务。⚠️ **样本量在两处口径不一致**：论文摘要逐字 "over **four million** Claude.ai conversations"，而官方公告页写的是 Clio 分析了「approximately **1 million** conversations」。两者的关系（总量 vs 实际映射子集）**原文未说明，查不到** | — （基线） |
| **v2** | **2025-03-27** | *Insights from Claude 3.7 Sonnet* | 630 个自底向上（bottom-up）细粒度使用簇；extended thinking 使用率 | ① 不再按「职业相关性」预筛，改为只做安全分类器过滤，以保留更多数据供自底向上分类法；② 分类模型从 Claude 3.5 Sonnet 换成 3.7 Sonnet | 修正了「automation 会在某些职业里占主导」的预期：**没有任何职业类别里 automation 占主导**，最高约 50%（生产类、计算机与数学类） |
| **v3** | **2025-09-15** | *Uneven geographic and enterprise AI adoption*（arXiv:2511.15080，2025-11-19 提交） | 地理维度（150+ 国家 / 美国各州）；一方 API（1P API）企业维度；**Anthropic AI Usage Index (AUI)** | 100 万 Claude.ai 对话 + 100 万 1P API transcript（2025-08，从占 1P API 用量约一半的客户池随机抽样）；分类模型 Sonnet 4 | **推翻 v1 的「augmentation 占多数」**：directive 自动化从 27% 升到 39%（八个月），Claude.ai 侧 automation 49.1% vs augmentation 47%——**automation 首次反超** |
| **v4** | **2026-01-15** | *Economic primitives / New building blocks* | **五个经济原语**：Task Complexity、Human and AI Skills、Use Case、AI Autonomy（1–5 分）、Task Success | 100 万 Claude.ai + 100 万 1P API（2025-11 样本，2025-11-13~11-20）；模型 Sonnet 4.5；测量维度从 2 个扩到 7 个 | ① **augmentation 回升**至 52%（+5pp），automation 落到 45%（−4pp）——即 v3 的反超**未持续**；② **把自己 1.8pp 的生产率估计砍半到 1.0–1.2pp**（见下） |
| **v5** | **2026-03-24** | *Learning curves* | 用户 tenure（注册满 6 个月）；模型选择行为；task value（美元时薪当量） | 样本 2026-02-05~02-12；模型 Opus 4.5/4.6；**O*NET-SOC 编码从 2010 版换到 2019 版**；新增控制回归以剥离 tenure 与任务选择 | **明确推翻自己 2025 年的假设**：原文「This pushes back against a hypothesis we made last year that automated use may be more typical of more experienced, sophisticated users」——高 tenure 用户反而更协作、更迭代。另：美国州级人均用量收敛时间从「2–5 年」改为「**5–9 年**」 |
| **v6** | **2026-06-26** | *Cadences* | **输出物分类器**（30+ 类 artifact）；小时级节律；chat/Cowork 与 1P API 分开 | ① 采样率提高到可看小时级（此前是 7 天窗口快照）；② 新增 output classifier 标注「这次对话产出了什么」；③ 1P API 改为月度聚合 | 查不到明确的「推翻」表述。新增事实：**93% 的对话能识别出 artifact**；Claude Code 的平均 autonomy 比 chat/Cowork 高 0.37 分 |
| （配套） | **2025-12-04** | *Introducing Anthropic Interviewer* | 定性访谈 | 1,250 名专业人士（1,000 通用劳动力 + 125 创意 + 125 科学家），Claude 主持 10–15 分钟自适应访谈 | 86% 通用劳动力报告省时；但 69% 提到使用 AI 有社会污名 |
| （配套） | **2026-04-22** | *Announcing the Anthropic Economic Index Survey* | 月度问卷 + 用量数据链接 | 从注册满两周的个人账号中每月随机抽样 | Anthropic 自陈：用量指标「track what has already happened, often with meaningful delay」，且**都不能捕捉人们如何体验这些变化** |

**来源**
- v1 公告：https://www.anthropic.com/news/the-anthropic-economic-index （2025-02-10）
- v1 论文：https://arxiv.org/abs/2503.04761 v1，提交 2025-02-11（Handa, Tamkin, McCain, Huang, Durmus, Heck, Mueller, Hong, Ritchie, Belonax, Troy, Amodei, Kaplan, Clark, Ganguli）
- v2：https://www.anthropic.com/news/anthropic-economic-index-insights-from-claude-sonnet-3-7 （2025-03-27）
- v3：https://www.anthropic.com/research/economic-index-geography （2025-09-15）；论文 https://arxiv.org/abs/2511.15080 v1，2025-11-19（Appel, McCrory, Tamkin, McCain, Neylon, Stern）
- v4：https://www.anthropic.com/research/anthropic-economic-index-january-2026-report 与 https://www.anthropic.com/research/economic-index-primitives （2026-01-15）
- v5：https://www.anthropic.com/research/economic-index-march-2026-report （2026-03-24）
- v6：https://www.anthropic.com/research/economic-index-june-2026-report （2026-06-26）
- Interviewer：https://www.anthropic.com/research/anthropic-interviewer （2025-12-04）
- Survey：https://www.anthropic.com/research/economic-index-survey-announcement （2026-04-22）

### 1.1 三条最重要的「被推翻」的结论（PRD 里必须体现）

1. **automation/augmentation 的比值不稳定，会来回翻。** 57/43（2025-02）→ 57/43 不变（2025-03）→ **49.1/47 automation 反超**（2025-09）→ 45/52 augmentation 再反超（2026-01）。**推断（我的）：一个会在 16 个月内翻两次方向的比值，做成「你的自动化率是 X%」这种单点展示是误导的；它只有在同口径时间序列里才有意义。**
2. **「越资深越倾向自动化」是错的。** v5 明确推翻（2026-03-24）。
3. **AEI 自己把生产率估计砍了一半。** v4（2026-01-15）：按 Hulten 定理做的任务级生产率冲击聚合，原为「未来十年年均 +1.8pp 劳动生产率」；把 **task success rate** 乘进去之后，Claude.ai 侧降到 **1.2pp**，1P API 侧降到 **1.0pp**。原文理由：如果工人必须验证 AI 输出，raw speedup 就高估了实际收益。

---

## 2. AEI 完整指标清单（指标名 / 精确定义 / 数据来源 / 单人数据可否复现）

「单人可否复现」一栏的判据：本机数据是 4,685 场会话（含 fan-out/批处理），有 day 级时间戳、工具调用计数、token、turn、error 计数、project 路径、harness、model；**没有** O*NET 映射、**没有** 多用户、**没有** 地理、**没有** 工资数据、**没有** 人类验证标注。

| # | 指标 | AEI 的精确定义（原文口径） | 数据来源 | 单人数据可否复现 |
|---|---|---|---|---|
| 1 | **O*NET 任务映射** | 对话经 Claude 自顶向下遍历三层树：12 个顶层 → 474 个中层 → **19,530 个 O*NET 底层任务**；「If multiple options apply, choose the single-most pertinent one」 | O*NET（美国劳工部），约 2 万条任务 | **需替代**。O*NET 是职业任务库，本机会话是「一个人在自己项目里的动作」。硬套会把 90% 归到 15-1252.00 Software Developers 一个坑里，无信息量。替代见 §5.2 |
| 2 | **职业任务覆盖率（task coverage）** | 「what fraction of each occupation's tasks appeared in our Clio run」。阈值结果：**~36% 的职业 ≥25% 的任务**、~11% ≥50%、**~4% ≥75%** | 同上 | **不可**。分母是「某职业的全部任务」，单人没有职业总体。**这是 §5.1 说的伪科学项之一** |
| 3 | **有效覆盖的隐私下限** | 「only examine tasks that have accumulated at least **15 separate conversations** spread across a minimum of **five different user accounts**」；低于此的任务被剔除 | Clio | **不可**（5 个账号这条对单人恒为 1）。**但这条是「有效覆盖率」概念在 AEI 里最接近的对应物**，见下方注 |
| 4 | **automation / augmentation 二分** | 五种协作模式二分：**automative** = Directive（"Complete task delegation with minimal interaction"）+ Feedback Loop（"Task completion guided by environmental feedback"）；**augmentative** = Task Iteration（"Collaborative refinement process"）+ Learning（"Knowledge acquisition and understanding"）+ Validation（"Work verification and improvement"）。v1 分布：Directive 27.8% / Feedback Loop 14.8% / Task Iteration 31.3% / Learning 23.3% / Validation 2.8% | Claude 对**整段对话的交互形态**做分类 | **可（需重做分类器）**。分类对象是「人和 AI 谁在做决定」，这在 agent 会话里同样可观察（谁发起、有没有人类中途干预、有没有人类验收）。但**绝不能用关键词匹配**——见 §3 |
| 5 | **分类器人工验证准确率** | 150 条对话人工核对：顶层 95.3% / 中层 91.3% / **底层（O*NET）86%**；automation/augmentation 标签「90.7% of conversations are assigned to their optimal label as assessed by human raters」 | 人工评分 | **可**（应该做）。这是 AEI 有而本机完全没有的一环 |
| 6 | **职业级用量 share** | 「aggregate the number of conversations associated with tasks for a given occupation. In the case that a single task maps to multiple occupations, each occupation's conversation count is incremented by the number of conversations assigned to that task divided by the number of occupations associated with that task」——**多职业任务按职业数均摊** | Clio + O*NET | **不可**（无职业维度）。**需替代**：换成「项目/仓 × 活动类型」的均摊份额 |
| 7 | **工资分布关系（inverted-U）** | 用量在**工资上四分位**达峰；极高薪（医生）与低薪（餐饮）都低 | O*NET-SOC × BLS 工资 | **不可**。单人只有一个工资点，画不出分布。**伪科学项** |
| 8 | **Task value（美元时薪当量）** | 「average hourly wages paid to US workers performing equivalent occupational tasks」，BLS 2024-05。v5 观察到从 $49.30 降到 $47.90 | BLS | **不可**（不诚实）。除非 owner 愿意给自己定一个显式时薪并声明它是假设值 |
| 9 | **Anthropic AI Usage Index (AUI)** | 「normalizing each country's share of Claude.ai use by its share of the world's working population」；>1 表示超预期采用 | 地理 + 人口 | **不可**（无地理、无人口分母）。**需替代**：见 §5.3「项目 AUI」 |
| 10 | **地理分布** | 150+ 国家 / 美国各州。**注意：AEI 报告页与 arXiv abs 页都没有公开说明国家/州具体怎么推断的（IP？账号元数据？）——查不到** | 未公开 | **不可** |
| 11 | **Gini 系数（用量不平等）** | v4 报美国州级 Gini 从 0.37 降到 0.32 | 地理用量 | **需替代**。Gini 本身对单人无意义（跨人不平等），但**跨项目/跨时间的注意力集中度**是同一个数学对象，可以诚实地重定义，见 §6 |
| 12 | **Top-N 任务集中度** | v4：top 10 任务占 24% 对话；v5 降到 19% | 任务分布 | **可**（换成 top-N 项目/主题占比） |
| 13 | **Task Complexity（原语 1）** | 三个量：无 AI 时的人类预估耗时、有 Claude 时的耗时、单次对话是否含多任务 | Claude 自评 | **需替代**。Claude 自评的「无 AI 时要多久」是**模型对反事实的猜测**，不是测量。单人可用真实的 wall-clock 会话时长 + 轮次替代，但**不能声称它等于 speedup**（见 §4 METR） |
| 14 | **Human and AI Skills（原语 2）** | 「whether users could have completed tasks without Claude, and the years of education needed to understand both user prompts and Claude's responses」。v4：人类 prompt 与 AI 回答的教育年限相关 r > 0.92 | Claude 自评 | **不可**（不诚实）。让模型猜「这个人没有我能不能做成」在 n=1 上无法证伪 |
| 15 | **Use Case（原语 3）** | work / coursework(educational) / personal 三分。v4：46% work、19% coursework、35% personal | Claude 分类 | **可**（本机可映射为 项目工作 / 学习 / 个人事务；但要先剔掉 fan-out） |
| 16 | **AI Autonomy（原语 4）** | 「degree to which users delegate decision-making to Claude」，**1–5 分**。注意 AEI 明确说它与 directive 不同：翻译任务虽是 directive 但 autonomy 低 | Claude 分类 | **可，而且这是最该做的一个**。agent 会话里「人类干预点」是硬可观察的：user turn 数、abort 数、人类是否在结束前发言 |
| 17 | **Task Success（原语 5）** | 「Claude's assessment of whether Claude completes tasks successfully」。v4：Claude.ai 67%，1P API 49% | Claude 自评 | **需替代**。**模型自评成功率在自己产生的会话里是系统性乐观的**（AEI 自己也承认它只是 Claude's assessment）。本机有更硬的替代：error_event_count、abort_count、后续是否有同题复问（agent_brief 的 repeats 已经在做） |
| 18 | **劳动生产率增长估计** | Hulten 定理 + 任务级时间节省对数差 × O*NET 任务时间权重 × 工资份额加权求和。1.8pp → 乘 success rate 后 1.0–1.2pp | O*NET + BLS + 自评耗时 | **不可**。**伪科学项**：单人无工资份额、无任务时间权重、无反事实耗时 |
| 19 | **Artifact 输出分类（v6）** | 30+ 类；93% 对话有可识别产出；explanations 17% / documents-reports 15% / guidance 11% | 新 output classifier | **可，而且本机比 AEI 更强**：AEI 只能猜产出，本机能直接看 Write/Edit 工具落到了哪些文件、有没有进 git |
| 20 | **时间节律（v6）** | 小时级。个人类 prompt 周末从 ~35% 升到近 50%；4-14 报税请求是 5 月均值 8 倍 | 高频采样 | **可**（本机有 day 级，需确认是否保留了 hour 级时间戳） |
| 21 | **模型选择行为（v5）** | 每多 $10 task value，Opus 使用率 Claude.ai +1.5pp、API +2.8pp | 模型字段 | **部分可**：本机有 model_provider / models 字段，但没有 task value 做自变量 |
| 22 | **tenure 效应（v5）** | 注册满 6 个月为 high-tenure；高 tenure 成功率高 10%、work 用途高 7pp | 账号注册日 | **需替代**：单人没有「跨用户 tenure」，但有**自己的学习曲线**——按月切片看同类任务的 error/重试变化。**注意这是时间序列，不是 tenure** |

> **关于「有效覆盖率」**：任务里问的「覆盖率 / 有效覆盖率」这两个词，**AEI 原文没有「effective coverage」这个术语——查不到**。AEI 里存在的是两个不同的东西：(a) 上表 #2 的 per-occupation task coverage；(b) 上表 #3 的隐私下限（≥15 对话 且 ≥5 账号），后者事实上起到了「有效样本门槛」的作用——低于门槛的任务直接不进分析，不是记成 0。
> **这一点对本机极其重要**：实现 A 现在的做法恰恰相反——把 91.22% 分不出来的事件记成一个叫 `mixed_or_unknown` 的**桶**，然后把它和 automation/augmentation 并列展示成三个百分比。这在数学上是把「没测出来」当成了「测出来是第三类」。正确做法是分母只取可判定集合，同时把「可判定率」作为一级指标单独露出来。

---

## 3. 现有实现的差距表（先真读代码，逐条对照）

以下每条都标了文件与行号。**实现 A** = `memory_atlas_private/{analytics,normalization}.py`；**实现 B** = `build_memory_atlas_economic_proxy.py`。

### 3.1 ✅ 已做对的

| # | 事项 | 证据 |
|---|---|---|
| A1 | **运行期零模型调用**，分类确定性可复现 | `analytics.py:79-82` — `"classification": "observed_usage_multi_label_deterministic", "model_calls": 0` |
| A2 | **拒绝自称成功**：任何 `*_verified` 状态必须绑定 evidence adapter 的验证信封（PASS/VERIFIED + verifier + oracle + subject_ref + 至少一条含合法 sha256 的 evidence_ref），否则降级成 `claimed_*` | `normalization.py:41-97`。这条设计是对的，且注释写得很清楚：「Raw text/JSON can claim success but cannot prove world state」 |
| A3 | **禁止无同口径总体时生成全球百分位**：口径不一致或基准样本 < 30 一律降级为 `DIRECTION_ONLY` | `analytics.py:109-158`，前端 `BehaviorEconomyView.tsx` 有「全球比较门」说明 |
| A4 | `unknowns_are_not_pass: true` —— 明确声明未知不算通过 | `analytics.py:82` |
| A5 | **实现 B 的边界声明是硬校验，不是注释**：不接外部经济数据库、不做精确收入预测、不做财务建议，任一为真直接抛错 | `build_memory_atlas_economic_proxy.py:92-96, 399-407` |
| A6 | 实现 B 的每张分卡强制带公式 id、中文解释、参数引用、证据引用，缺一即 fail | 同上 `:368-391` |

### 3.2 ❌ 做错的（口径根本不对，不是精度问题）

| # | 事项 | 证据 | 为什么是错的 |
|---|---|---|---|
| **B1** | **automation / augmentation 是对整段 JSON 文本做关键词子串匹配** | `normalization.py:100-106`：把整个 payload `json.dumps` 后小写，含 `automation`/`自动化`/`scheduled` → automation；含 `recommend`/`建议`/`analysis`/`分析` → augmentation；否则 `mixed_or_unknown` | AEI 分的是**交互形态**（谁在做决定），这里分的是**文本里出现了哪个词**。一份讲「如何禁用自动化」的文档会被判成 automation；一份 CI 日志里出现 `scheduled` 也会。**这不是 AEI 指标的低精度版本，它测的是另一个东西。** |
| **B2** | **activity 分类是有序 first-match-wins 的关键词规则，第一条就吃掉了大半** | `normalization.py:22-35`：`verification_repair` 的词表含 `test`、`error`、`bug`；它排在第一位 | 任何工具日志里几乎必然出现 `error` 或 `test`。实测 `verification_repair` 占 22.76%，且**同时含 `test` 与 `deploy` 的 payload 永远被判成 verification_repair**，规则顺序即结论 |
| **B3** | **分析单位是文件/JSONL 行，不是会话** | `normalization.py:155-181`，`analytics.py:45-64` | `event_count = 320,539` 对 ~4,685 场会话。一个 6 万行日志 = 6 万票。AEI 的单位是 conversation，两者的 share 不可比 |
| **B4** | **`project` 取相对路径第一段** | `normalization.py:17-19` | 产出 260 个「项目」，前几名是 `public_raw`、`2026`、`desktop`、`marketplaces`、`wd_linzezhang_a539f10d744d` —— 全是目录名 |
| **B5** | **`verified_outcome_rate` = 0.0 但 state 标成 `MEASURED`** | `analytics.py:93-100`；实测 `latest.json`：`{"value": 0.0, "numerator": 0.0, "denominator": 320539.0, "state": "MEASURED"}` | 真相是「验证管道从没接上」，展示出来是「已验证结果率 0.0%（已测量）」。这是把**未接线**呈现成**测量到零**——`unknowns_are_not_pass` 的精神在这里被自己违反了 |
| **B6** | **`effort_minutes` 恒为 None**，导致分母静默从 effort 掉回 event_count | `normalization.py:112-113` 只从 `payload["effort_minutes"]` 读，而没有任何来源写这个字段；实测 260 个项目的 `effort_minutes` 全部为 0.0 | 分母类型切换是静默的，UI 只显示「分母类型：事件计数」，不告诉用户 effort 口径从来没生效过 |

### 3.3 ⚠️ 做了但口径不对的

| # | 事项 | 证据 | 正确口径 |
|---|---|---|---|
| **C1** | **`mixed_or_unknown` 与 automation/augmentation 并列成三个百分比** | `analytics.py:88-91` 对所有出现过的 key 一视同仁地除以 `event_count`；实测 automation 4.25% / augmentation 4.53% / **mixed_or_unknown 91.22%** | 「未知」不是第三种协作模式。分母应只取可判定集合（automation + augmentation = 28,149），并把**可判定率 8.78%** 作为一级指标单独露出。现在这版让人误读成「我 4% 自动化」，真相是「91% 没测出来」 |
| **C2** | **`activity_distribution` 里 `unknown` 39.29%**，同样并列展示 | `analytics.py:84-87` + `latest.json` | 同 C1。AEI 的对应做法是设 ≥15 对话/≥5 账号的门槛把不足样本**剔除**，而不是记成一类 |
| **C3** | **实现 B 的 `automation_ratio` 分母漏掉了一个真实存在的类别** | `build_memory_atlas_economic_proxy.py:194-196`：分母写死为 automation + productization + template + compounding。实测 `opportunities.json` 的类型分布是 `{automation: 8, compounding: 1, defer: 1, productization: 1, template: 1}` —— **共 12 个，但 `defer` 这一类被静默丢弃，分母只有 11**。另外 `max(1, ...)` 会在全零时给出 0/1 = 0 而不是 UNKNOWN | 实测 automation_ratio = 0.7273 = 8/11。**11 个样本撑起一个展示到小数点后 4 位的比率**——精度远超样本能支撑的分辨率。而且类别表是硬编码的：上游每新增一种 opportunity_type，分母就会再漏一次，且不会报错 |
| **C4** | **实现 B 的 `time_saved_proxy` 已经打到上限 100，失去分辨力** | 参数：automation 2.0h、template 1.2h、productization 1.5h、loop 0.75h，`score_per_proxy_hour = 4.0`；实测 `proxy_hours = 41.95` → 41.95×4 = 167.8 → clamp 到 **100** | 任何 >25 proxy hours 的输入都得 100 分。指标已饱和，再多做一倍工作分数不变 |
| **C5** | **`opportunity_score_proxy = 86` 是一个常数，不是一个测量值** | 实测 `data/derived/behavior_intelligence/opportunities.json`：**12 个机会的 score 全部恰好等于 100，evidence_refs 数量全部恰好等于 10**。代入公式 `100×0.72 + 10×1.4 = 86` —— 与展示值完全一致 | 两个自变量都被上游钉死在上限，这张分卡**在数学上无法变化**。它看起来是一个 0–100 的分数，实际是一个写死的 86。**一个恒等于上限的平均值不能作为自变量** |
| **C6** | **「小时数」参数是无出处的常数** | `personal_economic_proxy.v1_2_s07_p1.json`：`hours_per_automation_candidate: 2.0` 等 | 这些数字没有任何观测支撑。它们不是「估计」，是**假设**。可以保留，但必须在 UI 上标成假设并允许改（`build_memory_atlas_formula_what_if.py` 已有 what-if，方向对） |
| **C7** | **`personal_ai_economic_index_score` 是 6 张分卡的等权算术平均** | `build_memory_atlas_economic_proxy.py:318` | 6 个量纲完全不同、部分已饱和的分数取等权平均，得到 72。**这个 72 无法回答任何「A 还是 B」的问题**——它涨了，你不知道是自动化多了还是返工少了 |

### 3.4 🕳 缺的（AEI 有、本机完全没有）

| # | 缺什么 | AEI 对应 | 本机能不能补 |
|---|---|---|---|
| D1 | **人机分离**：fan-out / 批处理 / 真人对话没有拆开 | AEI 分 Claude.ai（人）与 1P API（程序），且从 v3 起一直分开报 | **能，且必须先做**。判定规则已实测可用（同 source 同小时 ≥15 场 → fanout；无用户发言/单轮/前 80 字重复 ≥5 次 → auto） |
| D2 | **分类器人工验证** | 150 条人工核对，报到每层的准确率 | 能。这是把「关键词规则」从不可信变成可信的唯一路径 |
| D3 | **时间序列口径锁定**：同一定义下的跨期对比 | AEI 每版都报「相比上期 ±X pp」 | 能。本机有 2026-08-08 → 2026-08-20 的 span（agent_brief），但太短 |
| D4 | **AI Autonomy 1–5 分**（与 directive 区分开） | 原语 4 | **能，而且本机数据比 AEI 更适合**：agent 会话里人类干预点是硬可观察的 |
| D5 | **输出物分类（artifact）** | v6，93% 对话有可识别产出 | **能，而且更强**：能直接看 Write/Edit 落到哪些路径、是否进 git |
| D6 | **成功/失败的硬信号** | 原语 5（但 AEI 只有模型自评） | 能，且更强：error_event_count / abort_count / 同题复问 |
| D7 | **不确定性表达**：AEI 报的是聚合百万级样本的点估计；本机样本小得多却报到小数点后 4 位 | — | 能：小样本必须给区间或直接不给 |
| D8 | **明确的「本指标不能回答什么」清单** | AEI v1 §4.1 Limitations 逐条列出；最关键一条：「cannot make definitive judgments as to how much Claude's outputs are actually incorporated by users in their tasks」 | 能。实现 B 有 `limitation_zh`，实现 A 没有 |

---

## 4. 同类工作的关键结论（每条带出处，重点标注反直觉的）

### 4.1 METR 随机对照实验 —— 本节最重要，因为它直接否定了本项目的默认叙事

**主文献**：Becker, Rush, Barnes, Rein，*Measuring the Impact of Early-2025 AI on Experienced Open-Source Developer Productivity*，arXiv:**2507.09089**（v1 2025-07-12，v2 2025-07-25，截至 2026-08-20 无 v3）；博客 https://metr.org/blog/2025-07-10-early-2025-ai-experienced-os-dev-study/ （2025-07-10）。**仅预印本，未见同行评审接收记录（查不到）。**

#### 🔴 反直觉结论 1：允许用 AI 让资深开发者**慢了 19%**

原文逐字："we find that allowing AI actually increases completion time by **19%**—AI tooling slowed developers down."

- 回归点估计 **0.188**，95% CI **(0.013, 0.395)**（即 +1.3%~+39.5%），来自仓库 https://github.com/METR/Measuring-Early-2025-AI-on-Exp-OSS-Devs 的 `regression.py` 输出
- **16 名**开发者、**246 个真实 issue**（136 允许 AI / 110 禁止）、任务均长 2.0 小时
- 开发者在该仓平均 5 年经验、1,500 次 commit，占仓库生命周期 59%
- 未做回归调整的原始差值是 **34%**（脚注 12）

**统计上的诚实补充（这是调研 agent 的读图推断，非 METR 文字陈述）**：论文默认 HC3 稳健标准误；Figure 15 里的两阶段 bootstrap（重采样开发者 → 开发者内 issue）区间**跨过 0**（上端约 −5%）。也就是说在最保守的不确定性口径下，该结果不显著。

#### 🔴 反直觉结论 2：**感知与实测差 39 个百分点**，而且专家比当事人错得更多

| 主体 | 判断 |
|---|---|
| 经济学专家（34 人） | 缩短 39% |
| ML 专家（54 人） | 缩短 38% |
| 开发者**事前**预测 | 缩短 24% |
| 开发者**事后**（做完之后）估计 | 缩短 20% |
| **实测** | **增加 19%** |

METR 后续自述（https://metr.org/blog/2026-05-11-ai-usage-survey/ ，2026-05-11）：开发者 "overestimated AI's effect on their time spent on tasks by **40 percentage points** on average"。

> **这条对本项目是致命的**：Memory Atlas 现在没有任何一个指标是「实测节省」，全部是从活动量推出来的代理量（实现 B 的 `time_saved_proxy` 直接把候选数 × 假设小时数当成节省）。**METR 证明了当事人对自己省了多少时间的直觉是系统性错误的，误差方向恒为高估。** 一个建立在「自我感觉」之上的省时分数，其误差不是随机噪声，是有方向的偏倚。

#### 🟡 但有个细分结论救回了一半：开发者的**相对**判断是准的

- 预测时间 vs 实际时间的 Pearson 相关：允许 AI 组 **0.64**，禁止组 **0.59**
- Figure 18 逐字："on issues that developers predict significant speedup (i.e. ≥ 33% or the top tertile of forecasted speedup), developers are **not slowed down** by AI"
- 逐字："**75% of developers experience slowdown**" —— 反过来说约 1/4 的人实测是加速

> **推断（我的）**：这说明「排序」比「幅度」可信。给本项目的直接启示是：**做排名和做趋势，不要做绝对幅度。**「这周比上周哪类任务更卡」是可信的；「你今年省了 41.95 小时」不可信。

#### METR 给出的 5 个「确有贡献」的减速因素（21 个候选里筛出的）

原文逐字分类："we find evidence that **5** factors contribute to the slowdown effect, ... mixed/unclear/no evidence for **10** factors, ... evidence against **6** factors."（注：博客写 20 个，论文 v2 写 21 个）

1. **Over-optimism about AI usefulness** —— 过度乐观导致**过度使用**
2. **High developer familiarity with repositories** —— 越熟悉自己的仓，AI 越难帮上忙
3. **Large and complex repositories** —— 平均 10 年历史、110 万行代码
4. **Low AI reliability** —— 建议接受率 **<44%**；**9%** 的时间花在审查/清理 AI 输出；**100%** 的开发者报告需要修改 AI 代码
5. **Implicit repository context** —— AI 用不上默会知识

时间去向对比（Figure 6，调研 agent 读图）：允许 AI 组多出「审查 AI 输出 ~9%、写 prompt ~8%、等待生成 ~4%」，而「实际写代码」从 ~36.5% 降到 ~24.5%。

#### METR 明确说**不能**推广到什么（Table 2，六条，逐字节选）

1. "We do not claim that our developers or repositories represent a majority or plurality of software development work"
2. "We only study software development"
3. 不主张近期 AI 在同一场景下也不会加速
4. 不主张不存在更有效的使用方式
5. 不主张经验更丰富的 AI 使用者也不会加速
6. "We estimate that **some** developers experience speedup from AI"

§4.1 补充逐字："our results are consistent with **small greenfield projects or development in unfamiliar codebases seeing substantial speedup** from AI assistance."

#### 🔴 反直觉结论 3：METR 在 2026 年**放弃了这个实验设计**，但**没有撤回结论**

《We are Changing our Developer Productivity Experiment Design》，https://metr.org/blog/2026-02-24-uplift-update/ ，**2026-02-24**。

第二轮：2025 年 8 月启动，**57 名开发者、143 个仓、800+ 任务**，报酬从 $150/h 降到 $50/h。新估计（逐字）：

> "For the subset of the original developers who participated in the later study, we now estimate a speedup of **-18% with a confidence interval between -38% and +9%**. Among newly-recruited developers the estimated speedup is **-4%, with a confidence interval between -15% and +9%**."

方向翻转成加速，但**两个区间都跨零**。

放弃设计的原因（逐字）：

> "**30% to 50% of developers** told us that they were choosing not to submit some tasks because they did not want to do them without AI."
> "Together, these effects make it likely that our estimate reported above is a **lower-bound**."

⚠️ **必须防的二手污染**：网上大量摘要称「METR 承认方法论存在致命缺陷」「修正结论为我们不知道 AI 是否提高生产力」——调研 agent 逐字核验原文，**这两句话不存在**。METR 的倾向判断反而是 AI 的加速效果在 2026 年初**已经上升**。另注：该文开头写 "a 20% slowdown"，结果段写 "19% longer"，**METR 自己的文案就不一致**。

#### 🔴 反直觉结论 4：任务级大幅加速 与 交付级小幅提升，可以同时为真

这是调和 METR 与所有「AI 让人快 55%」研究的最有力框架。

**NBER WP 35275**，Demirer, Musolff & Yang，*Writing Code vs. Shipping Code*，**2026-05**，https://www.nber.org/papers/w35275 ：10 万+ GitHub 开发者，累积 commit 效应 autocomplete **+40%**、interactive agents **+140%**、autonomous agents **+180%**，但衰减到**项目层 +50%**、**发布层 +30%**。

配套证据：
- **微软观测研究**（非 RCT）：Murphy-Hill, Butler & Savelieva，arXiv:2607.01418，**2026-07-01**，数万名微软工程师，"adopters merged roughly **24% more pull requests** than they would have otherwise"，四个月窗口内持续
- **Faros AI 遥测**（1,255 团队 / 10,000+ 开发者），https://www.faros.ai/blog/lab-vs-reality-ai-productivity-study-findings ，2025-07-28：任务完成率 +21%、合并 PR +98%，但 **PR 体积 +154%**、**评审时间 +91%**。逐字结论："Developers are completing a lot more tasks with AI, but organizations aren't delivering any faster"
- **He et al.《Speed at the Cost of Quality》**，arXiv:2511.04427（v1 2025-11-06 / v3 2026-01-26，MSR 2026）：Cursor 带来 "large but **transient**" 加速，伴随静态分析告警与复杂度**持续**上升，且质量债**因果性地**导致后期减速
- **Afroz et al.《The Fast and Spurious》**，arXiv:2510.24265（v1 2025-10-28 / v2 2026-04-05，FSE Companion 2026）：415 名从业者，"perceived productivity gains may be **spurious**"

> **给本项目的直接启示**：只统计「动作量」（events、commits、tool calls）必然得到乐观结论，因为动作量正是 AI 最容易放大的东西。**要诚实，就必须有一个下游的、更难放大的分母**（合并、发布、复发率）。

#### METR 的时间跨度（time horizon）指标 —— 顺带修正一个常见误引

*Measuring AI Ability to Complete Long **Software** Tasks*（v3/v4 改的名），arXiv:**2503.14499**，v1 2025-03-18 / v2 2025-03-30 / v3 2026-02-25 / v4 2026-07-10。

- v2 逐字：50% 成功率的时间跨度 "doubled every **212 days**（95% CI 171–249）"；v4 更新为 "**207 days**（166–240）"
- **Time Horizon 1.1 改版**（https://metr.org/blog/2026-1-29-time-horizon-1-1/ ，2026-01-29）：任务从 170 增至 228；**2023 年以后的倍增时间从 165 天缩到 131 天**，逐字 "progress is estimated to be **20% more rapid**"
- METR 自己的局限说明（Kwa，https://metr.org/notes/2026-01-22-time-horizon-limitations/ ，2026-01-22）逐字：
  - "**Time horizon is not the length of time AIs can work independently**"
  - "I really have no idea whether Claude's 'true' time horizon is 3.5h or 6.5h. Error bars have historically been a factor of **~2** in each direction."
  - "**Doubling the time horizon does not double the degree of automation.**"
  - 99%+ 可靠度下的时间跨度 "**cannot be fit at all**"
- ⚠️ 污染警告（《Frontier Risk Report》，https://metr.org/blog/2026-05-19-frontier-risk-report/ ，2026-05-19）逐字："for tasks that are over 8 hours long in Time Horizon 1.1, we found that at least **16% of successful runs were illegitimate** upon review"
- METR 内部自我批评（Barry，https://metr.org/notes/2026-03-20-impact-of-modelling-assumptions-on-time-horizon-results/ ，2026-03-20）逐字：多数建模假设的修正 "end up having the effect of **reducing recent 50% time horizon estimates**"；并披露 "Until it was updated on **2026/03/03**, the time horizon model didn't find the maximum likelihood estimates"

> **给本项目的启示**：一个被广泛引用的指标，其发布方自己在 10 个月内两次下修、公开承认拟合有 bug、并且明确说「它不是 AI 能自主工作多久」。**PRD 里任何一个「趋势线」都必须带这条纪律：版本化定义 + 重算历史 + 公示重算幅度。**

### 4.2 Google DORA：同一个团队，两年里把自己的结论反转了一半

**版本清单**（一手来源：https://dora.dev/research/publications/ ，2026-08-20 抓取）

| 报告 | 版本 | 日期 |
|---|---|---|
| 2024 Accelerate State of DevOps Report | v.2024.1 → 现行 **v.2024.3** | 2024-10-23 |
| **State of AI-assisted Software Development 2025**（首版） | v.2025.1 → **v.2025.2** | 2025-09-23/24 |
| DORA AI Capabilities Model report | v.2025.1 | 页面 2025-11-25 |
| **ROI of AI-assisted Software Development** | **v.2026.1** | 2026-04-22 |

⚠️ **截至 2026-08-20 不存在 2026 版《State of AI-assisted Software Development》**（`https://dora.dev/research/2026/` 返回 404）。2026 年唯一新报告是 ROI 报告。

#### 🔴 反直觉结论 1：DORA 2024 —— AI 采纳度上升，交付吞吐和稳定性**双双下降**

一手 PDF：https://services.google.com/fh/files/misc/2024_final_dora_report.pdf （页脚 v.2024.3）。统一口径逐字：`If AI adoption increases by 25%… Estimated % change in outcome`。

- **software delivery throughput：−1.5%**
- **delivery stability：−7.2%**
- 同一份问卷同一批人：**individual productivity +2.1%**、job satisfaction +2.6%、flow +2.2%
- **39.2% 的受访者对 AI 生成代码「little or no trust」**（DORA 勘误页逐字引 p.6：https://dora.dev/research/2024/errata/ ）

**同源自陈矛盾**：同一年同一份问卷里，个体说自己更高效（+2.1%），团队交付却更慢更不稳（−1.5% / −7.2%）。

**勘误记录核查**：https://dora.dev/research/2024/errata/ 显示 2024 报告的全部勘误都是排版/拼写，**−1.5% / −7.2% 这两个数从未被 DORA 自己撤回或修订**。

#### 🔴 反直觉结论 2：DORA 2025 反转了吞吐量结论，但**没有**反转不稳定性

Google Cloud 官方博客逐字（https://cloud.google.com/blog/products/ai-machine-learning/announcing-the-2025-dora-report ，2025-09-24）：

> "Unlike last year, we observe a **positive** relationship between AI adoption on both software delivery throughput and product performance... **However, AI adoption does continue to have a negative relationship with software delivery stability.**"

报告 PDF 内部逐字："AI adoption now improves ... **However, it still increases delivery instability.** This suggests that while teams are adapting for speed, their underlying systems have not yet evolved to ..."

⚠️ **一个几乎所有二手报道都漏掉的方法学陷阱**：2025 版**换了口径** —— 不再给「采纳度 +25% → ±X%」的百分比，改为**标准化 β + 89% 可信区间**（PDF 图注逐字："Estimated effect of AI adoption on key outcomes, with **89% credible intervals**"，脚注 "Technically a standardized beta weight" / "standard deviation increase in AI adoption"）。**2024 与 2025 的数字不可直接放进同一张表比较。**

2025 采纳与信任数字（一手 PDF）：**90% 使用 AI**（比去年 +14.1%）；每日中位交互 **2 小时**；**信任分布：完全不信 7% / 一点点 23% / 有些 46% / 很信 20% / 非常信 4%**（即 30% 低信任、24% 高信任）；**80%+ 认为 AI 提升了自己的生产力**。

> ⚠️ 二手源 Faros 写「95% of developers」，与 DORA 一手 PDF 的 90% 冲突，**以 90% 为准**。

#### DORA 2025 的七个团队原型（cluster analysis，占比来自一手 PDF 逐字）

Foundational challenges **10%** ｜ Legacy bottleneck **11%** ｜ Constrained by process **17%** ｜ High impact, low cadence **7%** ｜ Stable and methodical **15%** ｜ Pragmatic performers **20%** ｜ Harmonious high-achievers **20%**

（簇号 ↔ 名称的绑定是调研 agent 按占比对齐的**推断**，因为两个名称在 PDF 文本层被矢量化；名称本身由 Google 官方博客确认。）

#### DORA AI Capabilities Model 的七项能力（一手 PDF 目录页逐字）

1. Clear and communicated AI stance｜2. Healthy data ecosystems｜3. AI-accessible internal data｜4. **Strong version control practices**｜5. **Working in small batches**｜6. User-centric focus｜7. Quality internal platforms

⚠️ **每项能力的点估计效应量查不到** —— 报告只给「Small / Medium / Large increase」的定性网格。

#### 🔴 反直觉结论 3：DORA 自己提出「验证税」

https://dora.dev/insights/balancing-ai-tensions/ ，**2026-03-10**，基于 1,110 条 Google 工程师开放式回答（2025 Q3）。提出 **"verification tax"**：创作阶段省下的时间被重新分配到审计与验证。原文引用的工程师原话："I spend more time babysitting the AI and reviewing what it is trying to do." / "Reviewing code is so much harder than writing it."

DORA 的结论措辞是：这是**认知负担从作者转移到审阅者**，不是净生产力增益。

#### DORA 自己声明的因果限度（2025 一手 PDF 逐字）

> "**Correlation may not imply causation**, but how you think about causation will impact your correlations."
> "**Occasionally we will speak in causal terms, but ultimately, we're doing comparisons.**"
> "... our survey is a **snapshot, not a video** of a dynamic process."

DORA 是**纯问卷自陈、无遥测**；2025 样本 **4,867 名受访者** + 78 人定性访谈（其中 76 人在美国，原文自承 "not surprising, given the interviewer's limitations"）。

**DORA 的「AI 采纳度」因子由三个自陈项构成：使用频率 / 依赖程度 / 信任程度。** 原文承认 "Trust is a prerequisite for use, but use is the mechanism for building trust" 这个反馈环难以分离。
> **推断（调研 agent 的）**：这意味着 DORA 的「采纳度」不是纯行为量，内含态度成分；「高采纳 ↔ 好结果」的相关里有一部分是同源自陈方差。

### 4.3 GitHub / Microsoft Copilot 研究：数字随「任务真实度」单调下降

#### Peng et al. 2023 —— 「55% faster」的原始出处，以及它被滥用的方式

*The Impact of AI on Developer Productivity: Evidence from GitHub Copilot*，Peng, Kalliamvakou, Cihon, Demirer，**arXiv:2302.06590，2023-02-13，仅 v1**。

摘要逐字："Recruited software developers were asked to implement an **HTTP server in JavaScript** as quickly as possible. The treatment group... completed the task **55.8% faster**."

**必须一起说的限定词**（全部来自论文正文）：
- 实验期 **2022-05-15 ~ 06-20**（Copilot GA 之前）
- 招募自 **Upwork 自由职业平台**；随机分组 45 / 50，**最终完成并交问卷的只有两组各 35 人（合计 70 人）**
- 处理组 71.17 分钟 vs 对照组 160.89 分钟；**95% CI 宽达 [21%, 89%]**，p = 0.0017
- 四个 >300 分钟的离群值**全部在对照组**
- **成功率差异不显著**（95% CI [−0.11, 0.25]）
- 作者自陈逐字："**this study does not examine the effects of AI on code quality**"、"more research is needed to understand how our results generalizes to other tasks"

#### 🔴 反直觉结论 4：在这项研究里，开发者的自陈是**低估**，方向与 METR 相反

论文正文逐字：

> "On average, participants in **both treated and control groups estimated a 35% increase** in productivity, which is an **underestimation** compared with the **55.8%** increase in their revealed productivity."

> **这条极其重要，因为它阻止我们把「开发者总是高估 AI」当成定论。** Peng（合成短任务、陌生代码）里是低估 20pp；METR（成熟真实仓库、5 年经验）里是高估 39pp。**感知偏差的方向取决于任务真实度和熟悉度，不是常数。** 对本项目的意义：不能用一个固定的「乐观折扣系数」去校正自陈，因为方向本身会翻。

#### Cui et al. 三场田野 RCT —— 摘要说 26%，分实验看只有一场显著

*The Effects of Generative AI on High-Skilled Work: Evidence from Three Field Experiments with Software Developers*，Cui, Demirer, Jaffe, Musolff, Peng, Salz。**Management Science 在线首发 2026-02-27，DOI 10.1287/mnsc.2025.00535**；SSRN abstract_id=4945566；作者自存 PDF https://www.mertdemirer.com/Papers/Demirer_AI_productivity.pdf （标注 June 2025）。**AEA 注册号 AEARCTR-0014530，注意是 post-registered（事后注册）。NBER WP 编号：查不到。**

摘要逐字："when data is combined across three experiments and **4,867 developers**, our analysis reveals a **26.08% increase (SE: 10.3%)** in completed tasks"。

**分实验拆开看（Table 3，加权 IV 口径）**：

| | Microsoft | Accenture | Anon. Co. | Pooled |
|---|---|---|---|---|
| Pull Requests | **27.38 (12.88)** | 17.94 (18.72) **不显著** | 54.03 (42.63) **不显著** | 26.08 (10.3) |
| Commits | 18.32 **不显著** | −4.48 **不显著** | — | 13.55 **不显著** |
| Builds | 23.19 **不显著** | 92.40*** | — | 38.38*** |
| **Build Success Rate** | −1.34 | **−17.40 (7.12) 显著负** | — | −5.53 |

> **三场实验里只有 Microsoft 一场的主结果单独显著；Accenture 的 build success rate 显著下降 17.4%** —— 这个负信号在摘要里完全看不到。

作者自陈局限（逐字）："the implementation of these experiments was **ad-hoc**"；"Because of **imperfect compliance**, our preferred estimates use treatment status as an instrument for usage, so this is an estimate of the **local average treatment effect for adopters**"（不是 ITT，也不是全样本 ATE）。

作者对活动量指标的自我警告（逐字）："**A less optimistic interpretation of the increase in builds is that developers may engage** [in more trial-and-error]"；"the time saved on coding may not fully translate into additional coding output."

⚠️ 注意 Cui et al. 的样本数 4,867 与 DORA 2025 的受访者数 4,867 **完全相同，纯属巧合**，引用时勿混。

#### 🔴 反直觉结论 5：代码质量证据方向相反，取决于谁做的、测多久

| 来源 | 结论 | 设计 |
|---|---|---|
| **GitHub 自家 RCT**（Bauer，https://github.blog/news-insights/research/does-github-copilot-improve-code-quality-heres-what-the-data-says/ ，2024-11-18，更新 2025-02-06） | Copilot 组通过全部单测的可能性 **+53.2%**（p<0.01）、readability +3.62%、reliability +2.94% | **N=202，合成的餐厅评论 API 绿地小任务，厂商自研自评** |
| **GitClear 纵向**（https://www.gitclear.com/ai_assistant_code_quality_2025_research ，PDF 内标日期 **2025-02-14**） | **2.11 亿行变更（2020-01~2024-12）**：refactor 相关变更从 **2021 年 25% 降到 2024 年不足 10%**；copy/paste 从 **8.3% 升到 12.3%**；「copy/paste 首次超过 moved code」 | 真实企业仓库纵向数据 |
| **GitClear 2026**（https://www.gitclear.com/the_ai_code_quality_maintainability_gap ，2026-01） | **6.23 亿次变更（2023~2026）**：block duplication **+81%**、error-masking constructs **+47%**、two-week churn **+15%**；moved code 从 **21%(2022) → 3.8%(2026 YTD)**；「**The throughput is real, but so is the debt it accrues**」 | 真实仓库纵向 |
| **Uplevel**（https://uplevelteam.com/blog/ai-for-developer-productivity ） | 「Copilot access provided **no significant change in efficiency metrics**」；使用者「introduced **41% more bugs**」 | 近 800 名开发者的客观工程遥测。⚠️ 原始发布日期查不到（页面现显示 2026-07-21，疑为重发；最早报道见 2024-09-17） |

#### 🔴 反直觉结论 6：横截面上「AI 重度用户产出高 4–10 倍」，但绝大部分差距**先于 AI 就存在**

GitClear，*AI Coding Tools Attract Top Performers – But Do They Create Them?*，https://www.gitclear.com/developer_ai_productivity_analysis_tools_research_2026 ，**2026-01**。**2,172 个 developer-week**，数据直取 Cursor / Copilot / Claude Code 的提供商 API。

逐字："Developers who use AI throughout the day aren't just 10% faster—empirical data shows them authoring **4x to 10x more work** than 'AI non-users'"；但归因部分："**most of that gap pre-dated AI** — compared to **their past selves**, heavy AI users enjoyed a more modest **25% velocity gain**."

> **这是对本项目最直接的方法学警告**：任何「用 AI 的时段 vs 不用 AI 的时段」「AI 重度项目 vs 轻度项目」的横向对比，都会把「谁在用」误算成「用了什么」。**唯一诚实的对照是同一主体跟自己的过去比。**

#### 🔴 反直觉结论 7：验收率（acceptance rate）只预测「感知」生产力，**不**预测代码留存

Ziegler et al.，*Productivity Assessment of Neural Code Completion*，**arXiv:2205.06537，2022-05-13**（GitHub 自家作者）。摘要逐字：

> "Commercial products aim to increase programmers' productivity, **without being able to measure it directly**... We find that **the rate with which shown suggestions are accepted, rather than more specific metrics regarding the persistence of completions in the code over time, drives developers' perception of productivity**."

> **推断（调研 agent 的，我认同）**：论文标题里的产品就是 GitHub Copilot，而验收率正是 Copilot 官方公布的核心指标 —— 也就是说 GitHub 自家的论文测出：验收率是**感知生产力**的最佳预测因子，恰恰**不是**代码留存的预测因子。（「验收率被广泛用作 ROI 代理指标」这句我找不到可引的统计来源，故不写。）
> **对本项目的映射**：`tool_call_count`、`event_count` 这类活动量在 Memory Atlas 里扮演的正是验收率的角色 —— 它们预测「看起来很忙」，不预测「留下了什么」。

#### 一条可以立起来的主线（调研 agent 的推断，我认同并采纳）

**55.8%（合成任务、实验室、N=70）→ 26.08%（真实工作、三场 RCT 合并，仅 1/3 显著）→ −19%（成熟真实仓库、资深开发者）→ 同一人跟自己比约 +25%（提供商 API 遥测）。**

数字随「任务真实度↑、对代码库熟悉度↑、测量口径从活动量转向完成时间」而**系统性下降**。

> **对 Memory Atlas 的直接后果**：这个项目测的恰好是**最真实的一端**（自己的成熟仓、自己是最熟悉的人、真实任务）。**所以它没有资格引用 55% 那一类数字，也不应该期待自己的数据会长得像那些数字。** 如果 PRD 里出现「AI 让我快了 N 倍」，它和文献里最接近本场景的那条证据是矛盾的。

### 4.4 单人 / 单时间线数据的统计效力：什么能做、什么不能做

#### SPACE 框架 —— 它**允许**你测自己，但同时否定了你现在的测法

**一手出处（两个版本，正文一致）**
- ACM Queue 原版：Forsgren, Storey, Maddila, Zimmermann, Houck, Butler，*The SPACE of Developer Productivity*，*Queue* **19(1): 20–48**，**2021-02-28**，DOI 10.1145/3454122.3454124
- CACM 重印版（下面逐字引用取自这版）：同作者，*Communications of the ACM* **64(6): 46–53**，**2021-05-24**，DOI 10.1145/3453928。可取全文 PDF：https://people.uncw.edu/vetterr/classes/csc550-spring2023/The%20SPACE%20of%20Developer%20Productivity.pdf

摘要逐字："Developer productivity is about more than an individual's **activity levels**... and **it cannot be measured by a single metric or dimension**."

> **这一句同时命中现有实现的两个问题**：① 实现 A 的全部输入都是 activity（event 计数）；② 实现 B 把 6 张量纲不同的分卡等权平均成一个 `personal_ai_economic_index_score = 72`，正是「用单一指标衡量」。

**五个维度（原文定义，verbatim）**

| 维度 | 原文定义 |
|---|---|
| **S**atisfaction and well-being | "Satisfaction is how fulfilled developers feel with their work, team, tools, or culture; well-being is how healthy and happy they are" |
| **P**erformance | "Performance is the outcome of a system or process." |
| **A**ctivity | "Activity is a count of actions or outputs completed in the course of performing work." |
| **C**ommunication and collaboration | "capture how people and teams communicate and work together" |
| **E**fficiency and flow | "the ability to complete work or make progress on it with minimal interruptions or delays, whether individually or through a system" |

#### 🔴 最重要的一条修正：SPACE **没有**禁止个人层面度量

CACM 版 p.52 逐字（这是全文唯一直接回答这个问题的段落）：

> "Teams and organizations should be cognizant of developer privacy and report only anonymized, aggregate results at the team or group level. (In some countries, reporting on individual productivity isn't legal.) **Individual-level productivity analysis, however, may be insightful for developers.** … Developers can opt in to these types of analyses, gaining valuable insights to optimize their days and manage their energy."

原文区分的是三种场景，不是一刀切：

| 场景 | SPACE 原文立场 |
|---|---|
| 组织/管理者**对外报告**个人生产力 | 反对 —— 只报团队或组的**匿名聚合**结果 |
| **开发者自己分析自己（opt in）** | **明确允许，且认为「may be insightful」** |
| 用 Activity 单项指标奖惩个人 | **明确禁止** |

> **推断（我的）**：Memory Atlas 正好落在中间那一栏 —— owner 自愿地分析自己。**所以「SPACE 说不要测个人」这句常见转述用在这里是错的，不要写进 PRD。** 真正约束本项目的是下面那几条使用规则。
> ⚠️ 附带纠正：DX（Abi Noda 公司）科普页写 SPACE 指标 "designed for team and organizational insights, not individual performance evaluation"（https://getdx.com/blog/space-metrics/ ，更新 2025-07-30）——**这是厂商博客，不是原论文，且与原文那段并不一致**，引用需降级为二手。

**SPACE 论文自己定的使用规则（全部 verbatim，这些才是真正约束本项目的）**

1. **至少三个指标，且跨维度**："teams and leaders (and even individuals) should capture several metrics across multiple dimensions of the framework—**at least three are recommended**." 原文的操作说明：如果已经在量 commits，不要再加 PR 数和 coding time，因为这三个**都是 Activity**；要 "add at least one metric from **two different dimensions**"。
2. **至少一个必须是感知类（问卷）指标**："at least one of the metrics include **perceptual measures such as survey data**."
3. **也不能太多**："a good measure of productivity consists of a **handful** of metrics across at least three dimensions"；"Having too many metrics may also lead to confusion and lower motivation"。
4. **Activity 绝不能单独使用**（原文说了两次）："they should **never be used in isolation** either to reward or to penalize developers." / "…never be used in isolation to make decisions about individual or team productivity because of their known limitations."
5. **Activity 本身有可测性天花板**："it is **almost impossible to comprehensively measure and quantify all the facets** of developer activity"
6. **图 1 里带 † 的指标要额外小心**：脚注 "Use these metrics with (even more) caution — they can proxy more things."，被标 † 的包括 **Lines of code、Retention、Story points、Quality of meetings**
7. **不能跨文化/跨基线比较感知指标**："measures from these different cultures will have a different baseline and **shouldn't be compared with each other**."
8. **不要跨长时段做时间归一化**（原文举例：按年归一化会 "bias against those taking parental leave"）

> **逐条对照 Memory Atlas 的当前状态（我的推断）**：
> - 规则 1 ❌ —— 六个维度里**只有 Activity 一个有数据**（Performance 是 `verified_outcome_rate = 0`，Efficiency & flow 未实现）
> - 规则 2 ❌ —— **零个感知类指标**。而项目有「零 Agent 零 Token」铁律，问卷类数据需要 owner 自己录入，这是唯一的合法来源
> - 规则 4 ❌ —— 现在展示的三个百分比全部由 Activity 单独构成
> - 规则 5 ✅ 反向印证 —— 这正是 §5.2 说「日志分母不完整」的原论文依据
>
> **结论：按 SPACE 自己的规则，Memory Atlas 现在的「行为经济」页不构成一个合格的生产力测量 —— 不是因为它测了个人，而是因为它只有一个维度、且那个维度是被原文点名「绝不能单独使用」的那一个。**

#### DevEx 框架（SPACE 同一批作者的后续，三个维度）

Noda, Storey, Forsgren, Greiler，*DevEx: What Actually Drives Productivity*，*Queue* **21(2): 35–53**，**2023-04-30**，DOI 10.1145/3595878（CACM 版：*CACM* 66(11): 44–49，2023-10-20，DOI 10.1145/3610285）。可取 PDF：https://www.michaelagreiler.com/wp-content/uploads/2024/06/DevEx-WhatDrivesProductivity.pdf

三个维度（原文定义 verbatim）：
1. **Feedback loops** — "the speed and quality of responses to actions performed"
2. **Cognitive load** — "the amount of mental processing required for a developer to perform a task"
3. **Flow state** — "a mental state in which a person performing an activity is fully immersed"

⚠️ **DevEx 原文中没有任何禁止个人层面测量的句子 —— 查不到。** 它的相关表述是反向的：警告不要只看聚合（"Focusing only on aggregate results can lead to overlooking problems"）。

> **推断（我的）**：Feedback loops 这一维在本机是**现成可测**的 —— 会话内工具调用之间的等待时间、错误到修复的时延，都在数据里。**这是补齐 SPACE 规则 1「至少两个维度」成本最低的一条路。**

#### Goodhart / Campbell 定律 —— 为什么「把分数做高」本身就是失效模式

- **Goodhart 1975 原始表述**（as commonly quoted）："Any observed statistical regularity will tend to collapse once pressure is placed upon it for control purposes." —— Goodhart, C.A.E. (1975), *Papers in Monetary Economics*, Vol. I, Sydney: Reserve Bank of Australia。⚠️ **该措辞有两个流通版本**（另一版为 "…break down when pressure is applied…"），**1975 年原书未取得，无法裁定哪个字面为真 —— 查不到**，引用时应注明「as commonly quoted」。
- **Strathern 1997 的通俗化表述**（已取原文 PDF 逐字核对）："When a measure becomes a target, it ceases to be a good measure." —— Strathern, M. (1997), "'Improving ratings': audit in the British University system", *European Review* **5(3): 305–321，句子在 p.308**，DOI 10.1002/(SICI)1234-981X(199707)5:3<305::AID-EURO184>3.0.CO;2-4。PDF：https://gwern.net/doc/statistics/decision/1997-strathern.pdf
  **原文的下一句常被漏掉，而它恰好切中本项目**："The more a 2.1 examination performance becomes an expectation, the poorer it becomes as a discriminator of individual performances." —— 她说的是**指标丧失区分能力**。Strathern 本人并未自称提出定律，她把命名归给 Hoskin。
- **优先权其实在 Campbell**："The more any quantitative social indicator is used for social decision-making, the more subject it will be to corruption pressures…" —— Campbell, D.T. (1969), "Reforms as experiments", *American Psychologist* **24(4): 409–429**，DOI 10.1037/h0027982。溯源裁定见 Rodamar, J. (2018), "There ought to be a law! Campbell versus Goodhart", *Significance* **15(6): 9**，**2018-11-28**，DOI 10.1111/j.1740-9713.2018.01205.x，结论逐字："the phenomenon of the corruption of metrics is appropriately known as '**Campbell's law**'"。

> **对应本项目的具体风险**：§6 的【1】可判定率一旦被当成「要做高的分数」，最省事的做法就是放宽分类规则 —— 可判定率上去了，准确率下来了。**这就是为什么我把「人工抽检一致率」和它绑成一个不可拆的指标对。**

#### 对「用活动量/产出量当生产力」的具名批评

**McKinsey**，《Yes, you can measure software developer productivity》，**2023-08-17**，作者 Gnanasambandam, Harrysson, Hussin, Keovichit, Srivastava。https://www.mckinsey.com/industries/technology-media-and-telecommunications/our-insights/yes-you-can-measure-software-developer-productivity

它提出四个 "opportunity-focused metrics"：inner/outer loop time spent（目标 "up to 70 percent of their time doing inner-loop activities"）、Developer Velocity Index、**contribution analysis**（明确是个人层面："Assessing contributions by individuals to a team's backlog"，用 "a proprietary algorithm" 归一化 Jira 数据）、talent capability score。它自己也承认 LOC 与 commit 数是 misuse，并写 "developers may submit smaller changes more frequently as they seek to game the system"。

**公开反驳**
| 文章 | 作者 | 日期 |
|---|---|---|
| Measuring developer productivity? A response to McKinsey（Part 1） | **Gergely Orosz & Kent Beck** | **2023-08-29** — https://newsletter.pragmaticengineer.com/p/measuring-developer-productivity |
| Part 2 | 同上 | **2023-08-31** — https://newsletter.pragmaticengineer.com/p/measuring-developer-productivity-part-2 |
| What McKinsey got wrong about developer productivity | Jennifer Riggins（LeadDev） | **2023-10-23** — https://leaddev.com/career-development/what-mckinsey-got-wrong-about-developer-productivity |

核心论点（逐字节选，⚠️ 这是 newsletter 正文，非同行评审）：
- McKinsey 的自定义指标 "**measure effort or output**"，不是结果与影响（"4 out of the 5 new metrics suggested by McKinsey's measure effort or output"）
- 权衡律：**"The earlier in the cycle you measure, the easier it is to measure."** —— 越早越好测，也越容易产生副作用
- 后果：**"the act of measurement changes how developers work"**；Part 2 判定该框架会 "do far more harm than good to organizations"
- Kent Beck 的评价逐字："**absurdly naive and ignores the dynamics of high-performing software engineering teams**"；他举的 Facebook 反例：分数一旦向上汇总，"Directors put pressure on managers for better scores"
- 他们的建议：测**团队的 impact**（收入、成本、可靠性），effort/output 数据只用于 **debugging**，不进绩效激励

> **映射**：这条批评的靶心（effort/output 类指标）正是 Memory Atlas 现在唯一有数据的那一类。§6 的【3】下游收敛率就是为了把「产出」拉到「结果」那一端。
> **并且 Beck & Orosz 的「只用于 debugging」正是这个项目应该采取的定位** —— 这是一个个人自用的诊断工具，不是绩效系统。这个定位一旦写进 PRD，很多伪指标自然就不需要了。

#### 🔴 最有杀伤力的一条实证：遥测能解释的方差里，大部分是「他是谁」而不是「他做了什么」

**Beller, M., Orgovan, V., Buja, S., Zimmermann, T.，*Mind the Gap: On the Relationship Between Automatically Measured and Self-Reported Productivity*，*IEEE Software* 38(5): 24–31，2021-09**，DOI 10.1109/MS.2020.3048200｜预印本 https://arxiv.org/abs/2012.07428 （2020-12-14）。微软 81 名开发者。

逐层建模解释的「自评生产力」方差：

| 模型 | R² |
|---|---|
| 仅 coding time 遥测 | **7%** |
| + 全部应用遥测 | **9%**（只加了 2 个百分点） |
| **+ 每个开发者的个人截距（User ID）** | **34%** |
| + 日属性（睡眠 / 打断 / 出差等自报） | **47%** |

原文结论："establishing an **individual baseline** for rating behavior is crucial"，并指出自评与实测之间存在 "large conceptual discrepancy"。原文另引一项研究：LOC + 资历只解释 **1.7%**。

佐证：**Kuutila, Mäntylä, Claes, Elovainio, Adams，*Individual differences limit predicting well-being and productivity using software repositories*，*Empirical Software Engineering* 26(5)，2021-06-26**，DOI 10.1007/s10664-021-09977-1。单团队跟踪 8 个月 + 每日经验取样。摘要逐字："**individual variance accounts for most of the R² values**"；"Prediction models developed for each developer individually work better, with fixed effects R² value of up to **0.24**"；"**individualized prediction models are needed**"。

构念效度的经典批评：**Kaner, C. & Bond, W.P.，*Software Engineering Metrics: What Do They Measure and How Do We Know?*，METRICS 2004**，http://kaner.com/pdfs/metrics2004.pdf 。逐字："how we know that we're measuring the attribute that we think we're measuring?"；"**all metrics should be validated**"。

> **这三条合起来给本项目一个意外的好消息（我的推断）**：跨人比较活动计数在统计上几乎没有立足点（遥测只解释 7–9%），而**个人基线是必要条件** —— 这恰恰是 n=1 纵向数据相对跨人 benchmark 的**唯一结构性优势**。
> **所以正确的产品叙事不是「我和世界比」，而是「我和我的过去比」** —— 后者在文献里有支撑，前者没有。
>
> ⚠️ **查不到**：任何直接针对「session/会话计数」作为生产力代理的同行评审批评。commits / LOC / PR 都有，session 没有。**这意味着用会话数当产出量是一个未被验证过的构念，不是一个已被验证为坏的构念** —— 但按 Kaner & Bond 的标准，未验证的构念不能直接使用。

#### 单被试实验设计（SCED）与 n-of-1 —— 单人数据能做什么实验、门槛在哪

**权威标准文献**：What Works Clearinghouse，*Procedures and Standards Handbook, Version 5.0*，U.S. Dept. of Education, IES/NCEE，WWC 2022008，**2022 年 8 月**，第 VI 章。PDF：https://ies.ed.gov/ncee/wwc/Docs/referenceresources/Final_WWC-HandbookVer5.0-0-508.pdf
其他可引：Kratochwill et al.，*Single-Case Intervention Research Design Standards*，*Remedial and Special Education* **34(1): 26–38**，2012-08-15，DOI 10.1177/0741932512452794｜Horner et al.，*Exceptional Children* **71(2): 165–179**，2005-01，DOI 10.1177/001440290507100203｜**SCRIBE 2016 报告规范**：Tate et al.，*Archives of Scientific Psychology* **4(1): 1–9**，**2016-04-14**，DOI 10.1037/arc0000026

**设计类型（WWC v5.0 逐字）**："reversal/withdrawal designs, multiple baseline designs, alternating and simultaneous intervention designs, changing criterion designs, and variations of these core designs like multiple probe designs."

**核心门槛（逐字）**："at least **three demonstrations** of an intervention effect at **three different points in time**"

**各设计的最低数据量（WWC v5.0 原文数字）**

| 设计 | Meets Without Reservations | Meets With Reservations |
|---|---|---|
| Reversal/withdrawal (ABAB) | 每条件 ≥2 阶段（最简 4 阶段）；**首个基线 ≥6 点**；至少 2 个阶段 **≥5 点/阶段** | 每条件 2 阶段 **≥3 点/阶段** |
| Multiple baseline / multiple probe | 最少 6 阶段分 2 条件（最简 3 层）；每层**首个基线 ≥6 点**；后续阶段 **≥5 点**；相位切换需 **3 个不同时点** | 每条件 3 阶段 **≥3 点/阶段** |
| Alternating treatment | 每条件 **≥5 点**；快速交替中同一条件连续点 ≤2 | 每条件 **≥4 点** |
| Changing criterion | **≥3 次不同的标准变更** | — |

（v5.0 把首基线要求从 5 点提到 **6 点**：原文 "Previous versions of the standards required at least five data points per phase"。）

#### 🔴 对本项目最直接的一条判决：单纯的「上线前 / 上线后」两段（AB 设计）拿不到任何评级

WWC v5.0 逐字：

> "most SCD experts consider this simple form of the SCD to have **weak internal validity** because the effect of the intervention could be due to **some other change that co-occurred**"

且少于 4 个阶段的 reversal 设计 → **Does Not Meet WWC Standards**。

**外部效度**：WWC 要求把 SCD 证据写进 intervention report 需要 "single-case design findings including **at least 20 cases across studies**"，且 ≥2 项研究达标。**换言之：在 WWC 体系下，1 个 case 无论做得多严，都不足以支撑效果结论。**

**n-of-1 试验**：Lillie, Patay, Diamant, Issell, Topol, Schork，*The n-of-1 clinical trial: the ultimate strategy for individualizing medicine?*，*Personalized Medicine* **8(2): 161–173**，**2011-03**，DOI 10.2217/pme.11.7｜PMC3118090。
- 定义："an individual patient as the sole unit of observation"
- 何时有效："**Chronic conditions** for which there are easily measurable clinical end points and where the drugs or interventions… have a relatively **short half-life** are the most amenable"
- 何时无效：进展/消退很快的病症；以及残留效应 —— "even if washout periods are included… the influence of a prior intervention… will linger"
- **能否外推（直接回答）**：n-of-1 试验 "**clearly defy easy generalizability**"
- 聚合路径："If multiple n-of-1 trials investigating the same sets of interventions are initiated, then it is possible to pursue joint or **meta-analytic** studies"
- 报告规范（书目已核，⚠️ 全文 403 未取得，条目内容**查不到**）：Vohra et al.，*CONSORT extension for reporting N-of-1 trials (CENT) 2015 Statement*，*BMJ* 2015;350:h1738，**2015-05-14**

> **对本项目的三条结论（我的推断，基于上面这些方法学要求）**：
> 1. **份额型指标不是这类设计的产物。** SCED / n-of-1 产出的是「A 相与 B 相之间的差」，不是「行为里 57% 属于某类」。**把 AEI 的 share 搬到单人数据上，等于把一个总体描述统计量装进了一个只支持组内对比的容器里。**
> 2. **反转设计（ABAB）在这里做不了**，因为要求能撤回干预（一段时间不用 AI）。METR 2026-02-24 实测：付 $50/小时都招不到愿意不用 AI 工作的开发者（"30% to 50% of developers told us that they were choosing not to submit some tasks because they did not want to do them without AI"）。owner 对自己更不可能执行撤回相。
> 3. **所以剩下的只有两条路**：**多基线**（在不同项目/任务类型上错开引入某个改变）和 **中断时间序列**（见下）。这两条都不需要撤回干预。**PRD 里任何一条「我们要证明 X 让我更高效」的主张，如果不落在这两种设计之一上，它在方法学上没有依托。**

#### 中断时间序列（ITS）—— 单人数据唯一有正式方法学支撑的分析形式

Bernal, Cummins & Gasparrini，*Interrupted time series regression for the evaluation of public health interventions: a tutorial*，**International Journal of Epidemiology, 2017, 46(1):348**，DOI 10.1093/ije/dyw098。

这篇是 ITS 的标准方法学参考。关键要求（原文口径）：
- **最少时间点**：原文明确说 "there are no fixed limits regarding the number of data points"，因为功效取决于多个因素；但警告时间点少或预期效应小的研究 "may be underpowered"，**建议事前做功效模拟**
- **自相关**：这是时间序列数据的独有问题，要用残差图和偏自相关函数检查；季节性调整后仍有问题则用 Prais 回归或 ARIMA
- **季节性**：需要用日历分层、Fourier 项或样条调整
- **什么时候 ITS 不适用**：干预前后期分界不清；干预到效果的时滞不清或高度可变；无法控制同期发生的其它事件

> **对本项目的映射**：Memory Atlas 的数据本质上就是一条单主体时间序列。**这意味着「趋势 + 断点」是这份数据在方法学上站得住的分析形式**，而「份额 / 百分位 / 覆盖率」不是。
> **但有三个硬约束（实测 `agent_brief.json` 的 project_briefs）**：
> ① **全局 span 是 2025-11-24 → 2026-08-20（约 9 个月），够做日级 ITS；但分项目几乎全是几天到几周** —— 主力项目 AgentDatabase 只有 **2026-08-08 → 2026-08-20（12 天）**，`kmvideo_work` 只有 3 天。**所以 ITS 只能在全局或跨项目合并层面做，不能按项目做。**
> ② 会话数据有强烈的星期与工作节律（AEI v6 实测周末个人类 prompt 从 ~35% 升到近 50%），**不做季节性调整的趋势线一定是假的**。
> ③ 这条时间线上有巨大的机器脉冲（单日 518 场扇出），**不先剔除就等于在时间序列里插了几个人造尖峰**，任何断点检测都会打在这些尖峰上。

#### ITS 的硬性最低点数在 Cochrane EPOC，不在 Bernal

Bernal 那篇拒绝给死数字，死数字在这里：**Cochrane EPOC，*What study designs can be considered for inclusion in an EPOC review and what should they be called?*，v1，2021-07-15**，DOI 10.5281/zenodo.5106084。PDF：https://zenodo.org/records/5106085/files/what_study_designs_should_be_included_in_an_epoc_review.pdf

逐字：建议排除 "ITS studies that do not have a clearly defined point in time when the intervention occurred and **at least three data points before and three after** the intervention."

**同一文件对「单一无对照单元」的判决（对本项目极其关键）**：

> "There is **no way to assess the impact of any concurrent events** on the outcomes of interest."

以及："**Inclusion of uncontrolled before-after studies… is strongly discouraged. It is difficult, if not impossible to attribute causation from such studies.**"

⚠️ 顺带纠正一个常见引用错误：Bernal 那篇的勘误是 **2020 年**的（*IJE* 50(3): 1045，DOI 10.1093/ije/dyaa118），**不存在 2018 年的勘误**；2018 年那篇是独立正文《The use of controls in interrupted time series studies of public health interventions》，*IJE* **47(6): 2082–2093**，DOI 10.1093/ije/dyy135 —— 而那篇的立场正是**加对照**。

> **推断（我的）**：本项目没有对照单元（只有一个人、一条时间线），所以按 EPOC 的判决，**任何「因为做了 X，所以指标变好了」的归因都不成立**，只能做描述性的趋势陈述。这不是保守，这是 EPOC 的原话。

#### 🔴 遍历性（ergodicity）—— 为什么「群体结论 ≠ 个体结论」是一条数学条件，不是态度问题

**Fisher, A.J., Medaglia, J.D., Jeronimus, B.F.，*Lack of group-to-individual generalizability is a threat to human subjects research*，*PNAS* 115(27): E6106–E6115，2018-06-18**，DOI 10.1073/pnas.1711978115｜PMC6142277

摘要首句逐字：

> "**Only for ergodic processes** will inferences based on group-level data generalize to individual experience or behavior."

实测（6 个样本，每样本 87–94 人）：

> "the variance around the expected value was **two to four times larger within individuals than within groups**"

Significance 段更直接："**the variance in individuals is up to four times larger than in groups**"（个体内/个体间标准差比 3.79:1 至 13.20:1，均值 **7.85:1**）。

论文的行动建议逐字："Researchers should **explicitly test for equivalence of processes at the individual and group level**"

理论源头（书目已核，未取全文故不引 verbatim）：Molenaar, P.C.M. (2004)，*A Manifesto on Psychology as Idiographic Science*，*Measurement* **2(4): 201–218**，DOI 10.1207/s15366359mea0204_1；Molenaar & Campbell (2009)，*The New Person-Specific Paradigm in Psychology*，*Current Directions in Psychological Science* **18(2): 112–117**，DOI 10.1111/j.1467-8721.2009.01619.x

> **这条对本项目是双向的（我的推断）**：
> - **禁止的方向**：拿 AEI 的 45%/52% 当「我应该长成什么样」的参照 —— 群体统计量不能外推到个体，除非过程是遍历的，而 Fisher 实测它不是。
> - **允许的方向**：正因为个体内方差比个体间大 2–4 倍，**同一个人的纵向变化信号反而更强** —— 这是 n=1 纵向设计的统计学依据，不是退而求其次。

#### 生态学谬误与它的反面 —— 「从一个人推出份额」踩的是哪一个

**Robinson, W.S.，*Ecological Correlations and the Behavior of Individuals*，*American Sociological Review* 15(3): 351–357，1950-06**，DOI 10.2307/2087176。PDF：https://www.stats.uwo.ca/faculty/aim/2015/9938/articles/Robinson1950AmericanSociologicalReview.pdf

他的定义（verbatim）："An individual correlation is a correlation in which the statistical object or thing described is **indivisible**." / "In an ecological correlation the statistical object is **a group of persons**."

他实际报出的数字（1930 年美国普查，10 岁以上人口）：

| 变量对 | 个体层面 | 生态层面（9 大普查区） | 生态层面（48 州） |
|---|---|---|---|
| 肤色 × 文盲 | .203 | .946 | .773 |
| **出生地（外国出生）× 文盲** | **+.118** | **−.619** | **−.526** |

⚠️ 第二行是核心：**个体层面为正 .118，生态层面为负 −.619，符号完全反转。**

他的结论句极短（verbatim）："…whether ecological correlations can validly be used as substitutes for individual correlations. **They cannot.**"

⚠️ **"ecological fallacy" 这个词组是否由 Selvin (1958) 首创 —— 查不到**（原文未取得）。**Robinson 本人从未使用过这个词组。**

**反方向（个体 → 群体）叫原子论谬误 / 个体论谬误**，最直白可引的定义来自：**Dohoo, Martin & Stryhn，*Veterinary Epidemiologic Research*, 2nd ed., Ch. 29 §29.7.2**，全书免费 PDF：http://projects.upei.ca/ver/files/2022/08/VER_ch29.pdf （⚠️ **第二版出版年份查不到**，官网只写 "Third printing of the Second Edition"）

逐字："the **atomistic fallacy** (**using data from lower levels to make inferences about higher levels**)"

同处还有一句很有价值的判断（verbatim）："it is likely that the atomistic fallacy… is **undoubtedly the more common of the 2 errors**." / "**little is written about this fallacy**."

佐证（摘要句已核，全文付费墙）：**Subramanian, Jones, Kaddour, Krieger，*Revisiting Robinson: The perils of individualistic and ecologic fallacy*，*IJE* 38(2): 342–360，2009-01-28**，DOI 10.1093/ije/dyn359 —— "the implication is that perils are posed by not only ecological fallacy but also **individualistic fallacy**." / "**Multilevel thinking… is thus a necessity, not an option.**"

**逻辑学版本**：Dowden, B.，*Fallacies*，*Internet Encyclopedia of Philosophy*，ISSN 2161-0002，https://iep.utm.edu/fallacy/ （⚠️ 页面未标最后更新日期 —— 查不到；访问日期 2026-08-20）
- **Composition（合成谬误）** —— **这正是本项目的靶心**："The Composition Fallacy occurs when someone mistakenly assumes that a characteristic of some or all the individuals in a group is also a characteristic of the group itself."
- **Division（分割谬误）**："Merely because a group as a whole has a characteristic, it often doesn't follow that individuals in the group have that characteristic." 原文点明二者互为逆命题。

#### Simpson 悖论 —— 纵向自我度量最现实的失败模式

**Simpson, E.H.，*The Interpretation of Interaction in Contingency Tables*，*JRSS Series B* 13(2): 238–241，1951-07-01**，DOI 10.1111/j.2517-6161.1951.tb00088.x（前身：Pearson, Lee & Bramley-Moore 1899；Yule 1903）

现代权威定义：**Sprenger & Weinberger，*Simpson's Paradox*，*Stanford Encyclopedia of Philosophy*，首发 2021-03-24，实质修订 2026-06-06**，https://plato.stanford.edu/entries/paradox-simpson/

逐字："an association between two variables in a population **emerges, disappears or reverses** when the population is divided into subpopulations."

因果视角：Pearl, J.，*Comment: Understanding Simpson's Paradox*，*The American Statistician* **68(1): 8–13**，2014-01-02，DOI 10.1080/00031305.2014.876829

> **对本项目的意义（我的推断）**：把一个人在异质任务集合上的记录汇总成一个百分比，等于做了一次聚合。Simpson 悖论说明这次聚合可以让方向反转 —— 只要子集权重（任务类型、项目阶段、周次）在时间上漂移，**总体占比的变化方向可以与每一个子集内部的变化方向相反**。
> **在本机这个风险是具体的、已经存在的**：2026-08-17 单日 518 场扇出、2026-08-15~17 的 `kmvideo_work` 762 场 —— 这些脉冲会在几天之内彻底改写周级占比的构成权重。**不分层，8 月的「自动化率上升」可能只是那三天的图片标注批次。**

#### 四个方向的对照表

| 谬误 | 从 → 到 | 在本项目里长什么样 |
|---|---|---|
| **生态学谬误**（Robinson 1950） | 群体 → 个体 | 拿 AEI 的 45%/52% 说「我应该是这个数」 |
| **原子论 / 个体论谬误**（VER §29.7.2；Subramanian 2009） | **个体 → 群体** | **拿我一个人的 X% 说「开发者的 X%」← 本项目的风险点** |
| 合成谬误（IEP） | 成员 → 整体 | 同上，逻辑学版本 |
| 分割谬误（IEP） | 整体 → 成员 | 生态学谬误的逻辑学版本 |
| **Simpson 悖论**（Simpson 1951） | 聚合 ↔ 分层，方向可反转 | 总占比在涨，但每类任务内部都在跌 |

#### 结论：单人算出来的「X% 自动化」到底能不能说

⚠️ **先说边界：没有任何一篇文献直接讨论过「automation vs augmentation 任务占比」这个具体指标的效度 —— 查不到。** 下表是我基于上述来源做的推断，不是任一来源的原话。

| 陈述 | 效度 | 依据 |
|---|---|---|
| 「**在这段时间窗内、按这套编码规则，我自己记录到的任务中有 X% 属于自动化**」 | ✅ **成立** —— 这是**描述统计**，对象就是那份日志本身 | 无需推断性假设 |
| 「**开发者的任务中有 X% 是自动化**」 | ❌ **不成立** —— 这是总体参数估计，n=1 且非随机抽样 | Fisher 2018 的遍历性条件；WWC 的 ≥20 cases；合成谬误 / 原子论谬误 |
| 「**我的 X% 从 A 变到 B，且这个变化由某个干预造成**」 | ⚠️ **需要设计支撑**：SCED 要求至少 3 次不同时点的效果论证；ITS 要求明确中断点 + 前后各 ≥3 点 + 自相关处理；**且无对照单元时无法排除并发事件** | WWC v5.0；EPOC 2021；Bernal 2017 |

**还有一个分母问题**（我的推断，但有 SPACE 原文背书）：占比的分子分母都来自日志，而 SPACE 原文已说 "it is almost impossible to comprehensively measure and quantify all the facets of developer activity"。**分母本身不完整且系统性偏斜**（思考、看文档、线下决策、跟人讨论全部不进日志），因此这个百分比连「对这份日志的描述」之外的任何解释都不安全。

---

## 5. 给单人 / 单时间线数据的替代方案

### 5.1 先划出「伪科学区」：这些指标在单人数据上无论怎么做都不成立

| 指标 | 为什么在单人数据上是伪科学 | 处理方式 |
|---|---|---|
| **职业任务覆盖率**（"36% 的职业用 AI 做了 ≥25% 的任务"） | 分母是「某职业在 O*NET 里的全部任务」，是**跨人构造出来的总体**。一个人不构成一个职业。若硬算，分母只能是「我给自己列的任务清单」，而那份清单本身是由做过的事倒推出来的 —— **分母由分子决定，指标恒真**。（此处「若硬算」是假设情形，本机目前没有这个指标） | **删除，不替代。** 换成「主题集中度」（§5.6） |
| **工资分布 inverted-U / task value（$47.90）** | 需要一个跨职业的工资分布。单人只有一个工资点，画不出分布，也算不出「峰在上四分位」。 | **删除。** 若 owner 坚持要钱的维度，只能显式声明一个假设时薪，并标成假设 |
| **劳动生产率增长 pp（1.8 → 1.0–1.2）** | AEI 的算法是 Hulten 定理：任务级时间节省对数差 × O*NET 任务时间权重 × **工资份额**加权求和。单人三个输入全缺（无工资份额、无任务时间权重、无可信的反事实耗时）。 | **删除。** |
| **AUI / Gini（跨国、跨州不平等）** | 这两个量测的是**人与人之间**的不平等。单人无跨人分布。 | 数学对象可复用但**必须改名改叙事**，见 §5.4 |
| **「你今年省了 41.95 小时」** | 现有实现 B 的算法是 `候选数 × 假设小时数`，其中小时数（2.0 / 1.2 / 1.5 / 0.75）没有任何观测支撑。而 METR 证明：即便让当事人**亲自估**，误差也有 **+40pp 的系统性高估**（https://metr.org/blog/2026-05-11-ai-usage-survey/ ，2026-05-11）。用常数假设算出来的数只会更差。 | **降级为「可调假设下的排序工具」**，见 §5.7 |
| **automation_ratio = 0.7273** | 分子分母共 11 个样本，却输出到小数点后 4 位。精度冒充了确定性。 | 小样本一律不出小数，出区间或出「样本不足」 |

> ✅ **有一件事现有实现已经做对，必须保留**：`analytics.py:109-158` 的「同口径比较门」—— 口径不一致或基准样本 < 30 时拒绝生成全球百分位，只给方向参考。**这正是应对上面这类问题的正确姿态，应该把它从「百分位」一处扩展到所有指标。**

### 5.2 第一优先：把「人」和「机器」拆成两个总体（对应 AEI 的 Claude.ai vs 1P API）

AEI 从 v3（2025-09-15）起就把消费者对话和 1P API 分开报，因为两者的 automation 率差得离谱：**Claude.ai 49.1% vs API 77%**（https://www.anthropic.com/research/economic-index-geography ）。混在一起的比值没有任何含义。

本机的对应切分（判定规则已实测可用，来自 `agent-session-data-is-mostly-machine.md`，2026-08-20）：

| 总体 | 判定规则（确定性，零模型调用） | 规模 |
|---|---|---|
| **H（人在对话）** | 其余 | 952 / 2,826 |
| **F（agent 扇出）** | 同一 source 同一小时内启动 ≥15 场 | 1,485 |
| **B（批处理）** | 无用户发言／单轮机器指令／同一段提示词前 80 字重复 ≥5 次 | 389 |

**这个替代是诚实的，因为**：它没有假装单人数据能回答跨人问题，而是承认这份数据里本来就有两个不同性质的总体（人的决策流 vs 机器的执行流），并且这两个总体各自内部有足够样本做统计。**H 组回答「这个人怎么工作」，F+B 组回答「这套系统怎么跑」——这是两个不同的产品价值，混起来两个都答不了。**

**并且这条能直接修掉现有的两处假数据**：
- `agent_brief.json` 的 `repeats` 里排第一的「被问过 738 次」，实际是 **1 天内的一次图片标注扇出**，不是人问了 738 次。同理第 2 名 340 次（讲义生成）、第 4 名 297 次（评委打分）都是批处理。**现在这份「最该固化的重复问题」榜单，前 6 名里至少 5 名是机器批次。**
- `expensive_sessions` 第一名 `2026-07-29 KMOS 5 turns 2,550,035,331 tok` —— 25 亿 token。这是 codex 的 `input_tokens` **含缓存命中**、claude-code **不含**，两者直接相加造成的（同一份 memory 记录已实测）。

### 5.3 用 AEI v2 的「自底向上」路线替代 O*NET

AEI 自己在 v2（2025-03-27）就补了这条路：不再只做 O*NET 自顶向下匹配，而是**释放 630 个自底向上聚类出来的细粒度使用簇**。理由正是 O*NET 的静态与美国中心（v1 §4.1 limitations 逐字：cannot capture "emerging tasks and occupations that AI systems may create"，且是 "U.S.-centric classification system"）。

**替代方案**：建两层本地分类法
- **L1（6–8 类，固定）**：可以沿用现有 `ACTIVITIES` 的骨架，但**必须改掉 first-match-wins 的关键词规则**（§3.2 B2）
- **L2（自底向上，数量不固定）**：从会话首句聚类，用 memory 里已验证的方法 —— **IDF × log(1+次数) 自动降权**，不要手调词表（手调那版让「业务方案」吞掉 1055/1752 场，已实测）

**这个替代是诚实的，因为**：它复制的是 AEI 自己承认更可靠的那条路径（自底向上），而不是把一个为美国劳动力市场设计的静态职业库硬套到一个人的 git 仓上。

### 5.4 AUI / Gini 的诚实改写：从「跨人不平等」改成「跨项目注意力集中度」

AUI 定义（AEI v3 逐字）：normalizing each country's share of Claude.ai use by its share of the world's working population。

**结构是「实际份额 ÷ 应得份额」。** 单人没有「人口」这个应得份额基准，但有一个**同样是外生的**基准：**项目的代码量 / 文件数 / commit 数**。

替代指标：**项目注意力偏离度 = 该项目会话份额 ÷ 该项目代码份额**。>1 = 这个仓吃掉的注意力超过它的体量。

**为什么诚实**：分母（代码份额）不是从会话数据里推出来的，是独立可测的外生量，所以这个比值不会自证。**为什么仍会骗人**：新建仓代码少但必须投入大量注意力，恒 >1，看起来像「浪费」；必须按仓龄分层看。

Gini 同理可保留，但叙事必须从「不平等」改成「集中度」，并且明确写「这不是 AEI 的 Gini，AEI 的 Gini 测的是人与人之间」。

### 5.5 automation / augmentation 的诚实重做：不猜意图，只数干预点

AEI 的五模式定义（v1 Table 1，逐字）：
- automative = **Directive**（"Complete task delegation with minimal interaction"）+ **Feedback Loop**（"Task completion guided by environmental feedback"）
- augmentative = **Task Iteration**（"Collaborative refinement process"）+ **Learning**（"Knowledge acquisition and understanding"）+ **Validation**（"Work verification and improvement"）

**关键洞察：这五个词描述的全是「人类介入的位置和次数」，不是「内容主题」。** 而 agent 会话恰恰把人类介入点记录得比 AEI 更清楚 —— AEI 只能让模型猜，本机可以直接数。

替代口径（全部来自 `ALLOWED_SESSION_FIELDS`，已存在）：

| AEI 模式 | 本机可观测判据 |
|---|---|
| Directive | `user_message_count == 1` 且 `abort_count == 0` 且会话在助手轮结束 |
| Feedback Loop | `user_message_count == 1` 但 `error_event_count > 0` 且 `tool_call_count` 高（人只发了一次，环境在给反馈） |
| Task Iteration | `user_message_count >= 3` 且用户轮均匀分布在会话时间轴上 |
| Validation | 最后一轮是用户轮，且该会话之后没有同题复问 |
| Learning | 会话内 `tool_call_count == 0` 或极低、以问答为主 |

**为什么诚实**：判据全部是计数，不是语义猜测；可以人工抽样验证（AEI 自己就做了 150 条人工核对，automation/augmentation 标签一致率 **90.7%**）。
**为什么仍会骗人**：① fan-out 会话恒为 Directive，所以**必须先做 §5.2 的总体拆分**，否则这个比值只是在测「你今天跑了多少批处理」；② 一个人开着 agent 去干别的事、回来才看结果，会被判成 Directive，但其实是并行工作流 —— METR 在 2026-02-24 承认这正是他们的测量盲区（"would often work an unrelated task while waiting for the agent"）。

### 5.6 「覆盖率」的诚实替代

AEI 原文**没有 "effective coverage" 这个术语（查不到）**。它有的是：(a) per-occupation task coverage；(b) 隐私下限 ≥15 对话 且 ≥5 账号，低于门槛的任务**直接剔除**。

单人替代 —— 拆成三个各自可证伪的量，**不要合成一个「覆盖率」**：

1. **可判定率（decidable rate）** = 能给出非 unknown 标签的会话数 ÷ 总会话数。当前实测 automation/augmentation 维度的可判定率是 **8.78%**（28,149 / 320,539），活动维度是 **60.71%**。**这个数必须放在一级位置**，因为它决定了下面所有 share 的可信度。
2. **有效样本门槛** = 任何 L2 主题簇少于 N 场会话就不单独展示（对应 AEI 的 ≥15）。5 个账号那条对单人恒为 1，直接删。
3. **主题集中度** = top-N 主题占比（对应 AEI 的 top 10 任务占 24% → 19%）。这个可以直接对标，因为它不需要跨人分母。

**为什么诚实**：把「没测出来」和「测出来是第三类」彻底分开。现在的 `mixed_or_unknown 91.22%` 就是这两者被混成一个数的后果。

### 5.7 「省了多少时间」的唯一诚实做法：不报绝对值，报同类任务的时间序列

三条依据：
- METR 实测：当事人对自身省时的估计有 **+40pp 系统性高估**（2026-05-11）
- METR 实测：但当事人的**相对排序**是准的（预测 vs 实际 Pearson r = 0.64 / 0.59），且在自己预测「会大幅加速」的任务上实测确实不减速（Figure 18）
- AEI 自己：把 raw speedup 乘上 task success 后生产率估计**腰斩**（1.8 → 1.0–1.2pp，2026-01-15）

**替代做法**：
- 删掉「省了 41.95 小时」这种绝对值
- 改成**同类任务的耗时/轮次/重试次数随时间的变化**（同一 L2 主题簇内比较，自己跟自己比）
- 任何绝对小时数一律标成「假设参数」，并暴露在 what-if 里（`build_memory_atlas_formula_what_if.py` 方向已对）

**为什么诚实**：它只做 METR 证明可信的那件事（排序与趋势），不做 METR 证明不可信的那件事（幅度）。
**什么情况下它仍会骗人**：任务难度随时间漂移。今年的任务本来就更难，耗时上升不代表 AI 变差了。缓解办法是在同一 L2 簇内比，并公示每簇的样本数。

---

## 6. 我认为最值得加的 5 个新指标（按优先级排序）

排序依据：**没有 #1，#2~#5 全都不可信**；#2 是 AEI 最新一版最看重的维度（AI Autonomy）在本机唯一诚实的实现；#3 是唯一能防住「活动量假象」的结构；#4 和 #5 是把 owner 已经在感受、但目前没有数字的两件事变成数字。

---

### 【1】可判定率 + 人工抽检一致率（Decidable Rate & Inter-rater Agreement）

**它回答什么问题**：「你下面给我看的这些百分比，有多少比例的数据是真的被判定过的？」
这是**一个 A/B 决定**：是「相信这版分布，据此调整工作方式」还是「先去修分类器，别看分布」。

**数据够不够**：够，现在就能算。当前实测：
- automation/augmentation 维度可判定率 = **8.78%**（28,149 / 320,539）
- activity 维度可判定率 = **60.71%**（1 − 39.29% unknown）

**怎么算**
```
可判定率(维度 d) = 该维度非 unknown 标签的单位数 ÷ 总单位数
一致率(维度 d)   = 人工复核样本中与机器标签一致的条数 ÷ 复核条数
```
- 分母的「单位」必须先按 §0.3 从「文件行」改成「会话」
- 人工复核照抄 AEI 的规模即可：**150 条**（AEI v1 就是 150 条，报出顶层 95.3% / 中层 91.3% / 底层 86%，automation/augmentation 标签 90.7%）
- 展示规则：可判定率 < 50% 时，**该维度的所有 share 一律不出数字，只出「样本不足」**

**什么情况下它会骗人**
1. **最危险的一种**：为了把可判定率做高而放宽分类规则 —— 可判定率涨了，准确率跌了，指标反向。**所以这两个数必须成对出现，单独报可判定率就是给自己开后门。**
2. 分母选择会作弊：只统计「有内容的会话」而不是全部会话，可判定率会虚高。分母必须是**全部纳入分析的会话**。
3. 一致率的复核样本如果从「机器判定成功的那部分」里抽，是有偏的；必须从**全体**里随机抽，包括 unknown。

---

### 【2】人类介入密度（Human Intervention Density）—— AI Autonomy 的诚实本地版

**它回答什么问题**：「我现在到底还在哪些环节做决定？哪些环节我已经完全放手了？」
**A/B 决定**：是「该在某类任务上收回控制权（因为放手的地方正在出错）」还是「该在某类任务上进一步放手（因为我介入了但没改变结果）」。

**数据够不够**：够。所需字段全部在 `ALLOWED_SESSION_FIELDS` 里已存在：`user_message_count`、`assistant_message_count`、`tool_call_count`、`abort_count`、`error_event_count`、`started_at`、`updated_at`。

**怎么算**
```
介入密度 = user_message_count ÷ (assistant_message_count + tool_call_count)
介入位置 = 用户轮在会话时间轴上的分位数序列（是集中在开头，还是散布全程）
```
映射回 AEI 的五模式（判据见 §5.5）：Directive / Feedback Loop / Task Iteration / Validation / Learning。
**必须按 §5.2 的三个总体（H 人 / F 扇出 / B 批处理）分别报，绝不合并。**

对标：AEI v4（2026-01-15）的 AI Autonomy 是 **1–5 分**，且明确说明它与 directive 不同（翻译任务是 directive 但 autonomy 低）；AEI v6（2026-06-26）报告 **Claude Code 的平均 autonomy 比 chat/Cowork 高 0.37 分**。

**什么情况下它会骗人**
1. **并行工作流会被误判成「完全委托」** —— 人开着 agent 去干别的事、回来才看结果，`user_message_count` 很低但人其实一直在做判断。METR 在 2026-02-24 明确承认这是他们自己的测量盲区（"would often work an unrelated task while waiting for the agent"）。**缓解**：结合会话之间的间隔时间与同期其它会话，标出「并行嫌疑」。
2. **fan-out 会把介入密度压到接近 0** —— 不先做总体拆分，这个指标就退化成「你今天跑了多少批处理」。
3. **「一次说清楚」和「懒得管」在计数上完全一样** —— 一个精心写好的长 prompt 只算一次介入，一个随手扔过去的也算一次。**缓解**：把首轮 prompt 长度作为副指标一起看，但不要合成进主指标。

---

### 【3】下游收敛率（Downstream Convergence）—— 防「活动量假象」的唯一结构

**它回答什么问题**：「多出来的动作，有多少真的变成了交付？」
**A/B 决定**：是「继续加大 AI 用量」还是「先去修从产出到交付之间那一段」。

**依据**：NBER WP 35275（Demirer, Musolff & Yang，2026-05，https://www.nber.org/papers/w35275 ）实测的层级衰减 —— 累积 commit 效应 autonomous agents **+180%**，衰减到**项目层 +50%**、**发布层 +30%**。Faros AI 的遥测同向：合并 PR **+98%** 但 PR 体积 **+154%**、评审时间 **+91%**，结论逐字 "Developers are completing a lot more tasks with AI, but organizations aren't delivering any faster"。

**数据够不够**：**部分够，需要接一条线**。会话层与产出层现在就有（Write/Edit 工具调用、落盘路径）；**交付层需要接 git**（本机全部仓都在本地，可读 commit / merge / tag）。这是五个指标里唯一需要新接数据源的。

**怎么算**（三层比值，每层都报绝对值，不要只报比值）
```
L1 会话数   → L2 产生了文件变更的会话数   → L3 变更进入 main / 打了 tag / 上了线的会话数
收敛率 = L3 ÷ L1        产出率 = L2 ÷ L1        交付率 = L3 ÷ L2
```

**什么情况下它会骗人**
1. **单人仓没有评审关卡** —— 「进 main」是自己推的，门槛几乎为零，L3 会虚高。**缓解**：最后一层用「部署/发布/打 tag」而不是「commit 到 main」。本机已有 `deploy-registry-governance` 的登记机制可以当 L3 的权威来源。
2. **调研型会话天然不产出文件**，会被算成「不收敛」。**缓解**：按 L2 主题簇分层看，不要给全局一个数。
3. **一次大重构会让某周的 L3 暴涨** —— 比值对小分母极其敏感。**缓解**：报滚动 4 周窗口，且窗口内 L1 < 20 时不出数。

---

### 【4】复发成本（Recurrence Cost）—— 同一个问题烧了几次

**它回答什么问题**：「哪些问题我一直在重新问？每次重问烧掉多少？」
**A/B 决定**：是「把这条写进 AGENTS.md / 固化成 skill」还是「不值得，它只是偶发」。

**数据够不够**：**够，但现在这版被 fan-out 污染了，必须先修。** `agent_brief.json` 的 `repeats` 已经在算这件事（判重规则：每场会话第一句的前 26 个字），但当前榜单前 6 名里至少 5 名是机器批次而不是人的重复提问：

| 现榜位 | 「被问过」次数 | 天数 | 真相 |
|---|---|---|---|
| 1 | 738 次 | **1 天** | 一次图片标注扇出 |
| 2 | 340 次 | 4 天 | 讲义生成批处理 |
| 3 | 321 次 | **1 天** | 评分标准拆分批处理 |
| 4 | 297 次 | 2 天 | 评委打分批处理 |
| 5 | 161 次 | **1 天** | 角色扮演批处理 |

**怎么算**（修正版）
```
1. 先剔除 F（扇出）与 B（批处理）总体
2. 在 H 总体内按首句前 N 字判重（N 需要调优，26 太短）
3. 复发成本 = 重复次数 × 每次的实际 token（token 必须先修口径，见下）
4. 只保留「跨天数 ≥ 3」的簇 —— 同一天内的重复是一次工作，不是复发
```

**什么情况下它会骗人**
1. **前 26 字判重会误合并**：所有以「你是一位…」开头的 prompt 会被判成同一个问题。**且它会漏掉换了说法的同一个问题** —— 这个方向的漏报无法通过调 N 修复。
2. **token 口径现在是坏的**：codex 的 `input_tokens` **含**缓存命中，claude-code 的**不含**（缓存单列 `cache_read_input_tokens`），直接相加会把单场抬到 24 亿 —— `expensive_sessions` 榜首那条 `2026-07-29 KMOS 5 turns 2,550,035,331 tok` 就是这个 bug 的产物。**不修口径，「烧了多少」这个数就是假的。**
3. **「重复」不一定是浪费**：同一个问题在不同项目里问是合理的迁移。必须把 `projects` 字段带上，跨项目的重复和同项目内的重复要分开看。

---

### 【5】两周反悔率（Two-Week Reversal）—— GitClear churn 的本地版

**它回答什么问题**：「AI 帮我写的东西，两周内被我自己推翻了多少？」
**A/B 决定**：是「这类任务可以放手交给 agent」还是「这类任务的产出留不住，得改工作方式」。

**依据**：GitClear 定义逐字 —— "**Code churn** -- the percentage of lines that are reverted or updated **less than two weeks** after being authored"（https://www.gitclear.com/coding_on_copilot_data_shows_ais_downward_pressure_on_code_quality ，确切发布日期查不到）。2026 版（https://www.gitclear.com/the_ai_code_quality_maintainability_gap ，2026-01，6.23 亿次变更）实测 two-week churn **+15%**、block duplication **+81%**、moved code 从 21%(2022) 降到 3.8%(2026 YTD)。

**数据够不够**：**需要接 git（同 #3）**，但接上之后完全够 —— 本机所有仓都在本地，有完整 commit 历史。

**怎么算**
```
两周反悔率 = (某会话产出的行数中，14 天内被再次修改或删除的行数) ÷ (该会话产出的总行数)
按 L2 主题簇 与 §5.5 的协作模式 分别报
```

**什么情况下它会骗人**（这是五个里最容易骗人的一个，必须写清楚）
1. **没有「非 AI 基线」可比了。** GitClear 能说「+15%」是因为它有 2020–2022 的前 AI 数据。本机的会话数据起点就已经是 AI 时代，**算出来的绝对值没有参照系**。METR 在 2026-02-24 遇到的正是同一个问题：现在已经招不到愿意不用 AI 工作的开发者了（"**30% to 50%** of developers told us that they were choosing not to submit some tasks because they did not want to do them without AI"）。**结论：这个指标只能自己跟自己的过去比趋势，绝不能报绝对水平。**
2. **活跃开发本来就会改代码。** 一个正在快速迭代的模块，两周反悔率天然高，这是健康的。**缓解**：必须按模块成熟度分层，或者只在同一模块内看时间趋势。
3. **「反悔」和「迭代」在 git 上长得一样。** 无法从 diff 区分「这段是错的，删掉」和「这段是对的，继续演进」。**这是这个指标的硬边界，不要假装能区分。**

---

### ⚠️ 这 5 个指标仍然满足不了 SPACE 的一条规则 —— 必须在 PRD 里正面处理

SPACE 原文要求「**at least one of the metrics include perceptual measures such as survey data**」（§4.4 规则 2）。

上面 5 个指标**全部是行为/遥测指标，一个感知类指标都没有**。而 Beller 2021 实测：纯遥测只解释自评生产力方差的 7–9%，**剩下 90% 以上遥测碰不到**。

**这里有一个和项目铁律的真实冲突**：本仓有「运行期禁调模型、数据靠派生」的零 Agent 零 Token 规则，而感知类数据无法从日志派生 —— 它只能由 owner 自己录入。

**两个可行选项，需要 owner 拍板（这是一个真正的 A/B）**：
- **A**：加一个极轻的每日/每周自评（一个 1–5 分的滑块 + 一句话），录入即入库，不调任何模型，不违反铁律。**代价**：需要 owner 每天花 10 秒。
- **B**：不加，并在产品里**明确写出**「本工具只覆盖 SPACE 的 Activity 与 Performance 两维，不构成生产力测量」。**代价**：叙事必须一路降级，不能说「生产力」三个字。

**推断（我的）**：B 是诚实的，A 是完整的。**但绝不能既不加感知指标、又继续用「生产力」这个词** —— 那就是 §0.2 那类假数据的另一种形态。

### 落选但值得提一句的两个

- **项目注意力偏离度**（§5.4，AUI 的本地改写）：结构漂亮，但新建仓恒 >1，需要按仓龄分层才不误导，实现成本高于收益。
- **单位交付成本（token / 交付）**：只要 #3 和 token 口径修好，这个就是白捡的；但它依赖前两者，不能独立上线。

### 已经有引擎但从没喂过数据的两处（不是新指标，是接线）

| 位置 | 现状 | 说明 |
|---|---|---|
| `verified_outcome_rate` | **0.0 / 320,539，state = MEASURED** | 从没有任何 evidence adapter 写过验证信封。**建议改成 `state = NOT_WIRED`，不要显示 0.0%** |
| `failure_compound` | `incident_count / historical_recurrences / blocked_recurrences / nonrecurrence_ratio` **全部为 0** | `failure_compound.py:426-464` 的 `nonrecurrence_ratio` 与复合分公式已实现，只是没有数据源 |

**推断（我的）**：Memory Atlas 现在有三个「经济」面板，其中两个显示的是结构性零。**这可能正是 owner 说「还是不够」的一部分原因 —— 不是指标设计得不够多，而是已有的指标里有一半是空的，剩下一半的分母是错的。**

---

## 7. 交付边界与自检

### 本轮做了什么 / 没做什么

- ✅ 只调研、只产出这一份文档。**没有写任何实现代码，没有修改项目里任何文件。**
- ✅ 真读了代码再写差距表：`memory_atlas_private/analytics.py`（202 行）、`normalization.py`（184 行）、`build_memory_atlas_economic_proxy.py`（449 行）、`models.py`、`codex_activity_adapter.py`、`BehaviorEconomyView.tsx`、`features/v31/contracts.ts`，以及线上产出 `memory-atlas/analytics/latest.json` 与 `personal_economic_proxy.json` 的实际数值。
- ❌ **没有**验证 `memoryatlas.linzezhang.com` 线上页面当前展示的是哪一版数据（本轮只读本机文件）。

### 关于「查不到」的完整清单

| 项 | 状态 |
|---|---|
| `atlas/build/aei.py`（任务给的路径） | **本机不存在**（全盘 find 无结果） |
| AEI 的 "effective coverage / 有效覆盖率" 术语 | **AEI 原文没有这个词**。最接近的是 ≥15 对话 / ≥5 账号的隐私下限 |
| AEI 如何推断国家/美国州（IP？账号元数据？） | 报告页与 arXiv abs 页**都未公开说明** |
| AUI 的精确计算公式 | 报告只给文字描述（"normalizing each country's share... by its share of the world's working population"），**未给公式** |
| AEI v6 是否推翻过往结论 | **未找到明确的推翻表述** |
| 2026 版 DORA《State of AI-assisted Software Development》 | **不存在**（`dora.dev/research/2026/` 为 404，截至 2026-08-20） |
| DORA 2024 报告的当年样本量 N | PDF 文本层取不出；二手引的 39,000+ 是**项目累计数**，不可当年用 |
| DORA AI Capabilities Model 每项能力的点估计效应量 | 报告只给「Small/Medium/Large」定性网格 |
| DORA ROI 报告（v.2026.1）的一手 PDF 直链 | 需填表下载；文中数字仅来自 InfoQ / Kodus 二手复述 |
| METR 19% 减速在**论文正文**里的数值 CI | 正文未印，只在 Figure 1 里；数值 CI 来自其 GitHub 仓的 `regression.py` 输出与 2026 年博客 |
| METR RCT 的同行评审接收记录 | **查不到**（仅预印本，arXiv:2507.09089） |
| 对 METR RCT 协议的独立直接复制 | **查不到** |
| Cui et al. 的 NBER working paper 编号 | **不存在**（该文有 AEA 注册号 AEARCTR-0014530，但无 NBER WP 号） |
| Ziegler et al. (2022) 的受访开发者人数 | **查不到** |
| GitClear《Coding on Copilot》的确切发布日期 | 页面未标 |
| Uplevel 研究的原始发布日期 | 页面现显示 2026-07-21（疑为重发），最早报道见 2024-09-17 |
| Goodhart 1975 原书的确切字面措辞 | 流通有两版（"collapse once pressure is placed" vs "break down when pressure is applied"），**原书未取得，无法裁定**；引用时应写「as commonly quoted」 |
| "ecological fallacy" 是否由 Selvin (1958) 首创 | 原文未取得，**查不到**。可确认的是 **Robinson 本人从未用过这个词组** |
| CENT 2015（BMJ 350:h1738）的正文条目内容 | 书目已核，全文 403 |
| Diez-Roux 1998 / 2002 中 atomistic fallacy 的逐字定义 | 全文被拦截；已改用 VER Ch.29 §29.7.2 的定义替代 |
| Alker (1969)、Riley (1963) 原文 | 无电子版 |
| Barlow, Nock & Hersen《Single Case Experimental Designs》的版次/年份 | 未取得出版商页面 |
| AHRQ《Design and Implementation of N-of-1 Trials》(Kravitz & Duan, 2014) 的可访问链接 | 405 / 未命中 |
| VER 第二版的出版年份 | 官网只写 "Third printing of the Second Edition"，未标年份 |
| 针对「**session / 会话计数**」作为生产力代理的同行评审批评 | **不存在** —— commits / LOC / PR 都有，session 没有。**这意味着「用会话数当产出量」是一个未被验证过的构念**（按 Kaner & Bond 2004 的标准，未验证的构念不能直接使用） |
| 任何直接讨论「automation vs augmentation **任务占比**」这一具体指标效度的文献 | **不存在** |
| ITS 的「2018 年 corrigendum」 | **不存在** —— 勘误是 2020 年的（*IJE* 50(3):1045）；2018 年那篇是独立正文（*IJE* 47(6):2082–2093），立场是**加对照** |
| SPACE / DevEx 的 ACM Queue 与 dl.acm.org 原始页面 | 对本环境一律 403；已改用 CACM 重印版与作者自存 PDF 取得逐字原文 |

### 三条必须防的二手信息污染（调研中实际遇到的）

1. **「METR 承认方法论存在致命缺陷 / 撤回了结论」** —— 逐字核验 https://metr.org/blog/2026-02-24-uplift-update/ 全文，**这两句话不存在**。METR 只是识别出选择效应并改设计，且倾向判断是 AI 的加速效果在 2026 年**已经上升**。
2. **「DORA 2025：95% 的开发者使用 AI」** —— DORA 一手 PDF 是 **90%**。95% 来自 Faros 的二手复述，它把 DORA 问卷数据和 Faros 自家遥测混在了一起。
3. **把 DORA 2024 的 −1.5% / −7.2% 和 DORA 2025 的效应量放进同一张表** —— 2024 是「采纳度 +25% → 百分比变化」，2025 是「采纳度 +1 个标准差 → 标准化 β + 89% 可信区间」。**口径变了，数值不可比。**

另有两处**发布方自己的数字不一致**，引用时需注明：
- METR 2026-02-24 文中写 "a 20% slowdown"，而 2025 论文摘要是 "increases completion time by **19%**"
- Cui et al. 引用 Peng et al. 时写 "58% decrease"，而 Peng et al. 原文是 **55.8%**

### 我的推断与原文的分界（本文所有标了「推断」的地方）

本文所有以「**推断（我的）**」「**推断（调研 agent 的）**」开头的段落，都是从原文事实出发的判断，**不是任何来源的原话**。主要有：

1. `atlas/build/aei.py` 可能是 PRD 的目标路径而非已有文件
2. owner 说「还是不够」很可能与 `mixed_or_unknown 91.22%` 和两个结构性零直接相关
3. 「automation/augmentation 比值 16 个月翻两次方向 → 不适合做单点展示」
4. DORA 的「AI 采纳度」内含态度成分，相关里有同源自陈方差
5. 「数字随任务真实度单调下降」这条主线，以及「Memory Atlas 测的是最真实的一端，所以没有资格引用 55% 那类数字」
6. METR Figure 15 的两阶段 bootstrap 区间跨零（读图所得，METR 未以文字陈述）
7. §6 里每个指标的「什么情况下它会骗人」
8. §4.4 里「Memory Atlas 逐条不满足 SPACE 四条规则」的对照表 —— SPACE 原文只给规则，没点评任何具体产品
9. 「正确叙事是我和我的过去比，不是我和世界比」—— 由 Fisher 2018 的遍历性条件 + Beller 2021 的 R² 分层推出，两篇都没有讲这句话
10. §4.4 末尾那张「X% 三种说法的效度」对照表 —— **没有任何文献直接讨论过 automation/augmentation 占比这个指标**，该表完全是我基于遍历性、SCED 门槛、聚合谬误三条推出的
11. 「Simpson 悖论风险在本机是具体的」—— 由 2026-08-17 单日 518 场扇出与 `kmvideo_work` 三天 762 场这两个实测脉冲推出

### 关于「二手来源」的标注纪律

本文对来源做了三级区分，引用时请保持：
- **一手逐字**：CACM 重印版 SPACE / DevEx、Strathern 1997 PDF、Robinson 1950 PDF、WWC v5.0、EPOC 2021、Fisher 2018、Beller 2021、METR 论文与博客、DORA 一手 PDF、Peng et al. 与 Cui et al. 的 PDF、AEI 各报告页与 arXiv
- **二手，已标注**：Swarmia 的 SPACE 转述（已被一手取代，保留仅作对照）、DX 博客、InfoQ / Kodus 对 DORA ROI 报告的复述、Faros 对 DORA 2025 的复述（且其 95% 与一手的 90% 冲突）
- **百科条目（最弱）**：Goodhart 定律的措辞归属、单被试设计与 n-of-1 的概览 —— 这两处后来都用一手文献（Strathern PDF、WWC v5.0、Lillie et al. 2011）补上了，百科仅作线索
