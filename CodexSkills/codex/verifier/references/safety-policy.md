# 高风险测试与外部副作用安全策略

适用于 load/stress/spike/soak/breakpoint、主动安全扫描、故障注入、生产环境、真实敏感数据、AI 工具调用和费用/外发/删除等副作用。

## 默认许可矩阵

| 动作 | local/test/staging | production-clone | production |
|---|---|---|---|
| 只读功能/API | 范围明确可执行 | 可执行 | 低风险、限流、明确授权 |
| average-load | 有阈值/监控/abort 可执行 | 明确窗口 | 显式授权、限流、实时监控 |
| stress/spike/soak | 隔离且可恢复 | 专门授权 | 默认禁止 |
| breakpoint | 隔离 + kill switch | 默认禁止 | 禁止 |
| passive scan | 可执行 | 可执行 | 明确 scope 后低风险执行 |
| active scan/fuzz writes | 显式授权、可重置 | 专门授权 | 默认禁止 |
| chaos/fault injection | steady-state、自动恢复 | 专门授权 | 默认禁止 |
| destructive data/restore | 快照 + 演练 | 专门授权 | 仅正式灾备 Run Contract |
| AI 外部工具写操作 | sandbox/模拟目标优先 | 显式权限与费用上限 | 默认需逐类授权和确认门 |

“全面验收”不自动等于破坏性或生产授权。

## 执行前硬门

- allowlist：协议、主机、端口、tenant/namespace、工具和第三方排除；
- 时间窗、最大 VU/RPS/带宽/请求/步骤/持续时间/费用；
- 监控：错误、p95/p99、资源、连接、队列、数据库和业务健康；
- abort：阈值、连续窗口、kill/rollback 命令、责任人和冷却；
- 数据：seed/snapshot、外发拦截、PII/secret 边界、清理；
- 恢复：停止后动作、RTO/RPO、数据不变量和验证方法；
- AI：工具权限、确认门、不可逆动作、最大步骤/token/费用和循环终止。

任一硬门缺失：相关测试 `BLOCKED`；已观察到危险状态：`ACTION: STOP`。

## 负载

- health+smoke 后逐级升压；上一阶未稳定通过不进入下一阶。
- 排除用户不控制的支付、身份、邮件、短信、地图等第三方。
- 使用真实任务比例、think time 和多样数据；校准负载发生器。
- 每阶结束观察恢复；只测峰值不测恢复不完整。

## 安全扫描

- passive 与 active 分开；认证扫描使用专用低权限账号。
- 发现严重疑似问题时停止扩散，只保留最小证明并走安全渠道。
- 扫描告警需记录可利用性、误报判断和残余风险。

## 故障注入

- 先定义 steady-state，一次只注入单一最小故障。
- scope 到资源/namespace/实例，时间有限，可立即撤销。
- 注入后验证功能、数据、队列和资源；Pod Running 不等于恢复完成。

## AI / Agent 副作用

- 默认用 sandbox、fake payment、邮件/短信 sink、测试 tenant 和最小权限工具。
- 不得让模型自行扩大工具权限、关闭审计、绕过确认或修改安全策略。
- 真实付款、删除、公开发布、外发消息和高费用调用必须显式授权并有硬上限。
- 失败/重试必须验证幂等，防止重复扣费、重复发送或重复写入。
- 发现循环、目标漂移、越权或费用异常立即停止。

## 证据脱敏

- 秘密替换为 `<REDACTED:type>`；不在 HAR/日志/HTML 保留 token/cookie。
- 截图检查 PII、财务数据和内部 URL。
- 敏感原始证据放受控存储，共享包只写引用和访问边界。
