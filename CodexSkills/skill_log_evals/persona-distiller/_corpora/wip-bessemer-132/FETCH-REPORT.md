# Henry Bessemer (1813–1898) —— 抓源报告 #132

- 抓源日期：2026-08-05
- 工作区：`_corpora/wip-bessemer-132/workspaces/henry-bessemer/raw/`
- 上游：`PROBE.md`（探测）、`NAMESAKE-NOTE.md`（同名处置）。本报告只记录**实际落盘**的东西。
- 落盘规模：**55 个文件 / 55 个 source_id / 254,894 词**。全部为一手。

---

## 〇、先回答那个必须回答的问题：份数

### 按「一份独立可取的文献 = 一个来源」计，**独立文献数 = 29**

| | 独立文献数 | 落成几个文件 | 为什么算这么多 |
|---|---|---|---|
| 1905 年自传（那一本书） | **1** | 27 | 无论切成 20 章还是 27 份，它**只有一次取回动作、只有一个 URL、只有一个 `_djvu.txt`**。1856 论文、1859 论文、1861 论文、1878/1882 两封《The Times》信、1890 私信、1894 文章——**七件全部是从这一本书内部取出来的**，不是七次独立取回 |
| 美国专利 | **28** | 28 | 每一件都是各自独立签发、各自独立编号、各自独立可取的美国政府出版物。逐件用 `patentimages.storage.googleapis.com/pdfs/US<号>.pdf` 单独取回并逐件验过发明人 |
| **合计** | **29** | **55** | |

### 门（quick 档：来源 ≥8 / 道 ≥3 / 一手占比 ≥0.40）怎么算

- **来源数**：按独立文献算 **29**，按文件算 55。**两种算法都过 ≥8**，而且**不靠切书**——光美国专利这一项就是 28，已经单独过门。**这一轮不需要用「同一本书的 20 章」去凑数**。
- **一手占比**：**29/29 = 1.00**（按文件 55/55 = 1.00）。工作区目前**没有落任何二手材料**。
- **道（channel）数**：**2** —— `archive.org` 与 `patentimages.storage.googleapis.com`。
  **这一项没过 ≥3。** 这是本轮的实打实缺口，见 §四。不用别的说法糊过去：
  第三条道（HathiTrust / Espacenet / ICE / Google Books API / The Times Digital Archive）**本机全部不可用**。

### 为什么还是切成了 20 章

**不是为了凑份数**（专利已经把份数做够了），是为了下游可用：整本 `_djvu.txt` 是 1,096,122 字节的单块文本，按章切成 20 份（每份 1.4k–17k 词）才好检索、好引、好定位。
**每一个章文件的头部都写死了这句话**：
`# DOCUMENT: doc-autobiography-1905 -- ONE independent document. ... The 20 chapter files are NOT 20 independent sources.`
统计来源数时**必须按 `DOCUMENT` 字段归并**，不能按目录数。

### 文本重复（必须扣掉，否则会重复计数）

7 个 derived 文件里，**有 3 个的正文与章文件重复**（它们是从章内部再切出来的）：

| 文件 | 重复于 | 重复词数 |
|---|---|---|
| `src-paper-1856-cheltenham` | `src-autobio-ch12`（pp.156–161） | 3,580 |
| `src-paper-1859-ice` | `src-autobio-ch16`（pp.223–224） | 1,175 |
| `src-paper-1861-imeche` | `src-autobio-ch16`（pp.230–231） | 808 |
| | **合计** | **5,563** |

另外 4 个（1878/1882 信、1890 私信、1894 文章）取自 **Ch. XXI（pp.364–379）**，
而 20 个章文件只到 p.326，**所以这 4 件不与任何章文件重复**。

→ **去重后正文 = 254,894 − 5,563 = 249,331 词。**

---

## 一、自传正文 pp.1–326（Ch. I–XX）—— 20 份

- 一手判定：**是**。第一人称自述，作者本人。
- 来源：archive.org `sirhenrybessemer00bessuoft`（多伦多大学 Gerstein 馆藏，504 leaves 解析成功）
  - 页面 <https://archive.org/details/sirhenrybessemer00bessuoft>
  - 文本 <https://ia601807.us.archive.org/31/items/sirhenrybessemer00bessuoft/sirhenrybessemer00bessuoft_djvu.txt>（1,096,122 字节，18,911 行，HTTP 200）
  - 权利：`possible-copyright-status = NOT_IN_COPYRIGHT`；1905 出版 < 1931（2026 年的美国 PD 分界）；作者卒 1898，英国 pma+70 已于 1968 到期。
