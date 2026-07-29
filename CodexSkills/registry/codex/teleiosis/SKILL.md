---
name: teleiosis
description: White-box iteration, causal evaluation, market evidence, and controlled evolution for an existing Agent Skill or Teleiosis itself. Use when a user asks to improve, benchmark, stress-test, compare, self-evolve, validate with real tasks or users, productize, or package a Skill with frozen baselines, five-arm experiments, six stress classes, market feedback, rollback, independent review, and installable delivery. Do not use for ordinary code review or direct in-place edits to a production Skill.
license: MIT
compatibility: Python 3.9+ and Git. Live competitor pull requires network access. Formal independent-review PASS requires genuinely isolated SubAgents plus a separate read-only verifier.
metadata:
  author: LinzeColin
  version: "v0.0.0.2"
  language: "zh-CN"
  display_name_zh: "白箱迭代Skill"
  english_brand: "Teleiosis"
  functional_name: "White-Box Iteration Skill"
  architecture: "thin-kernel-open-adapters"
  genesis: "LOCKED_GENESIS"
---

# 白箱迭代Skill

**Teleiosis · White-Box Iteration Skill**

对目标 Skill 或本 Skill自身进行真实、可验证、可回退的完善。v0.0.0.2 将市场实证内核并入同一控制面：实验室模拟、因果实验、六类压力、大数据、真实任务与用户反馈都产生证据，但只有 Teleiosis 拥有正式晋级和发布裁决权。

## 0. 启动硬门

```bash
python3 scripts/wbi.py verify-self --strict \
  --expected-genesis-hash 14ab08b9053db4ca87140e59a49f1de8105a718a87ec2d55590c6487c1a77086
```

失败即停止且不得自动重签 Genesis。源码、Gate、Schema、脚本、测试或依赖变化及正式封包前才运行 `self-test`；安装使用非递归 `release-smoke`，旧收据不能证明新 tree。

## 1. 不可变原则

- 目标 Skill 与白箱迭代Skill自身均采用只读 Baseline、独立 Candidate、精确 diff、原始结果、失败保留与回滚。
- 修改前完成：存在性挑战、只读时效扫描、至少五个真实同行、生态位、真实产物和冻结评测合同。
- 正式完善覆盖十个系统视角；每轮可 `KEEP / REVERT / NO_CHANGE`，也可比较增量、架构跃迁、clean-slate 与组合候选。
- Candidate 不得控制 Genesis、评测合同、sealed holdout、同行证据、复审包或最终批准。
- 单次 run 有多维预算和熔断；停止当前 run 不限制未来 reheat、新模型、新架构或新候选。
- 只约束不透明、不可逆、不安全和不可验证的行为；不限制合法假设、架构、模型、工具、文件和候选空间。

## 2. 建立白箱工作区

```bash
python3 scripts/wbi.py init-run /absolute/path/to/target-skill \
  --workspace /absolute/path/outside/skills/wbi-run \
  --strategy incremental \
  --strategy architecture-leap \
  --strategy pareto-population \
  --review-attestation-contract /trusted/runtime/review-contract.json \
  --valid-as-of 2026-07-26 \
  --self-evolve
```

仅在迭代本 Skill 自身时使用 `--self-evolve`。运行策略与预算可替换；Genesis 规定的十个审查视角不可省略。

## 3. 修改前研究与考试冻结

1. 写明目标、范围、非目标、用户硬要求、现实限制、权限、风险和验收标准。
2. 完成四问 premise challenge：真实问题、独特价值、安装理由、可观察产物；输出 `CONTINUE / REPOSITION / MERGE / SPLIT / RETIRE`。
3. 执行 `freshness-scan`，覆盖模型/runtime、方法/架构、评测、标准/安全和同行。
4. 执行 `competitors`，自动发现和安全拉取真实 GitHub 仓库；也可加入可复核在线产品或真实产物包。论文、Issue、链接和本地夹具不计入五同行。
5. 完成生态位、真实产物核验和机制借鉴账本，然后 `seal-research`；seal 必须重新核验每个冻结文件的实际哈希。
6. 在首个 Candidate 变更前 `seal-eval`；sealed holdout 只保存外部 ID 与哈希，不把题目放进 Candidate 可读范围。每条结果必须绑定合同内 system、dataset 与精确 Candidate tree hash。

