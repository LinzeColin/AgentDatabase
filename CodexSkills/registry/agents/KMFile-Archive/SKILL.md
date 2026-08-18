# KMFile-Archive（KMFile 一体化流水线）

> 版本 v0.0.0.2（260819）。`KMMedia-Archive` 的同位体，只处理钉钉**文件（文档）**。
> v0.0.0.2 按 260818 全量实跑（137 文件）的 12 条问题记录迭代：动态群名单、
> 增量起点直读 manifest、manifest 写入保护、永久错误不堵窗口、dws 绝对路径、
> 并发锁、SMB 健康自检、accept 的 md5 校验改走改名账本。
> 上级规则：`smb://192.168.0.1/share/03_资料库/MetaData/IDS_MetaData/KMFile/README.md`（冲突以 README 为准）。
> 命名规则与业务映射表与 KMVideo 共用同一套，不另立门户。

## 一句话

从钉钉群到交付：**全量扫描 → 增量归档 → 规格探测 → 正文抽取 → md5 精确去重 → 本地标注 → 幂等改名 → 登记表双格式 → 四处落地（SMB / 本机输出区 / Downloads / KMOS 公开仓 + Private-Database）→ 自验收 → 产能汇总**，一条命令全跑，全程不调用任何外部 agent。

## 与 KMMedia-Archive 的三处根本差异（实测冻结）

| | KMMedia-Archive | KMFile-Archive |
|---|---|---|
| 消息体 | `[图片消息](mediaId=@lQLPJw...)` | `[文件] 2026投标记录-武汉开明.xlsx fileId: R4Gpn...` |
| 下载 | `dws chat message download-media --type mediaId` | `dws drive download --node <fileId>` |
| 元数据 | ffprobe / PIL 本地探测 | `dws drive info --node` 返回服务端 **md5 + fileSize** |

服务端 md5 是 `base64(MD5 digest)`，实测与本机 `base64.b64encode(hashlib.md5(...).digest())` 逐字节相等。
因此文件版的完整性校验比媒体版多一层：**字节数 + 头尾抽样 + 服务端 md5 逐份复核**，
且存在性判定只读 `drive info`，**不整包下载**（云成本红线）。

**音视频不进 KMFile。** 扩展名命中 `AV_EXTENSIONS`（mp4/mov/mp3/…）的文件消息只登记为
`handoff_av` 记录并导出 `待转KMVideo.csv`，由 KMMedia-Archive v0.2.1 侧收
（该版本已打补丁，认 `[文件]` 传输的音视频）。

## 硬约束（违反任一条即停止）

1. 原始文件区只读；输入源不得删除、覆盖未知既有文件。
2. `.manifest.jsonl` 任何情况下不得修改。
3. 群目录只允许 `file/`、`.manifest.jsonl` **两样**。
4. 原始文件不得写入 KMOS 公开仓；KMOS 只放源码、Skill、脱敏登记表。
5. 长期业务数据走 `LinzeColin/Private-Database` 的 `Private-KMDatabase/`，经 `private_db_client.py`，禁止 clone 私有仓。
6. 云成本红线：禁止 `InfrequentAccess`；禁止整包下载做存在性校验（存在性用 `dws drive info` 的 md5/size）。
7. SMB 写入禁用 Python 写与 `shutil.copyfile` 快速路径；用 `rsync --inplace --whole-file` 或 `/bin/dd conv=fsync`，写后必须校验字节数**并复核服务端 md5**。
8. 日期一律 `YYMMDD`；公开仓禁用客户全称，项目名一律泛化为「业务名+群」，且去掉「能证明什么」列。
9. 不得新建平行登记表；所有标注写进根目录 `文件登记表.csv`，以新增列扩展。不与 KMVideo 的 `素材登记表.csv` 混表。
10. **不得调用任何外部 agent**（Claude Code CLI / Codex CLI / 其他 CLI agent / 远程视觉或语言服务）。
    文档没有画面，标注一律本地三路自解：
    - **原文件名** ← 关键词表（可信度最高，优先命中）
    - **消息上下文** ← 媒体消息前后 30 分钟内的文本消息
    - **抽取正文** ← 本地文本抽取（见下表），只取首段做兜底

