# Operator Run Modes

| Run mode | 可输出 | 不可输出 |
|---|---|---|
| `diagnostic` | 结构、研究、预检、成本估计、阻塞原因 | formal PASS、自动 promotion |
| `engineering` | Candidate、真实 eval、installable evidence | 无外部独立复审时的 formal promotion |
| `formal` | 全部 seal、真实任务、外部 2×6+1、promotion verdict | 缺能力时伪造 PASS |

`--package-profile` 描述包类型；`--verification-level fast/release/deep` 描述验证深度，不能与 run mode 混用。

编排器只维护 durable state 和 immutable receipt binding。`resume` 不改变 run identity，不覆盖已 seal 证据；receipt 漂移会 BLOCKED。高级用户可继续直接调用全部底层命令。
