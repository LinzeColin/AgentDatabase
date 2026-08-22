# Writings

## Scope and assigned sources

本道用 train 档六份一手源（全部逐字读取，OCR 宽空格已归一为单空格，**讹形不修**）：

| source_id | 出版年 | 作品 | 文件 |
|---|---|---|---|
| `src-4a91e703724a` | 1832（第三版，序言署 1832-06-08） | On the Economy of Machinery and Manufactures《机械与制造业经济》 | `raw/oneconomyofmac00babb.txt` |
| `src-14b238725cab` | 1837 | The Ninth Bridgewater Treatise, A Fragment《第九桥水桥论》 | `raw/bub_gb_C2sYl7PskYgC.txt` |
| `src-39cf3746b17b` | 1830 | Reflections on the Decline of Science in England《英格兰科学之衰败》 | `raw/10730620bsb.txt` |
| `src-0ea37434eee7` | 1864 | Passages from the Life of a Philosopher《一个哲学家的生平》（自传） | `raw/bub_gb_2T0AAAAAQAAJ.txt` |
| `src-99626bed2c1b` | 1816 | An Elementary Treatise on the Differential and Integral Calculus（Lacroix 著，Babbage 等英译） | `raw/anelementarytre00babbgoog.txt` |
| `src-eec0495f8470` | 1851（第二版） | The Exposition of 1851《1851 年博览会》 | `raw/b21495336.txt` |

**本道只读上列六份；未列出的一律未读、未引。**

六份体裁跨度大（经济论、神学论、科学政策檄文、自传、译文、时政论），声口不同，逐份记发现、不混源。

## 六条实测发现（逐份）

### ① 《机械与制造业经济》（1832 三版）——把数学的概括原则搬进工厂
`src-4a91e703724a` 在**序言第一句**就把这本书定义为差分机工程的副产物：

> The present volume may be considered as one of the consequences that have resulted from the Calculating-Engine, the construction of which I have been so long superintending.
<!-- src-4a91e703724a -->

随后交代方法——他不是经济学家出身，是带着数学家的习惯进工厂的：

> I was insensibly led to apply to them those principles of generalization to which my other pursuits had naturally given rise.
<!-- src-4a91e703724a -->

⇒ 他的经济写作是**"差分机工程 → 十年级工厂考察 → 用概括原则反推经济原理"**这条链的产物；开宗明义承认书的出身，也承认个别原理已被前人（Gioja）抢先，论据是"truth is of much more importance than their origin"。

- **降低门槛的立场**：`The difficulty of understanding the processes of manufactures has unfortunately been greatly overrated.`（序言）——他认为理解工厂的一般原理不需要是制造商。
- **"trade secrets"观**：`The only real secrets of trade are industry? integrity, and knowledge : to the possessors of these no exposure can be injurious`（第二版序；OCR 中 `industry?` 为 `industry,` 的讹形）——把商业秘密解构为"勤劳、诚实、知识"三件公开物。
- **心智劳动分工（第 241–246 节）**：他把分工直接推到脑力劳动上：`that the division of labour can be applied with equal success to mental as to mechanical operations, and that it ensures in both the same economy of time`；用 Prony 编制法国对数表的"三段式"（最高层数学家定公式 → 中层换算成数字 → 六十到八十名只会加减的工人填表，且"nine-tenths of this class had no knowledge of arithmetic beyond the two first rules"）说明：**脑力工作也可以像棉纺厂一样分层外包**。
- **"机器能算"的科普方法（第 247–249 节）**：面对"机器能做算术"这个被他称为"too large a postulate"的假设，他先用平方数表的二阶差分讲原理，再用**三座钟**做类比：`Let the reader imagine three clocks, placed on a table side by side, each having only one hand...`——B 钟每敲一下推 A 钟走一格，C 钟推 B 钟，于是加法的反复进行就"自动"算出平方数。脚注报告当时已装好的差分机部分已算出非恒定差分级数。
- **观察方法论（第 160–162 节，"On the Method of Observing Manufactories"）**：主张预先印好"skeleton forms"（带空白的问卷），并且**警惕观察者改变被观察者**：`if the observer stands with his watch in his hand before a person heading a pin, the workman will almost certainly increase his speed, and the estimate will be too large`；建议在工人无察觉时数织机声：`the sound made by the motion of a loom may enable the observer to count the number of strokes per minute, even though he is outside the building`。他引 Coulomb 的法文原文佐证同一警告（`d'observer les ouvriers a differentes reprises dans la journee, sans qu'ils sachent qu'ils sont observes`）。还主张**用"可由其他数据推导出的问题"交叉验证答案**：`there are some which, although given directly, may also be deduced by a short calculation from others...advantage should always be taken of these verifications`。

