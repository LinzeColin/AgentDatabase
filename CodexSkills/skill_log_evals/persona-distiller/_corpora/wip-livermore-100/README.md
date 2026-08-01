# Jesse Livermore #100 — 可续检查点（2026-08-01）

**状态：语料 + 同名门 + 分层入库全部完成，研究门只差六路正文。** 从第五节接着做。

## 一、这里有什么

| 文件 | 内容 |
|---|---|
| `HARVEST_REPORT.md` | 抓源全报告：150 份的逐条明细（**每条带可复现的 URL**）、16 条本人直引的逐字清单、8 条被剔除的误判及理由、端点实况 |
| `corpus_newspapers_149.tar.gz` | **149 份报纸语料**（Chronicling America / LoC，公共领域）。解开即用 |
| `split_book_1940.py` | 把 1940 年那本专著**按作者切开**（前言是 Dies 写的）。带 `--verify` 打印每段首尾 |
| `extract_windows.py` | 整版 OCR 截取工具。**本轮实测用不上**——抓源子代理已经做过窗口截取了 |
| `namesake_gate.BLOCKED.json` / `namesake_gate.json` | 同名门先 blocked（3 名候选）后 ready 的两份快照 |
| `livermore_namesake_*.json` | 候选与选定记录 |

## 二、★ 1940 年那本书**没有**放进来，必须自己重抓

`https://archive.org/details/how-to-trade-in-stocks-livermore-jesse-l-1940-duell-sloan-pearce-d-8d-4100576687`

**原因是版权状态存疑，不宜随仓库分发**：该副本属 `opensource` 集合、
上传者标了 CC public-domain mark，但来源署 "Anna's Archive"，
**1940 年注册件的美国续期状态未能独立核实**（Stanford 续期库被 Cloudflare 挡住）。
IA 的图书馆副本 `howtotradeinstoc0000live` 是 `access-restricted-item`（仅借阅）。

抓回来后跑：

```bash
python3 split_book_1940.py <书.txt> --outdir split --verify   # 先看边界
python3 split_book_1940.py <书.txt> --outdir split            # 再落盘
```

得到两份：`..._body_livermore.txt`（扉页 + 章节 I–IX，2898 非空行，**P1**）与
`..._preface_dies.txt`（64 非空行，**S1，作者 Edward Jerome Dies**）。

## 三、开工前必须知道的四件事

### 1. 头号陷阱：Edwin Lefèvre

《Reminiscences of a Stock Operator》(1923) **是 Lefèvre 写的小说**，
主角 **Larry Livingston 是虚构人物**。网上流传的绝大多数「Livermore 语录」出自这本小说。
实测：全书 `Livingston` 47 次 / `Livermore` 1 次；而他本人那本专著里
`Lefevre`／`Livingston` 出现 **0** 次。
Internet Archive 上有两个条目直接把这本小说题为 "Jesse Livermore Reminiscences…"——
**误归属是有实证的，不是假想**。

**任何 Lefèvre 文本一律不得标为他本人所写。** 若要就此立边界断言，
按 `S2` 入库、作者写 `Edwin Lefevre`、只进 `external` 路。

### 2. 他本人署名的材料**只有一种**

对全部报纸语料 grep `By Jesse L. Livermore` 命中 6 处，**逐条读后全部是假阳性**
（`managed by` / `statement by` / `engaged by`）。**没有任何署名报刊文章。**
Project Gutenberg 全库：Lefèvre 在册，**Livermore 本人 0 条**。

### 3. 直引只有 16 条，且抓源已剔除过 8 处误判

误判的说话人分别是：**他太太**（3 处）、**他的律师 Samuel F. Gillman**、
**国会议员 Mondell**、法庭上的另一名证人，以及同版面无关报道。
**引语核验必须核到「谁在说」，不能只核「这句在不在语料里」。**

### 4. OCR 状况（实测）

- 报纸语料（LoC）**干净**：149 份里只有 1 份含同形字，共 9 个字符。
- **那本书脏**：12.5 万字含 **1405 个西里尔同形字**、314 个全同形字词，
  连版权页的 `By` 都是西里尔的、`1940` 被认成 `1040`、`L.` 被认成 `1.`。
  → 取引文前先跑 `check_ocr_homoglyphs.py`（v0.0.0.17 起是发布门）。

## 四、下一步（从这里接着做）

