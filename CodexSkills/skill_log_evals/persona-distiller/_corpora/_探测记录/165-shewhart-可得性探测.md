# #165 Walter A. Shewhart —— 公有领域可得性探测

**探测日期**：2026-08-10　**执行**：子代理（并发 1，未下载文件，未触付费墙/验证码）

## 结论（我的判读，不是子代理的）

**★ 他与 #164 Heinrich 不同——不是「代表作差一年」那一类，是「代表作在墙内、而墙外另有一批一手」。**

| | Heinrich #164 | **Shewhart #165** |
|---|---|---|
| 代表作 | 1931（差一年） | 1931（差一年） |
| ≤1930 的一手 | **无** | **8 份已核实可免费全文，约 210 页** |
| 判读 | 只能等 2027-01-01 | **现在就能做，不必等书** |

≤1930 侧的实体：BSTJ 六篇（1924–1930，124 页）＋ 1914 硕士论文（82 leaves）＋ 1922 PNAS（4 页）。
**恰好 8 份 = quick 档 `min_sources` 的下限，零余量**——掉一份就过不了门，排期时要知道这一点。

声口：三个样本实测第一人称 **6.7–14 / 千词**，非零、中等密度；
**但只覆盖「正式论文」一端**，演讲/讨论体裁三个方向都没找到免费原文——
按 [[measured-voice-in-the-wrong-register]]，这是**单语域测量**，不能当全语域结论用。

同名者 0 个真风险；真正的污染源是**以他命名的术语**（Shewhart Chart / Cycle / Medal），
建库时要显式排除「别人写的、提到他名字」的文本。

---

以下为子代理原始报告，逐字保留。

# Walter A. Shewhart（1891–1967）可得性探测报告

探测方式：只读网页探测（WebSearch + WebFetch），**未下载任何文件到本地**，并发恒为 1，未触碰付费墙/验证码。
PD 判据：`published_at ≤ 1930` 才算公有领域；1931 年出版物按美国规则 1931+95=2026 年内仍受保护，**2027-01-01** 才进入公有领域。
探测时间：2026-08-10。

---

## ① 《Economic Control of Quality of Manufactured Product》首版年份

**结论：1931 年，D. Van Nostrand Company, Inc.（New York），xiv+501 页。这是「差一年」的情形 —— 若确为 1931，需等到 2027-01-01 才进入公有领域，本项目 2026-08-10 探测时点尚不可用。**

一手/近一手证据（五个独立来源交叉核实，互相一致）：

1. **archive.org 藏品 `in.ernet.dli.2015.150272`**（Digital Library of India 扫描件，标注为该书「第七版印次 SEVENTH PRINTING」实体扫描）
   URL: https://archive.org/details/in.ernet.dli.2015.150272
   我直接读取了该扫描件的 OCR 全文（`_djvu.txt`），版权页文字显示 **"Copyright ... 1931" / "By D. van Nostrand Company, Inc."**，印刷地 Lancaster, PA。这是我唯一能拿到、来自实体 1931 年版书页本身的文字证据。
   ⚠️ 但该条目页面本身的目录字段（`dc.date.citation`）标注的是「**1923**」，且同一次 OCR 抽取也一度把序言签署日期读成「April, 1923」——两者互相矛盾，且与史实不符（书中收录的 1924-05-16 备忘录不可能晚于序言）。我判断这是这份 印度数字图书馆（DLI）扫描件元数据本身的錄入/OCR 讹误（DLI 扫描的元数据质量问题是已知现象），**不采信「1923」**，理由见下方交叉证据。同一条目的出版地字段还写着「D. van Nostrand Company, **London**」，与其它四个独立来源的「New York」不一致，进一步印证这份元数据不可靠，只把它的版权页 OCR 原文当证据，不把它的目录字段当证据。

