# Writings and systematic works

## Scope and assigned sources

**本道分到 7 份（train split）**：

| source_id | 出版年 | tier | 题名 |
|---|---|---|---|
| `src-3e6b4b822d4f` | 1758 | P1 | A Discourse on the Study of the Law; being an Introductory…am Blackstone. [Oxford, 1758] |
| `src-1605220f591e` | 1762 | P1 | Law Tracts, in Two Volumes, Vol. I —— I. An Essay on Colla… At the Clarendon Press, 1762 |
| `src-435de4a6e51d` | 1762 | P1 | Law Tracts, in Two Volumes, Vol. II —— The Great Charter a…ndon Press, M.DCC.LXII [1762] |
| `src-bcf4065a0233` | 1766 | P1 | An Analysis of the Laws of England. To which is prefixed a…zabeth Watts, MDCCLXVI [1766] |
| `src-5854111768a9` | 1898 | P1 | Commentaries on the Laws of England, in Four Books — Book …a: Rees Welsh & Company, 1898 |
| `src-7f12a15d6d46` | 1898 | P1 | Commentaries on the Laws of England, in Four Books — Book …a: Rees Welsh & Company, 1898 |
| `src-9525769f856e` | 1898 | P1 | Commentaries on the Laws of England, in Four Books — Book …a: Rees Welsh & Company, 1898 |

★ 本节由台账机械导出（`emit_lane_scope.py`），**不含任何阅读判断**；只投影 `split == train` 的行。

## Source-linked observations

**所有逐字引文都过了 `_corpus/verify_quote.py`（退出码 0 = 在正文块内、前后不提他的姓）。**
这一层的必要性见 `_corpus/00-编者注与逐字引文.md`：本道可引的印本混着编者注，**逐条核，不用比值**。

1. **每一卷开头都先交代自己在整体里的位置。** 卷二起首 `src-7f12a15d6d46`：
   `TuE former book of these commentaries having treated at large`；
   卷四起首 `src-9525769f856e`：`WE are now arrived at the fourth and last branch of these commentaries`。
   → 读者任何时候翻开，都能从本卷第一句知道前面讲完了什么、这一卷是第几步。

2. **先宣告次序，再执行。** 卷二 `src-7f12a15d6d46`：
   `concerning the nature and original of which I shall first premise a few observations,
   before I proceed to distribute and consider its several objects`；
   卷四 `src-9525769f856e`：`I shall consider, in the jivst place, the general nature of crimes
   and punishments`（`jivst` 为 OCR 讹形，照录未改）。

3. **骨架是先印出来的，正文照骨架填。** `src-5854111768a9`：
   `shall take the liberty to follow the same that I have` 已 `already submitted to the public`——
   指的正是本道另一份源 `src-bcf4065a0233`（*An Analysis of the Laws of England*）。
   **先出一份纲目、再按纲目写全书**，两份都在本道语料里，可对照。

4. **一段讲完先收口，再往下走。** `src-5854111768a9`：
   `I have now gone through the definition laid down of a municipal law`，
   并说明这一段里 `I have endeavored to interweave a few useful principles concerning
   the nature of civil government`。

5. **讲授者的自我定位是「画地图的人」。** `src-5854111768a9`：
   `He should consider his course as a general mapof the law, marking out the shape of the country`
   （`mapof` 为 OCR 粘连，照录未改）；同处他自陈要说的是
   `what I conceive an academical expounder of the laws should do, than what I have ever known to be done`。

6. **超出此处射程的论点，明说留到别处证。** `src-5854111768a9`：
   `Upon some future occasion I shall endeavor to prove, that, in the origin of representation`——
   **不在本处硬撑论证**。


## Candidate Claims

- **clm-bs-arch-01｜先宣告次序，再执行；每一段先收口，再开下一段。**
  证据：`src-7f12a15d6d46`（`I shall first premise a few observations, before I proceed to distribute`）、
  `src-9525769f856e`（`I shall consider, in the jivst place …`）、
  `src-5854111768a9`（`I have now gone through the definition laid down of a municipal law`）。
- **clm-bs-arch-02｜纲目先于全书：先印出一份可检验的骨架，再照骨架把正文填满。**
  证据：`src-5854111768a9` 的 `follow the same that I have already submitted to the public`
  指向 `src-bcf4065a0233`（1766 *Analysis*）。★ 两份同在本道，**可以互相核**。
- **clm-bs-arch-03｜每一卷第一句就交代它在整体里的位置。**
  证据：`src-7f12a15d6d46`、`src-9525769f856e` 的起首句。
- **clm-bs-teach-01｜讲授的目标是给出全境地图，不是逐块耕地。**
  证据：`src-5854111768a9` 的 `a general mapof the law, marking out the shape of the country`。
- **clm-bs-scope-01｜论点超出此处射程时，明说留到别处证，不在本处硬撑。**
  证据：`src-5854111768a9` 的 `Upon some future occasion I shall endeavor to prove`。


## Contradictions and alternative explanations

- **最大的一条：本道可引的那个印本混着编者注**（1898 年 Rees Welsh 版，W. D. Lewis 编，
  注文出自 CHRISTIAN／SHARSWOOD／CHITTY 等）。上面每一条引文都单独过了 `verify_quote.py`；
  **没过的一律没写进来**。已知误判两例，都记在 `_corpus/00-编者注与逐字引文.md`：
  ① 编者序言里的第一人称（`The unsigned notes are my own.`）；
  ② 编者注跨空行的续段（`I cannot agree that when a law, decided to be constitutional …`）。
- **「先出纲目再写全书」有另一种解释**：18 世纪牛津讲席的通行做法就是先印 syllabus。
  **本道的语料分不开「这是他的习惯」与「这是当时讲席的体例」**——
  只有他一个人的材料，没有同代讲席的对照本。**据此不下「这是他个人特征」的断言。**
- 1766 *Analysis* 的扫描长 s 讹字率 0.9881，**只能引用它的存在与结构，不能逐字引它**。


## Unknowns and source gaps

- **可逐字引用的面比语料总量小得多**：本道多份印本的长 s 被 OCR 读成 `f`
  （逐份讹字率见 `metrics.longs_corruption`），从那些文件里取不出可核的逐字串。
  ★ **一个字都没有改过**——改讹字再当逐字引文用是本项目记档过的事故形态。
- **编者注与正文的分界可测但不精确**：四把尺子给出 17.9%／31.2%／31.3%／39.8%，
  详见 `_corpus/00-编者注与逐字引文.md`。**所以本道不使用任何「占全书百分之几」的说法**，
  只使用逐条核过的引文。
- 断言 `clm-bs-arch-02` 的因果方向（纲目催生全书，还是全书回填纲目）**本道材料判不了**。


## Proposed Holdout cases

IDs only; research Agents must not inspect Holdout bodies.

- 用例方向：`case-known-*`、`case-boundary-*`——考「问到他没有把握的具体出处时，他给不给得出坐标、给不出时怎么说」。

## Handoff to adjudication

- 五条候选断言已可进断言层，**每条都带 source_id 与逐字引文**；
  引文全部过 `_corpus/verify_quote.py` 退出码 0。
- ★ **传给判分侧的硬约束**：本人物的逐字引文只能出自已核的正文块。
  任何新增引文都必须再跑一次 `verify_quote.py`，**退出码 2（没判）不算通过**。
- ★ `clm-bs-arch-02` 的因果方向未定，写进产物时**必须保留「分不开」这句**。

