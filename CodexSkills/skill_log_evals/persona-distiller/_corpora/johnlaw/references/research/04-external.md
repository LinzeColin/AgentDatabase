# External

## Scope and assigned sources

**本道分到 1 份（train split）**：

| source_id | 出版年 | tier | 题名 |
|---|---|---|---|
| `src-95aa7717830b` | 1887 | P2 | An historical study of Law's system |

★ 本节由台账机械导出（`emit_lane_scope.py`），**不含任何阅读判断**；只投影 `split == train` 的行。

## 8 条实测发现（逐份）

★ 引文逐字照录 raw 扫描原文：双空格排版与 OCR 讹形原样保留（如 `com`=`coin`、`f`=长 s），行尾断词连字符照录，**不作静默拼接、不作「善意修正」**——保证每条引文都能在 raw 中逐字 grep 命中。个别位置因 OCR 版面有不规则空格（如「I   will   compel」三空格、`sum  of crowns,` 单空格），均照录；被引段落的原书脚注记号（如 `*`、`f`、`{billets}`）保留在行内相应位置。引文块中被省略的源行（脚注行、页数行如 `55`、空行）一律用 `[版口：…]` 在原位标出，不作静默跳行。

### ① 舞台设置：路易十四死后法国的财政破产，是 Davis 评价 Law 体系的背景框架

> At  the  death  of  Louis  XIV.,  France  was  practically
> bankrupt.

<!-- src-95aa7717830b -->

> Law  appeared  upon  the  scene.
> He  was  born  in  Edinburgh,  in  1671.

<!-- src-95aa7717830b -->

- Davis 开篇把 Law 放进一个具体的危机舞台：路易十四死时法国「实际上已破产」——浮债与年金的资本额约 30 亿里弗尔，但王国的资源连付息都勉强；长期战争耗尽国力，商业不振、制造停滞、农业几近荒废，劳动力逃亡意大利，政府信用几乎荡然。在此背景下摄政王被迫讨论赖账，Visa 清算、Chamber of Justice 等任意手段进一步吓跑资本。Davis 随后给出一段极简生平（1671 生于爱丁堡、1694 决斗杀人判死、越狱逃阿姆斯特丹、1705 苏格兰土地银行被否、流亡欧陆靠赌戏与投机致富）——把 Law 定位成「在一个急需救星的破产王国里登场的金融天才」。

### ② Law 的货币教义（经 Davis 转述）：三条命题 +「货币充足即繁荣、信用即货币的等价物」

> 1.  That  all  materials  suitable  for  coinage  may  be  con-
> verted into  money.
[版口：脚注行 *]
> 2.  That  the  abundance  of  money  is  the  condition  on
> which  depend  labor,  husbandry,  and  population.
[版口：行间空行]
> 3.  That  paper  is  more  suitable  than  the   metals  for  a
> ,    circulating  medium.

<!-- src-95aa7717830b -->

> The  source  of
> prosperity  in  any  country  he  attributed  to  the  abundance
> of  money.  Credit  was  the  equivalent  of  money.

<!-- src-95aa7717830b -->

- Davis 用 Forbonnais 的提要约简了 Law 的体系纲领：一切可铸材料皆可转成货币；货币充足是劳动、农桑、人口的先决条件；纸比金属更适合作流通媒介。在论证第三条时 Law 强调：君主借 augmentations/diminutions（币面价值增减）与成色改动可使金属币价值不定，金银币价值还随铸块市价（受进口量支配）波动、受制于外国；纸无内在价值，不受市场波动影响，数量可随需求调节，且可用「特定成色足重铸币」标价以抵御改币与挤兑。Davis 点出 Law 的核心因果链：任何国家的繁荣都源于货币充足，信用等于货币，靠增加流通媒介可压低国债利息、甚至赎回本金，从而刺激贸易与制造、最终扩大税收。这条「货币数量→繁荣」的链条正是后世批判的靶心。

### ③ 模型来源与目标：以阿姆斯特丹/英格兰银行为模板，把全国硬币吸进银行、以纸币取代流通

> the  banks  then  in  existence ;  but  it  is  evident  that  the
> banks  from  which  he  deduced  most  of  his  theories,  and
> upon  the  example  of  which  he  relied  for  his  plans  for  re-
[版口：插入长脚注 *（Law 著作 1790 年结集 Senovert/Daire 考订）]
> generating  France,  were  the  Bank  of  Amsterdam  and  the
> Bank  of  England.