详细路径见 `references/WORKFLOW.md`。

## 4. 固定宏循环：五次调用，每次连续三轮

一轮正式运行必须严格执行：

```text
T1 raw Teleiosis × 3 → 提交已批准 Candidate C1
M1 market evidence × 3 → 提交已批准 Candidate C2
T2 raw Teleiosis × 3 → 提交已批准 Candidate C3
M2 market evidence × 3 → 提交已批准 Candidate C4
T3 raw Teleiosis × 3 → 提交已批准 Candidate C5
```

每个 `×3` 是一次不可拆分调用：R1 诊断，R2 对抗/实验，R3 裁决、稳定和绑定 staged Candidate 哈希。紧随其后的“修改”只能原子提交 R3 已批准的同一目录树哈希，不得再产生新内容；否则整个宏循环无效。禁止跳段、交错、把两轮拼成一次、在 mutation 前开始下一段，或让最后一次修改逃逸最终验证。

```bash
python3 scripts/teleiosis_cycle.py init --workspace /outside/run-cycle \
  --subject-name <skill> --subject-version <version> --subject-digest <sha256>
python3 scripts/teleiosis_cycle.py record-subrun ...
python3 scripts/teleiosis_cycle.py commit-mutation ...
python3 scripts/teleiosis_cycle.py validate --workspace /outside/run-cycle --require-complete
```

`raw_teleiosis` 是同一 v0.0.0.2 包内关闭市场内核的不可递归 profile，不是旧版本。迭代 Teleiosis 自身时，它只能写外部 Candidate，不能修改 Genesis、评测合同或运行中的控制面。

## 5. 市场实证内核

Market Lab 已废止为独立 Skill，作为 `wbi_market` 内嵌。它运行 `No Skill / Baseline / Candidate / Competitor / Ablation` 五臂因果实验，覆盖语义、上下文、工具、安全、版本、经济六类压力，并按 L0–L7 区分实验室、Shadow、真实 Canary、外部交付/PR/赏金与持续复用证据。

市场内核的最高结论只能是 `EVIDENCE_READY_FOR_TELEIOSIS`；它不得直接 `PROMOTE`、修改正式 Candidate 或覆盖安全/真实性硬门。所有结果绑定任务簇、重复试验、模型/runtime、工具 trace、环境、产物、成本、时延、评委校准、Provider 版本和 sealed holdout 污染审计。

```bash
python3 scripts/wbi_market.py init-workspace --workspace /outside/market-run ...
python3 scripts/wbi_market.py expand-stress --input tasks.jsonl --output stress.jsonl --categories all
python3 scripts/wbi_market.py aggregate --spec experiment.json --results results.jsonl --output-dir evidence
python3 scripts/wbi_market.py quality-audit --spec experiment.json --tasks tasks.jsonl \
  --assignments assignments.jsonl --results results.jsonl --feedback feedback.jsonl \
  --calibration judge-calibration.jsonl --blind-map controller/blind-map.json \
  --output evidence/QUALITY_AUDIT.json
python3 scripts/wbi_market.py assurance-check --input assurance.json --output assurance-result.json
python3 scripts/wbi_market.py gate --spec experiment.json --summary evidence/SUMMARY.json \
  --quality-audit evidence/QUALITY_AUDIT.json --output market-gate.json
```

实验规范使用 Schema 2.0。冻结 Gate 必须绑定污染审计、paired/exclusive assignment integrity、sample-ratio mismatch、环境一致性、统计功效、评委校准、市场时间窗与 task→run→feedback 引用完整性；缺失或失效时直接 `BLOCKED`。

真实市场证据必须来自获授权且可撤回的用户/验收者、真实任务、真实结果与现实代价；模拟、LLM 评委和大规模合成数据永远不得冒充 L5–L7。

## 6. 十轮与候选组合

十个默认视角：需求；同行；触发；工作流；安全；架构；评测；运行发布；效率维护；真实产物与未来盲点。

每轮可包含一个或多个可归因 change set：

