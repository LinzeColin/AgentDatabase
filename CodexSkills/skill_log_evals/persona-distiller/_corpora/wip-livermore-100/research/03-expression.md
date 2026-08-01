# 03 · expression（语体）

## 证据基础与它的单点风险

本路的可用证据是：那本书的正文（src-78d1f7f3fb9a，17,444 词，1940 年，书面语）
加上 28 条口头直引（约 620 词，1908–1940）。
**按 RUNBOOK 的分层规则，第三人称叙述体不进 expression 路**——
527 份报纸对他的报道写的是记者的语体，不是他的。
所以这一路**97% 的字数来自同一本书、同一年、同一文体**。

## 书面语体的可观察特征（src-78d1f7f3fb9a）

**第二人称直呼读者。** 全书大量使用 "you"：「Let me warn you」「Don't let the stock
go stale on you」「have the courage of your convictions and stay with it」。
他不写论文体，写的是**对着一个具体的人讲话**。

**先立警告再给方法。** 开篇第一段就是排除法：「it is not a game for the stupid,
the mentally lazy, the man of inferior emotional balance, nor for the
get-rich-quick adventurer. They will die poor.」——**劝退在前，方法在后**。

**用具体价位演算，不用抽象符号。** 讲加仓讲的是「a stock is selling around \$25.00…
wait until it makes a new high, say around \$30.00」；讲正常回撤讲的是
「Take a stock that starts at 50… it might gradually sell up to 54」。
**他的说明单位是价位与股数，不是公式。**

**短断言收尾。** 长段落之后常以一句极短的话收口：
「Markets are never wrong—opinions often are.」
「Profits always take care of themselves, but losses never do.」
这类句子在书中是**结论位**，不是标题。

**自陈失败时不加缓冲。** 「I almost want to turn my face away in embarrassment when
I tell this.」「I became disgusted with myself.」「I have long since learned…
not to make excuses when wrong.」

## 口头语体（14 份来源的 28 条直引）

比书面更短、更直接，且**多为对提问的正面回答**：
「I am not a gambler. I am a speculative investor.」（src-6249b3b2fda8）、
「It was bad judgment.」（src-b6b01f04cda0）、
「Gentlemen, I have paid them.」（src-995ce3754fc9）。
**书面语体有铺陈，口头语体几乎没有。**

## ⚠ 一条必须写死的排除

网上流传的绝大多数「Livermore 语录」出自 **Edwin Lefèvre 1923 年的小说**
《Reminiscences of a Stock Operator》，主角 **Larry Livingston 是虚构人物**。
该书 112,180 词，是他全部存世文字（约 22,500 词）的 **5 倍**——
**这就是误引占压倒多数的结构性原因**。
实测：他本人那本专著里 `Lefevre`／`Livingston` 出现 **0 次**。
**任何来自该小说的句子都不得作为他的语体样本。**

## ⚠ OCR 状况

那本书的扫描件含 **1284 个西里尔同形字 / 280 个「全同形字词」**
（`ТО`=TO、`Ву`=By、连 `1940` 都被认成 `1040`）。
**取逐字引文前必须跑 `check_ocr_homoglyphs.py`**，并避开脏段落——
第 VI、VII、IX 章的 OCR 质量明显低于第 I、II 章。
