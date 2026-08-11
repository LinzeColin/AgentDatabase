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

### 四、★★★ 不只是编号——他**建了一套公理系统，然后按编号引用它推导**

`src-19eca701ec61` 的卷首目录（@24971）把第二章的内容写死了：

> `Prolegomena, in quibus Regulae IX et Leges XIII. CAPUT TER`

即：**九条规则（Regulae IX）＋ 十三条法则（Leges XIII）**，全在第二章里立完。

关键不在「他编了号」，而在**后文按编号回引**。三处：

> `Bellum igitur omne quatuor causarum ex aliqua oriri necesse est. Prima est sui defensio , ex lege prima.`

（@171760：「因此一切战争必起于四因之一。第一是自卫，**出自第一法**。」）

> `Unde bella civilia juste suscipiun- tur secundum regulam quintam sive septimam et legem nonam : extema secundum legem duodecimam et regulam nonam`

（@233615：「故内战之正当依**第五或第七规则与第九法**；外战依**第十二法与第九规则**。」
`extema`＝`externa`。）

> `injustas esse per legem de* cimam tertiam: quod et regulae convincunt unde si`

（@192943：「据**第十三法**为不义；诸规则亦证之——它们正是各法的出处。」
`de* cimam tertiam`＝`decimam tertiam`。）

**这三处不是修辞上的编号，是形式系统的用法**：先立公理，再用「依第 N 条」把
具体结论挂回具体公理。★ 而且他标出了层级——`regulae` 是 `leges` 的出处
（`quod et regulae convincunt unde singulae leges oriuntur`）。

★ 本条只说**结构**：没有核对那 9+13 条是否真的两两一致，
也没有判断哪一条被引对了。**「他这样论证」成立，「他论证得对」未查。**

### 五、★★ 另一部作品里**换了一套装置，方法是同一个**：先立通则，再逐条拆掉对方所有可能的名分

`src-52fd74630d7b`（*Mare Liberum*，Magoffin 1916 拉英对照本）十三章的章题**本身就是论证提纲**：

> `CHAPTER I By the Law of Nations navigation is free to all persons whatsoever`（@49015）

> `CHAPTER II The Portuguese have no right by title of discovery to sovereignty over the East Ind`（@63057）

> `CHAPTER VIII By the Law of Nations trade is free to all persons whatsoever`（@250541）

> `CHAPTER XII The Portuguese prohibition of trade has no foundation in equity`（@276601）

> `CHAPTER XIII The Dutch must maintain their right of trade with the East Indies by pe`（@288040）

排布是：**I 立通则（航行自由）→ II–VII 逐条否掉对方能主张的每一种名分**
（发现、教皇赠与、战争、时效、习惯……）**→ VIII 再立第二条通则（贸易自由）
→ IX–XI 再逐条否掉 → XII 收到衡平 → XIII 落到结论。**

★★ 与观察四对照：De Iure Praedae 用的是**编号公理**，这里用的是**穷举反证**——
**装置不同，形状相同：先把判准摆在台面上，再让每一个反例逐一撞上去。**
→ 这把 C-01 的射程从「一部作品」扩到了两部，**但要改写：
他固定的不是「编号」，是「先立判准、再逐条销案」。**

★ 本条同样只说结构。**没有读章内正文**，也没有核对每一章是否真的做到了它的标题。

### 六、★★★ 开篇第一句就在**划边界**：谁已经做过、谁没做过、我做哪一块

`src-2808cba204dc`（DJBP，Kelsey 1925 英译）Prolegomena 第 1 节（@120282）：

> `I. T'HE municipal law of Rome and of other states has been treated by many, who have undertaken to elucidate it by means of commentaries or to reduce it to a convenient digest. That body of law, however, which is concerned with the mutual relations among states or rulers of states, whether derived from nature, or established by divine ordinances, or having its origin in custom and tacit agree- ment, few have touched upon. Up to the present time no one has treated it in a comprehensive and systematic manner ; yet the welfare of mankind demands that this task be accomplished.`

（`T'HE`＝`THE`、`agree- ment`＝`agreement`，OCR 与折行原样。）

**三步，一句不多**：①「市民法**已有许多人**做过」→
②「而国与国之间那一部分，**少有人触及**」→
③「**至今无人以周全而系统的方式处理它**；而人类的福祉要求此事被完成」。

紧接第 2 节立刻搬权威——**不是为论点担保，是为「这题目值得做」担保**：

> `2. Cicero justly characterized as of surpassing worth a knowledge of treaties of alliance, conventions, and understandings of peoples, kings and foreign nations`

★★ 这是观察二那条「命题 → 权威」的**同一形状用在了立项上**。

★ DJBP 同样是编号的：Prolegomena 分节（I / VI / XIII…），全书 3 卷 57 章、
286 处「罗马数字. 大写起句」的编号小节 → **C-01 的射程扩到第三部作品。**

★ 本条只读了 Prolegomena 开头约 1,100 字符，**正文一章未读**。

### 七、★★ 第四部作品：同一个动作**收进了一个专章**

`src-6de33e4db80d`（*De imperio summarum potestatum circa sacra*，1751 法译本）
十二章，前四章的排布：

> `CHAPITRE I. _Le Pouvoir du Magistrat politique s'étend sur les choses sacrées._`（@5128）

