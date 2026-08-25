# White-box Iteration Log

## Iteration 1 — Evidence separation

问题：原包 96.1% 容易被误读为效果分。

改动：拆为 Goal Fit、Evidence Confidence、Native-model Evidence、Human Review、External Verifier。

## Iteration 2 — Model freshness

问题：版本标签混入未经官方核验的信息。

改动：建立当前模型注册表；Sora 2 非默认；未知 vendor label 不猜能力。

## Iteration 3 — Compiler architecture

问题：通用 Prompt 难以正确适配 H3、Runway I2V 和 LTX。

改动：加入 VideoPromptIR 和模型渲染器。

## Iteration 4 — Candidate competition

问题：单次扩写没有内部对照。

改动：Precision / Expressive 双分支，硬门槛后择优。

## Iteration 5 — Industrial mechanism

问题：工业规则仍可能停留在“真实尺度、稳定轨迹”等口号。

改动：九层物理账本、局部—全局复核、证据边界。

## Iteration 6 — Workflow breadth

问题：人物连续性、剧本转分镜、确定性剪辑不是正式路径。

改动：新增 Reference Sheet、screenplay_to_shots、EDL 优先工作流。

## Iteration 7 — Chinese footage route and duration semantics

问题：端到端样例把“把真实素材剪成……”误路由为 T2V，并可能把源素材时长误作目标成片时长。

改动：增加中文素材剪辑意图、`source_duration_seconds` / `duration_seconds` 双字段和固定回归；`40s source → 18s target` 已通过。

## Iteration 8 — Installation scope

问题：若安装器只复制运行文件，研究证据、Taskpack 和交接状态会丢失。

改动：安装器保留 `research/`、`taskpack/` 与 `.ramify/`，并增加自定义目标安装测试。

## Current frontier

真实模型 A/B、人工成片复核和外部 Verifier 尚未运行；这是下一阶段的证据缺口，不是文档继续扩写能替代的工作。
