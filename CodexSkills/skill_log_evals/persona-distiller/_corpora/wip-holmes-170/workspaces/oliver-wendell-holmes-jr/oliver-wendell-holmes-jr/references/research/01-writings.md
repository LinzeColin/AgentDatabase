# Writings and systematic works

## Scope and assigned sources

**本道分到 2 份（train split）**：

| source_id | 出版年 | tier | 题名 |
|---|---|---|---|
| `src-6deab2cc96a0` | 1882 | P1 | The Common Law. By O. W. Holmes, Jr. London: Macmillan & C…ss, Cambridge, Mass., U.S.A.） |
| `src-48135d4164bd` | 1920 | P1 | Collected Legal Papers. By Oliver Wendell Holmes. New York…ress, Norwood, Mass., U.S.A.） |

★ 本节由台账机械导出（`emit_lane_scope.py`），**不含任何阅读判断**；只投影 `split == train` 的行。

## Source-linked observations

**逐字引文一律照录 OCR，不改讹字**；折行连字符（`instru- mentality`）由核验器归一，
讹形（如 `hmits`＝`limits`）若入引文则在括号里注明。本道两份都是 20 世纪初排印，
无长 s 问题（本工作区实测：干净 13 份、未核 1 份）。

1. **开篇先否定一个方法，再给自己的方法。** `src-6deab2cc96a0` 正文第一段：
   `The object of this book is to present a general view of the Common Law`，
   紧接着 `To accomplish the task, other tools are needed besides logic`，
   然后才是那句 `The life of the law has not been logic : it has been experience`。
   → **他的顺序是「目标 → 现有工具不够 → 换工具」**，不是先亮结论。

2. **把「不够」讲成一份清单，而不是一句抱怨。** 同源紧接：
   `The felt necessities of the time, the prevalent moral and political theories,
   intuitions of public policy, avowed or unconscious, even the prejudices which judges
   share with their fellow-men, have had a good deal more to do than the syllogism
   in determining the rules by which men should be governed`。
   → 五项并列，**最后一项是「法官自己的偏见」**——他把观察者也算进被观察的系统里。

3. **历史只用到够用为止，并且当场划界。** `src-6deab2cc96a0`：
   `I shall use the history of our law so far as it is necessary to explain a conception
   or to interpret a rule, but no further`，并同时点出两个相反的错：
   一是以为熟悉的东西向来如此，二是 `The other mistake is the opposite one of asking too much of history`。
   → **他给方法配的是「两侧都会翻车」的护栏，不是单向的告诫。**

4. **射程声明写在序里，不写在结论里。** `src-6deab2cc96a0` 序言：
   `This book is written in pursuance of a plan which I have long had in mind`，
   并交代取材于 `a number of articles in the American Law Review`、
   因 Lowell Institute 讲座之邀才写成专著；随后明说
   `I have therefore not attempted to deal with Equity`。
   → **先说自己不打算做什么。** 这一条与 05 道里判决意见的收口方式同形。

5. **换到「法律是什么」时，他改用一个可操作的定义。** `src-48135d4164bd`（1897 年
   Boston University 法学院讲词，收入 1920 年文集）：
   `When we study law we are not studying a mystery but a well-known profession`，
   进而 `The object of our study, then, is prediction, the prediction of the incidence
   of the public force`。
   → **定义的检验标准是「能不能拿来预测」**，不是「合不合乎道德直觉」。

6. **他用一个刻意难看的视角做纯化器。** 同源：
   `If you want to know the law and nothing else, you must look at it as a bad man,
   who cares only for the material consequences which such knowledge enables him to predict`。
   → 这是**方法论装置**：换一个不关心道德的观察者，好把道德词汇从法律陈述里筛出去。
   他自己随即说明理由：法律语言 `is full of phraseology drawn from morals`。

7. **对「因为一直是这样」明确表态。** 同源：
   `It is revolting to have no better reason for a rule of law than that so it was laid down
   in the time of Henry IV`，并接
   `For the rational study of the law the black-letter man may be the man of the present,
   but the man of the future is the man of statistics and the master of economics`。
   → 与第 3 条不矛盾：**历史用来解释规则的来处，不用来为规则辩护。**

## Candidate Claims

- **C1（work-method）**：立论前先声明射程与不做的部分。证据：本道第 4 条 + 05 道判决收口。
- **C2（mental-model）**：法律陈述的检验标准是可预测性，不是道德一致性。证据：第 5、6 条。
- **C3（work-method）**：用一个与自己立场相反的观察者位置做纯化器（`bad man`）。证据：第 6 条。
- **C4（value）**：历史解释来处，不为现状辩护。证据：第 3、7 条。

★ 以上四条**都只有本道一种证据簇**，能不能立住要看 02／03／05 道有没有独立的第二簇——
按合成门的要求（≥2 源、≥2 语境、≥2 独立证据簇），**本道自己不足以支撑任何一条**。

## Contradictions and alternative explanations

- 第 1 条的「先否定后给出」可能是**讲座体裁**造成的（本书由 Lowell Institute 讲座改写，
  序言自陈 `The Lectures as actu- ally delivered were a good deal simplified`），
  而非他的思维顺序。**要用非讲座体裁的材料交叉验证**（05 道的判决意见不是讲座）。
- 第 6 条的 `bad man` 常被当成他的法律观本身；但在原文里它是**认识论工具**
  （用来分开两套词汇），不是价值主张。**两种读法都要留在产物里，不能只留一种。**

## Unknowns and source gaps

- 本道两份相隔 38 年（1882 / 1920），中间的演变**只能从别道补**。
- `src-48135d4164bd` 是文集，收录 1885–1918 各篇；**同一篇又见于 03 道的讲词集**，
  已在台账写 `derived_from`（见 `_corpus/00-重复源与派生关系.md`），
  引用时须避免把同一篇算成两处独立证据（[[two-source-ids-is-not-two-evidences]]）。

## Proposed Holdout cases

IDs only; research Agents must not inspect Holdout bodies.

## Handoff to adjudication

四条候选断言全部**待跨道合流**。本道单独能支持的只有对这两部书的事实陈述。
