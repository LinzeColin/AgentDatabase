# Teleiosis v0.0.0.5 Handoff

## 当前事实

- 版本：v0.0.0.5；一个 Skill，四个逻辑引擎；
- current_phase：`FROZEN_CANDIDATE`；
- 本地工程门：由包内三遍原始验证证据证明；
- 正式独立验收：`UNAVAILABLE`，只能由外部 Verifier 完成；
- 目标 Registry 安装：`NOT_RUN`，属于有写权限环境的最后一公里；
- 原生竞品与生产盲测：`NOT_CLAIMED / PENDING`。

## Build Agent 只做

1. 获取目标仓最新 main 和适用治理规则；
2. 运行 Stage 0 Semantic Reconcile；
3. 无 conflict/blocked 时执行事务安装；
4. 运行冻结测试和生成证据；
5. 按用户规则提交 main；
6. 将冻结 Candidate handoff 给外部 Verifier。

不得重新进行产品定义、市场研究、架构、Schema、Acceptance、测试设计或版本命名。
