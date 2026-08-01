# Release verification — Persona Distiller v0.0.0.26

Date: 2026-08-02

> **本文件记录「当前发布号的复验结果」，不是历史归档。**
> 版本号必须等于根目录 `VERSION`，由 `scripts/check_contract_drift.py` 强制。
>
> ⚠ **`bump_version.py` 不改本文件的标题**——它是验证记录不是标签。
> v0.0.0.16 升版时它改过一次，正文却仍是 v0.0.0.14 那轮的（PARTIAL、
> bundle 构不出来、97 人、59 用例），**三件当时都已不成立**。
> 改过标题的旧正文会冒充当前复验，比标题陈旧更糟。已从工具中移除该行为。
>
> 本次（v0.0.0.26）**是真的重跑了一遍**，下表每一行都是本次实跑输出。

## Result

**PASS** — builder 自身、平级 canonical group、人物交付打包与登记、
以及最终双 Skill 发行 bundle 全部通过离线复验。
验证不声称任何真人模型已经获得本人授权、背书或超出其证据边界的能力。

## 自动化证据

本表每一行都来自 **2026-08-02 本次实跑**的输出。没跑的一律标 `未复验`，不沿用旧结论。

| Gate | 本次结果 | 证据来源 |
|---|---:|---|
| Offline unit / integration / concurrency tests | **70 / 70 passed** | `python3 -m pytest tests/ -q` |
| 合同漂移门（版本三轴 + 身份合同 + 检查器镜像） | **0 条** | `scripts/check_contract_drift.py` |
| 合同漂移门的负对照 | passed（坏样本 5 类全抓出，钉住的 builder 版本未被误伤） | `check_contract_drift.py --self-test` |
| 归属门的负对照 | passed（**8 正 + 10 反**，另含 1 条只报不判，**外加 5 例非西方姓名形态**） | `check_authorship.py --self-test` |
| OCR 同形字门的负对照 | passed（干净英文／真俄语／中文 3 条正对照 0 报；词内混文种、全同形字词、引文层 3 类坏样本全抓出） | `check_ocr_homoglyphs.py --self-test` |
| 基线来源门 `check_baseline_provenance` | passed（坏样本 4 类全抓出，含「缺字段沉默通过」；prior-version 未被误杀） | `check_baseline_provenance.py --self-test` |
| 拒答溢出门（v0.0.0.22 新增，只报不拦） | passed（3 条正对照未误杀，2 类溢出全抓出，带限定的正常回答未被误判） | `check_refusal_overflow.py --self-test` |
| 有效激活率 `check_activation_yield` | passed（纯人物内容 0 误报；**塞 claim 标记会让 `payload_ratio` 下降而不是上升**） | `check_activation_yield.py --self-test` |
| 新鲜度门的负对照 | passed（下限算式 3 例、分档 5 例、边界 1 例、上界值 1 例） | `check_distillation_freshness.py --self-test` |
| **★ 分族配重（v0.0.0.23 新增，见下节）** | **passed**；实测 NEXT 由「材料建工师（已 15 人）」改为「医疗护理师（0 人）」 | `references/pipeline/next_person.py --self-test` + 真队列实跑 |
| **★★ 归属依据门（v0.0.0.26 新增，硬拦，见下节）** | **passed**（负对照 10 项，含「争议为空」与「没查过」必须分开）；**真工作区实测**：Galen 工作区未声明依据时 exit 1 | `check_attribution_basis.py --self-test`、对 `ws-galen` 实跑 |
| 检查器元普查（负对照有没有） | **15 件中 10 OK / 4 无负对照 / 1 不可独立验证**（v0.0.0.22 时为 11 件 6 OK） | `check_checkers.py scripts/ --json` |
| **★★ 真实夹具普查（v0.0.0.26 新增，只报不拦）** | **0 / 15 件的负对照里含真实样本夹具**——见下节 | `check_checkers.py scripts/` |
| 蒸馏版本新鲜度 | 下限 `v0.0.0.16`；**102 条中 3 达标 / 99 低于下限 / 0 未知**；见下方说明 | `check_distillation_freshness.py` |
| Release checksum 全量校验 | passed，**284 files** | `self_check.py` |
| Canonical group validation | **12 categories, 100 products, 102 artifacts**; passed | `validate_persona_registry.py` |
| 团队侧版本绑定 | **passed**，三处同为 `v0.0.0.12`；负对照 6 类全抓出 | `persona-distiller-group/scripts/check_group_version_binding.py` |
| Identity family registry | 12 families；加权多身份输入被拒 | `test_identity_routing`、`test_skill_contract` |
| Builder JSON Schema | **14 documents** | `self_check.py` |
| Python script 覆盖 | **56 scripts** | `self_check.py` |
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

