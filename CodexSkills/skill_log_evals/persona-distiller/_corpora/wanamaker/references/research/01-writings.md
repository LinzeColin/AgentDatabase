# Writings and systematic works

## Scope and assigned sources

**本道分到 4 份（train split）**：

| source_id | 出版年 | tier | 题名 |
|---|---|---|---|
| `src-c16093a0b977` | 1928 | P1 | Life of Isaiah V. Williamson（1928，Lippincott 出版；稿约 1907 年写成） |
| `src-fc86c5c756e1` | 1908 | P1 | The Wanamaker primer on Abraham Lincoln : strength, mind, heart, will…（版权页 OCR 作 COPYRIGHT 1909） |
| `src-d78114dc24d9` | 1919 | P1 | The Wanamaker primer on Abraham Lincoln（Lincoln Centenary 纪念重印本；版权页 OCR 作 `19tt`） |
| `src-eabfd2f57aac` | 1910 | P1 | History of the founding of Philadelphia … including the Wanamaker store |

★ 本节由台账机械导出（`emit_lane_scope.py`），**不含任何阅读判断**；只投影 `split == train` 的行。出版年按台账/题名页标注，未逐一核对版次。

## 五条实测发现（逐份）

### ① 《Isaiah V. Williamson 传》（1928）——借他人传记立"商人典范"，两层声口必须分清

`src-c16093a0b977` 卷首 8 页是 **Lippincott 编者的 Foreword（1928，二手）**，不是 Wanamaker 的话；它把 Wanamaker 本人的写作习惯交代得很具体：

> From his earliest days John Wanamaker was a voluminous writer.
<!-- src-c16093a0b977 -->

> His pioneer work transformed the writing of advertisements. When he reached middle life he began to write on municipal, state, and national political issues.
<!-- src-c16093a0b977 -->

> In his later years he wrote several thousand daily Store editorials.
<!-- src-c16093a0b977 -->

> Throughout his long career he carefully prepared, and generally wrote in long-hand, his speeches before they were delivered.
<!-- src-c16093a0b977 -->

（Foreword 还说明：此书是 Wanamaker 一生唯一的书稿长篇、是"成功者写给成功者"的励志书；并概括传主品格 `Honest living, honest thinking, and a passion for service`——此句同样是编者的话，**不是 Wanamaker 的自我表达**，引用须归声口。OCR 中 Foreword 有 `dailtf`=daily 讹形，未引。）

- **传主=Wanamaker 的价值镜像**：正文（Wanamaker 亲笔）反复表彰 Williamson"不被钱改变"——本段跨页折行，中部横一道页眉 `THE BACKGROUND / 7`，用 [版口] 标注、分段各自命中：

> He never cornered the stock market; he never helped to lock up money, as his vast wealth would have enabled him to do; he never [版口：THE BACKGROUND 7] profited by questionable transactions within the companies of which he was a director, by absorption of other companies, freezing out the unasserting and helpless minorities.
<!-- src-c16093a0b977 -->

- **品格清单——"资产"七项**（好出身、好名声、教育、学徒名声、诚实勤勉好习惯、店务训练、能挣钱能储蓄）：

> Honesty, truthfulness, industry, energy, and good habits, of which the people of Fallsington approved and to which they could bear witness.
<!-- src-c16093a0b977 -->

- **财富="托付"而非"所有"**（Wanamaker 盖章的退休观）：

> he regarded his life and its powers as a trust to be enlarged, controlled and administered diligently, savingly, and solely for others.
<!-- src-c16093a0b977 -->

- **慈善也要用生意人的方法核验**（查慈善机构如查赊贷客户——账目/管理/报告逐项核）：

> Just as he had done on Market Street, when in business, in examining into the character, capacity and actualities of business firms that sought to buy goods of his firm on credit, so did he go into the objects of charitable and other institutions, the quality of work, their methods of management, and the accuracy of their reports and financial statements.
<!-- src-c16093a0b977 -->

- **"废除学徒制是当代社会最大的错误之一"**——此句是 Wanamaker 转述 Williamson 的常谈（原文大意"他一再强调，废除学徒制是当代社会最大的错误之一"，跨行断词 `oft-`/`expressed` 无法逐字成句，改述并注明说话人是 Williamson），Wanamaker 在传记里以同情的笔墨记它，与 expression 道"商店学校"观同构；同章还引 Williamson 对《费城时报》记者的话（大意"正是看到街上赤脚褴褛、无人教育、无一技之长的男孩们，让我想到创办一所让每个男孩免费学会一门手艺的学校"，语料该句跨页、`use-`/`fulness` 断词，改述衔接，见 :3339-3350 段）。

