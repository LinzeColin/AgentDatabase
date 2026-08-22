# Writings

## Scope and assigned sources

**本道分到 8 份（train split）**：

| source_id | 出版年 | tier | 题名 |
|---|---|---|---|
| `src-d2dd432e2f00` | 1705 | P1 | Money and trade considered, with a proposal for supplying the nation with money.  1705 |
| `src-4a39617aea24` | 1720 | P1 | A full and impartial account of the Company of Mississipi …riend. In French and English. |
| `src-b88a0f5958dd` | 1750 | P1 | Money and trade considered: with a proposal for supplying …t published at Edinburgh 1705 |
| `src-06814a9eaeb9` | 1790 | P1 | Oeuvres de J. Law, : contrôleur-général des finances des F…t les banques. Avec des notes |
| `src-7ee6554bcc2a` | 1843 | P1 | Économistes financiers du XVIIIe siècle |
| `src-c048d781f923` | 1843 | P1 | Économistes financiers du XVIIIe siècle |
| `src-ce1dbab2c760` | 1843 | P1 | Économistes financiers de 18e siècle : Vauban, Boisquillebert, Jean Law, Melon, Dutot |
| `src-e2af27ed306e` | 1843 | P1 | Économistes financiers du XVIIIe siècle |

★ 本节由台账机械导出（`emit_lane_scope.py`），**不含任何阅读判断**；只投影 `split == train` 的行。

## 五条实测发现（逐份）

### ① 《Money and Trade Considered》（1705 初版）——以供需价值论奠基的货币哲学
`src-d2dd432e2f00` 题名区严重残缺，OCR 把 "AND" 读成 `wa`、把 "Supplying" 读成 `Supljng`、把 "with" 读成 `wth`，逐字照录：

> Money wa Trade
> CONSIDERED,
<!-- src-d2dd432e2f00 -->

> PROPOSAL E, Supljng the NATION
> wth MONEY,
<!-- src-d2dd432e2f00 -->

（OCR 讹形即 `wa`＝and、`PROPOSAL E`＝PROPOSAL for、`Supljng`＝Supplying、`wth`＝with；题名页扫损，正文仍可读。）

- **供需价值论**——开章用水与钻石例，把价值锚定在"数量对需求的比例"，并借以反驳 Locke 的"想象价值"说：

> Example. Water is of great uſe, yet of little Value; Becauſe the Quantity of Water is much greater than the Demand for it. Diamonds are of little uſe, yet of great Value, becauſe the Demand for Diamonds is much greater, than the Quantity ef them.
<!-- src-d2dd432e2f00 -->

（OCR `ef`＝of。）他无法想象不同国家能对一件东西"约定一个想象价值"：

> I cannot conceive how different Nations could agree to put an Imaginary Value upon any thing, eſpecially upon Silver, by which all other Goods are valued ; Or that any one Country would receive that as a Value, which was not valuable equal to what it was given for; Or how that Imaginary Value could have been kept up,
<!-- src-d2dd432e2f00 -->

- **货币的功能定义**：money 是"度量、交换媒介、契约计值标准"三位一体，且明言"不是抵押品"（OCR `|`＝页饰，`ſuppofed`＝ſuppoſed）：

> Money is not a pledge, as ſome call it. Its a Value payed, or Contracted to be payed, with which tis | ſuppofed, the Receiver may, as his occaſions require, Buy an equal Quantity of the ſame Goods he has Sold, or other Goods equal in Value to them:
<!-- src-d2dd432e2f00 -->

- **银行是增币的最优手段**（但他随即警告：银行的信用发行受制于国内存银量，信用过度必致停兑）：

> The uſe of Banks has been the beſt Method yet practis d for the increaſe of Money.
<!-- src-d2dd432e2f00 -->

- **反对"抬高/改合金货币"**——升值只在面值上做文章，不增真价值（OCR `N HEN`＝WHEN、`|` 页饰、`3` 讹形）：

> N HEN I uſe the Words, Raiſing the Money, I deſire to be underſtood raiſing | it in the Denomination 3; For I do not ſuppoſe it adds to the Value.
<!-- src-d2dd432e2f00 -->

