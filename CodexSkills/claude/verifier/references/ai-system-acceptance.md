# AI / LLM / Agent 验收专项

## 何时适用

模型输出、提示词、工具调用、检索结果或 Agent 决策只要会改变用户结果、数据或外部副作用，即 `ai_system.applicable=true`。AI 不是确定性函数，不能只跑一次。

## 1. 锁定系统身份

至少记录 provider/model/snapshot、system/developer prompt或policy hash、Agent harness/toolset hash与权限、retrieval snapshot、safety policy、sampling、步骤/token/时间/费用预算、环境和外部动作边界。模型、prompt、tool、retrieval、policy任一变化都可能触发 reacceptance。

## 2. Task / Trial / Grader / Outcome

- task：带输入、环境和成功条件的案例；
- trial：task的一次独立尝试；
- grader：评价某一维度的规则；
- trace/trajectory：完整输出与工具调用；
- outcome：结束后的真实世界状态。

Agent说“已完成”不是完成；数据库、文件、消息、预订、代码、审批或其他 world state 才是主证据。

## 3. 多次试验

正向 PASS 的每个声明任务切片至少3个独立trial；每个有唯一context、干净/重置证据、完整trace、world-state outcome、成本和延迟。高波动、高风险增加trial；不得只挑最好一次。执行前定义success threshold；总体与每个切片的 observed pass rate 都由原始记录计算，不能手填。每个切片必须独立达到阈值，不能用总体平均掩盖关键切片失败；不同配置不得混成一个通过率。

## 4. 代表性切片

覆盖常见任务、高价值/高损失任务、长尾歧义、多轮长上下文、工具失败、角色/权限/语言、外部副作用、拒绝与过度拒绝、prompt injection、数据外泄、越权工具、成本/延迟/步骤上限。关键安全切片不能被总体平均抵消。

## 5. Grader 独立性

优先级：确定性 world-state/invariant → 程序化grader → 经校准模型grader → 人工专家。

正向 verdict 必须满足：

- `generator_is_sole_judge=false`；
- 记录 grader 类型、独立 evaluator ID、分歧处理与证据；
- 使用模型/composite grader 时，`cross_model_review=true`、`blind_evaluation=true`，且至少一个 evaluator 与生成模型不同；
- 候选标签/顺序在比较评测中盲化或随机化；
- 模型分歧不能自动取更有利结论，按预定规则转人工/确定性证据或 BLOCKED。

不同模型互审降低相关性盲区，但不能替代真实世界 Oracle。

## 6. Baseline 与统计边界

对比上一已接受系统或候选，报告task success/pass@k或业务成功率、分切片结果、关键安全失败率、延迟/token/工具/费用、失败类型与新增回归。样本不足写低置信度，不用小样本差异声称稳定提升。

## 7. Agent 专项

验证最小权限和工具allowlist；不得绕过确认/审批/支付/删除门；重试/恢复不重复副作用；中途失败状态可解释；长任务不无限循环/失控花费/偏离目标；输出与world state一致；trace足以复现关键动作。

## 8. 放行门

AI适用时 PASS 至少需要：系统身份完整、AI gate PASS、每个声明切片至少3次trial且独立达阈值、world-state grader、独立评测机制、baseline或缺失原因、预定义阈值与机器计算总体/分切片pass rate、每trial独立context/reset/outcome/trace、prompt injection/权限/敏感数据检查、成本与延迟证据、无不可豁免安全失败。

生产行为漂移、provider/model snapshot或工具权限变化触发post-deploy监控与再验。
