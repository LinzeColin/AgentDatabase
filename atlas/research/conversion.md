# 成果转化 / 变现路径调研

调研日期：2026-08-20
调研对象处境：3 个月 4802 场 agent 会话（984 场本人开口）、119 个有会话的日子里只有 38 天产生 git 提交、造:交:换钱 = 10:5:1、9 个仓 / 741 提交 / 300 PR / 45 Release / 一台 OVH 生产机 / Cloudflare Tunnel / 多个自建站点。核心痛点：**重度用 AI 三个月，没有创造出经济价值。**

先读了现有实现：
- `~/.memory-atlas/src/atlas/build/build.py` 的 `opportunity_block()`（第 562 行起）
- `~/.memory-atlas/src/atlas/build/compound.py`

（任务描述里给的路径 `AgentDatabase/atlas/build/` 不存在，实际在 `~/.memory-atlas/src/atlas/build/`。）

**读后结论先放这里，因为它影响下面所有判断**：`compound.py` 的漏斗设计（CAPTURED → QUALIFIED → EXPERIMENT → ADOPTED → OUTCOME → ECONOMIC_IMPACT，加 `_evidence_ceiling()` 强制只降不升）**比本次调研找到的大多数公开框架更严格** —— 它连"部署成功"都不算 OUTCOME，这正是 Melissa Perri 的 output/outcome 区分要表达的东西，而且它用代码执行而不是靠自觉。**缺的不是框架，是 `economic` 那一列的数据入口。** `NOT_MEASURED` 里自己写了"本机没有账单/发票/收款记录的接入口"—— 这句话就是全部问题的镜像：没有收款记录，是因为**还没有第一次收款**，不是因为没接口。

---

## 0. 阅读须知：怎么区分两类证据

本文所有数字分三档标注：

| 标记 | 含义 |
|---|---|
| **【有分母】** | 有明确样本量和方法，可以拿来算比例 |
| **【幸存者】** | 单个成功案例的自述，只能证明"这条路存在"，不能算概率 |
| **【二手/无法核实】** | 只查到转述、或来源无方法说明。写出来是因为它是我能找到的唯一线索，**不能当决策依据** |

**没有数字的路径我直接写「查不到数字」。**

---

## 1. 变现路径对照表

