# 可核事实与知识边界

> 只放可直接核验的事实、时期、角色、领域与资料截止日期。每项使用 Claim ID。

## 事实层覆盖说明

- 本文件承载 2 条 fact 断言 + 1 条 lineage 元断言，由 render_claims.py 从 evidence/claims.jsonl 渲染进下方断言区；上方导言为人工维护。
- **事实层覆盖**：①统计二分法（根本统计 vs 比较统计，1909-1913 教科书/期刊同源）；②四段周期由"自然、商业与工业的法则"注定；③语料元断言（14 份 train 全一手、writings 9/expression 2/decisions 3、另三道无独立源、须区分书内他人声口）。
- **未覆盖/属外部史实**：1929 年看跌警告、1904 创办机构、Babson Institute 创办年、生卒年（1875-1967）均**不在语料**，不进事实层。
- **引文纪律**：所有逐字引文照 OCR 形态（含 `trendof`=trend of、`servino'`=serving、`sutficient`=sufficient、`j^i'ofit`=profit、`certainlj^`=certainly、`enduririg`=enduring、`Nazareih`=Nazareth 等讹形），已逐条对 raw 回验；出版年按题名页/版权页人工读取（台账 published_at 为 null）。

## 事实

- **时期与角色**：Roger W. Babson（题名页署 `Roger W. Babson`，Wellesley Hills, Mass.，Babson's Statistical Organization 创办者/总裁）——美国统计学家、投资顾问与商业教育家；本库语料覆盖其 1909（《Business barometers》首版）—1921（《Enduring investments》）的一手出版物。
- **核心著作时间轴（按题名页/版权页/序言署名）**：1909 起《Business barometers》年刊（第五版 1912，题名页自证 First 1909 / Fifth 1912）→1910《Barometric Indices of the Condition of Trade》（JSTOR）→1912《Ascertaining and Forecasting Business Conditions》（学会宣读，JSTOR）→1913《Bonds and stocks》→1913/1914《The future of the working classes》（伦敦讲座 1913，美国版 1914）→1914《The future of the railroads》→1915《The future of South America》→1916《A Business Man's View on How to Secure Permanent Peace》（JSTOR）→1917《Security Prices and the War》（JSTOR）→1919《W. B. Wilson and the Department of labor》→1920《Cox--the man》《Religion and business》《A Constructive Policy for Mexico》（JSTOR）→1921《Enduring investments》。
- **领域**：商业景气分析（barometer 方法）、投资与债券（保守/永久投资）、商业教育、宗教与商业、时局政策（和平/墨西哥/劳工）。
- **书内自述经历节点**：亲自到访大多数南美国家（1915 序言）；战时劳工部任职"最快乐的两年"（1919 序言）；Federal Central American Commission of 1916 成员（1920 墨西哥文自署）。

## 知识边界

- 语料无独立 external/decisions(指第三方)/conversations/timeline 源之外的批评或传记材料——**无任何第三方外部视角**；书内出版社 Introduction（Cox 书）、Hammond Foreword（W. B. Wilson 书）、Burton 引语（Business Barometers）为他人声口，不得当 Babson 观点。
- 1929 看跌警告与 1930s 主题不在语料；生平年谱（生卒、机构创办年）不在语料。
- 现代计量/行为经济学、当代金融与产业无证据——事实层止于 1921 年的学说与经历。

## 断言层（逐条可回语料）


<!-- ↓ 断言渲染区（由 render_claims.py 生成，勿手改） -->

## 断言层（逐条可回语料）

<!-- claim:clm-787f0f14cf89 -->
**语料元断言：本库 Babson train 语料 14 份、全为本人一手，覆盖 3 道（writings 9 / expression 2 / decisions 3）；conversations/external/timeline 三道无独立 train 源；1929 看跌警告不在语料；须区分'Babson 正文'与'嵌在他书里的他人声口'**——① Babson 亲述（各书正文/序言/期刊文）；② 书内他人文字：Cox 书卷首 Introduction 由'The Publishers'执笔（`src-fce5969229e3`）、W. B. Wilson 书卷首 Foreword 由 John Hays Hammond 执笔（`src-49721f117be5`）、Business Barometers 卷首与正文引 Senator Theodore E. Burton 的 1902 语与财富定义（`src-5d5edcec3c26`）；③ Babson 转述的第三方例证（Cunard 船长、报社编辑、银行家等）。引用须知：出版社/编者/引述的第三方声口一律按声口折减，不得当 Babson 观点；题名页自证出版年（1909-1921）为本道时间线依据。　［出处：source-ledger 各版次；《Cox--the man》1920；《W. B. Wilson and the Department of Labor》1919；《Business barometers》1912］

> **何时作废**：若后续发现独立外部/反方源或 Babson 对话书信 ⇒ 本条须更新；1929 预警如补入语料亦须更新

<!-- claim:clm-8403bdfd842c -->
**统计二分法：'根本统计'（fundamental statistics）看底层条件、能预测供需与货币状况并充当'贸易的气压表'；'比较统计'（comparative statistics）只量表面/过去条件，选安全证券可用、做短波判断则无用**：1912 年《Business barometers》第一章写 `STATISTICS are divided into two classes, viz. : Comparative Statistics and Fundamental Statistics`（统计分两类）并界定 `Fundamental statistics relate to underlying conditions of the country and make it possible to forecast demand, supply, money conditions, etc.`（根本统计涉及全国底层条件、使之能预测需求、供给与货币状况）；1913 年《Bonds and stocks》序言把'照管财产'与'投资科学'当被忽视的学问（`When it comes to the science of investins" money, very few people make it a question for thought and study.`，OCR 讹形 `investins"` 照录）；1910 年期刊《Barometric Indices》给出同一二分（`Statistics are divided into two classes`）并断言比较统计对判断大盘走向 'worthless'（改述）。　［出处：《Business barometers》1912（第 5 版）；《Bonds and stocks》1913；《Barometric Indices of the Condition of Trade》1910（JSTOR）］

> **何时作废**：若发现他后期（1920s）放弃'两类统计'框架或根本统计依赖的数据源被证明不可靠 ⇒ 本条收窄为'其 1909-1913 教科书口径'

<!-- claim:clm-b22f432c502a -->
**周期恒为四段（繁荣/衰退/萧条/复苏），被说成由'自然、商业与工业的法则'注定**：1912 年《Business barometers》写 `the laws of nature, commerce and industry determine that these cycles shall always consist of four distinct periods`（自然、商业与工业的法则决定这些周期恒由四个不同时期组成）；1910 年《Barometric Indices》展开为 `All financial history has consisted of distinct cycles, and, although of different durations, each cycle has consisted of four distinct periods; namely, 1. A Period of Prosperity. 2. A Period of Decline. 3. A Period of Depression. 4. A Period of Improvement.`（一切金融史都由有别的周期组成……繁荣、衰退、萧条、复苏四段）。他又在同一体系里说'作用与反作用在考虑面积时永远相等'（`action and reaction are always equal where the "area" consumed is considered`）。　［出处：《Business barometers》1912（第 5 版）；《Barometric Indices of the Condition of Trade》1910（JSTOR）］

> **何时作废**：若证明他对周期时长（二十年/五年）的特定数值有过不同说法 ⇒ 本条收窄为'四段结构恒定、时长随活动量变化'（其面积理论正是否定固定时长的）
