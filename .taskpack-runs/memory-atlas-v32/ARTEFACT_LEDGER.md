# v0.0.0.32 — 声明产物逐条对账

任务包规定「未有真实证据不得标记完成」。这份台账逐条列出 DAG 声明的每个产物：
**落地了 / 换了形式落地 / 现在补不出来**，后两类写明原因。
不合并、不含糊，因为「记录在别处」和「没有记录」在汇报里长得一样。

| 任务 | 声明产物 | 状态 | 说明 |
|---|---|---|---|
| T00 | `SEMANTIC_RECONCILIATION.json` | ✅ 落地 | `.taskpack-runs/memory-atlas-v32/` |
| T00 | `LIVE_BASELINE.json` | ⚠️ 换形式 | Stage 0 的治理／代码／Hook／Automation／OVH／Cloudflare／PDB／R2／API／站点事实记在 `T00_CLASSIFICATION.md` 的散文与表格里，没有另出 JSON |
| T00 | `ENVIRONMENT_A0.json` | ⚠️ 换形式 | 同上；环境事实分散在 `T00_CLASSIFICATION.md` 与 `t08/T08_RECORD.md` |
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
| T09 | `REAL_GOLDEN_TRANSACTION_REPORT.json` | ⚠️ 换形式 | 写成了 `.md`（内容完整，含 2026-08-04 发布身份闭环的追加） |
| T09 | same-run receipts / world-state evidence | ✅ 落地 | 同一文件内逐项列出，并由 `t10/` 的验证者复核 |
| T10 | `FROZEN_CANDIDATE.json` / `DURABILITY_RECOVERY_REPORT.json` / `INDEPENDENT_VERIFIER_REPORT.json` | ✅ 落地 | `t10/`，独立验证者四条全 PASS |

## 结论

**14 项落地，3 项换了形式落地，1 项补不出来。**

补不出来的那一项（`BEFORE_BROWSER_RECEIPT.json`）是时间性的：证据窗口已经关闭。
换形式的三项内容都在，只是没有按声明的文件名和格式单独出一份。

这两类都**不算「已完成」**，按任务包的规矩如实标注在这里，
而不是在汇报里用「都做完了」一句带过。
