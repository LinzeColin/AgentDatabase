---
name: project-cost-table-skill
description: 为 KMFA 项目成本表运行提供输入充分性预检、公共与私有数据隔离、双成本口径、全负担工资分配、fail-closed 校验和可定位输出；当用户要求生成、复算、核对或回放项目成本表时使用。
---

# 项目成本表 Skill

当前状态：`RELEASED_0_2_0_FAIL_CLOSED`。产品工作流已通过 R12 发布门禁，但当前公司输入仍是 `BLOCKED_SOURCE`，不得把发布状态当作真实成本计算成功。R12 不包含机器级安装；本机安装状态以 `$CODEX_HOME/skills/project-cost-table-skill` 的 fresh discovery 与外部封印回执为准，不能从仓库发布字段推断。

## 不可绕过的运行合同

1. 每次运行先生成输入充分性报告；输入不足时停止正式计算并明确列出缺口。
2. 只有用户形成可审计的明确决议后，才能省略非强制输入或采用替代处理；强制门禁不可授权绕过。
3. 参考回放与原始来源重算严格隔离，不用参考差额反推或补齐计算结果。
4. 任一来源、身份、工资、税费、利息、算术或谱系门禁失败时，输出 `BLOCKED`，不得生成伪正式结果。
5. 数据与全部校验通过后直接生成最终文件；本 Skill 不设置财务负责人或授权人，也不管理公司内部审批。
6. 每次运行无论成功、阻塞或失败，都必须在对话与 `output_index` 中明确列出绝对输出路径。

## R1 已实现边界

- 公共、私有运行时、原始来源三平面分类。
- 私有目录初始化但不跟踪任何占位文件。
- 工作树与暂存区边界扫描器，默认拒绝未知路径、危险附件、二进制、符号链接和敏感路径特征。
- 公共合成测试与私有回归数据隔离。

## R2 已实现边界

- 只接受 ASCII 严格金额语法、`Decimal` 或整数；拒绝 float、bool、非有限数、混淆 Unicode 符号、非法分组、过度小数位和整数分溢出。
- 金额只在显式登记的舍入层按 `ROUND_HALF_UP` 转换为整数分；空值、负零和舍入事实保留审计状态。
- 输入路径拒绝越界、穿越、软链接、硬链接、设备文件和超限文件；输出采用不可覆盖、失败可清理的原子文件/目录发布。
- ZIP 在内容使用前校验路径、重复目标、加密、成员类型、压缩算法、成员数、大小、压缩比与 CRC；嵌套 ZIP/XLSX 必须使用显式 private scratch 递归校验。
- OOXML 检测宏、VBA、ActiveX/OLE、外链、数据连接、公式、DDE、自动运行名称、隐藏 sheet 元数据与 image-only sheet；不执行任何公式或 Office 自动化。
- Legacy XLS 没有锁定 reader 时明确阻塞；PDF 只过容器门禁且阻塞缺失 EOF、加密和活动内容；不把 PDF 当结构化 calculate 输入。
- 输出文本对 Excel/CSV 公式前缀做转义，数字仍必须由数值 writer 写入。

## R3 已实现边界

- 每次操作先按 mode、Metric、basis、项目范围、截止日、策略和输出目录执行输入充分性门禁；门禁阶段只读取请求、公共配置、私有 manifest 和原始目录元数据，不打开原始业务文件正文。
- 输入不足时只生成一次紧凑编号矩阵，明确提供“补充、缩小范围、合格替代、仅省略可选展示、停止”五类处理；未回复不构成授权，非可豁免门禁不能省略。
- 任何明确处理必须保存用户精确指令和影响范围，并绑定上一份已封存不足报告、当前请求、manifest 与要求配置；补充或替代证据必须重新扫描为 `PRESENT`。
- 每个必需来源 slot 都要求显式 opaque source ID、完整 SHA256、schema fingerprint、reader version 和 logical source period；mtime、文件枚举顺序和缓存摘要不能决定正式结果。
- 私有完整 inventory 与公开聚合摘要严格分开；公开摘要不含原始路径、文件名、source ID、hash、表头或金额。
- source record、candidate、decision、validated fact 四层记录不可变、不可覆盖且谱系明确；这里的 validated fact 是数据门禁，不代表公司审批。
- 每次门禁运行都原子生成 `input_sufficiency_report.json`、可选 `input_resolution.json`、`OUTPUT_INDEX.md`、`output_index.json` 和 `run_seal.sha256`，并在终端重复绝对 `OUTPUT_DIR`、`PRIMARY_OUTPUT`、`OUTPUT_INDEX`。

