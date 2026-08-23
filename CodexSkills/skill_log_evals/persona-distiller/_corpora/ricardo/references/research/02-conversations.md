# Conversations

## Scope and assigned sources

**本道分到 3 份（train split）**：

| source_id | 出版年 | tier | 题名 |
|---|---|---|---|
| `src-23315b56db3b` | 1887 | P1 | Letters to Thomas Robert Malthus, 1810-1823. Edited by James Bonar |
| `src-47d7fb0a92a7` | 1895 | P1 | Letters of David Ricardo to John Ramsay McCulloch, 1816-1823 |
| `src-eadbd44737d2` | 1903 | P1 | Three letters on the price of gold, contributed to the Mor…don) in August-November, 1809 |

★ 本节由台账机械导出（`emit_lane_scope.py`），**不含任何阅读判断**；只投影 `split == train` 的行。

## 19 条实测发现（逐份）

### ① 公开论战信的形式与署名：写给"编辑先生"、落款为 R.（Three Letters）

> I  am.  Sir,  your  obedient  Servant,
>
> R.

<!-- src-eadbd44737d2 -->

⇒ 三封信里后两封（1809-09-20、1809-11-23）是正式投给《晨报》编辑的信件，署名 "R."；第一封（1809-08-29）则是一篇未署名的短论《The Price of Gold》。编辑 Hollander 的导言称这组信"标志着 David Ricardo 作为经济学家与政论作者生涯的开端"（编者语，非 Ricardo 自述），且说明首篇发表后引来化名 "A Friend to Bank Notes but no Bank Director" 的反驳，由此触发三封信的来回（详见 ②）。用化名进入报刊论战而非实名出版，是他在论战中的一贯做法。

### ② 对论敌"A Friend to Bank Notes"的口吻：礼貌、不指名、先引述再驳

> I  did  not  apprehend,  any  more  than  your  Correspondent,  under  the  signature  of  "A  Friend  to  Bank  Notes,"  that  the  issues  of  the  Bank  would  involve  us  in  the  dangers  of  a  national  bankruptcy.

<!-- src-eadbd44737d2 -->

⇒ 他不点名攻击对手，始终称 "your Correspondent"，并主动表明自己与对方一样并不主张"国家破产"的极端论断——先把对方可能的最坏解读挡回去，再进入技术性论证。这种"先共情、后反驳"是他在报刊论战里的固定声口（对照 ④ 的"请对方亮牌"策略）。

### ③ 对法律与权威的独立姿态：连"最严厉、或许荒谬的法律"也敢评

>  notwithstanding  the  most  severe,  and,  perhaps,  absurd  laws,  when  it  becomes  greatly  the  interest  of  individuals  from  a  high  market  price  of  gold,  the  coin  will  be  melted  and  sold  as  bullion

<!-- src-eadbd44737d2 -->

⇒ 讲"熔化金币套利"时，他顺口把禁熔金银的旧法称作"最严厉、或许荒谬的法律"。对一个靠市场交易发家的银行贴现经纪来说，法律不是不可批评的神圣物；金价/币值由利益驱动，他毫不掩饰这一点。这也是他整场金价论战的基本立场：货币问题是经济学问题，不是法律问题。

### ④ 论争策略：拒绝卷入人身/串谋指控，把辩论锚在"谁的理论对"上

>  A  writer  in  The  Pilot  newspaper  has  been  pleased  to  suppose,  that  a  gentleman  who  has  written  in  your  paper  under  the  signature  of  "  Mercator,"  has  done  so  "  in  aid  or  in  imitation  of,  or  in  conjunction  and  conspiracy  with  me."

<!-- src-eadbd44737d2 -->

>  The  fact  can  of  itself  be  of  little  importance.  If  his  arguments  or  mine  or  weak,  let  him  shew  them  to  be  so

<!-- src-eadbd44737d2 -->

（"or weak"＝are weak 之 OCR 讹形照录。）⇒ 《Pilot》报指控某位署名 "Mercator" 的撰稿人是在与他合谋（或仿效他）写稿；他回应：这事实本身无关紧要，"你我谁的道理若站不住，请对方证明它站不住"，并澄清自己对 Mercator 一文的态度与他相同——都只是通过《晨报》看到对方的意见（"The  sentiments  of  'Mercator'  are  only  known  to  me  as  they  are  to  him,  through  the  medium  of  The  Morning  Chronicle"）。面对报刊人身攻击，他惯于把辩论锚在"谁的理论对"上、拒绝情绪化缠斗——这套"请对方亮牌"的论争策略在他日后《Reply to Bosanquet》里对最大对手用得最彻底（见 decisions 道）。

