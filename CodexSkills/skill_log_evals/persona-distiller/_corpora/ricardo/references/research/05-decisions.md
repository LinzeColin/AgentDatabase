# Decisions

## Scope and assigned sources

**本道分到 2 份（train split）**：

| source_id | 出版年 | tier | 题名 |
|---|---|---|---|
| `src-ab6006937cf3` | 1811 | P1 | Reply to Mr. Bosanquet's Practical observations on the report of the Bullion Committee |
| `src-1fb434eb687b` | 1816 | P1 | Proposals for an economical and secure currency : with obs…the proprietors of bank stock |

★ 本节由台账机械导出（`emit_lane_scope.py`），**不含任何阅读判断**；只投影 `split == train` 的行。

## 14 条实测发现（逐份）

### ① 论战定性：承认 Bosanquet 是最强对手，并把驳倒他当作守原则的试炼

>  Of  all  the  attacks  on  the  report  of  the  Committee,  however,  that  of  Mr.  Bosanquet  has  appeared  to  me  the  most  formidable.

<!-- src-ab6006937cf3 -->

>  It  is  these  proofs  which  I  propose  to  examine,  and  am  confident  that  it  will  be  from  a  deficiency  of  ability  in  me,  and  not  from  any  fault  in  the  principles  themselves,  if  I  do  not  shew  that  they  are  wholly  unfounded.

<!-- src-ab6006937cf3 -->

⇒ 他不否认对手"可畏"：Bosanquet 不像前人那样只做空泛斥责，而是搬出"与理论相冲突的历史事实"来攻金块委员会。他的应战方式是：逐条检验这些"事实"，并预先把失败归到"自己能力不足"而非"原则有错"——这句自白是他整个驳论的基调：理论本身在他心中已定案，需要检验的只是对方的"事实"。

### ② 处置"理论 vs 事实"之争：要求对方亮出理论或指出事实，自己愿受检验

>  can  that  system  be  called  wholly  theoretical  which  appeals  to  those  principles,  and  is  willing  to  submit  to  the  test  of  those  laws?

<!-- src-ab6006937cf3 -->

>  I  have  long  wished  that  those  who  refused  their  assent  to  principles  which  experience  has  appeared  to  sanction,  would  either  state  their  own  theory  as  to  the  cause  of  the  present  appearances  in  tlie  state  of  [版口：跨页，原版第 4 页页眉插入]  our  currency,  or  that  they  would  point  out  those  facts  which  they  considered  at  variance  with  that  which,  from  the  firmest  conviction,  I  have  espoused.

<!-- src-ab6006937cf3 -->

（引文跨版口，"tlie"＝the 之 OCR 讹形照录。）⇒ 面对"理论家不懂实际"的俗套指控，他反诘：一个肯用货币学久经验证的原则、并自愿接受这些规律检验的体系，怎能叫"纯理论"？他并主动向反对者开价：要么提出自己的理论解释当前币情，要么指出那些他们认为与理论冲突的事实。他对"事实"检验的姿态是开放甚至欢迎的——前提是对方拿出可验证的东西，而不是空喊口号。

### ③ 理论基石：套利/竞争会把超额利润压回一般利润率

>  That  theory  takes  for  granted,  that  whenever  enormous  profits  can  be  made  in  any  particular  trade,  a  sufficient  number  of  capitalists  will  be  induced  to  engage  in  it,  who  will,  by  their  competition,  reduce  the  profits  to  the  general  rate  of  mercantile  gains.

<!-- src-ab6006937cf3 -->

⇒ 驳"1764–68 年伦敦—巴黎汇率长期偏离运金成本"这一史例时，他亮出理论基石：只要某一行当能赚超额利润，足够的资本家会被引进来、靠竞争把利润压回一般商业利润率；汇率套利正是这类"竞争最充分"的行当，不可能长期维持 12–14% 的套利利润。用一般均衡/竞争理论消化"反常史例"，是他处理反对者"事实"的标准动作。

### ④ 判断：限制法下英格兰银行确实握有"强制流通"银行券的能力

>  It  is  not  intended  by  the  words  forced  circulation  to  accuse  the  Bank  of  having  departed  from  those  cautions  which  have  usually  accompanied  the  issue  of  their  paper

<!-- src-ab6006937cf3 -->

