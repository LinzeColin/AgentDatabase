# Canonical root route — 人物蒸馏专家团队

本文件是团队选择与角色隔离的最高优先级人读规则。候选事实来自 `team-index.json`；人物语义来自各自 `team-card.json`；版本与哈希来自 `registration.json`。三者冲突时停止并运行 `scripts/validate_group.py`，不得猜测。

## 当前 canonical roster

<!-- PERSONA-REGISTRY:START -->
当前唯一登记：**28 个人物**。

| 人物 | 唯一身份 | 版本 | 场景 | 关键能力 | 准备度 |
|---|---|---|---|---|---|
| Anne Mulcahy | `创业经营家` | `0.0.0.1` | Enterprise turnaround and cash-constrained operating plans；Customer trust recovery and B2B service-system redesign | Crisis operating cadence and multi-signal scorecards；Selective cost reduction with future-capability fences | `ready` |
| Reed Hastings / 里德·哈斯廷斯 | `创业经营家` | `0.0.0.1` | Company strategy and business-model transition；Organization culture and talent-system design | Self-disruptive strategy and staged migration；High-talent organizational operating systems | `ready` |
| Tim Cook | `创业经营家` | `0.0.0.1` | enterprise strategy；operations and supply resilience | enterprise operating system design；supply-chain and execution review | `ready` |
| 路易斯·郭士纳 / Louis V. Gerstner Jr. | `创业经营家` | `0.0.0.1` | 成熟企业危机稳定与九十天计划；B2B 客户导向战略和服务化转型 | 危机事实底板与转型排序；端到端客户价值和企业边界分析 | `ready` |
| Aswath Damodaran | `多重身份` | `0.0.0.1` | 上市与非上市公司估值；高增长、亏损或复杂公司的情景分析 | 叙事到收入、利润、再投资、风险和终值的量化映射；透明 DCF、相对定价和风险溢价分析 | `ready` |
| Ben Horowitz | `多重身份` | `0.0.0.1` | strategy-decision；leadership-organization | 和平/战时情境诊断与危机优先级收敛；创始人、CEO 与高管岗位匹配判断 | `ready` |
| Charlie Munger | `多重身份` | `0.0.0.1` | Company and acquisition analysis with current filings and valuation data.；Capital allocation, portfolio review, and downside stress testing. | Business-quality and opportunity-cost analysis.；Inversion-led risk identification and lollapalooza-effect red teaming. | `ready` |
| Chip Huyen | `多重身份` | `0.0.0.1` | AI/ML system architecture and production-readiness review；Foundation-model application strategy, evaluation, and feedback design | End-to-end AI/ML system design；Evaluation, monitoring, and feedback-loop design | `ready` |
| David Packard | `多重身份` | `0.0.0.1` | Company strategy and product-field selection；Leadership, organization design and management systems | Contribution-gated opportunity screening；Management-by-objectives operating design | `ready` |
| Edward O. Thorp（爱德华·索普） | `多重身份` | `0.0.0.1` | 量化或基本面投资方案审查；研究假设、实验与原型设计 | 状态变量建模与判别实验；概率优势、Kelly仓位与破产风险 | `ready` |
| Kent Beck | `多重身份` | `0.0.0.1` | TDD and test-strategy design；Refactoring and evolutionary architecture review | Software design and refactoring economics；Test-driven development and feedback-loop design | `ready` |
| Martin Fowler / 马丁·福勒 | `多重身份` | `0.0.0.1` | 软件架构与微服务/单体取舍评审；重构、技术债与遗留系统渐进迁移 | 小步保持行为的重构和迁移规划；架构收益、成本、前置条件和失败模式分析 | `ready` |
| Michael J. Mauboussin | `多重身份` | `0.0.0.1` | 公司研究与价格隐含预期分析；资本配置、并购、回购和再投资评估 | Expectations Investing / reverse DCF；ROIC与资本成本驱动的价值创造分析 | `ready` |
| Robert A. Kindler | `多重身份` | `0.0.0.1` | M&A strategy and transaction screening；board and corporate-governance decision support | legal-commercial dual-track analysis；transaction lifecycle and stage-gate design | `ready` |
| Sam Walton | `多重身份` | `0.0.0.1` | Retail and multi-site strategy；Inventory and supply-chain diagnosis | Unit-economics flywheel mapping；Store-cluster and distribution-density planning | `ready` |
| Simon Willison | `多重身份` | `0.0.0.1` | 技术方案与代码变更审查；coding-agent 工作流设计与评测 | Python/SQLite/CLI 开源工程工作系统；测试驱动、可回退、可审查的变更与发布 | `ready` |
| Barbara Liskov | `技术工程师` | `0.0.0.1` | research-problem-solving；technical-architecture | 数据抽象与行为规格；模块化与局部推理 | `ready` |
| Howard Marks | `投资资本家` | `0.0.0.1` | 公司与证券研究；组合风险审查 | 价格—价值与隐含预期分析；风险分布和压力测试 | `ready` |
| Joel Greenblatt | `投资资本家` | `0.0.0.1` | 公司研究与估值备忘录；特殊情形研究计划 | 现金流与资本回报驱动的企业估值；结构性错价诊断 | `ready` |
| Nick Sleep | `投资资本家` | `0.0.0.1` | 公司与商业模型研究；长期投资决策与组合复盘 | 终点—机制—概率分析；规模经济共享与客户互惠飞轮识别 | `ready` |
| Seth Klarman | `投资资本家` | `0.0.0.1` | 公司与证券研究；投资委员会备忘录 | 基本面估值与下行分析；催化剂和时间路径设计 | `ready` |
| Warren Buffett | `投资资本家` | `0.0.0.1` | 公司研究与价值—价格判断；企业资本配置和回购/并购决策 | 公开公司商业质量与长期经济性分析；内在价值区间、回购与整企收购初筛 | `ready` |
| 李录 Li Lu | `投资资本家` | `0.0.0.1` | 公司研究与商业质量评估；资本配置、组合风险和仓位框架 | 企业所有权、能力圈、安全边际和永久损失的一体化分析；高质量复利企业、管理层与长期增长跑道判断 | `ready` |
| Beth Wilkinson | `政治法律家` | `0.0.0.1` | governance-legal；communication-negotiation | 复杂事实记录压缩与结果敏感争点识别；审判、调查与制度风险结构化 | `ready` |
| Evan R. Chesler | `政治法律家` | `0.0.0.1` | governance-legal；strategy-decision | 高风险商事诉讼框架与庭审准备；复杂事实和科学材料的非专家转译 | `ready` |
| H. Rodgin Cohen | `政治法律家` | `0.0.0.1` | governance-legal；strategy-decision | 银行监管、控制权与重大交易门槛结构化；系统性风险、流动性、信心传染与失败处置分析 | `ready` |
| Scott A. Barshay | `政治法律家` | `0.0.0.1` | governance-legal；strategy-decision | 复杂M&A目标、结构、流程与路径设计；董事会授权、治理和重大事项决策框架 | `ready` |
| Theodore V. Wells Jr. | `政治法律家` | `0.0.0.1` | governance-legal；strategy-decision | 复杂商事、证券和白领刑事争议的中心理论与证据矩阵；证明责任、举证与当事人作证的阶段性决策 | `ready` |
<!-- PERSONA-REGISTRY:END -->

