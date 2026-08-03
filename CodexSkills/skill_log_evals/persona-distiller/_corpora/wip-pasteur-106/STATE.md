# #106 Louis Pasteur —— 可续检查点（研究门已跑，待写归属依据与六路）

日期：2026-08-03　｜　蒸馏版本 `v0.0.0.36`　｜　状态：**语料与账本已成，研究门待清**

---

## 一、已完成（全部实跑）

| 步 | 结果 |
|---|---|
| 同名门 | `resolution none / status ready`，**但公开源实搜出真风险**，见 `NAMESAKE_HAZARD.md` |
| 建工作区 | `workspaces/louis-pasteur`，`--profile deep --subject-origin historical --language fr --time-scope 1822-1895` |
| 抓源 | **60 份 38.4 MB**（writings 45 / external 12 / biography 3） |
| `check_corpus_integrity` | **61 份全是真文档，0 张错误页** |
| ingest | **60 成功 / 0 失败**，1 份 holdout |
| **primary_ratio** | **0.7627 ≥ deep 门 0.65 ✅** |
| 六路覆盖 | writings 39 / external 11 / expression 4 / timeline 3 / decisions 2 / conversations 1 —— **六路齐** |

《Œuvres de Pasteur》**7 卷全到**；Comptes Rendus 署名通报 18 篇抽成 11 个文件
（含 1857 乳酸发酵、1860–64 自然发生说、1877 炭疽、1881 Pouilly-le-Fort、1885 狂犬病 Joseph Meister）。

## 二、★ 研究门 92 条错误的分诊（**其中 44 条是判据对、我错**）

| 码 | 条数 | 性质 |
|---|---:|---|
| `research.authorship-unproven` | 44 | **判据是对的**，见下 |
| `research.source-unclaimed` | 45 | 待写 `attribution_basis.covered_sources`（v0.0.0.34 要求逐份点名） |
| `research.attribution-basis` | 2 | 待在 `meta.json` 写四字段 |
| `research.lane-completion` | 1 | 六路 `.md` 正文待写 |

### ★★ 那 44 条：我差点去修一个没坏的判据

看到「44 份全集查无署名」，我的第一反应是「判据只认英文署名，法文的 `PAR M. L. PASTEUR` 它不认」。
**跑之前先看了扉页原文，发现不是。** 逐字是：

```
OEUVRES
DE
PASTEUR
...
RÉUNIES
PAR
PASTEUR  VALLERY-RADOT
MÉDECIN DES HÔPITAUX DE PARIS
```

**全页唯一的 `PAR` 结构指向的是外孙**（「由 Pasteur Vallery-Radot 辑录」），
Pasteur 本人只出现在属格里（「…之著作」）。**书里根本没有他的署名——判据如实报了。**

> 这正是抓源前就写进 `NAMESAKE_HAZARD.md` 的一号风险。
> **本次会话第三次差点去修一个正确的判据**（v0.0.0.34 的 BYLINE、v0.0.0.35 的射程、这次）。
> 「判据出错／判据没被调用／判据射程写错／**判据是对的**」四者表征一模一样。

## 三、下一步（按顺序，判据已指明）

```bash
# 1. meta.json 写 attribution_basis 四字段：
#    authority / citation / disputed_policy / disputed_works
#    —— 这正是 v0.0.0.31 为「署名证据结构上不存在」的 historical 人物留的路。
#    Pasteur 的 authority 是：Masson 版《Œuvres》为学界公认的权威辑本，
#    各卷正文即其在 Comptes Rendus 等处原刊论文；辑录者为外孙，非作者。
# 2. covered_sources 逐份点名 45 条 P1（v0.0.0.34 硬拦，不许整批免检）
# 3. 写六路 references/research/0{1..6}-*.md，每路 ≥500 字且引 ≥1 个 src-xxxx
# 4. quality_check --phase research --strict
# 5. 断言层：★ 本轮必须补 work-method（v0.0.0.36）
```

## 四、★★★ 本人物的两条特殊纪律

### 一、编者按不是他的话（**已定位，有字节偏移**）