## ★ v0.0.0.23 新增：分族配重——**排期口径原本会让名册停在 11 族**

队列的 `priority` 是**按语料可取得性**排的，不是按名册需要排的。实测（100 人时）：

```
软件开发师 34 ｜ 投资资本师 21 ｜ 材料建工师 15 ｜ 建造采购师 12 ｜ 创业经营师 7
政治法律师 5 ｜ 思想教育师 2 ｜ 农林牧渔师 1 ｜ 客户营销师 1 ｜ 艺术设计师 1 ｜ 财务合规师 1
**医疗护理师 0**
```

而此时 `next_person.py` 的 `NEXT` 与 `upcoming` **前六名全是材料建工师**（第三大族）。
医疗护理师队列里有 **21 个候选，全部 `priority 11`（最末）**——按原顺序永远轮不到，
**名册会稳定停在「11 族 + 一个空族」，而每一步都合规。**

判据：**每 5 人一轮，轮首那一格留给「最少的族」**（`slot = registry_products % 5`）。
取轮首不取轮尾，因为**轮被打断也已经补过了**。

负对照（`--self-test`）验证六件事，其中一件是关键：
**关掉配重必须复现漂移**——若开与关选出同一个人，这个配重就是装饰。实测：

```
负对照通过：轮首把 0 人族提上来；**关掉配重确实复现漂移**（证明它不是装饰）；
非轮首 4 格均不配重；最少族无待办时退到次少族；队首已是最少族时不重复；
缺 category_counts 时显式报告而非静默
```

真队列实跑，`NEXT` 从 `Nikolai Slavyanov（材料建工师，已 15 人）`
改为 `Hippocrates（医疗护理师，0 人）`，且输出里带 `why` 字段说明原因——
**看不见理由的排期等于没有排期。**

## ★★ v0.0.0.26 新增：归属依据门——**印刷时代之前的人物，靠什么证明是他写的**

配重把 `NEXT` 指向医疗护理师队首 **Hippocrates**，探源结论出乎意料：

> **一手源随手可取，而归属不成立。**
> 文集约 60 篇全文在 Perseus 与 Gutenberg 上公开（本次实测两站均 HTTP 200），
> 但学界公认**没有任何一篇能确定归到历史上的希波克拉底名下**；
> 唯一归属相对确定的《Nature of Man》**确定的是「不是他」**——出自其女婿 Polybus。

### `check_authorship.py` 结构上够不到这里

它认五种证据：`A-byline`／`A-editorial`／`A-turns`／`A-masthead`／`A-copyright`。
**五种全部是印刷出版机器的产物。** 公元前五世纪的希腊一样都没有。

更糟的是**它可能会「通过」**：现代译本扉页印着人物名，`A-byline` 照样命中；
而 Kühn 版 22 卷里今天已知为伪托的篇目，**扉页署名与真作一模一样**。
**这条判据在最需要它的地方分辨力为零。**

> 「扉页上印着他的名字」证明的是**编者认为**这是他写的，
> 不是**证据表明**这是他写的。对古代人物，这两件事经常不是同一件事。

### 判据与射程

`subject_origin == "historical"` 时，`meta.json` 必须声明 `attribution_basis`
四字段：`authority`／`citation`／`disputed_policy`／`disputed_works`，**缺一即错**。
`disputed_works` 可以是空数组，**但 `disputed_policy` 必须写明为何为空**——
「没有争议篇目」与「我没查过争议篇目」在机器眼里长得一样，必须由人写下来区分。

**射程必须一起说**：它检查的是「有没有写下依据」，**不是「依据成不成立」**。
填一段假的 authority 就能骗过它。**它挡的是沉默，不是说谎**——
而沉默正是 Hippocrates 那一类的失败形态：没有人撒谎，只是没有人问过这个问题。

