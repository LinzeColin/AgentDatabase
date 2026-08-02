#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Harvey #103 断言层。**按 v0.0.0.29/31 口径：账本事实一条不写。**"""
import hashlib, json, pathlib, sys
WS=pathlib.Path(__file__).resolve().parent/"ws-harvey/william-harvey"
S=json.loads((pathlib.Path(__file__).resolve().parent/"hv_srcmap.json").read_text(encoding="utf-8"))
NOW="2026-08-02T00:00:00Z"
W,BD,DG,DL=S["works_willis_1847"],S["demotu_body"],S["degen_exercises"],S["degen_later"]
RD,LT,PM,DE=S["riolan_disquisitions"],S["letters_9"],S["parr_montgomery"],S["dedications"]
AU,PR,PL,WL=S["aubrey_lives"],S["primrose_1630"],S["prelectiones_1886_DISPUTED"],S["willis_life_1878"]
E53,PP,DG51,RL=S["demotu_english_1653"],S["power_portraits_1913"],S["degeneratione_1651"],S["riolan_letters_1649"]
C_OWN="他本人著作（De Motu Cordis 正文、De Generatione、两篇 Riolan 驳论、献词）"
C_LET="九封书信（Willis 英译，含 Hofmann 那封的纽伦堡印本转录）"
C_CASE="临床件（帕尔尸检、蒙哥马利病例、遗嘱）"
C_OPP="同期具名对手（Primrose 1630、Riolan、Hofmann、Parisano）"
C_AUB="Aubrey《Brief Lives》（1651 年起当面所记）"
C_MOD="现代文献学（Willis 1878 传、Power 1913 图像志、1886 RCP 影印本序）"
rows=[]
def add(cat,claim,srcs,ctx,cl,fal,scope,conf,status="pattern",alts=()):
    rows.append({"claim_id":"clm-"+hashlib.sha256(claim.encode()).hexdigest()[:12],"claim":claim,"category":cat,
      "status":status,"source_ids":list(srcs),"counter_source_ids":[],"contexts":list(ctx),
      "evidence_clusters":list(cl),"falsifiers":list(fal),"time_scope":scope,"confidence":conf,
      "author_role":"distiller","created_at":NOW,"alternative_explanations":list(alts)})
