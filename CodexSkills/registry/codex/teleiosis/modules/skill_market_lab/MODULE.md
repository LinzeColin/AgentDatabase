---
module_name: skill-market-lab
description: Design, execute, and govern evidence-led market validation for Agent Skills through permanent no-skill controls, baseline/candidate/competitor/ablation experiments, simulations, large-scale datasets, six-category stress testing, shadow replay, opt-in canaries, real user outcomes, cost and acceptance tracking, release gates, rollback, and continuous optimization. Use when users ask to create, benchmark, harden, compare, market-validate, or iteratively improve a Skill by 跑模拟、跑测试、跑极限压力、跑大数据、竞品对照或真实市场反馈，而不是依赖自评。
metadata:
  version: v0.0.0.3
  source_lineage: skill-market-lab-v0.0.0.1
  registry_entry: false
  execution_mode: FULL_NO_ROUTING
---
# 技能市场实证实验室

**Skill Market Lab · Laboratory-to-Market Evidence and Optimization Control Plane**

把 Skill 的“看起来更专业”转化为可复核的因果证据、真实市场结果和可回退的优化决策。核心脚本使用 Python 标准库，不要求模型 API；外部模型、红队、负载和市场渠道只通过可替换 Adapter 接入。

## 1. 先守住证据边界

始终区分：

```text
模拟 / 离线测试 / 压力 / 大数据 = 实验室证据
真实用户 + 真实任务 + 可观察结果与代价 + 独立验收 = 市场证据
```

不得把模拟用户、LLM 评委、文档引用、点赞或单次成功冒充真实市场反馈。不得让生成器成为唯一评委。保留永久 `No Skill` 对照；Skill 只有相对 No Skill 的增量价值才算贡献。

每条市场反馈必须绑定同一实验中的 `task_id + run_id + arm_id + artifact_digest`。只有 Candidate 与冻结主 Comparator 都具备足量、同级、可比较的真实事件时，市场证据才可晋级；Candidate-only、Baseline-only 或与真实运行脱节的反馈不能支持晋级。

## 2. 不可变原则

1. 冻结只读 Baseline；所有修改进入独立 Candidate。
2. Candidate 不得控制 Gate、sealed holdout、blind map、竞品证据、评分标准或最终批准。
3. 同一任务在相同模型、运行时、工具、权限和预算下比较 `No Skill / Baseline / Candidate / Competitor / Ablation`。
4. 保存原始结果、失败、工具轨迹、成本、时延、制品哈希和运行身份；`NOT_RUN / BLOCKED / UNKNOWN` 永不折算为 PASS。
5. 先过身份、安全、隐私、授权、holdout 和保护任务硬门，再比较效果与成本；总体平均不得补偿关键退化。
6. 将真实竞品、模拟竞品和代理证据分别标记为 `real / simulated / proxy`；只有锁定并真实执行的竞品才能参与直接性能对比，模拟竞品只能提出假设。
7. 真实用户数据默认不上传原始 Prompt、输出、文件、凭据或个人信息；市场任务必须有 consent reference。
8. 不在 Skill 安装目录保存运行数据。代码仓只保存 Skill、Schema 和模板；实验数据进入代码目录外的工作区或授权私有事实层。
9. 不依赖活动 Agent、聊天线程、本机常驻进程或 macOS launchd。长时间测试必须由 CI、受控 runner 或运行系统执行并记录状态。
10. 每个变化只允许 `KEEP / REVERT / NO_CHANGE`；达到停止条件后进入 Owner Gate，不以“还可更完美”为由无限循环。

## 3. 唯一状态机

```text
CONTEXT_CAPTURE
→ RESEARCH_AND_REUSE
→ PREBUILD
→ TEN_LENS_REVIEW
→ REMEDIATION
→ BUILDER_READINESS
→ OWNER_GATE
→ SEALED_TASKPACK
→ BUILD_LAST_MILE
→ FROZEN_CANDIDATE
→ VERIFY_AND_RELEASE
→ POST_DEPLOY_OBSERVATION
```

把当前状态写入工作区 `CANONICAL_STATE.json`。状态变化必须绑定事实、制品或证据；只改措辞不算推进。

## 4. 最短启动

从 Skill 根目录执行：

```bash
python3 scripts/market_lab.py doctor --skill-root .

python3 scripts/market_lab.py init-workspace \
  --workspace /absolute/path/outside/skills/market-lab-run \
  --subject-name target-skill \
  --subject-version v0.0.0.1 \
  --subject-digest <exact-tree-or-archive-digest>
```

编辑工作区 `config/experiment.json`，冻结目标、五臂、预算、Gate、隐私和证据目标，然后：

```bash
python3 scripts/market_lab.py validate-spec \
  --spec /path/run/config/experiment.json

python3 scripts/market_lab.py validate-tasks \
  --tasks /path/run/datasets/source-tasks.jsonl
```

## 5. 执行完整闭环

### 5.1 捕获目标与权限

