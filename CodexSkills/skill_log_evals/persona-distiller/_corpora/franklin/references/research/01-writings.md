# Writings

## Scope and assigned sources

**本道分到 5 份（train split）**：

| source_id | 出版年 | tier | 题名 |
|---|---|---|---|
| `src-be316839952b` | 1759 | P1 | A true and impartial state of the province of Pennsylvania…nd their governors; ...  1759 |
| `src-cfc75b551c97` | 1760 | P1 | The interest of Great Britain considered with regard to he…ublick-spirited people.  1760 |
| `src-bdc45c999289` | 1769 | P1 | Experiments and observations on electricity, made at Philadelphia in America |
| `src-37cd0e797159` | 1784 | P1 | Two tracts: : Information to those who would remove to Ame…the savages of North America. |
| `src-c3c1277534b0` | 1794 | P1 | Works of the late Doctor Benjamin Franklin: consisting of … In two volumes.  1794: Vol 2 |

★ 本节由台账机械导出（`emit_lane_scope.py`），**不含任何阅读判断**；只投影 `split == train` 的行。

## 五条实测发现（逐份）

### ① 《电学实验与观察》（1769）——观察第一、假设第二的自然哲学家声口
`src-bdc45c999289` 是 1747 年起致伦敦皇家学会会员 Peter Collinson 的书信汇编。开篇（1747-03-28，Philadelphia）以谦逊的实验者声口自报：

> OUR kind prefent of an eleCtric tube
<!-- src-bdc45c999289 -->

（该卷 Letter I 原文为「我们收到你送来的电管与用法说明后，数人开始做电学实验，观察到几个我们认为新奇的现象，将在下一封信里告知你」——此句语料跨行断词严重，仅引句首，其余改述。）

- **正负（plus/minus）命名**（Letter 一段）：他用电的"盈/亏"来命名正负电：

> B is eledrifed plus, A, minus. And we daily in our experiments eledrife bodies plus or minus, as we think proper.
<!-- src-bdc45c999289 -->

- **尖端的"引电/放电"效应**（避雷针原理的实验基础）：

> The firft is the wonderful effedt of pointed bodies, both in drawing off and throwing off the eledtrieal fire.
<!-- src-bdc45c999289 -->

- **风筝实验**（Letter XI，述 Philadelphia 如何验证"电与雷同质"）：

> As foon as any of the thunder clouds come over the kite, the pointed wire will draw the eledric fire from them
<!-- src-bdc45c999289 -->

> the fame-nefs of the eledric matter with that of lightening completely demonftrated.
<!-- src-bdc45c999289 -->

（该段末署名 `B. F(`，即 B. F.。）

- **避雷针提议**（用云=带电体的小尺度模型外推到建筑；句末"before it came nigh enough to strike, and thereby secure us from that most sudden and terrible mischief"跨页断行，以改述呈现）：

> Would not thefe pointed rods probably draw the eledrical fire filently out of a cloud
<!-- src-bdc45c999289 -->

（另段还建议"fix on the higheft parts of thofe edifices, upright rods of iron made fharp as a needle"，即在高处立"尖如针的铁杆"引雷入地，改述。）

- **方法论自白（最重要）**——在另一封信里他对自己的理论作保留，明确"观察 > 假设"。本段 OCR 以 `y` 代分号、`wiih`=wish、`againft`=against：

> Whatever I have wrote of that kind, are really, as they are entitled, but Conjectures and Suppofitions y which ought always to give place, when careful obfervation militates againft them. I own I have too ftrong a penchant [版口：此行缺] to the building of hypothefes y they indulge my natural indolence
<!-- src-bdc45c999289 -->

（本句后半大意："但愿我更有你做观察的耐心与精确——真哲学只能建在观察上"——该处 `obſervations, on which, alone, true Philoſophy can be founded` 语料带 `,.` 连排讹形，改述。）

⇒ 他把理论自贬为"假设/臆测"，并自嘲爱搭假设只是"纵容天性懒惰"；真哲学只能建在观察上——这是富兰克林科学声口的指纹，与《电学》序言（编者代笔）里"以一连串事实与明智反思引向现象的或然原因"的描述互相印证。

### ② 《论大不列颠的利益》（1760）——殖民地人口-经济因果模型
`src-cfc75b551c97` 含两部分：正文驳"留加拿大还是留瓜德罗普"之争，附《Increase of Mankind》人口论（正文署 *Written in Penſylvania, 1751*）。他的经济推理是链条式的因果：

- **人口 = 结婚意愿的函数，结婚意愿 = 养家难易的函数**（Obs. 2）：

> For people increaſe in proportion to the number of marriages, and that is greater in proportion to the eaſe and convenience of ſupporting a family.
<!-- src-cfc75b551c97 -->

