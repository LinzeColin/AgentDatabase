# Tool Routing Matrix

| 能力 | 首选 | 备选/补充 | 关键限制 |
|---|---|---|---|
| Browser deterministic | Playwright | Cypress/Selenium（已有基线时） | Trace 与稳定 locator；跨引擎按风险 |
| Browser model exploration | Playwright CLI/MCP, Stagehand | BrowserGym/Hercules | 只能探索，不能独立裁决 |
| Accessibility | axe-core + Playwright | Lighthouse、人工读屏 | 自动化不能发现全部问题 |
| API schema/property | Schemathesis | Dredd、语言原生 property tools | 需要可信 OpenAPI/GraphQL Schema |
| Stateful model | Hypothesis | fast-check、jqwik、QuickCheck | 必须定义 invariant |
| Combinatorial | NIST ACTS/覆盖数组库 | 自有 pairwise generator | 高风险交互提高 t-way |
| Mutation | Stryker 家族 | PIT、mutmut、Cosmic Ray | 关注关键决策内核，处理 equivalent mutants |
| Performance | k6 | Locust/JMeter（现有基线时） | 负载来自 operational profile |
| Static security | CodeQL | Semgrep、语言扫描器 | 版本与规则集固定 |
| Dynamic security | OWASP ZAP | 现有 DAST | 主动模式仅授权环境 |
| Chaos | Chaos Mesh/Litmus | Toxiproxy/Pumba/自有 fault proxy | 先 steady state/abort/rollback |
| OSS provenance | ScanCode | Syft/ORT/FOSSology | 保留 notice/license/source |
| Observability | OpenTelemetry | 现有 APM | 跨服务 context propagation |
| Product analytics | PostHog | 现有平台 | 隐私遮罩、采样、Flag 关联 |

不要为了工具统一而替换稳定的项目原生基线；统一的是证据协议，不是工具品牌。
