# Writings

## Scope and assigned sources

**本道分到 2 份（train split）**：

| source_id | 出版年 | tier | 题名 |
|---|---|---|---|
| `src-65463ac971fb` | 1810 | P1 | The high price of bullion : a proof of the depreciation of bank notes |
| `src-223af918b1a2` | 1821 | P1 | On the principles of political economy and taxation. |

★ 本节由台账机械导出（`emit_lane_scope.py`），**不含任何阅读判断**；只投影 `split == train` 的行。

## 三条实测发现（逐份）

### ① 《On the Principles of Political Economy, and Taxation》（1821 三版）——以「劳动量定价值、分配定去向」的演绎体系
`src-223af918b1a2` 第三版在序言里先立总纲：地租、利润、工资三者的分配规律是政治经济学的首要问题（原文 OCR 讹形较重，改述：`To determine the laws which regulate this distribution, is the principal problem in Political Economy` 一句中 `tjiis`/`prQblem`/`Po-Htieal` 为讹形），并点名 Malthus 1815 年与 Oxford Fellow 同时提出「地租真义」之后，税收研究才成为可能。ADVERTISEMENT（署 1821-03-26）交代三版新增：第一章「Value」加写、新增 Machinery 章、重审 Say 的 Value and Riches、末章论证「即使一国商品货币价值总量下降，仍可负担新增货币税」——即自由贸易进口谷物可压低工资、维持纳税能力的政策推论。

- **价值论（第一章，Section I）先立定义再推结论**——先划掉「稀缺性」例外，再给劳动量标准：

> Possessing utility, commodities derive their ex- changeable value from two sources: from their scarcity, and from the quantity of labour required to obtain them.
<!-- src-223af918b1a2 -->

（上句 `ex- changeable` 的连字符为排版断行残留，照录。）开篇同段即把「有用性」逐出价值尺度，但承认它是价值的必要条件：

> Utility then is not the measure of exchangeable value, although it is absolutely essential to it.
<!-- src-223af918b1a2 -->

Section III 把「用于商品本身的劳动」扩展到「连同其工具、机器、建筑里凝结的劳动」，得出**劳动节约必降相对价值**（此句原文因跨页被页眉噪音打断，只能改述：劳动使用上的节约必然降低商品的相对价值（OCR 中 `faUs` 即 `fails` 的讹形）；随后用两种商品相对变动来演示「先比一般价格、再查劳动量、把或然变确定」的判据）：

> Two commodities vary in relative value, and we wish to know in which the variation has really taken place.
<!-- src-223af918b1a2 -->

- **地租论（第二章）——「级差地租」与「地租不是成本」**：先给严格定义（只对土地「原始且不可毁灭的能力」付的报酬）：

> Rent is that portion of the produce of the earth, which is paid to the landlord for the use of the original and indestructible powers of the soil.
<!-- src-223af918b1a2 -->

随即用 No.1/2/3 三类土地的 100/90/80 夸特示例演示：人口推进→次等土地被开垦→头等土地开始有租，地租恒等于相邻等级产出之差；同一逻辑也适用于同地加投（1000l. 资本二度投放只得 85 夸特）。核心因果是「地租是价高的结果而非原因」（`Com` 即 `Corn` 的 OCR 形）：

> Com is not high because a rent is paid, but a rent is paid because com is high;
<!-- src-223af918b1a2 -->

> rent invariably proceeds from the emplojrment of an additional quantity of labour
<!-- src-223af918b1a2 -->

（`emplojrment` 即 `employment` 的 OCR 形；句尾「with a propor- tionally less return」因断行连字符未续引。）结论：谷物价格由**不付地租的最差地**上的劳动量决定——边际成本定价；即便地主让渡全部地租，也降不了种谷所需劳动量。

- **工资与价格（第四、五章）——自然价/市场价二分**：价格由劳动量定，但承认市场价的偶然短期偏离，靠资本跨行业流动把利润拉平（此段 OCR `wliich`/`cafHtalist` 讹形较重，故改述）。第五章工资论先定义：

> Labour, like all other things which are purchased and sold, and which may be increased or diminish- ed in quantity, has its natural and its market price.
<!-- src-223af918b1a2 -->