>  The  plea  that  no  more  is  issued  than  the  wants  of  commerce  require  is  of  no  weight;  because  the  sum  required  for  such  purpose  cannot  be  defined.  Commerce  is  insatiable  in  its  demands,  and  the  same  portion  of  it  may  employ  10  millions  or  100  millions  of  circulating  medium;  the  quantity  depends  wholly  on  its  value.

<!-- src-ab6006937cf3 -->

⇒ 针对"银行从无能力强迫流通"的辩护，他划清界限：不是说银行违背了以往发行时的谨慎，而是《限制法》使银行能维持在无此法律时无法维持的超额银行券余额——这余额的效应与"政府银行强制发行"完全相同。他并击碎"只发行商业所需"的辩护：商业所需的数额根本无法界定，"商业的胃口贪得无厌，同一块生意可用 1000 万也可用 1 亿流通媒介，数量完全取决于其价值"——发行量问题被彻底还原为价值问题。

### ⑤ 判断：减少银行券会降金价、改善汇率，且不扰乱进出口结构

>  To  me,however,  it  appears  perfectly  clear,  that  a  reduction  of  Bank  notes  would  lower  the  price  of  bullion  and  improve  the  exchange,  without  in  the  least  disturbing  the  regularity  of  our  present  exports  and  imports.

<!-- src-ab6006937cf3 -->

>  No  mistake  would  be  greater  than  to  suppose  there  was  in  it  any  real  advantage.

<!-- src-ab6006937cf3 -->

⇒ 针对 Bosanquet"恢复现金支付会带来大祸、除非进出口结构改变否则汇率不会改善"的意见，他断言：减少银行券足以压低金价并改善汇率，而对外贸易的实际交易量不变；恢复平价后出现的那几个先令差额（如对汉堡从 28 先令恢复到 34 先令）只是"名义与外观上的好处"，若以为其中有任何真实利益，是最大的错误。他对"名义汇价回升"保持了冷静——真正要紧的是币值的实在恢复。

### ⑥ 判断：对外战争支出最终靠本国劳动产品偿付；唯一该警惕的是死守现行体制

>  I  am  persuaded  that  our  foreign  expenditure  is  neither  paid  with  gold  nor  with  bills  of  exchange,—  that  it  must  eventually  be  discharged  with  the  produce  of  the  labour  and  industry  of  our  people.

<!-- src-ab6006937cf3 -->

>  It  is  only  to  a  blind  perseverance  in  our  present  system  of  circulation  that  I  look  with  alarm, —  a  system  which  is  gradually  undermining  our  re- sources.

<!-- src-ab6006937cf3 -->

⇒ 他不接受"英国会被黄金抽干、注定败战"的末日推演：对外支出既非黄金也非汇票偿付，最终必须以本国劳动与工业的产品清偿。他把唯一的警报留给"对现行流通体制的盲目坚持"——这个体制正在逐步掏空本国资源。这是他把"恢复金本位"当作避免长期系统性损害的手段，而非情绪化的金本位崇拜。

### ⑦ 政策结论：唯一的"安全补救"是减少银行券；金价是检验尺度

>  The  more  I  have  reflected  on  this  subject,  the  more  convinced  I  am  that  the  evil  admits  of  no  other  safe  remedy  but  a  reduction  in  the  amount  of  Bank  notes.

<!-- src-ab6006937cf3 -->

>  the  high  price  of  bullion  was  the  test  on  whicli  I  most  relied  for  the  proof  of  depreciation

<!-- src-ab6006937cf3 -->

（"whicli"＝which 之 OCR 讹形照录；此句为书末附录脚注。）⇒ 全书收束于一句方法论自白：想得越多越确信，此弊"除了减少银行券数量没有别的安全补救"；而他自称"一贯主张"以金价高于造币厂价为判断贬值的首要检验标准（金价十年未低于造币厂价，他据此认为自己的结论无可辩驳）。同一页他还警告：在此体制下"谁还肯持有货币或以货币付息的证券？凡是持有这类财产的人，都应不惜代价为自己的未来做保障"（"Who  will  consent  to  hold  money  or  securities,  the  interest  on  which  is  payable  in  money,  on  such  terms?"）。

### ⑧ 讥讽对手标准的"朗姆酒桶"类比：不能用被掺假的酒样来检验掺假

