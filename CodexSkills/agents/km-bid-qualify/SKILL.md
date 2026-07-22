---
name: km-bid-qualify
description: 把语义候选绑定到唯一投标主体，核当前资质、人员、社保、业绩、供应商库、地域、商务、资金和产能，输出P0/P1/P2/X及唯一下一步。不得跨公司拼接或用过期底表当实时事实。
---

# KM Bid Qualify

## 每次运行前后硬契约

- `INPUT_SUFFICIENCY_PREFLIGHT`：直接调用时也必须先按 `../km-bid-scout/references/input_preflight_and_output_locator.md` 检查本 Skill 的 required 输入；缺失即 `BLOCKED`，不得静默省略，只有 Owner 逐字段、逐 run 显式授权的可豁免项才能降级。
- `OUTPUT_LOCATOR`：最终回复必须列出创建/更新/复用文件的绝对路径；没有文件时明确写“本次未生成文件”并给 output root。

## 触发

输入语义裁决和证据包，判断公司是否能直接投、可补后投、需继续取证或排除。

## 输入事实

私有company profile：legal_entity、资质/许可、安许、人员、注册、三类/特种人员、社保、在建占用、业绩证据、平台供应商权限、设备/产能和商业限制。所有动态事实必须有as_of、valid_until、source和freshness。

## 流程

1. 为每个lot枚举可能投标主体，但每个决策只绑定一个`legal_entity_id`。
2. 禁止用A公司资质+B公司人员+C公司业绩拼接。联合体/总分包只能进人工救援：公告明确允许、法律载体完整且Owner单标批准；不得暗中等效为跨主体拼证。
3. 把要求拆成：硬资格、评分项、商务条件；硬项不满足不能P0。
4. 人员核当前电子证、B/C证、社保月份、无在建/占用和可调度性。
5. 业绩按设备、范围、时间、金额、验收、发票/付款和主体逐字段匹配。
6. 核供应商库、邀请名单、品牌/制造商身份和平台账号权限。
7. 按lot实际实施地应用排除地域；其他地区计算调遣和响应，不额外一刀切。
8. 评估主材、脚手架/吊装、保证金、付款、验收、质保、工期、峰值现金和产能冲突。
9. 分别输出eligibility、commercial_worth、evidence_quality和readiness。
10. P1只保留截止前有现实可能补齐的缺口；每条给唯一下一步。

## Readiness

- P0_DIRECT：全部硬门、官方证据、商务底线和审计前置齐；
- P1_RESOLVABLE：明确缺口且截止前可补；
- P2_EVIDENCE：正文/附件/地点/动态事实不足；
- X_EXCLUDE：有充分证据的地域、货物、劳务、关闭、硬资格或Owner精确排除。

## 输出

`QualificationDecision`、`Opportunity`、`EvidenceChecklist`、`CapacityConflicts`、`NextAction`。

输出契约版本 `0.4.1`；用 `python3 scripts/validate_output.py OUTPUT.json` 检查。不符合 `assets/output.schema.json` 的输出不交给下游。
