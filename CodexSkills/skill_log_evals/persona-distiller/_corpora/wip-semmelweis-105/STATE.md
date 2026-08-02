# #105 Ignaz Semmelweis —— 延后（第四类成因：**一手源全部到手，仍然不够**）

日期：2026-08-03　｜　蒸馏版本 `v0.0.0.36`　｜　状态：**延后，语料留档**

---

## 一、实测（全部实跑，非估计）

| 项 | 值 |
|---|---|
| 落盘语料 | **60 份，54.2 MB** |
| `check_corpus_integrity` | **61 份全是真文档，0 张错误页**（子代理自查 0 删，我复扫确认） |
| ingest | 60 条全部入账本 |
| tier 分布 | **P1 7 ／ S1 37 ／ S2 16** |
| **primary_ratio** | **0.1186** |
| 门槛 | deep 0.65 ／ standard 0.50 ／ **quick 0.40** |

**连最低的 quick 档都差 3.4 倍。**

## 二、★ 为什么这不是抓源没做够

**他一生只出版过 5 部作品，而这 5 部我全部拿到了：**

1. 《Die Aetiologie, der Begriff und die Prophylaxis des Kindbettfiebers》(1861)
   —— 主著，取自 Deutsches Textarchiv（`semmelweis_kindbettfieber_1861`），
   **990,732 字节的学术转录本，不是 OCR**，是全批语料里质量最高的一份
2. 《Gesammelte Werke》(1905，Győry 编) —— **磁盘上有 4 份，实为同一本书的四次 OCR**
   （逐份特征词计数验证：Chlor 256/436/324/372、Scanzoni 266/356/292/329，同型）
3. 《Zwei offene Briefe an Spaeth & Scanzoni》(1861)
4. 《Zwei offene Briefe an Siebold & Scanzoni》(1861)
5. 《Offener Brief an sämmtliche Professoren》(1862)
   —— **Fraktur 排印，OCR 报废**（德文虚词率 0.9%，干净德文扫描约 17%）。**不可引用。**
   同一封信的干净文本在《Gesammelte Werke》里。

**去重之后，真正可用的独立一手件是 5 部，其中 1 部不可引用。**

## 三、★★ 判据在这里的方向是反的

`primary_ratio` 是**比例**。他的分子被他一生的产量钉死在 5，
**分母却随我把外围史料收得越全而越大。**

> **史料收得越完整，比例越差。**
> 要把 11.9% 抬到 quick 的 40%，唯一的办法是**丢掉 45 份外围史料**——
> 而丢掉的正是同时代反对方（Scanzoni、Späth、Virchow、Michaelis）的材料，
> 也就是 `contrast` 套组唯一的依据。而 `contrast` 是四人合并里最差的一组（**−0.1281**）。

**为了过比例门去砍掉最需要的那批材料，是优化指标不是优化产物。不做。**

## 四、这一类与已有三类都不同

| 类 | 成因 | 例 |
|---|---|---|
| 一 | 一手源**抓不到**／比例不够 | Hopper、Hamilton、Simons、Swensen、Druckenmiller、Templeton |
| 二 | 一手源随手可取而**归属不成立** | Hippocrates |
| 三 | 语料充足、全流程走完，**判分不合格** | Galen、Vesalius、Harvey、Jenner |
| **四** | **一手源全部到手，而他一生只写了这么多** | **Semmelweis** |

第一类是「我没找到」，**第四类是「世界上就这些」**。
前者靠再抓一轮可能解决，**后者再抓一百轮也不会变**。

## 五、留在这里的东西（未删，可续）

- `raw/` 60 份语料、`raw/_ids.txt`、`raw/_fetch.log`
- `workspaces/ignaz-semmelweis/` 账本 60 条，tier 与 dimension 已标
- `ingest_semmelweis.py`（**注意：它的 `_ids.txt` 文件名匹配写得差，18 份靠前缀补灌**）

## 六、若日后解封，第一件事

**不是再抓源。** 是先决定一个口径问题：

> **`primary_ratio` 该不该对「著作少而重要」的人物设例外？**
> 若设，例外的判据是什么、由谁认定、怎么防止它变成万能豁免？

**在这个问题有答案之前，不许为他单独放宽任何一档。**
（判据出错与判据被绕开表征相同——本项目已踩过三次。）
