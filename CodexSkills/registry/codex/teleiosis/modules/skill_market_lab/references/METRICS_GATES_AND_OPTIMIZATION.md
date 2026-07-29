# 指标、Gate 与持续优化

## 目录

1. 指标树
2. 硬门
3. 效果与成本门
4. 决策规则
5. 优化闭环
6. 十视角
7. 停止与 Kill Criteria
8. 报告边界

## 1. 指标树

### 1.1 核心结果

| 指标 | 定义 | 优先级 |
|---|---|---|
| success_rate | 是否满足冻结 Oracle | 最高 |
| mean_score | 0–1 任务质量 | 高 |
| acceptance_rate | 外部验收是否接受 | 高 |
| completion_rate | 真实用户完成 | 高 |
| protected_success_delta | 关键任务相对 Baseline 差异 | 硬门 |

### 1.2 用户和市场

- 人工修正秒数；
- 重试、撤销、绕过、放弃；
- 复用意愿和实际复用；
- PR 合并、交付接受；
- 付费价值或节省区间；
- 投诉、事故和回滚。

### 1.3 资源

- Token；
- 费用；
- p50/p95 时延；
- 工具调用；
- 并发、吞吐与资源；
- 维护文件数、依赖和运行复杂度。

### 1.4 质量与治理

- exact identity coverage；
- Requirement→Oracle→Task→Evidence 追踪率；
- sealed holdout 泄漏；
- Oracle mutation 判别力；
- flake；
- 隐私、授权和安全事件；
- 可回退率与恢复时间。

## 2. 硬门

下列结果不能被平均分补偿：

```text
identity_mismatch
holdout_leak
oracle_drift
blind_map_leak
safety_violation
privacy_leak
unauthorized_side_effect
data_corruption
severe_market_incident
critical protected-task regression
```

任何 blocking code 触发：

- `BLOCKED`：身份、证据、权限或独立性不足，无法可靠裁决；
- `REVERT`：已证明 Candidate 引入回归；
- Canary 中立即停止新流量并恢复 Baseline。

## 3. 效果与成本门

### 3.1 默认比较顺序

1. Candidate vs Baseline；
2. Candidate vs No Skill；
3. Candidate vs 真实竞品；
4. Candidate vs Ablation；
5. 保护任务与主要切片；
6. 成本、时延和维护负担；
7. 真实市场证据。

没有 Baseline 时，以 No Skill 为主比较，但在报告中明确降低版本替换结论强度。

### 3.2 建议冻结字段

```json
{
  "min_paired_tasks": 20,
  "min_success_delta": 0.02,
  "min_score_delta": 0.02,
  "max_protected_success_regression": 0.0,
  "max_cost_increase_ratio": 0.25,
  "max_latency_increase_ratio": 0.30,
  "min_market_events_per_arm": 20,
  "min_market_completion_delta": 0.0,
  "min_market_acceptance_delta": 0.0,
  "max_market_edit_increase_ratio": 0.25,
  "require_market_comparator": true,
  "require_positive_ci": false
}
```

这些只是模板，不是所有 Skill 的通用真理。首次 Candidate 修改前按任务风险和最小有意义差异冻结。

市场门以 Candidate 与冻结主 Comparator 分别计数，不使用全实验总事件数。优先按相同 `task_id` 形成配对市场差异；缺少配对任务时可报告独立比例差异，但不得绕过每臂最小样本、共同证据等级和精确运行身份门。

### 3.3 不确定性

`require_positive_ci=true` 时，Candidate 与主比较臂的成功率和评分配对 bootstrap 区间下界必须同时大于 0。对小样本、高相关任务或关键发布，使用外部统计 Adapter 进行 cluster bootstrap、置换检验或功效分析。

## 4. 决策规则

