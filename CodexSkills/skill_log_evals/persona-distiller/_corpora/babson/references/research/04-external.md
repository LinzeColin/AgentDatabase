# External views, criticism, and counterexamples

## Scope and assigned sources

Pending. Use train-split source IDs only.

## Source-linked observations

**本道无 train 源——语料库没有任何独立的外部视角/批评/反例文献。** 14 份 train 源全部是 Babson 本人署名的一手著作与期刊文章（writings 9 / expression 2 / decisions 3，见各道 Scope 表）；没有第三方传记、同代人评述、学术批评、访谈或反驳文章。要核"别人怎么看 Babson"，本库语料给不出独立材料。

语料内能找到的"外部声音"只有三类，且全部**嵌在 Babson 自己的书里**、由他主动引用：

### ① 出版方/编者执笔的卷首文字（Babson 书内的他人声口）
- 《Cox--the man》卷首 Introduction 由"The Publishers"执笔，称 Babson 为 the noted statistician、说明此书缘起（1920 大选中摇摆的共和党选民需要一份 Cox 研究）——这是**出版社的定位，不是 Babson 自评**：
  - 引文见 `src-fce5969229e3` 卷首（The Publishers 段），本道只改述、不逐字引（声口归属问题在 01-writings Contradictions 节已记）。
- 《W. B. Wilson and the Department of Labor》卷首 Foreword 由 John Hays Hammond 执笔，从"促成劳工部设立者"的立场称颂首任部长 Wilson——同样是他人文字（`src-49721f117be5` 卷首，改述）。
- 《Business Barometers》引 Senator Theodore E. Burton 1902 年关于统计缺陷的公开语作卷首引言，并把 Burton 的财富定义搬进正文第二章——**Babson 借权威立论**（`src-5d5edcec3c26` 卷首与正文，改述）。

### ② Babson 转述的第三方例证（引用来佐证、非批评）
他在论证中反复引用"某船长/银行家/编辑对他说的话"当作事实例证（船长无线电报类比、报社编辑"软处理战争新闻"、纽约保守银行家的战后判断）——这些是**被引用的外部经验**，不是外部对本人的评价（分散于 `src-e8a7e154615a`、`src-7f7930c5bcaa`、`src-55080b01fc0a`，改述）。

### ③ 他对对手的回应里透露的"外部立场"
- 在《Ascertaining and Forecasting Business Conditions》里他反驳"本地商人用不上统计"的两类常见异议（本地生意只看本地、本行业只看本行）——**他自己树靶子再拆**（`src-e8a7e154615a` 开头，改述）。
- 在《Religion and Business》里他回应"商人只在口头上信教/教会与商业互相看不上"的流行批评（`src-8d6c1ba9f9d2`，改述）。

⇒ 结论：本道如实记"无 train 源"——外部视角缺失是语料的结构性事实（全为本人一手），不是遗漏。凡"别人如何评价 Babson"类问题，模型没有语料证据，只能给出"语料内无此信息"的边界回答。

## Candidate Claims

- C-X1（lineage 元断言）：本库 14 份 train 源全部为 Babson 本人一手，**无独立外部/批评/反例文献**；语料内唯一的外部声口是嵌在他书里的出版社/编者卷首文字（src-fce5969229e3、src-49721f117be5、src-5d5edcec3c26）与转述例证（src-e8a7e154615a、src-7f7930c5bcaa、src-55080b01fc0a）——均须按声口折减，不得当 Babson 观点。
- C-X2（boundary）：外部评价类问题（"当时人怎么看他/学界怎么批评他"）在语料内无证据，模型应明确拒绝推断。

## Contradictions and alternative explanations

- "书里没有外部批评"不等于"外界没有批评过他"——Babson 1920s 后名声很大、争议很多（1929 看跌警告、政府干预主张等），但那些批评不在本库；**本道只能证"语料无"，不能证"历史无"**。
- 出版社 Introduction 与 Hammond Foreword 虽在 Babson 的书里，但表述的是第三方立场（出版社的销售定位、Hammond 的政治立场）；引用时若当 Babson 自评，即属声口污染。

## Unknowns and source gaps

- 无任何第三方传记/批评/学术回应/报刊评论 train 源；无 Babson 与同行的书信往来。
- 无法核验 Babson 转述的第三方例证（Cunard 船长、银行家等）的真实性——语料未给出处。
- "1929 年看跌警告"的当时反响（媒体如何报道、学界如何评价）不在语料内，属外部史实、无引文可依。

## Proposed Holdout cases

IDs only; research Agents must not inspect Holdout bodies.

## Handoff to adjudication

- C-X1 作为 lineage 元断言，与 facts.md 的"语料覆盖"说明合流：模型文档须写明"无外部/反方语料"这一结构事实，防止下游把 Babson 书内的第三方声口当 Babson 观点。
- C-X2 供边界文档用："外部评价"类问题一律让渡或拒绝。
- 若后续补源（如同时代报刊对 Babson 的报道），本道再行填充；当前如实记"无 train 源"。

## 未做完 / 未核

- 未系统翻检全部 14 份正文里是否还有未提取的第三方转述/引文（只核了三类各一例）；Babson 引用他人（Burton、耶稣、牛顿、Hill 等）的完整清单未枚举。
- 卷首"出版社 Introduction/Hammond Foreword"仅确认为他人执笔，未逐段核对两篇文字中是否有 Babson 参与署名的段落（Cox 卷首 Introduction 未署名作者，Hammond Foreword 明确署名 Hammond）。
