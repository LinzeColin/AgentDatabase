# Stage 0 Semantic Reconcile

每次写入移动仓库前先读取最新 integration base、AGENTS、governance 和部署规则，再按任务分类：

| 状态 | 含义 | 动作 |
|---|---|---|
| satisfied | 与冻结实现精确一致 | 跳过 |
| equivalent | 上游已语义等价实现 | 保留上游 |
| apply | 目标语义不存在 | 新增最小实现 |
| adapt | 已有相关实现但不等价 | 薄适配，禁止旧整树覆盖 |
| conflict | 身份、Genesis、权限、安全或 Scope 冲突 | 停止 |
| blocked | 缺少权威、文件、凭证或环境 | 停止并给最小采集方法 |
| obsolete | 更晚权威明确废止 | 不实施 |

运行：

```bash
python3 scripts/teleiosis.py semantic-reconcile --repository /latest/main --spec templates/semantic-reconcile-spec.example.json --output /outside/report.json
```

报告中的 repository SHA 只可作为观察点，不能变成移动 main 的冻结前置门。
