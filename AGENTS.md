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

## Kimi Code GUI 前后台生命周期

- **结论**：Kimi Code 外壳不能只保存自己 `spawn()` 返回的 `ChildProcess`；端口已存在时也要核对监听者确为 `~/.kimi-code/bin/kimi`、接管其 PID，并在 `before-quit` 中等待该 PID 退出后再结束 GUI。macOS 下红色关闭键和 `Cmd+W` 只关窗口，`activate` 负责恢复窗口；`Cmd+Q` 才关闭后台并释放端口。设置 `app.setName("Kimi Code")` 后必须把原 `userData` 路径设回去，否则登录与会话会表现成全新安装。
  **为什么**：旧实现检测到端口已开就直接返回，`serverProc` 仍是 `null`，因此 GUI 重启后复用的是失联后台，之后 `Cmd+Q` 永远回收不了它。应用名称更正又会让 Electron 默认资料目录从 `kimi-shell` 漂到 `Kimi Code`。
  **代价**：修复前会出现 GUI 已退出但 CLI/端口仍驻留、前后台权限主体错位，以及改菜单名后会话“消失”的假回归。完全磁盘访问需同时授权 GUI bundle `com.electron.kimi-code` 与实际 CLI 路径，并完整退出重开后生效。

## 「已完成」的判据必须是读回校验，不能是脚本返回成功（2026-08-23 · 代价 $4.51）

**结论**：`~/.harness-ui/harness_service.py`（launchd `com.harnessui.assets`，每 900 秒一轮）
把 SMB 当真源往本地 `master/` 反向回填，判据是 `source.st_size != dest.st_size or source 更新`。
**「尺寸不同」就回填** —— 而重出的图尺寸必然和旧图不同，于是 `regen.py` 刚写的 25 张返工新图
在下一个周期被 `shutil.copy2` 用 SMB 的旧版盖回，`copy2` 连源 mtime 一起还原，
**文件看上去根本没被动过**。已据此向用户报过「13/13 完成」，是假的。

**为什么没被抓到**：SMB 静默写 0 那次（§10）写的是 0，`audit.py empty` 抓得到；
这次写的是**一模一样的旧内容**，任何非空/非零/尺寸校验都通过。
连"归档后比对 master↔NAS 摘要一致"也通过 —— 因为两边都已经是旧内容。
唯一抓得到的判据是**和 `.rejected-N.png` 比 md5**，以及 `stat -f %SB`（birth）与 mtime 打架：
新图 birth 08-23 21:47、mtime 却是 08-21，两个不同 inode 同 mtime 同内容 = 保留时间戳的拷贝，不是 rename。

**代价**：$4.51 的 25 张图全销毁，且带着"已完成"的结论进了交接单，差点被下游按可发排期。

**怎么办**：
1. `copy_required` 已加前置 `if dest.st_mtime_ns > source.st_mtime_ns: return False`（本地更新绝不回填）。
   备份 `harness_service.py.bak-20260823-*`，改完必须 `launchctl kickstart -k gui/$(id -u)/com.harnessui.assets`，
   **不重启等于没改**（跑着的进程还是旧代码）。
2. 任何"生成→落盘"的产线，收尾判据一律改成**隔一个同步周期后回读比对**，
   而不是"脚本 print 了 ✓"。有 `.rejected` 留底的，直接和留底比 md5。
3. 本机多条 Claude 会话并发跑同一个库。动 `catalog.json` / `private_only.json` 前先 `stat` 修改时间。

## 素材复核页/总览页禁止写死 `http://127.0.0.1:PORT`（2026-08-23）

**结论**：`review.html` 与 `qa/index.html` 曾把 828 / 1656 条图片地址写成
`http://127.0.0.1:3099/...`。素材服务不跑时用户双击打开就是整页碎图，连续两次被反馈"打不开"。
**改成相对路径**（页面与 `crops/`、`thumb/`、`display/` 同级），零 `fetch`/XHR，`file://` 直接能开。

**为什么**：这类页是给人看的一次性交付物，不该带运行时依赖。
生成器 `tools/build_gallery.py` 已把"所有地址必须相对 + 逐条核文件存在"写成硬校验，缺一个就报错不出页。

**附带**：背板是 3840×2160、人物贴在一侧，缩略图用 `object-fit:cover` 居中裁**只剩天空**，
414 张分不清谁是谁。缩略图必须用 `qa/crops/` 的人物特写（460×616），灯箱再看整张背板。

