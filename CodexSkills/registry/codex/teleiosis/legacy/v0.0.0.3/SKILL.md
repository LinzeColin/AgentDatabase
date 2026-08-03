---
name: teleiosis
description: Full non-routed white-box Skill iteration that always runs Raw Teleiosis, Skill Market Lab, and Product Reality Lab over the same evolving Candidate. Use to improve, compare, stress-test, market-test, reality-test, self-evolve, validate, package, install, or release an Agent Skill. One run is three groups of three T-C-S-C-P-C rounds; C is the iteration object itself, not a fixed SHA checkpoint. Do not use for ordinary code review or direct unapproved production edits.
license: MIT
compatibility: Python 3.9+ and Git. Live competitors, field users, browser/API/load/security adapters, GitHub push, and formal independent review require their own authorized environments.
metadata:
  author: LinzeColin
  version: "v0.0.0.3"
  language: "zh-CN"
  display_name_zh: "白箱迭代Skill"
  english_brand: "Teleiosis"
  functional_name: "White-Box Iteration Skill"
  architecture: "single-skill-three-built-in-full-run-modules"
  scope_mode: "FULL_NO_ROUTING"
  genesis: "LOCKED_GENESIS"
---

# 白箱迭代Skill

**Teleiosis v0.0.0.3**

对目标 Skill 或 Teleiosis 自身进行真实、可验证、可回退的持续优化。正式运行始终使用同一个外部 Candidate 工作副本，并全量执行 T、S、P 三个内置模块；S/P 不注册为独立 Skill，外部 Verifier 保持独立。

## 0. 启动

```bash
python3 scripts/wbi.py verify-self --strict
python3 scripts/teleiosis_run.py contract
```

验证失败即停止；不得自动修改或重签 Genesis。自包含锚用于安装可用性，显式外部锚仍可作为更强防协同篡改证据。

## 1. 固定非路由 Run

```text
一轮：T1 -> C1 -> S1 -> C2 -> P1 -> C3
一组：连续三轮
一次 Run：连续三组
```

`T`、`S`、`P` 每次读取完整 Capability Manifest，不经 router 选择。单一路径重复轮跑：相邻模块交叉验证、每组复审 lineage 与回归影响、Run 末执行最终反证复审。每个能力必须记录 `EXECUTED / NOT_APPLICABLE_WITH_REASON / NOT_RUN / BLOCKED`；N/A 必须先检查并解释，NOT_RUN 不能折算完成。

`C` 是迭代对象本身的 Candidate revision。T/S/P 可以基于各自证据修改当前 Candidate，然后形成下一个 C；也可 `NO_CHANGE`。revision 必须记录 parent、变更文件、diff、测试、理由和回滚。动态 content fingerprint 是事后证据，不是预设 SHA，不得锁死移动 main、普通上游漂移或下一阶段修改。

## 2. T - Raw Teleiosis

完整执行 Genesis、需求与存在性挑战、当前环境、至少五个真实同行、生态位、真实产物、只读 Baseline/独立 Candidate、冻结 Acceptance 与 sealed holdout、十视角、因果 change set、硬门、保护任务、复审边界、打包、安装、回滚和 reheat。只有 T 能形成内部 DecisionReceipt。

## 3. S - Skill Market Lab

完整执行 No Skill/Baseline/Candidate/Competitor/Ablation 五臂因果实验，语义/上下文/工具/安全/版本/经济六类压力，大数据分层与任务簇统计，竞品、Shadow、Canary/A-B、真实任务/结果/代价、市场 L0-L7、隐私同意和事故回流。S 只供证，最高为 `EVIDENCE_READY_FOR_TELEIOSIS`。

## 4. P - Product Reality Lab

完整执行五类参照、开源 provenance、源码/运行时 Census 对账，Surface/State/Transition/Role/Data/Fault/Oracle/Evidence 八维覆盖，前端、API、数据、性能、可靠性、安全、Chaos、恢复、防呆、Negative Control/Mutation、Field 分级和缺陷收敛。P 只输出 `READY_FOR_VERIFIER / MORE_EVIDENCE_REQUIRED / FIELD_VALIDATION_PENDING / BLOCKED`。

