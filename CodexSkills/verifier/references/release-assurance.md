# 发布保证：从授权候选到上线观察

## 核心边界

`release_candidate PASS` 只说明锁定候选具备进入受控发布的条件；只有 `post_deploy PASS` 才说明锁定部署在实际观察窗内达到本次放行门。

## 1. 候选与验收契约身份

必须同时证明：

```text
authorized taskpack digest
→ source snapshot / revision
→ build
→ artifact/image digest
→ deployment identity + runtime config
```

`release.candidate_identity` 必须等于 artifact SHA-256 或 image digest；build 名、package version、tag 只能显示。实际部署无法映射到候选，或部署内容与被验 Acceptance/配置不一致，均不得放行。

同时记录 Feature Flag、schema/migration、任务包摘要与 change-impact。可用时验证 SBOM、provenance 和签名。

## 2. Baseline / Control

优先上一已接受版本；一旦声明 baseline，记录其不可变身份和上一验收包 root hash。对比核心旅程成功率、错误/延迟/资源、业务不变量、关键可用性/AI质量和新增告警。没有 baseline 时写原因和降低的置信度，不能伪造“无回归”。

## 3. 运营就绪

生产或共享环境至少确认 Owner/on-call、升级路径、可查询 logs/traces/metrics、告警触发与送达、SLO/健康门、容量/限流/配额/成本、runbook、依赖与恢复、备份/数据保护。“有监控链接”不等于信号有效。

## 4. 兼容、迁移与恢复

验证 fresh install/upgrade、旧↔新/mixed-version、schema expand/contract、迁移幂等/续跑/部分失败、before/after勾稽，以及 rollback 或 roll-forward 后的数据不变量。不可逆迁移必须有已演练恢复或前滚路径、RTO/RPO边界。

## 5. 渐进发布

策略可为 `canary | ring | blue-green | rolling`。每个 rollout group 定义：暴露范围、control/candidate、技术健康信号、业务不变量、abort条件与连续窗口、kill/rollback动作、最小bake、机器/人工责任边界。

只看5xx不够；核心业务动作、数据不变量、任务包成功指标和用户结果必须进入门禁。

## 6. Bake、漂移与 Post-deploy

观察时长来自风险、流量周期、延迟故障模式和业务时区。记录 required/observed；不足只能 BLOCKED/停留当前ring。

扩流期间持续检查：实际 deployment identity、runtime config/flags、任务包 Acceptance、模型/prompt/tool/retrieval 和数据 schema 是否漂移。任一实质变化触发受影响重验。

`post_deploy PASS` 前确认实际流量与观察窗、canary/control结果、错误/延迟/资源/队列、业务不变量、真实核心旅程、告警/事故/回滚事件，并记录 promote/hold/rollback。

## 7. 非豁免门

部署身份或内容无法证明、任务包/Oracle漂移、核心旅程/业务不变量失败、高风险迁移无恢复、abort不能执行、关键监控缺失、观察不足却要求全量、实际数据/权限/成本风险，均不可豁免放行。
