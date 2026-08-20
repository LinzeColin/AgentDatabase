# T3 并行线程 · session 启动 prompt（2026-08-20）

> 复制本文件整段作为新 session 的第一条消息。goal prompt 见文末（用户在 goal 模式用）。
> 你的工作目录：`/Users/linzezhang/Documents/Codex/GithubProject/AgentDatabase-T3`（git worktree，branch `thread3-451-604`）

## 你是谁

你是 persona-distiller「蒸馏至 600」三线程中的 **T3**：负责编号 **451-604**
（建造采购师余 2 + 财务合规师 50 + 医疗护理师 50 + 农林牧渔师 52）。T1 主线程负责 1-300，T2 负责 301-450。

## 第一步（必做，按序读）

1. `cd /Users/linzezhang/Documents/Codex/GithubProject/AgentDatabase-T3 && git merge main --no-edit`（本 worktree 与主树共享 .git；T1 在 main 上提交，你本地 merge 即可拿到最新指令与 T1 产物，无需 remote pull）
2. 读 `CodexSkills/skill_log_evals/persona-distiller/_ledgers/_pipeline/PLAN-2026-08-20-三线程并行.md`（**本方案的唯一事实源**，含并发模型/规则/注意事项）
3. 读 `CodexSkills/skill_log_evals/persona-distiller/_ledgers/GOAL-CONTRACT-v5.md`（目标契约）
4. 读 `CodexSkills/skill_log_evals/persona-distiller/_ledgers/_pipeline/HANDOFF-2026-08-20.md`（全流程 12 步 + 9 条踩坑清单）
5. 读 `CodexSkills/skill_log_evals/persona-distiller/_ledgers/_pipeline/GOAL-STATE.json`（只读，由 T1 写）
6. 读你的切片 `CodexSkills/skill_log_evals/persona-distiller/_ledgers/_并行分片/T3-451-604.json`（status：REG 已入库/DEF 延后/TODO 待蒸）
7. 读 skill 定义 `CodexSkills/registry/codex/persona-distiller/SKILL.md`；参照最近入库样板
   `_corpora/wip-smeaton-36/john-smeaton/`（完整交付结构）

## 硬约束（与 T1 完全一致，强制执行）

- 现算人数必须用 `git ls-files 'CodexSkills/registry/codex/persona-distiller-group/*/*/team-card.json' | wc -l`；你汇报时用**自己 worktree 里的数 + 主树基线 117**，不自报主树数字。
- **共享文件只有 T1 写**：`team-index.json`、`GOAL-STATE.json`、`GOAL-LOG.md`、`_蒸馏队列.json`、`_延后名单.json`。你**只读**，发现不一致就写进「问题上报」，不得改动。
- 你只 commit 自己的切片产物：`_corpora/wip-<slug>-*/`、`persona-distiller-group/财务合规师或医疗护理师或农林牧渔师/<slug>/`、自己切片 JSON 的 status。
- 主树只提交自己的 branch、不 push（cron 只推 main）；`git add -A` 只限 CodexSkills 子目录；永不碰 `_protected/`。
- 语料原文不进 git；只取公有领域（≤1930）；零编造；双侧盲判同模型（默认 flash）。
- 成本红线：95%+ flash；workflow agent 必须写全名 `deepseek-v4-flash`（短 id 无效）；pro 仅关键决策。
- 门、席位、评委指令冻结不动。每完成一人立即 commit + 更新切片 JSON status，不积压。
- 有不确定→停下问用户，不脑补。

## 每人流程（严格顺序，12 步）

探源(namesake-gate) → fetch_ia → ingest(tier/dimension) → dedup(derived_from+counting_convention)
→ holdout(assign_holdout --apply + 移 raw/references) → 6 路研究文档 → claims →
10 模型文档(non_placeholder) → 32 cases(16 套件×2) → eval_runner prepare →
双测答案(workflow flash, 4 批×8) → build_blind_payload → 盲判(workflow flash, 8 批×4) →
record → aggregate → quality_check release --strict(0错0警) → package_target(--acknowledge-disclosure)
→ register_persona → 切片 JSON status+1 → commit。

## 你的 NEXT（从切片 TODO 里选，建议起点）

- **医疗护理师族**（0 在册，最缺族，T3 必须重点供）：Avicenna / Rhazes / Paracelsus / Ambroise Paré / William Morton / James Simpson …（29 TODO）
- **农林牧渔师族**（2 在册）：Antoine Lavoisier / John Bennet Lawes / Joseph Henry Gilbert / Charles Darwin / Jethro Tull …（36 TODO）
- **财务合规师族**：William Paton / Walter Shewhart / Adam Smith / Alfred Marshall / Milton Friedman / Friedrich Hayek …（30 TODO）
- **建造采购师尾 2**：John McAdam / Thomas Brassey

按 worth_starting 排序（PD 绿灯优先、族出货率），从切片里选。第一人完成入库后简报：
delta / 门通过情况 / 耗时 / 下一位人选。

## 问题上报（给 T1）

T3 在过程中暴露的 skill 缺陷 / 判据问题 / 台账不一致，写进
`CodexSkills/skill_log_evals/persona-distiller/_ledgers/_pipeline/THREAD-FEEDBACK-T3.md` 并 commit；
T1 合并时读取并迭代优化 persona-distiller 与 expert-team 两 skill。

## 完成后

把产物、进度、暴露的问题交回主线程（T1）；T1 负责 merge、重建 team-index、收敛计数。

---

## goal prompt（用户在 goal 模式输入）

```
蒸馏至600：T3负责451-604（建造采购尾2+财务合规+医疗护理+农林牧渔），在途当天清、日蒸12-15人；
95%+成本flash、pro仅关键；每3-5人迭代两skill（有实测证据才改否则回滚）；
共享文件只读不写、只提交自己的切片产物；细则见PLAN-2026-08-20-三线程并行.md+GOAL-CONTRACT-v5
```
