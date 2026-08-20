---
name: kmmedia-archive
description: "钉钉媒体归档与 KMVideo 管理流水线。"
---

# KMMedia-Archive（KMVideo 一体化流水线）

> 版本 v0.3.1（260820）。素材库任务书 v0.0.2.0 的完整执行体。
> v0.3.1 三处运维修复：SMB 挂载点动态解析（盘换挂后 skill 起不来）、单窗口失败不再中断整轮（一个坏件曾毁掉当轮全部剩余窗口）、SMB 写后 stat 延迟沉降 2 次→4 次带退避。
> v0.3.0 按 260818 全量实跑的 12 条问题记录迭代：audit 认改名账本（误报归零）、
> 动态群名单、增量起点直读 manifest、manifest 写入保护、永久错误不堵窗口、
> dws 绝对路径、并发锁、SMB 健康自检。
> 上级规则：`smb://192.168.0.1/share/03_资料库/MetaData/IDS_MetaData/KMVideo/README.md`（冲突以 README 为准）。

## 一句话

从钉钉群到交付：**全量扫描 → 增量归档 → 规格探测 → 哈希去重 → 缩略图 → 本地标注 → 幂等改名 → 登记表双格式 → 三处落地（SMB / GitHub / KMOS 公开仓 / Private-Database）→ 自验收 → 产能汇总**，一条命令全跑，全程不调用任何外部 agent。

## 硬约束（违反任一条即停止）

1. 原始素材区只读；输入源不得删除、覆盖未知既有文件。
2. `.manifest.jsonl` 任何情况下不得修改。
3. 群目录只允许 `photo/`、`video/`、`.manifest.jsonl` 三样。
4. 原始素材不得写入 KMOS 公开仓；KMOS 只放源码、Skill、脱敏登记表、缩略图清单。
5. 长期业务数据走 `LinzeColin/Private-Database` 的 `Private-KMDatabase/`，经 `private_db_client.py`，禁止 clone 私有仓。
6. 云成本红线：禁止 `InfrequentAccess`；禁止整包下载做存在性校验。
7. SMB 写入禁用 Python 写与 `shutil.copyfile` 快速路径；用 `rsync --inplace --whole-file` 或 `/bin/dd conv=fsync`，写后必须校验字节数。
8. 日期一律 `YYMMDD`；公开仓禁用客户全称，项目名一律泛化为「业务名+群」（如 `安装检修群`）。
9. 不得新建平行登记表；所有标注写进根目录 `素材登记表.csv`，以新增列扩展。
10. 以 `[文件]` 形式发送的音视频也归本 skill（v0.2.1 新增）。钉钉里同一段视频可能走两种传输：
    `[视频消息](mediaId=...)` 走 `dws chat message download-media`，
    `[文件] xxx.mp4 fileId: ...` 走 `dws drive download --node`。
    v0.2.0 只认前者，实测 90 天内漏采 37 个 mp4。按扩展名与 `KMFile-Archive` 分流：
    音视频/图片扩展名归 KMVideo，文档扩展名归 KMFile，不重不漏。
11. **不得调用任何外部 agent**（Claude Code CLI / Codex CLI / 其他 CLI agent / 远程视觉服务）。多模态问题一律本地自解：
    - 语义标注 ← **DWS 消息上下文**（媒体消息前后 30 分钟内的文本消息，关键词映射）
    - 精确地理位置 ← **EXIF GPS**（PIL 读 EXIF）
    - 画质等级 ← **ffprobe 分辨率**（短边 ≥720 可全屏，否则仅可内嵌）
    - 重复检测 ← **感知哈希 aHash**（PIL）
    - OCR/人脸（可选增强）：本机安装 tesseract / opencv 时自动启用，未安装则跳过

## 执行方式

```bash
python3 scripts/kmvideo_pipeline.py all --groups-file <白名单.txt> [--workdir /tmp/kmvideo_work/pipeline]
```

单阶段可独立重跑（幂等）：`scan|probe|dedup|thumbs|label|rename|registry|upload|accept|report`。

- `--allow-title` 白名单逐群显式传入（复用 archive_internal_media 的全部归档语义与去重规则）。
- `--only-group 群名` 可先打样单群；`--skip-accept-upload` 可只跑本地阶段。
- 私有仓落地依赖 `KMOS_ROOT` 环境变量（或运行于 KMOS worktree 内）定位 `private_db_client.py`；
  两者都失效时 `upload` 阶段**报错退出**（不再静默跳过）。显式跳过私有仓用 `--no-private`。
