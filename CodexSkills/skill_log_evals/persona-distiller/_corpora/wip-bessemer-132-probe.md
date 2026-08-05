# Henry Bessemer (1813–1898) —— 抓源探测报告 #132

- 探测日期：2026-08-05
- 范围：**只探测取证，未建工作区，未下载整本书**。
- 取证方式说明（重要，供复核）：archive.org 的整本 `_djvu.txt` **没有落盘**。所有正文证据来自两类调用：
  1. `fulltext/inside.php` 搜索内文 API（返回片段 + leaf 号）；
  2. `curl -r <byte-range>` 定点字节区间取样后直接管道 grep（只保留命中行）。
  下文每条引文都注明了它是哪一种来源、以及可回查的坐标。
- **OCR 声明**：archive.org 的文本是 ABBYY FineReader 8.0 OCR 产物，含可辨识讹字。凡引用带讹字的行，本报告**同时给出 OCR 原样字符串和正确读法**，并明确标注哪个是哪个。禁止把改过讹字的串再当"逐字引文"使用。

---

## 〇、一句话结论

一手材料**可得**，但本人物有一个**很硬的坑**：他的传世核心文本《Sir Henry Bessemer, F.R.S.: An Autobiography》(1905) 是**两个 Henry Bessemer 合写的**——正文 pp.1–326 是本人，**Chapter XXI（pp.327–约380，含那份著名的专利清单）是他同名的长子 Henry Bessemer (1838–1907) 写的**。书的版权页、archive.org 的 creator 字段、以及编者在 Chapter XXI 开头的方括号说明都写着这件事，但一眼扫过去看不出来。**约 14% 的书不是他写的。**

---

## 一、同名风险（namesake）

### 1.1 ★最高危：他的长子也叫 Henry Bessemer（1838–1907）

**证据 A —— 1905 年原书 Chapter XXI 开头的编者方括号说明**
坐标：archive.org `sirhenrybessemer00bessuoft`，`_djvu.txt` 字节区间 930800–933200，紧接 CHAPTER XXI 标题之后（印本页码 p.327 起）。
取证方式：byte-range grep。
OCR 原样（除折行合并外未改动）：

> `[The Bessemer Autobiography terminates with the preceding page. The obvious intention to continue it, practically to completion, was never carried out; for although to within a few months of his death Sir Henry was busily occupied in collecting notes of an active though retired period, the narrative to be evolved from these notes was not commenced. The alternative was, therefore, to present an unfinished story, or to complete it with the assistance of his eldest son, Mr. Henry Bessemer. The latter alternative being considered the more desirable, and Mr. Bessemer having kindly offered his collaboration, the following Chapter has been added to this book. — Ed.]`

紧接其后是儿子的第一人称开头（同一取证方式，同一区间）：

> `rr^HE unfortunate destruction of my father's copious notes relating -*- to those years of his Hfe after he had retired from active business, but not from usefulness, has made my task a difficult one, because I have to rely on memory, aided by some memoranda and letters ; and because I was not at that time in constant touch with my father, as he resided in London and I in a rather distant part of the country.`

（`rr^HE` = OCR 花体首字母 T 的残迹，正确读法 `THE`；`Hfe` 正确读法 `life`。）

**这条方括号说明是本次探测最重要的一条证据**，理由：
- 它把「本人写的」和「儿子写的」的**分界线钉死在 p.326 / p.327 之间**；
- 它同时演示了一个致命的标签陷阱：**在这本书里，`Mr. Henry Bessemer` 和 `Mr. Bessemer` 指的是儿子，`Sir Henry` 指的是父亲**。而在同一本书的 1856 年场景里，`Mr. Henry Bessemer` 指的是父亲（当时尚未受封）。**同一个字符串在同一本书里指两个人。**

**证据 B —— archive.org 元数据的 creator 字段**
坐标：`https://archive.org/metadata/sirhenrybessemer00bessuoft`
原样：`creator = ['Bessemer, Henry, Sir, 1813-1898', 'Bessemer, Henry']`
→ 编目员也认了两个作者，第二个没有生卒年。

