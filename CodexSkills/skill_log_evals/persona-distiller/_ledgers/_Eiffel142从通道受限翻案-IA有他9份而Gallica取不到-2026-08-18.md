# Eiffel #142 翻案：Gallica 取不到正文，**archive.org 取得到**（2026-08-18）

## 在此之前记录里写的是什么

同一天早些时候的 `_403不是一种东西-Gallica那条是UA过滤` 里，Eiffel 的结论是：

> Gallica `dc.creator all "Eiffel Gustave"` → 32 条，`Auteur du texte` 且 ≤1930 的 14 条，
> `unblock_todo` 点名的 1907／1910／1911／1913 四部全在（ARK 已记）。
> ★★★ **但 `.texteBrut` 取不到正文**（三种形式返回逐字节相同的 50212 B 网页外壳）⇒ **仍不解锁**。

那一条**只探了 Gallica**。本条是去探**没探过的那一类**
（[[we-need-X-is-a-hypothesis-until-you-fetch-an-X]]、[[named-the-resource-class-then-never-searched-it]]）。

## 实测：archive.org 有他，而且正文真取得到

`creator:("Eiffel, Gustave")` → 9 条，**全部 ≤1930**。逐条下载 `_djvu.txt` 并数法文虚词：

| 年 | 条目 | 词数 | 作品 |
|---:|---|---:|---|
| 1879 | `gri_33125000583548` | 5,301 | Notice sur le pont du Douro |
| 1888 | `TA624282EIF` | 7,028 | Notice sur le viaduc de Garabit（扫本 A） |
| 1888 | `noticesurleviadu00eiff` | 6,480 | 同上（**扫本 B**） |
| 1888 | `lesgrandesconstr00eiff` | 7,443 | Les grandes constructions métalliques |
| 1889 | `TA62428EIF` | 48,645 | Mémoire … projet définitif du Viaduc |
| 1900 | `travauxscientifi00eiff` | 83,778 | Travaux scientifiques（扫本 A） |
| 1900 | `travauxscientif00eiffgoog` | 85,672 | 同上（**扫本 B**） |
| 1900 | `n-0106381-pdf-1-400` | **261,968** | **La tour de trois cents mètres** |
| 1902 | `latoureiffelen1900eiff` | 113,019 | La Tour Eiffel en 1900 |

★ 最后那部 261,968 词的《三百米塔》，其 IA 文件名里含 `bpt6k6542854f` ——
**那是 Gallica 的 ARK**。也就是说：**Gallica 自己给不出的正文，经 IA 转存拿到了。**

## 三条必须剔除的（都是「与他有关 ≠ 他写的」）

- `LLT_1929032001` —— 报纸《La liberté》1929-03-20，只因提到他而命中
- `jstor-1763464` —— `creator=None`，题名就叫「Gustave Eiffel」，是**写他的**
- `cu31924031484201` 1913 —— 法文虚词 **0**，是英文纪念册
- 另记一档：`nasa_techdoc_19930083161`（1905）`creator=Eiffel,` 但是 **NACA 英译本**，
  可作内容源、**不可作声口源**

## 同名护栏：实测有 5 条同名者，其中一条是舞曲乐队

`creator:(Eiffel)` 17 条逐条看署名：本人 11 条；
**同名 5 条 —— `Eiffel 65`（1990 年代意大利舞曲乐队）、`Waltraud Eiffel`、
`Eric VENOT-EIFFEL`、裸 `EIFFEL`**；另 1 条裸 `Eiffel,` 归属待定。
⇒ 收语料一律用 `creator:("Eiffel, Gustave")`，**不许用 `creator:(Eiffel)`**。
`namesake_gate.py` 已按此证据出 `status: ready`（单候选）。

## ★★★ 本节原来写错了 —— 当天就被仓里已有的记录推翻

**原文（已作废）**：「9 份里两对是重扫，如实声明后只剩 7，quick 当场不成立（7 < 8）。」

**实际是 8 部可用，quick 够得着。** 三处错，错法各不相同：

### ① 我把一个被打印截断的标识符当成了真的

1910《La résistance de l'air et l'aviation》我判成「条目里 0 个文件，是空壳」。
我查的是 `EiffelLaRsistanceDeLairEtLaviati` —— **32 字，是我自己 `[:32]` 打印出来的**。
真标识符是 `EiffelLaRsistanceDeLairEtLaviation1910`（尾部有年份）。当场复核：

    截断 id  EiffelLaRsistanceDeLairEtLaviati        文件  0 个
    完整 id  EiffelLaRsistanceDeLairEtLaviation1910  文件 12 个，含 _djvu.txt

而那个 `_djvu.txt` 的文件名是 `Eiffel_-_La_résistance_de_l'air_et_l'aviation,_1910_djvu.txt`
—— **带重音、带逗号、不是标准 `{id}_djvu.txt`**，所以「按 id 拼路径」也取不到它。
★ 这是同一天**第三次**栽在截断/重建字符串上（另两次：《三百米塔》文件名字面含 `[...]`；
按打印结果重建下载路径）。[[filename-matching-is-brittle]]

### ② 这件事仓里今早已经做过，而我没先看

`wip-eiffel-142/PROFILE-决定点.md`（10:21 写的）已经把 **11 个 identifier → 9 部作品 → 可用 8 部**
清点完，并且**当天已实测**取到 1910 那部（429,518 字节 / 77,462 词，sha256 `72329cd0…`）
与《三百米塔》OCR 正文（1,593,995 字节）。
`namesake-gate.json`（10:17）也已把 **3 个候选收窄到 1 个**。
我又建了一份候选文件重跑一次门 —— **纯重复劳动**。
[[three-times-in-one-day-i-rediscovered-what-the-repo-already-had]]

### ③ 因此结论反过来

    check_corpus_ceiling.verdict(一手 8 / 总 8 / 道 3, "quick") → **够得着**
    standard 要 24、deep 要 45 —— 两档都不可能，按可得性选 quick（㉞ 已裁）

**但「不许把重扫本拆成两源去凑数」这条仍然成立且更要紧**：
可用 8 部**一部都不能再丢**，而 `min_sources` 正好是 8。
今天同一批实测里，Bismarck / Jefferson / Machiavelli / Kant / Lincoln
**五个工作区全部报 `corpus.undeclared-duplicate-sources`** ——
语料一回到盘上，这道门就红，说明抓源那步从来没给重扫本声明过 `derived_from`。

## 未做完（下一步）

- 语料尚未落盘到 `workspaces/gustave-eiffel/raw/`（下载进程被同一台主机的并发拖住）
- 落盘后按 `--derived-from` 声明 Garabit（`TA624282EIF` ↔ `noticesurleviadu00eiff`）
  与 Travaux（`travauxscientifi00eiff` ↔ `travauxscientif00eiffgoog`）两对重扫
- **声口这一项在法文语料上量不出来**（`check_first_person_density` 只认英文锚点，
  今早实测它正确地返回 `null` 而不是 `0`）—— 判决书里要如实写「未量」，
  不许当成「够」也不许当成「不够」
