# Agentic Sparse MoE 路由合同

## 映射

- Token → Work Packet
- Expert → Capability / Method / Tool / Persona Capsule
- Gate → Task Compiler + Router
- Top-k → 最小充分人物集合
- Capacity → 上下文、工具、并发和工作包容量
- Expert Choice → 人物按已证明能力反向接受或拒绝工作包
- Router Loss → route regret、冗余席位、负 Delta、成本和延迟
- Early Exit → 阶段门通过后停止扩员

## C 层

C 只有在结果遥测满足以下条件时启用：至少 60 个可归因结果、Expected Calibration Error 不高于 0.12、任务切片覆盖不低于 0.75。否则明确回 B。

## B 层

B 以 work-packet DAG、能力、方法、工具、边界、当前性和明确输出责任进行确定性路由，是稳定面、解释面和 C 的数据源。

## A 层

A 保持旧类别和场景匹配，只用于兼容。人工关键词不得成为冠军路由的主要证据。

## 路由观测

每次保存：候选、排除原因、选中理由、策略、信心、容量、任务分配、降级原因、路由结果和后续真实效果。路由分数只是选择信号，不是质量证明。
