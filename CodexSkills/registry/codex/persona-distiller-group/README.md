# 人物蒸馏专家团队与 canonical registry

本目录与 `persona-distiller/` 平级，承担两件事：

1. 保存人物蒸馏产物的唯一 canonical 登记与单 ZIP 完整交付备份；
2. 在调用专家团队时，按当前任务自动选择高相关人物专家并隔离复审、裁判和反证。

构建器在 [`../persona-distiller/`](../persona-distiller/)；canonical 路由规则在 [`CANONICAL-ROOT-ROUTE.md`](CANONICAL-ROOT-ROUTE.md)。

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
当前唯一登记：**6 个人物**。

| 人物 | 唯一身份 | 版本 | 选入原因 | 最值得蒸馏的特点 | 对用户的利益/帮助 | 应用场景 | 关键能力 | 完整 ZIP |
|---|---|---|---|---|---|---|---|---|
| Robert A. Kindler | `多重身份` | `0.0.0.1` | Unique career spanning elite M&A legal practice and senior investment-banking leadership.；Public evidence supports a transferable interface between document precision, board strategy and transaction execution. | dual legal-and-banker lens；separates strategic need from execution feasibility | Review M&A and governance decisions without collapsing legal and commercial dimensions.；Build board-ready decision memos with explicit authorization, risk and stop conditions. | M&A strategy and transaction screening；board and corporate-governance decision support | legal-commercial dual-track analysis；transaction lifecycle and stage-gate design | [ZIP](多重身份/robert-a-kindler/versions/0.0.0.1/robert-a-kindler-persona-distillation-delivery-v0.0.0.1.zip) |
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