<!-- src-95aa7717830b -->

> means  of  the  increase  of  the  circulating  medium,  interest
> on  the  debt  could  be  reduced,  and  perhaps  the  principal
> could  be  redeemed.

<!-- src-95aa7717830b -->

- Davis 分析 Law 的两个理论模板：阿姆斯特丹银行是存款银行（货币入行即沉淀、以账面信用替代流通，靠经纪人维持硬币与信用间的均衡），英格兰银行建立在政府信用上、以贷款给政府为业、是贴现与流通银行；Law 从中得出的方案是——只要法国人像阿姆斯特丹商人信任其银行那样与一家银行往来，全国硬币都能吸进银行金库，大量纸币会发行并被偏好于硬币，银行可当政府代理、收齐税款、凭此信用再发更多纸钞。Davis 指出 Law 设定的关键等式：借流通媒介的增加压低国债利息、赎还本金，从而刺激贸易、扩大税收（引文即此）。Davis 还提到 Law 的第一份银行方案是 1715 年 10 月 24 日在一次有银行家、商人、城市代表参加的枢密院特别会议上提出的，但因当时主管财政的 Duke of Noailles 反对而胎死腹中。

### ④ 同时代统治者的警惕：萨伏依的 Victor Amadeus 的拒绝，与「才华难驳、方案离经」的欧陆名声

> "  I  am  not  rich  enough
> to  ruin  myself."

<!-- src-95aa7717830b -->

> a  brilliant  financier,
> whose  reasoning  it  was  difficult  to  refute,  but  whose  plans
> differed  so  materially  from  those  then  in  vogue

<!-- src-95aa7717830b -->

- 在 Law 找到法国这个「实验场」之前，他走遍欧洲向各君主兜售银行与信用方案：向 Chamillart 提议设银行、向 Prince de Conti 呈送备忘录（路易十四末年又转给 Desmarets）、向萨伏依的 Victor Amadeus 提出同一方案——后者用一句警句式答语打发了他：「我还没富到能把自己毁掉的程度」（引文即此）。Davis 概括 Law 当时的欧陆名声：一个才华横溢的金融家，其推理难以驳倒，但方案与通行做法相去太远，以致没有君主愿意采纳。Davis 强调他赌桌上的成功与放荡生涯并不妨碍其影响力。

### ⑤ 同一道敕令（1720 年 3 月 5 日）的四种后世解读：Daire 视为拱顶石、Dutot 视为致命一击、Forbonnais 视为垮台信号、Louis Blanc 视为栽赃罪行

> According  to  Daire,  it  was  the  key-
> stone of  the  system,  and  fully  realized  Law's  economic
> thought.

<!-- src-95aa7717830b -->

> Dutot  says  the  decree  was  a  mortal
> blow  to  the  system.

<!-- src-95aa7717830b -->

> Forbonnais  says  the  decree  absolutely  decided
> the  fall  of  the  system.

<!-- src-95aa7717830b -->

> Louis  Blanc  denounces  the  decree  as  a  crime,  which  has
> unjustly  been  imputed  to  Law

<!-- src-95aa7717830b -->

- external 道的核心素材：Davis 用 1720 年 3 月 5 日敕令（规定股票可在银行按每股 9000 里弗尔固定价兑换纸币、银行收回全部贷款）展示了后世对 Law 体系评价的严重分裂——Daire（反 Law）视它为体系拱顶石、完整实现了 Law 的经济思想（银行变成流通媒介的蓄水池，纸币与股票互为出入口）；Dutot（辩护方）称它是「对体系的致命一击」，认为 Law 被迫在保纸币与保股票间二选一、选了股票，且暗示敕令实出摄政王与体系之敌之手；Forbonnais 认为它「绝对决定了体系的垮台」（Law 主张财富倍增、想让股票取得货币属性）；Louis Blanc（Law 的热忱崇拜者）则斥之为「归到 Law 头上的不义罪行」，称它其实是宫廷利益的产物、还「救了几个大领主」。Davis 把这一分歧当作衡量 Law 责任归属的坐标轴，并提醒读者：Dutot 曾估 1720 年 2 月底流通的股票市值约 4,891,000,000 里弗尔、同期纸币约 1,059,000,000 里弗尔，二者合计近 6,000,000,000——纸币与按固定价可兑的股票共同构成空前规模的纸面货币。

### ⑥ 1720 年 5 月 21 日敕令：体系的终点，与「谁该负责」的持续争论

