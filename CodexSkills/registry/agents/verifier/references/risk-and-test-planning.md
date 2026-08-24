# 风险、深度、测试选择与停止策略

## 目的

把“全面测试”改为可解释的 **risk-weighted evidence plan**：先覆盖最可能造成重大用户损失、最容易被遗漏、且最能改变 verdict 的事实。

## 1. 风险评分不是 verdict

评分只用于选择深度、顺序、独立性和证据强度。不得因为分数低就放宽 Acceptance。

建议每项 0–3：

| 维度 | 0 | 1 | 2 | 3 |
|---|---|---|---|---|
| 用户/业务影响 | 无可见影响 | 局部可恢复 | 关键流程中断 | 财务、安全、合规或不可逆损失 |
| 变更爆炸半径 | 单函数 | 单组件 | 跨服务/共享契约 | 全局/多租户/生产数据 |
| 可逆性 | 即时回滚 | 容易恢复 | 恢复昂贵 | 不可逆或恢复未知 |
| 新颖性/不确定性 | 成熟路径 | 小改 | 新依赖/架构 | 未验证技术/模型行为 |
| 权限与副作用 | 只读 | 测试写入 | 外部写入 | 生产/支付/消息/删除 |
| 可观测性 | 完整 | 有缺口 | 难定位 | 无可靠信号 |

总分建议：0–4 low，5–8 medium，9–13 high，14–18 critical。以下触发器可直接升级：权限边界、秘密、支付、生产写入、迁移/删除、不可逆操作、自主 Agent 外部动作、关键合规、安全机制绕过。

## 2. 深度映射

- `quick`：low 且无 API/schema/权限/数据/部署/AI 行为变化；focused deterministic checks + 一个真实结果。
- `standard`：默认；changed-scope regression、核心 journey、边界/错误路径、干净复跑。
- `deep`：high/critical 或直接触发器；环境复现、契约/迁移/恢复、discrimination tests、独立复审、发布/AI 专项。

Owner 显式选择更浅 profile 不会降低不可豁免门；记录为约束并在无法形成可靠 verdict 时 BLOCKED。

## 3. 变更影响选择

对每个 changed component 记录：

```text
changed path/symbol
→ direct behavior
→ callers/consumers
→ schema/data/config/flag
→ user journey
→ Acceptance IDs
→ selected tests
→ evidence
```

至少覆盖：直接影响、共享契约、持久化/迁移、权限、失败恢复、部署配置。无法建立影响边界时扩大到相关子系统，不机械全仓测试。

## 4. 执行排序

1. Subject / taskpack / authorization identity。
2. 环境、依赖锁、配置、迁移预检。
3. build/start/health 与 focused static checks。
4. 最短失败复现或关键 deterministic tests。
5. 真实用户结果与 world state。
6. 边界、并发、恢复、兼容、安全等风险专项。
7. 受控性能/故障/安全主动测试。
8. release canary/control/bake 或 AI 多 trial。

## 5. 预算

`ACCEPTANCE_PLAN.json` 至少记录：

- `max_commands`、`max_elapsed_seconds`、`max_output_bytes`；
- 网络、费用、并发、请求量、数据写入上限；
- allowlisted commands/tools/targets；
- hard stop 与 soft stop；
- 预算耗尽动作：`STOP_AND_BLOCK | STOP_AND_REPORT_PARTIAL | REQUEST_AUTHORIZATION`。

预算不能通过丢弃失败证据或缩短必须的 bake/trials 来“达标”。

## 6. 停止条件

立即停止并保全证据：

- 目标不在 allowlist、身份漂移、任务包/Oracle 漂移；
- 发现真实秘密、敏感数据外泄或越权访问；
- 生产健康/业务不变量越过 abort 阈值；
- 费用、请求、并发、持续时间超限；
- 测试造成非预期写入、删除、消息、支付；
- 环境无法恢复或证据完整性受损。

发现确定阻断后可跳过昂贵检查，但必须保留 `NOT_RUN`、原因和剩余不确定性。

## 7. 验收计划质量门

计划不得正向执行，除非：权威契约与 Subject 已定位；关键 Acceptance 有 Oracle；测试能区分正确/错误行为；命令/目标已授权；停止条件可执行；证据路径和清理策略明确。