R3 命令入口：

```bash
python3 scripts/run_input_preflight.py \
  --request /ABSOLUTE/PRIVATE/operation_request.json \
  --module-root /ABSOLUTE/PATH/TO/project-cost-table-skill
```

输入足够只表示可以进入下一项受控门禁；R3 不生成最终财务工作簿。未来全部数据和产品校验通过时必须在同一运行直接生成最终版本，Skill 不设置财务负责人、授权人或公司审批状态，生成后的内部流程在 Skill 外进行。

## R4 已实现边界

- 项目事实纳入计算前必须唯一解析到在截止日有效的 `canonical_project_id + legal_entity_id + wbs_or_cost_code`，并绑定合同、受治理来源 ID、mapping resolution 和证据引用。
- 最终匹配仅接受精确 canonical scope、精确合同、精确受治理来源 ID 或证据合格的显式 resolution；项目编号、名称、客户、自由文本和金额相似度只能生成候选。
- 有效期重叠、一对多别名、多活动匹配、合同/项目或标识冲突、跨主体歧义、陈旧映射、主键不完整和未映射全部 `BLOCKED_IDENTITY`，并生成不可覆盖的私有候选和 `P0` review task。
- 跨主体视图保留法人主体、WBS/成本码与 identity reference，不做破坏性合并；公开身份摘要只含聚合计数。
- `APPROVED` 只表示证据合格的数据映射，review task 只属于数据治理；二者均不设置财务负责人、授权人或公司内部审批。

R4 的操作与数据契约见 `references/PROJECT_IDENTITY_AND_REVIEW.md`。身份主数据仍须通过 R3 输入门禁并保存在 gitignored `private_runtime`；公共仓库只包含空模板、配置、Schema 和合成测试。

## R5 已实现边界

- 金蝶读取器只接受 manifest 已选定、完整摘要与 reader/schema 锁一致、并通过 R2 安全预检的 value-only `.xlsx` 或受治理账套 ZIP。账套中的每个 `.xlsx`/`.xls` 必须在私有 `ACTIVE` bundle profile 中逐一列为纳入或有 hash-bound evidence 的范围排除；所有纳入 `.xlsx` 必须完整读取，任何未分类工作簿、成员漂移、危险 OOXML、缺 reader profile 或纳入范围的 legacy `.xls` 都阻断整个 `general_ledger` slot，禁止部分成功。
- 读取器保存主体/项目/WBS/合同来源键、科目、凭证行、单据/业务/记账日期、借贷、余额、币种、来源状态、行类型与不透明的容器/成员 lineage；空值保持 `null`，非法金额或日期不转成 0，成员、空行和三列金额控制形成逐来源守恒报告。bundle 解包只使用与只读输入根隔离、运行开始为空的 private scratch，临时成员必清理。
- 口径引擎必须使用有效期内、hash-bound evidence 支持的私有 `ACTIVE` 状态/行类型/科目/期间/估值 policy；公共 template 永远不能直接运行。
- `JOB_COST_INCURRED` 与 `GL_RECOGNIZED_COGS` 分开生成，禁止相加成一个无名“总成本”。WIP 主桥与 5001→6401 结转控制均必须为 0 分。
- 每个期间内业务记录必须绑定一个在记账日有效的 R4 canonical project + legal entity + WBS/cost code + contract identity；只有运行请求中的精确 canonical scope 可进入桥接，其他已解析 scope 作为守恒排除项，不得跨项目混算。未知科目、状态、行类型、身份、币种或期间 policy 全部 fail closed。
- `COST_POSTED_ACTUAL` 使用 posting date。关闭期间必须绑定同范围、同期间且内容寻址的前序快照；新增、删除或修改行要求 `restate` 和明确 `supersedes_run_ref`，不得覆盖历史。
- R5 成功状态仅为 `R5_RECONCILED_NOT_FINAL`。它不生成正式工作簿、不设置财务负责人或授权人，也不管理公司内部审批。