（`diminish- ed` 连字符为断行残留。）自然工资由工人及其家庭「生存并延续种族」所需的食物与必需品价格决定，随社会进步而趋升；市场工资围绕自然工资波动。他对劳动市场干预的态度在第五章末（`coiupetition`=competition、`K^ntroUed`=controlled；前半句「wages should be left to the fair and free competition of the market」跨版口被页眉打断 [版口：102 ON WAGES]，故只引后半）：

> free coiupetition of the market, and should never be K^ntroUed by the interference of the legislature.
<!-- src-223af918b1a2 -->

- **利润（第六章）——工资与利润反向，利润由谷价/工资钉住**（`com`=corn）：

> Supposing com and manufactured goods always to sell at the same price, profits would be high or low in proportion as wages were low or high.
<!-- src-223af918b1a2 -->

配合第一章/第六章「同一劳动量下工人实际份额递减、地主份额量价齐增」的分配结论（Diehl ③ 有对应的德译，见下）。谷物涨价（因更差地进入耕作）抬高工资、压低利润，利润率的长期下降是增长的自然结果。

- **比较优势（第七章）**——先破「对外贸易抬高利润率」论（`ex* tension` 中 `*` 为脚注标记），再立国际分工原则：

> Under a system of perfectly free commerce, each country naturally devotes its capital and labour to such employments as are most beneficial to each. This pursuit of individual advantage is admirably connected with the universal good of the whole.
<!-- src-223af918b1a2 -->

经典数字例：英国产布 100 人·年、自酿葡萄酒要 120 人·年；葡萄牙酿酒仅 80 人·年、织布要 90 人·年——葡萄牙在两种商品上都更有效率，仍应专事酿酒进口英国布，因为：

> Thus England would give the produce of the labour of 100 men, for the produce of the labour of 80.
<!-- src-223af918b1a2 -->

他并解释此种交换「在同国两个体间不可能发生」——资本在一国之内可自由流动、在国家之间几乎不动，这是国与国比较优势的微观基础（第 141 页脚注用「制鞋者与制帽者」的相对优势例证同一原则）。第七章还给出**国际间相对价格不受国内劳动量规则约束**的著名断语（原文 `tlie`/`va* lue`/`regu-` 等讹形与断行较重，改述：同一规则调节一国之内的相对价值，却不调节两国之间所交换商品的相对价值）。

- **税收各章（第八、九章等）——税收归宿与转嫁**：总纲是先分「资本/收入」两渠：

> There are no taxes which have not a tendency to lessen the power to accumulate. All taxes must either fall on capital or revenue.
<!-- src-223af918b1a2 -->

第九章给出生谷物的转嫁结论（`woidd` 即 `would` 的 OCR 形；分号前空格照录）：

> A tax on raw produce would not be paid by the landlord ; it would not be paid by the farmer; but it woidd be paid, in an increased price, by the consumer.
<!-- src-223af918b1a2 -->

即：只要产出价能补偿税负、资本可退出低利行业，税就沿边际成本传导到消费者；地租不是价格构成，故「地主不受生产税」是 Ricardo 税收分析的第一根杠杆。

⇒ 论证方法签名：**先定义→再假设（如"货币价值不变"）→用数字算例做演绎载体（猎人/鹿、渔夫/猎人、No.1/2/3 土地、100/80 人·年）→推可检验命题**；对手（Smith/Say/Malthus/Thornton）的观点先引用再逐条反驳，行文是"我说他对在哪、错在哪"。

### ② 《The High Price of Bullion》（1810 三版）——金块溢价即纸币贬值，恢复可兑换是唯一正解
`src-65463ac971fb` 全书是金块论战的开场檄文：1797 年英格兰银行停止铸币兑付（Bank Restriction）后，金块市价持续高于铸币平价，作者在引言里点名他观察到「贬值被公众否认、或归因于任何原因就不归因于真正的那个」（改述引言首段），并声明要从**公认的政治经济学原理**推出原因。引言的论证目标句：

> proceeding from a su- perabundance in its quantity, and not from any want of confidence in the Bank of England, or from any doubts of their ability to fulfil their engagements.
<!-- src-65463ac971fb -->

（`su- perabundance` 为断行连字符；句中「at a considerable discount」跨版口被页眉打断 [版口：IV INTRODUCTION.]，故只引后半。）方法论先行句（`Be- fore` 为断行连字符）：

> Be- fore any remedy can be successfully applied to an evil of such magnitude, it is essential that there should be no doubt as to its cause.
<!-- src-65463ac971fb -->

