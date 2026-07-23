# 00｜Recurring 分析（最新）

> GitHub Actions 自动生成。只分析已经上传到仓库的治理后 Codex session；不是本机实时记忆。

## 当前结论

- 验证状态：`PASS`
- 数据状态：`延迟`
- 数据覆盖至：`2026-07-10T16:39:25Z`
- 本次核验时间：`2026-07-23T00:00:00Z`
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
5. 运行健康度看同目录 `00_Recurring运行状态.md`；Action 页面看 `Recurring Prompt Analysis｜重复提示词自动分析` 的最新 Summary。

## 数据边界

- 只处理 `OpenAIDatabase/data/public_raw/codex/sessions/**/*.jsonl` 中已经上传的数据。
- 只提取明确的 user message event；忽略 assistant、reasoning、tool output、turn_context 与 base instructions。
- 本结果仍是 candidate analytics，不会自动写入长期记忆或 Memory Atlas canonical 层。
- 全流程只使用 Python 标准库；LLM、embedding、外部网络调用均为 0。