- **货币稀缺是"因"不是"果"**（此句后半跨版口、OCR 跳行，只引前半；干净全句见 ②）：

> Moſt People think ſcarcity of Money is only the Conſequence of a Ballance due
<!-- src-d2dd432e2f00 -->

- **土地是最佳货币**——"土地生万物、银子只是产物"，土地量不增不减故价值最稳（两句均跨断行，归一空白后可回验）：

> Land is what produces every thing, Silver is only the product.
<!-- src-d2dd432e2f00 -->

> Land is what in all ap-
> pearance will keep its Value beſt, it may riſe in va-
> ſue, but cannot well fall: Gold or Silver are lyable to many Accidents, whereby their Value may leſſen; but cannot well riſe in value.
<!-- src-d2dd432e2f00 -->

⇒ 第 V 章结尾立论："国家实力＝人口＋仓储，皆系于贸易，贸易系于货币"（此句在 1705 中 OCR 讹作 `Wm TATIONAL Power and Wealth`，`TATIONAL`＝NATIONAL）；故以土地为担保发钞是 Law 的终极药方，即第 VII 章"40 名专员、以地抵押发钞、随供需增减"的提案骨架。

### ② 《Money and Trade Considered》（1750 格拉斯哥版）——同书的干净重印与死后署名
`src-b88a0f5958dd` 是 1705 的重印（1750 年，Law 已死于 1729），题名页完整，把作者写死为"THE CELEBRATED JOHN LAW"，并加注其"AFTERWARD DIRECTOR TO THE MISSISIPI COMPANY"。题名页 OCR 讹形照录（`MDCCY.`＝MDCCV、`con sidered:`＝considered:、`LA W`＝LAW、`MISSISIPI`＝Mississippi、`FOIJLI`＝FOULIS、`MD CCL.`＝MDCCL）：

> MONEY AND TRADE con sidered: WITH A PROPOSAL FOR SUPPLYING THE NATION WITH MONEY. FIRST PUBLISHED AT EDINBURGH MDCCY. BY THE CELEBRATED JOHN LA W, Esq; AFTERWARD DIRECTOR TO THE MISSISIPI COMPANY. GLASGOW, PRINTED AND SOLD BY R. & A. FOIJLI MD CCL.
<!-- src-b88a0f5958dd -->

正文与 1705 同书（八章结构一致，OCR 干净得多，长 s 讹为 f：`fcarcity`＝scarcity、`fhall`＝shall 等）。①里无法逐字引用的"货币稀缺即原因"全句，在此得到干净版（OCR `mo- ney`＝money 断行、`confequenceof`＝consequence of 紧连、`abal- lance`＝balance 断行）：

> Moft people think fcarcity of mo- ney is only the confequenceof abal- lance due ; but 'tis the caufe as well as the confequence, and the effectual way to bring the ballance to our fide, is to add to the money.
<!-- src-b88a0f5958dd -->

- **信用不能脱离货币存量无限扩张**（这是理解他后来"以土地为担保、而非凭空印钞"的关键约束；`inconsi- derable`＝inconsiderable 断行）：

> Credit that promifes a payment of money, cannot well be extended beyond a certain proportion it ought to have with the money, and we have fo little money, that any credit could be given upon it, would be inconsi- derable.
<!-- src-b88a0f5958dd -->

- **提案的自我定位**（对苏格兰的许诺——"安全、可行、对苏格兰全体与每个苏格兰人有利"；`advan- geous`＝advantageous 断行讹形）：

> What I propofe, will I hope be found fafe, and practicable ; advanta- geous in general to Scotland, and in particular to every Scots-man.
<!-- src-b88a0f5958dd -->

- **"货币供给＝需求"的稳定币值承诺**（OCR `paper- money`＝paper-money 断行、`will be keep`＝will keep、`wrill`＝will）：

> this paper- money will be keep its value, and there wrill always be as much money as there is occafion, or imployment for, and no more.
<!-- src-b88a0f5958dd -->

