# #107 Robert Koch —— 同名与归属风险

`namesake_gate.py` 返回 `resolution: none / candidate_count: 0`——**那只说明平级注册表里没有**。
实搜：**存在 `Robert Koch (disambiguation)` 页**，但同名者按年代／领域全部可分：

| 同名者 | 可分依据 |
|---|---|
| Robert Koch（足球运动员，1986–） | 年代 |
| Robot Koch（电子音乐人，1977–） | 年代＋领域 |
| Bobby Koch（美国政治人物，1960–） | 领域 |
| Robert Koch Woolf（室内设计师，1923–2004） | 全名不同 |
| **《Robert Koch》(1939) 德国传记电影** | **是关于他的作品，不是他的作品**——须记 external |

## ★ 本人物真正的风险不是同名，是三件别的

### 一、**Koch–Pasteur 之争**（我刚做完 Pasteur #106）

两人在炭疽、疫苗、方法论上有真实且激烈的公开分歧。
**Harvey #103 的失败根因就是我编造了对手的立场**；Pasteur #106 第 1 轮又把 Pouchet 的主张
挂到一本讲自发排卵的书上（两席各自抓出）。

> **凡「Pasteur 主张 X」，必须指到 Pasteur 的原文，而 Pasteur 的语料我手上就有
> （`_corpora/wip-pasteur-106/raw/`，60 份）。指不到就不写。**
> 这是本项目第一次出现「争论双方的语料都在本机」的情形——**没有借口。**

### 二、**德文写作 → 有译文层**

与 Jenner（英文原著、无译文层）不同，与 Pasteur（法文）同类。
凡引英译须标明是译本。`check_quote_layer` 管这一条；
`check_quote_integrity` 自 v0.0.0.37 起认德文 `„…"` 引号（此前只认「」与 "）。

### 三、机构名淹没

**Robert Koch Institute**（柏林，1891 年起，至今存在）、
Robert Koch Medal／Prize、无数以他命名的街道与建筑。
全文搜 "Koch" 会被淹没，须配合年份、地点或与 `Robert` 连用。

## ★★ 出题阶段的硬约束（Pasteur #106 用三轮换来的）

**题面里的每一个数与每一个口径，写进去之前都要回语料核一遍。**

Pasteur 因 `fact-preservation` 三轮未过 0.93 而拒发，
而根因是**我自己把两处题面写歪了**：把「担保率」问成「成功率」、把 1880-12-10 写成「1881 年 12 月」。
**题面按人物冻结、中途不改——错的刻度会一直错到人物结束。**
这一条落不成判据（我写过 `check_case_premises.py`，自检全绿、真实数据 0 命中，已删），
**只能靠出题时逐条核。**
