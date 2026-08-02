# 外部优化器 Adapter 边界

Teleiosis 不复制第三方代码。Arena 通过结果导入或无 shell 的命令数组接入外部实现。

- AutoResearch 类循环：默认用于一次一个变更、固定预算、保留或丢弃，强调可归因。
- GEPA：在停滞、复杂交互或多目标时升级，读取完整失败轨迹并进行反思、变异和 Pareto 选择。
- Promptfoo：用于独立 eval、断言、validation split、红队和持续集成门。
- MetaHarness：只在优化记忆、检索、上下文、工具和 Agent 外壳时启用。

Adapter 必须记录官方实现、版本、commit、许可证、运行命令、模型、凭证边界、数据外传、预算和原始结果。代理实现必须 `native_execution=false`，证据最高 L2。
