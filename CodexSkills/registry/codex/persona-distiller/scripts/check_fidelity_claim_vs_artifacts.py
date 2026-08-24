#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""**声称「照印本录，一字不改」，紧接着录出印本不可能有的东西。**

## 它是席 F 在 Sorby #133 第 2 轮当场指出的，原话

> 声明「以下照印本录，**一字不改**」，随即录出「complete immu- nity」
> 「one **balf** of **wbat** I intended」。
> **印本上不会印着 `balf`、`wbat`，也不会把 `immunity` 从中间断开。**
> 我没有语料、没核也没假装核过引文真伪，只指出这段的自述与它自己的产出对不上。

★ 这是**不需要语料就能判的**——两句话自己打架。
评委没有语料、核不了任何引文真伪，却仍然抓到了它，靠的就是内部一致性。

## 为什么单独立一件，而不并进出戏门

出戏门问的是「**人物该不该谈这个**」，它有出处套组豁免——
`fact-preservation` 那类题里谈讹字**是对的**，所以出戏门对这一处放行，且放行得没错。

本件问的是另一件事：「**这段话自己前后对不对得上**」。
声称逐字忠实于**印本**，却展示只有**影印/OCR** 才会产生的痕迹，
那么要么「照印本录」这句是错的（其实照的是扫描件），要么引文被动过。
**两者都得改，而出戏门永远看不到它。**

## 它判什么

同一条答案里同时出现：

1. **忠实度声明**——「一字不改」「照录不改」「照印本录」「原样保留」「逐字」…
2. **印本不可能有的痕迹**——
   · 跨行断字 `immu- nity`（字母、连字符、**空格**、字母）；
   · 已知 OCR 形近讹字 `balf`←half、`wbat`←what、`arc`→`are` 这一类
     （**只认成对出现且答案自己点名的**，不猜）。

→ 报「忠实度声明与印本不可能的痕迹同现」。**只报不拦。**

★★ 正确的写法有两种，本件都不拦：
   · 只录、不声称「照印本录」（改称「照我手上这份影印件录」）；
   · 或者引一句没有排印异常的原话。

★★★ **不拦的理由**：改法涉及引文，而引文一字不能乱动
（[[verbatim-is-not-understood]] 的另一半：改了讹字再当逐字引文用，一天出过两次）。
这必须由人来定改哪一头。
"""

import argparse
import json
import pathlib
import re
import sys

# ① 忠实度声明
FIDELITY = (
    r"一字不改", r"一字未改", r"照录不改", r"照印本[录抄]", r"原样保留",
    r"原样引", r"照原样", r"逐字引", r"未改字",
)
# ② 印本不可能有的痕迹
#   ★ 跨行断字：字母-连字符-**空格**-字母。`well-known` 不中（连字符后无空格）。
HYPHEN_BREAK = re.compile(r"[A-Za-z]{2,}-\s+[A-Za-z]{2,}")
#   ★ 形近讹字**只认答案自己点名的**——不去猜哪个词是讹字。
#     形如「印本作 balf、wbat，即 half 与 what」「are 是 arc 的 OCR 讹字」。
NAMED_TYPO = (
    re.compile(r"[（(][^）)]{0,20}(?:印本作|原作|作)\s*[A-Za-z]{2,}"),
    re.compile(r"[A-Za-z]{2,}\s*是\s*[A-Za-z]{2,}\s*的\s*(?:OCR\s*)?讹字"),
    re.compile(r"(?:讹|误)(?:排|印|作)\s*[A-Za-z]{2,}"),
)


def scan(text: str) -> dict:
    t = str(text)
    claims = [m.group(0) for pat in FIDELITY for m in re.finditer(pat, t)]
    marks = []
    for m in HYPHEN_BREAK.finditer(t):
        marks.append(("跨行断字", m.group(0)))
    for pat in NAMED_TYPO:
        for m in pat.finditer(t):
            marks.append(("点名的形近讹字", m.group(0)))
    return {"忠实度声明": sorted(set(claims)), "印本不可能的痕迹": marks}


def check(answers: dict) -> dict:
    hits = {}
    for cid, ans in sorted((answers or {}).items()):
        r = scan(ans)
        if r["忠实度声明"] and r["印本不可能的痕迹"]:
            hits[cid] = r
    return {
        "题数": len(answers or {}),
        "**声明与痕迹同现**": hits,
        "计数": f"{len(hits)} 题声称逐字忠实于印本，同时展示了印本不可能有的痕迹",
        "★ 口径": "**只报不拦**——改法涉及引文，引文一字不能乱动，改哪一头由人定。",
        "通过": True,
    }


def self_test() -> int:
    bad = []

    def chk(label, ok):
        print(f"  {'✓' if ok else '✗'} {label}")
        if not ok:
            bad.append(label)

    print("── 正例：席 F 在 Sorby #133 当场指出的那一段 ──")
    r = check({"hs-fact-preservation-01":
               "以下照印本录，一字不改。「in the course of nearly thirty years」，"
               "immunity 印本跨行断作 immu- nity，原样保留。"})
    chk("报出来了", "hs-fact-preservation-01" in r["**声明与痕迹同现**"])

    print("\n── ★ 反向对照①：只有声明、没有痕迹 → 不许报 ──")
    r = check({"a-1": "以下照印本录，一字不改。「the microscope tells more than the eye」。"})
    chk(f"没报：{r['计数']}", not r["**声明与痕迹同现**"])

    print("\n── ★ 反向对照②：只有痕迹、没有声明 → 不许报 ──")
    # 这一头归出戏门管，不归本件。**两件事不许互相顶替。**
    r = check({"a-2": "我当年写的是 complete immu- nity。"})
    chk(f"没报：{r['计数']}", not r["**声明与痕迹同现**"])

    print("\n── ★★ 反向对照③：`well-known` 这类连字符不许当跨行断字 ──")
    r = check({"a-3": "照录不改：this is a well-known and self-evident matter."})
    chk(f"没报：{r['计数']}", not r["**声明与痕迹同现**"])

    print("\n── ★★ 反向对照④：破折号不是连字符 ──")
    r = check({"a-4": "一字不改——我当年就是这么写的，没有别的说法。"})
    chk(f"没报：{r['计数']}", not r["**声明与痕迹同现**"])

    print("\n── ★★★ 反向对照⑤：空答案不许报 ──")
    chk("空的没报", not check({})["**声明与痕迹同现**"])

    if bad:
        print("\n未过：")
        for b in bad:
            print(f"  · {b}")
        return 2
    print("\n✓ 自测全过（1 正 + 5 反向对照）")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("answers", nargs="?", help="case_id → 答案 的 JSON")
    ap.add_argument("--self-test", action="store_true")
    a = ap.parse_args()
    if a.self_test:
        return self_test()
    if not a.answers:
        ap.error("要么 --self-test，要么给答案 JSON")
    d = json.loads(pathlib.Path(a.answers).read_text(encoding="utf-8"))
    if not isinstance(d, dict):
        print("✗ 需要 {case_id: 答案} 形状的 JSON", file=sys.stderr)
        return 2
    print(json.dumps(check({k: v for k, v in d.items() if isinstance(v, str)}),
                     ensure_ascii=False, indent=2))
    return 0            # **只报不拦**


if __name__ == "__main__":
    sys.exit(main())
