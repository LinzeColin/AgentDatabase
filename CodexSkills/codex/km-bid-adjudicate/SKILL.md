---
name: km-bid-adjudicate
description: 基于官方正文和附件构建采购事件图，识别货物、维修、工程、结果型运维、纯劳务、加工或混合主要义务，并映射A/B方向。用于复杂采购/维修交叉语义；未知不得排除。
---

# KM Bid Adjudicate

## 每次运行前后硬契约

- `INPUT_SUFFICIENCY_PREFLIGHT`：直接调用时也必须先按 `../km-bid-scout/references/input_preflight_and_output_locator.md` 检查本 Skill 的 required 输入；缺失即 `BLOCKED`，不得静默省略，只有 Owner 逐字段、逐 run 显式授权的可豁免项才能降级。
- `OUTPUT_LOCATOR`：最终回复必须列出创建/更新/复用文件的绝对路径；没有文件时明确写“本次未生成文件”并给 output root。

## 触发

输入完整或部分 `EvidenceBundle`，需要判断项目实质和A/B方向时。

## 不触发

不核最终资质、人员、业绩、平台权限或经济价值；不根据标题/单词直接排除。

## 核心模型

建立 `ProcurementEventGraph`：行业、系统、设备、部件、动作、故障、主要交付、验收、计价、材料、工艺、性能、质保、劳务指标、品牌身份、worksite和lot。

优先级：

```text
验收责任 > 主要交付 > 范围/工艺/性能责任 > 计价 > 材料 > 质保 > 标题
```

## 主要义务

- GOODS：型号/数量/到货验收，安装附随；
- REPAIR：旧设备拆检、修复、装配、试运和性能恢复；
- ENGINEERING：安装/改造/检修/联调并承担系统结果；
- O_AND_M：按可用率、工作包或结果负责，不只按人数工日；
- LABOR：甲方掌握工艺质量、按人数/工日/工时；
- MACHINING：加工为主，进入重型非标经济模型；
- MIXED：多种义务，按主要对价和验收确定；
- UNKNOWN：证据不足。

## 必须正确处理

- 维修中乙供轴承/密封/齿轮仍可为REPAIR；
- 标准设备供货含安装指导仍为GOODS；
- 供货+系统设计+基础+管线+电仪+性能保证可为ENGINEERING；
- 大型重型非标/修复再制造/紧急件加工不能被“加工”词排除；
- 全国公告逐lot判定。

## 反事实检查

拟排除时回答：为何不是维修/工程；是否有可救lot；若动作换成修复/性能验收是否改变；证据是否至少两类。回答不完整→NEEDS_EVIDENCE。

将标题中“采购/工程/维修”等词替换但保留范围证据时，结论应稳定；否则标记规则脆弱并进复核。

## 输出

`ProcurementEventGraph`、`principal_obligation`、`business_direction`、`semantic_confidence`、`evidence_refs`、`counterfactual_rescue_check`。

输出契约版本 `0.4.1`；用 `python3 scripts/validate_output.py OUTPUT.json` 检查。不符合 `assets/output.schema.json` 的输出不交给下游。
