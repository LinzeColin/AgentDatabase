# Benardos #128 → **延后（通道受限）**

日期：2026-08-05　profile：quick　identity：材料建工师

## 门的实测

| quick 门 | 实测 | |
|---|---|---|
| 来源 ≥8 | **20** | ✓ |
| 道 ≥3 | **3**（`writings` 6 / `external` 11 / `timeline` 3） | ✓ |
| **一手占比 ≥0.40** | **6/20 = 30.0%** | **✗ 差 10.0 个百分点** |

tier：P1 6、S2 14（无 P2/S1/U）。mark：HIS-OWN 5、**CO-AUTHORED 1**、THIRD-PARTY 14。
★ 台账 20 行、列数唯一值 9，**我独立复核过**，与抓源方自报一致。

## 延后类别：**通道受限**，不是材料不存在

与 Vavilov #126 同类。**能按号直取全文的只有美国专利，而美国专利已经取全了。**

抓源方把 1886–1892 七卷 *Annual Report of the Commissioner of Patents* 整卷下载，
用容错正则 `B[eoc][nu][ae]r[dcl][o0e][sa]` 逐年 grep（确实抓到讹字：1887 卷印成 `N. De Beuardus`），
命中 0/1/4/1/0/0/0 = **六件，与落盘的六件一一对上。没有第七件美国专利。**

其余一手全部在墙后，`_NOT_FETCHED.txt` 有逐条 URL 与 HTTP 码，**全部未绕过**：
Google Patents 503、Espacenet 403、DEPATISnet 只回 JS 空壳、INPI 403、Gallica 403、
HathiTrust 403、Google Books 429。

**已从扫描件读出号码但取不到全文**：DE 38011（ETZ 1887 p.60 原文）、DE 43650、
DE 46776、DE 53502、DE 67615、CH 1054，以及一件号码待考的德国专利（见下）。

★★ **他的五本俄文小册子（1890–1896）archive.org 全库零命中。
若能取到，一手占比立刻 11/25 = 44.0%，直接过门。**

## 署名判据被实际动用了两次，都改变了结论

1. ETZ 1887 卷**自己的人名索引**印着 `Benardos, v., Schweissverfahren mittels Elektrizität 60, 410, 463`。
   三页全部打开核过：p.57-60 是编辑部 Rundschau、p.410 是新闻短讯、**p.463-471 署 R. Rühlmann**。
   **索引挂在他名下不等于署名。**
2. 《Электричество》1890 № 9-10 那封感谢信，翻到落款是 **Л. И. Полешко**。记 S2。

68 期俄文刊全部 grep 过（含讹字 `Бенардоеа`），13 期提到他，**零篇署名 Н. Н. Бенардосъ**；
发言人标签（`сказалъ`/`заявилъ`）邻近扫描零命中——**`conversations` 这一道确实没有。**

## ★★ 一个比一手占比更要紧、但这次没轮到它说话的问题

六份专利合计 8,823 词、第一人称动词 20 处，**逐处看绝大多数是专利套话**
（`In testimony whereof I have hereunto set my hand`／
`I do not wish to be understood as confining myself to…`／`what I do claim herein…`）。
真正有认知内容的只有一处：

> `an electromagnet, which I have ascertained influences not only the electric arc,
> but also the molten metal`

**一手占比量的是「有多少件是他的」，量不到「他的那些件里有没有他的想法」。**
本次是占比先卡住，所以这一条没轮到它说话；**但补齐俄文小册子之后重启时，
这一条要先问一遍**——否则可能出现「一手门过了、断言层撑不起来」。

## 顺带修掉的一处旧缺陷

抓源方如实报了一处跨语料矛盾（同一件德国专利，Slavyanov 记 43194 / Google 索引记 43174，它没选边）。
去翻 Slavyanov 的扫描原文，**印的是 `Kl. 48» Kr. 48194`——第三个数**，
而那份文件的头部用书名号引着 `Nr. 43194`，**是把 OCR 悄悄改了一位再当逐字引文用**。
已撤回该更正并改为照录。**号码待考，不许在任何断言里当作已知。**

## 恢复条件

**取到他那五本俄文小册子（1890–1896）中的任意两本**，一手占比即达 11/25 = 44.0% 过门。
其次是任一件德国/法国/比利时专利全文。

★ **不放宽 `min_primary_ratio`。** 差 10 个百分点不是「几乎够了」，
而且这一项正是 Slavyanov（8/53）与 Liebig（0.6094 对 deep 0.65）被延后的同一项。