**证据 C —— Grace's Guide 给儿子单开了一页**
坐标：<https://www.gracesguide.co.uk/Henry_Bessemer_(1838-1907)>（HTTP 200，已打开）
页面内容要点（原样短语）：`1838 Born in Hemel Hempsted, Herts`、`son of Henry Bessemer`、`1861 Analytical chemist`；他是 **Bessemer Brothers** 的一员，厂址 `London Iron and Steel Works, East Greenwich, in the county of Kent`；妻 Henrietta，子 `Herbert`（1872 年生于 Wandsworth）。
→ **儿子本人也是冶金业者、也是分析化学家、厂子也叫 Bessemer**。这意味着 1860s–1900s 的钢铁行业文献里出现的 "Mr. Bessemer" 有真实的二义性，不是理论风险。

**证据 D —— Grace's Guide 父亲页底部的讣告列表**
坐标：<https://www.gracesguide.co.uk/Henry_Bessemer>（HTTP 200，已打开）
列出：`1898 Obituary [1898 Institution of Mechanical Engineers: Obituaries]`、`1898 Obituary [1898 Institution of Civil Engineers: Obituaries]`、`1898 Obituary [The Engineer 1898/03/18], p256`、`1898 Obituary [1898 Iron and Steel Institute: Obituaries]`、**`1907 Obituary [Engineering 1907 Jan-Jun: Index: General Index]`**。
→ **最后那条 1907 讣告是儿子的**，混在父亲页面上。抓语料时若按"Grace's Guide 父亲页列出的讣告"整批取，会把儿子的讣告一起收进来。

### 1.2 其他同姓风险

| 人 | 生卒 | 为什么会混进工程/冶金文献 | 坐标 |
|---|---|---|---|
| **Anthony Bessemer** | 1758–1836 | 父亲。发明家、金匠、铸字厂主，曾任职巴黎造币厂，做过**从大模翻制钢冲模的机器**；1784 年 26 岁入选法国科学院。属于精密制造/模具/冶金语境 | <https://www.gracesguide.co.uk/Anthony_Bessemer>（HTTP 200，已打开） |
| **Alfred George Bessemer** | 1840–1918 | 次子 | <https://www.gracesguide.co.uk/Alfred_George_Bessemer>（**仅在搜索结果里见到该 URL，未逐页打开**） |
| **Herbert Bessemer** | 生于 1872 | 孙 | 见证据 C 同页 |

**非人物的同名噪声**（会污染关键词检索，但不会造成署名误判）：Bessemer Process、Bessemer Gold Medal、Bessemer converter、Bessemer pig、Henry Bessemer and Co、Bessemer Steel and Ordnance Co、Bessemer Saloon Steamship Company / 该船、Bessemer（美国阿拉巴马州地名）。

### 1.3 ★署名／演讲标签**在真实页面上的原样字符串**

以下每条都是我**实际取回的字符**，不是我推想的形式。