## 正文抽取（零新增 pip 依赖）

| 扩展名 | 手段 | 依赖 |
|---|---|---|
| `pdf` | PyMuPDF (`fitz`) | 本机已装 1.26.5 |
| `xlsx` `docx` `pptx` `et` `wps` `dps` | 标准库 `zipfile` + XML 去标签（这些本质就是 zip 容器） | 零依赖 |
| `doc` `rtf` `html` `odt` | `/usr/bin/textutil -convert txt -stdout` | macOS 自带 |
| `txt` `csv` `md` `log` `json` `xml` | 直接读 | 零依赖 |
| `dwg` `zip` `rar` 等 | 不抽文本，只靠文件名 + 消息上下文 | — |

抽不出正文不算失败，降级为「无正文」继续跑；说明填不出就留「待确认」并**保留原文件名**，进待办等人工终审。

## 执行方式

```bash
python3 scripts/kmfile_pipeline.py all --groups-file <白名单.txt> \
        --start "2025-01-01 00:00:00" --window-days 30 \
        [--workdir /tmp/kmfile_work/pipeline]
```

单阶段可独立重跑（幂等）：`scan|probe|extract|dedup|label|rename|registry|upload|accept|report`。

- `--only-group 群名` 可先打样单群；`--no-private` 显式声明本轮跳过私有仓落地。
- `--window-days 30` 为拍板值：首轮从 `2025-01-01` 起按 30 天切片推进，之后每日增量。
- 私有仓落地依赖 `KMOS_ROOT` 环境变量（或运行于 KMOS worktree 内）定位 `private_db_client.py`；
  两者都失效时 `upload` 阶段**报错退出**（不再静默跳过）。
- 标注若有更高置信度的人工结论，`label` 阶段以 `workdir/label_override.jsonl`（键=`file`，值=字段）优先。

底层归档器也可单独调用：

```bash
python3 scripts/archive_internal_files.py --allow-title "2026年商务部报价群" \
        --start "2025-01-01 00:00:00" --window-days 30 --workers 4 --apply
python3 scripts/archive_internal_files.py --allow-title "..." --dry-run --audit   # 完成度审计
python3 scripts/archive_internal_files.py --allow-title "..." --dry-run --export-handoff ~/Downloads/待转KMVideo.csv
```

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
| 一 扫描+增量归档 | `scan` | manifest 增量（复读不改）、`workdir/context.jsonl` 消息上下文、`handoff_av` 交接记录 |
| 二 规格探测 | `probe` | `specs.jsonl`（扩展名/字节数/md5/发送人/磁盘核对） |
| 三 正文抽取 | `extract` | `workdir/texts/*.txt`、页数或行数、字数、摘要 |
| 四 md5 去重 | `dedup` | `dups.jsonl`（保留最早发出的那份，其余标「重复于」） |
| 五 本地标注 | `label` | `desc.csv`（文档类型/说明/工序阶段/能证明什么/脱敏风险/置信度） |
| 六 改名 | `rename` | 磁盘幂等改名 + `改名前后对照.csv` |
| 七 登记与落地 | `registry` `upload` | `文件登记表.csv`、`原名新名映射.csv`、`待转KMVideo.csv`、四处分发、公开仓、私有仓 ingest |
| 八 自验收+汇总 | `accept` `report` | `accept_report.json`、产能汇总表 |

### 登记表落点（三个本机 + 一个 GitHub）

