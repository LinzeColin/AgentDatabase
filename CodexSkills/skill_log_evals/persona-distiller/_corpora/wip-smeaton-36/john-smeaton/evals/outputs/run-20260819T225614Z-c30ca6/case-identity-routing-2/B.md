# Output B

纯现代气象学研究任务在本路由体系中无专属 intent（实测 `--intent meteorology` 返回 `FAIL: unknown_intent`）。正确做法：走默认 `--intent startup`，仅读 `data/memory/agent-memory.json` 完成最小握手；气象学与 profile/taste/记忆更新无关，不加载任何 conditional 资源、不触发广扫。实际研究内容在仓外完成——用 `agent-reach` 检索官方气象来源。该任务不属于记忆同步范围，不写 update_targets、不产生 sync_runs 记录。
