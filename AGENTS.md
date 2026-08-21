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
5. **新项目与新周期任务默认不得写 R2。** 默认使用 GitHub Release 或既有本地/私有仓通道；
   只有 Owner 单独授权、机器守卫同一计费周期直接证明全部 Bucket 默认 `Standard`、无非 Standard
   对象，并且最坏情况月操作量与新增存储都低于免费额度 40% 时，才可提出启用 R2。证据缺失、
   status 过期或任一指标达到 40% 时必须 fail-closed 跳过 R2，不得把“备份成功”与“R2 必须写入”绑定。
6. **Memory Atlas 每日完整备份固定为 `GITHUB_RELEASE_ONLY`。** 原始来源进入 age 加密私有
   Release，canonical 事件进入私有 Release；两者都必须远端读回，原始来源还必须隔离恢复。
   Schedule 中 R2 必须报告 `SKIPPED_ZERO_CHARGE` 且 `billable_requests=0`。未经 Owner 新授权不得改回。

完整事故记录、账单逐行归因、免费额度速查表 → **`Private-Database` 仓 `OPS/AGENT_ONBOARDING.md` §9.7**。
机器守卫 → OVH `/usr/local/bin/linze-r2-free-tier-guard.py`（每 6 小时，非 Standard 桶自动熔断改回；
判定 `/srv/linze/apps/status/data/r2_free_tier_guard.json`）。

### R2 周期任务清单与预算（改动前必读）

云端账单恒为 $0.00，靠的是下面这份预算不被打破。**改这些任务的频率、范围或参数之前，先算月操作量。**
数字为 2026-08-07 实测（Cloudflare GraphQL `r2OperationsAdaptiveGroups`，7 个完整日日均外推）。

| 任务 | 频率 | 桶 | 作用 | 月 Class A | 月 Class B | **一碰就变收费的地方** |
|---|---|---|---|---|---|---|
| `weread-port-r2-oci-backup` | 每日 04:23 | weread-port-private | 加密用户对象镜像到 OCI 异地冷备 | 465 | 0 | **`rclone sync` 必须带 `--fast-list`**。删掉它 → 按前缀逐个列举，实测 15 次 → **9,300 次**（Class A 额度的 28.8%），且随对象数线性增长 |
| `memory-atlas-reconcile` | **每日** | weread-port-private | 核对 R2 是否仍持有 manifest 里的字节 | 434 | **229,338 (2.3%)** | **频率**。原为每 15 分钟 = 21.3M/月，直接打穿 10M 额度。因为 `exists_with_hash()` 对每个对象**整包下载**（2 Head + 1 Get × 2466 对象 = 7,398/轮） |
| `linze-status-r2-mirror.sh` | 每 5 分钟 | primary-objects | status 站数据镜像 | 31,872 (3.2%) | ~200 | **镜像的文件个数**。每多镜像 1 个文件 = +8,928 次/月 |
| weread-port 平台写入（常驻） | 持续 ~56 次/小时 | weread-port-private | 加密笔记 / 跨设备同步的对象写入 | 41,664 (4.2%) | 0 | 随用户活跃度增长。**写入方未逐一归因**，但已确认不是 reconcile（降频后仍在） |
| `social-archive-replication` | 每 15 分钟 | social-archive-e2n-v0004 | 对象复制到多存储 | 3,224 | 19,468 | **`--limit 200` 这个上限**，别放大 |
| `weread-port-private-database-backup` | 每日 04:01 | backups | Private-Database git bundle 冷备 | 190 | ~30 | 有 `UNCHANGED` 短路，**别去掉** |
| `linze-offsite-backup.sh` | 每日 03:40 | backups | 全量加密备份（单对象） | ~60 | ~30 | 别改成分片小块上传 |
| `cyberboss-backup` | 每日 03:35 | cyberboss-cold | CyberBoss 冷备 | 35 | ~150 | — |
| `memory-atlas-action-worker` | 每分钟 | weread-port-private | 有界 owner 动作队列 | ~0 | ~0 | 队列空时不发任何 R2 请求；**队列一旦长期非空，就会变成每分钟打 R2** |
| 其余（adp / sl-* / kmfa / status-evidence） | 每日 | 各自 | 各项目产物 | <900 | <100 | — |
| **合计** | | | | **≈ 8.0% 的 100 万/月** | **≈ 2.5% 的 1000 万/月** | |

