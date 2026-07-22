# 验收输入契约：单次单项目，结论绑定任务包与交付物

本契约防止五类根本错误：验错项目、验错版本、验错需求、漏掉决定用户结果的运行时表面、把候选通过写成上线成功。

## 1. 唯一裁决对象

每次只有一个 `target_project`，执行范围是其**最小验收闭包**：

```text
target project
+ 关键共享代码/包
+ schema / migration / auth / config / feature flags
+ 核心旅程必经的服务或第三方接口切片
+ 构建、制品和部署映射
```

闭包只为证明目标项目结果服务。共享组件和其他项目不因此获得 verdict。

## 2. Owner 最少输入

| 字段 | Owner 提供 | Verifier 自动完成 |
|---|---|---|
| repository | URL、PR、release、压缩包或路径 | 定位 repo root、访问方式和权威 remote |
| target_project | 项目名或路径 | 解析唯一项目根和验收闭包 |
| expected_outcome | 一句话业务结果或权威文档引用 | 拆成 journey、Oracle、数据与回归门 |
| product_design_taskpack | 已定版目录/ZIP及授权引用；没有可空 | 冻结完整任务包快照，计算完整包/七角色双摘要，提取 Acceptance/Task ID 候选并核对完整性 |
| delivery_reference | commit/PR/build，可先留空 | 锁定实际 snapshot/artifact/deployment；发布级不能为空 |

不要求 Owner 手工填写 package manager、测试命令、依赖图、浏览器矩阵、Task/Acceptance 清单或工具版本。

## 3. Product-Design-Taskpack 契约

存在 Skill 1 定版包时，它是首要验收输入。Verifier 不修改任务包，只执行：

1. 冻结包括引用附件在内的完整任务包为 `TASKPACK_SOURCE_SNAPSHOT.zip`；
2. 计算规范化完整包 `pack_digest_sha256` 与七角色 `contract_digest_sha256`；
3. 核对 Owner 授权引用及可选的完整包授权摘要，并核对 Acceptance/Task ID 清单是否完整；
4. 形成需求→Acceptance→Oracle→Task→Test→Evidence→Subject 的强追溯；
5. 对语义兼容、实现漂移分别留下证据。

正向 verdict 必须满足：

```text
integrity_status = PASS
compatibility_status = PASS
compatibility_evidence_paths 非空
drift_status = PASS
drift_evidence_paths 非空
```

完整包/契约哈希正确不等于语义兼容；“没有发现漂移”也必须有比较证据。原始 ZIP hash 不能代替规范化完整包授权摘要。

## 4. 项目解析顺序

1. Owner 明确路径；
2. workspace/project registry、submodule、项目级 `AGENTS.md`；
3. `package.json`、`pnpm-workspace.yaml`、`pyproject.toml`、`Cargo.toml`、`go.mod`、构建文件；
4. 已授权任务包、PRD、Issue、任务卡、CI workflow、测试目录；
5. git diff、import/build graph、运行配置和部署清单。

同名候选仍无法消歧时，只提出一个封闭选择题并给默认推荐，不要求 Owner 解释整个仓库。

## 5. 最小验收闭包

满足任一条件即进入闭包：

- 核心用户旅程实际调用或依赖；
- 本次修改 shared package、root lockfile、schema、auth、build config、migration 或 Feature Flag；
- 不检查就无法证明数据、权限、兼容、恢复或实际部署正确；
- 其失败会使目标项目核心结果失真、丢失、重复或不可恢复。

默认排除无依赖关系的应用、archive/retired 项目、外部服务全部功能、与目标结果无关的全仓重型测试，以及不能改变 verdict 的检查。

## 6. 版本与交付主体

正式 verdict 必须建立：

```text
source snapshot → build identity → artifact/package/image digest → deployment identity
```

至少记录：repo/branch/upstream/完整 HEAD、`git status`、source snapshot SHA-256（dirty 时）、build ID、artifact SHA-256 或 image digest、source-to-artifact 映射、deployment identity、runtime config/flags/schema 版本；可用时记录 SBOM、provenance 与签名验证。

规则：

