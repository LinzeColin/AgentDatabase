# 团队路由策略

## 原则

- 不让用户选择身份；从任务内部推断。
- 人物专家以正向解决问题为主，不把人物模型当作自动权威。
- 复审、裁判、反证使用中立功能协议，与正向方案隔离。
- 只选证据支持、场景相关、边界允许且能带来新增角度的人物。
- 输出候选评分、排除理由、角色隔离和不足状态，便于审计。

## 默认角色模板

| 角色 | 类型 | 任务 |
|---|---|---|
| persona-solver | 人物正向专家 | 按已证明能力形成独立方案 |
| evidence-researcher | 中立正向 | 补事实、来源与当前性 |
| execution-planner | 中立正向 | 把方案变成步骤、资源与停止条件 |
| synthesis-lead | 中立正向 | 合并互补方案，不抹平分歧 |
| counterevidence-analyst | 中立控制 | 找最强反证和替代解释 |
| independent-reviewer | 中立控制 | 复核证据、遗漏、边界和可执行性 |
| decision-judge | 中立控制 | 按预先 rubric 裁决，不参与生成 |

人物库存足够时，优先增加 `persona-solver`，并减少中立正向补位；三个控制角色始终保留。

## 输出契约

路由计划至少包含：

- `status`
- `inferred_identity`
- `inferred_scenario`
- `requested_size` / `actual_size`
- `selected_roles`
- `excluded_candidates`
- `control_roles`
- `separation_protocol`
- `limitations`

`status=ready` 只表示路由结构满足，不表示任务结论已经正确。无合格人物时为 `insufficient_roster`。
