# Henry Clifton Sorby (1826–1908) —— 同名消歧 + 公有领域可得性探测报告 #133

- 探测日期：**2026-08-05**
- 范围：**只探测取证。未建工作区、未下载任何整本 PDF、未组装语料。**
- 并发：全程串行（curl 单发 + sleep），无并行抓取。
- 花费：零。只用了 archive.org 公开 API（advancedsearch / metadata / fulltext-inside）、Wikidata MediaWiki API、Wikisource、Wikipedia、Grace's Guide 公开条目、University of Sheffield 档案检索页。**没有调用任何付费接口，没有绕过任何访问控制。**
- 落盘的临时文件：只有两份 `_djvu.txt` 落在会话 scratchpad（不在本仓）——`reportofbritisha65brit`（2,569,699 B）与 `journalofroyalmi262roya`（1,794,393 B）。本仓内除本文件与 `namesake-candidates.json` 外未新增任何内容。

**OCR 声明（贯穿全文）**：本报告所有「原样」引文都是 archive.org OCR 的**未改动字符**。凡我判断存在讹字的，**同时给出 OCR 原样与正确读法，并标明哪个是哪个**。改过讹字的字符串不得再当逐字引文使用。

---

## 〇、一句话结论

**一手材料非常充裕（去重后 ≈34 件独立作品，全部可免费全文取得），quick 档的两条线（≥8 份来源、一手 ≥0.40）不构成任何压力。**
真正的风险不在「够不够」，而在三处：
1. **父子同名 `Henry Sorby`**——他父亲的名字与他完全一致，且同城同业；
2. **他最著名的那件事（金相学）的核心印本 JISI 1886/1887 两卷，本次在所有免费通道上都没找到**——他在钢铁上的东西目前只能靠 1864 年 BAAS 摘要 + 1886 年《Nature》会议报道拿到，**而这两件都是第三人称转述，不是他的声口**；
3. **能拿到的绝大多数一手材料，主题是颜色化学与显微分光，不是岩相／金相**。按来源数排期会得到一个「化学家 Sorby」，与建库理由（岩相／金相奠基者）不符。这是 Coffin #130 那类**语料形状风险**，排期前必须先量声口密度。

---

## 一、同名／同姓者：找到 9 个，另有 1 个同名簇

产物见 `namesake-candidates.json`（10 条 = 目标 1 + 排除 9）。
`namesake_gate.py --name "Henry Clifton Sorby" --candidates-file namesake-candidates.json`
实跑结果：**`status=blocked`、`resolution=multiple`、`candidate_count=10`、标签 A–J**（这是这道门在多候选下的正常行为；按 Coffin #130 / Bessemer #132 先例，选定后另存只含目标的一份再跑一次，才会变 `ready`）。

### 1.1 检索面（先说我查了哪些库，再说查到什么）

| 库 | 怎么查的 | 结果 |
|---|---|---|
| Wikidata | `action=query&list=search&srsearch=haswbstatement:P31=Q5 Sorby`（SPARQL 端点 **HTTP 504 超时**，改用 MediaWiki API） | totalhits **42**，取回 42 个 QID，其中英文标签含 "Sorby" 的 **24 人** |
| Wikipedia | <https://en.wikipedia.org/wiki/Sorby>（消歧页） | 7 人 + 3 个非人条目 |
| Grace's Guide | 逐条 URL 探测（`Special:Search` 全文检索端点 **HTTP 401**，见 §四） | `Henry_Clifton_Sorby` / `Henry_Sorby` / `Robert_Sorby` / `Robert_Sorby_and_Sons` / `John_Sorby_and_Sons` / `J._and_H._Sorby` 全 **200**；`Thomas_Charles_Sorby` **404**（Grace's Guide 没收建筑师） |
| archive.org | `creator:("Sorby, Henry Clifton") OR creator:("Sorby, H. C.") OR creator:("Sorby")`，rows=100 | numFound **63**，其中至少 4 个不同的 Sorby 作者混在同一结果页 |
| Biographical Dictionary of Architects in Canada | 直接取 node/1317 | 200 |
| University of Sheffield 档案 | `archives.shef.ac.uk/repositories/3/resources/333` | 200 |

**★ 找过但没找到的**：本次**没有**发现第二个「Henry **Clifton** Sorby」。中名 Clifton 目前是唯一的、可靠的、无冲突的区分符。

### 1.2 ★★★ 最高危：他父亲也叫 Henry Sorby

Grace's Guide 为父亲单开了条目 <https://www.gracesguide.co.uk/Henry_Sorby>（HTTP 200，已打开），原样要点：

> `of Woodbourne, Attercliffe` / `c.1791 Born in Yorkshire, presumably a son of John Sorby` / `1846 Died` / `1841 Henry Sorby 50, land and mineral owner, lived in Sheffield`

同一条 1841 年人口普查记录里还列着 `Amelia Sorby 40`（妻）与一个 **15 岁的 `Henry Sorby`**——1826 年生的人在 1841 年正好 15 岁，即**目标人物本人在官方记录里就是以「Henry Sorby」被登记的，没有 Clifton**。

DNB 1912 supplement 独立佐证父名与母名：

> "His father, Henry Sorby, was a partner in an edge-tool manufacturing firm, and his mother was Amelia Lambert."
> （<https://en.wikisource.org/wiki/Dictionary_of_National_Biography,_1912_supplement/Sorby,_Henry_Clifton>）

商号侧的证据链（三页互相咬合，全部 HTTP 200 已打开）：

