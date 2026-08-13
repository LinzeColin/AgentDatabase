# Decision records

## Scope and assigned sources

**本道分到 0 份（train split）**：

| source_id | 出版年 | tier | 题名 |
|---|---|---|---|

## 本道为空 —— **不是没抓到，是探源阶段的 11 条全是误配**

抓源前按题名估分布时，`decisions` 报了 **11 条**，逐条打开一看
**全部是《最后的审判》**（西斯廷壁画）：命中的是正则里的 `judgment`。
**画名不是判决记录。** 已在 `assign_lanes` 里加 `ARTWORK_NOT_DECISION` 排除
（射程实测：对存量 37 个工作区一条都不动）。

★ 他的合同、工程账目、教廷委托文书**确实存在**，但不在本轮 IA 池子里
（多在 Archivio Buonarroti、梵蒂冈档案）。**要补这一道得换通道。**

**本道不产生任何断言。**
