# 竞品同层对抗与能力吸收矩阵

核验日期：2026-08-03。

| 竞品 | 同层必须击败的能力 | 下层可路由能力 | 本 Skill 执行方式 | 证据限制 |
|---|---|---|---|---|
| GEPA 0.1.4 | 全轨迹反思、变异、Pareto、多工件优化、并行 Proposal | 失败诊断、定向变异、Pareto 候选 | 只运行官方 `gepa.optimize_anything` | API 缺失、执行失败或无候选即阻塞；无本地回退 |
| AutoResearch | 固定预算实验、一次一个变化、保留或丢弃、实验日志 | 单变更归因、失败记忆、稳定迭代 | 可验证官方/受控 Git 工作区的隔离副本 + 真实外部命令 | 只允许声明候选路径变化；无本地同名模拟 |
| Meta-Harness | 固定模型外围的存储、检索、展示、工具和恢复路径搜索 | Harness 结构、上下文和工具边界 | 官方参考入口发现 + 隔离工作区真实命令 | 未发现入口、候选未变化或越界修改即阻塞；无本地同名模拟 |
| Promptfoo 0.121.20 | Eval、断言、优化、回归、红队、CI | 失败样本、断言、红队和发布证据 | 官方 CLI；只从精确 `Best prompt` 区段提取候选 | 目标模型与建议模型分角色记录；无兼容候选回退 |
| DSPy MIPROv2 | 指令、示例和程序化 Pipeline 优化 | Few-shot 与程序结构搜索 | 通用 JSON Bridge | 默认关闭；启用后自动成为本轮必选对手 |
| TextGrad | 文本梯度与反向反馈 | 细粒度自然语言梯度 | 通用 JSON Bridge | 同上 |
| OPRO | 分数条件 Proposal | 以 Prompt 执行优化 | 通用 JSON Bridge | 同上 |
| PromptWizard | Prompt 与示例联合优化 | 合成示例、反馈迭代 | 通用 JSON Bridge | 同上 |
| PromptAgent | Agentic/MCTS 搜索 | 搜索树与回溯 | 通用 JSON Bridge | 同上 |
| SAMMO | Prompt Program 搜索 | 结构化变异与搜索 | 通用 JSON Bridge | 同上 |
| Opik Optimizer | 多算法、轨迹和可视化 | 实验编排和追踪 | 通用 JSON Bridge | 平台自报分必须独立复评 |
| MLflow | Prompt 注册、优化和生产治理 | 版本、别名和审计 | 通用 JSON Bridge/导出 | 本地证据仍是当前运行真值 |
| OpenAI/Anthropic/Google 优化器 | 供应商模型定向生成与优化 | Provider 专属候选 | 通用 JSON Bridge | 不硬编码供应商，不隐式花费 |
| PromptHub/PromptLayer | 注册、协作、日志和生产反馈 | 版本和线上 Trace | 通用 JSON Bridge | 外部数据需授权和脱敏 |

## 统一公平合同

所有启用竞品只能看到种子、训练、验证、目标、要求和预算；最终测试不发送给竞品。所有候选由 Prompt Compiler 使用同一任务模型、同一最终评委和同一 Oracle 复测。启用的外部竞品若缺候选，冠军状态自动阻塞，不能通过关闭证据字段规避。
