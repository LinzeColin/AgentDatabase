# 可核事实与知识边界

> 只放可直接核验的事实、时期、角色、领域与资料截止日期。每项使用 Claim ID。

## 事实层覆盖说明

- 本文件承载 4 条 fact 断言 + 1 条 lineage 元断言，由 render_claims.py 从 evidence/claims.jsonl 渲染进下方断言区；上方导言为人工维护。
- **事实层覆盖**：销售法则核心表述（跨 1841 法文/1821 英文）、生产=创造效用＋三分法、货币=价值运载工具/商品、教育/真利益=道德（value 类入 strategy，此处为 fact 类覆盖）。
- **元断言要点**：语料 12 份 train 源、覆盖 writings/conversations/expression 三道；external/decisions/timeline 无独立源（时间线/决策由 notice 层间接提取）；须区分 Say 亲述／译者注／编者 Notice／后世编者四层声口。
- **引文纪律**：所有逐字引文照 OCR 形态（含 `tems`=temps、`débouché`/`économie` 重音丢混、`voiture` 等），已逐条对 raw 回验；具体生卒年等日期仅经编者 Notice 转述，已在条目内标注"二手"。

## 事实

- **时期与角色**：Jean-Baptiste Say（1767-1832，里昂/巴黎），法国经济学家、实业家与政论家；销售法则（萨伊定律）提出者、政治经济学教学制度化推动者。本库语料覆盖其 1800（《Olbie》）—1848（《Oeuvres diverses》生后编）的主要著作与译本。
- **核心论著时间轴（经编者 Notice/版本页转述）**：1800《Olbie》→1803《Traité》首版（时年 36）→1815 Athénée 开课→1817《Catéchisme》与《Petit volume》首版→1819《Traité》第 4 版→1820 与马尔萨斯论战（1821 英译）→1828-29《Cours complet》成书→1830 后入法兰西公学院→1832-11-15 卒（享年 66）。
- **领域**：生产-分配-消费三分法下的政治经济学（生产/价值/货币/市场）、经济学教学法、政策论辩（自由贸易/反管制）、道德改革随笔（Olbie/Petit volume）。

## 知识边界

- 语料无独立 external/decisions/timeline 源；生平与决策细节均在编者 Notice 层（二手），具体日期以"转述"标注。
- 现代计量/行为经济学、当代金融与产业无证据——事实层止于 19 世纪上半叶的学说与经历。
- 四层声口（Say/译者/编者/后世编者）须区分；译文与 Notice 不能当亲笔。

## 断言层（逐条可回语料）


<!-- ↓ 断言渲染区（由 render_claims.py 生成，勿手改） -->

## 断言层（逐条可回语料）

<!-- claim:clm-ab0149b8075d -->
**销售法则（萨伊定律）核心表述——"产品一旦完成，即从那一刻起为其他产品开出全额市场"，跨法/英两版同源**：1841 年第 6 版法文《Traité》第十五章写 `il est bon de remarquer qu'un produit terminé offre, dès cet instant, un débouché à d'autres produits pour tout le montant de sa valeur`（`débouché`=销路/市场，法文原典名句），同章又以 `le fait seul de la formation d'un produit ouvre, dès l'instant même, un débouché à d'autres produits` 收束；1821 年 Prinsep 英译同章平行表述 `a product is no sooner created, than it, from that instant, affords a market for other products to the full extent of its own value`（`affords a market for`=为…开出市场）。其推论是"局部滞销只因他物生产不足"：`It is because the production of some commodities has declined, that other commodities are superabundant.`（`superabundant`=过剩）。　［出处：《Traité d'économie politique》1841（第 6 版，法文）；《A treatise on political economy》1821（Prinsep 英译）］

> **何时作废**：若档案证明"供给创造自身需求"的完整表述更早见于他人著作（如 James Mill 1819 年之前）⇒ 本条须改为"已知最早最完整表述之一，并标注与 James Mill 的先后来"