写明：目标 Skill、真实用户、问题、范围、非目标、基线、资源与成本上限、数据权限、生产副作用授权、成功指标、Kill Criteria 和回滚边界。仅当方向、权限、数据、成本、法律或不可逆事项无法推断时提出一个合并后的最小问题。

### 5.2 研究同行并冻结竞品

研究 5–12 个当前真实同行或相似产品，记录 URL、访问日期、版本或 commit、许可证、可观察产物、采用与拒绝理由。至少保留：

- 一个永久 No Skill 对照；
- 当前正式 Baseline；
- 独立 Candidate；
- 一个锁定且可真实执行的同行；
- 一个能定位机制贡献的 Ablation。

需要竞品协议时读取 [COMPETITOR_PROTOCOL.md](references/COMPETITOR_PROTOCOL.md)。

冻结 5–12 个同行登记并先验证：

```bash
python3 scripts/market_lab.py validate-competitors \
  --registry assets/templates/competitors.example.json
```

### 5.3 构造数据与 sealed holdout

按来源和失效机制，而不是按数量堆重复样本。至少拆分：

```text
development / validation / sealed_holdout / adversarial
market_live / incident_replay
```

为 Candidate 生成不含 holdout 的视图：

```bash
python3 scripts/market_lab.py holdout-manifest \
  --tasks /trusted/controller/all-tasks.jsonl \
  --output /trusted/controller/HOLDOUT_MANIFEST.json

python3 scripts/market_lab.py candidate-view \
  --tasks /trusted/controller/all-tasks.jsonl \
  --output /candidate-visible/tasks.jsonl
```

详细数据合同与大数据策略见 [DATA_AND_STRESS.md](references/DATA_AND_STRESS.md)。

### 5.4 生成六类压力变体

```bash
python3 scripts/market_lab.py expand-stress \
  --input /path/base-tasks.jsonl \
  --output /path/stress-tasks.jsonl \
  --categories all \
  --variants-per-category 2 \
  --seed 20260729 \
  --include-original
```

六类是：语义、上下文、工具、安全、版本、经济。基础设施另跑 smoke、average load、stress、spike、自动化 soak 和 breakpoint。压力定义见 [DATA_AND_STRESS.md](references/DATA_AND_STRESS.md)。

### 5.5 生成盲化配对任务

```bash
python3 scripts/market_lab.py make-assignments \
  --spec /path/run/config/experiment.json \
  --tasks /trusted/controller/tasks.jsonl \
  --output /trusted/controller/assignments.jsonl \
  --blind-map-output /trusted/controller/blind-map.json
```

只向执行器提供其所需任务；只向评委提供去标签输出与冻结 Oracle；blind map 留在控制器。每个声明任务切片默认至少 3 次独立 trial，关键结论使用配对差异和不确定性，不用一次性分数。

因果与证据等级见 [EVIDENCE_AND_CAUSALITY.md](references/EVIDENCE_AND_CAUSALITY.md)。

### 5.6 接入执行器

执行器只读取 JSONL assignment 并写 JSONL result；它没有裁决权。可接入模型 runner、Promptfoo、PyRIT、Petri、k6、Locust、CI、人工评委或真实业务渠道，但必须统一归一化：

```text
输入任务 + 精确 condition + 精确 Subject + 环境与预算
→ 原始轨迹与制品
→ 结构化 result
```

Adapter 契约见 [ADAPTER_CONTRACTS.md](references/ADAPTER_CONTRACTS.md)。

### 5.7 收集真实市场反馈

按证据强度逐级推进：

1. Shadow replay：只读重放真实历史轨迹；
2. Opt-in 匿名反馈：完成、返工、节省、复用意愿；
3. 盲化 Canary / A-B：随机分流并设置自动终止；
4. 真实 Issue、PR、交付物或微赏金：由外部维护者或专家盲验收；
5. 留存、重复使用、付费、实际节省、回滚与事故：形成最强市场证据。

先匿名化：

```bash
export MARKET_LAB_HASH_SALT='<runtime-secret-at-least-16-chars>'
python3 scripts/market_lab.py anonymize-feedback \
  --spec /path/run/config/experiment.json \
  --input /path/raw-feedback.jsonl \
  --output /path/anonymized-feedback.jsonl
```

完整期程、四种现实机制与中止规则见 [MARKET_FEEDBACK.md](references/MARKET_FEEDBACK.md)。

### 5.8 汇总、Gate 与下一轮计划

```bash
python3 scripts/market_lab.py aggregate \
  --spec /path/run/config/experiment.json \
  --results /path/run/results.jsonl \
  --feedback /path/run/anonymized-feedback.jsonl \
  --output-dir /path/run/reports

python3 scripts/market_lab.py gate \
  --spec /path/run/config/experiment.json \
  --summary /path/run/reports/SUMMARY.json \
  --output /path/run/reports/GATE.json

python3 scripts/market_lab.py plan-next \
  --spec /path/run/config/experiment.json \
  --summary /path/run/reports/SUMMARY.json \
  --gate /path/run/reports/GATE.json \
  --output /path/run/reports/NEXT_ITERATION.json
```

