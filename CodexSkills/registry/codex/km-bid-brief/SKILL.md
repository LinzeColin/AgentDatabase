---
name: km-bid-brief
description: 把已审计机会整理成Owner可直接使用的简明搜标结果、截止动作和投标证据清单。用于每日/增量报告，限制噪声和人工时间；不得把P2包装成可投或隐藏来源降级。
---

# KM Bid Brief

## 每次运行前后硬契约

- `INPUT_SUFFICIENCY_PREFLIGHT`：直接调用时也必须先按 `../km-bid-scout/references/input_preflight_and_output_locator.md` 检查本 Skill 的 required 输入；缺失即 `BLOCKED`，不得静默省略，只有 Owner 逐字段、逐 run 显式授权的可豁免项才能降级。
- `OUTPUT_LOCATOR`：最终回复必须列出创建/更新/复用文件的绝对路径；没有文件时明确写“本次未生成文件”并给 output root。

## 触发

审计完成后生成用户可见报告和机器产物索引。

## 报告顺序

1. `P0_DIRECT`：可立即进入投标准备；
2. `P1_RESOLVABLE`：只列截止前可补的明确缺口；
3. `P2_EVIDENCE`：只列高匹配且值得继续取证的少量项目；
4. `X_EXCLUDE`：汇总数量和原因，默认不展开，保留机器证据；
5. `coverage_degraded`：必须显著展示。

`SIGNAL` 另立“公告前线索”区，必须显示 horizon/confidence，不得混入 P0/P1。

## 每条必备字段

项目/标包、A/B方向、官方链接、采购人、实施地、参与/购标/报价节点原文、主要工作、唯一主体、满足证据、缺口、商务风险、唯一下一步、审计状态。

## 人工预算

- Owner每日通常只看P0、P1和最多3个例外；
- 不输出长篇代码或过程；
- 证据细节放可展开附录；
- 同项目多个镜像只展示官方入口；
- 截止不明确明确写UNKNOWN，不自行换算。

## 质量门

P0/P1无官方源、无审计、跨主体、动态证据过期或关键附件缺失时必须降级。来源故障不得生成“今日无机会”。

## 输出

Markdown/JSON/可选Excel简报、截止动作表、EvidenceChecklist和RunCoverage摘要。

Owner接受时可附 `CaptureHandoff`，仅包含投标准备的证据清单、节点、责任人和缺口；不扩张为写标书、报价或提交。

输出契约版本 `0.4.1`；用 `python3 scripts/validate_output.py OUTPUT.json` 检查。不符合 `assets/output.schema.json` 的输出不交给用户。
