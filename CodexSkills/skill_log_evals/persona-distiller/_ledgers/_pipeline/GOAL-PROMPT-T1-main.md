# T1 主线程 goal prompt（主线程 = 本会话）

> 用法：作为主线程的 Pursuing Goal 目标契约，每轮开头重读
> `_ledgers/_pipeline/PLAN-2026-08-20-三线程并行.md` 与 `_ledgers/GOAL-CONTRACT-v5.md`。

## goal objective

```
蒸馏至600：T1负责1-300（材料/软件/艺术/创业/投资/思想 6 族），P0当天清、日蒸12-15人；
95%+成本flash、pro仅关键；每3-5人迭代两skill（有实测证据才改否则回滚）；
共享文件只有T1写（team-index/GOAL-STATE/GOAL-LOG/队列/延后）；细则见PLAN+GOAL-CONTRACT-v5
```

## 轮次纪律（每轮强制）

1. 先 `TZ=Australia/Sydney date +%H%M` + 读 `~/.dsh/cron-flags/`，判峰谷；再读 GOAL-STATE.json。
2. 每次汇报带两个数（现算，不引用）：`git ls-files 'CodexSkills/registry/codex/persona-distiller-group/*/*/team-card.json' | wc -l` + 本轮新增。
3. 连续 3 轮没让包内人数 +1 → 停一切判据/复核/缺陷调查，只做「让下一位出货」的事。
4. 峰时（悉尼 11-14、16-20）零工具调用等效 block；谷时全力。

## 在途优先级

- P0：查 wip-eiffel-142 卡点（已做未出货）→ 能复用则出货，否则重做。
- NEXT：Thomas Telford（材料建工师 #37）→ Frederick Winslow Taylor。
- 每 5 人须含 1 名最少三族的人（决策台账规则）。

## 硬约束（不可违反）

- 主树只提交 main、不 push（cron 推）；`git add -A` 只限 CodexSkills 子目录；永不碰 `_protected/`。
- 语料原文不进 git；只取公有领域（≤1930）；零编造；双侧盲判同模型（默认 flash）。
- 门、席位、评委指令冻结不动；每 3-5 人检查点迭代两 skill，无净增益回滚。
- 收 T2/T3 问题上报 → 迭代优化 persona-distiller 与 expert-team 两 skill（build_manifest+check_contract_drift+全量自检全绿才落盘+commit+留痕）。
- 完成 = 600 人或用户喊停。
