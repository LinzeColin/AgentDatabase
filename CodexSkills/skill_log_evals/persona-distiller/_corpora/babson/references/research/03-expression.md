# Expression DNA and micro-behavior

## Scope and assigned sources

**本道分到 2 份（train split）**：

| source_id | 出版年 | tier | 题名 |
|---|---|---|---|
| `src-55080b01fc0a` | — | P1 | Security Prices and the War |
| `src-8fe78fbcd4b3` | — | P1 | Barometric Indices of the Condition of Trade |

★ 本节由台账机械导出（`emit_lane_scope.py`），**不含任何阅读判断**；只投影 `split == train` 的行。

## Source-linked observations

### ① 《Barometric Indices of the Condition of Trade》（1910，The Annals of the American Academy）——"商业的科学化"表达范本
`src-8fe78fbcd4b3` 是他 barometer 方法最早的期刊完整陈述（发表于 1910，早于 1912 版《Business Barometers》同名章节；meta 记账与 Business Barometers 内容重叠约 34.2%，是同一方法在期刊载体的表述）。**开篇即作两类统计的二分**：

> Statistics are divided into two classes, viz. : Comparative Statistics and Fundamental Statistics
<!-- src-8fe78fbcd4b3 -->

- 他给周期下的"四段"定义（与《Business Barometers》第一章几乎逐字同源）：

> All financial history has consisted of distinct cycles, and, although of different durations, each cycle has consisted of four distinct periods; namely, 1. A Period of Prosperity. 2. A Period of Decline. 3. A Period of Depression. 4. A Period of Improvement.
<!-- src-8fe78fbcd4b3 -->

- 给"作用=反作用"加上"面积"条件（比书上更早写出）：

> action and reaction are always equal where the "area" consumed is considered
<!-- src-8fe78fbcd4b3 -->

- 方法断言——根本统计"消除一切猜测与不确定"：

> The use of fundamental statistics eliminates all guessing and uncertainty concerning mercantile and market movements and gives a barometric index of conditions of trade.
<!-- src-8fe78fbcd4b3 -->

> These twelve main subjects have by custom come to be known among merchants as the twelve barometric indices of the condition of trade
<!-- src-8fe78fbcd4b3 -->

- 对单一指标（金流动等）的否定——**必须复合解读**：

> No one of these subjects, when studied independently, serves to foretell the great changes in conditions which have occurred since i860
<!-- src-8fe78fbcd4b3 -->

（此处 OCR 作 `i860`，应为 1860，照录。）

- 他的几个标志性表达习惯：
  - **医生类比**——把统计师比作诊脉/查体征、翻病历的医师：

> In many ways the work resembles the work of a physician.
<!-- src-8fe78fbcd4b3 -->

  - **铁价当气压表**：

> all merchants watch the price of iron as an index of the amount of steel in demand, and, therefore, as a barometer of actual conditions
<!-- src-8fe78fbcd4b3 -->

  - **"太少破产反而预告灾难"的反直觉句**：

> Contrary to the ordinary impression, too few failures foretell disaster and panic.
<!-- src-8fe78fbcd4b3 -->

  - **"货币是一切贸易的基础、最敏感的气压表"**：

> Money is the basis of all trade, and is, therefore, probably the most sensitive of all barometers.
<!-- src-8fe78fbcd4b3 -->

- 全文收束在他最著名的一句话上——**"美国要的是愿意去研究根本条件的士兵"**（本句带破折号，归一后按 `-` 比对，照录）：

> America wants men who are willing to enlist as soldiers — not to kill and destroy — but to study fundamental conditions
<!-- src-8fe78fbcd4b3 -->

⇒ 声口/论点：期刊文章的声口比教科书更"布道"——通篇用医生、船长、士兵、银行家的类比，把统计方法讲成"国家需要的公民职责"；结尾直接向读者喊话（"whether our nation is truly better or worse by having us as citizens"，改述）。

### ② 《Security Prices and the War》（1917，American Economic Association）——战争时局下的逐项判断
`src-55080b01fc0a` 是他 1917 年在美国经济学会的发言，讨论欧战结束后美国证券价格的走向。**他先给"决定证券价格的四个力"**（需求、供给、投资吸引力、货币尺度），然后把证券分股票/债券/商业票据三组逐一判断。这是语料里最典型的"**用供需框架对具体时局下判断**"的样本：

> The demand for securities, which exists during periods of prosperity and which is especially potent in the early part of a period of prosperity
<!-- src-55080b01fc0a -->

（"需求在繁荣期存在、在繁荣前期尤强；随繁荣发展而消退"——改述衔接。）

- 他的战后市况预测（这句跨页，用 [版口] 标出断处）：

> Personally, I believe that within twelve months [版口：230 American Economic Association] after the war there will be a decline of from 25 per cent to 50 per cent in the price of many commodities.
<!-- src-55080b01fc0a -->

