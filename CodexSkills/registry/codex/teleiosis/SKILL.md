---
name: teleiosis
description: Full non-routed white-box Skill iteration that always runs Raw Teleiosis, Skill Market Lab, Product Reality Lab, and Arena Lab over one evolving Candidate, then prepares a read-only handoff for an external Verifier. Use to improve, compare, stress-test, market-test, reality-test, benchmark, package, install, upgrade, rollback, or release an Agent Skill. One run is three groups of three T-C-S-C-P-C-A-C rounds. Do not use for ordinary code review or unapproved production edits.
license: MIT
compatibility: Python 3.9+; standard library only. Native competitor runs, field users, production side effects, registry push, and formal independent review require separately authorized environments.
metadata:
  author: LinzeColin
  version: "v0.0.0.5"
  language: "zh-CN"
  display_name_zh: "白箱迭代Skill"
  english_brand: "Teleiosis"
  functional_name: "White-Box Iteration Skill"
  architecture: "single-skill-four-built-in-full-run-engines"
  scope_mode: "FULL_NO_ROUTING"
  genesis: "LOCKED_GENESIS_PLUS_APPEND_ONLY_AMENDMENTS"
---

# Teleiosis v0.0.0.5

一个安装项，四个逻辑引擎，一个连续 Candidate，一条完整 Run，一个外部终审者。

## 0. 第一条命令

```bash
python3 START_HERE.py doctor
python3 START_HERE.py install
```

Doctor 失败即停止；不得重签 Genesis、忽略 Manifest 或把本地自检冒充正式 PASS。

## 1. 固定非路由执行

```text
一轮：T1 → C1 → S1 → C2 → P1 → C3 → A1 → C4
一组：连续三轮
一次 Run：连续三组，共 36 个 T/S/P/A 阶段
```

- T：白箱控制、Genesis、Candidate、硬门、回滚、Taskpack、Skill Audit。
- S：同行、因果、市场、成本、许可证与证据等级。
- P：真实流程、全栈、故障、恢复、防呆、Field 边界。
- A：开发/密封竞技、同预算、Bootstrap、Pareto、失败轨迹。
- External Verifier：冻结 Subject 的唯一正式 PASS 权限。

四个引擎每次读取完整 Capability Manifest；不得用 router 缩减。每项能力只能记录 `EXECUTED / NOT_APPLICABLE_WITH_REASON / NOT_RUN / BLOCKED`，其中 NOT_RUN 不算完成。

## 2. Candidate 与回滚

所有阶段操作同一 Candidate lineage。真实内容变化必须产生新 revision、parent、tree digest、变更清单、证据与回滚指针。动态 hash 是事后证据，不是移动仓库的固定前置门。`KEEP / REVERT / NO_CHANGE / BLOCKED` 均保留记录；失败 Candidate 不删除。

## 3. v0.0.0.3 非降级继承

`legacy/v0.0.0.3/` 保存当前 v3 的原始 SKILL、README 和 444 条 Manifest 快照。v5 保留 v3 的 T/S/P 全量非路由、连续 Candidate、三轮×三组、移动 main 适配、证据、安装和回滚语义，并增加 A、Stage 0、Taskpack、三次 Skill Audit、8192 条回归语料、Doctor 与 Verifier handoff。

本包不伪称取得 v3 全部 444 个文件字节；以可执行功能、原始快照、继承矩阵和回归门证明非降级。

## 4. Stage 0 Semantic Reconcile

```bash
python3 scripts/teleiosis.py semantic-reconcile \
  --repository /path/to/latest-main \
  --spec templates/semantic-reconcile-spec.example.json \
  --output /outside/stage0-report.json
```

每项任务分类为 `satisfied / apply / adapt / equivalent / conflict / blocked / obsolete`。保留更新、更好的上游实现；普通字节漂移走 adapt；身份、Genesis、未来高版本或安全边界冲突才阻断。

## 5. 三次 Skill Audit

