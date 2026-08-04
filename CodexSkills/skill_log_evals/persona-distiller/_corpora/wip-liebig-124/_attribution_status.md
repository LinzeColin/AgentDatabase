# Liebig #124 归属核查——**扉页署名逐份扫过，又查出 6 份不是他写的**

日期：2026-08-04　方法：对 35 份 P1/P2 逐份在正文前 14k（未中者再扩到 60k）搜署名式，
并对每份拉 archive.org `creator` 原始字段比对

---

## 一、结果

```
P1/P2 共 35 份
  前 14k 内找到署名：**21 份**
  扩到 60k 后再找到：**4 份**（justusvonliebigu、b22278503、ueberghrungberq、b2236738x、principlesagric01）
  60k 内仍无署名：**9 份**
```

## 二、★ 扩查之后查出的第二批错分（在已改的 2 份之外）

| short | IA creator 实际是谁 | 这是什么 | 现记 | 应记 |
|---|---|---|---|---|
| `homoeopathiclawo00grau` | **Grauvogl, Eduard von** | 那封公开信的**英译本** | P2 | **S1/external** |
| `culturedemandedb02youm` | **Youmans, E. L.（ed.）**, Tyndall… | **文集**，Liebig 是其中一位撰稿人 | P2 | **P2 但卷非他所著** |
| `correlationandco00youmrich` | **Youmans, E. L.**, Helmholtz… | **文集**，同上 | P2 | 同上 |
| `magazinfrpharma14unkngoog` | **Geiger, P. L.／Hänle, G. F.** | **期刊**，他在其中发论文 | P2 | 同上 |
| `b2931236x` | **Davy, Humphry** / Shier / Liebig | **合集** | P2 | 同上 |
| `bub_gb_hEo0AQAAMAAJ` | **Müller, Johann Heinrich Jacob** | 他人著作 | P2 | **S1/external** |
| `anleitungzurqua00liebgoog` | **Fresenius, C. Remigius** / Liebig | **Fresenius 所著**，Liebig 作序 | P1 | **S1，或只取序** |

★ 与前一批（`erklrungveranl00buffuoft` = Buff 的论战文、
`dashomopathisc00grau` = Grauvogl 写给他的公开信）合计，
**抓源分类把 9 份不是他写的东西记成了一手。**

## 三、确认是他的（署名可出示）

```
b2236738x                「EXTRACT OF MEAT. BY BARON LIEBIG, President of the Royal Academy…」
ueberghrungberq00liebgoog 「München, im Februar 1870.　Justus von Liebig.」（文末亲署）
ausjustusliebig00whgoog  「AUS JUSTUS LIEBIG'S / FRIEDRICH WÖHLER'S BRIEFWECHSEL…」（书信集，CO-AUTHORED）
b22278503                「…CLOSING CORRESPONDENCE WITH BARON LIEBIG」（书信，CO-AUTHORED）
justusvonliebigu00liebuoft 「Justus von Liebig und…」Kahlbaum 编（书信集，CO-AUTHORED）
b31351736                「BRIEFE VON JUSTUS LIEBIG NACH NEUEN FUNDEN / Herausgegeben von Prof. Dr. Ernst Berl」
```

## 四、★ 一个要留意的：`principlesagric01liebgoog`

IA creator 写 `Justus Liebig`，而正文里出现的是**第三人称转述**：
「as **Baron Liebig somewhere has said**, therein lies the whole future…」
——**这是别人在引用他，不是他在写。** 该份须回头确认是原著还是评注本，
在确认之前**不计入一手**。

## 五、现在的门状态

```
research 门错误 23 条 → 其中
  research.source-unclaimed   ×20   ← 本文件处理的就是这一类
  research.attribution-basis  ×1
  structure.missing           ×1    ← evidence/claims.jsonl（下一道工序，尚未开始）
  research.lane-completion    ×1    ← 六条道的研究尚未做
```

`attribution_basis` 已写入 `meta.json` 并通过 `check_attribution_basis`
（6 条争议篇目具名，含 `Judenfrage4/5` 那个 creator 串一字不差的反例）。

## 六、下一步（未做，不假装做了）

1. 按第二节逐份改分档并重跑 `ingest`
2. 改后重算 deep 四项——**一手 35 份要减掉 7–9 份，`min_primary 30` 会贴到边**，
   届时若不足**记延后，不放宽**
3. 六条道的研究 → `evidence/claims.jsonl`