R5 的操作、公式、输入与阻断契约见 `references/KINGDEE_AND_ACCOUNTING_BASIS.md`。真实科目、期间、估值和表头 policy 只能保存在 gitignored private runtime；公共仓库没有真实金额、文件名、路径或有效公司政策。

## R6 已实现边界

- `project_billing`、`cash_out`、`contract_and_changes`、`cash_in` slot 支持一个或多个 manifest 显式锁定来源；每个来源仍须独立绑定完整摘要、reader/schema 版本、period 与只读文件身份。
- 四类 value-only XLSX 读取器使用私有 `ACTIVE` profile 的精确表头、列绑定、日期、必填、状态、事件类型和行类型规则；公共 template 不能直接运行。未知语义、schema 漂移、公式/危险 OOXML、legacy XLS、非法金额日期或非 CNY 全部 fail closed。
- 开票只形成 `REVENUE/BILLED`，付款只形成 `CASH_OUT/PAID`，客户合同只形成 `REVENUE/CONTRACT_VALUE`，供应商合同只形成 `COST/COMMITMENT`，回款只形成 `CASH_IN/COLLECTED`。付款不自动成为成本，开票/回款不自动成为确认收入。
- event candidate 保留主体、项目、WBS、合同、对手方、单据行、全部相关日期、来源状态、gross/net/tax 与原始算术差异；身份固定为 `PENDING_IDENTITY`，Metric inclusion 固定为 `NOT_EVALUATED_R6`。自由文本不能自动归项目。
- 来源状态、credit/refund/reduction 符号与 reversal lineage 必须来自证据锁定规则；`SOURCE_REVERSED` 缺原来源键或撤销日期即阻塞。gross/net/tax 差异只报告，不回写来源值。
- R6 只合并同 slot、同锁定 profile/schema、normalized business content 完全相同的整份重复导出；事件只计一次、所有 aliases 保留、数量与金额零分守恒。新增重复下载副本不改变 business fingerprint；部分重叠、状态/金额变化和单导出内部重复留给 R7，不静默去重。
- 公开摘要只有聚合状态/计数。R6 成功状态为 `R6_LIFECYCLE_CANDIDATES_NOT_FINAL`，仍不生成正式项目成本表，也不设置财务负责人、授权人或公司审批状态。

R6 的输入、生命周期、重复下载与阻断合同见 `references/LIFECYCLE_SOURCE_READERS.md`。真实红圈、合同、开票、付款、回款表头与状态含义必须先取得证据并写入 gitignored private runtime；不明确时先提醒用户补充或选择允许的处理方式。

## R7 已实现边界

- R6 candidate 必须先形成绑定 R4 身份证据的 immutable `RelationEvent`；身份未解析时只能保持 `ALLOCATION_REQUIRED`，不能携带半套 canonical scope，也不能进入最终 Metric。
- 同阶段去重明确区分 `BYTE_DUPLICATE`、`BUSINESS_CONTENT_DUPLICATE`、`SAME_KEY_SAME_VERSION`、`SAME_KEY_CHANGED_VERSION`、`POSSIBLE_DUPLICATE` 和 `DISTINCT`。只有同键同版本可自动排除；变更版本和跨键业务等价必须绑定精确事件集合、input resolution 与 hash-bound evidence。金额、日期、对手方、单据或文本相似只能生成候选。
- 跨阶段关系使用固定类型：`DERIVED_FROM`、`FULFILLS_COMMITMENT`、`ACCRUAL_FOR`、`REVERSES`、`SUPERSEDES`、`INVOICES`、`POSTS_TO_GL`、`SETTLES`、`ALLOCATES_TO`、`TRANSFERRED_BETWEEN`、`REFERENCES_ONLY`。链接匹配顺序优先稳定 ID、证据合格身份/合同和显式分配 resolution，不按自由文本自动归项目。
- 1:N、N:1 和多条链接组成的同轴 connected match group 均以绝对分值分配，同时保留原事件正负号。source allocation、target allocation 与独立 match-group control 必须零分差异；禁止自动摊平残差。部分分配保留 `PENDING_RESIDUAL`，不能伪装为完成。
- 原始冲销与 refund/credit/reduction 保留原事件和反向事件；`REVERSES` 必须一对一绑定原事件、金额绝对值相等、符号相反并净额为零。`SUPERSEDES` 保留旧版本，不覆盖历史。
- 来源守恒同时计算 signed 与 absolute 控制：`source_control = included + excluded + pending + parse_error`。通道 A 直接逐条汇总 included；通道 B 独立从 source control 扣除其他池；两条路径都必须零分差异。
- duplicate candidate comparison 先按主体、项目、WBS、合同、方向和阶段分区，并受 1,000,000 pair 上限保护；跨阶段禁止去重。公开摘要只含聚合计数和控制差异。
- R7 所有链接、去重和 reconciliation 均固定 `NOT_EVALUATED_R7`，不决定 named Metric、不生成正式工作簿、不设置财务负责人或授权人，也不管理公司内部审批。真实链接证据或 scope resolution 不足时必须提醒用户补充或明确选择允许的处理方式，并输出 blocker/review task 与绝对结果路径。

