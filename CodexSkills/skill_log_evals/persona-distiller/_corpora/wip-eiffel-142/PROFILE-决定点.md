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
| 1900 | La Tour de 300 Mètres（图版与正文） | `n-0106381-pdf-1-400` | 待测 |
| 1902 | La Tour Eiffel en 1900 | `latoureiffelen1900eiff` | 790,986 |
| 1910 | **La résistance de l'air et l'aviation** | `EiffelLaRsistanceDeLairEtLaviation19` | 待测 |

**11 个 identifier → 9 部作品 → 可用 8 部。**
Garabit 与 Travaux 各有两个 id，**同一部作品的多个副本只算一部**
（「两个 source_id 不等于两处证据」）。

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