**余量**：Class B 有 **40 倍**余量；Class A 有 **12 倍**余量。两者都健康，但 **Class A 历来是先见底的那个**
（修 `--fast-list` 之前它已经到 37%，而 Class B 只有 2.5%）—— 盯额度先盯 Class A。

**改动这些任务时的三条硬规则**

1. **别删这三类参数** —— 它们是额度的直接开关，不是性能调优：
   `--fast-list`（rclone 列举方式）、`--limit`（单轮上限）、`UNCHANGED` / `--skip-if-unchanged`（无变化短路）。
2. **别把日级任务改成分钟级。** 先算：`每轮操作数 × 每天轮数 × 31 < 免费额度 × 50%`。**算不出来就不上线。**
3. **别用"整包下载"判断对象存在或做校验。** 判断存在用 `HeadObject` 读 `Metadata.sha256`；
   逐字节复核按天/周跑，不许按分钟跑。（`exists_with_hash()` 就是反例，它是这次事故的第二个根因。）

**改完自己核**（不要交给 owner 去发现）：

```bash
ssh ovh 'sudo /usr/local/bin/linze-r2-free-tier-guard.py'
```

它会打印本计费周期 Class A / Class B / 存储对免费额度的投影占比，≥40% 报 WARN、≥50% 报 CRIT，
并把判定写进每日复审清单。完整事故记录见 `Private-Database` 仓 `OPS/AGENT_ONBOARDING.md` §9.7。

**存储维度（唯一跨月累积的）**：操作次数每计费周期清零，**存储不清零**。2026-08-10 实测 **4.55 GB / 10 GB = 44.4%**。

| 桶 | 当前 | 状态 |
|---|---|---|
| `weread-port-private` | 3.22 GB | 冻结（memory-atlas 迁出后不再增长） |
| `backups` | 0.96 GB | 冻结（`linze-offsite-backup.sh` 的 R2 写入已停用：`R2_CODE=disabled_zero_charge_policy`） |
| `social-archive-e2n-v0004` | 0.31 GB | **3 天保留封顶**（见下） |
| 其余 7 个桶 | 合计 <0.06 GB | 冻结 |

**social-archive 的 3 天保留（Owner 2026-08-10 定）**

`backups/runtime-db/` 每 15 分钟写一份 1.03 MB 加密快照，而 `prune_runtime_db_snapshots.py`
**只清本地**——它的文件头明确写着「不碰远端副本(R2/OCI/GitHub)，保留期是另一个决定」，
那个决定一直没给，于是 R2 上累积了 **512 份 / 521 MB、+99 MB/天**，是当时账号里唯一还在长的东西。

现由 `social-archive/scripts/prune_r2_backup_replicas.py --apply` 承接（挂在
`social-archive-backup.service`，每日 03:20），保留 **72 小时**，稳态约 290 MB。首次执行删了 258 个 / 234 MB。

> **改动禁区**：① 别删那条 `ExecStart`，② 别把 `--apply` 拿掉，③ 别放宽 `--hours`。
> 脚本的安全底线也别削：**删 R2 对象前先 `HeadObject` 核对 OCI 上同 key 同大小，核不上就跳过不删**；
> 最新一批永远保留；只碰 `backups/<组>/<时间戳>/`，**不碰 `primary-objects/`（那是制品字节，删了就是毁档）**。
> 每份快照有 `r2`/`oci`/`github` 三个 verified 副本，删掉 R2 那份仍剩两份 —— 这是「卸载」不是「删除」。

