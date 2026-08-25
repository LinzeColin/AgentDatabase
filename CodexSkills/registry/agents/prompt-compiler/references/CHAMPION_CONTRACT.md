# 全维冠军合同

## 目标

Prompt Compiler 既与 GEPA、AutoResearch、Meta-Harness、Promptfoo 在同层竞争，也把它们作为下层能力源。发布条件不是“综合分最高”，而是：

```text
全部必选竞品实际运行
AND 全部冻结维度都有证据
AND 每个维度逐一排名第一
AND 总体第一
AND 无硬失败
AND 独立终审、回归、红队、外部证据与 CI 均通过
```

## 严格逐维判定

每个竞品、每个维度形成配对差值样本。默认使用 95% 配对 Bootstrap 区间：

- 下界 `> minimum_margin`：`STRICTLY_FIRST`；
- 双方均为 100% 且下界不低于允许边界：`TIED_FIRST_AT_CEILING`；
- 上界 `< -minimum_margin`：`PEER_BETTER`；
- 其余：`NOT_SEPARATED`；
- 任一侧无样本：`MISSING_EVIDENCE`。

低于 100% 的并列不通过。原因是“观察均值相同”不能证明 Prompt Compiler 第一，也可能只是案例缺乏区分度。

## 动态维度冻结

内置 15 个维度始终纳入。项目配置可添加 `champion.additional_dimensions`；验证阶段实际出现的评分维度在 `auto_freeze_discovered_dimensions=true` 时也会自动纳入。最终测试打开后维度集合不得变化。

附加维度必须：

1. 名称稳定且符合机器字段规则；
2. 0–1 规范化；
3. 越高越好；
4. 对所有终审候选逐行输出；
5. 有业务定义、Oracle 和失败含义。

## 状态机

| 状态 | 条件 | 发布行为 |
|---|---|---|
| CHAMPION_PASS | 每个必选竞品、每个冻结维度均严格第一或满分共同第一 | 才能进入发布门 |
| CHAMPION_NOT_PROVEN | 缺竞品、缺维度、区间重叠或低于满分并列 | 保持原版，补证据或继续优化 |
| CHAMPION_REJECTED | 至少一项 `PEER_BETTER` | 针对差距整改，不发布 |

## 反作弊约束

- 不允许删除表现更好的竞品；
- 不允许优化后修改测试集、权重、阈值或 Oracle；
- 不允许竞品和 Prompt Compiler 使用不同数据或不同最终评委；
- 不允许把外部工具自报分直接写入冠军表；
- 不允许只保留最好一次；
- 不允许用平均分抵消硬失败或最弱切片；
- 不允许在最终测试打开后更换候选；
- 不允许篡改报告中的 `release_allowed` 代替独立证据文件。

## 结论范围

冠军结论绑定数据封印哈希、模型稳定身份、竞品版本、总预算、预算分配、重复次数、维度集合、最终评委和代码版本。任何一项变化都需要重新运行同场竞技。