- 提取方式：`_djvu.txt` **逐字**，未改一个字符。切分坐标由 `_djvu.xml`（12,811,416 字节）解析出的 504 个 leaf 建立。

| source_id | 章 | 印本页 | 扫描 leaf | `_djvu.txt` 行 | 词 |
|---|---|---|---|---|---|
| `src-autobio-ch01` | I 早年 | 1–18 | 22–41 | 611–1391 | 7,685 |
| `src-autobio-ch02` | II 发明的报酬 | 19–32 | 42–59 | 1394–2130 | 7,752 |
| `src-autobio-ch03` | III 石墨压制／铸字／排字机 | 33–47 | 60–78 | 2133–2743 | 5,651 |
| `src-autobio-ch04` | IV 乌得勒支绒 | 48–52 | 79–85 | 2746–2918 | 1,737 |
| `src-autobio-ch05` | V 青铜粉制造 | 53–85 | 86–118 | 2921–4264 | 13,441 |
| `src-autobio-ch06` | VI 制糖改良 | 86–95 | 119–130 | 4267–4657 | 3,252 |
| `src-autobio-ch07` | VII 德国之行 | 96–99 | 131–134 | 4660–4785 | 1,387 |
| `src-autobio-ch08` | VIII 玻璃制造改良 | 100–123 | 135–164 | 4788–5765 | 9,609 |
| `src-autobio-ch09` | IX 1851 年博览会 | 124–129 | 165–170 | 5768–5985 | 2,315 |
| `src-autobio-ch10` | X 早期火炮实验 | 130–137 | 171–178 | 5988–6277 | 2,625 |
| `src-autobio-ch11` | XI 转炉法的由来 | 138–151 | 179–206 | 6280–6950 | 5,412 |
| `src-autobio-ch12` | XII 转炉法（**含 1856 论文**） | 152–177 | 207–232 | 6953–8027 | 12,331 |
| `src-autobio-ch13` | XIII 与 Eardley Wilmot 上校 | 178–188 | 233–243 | 8030–8568 | 4,263 |
| `src-autobio-ch14` | XIV 转炉法与陆军部 | 189–199 | 244–256 | 8571–9150 | 4,269 |
| `src-autobio-ch15` | XV Armstrong 之争 | 200–215 | 257–284 | 9152–9929 | 6,469 |
| `src-autobio-ch16` | XVI 钢炮（**含 1859／1861 论文**） | 216–239 | 285–318 | 9932–11020 | 10,373 |
| `src-autobio-ch17` | XVII 造船用铸钢 | 240–255 | 319–340 | 11023–11816 | 6,136 |
| `src-autobio-ch18` | XVIII 炼钢中的锰 | 256–295 | 341–386 | 11819–13655 | 16,970 |
| `src-autobio-ch19` | XIX Ebbw Vale | 296–303 | 387–394 | 13658–13996 | 3,227 |
| `src-autobio-ch20` | XX Bessemer 号客舱汽船 | 304–326 | 395–429 | 13999–15070 | 10,665 |

**验算（已实跑）**：
- 20 份**连续、不重不漏**：相邻两份之间只有空行，无非空行落在缝里。
- 20 份拼回去与原文 pp.1–326 区间**逐行相同**（11,750 个非空行）。
- 印本 1–326 页**每一页都恰好对上一个 leaf**：leaf 22–429 共 408 个 leaf，减去 82 个无页码图版 leaf = 326，与 326 页严丝合缝。

### 页码映射是怎么建的（可复核）

版口锚点：偶数页 `<页码> HENRY BESSEMER`，奇数页 `<章题> <页码>`。**但版口 OCR 会错**——
`leaf 303` 的版口 OCR 成 `280 HENRY BESSEMER`、`leaf 304` OCR 成 `GUN-MAKING AT SHEFFIELD 281`，
实际是 **230／231**。所以映射不是照抄版口，而是先做**单调性 DP**（页码必须递增，且相邻锚点页差 ≤ leaf 差），
把不自洽的锚点剔掉，再插值。268 个候选锚点里只剔掉了上述 2 个，剔完后 1–326 页零缺口。

