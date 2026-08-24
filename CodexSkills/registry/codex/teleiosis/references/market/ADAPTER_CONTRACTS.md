# Adapter 契约与工具路由

## 目录

1. 通用原则
2. Executor 输入输出
3. Adapter 类型
4. 模拟与评测工具
5. 红队工具
6. 负载工具
7. 人工与市场 Adapter
8. 归一化与裁决

## 1. 通用原则

Teleiosis 市场实证内核 不绑定供应商。所有外部模型、评测、红队、负载、人工和业务系统均作为无裁决权 Adapter：

```text
Frozen Assignment
→ Adapter Execution
→ Raw Artifact / Trace
→ Normalized Result
→ Teleiosis Market Aggregate
→ Frozen Gate
```

Adapter 不能：

- 改 task、Oracle、Gate 或 budget；
- 把 warning、skip、timeout 或 partial 变成 PASS；
- 隐藏失败 trial；
- 用总体 PASS 掩盖单项非 PASS；
- 替代最终独立 verifier。

## 2. Executor 输入输出

### 2.1 输入 JSONL

每行至少：

```json
{
  "assignment_id": "asg-...",
  "experiment_id": "exp-...",
  "task_id": "task-...",
  "partition": "validation",
  "repetition": 1,
  "sequence": 1,
  "condition_code": "condition-...",
  "prompt": "...",
  "oracle": {"type": "rubric"},
  "protected": true,
  "metadata": {}
}
```

控制器保留 `condition_code → arm_id` 映射。执行器可以在受控端解码以加载对应制品，但不得把映射泄漏给 Candidate 或盲评委。

### 2.2 输出 JSONL

每行至少：

```json
{
  "experiment_id": "exp-...",
  "run_id": "run-...",
  "task_id": "task-...",
  "partition": "validation",
  "arm_id": "candidate",
  "repetition": 1,
  "status": "completed",
  "outcome": {
    "success": true,
    "score": 0.9,
    "accepted": null,
    "human_edit_seconds": 0
  },
  "usage": {
    "tokens": 1000,
    "cost_usd": 0.01,
    "latency_ms": 2000,
    "tool_calls": 2
  },
  "evidence_kind": "offline",
  "protected": true,
  "hard_failures": [],
  "artifact_digest": "exact-arm-digest",
  "trace_digest": "sha256:..."
}
```

必须记录模型、runtime、tool harness 和环境身份，可放在 `metadata`。正向发布结论不得只绑定浮动模型名称或 branch。

### 2.3 市场反馈 JSONL

每条反馈必须绑定真实运行，而不是只绑定实验：

```json
{
  "event_id": "event-...",
  "timestamp": "2026-07-29T00:00:00Z",
  "experiment_id": "exp-...",
  "run_id": "run-...",
  "task_id": "task-...",
  "arm_id": "candidate",
  "artifact_digest": "exact-arm-digest",
  "source": "blind_canary",
  "assignment_id": "asg-...",
  "randomized": true,
  "completion": "complete",
  "consent_ref": "consent-...",
  "incident_severity": "none",
  "accepted": true,
  "would_reuse": true,
  "human_edit_seconds": 15,
  "time_saved_minutes": 20
}
```

额外规则：

- `blind_canary` 必须有 `assignment_id` 且 `randomized=true`；
- `external_acceptor` 和 `micro_bounty` 必须有 `acceptance_ref`；
- `micro_bounty` 必须记录实际 `paid_value_usd`，零支付也应明确为 0；
- `no_skill` 的 `artifact_digest` 必须为 null；其余 arm 必须精确匹配冻结制品；
- feedback 必须能在 results 中找到同一 `run_id + task_id + arm_id`；
- 模拟或代理竞品不能提交可抬升 L5–L7 的市场事件。

## 3. Adapter 类型

| 类型 | 用途 | evidence_kind |
|---|---|---|
| deterministic-test | build、unit、integration、Schema、world state | offline |
| model-runner | Agent/LLM 任务执行 | offline / shadow / canary |
| simulation | 模拟用户、工具、环境和多轮情景 | simulation |
| red-team | 注入、越权、隐私、滥用 | stress |
| load | 服务容量、时延、错误率 | stress |
| human-evaluator | 外部领域验收 | external_acceptance |
| market-telemetry | 完成、返工、复用、付费、事故 | canary / economic / retention / incident |

## 4. 模拟与评测工具

### 4.1 OpenAI Evals 或自有 Harness

适合：结构化任务、确定性 grader、模型评测和回归。锁定 eval 定义、模型 snapshot、sampling、数据版本和运行日志。

### 4.2 Promptfoo

适合：多 provider 对比、Prompt/Agent eval、CI 和红队。将其输出归一化为逐任务结果；Promptfoo 自身 PASS 不是最终 verdict。

### 4.3 Petri 类多 Agent 模拟

适合：模拟用户与工具的多轮场景、假设审计和未知失效发现。其结果最高属于 L2/L3，除非场景来自真实轨迹且由外部证据补强。

### 4.4 自定义 runner

当现有工具不能表达 Skill 安装、文件制品、真实仓库或 world state 时，优先编写薄 Adapter，不重建完整评测平台。

## 5. 红队工具

### 5.1 PyRIT

适合编排模型红队、多轮攻击和目标评分。记录攻击策略、目标模型、版本、成功定义和原始证据。红队 Agent 不能自批修复后的安全 PASS。

### 5.2 Promptfoo Red Team

适合 CI、批量插件和 provider 对比。将发现映射到稳定 failure code，并保留最小复现。

### 5.3 自定义安全夹具

对路径穿越、symlink、ZIP bomb、权限、数据泄漏和未授权副作用，确定性夹具通常比 LLM 攻击更可靠。

## 6. 负载工具

### 6.1 k6

适合 HTTP/service 的 smoke、average、stress、spike、soak 和 breakpoint。用 threshold 将 SLO 变成自动 PASS/FAIL，并导出原始指标。

### 6.2 Locust

适合 Python 用户行为和分布式负载。记录用户模型、spawn rate、worker、运行时和测试数据。

### 6.3 边界

负载工具只能证明基础设施吞吐、时延、错误和恢复，不能证明 Skill 推理、任务质量或市场价值。必须与 Outcome eval 分开。

## 7. 人工与市场 Adapter

### 7.1 外部评委

输入：去标签制品、冻结 Acceptance、冲突披露和最小上下文。输出：accepted、缺陷、返工、证据引用。不得给评委 Candidate 的设计意图或预期答案。

### 7.2 GitHub Issue / PR

Adapter 锁定：repo、commit、Issue、测试、权限和 PR 结果。合并、拒绝、返工和维护者反馈均为事件，不把打开 PR 自动算成功。

### 7.3 微赏金

记录任务、预算、外部验收者、支付条件和实际支付。不能虚构交易或把内部转账冒充市场需求。

### 7.4 产品埋点

只收最小结果和负行为；原始用户内容默认不进入遥测。埋点 schema、consent、retention 和 deletion 必须先冻结。

## 8. 归一化与裁决

每个 Adapter result 必须绑定：

- adapter name/version；
- exact argv/config；
- Subject digest；
- task/assignment/run ID；
- start/end timestamp；
- raw evidence location + SHA-256；
- status 映射；
- usage/cost；
- environment fingerprint；
- failure code。

Market Lab 只接受结构化记录。若 Adapter 输出缺少身份、原始证据或状态映射，标记 `BLOCKED`，不得推断成功。
