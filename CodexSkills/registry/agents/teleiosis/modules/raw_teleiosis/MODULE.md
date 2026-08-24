# Raw Teleiosis｜白箱迭代控制面

**符号：** `T`  
**版本：** `v0.0.0.5`  
**运行模式：** `FULL_NO_ROUTING`

每次正式阶段必须读取并逐项完成 `CAPABILITIES.json` 的全部能力。允许 `NOT_APPLICABLE_WITH_REASON`，但必须先检查并给出具体原因；`NOT_RUN` 或 `BLOCKED` 会阻止该阶段推进。

**裁决边界：** 可生成内部 DecisionReceipt，但不能替代 external verifier formal PASS。
