# 📍 数据在哪 / 迁移状态：本地 data/ = 活运行态（只读镜像源），Private-AgentDatabase = 已镜像的跨仓入口

> **给所有开发中 / 后续新 agent 的路牌。动本目录前，先读完这条。**

## 🚫 最重要：勿再上传 / 合并 / 重新同步（防重复）

本目录 `OpenAIDatabase/data/` 已完整镜像到 `LinzeColin/Private-Database` 的 `Private-AgentDatabase/`，**迁移已完成**。

- ✅ **已核对一致**：截至 **2026-07-23**，`data/` 下 **691 个文件两边 git blob sha 完全相同**。
- ⚠️ 本地另有 2 个**非数据**文件——本路牌 `WHERE_IS_THE_DATA.md` + `run_logs/skills_runs/README.md`（本地脚手架）——**属本地专有，不镜像、无需上传补齐**。Private 是 691、本地是 693，这个差是**预期的，不是缺口**。
- 🚫 **任何 agent 不要再把本地 `data/` 上传 / 同步 / 合并 / 重灌到 Private。** 数据的跨仓落地已完成；再传只会产生重复对象和 churn。机器可读信号见同目录 **`MIRROR_STATUS.json`**（`status: MIRRORED_DO_NOT_REUPLOAD`）。

## ⚠️ 同样重要：别删本地 data/

`data/memory/agent-memory.json` 是 agent 的**启动读取入口**，CI（`atlasctl build-atlas`）每次也读它，本仓运行时**仍在持续读写**本目录。**它是活运行态，删了本仓系统会崩。**

## 权威 / 生命周期（务必分清）

| 位置 | 角色 |
|---|---|
| 本仓 `OpenAIDatabase/data/`（693 文件，其中 691 为数据） | **本仓运行时的活读写权威**；对迁移 / 同步类 agent 而言 = **只读源**，处于**逐步淘汰（gradual phase-out）**路径 |
| `LinzeColin/Private-Database` 的 `Private-AgentDatabase/`（691 数据 + objects/ + manifest） | **已镜像的跨仓访问入口**；与本地一致，**不需再同步** |

- **本仓自身运行时**（agent 记忆读写 / CI atlasctl）：照常读写本地 `data/`，不受迁移影响。
- **迁移 / 同步 / 清理类 agent**：把本地 `data/` 当**只读**，**不上传、不合并、不删**。
- **逐步淘汰说明**：长期目标是把消费者启动 / CI 的读取路径改为经 SDK 读 Private；**该改造尚未做**。在那之前本地 `data/` 仍是本仓活权威，保持只读对待、勿改勿删。改造完成、校验通过后，再按流程退役本地副本——**不是现在**。

## 跨仓怎么读（别的仓 / 别的机器，免 clone）

不要 `git clone` Private-Database（预计 500GB+，损伤本地机器）。用 SDK 按需取单文件：

```bash
T=OpenAIDatabase/scripts/private_db_client.py
python3 $T get  Private-AgentDatabase data/processed/yyy.json ./out.json   # 按需下载单文件
python3 $T list Private-AgentDatabase data/public_raw                       # 列目录
```

## 大文件（会话历史 / 导出 / 恢复包）已迁 Release

会话历史、ChatGPT 导出、修复包等大文件（21 项，最大 ~1.5GB）已从**公开 AgentDatabase Release 删除**、迁到 **Private-Database Releases**（多数 `public_copy_status: DELETED_VERIFIED_ABSENT`）。

- 旧的公开 AgentDatabase Release URL 已失效；**改从 Private-Database Releases 取**。
- 完整 旧→新 映射账本：`Private-AgentDatabase/manifest.jsonl`（每条含 `original_name` / `destination_release_tag` / `object_path`）。

协议见 `Private-Database/PROTOCOL.md`；统一数据仓总说明见 `Private-Database/README.md`。