⇒ 声口/论点：**借赞人来自况**——不投机、不锁死资金、好名声是最大的资本、财富是托付、慈善要像做生意一样核账。传主就是 Wanamaker 认同的"商人圣人"模型。

### ② 《Lincoln Primer》1908 版——"Rule of Four"店内道德教本，"商业即服务"的宣言书

`src-fc86c5c756e1`（版权页 1909）开卷是林肯传记（四章：STRENGTH/MIND/HEART/WILL），后半部（`THE RULE OF FOUR` 起）是面向 Wanamaker 店员的道德训教。**全书高潮是把四要素焊在商店使命上**：

> With all my STRENGTH
> With all my MIND
> With all my HEART
> With all my WILL
>
> I SERVE THE PUBLIC
>
> at
> THE WANAMAKER STORES
<!-- src-fc86c5c756e1 -->

- **"全力"的解析**（把口号拆成可执行定义；语料 `lias`=has、`t/iat`=that 讹形，引文自 `great latent power` 起、句首"A."为跨行 OCR 伪影舍弃）：

> great latent power even when at rest, but until the engineer opens the throttle and makes that power active, the locomotive accomplishes nothing.
<!-- src-fc86c5c756e1 -->

- **收束章（Conclusion）——商店存在的唯一理由**：

> And that is all we are in business for — to serve the public.
<!-- src-fc86c5c756e1 -->

> This large granite building — the new home of the Wanamaker Store — was built for SERVICE alone. The founder of the business has given his whole life to service.
<!-- src-fc86c5c756e1 -->

> "I serve" is the grandest motto any one can have.
<!-- src-fc86c5c756e1 -->

> For selfishness is the one great sin. The happiest people are those who live for each other. The successful men and women are those who co-operate with one another.
<!-- src-fc86c5c756e1 -->

- **知识观**（OCR `otir`=our、`sahtrate`=saturate 讹形照录）：

> more important to fill otir minds with a few essential truths than it is to sahtrate our brains with a smattering of everything
<!-- src-fc86c5c756e1 -->

- **行动观**：

> The way to get into action is to get into action — go and do the thing.
<!-- src-fc86c5c756e1 -->

- 立志页：`I will do my full DUTY every day!`（见 :4894-4898 段）。卷首献词引**富兰克林**"To Temperance I ascribe my long-continued health…to Industry and Frugality the early easiness of my circumstances and acquisition of my fortune"（:30-43 段，富兰克林的话，非 Wanamaker 语）；卷末引 **James Allen**"A man is literally what he thinks…"（:4913-4930 段，同属外部声口）。

⇒ 声口/论点：**布道式商业伦理**——把林肯人格拆成四要素当"人生操作手册"，收在"I SERVE THE PUBLIC"上；语气是给店员（尤其少年店员）的训话体。

### ③ 《Lincoln Primer》1919 版——纪念重印本，删掉了店内教学篇

`src-d78114dc24d9` 是林肯百年（Lincoln Centenary 1909）纪念文本的重印：题名页与 1908 版同构（STRENGTH/MIND/HEART/WILL、Full-Rounded Man、Rule of Four 字样），**但正文止于林肯传记五章+林肯演讲+《SHORT SAYINGS OF ABRAHAM LINCOLN》**，不含 1908 版的"Rule of Four"教学篇与"I serve the public"收束（本道通读比对，1919 版内 grep 无 `serve the public` 字样）。其独有内容是一整页林肯短句选：

> Work, work, work! … Hold on with a bull-dog grip. All in that one word. Thorough!
<!-- src-d78114dc24d9 -->

（该页另有 `I'm nothing, but truth is everything`、`You may fool all of the people some of the time, and some of the people all of the time, but you cannot fool all of the people all of the time.` 等句——均为林肯语，由 Wanamaker 编选引用，不是 Wanamaker 自述。）传记部分与 1908 版仍大面积重叠（Dennis Hanks 方言引文、Bixby 信、`Now he belongs to the ages` 等段落两版几乎逐字一致），仅个别拼写变体（如 1908 作 `The Pilgrims Progress`、1919 作 `The  Pilgrhns  Progress`）。

⇒ 声口/论点：**两版同书不同功能**——1908/1909 版是店内道德教材（Rule of Four 教学篇收束于"服务公众"）；1919 纪念版是林肯颂扬读物（收于林肯本人言论）。下游引用须注明版本，勿把 1919 版的"无教学篇"当作 1908 版没有。

