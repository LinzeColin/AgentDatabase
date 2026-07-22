# Router run contract

每次运行必须记录：

- 唯一 run/trigger id 和原始 triggered_at；
- mode、source scope、来源级预算和外部效应策略；
- code/schema/rules/query/source registry/model/prompt hash；
- 实际路由和每步输入/输出 hash；
- coverage、失败、DLQ、阻塞、唯一 next action；
- 本地产物索引，不包含 secret/未脱敏私有数据。

路由器不得将 `PARTIAL/BLOCKED` 序列化为 `PASS`。