## 5. Candidate 与证据

所有模块操作同一 Candidate lineage。每次真实内容变化产生新 revision；旧证据不能冒充新 revision 证据。候选身份由稳定 `candidate_id + revision_number + parent_revision_id + workspace path` 表示；hash 只作为可选动态指纹。不得使用固定 repo HEAD、目标文件 SHA 或 overlay SHA 作为安装/合并前提。

## 6. 完整运行控制器

```bash
python3 scripts/teleiosis_run.py init --subject /path/to/skill --workspace /outside/run
python3 scripts/teleiosis_run.py next --workspace /outside/run --module T --result AUTO --evidence /path/to/evidence.json --decision KEEP
python3 scripts/teleiosis_run.py status --workspace /outside/run
python3 scripts/teleiosis_run.py validate --workspace /outside/run --require-complete
```

控制器拒绝错序、漏 T/S/P、路由缩减、缺 parent revision、无回滚指针、NOT_RUN 被当完成和嵌套外层 Run。它不要求 Candidate 保持固定 hash。

## 7. 防呆与低熵输入输出

- 初始化前校验 Subject/Workspace 不嵌套、无符号链接、容量在上限内；失败时不创建半成品；
- Capability Result 采用严格白名单 Schema、固定顺序和完整能力表，未知字段、错模块、错阶段、缺证据、凭证或超限输入全部 fail-closed；
- Workspace 根目录仅保留 Candidate、隐藏控制面和 5 个稳定的人机结果文件；阶段输入被消费后自动清理；
- `NO_CHANGE` 与真实 Delta 冲突时阻断并保留修改，`KEEP` 无 Delta 自动归一化，`REVERT` 保存 rejected archive 并恢复父 Candidate；
- 每个阶段先完成 Evidence/Manifest/Revision，再原子更新 State；任何失败恢复 Candidate、revision-store 和公开状态；
- CLI 正常与错误均只输出一个 JSON 文档，不打印 traceback/usage 噪声，敏感值递归脱敏；
- 外部子进程按固定尾缓冲流式读取，超过硬总输出上限或 timeout 时终止整个进程组，防止内存爆炸和孤儿进程；
- 任务包结果文件只能原子写入包外普通路径，权限为 `0600`，拒绝包内路径和符号链接；
- revision-store 的动态 ref 只用于精确回滚，不是仓库合并、安装或下一阶段的 SHA 前置门。

## 8. 安装与移动 main

任务包根目录的 `install.py` 可直接安装或升级。AgentDatabase 使用 `scripts/integrate_repo.py` 做语义适配，使用 `scripts/publish_main.py` 从最新远端 main 临时 clone 并在推送竞争时重新基于最新 main 重试。普通字节差异属于 `adapt`，不是自动 `conflict`；只有身份、Genesis、未来高版本、仓库规则或安全边界冲突才阻断。

## 9. 真实结论

模拟、合成大数据、压力流量和 LLM judge 不等于真实市场。真实用户、真实任务、结果/代价、授权和可审计轨迹缺一时写 `NOT_CLAIMED`。正式 PASS 归外部独立 Verifier。

## 10. 按需读取

- 流程：`references/FULL_RUN_CONTRACT.md`
- 五源：`references/FIVE_SOURCE_INTEGRATION.md`
- 安装：`delivery/INSTALL_AND_GITHUB.md`
- 内置模块：`modules/*/CAPABILITIES.json` 与 `MODULE.md`
- 市场：`references/market/`
- 产品：`references/product/`

## 11. 最短调用

```text
调用 Teleiosis v0.0.0.3，以 T1→C1→S1→C2→P1→C3 为一轮，连续三轮为一组、连续三组为一次完整 Run。禁止路由，T/S/P 各自全量运行；C 是同一迭代对象的连续 Candidate revision，不是 SHA 检查点。依据竞品、因果、大数据、六类压力、产品八维、真实任务/市场/Field、交叉验证与复审持续优化，保留精确 diff、测试和回滚，最后交给独立 Verifier。
```
