# Writings 道 —— Rankine 的体系化著作与科学写作

## Scope and assigned sources

**本道分到 6 份（train split）**：

| source_id | 出版年 | tier | 题名 |
|---|---|---|---|
| `src-00aa2c4da15f` | — | P1 | A Manual of Civil Engineering (1861) |
| `src-2797b40bd6e6` | — | P1 | A Manual of Applied Mechanics (1858) |
| `src-2dd1b7bdeab3` | — | P1 | A Manual of Machinery and Millwork (1869) |
| `src-9d1c303213ab` | — | P1 | A Manual of the Steam Engine (1859) |
| `src-b538bc0041f9` | — | P1 | Miscellaneous Scientific Papers (1881) |
| `src-cef6df501532` | — | P1 | Remarks on Mr. Heppel's theory of continuous beams |

★ 本节由台账机械导出（`emit_lane_scope.py`），**不含任何阅读判断**；只投影 `split == train` 的行。

## Source-linked observations

★ **出版年说明（放在观测节而不是 Scope 节——Scope 节由工具拥有）**：台账 `published_at` 全为 null，Scope 表按机器渲染以「—」占位；各引文的出版年坐标取自该源题名页/序言自证年份（1858／1859／1861／1869／1881），`src-cef6df501532` 据文内「Received December 22, 1869」与脚注标 1870 年 1 月 27 日宣读，据此取 1870（台账标「1862 前后」，出入见「Contradictions」）。各印本版次晚于台账年份的勘定也见该节。

- **理论／实践割裂是工程界的头号公害，而正解是「科学地实用的技艺」。** Rankine 在《应用力学手册》的预备论文里断言：所谓理论与实践不合的「观念的错误影响」阻断了科学家与实务者之间的思想交流；他随后给出正面理想——那种「以最少材料与工耗取得最大效果」的技艺，在英伦实例稀少。这段话是他对工程师职业使命的一段宣言：理论不是装饰，是要被实践兑现的工具。
  原文：`"This it is which opposes the mutual communication of ideas between men of science and men of practice"`（1858，src-2797b40bd6e6）；`"of that scientifically practical skill which produces the greatest effect with the least possible expenditure of material and work"`（1858，src-2797b40bd6e6）

- **在理论家的眼里，结构物与机器首先是「实验数据」。** 同篇预备论文在讲纯科学那一支教育时，Rankine 说真理的查明与阐明是目的，结构物与机器「只是被当作自然物体」——其价值在于为确立原理提供实验数据、为阐述原理提供实例。这把「工程造物」在认识论上摆到了与自然物同等的「数据来源」位置，与他「理论必须建立在实测之上」的一贯立场一致。
  原文：`"The ascertainment and illustration of truth are the objects ; and structures and machines are looked upon merely as natural bodies are"`（1858，src-2797b40bd6e6）；`"as furnishing experimental data for the ascertaining of principles"`（1858，src-2797b40bd6e6）

- **应用科学是一个闭环：算理论极限 → 量实际差距 → 查原因 → 改进。** 在「第三种、居间的教育」那一段，Rankine 把工程师的能力定义为：按科学原理算出结构／机器的理论强度极限或效率极限，再查明实际造物距此极限差多少、找出短处的原因、设计改进以消除原因。他随后补了一句：这本领使工程师能判断一条惯用经验规则「几分建立在理性上、几分只是习惯、几分是错误」。这是他的方法论纲领——理论定界，实测对标，然后动手改。同种「理论预期→实验核验」的姿势在他书里反复出现，例如铰接柱的强度应等于两倍长固接柱，随即注明已被 Hodgkinson 的实验证实（`"conclusion verified by the experiments of Mr. Hodgkinson"`，1858，src-2797b40bd6e6）。
  原文：`"It enables him to compute the theoretical limit of the strength or stability of a structure, or the efficiency of a machine of a particular kind"`（1858，src-2797b40bd6e6）；续文 `"to ascertain how far an actual structure or machine fails to attain that limit"`、`"to discover the causes of such shortcomings"`、`"and to devise improvements for obviating such causes"`（1858，src-2797b40bd6e6）

