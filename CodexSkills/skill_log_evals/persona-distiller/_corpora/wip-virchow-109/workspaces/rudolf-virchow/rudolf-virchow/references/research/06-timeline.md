# 06 年表

**本路只有 2 条源，且都在生命末端。年份锚点分散在其他各路，本路不集中。**

## 本路的两条

- src-c219d2d3c1ba《Zur Erinnerung. Blätter des Dankes für meine Freunde》(1902)
  —— **他本人所撰，同年卒**。是他自己回望的文本，不是别人给他写的年表。
- src-c8cc4a3bfc5f 同文另一扫本（P2）

## 可核的年份锚点，逐条指到别路的源

| 年 | 事 | 源 |
|---|---|---|
| 1839–1864 | 致父母家书（求学至中年早期） | src-fb1a2a211a95（02） |
| 1848 | 上西里西亚斑疹伤寒调查报告 | src-2b544cb633c5（05） |
| 1852 | 《Die Noth im Spessart》 | src-ace6038037a8（05） |
| 1855 | 〈Cellular-Pathologie〉，作 `Omnis cellula **a** cellula` | src-0f84fd47f3c0（01） |
| 1856 | 《Gesammelte Abhandlungen》，作 `Omnis cellula a cellulla` | src-911fadcbcd25（01） |
| 1858 | 《Die Cellularpathologie》，改作 `Omnis cellula **e** cellula` | src-63ac5a56f924 / src-3bf8c9c3b522（01） |
| 1862 | 《Vier Reden über Leben und Kranksein》 | src-5d35637306ca（03） |
| 1863 | 唯物论演说 | src-bf564520e161（03） |
| 1863–67 | 《Die krankhaften Geschwülste》 | src-d82862576099（01） |
| 1868 | 《Ueber die Kanalisation von Berlin》 | src-c3af13c32c72（05） |
| 1869 | 《Canalisation oder Abfuhr?》 | src-70b23b71ffbf（05） |
| 1870 | 战地卫生列车 | src-be0d95be2a93（05） |
| 1871 | 《Cellularpathologie》第四版，仍作 `e cellula` | src-f98483048f3c（01） |
| 1873 | 《Reinigung und Entwässerung Berlins》 | src-436e416ed564（05） |
| 1877 | 《Sectionstechnik》 | **故意留作 holdout，本表不给源 id** |
| 1878 | Haeckel《Freie Wissenschaft und freie Lehre》驳其反演化论教学之说 | src-11e28e04ae8d（04） |
| 1879 | 《Gesammelte Abhandlungen aus dem Gebiete der öffentlichen Medicin》 | src-aa4d097813fb（05） |
| 1880 | Schliemann《Ilios》/《The Necropolis of Ancon》 | src-41aa7a868b1c / src-9b17fba0ba2a（04） |
| 1886 | 〈Descendenz und Pathologie〉 | src-05057e87c590（01） |
| 1891 | 七十寿辰纪念文集 | src-f01a86fd4192（04） |
| 1902 | 《Zur Erinnerung》，同年卒 | src-c219d2d3c1ba（本路） |

**★ 1877 那一行为什么不给源 id**：该源被留作 holdout。
年表里写出年份与书名不算泄露（那是公开著录），
**但只要写上它的 source_id，研究门就会拦**——实测拦住过一次。

## ★ 一条抓源阶段实测的著录陷阱

**archive.org 对每一份 `archiv-*` 的 Google 扫本，年份字段都报 1847**
（该刊的创刊年），**不是该卷的年份**。

按著录年份排年表，44 个卷次会全部错到 1847。
**卷年须从卷内取（扉页与页脚），不能从著录字段取。**
这一条已写进 `raw/_ids.txt` 与账本。
