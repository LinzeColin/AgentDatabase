# Release verification — Persona Distiller v0.0.0.15

Date: 2026-07-29

> **本文件记录「当前发布号的复验结果」，不是历史归档。**
> 版本号必须等于根目录 `VERSION`，由 `scripts/check_contract_drift.py` 强制。
> 上一份 v0.0.0.5（2026-07-23）的逐项结论见 `CHANGELOG.md`——
> **那些结论不得在本文件里被重述为当前状态**：v0.0.0.5 的表格一路留到 v0.0.0.13
> 都没重跑过，是这次查出的漂移之一。

## Result

**PARTIAL** — builder 自身、平级 canonical group、人物交付打包与登记全部通过离线复验；
**最终双 Skill 发行 bundle 无法构建**，见下方「未通过」。
验证不声称任何真人模型已经获得本人授权、背书或超出其证据边界的能力。

## 自动化证据

本表每一行都来自 **2026-07-29 本次实跑**的输出。没跑的一律标 `未复验`，不沿用旧结论。

| Gate | 本次结果 | 证据来源 |
|---|---:|---|
| Offline unit / integration / concurrency tests | **57 / 59 passed，2 failed** | `python3 -m pytest tests/ -q` |
| 合同漂移门（版本三轴 + 身份输入合同） | **0 条**（修复前 18 条） | `scripts/check_contract_drift.py` |
| 合同漂移门的负对照 | passed | `check_contract_drift.py --self-test` |
| Release checksum 全量校验 | passed，272 files | `self_check.py` |
| Canonical group validation | **12 categories, 97 products, 99 artifacts**; passed | `validate_persona_registry.py` |
| Identity family registry | 12 families；加权多身份输入被拒 | `test_identity_routing`、`test_skill_contract` |
| Builder JSON Schema | 14 documents | `self_check.py` |
| Python script 覆盖 | 45 scripts | `self_check.py` |
| Root `SKILL.md` 行数 | 206 行；self_check 未报越界 | `self_check.py` |
| Secret-pattern scan | 0 findings | `self_check.py` |
| Reviewer harness 两轮 | passed | `test_six_reviewer_harness_passes_both_rounds` |
| Person-delivery deterministic rebuild | passed | `test_target_package_is_deterministic_for_unchanged_state` |
| Person-delivery checksum tamper rejection | passed | `test_packaged_target_installer_verifies_checksums_and_rejects_tamper` |
| Runtime history reset / 调用不编号 | passed | `test_runtime_recording` 全部用例 |
| Concurrent unnumbered audit append | passed | `test_zz_runtime_concurrency` |
| Per-person product registration | first / next / gap / idempotence / contention / 999 / exhaustion passed | `test_persona_registry` |
| Cross-category uniqueness | passed | `test_persona_registry` |
| **Complete-release deterministic rebuild** | **FAILED — 无法构建** | `test_complete_release_is_one_deterministic_zip_and_installs_both_skills` |
| **Complete-release checksum tamper rejection** | **FAILED — 无法构建，未能进入被测点** | `test_complete_release_installer_rejects_tampering` |
| Atomic dual-Skill clean install | **未复验**（依赖上面那个构不出来的 bundle） | — |

## 未通过：发行 bundle 自 v0.0.0.9 起构建不出来

`scripts/build_release_bundle.py` 要求 `persona-distiller` 与 `persona-distiller-group`
两个 Skill 的 `VERSION` **完全相等**，否则直接 `SystemExit: version mismatch`。

- `persona-distiller/VERSION` = `v0.0.0.14`
- `persona-distiller-group/VERSION` = `v0.0.0.8`

v0.0.0.9 之后的改动都只落在 builder 一侧，group 的版本号没有跟着动，
于是**从 v0.0.0.9 起，`PersonaDistiller-Final-*.zip` 一次也构建不出来**——
而这件事此前没有被发现，因为它的两个失败用例混在另外三个校验和失败里。

这不是文件名不统一，是**发行物根本不存在**。修法需要先定一件事：
bundle 版本号是「一个号盖两个 Skill」还是「两个 Skill 各自独立编号、bundle 只记录两者」。
在用户裁定前不擅自改动 group 的版本号——那会凭空宣称 6 次没有发生过的 group 发布。

## v0.0.0.5 交付合同

- 最终 Persona Distiller 发行只产生**一个** bundle。**文件名跟的是 skill 发布号，不是本节的交付合同号**：`PersonaDistiller-Final-<VERSION>.zip`，由 `scripts/build_release_bundle.py` 从 `VERSION` 读取。
- ZIP 只有一个顶层目录，完整包含 `persona-distiller/` 与 `persona-distiller-group/`、原子安装器、manifest 和全文件 SHA-256。
- 默认只安装到 `~/.codex/skills`；不会同时在 `~/.agents/skills` 保留第二来源。
- 每个人物发布只产生一个外层完整交付 ZIP；其中恰好嵌入一个不可变运行时 Skill ZIP，并包含安装、登记、team card、来源覆盖、评测、验证、provenance、review 和 handoff。
- 文件与 schema 不枚举或限制人物姓名、语言、职业或内容风格；稳定 slug 仅用于安全、兼容的文件路径。
- 十二类 canonical 登记仅存在于平级 `persona-distiller-group/`，目录名与内部身份名称一致。

## 版本与调用边界

- `builder_version`（交付合同）钉在 `v0.0.0.5`，**不随 Skill 发布号移动**；
  Skill 发布号以根目录 `VERSION` 为唯一真源。两者是独立的轴，不能互相顶替。
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
