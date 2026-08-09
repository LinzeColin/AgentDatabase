# External accounts

## Scope and assigned sources

- `src-940890f8d2dd` — Smithsonian Dibner 藏品里的**讣告与传记剪报**（S2，1890 前后）。
  含一张德文著录卡片与至少一篇爱丁堡报纸的讣告 `THE LATE JAMES NASMYTH.`。
- `src-c6ac9016e131` / `src-bc1b055cc253` — MNRAS 1844／1846，**学会记录员的第三人称摘要**（S1）。
- `src-740e57fe9bac` — 1843 London Journal 转载的蒸汽锤专利节录（S1，第三人称）。

## ★★★★ 先说独立性：**这一道的主源大部分不独立于自传**

讣告自己写着：

> The recollections of Nasmyth’s boyhood, as narrated in his ‘‘ Autobiography,’. are full of
> interest.

之后整段少年经历（爱丁堡街头的军队、法国俘虏、1817 年拆 Old Tolbooth、1824 年大火时
与 Walter Scott 同在 St Giles 塔顶）**都是自传内容的复述**。

★★ **所以：拿讣告与自传当「两处证据」是塌缩**（同一处证据的两个 `source_id`）。
[[two-source-ids-is-not-two-evidences]]
**本道凡与自传重合的内容一律不计为独立证据**，只记下面「独立于自传的部分」。

## Source-linked observations（**只记独立于自传的**）

**① 家中排行：第四子、第十个孩子。**

> fourth son and tenth child of Alexander Nasmyth, ithe artist

★ 这条同时是**同名护栏的依据**：父亲是画家 Alexander Nasmyth，
Wilkie 称他 `the founder of the landscape painting school of Scotland`。
**语料里 23 处 `Alexander Nasmyth` 全指父亲**（已写进 `meta.json:known_namesakes`）。

**② ★★ 同一篇讣告内部自相矛盾。**

前面说他是 `the fourth son and tenth child`，后文却写：

> It was here that his youngest kon acquired the manual dexterity in the use of

★ **第四子 ≠ 幼子。** 同一篇文章里两个说法对不上。
**这不是我推断的矛盾，是原文摆在那里的**——凡引用他在家中位置，须标明出自哪一句。

**③ ★★★ 一条可核的人际链：Leonard Horner。**

