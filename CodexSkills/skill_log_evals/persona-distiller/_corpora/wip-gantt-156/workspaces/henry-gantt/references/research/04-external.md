# External accounts

## Scope and assigned sources

**3 份**，一份 P2、两份 S2。**本道不产出任何关于他思考方式的断言。**

- `asme-v40-1918-secretary-third-person-paraphrase-NOT-verbatim`（**P2 / third-person**，2,243 字节）
- `asme-v41-1919-necrology-henry-laurence-gantt`（S2，5,278 字节）——事实部分见 `06-timeline.md`
- `clark-1922-the-gantt-chart`（S2，204,407 字节）

## ★★★★ E1（P2）：**读起来完全像他，一个字都不是他的**——这份是陷阱的实物

`asme-v40-1918-…-NOT-verbatim` 全篇是**学会秘书的第三人称转述**：

> In presenting his paper the author pointed out that on the battle front war was competition
> in destruction, while behind the lines it was competition in production. He quoted Prof. C.
> R. Mann as saying that war was eight-tenths engineering, and that the engineer was the great
> production factor in the commonwealth.

> He then led up to the point where he hoped the engineer would be a more influential factor in
> the conduct of national affairs than heretofore, because he had demonstrated that he knows
> what to do a

★ **三层嵌套，一层比一层远**：
1. 秘书在转述（`the author pointed out that…`）；
2. 秘书转述的是**他在引用别人**（`He quoted Prof. C. R. Mann as saying…`）；
3. 而秘书还在替他描述心理状态（`he hoped…`）。

★★ **这一份存在的意义就是当反例。** 抓源方特意把它单独存成一份、文件名里写死
`NOT-verbatim`、分档标 `P2 / third-person`——**不是为了用它，是为了让这条界线可查。**

★★★ 同族的两处，**已写进 `meta.json` 与 `02-conversations`**：
- ASME 讨论排版 v32/v38/v40 是 `H. L. Gantt said that…`（秘书转述），
  而 v16–v25/v30 是 `Mr. Gantt.— <原话>`（逐字）；
- **v38 里紧挨 No.1578 之前那句 ‹THE AUTHOR. In closing the discussion…› 是 Polakov 不是 Gantt。**
  （★ 这一句有意用 `‹›` 不用反引号：**它是反面例子**，而两件引文判据都把反引号内的长英文串当成「声称逐字」去核。
  **今天我在这同一句上犯了三次**——第三次才把它写进正文当提醒。）

## ★★★ E2（S2）：Clark 1922 —— **书名带他的姓，而全书零处他的署名文字**

丛书广告页逐字：

> THE GANTT CHART. By WALLACE CLARK. Illustrates applications in management. 1922. 157 pages.

★ **作者是 Wallace Clark**，抓源方逐处核过：**全书没有一处 Gantt 的署名文字**。
★★ **而 archive.org 的 `creator` 字段把 Gantt 列为共同作者**——**元数据陷阱**。
同族的另一处：William Kent《Investigating an Industry》(1914) 的 `creator` 也列了 Gantt，
**实际只有 998–1000 词的导言是他的**（那一节已单独入库，整本未入库）。

★★★ **本道给下游最实用的一条**：
**「书名里有他的名字」「元数据把他列为作者」都不是署名证据。**
署名证据只有一种：**页面上印着的署名行**。

## E3（S2）：讣告

事实部分全部写在 `06-timeline.md`（T2–T9），**此处不重复**。
本道只留一条口径：**讣告是学会写的褒扬体裁**，
且在可核的篇名上已经出了两处不精确（`Training **of** Workmen`、`Coéperation`）——
**同一份文件在可核的地方就已经不精确。**

## Candidate Claims

★ **本道不产出 mental-model／heuristic／value 类断言。**
P2 与 S2 都是别人对他的记述或转述，**不能用来推他的思考方式**。

**E-A（fact，可成条）**：**《The Gantt Chart》(1922) 的作者是 Wallace Clark，不是 Gantt。**
- 证据 A：该书丛书广告页逐字 `THE GANTT CHART. By WALLACE CLARK.`（S2）
- 证据 B：抓源方逐处核过全书零处 Gantt 署名文字（**过程证据，非文本证据**）
- ★ 这一条的用处是**防误**：产物里绝不许把这本书当成他的作品。

## Contradictions and alternative explanations

- **E1 的内容与他自己写的东西高度一致**（工程师应在国政中更有分量、
  生意人的做法产不出船与炮弹）——**这正是它危险的地方**：
  **一致不等于是他说的。** 判断依据只能是**排版体例**，不能是**读起来像不像**。
- **E2 的「零处署名文字」是抓源方的过程结论**，我本轮**没有独立复核**。
  ★ 但书名页那一行是可核的，**且它已经足够支持 E-A**。

## Unknowns and source gaps

- **同代人的独立评述本轮一份也没有**：没有同行的回忆录、没有 Taylor Society 的悼念文集
  （抓源方提到 ASME 1920 年有一本 *The Life and Work of Henry L. Gantt*、
  Fred J. Miller 1930 年在 *The Management Review* 有一篇 —— **两件都没找到电子全文**）。
- ★ 本道现在**全部建在 ASME 自己的出版物上**（讣告、会刊转述）＋ 一本以他命名而非他写的书。
  **「学会之外的人怎么看他」这一层完全缺席**，这一条要写进 `divergence-map`。
- L. P. Alford《Henry Laurence Gantt: Leader in Industry》(1934) 是标准传记，
  **超 1931 分界，不合规，未抓也不许抓**。

## Proposed evaluation-set candidates

（本轮未提名。提名须在隔离样本划定之后、且不打开正文。）

## Handoff to adjudication

- Validate origin independence and evaluation-set separation before promotion.
- ★★★★ **本道给下游的第一条是防误清单，不是断言**：
  1. `asme-v40-1918-…-NOT-verbatim` **一个字都不是他的**，尽管读起来完全像；
  2. 《The Gantt Chart》(1922) **是 Wallace Clark 写的**；
  3. archive.org 的 `creator` 字段把 Gantt 列进了 Clark 与 Kent 两本书——**元数据不是署名**。
- ★★ **「学会之外的人怎么看他」本轮零材料**——产物里不许出现这一层的任何概括。
