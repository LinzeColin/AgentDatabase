# Decisions and actions

## Scope and assigned sources

**本道分到 2 份（train split）**：

| source_id | 出版年 | tier | 题名 |
|---|---|---|---|
| `src-9a5ff4e9a5e6` | 1781 | P1 | Reports of Cases determined in the several Courts of Westm…. Cadell; and D. Prince, 1781 |
| `src-b9d9a74b4192` | 1781 | P1 | Reports of Cases determined in the several Courts of Westm…d D. Prince, MDCCLXXXI [1781] |

★ 本节由台账机械导出（`emit_lane_scope.py`），**不含任何阅读判断**；只投影 `split == train` 的行。

## Source-linked observations

★★ **本道不含任何我从正文提取的逐字引文**：本道分到的印本，长 s 被 OCR 读成 `f`（讹字率见 `metrics.longs_corruption`），**取不出可核的逐字串**。下面凡带反引号的字符串，都是**台账 `attribution` 字段里抓源方逐字照录并硬校验过的扉页／首行**，已标明出处；**不是我自己从正文里截的**。一个字都没有改。

1. **判例汇编是他自己编的，身后才刊。** `src-9a5ff4e9a5e6` / `src-b9d9a74b4192`
   台账扉页照录作 `Taken and n by the Hotvurable | Six WILLIAM BLACKSTONE, Knt.`
   （`Six` = OCR 的 `Sir`，`Taken and n` = `Taken and compiled` 被打碎），
   印工 `W. STRAHAN; T. CADELL`，年份 `MDCCLXXXI`（1781）——**他卒于 1780**。

2. **收录跨度自陈在扉页上**：照录作 `From 1746 to 1779`。
   → **三十三年的案子由同一个人挑选、编次**；他 1770 年起在庭上，
   前二十四年是以出庭律师身份记录的。

3. **刊行者是遗嘱执行人**，同一卷首附有其所撰传记（见 03 道对该传记的使用）。
   → **这批材料的编次与取舍出自他本人，而出版决定不是。**


## Candidate Claims

- **clm-bs-dec-01｜他把三十三年的庭上材料按自己的编次整理成一部可查的汇编，
  且这件事贯穿他从出庭到在庭的两个阶段。** 证据：两卷扉页照录 `From 1746 to 1779`＋
  `Taken and compiled by … Blackstone`。
- **clm-bs-dec-02｜汇编的编次是他的，出版不是他的决定**（身后由遗嘱执行人刊行）。
  证据：扉页年份 1781 与卒年 1780 之差；卷首传记的作者身份。


## Contradictions and alternative explanations

- **「他挑了哪些案子」与「他怎么判」是两件事。** 本道扉页层面只能支持前者；
  **后者需要读正文里他自己的判词，而本道印本取不出可核逐字串**（长 s）。
- 汇编里**多数案子不是他判的**（1746–1770 他不在庭上）。
  ★ **不得从「这部汇编是他的」推出「这些判决是他的」。**


## Unknowns and source gaps

- 本道两卷取不出可核的逐字引文，**因此「他的判词长什么样」本道给不出证据**。
- 第一卷内含遗嘱执行人所撰传记（二手），**台账未把它从一手字节里拆出扣除**——
  一手占比的分子因此偏乐观，已记在此。


## Proposed Holdout cases

IDs only; research Agents must not inspect Holdout bodies.

- 用例方向：`case-planning-fidelity-*`、`case-boundary-*`——问到具体某案时，他给不给得出坐标；给不出时怎么说。

## Handoff to adjudication

- 两条候选断言均带 source_id，**证据止于扉页层**。
- ★★ **传给判分侧的红线**：本道**不支持任何关于「他如何判案」的断言**。
  产物里若出现他的判词口吻，那是**没有证据的**，必须删。

