# AgentDatabase Agent Contract

## P0 repository boundary

This checkout is the sole canonical `LinzeColin/AgentDatabase` repository.
Its active product scopes are `OpenAIDatabase/`, top-level `MemoryAtlas/`, and
`CodexSkills/`.
Do not restore projects migrated to other repositories, the retired root
governance tree, a second OpenAIDatabase fact source, private core, credentials,
session material, `data/raw_archives/**`, or historical large archives.

The canonical branch is `main`. Use ordinary commits and fast-forward-safe
pushes only after the active task gates pass. Do not create a temporary remote
branch or pull request, and never reset, rebase, merge, force-push, or rewrite
history as a migration shortcut.

## 数据落地铁律（长期有效 · 自运行分仓治理）

长期/业务/运行时数据一律写私有仓 `LinzeColin/Private-Database`（Agent 会话/记忆 → `Private-AgentDatabase/`；
其余按仓分区），用 `private_db_client.py` 免 clone 读写（`ingest/get/list/verify`）；**禁止把数据提交进本代码仓**，
派生/临时/可再生产物走 `.gitignore`。目的：分仓治理长期自运行，不需人工反复迁移。

⛔ **唯一尚未闭环的缺口**：`OpenAIDatabase/data/` 仍是活运行记忆、尚未迁走。
接手 OpenAIDatabase 前必读 [`OpenAIDatabase/MIGRATION_MANDATE.md`](OpenAIDatabase/MIGRATION_MANDATE.md)——那是一项**必须完成**的迁移，但在启动/CI 完成 SDK cutover 前**不得删除**本地 `data/`。

## OpenAIDatabase routing

Read `OpenAIDatabase/AGENTS.md` before changing OpenAIDatabase. Start task
routing with:

```bash
python3 -B OpenAIDatabase/scripts/route_agent_resources.py \
  --database-dir OpenAIDatabase --intent startup
```

The generated memory discovery object is
`OpenAIDatabase/data/memory/agent-memory.json`. Follow its indexed paths only
when task-relevant; do not recursively scan raw or private data.

## Migration recovery

The S04-S13 preservation package under
`OpenAIDatabase/docs/migration_handoff/20260717_local_s04_s13_preservation/`
is evidence, not an integrated tree. Reconcile patches in order, preserve the
post-split architecture, and require material coverage loss to be zero before
starting S14. Rebuild generated views from current canonical facts; do not copy
old generated views.

One meaningful run may complete at most one product Phase. Unknown remote,
App, live, authorization, readiness, or data-freshness facts remain UNKNOWN or
FAILED until directly reverified.

---

## 云成本红线：对象存储必须零付费（Owner 硬指令 · 长期有效）

**云端账单必须恒为 $0.00。不允许任何 agent 触发收费行为。**

1. **禁止 `InfrequentAccess` 存储类** —— 建桶、写对象、生命周期转换，一律不许。
   R2 的免费额度（10GB 存储 / 100 万 Class A / 1000 万 Class B）**只覆盖 Standard**；
   IA 从第 1 次操作起计费，且**按整计费单位向上取整**。
   2026-08-07 实账单：**51 次 IA 操作 = $9.00**，同期 **301 万次 Standard 操作 = $0.00**。
   根因是建桶时默认存储类选了 IA，写入端不指定存储类就全部继承 —— 一次手滑，之后静默自动计费。
2. **禁止"整包下载来判断存在 / 做校验"的高频轮询。** 判断对象存在用 `HeadObject`
   （写入时把 sha256 放进对象 `Metadata`，Head 就读得到）；真要逐字节复核，
   **按天或按周跑，不许按分钟跑**。
   反例：memory-atlas reconcile 每 15 分钟把 2466 个对象整包拉一遍核 sha256，
   折合 71 万次 Class B/天、21.3M/月，直接打穿 10M/月免费额度。
3. **新增或改动任何周期性任务，先算月操作量**：
   `每轮操作数 × 每天轮数 × 31 < 免费额度 × 50%`。**算不出来就不上线。**
4. **存储优先级**：**GitHub Release 资产 > R2 > OVH 本地**。
   Release 资产不计仓库体积、没有操作计费，永远优先。

完整事故记录、账单逐行归因、免费额度速查表 → **`Private-Database` 仓 `OPS/AGENT_ONBOARDING.md` §9.7**。
机器守卫 → OVH `/usr/local/bin/linze-r2-free-tier-guard.py`（每 6 小时，非 Standard 桶自动熔断改回；
判定 `/srv/linze/apps/status/data/r2_free_tier_guard.json`）。