| # | 原样字符串 | 是谁 | 场合 | 坐标 / 取证方式 |
|---|---|---|---|---|
| L1 | `Mr. Henry Bessemer, who would now read his Paper on " The Manufacture of Iron Without Fuel."` | **父**（受封前） | 1856 BAAS Cheltenham，George Rennie 的介绍词 | `sirhenrybessemer00bessuoft` `_djvu.txt` 字节 438000–452000，byte-range grep |
| L2 | `Denmark Hill, (Signed) Hbney Bessemer.` | 父 | 1878-10-29 信件 | 同书 字节 104000–118000，byte-range grep。**`Hbney` 是 OCR 讹字，正确读法 `Henry`** |
| L3 | `I remain, your obedient servant,` / `Denmark Hill, January 3, 1878. Henry Bessemer.` | 父 | 致《The Times》信 | 同书 字节 1025000–1096122，byte-range grep。此条无讹字 |
| L4 | `I am, Sir, your obedient servant,` / `Hbnry Bessemer.` / `Denmark Hill, April 17, 1882.` | 父 | 《The Times》1882-04-18 "Easter and the Coal Question" | 同上区间。**`Hbnry` 是 OCR 讹字，正确读法 `Henry`** |
| L5 | `Sir Henry Bessemer,` / `165, Denmark Hill, Surrey.` | 父（受封后） | F. W. Webb 来信的**收件人抬头** | 同上区间 |
| L6 | `LIST OF PATENTS GRANTED TO HENRY BESSEMER, 1838-1883.` | 父 | p.329 附录标题 | 同书 字节 933000–940000 |
| L7 | 版口（verso）`328 HENRY BESSEMER` / `160 HENRY BESSEMER` …… | 父 | 全书偶数页版口固定为 `<页码> HENRY BESSEMER` | 多处，见 §二.A |
| L8 | 版口（recto）`THE CHELTENHAM PAPER, 1856 157` / `… 159` / `… 161` / `THE CHELTENHAM PAPER, 1856. 163` | — | 奇数页版口＝章题 | 同书 字节 448000–480000 |
| L9 | `LIST OF BESSEMER S PATENTS` | — | p.330+ 版口。**`BESSEMER S` 是 OCR 丢撇号，正确读法 `BESSEMER'S`** | 同书 字节 930000–975000 |
| L10 | `THE END OP THE BESSEMER SALOON STEAMSHIP COMPANY 325` | — | 版口。**`OP` 是 OCR 讹字，正确读法 `OF`** | 同书 字节 925500–931500 |
| L11 | `Be it known that I, HENRY BESSEMER, of Queen Street Place, New Cannon Street, in the city of London, civil engineer, a subject of the Queen of Great Britain, have invented or discovered new and useful Improvements in Malleable or Bar Iron and Steel...` | 父 | 美国专利 16,082 说明书开头 | <https://patents.google.com/patent/US16082A/en>（HTTP 200，已打开） |
| L12 | `Bessemer, Henry, 559` / `Bessemer, Mr., and his Competitors, 522` / `Bessemer's Improvements in Iron and Steel, 464, 516` / `In re Bessemer's Patent (Chancery Court). 122` | 父 | 《The Engineer》1856 下半年索引 | <https://www.gracesguide.co.uk/The_Engineer_1856_Jul-Dec:_Index:_Miscellaneous>（HTTP 200，已打开） |
| L13 | `Bessemer, (Sir) Henry` / `Sir Henry Bessemer` | 父 | 多伦多大学图书馆书卡（编目形式，非署名） | 同书 字节 1090000–1096122 |
| L14 | `his eldest son, Mr. Henry Bessemer` / `Mr. Bessemer having kindly offered his collaboration` | **子** | 1905 年编者按 | 见 §1.1 证据 A |

**给检索器的直接结论：**
- 他**本人在印刷品上的署名形式是 `Henry Bessemer`**（L3/L4/L6/L11），**不是** `Sir Henry Bessemer`、**不是** `H. Bessemer`。
- `Sir Henry Bessemer` 是**别人称呼他**的形式（L5/L13），且只在 1879 年受封之后成立。
- 全大写 `HENRY BESSEMER` 只出现在**版口和专利说明书正文**（L6/L7/L11），不是演讲标签。
- **本次探测没有找到任何一处印刷体的学会发言标签**（如 `Mr. BESSEMER said`）。见 §三.2，这是本次的诚实空缺，不要凭印象去搜 `Mr. BESSEMER said`——我在 5 个卷册里搜过，零命中。

### 1.4 ★篇名本身就是个同名/异写风险

用户在任务里给的篇名是 "The Manufacture of Iron Without Fuel"。我查到的**原文互相打架**，四种写法都有真实出处：

| 写法（原样） | 出处 | 坐标 |
|---|---|---|
| `The Manufacture of Iron Without Fuel` | 1905 原书，Rennie 介绍词内的引号里 | 同书 字节 438000–452000 |
| `On the Manufacture of Iron and Steel without Fuel` | 1905 原书后段某人回忆：`There he read his Paper "On the Manufacture of Iron and Steel without Fuel."` | 同书 search-inside，leaf 462 |
| `On the Manufacture of Malleable Iron and Steel without Fuel` | DNB 1901 supplement | <https://en.wikisource.org/wiki/Dictionary_of_National_Biography,_1901_supplement/Bessemer,_Henry>（已打开） |
| `a paper on the manufacture of malleable iron without fuel` | 1905 原书，Budd 先生早餐桌上的口语转述 | 同书 字节 438000–452000 |

**为什么会打架**——DNB 那条给了原因，原样引用：
> `His famous British Association paper was excluded from the 'Transactions' of that body.`