- **土压力理论要「不借助任何技巧或假设」地从一条原理出发。** 《应用力学手册》Article 194 处理松散颗粒质量的摩擦稳定性时，Rankine 特意与 Coulomb 式「最弱阻力楔体」这类构造技巧决裂：他提出从唯一一条原理——沿任一平面的抗滑阻力等于两侧法向压力乘一常数（摩擦系数，即休止角正切）——出发，直接推出整个数学理论。这是他把工程问题「原理化、方程化」的典型动作：先立公理，再推公式，拒绝临时拼凑的几何技巧。该节脚注自称是从他 Phil. Trans.「1856-7」的论文 *On the Stability of Loose Earth* 大幅缩写而来。
  原文：`"I propose, therefore, to investigate the mathematical theory of the [版口：fiictional] stability of a granular mass, without the aid of any artifice or assumption"`（1858，src-2797b40bd6e6）。〔注：原文此处 OCR 讹为 "fiictional"（＝frictional），按本流水线版口标记法照录，不改字。〕

- **土压力理论的公理化起点：颗粒质量沿任何平面的压力方向不得偏离法线超过休止角。** 《土木工程手册》Article 183（论土压力与稳定）把松散颗粒质量稳定的充要条件表述为：任一分割平面处压力方向与该平面法线的夹角不得大于休止角。后面整套「共轭压力」公式（含那个以斜坡倾角与休止角表达的土压力系数）都由这条判据推出。这就是后世所称 Rankine 土压力理论的源头公式。
  原文：`"necessary to the stability of a granular mass, that the direction of the pressure between the portions into which it is divided by any plane should not, at any point, make with the normal to that plane an angle greater than the angle of repose"`（1861，src-00aa2c4da15f）

- **理论判据给完，转身用现存挡土墙的实际尺寸来标定安全系数。** 同书稳定墙一节，Rankine 在给出理论公式后不停在公式：他把「q」（压力合力相对墙底厚度中心的许用偏心率）的取值回收到实际工程上——按英国工程师的实践 q≈0.375，按法国工程师 q≈0.30～0.25——并注明这些是「由实际挡土墙尺寸反推的平均值」。这是「实测数据校准理论系数」的直接样本：理论给形状，实践给数值。
  原文：`"In retaining walls for sustaining the pressure of earth or of water, the following are average values of q deduced from the dimensions of actual retaining walls"`（1861，src-00aa2c4da15f）

- **理论有不确定处，就并列一条从实际例子归纳的经验规则。** 地下拱（隧道／涵洞）一节，Rankine 既给理论的解——压力线应为椭圆线形拱、其长短轴之比取水平与竖向土压之比的平方根——也明说该理论对某些情形不够确定，于是补充了一条「从实际例子中归纳出来」的最小厚度经验规则，并指出它与求拱顶石深度的经验规则完全同构。理论归理论，经验规则归经验规则，他让两者在手册里并存、各司其职。
  原文：`"the following empirical rule, exactly similar to that for finding the depth of the keystone of an arch, has been deduced from practical examples"`（1861，src-00aa2c4da15f）

- **示功图是他体系里「实测」与「热力学理论」的接缝。** 《蒸汽机手册》里，Rankine 把指示器画出的示功图面积当作流体施加在活塞上的能量（即指示功率）；而当目的是考察「热与功之间的热力学关系」时，他主张把多缸的示功图合成一张再分析。也就是说：实测功率从图上来，而热力学分析也借同一张图展开——测量与理论在他那里共用同一件工具。
  原文：`"the energy exerted on the piston"`（1859，src-9d1c303213ab）；`"the thermodynamic relations between heat"`（1859，src-9d1c303213ab）

- **设计问题本身被方程化：膨胀比是那个「起初未知、待求解」的量。** 在蒸汽机设计规则里，Rankine 把膨胀比 r 当作可能要反求的未知量——若它起初未知，则以「全压行程所占比例」等已知数据代入相应公式解出。他习惯把设计题列成「已知量—未知量—用哪条公式解哪个量」的清单，让工程问题可以照单演算。
  原文：`"the ratio of expansion r may at first be unknown"`（1859，src-9d1c303213ab）

