# Architecture｜薄内核与适配器

## 为什么不是“一个超级测试 Agent”

单一模型同时负责研究、生成、执行、判断和放行，会产生三种系统性偏差：

- 自证完成：倾向解释自己的结果为正确。
- 工具锁定：某个浏览器 Agent 或模型升级后整个 Skill 失效。
- 证据不可比：不同测试产生不同格式，无法收敛或交给 verifier。

因此采用四层：

1. **Contract Layer**：Run Contract、安全、授权、预算。
2. **Reality Model Layer**：Surface/State/Fault/Oracle 图。
3. **Adapter Layer**：UI、API、数据、性能、安全、Chaos、Field、模型探索器。
4. **Evidence Layer**：统一 Ledger、hash、缺陷、覆盖和 verifier handoff。

适配器可替换，但证据契约不变。

## 控制流

```text
Census → Gap Queue → Risk Prioritizer → Adapter Run
   ↑                                      ↓
Field profile ← Coverage/Defect Ledger ← Evidence Normalizer
                         ↓
                   Convergence Gate
                         ↓
                  Verifier Handoff
```

## 未覆盖队列

每个待办必须绑定至少一个：

- 未覆盖 critical node/edge；
- 高风险 fault；
- 竞品 benchmark gap；
- field escape；
- surviving mutant；
- unresolved contradiction；
- expired evidence/waiver。

没有绑定的模型探索不执行。