### ④ 《费城建城史》（1910）——城市史与商店宣传的双重文本

`src-eabfd2f57aac` 题名页副题即点破其双重身份（书题末段含 "including the Wanamaker store / City hall square" 字样，跨行分排、大小写不一，改述）。卷首"Primer"页三则"简纲"是**零售政策的最浓缩自述**：

> The Store System in Brief. Trustworthy goods only, at uniformly right prices ; all articles (with few exceptions, mainly for sanitary reasons) returnable within reasonable time for cheerful reimbursement if uninjured.
<!-- src-eabfd2f57aac -->

> The Mail Order System in Brief. Individual service by experienced shoppers, who watch out for your wishes 6c your interests ; prompt attention to every message ; a telephone service that never sleeps.
<!-- src-eabfd2f57aac -->

- **广告哲学**（卷首剪报《The Daily Wanamaker Announcements》，宣传声口）：

> We do not try to force upon the people what we want to sell, but rather we try to find out & give news to the people about what they want to buy.
<!-- src-eabfd2f57aac -->

- **商店年表（Chronology 段，:918-1258）**给出"第一/首创"清单：`1862 — The Wanamaker Store declared for shorter hours.`、`1876, March 12 — The present Wanamaker Store opened.`、`December 26 — The Wanamaker Store the first in the world to be lit by electricity.`（条目年份 1878 在上一行，引文去年份照录）、`1880 — Cash carriers introduced in the Wanamaker Store — in this a pioneer.`、`1886, July 4 — The Store starts the Saturday half-holiday.`、`April 15 — The Wanamaker Store enters the piano trade, and revolutionizes it.`（条目年份 1899 在上一行，引文去年份照录）、`1904, July 11 — First steel pillar of the new Store planted by Mr. John Wanamaker.`、`1909, February 8 — First pillar of the south wing of the new store planted by John Wanamaker.`（逐条照录，改述拼合）。

- 正文另有对"新建筑"的自豪描述 `THE PHILADELPHIA WANAMAKER BUILDING IS THE LARGEST RETAIL STORE IN THE WORLD & contains nearly 45 acres of floor space`（:2910-2914 段，改述）。

⇒ 声口/论点：**把商店写成城市的地标与心脏**——城史写到哪儿，商店就出现在哪儿；"第一"密集排比属宣传声口，数字须折减。此卷是"明码标价/退换货/广告观"的最直接一手出处，也是 1876-1910 商店年表的唯一文档内清单。

## Candidate Claims

- C-W1（fact）：零售原则三件套——"货真价实/统一合理标价/可退换"的完整表述（`Trustworthy goods only, at uniformly right prices ; all articles … returnable within reasonable time for cheerful reimbursement if uninjured`，src-eabfd2f57aac；`refund, not as a favor but as a condition of the contract of sale, is a boon to the ignorant and hasty buyer`，src-342fd9325225——`return of goods for` 与 `refund` 间横一道页眉 `The Evolution of Mercantile Business. 135`，引文自 `refund` 起）。
- C-W2（fact）：广告哲学——"不硬塞要卖的，只告知人们想买的"（src-eabfd2f57aac `We do not try to force upon the people…`；src-2f57e8856a02 "truth-telling in public print…advertisingly"）。
- C-W3（mental-model）：商业=服务公众（src-fc86c5c756e1 "all we are in business for — to serve the public"；src-342fd9325225 "Public service is the sole basic condition of retail business growth"）。
- C-W4（mental-model）：竞争 vs 垄断的零售模型（src-342fd9325225 "so long as competition is not suppressed by law, monopolies cannot exist in storekeeping"；src-2f57e8856a02 "A competitive and co-operative business is the antithesis of such trusts…"）。
- C-W5（value）：财富观——不投机、钱是托付、自私是大罪（src-c16093a0b977 "He never cornered the stock market"；src-fc86c5c756e1 "selfishness is the one great sin"）。
- C-W6（lineage）：两版 Primer 一教学篇/一纪念篇的结构差异（src-fc86c5c756e1 含 Rule of Four 全套；src-d78114dc24d9 无）。

## Contradictions and alternative explanations

