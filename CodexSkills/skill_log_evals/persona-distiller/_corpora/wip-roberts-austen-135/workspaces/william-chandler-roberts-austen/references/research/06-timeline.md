# Timeline and life events

## Scope and assigned sources

**本道分到 1 份（train split）**：

| source_id | 出版年 | tier | 题名 |
|---|---|---|---|
| `src-2b601c0c1e58` | 1914 | P2 | robertsaustenar00smitgoog.txt |

★ 本节由台账机械导出（`emit_lane_scope.py`），**不含任何阅读判断**；只投影 `split == train` 的行。

## Source-linked observations

★ 2026-08-12：下面几行原在本文件开头那个 Scope 节里。
  那一节由 emit_lane_scope.py 从台账**机械重出、不含阅读判断**，
  手写内容重出时会被静默抹掉——判断性的话搬到这里才留得住。
  ★★ 本条注释**刻意不用反引号**：反引号里的英文会被
     check_lane_quotes_verbatim 当成一条待核引文，而它当然核不到
     （第一版就是这么把三个工作区改红的）。

Train-split、`dimensions` 含 `timeline` 的 **1 份**：
★ **本轮仍未通读**，但已按 04-external 得到的四个节点定点开挖，
**挖到了这份材料里的编年表**，下面每一条都是逐字核过的。


### ★★★ ① 这份里有一张**按年排的履历表**

> `events in his career arranged in chronological sequence : —`

已逐字核过的条目（节选）：

> `1865. Completed the course and obtained the Associateship in Metallurgy, and
> shortly afterwards became Private Assistant to Thomas Graham at the Royal Mint`
> `1876. Elected a Fellow of the Royal Society`
> `1880. Succeeded Dr. Percy in the Chair of Metallurgy at the Royal School of Mines`
> `1889. Appointed to the Alloys Research Committee of the Institution of Mechanical Engineers`

### ★★ ② 「Graham 的私人助手」由此**有了第二处出处**

04-external 只有 DNB 1912 一处。**本条是 1914 年这份的独立记载**——
两份都说 1865 年他成为 Graham 在造币厂的私人助手。
**这是本人物第二条跨来源印证的事实**（第一条是「合作者具名」）。

### ★★★ ③ 缺失的那批报告，**日期在这里**

> `Publication of the First Report of the Alloys Research Committee, subsequent
> Reports appearing in 1893, 1895, 1897, and 1899.`

配合 `1889. Appointed to the Alloys Research Committee`——
**合金研究委员会报告共五份：1891、1893、1895、1897、1899。**

★ 这正是抓源员报「Proc. IMechE 1880–1910 在 archive.org 检索 numFound 0（★ 有意不用反引号：**这是抓源记录，不是引文**）」的那批，
也是 01-writings 观察 ① 里他说「标定方法的细节在那份 IMechE 报告里」所指的东西。
**现在缺口有了确切的年份清单，下一轮可以按年去找，而不是按刊名盲搜。**

### ④ 1876 这一年同时发生两件事

`1876. Elected a Fellow of the Royal Society`，
而同年他为 Graham 的文集写了那篇书评（03-expression 观察 ①，`src-4b50569ba761`）。
**当选皇家学会会士与为亡师文集作评是同一年。** 两处出处相互独立。

## Candidate Claims

- **师承是职务性的，且有两处出处**：1865 年起任 Graham 私人助手。依据：观察 ②。
- **合金研究委员会报告为五份，年份确定**：1891/1893/1895/1897/1899。依据：观察 ③。

## Contradictions and alternative explanations

- 本道来源是 **P2**，且是**他主编的丛书卷里的传略**，撰者非他本人。
  编年表的可靠性依赖撰者；**与 DNB 一致的那几条可以互证，其余条目只有这一处。**
- ★ 观察 ④ 的「同一年」是**两份来源各自记的年份对上了**，
  **不是任何一处说「因为当选所以作评」**。**不要读成因果。**

## Unknowns and source gaps

- **1.24M 字符仍未通读**，本轮只做了定点开挖（四个年份 + 编年表 + 报告年份）。
- 编年表之外，这份还列有
  `Official Work and Researches, 1870-1880, 1881-1890, 1891-1902`、
  `References to Memoranda in the Annual Mint Reports, 18701889 and 1890-1902`（★ `18701889` 缺的那个连字符是 OCR 掉的，**我曾把它补上**——补字就是改内容）、
  `Additional Bibliography`——**这三块都没读，是明确的下一轮目标。**

## Proposed Holdout cases

IDs only; research Agents must not inspect Holdout bodies.

（本轮未提名。）

## Handoff to adjudication

**本道从「待开采」变成「已开出两条」**：Graham 助手关系的第二处出处，
以及合金研究委员会五份报告的确切年份。

**但仍不是通读结论**——编年表之外的三大块（官方工作、造币厂年报备忘录索引、补充书目）
一个字没读。下游引用本道时，**只许引上面逐字列出的那几条**。
