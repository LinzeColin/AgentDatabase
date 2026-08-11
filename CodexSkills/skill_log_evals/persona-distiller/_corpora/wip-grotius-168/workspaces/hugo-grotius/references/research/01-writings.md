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

### 八、★★★ 换了体裁，架构就换掉了：史书里**一卷＝一年**，不是一卷＝一个判准

`src-f4df79764828`（*Annales et Historiae de Rebus Belgicis*，1658）卷末索引，
每卷条目以「卷号 + 年」起头：

> `LIBER XI, Anno 1602. Obfidii Oftendani conti`（@1634323）

> `LIBER XII. Anno 1S03, Elifabetha moritur. .`（@1635697）

> `LIBER XIII. Auno 1504. Badlniacus.juiru Albert`（@1637508）

> `LIBER XV. Anno 1606. Spioola a Philippo jvg`（@1641104）

> `LIBER XVIII. Anno 1S09. gelandi ceterarum pr`（@1653237）

**一卷＝一年，顺次排下去**：XI=1602、XII=1603、XIII=1604、XIV=1605、XV=1606、
XVII=1608、XVIII=1609。

★★ 讹形是**靠序列的算术定死的，不是猜的**：`1S03`／`1504`／`1390` 单看都可读成
1503／1504／1390，而连续卷对连续年这条约束只允许一种解——
1603／1604／1590。（同一手法见 [[verbatim-is-not-understood]]：
在同一份文件里找同构的结构来定标。）

**与前四条观察的对比是本条的全部要点**：
法学著作里组织单位是**判准**（编号公理／穷举名分／专章反驳），
史书里组织单位是**年份**。→ **C-01 有体裁边界**，见 C-01 的射程栏。

### ★ 我先说错了一次，是自己数出来的

第一眼看到索引里满是 `Anno`，我写下「正文按编年组织」。
去数：全书 `Anno` 共 **45 处，其中 40 处在索引区、正文只有 5 处**
（密度对照：DJBP 1646 是 6 处/258 万字符、De Iure Praedae 6 处/77 万字符——
Annales 高 2.7–9 倍，但绝对量都太小）。
→ **「正文按编年组织」这个说法拿不出证据**，已改成只讲索引层能立住的部分。

### ★ 本节没做什么

- 只读了本道 12 份里的 **6 份**（`src-19eca701ec61`、`src-8651f2b87336`、
  `src-52fd74630d7b`、`src-2808cba204dc`、`src-6de33e4db80d`、`src-f4df79764828`），
  且后四份只读了章题／索引／开篇。其余 6 份**尚未读**，不是「读过没发现」。
- 八条观察全是**形态**（他怎么排论证、怎么立项），
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
- **射程**：**四部法学作品**（De Iure Praedae 编号公理／Mare Liberum 穷举反证六章／
  DJBP 三卷 57 章 286 处编号小节／De imperio 专章反驳），四种版面实现同一形状。
  ★ 但 Mare Liberum 与 De Iure Praedae **是同一部作品的整体与被单刊的一章**
  （台账已声明），所以严格说是**三处独立证据**，不是四处。
- ★★ **体裁边界（观察八）**：同一个人写史书时**不用这个形状**——
  *Annales* 的组织单位是年份（一卷＝一年，XI=1602…XVIII=1609）。
  **C-01 只在他做规范性论证时成立**，不是他的通用写法。

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

### X-01 `etiamsi daremus` 那句：**同一段里他自己给了相反的两半**

观察三的两半在语料里紧挨着：

- 前半（@83307）：这些结论「纵使我们承认并无上帝……也仍然站得住」。
- 后半（@83355）：`cujus contrarium cum nobis partim ratio, partim traditio perpetua inseverint`
  ——「而与之相反的（即上帝存在且理会人事），理性与不断的传统已植入我们心中」。

**两种读法都能从这一段取到证据**：
① 他在做一个**方法论上的独立性声明**（论证不依赖神学前提）；
② 他在做一个**修辞上的让步**，随即收回，本意反而是强调神学根基。