```text
失败/机会证据 -> 可证伪假设 -> 候选或候选组合 -> 真实评测
-> 与 Baseline/当前最佳比较 -> KEEP | REVERT | NO_CHANGE
```

不为凑轮次制造修改。架构跃迁不必被拆成失去意义的单文件小补丁，但每项变更、命令、责任主体和结果仍须白箱记录。

## 7. 评测与独立治理

- 分开评测触发、任务效果、安全、真实性、成本、时延、安装、兼容、跨模型迁移、维护和未来适应。
- 先过硬门，再检查保护任务负迁移，最后使用 Pareto frontier；任何总分不能补偿硬退化。
- 两轮各六个真正独立 SubAgent 使用隔离上下文和 provider run ID；正式 PASS 还必须绑定运行开始前冻结的外部 review-attestation adapter。软性分歧可由第十三个独立只读 verifier 依据证据解决；未解决的硬域或高严重度问题必须阻断。
- 本地自写 capability/receipt、角色模拟或重复上下文不能证明独立性；runtime 不支持可信独立实例时返回 `INDEPENDENT_REVIEW_UNAVAILABLE`。

## 8. 发布、安装与回炉

```bash
python3 scripts/wbi.py gate /path/to/wbi-run --output gate.json
python3 scripts/wbi.py package /path/to/selected/teleiosis --output final.zip \
  --profile optimizer --verification-level release \
  --expected-genesis-hash 14ab08b9053db4ca87140e59a49f1de8105a718a87ec2d55590c6487c1a77086
ARCHIVE_SHA256="<from SHA256SUMS.txt>"
python3 scripts/wbi.py install final.zip --skills-root /runtime-specific/skills-root \
  --profile optimizer --verification-level release --result-file /external/install-result.json \
  --expected-genesis-hash 14ab08b9053db4ca87140e59a49f1de8105a718a87ec2d55590c6487c1a77086 \
  --expected-archive-sha256 "$ARCHIVE_SHA256"
```

`release` 封包执行完整回归，安装只做非递归验证；切换前需再跑全套时使用 `deep`。安装写入持久事务收据；中断后以 `install-status` / `recover-install` 判定，不得猜测。详见 `delivery/INSTALL.md`。

公开、内部、基础设施与方法类 Skill 使用不同的真实展示证据，不强迫所有 Skill 制作相同 UI。过期、真实失败、安全公告、依赖弃用、新模型/runtime 或更强同行会触发 `REHEAT_REQUIRED`，而不是在同一 run 中无限循环。

## 9. 按需读取

- 架构与流程：`ARCHITECTURE.md`、`WORKFLOW.md`、`WHITEBOX_EVIDENCE.md`、`SELF_EVOLUTION.md`。
- 研究与评测：`FRESHNESS_AND_FUTURE.md`、`COMPETITOR_INTELLIGENCE.md`、`LUBAN_GATES.md`、`EVALUATION.md`。
- 治理与交付：`INDEPENDENT_REVIEW.md`、`SECURITY_AND_AUTHORITY.md`、`RELEASE_AND_REHEAT.md`。
- 覆盖与扩展：`REQUIREMENT_COVERAGE.md`、`RUNTIME_ADAPTERS.md`。

以上文件均位于 `references/`，只读取当前阶段所需内容。

## 10. 最短调用

```text
调用 Teleiosis v0.0.0.2，在安装目录外冻结 <目标 Skill> 的 Baseline；严格执行 T1×3→C1→M1×3→C2→T2×3→C3→M2×3→C4→T3×3→C5，所有修改仅提交前一第三轮批准的哈希。完成真实同行、五臂因果、六类压力、任务簇统计、市场 L0–L7、十视角、独立复审、Gate、回滚和安装交付。Market 内核只提供证据，不拥有 PROMOTE 权；不得原地覆盖、读取 sealed holdout 或伪造真实市场/独立能力。
```

## v0.0.0.2 质量与因果硬门

市场实证内核在汇总前强制执行 holdout 污染、assignment、SRM、跨臂暴露、环境一致性、事前 power plan、可选 judge 校准、市场时间和引用完整性，并用 evidence chain 绑定全部制品。详见 `references/market/QUALITY_AND_CAUSALITY.md`。