> People will not buy on declining markets, either commodities or stocks.
<!-- src-55080b01fc0a -->

- 对黄金流动的态度很"去魅"——金流入不直接影响股价（"If the bringing of gold into the country inflates dividends, it likewise deflates the purchasing power of dividends"，改述）；通胀只借"投机者更容易借钱"间接托市（改述）。他对债券的判断取决于"欧洲是否赖账/是否转银本位"（改述），并强调**免税证券（farm-loan bonds 等）战后世会持续吃香**（改述）。

⇒ 声口/论点：**把预测写成"决定性力量的清单＋逐项概率判断"**；措辞谨慎（"Concerning this, nobody knows"——指欧洲债务去向无人能知，改述）、但结论明确（25-50% 商品价跌幅）。与《Barometric Indices》的布道式不同，这篇是面向同行的专业研判，直陈"Statistics seem to indicate..."。

## Candidate Claims

- C-E1（fact）：比较统计 vs 根本统计二分的最早期刊表述——前者只看表面/过去，后者看底层条件、是贸易的"气压表"（src-8fe78fbcd4b3，与 writings C-W1 同簇）。
- C-E2（mental-model）：四段周期（繁荣/衰退/萧条/复苏）＋"作用=反作用、面积相等"是预测基础（src-8fe78fbcd4b3）。
- C-E3（mental-model）：单一指标不可靠、必须"十二项复合"解读；"太少破产反而预告灾难"（src-8fe78fbcd4b3）。
- C-E4（heuristic）：用医生/船长/士兵类比讲统计——把统计师定位成"国家的公民职责"（src-8fe78fbcd4b3）。
- C-E5（fact）：1917 战后市况判断——商品价 12 个月内跌 25-50%、"人们不在下跌市场买入"；金流动对股价无直接效果（src-55080b01fc0a）。
- C-E6（mental-model）：供需框架直接用于证券三级分类（股票/债券/商业票据）与具体时局（战争/通胀/免税）（src-55080b01fc0a）。

## Contradictions and alternative explanations

- **同一方法两种声口**：1910《Barometric Indices》是"布道式普及"（统计=公民职责），1917《Security Prices and the War》是"同行研判"（直陈概率判断、承认不确定性）。二者方法同源、语气迥异——下游引用须按语境取用。
- **"统计消除一切猜测" vs "Concerning this, nobody knows"**：1910 断言根本统计"eliminates all guessing"，1917 却承认欧洲债务去向无人能知。他的"确定性"承诺限定了适用范围（可测的周期/供需），对不可测的政治变量保持沉默——这不是自相矛盾，而是**他划定了"可测/不可测"边界**。
- 1910 文与《Business Barometers》重叠约 34%（meta 记账口径）——两处引文可能同源复现，合并引用时注意不是两处独立证据。

## Unknowns and source gaps

- `src-8fe78fbcd4b3`（57KB）只精读了正文论旨、十二项清单、理论与机械工作段落；中间的 **composite plot 原图区域是扫描图噪声**（OCR 打出的全是符号行），图表本身不可读、无法引用。
- 1917 文的"25-50%"预测是战时判断，语料没有后续校验（他之后是否改口不可考）；"免税证券将持续吃香"与具体 bond 判断未展开。
- 两篇都没给 Babson 的个人生平细节；expression 道只有这两篇期刊文章，没有他的散文/诗/演讲辞等其他表达形态样本。

## Proposed Holdout cases

IDs only; research Agents must not inspect Holdout bodies.

## Handoff to adjudication

- C-E1/C-E2 与 writings 道 C-W1/C-W2 跨道同源（同一方法、教科书 vs 期刊），建议合并为"根本统计/四段周期/等量反应"一条主链。
- C-E5/C-E6 的"供需框架用于时局研判"与 decisions 道（Peace 的经济因果、Mexico 的时局判断）互证——他的时局观是"把当前事件放进供需/周期框架里定位"。
- C-E4 的类比手法（医生/船长/士兵）可作表达 DNA 的独立证据，供 voice/expression 类评测用例取材。
- 引用须知：两篇均为 Babson 本名署名的一手期刊文章；1910 文与书重叠处标注；OCR `i860`/破折号按原样。

## 未做完 / 未核

- 1910 文未整篇通读：只读了正文论旨与"理论/机械工作"两大部分，中间的图表区域（扫描噪声）与个别附表（Exhibit A/B/C 描述）未核。
- 1917 文未核他后续的利率/金流动预测是否在别处被修正；两篇文的发表日期（1910/1917）按刊号与卷页推断，未逐一与刊期对照。
- 未把 expression 道与《Business Barometers》同名章节做逐段 diff（仅按 meta 的 34.2% 重叠口径，未逐段核重）。
