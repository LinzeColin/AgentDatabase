# Expression DNA and micro-behavior

## Scope and assigned sources

**本道分到 3 份（train split）**：

| source_id | 出版年 | tier | 题名 |
|---|---|---|---|
| `src-4f99e70027da` | — | P1 | Oeuvres divers : contenant: Catechisme d'économie politiq…ie et les travaux de l'auteur |
| `src-b68240fb3bd9` | — | P1 | Petit volume contenant quelques aperçus des hommes et de la société |
| `src-cfbc1f979683` | — | P1 | Olbie, ou, Essai sur les moyens de réformer les mœurs d'une nation |

★ 本节由台账机械导出（`emit_lane_scope.py`），**不含任何阅读判断**；只投影 `split == train` 的行。

## Source-linked observations

### ① 《Olbie》（1800）——用"场景/画面"取代"推理"的道德改革随笔

`src-cfbc1f979683` 是为法兰西学院征文（"以何种方式在一个民族中建立道德"）写的参赛文。卷首《Avertissement》交代了学院多次改题、最终无人获奖的经过，并**为 Say 自己的写法辩护**——他说学院批评他"用画面代替推理、把别人理论化的东西付诸行动"，而他认为"正是理论体系才是征题想要的"：

> ma méthode présente ... au lieu de raisonnemens, des tableaux ... met en action ce que d'autres ont ... mis en théorie et en système
<!-- src-cfbc1f979683 -->

（句中夹页眉 `Os ( viij)` 与 `))` 等扫描伪影，以省略号跳过；句意"我的方法以画面代替推理、把别人理论化的东西付诸行动"以改述补全。）

- **改革道德要靠两类制度**（教育未来的公民 + 改造已成年的公民；"à l'éducation"后夹脚注标 `(i)`，以省略号跳过）：

> il est deux sortes d'institutions dont il est nécessaire qu'ils s'occupent: celles qui doivent donner de bonnes moeurs aux hommes à venir, c'est-à-dire celles qui ont rapport à l'éducation ... et celles qui peuvent reformer les hommes faits.
<!-- src-cfbc1f979683 -->

- **"好风俗不过是好习惯"**：

> de bonnes mœurs ne sont que de bonnes habitudes
<!-- src-cfbc1f979683 -->

- **教育（instruction）的两重好处：使风俗温和＋让人看清自己真正利益**：

> L'instruction a, relativement aux mœurs, ces deux grands avantages: c'est d'abord qu'elle les adoucit, et, en second lieu, qu'elle nous éclaire sur nos vrais intérêts.
<!-- src-cfbc1f979683 -->

> c'est principalement en nous éclairant sur nos propres intérêts, que l'instruction est favorable à la morale.
<!-- src-cfbc1f979683 -->

- **自由国家尤其需要开明的人民，德与腐从权力顶端流下**：

> C'est sur-tout dans un état libre qu'il importe que le peuple soit éclairé.
<!-- src-cfbc1f979683 -->

> c'est du sommet du pouvoir que découle ensuite la vertu ou la corruption
<!-- src-cfbc1f979683 -->

- **"勤勉工人攒钱"vs"酗酒工人"的对照例**（把经济学伦理写成对照画面；句中 `raanouvrier`=manouvrier 的 OCR 形，中段被 pris de (fi) viï,batsafemme,corroinptparsonexemple 等大量扫描噪声阻断，以省略号跳过）：

> raanouvrier qui boit en quelques heures ses profits de la semaine ... calcule moins bien que cet ouvrier diligent qui, loin de dissiper ses petites épargnes, les accumule, ainsi que leurs intérêts
<!-- src-cfbc1f979683 -->

（`accumule, ainsi que leurs intérêts`=把小小积蓄连同利息一起攒起来。）

⇒ 声口：道德随笔采用"先立两类制度→再讲习惯/利益→再给对照画面"的结构；教育=启蒙利益=道德基础，是《Olbie》的心智指纹——**利益自觉**而非禁欲，是他与道德主义者的分界。

### ② 《Petit volume》（1839 第 3 版，Horace Say 编）——La Bruyère/La Rochefoucauld 式的警句集

`src-b68240fb3bd9` 是"关于人与社会的若干瞥见"的警句集；编者的《Avertissement》（Say 之子 Horace Say 所写）交代它 1817 年首版、1818 年二版售罄、作者生前还在反复修改直至去世（改述，二手编者层）。正文是 Say 自己的警句：

- **"世故经验在于反思过多少，而非见过多少"**：

> L'expérience du monde ne se compose pas du nombre de choses qu'on a vues, mais du nombre de choses sur lesquelles on a réfléchi.
<!-- src-b68240fb3bd9 -->

- **"升到一般之思=由事实溯到其法则"（牛顿苹果例；`cluites`=chûtes 的 OCR 形，照录）**：

> S'élever à des considérations générales c'est, à la vue d'un fait, remonter à la loi dont ce fait n'est qu'une conséquence.
<!-- src-b68240fb3bd9 -->

