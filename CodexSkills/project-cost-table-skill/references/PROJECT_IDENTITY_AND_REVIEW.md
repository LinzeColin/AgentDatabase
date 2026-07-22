# 项目身份主数据与冲突处理

R4 在任何业务事实纳入项目成本前，要求唯一且在截止日有效的：

```text
canonical_project_id + legal_entity_id + wbs_or_cost_code + valid_at
```

## 最终匹配顺序

1. 精确且有效的项目、法人主体与 WBS/成本码组合；
2. 精确合同 ID；
3. 精确受治理来源系统 ID；
4. 有证据绑定的显式 mapping resolution；
5. 仅生成候选：项目编号、项目名称、客户、自由文本或金额相似度。

候选字段永远不能直接形成最终映射；不做模糊匹配，不按自由文本或金额自动归项目。每条 `APPROVED` 数据映射至少绑定一个合同 ID 和一条 hash-bound 证据。大小写敏感，只接受已完成 NFC 规范化且无首尾空格的标识。

## Fail-closed 门禁

以下任一情况均输出 `BLOCKED_IDENTITY`、候选记录和 `P0` 数据治理 review task：有效期重叠、一对多别名、多活动匹配、合同与项目冲突、受治理标识冲突、跨法人主体歧义、主数据或 resolution 过期、主键不完整、只有候选字段、完全未映射。Identity-master hash 同时绑定策略文件 SHA、所有映射、有效期、resolution 与证据引用；其中任一变化都会使旧 lookup 失效。

这些门禁不能通过一般性“允许省略”授权绕过。用户可补充合格证据，或明确移除受影响项目/Metric 后重新运行。已验证映射、候选/冲突映射、历史映射和 review task 分目录写入 `private_runtime` 的不可覆盖记录；公共摘要只输出聚合计数。

## 公司流程边界

`project_record.identity_status=APPROVED` 只表示“证据合格的数据映射”，`review_task.status` 也只表示数据治理任务状态。二者都不代表财务负责人、授权人或公司内部审批。Skill 不设置负责人、不管理公司审批；全部数据与产品校验通过后直接生成最终版本，生成后由操作人按公司现有内部流程处理。

跨主体报告仅可构造保留 `legal_entity_id`、`wbs_or_cost_code` 和 identity record reference 的视图，不得破坏性合并主体维度或冲销未建模的内部往来。
