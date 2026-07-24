# 04 Agent 授权、潜性信号、自我迭代与决策债

> 合并版本：`v0.0.0.1`。以下源文档严格按原目录顺序串联；正文仅更新因合并失效的文件路径，并增加稳定锚点、来源边界与自动生成区块。

> 范围：Agent 授权边界、潜性信号、自我迭代建议、决策债与首页增量说明。

## 本卷源文件映射

| 顺序 | 原文件 | 本文件锚点 | 类型 |
|---:|---|---|---|
| 1 | 20_Agent授权边界说明.md | [src-20-agent-authorization](#src-20-agent-authorization) | 静态原文 |
| 2 | 21_潜性信号说明.md | [src-21-latent-signals](#src-21-latent-signals) | 静态原文 |
| 3 | 22_自我迭代建议说明.md | [src-22-self-iteration](#src-22-self-iteration) | 静态原文 |
| 4 | 23_决策债说明.md | [src-23-decision-debt](#src-23-decision-debt) | 静态原文 |
| 5 | 24_首页上次来以后发生了什么说明.md | [src-24-since-last-visit](#src-24-since-last-visit) | 静态原文 |

---

<!-- BEGIN SOURCE: src-20-agent-authorization; original=20_Agent授权边界说明.md; baseline_sha256=7f8d8b3a624e71f9d1de91e9a75c3ac72845bbabf6aa74d25ace393e7b0c5aee -->
<a id="src-20-agent-authorization"></a>
# 20 Agent 授权边界说明

## 结论

S08 P2 已完成。任务 ID 为 `MA-V12-S08P2`，验收 ID 为
`ACC-MA-V12-S08P2`，状态为
`phase_s08_p2_authorization_boundary_completed_pending_s08_p3`。

本阶段只做轻量授权边界：人类授权后才能 apply，raw 不可修改，proposal 需要先被人类
确认。这里不做复杂 Delegation Contract UI，不做多 agent 系统，也不执行真正的 apply。
下一步只允许进入 S08 P3。

## 人类负责什么

- 判断 proposal 是否值得 apply。
- 检查 proposal 的目标文件、风险、回滚方案和验证命令。
- 明确批准或拒绝 proposal。
- 只有批准后，proposal 才能进入 `approved_by_human`。

## Agent 负责什么

- 生成 proposal 草案。
- 标明 `proposal_id`、`target_type`、`target_files`、`validation_commands` 和
  `rollback_plan`。
- 做机器输出检查，确认 raw 不可修改、credential 不可作为目标、没有未授权 apply。
- 输出 `data/derived/agent_collaboration/agent_authorization_boundary_report.json`。

## 不能做什么

- raw 不可修改，`data/public_raw/` 不能作为 apply target。
- credentials 不能作为 transcript 或 proposal target。
- 未进入 `approved_by_human` 的 proposal 不能 apply。
- S08 P2 不实现复杂 Delegation Contract UI。
- S08 P2 不创建多 agent 系统。
- S08 P2 不生成 stage flight recorder；这留给 S08 P3。
- No GitHub main upload in this phase。

## 怎么验证

- `python scripts/atlasctl.py analyze --stage agent-authorization --dry-run`
- `python scripts/atlasctl.py audit --check agent-authorization`
- `validate:v1.2-s08-p2`

如果验证通过，说明当前系统能解释授权边界：raw 不可改、proposal 需人类授权、apply
不在本 phase 执行、复杂 Delegation Contract UI 不在本 phase 实现。
<!-- END SOURCE: src-20-agent-authorization -->

---

<!-- BEGIN SOURCE: src-21-latent-signals; original=21_潜性信号说明.md; baseline_sha256=feb74709f4718ddebb29c7dce289d7a7c919a772f3ef72b0a667817a2dbe9f4f -->
<a id="src-21-latent-signals"></a>
# 21 潜性信号说明

S09 P1 已生成 `data/derived/behavior_intelligence/latent_signals.json`。

这些内容只是“候选信号”：每条都必须同时写出证据、反证、另一种解释、置信度和下一次验证。它们不是诊断，也不是人格标签。

当前有 5 条候选，主要指向：

- 可恢复资产是否值得沉淀。
- 重复流程是否适合收束为 dry-run 或 validator。
- 讨论是否需要先变成单个交付件。
- 细节优化是否需要质量上限。
- 多来源任务是否需要更早固定 run contract。

下一步只允许进入 S09 P2：自我迭代建议与 proposal expiry。整体 S01-S14 全部完成前不上传 GitHub main。
<!-- END SOURCE: src-21-latent-signals -->

---

<!-- BEGIN SOURCE: src-22-self-iteration; original=22_自我迭代建议说明.md; baseline_sha256=61d098d9416463a615d0d23533cb883360c7dbb42747b7432ab932a1f010550f -->
<a id="src-22-self-iteration"></a>
# 22 自我迭代建议说明

S09 P2 已生成 `data/derived/behavior_intelligence/self_iteration_suggestions.json`。

这 5 条内容都是候选 proposal，不会在本阶段自动改文件。每条 proposal 都有过期时间和行动半衰期，避免永久 pending。

当前覆盖：

- memory
- config
- AGENTS
- style
- personalization

下一步只允许进入 S09 P3：Decision Debt Ledger。整体 S01-S14 全部完成前不上传 GitHub main。
<!-- END SOURCE: src-22-self-iteration -->

---

<!-- BEGIN SOURCE: src-23-decision-debt; original=23_决策债说明.md; baseline_sha256=37118f61fb99a614530455b47606f92d1a648b5b5f8888384ddc1f007d23a39e -->
<a id="src-23-decision-debt"></a>
# 23 决策债说明

S09 P3 已生成 `data/derived/behavior_intelligence/decision_debt_ledger.json`。

这 8 条内容都是候选记录，用来指出反复讨论但还没落地的区域。每条只给一个最小下一步、一个预期交付件和一个停止条件。

当前不会自动改文件、不会生成待办压力清单、不会修改 raw。

下一步只允许进入 S09 Review。整体 S01-S14 全部完成前不上传 GitHub main。
<!-- END SOURCE: src-23-decision-debt -->

---

<!-- BEGIN SOURCE: src-24-since-last-visit; original=24_首页上次来以后发生了什么说明.md; baseline_sha256=700146ecfd8af903cd14c22324a2ab3829e30d47de1fc400ed9fcedb4fb762dc -->
<a id="src-24-since-last-visit"></a>
# 24 首页上次来以后发生了什么说明

## 结论

S10 P1 已把 Memory Atlas 首页首屏改成中文信息 ROI 入口。用户进入首页后先看到
“上次来以后发生了什么”，再决定是否进入星图、时间轴、搜索或总结复盘。

## 首屏回答的五个问题

1. 新增重要资料：近 30 天新增或活跃的高价值资料是什么。
2. 增强结论：哪些主题或结论比上一窗口更强。
3. 减弱或过期结论：哪些结论正在冷却、过期或需要复核。
4. 待授权 proposal：哪些 recommendation 或行动候选需要人工 triage。
5. 同步失败：哪些数据源不新鲜或同步失败。

## 使用方式

- 先读每张卡片的中文结论和证据摘要。
- 看“下一步”决定进入星图、时间轴、总结与迭代或搜索。
- 需要机器细节时展开“机器细节”；默认不展示 schema/hash/path 堆叠。

## 边界

- 本 phase 不执行 proposal apply。
- 本 phase 不修改 raw。
- 本 phase 不上传 GitHub main。
- S10 P2 再处理全局中文和 Chinese UX linter 增强。

Machine-readable boundary summary: Memory Atlas v1.2 S10 P1; MA-V12-S10P1; ACC-MA-V12-S10P1; phase_s10_p1_home_arrival_briefing_completed_pending_s10_p2; validate:v1.2-s10-p1; home_arrival_briefing.v1_2_s10_p1; pending S10 P2; No GitHub main upload in this phase; No raw mutation; No proposal apply execution.
<!-- END SOURCE: src-24-since-last-visit -->
