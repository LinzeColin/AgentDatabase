# 专家团队输出合同

## 执行波次

1. G0：冻结目标、假设、证伪条件和改判触发器。
2. G1：人物专家在隔离工作包内形成 claim-linked 制品。
3. G2：对抗者寻找反证、替代解释和相关性错误。
4. G3：独立复审检查事实、边界、完整性、可执行性和制品。
5. G4：裁判按冻结判据选择方案，不按多数票。
6. G5：整合者输出一个最终成品和 Team Delta Card。

## 人物贡献最小结构

```json
{
  "claim": "bounded conclusion",
  "claim_ids": ["own-claim-id"],
  "evidence": ["dated source or fact lane"],
  "assumptions": [],
  "failure_conditions": [],
  "artifact": "mergeable output"
}
```

无法引用自身 claim 的人物特有观点视为未发生。历史人物不能替代当前事实。

## 用户主输出

只显示结论与下一步、已完成工作、改变结论的分歧、风险和未知、Team Delta Card。完整路由和 claim trace 默认进入审计附件。