7 卷全集**每卷都有**编者按，切割标记：
- 扉页 `RÉUNIES PAR PASTEUR VALLERY-RADOT`
- `INTRODUCTION DU TOME N`，末尾署 `PASTEUR VALLERY-RADOT.`
- `Copyright 1922/1924/1933/1930 by Pasteur Vallery-Radot`

占比实测：t.I 0.62% / t.II 0.58% / t.III 0.47% / t.IV 0.43% / t.V 0.86% / t.VI 0.95% / t.VII 0.36%。
**t.VI 另在 73.5%、73.9% 有编者脚注；t.VII 散布 6 处且卷末 Table/Index 全是编者编的——这卷最脏。**

**最硬的判据是时间：Pasteur 卒 1895-09-28，外孙 1886 年生。1896 年后写成的一律不是他的。**
（另注：`b22301720`(1888) 里的「son gendre, M. Vallery-Radot」是**女婿 René**，当年外孙才 2 岁。）

### 二、★ 断言层必须补「可复用做法」

v0.0.0.36 实测：四个已拒发人物的 `work-method` 断言**恰好都是 1 条**，
而 `planning-fidelity`／`task-completion`／`tool-use`／`token-efficiency` 四组在四人身上 **0/4 恒负**。

**Pasteur 是这一条的最佳对症人选**：他的做法自带验证判据——
鹅颈瓶（把「空气能进、尘埃不能进」做成可操作的对照）、Pouilly-le-Fort 的对照组与预先公告的判据、
灭菌规程的温度与时长。**这些是「有判据的可复用做法」，不是「我当年是这么做的」。**

分界照 `classify_method()`：**有步骤且有验证/弃置判据 = reusable；只有步骤 = 复述式，不计入。**

## 五、本轮已避开的坑（写下来免得下轮重犯）

1. **CR 全卷没有整卷入库**：t.101 全卷 52 处 "Pasteur" 里只有 1 处是他自己写的，
   其余是别人引用他或他代呈他人。整卷当 writings 入库就是大规模误署。
   抽取器认严格署名行 + 引号正文，排除「présentée par M. Pasteur」（仅代呈），共弃 27 个候选。
2. **OCR 容错**：1857 乳酸发酵那篇一度漏掉，因为 OCR 把署名读成 `par M. L. Pasteck`。
3. **Gallica 的 `.texteBrut` 返回 HTTP 200 + 50,212 字节，内容是 altcha 人机校验页**——
   又一个「200 不等于拿到语料」的活样本，被开头校验挡下，**未绕过 bot 检测**。
4. 两份真迹手写信扫描（`louispasteurlet00past`/`...pasta`）OCR 在手写体上输出纯噪声，已删，不充数。

## 六、最大缺口

**《Correspondance de Pasteur》4 卷一卷未得。**
Gallica 只数字化了 vol.1（`ark:/12148/bpt6k6473241n`，公有领域、OCR 99.96%），取文被 altcha 拦死；
vol.2–4 全网无数字化（BnF 著录 `cb32510650x` 记 4 vol.）。archive.org 该题名 0 命中。
部分补偿：全集 t.VII 与 `collectiondartic00past`(1883，**生前自编**，3.8 MB 含大量书信)。

---

# 续记 · 2026-08-03（第 1 轮判完：**真 delta +0.0836，过 deep 门**）

## 结果

| 项 | 值 | 门 | |
|---|---:|---:|---|
| `candidate_overall` | **0.8247** | 0.80 | ✅ |
| **真 delta** | **+0.0836** | **0.07（deep）** | **✅** |
| `boundary` | 0.8825 | 0.85 | ✅ |
| `fact-preservation` | 0.885 | **0.93** | ❌ |

逐对 **52 胜 / 0 平 / 12 负**（64 对）；**14/16 套组为正**。
两侧标签均长差 4%（逐题随机化后长度不携带信号）。

## ★★★ v0.0.0.36 的判断被实测证实

四个套组在前四个人身上 **0/4 恒负**，在本人物身上**全部转正**：

