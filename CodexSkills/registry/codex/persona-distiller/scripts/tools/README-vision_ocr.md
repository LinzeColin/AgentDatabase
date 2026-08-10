# `vision_ocr.m` —— 用 macOS 自带 Vision 重新 OCR 页图

## 什么时候用它

**当聚合站（archive.org / HathiTrust）的 OCR 派生件坏掉，而页图是好的。**

判断「坏没坏」用这一个数：**≤2 字母词占比**。

```bash
python3 -c "
import sys,pathlib
t=pathlib.Path(sys.argv[1]).read_text(encoding='utf-8',errors='replace')
k=t.split(); print(f'{sum(1 for x in k if len(x)<=2)/max(1,len(k)):.4f}')
" 某文件.txt
```

| 值 | 判读 |
|---:|---|
| **0.25–0.28** | 正常英语散文 |
| 0.30–0.36 | 正常，但页内有数据表（短数字 token 多） |
| **< 0.10** | **系统性丢虚词**——`a / of / to / in / is` 这类被吃掉，**文本派生件救不回来** |

★ 实例（Shewhart #165，2026-08-11）：ASCE Transactions Vol.91 (1927) 全卷 **0.0265**，
`_djvu.txt` / `_hocr_searchtext` / 原始 `_hocr.html` 三处同值——**词根本不在 hOCR 里**，
不是被低置信度过滤掉的。而该件元数据**自报 `confidence: 94`、950 页均值 93.35**。
**自报 94 分的同时丢了八成虚词——聚合站的置信度字段不能当质量判据。**

★★ 对照：同一批里那份「已知 OCR 差」的 BSTJ 9-2-364 是 **0.2815**——
它的毛病是**认错字母**（`JOVRSAL`、`Br`←`By`），不是丢词。**两种坏法要分开。**

## 建

本机**没有** tesseract / pdftotext / ocrmypdf，但有 `clang` 和 `Vision.framework`。

```bash
clang -fobjc-arc -O2 -o vision_ocr vision_ocr.m \
  -framework Foundation -framework Vision -framework ImageIO -framework CoreGraphics
```

★ **不要用 Swift 写这个工具。** 只装了 Command Line Tools（没装完整 Xcode）时，
`swiftc` 会去重建 SDK 的 `.swiftinterface` 并失败——实测两版（含只依赖
Foundation/Vision/ImageIO 的最小版）各跑了 3 分钟以上后报错。
**Objective-C 完全不碰 swiftinterface，一次就过。**

## 跑

```bash
./vision_ocr pages/leaf63.jpg pages/leaf64.jpg > out.txt
```

每页输出 `=== 文件名 === 宽x高 N 行`，随后逐行是识别结果。

- `usesLanguageCorrection = NO` —— **要照录，不要它替我猜**。讹字保留。
- `recognitionLevel = .accurate`。

## 取页图

```
https://archive.org/download/<identifier>/page/leaf<N>.jpg
```

302 跳到 BookReaderImages，直接给原生分辨率灰度 JPEG。
★ `page/n<N>_x1400.jpg` 会给**裁剪过的**小图（实测 837×3448 而非 2236×3448），别用。
★ 用 `scandata.xml` 里的 `origWidth`/`origHeight` 核对拿到的是不是原生分辨率。

## ★★★ 用它切段时的两条铁律（Shewhart #165 实测踩过）

1. **起讫由发言标签定，不由书眉定。**
   ASCE 那一卷实测：p.50 书眉写 `SHEWHART ON …` 而**前 37 行是前一位发言人的尾巴**；
   p.54 书眉写 `NIMMO ON …` 而**他的话在那一页还延续 19 行**。
   **照书眉切，两头都会切错人。**
2. **剥版口只剥「书眉行 + 紧邻它的那个数字」。**
   我第一版写 `^\d{1,3}$` 剥「页码」，把表格里的 `779` / `673` / `953` 一起吃掉了——
   这几页有数据表。**静默丢数据比留着版口糟得多。**

## 落账要求

重 OCR 得到的正文**必须在台账里写明它来自哪一遍 OCR**：
下游若要逐字引文，引的是**你这一遍**的字，不是聚合站那一遍的。