- **"服务公众"宣言 vs "广告促销"文本共存**：同一座建筑（1910 卷）既写"只为服务而建"（Primer 1908 收束），又写"Silk Sales/Clothing Sales…the saving in price will often more than pay your railroad fare"（1910 卷:2906-2908 段促销段）——两卷同一年代，服务话语与促销话语并行，不是互相否定，但下游引用须按文本功能取用。
- **"第一/首创"清单是宣传声口**：1878 电灯第一、1880 cash carriers 第一、1905 全球第一家电灯商店等"第一"全部出自商店自己的出版物（src-eabfd2f57aac），无独立外部印证；Evolution 篇（src-342fd9325225）的"1876 起百货店运动"叙事同为自述。**只可当"其自称"，不可当"史实定论"。**
- **Williamson 传里的"不投机"是传主的事迹，不是 Wanamaker 的自述**：Wanamaker 写 Williamson 不投机不等于可断言 Wanamaker 自己不投机——只能当"他推崇不投机"的证据（声口须标注）。
- **两版 Primer 的重叠=内容互证 vs 冗余**：1908/1919 大量逐字重叠段（林肯轶事）是同一文本系统，跨版引用时不得把同一句在两个版本里各当一份独立证据。

## Unknowns and source gaps

- **Williamson 传只精读了 Foreword、背景章、品格清单、慈善/学校相关段**：全书 5909 行未整本通读；"Seeing the World"（第四章）、"At the Cross-Roads"（第五章）等章的逐段细节未核。
- **1908 版 Primer 未整本逐页读**：林肯传记章（:355-2510）只精读了 Rule of Four 相关与前段；Dennis Hanks 方言大段（:836-1000 等）只抽查。
- **1919 版只确认"无教学篇"这一结构事实**：其 Chapters I-V 与 1908 版的逐字差异未全量比对（只抽查数处拼写变体）；`19tt` 版权年未核。
- **History of Philadelphia（1910）的 Chronology 只取了商店条目**：城市年表其余条目（铁路/火灾/市政史）未核对；"第一"条目与外部史实的交叉验证不在语料内。
- **出处页 OCR 疑难未逐一解**：Primer 1908 版权页作 1909、Williamson 传出版页 1928 但版权页 OCR 作 `1938`——均照录并标注"未核"。

## Proposed Holdout cases

IDs only; research Agents must not inspect Holdout bodies.

## Handoff to adjudication

- **零售原则主簇（C-W1/C-W2）**：与 expression 道 Evolution 篇（"minimum of profit for the creation of the maximum of business"）合流，构成"明码标价/退换/广告"的一手证据链。
- **服务公众观（C-W3）**：与 expression 道 Commercial Institute（商店学校）互证，是 persona/work 的核心理念。
- **财富观（C-W5）**：价值簇，进 strategy。
- **两版 Primer 结构差异（C-W6）**：lineage 元信息，供 facts 与 downstream 文档引用时标版本。
- **宣传声口纪律向下传**：1910 费城卷与 1911 Lincoln Chair 同属"商店自家出版物"，凡"第一/最多/最方便"一律按宣传声口折减。

## 这一道给下游的东西

- **商店使命的三层表述**（可作 claims 强证据）："I SERVE THE PUBLIC at THE WANAMAKER STORES"（1908 版）、"all we are in business for — to serve the public"（1908 版收束）、"Public service is the sole basic condition of retail business growth"（Evolution 1900）——三句跨三部文献指向同一信条。
- **零售三原则一手出处**：`Trustworthy goods only, at uniformly right prices; …returnable within reasonable time for cheerful reimbursement`（1910）。
- **广告哲学一手出处**："We do not try to force upon the people what we want to sell…"（1910）。
- **"Rule of Four"四段论（Strength/Mind/Heart/Will）**：Wanamaker 的自我修养框架，跨工作/人格/演讲多个下游文档可复用。
- **OCR/排印指纹**：Foreword 与史书排印质量最好；Primer 1908 有 `otir`/`sahtrate`、`lias`、`t/iat` 讹形；Williamson 传跨页页眉（`THE BACKGROUND`）须用 [版口] 标注；History 卷用 `&`、`tji`/`tjj` 装饰符。引文一律照录。

## 未做完 / 未核

- 1908 版 Primer 中段（:1900-2880，林肯"Will"章与大段轶事）未逐页精读，只确认结构并取前后端引文。
- Williamson 传"Seeing the World"/"Cross-Roads"两章未读；传内 Lincoln 轶事与 Primer 的重叠未比对。
- 1919 版与 1908 版的正文字级 diff 未做（只抽查）；`19tt` 版权年、Lincoln National Life Foundation 关系未核。
- 1910 费城卷"Dictionary of Landmarks"等工具性章节未读（不涉 Wanamaker 声口，优先级低）。