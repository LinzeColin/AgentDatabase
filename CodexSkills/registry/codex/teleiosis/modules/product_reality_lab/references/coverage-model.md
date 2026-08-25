# Coverage Model

## 八维向量

```json
{
  "surface": "功能和系统表面是否被盘点并触达",
  "state": "关键角色/数据/Flag/环境状态是否可达",
  "transition": "正向、失败、恢复和顺序转移是否覆盖",
  "role": "允许、拒绝、越权和租户隔离是否覆盖",
  "data": "正常、边界、非法、重复、损坏、时间和迁移数据",
  "fault": "依赖、网络、资源、并发、崩溃和恢复",
  "oracle": "结果正确性是否有独立判据",
  "evidence": "结论是否可定位、可重放、带版本/hash"
}
```

## 关键项 Gate

关键项默认必须 100% covered 或逐项 waiver。非关键项使用风险预算，不以虚假的 100% 为目标。

## Item-level ledger 与自动反算

每个维度必须维护 `items[]`，每项至少包含：

```text
item_id + source_ref + critical + status
+ evidence_refs + waiver_id
```

`critical_total / critical_covered / critical_waived / noncritical_total / noncritical_covered` 只是由 items 反算的缓存。校验同时比较：

1. Catalog 对象与 Coverage Item 是否一一对应；
2. Criticality 是否与源对象一致；
3. `COVERED` 是否至少有一个已索引证据；
4. `WAIVED` 是否引用未过期的 Owner waiver；
5. 顶层 evidence/waiver 汇总是否等于 item-level 并集。

任意不一致均是 integrity failure，而不是普通低覆盖。

## 状态签名

建议签名字段：

```text
route/task + role + auth + tenant + flags + fixture
+ browser/device + locale/timezone
+ canonical AX/DOM summary + key world-state digest
```

签名用于去重，不用于证明业务正确。

## 组合爆炸处理

- 少量关键变量：完整枚举。
- 多变量配置：2-way 起步，高风险交互提高到 3–6 way。
- 操作顺序：sequence covering array。
- 有状态对象/API：rule/state-machine generation。
- 语义/可用性未知：模型探索 + 真人任务。

## 反作弊

Coverage denominator 必须来自源代码清单、运行时清单、API/Data Schema 和业务任务的并集；删除清单项需要证据和 owner 决策。

使用 `sync-coverage` 从当前目录自动重建 inventory；不得直接把总数改为 100%。
