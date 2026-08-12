# Expression and public voice

## Scope and assigned sources

**本道分到 9 份（train split）**：

| source_id | 出版年 | tier | 题名 |
|---|---|---|---|
| `src-32716caed453` | 1842 | P1 | Lincoln's stories and speeches |
| `src-aa53d1f400e4` | 1861 | P1 | Inaugural address of the President of the United States on the fourth of March, 1861 |
| `src-ab69e48d1697` | 1888 | P1 | The Gettysburg speech and other papers |
| `src-51dd7f2ad228` | 1899 | P1 | The Gettysburg speech, and other papers |
| `src-604e07555b56` | 1909 | P1 | ...First and second inaugural addresses, message, July 5, 1861; |
| `src-db8fa016fda1` | 1909 | P1 | ...First and second inaugural addresses, message, July 5, 1861; |
| `src-be0b3ab8adad` | 1911 | P1 | The best of Lincoln : early speeches, Springfield speech, Cooper Union speech, etc. |
| `src-3994ac473078` | 1920 | P1 | Early speeches of Abraham Lincoln, 1830-1860 |
| `src-5067960bb8f2` | 1920 | P1 | The cross of Gettysburg : Lincoln's immortal address in cruciform arrangement |

★ 本节由台账机械导出（`emit_lane_scope.py`），**不含任何阅读判断**；只投影 `split == train` 的行。

## Source-linked observations

### O-1 · 自撰小传的第一句是户籍式的，没有一个形容词

> `I was born, February 12, 1809, in Hardin County, Kentucky.`
> —— `src-32716caed453` @862

★ 这是他应人之请写的自述开头。**没有铺垫、没有自评**，
先给可核的三项：日期、县、州。与 01-writings 的 O-3（先缩小主张射程）同一路数。
★ 引文起点特意从 `I was born` 起算——原文此前是编者的 `Here is the letter:`，
  **那是编者的话，不属于他**。

---

## ★ 跨道重复：第一次就职演说那句在三道里都出现

    01-writings   src-c80788c2eea1 @1492
    03-expression src-aa53d1f400e4 / src-db8fa016fda1
    05-decisions  src-7e649f429905

**同一段文字被不同编本收进不同体裁的册子里**，于是分道时落到三条道。
⇒ **道数不因此变多，证据也不因此变三份。** 断言层只署 01-writings 那一处。

## ★ 本道剔除的两条

- `He forgets himself so entirely in his object…` —— **第三人称评论他**，不是他的话
- `The body of the pamphlet is occupied with a few of the most striking speeches…`
  —— 编者对这本小册子的说明
## Candidate Claims

Pending.

## Contradictions and alternative explanations

Pending.

## Unknowns and source gaps

Pending.

## Proposed Holdout cases

IDs only; research Agents must not inspect Holdout bodies.

## Handoff to adjudication

Pending.
