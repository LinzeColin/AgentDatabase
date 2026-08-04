# 编年（`timeline`）

**train 侧 14 份，合计 425,059 词**（份数与字数由 `gen_lanes.py` 从台账与正文现算，不手写）。holdout 的 6 份**不列在此**。

1895 年自传《Pioneer Work in Opening the Medical Profession to Women》为主干，加 LoC 的 16 册日记（1836–1908）与著作系年表。

★ **关键锚点**：1847 年 10 月入 Geneva Medical College（自传里那封信落款 `Geneva: October 20, 1847.`）、1848 年夏在费城 Blockley Almshouse 实习、1849 年赴巴黎入 La Maternité、1854 年 New York Infirmary 立案。

★ **日记不适合做事实断言**：逐日流水（天气、家用账、访客名单），它们的价值在编年与文体，不在事实密度。

## 逐份清单

| 来源编号 | 档 | 篇名 |
|---|---|---|
| `src-9db0816a3abe` | P1 | Pioneer Work in Opening the Medical Profession to Women |
| `src-68547c3dee10` | P1 | Elizabeth Blackwell Papers: Diary, 1837-1839 |
| `src-a60d08301dac` | P1 | Elizabeth Blackwell Papers: Diary, 1869-1871 |
| `src-8e8bb3cd393b` | P1 | Elizabeth Blackwell Papers: Diary, 1875-1877 |
| `src-626487fdeae2` | P1 | Elizabeth Blackwell Papers: Diary, 1878-1880 |
| `src-fe2535891e86` | P1 | Elizabeth Blackwell Papers: Diary, 1881,1883 |
| `src-a03497151b47` | P1 | Elizabeth Blackwell Papers: Diary, 1885-1887 |
| `src-267b7e3a9bca` | P1 | Elizabeth Blackwell Papers: Diary, 1888-1890 |
| `src-61060e998da0` | P1 | Elizabeth Blackwell Papers: Diary, 1891-1893 |
| `src-4d9a945a3461` | P1 | Elizabeth Blackwell Papers: Diary, 1894-1896 |
| `src-fa9323450221` | P1 | Elizabeth Blackwell Papers: Diary, 1897-1899 |
| `src-b257d99583e6` | P1 | Elizabeth Blackwell Papers: Diary, 1906-1908 |
| `src-3ca4b3b30964` | P1 | Elizabeth Blackwell Papers: Diary, 未系年 |
| `src-a9a8aec383d8` | P1 | Elizabeth Blackwell Papers: Bibliography |

---

## ★ 三处杂质（引文不许引到这里）

1. **16 册日记混有印刷扉页**——商品袖珍日记本前面印的邮资表、印花税则、王室年表，被众包连同手写一起转写。实测 1885–87 占 9.7%、1888–90 占 12.2%、1891–93 占 13.4%，其余约 2%，全 16 册合计 **4.1%**。
2. **`contaminated-1247` / `contaminated-1265`** 是整版报纸剪贴簿（分类广告、地方法庭报道、股票行情），**已标 U，不计入 usable**。
3. **`sp-1261` 末尾第 1797–1811 行**接了一栏「SITUATIONS WANTED」求职广告（约 284 词 = 1.7%），从她的句子中断处突起。

**引文判据只验「这句话在语料里」——它分不出这三处不是她的话。**

