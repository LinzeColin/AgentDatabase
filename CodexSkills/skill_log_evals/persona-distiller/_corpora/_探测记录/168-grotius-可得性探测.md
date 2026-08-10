# Hugo Grotius —— 开工前探测

- 日期：2026-08-11
- 目标人物：Hugo Grotius / Huig (Hugo) de Groot，1583-04-10 Delft — 1645-08-28 Rostock
- 公有领域分界：**出版于 1930 年及以前**（2026 年分界 = 1931）
- 并发：1（全程串行 curl，未花任何 API 费用）
- 本仓（`~/Documents/Codex/GithubProject/`）**未写入任何内容**

## 0. 方法与边界（先说不可信的部分）

| 项 | 状态 |
|---|---|
| Wikidata API | 直连可用，**逐条实调** |
| id.loc.gov（LCCN 名称规范档） | 直连可用，**逐条实调** |
| GND（经 hub.culturegraph.org/entityfacts） | 直连可用，**6 条逐条实调** |
| **VIAF** | **HTTP 403，Cloudflare bot 墙**。未绕过。下表 VIAF 号来自 Wikidata 的声明，**我没有独立核实过** |
| lobid.org | 连接失败（HTTP 000），改走 d-nb.info |
| Internet Archive advancedsearch + metadata + download | 可用，**下载后逐份回读首 200 字节并记 sha256 前 16 位** |
| Project Gutenberg | 可用，4 份全下载并回读版本页 |
| dbnl.org / grotius.huygens.knaw.nl | 可用 |

**没有触碰任何付费墙，没有绕过任何访问控制，没有绕验证码。**

三条我明确标注为「未核实」的：
1. 所有 VIAF 号（通道被墙）。
2. DBNL 上 20 余个题名的**逐条版本年**——我只核了作者页存在与可免费打开，没有逐条开版权页。
3. 1687 年 *Epistolae* 是否 100% 只含他本人所写的信（见 §3.3，有正面证据但不是全量核对）。

---

## 1. 同名场

### 1.1 目标人物本体

| 标识符 | 值 | 是否实调 |
|---|---|---|
| Wikidata | **Q154959** | ✅ |
| LCCN | **n78087113**（`Grotius, Hugo, 1583-1645`） | ✅ id.loc.gov |
| GND | **118542702** | ✅ 返回 `Hugo Grotius`, b=1583-04-10, d=1645-08-28, prof=Jurist/Historiker/Politiker/Theologe |
| ISNI | 0000000121266471 | ⚠️ 仅 Wikidata 声明 |
| VIAF | 32005141 | ❌ **通道被墙，未核实** |

GND 记录里的变体名包含 `Hugo De Groot` / `Hugo DeGroot` / `Xiusi Gelao`（中文转写「格劳秀斯」的拼音回译）。
Wikidata 别名：`Grotius`、`Huig de Groot`、`H. de Groot`、`Huigh de Groot`。

### 1.2 家族同名者 —— 这一族确实不是形式主义

**关键事实：他的父、叔、弟、两个儿子，在国家级规范档里全部带拉丁化的 `Grotius` 形，其中 4 人职业字段是「Jurist」。**

| 人 | 关系 | 生卒 | Wikidata | LCCN | GND（实调） | 规范档里的拉丁名 |
|---|---|---|---|---|---|---|
| **Willem de Groot** | **弟** | 1597-02-10 – 1662-03-12 | Q33129643 | **n82127326** | **128535741** | **`Guilelmus Grotius`／`Wilhelmus Grotius`／`Guillaume Grotius`**，prof=**Jurist** |
| **Pieter de Groot** | **子** | 1615-03-28 – 1678-06-02 | Q2195847 | **n85053983** | **121560252** | **`Petrus Grotius`**，prof=Diplomat; **Jurist** |
| **Cornelis de Groot** | **子** | 1613-02-02 – 1665-10-15 | Q106806196 | —（无） | **136951589** | **`Cornelius Grotius`** |
| **Jan Cornets de Groot** | **父** | 1554 – 1640 | Q2596609 | —（无） | **1011712989** | GND **首选名就是 `Janus de Grotius`**，prof=Politiker; **Jurist**; Bürgermeister |
| **Cornelis de Groot** | **叔**（父之兄） | 1544/46 – 1610-08-05 | Q1133607 | —（无） | **1055674853** | `Cornelius de Groot`，prof=**Jurist** |
| **Hugo de Groot** | **祖父** | 1511 – 1567-04-12 | Q110557854 | 无 | 无 | 别名字面 **`Hugo de Groot`** |
| Hugo Cornets de Groot | 曾孙（Pieter 之子） | 1658 – 1705 | Q110557735 | 无 | 无 | — |
| Maria van Reigersberch | 妻 | 1589 – 1653 | Q2268364 | no2019070814 | 138294844 | — |