>  A  puncheon  of  rum  has  16  per  cent  of  its  contents  taken  out,  and  water  poured  in  for  it.

<!-- src-ab6006937cf3 -->

>  What  is  the  standard  by  which  Mr.  Bosanquet  attempts  to  detect  the  adulteration

<!-- src-ab6006937cf3 -->

>  A  sample  [版口：(141)]  ef  the  adulterated  liquor  taken  out  of  the  same  cask.

<!-- src-ab6006937cf3 -->

（"ef"＝of 之 OCR 讹形照录；第二句原版作问句，OCR 以 "}" 收尾，引文改作 "?"；第三句跨版口，页号 141 为原版页码，作 `[版口：(141)]` 标出。）⇒ Bosanquet 声称"一镑银行券的标准可能就是 33 镑 6 先令 8 便士 3% 公债的利息"（即以银行券本身/其收益率作标准），Ricardo 用比喻反击：一桶朗姆酒被抽走 16% 又灌进水，Bosanquet 却取同一桶里已被掺假的酒样来检验掺假——标准与待检对象同源，当然检测不出贬值。这是他全书最尖锐也最形象的论战笔法。

### ⑨ 方案目标定义：完美的通货 = 不变的标准 + 始终贴合标准 + 最大节约

>  A  currency  may  be  considered  as  perfect,  of  which  the  standard  is  invariable,  which  always  conforms  to  that  standard,  and  in  the  use  of  which  the  utmost  economy  is  practised.

<!-- src-1fb434eb687b -->

⇒ 《Proposals》开篇即给出目标函数：通货的"完美"由三条同时成立——标准本身不变、通货始终贴合标准、使用上做到极致节约。这份 1816 年的方案正是把这三条逐条落地：金本位标准（⑫）、以金价为锚的发行规则（⑩）、以及把金属币换成纸币以实现"最省钱的流通媒介"（⑪）。

### ⑩ 核心方案：发行规则只看金价不看数量；银行按造币厂价兑付/收兑金块

>  The  issuers  of  paper  money  should  regulate  their  issues  solely  by  the  price  of  bullion,  and  never  by  the  quantity  of  their  paper  in  circulation.

<!-- src-1fb434eb687b -->

>  we  should  possess  all  these  advantages  by  [版口：26]  subjecting  the  Bank  to  the  delivery  of  uncoined  gold  or  silver  at  the  mint  standard  and  price,  in  exchange  for  their  notes,  instead  of  the  delivery  of  guineas

<!-- src-1fb434eb687b -->

（引文跨版口，页号 26 为原版页码，作 `[版口：26]` 标出。）⇒ 这是著名的"金块方案"（ingot scheme）：恢复兑付时，银行只需按造币厂标准价以"未铸金块"兑付银行券，而无需回到几尼金币；同时银行应按固定价（如每盎司 3 镑 17 先令）买入标准金，且单笔最低 20 盎司以免过琐碎。配套规则是：

>  The  most  perfect  liberty  should  be  given,  at  the  same  time,  to  export  or  import  every  description  of  bullion.

<!-- src-1fb434eb687b -->

⇒ 发行规则与金块自由进出相结合：银行只管按金价买卖金块来锚定币值，金银的进出口则完全放开。这样既恢复"可兑换"的信用约束，又避免保留高成本的几尼铸币流通。

### ⑪ 立场：纸币是商业的重大改进，不应因偏见退回金属币；金价高于造币厂价即贬值，此命题"无可回答"

>  A  well  regulated  paper  currency  is  so  great  an  improvement  in  commerce,  that  1  should  greatly  regret,  if  prejudice  should  induce  us  to  return  to  a  system  of  less  utility.

<!-- src-1fb434eb687b -->

（"1"＝I 之 OCR 讹形照录。）⇒ 他明确反对"恢复现金支付＝回到几尼金币流通"：规范管理的纸币是商业的重大进步，因偏见退回效用更低的体系是他最不愿看到的。同时他把金本位下的贬值判据钉死：

>  This  proposition  is  unanswered,  and  is  unanswerable.

<!-- src-1fb434eb687b -->

（此句紧接"while  these  metals  are  the  standard,  the  currency  should  conform  in  value  to  them,  and  whenever  it  does  not,  and  the  market  price  of  bullion  is  above  the  mint  price,  the  currency  is  depreciated"。）⇒ 对"市场金价高于造币厂价＝通货贬值"他给出不容置疑的表述，并把两种金属的标准之争也表了态：