---

## persona-distiller 流水线经验（2026-08-21 Telford#37 实测，供 T1/T2/T3 共用）

- **结论**：模型文档里引文坐标必须写成 `（src-XXX，YYYY 年）`，裸 `（src-XXX）` 不算坐标。
  **为什么**：check_quote_locator 的 LOCATOR 只认同段内的年份/页码/刊名/@偏移，不含 source_id；
  10 份产物一次性扫出 65 条缺坐标，release 被拦。**代价**：65 条 × 8 文件逐条返工（约 1 段）。
- **结论**：claims 层无排除机制——OCR 拼写变体（如 Pontcysyllte→Pontycysyllte）时，claim 文本必须
  用语料拼写；答案/产物可留标准拼写，但要在 `raw/_EXCLUDED.txt` 记录（二手依据，脱「无依据」）。
  **为什么**：check_claim_coverage 只看语料正文+台账，不读排除表；check_unsourced_names 读 raw/ 下
  `_` 前缀 .txt。**代价**：两个名字各一次拦门 + 一轮排查。
- **结论**：盲判载荷构建用 `--balanced-positions`（默认 sha256%2 可能偏，Telford 抽到 21/11）。
  **为什么**：位次与系统相关会灌进 delta（Holmes#170 实测位次效应 +0.015~+0.027）。重建只重排
  A/B 标签、不重生成答案，便宜。**代价**：重排后 judge 输入须重建（几行脚本）。
- **结论**：release 门扫 `evals/judge_payload.v1.json`（候选侧），不扫 A/B 盲判载荷——baseline 侧
  引文缺坐标不阻塞 release；基线 provenance warning 用 `package_target.py --acknowledge-disclosure
  '<warning 原文子串>'` 具名承认，不是 error，不打回。**为什么**：裸模型基线本来就是「非能力证据」，
  门拦的是冒充，不是发布。**代价**：0（按标准流程走）。
- **结论**：case-known 类题有意测 holdout 记忆，rubric 里会要求 holdout 细节（如 "Appendices 7-13"）；
  这类源标题词会穿过 holdout 泄漏门（非独有专名/数字）但被 unsourced-name 门抓——答案必须靠
  `_EXCLUDED.txt` 记录兜底，别去改答案。**为什么**：holdout 密封源正文不在 raw/，checker 查不到属预期。
  **代价**：Telford case-known-2 一次拦门。

## worktree 位置：桌面版**没有**「Worktree location」这个设置（2026-08-13 实测，Claude Code 2.1.212）

**结论**：`GithubProject/README.md` 里长期写着「桌面版可在 Settings → Claude Code → Worktree location
指到 `~/Documents/Codex/GithubProject/_scratch/`」—— **那个设置不存在**。二进制里 0 处该文案；
`~/.claude.json`、`~/.claude/settings.json`、桌面版 `claude_desktop_config.json` 里都没有对应键；
搜「值为 `~/Documents/Codex` 的配置项」也是 0 处。这条是当初某个 agent **猜的**。

真实规则是**算出来的**：worktree 固定落在 `<仓的祖父目录>/<仓名>/<worktree名>`。
所以根指到 `GithubProject/AgentDatabase` 时，worktree 落在 `~/Documents/Codex/AgentDatabase/<名字>`，
**在 `GithubProject/` 外面，违反铁律 2**。证据在桌面版自己的登记表
`~/Library/Application Support/Claude/git-worktrees.json` 的 `untrackedDirGc.roots`，
明写着 `~/Documents/Codex/AgentDatabase` 和 `~/Documents/Codex/MetaDatabase` 两个根。

**代价**：这条铁律从写下那天起就不可执行，而后来每个 agent（包括我）都把它当「Owner 定的规矩」引用，
**谁也没去点开看一眼**。我还差点把「你去 Settings 改」当成 Owner 的待办交回去 ——
要他去改的那个东西本来就是 agent 写错的，交回去等于让他替我们的错买单。

