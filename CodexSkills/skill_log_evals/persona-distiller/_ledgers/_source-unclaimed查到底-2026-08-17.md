# `research.source-unclaimed` 22 条查到底：18 条已记档，**2 条从没记过**（2026-08-17）

普查 25 个被检查的未判分工作区，这个码撞 **4 个**（不是我第一版说的 22 个 ——
那是「出现次数」）。22 条记录逐个查完。

## 判据的口径（先读定义再开数据）

`check_source_attribution.evaluate()`：只管 `subject_origin == "historical"`，
取 **`tier == "P1"` 且 `author` 逐字等于人物名**的源，逐份问两件事 ——

1. `authorship_evidence`（或 `evidence_kinds`）里有没有 `A-*` 开头的项；
2. 它的 `locator` / `original_name` / 去扩展名的词干，有没有出现在
   `meta.attribution_basis` 的 `citation`／`authority`／`covered_sources`／
   `counting_convention` 四个字段拼成的文本里。

两条都不满足 → 记一条 `research.source-unclaimed`。

★ **我头一个探针读的是 `evidence` 字段，全 0** —— 而门只报 22 条。
  字段名是我猜的，不是读来的。**今天第四次凭猜读键。**
  换成判据真正读的字段后，数字精确复现：

| 工作区 | 账本 | P1 且署他名 | 有 A-* | basis 点名 | **未认领** |
|---|---:|---:|---:|---:|---:|
| william-chandler-roberts-austen | 32 | 22 | 15 | 0 | **7** |
| adolf-martens | 25 | 12 | 1 | 0 | **11** |
| justus-von-liebig | 64 | 30 | 26 | 2 | **2** |
| ignaz-semmelweis | 60 | 5 | 3 | 0 | **2** |
| | | | | | **22** |

## 逐个对已有记录

四个人**都在**延后名单（186 条）里。
★ 第一次我用子串匹配去查，「martens」命中的那条 `name` 是 **Morris Cohen** ——
  结论碰巧对，路径是错的。改成按 `name` 字段逐字比对重做了一遍。

| 人 | 门今天报 | 记录里写的 | 对得上吗 |
|---|---:|---|---|
| Martens #134 | 11 | 「未被逐份认领 **11** 条（**用 11 不用 12**）」，㉕ 已裁「维持现状」 | **精确对上** |
| Roberts-Austen #135 | 7 | 「归属已从 3/30 核到 16/30，剩 **14** 份」，㉕ 同裁 | **口径不同，不是进展** |
| Liebig #124 | 2 | 「**37/39** 一手已逐份点名并附扉页署名原文」⇒ 2 份未点名 | 条数对上，分母不同 |
| Semmelweis #105 | 2 | 整条记录提到「归属」的那句说的是**别人**的分类 | **★★ 从没记过** |

★ **Roberts-Austen 的 14 → 7 不是「修好了 7 份」。** 两个数用的是两把尺：
  记录里的 14 是「归属未核出的份数」（分母 30）；
  门今天数的是「P1 ∧ author==他 ∧ 无 A-* ∧ 未被 basis 点名」（分母 22，其中 15 有 A-*）。
  [[changing-the-sampling-unit-changes-the-ruler]]

## ★★ 唯一的新事实：Semmelweis 那 2 条

他 5 条 P1 里，3 条《Gesammelte Werke》(1905) 都带 `A-byline-standalone`，
另外两条没有署名证据 —— 而那两条正是他最有名的两封公开信：

    w_offener_brief_saemmtliche_professoren_1862.txt   1862  archive.org/details/offenerbriefsm00semm
    w_zwei_offene_briefe_spaeth_scanzoni_wellcome_1861.txt 1861  archive.org/details/b33674164

两条的 `author` 都写着 Ignaz Semmelweis、`rights` 都是 public-domain。
**门报的不是「这不是他写的」，是「没记证据」** —— 一处记账缺口。

★ **今天补不了，补了就是编造。** 两份的 `local_path` 指向
`raw/src-…/…txt`，而该工作区 `raw/` 里只有 `.gitkeep`
（语料正文不进 git，同日 `_未判分工作区研究门全量实跑` 已查清）。
要落 `A-byline-standalone` 就得**真读扉页**，读不到就不许写。

★ **不改变他的处置**：他延后的理由是 `primary_ratio` **0.1186**，
  而 quick 档门槛 0.40 —— 差得远，补上这 2 条署名证据也一样过不去。

## 结论

22 条 = 18 条已记档（其中 11 条 ㉕ 已裁「维持现状」）+ **2 条从没记过**。
那 2 条是记账缺口不是归属错误，**要读扉页才能补，本机读不到**。
`research.source-unclaimed` 这个码到此查完，**零条需要立刻动手**。