⇒ 1750 版的价值：①提供 1705 残缺/讹损处的干净对照；②证明这本 1705 提案书在 Law 死后仍被当作"密西西比公司导演者"的著作重印——死后署名的"品牌化"，题名页本身就是一条传记证据。

### ③ 《A Full and Impartial Account...》（1720）——泡沫进行时的亲 Law 宣传册
`src-4a39617aea24` 是 1720 年（System 尚未崩盘）的英法双语小册，通篇亲摄政王、亲 Law。扫描件首页附一则书商目录注（"8vo., French and English, scarce and curious, hf. mor. Lond. 1720 … In Rich's Bib. … Very rare"），属二手出处、非正文。题名页以"不可思议的收益"点题（OCR `aloft`＝almost、`Eftablifhment`＝Establishment、`|` 页饰）：

> WHEREIN the Nature of that Eftablifhment and the | aloft incredible Advantages thereby accruing to the
<!-- src-4a39617aea24 -->

- **公司建立的叙事**：1717 年成立，Law 任 principal Director（OCR `whofe`＝whose、`catry’d`＝carried、`Stu- dy`＝Study）：

> Mr. Law, a Scotch Gentleman whofe Genius always catry’d him to the Stu- dy of Trade and Money
<!-- src-4a39617aea24 -->

- **狂热数字**：股票（Aétions）几小时内认购满额、超出部分三分之二被退回（OCR `Hours : ;`＝Hours:;、`oblie’d`＝oblig’d、`fabferib’d`＝fubfcrib’d、`amounted.`＝amounted），又"几周内涨到一千二"：

> The Subfcriptions were fill'd in a few Hours : ; nay, and they were oblie’d to return a Third Part which was fabferib’d above the Sum, which amounted. to Seven hundred and feventy five Millions.
<!-- src-4a39617aea24 -->

> fo that ina few Weeks they advanc'd to Twelve hundred.
<!-- src-4a39617aea24 -->

（OCR `ina`＝in a。）此册甚至为"股价跌至 760 时公司挂告示按 900 回购"辩护，把稳定股价的公开回购当作信用工具来宣扬。

- **"货币流通"作为颂词**：流通量"肯定是史无前例的三倍"（页饰 `|` 隔在 the 与 Circulation 之间、`D:` 夹在 certainly 与 three 之间，故分作两引）；巴黎"人人钱多到不知往哪儿放"：

> Circulation of the Species, which is certainly
<!-- src-4a39617aea24 -->

> three times greater than it ever was
<!-- src-4a39617aea24 -->

> Money grew fo common, that People did not know where to put it out at Three per Cent.
<!-- src-4a39617aea24 -->

- **对 Law 个人的颂扬**——同页称其"连他的敌人也得到提携"（OCR `tohis`＝to his；"done Service to vaft Numbers of People"前半混入页饰，未逐字引全）：

> even tohis Enemies
<!-- src-4a39617aea24 -->

- **巴黎银行与 1719-12-21 敕令**：说明银行早于密西西比公司设立；敕令把"银行货币"固定为高于现行硬币 5%（原文为法文，OCR `PArgent'`＝l'Argent、`de meurera`＝demeurera、`au deffus`＝au-dessus）：

> Mr. Law fet up a Bank at Paris, by the
<!-- src-4a39617aea24 -->

> PArgent' de Banque fera & de meurera fixé a Cinq pour Cent au deffus de la valeur de Argent courant
<!-- src-4a39617aea24 -->

（"fome Time before the Eftablifhment of the Miffiffipi"在 OCR 中为 `Efta- i blifament`、`Miffi/fipi`，页饰 `|`/`i` 掺入，未逐字引全句。）

⇒ 这份源的声口是 **System 的辩护方**（"流通三倍""皇库增收 4000 万""土地涨到 50–60 年购买率"），与 1705 书里"自愿接受信用、货币供给随需求伸缩"的谨慎形成张力——这正是泡沫期间 Law 系话语的样本。

