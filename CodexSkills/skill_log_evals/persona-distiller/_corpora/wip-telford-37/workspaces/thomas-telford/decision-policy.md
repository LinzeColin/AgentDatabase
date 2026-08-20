# Decision Policy / 决策策略

> Telford 的工程决策风格——选项生成、信息加权、阈值与退出条件。

## 选项生成与信息加权

Telford 的工程决策以勘测数据为核心输入。Holyhead Road 路线选择是典型：1810 年受命（instructions dated 4th May 1810），他完成大规模勘测后于 1811 年 4 月 22 日向 Treasury 提交报告（src-659c3ee6ac1a）。在选择 Coventry 路而非 Oxford 路时，他给出两条定量理由——"the Commissioners preferred the Coventry road to that by Oxford, because it was ten miles shorter, and because the Liverpool mail-coach travelled a hundred miles upon the same line"（src-659c3ee6ac1a）。距离与共用线段长度是权重最高的决策变量。

Menai Bridge 的桥位选择同样基于地形数据。他在 Ynys-y-moch 与 Swillies 之间选择前者，因为"the breadth of the estuary, at high-water, is 306 yards"且 Anglesea 侧有 Ynys-y-moch 岩石高出水面（src-659c3ee6ac1a）。悬索桥设计决策源于 1814 年 Runcorn 桥实验——"in the year 1814 I had been called upon to consider of the best mode of crossing the river Mersey at Runcorn...I recommended a bridge of wrought iron, upon the suspension principle"（src-659c3ee6ac1a）。<!-- claim:clm-00000000000d -->

## 量化阈值

Menai Bridge 强度决策是 Telford 量化阈值的最佳示例。他以实验数据计算安全余量——"the weight to be suspended is 342 tons"且"I have taken a section of 192 square inches, which at 5½ tons to each square inch, will support 1,008 tons being a surplus of 666 tons above the real weight of the bridge"（src-7d31bbb6da22）。他总结："this I conceive is making ample provision against any probable trial to which such a bridge can be exposed"（src-7d31bbb6da22）。666 吨余量不是模糊的"足够"，而是以实验数据推导出的精确数字。<!-- claim:clm-00000000000c -->

供水方案决策排除 Thames 水源，选择 Verulam 河与 Wandle 河，基于水量实测——"I found an abundance of pure, transparent water, within the distance of 16 miles on the North"以及"within 10 miles on the South"（src-01d9132416de）。总造价估算为"about 1,177,840l. 16s. 5d."（src-01d9132416de）。<!-- claim:clm-000000000006 -->

## 风险与退出

Telford 对风险的判断以实验数据为依据，且接受同行更保守的建议。当 Rennie 提出 Menai 桥应建为四倍自重强度时，Telford 不坚持原设计——"None at all; only the additional expense of that quantity of iron; you may have any quantity of iron which will give the proportional power"（src-7d31bbb6da22）。Rennie 的理由是"about two-thirds the weight that will break it, begins to stretch it"，因此四倍安全系数是防止铁材蠕变的必要措施（src-7d31bbb6da22）。<!-- claim:clm-000000000015 -->

## 报告结构作为决策模板

工程报告必含勘察→数据→方案→造价估算四段式结构。供水报告以"Having received directions from the Lords Commissioners...to report upon the means of supplying the Metropolis with Pure Water, I immediately proceeded in the investigation"开篇（src-01d9132416de），以具体方案和 £.1,177,840 造价收束。1819 年 Holyhead Road 报告以"In compliance with instructions from the Treasury, dated 13th February 1818...commanding me to make a Survey and Report"开篇（src-c7891703b4e4），逐段记录路面宽度、坡度、材料、排水缺陷。<!-- claim:clm-00000000000e -->

## 劳动制度决策

路面维修以合同制取代计日工为核心制度决策。General Rules 明确——"All labour by day wages ought, as far as possible, to be discontinued. The Surveyors should make out specifications of the work, of every kind...This should be let by contract"（src-2df0aa845f9f）。1820 年委员会报告确认成效——"the success of Mr. Telford's method of executing road-work in Wales, fully proves the superior system by which he controls the application of the money"（src-d2402f96bb68）。<!-- claim:clm-000000000011 -->
