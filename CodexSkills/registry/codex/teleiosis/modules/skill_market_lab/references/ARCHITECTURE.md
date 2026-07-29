# 架构与责任边界

## 目录

1. 使命与非目标
2. 角色
3. 控制面架构
4. 状态与数据流
5. 存储与权威
6. 运行方式
7. 失败与恢复

## 1. 使命与非目标

Skill Market Lab 是一个**证据控制面**，不是模型供应商、在线遥测 SaaS、自动发布机器人或自我批准系统。它把外部执行器产生的观察统一成可复核证据，再依据预先冻结的合同做晋级、保留、回退或回炉判断。

目标：

- 证明目标 Skill 相对 No Skill 的边际价值；
- 比较 Baseline、Candidate、真实竞品与消融版本；
- 覆盖模拟、功能、压力、规模、故障与真实市场证据；
- 把失败与反馈转成可证伪的下一轮改进；
- 保证精确身份、盲化、holdout、预算、隐私和回滚。

非目标：

- 不自动修改正式 Skill；
- 不以模拟代替真实用户；
- 不为所有项目强制安装同一模型、评测或负载工具；
- 不在代码仓保存长期运行数据；
- 不要求开发 Agent 持续在线或等待真实时间；
- 不用单一总分替代安全、真实性和关键任务硬门。

## 2. 角色

| 角色 | 责任 | 不得做 |
|---|---|---|
| Owner | 批准方向、范围、权限、成本、法律与不可逆动作 | 承担普通技术选型 |
| Preparation / Experiment Controller | 研究、冻结合同、建数据、盲化、聚合与封存 | 修改 Baseline、读取后放宽 Gate |
| Candidate Builder | 在独立工作区实现冻结 change set | 读取 holdout、blind map 或改评分 |
| Executor Adapter | 执行任务并输出原始观察 | 写最终 verdict |
| Evaluator / Oracle | 按冻结标准评价去标签结果 | 知道 Candidate 身份或变更意图 |
| Market Adapter | 收集经授权的真实用户、交付、成本和行为事件 | 默认上传原始私有内容 |
| Verifier | 验收精确 Subject、证据链与 world state | 相信 Builder 自评或直接修代码 |
| Runtime System | 调度、预算、熔断、日志、备份与恢复 | 依赖聊天线程、活动 Agent 或人工保活 |

无法提供真实隔离 Agent 时，只能标记 `role_separated_same_model`。正式独立结论需要独立上下文、独立运行身份和只读 verifier。

## 3. 控制面架构

```text
                    ┌──────────────────────────┐
                    │ Frozen Experiment Contract│
                    │ scope / arms / budgets    │
                    │ metrics / gates / privacy │
                    └─────────────┬────────────┘
                                  │
           ┌──────────────────────┼──────────────────────┐
           │                      │                      │
┌──────────▼──────────┐ ┌─────────▼─────────┐ ┌──────────▼──────────┐
│ Task & Data Control │ │ Competitor Control│ │ Identity & Integrity│
│ partitions/holdout  │ │ real/sim/proxy    │ │ hashes/blind map    │
└──────────┬──────────┘ └─────────┬─────────┘ └──────────┬──────────┘
           └──────────────────────┼──────────────────────┘
                                  │ assignments
                     ┌────────────▼────────────┐
                     │ Executor Adapter Layer  │
                     │ model/red-team/load/human│
                     └────────────┬────────────┘
                                  │ raw results
          ┌───────────────────────┼────────────────────────┐
          │                       │                        │
┌─────────▼─────────┐  ┌──────────▼──────────┐  ┌──────────▼──────────┐
│ Lab Evidence      │  │ Market Evidence     │  │ Trace/Artifact Store│
│ offline/sim/stress│  │ canary/accept/value │  │ exact digests       │
└─────────┬─────────┘  └──────────┬──────────┘  └──────────┬──────────┘
          └───────────────────────┼────────────────────────┘
                                  │
                     ┌────────────▼────────────┐
                     │ Aggregate + Hard Gates  │
                     │ paired delta / CI / cost│
                     └────────────┬────────────┘
                                  │
              ┌───────────────────┼────────────────────┐
              │                   │                    │
         PROMOTE          KEEP / REVERT       REHEAT / BLOCKED
              │                   │                    │
              └───────────────────▼────────────────────┘
                       Evidence-led next iteration
```

