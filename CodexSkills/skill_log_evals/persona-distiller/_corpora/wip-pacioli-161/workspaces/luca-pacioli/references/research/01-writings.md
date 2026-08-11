# Writings

## Scope and assigned sources

**本道分到 7 份（train split）**：

| source_id | 出版年 | tier | 题名 |
|---|---|---|---|
| `src-a065a9dd18dc` | 1494 | P1 | summa-arithmetica-1494-venice-djvu.txt |
| `src-0ab42213e81b` | 1500 | P1 | de-viribus-quantitatis-1496-bologna-ms250.txt |
| `src-9090173c710f` | 1509 | P1 | de-divina-proportione-1509-venice-getty.txt |
| `src-671c6f35b828` | 1889 | P2 | winterberg-1889-german-translation-divina-proportione.txt |
| `src-cf1287bdb650` | 1896 | P2 | pacioli-1896-dutch-translation-koopmansboekhouding.txt |
| `src-bcece04a709a` | 1914 | P2 | geijsbeek-1914-ancient-double-entry-bookkeeping.txt |
| `src-17ba7903aac0` | 1924 | P2 | crivelli-1924-original-translation-double-entry.txt |

★ 本节由台账机械导出（`emit_lane_scope.py`），**不含任何阅读判断**；只投影 `split == train` 的行。

## ★★★★ 本道的第一条结论：**一手在库、是公有领域、也读得到，而它的 OCR 撑不起逐字引用**

来源：src-a065a9dd18dc src-9090173c710f src-0ab42213e81b

**实测（同一把尺子量全部 10 份：空白切 token，数其中纯字母且长度 ≥2 的占比）**：

| 份 | 档 | token 数 | 干净词占比 |
|---|---|---:|---:|
| `vasari-1568`（1912 英译） | S2 | 2,787 | **95.6%** |
| `catholic-encyclopedia-1911` | S2 | 284 | 93.3% |
| `rouseball-1908` | S2 | 1,504 | 91.2% |
| `pacioli-1896-dutch` | P2 | 36,658 | 90.5% |
| `crivelli-1924` | P2 | 34,315 | 90.2% |
| `winterberg-1889` | P2 | 121,233 | 90.1% |
| `geijsbeek-1914` | P2 | 116,436 | 81.6% |
| **`de-viribus-quantitatis-1496`** | **P1** | 98,962 | **80.8%** |
| **`de-divina-proportione-1509`** | **P1** | 67,683 | **75.6%** |
| **`summa-arithmetica-1494`** | **P1** | 452,006 | **62.0%** |

★★★ **三份一手正好是最差的三份**，而其中最重要的那一份（1494 Summa，复式记账论述所在）
**约 38% 的 token 是 OCR 噪声**。随机抽三段的样子：

‹e vnita dx fonno ì li nucri qdrati oe li nueri cb 02 dinataméte afeedano p ternario›

★★★★ **更硬的一条实测**：在那 2,945,546 字符里，
`computis` **0 次**、`scripturis` **0 次**、`Particularis` **0 次**——
**连那一节的标题本身都恢复不出来。**
而记账词汇是在的：`quaderno` 59、`giornale` 47、`memoriale` 11、
`debitore` 15、`creditore` 17、`mercante` 20——**内容在，字不在。**

### 这一条对下游意味着什么（**必须写进产物**）

1. **凡「他的原话」，在本产物里都只能是译文**，且必须标明是哪一位译者哪一年的译文。
   **1494 原刊无法提供任何一句可逐字回查的话。**
2. **`persona.md` 的语气不能建在一手语言上。** 与 Gantt #156 的 `expression` 道为 0 不同——
   那是**载体不存在**；这里是**载体在、可取、公有领域，而字读不出来**。
3. ★ 这不是「取不到」，也不是「不是他写的」。**是第四种**：**一手不可引用。**

## Source-linked observations

★ 2026-08-12：下面几行原在本文件开头那个 Scope 节里。
  那一节由 emit_lane_scope.py 从台账**机械重出、不含阅读判断**，
  手写内容重出时会被静默抹掉——判断性的话搬到这里才留得住。
  ★★ 本条注释**刻意不用反引号**：反引号里的英文会被
     check_lane_quotes_verbatim 当成一条待核引文，而它当然核不到
     （第一版就是这么把三个工作区改红的）。

**7 份**：3 份一手原刊（P1）＋ 4 份 1931 年前的译本（P2）。
- P1：`summa-arithmetica-1494`（威尼斯原刊）、`de-divina-proportione-1509`（Getty 藏本）、
`de-viribus-quantitatis-1496`（博洛尼亚 MS 250 手稿）
- P2：`geijsbeek-1914`（英译）、`crivelli-1924`（英译）、`pacioli-1896-dutch`（荷译）、
`winterberg-1889`（德译）


### ★★★ W1：他自己那句解二次方程的口诀——**经二手转述才读得到**

来源：src-0af54aee74c3 src-a065a9dd18dc

Rouse Ball 1908 直接引了 1494 年版第 145 页的原文（拉丁文，rhetorical 而非 syncopated）：

> Si res et census numero coaequantur, a rebus dimidio sumpto censum producere debes,
> addereque numero, cujus a radice totiens tolle semis rerum, census latusque redibit.

★★ **这是本库里唯一一句能读到的、他自己的拉丁原文**——
**而它是从一份 1908 年的二手书里读到的，不是从 1494 原刊里读到的**（原刊那一页的 OCR 不可读）。
★ 分档要写清：**句子是他的，见证是二手的。**

