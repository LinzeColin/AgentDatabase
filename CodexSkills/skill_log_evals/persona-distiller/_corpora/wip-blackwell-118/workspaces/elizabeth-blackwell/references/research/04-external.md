# 外部评述（`external`）

**train 侧 15 份，合计 20,654 词**（份数与字数由 `gen_lanes.py` 从台账与正文现算，不手写）。holdout 的 6 份**不列在此**。

LoC 一般通信 10 卷（**寄给她的来信**）与书评剪报 1 卷。

★ **收信人是她 ≠ 她写的**——这一整条道都标 S1/THIRD-PARTY，`author` 留空，**不计入一手占比**。其中 Florence Nightingale 卷档案标注 `from + To`，3,661 词。

★ 这条道是本人物**最薄**的一条：只有 11 份，且都在 LoC 一处。同时代医学界对她的系统评述（Waite 1947、Fleming 1956 等）**在版权期内，未取**。

## 逐份清单

| 来源编号 | 档 | 篇名 |
|---|---|---|
| `src-465a8fc7f3be` | S1 | Elizabeth Blackwell Papers: Family Correspondence, Alice Stone Blackwe |
| `src-d87cfca546aa` | S1 | Elizabeth Blackwell Papers: Family Correspondence, Anna Blackwell |
| `src-ab157d87aa2b` | S1 | Elizabeth Blackwell Papers: Family Correspondence, Henry Browne Blackw |
| `src-884baa56563c` | S1 | Elizabeth Blackwell Papers: Family Correspondence, John Kenyon Blackwe |
| `src-f5276ad67fcd` | S1 | Elizabeth Blackwell Papers: General Correspondence, folder 988 |
| `src-1130f0b24a5c` | S1 | Elizabeth Blackwell Papers: General Correspondence, folder 1025 |
| `src-1b05a3efcb99` | S1 | Elizabeth Blackwell Papers: General Correspondence, folder 1038 |
| `src-233ddf08b575` | S1 | Elizabeth Blackwell Papers: General Correspondence, folder 1063 |
| `src-68c28a078f11` | S1 | Elizabeth Blackwell Papers: General Correspondence, folder 1088 |
| `src-a908b2aa19b6` | S1 | Elizabeth Blackwell Papers: General Correspondence, folder 1138 |
| `src-80d9926e7cbe` | S1 | Elizabeth Blackwell Papers: General Correspondence, folder 1143 |
| `src-9b22167bbfa7` | S1 | Elizabeth Blackwell Papers: General Correspondence, folder 1163 |
| `src-ab4b7be6d8c6` | S1 | Elizabeth Blackwell Papers: General Correspondence, folder 1188 |
| `src-a769fdf2543b` | S1 | Elizabeth Blackwell Papers: General Correspondence, folder 1213 |
| `src-8fa9d8aa780f` | S1 | Elizabeth Blackwell Papers: Book reviews（剪报） |

---

## ★ 三处杂质（引文不许引到这里）

1. **16 册日记混有印刷扉页**——商品袖珍日记本前面印的邮资表、印花税则、王室年表，被众包连同手写一起转写。实测 1885–87 占 9.7%、1888–90 占 12.2%、1891–93 占 13.4%，其余约 2%，全 16 册合计 **4.1%**。
2. **`contaminated-1247` / `contaminated-1265`** 是整版报纸剪贴簿（分类广告、地方法庭报道、股票行情），**已标 U，不计入 usable**。
3. **`sp-1261` 末尾第 1797–1811 行**接了一栏「SITUATIONS WANTED」求职广告（约 284 词 = 1.7%），从她的句子中断处突起。

**引文判据只验「这句话在语料里」——它分不出这三处不是她的话。**

