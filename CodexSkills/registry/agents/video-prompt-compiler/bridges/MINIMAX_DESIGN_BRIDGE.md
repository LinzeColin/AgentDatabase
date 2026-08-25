# MiniMax Design 桥接 v0.0.0.2

复制顺序：

1. `MINIMAX_MASTER_PROMPT`：项目目标、约束账本、素材角色、时间线和节点方法；
2. 要求工作台先回报实际模型/输入/时长/分辨率/变体数/预计消耗；
3. 用户批准；
4. 逐节点复制模型 Prompt；
5. 结果回到本 Skill 做 Observe–Diagnose–Delta。

固定停止门：

```text
已启用模型只作为允许池，不得全部并行运行。
每个节点默认一个模型；只有明确标记 A/B 的关键镜头允许两个。
无法读取模型、费用或参数时写 UNKNOWN。
未经“批准生成”不得调用收费媒体模型。
```

MiniMax Design 的 Router、可见模型、plugins/skills 和 credits 是账户/地区/版本相关，运行时核实。
