# 市场实证能力竞品分析与采用决策

本版本采用而非复制以下成熟机制：

| 机制来源 | 采用机制 | Teleiosis 中的边界 |
|---|---|---|
| OpenAI Agent Evals / Evals | Dataset、trace、grader、逐任务结果 | Provider 可替换；不依赖即将退役的旧平台控制面 |
| Inspect AI | Task / solver / scorer 类型化 Adapter | 仅作为执行 Adapter，不取得晋级权 |
| Promptfoo | 多 Provider 矩阵、CI eval、red-team | 默认拒绝外发私有原文；固定 egress allowlist |
| Microsoft PyRIT | 攻击编排、记忆、失败分类 | 只生成安全证据，不冒充市场证据 |
| Anthropic Petri | 模拟用户与工具的多轮审计 | 证据上限保持实验室层 |
| DeepEval / LangSmith | deterministic-first、评委校准 | LLM judge 可关闭，启用时必须人类金标校准 |
| Braintrust / Phoenix | 数据集版本、不可变 experiment、trace 回流 | 用 SHA-256 和 evidence chain 固化 |
| k6 / Locust | smoke/stress/spike/soak/breakpoint | 只证明基础设施，不证明 Skill 推理价值 |
| SWE-Lancer / GDPval | 真实任务、验收和经济价值 | 通过 Issue、PR、交付、微赏金和复用进入 L6/L7 |

永久保留 No Skill 控制；模拟、压力与大数据只产生实验室证据，只有真实任务、真实用户/外部验收、真实结果与代价才能提升市场证据等级。
