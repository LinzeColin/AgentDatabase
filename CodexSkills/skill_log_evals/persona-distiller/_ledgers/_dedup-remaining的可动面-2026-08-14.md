# `dedup-remaining` 到底还能动哪些（2026-08-14 夜实测）

## 为什么量这一条

`_长期待办.json` 里六条，**只有 `dedup-remaining` 写着 `blocked_by: None`** ——
其余五条分别卡在 push／㉜／600 人／用户裁定／抓源侧。所以它是唯一「现在就能做」的。
`done_when` 是「每个工作区 `check_source_dedup` 未声明为 0，且每条 `derived_from` 有口径说明」。

## 实测：盘上的 `raw/_dedup.json` 只覆盖 18 个工作区、83 个重复簇

（**只读盘上已有的文件**，没有重跑 `dedup_corpus.py` ——
它会写 `raw/_dedup.json`，而今天已经因为「判据会写盘」栽过一次。）

| 工作区 | 重复簇 | 台账里有 `derived_from` 的行 | 状态 |
|---|---:|---:|---|
| john-marshall | 14 | 30 | ㊺ 已结案（装置不成立） |
| **abraham-lincoln** | 13 | 23 | **第 1 批，等着判分** |
| **thomas-jefferson** | 10 | 15 | **第 1 批** |
| **friedrich-frobel** | 8 | 26 | **第 1 批** |
| john-dewey | 7 | 9 | 返工中 |
| gifford-pinchot | 6 | 9 | 语料阶段（连 meta.json 都没有） |
| luther-burbank | 5 | 7 | 语料阶段 |
| **otto-von-bismarck** | 4 | 4 | **第 1 批** |
| louis-brandeis | 4 | 7 | 返工中 |
| **johann-pestalozzi** | 4 | 4 | **第 1 批** |
| henry-ford | 2 | 6 | 语料阶段 |
| michelangelo-buonarroti | 2 | 2 | 返工中 |
| winston-churchill | 1 | 1 | 缺 SKILL.md，合成门从没跑过他 |
| **immanuel-kant** | 1 | 1 | **第 1 批** |
| leonardo-da-vinci | 1 | 2 | 语料阶段 |
| **niccolo-machiavelli** | 1 | 1 | **第 1 批** |

## ★★ 两个纠正

### ① `blocked_by: None` 是**过时的**

83 个簇里，**41 个落在第 1 批那七个正等着判分的人身上**
（lincoln 13＋jefferson 10＋frobel 8＋bismarck 4＋pestalozzi 4＋kant 1＋machiavelli 1）。
**在预登记之后、判分之前改他们的语料台账 = 中途换被测物**
（同一条理由今天已用于屈折署名候选的裁定）。
⇒ 它的 `blocked_by` 应当写成 **「第 1 批判分完成」**，不是 `None`。

### ② 624 对与这 83 个簇**不是一回事**

`_未声明重复源-按重叠度重量-2026-08-11.md` 记的 **624 对**主要在
**Barton／Osler／Virchow／Nightingale** 身上（≥0.80 段 114 对里 110 对是这三人），
而**这四个人的工作区里根本没有 `raw/_dedup.json`** ——
那份分析用的是另一条路径。两个数**分母不同，不能互相引用**。
[[counts-need-their-cutoff-stated]]

## 现在真正可动的：**42 个簇 / 9 个工作区**

83 − 41（第 1 批）= **42**：marshall 14／dewey 7／pinchot 6／burbank 5／brandeis 4／
ford 2／michelangelo 2／churchill 1／leonardo 1。

★ 但**本轮没有动它们**，理由逐条写清：

- marshall／dewey／brandeis／michelangelo **在返工或结案流程里**，
  今天已经因为「动了正在被别的判定用的东西」栽过；
- pinchot／burbank／ford／leonardo 是**语料阶段**，
  它们的 `derived_from` 该在抓源那一步写，不是事后补；
- churchill 缺 `SKILL.md`，合成门从没对他成立过，先补产物再谈台账卫生。

## 我**没有**量的（写清楚，免得被当成已核）

- **这 83 个簇里，有多少已经在台账里声明过** —— 要逐簇比对 `derived_from` 的取值，
  本轮没做；上表的「有 `derived_from` 的行」是**台账行数**，不是**簇的覆盖率**，
  两者不可换算；
- Barton／Osler／Virchow／Nightingale 那 624 对的当前状态 —— 没有 `_dedup.json`，
  要重跑才有，而重跑会写盘、且他们判过分。
