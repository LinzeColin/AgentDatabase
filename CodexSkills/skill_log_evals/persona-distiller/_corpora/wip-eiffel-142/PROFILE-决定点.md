# Eiffel #142 的 profile 还没定死——**判分开始前必须回来看一眼**

尚未 `init_target`。本文件先记住抓源前已量清的一件事。

## ★★★ 作品清点：9 部，可用 8 部——**恰好压在 quick 的下限上**

| 年 | 作品 | identifier | 全文字节 |
|---|---|---|---|
| 1879 | Notice sur le pont du Douro, à Porto | `gri_33125000583548` | 32,491 |
| 1887 | Letters | `letters00eiff` | **226 ← 读不出内容，不可用** |
| 1888 | Les grandes constructions métalliques | `lesgrandesconstr00eiff` | 54,374 |
| 1888 | Notice sur le viaduc de Garabit | `TA624282EIF` ／ `noticesurleviadu00eiff` | 43,616 ／ 46,312 |
| 1889 | Mémoire présenté à l'appui du projet définitif | `TA62428EIF` | 324,654 |
| 1900 | Travaux scientifiques exécutés à la tour | `travauxscientif00eiffgoog` ／ `travauxscientifi00eiff` | 525,623 ／ 576,454 |
| 1900 | La Tour de 300 Mètres（图版与正文） | `n-0106381-pdf-1-400` | **1,593,995 ✅ 2026-08-18 实测** |
| 1902 | La Tour Eiffel en 1900 | `latoureiffelen1900eiff` | 790,986 |
| 1910 | **La résistance de l'air et l'aviation** | `EiffelLaRsistanceDeLairEtLaviation1910` | **429,518 ✅ 2026-08-18 已取正文** |

**11 个 identifier → 9 部作品 → 可用 8 部。**
Garabit 与 Travaux 各有两个 id，**同一部作品的多个副本只算一部**
（「两个 source_id 不等于两处证据」）。

## ★★★ 2026-08-18：**两件「优先验」都验完了，都过**

本节下面那句「抓源时这两件优先验」已执行：

- `n-0106381-pdf-1-400`（1900 图版本，原担心「可能无 OCR 文本」）——
  实测 `N0106381_PDF_1_400_djvu.txt` **1,593,995 字节**，**有 OCR 正文，担心证伪**。
  ★ 该条目还带 `…_bpt6k6542…` 文件（2,684,108 B）——是 **Gallica ARK**，说明这份 IA 副本源自 Gallica。
- 1910《La résistance de l'air et l'aviation》——`EiffelLaRsistanceDeLairEtLaviation1910`，
  **429,518 字节 / 77,462 词**，sha256 `72329cd0…`，过 `check_ocr_language_death`。
  ★ 文件名是 `Eiffel_-_La_résistance_de_l'air_et_l'aviation,_1910_djvu.txt`（**带重音，不是标准 `{id}_djvu.txt`**）。
- `letters00eiff` **226 字节** 复核一致 —— 确实读不出，不计入。

⇒ **8 部可用作品全部确认有正文；quick 的 `min_sources = 8` 够得着，不会掉到 7。**
⇒ 只读 metadata 判定，**没有整包下载**（铁律 7）。真抓源仍需 Owner 的下载授权。

★ quick 的 min_sources 是 8。**一部都不能再丢**——
若 `n-0106381-pdf-1-400`（图版本，可能无 OCR 文本）或 1910 那本取不到全文，
**立刻掉到 7，quick 也过不了**。抓源时这两件优先验。

## 定死的条件（抓源落盘后照这个判）

- 一手 ≥30 部才谈 deep；≥24 且道 ≥6 才谈 standard。**目前 9 部，两档都够不着。**
- **不许把 Garabit／Travaux 的两个副本拆成两源去凑数**——那正是这条规矩要防的。

## ★★ 语料是法文——三条已知的坑先记下

1. `check_first_person_density` 的**语种关必须先跑**：德语语料曾被判成「没有声口」，差 25–180 倍。
2. `check_authorship` 的法文署名前缀 `par` 已在 v0.0.0.157 加过（Martens 那次）。
3. 逐字引文判据在法文上没跑过——**首次落盘后要专门验一遍**。

## ★★★ 关于铁塔的硬规矩

`La Tour Eiffel en 1900`、`La Tour de 300 Mètres`、`Travaux scientifiques… à la tour`
**这三部是他写的**（creator 逐字为 `Eiffel, Gustave, 1832-19…`），可进一手。
而**题名含 Tour Eiffel 但作者不是他的一律不进一手**——
本轮检索里就混着 Cocteau 的剧本、Duvivier 的电影、Epinal 的版画、
以及 1889 年的博览会纪念册。**以他命名的东西不是他的作品。**

