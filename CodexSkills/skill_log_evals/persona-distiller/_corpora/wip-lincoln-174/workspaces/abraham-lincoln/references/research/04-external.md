# External accounts

## Scope and assigned sources

**本道分到 2 份（train split）**：

| source_id | 出版年 | tier | 题名 |
|---|---|---|---|
| `src-3c98457dd41d` | 1879 | S1 | Anecdotes of Abraham Lincoln and Lincoln's stories : inclu…tories, miscellaneous stories |
| `src-6546cbb74276` | 1923 | S1 | The writings of Abraham Lincoln, Life of Lincoln |

★ 本节由台账机械导出（`emit_lane_scope.py`），**不含任何阅读判断**；只投影 `split == train` 的行。

## Source-linked observations

### 本道**按定义取不到署名引文**，这不是缺口

`external` 装的是「别人怎么看他」，台账里这些源的 `tier` 是 `S1`（二手）。
pull_quotes.py 以 --lane external 跑，返回 **rc=3「一条都没取到」**——
**那是对的**：本项目的引文只署他本人的话，二手材料里的第一人称是别人的。

★ 记这一条是为了防一种误读：
**「这道没有引文」不等于「这道空着」**。它有 2 份源，参与 `min_lanes` 计数，
只是**不产出署名引文**。
（同 [[empty-default-swallows-unknown]]：rc=3 要被读成「按定义如此」，
 而不是「工具坏了」或「材料不够」。）
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