★ **这两页在 `src-paper-1861-imeche` 的头部单独标了红**，因为 1861 IMechE 论文正好落在这两页上，
不写清楚的话下游会照抄 OCR 的 280/281。

### 章边界的独立交叉验证

章开头 leaf 由正则 `CHAPTER <罗马数字>` 找到（OCR 变体 `CHAPTER, X` / `CHAPTEK XVIII` 也命中），
与目录页（leaf 10–13）印的页码区间**逐条对上**，20 章无一例外。目录页是书自己印的，不是我推的。

---

## 二、从自传内部取出的 7 件他本人的作品（derived，**不是新的独立文献**）

每一份的头部都写了 `DERIVED-FROM` 或 `DOCUMENT: doc-autobiography-1905`。

| source_id | 篇名 | 坐标 | 一手？ | 理由 / 注意 |
|---|---|---|---|---|
| `src-paper-1856-cheltenham` | 1856 年 Cheltenham 英国科学促进会论文 | 印本 pp.156–161；`_djvu.txt` 行 7131–7377；leaf 211–216 | **是** | 他自己写明「a verbatim copy is here given」。**篇名无定本**（BAAS Report 未收），头部列了四种写法。**注意 PROBE 说的是 pp.156/157–164，实测精确边界是 pp.156–161**：p.161 末句 `ordinary puddle-balls.` 之后就转回叙事（`During the reading of the paper, I made a chalk sketch...`），pp.162–164 是会后讨论与他的回忆，**不是论文**。边界另用字号独立验证过（论文正文字高 38–41，叙事 49–51） |
| `src-paper-1859-ice` | 1859 年 5 月 ICE 论文摘录（两段） | 印本 pp.223–224；行 10204–10292 | **是** | 他自己写明摘自「the report of my paper ... printed by the Institution of Civil Engineers」。**是摘录不是全文**。两段之间插了一行 `[[ OMITTED HERE: ... ]]`，**这是全库唯一一处我写进正文的字**，头部已声明 |
| `src-paper-1861-imeche` | 1861 年 Sheffield IMechE 论文（Proceedings 1861 第 144–145 页） | 印本 pp.230–231；行 10586–10645 | **是** | 他自己写明「I have reproduced here pages 144 and 145 from the published Proceedings for 1861」。★ **原文用第三人称 `the author`**（IMechE 的排印惯例），**别把第三人称读成别人写他**，头部已标 |
| `src-letter-1890-wd-allen` | 1890 年致 W. D. Allen 私信 | 印本 pp.364–365；行 17888–17939 | **是** | 他本人署名私信 |
| `src-times-1878-billion-dissected` | 《The Times》1878-01「A Billion Dissected」 | 印本 pp.368–370；行 18234–18323 | **是** | 落款 `Denmark Hill, January 3, 1878. Henry Bessemer.` |
| `src-times-1882-easter-and-the-coal-question` | 《The Times》1882-04-18「Easter and the Coal Question」 | 印本 pp.370–373；行 18328–18489 | **是** | 落款 `Hbnry Bessemer. / Denmark Hill, April 17, 1882.`（`Hbnry` 是 OCR 讹字，原样保留） |
| `src-engreview-1894-statistical-sketch` | 《Engineering Review》1894-07-20「A Brief Statistical Sketch of the Bessemer Steel Industry」 | 印本 pp.373–379；行 18495–18825 | **是** | 第一人称（`It is an old man's privilege...`）。p.376 是整版插图（Fig. 107），OCR 只剩图注碎字，头部已说明 |

### ★ 后 4 件的载体是**儿子的章**——已单独标注

`src-letter-1890-*`、`src-times-1878-*`、`src-times-1882-*`、`src-engreview-1894-*`
四件都落在 **Ch. XXI（pp.327–380）** 内，而 Ch. XXI 是**长子 Henry Bessemer (1838–1907) 写的**。
这四个文件的头部各有一段 `***** CARRIER WARNING *****`，写明：
- 正文是本人的，**周围的叙述是儿子的**；
- Ch. XXI 里 `Mr. Henry Bessemer` / `Mr. Bessemer` = **儿子**，`Sir Henry` / `my father` = 本人；
- pp.329ff 那份 1838–1883 专利清单是**儿子编的**，**没有入库**。

