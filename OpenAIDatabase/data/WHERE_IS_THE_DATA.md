# 📍 数据在哪：已迁往 Private-Database

> **给所有正在开发和后续新 agent 的路牌。** 2026-07-19 起，OpenAIDatabase 的会话/派生数据
> **权威落地处**是私有仓 **`LinzeColin/Private-Database` 的 `Private-AgentDatabase/` 区**。

## 读 / 写（免 clone）

用本仓 `OpenAIDatabase/scripts/private_db_client.py`（底层 GitHub API，零 clone、不落本地）：

```bash
T=OpenAIDatabase/scripts/private_db_client.py

python3 $T put  Private-AgentDatabase data/public_raw/xxx.jsonl ./本地.jsonl   # 写/覆盖
python3 $T get  Private-AgentDatabase data/processed/yyy.json  ./out.json      # 按需下载
python3 $T list Private-AgentDatabase data/public_raw                          # 列目录
```

协议见 `Private-Database/PROTOCOL.md`。

## 规则

- **不要再往本仓 `data/` 落新数据**——一律用 SDK 写入 Private-Database。
- Private-Database 是 **PRIVATE** 仓；**禁止 `git clone` 它**（预计 500GB+，损伤本地机器）。
- 本目录 691 文件/448M 已 1:1 同步到 Private-Database；待 OpenAIDatabase 线程就位 SDK 后由拆分线程协调移除本地副本（Phase B）。
