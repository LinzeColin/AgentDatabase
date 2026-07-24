---
{
  "schema_version": "dynamic_personal_profile.v1",
  "artifact": "dynamic_personal_profile",
  "artifact_status": "generated_derived_view",
  "skill_version": "0.0.0.2",
  "generated_at": "2026-07-24T02:47:00Z",
  "input_mode": "derived_only",
  "canonical_stable_profile_write": false,
  "source_snapshot_sha256": "sha256:b9cf4e6941c8967150af02ca7fd0ec1dda1b08b3e14cc544e5906b4411ec38a0",
  "semantic_snapshot_sha256": "sha256:266c4b8d65f2228484fa884e612ea9d13a739f4c72a5ac066612d3d663f981a7",
  "source_files": [
    {
      "path": "OpenAIDatabase/data/derived/behavior_intelligence/low_value_loops.json",
      "sha256": "sha256:7c8ebca815cf9ba5cd5f16ab56aba6b32e319d753f4d54b51391b98c9329a094",
      "bytes": 209747
    },
    {
      "path": "OpenAIDatabase/data/derived/codex/codex_agent_recommendations.json",
      "sha256": "sha256:04f86c5cb08a125fe4a1fc6488e366bdc505147dd82a13e3d08c1239e4e49705",
      "bytes": 3934
    },
    {
      "path": "OpenAIDatabase/data/derived/profile/CORE_PROFILE.md",
      "sha256": "sha256:bec0b01730c2ece12e62a47612b1c14239dc52c80bb34a710d17d59116a1e521",
      "bytes": 3906
    }
  ],
  "time_windows": [
    "recent_7d",
    "recent_30d",
    "long_baseline"
  ],
  "entry_count": 17,
  "entries": [
    {
      "id": "dp-e3617b021a69",
      "type": "profile_signal",
      "status": "current",
      "statement": "GitHub 上的 OpenAIDatabase 应作为任意 agent 可读取的长期记忆、画像、偏好和历史上下文数据库。",
      "evidence": [
        "OpenAIDatabase/data/derived/codex/codex_agent_recommendations.json"
      ],
      "counterevidence": [
        "This redacted derived summary was not independently rechecked against its underlying sessions in v0.0.0.2."
      ],
      "confidence": "high",
      "observed_window": "recent_30d",
      "valid_until": null,
      "agent_action": "在下一次与“GitHub 上的 OpenAIDatabase 应作为任意 agent 可读取的长期记忆、画像、偏好和历史上下文数据库。”直接相关的任务中试用一次；若没有可观察收益或出现反证，立即失效。",
      "asset_candidate": "observation",
      "occurrences": 1036,
      "source_count": 1
    },
    {
      "id": "dp-24c22481a927",
      "type": "profile_signal",
      "status": "current",
      "statement": "GitHub 备份中不得提交 plaintext high-risk secrets；金融/交易 agent 使用 secret_ref 和受控本地 resolver。",
      "evidence": [
        "OpenAIDatabase/data/derived/codex/codex_agent_recommendations.json"
      ],
      "counterevidence": [
        "This redacted derived summary was not independently rechecked against its underlying sessions in v0.0.0.2."
      ],
      "confidence": "high",
      "observed_window": "recent_30d",
      "valid_until": null,
      "agent_action": "在下一次与“GitHub 备份中不得提交 plaintext high-risk secrets；金融/交易 agent 使用 secret_ref 和受控本地 resolver。”直接相关的任务中试用一次；若没有可观察收益或出现反证，立即失效。",
      "asset_candidate": "observation",
      "occurrences": 1035,
      "source_count": 1
    },
    {
      "id": "dp-0131e7df4695",
      "type": "profile_signal",
      "status": "current",
      "statement": "所有 agent 访问后都应能生成适配用户的 profile、preference、project context、rules 和 history summary。",
      "evidence": [
        "OpenAIDatabase/data/derived/codex/codex_agent_recommendations.json"
      ],
      "counterevidence": [
        "This redacted derived summary was not independently rechecked against its underlying sessions in v0.0.0.2."
      ],
      "confidence": "high",
      "observed_window": "recent_30d",
      "valid_until": null,
      "agent_action": "在下一次与“所有 agent 访问后都应能生成适配用户的 profile、preference、project context、rules 和 history summary。”直接相关的任务中试用一次；若没有可观察收益或出现反证，立即失效。",
      "asset_candidate": "observation",
      "occurrences": 759,
      "source_count": 1
    },
    {
      "id": "dp-8e45829f83b7",
      "type": "profile_signal",
      "status": "current",
      "statement": "用户明确要求使用真实 Codex / ChatGPT / GitHub 数据，不接受 mock、伪进度或只给概念演示。",
      "evidence": [
        "OpenAIDatabase/data/derived/codex/codex_agent_recommendations.json"
      ],
      "counterevidence": [
        "This redacted derived summary was not independently rechecked against its underlying sessions in v0.0.0.2."
      ],
      "confidence": "high",
      "observed_window": "recent_30d",
      "valid_until": null,
      "agent_action": "在下一次与“用户明确要求使用真实 Codex / ChatGPT / GitHub 数据，不接受 mock、伪进度或只给概念演示。”直接相关的任务中试用一次；若没有可观察收益或出现反证，立即失效。",
      "asset_candidate": "observation",
      "occurrences": 424,
      "source_count": 1
    },
    {
      "id": "dp-7048dbe33903",
      "type": "profile_signal",
      "status": "current",
      "statement": "用户说先不开始时必须先澄清需求；用户授权开始后应持续推进到可验证结果。",
      "evidence": [
        "OpenAIDatabase/data/derived/codex/codex_agent_recommendations.json"
      ],
      "counterevidence": [
        "This redacted derived summary was not independently rechecked against its underlying sessions in v0.0.0.2."
      ],
      "confidence": "high",
      "observed_window": "recent_30d",
      "valid_until": null,
      "agent_action": "在下一次与“用户说先不开始时必须先澄清需求；用户授权开始后应持续推进到可验证结果。”直接相关的任务中试用一次；若没有可观察收益或出现反证，立即失效。",
      "asset_candidate": "observation",
      "occurrences": 278,
      "source_count": 1
    },
    {
      "id": "dp-bd6e8a3c0ee6",
      "type": "profile_signal",
      "status": "current",
      "statement": "用户长期偏好中文输出；代码、API、库名、错误信息和专业术语可保留英文。",
      "evidence": [
        "OpenAIDatabase/data/derived/codex/codex_agent_recommendations.json"
      ],
      "counterevidence": [
        "This redacted derived summary was not independently rechecked against its underlying sessions in v0.0.0.2."
      ],
      "confidence": "high",
      "observed_window": "recent_30d",
      "valid_until": null,
      "agent_action": "在下一次与“用户长期偏好中文输出；代码、API、库名、错误信息和专业术语可保留英文。”直接相关的任务中试用一次；若没有可观察收益或出现反证，立即失效。",
      "asset_candidate": "observation",
      "occurrences": 212,
      "source_count": 1
    },
    {
      "id": "dp-49cab09a94bf",
      "type": "profile_signal",
      "status": "current",
      "statement": "处理记忆或行为数据后，应输出人能直接使用的话题、行动、建议、机会、ROI、能力成长和风险提醒。",
      "evidence": [
        "OpenAIDatabase/data/derived/codex/codex_agent_recommendations.json"
      ],
      "counterevidence": [
        "This redacted derived summary was not independently rechecked against its underlying sessions in v0.0.0.2."
      ],
      "confidence": "high",
      "observed_window": "recent_30d",
      "valid_until": null,
      "agent_action": "在下一次与“处理记忆或行为数据后，应输出人能直接使用的话题、行动、建议、机会、ROI、能力成长和风险提醒。”直接相关的任务中试用一次；若没有可观察收益或出现反证，立即失效。",
      "asset_candidate": "observation",
      "occurrences": 174,
      "source_count": 1
    },
    {
      "id": "dp-01da6cc16766",
      "type": "profile_signal",
      "status": "current",
      "statement": "复杂工程、研究或系统任务应输出当前阶段状态表，按严格高标准推进，并以可验证、可维护、可落地的交付为目标；部署、本地运行、PDF 报告等只在任务明确需要时作为交付要求。",
      "evidence": [
        "OpenAIDatabase/data/derived/profile/CORE_PROFILE.md"
      ],
      "counterevidence": [
        "Stable curated baseline; this source does not provide a recent observation timestamp."
      ],
      "confidence": "high",
      "observed_window": "long_baseline",
      "valid_until": null,
      "agent_action": "在下一次与“复杂工程、研究或系统任务应输出当前阶段状态表，按严格高标准推进，并以可验证、可维护、可落地的交付为目标；部署、本地运行、PDF 报告等只在任务明确需要时作为交付要求。”直接相关的任务中试用一次；若没有可观察收益或出现反证，立即失效。",
      "asset_candidate": "observation",
      "occurrences": 1,
      "source_count": 1
    },
    {
      "id": "dp-28f4d259c36e",
      "type": "profile_signal",
      "status": "current",
      "statement": "研究和决策支持任务优先使用公开、合规、授权、可验证的信息来源，避免依赖未授权或不可审计来源。",
      "evidence": [
        "OpenAIDatabase/data/derived/profile/CORE_PROFILE.md"
      ],
      "counterevidence": [
        "Stable curated baseline; this source does not provide a recent observation timestamp."
      ],
      "confidence": "high",
      "observed_window": "long_baseline",
      "valid_until": null,
      "agent_action": "在下一次与“研究和决策支持任务优先使用公开、合规、授权、可验证的信息来源，避免依赖未授权或不可审计来源。”直接相关的任务中试用一次；若没有可观察收益或出现反证，立即失效。",
      "asset_candidate": "observation",
      "occurrences": 1,
      "source_count": 1
    },
    {
      "id": "dp-3590331dfea1",
      "type": "profile_signal",
      "status": "current",
      "statement": "默认交互方式应优先使用编号选择题、多选矩阵、默认推荐项、少量必要填空、当前步骤状态表和下一步 A/B/C，避免让用户大量自由文本输入。",
      "evidence": [
        "OpenAIDatabase/data/derived/profile/CORE_PROFILE.md"
      ],
      "counterevidence": [
        "Stable curated baseline; this source does not provide a recent observation timestamp."
      ],
      "confidence": "high",
      "observed_window": "long_baseline",
      "valid_until": null,
      "agent_action": "在下一次与“默认交互方式应优先使用编号选择题、多选矩阵、默认推荐项、少量必要填空、当前步骤状态表和下一步 A/B/C，避免让用户大量自由文本输入。”直接相关的任务中试用一次；若没有可观察收益或出现反证，立即失效。",
      "asset_candidate": "observation",
      "occurrences": 1,
      "source_count": 1
    },
    {
      "id": "dp-59aa7a5a95d6",
      "type": "profile_signal",
      "status": "current",
      "statement": "如果当前环境不具备联网或外部验证能力，必须明确标注“待外部验证”，不要把未验证信息说成确定事实。",
      "evidence": [
        "OpenAIDatabase/data/derived/profile/CORE_PROFILE.md"
      ],
      "counterevidence": [
        "Stable curated baseline; this source does not provide a recent observation timestamp."
      ],
      "confidence": "high",
      "observed_window": "long_baseline",
      "valid_until": null,
      "agent_action": "在下一次与“如果当前环境不具备联网或外部验证能力，必须明确标注“待外部验证”，不要把未验证信息说成确定事实。”直接相关的任务中试用一次；若没有可观察收益或出现反证，立即失效。",
      "asset_candidate": "observation",
      "occurrences": 1,
      "source_count": 1
    },
    {
      "id": "dp-af2dbe5ccd56",
      "type": "profile_signal",
      "status": "current",
      "statement": "如果具备联网能力，涉及最新事实、官方文档、行业报告、论文、政策、价格、API 或高风险决策时，必须先检索权威来源再回答。",
      "evidence": [
        "OpenAIDatabase/data/derived/profile/CORE_PROFILE.md"
      ],
      "counterevidence": [
        "Stable curated baseline; this source does not provide a recent observation timestamp."
      ],
      "confidence": "high",
      "observed_window": "long_baseline",
      "valid_until": null,
      "agent_action": "在下一次与“如果具备联网能力，涉及最新事实、官方文档、行业报告、论文、政策、价格、API 或高风险决策时，必须先检索权威来源再回答。”直接相关的任务中试用一次；若没有可观察收益或出现反证，立即失效。",
      "asset_candidate": "observation",
      "occurrences": 1,
      "source_count": 1
    },
    {
      "id": "dp-6dedb6746760",
      "type": "asset_candidate",
      "status": "emerging",
      "statement": "派生行为数据在 8 个主题簇中检测到高频细节迭代候选（累计 227 条事件）；下一次相关任务应先冻结质量上限，达到验收后停止扩张。",
      "evidence": [
        "OpenAIDatabase/data/derived/behavior_intelligence/low_value_loops.json"
      ],
      "counterevidence": [
        "The aggregation may reflect a temporary period of concentrated development rather than a durable work pattern."
      ],
      "confidence": "medium",
      "observed_window": "recent_30d",
      "valid_until": null,
      "agent_action": "在下一次与“派生行为数据在 8 个主题簇中检测到高频细节迭代候选（累计 227 条事件）；下一次相关任务应先冻结质量上限，达到验收后停止扩张。”直接相关的任务中试用一次；若没有可观察收益或出现反证，立即失效。",
      "asset_candidate": "workflow",
      "occurrences": 227,
      "source_count": 1
    },
    {
      "id": "dp-c451522dd196",
      "type": "asset_candidate",
      "status": "emerging",
      "statement": "派生行为数据在 5 个主题簇中检测到 scope creep 候选（累计 181 条事件）；下一次相关任务应先冻结 run contract、非目标和写入边界。",
      "evidence": [
        "OpenAIDatabase/data/derived/behavior_intelligence/low_value_loops.json"
      ],
      "counterevidence": [
        "The aggregation may reflect a temporary period of concentrated development rather than a durable work pattern."
      ],
      "confidence": "medium",
      "observed_window": "recent_30d",
      "valid_until": null,
      "agent_action": "在下一次与“派生行为数据在 5 个主题簇中检测到 scope creep 候选（累计 181 条事件）；下一次相关任务应先冻结 run contract、非目标和写入边界。”直接相关的任务中试用一次；若没有可观察收益或出现反证，立即失效。",
      "asset_candidate": "workflow",
      "occurrences": 181,
      "source_count": 1
    },
    {
      "id": "dp-391a0586617b",
      "type": "asset_candidate",
      "status": "emerging",
      "statement": "派生行为数据在 13 个主题簇中检测到反复返工候选（累计 177 条事件）；下一次相关任务应先复用现有资产并设置一次复跑验收。",
      "evidence": [
        "OpenAIDatabase/data/derived/behavior_intelligence/low_value_loops.json"
      ],
      "counterevidence": [
        "The aggregation may reflect a temporary period of concentrated development rather than a durable work pattern."
      ],
      "confidence": "medium",
      "observed_window": "recent_30d",
      "valid_until": null,
      "agent_action": "在下一次与“派生行为数据在 13 个主题簇中检测到反复返工候选（累计 177 条事件）；下一次相关任务应先复用现有资产并设置一次复跑验收。”直接相关的任务中试用一次；若没有可观察收益或出现反证，立即失效。",
      "asset_candidate": "workflow",
      "occurrences": 177,
      "source_count": 1
    },
    {
      "id": "dp-efb1c46181b4",
      "type": "asset_candidate",
      "status": "emerging",
      "statement": "派生行为数据在 5 个主题簇中检测到多次讨论但缺少落地产物（累计 54 条事件）；下一次相关任务先收口为一个交付件、一个验收命令和一个停止条件。",
      "evidence": [
        "OpenAIDatabase/data/derived/behavior_intelligence/low_value_loops.json"
      ],
      "counterevidence": [
        "The aggregation may reflect a temporary period of concentrated development rather than a durable work pattern."
      ],
      "confidence": "medium",
      "observed_window": "recent_30d",
      "valid_until": null,
      "agent_action": "在下一次与“派生行为数据在 5 个主题簇中检测到多次讨论但缺少落地产物（累计 54 条事件）；下一次相关任务先收口为一个交付件、一个验收命令和一个停止条件。”直接相关的任务中试用一次；若没有可观察收益或出现反证，立即失效。",
      "asset_candidate": "workflow",
      "occurrences": 54,
      "source_count": 1
    },
    {
      "id": "dp-eebd14f83885",
      "type": "profile_signal",
      "status": "hypothesis",
      "statement": "用户长期关注 AI 时代对社会、工作方式、沟通、人类能力边界和个人突破路径的影响；讨论这类问题时应先做深度研究，再输出结构化机会、风险和行动建议。",
      "evidence": [
        "OpenAIDatabase/data/derived/profile/CORE_PROFILE.md"
      ],
      "counterevidence": [
        "Stable curated baseline; this source does not provide a recent observation timestamp."
      ],
      "confidence": "medium",
      "observed_window": "long_baseline",
      "valid_until": null,
      "agent_action": "在下一次与“用户长期关注 AI 时代对社会、工作方式、沟通、人类能力边界和个人突破路径的影响；讨论这类问题时应先做深度研究，再输出结构化机会、风险和行动建议。”直接相关的任务中试用一次；若没有可观察收益或出现反证，立即失效。",
      "asset_candidate": "observation",
      "occurrences": 1,
      "source_count": 1
    }
  ]
}
---

