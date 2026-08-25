# 先读：Video Prompt Compiler v0.0.0.2

这是一个可安装 Agent Skill，把用户的自然语言想法编译为目标视频模型可执行的 Prompt。它已经从 v0.0.0.1 的“路由 + 模型指南”升级为：

```text
约束账本 → VideoPromptIR → 精确/表现双候选 → 硬门槛 → 多维评分择优 → 模型适配器 → Delta 修复
```

## 本版解决的关键问题

- 不再假设“一段万能长 Prompt”适合所有模型；
- 当前模型和过时/未知标签分开管理；
- 工业物理从关键词升级为实体、约束、驱动力、轨迹、材料响应和最终不变量；
- 评分拆分为“结构规格覆盖”和“真实生成证据”；
- 引入 RAPO 式双分支择优、VideoFeedback2 式评价维度和 PhyT2V 式物理复核；
- 引入人物/产品 Reference Sheet → 场景锚帧 → 多镜连续性流程；
- 剪辑、剧本转分镜、2D、AIGC 3D、真实 CAD 继续保持独立路线。

## 最简单用法

```text
$video-prompt-compiler
我想做一个 8 秒工业镜头：机器人沿十字轴曲面做激光熔覆。真实、克制、有电影质感。目标 Seedance 2.0，只给我最终可复制 Prompt，并给多维评分。
```

## 状态

- 包结构、脚本语法和离线功能测试：本包内运行并记录；
- 真实付费视频模型盲测：`NOT_RUN`；
- 人工观看生成结果：`NOT_RUN`；
- 外部独立 Verifier：`NOT_RUN`；
- AgentDatabase 落库、commit、push：由 Codex 最后一公里执行。

先读顺序：`SKILL.md` → `references/compiler-ir.md` → 目标模型适配文件 → `taskpack/CODEX_EXECUTION.md`。