- **材料强度几乎全靠实验定常数，理论只负责组织「怎么用」。** 《机械与磨坊手册》中 Rankine 明说：迄今几乎所有材料强度实验给出的都是「极限强度系数或模量」——材料将坏瞬间最受应力粒子处的应力强度。于是设计计算里材料常数来自实验表，理论只负责给安全系数的两种等价用法（乘工作荷载求破断荷载，或除极限模量得工作应力模量），并指出两者数学等价、后者更方便。实验供数、理论供算法，分工明确。
  原文：`"Almost all the experiments hitherto made on the strength of materials give co-efficients or moduli of ultimate strength; that is, co-efficients expressing the intensity of the stress exerted by the most severely strained particles of the material just before it gives way."`（1869，src-2dd1b7bdeab3）

- **活载对死载的「加倍效应」由理论推出，再转成设计规则。** 同书安全系数一节，Rankine 论证：实践中大多数情形下活载（突然施加或伴随振动，如驶过铁路桥的快车）产生或可能产生约等于同量死载两倍的应力应变效果；因此实践惯例是活载的安全系数取死载的两倍。动力学结论直接落成设计规则，论证与规则在同一段里。
  原文：`"It can be shown that in most cases which occur in practice a live load produces, or is liable to produce, twice, or very nearly twice, the effect, in the shape of stress and strain, which an equal dead load would produce."`（1869，src-2dd1b7bdeab3）

- **机械几何的教学选择：能画图就不算。** 《机械手册》序言里，Rankine 声明：既然这些规则的目的就是「用实用几何去调整零件尺寸」，他决定「每道题用画图解决、而不是用计算解决」，只在少数非算不可的场合才用计算。这是他一贯的教学表达——把解法尽量做成可视化、几何化，让读者能不依赖繁琐代数就把题目做出来。
  原文：`"Considering that the object of such rules is to adjust the dimensions of the parts of machines by processes of practical geometry, I have thought it advisable to solve every question by drawing, rather than by calculation, except in a few special cases where calculation is indispensable."`（1869，src-2dd1b7bdeab3）

- **物理理论观：先把形式定律归约成「最简原理系统」。** 《能量学纲要》（1855 年在 Glasgow 哲学会的讲演，1881 年收入合集）把认识进程分成两段：第一段观察现象（包括实验）并把观察到的关系表述为「形式定律」；第二段把一整类现象的形式定律归约成科学——即发现「最简的原理系统，使该类全部形式定律都能作为其推论被导出」。这样的原理系统及其有条理推出的后果，就构成这一类现象的物理理论。这是他把工程问题方程化背后的自觉纲领。
  原文：`"Such a system of principles, with its consequences methodically deduced, constitutes the physical theory of a class of phenomena."`（1881，src-b538bc0041f9）

- **工程判断的自我设限：数据不够硬，就不硬推理论。** 《砌石坝的设计与建造报告》（1872）里，Rankine 面对大坝内外面竖向压力限值的选取，明确说他「没有尝试」从固体应力分布理论去推出两面限值应有的比例——因为支撑任何这种理论判定的数据太不可靠；他改用实用限值。同一份报告里他还与执行工程师的「墙内倾悬挑」方案唱反调，理由是悬挑墙多得的抗水推力只等于其排水量以上的那部分重量、约只抵其一半效果。理论有用，但明知依据不足时宁可不硬推——这是他工程判断的谨慎。
  原文：`"I have not attempted to deduce the ratio which those quantities ought to bear to each other from the theory of the distribution of stress in a solid body"`（1881，src-b538bc0041f9）

- **把别人的理论缩写成「可教的形式」，并把可教学性当独立价值。** 在《连续梁》短论里，Rankine 称赞 Heppel 处理连续梁应力问题的方法清晰，尤其是「代数推演的每一步与应用于实践时算术计算的每一步严丝合缝」；但他仍主动把原理缩写成凝练形式，理由是「为了工程科学的教学」——并明确声明这不是新研究，只是 Heppel 研究的缩写版。这是他甘愿为教学做「次级工作」的少见自证：把他人成果重排成学生能学的形状，本身就是贡献。
  原文：`"Still it appears to me that, for the scientific study of the principles of the method, and for the instruction of students in engineering science, it may be desirable to have those principles expressed in a condensed form"`（1870，src-cef6df501532）；`"the several steps of the algebraical investigation correspond closely with the steps of the arithmetical calculations which will have to be performed in applying the method to practice"`（1870，src-cef6df501532）