| 商号 | 合伙人原样 | 坐标 |
|---|---|---|
| J. & H. Sorby，Spital-Hill, Sheffield | `John Sorby the elder, John Sorby the younger, and Henry Sorby`（1828 年长者退出，`John Sorby the younger and Henry Sorby` 续收债权） | <https://www.gracesguide.co.uk/J._and_H._Sorby> |
| John Sorby and Sons，Spital-Hill（1825–1844） | 1832 年解散：`John Sorby, Henry Sorby, and Alfred Sorby`；1844 年解散：`Alfred Sorby and John Francis Sorby`，转 Lockwood 三兄弟 | <https://www.gracesguide.co.uk/John_Sorby_and_Sons> |
| Robert Sorby and Sons | 1829 年解散：`the Partnership formerly existing between us the undersigned, William Lockwood, Robert Sorby, and John Lockwood, as Manufacturers of Files, in Sheffield` | <https://www.gracesguide.co.uk/Robert_Sorby> |

**→ 1820s–1840s 的 Sheffield 金属业里同时活着至少六个 Sorby**：John the elder、John the younger、Henry（父）、Alfred、John Francis、Robert（1787–1857）＋ Robert 之子 Thomas Austin Sorby（1823 生）。

**★ 而且这条风险一直延伸进档案馆**：University of Sheffield 的 Sorby Collection（ref 51）藏品清单里明写有

> "eleven diaries spanning 1859-1908, **one diary from his father covering 1845-1846**"
> （<https://archives.shef.ac.uk/repositories/3/resources/333>）

即**同一个馆藏里「Sorby 的日记」指两个人**。任何按「Sorby diary」取材的动作都必须先问是哪一本。

**分界线（并且这条线本身有争议，见 §五.1）**：父卒 **1846**（Grace's Guide）vs **1847**（Wikipedia：`In 1847, when he was 21, his father died`）。**本次未能裁定，两个年份都不要写死。**

### 1.3 ★★ 第二危：建筑师 Thomas Charles Sorby（1836–1924）——他在 Sheffield 真有工程

用户在任务里问「Sheffield 同时代有其他 Sorby（例如建筑师一系），核实是否存在」。**存在，且比预想的更贴身**：

- 1836-02-16 生于 Yorkshire（Wikipedia 记 **Chevet**；另一来源记 **Wakefield**——两说并存，本次未裁定），1924-11-15 卒于 British Columbia 的 Victoria。
- 伦敦从 Charles Reeves 学艺；1866 年 12 月 Reeves 死后，1867 年初接任**英格兰与威尔士警署建筑与郡法院测绘官**。
- **1866 年赢得 Sheffield 的 St Michael and All Angels 教堂设计首奖**（Biographical Dictionary of Architects in Canada，<http://dictionaryofarchitectsincanada.org/node/1317>，HTTP 200）。
- 1863 年 Holborn 高架桥竞图 105 人中获次奖。
- 1883 年移居加拿大；为 CPR 设计 Hotel Vancouver、Glacier House、Mount Stephen House。
- **向《Building News》投稿**（Wikipedia）。

**为什么这条对本流水线致命**：署名 `T. C. Sorby` 与 `H. C. Sorby` **只差一个首字母**，而 19 世纪扫描件把这个位置读错是常态——本次实测在同一批 archive.org 扫描里已经见到 `H. G. Sorby`、`U. G. Sorby`、`IT. C. Sorby`、`E. 0. Sorby`（详见 §三.4）。**一个只比姓的护栏，和一个比「Sorby + 单个首字母」的护栏，在这个人物身上都会漏。**

archive.org 上确有他的条目：`cihm_83298`，creator 原样 `Sorby, Thomas C. (Thomas Charles), 1836-1924`，题名 `List of docks, wharves, shipyards, marine railways and other facilities for repairing ships in the port of Victoria, British Columbia`，1919，`Victoria [B.C.] : T.R. Cusack Press`。**它就出现在我第一次跑 `creator:("Sorby")` 的结果页里。**

### 1.4 ★★ 第三危：「Sorby」在 Sheffield 首先是刃具品牌

Robert Sorby（1787–1857）的商号名至今仍是在售木工凿具品牌。这条风险的形状与前两条不同：它不会造成**署名**误判，但会让「Sorby + Sheffield + 钢 / 刃具 / 金属」这一类检索**几乎全部命中工具而不是人**。麻烦之处在于目标人物的家族产业正是刃具、他的成名工作正是钢的显微组织——**关键词空间高度重叠**。

### 1.5 其余同姓者（按危险度降序）

| 人 | 生卒 | 危险方式 | 坐标 |
|---|---|---|---|
| **Sheryl Ann Sorby** | 1959– | **检索噪声量最大**。`creator:("Sorby")` 前 100 条里她的条目数超过目标人物任何单一年份。且是**工程学**作者（3-D 可视化、工程图学），关键词相邻；**在世、作品在版权期内**，混入即同时破两条判据 | <https://www.wikidata.org/wiki/Q124738707>；IA `introductionto3d0000sorb` creator 原样 `Sorby, Sheryl Ann, 1959-` |
| **Harold Sorby** | 不详 | **他是 `creator:("Sorby")` 直接返回的条目之一**，年代（1895）落在目标活跃期内、主题（疫苗／医学显微）与目标的显微生物学相邻。生卒国籍职业**一概查不到，本次不作推断** | IA `animalvaccinatio00sorb`，creator 原样 `[Sorby, Harold] [from old catalog]`，call_number 5872413 |
| **Albert Sorby Buxton** | 1867–1932 | **中名陷阱**：署名 `A. Sorby Buxton`，姓根本不是 Sorby，但子串匹配必命中 | <https://www.wikidata.org/wiki/Q4711243> |
| **Angela Sorby** | 1965– | 当代诗歌学者，但著作题名含 `1865-1917` 这类 19 世纪年份，**按年代过滤会被误留** | <https://www.wikidata.org/wiki/Q4762559>；IA `schoolroompoetsc0000sorb` |
| **Thomas Sorby** | 1856–1930 | 同代英国人、同姓；领域（体育）不交叠。**须与建筑师 Thomas Charles Sorby 分开——两个 Thomas Sorby，差 20 岁** | <https://en.wikipedia.org/wiki/Thomas_Sorby> |
| Sunniva Sorby / Warren Sorby / Karol Sorby / Karol R. Sorby / Hugh Sorby / Kris L Sorby / Nicole Sorby / Lorraine Sorby-Howlett | 当代 | 纯检索噪声，无著作署名冲突。**未逐个核实，只从 Wikidata / IA creator 字段读到名字** | Wikidata Q87416198 / Q18158731 / Q112380601 / Q95179483 / Q98219487 / Q88909961 / Q121337099；IA `weddingdesigns0000sorb` |