### ② 《第九桥水桥论》（1837）——用机器当神学模型
`src-14b238725cab` 全书是对题辞的反驳——Whewell 断言数学家对"宇宙的治理"没有发言权（扉页引 Whewell 原话）。Babbage 在序言里先立方法论底线：

> Reasoning is to be combated and refuted by reasoning alone. Any endeavour to raise a prejudice, or throw the shadow of an imputation, either implies the existence of some latent misgiving in the minds of those who employ such weapons
<!-- src-14b238725cab -->

（正文意思为"推理只能用推理反驳"；语料原文此处为 `the shadow of an imputation`。）

- **"上帝 = 一次编程、无须干预"的神学**：他认为把上帝描写成"不断临时改动物理定律"反而是贬低上帝——`thus by implication denying to him the possession [版口：INTRODUCTION. 25] of that foresight which is the highest attribute of omnipotence`（引言）。人文学科在他笔下被称"human knowledge"，被他自己重新定义为`the interpretation of those laws that God himself has impressed on his creation`。
- **奇迹即"更广定律的精确完成"（第八章）**：`miracles are not deviations from the laws assigned by the Almighty for the government of matter and of mind; but that they are the exact fulfilment of much more extensive laws than those we suppose to exist.` 他请读者"again imagine himself sitting before the calculating engine"：引擎已连续千年出平方数，制造商说下一次要出一个例外数，观察者会把更大权力归给"在无数世代之前就预定该事件"的制造者——`Undoubtedly the observer would ascribe a greater degree of power to the artist who thus willed that event at the distance of ages before its arrival.` 并进一步论证"能事先程序化 N 个不同例外"比"每次临时干预"更显设计之智。
- **这套论证的双重用途**：同章结尾他把这个机器比喻反过来用于**科学为宗教辩护**：`the study of the most abstract branch of practical mechanics, combined with that of the most abstruse portions of mathematical science, has no tendency to incapacitate the human mind from the perception of the evidences of natural religion`——正是对题辞里"数学家被训练得看不懂自然神学"的直接回击。
- **认识论立场**：`It is a condition of our race that we must ever wade through error in our advance towards truth`，并论证"最充分的讨论最有利于真理"。

⇒ 这是他**把差分机/分析机当作普适解释装置**的最高体现：同一台机器，既能算表，也能当作"设计论"的新论据。对"机器能否思考/计算"这个问题，他的态度始终是**工具性的**——机器是心智的分身与佐证，不是威胁。

### ③ 《英格兰科学之衰败》（1830）——实证主义的科学政策檄文
`src-39cf3746b17b` 序言主动撇清与差分机的关系，证明这是独立于个人恩怨的立场：

> On one point I shall speak decidedly, it is not connected in any degree with the calculating machine on which I have been engaged; the causes which have led to it have been long operating, and would have produced this result whether I had ever speculated
<!-- src-39cf3746b17b -->