# Dynamic Personal Profile

## 先看结论

- **current / high**：GitHub 上的 OpenAIDatabase 应作为任意 agent 可读取的长期记忆、画像、偏好和历史上下文数据库。
- **current / high**：GitHub 备份中不得提交 plaintext high-risk secrets；金融/交易 agent 使用 secret_ref 和受控本地 resolver。
- **current / high**：所有 agent 访问后都应能生成适配用户的 profile、preference、project context、rules 和 history summary。
- **current / high**：用户明确要求使用真实 Codex / ChatGPT / GitHub 数据，不接受 mock、伪进度或只给概念演示。
- **current / high**：用户说先不开始时必须先澄清需求；用户授权开始后应持续推进到可验证结果。
- **current / high**：用户长期偏好中文输出；代码、API、库名、错误信息和专业术语可保留英文。
- **current / high**：处理记忆或行为数据后，应输出人能直接使用的话题、行动、建议、机会、ROI、能力成长和风险提醒。
- **current / high**：复杂工程、研究或系统任务应输出当前阶段状态表，按严格高标准推进，并以可验证、可维护、可落地的交付为目标；部署、本地运行、PDF 报告等只在任务明确需要时作为交付要求。

## 变化条目

### dp-e3617b021a69｜current

- 类型：`profile_signal`；资产候选：`observation`
- 观察：GitHub 上的 OpenAIDatabase 应作为任意 agent 可读取的长期记忆、画像、偏好和历史上下文数据库。
- 证据：`OpenAIDatabase/data/derived/codex/codex_agent_recommendations.json`
- 反证：This redacted derived summary was not independently rechecked against its underlying sessions in v0.0.0.2.
- 置信度：`high`；时间窗口：`recent_30d`
- 临时 Agent 行为：在下一次与“GitHub 上的 OpenAIDatabase 应作为任意 agent 可读取的长期记忆、画像、偏好和历史上下文数据库。”直接相关的任务中试用一次；若没有可观察收益或出现反证，立即失效。