- **论证链第一环：贵金属的价值与分布**——金和银同任何商品一样有内在价值，靠稀缺性与获得它们的劳动量决定：

> Gold and silver, like other commodities, have an intrinsic value, which is not arbitrary
<!-- src-65463ac971fb -->

- **论证链第二环：出金的机制**——货币过多→金价上升→金被出口，是调节，不是灾难；且这是"选择而非必需"，政府禁止铸币出口的旧法是无效且有害的：

> The exportation of the coin is caused by its cheapness, and is not the effect, but the cause of an unfavourable balance
<!-- src-65463ac971fb -->

- **论证链第三环：纸币不可兑换后，超发即贬值**（`circu-`/`re-`/`na-` 为断行连字符）：

> a depreciation of the circu- lating medium is the necessary consequence of its re- dundance ; and that in the common state of the na- tional currency this depreciation is counteracted by the exportation of the precious metals.
<!-- src-65463ac971fb -->

- **与 Thornton 的正面论战**：Thornton 把「贸易逆差→汇兑不利→金价升」当因果，作者反过来说——「区分黄金价值的上升与其货币价格的上升」才是正解（改述第 469–471 行）；汇兑的涨落只能反映运输成本的区间，超过该区间必是货币本身的贬值（第 990–1002 行）。对「金块贵了」这句流行说法，他给出全篇最锋利的一句：

> In saying however that gold is at a high price, we are mistaken ; it is not gold,
<!-- src-65463ac971fb -->

（分号前空格照录；此句「it n」与「is paper」之间跨页脚 [版口：( 34 )]，故只引到 `it is not gold` 为止；后半句「is paper which has changed its value」改述。）——不是黄金变贵，是纸币变贱：这是数量论语言的精确化。

- **利率与货币量无关**：反驳「纸币多则利率低」的流行论（这正是日后 Currency vs Banking 学派之争的先声）：

> the rate of interest is not regulated by the abundance or scarcity of money, but by the abundance or scarcity of that part of capital, not consisting of money.
<!-- src-65463ac971fb -->

- **药方：渐进缩量、恢复可兑换（金本位）**——这是全书的落点（`de- crease` 为断行连字符）：

> The remedy which I propose for all the evils in our currency, is that the Bank should gradually de- crease the amount of their notes in circulation until they shall have rendered the remainder of equal value with the coins which they represent
<!-- src-65463ac971fb -->

> The only legitimate security which the public can possess against the indiscretion of the Bank is to oblige them to pay their notes on demand in specie
<!-- src-65463ac971fb -->

> the Bank can never resume their payments in specie, until they first reduce the amount of their notes in circulation to these limits.
<!-- src-65463ac971fb -->

他特别强调恢复兑付必须**渐进**（"in one year or in five"），断言否则只剩「纸币信用彻底垮台」一途；并指出 1797 年停兑本身是政治恐慌所致，与纸币量无关——是 Bank 与政府过密（给政府垫款）才让限制长期化（改述第 2090–2113 行）。结尾自谦（`consider- ation` 为断行连字符）：

> Here I will conclude ; happy if my feeble efforts should awaken the public attention to a due consider- ation of the state of our circulating medium.
<!-- src-65463ac971fb -->

另有一句数量论的极端表述（第 1810 行）：

> The circulation can never be over-full.
<!-- src-65463ac971fb -->

以及「硬币只为清偿超量纸币才会出口」的反重商主义论断（`w hen` 即 `when` 的 OCR 形）：

> Thus then specie will be sent abroad to discharge a debt only w hen it is superabundant ; only when it is the cheapest exportable commodity.
<!-- src-65463ac971fb -->

⇒ 对纸币发行的态度：**可兑换是不可动摇的纪律**；超发→贬值→财富从债权人向债务人的"暴烈而不公的转移"（第 1886–1888 行），是隐蔽的国家违约。对重商主义的态度：贸易差额论把结果当原因，金条贸易逆差不是损失而是把无用之物换成资本。