1. 解开 `corpus_newspapers_149.tar.gz`，重抓那本书并切开。
2. **先去重**：149 份里 **41 份的摘录正文在同一文件内重复出现 ≥2 次**
   （抓源脚本的产物特征）。不去重会顶高 holdout 重叠率、并让覆盖检查失准。
3. `ingest.py` 分层：
   - `P1` —— 书的正文段（作者 `Jesse L. Livermore`，`A-copyright` 有据，v0.0.0.18 起）
   - `P2` —— 149 份同期报道（**按 RUNBOOK 第 822 行：第三人称叙述体降 P2，
     只有明确标注的直接引语可引**）。1942 / 1949 两份是身后回顾，建议降 `S1`
   - `S1` —— Dies 的前言
   - `S2` —— Lefèvre 小说（若要立边界断言才入）
4. holdout 按四步顺序（清洗→取样→抽取→隔离）抽定，**抽样前不许读**。
5. `quality_check --phase research --strict`。
   profile 当前是 **deep**（`min_sources` 45／`min_primary_ratio` 0.65／六路全覆盖）。
   六路的预判：`writings` 靠那本书、`conversations` 只有 8 份带直引的（**最薄的一路**）、
   `expression` 按第 822 行只能靠书 + 16 条直引、`external`／`decisions`／`timeline` 充裕。
   **`conversations` 若过不了，走「降 profile 但内容评分门自加」的既定退路**（Steinhardt #98 先例），
   并把限制写进 team-card 硬边界，**不许灌次级源凑数**。


---

# 五、【2026-08-01 续】入库已完成，研究门只剩一项

## 实测

```
$ python3 prep_livermore.py --raw <raw> --clean <clean> --target <t> --skill <s>
去重：149 份，压掉重复段 509 处
holdout（报纸，按 sha256(文件名) 取前 2）：
  ['jl_1935_thewashingtontim_065.txt', 'jl_1937_thewashingtontim_071.txt']
ingest：成功 149，失败 0

$ python3 scripts/quality_check.py <t> --phase research --strict
passed: False
  primary_ratio: 0.9799   usable train: 149   holdout: 3
  lanes: {'writings': 1, 'conversations': 8, 'expression': 1,
          'external': 148, 'decisions': 148, 'timeline': 148}
  authorship: {"P1 声称为本人所著": 2, "已证实归属": 2}
ERRORS: ['research.lane-completion']
   - completed source-linked lanes 0 < profile minimum 6: []
```

**唯一未过的是六路正文没写。** 来源侧全部达标：deep 要 45 源 / 0.65 一手，
实得 **149 源 / 0.980**，六路来源全覆盖，归属 2/2 证实。
`source-ledger.jsonl` 已随本目录提交，可直接比对。

## 分层结果

| 层 | 数 | 是什么 |
|---|---:|---|
| `P1` | 2 | 那本书的 train 卷（17,444 词）与 holdout 章（4,508 词），**两条都由 `A-copyright` 证实** |
| `P2` | 147 | 1907–1940 同期报道 |
| `S1` | 3 | Dies 的前言 + 1942 / 1949 两份身后回顾 |

## 三个必须随分数一起说的限制

### 1. `writings` 与 `expression` 各只有 **1 个来源**

就是那本书。deep 只要求每路 ≥1 源，形式上过得去，
**但语体与写作模型实际建立在单一文本上**。必须写进 team-card 硬边界。

### 2. `conversations` 只有 8 份——**这里我抓到过自己一次**

`dims_for()` 第一版写成 `if quotes > 0 or name in QUOTE_FILES`，
该路立刻涨到 **40**。而抓源报告第四节白纸黑字写着：自动检测器的候选
大量是**他太太、他的律师、国会议员、同版面无关报道**在说话。

> **拿一个自己都声明不可靠的信号去填车道计数，就是把门喂饱。**

已改为只认人工核过的那 8 份，该路回落到 8。

### 3. ★ holdout 章的归属证据是**本流程抄进去的**

章节页本身没有扉页，`A-copyright` 判它「无据」——**这是对的**。
处置是把该卷版权页的逐字原文（`COPYRIGHT, 1040, BY / JESSE 1. LIVERMORE`）
抄进文件头部并标 `[provenance]`。

**这一步必须留在明面上**：它让一份文件「自带」了原本不在其中的证据。
陈述本身为真（这一章确实出自那一卷），与报纸语料带 `SOURCE-URL:` 头同性质。
**但要知道这条路是开着的**——归属门防的是「别人的文章被顺手冠上人物名」这类疏忽，
**防不住有意粘贴**。