### 1.6 非人物的同名噪声

- **Sorby Research Institute**——Sheffield，二战期间的医学研究设施（Wikipedia 消歧页）。**以他命名，不是他办的。**
- **Sorbey, Meuse / Sorbey, Moselle**——法国两个市镇。
- **`Sorbus` / `Sorbi`**（花楸属及其种加词）——★ 本次实测的**真实词形碰撞**：在 `journalofroyalmi262roya` 全文里搜 `Sorb`，4 个命中中有 2 个是 `On dead branches of **Sorbus** Aucuparia, the author finds a second species of Cucurbitaria, which he names C. **Sorbi**.`（scratchpad 副本 offset 1364711/1364799）。**博物学语料里做 `Sorb*` 前缀匹配会中招。**

### 1.7 ★ 给护栏的直接结论

1. 只比姓 → 漏 9 个（其中 3 个是同代英国专业人士）。
2. 比「姓 + 单个首字母」→ 仍漏 `T. C. Sorby`（OCR 把 T/H 互读是常态）。
3. **可用的判据是三选一同时成立**：`Clifton` 出现在名字里 **或** `Sorby` 旁边有 `F.R.S.`／`F.G.S.` **或** 出处是 1850–1908 年的学会会刊／《Nature》／BAAS Report。
4. **1846/1847 年以前、Sheffield 出处、署名只有 `Henry Sorby` 的文件，一律不得默认归给目标人物。**

---

## 二、一手材料清单（逐条给真实 locator）

★ 计数口径：**按「作品」去重，不按 archive.org id 计数**。本人物的 id 塌缩非常严重——单是 1862 年的 Bakerian Lecture 就有 `jstor-112306`、`paper-doi-10_1098_rspl_1862_0117`、`philtrans01590980` **三个 id 指同一篇**。全表 63 条 IA 命中里，落在 1840–1912 的只有 **40 条**，去重后 **≈24 件**独立作品，再加上整卷期刊里逐篇定位到的，合计 **≈34 件**。

### A. 皇家学会（Proc. Roy. Soc. / Phil. Trans.）—— 8 件，全部可下载

每件都有 `<id>.pdf` + `<id>_djvu.txt`；`licenseurl = https://creativecommons.org/publicdomain/mark/1.0/`（PD Mark）。

| # | 作品 | 年 | 可用 id（**同一篇的多个 id 必须合并计一件**） |
|---|---|---|---|
| A1 | The Bakerian Lecture: On the Direct Correlation of Mechanical and Chemical Forces | 1862（Proc. Roy. Soc. **12:538–550**，见 `philtrans01590980` description 原样） | `jstor-112306` / `paper-doi-10_1098_rspl_1862_0117` / `philtrans01590980` |
| A2 | On the Microscopical Structure of Meteorites | 1863 | `jstor-112058` / `paper-doi-10_1098_rspl_1863_0075` / `philtrans06701849` |
| A3 | On a Definite Method of Qualitative Analysis of Animal and Vegetable Colouring-Matters by Means of the Spectrum Microscope | 1866 | `jstor-112671` / `paper-doi-10_1098_rspl_1866_0101` / `philtrans07502180` |
| A4 | On the Structure of Rubies, Sapphires, Diamonds, and Some other Minerals（与 **P. J. Butler** 合著） | 1868 | `paper-doi-10_1098_rspl_1868_0050` / `philtrans02377210` |
| A5 | On Jargonium, a New Elementary Substance Associated with Zirconium | 1868 | `jstor-112452` / `paper-doi-10_1098_rspl_1868_0105` / `philtrans06936978` |
| A6 | On Some Remarkable Spectra of Compounds of Zirconia and the Oxides of Uranium | 1869 | `jstor-112741` / `paper-doi-10_1098_rspl_1869_0048` / `philtrans03649923` |
| A7 | On Comparative Vegetable Chromatology | 1872 | `paper-doi-10_1098_rspl_1872_0090` / `philtrans05874967` |
| A8 | On Some Hitherto Undescribed Optical Properties of Doubly Refracting Crystals.--Preliminary… | 1877 | `paper-doi-10_1098_rspl_1877_0059` / `philtrans08452871` |

实测样本（`jstor-112058`）：`112058.pdf` 353,984 B、`112058_djvu.txt` 7,512 B，`is_dark = None`，无 access-restricted 标记。

### B. 《Nature》通讯与短文 —— 8 件，全部可下载

全部 `collection = paper_doi_mirrored_texts`，PD Mark，`.pdf` + `_djvu.txt` 齐备。

| # | 题名 | 年 | id |
|---|---|---|---|
| B1 | Remarkable Spectra of Compounds of Zirconia and Uranium | 1870 | `paper-doi-10_1038_001588a0` |
| B2 | On the Various Tints of Foliage | 1871 | `paper-doi-10_1038_004341a0` |
| B3 | On the Best Form of Compound Prism for the Spectrum Microscope | 1871 | `paper-doi-10_1038_004511a0` |
| B4 | Chlorophyll Colouring-Matters | 1873 | `paper-doi-10_1038_008224b0` |
| B5 | The Colouring of Birds' Eggs | 1878 | `paper-doi-10_1038_018426c0` |
| B6 | On the Autumnal Tints of Foliage | 1884 | `paper-doi-10_1038_031105a0` |
| B7 | The Preparation of Marine Animals and Plants as Transparent Lantern-Slides | 1898 | `paper-doi-10_1038_057520a0` |
| B8 | On the Colouring Matters of Flowers | 1908（**卒年，很可能是遗稿**——未核实是否身后刊出） | `paper-doi-10_1038_077260b0` |

