ACTION: <NONE|ACT|STOP|ESCALATE>

# 验收结论 — <目标项目> <锁定Subject>

## 你只需要先看这里

- **本次验收：** `<项目名>`（`<项目路径>`）
- **任务包：** `<未提供 | version + full-pack SHA-256 + seven-role contract SHA-256 + authorization reference>`
- **不可变Subject：** `<commit / source snapshot / artifact digest / deployment identity>`
- **结论适用范围：** `<开发检查 | 发布候选 | 灰度阶段 | 上线后观察>`
- **结论：** `<本范围检查通过 | 可继续但有明确风险 | 不能接受 | 现在无法判断 | 危险立即停止>`
- **一句话原因：**
- **你现在只需要做：** `<接受 | 进入受控灰度 | 交给开发修复 | 补一个条件 | 接受限时风险 | 停止/回滚>`

### 我实际证明了什么

1. `<核心用户结果>`
2. `<数据/API/文件/下游世界状态>`
3. `<最重要的错误、回归、发布或AI检查>`

### 任务包与追溯

- Taskpack source snapshot / full-pack digest / contract digest：
- Taskpack integrity / compatibility / drift：
- Acceptance覆盖：`<mapped>/<declared>`
- Task引用与change-impact：
- Traceability status / evidence：
- Oracle或交付内容漂移：`无 | 有，见finding`

### 最大问题或残余风险

1. `<无 / 风险1>`
2. `<无 / 风险2>`
3. `<无 / 风险3>`

### 本次没有验收什么

- 其他项目：
- 未执行能力及原因：
- 是否影响结论：`YES | NO`，原因：

### 证据封存

- Evidence root SHA-256：见 `FINAL_DECISION.json`
- in-toto Test Result：`ACCEPTANCE_ATTESTATION.intoto.json`
- 完整性复核：`PASS | FAIL | NOT_RUN`
- 外部签名/provenance：`有引用 | 无；仅内部一致性`

> `developer_check PASS` 不等于正式可发布；`release_candidate PASS` 只表示可进入受控发布；只有 `post_deploy PASS` 才说明锁定部署在本次观察窗内达到放行门。

---

## 技术记录

- Verdict / ACTION：
- Repository / target / closure：
- Taskpack version / full-pack digest / contract digest / source snapshot / authorization：
- Source snapshot → build → artifact/image → deployment：
- Environment / config / flags：
- Risk / profile / independent passes：
- Baseline：

## 交付门结果

| Gate | Status | Expected | Actual | Evidence / Finding |
|---|---|---|---|---|
| taskpack_integrity |  |  |  |  |
| taskpack_compatibility |  |  |  |  |
| taskpack_drift |  |  |  |  |
| traceability |  |  |  |  |
| subject_identity |  |  |  |  |
| build_start_health |  |  |  |  |
| core_journey |  |  |  |  |
| data_or_output |  |  |  |  |
| changed_scope_regression |  |  |  |  |
| safety_security |  |  |  |  |
| operational_readiness |  |  |  |  |
| rollback_or_rollforward |  |  |  |  |
| staged_release_observation |  |  |  |  |
| ai_eval |  |  |  |  |

## 问题、测量与复现

- Findings：`L0=<n> L1=<n> L2=<n>`
- Tests：`PASS=<n> FAIL=<n> BLOCKED=<n> NOT_RUN=<n> N/A=<n> WAIVED=<n>`
- 不可豁免问题 / waivers / critical blocked：
- Functional/data/API/concurrency/performance/recovery/human：
- AI success/slices/safety/grader independence/cost：
- Canary/control/bake/post-deploy：
- Exact rerun / rollback / restore：

## 证据索引

- `RUN_MANIFEST.yaml`
- `TRACEABILITY_MATRIX.json`
- `taskpack/TASKPACK_SOURCE_SNAPSHOT.zip`、七角色副本与 `raw-results/taskpack-lock.json`（适用时）
- `TEST_MATRIX.md` / `DEFECT_REPORT.md`
- `RELEASE_ASSURANCE.md` / `AI_EVAL_MATRIX.md`
- `EVIDENCE_INDEX.json` / `FINAL_DECISION.json`
- `ACCEPTANCE_ATTESTATION.intoto.json` / `SHA256SUMS.txt`
