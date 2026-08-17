#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""check_unblock_premise_fresh.py —— **「在等某个裁定」的条目，那个裁定可能早就裁过了**

## 抓到它的那一次

2026-08-17：想推进本周蒸馏，去翻延后名单的 `unblock_todo`。
**75 条**的第一句写着：

    ★ 等待 ㉜ 裁定；裁定放宽即整批复活并逐个重新探测。

而 ㉜ **已于 2026-08-12 裁定「A：规则只管新做的」——不放宽**。
更正确实写了，但在**第二条**；首行仍是那句过期话。
只读首行的人（或工具）拿到的是过期答案。
[[i-read-the-superseded-original-not-the-correction-4000-lines-away]]
[[a-blocked-by-x-label-needs-x-rerun]]（★ 暂停的理由也会过期）

## 本件判什么

`unblock_todo` 里点名了某个**裁定编号**（㉒–㊿ 那一组带圈数字）的条目：

1. 若该编号在「已裁定清单」里 ⇒ **首行必须是更正**（以「【裁决更正」开头）；
2. 否则报出来 —— **不是「没问题」，是「它在等一个已经落地的东西」**。

「已裁定清单」从 `_已裁定编号.json` 读；读不到就 **rc=4 未量**，
**不许当成「没有已裁定的编号」**（那会让本件恒绿）。
[[zero-hit-gates-must-prove-they-can-hit]]

