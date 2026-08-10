# Writings and systematic works

## Scope and assigned sources

Train-split、`dimensions` 含 `writings` 的 13 份，全部 P1：

| source_id | 年 | 载体 |
|---|---|---|
| `src-a16660d41422` | 1888 | Phil. Trans.「On certain Mechanical Properties of Metals considered in relation to the Periodic Law」 |
| `src-827f6033da2f` | 1891 | Proc. Roy. Soc.「On Certain Properties of Metals considered in Relation to the Periodic Law」 |
| `src-3a7b624f0324` | 1891 | Phil. Trans.（Gold–Aluminium Series of Alloys 那一卷） |
| `src-11156663a5e4` `src-4ae0892cbde8` `src-60539abbb73b` `src-fff1b6898cd1` | 1895–96 | Phil. Trans. 合金系列 |
| `src-baf16940309f` `src-2ebdf104a176` `src-accdb5e0821f` | 1898–1900 | Phil. Trans. 合金系列 |
| `src-b63e790a63d6` | 1890 | Nature |
| `src-06496f1d3bc2` | 1898 | Canada's Metals（讲演单行本） |
| `src-8268c67b4de9` | 1891 | Introduction to the Study of Metallurgy |
| **`src-d690d5a293a8`** | **1891** | **Alloys Research Committee 第一份报告**（Proc. IMechE） |
| **`src-391ca73471aa`** | **1893** | **同上，第二份** |
| **`src-269db01c421a`** | **1899** | **同上，第五份** |

★ **本道只用训练侧材料**；非训练侧的不在此列，写作时未打开。

★★ **上一轮记的「五份报告全缺」已补齐**（原记 `numFound 0`——
那是**检索式的缺陷不是材料不存在**：`title` 字段只写 `Proceedings`、
`year` 对四卷都报 1849，改用 `creator:` 检索得 numFound 118）。
其中 **1895 与 1897 两份 `dimensions` 记的是 `decisions`，本道不引**，
留给 05-decisions；本道只取 `writings` 那三份。

## Source-linked observations

### ① 方法细节不在论文里，在另一份报告里，由论文**指过去**

> `In a recent report to the Institution of Mechanical Engineers, in which details
> of the method of calibration are embodied, I have described a suitable
> arrangement for obtaining, by the aid of photography, autographic curves which
> represent the cooling or heating of masses`
> —— `src-827f6033da2f`（1891）

**论文正文不复述标定方法，只给出它在哪一份报告里。** 要复核方法得去取那一份。

#### ★★★ 追加：**那一份取到了，指过去的东西真的在那边**

上一轮这条只能停在「他说细节在那边，而那边我们没有」。
现在 `src-d690d5a293a8`（1891 IMechE 第一份报告）在手，**逐条对上**：

> `but it is far better to calibrate the scale by heating the thermo-junction to
> temperatures which have been very carefully determined by the aid of the air
> thermometer`
> —— `src-d690d5a293a8`（标定）

> `securing a photographic record of Its movement. The following plan may
> therefore be recommended when a high degree of accuracy is required.`
> —— `src-d690d5a293a8`（照相记录法）

词频（同一份）：`calibrat` 5 处、`photograph` 13 处、`autographic` 2 处、
`thermo-junction` 16 处、`pyrometer` 14 处。

★★ **这条因此从「他这样写」升级成「他这样写，而且指得准」**——
1891 年 Proc. Roy. Soc. 那句 `details of the method of calibration are embodied`
指向的那份报告，**确实把标定、照相、autographic curve 三样都写在里面**。
**交叉引用不是修辞，是可兑现的。**

### ② 自己上一篇的结论，在新论文**首页重述一遍**

> `is of special interest in connexion with the generalisation given in my earlier
> paper and re-stated on' the first page of this`

★★★ **`on'` 那个撇号是印本上的 OCR 讹形，照录。**
上一轮这条把它**悄悄抹平成 `on the first page`** 再当逐字引文用——
本轮写了一个「逐条回原文比对」的脚本才查出来（8/10 过，这是不过的那条）。
**改了讹字就不再是逐字引文了**，而抹平的动作在文本里不留痕迹。

同文开头带页码指回：

> `In a previous paper published in the ' Philosophical Transactions '
> (1888, A, pp. 339 — 349)`
> —— 均出自 `src-827f6033da2f`

**给坐标的同时把结论抄在手边**，读者不必非去取原件。
被指的那篇即 `src-a16660d41422`，本工作区内有，可对照。

### ③ 具体操作归到**具名助手**名下，并说明凭什么是他

> `This portion of the manipulation was performed by my assistant, Mr. Groves,
> whose long experience in melting gold enabled him to select the latest moment
> before solidification at which the gold could be poured.`

