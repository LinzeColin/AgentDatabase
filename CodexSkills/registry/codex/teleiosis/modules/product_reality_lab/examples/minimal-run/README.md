# Minimal Run Example

这个目录由 `prl.py init` 真实生成，故意保持 `MORE_EVIDENCE_REQUIRED`，用于展示一个尚未伪造完成度的初始工作区。

下一步顺序：

1. 完成 Surface、Journey/State、Fault、Oracle、Test Matrix、竞品与防呆清单；
2. 把可重放证据放入 `evidence/` 后运行 `index-evidence`；
3. 运行 `sync-coverage --auto-cover-evidenced` 自动建立逐项覆盖清单；
4. 人工复核每个 Coverage Item、Waiver 和残余风险；
5. `validate`、`score`，只有状态为 `READY_FOR_VERIFIER` 才能生成 handoff。

本示例不含真实业务证据，也不代表任何项目已经通过。
