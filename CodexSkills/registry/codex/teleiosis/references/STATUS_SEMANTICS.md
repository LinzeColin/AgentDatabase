# Status Semantics

Teleiosis 使用七个不可互相替代的状态域：

| 域 | 允许值 |
|---|---|
| `control_plane_status` | `PASS / FAIL / BLOCKED` |
| `benchmark_integrity_status` | `VALID / INVALID / INCOMPLETE / BLOCKED` |
| `outcome_status` | `SUPPORTED / NOT_PROVEN / REGRESSED / UNKNOWN` |
| `cost_evidence_status` | `MEASURED / PARTIAL / ESTIMATED / UNKNOWN` |
| `independent_review_status` | `PASS / BLOCKED / UNAVAILABLE / FAIL` |
| `engineering_release_status` | `INSTALLABLE / NOT_INSTALLABLE` |
| `formal_promotion_status` | `PASS / BLOCKED / FAIL` |

## 不可混淆的语义

- `CONTROL_PLANE_PASS` 只证明冻结、身份、Gate、安装与回滚按合同工作。
- `BENCHMARK_VALID` 只证明实验结构有效，不自动证明 Candidate 更好。
- `OUTCOME_SUPPORTED` 只允许来自冻结的真实任务、sealed holdout、同预算和无硬退化结果。
- `ENGINEERING_RELEASE_INSTALLABLE` 可以与 `OUTCOME_NOT_PROVEN`、`REVIEW_UNAVAILABLE` 和 `PROMOTION_BLOCKED` 同时成立。
- `INDEPENDENT_REVIEW_UNAVAILABLE` 不是 review failure，但必须阻断 formal promotion。

## 成本状态

成本摘要同时保存完整总量、已知小计和未知调用数：

```text
total_tokens
known_total_tokens
unknown_token_invocations
total_monetary_cost
known_monetary_cost
unknown_cost_invocations
currency
```

规则：

- 任一 token 调用未知时，`total_tokens=null`；已知部分只能写入 `known_total_tokens`。
- 任一货币成本未知时，`total_monetary_cost=null`；已知部分只能写入 `known_monetary_cost`。
- `PARTIAL` 必须至少有一个未知调用，且两个不完整总量保持 `null`；不能写成 0。
- `UNKNOWN` 不得含已知小计；若已有部分证据，应使用 `PARTIAL`。
- `MEASURED` 必须无未知调用，完整总量等于已知小计。
- `ESTIMATED` 必须无未知调用并记录 `estimation_methods`。

Formal PASS 要求：control PASS、benchmark VALID、outcome SUPPORTED、cost 为完整 `MEASURED` 或 `ESTIMATED`、independent review PASS、engineering INSTALLABLE。

顶层模糊 `PASS/FAIL` 被禁止；每个状态必须带理由与证据路径。Candidate tree 必须绑定真实 64 位 SHA-256。