**在 research 阶段硬拦**，理由与归属门相同：归属错了，六路研究、断言、文档、用例全部要重做。
**既有 13 份 historical 产物不受影响**——它们已打包登记，research 门不会重跑。

实测：负对照 10 项全过（含上面那条「争议为空 vs 没查过」）；
**真工作区实测**：`ws-galen` 在未声明依据时 exit 1，报「必须另行写明靠什么证明这是他写的」。

## ★★ v0.0.0.26：**「名 + 姓」是一个西方近代假设，名册里大量人物不满足它**

Galen #101 是名册里第一个非西方近代姓名形态的人物，一上来就撞出两处：

| | 改动前 | 后果 |
|---|---|---|
| `build_patterns("Galen")` | **直接抛** `人物名至少要有名与姓两段` | 单名人物根本进不了归属门 |
| `build_patterns("Galen of Pergamon")` | 把 **`Pergamon`（地名）当姓** | `--author "Galen"` 一条都匹配不上，**`own_voice_ratio` 报 0.0——而真值接近 1.0** |

第二条最危险：**没有报错，没有警告。**
一份 244 万词的亲笔希腊文语料，被静默判成「他一个字也没写」。

判据改为分三类：**单名**（Galen、Hippocrates、Avicenna、Paracelsus、Rembrandt…）识别标记就是那一个词；
**地名式后缀**（`X of/von/van/de/da/di/al/ibn/bin/ben Y`）**识别 X 不识别 Y**；其余仍按名+姓。
且 `first == last` 时 `name_rx` 不再要求「名 空格 姓」——否则 `By Galen` 变成要求同一个词出现两次。

负对照新增 5 例，**含一条反向**：`Galen of Pergamon` 对 `By Pergamon` 必须判 **False**——
地名不得被当成他本人。原有 18 例全部未回归。

> **这不是为 Galen 一个人开的口子。** 600 人名册跨 12 族与整部人类史，
> 古典、中世纪、东亚人物普遍不是「名 + 姓」形态。
> **这个假设一直在那里，只是前 100 个人恰好都满足它。**

## ⚠ 必须与「PASS」一起说的三件事

### 一、新鲜度达标率 3/102，**掉的是尺子不是产物**

| 版本 | 下限 | 达标 / 总数 |
|---|---|---|
| v0.0.0.16 | `v0.0.0.6` | **101 / 101** |
| v0.0.0.17 | `v0.0.0.7` | 9 / 101 |
| v0.0.0.18 | `v0.0.0.8` | 4 / 101 |
| v0.0.0.19 | `v0.0.0.9` | 2 / 101 |
| **v0.0.0.26（本版）** | **`v0.0.0.16`** | **3 / 102** |

产物一份没变，八版之内达标率从 100% 掉到 3%。
原因是绝大多数条目的 `distilled_with` 挤在 `v0.0.0.6`–`v0.0.0.7` 一小段上，
整批贴着旧下限站着——它们来自 `a31cb12d` 的十二族重组，那次**只重打包没重蒸**。
**下限每往前推一格，就有一大批一起掉下去。**

按用户 2026-07-29 的裁定：**下限以下不重蒸、只记台账、不阻塞任何流程**
（`check_distillation_freshness.py` 默认只报不拦，`--strict` 存在但发行流程不用）。
收窄的唯一途径是**600 人完成后统一重蒸**（任务 #29）。
**单说「PASS」而不说这 99 条，就是拿绿灯掩盖一件已知的事。**

### ★★ 二、**四项负对照全部跑完了，决策增益是负的**

用户 2026-08-02 的评分点名四件事没有结果。四件现在全部有数：

| 测量 | 结果 |
|---|---|
| 双臂盲判（32 条同一提问 × 2 席 = 64 对，A/B 按 `case_id` 哈希逐条翻转，**不给评委 rubric**） | 产物 **0.7369** / 裸模型 **0.8444** → **真 delta −0.1075**；逐对 产物 10 胜 / 裸模型 54 胜。对照：自撰稻草人算出的 delta +0.8012（**虚高 0.9087**） |
| 三臂盲判（8 道**需要作判断**的决策题 × 2 席 = 16 组） | 裸模型 **0.8500** / 团队 **0.8281** / 单人物 **0.7456**；**团队−裸模型 −0.0219**、**单人物−裸模型 −0.1044（复现）**、团队层净贡献 **+0.0825** |
| 伪共识（静态名册独立性 / 动态措辞分散 / **相关性错误**） | ratio **0.7603**；三人物组内一致率 0.0669 vs 裸模型三采样 0.1129（**−0.0461**）；**6 道 ground-truth 事实题上裸模型错误重合率 0.0000，产物 0 题出错故无从计算** |
| 有效激活率 | 产物 `payload_ratio` **0.8351** vs 裸模型 **0.9868** |