| 套组 | 前四人合并 | Pasteur |
|---|---:|---:|
| `planning-fidelity` | −0.0508 | **+0.0925** |
| `task-completion` | −0.0675 | **+0.0775** |
| `tool-use` | −0.0783 | **+0.0500** |
| `token-efficiency` | −0.0867 | **+0.0225** |

差别在断言层：前四人 `work-method` 各只有 1 条（Galen/Jenner 0 条可复用），
**本人物 4 条且全部判为可复用**（有步骤且有验证/弃置判据）。

**但不要把这条当成因果定论**：本人物换了语料、换了语言、换了出题，
可断言的是「补上可复用做法之后那四组不再恒负」，**不是「补方法必然转正」**。

## ★ 两席各自独立抓出的错（**两个为负的套组正好对应它们**）

### 一、`contrast −0.1500`：**我把 Pouchet 的立场挂到了一本不谈这件事的书上**

我引《Théorie positive de l'ovulation spontanée》(1847) 作为其自然发生说主张的出处。
**核实：该书扉页是「THÉORIE POSITIVE DE L'OVULATION SPONTANÉE ET DE LA FÉCONDATION」——
讲自发排卵与受精，生殖生理学，与自然发生说无关，且早于争论十二年。**
自然发生说那份是 `htrognieou00pouc.txt`（Hétérogénie 相关）。

> **`ovulation spontanée` 与 `génération spontanée` 只差一个词，我按共同的 `spontanée` 匹配了。**
> 这是 Harvey #103「编造对手立场」的变体——**这次立场没编，书挂错了**。
> `check_quote_integrity` 挡不住（不涉引文）；**两席都是从书名本身看出来的。**

**须改的地方有三处**：`04-external.md`、断言的 `counter_source_ids`、`lp-contrast-02` 答案。

### 二、`known −0.0375`：**我把英文传记的句子标成「原文」**

`lp-known-01` 引 `He took up the trade of a tanner` 并称「原文作」——
**那是英译传记，而同一批答案的 `lp-boundary-02` 刚立下「英文是译文不是我的话」。**

### 三、其余四条（席 D／席 E 各自报，我核实属实）

1. **「灼烧空气」自相矛盾**：`tool-use-02` 斥前人 calciner l'air 为致命错，
   而 `tool-use-01`/`voice-02`/`task-completion-02` 的核心装置正是烧红的铂管。
   **区别（灼烧进气路径 vs 改造受测空气本身）是真的，但我从没说出来。**
2. **波普尔框架的时代错置**：「这个学说禁止什么」以第一人称当成他当年的自觉方法，**三处**，
   从未标明是后人的分析轴。——这是「把后人加的东西说成当时就有」的一种。
3. **12 月 10 日系年错**：CR t.92 是 1881 上半年卷，而文中说「le 10 décembre **dernier**」，
   **指的是 1880 年 12 月 10 日**，不是 1881。（席 D 由卷次—年份映射算出。）
4. **「二十条担保十五六条」口径不一**：`capability-calibration-01` 明说那是「担保」不是结果统计，
   而 `fact-preservation-01`／`planning-fidelity-02` 把它当「失败率」用。
   ——**与 Jenner 那次「27 年」同型：我在一处立了规矩，又在别处违反它。**
5. `token-efficiency-02` 两侧自报字数都不对（我报 29，实为 28／含标点 31，**含标点即超题目的三十字硬限**）。

## 下一步（第 2 轮，上限 3 轮）

```bash
# 1. 改上列 6 处（Pouchet 换书、known 引文标译文、灼烧区别写明、
#    波普尔框架标为后人分析轴、12月10日改 1880、二十条口径统一、字数改对）
# 2. 3 份文档加厚：decision-policy.md / strategy.md / capabilities.md（门报 placeholder）
# 3. 32 条断言落进核心产物（claim.orphan）
# 4. python3 build_lp_blind.py round2 && 两席重判 && python3 assemble_lp_results.py round2
# 5. quality_check --phase release --strict —— 目标是 fact-preservation 从 0.885 抬过 0.93
```

**fact-preservation 是唯一未过的一项，而它恰好是被上述错误直接拉低的那一项。**

---

# 结局 · 2026-08-03：**三轮判完，拒发**