### ④ 《Oeuvres de J. Law》（1790）——法国大革命语境下的 Law 结集
`src-06814a9eaeb9` 是 1790 年（革命政府发行 assignats 前夜）出版的 Law 论著结集，编注者为 M. de Senovert（据 ⑤ Daire 卷内注；题名页未署名）。卷首是编者的《Discours préliminaire》，把"信用"抬成治国之学（编者语，非 Law 原文）：

> Le crédit joue un rôle si considérable dans l'économie politique des nations modernes , il est si intimement lié à leur prospérité et même à leur existence , qu'on pourroit dire que la science du Gouvernement n'est autre chose que la science du crédit lui-même
<!-- src-06814a9eaeb9 -->

- **编者笔下的 Law 结局**（传记性尾声，为整卷定调；OCR `a ne` 残句略去）：

> cet homme venu en France avec une fortune considérable et qui avoit disposé de plusieurs milliards; après avoir erré dans plusieurs contrées, mourut à Venise dans une indigence et un abandon absolus
<!-- src-06814a9eaeb9 -->

- **《Premier Mémoire sur les Banques》（呈摄政王）**——开宗明义：国家实力＝货币数量与运用（OCR `cjuî`＝qui、`Sont`＝sont，`dé- pendent`／`mon- noies` 为断行连字符）：

> Le commerce et le nombre des peuples cjuî Sont la richesse et puissance d'un Etat, dé- pendent de la quantité et conduite des mon- noies.
<!-- src-06814a9eaeb9 -->

> Les hommes sont d'un grand prix
<!-- src-06814a9eaeb9 -->

- **《Second Mémoire sur les Banques》**——银行即"一般信用"，并论证钞票流速约三倍于硬币、可等值于三倍货币量（`principa- lement` 为断行；标点前空格为 OCR 版式）：

> La banque est un crédit général qui produit des commodités et des avantages à toutes les parties de l'Etat et principa- lement au commerce.
<!-- src-06814a9eaeb9 -->

> une somme en billets, circulant par exemple trois fois plus vite qu’en espèces , elle figure dans le commerce , comme s’il y en avoit trois fois autant.
<!-- src-06814a9eaeb9 -->

- **绝对君主更善用信用的论点**——向法国君主制献计的核心（OCR `meme`＝même 去重音，`gou- verner`／`davan- tage` 为断行；后文"以低于受限于议会之君主的利率借到所需之款"跨版口噪声，未逐字引）：

> Je soutiens meme qu’un prince absolu qui sait gou- verner , peut étendre son crédit davan- tage
<!-- src-06814a9eaeb9 -->

- **《Lettre I》（1715 年致摄政王）**——"信用时代"取代"硬通货时代"：

> Avant l'introduction du crédit , l'Etat qui était le plus riche en espèces était le plus puissant ; mais à présent , c'est celui qui se sert le mieux de son crédit
<!-- src-06814a9eaeb9 -->

并记 Marly 轶事——他告诉摄政王"银行不是我最要紧的想法"，另有一个能"无代价供给 500 百万"的方案（OCR `fourni-* rois`＝fournirois 断行带脚注星号、`5oo`＝500）：

> que mon idée de banque n’étoit pas la plus considérable, que j’en avois une par laquelle je fourni-* rois 5oo millions qui ne coûteraient rien aux peuples.
<!-- src-06814a9eaeb9 -->

- **编者同信注里的失败归因**（OCR `L auteur`＝l'auteur、`i!`＝il、`idavoit`＝avoit、`courti- sans` 断行）：

> L auteur avoit prévu l’avidité du gouvernement, mais i! idavoit prévu, ni son ignorance, ni les intrigues des courti- sans, ni la folie des peuples
<!-- src-06814a9eaeb9 -->

⇒ 1790 结集把 Law 的"信用/货币/银行"论捆绑成一份体系文本，被革命时代借为论战资源；其声口是编者（同情而清醒的史评者）＋Law 本人（推销者）两层，引用时须区分。

