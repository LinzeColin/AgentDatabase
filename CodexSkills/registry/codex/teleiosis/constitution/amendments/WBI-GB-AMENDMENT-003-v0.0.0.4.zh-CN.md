# 白箱迭代Skill｜Genesis Amendment 003 v0.0.0.4

**Amendment ID：** `WBI-GB-AMENDMENT-003`  
**新增 Requirement：** `WBI-GB-030`、`WBI-GB-031`、`WBI-GB-032`  
**状态：** `LOCKED_APPEND_ONLY_AMENDMENT`  
**授权来源：** Owner 于 2026-08-02 明确批准将同场竞技榜作为 Arena Lab 逻辑引擎并入唯一 Teleiosis，整体版本定为 `v0.0.0.4`。  
**前置有效 Genesis：** `WBI-GB-CANDIDATE-001+A001+A002` / `v0.0.0.3`  
**基础 Locked Genesis SHA-256：** `14ab08b9053db4ca87140e59a49f1de8105a718a87ec2d55590c6487c1a77086`

> 本 Amendment 仅按 Owner 最新明确授权扩展 WBI-GB-029 的运行序列和证据面。WBI-GB-001—029 继续有效；与旧三引擎顺序冲突的部分，仅由下列更晚条款以最小范围替代，不得借此弱化任何硬门。

## WBI-GB-030｜四引擎统一、全量非路由与唯一 Candidate 生命周期

Teleiosis 物理上仍只安装一个 `teleiosis` Skill；逻辑上固定包含 `T / Raw Teleiosis`、`S / Skill Market Lab`、`P / Product Reality Lab`、`A / Arena Lab` 四个正交引擎。正式一轮语义顺序升级为 `T1 -> C1 -> S1 -> C2 -> P1 -> C3 -> A1 -> C4`；连续三轮构成一组，连续三组构成一次完整 Run。任何公共入口均不得静默路由、删减或跳过引擎。`C` 仍表示同一迭代对象的连续 Candidate revision；四个引擎共享 CandidateIdentity、证据合同、版本谱系和回滚链，但职责与裁决权相互隔离。

## WBI-GB-031｜公平竞技、双竞技场与密封数据合同

Arena Lab 必须在运行前冻结参赛身份、模型、数据、评分、预算、重复次数、随机种子、停止条件和证据等级。公平主榜只接受同数据、同模型、同规则、同总预算的对比；不同预算结果只能进入敏感性附榜。Arena 必须分为可迭代的 Development Arena 与只读密封的 Sealed Arena：前者可暴露失败轨迹但不能产生正式晋级证据；后者的隐藏 IID、隐藏 OOD、红队和回归数据不得被 Candidate 读取，不得在同一 CandidateIdentity 下反复刷分。候选生成者不得修改冻结协议、删减难测项、拼接跨 Candidate 证据或把方法代理运行冒充官方原生运行。

## WBI-GB-032｜三层榜单、证据等级与裁决分权

Arena 输出必须分离经验效果主榜、治理能力榜和多目标 Pareto 前沿。经验主榜至少独立报告隐藏质量、最弱切片、硬约束、红队、回归和成本效率；治理能力不得混入经验效果掩盖任务退化；安全、真实性、权限、数据完整性和密封泄漏属于不可补偿硬门。统计结论必须携带样本量、重复、方差或区间、配对差值和成本账本。证据分为 L1 结构审计、L2 受控模拟、L3 官方原生同场、L4 生产盲测，低等级不得升级表述。Arena 只能输出 `IMPROVED / DEGRADED / REHEAT_REQUIRED / INSUFFICIENT_EVIDENCE / ARENA_EVIDENCE_READY / BLOCKED / INVALID_RUN`，正式 `PASS` 仍只来自外部独立 Verifier。

**严重性：** `HARD_NON_COMPENSABLE`

## 回滚

回滚不得删除本文件。若需改变四引擎顺序、Arena 密封规则或裁决分权，Owner 必须依据 WBI-GB-026 追加新的 append-only Amendment，并明确替代范围、理由和新有效版本。