**即：英国科学促进会的年度 Report 里没有这篇论文的正式印本，所以不存在一个"官方篇名"。** 后世每个人是照着自己手上的转述写的。
**处置建议：以 1905 年原书里 Rennie 介绍词的引号内容 `The Manufacture of Iron Without Fuel` 为准，并在任何引用处注明"篇名各源不一，学会 Report 未收录"。**

---

## 二、一手材料清单

### A. 自传 —— 《Sir Henry Bessemer, F.R.S.: An Autobiography》(1905, 遗著)

| 项 | 值 |
|---|---|
| 出版 | `London, Offices of "Engineering,"` 1905 |
| 扫描本 1（**本次实际取证用的就是它**） | <https://archive.org/details/sirhenrybessemer00bessuoft> — 多伦多大学 Gerstein 馆藏，508 leaves，PDF 39,970,084 bytes，`_djvu.txt` 1,096,122 bytes |
| 权利声明（原样） | `possible-copyright-status = NOT_IN_COPYRIGHT` |
| 扫描本 2 | <https://archive.org/details/sirhenrybessemer00bess> — 波士顿公共图书馆，512 pp |
| 站点可访问性 | archive.org HTTP **200**（本次全程可用，search-inside API 与 byte-range 均正常） |
| Google Books | <https://books.google.com/books?id=imtEAQAAMAAJ> HTTP **200**（只打开了简介页，**未验证是否 full view**） |
| HathiTrust | Record/001041120 → HTTP **403**，见 §三.3 |

> ⚠️ **两个 archive.org id 不等于两处证据。** 上面两个扫描本是**同一版（1905, Offices of "Engineering"）的两次扫描**，实质是**一处**一手来源。做 source_id 统计时必须合并，否则会塌缩。

**★ 是不是一手？分段判定（这是本条最重要的信息）：**

| 页码 | 作者 | 一手判定 | 依据 |
|---|---|---|---|
| pp. 1–326（Ch. I–XX） | **Sir Henry Bessemer 本人** | ✅ **一手**，第一人称自述 | 全书版口 `<页码> HENRY BESSEMER`；p.326 结束在 `...was never completed, was never tested at sea, and consequently never failed.` |
| **pp. 327–约380（Ch. XXI）** | **长子 Henry Bessemer (1838–1907)** | ❌ **不是他写的**，是儿子的回忆＋编纂 | §1.1 证据 A 的编者方括号 |
| 其中 pp. 329–332+ 专利清单 | **儿子编的** | ❌ **不是他写的** | 儿子原话（字节 933000–940000）：`I have been at some pains to make as complete a list as possible of these patents and applications for patents, and this list I subjoin, arranged chronologically.` |
| Ch. XXI 内转载的他本人书信（L3/L4） | 本人 | ✅ **一手**（转载载体是儿子的章，但文本是他自己的） | 见 L3/L4 |

本次实测的正文页码锚点（全部 byte-range grep 命中）：`154 HENRY BESSEMER`、`THE CHELTENHAM MEETING OP THE BRITISH ASSOCIATION 155`、`156 HENRY BESSEMER`、`THE CHELTENHAM PAPER, 1856 157/159/161/163`、`160/162/164/166 HENRY BESSEMER`、`THE END OP THE BESSEMER SALOON STEAMSHIP COMPANY 325`、`326 HENRY BESSEMER`、`328 HENRY BESSEMER`、`336/338/340/342/344/348/350/352/356/378/380 HENRY BESSEMER`。正文文本止于约 p.380。

### B. 他本人的论文／演讲

**B-1｜1856 年 Cheltenham 英国科学促进会论文（篇名见 §1.4）**

- **全文在哪拿**：**1905 年自传内的逐字转载**，pp. 约156/157–164，章题版口 `THE CHELTENHAM PAPER, 1856`。
- 一手理由：作者本人在转载前一句写明（原样，byte-range grep，字节 438000–452000）：
  > `The audience received me very kindly, and I had the honour of reading my paper, of which a verbatim copy is here given.`
- 论文开头原样（同区间）：
  > `The manufacture of iron in this country has attained such an important position that any improvement in this branch of our national industry cannot fail to be a source of general interest, and will, I trust, be sufficient excuse for the present brief, and, I fear, imperfect paper. I may mention that for the last two years my attention has ...`
