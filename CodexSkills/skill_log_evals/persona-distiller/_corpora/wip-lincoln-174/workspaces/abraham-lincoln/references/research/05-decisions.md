# Decisions and judgments

## Scope and assigned sources

**本道分到 5 份（train split）**：

| source_id | 出版年 | tier | 题名 |
|---|---|---|---|
| `src-11166a3889de` | 1863 | P1 | General orders. No. 1. War department, adjutant general's …es of America. A proclamation |
| `src-81327220bc31` | 1864 | P1 | Emancipation proclamation of January 1st, 1864 [sic] |
| `src-244c03202b38` | 1894 | P1 | Abraham Lincoln: Complete Works, comprising his Speeches, …iscellaneous Writings, Vol. I |
| `src-7e649f429905` | 1894 | P1 | Abraham Lincoln; complete works, comprising his speeches, …, and miscellaneous writings; |
| `src-bcceedbd3d14` | 1915 | P1 | Complete works : comprising his speeches, letters, state p…s, and miscellaneous writings |

★ 本节由台账机械导出（`emit_lane_scope.py`），**不含任何阅读判断**；只投影 `split == train` 的行。

## Source-linked observations

### O-1 · 公文里他把「获准入伍」写成对方可执行的条款，而不是恩典

> `And I further declare and make known that such persons, of suitable condition, will be received into th`
> —— `src-81327220bc31` @3763（《解放宣言》）

★ `declare and make known` 是公文套语，而后半句 `will be received into…`
**给的是一条对方可以照着做的安排**，不是宣告态度。
与 01-writings 的 O-2（引旧话来自我设限）放在一起：**他习惯把话说成可核可执行的条款。**

---

## ★ 本道有两条**是他的、而 OCR 坏到不能引**

一条是公文结尾套语（原应作 In witness whereof, I have hereunto set my hand and
caused the seal…），扫描件把 my hand 打成一个词、caused 打成 cmiseil，
出处 src-11166a3889de 偏移 4212。
另一条是 1836 年致 Sangamo Journal 的信，讲他主张哪些人应有选举权，
扫描件在关键处丢了字，出处 src-244c03202b38 偏移 544。

**两条都确实是他的文字，但扫描件把词打散了。**
⇒ **不改字**（[[verbatim-is-not-understood]]），**也不引** ——
  要用就去换一个 OCR 更干净的版次，本轮不换。

★★ 这两句**有意不加反引号、也不写成引用块**：
  `check_lane_quotes_verbatim.py` 会把研究稿里反引号包着的片段一律当引文收走，
  而它们**按我的判断不该进引文层**。同理，出处与偏移写成散文而不是 `src-… @…`。
