# External views, criticism, and counterexamples

## Scope and assigned sources

**本道无独立 train 源。** 台账里没有任何一份属于 external 维度的二手传记/评论专书（source-ledger 的 `dimensions` 全部落在 writings/conversations/expression）。因此本道**不产出"独立二手观察"**；下面只如实记录：语料中存在的、**嵌在 train 源内部的"外部/编者声口"**——它们不是 Say 亲述，但确实是关于 Say 的二手评价与批评，可作为 external 层的下限证据。这些声口所在的三份源均在 train split 内，可安全引用。

★ 本节由台账机械导出（`emit_lane_scope.py`）**不适用**（本道 0 源）；以下内容为本研究阶段的人工记录。

## Source-linked observations

### ① 嵌入 `src-0d7cfabc38d1`（Letters to Malthus 英译卷首）的译者 Preface（J. R. = John Richter）

Richter 在 1821 年英译卷首给 Say 定位：

> Mr. Say was the first writer who attempted to raise Political Economy to the rank of the exact sciences
<!-- src-0d7cfabc38d1 -->

（译者把 Say 捧为"把政治经济学提到精密科学之列的第一人"——**二手尊崇评价**；同段还批评 Malthus 在《原理》中"controversy"了这门科学最确证的原理，改述。出处层：这是 J.R. 的话，不是 Say 的话。）

### ② 嵌入 `src-47686e48abd4`（Traité 英译 1821）的译者脚注（C. R. Prinsep）

Prinsep 在翻译第 4 版法文《概论》时加注，**公开不赞同 Say 的价值论**：

> It is remarkable, that he should throughout the whole of Book I. treat value as founded wholly upon utility, whereas in Book II. he seems to admit, that difficulty of attainment determines its ratio. Smith appears to have considered the labour expended in surmounting the difficulty of attainment to be the groundwork, as well as the measure of value; and he has been followed in the first part of that opinion by Ricardo.
<!-- src-47686e48abd4 -->

（Prinsep：Say 第一卷把价值全建立在效用上、第二卷又似乎承认"取得难度"决定其比例——**同时代的译者对作者内部一致性的批评**；并指出 Smith/Ricardo 走的是另一条路。脚注以 `T.` 署名，属编者层；`groundwork` 原文如此，无连字符。）

### ③ 嵌入 `src-4f99e70027da`（Oeuvres diverses 1848）的编者 Notice（Ch. Comte / Blanqui / Reybaud 源）

notice 层对 Say 的**性格画像**与**学界评价**（第三人称二手）：

> Personne ne mit plus de soin que lui, n'employa plus de temps à se former un corps de doctrines; personne aussi, quand il fut formé, ne s'y attacha ... Ce fut avant tout un esprit exact, une intelligence sûre.
<!-- src-4f99e70027da -->

> La ... des débouchés, en prouvant que chaque nation est intéressée à la prospérité de toutes les autres, exercera la plus heureuse influence sur le sort de l'humanité.
<!-- src-4f99e70027da -->

（`La tbéorie`=La théorie 的 OCR 形，以省略号跳过；"ne s'y attacha d'une manière plus inébranlable"中 `d'ine`/`inébraulable` 亦为讹形，以省略号处理。编者评：销售法则"证明每个国家都关心所有其他国家的繁荣"，将造福人类——**后死者的盖棺定论**，比 Say 自述更乐观。）

### ④ 嵌入 `src-8249fec8789a`（Trattato 1854 合卷）的编者导言（Prof. Fr. Ferrara）

Ferrara 在 1854 年"经济学丛书"卷首回顾：

> non v'ha, io credo, che Sismondi e Malthus ... della teoria degli sbocchi, in cui G. H. Say nulla ha lasciato ... a' suoi successori
<!-- src-8249fec8789a -->

（OCR 讹形照录：`G. H. Say`=G. B. Say；句首"nella questione del general glut"在语料中作 `qnistione`/`generai glnt` 等讹形，已以省略号处理。Ferrara：一般过剩问题上只有 Sismondi 与 Malthus 还抗拒"销路理论"的明显性，该理论 Say 已做到后来者无可再加——**19 世纪中期的学界评价**，兼有"Say 学说胜利"的判词性质。）

## Candidate Claims

- C-X1（lineage，二手）：本库 train 语料**无独立 external 源**；四份外部/编者声口全部嵌在 train 源内部（译者 Preface、译者脚注、编者 Notice、编者导言），引用时必须标声口层（src-0d7cfabc38d1 / src-47686e48abd4 / src-4f99e70027da / src-8249fec8789a）。

## Contradictions and alternative explanations

- **编者评价与 Say 自述的温差**：Richter/Ferrara/notice 对销售法则的评价（"第一人/无可再加/造福人类"）明显高于 Say 在书信里自己承认的"这命题有悖常理、招致偏见"（`I am aware that this proposition has a paradoxical appearance, which creates prejudices against it`，src-0d7cfabc38d1）——下游模型若按编者口径表态，会偏离 Say 本人的谨慎。
- **Prinsep 的价值论批评与正文冲突**：正文（Say 层）说效用是价值基础，Prinsep 注（编者层）说价值=效用＋取得难度——同一本书里两种口径并存，引用须指定层。

## Unknowns and source gaps

- 本道 0 独立源：**没有专门的二手传记、没有对立学派的整部评论**。Ricardo 对 Say 的回应、Mill、马克思对萨伊定律的批评等均不在本库 train 语料内——凡涉及这些的断言一律无证据、不可写实。
- 嵌入声口只取到四份的可见部分：Richter Preface 未逐字通读、Prinsep 全注未枚举、notice 与 Ferrara 导言只精读了与学说评价相关段——其余编者内容未穷尽。

## Proposed Holdout cases

IDs only; research Agents must not inspect Holdout bodies.

## Handoff to adjudication

- C-X1 作为 lineage 元断言，交代"external 层由嵌入声口支撑、无独立源"——下游模型文档与 claims 的"语料覆盖/声口层"说明必须引用它，防止把编者的话当 Say 的话。
- 建议把 Richter/Ferrara 对销售法则的**后世评价**作为"外部验证"证据，但只用于说明"学说传播史"，不用于给 Say 本人"加光环"。