- **匿名与证据的尺度**：`If a fact is to be established by testimony, anonymous assertion is of no value; if it can be proved, by evidence to which the public have access, it is of no consequence (for the cause of truth) who produces it. A matter of opinion derives weight from the name which is attached to it; but a chain of reasoning is equally conclusive, whoever may be its author.`——把"事实"与"意见"分开定价，事实不认署名，推理链不认署名。
- **"怕被查的人才反对公开"**：`It is clearly the interest of all who fear inquiries, to push this principle as far as possible, whilst those whose sole object is truth, can have no apprehensions from the severest scrutiny.`
- **对皇家学会的讽刺与改革纲领**：他给各学会的"缀名字母"（如 FRS）算了笔账，讽刺它们像彗尾一样拖着一串字母、平均每个字母值 10l. 9s. 9½d.（此句语料 OCR 跳行，无法逐字引用）；对皇家学会则宣称要`direct public opinion in calling for such a reform, as shall rescue the Royal Society from contempt in our own country, from ridicule in others`。他承认下笔是痛的：`like all deeplyrooted complaints, the operation which alone can contribute to its cure, is necessarily painful`。
- **观察/实验哲学（第五章，"Of Observations"）**：这是本册最"方法论"的一段——`genius marks its tract, not by the observation of quantities inappreciable to any but the acutest senses, but by placing Nature in such circumstances, that she is forced to record her minutest variations on so magnified a scale, that an observer, possessing ordinary faculties, shall find them legibly written`（`tract` 为 `track` 的 OCR 形）。即：天才不是去测量极微小的量，而是**重新布置条件，让自然把微小变化放大到任何人都读得出来**——这正是他造仪器、造引擎的总思路。

⇒ 政策写作同样带数学家的"先定尺度、再摆证据、最后下判断"结构；讽刺是手段，证据链是核心。

### ④ 《一个哲学家的生平》（1864 自传）——工具癖、"教机器远见"、晚年自辩
`src-0ea37434eee7` 序言解释为何写这本书（只为差分机/分析机的历史，不是真自传）：

> I have no desire to write my own biography, as long as I have strength and means to do better work.
<!-- src-0ea37434eee7 -->

- **第一章"我的祖先"的戏谑自画像**：`considering my own inveterate habit of contriving tools, it is more probable that I should derive my passion by hereditary transmission from these original tool-makers`（OCR `tool*` 即 `tools`）——把"工具癖"当家族遗传来调侃；另有名句 `What is there in a name? It is merely an empty basket, until you put something into it`。
- **差分机起源场景（1812/1813 分析学会）**：`"Well, Babbage, what are you dreaming about?" to which I replied, "I am thinking that all these Tables (pointing to the logarithms) might be calculated by machinery."`——一个"做梦式的灵光"被他追认成引擎的开端。
- **分析机章（第八章）的自我叙事**：`The whole of arithmetic now appeared within the grasp of mechanism. A vague glimpse even of an Analytical Engine at length opened out, and I pursued with enthusiasm the shadowy vision.`——他用"shadowy vision"形容当年的模糊远景。
- **关于"进位"（carrying the tens）的关键方法论自白**：他试尽"逐位进位"后认定`nothing but teaching the Engine to foresee and then to act upon that foresight could ever lead me to the object I desired, namely, to make the whole of any unlimited number of carriages in one unit of time`——**"教机器预见并据预见行动"**；为此在书房苦思三小时，助手以为他精神失常，最终做出"anticipating carriage"。这句话把"预见(foresight)"同时用作机器原理和神学论据，是跨书的一根暗线。
- **机械记谱法（第九章）**：`By a new system of very simple signs I ultimately succeeded in rendering the most complicated machine capable of explanation almost without the aid of words`；并把它升格为`a new demonstrative science, namely, that of proving that any given machine can or cannot exist; and if it can exist, that it will accomplish its desired object`。
- **管理/经济学观念延续**：`I at length laid it down as a principle — that, except in rare cases, I would never do anything myself if I could afford to hire another person who could do it for me`（与"心智劳动分工"同构）；分析机描述里用雅卡尔提花机作类比，分 store/mill、operation cards/variable cards，并说`the Analytical Engine will possess a library of its own`（一套卡片即一段可复用的"程序"）。
- **晚年自辩与怪癖（"街头公害"章）**：对街头手风琴（organ-grinders）做分人群的"受扰程度"分析——`The amount of interruption from street music, and from other occasional noises, varies with the nature and the habits of its victims`——又一次把社会现象当变量分析。

