# Conversations

## Scope and assigned sources

**本道分到 6 份（train split）**：

| source_id | 出版年 | tier | 题名 |
|---|---|---|---|
| `src-1d65d5b7b971` | 1758 | P1 | Des Herrn Benjamin Franklins Esq. Briefe von der Elektricität |
| `src-c6d006f2fb87` | 1760 | P1 | New experiments and observations on electricity. Made at P…er Collinson, Esq; ... Part I |
| `src-20bd8bdae405` | 1774 | P1 | The causes of the present distractions in America explaine…ondon. By F-----B-----.  1774 |
| `src-49c9874da84f` | 1774 | P1 | Scelta di lettere e di opuscoli |
| `src-724fbee3763e` | 1784 | P1 | Reflections on courtship and marriage: in two letters to a…alousy. By Mr. Addison.  1784 |
| `src-f06f440c725d` | 1787 | P1 | Observations on the causes and cure of smoky chimneys. By …ated by a copper-plate.  1787 |

★ 本节由台账机械导出（`emit_lane_scope.py`），**不含任何阅读判断**；只投影 `split == train` 的行。

## 22 条实测发现（逐份）

### src-c6d006f2fb87 · 致 Collinson 的电学书信（1760 版，英文）

#### ① 通信开场：自谦"不一定对您是新事"，把发现归功于欧洲同行也在做实验

Letter II（1747-09-01）正文里，他对 Collinson 报告新发现时的开场，先给自己"泼冷水"——称这些或许对您不算新鲜，因为您那边每天都在做电学实验：

> which we looked upon to be new, and of which I promifed to give you fome account, tho’ I apprehended they might poflibly not be new to you, as fo many hands aie daily employ d in electrical experiments on your fide the water, fome or other of which would probably hit on the fame obfervations
<!-- src-c6d006f2fb87 -->

