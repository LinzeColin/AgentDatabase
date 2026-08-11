# External views, criticism, and counterexamples

## Scope and assigned sources

**本道分到 1 份（train split）**：

| source_id | 出版年 | tier | 题名 |
|---|---|---|---|
| `src-8975bb29e982` | 1929 | S1 | The Dissenting Opinions of Mr. Justice Holmes. Arranged wi…ork: The Vanguard Press, 1929 |

★ 本节由台账机械导出（`emit_lane_scope.py`），**不含任何阅读判断**；只投影 `split == train` 的行。

## Source-linked observations

### ★ 这一份是混着两个人的字的（与 #169 Blackstone 同型）

`src-8975bb29e982` 的署名页写着 `Arranged with Introductory Notes , by ALFRED LIEF
With a Foreword by DR. GEORGE W. KIRCHWEY`。**书里至少有三层**：

| 层 | 谁写的 | 能不能当他的话 |
|---|---|---|
| 序（Foreword） | George W. Kirchwey | **不能**——这是外部评价，正是本道要的 |
| 各篇导语与**篇目标题** | Alfred Lief | **不能** |
| 重印的意见正文 | 他本人 | 能，但**它与 05 道是同一批文字，不是第二处证据** |

★ 编者给每篇起的标题（`ON HAMPERING SOCIAL EXPERIMENTS`、`CHILD LABOR BEYOND REACH`、
`POST OFFICE TYRANNY`、`ONE LANGUAGE AT SCHOOL`）**全部是 Lief 的措辞，不是案名**。
**本道只用第一、二层。** 第三层已在台账写 `derived_from`
（见 `_corpus/00-重复源与派生关系.md`），防止把同一批意见算成两处独立证据。

### 同代人怎么定位他（1929 年，他在世时）

1. **不是孤鸣者——编者序自己先把这个印象拆掉。** `src-8975bb29e982`：
   `He is not a voice crying in the wilderness. While he has not hesitated on occasion
   to stand alone, this has rarely been his fate — only once, indeed, in the long period
   covered by this collection`。

2. **★ 这一条能用本工作区的语料独立核。** 同源：
   `the opinions in which he has given expression to the judgment of the court or in which
   he has con¬ curred in its judgment far out-number, in the ratio of eight or ten to one,
   those in which he has felt it necessary to record his dissent`。

   本工作区机械计数（`===` 条目）：多数意见 `src-4daf4f3927bc` 191 则 ＋
   `src-5f7df25e761f` 305 则 ＝ **496**；异议／协同 `src-2bba40c2b8a4` **68** 则。
   **496 ÷ 68 ＝ 7.3∶1**。而本工作区的多数意见语料**不覆盖他任期的全部卷次**，
   异议语料覆盖的卷次范围更宽，**故 7.3 是下界，真值只会更高**——
   与序里说的 8–10∶1 相容。
   → **一条 1929 年的外部断言，用一手语料核过，不是转述。**

3. **同代人已经把「异议者」当成他的公众形象，而编者认为这个形象需要纠正。** 同源：
   `If it should be urged that this collection does not give a fair picture of the fight
   as a whole and that it exhibits the hero with¬ out an antagonist, the answer is that
   Holmes’ warfare was not waged with men but with ideas`。
   → 编者**预先承认自己这本书会造成偏差**，再解释为什么仍这样编。

4. **反面证据：这本书的编法本身就是一种筛选。** 五十五则里 `In seventeen of the
   fifty-five cases here reported the decisions from which he dis¬ sented were reached
   by a bare majority of the court and in twenty others his dissent was shared by
   two of his colleagues`——**37/55 是有人附议的**，
   即「独自反对」这个印象在编者自己给的数里就不成立。

## Candidate Claims

- **C16（fact）**：他的多数／协同意见远多于异议（本工作区计数 ≥7.3∶1），
  「常年异议者」是选编造成的印象。证据：本道第 2、4 条 + 05 道的条目计数（两簇）。
- **C17（lineage）**：他在世时（1929）已被按主题重新编排出版，
  篇目标题出自编者而非案名。证据：第 1 层与篇目表。

## Contradictions and alternative explanations

- **本道只有一份 S1，且它是拥护性的选编**（Vanguard Press，1929）。
  **没有敌意方的材料**——批评他的同代文字本轮一份都没有。
  → 产物里不许写「同代人如何评价他」这种全称句，只能写「这一份选编如何定位他」。
- 第 2 条的计数是**本工作区语料内的计数**，不是他全部判决的统计；
  已在上面注明是下界。**不得改写成「他一生的比例是 7.3∶1」。**

## Unknowns and source gaps

- 缺**批评方**：1905 年 Lochner 异议、1919 年言论案异议在当时都有公开批评，
  本轮 PD 可得的批评文本一份未取。这是本道最大的缺口，**直接影响 divergence-map 的可信度**。
- 缺**非法律界**的外部视角（报刊、政治评论）。

## Proposed Holdout cases

IDs only; research Agents must not inspect Holdout bodies.

## Handoff to adjudication

C16 交合流（已有两簇）；C17 单簇，按事实陈述记。
**本道要向下游明确交代：外部视角只有一个方向，产物必须写出这个偏斜。**
