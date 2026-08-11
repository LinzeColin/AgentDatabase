# External views, criticism, and counterexamples

## Scope and assigned sources

**本道分到 2 份（train split）**：

| source_id | 出版年 | tier | 题名 |
|---|---|---|---|
| `src-cef41ec3ad00` | 1770 | S1 | Letters to the Honourable Mr. Justice Blackstone, concerni… Cadell, M D C C L X X [1770] |
| `src-e7c18380b775` | 1773 | S1 | An Interesting Appendix to Sir William Blackstone's Commen…by R. Bell, MDCCLXXIII [1773] |

★ 本节由台账机械导出（`emit_lane_scope.py`），**不含任何阅读判断**；只投影 `split == train` 的行。

## Source-linked observations

★★ **本道不含任何我从正文提取的逐字引文**：本道分到的印本，长 s 被 OCR 读成 `f`（讹字率见 `metrics.longs_corruption`），**取不出可核的逐字串**。下面凡带反引号的字符串，都是**台账 `attribution` 字段里抓源方逐字照录并硬校验过的扉页／首行**，已标明出处；**不是我自己从正文里截的**。一个字都没有改。

1. **有人以公开信的形式指名向他发难。** `src-cef41ec3ad00` 台账题名照录作
   `Letters to the Honourable Mr. Justice Blackstone, concerni…`，1770 年，
   London: Cadell。→ **称谓是「Mr. Justice」**，与他 1770 年就任普通诉讼法院法官相合。

2. **第二年那场争论被人编成合刊出版。** `src-e7c18380b775` 题名照录作
   `An Interesting Appendix to Sir William Blackstone's Commen…`，1773 年，
   费城 R. Bell 印。→ **争论被第三方打包成商品在北美重印**，
   说明这场争论当时有市场。

3. **两份都是别人写他，不是他写。** 台账 tier 均为 `S1`，`author` 非目标本人。
   → 本道**只用来看「同代人怎么称呼他、就什么事找他」**，不用来提取他的声口。


## Candidate Claims

- **clm-bs-ext-01｜1770 年前后，同代人以「Mr. Justice Blackstone」相称并公开向他致函论辩。**
  证据：`src-cef41ec3ad00` 台账题名照录。
- **clm-bs-ext-02｜围绕《释义》的争论在他生前即被第三方编印成册并在北美重印。**
  证据：`src-e7c18380b775` 台账题名与印工照录（Philadelphia, R. Bell, 1773）。


## Contradictions and alternative explanations

- **两份都出自同一场争论**（对造与题材相同），**在「同代人评价」这一层上它们不是两处独立证据**。
- 北美重印**说明有市场，不说明他本人参与了那次重印**——本道无证据表明他知情或授权。


## Unknowns and source gaps

- 本道两份的长 s 讹字率分别为 **0.9837 / 0.9784**（`metrics.longs_corruption`），
  **取不出任何可核的逐字引文**；上面的字符串全部来自台账照录。
- **同代人对他的评价是褒是贬，本道判不了**：两份都是论辩文，立场先定。


## Proposed Holdout cases

IDs only; research Agents must not inspect Holdout bodies.

- 用例方向：`case-external-*`——区分「他说过的」与「别人说他说过的」。

## Handoff to adjudication

- 两条候选断言均带 source_id，**证据是台账照录的题名与印工，不是正文**。
- ★ 本道**不提供任何声口证据**——判分侧不要用它去核「像不像他说话」。