<!-- claim:clm-cd9b5486f21d -->
**货币观：金钱只是价值的"运载工具/中转"，不是财富本身——缺钱不是滞销之因**：1841 年法文《Traité》写 `l'argent n'est que la voiture de la valeur des produits`（`voiture`=运载工具，名句），并直斥"销售不畅因缺钱"是 `on prend le moyen pour la cause`（把手段当原因）、`La vente ne va pas, parce que l'argent est rare, mais parce que les autres produits le sont`（不是缺钱而是别的产品缺）；1826 年法语《Catéchisme》货币章给货币下定义 `La monnaie est un produit de l'industrie, une marchandise qui a une valeur échangeable.`（货币是工业的产品、有交换价值的商品）。　［出处：《Traité d'économie politique》1841（第 6 版，法文）；《Catéchisme d'économie politique》1826（第 4 版，法文）］

> **何时作废**：若发现他主张货币本身可独立创造财富（金本位狂热）⇒ 本条收窄为"其反重商口径"；目前语料只见其"货币是商品/手段"说

<!-- claim:clm-d01c69e18563 -->
**生产=创造效用而非创造物质；财富=交换价值；全书按生产-分配-消费三分**：1821 年 Prinsep 英译《概论》第一卷第一章写 `Production is the creation, not of matter, but of utility.`（`utility`=效用）并展开 `to create objects which have any kind of utility, is to create wealth; for the utility of things is the ground-work of their value, and their value constitutes wealth.`（效用是价值的基础、价值构成财富）；1848 年《Oeuvres diverses》编者 Notice 转述他的学科定义 `suivant lui, l'Economie politique était le simple exposé des lois qui régissent la production, la distribution et la consommation des richesses`（按他的说法，政治经济学是支配财富生产、分配、消费之法则的简明陈述——`suivant lui`=按他说，系 notice 转述的三分法定义）。　［出处：《A treatise on political economy》1821（Prinsep 英译）；《Oeuvres diverses》1848（编者 Notice 转述）］

> **何时作废**：若史料证明三分法首见于他人（如 Smith 的局部划分）⇒ 本条收窄为"Say 将三分法作为全书结构系统化"

<!-- claim:clm-e6e7f0321a3d -->
**语料元断言：本库 Say train 语料 12 份、覆盖 3 道（writings 8 / conversations 1 / expression 3），external/decisions/timeline 三道无独立 train 源；须区分四个声口层**——① Say 亲述正文（Traité/Catéchisme/Cours/Letters/Olbie/Petit volume）；② 译者层（Richter 英译《Letters》卷首 Preface 自署 `J. R.`、称 `Mr. Say was the first writer who attempted to raise Political Economy to the rank of the exact sciences`——这是译者评价非 Say 自评；Prinsep 的英译脚注以 `T.` 署名、公开批评 Say 价值论 `It is remarkable, that he should throughout the whole of Book I. treat value as founded wholly upon utility`）；③ 编者层（1848《Oeuvres diverses》Notice 取材 Ch. Comte 1833 / Blanqui 1841 / Reybaud，其生平日期如 `le â janvier 17 07`（=1767-01-05 的 OCR 丢字）与 `Le 15 novembre 1832... expira` 均属二手转述）；④ 后世编者层（1854 意大利合卷 Ferrara 导言，`G. B. Say nulla ha lasciato a fare a' suoi successori`）。引用须知：德/意/英译本与二手 Notice 均须按声口折减，不可当 Say 亲笔观点。　［出处：source-ledger 各版次；《Letters to Mr. Malthus》1821 英译 Preface；《A treatise on political economy》1821 Prinsep 注；《Oeuvres diverses》1848 Notice；《Trattato d'economia politica》1854（Biblioteca dell'Economista）］

> **何时作废**：若后续发现语料含他人伪托篇目或新增独立 external 源 ⇒ 本条须更新
