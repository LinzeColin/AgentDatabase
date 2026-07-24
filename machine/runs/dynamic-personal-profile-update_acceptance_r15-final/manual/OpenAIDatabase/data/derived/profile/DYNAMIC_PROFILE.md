---
{
  "schema_version": "dynamic_personal_profile.v1",
  "artifact": "dynamic_personal_profile",
  "artifact_status": "generated_derived_view",
  "skill_version": "0.0.0.1",
  "generated_at": "2026-07-22T12:00:00Z",
  "input_mode": "derived_only",
  "canonical_stable_profile_write": false,
  "source_snapshot_sha256": "sha256:6db433ef6257d11f09ad0dbc8328acbfad87bbd2c269924d45f7b536b7ef7560",
  "semantic_snapshot_sha256": "sha256:ef11a3563821d8c575ed55f5049e5b2bf44b8c3c0cf935ebb0a06e8da9897e27",
  "source_files": [
    {
      "path": "OpenAIDatabase/data/derived/behavior_intelligence/low_value_loops.json",
      "sha256": "sha256:04ba6571e868643e46608802826cd805537d75d9774c98af24f88c20804d772d",
      "bytes": 162
    },
    {
      "path": "OpenAIDatabase/data/derived/codex/codex_agent_recommendations.json",
      "sha256": "sha256:28253aaa455efd662f6d315f6f98decd0cee5194786c428e8e8dfa7c923b83b2",
      "bytes": 191
    },
    {
      "path": "OpenAIDatabase/data/derived/profile/CORE_PROFILE.md",
      "sha256": "sha256:368e3803bcb99b5952ca83d41034473febe608878ccaecd53a19fda3cde6cbf9",
      "bytes": 118
    }
  ],
  "time_windows": [
    "recent_7d",
    "recent_30d",
    "long_baseline"
  ],
  "entry_count": 4,
  "entries": [
    {
      "id": "dp-f7f4391ae134",
      "type": "profile_signal",
      "status": "current",
      "statement": "Prefer deterministic profile view.",
      "evidence": [
        "OpenAIDatabase/data/derived/codex/codex_agent_recommendations.json"
      ],
      "counterevidence": [
        "This redacted derived summary was not independently rechecked against its underlying sessions in v0.0.0.1."
      ],
      "confidence": "high",
      "observed_window": "recent_7d",
      "valid_until": null,
      "agent_action": "在下一次与“Prefer deterministic profile view.”直接相关的任务中试用一次；若没有可观察收益或出现反证，立即失效。",
      "asset_candidate": "observation",
      "occurrences": 7,
      "source_count": 1
    },
    {
      "id": "dp-093d342dbbc2",
      "type": "profile_signal",
      "status": "current",
      "statement": "Prefer evidence-backed delivery.",
      "evidence": [
        "OpenAIDatabase/data/derived/profile/CORE_PROFILE.md"
      ],
      "counterevidence": [
        "Stable curated baseline; this source does not provide a recent observation timestamp."
      ],
      "confidence": "high",
      "observed_window": "long_baseline",
      "valid_until": null,
      "agent_action": "在下一次与“Prefer evidence-backed delivery.”直接相关的任务中试用一次；若没有可观察收益或出现反证，立即失效。",
      "asset_candidate": "observation",
      "occurrences": 1,
      "source_count": 1
    },
    {
      "id": "dp-227a074aac71",
      "type": "asset_candidate",
      "status": "emerging",
      "statement": "派生行为数据在 1 个主题簇中检测到 scope creep 候选（累计 3 条事件）；下一次相关任务应先冻结 run contract、非目标和写入边界。",
      "evidence": [
        "OpenAIDatabase/data/derived/behavior_intelligence/low_value_loops.json"
      ],
      "counterevidence": [
        "The aggregation may reflect a temporary period of concentrated development rather than a durable work pattern."
      ],
      "confidence": "medium",
      "observed_window": "recent_7d",
      "valid_until": null,
      "agent_action": "在下一次与“派生行为数据在 1 个主题簇中检测到 scope creep 候选（累计 3 条事件）；下一次相关任务应先冻结 run contract、非目标和写入边界。”直接相关的任务中试用一次；若没有可观察收益或出现反证，立即失效。",
      "asset_candidate": "workflow",
      "occurrences": 3,
      "source_count": 1
    },
    {
      "id": "dp-f09e0df53607",
      "type": "asset_candidate",
      "status": "emerging",
      "statement": "派生行为数据在 1 个主题簇中检测到反复返工候选（累计 2 条事件）；下一次相关任务应先复用现有资产并设置一次复跑验收。",
      "evidence": [
        "OpenAIDatabase/data/derived/behavior_intelligence/low_value_loops.json"
      ],
      "counterevidence": [
        "The aggregation may reflect a temporary period of concentrated development rather than a durable work pattern."
      ],
      "confidence": "medium",
      "observed_window": "recent_7d",
      "valid_until": null,
      "agent_action": "在下一次与“派生行为数据在 1 个主题簇中检测到反复返工候选（累计 2 条事件）；下一次相关任务应先复用现有资产并设置一次复跑验收。”直接相关的任务中试用一次；若没有可观察收益或出现反证，立即失效。",
      "asset_candidate": "workflow",
      "occurrences": 2,
      "source_count": 1
    }
  ]
}
---