退出码：0＝全部新鲜；1＝有条目的前提已过期；4＝读不到名单或清单（未量）。
"""
import argparse
import json
import pathlib
import re
import sys

HERE = pathlib.Path(__file__).resolve().parent
LEDGERS = HERE.parent
DEFER = LEDGERS / "_延后名单.json"
DECIDED = LEDGERS / "_已裁定编号.json"

# ★★★ 带圈数字**横跨三个 Unicode 区块** —— 我第一版只写了 `[㉒-㉿㊀-㊿]`，
#   ⑱⑲⑳㉑ 四个当场漏掉（它们在 U+2460–24FF 与 U+3251–325F）。
#   [[checkers-assume-a-shape-the-product-outgrows]]
CIRCLED = re.compile("[\u2460-\u24ff\u3251-\u325f\u32b1-\u32bf]")
LEAD = "【裁决更正"


# ★★★ **「提到 X」不等于「在等 X」**。实测样本：
#   真·在等：「**待裁定 ㉓** 定了口径后可重判」
#   只是引用：「不要按卒年下结论——按出版年查（**㉚ 更正记着这一条**）」
#   第一版把两者混在一起报，15 条里 Khan/Weibull 那一批全是假阳。
#   ⇒ 只在**等待语境**里才算。[[read-the-hits-before-reporting-the-rate]]
WAIT = ("待裁定", "等待", "等 ", "若裁定", "若 ", "除非", "有待", "取决于", "裁定放宽", "裁定后")
_WIN = 24          # 编号前后各看这么多字符


def cited(todo, only_waiting: bool = True) -> set:
    """→ 这一条 `unblock_todo` 里**在等**的裁定编号集合。

    `only_waiting=False` 时退回「凡提到就算」——**只给自测用**，
    产线一律用等待语境，否则「引用某条裁定当依据」会被报成前提过期。
    """
    if isinstance(todo, str):
        todo = [todo]
    text = " ".join(str(x) for x in (todo or []))
    out = set()
    for m in CIRCLED.finditer(text):
        if not only_waiting:
            out.add(m.group()); continue
        win = text[max(0, m.start() - _WIN): m.end() + _WIN]
        if any(w in win for w in WAIT):
            out.add(m.group())
    return out


def stale(todo, decided: set) -> set:
    """→ 已裁定、而**首行不是更正**的那些编号。空集 = 新鲜。"""
    if isinstance(todo, str):
        todo = [todo]
    todo = list(todo or [])
    if todo and str(todo[0]).startswith(LEAD):
        return set()
    return cited(todo) & decided


def self_test() -> int:
    bad = []

    def chk(lbl, ok):
        print(("  ✓ " if ok else "  ✗ ") + lbl)
        if not ok:
            bad.append(lbl)

    chk("★ 等待语境里的编号抽得出来", cited(["等 ㉜ 裁定"]) == {"㉜"})
    chk("★★★ 反对照：**只是引用某条裁定当依据，不算在等**"
        "（「按出版年查（㉚ 更正记着这一条）」——Khan/Weibull 那一批）",
        cited(["不要按卒年下结论——按出版年查（㉚ 更正记着这一条）"]) == set())
    chk("★★★ 正对照：**真·在等的照样抓**（「待裁定 ㉓ 定了口径后可重判」——Bessemer）",
        cited(["待裁定 ㉓ 定了口径后可重判"]) == {"㉓"})
    chk("★★★ **三个 Unicode 区块的带圈数字都要认**（⑱⑲⑳ 在 U+2460 区、㉑ 在 U+3251 区、"
        "㊵ 在 U+32B1 区）—— 第一版只写了一个区，四个当场漏掉",
        cited(["⑱⑲⑳㉑ 与 ㉜ ㊵"], only_waiting=False) == {"⑱", "⑲", "⑳", "㉑", "㉜", "㊵"})
    chk("★ 没点名编号就是空集", cited(["去抓耶鲁档案馆"]) == set())
    chk("★★ 已裁定 + 首行不是更正 ⇒ **报出来**",
        stale(["★ 等待 ㉜ 裁定"], {"㉜"}) == {"㉜"})
    chk("★★ 已裁定 + **首行是更正** ⇒ 不报",
        stale(["【裁决更正 · 置顶】㉜ 已裁…", "★ 等待 ㉜ 裁定"], {"㉜"}) == set())
    chk("★★ 反对照：**没裁过的编号不许报**（它本来就该在等）",
        stale(["★ 等待 ㊿ 裁定"], {"㉜"}) == set())
    chk("★★ 反对照：**空 unblock_todo 不许报**（缺信息 ≠ 前提过期）",
        stale([], {"㉜"}) == set() and stale(None, {"㉜"}) == set())
    chk("★★★ 反对照：更正在**第二条**而首行仍是旧话 ⇒ **照样报** —— "
        "这正是抓到的那一次的形状",
        stale(["★ 等待 ㉜ 裁定", "★★ 更新：㉜ 已裁定不放宽"], {"㉜"}) == {"㉜"})
    print("\n自测 %d/%d" % (10 - len(bad), 10))
    return 1 if bad else 0


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--self-test", "--selftest", dest="selftest", action="store_true")
    a = ap.parse_args()
    if a.selftest:
        return self_test()

    miss = [p for p in (DEFER, DECIDED) if not p.is_file()]
    if miss:
        print("★ **未量，不是通过**（rc=4）—— 读不到：")
        for p in miss:
            print("     " + str(p))
        print("   ★ 「已裁定清单」缺席时**不许当成「没有已裁定的编号」** —— 那会让本件恒绿。")
        return 4

    rows = json.loads(DEFER.read_text(encoding="utf-8"))["deferred"]
    decided = set(json.loads(DECIDED.read_text(encoding="utf-8")).get("已裁定", {}))
    if not decided:
        print("★ **未量，不是通过**（rc=4）—— 已裁定清单是空的，本件没有可比对的东西")
        return 4

    n_cite = sum(1 for r in rows if cited(r.get("unblock_todo")))
    hits = [(r["name"], sorted(stale(r.get("unblock_todo"), decided))) for r in rows]
    hits = [(n, s) for n, s in hits if s]
    print("扫描面：延后名单 **%d** 条｜其中点名了裁定编号的 **%d** 条｜"
          "已裁定清单 **%d** 个编号" % (len(rows), n_cite, len(decided)))
    if not n_cite:
        print("⚠ **一条都没点名裁定编号 —— 本次未核，不是通过。**")
        return 4
    if hits:
        print("\n✗ **前提已过期** —— 这些条目在等一个**已经裁过**的编号，"
              "而首行没有更正：**%d** 条" % len(hits))
        for n, s in hits[:20]:
            print("     %-26s 等：%s" % (n, "、".join(s)))
        if len(hits) > 20:
            print("     …（共 %d 条）" % len(hits))
        print("\n  ★ 处置：在 `unblock_todo` **最前面**插一条以「【裁决更正」开头的说明，"
              "写清裁定结果与它对本条的影响。**原文一字不改，保留在下面。**")
        return 1
    print("✓ 点名裁定编号的 **%d** 条，前提全部新鲜"
          "（已裁的都在首行带了更正）" % n_cite)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
