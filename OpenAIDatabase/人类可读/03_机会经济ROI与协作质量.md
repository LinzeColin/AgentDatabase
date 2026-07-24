# 03 机会发现、经济代理、ROI 与协作质量

> 合并版本：`v0.0.0.1`。以下源文档严格按原目录顺序串联；正文仅更新因合并失效的文件路径，并增加稳定锚点、来源边界与自动生成区块。

> 范围：机会发现、Personal Economic Proxy、Information ROI、What-If 与 Agent 协作质量。

## 本卷源文件映射

| 顺序 | 原文件 | 本文件锚点 | 类型 |
|---:|---|---|---|
| 1 | 15_机会发现与为什么不是现在卡片.md | [src-15-opportunity-discovery](#src-15-opportunity-discovery) | 静态原文 |
| 2 | 16_PersonalEconomicProxy公式说明.md | [src-16-personal-economic-proxy](#src-16-personal-economic-proxy) | 静态原文 |
| 3 | 17_InformationROI与VisualROIGate说明.md | [src-17-information-roi](#src-17-information-roi) | 静态原文 |
| 4 | 18_FormulaWhatIf配置预览说明.md | [src-18-formula-what-if](#src-18-formula-what-if) | 静态原文 |
| 5 | 19_Agent协作质量指标说明.md | [src-19-agent-collaboration-quality](#src-19-agent-collaboration-quality) | 静态原文 |

---

<!-- BEGIN SOURCE: src-15-opportunity-discovery; original=15_机会发现与为什么不是现在卡片.md; baseline_sha256=2b9dc56ed3e8181eacf076ce3cc30ad975baaccb6d9e4932bb3bfe3adfa4cddd -->
<a id="src-15-opportunity-discovery"></a>
# 15 机会发现与为什么不是现在卡片

## 结论

当前 S06 P3 已完成。任务 ID 为 `MA-V12-S06P3`，验收 ID 为
`ACC-MA-V12-S06P3`，状态为
`phase_s06_p3_opportunity_discovery_completed_pending_s06_review`。

机会发现输出位于
`data/derived/behavior_intelligence/opportunities.json`。它把 S05 行为事件、
S06 P1 行为簇和 S06 P2 低价值循环候选合并成候选机会，不把机会写成必须马上做的任务。

## 输出是什么

- 候选机会：可自动化、可产品化、可模板化、可复利、应该暂缓。
- 为什么不是现在：每条机会都有一张卡片，说明暂缓、先降级或先验证的理由。
- 证据引用：每条候选机会都带 `evidence_refs`，并可回到 event、cluster 或 low-value loop。
- 下一步：每条机会只给一个最小 next step，不生成压力清单。

## 为什么不是现在

S06 P3 的目标不是把机会列表做成无限待办。为什么不是现在 卡片用于记录：

- 当前证据是否足够。
- 是否存在重复返工、过度优化、scope creep 或讨论未落地。
- 是否应该先做更小验证。
- 是否应该暂缓到后续 review 再决定。

## 边界

- 不接外部经济数据库。
- 不输出心理诊断。
- 不修改 raw。
- 不生成无穷压力清单。
- 不上传 GitHub main。
- 不进入 S06 Review。

下一步只允许进入 S06 Review。
<!-- END SOURCE: src-15-opportunity-discovery -->

---

<!-- BEGIN SOURCE: src-16-personal-economic-proxy; original=16_PersonalEconomicProxy公式说明.md; baseline_sha256=ac600922c1e5dc3110fc1b93171ab25f45ae369e8400466dcaccb568e5cc8549 -->
<a id="src-16-personal-economic-proxy"></a>
# 16 Personal Economic Proxy 公式说明

## 结论

S07 P1 已完成。任务 ID 为 `MA-V12-S07P1`，验收 ID 为
`ACC-MA-V12-S07P1`，状态为
`phase_s07_p1_economic_proxy_completed_pending_s07_p2`。

本阶段用内部派生数据生成 Personal Economic Proxy。它把 S06 的主题簇、低价值循环和机会线索转换成六个可解释分数：时间节省、复用价值、返工成本、机会分、技能复利和自动化/增强比例。

公式来源是 `机器治理/参数与公式/personal_economic_proxy.v1_2_s07_p1.json`。
输出是 `data/derived/economic_proxy/personal_economic_proxy.json`。
下一步只允许进入 S07 P2。

## 六个分数

| 分数 | score_key | 含义 | 公式来源 |
|---|---|---|---|
| 时间节省 | `time_saved_proxy` | 估算自动化、模板化、产品化和减少返工可能节省的重复工作时间。 | `FORM-MA-V12-S07P1-001` |
| 复用价值 | `reuse_value_proxy` | 判断哪些主题簇和机会适合沉淀为模板、脚本、validator 或产品入口。 | `FORM-MA-V12-S07P1-002` |
| 返工成本 | `rework_cost_proxy` | 衡量低价值循环和行动半衰期带来的返工成本信号。 | `FORM-MA-V12-S07P1-003` |
| 机会分 | `opportunity_score_proxy` | 使用 S06 候选机会分数和证据密度评估可行动程度。 | `FORM-MA-V12-S07P1-004` |
| 技能复利 | `skill_compounding_proxy` | 衡量跨时间重复出现的能力或工作流是否值得固化为长期复利资产。 | `FORM-MA-V12-S07P1-005` |
| 自动化/增强比例 | `automation_enhancement_ratio_proxy` | 区分更适合自动化的候选和更适合增强、模板化或产品化的候选。 | `FORM-MA-V12-S07P1-006` |

## 限制

- 这是内部 proxy，不是精确收入预测。
- 这不是财务建议，不用于收入、薪资、投资或商业价值承诺。
- 本阶段不接入外部经济数据库；外部经济数据库只保留 v2 接口占位。
- 本阶段不实现 S07 P2 的信息 ROI gate。
- 本阶段不实现 S07 P3 的 Formula What-if Simulator UI。
- 本阶段不修改 raw。

Machine-readable boundary summary: Memory Atlas v1.2 S07 P1 Personal Economic Proxy; MA-V12-S07P1; ACC-MA-V12-S07P1; phase_s07_p1_economic_proxy_completed_pending_s07_p2; validate:v1.2-s07-p1; personal_economic_proxy.v1_2_s07_p1.json; personal_economic_proxy.json; time_saved_proxy; reuse_value_proxy; rework_cost_proxy; opportunity_score_proxy; skill_compounding_proxy; automation_enhancement_ratio_proxy; pending S07 P2; No GitHub main upload in this phase; No remote push in this phase; No raw mutation in this phase; No external economic database; No precise income prediction; No S07 P2 information ROI gate; No S07 P3 what-if UI.
<!-- END SOURCE: src-16-personal-economic-proxy -->

---

<!-- BEGIN SOURCE: src-17-information-roi; original=17_InformationROI与VisualROIGate说明.md; baseline_sha256=707858a2e53b540dfaf3aa40ddc5ccf292fd4fffb9a22e3ce9bbe658c4862654 -->
<a id="src-17-information-roi"></a>
# Information ROI 与 Visual ROI Gate 说明

S07 P2 已完成。任务 ID 为 `MA-V12-S07P2`，验收 ID 为
`ACC-MA-V12-S07P2`，状态为
`phase_s07_p2_information_roi_completed_pending_s07_p3`。

本阶段定义每个 insight、card、chart 的 Information ROI，并实现轻量
Visual ROI Gate。核心规则是：没有决策价值的图表不进 P0。

## 产物

- 公式配置：`机器治理/参数与公式/information_roi.v1_2_s07_p2.json`
- Visual ROI Gate 配置：`机器治理/可视化配置/visual_roi_gate.v1_2_s07_p2.json`
- 派生输出：`data/derived/information_roi/information_roi_gate.json`
- 生成脚本：`scripts/build_memory_atlas_information_roi.py`
- 运行入口：`python scripts/atlasctl.py analyze --stage information-roi`
- 审计入口：`python scripts/atlasctl.py audit --check visual-roi`
- Validator：`validate:v1.2-s07-p2`

## 如何读

Information ROI 使用内部 derived 数据评估内容是否值得占据决策视图。每个 ROI item
都保留 `formula_id`、`formula_source`、`parameter_refs` 和 `evidence_refs`。

输出当前覆盖：

| 类型 | 数量 | 用途 |
|---|---:|---|
| insight | 15 | 判断哪些洞察有行动价值、复用价值和证据强度。 |
| card | 6 | 判断 Personal Economic Proxy score card 是否值得继续作为 P0 解释卡。 |
| chart | 10 | 判断 P0 图表是否有清晰 human question 和 action。 |

Visual ROI Gate 要求每个 P0 chart 同时具备：

- `human_question`：用户打开图表时要回答的真实问题。
- `action`：图表支持的下一步动作。
- `information_roi_score`：达到 P0 阈值。
- `visual_roi_gate_pass=true`。

当前 10 个 P0 visual 均通过 gate，`failed_p0_count=0`。被排除示例包括
`decorative_word_cloud` 和 `raw_schema_table`，原因是它们没有足够直接的决策价值。

## 边界

- 不接入外部经济数据库。
- 不是精确收入预测。
- 不构成财务建议。
- 不修改 raw。
- 不修改运行时 UI。
- 不实现 S07 P3 Formula What-if Simulator UI。
- No GitHub main upload in this phase。

下一步只允许进入 S07 P3。

Machine-readable boundary summary: Memory Atlas v1.2 S07 P2 Information ROI and Visual ROI Gate; MA-V12-S07P2; ACC-MA-V12-S07P2; phase_s07_p2_information_roi_completed_pending_s07_p3; validate:v1.2-s07-p2; information_roi.v1_2_s07_p2.json; visual_roi_gate.v1_2_s07_p2.json; information_roi_gate.json; insight; card; chart; 没有决策价值的图表不进 P0; pending S07 P3; No GitHub main upload in this phase; No remote push in this phase; No raw mutation in this phase; No external economic database; No precise income prediction; No S07 P3 what-if UI.
<!-- END SOURCE: src-17-information-roi -->

---

<!-- BEGIN SOURCE: src-18-formula-what-if; original=18_FormulaWhatIf配置预览说明.md; baseline_sha256=33d138a20e400d632730ca497760339cca3f36a7eddfbf9941c5adc35775382c -->
<a id="src-18-formula-what-if"></a>
# 18 Formula What-if 配置预览说明

## 结论

S07 P3 已完成 Formula What-if 的最小配置预览。任务 ID 为 `MA-V12-S07P3`，
验收 ID 为 `ACC-MA-V12-S07P3`，状态为
`phase_s07_p3_formula_what_if_completed_pending_s07_review`。

本阶段没有实现运行时 UI，也没有修改 active formula config。它只生成可审计的
配置预览输出，帮助查看不同权重假设下 Personal Economic Proxy 会怎样变化。
下一步只允许进入 S07 Review。

## 文件

- 配置：`机器治理/参数与公式/formula_what_if_defaults.v1_2_s07_p3.json`
- 输出：`data/derived/economic_proxy/formula_what_if_preview.json`
- Builder：`scripts/build_memory_atlas_formula_what_if.py`
- Validator：`apps/memory-atlas/scripts/validate_memory_atlas_v1_2_s07_p3.cjs`
- Review：`docs/reviews/memory_atlas_v1_2_s07_p3_formula_what_if.md`

## 可调整权重

Formula What-if 预览支持查看这些权重组合：

- 时间节省：`time_saved_weight`
- 复用价值：`reuse_value_weight`
- 机会价值：`opportunity_value_weight`
- 长期复利：`skill_compounding_weight`
- 自动化增强：`automation_alignment_weight`
- 返工成本：`rework_cost_weight`
- 低价值循环惩罚：`low_value_loop_penalty_weight`

输出中的每个 scenario 都包含中文说明、公式来源、参数引用、加权 proxy 分数、
相对 baseline 的变化、主要参数影响和 `parameter_change_proposal`。

## 边界

- `active_config_write=false`。
- `proposal_required_before_apply=true`。
- 不接入外部经济数据库。
- 不是精确收入预测。
- 不是财务建议。
- 不修改 raw。
- 不修改运行时 UI。
- No GitHub main upload in this phase。

## 如何查看

可使用：

```bash
python scripts/atlasctl.py analyze --stage formula-what-if --dry-run
python scripts/atlasctl.py audit --check formula-what-if
```

`--dry-run` 只返回预览，不写文件。正式生成的派生输出为
`data/derived/economic_proxy/formula_what_if_preview.json`。

## 下一步

下一步只允许进入 S07 Review。S07 Review 应复审 S07 P1 Personal Economic Proxy、
S07 P2 Information ROI 与 Visual ROI Gate、S07 P3 Formula What-if 配置预览是否
解释一致、边界一致、validator 可复跑，并继续保持 No GitHub main upload in this phase。
<!-- END SOURCE: src-18-formula-what-if -->

---

<!-- BEGIN SOURCE: src-19-agent-collaboration-quality; original=19_Agent协作质量指标说明.md; baseline_sha256=53a2bfb92c894f92d27f62ea0f998c4a37c6a1ab352e5e3b680d00fe1f043f2c -->
<a id="src-19-agent-collaboration-quality"></a>
# Agent 协作质量指标说明

## 当前结论

任务 ID：`MA-V12-S08P1`

验收 ID：`ACC-MA-V12-S08P1`

当前状态：`phase_s08_p1_collaboration_metrics_completed_pending_s08_p2`

S08 P1 已生成 Codex/Agent 协作质量报告：

`data/derived/agent_collaboration/agent_collaboration_quality_report.json`

下一步只允许进入 S08 P2。

## 这份报告回答什么

- 人负责什么：目标、范围、授权、是否 apply、业务优先级和高风险取舍。
- Agent 负责什么：在明确边界内执行可验证任务、保留证据、运行 validator、说明回滚路径。
- 返工来自哪里：repeated rework、decision debt、scope creep、evidence gap 和 action half-life。
- 哪些任务适合继续交给 Codex/agent：有清晰下一步、可测试输出、可回滚边界和足够证据的任务。
- 哪些必须人工判断：授权 apply、修改 active config、解释冲突证据、业务优先级和范围扩张。

## 指标

- `planning_clarity`：规划清晰度。
- `execution_clarity`：执行清晰度。
- `review_burden`：复审负担健康度，高分表示复审负担较低。
- `rework_count`：返工控制健康度，高分表示返工压力较可控。
- `scope_clarity`：范围清晰度。
- `testability`：可测试性。
- `rollbackability`：可回滚性。

这些分数是内部 proxy，不是对人或 agent 的人格判断，也不是任务价值的绝对排序。

## 边界

S08 P1 不创建多 agent 系统，不实现复杂 Delegation Contract UI，不执行 proposal apply，
不定义授权边界，不生成 stage flight recorder，不修改 raw。

授权边界进入 S08 P2。stage flight recorder 进入 S08 P3。

No GitHub main upload in this phase.
<!-- END SOURCE: src-19-agent-collaboration-quality -->