## 六、下一步

1. **写六路正文**（`references/research/*.md`，每路 ≥500 字、逐句挂 source_id）。
   这是唯一挡住研究门的一项。**判断密集，不外包。**
2. 断言 → 文档 → 32 用例 → 2 席评委（≤3 轮，指令按人物冻结）。
3. 取引文前先跑 `check_ocr_homoglyphs.py`：那本书 train 卷含
   **1284 个西里尔同形字 / 280 个全同形字词**，holdout 章另有 97 / 29。
   **报纸语料基本干净**（149 份里只有 1 份含 9 个字符）。


---

# 七、【2026-08-01 再续】抓源子代理最终收口于 **542 份**，已按全量重灌

## ⚠ 先看这条：第一版的数字是**中间态**

我第一次读报告时它抓到 **150 份**，写下「8 份带直引 / 16 条」并据此建了库。
子代理后来继续抓到 **542 份**，终值是 **14 份带直引 / 28 条**。

> **中间态的清单不要留着当终版用。** 已按终版全量重灌。

## 语料存放位置（**不在 git 里**）

```
~/Downloads/蒸馏/_corpora/livermore-100/
    corpus_newspapers_541.tar.gz          541 份报纸（LoC，公共领域）
    jl_1940_HowToTradeInStocks_01.txt     那本书的原始 OCR
    jl_1940_book_TRAIN.txt                切好的 train 卷
    jl_1940_book_HOLDOUT_chapter.txt      切好的 holdout 章（含 [provenance] 头）
    jl_1940_HowToTradeInStocks_preface_dies.txt
```

**放 D 档而不是 git 的理由**：7.9 MB 一个人物，600 人就是 4.7 GB，
**这个量级不能进仓库**。D 档按用户 2026-07-29 的裁定**留到 600 人全部完成后才清**，
且 `HARVEST_REPORT.md` 里每一条都带可复现 URL（重抓约 73 分钟）。
本目录只留报告、脚本与账本。

## 全量实测

```
去重：541 份，压掉重复段 1645 处
holdout（报纸，sha256(文件名) 前 3）：
  jl_1922_thebuffalovoice_419 / jl_1926_eveningstar_462 / jl_1935_thewashingtontim_065
ingest：成功 541，失败 0

$ quality_check --phase research --strict
  primary_ratio  : 0.9887   usable train: 532   holdout: 4
  own_voice_ratio: 0.0076   ← v0.0.0.19 新增
  lanes: {'writings': 1, 'conversations': 14, 'expression': 1,
          'external': 531, 'decisions': 531, 'timeline': 531}
  authorship: {"P1 声称为本人所著": 2, "已证实归属": 2}
ERRORS: ['research.lane-completion']       ← 仍然只差六路正文
```

## ★ 这一版最重要的一个数

| 量 | 值 |
|---|---|
| `primary_ratio` | **0.9887**（deep 要 0.65） |
| `own_voice_ratio` | **0.0076** |

**两个都是对的，差 130 倍。** 532 份可用 train 里 530 份是同期报纸**对他的报道**，
按 RUNBOOK 第 822 行它们是 `P2`，而 `primary_ratio` 的分子是 `P1 ∪ P2`。

他一生可公开抓取的原话约 **22,500 词**，**97% 压在那一本书上**；
去掉那本书只剩约 **600 词**。Lefèvre 那本小说 **112,180 词**，
是他全部存世文字的 **5 倍**——**这就是「Livermore 语录」绝大多数出自小说的结构性原因。**

**这两个数必须一起写进 team-card 硬边界。**

## 抓源子代理指出的两件事

1. **1923-12-21 参议院公共土地委员会宣誓证词的印本全文**
   （*Leases upon Naval Oil Reserves* hearings）确认存在但取不到
   （archive.org 无此卷、HathiTrust 被 Cloudflare 挡）。
   **这是唯一可能提供数千词逐字问答的一手材料，值得人工补。**
   补到了，`conversations` 与 `expression` 两路的单点风险会实质缓解。
2. 高价值实得项：**1908-05-15 棉花逼仓当日访谈**、
   **1923-12-21 参议院证词摘要**、**1940-09-22 死前两月最后一次市场评论**、
   **1940-11-29 遗书**。
