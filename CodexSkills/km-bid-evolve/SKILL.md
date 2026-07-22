---
name: km-bid-evolve
description: 基于历史回放、Owner反馈、钉钉投标结果和官方公示评估搜标质量，提出安全扩词、来源修复、排序或规则修改建议，并做影子运行。不得修改正式规则、Skill、holdout、evaluator或自动发布。
---

# KM Bid Evolve

## 每次运行前后硬契约

- `INPUT_SUFFICIENCY_PREFLIGHT`：直接调用时也必须先按 `../km-bid-scout/references/input_preflight_and_output_locator.md` 检查本 Skill 的 required 输入；缺失即 `BLOCKED`，不得静默省略，只有 Owner 逐字段、逐 run 显式授权的可豁免项才能降级。
- `OUTPUT_LOCATOR`：最终回复必须列出创建/更新/复用文件的绝对路径；没有文件时明确写“本次未生成文件”并给 output root。

## 触发

`EVOLVE_SHADOW`、质量复盘、规则提案和惊喜发现。

## 标签策略

- Owner接受/拒绝、实际投标、资格、候选、最终、中标后经济结果是不同成熟度标签；
- 未投不等于不相关，必须分原因；
- 落标不等于搜标错误；
- 结果待定不进入输赢训练；
- 中标但亏损更新商务模型，不作为纯成功。

## 流程

1. 按公告当时信息做时间切片回放；
2. 比较Agent first_seen与群first_seen；
3. 统计正样本召回、未知自动排除、精确负样本逃逸、审计冲突、资格准确、结果解析和人工时间；
4. 随机反查X/P2，发现隐蔽漏报；
5. 生成只扩召回的同义词、来源和结果模板提案；
6. 对任何收窄规则列出正反例、受影响项目和反事实；
7. ACTIVE与SHADOW并行，比较新增/删除/降级、质量、成本和人工；
8. sealed holdout由独立评估器执行；优化器不读标签；
9. 输出proposal，不修改ACTIVE、Skill或测试。
10. 把采购意向、合同到期和周期预测作为 `SIGNAL`评估，不计入当前 NOTICE 召回或 P0/P1。

## 自动/人工边界

只扩召回和解析修复可在测试通过后进入候选发布流程；新增排除、地域、能力、资格、业绩、商务门槛或sealed测试必须Owner approval。

## 输出

`MetricsReport`、`MissedOpportunitySamples`、`QueryExpansionProposal`、`RuleProposal`、`ShadowDiff`、`SurpriseQueue`。

输出契约版本 `0.4.1`；用 `python3 scripts/validate_output.py OUTPUT.json` 检查。不符合 `assets/output.schema.json` 的输出不交给下游。