### dp-24c22481a927｜current

- 类型：`profile_signal`；资产候选：`observation`
- 观察：GitHub 备份中不得提交 plaintext high-risk secrets；金融/交易 agent 使用 secret_ref 和受控本地 resolver。
- 证据：`OpenAIDatabase/data/derived/codex/codex_agent_recommendations.json`
- 反证：This redacted derived summary was not independently rechecked against its underlying sessions in v0.0.0.2.
- 置信度：`high`；时间窗口：`recent_30d`
- 临时 Agent 行为：在下一次与“GitHub 备份中不得提交 plaintext high-risk secrets；金融/交易 agent 使用 secret_ref 和受控本地 resolver。”直接相关的任务中试用一次；若没有可观察收益或出现反证，立即失效。

### dp-0131e7df4695｜current

- 类型：`profile_signal`；资产候选：`observation`
- 观察：所有 agent 访问后都应能生成适配用户的 profile、preference、project context、rules 和 history summary。
- 证据：`OpenAIDatabase/data/derived/codex/codex_agent_recommendations.json`
- 反证：This redacted derived summary was not independently rechecked against its underlying sessions in v0.0.0.2.
- 置信度：`high`；时间窗口：`recent_30d`
- 临时 Agent 行为：在下一次与“所有 agent 访问后都应能生成适配用户的 profile、preference、project context、rules 和 history summary。”直接相关的任务中试用一次；若没有可观察收益或出现反证，立即失效。