2. **archive.org 藏品 `economiccontrolo0000shew`**（1980 年 ASQC 五十周年纪念重印本扫描件）
   URL: https://archive.org/details/economiccontrolo0000shew
   该重印本扉页背面（t.p. verso）印着 **"Originally published: New York : Van Nostrand, 1931"**，ISBN 0873890760，LCCN 91195803。

3. **Google Books / 威斯康星大学麦迪逊分校馆藏扫描**
   URL: https://books.google.com.au/books/about/Economic_Control_of_Quality_of_Manufactu.html?id=JtVnAAAAMAAJ&redir_esc=y
   条目显示：出版年 **1931**，出版商 D. Van Nostrand Company, Incorporated，501 页，注明是 "The Bell Telephone Laboratories Series" 第 4 卷。

4. **SPC Press**（Donald J. Wheeler 主持的专业质量控制出版社，长期重印 Shewhart/Deming 著作）
   URL: http://www.spcpress.com/book_economic_control_qmp.php
   页面明确写「原始出版年份：1931」，并说明 1980 年由 ASQC 重印、附 W. Edwards Deming 献词。

5. 多个二手书目交叉印证（不作为独立证据，仅作佐证）：WorldCat（OCLC 1045408）、SciRP 参考文献库、ScienceDirect 条目、一份标注 "1931 HC" 的 eBay 实物书拍卖列表，均记 1931 年 Van Nostrand。

**我没能做到的**：没能亲眼看到该书原版书页的**图像**（只看到 OCR 转录文字），archive.org 的 BookReader 是 JS 渲染的翻页器，本次探测工具链无法截图/渲染其画布内容，只能取 OCR 文本层。HathiTrust 目录页（`catalog.hathitrust.org/Record/001115960`）返回 403，未能核对其编目记录。

---

## ② 1930 年及以前的一手文字（核心部分）

### BSTJ（Bell System Technical Journal）—— 全部免费可得，无付费墙，逐条读取/核对了 archive.org 条目自身的编目元数据

BSTJ 在 archive.org 上有完整的开放数字化（源自 worldradiohistory.com 的扫描项目），逐条检索 `Shewhart` 后确认，1931 年之前他在 BSTJ 上共发表 **6 篇**：

| # | 标题 | 卷期 | 出版月份/年 | 页码 | 页数 | URL | 我看到年份的位置 |
|---|------|------|------------|------|------|-----|-----------------|
| 1 | Some Applications of Statistical Methods to the Analysis of Physical and Engineering Data | Vol.3 No.1 | **1924-01** | 43–87 | 45 | https://archive.org/details/bstj3-1-43 | archive.org 条目元数据 + 我直接读取了该文 OCR 全文正文 |
| 2 | Correction of Data for Errors of Measurement | Vol.5 No.1 | **1926-01** | 11–26 | 16 | https://archive.org/details/bstj5-1-11 | archive.org 条目元数据（metadata API） |
| 3 | Correction of Data for Errors of Averages Obtained from Small Samples | Vol.5 No.2 | **1926-04** | 308–319 | 12 | https://archive.org/details/bstj5-2-308 | archive.org 条目元数据（metadata API） |
| 4 | Quality Control Charts | Vol.5 No.4 | **1926-10** | 593–603 | 11 | https://archive.org/details/bstj5-4-593 | archive.org 条目元数据 + 我直接读取了该文 OCR 全文正文 |
| 5 | Quality Control | Vol.6 No.4 | **1927-10** | 722–735 | 14 | https://archive.org/details/bstj6-4-722 | archive.org 条目元数据（metadata API） |
| 6 | Economic Quality Control of Manufactured Product（此文 1931 年扩写成上面①那本书） | Vol.9 No.2 | **1930-04** | 364–389 | 26 | https://archive.org/details/bstj9-2-364 | archive.org 条目元数据 + 独立 TOC 页 `ftp.math.utah.edu/pub/tex/bib/toc/bstj1930.html` 交叉确认 |

6 篇合计 **124 页**，全部在 archive.org 上可直接下载全文（PDF / OCR 文本 / DjVu），本次探测过程中没有遇到登录墙或验证码。

