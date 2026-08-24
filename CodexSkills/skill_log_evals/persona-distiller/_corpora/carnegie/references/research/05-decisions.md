# Decisions and actions

## Scope and assigned sources

**本道无独立 train 源**：台账里没有任何 `split == train` 的"决策/行动记录"文献（`dimensions` 无 decisions 项）。

★ 本节由台账机械导出（`emit_lane_scope.py`），**不含任何阅读判断**；只投影 `split == train` 的行。
★ 本道虽无独立源，但下列观察**全部间接取自其他道的 train 源**，逐条标出：`src-f942339e1cea`（Autobiography）、`src-b465964357a3`（The Empire of Business）、`src-5512c8642a23`（Problems of To-day）。

## Source-linked observations

### ① 道内无独立观察——如实说明

- 本道**没有专门的决策/行动文献**，但决策与行动**可从自传（06 道）与其他道的自述中大量间接重建**。按主题列出可直接引用的一手段落（声口均为"他事后自述"）：

1. **移民决策（06 道）**：1848 年全家卖织机赴美——`The decision was taken to sell the looms and furniture by auction`（改述，引文见 06 道）；父亲唱 "To the West, to the West, to the land of the free"（06 道）。
2. **职业转折（06 道）**：电报童工→宾州铁路司科特麾下→南北战争期间主管华盛顿运输——他在自传里称"电报信差生活各方面都很快乐"（改述，见 06 道）。
3. **"集中经营"的转向（01 道《Empire of Business》）**：`concentrate your energy, thought, and capital exclusively upon the business in which you are engaged`——他从多元化（铁路/石油/桥梁/钢铁）转向集中钢铁，是经营决策的自述准则。
4. **"不投机"的戒律（01 道）**：`The speculator and the business man tread diverging lines`——对应自传里他自称反对投机（改述）。
5. **Homestead 罢工（06 道）**：1892 年他身在苏格兰、合伙人以武力对付工会——`on July 1, 1892, during my absence in the Highlands of Scotland, there occurred the one really serious quarrel with our workmen in our whole history`（引文见 06 道）；他事后以"我素来倾向让步、合伙人拦我回国"自辩（Phipps 信，改述）。
6. **退休/散财（01+06 道）**：1901 把卡内基钢铁公司卖给美国钢铁公司（自传索引层记为 "Carnegie Steel Company sells out to United States Steel Corporation"，索引非正文，改述引用）；随后建立各类基金（自传索引层，改述）——"生前散财"由行动落实。
7. **和平运动（06 道）**：资助海牙"和平宫"——`the draft for a million and a half is kept`（改述，引文见 06 道）；当"和平协会主席"（自传索引层，改述）。

⇒ 结论：本道无独立源，但**决策链（移民→学徒→经营集中→退休散财→和平）可借 01/06 道完整重建**；只是每一条都要标"事后自述/自传回顾"，不是当时记录。

## Candidate Claims

- 本道**无独立候选断言**（无独立 train 源）。
- 可移交跨道的决策性断言：移民与职业转折（06 道）、集中经营与不投机（01 道）、Homestead 与退休散财（06 道）——均已在对应道承接，本道不重复计。

## Contradictions and alternative explanations

- **"经营自述"与"实际处境"的落差**：他自述"素来倾向向工人让步"（Phipps 信），但 Homestead 事实是动用武力镇压、多人死亡——**自述的"让步者"形象与"武力解决"的事实并置**是本库最尖锐的决策层张力（详见 06 道与 divergence-map）。
- **"反投机"与"早期投机"**：自传索引层记他早年投过石油、买过铁路股权（改述，见 06 道）——他"反对投机"的戒律更像**晚年对年轻人的劝诫**，而非他本人从未投机；引用时须区分。
- **"退休散财"与"继续经营"**：自传 Preface（妻 Louise 写）说他 1901 退休后"比以往更忙"（改述）——"退休"是名义上的，决策重心从钢铁转到公共事务。

## Unknowns and source gaps

- 语料无**当时记录**：所有决策都是事后回顾（自传 1914 前后撰写、1920 刊行），时间与动机细节未经当时文件核对。
- 自传只选编了少量书信；**大批经营决策文件（董事会记录、合同）不在语料**。
- Homestead 一事的**工会一方叙述完全缺失**（语料只有他/合伙人的辩护视角）。

## Proposed Holdout cases

IDs only; research Agents must not inspect Holdout bodies.

## Handoff to adjudication

- 本道**不产 claims**，但向 06 道提供"决策事件"清单，向 divergence-map 提供"让步者自述 vs 武力事实"的冲突素材。
- 决策类用例（如"遇到劳资冲突他会怎么决定"）应以 01/06 道的自述准则（合伙/滑动工资/集中）+ Homestead 反例的张力来建模，**不能只取"让步者"一面**。

## 这一道给下游的东西

- **决策链清单**：移民→学徒→集中经营→退休散财→和平，每条标注一手出处（01/06 道）。
- **"自述 vs 事实"的张力**：Homestead 是建模时必须处理的决策层反例。

## 未做完 / 未核

- 本道**全部未做**（无源可做），非"未完成"而是"不适用"。
- 未核：自传索引层的决策条目（卖给美国钢铁、和平宫、各类基金）未逐条回溯到正文段落核对细节；各决策年份未与档案核对。
