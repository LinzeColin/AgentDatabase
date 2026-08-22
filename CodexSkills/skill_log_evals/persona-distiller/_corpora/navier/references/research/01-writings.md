# Writings

## Scope and assigned sources

| source_id | 出版年 | tier | 题名 |
|---|---|---|---|
| src-4b7ed8ad4371 | 1833 | P1 | Résumé des leçons données à l'École des ponts et chaussées sur l'application de la mécanique（第二版，弹性/梁理论讲义） |
| src-2cf5fe26f051 | 1835 | P1 | Considérations sur les principes de la police du roulage, et sur les travaux d'entretien des routes（委员会报告，Navier 为起草人） |
| src-83dbfc1ebade | 1835 | P1 | Note sur le mouvement uniforme des waggons dans les chemins de fer en ligne courbe（Annales des ponts et chaussées） |
| src-11c8beafdc2c | 1836 | P1 | On the Means of Comparing the Respective Advantages of Different Lines of Railway（J. MacNeill 英译本） |
| src-b430f904cdde | 1819 | P1 | Examen de la tontine perpétuelle d'amortissement（年金数学） |

## Source-linked observations

- **惯例设计法在经验沉默处失灵，理论必须接管（对同行/营造者的批评）。** Navier 在前言梳理 Galilée、Bernoulli、Leibnitz、Euler、LaGrange、Buffon、Coulomb 的力学史后，直指大多数营造者按"既有惯例"和"现成范例"定尺寸、几乎不算部件实际受力与抗力——这在常规尺度内无害，但"当环境迫使人跳出这些界限，或涉及经验一无所知的新式建筑时"，就必须靠计算。这既是批评，也是他给自己讲义定下的存在理由。原文："La plupart des constructeurs déterminent les dimensions des parties des édifices ou des machines d'après les usages établis, et l'exemple des ouvrages existans; ils se rendent compte rarement des efforts que ces parties supportent, et des résistances qu'elles opposent."（1833，src-4b7ed8ad4371）；"Mais on ne peut plus en user de la même manière lorsque les circonstances obligent à sortir de ces limites, ou lorsqu'il s'agit d'édifices d'un genre nouveau, et sur lesquels l'expérience n'a rien appris."（1833，src-4b7ed8ad4371）

- **安全观：要的不是"断裂载荷"而是"可长期承载而不随时间劣化"的载荷；无法直接实验测定时，反用现存建筑经验取极限。** 这已近似现代的疲劳/时效安全思路，且体现他对"经验证据"的取用方式——把经久考验的现有构造当作可外推的实测样本。原文："il s'agit de connaître , non pas le poids qui rompt une pièce , mais le poids dont on peut la charger sans que l'altération qu'elle subit augmente avec le temps. La recherche de cette dernière limite, qui est de la plus grande importance, peut être rarement l'objet d'expériences directes ; mais on peut ici se servir avec avantage des exemples fournis par les constructions existantes."（1833，src-4b7ed8ad4371）

- **工程判断的审慎：经济是首要条件之一，但坚固与耐久同样重要；且不能因求经济就无限逼近安全极限。** 他把"逼近到什么程度"定义为一种技艺判断，而非公式能一劳永逸解决的事——这是他对"理论与工程实务之间张力"的明确自觉。原文："Parmi ces conditions, l'une des plus essentielles est l'économie; la solidité et la durée ne sont pas moins importantes."（1833，src-4b7ed8ad4371）；"Il ne faudrait pas conclure d'ailleurs que l'on doit toujours, pour avoir égard à l'économie, se placer tout près de ces limites. Les différences que l'on trouve dans les qualités des matériaux, et plusieurs autres motifs s'y opposent; l'art consiste principalement à juger jusqu'à quel point il est permis de s'en approcher."（1833，src-4b7ed8ad4371）

- **梁弯曲的方程化风格：把物理问题分解为纤维伸缩 + 截面平衡方程，并明确列出近似前提与适用边界。** 弯曲抗力被化为"纵向力平衡定中性轴 + 绕轴力矩等于 P(a−x)"，小挠度时忽略二阶小量；他同时划清"细长梁"前提——不满足则该式不可用。这种"先建方程、再注明何时失效"的写法是他的标志性论证风格。原文："On néglige les momens des forces verticales, ce qui est permis quand l'épaisseur du corps est petite par rapport à sa longueur. Il est nécessaire d'ailleurs que l'épaisseur du corps soit petite par rapport à sa longueur pour que les allongemens et accourcissemens des fibres, et les forces intérieures qui en résultent , soient telles qu'on le suppose ici ; et les résultats suivans ne peuvent être appliqués lorsque cette condition n'est pas satisfaite."（1833，src-4b7ed8ad4371）；推导结果："Ainsi la résistance à la flexion est proportionnelle à la largeur et au cube de la hauteur du solide."（1833，src-4b7ed8ad4371）