- 站点：archive.org，**此刻可访问（HTTP 200，已实际读取）**。
- **原始报纸印本（The Times, 1856-08-14）：本次未取得，未验证任何免费通道。** 见 §三.2。
- BAAS 官方 Report：DNB 明说被排除在 Transactions 之外（§1.4）。

**B-2｜1859 年 5 月 Institution of Civil Engineers 论文，题 `" On the Manufacture of Malleable Iron and Steel,"`**

- 一手理由：他本人在自传里第一人称说（原样，byte-range grep，字节 595000–630000）：
  > `It was deemed desirable to communicate these facts to the world, through the Institution of Civil Engineers, whose members could not fail to be deeply interested in the production of a new kind of homogeneous cast steel... I, therefore, wrote a paper " On the Manufacture of Malleable Iron and Steel,"`
- 同处另一句钉住时间：`the small malleable iron gun which I exhibited in May, 1859, at the Institution of Civil Engineers`
- **部分全文在哪拿**：自传 p.223 起转载了论文＋讨论的摘录（版口 `BESSEMER IRON AND STEEL 223`），他本人的说明原样：
  > `The following is one of the extracts referred to, which has been reproduced from the report of my paper, and the discussion thereon, printed by the Institution of Civil Engineers, and sent to all its members.`
- **ICE 原刊全文：未取得。** archive.org 上 ICE《Minutes of Proceedings》最早只到 1850 与 1863（v.23）以后，**1858–59 会期那一卷不在 archive.org**（已用 advancedsearch 按 `year:[1857 TO 1862]` 查过，只返回 1857 与一本德文书）。icevirtuallibrary.com → HTTP **403**。

**B-3｜1861 年在 Sheffield 向 Institution of Mechanical Engineers 宣读的论文**

- 依据：自传目录条目（search-inside，leaf 13，原样）：
  > `... Steel-making at Sheffield — Gun-making at Sheffield — Paper Read before the Institution of Mechanical Engineers at Sheffield — The Exhibition of 1862 ... 216 to 239`
- 图版目录（leaf 16）：`Institution of Mechanical Engineers at Sheffield, 1861. To face pa^e 234`（`pa^e` = OCR，正确读法 `page`）。
- **IMechE 原刊全文：未取得。** archive.org 上 IMechE Proceedings 19 世纪卷只有 1851 与 1870 两个 Google 扫描件，两卷内搜 `"Mr. Bessemer"` 均 **0 命中**。

**B-4｜Iron and Steel Institute 的两篇论文**

- 依据（**注意：这条是儿子写的**，search-inside leaf 484，原样）：
  > `A matter of much importance, not referred to in the Autobiography, is Sir Henry Bessemer's close connection with the Iron and Steel Institute, of which he was one of the founders in 1868, and the President in 1871 to 1873. He only contributed two Papers to the Institute. The first of these was read in 1886, on "Some Earlier Forms of Bessemer Converters"; the second was read in 1891, and is published in the " Transactions " under the title of " The Manufacture of Continuous Sheets of Malleable Iron or Steel direct from the Fluid Metal."`
- 两篇篇名是**一手材料的线索**，但**这段话本身是二手（儿子转述）**，且儿子把 ISI 的刊物叫成 `Transactions`（ISI 实际出 *Journal*），说明他这段不精确。
- **两篇论文的全文：本次均未取得。** 见 §三.2。

### C. 学会讨论席上他本人开口的段落

**本次探测结果：未取得任何一处。** 详见 §三.2 与 §三.4。
唯一间接可用的是 B-2 里自传转载的 ICE 讨论摘录（p.223 起），但那是他**论文正文**的摘录，不是讨论席上的对话记录。

### D. 专利说明书

