---
name: km-bid-discover
description: 在公开与已授权招采来源中进行高召回搜标、来源覆盖和官方线索发现；用于A/B工业维修检修机会的全量或增量发现。不得按设备/采购负关键词删结果，不作最终可投或排除结论。
---

# KM Bid Discover

## 每次运行前后硬契约

- `INPUT_SUFFICIENCY_PREFLIGHT`：直接调用时也必须先按 `../km-bid-scout/references/input_preflight_and_output_locator.md` 检查本 Skill 的 required 输入；缺失即 `BLOCKED`，不得静默省略，只有 Owner 逐字段、逐 run 显式授权的可豁免项才能降级。
- `OUTPUT_LOCATOR`：最终回复必须列出创建/更新/复用文件的绝对路径；没有文件时明确写“本次未生成文件”并给 output root。

## 触发

用于 `FULL_DISCOVERY`、`INCREMENTAL_DISCOVERY`、`DEADLINE_WATCH` 的发现阶段。

## 不触发

不要用本Skill判定资质、业绩、商务价值、最终P0/P1/X；不要读取或写入钉钉；不要发布规则。

## 输入

- trigger context：run_id、triggered_at原值、mode、source_scope、budget；
- `SourceRegistry`、query lattice、source cursors；
- 当前ACTIVE规则的只读manifest，仅用于保留Owner精确指纹，不用于搜索负过滤。

## 流程

1. 运行来源preflight：访问、登录能力、分页、合同漂移、cursor和缓存状态。
   同时核对条款、robots、授权、数据类别、保留策略和 query/page/byte/concurrency/timeout 预算；任一未审批则 `not_run`。
2. 生成六维查询格栅：设备×动作×故障×结果×合同形态×行业；控制组合爆炸并记录query_id。
3. 不使用`-采购/-轴承/-泵/-减速机/-加工/-地区`等负查询删结果。
4. 官方平台优先；聚合/搜索引擎只用于发现，保存回源待办。
5. 全国公告全部保留，地域在lot和worksite解析后处理。
6. 保存标题、编号、采购人、平台、链接、发布时间原文、初始截止原文和摘要；不从摘要推断最终性质。
7. 以项目编号+采购人+lot+版本为核心去重；重招、二次公告和更正不得误并。
8. 输出每个来源的ok/degraded/failed/not_run、查询/页/字节、cursor、重试、DLQ、错误和未覆盖原因；记录因预算未执行的 query。
9. 对新术语产生“召回扩词候选”，不直接改ACTIVE查询。
10. 采购意向、年度计划、合同到期等只产生 `SIGNAL`，不产生当前 P0/P1 候选。

## 质量门

- 来源失败不得输出“零机会”；必须`coverage_degraded=true`。
- 设备词、采购词、地域词不得在搜索层直接删除。
- 每条候选有source_id、query_id、first_seen、source_url和dedup evidence。
- 不确定内容保持原文，不补全。

## 性能

来源间并行；来源内按registry预算。优先增量cursor和内容hash。只把R0元数据交给下游，不下载无关全站。

## 输出

`SourceRun[]`、`SourceCoverage[]`、`DiscoveryCandidate[]`、`OfficialResolutionQueue[]`、`QueryExpansionProposal[]`。

输出契约版本 `0.4.1`；用 `python3 scripts/validate_output.py OUTPUT.json` 检查。不符合 `assets/output.schema.json` 的输出不交给下游。
