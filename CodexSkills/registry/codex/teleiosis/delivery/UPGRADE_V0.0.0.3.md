# 升级至 Teleiosis v0.0.0.3

1. 从最新 `origin/main` 开始，确认当前分支为 main、工作树无无关修改。
2. 运行任务包 semantic reconcile `plan`，检查七类分类和 Genesis。
3. `conflict/blocked` 立即停止；`equivalent/satisfied` 保留上游；`adapt/apply` 使用仓外备份原子应用。
4. 不创建独立 `skill-market-lab` 或 `product-reality-lab` 目录；它们只存在于 teleiosis 内部命名空间。
5. 运行 `scripts/run_v3_integrated_tests.py`、原生 `verify-self --strict` 和 `self-test --timeout 600`。
6. 动态重建 `MANIFEST.sha256`，更新 `CodexSkills/index.json`，保证 Skill instance/slug 数不增加。
7. 检查 diff 只包含 teleiosis 与 index，直接 commit main，fetch 后只做 fast-forward-safe push。
8. 任一硬门失败用任务包 rollback 精确恢复；不得放宽 Gate、修改测试或自动重签 Genesis。
