# 工具路由与复用原则

先问“要证明什么”，再选工具。优先项目已有、锁定版本的 runner；新工具只在隔离环境、ROI明确且不改变被验对象时安装。工具存在不等于测试已执行。

| 目标 | 首选 | 补充/替代 | 必留证据 |
|---|---|---|---|
| 任务包锁定 | `ingest_taskpack.py` | 外部签名/制品库引用 | 完整源快照、完整包/七角色双摘要、授权摘要、ID清单、兼容/漂移证据 |
| 追溯与影响面 | Task Graph + Acceptance Contract + diff/build graph | CodeQL/依赖图/覆盖工具等已有能力 | Acceptance/Task/Test映射、change-impact、未覆盖原因 |
| Web E2E/跨浏览器 | 项目 Playwright/Cypress/Selenium | Playwright | trace、console、network、video/screenshot、report |
| API 合约/边界 | 项目 contract tests | Pact、Schemathesis、Newman、REST Assured | schema/version、seed、JUnit/JSON |
| 分布式因果链 | 项目 tracing/OTel | Tracetest 等已有栈 | trace ID、span assertion、服务版本与错误路径 |
| 属性/极值 | 语言原生 property/fuzz | Hypothesis、fast-check | seed、最小失败例、迭代数 |
| 数据/迁移 | 项目 query/reconciliation | dbt tests、Great Expectations 等已有栈 | before/after、控制总数、迁移/恢复日志 |
| 负载/压力 | 项目已有 | k6、Locust、Gatling/JMeter | workload、threshold、summary、服务端资源 |
| 无障碍 | axe-core + 手工键盘/W3C checks | pa11y/Lighthouse | 规则 JSON、激活状态、键盘记录、未覆盖声明 |
| Web 安全 | passive + 项目 SAST/SCA | ZAP active/Nuclei 仅授权环境 | scope、policy、rate、原始告警、误报处置 |
| Mobile/Desktop | 原生 harness | Appium/OS automation/computer-use探索 | app hash、设备/OS、video、system logs |
| 隔离依赖 | 项目 Docker/Testcontainers | 受管测试环境 | image digest、seed、startup/cleanup logs |
| 韧性/故障注入 | 应用故障开关、容器/网络控制 | Litmus/Chaos Mesh/云故障工具，仅授权 | steady-state、fault spec、abort、恢复证据 |
| AI/Agent | 项目 eval harness + 程序化 outcome grader | provider eval、跨模型 judge、人工盲评 | task/trial、系统hash、trace、world state、grader独立性、成本 |
| 供应链身份 | CI provenance、artifact digest | SLSA verifier、cosign、SBOM工具 | provenance、签名验证、SBOM、source mapping |
| 渐进发布 | 平台原生 canary/ring | Argo Rollouts/Flagger/Feature Flag | candidate/control、analysis、bake、abort/rollback |
| 测试编排 | 项目 CI | Testkube/类似控制平面（已有或ROI明确） | runner版本、触发、原始结果、环境与重试序列 |
| 报告/attestation | 原始runner + Markdown/JSON | JUnit/Allure/HTML聚合 | 原始结果优先，in-toto Test Result 可追溯 |

## 硬规则

1. 关键断言靠语义、数据或 world state，不靠坐标、单图或模型自报。
2. 任务包哈希、兼容性和漂移是不同证据；不得互相替代。
3. AI生成测试保存为普通可审计代码；自愈 locator 只能提候选，不能静默改写后宣布通过。
4. 负载主要用协议层，少量真实浏览器验证用户体验。
5. 扫描器/模型 judge 是信号，不是自动事实；模型 judge 必须记录版本、盲评、跨模型/人工校准和争议处理。
6. 工具版本、配置 hash、精确命令和退出码进入 manifest。
7. 新工具不能污染全局环境或修改产品锁文件；否则在临时副本/容器运行。

## 能力不足时

无浏览器自动化、OpenAPI、服务端监控、隔离环境、代表性数据、构建 provenance 或机器可读 Acceptance ID 时，应明确降低可证明范围或 BLOCKED，不能通过人工口头补齐后伪装为完整自动验收。
