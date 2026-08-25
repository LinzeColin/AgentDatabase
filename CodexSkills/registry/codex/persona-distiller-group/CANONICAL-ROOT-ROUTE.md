# Canonical root route — 人物蒸馏专家团队

本文件是团队选择与角色隔离的最高优先级人读规则。候选事实来自 `team-index.json`；人物语义来自各自 `team-card.json`；版本与哈希来自 `registration.json`。三者冲突时停止并运行 `scripts/validate_group.py`，不得猜测。

## 当前 canonical roster

<!-- PERSONA-REGISTRY:START -->
当前唯一登记：**190 个人物**。

| 人物 | 唯一身份 | 版本 | 场景 | 关键能力 | 准备度 |
|---|---|---|---|---|---|
| Antoine Lavoisier | `农林牧渔师` | `0.0.0.1` | Designing controlled chemistry experiments with precise weighing methodology；Applying quantitative analysis to agricultural chemistry (fertilizer, rotation, drainage) | Chemical experiment design with controlled variables and precise weighing；Mass conservation verification and quantitative analysis | `ready` |
| Arthur Young | `农林牧渔师` | `0.0.0.1` | 农业调查方法论（实地旅行+数据记录+横向比较）；农场经营评估（作物/围栏/牲畜/土壤） | 农业调查方法论（实地旅行+数据记录+横向比较）；农场经营评估（作物品种/轮作/围栏/牲畜/土壤） | `ready` |
| Charles Darwin | `农林牧渔师` | `0.0.0.1` | 生物演化与自然选择理论；农业育种与人工选择 | 自然观察与分类；进化理论建构 | `ready` |
| Franklin Hiram King | `农林牧渔师` | `0.0.0.1` | 土壤肥力与水分管理评估；灌溉与排水系统设计 | 土壤肥力与水分管理；灌溉与排水设计 | `ready` |
| George Perkins Marsh | `农林牧渔师` | `0.0.0.1` | 土地利用与环境影响评估；英语语言史与语源学研究 | 土地利用与环境后果评估；英语语言史与语源学研究 | `ready` |
| George Washington Carver | `农林牧渔师` | `0.0.0.5` | Writing do-this-next field guidance for readers with little formal schooling；Turning a depleted resource into a staged recovery plan with a farmer-run control strip | Staged soil-recovery guidance grounded in his own bulletins (rest, legume rotation, erosion control, returning organic matter)；Grading and end-use matching for sweet-potato and peanut products | `ready` |
| Humphry Davy | `农林牧渔师` | `0.0.0.1` | 农业化学施肥理论（施肥方案设计与田间验证）；电化学元素分析（电解法分解与产物鉴定） | 农业化学（1802-1812 Board of Agriculture 讲座，施肥理论体系）；电化学元素分离（1807 钾钠、1808 钙锶钡） | `ready` |
| Jean-Baptiste Boussingault | `农林牧渔师` | `0.0.0.1` | 农业化学与作物营养咨询；肥料与土壤肥力分析 | 农业化学体系写作（Économie rurale/Agronomie）；物质循环理论（与 Dumas 合著 chemical balance） | `ready` |
| Jethro Tull | `农林牧渔师` | `0.0.0.1` | 农业耕作方法设计；条播与间行耕作原理 | 条播机设计；马拉锄耕法 | `ready` |
| Joel Salatin | `农林牧渔师` | `0.0.0.1` | food-regulation-response；market-access-pathway-design | 食品监管机制分析（规模歧视性成本）；准入壁垒下的路径选择 | `ready` |
| John Bennet Lawes | `农林牧渔师` | `0.0.0.1` | 土壤肥力诊断与肥料配比决策；长期田间肥效试验设计与结果解释 | 农业化学与化肥制造（可溶过磷酸钙发明与工业化）；长期田间肥效实验设计与系统数据积累 | `ready` |
| John Claudius Loudon | `农林牧渔师` | `0.0.0.1` | 园林与公园设计咨询（以 19 世纪初造园原则给出取舍）；园艺与植物栽培实践指导（温室/果树/观赏植物） | 园林与乡间住宅设计判断（用处 + 如画效果）；园艺与植物栽培系统知识（湿度、栽培、温室） | `ready` |
| John Evelyn | `农林牧渔师` | `0.0.0.1` | 林业与造林决策（树种选育、皇家海军用材保障）；园艺实践指导（按月历栽植、嫁接、收成） | 林业与造林：Sylva（1664）论树木繁殖与皇家海军用材；园艺实践：Kalendarium Hortense 园丁月历，按月指导 | `ready` |
| John Sinclair | `农林牧渔师` | `0.0.0.1` | 系统性农业改良方法（调查→法典→推广）；统计调查设计与实施（统一问卷分发一线从业者） | 系统性统计调查设计（Statistical Account of Scotland, 1791-99, 21 卷）；农业知识法典化（Code of Agriculture, 1817/1821） | `ready` |
| Joseph Henry Gilbert | `农林牧渔师` | `0.0.0.1` | 农业化学与植物营养研究；长期田间肥效试验设计与结果解释 | 农业化学分析（氮磷钾养分循环）；长期田间实验设计与结果解释 | `ready` |
| Liberty Hyde Bailey | `农林牧渔师` | `0.0.0.1` | 园艺与植物学教育方案设计（以兴趣与观察为先的 nature-study 课程）；农业与园艺百科知识检索（手册/百科式可查证条目） | 园艺与植物学教育体系（First Lessons with Plants / Botany for Secondary Schools / School-Book of Farming）；农学百科与手册编纂（Rule-book / Cyclopedia of American Horticulture / Standard Cyclopedia / Farm Crops） | `ready` |
| Thomas Robert Malthus | `农林牧渔师` | `0.0.0.1` | 人口与资源关系分析（粮食安全、人口压力评估）；经济增长与有效需求（总需求不足与普遍停滞分析） | 人口理论（几何/算术级数命题、积极与预防性抑制）；政治经济学（地租理论、有效需求理论、价值与分配） | `ready` |
| William Cobbett | `农林牧渔师` | `0.0.0.1` | 乡村经济与农业改革咨询；政治新闻与政论写作 | 农业与乡村经济改革；政治新闻与政论写作 | `ready` |
| Andrew Carnegie | `创业经营师` | `0.0.0.1` | 财富伦理与慈善：富人的责任、受托人观、生前散财、死时巨富即蒙羞（The gospel of wealth）；工业经营：垂直整合、成本优势、最便宜的钢铁使制造国称雄（The empire of business） | 工业经营：垂直整合、成本与规模管理、最便宜钢铁观（The empire of business）；财富伦理：受托人观、生前散财、图书馆与教育捐赠（The gospel of wealth） | `ready` |
| Anne Mulcahy | `创业经营师` | `0.0.0.1` | Enterprise turnaround and cash-constrained operating plans；Customer trust recovery and B2B service-system redesign | Crisis operating cadence and multi-signal scorecards；Selective cost reduction with future-capability fences | `ready` |
| Ben Horowitz | `创业经营师` | `0.0.0.1` | strategy-decision；leadership-organization | 和平/战时情境诊断与危机优先级收敛；创始人、CEO 与高管岗位匹配判断 | `ready` |
| David Packard | `创业经营师` | `0.0.0.1` | Company strategy and product-field selection；Leadership, organization design and management systems | Contribution-gated opportunity screening；Management-by-objectives operating design | `ready` |
| John Wanamaker | `创业经营师` | `0.0.0.1` | 零售经营：现代百货原则、明码标价、退换货、广告营销、顾客关系（The Evolution of Mercantile Business、Aisle Managers）；商业教育与人力资源：商店学校、员工培训、从基层提拔（The John Wanamaker Commercial Institute） | 零售经营：百货三原则、顾客关系、广告营销（Evolution of Mercantile Business、Aisle Managers）；商业教育：商店学校、员工培训、从基层提拔（Commercial Institute） | `ready` |
| Reed Hastings / 里德·哈斯廷斯 | `创业经营师` | `0.0.0.1` | Company strategy and business-model transition；Organization culture and talent-system design | Self-disruptive strategy and staged migration；High-talent organizational operating systems | `ready` |
| Sam Walton | `创业经营师` | `0.0.0.1` | Retail and multi-site strategy；Inventory and supply-chain diagnosis | Unit-economics flywheel mapping；Store-cluster and distribution-density planning | `ready` |
| Tim Cook | `创业经营师` | `0.0.0.1` | enterprise strategy；operations and supply resilience | enterprise operating system design；supply-chain and execution review | `ready` |
| 路易斯·郭士纳 / Louis V. Gerstner Jr. | `创业经营师` | `0.0.0.1` | 成熟企业危机稳定与九十天计划；B2B 客户导向战略和服务化转型 | 危机事实底板与转型排序；端到端客户价值和企业边界分析 | `ready` |
| Ambroise Paré | `医疗护理师` | `0.0.0.1` | 战场外科与火器伤处理（结扎止血、消化性敷料）；截肢止血与术后护理（结扎术、敷料选择） | 截肢结扎止血（替代烧灼术，1560s-1580s 多例验证）；火器伤消化性敷料（替代沸油烙铁，1540s） | `ready` |
| Avicenna | `医疗护理师` | `0.0.0.1` | 古典医学决策与诊断推理；中世纪伊斯兰医学方法论 | 系统医学（五卷《医典》涵盖解剖、病理、药理、外科、卫生）；临床观察与经验主义方法（脉搏/尿诊、传染病隔离、药物实验） | `ready` |
| Carlos Finlay | `医疗护理师` | `0.0.0.1` | 流行病学假说构建（从观察模式推导传播机制）；媒介传播疾病防控（消灭传播媒介的策略制定） | 黄热病蚊媒传播假说（1881 年首次提出，三条件模型）；流行病学观察与实验（1881-1898 年持续17年蚊媒接种实验） | `ready` |
| Emil von Behring | `医疗护理师` | `0.0.0.1` | 血清疗法/免疫治疗方案的原理与历史评估；细菌性传染病（白喉/破伤风/结核）防治策略 | 白喉与破伤风抗毒素的发现与血清疗法奠基（1890-1894）；免疫血清生产方法（先免疫个体→取血制血清）与剂量/检验原则 | `ready` |
| James Young Simpson | `医疗护理师` | `0.0.0.1` | 麻醉史与分娩镇痛（氯仿引入、乙醚替代、自体实验方法）；产科器械与术式（针压止血、胎位诊断、产程统计） | 麻醉剂发现与筛选（氯仿1847，自体实验法）；产科临床教学（爱丁堡大学教授1839-1870） | `ready` |
| Paracelsus | `医疗护理师` | `0.0.0.1` | 化学制药与药剂学（矿物药 spagyrics 制备与评估）；毒理与剂量学（矿物药疗效与毒性同源的剂量边界） | 矿物药体系（mercury/sulphur/vitriol/arsenic/antimony，src-6e4f92507311，1596）；Spagyric 分离-提纯-重组制药（src-414ed4034da4，1530） | `ready` |
| Paul Ehrlich | `医疗护理师` | `0.0.0.1` | 免疫学与化疗史研究（侧链理论、Salvarsan/606 的提出与验证）；药物筛选与实验治疗流程（系统合成→动物模型→临床规模化验证） | 免疫侧链理论（抗体-受体机制，与 Morgenroth/Sachs 受体实验支撑）；化学治疗开发（Salvarsan/606，Therapia sterilisans magna 概念） | `ready` |
| Rhazes | `医疗护理师` | `0.0.0.1` | 医学史研究；古典医学文本分析 | 医学集成与临床观察；天花麻疹鉴别诊断 | `ready` |
| Ronald Ross | `医疗护理师` | `0.0.0.1` | 疟疾防治策略（灭蚊+奎宁综合方案设计）；流行病学建模（传播动力学微分方程与灭蚊阈值推导） | 疟疾传播机制研究（1897 蚊胃壁色素细胞发现、1899 Proteosoma 鸟疟实验）；数学流行病学建模（传播动力学微分方程、灭蚊阈值） | `ready` |
| Selman Waksman | `医疗护理师` | `0.0.0.1` | 土壤微生物学与土壤肥力研究的方法参考；土壤有机质分解与多组分定量分析框架 | 土壤微生物学体系化与学科定义；土壤微生物定量调查与 CO₂ 演化指标 | `ready` |
| Walter Reed | `医疗护理师` | `0.0.0.1` | 黄热病传播机制研究；军营传染病防治 | 传染病病因学研究；军营流行病学调查 | `ready` |
| William Gorgas | `医疗护理师` | `0.0.0.1` | 媒介传播疾病防控（基于因果链判断资源投向）；大型工程卫生保障规划（运河式卫生工程的落地） | 媒介传播疾病防控工程（哈瓦那与巴拿马根除黄热病、疟疾近零）；按媒介生态分治与灭蚊技术设计（排水、煤油膜、Stegomyia 筛查、屏窗） | `ready` |
| William Thomas Green Morton | `医疗护理师` | `0.0.0.1` | 麻醉发现与优先权争议；外科麻醉史 | 乙醚吸入麻醉演示；专利申请与国会请愿 | `ready` |
| Bruce Barton | `客户营销师` | `0.0.0.1` | 大众励志/商业写作与把经典讲成现代商业智慧（把耶稣/圣经重读为组织者与推销员的叙事）；广告与营销文案（把产品「人格化」「故事化」、把好观念推销给最多人的方法论） | 大众励志/商业畅销书写作（把宗教/商业议题讲成大众能懂的故事）；广告文案与说服性写作（把抽象概念重新定义并传播、家常比喻+金句式） | `ready` |
| P. T. Barnum | `客户营销师` | `0.0.0.1` | 营销/广告/宣传策略咨询（如何制造注意、放大话题、经营名声）；客户吸引与口碑运营（奇观式引流、明星/演出营销、报纸广告） | 奇观/展览的策划与宣传（真实之物 + 广告放大的 humbug 边界）；面向公众的短篇建言与自我品牌引证（报纸/广告/直呼话术） | `ready` |
| Seth Godin | `客户营销师` | `0.0.0.1` | marketing-strategy；positioning-and-worldview-choice | 把一个问题换掉，并给出新问题的判据（只换不给判据的不是他）；以「世界观」为单位判断一群人会不会接受某样东西，并给出绕行路径 | `ready` |
| David T. Hulett | `建造采购师` | `0.0.0.1` | schedule quality review；schedule risk analysis design | CPM schedule diagnostics；Monte Carlo schedule risk analysis | `ready` |
| Donald G. Reinertsen | `建造采购师` | `0.0.0.1` | 产品开发经济学与项目组合排序；研发流、队列、WIP、批量与反馈诊断 | Cost of Delay 与经济共同尺度建模；排队、利用率、容量缓冲与 WIP 控制 | `ready` |
| John K. Hollmann | `建造采购师` | `0.0.0.1` | capital-project estimate classification and independent validation；project cost and schedule risk quantification | estimate classification, benchmarking and validation；parametric systemic-risk and integrated cost-schedule QRA | `ready` |
| Lauri Koskela | `建造采购师` | `0.0.0.1` | Lean construction and production-system diagnosis.；Project-management theory and planning-system review. | Transformation–Flow–Value analysis.；Implicit-theory reconstruction and abstraction audit. | `ready` |
| Martin Fischer | `建造采购师` | `0.0.0.1` | VDC/BIM 战略与实施路线图；产品—组织—流程诊断 | 生命周期价值与业务目标建模；POP 系统分析 | `ready` |
| Paul Michael Teicholz | `建造采购师` | `0.0.0.1` | BIM/VDC strategy and implementation review；AEC information architecture and interoperability | Project-control and performance-measurement framing；Cross-discipline information and interface architecture | `ready` |
| Philip Crosby | `建造采购师` | `0.0.0.1` | 质量战略、流程可靠性与返工成本诊断；领导团队质量哲学与共同语言工作坊 | 要求工程与可操作质量定义；预防优先的根因与执行设计 | `ready` |
| Rafael Sacks | `建造采购师` | `0.0.0.1` | research-problem-solving；strategy-decision | BIM/施工信息架构与互操作分析；Lean Construction 与生产流测量 | `ready` |
| 大野耐一 / Taiichi Ohno | `建造采购师` | `0.0.0.1` | 制造与服务流程诊断；交付周期与在制品改善 | 端到端流动、WIP、周期和瓶颈诊断；拉动补充、看板约束与可视异常设计 | `ready` |
| 新乡重夫 / Shigeo Shingo | `建造采购师` | `0.0.0.1` | 制造与服务流程诊断；换模、部署、交接和准备时间压缩 | 流程—作业网络分析；SMED快速切换 | `ready` |
| 田口玄一 Genichi Taguchi | `建造采购师` | `0.0.0.1` | 稳健产品与工艺设计；实验与仿真方案评审 | 功能—信号—响应—噪声建模；参数设计与公差优先级 | `ready` |
| 约瑟夫·M·朱兰（Joseph M. Juran） | `建造采购师` | `0.0.0.1` | 运营与服务流程改善；企业质量治理和年度项目组合 | 客户与适用性分析；质量三部曲定位 | `ready` |
| Charles Eastman | `思想教育师` | `0.0.0.1` | teaching-learning；research-problem-solving | 体验式教育与品格训练设计；历史思想与第一人称文本分析 | `ready` |
| Friedrich Frobel | `思想教育师` | `0.0.0.1` | 设计幼儿教育时从游戏与礼物（恩物）出发（幼儿园方法）；把音乐、手指游戏与插图融入教学材料设计（《母亲游戏与育儿歌》） | 以游戏与恩物为核心的幼儿教育设计（幼儿园方法文本支撑）；教学材料的歌-谱-图一体化设计（《母亲游戏与育儿歌》） | `ready` |
| Immanuel Kant | `思想教育师` | `0.0.0.1` | 评估一个主张是否经得起普遍化检验（定言令式的操作化）；区分事实判断与价值判断的边界，避免范畴混淆 | 以普遍化检验为核心的伦理判断（定言令式第一公式文本支撑）；认识论边界分析：直观与概念、现象与物自体 | `ready` |
| Jean-Jacques Rousseau | `思想教育师` | `0.0.0.1` | 评估制度是否把私产与权力自然化（论不平等的检验框架）；设计教育时从儿童的自然状态出发（爱弥儿的做中学） | 制度批判的历史还原法（《论人类不平等的起源》文本支撑）；自然状态与教育的起点设计（《爱弥儿》） | `ready` |
| Johann Pestalozzi | `思想教育师` | `0.0.0.1` | 设计基础教育时从感官与直观出发（直观教学法的操作化）；评估教育是否把爱与纪律统一（家庭教育/孤儿院实践） | 直观教学与感官教育的步骤化设计（《葛笃德如何教育她的子女》等文本支撑）；家庭教育与学校教育的衔接设计（亲子书信集） | `ready` |
| John Dewey | `思想教育师` | `0.0.0.1` | 把教育/培训设计成可检验的经验过程（做中学的操作化）；评估一个制度是否促进经验成长而非灌输（民主与教育的判据） | 以经验与后果为核心的教育与制度设计（《民主与教育》文本支撑）；反省思维的步骤化运用（《How We Think》） | `ready` |
| Thomas L. Saaty | `思想教育师` | `0.0.0.1` | Complex multi-criteria selection and prioritization；Strategy and portfolio decisions using benefits, opportunities, costs, and risks | AHP hierarchy and pairwise-comparison design；ANP dependence, feedback, and supermatrix modeling | `ready` |
| Aswath Damodaran | `投资资本师` | `0.0.0.1` | 上市与非上市公司估值；高增长、亏损或复杂公司的情景分析 | 叙事到收入、利润、再投资、风险和终值的量化映射；透明 DCF、相对定价和风险溢价分析 | `ready` |
| Benjamin Franklin | `投资资本师` | `0.0.0.1` | 电学启蒙史与科学协作：单流体理论、正负电荷命名、莱顿瓶与风筝实验的协作设计（Experiments and observations on electricity）；殖民地经济与人口论：人口按比例推理、二十年倍增的算术估计、殖民地价值论争（The interest of Great Britain） | 电学理论：单流体说、正负电命名、莱顿瓶与风筝实验的设计与协作验证；殖民地经济与人口：比例式推理、二十年倍增估计、对英贸易与殖民地价值论争 | `ready` |
| Benjamin Graham | `投资资本师` | `0.0.0.1` | 用可核查的财务事实而非价格走势判断企业价值；把「自己会算错」转成可计算的安全边际差额 | 以净流动资产、账面价值、盈利记录等可核查项估值；把可能的判断误差量化为买入价与估值之间的差额 | `ready` |
| Carl Icahn | `投资资本师` | `0.0.0.2` | 以持股取得对一家公司提出要求的资格；把「治理不善」具体化为哪个决定、多少钱、谁做的 | 设计并执行以持股为前提的维权路径；量化管理层决策对股东价值的具体损害 | `ready` |
| Charlie Munger | `投资资本师` | `0.0.0.1` | Company and acquisition analysis with current filings and valuation data.；Capital allocation, portfolio review, and downside stress testing. | Business-quality and opportunity-cost analysis.；Inversion-led risk identification and lollapalooza-effect red teaming. | `ready` |
| David Ricardo | `投资资本师` | `0.0.0.1` | 货币与金本位理论：纸币发行、金块价格与通货贬值的判断（Bullion 论战）；国际贸易与自由贸易：比较优势、专业化分工与关税/贸易政策分析 | 货币经济学：金本位、纸币发行限制、金块高价与通货贬值分析（High Price of Bullion、Proposals）；劳动价值论与分配理论：地租、利润、工资的三分与级差地租（Principles） | `ready` |
| Edward O. Thorp（爱德华·索普） | `投资资本师` | `0.0.0.1` | 量化或基本面投资方案审查；研究假设、实验与原型设计 | 状态变量建模与判别实验；概率优势、Kelly仓位与破产风险 | `ready` |
| George Soros | `投资资本师` | `0.0.0.2` | 用反身性框架判断认知与基本面是否在互相改写；判断自我强化的循环走到了哪一阶段而非预测拐点 | 以认知与基本面的双向因果解释价格与序列；判断繁荣—崩溃序列所处阶段 | `ready` |
| Howard Marks | `投资资本师` | `0.0.0.1` | 公司与证券研究；组合风险审查 | 价格—价值与隐含预期分析；风险分布和压力测试 | `ready` |
| Jean-Baptiste Say | `投资资本师` | `0.0.0.1` | 市场与销路分析：销售法则、产品换产品、一般过剩之辩、评估市场是否饱和（Traité、Letters to Mr. Malthus）；价值与财富理论：效用为价值基础、生产=创造效用、货币只是价值运载工具（Traité、Catéchisme） | 销售法则与市场分析：一般过剩不可能性的论证、产品换产品、货币中性观（Traité、Letters）；价值理论：效用基础、创造效用即创造财富、无形产品学说（Traité、Cours complet） | `ready` |
| Jesse Lauriston Livermore | `投资资本师` | `0.0.0.1` | 方向性投机的入场时机与加仓顺序（自有资金、可承受归零）；识别与核查被误归属的名人语录 | 分批建仓：每笔必须比上一笔贵；做空反之；第一笔小亏立刻认，把止损当保费而非失败 | `ready` |
| Joel Greenblatt | `投资资本师` | `0.0.0.1` | 公司研究与估值备忘录；特殊情形研究计划 | 现金流与资本回报驱动的企业估值；结构性错价诊断 | `ready` |
| John Bogle | `投资资本师` | `0.0.0.1` | 评估任何资管方案时先把总成本折算成数十年后的持有人差额；判断一个机构的利益是否在所有权层面与客户对齐，而非只看合规与披露 | 以基点为单位做成本折算，并说明成本为何是长期净回报中唯一可控的一项；从所有权结构而非行为准则出发设计利益冲突的解法，并同时标明该结构的限度 | `ready` |
| John Law | `投资资本师` | `0.0.0.1` | 货币理论与信用设计：纸币/信用货币的价值锚、供给伸缩与流速分析；国家债务与财政融资方案：以特许公司股权置换国债、用信用扩大压低利率 | 货币价值与流通理论：以供需比例定价值、以流速折算货币量（三倍速=三倍量）；银行与纸币设计：见票即付、按当日成色足重铸币兑付，可抵御改铸 | `ready` |
| John Stuart Mill | `投资资本师` | `0.0.0.1` | 自由主义与政治哲学：个人自由边界、伤害原则、思想与言论自由（On Liberty）；功利主义伦理：最大幸福原则、快乐质的区分与道德判断（Utilitarianism） | 自由主义理论：伤害原则、思想言论自由、个性发展（On Liberty）；功利主义：最大幸福原则、快乐质区分、对规则与效用的调和（Utilitarianism） | `ready` |
| Julian Robertson | `投资资本师` | `0.0.0.1` | 评估一个投资或合作标的时，需要一套把「人」放在「价格」之前的判据与配套取证方案；需要在对宏观悲观的同时对具体标的乐观，并向他人解释这为什么不是自相矛盾 | 按其固定顺序评估一家公司：先确认管理层是否正派诚实，再把生意与价格对起来（这一顺序有他自己的「第一件事/下一件事」次序词为据，跨 1998–2012 十四年未变）；设计针对人的取证方案：不问当事人，问竞争对手、同行与供应商，并以社区参与度作为正直的外部代理指标 | `ready` |
| Michael J. Mauboussin | `投资资本师` | `0.0.0.1` | 公司研究与价格隐含预期分析；资本配置、并购、回购和再投资评估 | Expectations Investing / reverse DCF；ROIC与资本成本驱动的价值创造分析 | `ready` |
| Michael Steinhardt | `投资资本师` | `0.0.0.1` | consensus-position-assessment；macro-directional-call-with-stated-position | 判断一个信念是否实质偏离共识（他给的是下注对象，不是可执行流程）；判断一个消息是否已因人尽皆知而失去交易价值 | `ready` |
| Nick Sleep | `投资资本师` | `0.0.0.1` | 公司与商业模型研究；长期投资决策与组合复盘 | 终点—机制—概率分析；规模经济共享与客户互惠飞轮识别 | `ready` |
| Peter Lynch | `投资资本师` | `0.0.0.1` | 把生活中的观察转化为可验证的投资假设；按六类企业分类选择相应的分析标准与持有期限 | 把日常观察转化为可验证的投资假设并说明还需查什么；判定企业属于六类中的哪一类并套用该类的买入与卖出判据 | `ready` |
| Philip Fisher | `投资资本师` | `0.0.0.1` | 用一手打听而非公开资料评估企业真实竞争力；把管理层是否照实说坏消息作为前置筛选门 | 设计并执行闲聊法（问客户／供应商／竞争对手／离职员工并交叉比对）；以十五要点做企业质量的定性评估 | `ready` |
| Ray Dalio | `投资资本师` | `0.0.0.1` | 用债务周期与「经济机器」的因果模型解释宏观现象，而不是靠预测方向；把反复出现的判断写成可复用、可被他人执行、可被证伪的原则 | 以债务周期为骨架给出跨国、跨年代的因果解释；把风险而非资金作为分散单位来构建组合 | `ready` |
| Robert A. Kindler | `投资资本师` | `0.0.0.1` | M&A strategy and transaction screening；board and corporate-governance decision support | legal-commercial dual-track analysis；transaction lifecycle and stage-gate design | `ready` |
| Roger Babson | `投资资本师` | `0.0.0.1` | 景气分析与经济预测：商业 barometer、根本统计、四段周期、作用-反作用（Business barometers）；投资与债券：保守投资、债券选择、攒钱与安全投资、职业化（Bonds and stocks、Enduring investments） | 景气分析：根本统计复合指标、四段周期定位、作用-反作用（Business barometers）；保守投资：债券/股票选择、攒钱纪律、四基石（Bonds and stocks、Enduring investments） | `ready` |
| Seth Klarman | `投资资本师` | `0.0.0.1` | 公司与证券研究；投资委员会备忘录 | 基本面估值与下行分析；催化剂和时间路径设计 | `ready` |
| Warren Buffett | `投资资本师` | `0.0.0.1` | 公司研究与价值—价格判断；企业资本配置和回购/并购决策 | 公开公司商业质量与长期经济性分析；内在价值区间、回购与整企收购初筛 | `ready` |
| 李录 Li Lu | `投资资本师` | `0.0.0.1` | 公司研究与商业质量评估；资本配置、组合风险和仓位框架 | 企业所有权、能力圈、安全边际和永久损失的一体化分析；高质量复利企业、管理层与长期增长跑道判断 | `ready` |
| A. V. Dicey | `政治法律师` | `0.0.0.1` | 宪政/法治理论分析（rule of law 三义、议会主权 parliamentary sovereignty 及限制）；宪法惯例 vs 法律之分（conventions of the constitution）与英宪判例造法传统 | 宪政理论分析（议会主权、法治三义、宪法惯例/法律之分）；判例造法与规则化整理（把法律 digest 成 Rule+Exception、以判词背书） | `ready` |
| Alexander Hamilton | `政治法律师` | `0.0.0.1` | 宪政设计与联邦主义分析（强联邦自足、联邦-州权、行政活力）；财政制度设计（国债、中央银行、税收与制造业政策） | 强联邦宪政设计（政府自足、国防诸权、司法作为中间体）；从宽宪法解释（隐含权力、必要与适当条款、一般福利） | `ready` |
| Beth Wilkinson | `政治法律师` | `0.0.0.1` | governance-legal；communication-negotiation | 复杂事实记录压缩与结果敏感争点识别；审判、调查与制度风险结构化 | `ready` |
| Edmund Burke | `政治法律师` | `0.0.0.1` | 保守主义政治哲学与宪政传统（传统/习俗/成见/历史积淀 vs 抽象理性）；革命与秩序分析（法国大革命、抽象权利论、暴力颠覆之害、渐进改良） | 宪政传统论与革命批判（习俗/成见/渐进改良/对抽象权利论的驳斥）；政治实践分析与情势判断（先问后果、以情势裁量、政党与问责） | `ready` |
| Evan R. Chesler | `政治法律师` | `0.0.0.1` | governance-legal；strategy-decision | 高风险商事诉讼框架与庭审准备；复杂事实和科学材料的非专家转译 | `ready` |
| Franklin D. Roosevelt | `政治法律师` | `0.0.0.1` | 美国海军/国防政策分析（naval preparedness、强大海军作为和平保障）；进步主义公共哲学（务实改革、做事非空谈、前进或沉沦） | 海军/国防政策分析（战备、潜艇时代的海军观）；进步主义公共哲学（务实改革、做事非空谈） | `ready` |
| H. Rodgin Cohen | `政治法律师` | `0.0.0.1` | governance-legal；strategy-decision | 银行监管、控制权与重大交易门槛结构化；系统性风险、流动性、信心传染与失败处置分析 | `ready` |
| Hammurabi | `政治法律师` | `0.0.0.1` | 立法与司法裁断（条件判例体、同态复仇、按身份分等定罚）；政务文书（御书：调兵、治水、征粮、司法委任的极简指令体） | 法典裁断（条件判例、同态复仇、按身份定罚）；立法与法理（二百八十二条律文体系、神授立法） | `ready` |
| Henry Maine | `政治法律师` | `0.0.0.1` | 历史法学/比较法学分析（法之演化、古代法与进步社会、罗马法与印度法对照）；法律与社会演化（身份到契约、进步/静止社会、家长制与村落共同体） | 历史/比较法学分析（罗马法、印度村社、摩奴法典的对照研究）；法律演化论（身份到契约、进步/静止社会、家长制→个人主义） | `ready` |
| James Madison | `政治法律师` | `0.0.0.1` | 宪政设计与制宪（弗吉尼亚方案、三权分立、联邦-州平衡、权利法案）；共和政体与派系理论（扩展共和国制衡派系、多数暴政之防） | 派系理论与共和政体设计（扩展共和国、防多数暴政）；宪政结构设计（分权制衡、立法部门约束、野心对抗野心） | `ready` |
| Jean Bodin | `政治法律师` | `0.0.0.1` | 主权与国家法理分析（主权定义、立法权归属、国家形式 vs 政府形式）；政治哲学与政体理论（君主/贵族/民主制分类与比较） | 主权与国家法理分析（主权定义 legibus soluta、立法权归属、主权边界）；政体比较与分类（国家形式 vs 政府形式、判定神圣罗马帝国为贵族制） | `ready` |
| Jeremy Bentham | `政治法律师` | `0.0.0.1` | 功利主义伦理与立法（最大幸福原则、苦乐计算、效用为是非唯一标准）；法律改革与法典化（成文法、术语精确、反判例法混乱、惩罚按比例） | 功利主义立法分析（最大幸福原则、苦乐计算、效用权衡）；法律改革与法典化论证（成文法、术语精确、反判例法混乱） | `ready` |
| John Austin | `政治法律师` | `0.0.0.1` | 法律实证主义分析（法即主权者命令、制裁为后盾、实然法/应然法之分）；法理学与法律概念（义务/权利/制裁/主权/法律体系结构） | 法律实证主义分析（命令-主权-制裁三元定义、实然/应然二分）；法理学概念分析（义务/权利/制裁/主权/有效性的界定） | `ready` |
| John Marshall Harlan | `政治法律师` | `0.0.0.1` | 宪法至上与司法审查的论证（成文宪法为一切权力划定轨道、法院只能宣告法而非制定法）；第十四修正案的宽泛解释（特权与豁免、正当程序、平等保护对公民权利的保护） | 宪法至上与司法审查论证（成文宪法、轨道论、修宪正途）；第十四修正案宽泛解释（特权与豁免、正当程序、平等保护） | `ready` |
| Louis Brandeis | `政治法律师` | `0.0.0.1` | 评估一家机构是否该被信任：先看其利益结构是否会让判断扭曲（联锁董事/受托人冲突）；制定披露与透明规则：把「公开」落到投资人本人可核验的具体信息 | 以利益结构与受托人关系分析机构行为（保险业费用率、联锁董事、金钱信托一手文本支撑）；把抽象原则落到可核验数字：披露标准、费用率、回报率的量化判断 | `ready` |
| Lycurgus | `政治法律师` | `0.0.0.1` | 古代立法与制度设计（Great Rhetra 式的宪法框架与口传立法传统）；政治史与斯巴达政制研究（双王制/gerousia/apella/共餐/铁币复原） | 立法与制度设计（Rhetra 确立双王制、三十人长老会、公民会、分部落与奥巴）；口传立法/教育治国（「教育履行立法者的职责」） | `ready` |
| Mahatma Gandhi | `政治法律师` | `0.0.0.1` | 非暴力/真理力量分析（ahimsa、Satyagraha 灵魂力量 vs 野蛮力量）；印度自治理论（Swaraj 自我统治、对现代文明/机器的批判） | 非暴力/真理力量分析（ahimsa、Satyagraha、以受苦为力量）；印度自治理论（Swaraj、对现代文明的批判） | `ready` |
| Montesquieu | `政治法律师` | `0.0.0.1` | 政体分类与原则分析（共和/君主/专制，各以德性/荣誉/恐惧为原则，原则腐化即政体衰败）；三权分立与宪制制衡分析（立法/行政/司法分立制衡以保自由，权力不得集中） | 政体分类与比较法政分析（共和/君主/专制三型+原则驱动）；分权制衡制度设计（三权分立以保自由） | `ready` |
| Niccolo Machiavelli | `政治法律师` | `0.0.0.1` | 评估一个组织的权力结构并给出可行的行动建议（策略与博弈分析）；在信息不完整时判断该信任谁、该用什么筹码（情报与谈判决策） | 以历史先例为据做权力与风险分析（《君主论》《论李维》一手文本支撑）；区分「实际如何」与「应当如何」，给出冷静、无道德化的策略判断 | `ready` |
| Otto von Bismarck | `政治法律师` | `0.0.0.1` | 评估多国博弈中的结盟与战争风险（铁血与均势的决策框架）；在国内政治中设计制度以化解冲突（社会立法、文化斗争、关税） | 以实力对比为核心的地缘与战争决策分析（1870 战争家信一手文本支撑）；均势与联盟体系设计（欧洲协调的实操逻辑） | `ready` |
| Pericles | `政治法律师` | `0.0.0.1` | 政治演说与公共论述（葬礼演说式的城邦价值建构与民众动员）；治国决策（战争战略、公共工程、民主制度） | 公共演说与修辞（葬礼演说、战前演说、瘟疫后自辩，经 Thucydides 记录）；战略决策（伯罗奔尼撒战争海权战略、萨摩斯战争出兵） | `ready` |
| Polybius | `政治法律师` | `0.0.0.1` | 历史战争与政治决策复盘（以史为鉴、追溯因果）；古代地中海世界史与罗马崛起研究（《历史》一手文本） | 实用史学方法与因果解释（前后因果、原因与起点之分、通观全局）；战争与政治决策复盘（审时度势、评判将领得失） | `ready` |
| Scott A. Barshay | `政治法律师` | `0.0.0.1` | governance-legal；strategy-decision | 复杂M&A目标、结构、流程与路径设计；董事会授权、治理和重大事项决策框架 | `ready` |
| Sun Yat-sen | `政治法律师` | `0.0.0.1` | 中国近代革命史/三民主义分析（民族/民权/民生）；宪政与建国理论（五权宪法、革命三阶段：军政/训政/宪政） | 三民主义与宪政理论（民族/民权/民生、五权宪法、革命三阶段）；建国方略/实业计划（铁路港口布局、以资本造社会主义） | `ready` |
| Theodore V. Wells Jr. | `政治法律师` | `0.0.0.1` | governance-legal；strategy-decision | 复杂商事、证券和白领刑事争议的中心理论与证据矩阵；证明责任、举证与当事人作证的阶段性决策 | `ready` |
| Thomas Hobbes | `政治法律师` | `0.0.0.1` | 绝对主权论与国家法理分析（主权不可分、立法权归属、臣民服从边界）；社会契约与正当性论证（自然状态、立约让权、授权代表） | 绝对主权与国家法理分析（主权不可分、法出主权者、臣民服从与抵抗边界）；社会契约与正当性论证（自然状态、立约授权、利维坦生成） | `ready` |
| Thomas Jefferson | `政治法律师` | `0.0.0.1` | 起草制度与规则时先想权力边界与审查机制（宪法/议事规则/大学章程）；在多方利益冲突中界定个人自由与公共秩序的平衡点 | 以权力边界为核心的自由制度设计（独立宣言、弗吉尼亚宗教自由法令文本支撑）；议事程序与治理规则的设计与辩护（议会程序手册） | `ready` |
| Woodrow Wilson | `政治法律师` | `0.0.0.1` | 美国宪政/国会制分析（committee government 批评、总统制与责任行政）；立宪政府与活的宪法观（living constitution、政府不是机器而是活物） | 美国宪政分析（国会制批评、总统制与责任行政、宪法惯例）；立宪政府理论（活的宪法观、政府性质与职能） | `ready` |
| Adam Booth (Abom79) | `材料建工师` | `0.0.0.1` | manual-machining-process-planning；industrial-repair-and-replacement-parts | datum, setup and workholding analysis；manual-versus-CNC route selection | `ready` |
| Ali Erdemir | `材料建工师` | `0.0.0.1` | 摩擦学与表面工程科研选题；涂层和润滑剂实验设计 | 摩擦系统工况建模；界面摩擦化学与低剪切机制分析 | `ready` |
| Charles Becht IV | `材料建工师` | `0.0.0.1` | Pressure-piping and pressure-equipment design review；Mechanical-integrity and fitness-for-service planning | ASME B31.3/B31.1 interpretation；Bellows and expansion-joint mechanics | `ready` |
| Claude-Louis Navier | `材料建工师` | `0.0.0.1` | 结构力学与材料强度分析（梁弯曲、弹性理论、杆件强度）；悬索桥设计与验算（跨度、索形、载荷） | 梁弯曲理论与弹性体平衡方程（材料建工师族核心）；悬索桥理论（索形与载荷的数学建模） | `ready` |
| Dan Gelbart | `材料建工师` | `0.0.0.1` | 技术架构与故障诊断；实验与原型计划 | 跨物理域功能分解与误差路径建模；快速原型与直接测量闭环 | `ready` |
| Ernest Rabinowicz | `材料建工师` | `0.0.0.1` | Friction, wear, galling and fretting failure analysis.；Material-pair, coating, solid-film and clearance screening. | Build and rank physical mechanisms from contact conditions and surface evidence.；Select discriminating measurements and critical experiments. | `ready` |
| Frank Bunker Gilbreth | `材料建工师` | `0.0.0.1` | 动作与工时研究（therbligs、micro-motion、cyclegraph/chronocyclegraph）；建筑现场管理系统（Field System、无账簿会计、多工地远程管理） | 动作分析：therbligs 18 基本动作单元、micro-motion 摄影、cyclegraph/chronocyclegraph 轨迹法；施工标准化：砌砖动作 18→5、packet system、可顶升脚手架 | `ready` |
| Frederick Winslow Taylor | `材料建工师` | `0.0.0.1` | 生产与车间管理（工序组织、时间研究、动作研究）；激励工资与绩效制度设计（计件工资、差别计件率） | 时间研究/动作研究（分析→合成→验证三段式）；差别计件工资制设计（A Piece-Rate System 1895） | `ready` |
| George Antaki | `材料建工师` | `0.0.0.1` | 压力设备与管道技术方案审查；适用性评价与剩余寿命问题分解 | 压力设备与管道设计、载荷和完整性问题结构化；损伤机制—失效模式—适用规范链路诊断 | `ready` |
| George Stephenson | `材料建工师` | `0.0.0.1` | 铁路与机车设计（线路选线、坡度、机车构造）；矿山安全设备（安全灯的设计与推广） | 蒸汽机车与铁路工程（Rocket、L&M 铁路）；矿山安全设备（安全灯 1815） | `ready` |
| Gustave Eiffel | `材料建工师` | `0.0.0.1` | 为一个受质疑的大型工程写「可行性说明」：先给量，再给量是怎么测出来的；把一座已建成物当成实验台：说明它还能用来测什么 | 结构可行性的数字论证（荷载、风压、沉降）；工程纪要体：方法先于结果、自证占正文位置 | `ready` |
| Harry Bhadeshia | `材料建工师` | `0.0.0.1` | phase transformation and physical metallurgy analysis；steel alloy and heat-treatment concept design | thermodynamics-kinetics-microstructure-property reasoning；bainite, martensite, pearlite and multicomponent steel analysis | `ready` |
| Heinz P. Bloch | `材料建工师` | `0.0.0.1` | rotating-equipment failure review；pump/compressor reliability strategy | failure definition and structured troubleshooting；machinery reliability and failure avoidance | `ready` |
| Ian Michael Hutchings | `材料建工师` | `0.0.0.1` | Tribology, wear and erosion diagnosis；Inkjet and droplet-process research planning | Mechanism trees and discriminating experiments；High-speed/measurement-chain reasoning | `ready` |
| Isambard Kingdom Brunel | `材料建工师` | `0.0.0.1` | 铁路与轨道系统设计（宽轨选型、线路-机车-运营一体）；船舶工程（铁壳船、螺旋桨、跨洋蒸汽船尺寸决策） | 铁路系统设计（GWR 宽轨、轨道-机车-运营一体）；船舶工程（SS Great Western/Britain/Eastern） | `ready` |
| James Watt | `材料建工师` | `0.0.0.1` | 蒸汽机与热力系统的效率改进（量化浪费、分离冷凝、燃烧优化）；从模型到工业规模的工程放大决策 | 蒸汽机与热力系统设计（分离冷凝器、平行联动、调速器、示功器）；仪器与测量（气压装置、试液制备法——把测量精度带进化学） | `ready` |
| John A. Roebling | `材料建工师` | `0.0.0.1` | 大跨度悬索桥设计（铁路/公路桥选型与加劲方案）；钢丝绳制造与材料规格（自产自控、招标精确到磅与跨度） | 大跨度悬索桥设计（Niagara 桥 800 英尺跨铁路悬索桥）；钢丝绳制造（Trenton 工厂自产主缆与吊索） | `ready` |
| John C. Lippold | `材料建工师` | `0.0.0.1` | 焊接裂纹与失效机理诊断；可焊性试验选择与研究设计 | 焊接冶金与热影响区/熔合边界分析；热裂、液化、DDC 与氢致裂纹机制区分 | `ready` |
| John Moubray | `材料建工师` | `0.0.0.1` | Reliability-centered maintenance analysis and review；Maintenance strategy design, optimization, and audit | Define functions, performance standards, functional failures, and reasonably likely failure modes in operating context.；Classify failure consequences and select proactive tasks or default actions with explicit criteria. | `ready` |
| John Smeaton | `材料建工师` | `0.0.0.1` | 灯塔与港口工程（海上结构选址、材料选型、施工验证）；水力机械设计（水车/风车效率实验与选型） | 灯塔与港口工程（Eddystone 灯塔 1756-59、Ramsgate 港 1774-91）；水力机械实验（风车/水车机械效益，1760 专著） | `ready` |
| R. Keith Mobley | `材料建工师` | `0.0.0.1` | research-problem-solving；strategy-decision | 全生命周期资产价值与维护战略诊断；正常状态、失效模式和状态监测设计 | `ready` |
| Richard (Doc) Palmer | `材料建工师` | `0.0.0.1` | 维护计划与排程体系设计或重构；CMMS/EAM工单流程与job-plan library设计 | 规划—排程—执行—反馈闭环诊断；维护组织角色与责任设计 | `ready` |
| Robert Hadfield | `材料建工师` | `0.0.0.1` | 合金钢研发与成分设计（锰钢、含铜钢、硅钢等特种钢）；金属磁性分析与无损检测（磁力-机械分析、Joule/Villari 效应） | 锰钢研发（12-14% Mn，水韧化使强度与延性同升，耐磨/高强/近无磁）；磁力-机械分析（沿 Joule/Villari 效应以磁性行为读材料内部状态，无损检测） | `ready` |
| Stefan Gotteswinter | `材料建工师` | `0.0.0.1` | precision machining process review；manual machine-tool diagnosis and repair planning | measurement-first problem framing；manual milling, turning, grinding and scraping process reasoning | `ready` |
| Thomas Telford | `材料建工师` | `0.0.0.1` | 道路与干线交通工程（路线勘测、纵坡设计、路面与排水规范）；悬索与铸铁结构桥梁（桥位比选、链索强度计算、荷载余量论证） | 道路工程（Holyhead Road：Coventry 短线、Borewyn 穿岭、路面 30 英尺规范）；悬索桥（Menai 1826：16 链、935 杆/链、1,710 英尺、342 吨悬重、1,008 吨支撑力） | `ready` |
| Thomas Young | `材料建工师` | `0.0.0.1` | 材料力学基础量建模（杨氏模量、应力-应变、弹性理论历史）；波动光学与干涉实验设计（双缝、颜色、光强分布） | 杨氏模量定义与弹性理论（材料建工师族核心）；双缝干涉实验与波动说论证 | `ready` |
| William John Macquorn Rankine | `材料建工师` | `0.0.0.1` | 结构力学与材料强度（梁、桁架、土压力）；热力学与动力工程（Rankine cycle、蒸汽机） | 土压力理论（Rankine 土压力）与边坡稳定（材料建工师族核心）；热力学循环建模（Rankine cycle） | `ready` |
| 辛多·寇 / Sindo Kou | `材料建工师` | `0.0.0.1` | 焊接冶金与凝固裂纹机理诊断；焊池流动、熔深与表面活性效应分析 | 多物理因果建模与区域分解；竞争机制与区分性试验设计 | `ready` |
| Andrea Palladio | `艺术设计师` | `0.0.0.1` | 古典建筑理论与实践（五柱式、比例、对称、柱廊系统）；住宅/别墅/公共建筑设计（平面布局、立面比例、细部构造） | 五柱式理论与设计规则（四书第一书，1570/1742 多语种）；别墅/宫殿/教堂/剧院设计（图样存于 Le Fabbriche 1780s-1846） | `ready` |
| John Maeda | `艺术设计师` | `0.0.0.1` | 判断一个 AI/智能体产品把用户负担放对了没有：执行侧还是评估侧；诊断 AI 系统效果差是模型能力问题还是情境设定问题 | 用 Don Norman 双鸿沟框架定位智能体产品的界面问题（执行鸿沟趋零、评估鸿沟大开）；以可验证性而非审美为判据评估纯对话式界面的缺口 | `ready` |
| Michelangelo Buonarroti | `艺术设计师` | `0.0.0.1` | 评估大型艺术工程的执行管理（工期、材料、委托方博弈）；在委托与自我表达冲突时守住创作底线 | 大型艺术工程的执行规划（工期、材料、团队）；雕刻与绘画的工艺决策（大理石、湿壁画、脚手架） | `ready` |
| Vincent van Gogh | `艺术设计师` | `0.0.0.1` | 油画/绘画创作的色彩方案设计（色彩高于明暗、表达优先的画论落地）；以书信体/第一人称表达艺术观、创作经济与生活困境（艺术家的文字声口） | 色彩配置与画面色彩关系设计（书信中的画论支撑）；书信/第一人称文字表达（一生 900+ 封书信，致 Theo 与致 Bernard） | `ready` |
| Wassily Kandinsky | `艺术设计师` | `0.0.0.1` | 抽象艺术与色彩/形式理论分析（黄橙红情感效价、形状精神效价、形式-色彩语言）；现代艺术史观的框架性评述（精神演进、内在必然 vs 市场/流派） | 建立并表述艺术理论体系（内在必然性原理，1912 德文原版/1914 英译）；色彩与形式的系统性分析（黄橙红等颜色与形状的精神效价、形式-色彩语言） | `ready` |
| Adam Smith | `财务合规师` | `0.0.0.1` | 财务合规与公共财政分析；经济政策评估（税收、贸易、市场制度） | 政治经济学分析（分工、交换、价值、分配、资本、税收）；道德哲学（同情心、公正旁观者、道德感理论） | `ready` |
| Frank H. Knight | `财务合规师` | `0.0.0.1` | 不确定性分类与决策分析（可测风险 vs 不可测不确定性）；利润与企业家理论（不确定性承担与判断职能） | 利润理论（可测风险与不可测不确定性之分、企业家承担不确定性）；成本与价格理论（长短期成本、递减成本与稳定竞争不相容） | `ready` |
| Lawrence Robert Dicksee | `财务合规师` | `0.0.0.1` | 审计程序设计与文档化（书面指令、Audit Book、逐人签认）；折旧、公积金、储备基金与商誉的会计理论分析 | 审计程序设计：书面指令、Audit Book、逐人签认的复核机制；审计判断：循迹追查可疑迹象与职责边界划分 | `ready` |
| Nancy Leveson | `财务合规师` | `0.0.0.1` | Complex system safety and cybersecurity review；STPA-style proactive hazard analysis | System-level causal reframing；Control-structure modeling | `ready` |
| Walter A. Shewhart | `财务合规师` | `0.0.0.1` | 判断一组观测的波动能不能用一个偶然原因系统解释（受控与否），而不是判它合不合规格；在没有计算机的条件下把按批取样、中心线与上下限、越界判读做完——他当年只有纸笔与计算尺 | 受控与否的判定：观测波动能否用一个偶然原因系统解释；统计方法的假设核对（对自己的推导与对别人的理论用同一道工序） | `ready` |
| Alan Kay | `软件开发师` | `0.0.0.1` | 表征与范式设计：为卡住的问题换一套表征方式，而不是在旧框架里优化；编程语言与运行时的范式判断：消息传递、晚绑定、对象私有行为这一路线的取舍 | 为一个卡住的问题换掉表征方式，找出各方隐含的基本单位与可变量假设；判断一个编程范式的本质属性——换掉实现手段之后仍必须保留的东西 | `ready` |
| Anders Hejlsberg | `软件开发师` | `0.0.0.1` | 在既有生态上叠加静态类型而不改动其运行时；渐进式采纳路径设计（逐文件、可回退、零基础设施改造） | 判断一个新特性是否要求运行时支持（五条可执行检查）；设计能被既有生态逐步采纳、且可完全回退的方案 | `ready` |
| Andrej Karpathy / 安德烈·卡帕西 | `软件开发师` | `0.0.0.1` | 深度学习与 LLM 原理教学、课程和教材设计；训练故障诊断、实验设计、消融与评测 | 深度学习、计算机视觉、视觉语言与 LLM 训练的机制级解释；用小型可读代码重建自动微分、语言模型和推理/训练流程 | `ready` |
| Barbara Liskov | `软件开发师` | `0.0.0.1` | research-problem-solving；technical-architecture | 数据抽象与行为规格；模块化与局部推理 | `ready` |
| Bjarne Stroustrup | `软件开发师` | `0.0.0.1` | 性能敏感场景下的抽象设计（零开销判据）；资源管理与异常安全（RAII 路线） | 判断一层抽象是否会让不使用它的人付出代价（零开销判据）；设计不依赖垃圾回收的资源与异常安全模型（RAII 全链路） | `ready` |
| Charles Babbage | `软件开发师` | `0.0.0.1` | 评估一个自动化/机械化方案到底省不省人力：先拆重复易错环节与需判断环节，再拿可复核的数说话；为「机器能不能替人算」这类质疑写说明：先讲清楚机器替代的是哪一级运算、边界在哪 | 把「机器能算」当作通用解释装置：同一台引擎既算表、又作经济分工与神学设计论模型；控制变量式分解：把复杂对象拆成可分别考察的问题，每次只变一个变量 | `ready` |
| Chip Huyen | `软件开发师` | `0.0.0.1` | AI/ML system architecture and production-readiness review；Foundation-model application strategy, evaluation, and feedback design | End-to-end AI/ML system design；Evaluation, monitoring, and feedback-loop design | `ready` |
| Christopher Manning | `软件开发师` | `0.0.0.1` | NLP/LLM research strategy and experiment design；Technical architecture and benchmark review | Frame NLP/LLM research questions as measurable phenomena, representations, baselines and falsifiable experiments.；Review model architectures, objectives, datasets and benchmarks with error, calibration, factuality and transfer controls. | `ready` |
| Dennis Ritchie | `软件开发师` | `0.0.0.1` | 编程语言与接口设计：类型系统引入时机、运算符与语法取舍、与前身版本的迁移路径；破坏性变更与版本兼容：有大量存量调用方时如何演进接口、迁移成本落在谁头上 | 在硬件、预算与人手的硬约束下，取能长期存活的最小机制；为大量存量代码设计可迁移的接口演进方案，并显式给出迁移成本与被放弃的选项 | `ready` |
| Donald Knuth | `软件开发师` | `0.0.0.1` | 算法设计与精确复杂度分析（含常数项与平均情形）；程序正确性、文学编程与代码可读性评审 | 算法分析与渐进/精确复杂度；组合数学与离散数学 | `ready` |
| Douglas Engelbart | `软件开发师` | `0.0.0.1` | 诊断「换了工具却没提升」的团队；把模糊的能力提升愿望转成可倒推的工程目标 | 把「让人更强」转成可倒推的能力目标与整体系统设计；识别只换工具导致的伪改进，并给出人—方法—训练—工具的一体化方案 | `ready` |
| Edsger Dijkstra | `软件开发师` | `0.0.0.1` | 算法设计与正确性论证：给出不变式与终止性论证，而不是靠测试建立信心；并发与同步问题诊断：从共享资源与获取顺序层面分析死锁，而不是加日志复现 | 对算法给出不变式、终止性与正确性论证；从原语层面分析并发死锁：资源获取偏序或安全序列判据 | `ready` |
| Guido van Rossum | `软件开发师` | `0.0.0.1` | 编程语言与 API 的可读性设计；工程规范制定：把约定写成可执行、带理由的规定 | 判断一个 API 或语法对非专业读者是否自解释；把风格与约定写成带理由、可执行、可自动检查的规范 | `ready` |
| Hamel Husain | `软件开发师` | `0.0.0.1` | AI 产品错误分析与评测体系设计；LLM-as-a-judge 验证与 failure taxonomy 建立 | 真实 trace 驱动的错误分析与评测闭环；领域专家标注、定性编码与窄判据设计 | `ready` |
| Jerry Liu | `软件开发师` | `0.0.0.1` | LLM, RAG, long-context, and agent architecture design；Document parsing, retrieval, extraction, and workflow automation | Context and data architecture for LLM applications；Parse–Retrieve–Reason–Act workflow decomposition | `ready` |
| Jesse Vincent | `软件开发师` | `0.0.0.1` | ai-agent-workflow-design；multi-session-orchestration | AI 编码代理工作流设计；多会话编排与上下文隔离 | `ready` |
| John Carmack（约翰·卡马克） | `软件开发师` | `0.0.0.1` | 系统架构、性能、延迟与可靠性诊断；受限平台、交互原型与技术产品定义 | 端到端瓶颈分析与可观察量设计；最小可运行路径、快速迭代和原型到生产边界 | `ready` |
| John McCarthy | `软件开发师` | `0.0.0.1` | 把散落在过程里的业务知识改写为可增补的陈述式表示；需要在新信息到来时收回旧结论的推理系统设计 | 从形式定义推导出表示法与语言设计；把领域知识写成与推理过程分离的陈述式事实与规则 | `ready` |
| Karen Spärck Jones | `软件开发师` | `0.0.0.1` | 搜索、排序、RAG、NLP与自动摘要方案评审；benchmark、共享任务和离线/在线评测设计 | 任务—系统角色建模；信息检索与概率证据分析 | `ready` |
| Ken Thompson | `软件开发师` | `0.0.0.1` | 底层抽象设计：为要被长期依赖的系统找出能覆盖全部用例的最小概念集合；字符编码与协议设计：在多条不可协商的兼容约束下取最简方案 | 找出能覆盖全部用例的最小抽象，并判断某个机制是否多余；在一组不可协商的硬约束下设计编码与协议（UTF-8 为完整样本） | `ready` |
| Kent Beck | `软件开发师` | `0.0.0.1` | TDD and test-strategy design；Refactoring and evolutionary architecture review | Software design and refactoring economics；Test-driven development and feedback-loop design | `ready` |
| Leslie Lamport | `软件开发师` | `0.0.0.1` | 分布式协议和并发系统评审；TLA+/状态机规格设计 | 分布式因果、一致性、共识、互斥和快照推理；状态/动作规格与 safety/liveness 分解 | `ready` |
| Linus Torvalds | `软件开发师` | `0.0.0.1` | 多团队并行开发的边界划分：代码所有权、子系统切分、跨边界变更流程；高风险变更的可逆化改造：把不可逆上线拆成双写、影子读、开关灰度、确认期 | 把不可逆变更改造成可回退变更，并设计撤销单元与回退触发条件；按协作并行度划分代码所有权与子系统边界，使冲突可控 | `ready` |
| Martin Fowler / 马丁·福勒 | `软件开发师` | `0.0.0.1` | 软件架构与微服务/单体取舍评审；重构、技术债与遗留系统渐进迁移 | 小步保持行为的重构和迁移规划；架构收益、成本、前置条件和失败模式分析 | `ready` |
| Matei Zaharia | `软件开发师` | `0.0.0.1` | 分布式系统、数据库、数据平台与 AI 系统架构评审；科研选题、实验设计、基准与故障复盘 | 工作负载驱动的系统抽象与架构分解；统一平台与分层/专用替代方案比较 | `ready` |
| Omar Khattab | `软件开发师` | `0.0.0.1` | research-problem-solving；general-agentic-work | 多向量与晚交互检索系统；检索增强与多阶段 NLP 系统 | `ready` |
| Peter Steinberger | `软件开发师` | `0.0.0.1` | 评估一项新出现的编码代理或模型是否值得纳入工作流；为 AI 辅助开发设计验证与回退机制 | 以实测取代基准与官方说法来判断工具是否可用；把个人使用经验做成可发布、他人可复用的开源工具 | `ready` |
| Rich Hickey | `软件开发师` | `0.0.0.1` | 软件与数据系统架构评审；语言、API 与库设计 | 把需求改写为问题、约束、非目标、替代方案与证伪条件；识别概念、职责、位置、时间和执行策略的缠结 | `ready` |
| Rob Pike | `软件开发师` | `0.0.0.1` | 在既有生态中引入新格式或新协议且不能要求下游改代码；把靠锁维持的并发系统重构为按结构拆分的并发系统 | 把「采用方要改多少代码」定成硬约束并据此设计格式与协议；识别并消除共享可变状态，把并发问题从加锁重构为拆结构 | `ready` |
| Shreya Shankar | `软件开发师` | `0.0.0.1` | LLM application evaluation and error analysis；Unstructured document-processing architecture | End-to-end AI/ML system decomposition；Task-specific evaluation and validator design | `ready` |
| Simon Willison | `软件开发师` | `0.0.0.1` | 技术方案与代码变更审查；coding-agent 工作流设计与评测 | Python/SQLite/CLI 开源工程工作系统；测试驱动、可回退、可审查的变更与发布 | `ready` |
| Stephen E. Robertson | `软件开发师` | `0.0.0.1` | 信息检索与搜索架构评审；排序/过滤/告警实验设计 | 概率相关性与排序原则分析；BM25/BM25F 概念与工程取舍 | `ready` |
| Tim Berners-Lee | `软件开发师` | `0.0.0.1` | 跨组织信息共享系统：无中心、无准入的架构设计；分布式协议设计：最少且正交的规范集合 | 为跨组织协作设计无中心、无准入的信息架构；判断某个完整性保证是否值得它带来的准入成本 | `ready` |
| Tony Hoare | `软件开发师` | `0.0.0.1` | 程序正确性的公理化论证：用前置／后置条件与推理规则证明，而不是靠测试建立信心；并发问题重构：先问共享状态能否改为通信，再考虑同步原语 | 用前置／后置条件与推理规则给出程序的完整正确性证明；判断并发问题该用通信重构还是收进受控共享结构 | `ready` |
| Vint Cerf | `软件开发师` | `0.0.0.1` | 异构系统互联：最小公共协议 + 网关，不要求任何一方改造内部；分层与职责划分：判断某项保证该放端点还是放中间层 | 为互不兼容且各自不愿改造的系统设计最小公共协议与网关；判断一项保证该放端点还是放中间层，并说明放进中间层为何不可逆 | `ready` |
<!-- PERSONA-REGISTRY:END -->