### C. 博物学期刊（BHL → biostor）—— 4 件，全部可下载

| # | 题名 | 年 | id | 备注 |
|---|---|---|---|---|
| C1 | XIX.—On the organic origin of the so-called 'Crystalloids' of the chalk | 1861 | `biostor-90680`（vol 8, pp.**193–200**） | licenseurl 是 **CC BY-NC 3.0**——这是 biostor 给自己扫描件贴的标，**不是原文的权利状态**（原文 1861 年，早已 PD）。★ 与记忆里「聚合器的 license 不是权利声明」同形，别据此判定不可用，也别据此判定可用；以出版年为准 |
| C2 | On the Green Colour of the Hair of Sloths | 1881 | `biostor-284053` | |
| C3 | On the Ascidians collected during the Cruise of the Yacht 'Glimpse,' 1881（与 **W. A. Herdman** 合著） | 1882 | `biostor-284078` | 与 DNB 所载「1872 年母亲去世后购游艇 Glimpse」互证 |
| C4 | Notes on some Species of Nereis in the District of the Thames Estuary | 1906 | `biostor-283693` | 卒前两年 |

### D. 单行本／抽印本 —— 1 件

| # | 作品 | 坐标 |
|---|---|---|
| D1 | **On the microscopical structure of crystals, indicating the origin of minerals and rocks**，1858，`Printed by Taylor and Francis` | <https://archive.org/details/OnTheMicroscopicalStructureOfCrystalsIndicatingTheOriginOfMinerals_125>。IA description 原样：`From the Proceedings of the Geological Society. Quarterly journal of the Geological Society for November 1858, vol. XIV, pp. 453-500.` 文件：`sorby-h-microscopical-1858-RTL010259.pdf` 39,864,668 B、`_djvu.txt` **156,809 B**、另有 LowRes 版与 `.epub`。上传者 `library@gia.edu`（GIA 图书馆） |

**这是他岩相学奠基工作的单篇核心印本，且是本清单里唯一一件他自己的长篇岩相文本可直接全文取得的。**

### E. 《Monthly Microscopical Journal》整卷（BHL 扫描，全卷 `_djvu.txt` 800 KB–1.1 MB）—— 已逐篇定位 8 件

这批是**最有价值的一块**：他 1874–1877 年任皇家显微学会主席，年会致辞是长篇第一人称。以下坐标全部来自 archive.org **fulltext/inside.php** 实跑（返回 leaf 号），非推想。