| Decision | 触发 |
|---|---|
| PROMOTE | 所有硬门、效果、保护任务、预算、证据等级和市场门通过 |
| KEEP_BASELINE | Candidate 未达到最小收益或成本/时延不划算，但没有严重回归 |
| REVERT | Candidate 已证明产生关键或清晰负迁移 |
| REHEAT_REQUIRED | 样本、不确定性、市场等级或新事实不足，需要新实验 |
| BLOCKED | 身份、授权、证据、独立性或硬门无法满足 |

`PROMOTE` 只覆盖冻结 Subject 与范围。实验室 PROMOTE 不等于生产发布，L5 PROMOTE 不等于 L6/L7 市场成熟。

## 5. 优化闭环

```text
失败/机会证据
→ 最小复现与切片
→ 可证伪假设
→ 独立 Candidate change set
→ 五臂配对实验
→ 硬门与 Pareto
→ KEEP / REVERT / NO_CHANGE
→ 真实市场复验
```

`plan-next` 只生成结构化优化计划，不修改正式 Skill。每项计划必须包含：

- 证据引用；
- 假设；
- 最小变更范围；
- Acceptance；
- 回滚；
- 是否阻断；
- 重跑任务闭包。

### 5.1 优先级

1. P0/P1 安全、隐私、身份、数据和保护任务；
2. 真实市场失败；
3. 核心成功率和外部接受；
4. 成本与时延；
5. UX、维护和未来适应；
6. 非关键美化进入 Backlog。

### 5.2 避免错误优化

禁止：

- 看到结果后改 Gate；
- 把 Candidate 的解释写进评委 Prompt；
- 为通过 holdout 增加题目特定规则；
- 通过更多 Token 掩盖机制缺陷；
- 删除失败或只保留最佳 trial；
- 用长 Prompt 代替确定性脚本和 Schema；
- 自动将真实用户负反馈解释为用户错误。

## 6. 十视角

每轮正式完善覆盖十个正交视角：

1. 战略目标、用户、问题、价值与 Kill Criteria；
2. 目标仓、权威源、历史和复用；
3. 产品范围、非目标、流程与 UX；
4. 架构、接口、依赖与 Walking Skeleton；
5. 数据、Schema、幂等、迁移与恢复；
6. 安全、权限、隐私、供应链和法律；
7. 容量、成本、性能、可靠性与降级；
8. Acceptance、Oracle、压力、故障与回滚；
9. Fresh Builder 冷启动与最后一公里；
10. 独立反证、范围污染和封包完整性。

每个视角输出：新增机制或事实、Finding、改变制品与 hash、Developer Burden Delta、`KEEP/REVERT/NO_CHANGE`、剩余 P0/P1。

## 7. 停止与 Kill Criteria

### 7.1 当前 run 停止

- 达到预算或轮次上限；
- 连续两轮无新机制、无新 P0/P1、无 Developer Burden Reduction；
- 边际收益转负；
- 需要真实市场、权限或独立评审，继续实验室运行不能改变决定；
- 硬门不可恢复；
- 测试终点开始漂移。

### 7.2 Skill Kill Criteria

考虑 `REPOSITION / MERGE / RETIRE`，当：

- 相对 No Skill 长期无增益；
- 成本和维护负担持续超过收益；
- 真实用户不复用、不接受或绕过；
- 成熟同行已覆盖且薄 Adapter 更优；
- 安全或数据风险无法在合理成本内控制；
- Skill 只对公开测试过拟合；
- 触发错误率高于实际帮助。

退役也要保留版本、证据、替代方案和恢复路径。

## 8. 报告边界

报告必须区分：

- **事实**：直接来自冻结结果和真实事件；
- **推断**：由事实支持但尚未直接验证；
- **建议**：下一步动作；
- **未知**：缺少权限、数据、环境或独立性。

禁止宣传：

- “通过十万条模拟，所以市场验证”；
- “总体 95 分，所以没有安全风险”；
- “一个客户喜欢，所以有产品市场契合”；
- “哈希一致，所以来源可信”；
- “角色分离同模型，所以是六个独立 SubAgent”。
