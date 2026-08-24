# v0.0.0.3 → v0.0.0.4 迁移说明

## 破坏性语义变化

- AutoResearch、MetaHarness 和 Omni 不再允许本地同名模拟。
- GEPA 和 Promptfoo 不再使用本地兼容回退。
- Promptfoo Optimize 只接受官方输出中的精确 `Best prompt` 区段。
- Omni 只有在四条独立原生路径全部通过且各自产生候选时才进入第二阶段。

## 新增配置

`optimization.native_engines.autoresearch`：`workspace`、`command`、`candidate_path`、`required_files`、`allowed_paths`、`require_official_origin`。

`optimization.native_engines.meta_harness`：`workspace`、`command`、`entrypoint`、`candidate_path`、`allowed_paths`、`iterations`、`require_official_origin`。

`optimization.native_engines.promptfoo`：`suggestions_identity`、`require_distinct_suggestions_identity`、`validation_split`。

## 迁移原则

旧项目配置仍可读取；但缺少原生工作区或命令时会显式 `BLOCKED`，不会退回本地模拟。正式运行前应先执行 `doctor --probe` 并补齐报告中的环境绑定缺项。
