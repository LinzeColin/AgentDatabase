# 07 Diff Narrator 与 Apply 回滚

> 合并版本：`v0.0.0.1`。以下源文档严格按原目录顺序串联；正文仅更新因合并失效的文件路径，并增加稳定锚点、来源边界与自动生成区块。

> 范围：差异叙述、Apply 门禁与回滚边界。

## 本卷源文件映射

| 顺序 | 原文件 | 本文件锚点 | 类型 |
|---:|---|---|---|
| 1 | 35_DiffNarrator说明.md | [src-35-diff-narrator](#src-35-diff-narrator) | 静态原文 |
| 2 | 36_Apply回滚说明.md | [src-36-apply-rollback](#src-36-apply-rollback) | 静态原文 |

---

<!-- BEGIN SOURCE: src-35-diff-narrator; original=35_DiffNarrator说明.md; baseline_sha256=e8b42eac7e56758d7332c0540530e513f28ac8f9c8960d2a2c4d30094b835bb5 -->
<a id="src-35-diff-narrator"></a>
# Diff Narrator 说明

## 结论

S13 P2 已完成。任务 ID 为 `MA-V12-S13P2`，验收 ID 为 `ACC-MA-V12-S13P2`，
状态为 `phase_s13_p2_diff_narrator_completed_pending_s13_p3`，validator 为
`validate:v1.2-s13-p2`，机器合同为 `diff_narrator.v1_2_s13_p2`。

Diff narrator 用中文解释 proposal：改了什么、为什么改、影响什么、如何验证、如何回滚。
完整机器 diff 不放在人类首页，机器 diff 保留在治理证据文件。下一步是 pending S13 P3。

## 你应该怎么读

- 改了什么：说明 proposal 采纳后可能改变的目标范围。
- 为什么改：说明来源理由和预期收益。
- 影响什么：说明影响的页面、报告、命令或文件范围，并明确不影响 raw。
- 如何验证：列出最小验证命令。
- 如何回滚：说明后续采纳失败时的回滚路径。

当前 S13 P2 不执行 apply，不执行 rollback，不授权 proposal，不修改 raw。

## 机器证据

机器 diff 位于
`机器治理/证据与日志/proposal_diffs/diff_narrator_machine_diff.v1_2_s13_p2.json`。
人类摘要位于 `data/derived/proposals/diff_narrator_report.json`。

## 边界

- No GitHub main upload。
- No remote push。
- No raw mutation。
- No proposal apply execution。
- pending S13 P3。

Machine-readable boundary summary: Memory Atlas v1.2 S13 P2; MA-V12-S13P2; ACC-MA-V12-S13P2; phase_s13_p2_diff_narrator_completed_pending_s13_p3; validate:v1.2-s13-p2; diff_narrator.v1_2_s13_p2; S13 P2; Diff narrator; 改了什么; 为什么改; 影响什么; 如何验证; 如何回滚; 机器 diff; No GitHub main upload; No remote push; No raw mutation; No proposal apply execution; pending S13 P3.
<!-- END SOURCE: src-35-diff-narrator -->

---

<!-- BEGIN SOURCE: src-36-apply-rollback; original=36_Apply回滚说明.md; baseline_sha256=862cd3e1e5f1467be1bdb8022b1748c149846e6897d99cc7ba7c86239d117516 -->
<a id="src-36-apply-rollback"></a>
# 36 Apply 回滚说明

S13 P3 已完成 Apply 与回滚。任务 ID 为 `MA-V12-S13P3`，验收 ID 为
`ACC-MA-V12-S13P3`，状态为
`phase_s13_p3_apply_rollback_completed_pending_s13_review`。Validator 为
`validate:v1.2-s13-p3`。

本 phase 的核心不是直接采纳所有 proposal，而是把安全闭环固定下来：

- 未授权的 `sample_unauthorized` 必须 fail-closed。
- 已授权的 `sample` 可以走自动 apply dry-run 路径。
- apply 后必须有 validation。
- validation 失败时必须进入 rollback 或 `rollback_or_needs_revision`。
- raw archive 永远不能作为 apply target。

真实 pending proposal 仍然需要人类授权。当前 5 个真实 pending proposal 没有被 apply。
`sample` 只是验收 fixture，用来证明授权 apply 代码路径可运行。

## 如何验证

```bash
pnpm --dir apps/memory-atlas run validate:v1.2-s13-p3
```

```bash
python3 scripts/atlasctl.py apply --proposal sample_unauthorized --dry-run
```

```bash
python3 scripts/atlasctl.py apply --proposal sample --dry-run
```

```bash
python3 scripts/atlasctl.py apply --proposal sample --dry-run --simulate-validation-failure
```

## 如何回滚

回滚本 phase 使用 git revert 对应本地 commit。若后续真实 proposal 被 apply，则优先使用
proposal 自带 rollback plan 或 git revert；raw 文件不回滚，因为 raw 只读、只追加。

边界：

- No GitHub main upload。
- No remote push。
- No raw mutation。
- pending S13 Review。

Machine-readable boundary summary: Memory Atlas v1.2 S13 P3; MA-V12-S13P3; ACC-MA-V12-S13P3; phase_s13_p3_apply_rollback_completed_pending_s13_review; validate:v1.2-s13-p3; proposal_apply.v1_2_s13_p3; S13 P3; Apply 与回滚; sample_unauthorized; sample; authorization required; validation_after_apply; rollback_or_needs_revision; No GitHub main upload; No remote push; No raw mutation; pending S13 Review.
<!-- END SOURCE: src-36-apply-rollback -->