## 1. 内部身份分类

从用户的当前任务推断一个主身份，可附带次身份。不要让用户选择菜单。

| 身份目录 | 优先任务信号 |
|---|---|
| `技术工程师` | 科研、工程、架构、实验、诊断、实现、质量 |
| `创业经营家` | 创业、经营、组织、增长、产品市场、资源配置、危机 |
| `投资资本家` | 投资、估值、组合、资本、风险预算、商业分析 |
| `开发设计家` | 软件开发、产品、设计、创意、写作制作、体验与审美 |
| `思想教育家` | 思想、教育、学习、写作、训练、传播、长期判断 |
| `政治法律家` | 法律、政策、治理、制度、诉讼、谈判、公共风险 |
| `多重身份` | 两个以上身份都对结果有实质影响，不能安全压成单一身份 |

分类只是候选检索入口。最终选择仍受能力、场景、证据、边界和互补性约束。

## 2. 场景识别

从任务中选择最贴近的主场景，并允许一个次场景：

- `research-problem-solving`
- `strategy-decision`
- `general-agentic-work`
- `product-creation`
- `investment-business`
- `leadership-organization`
- `governance-legal`
- `communication-negotiation`
- `teaching-learning`
- `red-team-risk`

人物自己的专用场景可以参与匹配，但不能覆盖硬边界。

## 3. 候选评分

满分 100：

- 身份匹配：25
- 场景匹配：25
- 关键能力与证据准备度：20
- 对用户的明确价值：15
- 与已选角色的互补性：10
- 研究时效：5

扣分项：

- `readiness` 不是 `ready`：排除；
- 命中能力禁区或硬边界：排除；
- 证据状态未知但任务依赖该能力：至少扣 20，必要时排除；
- 与已选人物高度重复且没有新增角度：扣 10–25；
- 当前事实高度时效敏感而没有独立核验计划：扣 10–30。

## 4. 团队规模与组成

总角色数为 5–20，默认 7–10。

必需控制角色：

1. `independent-reviewer`：检查遗漏、证据链、可执行性和边界；
2. `decision-judge`：按预先声明标准对密封候选作最终裁决；
3. `counterevidence-analyst`：寻找最强反证、替代解释和失败条件。

这些控制角色是中立功能协议，不绑定任何人物模型。正向主力优先使用高分人物专家；候选不足时才用 `evidence-researcher`、`execution-planner`、`synthesis-lead` 等中立正向角色补足。

## 5. 隔离顺序

```text
任务与证据包
  → 正向人物专家并行/独立形成方案
  → 中立反证分析（只看任务、证据与候选）
  → 中立独立复审（不参与原方案）
  → 中立裁判（密封输入、预先评分标准）
  → 综合交付与事实核验
```

同一人物或同一上下文不得兼任其方案的复审与裁判。若宿主不能启动独立 agent，使用串行密封上下文，并明确独立性较弱。

## 6. 低库存与停止条件

- 没有相关且 `ready` 的人物：返回 `insufficient_roster`，不得用不相关名人凑数。
- 只有少量人物：保留这些正向专家，用中立正向角色和三个控制角色补足最低 5 人。
- 高风险任务缺少当前一手事实或有责任专业人员：只交付分析与验证计划。
- 登记、哈希或版本不一致：停止路由，先修复 registry。
- 团队规模、角色隔离或至少一复审/一裁判/一反证无法满足：不得声称已完成专家团队流程。