两个必须单独强调的：

- **叔父 Cornelis de Groot（1544/46–1610）是莱顿大学罗马法与封建法教授**，四任 rector magnificus，出版《Commentaria ad libros quatuor institutionum Juris Civilis》等**拉丁法学注疏**，Wikidata 别名 `C. Grotius (de Groot)`。荷兰语维基证实他与 Hugo 之父同为 Huych Cornelisz de Groot 之子 → **叔侄关系成立**。一个与目标人物**同姓、同拉丁化姓、同学科、同城、同时代**的法学教授。
- **祖父就叫 Hugo de Groot**（Q110557854，1511–1567）。全名撞车。

### 1.3 非家族同名者（LOC 名称规范档实调）

| LCCN | 规范标目 | 实为何人 | 为什么会混进来 |
|---|---|---|---|
| **nr90009650** | **`Grotius`**（光杆姓，无生卒） | **1775 年美洲小册子 *Pills for the delegates: or The chairman chastised* 的署名**，来源注写明「t.p. (Grotius)」 | 独立战争前夕的**笔名**。按姓氏检索必然命中 |
| **no2021014070** | `Groot, Willem de, active 1728-1765` | **莱顿大学印刷商**，1734 年任 university printer | 变体名字面就是 **`Grotius, Gulielmus`**；题名页作 `Lugduni Batavorum, Typis Wilhelmi de Groot`。**与弟弟 Willem 同名同拉丁形** |
| **n2006001685** | `Groot, Jan de, active 1667` | 17 世纪人物 | 变体名 **`Grotius, Joannes`**；来源注是「**Willem de Groot,《De principiis juris naturalis enchiridion》1667, p.[5] (Joannes Grotii)**」——即他出现在**弟弟的书里** |
| **no2020033024** | `Groot, Jan de, active 1761-1801` | 阿姆斯特丹书商 | 变体 `Groot, Joannes de`，出现在题名页 impressum |
| **n98009764** | `Groot, Hugo de` | **Hugo de Groot（1897–1986），荷兰作曲家、指挥**，VARA 广播乐团指挥 | **全名完全相同**，且 LOC 把他单列为与 n78087113 不同的规范档 |
| **no91013173** | `Groot, Cornelis de` | **生于 1961，莱顿大学商法讲师** | **与叔父同名 + 同学科（法）+ 同校（莱顿）** |
| **n85120873** | `Groot, Pieter de` | 生于 1946，弗里斯兰作者 | 与儿子 Pieter 同名 |
| **n2016069395** | `De Groot, 1880-1933` | David de Groot，英国轻音乐乐队指挥 | 来源注：「**the David was always omitted professionally**」——职业上就只署 `De Groot` |
| Q110769507 | Michiel de Groot（1634–1680） | 荷兰共和国**书商／装订商** | 17 世纪 impressum 里的 `de Groot` 是**出版者**不是作者 |

### 1.4 ★「题名页只印 GROTIUS」会把谁混进来

按姓氏（`Grotius` / `de Groot`）检索 17 世纪版本，**会混入的至少五类**：

1. **弟弟 Willem 的自著法学书**。实测：Internet Archive 有 `bub_gb_djyuDVMmA3gC`，1667 年，题名页字面为
   **`De principiis juris naturalis enchiridion. Auctore Guilielmo Grotio jcto Delphensi`**
   （「代尔夫特法学家 Guilielmus Grotius 著」）。**代尔夫特 + 法学家 + Grotius + 自然法手册**——与 Hugo 的四个识别特征全部重合。