Pass A 在 Baseline 后；Pass B 在重大 Candidate 变化后；Pass C 在冻结封包前。每次调用记录 Skill/version、目的、输入 hash、制品、Finding、新机制、关闭风险、Developer Burden Delta 与重跑触发条件。输入没变化不得重复凑数。

人物专家只有实际载入 dossier、claim_id 与分歧才计入。当前包没有这些字节，因此明确使用 `INSUFFICIENT_ROSTER_FALLBACK` 和中立六角色，不冒充人物专家或独立模型。

## 6. Taskpack 与 Fresh Builder

```bash
python3 scripts/teleiosis.py taskpack validate
python3 scripts/teleiosis.py taskpack fresh-builder
```

Project Input、唯一状态机、六类无环 Task DAG、Acceptance→Task→Test→Oracle→Evidence→Artifact、最后一公里和回滚全部机器验证。Build Agent 只处理目标仓写权限、真实凭证、供应商控制台、生产环境和兼容性反馈。

## 7. Arena Lab

```bash
python3 scripts/arena_lab.py freeze --spec INPUT.json --output FROZEN.json
python3 scripts/arena_lab.py score --spec FROZEN.json --observations RESULTS.jsonl --output RESULT.json
```

开发竞技场可反复诊断；密封竞技场不能让 Candidate 读取隐藏集或修改评分器。效果榜、治理榜和 Pareto 前沿分开。L1 结构、L2 模拟、L3 原生同场、L4 生产盲测不得混写。

## 8. 大样本回归

```bash
python3 scripts/teleiosis.py regression
python3 scripts/validate_release.py --output-dir /outside/teleiosis-v5-validation --runs 3
```

`fixtures/regression/teleiosis-v5-regression.jsonl` 含 8192 条确定性案例，覆盖 T/S/P/A 与 development、selection、hidden_iid、hidden_ood、redteam、regression 六分区。它是离线回归证据，不是真实市场证据。

## 9. 外部 Verifier 交接

```bash
python3 scripts/teleiosis.py verifier-handoff build --output /outside/acceptance-review.zip
python3 scripts/teleiosis.py verifier-handoff validate --zip /outside/acceptance-review.zip
```

handoff 绑定精确 Candidate tree、Acceptance 与 Manifest，内部状态始终 `NOT_ISSUED`。正式 PASS 只能由外部独立 Verifier 产生。

## 10. 运行控制器

```bash
python3 scripts/teleiosis_run.py contract
python3 scripts/teleiosis_run.py init --subject /path/to/skill --workspace /outside/run
python3 scripts/teleiosis_run.py next --workspace /outside/run --result /outside/result.json
python3 scripts/teleiosis_run.py status --workspace /outside/run
python3 scripts/teleiosis_run.py validate-run --workspace /outside/run --require-complete
```

Workspace 根目录只保留 Candidate、隐藏控制面和稳定结果文件。未知字段、错序、漏能力、缺证据、凭证、符号链接、路径穿越、超限输入全部 fail-closed。

## 11. 按需读取

- 完整运行：`references/FULL_RUN_CONTRACT.md`
- v3 继承：`references/V3_INHERITANCE.md`
- Stage 0：`references/STAGE0_SEMANTIC_RECONCILE.md`
- Skill 调用：`references/SKILL_CATALOG_CALLS.md`
- 人物边界：`references/PERSONA_TEAM_BOUNDARY.md`
- Arena：`references/ARENA_LAB_CONTRACT.md`
- 原生同场：`references/NATIVE_ARENA_EXECUTION.md`
- Verifier：`references/EXTERNAL_VERIFIER_HANDOFF.md`
- 安装：`INSTALL.md`
- 架构：`architecture/`

## 12. 证据边界

本地工程、测试、回归、安装、回滚、封包与冷解压可以在包内证明。目标 Registry 写入、官方原生竞品胜负、真实市场、生产盲测与正式独立验收没有运行时必须保持 `NOT_RUN / NOT_CLAIMED / PENDING / UNAVAILABLE`。