R7 的数据结构、匹配优先级、分配守恒和阻断合同见 `references/DEDUP_LINKS_AND_RECONCILIATION.md`。

## R8 已实现边界

- 每次真实计算在 R3 输入充分性之后继续执行 R8 公式就绪门禁。未知公式、无适用活动 profile、请求绑定漂移、有效期/范围不符、活动范围重叠、缺 policy/evidence/input resolution 或 test vector 均 `BLOCKED_R8_POLICY_INPUTS`；用户必须补充、提供合格替代证据、明确缩小受影响 Metric 范围或保持阻塞，未回复不构成授权。
- 公式引擎只执行登记的整数有理数表达式，不接受 `eval`、float、自由文本公式、历史差额反推或默认费率。活动 profile 必须声明单位/基数、canonical scope、有效日期、舍入层、`ROUND_HALF_UP`、请求/输入/配置 SHA256、证据及可执行 test vector；supersession 只追加不覆盖。
- 历史管理费 2% 只登记为 `REFERENCE_OBSERVED_NOT_ACTIVE`，不能作为 calculate 默认。产品 0.2 只支持 CNY；FX rate 已登记为 deferred，任何活动 FX profile 均阻塞。
- 工资采用 `FULLY_LOADED_EMPLOYER_COST_WITH_APPROVED_TIME`。每个观察到的 component 必须由有效 registry 明确纳入、排除或识别为不能进入 employee payroll 的外部劳务；component 合计=payroll control、项目+未分配时间=approved-time control、项目分配+未分配工资=可分配雇主成本均要求精确相等。
- 工资更正、追溯和冲销保留 lineage；冲销必须精确反向。禁止猜工资/日薪、把缺失 component 当 0、按文本推断外部劳务、跨主体分配、缺 WBS 分配或自动摊平残差。舍入导致项目分配超过可分配成本时保留带符号诊断残余并阻塞。
- 项目税依次接受项目直接证据、受治理项目税台账、证据支持的项目分配 policy；公司级税表不能默认分项目。来源税额与复算税额、gross 算术差异、invoice type 和 recoverability 同时保留，不覆盖来源。
- 利息要求 principal、起止日、有效年率、day-count denominator、receipt/payment/prepayment 同日顺序、全部资金 movement、舍入层、证据与 policy；任一缺失或顺序导致负 principal 即阻塞。
- 人工调整必须有显式正负号、原因、证据、formula profile、policy 或合格 input resolution、有效期/expiry、reversal policy、请求/输入/配置 hash 与 supersession/reversal lineage。过期但仍 active、跨 scope supersession、非精确反向或自动冲销均阻塞。
- R8 只产生 `NOT_EVALUATED_R8` 的政策计算和控制结果，不决定 named Metric、不生成最终工作簿。Skill 不设置财务负责人或授权人，也不管理公司内部审批；R9 及后续全部门禁通过后才直接生成最终文件，并将绝对路径交给操作人走公司现有流程。

R8 的输入选择、公式、工资、税费、利息、调整与 surprise 合同见 `references/FORMULA_PAYROLL_POLICY_INPUTS.md`。公共 template 全部不可运行；真实费率、component、工资、工时、税费、利息和政策只能放在 gitignored private runtime。

## R9 已实现边界