### ⑤ 论争的实质命题：金是价值标准，银行券超发即贬值

>  It  was  evident  from  the  tenor  of  that  and  the  subsequent  paper,  that  I  considered  Gold  Coin  as  the  standard  of  commerce,  and  by  it  estimated  the  depreciation  of  Bank-notes.

<!-- src-eadbd44737d2 -->

>  But  if,  as  I  shall  attempt  to  prove.  Gold  be  the  standard  of  value,  and  consequently,  Bank  Notes  the  representatives  of  the  Gold-coin,  I  do  expect  that  this  writer  will  agree  with  me  that  Bank  Notes  are  at  a  discount

<!-- src-eadbd44737d2 -->

（"prove.  Gold"＝prove, 之 OCR 讹形照录。）⇒ 三封信的主线论证是：金是英国的价值标准（援引 Lord Liverpool 的《On the Coins》与 1797 年贵族院报告），故市场金价高于造币厂价即等于银行券贬值。他还给对手留了台阶——"只要你承认金是标准，你自然会同意我的结论"；这种"从对方立论出发推导"的论证方式贯穿他与 Malthus、McCulloch 的全部书信（见 ⑥⑩⑯）。

### ⑥ 与 Malthus 的分歧焦点之一：永久原因 vs 暂时原因

>  one  great  cause  of  our  difference  in  opinion  on  the  subjects  which  we  have  so  often  d'mrmsod  is  that  yon  have  always  in  your  mind  the  immediate  and  temporary  effects  of  particular  changes,  whereas  I  put  these  immediate  and  temporary  effects  quite  aside,  and  fix  my  whole  attention  on  the  permanent  state  of  things  which  will  result  from  them.

<!-- src-23315b56db3b -->

（"d'mrmsod"＝discussed、"yon"＝you 之 OCR 讹形照录。）⇒ 他自己总结两人思维方式的分野：Malthus 盯"当前与暂时效应"，他"把暂时效应搁到一边，把全部注意力钉在由此产生的永久状态上"。这是 Ricardian 方法论的自我陈述——分析只认长期均衡，短期的扰动在他看来是噪音。同一封信里他还说这是"偏好的差异"（他可能过高估价了对方不愿让步的那一面），见 ⑪。

### ⑦ 分歧焦点之二：地租的本质——是转移而非创造

>  rent  is  not  a  creation  but  a  transfer  of  wealth.  It  is  the  necessary  consequence  of  rent  being  the  effect  and  not  the  cause  of  high  price

<!-- src-23315b56db3b -->

（句末原为脚注锚点 3，引文剔除脚注号、止于 "high  price"。）⇒ 论地租（1815 年前后，针对 Malthus 论租的三本小册子）他立场鲜明：地主所得不是社会新增财富，而是从他人处转移来的；地租是高价的结果而非原因（边际/差额地租论的核心表达）。他在信里同时批评 Malthus 的文章用词含糊、把"高地租是土地稀缺的结果"与"高地租是土地稀缺的原因"两种说法搅在一起。

### ⑧ 分歧焦点之三：普遍过剩（general glut）——"坚决反对"需求不足论

>  It  is  against  this  latter  doctrine  that  I  protest,  and  give  my  decided  opposition.

<!-- src-23315b56db3b -->

⇒ 论 Malthus《政治经济学原理》（1820–1821）时，Malthus 主张"生产过剩需要靠增加消费/非生产性消费来治"，Ricardo 坚决反对：生产若无充分动机就不会发生，因此不可能存在"已生产出来却无人愿买"的普遍停滞。他承认"可能没有足够的动机去生产，所以东西就不会被生产出来"，但否认会出现"带着充分动机生产出来后反而有害"的情形——Say 定律阵营的立场。

### ⑨ 分歧焦点之四：价值尺度——"从来没有、我想永远不会有完美的价值尺度"

>  There  is  no  such  thing;  your  measure  as  well  as  mine  will  measure  variations  arising  from  more  or  leas  labour  being  required  to  produce  commodities,  but  the  difficulty  is  respecting  the  varying  proportions  which  go  to  labour  and  profits.

<!-- src-23315b56db3b -->

>  for  these  variations  there  has  never  been,  and  I  think  never  will  be,  any  perfect  measure  of  value.

<!-- src-23315b56db3b -->

（"leas"＝less 之 OCR 讹形照录。）⇒ 价值尺度之争是 Malthus 通信最后一年（1823）的高潮。Ricardo 承认自己的劳动尺度并不完美，但认为对方的"劳动购买力"尺度同样不成立；他的落点是"绝对价值尺度并不存在，人人都只能找到在多数情形下适用、在其余情形下偏差不大的近似尺度"。他对自己的尺度有清醒的边界意识，却不容对方声称自己找到了绝对标准。

