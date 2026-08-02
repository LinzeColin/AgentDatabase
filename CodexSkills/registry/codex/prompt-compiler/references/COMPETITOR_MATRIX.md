# 竞品能力吸收与证据边界

| 方案 | 强项 | 提示词编译器的处理 |
|---|---|---|
| GEPA | 失败轨迹反思、变异、帕累托演化、多工件优化 | 固定版本官方接口作为候选引擎；最终测试和发布权不交给 GEPA |
| AutoResearch | 自动提出假设、运行实验、记录结果、继续研究 | 内置“单假设、单变化”兼容执行器；相同预算比较；保留失败路径避免循环 |
| MetaHarness | 元级执行框架、智能体结构与配置搜索 | 内置结构、步骤、工具、恢复和验收接口联合搜索兼容执行器 |
| Promptfoo | 断言、数据集、模型比较、自定义函数、回归、红队、报告和优化 | 固定版本官方优化与独立双版对照；种子和候选必须同时出现；持续集成重新核验其真实结果 |
| DSPy/MIPROv2 | 程序化提示词、指令与示例联合优化 | 通过 `dspy_mipro` 通用竞品桥加入候选；主控统一复评 |
| Opik Agent Optimizer | 多算法、轨迹与可视化优化 | 通过 `opik` 桥接；平台自报分数不能替代独立最终测试 |
| MLflow Prompt Registry/Optimization | 版本、别名、审计、优化和生产治理 | 本地历史账本提供真值；可通过 `mlflow` 桥接或导出；发布仍由本地门禁决定 |
| OpenAI Prompt Optimizer/Playground | OpenAI 定向生成与优化 | 通过 `openai_optimizer` 桥接；不硬编码供应商，不以生成结果替代测试 |
| Anthropic Prompt Generator | Claude 定向生成、测试用例和比较 | 通过 `anthropic_generator` 桥接；同时保留 Claude 目标版本 |
| Google Prompt Optimizer | 零样本、少样本、数据驱动和模型迁移 | 通过 `google_optimizer` 桥接；最终仍使用统一预言机 |
| PromptHub | 提示词版本、对比、协作和分发 | 本地 SQLite/Git 作为真值；通过 `prompthub` 桥接候选与导入导出 |
| PromptLayer | 注册表、日志、成本、轨迹和评测 | 本地证据链为默认；通过 `promptlayer` 桥接生产反馈 |

“吸收”仅指能力合同、内置兼容循环或可选桥接，不表示把第三方源代码、云服务、账户或商标打包进本技能。未配置的第三方桥不算已运行，也不能用于“比竞品好”的结论。