2. **儿子 Cornelis 与 Pieter 作为编者**。实测：IA 的 1658 年 *Annales et historiae de rebus Belgicis* 两份（`bub_gb_Zurwy1gB7GMC`、`bub_gb_d73Ee7BykS0C`）creator 字段字面写着 `Grotius, Hugo; Groot, Cornelius de; Groot, Pieter de; Blaeu, Joan`。1657 年首版题名页作「Ediderunt Cornelius et Petrus Grotius」。
3. **弟弟 Willem 作为编者**。1637 年 *Poemata* 题名页：`collecta et magnam partem nunc primùm edita à fratre Guilielmo Grotio`。
4. **18 世纪莱顿印刷商 Wilhelmus de Groot（Grotius, Gulielmus）** 的 impressum。
5. **父亲 Janus de Grotius / 叔父 C. Grotius** 的法学著作。

**另有一类不靠姓氏、靠机构名混进来**：现代 **Grotius Society**（伦敦，1915 年成立）。实测：IA `creator:(Grotius) AND mediatype:texts` 共 **395** 条，其中 **4 条**（`transactions01/02/05grotuoft`、`publicationstext00unknuoft`，1915/1921）是该学会会刊，**与他本人无关**，且年份 ≤1930，**过年份门**。

---

## 2. 1930 年及以前、可免费全文取得的一手文本

### 2.1 总量与成分（分母写在前面）

Internet Archive `creator:(Grotius) AND mediatype:texts`：

| 口径 | 数 |
|---|---|
| 命中总数 | **395** |
| 其中 `year ≤ 1930` | **368** |
| 其中 `year > 1930` | 23 |
| 无 year 字段 | 4 |

对 395 条按 creator/title 做成分拆分：

| 类别 | 数 | 说明 |
|---|---|---|
| Grotius Society（**根本不是他**） | 4 | 见 §1.4 |
| **他给别人的书做编者／译者** | 45 | Stobaeus、Lucan *Pharsalia*、Manilius、希腊诗选（Dübner-Cougny）、Tacitus、Euripides *Phoenissae*、Viverius *Emblemata amatoria* 等 |
| 余下 | 346 | 含**同一版本的多份重复扫描**（如 1901 Campbell 译本至少 7 份、1916 Magoffin 译本至少 8 份、1853 Whewell 译本至少 16 份） |

**「368 份 ≤1930」这个数不能直接当语料规模用**——去掉学会、去掉他编别人的书、去掉重复扫描之后，**独立版本数远低于此**。我没有做全量去重，所以不给一个精确的「独立一手版本数」。

### 2.2 逐条清单（全部实调；「已下载回读」= 我真的把文件拉下来看过首字节）

图例：**PD 明文** = 页面/元数据上有 public-domain 的明文声明；**仅年份** = 没有明文声明，PD 依据只能是出版年。

#### Mare Liberum（原著 1609）

| # | 篇名 | 出版年 | 版本/译者 | URL | 免费全文 | PD 明文声明 |
|---|---|---|---|---|---|---|
| 1 | *Mare liberum sive De iure quod Batavis competit ad Indicana commercia* | **1618** | 拉丁，Elzevir | `https://archive.org/details/bub_gb_9AutU4aFPyAC` | ✅ djvu.txt 107 KB | ✅ **有**：`licenseurl = creativecommons.org/publicdomain/mark/1.0/` |
| 2 | *The Freedom of the Seas* | **1916** | 英译 R. Van Deman **Magoffin**，Carnegie Endowment / Oxford UP | `https://archive.org/details/freedomofseasorr00grot` | ✅ **已下载回读** 324,441 B | ❌ **无**（仅年份） |
| 3 | 同上（Cornell 扫描） | **1916** | 同上 | `https://archive.org/details/cu31924005221498` | ✅ 283 KB | ❌ 无（仅年份） |
| 4 | 同上（拉丁+英对开） | **1916** | 同上；PG 转录，含 1633 年拉丁底本 | `https://www.gutenberg.org/ebooks/75962` | ✅ **已下载回读** 302,786 B | ❌ **无**——正文内 `public domain` 出现 **0** 次 |
| — | ⚠️ *The freedom of the seas*（Arno Press 重印） | **1972** | — | `https://archive.org/details/freedomofseasorr0000grot` | ❌ **`access-restricted-item = true`**，`inlibrary/printdisabled`，仅借阅 | — **年份也不合格** |

