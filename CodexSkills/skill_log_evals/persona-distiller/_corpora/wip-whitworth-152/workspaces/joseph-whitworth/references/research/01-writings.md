# 01 · writings —— Joseph Whitworth 的自著

> 本道全部依据 `train` 分档的来源。引文**逐字照录**，连原文的分号、破折号与
> `on being raised` 这类插入语一起，未做任何整理。

## ★ 先说这一道实际有多少东西（口径在前）

台账 9 条、`usable` 7 条，而**按内容去重后只有 3 部作品**（`check_source_dedup` 实测，虚高 2.333×）：

| 作品 | source_id | 说明 |
|---|---|---|
| 1858《Miscellaneous Papers on Mechanical Subjects》 | `src-dcb590c32cf4`（Oxford 扫描）<br>`src-d70bdcbfcc85`（NYPL 扫描）<br>`src-f801c53b936e`（Wikisource 人工转录） | **三个 id、一部作品** |
| 1854 纽约工业展特别报告 | `src-b779f154d334` | **整篇作附录重印于上一部**（与三个副本重叠 40.4% / 38.4% / 47.9%） |
| 1873《Guns and Steel》 | `src-548b27e71548`（Oxford）<br>`src-7a88f8465ab7`（Harvard） | **两个 id、一部作品** |
| 1868 机械科学奖学金的信与备忘录 | `src-28dfa1d4651c` | 全文 158,877 字符里**只有 8,800 字节（5.5%）是他的** |

★ 另有两份 `tier=U` **不入本道**：`src-b33a177ee07d`（1860 亲笔信，OCR 里他的文字 0 字节）、
`src-86fb98d51ecf`（1855 专利，125 字节全是噪声）。

★★ **取引文一律用 `src-f801c53b936e`（Wikisource 人工校对本）**，两个扫描本满是
`BurfacBj`／`tlie`／`soraetimea` 一类讹字。但该本正文里**混着 Wikisource 自己的许可页脚**
（`This work was published before January 1, 1931, and is in the public domain worldwide…`），
取引文时必须避开——那不是他的话。

★ 另：本份**取不到署名**（`authorship_evidence` 为空）。原因是独立行署名判据的位置护栏——
  署名在 2676 行的第 **1869** 行（**行口径 69.8%**；判据只认文首/文末 10%，防索引误判）。
  **根因是我把 7 个子页拼成一份**，题页位置的语义被暂存方式破坏了，不是判据的错。

---

## 一、他把「平」当成一切的地基，而且给出的是**工序**不是标准件

`src-f801c53b936e` · 1840 年向 British Association 宣读《On Plane Metallic Surfaces, or True Planes》。

开篇他先说旧办法坏在哪：

> The method hitherto adopted[1] in getting up plane surfaces has been (after filing to the straight edge) to grind them together, with emery.

★ 他的替代不是「买一块更准的基准板」，而是**三块互研**——用三个面互相比对，
让误差没有地方藏。这一条在他后面每一篇里都反复出现：
**先把「准」变成可复现的动作，再谈量。**

## 二、量的次序：先有平，才谈得上量

> Next in importance to a true plane is the power of measurement.

`src-f801c53b936e` · 1856 年格拉斯哥 IMechE 会长致辞。

他随即把比长机端出来，而说明的方式是**换感官**：

> The principle is that of employing the sense of touch, instead of sight.

具体到那个零件：

> This thin bar, which I name the gravity piece, is brought into contact with the two planes, so as just to allow it, on being raised, to fall by its gravity; and you will find that, by bringing the planes into closer contact by even the one-millionth of an inch, the gravity piece will be suspended, friction overcoming its gravity.

★ 值得注意的是他**给判据而不是给数字**：「掉不掉下去」是一个任何人当场能复现的二值判断，
不需要读刻度、不需要信任读数的人。这与他在螺纹那篇里的做法同构。

## 三、端面量 vs 刻线量——他给的是可当场验证的对比

> In all cases of fitting, end measures of length should be used, instead of lines.

而理由是**车间里的实测对比**，不是原理推导：用端面基准做到万分之一英寸，
比照两英尺尺上的刻线做到百分之一英寸还容易。

## 四、螺纹：他解决的是**协调问题**，不是技术问题

`src-f801c53b936e` · 1841 年向 Institution of Civil Engineers 宣读
《A Paper on an Uniform System of Screw Threads》。

> Great inconvenience is found to arise from the variety of threads adopted by different manufacturers.

★ 这一篇通篇没有在论证「哪种牙型最优」，而在论证「**各家各自最优等于全行业不通用**」。
他的方案取的是当时通行做法的平均值，不是理论最优——**能被采纳比能被证明更重要**。

## 五、他自己交代的时间与身份（一手，不必外求）

`src-f801c53b936e` · 1858 年版序言：

> during which years I had the honour of being President.

同一段里他逐条说明本书各篇的来历：1854 年纽约报告「has been appended to the other papers」、
1856 年致辞在格拉斯哥、1857 年《Standard Decimal Measures of Length》在曼彻斯特。
**这批论文的年份与场合由他本人在书里写明，不依赖第三方著录。**

## 六、1873《Guns and Steel》——同一套方法搬到另一个领域

`src-548b27e71548` · 标题页署名逐字 `BY SIR JOSEPH WHITWORTH, BART., C.E., F.R.S., LL.D, D.C.L.`，
序言第一句即第一人称：`The following pages give an account of my system of rifled guns`。

## 七、1868 奖学金创设文件（`src-28dfa1d4651c`）

★ **反直觉的一份**：Whitworth Scholarship 的材料通常属污染类（他人写的章程与考卷），
而这一份是**创设的信与备忘录本身、由他署名**——落款逐字
`(Signed) Jos[ep]h Whitworth / Manchester, 4th May, 1868.`（OCR 把 `ph` 读成 `Er`／`i`）。
全卷第一人称密度 9.77/千词是被会刊里别人的第一人称抬起来的，
**他那 8,800 字节单独量是 17.73/千词**。

---

## ★ 本道的缺口（写下来，不用沉默替代）

1. **只有 3 部独立作品**，而 quick 门要 8 份来源。差额不能靠重份补。
2. **三条全文检索通道全被挡**（自己复验过）：`ia-fts.archive.org` HTTP **000**、
   Google Books **429**（报错原文写明是 `Queries per day` **日配额**）、
   HathiTrust **403**（Cloudflare 挑战页）。
   因此他在《The Engineer》《The Times》上的信件、1863 年军械特别委员会的证词、
   IMechE 会刊里他的答辩发言，**本次一条也没查过**——不能据此说「只有这些」。
3. **`conversations` 道在已取语料里是 0**：`Mr. Whitworth said/observed/remarked` 全库 0 次、
   讨论轮次标签 0 次；`newyorkindustria00whit` 里 82 处 `Mr. Whitworth` **全是版口**。