- R9 只接受已经通过 R3/R4/R5–R8 数据门禁、并绑定显式 Metric inclusion decision 与证据的事实；R7 event 和 R5 accounting-basis view 均有显式 adapter，不能把未解析候选直接提升为最终 Metric。
- `config/metric_catalog.yml` 分开预算、承诺、暂估、实际、支付、预测、合同值、开票、确认收入、回款与两类 margin；`COST_POSTED_ACTUAL` 一旦在范围内，必须同时生成 `JOB_COST_INCURRED` 和 `GL_RECOGNIZED_COGS`，不得合并成无名总成本。
- 每个直接 Metric 同时执行两条独立通道：A 逐条汇总 `INCLUDED`；B 从来源控制额扣除 `EXCLUDED/PENDING/PARSE_ERROR`。来源数量、signed、absolute、两通道和 source/recomputed/calculated 差异任一非零均阻断。
- `execution_status`、`input_readiness_status`、`calculation_status`、`generation_status` 四平面独立；只有 `SUCCEEDED + SUFFICIENT(_WITH_DOCUMENTED_SCOPE) + VALIDATED` 才能成为 `FINAL_GENERATED`。
- 输入不足、Metric 阻断或工作簿 runtime 缺失时，必须生成可定位诊断与明确处理选项，不得生成 `.xlsx`；渲染/导出故障原子撤销正式外观文件并封存 `FAILED` 诊断。
- 全部门禁通过后立即生成一个包含两个成本口径的 values-only `.xlsx`。八张可见表均使用整数分作为精确金额真值，并另列由整数分格式化的元展示文本；禁止公式、宏、DDE、外链、连接或活动内容，且每张表都必须完成视觉渲染验证。
- 每次运行按非循环顺序生成 business artifacts → `run_manifest.json` → `OUTPUT_INDEX.md` → `output_index.json` → `run_seal.sha256`，验证后才原子发布。成功、阻断和生成失败均返回绝对 `OUTPUT_DIR`、`PRIMARY_OUTPUT`、`OUTPUT_INDEX` 与下一步。
- 成功时额外生成 `INTERNAL_PROCESS_HANDOFF.md`，供调用方 Codex/操作人在 Skill 外继续公司现有内部流程。本 Skill 不设置财务负责人或授权人，不表示或管理公司内部审批状态。

R9 的 Metric、状态、工作簿、原子输出、运行时依赖和 surprise 合同见 `references/METRICS_WORKBOOK_GENERATION.md`。公开合成与 R12 产品发布都不证明真实 KMFA 输入已齐全；真实运行仍先执行输入充分性门禁。

## R10 已实现边界

- `reference-replay` 运行前先校验：新输出目录、私有 import manifest、基线文件身份与完整 SHA256、预期项目数、8 份 PDF 的安全门禁与完整 SHA256。任一缺失、漂移或不安全即生成可定位的阻塞诊断；强制 hash 门禁不可由授权省略。
- 回放只接受整数分的私有基线，并要求每个项目的逐行合计与来源总成本精确相等。8/8 hash-bound 项目与 68 条行项目已完成私有精确回放；私有值、项目名、文件名和哈希均不进入 Git 跟踪路径。
- 来源利润与 `收入－总成本` 的独立复算值并列保存；已知来源算术差异保留为 `SOURCE_ARITHMETIC_DIFFERENCE`，不得静默覆盖或把差额注入 calculate。
- 回放状态固定为 `calculation_status=NOT_EVALUATED`、`generation_status=NOT_GENERATED`。它只用于历史显示/审计，不生成正式 `.xlsx`，也不生成 `INTERNAL_PROCESS_HANDOFF.md`。
- calculate 模块的静态导入图、子进程导入探针和入口依赖均验证不能引用 `reference_replay`；回放实现也不能导入 Metric、工资、公式、调整、会计口径或最终生成模块。
- 成功、阻塞和失败均原子、不可覆盖地生成 `run_manifest.json`、`OUTPUT_INDEX.md/json` 与 detached `run_seal.sha256`，并在终端打印绝对 `OUTPUT_DIR`、`PRIMARY_OUTPUT`、`OUTPUT_INDEX`。失败中途产物会先在未发布 staging 中清除，再封存失败证据。

R10 私有回放入口：