#### De Jure Belli ac Pacis（原著 1625）

| # | 篇名 | 出版年 | 版本/译者 | URL | 免费全文 | PD 明文声明 |
|---|---|---|---|---|---|---|
| 5 | *De jure belli ac pacis libri tres* | **1646** | 拉丁（作者生前末版） | `https://archive.org/details/bub_gb_9GTcjhD3wRgC` | ✅ 2.53 MB | ✅ **有** CC PDM 1.0 |
| 6 | 同上 | **1670** | 拉丁 | `https://archive.org/details/gri_hugonisgroti00grot` | ✅ 2.47 MB | ✅ **有** `NOT_IN_COPYRIGHT` |
| 7 | *The most excellent Hugo Grotius his three books treating of the rights of war & peace* | **1682** | 最早英译 | `https://archive.org/details/mostexcellenthug00grot` | ✅ 2.89 MB | ❌ 无（仅年份） |
| 8 | *On the rights of war and peace* | **1853** | 英译 **Whewell**（节译） | `https://archive.org/details/onrightsofwarpea00grotuoft` | ✅ 1.73 MB | ✅ `NOT_IN_COPYRIGHT` |
| 9 | *The rights of war and peace* | **1901** | 英译 **A. C. Campbell**，导言 David J. Hill | `https://archive.org/details/rightsofwarpeace00grotuoft` | ✅ 1.15 MB | ✅ `NOT_IN_COPYRIGHT` |
| 10 | 同上（PG 转录，Universal Classics Library, M. Walter Dunne） | **1901**（版权页 `COPYRIGHT, 1901`） | 同上 | `https://www.gutenberg.org/ebooks/46564` | ✅ **已下载回读** 1,013,933 B | ❌ **无**——`public domain` 出现 **0** 次 |
| 11 | 1646 年版**照相复制**（Classics of International Law No. 3, Vol. I） | **1913** | 拉丁影印，Kelsey 等 | `https://archive.org/details/hugonisgrottiide00grotuoft` | ✅ 702 KB | ✅ `NOT_IN_COPYRIGHT` |
| 12 | **★ *De Jure Belli ac Pacis*, Vol. II — The Translation** | **1925** | 英译 **Francis W. Kelsey** 等，导言 James Brown Scott，**Oxford: Clarendon Press / Humphrey Milford, 1925**（初版印次） | `https://archive.org/details/dejurebelliacpac013020mbp` | ✅ **已下载回读** 2,972,467 B | ❌ 无（`possible-copyright-status = lendinglibrary_nomatch`，**这不是 PD 声明**） |
| 13 | ⚠️ *The law of war and peace*（同一 Kelsey 译文） | 元数据写 **1925**，**实物是 1962 印次** | Bobbs-Merrill；扫描件自身 OCR 显示 `KZ 2093 .A3 J8813 **1962**`、`Library of Congress Catalog Card Number: 62-20420`，版权页 `COPYRIGHT, 1925` | `https://archive.org/details/lawofwarpeacedej0000grot` | ✅ 已下载回读 2,960,919 B | ❌ 无 |

> **★ 译本年份逐份分清（按你的规则）**：
> - Whewell 译 → `published_at = **1853**` ≤1930 ✅
> - Campbell 译 → `published_at = **1901**` ≤1930 ✅
> - **Kelsey 译 → `published_at = 1925`** ≤1930 ✅（**不是 1625**）
> - 第 13 条：**译文是 1925，但这一份扫描的实物是 1962 印次**。若要严格按「这一份的出版年」记，**它是 1962，不合格**；要用 Kelsey 1925，请用**第 12 条**（Clarendon 1925 初版印次，我已回读版权页确认）。**这是本次探测中最容易被元数据骗过去的一条。**

