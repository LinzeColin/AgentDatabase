<!-- 给 Owner 看的：这套东西你每天怎么用。不是设计文档。 -->

# 你怎么用这套 memory atlas

## 一句话

**你什么都不用做。** 每天凌晨 codex 自动跑一遍，你在
`https://memoryatlas.linzezhang.com` 打开就能看到最新的。

## 你会看到什么

| 你想知道 | 去哪看 |
|---|---|
| 我最近在忙什么 | 星图首页顶部：会话数、活跃天、图谱环 |
| 我把时间花在哪类事上 | 主题下拉：「我在做·修bug（1139 会话）」这类 |
| 我用哪个 AI 工具最多 | 主题下拉：「AI 工具·claude-code（1500 会话）」这类 |
| 哪天最忙 | 时间线视图，按天 |
| **钱漏在哪一步** | 分析报告的「三、钱漏在哪一步」 |

## 三份给你的报告（每天自动更新）

1. **我在用AI做什么.md** —— 九档时间切片（3/7/15/30/45/60/90/180 天 + 全历史）、
   主题分布、主题趋势、以及「建设 : 上线 : 收入」的比例
2. **日记.md** —— 按天：那天开了几个会话、说了几次、卡在哪、开头几句是什么
3. **日历.md / 时间线.md** —— 哪天忙、并行着几条项目线

> 这三份含你的原话，**只在本机和私有仓**，不进公开仓。

## 一份给 agent 的（这是降 token 的那部分）

**LESSONS.md** —— 从你的真实会话里提炼的教训，带出处，8KB 硬上限。
后续任何 agent 开工前读它，就不用把你踩过的坑再踩一遍。
已写进 `OpenAIDatabase/AGENTS.md`，agent 会自己读到。

## 每天发生什么

```
03:00  codex automation 触发（唯一的 agent 依赖，它只是个开关）
       ├── 现有：全量加密备份 → Private-Database 私有 Release
       └── 新增：memory_atlas_daily.py
             1 抽取   各 agent 会话 → 结构化事件（只算变化的文件）
             2 分析   九档切片 + 主题趋势 + 收入阶梯
             3 视图   日记 / 日历 / 时间线
             4 沉淀   给 agent 的教训
             5 投影   写进星图数据
推 main → GitHub Actions 自动构建并发 preview（本机零参与）
```

**运行期零 agent、零 token。** 五个工具全是纯 Python 标准库，
不调任何模型、不联网、不需要 pip install —— CI 里有一道 AST 门守着这条。

## 你唯一需要做一次的事

线上 Pages 项目 `openai-memory-atlas` **没有接仓库**（2026-08-03 就查明了），
推 main 不会自动部署。我已经把部署工作流写好了，但它需要两个 secret，
**凭据只能你自己加，我不碰**：

1. 打开 `LinzeColin/AgentDatabase` → Settings → Secrets and variables → Actions
2. 添加 `CLOUDFLARE_API_TOKEN` 与 `CLOUDFLARE_ACCOUNT_ID`
3. 之后推 main 就会自动构建并发 preview

**production 不会自动升级** —— 因为线上现役是个从未推送过的孤儿构建
（commit `12734c10bf37` 在 GitHub 上根本不存在），覆盖后回不去。
要升级时去 Actions 手动跑一次并勾选 promote。

## 出问题怎么看

每次跑完输出一行 JSON receipt，`state` 是 `SUCCEEDED` 或 `FAILED`，
四个步骤各自的状态和耗时都在里面。排查见
`MEMORY_ATLAS_DAILY_SEDIMENT.md` 的「坏了怎么查」。
