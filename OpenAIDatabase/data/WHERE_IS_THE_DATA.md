# 📍 数据在哪：本地 data/ 是活运行态，Private-Database 是跨仓快照入口

> **给所有正在开发和后续新 agent 的路牌。**
>
> ⚠️ **先读懂这条，别删本地 data/**：本目录 `OpenAIDatabase/data/` 是 MemoryAtlas 记忆系统的
> **活运行态**——`data/memory/agent-memory.json` 是 agent 的**启动读取入口**，CI（`atlasctl build-atlas`）
> 每次也读它，系统还在持续往这里写。**它不是可弃的迁移副本，删了整个系统会崩。**

## 权威关系（务必分清）

| 位置 | 角色 |
|---|---|
| 本仓 `OpenAIDatabase/data/`（692 文件） | **活的、权威的**运行记忆，随系统写入持续更新 |
| `LinzeColin/Private-Database` 的 `Private-AgentDatabase/`（691 文件快照） | **时间点快照 + 跨仓访问入口**；自 2026-07-19 播种后本地已继续演进，此快照会过期 |

## 什么时候用哪个

- **本仓自身的代码/CI/agent 启动**：照旧读写本地 `OpenAIDatabase/data/`，不要改。
- **别的仓 / 别的 agent 想跨仓拿这批数据**：用 SDK 从 Private-Database 按需下载，**不要 `git clone` Private-Database**（预计 500GB+，损伤本地机器）：

```bash
T=OpenAIDatabase/scripts/private_db_client.py
python3 $T get  Private-AgentDatabase data/processed/yyy.json ./out.json   # 按需下载单文件
python3 $T list Private-AgentDatabase data/public_raw                       # 列目录
```

## 若要真正「data 只存 Private-Database」（后续 agent 注意）

那需要把 OpenAIDatabase 的启动/CI 读取路径从本地 `data/` 改为经 SDK 读 Private-Database，
并让 Private-AgentDatabase 保持与本地同步。**这是 OpenAIDatabase 系统自身的架构改造工作，
不是「仓库拆分」线程能代做的**——拆分线程只负责把统一数据仓、SDK、路牌就位（已完成）。
在那次改造完成前，**本地 data/ 是唯一权威，Private-AgentDatabase 是备份/跨仓入口**。

协议见 `Private-Database/PROTOCOL.md`；统一数据仓总说明见 `Private-Database/README.md`。