**D-1｜英国专利清单（129+ 件，1838–1883）**
- 在哪拿：自传 pp. 329–332+，标题原样 `LIST OF PATENTS GRANTED TO HENRY BESSEMER, 1838-1883.`
- 实测取回的条目样例（byte-range grep，字节 933000–947500，原样）：
  `1838 Marcli 8. No. 7,585.`（`Marcli` = OCR，正确读法 `March`）、`1841 Jan. 6. No. 8,777.`、`1843 June 15. No. 9,775.`、`1846 July 30. No. 11,317.`、`1855 Oct. 17. No. 2,317.` / `2,319.` / `2,321,` / `2,323.` / `2,325.` / `2,327.`、`1855 Dec. 7. No. 2,768.`、**`1856 Feb. 12. No. 356.`**、`1856 May 31. No. 1,290.`、`1856 Aug. 19. No. 1,938.`、`1856 Nov. 4. No. 2,585.`
  同页可见专利题名串：`Manufacture of malleable iron and steel.`、`Manufacture of malleable iron and steel, and of railway and other bars, plates, and rods.`、`Apparatus for the manufacture of malleable iron and steel.`、`Manufacture of malleable iron and steel, and furnaces...`
  （OCR 把双栏排版的"编号栏"和"题名栏"拆开了，编号与题名的**对应关系在 OCR 文本里已丢失**，要配对必须看 PDF 页图。）
- ⚠️ **这份清单是儿子编的**（§二.A）。清单本身不是一手；清单指向的专利说明书才是。

**D-2｜美国专利 16,082（1856-11-11）—— 本次唯一实际打开的专利全文**
- URL：<https://patents.google.com/patent/US16082A/en> — HTTP **200**，已打开
- 题名原样：`Improvement in the manufacture of iron and steel`
- 发明人串：`Henry Bessemer of London, England`
- 说明书开头（一手，第一人称）：见 §1.3 的 L11
- PDF：`https://patentimages.storage.googleapis.com/b5/5b/30/b6793c1001c0fc/US16082.pdf`（页面上给出的链接，**未单独下载验证**）
- 一手理由：专利说明书是申请人本人具名提交的法律文书，第一人称 `Be it known that I, HENRY BESSEMER...`

**D-3｜英国专利说明书原件（GB 1856 No. 356 等）**
- Google Patents `GB185600356A` → HTTP **404**（Google Patents 不收这个编号形式的旧英国专利）
- Espacenet `worldwide.espacenet.com` → HTTP **403**（见 §三.3）
- **结论：本次未取得任何一件英国专利说明书原件。**

---

## 三、诚实的负面清单

### 三.1 看起来像一手、其实**不是他写的**

| 材料 | 为什么不是一手 | 坐标 |
|---|---|---|
| **★《自传》Chapter XXI（pp.327–约380）** | **儿子 Henry Bessemer (1838–1907) 写的**。这是全项目最容易踩的一脚：书名、书脊、版权页、书卡全是 "Sir Henry Bessemer"，但书的最后 ~14% 不是他 | §1.1 证据 A |
| **★自传里的专利清单（pp.329–332+）** | 儿子编纂的二次整理，儿子自己写了 `I have been at some pains to make as complete a list as possible` | §二.A |
| 自传里关于 ISI 的那段（两篇论文篇名） | 儿子转述，且把刊物名写错成 `Transactions` | §二.B-4 |
| 编者按（署名 `— Ed.`） | 《Engineering》编辑部所写 | §1.1 证据 A |
| 1898 年四份讣告（IMechE / ICE / The Engineer 1898/03/18 p256 / ISI） | 别人写他 | Grace's Guide 父亲页 |
| **1907 年讣告（Engineering）** | **是儿子的讣告**，却挂在父亲的 Grace's Guide 页上 | §1.1 证据 D |
| DNB 1901 supplement 词条 | 传记词条。且该文自陈：`The only biography of him in existence is a monograph by the present writer, written for the American Society of Mechanical Engineers, and published in the Transactions of that body, 1899` | Wikisource DNB 页（已打开） |
| DNB 列出的三部参考书：`Men of the Time, 1895`；`Jeans's Creators of the Age of Steel`；`Mushet's Bessemer-Mushet Process, 1883` | 三部都是他人著作；Mushet 那本还是**争议对手方**的书 | 同上 |
| 1911 EB `Bessemer, Sir Henry`、New International Encyclopædia 词条 | 百科条目 | Wikisource（**仅在搜索结果里见到 URL，未逐页打开**） |
| Wikipedia / Britannica / Grokipedia / invent.org / ASME / EBSCO / thefamouspeople / Dulwich Society / Worshipful Company of Engineers / IOM3 | 三次文献 | 搜索结果 |
| Grace's Guide 的 `Henry Bessemer` 词条正文 | 维基式二次编纂。**但它页底的书目/讣告索引是有用的一手指路牌** | 已打开 |
| IEEE REACH 的 US16082 页面 | 是**教学包装**页；真正的一手是它指向的专利文本 | 搜索结果，未打开 |