### dp-8e45829f83b7｜current

- 类型：`profile_signal`；资产候选：`observation`
- 观察：用户明确要求使用真实 Codex / ChatGPT / GitHub 数据，不接受 mock、伪进度或只给概念演示。
- 证据：`OpenAIDatabase/data/derived/codex/codex_agent_recommendations.json`
- 反证：This redacted derived summary was not independently rechecked against its underlying sessions in v0.0.0.2.
- 置信度：`high`；时间窗口：`recent_30d`
- 临时 Agent 行为：在下一次与“用户明确要求使用真实 Codex / ChatGPT / GitHub 数据，不接受 mock、伪进度或只给概念演示。”直接相关的任务中试用一次；若没有可观察收益或出现反证，立即失效。

### dp-7048dbe33903｜current

- 类型：`profile_signal`；资产候选：`observation`
- 观察：用户说先不开始时必须先澄清需求；用户授权开始后应持续推进到可验证结果。
- 证据：`OpenAIDatabase/data/derived/codex/codex_agent_recommendations.json`
- 反证：This redacted derived summary was not independently rechecked against its underlying sessions in v0.0.0.2.
- 置信度：`high`；时间窗口：`recent_30d`
- 临时 Agent 行为：在下一次与“用户说先不开始时必须先澄清需求；用户授权开始后应持续推进到可验证结果。”直接相关的任务中试用一次；若没有可观察收益或出现反证，立即失效。

