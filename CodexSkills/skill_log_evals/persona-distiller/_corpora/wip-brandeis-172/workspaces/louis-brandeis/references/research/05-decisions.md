# Decision records

## Scope and assigned sources

**本道分到 1 份（train split）**：

| source_id | 出版年 | tier | 题名 |
|---|---|---|---|
| `src-0b710810f1f3` | 1908 | P1 | Women in industry; decision of the United States Supreme C…brief for the State of Oregon |

★ 本节由台账机械导出（`emit_lane_scope.py`），**不含任何阅读判断**；只投影 `split == train` 的行。

## ★ 本道**不产生逐字引文**

打开读过：这一卷里的第一人称**几乎全是辩状所引证的权威**，
例如「It is gradual and progressive in its effect…」是
**英国皇家外科医学院院长 Sir W. MacCormac 在上议院作证**的话。

⇒ **这正是「Brandeis Brief」的写法**：用大量他人的社会事实与医学证词立论，
**他自己的话反而少**。要从这一道取他的声口，必须先逐段剔除引证部分——
本轮**不从这一道取引文**，只把它当事实来源。

---

★★ **本工作区取引文的硬纪律** —— 数字是 2026-08-13 跑出来的，不是估的：

    pull_quotes.py --first-person  →  flag_borrowed_voice.py
    writings 候选 14｜**高 9**｜中 1｜无标记 4
    decisions 候选 1｜**高 1**
    conversations / expression / external：**高 0**

**writings 道 14 条第一人称候选里 9 条不是他**，分四种：
① 尤蒂卡审计官 **Fred G. Reusswig**（3 条，《Other people's money》里一整段长引语）；
② ICC 听证证人 **Henry R. Towne**（3 条，《Scientific management and railroads》）；
③ **Mr. Justice North** 在 Pollard v. Photographic Co. 的判词（1 条，落在脚注里）；
④ Sydney G. **Fisher**（1 条）与一名工厂主的转述（1 条）。
`decisions` 道那 1 条是英国皇家外科医学院院长 **Sir W. MacCormac** 在上议院委员会作证。

★★★ **这五种里有三种，`flag_borrowed_voice.py` 当天才认得**——
本轮开工时它对这 9 条只标出 1 条（**漏 8**）。补进去的三条机制是：
**⑤未闭合引语**（Reusswig／North）、**⑥听证转录的说话人标记**（Towne）、
**⑦引证抬头**（MacCormac —— 「Brandeis Brief」体**整段不打引号**，
靠一行「姓名，职衔：」把下面归给别人，前六条机制一条都够不到）。

⇒ **每一条引文仍要回原文看前 700 字**。工具补完之后也一样：
上面那 9 条是**先用手核出来的**，工具是照着它们补的。
