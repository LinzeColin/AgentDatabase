# Expression DNA and micro-behavior

## Scope and assigned sources

**本道分到 5 份（train split）**：

| source_id | 出版年 | tier | 题名 |
|---|---|---|---|
| `src-ccb348b4687c` | 1914 | P1 | Eine Grundlegung der Rechtssoziologie |
| `src-c78fac5e78b4` | 1916 | P1 | Die Rechtswissenschaft als Norm- oder als Kulturwissenschaft |
| `src-bfbcf301361b` | 1918 | P1 | Politische Weltanschauung und Erziehung |
| `src-f7ad7280693a` | 1922 | P1 | Staat und Recht |
| `src-31c509a0e332` | 1926 | P1 | Les rapports de système entre le droit interne et le droit international public |

★ 本节由台账机械导出（`emit_lane_scope.py`），**不含任何阅读判断**；只投影 `split == train` 的行。

## ★★ 本道能用的其实只有三份

- `src-c78fac5e78b4`（1916）**禁引**——Fraktur 讹形超门，一句逐字都不取。
  ★ 偏偏它是本道声口密度第二高的一份（6.96／万词），**能引的与话最多的不重合**。
- `src-31c509a0e332`（1926，法语）按抓源指令第 ⑥ 条**不作第一人称声口的证据**：
  未找到译者署名，也未找到「本人以法文撰写」的声明。可作事实来源。
- ⇒ 下面的逐字引文只来自 **1914 / 1918 / 1922** 三份。

## Source-linked observations

**逐字引文一律照录 OCR，不改讹字**；折行连字符由核验器归一。

### 1. ★ 他会在**跨越 Sein→Sollen 的那一刻停下来，明说自己正在跨**

`src-bfbcf301361b` 全文最长的一段第一人称，逐字：

> Indem ich die Erörterung dieses Postulates aufnehme, trete ich aus der Ebene einer
> Seinserklärung und kausalen Wirklichkeitebeschreibung in ein Gebiet der Soll-Betrachtung.
> Während ich bisher nur objektiv gegebene Tatsachen aufzuzeigen und durch ihre kausalen
> Beziehungen zn verstehen bemüht war, versuche ich nunmehr, da ich best
（`zn`／`Wirklichkeitebeschreibung` 为 OCR 讹形，照录未改。）

→ **他不是默默换轨，是把换轨这个动作本身写出来给读者看。**
这一段的功能不是表达感受，是**给读者一个方位标**：从这里起，说的不再是「是什么」而是「该是什么」。

★ 这是本工作区里**唯一一处**他明写自己在方法上的位置移动，价值在于它是可核的一句原话，
不是我从他的学说反推出来的性格。

### 2. 第一人称的形态是**「宣告下一步」，不是「讲自己」**

`src-bfbcf301361b` 12 处真声口（见 §「量法」），形态只有三类，逐字各举一条：

- **明说不追某条线**：
> Ich möchte hier nicht untersuchen, ob es einem Lehrer, der die
> tatsächlichen Verhältnisse des modernen Staates kennt, und der seine Schüler nicht betr
- **落一个第一人称判断**：
> Ich halte es nicht für einen Zufall, daß in dem Lande des
> intensivsten politischen Lebens die meisten Spielhöllen zu finden sind, und daß die Nation,
- **回指本文前面某处**：
> die ich sooben über politische oder unpolitische Weltanschauung
> entwickelt habe

  （`sooben` 为 OCR 讹形，照录未改。）

→ **一处生平、一处轶事、一处情绪都没有。** 他的「我」全部用来管理论证的走向。
下游出 `voice` 类用例时要按这个形态出，**不能指望他讲自己**。

### 3. 起手一律**先把对方或通说完整摆出来，再动手**

两份不同刊物、隔八年，开篇同形：

- `src-ccb348b4687c`（1914，驳 Ehrlich）：
> Wenn einer der Führer und Begründer der neuestens
> immer stärker vordringenden sogenannten »soziologischen« Rechtswissenschaft mit einem großen
> Werke vor die Oeffentlichkeit tritt, dessen Titel ankündigt, die Grundlegung dieser neuen
> Wissenschaft zu geben, so hat man alle Ursache, an solches Unterneh
- `src-f7ad7280693a`（1922）：
> Daß Staat und Recht zwei verschiedene Wesenheiten seien, kann als
> die herrschende Lehrmeinung aller mit diesen Gegenständen be faßten Wissenschaften angesehen
> werden.

  （`be faßten` 为 OCR 折断，照录未改。）

→ **他从不先亮自己的结论。** 第一段的位置永远留给「现在大家怎么说」，
自己的动作放在读者已经看清对方立场之后。

★★ 这是 01 道 K1（「立论前先证明现有用法已失去确定含义，再重建定义」）请求的**第二簇**——
01 道的两条证据在 `writings`（1920 两件），本道这两条在 `expression`（1914／1922），
**四件跨两道、跨十二年、跨四家刊物**。

### 4. 1922 那篇**一个 `ich` 都没有，5 处 `wir` 全是「认识着的我们」**

`src-f7ad7280693a` 严格 `ich` = **0**，`wir` = 5。五处全在同一种用法里，逐字：

> Des Eigensinns, der Eigengesetzlichkeit jenes besonderen Gegenstandes, den wir „Staat‘‘
> nennen und zum Objekt einer eigenen Wissenschaft gemacht haben, können wir uns nicht
> bemächtigen, wenn wir unsere Betrachtung auf irgendwelche seelische Prozesse des Denkens
> und Wollens, sondern nur, wenn wir unsere Erkenntnis auf ein spezifi

