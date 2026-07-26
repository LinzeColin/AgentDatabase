# Verifier + Persona Bridge

## Verifier Bridge

Teleiosis 负责生成 Candidate、证据和安装包；Verifier 负责对一个精确 Subject 做验收裁决。桥接规则：

1. Verifier 的 Subject 必须绑定 Teleiosis 输出的 candidate tree hash 或 archive SHA-256。
2. Verifier 的 PASS 只覆盖该 Subject，不自动证明市场领先。
3. Builder 自评、绿色 CI 和 README 只算线索。
4. `UNKNOWN / NOT_RUN / WAIVED` 不得改写为 PASS。

## Persona Bridge

PersonaDistillerGroup 可用于生成专家视角、反证、裁判和复审建议。桥接规则：

1. 人物专家主要提供高质量候选和盲点。
2. 控制角色必须与正向角色隔离。
3. 没有外部 provider receipt 和唯一身份时，只能标为 `role_separated_same_model` 或 `insufficient_roster`。
4. 不得把人格化专家输出当作 formal independent review。

## 推荐调用链

```text
Teleiosis market-profile -> Persona route for candidate ideas -> Teleiosis benchmark/gates -> Verifier exact-subject acceptance -> external attested review for formal promotion
```