### ⑩ 争论不休却友谊不破：晚年价值论战的收尾自白

>  And  now,  my  dear  Mai  thus,  I  have  done.  Like  other  disputants,  after  much  discussion  we  each  retain  our  own  opinions.  These  discussions,  however,  never  influence  our  friendship ;  I  should  not  like  you  more  than  I  do  if  you  agreed  in  opinion  with  me.

<!-- src-23315b56db3b -->

（"Mai  thus"＝Malthus 之 OCR 讹形照录。）⇒ 这是整部通信集的最后一句实质内容（LXXXVIII，1823-08-31）。他在"各自保留己见"后特意声明：讨论从不影响友谊，"即使你同意我的意见，我也不会更喜欢你"——把智识上的寸步不让与私人感情彻底分开。同封信他前面刚写过"我并非闭眼拒绝被说服，只是你这命题若真如此清楚，我实在无法解释自己为何看不懂"（"I  hope  you  do  not  suspect  me  of  shutting  my  eyes  against  conviction"），可见两人论争的坦诚与互信。

### ⑪ 自我认知：理论偏重 vs 实际偏重，及其理由

>  If  I  am  too  theoretical  (which  I  really  believe  is  is  the  case),  you  I  think  are  too  practical.  There  are  so  many  combinations  and  so  many  operating  causes  in  Political  Economy  that  there  is  great  danger  in  appealing  to  experience  in  favour  of  a  particular  doctrine,  unless  we  are  sure  that  all  the  causes  of  variation  are  seen  and  their  effects  duly  estimated.

<!-- src-23315b56db3b -->

（"is  is"＝is 之 OCR 衍字照录。）⇒ 他承认自己"太理论"，但给出理由：政治经济学里有太多组合与作用原因，若不确认全部变异原因及其效应已被看清，诉诸经验就有危险。这是他为"抽象优先"辩护的经典段落——也直接解释了他对 Malthus"从牙买加商人、城里金银经纪那里找灵感"（Bonar 前言的概括）的不以为然。

### ⑫ 自我认知：写作与表达的"压缩病"

>  My  speaking  is  like  my  writing  too  much  compressed.  I  am  too  apt  to  crowd  a  great  deal  of  difficult  matter  into  so  short  a  space  as  to  be  incomprehensible  to  the  generality  of  readers.

<!-- src-23315b56db3b -->

⇒ 在讲银行股东大会（Bank Court）上自己被迫发言的经过时，他自嘲说话和写作一样"压得太紧"，容易把大量难题塞进太短的篇幅而让普通读者看不懂。这是罕见的自我批评式自述，和他"方法自白：想象强例"（⑬）一起勾勒出他对自己思维方式的自觉。

### ⑬ 方法自白：为阐明原理而"想象强例"

>  My  object  was  to  elucidate  principles,  and  to  do  this  I  imagined  strong  nssns  that  I  might  show  the  operation  of  those  principles

<!-- src-23315b56db3b -->

（"nssns"＝cases 之 OCR 讹形照录；句末原为脚注锚点 1，引文剔除脚注号。）⇒ 论 Malthus 批评他把书写得"比本意更实用"时，他澄清：自己的目的是阐明原理，为此会"想象强例"（如假设一次立刻让土地产量翻倍的农业改良），以展示原理在不受其他干扰时如何运作——这是他对"抽象模型/思想实验"方法的自我辩护，也是理解他全部论证风格的一把钥匙。

### ⑭ 对 Malthus 的尊重 + 个人生活音：Gatcomb 与家庭

>  The  general  impression  which  I  retain  of  the  book  is  excellent

<!-- src-23315b56db3b -->

（原文句末无句号，直连下句；"The  doctrines  appeared  so  clear  and  so  satisfactorily  laid  down  that  they  excited  an  interest  in  me  inferior  only  to  that  produced  by  Adam  Smith's  celebrated  work" 为紧接的续句。）⇒ 论《人口论》他留了极高的敬意（"只次于亚当·斯密名作"的激赏）；这与 ⑨⑩ 的寸步不让形成对照——他在理论上彻底独立，但对对手作为经济学家始终以礼相待。个人层面，他在 Gatcomb 乡居信里说：

>  I  believe  that  in  this  sweet  place  I  shall  not  sigh  after  the  Stock  Exchange  and  its  enjoyments.

<!-- src-23315b56db3b -->

