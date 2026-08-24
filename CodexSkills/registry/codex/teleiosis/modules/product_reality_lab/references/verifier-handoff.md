# Verifier Handoff Contract

Reality Lab 只在关键门满足时生成 `verifier_intake.json`。

必须包含：

- exact subject identity and digest；
- run contract hash；
- frozen claims/acceptance references；
- coverage vector and item-level waivers；
- evidence index with hashes；
- defect ledger summary and zero open P0/P1；
- field evidence requirement/status/class；
- residual risks and contradictions；
- tools/models/config versions；
- readiness calculation version。

Current candidate calculation version: `0.2.1`. It includes catalog-to-item reconciliation, derived counters, evidence-class integrity, graph/reference integrity, competitor/poka-yoke gates and negative-control effectiveness.

Verifier 应在独立上下文重新检查 subject、contract、evidence 和现实副作用，不接受 Reality Lab 的状态作为最终裁决。