- 可变 tag、branch 名、文件名和“latest”不是不可变身份。
- 干净源码可用完整 commit；dirty 源码的正向结论必须绑定可复验 snapshot 或实际 artifact/image，旧 HEAD 不能代表未提交内容。
- 发布级结论必须绑定 artifact/image digest；部署结论还必须证明 deployment mapping。
- 修复复验使用新身份和新 manifest，不能覆盖旧 verdict。

## 7. 决策范围

| decision_scope | 能说明什么 | 不能说明什么 |
|---|---|---|
| developer_check | 锁定工作副本/snapshot满足已执行检查 | 不等于正式制品可发布 |
| release_candidate | 锁定候选具备进入受控发布条件 | 不等于生产已成功 |
| staged_release | 指定小流量/ring达到观察门 | 不等于全量已稳定 |
| post_deploy | 锁定部署在实际观察窗内达到放行门 | 不保证未来永不故障 |

报告第一屏必须显示 decision scope。

## 8. 需求真相优先级

1. Owner 对精确任务包版本/摘要的授权；
2. 锁定 Acceptance Contract、PRD、技术运营设计和 Pursuing Goal；
3. 已批准 Issue、任务卡、接口/数据契约；
4. Task Graph、Roadmap、delivery notes 和 diff；
5. README、用户文档和既有测试；
6. 当前实现，只能作为 `INFERRED` 行为。

冲突标记 `REQUIREMENT_GAP`；不得选择更容易通过的一方，也不得用实现反向发明或放宽需求。

## 9. 可执行 Oracle 与追溯

每条关键旅程定义：

```text
Given: 角色、干净状态、输入、依赖、版本和 flags
When: 用户/调用方完成目标
Then: 用户可见结果 + API/数据/文件/下游世界状态
Recovery: 刷新、重启、重试、重复或依赖失败后的约束
Cleanup: 清理/保留策略
Evidence: 命令、trace、日志、query、截图、result path
```

`TRACEABILITY_MATRIX.json` 中每个权威 Acceptance ID 恰好一行，并且：

- Task ID 必须存在于锁定 Task Graph；
- Test ID 必须存在于 `RUN_MANIFEST.results`；
- 行状态由实际 Test 状态聚合，不可手填美化；
- Evidence 路径必须存在；
- Subject identity 必须与本次交付物一致；
- `change_impact` 至少有一条，初次交付可使用 `initial-delivery/current-subject`。

追溯完整与测试通过是两个独立问题：FAIL 也应完整追溯；无法追溯应 BLOCKED。

## 10. `auto` 风险路由

`quick` 仅限无 API/schema/数据/权限/迁移、关键依赖、部署或 AI 行为变化，且无真实外发、费用或不可逆副作用。出现登录/权限、数据写、外部 API、并发、公开发布、共享依赖至少 `standard`；支付、敏感数据、迁移、生产写、重大容量、安全/恢复承诺或高权限 Agent 使用 `deep`；大范围数据损坏/泄露、重大财务合规或高自主高权限操作为 `critical`，正向结论需两个独立 verifier pass。

## 11. 只在这些情况下问 Owner

- 业务成功结果无法从权威来源判断；
- 授权的精确任务包版本/摘要无法确认；
- 受限环境、账号或测试身份不可获得；
- 付款、邮件、短信、删除、真实客户数据、生产写或付费 API；
- 要求性能 PASS/FAIL 却无阈值；
- 破坏性测试无隔离、备份、abort 或恢复；
- 目标项目存在无法消除的同名歧义；
- 残余风险需要明确接受。

问题一次性合并，给默认建议与不回答的后果。

## 12. 状态、事实与独立性

测试状态仅使用 `PLANNED | RUNNING | PASS | FAIL | BLOCKED | NOT_RUN | NOT_APPLICABLE | WAIVED`；事实状态仅使用 `VERIFIED | INFERRED | UNKNOWN | CONTRADICTED | STALE`。`NOT_RUN` 不是 PASS；关键证据冲突 fail-closed。

可接受独立性包括 fresh thread、独立 QA agent/person、从不可变 subject 启动的独立 CI。新线程不自动可信，仍需自行核对身份、环境、命令与结果。
