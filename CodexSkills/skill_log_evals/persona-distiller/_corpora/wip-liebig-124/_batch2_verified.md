# 第二轮补抓 12 份：**我自己复核过，不是照抄抓源方的自述**

日期：2026-08-04　方法：用 `check_ocr_legibility.legibility()` 与逐字子串比对独立重跑

---

## 一、为什么要复核

抓源方交回一张表，自报每份的 OCR 词率与扉页署名。
**自述不是证据**——能出示的就出示。这 12 份的两项都能自己重跑，所以重跑了。

## 二、OCR 可读性：自报 vs 实测

| short | 自报 good | 实测 good | 自报 bad | 实测 bad | 判定 |
|---|---:|---:|---:|---:|---|
| dieorganischeche00lieb | 0.1611 | 0.1582 | 0.0004 | 0.0004 | ok |
| b33487364 | 0.1588 | 0.1496 | 0.0006 | 0.0006 | ok |
| diechemieinihre04liebgoog | 0.1216 | 0.1141 | 0.0231 | 0.0217 | ok |
| 10074344bsb | 0.1515 | 0.1559 | 0.0022 | 0.0022 | ok |
| chemischebriefe01liebgoog | 0.1248 | 0.1219 | 0.0289 | 0.0283 | ok |
| 34444006902092 | 0.1556 | 0.1399 | 0.0002 | 0.0002 | ok |
| 34444006902092_0 | 0.1580 | 0.1481 | 0.0003 | 0.0002 | ok |
| diechemieinihre01liebgoog | 0.0986 | 0.0877 | 0.0485 | 0.0431 | ok |
| diechemieinihre03liebgoog | 0.1101 | 0.1027 | 0.0379 | 0.0353 | ok |
| 10701480bsb | 0.1574 | 0.1504 | 0.0012 | 0.0011 | ok |
| chemischebriefe00lieb | 0.1641 | 0.1608 | 0.0000 | 0.0000 | ok |
| briefwechselzwis00liebuoft | 0.1317 | 0.1289 | 0.0001 | 0.0001 | ok |

```
12 份里判为非 ok 的：**0**
自报与实测的差都在 ±0.016 以内（分词口径略不同），**方向与量级一致**
```

## 三、★ 有 4 份是「可读但讹字偏多」，不是「干净」

```
diechemieinihre01liebgoog  乱码形 0.0431
diechemieinihre03liebgoog  0.0353
chemischebriefe01liebgoog  0.0283
diechemieinihre04liebgoog  0.0217
```

**判定仍是 `ok`**——正确形（0.088–0.122）明显更高。
判据判的是**「整篇不可读」**，不是**「有讹字」**（Osler／Blackwell 那种
「保留扫本讹字并标出」反而是加分项）。

**但要记着这 4 份的引文风险更高**，从它们取逐字引文时须回原扫描件核对。

## 四、扉页署名：逐字复核 **12/12 在正文里**

抓源方照录的那一行，**逐字**拿去正文里搜：

```
dieorganischeche00lieb        `Juſtus Liebig,`             ✓
b33487364                     `Juſtus Liebig,`             ✓
diechemieinihre04liebgoog     `Juſtus Liebig.`             ✓
10074344bsb                   `Liebig, Justus <<von>>,`    ✓
chemischebriefe01liebgoog     `Inſtus von Liebig.`         ✓   ← OCR 把 J 读成 I，原样保留
…（其余 7 份同样命中）
```

★ **长 s（`ſ`）与讹字都原样保留**，没有代改。
`Inſtus`／`Ziebig`／`Jiebig` 是扫本实况，改了反而无从复核。

## 五、这 12 份把两项门推到哪

```
一手  27 → **39**   （deep 门 30）✓ **过了**
总数  52 → **64**
占比  0.5192 → **0.6094**（deep 门 0.65）✗ **仍未过**
道    writings +11、conversations +1；expression／decisions **各 +0**
```

★ 抓源方查明那两道空缺的成因是**扫描质量不是语料不存在**：
27 份候选里 11 份花体乱码，而乱码的**恰好全是 expression／decisions 的短篇**，
Bacon 那篇换了**三个独立扫描件全乱**。已发第二轮去 MDZ／Google Books 取干净本。

★ 差 **8 份纯 P1** 到 0.65：`(39+x)/(64+x) ≥ 0.65` → `x ≥ 7.43`。

## 六、抓源方的一个方法学证实

`chemischebriefe01liebgoog` 与 `02liebgoog` **扉页一字不差**
（`Dierte umgearbeitete und vermehrte Auflage`／1859／Winter），
**8-gram containment 却 <0.30**——长 s 归一化之后仍然如此，
因为两侧的花体误读模式不同。

**书目判重（题名+年+出版者+版次）才是这批的判准**，内容判重不可靠。
这与 v0.0.0.104 的结论一致，是第二次独立撞到。