> This  decree  was  the  end  of  the  system.  Steuart  says :
> "  The  arret  was  no  sooner  published  than  the  whole  paper
> fabric   fell   to  nothing.

<!-- src-95aa7717830b -->

> May,  a  man  might  have  starved  with  100,000,000  in  his
> pocket."

<!-- src-95aa7717830b -->

> Forbon-
> nais  says  the  step  taken  was  an  imprudent  one,  but
> cannot  be  attributed  to  the  enemies  of  Law.  The  plan
> was  prepared  by  Law,  and  had  been  submitted  to  the
> regent  for  consideration  more  than  two  months  before  this
> date.

<!-- src-95aa7717830b -->

- 5 月 21 日敕令把股票自 9000 里弗尔逐月降至 12 月 1 日的 5000、纸币同步减半——Davis 直接判它「是体系的终点」，并引 Steuart 的名言：arret（敕令）一出「整座纸建筑化为乌有」，次日「一个人口袋里揣着一亿里弗尔也可能饿死」。围绕责任归属，Davis 汇评：Forbonnais（无偏见）称这是「不智之举」但不能归罪于 Law 的敌人——计划由 Law 起草、早在两个多月前就呈交摄政王（引文即此）；Daire 认为「Law 反对此敕令」的说法很可能成立（看不出体系能从中得什么好处）；Duhautchamp 记录当时市场主流看法是 Law 本有「退出纸币、以硬币恢复流通」的计划，只因未获采纳、且他作为财政总监不得不呈报这份出于其政敌（d'Argenson、Le Blanc、Dubois）的敕令。Davis 的结论是：无论 Law 是否赞成，5 月 21 日的敕令摧毁了对纸币的一切信心，27 日撤回也救不回体系。

### ⑦ 对「强制信用」与专制手段的批判：分不清「信心与服从」，用强制力维持纸币

> "  I   will   compel   confi-
[版口：脚注 * 及页码 55]
> dence,"  he  had  asserted.

<!-- src-95aa7717830b -->

> He  was  willing  to  use  force
> in  an  emergency,  notwithstanding  the  fact  that  it  was
> opposed  to  the  principles  of  credit.

<!-- src-95aa7717830b -->

> His  faith  in  the  power
> of  decrees  of  council  lost  him  the  contest  with  the  real-
> izers.

<!-- src-95aa7717830b -->

- Davis 对 Law 最重要的批判点之一：他明知「强制与信用赖以建立的原理相悖」，却在紧急时毫不犹豫要用强制力（引文即此）。Davis 详列 Law 执政期的强制手段——1720 年 1 月 20 日授权搜查所有宅邸（含宗教团体）找隐匿硬币；1 月 28 日敕令纸币全国通行；2 月 4 日禁戴钻石珍珠、2 月 18 日禁金匠造金银器、2 月 19 日禁任何人持有超 500 里弗尔铸币、禁止持有金银器物（搜获归检举人）；1 月 29 日以纸币纳税打 25% 折扣；3 月 11 日禁止铸币支付、黄金去货币化——并借 Duclos 转述 Stair 勋爵的讥评：既然 Law 已把纸变成钱、证明了「变体」，他那套告发抄家制无异于在法国设立宗教裁判所。Davis 总结：Law 对枢密院敕令威力的信仰，使他输给了那些急于兑现（realize）的股东阵营。

### ⑧ Davis 的总评与后世定位：天才、国家银行原型、期货/保证金交易引入者，但高估专制权力、低估舆论

> of  the  history  of  the  system  reveals  Law  to  us  as  a  man
> of  genius,  whose  wonderful  insight  enabled  him  to  fathom
> the   marvellous   power   of  credit.

<!-- src-95aa7717830b -->

> which  was  in  many  respects  the  prototype  of  our  na-
> tional banks.

<!-- src-95aa7717830b -->

> He  familiarized  the  French  with  methods
> of  dealings  in  futures  and  on  margins  which  are  used
> in  speculation  to-day.

<!-- src-95aa7717830b -->

> He  exhibited  inconsistencies  in
> theory  and  practice,  many  of  which  are  traceable  to
> his  incapacity  to  recognize  the  difference  between  confi-
> dence and  obedience.

<!-- src-95aa7717830b -->

> He  overestimated  the  power  of
> despotic  authority,  and  underrated  the  influence  in  an
> absolute  monarchy  of  public  opinion  in  money  matters.

<!-- src-95aa7717830b -->

