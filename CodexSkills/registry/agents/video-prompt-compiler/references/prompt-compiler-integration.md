# 与现有 Prompt Compiler / Teleiosis / Verifier 的集成

## 角色分离

### Video Prompt Compiler

负责视频领域的语义编译：方法、镜头、运动、表演、工业物理、模型适配、2D/3D 和参考视频反推。

### Prompt Compiler v0.0.0.4

作为可选通用优化层：受保护字面量、候选比较、回归、红队与严格发布门。它不应替代视频方法路由，也不得覆盖本 Skill。

### Teleiosis

用于 Skill 版本迭代：

- Stage 0 语义对账；
- 单一 Candidate 迭代；
- 竞品、现实流程、成本与失败分析；
- KEEP / REVERT；
- 外部 Verifier 交接。

日常 Prompt 编译无需每次运行完整 Teleiosis。

### Verifier

独立验收：

- 安装结构；
- 自然语言路由；
- 模型适配；
- 工业和微表演样例；
- 参考视频抽帧；
- 输出验证；
- 权利与事实边界。

本包只提供交接材料，不声称已经获得外部正式 PASS。

### Context Kernel

`.ramify/` 保存北极星、决策、未知、风险和下一步。只保留后续执行需要的最小上下文。

## IOSS 状态

在当前可访问的 `LinzeColin` 相关仓库与 Skill 索引中未定位到名为 `IOSS` 的可执行 Skill。本版本没有虚构或假装调用 IOSS。若后续提供准确路径，可在下一版本进行 Stage 0 语义对账并接入。

## 推荐链路

```text
用户自然语言
→ Video Prompt Compiler
→ 领域候选 Prompt
→ 可选 Prompt Compiler 优化/比较
→ 人工批准
→ MiniMax Design / 目标模型
→ 生成结果
→ Video Prompt Compiler repair / lessons
→ 外部 Verifier（版本发布时）
```