> Le premier il rapproche ce fait, insignifiant en apparence, de la déviation de la lune au-dessous de sa tangente; il mesure la rapidité de ces deux cluites; il trouve qu'elles appartiennent à une loi commune ... et voilà la gravitation universelle découverte.
<!-- src-b68240fb3bd9 -->

（`cluites`=chûtes（坠落）的 OCR 形照录；句中"que confirment toutes les autres observations"以省略号跳过。核心：从个别事实（苹果落地）跳到一般法则（万有引力）。）

- **"性格的坚定＋概括的禀赋=卓越之人"**：

> La fermeté de caractère, quand elle se trouve jointe à la faculté de généraliser, fait les hommes supérieurs. Ceux-là savent penser, et en même temps ils savent agir.
<!-- src-b68240fb3bd9 -->

- **"越聪明越看一般、少看个人"＋"未受争辩的真理常带被争辩的后果，要读行间空白"（借 Galiani；`con9 teste`=conteste、`cljerchez`=cherchez 的 OCR 形，均以省略号跳过）**：

> Une vérité non contestée a souvent des conséquences que l'on ... teste beaucoup. Elles ne sont pas exprimées ces conséquences; ... elles sont peut-être entre les lignes.
<!-- src-b68240fb3bd9 -->

（Galiani 那句"要读行间空白"以改述衔接。）

⇒ 声口：把认识论（归纳/概括/从个别到一般）压成一句句可记住的警句；人物身上"能想+能做"并列、"熟思胜于多闻"是其一贯气质。全本没有一处经济学行话，却在讲"从事实到法则"的方法——这正是他把经济学当"从观察到法则的科学"的散文版。

### ③ 《Oeuvres diverses》（1848）——生后合集：notice 层的"第三人称 Say"＋书信层

`src-4f99e70027da`（2.2M）是生后合集，含 Catéchisme、未刊片段、通信、Olbie、Petit volume、《Mélanges》，卷首有编者（Charles Comte 等）写的《Notice sur la vie et les travaux de l'auteur》。**notice 是二手视角**（编者明说取材自 Ch. Comte 1833 年旧 notice、Blanqui 1841 年悼词、Louis Reybaud 未刊稿，改述）。这一层对"第三人称的 Say 声口"极有价值：

- **"他的全部生活都献给了一套学说的形成与坚守"**（句中 `d'ine`=d'une、`inébraulable`=inébranlable 的 OCR 形，以省略号跳过）：

> Personne ne mit plus de soin que lui, n'employa plus de temps à se former un corps de doctrines; personne aussi, quand il fut formé, ne s'y attacha ... Ce fut avant tout un esprit exact, une intelligence sûre.
<!-- src-4f99e70027da -->

- **"事实站在他一边他接受；事实似乎反对他他仍坚持"**（编者对他的方法论画像；`donnaientrils`=donnaient-ils、`Il 1`=Il l' 等 OCR 形，以省略号跳过）：

> Les faits lui donnaient ... raison? ... acceptait sans orgueil comme une conséquence prévue. Semblaient-ils témoigner contre lui, il les discutait sans aigreur et remettait au temps ... soin d'effacer quelques anomalies passagères.
<!-- src-4f99e70027da -->

- **"了解自己的真正利益是道德的开端"（他本人的格言，被 notice 引述）**：

> Connaître ses vrais intérêts est le commencement de la morale; agir en conséquence est le complément.
<!-- src-4f99e70027da -->

> chacun n'écoute que son intérêt, disait Jean-Baptiste Say, je m'afflige du contraire.
<!-- src-4f99e70027da -->

（notice 作"On ne plaint que chacun n'écoute…"，"On ne plaint que"夹在前一页页脚与页眉之间，本引文从"chacun"起取；意：有人抱怨人人只谋私利，他说他难过的恰是相反——人们连真正利益都不懂。）

- **关于讲授：他从不即兴、课都写成稿**（notice 转述，原文 OCR 损毁严重，Je n'ai presque jamais été content de ma conversation 与 Si cela était facile, tout autre le ferait 两句在语料中均被扫描成不可读伪形，故**只改述不引**）：他自认几乎从不对自己的谈话满意，并说若写作容易则人人可为、何来荣誉与功绩。［改述，未逐字引］
<!-- src-4f99e70027da -->

- **"财富悖论"——国家财富由可交换价值构成、而价越低国越富**（notice 概括 Say 的命题；语料中 `ricfusse`=richesse、`Wautanl`=d'autant 等 OCR 形损毁严重，故**只改述不引**）：[改述，未逐字引]
<!-- src-4f99e70027da -->

- **克洛伊登窗户轶事**（少年在英国当学徒时，房东因英国"门窗税"封掉他两扇窗中的一扇；他说"我丢了一扇窗，国库啥也没得着"；`se di>ait-il`=se disait-il、`ga• cnr`=gagné 的 OCR 形，以省略号跳过）：

> J'ai perdu une fenêtre ... et le Trésor n'y a rien ...
<!-- src-4f99e70027da -->

