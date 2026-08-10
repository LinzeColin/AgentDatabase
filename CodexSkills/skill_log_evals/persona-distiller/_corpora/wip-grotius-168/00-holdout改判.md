# Grotius #168 holdout 改判 —— 密封整部 De Veritate

> 2026-08-11 写在动手之前。所有数字都是本机跑出来的，复算脚本见文末。
> **本人物尚未产生任何分数**（claims 0 行、cases 0 行、results 0 行，研究道正文全是 `Pending.`），
> 因此这不是「中途改尺子」——尺子还没开始量。

## 一、要改的是什么

第一版建工作区时我把 holdout 定成 `de_veritate_leclerc_1809_en`（1809 英译），
**而同一部作品的拉丁本 `de_veritate_1640_lat` 留在 train 里当 P1**。

| | source_id | 题名（台账 title 字面） | 原 split |
|---|---|---|---|
| holdout | `src-cb4b5545eb76` | The Truth of the Christian Religion… | holdout |
| train | `src-aa617a65bf8d` | De Veritate Religionis Christianae… | **train** |

一边密封、一边喂料，**同一部作品**。这从台账题名就看得见，不需要任何工具。

## 二、判据为什么没报

`check_holdout_overlap` 对这一对报 **0.007%**——比一对确定不同的作品（0.061%）还低 9 倍。
它按内容重叠判，而**跨语种重叠恒为 0**，判据文件头自己写着这条射程。

★ 所以：**这个人物的 holdout 门报绿，不构成隔离成立的证据。**

## 三、为什么不采用「换成 de_iure_praedae 当 holdout」

替代方案曾是：把 `de_iure_praedae_1869_lat` 设为 holdout，三份 De Veritate 全进 train。
**实测否掉了它**——De Iure Praedae 第 12 章的大部分就是 *Mare Liberum*，
而 Mare Liberum 的拉丁本与英译本**两份都在 train 里**。换过去只是把破口从一部作品挪到另一部。

一手依据（1869 本编者序逐字，本文件内可回读）：

> `Post Historica sequitur caput duodecimum, cujus major pars Maris liberi titulo separatim edita est.`

★ 注意是 `major pars`（大部分），不是全章——不要写成「Mare Liberum 就是第 12 章」。

### 实测（用 `check_source_dedup` 自己的 shingles/containment，数值与 0.30 那道门可比）

**先解决一件事：判据默认的 n=8 在这批语料上够不到自己的门。**
两对**我确知是同一部作品、同一种语言**的标定对，在 n=8 上只读到 0.017/0.021。

于是扫 n=1…8，让已知同/异自己把缝划出来（字形归一：f→s、v→u、j→i）：

| 对 | 真值 | n=2 | n=3 | n=4 | n=5 | n=6 | n=8 |
|---|---|---:|---:|---:|---:|---:|---:|
| DJBP 1646lat × 1853lat vol1 | **同** | 0.263 | 0.146 | 0.093 | 0.063 | 0.043 | 0.021 |
| De Veritate 1640lat × 1813lat | **同** | 0.297 | 0.171 | 0.103 | 0.063 | 0.040 | 0.017 |
| ★ de_iure_praedae 1869 × mare_liberum 1618 | ? | 0.272 | **0.136** | 0.076 | 0.044 | 0.026 | 0.010 |
| 诗集 × 论著 | 异 | 0.027 | 0.001 | 0.000 | 0.000 | 0.000 | 0.000 |
| 书信 × 论著 | 异 | 0.034 | 0.001 | 0.000 | 0.000 | 0.000 | 0.000 |

- **n=3 分离度 117 倍**（同 ≥0.146 / 异 ≤0.0012），待判那对 = 0.136 → **落在同作品一侧**；n=2/4/5/6 五档结论一致。
- 分母取短的一侧（Mare Liberum 107 KB vs De Iure Praedae 784 KB），
  所以这就是「ML 整个落在 DIP 里」的形状，与编者序自述同向。
- 正对照（自己比自己）= 1.0000，仪器是活的；负对照在 n≥3 上为 0，归一没有制造底噪。

