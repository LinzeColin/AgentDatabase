# 人物蒸馏专家团队与 canonical registry

本目录与 `persona-distiller/` 平级，承担两件事：

1. 保存人物蒸馏产物的唯一 canonical 登记与单 ZIP 完整交付备份；
2. 在调用专家团队时，按当前任务自动选择高相关人物专家并隔离复审、裁判和反证。

构建器在 [`../persona-distiller/`](../persona-distiller/)；canonical 路由规则在 [`CANONICAL-ROOT-ROUTE.md`](CANONICAL-ROOT-ROUTE.md)。
需要在readme文件登陆每个目录有多少个人物，一共有多少个人物。

## 七类唯一目录

| 唯一目录 | identity family |
|---|---|
| `技术工程师/` | `technical-engineer` |
| `创业经营家/` | `entrepreneur-operator` |
| `投资资本家/` | `investor-capital-allocator` |
| `开发设计家/` | `developer-designer` |
| `思想教育家/` | `thinker-educator` |
| `政治法律家/` | `political-legal` |
| `多重身份/` | `multi-identity` |

同一 canonical 人物只能登记一次。单身份进入对应目录；多重身份只进入 `多重身份/`。身份目录是内部登记与路由元数据，不是人物 Skill 的调用门槛。

## 每个人物的固定结构

```text
<身份>/<slug>/
├── registration.json
├── team-card.json
└── versions/
    └── <0.0.0.N>/
        └── <slug>-persona-distillation-delivery-v<0.0.0.N>.zip
```

每个版本目录只能有一个完整交付 ZIP。人物发布号按 canonical 人物独立、连续地使用 `0.0.0.1..0.0.0.999`；运行时调用不编号。

## 完整交付

完整交付 ZIP 必须包含一个不可变的运行时 Skill ZIP，以及安装、登记、团队卡、来源覆盖、评测、验证、provenance、边界和 handoff。人读报告可按项目需要增加，但不作为通用硬要求。任何缺失历史证据必须显式标为不可用，不能虚构。

完整规范见 [`references/delivery-package-standard.md`](references/delivery-package-standard.md)。

## 登记字段

`team-card.json` 至少登记截图所要求的五类基础信息：

- 选入原因 `selection_reasons`
- 最值得蒸馏的特点 `distillation_traits`
- 对用户的利益、作用和帮助 `user_value`
- 应用场景 `application_scenarios`
- 关键能力 `key_capabilities`

还须登记身份、可用性、能力边界、研究截止、最新版本和 artifact 引用。`registration.json` 是版本与双层哈希真源；`team-card.json` 是路由语义真源；`team-index.json` 和本 README 的登记表由脚本重建。

## 当前登记

<!-- PERSONA-REGISTRY:START -->
当前唯一登记：**35 个人物**。

| 唯一目录 | 人物数 |
|---|---:|
| `技术工程师/` | 2 |
| `创业经营家/` | 4 |
| `投资资本家/` | 6 |
| `开发设计家/` | 0 |
| `思想教育家/` | 0 |
| `政治法律家/` | 5 |
| `多重身份/` | 18 |
| **总计** | **35** |

