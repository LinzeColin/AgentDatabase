# Flaky Test、重试与测试有效性

## 1. 不允许“重试洗绿”

每次执行是独立 attempt，保留原始状态、seed、顺序、环境、耗时和证据。最终状态示例：

- `PASS_STABLE`：要求次数全部通过；
- `FAIL_REPRODUCIBLE`：稳定失败；
- `FLAKY`：相同 Subject/条件下结果不一致；
- `BLOCKED_ENVIRONMENT`：环境不具可比性；
- `NOT_RUN`。

只展示最后一次 PASS 属于证据污染。flake 对关键 Acceptance 默认非正向；低影响 flake 仅可作为有 Owner/到期/补偿控制的剩余风险。

## 2. 重试策略

重试必须在计划中预定义：最大次数、触发条件、是否重置状态、seed、间隔。不得在看到失败后临时无限重试。

建议：

- deterministic unit/contract：0–1 次诊断性复跑；
- UI/网络：最多 2 次，并保留 trace/video/network；
- AI/Agent：不是“重试直到成功”，而是预先定义的独立 trial 分布；
- load/recovery：失败后先检查环境稳定性，不能直接重跑覆盖事故。

## 3. Test discrimination

通过不能证明测试有能力发现错误。关键 Acceptance 至少选一种：

- mutation testing：改变行为并确认测试 kill mutant；
- property-based testing：生成边界和最小反例；
- contract negative tests：破坏 schema/version/permission；
- fault injection：受控使依赖失败、延迟、重复或乱序；
- oracle reversal：在 scratch 状态注入错误期望；
- golden/baseline differential：与已接受版本或独立实现比较。

surviving mutant 可能表示测试缺口、Oracle 不精确或等价 mutant；必须分类，不机械判失败。

## 4. 污染与隔离

记录并控制：测试顺序、共享 DB/缓存、时区/locale、随机 seed、并发、端口、临时目录、网络、Feature Flag、依赖版本。standard/deep 的关键路径在干净状态复跑。

## 5. 统计解释

小样本不报告伪精确可靠性。AI trial 或 flake 率需同时报告 `n`、通过数、失败类型和置信限制；关键切片逐项过门，不以总体平均替代。

## 6. 测试选择退出条件

一个测试只有在以下至少一项成立时保留：覆盖权威 Acceptance；验证变更影响；降低重大风险不确定性；验证修复；验证发布/恢复/AI 门。否则删除或降为可选，减少时间与 token 噪声。