- **拿自己已出版的公式去接受新方法的检验。** 同篇里 Rankine 说明：《土木工程手册》第 288 页那些关于等跨、交替轻重荷载的公式，正是建立在 Heppel 所述假设之上，因此他觉得「值得用 Heppel 的方法去检验这些公式」——并报告结果：令连续度 t=0 时完全吻合第 289 页的公式。把自己的手册当被检对象、用更严格方法复核，并如实报告吻合与适用边界（大跨度可靠、小跨度误差较大需修正），是这个人的自我检验纪律。
  原文：`"it therefore seems to me desirable to test those formulae by means of Mr. Heppel's method"`（1870，src-cef6df501532）

## Candidate Claims

Pending.

## Contradictions and alternative explanations

- **`src-cef6df501532` 的年份**：台账 attribution 记为「1862 前后」，但该源正文标题下方自记「Received December 22, 1869」，脚注标 1870 年 1 月 27 日宣读（见卷 xviii 页 178）——即这篇连续梁短论实为 1869 年底收到、1870 年发表。本道坐标统一采用 1870；台账的「1862 前后」与源正文自证冲突，建议 adjudication 复核台账。
- **各手册印本版次晚于台账首版年份**：《蒸汽机手册》印本题名页（Charles Griffin & Co., London）标 1870，属 1859 首版之后的重印；《土木工程手册》序言可读到第三版（1862）、第四版（1864）、第五版（1866）三次签名，本扫本至少为第五版（1866），而台账记为 1861 首版；《机械与磨坊手册》序言末见「The Seventh Edition has been revised … Glasgow, May, 1893」，本扫本为第七版（1893），台账记为 1869 首版。研究阶段坐标仍按各书首版出版年（1859／1861／1869），但这些印本是否经 Rankine 生前亲改、以及内容与首版的差异，需 adjudication 裁定是否影响「出版年」口径。
- **「Rankine cycle」一词不出现在语料中**：任务提示的目标概念在 `src-9d1c303213ab` 里对应的是「理想热机循环」（四步操作）与「效率只取决于两温度限、与工质性质无关」的 Carnot 律陈述，但该源 OCR 损坏极重，相关段落无法提供干净的逐字引文；本道只锚到「热与功的热力学关系」「能量施加于活塞」「膨胀比」等短引文，循环四步的具体描述属于「读出的转述、非逐字」，已在观测与 Unknowns 中标明。
- **两本手册的土压力表述一致、无内部矛盾**：《应用力学手册》Article 194-195 与《土木工程手册》Article 183 都从同一「休止角／共轭压力」原理出发，公式同源（Applied Mechanics 自称源自 Phil. Trans. 1856-7 的 *On the Stability of Loose Earth*）。

## Unknowns and source gaps

- `src-9d1c303213ab`（Steam Engine）是六源中 OCR 质量最差的：理想循环、Carnot 律、热力学函数所在段落几乎全部损坏，只能逐字引用极短片段；「理想热机四步循环」的转述（见观测）无法给出逐字原文锚。
- 台账 `published_at` 全为 null，各源出版年需人工从 attribution／题名页／序言勘定；各扫本的具体版次（除文中自记外）未知，见 Contradictions。
- *On the Stability of Loose Earth*（Phil. Trans., 1856-7）的原始论文正文不在本语料内，本道只有它在两本手册里的转写版（Applied Mechanics Article 194-195、Civil Engineering Article 183）；土压力理论在语料内的「一手论文原貌」不可直接核。
- `src-b538bc0041f9`（Miscellaneous Scientific Papers）卷内各篇年代跨度大（1855 讲演至 1872 报告），本道统一用 1881 卷年做坐标；单篇发表年（如 masonry dams 报告 = 1872）只在正文里写明，未进坐标。
- `src-cef6df501532` 文件开头 15 行是上一页（p.67）的续文，经页眉「Dr. W. J. M. Rankine on Mr. Heppel's」确认系 Rankine 本人论述（含对助手 Henry Reilly 的致谢与对小桥误差修正的说明），本道已使用其中的大／小桥适用边界句（见观测），但未给该句单独坐标段。

## Proposed Holdout cases

IDs only; research Agents must not inspect Holdout bodies.

## Handoff to adjudication

Pending.