### dp-bd6e8a3c0ee6｜current

- 类型：`profile_signal`；资产候选：`observation`
- 观察：用户长期偏好中文输出；代码、API、库名、错误信息和专业术语可保留英文。
- 证据：`OpenAIDatabase/data/derived/codex/codex_agent_recommendations.json`
- 反证：This redacted derived summary was not independently rechecked against its underlying sessions in v0.0.0.2.
- 置信度：`high`；时间窗口：`recent_30d`
- 临时 Agent 行为：在下一次与“用户长期偏好中文输出；代码、API、库名、错误信息和专业术语可保留英文。”直接相关的任务中试用一次；若没有可观察收益或出现反证，立即失效。

### dp-49cab09a94bf｜current

- 类型：`profile_signal`；资产候选：`observation`
- 观察：处理记忆或行为数据后，应输出人能直接使用的话题、行动、建议、机会、ROI、能力成长和风险提醒。
- 证据：`OpenAIDatabase/data/derived/codex/codex_agent_recommendations.json`
- 反证：This redacted derived summary was not independently rechecked against its underlying sessions in v0.0.0.2.
- 置信度：`high`；时间窗口：`recent_30d`
- 临时 Agent 行为：在下一次与“处理记忆或行为数据后，应输出人能直接使用的话题、行动、建议、机会、ROI、能力成长和风险提醒。”直接相关的任务中试用一次；若没有可观察收益或出现反证，立即失效。

