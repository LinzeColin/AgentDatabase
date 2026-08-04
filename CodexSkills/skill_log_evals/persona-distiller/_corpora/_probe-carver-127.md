# #127 George Washington Carver 可得性探测：**一手最富的一档，却卡在通道数上**

日期：2026-08-05　状态：**★★★ 三道全部可取，quick 档前置满足 → 可开工（见第十节）**

---

## 一、一句话

**不够开 quick 档，而卡点既不是版权、也不是数量、也不是归属——是通道数。**

```
≥8 份来源        **远超**：35 份 ≤1930 的 PD bulletin
一手占比 ≥0.40   **满**：35/35 = **1.00**（署名逐份核过印本，不是抄编目）
**≥3 道**         **不满**：严格口径（要可机读文本）**只有 1 道**；宽松口径（图像也算）**2 道**
```

## 二、★★ 这次 PD 分界更正，对他的增量是 **0**

v0.0.0.123 把分界从 1929 挪到 1931。**卡佛在 1929 与 1930 两年一份都没出版**：

```
No.39（1927） →→→ 八年空白 →→→ No.40（1935）
```

**所以这条线挪到哪里，对他的一手著述一点差别都没有。**

★ 这是**第二次独立确认**那次更正不是「为凑数放宽判据」：
第一次是 Vavilov（份数从 2 变 4，但 `min_lanes` 照样过不去，仍延后）；
这一次是**连份数都没变**。

★ 唯一确实靠更正才进来的，是 **Merritt 1929 年那本传记**
（*From Captivity to Fame*, Meador, 1929，DocSouth 全文）——
**但那是别人写他的，属 lane 4，不进一手计数。**

## 三、六道的实况

| 道 | 实况 |
|---|---|
| **1 writings** | **有，且过剩**：35 份 PD bulletin，OCR 合计 ≈1,072 KB |
| **★ 2 conversations** | **空。** 1921-01-21 众议院筹款委员会花生关税作证确有其事，但**印本听证的 Schedule G 分册没找到公开全文**（IA 只有 Schedule A/B 的 Part I；HathiTrust 全站 Cloudflare 挡下、**未绕过**） |
| **★ 3 expression（书信）** | **材料在手，但没有文本层。** NAL 特藏 120 封（1933–1950）**免费可看、零 OCR、无 .txt/.pdf**；Smithsonian 那封 1930 手稿信明标 PD，**但手写正文 OCR 一个字没出来**（`_djvu.txt` 仅 1,018 字节，认出的全是信笺抬头的铅印董事名单） |
| 4 external | 有：Merritt 1929 传记 |
| 5 decisions / 6 timeline | 无独立源类，只能从 1/3 派生 |

## 四、★ 探测里几条要单独记住的

### 「与他有关 ≠ 他写的」，这次又出现两处

1. **IA 的「Carver and Tuskegee Weather Data」24 件**（`tuskegee_1929-*` / `tuskegee_1930-*`）——
   读了 1930 年 1 月那份全文：是 **U.S. Weather Bureau Form 1009 合作观测员气象记录**，
   **全文 "Carver" 出现 0 次**，标题里的人名是 IA 的集合级补题。**不计入。**
2. **NAL 那 120 封信**著录写的是「primarily **between**」卡佛与 USDA 三位真菌学家——
   **其中相当部分不是他写的。** 真要用，得逐封定署名。

### ★★ 45 个扫描件 ↔ **39 个不同作品**——「两个 source_id ≠ 两处证据」

- No.31 有 **4 个印次**（1916/1917/1925 与另一次）、No.38 有 2 版、
  No.21 另有杜克扫本（OCR 9,570 vs 9,573 字节，**实为同一文本**）
- 内容层面还有重叠：**No.30 是 No.17 的修订重印**；No.13／No.35／No.43 印本自称
  revised／reprinted；**No.4 是爱荷华科学院论文的重印**

**按文件数报会虚增 15%。** 与既有记录同形（流水线数的是文件，不是作品）。

★★ **但这一半现有工具已经能抓——去核过了，不用新建判据。**
拿 `build_source_ledger.near_duplicates` 对造出来的卡佛式重复实跑：

```
两个印次（正文同、只差版次行）      → containment **1.0**，报出
两个扫描件（差一个句点）            → containment **1.0**，报出
一份真正不同的（Feeding Acorns）    → **不报**（未误报）
```

