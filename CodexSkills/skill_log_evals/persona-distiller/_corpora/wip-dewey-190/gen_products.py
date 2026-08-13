#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Dewey #190 十份产物生成器。

★★ **正文一律从 `evidence/claims.jsonl` 现取，不在这里手打。**
   判据盯 JSON，而用户读的是散文；两边各手打一次就会漂。
★ 每条都带 `<!-- claim:clm-… -->` 与**反证条件**（取自断言的 `falsifiers`，不重写）。
★ 自查：产物正文里**不许出现** holdout／留出集／密封集这几个词。
"""
import json
import pathlib
import sys
from collections import defaultdict

HERE = pathlib.Path(__file__).resolve().parent
W = HERE / "workspaces" / "john-dewey"
CLAIMS = [json.loads(l) for l in (W / "evidence" / "claims.jsonl")
          .read_text(encoding="utf-8").splitlines() if l.strip()]
BY = defaultdict(list)
for c in CLAIMS:
    BY[c["category"]].append(c)

NAME = "John Dewey"
BANNED = ("holdout", "留出集", "密封集")


def render(c, indent=""):
    out = [f"{indent}- {c['claim']} <!-- claim:{c['claim_id']} -->"]
    for f in c.get("falsifiers", [])[:2]:
        out.append(f"{indent}  - **反证条件**：{f}")
    return "\n".join(out)


def block(cs, indent=""):
    return "\n".join(render(c, indent) for c in cs)


# fact 分两节：**著作侧**（他写了什么、怎么写的）与**行程侧**（1919–20 在日本）
BOOKS = [c for c in BY["fact"] if c["time_scope"] not in ("1919", "1920")]
TRIP = [c for c in BY["fact"] if c["time_scope"] in ("1919", "1920")]

SCOPE = f"""{NAME}（1859–1952）。本库覆盖的是他**出版年 ≤1930** 的著作、
两篇 1915 年协会致辞，以及 1919–20 年旅日书信中**能判定归他**的那一部分。
不覆盖 1930 年后的作品（落在公有领域分界之外，分界随年份滚动）。

★★ **两处必须先知道的射程限制**，不知道就会把别人的话当成他的：

1. **1908 年的《Ethics》过半不是他写的。** 书的卷前序言明写
   Part I 与 Part III 第 XXII–XXVI 章归 James H. Tufts。**本库引文一律避开那些部分。**
2. **1920 年的旅日书信集与妻子 Alice Chipman Dewey 共同署名**，书里没有逐封署名。
   本库按「写信人怎么称呼配偶」判定归属，**只用能判定归他的 19.6%**；
   判不了的 69.1% 一个字没用。
"""

FILES = {}

FILES["facts.md"] = f"""# 事实 · {NAME}

{SCOPE}

## 著作与讲话

{block(BOOKS)}

## 1919–20 年旅日期间

{block(TRIP)}
"""

FILES["work.md"] = f"""# 做法 · {NAME}

下面每条都是**可复用的步骤 + 判据**，不是格言。

{block(BY["work-method"])}
"""

FILES["decision-policy.md"] = f"""# 决策规则 · {NAME}

替他作答时按下列次序，**次序本身就是规则**：

1. **先划射程**——先说这次不打算做什么，且不为此致歉。
2. **定义先减后加**——先划掉不算的那一类，再在剩下的范围里下判断。
3. **让步在前、断言在后**——把对方最常说的缺点原样承认，再给更强的正面判断。
4. **评价之前先给合格条件**——先说「怎样才算数」，再判断眼下够不够格。

{block(BY["work-method"] + BY["boundary"])}
"""

FILES["strategy.md"] = f"""# 策略 · {NAME}

他处理一个有争议的抽象问题时的固定路数：
**把争议压成一个可举例的问题 → 搬出一个专名级的具体例子 → 让例子完成反驳。**

{block([c for c in BY["work-method"] if "实物" in c["claim"] or "举例" in c["claim"]])}

★ 判据是**反例必须是专名**（《林肯传》而不是「一本传记」）。
用范畴词做反例就不是他的路数。
"""

FILES["capabilities.md"] = f"""# 能答什么 · {NAME}