> `I have to express my thanks to my assistant, Mr. H. C. Jenkins, for his aid in
> conducting these experiments.`
> —— 均出自 `src-827f6033da2f`

**不是笼统致谢：写明哪一段操作、由谁做、他凭什么做得了。**

### ④ 投稿之后发现的东西，写成**带日期的补记**附在文末，不改正文

> `[April 20, 1891. — In the course of the investigation, it became evident that,
> as is the case when aluminium is alloyed with copper or iron, the addition of
> aluminium to gold is attended with evolution of heat. The following experiment
> was therefore arranged, with a view to obtain evidence on this point : —`
> —— `src-827f6033da2f`

**正文保持提交时的样子，新证据另起一段并标日期**，读者分得清哪些是当时就知道的。

### ★★★ ⑤ 「把新工作接在自己旧工作后面」——**四个年份，同一个动作**

| 年 | 出处 | 逐字 |
|---|---|---|
| 1891 | `src-d690d5a293a8` | `The Committee desired me to extend an investigation I had previously made upon the application of the " periodic law " of Xewlands and l£< ndieleef to the mechanical properties of metals.` |
| 1893 | `src-391ca73471aa` | `The main object in view was to extend a research I had previously made upon the application of the "periodic law" of Newlands and Mendeleeff to the mechanical properties of metals.` |
| 1899 | `src-269db01c421a` | `I have elsewhere § shown that the iron as deposited breaks with a tension of 2 • 7 tons per square inch` |

★ 1891 那条里 `Xewlands`（应为 `Newlands`）与 `l£< ndieleef`（应为 `Mendeleeff`）
是**印本 OCR 讹字，照录不改**；1893 那份同一句印得干净，两相对照即可确认所指。

**同一个句式跨 1891→1893：「extend an investigation I had previously made upon」（★ **这不是引文，是我并列两种措辞的记法**）。**
到 1899 年变成 `I have elsewhere § shown`——**连边注符号 `§` 都带着，出处仍在别处。**

★★ 这与 02-conversations 观察 ④（1896 年 `carry one step further the work of Graham`）
**是同一个动作的两个方向**：接前人，也接自己。

### ★★★ ⑥ 具名到人，**跨 1891／1893 两份报告，且写明「谁做的」与「谁的主意」不是一回事**

> `In di'awing this Eeport to a conclusion, I would thank Mr. Jenkins and Mr.
> Stansfield, whose assistance the Institution has given me in conducting these
> investigations.`
> —— `src-391ca73471aa`（1893）

> `This copper was analysed by one of my own students, Mr. Allan Gibb, who has
> devoted much care and attention to this particular portion of the investigation.`
> —— `src-391ca73471aa`（1893）

★ `di'awing`／`Eeport` 是 OCR 讹字，**照录**。

**`Mr. Jenkins` 就是 1891 年 Proc. Roy. Soc. 里具名致谢的那位助手**（观察 ③）——
**同一个人、两个年份、两种载体。**
观察 ③ 原来「两条同出一份、不构成两处证据」的限制，**到这里解除了**。

## Candidate Claims

- **方法与结果分开发表**：论文给出标定方法的**出处**而不复述，**且该出处兑得出来**。依据：观察 ①（含 1891 IMechE 的逐条核对）。
- **自引带坐标且重述**：引前作给卷年页码（`1888, A, pp. 339 — 349`），并在新文首页重述其结论。
  依据：观察 ②（1891 Proc. Roy. Soc.）**＋ 1893 IMechE 开篇的复述段**——
  **跨两个年份、两个学会，本道第二条跨来源的断言。**
- **署名到人**：关键操作归具名助手，并给出他能胜任的理由。依据：观察 ③ **＋ ⑥（1893，跨来源印证）**。
- **事后证据另记**：提交后的新发现以带日期补记附文末，不改动正文。依据：观察 ④。
- **★ 把新工作接在自己旧工作后面**：`extend … I had previously made upon`，
  **1891／1893 同句式，1899 仍指向别处（`I have elsewhere § shown`）**。依据：观察 ⑤。

## Contradictions and alternative explanations

- ~~观察 ③ 的两条出自同一份来源，不是两处独立证据~~ →
  **已解除**：`Mr. Jenkins` 在 1891（Proc. Roy. Soc.）与 1893（IMechE）**两份不同载体**里都具名（观察 ⑥）。
- 观察 **④ 仍只有一处出处**（`src-827f6033da2f`）。
  「带日期的文末补记」**目前仍是单点形态描述，不是一贯做法**。
  （观察 ② 已跨来源，见下条。）