#### De Veritate Religionis Christianae（原著 1627）

| # | 篇名 | 出版年 | 版本/译者 | URL | 免费全文 | PD 明文声明 |
|---|---|---|---|---|---|---|
| 14 | *De veritate religionis christianae* | **1640** | 拉丁 | `https://archive.org/details/bub_gb_N_rOpPIeLwUC` | ✅ 648 KB | ✅ **有** CC PDM 1.0 |
| 15 | *The truth of the Christian religion, in six books* | **1793** | 英译（Clarke/Le Clerc 系） | `https://archive.org/details/thetruthofthechr00kaftuoft` | ✅ 767 KB | ✅ `NOT_IN_COPYRIGHT` |
| 16 | *Traité de la Vérité de la Religion Chrétienne* | **1797** | 法译 **P. le Jeune**（底本 BnF/Gallica） | `https://www.gutenberg.org/ebooks/15739` | ✅ **已下载回读** 664,701 B | ✅ **有**——文内 `public domain` 出现 7 次 |

（IA 另有 1639/1650/1660/1662/1675/1680/1683/1689/1694/1700/1709/1711/1718/1719/1724/1729/1743/1745/1754/1755/1756/1761/1767/1772/1786/1788 等数十个版本，共 56 条命中，全部 ≤1930。）

#### Annales et Historiae de Rebus Belgicis（1657 遗著）

| # | 篇名 | 出版年 | 版本 | URL | 免费全文 | PD 明文声明 |
|---|---|---|---|---|---|---|
| 17 | *Annales et historiae de rebus Belgicis* | **1658** | 拉丁 | `https://archive.org/details/hugonisgrotiiann00grot` | ✅ 1.63 MB | ❌ 无（仅年份） |
| 18 | *Hugo de Groots Nederlandtsche jaerboeken en historien* | **1681** | 荷译 | `https://archive.org/details/hugodegrootsnede00grot` | ✅ 3.66 MB | ❌ 无（仅年份） |
| — | 1657 首版 | 1657 | 拉丁，**Ediderunt Cornelius et Petrus Grotius** | `https://archive.org/details/annalesethistor00grotgoog` | ✅ | ❌ |

#### 诗作

| # | 篇名 | 出版年 | 版本 | URL | 免费全文 | PD 明文声明 |
|---|---|---|---|---|---|---|
| 19 | *Hugonis Grotij Poemata, collecta ... à fratre Guilielmo Grotio* | **1637** | 拉丁全集，**弟 Willem 编** | `https://archive.org/details/bub_gb_D-T4XTbuclUC` | ✅ **已下载回读** 773,132 B（解码后 768,513 字符） | ✅ **有** CC PDM 1.0 |
| 20 | *Sacra in quibus Adamus exul tragoedia* | **1601** | 拉丁 | `https://archive.org/details/bub_gb_Ioz6RpUdaNoC` | ✅ | — |
| 21 | *The Adamus exul of Grotius* | **1839** | 英译 F. Barham | `https://archive.org/details/adamusexulgroti00grotgoog` | ✅ 128 KB | ✅ `NOT_IN_COPYRIGHT` |

#### 书信

| # | 篇名 | 出版年 | 版本 | URL | 免费全文 | PD 明文声明 |
|---|---|---|---|---|---|---|
| 22 | *Epistolae quotquot reperiri potuerunt* | **1687** | 拉丁，最大的一部信集 | `https://archive.org/details/bub_gb_7cDeih1PbMkC` | ✅ **已下载回读 7,307,604 B**（sha256:16 = `1be9153766c6d7ec`） | ✅ **有** CC PDM 1.0 |
| 23 | *Hugonis Grotii epistolae ineditae ... ad Oxenstiernas* | **1806** | 拉丁 | `https://archive.org/details/hugonisgrotiiepi00grot` | ✅ **已下载回读** 452,671 B（解码后 452,317 字符） | ⚠️ **反向**：`licenseurl = creativecommons.org/licenses/**by-nc-nd/3.0/**` |
| 24 | *Hugonis Grotii ad Ioh. Oxenstiernam ...* | **1829** | 拉丁 | `https://archive.org/details/hugonisgrotiiepi00grot` 系列 / `hugonisgrotiiad00crgoog` | ✅ | — |

