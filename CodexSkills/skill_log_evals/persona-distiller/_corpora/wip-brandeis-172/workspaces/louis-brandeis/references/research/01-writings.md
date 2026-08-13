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

1. ★★★ **他的书大量引用他人，第一人称不等于他**。实测 7 条候选里 3 条是被引的第三方：
   - `src-0b710810f1f3`（Muller v. Oregon 那一卷）：「It is gradual and progressive…」
     是**英国皇家外科医学院院长 Sir W. MacCormac 在上议院作证**，被辩状引用；
   - `src-26dbd660239a`：紧接在「In Mr. **Fisher's** own words」之后；
   - `src-26a41d751b61`（《Other people's money》）：是**尤蒂卡审计官 Fred G. Reusswig** 的长段引语。
   ⇒ **每条引文都要回原文看前 700 字。**
2. ★★ `measure_voice` 新加的「多人对话体」检测**抓不到这一类**：
   《Other people's money》的说话人标记只有 **0.09/千词**，而它满是长引语——
   **引号内的引文不带 `Mr. X.` 那种标记**。检测只挡得住听证/庭审那种体裁。
3. `The Right to Privacy`（1890）**与 Samuel D. Warren 合著**，取引文须标明。

## Unknowns and source gaps

- `timeline` 道为空：年表/传记条目按定义不由他署名，`creator:` 检索够不到。
  补它要换 `title:` 检索式，**而那正是同名门失效的那一步**（见 `04-探源分析.md` 第三节）。

---

★★ **本工作区取引文的硬纪律**：他的著作**大量引用他人**，
7 条第一人称候选里 **3 条是被引的第三方**（英国皇家外科医学院院长 MacCormac、
Fisher、尤蒂卡审计官 Reusswig）。**每一条引文都要回原文看前 700 字**，
看它是不是落在引号或「X's own words」之后。
