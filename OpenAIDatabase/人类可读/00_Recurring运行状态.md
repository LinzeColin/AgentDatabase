# 00｜Recurring 运行状态

> 这是最浅层的验收入口。正常情况下只看本页和《00_Recurring分析_最新.md》。

| 验收项 | 当前值 |
|---|---|
| 总体验证 | **PASS** |
| 数据状态 | **延迟** |
| 数据覆盖至 | `2026-07-10T16:39:25Z` |
| 本次核验时间 | `2026-07-23T00:00:00Z` |
| 人工重复组 | `2309` |
| Automation 重复组 | `1412`（隔离） |
| 问题与纠正 | `18` |
| 规则与偏好 | `399` |
| 任务与主题 | `1892` |
| 分析脚本 LLM / embedding / 外部模型 API | `0 / 0 / 0` |
| 注入完整性防护 | **PASS** |
| 修复后真实数据批次 | **候选通过 1/2** |
| 原始文件 | `131` |
| 派生数据指纹 | `sha256:65679140dbe4367eb38b4c103cdeb55406a620076eaeb6d9b336e68829fcfe92` |

## 自动防护

- ✅ 只读取明确的 user message event。
- ✅ 同一 turn 优先信任 `event_msg/user_message`，并在条款拆分前丢弃对应 `response_item`。
- ✅ 再按 content block 保留来源边界，剥离 AGENTS、environment、turn_context 和系统/开发者注入。
- ✅ Builder 发布前与 Validator 发布后分别独立执行注入完整性硬门。
- ✅ 增量复用后再次执行全局来源权威检查，避免跨 part 文件漏网。
- ✅ 人工 Prompt 与 Codex Automation 分开统计。
- ✅ 严格只有三类；Action 内执行单元测试、来源校验、隐私扫描和独立全量对账。

## 去哪里看

1. 结果正文：[打开 00_Recurring分析_最新.md](./00_Recurring分析_最新.md)
2. GitHub：仓库顶部 `Actions` → `Recurring Prompt Analysis｜重复提示词自动分析` → 最新绿色运行 → `Summary`。
3. 下载包：同一次 Action 页面底部 `Artifacts` → `Recurring中文验收包-*`。
