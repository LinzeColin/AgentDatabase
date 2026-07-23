# R9 Metrics, workbook and generation contract

## Authority and scope

本合同实现 Task Pack `1.2.0` 的 R9。它只处理 named Metric、四状态平面、最终/阻断/生成失败 artifacts、values-only 工作簿、绝对输出定位和公司流程位置交接。

R9 不读取真实原始财务文件，不执行 R10 私有 reference/calculate 隔离验证，不做 R11 当前数据回归，不做 R12 发布/性能/安装，也不创建财务负责人、授权人或公司审批状态。

## Mandatory pre-generation sequence

1. 在读取不必要的来源正文前执行 R3 输入充分性门禁。
2. 缺项时仅生成一个紧凑编号矩阵，提供：补充输入、缩小范围、合格替代证据、仅省略可选展示、停止。
3. 未回复不构成授权；`NON_WAIVABLE` 门禁不能通过“省略”变成 sufficient。
4. 使用了用户明确处理时，必须绑定上一份 sufficiency report、当前 request/manifest/config hash 和用户精确指令；补充或替代证据必须重新扫描为 `PRESENT`。
5. 只有 `SUFFICIENT` 或 `SUFFICIENT_WITH_DOCUMENTED_SCOPE` 才能进入 R9 Metric 计算。后者只表示受影响范围已被显式缩小或可选展示被明确省略，不豁免仍在范围内的正确性/安全门禁。
6. R5–R8 的来源、身份、关系、公式、工资、税费、利息、调整和守恒门禁全部通过后，才构造 R9 facts。

全流程应在同一个尚未发布的 run 中保留 in-memory sufficiency report，再由 R9 原子生成器一次性发布。R3 standalone preflight 已占用的输出目录不能被 R9 覆盖；继续计算必须使用新的 run ID/输出目录并保留前序绑定。

## Explicit fact promotion

`MetricFact` 必须绑定：

- named `metric_id` 与 `accounting_basis_id`；
- direction、lifecycle stage 与 metric-specific date；
- `legal_entity_id + canonical_project_id + wbs_or_cost_code`；
- CNY integer minor-unit amount；
- exactly one disposition：`INCLUDED / EXCLUDED / PENDING / PARSE_ERROR`；
- source records、mapping resolution、formula/parameter/policy/input-resolution refs；
- content-addressed Metric inclusion decision 与 evidence；
- `upstream_validation_status=VALIDATED`。

R7 `RelationEvent` 只有完整 `VALIDATED_IDENTITY` 且方向/生命周期与 Metric catalog 相符时才能经 adapter 提升。R5 `BasisView` 的每个 bridge component 都必须取得一一对应的 source/mapping/evidence lineage；缺少或多出 component lineage 均阻断。

## Metric catalog and basis separation

直接 Metric：

- `COST_BUDGET / BUDGET_APPROVED`
- `COST_COMMITTED / COMMITMENT_APPROVED`
- `COST_ACCRUED / JOB_COST_INCURRED`
- `COST_POSTED_ACTUAL / JOB_COST_INCURRED`
- `COST_POSTED_ACTUAL / GL_RECOGNIZED_COGS`
- `COST_PAID / CASH_VERIFIED`
- `COST_FORECAST_EAC / JOB_COST_EAC_APPROVED`
- `REV_CONTRACT_VALUE / CONTRACT_APPROVED`
- `REV_BILLED / BILLING_STATUS_APPROVED`
- `REV_RECOGNIZED / GL_RECOGNIZED_REVENUE`
- `CASH_COLLECTED / CASH_VERIFIED`

派生 Metric：

- accounting margin by job-cost basis = recognized revenue − posted job cost − accrual；
- accounting margin by GL COGS basis = recognized revenue − GL-recognized COGS；
- cash margin = verified collected cash − verified paid cash。

派生组件必须具有相同 as-of 和 canonical scope，且各组件自身先达到 `VALIDATED`。两类 accounting margin 不得混合或只输出一个无口径“利润”。

## Independent Metric reconciliation

每个直接 Metric 保存一个不可变 source control：count、signed amount、absolute amount 与可选 source-reported value。

```text
source_control = included + excluded + pending + parse_error
channel_A = sum(included facts)
channel_B = source_control - excluded - pending - parse_error
required: channel_A_signed - channel_B_signed = 0 minor
required: channel_A_absolute - channel_B_absolute = 0 minor
```

输出同时保留：

- `source_value_minor`
- `recomputed_value_minor`
- `calculated_value_minor`
- `source_recomputed_delta_minor`
- `recomputed_calculated_delta_minor`
- signed/absolute channel deltas
- source control、facts hash、formula/parameter/policy/resolution refs 与 blocker codes

来源值不为空时，来源与复算差一分即 `BLOCKED_SOURCE`；任何 pending/parse-error pool、as-of 超期、scope/lifecycle 冲突或通道差异均 fail closed，不能覆盖来源值或自动摊平。

## Four status planes

四平面不可压缩为一个 status：

- execution：`SUCCEEDED / NEEDS_USER_INPUT / EXPECTED_BLOCKED / FAILED / CANCELLED`
- input readiness：`NOT_EVALUATED / SUFFICIENT / SUFFICIENT_WITH_DOCUMENTED_SCOPE / NEEDS_SUPPLEMENT / NEEDS_EXPLICIT_HANDLING / BLOCKED_NON_WAIVABLE`
- calculation：`NOT_EVALUATED / VALIDATED / BLOCKED_* / ERROR`
- generation：`NOT_GENERATED / FINAL_GENERATED / BLOCKED_DIAGNOSTICS_GENERATED / FAILED / SUPERSEDED`