- 视觉字段若存在更高置信度的外部标注（如任务书打样产物），`label` 阶段以 `workdir/vision_override.jsonl`（键=文件名，值=字段）优先。

### v0.3.0 / v0.0.0.2 新增开关

| 开关 | 作用 | 什么时候用 |
|---|---|---|
| `--since-manifest` | 每群起点改为该群 manifest 最后一个 complete 窗口的终点 | 日常增量。全量 audit 从 2025-01-01 遍历极慢（媒体侧 27 群约 50 分钟），增量只扫新窗口 |
| `--refresh-groups` | 跑前用 dws 实时枚举群列表，与 `--groups-file` 求并集 | 静态白名单会漏群（实测旧名单 26、实时 30）。**新增群只报不收** |
| `--include-new-groups` | 与上一条连用，把新发现的群纳入本轮 | Owner 确认要收之后 |
| `--skip-smb-check` | 跳过开跑前的 SMB 健康自检 | 明知挂载正常、想省 1 秒时 |

新增群清单写在 `workdir/新增群待确认.txt`，同时列进产能汇总。
Owner 已明确说过「不管」的群（台泥(贵港)、生产付款群、生产周例会工作群）写在
脚本的 `DECLINED_TITLES` 里，归入「已排除」而不是「新增待确认」，不会每轮重复问。

## 阶段说明

| 阶段 | 子命令 | 产出 |
|---|---|---|
| 一 扫描+增量归档 | `scan` | manifest 增量（复读不改）、`workdir/context.jsonl` 消息上下文 |
| 二 规格探测/去重/缩略图 | `probe` `dedup` `thumbs` | `specs.jsonl`、`dups.jsonl`、`workdir/thumbs/*.jpg`、SMB `KMVideo_缩略图/` |
| 三 本地标注 | `label` | `desc.csv`（描述/功能位/画质等级/画面元素/镜头特征/工序阶段/能证明什么/脱敏风险/置信度） |
| 四 改名 | `rename` | 磁盘幂等改名 + `改名前后对照.csv` |
| 五 登记与落地 | `registry` `upload` | `素材登记表.csv`（+18 新列）、`原名新名映射.csv`、视频子集、三处本机分发、公开仓、私有仓 ingest、GitHub Release 资产 |

### 登记表落点（三个本机 + 一个 GitHub）

| # | 位置 | 内容 | 性质 |
|---|---|---|---|
| 1 | `smb://192.168.0.1/.../IDS_MetaData/KMVideo/` | `素材登记表.csv`、`原名新名映射.csv` | **唯一真源**，`rsync` 写入并校验字节数 |
| 2 | `~/Documents/KMVideo/00_治理与登记/02_登记与索引/` | 全量表、映射表、视频子集、公开脱敏版 csv/md | 输出工作区副本 |
| 3 | `~/Downloads/` | `KMVideo素材登记表.csv`、`KMVideo素材登记表_视频子集.csv` | 便于拖给 ChatGPT 上传 |
| 4 | KMOS 公开仓 `KMDatabase/data/KMVideo/` | **仅脱敏版**：`素材登记表_public.csv/md`、`素材登记表_视频子集_public.csv`、缩略图清单 | 公开，项目名一律泛化为「业务名+群」，且去掉「能证明什么」列 |

- 分发由 `distribute_registry()` 完成，逐份校验字节数；**任一处写失败即抛错中止，不得静默跳过**——本机副本过期会让下游 agent 读到错数据。
- `素材登记表_视频子集.csv` 只含视频、精简为 14 列，体积约 40 KB，供无本地文件权限的模型（ChatGPT 等）直接上传使用。
- 进 KMOS 公开仓的**只能是 `_public` 后缀那几份**；含真实甲方群名与「能证明什么」的版本不得公开。
| 六 自验收+汇总 | `accept` `report` | `accept_report.json`、产能汇总表 |

## 命名规则（照抄任务书）

`{业务}_{说明}_{YYMMDD}_{序号}.ext`
- 视频：序号沿用原文件名两位序号（任务书示例语义，天然幂等）
- 照片：同（业务,说明,日期,类型）内递增两位
- 业务映射表（内置 BUSINESS 常量，任务书照抄）：
  内部 / 焊接 / 安装检修 / 化工钢铁 / 化工 / 水泥调测窑 / 水泥

