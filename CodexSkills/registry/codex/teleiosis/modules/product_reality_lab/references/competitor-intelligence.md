# Competitor & Open-source Intelligence Protocol

## 参考对象五分法

- Direct：解决同一用户、同一任务。
- Adjacent：解决相邻任务或不同用户。
- Substitute：用不同机制替代同一结果。
- Manual workaround：Excel、人工、群聊、脚本等现实替代。
- OSS analogue：可读源码和 Issue 的公开实现。

## 证据优先级

1. 官方产品、文档、API、Changelog、公开 Demo。
2. 原始开源仓库、Release、Issue、讨论、许可证。
3. 真实用户 Review、论坛、支持材料。
4. 二手评测仅作为发现线索，关键结论回到一手来源。

## 同任务 Benchmark

不要比较功能名称数量。对相同任务记录：

- 起始状态与输入；
- 步骤和认知负担；
- 成功结果和时间；
- 错误预防、反馈和恢复；
- 可观测性、导出、权限和审计；
- 失败路径、限制和成本；
- 用户证据与置信度。

## 借鉴决策

每个候选模式标记：

- `ADOPT`：证据充分，适合本产品。
- `ADAPT`：机制有价值，但需重构以适配约束。
- `DIFFERENTIATE`：竞品弱点可形成优势。
- `REJECT`：复杂度、风险或证据不足。
- `DEFER`：需真实 Field 数据。

## Provenance

任何代码、设计资产或文本复用必须记录 exact source、version/commit、license、copyright/notice、modified files、allowed use 和 reviewer。