```bash
python3 scripts/run_reference_regression.py \
  --run-id <NEW_RUN_ID> \
  --input-root /ABSOLUTE/READ_ONLY/INPUT_ROOT \
  --baseline-manifest /ABSOLUTE/PRIVATE/import_manifest.json \
  --as-of YYYY-MM-DD \
  --output-dir /ABSOLUTE/PRIVATE/NEW_OUTPUT_DIR
```

终端和 `OUTPUT_INDEX.md` 都会明确显示输出文件位置。R10 的隔离、状态和阻断合同见 `references/REFERENCE_REPLAY_ISOLATION.md`。R10 精确回放不证明当前来源可以重建正式成本；R11 必须独立运行 calculate 并保留预期 blocker。

## R11 已实现边界

- 当前来源生产运行先校验私有 current-source contract 的完整 SHA256、截止日、输入根、58 项元数据指纹与 9 个非参考生产来源的完整摘要；任何漂移都要求重新审阅并生成新合同，禁止覆盖密封快照。
- current-source contract 只含当前来源定位/状态和通用证据要求，不含参考基线金额、PDF 行项目或 replay adapter。生产入口只读取该合同；它不能读取 expected-block contract。
- 当前 8 项目全范围同时请求 `COST_POSTED_ACTUAL` 的 `JOB_COST_INCURRED` 与 `GL_RECOGNIZED_COGS`。输入充分性报告逐项列出强制缺口，并输出补充、合格替代、缩小范围或保持阻塞等明确选择；未回复不构成授权，非可豁免缺口不能选择“省略”。
- 当前精确 blocker 为：v3 manifest、项目身份、Kingdee reader profile、5001/6401/WIP 会计口径 policy、工资与工时来源、全负担工资 policy、项目税 policy/直接台账、资金占用利息 policy、付款归项目 mapping。参考报告与“金蝶差额”不属于 calculate 输入，也不能成为自动补差 blocker。
- 生产命令真实返回 exit `3`，状态固定为 `NEEDS_USER_INPUT + BLOCKED_NON_WAIVABLE + BLOCKED_SOURCE + BLOCKED_DIAGNOSTICS_GENERATED`，只生成诊断、review queue、谱系、校验/隐私/性能摘要、绝对索引和 detached seal；不得生成 `.xlsx` 或 `INTERNAL_PROCESS_HANDOFF.md`。
- expected-block contract 必须在生产运行前另行密封。独立 harness 只有在生产 exit `3`、四状态平面、9 项 blocker 集合、来源绑定、绝对索引、detached seal 与零参考数据流全部精确匹配时才返回 exit `0` 并标记 `EXPECTED_BLOCKED`。该 exit `0` 是测试通过，不是生产可用。
- 本入口是 R11 的冻结回归入口，不是永久的“正式计算快捷方式”。如果九项缺口已消失，它必须报 `CURRENT_R11_EXPECTATION_STALE` 并退出旧回归合同；随后进入受治理的正常 calculate 管线，全部数据与产品门禁通过即由 R9 直接生成最终文件，不能继续运行旧 harness 来阻止或伪装成功。
- 全局库存出现但不命中任何治理 slot 的变化必须写入 append-only drift review。当前漂移已归类为 `OUT_OF_SCOPE_INVENTORY_DRIFT`，所有生产 slot 的摘要集合未变，旧快照未覆盖。
- 每次生产或 harness 运行都在终端与 `OUTPUT_INDEX.md/json` 中重复绝对 `OUTPUT_DIR`、`PRIMARY_OUTPUT`、`OUTPUT_INDEX` 和下一步。阻塞时下一步是补充输入、提供合格替代证据、明确缩小范围或保持阻塞。

R11 三步入口。所有输出目录都必须是绝对、私有、新建且尚不存在的路径；preparation 先冻结双合同及其摘要：

```bash
python3 scripts/prepare_current_regression.py \
  --task-pack-root /ABSOLUTE/SEALED/TASK_PACK_ROOT \
  --input-root /ABSOLUTE/READ_ONLY/INPUT_ROOT \
  --output-dir /ABSOLUTE/PRIVATE/NEW_BINDING_DIR \
  --contract-id <NEW_CONTRACT_ID> \
  --as-of YYYY-MM-DD
```

随后运行一次直接生产入口（真实阻断必须保留 exit `3`）：