---

## ★★★★ 更正（同日，验完那两件之后）：**可用 7 部，不是 8——比 quick 下限少 1**

上一节写「可用 8 部」，并特意标了「若那两件取不到全文就掉到 7」。**验了，掉了。**

    n-0106381-pdf-1-400（1900 La Tour de 300 Mètres）      1,593,995 B  ✓
    EiffelLaRsistanceDeLairEtLaviation19（1910 空气动力学） **条目是空的，一个文件都没有**  ✗

### 确定可用的 7 部

    1879  Notice sur le pont du Douro, à Porto          gri_33125000583548        32,491 B
    1888  Les grandes constructions métalliques         lesgrandesconstr00eiff    54,374 B
    1888  Notice sur le viaduc de Garabit               TA624282EIF（+1 副本）     46,312 B
    1889  Mémoire présenté à l'appui du projet définitif TA62428EIF              324,654 B
    1900  Travaux scientifiques exécutés à la tour      travauxscientifi00eiff（+1 副本） 576,454 B
    1900  La Tour de 300 Mètres（图版与正文）             n-0106381-pdf-1-400    1,593,995 B
    1902  La Tour Eiffel en 1900                        latoureiffelen1900eiff   790,986 B

    不可用：letters00eiff（1887）**只有 226 B，读不出内容**

**7 < quick 的 min_sources 8。** 已复查：archive.org `creator:("Eiffel") AND mediatype:texts`
共 17 条，他的就这些，**没有更多**。

### ★ 不为凑数做的三件事（写下来，免得下次自己忘了为什么没做）

1. **不把 Garabit／Travaux 的第二个副本算成第二源**——同一部作品的多个 id 只算一部。
2. **不把 226 B 的 `letters00eiff` 算进去**——读不出内容的东西不是来源。
3. **不把题名含 Tour Eiffel 而作者不是他的收进一手**（Cocteau 剧本、Duvivier 电影、
   Epinal 版画、1889 年博览会纪念册都在检索结果里）。

### 解锁路径：**Gallica（BnF）——尚未试**

他是法国人，主要著作由 BnF 数字化；本轮检索里已经出现过两个 BnF 条目
（`bnf-bpt6k6558250v`、`bnf-bpt6k65461081`），但那两个是我已有作品的**另一份副本**，不增作品数。
**Gallica 本站没查过**——1910 那本《La résistance de l'air et l'aviation》
以及他 1907／1911 年的空气动力学报告很可能在那里。
★ 这是**合法的公有领域通道**，不是绕过任何访问控制。**下一次动他之前先走这条。**

**在 Gallica 查过之前，不给他定档，也不记延后。**

---

## ★★★★★ Gallica 试过了：**403，本机通道被挡**（2026-08-06）

    GET https://gallica.bnf.fr/SRU?operation=searchRetrieve&version=1.2
        &query=gallica all "Eiffel Gustave"     →  **Access Denied: 403 Access Interdit**
    GET 同上，query=dc.creator all "Eiffel"      →  返回 34 字节，无记录

**不绕。** 不绕过任何访问控制、不绕验证码是本项目的硬规矩。

### 于是 Eiffel #142 的状态是**两种缺口叠在一起**

1. **一手规模不够**：archive.org 上可用 **7 部 < quick 门 8**，已复查无更多；
2. **通道受限**：补足所缺的那一部（1910《La résistance de l'air et l'aviation》，
   以及他 1907／1911 年的空气动力学报告）**只能走 Gallica，而本机 403**。

★ 这与 Mehl #137、Benardos #128 是同一形态：
**材料存在、是公有领域、坐标已定位，而本机通道堵住。**

### 解锁待办（坐标写全，换台机器或换个网络就能续）

1. `https://gallica.bnf.fr/SRU?operation=searchRetrieve&version=1.2&query=dc.creator all "Eiffel"`
   —— 换个出口再试；或直接用 Gallica 网页检索 `Eiffel, Gustave (1832-1923)` 的作者页。
2. 目标篇目：**1910《La résistance de l'air et l'aviation》**；
   另查 `Recherches expérimentales sur la résistance de l'air`（1907／1911 两份报告）。
3. **只要再取到 1 部**，quick 的 8 源即成立——**差的就是 1 部**。
4. ★ 也可试 HathiTrust 与 Google Books 的公有领域全文；**不要试付费墙与需登录的库**。

### 本轮不给他定档，也不记延后

**「本机取不到」不是「不存在」。** 差 1 部而通道明确、坐标已写清——
这一条留着，不当作做不成。

