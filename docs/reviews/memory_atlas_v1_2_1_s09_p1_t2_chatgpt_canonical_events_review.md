# S09-P1-T2 ChatGPT Canonical Events Review

## Scope

本 Task 只实现稳定 conversation/message identity、内容 hash、版本链和增量去重。
`S09-P1-T3` 的 facets、主题、活动和 Universe State 输入均未开始。Owner 已明确
停止 export/browser/download 工作；`S08-P3-T1` 仍保持延期且未完成。

## Implementation

- conversation ID 只依赖 ChatGPT source identity；缺少 conversation source ID 时，
  使用 parser provenance、创建时间和首个稳定 message anchor 的内容无关 fallback。
- message ID 只依赖 canonical conversation ID 与 source message identity；message
  内容变化只改变 `message_sha256`，不会改变 message ID。
- version ID 来自完整 canonical conversation payload 的 SHA-256；export hash、
  observed time、raw ref 和 parser provenance 不进入版本 identity。
- `chatgpt_canonical_events.jsonl` 每个未见版本只追加一行，并验证连续
  `version_number` / `previous_version_id`。重复导入不写任何 event bytes。
- sync 在 raw 写入前完整校验旧 ledger；修改后的对话写入新 content-addressed raw，
  旧 raw 字节保持不变。canonical commit 失败时保留可重试的 append-only raw 真相。
- source registry、atlasctl dry-run、`validate:sync` 和测试价值清单均已登记 T2。

## Evidence

- Test-first：实现前因 `memory_atlas_cli.chatgpt_canonical_events` 缺失失败。
- Dedicated regression：`9/9 PASS`，覆盖稳定 ID、内容 hash、transport-independent
  version、append/replay、旧 raw 保留、损坏 ledger preflight 和 CLI no-write 合同。
- Parser/S04/R7/raw-ledger compatibility：`63/63 PASS`。
- Registry/canonical integration：`42/42 PASS`。
- Governance/profile/script related regression：`66/66 PASS`。
- Final post-cleanup related regression：`160/160 PASS`。
- `ruff check`：PASS。
- `validate:fast`：最终 `6/6 PASS`，`22.752s`；首次运行仅因两处旧 CLI
  stdout hash 快照失败，更新到新增 canonical output 的同一实际 hash 后通过。
- `validate:sync`：`10/10 PASS`，`201.480s`；其中 sync unit step `55.390s`，
  credential scan `139.742s`；`raw_mutation=false`、`remote_push=false`、
  `shell=false`。

## Decision

状态：`PASS_LOCAL_ONLY`。`S09-P1-T2` 是第 `62/149` 个已完成 Task；本轮仅允许该
Task。下一 run 才可执行 `S09-P1-T3`。整包完成前禁止 push/deploy，也不得恢复
S08 export 工作，除非 owner 给出新指令。