> ⚠️ **第 23 条是一个必须记下来的坑**：一份 **1806 年**出版的书，IA 上挂着 **CC BY-NC-ND 3.0**。这是扫描方的声明，**不是权利事实**，而且方向是**比 PD 更严**。结论：**IA 的 `licenseurl` 字段两个方向都不可信**——有的给 PD 标（对），有的给 NC-ND（错）。**PD 依据只能是出版年。**

#### 其他

| # | 篇名 | 出版年 | 版本 | URL | 免费全文 | PD 明文 |
|---|---|---|---|---|---|---|
| 25 | *Traité du Pouvoir du Magistrat Politique sur les choses sacrées*（= *De imperio summarum potestatum circa sacra*） | **1751**（A Londres） | 法译 | `https://www.gutenberg.org/ebooks/14905` | ✅ **已下载回读** 532,393 B | ✅ **有**，`public domain` 出现 2 次 |

### 2.3 ★ 书信集（Briefwisseling）—— 必须单独说明，**它不是 PD 源**

`https://grotius.huygens.knaw.nl/`（实调 HTTP 200）
= *The Correspondence of Hugo Grotius*，eLaborate 平台，覆盖 **1597–1645** 全部年份，17 卷，编者 P.C. Molhuysen、B.L. Meulenbroek、P.P. Witkam、H.J.M. Nellen、C.M. Ridderikhoff。

**可以免费打开，但：**

1. 站点页脚字面写着 **`Version October 2009 © Huygens Instituut – KNAW 2009`** ——**明文版权声明，不是 PD**。
2. 印本卷次跨 1928–2001，**只有第 1 卷落在 ≤1930**；我**没有**从该站核到逐卷年份（`/volumes` 与 `/introductions` 都是 404，只能从 `/parts/introductions` 看到「Volume 1…17」的列表，无年份）。**这一条是未核实项。**
3. 该集**混编双向信件**：年表页字面区分 `Aan …`（他寄出）与 `Van …`（寄给他）。例如 1609 年：`155. Aan D. Heinsius`、`157. Van J. Boreel`。**直接整卷取用会把别人写的信当成他的声口。**

**→ 结论：要 PD 的书信，用 §2.2 第 22/23/24 条（1687 / 1806 / 1829），不要用 Huygens 数字版。**

### 2.4 DBNL（荷兰语作品）

`https://www.dbnl.org/auteurs/auteur.php?id=groo001`（实调 HTTP 200，2.08 MB）
列出 20 余个题名，含 *Bewys van den waren godsdienst*、*Inleidinge tot de Hollandsche rechts-geleerdheid*（2 册）、*Nederduitsche Gedichten*、*Tractaet vande oudtheyt vande Batavische nu Hollandsche republique*、*Christelicke gesanghen*、*Sofompaneas of Josef in 't Hof*、*De dichtwerken van Hugo Grotius* 等。
⚠️ **逐条版本年我没有核**。其中 *De dichtwerken van Hugo Grotius*（`groo001blme02`）显然是 20 世纪学术版，**大概率 >1930**。**用之前必须逐条开版权页。**

---

## 3. 声口密度 —— **这是本次探测最重要的部分**

### 3.1 计数规则与排除账（全部可复跑）

**英文**：只有当 `I` 的**下一个非空白 token 以小写开头**（或本身是 `I'll`/`I've` 缩写）时才算代词；且前一个 token 若是 `book|chapter|chap|cap|sect|vol|lib|art|note|title|psalm|…` 则一律排除。
**拉丁**：只数**无歧义的第一人称代词**（`ego`/`mihi`/`me`/`mecum`/`meus` 全格 + `nos`/`nobis`/`noster` 全格），并加 OCR 容错（长 s→f、c↔e）。**第一人称动词词尾没有数**（无形态分析器，硬凑必然出错）→ **拉丁数字是下界**。