唯一 final 组合：

```text
execution_status=SUCCEEDED
input_readiness_status=SUFFICIENT or SUFFICIENT_WITH_DOCUMENTED_SCOPE
calculation_status=VALIDATED
generation_status=FINAL_GENERATED
```

公司审批不属于第五个状态平面，也不能影响是否生成 final。

## Workbook runtime and security

工作簿只能由 Codex workspace loader 提供的 Node executable 和 `@oai/artifact-tool` node_modules 创建。调用方先取得依赖路径，再显式注入 `CODEX_SPREADSHEET_NODE` 与 `CODEX_SPREADSHEET_NODE_MODULES`。Skill 不搜索、安装、猜测或使用系统/global/repo-local spreadsheet package。

运行时在私有 scratch 中创建 `node_modules` symlink，执行唯一 builder `scripts/build_project_cost_workbook.mjs`，成功后删除 scratch。runtime 不足属于显式非 final blocker。

最终 `.xlsx` 固定八张可见表：

1. `01_项目成本表`
2. `02_成本明细`
3. `03_生命周期对照`
4. `04_收入与现金`
5. `05_来源与核销`
6. `06_差异与待确认`
7. `07_项目身份`
8. `08_运行说明`

所有业务单元格写 values，不写 formulas。精确金额真值使用 integer minor units（分）；元列是从整数分确定性格式化的展示文本，不进入任何计算。所有不可信文本先做 spreadsheet-formula 前缀转义。

生成后必须：

- 逐张表 render 并验证八个非空 preview；
- 校验 sheet 顺序/可见性、styles、values 和 OOXML relationships；
- 拒绝 formula、DDE、macro、ActiveX/OLE、external link、connection、embedded active content 与 formula-error token；
- 计算不依赖 Office recalc 的 semantic workbook hash。

`visual_evidence_dir` 仅供受控验收把八张临时 preview 复制到仓外证据目录；正式运行默认不保留 preview，也不把它们加入 final output bundle。

## Final, blocked and failed outputs

### Final

全门禁通过后立即生成一个同时列出两个 cost bases 的 final workbook，并额外生成 Metric snapshots、lineage、validation、review queue、manifest、indexes、seal 与 `INTERNAL_PROCESS_HANDOFF.md`。

私有 `metric_facts.json` 保存工作簿明细背后的完整事实、决议与证据引用；工作簿中被截短的哈希仅用于可读展示，完整值以该文件和 `metric_snapshots.json` 为准。

### Blocked

输入或业务门禁未通过时：

- 不生成任何 `.xlsx`；
- 生成 `missing_input_prompt.md`、`blocked_diagnostics.json`、`review_tasks.csv` 和控制 artifacts；
- 提示用户补充、合格替代、明确缩小范围、仅省略可选展示或保持阻塞。

### Renderer/export failure

builder、render、OOXML 或 index validation 失败时，临时 final artifacts 被原子清理，再以 `generation_status=FAILED` 封存 `generation_failure.json` 和绝对定位；不得遗留 `.xlsx` 或 handoff。

## Non-cyclic generation and discovery

写入顺序：

1. business outputs or diagnostics；
2. `run_manifest.json`，其 `output_hashes` 排除 manifest/indexes/seal；
3. `OUTPUT_INDEX.md`，不为 machine index 或 seal 自哈希；
4. `output_index.json`，列出并哈希除自身与 seal 外的所有 finalized files；
5. `run_seal.sha256`，哈希除自身外所有 finalized files；
6. 验证 seal/index 后 atomic no-replace publish。

每次对话/终端必须重复：

```text
RESULT_STATUS: ...
OUTPUT_DIR: /absolute/path
PRIMARY_OUTPUT: /absolute/path
OUTPUT_INDEX: /absolute/path/OUTPUT_INDEX.md
NEXT_STEP: ...
```

历史正式目录不可覆盖。输入、规则、policy、resolution 或输出内容改变时，创建新的 `restate` run 并绑定 `supersedes_run_id`。

## Company process boundary

`INTERNAL_PROCESS_HANDOFF.md` 只在 final 时存在，只交接主文件、output index 与证据位置。它明确指示调用方 Codex/操作人在 Skill 外按公司现有内部流程继续。

Skill 不设置财务负责人或授权人，不发送审批，不记录审批状态，也不声称生成文件等于公司审批完成。

## R9 residual risks and surprises

- R3 standalone preflight 会占用其输出目录；完整 calculate pipeline 必须把 sufficient report 放在同一未发布 run 中，或创建新 run，不能覆写 standalone 目录。
- 工作簿的精确金额列是“分”；元列为展示文本。若未来要求可编辑元金额或 Excel 内公式，必须单独变更安全、精度与审计合同，不能静默改用 JS float 或公式。
- R9 的公开合成 final 只证明生成器和合同；未读取真实 KMFA 原始数据，因此不能证明真实输入、policy、mapping 或 calculate 结果已 ready。
- `reference-replay` 仍由 R10 隔离验证；R9 final generator 不接受 reference display 作为 calculate 真值。