唯一决策集合：

```text
PROMOTE | KEEP_BASELINE | REVERT | REHEAT_REQUIRED | BLOCKED
```

把 `NEXT_ITERATION` 中每个假设交给白箱迭代流程，在独立 Candidate 上实现；重跑相同冻结合同和新 incident regression。不得让本 Skill 自动修改正式 Skill。指标、Gate、Pareto 和停止合同见 [METRICS_GATES_AND_OPTIMIZATION.md](references/METRICS_GATES_AND_OPTIMIZATION.md)。

## 6. 证据等级

| 等级 | 证据 | 能否宣称市场验证 |
|---|---|---|
| L0 | Schema、安装、权限、静态检查 | 否 |
| L1 | No Skill / Skill ON 配对离线测试 | 否 |
| L2 | 模拟用户、工具和多 Agent 情景 | 否 |
| L3 | 红队、故障、压力、长上下文 | 否 |
| L4 | 真实历史重放与 Shadow | 仅部分 |
| L5 | 自愿真实用户 Canary / A-B | 是，初级 |
| L6 | 真实交付、PR、微赏金、外部盲验收 | 是，强 |
| L7 | 重复使用、留存、付费、节省与事故率 | 是，最强 |

实验目标为 `market_validated` 时，Candidate 与冻结主 Comparator 的共同证据至少达到 L6；模拟竞品和模拟用户永远不能抬升到 L5。

## 7. 硬门与中止

出现以下任一项立即阻断或回退：

- 身份或制品哈希不匹配；
- 市场反馈找不到其绑定的真实 run，或反馈的 arm / artifact 与 run 不一致；
- sealed holdout 泄漏、Oracle 漂移或 blind map 泄漏；
- 安全违规、隐私泄漏、未授权副作用；
- 关键保护任务退化；
- 真实市场出现 high / critical 事故；
- 超过 Token、费用、时延、工具调用或副作用预算；
- 缺少 consent、原始证据或可复跑路径；
- Candidate、生成器或模拟评委成为唯一批准者。

命令安全、隐私、恢复和封存见 [PRIVACY_SECURITY_AND_RUNBOOK.md](references/PRIVACY_SECURITY_AND_RUNBOOK.md)。

## 8. 输出合同

每次有效运行至少保留：

```text
experiment.json
exact subject / arm identities
source task registry + sealed holdout manifest
assignments + controller-only blind map
raw results + trace/artifact digests
arm-bound anonymized market feedback
SUMMARY.json / SUMMARY.md
GATE.json / GATE.md
NEXT_ITERATION.json / NEXT_ITERATION.md
tree manifest + SHA-256
```

对人输出先给结论与下一步，再给差分、证据和剩余风险。不要倾倒完整研究日志。正式独立复审能力不可用时，明确标记 `INDEPENDENT_REVIEW_UNAVAILABLE` 或 `role_separated_same_model`，不得伪造 PASS。

## 9. 按需读取

| 当前任务 | 读取文件 |
|---|---|
| 控制面、状态机、存储和角色 | [ARCHITECTURE.md](references/ARCHITECTURE.md) |
| 证据阶梯、五臂因果与统计 | [EVIDENCE_AND_CAUSALITY.md](references/EVIDENCE_AND_CAUSALITY.md) |
| 大数据、分区和六类压力 | [DATA_AND_STRESS.md](references/DATA_AND_STRESS.md) |
| 市场反馈期程与现实机制 | [MARKET_FEEDBACK.md](references/MARKET_FEEDBACK.md) |
| 真实/模拟/代理竞品 | [COMPETITOR_PROTOCOL.md](references/COMPETITOR_PROTOCOL.md) |
| 指标、Gate、优化和停止 | [METRICS_GATES_AND_OPTIMIZATION.md](references/METRICS_GATES_AND_OPTIMIZATION.md) |
| 隐私、安全、失败和封存 | [PRIVACY_SECURITY_AND_RUNBOOK.md](references/PRIVACY_SECURITY_AND_RUNBOOK.md) |
| 外部 runner 与工具接入 | [ADAPTER_CONTRACTS.md](references/ADAPTER_CONTRACTS.md) |

## 10. 最短调用语句

```text
调用 skill-market-lab，为目标 Skill 在安装目录外建立只读 Baseline、独立 Candidate、永久 No Skill 对照、真实竞品与消融五臂实验；冻结数据分区、sealed holdout、预算、Gate 和回滚，运行模拟、测试、六类压力和流式大数据，再通过 Shadow、opt-in Canary、真实交付/微赏金、复用和成本事件形成市场证据。严格区分实验室与市场证据，输出 PROMOTE / KEEP_BASELINE / REVERT / REHEAT_REQUIRED / BLOCKED 及下一轮可证伪优化计划，不得自评自批或读取 holdout。
```