**儿子写的任何一个字都没有进 raw/。** 20 个章文件止于 p.326（末句 `never failed.`，与 PROBE 记录一致）。

---

## 三、美国专利 —— 28 份（**本轮真正的独立文献来源**）

- 检索：Google Patents 查询接口 `patents.google.com/xhr/query`，`q="henry bessemer" before=priority:19000101`，
  **HTTP 200，返回 total_num_results = 36**（这一次查询成功；此后该主机被限流，见 §四）。
- 取回：**逐件**从 `https://patentimages.storage.googleapis.com/pdfs/US<号>.pdf` 下载（35 件全部 HTTP 200），
  用 `pypdf` 读 PDF 文本层，**逐字落盘**。这是一条与 `patents.google.com` **不同的主机**，未被限流。
- 权利：美国政府出版物 + 19 世纪签发 → 公有领域。
- 一手理由：专利说明书是申请人本人具名提交的法律文书，正文第一人称
  `Be it known that I, HENRY BESSEMER, of ...`。**每一份的头部都逐字抄了这一句**（含 OCR 讹字）。

| source_id | 专利号 | 篇名（Google Patents 索引题名） | 签发 | 词 | 署名 |
|---|---|---|---|---|---|
| `src-uspat-us8137` | US 8,137 | Improvement in machines for expressing cane-juice | 1851-06-03 | 3,830 | 独 |
| `src-uspat-us9607` | US 9,607 | Improvement in cane-juice evaporators | 1853-03-08 | 4,596 | 独 |
| `src-uspat-us9608` | US 9,608 | Filter for cane-juice (filtering-drum) | 1853-03-08 | 905 | 独 |
| `src-uspat-us9617` | US 9,617 | Improvement in machines for expressing sugar-cane juice | 1853-03-15 | 3,181 | 独 |
| `src-uspat-us9618` | US 9,618 | Improvement in heaters for sugar-sirup | 1853-03-15 | 712 | 独 |
| `src-uspat-us9681` | US 9,681 | Improvement in sugar-drainers | 1853-04-26 | 3,243 | 独 |
| `src-uspat-us16082` | US 16,082 | Improvement in the manufacture of iron and steel | 1856-11-11 | 5,893 | 独 |
| `src-uspat-us16083` | US 16,083 | Improvement in smelting iron ore | 1856-11-18 | 1,514 | 独 |
| `src-uspat-us49051` | US 49,051 | Improvement in the manufacture of iron and steel | 1865-07-25 | 2,196 | 独 |
| `src-uspat-us49052` | US 49,052 | Improvement in the manufacture of iron and steel | 1865-07-25 | 2,287 | 独 |
| `src-uspat-us49053` | US 49,053 | Improvement in the manufacture of iron and steel | 1865-07-25 | 2,550 | 独 |
| `src-uspat-us49054` | US 49,054 | Improved process of manufacturing axles | 1865-07-25 | 1,788 | 独 |
| `src-uspat-us49055` | US 49,055 | Improvement in machinery for the manufacture of iron and steel | 1865-07-25 | 4,637 | 独 |
| `src-uspat-us51397` | US 51,397 | Improvement in the manufacture of iron and steel | 1865-12-05 | 3,696 | 独 |
| `src-uspat-us51399` | US 51,399 | Improvement in the manufacture of malleable iron and steel | 1865-12-05 | 5,279 | 独 |
| `src-uspat-us51400` | US 51,400 | Improvement in the manufacture of malleable iron and steel | 1865-12-05 | 1,667 | 独 |
| `src-uspat-us51401` | US 51,401 | Improvement in the manufacture of malleable iron and steel | 1865-12-05 | 6,222 | 独 |
| `src-uspat-us94994` | US 94,994 | Improvement in the manufacture of iron and steel | 1869-09-21 | 3,596 | 独 |
| `src-uspat-us94995` | US 94,995 | Improvement in the manufacture of iron and steel | 1869-09-21 | 2,388 | 独 |
| `src-uspat-us94996` | US 94,996 | Improvement in the manufacture of iron and steel | 1869-09-21 | 3,027 | 独 |
| `src-uspat-us100003` | US 100,003 | Improvement in processes and apparatus for the manufacture of iron and steel | 1870-02-22 | 12,942 | 独 |
| `src-uspat-us117246` | US 117,246 | Improvements in working blast-furnaces | 1871-07-25 | 3,032 | 独 |
| `src-uspat-us117247` | US 117,247 | Improvement in furnaces for the manufacture of malleable iron and steel | 1871-07-25 | 7,868 | 独 |
| `src-uspat-us117248` | US 117,248 | Improvement in bessemer converters for converting crude iron into steel | 1871-07-25 | 3,350 | 独 |
| `src-uspat-us117249` | US 117,249 | Improvement in apparatus for melting and casting metals under pressure | 1871-07-25 | 5,799 | 独 |
| `src-uspat-us117250` | US 117,250 | Improvement in the construction and operation of metallurgical furnaces | 1871-07-25 | 5,066 | 独 |
| `src-uspat-us117968` | US 117,968 | Improvement in machinery and buildings for manufacture of iron and steel | 1871-08-15 | 3,044 | 独 |
| `src-uspat-us131561` | US 131,561 | Improvement in the manufacture of artificial stone | 1872-09-24 | 2,118 | **合著** |