[版口：OCR 讹形 "aie" 即 are、"employ d" 即 employ'd、"fide" 即 side、"fame" 即 same。]
⇒ 他面对科学界上位者（皇家学会会员、伦敦）时，开场姿态是"自我降格"：先承认对方阵营人才济济、撞见同样观察也属平常。这既是客套，也是一种诚实的学术登记——新发现可能已被他人同时做出，故下笔时自带保留。与同信后续详述具体实验的自信形成对照。

#### ② 协作式通信：主动请对方"提出要做的实验"，并明确求批评

Letter VI（致 C. C.［New York］，1751）——他读完对方来信的质疑后，主动把通信关系定义成双向实验协作：

> I will endeavour to make any new experi¬ ments you fhall propofe, that you think may afford far¬ ther light or fatisfadion to either of us ; and (hall be much obliged to you for fuch remarks, objections, &c. as may occur to you
<!-- src-c6d006f2fb87 -->

[版口：OCR 软连字符 "¬" 为原页折行符；"(hall" 即 shall。]
⇒ 他把书信往来当作科学进程本身：不仅汇报自己的结果，还主动承接对方提议的实验、并请对方把 remarks/objections 直接寄来。通信对方是平等合作者，不是读者。这是 18 世纪业余科学网络的典型声口。

#### ③ 热情与自我确信：电力的"力量无边界"，并附 Rabelais 式玩笑

同信（Letter VI）中他写下对电力潜力的乐观估计，末了引 Rabelais 打趣：

> Theie are no bounds (but what expence and labour give) to the force man may raife and ufe in the electrical way : For bottle may be added to bottle in infinitum, and all united and difeharged together as one, the force and effect proportioned to their number and fize
<!-- src-c6d006f2fb87 -->

[版口：OCR 讹形 "Theie" 即 There、"raife" 即 raise。]
⇒ 对实验能力的边界他有清醒核算——唯一限制是"费用与劳动"；同时带着"远超常人相信"的自我确信，并以 Rabelais 的魔鬼比喻（"只学会对着卷心菜打雷"）自嘲式地抬高己方成绩。落款风格为正式书信体：

> I am, with fmcere refpeSf, Totr mojl obliged humble fervant. B. FRANKLIN.
<!-- src-c6d006f2fb87 -->

[版口：OCR 讹形 "fmcere" 即 sincere、"refpeSf" 即 respect、"Totr" 即 Your、"mojl" 即 most、"fervant" 即 servant。]

#### ④ 对异议者的礼貌反驳：指对方"没细想就下笔"，但保留体面

Letter V（1750-07-27，仍致 Collinson，回应 Watson 的反对意见）：

> without having firft well confidered the experiments related §. iy. which ftill appear to me decifive in the queftion
<!-- src-c6d006f2fb87 -->

[版口：OCR 讹形 "firft" 即 first、"confidered" 即 considered、"§. iy." 即 §. 17、"ftill" 即 still、"decifive" 即 decisive、"queftion" 即 question（该处为字面 f 字符）。]
⇒ 他反驳科学界的异议时措辞克制而有锋芒：不说对方错了，只委婉说"恐怕对方没先细想"；随即坚定地重申自己实验的决定性。科学与面子的平衡——书面论辩中不撕破脸、但立场毫不含糊。

#### ⑤ 汇报公共性成果：把个人实验写成"给好奇者看的汇报"

Letter X（1752-10-19，风筝实验）的开场：

> it may be agreeable to inform the curious that the fame experiment has fucceeded in Philadelphia , though made in a different and more eafy manner, which is as follows :
<!-- src-c6d006f2fb87 -->

[版口：OCR 讹形 "fame" 即 same、"fucceeded" 即 succeeded、"eafy" 即 easy。]
⇒ 欧洲报纸已报道"费城实验"成功，他写信确认并强调本地用了"更简便的不同做法"——带着轻微的领先姿态，把个人/本地成果呈给伦敦通信圈。末署 "B. F."（简短缩写，说明信件对收信人而言不需要全名落款）。

#### ⑥ 与同行 Kinnersley 的往复：感谢、照办、并提出替代解释

Letter VIII/IX（1752，致 Boston 的 E. Kinnersley）：

> I Thank you for the experiments communicated. I fent immediately for your brimftone globe
<!-- src-c6d006f2fb87 -->

> In the mean time I fufped, that the different attractions and repulfions you obferved, proceeded rather from the greater or fmaller quantities of the fire
<!-- src-c6d006f2fb87 -->

> In halte, 1 am, &c. B. FRANKLIN.
<!-- src-c6d006f2fb87 -->

[版口：OCR 讹形 "fent" 即 sent、"brimftone" 即 brimstone、"fufped" 即 suspected、"repulfions" 即 repulsions、"obferved" 即 observed、"halte" 即 haste、"1 am" 即 I am。]
⇒ 对平辈同行（Kinnersley 是费城电学实验伙伴，非皇家学会成员），他的口吻更随和：先谢对方传来的实验，说已照办去取硫磺球来复现；同时不盲从，礼貌提出自己的替代解释（数量差异而非种类差异）。落款 "In halte, I am, &c." 是标准的快信体——用速度弥补正式度。

### src-1d65d5b7b971 · 致 Collinson 电学书信的德文译本（1758）

[版口：本档为同一批 1747 年致 Collinson 书信的德文译本，与 src-c6d006f2fb87 的英文 Letter I/II 为对照文本；故本源发现标注为"跨版口对照"，不重复计内容新发现，仅证明译本的通信声口与原英文一致。]

#### ⑦ Erster Brief 开场：抱怨"抄长信很烦"的自谦（德文）

> Der unvermeidliche Verdruß, welchen das Abſchreiben langer Briefe
<!-- src-1d65d5b7b971 -->

> hat mir den Muth, von dieſer Sache etwas mehreres zu ſchreiben, faſt halb benommen.
<!-- src-1d65d5b7b971 -->

[版口：德文；大意"抄写长信难免的烦扰几乎打消了我再写此事的勇气"——与英文 Letter I 同源。]
⇒ 德文译本的 Erster Brief 开场同样自谦：连"给您写信"都要先自我解嘲一下（怕写过去时您在电学上又前进了一步、读着没新意）。同一开场姿态跨语言稳定。

#### ⑧ Zweyter Brief：欧洲"许多手在做电学实验"的德文版

> Ich befuͤrchte aber faſt, daß Ihnen dieſelben nicht mehr neu vorkommen werden
<!-- src-1d65d5b7b971 -->

[版口：德文；大意"我几乎担心这些对您已不再新奇"——对应英文 Letter II 的 "I apprehended they might possibly not be new to you"。]
⇒ 同一句自谦在两种语言里都出现，可作为"通信开场必带 self-effacing 前缀"的稳定声口证据：他写给科学通信对象的每封信，几乎都以"怕您早知道"起头。

### src-f06f440c725d · 致 Ingen-Housz 的烟囱信（1787）

#### ⑨ 海上写信的私人开场：回应友人"把烟囱想法写下来"的请求

> one of your letters, a little before I left France, you defire me to give you, in writing, my thoughts upon the Conſtruction and Uſe of 'Chimneys 3 a ſubject you had ſometimes heard me touch upon in converſation.
<!-- src-f06f440c725d -->

[版口：OCR 讹形 "'Chimneys 3" 即 Chimneys；"3" 即分号 ";"（OCR 将 ; 误作 3）。]
⇒ 收信人是曾在对话里听他聊过烟囱、后来去信索要成文的友人（Ingen-Housz）。他把自己口头谈过的话题"应请求"落成文字——这正是"conversations"道的核心形态：私人对话/通信转化为正式著述的桥梁。

#### ⑩ 把私人请求升格为公益："既是对朋友的敬意，也可能对他人有用"

> I embrace willingly this leifure afforded:by: my preſent fituation, to comply with your requeſt, as it will not only ſhew my regard to the defires of a friend, but may at the ſame time be of ſotne utility to others
<!-- src-f06f440c725d -->

[版口：OCR 讹形 "leifure" 即 leisure、"afforded:by:" 即 afforded by、"preſent" 即 present、"fituation" 即 situation、"ſhew" 即 shew/show、"ſotne" 即 some。]
⇒ 他明确把"满足朋友请求"与"惠及他人"并列——私人通信在他手里天然向公共知识倾斜。同时点出写作动机的务实面：烟囱之理"尚未被普遍理解，误解导致不断的不便与白费的开销"（该句为改述，未逐字引用）。

#### ⑪ 在信里坦承"我以前错了"：以亲身体验修正旧观念

> I now look upon freſh air as a friend: I even fleep with an open window. I am perſuaded that no common air from without is ſo unwholeſome as the air within a cloſe room that has been often breathed and not changed
<!-- src-f06f440c725d -->

> here I am at this preſent writing, in a ſhip with above forty perſons, who have had no other but moiſt air to breathe for ſix weeks paſt
<!-- src-f06f440c725d -->

[版口：OCR 讹形 "freſh" 即 fresh、"fleep" 即 sleep、"perſuaded" 即 persuaded、"ſo" 即 so、"unwholeſome" 即 unwholesome、"moiſt" 即 moist。]
⇒ 这是"书信即自我修正"的实例：他先说自己从前把凉气当敌人、堵死所有缝隙，"经验已让我认错"（"Experience has convinced me of my error" 在原文前文，未逐字引用），现在开着窗睡觉，并在信中以"我正在一艘四十余人、六周只呼吸潮湿空气的船上，大家照样健康"的当下经验作证。论点直接来自个人处境——通信的即时性被他用作论证材料。

#### ⑫ 结尾的深情私人落款：友情多年不辍，"来世亦敬重你"

> I have great pleaſure in having thus complied with your requeſt, and in the reflection that the friendſhip you honour me with, and in which I have ever been ſo happy, has continued ſo many years without the ſmalleſt interruption
<!-- src-f06f440c725d -->

> my eſteem and reſpect for you, wy dear friend, will be everlaſting,
<!-- src-f06f440c725d -->

[版口：OCR 讹形 "friendſhip" 即 friendship、"ſmalleſt" 即 smallest、"eſteem" 即 esteem、"wy" 即 my。]
⇒ 这份写给科学家友人的信以极其私人化的深情收束：承认友情"多年毫无间断"，并说若来世尚有知觉与记忆，"我对你的敬重将永存"。它证明：即使纯技术性的科学通信，富兰克林也会在首尾保留完整的私人温度。另一处技术性段落他同样把社会效用挂上：修路、开运河让燃料便宜运入，"促进它们的人可被算作人类的造福者"（"thoſe who pro- mote them may be reckoned among the benefae- tors of mankind."，未作独立引文块）。

### src-724fbee3763e · 致友人的婚姻论书信（1784）

#### ⑬ 应友人辩论之约：确认"你有权问我"，再进入正题

Letter I 开场：

> You have an unqueſtionable right to aſk me? I wiſh my anſwer may prove ſatisfactory.
<!-- src-724fbee3763e -->

> Marriage, you know, was the topic of our cons... verſation, and the ſubject of our diſpute.
<!-- src-724fbee3763e -->

[版口：OCR 讹形 "unqueſtionable" 即 unquestionable、"aſk" 即 ask、"ſatisfactory" 即 satisfactory；"cons... verſation" 即 conversation（原页折行造成省略号）。]
⇒ 这封"婚姻反思"是友人间的哲学通信：对方因前一场争辩而成了"对两边都怀疑的人"，来信索取他的深思。他先承认对方的发问权、祝自己的答复能令人满意，再回顾"我们那天的辩论"——书信承接的是面对面对话的延续。

#### ⑭ 婚姻观的核心命题："没有友谊，爱情很快就会饿死"

> That love will ſoon ſtarve without friendſhip :
<!-- src-724fbee3763e -->

[版口：OCR 讹形 "ſoon" 即 soon、"friendſhip" 即 friendship。]
⇒ 这是他婚姻论的中心论旨之一：婚内幸福建立在判断力、审慎与好脾性上，爱情若缺友谊支撑会枯竭。以格言体下论断——书信中常把论点压成警句，便于友人记住与转述。

#### ⑮ 写给新婚少女的信：长者劝诫 + 婚姻即"寻一知己与真友"

信中另一封信体文本是"致一位新婚的年轻小姐"（A Letter to a very young Lady on her Marriage）：

> Jou are beginning to enter into a courſe of life, where you will want
<!-- src-724fbee3763e -->

> falling into ma- ny errors, foppeties, and follies, to which your ſex is ſubjectk
<!-- src-724fbee3763e -->

> wants a reaſonable companion, and a true friend,
<!-- src-724fbee3763e -->

[版口：OCR 讹形 "Jou" 即 You、"courſe" 即 course、"ſex" 即 sex、"subjectk" 即 subject；"ma- ny" 为原页折行。]
⇒ 对一位年轻女性，他以长辈口吻写信（"你正进入一段人生，需要很多忠告以防坠入你性别易犯的诸多错误、浮华与荒唐"），并以"明智的男人会厌倦扮演情人、把妻子当情妇对待，他要的是一个合宜的伴侣和一个真正的朋友"作为劝她"修养心智"的理由。此信佐证他书信对象覆盖面：不止科学界，也及于晚辈私交，且对之保持说教式亲切。

### src-20bd8bdae405 · 致伦敦商人的美国时局书信（1774）

#### ⑯ 向伦敦商人"转述"美国人想法的书信框架

> It is not my intention e this opi- nion; but perhaps it may be ſome ſatisfaction to you to know what ideas the Americans bave on the ſubject
<!-- src-20bd8bdae405 -->

[版口：OCR 讹形 "ſome" 即 some、"ſatisfaction" 即 satisfaction、"bave" 即 have。]
⇒ 面对身在伦敦的商人（对美贸易利益相关者），他先声明"无意争辩"，再以"您或许想知道美国人怎么想"为引子，把美国殖民地的立场娓娓道来。收信人是"要说服/要理解的对象"而非同党——这是政治书信的修辞：低姿态开场，实为向对方完整陈述己方理据。

#### ⑰ 政府治理观：对既有舆论要么说服、要么绕开，别硬碰

> they are to — changed before, we act againſt them, and they can nh be changed by reaſon and perſuaſion.— But if public ſervice can be carried on without thwarting thoſe opinions
<!-- src-20bd8bdae405 -->

[版口：OCR 讹形 "they are to — changed" 即 they are to be changed、"nh" 即 only（讹）；"againſt" 即 against、"perſuaſion" 即 persuasion。]
⇒ 他给伦敦商人讲治国之道：对民众既有且稳固的舆论，若妨碍公务须先设法改变（且只能靠理性与说服），若公务不妨、甚至能借力，就"没必要无端违背，无论那些意见多荒谬"（后半句为改述）。这是书信里夹杂的政论——把政治策略写成对收信人的教育性论述。

#### ⑱ 忠诚宣言与对"对议会的忠诚"的质疑

> we baye been reviled in their Senatg as rebels and traiters, we are truly a loyal people.
<!-- src-20bd8bdae405 -->

> But a new kind of loyalty ſeems to be required of us, a loyalty to Parliament; a loyalty that is to extend, it ſeems, to a ſur- render of all our properties, whenever a Houſe of Commons, in Which there is, not a ſingle member of our chooſing, ſhall think fit to grant them away without our conſent
<!-- src-20bd8bdae405 -->

> We were ſeparated too far from Britain by the ocean, but we were united ſtrongly to it by reſpect and love
<!-- src-20bd8bdae405 -->

[版口：OCR 讹形 "baye" 即 have、"Senatg" 即 Senate、"traiters" 即 traitors、"ſur- render" 即 surrender（折行）、"Houſe" 即 House、"chooſing" 即 choosing、"ſeparated" 即 separated。]
⇒ 他先替殖民地辩白"被骂作叛徒与卖国者，我们却是真正忠诚的人民"，随即抛出关键转折："现在似乎要我们效忠的是一种新的忠诚——对议会的忠诚"，并点破其荒谬：那是一个"没有一位我们选出的议员"的下议院可随时不经我们同意把财产授出。最后用"隔着大洋、却因尊敬与爱而紧紧相系"收束。这段话既在信里维护己方，也把殖民地的政治立场完整译给伦敦商人听。

#### ⑲ 收尾的修辞策略：先称"疯话"，再表达真诚的祝愿

> T do not pretend to ſupport or juſtify them
<!-- src-20bd8bdae405 -->

> for the fake of the mäfufactures and commerce of Great-Britain
<!-- src-20bd8bdae405 -->

[版口：OCR 讹形 "T" 即 I、"juſtify" 即 justify、"fake" 即 sake、"mäfufactures" 即 manufactures。]
⇒ 他刚陈述完美国人的强烈情绪（原文另处称那些是"近乎疯癫的美国人的狂言"，"To be sure no reasonable man in England can approve of such sentiments"，未作独立引文块），随即话锋一转：我无意支持或辩护这些言论，但我真心希望——为了大不列颠的制造业与商业、为了与成长中殖民地的牢固联盟——"那些人从未被如此不必要地逼出理智"（该句为改述）。这是极具代表性的书信修辞：以退为进，先把对方立场让足，再把自己的愿望以"为你们好"包装送出。

### src-49c9874da84f · 意大利文书信集（1774）

[版口：本档为意大利文译本；"Voi/voi" 为敬称，与德文/英文的"您"对应。]

#### ⑳ 久未通信的私交口吻：致歉 + 托人带信 + 引荐来客

首信（New York，1757-04-14，"SIGNORE"）开场：

> affai tempo, che io non ho pro» vato il piacere di ricever lettere da voi
<!-- src-49c9874da84f -->

> mi hanno refo così trafcurato nel rifpondere, che io non debbo afpettare efattezza ne- gli altri
<!-- src-49c9874da84f -->

[版口：意大利文；OCR 讹形 "pro» vato" 即 provato（意"感受到"）。大意："我已许久没收到您的信；时局动荡、公务缠身使我疏于回信，所以我也不能指望别人准时。"]
⇒ 即便写给科学通信对象，他的私人寒暄也毫不省略：先为长期未通信致歉、归因于"国中纷扰 + 事务缠身"，并自嘲"既然我都不准时，也不好要求别人准时"。随后说他即将登船赴英，趁此托信并引荐一位"有学问、有才干的绅士 Bouguet 上校"（"ed al tempo fteffo prendermi la libertà di farvi conofcere il Colonello Errico Bouguet, gentiluomo letterato, e di merito"）。书信在他手里同时是引荐媒介——把熟人介绍给另一地的熟人，扩展自己的社会网络。

#### ㉑ 科学谦逊的经典句：现象不会解释，"我只有些零散想法"

> Io non fo come debba effere fpiegato quefto fenomeno ; effo però mi porge occafione di proporvi alcune idee slegate
<!-- src-49c9874da84f -->

> a cui non ho tuttavia dato ordine
<!-- src-49c9874da84f -->

[版口：意大利文；大意"我不知道这现象该如何解释；但它给了我机会向您提出一些关于冷热的零散想法，我尚未给它们任何条理。"]
⇒ 向通信对象坦白"我不会解释"，同时把未成体系的思路大方交出——这正是他在科学书信里的标志性姿态：承认未知、分享半成品、把"整理出条理"当作后续工作。科学谦逊与产出欲并存。

#### ㉒ 好公民哲学 + 亲昵落款

> la pratica de’ doveri effenziali, fiamo degni di riprenfione
<!-- src-49c9874da84f -->

> un buon padre, un buon figlio, un buon ma- rito, una buona moglie, un buon vicino, od amico
<!-- src-49c9874da84f -->

> un buon fuddito o cittadino ,. cioè, in poche parole, un buon criftiano
<!-- src-49c9874da84f -->

[版口：意大利文；"de’" 即 dei；大意"若为精通自然之学问而荒废本质义务，则当受责难；自然之学中再没有比做个好父亲、好儿子、好丈夫、好妻子、好邻居或朋友、好臣民或公民——一言以蔽之，好基督徒——更值得、更重要的事了。"]
⇒ 一段科学信里冒出的人生观总结：自然哲学只是"装饰与利益"，不可侵占"本质义务"。同源的信末落款充满私交温度：

> Addio, mia. cara Amica, credetemi ognora Voftro affezionatiffimo B. Franklin.
<!-- src-49c9874da84f -->

> Addio, mia filofofeffina. Prefentate i miei com- plimenti pieni di rifpetto alle buone fisnore voftre zie, e a Madamigella Pitt; e credetemi ognora Voftro affezionatifs. amico, ed umile Servitore B. Franklin.
<!-- src-49c9874da84f -->

[版口：意大利文；"mia filofofeffina" 即"我小小的女哲学家"（戏称）；大意"再见，我的小女哲学家。请代我向您两位姑母和 Pitt 小姐致以敬意；永远相信您最深情的朋友与谦卑的仆人，B. Franklin。"]
⇒ 与女通信人（"小女哲学家"）的落款以戏称 + 请安代话收束——书信体在他笔下能同时在"正式敬称"（ed umile Servitore）与"亲昵戏谑"（mia filofofeffina）之间自由切换，显示其对收信人关系亲疏的精确拿捏。

## 这一道给下游的东西

- **稳定的书信开场仪式（self-effacing prefix）**：写给科学界上位者（Collinson）的多封信，开头几乎都以"这些也许对您不是新事 / 怕写过去已过时"的自谦起手（src-c6d006f2fb87 ①；德文译本 src-1d65d5b7b971 ⑦⑧ 平行复现）。可作人物"对话模型"的第一人称起始模板。
- **写信对象决定口吻梯度**：对皇家学会会员（Collinson）——正式、恭敬、自谦、落款 "Your most obliged humble servant"（①④⑤）；对平辈实验伙伴（Kinnersley）——随和、以"感谢+照办+替代解释"推进、落款 "In haste, I am, &c."（⑥）；对科学家友人（Ingen-Housz）——技术内容 + 私人深情的首尾（⑨⑫）；对友人与晚辈（婚姻书信）——说教式亲切与格言体（⑬⑭⑮）；对伦敦商人（政治书信）——低姿态转述 + 以退为进的修辞（⑯⑲）；对女通信人（意大利文）——戏称与亲昵（㉒）。**下游可直接用"对象→口吻"做人物在对话场景的行为分布。**
- **书信作为论证工具的三类用法**：a) 汇报成果/邀人做实验（②⑥）；b) 以亲历经验当场修正旧论（⑪，船上的潮湿空气）；c) 把私人请求升格为公共效用（⑩）。这些都是"书信体论证"的独有特征。
- **礼貌反驳的范式**：对 Watson 只说"恐怕没细想"、却重申己见决定性（④）——书面论辩中"不撕破脸 + 立场不让"的组合。
- **人格信条句**："没有友谊爱情会饿死"（⑭）、"做一家之主/好公民/好基督徒比精通学问更紧要"（㉒）、"力量无边界，只受费用与劳动限制"（③）、"只靠理性与说服改变舆论"（⑰）。这些可作第一人称格言库。
- **conversations 道的语言面**：同一批信有三种语言文本（英文 1760 版、德文 1758 版、意大利文 1774 版），口吻高度一致——自谦、礼貌、务实、把私人通信导向公共利益。下游引用德/意文时需知为译本，坐标注明语种与版口。