| # | 作品 | 卷 / 印本页 | IA id | leaf | 取证原样 |
|---|---|---|---|---|---|
| E1 | On the Connection between Fluorescence and Absorption | v.13 (1875), p.**163**– | `monthlymicroscop13roya` | 199 | `IV. — On the Connection between Fluorescence and Absorption. By H. C. Sorby, F.R.S., &c., President R.M.S.` |
| E2 | Microscope Spectrum Apparatus | v.13 (1875), pp.**199–207** | `monthlymicroscop13roya` | 242–251 | `By H. C. Sorby, F.B.S., &c., Pres. K.M.S.`（**`F.B.S.` 讹字，正确读法 `F.R.S.`；`K.M.S.` 讹字，正确读法 `R.M.S.`**） |
| E3 | ★ **THE PRESIDENT'S ADDRESS（1876-02-02 宣读）** | v.15 (1876), pp.**105–121**+ | `monthlymicroscop15roya` | 121–137 | `I.—THE PRESIDENT'S ADDRESS. By H. C. Sorsy, F.RS., F.L.8., F.G.8., F.Z8., &c. (Delivered before the Royau MicroscopicaL Society, Mebruary 2, 1876.)`（**讹字：`Sorsy`→Sorby；`F.RS.`→F.R.S.；`F.L.8.`→F.L.S.；`F.G.8.`→F.G.S.；`F.Z8.`→F.Z.S.；`Royau`→Royal；`Mebruary`→February**） |
| E3b | Corrections in the President's Address | v.15, p.**194** | 同上 | 220 | `Corrections in the President's Address.` |
| E4 | Photographs of Nobert's 19th Band | v.16 (1876), p.**7** | `monthlymicrosco161876roya` | 15 | `Photographs of Nobert's 19th Band. By H.C. Sorby. 7` |
| E5 | A New Form of Small Pocket Spectroscope | v.16, p.**65** | 同上 | 79 | `A New Form of Small Pocket Spectroscope. By H.C. Sorby. 65` |
| E6 | The Structure of Amber（与 **P. J. Butler** 合著） | v.16, pp.**227–231** | 同上 | 257–261 | `The Structure of Amber. By H. C. Sorby and P. J. Butler, 227` |
| E7 | ★ **Anniversary Address of the President（1877）** | v.17 (1877), pp.**117–125**+ | `monthlymicrosco01britgoog` | 136–144 | `AnniverBary Address of the Prestdeni, H. G. Sorby, F.R.S. 117`（**讹字：`AnniverBary`→Anniversary；`Prestdeni`→President；`H. G.`→H. C.**） |
| E8 | On a New Arrangement for distinguishing the Axes of Doubly Refracting Substances | v.18 (1877), pp.**209–211** | `monthlymicroscop1818roya` | 243–245 | `Axes of Doubly Refracting Sub-stances, on a New Arrangement for distinguishing the. By II. C. Sorby, F.R.S., 209.`（**`II. C.` 讹字，正确读法 `H. C.`**） |

权利状态：`monthlymicrosco161876roya` 的 `possible-copyright-status` 原样以 `Not in copyright. The BHL kn…` 开头；`monthlymicroscop1818roya` 以 `Public domain. The BHL consi…` 开头。**其余几卷该字段为空**（`None`）——但出版年 1875–1877，PD 判定不依赖聚合器的标注（记忆条「聚合器的 license 不是权利声明」）。

**★ 未扫完的部分（诚实空缺）**：MMJ v.1–v.12、v.14 只做了抽样，`monthlymicrosco15britgoog`（v.14）只搜到一条主持记录（`H. C. Sorby, Esq., F.E.S., President, in the chair.` leaf 303），**不代表 v.14 里没有他的论文**——只代表我没有逐卷扫。同理 JRMS（1878 年起）系列只扫了 2 卷。**这一块的真实数量应当高于 8。**

### F. 书籍章节 —— 1 件，★ 全清单里唯一的长篇第一人称自述

**《Essays on the Endowment of Research》(London: H. S. King & co., 1876)，Essay VI，pp. 149–178**

- 题名与署名（印本 p.149 / **leaf 163**，OCR 原样，未改动）：
  > `unencumbubed ee8eabch: a personal e:^pebienge.`
  > `By Heitet Oxifton Soebt, F.R.S., President of the Hoyal Microscopical Society.`
  - **正确读法：`UNENCUMBERED RESEARCH: A PERSONAL EXPERIENCE.` / `By Henry Clifton Sorby, F.R.S., President of the Royal Microscopical Society.`**
- 目录页（**leaf 14**）原样：`By Henry Chiton Soebt, F.E.S., President of the Boyal Micro-.tcopical Society page 149`
- 正文开头（同 leaf 163，OCR 原样，仅合并折行）：
  > `The question which I propose to discuss in the following pages is whether it is better for the progress of original discovery if an investigator is able to devote to it his whole time and thought free from the cares and duties of any other occupation… I am thankful to say that complete immunity from any such routine employment has been my own happy lot…`
- 篇幅：Essay VII 起于 p.179，故本篇 **约 30 印本页**。
- 坐标：<https://archive.org/details/essaysonendowmen00patt>，`essaysonendowmen00patt_djvu.txt` **610,104 B**。

**★★ 这一条同时是一次判据事故的现场：**
`fulltext/inside.php?q=Sorby` 对这本书返回 `{"indexed": true, "matches": []}`——**零命中**。
`grep -i sorby` 对整份 610 KB 全文同样零命中。
**书里确实有他，OCR 把他的姓读成了 `Soebt`。** 改查 `q=Soebt` 立刻返回 2 条（leaf 14 与 leaf 163）。
→ **「搜不到」在这个人物身上不等于「没有」。任何以 `Sorby` 为唯一关键词的覆盖统计，在 19 世纪扫描件上都会低报。**

### G. 英国科学促进会 Report（BAAS）—— 3 件

**G1/G2 同卷：`reportofbritisha65brit`**（Bath 1864 年会，NHM London 扫描，`_djvu.txt` **2,569,699 B**）
索引原样（leaf 727）：
> `Sorby (H. C.) on the conclusion to be drawn from the physical structure of some meteorites, 70; on microscopical photographs of various kinds of iron and steel, 189.`

| # | 作品 | 印本页 | 正文原样（scratchpad 副本 byte offset） |
|---|---|---|---|
| G1 | On the Conclusion to be drawn from the Physical Structure of some Meteorites | Trans. Sections **p.70** | offset 1665149：`On the Conclusion to be drawn from the Physical Structure of some Meteorites. By H. C. Sorsy, h.AS., FG.`（**讹字：`Sorsy`→Sorby；`h.AS., FG.`→F.R.S., F.G.S.**） |
| G2 | ★ **On Microscopical Photographs of various Kinds of Iron and Steel** | Trans. Sections **p.189** | offset 2191999：`On Microscopical Photographs of various Kinds of Iron and Steel.` / `By H. C. Sorpy, F.RS., F.GS,`（**讹字：`Sorpy`→Sorby**）。正文约 180 词，下一页版口 `190 +) onmportT——1864:`（＝`190  REPORT—1864`） |

同卷还记他为 **SECTION C.—GEOLOGY** 的秘书（offset 88531，原样 `Secretaries.—H. C. Sorby, F.R.S.; W. Pengelly, F.R.S.; W. B. Dawkins, F.G.S. ; J. Johnston,`）。

**G2 的重要性**：1911 年 EB「Metallography」条给出的正式著录是
> `H. C. Sorby, "On Microscopical Photographs of Various Kinds of Iron and Steel," Brit. Assoc. Report (1864), pt. ii. p. 189`
> （<https://en.wikisource.org/wiki/1911_Encyclop%C3%A6dia_Britannica/Metallography>）

**页码 189 完全对上。这是目前唯一一件我实际取到全文的、他本人的金相学发端文本。**
⚠️ 但它是 **BAAS Report 的第三人称摘要**（`The author first briefly explained how sections of iron and steel may be prepared…`），**不是他的声口**。

**G3：`reportofbritisha64brit`**（Newcastle 1863 年会，NHM 扫描，`_djvu.txt` 3,664,217 B）
索引原样（leaf 1099/1102/1103）：`Mica-schist and slate, H. C. Sorby on models illustrating contortions in, 88.`
→ 印本 **p.88**，同样是摘要体。

### H. 书信手稿 —— 1 个 source_id，2 封信

<https://archive.org/details/letters00sorb>
- creator 原样 `Sorby, Henry Clifton, 1826-1908, author`
- description 原样：`2 items` / `Two A.L.S. ([18]67 April 16, Hyde Park, [London] and [18]70 March 10, Sheffield) concerning microscopy` / `Gift; Bern Dibner`
- 权利原样：`Public domain. The Library considers that this work is no longer under copyright protection`
- 藏：Smithsonian Libraries and Archives，call_number 39088003346152
- 文件：`letters00sorb.pdf` 2,880,620 B；`letters00sorb_djvu.txt` **仅 809 B**（手写体，OCR 基本失败）

⚠️ **可下载 ≠ 可用**：809 字节的 OCR 对手写信几乎等于没有。要用必须人工转录扫描页。**且转录件不是逐字引文的合法来源，除非在答案里说明它是转录。**

---

## 三、拿不到 / 只拿到部分的

### 3.1 ★★★ 最痛的一处：JISI 1886 与 1887 两卷，本次全部通道未获

他在金相学上的两件核心印本：

| 作品 | 著录来源（PD，可核） | 状态 |
|---|---|---|
| **On the Application of Very High Powers to the Study of the Microscopical Structure of Steel**，Journal of the Iron and Steel Institute，**1886**，p.**511**（JRMS 摘要页码） | JRMS 1886 索引原样（`journalofroyalmi262roya` leaf 633）：`Sorby, H. C., Application of Very High Powers to the Study of the Micro-scopical Structure of Steel, 511.` | **JISI 原卷未获** |
| **(On the) Microscopical Structure of Iron and Steel**，*Journ. Iron and Steel Inst.* (**1887**), p.**255** | 1911 EB「Metallography」条正式著录（Wikisource，PD） | **JISI 原卷未获** |

**卡在哪一步（写清楚，换台机器能续）：**
1. `archive.org advancedsearch: title:("Journal of the Iron and Steel Institute") AND mediatype:texts`，rows=100 → numFound 200，但**年份分布是 1871、1883、1899、1900、1912，然后直接跳到 1921**。1886/1887 两卷**不在 archive.org**。
2. 换 `title:("iron and steel institute") AND year:[1884 TO 1892]` → 65 条，全是名录、目录、教科书，**没有会刊本身**。
3. Google Books API `https://www.googleapis.com/books/v1/volumes` → **HTTP 429**，错误体原样：`Quota exceeded for quota metric 'Queries' and limit 'Queries per day' of service 'books.googleapis.com' for consumer 'project_number:624717413613'`。**是本机匿名配额当日耗尽，不是 Google 拒绝这本书——换机器／隔天重试大概率能通。**
4. HathiTrust → 见 §四，403。

