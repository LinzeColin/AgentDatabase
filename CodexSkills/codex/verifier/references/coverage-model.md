# 风险驱动验收覆盖模型（10 维 + 6 个横向门）

不要求无意义地跑满工具；任何声称通过的能力必须有已授权 Acceptance、可执行 Oracle、实际执行和绑定精确 Subject 的证据。

## 业务与质量 10 维

| ID | 维度 | 必答问题 | 典型检查 |
|---|---|---|---|
| F | 功能与旅程 | 用户能否完成产品存在的目的 | happy path、角色权限、跨模块流程、结果物 |
| D | 数据完整性 | 数据是否正确、完整、持久、可追溯 | count/sum/hash、唯一性、事务、幂等、迁移勾稽 |
| A | API/集成 | 依赖与接口是否按契约工作 | schema/auth/pagination/rate limit/timeout/retry/webhook |
| B | 边界与负向 | 极值、非法值和错误状态是否安全 | null/min/max/超长/特殊字符/乱序/非法状态跳转 |
| C | 并发与竞态 | 同时操作是否重复、丢失、死锁 | barrier、重复提交、乐观锁、队列乱序、最终状态 |
| P | 性能与容量 | 日常、峰值、持续和极限是否达标 | smoke/load/stress/spike/soak/breakpoint、p95/p99、资源 |
| R | 韧性与恢复 | 故障后能否检测、降级、恢复且不损数据 | 依赖失败、重启、资源压力、备份恢复、RTO/RPO |
| H | 真人可用性/a11y | 首次用户能否理解、完成、纠错和恢复 | persona、键盘/焦点、小屏、慢网、会话过期、WCAG |
| X | 兼容与交付 | 支持矩阵、安装、升级和混合版本是否可用 | browser/OS/locale、fresh install、upgrade、mixed version |
| S | 安全与隐私 | 权限、输入、依赖与数据边界是否安全 | secrets/authn/authz/session/SAST/SCA/DAST、数据最小化 |

## 六个横向门

| Gate | 何时必需 | 核心问题 |
|---|---|---|
| T 任务包 | 提供/发现已授权任务包 | 完整快照、完整包/七角色双摘要、授权、ID清单、兼容与漂移是否可证明 |
| Q Oracle/追溯 | 所有正式 verdict | Requirement→Acceptance→Oracle→Task→Test→Evidence→Subject 是否闭合 |
| I 身份/供应链 | 所有正式 verdict | 验收源码、snapshot、制品和部署是否是同一个对象 |
| E 证据完整性 | 所有最终 verdict | 结果是否可复跑，封存后是否增删改，attestation是否一致 |
| O 运营/发布 | release_candidate/staged/post_deploy | 出问题能否发现、停止、恢复；灰度和观察是否充分 |
| M AI/Agent | AI行为影响用户结果或副作用 | 系统身份、多trial、独立grader、安全和成本是否达标 |

## 覆盖不是“测试数量”

有效覆盖同时满足：

```text
权威 Acceptance 全覆盖
+ 变更影响全覆盖
+ 高风险表面全覆盖
+ 核心用户/世界状态全覆盖
+ 精确交付主体绑定
```

代码覆盖率、测试通过率和扫描数量只能作为辅助信号。一个未映射的阻断 Acceptance 不能被一千个绿色单测抵消。

## 数据与迁移最小集

记录输入数据集 ID/时间范围/schema/行数/摘要；验证 count、sum、唯一性、引用完整性、空值与重复率；核对 source→transform→sink、失败重跑和幂等；迁移覆盖 before/after、混合版本、部分失败、断点续跑、旧版本兼容、备份恢复或 roll-forward。只看 UI 不核对持久化，不能声明数据链路通过。

## 性能阶梯

1. smoke：验证脚本、监控和数据正确；
2. average-load：真实日常 workload；
3. stress：预期最大容量与退化；
4. spike：突发、排队、限流与恢复；
5. soak：泄漏、连接、队列和长期漂移；
6. breakpoint：仅在隔离和明确授权环境寻找拐点。

结论必须包含 workload、think time、数据多样性、发生器容量、服务端资源、阈值和恢复。无阈值只能 `MEASURED`，不能写“达标”。

## 并发与恢复

使用同步 barrier 制造真实冲突；核对成功数、错误类型、最终状态、重复副作用、丢失更新、死锁/超时与恢复。支付、库存、计费、审批、一次性任务验证业务 exactly-once 效果。故障注入先定义 steady state、爆炸半径、abort 和恢复 Oracle。

## 适用性

- `NOT_APPLICABLE`：技术上不存在该表面并写原因；
- `NOT_RUN`：适用但未执行，不得当 PASS；
- `BLOCKED`：因环境/权限/阈值/证据无法判断；
- `WAIVED`：风险被临时接受，不代表能力通过。