### dp-01da6cc16766｜current

- 类型：`profile_signal`；资产候选：`observation`
- 观察：复杂工程、研究或系统任务应输出当前阶段状态表，按严格高标准推进，并以可验证、可维护、可落地的交付为目标；部署、本地运行、PDF 报告等只在任务明确需要时作为交付要求。
- 证据：`OpenAIDatabase/data/derived/profile/CORE_PROFILE.md`
- 反证：Stable curated baseline; this source does not provide a recent observation timestamp.
- 置信度：`high`；时间窗口：`long_baseline`
- 临时 Agent 行为：在下一次与“复杂工程、研究或系统任务应输出当前阶段状态表，按严格高标准推进，并以可验证、可维护、可落地的交付为目标；部署、本地运行、PDF 报告等只在任务明确需要时作为交付要求。”直接相关的任务中试用一次；若没有可观察收益或出现反证，立即失效。

### dp-28f4d259c36e｜current

- 类型：`profile_signal`；资产候选：`observation`
- 观察：研究和决策支持任务优先使用公开、合规、授权、可验证的信息来源，避免依赖未授权或不可审计来源。
- 证据：`OpenAIDatabase/data/derived/profile/CORE_PROFILE.md`
- 反证：Stable curated baseline; this source does not provide a recent observation timestamp.
- 置信度：`high`；时间窗口：`long_baseline`
- 临时 Agent 行为：在下一次与“研究和决策支持任务优先使用公开、合规、授权、可验证的信息来源，避免依赖未授权或不可审计来源。”直接相关的任务中试用一次；若没有可观察收益或出现反证，立即失效。

### dp-3590331dfea1｜current

- 类型：`profile_signal`；资产候选：`observation`
- 观察：默认交互方式应优先使用编号选择题、多选矩阵、默认推荐项、少量必要填空、当前步骤状态表和下一步 A/B/C，避免让用户大量自由文本输入。
- 证据：`OpenAIDatabase/data/derived/profile/CORE_PROFILE.md`
- 反证：Stable curated baseline; this source does not provide a recent observation timestamp.
- 置信度：`high`；时间窗口：`long_baseline`
- 临时 Agent 行为：在下一次与“默认交互方式应优先使用编号选择题、多选矩阵、默认推荐项、少量必要填空、当前步骤状态表和下一步 A/B/C，避免让用户大量自由文本输入。”直接相关的任务中试用一次；若没有可观察收益或出现反证，立即失效。

### dp-59aa7a5a95d6｜current

- 类型：`profile_signal`；资产候选：`observation`
- 观察：如果当前环境不具备联网或外部验证能力，必须明确标注“待外部验证”，不要把未验证信息说成确定事实。
- 证据：`OpenAIDatabase/data/derived/profile/CORE_PROFILE.md`
- 反证：Stable curated baseline; this source does not provide a recent observation timestamp.
- 置信度：`high`；时间窗口：`long_baseline`
- 临时 Agent 行为：在下一次与“如果当前环境不具备联网或外部验证能力，必须明确标注“待外部验证”，不要把未验证信息说成确定事实。”直接相关的任务中试用一次；若没有可观察收益或出现反证，立即失效。

### dp-af2dbe5ccd56｜current

- 类型：`profile_signal`；资产候选：`observation`
- 观察：如果具备联网能力，涉及最新事实、官方文档、行业报告、论文、政策、价格、API 或高风险决策时，必须先检索权威来源再回答。
- 证据：`OpenAIDatabase/data/derived/profile/CORE_PROFILE.md`
- 反证：Stable curated baseline; this source does not provide a recent observation timestamp.
- 置信度：`high`；时间窗口：`long_baseline`
- 临时 Agent 行为：在下一次与“如果具备联网能力，涉及最新事实、官方文档、行业报告、论文、政策、价格、API 或高风险决策时，必须先检索权威来源再回答。”直接相关的任务中试用一次；若没有可观察收益或出现反证，立即失效。

### dp-6dedb6746760｜emerging

