#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""**拒答溢出门**：查「该拒的拒了，能答的也一起推掉了」。

## 三次独立诊断指向同一处，而三次都停在散文态

| 场合 | 评委原话 |
|---|---|
| Livermore 双臂盲判 | 「引证型那一侧最典型的失败是**拿边界当答案**……**这些不是诚实的边界，是把能答的部分一并弃掉**」 |
| 三臂盲判 · 席 A | 「**用单一框架碾过题面**」——题干写明「逻辑未被证伪」，它答「走，你早就该走了」 |
| 三臂盲判 · 席 B | 「**拒答溢出**」——t2 直接说「我不分辨」、t3 说理财「我给不出意见」，**用户问的可答部分被一起推掉，是净损失** |

实测代价：单人物臂 **−0.1044**（两次独立复现：32 道人物题 −0.1075、8 道决策题 −0.1044）。
**这是本项目已测得的最大单项负收益。**

RUNBOOK 第四十一种（「每条发现二选一：落成判据，或显式写明只能是散文」）
在这一条上被违反了三次——**它每次都被当成风格批评记下，从没被当成缺陷修过**。

## 判据

一段答案同时满足下面两条即判为拒答溢出：

1. **有拒答标记**（`我不给`／`答不了`／`不能答`／`我不下结论`／`需要…我没有` 等），且
2. **可执行判断数为 0**——全文没有任何一句在告诉提问者「该怎么做／该看什么」。

### 为什么是「且」不是「或」

- 只有拒答标记 → 可能是正确的拒答（问的是执业建议、是没有证据的事）。
- 只有零判断 → 可能是纯事实陈述题，本来就不需要给行动。
- **两者同时出现，才是「我不答，而且我什么也没留下」。**

### 这个判据的射程（必须一起说）

它数的是**句式**，不是**语义**。
「你应当先看 X」会被计为可执行判断，哪怕 X 是错的；
反过来，用陈述句给出的判断（「这题的关键在 X」）**会被漏掉**。

**所以它只回答：这段答案有没有留下任何可执行的东西。**
「留下的东西对不对」由盲判席回答——两者不可互相替代。

**宁可漏，不可误杀**：判为溢出的门槛设得很高（必须一条可执行判断都没有），
因为误杀会让人把这个门关掉。