→ 不是编辑性「我们」（谦称的自指），是**把读者拉进认识行为里的「我们」**：
「我们称之为国家的那个对象」「我们把认识指向……才能……」。
**同一个人、同一道、隔四年，从 14.11 的「我」切到 0 的「我」＋ 认识论的「我们」。**

## ★ 量法（两处我自己先量错了，写在这里免得下游重犯）

### 4-1 `ich` 不能大小写不敏感地数——德语名词 `das Ich` 会混进来

`src-bfbcf301361b` 25 处命中里 **13 处是名词**（`Ich-Bewußtsein`、`Ich und Welt`、
`das Faktum Ich`、`dem individualistischen Ich`）——**那一篇正好在论个人主义与集体主义，
满篇都在把「自我」当研究对象谈**。台账 `04-` 原记 29.39／万词，更正后 **14.11**。

| 件 | 命中 | 其中名词 | **真声口**／万词 |
|---|---|---|---|
| `src-ccb348b4687c` 1914 | 6 | 0 | 3.68 |
| `src-c78fac5e78b4` 1916（禁引） | 14 | 0 | 6.96 |
| `src-bfbcf301361b` 1918 | 25 | **13** | **14.11** |
| `src-f7ad7280693a` 1922 | 0 | 0 | **0.00** |
| `src-31c509a0e332` 1926（法语） | 1 | 1 | 0.00 |

可重跑（自测 6 条）：

    python3 _tools/measure3_register.py

### 4-2 自引不能数裸 `mein*`——德语 `meinen`／`meint`／`Meinung` 是「以为／意见」

`src-ccb348b4687c` 裸 `mein*` 25 处，**严格自引只有 2 处**；其余多数是
`Ehrlich meint …`／`Er meint offenbar …`——**说的是对手在想什么，不是他在引自己**。

| 件 | 裸 `mein*` | **严格自引** | 严格／万词 |
|---|---|---|---|
| 1914 | 25 | **2** | 1.25 |
| 1918 | 7 | 2 | 2.39 |
| 1922 | 5 | **0** | 0.00 |
| 1925（`writings` 道） | 175 | 59 | 2.47 |

★ 1925 那件严格值 **2.47** 与 01 道独立量到的 **2.42** 相合，两道用的是同一条判据。
★★ 1914 的两处自引之一是 `meine Hauptprobleme der Staatsrechtslehre, Tübingen 1911, $, 3 ff.`
——**01 道说本机取不到的那部 1911 年大书，在这里被他自己按页码引用**。
材料取不到，而「它存在且是他的」有一手证据。

## Candidate Claims

- **K4（work-method）**：跨越「是」与「应当」时明写自己正在跨。证据：本道第 1 条（单源单处）。
- **K5（expression-pattern）**：第一人称只用于管理论证走向（宣告不追／落判断／回指本文），
  不用于自述。证据：本道第 2 条（1918 的 12 处真声口全部归入三类）。
- **K6（expression-pattern）**：开篇位置留给通说或对手，自己的动作放在其后。
  证据：本道第 3 条（1914／1922）＋ 01 道 K1（1920 两件）——**跨两道四件**。
- **K7（fact）**：同一道内声口密度从 14.11 摆到 0.00，且 0 的那篇改用认识论的「我们」。
  证据：本道第 4 条 + §4-1 表。

## Contradictions and alternative explanations

- 第 3 条的「先摆通说」**可能是德语法学论战文的通用体例**，不是他个人特征。
  1914 载于 *Archiv für Sozialwissenschaft*、1922 载于 *Kölner Vierteljahrshefte*，
  两者都有书评／论战体例。**本工作区没有同代其他法学家的文本，分不开。**
  ★ 与 01 道记的同一条保留意见一致——**两道各自独立撞到同一个分不开的地方，不是互相抄的**。
- 第 4 条的 `ich` = 0 **要连样本量一起看**：该篇仅 7,322 词，
  按本批干净德语件的合并声口率（约 3.4／万词）期望值只有 **2.5** 次，
  观察到 0 次并不罕见。⇒ **可以说「这一篇没出现 ich」，不能说「他在这一篇刻意不用 ich」。**
- 第 1 条只有**一处**证据。它是一句很强的原话，但**单处不足以立成习惯**；
  1916 那份声口第二高的件禁引，本来最可能提供第二处的就是它。

## Unknowns and source gaps

- **本道声口密度第二高的一份（1916，6.96／万词）一句都引不出来**——禁引。
  它是《Norm- oder Kulturwissenschaft》，正是方法论论战，**最可能重复第 1 条那个动作的地方**。
- 法语那件（1926）体量最大（38,342 词）而按指令不作声口证据。
  它的 `nous` 密度是全批最高，**这条指令的代价已写在 `04-` 台账 §3-3**。
- 三件 *Erwiderung*（论战答辩）本机取不到 PD 全文——探测报告预期它们的声口最高。

## Proposed Holdout cases

IDs only; research Agents must not inspect Holdout bodies.

## Handoff to adjudication

- K6 已有跨道第二簇（本道 + 01 道），**可进多源类别**。
- K4 单源单处、K5 单源，**都要 02／04 道或后续材料补第二簇**；补不到就只能记 `status: hypothesis`。
- K7 是事实陈述，单道成立，但**必须连「0 的那篇样本只有 7,322 词」一起交下游**。
