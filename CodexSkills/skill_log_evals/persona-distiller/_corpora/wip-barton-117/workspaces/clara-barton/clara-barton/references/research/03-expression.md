# Expression DNA and micro-behavior

**本路 18 份（P1 17／S1 1）。最要紧的一条不是「她怎么说话」，
而是「这一卷里哪些话根本不是她的」。**

## Scope and assigned sources

train 分割，18 份。核心三份：
src-830d04ae857d（War lectures, 1860s，39.6 万字符）、
src-1b1b3a253ec5（Poetry, 1864-1909）、
src-10d339032b4c（Poetry, 1854-1909, undated）。
另有 src-b8a894e3831c（Franco-Prussian War lecture, 1870）、
src-4776c52df4ea（Memorial Day address, undated）、
src-3ad3fc0fc419（1849 年日记，含诗）。

## ★★ Source-linked observations 一：诗作卷是杂抄本，不是她的诗集

`Speeches and Writings File; Poetry; 1864-1909`（LOC mss11973，106/0700）
**卷内自己就用三种标记把来源分开了**，逐行照录：

```
第  10 行   Copied from Clara Barton diary.
第  36 行   By Room   June 5, 1864.        （其后整首加引号）
第  76 行   Written by Miss Clara Barton in 1872 for reading at a social
第 277 行   Written by Clara Barton while ill in
```

**只有标 `Written by … Clara Barton` 的才是她写的。**
第 10 行那首（`Has our love all died out, have its altars grown cold,`）
标的是 **`Copied`**——**抄进日记不等于她写的**；
第 36 行那首标 `By <他人>` 且全诗加引号，是**转录别人的作品**。

**整卷当作她的诗，就会把别人的诗放进她嘴里。**
姊妹卷 src-10d339032b4c 同型：`check_authorship` 在其中实测检出他人署名
`By  John  W.  Chadruck.`。

**处置**：取逐字引文前，先在该条上方找最近的一个来源标记；**找不到标记的一律不取。**

## Source-linked observations 二：她本人的声音 —— src-830d04ae857d

战后巡回演讲手稿，开篇逐字照录（**句中大写与连字符为原稿形态**）：

> `Gentlemen and Ladies,`
> `I come Before you`
> `to-night Both willingly and cheerfully -`
> `more than willing to render my`
> `account for the unmeasured kindness`
> `received of the american people, and`
> `the great confidence reposed in me by`
> `the officers and men of the army`

两处可用：

1. **句中大写**（`Before`、`Both`）是她手稿的书写习惯，**不是 OCR 噪声**
   ——同一段里 `american` 反而小写，说明大写是选择性的。
2. **她把演讲定位成「交账」**（`render my account`）而非自述功绩，
   紧接一句 `it is my duty to state them when required`。
   **「受人之托、有义务说明」是她给自己找的说话位置。**

## Contradictions and alternative explanations

「句中大写」也可能来自转录者的忠实迻录而非她的习惯。
**本路不据此单独下断言**；要用它，须在 01 写作路的**出版物**里找到同型证据
（出版物经排版规范化，若仍保留则更可能是她的习惯）。

## Unknowns and source gaps

- **这一路全是未刊手稿，没有一份经她本人校订出版。** 与 01 路的出版物不是同一种可靠度。
- 多份标 `undated`（含 src-4776c52df4ea）。**不许给它们编年份**；
  需要时间锚点的断言去 06 时间线找。
- **没有任何录音或逐字速记稿**——十九世纪不存在。
  凡涉及「她当场怎么应答」的断言，**本路给不出证据**，只能去 02 对话路。
- src-b8a894e3831c（普法战争讲稿）尚未逐段读完；
  **她随普鲁士红十字工作、并据此把欧洲经验带回美国**，下一轮优先。
- **本批语料是双空格 OCR**（`CLARA··BARTON.`；`taken` 被认成 `talien`）。
  逐字引文核查**必须容多空格与 OCR 变体**，否则真引文会被报成未命中。

## Proposed Holdout cases

不从本路提取 holdout。现有 holdout 为四册单副本日记
（1864／1867／1871／1897），已跑过 `check_holdout_overlap`：硬失败 0。

## Handoff to adjudication

1. **诗作卷的逐条来源标记必须进边界文档**，与 andersonville 的 Atwater 段同级处理。
2. **风格判据只用明确标为她所写的讲稿**（src-830d04ae857d 一类），
   **不用诗作卷**——那一卷的作者身份逐条不同。