控制来自不可被 Candidate 修改的合同、数据边界和哈希，不来自一段越来越长的 Prompt。

## 4. 状态与数据流

### 4.1 设计与交付状态机

沿用：

```text
CONTEXT_CAPTURE → RESEARCH_AND_REUSE → PREBUILD → TEN_LENS_REVIEW
→ REMEDIATION → BUILDER_READINESS → OWNER_GATE → SEALED_TASKPACK
→ BUILD_LAST_MILE → FROZEN_CANDIDATE → VERIFY_AND_RELEASE
→ POST_DEPLOY_OBSERVATION
```

### 4.2 单次实验内部状态

```text
DRAFT
→ CONTRACT_FROZEN
→ DATA_FROZEN
→ ASSIGNMENTS_SEALED
→ RUNNING
→ EVIDENCE_COMPLETE
→ GATED
→ SEALED
```

- `CONTRACT_FROZEN` 后不得改变指标、阈值或预算；新事实要求新 experiment_id。
- `DATA_FROZEN` 后 sealed holdout 只能由控制器读取。
- `RUNNING` 期间记录每项失败，不用重试覆盖 flake。
- `GATED` 后只允许生成报告、封存或根据新事实开启下一实验。

### 4.3 数据流不变量

```text
Requirement
→ Acceptance
→ Oracle
→ Task IDs
→ Assignment IDs
→ Run IDs
→ Raw Evidence Digests
→ Paired Metrics
→ Gate Decision
→ Exact Candidate
```

任一环断裂，正向发布结论必须 fail-closed。

## 5. 存储与权威

### 5.1 安装目录

只包含：

- `SKILL.md`；
- `agents/openai.yaml`；
- 决定性脚本；
- 引用文档；
- 可复制模板。

不得写运行数据、反馈、密钥、缓存或长期事实。

### 5.2 代码目录外工作区

建议结构：

```text
run/
  CANONICAL_STATE.json
  config/experiment.json
  datasets/{development,validation,sealed_holdout,adversarial,market_live,incident_replay}/
  assignments/controller_only/
  runs/raw/
  feedback/raw/
  reports/
  evidence/
  seals/
```

### 5.3 长期事实

在 LinzeColin/AgentDatabase 语境下：

- Skill 代码、Schema 与模板进入 AgentDatabase；
- 长期业务与运行事实进入授权的 Private-Database；
- 大对象与不可变二进制证据进入授权对象存储；
- 代码仓不得成为第二运行事实源；
- 无新增事实不得制造空提交。

未获得私有仓授权时，保持事实为 `UNKNOWN`，只输出最小采集方法。

## 6. 运行方式

核心脚本是本地、CI 和 runner 可执行的标准库 Python。外部模型和工具通过 JSONL Adapter 接入：

```text
assignments.jsonl → external executor → results.jsonl
feedback source → anonymizer → feedback.jsonl
results + feedback → aggregate → gate → next iteration
```

采用显式命令或 CI job。不得让 Agent 声称会在后台等待 soak 或市场反馈；只实现自动任务、状态与证据读取。

## 7. 失败与恢复

| 失败 | 动作 |
|---|---|
| 输入合同无效 | 停止，不产生部分 PASS |
| 执行器超时/429/500 | 记录原始失败；按冻结重试预算处理 |
| 部分写入 | 使用原子临时文件替换；保留失败记录 |
| blind map 泄漏 | 实验失效，创建新 experiment_id |
| holdout 泄漏 | 实验失效；污染任务永久移出 holdout |
| 身份不匹配 | BLOCKED，不猜测 Candidate |
| high/critical 市场事故 | 终止 Canary，回退 Baseline |
| 汇总或 Gate 中断 | 从原始 JSONL 重建；不得手工补绿 |
| 封存校验失败 | 拒绝发布，定位缺失/变化/多余文件 |

恢复必须绑定最后一次已接受 Baseline、精确制品摘要和安装事务收据。
