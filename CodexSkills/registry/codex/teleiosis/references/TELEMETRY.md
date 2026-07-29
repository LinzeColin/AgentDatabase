# Telemetry and Governance Burden

每次外部调用必须有唯一 `invocation_id` 和不复用的 `attempt_id`，记录阶段、provider、model、runtime、adapter、开始/结束、latency、retry、token、货币成本和 human minutes。

- provider 返回 usage：`MEASURED`；
- 可复核公式估算：`ESTIMATED`；
- 无可靠数据：`UNKNOWN`，字段为 `null`，不能写 0；
- retry 的每次 attempt 只计算一次；
- evaluation、review、packaging、installation 和 recovery 成本不能从总成本中省略；
- p50/p95 与长尾 timeout 单独报告；
- 多货币没有冻结换算合同时禁止聚合。

## 部分未知不是零

当部分调用提供 usage、部分调用不提供时，聚合器输出：

```text
total_tokens = null
known_total_tokens = 已知调用小计
unknown_token_invocations = 未知调用数

total_monetary_cost = null
known_monetary_cost = 已知调用小计
unknown_cost_invocations = 未知调用数
```

这防止把“已知部分为零”误报为“全部成本为零”。状态摘要再次验证同一规则，避免下游手工 JSON 绕过 telemetry 聚合器。

`telemetry-aggregate` 检测 invocation/attempt 重复、retry 双算或漏算、未知值伪装为零及不兼容货币。真实 benchmark 中 token 证据未知会令 equal-budget 完整性变为 `INCOMPLETE`；未知货币成本在无冻结成本上限时只降低成本证据状态，不伪造零成本。