### 学位论文（早于 BSTJ 时期，物理学训练背景）

| 类型 | 标题 | 机构 | 年份 | 页数 | URL | 证据 |
|------|------|------|------|------|-----|------|
| 硕士论文 (M.A.) | A study of the propagation, refraction, reflection, interference and diffraction of ripple waves | University of Illinois | **1914** | 82 leaves | https://archive.org/details/studyofpropagati00shew | archive.org 元数据明确标注 "Thesis (M.A.)--University of Illinois, 1914"，作者全名 "Shewhart, Walter Andrew" 与生平吻合 |
| 博士论文 (Ph.D.)，另有同题简报发表于 *Physical Review* | A Study of the Accelerated Motion of Small Drops through a Viscous Medium | UC Berkeley | 1917 | 未核实 | 无（见下）| **未能独立核实**：仅查到二手书目引用 "Physical Review 9 (May 1917): 432"，`journals.aps.org` 直接访问返回 403，archive.org 未检索到独立条目。不确定这是全文论文还是学会年会摘要（当年 Physical Review 常刊登一句话式的会议摘要）。**列为线索，未核实。** |

### 一篇免费开放的物理学论文（比统计质控更早、更基础）

| 标题 | 刊物 | 卷 | 年份 | 页码 | 篇幅 | URL | 证据 |
|------|------|-----|------|------|------|-----|------|
| On the Measurement of a Physical Quantity Whose Magnitude is Influenced by Primary Causes beyond the Control of the Observer and on the Method of Determining the Relation between Two Such Quantities | Proceedings of the National Academy of Sciences | Vol.8 | **1922-08-15** | 248–251 | 4 页，实测约 1,200 词 | https://archive.org/details/jstor-84021 | archive.org 条目明确标注版权状态 **"Public domain"**（源自 JSTOR Early Journal Content 计划），我直接读取了全文 OCR 正文 |

### 有据可查、但本次探测撞上付费墙、未获取全文的条目（不违反硬约束——遇墙即止，如实记）

| 标题 | 刊物 | 卷期 | 年份 | 页码 | 我核实到的程度 |
|------|------|------|------|------|--------------|
| The Application of Statistics as an Aid in Maintaining Quality of a Manufactured Product | Journal of the American Statistical Association | Vol.20 No.152 | 1925 | 546–548 | 直接访问 tandfonline.com 返回 403；标题/卷期/页码来自搜索引擎对该出版商页面的索引摘要，未亲眼打开全文 |
| Significance of an Observed Range | Journal of Forestry | Vol.26 No.7 | 1928-11 | 899–905 | **直接打开了** Oxford Academic 的文章落地页（https://academic.oup.com/jof/article/26/7/899/4753457），页面本身显示标题/作者/卷期/页码/日期，并标注 "Subscription required"，只读到落地页，未读正文 |

### 仅见于二手书目、本次未能独立核实的条目（如实列出，不冒充已核实）

以下 4 条只出现在二手传记/书目页面（Encyclopedia.com、Duke大学 HOPE 经济学史中心综述等），**我没有找到并打开任何一手或出版商的原始页面来核对**，因此不计入「已核实」清单，仅作线索记录：

- "Note on the Probability Associated with the Error of a Single Observation," *Journal of Forestry*, 26 (1928), 600–607
- "Economic Aspects of Engineering Applications of Statistical Methods," *Journal of the Franklin Institute*, 205(3) (1928), 395–405
- "Small Samples: New Experimental Results"（与 F. W. Winters 合著）, *JASA*, 23 (1928), 144–153
- "Basis for Analysis of Test Results of Die-Casting Alloy Investigation," *ASTM Proceedings*, 29 (1929), 200–210

### ★ 1924-05-16 备忘录（线索原文）

