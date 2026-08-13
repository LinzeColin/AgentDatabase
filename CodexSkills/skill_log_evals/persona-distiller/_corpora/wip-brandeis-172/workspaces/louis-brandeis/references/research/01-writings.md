# Writings and systematic works

## Scope and assigned sources

**本道分到 21 份（train split）**：

| source_id | 出版年 | tier | 题名 |
|---|---|---|---|
| `src-663cb6829ba6` | 1887 | P1 | Notes |
| `src-7c7b306a7231` | 1889 | P1 | The Law of Ponds |
| `src-26dbd660239a` | 1890 | P1 | Notes |
| `src-e6750d32440f` | 1890 | P1 | The Right to Privacy |
| `src-ea2c7920700d` | 1905 | P1 | Life insurance: the abuses and the remedies |
| `src-5aaf9a59012e` | 1907 | P1 | Savings insurance |
| `src-76811a9c2362` | 1909 | P1 | Massachusetts Savings-Bank Insurance and Pension System |
| `src-04857426d8e2` | 1911 | P1 | Scientific management and railroads [microform] : being pa…nterstate commerce commission |
| `src-696d2c185f7d` | 1912 | P1 | Scientific management and railroads; being part of a brief…nterstate commerce commission |
| `src-dc08306e597b` | 1912 | P1 | Scientific management and railroads; being part of a brief…nterstate commerce commission |
| `src-26a41d751b61` | 1914 | P1 | Other people's money : and how the bankers use it  |
| `src-3d16531d4151` | 1914 | P1 | Business--a profession  |
| `src-652aa149475b` | 1914 | P1 | Other people's money : and how the bankers use it  |
| `src-75ebbbaa5e10` | 1914 | P1 | Other people's money, and how the bankers use it |
| `src-f262a6c0fb76` | 1914 | P1 | Business--a profession |
| `src-0a5e23fd4921` | 1915 | P1 | Interlocking Directorates |
| `src-2ef164245cdd` | 1915 | P1 | The Jewish problem; how to solve it |
| `src-94baf0d4e64a` | 1918 | P1 | The people of the State of New York, respondent, against C…tted on behalf of the people  |
| `src-e6c93e0f739a` | 1918 | P1 | Zionism and patriotism |
| `src-2e8456e43798` | 1919 | P1 | The Jewish problem, how to solve it |
| `src-cc33bc7e060b` | 1925 | P1 | Business--a profession, |

★ 本节由台账机械导出（`emit_lane_scope.py`），**不含任何阅读判断**；只投影 `split == train` 的行。

## Source-linked observations

### O-1 · 他给结论时**先申明这是意见，再说必须**

`src-ea2c7920700d`（1905，《Life insurance: the abuses and the remedies》）：

> These in general are the remedies which in my opinion must be adopted to avoid the abuses incident to the life insurance business as now conducted.

**「in my opinion must be adopted」**——把「这是我的判断」与「必须照办」放在同一句里。
判据：他不说「应该考虑」，也不说「显然必须」，而是**标明归属之后再下强断言**。

### O-2 · 谈工会时，他把**赔偿**说成最划算的支出

`src-3d16531d4151`（1914，《Business—a profession》）：

> I can conceive of no expenditure of money by a union which could bring so large a return as the payment of compensation for some wrong actually committed by it.

前文谈的是工会基金可否被追索。**他的答法不是「该不该赔」，是「赔的回报率最高」**——
把一个法律/道德问题换成**可比较的收益问题**。

### O-3 · 对法院的批评带**程度限定**

`src-f262a6c0fb76`（1914，同书）：

> I am inclined to think that there have been rendered in this country many decisions which do unduly restrict the activity of the unions.

**`I am inclined to think`＋`many`＋`unduly`**——三重限定叠在一起。
与 O-1 同型：**先标明这是判断的强度，再给内容。**

## ★ 三件要写下来的

1. ★★★ **他的书大量引用他人，第一人称不等于他**。
   ★ 这一条第一版写的是「7 条候选里 3 条」——**那是抽样看到的，不是全量**。
   把候选放到 14 条、逐条读前 700 字之后，真值是 **14 条里 9 条**（见文末实测口径）。
   ⇒ 与 [[samples-cannot-support-universal-claims]] 同型：先给全量分布，再写比例。
2. ★★ `measure_voice` 新加的「多人对话体」检测**抓不到这一类**：
   《Other people's money》的说话人标记只有 **0.09/千词**，而它满是长引语——
   **引号内的引文不带 `Mr. X.` 那种标记**。检测只挡得住听证/庭审那种体裁。
   （⑤／⑦ 两条机制正是补这个的；⑥ 补的才是听证体。）
3. `The Right to Privacy`（1890）**与 Samuel D. Warren 合著**，取引文须标明。
   ★ 而且这一份里那条第一人称候选**根本不是两人中任一位**——
   是 **Mr. Justice North** 在 Pollard v. Photographic Co. 的判词，落在脚注里。

## Unknowns and source gaps

- `timeline` 道为空：年表/传记条目按定义不由他署名，`creator:` 检索够不到。
  补它要换 `title:` 检索式，**而那正是同名门失效的那一步**（见 `04-探源分析.md` 第三节）。

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
