# 06 问题地图、命令面板、个性化与 Proposal

> 合并版本：`v0.0.0.1`。以下源文档严格按原目录顺序串联；正文仅更新因合并失效的文件路径，并增加稳定锚点、来源边界与自动生成区块。

> 范围：Human Question Map、Command Palette、Personalization Prompt、ChatGPT 深度探索与 Proposal 状态机。

## 本卷源文件映射

| 顺序 | 原文件 | 本文件锚点 | 类型 |
|---:|---|---|---|
| 1 | 30_HumanQuestionMap说明.md | [src-30-human-question-map](#src-30-human-question-map) | 静态原文 |
| 2 | 31_CommandPalette命令面板说明.md | [src-31-command-palette](#src-31-command-palette) | 静态原文 |
| 3 | 32_PersonalizationPrompt说明.md | [src-32-personalization-prompt](#src-32-personalization-prompt) | 静态原文 |
| 4 | 33_ChatGPT深度探索说明.md | [src-33-chatgpt-deep-exploration](#src-33-chatgpt-deep-exploration) | 静态原文 |
| 5 | 34_Proposal状态机说明.md | [src-34-proposal-state-machine](#src-34-proposal-state-machine) | 静态原文 |

---

<!-- BEGIN SOURCE: src-30-human-question-map; original=30_HumanQuestionMap说明.md; baseline_sha256=80df52f7ca44a6e3ab9ce3c491785ace5b7d68bd2e2a186af338aca6e3ac6148 -->
<a id="src-30-human-question-map"></a>
# Human Question Map 说明

S11 P4 已完成 Human Question Map。它不是新加一批装饰图，而是把已经进入 P0 的
12 张图谱统一回答三个问题：

- 这张图回答哪个人类问题。
- 看完以后应该采取什么行动。
- 它是否通过 Visual ROI Gate 并允许进入 P0。

当前 P0 图谱覆盖 Clio-like visuals、Economic-like visuals 和
Workflow/latent/governance visuals。首页问题地图支持 `source/time/project/task`
过滤，点击卡片会进入对应的星图、搜索、ROI、总结或时间线视图继续复核。

Visual ROI Gate 不通过的候选不会进入 P0。本 phase 记录的失败候选包括
`decorative_density_cloud` 和 `raw_conversation_heat_glow`，它们只用于说明停用原因，
不作为 P0 图谱展示。

边界：No GitHub main upload in this phase。No raw mutation。No proposal apply execution。
下一步是 S11 Review。
<!-- END SOURCE: src-30-human-question-map -->

---

<!-- BEGIN SOURCE: src-31-command-palette; original=31_CommandPalette命令面板说明.md; baseline_sha256=09196ecaa3d363c3bc44dcb7cffa2062e312f93e9ac7a132d9516147e8f05d33 -->
<a id="src-31-command-palette"></a>
# 31 Command Palette 命令面板说明

## 结论

S12 P1 已完成命令面板。任务 ID 为 `MA-V12-S12P1`，验收 ID 为
`ACC-MA-V12-S12P1`，状态为
`phase_s12_p1_command_palette_completed_pending_s12_p2`，validator 为
`validate:v1.2-s12-p1`，运行合同为 `command_palette.v1_2_s12_p1`。

本阶段只完成低负担命令入口，不完成 S12 P2 的完整 personalization prompt 产物，
不完成 S12 P3 的 ChatGPT deep explore 发送或跳转自动化。

## 可用命令

| 命令 | command_id | 用途 |
|---|---|---|
| 同步 ChatGPT | `sync_chatgpt` | 用户触发后查看 ChatGPT 同步 dry-run 命令。 |
| 同步 Codex | `sync_codex` | 用户触发后查看 Codex 同步 dry-run 命令。 |
| 生成本周报告 | `generate_weekly_report` | 用户触发后进入 summary 视图，查看周报生成入口。 |
| 查看待授权 proposal | `view_pending_proposals` | 用户触发后进入 summary 视图，只查看 proposal，不执行 apply。 |
| 生成 personalization prompt | `generate_personalization_prompt` | 用户触发后查看 ChatGPT、Codex、other agent 可用 prompt 的 dry-run 合同。 |

## 安全边界

- No automatic send。
- No GitHub main upload。
- No remote push。
- No raw mutation。
- No proposal apply execution。
- No cookie、token、secret 输出。
- 下一步是 S12 P2。

## 运行与验证

- `python3 scripts/atlasctl.py generate-personalization-prompt --dry-run`
- `pnpm --dir apps/memory-atlas run validate:v1.2-s12-p1`

Machine-readable boundary summary: Memory Atlas v1.2 S12 P1; MA-V12-S12P1; ACC-MA-V12-S12P1; phase_s12_p1_command_palette_completed_pending_s12_p2; validate:v1.2-s12-p1; command_palette.v1_2_s12_p1; 同步 ChatGPT; 同步 Codex; 生成本周报告; 查看待授权 proposal; 生成 personalization prompt; generate_personalization_prompt; ChatGPT; Codex; other agent; No automatic send; No GitHub main upload; No remote push; No raw mutation; No proposal apply execution; S12 P2.
<!-- END SOURCE: src-31-command-palette -->

---

<!-- BEGIN SOURCE: src-32-personalization-prompt; original=32_PersonalizationPrompt说明.md; baseline_sha256=da8a17c5633c32b18c3362f90e3d6a4638a9913c831cafb7363990c1be75aa81 -->
<a id="src-32-personalization-prompt"></a>
# 32 Personalization Prompt 说明

## 结论

S12 P2 已完成 Personalization Prompt。任务 ID 为 `MA-V12-S12P2`，验收 ID 为
`ACC-MA-V12-S12P2`，状态为
`phase_s12_p2_personalization_prompt_completed_pending_s12_p3`，validator 为
`validate:v1.2-s12-p2`，prompt 合同为 `personalization_prompt.v1_2_s12_p2`。

本阶段生成 ChatGPT、Codex、other agent 三类可复制提示词。每类文件都有中文人类说明和
`机器可复制文本`。这些提示词来自 latest memory、behavior、latent、self_iteration、
decision debt 和 agent collaboration 等脱敏派生报告。

## 输出文件

| 目标 | 文件 | 说明 |
|---|---|---|
| 中文人类说明 | `data/derived/personalization/personalization_prompt_human_zh.md` | 汇总来源、目标和边界。 |
| ChatGPT | `data/derived/personalization/chatgpt_personalization.md` | 可复制到 ChatGPT personalization 或新对话启动上下文。 |
| Codex | `data/derived/personalization/codex_personalization.md` | 可复制到 Codex 任务启动上下文。 |
| other agent | `data/derived/personalization/other_agent_personalization.md` | 给后续其他 agent 的通用个性化入口。 |
| machine | `data/derived/personalization/personalization_export.json` | 机器可读 prompt、来源 freshness 和安全边界。 |

## 运行方式

- `python3 scripts/atlasctl.py generate-personalization-prompt`
- `python3 scripts/atlasctl.py generate-personalization-prompt --dry-run`

## 边界

- No automatic send。
- No GitHub main upload。
- No remote push。
- No raw mutation。
- No proposal apply execution。
- No S12 P3 ChatGPT deep explore execution。
- 下一步是 S12 P3。

Machine-readable boundary summary: Memory Atlas v1.2 S12 P2; MA-V12-S12P2; ACC-MA-V12-S12P2; phase_s12_p2_personalization_prompt_completed_pending_s12_p3; validate:v1.2-s12-p2; personalization_prompt.v1_2_s12_p2; ChatGPT; Codex; other agent; 中文人类说明; 机器可复制文本; latest memory; behavior; latent; self_iteration; S12 P3; No GitHub main upload; No remote push; No raw mutation; No proposal apply execution.
<!-- END SOURCE: src-32-personalization-prompt -->

---

<!-- BEGIN SOURCE: src-33-chatgpt-deep-exploration; original=33_ChatGPT深度探索说明.md; baseline_sha256=22e80b6555a3df0200617e79601ba4a9b45b6f882bd0b73c887c50ebec4d450d -->
<a id="src-33-chatgpt-deep-exploration"></a>
# 33 ChatGPT 深度探索说明

S12 P3 已完成 ChatGPT 深度探索入口。任务 ID 为 `MA-V12-S12P3`，验收 ID 为
`ACC-MA-V12-S12P3`，状态为
`phase_s12_p3_chatgpt_deep_explore_completed_pending_s12_review`，validator 为
`validate:v1.2-s12-p3`，合同为 `chatgpt_deep_explore.v1_2_s12_p3`。

本阶段只完成用户触发的 ChatGPT 深度探索入口。默认模式是 `prefill_only`：生成最新记忆
分析报告和深度探索提示，并构造 ChatGPT 预填充 URL。`auto_submit` 是配置受控模式，必须
同时满足配置和显式确认；默认不发送。

## 产物

| 产物 | 路径 | 用途 |
|---|---|---|
| Prompt payload | `data/derived/chatgpt_deep_explore/latest_memory_analysis_prompt.md` | 机器可复制文本和探索提示。 |
| Machine export | `data/derived/chatgpt_deep_explore/chatgpt_deep_explore_export.json` | launch URL、source freshness 和安全边界。 |
| Gate config | `机器治理/运行门禁/chatgpt_deep_explore.v1_2_s12_p3.json` | prefill_only / auto_submit 配置门禁。 |
| atlasctl | `scripts/atlasctl.py chatgpt-deep-explore` | 用户触发的 dry-run、生成和 open 命令。 |

## 用户触发命令

- `python3 scripts/atlasctl.py chatgpt-deep-explore --mode prefill_only --dry-run`
- `python3 scripts/atlasctl.py chatgpt-deep-explore --mode prefill_only`
- `python3 scripts/atlasctl.py chatgpt-deep-explore --mode prefill_only --open`

## 边界

- 用户触发。
- `prefill_only` 默认只填入。
- `auto_submit` 必须显式配置和确认。
- No silent send。
- No cookie/token/secret export。
- No GitHub main upload。
- No remote push。
- No raw mutation。
- No proposal apply execution。
- 下一步是 pending S12 Review。

Machine-readable boundary summary: Memory Atlas v1.2 S12 P3; MA-V12-S12P3; ACC-MA-V12-S12P3; phase_s12_p3_chatgpt_deep_explore_completed_pending_s12_review; validate:v1.2-s12-p3; chatgpt_deep_explore.v1_2_s12_p3; ChatGPT 深度探索; prefill_only; auto_submit; 用户触发; No silent send; No cookie/token/secret export; No GitHub main upload; No remote push; No raw mutation; No proposal apply execution; pending S12 Review.
<!-- END SOURCE: src-33-chatgpt-deep-exploration -->

---

<!-- BEGIN SOURCE: src-34-proposal-state-machine; original=34_Proposal状态机说明.md; baseline_sha256=f157d2ae230d73270767be18c40e1805dc506b8f1c974e34a01a204938345d8b -->
<a id="src-34-proposal-state-machine"></a>
# Proposal 状态机说明

## 结论

S13 P1 已完成。任务 ID 为 `MA-V12-S13P1`，验收 ID 为 `ACC-MA-V12-S13P1`，
状态为 `phase_s13_p1_proposal_state_machine_completed_pending_s13_p2`，validator 为
`validate:v1.2-s13-p1`，机器合同为 `proposal_state_machine.v1_2_s13_p1`。

本阶段只做 Proposal 状态机，不做 Diff narrator，不执行 apply，不执行 rollback。下一步是
pending S13 P2。

## 状态

- `draft`
- `pending_human_review`
- `approved_by_human`
- `applying`
- `applied`
- `validated`
- `committed`
- `failed_validation`
- `rollback_or_needs_revision`

主路径是 `draft → pending_human_review → approved_by_human → applying → applied → validated → committed`。
失败路径是 `failed_validation → rollback_or_needs_revision`。

## 当前 proposal

当前报告 `data/derived/proposals/proposal_state_machine_report.json` 汇总 5 个 proposal。
这些 proposal 都来自已脱敏 derived 报告，当前均为 `pending_human_review`，没有被授权，
因此不会进入 `applying`。

proposal expiry 已接入：warn 7 days、stale 30 days、archive 90 days。过期 proposal
不能进入 `applying`。

## 边界

- No GitHub main upload。
- No remote push。
- No raw mutation。
- No proposal apply execution。
- pending S13 P2。

Machine-readable boundary summary: Memory Atlas v1.2 S13 P1; MA-V12-S13P1; ACC-MA-V12-S13P1; phase_s13_p1_proposal_state_machine_completed_pending_s13_p2; validate:v1.2-s13-p1; proposal_state_machine.v1_2_s13_p1; S13 P1; Proposal 状态机; draft; pending_human_review; approved_by_human; applying; applied; validated; committed; failed_validation; rollback_or_needs_revision; proposal expiry; No GitHub main upload; No remote push; No raw mutation; No proposal apply execution; pending S13 P2.
<!-- END SOURCE: src-34-proposal-state-machine -->