（同信另句写他在"surrounded  by  upholsterers,  carpenters,  etc."——装修工人环伺下写信。）⇒ 这些书信里有大量这类生活细节：邀请 Malthus 全家、安排早餐会、抱怨布鲁克街的房子还在装修、向家人问好——通信的私人口吻非常浓，远非纯学术笔谈。

### ⑮ 与 McCulloch 的口吻：对"弟子"热忱鼓励 + 平等论争

>  We  shall  all  be  delighted  to  see  you,  and  shall  be  prepared  to  learn  with  docility  all  the  good  principles  which  you  are  to  teach  us.  You  have  already  done  much  for  the  good  cause

<!-- src-47d7fb0a92a7 -->

⇒ 对年轻 17 岁的 McCulloch，他的态度是长辈式的热情：邀请来乡居、请对方"以顺从之心来教我们好原理"，把他当作"好事业（指政治经济学与自由贸易）"的推进者。但当对方挑战他时，他又坚持平等互评：

>  I  promise  to  use  equal  freedom  with  you,  and  to  retain  my  own  expression  if  I  am  not  convinced  by  you.

<!-- src-47d7fb0a92a7 -->

⇒ 他请 McCulloch 自由挑出书中可改的段落，许诺"与你一样自由、不被你说服就保留原话"——对批评开放、但保留判断权，这与 ⑩ 对 Malthus 的"友谊不伤争论"是同一性格的两个侧面。

### ⑯ 机器章节论争：承认改口、与 Malthus 立场划清界线

>  The  whole  change  of  my  opinion  is  simply  this:  I  formerly  thought  that  machinery  enabled  a  country  to  add  annually  to  the  gross  produce  of  its  commodities,  and  I  now  think  that  the  use  of  it  rather  tends  to  the  diminution  of  the  gross  produce.

<!-- src-47d7fb0a92a7 -->

⇒ 第三版《原理》新增的"论机器"一章（承认机器可能减少总产量）让 McCulloch 大受震动，认为他背叛了正统。Ricardo 的回应是平静地交代改口内容、且表示"若被证明错了仍愿意再认错"；同时他坚决否认自己"向 Malthus 投降"：

>  Mine,  on  the  contrary,  is  that  the  use  of  machinery  often  diminishes  the  quantity.  of  gross  produce,  and  although  the  inclination  to  consume  is  unlimited,  the  demand  will  be  diminished  by  the  want  of  means  of  purchasing.  Can  any  two  doctrines  be  more.different?

<!-- src-47d7fb0a92a7 -->

（"quantity."、"more.different" 为 OCR 点号连排照录。）⇒ 他反复划清与 Malthus 的界线：Malthus 说机器让总产量大增、供过于求；他说机器常使总产量减少、消费欲无限但购买力不足。两人"都谈机器导致失业"，结论却相反——他很在意别人误把他和 Malthus 混为一谈。

### ⑰ 对价值尺度的困境自白：深陷迷宫

>  The  difficult  subject  of  value  has  engaged  my  thoughts  but  without  my  being  able  satisfactorily  to  find  my  way  out  of  the  labyrinth.

<!-- src-47d7fb0a92a7 -->

⇒ 1823-08-08 给 McCulloch 的信里，他承认价值难题"占尽心思却找不到出路"，甚至转寄 Malthus 的来信与自己的答复给 McCulloch 求"书面意见"。相比给 Malthus 写信时的寸步不让，这里他对更年轻的盟友更坦然地暴露困惑——两种关系下他流露自信与求索的不同面向。

### ⑱ 政策立场在通信中的口头表述：整体利益、节约、低价偏好

>  Laws  are  made  for  the  benefit  of  the  whole  community,  and  not  for  the  benefit  of  any  particular  class

<!-- src-47d7fb0a92a7 -->

>  every  guinea  that  is  spent  unnecessarily  I  think  is  a  public  wrong

<!-- src-47d7fb0a92a7 -->

⇒ 论玉米法与偿债基金时他讲原则：法律为全体社区而立，不为任何特定阶级；政府浪费的每个几尼都是"公共过错"（此语亦见他 1818 年致 McCulloch 信）。1822 年欧洲旅行的家信（该版编者在 McCulloch 信后附入）里，他把同一原则落到物价上：

>  if  the  scale  must  preponderate,  let  it  be  on  the  side  of  cheapness

<!-- src-47d7fb0a92a7 -->

⇒ 面对 1817 年饥荒与 1822 年丰收谷贱的反差，他主张"宁可偏廉价一边"——用具体观察（法国乞丐锐减、面包从 11 苏降到 3 苏）印证"低价对消费者最有利"。

### ⑲ 与弟子在"科学进步"上的同侪感（编者在导言中引述 Ricardo 语）

