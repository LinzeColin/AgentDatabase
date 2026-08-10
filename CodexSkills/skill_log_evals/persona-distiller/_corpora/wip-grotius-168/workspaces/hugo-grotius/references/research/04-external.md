# External views, criticism, and counterexamples

## Scope and assigned sources

**本道分到 4 份（train split）**：

| source_id | 出版年 | tier | 题名 |
|---|---|---|---|
| `src-2e9cff2611dd` | 1643 | S1 | Ioannis de Laet Antwerpiani Notae ad Dissertationem Hugoni… Origine Gentium Americanarum |
| `src-b0e9a4b92aa5` | 1644 | S1 | Ioannis de Laet Antwerpiani Responsio ad Dissertationem Se… Origine Gentium Americanarum |
| `src-52882c964c73` | 1652 | S1 | Of the Dominion, or, Ownership of the Sea, Two Books（= Mare Clausum，1635 拉丁本的英译） |
| `src-2c8d5663651f` | 1826 | S1 | The Life of Hugo Grotius, with Brief Minutes of the Civil,…ry History of the Netherlands |

★ 本节由台账机械导出（`emit_lane_scope.py`），**不含任何阅读判断**；只投影 `split == train` 的行。

## Source-linked observations

### 一、★★ 三份论敌之作**姓名命中低得可疑**——查下来是 OCR 与行文习惯，不是源不对

先给可疑的数（`Grot*` 逐份命中）：

| 源 | 字符 | `Grot*` |
|---|---:|---:|
| `src-2c8d5663651f` Butler 传 1826 英 | 418,944 | 348 |
| `src-2e9cff2611dd` De Laet *Notae* 1643 拉 | 299,815 | 24 |
| `src-b0e9a4b92aa5` De Laet *Responsio* 1644 拉 | 166,907 | **2** |
| `src-52882c964c73` Selden *Mare Clausum* 1652 英 | 1,144,791 | **8** |

Selden 那本是针对《海洋自由论》的著名反驳，114 万字符只提 8 次，
De Laet 的 *Responsio* 16.7 万字符只提 2 次——**看起来像是抓错了源。**
去读命中，两条都不是：

> `ani Responsio disserta tio nem secundam Hvgonis G R O T I I ) D E Origine Gentium Americanarum^.`

（`src-b0e9a4b92aa5` @160，题名页：**整本书就是驳他那篇论美洲民族起源的第二篇论文**。）

> `raveram Clariffmum Vi¬ rum Hugonem Grotium mihi gratias fuijfe acturum , quod modejie illum monuiffcm`

（同上 @455，致读者序；`Clariffmum`＝`Clarissimum`、`fuijfe`＝`fuisse`、
`modejie`＝`modeste`、`monuiffcm`＝`monuissem`。
意为「我本以为这位卓越人物会谢我，因为我温和地提醒了他」——**论战的口吻**。）

> `Sea ; ejpeciaUy of Fer- nandus Vafquius, and Hugo Grotius. Chap. XXVI. HAving thus refuted, or upon`

（`src-52882c964c73` @425346，章题；`ejpeciaUy`＝`especially`、`Vafquius`＝`Vasquius`。）

> `ee com to the other, to wit, Hugo Grotius , a man of great learning, and ex. traordinarie knowledg in`

（同上 @431175。）

**真因两条**：①正文里他被称 `Clarissimum Virum` / `illum` / `the other`，姓名少；
②OCR 把姓名读坏（见下条）。**不是源不对。**

### 二、★★★ `Grotius` 在 17 世纪印本里是 `Grotivs`——**按现代拼写检索会系统性漏掉**

外部道四份的姓名形态合计（前 12 种）：

| 形态 | 次数 | | 形态 | 次数 |
|---|---:|---|---|---:|
| `Grotius` | 249 | | `Grot` | 6 |
| `GROTIUS.` | 44 | | `Grotivs.` | 5 |
| `GROTIUS` | 30 | | `GROT` | 5 |
| `Grotius.` | 18 | | `Grotivs` | 4 |
| `Grotii` | 8 | | `Grotim` | 3 |
| | | | `Grottus` / `GROTII` / `Grotiu^` | 1 / 2 / 1 |

现代拼写那 341 次**几乎全在 1826 那本传记里**。在 17 世纪那三份里：

> `m. elu&andum. Sed videamus porro ClarilLvirl fententiam. H. Grotivs. EGo 3 ut dicam qu<e mihi maxime fi probanh primum`

（`src-2e9cff2611dd` @14697；`Grotivs` 是 `Grotius`——**早期印本 u 印作 v**，
`ClarilLvirl`＝`Clarissimi viri`、`fententiam`＝`sententiam`。
这里 `H. Grotivs.` 是**引他发言的标记**，后面 `EGo` 起是他的话。）

**实测漏检率**：在 De Laet *Notae* 1643 里按字面 `Grotius` 检索只找到 **2 / 24 = 8.3%**；
`Grotivs`+`Grotivs.` 就有 9 次（37.5%），另有 `Grot` 6 次。

★ 这与 [[regex-must-clear-the-corpus-language]] 同型但更窄一层：
**正则不但要过语料的语种关，还要过它的正字法关**——
`u/v`、`i/j`、长 s、`us→m` 的讹形都要一起写进去。

### 三、逐字可引性：这一道**唯一干净的是二手传记**

| 源 | 判读 | 讹字率 |
|---|---|---:|
| Butler 传 1826 英（**二手**） | 干净 | 0.0000 |
| De Laet *Notae* 1643 拉 | **不可用** | 0.9022 |
| De Laet *Responsio* 1644 拉 | **不可用** | 0.9708 |
| Selden *Mare Clausum* 1652 英 | **不可用** | 0.9957 |

→ **「他的论敌当时怎么说他」拿不到一句可核的逐字引文**；
能逐字引的只有一位 1826 年的传记作者转述。

### ★ 本节没做什么

- 四份**都没有通读**。三条分别是命中计数、形态频次、判据实测表。
- **没有查 Butler 1826 的转述是否忠于原始文献**——它是二手，本道不判其准确性。
- Selden 与 De Laet 的**论点**一条都没读，只读到「书是针对他的」。

## Candidate Claims

Pending.

## Contradictions and alternative explanations

Pending.

## Unknowns and source gaps

Pending.

## Proposed Holdout cases

IDs only; research Agents must not inspect Holdout bodies.

## Handoff to adjudication

Pending.