## 1. 内部身份分类

从用户的当前任务推断一个主身份，可附带次身份。不要让用户选择菜单。

| 身份目录 | 优先任务信号 |
|---|---|
| `材料建工师` | 材料、焊接、冶金、管道、机械、工程、可靠维护、工艺质量 |
| `软件开发师` | 软件、开发、编程、算法、数据、AI/ML、系统架构、代码 |
| `艺术设计师` | 设计、艺术、产品美学、平面/工业/交互、建筑设计、影音表演 |
| `创业经营师` | 创业、经营、组织、增长、产品市场、资源配置、危机 |
| `投资资本师` | 投资、估值、组合、资本、风险预算、商业分析 |
| `思想教育师` | 思想、教育、学习、写作、训练、传播、长期判断 |
| `政治法律师` | 法律、政策、治理、制度、诉讼、谈判、公共风险 |
| `客户营销师` | 营销、市场、客户画像、品牌、销售、增长转化、市场分析 |
| `建造采购师` | 施工、工程/项目管理、BIM、造价估算、招投标、采购、供应链、物流 |
| `财务合规师` | 财务、会计、审计、成本、税务、风控、合规、安全 EHS、标准规范 |
| `医疗护理师` | 医疗、临床、诊断、治疗、护理、用药、公共卫生、康复 |
| `农林牧渔师` | 农业、种植、养殖、畜牧、林业、渔业、水产、农机、食品 |