### ③ 《Sozialwissenschaftliche Erläuterungen zu David Ricardos Grundgesetzen…》（1905，Karl Diehl）——德语学界把 Ricardo 体系读成"工资规律+货币数量论+自由贸易"的评述
`src-1a88ce6c8af5` **不是任务标注的 1877 年德译本**，而是德国经济学教授 Karl Diehl（柯尼斯堡大学）所著、Wilhelm Engelmann 1905 年出版的《对 David Ricardo〈国民经济学与赋税基本原理〉的社会科学评注》第 II 卷（第二版）。其目录分九章：第三至九章依次为**劳动工资论（Lohntheorie）、利息与企业利润、货币理论（Geldtheorie，含 High Price of Bullion 与 Proposals 专节）、对外贸易政策（auswärtige Handelspolitik）、危机/生产过剩/机器观、税收学说（Steuerlehre）、对 Ricardo 的总评与社会科学方法论**，另附 Ricardo 书目与 Person-/Sachregister——即它按评注体组织、与《原理》后部章节（Ch IV 至 Ch XVIII）一一对应，价值/地租章应在语料外的第 I 卷。故本道对 ③ 只核其**章节结构**与**转引 Ricardo 的德译语句**，引文属性一律标为「Diehl 转写」，不作 Ricardo 英文原词使用。

- **它把 Ricardo 的工资论框架化为「铁的工资规律」**（Diehl 本人随后引拉斯萨勒对其的批判，`Gotha`/`Bourgeois-Ökonomie`/`agitatorisch` 等词显示这是 19 世纪末德国工人运动语境的标签，不是 Ricardo 原词）——Diehl 的概括句是：

> So ist ihm die Bevölkerungsbewegung der große Regulator der Löhne: die letzte Ursache, warum die Löhne nie auf die Dauer ein gewisses Durchschnittsmaß übersteigen.
<!-- src-1a88ce6c8af5 -->

（改述为中文即：人口运动是工资的大调节器，是工资长期不能超过某个平均水平的最终原因。）同一节里 Diehl 转引 Ricardo《原理》论税收与工资的德译（三部分成分配；`yfias` 即 `Das`、`iiir`/`fiir` 即 `für`、`zerfallt` 即 `zerfällt` 的 OCR 讹形）：

> yfias ganze Erzeugnis des Bodens und der Arbeit jedes Landes zerfallt in drei Teile: von diesen ist ein Teil fiir Löhne, einer iiir Profite und einer iiir Renten bestimmt
<!-- src-1a88ce6c8af5 -->

- **转引的德译与英文版逐句对应，可作交叉核验**：Diehl 引 Ricardo 论工资—谷价的反向分配（`femer` 即 `ferner`、`Anteüs` 即 `Anteils` 的 OCR 形；句中被脚注标记 `» Princ. 96 (135)` 截断，故只引到 `vermindert` 为止）：

> Wir haben femer auch gezeigt, daß, obgleich der Tauschwert des Anteüs des Arbeiters infolge des hohen Preises der Nahrungs- mittel vermehrt wird, sein tatsächlicher Anteil vermindert
<!-- src-1a88ce6c8af5 -->

与英文 Principles 第六章「although the value of the labourer's portion will be increased by the high value of food, his real share will be diminished; whilst that of the landlord…」完全同义（原文见 `src-223af918b1a2`，因 `dimin- ished` 断行未逐字引）。Diehl 转引 Ricardo 论劳动市场自由竞争（与英文 `wages should be left to the fair and free competition of the market` 一一对应；`Gesetz- gebung` 为断行连字符）：

> Gleich allen anderen Verträgen sollte der Arbeitslohn dem gerechten und freien Wettbewerbe (fair and free competition) des Marktes überlassen bleiben, und niemals durch Einmischung der Gesetz- gebung beaufsichtigt werden
<!-- src-1a88ce6c8af5 -->

- **Diehl 对 Ricardo 利润/工资边界的转写**（`ver-` 为断行连字符；即「利润不可能吞掉太多而让工人活不下去」，对应英文 Ch XVI）：

> der Gewinn könne nie so viel ver- schlingen, daß nicht genug übrig bliebe, „um die Arbeiter mit den unumgänglich nötigen Lebensbedürfnissen (absolute neces- saries) zu versorgen
<!-- src-1a88ce6c8af5 -->

- **Diehl 转引 Ricardo 论人口原则压住工资**（句中 `"` 为混入的 OCR 噪音、`^^^kung` 即 `Wirkung`、`fiir` 即 `für`；Diehl 标出处为《原理》论生原料税章）：

> Wegen der "^^^kung des Bevölkerungsprinzips auf die Vermehrung der Menschheit bleiben die Löhne der niedrig- sten Art niemals hoch über dem Satze, den Natur und Ge- wohnheit fiir den Unterhalt der Arbeiter erfordern.
<!-- src-1a88ce6c8af5 -->

