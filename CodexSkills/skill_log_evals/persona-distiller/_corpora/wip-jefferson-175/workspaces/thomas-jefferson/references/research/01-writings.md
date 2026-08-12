# Writings and systematic works

## Scope and assigned sources

**本道分到 26 份（train split）**：

| source_id | 出版年 | tier | 题名 |
|---|---|---|---|
| `src-6a3cf5192354` | 1776 | P1 | Versión Final De La Declaración De La Independencia |
| `src-843f7cba4fcc` | 1786 | P1 | Draught of a fundamental constitution for the commonwealth of Virginia |
| `src-29b9a8e05249` | 1787 | P1 | Notes on the state of Virginia. Written by Thomas Jefferso…aware and Pennsylvania.  1787 |
| `src-b107fc414c7e` | 1801 | P1 | Notes on the state of Virginia |
| `src-1eeb8d395518` | 1832 | P1 | Notes on the state of Virginia |
| `src-5d9f1ea8579d` | 1851 | P1 | An essay towards facilitating instruction in the Anglo-Sax…of the University of Virginia |
| `src-f3ee30d59c57` | 1854 | P1 | The writings of Thomas Jefferson |
| `src-ac2df69c6c36` | 1871 | P1 | A manual of parliamentary practice: composed originally fo…e Senate of the United States |
| `src-0e84ede7e592` | 1892 | P1 | The writings of Thomas Jefferson; |
| `src-7e5b59c7c6af` | 1892 | P1 | The writings of Thomas Jefferson; |
| `src-c850b7f2e0c7` | 1892 | P1 | The writings of Thomas Jefferson: |
| `src-8bd16b706229` | 1902 | P1 | The life and morals of Jesus of Nazareth : extracted textu…octrines with those of others |
| `src-0604da4c825a` | 1903 | P1 | The writings of Thomas Jefferson |
| `src-965dc5776bbf` | 1903 | P1 | The Writings of Thomas Jefferson |
| `src-f20b182b53fb` | 1903 | P1 | The writings of Thomas Jefferson |
| `src-06b2c10518b9` | 1904 | P1 | Works; |
| `src-2080428c7f4f` | 1904 | P1 | The works of Thomas Jefferson; |
| `src-354b5e5d9486` | 1904 | P1 | The works of Thomas Jefferson; |
| `src-979a7acc8e1b` | 1904 | P1 | Works; |
| `src-b25132260b5c` | 1904 | P1 | Works; |
| `src-b98a3e20228d` | 1904 | P1 | The works of Thomas Jefferson; |
| `src-50b6bb84870e` | 1905 | P1 | The writings of Thomas Jefferson |
| `src-575e212950a7` | 1905 | P1 | The writings of Thomas Jefferson |
| `src-1e85535aa4a1` | 1907 | P1 | Master thoughts of Thomas Jefferson |
| `src-fa22311720b8` | 1907 | P1 | Master thoughts of Thomas Jefferson |
| `src-62fdaa348a52` | 1920 | P1 | The american political classics : Jefferson, Washington and Lincoln |

★ 本节由台账机械导出（`emit_lane_scope.py`），**不含任何阅读判断**；只投影 `split == train` 的行。

## Source-linked observations

**口径**：每条带 `source_id` 与 `norm_offset`，定位可复算（三条已现场验过）。
**逐字照录含 OCR 讹形**（`De`＝be、`m`＝in、`en deavored`／`ordi nary` 是折行），**未改**。

### O-1 · 他把自己的身体反应当**数据**记下来

> `Looking down from this height about a minute, gave me a violent head ach.`
> —— `src-29b9a8e05249` @60368（《弗吉尼亚纪事》，天生桥一段）

★ 描写一处地貌时，他给的不是形容词，是**一个可复现的观察条件与结果**：
往下看**约一分钟**，得到**剧烈头痛**。时间是量的，反应是身体的。
⇒ 他记录风景的方式与记录测量的方式**是同一种**。

### O-2 · 他在别人反驳之前，先把反驳的依据说出来

> `I am aware, that authorities can often De produced m opposition to the rules which
>  I lay down as parliamentary.`
> —— `src-ac2df69c6c36` @5495（《议事手册》）

★ `I am aware, that authorities can often be produced in opposition to the rules
which I lay down` ——**「我知道，常常能举出与我所立规则相反的权威」**。
先承认对面有牌，再往下讲。与 Lincoln 的 O-2（引旧话来自我设限）同一路数，
**而卢梭是先划清「这是谁的」、马基雅维利是先划清「在什么条件下」**——
四个人在同一个位置放的东西各不相同。

### O-3 · 他给自己的定位是**编纂者**，不是立法者

> `I have here en deavored to collect and digest so much of these as is called for in
>  ordi nary practice, collating the parliamentary with the senatorial rules, both where
>  they agree and where`
> —— `src-f3ee30d59c57` @7118

★ 动词是 `collect`／`digest`／`collating`，**没有一个是「创制」**。
且明写「**一致处与分歧处都并列**」——不藏分歧。

---

## ★ 本道剔除的几条

- 一条是**法文的数字化公有领域声明**（`Nous encourageons … l'utilisation des ouvrages
  et documents appartenant au domaine public`）——**图书馆的样板，不是他的话**，
  而它出现在一份 `tier=P1` 的源里。★ 这类样板**能被 `check_holdout_overlap` 的
  df 过滤当作样板剔掉，却挡不住引文摘取**。
- 一条 `They are now offered to the public in their original form and language.`
  ——语气像编者说明，**归属存疑，不引**。
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