> The  French  were 'like  children  in  such  affairs,  and  he  did
> not  realize  how  completely  the  control  of  children  may
> be  lost  in  a  panic.

<!-- src-95aa7717830b -->

- 结尾是 Davis 给 Law 的正式经济史定位：天才，其洞察力使他看透了「信用那不可思议的力量」；他创立的银行「在许多方面是我们国家银行的原型」（引文即此，`na-` / `tional` 为原书行尾断词）；他把期货（futures）与保证金（margins）交易方式引入法国——这些手法至今仍用于投机。但 Davis 同时点出他致命的二元错位：理论与实践不一致，许多矛盾源于他「分不清『信心』与『服从』」；他高估了专制权威的力量，低估了绝对君主制下舆论对货币事务的影响——「法国人在这类事上像孩子，他没有意识到在恐慌中，对孩子的控制会彻底失控」。Davis 还补了一句平衡评价：Law 的自负到最后都未消减，崇拜者敬他如神，「连他的敌人也承认他的意图是好的」。书末他转述的一首 pasquinade 概括了这场泡沫的生与死（周一买股、周二成百万富翁、周三安排家计、周四坐上马车、周五赴舞会、周六进了济贫院）——后世对 Law 体系「既敬其天才、又嘲其荒诞」的双面态度，在这份 1887 年的研究里完整保留。

## 这一道给下游的东西

**后世评价框架（Davis 1887 提供）**
- 经济史分期视角：把 Law 体系放进「路易十四死后法国财政破产 → 摄政王信用试验 → 泡沫 → 崩溃」的叙事框架；Law 是「在破产王国登场的金融天才」。
- 教义还原：三条命题（一切可铸材料皆货币 / 货币充足决定劳动农桑人口 / 纸优于金属作流通媒介）+「货币充足即繁荣、信用即货币等价物」+「借增发流通媒介压低国债利息」——这是后世评价 Law 货币理论的共同坐标。
- 模型谱系：阿姆斯特丹（存款银行）× 英格兰（贴现/流通银行）双模板；Law 的方案 = 把全国硬币吸入银行、以纸币替代、银行兼政府代理。
- 责任归属谱系：同一事件在不同作者笔下被截然定性（Daire=拱顶石 / Dutot=致命一击 / Forbonnais=垮台信号 / Louis Blanc=栽赃），评价 Law 必须先声明采用哪位作者的视角。
- 终极定性（Davis 本人）：天才+国家银行原型+期货保证金引入者；但理论与实践矛盾，分不清「信心 vs 服从」，高估专制权力、低估舆论，输给「兑现者阵营」。

**对 Law 体系的批判点（可作 claims/矛盾素材）**
- 「信用靠自愿才能成立，他却愿以强制力推行」——理论与手段的根本矛盾（compel confidence）。
- 「货币数量→繁荣」的因果过于简单：Davis 指出他不会看到「流通媒介过多会驱走铸币、过量纸币会贬值」，只会看到「增发→降息→刺激产业」的一面。
- 纸币面文从「当日成色足重铸币」改为「银币里弗尔」，等于把纸币重新暴露在他自己批评过的改币风险下（注：这条主要见 Wood，Davis 亦有涉笔）。
- 同一体系既被称「实现 Law 经济思想的拱顶石」又被称「致命一击」——证据不允许二选一，须保留分歧。
- 1720 年 2 月底纸币+按固定价兑换的股票合计近 6,000,000,000 里弗尔，远超王国铸币——「量」的失控是体系崩塌的机械原因。

## 未做完 / 未核

- Davis 正文大量数字（各次纸币/股票发行额、资本构成 1/4 现金 + 3/4 billets d'etat 等）在不同作者（Forbonnais、Ganilh、Dutot、Lemontey、Jobez）间有出入，Davis 自己逐条考订；本道只保留与「评价框架」相关的口径，未逐一重算每笔账面。
- Davis 多处引用 Law 本人著作（经 Daire 编《Économistes Financiers》），本道未把那些 Law 自述当作「外部评价」引证，仅在其为 Davis 所转述/所引证时一并呈现；若下游需要 Law 原话，应回到一手道（writings）。
- Davis 对 Law 改宗天主教、生活作风等私德基本未置评，本道未补；external 道只覆盖「后世对他货币体系的评价」，不覆盖他的人格评价（该素材主要在 Wood 一手的传记叙述里）。
- 1887 年之后的后续学术（如对 Law 作为早期中央银行思想先驱的再评价）不在本道一手源覆盖范围，未引用。
