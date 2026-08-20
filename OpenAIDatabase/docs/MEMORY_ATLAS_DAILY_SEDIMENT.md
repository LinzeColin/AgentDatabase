<!-- 这份是给「接手的人和 agent」看的操作说明，不是设计文档。 -->

# 每日沉淀 memory atlas —— 怎么跑、怎么验、坏了怎么查

## 一句话

本机所有 agent 的会话，每天自动抽成结构化事件，产出四样东西：
给 agent 看的**教训**、给 Owner 看的**分析 / 日记 / 日历 / 时间线**。

**运行期零 agent、零 token。** 唯一的 agent 依赖是 codex automation ——
而它只是个**触发器**，真正干活的是纯 Python 脚本。

## 怎么跑

```bash
python3 OpenAIDatabase/scripts/memory_atlas_daily.py --repo-root . \
    --weekly-archive OpenAIDatabase/data/derived/agent_sessions/weekly
```

- 默认**增量**（只重算 mtime/size 变化的会话文件）。首次或需要重算时加 `--full`。
- 输出一行 JSON receipt，`state` 为 `SUCCEEDED` / `FAILED`。
- 幂等：同一天重复跑结果一致，不产生重复事件。

### 接进 codex automation

在 `memory-atlas-daily-source-capture` 之后追加一步即可（它已经每天 03:00 跑）。
两者是**不同层**，都要保留：

| | 现有 automation | 本流水线 |
|---|---|---|
| 目的 | **备份**（丢了能恢复） | **入库**（能被查询分析） |
| 产物 | age 加密分片 Release | 结构化事件 + 四样产出 |
| 形态 | 密文，人和 agent 都读不了 | 明文结构化 |

## 产出去哪

| 产物 | 位置 | 给谁 |
|---|---|---|
| 教训（带出处，8KB 硬预算） | `data/derived/agent_context/LESSONS.md` | **agent 开工前读** |
| 我在用 AI 做什么（9 档切片） | `人类可读/memory-atlas/我在用AI做什么.md` | Owner |
| 日记 / 日历 / 时间线 | `人类可读/memory-atlas/` | Owner |
| canonical 事件 | `data/derived/agent_sessions/*.events.jsonl` | 机器 |
| 每周切片归档 | `data/derived/agent_sessions/weekly/` | 回溯 |

**归档粒度最粗只能到「周」**（ISO 周）。粒度越粗，出事时能回到的最近一个
完好点就越远 —— 这是 Owner 2026-08-19 定的，`max_granularity_policy`
字段里写死了。

## 为什么是抽取不是搬运

实测一个 151MB 的 Claude Code 会话：助手发言 44%、工具输出 40%、
attachment 12%、**用户发言只占 1%**。抽取后压缩 **99.9%**（4.3GB → 3.9MB），
而信息不丢：用户发言数、工具调用数、报错提及、主题、原始标题全部保留。

整包搬运会把 codex 那条备份链的负载翻三倍，顶穿它 90 分钟的批次上限
（它当前 1.77GB / 2808 对象，连续 12 天 100% 成功）。

而且本仓 `config/data_sources/source_registry.json` 的隐私合同本来就要求这样：

```
raw_payload_policy: never_commit_raw_platform_exports_or_full_messages_to_github
privacy_level:      private_redacted_derived
```

## 已知的坑（都是踩过的）

1. **`record_id` 必须对文件唯一，不能只用文件名。**
   kimi-code 的 419 个会话**全部叫 `wire.jsonl`**，只是分散在不同目录。
   只取 stem 会让 419 个 record_id 碰成 1 个，**增量去重时塌掉 418 条**。
   非增量路径看不出来（events 是 list 不去重），只有开增量才暴露。
   已加回归锁 `test_同名文件在不同目录不能碰撞`。

2. **不是所有来源都有对话。** 查过但无可入库内容的已登记在
   `source_registry.json` 的 `no_ingest_sources`，免得下次又有人去挖：
   - `DSH Desktop` 那 1.0GB 全是 Electron 缓存（blob_storage / GPUCache）
   - `~/.workbuddy` 1.3GB 里 binaries 707MB + plugins 189MB 是安装包
   - `~/.mmx` 只有 8KB 配置

3. **产出有预算上限，超了要精简条目、不许调大上限。**
   `LESSONS.md` 8KB（≈2000 tokens）—— 它每个 session 都要被读一遍，
   超预算就是新的 token 负担，不是减负。和 kit 的 `check_doc_budget` 同一立场。

4. **产出了不等于被读到。** 本仓的 `AGENT_CONTEXT.md` 就是活教训：
   产出了，但 9 个仓里 8 个的 AGENTS.md 没指向它、全局 CLAUDE.md 一字未提，
   所以从来没被读过。**加了新产出就必须同时加指路。**

## 坏了怎么查

receipt 里 `steps[]` 逐步骤给 `state` 与 `detail`。四步互不阻断
（某步挂了其余照跑），但最终退出码如实反映。常见：

| 现象 | 多半是 |
|---|---|
| `1_extract` FAIL | 某个来源目录不存在 —— 看 `MISSING_SOURCE` |
| 事件数突然掉 | record_id 碰撞类问题，先跑 `--full` 对照 |
| `4_lessons` 产出 8KB 整 | 正常，撞到预算上限被截断 |