⇒ ③ 的独立价值：它是**一手英文与德语二手转写之间的对译校验网**——凡 Diehl 转引处都能在 ① 找到同义英文句（本例已对通三处：分配三部分、劳动份额递减、劳动市场自由竞争），也确认德语学界到 1905 年仍把 Ricardo 读成「工资铁律 + 货币数量论 + 自由贸易」的三件套。

## 这一道给下游的东西

- **论证方法签名（跨三份一致）**：先定义→假设（货币价值不变等）→数字算例演绎→可检验命题→指名反驳对手。Bullion 里甚至把对手 Thornton 的观点整段引出再倒转因果；Principles 里对 Smith/Say/Malthus 同法。
- **核心理论签名（可独立成链）**：① 劳动价值论（含"凝结劳动+工具劳动"）与**边际成本定价**（最不利生产条件决定价格，租/税都不进价）；② 级差地租=质量差，地租是价果非价因；③ 工资-利润反向、利润率长期下降（增长悲剧面）；④ 比较优势（绝对劣势国仍可从贸易获益）；⑤ 货币数量论 + 金本位纪律。
- **对重商主义的态度**：反贸易差额论（逆差是结果不是原因、金条出口是资产置换），主张自由贸易（含进口谷物压工资→保利润→保纳税能力，见三版 ADVERTISEMENT）。
- **对纸币发行的态度**：可兑换是唯一合法安全阀；超发=隐蔽违约=「暴烈而不公」的财产转移；恢复须渐进。这条可与 05-decisions 道（议会议案、金块委员会、银行宪章）直接衔接。
- **政策锋芒**：反对济贫法与立法干预劳动市场（"应留给市场公平自由竞争"）、主张废除禁金出口旧法；但反干预只限于"个人自由+市场纪律"，政府仍有固定纳税义务的道德责任——注意他不反税，反的是转嫁错位。
- **归属红线**：③ 是 Karl Diehl 的**评述著作**（1905），其内文引文是德文转写，不可当作 Ricardo 英文原词；只能作 ① 的交叉核验与"德语接受史"旁证。任务元数据「1877 德译 Principles」与语料实况不符，已按语料纠正，勿沿用旧标注。

## 未做完 / 未核

- **① 元数据纠错（最高优先）**：任务标注 `src-1a88ce6c8af5` 为「1877 德译 Principles」；语料标题页实为 Karl Diehl 1905 年《Sozialwissenschaftliche Erläuterungen zu David Ricardos Grundgesetzen…》II. Teil 第二版（Leipzig, Wilhelm Engelmann）。**本语料内未见到 1877 年德译本正文**；下游若需德译 Principles 请另寻可靠译本的扫描件，不要引用本文件为「德译本」。
- **Principles 未整本通读**：精读序言/ADVERTISEMENT、第一、二、四、五、六、七、八、九章核心段；第三（矿山地租）、第十至十八（各税种）、第十九至三十二（贸易渠道剧变、价值与财富、货币与银行、机器、Malthus 论地租等）仅核目录未精读。
- **Bullion 整本通读毕**（2180 行）。
- **Diehl 仅读**：标题页、目录、工资/利润/货币/贸易各节抽样约 150 行；未读全书各 "Kritik" 节与书目附录。
- **引文坐标粒度**：本道坐标到 source_id 级；可标 Ch/Section（Principles ①可标 Ch.I/II/IV/V/VI/VII/VIII/IX，Bullion ②可按页 3–56），页码 OCR 不可靠，未逐一核。
- **OCR 噪音**：三份均含大量 19 世纪初 OCR 讹形与断行连字符（`ex- changeable`、`diminish- ed`、`Com`=Corn、`emplojrment`=employment、`coiupetition`=competition、`K^ntroUed`=controlled、`woidd`=would、`w hen`=when、`yfias`=Das、`iiir`=für、`^^^kung`=Wirkung、`Anteüs`=Anteils、`femer`=ferner 等），引文全部照录并逐条 grep 回验通过；跨页被页眉/脚注打断处（Principles `102 ON WAGES`、Bullion `IV INTRODUCTION.` 与 `( 34 )`、Diehl `Princ. 96 (135)`）已用 [版口：…] 标注或只引连续片段。