★ `ocr_variant_pairs` 那条长 s 失效**在这里不适用**——那是 Fraktur＋跨供应商才归零的，
卡佛全是英文 Antiqua、同一条 IA 管线。

**抓不到的是另一半，而那一半文档里早已写明要「叠一层书目判重」**：
**No.30 是 No.17 的修订重印、No.4 是爱荷华科学院论文的重印**——
正文实质不同、内容却重叠，**这是书目层的判断，不是文本相似度能解决的**。

### 印本署名弱的四份

**No.20 印本上根本没有个人署名**，只有试验站名单，卡佛署名是编目所加；
No.6／No.7／No.10 封面同样只有 Station Staff。

### 已验证**不是**他写的（勿混入）

No.22 *Dairying in connection with farming*（Turner, A. A.）、
No.28 *Smudging an orchard…*（Malone, R. E.）。**No.9、No.11 任何站点都没有数字化本，作者未核。**

### `sec105` 不成立，且理由干净

NAL 官网原话：1935 年起他是 USDA 植物真菌学部的 **collaborator**——
**不是联邦雇员**；bulletin 的出版者逐份印着 Tuskegee（私立），
而且 **1935 年晚于全部 35 份 ≤1928 的 bulletin**。
**「与联邦有关」在这里确实不等于联邦职务作品。**

### 生卒：卒年可钉死，生年不许写成确定值

**LC 名称权威档 `n50034776`**：`deathDate = "1943-01-05"`、
**`birthDate = "1864?"`（EDTF，问号即不确定）**。
Wikidata `P569` 带 `circa` 限定符，且引用源是 Famous Birthdays——**弱源，不采用**。
**队列里现有的 `confidence: low` 标注是对的，保持。**

## 五、处置：**先不记延后**——缺口有两条，且两条都不是死局

探测方的原话值得照抄：

> **「这两条任补其一，就够 3 道，quick 档立刻成立。」**

| 缺口 | 性质 | 下一步 |
|---|---|---|
| **lane 2** | **可得性**——目标非常具体：1921 年听证的 **Schedule G 分册** | **窄检索已派出**，只找这一样东西 |
| **lane 3** | **不是可得性，是文本层**——121 封信已经免费可看，**缺的只是 OCR／转录** | 若 lane 2 落空再评估；★★ **但「这批信是 PD」这句话对双向通信没有意义**，见下 |

### ★★★ lane 3 那批信：**在动它之前必须先拆开**

NAL 那 120 封的著录写的是「primarily **between**」卡佛与 USDA 三位真菌学家
（Shear／Stevenson／Jenkins），年份 **1933–1950**。三件事逐封定，不能整批算：

1. **哪几封是他写的、哪几封是写给他的**——「between」意味着两边都有；
2. **写给他的那些是另外三人的作品**，各自卒年决定各自保护期，**不随卡佛一起过期**；
3. **1943 年之后的信不可能是他写的**——他卒于 **1943-01-05**，而这批一直到 1950。

**所以那 121 封不是「121 份 lane 3 一手」，在拆开之前连份数都不知道。**
（已写进 RUNBOOK 的 lane 2/3 那一节。）

★ **所以本人物暂不写进延后名单**——先等那一条窄检索的结果。
**若两条都补不上，再按「可得性不足（很窄的一种）」记延后。**

★★ 未核清单（探测方明写的）：
1921 听证 Schedule G 全文、Bulletin No.9／No.11、`notice1909` 的续展记录、
书信是否曾在 2002-12-31 前正式出版（若有，§303 会顶到 2047）、
`helpforhardtimes00carv` 的归属（LC 著录用**方括号**＝推定）。


---

# 六、★★★ lane 2 找到了：**1921 年听证 Part III，Carver 证词 pp. 2070–2078**

窄检索的结果（**推翻了「Schedule G 分册不存在公开全文」这个前提**）：

```
Part **III** = Schedule F（烟草）+ **Schedule G（农产品与备用条款）** + Schedule H（酒类）
  Tariff Information, 1921: Hearings on General Tariff Revision
  Before the Committee on Ways and Means, House of Representatives
  [Jan. 20-22, 24, 25, 1921]

Google Books id **R2osAAAAMAAJ**　**full view / public domain**，PDF+EPUB，**有 OCR**
底本 Library of Congress 藏本，2007-02-28 数字化（与 Part I 同一批）
```

