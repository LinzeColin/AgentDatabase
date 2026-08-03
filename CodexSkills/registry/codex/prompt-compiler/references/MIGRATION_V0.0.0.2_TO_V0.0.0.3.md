# v0.0.0.2 → v0.0.0.3 迁移说明

## 核心变化

| v0.0.0.2 | v0.0.0.3 |
|---|---|
| 综合分和平均分可主导选胜者 | 硬安全、最弱维度和最弱切片优先 |
| 各引擎预算容易按份复制 | 全部引擎共享一个守恒总预算 |
| `omni` 单次组合 | `prompt_compiler` 多轮逐维差距合成；`omni` 仅保留兼容别名 |
| 竞品主要是候选源 | 同时是同层对手和可路由下层执行器 |
| 主要证明“不差于竞品” | 每竞品、每维度统计可分离第一 |
| 固定量表 | 15 个内置维度 + 自动冻结业务附加维度 |
| 报告布尔值可成为重要信号 | CI 重读冠军证据文件、校验哈希并逐维检查 |
| 重复执行可能重复消耗 | 按候选、案例、模型身份、重复号和阶段去重缓存 |

## 兼容性

- 旧项目的 `matched_budget` 仍可读取，但新项目优先使用 `total_budget`；
- 旧引擎名 `omni` 自动映射为 `prompt_compiler`；
- 原有 SQLite 历史、数据封印、四模型版本、Promptfoo、回归和红队合同保持；
- 安装器会事务式备份旧 Skill，安装失败自动回滚；
- 上游仓库移动时按语义合并，不依赖固定 SHA 或脆弱行号。

## 新配置

```json
{
  "optimization": {
    "engines": ["gepa", "autoresearch", "meta_harness", "promptfoo", "prompt_compiler"],
    "total_budget": {"smoke": 60, "quick": 180, "formal": 480},
    "minimum_probe_budget": {"smoke": 6, "quick": 12, "formal": 24},
    "synthesis_share": 0.24
  },
  "champion": {
    "enabled": true,
    "required_competitors": ["gepa", "autoresearch", "meta_harness", "promptfoo"],
    "required_dimensions": ["overall", "worst_case", "weakest_slice", "stability", "correctness", "coverage", "executability", "security", "efficiency", "oracle", "hard_safety", "regression", "redteam", "cost_efficiency", "latency_efficiency"],
    "additional_dimensions": [],
    "auto_freeze_discovered_dimensions": true,
    "bootstrap_iterations": 4000,
    "confidence": 0.95
  }
}
```
