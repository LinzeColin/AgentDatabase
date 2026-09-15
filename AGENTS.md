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
---

## 云成本红线：对象存储必须零付费（Owner 硬指令 · 长期有效）

红线全文与事故记录是工作区级规则，真源在 `GithubProject/README.md` **铁律 7**；
本仓独有的**周期任务预算表**、**存储维度实测**和 social-archive 保留策略在
[`文档/r2-成本红线与预算.md`](文档/r2-成本红线与预算.md)。**改任何周期任务的频率、范围或参数之前先读它。**

动手前必须过的四道闸：

1. **不用 `InfrequentAccess` 存储类** —— 建桶、写对象、生命周期转换都不用。免费额度只覆盖 Standard，IA 从第 1 次操作起计费。
2. **不用「整包下载」判断对象存在或做校验。** 判断存在用 `HeadObject` 读 `Metadata.sha256`；逐字节复核按天或按周跑。
3. **新增或改动周期性任务先算月操作量**：`每轮操作数 × 每天轮数 × 31 < 免费额度 × 50%`。算不出来就不上线。
4. **不删这三类参数**：`--fast-list`、`--limit`、`UNCHANGED` / `--skip-if-unchanged`。它们是额度开关，不是性能调优。

存储优先级：**GitHub Release 资产 > R2 > OVH 本地**。新项目与新周期任务默认不写 R2，需 Owner 单独授权加机器守卫证据。
Memory Atlas 每日完整备份固定 `GITHUB_RELEASE_ONLY`，R2 报 `SKIPPED_ZERO_CHARGE` 且 `billable_requests=0`。
canonical 事件超过单个 Release 资产容量时按 Manifest 分片，读取端顺序重组并兼容历史单文件资产。

改完自己核，不交给 Owner 去发现：

```bash
ssh ovh 'sudo /usr/local/bin/linze-r2-free-tier-guard.py'
```

## persona-distiller 实测经验

做 persona-distiller 相关任务时读 [`文档/persona-distiller-实测经验.md`](文档/persona-distiller-实测经验.md)（流水线 + 预筛/收尾两组结论，含为什么与代价）；其余任务不读。

## worktree 落点

规则真源是 `GithubProject/README.md` **铁律 2**：手开 worktree，不要用桌面版自动开的
（`git worktree add ../_scratch/<repo>-<任务名> -b <分支名> origin/main`），自查脚本也在那里。

本仓要额外记住的一条：**桌面版和 Codex 各有一个 `GithubProject/` 外的 worktree 根** ——
桌面版算出来落在 `~/Documents/Codex/<REPO>/`，Codex 落在 `~/.codex/worktrees/`
（2026-08-21 自查实测抓到 `~/.codex/worktrees/521b/MetaDatabase`）。所以自查要定期跑，不是换 agent 时才跑。

## 报路径一律用绝对路径

**结论**：报路径不 sed、不省略、不为对齐截断。界面把相对路径按**会话 cwd** 渲染成可点链接，
而会话 cwd 可能是一棵开在别处的 worktree —— 剥掉前缀就等于把 Owner 指向错误的位置。

**为什么**：2026-08-13 我把运维金库路径剥成 `_protected/ops_vault/...`，Owner 点开落在一棵公开仓工作树里，
据此判我泄漏。文件从头到尾都在正确的 `GithubProject/_protected/` 下，**错的是汇报**。
这类错比内容错更贵：内容错会被判据抓到，坐标错不会 —— 他必须先花时间证伪我，才能继续干活。

**怎么做**：① 凭据 / 备份 / 交付物这三类的位置尤其用绝对路径，报错位置是安全事故级；
② 想让输出好看用表格或缩进，不动路径本身的字符；③ 给别的 agent 指路也只给绝对路径；
④ 自查加一条：我打印的每条路径，从 Owner 的 cwd 出发点开，落在我以为的地方吗？
