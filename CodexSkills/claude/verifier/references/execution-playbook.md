# 执行 Playbook：用最少成本取得可靠结论

## 总路径

```text
初始化 run
→ 只读锁定任务包与授权摘要（适用时）
→ 锁定项目、验收闭包和不可变 Subject
→ 建立 Acceptance/Task ID 清单与追溯
→ 低成本确定性检查
→ 核心真实任务与世界状态
→ 专项风险、发布或 AI 路径
→ 缺陷归因与定向复验
→ 语义校验、in-toto Test Result、证据封存与最终裁决
```

## 1. 初始化

```bash
python3 scripts/init_acceptance_run.py <output-root> <project> --run-id <id>
```

`RUN_MANIFEST.yaml` 是严格 JSON 子集，必须可由 `json.load` 解析。

## 2. 只读接入任务包

存在定版 Skill 1 包时先执行：

```bash
python3 scripts/ingest_taskpack.py <taskpack-dir-or-zip> <run-dir> \
  --authoritative \
  --authorization-reference "owner-approved exact taskpack" \
  --authorized-pack-digest <可选的已授权SHA-256>
```

脚本自动：拒绝路径穿越、symlink、重复/大小写冲突 ZIP member、七角色缺失/歧义；冻结完整任务包确定性快照；生成规范化完整包摘要和七角色契约摘要；保守抽取显式 Acceptance/Task IDs。Verifier 随后核对 ID 完整性、目标/版本兼容性和实现漂移，并分别附证据；不得修改源任务包。

## 3. 定位项目、闭包与 Subject

1. 锁定 repo root、target path、完整 HEAD/snapshot、build/artifact/deployment；
2. 读取任务包、项目级文档、构建和测试入口；
3. 通过 workspace/build/import/diff/runtime config 确定最小验收闭包；
4. 排除 cache、generated、archive、backup、binary和无关大数据；
5. 在 manifest、TEST_MATRIX 和 TRACEABILITY_MATRIX 写 included/excluded、change impact 与证据。

Monorepo 只裁决目标项目，但执行受影响共享切片和核心跨模块旅程。

## 4. 建立追溯

每个权威 Acceptance ID 恰好一行：

```text
Requirement → Acceptance → Oracle → locked Task IDs
→ executed Test IDs → Evidence → exact Subject → row status
```

Task ID 不在锁定 Task Graph、Test ID 不在 manifest、行状态与 Test 聚合不一致、缺失 change-impact 记录，均不得进入完整裁决。

## 5. 自动发现命令与风险

命令优先级：已批准 Acceptance/CI → package scripts/workflow/Makefile → README → 语言标准入口 → 最后提出一个明确缺口。优先项目已有锁定 runner，不默认全局安装。

在 manifest 写明 `risk_level`、`risk_triggers`、`profile`；不得只写 auto。quick 用于低风险无接口/数据/权限/部署/AI行为变化；standard 为默认交付；deep 用于迁移、安全、恢复、容量、生产副作用和高自主 Agent；critical 还需第二次独立 pass。

## 6. 低成本检查顺序

1. taskpack/identity/dirty snapshot/依赖锁/配置/迁移预检；
2. install/build/start/health；
3. lint/typecheck/static/secret sanity；
4. focused unit/integration/contract；
5. changed-scope regression；
6. 核心 journey 与数据/副作用；
7. 权限、边界、并发、错误恢复；
8. 兼容、真人可用性、a11y；
9. 经授权的性能、安全、韧性；
10. 发布运营/回滚/灰度；
11. AI 多trial、独立grader、安全与成本。

确定性阻断已使 verdict 不可改变时，停止昂贵检查，但保留所有 `NOT_RUN` 与原因。

## 7. 重复、Baseline 与变更

- 确定性失败：保留第一次失败，同输入最小复现一次；
- 疑似 flaky：最多追加两次，记录完整序列；关键路径仍波动不得 PASS；
- 性能：同一 workload 至少两次；
- AI：至少三次独立 trial，高风险按波动增加。

有上一接受版本时锁定其 identity 与 evidence root；无 baseline 不自动失败，但不能声称“无回归”。`change_impact` 必须说明每个变更影响哪些 Acceptance/Test；初次交付使用 current-subject 记录。

## 8. 发布路径

- `release_candidate`：身份、运营、迁移兼容、恢复、灰度、健康/业务门和 abort 条件；通过只表示可进入受控发布。
- `staged_release`：锁定 control/candidate、rollout group、实际暴露、观察时长、健康和业务不变量；达到 abort 门立即停止扩流。
- `post_deploy`：核对实际 deployment identity、完整观察窗和真实核心旅程，记录 promote/hold/rollback；观察不足为 BLOCKED。

## 9. AI / Agent 路径

锁定模型、prompt、tool/harness、retrieval、policy 与参数；按真实任务和高风险切片执行多 trial；优先 world-state/程序化 grader；生成模型不得是唯一裁判。使用模型 grader 时执行盲评与跨模型复核，并保留分歧处理证据。检查 prompt injection、越权、敏感数据、过度拒绝、失败恢复、成本和延迟。

## 10. 证据与缺陷

证据命名：`<test-id>__<what>__a<attempt>.<ext>`。每个关键结果关联 Subject、命令、expected/actual、时间、环境和路径。缺陷分类只使用：

`PRODUCT_DEFECT | TEST_DEFECT | ENVIRONMENT_DEFECT | REQUIREMENT_GAP | FLAKY_UNRESOLVED | OBSERVATION`

修复复验：新 identity → 原失败 → 新回归 Oracle → 核心 journey → affected closure → 失效的发布/AI门；任务包/Oracle 变化必须重新授权，不能在 verifier 内修改。

## 11. 最终化

1. 更新 manifest、TRACEABILITY_MATRIX、TEST_MATRIX、VERDICT 和 DEFECT_REPORT；
2. 确认任务包完整/兼容/漂移证据、change impact、AI grader 独立性均满足；
3. 确认无 `PLANNED/RUNNING`、占位符、证据越界或秘密；
4. 运行 finalizer；
5. 再运行 `--verify`；
6. 交付 `FINAL_DECISION.json` evidence root 和 `ACCEPTANCE_ATTESTATION.intoto.json`。

finalizer 失败时不得宣称正式 PASS。
