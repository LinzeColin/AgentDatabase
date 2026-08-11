# Conversations and interviews

## Scope and assigned sources

**本道分到 4 份（train split）**：

| source_id | 出版年 | tier | 题名 |
|---|---|---|---|
| `src-96246ca9968e` | 1884 | P1 | Dead, Yet Living. An Address Delivered at Keene, N. H., Me…inn, Heath, and Company. 1884 |
| `src-de206b40fe7b` | 1891 | P1 | Speeches. By Oliver Wendell Holmes, Junior. Boston: Little… and Son, Cambridge）——初版，11 篇 |
| `src-4c4e28b10d9c` | 1913 | P1 | Speeches. By Oliver Wendell Holmes. Boston: Little, Brown,… Cambridge, U.S.A.）——增订本，18 篇 |
| `src-c7a49bbb129f` | 1913 | P1 | Speech of Mr. Justice Holmes at a Dinner of the Harvard La…245／260；封面 OCR 见 attribution） |

★ 本节由台账机械导出（`emit_lane_scope.py`），**不含任何阅读判断**；只投影 `split == train` 的行。

## Source-linked observations

**本道的射程先说清楚**：他没有留下访谈记录，可取得的对话性材料是**当众讲话的印本**——
有明确听众、有呼语、为一次具体场合而作。**这不是访谈，产物里不许说成访谈。**

★ 本道 4 份里有 3 份互为转载（1891 版 94.3% 落在 1913 增订本内，1884 单行本 68.7%
落在讲词集内，1913 GPO 单行本 66.9% 落在增订本内）。**它们不是四处独立证据**；
已在台账写 `derived_from`，量法见 `_corpus/00-重复源与派生关系.md`。

1. **开口先认领听众，再进入内容。** `src-c7a49bbb129f`／`src-4c4e28b10d9c`（同一篇，1913-02-15）：
   `Mr. Chairman and Gentlemen:`；`src-4c4e28b10d9c` 1911 年那篇：
   `Mr. President and Brethren of the Alumni:`。
   → 呼语逐篇不同，**按场合改**，不是套用的开场白。

2. **从一个别人问的问题起头，而不是从自己的主张起头。** `src-96246ca9968e`（1884 年
   Keene 讲词，同文亦见 `src-de206b40fe7b`）：
   `Not long ago I heard a young man ask why people still kept up Memorial Day,
   and it set me thinking of the answer`。
   → **把听众可能有的疑问先摆到台面上**，再给答案。

3. **对着质疑者说话，且先替他把话说完。** `src-4c4e28b10d9c`（1886-02-17 讲于哈佛本科生）：
   `And now, perhaps, I ought to have done. But I know- that some spirit of fire will feel
   that his main question has not been answered`，随后逐句代拟对方的反问
   （`What is all this to my soul ?`），再答
   `Gentlemen, I admit at once that these questions are not futile, that they may prove
   unanswerable, that they have often seemed to me un- answerable. And yet I believe there is an answer`。
   → **先承认对方的问题成立，甚至承认自己也答不上过**，然后才给自己的答案。
   这是本道最稳的一种模式，在 05 道的异议意见里有同构的对应（先陈述对方的理由）。

4. **用一个具体到近乎琐碎的画面开头。** `src-4c4e28b10d9c`（1895-05-30）：
   `Any day in Washington Street, when the throng is great- est and busiest,
   you may see a blind man playing a flute`，紧接
   `I suppose that some one hears him. Perhaps also my pipe may reach the heart of some passer in the crowd`。
   → **先给画面，再把自己放进画面里**——降低自我份量的一种固定手法。

5. **引别人的原话来定位自己要反对什么。** 同篇：
   `I once heard a man say, " Where Vanderbilt sits, there is the head of the table.
   I teach my son to be rich." He said what many think`。
   → 他反对的对象**是一句可以被引述的话，不是一个抽象立场**。

6. **场合越正式，自我评价越低。** `src-c7a49bbb129f`（1913 年纽约哈佛法学院协会晚宴）：
   `Vanity is the most philosophical of those feelings that we are taught to despise`，
   并把自己说成 `I have passed that age, but I still am on the firing line`。
   → 在最该自我表彰的场合，**先把「想被夸」这件事挑明并解释它**。

## Candidate Claims

- **C5（work-method）**：先替反对者把最强的反问说完，再回答。证据：本道第 3 条；
  跨道第二簇见 05 道异议意见的结构。
- **C6（expression）**：以具体画面／他人原话开场，把抽象主张锚在可复述的东西上。证据：第 4、5 条。
- **C7（boundary）**：他的「对话」材料全部是公开讲话，**没有私下对话可取**
  （书信集 1941／1953 印本年在 PD 分界之后，本项目不取）。

## Contradictions and alternative explanations

- 第 1、6 条都可能只是**19 世纪晚宴讲词的通用礼节**，不是他个人特征。
  **要用同代人的讲词做对照才能分开**——本工作区没有这种对照材料，
  故 C6 只作为 `expression` 类记录，**不升为 mental-model**。
- 第 3 条与 05 道的相似可能是**法律训练的通用形态**（先述对方主张再驳），
  同样无法在本工作区内证伪。已写进 `hypotheses` 的候选，不作为已证事实。

## Unknowns and source gaps

- 无速记稿、无听众反应记录：**讲词的实际效果不可知**，只有文本。
- 1891 与 1913 两版之间他改没改旧篇的字，本轮**未逐篇比对**（只量了整体包含率 0.9429）。

## Proposed Holdout cases

IDs only; research Agents must not inspect Holdout bodies.

## Handoff to adjudication

C5 交给 05 道求第二簇；C6／C7 只在本道成立，按 `expression`／`boundary` 记。