- **理论与实验的分工：弹性/断裂常数必须由实验测定；他重视微观实测细节并自引自家桥梁试验。** 讲义大量汇编各国实验（Buffon、Barlow、Lagerhjelm、Émile Martin 等），并回引自己在 Invalides 桥的铁材试验——卸载后精确回复原长、持续加载 12–36 小时伸长不增。这显示他既主张方程化，又把可测常数完全交给实验，二者缺一不可。原文："La force d'élasticité et la résistance à la rupture doivent être déterminées par l'expérience pour les diverses substances , et l'on s'est efforcé de rassembler tous les résultats de ce genre qui paraissaient être de quelque utilité."（1833，src-4b7ed8ad4371）；"Dans ces expériences la charge, portée jusqu'à 18 kil. par millimètre quarré, n'était pas assez grande pour altérer l'élasticité naturelle du fer. Il reprenait exactement sa longueur naturelle quand il était déchargé. L'allongement n'augmentait pas lorsque l'effort était exercé pendant 12 et même 36 heures."（1833，src-4b7ed8ad4371）

- **方法起点：讨论公共问题先"把问题摆得清楚精确"，且区分"信念"与"意志"。** 在《道路轮运警察》这份委员会报告的卷首，他明确把"清晰地提出问题"当作一切有益讨论的第一前提——这是面向行政/公共议题时他把自己工程师的分析习惯外推为公共方法。原文："La première chose à faire , lorsqu'on veut discuter utilement une question et la soumettre à un examen éclairé, est toujours de la poser d'une manière nette et précise."（1835，src-2cf5fe26f051）；"La conviction en premier lieu , en second lieu la volonté, semblent être deux élémens indispensables de tout ce qui peut être fait de grand et d'utile à la société."（1835，src-2cf5fe26f051）

- **工程师在公共辩论中的自我定位：替"无声的公共利益"发声，牺牲自身利益以尽职责，同时对舆论摇摆与私人利益保持冷静批判。** 在驳斥客运公司"取消限制"的游说时，他替工程师群体做了一个道德定位——工程师不因维持轮距/载重限制而获益，反而因此背负沉重责任，坚持制度纯出于公共利益；并冷静指出法国公共决策的常见怪圈：公共利益措施先被舆论热烈要求，政府一采纳就遭冷遇甚至反对，因为"私人利益比公共利益喊得更响"。原文："en donnant au gouvernement le conseil de maintenir les restrictions apportées aux chargemens du roulage et des messageries, les ingénieurs sacrifient leurs intérêts propres au sentiment de leur devoir, qui leur prescrit de proposer et de soutenir dans toute occasion, les mesures qui leur semblent le plus conformes aux intérêts publics."（1835，src-2cf5fe26f051）；"Nous voyons dans cette occasion , comme il arrive trop souvent en France , qu'une mesure d'intérêt général, réclamée d'abord par le vœu public avec la plus vive instance, est ensuite reçue avec froideur, et même avec opposition , lorsque le gouvernement finit par l'adopter."（1835，src-2cf5fe26f051）；"les intérêts particuliers parlent plus haut que l'intérêt public."（1835，src-2cf5fe26f051）

- **引证纪律与公平呈现反方证据：只引官方文本、给出可让读者自判的直译/摘录，并把赞成与反对自己立场的证据同样认真摆出。** 这是他论证风格的自我声明——把"可复核性"当作说服手段，而不是靠修辞压人。原文："On remarquera que nous citons toujours les textes officiels , et que la plupart du temps nous en donnons la traduction littérale , ou un extrait assez étendu pour que le lecteur puisse former lui-même son opinion , en rapportant avec le même soin les témoignages conformes aux notions que nous avons nous-même adoptées après un long examen , et ceux qui s'en écartent à quelques égards."（1835，src-2cf5fe26f051）

- **经济分析框架：把运输业拆成从业者、被服务公众、社会整体三重利益，并以"公共财富增长"为最高标准。** 他认为"公共利益"不等于"运输企业家的利益"——前者要求运费尽可能低，后者要求利润尽可能高；而判断载重制度的真正标尺是压低商业直接支付的运费（哪怕养路费略增），因为马力价值占运费至少四分之三、又随路况的牵引阻力变化。原文："L'intérêt du commerce en général , c'est-à-dire l'intérêt du public, n'est pas la même chose que l'intérêt des entrepreneurs de transport. L'intérêt du public exige que le prix moyen du transport soit le moindre possible. L'intérêt de l'entrepreneur est que son travail et ses capitaux lui rapportent les salaires et les bénéfices le plus élevés."（1835，src-2cf5fe26f051）；"la valeur du travail des chevaux formant toujours à elle seule la partie principale du prix du transport ( elle en est au moins les trois quarts) , ce prix s'établit surtout d'après l'intensité de l'effort de tirage nécessaire pour transporter un poids donné."（1835，src-2cf5fe26f051）

