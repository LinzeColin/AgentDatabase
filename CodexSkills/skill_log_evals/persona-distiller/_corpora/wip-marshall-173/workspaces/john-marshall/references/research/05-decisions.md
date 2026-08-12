# Decisions and judgments

## Scope and assigned sources

**本道分到 12 份（train split）**：

| source_id | 出版年 | tier | 题名 |
|---|---|---|---|
| `src-7930d4b1c287` | 1831 | P1 | Opinion of the Supreme Court of the United States, at Janu…me Court of the United States |
| `src-21deee17627c` | 1840 | P1 | Opinions of the late chief justice of the United States, J…shall, concerning Freemasonry |
| `src-290a5809b40f` | 1903 | P1 | John Marshall, complete constitutional decisions |
| `src-302df088d8b0` | 1903 | P1 | John Marshall : complete constitutional decisions, ed. wit…storical, critical and legal  |
| `src-5e21d3e359e3` | 1903 | P1 | Complete constitutional decisions; |
| `src-8c46f27be355` | 1903 | P1 | John Marshall, complete constitutional decisions, ed. with…istorical, critical and legal |
| `src-923493e0e5a1` | 1903 | P1 | John Marshall, complete constitutional decisions, ed. with…istorical, critical and legal |
| `src-b89805564c5f` | 1903 | P1 | John Marshall, complete constitutional decisions, ed. with…istorical, critical and legal |
| `src-e8724211539e` | 1903 | P1 | John Marshall, complete constitutional decisions |
| `src-73eaf91e64a8` | 1905 | P1 | The constitutional decisions of John Marshall |
| `src-a1079319c6f3` | 1905 | P1 | The constitutional decisions; |
| `src-d54359cf6442` | 1905 | P1 | The constitutional decisions; |

★ 本节由台账机械导出（`emit_lane_scope.py`），**不含任何阅读判断**；只投影 `split == train` 的行。

## Source-linked observations

**口径**：三条均取自 `src-8c46f27be355`（1903，Complete constitutional decisions），
**且逐条核过上下文是判决意见正文、不是编者按语**——
同一批话在另外几个编本里以 `In the present case occurs Marshall's famous dictum: "…"`
的形式出现，**那种是编者在引用他，不能当他的声口用**。

### O-1 · 他先把对方的说法推到荒谬，再说「不过还是要认真想」

> `It is emphatically the province and duty of the judicial department to say what the law is.`
> —— `src-8c46f27be355` @69739（马伯里案）

★ 前一句是 `an absurdity too gross to be insisted on. It shall, however, receive a more attentive consideration.`
**先判它荒谬，再回头认真论证它**——不靠「显然」收场。
与 Jefferson 的 O-2（先说出反方的依据）同一族，**而他多走一步：反方已被驳倒了仍继续论证**。

### O-2 · 他把「这是什么文件」当成解释的前提说出来

> `In considering this question, then, we must never forget that it is a Constitution we are expounding.`
> —— `src-8c46f27be355` @483554（麦卡洛克案）

★ 不是先解释条文，而是**先声明这份文件属于哪一类**，再据此定解释的宽严。

### O-3 · 他用连续分号把一串后果串成一条链

> `That the power to tax involves the power to destroy ;`
> —— `src-8c46f27be355` @523989（麦卡洛克案，OCR 保留了法式空格分号）

★ 原文继续为 `that the power to destroy may defeat and render useless the power to create; that there is a plain repugnance…`
——**同一句法反复三次**，把税权推到与创设权正面冲突。
论证形状是**递推**，不是罗列。
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