```bash
python3 scripts/run_current_source_reconstruction.py \
  --run-id <NEW_RUN_ID> \
  --input-root /ABSOLUTE/READ_ONLY/INPUT_ROOT \
  --current-source-contract /ABSOLUTE/PRIVATE/current_source_contract.private.json \
  --current-source-contract-sha256 <SHA256> \
  --as-of YYYY-MM-DD \
  --output-dir /ABSOLUTE/PRIVATE/NEW_OUTPUT_DIR
```

最后运行独立 harness。它不会复用上一步目录，而会在全新的 `--production-output-dir` 内启动第二次生产运行，再与 preparation 预先冻结的 expected-block contract 精确比对：

```bash
python3 scripts/validate_current_expected_block.py \
  --run-id <NEW_HARNESS_PRODUCTION_RUN_ID> \
  --input-root /ABSOLUTE/READ_ONLY/INPUT_ROOT \
  --current-source-contract /ABSOLUTE/PRIVATE/NEW_BINDING_DIR/current_source_contract.private.json \
  --current-source-contract-sha256 <CURRENT_SOURCE_CONTRACT_SHA256> \
  --expected-block-contract /ABSOLUTE/PRIVATE/NEW_BINDING_DIR/expected_block_contract.private.json \
  --expected-block-contract-sha256 <EXPECTED_BLOCK_CONTRACT_SHA256> \
  --as-of YYYY-MM-DD \
  --production-output-dir /ABSOLUTE/PRIVATE/NEW_HARNESS_PRODUCTION_OUTPUT_DIR \
  --harness-output-dir /ABSOLUTE/PRIVATE/NEW_HARNESS_OUTPUT_DIR
```

exit code 语义：直接 production `3` 是真实业务阻断；harness `0` 只是 `EXPECTED_BLOCKED` 回归精确通过并保持 `NO_GO_PRODUCTION`；harness `1` 是预期不匹配，必须审阅。不得把 harness `0` 当作正式计算成功。

R11 的双合同、状态、漂移、阻断与输出契约见 `references/CURRENT_RECONSTRUCTION_EXPECTED_BLOCK.md`。当前 harness 通过只证明 Skill 如实阻断；全部数据与产品校验真正通过时仍由 R9 同一运行直接生成双口径最终文件，随后由调用方 Codex/操作人在 Skill 外继续公司现有内部流程。Skill 不设置财务负责人或授权人，也不管理审批状态。

## R12 发布边界

- R12 使用严格 `config/performance_budgets.yml`：一个独立冷进程基线、三个独立后续进程，wall time 与 peak RSS 上限均为冷基线的 `1.50×`；每个选中来源每次运行只完整哈希一次，禁止应用级摘要缓存。
- duplicate candidate 先分区且不超过 1,000,000 pairs；禁止全局未分区二次匹配。对抗、property、metamorphic、完整测试、R10/R11 私有回归、真实 bundled workbook runtime 和 staged privacy scan 均是发布强制门禁。
- 私有当前快照基准只评估绑定来源的元数据与完整摘要门禁；由于真实计算输入不足，明确输出 `real_calculation_baseline_status=NOT_EVALUATED_BLOCKED_SOURCE`、`business_files_parsed=0`，不得伪称正式计算性能或结果通过。
- `scripts/run_release_benchmark.py` 只发布聚合性能证据、绝对索引与 detached seal；`scripts/validate_skill_package.py` 可分别校验工作树与真实 staged index。
- 产品 `0.2.0` 发布代表 fail-closed 工作流通过门禁，不代表当前成本数据已可用。每次实际运行仍先做输入充分性检查；不足时提醒补充、合格替代、真实缩小范围或保持阻塞，未回复不构成授权，非可豁免项不得省略。
- 数据与全部校验通过时直接生成最终双口径文件，并明确显示绝对输出路径。Skill 不设置财务负责人或授权人，不管理公司内部审批；调用方在 Skill 外走公司现有流程。
- R12 不执行全局安装。任何机器首次建立全局可发现性时，必须在独立运行中先确认远端、main 与发布提交一致，再安装并验证发现性与行为 parity；已有有效机器回执时只复核，不重复安装。

R12 的性能定义、命令、输出、停止条件和 surprise 审计见 `references/RELEASE_PERFORMANCE_AND_OPERABILITY.md`。
