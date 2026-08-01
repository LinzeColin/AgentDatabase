# 01 · writings（他写的东西）

## 一句话结论

**他一生只出过一本书。** 这不是抽样的结果，是穷尽检索后的事实：
对全部 541 份报纸语料 grep `By Jesse L. Livermore` 命中 6 处，逐条读后**全部是假阳性**
（`managed by` / `statement by` / `engaged by`）；Project Gutenberg 全库检索，
Lefèvre 在册而**他本人 0 条**。

## 唯一的一手著述

《How to Trade in Stocks: The Livermore Formula for Combining Time Element and Price》
（1940，Duell, Sloan & Pearce）。本工作区收录的是**剔除他人前言后的正文**（src-78d1f7f3fb9a），
train 卷 17,444 词，另有一章 4,508 词作 holdout 隔离。归属由版权页
`COPYRIGHT … BY / JESSE … LIVERMORE` 证实（`A-copyright`）。

**该卷的前言不是他写的**，署名 Edward Jerome Dies（src-882ba94037cc），已单独分层为 S1，
只进 external 路。整卷不分作者直接入库，会把 Dies 对他的溢美变成他的自述。

## 书里他自己声明的写作意图（src-78d1f7f3fb9a）

他在开篇写明这本书是给「愿意下功夫、只缺一个路标的人」的，并**预先拒绝了代劳**：
「You cannot wisely read a book on 'How to Keep Fit' and leave the physical exercises
to another.」——记录必须自己记、结论必须自己下，他只负责「light the way」。
这条自我限定在产物里必须保留：**他从不主张自己的方法可以照搬**。

同一章里他把这一点推到更远：「Certain guides which I utilize may be of no value to
anyone else… no guide can be 100% right.」——**他对自己方法的普适性主张是负的**。

## 全书的实际结构（src-78d1f7f3fb9a）

train 卷含五章：I 投机的挑战、II 股票怎样才算走对、VI 百万美元的失误、
VII 三百万美元的利润、IX 记录法细则。**前两章是原则，中两章是他自己的案例，
末章是操作细则**——细则细到「上升趋势栏用黑墨、下跌趋势栏用红墨、其余四栏用铅笔」。

值得注意的是**他明确拒绝图表**：「Personally, charts have never appealed to me.
I think they are altogether too confusing.」而他自己「是记录的狂热者」。
把他归入「技术分析之父」一类的说法与这句原话相抵触，产物中不得沿用。

## 这一路的硬限制

**writings 路只有 1 个来源。** deep 只要求每路 ≥1 源，形式上过得去，
但**写作模型实际建立在单一文本、单一文体、单一年份（1940）上**。
他 1891–1940 年间的交易生涯有 49 年，而这一路的证据只覆盖最后一年的一次总结性写作。
凡涉及「他早年怎么想」的问题，本路提供不了直接证据，只能由 conversations 与 decisions 两路补。