**排除了多少、怎么排的（逐份）：**

| 文本 | `I` 原始 token | 自动排除（罗马数字/标题） | 通过规则 | **再逐条读后**的真实成分 |
|---|---|---|---|---|
| *De Jure Belli* 正文，Campbell 1901 | 114 | 47 | 67 | 引用他人 **49**／漏网的 `I. and II.` 节号 **4**／法律假设句 **13**／**他本人 1** |
| *Prolegomena*，Kelsey 1925 | 64 | 4 | 60 | 引用他人 **11**／OCR 边注 **4**／**他本人 45** |
| *De Jure Belli* 正文，Kelsey 1925 | 2036 | 469 | 1366 | 抽样 45 条读完：OCR 边注 **23**（51%）／引用他人 **10**（22%）／**他本人 12（27%）** |

### 3.2 三个语域的结果

| 语域 | 文本 | 词数（分母） | 他本人的第一人称 | **每千词密度** |
|---|---|---|---|---|
| **论著·序言** | *Prolegomena*，Kelsey 1925 英译 | **12,013** | **45（逐条核实，非抽样）** | **3.75** |
| **论著·正文** | *De Jure Belli* Books I–III，Kelsey 1925 英译 | **426,191** | ≈364（抽样 45 推算） | **0.85**（95% CI **0.44–1.27**） |
| 论著·正文（节译本） | 同上，Campbell 1901 英译 | 153,942 | **1** | **0.007** |
| **书信** | *Epistolae* 1687 拉丁 | **897,032** | 3,870（单数代词，下界） | **4.31** |
| **书信** | *Epistolae ineditae* 1806 拉丁 | **58,701** | 248（单数代词，下界） | **4.23** |
| **诗** | *Poemata* 1637 拉丁，抒情/应景部分 | 44,907 | 344 | **7.66** |
| 诗 | *Poemata* 1637，悲剧部分（*Christus Patiens* 等） | 13,390 | 96 | 7.17 ⚠️ **是剧中人的声口，不是他的** |

### 3.3 四个必须写下来的坑

**① 节译本会把声口整段删掉——这是我本轮最大的一次自我更正。**
我先用 Campbell 1901 量出「16 万词里他本人只说了 **1** 句」，几乎要据此判「份数够但他不说话」。改用 Kelsey 1925 **全译本**复量，同一部书的密度是 **0.85/千词**，差 **130 倍**。原因是可计算的：**Campbell 正文只有 Kelsey 正文的 36% 长度**（153,942 vs 426,191 词），译者自己在脚注里写「The eighth Section is omitted … a discussion no way conducive to that clearness and simplicity — TRANSLATOR」。**Campbell 系统性删掉的正是他自己推理、让步、辩解的段落。**
→ **教训：选译本会决定声口测量的结论。别用节译本量声口。**

**② 序言与正文差 4.4 倍，Campbell 干脆没有序言。**
*Prolegomena* 是他大段自述的地方（「我为什么写这本书」「我如何取材」「我承认从 Gentili 得益」「找出我错处的人，我领受其教」），**45 条逐条核实全部是他本人**。而 **Campbell 1901 完全没有收 Prolegomena**（grep `Prolegom` = 0 命中）。
→ 要他的声口，**Prolegomena 是密度最高的一块，且必须从 Kelsey 1925 取，不能从 Campbell 取**。

**③ Kelsey 版正文的「第一人称」有一半是 OCR 把页边引注冲进正文流。**
抽样 45 条里 **23 条（51%）** 是 `[Livy, VII. xxxi. 4]`、`[On Duties, I x 32.]`、`[Annals, I. lix.]` 这类边注被 OCR 揉进正文，罗马数字 `I` 后面接了小写 OCR 噪声因而过了规则。**不读原文只报比率，会把正文密度高报 3.7 倍。**

**④ 拉丁 OCR 把第一人称标记本身打坏了——「0 命中」不等于「他没说」。**
1687 年 *Epistolae* 的长 s 被读成 f：

