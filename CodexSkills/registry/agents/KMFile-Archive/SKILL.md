# KMFile-Archive（KMFile 一体化流水线）

> 版本 v0.0.0.1（260818）。`KMMedia-Archive` 的同位体，只处理钉钉**文件（文档）**。
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

## 已知外部障碍（记录在案，不阻塞流水线）

- 群「项目设备工具类管理群」：DWS 分页返回空页且 `hasMore=true`（DWS 侧缺陷，与媒体版记录一致），扫描阶段记录 skip 并进产能汇总待办。
- 非 INTERNAL_GROUP 的项目群需在 `AUTHORIZED_NON_INTERNAL_TITLES` 白名单内，且仍要逐个 `--allow-title` 显式授权；名单外一律拒绝。
- `.et`（WPS 表格）新版是 OOXML zip、旧版是二进制；旧版抽不出正文时降级为「无正文」，靠文件名与上下文打标。
- 无上下文、无正文信号的文件：说明留「待确认」，保留原文件名，进待办清单，等人工终审。
