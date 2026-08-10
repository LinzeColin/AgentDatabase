# 01 著作（Writings and systematic works）

> 语种：**德文，无译文层**——本轮一份译本都没收（英译只有 1950 年 Piternick 那份，
> 版权状态未证实，按「开放获取 ≠ 公有领域」未取）。
> **所以本道不存在「译者的字被当成本人原话」那一整类问题**，可直接引德文原刊。
>
> ★ 载体口径：27 件作品住在 21 个载体里。**流水线按内容去重，一个载体只落一条来源**，
> 故下面用 `src-*` 指载体、作品名另标。作品级清单见 `_works.tsv`。

## Scope and assigned sources

train split，全部 P1 载体：

| src | 载体 | 承载的作品 |
|---|---|---|
| `src-60512437ee3e` | Verh. Brünn Bd.3–4 扫描 | **Versuche über Pflanzen-Hybriden (1866)** ＋ 1864／1865 两份气象观测 |
| `src-96f8ba377c2d` | Bd.1–2 | 1863 Bemerkungen ＋ 1863 年度气象观测 |
| `src-4e17c6c489a5` | Bd.5–6 | 1866 年度气象观测 |
| `src-42f3e6c57f7a` | Bd.7–8 | **Hieracium-Bastarde (1870)** ＋ 1869 年度气象观测 |
| `src-133987795400` | Bd.9 | **Die Windhose vom 13. October 1870** |
| `src-f57ca7a9aa53` | Brünner Zeitung 1857-08-18 | Ueber das Gewitter in Brünn am 7. August |

## Source-linked observations

### 一、他一生发表 14 件，其中 **9 件是气象观测**

| 类别 | 件数 |
|---|---:|
| 杂交实验 | **2**（Versuche 1866、Hieracium 1870） |
| 气象 | **9** |
| 昆虫 | 2（1853、1854） |
| 未取到 | 1（*Die Grundlage der Wetterprognosen* 1879，无数字化本） |

**「Mendel 是做豌豆的」这个像略掉了他产出的三分之二。**
`src-133987795400` 是一篇十八页的龙卷风实地分析。

### 二、Versuche 的扉页署名（逐字照录，**含 OCR 讹字，不代改**）

`src-60512437ee3e` 正文自偏移 **872,506** 起：

> `Versuche über Pflanzen-Hybriden. Von Gregor Mendel.`
> `(Vorgelest in den Sitzungen vom 8. Februar und $. März 1865.)`

★ 扫本把 `Vorgelesen` 读成 `Vorgelest`、`8.` 读成 `$.`、`Einleitende` 读成 `Hinleitende`。
**引用时按原样保留并标注**——改了就无从复核是哪一份扫本。

### 三、起因写得很朴素：**是园艺育种，不是理论追问**（@872506）

> `Künstliche Befruchtungen, welche an Zierpflanzen desshalb vorgenommen wurden,`
> `um neue Farben-Varianten zu erzielen, waren die Veranlassung zu den Versuchen,`
> `die her besprochen werden sollen.`

观赏植物为配新花色而做的人工授粉，**是这些实验的起因**。
接着才是：同种间杂交每次重现同样的杂种形态，那种 `auffallende Regelmässigkeit` 促使他继续。

### 四、选材判据**先于**选材（@875012、@876943）

> `Der Werth und die Geltung eines jeden Experimentes wird durch die Tauglichkeit`
> `der dazu benützten Hilfsmittel, sowie durch die zweckmässige Anwendung derselben bedingt.`

选 *Pisum* 的三条理由：

> `Einige ganz selbstständige Formen aus diesem Geschlechte besitzen constante,`
> `leicht und sicher zu unterscheidende Merkmale, und geben bei gegenseitiger Kreuzung`
> `in ihren Hybriden vollkommen fruchtbare Nachkommen. Auch kann eine Störung durch`
> `fremde Pollen nicht leicht eintreten`

**性状恒定且易分辨 ∧ 杂种完全可育 ∧ 不易被外来花粉干扰。**

### 五、术语由他当场定义，且给了命名理由（@888311）