- **美洲"地贱"→ 敢结婚 → 每二十年翻番**（Obs. 6-7）：

> Land being thus plenty in America, and ſo cheap as that a labouring man, that underſtands huſbandry, can in a ſhort time fave money enough to purchaſe a piece of new land ſufficient for a plantation, whereon he may ſubſiſt a family; ſuch are not afraid to marry
<!-- src-cfc75b551c97 -->

> our people muſt at leaſt be doubled every twenty years.
<!-- src-cfc75b551c97 -->

- **劳动力为何贵**（Obs. 8，直接回应重商派"殖民地会抢英国制造"的担忧）：

> and till it is fully ſettled, labour will never be cheap here, where no man continues long a labourer for others, but gets a plantation of his own
<!-- src-cfc75b551c97 -->

> The danger therefore of theſe colonies interfering with their mother country in trades that depend on labour
<!-- src-cfc75b551c97 -->

（该句续文"…manufactures, &c. is too remote to require the attention of Great Britain"语料作 `manufac- ' tures, Oc.`，断词+`Oc.`= &c. 讹形，改述。）

- **殖民地 = 市场而非竞争对手**（Obs. 10；`Br//;/5` 为 British 的 OCR 讹形）：

> a vaſt demand is growing for Br//;/5 manufactures; a glorious market wholly in the power of Britain
<!-- src-cfc75b551c97 -->

- **"制造源于贫困"定理**（正文最锋利的一句经济观察，主张"只要人人有地，就不会有制造业"）：

> Manufactures are founded in poverty. It is the multitude of poor without land in a country, and who muſt work for others at low wages or ſtarve, that enables undertakers to carry on a manufacture
<!-- src-cfc75b551c97 -->

> But no man who can have a piece of land of his own, ſufficient by his labour to ſubſiſt his family in plenty, is poor enough to be a manufacturer, and work for a maſter.
<!-- src-cfc75b551c97 -->

⇒ 论证方法：从"地广人稀 → 劳动贵 → 无廉价工人 → 无制造"推出一条链条，反过来说明美洲的安全形态（农业扩张）天然不会威胁母国制造业——**用经济因果而非道德立场论殖民**。

### ③ 《宾夕法尼亚省真实公正之状况》（1759）——宪政辩护文（本卷 OCR 退化最重，引文一律取可逐字核验的短片段，长句改述）
`src-be316839952b` 是富兰克林派在"Proprietary（业主家族）vs 议会/人民"之争中的檄文。**本卷 OCR 为五份中最差**（`Covina`=Government、`Vvinue`=Virtue、`Govery`=Governor、页号夹入正文），长句无法逐字成句，故本节只引可核短片段、句间用改述衔接（改述不加引号）。

- **论敌立场复述**（作者开篇引对手话再驳）：人民权力随人口财富增长、总督权力反而落后：

> contitwally increafing with their Numbers, and Riches

> far from keeping Pace with theirs
<!-- src-be316839952b -->

（`contitwally`=continually；对手原话大意"人民权力一直在随其人数与财富增长，而总督权力远未同步、反在同比缩减"——本册逐条反驳。）

- **己方回应——宾州并非更民主**（`chis`=this 讹形）：

> That chis Government, in its firſt Eſtabliſhment

> under our preſent Charters, does not incline more to
<!-- src-be316839952b -->

（下文大意"作为远离母国视野的 charter 政府，应接近混合政体，以智慧与审慎为准"——语料夹页号噪声，改述。）

- **总督否决纸币法案**（议会为防卫经费要发纸币，总督以业主训令为由断然否决）。总督回话大意"我既无此意、且时间紧迫、身体状况也不容许我卷入纸币法案之争，故就此给以绝对否决"——语料此段夹页号伪影 `8`、断词严重（`aud`=and 讹形），无法逐字成句，改述；其中"绝对否决"一句为可核片段：

> an abſolute Negative
<!-- src-be316839952b -->

作者（富兰克林派）评这笔否决对议会的打击（`graateſt`=greatest、`Welfate`=Welfare 讹形）：

> unfortunately for the People, a Bill. of the graateſt Importance to the Trade and Welfate
<!-- src-be316839952b -->

- **业主地产豁免税负**（议会要按地产征税而业主抗税；`jaſt`=juſt 讹形）：

> jaſt Tax, on their exorbitant
<!-- src-be316839952b -->

⇒ 立场：为省议会/人民的权利辩护，反对"业主私利凌驾于公共防卫与税制"；把宪制之争落在"谁有权征税、谁能否决、业主地产是否该豁免"这些具体制度点上，而不是抽象人权话术。