# Dynamic Personal Profile

## 先看结论

- **current / high**：Prefer deterministic profile view.
- **current / high**：Prefer evidence-backed delivery.
- **emerging / medium**：派生行为数据在 1 个主题簇中检测到 scope creep 候选（累计 3 条事件）；下一次相关任务应先冻结 run contract、非目标和写入边界。
- **emerging / medium**：派生行为数据在 1 个主题簇中检测到反复返工候选（累计 2 条事件）；下一次相关任务应先复用现有资产并设置一次复跑验收。

## 变化条目

### dp-f7f4391ae134｜current

- 类型：`profile_signal`；资产候选：`observation`
- 观察：Prefer deterministic profile view.
- 证据：`OpenAIDatabase/data/derived/codex/codex_agent_recommendations.json`
- 反证：This redacted derived summary was not independently rechecked against its underlying sessions in v0.0.0.1.
- 置信度：`high`；时间窗口：`recent_7d`
- 临时 Agent 行为：在下一次与“Prefer deterministic profile view.”直接相关的任务中试用一次；若没有可观察收益或出现反证，立即失效。

### dp-093d342dbbc2｜current

- 类型：`profile_signal`；资产候选：`observation`
- 观察：Prefer evidence-backed delivery.
- 证据：`OpenAIDatabase/data/derived/profile/CORE_PROFILE.md`
- 反证：Stable curated baseline; this source does not provide a recent observation timestamp.
- 置信度：`high`；时间窗口：`long_baseline`
- 临时 Agent 行为：在下一次与“Prefer evidence-backed delivery.”直接相关的任务中试用一次；若没有可观察收益或出现反证，立即失效。

### dp-227a074aac71｜emerging

- 类型：`asset_candidate`；资产候选：`workflow`
- 观察：派生行为数据在 1 个主题簇中检测到 scope creep 候选（累计 3 条事件）；下一次相关任务应先冻结 run contract、非目标和写入边界。
- 证据：`OpenAIDatabase/data/derived/behavior_intelligence/low_value_loops.json`
- 反证：The aggregation may reflect a temporary period of concentrated development rather than a durable work pattern.
- 置信度：`medium`；时间窗口：`recent_7d`
- 临时 Agent 行为：在下一次与“派生行为数据在 1 个主题簇中检测到 scope creep 候选（累计 3 条事件）；下一次相关任务应先冻结 run contract、非目标和写入边界。”直接相关的任务中试用一次；若没有可观察收益或出现反证，立即失效。

### dp-f09e0df53607｜emerging

- 类型：`asset_candidate`；资产候选：`workflow`
- 观察：派生行为数据在 1 个主题簇中检测到反复返工候选（累计 2 条事件）；下一次相关任务应先复用现有资产并设置一次复跑验收。
- 证据：`OpenAIDatabase/data/derived/behavior_intelligence/low_value_loops.json`
- 反证：The aggregation may reflect a temporary period of concentrated development rather than a durable work pattern.
- 置信度：`medium`；时间窗口：`recent_7d`
- 临时 Agent 行为：在下一次与“派生行为数据在 1 个主题簇中检测到反复返工候选（累计 2 条事件）；下一次相关任务应先复用现有资产并设置一次复跑验收。”直接相关的任务中试用一次；若没有可观察收益或出现反证，立即失效。

## 可立即试用的 Agent 行为

- `dp-f7f4391ae134`：在下一次与“Prefer deterministic profile view.”直接相关的任务中试用一次；若没有可观察收益或出现反证，立即失效。
- `dp-093d342dbbc2`：在下一次与“Prefer evidence-backed delivery.”直接相关的任务中试用一次；若没有可观察收益或出现反证，立即失效。
- `dp-227a074aac71`：在下一次与“派生行为数据在 1 个主题簇中检测到 scope creep 候选（累计 3 条事件）；下一次相关任务应先冻结 run contract、非目标和写入边界。”直接相关的任务中试用一次；若没有可观察收益或出现反证，立即失效。
- `dp-f09e0df53607`：在下一次与“派生行为数据在 1 个主题簇中检测到反复返工候选（累计 2 条事件）；下一次相关任务应先复用现有资产并设置一次复跑验收。”直接相关的任务中试用一次；若没有可观察收益或出现反证，立即失效。

## Recurring Asset 候选

- `dp-227a074aac71` / `workflow`：一次真实任务验证前保持 `pending`。
- `dp-f09e0df53607` / `workflow`：一次真实任务验证前保持 `pending`。

## 边界与不确定性

- 本文件来自脱敏派生数据，不是原始记录，也不是稳定核心画像。
- 没有源时间戳时不推断精确发生日期。
- 当前脚本不调用 LLM，不做语义事实确认，不自动写回长期记忆。
- `CORE_PROFILE.md`、Custom Instructions、AGENTS.md 和 Memory Atlas canonical records 不会被本次运行修改。
