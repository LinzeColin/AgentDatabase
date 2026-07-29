# No-Negative-Optimization Guard

## 来源机制

Luban 在压缩后体积大于原图时透传原图；这是一条比“平均压缩率”更强的产品保护原则。Teleiosis 将其迁移为：Candidate 不得在硬保护域退化后再靠其他维度总分补偿。

## 保护域

- 安全、权限、隐私、供应链；
- 安装、升级、恢复、回滚；
- sealed holdout 保护任务；
- 成本、token、时延和人工分钟；
- activation kernel 和 Codex token 压力；
- 证据真实性与 Subject 身份。

## 决策

| 情况 | 结论 |
|---|---|
| 所有硬门通过且没有保护域退化 | `KEEP` |
| 候选无实质收益 | `NO_CHANGE` |
| 任一不可豁免保护域退化 | `REVERT` |
| 证据缺失导致无法裁决 | `BLOCKED` |

## 禁止

不得把 `UNKNOWN` 记成 0；不得用更多 reviewer、更多文件、更多测试抵消安全或回滚失败；不得因用户要求“全市场第一”而省略 outcome 证据。