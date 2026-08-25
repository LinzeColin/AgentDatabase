# 白箱迭代Skill｜Genesis Amendment 004 v0.0.0.5

**新增 Requirement：** `WBI-GB-033` 至 `WBI-GB-042`  
**授权来源：** Owner 于 2026-08-03 明确要求交付真实可用、安装即用、完整继承并经至少三次实质 Skill 迭代的 Teleiosis v0.0.0.5。  
**基础 Locked Genesis SHA-256：** `14ab08b9053db4ca87140e59a49f1de8105a718a87ec2d55590c6487c1a77086`

本 Amendment 只追加新要求，不重写 WBI-GB-001—032。

## WBI-GB-033｜v0.0.0.3 非降级继承与来源边界

v0.0.0.5 必须保留 v0.0.0.3 的全量非路由、连续 Candidate、T/S/P 能力、移动仓库适配、证据与回滚语义，并以原始 SKILL、README、444 条 Manifest 快照和语义继承矩阵证明。无法取得全部上游字节时必须明确来源边界，不得伪称逐字节复制。

## WBI-GB-034｜移动仓库 Stage 0 Semantic Reconcile

开发前必须对最新 integration base 按 `satisfied / apply / adapt / equivalent / conflict / blocked / obsolete` 分类；保留更新、更好的上游实现，普通漂移不得被固定 SHA 阻断，冲突和缺失权威必须 fail-closed。

## WBI-GB-035｜三次真实 Skill Catalog 扫描

Baseline、重大 Candidate 变化后、最终冻结前必须分别完成 Pass A/B/C。每次记录 Skill、版本、目的、输入 hash、输出制品、Finding、新机制、关闭风险、Developer Burden Delta 和重跑触发条件；输入未变化不得用重复运行凑数。

## WBI-GB-036｜人物专家 dossier 硬门与中立回退

人物蒸馏专家团队只有在实际载入 dossier、使用 claim_id、呈现真实分歧并隔离控制角色后才计为有效。无法取得 dossier 时必须返回 `INSUFFICIENT_ROSTER_FALLBACK`，使用中立功能角色，不得虚构人物专家或独立模型。

## WBI-GB-037｜十视角、六角色与有界停止

必须完成十个正交视角、两轮六角色复审和真实整改；非隔离运行必须标记 `role_separated_same_model`。连续收敛、预算上限或边际收益转负时停止，不得为满足轮次制造文字变化。

## WBI-GB-038｜可执行 Taskpack、追踪与 Fresh Builder

Project Input、唯一状态机、六类无环 Task DAG、Acceptance、Oracle、Test、Evidence、Artifact、回滚、停止条件必须机器可验证。Fresh Builder 必须证明只剩真实环境绑定的最后一公里任务。

## WBI-GB-039｜冻结 Subject 与外部 Verifier 交接

内部系统只能生成绑定精确 Candidate、Acceptance 和 Manifest 的只读 Verifier handoff，不能签发正式 PASS。NOT_RUN、UNKNOWN、WAIVED、模拟、角色替代不得提升为通过。

## WBI-GB-040｜大样本确定性回归语料

发布包必须包含可校验、可重放的 T/S/P/A 多分区回归语料，覆盖开发、选择、隐藏 IID、隐藏 OOD、红队和回归集，并通过记录级 checksum、总哈希、数量与覆盖验证；语料不得冒充真实市场。

## WBI-GB-041｜零技术门槛事务安装与诊断

根目录必须提供一键体检与安装入口，支持全新、幂等、v1—v4 升级、未知非冲突文件保留、备份、精确回滚、冷解压和跨平台脚本；任何安全或 Genesis 冲突必须阻断。

## WBI-GB-042｜完整原始证据与唯一正式制品

最终只交付一个无歧义 ZIP。包内必须包含原始测试日志、三次 Skill pass、复审、Fresh Builder、安装/升级/回滚、确定性构建、冷解压、ZIP 审计、来源快照、Roadmap、Pursuing Goal 和架构图；摘要或哈希不得替代本可随包保存的原始证据。