- 类型：`asset_candidate`；资产候选：`workflow`
- 观察：派生行为数据在 8 个主题簇中检测到高频细节迭代候选（累计 227 条事件）；下一次相关任务应先冻结质量上限，达到验收后停止扩张。
- 证据：`OpenAIDatabase/data/derived/behavior_intelligence/low_value_loops.json`
- 反证：The aggregation may reflect a temporary period of concentrated development rather than a durable work pattern.
- 置信度：`medium`；时间窗口：`recent_30d`
- 临时 Agent 行为：在下一次与“派生行为数据在 8 个主题簇中检测到高频细节迭代候选（累计 227 条事件）；下一次相关任务应先冻结质量上限，达到验收后停止扩张。”直接相关的任务中试用一次；若没有可观察收益或出现反证，立即失效。

### dp-c451522dd196｜emerging

- 类型：`asset_candidate`；资产候选：`workflow`
- 观察：派生行为数据在 5 个主题簇中检测到 scope creep 候选（累计 181 条事件）；下一次相关任务应先冻结 run contract、非目标和写入边界。
- 证据：`OpenAIDatabase/data/derived/behavior_intelligence/low_value_loops.json`
- 反证：The aggregation may reflect a temporary period of concentrated development rather than a durable work pattern.
- 置信度：`medium`；时间窗口：`recent_30d`
- 临时 Agent 行为：在下一次与“派生行为数据在 5 个主题簇中检测到 scope creep 候选（累计 181 条事件）；下一次相关任务应先冻结 run contract、非目标和写入边界。”直接相关的任务中试用一次；若没有可观察收益或出现反证，立即失效。

### dp-391a0586617b｜emerging

- 类型：`asset_candidate`；资产候选：`workflow`
- 观察：派生行为数据在 13 个主题簇中检测到反复返工候选（累计 177 条事件）；下一次相关任务应先复用现有资产并设置一次复跑验收。
- 证据：`OpenAIDatabase/data/derived/behavior_intelligence/low_value_loops.json`
- 反证：The aggregation may reflect a temporary period of concentrated development rather than a durable work pattern.
- 置信度：`medium`；时间窗口：`recent_30d`
- 临时 Agent 行为：在下一次与“派生行为数据在 13 个主题簇中检测到反复返工候选（累计 177 条事件）；下一次相关任务应先复用现有资产并设置一次复跑验收。”直接相关的任务中试用一次；若没有可观察收益或出现反证，立即失效。

### dp-efb1c46181b4｜emerging

- 类型：`asset_candidate`；资产候选：`workflow`
- 观察：派生行为数据在 5 个主题簇中检测到多次讨论但缺少落地产物（累计 54 条事件）；下一次相关任务先收口为一个交付件、一个验收命令和一个停止条件。
- 证据：`OpenAIDatabase/data/derived/behavior_intelligence/low_value_loops.json`
- 反证：The aggregation may reflect a temporary period of concentrated development rather than a durable work pattern.
- 置信度：`medium`；时间窗口：`recent_30d`
- 临时 Agent 行为：在下一次与“派生行为数据在 5 个主题簇中检测到多次讨论但缺少落地产物（累计 54 条事件）；下一次相关任务先收口为一个交付件、一个验收命令和一个停止条件。”直接相关的任务中试用一次；若没有可观察收益或出现反证，立即失效。

### dp-eebd14f83885｜hypothesis

- 类型：`profile_signal`；资产候选：`observation`
- 观察：用户长期关注 AI 时代对社会、工作方式、沟通、人类能力边界和个人突破路径的影响；讨论这类问题时应先做深度研究，再输出结构化机会、风险和行动建议。
- 证据：`OpenAIDatabase/data/derived/profile/CORE_PROFILE.md`
- 反证：Stable curated baseline; this source does not provide a recent observation timestamp.
- 置信度：`medium`；时间窗口：`long_baseline`
- 临时 Agent 行为：在下一次与“用户长期关注 AI 时代对社会、工作方式、沟通、人类能力边界和个人突破路径的影响；讨论这类问题时应先做深度研究，再输出结构化机会、风险和行动建议。”直接相关的任务中试用一次；若没有可观察收益或出现反证，立即失效。

## 可立即试用的 Agent 行为