**Carver 证词位置（出自该卷自己的检索索引，不是推测）**：

```
卷末索引：`Carver, George W., peanut products .. 2070, 2077`
p.2070 标题行：`...CARVER, REPRESENTING THE UNITED PEANUT ASSOCIATION OF AMERICA, TUSKEGEE, ALA.`
命中续至 2072–2077，**p.2078 见签名 `GEO W. CARVER`**
→ 约 **pp. 2070–2078**
```

★ 此前那个死路也查清了：`tariffinformati00meangoog` 是 **Part I（Schedule A/B）**；
而 `tariffinformati02meangoog` **根本不是听证**，是 Tariff Commission 的 Schedule G 报告
（全文实测：`hearing` 0 次、`Carver` 0 次）。**两个都不是。**

## ★★ 但「找到了」不等于「取到了」——**本机三条通道全被挡**

| 通道 | 实况 |
|---|---|
| Google Books 直连 | `books.google.com` curl **一律 403**；连续调用后返回 `google.com/sorry` **验证码挑战** → **已停手，未尝试破解** |
| Google Books API | **429，`quota_limit_value: 0`** —— 本环境永久不可用，不是临时限流 |
| HathiTrust（3 个 `rights: pd` 副本：Cornell／Harvard／UMN） | 全站 Cloudflare「Just a moment…」**403，未绕过**（★ 但 Bib API 正常，`full view` 是从它确认的） |
| archive.org | **Google 的 pt.3–7 扫描件未镜像到 IA**（`source:R2osAAAAMAAJ` 返回 0） |

### ★★★ 我用**第二种工具**独立复核了这两个「挡住」——都是真的，且我没有绕

子代理报的是 `curl` 403。**curl 被挡不等于浏览器也被挡**，所以我用应用内浏览器各开了一次：

| 站 | 浏览器里看到的原文 | 我做了什么 |
|---|---|---|
| `babel.hathitrust.org/cgi/pt?id=coo.31924098378726` | **"Just a moment... Performing security verification / This website uses a security service to protect against malicious bots."** | **停手**。这是访问控制，不绕 |
| `books.google.com/books?id=R2osAAAAMAAJ` | **"Our systems have detected unusual traffic from your computer network. This page checks to see if it's really you sending the requests, and not a robot."** | **停手**。同上 |

**两处都不是 `curl` 的毛病，是真的挡着。** 一次都没有尝试通过。

**所以本条的准确表述是：**

> **lane 2 的材料确实存在、确实是公有领域、确实有 OCR 全文，
> 且已定位到页码——但从本机取不到它的字节。**

★★ **这不是「未核」，也不是「取到了」。** 两者都不许写。
**这是「已核实其存在与权利状态，取用通道未解决」。**

## 七、于是 quick 档的账现在长这样

```
≥8 份来源        **满**（35 份 PD bulletin，archive.org 无限制，可取）
一手占比 ≥0.40   **满**（35/36 ≈ 0.97）
≥3 道            lane 1 ✓可取　**lane 2 已定位但取不到**　lane 4 ✓可取
                 → **能取到的只有 2 道。够不够 3 道，全看 lane 2。**
```

### lane 1 也亲自抽验了一份（**不是转述子代理**）

`archive.org/metadata/CAT31355396`（Bulletin No.31，1916，
*How to grow the peanut, and 105 ways of preparing it for human consumption*）：

```
**`access-restricted-item` 字段不存在** → 无限制
`_djvu.txt` **存在，64,830 字节**
rights：「The contributing institution **believes** that this item is not in copyright」
27 个衍生文件（EPUB / Text PDF / Abbyy GZ 齐全）
```

★★ **那个 64,830 与子代理报的数字逐位相同**——**独立对上了**。

★ 但 rights 那句要照实读：**是「馆方相信」，不是法律认定**。
PD 判据仍然落在**出版年 1916 ≤1930** 这条规则上，不落在馆方的措辞上。

### lane 4 我另外亲自验了一次（**不是转述子代理**）

浏览器打开 `docsouth.unc.edu/neh/merritt/merritt.html`：**正常加载，无任何挑战**。

```
Raleigh H. Merritt, *From Captivity to Fame or The Life of George Washington Carver*
MEADOR PUBLISHING COMPANY, 27 Beach Street, BOSTON, MASSACHUSETTS, **1929**，196 p.
UNC-CH Rare Book Collection 索书号 S417.C3 M4
**Text transcribed by Apex Data Services** —— 是**人工转录**，不是 OCR，约 360K
```

