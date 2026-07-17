# OpenAIDatabase migration recovery status

状态：`COMPATIBILITY_GATES_REPAIRED_MATERIAL_COVERAGE_PENDING`

更新时间：`2026-07-17T08:19:52Z`

## 本 run execution contract

- 目标：在迁移后的唯一 AgentDatabase canonical checkout 中恢复可运行的兼容性闸门，并对 45 个 preservation patch 做 fail-closed coverage 对账。
- 最小范围：根双平面入口、OpenAIDatabase agent/human views、settlement/security/hygiene/candidate gates、迁移 handoff 证据。
- 禁止范围：旧根 governance/agent loop、已迁出项目、`data/**`/`macdata/**` raw 回灌、private core、credential、历史大型 archive、live/deploy 状态改写。
- 停止条件：`material coverage loss > 0`、S13 当前证据未成立、任一 gate 失败、或动作将进入 S14-P2。
- 本 run 停止点：`material coverage loss = 28`，所以 S14-P1 未开始。

## Canonical 与 patch 完整性

- 本 run 起点：`HEAD == origin/main == 89d5a48dbebcc6ac0cba8126df11ad7c19e38d7e`，clean。
- 本地 compatibility checkpoint：`b6d0e401acb0b2678a2b0c48ca34e9cba3e10bdc`；未 push。
- 逻辑 patch：`45`；存储文件：`46`。
- stored series SHA-256：`c79feb8be37c63546cb5f0118b5687bc8c9fc1b14bca76981f5fbadc69a4f0e2`，PASS。
- decompressed series SHA-256：`4ee88eb7be9a889308344dcd8540bee13caaa3924e253594a4e36b18fc20e0b9`，PASS。
- 第 8 个 patch：按 `8.chunk00`、`8.chunk01` 顺序连接后解压，PASS。
- 未执行批量 `git am`；未执行 reset、rebase、merge、force、临时远端 branch 或 PR。

## Coverage 结论

机器可读明细见 [`COVERAGE_MATRIX.tsv`](COVERAGE_MATRIX.tsv)。

| 状态 | 数量 | 解释 |
|---|---:|---|
| integrated | 1 | 由当前 canonical source 确定重建并通过当前 gate |
| superseded | 16 | 被迁移后的双平面、顶层 MemoryAtlas 或更严格安全/数据合同替代 |
| pending | 28 | 当前 active tree 无足够实现或 acceptance 证据 |

`material coverage loss = 28`，不是 0。最早 pending 项是 sequence 6 / `S04-P2`。另一路
`OpenAIDatabase/docs/remediation/memory_atlas_v1_2/` 的 66/149 scoped roadmap 与本 preservation
line 不同，不能用来把本 matrix 的 S09-P2/P3 写成 PASS。

## 本 run 恢复的 current-source 能力

- 新根 `AGENTS.md`：绑定唯一 AgentDatabase checkout、main-only、双平面与禁止恢复边界。
- agent views：从 198 条 canonical records 重建 `AGENT_MEMORY.md` 与 `agent-memory.json`；drift=0。
- human views：从当前 `docs/governance` 确定生成 `功能清单.md`、`开发记录.md`、`模型参数文件.md`；check-render PASS。
- local settlement policy：移除对已迁出根 `scripts/agent_loop/settlement_policy.py` 的运行依赖。
- workflow security：只审计当前 `.github/workflows/dual-plane.yml`；2 个外部 Action 均固定到官方 full SHA，permissions/concurrency/timeout 完整。
- repository hygiene：1814 tracked files、509181652 bytes、36 large objects、0 violations；
  baseline tree `772014ef4433dc9db75c874428434fe98b474074`。
- snapshot recovery：绑定 checkpoint `b6d0e40`，canonical hash 100%、10 个 offline queries、3 个 negative cases、约 3.2 秒。
- candidate gate：6 proofs PASS、5 profiles PASS、160 benchmark cases、37 fault cases、7 E2E scenarios、0 hard-gate failures；状态仅为 `CANDIDATE_READY_NOT_PUBLISHED`。

## 未解除的事实

- active canonical 上的 S13 Whole-Stage Review 尚未成立；preservation 声明的
  Critical/Important=`0/0` 与 Phase progress=`36/50` 只能作为待恢复目标，不能提升为当前 PASS。
- S14-P1：`NOT_STARTED`；S14-P2：`NOT_STARTED`。
- S08：`FAILED_NEEDS_HUMAN_AUTH`，development-nonblocking。
- `delivery_readiness=FAILED`。
- `TASK-OAI-B-001=blocked`。
- App/live：本 run 未真实重验，状态不更新。
- 2026-07-07 raw 数据继续只使用 AgentDatabase `raw-archives-20260708` Release；未复制任何 raw/archive。

## 下一 run

只执行 `S04-P2`：从 patch 6 提取行为合同，在顶层 `MemoryAtlas/` 与当前 OpenAIDatabase
双平面上实现等价的 modular atlasctl/runtime；先写 regression，再运行目标测试、
check-render、changed-scope governance、repository hygiene 与 candidate gate。通过后停止，
不进入 S04-P3，更不进入 S14。

预计还需 `29–33` 个 run（28 个 pending coverage item 的 phase/review 收敛，加 S14-P1
与必要复核）；约 `18–36` 小时工程时间；当前置信度 `0.67`。估算会随每个 phase
被判定 integrated 或 superseded 而收敛。