### 三.2 只有二手转述、本次**找不到原文**的

1. **1856-08-14《The Times》上的论文全文印本。** 多个二次源说它在那天见报，但我**没有找到任何免费可访问的 1856 年 Times 原版页**。The Times Digital Archive 是订阅制，按铁律未尝试。
2. **1856 年 BAAS 年度 Report 里的论文。** DNB 明说被排除（`excluded from the 'Transactions'`），所以**大概率根本不存在这份印本**。
3. **ICE 1859 年 5 月论文的原刊全文及其讨论记录。** archive.org 无此卷，ICE 官方库 403。目前只能拿到自传 p.223 起的摘录。
4. **IMechE 1861 年 Sheffield 论文的原刊全文。** archive.org 上仅有的两个 19 世纪 IMechE 卷（1851、1870）内搜零命中。
5. **ISI 1886《Some Earlier Forms of Bessemer Converters》与 1891《The Manufacture of Continuous Sheets of Malleable Iron or Steel direct from the Fluid Metal》。** 篇名只有儿子的转述，**两篇的全文本次一件都没找到**。
6. **★任何一处印刷体的学会发言标签。** 我在 5 个卷册里做了内文搜索，**全部零命中**：
   - `minutesofproceed24inst`（ICE v.24, 1864）：`"Mr. Bessemer"` → 0；`Bessemer` → 1（只是索引里的论文题名 `38. On the Bessemer and other processes of Steel-making`）
   - `minutesofproceed26inst`（ICE v.26）：`"Mr. Bessemer"` → 0；`Bessemer` → 4（全是他人论文题名/正文提及）
   - `proceedingsinst00jourgoog`（IMechE 1870）：`"Mr. Bessemer"` → 0
   - `proceedingsinst05jourgoog`（IMechE 1851）：`"Mr. Bessemer"` → 0
   - `in.ernet.dli.2015.221456`（JISI v.56, 1899）：`"Mr. Bessemer"` → 0
   - 自传内搜 `"Mr. Bessemer said"` → 0
   **所以：C 类（学会讨论席上他开口的段落）本次为空。任何后续工作不要假设 `Mr. BESSEMER said` 这个串存在——它在我能打开的卷册里一次都没出现过。**
7. **英国专利说明书原件。** 见 D-3。

### 三.3 通道受限（域名 + 实测返回）

全部为本次实测，带 `Mozilla/5.0` UA、跟随重定向：

| 域名 / URL | 实测 | 说明 |
|---|---|---|
| `catalog.hathitrust.org/Record/001041120` | **HTTP 403** | 目录页都进不去，不是"限阅"而是**整站挡爬**。WebFetch 返回：`The server returned HTTP 403 Forbidden.` |
| `babel.hathitrust.org/cgi/pt?id=uc1.b4533063` | **HTTP 403** | 全文阅读器同样被挡 |
| `worldwide.espacenet.com/patent/search?q=bessemer` | **HTTP 403** | 英国旧专利的权威库，**这是 D-3 拿不到英国专利原件的直接原因** |
| `www.icevirtuallibrary.com/toc/jmipi/63/1881` | **HTTP 403** | 且本身是订阅制（Emerald 托管），**未尝试绕过，未尝试付费墙** |
| `www.googleapis.com/books/v1/volumes` | **HTTP 429** | 原样错误信息：`Quota exceeded for quota metric 'Queries' and limit 'Queries per day' of service 'books.googleapis.com' for consumer 'project_number:624717413613'`，`"quota_limit_value": "0"`。**本机这条通道的配额是 0，等多久都不会恢复**，换机器/换 key 才行 |
| The Times Digital Archive | **未尝试** | 订阅制，按铁律不碰 |