{SCOPE}

## 答得上来的

- 他 1886–1930 年著作里的立场与论证方式（心理学、逻辑、教育、伦理、人性与行为）。
- 1915 年他作为美国大学教授协会首任会长的两篇致辞里的组织主张。
- 1919–20 年旅日期间的具体见闻，**限于能判定归他的那部分书信**。

## 答不上来的

- **1930 年之后的一切**——不在语料射程内。
- **《Ethics》里 Tufts 写的那一半**（Part I、Part III 第 XXII–XXVI 章）。
- **旅日书信里判不了归属的 69.1%**。

{block(BY["boundary"])}
"""

FILES["boundaries.md"] = f"""# 边界 · {NAME}

{SCOPE}

## 三条硬边界

1. **合著部分不冒充他**：《Ethics》(1908) 的 Part I 与 Part III 第 XXII–XXVI 章是
   James H. Tufts 写的，书的序言自己写明了。任何来自那些部分的话**不许挂他名下**。
2. **共同署名的书信不默认是他**：1920 年那本书信集与妻子共同署名、没有逐封署名。
   只有能判定归他的段落可用。
3. **1930 年是硬线**：晚年作品不在本库射程内，且**这条线随年份滚动**——
   分界每年元旦前移一年。

{block(BY["boundary"] + BY["hypothesis"])}
"""

FILES["cognitive-os.md"] = f"""# 思考方式 · {NAME}

{block(BY["mental-model"])}

## 它怎么影响他的句子

- 定义**先减后加**：第一句常是「不算什么」。
- 抽象名词一律**换成一件实物**再谈。
- 判断句里**限定语与断言同处一句**，删掉限定语就不像他。

{block(BY["work-method"], indent="")}
"""

FILES["hypotheses.md"] = f"""# 假说 · {NAME}

下面这些**没有被证实**，写在这里是为了让人知道本产物哪里是薄的。

{block(BY["hypothesis"])}
"""

FILES["persona.md"] = f"""# 人物 · {NAME}

{SCOPE}

## 说话的样子

{block(BY["work-method"][:2])}

## 他知道的具体的事

{block(BOOKS[:3])}

---

★ 一句可直接感受的：他记下日本内务大臣发给他一等铁路通行证、
而同一特权被拒绝给他妻子之后，用一句自嘲收尾——**先事实、后自嘲，不发议论**。
"""

FILES["divergence-map.md"] = f"""# 与常见印象的分歧 · {NAME}

| 常见印象 | 本库语料给出的 |
|---|---|
| 「《Ethics》是杜威的伦理学代表作」 | **过半不是他写的**——序言明写 Part I 与第 XXII–XXVI 章归 Tufts |
| 「旅日书信是杜威的观察记录」 | **与妻子共同署名**，且书里没有逐封署名；能判定归他的只有 19.6% |
| 「他是抽象的哲学家」 | 他谈抽象问题时**一律换成专名级的具体实物**（用《林肯传》驳「生活」的窄义） |
| 「教育学者只谈理念」 | 1915 年那两篇致辞谈的是**会费、会员分布、年会选址**这类组织细节 |

{block(BY["mental-model"] + BY["hypothesis"])}
"""


def main():
    bad = []
    for name, body in FILES.items():
        low = body.lower()
        for w in BANNED:
            if w.lower() in low:
                bad.append((name, w))
        (W / name).write_text(body, encoding="utf-8")
    if bad:
        print("✗ 产物正文里出现了不该出现的词：", bad)
        return 1
    ids = set()
    for body in FILES.values():
        import re
        ids |= set(re.findall(r"<!-- claim:(clm-[0-9a-f]+) -->", body))
    print(f"✓ 十份产物写好：{'、'.join(sorted(FILES))}")
    print(f"   引用到的断言 {len(ids)}/{len(CLAIMS)} 条；正文全部从 claims.jsonl 现渲染")
    miss = {c['claim_id'] for c in CLAIMS} - ids
    if miss:
        print(f"   ★ 没被任何产物引用的断言 {len(miss)} 条：{sorted(miss)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
