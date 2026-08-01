# Release verification — Persona Distiller v0.0.0.21

Date: 2026-08-01

> **本文件记录「当前发布号的复验结果」，不是历史归档。**
> 版本号必须等于根目录 `VERSION`，由 `scripts/check_contract_drift.py` 强制。
>
> ⚠ **`bump_version.py` 不改本文件的标题**——它是验证记录不是标签。
> v0.0.0.16 升版时它改过一次，正文却仍是 v0.0.0.14 那轮的（PARTIAL、
> bundle 构不出来、97 人、59 用例），**三件当时都已不成立**。
> 改过标题的旧正文会冒充当前复验，比标题陈旧更糟。已从工具中移除该行为。
>
> 本次（v0.0.0.21）**是真的重跑了一遍**，下表每一行都是本次实跑输出。

## Result

**PASS** — builder 自身、平级 canonical group、人物交付打包与登记、
以及最终双 Skill 发行 bundle 全部通过离线复验。
验证不声称任何真人模型已经获得本人授权、背书或超出其证据边界的能力。

## 自动化证据

本表每一行都来自 **2026-08-01 本次实跑**的输出。没跑的一律标 `未复验`，不沿用旧结论。

| Gate | 本次结果 | 证据来源 |
|---|---:|---|
| Offline unit / integration / concurrency tests | **70 / 70 passed** | `python3 -m pytest tests/ -q` |
| 合同漂移门（版本三轴 + 身份合同 + 检查器镜像） | **0 条** | `scripts/check_contract_drift.py` |
| 合同漂移门的负对照 | passed（坏样本 6 类全抓出） | `check_contract_drift.py --self-test` |
| 归属门的负对照 | passed（**8 正 + 10 反**，另含 1 条只报不判） | `check_authorship.py --self-test` |
| OCR 同形字门的负对照（v0.0.0.17 新增） | **passed**（干净英文／真俄语／中文 3 条正对照 0 报；混文种、全同形字词、引文层 3 类坏样本全抓出） | `check_ocr_homoglyphs.py --self-test` |
| **扫描件版权页归属 `A-copyright`（v0.0.0.18 新增）** | **passed**；实测他 1940 年那本亲笔著作由「无据」变为 `A-copyright` 有据，Dies 前言仍判无据 | `check_authorship.py --self-test`、真件三向实测 |
| **`own_voice_ratio`（v0.0.0.19 新增，只报不拦）** | Livermore #100 实测 **0.0076**，而同一份语料 `primary_ratio = 0.9887`——**两个数差 130 倍**；回归用例钉死「把 tier 全改成 P1 也抬不高它」 | `test_own_voice_ratio_is_not_satisfied_by_reclassifying_tiers` |
| **基线来源门 `check_baseline_provenance`（v0.0.0.20 新增）** | **负对照 4 类全抓出**（含「缺字段沉默通过」）；**对已入库产物实测：64/64 条基线为 `unknown`，判为不可作能力证据** | `--self-test`、真实产物实测 |
| 新鲜度门的负对照 | passed | `check_distillation_freshness.py --self-test` |
| 检查器元普查（负对照有没有） | 11 件中 **6 OK / 4 无负对照 / 1 不可独立验证** | `check_checkers.py scripts/ --json` |
| 蒸馏版本新鲜度 | 下限 `v0.0.0.10`；见下方说明 | `check_distillation_freshness.py` |
| Release checksum 全量校验 | passed，**276 files** | `self_check.py` |
| Canonical group validation | **12 categories, 99 products, 101 artifacts**; passed | `validate_persona_registry.py` |
| **团队侧版本绑定（group v0.0.0.9 新增）** | **passed**，三处同为 `v0.0.0.9`；负对照 6 类全抓出 | `persona-distiller-group/scripts/check_group_version_binding.py` |
| Identity family registry | 12 families；加权多身份输入被拒 | `test_identity_routing`、`test_skill_contract` |
| Builder JSON Schema | 14 documents | `self_check.py` |
| Python script 覆盖 | **50 scripts** | `self_check.py` |
| Root `SKILL.md` 行数 | 206 行；self_check 未报越界 | `self_check.py` |
| Secret-pattern scan | **0 findings** | `self_check.py` |
| Reviewer harness 两轮 | passed | `test_six_reviewer_harness_passes_both_rounds` |
| Person-delivery deterministic rebuild | passed | `test_target_package_is_deterministic_for_unchanged_state` |
| Person-delivery checksum tamper rejection | passed | `test_packaged_target_installer_verifies_checksums_and_rejects_tamper` |
| Runtime history reset / 调用不编号 | passed | `test_runtime_recording` 全部用例 |
| Concurrent unnumbered audit append | passed | `test_zz_runtime_concurrency` |
| Per-person product registration | first / next / gap / idempotence / contention / 999 / exhaustion passed | `test_persona_registry` |
| Cross-category uniqueness | passed | `test_persona_registry` |
| Complete-release deterministic rebuild | passed | `test_complete_release_is_one_deterministic_zip_and_installs_both_skills` |
| Complete-release checksum tamper rejection | passed | `test_complete_release_installer_rejects_tampering` |
| Atomic dual-Skill clean install | passed | 同上用例内 |

