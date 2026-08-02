# 02 · 对话路：书信，以及「谁转录的」这个问题

## 本人书信（P1）

`src-3b2c4ba0103c` —— McGill 大学 Osler 图书馆藏 1790 年
*A Report and Two Letters of Edward Jenner, and a Letter of Mrs Jenner to the Rev. Mr. Ferryman*。

**这一份的 OCR 烂到不像话**，开头是：

> `ie ie + t: 4 FROM BOUND BY MALTHY.O-%F ORD THE LIBRARY`

**但它是真的。** v0.0.0.33 的 `check_corpus_integrity.py` 专门拿它做了一条负对照夹具，
就是为了保证「OCR 差」不会被当成「不是语料」——**那一版抓源里有 4 份是 HTML 错误页，
而这一份不是**。要用它作断言，必须逐段人工校读，不能靠 grep。

## ★ 转录的书信（P2，且必须标明是转录）

`src-7dafc3756d85`（vol.1）／`src-640934253b04`（vol.2）／`src-5b5128447897`
—— John Baron *The Life of Edward Jenner*（1838 增订本）。

Baron 是 Jenner 的**友人兼医师**，书中转录大量原始书信。**但转录本身是二手**：

- 多数原件今已不存，**无从与转录本对校**；
- Baron 有明显的辩护立场（他写这本书时 Jenner 已故，反疫苗争论仍在）。

**裁定**：Baron 卷记 **P2 而非 P1**；凡引其中书信，断言里必须写「据 Baron 转录」。
这条写进了 `meta.json:attribution_basis:disputed_policy`。

> 这正是 Livermore #100 那次的错的同形态：**把编者写的东西当成本人的自陈**。
> 那次是席 E 抓的；这次在研究阶段就先钉住。
