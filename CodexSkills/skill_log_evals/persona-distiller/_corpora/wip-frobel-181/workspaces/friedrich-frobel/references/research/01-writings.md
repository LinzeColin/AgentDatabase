# Writings and systematic works

## Scope and assigned sources

**本道分到 30 份（train split）**：

| source_id | 出版年 | tier | 题名 |
|---|---|---|---|
| `src-78c284144dcf` | 1862 | P1 | Gesammelte pädagogische Schriften |
| `src-0e9685ee5c80` | 1863 | P1 | Die Menschenerziehung und Kussäke verschiedenen Inhalts |
| `src-18b6090f5f15` | 1863 | P1 | Friedrich Fröbel's gesammelte pädagogische Schriften. 1,2 |
| `src-e2268900dcc4` | 1885 | P1 | La educación del hombre |
| `src-3bab9a30dc87` | 1887 | P1 | The education of man |
| `src-dd6af8da94b3` | 1887 | P1 | The education of man |
| `src-cc7abad9b0a2` | 1888 | P1 | La educación del hombre |
| `src-c5b1c845ca63` | 1890 | P1 | The education of man |
| `src-393062b3c22a` | 1895 | P1 | Friedrich Froebel's pedagogics of the kindergarten |
| `src-4f056938f63e` | 1895 | P1 | Friedrich Froebel's pedagogics of the kindergarten |
| `src-b74213b6501a` | 1895 | P1 | Friedrich Froebel's pedagogics of the kindergarten |
| `src-fb6c24863e56` | 1895 | P1 | The mottoes and commentaries of Friedrich Froebel's Mother play |
| `src-36349185b8d9` | 1896 | P1 | The education of man ; |
| `src-3b1d8669e740` | 1896 | P1 | The student's Froebel adapted from Die erziehung der menschheit of F. Froebel |
| `src-464c59771f2d` | 1896 | P1 | The student's Froebel adapted from Die erziehung der menschheit of F. Froebel |
| `src-5f4c85ec8d34` | 1898 | P1 | The mottoes and commentaries of Friedrich Froebel's Mother play |
| `src-0ee0bb0ac3f7` | 1899 | P1 | Friedrich Froebel's Education by development |
| `src-206610b15226` | 1899 | P1 | Friedrich Froebel's Education by development, the second p…dagogics of the kindergarten; |
| `src-2ca0e80439a5` | 1899 | P1 | Friedrich Froebel's Education by development |
| `src-f32e3228c157` | 1899 | P1 | Friedrich Froebel's Education by development |
| `src-5a7b788a774a` | 1901 | P1 | The education of man |
| `src-82d4f0e78a25` | 1902 | P1 | Friedrich Froebel's Education by development |
| `src-8691d5260829` | 1902 | P1 | The mottoes and commentaries of Friedrich Froebel's Mother play |
| `src-a7db55db365f` | 1902 | P1 | Friedrich Froebel's Education by development, the second p…dagogics of the kindergarten; |
| `src-020c6b623301` | 1903 | P1 | The education of man |
| `src-265b964e5142` | 1903 | P1 | Friedrich Froebel's Education by development, the second p…dagogics of the kindergarten; |
| `src-5d88b1d62ecc` | 1909 | P1 | Friedrich Froebel's pedagogics of the kindergarten, or, Hi… and playthings of the child; |
| `src-42ae0c161d4f` | 1912 | P1 | Froebel's chief writings on education |
| `src-b9e8ee0a133a` | 1912 | P1 | Froebel's chief writings on education |
| `src-f9b18fc33e99` | 1916 | P1 | The student's Froebel : adapted from Die Menschenerziehung of F. Froebel |

★ 本节由台账机械导出（`emit_lane_scope.py`），**不含任何阅读判断**；只投影 `split == train` 的行。

## Source-linked observations

★★★ **本道的主要结论是一个否定结论：这批语料里几乎找不到他本人的第一人称。**

## 一、可用面比数字小得多

| 口径 | 数 |
|---|---:|
| 台账条数 | 51 |
| **译本**（元数据 ∪ 题名页） | **29（57%）** |
| **德文原文一手** | **4** |

`measure_voice` 报他 2.44/千词 —— **而那 2.44 里相当一部分不是他的**，见下。

## 二、机械摘取 6 条，**逐条人判后 0 条可作声口样本**

| 出处 | 为什么不是他 |
|---|---|
| 偏移 4024 | 说话人称 Louise Fröbel 为「**我的亲戚**」（`meinen Verwandten Frau Louiſe Fröbel`）——而她是**福禄贝尔的妻子**。⇒ 编者 |
| 偏移 1497 | `muß ich Anftand nehmen, das Motiv, welches **feiner** Seele vorſchwebte` ——「**他**心中的动机」。⇒ 编者 |
| 偏移 3238 | 「我几乎每个下午、常常连夜在**他**身边工作」。⇒ 编者 |
| 偏移 212338 | Fraktur OCR 崩坏，不可读 |
| 两条英文 | 第三人称传记（`This announcement was made in 1829 … in Froebel's breast`） |

★ 三条可读的第一人称**偏移都在 1500–4100**，即**卷首编者序之内**。
  他的《Gesammelte pädagogische Schriften》由 **Wichard Lange** 编订并作长序，
  **那一层的「我」是 Lange 的**。

## 三、跳过编者序、进正文深处之后，`ich` 仍然多半不是他

224 处（前 15% 之外）里抽查三处：

- 偏移 231957 —— `ihr würdet ſo durch mich das wahrhaft ewige Leben empfangen und ich
  würde euch das wahrhaft ewige Leben geben` ⇒ **那是基督在说话**（引用/化用经文）
- 偏移 278359 —— Fraktur 崩坏
- 偏移 334122 —— **唯一一条是他自己的**，见 O-1

### O-1 · 他的写法是**禁止读者说某一句具体的话**

> `Vater, Lehrer, Kinderführer antworte nicht: Davon weiß ich felbft noch nichts, das
>  kenne ich felbft noch nicht.`
> —— `src-0e9685ee5c80` @334122（`felbft`＝`selbst`，长 s 被 OCR 读成 f，**未改**）

★ 「父亲、教师、育儿者，**不要这样回答**：『这个我自己也还不知道，这个我自己也还不认识。』」
**句中的「我」是他替对方拟的推辞，祈使的那个人才是他。**
⇒ 他不写「应当如何」，他**先把对方会说的那句话写出来，再禁止它**。

---

## ★★ 处置建议：**按 Coffin #130 的先例对待**

Coffin 的情形是「三道门全过、17 万字里实质的话只有 8 句」。
Fröbel 这里更细一层：**门看到的 2.44/千词，主要来自编者序与引用的经文**。

⇒ **在补到更多德文原文之前，不要给他做声口向的断言。**
  事实与观点仍可用（《人的教育》正文是他写的），
  但「他会怎么说」这一面，**这批语料撑不住**。
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
