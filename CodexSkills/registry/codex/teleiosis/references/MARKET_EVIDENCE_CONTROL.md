# Teleiosis v0.0.0.2｜市场实证控制面

## 1. 目的

市场实证内核把实验室模拟与真实市场证据放在同一可追踪框架中，但不混淆证据等级：

```text
实验室：L0–L3
真实重放/Shadow：L4
真实 Opt-in Canary：L5
真实 Issue / PR / 交付 / 微赏金：L6
复用 / 留存 / 付费 / 实际节省 / 事故率：L7
```

更多 L2/L3 数据永远不能累计成 L5。

## 2. 五臂因果

每次比较至少保留 `No Skill`，并尽可能同时运行：

- No Skill；
- 当前 Baseline；
- Candidate；
- 锁定版本的真实 Competitor；
- 单机制 Ablation。

模型、工具、权限、任务、Oracle、预算、重试和评估合同尽可能相同。不可消除的差异必须降低结论置信度。

## 3. 六类压力

1. 语义：错别字、歧义、冲突、隐含意图、多语言；
2. 上下文：长线程、大仓库、冲突/过期资料；
3. 工具：超时、429/500、部分写入、中断；
4. 安全：注入、恶意仓库文本、密钥诱导、路径和权限攻击；
5. 版本：模型、runtime、依赖、OS、Skill API 变化；
6. 经济：固定 Token、成本、工具调用和截止合同。

k6/Locust 只验证基础设施吞吐、时延和稳定性，不验证推理质量。

## 4. 防伪大数据

- 以任务/来源 cluster 为推断单位；
- 同一事件的改写、重复 trial 和同一仓库 Issue 不视为完全独立；
- 重复运行先在 cluster 内聚合，再做 paired bootstrap；
- development、validation、sealed_holdout、adversarial、market_live、incident_replay 分开；
- Candidate 对 holdout 的任何访问、过阈值 overlap 或 Oracle 漂移直接 BLOCKED。

## 5. Assurance 硬门

`assurance-check` 必须验证：

- 精确 `subject/environment/tool-trace/artifact/handoff` digest；
- generator/evaluator 身份不重叠；
- 人工校准样本、agreement 和 Cohen’s kappa 达标；
- Adapter 的版本、状态、来源与 `valid_until`；
- sealed holdout 污染审计；
- Canary 停止规则运行前冻结且被实际执行；
- 证据 freshness 与 reheat trigger。

在任何 Market Gate 前，还必须生成冻结的 `QUALITY_AUDIT.json`，至少覆盖：

- development/validation/holdout/adversarial/market 分区的精确与近重复污染；
- 实验室 paired full-factorial 或线上 exclusive assignment 完整性；
- Sample Ratio Mismatch；
- 模型、runtime、工具、权限、预算、system 与 dataset 的跨臂环境一致性；
- 运行前冻结的 alpha、power、MDE 与样本量；
- LLM judge 对人工 gold 的 agreement 与 Cohen's kappa；
- 市场事件新鲜度、未来时间戳、重复 event_id 与跨臂时间偏斜；
- task → result run → feedback 的引用和 artifact digest 完整性。

Gate 缺少该审计、审计未绑定当前 `spec_digest` 或状态不是 `PASS` 时直接 `BLOCKED`，不能由平均得分补偿。

## 6. 真实市场机制

- Opt-in 最小匿名反馈；
- 盲化 Canary/A-B；
- 冻结 Issue/commit/Acceptance 的真实 PR、交付或微赏金；
- 重试、撤销、绕过、卸载、回滚、投诉和事故等负行为回流。

默认不上传原始 Prompt、输出、文件、私有仓内容、身份或凭证。没有 consent 与精确版本的反馈不进入 L5–L7。

## 7. 决策权

Market Evidence Kernel 输出：

- `EVIDENCE_READY_FOR_TELEIOSIS`；
- `KEEP_BASELINE`；
- `REVERT`；
- `REHEAT_REQUIRED`；
- `BLOCKED`。

它没有 `PROMOTE` 权。最终裁决由 Teleiosis 在全部白箱硬门、保护任务和外部复审之后做出。
