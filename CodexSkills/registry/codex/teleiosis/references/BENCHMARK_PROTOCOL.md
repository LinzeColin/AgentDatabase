# Benchmark Protocol

## 目标

把“控制面设计得很严”与“真实任务效果更好”分开验证。所有 outcome claim 必须来自首个 Candidate patch 前冻结的合同。

## 三个分轨

| Track | 对照 | 主要问题 |
|---|---|---|
| A - Optimization | Baseline / Darwin / Teleiosis | 同一预算下谁真正改善任务、安全和负迁移 |
| B - Productization | 原 Skill / Luban / Teleiosis | 谁改善触发、安装、理解、真实产物和采用任务 |
| C - Assurance | 无控制面 / Teleiosis | 谁更可靠冻结、阻断污染、恢复、打包、安装与回滚 |

三轨分别报告，不能合成一个冠军总分。

## 正式最小集

- 六个真实 Skill：文本推理 2、工具产物 2、高风险可逆 2；
- 每个 target：dev、validation、sealed holdout、adversarial、protected；
- sealed holdout 每 target 至少 20 条，正文保存在 Candidate 不可读外部路径；
- 每个 system × target × track × split 至少三次随机执行；
- 固定模型、runtime、工具权限、context、sampling、预算、judge、normalization 和 blind mapping；
- 保存全部 raw output、trace、失败、timeout 和 retry。

## 指标与成本真实性

Trigger、Task、Safety/authority、Truthfulness、Protected-task transfer、Cost、Latency、Reliability、Install/rollback、Portability、Maintenance、Evidence quality 分开报告。

```text
quality_efficiency = protected-safe outcome gain / model tokens
governance_burden = governance tokens + reviewer calls + human minutes
evidence_cost_ratio = governance_burden / accepted outcome gain
```

outcome gain 为零或负时返回 `NO_MEASURABLE_GAIN` 或 `REGRESSED`，不能制造正比率。

每条 result 的 token 与 monetary cost 必须分别声明 `MEASURED / ESTIMATED / UNKNOWN`。未知值使用 `null`；已知小计不能冒充完整总量。模型 token 未知时无法证明 equal-budget，benchmark 为 `INCOMPLETE`，不得支持 outcome claim。货币成本未知但没有冻结货币预算时，实验结构仍可有效，但成本证据只能是 `PARTIAL/UNKNOWN`。

## Claim policy

- `BENCHMARK_VALID` 只证明实验完整性；
- `OUTCOME_SUPPORTED` 还要求 Candidate 全部硬门 PASS、达到冻结增益阈值、无超预算和保护任务不可接受退化；
- 任一矩阵缺失、tree/hash 漂移、holdout 泄漏、token 预算不公平或 raw evidence 缺失都会阻断 outcome claim；
- fixture 只能证明 runner 工作，不能证明市场 superiority；
- fixture 或任何 `NOT_PROVEN/REGRESSED` 结果的 `selected_candidate` 必须为 `null`，可另外记录 `diagnostic_selected_candidate` 供调试，避免把 runner 诊断误读为正式获胜者。