## ⚠ 必须与「PASS」一起说的两件事

### 一、新鲜度两版之内从 100/100 掉到 4/101，**掉的是尺子不是产物**

| 版本 | 下限 | 达标 / 总数 |
|---|---|---|
| v0.0.0.16 | `v0.0.0.6` | **101 / 101** |
| v0.0.0.17 | `v0.0.0.7` | 9 / 101 |
| v0.0.0.18 | `v0.0.0.8` | 4 / 101 |
| **v0.0.0.19（本版）** | **`v0.0.0.9`** | **2 / 101** |

产物一份没变，三版之内达标率从 100% 掉到 2%。
原因是绝大多数条目的 `distilled_with` 挤在 `v0.0.0.6`–`v0.0.0.7` 一小段上，
整批贴着旧下限站着——它们来自 `a31cb12d` 的十二族重组，那次**只重打包没重蒸**。
**下限每往前推一格，就有一大批一起掉下去。**

按用户 2026-07-29 的裁定：**下限以下不重蒸、只记台账、不阻塞任何流程**
（`check_distillation_freshness.py` 默认只报不拦，`--strict` 存在但发行流程不用）。
收窄的唯一途径是**600 人完成后统一重蒸**（任务 #29）。
**单说「PASS」而不说这 92 条，就是拿绿灯掩盖一件已知的事。**

### ★★ 零之前：**负对照跑出来了，结果是负的**

2026-08-02，Livermore #100 首次盲态 A/B（32 条同一提问 × 2 席独立评委 = 64 对，
A/B 归属按 `case_id` 哈希逐条翻转，**不给评委任何 rubric**）：

| | 值 |
|---|---:|
| 产物 | **0.7369** |
| 裸模型 | **0.8444** |
| **真 delta** | **−0.1075** |
| 逐对胜负 | 产物 10 胜 / **裸模型 54 胜** |
| 对照：自撰稻草人算出的 delta | +0.8012（**虚高 0.9087**） |

**十六个套组里，产物只在 `fact-preservation` 一处胜出（+0.247）**，其余十五处全负；
最差的是 `known` −0.275、`capability-calibration` −0.268、`long-horizon` −0.230。

两席盲判**各自独立**指出同一机制：**拿边界当答案**——
自称手握 16 份材料却只报计数、被问「发生了什么」却用「不能推断想法」挡回去、
被要求给判断却以「语料里没有前瞻检验」拒绝。
以及：`own_voice_ratio`、份数、词频这类**内部遥测，用户拿不走**。

**结论必须写死**：本产物集是**引文核查器，不是决策助手**。
在归属类问题（这句是不是他说的）上有真实优势，
在判断、规划、执行类问题上**目前是净负担**。

### ★ 零、最重要的一条：**产品本身从未做过负对照**

用户 2026-08-02 评分指出：没有任何「专家团队相对裸模型在真实盲测任务上提高多少正确率」的结果。

**诊断**：本 skill 给每一件检查器都做了负对照（第十八种执行了三十多个版本），
**唯独没有给产品本身做过**。每个人物 eval 里的 `baseline` 是**作者手写的稻草人**——
Livermore #100 第 2 轮 E 席原话：「候选/对照的分差被显著放大，**不能当作能力证据**」。

**因此：本文件与任何产物报出的 `delta`，在「比裸模型强」这个问题上等于零信息。**
v0.0.0.20 落成 `check_baseline_provenance.py` 把这件事变成机器可见的：
`self-authored-strawman` 与缺字段一律判为不可作能力证据，
**已入库产物实测 64/64 条命中**。

**该门在 `--strict` 下会让发布失败——这是有意的**：唯一的解法是拿真实的裸模型基线来跑。

### 二、11 件检查器里有 4 件没有负对照

`check_absence_claims` / `check_claim_anchors` / `check_redundancy` /
`check_schema_drift` **没有 `--self-test`**，`check_quote_integrity` 有但不可独立验证。
**没有负对照的检查器，它的「全绿」不构成任何证据**（RUNBOOK 第十八种）。
这四件目前的结论只当参考，元普查每次都会把它们点出来。

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
