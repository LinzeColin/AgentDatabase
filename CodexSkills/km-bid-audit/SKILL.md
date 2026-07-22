---
name: km-bid-audit
description: 对P0/P1和高风险排除进行独立反对者审计，专门寻找维修机会被采购词误删、货物被工程词误推、地域/标包/资格/结果误判。审计冲突必须保留并升级，不得自动删除。
---

# KM Bid Audit

## 每次运行前后硬契约

- `INPUT_SUFFICIENCY_PREFLIGHT`：直接调用时也必须先按 `../km-bid-scout/references/input_preflight_and_output_locator.md` 检查本 Skill 的 required 输入；缺失即 `BLOCKED`，不得静默省略，只有 Owner 逐字段、逐 run 显式授权的可豁免项才能降级。
- `OUTPUT_LOCATOR`：最终回复必须列出创建/更新/复用文件的绝对路径；没有文件时明确写“本次未生成文件”并给 output root。

## 触发

P0/P1 100%执行；X/P2按风险、随机抽样和规则变更影响执行。

## 隔离要求

审计不读取前一Agent的自然语言理由，只读取原始EvidenceBundle、结构化抽取、规则版本和必要公司事实。避免确认偏差。

## 反对者任务

1. 若前序保留，寻找：标准货物主导、安装附随、纯劳务、排除地区、硬资格缺口、过期/终止、跨主体拼接、商业灾难。
2. 若前序排除，寻找：旧设备修复、性能验收、系统改造、可救lot、维修附带备件、结果型运维、重型非标加工、地点误读和附件遗漏。
3. 检查公告最新版本、更正、延期、终止和结果状态。
4. 检查关键字段的证据是否来自官方正文/附件而非摘要。
5. 复做反事实：改变标题但保留范围，结论是否稳定。
6. 核对官方域/来源注册表、项目/标包身份和证据版本，识别聚合镜像、仿冒链接和过期正文。

## 冲突策略

- 任一方向冲突 → `DISAGREEMENT_REVIEW`；
- 前序X、审计可保留 → 优先救回并继续取证；
- 双方UNKNOWN → Evidence backfill；
- 只有一致且证据齐，才通过P0/P1或X。

## 输出

`AuditDecision`：pass/conflict/pending、反证、漏证、受影响字段、建议状态和继续取证动作。

输出契约版本 `0.4.1`；用 `python3 scripts/validate_output.py OUTPUT.json` 检查。不符合 `assets/output.schema.json` 的输出不交给下游。