## 本地 SDXL 出图产线：跑通了什么、卡在哪（2026-08-24 · 代价约 2.5 小时 GPU）

**动机**：托管 API 成本远超收益 —— 414 个变体已花 $25+，且高档位配方实测 **67/110 被远端策略拒绝**、
单变体成本 $0.34（被拒也计费）。

**本机已有的底子**（`~/ComfyUI-Installs/ComfyUI/ComfyUI`）：
`waiIllustriousSDXL_v170`（danbooru 训练、认角色 tag）+ 27 个角色 LoRA +
ControlNet depth + IP-Adapter plus + CLIP-ViT-H + 4x-UltraSharp + RealESRGAN_x4plus_anime_6B +
MeshGraphormer（手部修复）+ 全套 inpaint 节点。

### 已证明
| 维度 | 结论 |
|---|---|
| 画质 | **够**。单张实测：服装口径全中、构图锁左三分之一、手部正确、体型比例未被扭曲 |
| 成本 | **$0** |
| 内容策略 | 本地模型无远端内容策略拦截，产线里那套「被拒→降档重试」的阶梯**在本地可以整个删掉**（具体档位口径不在本仓，见 04_DouyinOps） |
| 只修手 | **能**。MeshGraphormer 框手 + inpaint，其余像素不动 —— gpt-image-2 做不到（无 mask），13 张缺陷里 10 张是手 |

### 未解决（不解决就不能切）
1. **人物辨识度**。有专属 LoRA 的芙宁娜都丢了帽子和标志配色，踩 pipeline「严格不能偏离基准人物特征」。
   **27 个 LoRA 只覆盖 33/414 变体（8%）**，其余 92% 无 LoRA。
2. **IP-Adapter 救不回来，反而更差**（详见下节），用户两张全否。
3. **LoRA 采购路径不通**：Civitai 返回 **451 REGION_BLOCKED**，需另找源。
4. **吞吐**。单张 **555 秒**（gpt-image-2 是 30–60 秒且可并发）。414 变体全量 ≈ **64 小时**连续占机。
5. **远端策略这道兜底消失**。那 67 次拒绝实际替产线挡下了 67 张超出发布口径的素材；
   切到本地后，合规判定 100% 落在自己的闸门上（口径见 04_DouyinOps，不在本仓）。

### IP-Adapter 是错的工具，别再试第二遍
`IPAdapterAdvanced` weight 0.7 / end_at 0.75 / concat / V only，两种失败模式：
- **画面长出两个人**：`ConditioningSetArea` 只约束**文字条件**在左 512px，
  而 **IP-Adapter 全图生效** —— 它在整幅画上都想要人物。多出来那个还穿了完全不同的服装，服装口径作废。
- **渲染扁平劣质**：锚图的平面立绘风格被一起搬进来。

**不加锚图、只用 LoRA 的那张画质更好。** 锁身份的正解是角色 LoRA，不是 IP-Adapter。

### 环境坑（会直接烧掉几小时）
- **`--bf16-unet` 让 SDXL 在 Apple MPS 上算出 NaN**，产纯色图但 ComfyUI 仍报 `success`。
  同一张最小图：bf16 → 3KB 纯灰；fp16 → 1133KB 真图。日志证据是
  `RuntimeWarning: invalid value encountered in cast`（NaN 转 uint8）。
  **用共享实例前先 `ps -o command=` 看精度参数。**
- **判废判据**：3840×2160 的 PNG 只有 ~27KB，或缩到 64px 后 <1200 字节 = 纯色废图。
- **ComfyUI 的 queue/history 是内存态，重启即全清。** 2026-08-24 一小时内被别的线程重启三次，
  T04 排的队两次整队蒸发、**一秒 GPU 都没拿到**。判「产物在不在」**一律扫盘，不看 history**。
- **同一配方连败 2 次就停手做最小复现**，不要换 seed 重试。我掷了 6 次骰子 ≈ 两小时，
  最小复现两分钟定死根因。守护进程会一边帮你重试一边掩盖问题，**诊断前先停它**。
- macOS **没有 `setsid`**，后台起服务用 `nohup ... &`。

### 复现入口
对照页生成器与实验脚本在会话 scratchpad（`bench/run.py` / `run_ipa.py` / `page.py` / `supervise.py`），
产物对照页 `~/Downloads/本地出图对照-260824/对照.html`（三栏：gpt-image-2 / 本地无锚图 / 本地+锚图）。
