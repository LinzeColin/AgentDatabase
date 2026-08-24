# 十视角与两轮六角色复审

十个正交视角：战略价值；目标仓与复用；产品范围和 UX；架构接口；数据与恢复；安全隐私许可；容量成本可靠性；Acceptance/Oracle/回滚；Fresh Builder；独立反证和范围污染。

每个视角记录新机制、Finding、变化制品、输入/输出 hash、Developer Burden Delta、KEEP/REVERT/NO_CHANGE 和 P0/P1。收敛视角可以 NO_CHANGE，但不能用同义改写伪造迭代。

第一轮六角色只读审查并去重 Finding；统一整改后，第二轮只复审变化、未关闭 Finding 和回归。无法实例化真实隔离 actor 时必须标记 `role_separated_same_model`，不能作为正式独立 PASS。