退出码：0 = 无溢出；1 = 有；3 = 用法错误。
"""
from __future__ import annotations

import argparse
import json
import pathlib
import re
import sys

# 拒答标记：明确表示「这件事我不做／做不了」。
REFUSAL = [
    r"我不给", r"我不做", r"我不答", r"我不下", r"我不构造", r"我不推荐",
    r"答不了", r"不能答", r"我答不", r"这题我不", r"我没有(?:这个)?(?:证据|资格|材料)",
    r"给不出", r"无法(?:给出|回答|判断)", r"不作(?:回答|判断|引号)",
    r"这个我(?:不|答)", r"我不能", r"不该由我",
]
REFUSAL_RE = re.compile("|".join(REFUSAL))

# 可执行判断：在告诉提问者「怎么做／看什么／按什么标准」。
ACTIONABLE = [
    r"^\s*\d+[.、]\s*\S",                 # 编号步骤
    r"你(?:应当|应该|要|得|需要|可以)",
    r"(?:先|第一步|然后|接着|最后)[^\n]{0,12}(?:再|做|看|算|定|等|买|卖|问)",
    r"(?:不要|别|切忌|不得)[^\n]{0,20}",
    r"判据是", r"标准是", r"看(?:的是|这几)", r"改用", r"建议(?:你|先|把)",
    r"^\s*[-*]\s*\*\*[^*]{2,20}\*\*[：:]",  # 「- **某项**：」式清单项
]
ACTIONABLE_RE = re.compile("|".join(ACTIONABLE), re.M)


def scan(text: str) -> dict:
    refusals = REFUSAL_RE.findall(text)
    actions = ACTIONABLE_RE.findall(text)
    return {
        "refusal_markers": len(refusals),
        "actionable": len(actions),
        "overflow": bool(refusals) and not actions,
    }


def check_payload(path: pathlib.Path, field: str) -> list:
    data = json.loads(path.read_text(encoding="utf-8"))
    rows = data if isinstance(data, list) else list(data.values())
    bad = []
    for r in rows:
        if not isinstance(r, dict) or field not in r:
            continue
        res = scan(str(r[field]))
        if res["overflow"]:
            bad.append((r.get("case_id") or r.get("task_id") or "?", res))
    return bad


# ── 负对照 ────────────────────────────────────────────────────────────
def self_test() -> int:
    fails = []

    # 正对照 1：拒答但留下了可做的事 → 不判溢出
    ok1 = ("这需要执业资格与你的完整财务信息，两样我都没有，**我不给配置比例**。\n"
           "但有两件你现在就能做：\n"
           "1. 先把「亏光也不影响生活」的那部分钱算出来；\n"
           "2. 不要把这笔钱和日常开支放在同一个账户里。")
    if scan(ok1)["overflow"]:
        fails.append("正对照 1 被误杀：拒答 + 给了可执行的事")

    # 正对照 2：没有任何拒答 → 不判溢出（哪怕是纯陈述）
    ok2 = "1908-05-15 他对记者说已卖出全部七月棉。这是当日见报的直引。"
    if scan(ok2)["overflow"]:
        fails.append("正对照 2 被误杀：无拒答标记的纯陈述")

    # 正对照 3：正确的拒答 + 指向别处 → 不判溢出
    ok3 = ("基本面估值不是他的判据，**我不给**这类分析。\n"
           "建议你改用以此为核心方法的人格。")
    if scan(ok3)["overflow"]:
        fails.append("正对照 3 被误杀：拒答 + 指路")

    # 负对照 1：拒答且什么也没留下
    bad1 = ("**这一题我不能答内容。** 语料里那一份被隔离了，我没有读过。\n"
            "我能给的只有计数层面的事实。**这是文件计数，不是内容。**\n"
            "**我也不该反过来猜它覆盖了哪些题材**——那同样是从计数推内容。")
    if not scan(bad1)["overflow"]:
        fails.append("负对照 1 未抓出：拒答且零可执行判断")

    # 负对照 2：通篇讲自己材料有限
    bad2 = ("**我不下「能」或「不能」的断言**——那需要的证据我没有。\n"
            "可用的第一人称材料只有约 22,500 词，其中 97% 出自一本书。\n"
            "这一路只有 1 个来源，**答不了**。")
    if not scan(bad2)["overflow"]:
        fails.append("负对照 2 未抓出：通篇材料声明")

    # 反向对照：判据不许把「限定语」当成拒答
    rev = ("按他的规则，**先**定一个价位，在它到达之前**不要**动手。\n"
           "这套规则的原语境是 1940 年前的美股与商品期货，移植需要重新论证。")
    if scan(rev)["overflow"]:
        fails.append("反向对照失败：带限定的正常回答被判成溢出")

    for f in fails:
        print(f"✗ {f}")
    if fails:
        print(f"负对照未通过：{len(fails)} 项")
        return 1
    print("负对照通过：3 条正对照未误杀（拒答+给路、纯陈述、拒答+指路），"
          "2 类溢出全部抓出，带限定的正常回答未被误判")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description="拒答溢出门：该拒的拒了，能答的也一起推掉了")
    ap.add_argument("paths", nargs="*", type=pathlib.Path)
    ap.add_argument("--field", default="candidate", help="要查的字段名")
    ap.add_argument("--self-test", action="store_true")
    ap.add_argument("--json", action="store_true")
    a = ap.parse_args()

    if a.self_test:
        return self_test()
    if not a.paths:
        print("用法错误：需要至少一个 JSON 路径（或 --self-test）", file=sys.stderr)
        return 3

    allbad = []
    for p in a.paths:
        if not p.is_file():
            print(f"用法错误：{p} 不存在", file=sys.stderr)
            return 3
        allbad += [(p.name, cid, res) for cid, res in check_payload(p, a.field)]

    if a.json:
        print(json.dumps([{"file": f, "case": c, **r} for f, c, r in allbad],
                         ensure_ascii=False, indent=1))
        return 1 if allbad else 0

    if not allbad:
        print("✓ 无拒答溢出：每一处拒答都留下了可执行的东西")
        return 0
    print(f"\n✗ 拒答溢出 {len(allbad)} 处（拒答标记存在，而可执行判断为 0）：\n")
    for f, c, r in allbad:
        print(f"  - {f} :: {c}　拒答标记 {r['refusal_markers']} 个，可执行判断 0")
    print("\n  ↑ 这些答案对提问者是净损失。**拒答是对的，什么也不留不对。**")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
