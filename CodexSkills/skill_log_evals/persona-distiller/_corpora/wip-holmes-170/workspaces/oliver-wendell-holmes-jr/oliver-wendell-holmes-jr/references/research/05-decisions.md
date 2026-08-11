# Decisions and actions

## Scope and assigned sources

**本道分到 6 份（train split）**：

| source_id | 出版年 | tier | 题名 |
|---|---|---|---|
| `src-fbc3bb4680f2` | 1884–1896 | P1 | Massachusetts Reports: Cases Argued and Determined in the …的扫描件，**题名页原文本轮取不到，如实标注，不代填。** |
| `src-737ead5f32e1` | 1893–1900 | P1 | Massachusetts Reports: Cases Argued and Determined in the …的扫描件，**题名页原文本轮取不到，如实标注，不代填。** |
| `src-11c067343c4d` | 1900–1903 | P1 | Massachusetts Reports: Cases Argued and Determined in the …的扫描件，**题名页原文本轮取不到，如实标注，不代填。** |
| `src-4daf4f3927bc` | 1903–1909 | P1 | United States Reports, Volumes 187–214（October Terms，判决日期 …00 U.S. 题名页逐字照录见 attribution。 |
| `src-2bba40c2b8a4` | 1905–1930 | P1 | United States Reports, Volumes 195–280（October Terms，判决日期 …49 U.S. 题名页逐字照录见 attribution。 |
| `src-5f7df25e761f` | 1919–1930 | P1 | United States Reports, Volumes 248–281（October Terms，判决日期 …49 U.S. 题名页逐字照录见 attribution。 |

★ 本节由台账机械导出（`emit_lane_scope.py`），**不含任何阅读判断**；只投影 `split == train` 的行。

## Source-linked observations

### ★ 本道语料里有一大块不是他写的——已在抓源指令里写死

*U.S. Reports* 每则判例开头的 **syllabus（判决要旨）由 Reporter of Decisions 编写**，
案由、当事人、律师姓名、程序史同样出自书记官。抓源方按指令**只取他主笔的意见与他署名的
异议／协同意见**，本道观察只建立在这一层上。**这与 #169 Blackstone 的编者注是同一类问题**
（署名页写着他，正文里混着别人），区别是那里有 `(27)` 这样的显式记号，
而这里 syllabus 与意见正文在纯文本里往往只隔一个空行。

本道各文件已由抓源方切成 `=== <案号> | <案名> | decided <日期> | ... ===` 的条目，
条目头写明该则是 `majority by` 还是 `dissent by`。**分层是抓源时做的，不是我事后判的。**

### 规模（`===` 条目计数，机械数出）

| 源 | 层 | 则数 |
|---|---|---|
| `src-4daf4f3927bc` | 多数意见 | 191 |
| `src-5f7df25e761f` | 多数意见 | 305 |
| `src-2bba40c2b8a4` | 异议／协同意见 | 68 |

1. **写多数意见时，他把自己从句子里拿掉。** `src-4daf4f3927bc`（1903-02-02）：
   `Me. Justice Holmes delivered the opinion of the court`（`Me.`＝`Mr.` 的 OCR 讹形，照录未改），
   通篇以 `we`／`the court` 行文，第一人称 `I` 实测 2.7／万词。
   `src-5f7df25e761f`（1919）同样：`We admit that in many places and in ordinary times
   the defendants in saying all that was said in the circular would have been within
   their constitutional rights`。

2. **写异议时，他把自己放回去。** `src-2bba40c2b8a4`（1905-04-17）：
   `I rtegret sincerely that I am unable to agree with the judgment in this case,
   and that I think it my duty to express my dissent`（`rtegret` 为 OCR 讹形，照录未改）。
   该卷 `I` 实测 130.2／万词，`I think` 55,064 词里 127 次。
   → **同一份职务、同一年、相差 48 倍**。体裁决定第一人称的位置，不是他的性格在变。

3. **异议的第一步是把自己的权限与自己的意见分开。** 同则：
   `This case is decided upon an economic theory`，随即
   `I strongly believe that my agreement or disagreement has nothing to do with
   the right of a majority to embody their opinions in law`。
   → 这是 03 道 C11 的第二簇：**先说「我同不同意不算数」，再说为什么判决错了。**

4. **判准写成可操作的检验句，不写成原则。** `src-5f7df25e761f`（1919）：
   `The question in every case is whether the words used are used in such circumstances
   and are of such a nature as to. create a clear and present danger that they will bring
   about the substantive evils that Congress has a right to prevent`，并当场收口：
   `It is a question of proximity and degree`。
   → 与 01 道 C2（检验标准是可预测性）同形：**给一个下次能照着用的问句。**

5. **给自己的职业能力划界，并把界外的事交出去。** `src-4daf4f3927bc`（1903-02-02）：
   `It would be a dangerous undertaking for persons trained only to the law to constitute
   themselves final judges of the worth of pictorial illustrations, outside of the narrowest
   and most obvious limits`。
   → **他用「我这行不擅长这个」当判决理由**，而不是用它当谦辞。

6. **旧立场不撤回，也不重述，只标注仍然有效。** `src-2bba40c2b8a4`：
   `I still entertain the opinions expressed by me in Massachusetts`。
   → 03 道 C10（给自己的说法打时间戳）的第二簇。

7. **他把制度本身说成可错的试验。** `src-2bba40c2b8a4`（1919）：
   `the best test of truth is the power of the thought to get itself accepted in the
   competition of the market`，紧接
   `That at any rate is the theory of our Con- A stitution. It is an experiment, as all life
   is an experiment`（`Con- A stitution` 为版口噪声，照录未改）。

## Candidate Claims

- **C12（work-method）**：按体裁切换人称——代表机构时用 `we`，代表自己时用 `I`，两者不混。
  证据：第 1、2 条（三源、两语境、两簇）。
- **C13（mental-model）**：「我是否同意」与「我是否有权干预」是两个独立问题。证据：第 3 条 + 03 道第 5 条。
- **C14（work-method）**：判准落成一句可复用的检验句，并当场声明它是程度问题。证据：第 4 条 + 01 道。
- **C15（boundary）**：以职业能力边界作为拒绝裁断的正当理由。证据：第 5 条。

## Contradictions and alternative explanations

- 第 1、2 条的人称差异**几乎肯定有司法惯例的成分**（多数意见代表法院，惯例即用 `we`）。
  本工作区无同院其他法官的对照文本，**分不开「惯例」与「他的选择」**。
  → 产物里只能说「他在两种体裁里的人称是分开的」，**不许说成他独有的写法**。
- 第 7 条常被当作他的政治信条；原文语境是**言论管制案的异议**，
  射程是宪法解释，不是普遍世界观。两种读法都留。

## Unknowns and source gaps

- 合议过程、初稿、同僚往还**全部不可得**（书信集印本年在 PD 分界之后，本项目不取）。
  → **「他为什么这样判」只能从判词本身读，不能从过程读。**
- 州法院期（1883–1902）三份合计 93 万词，本轮只做了体裁级的人称统计，
  **未逐则读**；本道 1–7 条的观察全部取自联邦期。

## Proposed Holdout cases

IDs only; research Agents must not inspect Holdout bodies.

## Handoff to adjudication

C12–C15 四条中，C12／C13／C14 已具备跨道第二簇，交合流；C15 只有本道一簇，
按对具体判词的事实陈述记，**不升为方法类断言**。
