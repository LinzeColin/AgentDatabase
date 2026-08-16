# 扣分不是禁令 —— `restricted` 从来没被执行过

**2026-08-17**｜合同白纸黑字、数据结构化记着、**没有任何地方在执行**。

## 合同怎么写的

`persona-producer-consumer-contract.md`：

> `eligible`：可在声明能力和边界内使用。
> `restricted`：**只允许命中已测量切片；不得外推为一般能力。**
> `blocked`：……不得路由。

`blocked` 一直是**硬排除**（`return ... "blocked by expert-fleet admission gate"`）。
`restricted` 呢？只有 `restriction_penalty = 0.08` —— **一次扣分**。

## 实测后果

把 Carver（唯一一位 `restricted`）放进 20 人队，任务选**诗集排版**：

    选中 Carver = **是**
    他这题的 domain_match = **0.0000**（完全不在他被测量过的范围）
    admission_restriction = 0.0800   ← 发了火
    measured_scope        = 0.1600   ← 也发了火
    ⇒ **两个扣分都发火了，他照样入座**

**扣分只排名次，不设禁令。** 一个 0.08 + 0.16 的惩罚，在 20 个席位的队伍里
根本挡不住任何人。

## 最刺眼的一点：答案早就在数据里

准入账本 `expert-fleet-admission.json` 对他记着：

    "admission": "restricted",
    "routing_scope": "measured-only"      ← **结构化字段，含义明确**
    "dimensions": { ..., "measured_scope_clarity": 100, ... }

而 `route_team_moe.py` **从头到尾没有出现过 `routing_scope`**。

★ 还有一个同名陷阱：打分里确实有一项叫 `penalties.measured_scope`，
但它扫的是 `card.user_value` 的**散文**找负面词，跟那个结构化字段毫无关系 ——
**名字像，管的不是同一件事**。而它在 24 题上的贡献实测是 **0.0%**。

## 修法：与 `blocked` 完全同构

    if gate.admission == "restricted" and gate.routing_scope == "measured-only":
        if domain_match <= 0:
            排除，理由 = "restricted persona: task is outside its measured scope"

「命中已测量切片」用这个候选**本来就已经算出来的量**表达。
**改的是「谁有资格」，不是「谁得几分」** —— 权重、阈值、人数、模式一律未动。

## 收益：基准上实测是 **0**，如实报

A/B 同一把尺子：24 题路由集与 72 题 oracle 集**逐项相同**。
因为全库 **102 人里只有 1 位** `restricted`。
**证据是探针，不是基准。** 今天这是第三次遇到「修得对、基准动不了」——
基准的覆盖面本身就是有限的。

## 一条可执行的

**凡是「某某只允许／不得……」的规则，去代码里找它的执行点。**
找不到执行点，就等于没有这条规则 —— 哪怕：

- 合同里写了（写了）
- 数据里有结构化字段（有：`routing_scope: measured-only`）
- 甚至有个名字很像的机制在跑（有：`penalties.measured_scope`，管的是别的事）

**三样齐全，仍然可以一次都没执行过。**
[[a-comment-claiming-a-guard-is-not-a-guard]]｜[[a-rule-in-a-doc-has-no-enforcer]]｜
[[every-requirement-needs-an-owner]]

★ 测试的射程也钉住了：名册里若一个 `restricted` 都没有，
测试**报 NO-SUBJECT 并失败**，不许把空扫描面当通过。
[[zero-hit-gates-must-prove-they-can-hit]]
