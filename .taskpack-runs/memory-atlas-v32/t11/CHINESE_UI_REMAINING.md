# 中文化剩余工作（实测，非估计）

生产渲染实测：**166 处**非中文可见文本，分布在 11 个视图。

- 机器标识符泄漏：51
- 未翻译英文：115

## 按视图

- home：48
- search：28
- timeline：25
- notion：22
- summary：13
- galaxy：10
- wordcloud：10
- obsidian：5
- runtime：3
- roi：1
- contribution：1

## 出现最多的词

- `ROI` × 16
- `capability` × 12
- `0.00` × 9
- `codex_usage_record` × 8
- `high` × 6
- `Memory` × 5
- `Proposal` × 5
- `event_count` × 4
- `false` × 4
- `true` × 4
- `low` × 3
- `core_profile` × 2
- `opportunity` × 2
- `stale` × 2
- `Legacy` × 2
- `answering_rule` × 2
- `tier` × 2
- `memory_atlas_proposal_draft.v1` × 2
- `importance` × 2
- `original_value:` × 2
- `proposed_value:` × 2
- `priority` × 2
- `note` × 2
- `Diff` × 2
- `Preview` × 2

判据是 `MemoryAtlas/scripts/audit_chinese_ui_v32.mjs`，跑一次就能重新量。
它按契约放行产品名、第三方名、协议字段，以及默认折叠的机器字段区。
