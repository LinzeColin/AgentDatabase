# Product Reality Lab｜内嵌架构

Product Reality Lab 不是独立发布权威，而是 Teleiosis v0.0.0.3 的 P 引擎。它把源码与运行时产品面转换为同一可核验数字孪生，随后在八个正交维度上运行前端、后端/API、数据、性能、可靠性、安全、混沌、防呆与恢复实验。模型可以提出未知路径和边界假设，但不得成为唯一 Oracle。

```text
source census + runtime census
  -> reconciliation
  -> Surface/State/Transition/Role/Data/Fault/Oracle/Evidence
  -> deterministic + model-assisted exploration
  -> negative controls / mutation discrimination
  -> defects and neighborhood regression
  -> SYNTHETIC / CONTROLLED_HUMAN / FIELD_OBSERVED
  -> READY_FOR_VERIFIER | MORE_EVIDENCE_REQUIRED | FIELD_VALIDATION_PENDING | BLOCKED
```

P 引擎永远不得输出 PASS、VERIFIED 或 PRODUCTION_READY。其最强正向输出只是 READY_FOR_VERIFIER，正式裁决属于外部 verifier。