## 自验收判据（accept 阶段自动执行）

- 目标行齐全无重复；文件名格式与业务映射正确；说明 2–6 字
- 枚举字段全部使用原始词汇表
- 画质等级与分辨率一致；`.manifest.jsonl` mtime 未变
- 改名幂等：连跑两次第二次零变更
- 三处落地校验：SMB 写后字节数相等；公开仓含脱敏版；私有仓 ingest 成功

## 每日增量：怎么设 cron（v0.3.1 / v0.0.0.3 起）

**先看两个实测数字**（260814–260820，31 群）：

| | 数值 |
|---|---|
| 新增速率 | **155 件/天**（照片 1016 / 文件 40 / 视频 31，7 天 1087 件） |
| 归档速率 | **4.11 秒/件**（均 566KB，137 KB/s）→ 单线程 875 件/小时 |
| 日增量耗时 | **约 13 分钟**（单线程），8 worker 更短 |

**结论：半小时/天的预算有 2 倍余量。质量一条都不用降。**

### 回填和增量必须拆成两个 cron

混在一起跑，看到的永远是回填的耗时（武汉开明一个群 18027 件是一次性回填，
它的日增量只有 110 件），会得出「永远追不上」的错误结论。

```bash
# 每日增量（进 cron）—— 起点由 manifest 自己算，窗口切到 1 天
python3 scripts/<pipeline>.py all --since-manifest --window-days 1

# 全量回填（不进 cron，跑完就停）
python3 scripts/<pipeline>.py all --start "2025-01-01 00:00:00" --window-days 30
```

### 量大的群单独一个 cron

武汉开明占日增量的 **71%**（773/1087）。把它单独拆一个 cron 给 8 worker，
其余 30 群一个 cron，互不阻塞。

### cron 间隔必须大于单轮耗时

pipeline 自己有 `workdir/.pipeline.lock` pid 锁，第二个实例会直接退出，
但间隔太密只是在反复白启动。

## 窗口失败语义（v0.3.1 / v0.0.0.3 改动）

**单个窗口失败不再中断整轮。** 旧版遇到一个坏件就 `break`，当轮剩下的窗口全不跑 ——
实测全库 13 个 stopped 窗口（项目设备工具类管理群 9、武汉开明 4），
而武汉开明占日增量 71%，它一被截断整体就停住，这才是「追不上」的真机制。

现在：失败窗口记 `stopped` 后**继续下一个窗口**，下轮重试；
连续 `MAX_CONSECUTIVE_WINDOW_FAILURES`（3）个失败才放弃该群本轮。

**「不得跳过未完成窗口」这条保证没有丢**，改由 `manifest_window_bounds` 兜：
增量起点只推进到**第一个非 complete 窗口之前**，不是 `max(end)`。
所以中间卡着 stopped 窗口的群，起点会停在它前面反复重扫那几天 ——
这是**正确的代价**，不重扫就是静默缺口。把坏窗口修好，起点自动前进。

## SMB 挂载点

`SMB_ROOT` 现在动态解析，**不再写死 `/Volumes/share`**：
`KM_SMB_ROOT` 环境变量 → `/Volumes/share` → `~/mnt/share` → `mount` 输出里任何 smbfs 挂载点。

起因是实测事故：260820 盘换挂到 `~/mnt/share` 之后，写死路径的两个 skill 直接报
`SMB root is unavailable` 起不来 —— 定时任务会天天空转失败且不易察觉。

## 接手须知（新 agent 从这里开始）

### 第一次接手先跑这三条，都不改数据

```bash
# 1) 账本自愈（只修 原名新名映射.csv，不动素材、不动 manifest）
python3 scripts/kmvideo_pipeline.py probe --workdir /tmp/km_heal

# 2) 看当前健康度
python3 scripts/kmvideo_pipeline.py accept --workdir /tmp/km_heal

# 3) 看有没有真缺（增量，别全量遍历）
python3 scripts/archive_internal_media.py --allow-title "<群名>" --since-manifest --dry-run --audit
```

不传 `--groups-file` 时用内置 `BUSINESS` 映射表作基线（Owner 已授权的那批群），
skill 包里不需要额外带白名单文件。要拿 dws 实时名单加 `--refresh-groups`。

