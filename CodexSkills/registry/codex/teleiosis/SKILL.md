---
name: teleiosis
description: White-box iteration, evaluation, and controlled evolution for an existing Agent Skill or for Teleiosis itself. Use when a user asks to improve, benchmark, refactor, harden, compare, self-evolve, productize, or package a Skill with frozen baselines, current research, real peers, ten evidence-led system reviews, rollback, genuinely independent review, and installable delivery. Do not use for ordinary code review or direct in-place edits to a production Skill.
license: MIT
compatibility: Python 3.9+ and Git. Live competitor pull requires network access. Formal independent-review PASS requires genuinely isolated SubAgents plus a separate read-only verifier.
metadata:
  author: LinzeColin
  version: "v0.0.0.1"
  language: "zh-CN"
  display_name_zh: "白箱迭代Skill"
  english_brand: "Teleiosis"
  functional_name: "White-Box Iteration Skill"
  architecture: "thin-kernel-open-adapters"
  genesis: "LOCKED_GENESIS"
---

# 白箱迭代Skill

**Teleiosis · White-Box Iteration Skill**

对目标 Skill 或本 Skill 自身进行真实、可验证、可回退的完善。控制来自冻结证据、Gate、Schema、测试和外部审计，不来自不断变长的 Prompt。

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

## 4. 十轮与候选组合

十个默认视角：需求；同行；触发；工作流；安全；架构；评测；运行发布；效率维护；真实产物与未来盲点。

每轮可包含一个或多个可归因 change set：

```text
失败/机会证据 -> 可证伪假设 -> 候选或候选组合 -> 真实评测
-> 与 Baseline/当前最佳比较 -> KEEP | REVERT | NO_CHANGE
```

不为凑轮次制造修改。架构跃迁不必被拆成失去意义的单文件小补丁，但每项变更、命令、责任主体和结果仍须白箱记录。

## 5. 评测与独立治理

- 分开评测触发、任务效果、安全、真实性、成本、时延、安装、兼容、跨模型迁移、维护和未来适应。
- 先过硬门，再检查保护任务负迁移，最后使用 Pareto frontier；任何总分不能补偿硬退化。
- 两轮各六个真正独立 SubAgent 使用隔离上下文和 provider run ID；正式 PASS 还必须绑定运行开始前冻结的外部 review-attestation adapter。软性分歧可由第十三个独立只读 verifier 依据证据解决；未解决的硬域或高严重度问题必须阻断。
- 本地自写 capability/receipt、角色模拟或重复上下文不能证明独立性；runtime 不支持可信独立实例时返回 `INDEPENDENT_REVIEW_UNAVAILABLE`。

## 6. 发布、安装与回炉

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

## 7. 按需读取

- 架构与流程：`ARCHITECTURE.md`、`WORKFLOW.md`、`WHITEBOX_EVIDENCE.md`、`SELF_EVOLUTION.md`。
- 研究与评测：`FRESHNESS_AND_FUTURE.md`、`COMPETITOR_INTELLIGENCE.md`、`LUBAN_GATES.md`、`EVALUATION.md`。
- 治理与交付：`INDEPENDENT_REVIEW.md`、`SECURITY_AND_AUTHORITY.md`、`RELEASE_AND_REHEAT.md`。
- 覆盖与扩展：`REQUIREMENT_COVERAGE.md`、`RUNTIME_ADAPTERS.md`。

以上文件均位于 `references/`，只读取当前阶段所需内容。

## 8. 最短调用

```text
调用白箱迭代Skill（Teleiosis），在安装目录外为 <目标 Skill> 冻结 Baseline 并建立多候选白箱工作区；先完成存在性挑战、时效性研究、至少五个真实同行、生态位、真实产物和冻结评测，再执行十个系统视角的证据化完善、2×6 独立复审、第十三个只读终审、回滚和安装包交付。允许架构跃迁与新模型，不得原地覆盖正式版、读取 sealed holdout 或伪造不可用能力。
```
