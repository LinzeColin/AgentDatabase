---
module_name: raw-teleiosis
description: Canonical full white-box iteration control plane for Teleiosis v0.0.0.3. It executes Genesis/identity, premise challenge, current-environment and competitor research, Baseline/Candidate isolation, evaluation/holdout, ten-lens review, causal attribution, utility hard gates, independent-review boundary, packaging, rollback and reheat. This is an internal non-routed module, not a separately installable Skill.
metadata:
  version: v0.0.0.3
  source_lineage:
    - teleiosis-v0.0.0.1
    - owner-teleiosis-v0.0.0.2
    - market-integrated-teleiosis-v0.0.0.2
  implementation: canonical-parent-skill
  registry_entry: false
---

# Raw Teleiosis｜内置 T 模块

`T` 的实现就是当前 `teleiosis` 根目录的 canonical engine。这里仅保留模块身份、完整 Capability Manifest 和来源治理，不复制第二套脚本、Schema、测试或旧执行文档。

## 固定职责

- 永久 Genesis 与唯一 Skill 身份；
- 存在性挑战、当前环境、真实同行与真实产物；
- 只读 Baseline、可回滚 Candidate、冻结 Acceptance 与 sealed holdout；
- 十视角、因果 change set、保护任务、效用硬门和 `KEEP / REVERT / NO_CHANGE`；
- 独立复审边界、打包、安装、回滚、证据租约和 reheat。

## 执行边界

- `execution_mode = FULL_NO_ROUTING`；
- 每次 T 阶段必须读取 `CAPABILITIES.json` 的完整能力表；
- `NOT_APPLICABLE_WITH_REASON` 只允许在实际检查后使用；
- T 可以形成内部 `DecisionReceipt`，S/P 只能供证；
- 当前实现路径为父 Skill 的 `scripts/`、`references/`、`schemas/`、`tests/` 和 `delivery/`，不得从本目录启动第二套控制面。