**目前的诚实退路（已实际取到，但要标清性质）**：
- **《Nature》1886-05-20「THE IRON AND STEEL INSTITUTE」**，`paper-doi-10_1038_034062a0`，`_djvu.txt` 29,482 B。
  卷首原样：`NA TURE [May 20, 1886] THE IRON AND STEEL INSTITUTE — r T > HE Iron and Steel Institute held its meeting on the 12th, 13th, and 14th inst., under the presidency of Dr. J. Percy, F.R.S., in the Theatre of the Institution of Civil Engineers.`
  Sorby 段落在 **djvu.txt 第 263–307 行**（约 45 行 ≈ 2 栏），开头原样：
  > `Dr. H. C. Sorby drew attention to the application of very high powers to the stucfy of the microscopical structure of steel, having employed a power of 650 linear which, being about ten times that used in his previous researches, opened out a new field for research.`
  （**`stucfy` 讹字，正确读法 `study`**）
  段内含珠光体层片的完整推理链（`these smaller crystals finally split up into alternating very thin plates` / `a stable compound of iron with a small amount of carbon existed at a high temperature, which at a lower broke up into…`）。
  ⚠️ **全段是第三人称间接引语，是记者转述，不是他写的字。**

### 3.2 地质学会主席年会致辞（1879 / 1880）—— 只拿到作者自供的摘要

- **1879「The Structure and Origin of Limestones」**：`paper-doi-10_1038_019424b0`（《Nature》1879-03-06），`_djvu.txt` 18,553 B，正文在第 132–233 行。
  脚注原样（第 164–165 行）：
  > `Abstract of Anniversary Address to the Geological Society by Mr. H. C. Sorby, F.R.S., President, communicated by the author.`
  → **「communicated by the author」意味着摘要是他自己供的**，但正文仍是第三人称（`the president confined his own special address to…`）。**性质介于一手与二手之间，必须在使用处标明。**
- **1880「On the Structure and Origin of Non-Calcareous Stratified Rocks」**：**本次未找到任何免费全文**。QJGS 全卷在 archive.org 上覆盖极稀（`title:("Quarterly journal of the Geological Society") AND year:[1850 TO 1890]` 只有 **12 条**，且缺 vol.14 / vol.35 / vol.36 —— 正是 1858 / 1879 / 1880 三篇的原卷）。
- **1858 年那篇的原卷（QJGS vol. XIV）同样不在 archive.org**——好在有 GIA 上传的抽印本（§D1），**内容等价，但要记成一处来源不是两处**。

### 3.3 日记（1859–1908，共 11 本）—— 存在、已编目、**未数字化**

<https://archives.shef.ac.uk/repositories/3/resources/333>（HTTP 200）
- Reference Code **51**；日期范围 1845–1906；规模 **9 boxes and 2 volumes**
- 藏品含：`eleven diaries spanning 1859-1908`、`one diary from his father covering 1845-1846`、`printed papers with manuscript amendments`（**他亲笔批注的抽印本！**）、建筑摄影
- 访问条件原样：`Available in our reading room by appointment. Photographs have been digitised and can be viewed online`
- → **只有照片数字化了；日记与带批注的抽印本必须到馆**。

**这是本人物最有价值的声口材料，也是本次唯一一处「材料存在、权利无碍、而本机取不到」的经典延后类型（通道＝物理馆藏，不是 bot 墙）。**

### 3.4 ★ 他的姓在 OCR 里的全部实测讹形（供检索器直接用）

以下每一个都是**本次实际取回的字符**，不是我推想的：

`Soebt`（Essays 1876，两处）、`Sorsy`（BAAS Report ×2、MMJ v.15）、`Sorpy`（BAAS Report ×2）、`Sorbi)`（MMJ v.17，原样 `Mr. Sorbi) on the Bed Clays of the Ocean-ioUom`）、以及首字母讹形 `H. G. Sorby`、`U. G. Sorby`、`IT. C. Sorby`、`II. C. Sorby`、`E. 0. Sorby`。
学位后缀讹形：`F.RS.` `F.E.S.` `F.B.S.` `F.B.8.` `F.E.9.` `F.K.S.` `F.G.8.` `F.L.8.` `F.Z8.` `h.AS.` `F.GS,`（全部＝F.R.S. / F.G.S. / F.L.S. / F.Z.S.）。