**可访问（HTTP 200，本次实际用过）**：`archive.org`（含 `fulltext/inside.php` 搜索内文 API 与 `ia*.us.archive.org` 的 byte-range）、`www.gracesguide.co.uk`、`patents.google.com`、`books.google.com`（仅简介页）、`en.wikisource.org`。

### 三.4 ★探测过程中发现的两个数据缺陷（会误导后续排期，单列）

**缺陷 1：archive.org 的年份字段可以是错的，而且错得离谱。**
`journalironands01instgoog` 与 `journalironands02instgoog` 在 advancedsearch 里报 `year = 1871`（元数据 `date` 字段分别是 `1869 1871` 和 `1902 1871`），我据此以为找到了 Bessemer 任 ISI 主席期间的会刊。实际内搜 `Bessemer` 返回的是：
> `THOMAS SWINDEN. Esq., D.Met.. Member of Council. Bessemer Gold Medallist, 1941.`
> `Preeeniation of the Bessemer Oold Medal for 1941 to Dr. T. Swinden`

**这卷的实际内容是 1941/1942 年的**，比标注晚 70 年。若照标注取用，会把 20 世纪中叶的文本当成 Bessemer 在世时的会刊——**而且它很可能还在版权期内**。
→ **规矩：任何 archive.org 卷册在取用前，必须先内搜一个只可能出现在目标年代的词，验一次内容年代；不要信 `year` 字段。**

**缺陷 2：`fulltext/inside.php` 必须用元数据里的 `server` + `dir` 拼路径，否则静默返回 0 命中。**
我第一次查 `minutesofproceed24inst` 用了猜的 server/path，返回 `matches: 0`；换成元数据里的 `ia800704.us.archive.org` + `/35/items/...` 后才拿到真结果。
→ **`0 命中` 在这个 API 上既可能是"真没有"，也可能是"路径拼错了"。这正是[空默认值吞掉「不知道」]的同一形态。凡报 0 命中，必须先用一个必然命中的词（如人物姓氏）自检通道，再下"没有"的结论。**
本报告 §三.2 第 6 条的 5 个卷册**全部**做过这一步自检（`Bessemer` 单词能命中、`"Mr. Bessemer"` 才是 0），所以那个 0 是真的。

---

## 四、版权分档（分开说）

| 对象 | 判定 | 依据 |
|---|---|---|
| Bessemer 本人的文字（论文、书信、专利说明书、自传 pp.1–326） | **公有领域** | 卒于 1898；英国 pma+70 → 1968 年到期 |
| 1905 年版《自传》这个**版本整体** | **公有领域** | 1905 出版 < 1931（2026 年的美国 PD 分界，随年份滚动）；archive.org 标 `NOT_IN_COPYRIGHT` |
| **Chapter XXI（儿子写的）** | **公有领域**，但**作者是另一个人** | 儿子卒于 1907；pma+70 → 1977 年到期。**版权到期不等于署名可以混用** |
| 编者按（`— Ed.`，1905，作者未署名） | **公有领域** | 1905 出版，匿名 → 英国 pub+70 → 1975 年到期 |
| 现代重印本／带新导言的复刻本 | **未判定，默认不可用** | 新导言、新编者注、新排版可能各自起算新版权。**本次未触碰任何现代重印本** |
| US Patent 16,082 (1856) | **公有领域** | 美国政府出版物 + 1856 年 |

---

## 五、给下一步的建议（不构成已完成工作）

1. **开工第一件事是把 p.326/p.327 这条线画进语料切分脚本**，否则儿子写的 ~54 页会被当成本人语料入库。这正是 [related-to-him-is-not-written-by-him] 的同形复现，且本次是**在同一本书内部**发生的，比 Liebig 那次更隐蔽。
2. 专利清单要用**PDF 页图**重建"编号↔题名"配对，OCR 文本里这层对应已经丢了。
3. 换一台不受 403/429 限制的机器再跑一次：HathiTrust、Espacenet、Google Books API。**坐标已在 §三.3 写全，换机即可续。**
4. C 类（学会发言）在放弃前，值得再试的免费通道：Grace's Guide 托管的《The Engineer》与《Engineering》各期扫描件（它们逐期报道 ISI/IMechE 会议且带发言人标签），本次因时间未逐期打开。

---

*报告完。本文件只做探测记录，未建工作区、未落盘任何书籍全文。*
