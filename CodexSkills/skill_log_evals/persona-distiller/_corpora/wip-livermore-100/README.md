# Jesse Livermore #100 — 可续检查点（2026-08-01）

**状态：语料与同名门完成，尚未 ingest。** 从下面第四节接着做。

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