**为什么第 1 步必须先跑。** `.manifest.jsonl` 永远记原名（硬约束 2 禁改），改过名的文件
要靠 `原名新名映射.csv` 这本账才能定位。这本账一旦写丢过一次（进程被硬杀、SMB 写失败、
跨版本运行），改名的幂等闸就再也不会补写它 —— 表现是 audit / accept 一直报 missing，
而磁盘上文件其实好好的。`probe` 阶段的 `reconcile_ledger()` 会自动认回：
媒体侧按「同目录、同字节数、且唯一未被认领」匹配（manifest 里没有 md5），
**有歧义一律不猜**，把候选打印出来留给人工。

日志里看 `账本自愈={'repaired': N, 'ambiguous': M}`：`repaired` 是自动认回的，
`ambiguous` 那几条必须人工定夺。

### 当前已知待办（截至 260819，会过期）

> 实时状态以 `workdir/accept_report.json` 和 `workdir/产能汇总.md` 为准，别信这段的数字。

1. **人工复核**：脱敏风险非「无」的 100% + 其余抽样 ≥10%。这是 accept 里唯一一项
   靠人过的闸门，跑得再干净它也会挂，属正常。复核后把 `素材登记表.csv` 的
   `复核状态` 列改成「已复核通过」或「已复核修正」。
2. **2025 年缺口**：多数群 manifest 首窗口是 2026-01-01，更早的消息从没扫过。
   跑任何命令时留意 `window_coverage_gap` 事件，命中的群需要一次
   `--start "2025-01-01 00:00:00"` 的补跑。
3. **「项目设备工具类管理群」**：DWS 分页缺陷（空页 + `hasMore=true`），只能记 skip。
4. **KMVideo 待确认标注 10410 条**：早前批次遗留，`描述` 为空或置信度「待确认」，需人工终审。
   这批不影响归档完整性，只影响改名 —— 说明填不出的一律保留原文件名。

### 三条绝对不要做

1. **不要对运行中的 pipeline 用 `pkill -9`。** 用 SIGTERM 等它写完当前 manifest。
   历史事故：SIGKILL 打断 manifest 写入，7 个群的 `.manifest.jsonl` 整个消失，
   逐群重建花了约 10 分钟/群。现在有 `.bak` 兜底，但兜底是最后一道，不是常规操作。
2. **不要用「ls 超时」判断进程卡死。** SMB 慢的时候 ls 必然超时，会把还活着的批次误杀。
   用「产物 mtime 停滞 + 进程 CPU time 不涨」判。
3. **不要修改 `.manifest.jsonl`。** 它是归档器的durable 账本，硬约束 2。
   要改「现用名」改 `原名新名映射.csv`。

### 已排除的群

`kmvideo_pipeline.py` 里的 `DECLINED_TITLES` 常量列着 Owner 明确说过「不管」的群
（台泥(贵港)、生产付款群、生产周例会工作群，2026-08-16 的决定）。
`--refresh-groups` 会把它们归入「已排除」而不是「新增待确认」，不会每轮重复问。
**要重新纳入就把群名从该常量里删掉**，别绕过它。

## 运行知识（实测，不是推测）

### SMB 慢：是会话退化，不是「白天不可用」

服务端是 OpenWRT 路由器上的 Samba（USB 外接硬盘）。症状表现为白天不可用，实测真因是
**SMB 会话退化 + 卡死进程占管道**，与时段和网络都无关。修复三步（实测 20–100 倍提速）：

```bash
# 1) ~/Library/Preferences/nsmb.conf
[default]
dir_cache_max=300
dir_cache_min=240
max_dirs_cached=512
notify_off=yes
streams=no
soft=yes
# 2) 重挂
diskutil unmount force /Volumes/share && open "smb://GUEST:@192.168.0.1/share" && sleep 12
# 3) sample 查是否有进程阻塞在 stat，有就杀掉
```

| 指标 | 退化时 | 修复后 |
|---|---|---|
| 18k 文件目录枚举 | 90s+ 跑不完 | 4s |
| 单文件读 | 1–2s | 0.04s |
| 写 2MB | 8.6s | 1s |

pipeline 开跑前自动跑一次健康自检（listdir 计时，超 `SMB_SLOW_SECONDS`，默认 10s
即判 degraded 并打印修复命令）。`--skip-smb-check` 可关。

### 卡死判据

**不要用「ls 超时」判死** —— SMB 慢的时候 ls 必然超时，会把还活着的批次误杀。
用「产物 mtime 停滞 + 进程 CPU time 不涨」判死。真卡死的特征：进程状态 U、
产出零增长、CPU time 不动、worker 线程全阻塞在 stat。

