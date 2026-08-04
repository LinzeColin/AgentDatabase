# 引文真伪判据支持 `--answers`，**而全项目没有一处这样调用过它**

日期：2026-08-05　撞出人物：#125 Mendel（收尾时补跑）

---

## 一、事实

`check_quote_integrity.py` 从第一版就有 `--answers` 参数。
**全代码库搜一遍：没有任何一处拿它去核候选答案。** 它只被用来核断言层。

**而候选答案正是评委看到的那份东西——评委手里没有语料，这一类他们结构性地核不了。**
（已有记录：两席三轮六次评审对四处编造 **0 命中**，一行 grep 全抓出。）

## 二、补跑 #125 Mendel，报出一条，**是真的**

```
语料 17 份（train，holdout 已排除）　引文 6 条　**未命中 1 条**
⚠ gm-fact-preservation-01：「Einleitende Bemerkungen」
```

回原文：**语料里印的是 OCR 讹字 `Hinleitende Bemerkungen`**（E 读成 H）。

> `Versuche über Pflanzen-Hybriden. Von Gregor Mendel.`
> `(Vorgelest in den Sitzungen vom 8. Februar und $. März 1865.)`
> `**Hinleitende Bemerkungen.** Künstliche Befruchtungen, welche an Zierpflanzen`
> `**desshalb** vorgenommen wurden, … waren die Veranlassung zu den Versuchen,`

★★ **我把 OCR 错字改正之后，当逐字引文用了，而且没有标注。**
本项目的做法是**照录含讹字**（`06-timeline.md` 明写「逐字照录，含 OCR 讹字」）——
**同一份产物里两种做法并存。**

**席 D 给这一题 0.93（它第 3 轮的最高分），席 E 给 0.82。两席都没抓到。**

★ 同一次补跑**顺带证实了两处席 E 明说「无从核对」的**：
`desshalb`（旧拼）与 `waren die Veranlassung zu den Versuchen`，**两条都逐字属实**。

## 三、★★ 回头全扫十人——**我第一版的扫法把一半人报成了「未核」，那是错的**

### 先说那个错

我第一版报「barton／fleming／nightingale／osler／virchow **语料目录不在本机 → 未核**」。
**假的。** 语料一直都在，是我的路径写错了：

```
koch / lister / pasteur / mendel      → workspaces/<人>/references/
barton / fleming / nightingale /
osler / virchow                        → workspaces/<人>/**<人>**/references/   ← 多嵌一层
```

**十个人里有五个的工作区多嵌一层同名目录**，而我的 glob 只写了一层。
★ 一度还因此看到「git 索引里有 735 个 .txt、磁盘上 0 个」这种不可能的现象，
**差点当成数据丢失去查** ——`git status` 一直是干净的，文件一直都在。

### 扫全之后的真实结果

| 人物 | 引文 | 未命中 | |
|---|---:|---:|---|
| barton-117 | 25 | **0** | |
| virchow-109 | 22 | **0** | |
| koch-107 | 16 | **0** | |
| lister-108 | 15 | **0** | |
| **mendel-125** | 6 | **1** | ★ **唯一的真缺陷** |
| fleming-111 | 17 | 2 | 误报 |
| nightingale-112 | 13 | 2 | 误报 |
| pasteur-106 | 22 | 2 | 误报 |
| osler-110 | 28 | 3 | 误报 |
| jenner-104 | — | — | **无 references 目录，这个才是真的未核** |

```
九人可扫，引文 164 条，报出 10 条
  真缺陷 **1 条**（Mendel 的 OCR 校正，且**没有标注**）
  误报 **9 条** → **精确率 1/10**
```

### ★★★ 九条误报是同一件事，而那件事恰恰是**正确做法**

九条全部是「引了语料之外的东西，**而答案里已经说明了它是什么**」：

| 人物 | 被报的字符串 | 答案里怎么说的 |
|---|---|---|
| Pasteur | `He took up the trade of a tanner` | 「**那是译者的英文，不是我的原话**；法文原本我这里没有」 |
| Pasteur | `Copyright 1922/…/1930 by Pasteur Vallery-Radot` | 一张「哪些字不是我的」清单里的**压缩列举** |
| Osler | `EDITED, WITH ADDITIONS, BY WILLIAM OSLER` | 明说是**扉页那一行** |
| Osler | `Osler, William, Sir, 1849-1919` | 明说是**著录的 creator 字段** |
| Fleming | `Fleming, Alexander, 1824-1875` | 「archive.org 把 1845 年那本**著录在**…名下」，另一处更直接：**「（不在语料里，出自抓源时的同名排除记录）」** |
| Nightingale | `David, F. N. (Florence Nightingale), 1909-1993` | 同上，同名排除用的著录条目 |

★★ **早先的产物一直在做对的事，而且做得很齐。** 只有 Mendel 那一处没标注。
**规矩不是新的——是我在 Mendel 上没照做。**

## 四、做了什么

**接进 `build_blind_payload.py`（v0.0.0.122），在派发之前跑，只报不拦。**

**没有做的**：没有改 Mendel 的答案（本轮已判完，改它就是中途换被测物）；
没有把 `check_quote_integrity` 改成硬门（**报出里 9/10 是误报，做成硬门会拦下九个正确的产物**）。

## 五、留给后面的一条具体规矩

> **引一段非原语／非原样的字，就在答案里说明它是什么**——
> 是译文、是著录的 creator 字段、是扉页那一行、是校正过的 OCR，还是压缩的列举。

★ **九个范本**（Pasteur、Osler、Fleming、Nightingale 各处），**一个反例**
（Mendel `gm-fact-preservation-01`）。**这条规矩不是今天新立的，是它一直在被遵守，而我漏了一次。**

## 六、★ 顺带记一条结构上的不一致

十个工作区里，**五个是 `workspaces/<人>/references/`，五个是 `workspaces/<人>/<人>/references/`**。
**同一条流水线产出的目录结构不一致**，而任何按固定深度写的 glob 都会静默漏掉一半。
今天就漏了一次，并因此报出「语料不在本机」这个**假结论**。

参见 `_corpora/wip-mendel-125/_round3_verdict.md` 第七节、
[[judges-cannot-verify-quotes]]、[[verbatim-is-not-understood]]。