---

## 四、被挡住的通道（写清坐标，换台机器能续）

| 通道 | 我怎么试的 | 返回 | 形态 |
|---|---|---|---|
| **HathiTrust 全文阅读** | `curl -A "Mozilla/5.0 …" -L "https://babel.hathitrust.org/cgi/pt?id=mdp.39015021231657"` | **HTTP 403** | bot 墙。整站阅读端点对脚本关闭 |
| **HathiTrust 目录检索** | `https://catalog.hathitrust.org/Search/Home?lookfor=Journal+of+the+Iron+and+Steel+Institute&type=title` | **HTTP 403** | 同上 |
| HathiTrust Bib API | `https://catalog.hathitrust.org/api/volumes/brief/oclc/1754499.json` | **HTTP 200**，但返回 `{"records": {}, "items": []}` | **接口通、该 OCLC 无记录**。这条**不是被挡**，是我给的 OCLC 号不对 → 后续可用正确 OCLC 重试 |
| **Biodiversity Heritage Library 网站** | `https://www.biodiversitylibrary.org/search?searchTerm=Sorby` | **HTTP 403** | bot 墙 |
| **BHL API v3** | `https://www.biodiversitylibrary.org/api3?op=PublicationSearch&searchterm=Sorby&format=json` | **HTTP 401**，body 原样 `{"Status":"unauthorized","ErrorMessage":"'' is an invalid or unauthorized API key."}` | 需注册 API key。**免费可申请，但本次没有 key，也没有申请（不动账号）**。★ 好消息：BHL 的扫描件本身大量镜像在 archive.org（§E 那批就是），绕道可通 |
| **Google Books API** | `https://www.googleapis.com/books/v1/volumes?q=…` | **HTTP 429**，`Quota exceeded … 'Queries per day' … consumer 'project_number:624717413613'` | **当日匿名配额耗尽**。非永久障碍 |
| **Grace's Guide 全文检索端点** | WebFetch `https://www.gracesguide.co.uk/index.php?search=Sorby&title=Special%3ASearch&fulltext=1&ns0=1&limit=100` | **HTTP 401** | 只有 `Special:Search` 全文端点被挡；**普通条目 URL 全部 200**（已实测 5 个）。绕法：直接猜条目名逐个探测 |
| **Wikidata SPARQL** | `https://query.wikidata.org/sparql`（含 UNION 的姓氏＋标签查询） | **HTTP 504 upstream request timeout** | 查询太重。绕法：改用 `www.wikidata.org/w/api.php` 的 `list=search` + `wbgetentities`，**已成功** |
| **archive.org 下载重定向** | `curl -L https://archive.org/download/reportofbritisha65brit/…_djvu.txt` | 重定向到 `dn720006.ca.archive.org`，**HTTP 500（nginx）**，body 只有 170 B 错误页 | **偶发节点故障**。绕法：先 `GET /metadata/<id>` 取 `server` 与 `dir`，再直连 `https://<server><dir>/<file>` → **HTTP 200，2,569,699 B**。★ 这条要记牢：`-L` 的 200 不代表拿到了正文 |

---

## 五、陷阱与不确定（★ 宁可标不确定）

### 5.1 ★ 父亲卒年两说，本次未裁定
- Grace's Guide `Henry_Sorby` 条：`1846 Died`
- Wikipedia `Henry Clifton Sorby` 条：`In 1847, when he was 21, his father died, leaving him a comfortable private income.`
- **差一年，而这一年正好是「1846 年以前的 `Henry Sorby` 归谁」这条护栏的分界线。** 两个都别写死；用的时候写「1846 或 1847（两说）」。

### 5.2 ★ 母亲名两写
DNB：`Amelia Lambert`；Grace's Guide：`married Amelia Lamberts in London`。未裁定。

### 5.3 ★ Bakerian Lecture 年份两说
IA/philtrans 的 description 原样把它系于 `Proceedings of the Royal Society of London (1854-1905). 1862-01-01. 12:538–550`；Wikipedia 写 `Bakerian Lecture (1863)`。**卷期页码有原样出处，年份没有**——用页码，别用年份。

### 5.4 ★ Thomas Charles Sorby 出生地两说
Wikipedia：`Chevet, West Riding of Yorkshire`；另一检索来源：`Wakefield, Yorkshire`。未裁定。**（Chevet 就在 Wakefield 近郊，可能两者兼容，但我没有证据说它们是同一件事，所以不合并。）**

### 5.5 ★★ 在版权期内的东西冒充一手 —— 找到 1 个确凿的、1 个半

**(1) 确凿：`sorbycentennials0000sorb`**
`The Sorby Centennial Symposium on the History of Metallurgy, Cleveland, Ohio, October 22-23, 1963 : proceedings`，`New York : Gordon and Breach`，1963。
- `associated-names` 原样含 `Smith, Cyril Stanley, 1903-; **Sorby, Henry Clifton, 1826-1908**; …`
- `access-restricted-item = true`，collection 含 `inlibrary` / `printdisabled`
- **实测**：`curl -L .../sorbycentennials0000sorb_djvu.txt` → **HTTP 401**（172 B）。对照组 `monthlymicroscop15roya_djvu.txt` → **HTTP 200（824,990 B）**。
- → **1963 年版权作品，受控借阅，不可下载、不得使用。**它之所以危险，是因为 `creator:("Sorby")` 检索会返回它、`associated-names` 里挂着目标人物、题名以 Sorby 开头，**看起来像一部 Sorby 文集**。

