# 白箱迭代Skill｜Genesis Amendment 001 v0.0.0.2

**Amendment ID：** `WBI-GB-AMENDMENT-001`  
**新增 Requirement：** `WBI-GB-028`  
**状态：** `LOCKED_APPEND_ONLY_AMENDMENT`  
**授权来源：** 用户于 2026-07-26 明确要求融合“确保迭代机制和迭代后的输出不会有时效局限性，确保是当前环境最强”，并允许适当兼容性改写和重构。  
**适用对象：** 白箱迭代Skill自身，以及所有被其迭代的 Skill  
**前置 Genesis：** `WBI-GB-CANDIDATE-001` / `v0.0.0.1`  
**前置 Locked Genesis SHA-256：** `14ab08b9053db4ca87140e59a49f1de8105a718a87ec2d55590c6487c1a77086`

> 本 Amendment 只追加新要求，不修改、删除、弱化、重排或重新解释 WBI-GB-001—027。旧 Genesis 文件保持逐字节不变，并继续作为可独立验证和回滚的基础锚点。

## WBI-GB-028｜无静态时效局限与当前环境最强输出合同

白箱迭代Skill的迭代机制及其最终输出不得依赖静态、永久有效或未重新核验的前沿假设。每次正式 run 必须在首个 Candidate 修改前以及最终交付前，分别冻结并哈希绑定一份 `current_environment_snapshot`，至少包含：`valid_as_of` 与时区、目标与迭代器精确版本及 tree hash、可用模型/LLM/Agent runtime/工具/权限/网络/预算、最新可获得的一手前沿来源与真实同行版本、评测与行为覆盖、Skill 检索/触发/遮蔽风险、成本与时延、未知项及能力阻塞。

每个最终输出必须携带机器可读的 `evidence_lease` 与 `environment_strength_attestation`：明确生效时间、到期时间、事件驱动 reheat 条件、比较集合、可行 Candidate 集、冻结环境、同预算指标、硬门、证据哈希和未知边界。只有当同一冻结环境与授权预算下，当前可行 Candidate 集中没有已知 Candidate 能在任何不可补偿硬门不退化的前提下整体支配被选 Candidate，且前沿扫描、真实产物、行为覆盖、检索/遮蔽与必要 benchmark 证据均达到对应 Gate，才可标记 `PARETO_UNDOMINATED_FOR_VERIFIED_CURRENT_ENVIRONMENT`；证据不足时必须标记 `NOT_PROVEN / BLOCKED / REGRESSED / REHEAT_REQUIRED`，不得用“当前最强”“超越时代”或类似措辞代替证据。

“不会有时效局限性”应通过持续重建证据、到期失效和事件驱动 reheat 实现，而不是声称某个版本永久有效。模型、供应商、工具、评分器、数据源、搜索策略、有效期长度和实现架构均不得因此被永久写死；它们必须保持可替换。环境、模型、标准、依赖、真实任务表现、安全状态、同行优势或用户要求出现实质变化时，既有领先状态立即失效并进入 bounded reheat。

**严重性：** `HARD_NON_COMPENSABLE`

## 变更收益—成本判断

本 Amendment 关闭的是“Genesis 要求做时效扫描，但每个最终输出未被强制携带可执行有效期、当前环境证明和失效语义”的治理缺口。它增加一条硬门和若干机器证据，但不增加固定 Prompt、不绑定具体技术，也不修改旧基线；收益高于增加的验证和迁移成本。

## 回滚

回滚不删除本文件。需要停用本 Amendment 时，必须由用户按 WBI-GB-026 新增后续 append-only Amendment，明确停用范围、理由、替代条款与新有效 Genesis 版本。`v0.0.0.1` 基础 Genesis 的原文件与哈希始终保留。