| 路径 | 真实规模数字 | 进入门槛 | 典型周期 | 已知失败率 | 出处 |
|---|---|---|---|---|---|
| **开源 → 个人赞助** | GitHub Sponsors 7 年累计 **$100M**，分给 **70,000+** maintainer/组织 → 人均终身 ≈ **$1,430**（约 $17/月）。个人赞助均值 **$8/月**，组织赞助约为个人的 **15 倍**【有分母】 | 极低（开个开关） | 核心项目也要数年 | 49,148 人的赞助图谱样本里，**只有 7,343 人在收钱**（15%），40,549 人在给钱，比例 5.5:1【有分母】 | [github.blog 2026-07-20](https://github.blog/open-source/maintainers/100-million-for-open-source-a-milestone-built-by-the-community/)；[arXiv 2604.03846](https://arxiv.org/html/2604.03846)（2026-03 采集） |
| **开源 → B2B 支持合同** | curl：wolfSSL 卖分层支持 **$2,000 / $6,000 / $23,000 / $50,000 每年**，用这笔钱发 Daniel Stenberg 全职工资（2019-02 起至今）【幸存者，但机制清晰】 | 中（要有法人/发票能力 + 一个客户） | 从 0 到第 1 个合同，取决于对话数不是流量 | 查不到分母 | [helpnetsecurity 2019-02-07](https://www.helpnetsecurity.com/2019/02/07/daniel-stemberg-joins-wolfssl/)；[wolfSSL curl 页](https://www.wolfssl.com/curl-roadmap-2026-with-daniel-stenberg/) |
| **开源 → 托管版 SaaS** | Plausible：2019-05 开卖 → **324 天**才到第一个 $400 MRR → 再 **9 个月**到 $10k MRR → 10 个月到 $500k ARR → 2022-06-02 越过 **$1M ARR（$83,637 MRR）**。4 人，零广告【幸存者，逐步公开】 | 高（要运维、要支持、要合规） | **≈3 年到 $1M ARR** | 查不到分母 | [plausible.io/blog/open-source-saas](https://plausible.io/blog/open-source-saas) |
| **内部工具 → 卖给开发者的模板/脚手架** | Tailwind UI **首日 $400k**、5 个月近 $2M、2 年内 >$4M；ShipFast 5 个月 $250k、峰值 ~$141k MRR（2024-04）；ShipAny **上线 4 小时 $10,000**（$249/份）【幸存者，均自述】 | 低（代码已经在手上） | 上线当天就有钱**——如果分发已经在了** | 有清晰衰减：ShipFast $141k MRR（2024-04）→ **$20k/月（2026-01）**，18 个月掉 85%【幸存者自述】 | [adamwathan.me 2020-08-02](https://adamwathan.me/tailwindcss-from-side-project-byproduct-to-multi-mullion-dollar-business/)；[newsletter.marclou.com 2026-01](https://newsletter.marclou.com/p/i-made-1-032-000-in-2025)；[hub.baai.ac.cn](https://hub.baai.ac.cn/view/42470) |
| **内部工具 → 面向普通用户的 SaaS/AI 产品** | Indie Hackers 产品 **54% 收入为 $0**（2023/2024/2026 三年不变）；有收入的里 ~25% <$1k MRR、~5% 在 $10k-100k、~1% >$100k【二手：solooperatorstack 引 ScrapingFish 引 "Stripe-verified"，未取到原始数据集】 | 低 | idoubi：11 个产品 / 1 年 → 合计 **$1,000 MRR** | ThinkAny 月访问 64 万，**付费率 0.03%**【幸存者自述】 | [solooperatorstack 2026-07-15](https://solooperatorstack.com/blog/indie-hacker-revenue-distribution-tam-clarity/)；[hub.baai.ac.cn](https://hub.baai.ac.cn/view/42470) |
| **数字产品（电子书/课程/模板）挂平台** | Gumroad 146,271 个商品：中位创作者 **$72/月**，**44% 的商品收入 $0**，top 1% 拿走 **99.5%** 的流水【有分母，但是第三方爬取+估算，非平台口径】。Gumroad 官方早期披露：789 人月入 >$1,000、81 人月入 >$10,000 | 极低 | 有受众 60-90 天到第一个 $100；无受众 6-12 个月 | 44% 归零 | [insightraider.com](https://insightraider.com/en/state-of-gumroad-2026)（2026-01~04 爬取） |
| **技术内容 → 引流 → 卖别的** | B站 22 万粉剪辑教程 UP：**141 个视频的平台激励总共 7,313 元**；同期一年约 5 个商单赚 **≈4 万元**。另一位 30 万粉前端教程 UP 自称月入 12 万+（靠免费教程转付费）【幸存者自述，无第三方核实】 | 低 | 数月起 | 平台激励几乎不是收入 | [虎嗅 2022-05](https://www.huxiu.com/article/554124.html)；[CSDN 2025](https://blog.csdn.net/HONGGE1688/article/details/148408666) |
| **付费专栏（中文）** | 掘金小册：平台抽 **30%**、作者拿 70%，要 LV5 以上。**作者收入数字查不到**。极客时间分成比例**查不到**。知识星球头部：stormzhang 第三期 1.91 万人 × 299 元 ≈ 500 万+【自媒体估算，非本人公布】；洪灏开星球 11 天收入超 800 万元【证券时报报道】 | 低-中（要先有名） | — | 转述称"99% 的知识星球年收入 <10 万元"【无法核实，无方法说明】 | [juejin.cn](https://juejin.cn/post/6992048482441756709)；[stcn.com](https://www.stcn.com/article/detail/3477342.html) |
| **自动化能力 → 中小企业交付** | 中文侧：技术咨询报价 **500-2,000 元/小时**；入门级小程序出现 **1,000 元**低价单；2025 自由职业者数量 +35% 而订单量增速仅 +18%；75% 的项目要求"交付+运维+优化"全流程【二手：知乎行业文，无方法说明】 | 中（要谈、要合同、要售后） | 一次对话到一张合同 | 查不到可靠分母 | [知乎行业报告](https://zhuanlan.zhihu.com/p/1991483501489432478) |
| **卖 Prompt** | PromptBase 2025-11 月访问 **487,110**，环比 **-13.6%**（Similarweb）；平台抽 20%。卖家收入分布**查不到** | 极低 | — | **赛道在缩** | [similarweb.com/website/promptbase.com](https://www.similarweb.com/website/promptbase.com/) |
| **卖 GPT（GPT Store）** | OpenAI 称已有 **300 万个**自定义 GPT。分成计划仅对"美国的、做出热门 GPT 的少数 builder"开放且**不再接收新 builder**。总分成额、参与人数 **OpenAI 从未公布 → 查不到官方数字**。二手转述：约 $0.03/次对话、要 $1,000/月需 33,000+ 次对话【无法核实】 | 极低 | — | 多数创作者拿不到钱（有每周 25 次对话的最低门槛）【二手】 | [venturebeat](https://venturebeat.com/ai/openai-launches-gpt-store-but-revenue-sharing-is-still-to-come)；[OpenAI 社区讨论串](https://community.openai.com/t/what-is-the-status-with-gpt-store-revenue-share/839172) |
| **卖 MCP server** | 官方 registry 2025-09 上线，**2025-11 接近 2,000 条**（较首批 +407%）。**没有查到任何一笔公开的 MCP server 收入金额 → 查不到数字** | 极低 | — | 无分母可算 | [modelcontextprotocol.io/registry](https://modelcontextprotocol.io/registry/about)；[MCP 博客 2025-11-25](https://blog.modelcontextprotocol.io/posts/2025-11-25-first-mcp-anniversary/) |
| **卖 Claude Skill / Agent Skill** | **没有官方市场。** 第三方：Agensi（创作者拿 70%）、Agent37（托管 $3.99/月起）、ClaudeSkillsMarket（37+ 免费社区 skill）。**没有任何一家公开过成交额或卖家收入 → 查不到数字，连分母都不存在** | 极低 | — | 无法评估 | [agensi.io](https://www.agensi.io/learn/agent-skills-marketplace-sell-your-skills)；[claudeskillsmarket.com](https://www.claudeskillsmarket.com/) |
| **把产品卖掉（退出）** | Acquire.com 2,000+ 笔完成交易：2024、2025 两年 SaaS **中位成交都是 3.9× 年利润**（<$1M ARR 走 SDE 口径）；微型 SaaS（<$10k MRR）通常 **2-3.5× ARR**【有分母】 | — | — | **年利润 0 → 估值 0** | [blog.acquire.com 2026-02](https://blog.acquire.com/acquire-com-biannual-acquisition-multiples-report-jan-2026/) |

---

## 2. 有数字的案例集（9 个，中英各半）

### 案例 1 · Tailwind UI（英）—— 免费项目就是分发渠道
- **起点**：2017-11-01 开源 Tailwind CSS，免费，无商业计划。
- **动作**：公开直播开发过程；2018-12 先出《Refactoring UI》电子书（第一笔收入，作者说这笔钱让他能全职）；**2020-02-26** 才上线第一个和框架直接绑定的付费产品 Tailwind UI。
- **结果**：**上线首日 $400,000**；到 2020-08 接近 $2M；2 年内超过 $4M；2020 年底"稳定七位数中段/年"。
- **耗时**：**从开源到第一天大额收入，2 年 3 个月 27 天。**
- **要点**：作者自己归因于"公开工作"——他说如果不是当时在直播那个"又一个会被放弃的副项目"，这门生意根本不会存在。**收钱那天是短的；建分发那 2 年是长的。**
- 出处：[adamwathan.me](https://adamwathan.me/tailwindcss-from-side-project-byproduct-to-multi-mullion-dollar-business/)（2020-08-02）【幸存者】

### 案例 2 · ShipFast / Marc Lou（英）—— 模板赛道的完整生命周期
- **起点**：2023-09 上线一个 Next.js 样板代码，$199 起。
- **动作**：在 X 上高频公开收入。
- **结果**：**5 个月 ~$250,000**；峰值 **~$141k MRR（2024-04）**；**2026-01 降到 ~$20k/月**（作者归因于 Next.js 样板市场饱和）。2025 全年总收入 **$1,032,000**，**比 2024 少 20%**。其中 ShipFast $20k/月、CodeFast $20k/月、DataFast $15.8k/月、X 平台分成 $14,339、投资收益 $147,000。
- **同期归零的**：BioAge、ClipMarc 两个产品收入为 **0**。
- **耗时**：起量 5 个月；衰减 18 个月掉 85%。
- **要点**：这是唯一一个能看到**同一个人内部幸存者偏差**的案例——他有 10 万粉丝，仍然有产品是 0。他自己说：有受众不保证创业成功。
- 出处：[newsletter.marclou.com](https://newsletter.marclou.com/p/i-made-1-032-000-in-2025)（2026-01）【幸存者自述】

### 案例 3 · idoubi / ShipAny（中）—— **最贴近本人处境的一个**
- **起点**：从腾讯离职做独立开发，2024 年全年造东西。
- **动作**：2024 年上线 **11 款 AI 产品**（含未发布的约 20 个项目）：AI Cover（春节赚了几千块）、Sora FM（**0**，域名后来被封）、ThinkAny（5 月做到 **64 万月访问**）、Melodisco（**0**，一个月后放弃）、HeyBeauty（**0**）、Pagen（**0**，拒了 $10k 收购）、PodLM（营收还行、付费率较高）、mcp.so 导航站、ShipAny。
- **结果**：**2024 年底，4 款产品合计 MRR = $1,000。** ThinkAny 的**付费率 0.03%**。然后 2024-12-25 上线 ShipAny（$249 的 AI SaaS 脚手架），**4 小时 $10,000**，**一周的收入超过其他所有产品一年之和**。
- **耗时**：12 个月造 11 个面向用户的产品 → $1,000 MRR；1 个卖给开发者的模板 → 4 小时 $10,000。
- **补充数字（2025-11）**：他用 ShipAny Two 搭了个 AI 音乐生成器验证 SEO，一个月纯搜索流量带来 **8,000 注册用户**，接上支付一周多，**开了 15 单、收入 500 多刀**。→ **8,000 注册 = 15 单 = 0.19%**。
- **要点**：一个人、一年、11 个产品，唯一起量的是**卖给和他一样的人的工具**。这条经验对 owner 的映射几乎是 1:1。
- 出处：[hub.baai.ac.cn/view/42470](https://hub.baai.ac.cn/view/42470)（2025-01）；[X @idoubicc 2025-11](https://x.com/idoubicc/status/1990229939854164297)【幸存者自述】

### 案例 4 · curl / Daniel Stenberg（英）—— 装机量不是钱，合同才是
- **起点**：curl 是地球上部署量最大的软件之一。
- **动作**：**2019-02-01 起**，wolfSSL 开始卖 curl 的商业支持：Basic **$2,000/年**、Standard **$6,000/年**、Premium **$23,000/年**、24×7 **$50,000/年**。
- **结果**：wolfSSL 收客户的钱，发 Stenberg 的**全职工资**。他到 2026 年仍在这个安排下全职做 curl。
- **耗时**：curl 1998 年就有了，这条路径 2019 年才打通 —— **20 年**。
- **要点**：**这条路径的钱不来自捐赠，来自 B2B 合同，且需要一个能开合同的法人。** 对比案例 5 看。
- 出处：[helpnetsecurity](https://www.helpnetsecurity.com/2019/02/07/daniel-stemberg-joins-wolfssl/)（2019-02-07）【幸存者，机制可复制】

### 案例 5 · core-js / Denis Pushkarev（英）—— 最强的反面数字
- **起点**：core-js，npm **每月 2.5 亿次**下载、累计 **90 亿次**，被互联网 **top 100 网站的 75%** 使用。
- **动作**：多次公开募捐。
- **结果**：全职维护期约 **$2,500/月**，后来降到 **≈$400/月**；更早一次募捐的结果是 **$57/月**。作者公开抱怨开源模式坏掉了（2023-02）。
- **要点**：**如果"用的人多"能变成钱，core-js 的作者应该是富人。** 2.5 亿次/月的下载量 = $400/月。**赞助路径与装机量脱钩，这是有具体数字的。**
- 出处：[The Register 2023-02-15](https://www.theregister.com/2023/02/15/corejs_russia_open_source/)；[The Stack](https://www.thestack.technology/core-js-maintainer-denis-pusharev-license-broke-angry/)【单案例，但极端到有诊断价值】

### 案例 6 · Plausible Analytics（英）—— 开源托管版的真实时间轴
- **起点**：2019-05 开始卖订阅。
- **动作**：开源 + 内容营销，**从不投广告**。
- **结果**：**324 天**才到第一个 **$400 MRR**；从 $400 到 $2,750 MRR 用了 **135 天**；从 $400 到 $10,000 MRR 用了 **9 个月**；**10 个月**到 $500k ARR；**2022-06-02** 越过 $1M ARR（$83,637 MRR）。到 2026 年 19,000+ 付费订阅，团队 4 人。
- **耗时**：**开卖到 $1M ARR ≈ 3 年 1 个月。第一年基本没钱。**
- **要点**：这条曲线是"开源 SaaS 最好的公开样本之一"，**它的第一年是 324 天换 $400/月**。任何人拿"开源 SaaS 能赚钱"当近路，先看这个数字。
- 出处：[plausible.io/blog/open-source-saas](https://plausible.io/blog/open-source-saas)、[bootstrapping-saas](https://plausible.io/blog/bootstrapping-saas)【幸存者，逐步公开】

### 案例 7 · B站 22 万粉技术/教程 UP 主（中）—— 内容不是收入，是渠道
- **起点**：剪辑教程账号，22 万粉，141 个视频。
- **结果**：**141 个视频的平台激励计划总收益 = 7,313 元**（平均一个视频约 51 元）。同期**一年接约 5 个商单，赚约 4 万元**。
- **对照组**：另一位 30 万粉的前端开发教程 UP 自称**月收入稳定 12 万以上**，机制是"免费基础教程引流 → 转化为付费用户"。
- **要点**：**同样量级的粉丝，收入差 30 倍，差别不在粉丝数，在有没有东西可卖。** 平台分成在两个案例里都接近于 0。
- 出处：[虎嗅/腾讯新闻 2022-05](https://www.huxiu.com/article/554124.html)；[CSDN 2025](https://blog.csdn.net/HONGGE1688/article/details/148408666)【自报，无第三方核实】

### 案例 8 · Gumroad 全平台（英）—— 有分母的长尾形状
- **样本**：146,271 个商品，2026 年 1-4 月爬取。
- **结果**：**中位创作者月入 $72**；**44% 的商品收入为 $0**；**top 1% 拿走 99.5% 的平台流水**；追踪到的总流水 $206M。有受众的人 60-90 天到第一个 $100，没受众的 6-12 个月。
- **早期官方对照**（Sahil Lavingia 公布）：**789 人**月入 >$1,000、**81 人**月入 >$10,000。
- **方法学警告**：收入是"评分数 × 均价 × 转化系数"估算的，**不是 Gumroad 官方口径**，发布方自己承认"关闭评分或用自定义店面的商品会被低估"。**结构（长尾、44% 归零）可信，绝对值要打折看。**
- 出处：[insightraider.com/en/state-of-gumroad-2026](https://insightraider.com/en/state-of-gumroad-2026)【有分母，方法有缺陷】

### 案例 9 · Steam 全平台（英）—— "单人做产品"收入分布的最干净代理
- **样本**：Steam 上 71,000+ 款游戏（Gamalytic 数据，2023-10）。
- **结果**：**67% 的游戏终身收入 <$5,000**；近 3 年发行的游戏里 **76.5% <$5,000**；近 3 年非免费游戏的**中位收入 ≈ $700**。只有 8.9% 超过 $20 万；77% 的游戏定价低于 $10。
- **要点**：这是我能找到的最有分母、最没有自我选择偏差的"一个人做一件产品去市场上卖"的分布。**中位数 $700。** 任何"我做一个东西挂出去"的路径，先按这个先验来估。
- 出处：[gamedevreports.substack.com](https://gamedevreports.substack.com/p/gamalytic-67-of-games-on-steam-earned)（2023-10）【有分母】

---

## 3. 「做了很多但没变成钱」的诊断框架

### 3.1 已有的公开论述（有论证的部分）

| 来源 | 核心论证 | 有没有数字 |
|---|---|---|
| **Melissa Perri《Escaping the Build Trap》**（O'Reilly, 2018） | 陷阱的定义：**用"发了多少功能"（output）衡量成功，而不是"产生了什么结果"（outcome）**。output 好量化（功能数、发布数、velocity），outcome 是业务和客户的实际变化。默认用 output 度量的组织会变成"功能工厂"，价值反而缩水。 | 无量化数字，属**有影响力的观点**。但**定义本身是可操作的** |
| **Peter Thiel《Zero to One》第 11 章** | 论断（中文转述）：**发明了新东西却没发明一个有效的卖法，那就是一门糟糕的生意，产品再好也一样。** 更强的一半：卓越的分销本身就能造出垄断，即使产品没有差异化；**反过来不成立**——好产品在没有分销时会死。 | 无数字，属**观点**。但和下面 CB Insights 的 43% 互相印证 |
| **CB Insights 创业失败复盘**（2026-03-05 版，431 家已关停的 VC 支持公司，385 家可归因） | **70% "钱烧完了"——但那是死因不是病因**；**43% 产品市场匹配差**；**29% 时机不对**；**19% 单位经济模型不成立**。431 家合计融资 $17.5B，中位 $11M。早期版本（110+ 复盘，2014-2021）里 **"没有市场需求" 42%** 排第一。 | **有数字、有分母** |
| **Rob Walling《Stair Step Method》**（2015-03-26） | 三步：① 做一个**一次性付费、单一渠道**的小产品（明确说：**别把 SaaS 当第一个产品**，优先做寄生在已有生态上的插件/加载项）；② 重复第一步直到能替代工资；③ 才做订阅制产品。渠道纪律：**盯住第一个奏效的免费渠道，做到它进入平台期为止**，不要同时开多个。 | 无量化数字，属**方法论**。但和案例 1/2/3 的实际路径完全吻合 |
| **Sean Ellis 40% PMF 测试** | 研究近 100 家创业公司得出：问"如果不能再用这个产品你会怎样"，**≥40% 回答"非常失望"** 就大概率有 PMF。**样本量要求：40-100 份有效回答**，低于 40 份几个离群值就能让分数摆动 10+ 个百分点，且只能问"过去两周用过核心功能"的活跃用户。 | **有数字**（样本量门槛是硬的） |

**中文侧**：没有找到有数据支撑的系统论述。查到的都是自媒体总结，**无方法说明 → 不采用**。

### 3.2 自检清单（可操作，每一条都能从现有数据取到答案）

对每一个项目/资产，按顺序问。**任何一条答不上来就停在那一层，不许往下跳。**

| # | 问题 | 判定标准 | 现有数据能不能自动回答 |
|---|---|---|---|
| 1 | **过去 30 天，我做的哪一件事的目的是"有人付钱"？** 说不出就是 0。 | 必须能说出**具体动作**（发了一条推、发了一封邮件、报了一次价），不是"我做了 X 功能" | 能：`opportunity_block()` 已经在按主题分"离钱最近/纯技术"，但**它没有"对外动作"这一类** |
| 2 | **这个东西，除了我以外还有谁装过？** 0 个人 = 停在 EXPERIMENT。 | `compound.py` 的 `ADOPTED` 定义已经写对了：**"被第二个任务/项目复用"** | 能，`derive_debt()` 的 `deployed_no_adoption` 就是这条 |
| 3 | **我向多少人开过价？被拒了几次？理由是什么？** | 这是 0 用户时**唯一有统计意义的转化率**（分母是报价数不是访客数），n=5 就有信息 | **不能。这是现在完全缺失的一列** |
| 4 | **有没有人为了解决这个问题，在过去 12 个月里花过钱？花了多少？** | Mom Test 式的过去行为证据。问"你会买吗"无效，问"你上次为这个花了多少"有效 | 不能 |
| 5 | **我在这上面花的时间，转化成了一个可以被第二个人拿走的东西吗？** | 文件 / 包 / 脚本 / 文档，不是"我知道怎么做" | 能：`repeat_no_asset`（问了 N 遍还没固化）就是这条 |
| 6 | **这个东西如果今天消失，谁会来找我？** 答不出人名 = 没有 outcome | Perri 的 output/outcome 分界，落到个人尺度 | 不能 |
| 7 | **我的分发渠道是什么？它现在有多少人？** 答"还没有" = 这个产品还不该做完 | Thiel + Rob Walling 的渠道纪律 | 不能 |
| 8 | **距离第一美元还差几个动作？每个动作是什么？** 数不出来 = 这条路径没规划过 | 每个动作必须是"我做完就完了"的，不能是"等别人" | 不能 |

**第 3、4、6、7、8 条现在都取不到 —— 这五条恰好全部是"对外"的。这就是 10:5:1 里从 5 到 1 的那一段。**

---

## 4. 可借用的转化度量：单人 + 尚无用户时哪些仍然成立

### 4.1 仍然成立的（全部是绝对计数，不是比率）

| 指标 | 为什么成立 | 门槛 |
|---|---|---|
| **报价数 / 被拒数 / 被拒理由** | 分母是"我发出的报价"，我自己控制。n=5 就能看出模式（价格 vs 不需要 vs 不信任是三种完全不同的病） | 5 |
| **第一美元时间（TTFD）** | 单一数字，可跨案例对标。Plausible 是 **324 天到 $400 MRR**，ShipAny 是 **4 小时到 $10,000**，差别不在产品质量，在开卖那天分发在不在 | 1 |
| **跨任务复用次数** | `compound.py` 已经做对：单人工作区里"被第二个人采用"天然为空，**"被第二个任务复用"是唯一可观测的采用代理**。这个判断在公开文献里没人替单人场景写过，代码里已经写了 | 2 |
| **过去付费证据（Mom Test）** | "你上次为这个问题花过多少钱" —— 问过去行为不问未来意愿 | 5 |
| **对外动作计数** | 发出去的推 / 邮件 / 帖子 / demo 的**绝对次数**。零就是零，不需要统计学 | 1 |
| **AARRR 里只有 A（Acquisition）的绝对值** | Dave McClure 的 AARRR 后四段在 n<100 时全是噪声，但"有多少人来过"是可数的 | 1 |

### 4.2 **明确不成立的**（数字上不成立，不是"不重要"）

| 指标 | 为什么不成立 | 硬门槛数字 |
|---|---|---|
| **转化率优化 / A/B 测试** | 基线转化率 5%、想检出 20% 的相对提升（5%→6%），95% 置信 + 80% power，需要 **约 8,158-15,000 访客/变体**（合计 16,000-30,000）。想检出 5% 的相对提升，需要 **约 240,000 访客/变体**。样本量 ∝ 1/MDE² | **>8,000/变体** |
| **Sean Ellis 40% PMF 调查** | 需要 **40-100 份**"过去两周用过核心功能"的回答，低于 40 份分数会摆动 10+ 个百分点 | **40 份活跃用户** |
| **留存曲线 / cohort retention / DAU-MAU** | 需要多个足量 cohort 才能分辨真实衰减和噪声 | 每 cohort 数百 |
| **免费→付费转化率基准** | OpenView + Profitwell 汇总 1,000+ SaaS 的中位数是 **14-25%**（按试用模式分），自助 freemium 好的区间只有 **2-5%**；同一口径下不同年份差一倍（opt-in 试用 2025 年 18.2% vs 2026 年 8.9%）。**基准本身波动比信号大，拿它当目标是自欺** | 不适用 |
| **NPS** | 小样本无意义 | 不适用 |

**一句话**：**在 0 用户阶段，所有"率"都是假的，只有"数"是真的。** 现有 `compound.py` 的漏斗计数（每个 stage 有几条候选）恰好是"数"不是"率"—— 这个选择是对的。

### 4.3 给现有实现的两条具体建议（不写代码，只给结论）

1. **`opportunity_block()` 缺的是"对外动作"这一类。** 现在的 4 类（离钱最近的话题 / 做熟了但每次重来 / 投入了没交付 / 最贵的几场）全部是**对内**的。10:5:1 里，"造→交"这一段现有代码能测（`shipped` 字段），**"交→换到钱"这一段一条信号都没有**。缺的最小信号是：**「过去 30 天有没有一个动作的收件人不是我自己」**。这个可以从会话记录里确定性派生（有没有出现"发布/发帖/报价/联系"类主题），不需要模型。

2. **`compound.py` 的 `NOT_MEASURED` 里"本机没有账单/发票/收款记录的接入口"这条要改判。** 它现在被写成一个**测量能力的缺陷**，实际是一个**业务状态的事实**：没有收款记录是因为还没有第一次收款。这两件事在页面上应该分开显示，否则会一直读成"我们只是没接上数据"。

---

## 5. 对这个人的具体判断：路径排序 + 每条缺的那一步

### 排序（按"距离第一美元的动作数"，不是按天花板）

---

#### 第 1 名 · 把治理/流水线打成开发者付费包（对标 ShipAny / ShipFast / Tailwind UI）

**手上最接近的东西**：`CodexSkills/registry`（已经是 skill 注册表结构）+ Golden Path 6 步部署配方 + 9 个仓的 `AGENTS.md` / 机器守卫脚本 + taskpack/verifier 全套 + R2 零付费守卫 + "部署即登记"治理 + `flow.yaml` 业务流登记。

**为什么最短**：
- 这是他**已经造完并且自己在用**的东西，不需要新造。
- 目标客户和他自己是同一种人（重度用 agent、有多个仓、被 agent 乱改怕了）——**这是 idoubi 的唯一起量产品和 Marc Lou 的三个赚钱产品的共同特征：卖给和自己一样的人。**
- 数字支撑：这条是唯一在中英文两侧都有 4-6 位数首月的路径（Tailwind UI 首日 $400k、ShipFast 5 个月 $250k、ShipAny 4 小时 $10k）。

**缺的那一步（只有一步）**：**一个陌生人能在 10 分钟内自己装上、跑通、并看到它拦下一次真实错误的打包物 + 一个能收钱的页面。**

不是"做得更完善"。ShipAny 卖 $249 的时候不比他现在的东西完善。缺的是**离开这台机器还能跑**这个属性。

**风险数字（必须一起看）**：ShipFast 从 $141k MRR 掉到 $20k/月用了 18 个月 —— **这条路径的收入是脉冲式的，不是年金**。按"一次性买断 + 3-6 个月窗口"来规划，不要按 MRR 规划。

---

#### 第 2 名 · B2B 交付/支持合同（对标 curl↔wolfSSL、中文技术咨询 500-2,000 元/小时）

**手上最接近的东西**：一台**真的在跑生产流量**的 OVH VPS-3、Cloudflare Tunnel → Traefik 的完整链路、换机时踩过的六类静默失效、R2 从 $9 账单里学到的 IA 计费陷阱、"域名 200 不是迁移完成的证据"这类**别人真的会花钱避免的经验**。

**为什么第二短**：**它的分母不是 10,000 个访客，是 5 场对话。** 这是全部路径里唯一一条**不需要产品市场匹配、只需要一个客户**的。curl 的钱从来不是捐款，是 wolfSSL 开出的 $2,000-$50,000/年的合同。

**缺的那一步**：**一句能说清"我卖什么、多少钱"的报价，以及一个能开票收款的通道。**

现在的状态是"能做很多事"，那不是报价。报价长这样：*"我帮你把 X 部署到自己的机器上并做完监控和备份，Y 元，Z 天，做不到退款。"* 中文侧技术咨询的现价是 **500-2,000 元/小时**，这是可对标的锚。

**警告数字**：2025 年中文自由职业者数量同比 **+35%**，而外包订单量增速只有 **+18%**；且 **75% 的项目要求"交付+运维+优化"全流程**，只会开发的接单成功率下降 40%。**——他恰好是有运维和治理能力的那一类，这是他相对优势最大的地方。**（此数据为知乎行业文，无方法说明，**只能当方向不能当依据**。）

---

#### 第 3 名 · 用会话数据本身做内容，反过来给第 1、2 名引流

**手上最接近的东西**：4802 场会话的确定性统计。"119 天里只有 38 天产生提交"、"造:交:换钱 = 10:5:1"、"2826 场里只有 952 场是本人"、"7 个死等循环最长跑了 29 小时"、"51 次 IA 操作 = $9.00 而 301 万次 Standard = $0.00" —— **这些数字全网没有第二个人有。**

**为什么第三**：它本身几乎不产生收入（B站案例：141 个视频的平台激励总共 7,313 元），**但它是第 1、2 名唯一可行的分发渠道**。Tailwind UI 首日 $400k 的前提是免费框架跑了 2 年 3 个月；ShipAny 4 小时 $10k 的前提是作者在 X 上已经公开了一整年的产品日志。

**缺的那一步**：**一次公开发布。** 他有数据、有结论、有代码，**发出去的次数是 0**。这一步的成本是几小时，收益是让第 1、2 名从"不可能"变成"可能"。

---

#### 第 4 名 · 开源赞助（数学上不成立，只能当副产品）

**手上最接近的东西**：9 个仓、741 提交、45 Release。

**为什么远**：缺的不是"做得更好"，是"**有几十万人在用**"。core-js 每月 2.5 亿次下载 = **$400/月**。GitHub Sponsors 7 年 $100M 分给 7 万人 = 人均终身 $1,430。49,148 人的赞助图谱里只有 7,343 人在收钱。

**缺的那一步**：一个**量级差 5-6 个数量级**的用户基数。**这条路径不该被规划，只该被接受为第 1/2 名成功后的附赠品。**

---

#### 第 5 名 · 面向普通用户的 AI 产品 / SaaS（最远，失败率最高）

**手上最接近的东西**：MemoryAtlas、status 站、Gatus/uptime 这类自建站点。

**为什么最远**：
- idoubi：11 个产品 / 12 个月 → **$1,000 MRR**；ThinkAny 64 万月访问 → 付费率 **0.03%**；8,000 注册 → **15 单**。
- Indie Hackers **54% 的产品收入为 $0**（三年不变）。
- Steam 中位收入 **$700**。
- AI 工具目录：ToolDirectory.AI 追踪的 2,718 个工具里 **9.3% 已死**；Dang.ai 口径是 **26.8%**；**最常见的死法是域名过期（占墓地条目 40%，占"真死"的 64%）—— 没人发公告，就是停止续费。**

**缺的那一步**：**分发**。而这一步的成本远高于他造东西的成本 —— 他造东西的边际成本已经被 agent 压到接近 0，**这恰恰是为什么"再造一个"永远比"去卖一个"更容易，也永远换不到钱。**

---

### 5.1 逐条映射：第 1 节对照表里每一条路径，他手上最接近的是哪一样

| 路径（对应 §1） | 手上最接近的东西 | 距离 | 缺的那一步 |
|---|---|---|---|
| 开源 → 个人赞助 | 9 个仓 / 741 提交 / 45 Release | 远 | 用户量差 5-6 个数量级。**不该规划，只能当副产品** |
| 开源 → B2B 支持合同 | OVH VPS-3 生产机、CF Tunnel→Traefik 链路、迁移六类静默失效、R2 计费陷阱经验 | **近（第 2 名）** | 一句报价 + 一个收款通道 |
| 开源 → 托管版 SaaS | MemoryAtlas、status 站、Gatus/uptime | 远（3 年量级） | 先要有人在自己装 —— 现在装机数 = 1（他自己） |
| 内部工具 → 开发者模板/脚手架 | `CodexSkills/registry`、Golden Path 6 步、9 仓 AGENTS.md + 守卫、taskpack/verifier | **最近（第 1 名）** | 一个陌生人 10 分钟能装上跑通的打包物 + 收钱页面 |
| 内部工具 → 面向普通用户 SaaS | MemoryAtlas、status.linzezhang.com | 最远 | 分发。且这一步成本 >> 他造东西的成本 |
| 数字产品挂平台（Gumroad 类） | 会话统计报告、治理手册、`_protected/INFRA_CONFIG.md` 那类沉淀 | 中 | 挂平台前先要有第 3 名的渠道，否则落进 44% 归零的那一档 |
| 技术内容 → 引流 → 卖别的 | **4802 场会话的确定性统计**（10:5:1、84 天只聊没交付、2826 场里 952 场是本人、51 次 IA = $9.00） | **近（第 3 名）** | **一次公开发布。现在发出去的次数是 0** |
| 付费专栏（中文） | 同上那批数字 + 9 个仓的实战踩坑 | 中 | 要先有名。且**掘金/极客时间的作者收入零公开数据，无法估算回报** |
| 自动化能力 → 中小企业交付 | 整套 agent 流水线 + 部署即登记 + `flow.yaml` 业务流登记 + 每日复审 cron | **近（并入第 2 名）** | 同第 2 名：报价 + 收款。中文侧锚价 500-2,000 元/小时 |
| 卖 Prompt | CodexSkills 里的 prompt 版本治理 | 不建议 | 赛道在缩（-13.6%/月），**放弃** |
| 卖 GPT | 无直接对应 | 不可行 | 分成计划**不接收新 builder** |
| 卖 MCP server | 无直接对应（本机有 MCP 使用经验但无自建 server 资产） | 不可评估 | **连一笔公开收入金额都查不到，没有分母** |
| 卖 Claude Skill | `CodexSkills/registry`（结构上最接近，是他最强的资产之一） | 不可评估 | **没有官方市场，第三方无成交数据。→ 应该走"第 1 名"的自建打包+自建收款，不要指望市场** |
| 把产品卖掉（退出） | 无（所有资产年利润 = 0） | 不可行 | 中位成交 3.9× 年利润，**0 × 3.9 = 0** |

**注意 `CodexSkills/registry` 在表里出现了两次**（第 1 名的打包物 / 卖 Skill）。这不是巧合 —— 它是他手上**唯一一个同时具备"已成型的结构"和"已存在的付费意愿人群"**的资产。区别只在于：走第 1 名是**自己收钱**（有先例、有金额），走"卖 Skill 市场"是**等平台**（无先例、无金额）。**结论：同一个资产，走自建收款，不走市场。**

### 5.2 一句话总结排序理由

**他缺的不是能力、不是资产、不是工具 —— 是"收件人不是自己"的动作。** 前三名的共同点是它们都只差这一个动作；后两名的共同点是它们还差一个数量级的用户基数。

---

## 6. 反面清单：看起来诱人但对单人不成立

| # | 诱人的说法 | 为什么不成立 | 数字 |
|---|---|---|---|
| 1 | **"东西够好，star 多了自然有人赞助"** | 装机量与赞助收入**脱钩**，有极端个案证明 | core-js **2.5 亿次/月下载 = $400/月**；GitHub Sponsors 人均终身 $1,430；49,148 人样本里只有 **15%** 在收钱 |
| 2 | **"做个 AI 产品，用户自己会来"** | 免费用户转付费在这个量级下是 0.0X% | ThinkAny **0.03%** 付费率；8,000 注册 → **15 单（0.19%）**；IH **54% 产品收入 $0** |
| 3 | **"先做出来，再想怎么卖"** | 有分母的失败复盘直接否掉 | CB Insights 431 家：**43% PMF 差、29% 时机不对**（"钱烧完"的 70% 是死因不是病因）。Thiel 第 11 章：没发明卖法就是坏生意 |
| 4 | **"做 A/B 测试优化转化率"** | 样本量不够，产生的是噪声不是信号 | 5% 基线检出 20% 相对提升需 **8,158-15,000 访客/变体**；检出 5% 提升需 **240,000/变体** |
| 5 | **"跑个 PMF 调查看看有没有市场"** | 需要活跃用户，他有 0 个 | Sean Ellis 测试要 **40-100 份**"两周内用过核心功能"的回答 |
| 6 | **"卖 prompt / 卖 Claude Skill / 卖 MCP server"** | **赛道要么在缩，要么连分母都不存在** | PromptBase 2025-11 访问量 **-13.6%**；MCP registry 约 2,000 条但**没有一笔公开收入金额**；Claude Skill **没有官方市场**，第三方无一家公开成交额 |
| 7 | **"做 GPT 上 GPT Store 拿分成"** | 分成计划**不对新 builder 开放**，且总额从未公布 | 300 万个 GPT；分成仅限"美国的、已做出热门 GPT 的少数 builder"，**不再接收新 builder** |
| 8 | **"买课做 AI automation agency，被动收入"** | **交付服务本身成立，"加盟拿被动收入"是另一回事** | FTC 起诉 Click Profit（2025）：**1/5 客户一分钱没赚，1/3 客户终身收入 <$2,500**，亚马逊封停/终止了约 **95%** 的店铺 |
| 9 | **"先把产品做大再卖掉"** | 估值挂在利润上，不挂在代码量上 | Acquire.com 2,000+ 笔：**中位 3.9× 年利润**。**年利润 0 → 估值 0** |
| 10 | **"多做几个产品，总有一个中"** | 同一个人内部也是长尾，而且**分散会让每个都到不了分发临界点** | Marc Lou 有 10 万粉丝，同期 BioAge、ClipMarc 仍然是 **0**；idoubi 11 个产品 → $1,000 MRR，起量的只有 1 个 |
| 11 | **"靠内容变现"（做号赚钱）** | 平台分成接近于 0，钱在"卖东西"那一步 | B站 **141 个视频的激励总共 7,313 元**；同期 5 个商单 ≈ **4 万元**。差 5 倍以上，且商单本身也不是内容收入 |
| 12 | **"开源 SaaS 是条快路"** | 最好的公开样本第一年也几乎没钱 | Plausible **324 天**才到第一个 **$400 MRR**；到 $1M ARR 用了 **3 年** |

---

## 7. 出处清单（按引用顺序）

**开源 / 赞助**
- GitHub 官方 $100M 里程碑：https://github.blog/open-source/maintainers/100-million-for-open-source-a-milestone-built-by-the-community/ （2026-07-20）
- Mapping GitHub Sponsorships（arXiv 2604.03846，2026-03 采集，49,148 用户）：https://arxiv.org/html/2604.03846
- Who, What, Why and How? GitHub Sponsor 机制实证（arXiv 2111.13323，8,028 maintainers / 13,555 sponsors / 22,515 sponsorships）：https://arxiv.org/abs/2111.13323
- ICSE 2022 "GitHub Sponsors"（DOI 10.1145/3510003.3510116，**原文 403 未取到，转述称"仅 31% 开通者收到过打赏、其中 39.3% 只收到 $1"—— 二手，未核实**）：https://dl.acm.org/doi/10.1145/3510003.3510116
- core-js 资金状况：https://www.theregister.com/2023/02/15/corejs_russia_open_source/ （2023-02-15）
- curl 商业支持分层与 wolfSSL 雇佣关系：https://www.helpnetsecurity.com/2019/02/07/daniel-stemberg-joins-wolfssl/ （2019-02-07）
- Plausible 开源 SaaS 到 $1M ARR：https://plausible.io/blog/open-source-saas ；到 $500k：https://plausible.io/blog/bootstrapping-saas

**模板 / 独立开发者**
- Adam Wathan / Tailwind UI 完整时间轴：https://adamwathan.me/tailwindcss-from-side-project-byproduct-to-multi-mullion-dollar-business/ （2020-08-02）
- Marc Lou 2025 年收入拆解：https://newsletter.marclou.com/p/i-made-1-032-000-in-2025 （2026-01）
- idoubi 2024 年 11 款产品复盘：https://hub.baai.ac.cn/view/42470 （2025-01）
- idoubi SEO 站转化数字：https://x.com/idoubicc/status/1990229939854164297 （2025-11）
- Gumroad 全平台分布（146,271 商品，爬取估算）：https://insightraider.com/en/state-of-gumroad-2026 （2026-01~04）
- Indie Hackers 收入分布（**二手引用链**）：https://solooperatorstack.com/blog/indie-hacker-revenue-distribution-tam-clarity/ （2026-07-15）
- Steam 收入分布（Gamalytic，71,000+ 游戏）：https://gamedevreports.substack.com/p/gamalytic-67-of-games-on-steam-earned （2023-10）
- Acquire.com 成交倍数报告（2,000+ 笔）：https://blog.acquire.com/acquire-com-biannual-acquisition-multiples-report-jan-2026/ （2026-02）

**AI 时代形态**
- MCP registry 规模：https://blog.modelcontextprotocol.io/posts/2025-11-25-first-mcp-anniversary/ ；https://modelcontextprotocol.io/registry/about
- GPT Store 分成状态：https://venturebeat.com/ai/openai-launches-gpt-store-but-revenue-sharing-is-still-to-come ；https://community.openai.com/t/what-is-the-status-with-gpt-store-revenue-share/839172
- Claude Skill 第三方市场（无成交数据）：https://www.agensi.io/learn/agent-skills-marketplace-sell-your-skills ；https://www.claudeskillsmarket.com/
- PromptBase 流量：https://www.similarweb.com/website/promptbase.com/ （2025-11）
- AI 工具死亡率：https://tooldirectory.ai/ai-graveyard ；https://dang.ai/ai-graveyard （2026-08）
- FTC 起诉 Click Profit：https://www.nbcnews.com/business/business-news/amazon-ai-scammers-duped-investors-millions-passive-income-scheme-ftc-rcna196931 （2025）
- Hugging Face 变现模式（**对个人模型/数据集作者无分成机制**）：https://research.contrary.com/report/hugging-face

**诊断框架 / 度量**
- CB Insights 创业失败原因（431 家）：https://www.cbinsights.com/research/report/startup-failure-reasons-top/ （2026-03-05）
- Melissa Perri《Escaping the Build Trap》：https://www.oreilly.com/library/view/escaping-the-build/9781491973783/ （O'Reilly, 2018）
- Rob Walling Stair Step Method：https://robwalling.com/essays/2015/03/26/the-stair-step-method-of-bootstrapping （2015-03-26）
- Sean Ellis 40% 测试与样本量要求：https://measuringu.com/product-market-fit-item/ ；https://learningloop.io/plays/product-market-fit-survey
- A/B 测试样本量门槛：https://www.invespcro.com/blog/calculating-sample-size-for-an-ab-test/ ；https://splitmetrics.com/blog/mobile-a-b-testing-sample-size/
- OpenView + Profitwell 免费转付费基准（1,000+ SaaS）：https://userpilot.com/blog/saas-average-conversion-rate/

**中文侧**
- B站 UP 主收入拆解：https://www.huxiu.com/article/554124.html （2022-05）；https://blog.csdn.net/HONGGE1688/article/details/148408666 （2025）
- 掘金小册分成比例：https://juejin.cn/post/6992048482441756709
- 知识星球头部案例：https://www.stcn.com/article/detail/3477342.html （证券时报）
- 中文自由职业接单市场（**无方法说明，仅作方向**）：https://zhuanlan.zhihu.com/p/1991483501489432478
- 小报童收录规模：https://xiaobot.osguider.com/

---

## 8. 明确的「查不到数字」清单

以下是任务要求覆盖、但我确实找不到可核数字的，**列出来而不是用感觉填充**：

1. **掘金小册 / 极客时间单个作者的销量和收入** —— 只查到掘金抽成 30%，作者收入零公开数据。
2. **小报童创作者的收入分布** —— 有第三方导航站收录 1,934 个专栏 / 2,105 位创作者，有"总收入排行榜"页面但未取到具体金额。
3. **卖 MCP server 的任何一笔公开收入** —— 生态有 2,000 个 server，收入金额零公开。
4. **卖 Claude Skill 的任何一笔公开收入** —— 没有官方市场，第三方市场无一家公开成交额或卖家分布。
5. **GPT Store 分成的总额和受益人数** —— OpenAI 从未公布，所有流传数字均为二手推算。
6. **AI automation agency 的收入分母统计** —— 只查到"月入 $50k+ 约占 0.1%"的转述，无方法说明，**不采用**。
7. **Hugging Face 对个人模型/数据集作者的分成** —— 查到的资料显示**不存在这样的机制**，作者只能靠曝光间接变现。
8. **中文圈"多少独立开发者产品收入为 0"的统计** —— 没有找到任何有分母的中文调查。所有中文收入数字都是自报或自媒体估算。
9. **知识星球平台整体的创作者收入分布** —— "99% 年收入 <10 万元"是自媒体说法，无方法，**不采用**。
10. **Chrome Web Store / VS Code 扩展 / Obsidian 插件的收入分布** —— 未找到任何有分母的统计。