**查不到。** 这份被公认为「第一张控制图」诞生地的一页内部备忘录，本次探测未能找到任何公开数字化的原件或影印图片。查到的都是转述：
- Wikipedia（https://en.wikipedia.org/wiki/Walter_A._Shewhart）转引 Shewhart 上司 George D. Edwards 的回忆："Dr. Shewhart prepared a little memorandum only about a page in length..."，未提供原件链接。
- PMC 上一篇专门讲这份备忘录历史的文章（*Quality and Safety in Health Care*, 2006, Vol.15 No.2, pp.142–143，https://pmc.ncbi.nlm.nih.gov/articles/PMC2464836/，可免费读取全文）同样只有文字转述，明确不含原件影印图。
- 另检索到一篇 2023/2024 年的百年纪念综述（*Journal of Quality Technology*, tandfonline.com/doi/full/10.1080/00224065.2023.2282926）——直接访问返回 403，未能确认它是否收录影印图。

结论：这份备忘录本身**大概率没有被公开数字化**（或数字化后未被搜索引擎索引到、或被存放在贝尔实验室/AT&T 内部档案中未公开），只能拿到二手转述，不能拿到一手文本。

---

## ③ 声口密度 —— 分语域采样

**硬约束提醒的风险是真实的**：只抽一种语域会得出偏的结论。本次尝试寻找两类语域：
(a) 正式发表的技术论文（已找到多篇，见上）；
(b) 演讲/致辞/讨论发言改写稿（**尝试了但没能找到**）。

**(a) 正式论文语域 —— 3 个独立样本，逐一读取 OCR 正文计数：**

| 样本 | 取样范围 | 第一人称计数（I/we/my/our/us） | 密度 | 语气样例 |
|------|---------|------------------------------|------|---------|
| BSTJ 1924《Some Applications of Statistical Methods...》 | 正文前约 1,000 词 | 12 处 | ~12/千词 | "I have chosen"（真·单数第一人称，非只有editorial we） |
| BSTJ 1926《Quality Control Charts》 | 正文前约 1,000 词 | 12–14 处 | ~12–14/千词 | 以 "we" 为主，科学论文式的作者复数 |
| PNAS 1922（短技术note） | 全文约 1,200 词 | 8 处 | ~6.7/千词 | 全部是 "we/our/us"，无单数 "I"，行文更纯数理 |

三个样本**一致显示非零、中等密度的第一人称出现**（区间 6.7–14/千词），且 1924 年那篇明确出现真单数 "I"，不是纯粹编辑性复数。三篇都是"技术推导为主、夹杂少量立场性插入语"的混合语域（我请求的抽样也确认了：引言段落更有解释性/动机性表述，进入数学推导段落后第一人称基本消失）。

**(b) 演讲/口语改写语域 —— 未能取得样本，如实报告为缺口。**
尝试过的检索方向：ASTM Bulletin 讨论记录（委员会发言常带 "Mr. Shewhart said"）、1929-12-28 他在 AAAS 得梅因年会上宣读的论文、Bell Laboratories Record（贝尔实验室内部刊物，文风比 BSTJ 更通俗）——均未找到可免费打开的原文。因此**本次探测无法完成「至少各取一种语域读一段」的要求**：只覆盖了「正式论文」这一端，「口语改写」那一端缺失，不能排除他在演讲体裁下第一人称密度显著不同（更高或更低）的可能性。

---

## ④ 同名者与地名