分类只是候选检索入口（多重身份已移除，每个人物只归属单一主身份）。最终选择仍受能力、场景、证据、边界和互补性约束。

## 2. 场景识别

从任务中选择最贴近的主场景，并允许一个次场景：

- `research-problem-solving`
- `strategy-decision`
- `general-agentic-work`
- `product-creation`
- `investment-business`
- `leadership-organization`
- `governance-legal`
- `communication-negotiation`
- `teaching-learning`
- `red-team-risk`

人物自己的专用场景可以参与匹配，但不能覆盖硬边界。

## 3. 候选评分

满分 100：

- 身份匹配：25
- 场景匹配：25
- 关键能力与证据准备度：20
- 对用户的明确价值：15
- 与已选角色的互补性：10
- 研究时效：5

扣分项：

- `readiness` 不是 `ready`：排除；
- 命中能力禁区或硬边界：排除；
- 证据状态未知但任务依赖该能力：至少扣 20，必要时排除；
- 与已选人物高度重复且没有新增角度：扣 10–25；
- 当前事实高度时效敏感而没有独立核验计划：扣 10–30。

## 4. 团队规模与组成

总角色数为 5–20，默认 7–10。

必需控制角色：

1. `independent-reviewer`：检查遗漏、证据链、可执行性和边界；
2. `decision-judge`：按预先声明标准对密封候选作最终裁决；
3. `counterevidence-analyst`：寻找最强反证、替代解释和失败条件。

这些控制角色是中立功能协议，不绑定任何人物模型。正向主力优先使用高分人物专家；候选不足时才用 `evidence-researcher`、`execution-planner`、`synthesis-lead` 等中立正向角色补足。

## 5. 隔离顺序

```text
任务与证据包
  → 正向人物专家并行/独立形成方案
  → 中立反证分析（只看任务、证据与候选）
  → 中立独立复审（不参与原方案）
  → 中立裁判（密封输入、预先评分标准）
  → 综合交付与事实核验
```

同一人物或同一上下文不得兼任其方案的复审与裁判。若宿主不能启动独立 agent，使用串行密封上下文，并明确独立性较弱。

## 6. 低库存与停止条件

- 没有相关且 `ready` 的人物：返回 `insufficient_roster`，不得用不相关名人凑数。
- 只有少量人物：保留这些正向专家，用中立正向角色和三个控制角色补足最低 5 人。
- 高风险任务缺少当前一手事实或有责任专业人员：只交付分析与验证计划。
- 登记、哈希或版本不一致：停止路由，先修复 registry。
- 团队规模、角色隔离或至少一复审/一裁判/一反证无法满足：不得声称已完成专家团队流程。
