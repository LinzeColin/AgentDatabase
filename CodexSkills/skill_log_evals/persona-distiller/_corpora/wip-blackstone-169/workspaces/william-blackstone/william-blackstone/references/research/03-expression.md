# Expression DNA and micro-behavior

## Scope and assigned sources

**本道分到 3 份（train split）**：

| source_id | 出版年 | tier | 题名 |
|---|---|---|---|
| `src-e9e580101aaa` | 1747 | U | The Pantheon: a Vision. London: Printed for R. Dodsley at …ly's Head in Pall-Mall [1747] |
| `src-3e6b4b822d4f` | 1758 | P1 | A Discourse on the Study of the Law; being an Introductory…am Blackstone. [Oxford, 1758] |
| `src-80e44ce94930` | 1763 | P1 | The Lawyer's Farewell to his Muse. Written in the Year 174…. Dodsley, M DCC LXIII [1763] |

★ 本节由台账机械导出（`emit_lane_scope.py`），**不含任何阅读判断**；只投影 `split == train` 的行。

## Source-linked observations

★★ **本道不含任何我从正文提取的逐字引文**：本道分到的印本，长 s 被 OCR 读成 `f`（讹字率见 `metrics.longs_corruption`），**取不出可核的逐字串**。下面凡带反引号的字符串，都是**台账 `attribution` 字段里抓源方逐字照录并硬校验过的扉页／首行**，已标明出处；**不是我自己从正文里截的**。一个字都没有改。

1. **他写过韵文，而且是有意与法律生涯并置的。** `src-80e44ce94930` 是
   *The Lawyer's Farewell to his Muse*，台账题名照录含 `Written in the Year 174…`——
   **写作年与刊出年（1763）不是同一年**，收在 Dodsley 选集里。

2. **这首诗在选集里不署名。** 归属靠**另一份语料内的同代人证词**：
   遗嘱执行人 James Clitherow 撰、附于 1781 年判例汇编卷首的传记，
   台账照录作 `me of his Miſcellanies, intituled, The Lawyer's Faracell 1 Mae`
   （`Faracell 1 Mae` 是 OCR 把 `Farewell to his Muse` 打碎）。
   → **本工作区里唯一一份「靠外部证词而非自身扉页定归属」的材料。**

3. **就职讲词是「讲出来的」文体**：`src-3e6b4b822d4f` 台账照录首行作
   `Mu Vics-CHancaiiloR, AND GENTLEMEN OF THE UNIVERSITY)`——**对着人开口**，
   不是对着读者落笔。同一篇文字后来成了 1766 *Analysis* 的卷首，
   也进了《释义》卷一的导论（三处同源，台账已记）。

4. **1747 年那一份归属未定**（`src-e9e580101aaa`，tier `U`）：印本无署名，
   外部证据只有一条编目。**本道只登记它存在，不据它下任何关于他的断言。**


## Candidate Claims

- **clm-bs-voice-01｜他有一层不写在法律著作里的韵文声口，且自己把它与法律生涯并置**
  （诗题本身就是「向缪斯告别」）。证据：`src-80e44ce94930` 题名照录 + 1781 传记里的指认。
- **clm-bs-voice-02｜他的开场是对着听众的，不是对着读者的**：讲词首行直接呼语。
  证据：`src-3e6b4b822d4f` 台账照录首行。
- **clm-bs-voice-03｜同一篇文字被他反复用作三处的开头**（讲词 → 纲目卷首 → 全书导论）。
  证据：台账三条 `derived_from`／重叠记录。★ 这条与 01 道的 `clm-bs-arch-02` 互相印证。


## Contradictions and alternative explanations

- **诗的归属只有一条外部证词**（1781 年那篇传记），**不是两处独立证据**。
  ★ 传记作者是他的遗嘱执行人——**利害相关方**，这一点必须写进产物。
- 1747 年那一份 tier `U`，**不得用来支持任何「他早年写什么」的断言**。
- 「对着听众开口」也可能只是就职讲词这一体裁的固定格式，**本道分不开**。


## Unknowns and source gaps

- 本道三份印本的长 s 全部被读成 `f` 或保留本字，**取不出可核的逐字引文**；
  证据均为台账照录，已标明。**一个字没改。**
- 诗的**写作年**只有题名里的一个残缺串（`Written in the Year 174…`），**具体年份本道读不出**。


## Proposed Holdout cases

IDs only; research Agents must not inspect Holdout bodies.

- 用例方向：`case-voice-*`、`case-style-decoy-*`——能不能分辨「他的语域」与「像他的仿作」。

## Handoff to adjudication

- 三条候选断言均带 source_id。
- ★ **`clm-bs-voice-01` 必须连「归属只有一条证词、且出自利害相关方」一起写进产物**，
  不许简化成「他写过一首诗」。