**怎么办**（README 已改成这两条）：
① **手开 worktree，别用桌面版自动的** —— 在主树跑 `git worktree add ../_scratch/<repo>-<任务名> -b <分支> origin/main`。
本机 MetaDatabase 的 worktree 全在 `_scratch/` 下就是因为都是手开的，**这条一直有效，只是从没被写下来**。
② 已被自动开在外面的照常能用，但**收尾要多确认一步** `~/Documents/Codex/<REPO>/` 空了 ——
否则会留下 `git worktree list` 里都没有的空壳目录（2026-08-10 留下过一个，里面躺着一份文件）。

**自查**（已验四个方向：主树不报、`_scratch/` 下不报、`NotGithubProject/` 下报、别处报）：

```bash
ROOT=$(cd ~/Documents/Codex/GithubProject && pwd -P)   # 必须 pwd -P 取真实路径
for r in "$ROOT"/*/; do
  [ -d "$r/.git" ] || continue
  git -C "$r" worktree list --porcelain 2>/dev/null | awk -v ROOT="$ROOT/" -v R="$(basename "$r")" \
    '/^worktree /{p=substr($0,10); if (index(p, ROOT) != 1) print "✗ " R ": " p}'
done
```

> 这条命令的两个坑都是造夹具才炸出来的，**别改回去**：
> ① `!~ /GithubProject/` 是**子串**匹配，会放过 `/x/NotGithubProject/y`，也会把主树自己误报；必须 `index(p,ROOT)!=1` 做前缀。
> ② `ROOT` 不 `pwd -P` 的话，在有软链的环境（macOS `/tmp`→`/private/tmp`）**100% 全报** ——
> `git worktree list` 返回的是解析过软链的路径。本机 `~/Documents/` 没软链所以碰巧不发作，**换台机器就炸**。
>
> **不止桌面版会这样**：2026-08-21 跑这条自查抓到
> `/Users/linzezhang/.codex/worktrees/521b/MetaDatabase` —— **Codex 把 worktree 放在 `~/.codex/worktrees/`**，
> 又是另一个 `GithubProject/` 外的根。所以这条自查要**定期跑**，别只在换 agent 时想起来。

## 报路径一律用绝对路径 —— 剥前缀等于报错位置

**结论**：交付运维金库时我为了好看用 `sed 's|.*/GithubProject/|  |'` 把前缀剥掉，打印成
`_protected/ops_vault/LINZE_OPS_VAULT_20260813.tar.gz`。界面把相对路径按**会话 cwd** 渲染成可点链接，
而那个会话的 cwd 恰好是一棵开在错位置的 worktree —— **Owner 点开看到的是一条指向公开仓工作树的凭据路径，据此判我泄漏**。

文件从头到尾都在正确的 `GithubProject/_protected/` 下（`find` 全盘只有 3 处，全对）。**错的是我的汇报。**

**代价**：他必须先花时间**证伪我**，才能继续干活。这类错比内容错更贵 —— 内容错会被判据抓到，坐标错不会。

**规矩**：① 报路径一律绝对路径，不 sed、不省略、不为对齐截断；
② **凭据 / 备份 / 交付物**这三类的位置尤其如此，报错位置是安全事故级的；
③ 想让输出好看就用表格或缩进，**不要动路径本身的字符**；
④ 自查加一条：**我打印的每条路径，从 Owner 的 cwd 出发点开，落在我以为的地方吗？**

> 同一个错第二天在别人身上复现：Codex 报「`_protected` 里没东西」，因为它在
> `_scratch/metadatabase-abd-v0001-s11-p01/` 里找相对路径 —— **`_protected/` 在 `GithubProject/` 根下，往上两级**。
> 给别的 agent 指路时也只给绝对路径。