### ★★★ W2：他自己说三次方程解不出来——**而这句话四十年后就被推翻了**

来源：src-0af54aee74c3

> He mentions the Arabic classification of cubic equations, but adds that their solution
> appears to be as impossible as the quadrature of the circle.

★★★★ **这是本库里关于他认识论的最硬一条**：他把「解三次方程」与「化圆为方」并列，
**判成同一档的不可能**。而 Cardano/Tartaglia 在 1530–40 年代就解出了三次方程。
★ **产物里不许把这一条写成「他错了」就完事**——要写的是**他当时凭什么这么判**，
以及**本库没有材料能回答这个「凭什么」**（一手不可引用，转述里也没有他的理由）。

### ★★ W3：这本书的分量在「印了、传开了」，不在「新」

来源：src-0af54aee74c3

> This was the earliest printed book on arithmetic and algebra

> It is mainly based on the writings of Leonardo of Pisa, and its importance in the history of
> mathematics is largely due to its wide circulation

★★ 两句要一起读：**「最早印出来的」与「主要建立在 Leonardo of Pisa 之上」同时成立。**
Catholic Encyclopedia 1911 说得更直白：`he drew freely upon the writings of Leonardo da Pisa`。
★ **产物里不许把他写成复式记账的发明人**——本库的两份二手源都说他是**整理与传播者**。

### ★★ W4：会计那一节在书里的位置

来源：src-0af54aee74c3 src-bcece04a709a

> bills of exchange and the theory of book-keeping by double entry

★ Rouse Ball 把它放在「商用算术」那一大段里顺带提到——
**在 1908 年的数学史视角下，它只是全书的一小部分**。
★★ 而 Geijsbeek 1914 整本书就是围绕它做的。**同一节文本，两种取景。**

### ★ W5：1509 那一册的作者归属，本库只有二手支撑

来源：src-671c6f35b828 src-9090173c710f

Winterberg 1889 德译本导言：

> seine Autorschaft nicht von Pacioli, sondern von Piero della Francesca, also einem wirklichen
> Künstler, ableitet

★★★★ **而 1509 Getty 扫本里我核不到这一点**：`Francesca` 0 次、`Borgo` 0 次、
`quinque corporibus` 0 次（仅有的两处 `Piero` 是题献名单里不相干的人名）。
**页面上的署名证据本库拿不到。** 见 `04-external.md` 的瓦萨里那一节。

## Candidate Claims

**P1（fact，可成条）**：**1494 年《Summa》是最早印行的算术与代数书，
而它主要建立在 Leonardo of Pisa 的著作之上；它的分量在流传，不在原创。**
- 证据 A：Rouse Ball 1908 两句（S2）
- 证据 B：Catholic Encyclopedia 1911 `he drew freely upon the writings of Leonardo da Pisa`（S2）
- ★ **两处都是二手**；本库无法从一手侧核这一条。

**P2（epistemic，可成条）**：**他把三次方程的求解与化圆为方并列，判成同一档的不可能。**
- 证据 A：Rouse Ball 1908（S2，转述）
- ★★ **只有一处，且是转述**。**不许写成他的原话。**
- ★ 用处在于产物的射程：**问他「这道题能不能解」，他会给出一个当时看合理、后来被推翻的判断。**

**P3（boundary，可成条）**：**本产物里凡「他的原话」都只能是译文——1494 原刊的 OCR 不可逐字引用。**
- 证据 A：干净词占比 62.0%（一手最差的一份）
- 证据 B：`computis`／`scripturis`／`Particularis` 在 294 万字符里 **0 命中**
- ★★ 这是一条**关于本库的事实**，不是关于他的事实。

## Contradictions and alternative explanations

- **「最早印行」与「主要基于别人」并存**，两者都出自同一位作者（Rouse Ball）同一段。
  **产物里不许只取前半句。**
- **干净词占比这把尺子很粗**：它只数「像不像词」，不判语义，
  且对 15 世纪意大利语的缩写体系不公平（`p̄`、`cb̄` 这类合法缩写会被判成脏）。
  ★ **所以它只能用来做相对比较**（一手 62% vs 译本 90%），**不能当绝对判据**。

## Unknowns and source gaps

- **复式记账那一节（Distinctio IX, Tractatus XI）在一手侧定位不到**：标题词 0 命中。
  下一轮若要在一手侧定位，只能靠 `quaderno`／`giornale`／`debitore` 这些词去圈范围。
- **三份一手全都没有逐段读过**——OCR 质量决定了逐段读的收益很低。
- **1508 年 8 月 11 日威尼斯 San Bartolomeo 的公开演讲**（约 500 人）序言印在 1509 版欧几里得里，
  ★ **那是目前唯一有希望坐实 `conversations` 道的线索**，但那一册已判「不入库」
  （正文实质是欧几里得的），**要单独把序言切出来核**，本轮未做。

## Proposed evaluation-set candidates

（本轮未提名。提名须在隔离样本划定之后、且不打开正文。）

## Handoff to adjudication

- Validate origin independence and evaluation-set separation before promotion.
- ★★★★ **本道给下游的第一条**：**一手在库、是公有领域、读得到，而它的 OCR 撑不起逐字引用。**
  **凡「他的原话」都必须标明是哪一位译者哪一年的译文。**
- ★★ **不许把他写成复式记账的发明人**——本库两份二手源都说他是整理与传播者。
- ★ 三次方程那一条**只有一处二手转述**，**不许当他的原话引**。
