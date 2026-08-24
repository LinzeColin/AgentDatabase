# 评分合同

## 评分对象

评分器衡量 Prompt 的**结构规格覆盖率**，不是视频成片质量。它不能替代模型生成、人工观看或独立验收。

## 15 个维度

| 维度 | 默认权重 | 关注点 |
|---|---:|---|
| Intent Fidelity | 10% | 是否保持原始目标和关键语义 |
| Constraint Preservation | 10% | 硬约束是否逐项保留 |
| Method Fit | 8% | 是否符合 T2V/I2V/Edit/EDL 等路线结构 |
| Visual Executability | 8% | 是否从抽象词转成可见行为 |
| Shot & Camera | 8% | 景别、机位、唯一主要运镜是否协调 |
| Temporal Action Logic | 8% | 动作预算、先后、时长和节拍 |
| Continuity & Identity | 7% | 人物、产品、空间、光线和物理不变量 |
| Model/Input Fit | 8% | 模型是否已核验、输入模式是否匹配 |
| Prompt Density | 6% | 既不形容词堆积，也不过度重述参考图 |
| Audio/Dialogue | 5% | 对白、环境声、音效、音乐或静音策略 |
| Industrial Physics | 5% | 工业预设适用；工具—工件—轨迹—材料响应 |
| Micro-performance | 4% | 人物预设适用；触发、视线、生理和余韵 |
| Reference-role Clarity | 4% | 参考模式适用；每个素材的角色和保留程度 |
| End State | 4% | 动作是否落在稳定、可验收的结尾 |
| Evidence Boundary & Repairability | 5% | 未知/证据边界、保留/修改和回退路径 |

不适用维度从分母移除并重新归一化。

## 硬门槛

以下任一出现，候选直接阻断：

- 硬约束缺失；
- I2V 没有保持项；
- Reference 没有素材角色；
- V2V/Edit 没有 preserve 或 change-only；
- 剪辑计划没有素材 ID/时间码；
- 锁定镜头与强移动镜头冲突；
- 极短镜头动作预算严重超载；
- 把 AIGC 3D 当成工程结果；
- 工业镜头出现无证据的客户/性能结论；
- 使用已退休模型作为默认而未核实。

## 证据状态必须独立呈现

```text
Structural specification score: 0–100%
Native-model generation evidence: NOT_RUN / PARTIAL / RUN
Human visual review: NOT_RUN / PARTIAL / RUN
External verifier: NOT_RUN / PASS / FAIL / BLOCKED
```

`96% 结构分 + NOT_RUN 真实生成` 仍然只是高覆盖 Prompt 候选，不是 96% 成片质量。

## 竞品矩阵

`research/comparison_matrix.csv` 的百分比是对当前用户目标的机制覆盖编码，不能解释为项目绝对质量。`evidence_confidence_percent` 单独记录来源质量，不能与 Goal Fit 混为一项。