> Along with Leonard Horner, he attended the first session in the winter of 1821 of the
> School of Arts (now the Herio

★ 这与 `02-conversations.md` 里那条悬着的线索**对上了**：马克思引用过
「Nasmyth 1852 年致工厂视察员 Leonard Horner 的信」。
**同一个人，1821 年同窗、1852 年通信。** 这条链让那封信的存在更可信，
**但信的原刊期号页码仍未定位**——见 Unknowns。

**④ 他在学生缴费簿上把自己写成 `tinsmith`。**

> tinsmith” in the students’ fee-book

★ 这是**自述**而非他人评价，且是在一个不需要修饰的场合（缴费簿）。
与 `03-expression.md` 里 E2（第一人称只用于划界与限定，不用于自夸）方向一致，
**但它来自一份 S2 材料**，只能作旁证。

**⑤ 他靠卖自制模型付大学学费。**

> pay the fees for his attendlance at the chemistry, mathematical, and natural philosophy classes
> at the University of Edinburgh from the proceeds of the sale of steam engine and other models

★ **待核**：这一条极可能也源自自传（措辞是转述体）。**在自传里定位到对应段落之前，
不得当作独立证据。**

## ★★ 二手材料里的错，逐条记下（**不改，只标**）

- 德文著录卡片写 **`Erfand 1839 d. Dampfhammer`**（1839 年发明蒸汽锤）。
  而 GB 9382 专利是 **1842-06-09**（DNB 与 datamp 一致）。
  ★ 1839 是**草图**年份的通行说法，卡片把它写成了发明年。**两个数不能混用。**
- 同一张卡片把自传写成 `AUt@PL esraphy, ed by … 3 ed, 1885`——
  与已知的 **1883 首版／1897 popular edition** 都对不上，**且 1885 正是 1897 版序言的落款年**。
  ★ **版次混乱在二手材料里是常态**，这正是 `attribution_basis` 里那条
  「引用必须连版次写」的现实理由。
- 卡片把 `Maudslay` 拼成 `Mandslay`、把 `Edinburgh` 拼成 `Réinburgh`／`Edinburch`——
  **OCR 与手写混合损伤**。凡从这份取字面，须回图像复核。

## Candidate Claims

**X1（fact，达标性待定）**：**他是 Alexander Nasmyth（画家）的第四子、第十个孩子。**
- 证据 A：讣告（`src-940890f8d2dd`）
- 证据 B：**待自传补**。★ 同一篇讣告内部就有 `youngest son` 的反说法，
  **在自传里核到之前不成条**。

**X2（fact，可成条）**：**1821 年冬他与 Leonard Horner 同在 School of Arts 首期。**
- 证据 A：讣告（`src-940890f8d2dd`）
- 证据 B：马克思转引的 1852 年致 Horner 的信（**转引，非一手**）
- ★ 两处都不是一手，**按本项目的分档只能记 `fact` 且置信度压低**；
  自传若有对应段落即可升格。

★ **本道不产出 mental-model／heuristic／value 类断言**——
S1/S2 材料是别人对他的记述，**不能用来推他的思考方式**。

## Contradictions and alternative explanations

- **核心风险已写在最前面**：讣告大部分内容是自传的复述，**与自传不构成两处证据**。
- **讣告的褒扬语气是体裁决定的**（`Another of Edinburgh's famous sons has passed away`），
  **不能当成同代人的独立评价**。
- MNRAS 1844／1846 两篇（S1）是学会记录员写的第三人称摘要——
  ★ 它们**可以**用来证「他在某年某会上讲了某题」，**不能**用来引他的原话。

## ★★★★ 2026-08-10 更正：**D6 被自传（P1）推翻，讣告把一次意外写成了一桩慷慨**

`05-decisions.md` 初稿据讣告（S2）写「他先把方案给了对手，专利是发现对方造出来之后才申请的」，
并已标明「自传核到之前不得当成确定事实」。**核了，不成立。**

- **讣告（S2）**：`Mr Nasmyth … gave the benefit of his [sketch] to M. [Schneider]`——**主动相赠**。
- **自传（P1，`src-75240b0a8dbb`，他自己写的）**：他当时**不在场**；合伙人 Gaskell
  `as an act of courtesy he brought them my Scheme Book and allowed them to examine it`；
  Bourdon `took careful notes and sketches of the constructive details of the hammer`；
  而他本人 `was, therefore, **in entire ignorance** of the fact that these foreign visitors had
  taken with them to France a copy of the plan and details of my steam hammer`。

★ **真实经过**：1842 年 4 月他应法国海军部长 Bouchier 之邀访法，顺道到 Creusot；
Schneider 不在，Bourdon 接待。他注意到一根锻得异常精确的大型船机曲柄，问是怎么锻的——

> His immediate reply was, "**It was forged by your steam hammer!**"

而他自己的记述是：

> **Great was my surprise and pleasure at hearing this statement.**

★★ **不是愤怒，是「惊讶且高兴」。** 这一句是本人物性格上很硬的一处证据，**且是 P1**。

★★★ **本条对产物的意义**：`04-external.md` 那条独立性警告在这里拿到了最强的实例——
**讣告不只是复述自传，它在这一处改写了事实的性质**（意外 → 慷慨）。
**这正是 divergence-map 该收的东西。**

## Unknowns and source gaps

- **同代人的独立记述本轮一份也没有**：没有同行的回忆录、没有 IMechE 的 memoir
  （按抓源实测，**IMechE 论文与讣告都是「未找到」，不是「够不着」**）。
  ★ 本道现在**全部建在讣告与学会摘要上**，这一条要写进 divergence-map。
- **1852 年致 Leonard Horner 的信**：原刊于工厂视察员报告，**期号页码未定位**。
  X2 与 `02-conversations.md` 的缺口都指着它，**是下一轮最值得找的一份**。
- 讣告全文本轮只读了前约 110 行（共 518 行），**后半未读**。

## Proposed Holdout cases

IDs only; research Agents must not inspect Holdout bodies.

## Handoff to adjudication

- Validate origin independence and evaluation-set separation before promotion.
- ★★★ **本道给下游的第一条不是断言，是独立性警告**：
  `06b` 与自传高度重合，**产物里不许把它们并列成「两处来源都说」**。
- ★ X1 待自传核（同篇内部已有反说法）；X2 两处皆非一手，置信度须压低。
- ★★ 二手材料里已确认三处错（蒸汽锤年份 1839 vs 1842、自传版次 1885、多处拼写）——
  **这些错本身是产物里 `divergence-map` 的好材料**：它们说明「关于他的通行说法」在哪里失真。