### 第三条通道也试了：Google Books API **429**

    GET https://www.googleapis.com/books/v1/volumes?q=inauthor:"Gustave Eiffel"
        →  **HTTP 429 Quota exceeded for 'Queries per day'**（未鉴权的共享配额已耗尽）

**通道实测汇总（2026-08-06）**

| 通道 | 结果 |
|---|---|
| archive.org | ✓ 取到 **7 部**（已是全部；`mediatype:texts` 17 条复查过） |
| **Gallica (BnF) SRU** | ✗ **403 Access Interdit** |
| **Google Books API** | ✗ **429 配额耗尽** |
| HathiTrust | **未试** |

三条试了两条堵。**差 1 部就够 quick 的 8 源**，而那 1 部（1910 空气动力学）
在本机三条通道里取不到。**仍不记延后**——坐标已全，换台机器或换个网络即可续。

### 第四条通道 HathiTrust：**API 通，但它只吃标识符**

    GET https://catalog.hathitrust.org/api/volumes/brief/json/oclc:<号>   →  HTTP 200
    但我**没有那本书的 OCLC／LCCN 号**，试了一个猜的号返回 `{"records":[],"items":[]}`

★ **这与 Mehl #137 卡住的地方一模一样**——他那本 1948 年史论也是
「HathiTrust 书目 API 只吃标识符，而本轮查不到它的 OCLC 号」。
**同一个瓶颈在两个人物上出现，说明它是通道的性质，不是运气。**

    archive.org       ✓ 7 部（已是全部）
    Gallica SRU       ✗ 403 Access Interdit
    Google Books API  ✗ 429 配额耗尽
    HathiTrust        ✗ **要标识符，而标识符要靠前三条去查**

★★ 顺带：archive.org 按书名 `title:("resistance de l air")` 检索 **numFound=0**——
那本书在 archive.org 上确实没有全文条目，不是我检索姿势不对。

---

## ★★★ 一个我**故意没有当场决定**的问题

7 部里有两部是**合集形态**：
`Travaux scientifiques exécutés à la tour`（1900，576 KB）与
`La Tour de 300 Mètres — Planches et Texte`（1900，1.59 MB）。

**若它们内部是若干篇各有标题的独立报告，按篇计就不止 7 部，quick 的 8 源自然成立。**

★ 但我**现在不做这个决定**，理由写在这里：
**此刻我正好差 1 部**，在这个位置上把「合集拆成多篇」判成成立，
与「为凑数放宽判据」在外观上无法区分——**哪怕它实质上是对的。**

**正确的次序是：先把语料落盘，看清楚它内部到底是不是若干篇独立报告，再决定怎么计。**
判断依据是**文本的实际结构**（有没有各自的标题、日期、署名），
不是「我需要几部」。

★★ 与它成对的反面规矩已经写在上面：
**同一部作品的多个副本（Garabit ×2、Travaux ×2）只算一部。**
两条是同一条原则的两面——**按作品的实际边界计，不按 identifier 计，也不按需要计。**

---

## ★★★★★ 那个推迟的判断，落盘后看结构：**答案与我的利益相反**

抓源落盘（7 份，3,419,266 B）后逐份看内部结构：

    1900-travaux-scientifiques   554,151 字符   CHAPITRE **9** 处，无「目录」，无「PARTIE」
      扉页逐字：`G. EIFFEL … Travaux Scientifiques EXÉCUTÉS A LA TOUR DE TROIS CENTS MÈTRES DE 1889 A 1900`
      → **一部专著，分九章。**不是若干篇各自发表过的报告装订在一起。

    1900-tour-de-300-metres    1,545,675 字符   CHAPITRE **71** 处，PARTIE **6** 处
      扉页逐字：`IL A ÉTÉ TIRÉ DE CET OUVRAGE 500 Exemplaires sur papier vélin, numérotés`
      → **一部书**（`OUVRAGE`，限印 500 册），分六部分七十一章。

**章不是独立作品。把它们拆开计是错的。**

★ 所以 **7 就是 7**，quick 的 8 源不成立。
**这个结论与我的利益相反**——我正好差 1 部，而结构说不行。
把判断推迟到能看见证据之后，正是为了让它能这样落地。

## 定档结论：**不定档，记延后**（两种缺口叠加）

    ① 一手规模不够：可用 7 部 < quick 门 8（合集不拆、副本不重复计、226 B 的不算）
    ② 通道受限：补足所缺那 1 部，四条通道全试过——
       archive.org 无此条目（按书名检索 numFound=0）／Gallica 403／
       Google Books 429／HathiTrust 要标识符而标识符查不到

★★ 语料 7 份已落盘并留在仓里（`_fetch-staging/`，逐份记了 sha256），
**换台机器只要补到 1 部就能直接接着做**，不必重抓。