- **姓氏本身罕见**：Shewhart 是他父亲 Antone 一代由德语姓氏 **Schuchardt** 英语化改写而来（据搜索到的家族史资料，是老师建议改的），只见于这一个家族分支，不是常见姓氏，因此"同姓无关者"的碰撞风险本身就低。
- 检索 "W. Shewhart" / "A. Shewhart" 及一般 "Shewhart" 姓氏，**没有找到任何其他在世/历史上活跃的同姓公众人物**（作者、工程师、教授等）。Wikipedia 的 `Shewhart` 词条本身就是重定向到 Walter A. Shewhart 的传记页，不是消歧义页——即维基百科自己也认为这个姓氏不需要消歧义。
- **地名**：**Shewhart Hollow**，位于伊利诺伊州 Pike County、Pleasant Vale Township，距密西西比河约 4 英里，紧邻他出生地 New Canton。这不是"碰巧同名的地方"，而是**他自己家族的地产**（他父亲 Antone 的农场就在这条山谷里，多个 Schuchardt/Shewhart 家族分支在此立业）——对语料标注而言不构成"误认成另一个人"的风险，但值得记录，因为自动抓取如果看到 "Shewhart, Illinois" 之类的地理指称，指向的仍是同一个家族/同一个人物背景，不是需要排除的另一实体。
- **需要警惕的不是人名，是他自己名字派生的术语**：**Shewhart Chart / Shewhart 控制图**、**Shewhart Cycle**（后来常被称为 PDSA/Deming Cycle）、**Shewhart Medal**（美国质量学会 ASQ 设立的以他命名的奖项，颁给其他统计学家）。如果语料抓取按字符串 "Shewhart" 匹配，会命中大量"某人获得 XX 年 Shewhart 奖"或"某教材第 X 章讲 Shewhart 图"这类**别人写的、提到他名字的文本**，这些不是他自己的一手文字，需要在建库时明确排除。这条比"同名的人"更实际地会污染语料。

---

## ⑤ 一句话结论

**已核实可免费获取全文、明确早于或等于 1930 年的 Shewhart 一手文字：8 份（1 篇硕士论文 + 1 篇 PNAS 短文 + 6 篇 BSTJ 论文），共约 210 页（82 leaves + 4 页 + 124 页），实测词数样本换算的量级约在数万词（10⁴–10⁵ 词区间，估算依据：PNAS 全文实测约 1,200 词；BSTJ 六篇合计 124 页，按已读的两篇样本页密度粗估整体在 4–5 万词量级；硕士论文 82 页粗估另加约 1.5–2 万词；这是数量级估计，不是精确计数）。**
若把"确认真实存在、但本次因付费墙未读到全文"的 2 篇（JASA 1925、Journal of Forestry 1928-11）和"仅二手书目提及、未独立核实"的 4 篇再算进"已知 1930 年及以前存在"的条目总数，则总条目数为 **14 篇**，另有 1917 年博士论文/简报及 1924-05-16 备忘录 2 条线索未能核实其可得性。

---

## 给最终回复的四点摘要素材

**① 首版年份与证据**：1931 年，D. Van Nostrand，五个独立来源交叉确认（archive.org 该书自身版权页 OCR + 1980 年重印本扉页背面声明 + Google Books/UW-Madison 馆藏编目 + SPC Press + 多个二手书目），"差一年"，2027-01-01 才进入公有领域。唯一噪声是 DLI 扫描件自己的目录字段错标 1923（同一条目版权页 OCR 原文明明写 1931），已判定为该扫描件元数据录入/OCR 讹误，不采信。

**② ≤1930 已核实份数与篇幅**：全文免费可得且已核实 8 份、约 210 页（数万词量级，非精确计数）；另有 2 份确认真实存在但撞付费墙未读全文；另有 4 份仅见二手书目未独立核实；1917 博士论文/简报与 1924-05-16 备忘录本身，两条线索都没能核实其可公开获取性。BSTJ 确认是收获最大的一处：1924–1930 年间共 6 篇、124 页，全部在 archive.org 免费开放。

**③ 声口的分语域计数**：正式论文语域 3 个样本、密度 6.7–14 处/千词，一致非零，其中 1924 年那篇有真·单数"I"；口语/演讲改写语域**没能找到样本**，这一半的比较缺失，不能排除演讲体裁下密度不同的可能。

**④ 同名者**：**0 个**构成实际混淆风险的同姓人物（姓氏是他家族独有的德语姓氏英语化拼写，Wikipedia 自己都不设消歧义页）；有 1 处地名 Shewhart Hollow（伊利诺伊州 Pike County，是他自家地产，不是需排除的另一实体）；真正的语料污染风险来自 Shewhart Chart / Cycle / Medal 这几个以他命名的术语，会让"提到他名字但不是他写的"文本混进来。