（这则轶事由 notice 转述，是他"对税的反讽"的一手记忆被二手记录——既见他的税观，也见他把个人体验当论据的习惯。）

⇒ 声口：notice 层是**第三人称**，不能当 Say 亲述；但其中引述的格言（"了解真利益是道德开端"、"对谈话从不满意"）是 Say 亲口文本的转引，可信度介于一手/二手之间，引用时须标"经 notice 转引"；本道对 OCR 损毁过重无法逐字核验的句子一律降为改述，不设引文块。

## Candidate Claims

- C-E1（value）：道德改革=用教育（启蒙真利益）与习惯培养；"好风俗不过是好习惯"（src-cfbc1f979683 `de bonnes mœurs ne sont que de bonnes habitudes`；`c'est principalement en nous éclairant sur nos propres intérêts, que l'instruction est favorable à la morale`）。
- C-E2（expression）：以"画面/对照"代推理的随笔声口（src-cfbc1f979683 `ma méthode présente ... au lieu de raisonnemens, des tableaux`；src-b68240fb3bd9 勤勉工人/酗酒工人对照、牛顿苹果例）。
- C-E3（mental-model）：从个别事实到一般法则的概括方法（src-b68240fb3bd9 `S'élever à des considérations générales c'est, à la vue d'un fait, remonter à la loi`；`La fermeté de caractère, quand elle se trouve jointe à la faculté de généraliser, fait les hommes supérieurs`）。
- C-E4（value）：真利益=道德起点、利己主义之辩（src-4f99e70027da `Connaître ses vrais intérêts est le commencement de la morale`；`je m'afflige du contraire`——别人抱怨人人只谋私利，他反而难过人们连真利益都不懂）。
- C-E5（expression）：讲授从不即兴、追求最准确最快速的表述（src-4f99e70027da notice 转述，原句 OCR 损毁，仅改述：自认几乎从不对自己的谈话满意，且说若写作容易则人人可为）。

## Contradictions and alternative explanations

- **一手/二手层必须分清**：《Oeuvres diverses》的 notice 是编者（Comte/Blanqui/Reybaud 源）写的，`Personne ne mit plus de soin que lui`、Les faits lui donnaient-ils raison? 是**别人对 Say 的评价**，不是 Say 自述；而 `Connaître ses vrais intérêts`、`je m'afflige du contraire` 是 notice 转引的 Say 亲口格言。下游引用时前者按二手折减，后者可当一手转引。
- **《Olbie》的"画面代推理" vs 著作的"严格论证"**：Olbie 作者自陈用 tableaux 而非推理，而《Traité》《Cours》是严密论证——不是矛盾，是他按文体分工（随笔负责打动、论著负责证明）；这条分工本身就是声口特征。
- **"利益自觉=道德"与《Petit volume》对"无信念者"的讥讽**：他不反利益、反的是"只谋眼前小利/无信念"，两处是同一伦理的两面（notice 说他爱挖苦"无信念的人"，改述）。
- Petit volume 与 Oeuvres diverses 都含**编者（Horace Say / Charles Comte）**写的 Avertissement，凡"1817 首版、1818 二版"这类出版史信息均出自编者层。

## Unknowns and source gaps

- `src-4f99e70027da`（2.2M）只精读了 notice 层、Catéchisme 复排开头与零星通信引段（提到"您的 Catéchisme"的书信往来）；**通信正文、未刊片段、Mélanges 大部未通读**——若下游要他的私人通信声口（对 Ricardo/Bentham/Say 家族的信）需另案精读。
- `src-b68240fb3bd9`（172K）是警句集，本道只引了与"认识论/性格/利益"相关的若干条；全本其余警句（关于虚荣、男女、社交等）未穷尽，也未核对 1817 首版与 1839 第 3 版的增删。
- 法语语料重音普遍丢/混（`economie`/`économie`、`moeurs`/`mœurs`、`cluites` 旧形），本道一律照 OCR 原样，未做规范化。
- **notice 层多处 OCR 损毁到无法逐字核验**：Je n'ai presque jamais été content de ma conversation、"财富悖论"整句、"Si cela était facile..." 等在语料中均成伪形，本道一律降为改述并在 Unknowns 记录——下游如需这些名句的逐字文本，须另取更高质量扫描件。

## Proposed Holdout cases

IDs only; research Agents must not inspect Holdout bodies.

## Handoff to adjudication

- C-E1/C-E4 可合成一条"利益自觉伦理"簇，与 writings 道价值论、06-timeline 的"拒绝税官"决策互证——他主张"了解真利益"且自己按此拒官。
- C-E3 概括方法（从事实到法则）是认知指纹，建议与 writings 道"从观察出发反驳"、conversations 道"先立强对手再驳"合并为"认识论/论证方法"主簇。
- C-E2/C-E5 是表达层（画面代推理、写稿不即兴），可直接进 persona 文档；注意全部引文坐标须用〔年份 · 作品名〕而非 source_id。
