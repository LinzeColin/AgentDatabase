# Conversations and interviews

## Scope and assigned sources

**本道分到 3 份（train split）**：

| source_id | 出版年 | tier | 题名 |
|---|---|---|---|
| `src-1be9153766c6` | 1687 | P1 | Epistolae quotquot reperiri potuerunt（书信集，现存最大的一部） |
| `src-1a398fec8248` | 1806 | P1 | Hugonis Grotii Epistolae Ineditae（致 Oxenstierna 父子及瑞典参议，自法国寄出） |
| `src-b7384d9e7530` | 1829 | P1 | Hugonis Grotii ad Ioh. Oxenstiernam et Ioh. Adl. Salvium … Epistolae Ineditae |

★ 本节由台账机械导出（`emit_lane_scope.py`），**不含任何阅读判断**；只投影 `split == train` 的行。

## Source-linked observations

### 一、★★★ 这一道占语料的 28%，而它**一句逐字引文都提供不了**

train 侧各道体量（`corpus_body()` 现算，字符数）：

| 道 | 字符 | 占比 | 份数 |
|---|---:|---:|---:|
| writings | 17,400,524 | 61.6% | 12 |
| **conversations** | **7,911,102** | **28.0%** | **3** |
| external | 2,030,457 | 7.2% | 4 |
| expression | 898,878 | 3.2% | 2 |
| 合计 | 28,240,961 | | 21 |

而本道三份的长 s 讹字率是 **0.9544 / 0.9777 / 0.9775**
（`check_longs_corruption` 实测，逐份见工作区根目录 `00-密封改判.md` 文末）。

**后果要说清楚**：本项目**拿不到「他在信里怎么说话」的任何逐字证据**。
不是「没找到」，是**语料在字形上已经不支持逐字引用**——
三份里每 100 个含长 s 的词有 95–98 个是讹形。

★ 这不等于本道无用：**信件的存在、数量、纪年、收发对象仍然可用**，
只是**任何以「他写道：…」形式出现的句子都不能从本道取**。

### 二、★★ 卷首有一份**结构化的信件目录**——编号、收信人、地点、日期齐全

`src-1a398fec8248`（1806 卷）里 `16xx` 形式的纪年命中 70 处，
**其中 69 处挤在文件的前 2.9%**（@6621–@12986）——那不是正文，是**卷首目录**。
逐行形如：

> `XVL Axelio Oxenftierna , Lutet. xi Aug. 1635,`
> `XI. Schmalchio, Lutet. 5 Martii 1635.`
> `III. N. N. (Joanni Oxenfliernse) Francof. ~ Aug. 1634.`

（`Oxenftierna`＝`Oxenstierna`、`Oxenfliernse`＝`Oxenstiernae`、
`Scbmalchio`＝`Schmalchio`、`Lutet.`＝`Lutetiae`（巴黎）、`Francof.`＝`Francofurti`。）

从目录可机械读出（年份前 95 字符窗口内计数）：

| 维度 | 实测 |
|---|---|
| 年份跨度 | **1633 – 1645** |
| 地点 | `Lutet` **62**、`Hamburg` 3、`Francof` 2、`Dionys`（Saint-Denis）2、`Paris` 2 |
| 收信人 | `Oxenftiern*` **15**、`Eidem`（致同一人，续前）**29**、`Schmalchio` 7、`Salvio` 1、`Ignoto` 1 |

**目录本身给出了一条可核的行程线**：1633 Hamburgi → 1634 Aug. Francofurti →
1635 Febr. 起 ad Aedem Dionysii／Lutetiae，此后压倒性地在 Lutetiae，直到 1645。

★★ **这一条推翻了我半小时前写在本节的说法。** 我先用 `EPIST[OLA]` 后接罗马数字
去数编号，得到 101 个而前八个是 `L, I, L, L, XL, L, L, L`，
据此写下「编号不可用，是 OCR 把 `I.` 读成 `L`」。
**那个结论是错的**——编号是真的，只是我的正则取错了地方（`EPIST` 那串命中的
不是目录行）。去把年份的上下文逐处读出来，目录才露出来。
→ [[read-the-hits-before-reporting-the-rate]]：**报率之前先看命中**；
   这次我不但报了率，还据它下了「不可用」的判决。

### 三、★★ 另两份**各是另一种形态**，1806 那套读法一份都套不上

| 份 | 字符 | 纪年数 | 落在前 10% | 形态 | 跨度 |
|---|---:|---:|---:|---|---|
| `src-1a398fec8248` 1806 | 452,317 | 70 | **99%** | **卷首信件目录** | 1633–1645 |
| `src-1be9153766c6` 1687 | 7,267,511 | 356 | 7% | **无卷首目录**，纪年散在正文（信末落款） | 1515–1691 |
| `src-b7384d9e7530` 1829 | 191,274 | 43 | 95% | 前部是**编者序**，不是目录 | 1544–1687 |

- **1687 卷**样例：`Idib. Aprilibus 1608`（= Idibus Aprilibus，四月望日）——
  确是落款形态，但**分布在全文**，要逐封抽出来才有年表。
- **1829 卷**样例（@6550，照录）：`incipit. a menfe Maioanni 1643`
  （`menfe`＝`mense`、`Maioanni`＝`Maio anni`，中间那个句点也是原样）——
  这是**编者在序里陈述这批信的起点**，不是某封信的日期。

> ★★★ **同一个错，本节又犯了两次**：上面两条引文我第一次都是「顺手改对」了才写下的
> ——把 `XVL` 写成 `XVI.`、句末逗号写成句号；把 `Maioanni` 拆成 `Maio anni`、
> 删掉 `incipit` 后的句点。**加上 01-writings 那次，今天共四次。**
> 每一次都是 `check_lane_quotes_verbatim` 抓出来的，**没有一次是我自己发现的**。
> 形态很稳定：**读原文时脑子已经把讹字补正了，写下来的是补正后的版本。**
> → 对策不是「更小心」，是**从语料里复制，不要从理解里默写**。

★★ **两份的年份跨度都越过了他的生卒（1583–1645）**：1687 卷到 1691、1829 卷到 1687。
所以**这两份的纪年集合里混着引证年份与编者纪年**，
**不能拿它当「他的信写于哪些年」**——1806 卷可以，因为那 70 处全在目录行里。

### ★ 本节没做什么

- 三份**都没有通读**。上面三条一条是全量字符统计、两条是位置分布与正则计数，
  **都不需要读懂内容**，也**都不构成对他主张的任何判断**。
- 1806 目录里的收信人／地点**没有逐行核对到正文**——只核到「目录行长这样」。
- 1687 卷的 356 处落款**没有逐处分拣**（哪些是信末日期、哪些是正文引证）。

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