- `dp-e3617b021a69`：在下一次与“GitHub 上的 OpenAIDatabase 应作为任意 agent 可读取的长期记忆、画像、偏好和历史上下文数据库。”直接相关的任务中试用一次；若没有可观察收益或出现反证，立即失效。
- `dp-24c22481a927`：在下一次与“GitHub 备份中不得提交 plaintext high-risk secrets；金融/交易 agent 使用 secret_ref 和受控本地 resolver。”直接相关的任务中试用一次；若没有可观察收益或出现反证，立即失效。
- `dp-0131e7df4695`：在下一次与“所有 agent 访问后都应能生成适配用户的 profile、preference、project context、rules 和 history summary。”直接相关的任务中试用一次；若没有可观察收益或出现反证，立即失效。
- `dp-8e45829f83b7`：在下一次与“用户明确要求使用真实 Codex / ChatGPT / GitHub 数据，不接受 mock、伪进度或只给概念演示。”直接相关的任务中试用一次；若没有可观察收益或出现反证，立即失效。
- `dp-7048dbe33903`：在下一次与“用户说先不开始时必须先澄清需求；用户授权开始后应持续推进到可验证结果。”直接相关的任务中试用一次；若没有可观察收益或出现反证，立即失效。
- `dp-bd6e8a3c0ee6`：在下一次与“用户长期偏好中文输出；代码、API、库名、错误信息和专业术语可保留英文。”直接相关的任务中试用一次；若没有可观察收益或出现反证，立即失效。
- `dp-49cab09a94bf`：在下一次与“处理记忆或行为数据后，应输出人能直接使用的话题、行动、建议、机会、ROI、能力成长和风险提醒。”直接相关的任务中试用一次；若没有可观察收益或出现反证，立即失效。
- `dp-01da6cc16766`：在下一次与“复杂工程、研究或系统任务应输出当前阶段状态表，按严格高标准推进，并以可验证、可维护、可落地的交付为目标；部署、本地运行、PDF 报告等只在任务明确需要时作为交付要求。”直接相关的任务中试用一次；若没有可观察收益或出现反证，立即失效。
- `dp-28f4d259c36e`：在下一次与“研究和决策支持任务优先使用公开、合规、授权、可验证的信息来源，避免依赖未授权或不可审计来源。”直接相关的任务中试用一次；若没有可观察收益或出现反证，立即失效。
- `dp-3590331dfea1`：在下一次与“默认交互方式应优先使用编号选择题、多选矩阵、默认推荐项、少量必要填空、当前步骤状态表和下一步 A/B/C，避免让用户大量自由文本输入。”直接相关的任务中试用一次；若没有可观察收益或出现反证，立即失效。
- `dp-59aa7a5a95d6`：在下一次与“如果当前环境不具备联网或外部验证能力，必须明确标注“待外部验证”，不要把未验证信息说成确定事实。”直接相关的任务中试用一次；若没有可观察收益或出现反证，立即失效。
- `dp-af2dbe5ccd56`：在下一次与“如果具备联网能力，涉及最新事实、官方文档、行业报告、论文、政策、价格、API 或高风险决策时，必须先检索权威来源再回答。”直接相关的任务中试用一次；若没有可观察收益或出现反证，立即失效。
- `dp-6dedb6746760`：在下一次与“派生行为数据在 8 个主题簇中检测到高频细节迭代候选（累计 227 条事件）；下一次相关任务应先冻结质量上限，达到验收后停止扩张。”直接相关的任务中试用一次；若没有可观察收益或出现反证，立即失效。
- `dp-c451522dd196`：在下一次与“派生行为数据在 5 个主题簇中检测到 scope creep 候选（累计 181 条事件）；下一次相关任务应先冻结 run contract、非目标和写入边界。”直接相关的任务中试用一次；若没有可观察收益或出现反证，立即失效。
- `dp-391a0586617b`：在下一次与“派生行为数据在 13 个主题簇中检测到反复返工候选（累计 177 条事件）；下一次相关任务应先复用现有资产并设置一次复跑验收。”直接相关的任务中试用一次；若没有可观察收益或出现反证，立即失效。
- `dp-efb1c46181b4`：在下一次与“派生行为数据在 5 个主题簇中检测到多次讨论但缺少落地产物（累计 54 条事件）；下一次相关任务先收口为一个交付件、一个验收命令和一个停止条件。”直接相关的任务中试用一次；若没有可观察收益或出现反证，立即失效。

## Recurring Asset 候选

- `dp-6dedb6746760` / `workflow`：一次真实任务验证前保持 `pending`。
- `dp-c451522dd196` / `workflow`：一次真实任务验证前保持 `pending`。
- `dp-391a0586617b` / `workflow`：一次真实任务验证前保持 `pending`。
- `dp-efb1c46181b4` / `workflow`：一次真实任务验证前保持 `pending`。

## 边界与不确定性

- 本文件来自脱敏派生数据，不是原始记录，也不是稳定核心画像。
- 没有源时间戳时不推断精确发生日期。
- 当前脚本不调用 LLM，不做语义事实确认，不自动写回长期记忆。
- `CORE_PROFILE.md`、Custom Instructions、AGENTS.md 和 Memory Atlas canonical records 不会被本次运行修改。
