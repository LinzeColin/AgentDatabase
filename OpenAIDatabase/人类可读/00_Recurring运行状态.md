# 00｜Recurring 运行状态

> 这是最浅层的验收入口。正常情况下只看本页和《00_Recurring分析_最新.md》。

| 验收项 | 当前值 |
|---|---|
| 总体验证 | **PASS** |
| 数据状态 | **延迟** |
| 数据覆盖至 | `2026-07-10T16:39:25Z` |
| 本次核验时间 | `2026-07-23T00:00:00Z` |
| 人工重复组 | `2466` |
| Automation 重复组 | `1412`（隔离） |
| 问题与纠正 | `18` |
| 规则与偏好 | `443` |
| 任务与主题 | `2005` |
| 分析脚本 LLM / embedding / 外部模型 API | `0 / 0 / 0` |
| 原始文件 | `131` |
| 派生数据指纹 | `sha256:7721f953d4da475962b009e322263dd01889255cca2b75e43db2a9c3adf1bf0e` |

## 自动防护

- ✅ 只读取明确的 user message event。
- ✅ AGENTS、environment、turn_context、系统/开发者注入被排除。
- ✅ `event_msg` / `response_item` 双记录只保留一份。
- ✅ 人工 Prompt 与 Codex Automation 分开统计。
- ✅ 严格只有三类；Action 内执行单元测试、来源校验、隐私扫描和独立全量对账。

## 去哪里看

1. 结果正文：[打开 00_Recurring分析_最新.md](./00_Recurring分析_最新.md)
2. GitHub：仓库顶部 `Actions` → `Recurring Prompt Analysis｜重复提示词自动分析` → 最新绿色运行 → `Summary`。
3. 下载包：同一次 Action 页面底部 `Artifacts` → `Recurring中文验收包-*`。