### ⑤ 《Économistes financiers du XVIIIe siècle》（Daire 1843）——实证史家的 Law 传记与一手重印
`src-ce1dbab2c760` 是 512K 词大部头（Vauban、Boisguillebert、Law、Melon、Dutot 等合集）。本道只读含 Law 的部分：`NOTICE HISTORIQUE SUR JEAN LAW`（约 25016 行起）与 `LAW` 论著重印段（约 35846 行起，至"Ici se terminent les Oeuvres de Law"处收束），其后再附 1720 年四封信与《Mémoire sur les Monnaies》。Daire 的 Notice 开篇即传记（OCR `Édimboiirg`＝Édimbourg、`ep`＝en）：

> Jean Law naquit à Édimboiirg, ep 1671.
<!-- src-ce1dbab2c760 -->

- **Daire 对学理的概括**——"纸币是最佳货币，因为它没有内在价值"；但 Daire 认为这是被他一意孤行的"执念"：

> la monnaie par excellence, c'était le papier, parce qu'il manque de valeur intrinsèque.
<!-- src-ce1dbab2c760 -->

- **传记细节**（伦敦决斗杀人、流亡大陆习商、自称"社会经济学的大发现"；标点前空格为 OCR 版式）：

> finit par tuer, dans une rencontre particulière, un certain M. Wilson
<!-- src-ce1dbab2c760 -->

> d'un génie éminemment propre à l'action , crut avoir fait une grande découverte en économie sociale
<!-- src-ce1dbab2c760 -->

- **重印的《Lettre XV》（1716，致摄政王）——反强制纸币**：Law 在 1716 年明确主张信用须"与硬币平价、自愿接受"，强制反而有害（这是与 1720 年 System 实践最刺眼的张力；OCR `11 est`＝Il est）：

> 11 est absolument pour le bien de l'État, en tout temps , d'établir un crédit général , mais il est nécessaire que ce crédit soit au pair avec les espèces , et que l'introduction de ce crédit dans le commerce et payements particuliers soit volontaire ; si le crédit est forcé, il fera du mal au lieu de faire du bien
<!-- src-ce1dbab2c760 -->

- **1721 年致 Duc de Bourbon 的自辩信**（System 崩后，Law 在伦敦申诉；`sub- siste` 为断行）：

> je suis nu; on veut que je sub- siste sans biens, et que je paye des dettes, sans en avoir les fonds.
<!-- src-ce1dbab2c760 -->

- **编者对 System 后的 Law 的刻画**（"被放逐、迫害、诽谤、掠夺"地流亡欧洲；`ca- lomnié` 为断行，标点前空格为 OCR 版式）：

> son malheureux auteur, banni , persécuté , ca- lomnié, expolié, courait l'Europe
<!-- src-ce1dbab2c760 -->

- **1720 年《Première Lettre sur le nouveau système des finances》**（出自《Mercure de France》1720 年 2 月，Daire 归为 Law 为维护 System 所发）——关于"零息放贷"的理想（OCR `11 serait`＝Il serait）：

> 11 serait à souhaiter qu'il se prêtât toujours pour rien, ou dans la seule vue de partager avec l'emprunteur le profit qu'il en tirera; c'est le commerce que tout le monde peut faire sans être marchand
<!-- src-ce1dbab2c760 -->

⇒ Daire 卷的价值：①19 世纪实证史家对 Law 的传、评、一手重印三合一；②把 1716（反强制）与 1720（系统辩护）两个 Law 声口并置，暴露"Law 从反强制走向亲强制/被系统绑架"的路径——这是下游论战分析最宝贵的原料。

## 这一道给下游的东西