>  on  the  whole,  silver  is  preferable  to  gold  as  a  standard,  and  should  be  permanently  adopted  for  that  purpose.

<!-- src-1fb434eb687b -->

⇒ 值得注意：此刻（1816）他主张白银比黄金更适合做标准（更稳、且外国多以银定值），与 1811 年《Reply》里"金是标准"的论战立场并不完全相同——他的标准主张会随语境调整，但"通货必须锚定一个具体金属标准"这一原则从未动摇。

### ⑫ 英格兰银行利润归属：公共服务的支付"极度挥霍"，国家应成为纸币唯一发行者并独占其铸币税

>  the  services  performed  by  the  Bank  for  the  public  are  most  prodigally  paid

<!-- src-1fb434eb687b -->

>  Paper  money  may  be  considered  as  affording  a  seignorage  equal  to  its  whole  ex- changeable  value, —  but  seignorage  in  all  coun- tries  belongs  to  the  state

<!-- src-1fb434eb687b -->

>  the  state,  by  becoming  the  sole  issuer  of  paper  money,  in  town  as  well  as  in  the  country,  might  secure  a  net  revenue  to  the  public  of  no  less  than  two  millions  sterling.

<!-- src-1fb434eb687b -->

⇒ 这是全书最激进的政策主张：银行替公众做的服务"被极其挥霍地支付"；纸币相当于提供一笔等于其全部交换价值的铸币税，而铸币税在各国都归于国家——因此国家若成为城乡唯一的纸币发行者（以可兑换为前提、由只对议会负责的专员管理），可为国家带来每年不下两百万英镑的净收入。同一文本他还主张 1808 年与银行订立的国债管理协议可重订（"either  party  is  now  at  liberty  to  annul  it."），理由是：该协议"无固定期限，与八年前订立的银行章程并无必然联系"（"The  agreement  was  for  no  definite  period;  and  has  no  necessary  connexion  with  the  duration  of  the  charter,  which  was  made  eight  years  before  it."）。

### ⑬ 季付分红票方案：用提前交付的可转让红利凭单平滑季度性钱荒

>  If  a  plan  of  this  sort  were  adopted  there  could  never  be  any  particular  scarcity  of  money  before  the  payment  of  the  dividends,  nor  any  particular  plenty  of  it  after.

<!-- src-1fb434eb687b -->

⇒ 针对每季付息前"税收入库 → 流通货币骤减 → 贴现行高利（国库券可折价、甚至有人赚 15–20% 年息）"的周期性钱荒，他提出：让银行在收款日前几天先向债权人交付可转让的红利凭单，凭单可在税局按剩余天数折息收兑——于是大笔政府收付不再经过现钞，季前不闹钱荒、季后不闹钱多。他自陈这计划"只是把伦敦银行业已普遍采用的节约支付体系，延伸到一类尚未应用的支付"（"the  plan  here  proposed  is  merely  the  extension  of  this  economical  system  to  a  species  of  pjiyments  to  which  it  has  not  yet  been  applied."，"pjiyments"＝payments 之 OCR 讹形照录），显示他对金融实务细节的掌控。

### ⑭ 编制风格与自证习惯：给数字、给计算、把账面算给公众看

⇒ 他在涉及银行利润的论证里总是落成具体算式：从 1806 到 1816 这十年间，银行对 1100 万公共存款按 5% 年息获利约 550 万镑，而公众所得补偿仅 168 万镑，净差 382 万镑——即银行"替公众做银行家"每年净得 382,000 镑，而该部门全部开支"也许不超过 10,000 镑/年"（"perhaps,  the  whole  expense  attending  this  department  of  their  business  does  not  exceed  10,000/.  per  ann."）；管理费按每百万镑计、存款余额按利息计、人员工资按档计（引 1807 年公共支出委员会报告：公共业务文员 1786 年 243 人、1796 年 313 人、1807 年 450 人，人均薪资 120–170 镑，加总管理成本最高估计 119,500 镑/年），用可复核的数字支撑"银行被过度支付"的结论。这是他对"如何做判断"的方法论示范——先立可检验的事实/数字，再推结论。

