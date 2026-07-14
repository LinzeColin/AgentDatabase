# Memory Atlas 机器真相索引

## 结论

- 本页只负责路由：requirements、source、model、acceptance、evidence 的事实仍由对应 canonical owner 保存。
- 不在本页维护参数值、公式表达式、运行状态、测试断言或数据内容；改变事实时必须编辑表中指定的 canonical source。
- generated projection、tests 和 evidence 只承担投影、验证或证明职责，不建立第二个可执行源。

## 操作

1. 先按问题选择一个真相域，再打开该域表中的目标。
2. 只在 `canonical_editable` 目标修改对应事实；其他目标按其 mutability 规则生成、验证或追加。
3. 修改后运行相关测试与 renderer，确认索引仍只包含路径和职责，没有复制执行值。

## 五域索引

### requirements｜需求与当前执行状态

定位当前 Task、验收条件、依赖、进度和权威 TaskPack 身份。

| Canonical target | 职责 | Owner | Mutability |
|---|---|---|---|
| [docs/governance/roadmap.yaml](../docs/governance/roadmap.yaml) | 当前 Stage、Phase、Task、acceptance、进度和下一门禁的唯一治理源。 | requirements_governance | canonical_editable |
| [config/memory_atlas_test_value_review.json](../config/memory_atlas_test_value_review.json) | v1.2.1 TaskPack 文件名与 SHA-256 的审计绑定；不复制 TaskPack 正文。 | requirements_governance | canonical_editable |

### source｜数据来源定义

定位可接入来源、隐私边界、写回策略和最小字段定义。

| Canonical target | 职责 | Owner | Mutability |
|---|---|---|---|
| [config/data_sources/source_registry.json](../config/data_sources/source_registry.json) | ChatGPT、Codex 与其他已登记来源的唯一当前 source registry。 | source_registry | canonical_editable |

### model｜模型、公式与参数

定位模型目录、公式目录、参数目录及 owner 投影，执行值继续由各目录引用的 code/config 决定。

| Canonical target | 职责 | Owner | Mutability |
|---|---|---|---|
| [docs/governance/model_registry.yaml](../docs/governance/model_registry.yaml) | 模型身份、用途、输入输出和实现引用的 canonical catalog。 | model_governance | canonical_editable |
| [docs/governance/formula_registry.yaml](../docs/governance/formula_registry.yaml) | 公式表达式、约束和 implementation refs 的 canonical catalog。 | model_governance | canonical_editable |
| [docs/governance/parameter_registry.csv](../docs/governance/parameter_registry.csv) | 参数身份、active value、code/config ref 和校准状态的 canonical catalog。 | model_governance | canonical_editable |
| [docs/governance/project.yaml](../docs/governance/project.yaml) | 供 owner renderer 使用的治理投影；模型、公式和参数值不得在此建立第二套编辑源。 | model_governance | generated_projection |

### acceptance｜验收执行

定位公共 validator profile 和真实测试断言，不在索引中抄写 PASS 状态。

| Canonical target | 职责 | Owner | Mutability |
|---|---|---|---|
| [config/memory_atlas_validator_profiles.json](../config/memory_atlas_validator_profiles.json) | fast、sync、ui、release 四个公共 profile 的唯一当前组合合同。 | acceptance_governance | canonical_editable |
| [tests](../tests) | 业务、安全、恢复和用户路径的可执行断言；索引不复制断言内容。 | acceptance_tests | test_assertions |

### evidence｜事件与交付证据

定位追加式事件摘要和受保护运行证据，不把历史证据改写成当前状态。

| Canonical target | 职责 | Owner | Mutability |
|---|---|---|---|
| [docs/governance/events.jsonl](../docs/governance/events.jsonl) | 已验证 Task 的 append-only 事件摘要和 evidence refs。 | evidence_governance | append_only_evidence |
| [机器治理/证据与日志](证据与日志) | 运行、审计、恢复、release 与 review 的证据目录；证据不作为配置输入。 | evidence_governance | evidence_directory |

## 变更规则

- 索引只保存路径、职责和变更规则，不复制参数值、公式表达式、运行状态、测试断言或数据内容。
- 需要变更事实时编辑对应 canonical owner；generated projection、test assertions 和 evidence 不作为第二个可执行源。
- 机器治理子目录中的历史说明和证据本 Task 不删除，后续清理必须由 S05-P2-T2 单独验收。

## 边界

- 本 Task 只建立根索引，不删除机器治理子目录、历史 Stage 记录或证据；后续删除必须由独立 Task 验收。
- config、tests、data、docs/governance 和证据目录继续保有各自职责，本页不能替代它们。
