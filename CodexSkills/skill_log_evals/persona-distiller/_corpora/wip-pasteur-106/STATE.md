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