`US 131,561` 是与 Frederick Ransome、Ernest Leslie Ransome **三人共同署名**
（`Be it known that we, FREDERICK RANSOME, of Queen-Street Place, HENRY BESSEMER, also of Queen-Street Place...`）。
文件头部写了 `INVENTOR: ... (joint patentees)`。**这一件不能当作他独著的语料引用。**

### 同名验算：36 个候选里剔掉了 7 件（逐件核过署名，不是靠标题猜）

| 剔掉 | 说明书上的真发明人 |
|---|---|
| US 34,961 | SELAH HILER, of Harlem, New York |
| US 67,227 | JOHN BLAKE TARR, of Chicago, Illinois |
| US 86,859 | ORVILLE M. PHILLIPS, of New York |
| US 92,455 | THOMAS W. JOHNSON, of New York |
| US 126,880 | JAMES DOYLE, of New York |
| US 157,175 | WILLIAM M. HENDERSON, of Philadelphia |
| US 604,580 | GEORGE WELTDEN GESNER, of New York |

这 7 件之所以出现在检索结果里，是因为正文提到了 Bessemer 工艺 —— **与他有关，不是他写的**。
（另有 `ES591H1` 是西班牙件，不在美国专利范围，未取。）

### 父子之辨（每一件都验了，不是只验一件）

- 落库的 28 件，说明书上的住址只有两种：
  **Baxter House, Old St. Pancras Road, Middlesex**（1851–1853 六件糖业专利）与
  **Queen Street Place, New Cannon Street, city of London**（1856 年起全部）。
  两者都是**本人**的地址，与他自传里自述的一致。
- 长子（生于 1838）的厂址是 **East Greenwich, Kent**。**28 件里没有一件写这个地址**
  （全库扫 `Greenwich` 只命中一处：US 131,561 里的 **Ernest Leslie Ransome**，不是 Bessemer）。
- 1851–1856 那批的时点上儿子才 13–18 岁。

---

## 四、诚实的缺口

### 4.1 ★ 道数只有 2，没到 3

`archive.org` 与 `patentimages.storage.googleapis.com` 是本轮**实际取到东西**的两条道。
第三条道试过的全部结果如下（本次实测 + PROBE 已实测、按铁律未重试）：

| 通道 | 本轮实测 | 处置 |
|---|---|---|
| `patents.google.com`（网页 + xhr） | **首次 `xhr/query` HTTP 200**（拿到 36 个候选），随后**全部 HTTP 503**，返回页原文：`... but your computer or network may be sending automated queries.` 换过 2 分钟间隔重试 6 次仍 503 | **这是 bot 墙，没有绕**。改走同集团但不同主机的 `patentimages.storage.googleapis.com` 静态对象（HTTP 200），拿到了全部 PDF。**候选清单已在本报告 §三，换台机器可直接续** |
| `www.googleapis.com/books/v1` | 未重试 | PROBE 实测 HTTP 429，`quota_limit_value: "0"`，本机配额为 0，等多久都不恢复 |
| `catalog.hathitrust.org` / `babel.hathitrust.org` | 未重试 | PROBE 实测 403（整站挡爬） |
| `worldwide.espacenet.com` | 未重试 | PROBE 实测 403。**这是英国专利说明书原件拿不到的直接原因** |
| `www.icevirtuallibrary.com` | 未重试 | PROBE 实测 403，且本身订阅制 |
| The Times Digital Archive | **未尝试** | 订阅制付费墙，按铁律不碰。1856-08-14 那期的论文原始报纸印本因此**没有取到** |

