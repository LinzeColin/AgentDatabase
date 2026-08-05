# Sorby #133：同名护栏实测——**抓源之前必读**

## 结论：现有护栏挡不住他父亲，而他父亲的材料确实在馆藏里

`check_authorship.ocr_byline_evidence(text, first="Henry", last="Sorby")` 实跑：

| 署名行 | 是谁 | 期望 | **实际** |
|---|---|---|---|
| `By Henry Clifton Sorby, F.R.S.` | 目标本人 | 放行 | 判为本人 ✓ |
| `By H. C. Sorby, F.R.S.` | 目标常见署名 | 放行 | **不认为是本人**（漏，但无害） |
| **`By Henry Sorby.`** | **父亲（c.1791–1846）** | **应拦** | **★★★ 判为本人——挡不住** |
| `By T. C. Sorby, Architect.` | 建筑师 | 应拦 | 不认为是本人 ✓ |
| `By II. C. Sorby, F.R.S.` | OCR 把 H 读成 II | 放行 | 不认为是本人（漏，但无害） |
| `By Robert Sorby.` | 锉刀商 | 应拦 | 不认为是本人 ✓ |

★★★ **护栏比的是「名 + 姓」，而父子二人这两样全同。**
这正是 [[test-the-guard-against-this-persons-namesake]] 记的形状——
上一次是 GE 总裁 Charles A. Coffin 被当成焊接发明人的署名放行。
**这一次是在抓源之前测出来的，不是入库之后。**

## 为什么这不是理论风险

1. University of Sheffield 的 Sorby Collection 明写着
   `one diary from his father covering 1845-1846`——**同一馆藏里「Sorby 的日记」指两个人**。
2. **1841 年人口普查里目标本人也只登记为「Henry Sorby」**，没有 Clifton。
3. 父亲卒年本身还有争议：1846（Grace's Guide）vs 1847（Wikipedia）——
   **而这一年正好落在「哪些材料可能是父亲的」那条分界线上。**

## 抓源与入库必须照这条判据走（不是「注意一下」）

**「名+姓」不足以定人。** 三选一，命中任一才算目标本人：

1. 出现中名 **Clifton**（目前唯一无冲突的区分符，没找到第二个 Henry Clifton Sorby）；
2. 署名旁有 **F.R.S.** 或 **F.G.S.**（父亲不是会员）；
3. 出处是 **1850–1908 年的学会会刊**（父亲 1846/47 年已故，不可能在其上发表）。

★ 反过来的红线：**1850 年以前的、署名只有「Henry Sorby」的材料，一律先按父亲处置**，
除非能用上面三条之一正面证明是儿子。目标 1826 年生，1850 年他 24 岁——
**更早的东西几乎不可能是他发表的。**

## 还没做的

- 上面三条判据**尚未落成代码**。落之前，`ingest` 时须逐份人工核署名。
- `T. C. Sorby` 与 `H. C. Sorby` 只差一个首字母，而实测同批扫描的首字母讹形有
  `H. G.`／`U. G.`／`IT. C.`／`II. C.`／`E. 0.`——**首字母不可信，别拿它当判据。**