### ④ 《两篇短论》（1784）——移民指南与北美原住民评论（双声口）
`src-37cd0e797159` 收两文。其一《Information to Those Who Would Remove to America》逐条破除欧洲人"美洲遍地黄金"的想象，核心是"普遍的中等幸福"：

> there are in that country few people fo miferable as the poor of Europe, there are alfo very few that in Europe would be called rich
<!-- src-37cd0e797159 -->

> It is rather a general happy mediocrity that prevails. There are few great Proprietors of the foil, and few Tenants; moft people cultivate their own lands, or follow fome handicraft or merchandife
<!-- src-37cd0e797159 -->

- **公职少且不肥**（`fhould he`=should be 的 OCR 形；语料"and it is a rule"作 `ita rule`，改述）：

> Of civil offices or employments, there are few; no fuperfluous ones as in Europe
<!-- src-37cd0e797159 -->

> that no Office fhould he fo profitable as to make it defirable
<!-- src-37cd0e797159 -->

（引文背后是宾州宪法第 36 条"任何公职不应肥到使人觊觎"的主张，改述。）

- **工匠/学徒的"人口红利"**（工人稀缺→工匠反而更好过、甚至倒贴钱收学徒）：

> fo defirous of apprentices, that many of them will even give money to the parents
<!-- src-37cd0e797159 -->

（后文大意：学徒十至十五岁入行、二十一岁出师，许多穷家长靠此攒钱买地安家——语料此处断词+页号干扰，改述。）

其二《Remarks concerning the Savages of North America》用相对主义开篇：

> we fhould find no people fo rude as to be without any rules of politenefs; nor any fo polite
<!-- src-37cd0e797159 -->

（句尾"as not to have some remains of rudeness"语料作 `as not to: have fome remains of | rudenefs`，带 `:` 与页边符，改述。）

- **印第安社会"无强制而有序"**（"there is no force"被页号切断，改述；可核片段）：

> Hence they generally ftudy oratory

