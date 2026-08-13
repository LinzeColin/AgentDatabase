#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Brandeis #172 十份产物生成器。

★★ **正文一律从 `evidence/claims.jsonl` 现取，不在这里手打。**
理由是 [[gates-cover-json-not-the-prose-users-read]]：判据盯 JSON，
而用户读的是散文；两边一手打就会漂。这里散文由断言现渲染，
断言改了重跑一次就同步，`sync_products_from_claims.py` 也才查得动
（它靠正文里的 `<!-- claim:… -->` 标记比对）。

★ 每一条都带 `<!-- claim:clm-… -->` 与**反证条件**。反证条件取自断言的 `falsifiers`，
  **不重写**——重写就等于产物与断言各说各的。
"""
import json
import pathlib
from collections import defaultdict

HERE = pathlib.Path(__file__).resolve().parent
W = HERE / "workspaces" / "louis-brandeis"
CLAIMS = [json.loads(l) for l in (W / "evidence" / "claims.jsonl")
          .read_text(encoding="utf-8").splitlines() if l.strip()]
BY_CAT = defaultdict(list)
for c in CLAIMS:
    BY_CAT[c["category"]].append(c)

NAME = "Louis Brandeis"


def render(c, indent=""):
    out = [f"{indent}- {c['claim']} <!-- claim:{c['claim_id']} -->"]
    for f in c.get("falsifiers", [])[:2]:
        out.append(f"{indent}  - **反证条件**：{f}")
    return "\n".join(out)


def block(cs, indent=""):
    return "\n".join(render(c, indent) for c in cs)


# fact 按主题分三节（分节依据是 time_scope 与内容里的题目，不是随手分的）
def facts_sections():
    ins, money, jew = [], [], []
    for c in BY_CAT["fact"]:
        t = c["claim"]
        if "犹太" in t or "Jews" in t or "Jewish" in t or "代表席位" in t or "授权" in t:
            jew.append(c)
        elif "寿险" in t or "保险" in t or "工人险" in t or "费用率" in t or "佣金" in t or "换算" in t:
            ins.append(c)
        else:
            money.append(c)
    return ins, money, jew


INS, MONEY, JEW = facts_sections()

FILES = {}

FILES["facts.md"] = f"""# 事实 · {NAME}

★ 每一条都带**逐字引文**与 `source_id`；引文含 OCR 讹字时**照录不改**，
并在条目里注明该讹字读作什么。**改了讹字就不再是逐字引文。**

## 保险：他把成本拆到分，把「成功」换成可量的数

{block(INS)}

## 金融与法：他把问题定在处境上

{block(MONEY)}

## 犹太事务：他先划授权边界，再谈内容

{block(JEW)}

---

★★ **取引文的硬纪律**（本工作区实测，见 `references/research/01-writings.md`）：
他的著作大量引用他人。机械抽出的 14 条第一人称候选里 **9 条不是他**
（尤蒂卡审计官 Reusswig 3、ICC 听证证人 Towne 3、North 法官 1、Fisher 1、工厂主 1）。
**上面每一条都逐条读过原文前 700 字。**

★ 另一条：《Business—a profession》三个扫描件的**前 62,094 / 64,956 / 73,433 字
是 Ernest Poole 的导言**（1925 版还有 Frankfurter 的注）——占各自全文 13.6–14.1%。
上面取自那三份的条目，偏移全部在正文区，`gen_claims.py` 每次跑都断言一遍。
"""

FILES["work.md"] = f"""# 做法 · {NAME}

★ 只收**可复用**的做法：既有步骤，又有「怎么知道这步做对了／什么时候把结果丢掉」的判据。
只有步骤没有判据的，照着做的人不知道自己做错没有——那种不收。

{block(BY_CAT["work-method"])}

---

★ 四条的共同形状：**先定判准 → 再明说什么不算数 → 最后才给数。**
「明说什么不算数」那一步是判据所在，也是它们与「一段漂亮的方法论」的分界。
"""

FILES["decision-policy.md"] = f"""# 决策规则 · {NAME}

## 他反复用的两条

{block(BY_CAT["value"] + BY_CAT["mental-model"])}

## 落到具体做法

{block(BY_CAT["work-method"][:2])}

---

★ 用他的口吻答题时：**限定语在前、断言在后**。
把「so far as…」「I take it that…」「in my opinion」这类限定删掉，就不像他了。
"""

FILES["strategy.md"] = f"""# 策略 · {NAME}

{block(BY_CAT["value"])}

{block(BY_CAT["mental-model"])}

---

★ 他改的是**处境**不是**人**：谈联锁董事说 `even the best men have found themselves
unduly influenced`，谈公正说要先造出 `conditions under which truth may properly function`。
问「谁的错」时，他答的往往是「什么条件下这件事必然发生」。
"""

FILES["capabilities.md"] = f"""# 能答什么 · {NAME}

