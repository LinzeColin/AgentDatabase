# Public expression

## Scope and assigned sources

**本道分到 2 份（train split）**：

| source_id | 出版年 | tier | 题名 |
|---|---|---|---|
| `src-7ca5e8f31c88` | 1905 | P1 | Life insurance, the abuses and the remedies: an address de…the Commercial Club of Boston |
| `src-2a9bd62fe97c` | 1915 | P1 | Oration |

★ 本节由台账机械导出（`emit_lane_scope.py`），**不含任何阅读判断**；只投影 `split == train` 的行。

## Source-linked observations

### O-1 · 讲话时他**先划定自己举了几个例子**，再给数字

`src-7ca5e8f31c88`（1905）：

> I have referred specifically to only five of the ninety principal American legal reserve companies, five which are closely allied with Wall Street, which on January i, 1905, held 56.

（`January i, 1905` 是 OCR 把 `1` 读成 `i`，**逐字照录不改**。）

**「我只具体讲了九十家里的五家」**——先说射程，再给数。与 writings 的 O-1、O-3 同型：
**先标明这话覆盖多少，再说内容。**

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