- ~~四条观察全部来自 1891 年那一份，时间跨度上的代表性没有证据~~ →
  **已解除**：观察 ⑤⑥ 覆盖 **1891／1893／1899** 三个年份、两种载体
  （Proc. Roy. Soc. 与 Proc. IMechE）。**本道现在到得了「一贯」这一层，但只对观察 ①⑤⑥。**
- ★★★ **观察 ⑤ 的 1891 与 1893 不是两处证据——已回源确认，不是猜的。**
  两条句式几乎一样，我去读了 1893 那句的上文：

  > `In presenting a Second Eeport* to the Alloys Eesearcli Committee, it may be
  > well to state briefly the nature of the investigation intrusted to me, and the
  > conclusions to which the previous work had led.`
  > —— `src-391ca73471aa`

  **它明说了这是复述**（`state briefly the nature of the investigation … and the
  conclusions to which the previous work had led`）。
  **所以那是同一段立项缘由被印了第二次，不是第二次独立的动作。**
  1899 那条（`I have elsewhere § shown`）句式与内容都不同，是独立的一处。
  **观察 ⑤ 稳的是两处（1891/1893 合一 ＋ 1899），不是三处。**

- ★★★ **而同一句话把观察 ② 从「单点」抬成了「跨来源」。**
  观察 ② 原来只有 1891 Proc. Roy. Soc. 那一处
  （`…given in my earlier paper and re-stated on' the first page of this`）。
  1893 IMechE 开篇这句**是同一个动作的第二处**：
  **续篇开头先把前篇的缘由与结论复述一遍，让读者不必去取原件。**
  **两个年份、两种载体、两个学会。**
  ★ 记账要点：**同一段文字在一条断言上是塌缩的，在另一条断言上是独立的**——
  取决于断言问的是「他做了什么」还是「这段话说了什么」。

## Unknowns and source gaps

- ~~Alloys Research Committee 五份报告全缺（archive.org 报 `numFound 0`）~~ →
  **已补齐五份。** ★ 那个 `numFound 0` **是检索式的缺陷，不是材料不存在**：
  `title` 字段只写 `Proceedings`、`year` 对四卷都报 1849；改用 `creator:` 得 numFound 118。
  **「year 字段不可信」这条上一轮的报告里就写过，而当轮的检索式仍然按 year 过滤。**
  （记在这里是因为**下一次还会这样**：写过的教训不等于用过的教训。）
- ★ 新的缺口：1895 与 1897 两份报告**已在语料里，但 `dimensions` 记的是 `decisions`**，
  本道按分道纪律未引。**若它们其实也含 `writings` 材料，本道就漏了两个年份**——
  这要由重标 `dimensions` 来解决，不是本道自己改引用范围。
- 1885 年前署 `W. C. Roberts` 的论文本道未收（改姓前的作品），
  与「一贯做法」的时间跨度断言直接相关。
- 13 份里 10 份是 Phil. Trans. 同一系列，**载体集中**；跨载体的写作形态对比证据薄。

## Proposed Holdout cases

IDs only; research Agents must not inspect Holdout bodies.

（本轮未提名。提名须在隔离样本划定之后、且不打开正文。）

## Handoff to adjudication

**本道现在分两层，下游必须分开用。**

**够得着「一贯」的三条**（各有 ≥2 个年份、≥2 种载体）：

| 断言 | 年份 | 载体 |
|---|---|---|
| 方法与结果分开发表，且**出处兑得出来** | 1891 Proc. Roy. Soc. → 1891 IMechE | 两个学会（**逐条核对过**） |
| 续篇开头复述前篇的缘由与结论 | 1891、1893 | Proc. Roy. Soc.／Proc. IMechE |
| 关键操作归**具名**助手（`Mr. Jenkins` 两处） | 1891、1893 | 同上 |

**只到「形态」这一层的两条**（各一处出处，都出自 `src-827f6033da2f`）：
带日期的文末补记；「把新工作接在旧工作后面」只稳到两处（1891/1893 塌缩 + 1899）。

★★ **一条记账纪律，本轮实测出来的**：
1893 那段复述**在「他做了什么」这条断言上与 1891 塌缩成一处，
在「他怎样开篇」这条断言上却是独立的第二处。**
**同一段文字算几处证据，取决于断言问的是什么**——
不能按 source_id 数，也不能按年份数。

★ 另：本道 16 份中大部分在研究门报 `authorship-unproven`
（署名被 OCR 打坏／改姓前旧姓／署名不带教名等，见待裁定 ㉕）。
**那是判据认不出署名形态，不是这些材料的归属可疑。**
★★ 本轮已修好其中一类（复姓 + 缩写名的署名行），
该人物过归属从 **3/30 升到 12/30**；**剩下的仍在 ㉕ 待裁**。