> the beft {peaker having the moft influence.
<!-- src-37cd0e797159 -->

> The Indian women till the ground, drefs the food, nurfe and bring up the children, and preferve and hand down to pofterity the memory of public tranfactions.
<!-- src-37cd0e797159 -->

> Having few artificial wants, they have abundance of leifure for improvement by converfation.
<!-- src-37cd0e797159 -->

> they efteem flavifh and bafe

> they regard as frivolous and ufelefs.
<!-- src-37cd0e797159 -->

（合读："我们勤劳的生活方式，在他们眼里既奴役又卑下；我们引以为傲的学问，他们视为轻浮无用。"——改述衔接。）

- **反讽"文明人"**：拉卡斯特条约（1744）轶事里，弗吉尼亚人提议送印第安青年上学院，六族酋长反提议送白人青年来接受印第安教育，结论是回校青年"totally good for nothing"：

> they were totally good for nothing.
<!-- src-37cd0e797159 -->

> will fend us a dozen of their fons, we will take great care of their education
<!-- src-37cd0e797159 -->

（后句"instruct them in all we know, and make men of them"语料跨行夹 `e298')` 伪影、句尾作 `make $6 men of them`（`$6` 为页号伪影），无法逐字成句，改述。）

- **口头记忆优于书面记录**（`{tipulations`=stipulations 的 OCR 形）：

> They are the Records of the Council, and they preferve tradition of the {tipulations in Treaties a hundred years back; which, when we compare with our writings, we always find exact.
<!-- src-37cd0e797159 -->

- **礼貌到过头的反讽**（`1s`=is 的 OCR 形），并借"打断他人极不礼貌"反衬英国下议院的喧闹：

> To interrupt another, even in common converfation, 1s reckoned highly indecent.
<!-- src-37cd0e797159 -->

- **全文收束——好客是"野蛮人"的美德**：

> It is remarkable, that in all ages and countries, hofpitality has been allowed as the virtue of thofe, whom the Civilized were, pleafed to call Barbarians
<!-- src-37cd0e797159 -->

⇒ 声口：务实（移民指南只谈劳动与土地、不吹黄金）+ 相对主义与反讽（原住民篇借"文明/野蛮"倒转，讥讽欧洲礼仪与殖民教育的自负）。

### ⑤ 《富兰克林文集第二卷》（1794）——口传式道德随笔
`src-c3c1277534b0` 卷首署 *Works of the late Doctor Benjamin Franklin: consisting of his Life written by himself, together with essays, humorous, moral & literary, chiefly in the manner of The Spectator*。随笔是教训体（apologue），直白讲理、自嘲收尾。

- **《口哨》（The Whistle）**：童年用全部零钱买了一只哨子、被兄弟嘲笑"给了四倍的价"，由此得出教训：

> WHEN I was a child, at ſeven years old, my friends, on a holiday, filled my pocket with coppers.
<!-- src-c3c1277534b0 -->

> often, when I was tempted to buy ſome unneceflary thing, I faid to myſelf, Don't give too much for the whiſtle ; and fo I ſaved my money.
<!-- src-c3c1277534b0 -->

> In ſhort, I conceived that great part of the miſeries of mankind were brought upon them by the falſe eſtimate they had made of the value of things, and by their giving too much for their whiſtles
<!-- src-c3c1277534b0 -->

- **《给年轻商人的忠告》（Advice to a young Tradesman, written Anno 1748）**——三条"记住"开头的格言，把时间/信用/复利当资本看待：

> REMEMBER that time is money.
<!-- src-c3c1277534b0 -->

> Remember that money is of a prolific generating nature. Money can beget money, and its offspring can beget more, and ſo on.
<!-- src-c3c1277534b0 -->

> In ſhort, the way to wealth, if you deſire it, is as plain as the way to market. It depends chiefly on two words, induſtry and frugality; that is, waſte neither #ime nor money, but make the beſt uſe of both.
<!-- src-c3c1277534b0 -->

（`#ime`=time 的 OCR 形。）

⇒ 随笔声口：把抽象道理压成一句话、一个场景、一次童年糗事；"false eſtimate of the value of things"与《移民指南》的"happy mediocrity"、《电学》的"观察第一"是同一套**用经验校准价值**的心智。

## 这一道给下游的东西

- **科学方法链（贯穿 ① 与 ②）**：先观察/事实，后假设；理论只是"Conjectures and Suppofitions"，"careful obſervation militates against them"（①）；经济论同样以"bills of mortality / observations"式的经验表为底（② 的人口翻番推算）。"假设纵容我的懒惰"（①）是富兰克林自嘲式的方法论自白，可作 claims 的强证据。
- **人口-经济因果模型（②，可独立成链）**：结婚意愿 ∝ 养家容易度 → 美洲地贱人稀 → 每二十年翻番、劳动力贵 → 无廉价制造 → 殖民地是市场非对手；"Manufactures are founded in poverty" 是中心命题。
- **宪政立场（③）**：站在议会/人民一边，反对业主的否决权与地产税豁免；主张宾州是"接近混合政体"的 charter 政府；批评总督以个人训令压制公共防卫。
- **经验主义伦理（④⑤）**：价值要由经验校准——"false eſtimate of the value of things"（⑤）、"happy mediocrity"（④）、"time is money / credit is money / money begets money"（⑤）。同一心智在不同文体里反复出现。
- **相对主义与反讽（④）**：借"文明/野蛮"倒转讥讽欧洲；"Records of the Council" 口头记忆胜于文字；对"礼貌/礼仪"的表演性保持警觉。
- **声口区分**：电学序言是编者口吻（不可当富兰克林观点）；宾州文作者归属有争议（目录署 [Franklin, LL.D.]，作为"富兰克林派文献"使用而非铁证亲笔）；② 的《人口增长》正文署 1751 宾州旧作。
- **OCR 词汇指纹**：长 s 转写为 `ſ`（②③⑤）或 `f`（①④）；`eledric/eledrifed`（①）、`Br//;/5`＝British、`graateſt`＝greatest、`Welfate`＝Welfare、`{peaker`＝speaker、`#ime`＝time 等讹形——下游 claims 文本须用语料拼写。

## 未做完 / 未核

- **电学卷（920 KB）未整本通读**：仅取 1747–1752 前段信札、尖端/风筝/避雷针/假设段与 Letter XI；未核各信札日期、卷末后续实验、与各版（1747/1769）内容对应。
- **宾州卷 OCR 退化最重，最未完成**：`Covina`=Government、`Vvinue`=Virtue、`Govery`=Governor、`jaſt`=juſt 等大量讹形；"People's Power"段与"混合政体"段夹页号噪声，长句仅以可核短片段+改述处理，未逐段重建全文论据。`src-be316839952b` 的作者归属未在本道内考证（只记录目录署名）。
- **Works Vol 2 只读随笔部分**：未读卷内 Life（自传）与其余随笔（A Petition of the Left Hand、The handsome and deformed Leg、Chess、Dreams、现代英语创新论、Press 法庭等）——如其他道（timeline/decisions）需要自传内容，另案处理。
- **引文坐标粒度**：本道坐标到 source_id 级；跨行断词按"连字符接续"归一（如 `fame-nefs`、`prolific`、`tradi-tion`、`inftrudt`），个别段标注 [版口]；页码 OCR 不可靠，未逐一核页。
- **未读未引**：本道只引用了上述五个 train 源，其余来源一律未读、未引。
