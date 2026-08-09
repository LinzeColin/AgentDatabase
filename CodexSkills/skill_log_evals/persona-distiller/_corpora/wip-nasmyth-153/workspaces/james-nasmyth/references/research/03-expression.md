# Expression and voice

## Scope and assigned sources

本道**能拿来量语域的，只有两份，而且它们分属两个语域**：

- `src-231dfc291417` — 1836 下议院委员会**逐字问答**（口述，被追问状态下的即席回答）。
  ★ **这是本人物唯一可得的逐字口述记录**（见 `02-conversations.md` 的射程说明）。
- `src-7b92506095cc` — 1841 滑动原理论文（**书面**，面向同行技术读者，自己布局自己收尾）。

★★ **本道的价值就在这两份的对照上**：同一个人，相隔五年，一口一笔。
**单看一份会把语域当成声口。** [[measured-voice-in-the-wrong-register]] 记的正是这个坑——
拿合著技术论文的第一人称密度去判「有没有声口」。

**尚未读**：自传（88 万字符）——它是第三个语域（**回忆体、面向大众**），
读完之后本道要重写，**现在这份是两点连线，不是三点定面**。

## Source-linked observations

**① 口述状态下，他的答句短、且几乎不修辞。**

被问「省多少」时（Q.298）他的整句回答是：

> **About a third.**

被追问归因时（Q.302），整句回答是：

> **Yes.**

★ 委员会记录里他有能力长篇（Q.294、Q.307、Q.310 都是长段），
**但被问到量和归因这两类问题时，他给的是最短的可判读答案。**

**② 长答句的骨架是「先给做法，再给理由，最后给代价」。**

Q.310 那一段：先说主人若要工人做出他想要的形（做法），
再说主与工的品味落差是障碍（理由），最后落到
`a very great loss of time to the master in giving necessary instructions to his men`（代价）。
★ Q.294、Q.307 同一骨架。**三处同形，不是偶合。**

**③ 他在口述里主动划自己的资格边界，用的是并列句式。**（Q.304）

> ] have all my life been in _ panionable contact with the working mechanic, and being
> moreover the son of » artist of some celebrity, I have, **in the union of those two
> advantages**, been enabled to see …

★ `in the union of those two advantages` 是他自己的措辞——**他把自己的资格说成两件事的交集，
不是一件事的权威。**

**④ 书面语域完全不同：长句、层层从句、带情绪的形容词。**

1841 ¶484 一个句子里套了三层（`by which we are enabled to constrain … that with scarce any
expenditure of force … as may well be considered a mighty triumph over matter`），
并用上 `mighty triumph over matter`、`dazzling results`、`beautiful simplicity`、
`his admirable mind` 这类口述里**一次也没有出现**的词。

**⑤ 书面语域里他会写「我」，而且是用来划界的。**

- ¶483 `but for the introduction of the principle **which I am about to describe**`
- ¶491 `It would be blamable indeed … were **I** to suppress the name of …`
- ¶504 `were **I** to endeavour to trace in detail … a thousand pages would not give space`
- ¶505 `Hitherto, **so far as I am aware**, the form of tools … has not received that attention`

★ 四处 `I` **没有一处是在自夸**：两处是「我接下来要讲什么」，一处是「不点别人的名我该受责备」，
一处是 `so far as I am aware`（**给自己的断言加限定**）。

## Candidate Claims

**E1（work-method／声口，达标）**：**被问到量与归因时，他给最短的可判读答案；
展开时用「做法→理由→代价」的固定骨架。**
- 证据 A：Q.298 `About a third.`、Q.302 `Yes.`（`src-231dfc291417`）
- 证据 B：Q.294／Q.307／Q.310 三处同骨架（`src-231dfc291417`）
- ★ **但两条证据同属一个 source_id**——按本项目的门（≥2 source_id）**不达标**。
  需自传补第二份来源。**本轮不写进断言层。**

**E2（blind-spot 候选，达标性待定）**：**他的第一人称几乎只用于划界与限定，不用于归功自己。**
- 证据 A：1841 四处 `I` 全部是「接下来讲什么／不点名该受责备／据我所知」（`src-7b92506095cc`）
- 证据 B：1836 Q.304 用 `in the union of those two advantages` 把资格说成交集（`src-231dfc291417`）
- 语境：「技术论辩」「答问」　→ **2 个 source_id、2 个语境，达标。**
- ★★ 与 `01-writings.md` 的 C4（`blamable` 让功）**是同一件事的两面**，
  合并成一条还是拆成两条，**等自传读完再定**。

## Contradictions and alternative explanations

- **★★★ 语域差异不等于声口差异。** 口述短、书面长，这在任何人身上都成立；
  **把它当成「他这个人说话简短」是错的**。本道之所以还敢记 E1，是因为
  「被问量与归因时最短」是**同一场口述内部的对比**（同一份材料里他有长段），
  不是跨语域的对比。
- **1836 的记录经过委员会书记整理**，措辞可能被规整过。逐字程度已知的界限：
  该卷是 `MINUTES OF EVIDENCE`，体例上逐问逐答，但**没有速记原稿可比对**。
- **1841 的浮夸词可能是当时技术写作的通行文体**，不是他个人特征。
  ★ **本轮无法判定**——要与同卷其他作者（Buchanan／Tredgold／Rennie／Willis）对照才知道。
  语料里有全卷（`03b`，**有意未入库**，因为与 `03` 重份），**若要做这个对照可临时取用**。

## Unknowns and source gaps

- **自传未读**——第三个语域（回忆体）缺席。本道现在是**两点连线**。
- **第一人称密度没有量**（`check_stance_density` 只在质检门里跑，本道未单独取数）。
  ★ 提醒：那件判据在**判不出语种时返回 `None`**，而 OCR 损伤严重的几份可能落进这一档；
  取数时要看 `**判据说未核验的**` 那一栏，**不能把「未核验」读成 0**。
- **没有任何录音／影像**：他 1890 年去世，这一类材料**结构上不存在**，不是没找到。

## Proposed Holdout cases

IDs only; research Agents must not inspect Holdout bodies.

## Handoff to adjudication

- Validate origin independence and evaluation-set separation before promotion.
- ★ **E1 不达标**（两条证据同属一个 source_id），本轮不进断言层；E2 达标但与 writings 的 C4 重叠，待合并判断。
- ★★ **本道最该带给下游的一条不是断言，是警告**：
  这个人物只有一份逐字口述记录，**任何关于「他怎么说话」的断言都建在一份材料上**，
  必须在 divergence-map 里写明。
