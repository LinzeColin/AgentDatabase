---
name: teleiosis
description: White-box iteration for an Agent Skill or Teleiosis itself. Use to challenge existence, research real peers, evolve and benchmark Candidates, prevent negative optimization, bind current-environment evidence, govern independent review, and deliver reversible packages; not for ordinary code review or in-place production edits.
license: MIT
compatibility: Python 3.9+ and Git. Live frontier research needs network; outcome and formal claims need sealed external runtime evidence.
metadata:
  author: LinzeColin
  version: "v0.0.0.2"
  language: "zh-CN"
  display_name_zh: "白箱迭代Skill"
  english_brand: "Teleiosis"
  functional_name: "White-Box Iteration Skill"
  architecture: "thin-kernel-open-adapters"
  genesis: "LOCKED_BASE_PLUS_APPEND_ONLY_AMENDMENT"
---

# 白箱迭代Skill

**Teleiosis — White-Box Iteration Skill**

对白箱迭代Skill自身或目标 Skill 做真实、可验证、可回退的持续完善。约束来自冻结合同、外部锚点、证据与硬门，不来自长 Prompt。

## 0. 启动

```bash
BASE_GENESIS=14ab08b9053db4ca87140e59a49f1de8105a718a87ec2d55590c6487c1a77086
EFFECTIVE_GENESIS=fe80c467f8ecbe8343ef0c09ef5e6f9fd9683803c8260c9188998c7e3dfca0a2

python3 scripts/wbi.py verify-self --strict \
  --expected-genesis-hash "$BASE_GENESIS" \
  --expected-effective-genesis-hash "$EFFECTIVE_GENESIS"

python3 scripts/wbi.py optimize /absolute/path/to/target \
  --workspace /absolute/external/run \
  --run-mode engineering --valid-as-of 2026-07-26
```

能力不足时真实 `BLOCKED`；`OUTCOME_NOT_PROVEN` 与 `FORMAL_PROMOTION_BLOCKED` 是合法状态；不得修改/重签 Genesis，不得把 engineering、fixture 或角色模拟冒充 outcome、独立复审或 formal promotion。

## 1. 不可破坏合同

- 冻结只读 Baseline，只修改唯一 Candidate；目标 Skill 与 Teleiosis 采用同等或更严格的双白箱证据。
- 首个 patch 前完成存在性挑战、时效扫描、至少五个真实同行、生态位、真实产物以及 research/benchmark/holdout/budget/review seal。
- Candidate 不得读取 sealed holdout 正文或控制考试、复审包、receipt root、批准者；失败 Candidate、`NO_CHANGE` 和回滚均保留。
- 单次 run 有界且不递归；允许 incremental、bundle、architecture-leap、clean-slate、population/Pareto 或未来可替换策略。
- 当前环境领先状态必须有第二次环境快照、证据租约、行为覆盖、Skill 库遮蔽、同预算 outcome/cost 证据；证据不足只允许 `NOT_PROVEN/BLOCKED/REGRESSED/REHEAT_REQUIRED`。

## 2. 防止假优化

Benchmark 分轨：A 优化效果；B 产品化效果；C assurance 控制面。触发、任务、安全、真实性、行为覆盖、库内选择、成本、时延、迁移、安装和未来适应分别评测；硬退化不可补偿。

`utility-gate`：硬退化→`REVERT`；无实质收益→`KEEP_BASELINE`；只有实质收益且无硬退化→`KEEP_CANDIDATE`。随机结果未达到预声明证据规则时保持 `INCONCLUSIVE`，未知值不得记 0。

## 3. 独立责任链

正式 review 需要外部 2×6 reviewer 与独立只读 verifier；每席绑定唯一外部 receipt、context/provider run 和签名。`expert-panel-export`、`verifier-export` 只导出工作合同，不生成 verdict 或独立性。

## 4. 按需读取

- 流程/白箱：`references/WORKFLOW.md`、`references/WHITEBOX_EVIDENCE.md`
- 前沿/时效：`references/CURRENT_ENVIRONMENT_STRENGTH.md`、`references/FRESHNESS_AND_FUTURE.md`
- 覆盖/遮蔽/随机性：`references/BEHAVIOR_COVERAGE.md`、`references/SKILL_LIBRARY_SHADOWING.md`、`references/STOCHASTIC_EVIDENCE.md`
- 同行/效用：`references/PEER_TAXONOMY.md`、`references/NON_NEGATIVE_UTILITY.md`
- 运行/状态：`references/STATUS_SEMANTICS.md`、`references/OPERATOR_RUN_MODES.md`
- 复审/发布：`references/INDEPENDENT_REVIEW.md`、`references/RELEASE_AND_REHEAT.md`、`delivery/INSTALL.md`
