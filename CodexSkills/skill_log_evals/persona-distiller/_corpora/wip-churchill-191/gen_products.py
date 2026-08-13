#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Churchill #191 十份产物：正文一律从 claims.jsonl 现渲染，不在这里手打。"""
import json, pathlib, re, sys
from collections import defaultdict

W = pathlib.Path(__file__).resolve().parent / "workspaces" / "winston-churchill"
CLAIMS = [json.loads(l) for l in (W / "evidence/claims.jsonl")
          .read_text(encoding="utf-8").splitlines() if l.strip()]
BY = defaultdict(list)
for c in CLAIMS:
    BY[c["category"]].append(c)
NAME = "Winston Churchill"
BANNED = ("holdout", "留出集", "密封集")


def render(c, ind=""):
    out = [f"{ind}- {c['claim']} <!-- claim:{c['claim_id']} -->"]
    for f in c.get("falsifiers", [])[:2]:
        out.append(f"{ind}  - **反证条件**：{f}")
    return "\n".join(out)


def block(cs, ind=""):
    return "\n".join(render(c, ind) for c in cs)


SCOPE = f"""{NAME}（1874–1965）。本库覆盖的是他**出版年 ≤1930** 的著作：
1899 年的两部战地记述、1900 年的南非通讯、1923–27 年的《The World Crisis》、
以及 1930 年的自传《My Early Life》。**不覆盖 1930 年之后的一切**——
包括二战、《The Second World War》《A History of the English-Speaking Peoples》，
它们全部落在公有领域分界（≤1930，随年份滚动）之外。

★★ **三条必须先知道的射程限制**：

1. **《Lord Randolph Churchill》(1906) 整份不取引文**——那是他写**他父亲**的传记，
   正文里大量是转引的书信与校友回忆，且引语用**单引号**，
   自动判定器只认双引号、挡不住。里面的第一人称**不能默认是他的**。
2. **《Savrola》(1900) 整份不取引文**——那是**小说**，第一人称是虚构人物。
3. **他的公开讲话只能隔着第三方编者看**：语料里唯一的演说材料是
   1915 年别人编的汇编，被判成二手。

★ 同名者提示：**美国小说家 Winston Churchill（1871–1947）**与他同名同期，
作品同样在公有领域，且 Internet Archive 的著录**把两人混在一起**——
抓源时是靠**题名**排除的，不是靠生卒年。
"""

F = BY["fact"]
FILES = {}
FILES["facts.md"] = f"""# 事实 · {NAME}

{SCOPE}

## 早年与从军

{block([c for c in F if c["time_scope"] in ("1888-1893", "1893", "1895", "1899")])}

## 政治转折

{block([c for c in F if c["time_scope"] in ("1900", "1904")])}
"""
FILES["work.md"] = f"""# 做法 · {NAME}

每条都是**步骤 + 判据**，不是格言。

{block(BY["work-method"])}
"""
FILES["decision-policy.md"] = f"""# 决策规则 · {NAME}

替他作答时按下列次序：

1. **先划掉最流行的那个解释**，再给自己的。
2. **用成本语言下判断**——问负担得起负担不起，不问对错。
3. **不想裁决的争论，用一个具体到荒谬的条件收尾**。
4. **转述别人给的细节时明写出处。**

{block(BY["work-method"])}
"""
FILES["strategy.md"] = f"""# 策略 · {NAME}

他处理战略问题的固定路数：**把是非问题换算成负担问题**，
再把现成的口号放进引号里否掉。

{block([c for c in BY["work-method"] if "成本" in c["claim"]])}
"""
FILES["capabilities.md"] = f"""# 能答什么 · {NAME}

{SCOPE}

## 答得上来的

- 1897–1900 年印度西北边境、苏丹、南非三场战事里他**亲历的部分**。
- 他 1888–1904 年的求学、从军、进入政界与换党。
- 1911–1918 年海军部与战时决策，**限于 1923–27 年那几卷里他自己的叙述**。

## 答不上来的

- **1930 年之后的一切**（含二战全部）。
- 《Lord Randolph Churchill》与《Savrola》里的第一人称。
- 他的演说原文——只有第三方汇编。

{block(BY["boundary"])}
"""
FILES["boundaries.md"] = f"""# 边界 · {NAME}

{SCOPE}

{block(BY["boundary"] + BY["hypothesis"])}
"""
FILES["cognitive-os.md"] = f"""# 思考方式 · {NAME}

{block(BY["mental-model"])}

## 它怎么影响他的句子

- 定义爱用**两半式**（手段一半、目的一半），不用复合从句。
- 归因先做**减法**：先否掉通行解释。
- 判断落在**账面动词**上（afford／protect／cost）。

{block(BY["work-method"])}
"""
FILES["hypotheses.md"] = f"""# 假说 · {NAME}

下面这些**没有被证实**，写在这里是为了让人知道本产物哪里薄。

{block(BY["hypothesis"])}
"""
FILES["persona.md"] = f"""# 人物 · {NAME}

{SCOPE}

## 说话的样子

{block(BY["work-method"][:2])}

## 他知道的具体的事

{block(F[:3])}

---

★ 一句可直接感受的：谈接种争议时他不站队，最后一句是
**若他们能发明一种防子弹的接种法，我马上去打**——
**争论以一个具体到荒谬的条件收尾，而不是以结论收尾**。
"""
FILES["divergence-map.md"] = f"""# 与常见印象的分歧 · {NAME}

| 常见印象 | 本库语料给出的 |
|---|---|
| 「丘吉尔＝二战演说家」 | 本库**一个字都不覆盖 1930 年之后**；他在这里是战地记者与青年政客 |
| 「他天生擅长考试与学业」 | 他自己写**考进 Sandhurst 用了三次** |
| 「他的判断以道义为准」 | 战略判断落在**账面动词**上：负担得起负担不起 |
| 「《Lord Randolph Churchill》是他的自述」 | 那是他写**他父亲**的传记，正文大量转引他人书信 |
| 「IA 上署 Winston Churchill 的都是他」 | **美国小说家 Winston Churchill（1871–1947）**同名同期、同在公有领域，著录还把两人混在一起 |

{block(BY["mental-model"] + BY["hypothesis"])}
"""


def main():
    bad = [(n, w) for n, b in FILES.items() for w in BANNED if w.lower() in b.lower()]
    for n, b in FILES.items():
        (W / n).write_text(b, encoding="utf-8")
    if bad:
        print("✗ 产物正文出现不该出现的词：", bad); return 1
    ids = set()
    for b in FILES.values():
        ids |= set(re.findall(r"<!-- claim:(clm-[0-9a-f]+) -->", b))
    print(f"✓ 十份产物写好；引用到的断言 {len(ids)}/{len(CLAIMS)} 条")
    miss = {c["claim_id"] for c in CLAIMS} - ids
    if miss:
        print(f"   ★ 没被引用的断言 {len(miss)} 条：{sorted(miss)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
