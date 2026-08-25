# 可核事实与知识边界

> 只放可直接核验的事实、时期、角色、领域与资料截止日期。每项使用 Claim ID。

## 事实层覆盖说明

- 本文件承载 4 条 fact/lineage 断言（零售三原则、广告观、商店学校机制、语料元断言）＋1 条 lineage 元断言，由 render_claims.py 从 evidence/claims.jsonl 渲染进下方断言区；上方导言为人工维护。
- **事实层覆盖**：零售三原则（货真价实/统一标价/可退换）、广告哲学（告知而非硬塞）、商店学校机制（≈1897 创办、7,500 毕业生、成绩=晋升）、语料元断言（9 份 train、3 道、四声口层）。
- **引文纪律**：所有逐字引文照 OCR 形态（含 `6c`=and、`sometlimg`=something、`ictivity`=activity、`con¬ference` 软连字符等），已逐条对 references/sources 回验；1861/1876 两个"诞生"口径与"第一"清单均标"商店自述/宣传声口"。
- **时间坐标**：语料覆盖 1900（Evolution）—1928（Williamson 传出版）；人物生平（1838 生/1889-1893 邮政部长/1922 卒）均不在 train 内，仅人物背景提供。

## 事实

- **时期与角色**：John Wanamaker（1838-1922，费城），美国百货零售先驱；本库语料覆盖其 1900-1928 的自述文本（演讲/期刊/纪念册/传记），**不含邮政部长任内（1889-1893）内容**。
- **核心时间锚（商店自述）**：1861 生意诞生（[1911 · 《The Abraham Lincoln chair》宣传册] `Fifty years ago Abraham Lincoln became President of these United States. Fifty years ago the John Wanamaker Business was born.`）；1876-03-12 现店开业；1862 率先宣布缩短工时；1878 世界首家电灯照明商店（"第一"为自述）；1880 现金输送管；1886-07-04 周六半休；1899-04-15 进军钢琴业；1904/1909 亲手立新楼钢柱（以上均自 [1910 · 《History of the Founding of Philadelphia》] Chronology）。
- **领域**：百货零售（定价/退换/广告/邮购）、商业教育（商店学校）、公共演讲与政论（反托拉斯/诚实劳动）、人物纪念（林肯/Williamson）。
- **语料覆盖**：train 9 份——writings 4（Williamson 传 1928、Lincoln Primer 1908/1919、费城史 1910）、expression 4（Evolution 1900、Commercial Institute 1909、Aisle Managers 1914、Taft 献词 1912）、timeline 1（Lincoln Chair 1911）。

## 知识边界

- 语料无独立 external/decisions/conversations 源；邮政部长任内、私人财务、家庭细节均无 train 证据。
- "第一/最大/最方便"类事实仅商店自家出版物自述（1910 费城卷、1911 宣传册），未独立印证。
- 四层声口（亲述/被引他人/编者/宣传册）须区分；编者 Foreword（1928）与被引他人语不能当亲笔。

## 断言层（逐条可回语料）


<!-- ↓ 断言渲染区（由 render_claims.py 生成，勿手改） -->

## 断言层（逐条可回语料）

<!-- claim:clm-09a704672da8 -->
**商店学校（John Wanamaker Commercial Institute）的机制与规模：约 1897 年创办、1909 年时约 7,500 名毕业生、"学校成绩=晋升/去留依据"**——1909 年《Commercial Institute》 `To-day about 7,500 graduates of this commercial institute are showing the mercantile world what new kind of business men and women may be produced by this store-school.`（`busi-ness` 折行连字归一）与 `High standing in the school's records means certain promotion in the section of the store work to which a student is assigned; habitual low marks, indicating a lack of interest or a lack of capacity without improvement, result in a change of names on the payroll.`；同卷开头称该制度"已静静运行约十二年"（`an educational system that, for as many as twelve years, has been in active operation in a very quiet way under the title of "The John Wanamaker Commercial Institute"`，改述：1909-12≈1897 创办）。　［出处：《The John Wanamaker Commercial Institute》1909］

> **何时作废**：若档案显示 7,500 这个数字夸大或学校创办年另有他说 ⇒ 本条按档案修正数字/年份，引用标注'其自称'

<!-- claim:clm-44c7e60d754d -->
**语料元断言：本库 Wanamaker train 语料 9 份、覆盖 3 道（writings 4 / expression 4 / timeline 1），conversations/decisions/external 三道无独立 train 源（可由其他道间接提取）；须区分四个声口层**——① Wanamaker 亲述正文（Primer 1908 的 Rule of Four、Evolution、Commercial Institute、两篇讲话）；② 被引用的他人声口（Dennis Hanks 方言、林肯演讲/书信、富兰克林/James Allen 引文）；③ 编者/出版社层（1928 年 Williamson 传的 Lippincott Foreword，`From his earliest days John Wanamaker was a voluminous writer.` 等）；④ 宣传册声口（1911 Lincoln Chair `Fifty years ago Abraham Lincoln became President of these United States. Fifty years ago the John Wanamaker Business was born.`）。引用须知：编者 Foreword、宣传册、被引他人语均须按声口折减，不可当 Wanamaker 亲笔观点。　［出处：source-ledger 各版次；《Life of Isaiah V. Williamson》1928 Foreword；《The Abraham Lincoln chair》1911 宣传册］

> **何时作废**：若后续发现语料含他人伪托篇目或新增独立 external 源 ⇒ 本条须更新

<!-- claim:clm-bc253aa8f498 -->
**零售三原则：货真价实、统一标价、可退换**——1910 年《History of the Founding of Philadelphia》卷首《Store System in Brief》自述 `Trustworthy goods only, at uniformly right prices ; all articles (with few exceptions, mainly for sanitary reasons) returnable within reasonable time for cheerful reimbursement if uninjured.`（货真价实/统一合理标价/合理期限内无损可退并爽快退款——商店政策的官方简纲）；1900 年《Evolution of Mercantile Business》把"退换/保证"说成"合同条件而非恩惠" `refund, not as a favor but as a condition of the contract of sale, is a boon to the ignorant and hasty buyer`（`return of goods for` 与 `refund` 间横页眉，引文自 refund 起）。　［出处：《History of the Founding of Philadelphia》1910；《The Evolution of Mercantile Business》1900］

> **何时作废**：若档案证明这些原则早于他由他人（如 A. T. Stewart）系统实行 ⇒ 本条收窄为'其自称的首创/其政策表述'

<!-- claim:clm-c1f31a8178ce -->
**广告观：不硬塞要卖的，只告知人们想买的——广告是服务公众的信息员，且必须说真话**——1910 年《History of the Founding of Philadelphia》卷首《Daily Wanamaker Announcements》剪报自述 `We do not try to force upon the people what we want to sell, but rather we try to find out & give news to the people about what they want to buy.`（`&`=and 的排印，照录）；1912 年 Taft 献词对广告界呼吁回归"说真话" `I appeal for the recall, for the recall of old-fashioned truth-telling in public print, editorially, locally and advertisingly`——广告以顾客需求为起点、以真话为底线。　［出处：《History of the Founding of Philadelphia》1910；《Address at the Dedication of the Wanamaker Store》1912］

> **何时作废**：若发现他私下教唆夸大/虚假宣传 ⇒ 本条收窄为'其公开的广告观'