**(2) 半个：`sorby_on_meteorites_2022_english`**
`On Meteorites`，creator 原样 `['Henry Clifton Sorby', 'Solar Anamnesis']`，2022，`licenseurl = https://creativecommons.org/publicdomain/zero/1.0/`（CC0），uploader `solaranamnesis@tutanota.com`，collection `opensource`/`community`。
description 列出它汇编了 `On the Microscopical Structure of Meteorites.` / `On the Conclusion to be deduced from the Physical Structure of some Meteorites.` / `On the Physical History of Meteorites.` 等篇。
- **权利上没问题**（底本 PD，汇编者声明 CC0）。
- **但它是 2022 年的重新排版本，不是原始印本。**逐字引文一律不得引它——**引了就是引一份来路不明的转录**。要引就引 §A2 / §G1 的原扫描件。
- 它有 8 种不同排版的 PDF/djvu（`_aurical`、`_coelacanth`、`_compmodern`、`_custom`…），**同一份文本在同一个 id 下有 8 个文件，极易被当成 8 份材料。**

**(3) 翻译本，不是原文：`b28081444`**
`Relazione fra il limite degli ingrandimenti del microscopio e le molecule ultime della materia organica ed inorganica : discorso pronunziato il giorno 2 febbraio 1876 all'Adunanza della Reale Società Microscopica di Londra`，`Torino : Ermanno Loescher`，1877，Wellcome Library 藏，rights 原样为 CC Public Domain Mark。
- IA 的 `creator = Sorby, H. C`、`language = und`（未标语种），**看起来像一件 Sorby 的一手作品**。
- **实际是 §E3 那篇 1876-02-02 英文主席致辞的意大利文译本。**
- → **权利可用，内容可用，但绝不能当英文逐字引文。**它与 E3 是**同一件作品**，做 source 计数时必须合并。

### 5.6 ★ 两个（三个）id 不等于两处证据 —— 本人物尤其严重
- 1862 Bakerian Lecture：3 个 id
- 1863 Meteorites：3 个 id
- 1866 Colouring-Matters：3 个 id
- 1868 Jargonium：3 个 id
- 1869 Zirconia spectra：3 个 id
- 1868 Rubies / 1872 Chromatology / 1877 Doubly Refracting：各 2 个 id
- 1858 QJGS 抽印本：同 id 下 2 套 PDF（Low/High Res）+ epub
- 2022 汇编本：同 id 下 8 套排版
→ **40 条 1840–1912 的 IA 命中，去重后只有约 24 件独立作品。**不去重会直接把一手份数虚高 60%。

### 5.7 ★ 我不确定、没查的
- **1908 年那篇《Nature》「On the Colouring Matters of Flowers」是不是身后刊出**——他 1908-03-09 卒，条目 date 是 `1908-01`。**未核实。**
- **他一生「no fewer than two hundred and forty publications」**（Grace's Guide 原样）——本次只定位到约 34 件。**剩下约 200 件在哪，本次没查**，其中相当一部分应在 Proc. Yorkshire Geological Society、Proc. Sheffield Literary and Philosophical Society、Geological Magazine、Mineralogical Magazine、Journal of the Linnean Society 等本次完全没扫的刊物里。
- **MMJ / JRMS 只抽扫了 7 卷**，v.1–v.12、v.14、以及 1878 年后的 JRMS 全系列没有逐卷扫。
- **讣告一批**（DNB 列出 `Journal Geol. Soc. 1909; Proc. Roy. Soc. 1908; Geol. Mag. 1908; Nature, lxxvii. 465; Proc. Yorks. Geol. Soc. vol. xvi. 1909; Naturalist, 1906`）——**一条都没去取**。它们是二手，但对建立时间线有用。

---

## 六、粗估份数 vs quick 档门槛

| 项 | 值 | 说明 |
|---|---|---|
| **已定位的独立一手作品** | **≈34 件** | A 8 + B 8 + C 4 + D 1 + E 8 + F 1 + G 3 + H 1（信 1 个 source_id）。已按作品去重，未把同篇的多 id 计重 |
| **其中我实际取回过正文字节的** | **7 件** | Essays 1876 Essay VI、BAAS 1864 p.70、BAAS 1864 p.189、Nature 1886 ISI 报道、Nature 1879 限石摘要、MMJ v.15 主席致辞（片段+坐标）、JRMS 1886 索引 |
| **其余 27 件** | 已确认 `.pdf` + `_djvu.txt` 存在且 HTTP 200 可取，**但本次未逐件下载正文** | 这是探测，不是抓源 |
| quick 档 ≥8 份来源 | **✅ 远超（≈34 ≥ 8）** | |
| quick 档一手 ≥0.40 | **✅ 不构成压力** | 34 件一手意味着二手可加到 51 件仍守住 0.40 |
| deep 档 ≥30 份一手 | **✅ 已达（≈34），且天花板远高于此** | Grace's Guide 记他有 240 篇发表；本次只扫了不到 15% |

**→ 本人物不属于「一手规模不够」的延后类。**

---

## 七、下一步该先做什么（给抓源阶段的三条硬提醒）

1. **先量声口密度，再排期。** 现有 34 件里，**真正第一人称的只有 F1（Essay VI，≈30 页）、E3（1876 主席致辞，≈17 页）、E7（1877 年会致辞）、以及 A/B/C/E 各篇论文的正文**；而 G1/G2/G3（BAAS 摘要）、Nature 1886 会议报道、Nature 1879 限石摘要**全是第三人称转述**。按「来源数」排期会得到虚高的印象——记忆条「门数的是来源，不是声口」在这个人物身上直接命中。

2. **金相学这一支目前是残的。** 他之所以进库是「金相学奠基者」，而这一支现在只有：1864 BAAS 摘要（第三人称，180 词）+ 1886 Nature 报道（第三人称，约 45 行）+ JRMS 1886 的一条索引。**JISI 1886/1887 两卷必须再攻一次**（Google Books 配额、HathiTrust 换通道、或找 1880s–1890s 冶金教科书里的转载）。**在拿到之前，不要把这个产物宣传成金相学人物。**

3. **同名门要按 §1.7 的三选一判据设，不能只比姓、也不能只比「姓+首字母」。** 并且**每一次都要拿 §1.2 的父亲 `Henry Sorby` 和 §1.3 的 `T. C. Sorby` 各测一次**——记忆条「每个人物都要重测同名护栏」正是为 Coffin 那次事故立的。
