#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""同一段语料被多处引用时，把那几处的**结论句**并排列出来。

## 为什么有这件

Lister #108 第 2 轮，两席**各自独立**报了同一处：

> 席 D：「`jl-boundary-01` A 据 PREFACE 断言「选目是我自己定的」，
>        而 `jl-refusal-stop-02` A 引**同样两句**并明说这样讲「就说过头了」。」
> 席 E：「同一段引文在同一份载荷里得出互相否定的结论——后者是对的。
>        这是只读文字就能抓到的自相矛盾。」

代价量出来了：`boundary` 套组 0.8875 → **0.8300**，
把一道**本来已经过了** deep 门（0.85）的项打回不过，−0.0575。
根因是我把「选目由我定」这个说法改了两处、**漏了第三处**。

这个失误（「在一处立规矩、在另一处违反它」）此前已发生九次，
Koch #107 那次的价签是 −0.0146。**它是本流水线最贵的重复失误。**

## 两条走不通的路（都实测过，都是 0 命中，故未采用）

1. **按整条引文去重**：两处引 PREFACE 的起头不同（一处带省略号），
   字符串对不上。实测：11 段长引文里只有 1 段重复，**且不是出问题的那一段**。
2. **按轮次差分找「删了一处、别处仍在」的短句**：两处措辞本就不同
   （「选目是我定的」对「选目是我自己定的」）。实测：26 条被删短句，**0 条命中**。

第三条路才通：**按共享的语料片段分组**（滑窗子串），不要求整条引文一致。
实测在 Lister 上得 6 组，其中一组正是两席抓到的那一对。

## 判据形状：只列不判

它**不判**两处结论是否真的互相否定——那要读懂中文语义。
它做的是把 32 题压成几组并排，让人在几行之内看完。
**「只列不判」的语义就是不阻塞**，故输出进 warnings，不进 errors。

用法：

    python3 check_shared_anchor.py --answers evals/judge_payload.v1.json
    python3 check_shared_anchor.py --self-test

退出码：0=看过了（无论有没有分组）　2=自测未过
"""
from __future__ import annotations

import argparse
import collections
import json
import pathlib
import re
import sys

WINDOW = 40      # 滑窗宽度（字符）。低于此长度的共同片段多是套话，不是同源引用。
STRIDE = 20
MIN_RUN = 35     # 参与切窗的英文连续片段最短长度

RUN = re.compile(r"[A-Za-z][A-Za-z ,;'\-]{%d,}" % (MIN_RUN - 1))


def windows(text: str):
    """产出该文本里所有英文长片段的归一化滑窗。"""
    for m in RUN.finditer(text):
        s = re.sub(r"\s+", " ", m.group(0)).strip().lower()
        for i in range(0, max(1, len(s) - WINDOW), STRIDE):
            w = s[i:i + WINDOW]
            if len(w) == WINDOW:
                yield w


def conclusion_near(text: str, frag: str) -> str:
    """取该片段所在段落之后的第一句中文——那通常就是「据此我说什么」。"""
    low = re.sub(r"\s+", " ", text).lower()
    i = low.find(frag)
    if i < 0:
        return ""
    # 回到原文近似位置，取其后 240 字里的第一段中文
    tail = text[max(0, i):i + 600]
    zh = re.findall(r"[一-鿿][^\n]{6,80}", tail)
    return zh[0].strip() if zh else ""


def group(answers: dict[str, str]) -> dict[frozenset, set]:
    frag: dict[str, set] = collections.defaultdict(set)
    for cid, t in answers.items():
        for w in set(windows(t)):        # set：同一题内重复不算跨题
            frag[w].add(cid)
    shared = {k: v for k, v in frag.items() if len(v) >= 2}
    out: dict[frozenset, set] = collections.defaultdict(set)
    for k, v in shared.items():
        out[frozenset(v)].add(k)
    return out


def self_test() -> int:
    """负对照 + 三条反向对照。"""
    print("══ 负对照 ══")
    fail = 0
    SHARED = ("The two volumes contain all the papers and addresses which he himself "
              "considers to possess permanent interest")

    g = group({"a": SHARED + " 据此可说选目由他定。",
               "b": SHARED + " 但这样讲就说过头了。"})
    hit = any({"a", "b"} == set(k) for k in g)
    print(f"  {'✓ 抓到' if hit else '✗ 漏掉'} 两题引同一段语料 → 并排列出")
    fail += not hit

    print("\n══ 反向对照 ══")
    # ① 无共同片段 → 不得分组，否则本件会把每一对都列出来，等于没用
    g2 = group({"a": "In compound fracture there is an irregular wound exposed to the air",
                "b": "The paste should be changed daily and the rag maintained permanently"})
    print(f"  {'✓' if not g2 else '✗'} 两题无共同语料片段 → 不分组（{len(g2)} 组）")
    fail += bool(g2)

    # ② 同一题内重复出现 → 不算跨题
    g3 = group({"a": SHARED + " 中间隔一段。" + SHARED})
    print(f"  {'✓' if not g3 else '✗'} 同一题内重复 → 不算跨题（{len(g3)} 组）")
    fail += bool(g3)

    # ③ 短的共同套话 → 不得分组（窗口宽度在起作用）
    g4 = group({"a": "the antiseptic principle is what matters here in this case",
                "b": "the antiseptic principle was applied in a wholly different setting"})
    short_ok = not g4
    print(f"  {'✓' if short_ok else '✗'} 仅共享短套话 → 不分组（{len(g4)} 组）")
    fail += bool(g4)

    print("\n  ✓ 负对照通过（4/4）" if not fail
          else f"\n  ✗ {fail} 项未过——本检查器已失效，其「通过」不构成证据")
    return fail


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--answers", type=pathlib.Path, nargs="*", default=[])
    ap.add_argument("--self-test", action="store_true")
    a = ap.parse_args()

    if a.self_test and not a.answers:
        return 2 if self_test() else 0
    if not a.answers:
        ap.error("--answers 必填（除非只跑 --self-test）")

    answers: dict[str, str] = {}
    for path in a.answers:
        data = json.loads(path.read_text(encoding="utf-8"))
        if isinstance(data, list):
            for row in data:
                for side in ("A", "B"):
                    if isinstance(row.get(side), str):
                        answers[f"{row.get('case_id')}:{side}"] = row[side]
        elif isinstance(data, dict):
            for k, v in data.items():
                if isinstance(v, str) and not k.startswith("_"):
                    answers[k] = v

    g = group(answers)
    if not g:
        print(f"{len(answers)} 题里没有跨题共享的语料片段——**无从比对，不是通过**")
        return 0

    print(f"{len(answers)} 题里有 {len(g)} 组引了同一段语料。"
          "**逐组读一遍，看结论有没有互相否定——本件不判这个。**\n")
    for cids, frags in sorted(g.items(), key=lambda x: (-len(x[0]), sorted(x[0]))):
        f0 = sorted(frags)[0]
        print(f"  ── {sorted(cids)}")
        print(f"     共享片段：「{f0}…」")
        for cid in sorted(cids):
            c = conclusion_near(answers[cid], f0)
            print(f"       {cid}：{c or '（其后无中文结论句）'}")
        print()
    print("  ⚠ **只列不判。** 两处引同一段语料本身没有错，"
          "错的是据同一段得出互相否定的结论。\n"
          "    Lister #108 第 2 轮实测：这样的一处让 boundary 套组从 0.8875 掉到 0.8300，"
          "把一道已经过了的门打回不过。")
    return 0


if __name__ == "__main__":
    sys.exit(main())
