# Liebig #124：10 份因花体 OCR 乱码剔除（**不是删除，是记录**）

日期：2026-08-04　判据：`scripts/check_ocr_legibility.py`（v0.0.0.105）

---

## 剔除的 10 份

| short | 分档 | 道 | 字符数 | 正确形词率 | 乱码形词率 | 比值 |
|---|---|---|---:|---:|---:|---:|
| b2130886x | **P1** | expression | 1,846,853 | 0.0132 | 0.1126 | 8.53 |
| b2898304x | S1 | external | 984,548 | 0.0080 | 0.1030 | 12.90 |
| bub_gb_QlVBAAAAYAAJ | **P1** | writings | 863,556 | 0.0074 | 0.0741 | 10.06 |
| diemodernelandw00liebgoog | **P1** | writings | 646,155 | 0.0221 | 0.1004 | 4.54 |
| briefwechselzwi00liebgoog | **P1** | conversations | 549,833 | 0.0064 | 0.1070 | 16.83 |
| dieorganischech00liebgoog | **P1** | writings | 512,969 | 0.0091 | 0.1057 | 11.56 |
| vollstndigerunt00liebgoog | **P1** | writings | 180,626 | 0.0051 | 0.0685 | 13.50 |
| ueberfrancisbaco00lieb | **P1** | expression | 134,414 | 0.0239 | 0.0977 | 4.09 |
| b30359880 | **P1** | decisions | 72,959 | 0.0158 | 0.0947 | 5.98 |
| berdasstudiumd00liebuoft | **P1** | decisions | 45,407 | 0.0149 | 0.0978 | 6.56 |

**合计 5,837,320 字符，其中 9 份是 P1（一手）。**

## 长什么样

`b2130886x` 的正文（这是「德文」）：

```
dürften, vor 2filem ber I)od)ftnntge ©rünber ^)of)eni)eim6, unfterb(id)e Ser*
bienfte um bic beutfebe 2anbwirtbfd)aft erworben.
```

`ber`=der、`unb`=und、`bic`=die、`ift`=ist、`I)`=h、`2)`=D、`©`=G。
**整篇没有一个词能拿去检索或引用。**

## 为什么既有的门全放行

| 门 | 为什么看不见 |
|---|---|
| `sha256` 去重 | 字节当然不同 |
| 来源数 45 | **份数是真的** |
| 一手占比 0.65 | **分档是真的** |
| 字数统计 | **字数是真的**（还特别多） |
| `near_duplicates` | 长 s 把 shingle 打灭，见 v0.0.0.104 |
| `check_corpus_integrity` | 它判「是不是取不到的错误页」——这是真文档 |
| `check_ocr_homoglyphs` | 它查西里尔／希腊同形字——这不是同形字 |
| **`check_ocr_language_death`** | **10 份里只抓到 5 份**，成因见下 |

★ `check_ocr_language_death` 取**多语种里最高的**虚词占比，于是乱码德文被别的语种接住：

```
bub_gb_QlVBAAAAYAAJ       0.109 [pt]   ← 葡萄牙语接住了
vollstndigerunt00liebgoog 0.159 [pt]   ← 且高过 0.15 的门，逃掉
b2130886x                 0.189 [fr]   ← 法语接住，逃掉
diemodernelandw00liebgoog 0.327 [de]   ← **按德语算 0.327，远高于门**
```

最后一份最说明问题：**短虚词（in/so/an/um）扛过了花体 OCR**，
而 `der/die/und/ist` 整批被换成 `ber/bie/unb/ift`——
**虚词总量没掉，是被替换掉了。** 按「缺失」判的判据因此看不见它。

`check_ocr_legibility` 直接比「正确形 vs 乱码形」，这 10 份 **10/10 全中**。

## 剔除后仍过 deep 门

```
来源 62 → **52**（门 45）✓
道   6  → **6** （门 6） ✓
一手 46 → **37**（门 30）✓
一手占比 0.7419 → **0.7115**（门 0.65）✓
```

**四项仍然全过**，所以这不构成延后，只是语料变干净了。

## 这 10 份没有被删

原文仍在本次抓源的 scratchpad 产物里。**它们不是坏来源，是坏扫本**——
同一批书在别处可能有干净的转录（例如 Deutsches Textarchiv 的人工校对本，
本次因该站 `/search` 对 GET 参数无反应而**结论悬空，不记作 0 命中**）。
若日后取到干净扫本，这 10 条可以直接补回台账。