说明：上述算式在扫描页中数字区高度破损（如年份作 "18l6"、金额作 "1 1,000,000/." 与 "....  ^,0,500,000"），无法逐字可靠引用，本发现以改述呈现；数字含义与正文算式（原文逐项列明 5,500,000 / 1,680,000 / 3,820,000）一致，引用下游前建议换更高质量扫描核实个别数字。

## 这一道给下游的东西

（可作为 persona 依据的政策立场与判断方法，均按「（src-XXX，年份）」标注，均出自 Ricardo 署名文本。）

- 论战方法：承认对手"最可畏"、逐条检验其"事实"、把失败预先归到"自己能力不足"而非"原则有错"；要求反对者要么提出自己的理论、要么指出具体冲突事实（src-ab6006937cf3，1811）。
- 判断基石：套利/竞争会把任何行当的超额利润压回一般利润率，故反常史例不能推翻一般原理（src-ab6006937cf3，1811）。
- 核心判断：限制法使银行得以维持超发余额（"强制流通"）；"商业所需"无法界定，发行量问题即价值问题；减少银行券可降金价、改善汇率且不扰进出口（src-ab6006937cf3，1811）。
- 政策结论：恢复金本位（市场金价高于造币厂价即贬值，金价是首要检验尺度）；唯一安全补救是减少银行券；对外支出最终以本国劳动产品偿付；对死守现行流通体制的"盲目坚持"是他唯一的警报源（src-ab6006937cf3，1811）。
- 讥讽手法：用"以被掺假酒样检验掺假"类比揭穿"以银行券本身作标准"的循环论证（src-ab6006937cf3，1811）。
- 方案目标（1816）：完美的通货 = 不变的标准 + 始终贴合标准 + 极致节约；规范管理的纸币优于金属币，不应因偏见退回（src-1fb434eb687b，1816）。
- 金块方案：银行按造币厂价兑付/收兑未铸金块（单笔下限 20 盎司）、金银自由进出口、发行只看金价不看数量（src-1fb434eb687b，1816）。
- 银行利润归属：公共服务的支付"极其挥霍"；纸币即铸币税，铸币税当归国家；国家成为唯一纸币发行者每年可得不下 200 万镑净收入（src-1fb434eb687b，1816）。
- 实务细节：红利凭单方案平滑季度钱荒；论证必落数字算式（十年存款获利 550 万 vs 公众补偿 168 万，净差 382 万/年）（src-1fb434eb687b，1816）。
- 判断风格一致性：两源都以"先立可检验的原则/数字，再推政策结论"为方法；但具体标准主张有语境差异——1811 论战中坚持"金是英国标准"，1816 方案里主张"白银更适合作标准"，下游引用时须按年区分（src-ab6006937cf3 vs src-1fb434eb687b）。

## 未做完 / 未核

- **两份源均为 OCR 扫描文本**：个别字符/词形按 OCR 照录（如 `whicli`、`ef`、`1`、`tlie`），行尾断词连字符已机械拼接；三处跨版口引文（`[版口：4]`、`[版口：(141)]`、`[版口：26]`）为页号/页眉夹页所致，均按原文逐字保留并用标记标出。若下游需要标准拼写版本，建议在 `raw/_EXCLUDED.txt` 记录这些 OCR 变体，避免被拼写门拦。
- **《Reply》的章题/序言把 Bosanquet 的论点逐条编号引用**：本道只以 Ricardo 自己的驳论文字为据；Bosanquet 的观点均以"Bosanquet 声称…"转述，未直接引其原文（Bosanquet 原文不在本语料内）。
- **《Proposals》中"银优于金作标准"与《Reply》中"金是英国标准"看似矛盾**：已按年份与语境区分（1811 论战 vs 1816 方案），但这是立场演化还是措辞取舍，本语料不足以定论，下游引用时建议标注年份并避免跨文本断言。
- **"国家成为唯一纸币发行者"属激进主张**：文中明确以"可兑换 + 专员对议会负责"为前提，且当时银行章程至 1833 年方到期（书中自陈"为此银行在 1833 年前是安全的"）——即这是远景方案而非即时政策，引用时勿拔高为"当务之急"。
- **本道只读分配的两份 train 源**；`raw/` 下其余文件未读未引，属其他道分工。本道全部引文均出自分配的 train 源。