**⑤ 我没能核实的（明确列出）**：
1. 1931 年版书的实体书页**图像**（只核实到 OCR 文字层，没能看到扫描画面本身）；HathiTrust 目录页 403，未核对。
2. 1917 年博士论文全文，以及它在 *Physical Review* 上是完整论文还是仅一句话摘要（journals.aps.org 返回 403）。
3. JASA 1925 论文全文（tandfonline 403，只有出版商页面的搜索引擎索引摘要）。
4. Journal of Forestry 1928-11 那篇的正文（拿到了出版商落地页但正文订阅墙挡住）。
5. 另外 4 篇 1928–1929 年条目（Journal of Forestry 另一篇、Franklin Institute、JASA 与 Winters 合著、ASTM 1929）——只在二手书目里见过标题，没找到任何一手或出版商页面去核对卷期页码。
6. 1924-05-16 备忘录原件——查不到公开数字化版本，只有二手转述。
7. 演讲/讨论发言体裁的任何一手文本——检索了 ASTM 讨论记录、1929 年 AAAS 年会论文、Bell Laboratories Record 三个方向，均未找到可免费打开的原文，因此③的语域对比不完整。


---

## 开工状态（2026-08-10 晚补记）

**同名门跑过了，结果是 `UNVERIFIED_NAMESAKE_NO_CANDIDATES`（rc=4）——这是正确的拒绝。**

门的原话：「**一个候选都没有——这不是「没有同名风险」，是「没核」。**」
探测报告里那句「0 个构成实际混淆风险的同姓人物」是**子代理的判断**，
不是喂进门的**权威检索结果**，两者不是一回事。
（同一形状已记过：`empty-default-swallows-unknown` —— 空清单被读成「没问题」。）

**下一步**：给同名门喂 `--candidates-file`（权威检索结果），
或者在台账里写明为什么这个人没有可比对象。
★ 抓源类**并发恒为 1**，所以这一步要排在正在跑的 Deming 探测之后。

★★ 探测已经点出**本人物真正的语料污染源不是同姓者，是以他命名的术语**
（Shewhart Chart / Cycle / Medal）——建库时要显式排除「别人写的、提到他名字」的文本。
**这一条比同名门更要紧**，因为同名门只比姓，挡不住术语。


---

## ★★★ 撤回一条（2026-08-10 晚，同名权威检索之后）

上面（子代理原始报告一节）写着：
> 姓氏本身是他家族由德语姓 Schuchardt 英语化改写而来，只此一支

**这句撤回。** 做同名权威检索的那一轮明确报回来：
**这个说法只出现在搜索引擎的摘要里，不在任何一个真正读过的页面上**；
MacTutor 的传记**明确不给姓氏来源**。→ **改记为未核实。**

★ 它当时看着无害（只是个身世小注），**而我据它把 Schuchardt 全族写进了检索射程**。
射程扩大本身不是坏事（Schuchardt 确实是常见德语姓、Wikidata 上 113 人），
但**理由是错的**——扩射程的正当理由应该是「拼写近似会误命中」，不是「他家原姓这个」。

## ★★ 同名门的结果（2026-08-10 晚）

第一次跑：`UNVERIFIED_NAMESAKE_NO_CANDIDATES`（**正确拒绝**——「一个候选都没有，这不是没有风险，是没核」）。
喂进 17 个权威候选后：`BLOCKED_NAMESAKE_SELECTION`（17 个，要人选）。
选定 Walter A. Shewhart（Q462232）之后：**`status: ready`**，
`selected_subject_uid = shewhart-walter-a-1891`。

**检索纪律与「必须排除的」写在 `wip-shewhart-165/shewhart_namesake_selected.json`**，四条要点：

