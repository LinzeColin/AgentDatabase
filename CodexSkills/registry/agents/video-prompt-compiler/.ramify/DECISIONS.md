# DECISIONS — v0.0.0.2

- D-0001：独立 Skill，不覆盖 prompt-compiler。
- D-0002：默认 compile-only，不调用收费模型。
- D-0003：方法先于模型；真实素材和确定性编辑优先。
- D-0004：先建 VideoPromptIR，再按模型渲染；拒绝万能 Prompt。
- D-0005：默认 Precision / Expressive 两候选，硬门槛后择优。
- D-0006：结构分与真实生成、人工观看、外部 Verifier 分离。
- D-0007：工业使用九层物理账本；无证据参数保持 UNKNOWN。
- D-0008：模型版本只采用官方核验条目；其他标签 VERIFY_AT_RUNTIME。
- D-0009：Reddit 只生成低置信度假设，不进入硬事实。
- D-0010：AIGC 3D 与真实工程模型严格分离。