★ **权利要分两层说**（照「开放获取 ≠ 公有领域」那条）：
**1929 年那本书的正文是 PD**（≤1930）；
**DocSouth 那个 2000 年电子版是一项服务**（转录、编码、NEH 资助）。
用的是底下那层 PD 文本；**电子版本身的条款要在真去抓的时候看一眼，不能因为「免费可读」就当成 PD。**

★ **另一条 lane 2 检索仍在跑**（找「他的话当年印在学会会刊／期刊上」那一类）——
若那条找到一件**本机取得到**的，lane 2 就彻底落实，不必依赖 Google Books。

**在那条回来之前，本人物既不入库也不记延后。**

---

# 八、取用性总账（**三道全部亲自验过，不是转述**）

| 道 | 材料 | 本机取得到吗 | 怎么验的 |
|---|---|---|---|
| **1 writings** | 35 份 PD bulletin | **✓ 能** | 抽验 `CAT31355396`：无 `access-restricted-item`、`_djvu.txt` 64,830 字节 |
| **2 conversations** | 1921 听证 Part III，**pp. 2070–2078** | **✗ 不能** | Google 与 HathiTrust **各开一次浏览器，两处都是 bot 墙，当场停手** |
| **4 external** | Merritt 1929 传记 | **✓ 能** | DocSouth 正常加载，人工转录约 360K |

```
**能取到的道数 = 2　　quick 门要 3**
```

★ 所以 Carver 的结论**完全压在 lane 2 上**，而 lane 2 的材料**已经找到、已经定位到页**——
**只是这台机器拿不到。** 这正是新记的第五类：**通道受限，不是没有。**


---

# 九、★★★ 同日再更正：**他那 120 封信可能本来就该算 lane 2，不是 lane 3**

我在第三节把 NAL 那批信记成 **lane 3（expression）**。
去看别人的 `source-ledger.jsonl` 里 lane 2 实际装着什么：

```
Koch      robertkochlette00koch          ← **书信集，在 lane 2**
Virchow   briefe-an-eltern-1907-de       ← **书信，在 lane 2**
Barton    corr-adee-alvey-a-1888-1903 等 ← **通信卷，全在 lane 2**
```

**既有做法里，本人写的书信算 conversations（lane 2）。**
（而**写给他的**归 external —— Virchow 的 `s1-baltzer-briefe-an-virchow-1868` 就是这么归的，
**那正是「与他有关 ≠ 他写的」该有的样子**。）

## 这把卡佛的缺口换了一个形状

| 原来的说法 | 按既有惯例的说法 |
|---|---|
| lane 1 ✓、lane 2 ✗（要 1921 听证）、lane 3 只有图像、lane 4 ✓ | lane 1 ✓、**lane 2 ＝那批信（材料在手，缺文本层）**、lane 4 ✓ |
| **缺一整道** | **三道都有材料，缺的是其中一道的 OCR／转录** |

★★ **所以他的问题不是「找不到第三道」，是「第三道的材料躺在那里没有文字」。**
1921 听证仍然值得要（**它是干净的一手、定位到页**），
但**它不再是唯一的路**。

## ★ 但三件事要先解决，才能真的把那批信当 lane 2 用

1. **零 OCR** —— 145 张 JPEG，无 `.txt`／`.pdf`。这是转录工作量。
2. **著录写的是「primarily _between_」** —— **逐封定谁写的**；写给他的那些归 external，
   且**作者另有保护期**（见第八节前的 RUNBOOK 条目）。
3. **1943 年之后的信不可能是他写的**（卒于 1943-01-05，而这批到 1950）。

**在这三件解决之前，「120 封」既不是 120 份 lane 2，也不是 0 份——是未知。**

## ★ 一处我要自己认下来的

我派出去的那条 lane 2 窄检索，指令里写着
**「不要去找访谈、不要去找口述史、**不要去找通信集**」**——
**那句是基于我刚刚推翻的那个错误概括写的。**

对卡佛这一次影响不大（他的信本来就已知，检索的目标是**另找**一件），
**但那条指令本身的前提是错的，记在这里。**


---

# 十、★★★ lane 2 解决了——**而且就在 archive.org 上，本机取得到**

