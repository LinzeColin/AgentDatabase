# Adams #131：开工之前要落实的一件事（2026-08-05）

探测判「开工」，理由是两根支柱。**我逐根去核了，一根站住、一根核不到。**

## ✓ 站住的那根：会长致辞

`probe-adams-131/raw/address_cooperation_1919.txt` 确有其物，**26,033 字符**，首行：

```
COOPERATION
PRESIDENT’S ADDRESS
BY C. A. ADAMS
```

用 `check_first_person_density.py` 实测**这一篇**的第一人称密度 **4.32/万字**——

| | 密度/万字 |
|---|---|
| **Adams 这一篇** | **4.32** |
| Thomson #129 **全语料** | 4.25 |
| Coffin #130 **全语料** | 0.87 |

**一篇文章抵得上 Thomson 的整个语料。** `expression` 道有主力，这一条不必再核。

## ✗ 核不到的那根：「22 条署名逐字发言」

探测报告说只开 11 卷 AIEE Transactions 就点到 22 条署名逐字发言。
**我把留下的 12 个 `*djvu.txt` 逐卷搜过，一条都没找到。**

搜过的形态（**全部 0 命中**）：
`MR. C. A. ADAMS:`／`PRESIDENT ADAMS:`／`MR. ADAMS:`／`C. A. ADAMS:`，
以及宽松的 `(MR|PRESIDENT|PROF|DR).? ?[A-Z]?.? ?ADAMS ?[:：.]`。

这 12 卷里 `Adams` 的实际形态只有三类，**没有一类是发言**：

| 形态 | 实例 | 属于 |
|---|---|---|
| 论文署名 | `STUDY OF THE HEYLAND MACHINE AS MOTOR AND GENERATOR. BY COMFORT A. ADAMS.` | `writings` |
| **页眉** | `ADAMS: HEYLAND MACHINE`／`ADAMS: DESIGN OF INDUCTION MOTORS` | **正是要剔除的那 82 处** |
| 职员／委员会名单 | `PRESIDENT COMFORT A. ADAMS`、`EXECUTIVE COMMITTEE COMFORT A. ADAMS Chairman` | 都不是他的话 |

## 为什么这一条必须先落实

**`conversations` 道是这个人物压过 C. L. Coffin #130 的唯一理由。**
Coffin 三道门全绿、研究门 16→0 全绿，最后仍记延后——
因为 172,138 字符里他自己说的实质的话只有 15 句。
**这一次要在抓源投入之前把这个数落实，而不是判分时才发现。**

已把三种可能发回抓源方，请它给**至少 3 条原文样张**（卷次＋页码＋前后各一句）：

- **(a)** 在没下载的卷里 → 说是哪几卷，去取。
- **(b)** 在这 12 卷里但标签形态不同（OCR 打坏或别的排版）→ 给真实形态，写进抓源判据。
- **(c)** **当时数错了**——把论文署名或名单条目当成了发言 → 照实说，`conversations` 按 0 计。

★ **(c) 不丢人，把它当成 (a) 或 (b) 往下做才丢人。**

## 无论答案是哪一个，这个人物都不算死

`writings`（署名论文，如 Heyland 电机那篇）与 `expression`（会长致辞）**都是硬的**。
若 `conversations` 实为 0，**不是死路，而是要据实缩小用例范围**——
别出那些没有语料支撑的题（这正是 Thomson #129 与 Coffin #130 两次的教训）。

**两种情形都接受，唯一不接受的是数不实。**