| # | 位置 | 内容 | 性质 |
|---|---|---|---|
| 1 | `smb://192.168.0.1/.../IDS_MetaData/KMFile/` | `文件登记表.csv`、`原名新名映射.csv`、`待转KMVideo.csv` | **唯一真源**，`rsync` 写入并校验字节数 |
| 2 | `~/Documents/KMFile/00_治理与登记/02_登记与索引/` | 全量表、映射表、子集、公开脱敏版 csv/md、交接清单 | 输出工作区副本 |
| 3 | `~/Downloads/` | `KMFile文件登记表.csv`、`KMFile文件登记表_子集.csv` | 便于拖给 ChatGPT 上传 |
| 4 | KMOS 公开仓 `KMDatabase/data/KMFile/` | **仅脱敏版**：`文件登记表_public.csv/md`、`文件登记表_子集_public.csv` | 公开，项目名一律泛化为「业务名+群」，且去掉「能证明什么」列 |

- 分发由 `distribute_registry()` 完成，逐份校验字节数；**任一处写失败即抛错中止，不得静默跳过**。
- 进 KMOS 公开仓的**只能是 `_public` 后缀那几份**。

## 命名规则（照抄 KMVideo/README.md）

`{业务}_{说明}_{YYMMDD}_{序号}.ext`
- 说明 2–6 字，来自 `DOC_KEYWORDS` 三路命中；泛化词（文件/文档/资料/附件/扫描件…）一律拒绝
- 序号：同（群,业务,说明,日期）内递增两位，重跑时先把磁盘已有新名计入序号，保证不撞号
- 业务映射表（内置 BUSINESS 常量，与 KMVideo 同一张）：
  内部 / 焊接 / 安装检修 / 化工钢铁 / 化工 / 水泥调测窑 / 水泥
- 例：`内部_投标记录_260817_01.xlsx`、`化工_施工方案_260705_01.pdf`

## 登记表列（7 基础 + 14 新增）

基础：项目、文件名、日期、原文件名、大小、描述、置信度
新增：扩展名、文档类型、页数或行数、字数、md5、发送人、重复于、工序阶段、能证明什么、脱敏风险、摘要、标注执行者、标注日期、复核状态

枚举字段全部使用原始词汇，无 ABC 简写代称：
- 文档类型：报价单 / 投标记录 / 中标通知 / 合同 / 施工方案 / 验收报告 / 图纸 / 清单 / 工作日志 / 票据 / 明细账 / 通知公告 / 证明材料 / 技术资料 / 考勤薪酬 / 其他
- 工序阶段：测量 / 拆解 / 加工 / 焊接 / 复检 / 收尾 / 无法判断
- 脱敏风险：客户名称 / 人脸 / 打卡应用水印 / 精确地理位置 / 车牌 / 安全告示牌 / 金额报价 / 身份证号 / 银行账号 / 无

## 自验收判据（accept 阶段自动执行）

1. 登记表可读、非空、无重复行（项目+原文件名）
2. 已改名行的文件名格式与业务映射正确
3. 描述 2–6 字
4. 枚举字段全部落在原始词汇表内
5. **落地件 md5 与登记表（=服务端）一致** —— 文件版独有
6. `.manifest.jsonl` mtime 未变
7. 改名幂等：连跑两次第二次零变更、旧名残留 0
8. 复核覆盖率：脱敏风险非「无」100% 人工复核，其余抽样 ≥10%

## 接手须知（新 agent 从这里开始）

### 第一次接手先跑这三条，都不改数据

```bash
# 1) 账本自愈（只修 原名新名映射.csv，不动素材、不动 manifest）
python3 scripts/kmfile_pipeline.py probe --workdir /tmp/km_heal

# 2) 看当前健康度
python3 scripts/kmfile_pipeline.py accept --workdir /tmp/km_heal

# 3) 看有没有真缺（增量，别全量遍历）
python3 scripts/archive_internal_files.py --allow-title "<群名>" --since-manifest --dry-run --audit
```

不传 `--groups-file` 时用内置 `BUSINESS` 映射表作基线（Owner 已授权的那批群），
skill 包里不需要额外带白名单文件。要拿 dws 实时名单加 `--refresh-groups`。