- **货币理论签名**：价值＝数量/需求比（水与钻石例）；货币是"度量＋交换媒介＋契约计值"三重功能；货币"不是抵押品"；"货币稀缺是原因不是结果"；增币（经银行信用）可雇佣更多人口，而人口＝财富。
- **"土地＝最稳货币"论点**：土地量不增不减、价值只升不降，故以土地为担保的纸币比银子更适合作货币；纸币无内在价值反而是优点（不会因贵金属进口而贬值、不会被出口、供给可随需求伸缩）。
- **银行/信用理论**：银行是增币最优工具；钞票流速约 3 倍于硬币，等价于三倍货币量；信用须与硬币平价、自愿接受（1716 立场）；绝对君主比受议会限制的君主更能扩展信用、借得更便宜。
- **论战语法**：以"反例/思想实验"立论（岛屿例、水钻石例、两个订阅案对照）；对 Locke/对手逐条设 objection—answer；爱用精确算术推演（英格兰/荷兰/苏格兰对照表、工资×雇佣数算出国家增值额）。
- **声口对照链（可复用叙事弧线）**：1705 苏格兰提案人（谨慎、以"自愿信用"自持）→1715/1716 银行推销者（反强制、献计绝对君主）→1720 系统辩护/狂热宣传（流通三倍、皇库增收）→1721 自辩者（"我是赤裸的"）→1790/1843 编者（清醒的史评）。下游可写"被 System 反噬的理论家"：理论的自我约束（自愿、平价、随需求伸缩）在实践中被放弃。
- **归属红线（引文信用分级）**：1705/1750 两版是 Law 本人（1705 初版、1750 死后重印）；1720 小册按 IA 著录归 Law 但实为匿名（"Two Letters from a Gentleman"，部分书目归 Defoe）；1790 Oeuvres 是编者 de Senovert 结集，《Discours préliminaire》及脚注是编者语、不可当 Law 本人观点；1843 Daire 卷的 Notice 是 Daire 的二手传记，重印的一手文本（Lettres/Mémoires）才可当 Law 原文。**凡引"编者语"必须标"编者/二手"**。

## 未做完 / 未核

- **1705 题名区残缺**：`src-d2dd432e2f00` 题名页扫损，`Money wa Trade`／`Supljng the NATION wth MONEY` 只能拼读，得不到完整题名页；CHAP IV 后半与 CHAP VII 部分版面 OCR 严重噪损（大量乱码行），相关引文改用 1750 干净版或换句。
- **1705 卷末错字表**：文件末尾有一处 errata（如 "Pag. 126, Par. 1. laſt for 20833 lib. … 189585 lib."），OCR 噪损难逐字解读，未作为引文采用；它说明该册确为初版印本。
- **Économistes 只读 Law 分栏**：`src-ce1dbab2c760` 仅精读 `NOTICE HISTORIQUE SUR JEAN LAW` 与 `LAW` 论著重印段（约 25016–36630 行）；Daire 所附 1720 四封信与《Mémoire sur les Monnaies》只读到 Première Lettre 开头，未逐段读完；Melon/Dutot/Vauban 等其余作者未读、未引。
- **Oeuvres 未整本通读**：`src-06814a9eaeb9` 精读了 Discours préliminaire（开头＋传记尾声）、Premier/Second Mémoire、Lettre I 及全书表目；法译《Considérations》八章与 Lettre II–XV、致 Bourbon 信、Fragmens 仅扫读未逐段引。
- **年份/归属待核**：1720 小册署名有争议（IA creator=Law，正文匿名，部分书目归 Defoe）——按 IA 著录处理并在此注明；1790 Oeuvres 编注者据 Daire 卷内注为 M. de Senovert（题名页未署名），未独立核实；1720 小册首页书商目录注为扫描附加的二手出处。
- **回验口径**：引文已对五份 raw 文件逐条 grep 回验，比对前先归一空白（18 世纪宽空格/断行连字符/标点前空格），并将撇号字形（弯引号 ’ / 直引号 '）按纯排版差异归一再比对；OCR 讹形（`wa`、`ef them`、`Supljng`、`TATIONAL`、`whofe`、`catry'd`、`oblie'd`、`fabferib'd`、`tohis`、`cjuî`、`i!`、`idavoit`、`11 est`、`11 serait`、`Édimboiirg` 等）一律照录未修。
- **引文坐标粒度**：本道坐标到 source_id 级；1705/1750 可标章号（CHAP I–VIII），1720 可标页（(23)(44)…），Oeuvres/Daire 可标章/信序号，但页码 OCR 不可靠，未逐一核。
