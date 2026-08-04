# 文体样本（`expression`）

**train 侧 7 份，合计 38,739 词**（份数与字数由 `gen_lanes.py` 从台账与正文现算，不手写）。holdout 的 6 份**不列在此**。

诗、故事与译作、1830 年的少年习作本、演讲笔记，以及 1890 年伦敦女子医学院的开学致辞。

★ **最早的样本是 1830 年那本**，档案著录为 `Eliz. Blackwell's notebook 1830 with various compositions`——那年她九岁。

★ 她用过笔名：《Margaret St. Omer》档案卡片注 `by E. H. Lane in Dr. Eliz. writing written under pen name`。

## 逐份清单

| 来源编号 | 档 | 篇名 |
|---|---|---|
| `src-29479ee933c0` | P1 | The Influence of Women in the Profession of Medicine |
| `src-f25ff4a3f8bc` | P1 | Elizabeth Blackwell Papers: Misc. notes 3/3（1830 年少年习作本） |
| `src-6f19a408a417` | P1 | Elizabeth Blackwell Papers: Notes for speech on English charities |
| `src-2247e3c594eb` | P1 | Elizabeth Blackwell Papers: Poetry（`copies in Dr. Eliz. hand`） |
| `src-b6ac48c0213a` | P1 | Elizabeth Blackwell Papers: Stories and translations 1/3 |
| `src-87bd6d690953` | P1 | Elizabeth Blackwell Papers: Stories and translations 2/3 |
| `src-7c9ba52693a5` | P1 | Elizabeth Blackwell Papers: Stories and translations 3/3 |

---

## ★ 三处杂质（引文不许引到这里）

1. **16 册日记混有印刷扉页**——商品袖珍日记本前面印的邮资表、印花税则、王室年表，被众包连同手写一起转写。实测 1885–87 占 9.7%、1888–90 占 12.2%、1891–93 占 13.4%，其余约 2%，全 16 册合计 **4.1%**。
2. **`contaminated-1247` / `contaminated-1265`** 是整版报纸剪贴簿（分类广告、地方法庭报道、股票行情），**已标 U，不计入 usable**。
3. **`sp-1261` 末尾第 1797–1811 行**接了一栏「SITUATIONS WANTED」求职广告（约 284 词 = 1.7%），从她的句子中断处突起。

**引文判据只验「这句话在语料里」——它分不出这三处不是她的话。**

