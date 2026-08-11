# Writings and systematic works

## Scope and assigned sources

**本道分到 4 份（train split）**：

| source_id | 出版年 | tier | 题名 |
|---|---|---|---|
| `src-0fc9f0c6b3e0` | 1920 | P1 | Sozialismus und Staat |
| `src-5be5faaef4d3` | 1920 | P1 | Vom Wesen und Wert der Demokratie |
| `src-eb08f86eb37d` | 1925 | P1 | Allgemeine Staatslehre |
| `src-a0e86f4a1b24` | 1928 | P1 | Das Problem der Souveränität und die Theorie des Völkerrechts（2. Aufl.） |

★ 本节由台账机械导出（`emit_lane_scope.py`），**不含任何阅读判断**；只投影 `split == train` 的行。

## ★★ 本道先说清楚一件事：四份里有一份**一句逐字都不许引**

`src-a0e86f4a1b24`（*Das Problem der Souveränität*，1928，320 页）实测：
**h→b 讹变 28.6%**（`nicht`/`nicbt` = 817/353）、**变音符 0.0/千词**（本批干净德语件是 69.9–123.4）。
它是 **Antiqua 排印**，长 s 讹字率恰好 **0.0000**——**只按长 s 那把尺子必然放行**。

→ 本道**引用它作为材料的存在与体量**，但**不从它取任何逐字串**。
与 #169 Blackstone 同型（可引面与可证面不重合），只是这里只塌了一件。

## Source-linked observations

**逐字引文一律照录 OCR，不改讹字**；折行连字符由核验器归一。

### 1. 两件 1920 年的「书」其实是**期刊抽印本**——题名页自己写着

`src-5be5faaef4d3` 题名页逐字：
`Vom Wesen und Wert der Demokratie Von Dr. Hans Kelsen ord. öff. Professor an der Universität Wien
Tübingen Verlag von J. C. B. Mohr (Paul Siebeck) 1920`，
紧接一行：`Separatabdruck aus »Archiv für Sozialwissenschaft und Sozialpolitik« Band 47, Heft i.`
并给出对页表：`Die Seiten 3 — 38 dieses Separatabdruckes entsprechen den Seiten 50 — 85 des Archivs.`

`src-0fc9f0c6b3e0` 起首：`Sozialismus und Staat. Eine Untersuchung der politischen Theorie des Marxismus.
Von Hans Kelsen (Wien).`，其载体页眉显示是 Carl Grünberg 主编的 *Archiv* 抽印。

→ **这两件在编目里像专著，在题名页上是期刊抽印本。** 下游谈「他写了几部书」时必须带这个口径，
否则会把两篇长文数成两部专著。★ [[counts-need-their-cutoff-stated]]

### 2. 他开篇的动作：**先指出一个词已经失去确定含义**

`src-5be5faaef4d3` 正文第一段先描述局面——
`Ein offenes und unumwundenes Bekenntnis zur Auto- kratie ist während der letzten Jahrzehnte
weder bei einem bedeutenden Staatsmanne noch bei einem namhaften Literaten zu verzeichnen`——
随即把这一点翻成问题：`Jahrhundert fast allgemein beherrschende Schlagwort`，
而 `Gerade darum aber verliert es`（`wie jedes Schlagwort`）确定的意义。

→ **他不是先立定义，而是先证明现有的用法已经不成其为定义。**
这与 01 道另一份的起手同形：`src-0fc9f0c6b3e0` 的第一节标题就是
`Das Problem und seine Methode im historischen Materialismus`——**先安置问题与方法，再进入内容**。

### 3. ★ 可量的做法：**把自己的旧作按页码接进当前书**

逐份实测：自引＝第一人称物主代词接「论文／著作／论述／驳论／书／研究」一类名词的每万词频次；
页码引＝德语页码缩写接数字的每万词频次。**两条都是模式计数，不是逐字引文**。

| 件 | 词数 | 自引／万词 | 页码引／万词 |
|---|---|---|---|
| `src-eb08f86eb37d` 1925 | 240,148 | **2.42** | 15.7 |
| `src-5be5faaef4d3` 1920 | 13,096 | **2.29** | 0.8 |
| `src-0fc9f0c6b3e0` 1920 | 41,653 | 0.00 | 15.6 |
| `src-a0e86f4a1b24` 1928（禁引） | 128,850 | 0.47 | **39.2** |

1925 那部书的注中可见成串的自引形态：`meinen Aufsatz: Über Staatsunrecht`、
`meine Schrift: Das Problem der Souveränität und die Theorie des Völkerrechts, S. 21, 147`、
`meine Abhandlung: Das Verhältnis von Recht und Staat im Lichte der Erkenntnis- kritik`、
`Dann meine Gegenschrift: Rechtswissenschaftund Recht, 1922`（`Rechtswissenschaftund` 为 OCR 讹形，照录未改）。

→ **他把自己的著作当成一个可索引的体系在用**：不是重复论点，是给出「这一点我在哪里、第几页展开过」。

★★ **这张表有两处不能读成「他没这么做」**：
`src-0fc9f0c6b3e0` 的自引 0.00 是**该件体裁**（单篇论文，注释体例不同）；
而本工作区另外两件禁引件的 0.00 **是仪器看不见**——它们的实词被 OCR 打碎，
正则匹配不到 `meine …`。[[empty-default-swallows-unknown]]

## Candidate Claims

- **K1（work-method）**：立论前先证明现有用法已失去确定含义，再重建定义。证据：本道第 2 条（两源）。
- **K2（work-method）**：把自己的旧作按篇名＋页码接进当前著作，当作可索引的体系用。证据：第 3 条。
- **K3（fact）**：1920 年那两件在题名页上是期刊抽印本，不是独立专著。证据：第 1 条（两源题名页照录）。

★ 以上都**只有本道一种证据簇**，能不能立住要看 03 道有没有独立的第二簇。

## Contradictions and alternative explanations

- 第 2 条的「先拆词再定义」可能是**德语法学论文的通用体例**，不是他个人特征。
  本工作区没有同代其他法学家的文本，**分不开**。
- 第 3 条的自引密度**受体裁强烈影响**（专著注释多、单篇论文少）；
  在跨体裁比较之前不能说成「他比别人更爱自引」。

## Unknowns and source gaps

- 本道最重要的一件（1928 年那部 320 页专著）**一句逐字都引不出来**，
  只能作为「材料存在、体量多大」的证据。
- *Hauptprobleme der Staatsrechtslehre*（1911，709 页）本机四条通道都取不到，
  而它是他的第一部大书——**本道的时间下沿因此停在 1920，不是 1911**。

## Proposed Holdout cases

IDs only; research Agents must not inspect Holdout bodies.

## Handoff to adjudication

K1／K2 交跨道合流求第二簇；K3 是事实陈述，单道成立。
