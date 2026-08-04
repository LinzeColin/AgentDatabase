# v0.0.0.32 — 声明产物逐条对账

任务包规定「未有真实证据不得标记完成」。这份台账逐条列出 DAG 声明的每个产物：
**落地了 / 换了形式落地 / 现在补不出来**，后两类写明原因。
不合并、不含糊，因为「记录在别处」和「没有记录」在汇报里长得一样。

| 任务 | 声明产物 | 状态 | 说明 |
|---|---|---|---|
| T00 | `SEMANTIC_RECONCILIATION.json` | ✅ 落地 | `.taskpack-runs/memory-atlas-v32/` |
| T00 | `LIVE_BASELINE.json` | ❌ **补不出来** | `T00_CLASSIFICATION.md` 只记了主体提交（`895a7c28`、clean、`HEAD == origin/main`）与九项分类，没有留下声明要求的完整基线。**Stage 0 那个状态此后已大幅改变**（R2 按设计清空、发布换了十余轮），今天从散落记录里重建一份并标成 Stage 0，与伪造 before 回执是同一类事 |
| T00 | `ENVIRONMENT_A0.json` | ❌ **补不出来** | 同上。环境事实分散在 `T00_CLASSIFICATION.md` 与 `t08/T08_RECORD.md`，但都不是当时的原子快照 |
| T01 | `STATIC_BYPASS_REPRODUCTION.json` | ✅ 落地 | |
| T01 | `BEFORE_BROWSER_RECEIPT.json` | ❌ **补不出来** | 它要的是**旁路被修复之前**站点的浏览器回执。那个状态已经不存在了，现在采只会得到修复后的页面。**今天造一份并标成「before」就是伪造证据**，所以不造 |
| T02 | metric contract tests | ✅ 落地 | `tests/test_visual_analytics_v31.py`、`test_live_snapshot_adapter_v31.py` |
| T02 | benchmark gate tests | ✅ 落地 | `tests/test_benchmark_comparator_v31.py`。**2026-08-04 之前从未跑过**，见 `t02/T02_RECORD.md` |
| T03 | `current.json` / `previous.json` / `history/<run_id>.json` / store receipts | ✅ 落地（生产） | `/srv/linze/apps/memory-atlas/shared/data/live-snapshot/`；摘要与摘要哈希见 `t10/FROZEN_CANDIDATE.json` |
| T04 | API receipt / status receipt | ✅ 落地 | `t05/API_TO_CHART_PREVIEW.json`、`t08/PRODUCTION_LIVE_SNAPSHOT_SUMMARY.json`、生产 `status_registration` |
| T05 | preview UI / browser receipt / network receipt | ✅ 落地 | `t05/` 全套含 `browser-v31`、`screens` |
| T06 | degraded-path receipts / privacy report | ✅ 落地 | `t06/` |
| T07 | gate report / CI receipt / code-flow receipt | ✅ 落地 | `t07/GATE_FULL.json`、`GATE_QUICK.json` |
| T08 | preview / deployment / rollback identity / probe receipts | ✅ 落地 | `t08/` |
| T09 | `REAL_GOLDEN_TRANSACTION_REPORT.json` | ✅ 落地 | 2026-08-05 按声明格式补出。内容与同目录 `.md` 一致，全部来自生产实读；这是换格式，不是新主张 |
| T09 | same-run receipts / world-state evidence | ✅ 落地 | 同一文件内逐项列出，并由 `t10/` 的验证者复核 |
| T10 | `FROZEN_CANDIDATE.json` / `DURABILITY_RECOVERY_REPORT.json` / `INDEPENDENT_VERIFIER_REPORT.json` | ✅ 落地 | `t10/`，独立验证者四条全 PASS |

## 结论

**15 项落地，3 项补不出来。**

补不出来的三项——`BEFORE_BROWSER_RECEIPT.json`、`LIVE_BASELINE.json`、
`ENVIRONMENT_A0.json`——**是同一个原因：测量窗口已经关闭。**
它们要的都是某个已经不存在的时刻的原子快照：修复前的页面、Stage 0 的环境。
今天能采到的只有今天的状态；把今天的状态标上当时的时间戳就是伪造证据。

**这三项不算完成，也不会被后续工作补上**——除非重新制造那个时刻，而那没有意义。
按任务包「未有真实证据不得标记完成」的规矩记在这里，
而不是在汇报里用「都做完了」一句带过。

T09 原本列在「换形式」，2026-08-05 已按声明的 JSON 格式补出，转为落地。