> `CHAPITRE II. _Le pouvoir sur les choses sacrées, & la fonction sacrée sont distincts._`（@35070）

> `CHAPITRE IV. _Solution des objections contre le pouvoir du Magistrat politique sur la Religion._`（@85311）

**I 立通则 → II 先把两个会被混起来的概念分开 → III 划两者的边界 → IV 专章处理反对意见。**

★★ 与 Mare Liberum 对照：那里反例被摊在 II–VII 六章里逐条销案，
**这里收进第 IV 一章**。→ 「反例后撞」这个动作在**第四部作品**上再次出现，
而**它在版面上的实现又换了一种**。

★ 另记一条对 expression／conversations 两道有用的：本份是法译本，**保留了第一人称**——

> `CHAPITRE VIII _De la Législation sur les choses sacrées_. J'ai jusqu'à présent considéré le pouvoir en génér`（@230201）

`J'ai jusqu'à présent considéré`（「我至此考察的是……」）是**章与章之间的接榫句**。
★ 但这是 **1751 年译者的法文**，不是他的拉丁原文——**不得当作他的措辞**。

★ 本条只读了章题与一句接榫句，**正文一章未读**。

### ★ 本节没做什么

- 只读了本道 12 份里的 **5 份**（`src-19eca701ec61`、`src-8651f2b87336`、
  `src-52fd74630d7b`、`src-2808cba204dc`、`src-6de33e4db80d`），
  且后三份只读了章题与开篇。其余 7 份**尚未读**，不是「读过没发现」。
- 七条观察全是**形态**（他怎么排论证、怎么立项），
  **没有一条是关于他主张了什么**。实体主张要等其余各份读完再提。

## Candidate Claims

> 口径：每条候选断言只写**本道观察直接支撑得住**的部分，
> 支撑不住的写进「Unknowns」，不写进这里。
> 每条都标明**它是关于形态的还是关于主张的**——本轮全部是形态。

### C-01（形态）他**先把判准摆在台面上，再让每一个反例逐条撞上去**

- **依据**：
  - `src-19eca701ec61`：观察 一（Lex I…Lex XII 逐条陈述）＋ 观察 四
    （目录 `Regulae IX et Leges XIII`，后文三处按编号回引，并标出 `regulae` 是 `leges` 的出处）。
  - `src-52fd74630d7b`：观察 五（十三章＝立通则 → 逐条销案 → 再立通则 → 再销案 → 收束）。
- **★ 本条第一版写的是「他把规则**编号**立完」——被观察五改写了**：
  Mare Liberum 里没有编号，用的是穷举反证。**固定的不是装置，是次序**：
  判准先行、反例后撞。编号只是他在 De Iure Praedae 用的那一种实现。
- **可检验的形状**：给他一个新案子，他应当**先问判准是什么**，
  再逐一处理对方能提出的每一种名分——而不是先给结论再补理由。
- **射程**：**三部作品**（De Iure Praedae 编号公理／Mare Liberum 穷举反证／
  DJBP 三卷 57 章 286 处编号小节），三种规模同一形状。
  ★ 但 Mare Liberum 与 De Iure Praedae **是同一部作品的整体与被单刊的一章**
  （台账已声明），所以严格说是**两处独立证据**，不是三处。

### C-04（形态）立项时他**先划边界**：谁已经做过、谁没做过、我做哪一块

- **依据**：观察 六（DJBP Prolegomena 第 1 节三步：已有许多人做 → 少有人触及 →
  至今无人系统处理，而人类福祉要求做它；第 2 节立刻用 Cicero 为**题目的价值**担保）。
- **可检验的形状**：问他为什么要做某件事，他应当**先报已有工作的边界**，
  再指出缺口，最后说明这个缺口为什么必须补——而不是直接讲自己的方案。
- **射程**：只在 DJBP 一处核过。
  De Iure Praedae 与 Mare Liberum 的开篇**是否同一形状未查**。

### C-02（形态）他给每条规则配一个**读者已经承认的权威**，位置固定在陈述之后

- **依据**：观察 二（`quod quidem cum TuUio ' ita interpretabimur`；紧接 Seneca 一段）。
- **可检验的形状**：他的论证单元应当是「命题 → 权威 → 推论」，
  而**不是**「权威说了什么，所以……」。
- **射程**：只看了同一段落里的两处。**引证是否忠于原书，本道不判。**

### C-03（形态）他会**主动把最强的让步先说出来，再自己收回**

- **依据**：观察 三（`etiamsi daremus … non esse Deum`，
  紧接 `cujus contrarium cum nobis partim ratio, partim traditio perpetua inseverint`）。
- **可检验的形状**：遇到「你的前提要是不成立呢」，
  他应当**先承认那个假设下结论仍成立**，再说明他本人并不接受那个假设。
- ★ **反面即误读**：只取前半句会把他读成他明确否认的立场——
  这一条同时是**该人物产物的一个已知失真风险**。

### ★ 本轮没有一条是关于「他主张什么」的

三条全是**他怎么论证**。实体主张（战争何时正当、海洋能否占有……）
要等本道其余 10 份读完再提；现在提就是拿两份材料替十二份说话。

## Contradictions and alternative explanations

Pending.

## Unknowns and source gaps

Pending.

## Proposed Holdout cases

IDs only; research Agents must not inspect Holdout bodies.

## Handoff to adjudication

Pending.
