# 六视角对抗复审协议

## 目的

用不同失败模型挑战同一 evidence run。角色数量不等于独立性；必须如实记录模型、context、输入、时间和是否看过其他结论。

## 六个固定角色

1. `contract_traceability`：权威性、Acceptance/Oracle、Task/Change impact、范围漂移。
2. `test_effectiveness`：测试选择、反例、mutation/discrimination、flake、污染与统计。
3. `security_supply_chain`：权限、prompt injection、秘密、依赖、制品/provenance、命令安全。
4. `release_reliability`：部署身份、迁移、容量、告警、rollback/roll-forward、canary/control/bake。
5. `ai_model_risk`：trial 设计、切片阈值、grader 独立性、越权工具、敏感数据、成本/延迟。
6. `evidence_decision_ux`：证据完整性/隐私、waiver、verdict 一致性、Owner 与 builder 可执行性、token 噪声。

不适用角色仍需返回 `NOT_APPLICABLE + reason`，不能静默缺席。

## 两轮建议

- Round 1：广覆盖，寻找遗漏、冲突和证据缺口。
- Round 2：只接收锁定 Subject、契约、Round 1 新增事实/修复及可复跑清单；不接收 Round 1 最终结论。采用反事实、恶意环境、升级/回滚、数据污染、成本上限和独立审计视角。

## 上下文胶囊

每个 reviewer 仅收到：Subject identity、权威契约摘要与哈希、其角色相关测试/证据索引、已知约束、输出 schema。不得收到 builder 的说服性总结或其他 reviewer 的 verdict。

## 输出

每个 response 必须包含：

```json
{
  "role": "...",
  "round": 1,
  "reviewer_id": "...",
  "model_or_runtime": "...",
  "context_id": "...",
  "independence": "independent_context|role_separated_same_model|human|deterministic",
  "subject_identity": "...",
  "verdict": "PASS|PASS_WITH_RISKS|FAIL|BLOCKED|NOT_APPLICABLE",
  "findings": [],
  "challenges_run": [],
  "evidence_paths": [],
  "unknowns": []
}
```

finding 至少含稳定 ID、严重度、事实/推断、证据、反例、影响、建议 gate。

## 聚合规则

- 任一未解决 blocker → panel `BLOCKED/FAIL`，不得投票平均。
- 角色间矛盾必须保留并指定 resolution evidence；不能由聚合器静默选择有利答案。
- 同一模型/同一 context 的六角色只能称“role-separated review”，不能满足 critical 独立正向门。
- reviewer 修改产品或 evidence 后，其 review 失效，需 fresh context 复审。

`review_panel.py` 只生成胶囊、验证结构和聚合；它不会伪造或自动声称真实 SubAgent 已运行。


本协议本身不证明六个独立 SubAgent 已经运行；独立性必须由真实 reviewer/model/context 记录支持。