- **铁路曲线力学：把"过弯阻力"分析成可解方程，目的是让对新装置的判断"更有把握"。** 在这篇小论文里他明确说写作目标是为评判新装置提供可靠依据；同时把直行段阻力按经验取为与载荷 P 成正比（系数 φ），把离心力、横向/纵向滑移等逐一写成可解式——理论推导与实测系数并用的典型样例。原文："On essaiera , dans cette note , d'analyser les résistances particulières auxquelles donne lieu le passage des courbes des chemins de fer, dans la vue de mettre à même de porter un jugement plus assuré du degré d'avantage des dispositions nouvelles qui peuvent être proposées."（1835，src-83dbfc1ebade）；"on peut , conformément à ce que l'expérience a appris sur les chemins de fer , regarder la résistance dont il s'agit comme étant proportionnelle au poids P."（1835，src-83dbfc1ebade）

- **对同侪发明的克制评估：收益/代价量化权衡，不夸大新颖装置。** 他用自己推出的公式逐项测算 Laignel（不等径车轮）与 Verrier（车轮随曲线取向）两项发明实际能抵消多少过弯阻力（约 30/69 与 9/69），结论是"实用有限"、得不偿失，甚至用"把半径放大 3–7 倍就能让普通货车同样顺畅"来消解 Laignel 方案的卖点——评审式、算术式地说话，不因对方是提案人而客气。原文："Cette remarque semble atténuer beaucoup le degré d'utilité , assez restreint d'ailleurs , qui a été attribué à cette invention."（1835，src-83dbfc1ebade）；"les dispositions de ce genre ne procureraient probablement pas des avantages proportionnés à la complication à laquelle elles donneraient lieu dans la construction des waggons."（1835，src-83dbfc1ebade）

- **铁路选线比较：力求把"哪条线更好"归结为纯几何/力学量，其中"没有任何任意或不确定的成分"；并警告不能因速度快就随意加长线路。** 他把运输成本拆成"造价相关 + 吨位相关"两部分，主张只要造价、牵引功、长度三项都偏向一线，即可确定它更省运费，无需把各元素折成货币——这一"去任意性"的方法论同时服务于经济性判断。原文："The result of the comparison depends therefore entirely upon the determination of geometrical or mechanical quantities, in estimating which there is nothing arbitrary or uncertain."（1836，src-11c8beafdc2c）；"It would be committing a great error to suppose we may lengthen the line because the velocity of transport over it is great."（1836，src-11c8beafdc2c）

- **对权威/同侪批评的开放：因 de Prony 的一句提醒，重审旧作并主动承认对下坡效应"权重过大"、简化公式。** 这是最能蒸馏出他科学人格的段落之一——他没有辩护旧结论，反而说"我们越仔细研究，观念就越开阔越正确"，并公开收回先前计入的下坡效应修正项。原文："According as we examine with more care the circumstances depending on the use of locomotive engines on Rail-ways, our ideas become more extended and correct. I shall therefore return to the subject, on account of a remark which M. de Prony has been pleased to communicate to me upon some parts of the observations published in the preceding work."（1836，src-11c8beafdc2c）；"Nevertheless, in examining this subject more attentively, it will be perceived that we have attributed too great an influence to the effects of the descending slopes..."（1836，src-11c8beafdc2c）

- **自我定位与结论定性（年金数学）：声明无关个人利益、面向公共福祉，且裁决毫不含糊却保留可证伪性。** 在论文卷首他表态对金融投机全然陌生、无任何个人利益，把概率计算用于"公共利益对象"而非虚构问题；算完永续摊销年金后又断言该制度对行动人"必然不利"——"整个玩家群必然亏损，没有受益者就同时没有冤大头"；同时声明若有人能证明死亡率表失真，他"随时准备修改这个计算"。既下断语又留余地，是典型的"算式说话、接受反证"。原文："Cette recherche est une application du calcul des probabilités , qu'il m'a paru convenable de faire porter sur un objet d'utilité publique , plutôt que sur une question fictive."（1819，src-b430f904cdde）；"Complètement étranger, par ma situation particulière et par la nature de mes occupations, à toute spéculation financière , je n'ai pas besoin de dire qu'aucun intérêt personnel ne m'engage à publier cet écrit."（1819，src-b430f904cdde）；"cet établissement doit être assimilé à un jeu où l'ensemble des joueurs doit nécessairement perdre , et où il ne peut y avoir de gagnants sans qu'il y ait en même temps des dupes."（1819，src-b430f904cdde）；"si l'on a quelque moyen de prouver que, sur un grand nombre de personnes âgées de dix ans, il n'y en aura pas les 3/5 environ qui vivront encore 50 ans après, je suis tout prêt à réformer ce calcul."（1819，src-b430f904cdde）

## Candidate Claims

Pending.

## Contradictions and alternative explanations

Pending.

## Unknowns and source gaps

Pending.

## Proposed Holdout cases

IDs only; research Agents must not inspect Holdout bodies.

## Handoff to adjudication

Pending.
