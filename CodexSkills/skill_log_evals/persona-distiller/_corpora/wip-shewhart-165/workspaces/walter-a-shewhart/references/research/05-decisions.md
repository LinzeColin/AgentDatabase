# decisions 道 —— 三篇质量控制论文里的判定规则

本道 3 份：`src-f3562c1704fe`（Quality Control Charts, 1926）、
`src-abc67a749b2f`（Quality Control, 1927）、
`src-3eeef50256fe`（Economic Quality Control of Manufactured Product, 1930）。

★ 归在 decisions 而不是 writings，是因为**这三篇给的是判定程序**：
「这批产品受不受控」是一个要当场做出的判断，而它们规定了怎么做。

## 观察 1：他把一件事切成两半——**先由工程判断定标准，统计才开始**

`src-abc67a749b2f` 逐字：

> `The statistical problem`
> `enters after these standards have been fixed. It is to determine`
> `whether or not the observed fluctuations in the observed estimates of`
> `the para`…

★ **照录，本份是逐行断开的版面。**

这一刀切得很硬：**标准是谁定的、定得对不对，不在统计的射程内**。
统计接手的是一个更窄的问题——观测到的波动能不能用偶然解释。
→ 下游若把他写成「用数据决定该做什么」的人，方向就反了：
**他反复在做的是把「该做什么」挡在统计之外。**

## 观察 2：判定的对象是**有没有可归因原因**，不是「好不好」

`src-abc67a749b2f` 逐字：

> `The present paper gives simple detailed methods for determining from`
> `inspection data whether or not a product is being controlled in the`
> `sense of indicating the presence of `…

`src-f3562c1704fe` 给了这么做的理由：

> `The reason for trying to find assignable causes is obvious — it is only`
> `through the control of such factors that we are able to improve the`
> `product without changing the whol`…

★ 两句合起来是一条完整的动机链：**找可归因原因 → 因为只有它能在不推翻整个流程的前提下改进产品**。
这条链解释了他为什么执着于「区分偶然与可归因」——**那不是分类癖，是省钱**。

## 观察 3：1930 那篇把根据写成了公设

`src-3eeef50256fe` 逐字：

> `Postulate L Alt chance systems of causes are not alike in the`
> `sense that they enable its to predict the future in terms of the past.`

★★ **照录，本份 OCR 质量偏差**：`Postulate L Alt` 实为 `Postulate I. All`，
`its` 实为 `us`，同页另有 `recojjni7x*d`（`recognized`）、`JOVRSAL`、`TFXHNCAL`。
**下游若要当逐字引文用，必须先核那几处原字。**

内容上这是把前两篇的做法**往下挖了一层**：
控制图之所以成立，前提是「并非所有偶然原因系统都一样」——
有些能据往推来，有些不能，而**能不能，正是要判的东西**。

## 这一道对下游的两条硬约束

1. **不要把「控制」读成「达标」。** 三份里的 `controlled` 一律指
   「波动可用一个偶然原因系统解释」，**与规格上下限是两回事**。
2. **判定程序有前置条件，且他自己写明了**（观察 1）。
   凡是把他的方法搬到「标准还没定」的场合，都越出了他自己划的界。
