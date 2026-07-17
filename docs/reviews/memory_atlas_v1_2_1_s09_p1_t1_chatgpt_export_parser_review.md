# S09-P1-T1 ChatGPT Export Parser Review

## Scope

本 Task 只实现多格式、只读、loss-aware parser。`S09-P1-T2` 的稳定 ID、版本、
增量去重，以及 `S09-P1-T3` 的 facets/主题/活动/Universe State 均未开始。
Owner 已明确停止 export 工作；`S08-P3` 保持未完成并延期，不计入完成数。

## Implementation

- 支持 `conversations*.json`、编号 JSON、ZIP JSON members、metadata/attachments，
  以及可识别的 list/`data`/`items` 未来容器。
- 原 conversation/message/author/content/attachment/metadata 未知字段保留；sync
  规范化输出使用 extensions 字段承载，credential scan 覆盖完整规范化 payload。
- 文件、conversation item、mapping node 和 message 解析失败均产生明确 reason code；
  quarantine 仅保留来源、类型、字段名和 payload SHA-256，不复制原始值。
- source registry、`validate:sync` 与测试价值清单均登记新合同；旧 list loader、S04
  sync 和 raw-ledger 调用方式保持兼容。

## Evidence

- Test-first：实现前因 parser module 缺失失败。
- Dedicated parser regression：`13/13 PASS`，含 container extensions、保留字段
  冲突，以及全失败输入不覆盖既有 processed outputs。
- Parser/source-registry/S04/raw-ledger compatibility：`51/51 PASS`。
- Validator-profile/test-value：`23/23 PASS`。
- `ruff check`：PASS。
- Final related regression：`88/88 PASS`，`15.288s`。
- `validate:fast`：`6/6 PASS`，`23.544s`。
- `validate:sync`：`10/10 PASS`，`201.321s`；其中 sync unit step
  用时 `60.927s`，完整 credential scan 用时 `131.039s`；
  `raw_mutation=false`、`remote_push=false`、`shell=false`。
- 前两次 sync-profile 失败分别暴露了跨来源临时 fixture 耦合，以及验证副本缺 raw/
  带 `.DS_Store`。前者已在保持 registry 精确值校验的同时解除全局文件存在性耦合；
  后者仅修复任务验证副本，未改共享 checkout 或 source data。
- Human-plane audit：PASS，`178` machine files / `43` active configs /
  `133` evidence payloads；human/test-value/script/profile 回归 `59/59 PASS`。
- Official renderer：`drift=0`、`reference_issue=0`；required governance：
  `errors=0`、`warnings=0`。

## Decision

状态：`PASS_LOCAL_ONLY`。`S09-P1-T1` 是第 `61/149` 个已完成 Task；本轮仅允许该
Task。`S08-P3` 仍是 owner-deferred/open，不得回填为完成。下一 run 才可执行
`S09-P1-T2`，且整包完成前仍禁止 push/deploy。
