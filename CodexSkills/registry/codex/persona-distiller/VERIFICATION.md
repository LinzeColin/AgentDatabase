# Release verification — Persona Distiller v0.0.0.5

Date: 2026-07-23

## Result

**PASS** — builder、平级 canonical group、单人物完整交付和最终双 Skill 发行 bundle 均通过离线验证。验证不声称任何真人模型已经获得本人授权、背书或超出其证据边界的能力。

## 自动化证据

| Gate | Result |
|---|---:|
| Offline unit / integration / concurrency tests | 52 / 52 passed |
| Reviewer Round 1 | 6 roles, 24 / 24 checks passed |
| Reviewer Round 2 | 6 roles, 40 / 40 adversarial checks passed |
| Builder JSON Schema | 13 valid Draft 2020-12 documents |
| Python syntax coverage | 32 scripts |
| Root `SKILL.md` progressive-disclosure ceiling | 142 lines; passed |
| Secret-pattern scan | 0 findings |
| Canonical group validation | 7 categories, 3 products, 3 artifacts; passed |
| Complete-release deterministic rebuild | passed |
| Complete-release checksum tamper rejection | passed |
| Atomic dual-Skill clean install | passed |
| Person-delivery deterministic rebuild | passed |
| Person-delivery checksum tamper rejection | passed |
| Runtime history reset | passed; no numbered invocation state |
| Concurrent unnumbered audit append | complete records; passed |
| Per-person product registration | first, next, gap, idempotence, contention, 999, exhaustion passed |
| Cross-category uniqueness | subject UID, canonical key, runtime hash and outer hash gates passed |

## v0.0.0.5 交付合同

- 最终 Persona Distiller 发行只产生 `PersonaDistiller-Final-v0.0.0.5.zip`。
- ZIP 只有一个顶层目录，完整包含 `persona-distiller/` 与 `persona-distiller-group/`、原子安装器、manifest 和全文件 SHA-256。
- 默认只安装到 `~/.codex/skills`；不会同时在 `~/.agents/skills` 保留第二来源。
- 每个人物发布只产生一个外层完整交付 ZIP；其中恰好嵌入一个不可变运行时 Skill ZIP，并包含安装、登记、team card、来源覆盖、评测、验证、provenance、review 和 handoff。
- 文件与 schema 不枚举或限制人物姓名、语言、职业或内容风格；稳定 slug 仅用于安全、兼容的文件路径。
- 七类 canonical 登记仅存在于平级 `persona-distiller-group/`，目录名与内部身份名称一致。

## 版本与调用边界

- `v0.0.0.5` 是构建器与团队 Skill 的发行版本。
- `0.0.0.N` 仅是每个 canonical 人物独立、连续的产品版本，范围 `0.0.0.1..0.0.0.999`。
- 候选打包不占号；只有成功登记才占号。
- 人物 Skill 的每次运行不编号，也不要求用户选择身份、编号或权重。
- 既有三份人物产品仍为 `0.0.0.1`；迁移只增加 v0.0.0.5 完整外层，内层运行时字节与 SHA-256 保持不变。

## 团队路由边界

- 只有与当前任务高相关且 `ready` 的人物能进入 roster。
- 团队规模 5–20，以正向解决问题的专家为主。
- 至少隔离 1 个中立复审、1 个中立裁判和 1 个中立反证角色。
- 库存不足时返回 `insufficient_roster`，不得用不相关人物凑数。
- 哈希、登记或版本不一致时停止路由并先修复 registry。

## 隐私和供应链

- 运行时 ZIP 排除 raw、Holdout 正文、私密来源正文、历史运行内容和凭据。
- 私域人物要求真实授权；公开 registry 拒绝 private/self 产物。
- 外层和内层校验均拒绝空清单、漏项、重复路径、越界路径、symlink 和哈希不一致。
- 三份历史迁移交付对缺失证据明确标记 `not-available-in-source-artifact`，没有补造通过结论。
- 外层 ZIP 哈希由 canonical `registration.json` 保存，避免自引用哈希悖论。

## Review 独立性说明

本轮环境没有使用独立 subagent。两轮结果是六个隔离领域 checklist 的串行确定性复审，并由集成测试支撑；不能表述为六个独立外部模型的判断。

## 适用性限制

工程验证只能证明结构、安装、路由、版本、隐私和供应链合同。特定人物的行为保真仍取决于合法来源、证据质量、冻结 Holdout、独立评价和宿主模型/工具能力；当前事实和高风险专业结论必须另行核验。