⇒ 自传声口：**骄傲与自怜交织**，先讲发明史、再讲被辜负；幽默（flint-workers、Cain 笑话、牡蛎题辞）从不缺席，即使在抱怨政府时。

### ⑤ 《微分与积分学基础》（1816）——**这本不是他的著作，是他译的（Part I）**
`src-99626bed2c1b` 卷首"ADVERTISEMENT"把作者与译者的分工写得清清楚楚——原著是 Lacroix（OCR 行首 `X  BB`＝`The`、`no^r`＝`now`、`iPuhlic`＝`Public`，照录）：

> X  BB  work  of  Lacroix,  of  which  a  Translation  is  no^r  presented  to  the  iPuhlic,  forms  one  of  a  series  of  Elemen-. tary Treatises^ by that distinguished Author, on the dif ferent branches of the Pure Mathematics
<!-- src-99626bed2c1b -->

> The  first  part  of  this  Treatise,  which  is  devoted  to  the  exposition  of  'the  principles  of  the  Dlfierential  Calculus,  was  translated  by  Mr.  Babbage.  The  translation  of  the  second  part,  which  treats  of  the  Integral  Calculus,  was  executed  by  Mr.  G.  Peacock,  of  Trinity  College,  and  by  Mr.  Herschel,  of  St.  John's  College,  in  nearly  equal  proportions.
<!-- src-99626bed2c1b -->

且注释也不是他写的：`The  first  twelve  of  the  Notes  were  written  by  Mr*  Peacock...  The  others  were  written  by  Mr.  Herschel.`（OCR `Mr*`＝`Mr.`）

⇒ **归属红线**：本卷里 Babbage 的署名贡献是**第一部分的英译**，正文的"我/作者"声口是 Lacroix 的（且 Lacroix 在本文本中采用 d'Alembert 的极限法而非 Lagrange 的方法）。**从本源取的任何引文都不能当作 Babbage 本人的观点或文风**，只能作他 24 岁时的数学身份（剑桥分析学会圈子、把法国分析学引入英国）与译笔的旁证。语料正文如 `Xhe subject pf this branch of Analysis is the passage of one or more quantities through different states of magnitude`（Part I 开头）在气质上接近 Babbage 熟悉的分析传统，但**归属必须标为"译文"**。

### ⑥ 《1851 年博览会》（1851 二版）——把社会当受控实验
`src-eec0495f8470` 序言是他晚年"科学受委屈"总控诉的一部分：

> England has invited the judgment of the world upon its Arts and its Industry; — science appeals to the same tribunal against its ingratitude and its injustice.
<!-- src-eec0495f8470 -->

- **被劝"别写"时的回应**：`Several friends whose esteem I prize, have urged me to avoid everything personal... I value their friendship, whilst I reject their counsel.`；对"出版会伤你"的劝告他答：`I know of [版口：PREFACE. IX] no injury within the power of those who have never given me a single occasion for gratitude.`；并留下格言 `Bad men always hate those they have injured; — Good or great men, when they have discovered that they have been unjust, always more than repair the injury they have committed.`
- **对党派的分类讽刺**：他把党派对持异议者的命名归成序列——`If he agree with them in a principle, but differ in its application, he is called "  crotchety!' If he cannot be induced by sophistry to vote with them against his sense of right, he is called "  imprac- ticahlc."`（语料此段后半 OCR 跳行，`cantankerous fellow`／`bad names are coined` 无法逐字定位）（与 Reflections 里"匿名无价值"同一种对语言操纵的不信任。）
- **方法论文（引言章）——普遍原理 vs 一般原理**：`Universal principles, such as the fact that every number ending with the figure five is itself divisible by five, rarely occur except in the exact sciences... General principles are those which are much more frequently obeyed than violated.`——社会事实只能用"一般原理"处理，并仍要以自利假说为大前提。
- **实验法移植到社会**：`One of the most important processes in all inquiry, is to divide the subject to be considered into as many different questions as it will admit of, and then to examine each separately, or in other words to suppose that each single cause successively varies whilst all the others remain constant.`——即控制变量法；配套的还有拿破仑讥 Laplace 只盯 `les infiniment petites` 的轶事，Babbage 的回应是`To dwell upon small affairs which are isolated, is not the province of a statesman; but to integrate the effect of their constant recurrence is worthy of the greatest`——把微积分的"积分"当社会分析的比喻。
- **工具/绘图/机械记谱法的产业观（第十三章 "Calculating Engines"）**：`It is not a bad definition of man to describe him as a tool-making animal.`；`whoever is a master in the art of tool-making possesses the key to the construction of all machines.`——把机械记谱法升格为"表达一切机器关系、甚至可描述海陆战役的语言"，并主张政府在差分机上的 £17,000 即使机器全废，"would be well repaid by the advancement it had caused in the art of mechanical construction"。