★ **本道不裁**。裁它需要读他在同一部书别处怎么用这个前提，
而本道分到的 12 份里**没有一份是护教／神学体裁**——
所以这条**在本道的材料范围内无法解决**，要留给判读方。

**对产物的直接约束**：凡涉及这句，产物必须**把两半一起给**，
不得只引前半句。→ 已写进 C-03。

### X-02 「他不用这个形状」与「这份语料看不见它」分不开

观察八说史书里组织单位是年份。**替代解释**：*Annales* 讹字率 0.9748，
正文里的边注／小标题很可能已被 OCR 抹掉——
**「他没这么写」与「我看不见他这么写」在这份语料上无法区分**。

★ 目前只能说：**索引层能立住的是年份编排**；正文层**未核**。
要裁需要一份可读的 *Annales*（1800–1930 拉丁重排本
按 `00-重OCR报告.md` 检索 `numFound=0`，**目前不存在**）。

### X-03 四部作品「同一形状」有一个共同的可疑来源：**它们都是论战文本**

De Iure Praedae 是为拿捕案辩护、Mare Liberum 是驳葡萄牙、
De imperio 是介入教会与政权之争、DJBP 写在三十年战争中。
**「判准先行、反例后撞」也可能不是他的思维习惯，而是论战文体的通用要求。**

★ 要分开这两者，需要一份**非论战性**的规范性文本作对照。
本道 12 份里**没有**这样一份（Annales 是史书，不是规范性论证）。
→ 这条写进 Unknowns，不写进 Candidate Claims。

## Unknowns and source gaps

### 未读的部分（**不是「读过没发现」**）

本道 12 份里读过 6 份，而其中 4 份只读了章题／索引／开篇：

| source_id | 读到什么程度 |
|---|---|
| `src-19eca701ec61` De Iure Praedae 1869 | 第二章法则段、目录、三处按编号回引 |
| `src-8651f2b87336` DJBP 1853 拉 vol1 | Prolegomena 一段 |
| `src-52fd74630d7b` Mare Liberum 1916 | **仅章题** |
| `src-2808cba204dc` DJBP Kelsey 1925 | **仅 Prolegomena 开头约 1,100 字符** |
| `src-6de33e4db80d` De imperio 1751 法 | **仅章题 + 一句接榫句** |
| `src-f4df79764828` Annales 1658 | **仅卷末索引** |
| 其余 **6 份** | **完全未读** |

### 语料本身的硬缺口

1. **逐字拉丁引文只有一个来源**：本道 12 份里 ae 连字与长 s 都完好的只有
   `src-19eca701ec61`。DJBP 的拉丁正文（1853 三卷）**ae 被打散**，
   1646 初版长 s 讹字率 0.9554。→ **他最重要那部书的拉丁原文，一句都引不了。**
2. **`Annales` 正文不可读**（0.9748），且 1800–1930 无拉丁重排本
   （`00-重OCR报告.md` 实测 `numFound=0`）→ X-02 结构性无解。
3. **没有非论战性的规范性文本**（X-03），四部作品的「共同形状」
   分不清是他的思维习惯还是论战文体的要求。

### 需要别的道来答的

- **他自己怎么描述自己的方法**——本道只看到成品结构，没看到自述。
  书信道（`02-conversations`）可能有，但那三份讹字率 0.9544–0.9777，
  **取不出逐字证据**。
- **同时代人怎么评价他的方法**——外部道（`04-external`）有 De Laet 与 Selden 两位论敌，
  但同样不可逐字引；唯一干净的是 1826 年的二手传记。

### 已知会误导下游的两处

- **X-01**：`etiamsi daremus` 只引前半句会把他读成他明确否认的立场。
- **De imperio 的第一人称是 1751 年译者的法文**，不是他的措辞；
  Poemata 卷末 4.2%（@735866 起）是别人写他的。
  → 两处都不得用于「他的声口」。

## Proposed Holdout cases

IDs only; research Agents must not inspect Holdout bodies.

## Handoff to adjudication

Pending.