>  so  clear  an  exposition  of  all  the  important  principles  of  the  science  that  you  have  left  nothing  for  me  to  wish  for

<!-- src-47d7fb0a92a7 -->

⇒ 此句为编者在导言里引述的 Ricardo 对 McCulloch《百科全书》"政治经济学"条目的评语（Hollander 原文：Ricardo 写道"You have given so clear an exposition..."）。它说明：Ricardo 视 McCulloch 为自己的观点最忠实的阐释者，两人的通信在大部分议题上是"同门研讨"而非"对手论战"——与对 Malthus 的"分歧—友谊"关系形成另一极。

## 这一道给下游的东西

（可作为 persona 依据的通信声口与立场要点，均按「（src-XXX，年份）」标注；除注明外均出自 Ricardo 亲笔。）

- 公开论战声口（对报刊）：以化名 R. 上阵、礼貌地称对手 "your Correspondent"、先挡掉最坏解读再进入技术论证；拒绝卷入人身指控，要求对手"亮出自己的理论或指出事实"（src-eadbd44737d2，1809）。
- 论战主题：金是价值标准、银行券超发即贬值、市场金价高于造币厂价即贬值之证明（src-eadbd44737d2，1809）。
- 与 Malthus 的关系模式：理论上寸步不让、私人友谊牢固；晚年明言"讨论从不影响友谊，即使你同意我的意见我也不会更喜欢你"（src-23315b56db3b，1823）。
- 与 Malthus 的四个分歧焦点：① 永久 vs 暂时原因；② 地租是转移而非创造、是结果而非原因；③ 普遍过剩不可能（Say 定律）；④ 绝对价值尺度不存在（src-23315b56db3b，1814–1823）。
- 自我认知：自认"太理论"（对方"太实际"）、写作/说话"压得太紧"、方法上"想象强例"来阐明原理（src-23315b56db3b，1815–1820）。
- 对 Malthus《人口论》评价极高（仅次于亚当·斯密），对 Malthus 本人始终以礼相待（src-23315b56db3b，1816）。
- 对 McCulloch（年轻弟子）：热忱鼓励、平等互评、把对方当"好事业"（政治经济学与自由贸易）的推进者；对批评开放但保留判断权（src-47d7fb0a92a7，1816–1823）。
- 对机器章节的改口：承认"改口"但不承认"向 Malthus 投降"，坚持"机器常减少总产量"与 Malthus"总产量过剩"是两种相反学说（src-47d7fb0a92a7，1821）。
- 政策口头表述：法律为整体社区而非特定阶级而立；政府浪费的每几尼都是公共过错；物价偏廉一边对消费者有利（src-47d7fb0a92a7，1818–1822）。
- 私人口吻：书信里有大量生活细节（家庭、装修、乡居、互相探访），绝非纯学术笔谈；同时自称写作/发言都"太压缩"（src-23315b56db3b，1810–1823）。

## 未做完 / 未核

- **Malthus 书信扫描（letterstothomasr00ricauoft.txt）OCR 讹字率偏高**，个别经典段落在扫描页内已严重破损无法可靠逐字引用：如 1814-06-26 信里那句著名的"I never was more convinced of any proposition in Political Economy than that restrictions on importations of corn in an importing country have a tendency to lower profits"——扫描页中该句作"proposi-tion  in  l'..htical  Economy ... restrictions  on  ituporta-of  corn"，核心词被 OCR 毁掉，本道只能**改述**（称"他自陈生平再没有比'谷物进口限制会压低利润'更确信的命题"），未能引原文。若要逐字引，须换更高质扫描/转录源。
- **编辑层（非 Ricardo 亲笔）与亲笔的区分**：Three Letters 的导言与注释（Hollander）、Malthus 集的编者前言与脚注（Bonar）、McCulloch 集的导言（Hollander）均为编者语，只用作背景与交叉印证，不作为 Ricardo 声口直接证据。凡引用编者语（如 ⑭ 的 Bonar 警示、⑲ 的 Hollander 引述）已在文中标注。
- **"A Friend to Bank Notes but no Bank Director" 即 Hutches Trower 这一归属**只在 Three Letters 的编辑注释里出现（引 1899 年 Trower MSS 考证），非 Ricardo 文本；若下游要当史实用，需以该注释为据并注明是编者考证。
- **本道只读了分配的三个 train 源**；`raw/` 下其余文件（《Works》《Principles》《Economic Essays》等）未读未引，属其他道分工。本道全部引文均出自分配的 train 源。
- 书信缺页/残页（Bonar 前言注明有两处仅存残片、封缄破裂损字）可能导致个别句子引文不完整，引用时以原文为准。