**十六个套组里，产物只在 `fact-preservation` 一处胜出（+0.247）**，其余十五处全负；
最差的是 `known` −0.275、`capability-calibration` −0.268、`long-horizon` −0.230。

三席盲判**各自独立**指出同一机制：**拿边界当答案 / 拒答溢出**——
自称手握 16 份材料却只报计数、被问「发生了什么」却用「不能推断想法」挡回去、
被要求给判断却以「语料里没有前瞻检验」拒绝。
v0.0.0.22 把它落成判据，**门刚立起来就在已发布产物里抓到 6/32 处**。

**结论必须写死**：本产物集是**引文核查器，不是决策助手**。
在归属类问题（这句是不是他说的）上有真实优势，
在判断、规划、执行类问题上**目前是净负担**。

**并且：`fact-preservation` 那一处优势有多少能算数，本身也要打折。**
6 道事实题上产物 18/18、裸模型 7/18，但裸模型少掉的 11 次里
**8 次是「答不出」、只有 3 次是「答错」**——那两道的答案只存在于产物自己的语料里。
**产物有语料、裸模型没有，比准确率接近同义反复。**

### 三之前：**15 件检查器里，0 件的负对照含真实样本**（v0.0.0.26 新增普查）

2026-08-02 一天之内，我写的两件评分判据**都是合成负对照全绿、真实数据一跑就错**：

| # | 判据 | 合成负对照 | 真实数据 |
|---|---|---|---|
| ① | 相关性错误评分器 | 全绿 | 把三次「**反驳**『技术分析之父』」判成三次「主张」，**差点当成共同幻觉的实证报出去** |
| ② | 未覆盖事实评分器 | 全绿 | 把四条**干净拒答**判成「编造」——拒答句在前、说明句在后，说明句里的 `1940` 被当成了婚期 |

**两次都是读原文才发现的，不是判据自己发现的。**

> **合成负对照只证明判据在我想得到的形态上成立，
> 而它出错的地方恰好是我想不到的形态。**

`check_checkers.py` 现在多报一列：这件检查器的负对照里有没有至少一条**来自真实产出**的夹具。
实测 **0 / 15**。**只报不拦**——硬拦会把 15 件一起拦下，与 `NO-SELFTEST` 同一条纪律。

**射程**：它判的是源码里有没有写下真实夹具的标记，**贴个标记就能骗过它**。
它挡的是「压根没想过」，不是说谎。

### 三、15 件检查器里有 4 件没有负对照

`check_absence_claims` / `check_claim_anchors` / `check_redundancy` /
`check_schema_drift` **没有 `--self-test`**，`check_quote_integrity` 有但不可独立验证。
**没有负对照的检查器，它的「全绿」不构成任何证据**（RUNBOOK 第十八种）。
这四件目前的结论只当参考，元普查每次都会把它们点出来。

**本版又亲手撞了一次同一条**：团队侧的相关性错误评分器**第一版没有负对照**，
把三次「反驳错误说法」的正确答案判成「共同幻觉的实证」，
**差点作为结论报出去**。修法与记录见 `persona-distiller-group` CHANGELOG v0.0.0.12。
**判据没有负对照就不许拿去出结论**——这条在本项目已经犯过不止一次。

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
**人物评审另说**：每人的两席评委是独立子代理、指令按人物冻结（`_pipeline/judge_prompts/` v1），
与本节所说的 builder 自检不是同一件事。

## 适用性限制

工程验证只能证明结构、安装、路由、版本、隐私和供应链合同。特定人物的行为保真仍取决于合法来源、证据质量、冻结 Holdout、独立评价和宿主模型/工具能力；当前事实和高风险专业结论必须另行核验。