| 正确形 | 命中 | OCR 讹形 | 命中 |
|---|---|---|---|
| `esse` | **0** | `effe` | 20 |
| `nostri` | **0** | `noftri` | 188 |
| `sum` | 31 | `fum` | 314 |
| `ego` | 677 | **`cgo`** | **431** |

**`ego` 有 39% 被 OCR 成 `cgo`。** 一个只写 `\bego\b` 的判据会少数 431 次。整册干净 alpha token 占比只有 **0.528**，**部分页面已接近不可读**（1806 年那册 0.569，1637 年 *Poemata* 0.610）。
→ **这三册可以免费拿到、PD 无争议，但 OCR 质量不足以直接做逐字引文。要用得先过 OCR 复核或换更干净的扫描。**

### 3.4 ★ 一个把 ① 和 ③ 接起来的发现

1687 年 *Epistolae* 里 `GROTIO`（与格，「致…Grotius」）出现 **51 次**。逐条读上下文，它们是**他写给自家人的信的抬头**，署名 `H. G.`：

- `GVILIELMO GROTIO, Iurisconsulto, **Mi Frater**` —— 致弟弟 Willem，「我的兄弟」
- `CORNELIO GROTIO … **mi Fili**` —— 致儿子 Cornelis，「我的儿子」
- `PETRO GROTIO` —— 致儿子 Pieter
- `IANO GROTIO` —— 致 Jan

**同名场就长在一手语料内部。** 好消息：这些信是**他写的**（方向正确，且是最私人的语域）；坏消息：**任何按姓氏做归属的自动流程，在这一册里会把四个不同的人和作者本人搅在一起。**
对照 Huygens 数字版则相反——它 `Aan`（寄出）/`Van`（收到）双向混编，**整卷取用会直接把别人的信算成他的**。

---

## 4. 一句话结论

**够做，但必须换掉默认取材路径：语料规模绰绰有余（IA 单是 ≤1930 就有 368 条命中，PD 依据全部是出版年这一条硬事实），声口也真实存在——书信 4.2–4.3/千词、序言 3.75/千词，都远高于「三道门全过而声口不够」那个 0.87/万字 的延后案例；但只要沿用最容易拿到的 Campbell 1901 节译本，测出来就是 0.007/千词，会得出完全相反的、错误的「他不说话」结论。**

**我最没把握的一条**：**Kelsey 1925 正文那个 0.85/千词，是 45 条抽样推出来的，不是全量核实的。**
95% 置信区间 **0.44–1.27**，跨了近 3 倍；而这 45 条里有 51% 是 OCR 边注污染，说明这份文本的信噪比本来就差，抽样比例的估计对样本很敏感。序言那 45 条我是**逐条读完**的（12,013 词全覆盖），书信和诗是**代词全量正则**（不是抽样）——只有正文这一格是抽样。
**若这个判断要承重（例如决定「正文能不能当声口训练材料」），得把 1366 条全读一遍，或换一份 OCR 更干净的 Kelsey 扫描件再量。**

次一级不确定的两条，已在正文标注：① 全部 VIAF 号未独立核实（Cloudflare 403，未绕）；② Briefwisseling 逐卷年份未核到，我只核到「站点自称 © KNAW 2009」这一条足以排除它作为 PD 源。

---

## 附：本目录产物

| 文件 | 内容 |
|---|---|
| `GROTIUS_PROBE.md` | 本报告 |
| `wd.py` / `sparql.py` / `ia.py` / `iameta.py` | Wikidata、SPARQL、IA 检索与元数据取数脚本 |
| `voice.py` / `latin_voice.py` | 英文/拉丁第一人称计数器（含排除账） |
| `classify_jbp.py` / `kelsey_sample.py` | 67 条与 45 条抽样的逐条人工分类（可复跑，断言自校验） |
| `wd_grotius.json` / `wd_family.json` / `wd_family2.json` | 人物标识符原始返回 |
| `ia_*.json` | 各作品 IA 检索结果 |
| `big_meta.json` / `mare_meta.json` | 16+5 条候选的访问状态与许可字段 |
| `v_*.json` | 各文本的声口测量原始输出 |
| `txt/` `pg/` | 已下载并回读的全文（IA 7 份、PG 4 份） |
