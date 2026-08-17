# dingtalk-incremental-media-archive（KMVideo 一体化流水线）

> 版本 v0.2.0（260817）。素材库任务书 v0.0.2.0 的完整执行体。
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
10. **不得调用任何外部 agent**（Claude Code CLI / Codex CLI / 其他 CLI agent / 远程视觉服务）。多模态问题一律本地自解：
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

## 已知外部障碍（记录在案，不阻塞流水线）

- 群「项目设备工具类管理群」：DWS 分页返回空页且 `hasMore=true`（DWS 侧缺陷），扫描阶段记录 skip 并进产能汇总待办。
- 「张霖泽」单聊：SINGLE_CHAT 政策拒绝，除非 Owner 显式加入 AUTHORIZED_NON_INTERNAL_TITLES。
- 无上下文且无 EXIF/OCR 信号的素材：说明留「待确认」，保留原文件名，进待办清单，等人工终审。
