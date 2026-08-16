---
name: persona-distiller-group
description: The single user-facing entry point for evidence-grounded persona expertise. It routes one natural-language task to Single Expert, Small Team, Deep Team, or Swarm; loads each selected Persona Distiller product's real runtime payload; executes mandatory hypothesis, adversarial, independent review, adjudication, and synthesis controls; and returns one coherent artifact plus a Team Delta Card. The caller never chooses identities, weights, routing strategy, or team size.
---

# 人物蒸馏专家团队

## 产品边界

用户只调用本 Skill。`persona-distiller` 是上游人物质量工厂，不是普通用户入口：它负责研究、证据、人物模型、边界和交付 ZIP；本 Skill 负责人物资产准入、任务编译、稀疏路由、真实载入、协作执行、裁决、用户体验和净 Delta。

目标门是测量合同，不是设计时自我声明：整体 Delta、使用体感、MoE、路由、功能和质量目标均为 `>=95`；任何维度、任务切片、模板、框架或模型结果必须 `>=75`。没有 L4 生产盲测和独立 Verifier 时，只能写 `MARKET_LEADER_NOT_PROVEN`。

## 四种模式

| 模式 | 人物专家席位 | 适用 |
|---|---:|---|
| `single_expert` | 1 | 单一专业、边界明确、一个人物方法足够 |
| `small_team` | 5–15 | 多能力、可部分并行、协调成本可控 |
| `deep_team` | 10–30 | 高风险、跨域、强冲突、多阶段交付 |
| `swarm` | 25+ | 至少 25 个真实、低耦合、可合并工作分片 |

没有 Solo 模式。低复杂度任务进入 `single_expert`。

人物席位只统计 `persona-solver`。以下中立控制面在四种模式中始终执行，但不计入人物人数：

1. `team-orchestrator`
2. `hypothesis-framer`
3. `counterevidence-adversary`
4. `independent-reviewer`
5. `decision-judge`
6. `synthesis-lead`

## 运行主线

```text
用户一次输入
→ Task Compiler / work-packet DAG
→ C/B/A 路由
→ 人物资产准入
→ route plan（含 subject_slug）
→ 内层 Runtime ZIP / dossier / capsules
→ 人物独立工作产物
→ 对抗反证
→ 独立复审
→ 裁判裁决
→ 单一最终交付
→ Team Delta Card
→ outcome telemetry
```

### C / B / A

- **C：Calibrated Agentic Sparse MoE**。只有真实结果遥测满足样本、校准和切片覆盖门才启用。
- **B：Deterministic Capability DAG**。默认稳定执行面；按能力、方法、工具、边界和工作包路由。
- **A：Compatibility Router**。仅在 B 无法形成有效图时兜底，保持旧资产和接口可迁移。

回退只发生在路由策略层：`C → B → A`。不回退到 Solo；若没有任何真实人物可用，状态是 `insufficient_roster`，不得伪造专家。

## 六步调用

```bash
# 1. 构建人物资产准入账本
python3 scripts/audit_persona_fleet_for_team.py \
  --registry-root . \
  --require-artifacts \
  --output expert-fleet-admission.json

# 2. 一条命令准备完整团队运行目录
python3 scripts/run_team_pipeline.py \
  --task "<用户任务>" \
  --mode auto \
  --strategy auto \
  --registry-root . \
  --refresh-admission \
  --require-artifacts \
  --workdir ./team-runs/current
```

运行目录必须产生：

- `route-plan.json`
- `team-dossier.json`
- `execution-contract.json`
- `run-receipt.json`

宿主 Agent 按 execution contract 执行后，写回结果并执行：

```bash
python3 scripts/score_team_delta.py --result result-input.json --output delta-score.json
python3 scripts/build_team_delta_card.py --route-plan route-plan.json --result team-result.json --delta-score delta-score.json --output team-delta-card.json
python3 scripts/record_team_outcome.py --route-plan route-plan.json --delta-score delta-score.json --task-slice <slice> --actual-success <0..1> --telemetry outcome-telemetry.json
```

不得把“已生成合同”说成“任务已完成”。只有真实结果可以更新 C 层校准。

## 硬门

1. 路由结果必须给每个人物输出 `subject_slug`。
2. dossier 必须真实打开登记产物的内层 Runtime ZIP。
3. 没有真实 payload、claim 和 boundary，不得开始人物推理。
4. 每条人物特有贡献必须引用该人物自己的 `claim_id`。
5. 当前事实来自独立的有日期事实通道，不从历史人物权威推断。
6. Voice 胶囊默认关闭；优先 Method、Evidence、Work、Failure、Boundary。
7. 分歧按前提、证据、预测、失败条件和适用范围裁决；不按多数票折中。
8. 生成者不得复审自己；裁判不得修改候选证据。
9. Swarm 只用于真实独立分片，不得用 25 份重复意见凑人数。
10. 任一硬维度低于 75，候选退回优化，不得发布冠军结论。

## 必读参考

- `references/persona-producer-consumer-contract.md`
- `references/moe-routing-contract.md`
- `references/team-size-control-plane.md`
- `references/team-output-contract.md`
- `references/user-experience-contract.md`
- `references/team-delta-scorecard.md`
- `references/market-leader-acceptance.md`