按断言层的 `contexts` 机械汇总（**不是我另写的**）：

""" + "\n".join(
    f"- {ctx}" for ctx in sorted({x for c in CLAIMS for x in c.get("contexts", [])})
) + f"""

★ 覆盖的年份：{min(c['time_scope'].split('-')[0] for c in CLAIMS)}–1939（`boundaries.md` 写明其中哪一段没有语料）。
★ 断言 {len(CLAIMS)} 条，逐类：""" + "、".join(
    f"{k} {len(v)}" for k, v in sorted(BY_CAT.items())) + """
"""

FILES["boundaries.md"] = f"""# 边界 · {NAME}

{block(BY_CAT["boundary"])}

## 语料本身的边界

- 本工作区 **38 份**语料（其中 34 份进入建模）；六条研究道里 **timeline 道为 0 份**
  ——年表与传记条目按定义不由他署名，本轮的检索式（`creator` 字段的两种全名形式）够不到。
- `external` 道那 9 份的形态与别人不同：**是他立论所依据的实证研究（Goldmark），
  不是「别人怎么评价他」**。问「同时代人怎么看他」时，本库答不了。
- `decisions` 道只有 1 份，且**不产生逐字引文**：那一卷的第一人称几乎全是辩状所引证的权威。

## 不要做的事

- **不要把书里的第一人称当成他的**：实测 14 条候选里 9 条不是他。
- **不要引《Business—a profession》前 62k–73k 字**：那是 Poole 的导言与 Frankfurter 的注。
"""

FILES["cognitive-os.md"] = f"""# 思考方式 · {NAME}

{block(BY_CAT["mental-model"])}

## 三个反复出现的动作

1. **先说射程再说内容**——`only five of the ninety`／`so far as the unions have suffered`／
   `the details which I was given the power to modify`。
2. **把道德问题换成可比较的量**——问「工会该不该赔」，他答「赔的回报率最高」。
3. **明说什么不算数**——规模不算成功的证据；只往监管机构备案不算披露。

{block(BY_CAT["work-method"][2:])}
"""

FILES["hypotheses.md"] = f"""# 假说 · {NAME}

★ 这一份里的**不是事实**。每一条都写明被什么推翻。

{block(BY_CAT["hypothesis"])}
"""

FILES["persona.md"] = f"""# 人物 · {NAME}

Louis Brandeis（1856–1941）。本库覆盖的是他**上最高法院之前**的写作与讲话
（语料出版年 1887–1925），不覆盖 1916 年起的司法意见——理由见 `boundaries.md`。

## 说话的样子

{block(BY_CAT["mental-model"])}

{block(BY_CAT["value"])}

---

★ 一句可直接感受的：`Sunlight is said to be the best of disinfectants; electric light the
most efficient policeman.`（1914《Other people's money》第五章正文首段）
——注意他写的是 `is said to be`，**他在转述这句格言，不是宣称自创**。
"""

FILES["divergence-map.md"] = f"""# 与常见印象的分歧 · {NAME}

| 常见印象 | 本库语料里看到的 |
|---|---|
| 「阳光是最好的消毒剂」是他的名言 | 他自己写的是 `Sunlight **is said to be** the best of disinfectants` —— **转述**，不是自创 |
| 「Brandeis Brief」＝他用事实说话 | 那一卷里**他自己的话很少**：第一人称几乎全是被引证的权威（如 MacCormac 在上议院作证）。他的贡献是**选择与编排别人的事实**，不是自己发言 |
| 他反对大企业是出于道德义愤 | 语料里他一再把问题定在**处境**上：`even the best men have found themselves unduly influenced` |
| 他是法律人，所以讲法理 | 谈工会赔偿时他绕开对错，直接算**回报率**；谈寿险时他给的是费用率与失效率 |

## 本库自己的分歧点

{block(BY_CAT["hypothesis"])}
"""

BANNED = ("holdout", "留出集", "密封集")
leaks = [(n, w) for n, b in FILES.items() for w in BANNED if w in b]
if leaks:
    raise SystemExit(f"✗ 产物正文里出现了泄题词，**不写文件**：{leaks}")

for name, body in FILES.items():
    (W / name).write_text(body.rstrip() + "\n", encoding="utf-8")

marks = sum(body.count("<!-- claim:") for body in FILES.values())
used = {c["claim_id"] for c in CLAIMS
        if any(f"<!-- claim:{c['claim_id']} -->" in b for b in FILES.values())}
print(f"✓ 写出 {len(FILES)} 份产物，共 {marks} 处 claim 标记")
print(f"  断言 {len(CLAIMS)} 条，其中**被产物引用的** {len(used)} 条；"
      f"未被引用的 {len(CLAIMS) - len(used)} 条：{sorted(set(c['claim_id'] for c in CLAIMS) - used)}")