★ 元数据代理的报告写「`mare_liberum_1618_lat` 在这里没有发言权」，因为它 OCR 已死、n=8 只读到 0.33%。
**发言权是能还回来的**：把 n 降到 3 并做字形归一后，它与两对「坏 OCR × 干净重排本」的标定对读数同量级。
结论与代理一致，但依据不再是「读不出来所以不算数」。

## 四、定下来的做法

**把整部 De Veritate 密封**——它在 train 侧的存在归零：

| 文件 | source_id | 新 split | 理由 |
|---|---|---|---|
| `de_veritate_leclerc_1809_en` | `src-cb4b5545eb76` | holdout（不变） | 原 holdout |
| `de_veritate_1640_lat` | `src-aa617a65bf8d` | **train → holdout** | 同一部作品，堵住破口 |
| `de_veritate_1809_lat`（新） | `src-c34ffc3b8b9e` | **不 ingest** | 同属密封作品，进 train 会重开破口；进 holdout 无增益 |
| `de_veritate_1813_lat`（新） | `src-454307a1425a` | **不 ingest** | 同上 |

同时引进四份新语料到 train（理由见第五节）：

| 文件 | source_id | split |
|---|---|---|
| `djbp_1853_lat_vol1` | `src-8651f2b87336` | train |
| `djbp_1853_lat_vol2` | `src-d3bf3e7d3c8f` | train |
| `djbp_1853_lat_vol3` | `src-576d609b0ef0` | train |
| `de_iure_praedae_1869_lat` | `src-19eca701ec61` | train |

★ 四个 source_id 是**我自己算 sha256 验过的**，不是照抄报告的预测（报告预测的三个也确实对上）。

**没有放宽任何判据。** 改的是这个人物的材料划分，判据一行没动。

### 门的算术（改判后）

台账 23 份 = train 21 + holdout 2。

| 门 | 要求 | 改判后 | |
|---|---|---|---|
| min_sources | 8（真实下限 9） | 23 | ✔ |
| min_primary_ratio | 0.40 | 17 P1 / 21 = **0.810** | ✔ |
| min_lanes | 3 | writings / conversations / expression / external = 4 | ✔ |

## 五、为什么引进那四份：**不是「多几份源」，是第一次有能逐字引的拉丁文**

现有 8 份拉丁源的长 s 讹字率（8 组词对面板，正形 vs 讹形）：

| 文件 | 讹字率 | 判读 |
|---|---:|---|
| `mare_liberum_1618_lat` | 98.37% | 逐字引文不可用 |
| `epistolae_ineditae_1806_lat` | 98.39% | 同上 |
| `annales_1658_lat` | 98.14% | 同上 |
| `djbp_1646_lat` | 97.76% | 同上 |
| `epistolae_1687_lat` | 96.62% | 同上 |
| `de_veritate_1640_lat` | 96.67% | 同上 |
| `poemata_1637_lat` | 93.53% | 同上 |
| `epistolae_oxenstierna_1829_lat` | 69.63% | 同上（见下方 ★） |

四份新语料：`de_iure_praedae_1869` **0.06%**、`djbp_1853_vol1` 0.19%、`vol2` 0.31%、`vol3` 0.55%。

**结论：这个人物此前一句拉丁逐字引文都引不了。** 断言层要用一手拉丁原文，只能靠这四份。

### ★★ 附带查出的一个探针缺陷（值得单独落地）

`epistolae_oxenstierna_1829_lat` 是矛盾样本：`est/eft = 162/1`（看着干净），`esse/esfe = 0/74`（全坏）。
去读原文，L198 同一行上就有：

> `nomen est, commendandam esfe cenfuit, qiio`

真因是**排版惯例**：`st` 用连字（短 s），其余位置用长 s。所以：

| 探针 | 读数 | 判读 |
|---|---:|---|
| 只用 `est/eft` | **0.61%** | 判为「可用」 |
| 去掉 `est` 的其余 7 对 | **97.75%** | 逐字引文不可用 |

**单对探针在这里低估 160 倍**，而 `est/eft` 恰是这个面板里最常用的第一对。
面板救了这一次，只因为它还有另外 7 对。→ 已落成判据 `check_longs_corruption.py`。

## 六、复算

```bash
python3 grotius_shingle_n_sweep.py   # 第三节的 n 扫描表
python3 grotius_longs_panel.py       # 第五节的讹字率表
python3 scripts/check_longs_corruption.py --self-test
```
