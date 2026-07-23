# R6 生命周期来源读取合同

本合同覆盖 `project_billing`、`cash_out`、`contract_and_changes`、`cash_in` 四个输入 slot。R6 只把 manifest 明确选中的 value-only XLSX 转成不可变 source record 与 economic-event candidate；它不解析真实公司的未锁定语义，不完成跨阶段链接，也不决定最终 Metric。

## 运行前输入门禁

每次运行仍须先通过 R3 输入充分性门禁。对每个本次 Metric 必需的 slot，私有 manifest 必须明确锁定一个或多个 source ID、各自完整 SHA256、`reader_version=2.0.0`、logical source period、schema ID 与 schema fingerprint。缺失、候选冲突、摘要漂移或未锁定 schema 一律先提示补充或要求用户选择允许的缩小范围/合格替代；未回复不是授权，非可豁免输入不能省略。

公共 `*.template.yml` 只是空语义模板，状态必须保持 `TEMPLATE_NOT_ACTIVE`。真实运行前，应在 gitignored private runtime 创建 `ACTIVE` profile，并用公司实际文件证据锁定：

- sheet 与表头的精确序列；
- canonical 字段到来源列的精确绑定；
- 日期格式、必填字段及 CNY 范围；
- 每个来源状态、事件类型和行类型的精确含义；
- 每条状态/类型/行规则及 profile 的 hash-bound evidence。

任一表头、状态、事件类型、行类型或必填字段含义不明确时，读取器必须停止并返回结构化 blocker，禁止猜测同义词、靠列位置兜底或把未知值转为 0。

## 四类来源的权限边界

| Slot | Reader | R6 允许的 direction/stage | 明确禁止 |
| --- | --- | --- | --- |
| `project_billing` | `project_invoice_v2` | `REVENUE / BILLED` | 把发票直接当 `RECOGNIZED_REVENUE` 或项目成本 |
| `cash_out` | `payment_v2` | `CASH_OUT / PAID` | 把付款直接当 incurred/posted cost；按备注自动归项目 |
| `contract_and_changes` | `contract_change_v2` | `REVENUE / CONTRACT_VALUE` 或 `COST / COMMITMENT` | 把合同额当开票、收入确认、实际成本或现金 |
| `cash_in` | `collection_v2` | `CASH_IN / COLLECTED` | 把回款直接当收入确认 |

事件的 `identity_status` 固定为 `PENDING_IDENTITY`，`metric_inclusion_status` 固定为 `NOT_EVALUATED_R6`。项目、主体、WBS 和合同来源键只被保存；必须在后续通过 R4 证据化 identity 才能形成正式归属。自由文本只保留“存在候选文本”标志，不能授予项目归属。

## 金额、日期、状态与撤销

- 所有金额沿用 R2 严格 Decimal→整数分路径；blank 保持 null，非法非空值阻塞，CNY 之外阻塞产品 `0.2` 的正式路径。
- 单据、审批、开票、付款、回款、生效和撤销日期分别保存。`BILLED` 必须有 invoice date，`PAID` 必须有 payment date，`COLLECTED` 必须有 collection date，`CONTRACT_VALUE` 必须有 approval 或 effective date。当前 profile 只支持完整 ISO date 或启用的整日 Excel serial；timestamp 不会被静默截断成日期。
- 开票来源保留 transaction/gross/net/tax。`gross - net - tax` 不为 0 时保留 `SOURCE_ARITHMETIC_DELTA` 与分值差异，不自动覆盖来源金额。
- status 只通过 active profile 的精确规则映射为 `SOURCE_ACTIVE / SOURCE_PENDING / SOURCE_CANCELLED / SOURCE_REVERSED`。
- `SOURCE_REVERSED` 必须保留原来源键和 reversal date。credit/refund/reduction 可通过证据锁定的 `amount_multiplier=-1` 保存符号，但 R7 才建立完整原始—撤销—残余链。

## 来源守恒与重复下载

每个来源输出 physical rows、business/control records、empty rows、parse failures、四类金额正负零空计数和总额，并分别保存 business/control 金额分区。所有行数与金额分区必须精确守恒，解析失败不会产生部分成功结果。

R6 只处理一种明确重复：同一 slot、相同 locked profile/schema、相同 normalized business-record multiset 的完整导出副本。此时：

- 业务事件只计一次；
- 所有 source-record aliases 仍保留；
- suppressed count/amount 与 batch count/amount 都必须零差守恒；
- 新增一个完全相同的下载 alias 不改变 business fingerprint；
- ZIP 元数据、文件路径和来源行枚举顺序没有业务权威。

同一稳定单据但状态或金额不同、两个导出部分重叠、单个导出内部重复行，都不是 R6 可静默去重的情形。它们必须保持不同候选或阻塞，交给 R7 的 same-stage dedup/version/link/allocation 合同处理。

## 安全、公开输出与公司流程

R6 在打开业务 XML 前执行 R2 文件安全预检；公式、宏、外链、活动内容、危险 ZIP、schema 漂移和 legacy XLS 都 fail closed。公开摘要只输出状态和聚合计数，不包含路径、文件名、source ID、hash、表头、金额、项目/客户或自由文本。

R6 成功状态仅表示 `R6_LIFECYCLE_CANDIDATES_NOT_FINAL`。它不生成最终项目成本表，不设置财务负责人或授权人，也不管理公司审批。未来全部门禁通过后，Skill 直接生成最终文件，并在对话与 `output_index` 显示绝对路径；生成后的公司内部流程仍在 Skill 外执行。

## 留给 R7 及以后

- 同阶段逐行版本/冲突/业务去重；
- invoice↔GL、GL↔payment、contract↔invoice、invoice↔collection 等跨阶段 typed links；
- 一对多、多对一、部分分配、退款与 residual pool 守恒；
- 独立双通道聚合；
- as-of、basis、identity、status 与 policy 共同决定 named Metric inclusion；
- 最终 workbook、restatement、output manifest 和公司流程 handoff。
