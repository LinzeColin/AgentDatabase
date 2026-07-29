# 白箱迭代Skill（Teleiosis）v0.0.0.2

Teleiosis 是面向高风险 Agent Skill 演化的 **Skill Assurance & Evolution Control Plane**。它把“是否值得存在、向谁学习、改了什么、是否真的更好、成本多少、在当前环境是否仍有效、谁负责、如何恢复”转成可执行、可审计、可回滚的合同。

## 本版解决的根因

过去每轮总能发现新漏洞，并非单纯“测试不够多”，而是优化范围只覆盖上一轮已知问题，缺少持续发现未知问题的统一闭环。本版把下列缺口变成机制：

| 旧缺口 | v0.0.0.2 机制 |
|---|---|
| 新线程总能提出新的前沿项目 | 日期化 frontier scan、真实同行 Dataset、事件驱动 reheat、策略记忆 |
| 任务成功但关键约束从未被测到 | `coverage-evaluate` 行为覆盖与硬约束覆盖 |
| Skill 单独好用，装入大库后被误选/遮蔽 | `shadowing-evaluate` 检索、误触发、混淆和 outcome drop |
| 少量随机胜利被当成确定改善 | `stochastic-compare` 预声明 trial/区间规则与 `INCONCLUSIVE` |
| “当前最强”一生成就过时 | 双环境快照、`evidence_lease`、`environment_strength_attestation` |
| 新 Amendment 可被协调重写 | 基础 Genesis + effective Genesis + archive 三重外部哈希锚点 |
| 两条增强分支互相丢能力 | 机制级择优合并，保留 adaptive、market-frontier、utility、verifier/persona 与控制台能力 |

## 状态必须分域

```text
CONTROL_PLANE: PASS（以最终封版证据为准）
BENCHMARK_INTEGRITY: fixture VALID；真实同场 benchmark 仍需外部 runtime
OUTCOME: NOT_PROVEN
COST_EVIDENCE: PARTIAL/UNKNOWN（provider usage 不可得时不得写 0）
INDEPENDENT_REVIEW: UNAVAILABLE（当前环境无真实外部 2×6+1）
ENGINEERING_RELEASE: INSTALLABLE（以最终安装/升级/回滚证据为准）
FORMAL_PROMOTION: BLOCKED
CURRENT_ENVIRONMENT_STRENGTH: NOT_PROVEN，直到全部证据域通过
```

## 基线与 Amendment

基础 Genesis `WBI-GB-001—027` 原文件逐字节不变：

```text
14ab08b9053db4ca87140e59a49f1de8105a718a87ec2d55590c6487c1a77086
```

用户明确授权的 append-only Amendment 新增 `WBI-GB-028`，有效 Genesis 外部锚点为：

```text
fe80c467f8ecbe8343ef0c09ef5e6f9fd9683803c8260c9188998c7e3dfca0a2
```

它不承诺永久世界第一，而是要求每个最终输出携带有效期、当前环境比较边界、证据、未知项与自动 reheat 语义。

## 快速验证与安装

唯一 canonical 安装包：

```text
White-Box-Iteration-Skill-Teleiosis-v0.0.0.2-final.zip
```

```bash
BASE_GENESIS="14ab08b9053db4ca87140e59a49f1de8105a718a87ec2d55590c6487c1a77086"
EFFECTIVE_GENESIS="fe80c467f8ecbe8343ef0c09ef5e6f9fd9683803c8260c9188998c7e3dfca0a2"
ARCHIVE="/absolute/path/White-Box-Iteration-Skill-Teleiosis-v0.0.0.2-final.zip"
ARCHIVE_SHA256="<从外部 SHA256SUMS 获取>"

python3 scripts/wbi.py verify-self --strict \
  --expected-genesis-hash "$BASE_GENESIS" \
  --expected-effective-genesis-hash "$EFFECTIVE_GENESIS"

python3 scripts/wbi.py self-test --timeout 900

python3 scripts/wbi.py install "$ARCHIVE" \
  --skills-root /absolute/path/to/CodexSkills/registry/codex \
  --profile optimizer --verification-level release \
  --expected-genesis-hash "$BASE_GENESIS" \
  --expected-effective-genesis-hash "$EFFECTIVE_GENESIS" \
  --expected-archive-sha256 "$ARCHIVE_SHA256" \
  --result-file /absolute/external/install-result.json
```

Formal mode additionally requires an external, pre-frozen review contract:

```bash
python3 scripts/wbi.py optimize /absolute/path/to/target-skill \
  --workspace /absolute/external/formal-run \
  --run-mode formal --valid-as-of 2026-07-26 \
  --review-attestation-contract /absolute/external/review-contract.json
```

## 关键入口

```bash
python3 scripts/wbi.py doctor /absolute/path/to/target --output /absolute/external/diagnostic.json
python3 scripts/wbi.py adaptive-plan --diagnostic /absolute/external/diagnostic.json --output /absolute/external/plan.json
python3 scripts/wbi.py competitors /absolute/path/to/target --workspace /absolute/external/peers --seed alchaincyf/darwin-skill --seed LearnPrompt/luban-skill
python3 scripts/wbi.py coverage-evaluate --constraints templates/behavior-constraints.json --trajectories templates/behavior-trajectories.jsonl
python3 scripts/wbi.py shadowing-evaluate --records templates/shadowing-records.jsonl
python3 scripts/wbi.py stochastic-compare --results templates/stochastic-results.jsonl --baseline-id baseline --candidate-id candidate
python3 scripts/wbi.py environment-snapshot --help
python3 scripts/wbi.py environment-attest --help
```

## 关键资料

- `delivery/BASELINE_CHANGE_DECISION.md`
- `delivery/MARKET_LEADERSHIP_ANALYSIS.md`
- `delivery/COMPETITIVE_COMPARISON.md`
- `delivery/SELF_ITERATION_REPORT.md`
- `delivery/VERIFICATION_REPORT.md`
- `delivery/CODEX_TASK_PACK_v0.0.0.2.md`
