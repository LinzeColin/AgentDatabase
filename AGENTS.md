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