### 禁止对运行中的 pipeline 用 SIGKILL

用 SIGTERM 并等它写完当前 manifest。历史事故：`pkill -9` 打断 manifest 写入，
7 个群的 `.manifest.jsonl` 整个消失（媒体数据完好），只能逐群 `--smb-only` 重跑重建，
约 10 分钟/群。现在写 manifest 前会先留 `.bak`，读不到主文件时自动回退，
并在开跑时检测 `.partial-*` 残留。

### 并发

同一 workdir 只允许一个实例（`workdir/.pipeline.lock` pid 锁）。
cron 触发间隔一定要大于单轮耗时，否则第二个实例会和第一个抢同一份 manifest 与登记表。

### SMB rename 会随机永久挂死 —— 用子进程超时（260821 实测）

`os.rename` 在 OpenWRT Samba 上可能直接进 U 态永久挂死，主线程调用会卡死整条 pipeline。
新版 pipeline 已内置 `rename_with_timeout()`：单文件 rename 放 `subprocess.Popen(start_new_session=True)`
子进程，超 `KM_RENAME_TIMEOUT`（默认 8s）就 `killpg(SIGKILL)` 清掉。**不要在 pipeline 外另写直接
`os.rename` 的脚本去碰 SMB。** 账本增量落盘用 `flush_ledger()`（每 200 条写一次），
被杀进程/断连也不丢太多已改名条目。

### 超大目录 rename 是服务端缺陷，要单独针对性脚本（260821 实测）

单群万级文件（武汉开明 18027 件回填）的 photo 目录，NAS 服务端 rename 成功率约 50%、
8–10s/个，是服务端目录/索引退化，不是 skill 问题。命中时不要混进全量 rename：
写独立脚本只处理该群，每轮重挂新 SMB 会话绕开服务端目录污染 + 逐文件子进程超时 + 每 20 条落账，
后台长跑（数小时收敛），账本 flush 前被杀只丢当批。

### 白箱进度：一条命令看清在跑什么（v0.3.1 +260821）

用户问「你是不是在空转」「怎么看不到进度」时，说明进度不可见。本 skill 提供
`scripts/progress.py`，**只读**（读 workdir 产物 + pgrep 阶段进程，不碰 SMB、不动数据）：

```bash
python3 ~/.agents/skills/KMMedia-Archive/scripts/progress.py           # 一次快照
python3 ~/.agents/skills/KMMedia-Archive/scripts/progress.py --watch   # 每 60s 刷一次
python3 ~/.agents/skills/KMMedia-Archive/scripts/progress.py --workdir /tmp/xxx  # 指定 workdir
```

三段输出，缺一段就不算白箱：
- **① 登记表进度**：已改名 / 总数（百分比条）、标注已 / 待确认、accept pass/fail
- **② 阶段是否在跑**：scan/probe/thumbs/dedup/label/rename/registry/accept/report 谁活着
  （用 `pgrep -f kmvideo_pipeline.py <stage>` + `ps` 取命令行判断，排掉 progress.py 自身与 bash 包装）
- **③ 素材库概况**：照片/视频/脱敏非无/有描述/缩略图数

何时主动贴：每完成一个阶段；任何一步预计超 5 分钟先说清「怎么自己查」；等一个不会来的通知前先查快照。

## 已知外部障碍（记录在案，不阻塞流水线）

- 群「项目设备工具类管理群」：DWS 分页返回空页且 `hasMore=true`（DWS 侧缺陷），扫描阶段记录 skip 并进产能汇总待办。
- 钉钉侧已删除/已过期的素材：`dws` 报 `resource.notFound`，或下载回来是空文件（md5 `1B2M2Y8AsgTpgAmY7PhCfg==`）。
  这类是**永久错误**，记 `smb_status=unavailable` + 原因后继续，不再 window_stopped ——
  窗口从旧到新推进，一个永久坏件会把该群后面所有窗口全堵死（实测武汉开明 ~9 个文件正是如此）。
  这些条目进产能汇总待办，需人工到钉钉确认。
- 「张霖泽」单聊：SINGLE_CHAT 政策拒绝，除非 Owner 显式加入 AUTHORIZED_NON_INTERNAL_TITLES。
- 无上下文且无 EXIF/OCR 信号的素材：说明留「待确认」，保留原文件名，进待办清单，等人工终审。