→ **本轮的 `channel_count = 2`，达不到 quick 档的 ≥3。**
按[不许因为过不了门而卡住流程]，不为凑数把「同一域名的两个路径」算成两条道，
如实记为**通道受限**，坐标全部写在上表，换一台不被 Google/HathiTrust/Espacenet 挡的机器即可补齐。

### 4.2 没取到的一手材料（都有具体理由，不是没找）

| 材料 | 为什么没有 |
|---|---|
| 1856-08-14《The Times》上论文的**原始报纸印本** | 订阅制付费墙，未尝试。库里的 1856 论文是自传转载（自传 p.163 自陈：`from The Times report of August 14th, 1856, the copy just given is reproduced`） |
| 1856 年 BAAS 年度 Report 里的论文 | DNB 1901 supplement 明说 `His famous British Association paper was excluded from the 'Transactions' of that body` —— **大概率根本不存在这份印本** |
| ICE 1859 论文**原刊全文**及讨论记录 | archive.org 无 1858–59 会期卷；ICE 官方库 403。库里只有自传里的两段摘录 |
| IMechE 1861 论文**原刊全文** | archive.org 上 19 世纪 IMechE 只有 1851 与 1870 两卷，内搜 `"Mr. Bessemer"` 均 0 命中。库里只有自传转载的 pp.144–145 |
| ISI 1886《Some Earlier Forms of Bessemer Converters》、1891《The Manufacture of Continuous Sheets...》 | 两篇篇名只有**儿子的转述**（且他把 ISI 的刊物名写成 `Transactions`，实际是 *Journal*）。**两篇全文一件都没找到** |
| **英国专利说明书原件**（GB 1856 No. 356 等 129+ 件） | Espacenet 403；Google Patents 不收 `GB185600356A` 这种旧编号形式（404）。**一件都没有** |
| 学会讨论席上他开口的段落 | PROBE 在 5 个学会卷册里搜 `"Mr. Bessemer"` 全部 0 命中（且逐卷用必然命中的词自检过通道）。**本轮仍为空**，未新增 |
| 1856 年同时代期刊对论文的**逐字转载** | 实搜过 Scientific American 1856-09-13 / 09-20 / 09-27 / 10-04 四期（archive.org `fulltext/inside.php`，HTTP 200，各有命中）。**四期全部是编辑部自己写的报道与评论，不是他的原文逐字转载**，属二手，**未入库** |

### 4.3 OCR 质量分两档，已在文件头分别声明

| | 质量 | 声明写法 |
|---|---|---|
| 自传（27 份） | **可用**。ABBYY FineReader 产物，讹字零星（`Hbnry` / `Hfe` / `Marcli` / `OP`→`OF` / `280`→`230`） | 头部逐条列出已知讹字，写明**逐字未改**，并写明「**不要把改过讹字的串再当逐字引文用**」 |
| 美国专利（28 份） | **差**。1850s–70s 铅印页的 OCR 严重变形：姓氏被读成 `Bnssnnnn` / `Bnssnlunn` / `BEssEMEE` / `Bassanini` / `misstaan`；专利号被读成 `5L399` / `if @?l?d` / `51h/MDB`；**图纸页的图注被串进正文，阅读顺序是乱的** | 头部写了 `OCR WARNING -- SEVERE`，并明确写：**这些文件用于内容，不要用于逐字引文**；要引就去引 Google Patents 网页或 PDF 页图，**并在答案里说明引的是哪一个** |

---

## 五、复核入口

- 页码↔leaf↔行 三层坐标：每个文件头的 `# LOCATOR:` 行，可直接回 `_djvu.txt` 定位。
- 自传逐字性：把 20 个章文件正文拼起来，应与 `_djvu.txt` 第 611–15070 行的非空行**逐行相同**（11,750 行）。已跑通。
- 专利署名：每个专利文件头的 `# AUTHORSHIP EVIDENCE:` 行是从该件 PDF 文本层里逐字抄的 `Be it known that I, ...` 子句。
- 全库唯一一处人工插入的字：`src-paper-1859-ice` 里那一行 `[[ OMITTED HERE: ... ]]`。**除此之外，raw/ 下没有一个字是我写的。**
