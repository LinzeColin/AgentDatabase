# External views, criticism, and counterexamples

## Scope and assigned sources

**本道分到 7 份（train split）**：

| source_id | 出版年 | tier | 题名 |
|---|---|---|---|
| `src-83dba76ee577` | 1905 | P2 | Catalogus der tentoonstelling van schilderijen en teekenin…Gogh : juli en augustus, 1905 |
| `src-b6ad5f245978` | 1910 | P2 | Vincent van Gogh : persoonlijke herinneringen aangaande een kunstenaar |
| `src-8e3cd60bfeea` | 1913 | P2 | Personal recollections of Vincent van Gogh, by Elizabeth d…foreword by Arthur B. Davies. |
| `src-b3328eb38b77` | 1919 | P2 | Van Gogh, Vincent |
| `src-e9d58b40a500` | 1920 | P2 | Vincent van Gogh exhibition : October twenty-third, 1920 |
| `src-aa28f9129a99` | 1926 | P2 | Vincent Van Gogh : a biographical study |
| `src-15ac632b9c8b` | 1928 | P2 | La folie de Vincent van Gogh |

★ 本节由台账机械导出（`emit_lane_scope.py`），**不含任何阅读判断**；只投影 `split == train` 的行。

## Source-linked observations

- **时人评述（external）**：本道收集「别人怎么看梵高」。核心是三部传记/评述：
  Théodore Duret《Van Gogh, Vincent》（1919，`src-b3328eb38b77`）、
  Julius Meier-Graefe《Vincent Van Gogh: a biographical study》（1926 英译，
  `src-aa28f9129a99`）、Victor Doiteau《La folie de Vincent van Gogh》（1928 法文，
  `src-15ac632b9c8b`，医学/精神病学视角）。
<!-- src-aa28f9129a99 -->
- **妹妹的回忆录**（external 道与 timeline 道共用）：其妹 Elisabeth du Quesne-van Gogh
  的《Personal recollections of Vincent van Gogh》（1913 英译，`src-8e3cd60bfeea`；
  1910 荷文 `src-b6ad5f245978`）是家人视角的第一手记忆。
<!-- src-8e3cd60bfeea -->
- **展览目录提供「何时展出何作」**：1905 年阿姆斯特丹 Stedelijk Museum 画展目录
  （`src-83dba76ee577`，题名页 "CATALOGUS DER TENTOONSTELLING VAN SCHILDERIJEN EN
  TEEKENINGEN DOOR VINCENT VAN GOGH STEDELIJK MUSEUM AMSTERDAM JULI EN AUGUSTUS 1905"）、
  1920 年纽约 Montross 画廊展目录（`src-e9d58b40a500`，题名页 "Vincent van Gogh
  Exhibition October Twenty-third 1920 ... MONTROSS GALLERY 550 FIFTH AVENUE NEW YORK"）
  显示其名声在死后二十年间逐步确立。
<!-- src-83dba76ee577 -->
- **外部视角的边界**：这些材料是「关于他」的二手/同时代评述，不是他的声口；引文说话人
  分别是 Duret、Meier-Graefe、Doiteau、Elisabeth du Quesne-van Gogh 与展览方，须逐条
  归属，不得当梵高本人的话使用。

## Candidate Claims

- 梵高死后约二十年（1905-1926），其画作开始在阿姆斯特丹、纽约等地进入展览与批评视野，
  展览目录与时人评述记录了其声名的建立（`src-83dba76ee577`、`src-b3328eb38b77`）。
- 同时代批评把他放进化：印象派之后的「后印象派」语境中讨论（`src-aa28f9129a99`）。
- 关于其「疯狂」的医学评述（1928）构成其死后叙事的一个侧面（`src-15ac632b9c8b`）。

## Contradictions and alternative explanations

不同评述者对梵高评价不一：Duret 侧重其艺术成就，Doiteau 侧重其精神疾病，Meier-Graefe
作传记式综合。这些外部视角与他的自述（conversations 道）互相印证但各自独立，不能混为
一谈。

## Unknowns and source gaps

1892 年遗作展目录与 1927 英文第 2 卷不在本道范围；Duret 法文原版（1916/1919）与本
语料所收英译的关系以题名页为准；早期（1880s）在世时的批评反应在本语料中缺失。

## Proposed Holdout cases

IDs only; research Agents must not inspect Holdout bodies.

## Handoff to adjudication

external 道提供「别人怎么看他」的印照面：时人评述（Duret/Meier-Graefe/Doiteau）、
家人回忆（Elisabeth du Quesne-van Gogh）与展览记录（1905/1920），用于对照他的自述。