1. **最危险的是 `Mark Shewhart`**（OpenAlex A5054858528）——1991–2020 年
   **就发表在统计过程控制图这个领域**，常作 `M. Shewhart`，**只差一个首字母、且在目标自己的领域里**。
   → 目标 1967 年已故，**1968 年以后的新署名一律先判不是他**。
2. **真正的污染源是术语**：`Shewhart chart`（ISO 7870-2 / NIST 6.3.1 / GND 4498185-5）、
   `Shewhart cycle`、`Shewhart Medal`（ASQ，1948 首颁）。实测第三方文献
   **OpenAlex 766 / Crossref 531**（都抽了尾部核过）。**同名门只比姓，一条都挡不住。**
3. `Schuchardt` 里 **Karl（1901–1985）生卒几乎完全覆盖目标**、**Gerhard（1904–1981）职业同为 engineer**
   ——**年代与职业这两把常用筛子在他们身上都失效，只有拼写能分开**。
4. `R Shewhart` **很可能不是人**（形态像解析器把 `Shewhart R chart` 拆成了作者），**未能证实也未能证伪**。

★ 最大的核实缺口：**VIAF 全程 403、未绕**，而 VIAF 44469 这个号是从 Wikidata 拿的、
**不是从 VIAF 页面上读到的**。


---

## ★★★ 抓源之后自己复量：**8 份到齐，但「8」这个数有两种口径**

逐份剥标记后自己算的实词数（**没有采信子代理的自报**）：

| 文件 | 实词 | 页 | 词/页 |
|---|---:|---:|---:|
| `bstj3-1-43`（1924） | 14,835 | 45 | 330 |
| `bstj9-2-364`（1930） | 7,385 | 26 | 284 |
| `bstj6-4-722`（1927） | 4,264 | 14 | 305 |
| `bstj5-1-11`（1926） | 4,050 | 16 | 253 |
| `bstj5-4-593`（1926） | 3,172 | 11 | 288 |
| `bstj5-2-308`（1926） | 3,024 | 12 | 252 |
| `studyofpropagati00shew`（1914 硕论） | 5,814 | 82 leaves | **71** |
| `84021`（1922 PNAS） | 1,776 | 4 | 444 |

BSTJ 六篇词/页稳定在 250–330。**1914 硕论的 71 词/leaf 偏低，去核了：文本完整**——
题名页 `A STUDY OF THE PROPAGATION, REFRACTION, REFLECTION, INTERFERENCE AND DIFFRACTION
OF RIPPLE WAVES / BY / WALTER ANDREW SHEWHART / A. B. University of Illinois, 1913 / THESIS`，
结尾是致谢 `In conclusion I wish to thank Dr. F. R. Watson…`。
偏低是因为**它是带图版的物理论文**，82 leaves 含图版。

### ★★ 「8 份」的两种口径，必须一起说

| 口径 | 份数 |
|---|---:|
| **一手来源总数**（`min_sources` 数的就是这个） | **8** |
| **承载他为人所知的方法**（BSTJ 六篇 + 1922 PNAS） | **7** |
| 早年物理，与统计过程控制无关（1914 涟漪波硕论） | 1 |

1922 那篇 PNAS **算在方法一侧**：正文开头即
「it is impossible for the observer to control within narrow limits, **the causes of variation**
of a quantity while it is being subjected to measurement」——**那正是「可归因变异」这条根**。

★★★ **为什么必须写出这个差**：我在同一天判 Deming #167 时用的尺子是
「**内容必须承载他为人所知的方法**，早年物理论文即使 ≤1930 也不算」。
**同一把尺子用在 Shewhart 身上，是 7 < 8。**

- `min_sources` 判据本身**只数来源、不问内容**，所以按判据 8 成立、门过得去；
- 但若有人按「承载方法」的口径复核，会得到 7，**与「零余量」的说法叠加就是差一份**。

**两个数都记着，不选一个报。**（`counts-need-their-cutoff-stated`）
