# Writings and systematic works

## Scope and assigned sources

**本道分到 12 份（train split）**：

| source_id | 出版年 | tier | 题名 |
|---|---|---|---|
| `src-6c85055b8605` | 1618 | P1 | Mare Liberum, sive De iure quod Batavis competit ad Indicana commercia |
| `src-238b4a9f8cb9` | 1646 | P1 | De Jure Belli ac Pacis Libri Tres（拉丁） |
| `src-f4df79764828` | 1658 | P1 | Annales et Historiae de Rebus Belgicis |
| `src-667bd84bb386` | 1682 | P1 | The most excellent Hugo Grotius his three books treating of the rights of war & peace |
| `src-6de33e4db80d` | 1751 | P1 | Traité du Pouvoir du Magistrat Politique sur les choses sa…marum potestatum circa sacra） |
| `src-03c6588cea95` | 1853 | P1 | Grotius on the Rights of War and Peace: An Abridged Translation |
| `src-576d609b0ef0` | 1853 | P1 | Hugonis Grotii De Jure Belli et Pacis Libri Tres, accompan…am Whewell — Volume the Third |
| `src-8651f2b87336` | 1853 | P1 | Hugonis Grotii De Jure Belli et Pacis Libri Tres, accompan…am Whewell — Volume the First |
| `src-d3bf3e7d3c8f` | 1853 | P1 | Hugonis Grotii De Jure Belli et Pacis Libri Tres, accompan…m Whewell — Volume the Second |
| `src-19eca701ec61` | 1869 | P1 | Hugonis Grotii De Jure Praedae Commentarius (Le Droit de Prise) |
| `src-52fd74630d7b` | 1916 | P1 | The Freedom of the Seas, or The Right which Belongs to the…Part in the East Indian Trade |
| `src-2808cba204dc` | 1925 | P1 | De Jure Belli ac Pacis Libri Tres, Vol. II — The Translation（含 Prolegomena） |

★ 本节由台账机械导出（`emit_lane_scope.py`），**不含任何阅读判断**；只投影 `split == train` 的行。

## Source-linked observations

> **引文口径（先说清楚，后面每条都按这个来）**
> 本道语料全是 OCR。引文一律**照录 OCR 原样**，讹字在引文**外**用 `＝` 标出正形，
> 绝不在引文内替作者改字（[[verbatim-is-not-understood]]）。
> 坐标用 `source_id @字符偏移`，可用 `corpus_body()` 读回复核。
> ★ 逐字可引性实测见工作区根目录 `00-密封改判.md` 文末：本道 12 份里
> **ae 连字与长 s 都完好的只有 `src-19eca701ec61` 一份**；
> `src-8651f2b87336/d3bf/576d`（1853 拉丁三卷）长 s 干净而 **ae 被打散**，
> 从它们取的引文里 `que` 实为 `quae`、`hee` 实为 `haec`。

### 一、★★ 他写论证的单位是**编号的法则**，不是段落

`src-19eca701ec61` @49923，第二章正文里，他先说「由此涌出**两条**自然法的法则」，
然后**当场给它们编号并逐条陈述**：

> `liceat *. Altéra : Ux IL Adjungere sibi quae ad viyendum sunt utilia eaque retinere`
> `liceat; quod quidem cum TuUio ' ita interpretabimur`

（`Ux IL`＝`Lex II`、`viyendum`＝`vivendum`、`TuUio`＝`Tullio`。
前一句 @49875 是 `Lex L Prior : Vitam tutri et declinare nocitura liceat`，`tutri`＝`tueri`。）

编号一路排到十二条，中间不换体例。同一份里可直接读到：

> `occupet alteri occupât a. Haec lex absdnen* tiae , illa innocentiae est : inde vitae`
> `sccuritas oritur , hinc do- miniorum dîstinctîo`

（@56880；`absdnen* tiae`＝`abstinentiae`、`sccuritas`＝`securitas`、`do- miniorum`＝`dominiorum`。）

> `Lex X, raandati naturaliter insunt, hic etiam reperiuntur, una: Ut Ux XL magistratus`
> `omnia gerat e bono reipublicae^ altéra: Ut quid- quid magistratus gessit respublica ratum`

（@83021；`raandati`＝`mandati`、`Ux XL`＝`Lex XI`。）

> `Lexxii. alteriusye ciyem jus suum nisi judicio exsequatur. Cuius quidem legis nécessitas`
> `per se perspicua est`

（@86332；`Lexxii.`＝`Lex XII`、`alteriusye ciyem`＝`alteriusve civem`。）

**每条法则都是一个可以单独引用、单独反驳的命题**——先编号、再陈述、再往下推。
这不是文体偏好：后半部把一桩具体的拿捕案放进这套编号里逐条对照，
**论证的可检验性来自编号本身。**

### 二、每立一条，他紧接着搬一个**古人**来担保

同一段落里，法则陈述之后立刻接的是引证，而不是补充论证：

> `quod quidem cum TuUio ' ita interpretabimur`（@49990，`TuUio`＝`Tullio`，即 Cicero）

> `i et atterius , quorum ille cupidinis , hic amicitiae dicitur ^. Hujus autem aliqua etiam`
> `in rébus inanimis species obs`（@52060，`atterius`＝`alterius`；上文即引 Seneca）

**次序是固定的：先给命题，再给一个读者已经承认的权威，然后才往下推。**
★ 这一条只说「他这么排」，**不说他的引证对不对**——引证是否忠于原书，本道不判。

### 三、★★★ 他明说这套推理**即使拿掉神也站得住**

`src-8651f2b87336` @83355（DJBP 卷一，页眉 `xlvi PROLEGOMENA`）：

> `nequit, non esse Deum, aut non curari ab eo negotia humana: cujus contrarium cum nobis`
> `partim ratio, partim traditio perpetua inseverint`

（`ssculis`＝`saeculis`。前半句在 @83307，**照录原样含折行与杂符**：
`Et hee quidem que jam diximus, locum aliquem ha- berent, etiamsi daremus, ! quod sine summo scelere dari nequit`
——`hee`＝`haec`、`que`＝`quae`、`ha- berent`＝`haberent`，`!` 是版面杂符。）

> ★★ 这一条我第一次是**凭理解重打**的（把 `ha- berent` 接成 `haberent`、去掉 `!`），
> `check_lane_quotes_verbatim` 当场报「15 条里 1 条对不上」。
> **而我在本节开头刚写下「引文一律照录 OCR 原样」**——写下规矩不等于照着做，
> 是判据把它抓出来的。

即：**「我们刚才说的这些，纵使我们承认——那是不容承认的大罪——并无上帝，
或上帝不理会人间事，也仍然站得住。」**

★ 他没有停在这句上：**紧接着自己把这个让步收回**
（`cujus contrarium … inseverint`），并补上理由与见证。
**让步是方法论的，不是主张。** 读这段时若只取前半句，会把他读成他明确否认的立场。

### ★ 本节没做什么

- 只读了本道 12 份里的 2 份（`src-19eca701ec61`、`src-8651f2b87336`）。
  其余 10 份**尚未读**，不是「读过没发现」。
- 三条观察都只是**形态**（他怎么排论证），**没有一条是关于他主张了什么**。
  实体主张要等其余各份读完再提。

## Candidate Claims

Pending.

## Contradictions and alternative explanations

Pending.

## Unknowns and source gaps

Pending.

## Proposed Holdout cases

IDs only; research Agents must not inspect Holdout bodies.

## Handoff to adjudication

Pending.
