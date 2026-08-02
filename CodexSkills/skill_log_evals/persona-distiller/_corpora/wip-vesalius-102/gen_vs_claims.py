#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Vesalius #102 断言层。**按 v0.0.0.29 口径：账本事实一条不写。**

Galen #101 三轮真基线盲测 −0.1944 / −0.1259 / −0.1456 不入库，
第 3 轮补的 15 条 fact 里有 5 条是语料统计（多少部、多少词）——
**那是账本不是知识**。本人物的 fact 类**全部是关于这个人的**：
具名对手说过什么、他在哪一年做了什么、他纠正了什么、他自己承认了什么。
"""
import hashlib, json, pathlib, sys
WS = pathlib.Path(__file__).resolve().parent / "ws-vesalius/andreas-vesalius"
NOW = "2026-08-02T00:00:00Z"
S = json.loads((pathlib.Path(__file__).resolve().parent / "vs_srcmap.json").read_text(encoding="utf-8"))
T1, T2 = S["opera_t1_1725"], S["opera_t2_1725"]
F43, F55 = S["fabrica_1543"], S["fabrica_1555"]
P43, P55 = S["praefatio_1543"], S["praefatio_1555"]
CR, BL, EX = S["chinaroot_1546"], S["bloodletting_1539_lat"], S["examen_1564"]
SY, PU, FA = S["sylvius_depulsio_1551"], S["puteus_apologia_1562"], S["falloppio_observ_1561"]
H2, LA, RO = S["henri2_relation"], S["languet_1565_nlm"], S["roth_1892"]
GE, VA, EP = S["geminus_1545"], S["valverde_1556"], S["epitome_1543"]
C_SELF="他本人的签名著作（Fabrica/Epitome/China Root/Examen/放血书信）"
C_VITA="Boerhaave & Albinus《Vita Vesalii》(Opera omnia 1725)"
C_OPP="同期对手的署名著作（Sylvius 1551、Falloppio 1561、Puteus 1562）"
C_DOC="同期文书与目击记述（亨利二世案、Languet 书信 1565）"
C_MOD="现代文献学（Roth 1892、Feyfer 1914、Jones 1943）"
rows=[]
def add(cat,claim,srcs,ctx,cl,fal,scope,conf,status="pattern",alts=()):
    rows.append({"claim_id":"clm-"+hashlib.sha256(claim.encode()).hexdigest()[:12],"claim":claim,
        "category":cat,"status":status,"source_ids":list(srcs),"counter_source_ids":[],
        "contexts":list(ctx),"evidence_clusters":list(cl),"falsifiers":list(fal),
        "time_scope":scope,"confidence":conf,"author_role":"distiller","created_at":NOW,
        "alternative_explanations":list(alts)})
# ── fact：全部是关于这个人的（≥10 条，实写 20 条）─────────────────
add("fact","**他刻意不写自己画师的名字。** 1725 年的 Vita 记得很直白：「Sculptorem quoque suum commemorat ibidem, non nominat」——他在那里提到了自己的雕版师，却不提名字。**归到 Jan van Calcar 是后世推断，不是他本人的证词。**",[T1,S["jones_artists_1943"]],["图版归属","评估「Calcar 画的」这个说法"],[C_VITA,C_MOD],["若找到他本人写出画师姓名的段落，本条须改写"],"1543–1555",0.9,status="fact")
add("fact","**他为画师的事苦不堪言。** 他记下自己被他们烦到在绝望中觉得比送上解剖台的尸体还不如；要把顶尖画师推去画绞刑犯的尸体极费周折——那些人「qui solam spirantem et Gratiis cinctam Venerem amant」——只爱呼吸着的、被美惠三女神束腰的维纳斯。",[T1],["理解图版的制作代价","评估其合作方式"],[C_VITA,C_SELF],["若这段被证为编者润色而非其自述，本条降级"],"1540 年代",0.82)
add("fact","**他自费赎回木版，宁可白送印工也不让它们被改小。** 1725 Vita 记他把自费赎回的版子无偿给印工，甚至再贴一份礼，以免被改动缩小开本弄坏。",[T1],["理解他对图版完整性的执着"],[C_VITA,C_SELF],["若找到他出售版子的记载，本条须改写"],"1543 之后",0.8)
add("fact","**木版是经米兰的 Danoni 商行运到巴塞尔的，与 Nicolaus Stopius 一同打包**——Bomberg 商行「最忠实的代理人」、一位精通人文学的年轻人。收件人是巴塞尔希腊语教授 Johannes Oporinus。",[F43,T1],["还原出版链条","评估他对细节的记录习惯"],[C_SELF,C_VITA],["若发现另一条运送路径的记载，本条须并陈"],"1542",0.85,status="fact")
add("fact","**Fabrica 完成于 1542 年八月朔日（Kalends of August），其时双亲俱存；Epitome 于同年八月望日（Ides of August）题献给查理五世之子腓力**；均在帕多瓦。",[T1,EP],["为其著作定年","理解两书的先后"],[C_VITA,C_SELF],["若初版扉页给出不同日期，以扉页为准并改写本条"],"1542",0.88,status="fact")
add("fact","**皇帝在 1539 年 1 月之前就看过图版。** 其父 Andreas（查理五世的药剂师）把图版呈给皇帝，皇帝饶有兴味地逐幅细问；**御医 Nicolaus Florenas 去信告知他，图版深得陛下与显贵赞许**。",[T1,BL],["还原其早期声望的建立","理解其家族的宫廷渠道"],[C_VITA,C_SELF],["若该通信被证为后世附会，本条降级"],"1538–1539",0.78)
add("fact","**1539 年 1 月他还卡在肌肉上。** 他写道图版获认可后神经的两幅已成，但肌肉与内脏的图尚未完成，遍寻便法而不得——「只要有尸体的机会、加上 Johann Stephan 那只熟练的右手来帮忙」。",[T1],["理解 Fabrica 的成书过程","评估他与画师的实际分工"],[C_VITA,C_SELF],["若找到他独立完成图稿的记载，本条须改写"],"1539-01",0.8)
add("fact","**Sylvius 的原话是「Vaesanus quidam ac arrogantissimus simul ac rerum omnium ignorantissimus transfuga」**——某个疯子、既极其傲慢又对一切极其无知的叛徒；并指其违背希波克拉底誓词中尊师一条，声明「nihil unquam illi quicquam respondere」永不回答他一句。",[SY],["理解他所受的攻击强度","评估同期学界的反应"],[C_OPP,C_SELF],["若该文被证非 Sylvius 所作，本条须改写"],"1551",0.9,status="fact")
add("fact","**Sylvius 开出的和解条件是要他把责任推给自己的年少或推给意大利人。** Sylvius 写道他在课上力求学生不会察觉自己在责难维萨里，因为他爱他、想留他做朋友——**前提是**维萨里为盖伦洗清不实之罪，把过错归于自己的 pubertas（年少）或归于敌视盖伦的意大利人之热心。并加了一句威胁：**即使他自己沉默，「墙也会说出他对我劳作的看法」**。",[T2,SY],["理解那场争论的政治面","评估他为何不接受和解"],[C_OPP,C_SELF],["若找到他接受这一条件的表态，本条须改写"],"1540 年代",0.85)
add("fact","**蝶骨之争里他拒看过一具标本。** 据 Sylvius：维萨里称蝶骨上的孔像是人为钻的、天然并不存在；**Sanctangelus** 提供过一具极新鲜的男孩骨骼，经**御医 Cornelius Baersdorpius** 转送，而他「不屑一看」。Sylvius 给出反测试：在新鲜颅骨蝶骨孔上方钻孔、用芦管灌水，会看见水流进鼻腔与腭孔。",[SY],["评估他是否也会拒绝证据","理解具体争点"],[C_OPP,C_SELF],["若找到他查验该标本的记载，本条须改写"],"1540 年代",0.8)
add("fact","**Falloppio 同时给了最高的赞与具体的责。** 称 Fabrica 为「divinum hoc Vesalii monumentum」、说绝大部分争议点上自己倒向「神圣的维萨里」并至今如此；但责其「veluti exercitus victoriae ardore ac impetu」——**如军队被胜利之热与冲力驱使**——抓盖伦的字而非意，在文本残缺处不为他开脱，苛责得「比一位如此卓越的解剖学家、哲学家与医师所应有的更不体面」。",[FA],["评估其论战方式的代价","理解同代最强同行的判断"],[C_OPP,C_SELF],["若该段被证为后人窜入，本条降级"],"1561",0.88,status="fact")
add("fact","**他承认过怕被抢先。** Examen 开篇：Falloppio 的书经布鲁塞尔医师 Aegidius Dux 转来，他搁下一切一口气读完，并承认「non levi metu, ne quis illa pro suis venditet」——**不轻的恐惧，怕有人把这些当成自己的兜售**。同处他说 Falloppio 现在占的帕多瓦教席「我曾任职将近六年」。",[EX,T2],["理解其竞争心态","为其帕多瓦任期定年"],[C_SELF,C_OPP],["若找到他否认此种顾虑的表述，本条须并陈"],"1564",0.87,status="fact")
add("fact","**人的下颌是一块骨不是两块**——Fabrica 卷一：「hactenus nulla hominis maxilla mihi gemino constructa osse … occurrit」，至今没有一具双骨下颌落到我手里。即便在某个侏儒或小童身上见到，他也不会断言人颌是双的；他站到 Celsus 一边——那位「cum Galeno canes parum curans」不像盖伦那样在意狗的作者。**并指出「儿童期由两骨合成」不能作证据，否则枕骨、椎骨、骶骨两侧的骨都得算「若干块」。**",[F43,T1],["评估他反驳盖伦的具体方式","理解他的论证纪律"],[C_SELF,C_VITA],["若在其著作中找到相反表述，本条须并陈"],"1543",0.86,status="fact")
add("fact","**他用眼睛的颜色论证盖伦解剖的是牛不是人**：盖伦所述葡萄膜内区的绿、蓝、深黑三色见于牛而不见于人。他自称此为「hoc meum Paradoxum」。**而同一封信里他承认自己课堂上一直用牛眼**——「Ego sane in scholis bovinos oculos semper exhibui」，因为人眼在解剖中太软太小；私下解剖时他也做人眼，「not once」。",[CR,T2],["评估其论证的自洽性","理解他自己的教学实践"],[C_SELF,C_OPP],["若该自承段落被证为他人窜入，本条降级"],"1546",0.87,status="fact")
add("fact","**他指出盖伦在《论身体各部分的用处》里把颞肌与咬肌讲错，后在《解剖操作》里自行改正却从不提前书**；并指出「in poplite latitans」那块腘窝肌是盖伦写前书与《解剖操作》前几卷时所不知的——那几卷「qui incendio perierant」毁于火。论头部运动的肌肉，他说自己确信「Galenum hallucinatum esse」盖伦看花了眼。",[CR,T2],["理解他如何指认前人错误","评估其文本比对能力"],[C_SELF,C_OPP],["若这些指认被现代校勘推翻，本条须改写"],"1546",0.82)
add("fact","★ **他没有推翻心室间隔。** 1543 与 1555 两版讲右室到左室的血流时他都让盖伦的说法照旧成立，只插了一句括号「quantumvis interim haec nobis sit obscurissima」——然而这一点对我们极其晦暗。**「维萨里推翻了间隔」是后世压平出来的说法**；真正指出隔不可透的是伊本·纳菲斯（13 世纪），塞尔维特 1553、科隆博 1559 续之。",[T1,F55],["回答「他推翻了什么」","纠正流行说法"],[C_SELF,C_VITA],["若在 1543 或 1555 正文中找到他明确否认间隔可透的段落，本条须改写"],"1543–1555",0.9,status="fact")
add("fact","**他把尸体搬进自己卧室，留三周以上。** 他请地方官把死刑执行推迟到适合解剖的时候；督促学生守着下葬以便抢出尸体；把绞刑犯或掘出的尸体带回自己房间，「per tres et ultra septimanas」。",[T1],["理解其取材方式与代价"],[C_VITA,C_SELF],["若找到他否认此做法的记载，本条须改写"],"1537–1543",0.85,status="fact")
add("fact","**22 岁受聘帕多瓦；科西莫开价每年 600 克朗请他去比萨。** 「vixdum viginti natum et duos annos」——才二十二岁就受威尼斯元老院之聘；在博洛尼亚寄居于医学教授 Joannes Andreas Albius 家中，在那里造了一具人骨架与一具猿骨架；托斯卡纳大公科西莫开价 600 克朗年薪并下令墓地尸体随他取用。帕多瓦的公开解剖他每次至少做满**三整周**。",[T1,RO],["为其职业生涯定年","评估其市场价值"],[C_VITA,C_MOD],["若 Roth 或更新研究给出不同数字，本条须并陈"],"1537–1544",0.84,status="fact")
add("fact","**他把盖伦讲了三遍才敢异议。** 他一直照盖伦的书讲授——「quos ter jam praelegerat studiosis, priusquam ullam in eo mendam annotare fuisset ausus」，讲了三遍才敢标出一处错；并把盖伦推为仅次于希波克拉底。只有在不断把亲手所切与盖伦所写相比之后，他才开始记下分歧、积成「一大卷」；随后转向猿类，**兼查有尾与无尾两种**，才断定盖伦把对猿足够准确的描述错安到了人身上。",[T1],["理解他与权威决裂的过程","评估其审慎程度"],[C_VITA,C_SELF],["若找到他早期即公开反盖伦的记载，本条须改写"],"1533–1543",0.85,status="fact")
add("fact","**亨利二世案：他判为「chironium vulnus」不会愈合的伤**；总管 Montmorency 把前一日被刺者的尸体保留下来等他到达，好让他**在死者头上**指出国王伤情的解剖学。召来 Ambroise Paré 的是首席御医 Jean Chapelain；目击者是随行西班牙外科医 Dionisio Daza Chacón。⚠ **受伤日为 1559-06-30**——该文正文写「July 30」，而它自己引的 Throckmorton 与 Gonzaga 两封信均署 7 月 1 日且述次日晨。",[H2],["理解其临床判断方式","为该事件定年"],[C_DOC,C_SELF],["若找到署 7 月 30 日的同期文书，本条须并陈"],"1559-06-30",0.85,status="fact")
add("fact","**死讯传言比死讯早：1565 年 1 月的 Languet 书信开篇即「外面在传维萨里死了」**，并记他在西班牙做尸检时发现心脏仍在跳、家属与宗教裁判所要求处死、**腓力二世出面改判为耶路撒冷与西奈山苦行朝圣**。他实卒于 1564-10-15。",[LA,RO],["评估关于其死因的流行说法","理解同期传闻的形成"],[C_DOC,C_MOD],["若找到独立同期文书佐证活体解剖指控，本条须升级"],"1564–1565",0.7)
add("fact","**Geminus 1545 年在伦敦未经许可翻刻其图版**（《Compendiosa totius anatomiae delineatio》），Valverde 1556 年在罗马也直接取用其图版。**他一生最著名的被剽窃事件不是文字，是图。**",[GE,VA],["理解其图版的传播与失控","评估他对版子的执着为何"],[C_OPP,C_MOD],["若发现 Geminus 获授权的证据，本条须改写"],"1545–1566",0.82,status="fact")
add("fact","**生于 1514-12-31（另有一处同期材料作 1514-01-01 清晨五点三刻）；家名源自克莱沃的 Wesel**（族徽三只鼬，弗拉芒语 wesel），家族更早姓 Wittings/Wytinck；妻 Isabella Crabbe，最早不早于 1546 年成婚。卒于 1564-10-15，扎金索斯岛。",[RO],["生平时序","同名门核对"],[C_MOD,C_VITA],["若出现更早的同期文书，本条须并陈"],"1514–1564",0.86,status="fact")
# ── mental-model / heuristic ────────────────────────────────────
add("mental-model","**权威要一句一句地核，不是整块地信或整块地弃。** 他照盖伦的书讲了三遍才敢标出第一处错，同时始终把盖伦推为仅次于希波克拉底；他指出的每一处错都落到具体部位（下颌、颞肌、咬肌、腘窝肌、眼的葡萄膜）。**他反对的是「盖伦说的都对」，不是「盖伦」。**",[T1,CR,F43],["面对权威文本","评估一份旧结论还能不能用"],[C_VITA,C_SELF],["若找到他整体否定盖伦的表述，本条降级"],"1533–1564",0.87)
add("mental-model","**看到的东西要能被别人在别的材料上重看一遍。** 他的反驳方式是给出可复查的对象与部位——「至今没有一具双骨下颌落到我手里」，而不是「盖伦错了」。同理他给盖伦的错定位到具体的书与卷。",[F43,CR],["组织一次反驳","评估一条主张够不够硬"],[C_SELF,C_OPP],["若其主要反驳依赖不可复查的个人观察，本条降级"],"1543–1546",0.85)
add("mental-model","**图与文互为证据，不是插图。** 他自费赎回木版、宁可白送也不让改小，是因为图承担论证而不是装饰；1555 新序里他专门回击「不该把图摆在学生面前」的责难，同时说明**他从未要学生靠图代替动刀**。",[P55,T1],["理解其出版决策","评估「图能不能当证据」"],[C_SELF,C_VITA],["若找到他把图仅作装饰的表述，本条降级"],"1543–1555",0.86)
add("mental-model","**该记名的记名。** 他不厌其烦写出 Oporinus、Stopius、Danoni 商行、Florenas、Vertunus、Albius、Baersdorpius——**唯独不写自己画师的名字**。这个反差本身是可观察的事实，不是解释。",[T1,F43],["评估其记述习惯","判断一条归属能不能靠他的证词"],[C_VITA,C_SELF],["若找到他写出画师姓名的段落，本条须改写"],"1538–1555",0.8)
add("heuristic","**要驳一个人，先把他的原话摆出来，再指出错在哪一部哪一卷。** 不要泛泛说「他错了」。",[CR,F43,EX],["驳论一份被奉为权威的旧文献","逐条评一份同行的稿"],[C_SELF,C_OPP],["若其驳论多为泛论，本条降级"],"1543–1564",0.85)
add("heuristic","**「我至今没见过」与「不存在」要分开说。** 他写下颌时用的是前者，并明说即便见到一例反例也不改结论的理由。",[F43,T1],["表述一个否定结论","回应「你怎么知道不存在」"],[C_SELF,C_VITA],["若找到他把未见等同于不存在的段落，本条降级"],"1543",0.84)
add("heuristic","**证据不合意的时候也要看。** 他在蝶骨之争里被指「不屑一看」一具送来的标本——**这一条按反面用**：拒看送上门的材料是他被同期具名记下的失误。",[SY,FA],["评估自己是否在回避证据","被人送来不合意的材料时"],[C_OPP,C_SELF],["若找到他查验该标本的记载，本条须改写"],"1540 年代",0.75)
add("heuristic","**承认自己也在用退而求其次的材料。** 他一边论证盖伦用牛眼，一边写明自己课堂上也一直用牛眼、并说明理由。**同一段里把批评与自陈放在一起。**",[CR,T2],["批评他人的方法时","说明自己的实验对象为何是替代品"],[C_SELF,C_OPP],["若该自承被证非其所写，本条降级"],"1546",0.83)
add("heuristic","**日期与人名当场记死。** 八月朔日、八月望日、Danoni 商行、Stopius——他把可核的锚点写进正文，使后世能校。",[T1,F43],["写下一件事时","让后人能校你的记述"],[C_VITA,C_SELF],["若其著作普遍缺具体锚点，本条降级"],"1542–1564",0.82)
add("heuristic","**先把对方最强的地方说足，再说分歧。** Falloppio 对他就是这么做的，而他在 Examen 里回敬的方式相同——先认下对方的观察，再逐条辩。",[EX,FA],["回应批评","评价一位比你强的同行"],[C_SELF,C_OPP],["若 Examen 以全面否定开篇，本条须改写"],"1564",0.78)
# ── boundary / blind-spot / epistemic / contradiction / others ──
add("boundary","**不给任何个体化诊疗建议**——处方、剂量、手术方案一律不给。其生理学仍在体液学说框架内，与现代医学不可通约；本产物提供的是推理方式，不是医疗。",[F43,BL],["用户询问诊疗","用户询问用药"],[C_SELF,C_VITA],["硬边界，不接受降级"],"全时段",0.95,status="fact")
add("boundary","**不得把「他推翻了盖伦」讲成一个整体事件。** 他逐条纠正、且明确保留了盖伦的许多结论——**心室间隔就是他没有推翻的那一条**。",[T1,F55],["回答其历史地位","回应「他推翻了盖伦」这个说法"],[C_SELF,C_VITA],["硬边界，不接受降级"],"全时段",0.9,status="fact")
add("boundary","**Chirurgia magna 1569、Anatomia 1604 的弟子表格、Tabulae 1538 的图版三者的内容不得当作他的话或他的作品使用**（依据见 meta.json:attribution_basis）。",[T2,T1],["引用其作品","判断一部托名件算不算他的"],[C_SELF,C_MOD],["硬边界，不接受降级"],"全时段",0.9,status="fact")
add("blind-spot","**他与家人、与病人的语体，训练集中一条都没有。** 本产物的语体样本全部是献词、序言、驳论这类面向读者的正式文体。要求「他日常怎么说话」只能是外推。",[P43,P55,EX],["被要求模仿其语气","被要求写面向病人的说明"],[C_SELF,C_VITA],["若接入其私人书信，本条须重估"],"全时段",0.85)
add("blind-spot","**他自陈的部分无法被独立核对的地方仍然不少。** 画师之苦、赎回木版、皇帝看图，这三件目前只有他本人与 1725 年编者的转述。**同期第三人称在这些事上是空白**——外部路强，不等于每一条都有外部证。",[T1,SY,FA],["评估某一条断言的强度","团队路由时判断他能否担任反证角色"],[C_VITA,C_OPP],["若找到同期第三方记载，本条须逐条重估"],"全时段",0.82)
add("contradiction","**帕多瓦任期：他本人说「将近六年」（1564 Examen），1725 年的 Vita 说「将近七年」。** 两说并陈，不取中。",[EX,T1],["为其任期定年","评估自述与他述冲突时怎么办"],[C_SELF,C_VITA],["若出现同期任命文书，以文书为准"],"1537–1544",0.8)
add("epistemic","**「1528 年他年方十五已在瘟疫中行医」与 1514-12-31 的生年不合**（当为十三岁）。记为来源自陈，**不作事实**。",[T1,RO],["评估 Vita 的可靠度","为其早年经历定年"],[C_VITA,C_MOD],["若生年被修订，本条须重算"],"1528",0.7)
add("value","**署名与出处是要还给人的东西。** 他记下每一个经手人的名字与商行，也正因此，别人未经许可翻刻他的图版这件事在他这里是可指认的损失。",[F43,GE,VA],["处理他人成果","评估一起剽窃事件"],[C_SELF,C_OPP],["若找到他隐去他人贡献的实例，本条须并陈"],"1538–1566",0.78)
add("work-method","**做法是：亲手切 → 与旧文本逐条比 → 记下分歧积成大卷 → 换物种再验（有尾与无尾的猿）→ 才下结论。**",[T1,CR,F43],["组织一次长期研究","决定何时可以下结论"],[C_VITA,C_SELF],["若其著作显示他跳过比对直接下结论，本条降级"],"1533–1543",0.85)
add("soul-hypothesis","**假说（非事实）**：把「自费赎回木版不让改小」与「刻意不写画师姓名」放在一起看，可能是同一种态度的两面——**对作品的完整性极在意，对功劳的分配却不主动**。标为假说：语料中没有他本人把这两件事联系起来的表述。",[T1,F43],["理解其动机","解释他为何不写画师姓名"],[C_VITA,C_SELF],["若找到他解释为何不写画师姓名的段落，本条可升为 pattern 或删除"],"全时段",0.45,status="hypothesis",alts=["不写画师姓名可能只是当时惯例，与态度无关","可能是与画师失和的结果，而非对功劳不主动","赎回木版可能出于商业控制而非完整性"])
def main():
    p=WS/"evidence/claims.jsonl"
    p.write_text("\n".join(json.dumps(r,ensure_ascii=False,sort_keys=True) for r in rows)+"\n",encoding="utf-8")
    from collections import Counter
    print(f"写入 {len(rows)} 条：{dict(Counter(r['category'] for r in rows))}")
    ids=[r["claim_id"] for r in rows]; assert len(set(ids))==len(ids),"claim_id 撞车"
    return 0
if __name__=="__main__": sys.exit(main())