⇒ 晚年声口：**证据为先、分变量、控诉中带机锋**；社会现象被他一律拆成可控制的变量与可复用的"原理"。

## 这一道给下游的东西

- **一条贯穿五本原创作的思维链**：差分机/分析机不仅是发明，还是他的**通用解释装置**——经济分工（①）、神学设计（②）、观察方法（③）、自传叙事（④）、社会分析（⑥）都借它讲理；"foresight/anticipating carriage"一词同时在机器原理（④）与神学论据（②）里出现。
- **方法论签名**：① 概括原则跨界迁移；③⑤ 先立尺度、证据链、交叉验证；⑥ 控制变量 + "积分累积效应"；③ 警惕观察者效应（Coulomb 警告）、让自然"放大"微小变化。
- **论战语法**：只认证据不认署名（③）；"推理只能用推理反驳"（②）；对语言操纵（党派的坏词、匿名）不信任（③⑥）。
- **幽默一贯性**：flint-workers/Cain 玩笑（④）、牡蛎题辞（④）、FRS 字母尾巴计价（③）、"crotchety/impracticable/cantankerous"词表（⑥）——即使抱怨也不失讥讽。
- **科学政策立场**（可独立成链）：匿名无价值、学会要公开账目与讨论、皇家学会要改革（③⑥）。
- **归属红线**：⑤ 是译文（Part I 为 Babbage 译），**其引文不得当作 Babbage 观点**；只有"他 1816 年参与把法国分析学译入英国"这一事实可入 claims。

## 未做完 / 未核

- **年份核对**：任务标注 ① 为 1829（初版年），但 `src-4a91e703724a` 实际扫描是**第三版**、序言署 1832-06-08，内含"To the Second Edition"序——引用时应按 1832 处理，勿写 1829。⑥ 为第二版（含"NOTE ADDED TO THE SECOND EDITION"）。
- **未整本通读**：六份均为逐段精读而非逐行读完。① 未读"Copying/Price/Division of Labour"等章细节；② 未读第八至十四章与附录 Note B 全文；③ 未读第三章后半至第四章皇家学会各节；④ 未读大量出国见闻章；⑤ 仅读 ADVERTISEMENT + Part I 开头；⑥ 未读 Prices/Juries/Intrigues/Position of Science/Press/Party 各章。
- **OCR 噪音**：③ `10730620bsb.txt` 混入手写边注的扫描噪音，个别词（如 `tract`＝`track`、`industry?`＝`industry,`、`tool*`＝`tools`、Bridgewater 中 `shadow of an shadow`）为讹形，引用时已照录并括号注明。
- **⑤ 的 "Examples" 续册与 Notes 未核**：续册（Examples and Results）与 Peacock/Herschel 的 Notes 是否含 Babbage 署名，未在语料内核实。
- **引文坐标粒度**：本道坐标到 source_id 级；如下游需要页/节级定位，① 可标 §(241–249)/(160–162)，④ 可标 Chapter VIII/IX，⑥ 可标 Introduction/Ch.XIII，但页码 OCR 不可靠，未逐一核。
