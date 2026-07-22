# 证据完整性、Attestation 与可复验规则

## 目标

另一 verifier 或策略引擎必须能回答：验的是哪个授权任务包和交付物、执行了什么、得到什么、哪些没跑、结论如何推出、封存后是否被改动。

## 三种不同保证

1. **语义一致性**：finalizer 验证任务包门、追溯、状态、verdict 与 ACTION；
2. **完整性**：`EVIDENCE_INDEX.json` 和 `SHA256SUMS.txt` 检测封存后的增删改；
3. **真实性**：需要受信 provenance、签名或外部受控系统证明来源。

哈希不是签名；未签名 in-toto statement 也不是来源认证。身份链必须显式记录 `source snapshot → build → artifact/image → deployment`，并分别保存 mapping evidence；artifact、deployment 与 attestation 的真实性需要受信 provenance 或签名。

## 机器真相

- `RUN_MANIFEST.yaml`：严格 JSON，运行事实与裁决输入；
- `TRACEABILITY_MATRIX.json`：Acceptance/Task/Test/Evidence/Subject 闭环与变更影响；
- `raw-results/taskpack-lock.json`：完整任务包文件清单、完整包摘要、七角色契约摘要、ID 抽取和授权摘要；
- `taskpack/TASKPACK_SOURCE_SNAPSHOT.zip`：确定性、只读的完整任务包源快照；
- 原始 runner 输出：实际执行结果。

Markdown 供人读，不得与机器真相冲突。

每个结果至少包含 test_id、gate、status、blocking、expected、actual/reason、attempts 和 evidence_paths。PASS/FAIL 必须有原始证据；BLOCKED/NOT_RUN/N/A/WAIVED 必须有原因。

## 任务包证据分层

- `integrity_evidence_paths`：完整快照、全部相关文件清单、`pack_digest_sha256`、七角色 `contract_digest_sha256` 与锁记录；
- `compatibility_evidence_paths`：任务包对目标项目、候选版本和 decision scope 的适用性，以及 Acceptance/Task ID 清单完整性；
- `drift_evidence_paths`：实现、接口、数据、配置、发布和 Oracle 与授权包的比较；
- `authorization_evidence_paths`：可选的 Owner 授权记录；至少必须有 authorization reference。

不能用 taskpack-lock 文件同时冒充语义兼容和无漂移证明。`pack_digest_sha256` 证明规范化完整文件树，`contract_digest_sha256` 证明七角色契约；两者都不能证明任务包适用于当前 Subject。

## 封存前检查

1. 完整任务包快照、双摘要、Subject、环境、时间、命令、工具、输入和结果完整；
2. 无 `PLANNED/RUNNING`；
3. Manifest、Traceability、TEST_MATRIX、VERDICT 与 DEFECT_REPORT 不冲突；
4. 所有关键路径存在、相对、未越界且非 symlink；
5. Acceptance 全覆盖，Task/Test引用真实，change-impact 非空；
6. token、cookie、secret、PII、内部 URL 已检查和脱敏；
7. 运行目录无 symlink、FIFO、socket 或非常规文件；
8. PASS/PASS_WITH_RISKS 满足语义门；
9. critical 独立 pass 绑定同一 Subject；AI grader 具备独立性。

## 自动封存与复核

```bash
python3 scripts/finalize_acceptance_run.py <run-dir>
python3 scripts/finalize_acceptance_run.py <run-dir> --verify
```

成功生成四个 seal 文件：

- `EVIDENCE_INDEX.json`：路径、SHA-256、大小和 evidence root；
- `SHA256SUMS.txt`：通用完整性检查；
- `FINAL_DECISION.json`：目标、任务包、Subject、范围、verdict、ACTION 和 root；
- `ACCEPTANCE_ATTESTATION.intoto.json`：in-toto Test Result statement，绑定 Subject、配置以及 passed/warned/failed tests。

任何证据文件新增、删除、改动，或 attestation/decision/checksum 与 manifest/index 不一致，`--verify` 必须失败。更新报告应创建新 run，不能静默覆盖旧 seal。

## 保留与敏感信息

共享包只保留做决定所需最小内容；敏感原始证据放受控存储，manifest 写引用、分类和访问边界。HAR 移除认证头、cookie、token和PII；截图检查身份、地址、财务和内部URL；按项目/合规 retention 删除。

## 禁止

- 只保留成功结果、删除第一次失败；
- 重试到绿后覆盖失败序列；
- 复制 builder 截图称独立证据；
- 只锁七角色而遗漏其引用附件，或用锁文件冒充兼容/漂移评审；
- 封存后改文件仍沿用旧 hash；
- 把 hash 或未签名 attestation 说成来源签名；
- 把未执行测试写进 PASS；
- 让生成模型成为自己唯一裁判。
