# Conversations and correspondence

## Scope and assigned sources

**本道分到 1 份（train split）**：

| source_id | 出版年 | tier | 题名 |
|---|---|---|---|
| `src-7a97b0ef28fd` | 1920 | P1 | Letters from China and Japan |

★ 本节由台账机械导出（`emit_lane_scope.py`），**不含任何阅读判断**；只投影 `split == train` 的行。

## Source-linked observations

★★ **本道唯一的源是与妻子 Alice 共同署名的书信集**，书里没有逐封署名。
台账 `coauthor_declared` 里按「写信人怎么称呼配偶」切了 112 段：
**John 10,063 词（19.6%）／Alice 5,792 词（11.3%）／归属不了 35,535 词（69.1%）**。
下面每条引文都由 `gen_research.py` 断言**落在 John 那 19.6% 里**；
未判的 69.1% 一个字都没用。

### O-1 · 写信时先报自己的惊讶程度，再给理由

`src-7a97b0ef28fd`（1920，《Letters from China and Japan》）：

> `I can't get over my astonish- ment at the amount and quality of English spoken here; it is about as easy shopping in this store, the big department store, as it is at home — ^much easier as respects attention`

「I can't get over my astonishment at …」——**情绪在前、事实在后**，
与他著作里「先立论后举证」的次序正好相反。判据：私信里他允许自己先说反应。

### O-2 · 细节精确到工具

`src-7a97b0ef28fd`（1920，《Letters from China and Japan》）：

> `Then we had lunch at the store, a regular Japanese Ivmch, which tasted very good, and I ate mine with chop s`

吃的是「a regular Japanese lunch」，而他补了一句**用筷子吃的**。
判据：**记录里带着可核对的具体动作**，不停在「体验很好」这一层。

### O-3 · 用可数的量描述一天

`src-7a97b0ef28fd`（1920，《Letters from China and Japan》）：

> `To-day has been comparatively calm; we have only had four Japanese callers and two America`

「we have only had four Japanese callers and two American ones」——
「今天比较清静」这句判断后面**跟着数字**。判据：主观形容词后面接可数事实。