## 未做完 / 未核

- **src-c6d006f2fb87（英文电学书信）内还有大量 Letter I/III/IV 的技术正文**未逐字提取（如"正负电"的完整假说段、Letter IV "towards forming a new Hypothesis"、Letter XIII Kinnersley 云端实验汇报）；本道只取了开场/结尾/反驳/协作等"通信声口"切片，未穷尽。
- **src-724fbee3763e（1784 婚姻书信）OCR 质量最差**（大量噪声字符夹行，如 "3 1 am \"inclined ."、"10 fler my courſe 3/"、"T heſe are che wild ravings"），Letter I 结尾与部分段落无法得到干净的逐字引文，故改为改述或省略；"致新婚少女"信中段（关于礼仪/举止的具体劝诫）未逐一引用。
- **src-20bd8bdae405（1774 时局信）两封信的分界与各自落款**未核实——文件 OCR 噪声大、我未确认"两封信"的起讫页标，仅按正文连贯性取样；Letter 的完整签名/问候语未能引到。
- **src-1d65d5b7b971（德文）与 src-49c9874da84f（意大利文）** 均为译本，我只抽了与英文平行的开场/收尾句，未对德/意全本的每封信做通读比对；两档内的编者前言（如德文档论 Nollet 之争的前言、意大利文档的 Prefazione）系他人文字，**已排除在 Franklin 引文之外**，但未逐段确认哪些是 Franklin 原文哪些是编者文。
- 个别 OCR 讹形（如 "queftion" 实为字面 f 字符、"§. iy." 对应 §.17、"baye/reviled/Senatg"）已以 `[版口]` 注明，但按"逐字照录"原则未修正正文；下游转述时需知这些是 OCR 层噪音，不是富兰克林的原词原拼。
- 未对引文做"行内年份坐标"式标注（按本道约定仅以 source_id + 版口标注）；如需 `（src-XXX，YYYY 年）` 坐标格式，本道引文块后已带 source_id，年份可从版口/上下文补。