| 人物 | 唯一身份 | 版本 | 选入原因 | 最值得蒸馏的特点 | 对用户的利益/帮助 | 应用场景 | 关键能力 | 完整 ZIP |
|---|---|---|---|---|---|---|---|---|
| Anne Mulcahy | `创业经营家` | `0.0.0.1` | Her most deeply documented and outcome-linked role is enterprise operator leading Xerox through crisis, recovery, growth, and succession.；Public evidence spans direct retrospectives, authored work, company filings, SEC records, customer systems, operating results, and board governance. | High-frequency crisis truth loops linking cash, customers, ownership, and short review cycles；Selective severity: stop legacy activity while fencing a small set of future capabilities | Turns ambiguous turnaround problems into accountable actions, metrics, review points, and stop conditions；Prevents indiscriminate cost cutting by separating stop and protect portfolios | Enterprise turnaround and cash-constrained operating plans；Customer trust recovery and B2B service-system redesign | Crisis operating cadence and multi-signal scorecards；Selective cost reduction with future-capability fences | [ZIP](创业经营家/anne-mulcahy/versions/0.0.0.1/anne-mulcahy-persona-distillation-delivery-v0.0.0.1.zip) |
| Reed Hastings / 里德·哈斯廷斯 | `创业经营家` | `0.0.0.1` | Co-founded and scaled Netflix across DVD, streaming, global expansion, originals, monetization shifts, and founder succession.；Published an unusually explicit and repeatedly revised organizational operating system with observable decisions and counterexamples. | Adaptability over process efficiency in high-change markets.；Talent density, candor, context-not-control, and single-owner decisions as an interdependent system. | Design a strategy that cannibalizes a weakening core before competitors do.；Build decision rights, dissent, talent, and information flow as one operating system. | Company strategy and business-model transition；Organization culture and talent-system design | Self-disruptive strategy and staged migration；High-talent organizational operating systems | [ZIP](创业经营家/reed-hastings/versions/0.0.0.1/reed-hastings-persona-distillation-delivery-v0.0.0.1.zip) |
| Tim Cook | `创业经营家` | `0.0.0.1` | Career evidence is deepest in operations, supply chain, enterprise stewardship, functional organization, capital allocation, and succession.；Public product, privacy, policy, and values evidence is material but should be routed as bounded facets rather than separate expert identities. | operational rigor；focus by subtraction | Turns a large public record into an executable decision and work system.；Includes counterevidence so the model does not collapse into corporate public relations. | enterprise strategy；operations and supply resilience | enterprise operating system design；supply-chain and execution review | [ZIP](创业经营家/tim-cook/versions/0.0.0.1/tim-cook-persona-distillation-delivery-v0.0.0.1.zip) |
| 路易斯·郭士纳 / Louis V. Gerstner Jr. | `创业经营家` | `0.0.0.1` | 公开证据最密集地覆盖大型成熟企业的危机接管、客户战略、组织整合和资源配置。；IBM 1993—2002 提供连续的决策、执行、财务结果和外部批评记录，可构建可反证模型。 | 把客户端到端结果置于产品和部门局部最优之上。；按生存、战略、增长和制度化顺序组织转型。 | 将模糊转型议题压缩成少数可执行选择和停止项。；诊断跨事业部组织为何无法为客户提供整体结果。 | 成熟企业危机稳定与九十天计划；B2B 客户导向战略和服务化转型 | 危机事实底板与转型排序；端到端客户价值和企业边界分析 | [ZIP](创业经营家/lou-gerstner/versions/0.0.0.1/lou-gerstner-persona-distillation-delivery-v0.0.0.1.zip) |
| Aswath Damodaran | `多重身份` | `0.0.0.1` | 公开身份明确以教学为先，并长期构建估值与公司金融课程体系；大量公司估值、风险数据与投资哲学材料支持资本配置分面 | 故事与数字双向约束；价值与价格严格区分 | 把模糊商业故事转换为可审计估值；识别市场价格已经隐含的预期 | 上市与非上市公司估值；高增长、亏损或复杂公司的情景分析 | 叙事到收入、利润、再投资、风险和终值的量化映射；透明 DCF、相对定价和风险溢价分析 | [ZIP](多重身份/aswath-damodaran/versions/0.0.0.1/aswath-damodaran-persona-distillation-delivery-v0.0.0.1.zip) |
| Ben Horowitz | `多重身份` | `0.0.0.1` | 公开材料同时覆盖 Loudcloud/Opsware 的经营危机、a16z 的机构设计与资本配置，以及两本管理著作形成的教学体系。；模型在公司战略、组织管理、创始人判断和风险投资之间存在可验证的共享决策内核，同时保留角色差异。 | 先区分和平与战时，再选择授权、速度、目标宽度和规则例外。；把最坏消息、最难对话和最不舒服反证优先上桌。 | 把模糊经营困境压缩成情境诊断、少量真实选项、明确所有者与决定日期。；为裁员、降职、创始人角色、公司政治和危机沟通提供直接但保留尊严的执行协议。 | strategy-decision；leadership-organization | 和平/战时情境诊断与危机优先级收敛；创始人、CEO 与高管岗位匹配判断 | [ZIP](多重身份/ben-horowitz/versions/0.0.0.1/ben-horowitz-persona-distillation-delivery-v0.0.0.1.zip) |
| Charlie Munger | `多重身份` | `0.0.0.1` | Long, unusually well-documented record across speeches, shareholder letters, filings, and live Q&A.；Distinctive integration of capital allocation, multidisciplinary judgment, incentives, and institutional design. | Multidisciplinary latticework with inversion, incentives, opportunity cost, and combined psychological effects.；Low-frequency, high-threshold action with strong emphasis on survival, liquidity, and durable business quality. | Turns vague strategic or investment questions into a short causal model, downside test, and decision trigger set.；Improves learning plans by linking models to cases, counterexamples, and falsification exercises. | Company and acquisition analysis with current filings and valuation data.；Capital allocation, portfolio review, and downside stress testing. | Business-quality and opportunity-cost analysis.；Inversion-led risk identification and lollapalooza-effect red teaming. | [ZIP](多重身份/charlie-munger/versions/0.0.0.1/charlie-munger-persona-distillation-delivery-v0.0.0.1.zip) |
| Chip Huyen | `多重身份` | `0.0.0.1` | A large first-party corpus links production AI engineering, system design, technical education, open-source artifacts, and one documented AI-infrastructure startup outcome.；The same decision patterns recur across courses, books, essays, interviews, code, and institutional records, allowing cross-context adjudication rather than voice imitation. | Frames AI work as an end-to-end iterative system rather than an isolated model.；Uses simple baselines and progressive complexity, with evaluation and feedback as gating mechanisms. | Produces production-minded AI architecture and review plans with explicit objectives, baselines, evaluation, monitoring, and rollback.；Turns fast-moving technical fields into navigable maps and learning paths without hiding uncertainty. | AI/ML system architecture and production-readiness review；Foundation-model application strategy, evaluation, and feedback design | End-to-end AI/ML system design；Evaluation, monitoring, and feedback-loop design | [ZIP](多重身份/chip-huyen/versions/0.0.0.1/chip-huyen-persona-distillation-delivery-v0.0.0.1.zip) |
| Christopher Manning | `多重身份` | `0.0.0.1` | Longitudinal public record spans formal linguistics, statistical NLP, neural methods, LLMs, evaluation, open tooling and graduate education.；Multiple independent artifact classes support a stable representation-first, measurement-first research method. | Representation and task definition before architecture novelty.；Graded, decomposed account of language understanding rather than binary slogans. | Turns broad AI questions into cheap, discriminative experiments and explicit go/no-go gates.；Prevents benchmark, fluency and scale from being misread as deployment readiness or full understanding. | NLP/LLM research strategy and experiment design；Technical architecture and benchmark review | Frame NLP/LLM research questions as measurable phenomena, representations, baselines and falsifiable experiments.；Review model architectures, objectives, datasets and benchmarks with error, calibration, factuality and transfer controls. | [ZIP](多重身份/christopher-manning/versions/0.0.0.1/christopher-manning-persona-distillation-delivery-v0.0.0.1.zip) |
| Dan Gelbart | `多重身份` | `0.0.0.1` | 跨光学、机械、热流体、医疗器械与增材制造的一手专利形成稳定技术工程主轴。；Creo 与 Rapidia 的公开轨迹支持有界创业经营分面，但组织与资本细节保持限制。 | 先利用物理效应，再增加机构与控制。；以反馈延迟衡量原型系统，偏好设计者直接构建与测量。 | 把模糊技术问题压缩成可在数小时或数天内证伪的实验。；用简单、可解释、可维护的结构替代不必要复杂度。 | 技术架构与故障诊断；实验与原型计划 | 跨物理域功能分解与误差路径建模；快速原型与直接测量闭环 | [ZIP](多重身份/dan-gelbart/versions/0.0.0.1/dan-gelbart-persona-distillation-delivery-v0.0.0.1.zip) |
| David Packard | `多重身份` | `0.0.0.1` | Packard has a substantial first-party management corpus and contemporaneous HP operating documents.；His decisions span company building, technical organization, public acquisition governance and long-horizon institutions, enabling cross-context validation. | Contribution before scale or imitation；Clear objectives with autonomy over methods | Turns broad strategy into objective, owner, boundary, stage-gate and feedback architecture.；Provides a rigorous operating lens for engineering-led companies and research institutions. | Company strategy and product-field selection；Leadership, organization design and management systems | Contribution-gated opportunity screening；Management-by-objectives operating design | [ZIP](多重身份/david-packard/versions/0.0.0.1/david-packard-persona-distillation-delivery-v0.0.0.1.zip) |
| Edward O. Thorp（爱德华·索普） | `多重身份` | `0.0.0.1` | 跨赌场、工程和资本市场反复展示同一套可检验的概率—实验—风险闭环。；公开一手论文、长访谈与机构档案密度高，可区分事实、稳定模式和晚期修正。 | 机制优先：把叙事改写为状态变量、收益函数和可证伪预测。；优势与暴露分离：对冲已知因子后才评价残余收益。 | 为不确定问题提供可复算的实验与决策模板。；为投资或商业分析提供成本后优势、仓位、尾部和退出框架。 | 量化或基本面投资方案审查；研究假设、实验与原型设计 | 状态变量建模与判别实验；概率优势、Kelly仓位与破产风险 | [ZIP](多重身份/edward-o-thorp/versions/0.0.0.1/edward-o-thorp-persona-distillation-delivery-v0.0.0.1.zip) |
| Kent Beck | `多重身份` | `0.0.0.1` | Four decades of inspectable software artifacts connect ideas to executable practice.；Public failures and adaptations reveal update behavior, not only polished doctrine. | Shrinks uncertainty through rapid, specific feedback.；Separates structural change from behavioral change to preserve intent and reversibility. | Produces executable plans with tests, baselines, rollback, and stopping rules.；Improves code and design reviews without reducing them to style imitation. | TDD and test-strategy design；Refactoring and evolutionary architecture review | Software design and refactoring economics；Test-driven development and feedback-loop design | [ZIP](多重身份/kent-beck/versions/0.0.0.1/kent-beck-persona-distillation-delivery-v0.0.0.1.zip) |
| Martin Fischer | `多重身份` | `0.0.0.1` | 公开资料将其稳定定位为 VDC 与集成设施工程研究者和教育者；技术工程与教学两条身份均有跨年代一手来源支持 | 从业主与使用者价值倒推技术和项目系统；同时建模产品、组织与流程 | 把模糊数字化愿景转成目标、指标、责任和试点门槛；审查 BIM、VDC、数字孪生、机器人和 AI 项目的真实作用机制 | VDC/BIM 战略与实施路线图；产品—组织—流程诊断 | 生命周期价值与业务目标建模；POP 系统分析 | [ZIP](多重身份/martin-fischer-stanford/versions/0.0.0.1/martin-fischer-stanford-persona-distillation-delivery-v0.0.0.1.zip) |
| Martin Fowler / 马丁·福勒 | `多重身份` | `0.0.0.1` | 公开作品跨三十年持续覆盖重构、架构、敏捷技术实践与企业软件设计。；第一方资料对工作方法、编辑准则、证据局限和职业边界有明确自述。 | 以未来变化成本解释设计与内部质量。；用小步、快速反馈和安全网管理复杂改变。 | 把抽象架构争论转化为可执行、可验证、可回滚的演进路径。；识别敏捷仪式与真实工程能力之间的缺口。 | 软件架构与微服务/单体取舍评审；重构、技术债与遗留系统渐进迁移 | 小步保持行为的重构和迁移规划；架构收益、成本、前置条件和失败模式分析 | [ZIP](多重身份/martin-fowler/versions/0.0.0.1/martin-fowler-persona-distillation-delivery-v0.0.0.1.zip) |
| Michael J. Mauboussin | `多重身份` | `0.0.0.1` | 适用于需要把估值、资本配置与决策科学放进同一分析框架的任务；在不确定性、概率、基准率和反馈方面拥有长期、跨来源一致的公开方法体系 | 从价格或现状反推隐含预期，而非先猜目标值；持续追问“与什么相比”并使用外部参考类 | 把模糊商业故事转换为可检验的价值驱动因素和情景；用基准率、贝叶斯更新和概率—赔率降低预测偏差 | 公司研究与价格隐含预期分析；资本配置、并购、回购和再投资评估 | Expectations Investing / reverse DCF；ROIC与资本成本驱动的价值创造分析 | [ZIP](多重身份/michael-mauboussin/versions/0.0.0.1/michael-mauboussin-persona-distillation-delivery-v0.0.0.1.zip) |
| Rich Hickey | `多重身份` | `0.0.0.1` | 其跨 Clojure、Datomic、core.async、transducers、spec 的公开材料呈现高度稳定的设计原则。；一手论文、官方文章、代码项目与演讲转录覆盖创建、演化、组织转型和商业退休/独立项目角色边界。 | 用精确定义先消除概念缠结；把不可变值、身份、状态与时间分开 | 在方案进入实现前发现结构性复杂度和不可逆契约。；把模糊争论转换为可比较、可反驳、可长期维护的决策记录。 | 软件与数据系统架构评审；语言、API 与库设计 | 把需求改写为问题、约束、非目标、替代方案与证伪条件；识别概念、职责、位置、时间和执行策略的缠结 | [ZIP](多重身份/rich-hickey/versions/0.0.0.1/rich-hickey-persona-distillation-delivery-v0.0.0.1.zip) |
| Robert A. Kindler | `多重身份` | `0.0.0.1` | Unique career spanning elite M&A legal practice and senior investment-banking leadership.；Public evidence supports a transferable interface between document precision, board strategy and transaction execution. | dual legal-and-banker lens；separates strategic need from execution feasibility | Review M&A and governance decisions without collapsing legal and commercial dimensions.；Build board-ready decision memos with explicit authorization, risk and stop conditions. | M&A strategy and transaction screening；board and corporate-governance decision support | legal-commercial dual-track analysis；transaction lifecycle and stage-gate design | [ZIP](多重身份/robert-a-kindler/versions/0.0.0.1/robert-a-kindler-persona-distillation-delivery-v0.0.0.1.zip) |
| Sam Walton | `多重身份` | `0.0.0.1` | Multi-unit operating systems with customer value, inventory, logistics, field feedback or frontline execution；Evidence-grounded strategy teaching that needs concrete operating mechanisms | Customer-value flywheel；Density-before-dispersion expansion | Converts broad growth ideas into measurable pilots and rollout gates；Connects pricing, turns, logistics and organization in one operating model | Retail and multi-site strategy；Inventory and supply-chain diagnosis | Unit-economics flywheel mapping；Store-cluster and distribution-density planning | [ZIP](多重身份/sam-walton/versions/0.0.0.1/sam-walton-persona-distillation-delivery-v0.0.0.1.zip) |
| Shreya Shankar | `多重身份` | `0.0.0.1` | A rare cross-domain record connecting production ML failures, data systems, human–AI interaction, open-source system building, and industry-facing AI evaluation.；Public materials span nearly a decade and multiple evidence forms, enabling longitudinal rather than style-only distillation. | User workflow and data pipeline are treated as the real unit of AI product design.；Evaluation criteria are discovered from actual outputs and refined with human feedback. | Design more reliable LLM and data applications without over-centering model choice.；Build task-specific evals, monitoring, and continual-improvement loops. | LLM application evaluation and error analysis；Unstructured document-processing architecture | End-to-end AI/ML system decomposition；Task-specific evaluation and validator design | [ZIP](多重身份/shreya-shankar/versions/0.0.0.1/shreya-shankar-persona-distillation-delivery-v0.0.0.1.zip) |
| Simon Willison | `多重身份` | `0.0.0.1` | 需要以可执行证据、测试和公开工作流审查软件与 AI 工程任务；需要把复杂技术解释为可运行示例、注释性报告和开放问题 | 测试、文档、issue、release notes 与 TIL 构成外部认知系统；从具体用户问题生长小而可组合的 CLI、SQLite 与插件工具 | 把模糊技术想法转成可验证的最小实现与发布闭环；为 AI 辅助编码建立测试、人工演练、provenance 和停止规则 | 技术方案与代码变更审查；coding-agent 工作流设计与评测 | Python/SQLite/CLI 开源工程工作系统；测试驱动、可回退、可审查的变更与发布 | [ZIP](多重身份/simon-willison/versions/0.0.0.1/simon-willison-persona-distillation-delivery-v0.0.0.1.zip) |
| Stephen E. Robertson | `多重身份` | `0.0.0.1` | BM25 与概率相关性框架的核心奠基者之一；跨理论、操作系统与共享评测的长期研究轨迹 | 显式定义事件空间与假设；优先简单稳健且排序等价的近似 | 审查搜索/排序方案的目标函数、假设与评测泄漏；建立 BM25 或其他可解释强基线并设计升级实验 | 信息检索与搜索架构评审；排序/过滤/告警实验设计 | 概率相关性与排序原则分析；BM25/BM25F 概念与工程取舍 | [ZIP](多重身份/stephen-e-robertson/versions/0.0.0.1/stephen-e-robertson-persona-distillation-delivery-v0.0.0.1.zip) |
| Barbara Liskov | `技术工程师` | `0.0.0.1` | 其公开技术证据横跨数据抽象、编程语言、类型、复制、拜占庭容错、信息流与事务，足以形成跨五十年的可执行工程模型。；原始论文、系统实现、基准、教材、直接访谈和外部反例能够同时约束能力、工作方法、表达与边界。 | 以客户端可观察行为定义抽象边界，再隐藏表示以获得局部推理。；在协议设计前固定故障模型，并把恢复、升级和角色变化作为一等状态。 | 把模糊技术问题压缩为可观察规格、不变量、失败模型和验证计划。；在复杂架构中找到能够删除状态、消息、权限和跨模块推理的抽象。 | research-problem-solving；technical-architecture | 数据抽象与行为规格；模块化与局部推理 | [ZIP](技术工程师/barbara-liskov/versions/0.0.0.1/barbara-liskov-persona-distillation-delivery-v0.0.0.1.zip) |
| R. Keith Mobley | `技术工程师` | `0.0.0.1` | 公开证据横跨设备机理、预测性维护、根因失效分析、工厂工程、维护管理和企业经营，可形成完整的工程决策链。；近期长访谈把技术、预算、组织、数据与全生命周期价值明确连接，适合处理工业资产可靠性和维护转型任务。 | 从全生命周期企业价值而非维修活动量定义问题；以正常状态—失效模式—forcing functions—证据验证组织诊断 | 把重复故障、模糊 PM 和告警噪声转成可验证的原因、阈值与控制动作。；把年度维护工作、资源、停机窗口和预算连接为可审计的五十二周系统。 | research-problem-solving；strategy-decision | 全生命周期资产价值与维护战略诊断；正常状态、失效模式和状态监测设计 | [ZIP](技术工程师/r-keith-mobley/versions/0.0.0.1/r-keith-mobley-persona-distillation-delivery-v0.0.0.1.zip) |
| Howard Marks | `投资资本家` | `0.0.0.1` | 公开职业轨迹、Oaktree 投资哲学与跨周期备忘录均以投资、风险和资本配置为核心；思想教育能力作为次级分面有充分写作与访谈证据，但不取代主投资身份 | 价格与价值分离，先审查市场隐含预期；以结果分布、永久损失和生存能力定义风险 | 把二元投资问题转换为可审计的赔率、风险和规模决策；在泡沫、信用、杠杆和资本配置中识别不可逆损失路径 | 公司与证券研究；组合风险审查 | 价格—价值与隐含预期分析；风险分布和压力测试 | [ZIP](投资资本家/howard-marks/versions/0.0.0.1/howard-marks-persona-distillation-delivery-v0.0.0.1.zip) |
| Joel Greenblatt | `投资资本家` | `0.0.0.1` | 职业核心与主要公开作品长期聚焦价值投资、特殊情形、相对价值和资本配置。；监管披露显示其持续承担组合管理与共同首席投资官职责。 | 企业现金流价值先于价格叙事；结构性错价与低竞争机会场域 | 把模糊投资观点转为可证伪的企业价值与错价机制；按研究深度、容量和行为约束选择组合结构 | 公司研究与估值备忘录；特殊情形研究计划 | 现金流与资本回报驱动的企业估值；结构性错价诊断 | [ZIP](投资资本家/joel-greenblatt/versions/0.0.0.1/joel-greenblatt-persona-distillation-delivery-v0.0.0.1.zip) |
| Nick Sleep | `投资资本家` | `0.0.0.1` | 公开一手合伙人信跨越完整投资周期，可观察理念演化与压力期行为；投资、治理和慈善资本配置形成可比较的长期决策轨迹 | 从短期路径转向长期终点与到达概率；把规模效率回馈客户形成强化循环 | 审查企业是否具备可持续复利机制；把价格波动与业务事实、概率变化分开 | 公司与商业模型研究；长期投资决策与组合复盘 | 终点—机制—概率分析；规模经济共享与客户互惠飞轮识别 | [ZIP](投资资本家/nick-sleep/versions/0.0.0.1/nick-sleep-persona-distillation-delivery-v0.0.0.1.zip) |
| Seth Klarman | `投资资本家` | `0.0.0.1` | 长期担任 Baupost CEO 与投资组合经理，职业事实与投资资本家身份直接匹配；公开材料对估值、组合、风险、现金、催化剂和组织流程提供了跨时期证据 | 下行优先而非波动恐惧；价格—价值—催化剂—时间四联模型 | 把模糊的“价值投资”转换为可执行承保清单；在买入前强制暴露永久损失和价值陷阱 | 公司与证券研究；投资委员会备忘录 | 基本面估值与下行分析；催化剂和时间路径设计 | [ZIP](投资资本家/seth-klarman/versions/0.0.0.1/seth-klarman-persona-distillation-delivery-v0.0.0.1.zip) |
| Warren Buffett | `投资资本家` | `0.0.0.1` | 六十年Berkshire资本配置、股东信和公开决策构成最强证据域；主身份可由年度信、监管文件、交易复盘和现场问答交叉验证 | 企业所有权视角与价格—价值分离；机会成本驱动的跨用途资本配置 | 把“长期价值投资”转成可执行门槛、停止条件和证伪清单；区分可复制决策结构与Berkshire不可复制的融资、规模和交易优势 | 公司研究与价值—价格判断；企业资本配置和回购/并购决策 | 公开公司商业质量与长期经济性分析；内在价值区间、回购与整企收购初筛 | [ZIP](投资资本家/warren-buffett/versions/0.0.0.1/warren-buffett-persona-distillation-delivery-v0.0.0.1.zip) |
| 李录 Li Lu | `投资资本家` | `0.0.0.1` | 公开职业主线是自1997年以来的投资机构创办、主基金管理与资本配置。；最密集、最可核的一手材料集中于价值投资、企业研究、仓位、风险与长期持有。 | 企业所有者视角而非价格追随；能力圈与智识诚实 | 把股票或商业问题转化为可证伪的企业经济性分析。；在不确定性下建立坏情景、反方、行动阈值和退出规则。 | 公司研究与商业质量评估；资本配置、组合风险和仓位框架 | 企业所有权、能力圈、安全边际和永久损失的一体化分析；高质量复利企业、管理层与长期增长跑道判断 | [ZIP](投资资本家/li-lu/versions/0.0.0.1/li-lu-persona-distillation-delivery-v0.0.0.1.zip) |
| Beth Wilkinson | `政治法律家` | `0.0.0.1` | 其公开职业证据覆盖复杂诉讼、调查、监管与机构治理，可为高风险事实判断提供可执行结构。；模型同时记录胜负、争议、能力禁区和当前性要求，适合担任正向法律问题解决者。 | 事实核心—暂定结案—反向补证的工作循环；把机构拆成权限、激励、信息与否决点，而非视作单一行为者 | 把庞杂卷宗压缩为少数真正影响结果的事实与程序问题。；在形成主方案的同时主动暴露反证、冲突、未知和验证路径。 | governance-legal；communication-negotiation | 复杂事实记录压缩与结果敏感争点识别；审判、调查与制度风险结构化 | [ZIP](政治法律家/beth-wilkinson/versions/0.0.0.1/beth-wilkinson-persona-distillation-delivery-v0.0.0.1.zip) |
| Evan R. Chesler | `政治法律家` | `0.0.0.1` | 其蒸馏模型把复杂诉讼、证人、可信度、团队和路径选择连成可执行系统。；能力表明确区分高置信、有限迁移和不可用领域，便于安全组队。 | 以可信度为中心处理不利证据，不用修辞替代记录；把审判、和解与上诉视作可更新的路径组合 | 为重大争议建立记录驱动、可信度优先的案件与证人策略。；比较审判、和解与上诉路径的约束、信息需求和失败代价。 | governance-legal；strategy-decision | 高风险商事诉讼框架与庭审准备；复杂事实和科学材料的非专家转译 | [ZIP](政治法律家/evan-r-chesler/versions/0.0.0.1/evan-r-chesler-persona-distillation-delivery-v0.0.0.1.zip) |
| H. Rodgin Cohen | `政治法律家` | `0.0.0.1` | 公开证据的主轴是银行监管、重大金融机构交易、系统性危机处置与制度设计。；模型具有可证伪的系统因果、程序与执行规则，并明确大型金融机构视角偏差和能力禁区。 | 把法律、监管、资产负债表、市场信心与公共合法性建成耦合系统；在预先定义权限和责任的前提下保留危机工具与执行顺序的弹性 | 为受监管金融机构的危机、交易或治理任务建立权限-系统风险-执行一体化框架。；把反对意见转化为带触发条件、责任主体、损失安排和验证指标的可执行替代方案。 | governance-legal；strategy-decision | 银行监管、控制权与重大交易门槛结构化；系统性风险、流动性、信心传染与失败处置分析 | [ZIP](政治法律家/h-rodgin-cohen/versions/0.0.0.1/h-rodgin-cohen-persona-distillation-delivery-v0.0.0.1.zip) |
| Scott A. Barshay | `政治法律家` | `0.0.0.1` | Public evidence is deepest in high-stakes M&A, activist defense, board governance and regulatory transaction strategy.；Direct statements expose a repeatable decision system: listen, map constraints, prepare the endgame and then move quickly. | 先听清客户与对手方约束，再设计可执行妥协；签约前倒推监管、诉讼、补救和退出终局 | 为复杂交易、治理冲突和监管不确定性建立可执行决策树。；把多方利益、证据、时间、授权和退出条件压缩成董事会级决策材料。 | governance-legal；strategy-decision | 复杂M&A目标、结构、流程与路径设计；董事会授权、治理和重大事项决策框架 | [ZIP](政治法律家/scott-a-barshay/versions/0.0.0.1/scott-a-barshay-persona-distillation-delivery-v0.0.0.1.zip) |
| Theodore V. Wells Jr. | `政治法律家` | `0.0.0.1` | 现有交付包含六路来源覆盖、胜诉与败诉样本、32 个评测案例和明确的能力禁区。；模型适合在高风险争议中担任证据、程序、叙事和团队协同的正向解决者。 | 以证明责任和中心理论组织证据，并在关键节点更新是否举证与是否作证；同时构造最强反证、替代解释和可推翻条件，避免胜诉幸存者偏差 | 把高风险争议压缩为证明责任、中心理论、证据缺口和阶段动作。；在法律、调查、专家证据、舆情和组织多战线之间建立统一决策接口。 | governance-legal；strategy-decision | 复杂商事、证券和白领刑事争议的中心理论与证据矩阵；证明责任、举证与当事人作证的阶段性决策 | [ZIP](政治法律家/theodore-v-wells-jr/versions/0.0.0.1/theodore-v-wells-jr-persona-distillation-delivery-v0.0.0.1.zip) |
<!-- PERSONA-REGISTRY:END -->

## 团队路由

默认选择 7–10 个角色，总数必须为 5–20：

- 主要角色是正向解决问题的人物专家；
- 至少 1 个中立独立复审；
- 至少 1 个中立最终裁判；
- 至少 1 个中立反证分析；
- 人物候选不足时可用中立研究、规划或综合角色补足，但不得虚构人物。

## 白箱披露（必填）
- 场景：`<任务场景>`
- 主要：`[中文姓名, 入选作用]` ×1+
- 复审：`[中文姓名, 入选作用]` ×1+
- 裁判：`[中文姓名, 入选作用]` ×1+
- 反证：`[中文姓名, 入选作用]` ×1+
- 角色总数：`5-20`

```bash
python3 scripts/route_team.py --task "任务描述"
```

## 维护

```bash
python3 scripts/verify_delivery.py path/to/delivery.zip
python3 scripts/rebuild_team_views.py
python3 scripts/validate_group.py
```

所有备份保存与同步均以本目录为唯一位置；`persona-distiller/` 不再保存人物 ZIP 或 7 类登记目录。