# ── fact（人物事实，≥9；实写 24）────────────────────────────────
add("fact","**牛膀胱注水实验的判据是「漏不漏」。** 在一具绞刑犯尸体上、当着数位同行：扎住肺动脉、肺静脉与主动脉，切开左室，经腔静脉插管入右室，管口接一只牛膀胱「in the same way as a clyster-bag is usually made」，注入「the greater part of a pound of water」。结果：「not a drop of water or of blood made its escape through the orifice in the left ventricle.」改插肺动脉并扎住后：「a torrent of the fluid, mixed with a quantity of blood, immediately gushed forth from the perforation in the left ventricle.」",[LT,BD],["设计一次判定性实验","向不信的人演示"],[C_LET,C_OWN],["若在其著作中找到他以不可观察的理由裁定此争点，本条降级"],"约 1636 年前后",0.9,status="fact")
add("fact","**他指控盖伦与维萨里在这件事上纸上谈兵。** 两人都开出「在插入的管子上扎住动脉」这个实验来证明脉搏经动脉壁传导，而哈维写：「**neither Vesalius nor Galen says that he had tried the experiment, which, however, I did.**」他做出来的结果与教科书相反：扎住之下的部分仍然搏动，解开反而搏得更弱。",[RD,BD],["评估前人的实验是否真做过","设计对照"],[C_OWN,C_OPP],["若查到二人确曾记述亲手做过该实验，本条须改写"],"1649",0.88,status="fact")
add("fact","**定量论证的四组数字与它们服务的那一个论点。** 左室容量「two ounces, three ounces, one ounce and a half」；每搏排出四分之一至八分之一；半小时逾一千次搏动，「in some as many as two, three, and even four thousand」。由此得**十磅五盎司／二十磅十盎司／四十一磅八盎司／八十三磅四盎司**。**论证不是任一数字为真，而是每一个都超过全身血量，因此血必须回流。**",[BD,W],["用估算做归谬","评估一个量级论证"],[C_OWN,C_MOD],["若其原文以某一数字为准确值立论，本条须改写"],"1628",0.9,status="fact")
add("fact","**他为那个论证做了一次实测对照，并写明是自己做的。** 「in the sheep or dog, say that but a single scruple of blood passes with each stroke … in one half hour we should have one thousand scruples, or about three pounds and a half … but the body of neither animal contains above four pounds of blood, **a fact which I have myself ascertained in the case of the sheep**.」",[BD,W],["为估算找一个可验的分母","区分假设与实测"],[C_OWN,C_MOD],["若该句被证为编者补入，本条降级"],"1628",0.88,status="fact")
add("fact","**Hofmann 的指控原文**：说他把自然指为「a most clumsy and inefficient artificer」，让血反复回心是「uselessly spoiling the perfectly-made blood, merely to find her in something to do」。**哈维的回应是拒绝为一个自己从未提出的主张辩护**——请对方去看「my eighth and ninth chapters」，那里他「purposely omitted to speak of the concoction of the blood, and of the causes of this motion and circulation」。落款 **Nürnberg, 20 May 1636**。",[LT,W],["回应一个曲解你立场的批评","判断该不该应战"],[C_LET,C_OPP],["若查到他确曾主张过血的再熬煮，本条须改写"],"1636-05-20",0.9,status="fact")
add("fact","**纽伦堡当众演示之后，他放下解剖刀走人。** 他随 Arundel 伯爵使团到纽伦堡公开演示，Hofmann 不为所动。此节由 **Slegel 1650 年的序独立佐证**：「Neque tantum valuit Harveus, vel coram cum salutaret Hofmannum in itinere Germanico, vel literis.」",[W,WL],["面对说服不了的人","评估当面演示的限度"],[C_LET,C_MOD],["若找到他继续争辩的记载，本条须改写"],"1636",0.85,status="fact")
add("fact","**Riolan 让血穿过室间隔，哈维一句话打掉**：「I have nowhere assumed such a basis for my doctrine; **for there is a circulation in many red-blooded animals that have no lungs.**」他还诊断对方的动机是制度性的：Riolan 身为巴黎学院院长「was bound to see the physic of Galen kept in good repair … He has been playing the part of the advocate, therefore, rather than of the practised anatomist.」",[LT,RD,RL],["驳一个折中方案","分辨学术分歧与位置分歧"],[C_LET,C_OPP],["若 Riolan 的原文与此转述不符，本条须改写"],"1649",0.87,status="fact")
add("fact","**他对批评者的公开政策是不读也不答**：「**Detractors, mummers, and writers defiled with abuse, as I resolved with myself never to read them … so have I held them still less worthy of an answer.**」并接「It cannot be helped that dogs bark and vomit their foul stomachs, or that cynics should be numbered among philosophers.」**这条政策可核**：Primrose 1630 年——出版仅两年后的第一部公开攻击——**他终身没有回应**。",[RD,PR],["决定要不要回应攻击","评估沉默的代价"],[C_OWN,C_OPP],["若查到他回应过 Primrose，本条须改写"],"1630–1649",0.88,status="fact")
add("fact","**批评者的原话**：说他有「a vainglorious love of vivisections」，并讥讽他把「frogs and serpents, flies, and others of the lower animals upon the scene」搬上台面是「a piece of puerile levity」。",[RD],["理解当时对实验方法的抵触"],[C_OWN,C_OPP],["若该转述与原书不符，本条须改写"],"1649",0.82)
add("fact","**蒙哥马利开胸病例**：蒙哥马利子爵之子幼年坠伤左肋，胸腔留下永久开口；十八九岁间来到伦敦，**查理一世派哈维去核实**。哈维取下护板，「could readily introduce three of my fingers and my thumb」，并以**一手按心、一手按腕的时序判据**认出众人当作肺的东西是心尖；**随后把病人带到国王面前，让查理一世摸到一颗活人的心**。共同结论：心是无感觉的。",[PM,DL],["用一个判据分辨两个结构","把结论交给第三方复核"],[C_CASE,C_OWN],["若该病例被证为后世附会，本条须删除"],"约 1640 年代",0.87,status="fact")
add("fact","**托马斯·帕尔尸检（1635，传闻年 152）：他把死因归给伦敦，不归给年龄。** 肾多脂并有浆液囊肿其一「the size of a hen's egg」；肾与膀胱**无结石**；脾「very small」；脑「healthy, very firm and hard to the touch」。死因归于非自然因素骤变——被「the smoke engendered by the general use of sulphureous coal as fuel」污染的伦敦空气，对比他一生所居「open, sunny and healthy region of Salop」，加上改食「a table loaded with variety of viands」与烈酒。",[PM,W],["在多因中挑出可归责的那一个","抵抗「年龄解释一切」"],[C_CASE,C_OWN],["若原文把死因归于年龄，本条须改写"],"1635",0.88,status="fact")
add("fact","**致 Argent 院长的献词里同时装着优先权与政治计算**：「having now for **nine years and more** confirmed these views by multiplied demonstrations in your presence」；以及「I was greatly afraid lest I might be charged with presumption did I lay my work before the public at home, or send it beyond seas for impression, **unless I had first proposed its subject to you**.」",[DE,W],["为一个发现定年","在发表前处理机构关系"],[C_OWN,C_MOD],["若找到更早的可靠年份记载，本条须并陈"],"1628",0.9,status="fact")
add("fact","★ **「他 1616 年已有循环说」这条链是断的。** 1886 年皇家内科医学院影印本（Lumleian 讲席笔记，BL MS Sloane 230）的**编者序自己承认**：「A few, for the most part illegible, additions in red ink … have been omitted in the transcript」——**静默删去了后加的红笔批注**，而同一篇序又断言这份笔记是他首次提出循环之处。**用一份自承有删节的版本去支撑一个年份断言，不成立。** 本工作区改以 1628 年献词的「nine years and more」（约 1619 年起）为准。",[PL,DE],["为循环说定年","评估一份影印本能承载什么"],[C_MOD,C_OWN],["若 Whitteridge 1964 校订本可得且给出不同结论，本条须重估"],"1616 vs 1619",0.85,status="fact")
add("fact","**致查理一世的献词把心与王并置**：「The heart of animals is the foundation of their life, the sovereign of everything within them, the sun of their microcosm … The King, in like manner, is the foundation of his kingdom, the sun of the world around him, the heart of the republic.」",[DE,W],["理解其修辞与政治位置"],[C_OWN,C_MOD],["若该献词非其所撰，本条须改写"],"1628",0.88,status="fact")
add("fact","**查理一世为《De Generatione》提供实验动物**：他「had several exhibitions prepared of the punctum saliens in the embryo chick and deer, and … witnessed the dissections of many of the does which he so liberally placed at Harvey's disposal」。",[WL,DL],["理解其研究条件","评估王室支持的实质"],[C_MOD,C_OWN],["若该记载仅出于身后颂词，本条降级"],"1630 年代",0.8)
add("fact","**他承认自己从没看见过动静脉吻合**：「**I confess, I say, nay, I even pointedly assert, that I have never found any visible anastomoses.**」Willis 的编者判断更直白：「he never saw this transit; his idea of the way in which it was accomplished was even defective.」",[LT,WL],["承认一个理论缺口","评估他的证据完整性"],[C_LET,C_MOD],["若查到他声称看见过，本条须改写"],"1649–1651",0.88,status="fact")
add("fact","**他临终前六周拒绝重启研究。** 致 Haarlem 的 John Vlackveld，**1657-04-24**：「it is in vain that you apply the spur to urge me, at my present age, not mature merely but declining, to gird myself for any new investigation. **For I now consider myself entitled to my discharge from duty.**」同一封信里那句方法论：「**Nature is nowhere accustomed more openly to display her secret mysteries than in cases where she shows traces of her workings apart from the beaten path.**」",[LT,W],["决定何时收手","从异常个案入手"],[C_LET,C_OWN],["若查到他此后仍启新研究，本条须改写"],"1657-04-24",0.9,status="fact")
add("fact","**1642 年他的手稿被劫掠散失**——尸检记录、昆虫发育观察、比较解剖笔记。他对 Aubrey 说那部酝酿多年的《De insectis》被毁，「**was the greatest crucifying to him that ever he had in all his life**」。**因此「他没写过 X」这类否定断言在他身上格外不可靠。**",[AU,WL],["评估一条否定断言","理解其著作的缺口"],[C_AUB,C_MOD],["若那批手稿被寻回，本条须重估"],"1642",0.87,status="fact")
add("fact","**出版的职业代价是可核的**：Aubrey 记「after his booke of the Circulation of the Blood came-out, that he fell mightily in his practize, and that 'twas beleeved by the vulgar that he was crack-brained; and all the physitians were against his opinion, and envyed him.」并记其处方难懂：「I knew severall practisers in London that would not have given 3d. for one of his bills.」",[AU,WL],["评估发表一个反常识结论的代价","决定要不要发表"],[C_AUB,C_OPP],["若找到同期反证其执业未受影响的记载，本条须并陈"],"1628 之后",0.82)
add("fact","**Aubrey 记的三句原话**：论培根（他曾是其医）「'He writes philosophy like a Lord Chancelor,' said he to me, speaking in derision; 'I have cured him.'」；1651 年论读书「he bid me goe to the fountain head, and read Aristotle, Cicero, Avicenna, and did call the neoteriques shitt-breeches」；自评「He was wont to say that man was but a great mischievous baboon.」",[AU,WL],["模仿其口吻","理解其对同代人的评价"],[C_AUB,C_OWN],["若 Clark 版校勘指出这些系后人窜入，本条须删"],"1651 前后",0.85,status="fact")
add("fact","**1642-10-23 埃奇山**：受托看顾王子与约克公爵，「he withdrew with them under a hedge, and tooke out of his pockett a booke and read; but he had not read very long before a bullet of a great gun grazed on the ground neare him, which made him remove his station.」",[AU,WL],["理解其性情","为其生平定年"],[C_AUB,C_MOD],["若同期文书与此冲突，本条须并陈"],"1642-10-23",0.83,status="fact")
add("fact","**任职时序与具名前任**：1604 年入皇家内科医学院候选册，1607 年 Fellow；1609 年初以国王荐书与院长 **Dr Adkinson** 的证明，谋 **Dr Wilkinson** 所任圣巴塞洛缪医院医师之缺；Wilkinson 去世后 **1609-10-14 正式当选**。1615 年受任讲席（该讲席由 **Dr Richard Caldwal** 创设），**1616 年 4 月开讲**。",[WL,W],["为其职业生涯定年"],[C_MOD,C_OWN],["若学院档案给出不同日期，以档案为准"],"1604–1616",0.85,status="fact")
add("fact","**1653 年首个英译不是他授权的**：「Printed by **Francis Leach** for **Richard Lowndes** at the White Lion in St Paul's Churchyard」，**译者匿名**，且与 Zachariah Wood 的序、James de Back 的《心论》装订在一起。引英文时须标明用的是哪一版。",[E53,W],["引用其英文时","判断一段英文是不是他的话"],[C_OWN,C_MOD],["若查到他授权该译本，本条须改写"],"1653",0.86,status="fact")
add("fact","**Aubrey 说 George Ent 把两部书从英文译成拉丁文——这条已被驳倒。** Willis 按年代：Ent 生于 1603，《De Motu Cordis》写于 1619 时他 16 岁、1628 年付印时 25 岁；且 Ent 自己的献词只说他校了印：「As our author writes a bad hand, which no one without practice can easily read, I have taken some pains to prevent the printer committing any very grave blunders through this.」**由此得一条用源规则：Aubrey 论其为人一流，论其书目不可靠。**",[AU,WL],["判断 Aubrey 的哪些话可用","核一条流行的归属说法"],[C_AUB,C_MOD],["若发现支持 Ent 代译的一手证据，本条须改写"],"1628 / 1847 驳",0.86,status="fact")
# ── mental-model / heuristic ──────────────────────────────────
add("mental-model","**把说不清的争点换成一个当场可见的二值结果。** 牛膀胱注水那一段，全部论证压在「左室切口漏不漏」上；扎肺动脉之前不漏，之后血水涌出。**判据先定，再动手。**",[LT,BD],["设计一次判定性实验","面对一个各说各话的争论"],[C_LET,C_OWN],["若其主要论证依赖不可当场观察的推理，本条降级"],"1628–1649",0.88)
add("mental-model","**当直接观察够不着时，用量级归谬。** 他看不到血从动脉回到静脉，于是改算：无论取哪一组数字，半小时的排出量都超过全身血量，**所以血必须回流**。**结论不靠任一数字为真，靠所有数字都指向同一边。**",[BD,W],["证据不足以直接证明时","评估一个估算论证"],[C_OWN,C_MOD],["若他以某一数字为准确值立论，本条降级"],"1628",0.9)
add("mental-model","**把「老师教的结构」与「老师给的解释」分开。** 静脉瓣是 Fabricius 教给他的；他保留了结构，换掉了功能。**接受一个观察，不等于接受随它而来的说法。**",[BD,WL],["处理师承","评估一条传下来的解释"],[C_OWN,C_MOD],["若他并未沿用 Fabricius 的观察，本条须改写"],"1602–1628",0.84)
add("mental-model","**能不能自己做过，是引用一条实验时的第一个问题。** 他对盖伦与维萨里的指控不是「你们错了」，是「**你们没说自己做过，而我做了**」。",[RD,BD],["引用他人实验","评估一条教科书结论"],[C_OWN,C_OPP],["若他也曾引用未经自验的实验作证，本条降级"],"1649",0.86)
add("heuristic","**先定判据，再动手**：写下「出现什么就算你对、出现什么就算我对」，写不出来就先别做实验。",[LT,BD],["设计实验","裁一个争论"],[C_LET,C_OWN],["若其实验多为探索性而无预设判据，本条降级"],"1628–1649",0.86)
add("heuristic","**直接证不了就换量级**：算出一个所有取值都指向同一边的估算，比争论某个精确值更快。",[BD,W],["证据不足","面对不可直接观察的过程"],[C_OWN,C_MOD],["若量级论证在其著作中罕见，本条降级"],"1628",0.85)
add("heuristic","**引一条实验前先问「他说自己做过吗」。** 说没说过做过，与做没做过是两件事，但前者可核。",[RD,BD],["引用文献","评估一条传统结论"],[C_OWN,C_OPP],["若此问在其著作中未成惯例，本条降级"],"1649",0.84)
add("heuristic","**承认自己没看见的那一环，并且说清楚。** 「I have never found any visible anastomoses」——把缺口写在结论旁边，而不是绕开。",[LT,RD],["发表一个不完整的结论","被问到一个你没验证的环节"],[C_LET,C_MOD],["若他在别处宣称看见过，本条须改写"],"1649–1651",0.86)
add("heuristic","**归因时先排除环境再谈体质**：帕尔的死因他归给伦敦煤烟与骤改的饮食，不归给一百五十二岁。",[PM,W],["面对一个「显然是年龄/体质」的解释","做尸检归因"],[C_CASE,C_OWN],["若其他病例中他优先归因体质，本条降级"],"1635",0.83)
add("heuristic","**从异常个案入手**：「Nature is nowhere accustomed more openly to display her secret mysteries than in cases where she shows traces of her workings apart from the beaten path.」蒙哥马利那个开着胸腔的年轻人，就是这条的实例。",[LT,PM],["选择研究对象","面对一个罕见病例"],[C_LET,C_CASE],["若他明确回避异常个案，本条须改写"],"1640 年代–1657",0.87)
add("heuristic","**不与骂你的人辩。** 他写下不读也不答的政策，并对第一部公开攻击（Primrose 1630）**终身沉默**。**代价也一并记下**：沉默让攻击独占了两年的公共记录。",[RD,PR],["决定要不要回应攻击","评估长期沉默的代价"],[C_OWN,C_OPP],["若查到他回应过 Primrose，本条须改写"],"1630–1649",0.85)
# ── boundary / blind-spot / others ─────────────────────────────
add("boundary","**不给任何个体化诊疗建议**——处方、剂量、方案一律不给。其体系仍在十七世纪的生理学框架内。本产物提供推理方式，不是医疗。",[BD,PM],["用户询问诊疗","用户询问用药"],[C_OWN,C_CASE],["硬边界，不接受降级"],"全时段",0.95,status="fact")
add("boundary","★ **不得对他作否定断言。** 1642 年他的手稿被劫掠散失（尸检记录、昆虫发育观察、比较解剖笔记）——**「他没写过 X」在他身上格外不可靠**：不在存世著作里，可能只是毁于那一次。",[AU,WL],["回答「他有没有研究过 X」"],[C_AUB,C_MOD],["硬边界，不接受降级"],"全时段",0.9,status="fact")
add("boundary","**三件不得当作他的话使用**：Prelectiones（1886 影印本自承删节，**不得承载年份断言**）、《De Motu Locali Animalium》（在版权内、本工作区无法核对任何一句）、1653 年匿名英译（非其授权）。",[PL,E53],["引用其文本"],[C_MOD,C_OWN],["硬边界，不接受降级"],"全时段",0.9,status="fact")
add("blind-spot","**九封书信全部隔着 Willis 的英译**——他自序即言「The Letters … have never appeared in English before」，英文是他自己译的；**Hofmann 那封更只存于纽伦堡的一部印本，非亲笔**。凡引书信原话，须标明这一层。",[LT,W],["引用其书信","评估一句「他说」的强度"],[C_LET,C_MOD],["若拉丁原件可得，本条须重估"],"全时段",0.87)
add("blind-spot","**Aubrey 是本产物口语材料的唯一来源，而他的书目类陈述已被证伪一次**（Ent 代译说）。**论其为人可用，论其书目不可用**——这条分界必须在每次引用时执行。",[AU,WL],["引用 Aubrey","判断一条轶事能不能用"],[C_AUB,C_MOD],["若出现第二份同期口语记录，本条须重估"],"全时段",0.85)
add("contradiction","**他要求「你说自己做过吗」，而他自己最关键的一环没看见。** 他指控盖伦与维萨里没做过实验就写；同时承认「I have never found any visible anastomoses」——**动静脉如何连通，他是推出来的不是看出来的**。两者在他体系内并存。",[RD,LT],["评估其方法的自洽性","理解他为何仍被接受"],[C_OWN,C_LET],["若查到他声称观察到吻合，本条须改写"],"1628–1651",0.85)
add("epistemic","**「他 1616 年已有循环说」不成立于现有证据。** 支撑它的 1886 年影印本自序承认删去红笔批注；本工作区改以 1628 年献词的「nine years and more」为准（约 1619 年起）。**Whitteridge 1964 校订本在版权内、无法取得，故此点在本工作区无法从一手证据裁定。**",[PL,DE],["为循环说定年","评估一份二手影印本"],[C_MOD,C_OWN],["若 Whitteridge 版可得，本条须重估"],"1616–1628",0.85,status="fact")
add("value","**发表前先把话说给能验证的人听。** 「nine years and more … in your presence」——他先在学院同人面前反复演示了九年，才把书交出去。",[DE,W],["决定何时发表","建立可核的优先权"],[C_OWN,C_MOD],["若查到他并未做过这些演示，本条须改写"],"1619–1628",0.85)
add("work-method","**做法是：先在活体与尸体上反复演示 → 把判据压到二值 → 直接观察不到的那一环用量级归谬补 → 缺口写在结论旁边 → 发表后不与骂你的人辩。**",[BD,LT,RD],["组织一次长期研究","决定研究的收口方式"],[C_OWN,C_LET],["若其著作显示他跳过演示直接下结论，本条降级"],"1619–1651",0.86)
add("soul-hypothesis","**假说（非事实）**：把「不与骂你的人辩」与「缺口写在结论旁边」看作同一种态度的两面——**他把辩护的责任交给证据，而不是交给自己**。标为假说：语料中没有他本人把这两件事联系起来的表述。",[RD,LT],["理解其动机"],[C_OWN,C_LET],["若找到他解释为何不回应批评的段落，本条可升为 pattern 或删除"],"全时段",0.45,status="hypothesis",alts=["不回应也可能只是宫廷医师的处世谨慎，与认识论无关","承认缺口可能是修辞策略——先自曝短处以取信","两者可能分属不同时期，并非同一态度"])
def main():
    p=WS/"evidence/claims.jsonl"
    p.write_text("\n".join(json.dumps(r,ensure_ascii=False,sort_keys=True) for r in rows)+"\n",encoding="utf-8")
    from collections import Counter
    print(f"写入 {len(rows)} 条：{dict(Counter(r['category'] for r in rows))}")
    ids=[r["claim_id"] for r in rows]; assert len(set(ids))==len(ids)
    return 0
if __name__=="__main__": sys.exit(main())
