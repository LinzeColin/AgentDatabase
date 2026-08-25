# KERNEL — Video Prompt Compiler v0.0.0.2

## North Star

用户只用自然语言，获得事实受控、模型兼容、电影级/工业级且可修复的视频 Prompt，不必学习厂商语法。

## Phase

`INSTALLABLE_CANDIDATE / PROPOSED_NOT_COMMITTED`

## Current State

- 完成 Reddit、GitHub、Hugging Face、官方模型和论文的定向研究；
- 完成 VideoPromptIR、双候选、评分合同、当前模型注册表、工业物理账本、人物连续性和编辑/分镜路线；
- 包清单/JSON/Python 语法 PASS，Unit/Regression 52/52 PASS；
- 中文素材剪辑已区分 source 40s 与 target 18s，安装路径已保留 research/taskpack/.ramify；
- 压缩包独立解压复跑 52/52 PASS；
- 不覆盖现有 prompt-compiler；
- 真实视频模型、人工成片观看、外部 Verifier、AgentDatabase 落库仍为 NOT_RUN。

## Active Risks

- 模型、UI、时长、价格和账号功能快速变化；
- 结构评分不能预测审美或可用率；
- 工业事实与公开权利逐项目核验；
- 多参考越多越可能产生冲突；
- 长 Prompt 在不同模型中的最佳密度不同。

## Next

Codex 原样落库并运行离线验证；之后才进入目标模型 A/B 与独立验收。
