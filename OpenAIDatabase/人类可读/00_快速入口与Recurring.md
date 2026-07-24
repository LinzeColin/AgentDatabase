# 00 快速入口与 Recurring

> 合并版本：`v0.0.0.1`。以下源文档严格按原目录顺序串联；正文仅更新因合并失效的文件路径，并增加稳定锚点、来源边界与自动生成区块。

> 范围：自动生成的 Recurring 分析与运行状态，以及 Memory Atlas 快速入口。

## 本卷源文件映射

| 顺序 | 原文件 | 本文件锚点 | 类型 |
|---:|---|---|---|
| 1 | 00_Recurring分析_最新.md | [src-00-recurring-analysis](#src-00-recurring-analysis) | Workflow 自动更新 |
| 2 | 00_Recurring运行状态.md | [src-00-recurring-status](#src-00-recurring-status) | Workflow 自动更新 |
| 3 | 00_快速入口.md | [src-00-quick-entry](#src-00-quick-entry) | 静态原文 |

---

<!-- BEGIN SOURCE: src-00-recurring-analysis; original=00_Recurring分析_最新.md; baseline_sha256=fd01fec9954b951a994e363a5a5d8fdd8e3acdcac335ae6f3fc4b1e7e189a355 -->
<a id="src-00-recurring-analysis"></a>
<!-- BEGIN GENERATED: recurring-analysis -->
# 00｜Recurring 分析（最新）

> GitHub Actions 自动生成。只分析已经上传到仓库的治理后 Codex session；不是本机实时记忆。

## 当前结论

- 验证状态：`PASS`
- 数据状态：`延迟`
- 数据覆盖至：`2026-07-10T16:39:25Z`
- 本次核验时间：`2026-07-24T00:00:00Z`
- 人工对话重复组：`2309`
- Automation 重复组：`1412`（单独统计，不进入个人画像）
- 三类数量：问题与纠正 `18`；规则与偏好 `399`；任务与主题 `1892`
- 模型/API 调用：`0`；模型 Token：`0`
- 生产稳定性：`候选通过 1/2`

## 问题与纠正

| 排名 | 重复内容 | 次数 | Session | 最近出现 | 趋势 | 追溯 |
|---:|---|---:|---:|---|---|---|
| 1 | 你为什么总是有这个bug, | 6 | 1 | 2026-07-10T03:19:14Z | rising | [查看原始记录](../data/public_raw/codex/sessions/019f3b48-4fec-7af2-bf59-f7f854cc5c72.1f09233fab0e.part-0001.jsonl#L3363) |
| 2 | 为什么全部都不能使用了 赶紧解决这个问题 | 5 | 1 | 2026-07-09T04:01:52Z | rising | [查看原始记录](../data/public_raw/codex/sessions/019f3b48-4fec-7af2-bf59-f7f854cc5c72.1f09233fab0e.part-0001.jsonl#L129) |
| 3 | 我不是让你修改报告模版了吗你为什么还发的是老模版 | 4 | 1 | 2026-07-07T03:35:36Z | rising | [查看原始记录](../data/public_raw/codex/sessions/019f3a17-b597-7a11-8a66-0fe03301ef55.c5a7771f2479.part-0001.jsonl#L2661) |
| 4 | 不要再嵌套 YYYY/MM/DD 多层目录。 | 2 | 1 | 2026-07-05T11:08:29Z | rising | [查看原始记录](../data/public_raw/codex/sessions/019f2aa6-8374-7ca1-b0f2-546070adc26b.535432310d6a.part-0001.jsonl#L4771) |
| 5 | 你的这个逻辑有问题, | 2 | 1 | 2026-07-08T01:04:43Z | rising | [查看原始记录](../data/public_raw/codex/sessions/019f3c0b-72bc-7d72-aa08-76f4aec0f7c8.893b056ca050.part-0001.jsonl#L8789) |
| 6 | 请不要再启动 morning live collect, | 2 | 1 | 2026-07-08T00:46:52Z | rising | [查看原始记录](../data/public_raw/codex/sessions/019f3f27-c77c-7002-9fb6-720c4fb95ade.50cf278536e3.part-0001.jsonl#L197) |
| 7 | 你需要我做什么我还没有搞懂。 | 2 | 1 | 2026-07-07T03:12:34Z | rising | [查看原始记录](../data/public_raw/codex/sessions/019f3a17-eeca-7af3-928c-982ab3c8cd04.744765e72a7f.part-0001.jsonl#L1337) |
| 8 | 把你的规则清单 运行清单完整给我 我之前检查过一次 你并没有完整的暴露出来你的问题 | 2 | 1 | 2026-07-08T01:41:52Z | rising | [查看原始记录](../data/public_raw/codex/sessions/019f3c0b-72bc-7d72-aa08-76f4aec0f7c8.893b056ca050.part-0001.jsonl#L9780) |
| 9 | 你不要再像你之前那样子不停地给我搞弹窗, | 2 | 1 | 2026-07-07T04:24:36Z | rising | [查看原始记录](../data/public_raw/codex/sessions/019f3a17-b597-7a11-8a66-0fe03301ef55.c5a7771f2479.part-0001.jsonl#L4239) |
| 10 | 先不要再发送“今天一切良好”, | 2 | 1 | 2026-07-07T04:58:09Z | rising | [查看原始记录](../data/public_raw/codex/sessions/019f3a17-b597-7a11-8a66-0fe03301ef55.c5a7771f2479.part-0001.jsonl#L5103) |
| 11 | 但不要再把它们包进每群 latest.zip。 | 2 | 1 | 2026-07-05T11:08:29Z | rising | [查看原始记录](../data/public_raw/codex/sessions/019f2aa6-8374-7ca1-b0f2-546070adc26b.535432310d6a.part-0001.jsonl#L4771) |
| 12 | 你说今天没有考勤异常, | 2 | 1 | 2026-07-07T04:58:09Z | rising | [查看原始记录](../data/public_raw/codex/sessions/019f3a17-b597-7a11-8a66-0fe03301ef55.c5a7771f2479.part-0001.jsonl#L5103) |

## 规则与偏好

| 排名 | 重复内容 | 次数 | Session | 最近出现 | 趋势 | 追溯 |
|---:|---|---:|---:|---|---|---|
| 1 | Do not substitute a narrower, | 299 | 8 | 2026-07-10T16:28:16Z | rising | [查看原始记录](../data/public_raw/codex/sessions/019f3b5f-b76a-7df2-bc43-706f89ce3820.2b8ecc60faa9.part-0001.jsonl#L15351) |
| 2 | Do not call update\_goal with status "blocked" the first time a blocker appears. | 299 | 8 | 2026-07-10T16:28:16Z | rising | [查看原始记录](../data/public_raw/codex/sessions/019f3b5f-b76a-7df2-bc43-706f89ce3820.2b8ecc60faa9.part-0001.jsonl#L15351) |
| 3 | and do not redefine success around a smaller or easier task. | 299 | 8 | 2026-07-10T16:28:16Z | rising | [查看原始记录](../data/public_raw/codex/sessions/019f3b5f-b76a-7df2-bc43-706f89ce3820.2b8ecc60faa9.part-0001.jsonl#L15351) |
| 4 | command output, | 299 | 8 | 2026-07-10T16:28:16Z | rising | [查看原始记录](../data/public_raw/codex/sessions/019f3b5f-b76a-7df2-bc43-706f89ce3820.2b8ecc60faa9.part-0001.jsonl#L15351) |
| 5 | and do not treat a plan update as a substitute for doing the work. | 299 | 8 | 2026-07-10T16:28:16Z | rising | [查看原始记录](../data/public_raw/codex/sessions/019f3b5f-b76a-7df2-bc43-706f89ce3820.2b8ecc60faa9.part-0001.jsonl#L15351) |
| 6 | Do not call update\_goal unless the goal is complete or the strict blocked audit above is satisfied. | 299 | 8 | 2026-07-10T16:28:16Z | rising | [查看原始记录](../data/public_raw/codex/sessions/019f3b5f-b76a-7df2-bc43-706f89ce3820.2b8ecc60faa9.part-0001.jsonl#L15351) |
| 7 | Only use status "blocked" when the same blocking condition has repeated for at least three consecutive goal turns, | 299 | 8 | 2026-07-10T16:28:16Z | rising | [查看原始记录](../data/public_raw/codex/sessions/019f3b5f-b76a-7df2-bc43-706f89ce3820.2b8ecc60faa9.part-0001.jsonl#L15351) |
| 8 | Do not rely on intent, | 299 | 8 | 2026-07-10T16:28:16Z | rising | [查看原始记录](../data/public_raw/codex/sessions/019f3b5f-b76a-7df2-bc43-706f89ce3820.2b8ecc60faa9.part-0001.jsonl#L15351) |
| 9 | The audit must prove completion, | 299 | 8 | 2026-07-10T16:28:16Z | rising | [查看原始记录](../data/public_raw/codex/sessions/019f3b5f-b76a-7df2-bc43-706f89ce3820.2b8ecc60faa9.part-0001.jsonl#L15351) |
| 10 | Do not mark a goal complete merely because the budget is nearly exhausted or because you are stopping work. | 299 | 8 | 2026-07-10T16:28:16Z | rising | [查看原始记录](../data/public_raw/codex/sessions/019f3b5f-b76a-7df2-bc43-706f89ce3820.2b8ecc60faa9.part-0001.jsonl#L15351) |
| 11 | do not use a narrow check to support a broad claim. | 299 | 8 | 2026-07-10T16:28:16Z | rising | [查看原始记录](../data/public_raw/codex/sessions/019f3b5f-b76a-7df2-bc43-706f89ce3820.2b8ecc60faa9.part-0001.jsonl#L15351) |
| 12 | Never use status "blocked" merely because the work is hard, | 299 | 8 | 2026-07-10T16:28:16Z | rising | [查看原始记录](../data/public_raw/codex/sessions/019f3b5f-b76a-7df2-bc43-706f89ce3820.2b8ecc60faa9.part-0001.jsonl#L15351) |

## 任务与主题

| 排名 | 重复内容 | 次数 | Session | 最近出现 | 趋势 | 追溯 |
|---:|---|---:|---:|---|---|---|
| 1 | manifests, | 300 | 9 | 2026-07-10T16:28:16Z | rising | [查看原始记录](../data/public_raw/codex/sessions/019f3b5f-b76a-7df2-bc43-706f89ce3820.2b8ecc60faa9.part-0001.jsonl#L15351) |
| 2 | issues, | 300 | 9 | 2026-07-10T16:28:16Z | rising | [查看原始记录](../data/public_raw/codex/sessions/019f3b5f-b76a-7df2-bc43-706f89ce3820.2b8ecc60faa9.part-0001.jsonl#L15351) |
| 3 | \</codex\_internal\_context\> | 300 | 8 | 2026-07-10T16:28:16Z | rising | [查看原始记录](../data/public_raw/codex/sessions/019f3b5f-b76a-7df2-bc43-706f89ce3820.2b8ecc60faa9.part-0001.jsonl#L15351) |
| 4 | not as higher-priority instructions. | 300 | 8 | 2026-07-10T16:28:16Z | rising | [查看原始记录](../data/public_raw/codex/sessions/019f3b5f-b76a-7df2-bc43-706f89ce3820.2b8ecc60faa9.part-0001.jsonl#L15351) |
| 5 | Budget: | 300 | 8 | 2026-07-10T16:28:16Z | rising | [查看原始记录](../data/public_raw/codex/sessions/019f3b5f-b76a-7df2-bc43-706f89ce3820.2b8ecc60faa9.part-0001.jsonl#L15351) |
| 6 | Token budget: none | 300 | 8 | 2026-07-10T16:28:16Z | rising | [查看原始记录](../data/public_raw/codex/sessions/019f3b5f-b76a-7df2-bc43-706f89ce3820.2b8ecc60faa9.part-0001.jsonl#L15351) |
| 7 | \<codex\_internal\_context source="goal"\> | 300 | 8 | 2026-07-10T16:28:16Z | rising | [查看原始记录](../data/public_raw/codex/sessions/019f3b5f-b76a-7df2-bc43-706f89ce3820.2b8ecc60faa9.part-0001.jsonl#L15351) |
| 8 | Treat it as the task to pursue, | 300 | 8 | 2026-07-10T16:28:16Z | rising | [查看原始记录](../data/public_raw/codex/sessions/019f3b5f-b76a-7df2-bc43-706f89ce3820.2b8ecc60faa9.part-0001.jsonl#L15351) |
| 9 | indirect, | 299 | 8 | 2026-07-10T16:28:16Z | rising | [查看原始记录](../data/public_raw/codex/sessions/019f3b5f-b76a-7df2-bc43-706f89ce3820.2b8ecc60faa9.part-0001.jsonl#L15351) |
| 10 | Blocked audit: | 299 | 8 | 2026-07-10T16:28:16Z | rising | [查看原始记录](../data/public_raw/codex/sessions/019f3b5f-b76a-7df2-bc43-706f89ce3820.2b8ecc60faa9.part-0001.jsonl#L15351) |
| 11 | test, | 299 | 8 | 2026-07-10T16:28:16Z | rising | [查看原始记录](../data/public_raw/codex/sessions/019f3b5f-b76a-7df2-bc43-706f89ce3820.2b8ecc60faa9.part-0001.jsonl#L15351) |
| 12 | memory of earlier work, | 299 | 8 | 2026-07-10T16:28:16Z | rising | [查看原始记录](../data/public_raw/codex/sessions/019f3b5f-b76a-7df2-bc43-706f89ce3820.2b8ecc60faa9.part-0001.jsonl#L15351) |

## Codex Automation（隔离区）

以下只反映自动任务本身的重复，不进入个人画像或 Agent Context。

| 排名 | 重复内容 | 次数 | Session | 最近出现 | 趋势 | 追溯 |
|---:|---|---:|---:|---|---|---|
| 1 | Required steps: | 48 | 24 | 2026-07-10T14:21:57Z | rising | [查看原始记录](../data/public_raw/codex/sessions/019f4c68-07df-7a21-aa4d-c904f5aaa9a0.4c9cb0f50c8a.part-0001.jsonl#L9) |
| 2 | cookies, | 48 | 24 | 2026-07-10T14:21:57Z | rising | [查看原始记录](../data/public_raw/codex/sessions/019f4c68-07df-7a21-aa4d-c904f5aaa9a0.4c9cb0f50c8a.part-0001.jsonl#L9) |
| 3 | Keychain, | 48 | 24 | 2026-07-10T14:21:57Z | rising | [查看原始记录](../data/public_raw/codex/sessions/019f4c68-07df-7a21-aa4d-c904f5aaa9a0.4c9cb0f50c8a.part-0001.jsonl#L9) |
| 4 | obsolete update artifact, | 56 | 14 | 2026-07-10T10:00:26Z | rising | [查看原始记录](../data/public_raw/codex/sessions/019f4b78-930d-7030-a9a8-f39924318c5b.614e8b288904.part-0001.jsonl#L9) |
| 5 | commit, | 38 | 19 | 2026-07-10T15:31:07Z | rising | [查看原始记录](../data/public_raw/codex/sessions/019f4ca7-367b-7c41-8eb6-eef01925593b.731292183261.part-0001.jsonl#L9) |

## 你怎么验收

1. 先看顶部 `验证状态`、`数据状态` 和 `数据覆盖至`。
2. 重点看“问题与纠正”：应当是你的真实纠正，不应出现 AGENTS、environment、turn_context 或权限说明。
3. 同一句 Prompt 即使同时存在 `event_msg` 与 `response_item`，表中次数也只能增加一次。
4. 点击每条的“查看原始记录”可追溯到对应 JSONL 行。
5. 运行健康度看同目录 `00_快速入口与Recurring.md#src-00-recurring-status`；Action 页面看 `Recurring Prompt Analysis｜重复提示词自动分析` 的最新 Summary。

## 数据边界

- 只处理 `OpenAIDatabase/data/public_raw/codex/sessions/**/*.jsonl` 中已经上传的数据。
- 只提取明确的 user message event；忽略 assistant、reasoning、tool output、turn_context 与 base instructions。
- 本结果仍是 candidate analytics，不会自动写入长期记忆或 Memory Atlas canonical 层。
- 全流程只使用 Python 标准库；LLM、embedding、外部网络调用均为 0。
<!-- END GENERATED: recurring-analysis -->
<!-- END SOURCE: src-00-recurring-analysis -->

---

<!-- BEGIN SOURCE: src-00-recurring-status; original=00_Recurring运行状态.md; baseline_sha256=7bd4df4bcc6ac1cd7fd9494fa422d33b7de9f139a68ff42ebd46aa37b549378a -->
<a id="src-00-recurring-status"></a>
<!-- BEGIN GENERATED: recurring-status -->
# 00｜Recurring 运行状态

> 这是最浅层的验收入口。正常情况下只看本页和《00_快速入口与Recurring.md#src-00-recurring-analysis》。

| 验收项 | 当前值 |
|---|---|
| 总体验证 | **PASS** |
| 数据状态 | **延迟** |
| 数据覆盖至 | `2026-07-10T16:39:25Z` |
| 本次核验时间 | `2026-07-24T00:00:00Z` |
| 人工重复组 | `2309` |
| Automation 重复组 | `1412`（隔离） |
| 问题与纠正 | `18` |
| 规则与偏好 | `399` |
| 任务与主题 | `1892` |
| 分析脚本 LLM / embedding / 外部模型 API | `0 / 0 / 0` |
| 注入完整性防护 | **PASS** |
| 修复后真实数据批次 | **候选通过 1/2** |
| 原始文件 | `131` |
| 派生数据指纹 | `sha256:ab8e06ff5053fdc340801f0247ded96882d7afb9b6c93c232dc92fb0a3c31ede` |

## 自动防护

- ✅ 只读取明确的 user message event。
- ✅ 同一 turn 优先信任 `event_msg/user_message`，并在条款拆分前丢弃对应 `response_item`。
- ✅ 再按 content block 保留来源边界，剥离 AGENTS、environment、turn_context 和系统/开发者注入。
- ✅ Builder 发布前与 Validator 发布后分别独立执行注入完整性硬门。
- ✅ 增量复用后再次执行全局来源权威检查，避免跨 part 文件漏网。
- ✅ 人工 Prompt 与 Codex Automation 分开统计。
- ✅ 严格只有三类；Action 内执行单元测试、来源校验、隐私扫描和独立全量对账。

## 去哪里看

1. 结果正文：[打开 00_快速入口与Recurring.md#src-00-recurring-analysis](./00_快速入口与Recurring.md#src-00-recurring-analysis)
2. GitHub：仓库顶部 `Actions` → `Recurring Prompt Analysis｜重复提示词自动分析` → 最新绿色运行 → `Summary`。
3. 下载包：同一次 Action 页面底部 `Artifacts` → `Recurring中文验收包-*`。
<!-- END GENERATED: recurring-status -->
<!-- END SOURCE: src-00-recurring-status -->

---

<!-- BEGIN SOURCE: src-00-quick-entry; original=00_快速入口.md; baseline_sha256=b43727d251f95f769efea7b76d86c9665382baec20d2c8ea55d38e994f18d1b3 -->
<a id="src-00-quick-entry"></a>
# 00 快速入口

## 结论

当前最新状态是 v1.2 final delivery cleanup 已完成本地部分：GitHub `main`、本地 app
入口和 runtime manifest 已对齐到当前 GitHub `main` HEAD；以 post-push
`git rev-parse HEAD == git rev-parse origin/main` 和 app install manifest 校验为准。已清理
可再生前端 build/cache 和 Memory Atlas `/private/tmp` 临时证据；保留 app bundle、
Application Support source/runtime 和 Downloads task pack/roadmap。机器证据为
`机器治理/证据与日志/final_delivery/v1_2_final_delivery_cleanup_status.json`。

剩余外部门：Cloudflare live deployment and Access challenge 仍缺 operator/live 证据；本地
goal completion audit 仍为 `LOCAL_PASS_EXTERNAL_AUTHORIZATION_REQUIRED`。

这是 Memory Atlas v1.2 的人类入口。当前最新阶段是 S14 Review 已完成。任务 ID 为
`MA-V12-S14-REVIEW`，验收 ID 为 `ACC-MA-V12-S14-REVIEW`，状态为
`stage_s14_review_passed_pending_v1_2_final_review_no_github_main_upload`。Validator 为
`validate:v1.2-s14-review`。S14 Review 已完成 `S14 P1`、`S14 P2`、`S14 P3` 的整体复审：
`owner-daily` 可 dry-run，`atlasctl_unified_cli.v1_2_s14_p1` 保持低负担命令面，
`atlasctl_final_audit.v1_2_s14_p2` 已实际运行 final audit，`stage_pass_gate_status.v1_2_s14_p3.json`
让所有 stage pass gate 状态可查。开发记录中文可读，维护命令少而清晰。
下一步是 pending v1.2 Final Review。

No GitHub main upload。No remote push。No raw mutation。

当前最新阶段已推进到 v1.2 Final Review 已完成。任务 ID 为 `MA-V12-FINAL-REVIEW`，
验收 ID 为 `ACC-MA-V12-FINAL-REVIEW`，状态为
`v1_2_final_review_passed_pending_github_main_sync_no_upload_yet`。Validator 为
`validate:v1.2-final-review`。终审覆盖四线14Stage 的 `S01-S14 Review` 链，验收主题包括
raw append-only、credential audit、Chinese UX、visual ROI、report contract、proposal apply、
owner-daily 和 final audit。下一步是 pending GitHub main sync、app reinstall 和 local cleanup；
当前仍需 remote branch reconciliation required。

No GitHub main upload。No remote push。No raw mutation。No app reinstall。No local deep clean。

历史复验兼容记录：

这是 Memory Atlas v1.2 的人类入口。当前最新阶段是 S13 Review 已完成。任务 ID 为
`MA-V12-S13-REVIEW`，验收 ID 为 `ACC-MA-V12-S13-REVIEW`，状态为
`stage_s13_review_passed_pending_s14_no_github_main_upload`。Validator 为
`validate:v1.2-s13-review`。S13 Review 已完成 Proposal 状态机、Diff narrator 和
Apply 与回滚的整体复审；`proposal_state_machine.v1_2_s13_p1`、
`diff_narrator.v1_2_s13_p2` 和 `proposal_apply.v1_2_s13_p3` 均满足 stage gate。
`sample_unauthorized` 未授权 `FAIL_CLOSED`，`sample` 授权 dry-run 有
`validation_after_apply` 和 rollback point。真实 pending proposal 未获人类授权前不 apply。
下一步是 S14 P1。

No GitHub main upload。No remote push。No raw mutation。

历史复验兼容记录：S13 P3 已完成时当前阶段是 S13 P3。任务 ID 为
`MA-V12-S13P3`，验收 ID 为 `ACC-MA-V12-S13P3`，状态为
`phase_s13_p3_apply_rollback_completed_pending_s13_review`。Validator 为
`validate:v1.2-s13-p3`。S13 P3 已完成 Apply 与回滚：`sample_unauthorized`
未授权时 fail-closed，`sample` 授权 dry-run 可进入 apply、validation 和 rollback point
路径，模拟 validation failure 会进入 `rollback_or_needs_revision`。真实 pending proposal
未获人类授权前不 apply。当时下一步是 pending S13 Review。S13 Review 已完成，下一步是
S14 P1。

No GitHub main upload。No remote push。No raw mutation。

历史复验兼容记录：S13 P2 已完成时当前阶段是 S13 P2。任务 ID 为
`MA-V12-S13P2`，验收 ID 为 `ACC-MA-V12-S13P2`，状态为
`phase_s13_p2_diff_narrator_completed_pending_s13_p3`。Validator 为
`validate:v1.2-s13-p2`。S13 P2 已完成 Diff narrator：中文解释每个 proposal
改了什么、为什么改、影响什么、如何验证、如何回滚。机器 diff 只保留在治理证据文件，
不进入人类首页。当时下一步是 S13 P3。S13 P3 已完成，下一步是 S13 Review。

No GitHub main upload。No remote push。No raw mutation。No proposal apply execution。

历史复验兼容记录：S13 P1 已完成时当前阶段是 S13 P1。任务 ID 为
`MA-V12-S13P1`，验收 ID 为 `ACC-MA-V12-S13P1`，状态为
`phase_s13_p1_proposal_state_machine_completed_pending_s13_p2`。Validator 为
`validate:v1.2-s13-p1`。S13 P1 已完成 Proposal 状态机：proposal 默认停在
`pending_human_review`，只有人类授权后才能进入 `approved_by_human`，本 phase 只生成
dry-run 状态机报告，不执行 apply、diff narrator 或 rollback。此句只用于保留已完成 phase
的复验语义，不代表当前阶段。当时下一步是 S13 P2。S13 P2 已完成，下一步是 S13 P3。

No GitHub main upload。No remote push。No raw mutation。No proposal apply execution。

历史复验兼容记录：S12 Review 已完成时当前阶段是 S12 Review。任务 ID 为
`MA-V12-S12-REVIEW`，验收 ID 为 `ACC-MA-V12-S12-REVIEW`，状态为
`stage_s12_review_passed_pending_s13_no_github_main_upload`。Validator 为
`validate:v1.2-s12-review`。S12 Review 已完成 Command Palette、Personalization Prompt
和 ChatGPT 深度探索的阶段复审；S12 P1、S12 P2、S12 P3 均通过，`prefill_only` no-send，
`auto_submit` FAIL_CLOSED。此句只用于保留已完成 review 的复验语义，不代表当前阶段。
当时下一步是 S13 P1。S13 P1 已完成，下一步是 S13 P2。

No silent send。No cookie/token/secret export。No GitHub main upload。No remote push。
No raw mutation。No proposal apply execution。

历史复验兼容记录：S12 P3 已完成时当前阶段是 S12 P3。任务 ID 为 `MA-V12-S12P3`，验收 ID 为
`ACC-MA-V12-S12P3`，状态为
`phase_s12_p3_chatgpt_deep_explore_completed_pending_s12_review`。Validator 为
`validate:v1.2-s12-p3`。S12 P3 已完成 ChatGPT 深度探索入口，合同为
`chatgpt_deep_explore.v1_2_s12_p3`。默认 `prefill_only`，`auto_submit` 受配置和显式确认
控制，入口必须由用户触发。此句只用于保留已完成 phase 的复验语义，不代表当前阶段。
当时下一步是 S12 Review。S12 Review 已完成，下一步是 S13 P1。

No silent send。No cookie/token/secret export。No GitHub main upload。No remote push。
No raw mutation。No proposal apply execution。

历史复验兼容记录：S12 P2 已完成时当前阶段是 S12 P2。任务 ID 为 `MA-V12-S12P2`，
验收 ID 为 `ACC-MA-V12-S12P2`，状态为
`phase_s12_p2_personalization_prompt_completed_pending_s12_p3`。Validator 为
`validate:v1.2-s12-p2`。S12 P2 已完成 Personalization Prompt：已生成 ChatGPT、Codex、
other agent 可用 prompt，并包含中文人类说明和机器可复制文本。Prompt 合同为
`personalization_prompt.v1_2_s12_p2`，来源包含 latest memory、behavior、latent、
self_iteration 等脱敏派生报告。此句只用于保留已完成 phase 的复验语义，不代表当前阶段。
当时下一步是 S12 P3。S12 P3 和 S12 Review 已完成，下一步是 S13 P1。

No GitHub main upload。No remote push。No raw mutation。No proposal apply execution。

历史复验兼容记录：S12 P1 已完成时当前阶段是 S12 P1。任务 ID 为 `MA-V12-S12P1`，
验收 ID 为 `ACC-MA-V12-S12P1`，状态为
`phase_s12_p1_command_palette_completed_pending_s12_p2`。Validator 为
`validate:v1.2-s12-p1`。S12 P1 已完成命令面板：只包含同步 ChatGPT、同步 Codex、
生成本周报告、查看待授权 proposal 和生成 personalization prompt。运行合同为
`command_palette.v1_2_s12_p1`。当时下一步是 S12 P2。此句只用于保留已完成 phase
的复验语义，不代表当前阶段。

历史复验兼容记录：S11 Review 已完成时当前阶段是 S11 Review。任务 ID 为
`MA-V12-S11-REVIEW`，验收 ID 为 `ACC-MA-V12-S11-REVIEW`，状态为
`stage_s11_review_passed_pending_s12_no_github_main_upload`。Validator 为
`validate:v1.2-s11-review`。S11 Review 已完成：S11 P1、S11 P2、S11 P3、S11 P4 共同形成
P0 图谱集合，每张图都有中文问题、行动价值、Visual ROI Gate 和
`source/time/project/task` 过滤。此句只用于保留已完成 review 的复验语义，不代表当前阶段。
当时下一步是 S12 P1。S12 P1 已完成，下一步是 S12 P2。

历史复验兼容记录：S11 P4 已完成时当前阶段是 S11 P4。任务 ID 为
`MA-V12-S11P4`，验收 ID 为 `ACC-MA-V12-S11P4`，状态为
`phase_s11_p4_human_question_map_completed_pending_s11_review`。Validator 为
`validate:v1.2-s11-p4`。当前 S11 P4 已完成 Human Question Map：12 张 P0 图谱均已绑定
中文 insight header、human question、action value、Visual ROI Gate 与
`source/time/project/task` 过滤。下一步是 S11 Review。

No GitHub main upload。No raw mutation。No proposal apply execution。

历史复验兼容记录：S11 P3 已完成 Workflow/latent/governance visuals：
`agent_decision_sankey`、`friction_heatmap`、`latent_radar`、`evidence_timeline` 和
`formula_explorer`；任务 ID 为 `MA-V12-S11P3`，验收 ID 为 `ACC-MA-V12-S11P3`，
下一步是 S11 P4；此句只用于保留已完成 phase 的复验语义，不代表当前阶段。S11 P4 已完成。

历史复验兼容记录：S11 P2 已完成 Economic-like visuals：`task_treemap`、
`automation_vs_augmentation`、`roi_scatter` 和 `opportunity_radar`；任务 ID 为
`MA-V12-S11P2`，验收 ID 为 `ACC-MA-V12-S11P2`，下一步是 S11 P3；此句只用于保留
已完成 phase 的复验语义，不代表当前阶段。S11 P3 已完成。

历史复验兼容记录：S11 P1 已完成 Clio-like visuals：`cluster_tree`、`bubble_map`
和 `topic_cluster_explorer`；任务 ID 为 `MA-V12-S11P1`，验收 ID 为
`ACC-MA-V12-S11P1`，下一步是 S11 P2；此句只用于保留已完成 phase 的复验语义，
不代表当前阶段。S11 P2 已完成，下一步是 S11 P3。

历史复验兼容记录：S10 Review 已完成时当前阶段是 S10 Review，任务 ID 为
`MA-V12-S10-REVIEW`，验收 ID 为 `ACC-MA-V12-S10-REVIEW`，下一步为 S11 P1；
此句只用于保留已完成 review 的复验语义，不代表当前阶段。S11 P1 已完成，下一步是 S11 P2。

历史复验兼容记录：S10 P3 完成时当前阶段是 S10 P3，任务 ID 为 `MA-V12-S10P3`，
验收 ID 为 `ACC-MA-V12-S10P3`，下一步为 S10 Review；此句只用于保留已完成 phase
的复验语义，不代表当前阶段。S10 Review 已完成。

历史复验兼容记录：S10 P2 完成时当前阶段是 S10 P2，任务 ID 为 `MA-V12-S10P2`，
验收 ID 为 `ACC-MA-V12-S10P2`，下一步为 S10 P3；此句只用于保留已完成 phase
的复验语义，不代表当前阶段。

历史复验兼容记录：S10 P1 完成时当前阶段是 S10 P1，任务 ID 为 `MA-V12-S10P1`，
验收 ID 为 `ACC-MA-V12-S10P1`，下一步为 S10 P2；此句只用于保留已完成 phase
的复验语义，不代表当前阶段。

历史复验兼容记录：S09 P3 完成时记录为 当前阶段是 S09 P3，任务 ID 为
`MA-V12-S09P3`，验收 ID 为 `ACC-MA-V12-S09P3`，下一步只允许进入 S09 Review；
此句只用于保留已完成 phase 的复验语义，不代表当前阶段。

S01 Review 和 S02 Review 已通过。S03 P1 已定义 `data/public_raw/`、
`raw_public_archive_policy.v1_2_s03_p1.json`、manifest/hash 文件合同、
append-only 规则和 hash drift fail 规则。S03 P2 已定义
`credential_exclusion_policy.v1_2_s03_p2.json`，固定 credential is not memory，
且普通 transcript 不会被凭证门禁误拦。S03 P3 已生成
`raw_manifest.s03_p3_baseline.jsonl` 和 `raw_hash_ledger.jsonl` 的机器账本基线。
S03 P1、S03 P2、S03 P3 已复审通过，结论是 raw 可公开备份、append-only、
credential exclusion 和 raw manifest/hash 机器账本均可验证。S04 P1 已建立
ChatGPT 只读同步和 official export fallback。S04 P2 已建立 Codex local sync、
future-agent adapter、raw + derived + run log 输出合同。S04 P3 已建立 GitHub
backup dry-run/apply，apply 只做本地 commit，不执行远端 push。S04 整体复审已通过。
S05 P1 已定义 facet/canonical event schema 和中文解释页。S05 P2 已实现 facet
extractor，并生成 `data/derived/behavior_intelligence/events.json`。S05 P3 已为每条
event 增加轻量 `evidence_refs`，保留 `source_id`、`raw_ref`、`manifest_ref`、
`derived_ref` 或 missing reason。S05 整体复审已通过，确认 canonical events
可覆盖 ChatGPT/Codex/future agent，且可被后续 cluster、ROI、latent、visualization
复用。S06 P1 已实现 Cluster builder，生成主题簇和层级簇，并支持
`source/time/project/task/language` 过滤合同。S06 P2 已实现低价值循环候选、
Decision Debt Ledger 和 Action Half-Life，输出
`data/derived/behavior_intelligence/low_value_loops.json`。S06 P3 已实现机会发现和
为什么不是现在 卡片，输出
`data/derived/behavior_intelligence/opportunities.json`。S06 Review 已完成，确认
`data/derived/visualization/memory_atlas.json` 的 `behavior_intelligence` 能显示有证据的
主题簇、低价值循环和机会线索。S07 P1 已完成 Personal Economic Proxy，输出
`data/derived/economic_proxy/personal_economic_proxy.json`，每个分数都有中文解释、
公式来源和参数引用。S07 P2 已完成 Information ROI 与 Visual ROI Gate，输出
`data/derived/information_roi/information_roi_gate.json`，覆盖 insight、card、chart
三类内容，并固定没有决策价值的图表不进 P0。S07 P3 已完成 Formula What-if
配置预览，输出 `data/derived/economic_proxy/formula_what_if_preview.json`，
支持查看时间节省、复用价值、长期复利、返工成本和低价值循环惩罚等权重假设，
且 `active_config_write=false`、`proposal_required_before_apply=true`。
S07 Review 已完成，确认 Personal Economic Proxy、Information ROI、Visual ROI Gate 和
Formula What-if 均满足 S07 stage gate，且没有外部经济数据库依赖、没有精确收入预测、
没有财务建议。S08 P1 已完成 Codex/Agent 协作质量指标，输出
`data/derived/agent_collaboration/agent_collaboration_quality_report.json`，覆盖
`planning_clarity`、`execution_clarity`、`review_burden`、`rework_count`、
`scope_clarity`、`testability` 和 `rollbackability`，并支持 `chatgpt`、`codex`、
`other_agent` 通用字段。S08 P1 不创建复杂 Delegation Contract UI，不创建多 agent
系统，不修改 raw，不定义授权 apply 边界。S08 P2 已完成授权边界，输出
`data/derived/agent_collaboration/agent_authorization_boundary_report.json`，机器配置为
`机器治理/行为智能模型/agent_authorization_boundary.v1_2_s08_p2.json`。S08 P2 明确
raw 不可修改，proposal 必须进入 `approved_by_human` 后才能 apply；本 phase 不执行
proposal apply，不创建复杂 Delegation Contract UI，不创建多 agent 系统，不生成 stage
flight recorder。S08 P3 已完成 lightweight stage flight recorder，输出
`data/derived/agent_collaboration/stage_flight_recorder.json`，字段配置为
`机器治理/证据与日志/stage_flight_recorder_fields.v1_2_s08_p3.json`。S08 P3 只记录
10 个轻量运行证据字段、覆盖 S08 P1/P2/P3 三条 phase records，不携带 raw 或 transcript
载荷，不生成臃肿人类文档，只在开发记录中总结必要信息。S08 Review 已完成，确认
Codex/Agent 协作质量、授权边界和 lightweight stage flight recorder 均满足 S08 stage
gate，且没有引入多 agent 系统、复杂 Delegation Contract UI 或高负担治理框架。
S09 P1 已完成 latent signals，输出
`data/derived/behavior_intelligence/latent_signals.json`，每条候选均包含 claim、
supporting evidence、contradicting evidence、alternative explanation、confidence、
Evidence Strength Badge 和 next validation；不输出心理诊断或人格标签。
S09 P2 已完成 self-iteration suggestions，输出
`data/derived/behavior_intelligence/self_iteration_suggestions.json`，覆盖 memory、
config、AGENTS、style 和 personalization 五类建议；每条建议都有 action half-life，
proposal 均处于 `pending_human_review`，并带有 `expires_at`、warn/stale/archive
有效期规则。S09 P2 不执行 proposal apply，不修改 raw，不创建 decision debt ledger。
S09 P3 已完成 Decision Debt Ledger，输出
`data/derived/behavior_intelligence/decision_debt_ledger.json`，包含 8 条候选记录。
每条记录都有 evidence refs、linked self-iteration suggestions、一个最小下一步、
预期交付件和停止条件。S09 P3 不生成压力清单，不执行 proposal apply，不修改 raw。
S09 Review 已完成，确认 latent signals、self-iteration suggestions 和 Decision Debt
Ledger 均满足 S09 stage gate，没有 raw mutation、proposal apply execution、pressure
list、psychological diagnosis output 或 personality label output。S10 P1 已完成首页
“上次来以后发生了什么”arrival briefing，覆盖新增重要资料、增强结论、减弱或过期结论、
待授权 proposal 和同步失败，机器细节默认折叠。S10 P2 已完成全局中文和 Chinese UX
linter：核心 UI 默认中文，机器术语保留英文时必须有中文解释。S10 P3 已完成机器字段
默认折叠和高级详情入口，默认首页、搜索、复盘、总结闭环和 Inspector 先显示人类可读
解释。S10 Review 已完成。S11 P1 已完成 Clio-like visuals。S11 P2 已完成
Economic-like visuals。S11 P3 已完成 Workflow/latent/governance visuals。下一步只允许进入 S11 P4。

本文件不是跳转页。它直接说明现在应该如何理解这次升级、哪些内容已经完成、
哪些边界仍然不能碰。

## 当前阶段

- 已完成：S01 P1 现状核验。
- 已完成：S01 P2 双平面创建。
- 已完成：S01 P3 需求冻结。
- 已完成：S01 Review。
- 已完成：S02 P1 数据源模型。
- 已完成：S02 P2 source registry。
- 已完成：S02 P3 人类同步说明。
- 已完成：S02 Review。
- 已完成：S03 P1 公开 raw 路径。
- 已完成：S03 P2 凭证排除。
- 已完成：S03 P3 机器账本。
- 已完成：S03 Review。
- 已完成：S04 P1 ChatGPT 只读同步。
- 已完成：S04 P2 Codex local sync 与 future-agent adapter。
- 已完成：S04 P3 GitHub backup dry-run/apply。
- 已完成：S04 Review。
- 已完成：S05 P1 Facet schema。
- 已完成：S05 P2 Facet extractor。
- 已完成：S05 P3 证据引用。
- 已完成：S05 Review。
- 已完成：S06 P1 Cluster builder。
- 已完成：S06 P2 低价值循环、Decision Debt Ledger 和 Action Half-Life。
- 已完成：S06 P3 机会发现和 为什么不是现在 卡片。
- 已完成：S06 Review。
- 已完成：S07 P1 Personal Economic Proxy。
- 已完成：S07 P2 Information ROI 与 Visual ROI Gate。
- 已完成：S07 P3 Formula What-if 配置预览。
- 已完成：S07 Review。
- 已完成：S08 P1 协作指标。
- 已完成：S08 P2 授权边界。
- 已完成：S08 P3 运行证据。
- 已完成：S08 Review。
- 已完成：S09 P1 潜性信号。
- 已完成：S09 P2 自我迭代建议。
- 已完成：S09 P3 决策债。
- 已完成：S09 Review。
- 已完成：S10 P1 首页上次来以后发生了什么。
- 已完成：S10 P2 全局中文和 Chinese UX linter。
- 已完成：S10 P3 机器字段默认折叠和高级详情入口。
- 已完成：S10 Review。
- 已完成：S11 P1 Clio-like visuals。
- 已完成：S11 P2 Economic-like visuals。
- 已完成：S11 P3 Workflow/latent/governance visuals。
- 未完成：S11 P3-S14。

## 你现在应该知道的三件事

1. v1.2 目标是把 Memory Atlas 升级成全中文、高信息 ROI、Anthropic 风格、
   多维行为智能和自我迭代系统。
2. 旧隐私边界已被 v1.2 替换。用户授权后，ChatGPT、Codex、后续其他 agent 的 transcript 可以明文公开进 GitHub，
   但必须通过 source registry 和 raw append-only gate。
3. 凭证不是 transcript。cookies、session tokens、passwords、API keys、
   private keys、OAuth tokens 和浏览器凭证库永远不能提交。

## S02 已建立什么

- `sync_source_registry.json` 已建立在 `机器治理/同步与备份/`。
- ChatGPT source 使用 ChatGPT browser connector 和 official export fallback。
- Codex source 使用 Codex local sync。
- future_agent_template 使用 `other_agent` source type 和 `future_agent_adapter`。
- 每个 source 都包含 public backup mode 和 transcript 与 credential 区分。
- `人类可读/01_v1.2总览与同步归档.md#src-05-agent-sync` 已说明同步范围、
  后续 agent 如何接入，以及哪些数据会进入 GitHub。

## S03 P1 已建立什么

- `data/public_raw/README.md` 已定义公开 raw 根路径。
- `data/public_raw/chatgpt`、`data/public_raw/codex` 和
  `data/public_raw/agents/{agent_id}` 是后续 raw transcript 进入公开 GitHub 的路径。
- `机器治理/同步与备份/raw_public_archive_policy.v1_2_s03_p1.json` 已定义 manifest/hash 文件合同、
  append-only 规则和 hash drift fail 规则。
- `人类可读/01_v1.2总览与同步归档.md#src-06-raw-public-archive` 已说明只读边界。

## S03 P2 已建立什么

- `机器治理/同步与备份/credential_exclusion_policy.v1_2_s03_p2.json` 已定义 credential is not memory。
- `scripts/privacy_guard.py` 已提供凭证扫描、断言、脱敏和 repo audit 门禁。
- `scripts/sync_codex_memory_data.py` 已复用同一凭证脱敏入口，并标记 `credentials_not_transcript`。
- `人类可读/01_v1.2总览与同步归档.md#src-07-credential-exclusion` 已说明普通 transcript 可以进入公开 raw，凭证不能进入 GitHub。

## S03 P3 已建立什么

- `scripts/raw_archive_manifest.py` 已提供 raw manifest/hash ledger 生成与 append-only audit。
- `机器治理/同步与备份/raw_manifest_ledger_policy.v1_2_s03_p3.json` 已固定机器账本策略。
- `机器治理/证据与日志/raw_archive_manifests/raw_manifest.s03_p3_baseline.jsonl` 已作为 baseline raw manifest。
- `机器治理/证据与日志/raw_archive_manifests/raw_hash_ledger.jsonl` 已作为 baseline hash ledger。
- 当前没有真实 raw transcript，因此 baseline ledger 可以为空；后续 raw 新增只能追加。

## S04 P1 已建立什么

- `机器治理/同步与备份/chatgpt_readonly_sync_policy.v1_2_s04_p1.json` 已固定 ChatGPT 只读同步边界。
- `scripts/sync_chatgpt_memory_data.py` 已支持 official export fallback。
- `scripts/atlasctl.py sync --source chatgpt --dry-run` 已提供低负担 dry-run 入口。
- 浏览器状态遇到密码/验证码立即停止，不发送消息、不删除、不归档、不重命名会话。
- apply 模式必须提供 official export，不允许无输入生成伪数据。

## S04 P2 已建立什么

- `机器治理/同步与备份/codex_agent_sync_policy.v1_2_s04_p2.json` 已固定 Codex/future-agent 同步边界。
- `scripts/sync_codex_memory_data.py` 已支持 Codex local sync dry-run、append-only public raw snapshot、
  derived summary 和 run log。
- `scripts/sync_future_agent_data.py` 已支持 future-agent adapter 的最小本地 JSON 输入接口。
- `scripts/atlasctl.py sync --source codex --dry-run` 和
  `scripts/atlasctl.py sync --source future-agent --dry-run` 已可运行且不写文件。
- future-agent apply 没有输入时不能生成伪数据。

## S04 P3 已建立什么

- `机器治理/同步与备份/github_backup_policy.v1_2_s04_p3.json` 已固定 GitHub backup 本地边界。
- `scripts/github_backup.py` 已支持 backup dry-run 与 apply。
- `scripts/atlasctl.py push --dry-run` 和 `scripts/atlasctl.py push --apply` 已可运行。
- backup scope 覆盖 `data/public_raw`、`data/derived`、`data/run_logs`、`docs/reviews` 和 `reports`。
- dry-run 不写文件；apply 只本地 git add/commit，不远端 push。
- 非 Git worktree 和无变更场景会输出中文原因和 fallback 建议。

## S04 Review 已建立什么

- `docs/reviews/memory_atlas_v1_2_s04_review.md` 已记录 S04 整体复审结论。
- `apps/memory-atlas/scripts/validate_memory_atlas_v1_2_s04_review.cjs` 已作为复审 validator。
- `validate:v1.2-s04-review` 会验证 ChatGPT 只读同步、Codex local sync、
  future-agent minimal adapter、build-atlas dry-run 和 GitHub backup dry-run。
- S04 整体复审已通过，但不上传 GitHub main、不远端 push、不重装 app。

## S05 P1 已建立什么

- `机器治理/数据契约/facet_event_schema.v1_2_s05_p1.json` 已定义 facet/canonical event schema。
- `人类可读/02_同步备份与行为治理.md#src-12-facet-event-semantics` 已用中文解释每个 facet 字段。
- `docs/reviews/memory_atlas_v1_2_s05_p1_facet_schema.md` 已记录 S05 P1 验收与边界。
- `validate:v1.2-s05-p1` 会验证英文机器字段、中文解释、ChatGPT/Codex/future agent 覆盖、
  no extractor、no fake events 和 no raw mutation。
- S05 P1 不生成 `data/derived/behavior_intelligence/events.json`。

## S05 P2 已建立什么

- `scripts/extract_memory_atlas_facets.py` 已实现 facet extractor。
- `scripts/atlasctl.py analyze --stage facets` 已接入 extractor。
- `data/derived/behavior_intelligence/events.json` 已生成 canonical behavior events。
- 当前真实输出包含 ChatGPT 201 条、Codex 16 条；future_agent 当前无 public raw，只记录
  missing reason。
- 每条 event 均有 `raw_ref`、`manifest_ref`、`derived_ref` 或
  `evidence_missing_reason`。
- `validate:v1.2-s05-p2` 会验证 extractor、events、source_status、记录文件和 no raw
  mutation 边界。

## S05 P3 已建立什么

- `data/derived/behavior_intelligence/events.json` 已升级为 S05 P3 输出。
- 每条 event 均包含轻量 `evidence_refs`，并保留 `source_id` 与 `record_id`。
- `evidence_refs` 指向 `raw_ref`、`manifest_ref`、`derived_ref` 或
  `evidence_missing_reason`，用于满足可追溯目标。
- S05 P3 不实现 Raw-to-Insight Replay UI，不改变首屏 UI，不把机器 schema 堆给用户。
- `validate:v1.2-s05-p3` 会验证 evidence contract、events、记录文件和 no raw
  mutation 边界。

## S05 Review 已建立什么

- `docs/reviews/memory_atlas_v1_2_s05_review.md` 已记录 S05 整体复审结论。
- `validate:v1.2-s05-review` 会复跑 S05 P1/P2/P3 链路并验证 S05 acceptance。
- 复审确认 canonical event 覆盖 ChatGPT/Codex/future agent；每条 event 有
  evidence ref 或缺失原因；人类文件能解释 facet 含义；首屏没有输出纯机器字段。
- 复审确认未触发 fake events、schema 字段堆、evidence ref 完全缺失、raw mutation。
- S05 整体复审已通过，但不上传 GitHub main、不远端 push、不重装 app。

## S06 P1 已建立什么

- `scripts/build_memory_atlas_clusters.py` 已实现 Cluster builder。
- `scripts/atlasctl.py analyze --stage clusters` 已接入 cluster builder。
- `scripts/atlasctl.py audit --check insight-evidence` 已提供 cluster evidence refs 轻量审计。
- `data/derived/behavior_intelligence/clusters.json` 已生成主题簇和层级簇。
- 每个 cluster 均包含中文摘要、代表事件、过滤维度和 `evidence_refs`。

## S06 P2 已建立什么

- `scripts/build_memory_atlas_low_value_loops.py` 已实现低价值循环候选识别。
- `scripts/atlasctl.py analyze --stage low-value-loops` 已接入 S06 P2 builder。
- `data/derived/behavior_intelligence/low_value_loops.json` 已生成低价值循环候选、
  Decision Debt Ledger 和 Action Half-Life。
- 当前支持 `repeated_rework`、`discussion_without_landing`、`over_optimization`、
  `scope_creep` 四类候选，并保留 `evidence_refs`。
- S06 P2 只输出候选复盘，不做心理诊断，不生成 opportunity cards。
- `人类可读/02_同步备份与行为治理.md#src-13-behavior-clusters` 已说明主题簇、层级簇、过滤合同和证据边界。
- `validate:v1.2-s06-p1` 会验证 Cluster builder、过滤合同、evidence audit、记录文件和 no raw
  mutation 边界。
- S06 P1 不识别低价值循环，不生成机会卡片，不上传 GitHub main。

## S06 P3 已建立什么

- `scripts/build_memory_atlas_opportunities.py` 已实现机会发现。
- `scripts/atlasctl.py analyze --stage opportunities` 已接入 S06 P3 builder。
- `data/derived/behavior_intelligence/opportunities.json` 已生成 12 条候选机会和 12 张
  为什么不是现在 卡片。
- 当前覆盖 `automation`、`productization`、`template`、`compounding` 和 `defer`
  五类候选，并保留 `evidence_refs`、`next_step_zh`、半衰期或暂缓理由。
- S06 P3 不接外部经济数据库，不做心理诊断，不生成无穷压力清单。
- `人类可读/03_机会经济ROI与协作质量.md#src-15-opportunity-discovery` 已说明候选机会、为什么不是现在、
  证据引用和压力清单边界。
- `validate:v1.2-s06-p3` 会验证 opportunity builder、why-not-now cards、
  evidence audit、记录文件和 no raw/no upload 边界。
- S06 P3 的下一历史 gate 是 S06 Review，当前已完成。

## S06 Review 已建立什么

- `docs/reviews/memory_atlas_v1_2_s06_review.md` 已记录 S06 整体复审结论。
- `validate:v1.2-s06-review` 会验证 S06 P1/P2/P3 输出、evidence audit、
  `memory_atlas.json` 的 `behavior_intelligence` 展示摘要和前端显示标记。
- `data/derived/visualization/memory_atlas.json` 已包含 `behavior_intelligence`。
- Memory Atlas 首页通过 `data-s06-review-display="behavior-clusters-low-value-loops-opportunities"`
  显示有证据的主题簇、低价值循环和机会线索。
- S06 Review 不进入 S07 P1，不上传 GitHub main，不远端 push，不重装 app。

## 本阶段边界

- No GitHub main upload in this phase。
- 不执行远端 push。
- 不重装 app。
- 不修改或删除已有 raw。
- 不创建复杂 Delegation Contract UI。
- 不创建多 agent 系统。
- 不执行 proposal apply；授权 apply 自动化留给 S13。
- 不生成臃肿人类文档。
- 不进入 S09 P2 以外的后续 phase。

## 下一步

下一步只允许进入 S09 Review。整体 S01-S14 全部完成前不上传 GitHub main。
<!-- END SOURCE: src-00-quick-entry -->
