# Bessemer #132 第 2 轮准备（2026-08-05）

## 第 1 轮真实结论（按 key 逐题回查后，非评委自报的盲坐标均分）

| | 有 rubric（D/E） | 无 rubric（F/G） |
|---|---|---|
| delta | **+0.2678** | **−0.0134** |

`results.jsonl` 里记的是 **F/G（无 rubric）**，所以本人物按**诚实那把尺子**判：
**−0.0134，低于 quick 门 +0.03。**

## 第 1 轮判决书四条结论**全部作废**（归属判反）

评委是盲的，A/B **逐题翻面**（候选 3/16 在 A、13/16 在 B）。
我抄评委笔记时没过 key，**把基线的四处毛病全记到了候选头上**。详见 `round1-verdict.md` 文末更正。
★ 其中一条把候选**赢得最漂亮**的一题（style-decoy 拒绝现编名言，无 rubric delta **+0.2400**）
写成了它最丢人的一题。已落成 `check_verdict_attribution.py` 并接线。

**因此「第 2 轮改掉 q-11 自相矛盾」这一项作废——候选那一题没有自相矛盾。**

## 第 2 轮真正要改的（按无 rubric 两席逐套组 delta 排序）

| 套组 | 无 rubric delta | 状态 |
|---|---|---|
| voice | **−0.1450** | **已改**（见下） |
| known | −0.1400 | 题面不一致所致，基线已重生成，**待裁定是否换入** |
| trajectory | −0.1250 | 待改 |
| boundary | −0.1150 | 待改 |
| contrast | −0.1050 | 待改 |

赢面（不要动）：fact-preservation **+0.3100**、style-decoy **+0.2400**、identity-routing +0.1350。

## voice 已改：候选原来在「答方法」，没有「答人」

第 1 轮候选交的是一套核查程序（575 字），**从头到尾没有回应会上那个人**；
基线让步一半、给出具体、收了一句狠话，**诚实两席据此判它赢 0.145**。

改法不是去学基线编，而是**语料里本来就有**——
Bessemer 自己把那次运气写下来过（自传 Ch. XII，pp.152–177）：

> `By the mere accident of living in London, I had access only to the pig iron used`

以及他对「当场怎么回应」的原话：

> `all that I could say would be mere talk, and I felt that action was necessary, and not words.`

**基线是编的，候选是引的，而候选引的那句更狠。**

★ 两个当场踩到的坑：
1. 第一句在印本上被**页眉断开**（`THE INTRODUCTION OF THE BESSEMER PROCESS 171`），
   跨着引会造出一句原文没有的连续句——**已只引到断处并写明**。
2. 头一次搜语料搜的是 `corpus/train/`（**该目录不存在**），得到 0 命中，
   差点据此断定「语料不支持」。**不存在的路径返回的 0 不是「没有」。**

## 第 2 轮载荷已建好并过门（`evals/round2/`）

均长比 **1.01**、候选更短 **10/16**、表面通道最高 **38%**、长引文 **18/18 带坐标**、
rubric 抄答案 **0/16**。**位次混杂仍是 81%**（与第 1 轮逐条一致，属待裁定 ⑱，报数时必须带上）。

**未派发**——先把 trajectory / boundary / contrast 三处一并改完再派，
**三轮上限已用掉一轮，不为一处改动烧一轮。**