**为什么第 1 步必须先跑。** `.manifest.jsonl` 永远记原名（硬约束 2 禁改），改过名的文件
要靠 `原名新名映射.csv` 这本账才能定位。这本账一旦写丢过一次（进程被硬杀、SMB 写失败、
跨版本运行），改名的幂等闸就再也不会补写它 —— 表现是 audit / accept 一直报 missing，
而磁盘上文件其实好好的。`probe` 阶段的 `reconcile_ledger()` 会自动认回：
文件侧按 manifest 里的服务端 md5 精确匹配，
**有歧义一律不猜**，把候选打印出来留给人工。

日志里看 `账本自愈={'repaired': N, 'ambiguous': M}`：`repaired` 是自动认回的，
`ambiguous` 那几条必须人工定夺。

### 当前已知待办（截至 260819，会过期）

> 实时状态以 `workdir/accept_report.json` 和 `workdir/产能汇总.md` 为准，别信这段的数字。

1. **人工复核**：脱敏风险非「无」的 100% + 其余抽样 ≥10%。这是 accept 里唯一一项
   靠人过的闸门，跑得再干净它也会挂，属正常。复核后把 `文件登记表.csv` 的
   `复核状态` 列改成「已复核通过」或「已复核修正」。
2. **2025 年缺口**：多数群 manifest 首窗口是 2026-01-01，更早的消息从没扫过。
   跑任何命令时留意 `window_coverage_gap` 事件，命中的群需要一次
   `--start "2025-01-01 00:00:00"` 的补跑。
3. **「项目设备工具类管理群」**：DWS 分页缺陷（空页 + `hasMore=true`），只能记 skip。
4. **武汉开明 ~9 个文件 + 商务部部分历史文件**：钉钉侧已删（`drive resource.notFound`）。
   这类现在记 `smb_status=unavailable` 后继续，不再堵窗口，但需人工到钉钉确认是不是真没了。

### 三条绝对不要做

1. **不要对运行中的 pipeline 用 `pkill -9`。** 用 SIGTERM 等它写完当前 manifest。
   历史事故：SIGKILL 打断 manifest 写入，7 个群的 `.manifest.jsonl` 整个消失，
   逐群重建花了约 10 分钟/群。现在有 `.bak` 兜底，但兜底是最后一道，不是常规操作。
2. **不要用「ls 超时」判断进程卡死。** SMB 慢的时候 ls 必然超时，会把还活着的批次误杀。
   用「产物 mtime 停滞 + 进程 CPU time 不涨」判。
3. **不要修改 `.manifest.jsonl`。** 它是归档器的durable 账本，硬约束 2。
   要改「现用名」改 `原名新名映射.csv`。

### 已排除的群

`kmfile_pipeline.py` 里的 `DECLINED_TITLES` 常量列着 Owner 明确说过「不管」的群
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

## 已知外部障碍（记录在案，不阻塞流水线）

- 群「项目设备工具类管理群」：DWS 分页返回空页且 `hasMore=true`（DWS 侧缺陷，与媒体版记录一致），扫描阶段记录 skip 并进产能汇总待办。
- 钉钉侧已删除/已过期的文件：`dws drive download` 报 `resource.notFound`，或下载回来是空文件
  （md5 `1B2M2Y8AsgTpgAmY7PhCfg==`）。这类是**永久错误**，记 `smb_status=unavailable` + 原因后继续，
  不再 window_stopped —— 窗口从旧到新推进，一个永久坏件会把该群后面所有窗口全堵死。
  这些条目进产能汇总待办，需人工到钉钉确认（实测武汉开明 ~9 个文件、商务部部分历史文件）。
- 非 INTERNAL_GROUP 的项目群需在 `AUTHORIZED_NON_INTERNAL_TITLES` 白名单内，且仍要逐个 `--allow-title` 显式授权；名单外一律拒绝。
- `.et`（WPS 表格）新版是 OOXML zip、旧版是二进制；旧版抽不出正文时降级为「无正文」，靠文件名与上下文打标。
- 无上下文、无正文信号的文件：说明留「待确认」，保留原文件名，进待办清单，等人工终审。
