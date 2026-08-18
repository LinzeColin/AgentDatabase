# External views, criticism, and counterexamples

## Scope and assigned sources

**本道分到 11 份（train split）**：

| source_id | 出版年 | tier | 题名 |
|---|---|---|---|
| `src-6f12ff5b72d3` | 1869 | S1 | Obraz Jednoty eskobratrské ili Jana Lasitského Historie o …od Jana Amosa Komenského 1649 |
| `src-0e8f5a68d4b2` | 1892 | S1 | Johann Amos Comenius, sein Leben und Wirken |
| `src-50d0026dd459` | 1892 | S1 | Johann Amos Comenius. Sein Leben und seine Schriften |
| `src-d2cefc4ca2e2` | 1892 | S1 | Johann Amos Comenius. Sein Leben und seine Schriften |
| `src-ed8705a21c04` | 1892 | S1 | Leben und Schicksale des Johann Amos Comenius |
| `src-056c8f9a43bb` | 1904 | S1 | Johann Amos Comenius. Sein leben, seine pädagogischen schriften und seine bedeutung |
| `src-179871314a74` | 1904 | S1 | Johann Amos Comenius. Sein leben, seine pädagogischen schriften und seine bedeutung |
| `src-2d3d83165375` | 1904 | S1 | Johann Amos Comenius. Sein leben, seine pädagogischen schriften und seine bedeutung |
| `src-af3be0a7e20d` | 1904 | S1 | Johann Amos Comenius. Sein leben, seine pädagogischen schriften und seine bedeutung |
| `src-f3915d74323b` | 1904 | S1 | Johann Amos Comenius. Sein leben, seine pädagogischen schriften und seine bedeutung |
| `src-ca28b8af05fc` | 1920 | S1 | Der Rhein als Schicksal : oder, Das Problem der Völker |

★ 本节由台账机械导出（`emit_lane_scope.py`），**不含任何阅读判断**；只投影 `split == train` 的行。

## Source-linked observations

Pending.

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

## 本道读了什么

**只读下列 2 份第三方著述**（均为他身后的传记/教会史，非他本人所著）。
**未列出的一律未读、未引。**

| source_id | 年 | 用它证明什么 |
|---|---|---|
| `src-50d0026dd459` | 1892 | 关于他的基本事实**至今有争议**，而争议双方常不给出处 |
| `src-179871314a74` | 1904 | 决定他后半生的那件事**不是他能左右的** |

## 一、★ 连他的出生地都有两百年的分歧 —— 而且写的人不给出处

> `ſchon jeit zwei Yahrhunderten die Meinungen über den Geburtsort des Comenius jehr auseinandergehen. Einige fchrieben Niwnitz,) ohne die Duelle dafür anzugeben. Andere waren` <!-- src-50d0026dd459 -->

★ 这条直接约束替他作答的射程：**凡涉及他生平细节，须先说明该细节有无定论**。
本库的候选卡里写的「出生地不确定 —— 墓碑记 Uherský Brod，另有 Nivnice 与 Komňa 两说」，
与这份 1892 年的德文传记**互相印证**：分歧是真的，不是本库材料不足造成的。

## 二、决定他后半生的那件事，不由他决定

> `blieb und erſt durch den Tod des Comenius gelöjt wurde), jo wirkte auf ihn und alle Mitglieder der Brüder-Unität die - Nachricht, Die „Brüder“ ſeien beim weſtfäliſchen Frieden ausgejchloffen worden, wahrhaft niederjchmetternd. Denn nun war n` <!-- src-179871314a74 -->

★ 兄弟会在《威斯特伐利亚和约》里**被排除在外**的消息，
对他和全体成员是沉重打击。⇒ 替他作答时，
**流亡与失所不能被讲成「他选择的路线」**，那是被外部条约切断的结果。

## 三、本道**不能**证成的

· 以上两份都是**第三方叙述**，不是他自己的话。**不得转成第一人称自述。**
· 本轮未取到与他同代人的往还书信、也未取到对他方法的同代批评；
  ⇒ 「同代人怎么评价这套方法」在本库里**尚无材料**，
  **这是「未取」，不是「不存在」。**

## ★ 本道引文的语料质量（判据现算，不是我说的）

| source_id | `check_ocr_longs_corruption` 判定 |
|---|---|
| `src-179871314a74` | **不可用** |
| `src-50d0026dd459` | **不可用** |

★★ 本道引用的 2 个源里，**2 个被判「不可用」**——
判据的原话是「**从这些文件里取不出任何可核的逐字引文**」（长 s 讹字：esse→esfe、such→fuch）。

⇒ **本道的引文只可用于「结构与次序」**（章节标题、页码先后、编制单位数），
   **不得当作他的用词证据**：`fimili` 之类的字形是 OCR 的，不是他的。
   另一把尺 `check_lane_quotes_verbatim` 说这些引文「对得上」——**两句话都对**：
   引文忠实于语料，而语料本身不忠实于印本。
