# Product-Design-Taskpack 只读接入契约

## 边界

Verifier 只消费 Skill 1 已定版任务包，不修改、补写、重排或重新解释 Skill 1。任务包是验收输入，不是 verifier 输出；实现、builder 总结和既有测试不得反向降低 Acceptance。

## 完整包与七角色双锁

完整任务包不仅是七个核心文件，还包括被核心文件引用或决定验收语义的 schema、fixture、ADR、接口样例、迁移说明、策略、附件等相关文件。Verifier 必须先建立稳定只读快照，再发现七个语义角色：

1. Manifest：版本、文件索引与完整性；
2. Pursuing Goal：一句话目标；
3. PRD / Product Decision：问题、用户、价值、边界、指标与 Kill Criteria；
4. Technical & Operations Design：架构、接口、数据、安全、可靠性、迁移、监控和恢复；
5. Roadmap：Stage→Phase→Task 与关键路径；
6. Task Graph：任务 DAG、输入输出、依赖、风险、测试、证据与 Stop Condition；
7. Acceptance Contract：每条需求的唯一 Acceptance、Oracle、环境、输入、阈值与证据。

```bash
python3 scripts/ingest_taskpack.py <taskpack-dir-or-zip> <run-dir>   --authoritative   --authorization-reference "owner-approved exact taskpack"   --authorized-pack-digest <可选的已授权规范化完整包SHA-256>
```

脚本只读源任务包，并且：

- 拒绝路径穿越、绝对/驱动器路径、重复或大小写冲突、加密 ZIP member、symlink、非常规文件、超限文件树和部分覆盖；
- 在临时稳定副本上完成发现、提取和散列，降低读取期间源文件变化造成的 TOCTOU 歧义；
- 生成确定性 `taskpack/TASKPACK_SOURCE_SNAPSHOT.zip` 与完整 `source_files` 清单；
- 计算 `pack_digest_sha256`：规范化完整任务包文件树摘要；
- 计算 `contract_digest_sha256`：七个语义角色的角色稳定摘要；
- 保存七角色只读副本，保守提取显式 Acceptance/Task IDs。

`source_archive_sha256` 仅标识收到的原始 ZIP 字节。Owner 授权摘要绑定 `pack_digest_sha256`，因为同一内容可因 ZIP 时间戳/压缩参数产生不同 archive hash；反之，同名 ZIP 或相同七角色也可能包含不同附件。

## 真相优先级

```text
Owner 对精确任务包版本/规范化完整包摘要的授权
→ 完整任务包只读快照 + 锁定 Manifest / Acceptance Contract
→ PRD / 技术运营设计 / Pursuing Goal
→ Task Graph（用于覆盖，不得降低 Acceptance）
→ Roadmap / delivery notes / diff
→ 当前实现（只能作为事实观察）
```

## 四类证据，不能互相冒充

- `integrity_evidence_paths`：完整文件清单、完整包摘要、七角色契约摘要、确定性快照及锁记录；
- `compatibility_evidence_paths`：任务包适用于目标项目、Subject 和 decision scope，并证明 Acceptance/Task ID 清单及引用附件可解释；
- `drift_evidence_paths`：实现、配置、接口、数据、发布、附件依赖和 Oracle 与授权包逐项比较；
- `authorization_evidence_paths`：可选授权记录；至少有明确 authorization reference。

权威任务包存在时，PASS/PASS_WITH_RISKS 必须 integrity/compatibility/drift 全部 PASS，且兼容/漂移证据非空。哈希一致只说明 bytes 一致，不能证明语义适用或没有漂移；语义兼容也不能证明实际实现符合 Acceptance。

## 强追溯闭环

`TRACEABILITY_MATRIX.json` 每个权威 Acceptance ID 恰好一行：

```text
Requirement ID
→ Acceptance ID
→ Oracle ID
→ locked Task IDs
→ executed Test IDs
→ Evidence paths
→ exact Subject identity
→ result
```

Task ID 必须存在于锁定 Task Graph；Test ID 必须存在于 manifest；行状态由 Test 结果聚合。`change_impact` 至少一条，说明实际交付变化影响哪些 Acceptance/Test；初次交付可使用 `initial-delivery/current-subject`。完整包摘要必须与追溯矩阵、运行清单和 attestation 配置一致。

## 漂移处理

发现完整任务包、附件、Acceptance 或 Oracle 漂移时：

1. 不修改任务包；
2. 写 `drift_items`：旧值、新值、影响、证据和最小决策；
3. 建不可豁免 finding：`TASKPACK_INTEGRITY`、`ACCEPTANCE_ORACLE_DRIFT`、`TRACEABILITY_GAP` 或 `DELIVERY_CONTENT_MISMATCH`；
4. 完整性/兼容性不可证明时 BLOCKED；明确不符合授权 Acceptance 时 FAIL；
5. 只有 Owner 重新授权新的精确完整包版本后，才创建新 run。

## 无任务包场景

确实未提供时设置 `mode=not-provided`、`detected=false` 和原因，Verifier 可依据其他权威来源验收。一旦显式接入任务包，就不能用 `authoritative=false` 静默忽略；要么 BLOCKED，要么创建未接入任务包的新 run 并明确其较低保证范围。
