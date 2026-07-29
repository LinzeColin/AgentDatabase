# Field Validation

## 证据梯度

| 等级 | 定义 | 可证明什么 |
|---|---|---|
| SYNTHETIC | 模型/脚本/虚拟用户 | 技术可达性、边界、明显体验问题 |
| CONTROLLED_HUMAN | 内部或招募用户完成规定任务 | 可用性、理解、任务成功和恢复 |
| FIELD_OBSERVED | 真实用户、真实任务、真实环境 | 现实行为、采用、失败、留存和业务结果 |

## 阶段

Dogfood → 代表性任务 → Closed Beta → Canary → Segmented rollout。

每阶段必须有：

- hypothesis；
- target segment；
- primary metric；
- guardrail metrics；
- minimum evidence/exposure rule；
- rollback/kill-switch trigger；
- privacy masking；
- owner and decision date。

## 派生式 Field Gate

Field 完成门必须同时满足：

1. `field_experiment.json` 中至少一个实验为 `COMPLETED`；
2. 该实验声明 `FIELD_OBSERVED`；
3. 实验引用至少一个证据；
4. `evidence/index.json` 中这些证据自身也标为 `FIELD_OBSERVED`；
5. `field_feedback.json` 的 evidence class、证据和决策均完整。

`coverage_ledger.gates.field_validation_complete` 必须与上述派生结果一致；不一致直接 BLOCKED。

## 关联链

```text
user/session/feature flag
  → frontend event/replay
  → trace/span
  → service/log/error
  → database/world state
  → task/business outcome
```

## 禁止

- 用模型 Persona 的意见声称市场接受。
- 为追求样本量忽略用户代表性。
- 回放敏感字段不遮罩。
- 只看点击，不看任务结果和恢复。
- 指标变差仍继续扩大流量。