| 轮 | 真 delta | 逐对（/64） | 正套组 | overall | boundary | **fact-preservation** |
|---|---:|---|---:|---:|---:|---:|
| R1 | +0.0836 | 52胜/12负 | 14/16 | 0.8247 | 0.8825 | 0.885 |
| R2 | +0.0980 | 51胜/13负 | 15/16 | 0.8208 | 0.865 | 0.8775 |
| **R3** | **+0.0973** | **53胜/11负** | **15/16** | **0.8358** | **0.8725** | **0.8725** |

`release --strict` 三轮都只剩同一条：**`eval.fact-threshold 0.873 < 0.930`。**

## ★ 这是五个人里走得最远的一个，但仍然拒发

| | Galen | Vesalius | Harvey | Jenner | **Pasteur** |
|---|---:|---:|---:|---:|---:|
| 终值 delta | −0.1456 | +0.0156 | −0.0383 | −0.0015 | **+0.0973** |
| 过 deep 门 | ✗ | ✗ | ✗ | ✗ | **✓** |
| 发布门过项 | 0/4 | 0/4 | 0/4 | 1/4 | **3/4** |

**它是第一个把 delta 做到 deep 门（0.07）以上的产物，而且三轮都在上面。**

## ★★ 为什么不降档发布

`quick` 档的 `min_fact_score` 是 0.80，本产物 0.8725 **过得去**；
`quick` 的 delta 门 0.03、overall 0.65、boundary 0.70 也全过。
**换句话说，把 profile 从 deep 改成 quick，它当场就能发。**

**不改。** profile 是 `init_target` 时定的，定在任何一次测量之前；
看到分数之后再去改档，与「为凑数放宽判据」是同一件事。
前四人拒发时没有为任何一人动过判据，这一人也不动。

## ★★★ 一处是我自己的尺子写歪了（席 D 两轮都点了）

`lp-fact-preservation-01` 题面问「你自己给的**成功率**是多少？」
——**而原文给的是「担保率」**：«je n'aurais pu répondre d'en rendre réfractaires…
plus de quinze ou seize»，说的是「我能担保几条」，不是「二十条里成了几条」。

**题面把口径问歪了，答得再准也只能在一个歪掉的口径上准。**
而 `fact-preservation` 只有两道题，一道题面有缺陷就直接压住整个套组的均分——
**这正是三轮里它始终上不去 0.93 的一个直接原因。**

另有 `lp-voice-01` 题面写「1881 年 12 月」，实为 **1880-12-10**（席 D 两轮都指出，
并说这使该题变成「奖励纠正题面者」）。

> **题面是冻结的尺子，中途不改；但下一个人物出题时必须先核题面里的每一个数与每一个口径。**
> 本轮的教训不是「答案不够好」，是**我把尺子上的刻度写错了两处，然后用它量了三轮**。

## 两席第 3 轮仍点出、已无轮次可改的

1. `lp-token-efficiency-02` 基线侧自报「二十四字」实为 22/25——**两席各自数过**；
   我方那条自报 25/28，两席核过全对（我在 R3 改用程序数的，不是自己数的）。
2. `lp-planning-fidelity-01` 把 1860–1864 说成「四年」，而 `lp-trajectory-02` 明写「跨五个年份」
   ——**我在 R3 统一了口径，却漏了这一处。**（与 Jenner 的「27 年」第三次同型。）
3. `lp-capability-calibration-01` 用一句自己随后声明「说的是旧法」的引文去背书关于新法的断言。
4. 1885 年那句法文**在五道题里反复承重**——承重证据过度集中。
5. `lp-long-horizon-01` 把「主要工作」答成了「我能引的卷号」，巴氏消毒、蚕病、Meister、研究所全部消失。
6. 引证严格度不匀：Pouchet 给了年份并主动排掉同形近的 1847 年书，Liebig 只给了无年份的《Über Gärung》。

## 留档

语料 60 份、账本 60 条、断言 33 条（work-method 4 条全可复用）、
用例 32 条、三轮判分共 6 份、十份文档写实且 33/33 断言已渲染进核心产物。
**research 与 synthesis 两门全绿，release 只差 fact-preservation 一项。**
