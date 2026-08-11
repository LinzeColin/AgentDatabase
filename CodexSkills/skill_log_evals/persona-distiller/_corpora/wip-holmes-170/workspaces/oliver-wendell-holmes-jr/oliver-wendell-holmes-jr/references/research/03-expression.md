# Expression DNA and micro-behavior

## Scope and assigned sources

**本道分到 5 份（train split）**：

| source_id | 出版年 | tier | 题名 |
|---|---|---|---|
| `src-96246ca9968e` | 1884 | P1 | Dead, Yet Living. An Address Delivered at Keene, N. H., Me…inn, Heath, and Company. 1884 |
| `src-de206b40fe7b` | 1891 | P1 | Speeches. By Oliver Wendell Holmes, Junior. Boston: Little… and Son, Cambridge）——初版，11 篇 |
| `src-4c4e28b10d9c` | 1913 | P1 | Speeches. By Oliver Wendell Holmes. Boston: Little, Brown,… Cambridge, U.S.A.）——增订本，18 篇 |
| `src-c7a49bbb129f` | 1913 | P1 | Speech of Mr. Justice Holmes at a Dinner of the Harvard La…245／260；封面 OCR 见 attribution） |
| `src-48135d4164bd` | 1920 | P1 | Collected Legal Papers. By Oliver Wendell Holmes. New York…ress, Norwood, Mass., U.S.A.） |

★ 本节由台账机械导出（`emit_lane_scope.py`），**不含任何阅读判断**；只投影 `split == train` 的行。

## Source-linked observations

### ★ 先把声口密度量出来，再谈声口（Coffin #130 的教训）

判决意见能把来源数与一手占比撑得很高，**而它是机构文书**。本工作区逐份实测
（`[A-Za-z']+` 分词，独立词 `I` 的每万词频次）：

| 体裁 | 源 | 词数 | `I`／万词 | `we`／万词 |
|---|---|---|---|---|
| 讲词单行本 | `src-c7a49bbb129f` | 1,901 | **168.3** | 152.6 |
| 讲词单行本 | `src-96246ca9968e` | 4,337 | **161.4** | 113.0 |
| 讲词集 | `src-4c4e28b10d9c` | 28,434 | **157.9** | 86.9 |
| 讲词集 | `src-de206b40fe7b` | 15,037 | **155.0** | 71.8 |
| 论文集 | `src-48135d4164bd` | 87,768 | **120.3** | 43.2 |
| 专著 | `src-6deab2cc96a0` | 136,876 | 31.1 | 15.5 |
| **异议／协同意见** | `src-2bba40c2b8a4` | 55,064 | **130.2** | 26.5 |
| 多数意见 | `src-4daf4f3927bc` | 286,032 | 2.7 | 50.6 |
| 多数意见 | `src-5f7df25e761f` | 277,561 | 3.7 | 40.7 |
| 州法院意见 | `src-11c067343c4d` | 243,924 | 2.0 | 52.8 |

★★★ **同一个人、同一份职务、相差 35–65 倍**：他写多数意见时是 2.0–3.7，
写异议时是 130.2。**异议层在声口上更接近他的讲词，而不是他自己的多数意见。**
`I think` 一词：异议卷 55,064 词里 127 次，多数意见 286,032 词里 3 次。

**这个数不是靠计数下的结论**：随机抽 14 处异议里的 `I` 逐条读过，
14 处全部是实质判断（如 `The principle that I think should govern is the same
that I stated in`、`I cannot see what that policy has to do with`），
**没有一处是 `I concur` 之类的套语**。[[measured-voice-in-the-wrong-register]]

### 具体手法

1. **对仗式的否定—肯定。** `src-6deab2cc96a0`：
   `The life of the law has not been logic : it has been experience`。
   同型见 `src-48135d4164bd`：`the black-letter man may be the man of the present,
   but the man of the future is the man of statistics and the master of economics`。
   → **句子本身就是「拒绝 A／改取 B」的结构**，不需要额外的过渡句。

2. **把抽象命题降到一个可以想象的人身上。** `src-48135d4164bd`：
   `you must look at it as a bad man, who cares only for the material consequences`；
   `src-48135d4164bd`（1918）：`It is not enough for the knight of romance that you agree
   that his lady is a very nice girl`。
   → 一个角色、一句话、命题成立。

3. **用极端例子做量尺。** `src-48135d4164bd`：
   `There is in all men a demand for the superlative, so much so that the poor devil
   who has no other way of reaching it attains it by getting drunk`。

4. **对自己早年的说法明确标注是早年的。** `src-48135d4164bd`：
   `I used to say, when I was young, that truth was the majority vote of that nation
   that could lick all others`。
   → **他会给自己的话打时间戳**，而不是让它显得永远成立。这一条与 05 道
   `I still entertain the opinions expressed by me in Massachusetts` 是同一习惯的两面。

5. **把自己的立场限定在「我的位置允许我做什么」。** `src-2bba40c2b8a4`（1905-04-17）：
   `I strongly believe that my agreement or disagreement has nothing to do with
   the right of a majority to embody their opinions in law`。
   → **先划自己的权限，再谈内容**——与 01 道序言里的射程声明同形。

## Candidate Claims

- **C8（expression）**：句式常自带「否定—改取」的对仗，主张与其替代项同句出现。证据：第 1 条（两源）。
- **C9（expression）**：以单个可想象的角色承载抽象命题。证据：第 2、3 条。
- **C10（work-method）**：给自己的旧说法打时间戳，不让它默认仍然成立。证据：第 4 条 + 05 道。
- **C11（mental-model）**：区分「我同不同意」与「我有没有权限管」。证据：第 5 条 + 01 道射程声明。

## Contradictions and alternative explanations

- 声口密度表的**语域混杂风险**：`I` 在多数意见里少，是司法惯例（用 `the court`／`we`），
  **不能据此说他写多数意见时「没有自己」**——只能说该体裁不给第一人称位置。
  产物里必须按体裁分开表述，不许合并成一个「他的第一人称密度」。
- 第 1 条的对仗句式可能是**19 世纪散文的一般风格**；本工作区无同代人对照材料，
  故 C8 只记为 `expression`，不升为方法类。

## Unknowns and source gaps

- 无手稿、无修改稿：**成句过程不可见**，以上全部是成品特征。
- 讲词集两版之间的字句改动未逐篇比对（见 02 道同一条缺口）。

## Proposed Holdout cases

IDs only; research Agents must not inspect Holdout bodies.

## Handoff to adjudication

C10／C11 已有跨道第二簇候选（05 道），交合流；C8／C9 单道成立，按 `expression` 记。
