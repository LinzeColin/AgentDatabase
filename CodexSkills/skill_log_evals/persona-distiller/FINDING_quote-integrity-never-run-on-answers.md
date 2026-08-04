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

## 三、★★ 回头扫了所有能扫的人物——**而我的报出里三分之二是误报**

```
可扫的 4 人 + Mendel：
  koch-107     引文 16 条　未命中 **0**
  lister-108   引文 15 条　未命中 **0**
  pasteur-106  引文 22 条　未命中 **2**  ← **两条都是误报，见下**
  mendel-125   引文  6 条　未命中 **1**  ← 真的
  另 5 人（barton/fleming/jenner/nightingale/osler/virchow）
      **语料目录不在本机 → 未核，不是「通过」**
```

### Pasteur 的两条为什么是误报

**`lp-known-01`：「He took up the trade of a tanner」**

语料里 `trade of a tanner` **0 处**，但 `tanner` 22 处、`tanneur`（法文）16 处。
而**答案自己就写着**：

> （我手上这条出自一部**英译传记**，作 `He took up the trade of a tanner`——
> **那是译者的英文，不是我的原话**；法文原本我这里没有。**按我自己的规矩，这里标出来。**）

★★★ **这正是 Mendel 那一处该做而没做的事。**
一个更早的产物已经把正确做法演示过了：**引了非原语的字，就在答案里说明它是什么。**

**`lp-boundary-01`：「Copyright 1922/1924/1933/1930 by Pasteur Vallery-Radot」**

那是把四卷的版权行**压成一条列举**（年份用斜杠并列），不是宣称某一卷逐字如此；
上下文是一张「哪些字不是我的」清单。**写法偏松，但不是伪造。**

### 于是本次报出的精确率是 **1/3**

与既有记录一致：**判据自己第一版常错。**
**误报的成因是同一个**：判据分不出「引了并声明了来路」与「引了并宣称是原话」。

★ 而这**不该靠调判据解决**——它已经是「只报不拦」，文件头也明写
「未命中不等于伪造，须人工看一眼原文再定」。**人工那一步今天真的做了，三条各有归属。**

## 四、做了什么

**接进 `build_blind_payload.py`（v0.0.0.122），在派发之前跑，只报不拦。**

**没有做的**：没有改 Mendel 的答案（本轮已判完，改它就是中途换被测物）；
没有把 `check_quote_integrity` 改成硬门（**报出里三分之二是误报，做成硬门会拦下正确的产物**）。

## 五、留给后面的一条具体规矩

> **引一段非原语／非原样的字，就在答案里说明它是什么**——
> 是译文、是校正过的 OCR、还是压缩的列举。
> **Pasteur `lp-known-01` 是范本；Mendel `gm-fact-preservation-01` 是反例。**

参见 `_corpora/wip-mendel-125/_round3_verdict.md` 第七节、
[[judges-cannot-verify-quotes]]、[[verbatim-is-not-understood]]。
