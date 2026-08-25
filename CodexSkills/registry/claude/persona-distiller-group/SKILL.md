---
name: persona-distiller-group
description: The single user-facing entry point for evidence-grounded persona expertise. It routes one natural-language task to Single Expert, Small Team, Deep Team, or Swarm; loads each selected Persona Distiller product's real runtime payload; executes mandatory hypothesis, adversarial, independent review, adjudication, and synthesis controls; and returns one coherent artifact plus a Team Delta Card. The caller never chooses identities, weights, routing strategy, or team size.
---

# 人物蒸馏专家团队

## 产品边界

用户只调用本 Skill。`persona-distiller` 是上游人物质量工厂，不是普通用户入口：它负责研究、证据、人物模型、边界和交付 ZIP；本 Skill 负责人物资产准入、任务编译、稀疏路由、真实载入、协作执行、裁决、用户体验和净 Delta。

目标门是测量合同，不是设计时自我声明：整体 Delta、使用体感、MoE、路由、功能和质量目标均为 `>=95`；任何维度、任务切片、模板、框架或模型结果必须 `>=75`。没有 L4 生产盲测和独立 Verifier 时，只能写 `MARKET_LEADER_NOT_PROVEN`。

## 已测量的边界（2026-08-17 现算，不是设计声明）

上一节说「没有 L4 盲测就只能写 `MARKET_LEADER_NOT_PROVEN`」。
下面是**已经测出来的那部分** —— 每一条都能用仓里的判据重跑。
写在这里，是因为**读这份文档的人正是要据此决定用不用、怎么用**。

| 问题 | 实测 | 怎么重跑 |
|---|---|---|
| 路由比随机抽人好多少 | **n≥5 团队模式 +6.3 个百分点**（SE 2.6，离零 2.38 SE）；n=1 单专家 +64.0 pp（SE 21.5，4 题） | `measure_routing_discrimination.py` |
| 排序主要由什么驱动 | **`domain_match` 占 65.1%**（权重×σ），而它由一张**人工关键词表**算出；任务包路由合同写着「人工关键词不得成为冠军路由的主要证据」 | 同上 |
| 多少任务根本没有领域信号 | **2 / 24 = 8%**（词表 92→290 词之前是 54%）。这些任务排序落到 `currentness`，实测**低于随机抽人 1.7 pp**；route-plan 与执行合同会明写 `NO DOMAIN SIGNAL` | 同上 |
| 模式判对没有 | 任务包自带 72 道 oracle：**模式命中 33%**（16/48、8/24）；`single_expert` 与 `swarm` **一次都没被选中**；人数 `persona_target` **命中 0%**（中位偏差 +7 人） | `check_benchmark_mode_accuracy.py` |
| 强制控制面在不在 | **72 条全齐、0 次缺失** ✓ 这一条是真在执行的 | 同上 |
| 团队级结果遥测有多少条 | **0 条**。C 层要 ≥60 条 ⇒ **C 从未启用过，全部实跑都是 B** | `report_expert_team_state.py` |
| 分歧检测能不能命中 | 全库可互相点名的配对 **24 / 5151 = 0.47%**，且全部同族；而路由跨族选人 ⇒ **24 个任务里含可检出对的是 0 个**。`divergences: []` 意为「**没有检出**」，**不是**「专家一致」 | 同上 |
| 名册覆盖 | 12 个身份族中 **医疗护理师恒为 0 人**；命中该族的任务注定 0 | `audit_persona_fleet_for_team.py` |
| 名册里的人物本身测过没有 | **102 个在册产物中只有 2 个**（2%）有干净的盲测 delta 读数（Carver +0.3791、Shewhart +0.1822）；另 3 个只有污染读数（看过 rubric 才写基线，不算证据）；**97 个什么读数都没有**。三方向交叉核一致：102 份 registration.json 与 102 份 team-card.json 含 delta 字样的都是 **0** 份 | `check_registered_products_have_delta_evidence.py` |
| 团队 vs 裸模型的盲测增益 | **没有这个数。** 需要真跑任务并与裸模型盲比、且要互相独立的评委会话 —— 未做，**不编** | —— |

**怎么用这张表**

1. 任务落在没有领域信号的那 8% 时，**别把队伍当成「按专业挑出来的」** ——
   执行合同的 `selection_caveats` 会明写这一点。
2. `documented_divergences` 为空时，**不要写成「专家们意见一致」** ——
   执行合同的 `user_output_contract.phrasing_rules` 有明确措辞要求。
3. 需要 1 个人或 25+ 人的任务，**显式传 `--mode` / `--size`** ——
   auto 在基准的 72 道题上从没选中过这两种模式。
4. 想要「比裸模型强多少」的数，先跑真实任务并记录 outcome
   （`record_team_outcome.py` 默认写 `<registry-root>/telemetry/team-outcomes.json`，
   路由默认从同一处读）。**攒够 60 条 C 层才会启用。**

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

宿主 Agent 按 execution contract 执行后，写回结果并执行。

> **注意：下面两个 `--result` 要的是两份不同的文档。**
> `result-input.json` 是**判分输入**（`absolute` / `candidate` / `baseline` / `paired`）；
> `team-result.json` 是**运行叙述**（`work_completed` / `member_contributions` /
> `decision_changing_disagreements` / `audit_trace` / `next_action` /
> `remaining_unknowns`）。参数同名而内容不同，别把同一份传给两边 ——
> 传错时 `score_team_delta` 会 **`status: blocked` 并 rc=2**（不会给你一个 0 分冒充读数）。


```bash
python3 scripts/score_team_delta.py --result result-input.json --output delta-score.json
python3 scripts/build_team_delta_card.py --route-plan route-plan.json --result team-result.json --delta-score delta-score.json --output team-delta-card.json
python3 scripts/record_team_outcome.py --route-plan route-plan.json --delta-score delta-score.json --task-slice <slice> --actual-success <0..1> --telemetry outcome-telemetry.json
```

不得把“已生成合同”说成“任务已完成”。只有真实结果可以更新 C 层校准。

## 自检

    python3 scripts/run_tests.py            # 默认就是门：有红即 rc=1
    python3 scripts/run_tests.py --report   # 只报告

跑 `tests/` 全部 9 件（`test_*.py` **＋** `run_*.py` —— `run_functional_acceptance.py` 不叫 `test_*`，只按一种命名会漏掉它）。
文件正文里记着一张**变异实测表**：把核心函数逐个打坏，看几件测试会喊。

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
