# Oracle Catalog

## Oracle 类型

- Business invariant：账务、权限、数量、状态机规则。
- Contract/schema：类型、状态码、错误语义、事件格式。
- World state：数据库、对象存储、队列、通知、审计日志。
- Metamorphic：输入变换后输出应保持/按规则改变。
- Differential：多个兼容实现或版本应满足同一规范。
- Golden/visual：稳定视觉或输出基线。
- Accessibility：自动规则 + 人工可操作性。
- SLO/operational：延迟、错误率、资源和恢复。
- Human task：代表性用户是否独立完成任务。
- Field outcome：真实业务和行为指标。

## Oracle 独立性

关键行为避免生成器与裁判同源。示例：

- 模型生成 UI 测试 → 数据库 invariant 判断结果。
- API fuzzer 生成序列 → Schema + world-state 判断。
- 开发 Agent 写测试 → mutation/fault injection 检查测试有效性。
- 竞品 benchmark → 自身业务 Acceptance 判断是否值得采用。