第二条检索（找「他的话当年印在会刊／期刊上」那一类）交回两件，
**其中第一件把整个局面翻过来了**：

```
identifier  **tariffinformati01meangoog**（archive.org）
出处        Tariff Information, 1921: Hearings before the Committee on Ways and Means,
            House of Representatives, 66th Cong., 3d sess., **Schedule G**
            （Committee Print—**Unrevised**, No. 14）, GPO, 1921
```

## 我自己下下来核过了（**不是转述**）

```
metadata：**possible-copyright-status = NOT_IN_COPYRIGHT**、
          **无 `access-restricted-item`**、1153 页图、PDF＋_djvu.txt＋_hocr_searchtext
_djvu.txt **实际下载 4,328,671 字节**，无任何挑战
```

**证词段约 20,055 字符**，逐字照录（**含 OCR 讹字，一字不改**）：

> `STATEMENT OF MB. GEOEOE W. CABVER, UlTITED PEANUT ASSOCIATIOH OF AMEBIGA, TUSKE6EE, ALA.`
> `The Chairman. All right, Mr. Carver. We will give you 10 minutes.`
> `Mr. Carver. Mr. Chairman, I have been asked by the United Peanut Growers' Association`
> `to tell you something about the possi- bility of the peanut and its possible extension.`

```
**我数到的 `Mr. Carver.` 干净轮次：10**
另有 OCR 讹变体 Cabvbb／Cabveb／Cabvek／Cakveb／Carvbb／Cabyeb／Cabbw
同场委员：Garner（Gabneb）／Hawley／Oldfield（Oldfibld）／Rainey（Rainet）／Carew（Cabew）
```

★ **子代理报的是「39 个轮次」，我数干净形态只有 10。** 差额是 OCR 讹变体。
**报数以我实测的为准：10 个干净轮次 + 约 7 个讹变体。**

★ 这一件也顺带解掉了第六节那个「取不到」：
**这个 IA 件本身就是 Google 的扫描件镜像**（卷首印着 `Google This is a digital copy…`），
**所以 Google Books 挡住的内容，archive.org 这一路是通的。**

## ★★★ 我自己的核验连错三次，而子代理是对的——这一条必须记下来

| 第几次 | 我搜的 | 为什么落空 |
|---|---|---|
| 1 | `STATEMENT OF MR. GEORGE W. CARVER`、`Mr. CARVER.`、`The CHAIRMAN.` | **我照抄了子代理从页图上读到的排印形态**（小型大写字母），而 **OCR 文本里是 `MB. GEOEOE W. CABVER`、`Mr. Carver.`、`The Chairman.`** —— 五条全部 0 命中 |
| 2 | `t.find("Is Mr. Carver in the room")` | **原文里那句中间有换行**；我先前打印时用了 `" ".join(...split())` 归一，**于是照着归一后的样子去 find 原文** |
| 3 | 段落终点取「下一个 `STATEMENT OF M`」 | **它先匹配到了他自己那一行**，段长归零 |

**三次都是我的脚本错，不是材料错。**
**第一次尤其危险：我差点据此宣布「子代理报的东西不存在」。**

★ 规矩：**核 OCR 文本时，先归一空白，并且不要用排印形态去搜——用 OCR 实际吐出来的形态。**

# 十一、quick 档前置：**满足**

```
≥8 份来源       **满**：35 份 bulletin ＋ 3 篇 Iowa Academy 论文 ＋ 3 份 Iowa 站公报 = **41**
一手占比 ≥0.40  **满**：几乎全是一手
**≥3 道**       **满**：lane 1 ✓可取　**lane 2 ✓可取（已亲验）**　lane 4 ✓可取
```

★ 另有 1899 年 Hampton Negro Conference 宣读稿（`reportofhamptonn00hamp_0`, pp.53–55）——
**子代理自己诚实降级了**：那是事先写好当场宣读的论文，不是速记逐字稿，
**严格说在 lane 1／lane 2 之间**。不拿它充 lane 2。

★★ 一条**有价值的负结果**：Iowa Academy 那边**找不到他的发言记录**，
而且是**有据的否定**——该会自己的印本页脚写着 `Read by title and published in Proceedings`，
**即他那篇 1899 年的论文是「以题目宣读」（本人不在场）**。
**这类「有据的否定」比「没找到」值钱得多，记下来免得后人重找。**
