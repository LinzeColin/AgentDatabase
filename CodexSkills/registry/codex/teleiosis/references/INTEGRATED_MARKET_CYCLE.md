# Teleiosis v0.0.0.2｜统一宏循环合同

## 1. 唯一调用顺序

```text
T1 raw_teleiosis R1 → R2 → R3 → atomic commit C1
M1 market_evidence R1 → R2 → R3 → atomic commit C2
T2 raw_teleiosis R1 → R2 → R3 → atomic commit C3
M2 market_evidence R1 → R2 → R3 → atomic commit C4
T3 raw_teleiosis R1 → R2 → R3 → atomic commit C5
```

一轮只有这一条合法路径。完整运行必须恰好包含 15 个 `subrun` 事件和 5 个 `mutation_commit` 事件。

## 2. “一次调用连续三轮”的定义

| 子轮 | 目的 | 可改变什么 | 必须产出 |
|---:|---|---|---|
| R1 | diagnose / discovery | 假设、Finding、测试计划 | 输入 Subject hash、证据 hash、增量机制 |
| R2 | adversarial challenge / experiment | staged Candidate，可回退 | 真实命令、结果、失败、成本、反证 |
| R3 | adjudicate / stabilize | 只能稳定 staged Candidate | 决策、批准的 staged tree hash、剩余 P0/P1 |

R1/R2/R3 必须连续，不允许中间插入另一个 profile、另一个 Subject 或非账本 mutation。输入没有变化时允许 `NO_CHANGE`，但不能虚构新发现。

## 3. 修改节点为何不造成验收逃逸

R3 在“修改节点”之前对完整 staged Candidate 运行并批准其目录树 SHA-256。随后的 mutation 节点不是再次编辑，而是把**同一个哈希**原子设为下一正式 Candidate：

```text
approved_digest(R3) == actual_tree_digest(commit)
```

不相等即 FAIL。这样既满足“每次调用后修改对象”，又避免 T3 后最后一次修改未被任何 Teleiosis 调用检查。

## 4. Profile 边界

### raw_teleiosis

- 使用同一 v0.0.0.2 包中的原始白箱控制 profile；
- 关闭 Market Evidence Kernel；
- 不能递归调用自身、不能修改 Genesis、sealed eval、review contract 或运行中的 orchestrator；
- 迭代 Teleiosis 自身时，只能写安装目录外的 Candidate。

### market_evidence

- 运行五臂因果、压力、规模、真实任务与市场证据；
- 可以提出 patch/hypothesis，但不能直接修改正式 Candidate；
- 最高结论为 `EVIDENCE_READY_FOR_TELEIOSIS`；
- 不拥有最终发布、安装或回滚权限。

## 5. 账本与恢复

`teleiosis_cycle.py` 使用：

- `cycle_contract.json`：冻结序列、权威与 mutation 合同；
- `events.jsonl`：append-only 事件与 SHA-256 hash chain；
- `state.json`：可重建投影，不是第二事实源；
- `.cycle.lock`：进程互斥。

中断后先执行：

```bash
python3 scripts/teleiosis_cycle.py validate --workspace /outside/run
python3 scripts/teleiosis_cycle.py status --workspace /outside/run
```

账本未完成时从唯一 `expected stage/round` 继续；不得猜测或跳过。

## 6. 最终晋级

宏循环完整仅证明调用与变更链合法，不能单独证明市场成功。最终仍要求 Teleiosis 的冻结 Gate、保护任务、身份、安全、成本、独立复审、安装和回滚合同全部通过。
