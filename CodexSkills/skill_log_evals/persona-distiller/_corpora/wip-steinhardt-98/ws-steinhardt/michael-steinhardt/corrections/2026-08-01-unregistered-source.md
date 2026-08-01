# 订正：两个事实的唯一文本支撑是一份未登记文件（2026-08-01）

`check_claim_coverage.py` 报出装饰性引用后逐条追查，发现两处同源问题。

## 发现

`corpus/ms_xxxx_hedgefundalpha_resource_page.txt` **不在 `source-ledger.jsonl` 里**
（`split=None`、`source_id=None`、`tier=None`），也就是**从未经过 `ingest.py`**——
它没有 split 归属、没有分层、没有过 `check_authorship.py` 的归属门。

而全库范围内，只有它写出这两件事：

| 事实 | 唯一出处 | 处置 |
|---|---|---|
| 父亲名 **Sol**（`his father Sol "Red" Steinhardt`） | 该未登记文件 | **删名**——本条实质不依赖名字 |
| 生日 **Dec. 7, 1940** | 该未登记文件 | **只保留生年** |

生年 `1940` 另有独立支撑：`src-e9b19d42ad9f`（train，S1，
原文 `Born in 1940, Steinhardt grew up in Bensonhurst`），已加为 `clm-10e29f7e7408` 的引源。

语料中其余 `December 7` 全部是巧合——2021 年文物案恰在 12 月 7 日发布，
另有一件文物于 2004 年 12 月 7 日易手。**日期撞车不是来源。**

## 为什么这条值得单独记

被引来源里没有这个实体，而**该实体在语料的别处存在**，
于是「它在语料里」与「被引来源支持它」被混为一谈。
`check_claim_coverage.py` 查的正是后者，它是对的。

**未登记文件躺在 `corpus/` 里仍然会被读到。** 113 份 corpus 文件里只有 55 份进了账本，
其余是抓源池——池子里的东西不该进断言，但没有任何机制拦着。
这条记为下一版候选：**`corpus/` 里未登记的文件应当在目录层面与已登记的分开**，
否则「读得到」和「可引用」之间只隔着执行者的记性。
