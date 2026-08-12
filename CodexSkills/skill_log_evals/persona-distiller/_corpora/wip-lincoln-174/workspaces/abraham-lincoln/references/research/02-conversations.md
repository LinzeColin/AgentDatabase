# Conversations and interviews

## Scope and assigned sources

**本道分到 7 份（train split）**：

| source_id | 出版年 | tier | 题名 |
|---|---|---|---|
| `src-dc0a040e9036` | 1898 | P1 | ...Early speeches, Springfield speech, Cooper union speech…etters, Lincoln's lost speech |
| `src-3176773929d7` | 1903 | P1 | Unpublished Letters of Abraham Lincoln |
| `src-ad151187f39b` | 1903 | P1 | Letters and addresses of Abraham Lincoln |
| `src-fb5c5f0f20c2` | 1903 | P1 | Letters and addresses of Abraham Lincoln .. |
| `src-01cdd68a3dfa` | 1908 | P1 | Letters and addresses : with a brief biography, the story …ist of authorities, and index |
| `src-af9d9ae573da` | 1908 | P1 | Gettysburg address : delivered at the dedication of the Na…Mrs. Bixby, November 21, 1864 |
| `src-92e8d29fbc61` | 1922 | P1 | Abraham Lincoln and Mary Owen : three letters, Lincoln to … O.H. Browning to I.N. Arnold |

★ 本节由台账机械导出（`emit_lane_scope.py`），**不含任何阅读判断**；只投影 `split == train` 的行。

## Source-linked observations

**口径同 01-writings**：每条带 `source_id` 与 `norm_offset`，定位可复算。

### O-1 · 他二十三岁第一次公开求职，把「被同乡看得起」摆在首位

> `Whether it be true or not, I can say, for one, that I have no other so great as that
>  of being truly esteemed of my fellow-men, by rendering myself worthy of their esteem.`
> —— `src-ad151187f39b` @1242

★ 注意后半句的结构：`by rendering myself worthy of their esteem` ——
**被人看得起这件事，他把它挂在「先让自己配得上」这个条件上**，
而不是挂在别人怎么看。与 01-writings 的 O-2（引旧话来自我设限）是同一种手法。

### O-2 · 回信的第一句先复述对方来信，再落自己的话

> `Dear Sir Yours, inviting me to attend a mass meeting on the 23rd Inst is received.`
> —— `src-3176773929d7` @1789

★ 这是格式，但格式本身透露口径：**先把对方说的事复述成一句可核的事实**，
再开始自己的表态。

---

## ★★ 一句话，三个 source_id —— 证据塌缩的现成例子

O-1 那句同时出现在

    src-fb5c5f0f20c2 @820   （OCR 作 `rendering mj^self worthy`）
    src-ad151187f39b @1242  （OCR 作 `rendering myself worthy`）
    src-01cdd68a3dfa @1215

**三个 source_id，实质一处证据。**
★ 引用时**只署一个**（这里取 OCR 最干净的 `src-ad151187f39b`），
其余两个若要提，必须说明是同一处
（[[two-source-ids-is-not-two-evidences]]：落成判据后 11 人里 7 人有塌缩、共 57 条）。

★ 另注意 `mj^self` 与 `myself` 的差别：**逐字抄 OCR 是对的，
  而把讹字改回去再当逐字引文用是错的**（[[verbatim-is-not-understood]]）。
  这里选了本来就干净的那一份，**没有改任何字**。

## ★ 本道剔除的两条

- 一首赞颂他的诗（`He knew to bide his time…`，**第三人称**，作者不是他）
- 一段收藏者的说明（「以下三封信一度在我手上，我能担保其真实」）——
  **第一人称是收藏者的**。★ 这一条**没有任何机械特征可筛**，
  与 01-writings 里「林肯没当过法官」那句同类：**只能靠人读。**
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
