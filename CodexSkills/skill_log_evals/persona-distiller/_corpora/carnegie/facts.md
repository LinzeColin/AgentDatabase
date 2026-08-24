# 可核事实与知识边界

> 只放可直接核验的事实、时期、角色、领域与资料截止日期。每项使用 Claim ID。

## 事实层覆盖说明

- 本文件承载 1 条 fact 断言 + 1 条 lineage 元断言，由 render_claims.py 从 evidence/claims.jsonl 渲染进下方断言区；上方导言为人工维护。
- **事实层覆盖**：散财哲学核心（跨 1901 Gospel/1908 Problems）；语料元断言（8 份 train、3 道、声口分层、自传 1920 刊行但叙事 1835-1914）。
- **引文纪律**：所有逐字引文照 OCR 形态（含 `tiustee`=trustee、`mil_ lions`=millions、`beneftetal`=beneficial、`civiHzed`=civilized、`aU`=all、`potmds`=pounds、`ean`=can 等），已逐条对 raw 回验；时间坐标按内容（自传叙事 1835-1914），不按刊行年 1920。

## 事实

- **时期与角色**：Andrew Carnegie（1835 生于苏格兰邓弗姆林 —1919），美国钢铁工业奠基人、慈善家与政论家；"创业经营师"身份（meta.json identity=entrepreneur-operator）。本库语料覆盖其 1886（《Triumphant Democracy》）—1920（《Autobiography》刊行）的主要著作、演讲与自传。
- **核心论著时间轴（按题名页/内容）**：1886《Triumphant Democracy》→1889《Gospel of Wealth》（1901 收卷）→1891《The A B C of Money》（North American Review）→1898 Homestead 图书馆演说（1908 收入《Problems of To-day》）→1900《Thrift as a Duty》→1902《The Empire of Business》→1905-10-17 圣安德鲁斯校长演说《A League of Peace》（1906 刊）→1906《Edwin M. Stanton》→1907-10-16 爱丁堡《The Negro in America》→1908《Problems of To-day》→1920《Autobiography》（叙事止于 1914）。
- **领域**：钢铁工业经营（成本/垂直整合/规模）、财富伦理与慈善（散财哲学/图书馆/教育）、政论（共和民主/劳工/社会主义）、和平主义（国际仲裁/和平联盟）。
- **关键生平事实（自述层）**：1848-05-17 全家移民赴美（`The decision was taken to sell the looms and furniture by auction`）；电报童工周薪 2.50 美元、轮流扫办公室（`we all began at the bottom`）；1892-07-01 Homestead 罢工（`there occurred the one really serious quarrel with our workmen in our whole history`）；资助海牙和平宫（`the draft for a million and a half is kept`）。

## 知识边界

- 语料无独立 conversations/decisions/external 源；决策与外部视角只能从自传/演讲/著作间接提取，且均系他事后自述或转述。
- 现代宏观/金融/平台经济、当代战争与国际法、当代劳资关系无证据——事实层止于 20 世纪初的工业与公共议题。
- 多层声口须区分：亲述正文／编者层（Negro 卷首 Committee of Twelve 传记、Autobiography Preface）／他转述的第三方（Greeley/Abbott/林肯/格兰特）／自传索引层；不可当亲述。

## 断言层（逐条可回语料）


<!-- ↓ 断言渲染区（由 render_claims.py 生成，勿手改） -->

## 断言层（逐条可回语料）

<!-- claim:clm-000000000001 -->
**散财哲学核心：富人是社会盈余的"受托人/代理人"，死时仍握巨富即死时蒙羞；散财须在生前亲自做、用在能"刺激上进"的用途上**：1901 卷《The Gospel of Wealth》写 `The man who dies thus rich dies disgraced.`（死时仍富即死时蒙羞），并把富人定位为盈余的受托人——`which proclaims him only a trustee of: the surplus`（`tiustee`=trustee 的 OCR 讹形照录）、`a man of wealth thus becoming the mere—tiustee`（句中 `—` 为排印破折号）；又写死时留下的巨富者 `will pass away unwept, unhonored, and unsung`（`mil_ lions`=millions 的 OCR 讹形照录）；1908《Problems of To-day》转引 1889 原文重申累进遗产税 `By taxing estates heavily at death the State marks its condemnation of the selfish millionaire's unworthy life.`　［出处：《The gospel of wealth》1901；《Problems of to-day》1908］

> **何时作废**：若发现他晚年（1910s）放弃"生前散财"主张、转回留遗产给后代 ⇒ 本条收窄为"其 1889-1908 阶段的公开立场"

<!-- claim:clm-00000000000f -->
**语料元断言：本库 Carnegie train 语料 8 份、覆盖 3 道（writings 4 / expression 3 / timeline 1），conversations 与 decisions 无独立 train 源、external 亦无独立源；须区分多层声口——① Carnegie 亲述正文（Gospel/Empire/Problems/Triumphant/League/Negro 演讲正文/自传正文）；② 编者层（Negro 卷首 Committee of Twelve 传记，其转引 `The man who dies rich, dies in disgrace. That is the gospel I preach, that is the gospel I practice` 与 `What a man owns is already subordinate in America to what he knows...` 属二手转述；Autobiography 妻 Louise 所写 Preface）；③ 他转述的第三方话语（Stanton 演讲里 Greeley 悼文/林肯/格兰特信、League 里卢梭/华盛顿/林肯、Negro 结尾 Lyman Abbott）；④ 自传索引层（目录条目非正文）。引用须知：编者/转述层须标声口，不得当亲述**。　［出处：source-ledger；《The negro in America》1907 卷首传记；《Autobiography》1920 刊 Preface；《Edwin M. Stanton》1906］

> **何时作废**：若后续新增访谈/书信/外部批评独立源 ⇒ 本条须更新（conversations/external 道将有源）