> `jene Merkmale, welche ganz oder fast unverändert in die Hybride-Verbindung übergehen,`
> `somit selbst die Hybriden-Merkmale repräsentiren, als dominirende, und jene,`
> `welche in der Verbindung la_ tent werden, als recessive bezeichnet.`
> `Der Ausdruck „recessiv" wurde desshalb gewählt, weil die damit benannten Merkmale`
> `an den Hybriden zurücktreten oder ganz verschwinden`

### 六、数逐粒数、比值算出来——**报的不是 3:1**（@892398）

> `253 Hybriden wurden im zweiten Versuchsjahre 7324 Samen erhalten. Darunter waren`
> `rund oder rundlich 5474, und kantig runzlig 1850 Samen. Daraus ergibt sich das`
> `Verhältniss 2,96 :1.`
> `2. Versuch. Färbung des Albumens. 258 Pflanzen gaben 8023 Samen, 6022 gelbe und`
> `2001 grüne; daher stehen jene zu diesen im Verhältnisse 3,01:1.`

**5474 + 1850 = 7324 ✓　6022 + 2001 = 8023 ✓　两组各自加得平。**
他给的是 **2,96:1** 与 **3,01:1** 的实测商，**「3:1」是后面归纳的**。

★ 德式小数逗号（`2,96`）**照录时不要改成小数点**——见 [[verbatim-is-not-understood]]，
那次正是把 `,3` 读成 `0.3` 导致三项加不平。

## Candidate Claims

| # | 断言 | 证据（载体 + 偏移） |
|---|---|---|
| W-1 | 他把实验起因写成**园艺育种**，不是理论追问 | `src-60512437ee3e` @872506 |
| W-2 | **选材判据先于选材**：恒定性状 ∧ 可育杂种 ∧ 抗外源花粉 | 同上 @876943 |
| W-3 | `dominirend`／`recessiv` 由他定义，**并写出命名理由** | 同上 @888311 |
| W-4 | 报的是 **2,96:1／3,01:1 的实测商**，不是 3:1；且计数自洽 | 同上 @892398 |
| W-5 | 一生 14 件发表里 **9 件是气象**，杂交只有 2 件 | 原刊目次 ＋ Bd.10 Generalregister |

## Contradictions and alternative explanations

- **Hieracium（1870，`src-42f3e6c57f7a`）没有重复出豌豆的结果。**
  本道不回避它，但**本轮只核了署名与页码，正文尚未细读**——
  「他自己怎么解释这个反例」是本人物最值钱的一处，**下一轮必须读**。
- 1854 年那篇（`src-6131fc708412`）**目次署 `V. Kollar`**，只有内嵌那封信是他的，
  **不能整卷当他的著作引**。

## Unknowns and source gaps

- **Nägeli 通信 10 封（1866–1873）本轮未取到**（SLUB／DDB 在 Anubis PoW 之后，**未绕过**）。
  那是他**自己解释实验并回应质疑**的唯一连续文本——**本道最大的缺口**。
- *Die Grundlage der Wetterprognosen*（1879）无数字化本。
- 修道院院长任内文书在 Brno 州档案馆（MZA fond E6，约 700 件），**无公开数字化件**。

## Proposed Holdout cases

IDs only; research Agents must not inspect Holdout bodies.
★ **本道未取用任何非训练材料。** （★ 2026-08-10 改：此处原先写出了被隔离材料的**作者与书名**。研究道是建模者读得到的，写出书名等于告诉他被隔离的是什么。**件数与书名一并去掉，只留「本道未取用」这一个事实**。）
**本道只取用了训练侧材料**——已实测：非训练侧的 id 在全部研究文档与断言里各 0 处。
（★ 此处的一句统计原先与台账不符，2026-08-05 已更正；**行为无误，是本文写错**。★★ 2026-08-10 再改一次：**原文把件数写了出来**，而研究道是建模者读得到的，件数本身就是信息——**具体数字一律回台账查，不写在这里**。）**quick 档不强制隔离样本**，
但这意味着**本人物没有留出独立复核集**，须在处置记录里写明。

## Handoff to adjudication

W-1…W-5 五条，**每条都指得到载体与偏移**，且 W-4 的三个数互相可验。
未决：Hieracium 那个反例的解释（待下一轮读正文）。
