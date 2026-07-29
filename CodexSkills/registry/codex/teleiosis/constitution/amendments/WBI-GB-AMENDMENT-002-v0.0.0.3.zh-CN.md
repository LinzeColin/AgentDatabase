# 白箱迭代Skill｜Genesis Amendment 002 v0.0.0.3

**Amendment ID：** `WBI-GB-AMENDMENT-002`  
**新增 Requirement：** `WBI-GB-029`  
**状态：** `LOCKED_APPEND_ONLY_AMENDMENT`  
**授权来源：** Owner 于 2026-07-29 明确要求五源合并，并规定现在及以后采用 `T1 -> C1 -> S1 -> C2 -> P1 -> C3`，三轮一组、三组一次 Run；禁止路由缩减。  
**前置有效 Genesis：** `WBI-GB-CANDIDATE-001+A001` / `v0.0.0.2`  
**基础 Locked Genesis SHA-256：** `14ab08b9053db4ca87140e59a49f1de8105a718a87ec2d55590c6487c1a77086`  
**前置有效 Composite SHA-256：** `fe80c467f8ecbe8343ef0c09ef5e6f9fd9683803c8260c9188998c7e3dfca0a2`

> 本 Amendment 只追加 WBI-GB-029；WBI-GB-001—028 与基础 Genesis 原文件保持不变。

## WBI-GB-029｜五源统一、全量非路由与 Candidate 连续演化

Teleiosis 正式运行必须以唯一 Skill 身份、唯一 Candidate 生命周期、统一证据合同和唯一最终晋级权，完整执行以下语义顺序：一轮为 `T1 -> C1 -> S1 -> C2 -> P1 -> C3`；连续三轮构成一组；连续三组构成一次完整 Run。`T` 是 Raw Teleiosis 全量白箱迭代与控制面，`S` 是 Skill Market Lab 全量因果、压力、大数据、竞品和市场反馈面，`P` 是 Product Reality Lab 全量产品现实试炼面。

`C` 明确表示**迭代对象本身在该阶段之后的 Candidate revision**，不是 SHA 检查点、不是空提交、不是“只能提交同一哈希”的限制。T、S、P 均可依据各自完整证据对同一个外部 Candidate 工作副本实施被授权的修改；C1/C2/C3 分别是这些修改完成后的可运行 Candidate 状态。每个 C 必须保留父 revision、精确 diff、变更理由、测试结果、回滚指针和可选的动态内容指纹；内容指纹只用于审计与防篡改，不得作为安装、合并、移动 main 或后续修改的预设前提。

外部调用 `teleiosis` 必须启动同一完整 Run。Skill Market Lab 和 Product Reality Lab 是 Teleiosis 内置子模块，不注册为独立 Skill，不使用任务路由，也不得跳过完整能力表。Run 内 T/S/P 阶段使用 `internal_stage=true` 防止递归；每次阶段仍须完整扫描自身 Capability Manifest，逐项记录 `EXECUTED / NOT_APPLICABLE_WITH_REASON / NOT_RUN / BLOCKED`。`NO_CHANGE` 只表示该阶段没有合理修改，不表示可以免跑。

Skill Market Lab 和 Product Reality Lab 没有正式晋级权；只有 Teleiosis 能形成交给外部独立 Verifier 的证据就绪决定。模拟、合成大数据和模型评分不能升级成真实 Field、真实用户或真实市场事实。

本要求冻结的是语义顺序、全量执行、Candidate 连续演化、证据和责任边界；不冻结仓库 HEAD、目标文件 SHA、目录、工具、模型、供应商、适配器、评分器、数据源、预算或实现架构。移动 main 必须采用最新 integration base 上的语义适配，不得因普通字节漂移直接冲突。

**严重性：** `HARD_NON_COMPENSABLE`

## 回滚

回滚不得删除本文件。若需变更 WBI-GB-029，Owner 必须按 WBI-GB-026 明确指定变更范围并追加后续 Amendment。
